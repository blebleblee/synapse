# Lesson 2: Event-Driven Architecture Patterns

## 1. First-Principles Intuition & Invariants

Event-driven architecture fundamentally inverts the traditional request-response paradigm that has dominated distributed systems for decades. In a synchronous model, a service acts as a client, blocking its execution thread while waiting for a downstream server to process a request and return a response. This temporal coupling creates a brittle cascade of failure; if the downstream service experiences latency, the upstream service's thread pool exhausts, leading to cascading timeouts and systemic collapse. Serverless platforms like AWS Lambda exacerbate this fragility because the execution environment is ephemeral, and blocked connections represent wasted compute cycles billed by duration. Event-driven architecture severs this temporal cord. A producer emits an event—a record that something has occurred—and immediately continues its execution. The consumer processes the event asynchronously, completely unaware of the producer's current state.

The shift to asynchronous coupling demands a recalibration of our mental invariants. The most critical invariant is the acceptance of at-least-once delivery semantics. Exactly-once processing is a distributed systems fallacy; achieving it requires distributed consensus protocols like two-phase commits, which introduce unacceptable latency and lock contention. Instead, serverless systems rely on retry mechanisms and dead-letter queues, which guarantee delivery but permit duplicates. Consequently, consumers must be strictly idempotent. An operation is idempotent if executing it multiple times has the same effect as executing it once. In a serverless event-driven system, this is not an optimization; it is a prerequisite for correctness.

Another invariant is partitioned event ordering. Total global ordering of events across a distributed system is prohibitively expensive, requiring a single serialized bottleneck that negates the benefits of horizontal scaling. Instead, we enforce ordering only where it matters: per aggregate or per entity. By using a partition key, such as an `order_id` or `customer_id`, the infrastructure guarantees that all events related to that specific entity are delivered to the same processing lane in the order they were produced. This provides the illusion of synchronous state mutation for a single entity while allowing massive parallelism across different entities.

Finally, event sourcing reifies state as a sequence of immutable facts. Rather than mutating a current state record in place, an event-sourced system appends events to an append-only log. The current state is merely a projection—a materialized view—calculated by replaying the event log from the beginning. In serverless infrastructure, DynamoDB Streams combined with Lambda functions provide a native mechanism for implementing this pattern, allowing us to maintain a persistent event log and derive multiple read-optimized views from it.

## 2. Core Architecture & Mechanics

The mechanics of serverless event-driven architecture rely on a few foundational primitives: the event router, the queue, and the compute layer. AWS EventBridge serves as a high-performance event router, capable of filtering and routing JSON events to various targets based on content. To demonstrate pub/sub and fan-out, we provision an EventBridge rule that matches specific event types and routes them to independent SQS queues. This decouples the producer from multiple independent consumers, allowing each consumer to scale and fail independently.

The following Terraform configuration establishes a complete fan-out pattern. A custom EventBridge bus receives payment events, and a rule filters for `PaymentInitiated` events. The rule targets two distinct SQS queues: one for fraud detection and one for ledger updates. Crucially, the SQS queues are configured with dead-letter queues to capture poison pill messages.

```hcl
# EventBridge Bus and Rule for Fan-Out
resource "aws_cloudwatch_event_bus" "payment_bus" {
  name = "payment-events-bus"
}

resource "aws_cloudwatch_event_rule" "payment_initiated_rule" {
  name           = "payment-initiated-fanout"
  event_bus_name = aws_cloudwatch_event_bus.payment_bus.name
  event_pattern = jsonencode({
    "detail-type" = ["PaymentInitiated"]
  })
}

# SQS Queue for Fraud Detection
resource "aws_sqs_queue" "fraud_dlq" {
  name = "fraud-dlq"
}

resource "aws_sqs_queue" "fraud_queue" {
  name                       = "fraud-queue"
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.fraud_dlq.arn
    maxReceiveCount     = 3
  })
}

# SQS Queue for Ledger Update
resource "aws_sqs_queue" "ledger_dlq" {
  name = "ledger-dlq"
}

resource "aws_sqs_queue" "ledger_queue" {
  name                       = "ledger-queue"
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ledger_dlq.arn
    maxReceiveCount     = 3
  })
}

# EventBridge Targets
resource "aws_cloudwatch_event_target" "fraud_target" {
  rule           = aws_cloudwatch_event_rule.payment_initiated_rule.name
  event_bus_name = aws_cloudwatch_event_bus.payment_bus.name
  target_id      = "fraud-processor"
  arn            = aws_sqs_queue.fraud_queue.arn
}

resource "aws_cloudwatch_event_target" "ledger_target" {
  rule           = aws_cloudwatch_event_rule.payment_initiated_rule.name
  event_bus_name = aws_cloudwatch_event_bus.payment_bus.name
  target_id      = "ledger-processor"
  arn            = aws_sqs_queue.ledger_queue.arn
}
```

With the event routed to SQS, the compute layer must consume it idempotently. Using Rust for the Lambda consumer provides both memory safety and minimal cold start latency, crucial for processing high-volume streams. The following Rust code implements an idempotent consumer that processes SQS events. It utilizes DynamoDB conditional writes to guarantee that a duplicate message does not result in double-processing.

```rust
use aws_lambda_events::event::sqs::SqsEvent;
use aws_sdk_dynamodb::{Client, types::AttributeValue};
use lambda_runtime::{service_fn, Error, LambdaEvent};
use std::time::{SystemTime, UNIX_EPOCH};

async fn process_payment(body: &str) -> Result<(), Error> {
    let payload: serde_json::Value = serde_json::from_str(body)?;
    let amount = payload["amount"].as_f64().unwrap_or(0.0);
    if amount > 1000.0 {
        return Err("Amount exceeds limit".into());
    }
    Ok(())
}

async fn handler(event: LambdaEvent<SqsEvent>, client: &Client) -> Result<(), Error> {
    for record in event.payload.records.iter().filter_map(|r| r.as_ref().ok()) {
        if let (Some(message_id), Some(body)) = (&record.message_id, &record.body) {
            let idempotency_key = format!("IDEMP#{}", message_id);
            let ttl = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs() + 3600;

            match client.put_item()
                .table_name("IdempotencyStore")
                .item("pk", AttributeValue::S(idempotency_key.clone()))
                .item("ttl", AttributeValue::N(ttl.to_string()))
                .condition_expression("attribute_not_exists(pk)")
                .send()
                .await {
                Ok(_) => {
                    process_payment(body).await?;
                }
                Err(e) => {
                    let err_str = e.to_string();
                    if !err_str.contains("ConditionalCheckFailedException") {
                        return Err(e.into());
                    }
                }
            }
        }
    }
    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let config = aws_config::load_from_env().await;
    let client = Client::new(&config);
    lambda_runtime::run(service_fn(|event| handler(event, &client))).await
}
```

Event sourcing mechanics are natively supported by DynamoDB Streams. By treating a DynamoDB table as an append-only event log, we can stream changes to Lambda functions that build materialized views. The table is partitioned by the aggregate ID, ensuring that all events for a specific entity are delivered in strict sequence. In DynamoDB, the partition key determines which partition stores the data. DynamoDB Streams captures changes at the partition level. The stream shard maps to this partition. The Lambda event source mapping polls the shard iterator. Because the iterator is strictly ordered within a shard, the Lambda function receives the events in the exact order they were written to the partition. This guarantees per-aggregate ordering. The Terraform below provisions such a table with streaming enabled.

```hcl
resource "aws_dynamodb_table" "event_store" {
  name           = "EventStore"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "aggregate_id"
  range_key      = "version"
  stream_enabled = true
  stream_view_type = "NEW_IMAGE"

  attribute {
    name = "aggregate_id"
    type = "S"
  }
  attribute {
    name = "version"
    type = "N"
  }
}

resource "aws_lambda_event_source_mapping" "event_projection" {
  event_source_arn  = aws_dynamodb_table.event_store.stream_arn
  function_name     = aws_lambda_function.projection.arn
  starting_position = "LATEST"
  batch_size        = 10
}
```

When designing complex workflows that require coordination across multiple services, the choice between choreography and orchestration becomes critical. Choreography, implemented via EventBridge and SQS as shown above, relies on each service reacting to events independently. This works well for simple fan-out scenarios but can become difficult to trace as the number of services grows. Orchestration, conversely, uses a central coordinator—like AWS Step Functions—to explicitly manage the state transitions and sequence of operations. The following Terraform definition orchestrates a payment workflow, managing retries and fallback logic explicitly.

```hcl
resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_lambda_function" "fraud_check" {
  filename      = "fraud_check.zip"
  function_name = "fraud-check"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "bootstrap"
  runtime       = "provided.al2023"
}

resource "aws_lambda_function" "process_payment" {
  filename      = "process_payment.zip"
  function_name = "process-payment"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "bootstrap"
  runtime       = "provided.al2023"
}

resource "aws_lambda_function" "update_ledger" {
  filename      = "update_ledger.zip"
  function_name = "update-ledger"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "bootstrap"
  runtime       = "provided.al2023"
}

resource "aws_lambda_function" "reject_payment" {
  filename      = "reject_payment.zip"
  function_name = "reject-payment"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "bootstrap"
  runtime       = "provided.al2023"
}

resource "aws_iam_role" "sfn_exec" {
  name = "sfn_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "sfn_invoke_lambda" {
  name = "sfn_invoke_lambda"
  role = aws_iam_role.sfn_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "lambda:InvokeFunction"
        Effect = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "payment_orchestrator" {
  name     = "payment-orchestrator"
  role_arn = aws_iam_role.sfn_exec.arn

  definition = jsonencode({
    Comment = "Payment Orchestration Workflow"
    StartAt = "FraudCheck"
    States = {
      FraudCheck = {
        Type = "Task"
        Resource = aws_lambda_function.fraud_check.arn
        Retry = [
          {
            ErrorEquals = ["States.TaskFailed"]
            IntervalSeconds = 2
            MaxAttempts = 3
            BackoffRate = 2.0
          }
        ]
        Next = "FraudCheckChoice"
      }
      FraudCheckChoice = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.risk_score"
            NumericGreaterThan = 80
            Next = "RejectPayment"
          }
        ]
        Default = "ProcessPayment"
      }
      ProcessPayment = {
        Type = "Task"
        Resource = aws_lambda_function.process_payment.arn
        Next = "UpdateLedger"
      }
      UpdateLedger = {
        Type = "Task"
        Resource = aws_lambda_function.update_ledger.arn
        End = true
      }
      RejectPayment = {
        Type = "Task"
        Resource = aws_lambda_function.reject_payment.arn
        End = true
      }
    }
  })
}
```

## 3. High-Performance Optimization & Failure Modes

High-performance event-driven systems live and die by their handling of failure modes and backpressure. In a serverless context, backpressure manifests when a consumer cannot keep pace with the producer. SQS handles this natively by acting as a buffer, but if the queue depth grows unbounded, message latency increases, and cost can spiral. The primary mitigation is to tune the Lambda event source mapping concurrency. Setting a reserved concurrency limit on the Lambda function prevents it from scaling unbounded and exhausting downstream database connections, while adjusting the batch size optimizes the throughput per invocation.

Poison pill messages—messages that cause the consumer to fail repeatedly—must be isolated. The `redrive_policy` in the SQS queue configuration defines a `maxReceiveCount`. Once a message is received that number of times without deletion, SQS automatically routes it to the Dead Letter Queue. This prevents a single malformed event from blocking the entire pipeline. Engineers must monitor the DLQ with alerts, as messages in the DLQ represent manual intervention points.

Idempotency implementations must be resilient to clock drift and throttling. The DynamoDB conditional write approach is robust, but the TTL on the idempotency record must be set conservatively. If the TTL is too short, a delayed duplicate message might arrive after the original idempotency record has expired, resulting in double-processing. If the TTL is too long, the table grows unnecessarily, increasing storage costs. A 24-hour TTL is a standard heuristic, balancing the risk of extreme delivery latency against storage cost. Furthermore, the DynamoDB table used for idempotency should have autoscaling or on-demand capacity configured, as sudden bursts of events can exhaust provisioned throughput, causing throttling and Lambda invocation failures.

Finally, cold starts represent a latency tax on asynchronous processing. While SQS buffering absorbs much of the impact by allowing messages to wait, high-throughput streams require immediate processing. Using Rust, as demonstrated, minimizes the initialization duration. For Java or other JVM languages, SnapStart reduces cold start times by restoring from a pre-initialized snapshot. For the highest performance, provisioned concurrency keeps a pool of execution environments warm, eliminating cold starts entirely at the cost of continuous compute billing. The choice depends on the latency requirements of the specific event stream, but for internal infrastructure events where seconds of latency are tolerable, a purely event-driven, asynchronously coupled architecture with careful idempotency and DLQ management provides a resilient, infinitely scalable foundation.
