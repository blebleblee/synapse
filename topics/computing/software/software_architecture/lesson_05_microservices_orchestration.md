# Lesson 5: Microservices Orchestration

## 1. First-Principles Intuition & Invariants

The architectural transition from monolithic applications to microservices represents a fundamental shift in how we reason about distributed state, failure domains, and operational complexity. At its core, microservices orchestration is the disciplined practice of composing autonomous, independently deployable services into coherent business capabilities while preserving the invariants that make distributed systems correct: consistency, availability, and partition tolerance. The CAP theorem, formalized by Eric Brewer in 2000, establishes that no distributed system can simultaneously guarantee all three properties in the presence of network partitions. This constraint forces us to make explicit tradeoffs at service boundaries, transforming architectural design from an exercise in structural decomposition into a rigorous exercise in failure mode analysis and operational reasoning.

The microservices paradigm emerged from the recognition that monolithic applications create artificial coupling between components that evolve at different rates, are owned by different teams, and experience different scaling pressures. A monolith forces every feature to share the same runtime, deployment pipeline, database transaction scope, and failure domain. When a single poorly optimized query consumes excessive database connections, it starves unrelated features. When a memory leak destabilizes one module, the entire process crashes. When a team needs to deploy a critical security patch, they must coordinate a full application deployment that includes untested changes from every other team. These operational pathologies stem from a single root cause: the monolith violates the principle of isolation.

Microservices invert this default. Each service owns a bounded context—a term borrowed from Domain-Driven Design—that encapsulates a cohesive slice of business logic, its data models, and its persistence layer. Services communicate across well-defined API contracts, typically over HTTP or gRPC for synchronous request-response patterns, or through message brokers like Kafka and RabbitMQ for asynchronous event-driven flows. This architectural boundary enables independent deployment, polyglot persistence, and heterogeneous technology stacks. The payments service can use PostgreSQL with strict ACID transactions while the analytics service uses Cassandra for high-throughput append-only event logs. The recommendation engine can deploy a new machine learning model without coordinating with the user authentication service.

However, this independence comes at a cost: distributed systems complexity. When a monolith executes a business transaction, it coordinates multiple database writes within a single ACID transaction. The database engine guarantees atomicity through write-ahead logging, isolation through multiversion concurrency control, and durability through fsync barriers. When that same transaction spans multiple microservices, each with its own database, we lose the database's transactional guarantees. A failure after the payment service commits but before the inventory service deducts stock leaves the system in an inconsistent state. Rolling back the payment requires explicit compensating transactions, and detecting the failure requires distributed tracing and correlation IDs that propagate through the entire call chain.

The fundamental invariant of microservices orchestration is that every cross-service interaction must be designed with failure as the default case. Networks partition, services crash, downstream dependencies become temporarily unavailable, and requests timeout. In a monolith, these failures manifest as exceptions that bubble up the call stack and trigger transaction rollbacks. In a microservices architecture, they manifest as partial failures where some services succeed while others fail, leaving the system in a state that requires explicit reconciliation logic. The saga pattern, introduced by Hector Garcia-Molina and Kenneth Salem in 1987, provides a formal model for coordinating long-lived distributed transactions through a sequence of local transactions, each paired with a compensating transaction that semantically undoes its effects.

Service boundaries are not arbitrary lines drawn on an architecture diagram. They represent fault isolation boundaries, deployment boundaries, team ownership boundaries, and transactional consistency boundaries. A well-designed service boundary encapsulates a bounded context with high cohesion and low coupling. It owns a stable domain model that evolves independently from other services. It exposes a versioned API contract that insulates downstream consumers from internal implementation changes. It maintains its own datastore to avoid distributed joins and cross-service foreign key constraints. And it implements idempotency to tolerate duplicate requests, because in distributed systems with at-least-once delivery semantics, duplicates are not edge cases—they are operational certainties.

The choreography versus orchestration dichotomy captures two fundamentally different approaches to coordinating multi-service workflows. In orchestration, a central coordinator service explicitly invokes each participant in sequence, maintaining the workflow state and handling failures. This approach provides visibility and control but creates a single point of failure and tight coupling between the orchestrator and its participants. In choreography, services react to domain events published by other services, with no central coordinator. Each service listens for events it cares about, performs its local transaction, and publishes new events that trigger downstream reactions. This approach achieves loose coupling and eliminates the orchestrator bottleneck but makes the overall workflow implicit and harder to reason about. Production systems typically use a hybrid model: choreography for coarse-grained event-driven flows and orchestration for tightly coordinated workflows that require strong consistency guarantees.

Inter-service communication patterns fall into two broad categories: synchronous request-response and asynchronous event-driven messaging. Synchronous communication, implemented via HTTP REST or gRPC, couples the caller's execution to the callee's availability and latency. When Service A invokes Service B synchronously, it blocks waiting for B's response, propagating B's latency and unavailability upstream. This transitive dependency creates cascading failures: if B depends on C and C becomes slow, A's latency increases even though A has no direct dependency on C. Asynchronous messaging decouples producers and consumers through a message broker that buffers events and guarantees delivery. Producers publish events without blocking, and consumers process them at their own pace. This pattern absorbs traffic spikes, enables temporal decoupling where producers and consumers don't need to be online simultaneously, and provides natural backpressure through queue depth monitoring.

The distinction between events and commands is semantically critical. An event describes something that happened in the past: "Order Placed", "Payment Received", "Shipment Dispatched". Events are immutable facts that multiple consumers can observe and react to independently. A command describes an imperative action: "Charge Credit Card", "Reserve Inventory", "Send Confirmation Email". Commands are directed requests from one service to another, implying a request-response interaction. Event-driven architectures prefer events because they invert dependencies: the producer doesn't know or care who consumes its events, enabling new consumers to subscribe without modifying the producer. Command-driven architectures create point-to-point coupling where each producer must know which downstream service to invoke.

Distributed tracing transforms opaque service-to-service interactions into observable causality chains. When a request enters the system through an API gateway, the tracing infrastructure generates a unique trace ID and injects it into outgoing requests as an HTTP header or gRPC metadata field. Each service extracts the trace ID, records timing spans for its local processing, and propagates the trace ID to downstream dependencies. The tracing backend—typically Jaeger, Zipkin, or commercial solutions like Datadog and Honeycomb—reconstructs the full request path by correlating spans with the same trace ID. This enables operators to identify which service contributed the most latency, where errors occurred, and how failures propagated through the call graph.

The observability triad—metrics, logs, and traces—provides complementary perspectives on system behavior. Metrics aggregate numerical measurements over time windows: request rates, error rates, latency percentiles. They enable alerting on threshold violations and capacity planning through trend analysis. Logs capture discrete events with structured or unstructured payloads: application errors, audit trails, security events. They enable root cause analysis of specific failures. Traces capture request-scoped causality and timing: which services participated, in what order, with what latency. They enable performance debugging and understanding emergent behavior in complex call graphs. Production microservices architectures instrument all three layers and correlate them through common identifiers: trace IDs link traces to logs, and service name tags link traces and logs to metrics.

The shift from monolithic to microservices architectures fundamentally changes the failure mode surface. Monoliths fail catastrophically: the process crashes and stops serving traffic. Microservices fail partially: some requests succeed while others fail, depending on which services are healthy and which dependencies are unavailable. This partial failure mode requires sophisticated circuit breakers, bulkheads, and retry policies. A circuit breaker monitors the failure rate of calls to a downstream dependency and transitions to an open state when failures exceed a threshold, immediately rejecting subsequent requests without invoking the failing service. This prevents cascading failures and gives the downstream service time to recover. After a timeout, the circuit breaker transitions to a half-open state and allows a small number of test requests through. If they succeed, it closes the circuit and resumes normal traffic. If they fail, it re-opens and continues rejecting requests.

Bulkheads partition resources to prevent failures in one area from consuming shared resources needed by other areas. In a monolithic application, a single thread pool handles all incoming requests. If a slow database query blocks threads, the entire application becomes unresponsive. In a microservices architecture, each downstream dependency uses a separate thread pool or connection pool. If the recommendation service becomes slow, it exhausts only the threads allocated to recommendation calls, leaving other services unaffected. This resource isolation principle extends to network connections, database connections, memory buffers, and compute quotas. The name derives from bulkheads in ship hull design, which partition the interior into watertight compartments so that a breach floods only one compartment rather than sinking the entire vessel.

Idempotency transforms at-least-once delivery semantics into exactly-once processing semantics at the application layer. Message brokers like Kafka guarantee at-least-once delivery: every message is delivered to consumers at least once but may be delivered multiple times due to retries, network partitions, or consumer crashes during message processing. Without idempotency, duplicate messages cause duplicate side effects: charging a credit card twice, sending duplicate notification emails, double-counting analytics events. An idempotent service produces the same result regardless of how many times it processes the same request. This requires deduplication logic that tracks processed message IDs or request tokens in a durable store and skips processing for duplicates. For stateful operations like database updates, idempotency often requires compare-and-swap semantics: "Update order status to 'Shipped' only if current status is 'Paid'".

Service mesh architectures delegate cross-cutting concerns—service discovery, load balancing, mutual TLS, circuit breaking, distributed tracing—to a dedicated infrastructure layer. Rather than embedding this logic in application libraries, which creates coupling to a specific language and requires coordinated library upgrades across all services, the service mesh deploys a sidecar proxy alongside each service instance. The sidecar intercepts all inbound and outbound network traffic, enforcing policies and injecting observability instrumentation without application code changes. Istio, Linkerd, and Consul Connect are the dominant service mesh implementations in Kubernetes environments. They operate at layer 4 and layer 7 of the OSI model, providing transparent TCP proxying as well as protocol-aware features for HTTP, gRPC, and other application protocols.

The control plane and data plane dichotomy structures service mesh architecture. The data plane consists of sidecar proxies that handle actual request traffic, enforce policies, and collect telemetry. The control plane consists of centralized components that configure the proxies, distribute certificates, aggregate metrics, and provide operator APIs. Envoy, a high-performance C++ proxy developed at Lyft, dominates the data plane role due to its extensive protocol support, hot-reloading configuration without dropping connections, and rich observability output. The control plane components vary by mesh implementation: Istio uses Pilot for service discovery and configuration distribution, Citadel for certificate management, and Galley for configuration validation. This separation enables the control plane to evolve rapidly while the data plane remains stable and focused on performance.

## 2. Core Architecture & Mechanics

The mechanical foundation of microservices orchestration rests on three pillars: service registration and discovery, API gateway request routing, and message broker event distribution. Each pillar addresses a fundamental coordination problem that arises when services become independently deployed and scaled.

Service discovery solves the problem of locating service instances in dynamic environments where instances start and stop frequently due to autoscaling, deployments, and failures. In a static environment, services could hardcode the IP addresses and ports of their dependencies. In cloud-native environments with container orchestration, service instances are ephemeral and their network locations change constantly. Service discovery provides a layer of indirection where services register their network location upon startup and deregister upon shutdown. Clients query the service registry to obtain the current set of healthy instances for a given service name.

The service registry maintains a mapping from logical service names to physical network endpoints. In Kubernetes, the built-in DNS-based service discovery maps service names to cluster IP addresses backed by iptables or IPVS load balancing rules that distribute traffic across pod IPs. When a pod starts, the kubelet registers it with the API server, which updates the Endpoints object associated with the service. The kube-proxy component on each node watches Endpoints objects and programs the local iptables or IPVS rules to include the new pod. When clients resolve the service DNS name, they receive the cluster IP, and the node's iptables rules probabilistically select a backend pod using DNAT (Destination Network Address Translation).

```mermaid
flowchart TD
    Client["Client Pod"]
    DNS["CoreDNS (cluster DNS)<br/>Returns: 10.96.45.123 (ClusterIP of payment-service)"]
    IPTables["Node iptables/IPVS rules<br/>DNAT 10.96.45.123:8080 → {10.244.1.5:8080,<br/>10.244.2.8:8080,<br/>10.244.3.12:8080}"]
    Pod["Payment Pod<br/>10.244.2.8"]
    
    Client -->|"DNS query for<br/>payment-service.default.svc.cluster.local"| DNS
    DNS --> IPTables
    IPTables -->|"Load-balanced selection"| Pod
```

Client-side load balancing provides an alternative model where clients query the service registry directly and maintain their own load balancing state. Consul and Eureka popularized this pattern in pre-Kubernetes microservices deployments. The client periodically polls the registry for updated instance lists and uses local load balancing algorithms—round robin, least connections, weighted random—to select a target instance for each request. This approach eliminates the dependency on infrastructure load balancers but requires embedding registry client libraries in every service and handling registry failures gracefully. Service meshes revive client-side load balancing by moving the logic into sidecar proxies that query the control plane for service endpoints and perform sophisticated load balancing with health checking, connection pooling, and circuit breaking.

API gateways serve as the single entry point for external clients, routing requests to appropriate backend services based on URL paths, HTTP headers, or request payloads. They implement cross-cutting concerns that would otherwise be duplicated in every service: authentication, rate limiting, request transformation, response aggregation, and API versioning. Kong, Tyk, and Envoy-based gateways like Ambassador and Gloo dominate production deployments. The gateway parses incoming requests, authenticates the caller by validating JWT tokens or API keys, enforces rate limits by tracking request counts in Redis or a local in-memory cache, transforms the request format if needed, routes the request to the appropriate backend service, and optionally aggregates responses from multiple services into a single client response.

The routing decision logic evaluates request attributes against a set of configured rules. A typical configuration maps URL path prefixes to backend services: `/api/users/*` routes to the user service, `/api/orders/*` routes to the order service, `/api/payments/*` routes to the payment service. More sophisticated routing considers HTTP methods, header values, query parameters, and request body content. The gateway maintains a routing table populated from configuration files, environment variables, or a dynamic configuration API. When configuration changes, the gateway hot-reloads the routing table without dropping existing connections, ensuring zero-downtime configuration updates.

```go
// Production API Gateway Route Configuration (Kong declarative format)
services:
  - name: user-service
    url: http://user-service.default.svc.cluster.local:8080
    routes:
      - name: user-api
        paths:
          - /api/users
        methods:
          - GET
          - POST
          - PUT
          - DELETE
        strip_path: false
    plugins:
      - name: jwt
        config:
          secret_is_base64: false
          key_claim_name: kid
      - name: rate-limiting
        config:
          minute: 100
          policy: redis
          redis_host: redis.default.svc.cluster.local
          redis_port: 6379

  - name: order-service
    url: http://order-service.default.svc.cluster.local:8080
    routes:
      - name: order-api
        paths:
          - /api/orders
        methods:
          - GET
          - POST
        strip_path: false
    plugins:
      - name: jwt
        config:
          secret_is_base64: false
          key_claim_name: kid
      - name: correlation-id
        config:
          header_name: X-Correlation-ID
          generator: uuid
          echo_downstream: true

  - name: payment-service
    url: http://payment-service.default.svc.cluster.local:8080
    routes:
      - name: payment-api
        paths:
          - /api/payments
        methods:
          - POST
        strip_path: false
    plugins:
      - name: jwt
        config:
          secret_is_base64: false
          key_claim_name: kid
      - name: request-size-limiting
        config:
          allowed_payload_size: 1
      - name: correlation-id
        config:
          header_name: X-Correlation-ID
          generator: uuid
          echo_downstream: true
```

Message brokers decouple producers and consumers through persistent message queues or publish-subscribe topics. Apache Kafka has emerged as the dominant choice for event-driven microservices due to its high throughput, durable commit log architecture, and strong ordering guarantees within partitions. Kafka organizes messages into topics, which are partitioned across multiple brokers for horizontal scalability. Each partition is a totally ordered, immutable sequence of messages appended to a replicated commit log. Producers write messages to partition leaders, which replicate them to follower brokers before acknowledging the write. Consumers read messages from assigned partitions, tracking their position through consumer offsets stored in a special Kafka topic.

The partition assignment and consumer group coordination mechanism enables scalable parallel consumption. Consumers join a consumer group identified by a group ID. Kafka's group coordinator assigns each consumer a subset of the topic's partitions, ensuring that each partition is assigned to exactly one consumer in the group. When a consumer joins or leaves the group, Kafka triggers a rebalance that redistributes partitions among the remaining consumers. This enables horizontal scaling: adding more consumers to the group increases parallelism, and removing consumers redistributes their workload. The coordinator uses the Kafka protocol's heartbeat and session timeout mechanisms to detect consumer failures and trigger rebalances.

```mermaid
flowchart TD
    Topic["📊 Topic: order-events<br/>(6 partitions, RF=3)"]
    
    subgraph Brokers ["Partition Layout Across Brokers"]
        B1["<b>Broker 1</b><br/>P0-Leader<br/>P1-Follower<br/>P2-Follower<br/>P3-Leader<br/>P4-Follower<br/>P5-Follower"]
        B2["<b>Broker 2</b><br/>P0-Follower<br/>P1-Leader<br/>P2-Follower<br/>P3-Follower<br/>P4-Leader<br/>P5-Follower"]
        B3["<b>Broker 3</b><br/>P0-Follower<br/>P1-Follower<br/>P2-Leader<br/>P3-Follower<br/>P4-Follower<br/>P5-Leader"]
    end
    
    subgraph ConsumerGroup ["Consumer Group: order-processors"]
        CA["Consumer A<br/>[P0, P1]"]
        CB["Consumer B<br/>[P2, P3]"]
        CC["Consumer C<br/>[P4, P5]"]
    end
    
    Coordinator["🔧 Group Coordinator<br/>(Broker 2)<br/>• Assignments<br/>• Heartbeats<br/>• Offset Management"]
    
    OffsetsTopic["__consumer_offsets<br/>Topic"]
    
    Producer["📤 Producer"]
    
    Topic --> Brokers
    Brokers --> ConsumerGroup
    ConsumerGroup --> Coordinator
    Coordinator --> CA
    Coordinator --> CB
    Coordinator --> CC
    CA --> OffsetsTopic
    CB --> OffsetsTopic
    CC --> OffsetsTopic
    Producer --> Brokers
```

Synchronous inter-service communication via gRPC provides type-safe, high-performance request-response interactions. gRPC uses Protocol Buffers for interface definition and message serialization, generating client and server stubs from `.proto` schema files. The generated code provides strongly typed method signatures, eliminating entire classes of integration errors that plague schema-less HTTP APIs. The binary encoding is significantly more compact than JSON, reducing network bandwidth and serialization CPU overhead. HTTP/2 multiplexing enables multiple concurrent RPC calls over a single TCP connection, eliminating the head-of-line blocking that HTTP/1.1 suffers with connection-per-request patterns.

```protobuf
// order_service.proto - Production gRPC Service Definition
syntax = "proto3";

package order.v1;

import "google/protobuf/timestamp.proto";
import "google/api/annotations.proto";

service OrderService {
  rpc CreateOrder(CreateOrderRequest) returns (CreateOrderResponse) {
    option (google.api.http) = {
      post: "/v1/orders"
      body: "*"
    };
  }
  
  rpc GetOrder(GetOrderRequest) returns (Order) {
    option (google.api.http) = {
      get: "/v1/orders/{order_id}"
    };
  }
  
  rpc ListOrders(ListOrdersRequest) returns (ListOrdersResponse) {
    option (google.api.http) = {
      get: "/v1/orders"
    };
  }
  
  rpc UpdateOrderStatus(UpdateOrderStatusRequest) returns (Order) {
    option (google.api.http) = {
      patch: "/v1/orders/{order_id}/status"
      body: "*"
    };
  }
}

message CreateOrderRequest {
  string user_id = 1;
  repeated OrderItem items = 2;
  Address shipping_address = 3;
  PaymentMethod payment_method = 4;
  string idempotency_key = 5;  // Client-generated UUID for idempotent retries
}

message CreateOrderResponse {
  Order order = 1;
}

message Order {
  string order_id = 1;
  string user_id = 2;
  OrderStatus status = 3;
  repeated OrderItem items = 4;
  Address shipping_address = 5;
  Money total_amount = 6;
  google.protobuf.Timestamp created_at = 7;
  google.protobuf.Timestamp updated_at = 8;
}

message OrderItem {
  string product_id = 1;
  int32 quantity = 2;
  Money unit_price = 3;
}

message Address {
  string street = 1;
  string city = 2;
  string state = 3;
  string postal_code = 4;
  string country = 5;
}

message Money {
  string currency_code = 1;  // ISO 4217 currency code
  int64 amount = 2;          // Amount in smallest currency unit (cents)
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
  ORDER_STATUS_SHIPPED = 3;
  ORDER_STATUS_DELIVERED = 4;
  ORDER_STATUS_CANCELLED = 5;
}

message PaymentMethod {
  oneof method {
    CreditCard credit_card = 1;
    BankAccount bank_account = 2;
  }
}

message CreditCard {
  string token = 1;  // PCI-compliant tokenized card reference
  string last_four = 2;
}

message BankAccount {
  string token = 1;
  string last_four = 2;
}

message GetOrderRequest {
  string order_id = 1;
}

message ListOrdersRequest {
  string user_id = 1;
  int32 page_size = 2;
  string page_token = 3;
}

message ListOrdersResponse {
  repeated Order orders = 1;
  string next_page_token = 2;
}

message UpdateOrderStatusRequest {
  string order_id = 1;
  OrderStatus status = 2;
}
```

The gRPC server implementation handles incoming requests by unmarshaling protobuf-encoded messages, executing business logic, and marshaling responses. Connection lifecycle management, including HTTP/2 stream multiplexing and flow control, is handled transparently by the gRPC runtime. The server can stream responses incrementally for large result sets, enabling efficient pagination without holding the entire dataset in memory.

```go
// Production gRPC Server Implementation with Context Propagation
package main

import (
    "context"
    "database/sql"
    "fmt"
    "log"
    "net"
    "time"

    "github.com/google/uuid"
    _ "github.com/lib/pq"
    "go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/status"

    pb "example.com/order/v1"
)

type orderServer struct {
    pb.UnimplementedOrderServiceServer
    db     *sql.DB
    tracer trace.Tracer
}

func (s *orderServer) CreateOrder(ctx context.Context, req *pb.CreateOrderRequest) (*pb.CreateOrderResponse, error) {
    ctx, span := s.tracer.Start(ctx, "CreateOrder")
    defer span.End()

    // Extract trace context from gRPC metadata for distributed tracing
    md, ok := metadata.FromIncomingContext(ctx)
    if ok {
        if traceID := md.Get("x-trace-id"); len(traceID) > 0 {
            span.SetAttributes(attribute.String("trace.id", traceID[0]))
        }
    }

    // Validate idempotency key
    if req.IdempotencyKey == "" {
        return nil, status.Error(codes.InvalidArgument, "idempotency_key is required")
    }

    // Check for existing order with same idempotency key (idempotent retry handling)
    var existingOrderID string
    err := s.db.QueryRowContext(ctx,
        "SELECT order_id FROM orders WHERE idempotency_key = $1",
        req.IdempotencyKey,
    ).Scan(&existingOrderID)
    
    if err == nil {
        // Idempotent retry: return existing order
        span.SetAttributes(attribute.Bool("idempotent_retry", true))
        order, err := s.getOrderByID(ctx, existingOrderID)
        if err != nil {
            return nil, status.Errorf(codes.Internal, "failed to retrieve existing order: %v", err)
        }
        return &pb.CreateOrderResponse{Order: order}, nil
    } else if err != sql.ErrNoRows {
        return nil, status.Errorf(codes.Internal, "idempotency check failed: %v", err)
    }

    // Generate new order ID
    orderID := uuid.New().String()
    span.SetAttributes(attribute.String("order.id", orderID))

    // Calculate total amount
    var totalAmount int64
    for _, item := range req.Items {
        totalAmount += item.UnitPrice.Amount * int64(item.Quantity)
    }

    // Begin database transaction
    tx, err := s.db.BeginTx(ctx, nil)
    if err != nil {
        return nil, status.Errorf(codes.Internal, "failed to begin transaction: %v", err)
    }
    defer tx.Rollback()

    // Insert order record
    now := time.Now()
    _, err = tx.ExecContext(ctx,
        `INSERT INTO orders (order_id, user_id, status, total_amount, currency_code, 
                             idempotency_key, created_at, updated_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        orderID, req.UserId, pb.OrderStatus_ORDER_STATUS_PENDING, totalAmount,
        req.Items[0].UnitPrice.CurrencyCode, req.IdempotencyKey, now, now,
    )
    if err != nil {
        return nil, status.Errorf(codes.Internal, "failed to insert order: %v", err)
    }

    // Insert order items
    for _, item := range req.Items {
        _, err = tx.ExecContext(ctx,
            `INSERT INTO order_items (order_id, product_id, quantity, unit_price)
             VALUES ($1, $2, $3, $4)`,
            orderID, item.ProductId, item.Quantity, item.UnitPrice.Amount,
        )
        if err != nil {
            return nil, status.Errorf(codes.Internal, "failed to insert order item: %v", err)
        }
    }

    // Commit transaction
    if err := tx.Commit(); err != nil {
        return nil, status.Errorf(codes.Internal, "failed to commit transaction: %v", err)
    }

    // Construct response
    order := &pb.Order{
        OrderId:  orderID,
        UserId:   req.UserId,
        Status:   pb.OrderStatus_ORDER_STATUS_PENDING,
        Items:    req.Items,
        TotalAmount: &pb.Money{
            CurrencyCode: req.Items[0].UnitPrice.CurrencyCode,
            Amount:       totalAmount,
        },
        ShippingAddress: req.ShippingAddress,
        CreatedAt:       timestampProto(now),
        UpdatedAt:       timestampProto(now),
    }

    span.SetAttributes(attribute.Int64("order.total_amount", totalAmount))
    return &pb.CreateOrderResponse{Order: order}, nil
}

func (s *orderServer) GetOrder(ctx context.Context, req *pb.GetOrderRequest) (*pb.Order, error) {
    ctx, span := s.tracer.Start(ctx, "GetOrder")
    defer span.End()

    span.SetAttributes(attribute.String("order.id", req.OrderId))

    order, err := s.getOrderByID(ctx, req.OrderId)
    if err == sql.ErrNoRows {
        return nil, status.Error(codes.NotFound, "order not found")
    } else if err != nil {
        return nil, status.Errorf(codes.Internal, "failed to retrieve order: %v", err)
    }

    return order, nil
}

func (s *orderServer) getOrderByID(ctx context.Context, orderID string) (*pb.Order, error) {
    var order pb.Order
    var totalAmount int64
    var currencyCode string
    var createdAt, updatedAt time.Time
    var statusInt int32

    err := s.db.QueryRowContext(ctx,
        `SELECT order_id, user_id, status, total_amount, currency_code, created_at, updated_at
         FROM orders WHERE order_id = $1`,
        orderID,
    ).Scan(&order.OrderId, &order.UserId, &statusInt, &totalAmount, &currencyCode, &createdAt, &updatedAt)

    if err != nil {
        return nil, err
    }

    order.Status = pb.OrderStatus(statusInt)
    order.TotalAmount = &pb.Money{CurrencyCode: currencyCode, Amount: totalAmount}
    order.CreatedAt = timestampProto(createdAt)
    order.UpdatedAt = timestampProto(updatedAt)

    // Load order items
    rows, err := s.db.QueryContext(ctx,
        `SELECT product_id, quantity, unit_price FROM order_items WHERE order_id = $1`,
        orderID,
    )
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    for rows.Next() {
        var item pb.OrderItem
        var unitPrice int64
        if err := rows.Scan(&item.ProductId, &item.Quantity, &unitPrice); err != nil {
            return nil, err
        }
        item.UnitPrice = &pb.Money{CurrencyCode: currencyCode, Amount: unitPrice}
        order.Items = append(order.Items, &item)
    }

    return &order, nil
}

func timestampProto(t time.Time) *timestamppb.Timestamp {
    return &timestamppb.Timestamp{Seconds: t.Unix(), Nanos: int32(t.Nanosecond())}
}

func main() {
    // Initialize database connection
    db, err := sql.Open("postgres", "postgres://user:pass@localhost/orders?sslmode=disable")
    if err != nil {
        log.Fatalf("Failed to connect to database: %v", err)
    }
    defer db.Close()

    // Configure connection pool
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)

    // Initialize tracer
    tracer := otel.Tracer("order-service")

    // Create gRPC server with OpenTelemetry instrumentation
    grpcServer := grpc.NewServer(
        grpc.UnaryInterceptor(otelgrpc.UnaryServerInterceptor()),
        grpc.StreamInterceptor(otelgrpc.StreamServerInterceptor()),
        grpc.MaxRecvMsgSize(4*1024*1024), // 4MB max request size
    )

    orderSvc := &orderServer{db: db, tracer: tracer}
    pb.RegisterOrderServiceServer(grpcServer, orderSvc)

    // Start listening
    lis, err := net.Listen("tcp", ":8080")
    if err != nil {
        log.Fatalf("Failed to listen: %v", err)
    }

    log.Println("Order service listening on :8080")
    if err := grpcServer.Serve(lis); err != nil {
        log.Fatalf("Failed to serve: %v", err)
    }
}
```

Event-driven choreography enables loosely coupled workflows where services react to domain events published by other services. The canonical example is order fulfillment: when a user places an order, the order service publishes an "Order Created" event. The payment service subscribes to this event, charges the customer's credit card, and publishes a "Payment Completed" event. The inventory service subscribes to "Payment Completed", reserves stock, and publishes an "Inventory Reserved" event. The shipping service subscribes to "Inventory Reserved", creates a shipment, and publishes a "Shipment Created" event. Each service performs its local transaction, updates its own database, and publishes events that trigger downstream reactions. No central orchestrator coordinates the workflow; the overall flow emerges from the choreographed interactions.

```go
// Production Kafka Event Producer with Idempotent Publishing
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "time"

    "github.com/IBM/sarama"
    "github.com/google/uuid"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
)

type OrderEvent struct {
    EventID     string    `json:"event_id"`
    EventType   string    `json:"event_type"`
    OrderID     string    `json:"order_id"`
    UserID      string    `json:"user_id"`
    TotalAmount int64     `json:"total_amount"`
    Currency    string    `json:"currency"`
    Timestamp   time.Time `json:"timestamp"`
}

type EventProducer struct {
    producer sarama.SyncProducer
    tracer   trace.Tracer
}

func NewEventProducer(brokers []string) (*EventProducer, error) {
    config := sarama.NewConfig()
    config.Producer.RequiredAcks = sarama.WaitForAll // Wait for all in-sync replicas
    config.Producer.Retry.Max = 5
    config.Producer.Return.Successes = true
    config.Producer.Idempotent = true // Enable idempotent producer
    config.Producer.CompressionLevel = sarama.CompressionLevelDefault
    config.Net.MaxOpenRequests = 1 // Required for idempotent producer

    producer, err := sarama.NewSyncProducer(brokers, config)
    if err != nil {
        return nil, fmt.Errorf("failed to create producer: %w", err)
    }

    return &EventProducer{
        producer: producer,
        tracer:   otel.Tracer("event-producer"),
    }, nil
}

func (p *EventProducer) PublishOrderCreated(ctx context.Context, orderID, userID string, totalAmount int64, currency string) error {
    ctx, span := p.tracer.Start(ctx, "PublishOrderCreated")
    defer span.End()

    event := OrderEvent{
        EventID:     uuid.New().String(),
        EventType:   "order.created",
        OrderID:     orderID,
        UserID:      userID,
        TotalAmount: totalAmount,
        Currency:    currency,
        Timestamp:   time.Now().UTC(),
    }

    span.SetAttributes(
        attribute.String("event.id", event.EventID),
        attribute.String("event.type", event.EventType),
        attribute.String("order.id", orderID),
    )

    payload, err := json.Marshal(event)
    if err != nil {
        return fmt.Errorf("failed to marshal event: %w", err)
    }

    msg := &sarama.ProducerMessage{
        Topic: "order-events",
        Key:   sarama.StringEncoder(orderID), // Partition by order ID for ordering
        Value: sarama.ByteEncoder(payload),
        Headers: []sarama.RecordHeader{
            {Key: []byte("event_type"), Value: []byte(event.EventType)},
            {Key: []byte("event_id"), Value: []byte(event.EventID)},
        },
    }

    partition, offset, err := p.producer.SendMessage(msg)
    if err != nil {
        span.RecordError(err)
        return fmt.Errorf("failed to publish event: %w", err)
    }

    span.SetAttributes(
        attribute.Int("kafka.partition", int(partition)),
        attribute.Int64("kafka.offset", offset),
    )

    log.Printf("Published event %s to partition %d offset %d", event.EventID, partition, offset)
    return nil
}

func (p *EventProducer) Close() error {
    return p.producer.Close()
}
```

The consumer side implements at-least-once processing semantics with idempotency to achieve exactly-once business logic execution. The consumer reads messages from assigned partitions, processes each message, updates its local database, and commits the consumer offset back to Kafka. If the consumer crashes after processing a message but before committing the offset, it will re-process the message upon restart. Idempotency logic ensures that reprocessing produces the same result.

```go
// Production Kafka Event Consumer with Idempotent Processing
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "os"
    "os/signal"
    "syscall"

    "github.com/IBM/sarama"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
)

type PaymentService struct {
    consumer sarama.ConsumerGroup
    tracer   trace.Tracer
}

type OrderCreatedEvent struct {
    EventID     string `json:"event_id"`
    EventType   string `json:"event_type"`
    OrderID     string `json:"order_id"`
    UserID      string `json:"user_id"`
    TotalAmount int64  `json:"total_amount"`
    Currency    string `json:"currency"`
}

func NewPaymentService(brokers []string, groupID string) (*PaymentService, error) {
    config := sarama.NewConfig()
    config.Consumer.Return.Errors = true
    config.Consumer.Offsets.Initial = sarama.OffsetOldest
    config.Consumer.Group.Rebalance.Strategy = sarama.NewBalanceStrategyRoundRobin()

    consumer, err := sarama.NewConsumerGroup(brokers, groupID, config)
    if err != nil {
        return nil, fmt.Errorf("failed to create consumer group: %w", err)
    }

    return &PaymentService{
        consumer: consumer,
        tracer:   otel.Tracer("payment-service"),
    }, nil
}

func (s *PaymentService) Start(ctx context.Context) error {
    handler := &consumerGroupHandler{service: s}

    go func() {
        for err := range s.consumer.Errors() {
            log.Printf("Consumer error: %v", err)
        }
    }()

    for {
        if err := s.consumer.Consume(ctx, []string{"order-events"}, handler); err != nil {
            return fmt.Errorf("consumer error: %w", err)
        }

        if ctx.Err() != nil {
            return ctx.Err()
        }
    }
}

type consumerGroupHandler struct {
    service *PaymentService
}

func (h *consumerGroupHandler) Setup(sarama.ConsumerGroupSession) error {
    return nil
}

func (h *consumerGroupHandler) Cleanup(sarama.ConsumerGroupSession) error {
    return nil
}

func (h *consumerGroupHandler) ConsumeClaim(session sarama.ConsumerGroupSession, claim sarama.ConsumerGroupClaim) error {
    ctx := context.Background()

    for message := range claim.Messages() {
        ctx, span := h.service.tracer.Start(ctx, "ProcessOrderCreatedEvent")

        // Extract event metadata
        var eventType string
        for _, header := range message.Headers {
            if string(header.Key) == "event_type" {
                eventType = string(header.Value)
            }
        }

        span.SetAttributes(
            attribute.String("kafka.topic", message.Topic),
            attribute.Int("kafka.partition", int(message.Partition)),
            attribute.Int64("kafka.offset", message.Offset),
            attribute.String("event.type", eventType),
        )

        // Only process order.created events
        if eventType != "order.created" {
            session.MarkMessage(message, "")
            span.End()
            continue
        }

        var event OrderCreatedEvent
        if err := json.Unmarshal(message.Value, &event); err != nil {
            log.Printf("Failed to unmarshal event: %v", err)
            span.RecordError(err)
            span.End()
            session.MarkMessage(message, "") // Skip malformed messages
            continue
        }

        span.SetAttributes(
            attribute.String("event.id", event.EventID),
            attribute.String("order.id", event.OrderID),
        )

        // Process payment with idempotency
        if err := h.service.processPayment(ctx, &event); err != nil {
            log.Printf("Failed to process payment for order %s: %v", event.OrderID, err)
            span.RecordError(err)
            span.End()
            // Do not mark message - will be reprocessed
            continue
        }

        // Mark message as processed (commit offset)
        session.MarkMessage(message, "")
        span.End()
    }

    return nil
}

func (s *PaymentService) processPayment(ctx context.Context, event *OrderCreatedEvent) error {
    ctx, span := s.tracer.Start(ctx, "processPayment")
    defer span.End()

    // Check if payment already processed (idempotency check)
    // In production: query payments database with event_id as idempotency key
    // if exists, return success (idempotent retry)

    // Charge credit card (external payment gateway call)
    log.Printf("Processing payment for order %s: %d %s", event.OrderID, event.TotalAmount, event.Currency)

    // Store payment record in database with event_id for idempotency
    // Publish payment.completed event

    span.SetAttributes(attribute.String("payment.status", "completed"))
    return nil
}

func main() {
    brokers := []string{"localhost:9092"}
    service, err := NewPaymentService(brokers, "payment-service-group")
    if err != nil {
        log.Fatalf("Failed to create payment service: %v", err)
    }

    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Handle shutdown signals
    signals := make(chan os.Signal, 1)
    signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)

    go func() {
        <-signals
        log.Println("Shutting down...")
        cancel()
    }()

    if err := service.Start(ctx); err != nil {
        log.Fatalf("Service error: %v", err)
    }
}
```

The saga pattern coordinates distributed transactions through a sequence of local transactions with compensating actions for rollback. Sagas come in two flavors: orchestration-based and choreography-based. Orchestration-based sagas use a central coordinator that explicitly invokes each participant and tracks the overall workflow state. Choreography-based sagas distribute coordination across participants through event publishing and subscription. Both patterns require each step to be idempotent and to implement compensation logic that semantically undoes the step's effects.

Consider an e-commerce order fulfillment saga with four steps: create order, charge payment, reserve inventory, and create shipment. In an orchestration-based saga, the order service acts as coordinator. It creates the order record, invokes the payment service to charge the customer, invokes the inventory service to reserve stock, and invokes the shipping service to create a shipment. If any step fails, the coordinator executes compensating transactions in reverse order: cancel shipment, release inventory, refund payment, cancel order. The coordinator maintains a durable log of completed steps to resume from the point of failure after crashes.

```go
// Production Saga Orchestrator with Durable State Machine
package main

import (
    "context"
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "time"

    "github.com/google/uuid"
    _ "github.com/lib/pq"
)

type SagaState string

const (
    StateInitial          SagaState = "INITIAL"
    StateOrderCreated     SagaState = "ORDER_CREATED"
    StatePaymentCharged   SagaState = "PAYMENT_CHARGED"
    StateInventoryReserved SagaState = "INVENTORY_RESERVED"
    StateShipmentCreated  SagaState = "SHIPMENT_CREATED"
    StateCompleted        SagaState = "COMPLETED"
    StateFailed           SagaState = "FAILED"
    StateCompensating     SagaState = "COMPENSATING"
    StateCompensated      SagaState = "COMPENSATED"
)

type SagaStep struct {
    Name        string
    Execute     func(context.Context, *OrderFulfillmentSaga) error
    Compensate  func(context.Context, *OrderFulfillmentSaga) error
}

type OrderFulfillmentSaga struct {
    SagaID          string
    OrderID         string
    UserID          string
    TotalAmount     int64
    Currency        string
    State           SagaState
    PaymentID       string
    ReservationID   string
    ShipmentID      string
    CompletedSteps  []string
    ErrorMessage    string
    CreatedAt       time.Time
    UpdatedAt       time.Time

    db *sql.DB
}

type SagaOrchestrator struct {
    db    *sql.DB
    steps []SagaStep
}

func NewSagaOrchestrator(db *sql.DB) *SagaOrchestrator {
    return &SagaOrchestrator{
        db: db,
        steps: []SagaStep{
            {
                Name:    "CreateOrder",
                Execute: (*OrderFulfillmentSaga).createOrder,
                Compensate: (*OrderFulfillmentSaga).cancelOrder,
            },
            {
                Name:    "ChargePayment",
                Execute: (*OrderFulfillmentSaga).chargePayment,
                Compensate: (*OrderFulfillmentSaga).refundPayment,
            },
            {
                Name:    "ReserveInventory",
                Execute: (*OrderFulfillmentSaga).reserveInventory,
                Compensate: (*OrderFulfillmentSaga).releaseInventory,
            },
            {
                Name:    "CreateShipment",
                Execute: (*OrderFulfillmentSaga).createShipment,
                Compensate: (*OrderFulfillmentSaga).cancelShipment,
            },
        },
    }
}

func (o *SagaOrchestrator) StartSaga(ctx context.Context, orderID, userID string, totalAmount int64, currency string) (*OrderFulfillmentSaga, error) {
    saga := &OrderFulfillmentSaga{
        SagaID:      uuid.New().String(),
        OrderID:     orderID,
        UserID:      userID,
        TotalAmount: totalAmount,
        Currency:    currency,
        State:       StateInitial,
        CreatedAt:   time.Now(),
        UpdatedAt:   time.Now(),
        db:          o.db,
    }

    // Persist initial saga state
    if err := saga.save(ctx); err != nil {
        return nil, fmt.Errorf("failed to save saga: %w", err)
    }

    // Execute saga steps
    for i, step := range o.steps {
        log.Printf("Executing saga step %d: %s", i+1, step.Name)
        
        if err := step.Execute(ctx, saga); err != nil {
            log.Printf("Saga step %s failed: %v", step.Name, err)
            saga.ErrorMessage = err.Error()
            saga.State = StateFailed
            saga.save(ctx)

            // Execute compensating transactions in reverse order
            if err := o.compensate(ctx, saga, i); err != nil {
                log.Printf("Compensation failed: %v", err)
                return saga, fmt.Errorf("saga failed and compensation failed: %w", err)
            }

            saga.State = StateCompensated
            saga.save(ctx)
            return saga, fmt.Errorf("saga failed: %w", err)
        }

        saga.CompletedSteps = append(saga.CompletedSteps, step.Name)
        saga.save(ctx)
    }

    saga.State = StateCompleted
    saga.save(ctx)
    log.Printf("Saga %s completed successfully", saga.SagaID)
    return saga, nil
}

func (o *SagaOrchestrator) compensate(ctx context.Context, saga *OrderFulfillmentSaga, failedStepIndex int) error {
    saga.State = StateCompensating
    saga.save(ctx)

    // Execute compensating transactions in reverse order
    for i := failedStepIndex - 1; i >= 0; i-- {
        step := o.steps[i]
        log.Printf("Compensating saga step: %s", step.Name)

        if err := step.Compensate(ctx, saga); err != nil {
            return fmt.Errorf("compensation failed for step %s: %w", step.Name, err)
        }
    }

    return nil
}

func (s *OrderFulfillmentSaga) createOrder(ctx context.Context) error {
    s.State = StateOrderCreated
    s.UpdatedAt = time.Now()

    // Call order service to create order
    log.Printf("Creating order %s for user %s", s.OrderID, s.UserID)
    // In production: gRPC call to order service
    time.Sleep(100 * time.Millisecond) // Simulate network call

    return s.save(ctx)
}

func (s *OrderFulfillmentSaga) cancelOrder(ctx context.Context) error {
    log.Printf("Cancelling order %s", s.OrderID)
    // In production: gRPC call to order service to cancel order
    time.Sleep(100 * time.Millisecond)
    return nil
}

func (s *OrderFulfillmentSaga) chargePayment(ctx context.Context) error {
    s.PaymentID = uuid.New().String()
    s.State = StatePaymentCharged
    s.UpdatedAt = time.Now()

    // Call payment service to charge customer
    log.Printf("Charging payment %d %s for order %s", s.TotalAmount, s.Currency, s.OrderID)
    // In production: gRPC call to payment service
    time.Sleep(200 * time.Millisecond)

    return s.save(ctx)
}

func (s *OrderFulfillmentSaga) refundPayment(ctx context.Context) error {
    log.Printf("Refunding payment %s", s.PaymentID)
    // In production: gRPC call to payment service to refund
    time.Sleep(200 * time.Millisecond)
    return nil
}

func (s *OrderFulfillmentSaga) reserveInventory(ctx context.Context) error {
    s.ReservationID = uuid.New().String()
    s.State = StateInventoryReserved
    s.UpdatedAt = time.Now()

    // Call inventory service to reserve stock
    log.Printf("Reserving inventory for order %s", s.OrderID)
    // In production: gRPC call to inventory service
    time.Sleep(150 * time.Millisecond)

    // Simulate occasional inventory failure
    // Uncomment to test compensation:
    // return fmt.Errorf("insufficient inventory")

    return s.save(ctx)
}

func (s *OrderFulfillmentSaga) releaseInventory(ctx context.Context) error {
    log.Printf("Releasing inventory reservation %s", s.ReservationID)
    // In production: gRPC call to inventory service to release reservation
    time.Sleep(150 * time.Millisecond)
    return nil
}

func (s *OrderFulfillmentSaga) createShipment(ctx context.Context) error {
    s.ShipmentID = uuid.New().String()
    s.State = StateShipmentCreated
    s.UpdatedAt = time.Now()

    // Call shipping service to create shipment
    log.Printf("Creating shipment for order %s", s.OrderID)
    // In production: gRPC call to shipping service
    time.Sleep(100 * time.Millisecond)

    return s.save(ctx)
}

func (s *OrderFulfillmentSaga) cancelShipment(ctx context.Context) error {
    log.Printf("Cancelling shipment %s", s.ShipmentID)
    // In production: gRPC call to shipping service to cancel shipment
    time.Sleep(100 * time.Millisecond)
    return nil
}

func (s *OrderFulfillmentSaga) save(ctx context.Context) error {
    completedStepsJSON, err := json.Marshal(s.CompletedSteps)
    if err != nil {
        return err
    }

    _, err = s.db.ExecContext(ctx,
        `INSERT INTO saga_state (saga_id, order_id, user_id, total_amount, currency, state,
                                 payment_id, reservation_id, shipment_id, completed_steps,
                                 error_message, created_at, updated_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
         ON CONFLICT (saga_id) DO UPDATE SET
            state = EXCLUDED.state,
            payment_id = EXCLUDED.payment_id,
            reservation_id = EXCLUDED.reservation_id,
            shipment_id = EXCLUDED.shipment_id,
            completed_steps = EXCLUDED.completed_steps,
            error_message = EXCLUDED.error_message,
            updated_at = EXCLUDED.updated_at`,
        s.SagaID, s.OrderID, s.UserID, s.TotalAmount, s.Currency, s.State,
        s.PaymentID, s.ReservationID, s.ShipmentID, completedStepsJSON,
        s.ErrorMessage, s.CreatedAt, s.UpdatedAt,
    )

    return err
}

func main() {
    db, err := sql.Open("postgres", "postgres://user:pass@localhost/sagas?sslmode=disable")
    if err != nil {
        log.Fatalf("Failed to connect to database: %v", err)
    }
    defer db.Close()

    orchestrator := NewSagaOrchestrator(db)
    ctx := context.Background()

    saga, err := orchestrator.StartSaga(ctx, "order-12345", "user-67890", 9999, "USD")
    if err != nil {
        log.Printf("Saga failed: %v", err)
        log.Printf("Final saga state: %s", saga.State)
    } else {
        log.Printf("Saga completed: %s", saga.SagaID)
    }
}
```

Distributed tracing propagates trace context across service boundaries to reconstruct end-to-end request paths. The W3C Trace Context specification defines standard HTTP headers for trace propagation: `traceparent` encodes the trace ID, parent span ID, and sampling decision, while `tracestate` carries vendor-specific baggage. When Service A calls Service B, A's tracing library injects these headers into the outgoing request. B's library extracts them, creates a child span, and propagates the trace context to any downstream calls.

```go
// Production Distributed Tracing with OpenTelemetry
package main

import (
    "context"
    "fmt"
    "log"
    "net/http"
    "time"

    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.4.0"
    "go.opentelemetry.io/otel/trace"
)

func initTracer(serviceName string) (*sdktrace.TracerProvider, error) {
    // Create Jaeger exporter
    exporter, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint("http://localhost:14268/api/traces")))
    if err != nil {
        return nil, err
    }

    // Create tracer provider
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String(serviceName),
            attribute.String("environment", "production"),
        )),
        sdktrace.WithSampler(sdktrace.AlwaysSample()),
    )

    otel.SetTracerProvider(tp)
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))

    return tp, nil
}

// OrderService - Entry point service
func orderServiceHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    tracer := otel.Tracer("order-service")

    ctx, span := tracer.Start(ctx, "CreateOrder",
        trace.WithAttributes(
            attribute.String("user.id", "user-123"),
            attribute.String("order.id", "order-456"),
        ),
    )
    defer span.End()

    // Simulate order creation logic
    time.Sleep(50 * time.Millisecond)
    span.AddEvent("Order created in database")

    // Call payment service
    if err := callPaymentService(ctx); err != nil {
        span.RecordError(err)
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Call inventory service
    if err := callInventoryService(ctx); err != nil {
        span.RecordError(err)
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    span.SetAttributes(attribute.String("order.status", "completed"))
    w.WriteHeader(http.StatusCreated)
    fmt.Fprintf(w, "Order created successfully")
}

func callPaymentService(ctx context.Context) error {
    tracer := otel.Tracer("order-service")
    ctx, span := tracer.Start(ctx, "CallPaymentService")
    defer span.End()

    // Create HTTP request with trace context propagation
    req, _ := http.NewRequestWithContext(ctx, "POST", "http://localhost:8081/charge", nil)
    client := http.Client{Transport: otelhttp.NewTransport(http.DefaultTransport)}

    resp, err := client.Do(req)
    if err != nil {
        return fmt.Errorf("payment service call failed: %w", err)
    }
    defer resp.Body.Close()

    span.SetAttributes(attribute.Int("http.status_code", resp.StatusCode))

    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("payment failed with status %d", resp.StatusCode)
    }

    return nil
}

func callInventoryService(ctx context.Context) error {
    tracer := otel.Tracer("order-service")
    ctx, span := tracer.Start(ctx, "CallInventoryService")
    defer span.End()

    req, _ := http.NewRequestWithContext(ctx, "POST", "http://localhost:8082/reserve", nil)
    client := http.Client{Transport: otelhttp.NewTransport(http.DefaultTransport)}

    resp, err := client.Do(req)
    if err != nil {
        return fmt.Errorf("inventory service call failed: %w", err)
    }
    defer resp.Body.Close()

    span.SetAttributes(attribute.Int("http.status_code", resp.StatusCode))

    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("inventory reservation failed with status %d", resp.StatusCode)
    }

    return nil
}

// PaymentService - Downstream service
func paymentServiceHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    tracer := otel.Tracer("payment-service")

    ctx, span := tracer.Start(ctx, "ChargePayment")
    defer span.End()

    // Simulate payment processing
    time.Sleep(100 * time.Millisecond)
    span.AddEvent("Payment gateway called")

    // Simulate database write
    time.Sleep(20 * time.Millisecond)
    span.AddEvent("Payment record saved")

    span.SetAttributes(
        attribute.String("payment.id", "pay-789"),
        attribute.String("payment.status", "completed"),
    )

    w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, "Payment charged successfully")
}

// InventoryService - Downstream service
func inventoryServiceHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    tracer := otel.Tracer("inventory-service")

    ctx, span := tracer.Start(ctx, "ReserveInventory")
    defer span.End()

    // Simulate inventory check
    time.Sleep(75 * time.Millisecond)
    span.AddEvent("Inventory checked")

    // Simulate reservation
    time.Sleep(25 * time.Millisecond)
    span.AddEvent("Inventory reserved")

    span.SetAttributes(
        attribute.String("reservation.id", "res-321"),
        attribute.Int("quantity", 2),
    )

    w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, "Inventory reserved successfully")
}

func main() {
    // Initialize tracing for order service
    tp, err := initTracer("order-service")
    if err != nil {
        log.Fatalf("Failed to initialize tracer: %v", err)
    }
    defer tp.Shutdown(context.Background())

    // Start order service
    go func() {
        mux := http.NewServeMux()
        mux.Handle("/order", otelhttp.NewHandler(http.HandlerFunc(orderServiceHandler), "CreateOrder"))
        log.Println("Order service listening on :8080")
        http.ListenAndServe(":8080", mux)
    }()

    // Start payment service
    go func() {
        tp2, _ := initTracer("payment-service")
        defer tp2.Shutdown(context.Background())

        mux := http.NewServeMux()
        mux.Handle("/charge", otelhttp.NewHandler(http.HandlerFunc(paymentServiceHandler), "ChargePayment"))
        log.Println("Payment service listening on :8081")
        http.ListenAndServe(":8081", mux)
    }()

    // Start inventory service
    tp3, _ := initTracer("inventory-service")
    defer tp3.Shutdown(context.Background())

    mux := http.NewServeMux()
    mux.Handle("/reserve", otelhttp.NewHandler(http.HandlerFunc(inventoryServiceHandler), "ReserveInventory"))
    log.Println("Inventory service listening on :8082")
    log.Fatal(http.ListenAndServe(":8082", mux))
}
```

## 3. High-Performance Optimization & Failure Modes

Performance optimization in microservices architectures requires reasoning about latency budgets across the entire call chain. When the API gateway has a 500ms timeout for client requests, and the gateway calls Service A which calls Service B which calls Service C, each service's latency budget must be strictly smaller than the upstream timeout. If each service takes 100ms, the total latency is 300ms, leaving 200ms headroom for network delays and retries. Latency percentiles matter more than averages: a single slow request (P99 latency) can block client requests if services use synchronous request-response patterns without timeouts.

Connection pooling and HTTP/2 multiplexing dramatically improve throughput by amortizing TCP handshake and TLS negotiation costs across many requests. HTTP/1.1 requires a separate TCP connection for each concurrent request, quickly exhausting client and server file descriptor limits. HTTP/2 multiplexes multiple request-response streams over a single TCP connection, eliminating head-of-line blocking and reducing connection overhead. gRPC's use of HTTP/2 provides these benefits automatically. For HTTP/1.1 services, implementing connection pools with configurable min and max connection counts prevents connection exhaustion under load.

Circuit breakers prevent cascading failures by failing fast when downstream dependencies become unhealthy. A circuit breaker tracks the success and failure rates of calls to a downstream service. When failures exceed a threshold (e.g., 50% of requests in the last 10 seconds), the circuit trips to the open state and immediately rejects subsequent requests without invoking the failing service. This gives the downstream service time to recover without being overwhelmed by retry storms. After a timeout period (e.g., 30 seconds), the circuit enters half-open state and allows a small number of test requests through. If they succeed, the circuit closes and normal traffic resumes. If they fail, the circuit re-opens.

```go
// Production Circuit Breaker Implementation
package main

import (
    "context"
    "errors"
    "sync"
    "time"
)

type CircuitState int

const (
    StateClosed CircuitState = iota
    StateOpen
    StateHalfOpen
)

type CircuitBreaker struct {
    maxFailures      int
    timeout          time.Duration
    halfOpenRequests int

    state         CircuitState
    failures      int
    successes     int
    lastFailTime  time.Time
    mu            sync.RWMutex
}

func NewCircuitBreaker(maxFailures int, timeout time.Duration, halfOpenRequests int) *CircuitBreaker {
    return &CircuitBreaker{
        maxFailures:      maxFailures,
        timeout:          timeout,
        halfOpenRequests: halfOpenRequests,
        state:            StateClosed,
    }
}

var ErrCircuitOpen = errors.New("circuit breaker is open")

func (cb *CircuitBreaker) Call(ctx context.Context, fn func(context.Context) error) error {
    if !cb.allowRequest() {
        return ErrCircuitOpen
    }

    err := fn(ctx)

    if err != nil {
        cb.recordFailure()
        return err
    }

    cb.recordSuccess()
    return nil
}

func (cb *CircuitBreaker) allowRequest() bool {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    switch cb.state {
    case StateClosed:
        return true

    case StateOpen:
        // Check if timeout has elapsed
        if time.Since(cb.lastFailTime) > cb.timeout {
            cb.state = StateHalfOpen
            cb.successes = 0
            cb.failures = 0
            return true
        }
        return false

    case StateHalfOpen:
        // Allow limited requests in half-open state
        return cb.successes+cb.failures < cb.halfOpenRequests

    default:
        return false
    }
}

func (cb *CircuitBreaker) recordSuccess() {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    cb.successes++

    if cb.state == StateHalfOpen {
        // If enough successful requests, close the circuit
        if cb.successes >= cb.halfOpenRequests {
            cb.state = StateClosed
            cb.failures = 0
            cb.successes = 0
        }
    }
}

func (cb *CircuitBreaker) recordFailure() {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    cb.failures++
    cb.lastFailTime = time.Now()

    if cb.state == StateHalfOpen {
        // Any failure in half-open state re-opens the circuit
        cb.state = StateOpen
        return
    }

    if cb.failures >= cb.maxFailures {
        cb.state = StateOpen
    }
}

func (cb *CircuitBreaker) State() CircuitState {
    cb.mu.RLock()
    defer cb.mu.RUnlock()
    return cb.state
}
```

Rate limiting protects services from overload by rejecting requests that exceed configured throughput thresholds. Token bucket and leaky bucket algorithms provide smooth rate limiting with burst tolerance. A token bucket accumulates tokens at a steady rate up to a maximum capacity. Each request consumes one token. When the bucket is empty, requests are rejected. This allows burst traffic up to the bucket capacity while enforcing a long-term average rate. Distributed rate limiting requires shared state, typically implemented with Redis using Lua scripts to atomically check and decrement counters.

```go
// Production Token Bucket Rate Limiter with Redis
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/go-redis/redis/v8"
)

type RateLimiter struct {
    client      *redis.Client
    maxTokens   int64
    refillRate  float64 // tokens per second
}

func NewRateLimiter(client *redis.Client, maxTokens int64, refillRate float64) *RateLimiter {
    return &RateLimiter{
        client:     client,
        maxTokens:  maxTokens,
        refillRate: refillRate,
    }
}

// Lua script for atomic token bucket rate limiting
const tokenBucketScript = `
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or max_tokens
local last_refill = tonumber(bucket[2]) or now

-- Calculate tokens to add based on elapsed time
local elapsed = now - last_refill
local tokens_to_add = elapsed * refill_rate
tokens = math.min(max_tokens, tokens + tokens_to_add)

-- Check if enough tokens available
if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 3600)
    return {1, tokens}
else
    return {0, tokens}
end
`

func (rl *RateLimiter) Allow(ctx context.Context, key string, requested int64) (bool, error) {
    now := float64(time.Now().UnixNano()) / 1e9

    result, err := rl.client.Eval(ctx, tokenBucketScript,
        []string{fmt.Sprintf("ratelimit:%s", key)},
        rl.maxTokens, rl.refillRate, requested, now,
    ).Result()

    if err != nil {
        return false, err
    }

    resultSlice := result.([]interface{})
    allowed := resultSlice[0].(int64) == 1

    return allowed, nil
}

func main() {
    client := redis.NewClient(&redis.Options{
        Addr: "localhost:6379",
    })

    limiter := NewRateLimiter(client, 100, 10.0) // 100 token capacity, 10 tokens/sec refill

    ctx := context.Background()

    // Simulate requests
    for i := 0; i < 120; i++ {
        allowed, err := limiter.Allow(ctx, "user:123", 1)
        if err != nil {
            fmt.Printf("Error: %v\n", err)
            continue
        }

        if allowed {
            fmt.Printf("Request %d: allowed\n", i+1)
        } else {
            fmt.Printf("Request %d: rate limited\n", i+1)
        }

        time.Sleep(50 * time.Millisecond)
    }
}
```

Bulkhead isolation limits the blast radius of failures by partitioning resources. Thread pool bulkheads allocate separate thread pools for calls to different downstream services. If the recommendation service becomes slow and exhausts its thread pool, other services remain unaffected. Connection pool bulkheads allocate separate database connection pools for different query types. Read-only queries use one pool, write queries use another, preventing slow reporting queries from blocking transactional writes. The pattern extends to compute resources in Kubernetes: resource requests and limits enforce CPU and memory isolation between pods, preventing resource-hungry services from starving others.

```yaml
# Kubernetes Resource Limits for Bulkhead Isolation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment-service
        image: payment-service:v1.2.3
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        resources:
          requests:
            cpu: "500m"      # Guaranteed CPU allocation
            memory: "512Mi"  # Guaranteed memory allocation
          limits:
            cpu: "1000m"     # Maximum CPU (1 core)
            memory: "1Gi"    # Maximum memory (OOM kill if exceeded)
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        env:
        - name: DB_CONNECTION_POOL_SIZE
          value: "20"
        - name: DOWNSTREAM_SERVICE_TIMEOUT
          value: "5s"
        - name: CIRCUIT_BREAKER_THRESHOLD
          value: "5"
```

Retry policies must distinguish between transient and permanent failures. Network timeouts, DNS resolution failures, and HTTP 503 Service Unavailable responses are typically transient and warrant retries. HTTP 400 Bad Request and 404 Not Found indicate client errors that won't be fixed by retrying. Exponential backoff with jitter prevents retry storms: the first retry occurs after 1 second, the second after 2 seconds, the third after 4 seconds, with random jitter (±25%) to desynchronize clients. Retries without backoff overwhelm recovering services, prolonging outages. The maximum retry count and total timeout must respect upstream latency budgets.

Idempotency tokens enable safe retries for non-idempotent operations. When a client creates a payment, it generates a unique idempotency token (typically a UUID) and includes it in the request. The payment service records the token alongside the payment record. If the client retries with the same token, the service detects the duplicate and returns the existing payment result instead of charging twice. The token must be stored durably before processing the request and checked atomically with request processing to avoid race conditions.

```go
// Production Retry Policy with Exponential Backoff and Jitter
package main

import (
    "context"
    "fmt"
    "math"
    "math/rand"
    "time"
)

type RetryPolicy struct {
    maxAttempts int
    initialDelay time.Duration
    maxDelay     time.Duration
    multiplier   float64
    jitter       float64
}

func NewRetryPolicy(maxAttempts int, initialDelay, maxDelay time.Duration) *RetryPolicy {
    return &RetryPolicy{
        maxAttempts:  maxAttempts,
        initialDelay: initialDelay,
        maxDelay:     maxDelay,
        multiplier:   2.0,
        jitter:       0.25,
    }
}

func (p *RetryPolicy) Execute(ctx context.Context, fn func(context.Context) error, isRetryable func(error) bool) error {
    var lastErr error

    for attempt := 0; attempt < p.maxAttempts; attempt++ {
        err := fn(ctx)

        if err == nil {
            return nil
        }

        lastErr = err

        // Check if error is retryable
        if !isRetryable(err) {
            return fmt.Errorf("non-retryable error: %w", err)
        }

        // Check context cancellation
        if ctx.Err() != nil {
            return ctx.Err()
        }

        // Last attempt, don't sleep
        if attempt == p.maxAttempts-1 {
            break
        }

        // Calculate backoff with exponential growth and jitter
        backoff := p.calculateBackoff(attempt)
        
        fmt.Printf("Attempt %d failed, retrying in %v\n", attempt+1, backoff)

        select {
        case <-time.After(backoff):
            // Continue to next retry
        case <-ctx.Done():
            return ctx.Err()
        }
    }

    return fmt.Errorf("max retry attempts exceeded: %w", lastErr)
}

func (p *RetryPolicy) calculateBackoff(attempt int) time.Duration {
    // Exponential backoff: initialDelay * multiplier^attempt
    backoff := float64(p.initialDelay) * math.Pow(p.multiplier, float64(attempt))
    
    // Cap at maxDelay
    if backoff > float64(p.maxDelay) {
        backoff = float64(p.maxDelay)
    }

    // Add jitter: ±25% randomness
    jitterAmount := backoff * p.jitter
    jitter := (rand.Float64() * 2 - 1) * jitterAmount
    backoff += jitter

    return time.Duration(backoff)
}

func main() {
    policy := NewRetryPolicy(5, 1*time.Second, 30*time.Second)
    
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
    defer cancel()

    // Example: retry a network call
    err := policy.Execute(ctx,
        func(ctx context.Context) error {
            // Simulate transient failure
            if rand.Float64() < 0.7 {
                return fmt.Errorf("temporary network error")
            }
            fmt.Println("Success!")
            return nil
        },
        func(err error) bool {
            // Retry on network errors, don't retry on validation errors
            return err.Error() == "temporary network error"
        },
    )

    if err != nil {
        fmt.Printf("Operation failed: %v\n", err)
    }
}
```

Service decomposition boundaries determine the operational complexity and failure modes of the entire system. Conway's Law observes that system architecture mirrors the organizational structure that produced it. Teams organized around business capabilities naturally produce service boundaries aligned with bounded contexts. Cross-functional teams that own services end-to-end—from development through operations—internalize the operational cost of their architectural decisions. Teams that hand off services to separate operations groups optimize for development velocity at the expense of operational stability.

The domain-driven design bounded context provides rigorous heuristics for service boundaries. A bounded context encapsulates a cohesive domain model with consistent terminology, invariants, and business rules. The "Customer" concept means different things in the sales context versus the support context: sales cares about purchase history and sales pipeline, support cares about support tickets and contract terms. Forcing a single unified Customer model creates coupling and complexity. Splitting them into separate bounded contexts—and therefore separate services—enables independent evolution and team ownership. Service boundaries should align with aggregate roots that maintain invariants: the Order aggregate maintains the invariant that order total equals the sum of line item prices, so the order service owns all order data and ensures consistency.

Data ownership and consistency boundaries are inseparable from service boundaries. Each service must own its data exclusively, accessed only through the service's API. Sharing databases across services creates tight coupling: schema changes require coordination, query patterns leak across boundaries, and transaction semantics become undefined. The database becomes a distributed system integration point, the worst possible choice because databases were not designed for this role. Services may replicate data from other services through event-driven synchronization, creating eventually consistent read replicas. The source service publishes events when data changes; consumers maintain local copies optimized for their query patterns.

Eventual consistency is not a compromise but a recognition of distributed system reality. Strict consistency across service boundaries requires distributed transactions—two-phase commit or Paxos consensus—which sacrifice availability and latency. The CAP theorem proves this tradeoff is unavoidable. Eventual consistency acknowledges that different services will have different views of the system state at any given moment, but guarantees they will converge to a consistent state if updates stop. This model aligns with business reality: inventory counts, account balances, and recommendation scores are always stale approximations. Designing services to tolerate stale data and resolve conflicts when they arise produces more resilient systems than pretending real-time consistency is achievable.

The transactional outbox pattern solves the dual-write problem where a service must atomically update its database and publish an event. Without atomicity, either the database update succeeds and event publishing fails (lost event), or event publishing succeeds and the database update fails (phantom event). The outbox pattern performs both operations in a single local transaction: insert the event into an "outbox" table in the same database as the business data. A separate background process polls the outbox table, publishes events to the message broker, and marks them as published. This guarantees that every committed database change produces exactly one event, transforming at-most-once publishing into at-least-once publishing. Combined with consumer idempotency, this achieves exactly-once end-to-end semantics.

```go
// Production Transactional Outbox Pattern Implementation
package main

import (
    "context"
    "database/sql"
    "encoding/json"
    "fmt"
    "log"
    "time"

    "github.com/IBM/sarama"
    "github.com/google/uuid"
    _ "github.com/lib/pq"
)

type OutboxEvent struct {
    ID        string
    EventType string
    Payload   json.RawMessage
    CreatedAt time.Time
    Published bool
}

type OrderService struct {
    db       *sql.DB
    producer sarama.SyncProducer
}

func NewOrderService(db *sql.DB, producer sarama.SyncProducer) *OrderService {
    return &OrderService{db: db, producer: producer}
}

// CreateOrder atomically writes to database and outbox
func (s *OrderService) CreateOrder(ctx context.Context, userID string, totalAmount int64) (string, error) {
    tx, err := s.db.BeginTx(ctx, nil)
    if err != nil {
        return "", fmt.Errorf("failed to begin transaction: %w", err)
    }
    defer tx.Rollback()

    // Insert order into orders table
    orderID := uuid.New().String()
    _, err = tx.ExecContext(ctx,
        "INSERT INTO orders (order_id, user_id, total_amount, status, created_at) VALUES ($1, $2, $3, $4, $5)",
        orderID, userID, totalAmount, "PENDING", time.Now(),
    )
    if err != nil {
        return "", fmt.Errorf("failed to create order: %w", err)
    }

    // Create event payload
    eventPayload := map[string]interface{}{
        "order_id":     orderID,
        "user_id":      userID,
        "total_amount": totalAmount,
        "timestamp":    time.Now(),
    }
    payloadJSON, _ := json.Marshal(eventPayload)

    // Insert event into outbox table (same transaction)
    eventID := uuid.New().String()
    _, err = tx.ExecContext(ctx,
        "INSERT INTO outbox (id, event_type, payload, created_at, published) VALUES ($1, $2, $3, $4, $5)",
        eventID, "order.created", payloadJSON, time.Now(), false,
    )
    if err != nil {
        return "", fmt.Errorf("failed to insert outbox event: %w", err)
    }

    // Commit transaction (both order and outbox event committed atomically)
    if err := tx.Commit(); err != nil {
        return "", fmt.Errorf("failed to commit transaction: %w", err)
    }

    log.Printf("Order %s created with outbox event %s", orderID, eventID)
    return orderID, nil
}

// OutboxPublisher polls outbox table and publishes events
type OutboxPublisher struct {
    db       *sql.DB
    producer sarama.SyncProducer
    interval time.Duration
}

func NewOutboxPublisher(db *sql.DB, producer sarama.SyncProducer, interval time.Duration) *OutboxPublisher {
    return &OutboxPublisher{
        db:       db,
        producer: producer,
        interval: interval,
    }
}

func (p *OutboxPublisher) Start(ctx context.Context) error {
    ticker := time.NewTicker(p.interval)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-ticker.C:
            if err := p.publishPendingEvents(ctx); err != nil {
                log.Printf("Error publishing events: %v", err)
            }
        }
    }
}

func (p *OutboxPublisher) publishPendingEvents(ctx context.Context) error {
    // Query unpublished events
    rows, err := p.db.QueryContext(ctx,
        "SELECT id, event_type, payload FROM outbox WHERE published = false ORDER BY created_at LIMIT 100",
    )
    if err != nil {
        return err
    }
    defer rows.Close()

    var publishedIDs []string

    for rows.Next() {
        var event OutboxEvent
        if err := rows.Scan(&event.ID, &event.EventType, &event.Payload); err != nil {
            log.Printf("Failed to scan event: %v", err)
            continue
        }

        // Publish to Kafka
        msg := &sarama.ProducerMessage{
            Topic: "order-events",
            Key:   sarama.StringEncoder(event.ID),
            Value: sarama.ByteEncoder(event.Payload),
            Headers: []sarama.RecordHeader{
                {Key: []byte("event_type"), Value: []byte(event.EventType)},
                {Key: []byte("event_id"), Value: []byte(event.ID)},
            },
        }

        partition, offset, err := p.producer.SendMessage(msg)
        if err != nil {
            log.Printf("Failed to publish event %s: %v", event.ID, err)
            continue
        }

        log.Printf("Published event %s to partition %d offset %d", event.ID, partition, offset)
        publishedIDs = append(publishedIDs, event.ID)
    }

    // Mark events as published
    if len(publishedIDs) > 0 {
        placeholders := ""
        args := make([]interface{}, len(publishedIDs))
        for i, id := range publishedIDs {
            if i > 0 {
                placeholders += ","
            }
            placeholders += fmt.Sprintf("$%d", i+1)
            args[i] = id
        }

        query := fmt.Sprintf("UPDATE outbox SET published = true WHERE id IN (%s)", placeholders)
        _, err = p.db.ExecContext(ctx, query, args...)
        if err != nil {
            return fmt.Errorf("failed to mark events as published: %w", err)
        }
    }

    return nil
}

func main() {
    // Initialize database
    db, err := sql.Open("postgres", "postgres://user:pass@localhost/orders?sslmode=disable")
    if err != nil {
        log.Fatalf("Failed to connect to database: %v", err)
    }
    defer db.Close()

    // Initialize Kafka producer
    config := sarama.NewConfig()
    config.Producer.RequiredAcks = sarama.WaitForAll
    config.Producer.Return.Successes = true
    producer, err := sarama.NewSyncProducer([]string{"localhost:9092"}, config)
    if err != nil {
        log.Fatalf("Failed to create producer: %v", err)
    }
    defer producer.Close()

    // Create order service
    orderService := NewOrderService(db, producer)

    // Create order (writes to database and outbox atomically)
    ctx := context.Background()
    orderID, err := orderService.CreateOrder(ctx, "user-123", 9999)
    if err != nil {
        log.Fatalf("Failed to create order: %v", err)
    }
    log.Printf("Created order: %s", orderID)

    // Start outbox publisher (publishes events from outbox to Kafka)
    publisher := NewOutboxPublisher(db, producer, 5*time.Second)
    if err := publisher.Start(ctx); err != nil {
        log.Fatalf("Outbox publisher error: %v", err)
    }
}
```

Service mesh observability provides unified telemetry across all services without code instrumentation. Sidecar proxies intercept every network request, recording latency, status codes, and byte counts. They export metrics in Prometheus format, aggregate them in the mesh control plane, and expose them through visualization tools like Grafana. Distributed traces are automatically correlated by injecting and propagating trace context headers. Access logs capture every request with structured fields, enabling log aggregation and analysis with tools like Elasticsearch and Kibana. This comprehensive observability layer makes invisible service-to-service interactions visible and debuggable.

The final lesson of microservices orchestration is that operational maturity requirements increase proportionally with architectural complexity. A monolith with poor observability is debuggable with a debugger attached to the running process. A microservices system with poor observability is an indecipherable black box where failures propagate invisibly and root causes remain permanently mysterious. Distributed tracing, structured logging, metric aggregation, and comprehensive testing are not optional niceties but existential requirements. Teams that adopt microservices without investing in operational tooling discover that the architectural benefits are overwhelmed by the operational burden.
