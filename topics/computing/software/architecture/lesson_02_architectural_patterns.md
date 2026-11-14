# Lesson 2: Architectural Patterns

## 1. First-Principles Intuition & Invariants

Software architecture exists because complexity compounds non-linearly. A system with ten components has forty-five possible interaction pairs; a system with one hundred components has nearly five thousand. Without deliberate structural organization, the cognitive load of understanding dependencies, failure modes, and change impact becomes intractable. Architectural patterns emerge as formalized solutions to recurring structural problems, encoding decades of industry experience into reusable templates that constrain system topology in ways that manage this complexity.

At the foundational level, all architectural patterns solve a single root problem: how to partition a system's responsibilities such that modules remain comprehensible, testable, and evolvable in isolation while still cooperating to deliver end-to-end functionality. This partitioning challenge manifests across multiple dimensions. The first is coupling, which measures the degree to which one module depends on the internal implementation details of another. High coupling means changes ripple across boundaries, forcing parallel modifications and increasing the probability of regression. The second is cohesion, which measures whether a module's responsibilities form a conceptually unified whole. Low cohesion produces modules that do too many unrelated things, making them difficult to reason about and reuse. The third is abstraction stability, which governs whether the contracts between modules remain consistent even as internal implementations evolve. Unstable abstractions leak implementation details across boundaries, turning the entire system into a monolithic entity regardless of how many files or services it comprises.

The canonical architectural patterns—Layered, Hexagonal, Microservices, and Event-Driven—each enforce different strategies for managing these dimensions. They are not mutually exclusive taxonomies but rather complementary lenses that emphasize different trade-offs. A production system often exhibits multiple patterns simultaneously: a layered structure within a single service, hexagonal boundaries at the service periphery, microservice decomposition across teams, and event-driven integration between domains. Understanding each pattern's invariants and failure modes allows engineers to compose them deliberately rather than allowing architecture to emerge accidentally through incremental feature additions.

The Layered pattern enforces a strict acyclic dependency graph where higher layers depend on lower layers but never the reverse. This unidirectional flow creates a conceptual hierarchy—presentation depends on business logic, which depends on data access, which depends on the operating system kernel. The invariant is that dependencies point downward through the stack. When this invariant holds, you can replace any layer's implementation without affecting layers above it, provided the interface remains stable. When it breaks—when a lower layer imports types or calls functions from a higher layer—you create a circular dependency that prevents independent testing and deployment.

The Hexagonal pattern, also known as Ports and Adapters, inverts the traditional layered model by placing business logic at the center and treating all external systems—databases, message queues, HTTP endpoints, file systems—as interchangeable peripherals accessed through abstract interfaces. The invariant is that the core domain never imports concrete infrastructure. Instead, it defines ports (interfaces) that describe what operations it needs, and adapters (implementations) fulfill those contracts by translating between the domain's vocabulary and the external system's protocol. This inversion enables pure unit testing of business logic without mock databases or embedded servers, because the core has no knowledge of persistence mechanisms or transport layers.

The Microservices pattern decomposes a system into independently deployable services, each owning a bounded context within the overall domain model. The invariant is that inter-service communication occurs exclusively through network calls—no shared databases, no in-process function calls, no shared memory. This physical isolation forces explicit contracts and enables independent scaling, technology choices, and deployment cadences per service. The cost is operational complexity: distributed transactions become impossible without sagas or compensating transactions, network failures inject latency and partial failure modes, and debugging requires distributed tracing across process boundaries.

The Event-Driven pattern structures systems around immutable facts that have already occurred, rather than imperative commands requesting actions. Producers emit events to a durable log or message broker, and consumers react asynchronously by updating their local state or emitting derived events. The invariant is temporal decoupling: producers do not block waiting for consumers, and consumers do not need to know which producer emitted an event. This yields extreme scalability and resilience, because the event log absorbs load spikes and allows consumers to process at their own pace. The trade-off is eventual consistency—reads may observe stale data until all consumers have processed recent events—and debugging becomes an exercise in reconstructing causality from asynchronous message flows.

Each pattern encodes a different set of priorities. Layered architectures prioritize simplicity and cognitive familiarity, making them ideal for teams inheriting legacy codebases or building CRUD applications where scalability and independent deployment are not primary concerns. Hexagonal architectures prioritize testability and domain model purity, making them essential for systems with complex business rules that must remain correct across technology migrations. Microservices prioritize organizational scalability and deployment independence, making them suitable for large engineering organizations where teams need autonomy and the ability to ship features without coordinating releases. Event-driven architectures prioritize throughput and decoupling, making them necessary for high-scale systems processing millions of transactions per second or integrating heterogeneous systems with incompatible availability windows.

The critical realization is that architectural patterns are not aesthetic preferences but engineering decisions with measurable consequences for latency, throughput, fault tolerance, and development velocity. Choosing a pattern means accepting its invariants and mitigations for its failure modes. The remainder of this lesson dissects each pattern's internal mechanics and provides production-grade implementations that expose the trade-offs concretely.

## 2. Core Architecture & Mechanics

### Layered Architecture: Acyclic Dependency Graphs and Transitive Closure

The Layered pattern organizes code into horizontal strata where each layer provides services to the layer above and consumes services from the layer below. The most common instantiation is the three-tier model: presentation, business logic, and data access. In a typical web application, the presentation layer handles HTTP request parsing and response serialization, the business logic layer validates invariants and orchestrates domain operations, and the data access layer translates domain entities into SQL queries and result set mappings.

The enforcement mechanism is dependency direction. Consider a Java-based e-commerce system with strict package visibility rules. The presentation layer resides in `com.example.web`, business logic in `com.example.domain`, and data access in `com.example.persistence`. The `web` package imports types from `domain`, and `domain` imports types from `persistence`, but `persistence` has zero imports from `domain` or `web`. This dependency graph forms a directed acyclic graph (DAG) that prevents circular references.

```java
// com.example.web.OrderController.java
package com.example.web;

import com.example.domain.OrderService;
import com.example.domain.Order;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public OrderResponse createOrder(@RequestBody CreateOrderRequest request) {
        Order order = orderService.placeOrder(
            request.getCustomerId(),
            request.getItems()
        );
        return new OrderResponse(order.getId(), order.getTotal());
    }
}
```

The controller depends on the `OrderService` abstraction from the domain layer but has no knowledge of how orders are persisted. It constructs domain value objects from HTTP request payloads and delegates orchestration to the service layer.

```java
// com.example.domain.OrderService.java
package com.example.domain;

import com.example.persistence.OrderRepository;
import java.util.List;
import java.math.BigDecimal;

public class OrderService {
    private final OrderRepository repository;
    private final PricingEngine pricingEngine;

    public OrderService(OrderRepository repository, PricingEngine pricingEngine) {
        this.repository = repository;
        this.pricingEngine = pricingEngine;
    }

    public Order placeOrder(long customerId, List<OrderItem> items) {
        if (items.isEmpty()) {
            throw new IllegalArgumentException("Order must contain at least one item");
        }

        BigDecimal total = pricingEngine.calculateTotal(items);
        Order order = new Order(customerId, items, total);
        
        repository.save(order);
        return order;
    }
}
```

The service layer enforces business invariants—orders cannot be empty—and coordinates cross-cutting concerns like pricing calculation. It depends on the `OrderRepository` interface but does not reference concrete database implementations.

```java
// com.example.persistence.OrderRepository.java
package com.example.persistence;

import com.example.domain.Order;

public interface OrderRepository {
    void save(Order order);
    Order findById(long orderId);
}
```

```java
// com.example.persistence.JdbcOrderRepository.java
package com.example.persistence;

import com.example.domain.Order;
import org.springframework.jdbc.core.JdbcTemplate;

public class JdbcOrderRepository implements OrderRepository {
    private final JdbcTemplate jdbc;

    public JdbcOrderRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public void save(Order order) {
        jdbc.update(
            "INSERT INTO orders (customer_id, total, created_at) VALUES (?, ?, ?)",
            order.getCustomerId(),
            order.getTotal(),
            order.getCreatedAt()
        );
    }

    @Override
    public Order findById(long orderId) {
        return jdbc.queryForObject(
            "SELECT customer_id, total, created_at FROM orders WHERE id = ?",
            (rs, rowNum) -> new Order(
                rs.getLong("customer_id"),
                rs.getBigDecimal("total"),
                rs.getTimestamp("created_at")
            ),
            orderId
        );
    }
}
```

The data access layer translates domain entities into SQL statements and reconstructs entities from result sets. It depends on JDBC types but has no knowledge of HTTP controllers or request validation logic. This unidirectional dependency flow means you can replace `JdbcOrderRepository` with a MongoDB implementation or an in-memory fake without modifying the service or controller layers.

The failure mode occurs when developers shortcut the layer boundaries to avoid "unnecessary indirection." A common anti-pattern is accessing the repository directly from the controller to avoid adding a method to the service layer. This creates a maintenance trap: business logic that should be centralized in the service layer becomes scattered across multiple controllers, making it impossible to enforce invariants consistently. Another failure mode is leaking database-specific types into the domain layer—returning JDBC `ResultSet` objects or exposing ORM-managed entities with lazy-loading proxies. These types carry transactional and session semantics that cannot be tested in isolation, forcing integration tests for every business rule.

### Hexagonal Architecture: Inversion of Control and Dependency Injection

The Hexagonal pattern restructures the dependency graph by placing the domain model at the center and treating all external systems as adapters that conform to domain-defined interfaces. Instead of the domain depending on infrastructure, infrastructure depends on domain abstractions. This inversion enables testing business logic without booting a database or web server.

Consider a payment processing system where the core domain models a `PaymentGateway` interface that the business logic requires, but the concrete implementation might be Stripe, PayPal, or a test double.

```rust
// domain/mod.rs
pub mod payment;

use std::error::Error;

#[derive(Debug, Clone)]
pub struct PaymentRequest {
    pub amount_cents: u64,
    pub currency: String,
    pub customer_id: String,
}

#[derive(Debug, Clone)]
pub struct PaymentResult {
    pub transaction_id: String,
    pub status: PaymentStatus,
}

#[derive(Debug, Clone, PartialEq)]
pub enum PaymentStatus {
    Approved,
    Declined,
    PendingReview,
}

pub trait PaymentGateway: Send + Sync {
    fn charge(&self, request: &PaymentRequest) -> Result<PaymentResult, Box<dyn Error>>;
}
```

The domain defines the contract in its own vocabulary—`PaymentRequest`, `PaymentResult`, `PaymentStatus`—without referencing HTTP status codes, JSON serialization, or Stripe SDK types. Business logic depends only on this trait.

```rust
// domain/payment.rs
use super::{PaymentGateway, PaymentRequest, PaymentResult, PaymentStatus};
use std::error::Error;

pub struct PaymentService {
    gateway: Box<dyn PaymentGateway>,
    min_charge_cents: u64,
}

impl PaymentService {
    pub fn new(gateway: Box<dyn PaymentGateway>, min_charge_cents: u64) -> Self {
        Self { gateway, min_charge_cents }
    }

    pub fn process_payment(&self, request: &PaymentRequest) -> Result<PaymentResult, Box<dyn Error>> {
        if request.amount_cents < self.min_charge_cents {
            return Err(format!(
                "Amount {} cents below minimum {}",
                request.amount_cents, self.min_charge_cents
            ).into());
        }

        let result = self.gateway.charge(request)?;

        if result.status == PaymentStatus::Approved {
            // Emit domain event, update audit log, etc.
            println!("Payment approved: {}", result.transaction_id);
        }

        Ok(result)
    }
}
```

The service enforces business rules—minimum charge amounts—and coordinates side effects like audit logging. It has zero knowledge of whether the gateway is implemented via HTTP calls to Stripe or an in-memory fake.

Now implement the adapter layer that translates between the domain vocabulary and the external API's protocol.

```rust
// adapters/stripe.rs
use crate::domain::{PaymentGateway, PaymentRequest, PaymentResult, PaymentStatus};
use std::error::Error;
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};

pub struct StripeAdapter {
    client: Client,
    api_key: String,
    base_url: String,
}

#[derive(Serialize)]
struct StripeChargeRequest {
    amount: u64,
    currency: String,
    customer: String,
}

#[derive(Deserialize)]
struct StripeChargeResponse {
    id: String,
    status: String,
}

impl StripeAdapter {
    pub fn new(api_key: String) -> Self {
        Self {
            client: Client::new(),
            api_key,
            base_url: "https://api.stripe.com/v1".to_string(),
        }
    }
}

impl PaymentGateway for StripeAdapter {
    fn charge(&self, request: &PaymentRequest) -> Result<PaymentResult, Box<dyn Error>> {
        let stripe_request = StripeChargeRequest {
            amount: request.amount_cents,
            currency: request.currency.clone(),
            customer: request.customer_id.clone(),
        };

        let response = self.client
            .post(&format!("{}/charges", self.base_url))
            .bearer_auth(&self.api_key)
            .json(&stripe_request)
            .send()?
            .json::<StripeChargeResponse>()?;

        let status = match response.status.as_str() {
            "succeeded" => PaymentStatus::Approved,
            "failed" => PaymentStatus::Declined,
            _ => PaymentStatus::PendingReview,
        };

        Ok(PaymentResult {
            transaction_id: response.id,
            status,
        })
    }
}
```

The Stripe adapter implements the `PaymentGateway` trait by translating `PaymentRequest` into Stripe's JSON schema, making an HTTP POST with bearer authentication, and mapping Stripe's status codes back to domain-level enums. The domain has no dependency on `reqwest`, `serde`, or Stripe SDK types.

For testing, implement a fake adapter that returns deterministic results without network calls.

```rust
// adapters/fake_gateway.rs
use crate::domain::{PaymentGateway, PaymentRequest, PaymentResult, PaymentStatus};
use std::error::Error;

pub struct FakeGateway {
    should_approve: bool,
}

impl FakeGateway {
    pub fn new_approving() -> Self {
        Self { should_approve: true }
    }

    pub fn new_declining() -> Self {
        Self { should_approve: false }
    }
}

impl PaymentGateway for FakeGateway {
    fn charge(&self, request: &PaymentRequest) -> Result<PaymentResult, Box<dyn Error>> {
        let status = if self.should_approve {
            PaymentStatus::Approved
        } else {
            PaymentStatus::Declined
        };

        Ok(PaymentResult {
            transaction_id: format!("fake-txn-{}", request.customer_id),
            status,
        })
    }
}
```

Now write a unit test for the domain logic using the fake gateway.

```rust
// domain/payment.rs (continued)
#[cfg(test)]
mod tests {
    use super::*;
    use crate::adapters::fake_gateway::FakeGateway;

    #[test]
    fn test_minimum_charge_enforcement() {
        let gateway = Box::new(FakeGateway::new_approving());
        let service = PaymentService::new(gateway, 100);

        let request = PaymentRequest {
            amount_cents: 50,
            currency: "USD".to_string(),
            customer_id: "cust_123".to_string(),
        };

        let result = service.process_payment(&request);
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("below minimum"));
    }

    #[test]
    fn test_approved_payment() {
        let gateway = Box::new(FakeGateway::new_approving());
        let service = PaymentService::new(gateway, 100);

        let request = PaymentRequest {
            amount_cents: 500,
            currency: "USD".to_string(),
            customer_id: "cust_456".to_string(),
        };

        let result = service.process_payment(&request).unwrap();
        assert_eq!(result.status, PaymentStatus::Approved);
    }
}
```

These tests run in microseconds because they execute pure business logic without HTTP servers, database connections, or network latency. The hexagonal boundary ensures that domain rules remain testable regardless of infrastructure complexity.

The failure mode occurs when developers violate the dependency inversion principle by allowing the domain to import infrastructure types. For example, if `PaymentService` accepted a `reqwest::Client` parameter instead of a `PaymentGateway` trait, every test would require mocking HTTP responses, and migrating from Stripe to PayPal would require rewriting the service layer. Another anti-pattern is defining ports too close to infrastructure capabilities—creating a `HttpClient` trait with methods like `post(url: String, body: String)` instead of domain-level abstractions like `PaymentGateway`. This forces the domain to know about HTTP semantics, defeating the purpose of the hexagonal boundary.

### Microservices Architecture: Process Isolation and Network Boundaries

The Microservices pattern decomposes a monolithic application into independently deployable services communicating over network protocols. Each service owns a bounded context—a cohesive subset of the domain model—and exposes a stable API while keeping internal data structures private. The enforcement mechanism is process isolation: services cannot share memory or call each other's functions directly, forcing explicit contracts and enabling independent scaling.

Consider an e-commerce platform decomposed into three services: `order-service`, `inventory-service`, and `payment-service`. Each service runs in its own container with a dedicated database and exposes a REST API.

```yaml
# order-service/Dockerfile
FROM rust:1.75 AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/order-service /usr/local/bin/
EXPOSE 8080
CMD ["order-service"]
```

The `order-service` container packages the binary with minimal dependencies and exposes port 8080. Deploy it to Kubernetes with a dedicated PostgreSQL instance.

```yaml
# order-service/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: ecommerce
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:
      - name: order-service
        image: myregistry/order-service:1.0.0
        ports:
        - containerPort: 8080
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: order-db-credentials
              key: url
        - name: INVENTORY_SERVICE_URL
          value: http://inventory-service.ecommerce.svc.cluster.local:8080
        - name: PAYMENT_SERVICE_URL
          value: http://payment-service.ecommerce.svc.cluster.local:8080
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: ecommerce
spec:
  selector:
    app: order-service
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: ClusterIP
```

The deployment spec declares three replicas for horizontal scaling and configures environment variables pointing to the inventory and payment services via Kubernetes DNS. The `Service` resource creates a stable virtual IP that load-balances across the three pods.

The order service orchestrates a distributed transaction by calling inventory and payment services over HTTP.

```rust
// order-service/src/main.rs
use axum::{Router, Json, extract::State, http::StatusCode};
use serde::{Deserialize, Serialize};
use reqwest::Client;
use std::sync::Arc;

#[derive(Clone)]
struct AppState {
    db_pool: sqlx::PgPool,
    inventory_url: String,
    payment_url: String,
    http_client: Client,
}

#[derive(Deserialize)]
struct CreateOrderRequest {
    customer_id: i64,
    items: Vec<OrderItem>,
    payment_token: String,
}

#[derive(Deserialize, Clone)]
struct OrderItem {
    product_id: i64,
    quantity: i32,
}

#[derive(Serialize)]
struct ReserveInventoryRequest {
    items: Vec<OrderItem>,
}

#[derive(Deserialize)]
struct ReserveInventoryResponse {
    reservation_id: String,
    success: bool,
}

#[derive(Serialize)]
struct ChargePaymentRequest {
    amount_cents: i64,
    token: String,
}

#[derive(Deserialize)]
struct ChargePaymentResponse {
    transaction_id: String,
    approved: bool,
}

async fn create_order(
    State(state): State<Arc<AppState>>,
    Json(req): Json<CreateOrderRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    // Step 1: Reserve inventory
    let reserve_response = state.http_client
        .post(&format!("{}/reservations", state.inventory_url))
        .json(&ReserveInventoryRequest { items: req.items.clone() })
        .send()
        .await
        .map_err(|_| StatusCode::SERVICE_UNAVAILABLE)?
        .json::<ReserveInventoryResponse>()
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if !reserve_response.success {
        return Err(StatusCode::CONFLICT);
    }

    // Step 2: Charge payment
    let total_cents = calculate_total(&req.items);
    let payment_response = state.http_client
        .post(&format!("{}/charges", state.payment_url))
        .json(&ChargePaymentRequest {
            amount_cents: total_cents,
            token: req.payment_token.clone(),
        })
        .send()
        .await
        .map_err(|_| StatusCode::SERVICE_UNAVAILABLE)?
        .json::<ChargePaymentResponse>()
        .await
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if !payment_response.approved {
        // Compensating transaction: release inventory reservation
        let _ = state.http_client
            .delete(&format!("{}/reservations/{}", state.inventory_url, reserve_response.reservation_id))
            .send()
            .await;
        return Err(StatusCode::PAYMENT_REQUIRED);
    }

    // Step 3: Persist order
    let order_id = sqlx::query_scalar::<_, i64>(
        "INSERT INTO orders (customer_id, total_cents, payment_txn_id, created_at) 
         VALUES ($1, $2, $3, NOW()) RETURNING id"
    )
    .bind(req.customer_id)
    .bind(total_cents)
    .bind(payment_response.transaction_id)
    .fetch_one(&state.db_pool)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok(Json(serde_json::json!({ "order_id": order_id })))
}

fn calculate_total(items: &[OrderItem]) -> i64 {
    items.iter().map(|i| i.quantity as i64 * 1000).sum() // Simplified pricing
}

#[tokio::main]
async fn main() {
    let db_pool = sqlx::PgPool::connect(&std::env::var("DATABASE_URL").unwrap())
        .await
        .unwrap();

    let state = Arc::new(AppState {
        db_pool,
        inventory_url: std::env::var("INVENTORY_SERVICE_URL").unwrap(),
        payment_url: std::env::var("PAYMENT_SERVICE_URL").unwrap(),
        http_client: Client::new(),
    });

    let app = Router::new()
        .route("/orders", axum::routing::post(create_order))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

This implementation demonstrates the saga pattern for distributed transactions. The order service attempts to reserve inventory, then charge payment, then persist the order. If payment fails, it executes a compensating transaction by releasing the inventory reservation. Each step is an independent HTTP call that can fail due to network partitions, timeouts, or service crashes.

The failure modes are numerous and require deliberate mitigation. Network failures inject partial completion scenarios where inventory is reserved but payment times out, leaving orphaned reservations that must be cleaned up via background jobs with expiration policies. Service crashes mid-transaction require idempotency keys to prevent duplicate charges when clients retry. Cascading failures occur when one slow service causes request queues to back up in dependent services, exhausting connection pools and thread pools. Mitigate this with circuit breakers that stop calling failing services after a threshold of errors, timeouts that fail fast instead of blocking indefinitely, and bulkhead patterns that isolate thread pools per dependency so one slow service cannot starve resources for others.

Distributed tracing becomes mandatory for debugging. Instrument each service to propagate trace context via HTTP headers and emit spans to a collector like Jaeger or Tempo.

```rust
// Add to order-service dependencies in Cargo.toml
// opentelemetry = "0.21"
// opentelemetry-otlp = "0.14"
// tracing-opentelemetry = "0.22"

use opentelemetry::global;
use opentelemetry::trace::{TraceContextExt, Tracer};
use tracing_subscriber::layer::SubscriberExt;

fn init_tracing() {
    let tracer = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(opentelemetry_otlp::new_exporter().tonic())
        .install_batch(opentelemetry::runtime::Tokio)
        .unwrap();

    let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);
    let subscriber = tracing_subscriber::Registry::default().with(telemetry);
    tracing::subscriber::set_global_default(subscriber).unwrap();
}
```

With tracing enabled, a failed order creation emits spans showing latency breakdowns: inventory reservation took 50ms, payment charge timed out after 5s, compensating transaction took 30ms. This observability is impossible in a monolith where failures surface as stack traces in a single process.

### Event-Driven Architecture: Temporal Decoupling and Eventual Consistency

The Event-Driven pattern structures systems around immutable facts rather than imperative commands. Services emit events to a durable log when state changes occur, and other services react asynchronously by updating their local projections. The canonical implementation uses Apache Kafka or NATS JetStream as the event backbone.

Consider a retail system where the order service emits an `OrderPlaced` event when a customer completes checkout. The inventory service consumes this event to decrement stock counts, the shipping service creates a shipment record, and the analytics service updates sales dashboards. None of these consumers block the order service's response to the customer.

Deploy Kafka to Kubernetes using the Strimzi operator.

```yaml
# kafka/kafka-cluster.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: event-cluster
  namespace: events
spec:
  kafka:
    version: 3.6.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
      log.retention.hours: 168
    storage:
      type: jbod
      volumes:
      - id: 0
        type: persistent-claim
        size: 100Gi
        deleteClaim: false
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 10Gi
      deleteClaim: false
  entityOperator:
    topicOperator: {}
    userOperator: {}
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: order-events
  namespace: events
  labels:
    strimzi.io/cluster: event-cluster
spec:
  partitions: 12
  replicas: 3
  config:
    retention.ms: 604800000  # 7 days
    segment.ms: 3600000      # 1 hour
    min.insync.replicas: 2
```

This configuration deploys a three-node Kafka cluster with replication factor 3 and creates an `order-events` topic partitioned across twelve brokers for horizontal scaling. The `min.insync.replicas: 2` setting ensures that writes are acknowledged only after being replicated to at least two brokers, preventing data loss if one broker crashes.

The order service publishes events to Kafka after persisting the order to its local database. Use the transactional outbox pattern to ensure atomicity: write the event to an `outbox` table in the same transaction as the order, then use a background worker to poll the outbox and publish to Kafka.

```rust
// order-service/src/publisher.rs
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::ClientConfig;
use serde::Serialize;
use sqlx::PgPool;

#[derive(Serialize)]
struct OrderPlacedEvent {
    order_id: i64,
    customer_id: i64,
    total_cents: i64,
    items: Vec<OrderItem>,
    timestamp: i64,
}

pub struct EventPublisher {
    producer: FutureProducer,
    db_pool: PgPool,
}

impl EventPublisher {
    pub fn new(brokers: &str, db_pool: PgPool) -> Self {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("acks", "all")
            .set("enable.idempotence", "true")
            .set("max.in.flight.requests.per.connection", "5")
            .create()
            .expect("Failed to create Kafka producer");

        Self { producer, db_pool }
    }

    pub async fn run_outbox_relay(&self) {
        loop {
            let events: Vec<(i64, String, String)> = sqlx::query_as(
                "SELECT id, event_type, payload FROM outbox ORDER BY id LIMIT 100"
            )
            .fetch_all(&self.db_pool)
            .await
            .unwrap_or_default();

            for (id, event_type, payload) in events {
                let record = FutureRecord::to("order-events")
                    .key(&event_type)
                    .payload(&payload);

                if let Ok(_) = self.producer.send(record, std::time::Duration::from_secs(5)).await {
                    sqlx::query("DELETE FROM outbox WHERE id = $1")
                        .bind(id)
                        .execute(&self.db_pool)
                        .await
                        .ok();
                }
            }

            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }
    }
}
```

The outbox relay polls for unprocessed events, publishes them to Kafka with `acks=all` for durability, and deletes them from the outbox upon successful acknowledgment. This decouples event publishing from the critical path of order creation, preventing Kafka outages from blocking customer checkouts.

The inventory service consumes `OrderPlaced` events and updates stock counts atomically.

```rust
// inventory-service/src/consumer.rs
use rdkafka::consumer::{StreamConsumer, Consumer};
use rdkafka::{ClientConfig, Message};
use serde::Deserialize;
use sqlx::PgPool;

#[derive(Deserialize)]
struct OrderPlacedEvent {
    order_id: i64,
    items: Vec<OrderItem>,
}

#[derive(Deserialize)]
struct OrderItem {
    product_id: i64,
    quantity: i32,
}

pub struct InventoryConsumer {
    consumer: StreamConsumer,
    db_pool: PgPool,
}

impl InventoryConsumer {
    pub fn new(brokers: &str, group_id: &str, db_pool: PgPool) -> Self {
        let consumer: StreamConsumer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("group.id", group_id)
            .set("enable.auto.commit", "false")
            .set("auto.offset.reset", "earliest")
            .create()
            .expect("Failed to create Kafka consumer");

        consumer.subscribe(&["order-events"]).unwrap();

        Self { consumer, db_pool }
    }

    pub async fn run(&self) {
        loop {
            match self.consumer.recv().await {
                Ok(message) => {
                    if let Some(payload) = message.payload() {
                        if let Ok(event) = serde_json::from_slice::<OrderPlacedEvent>(payload) {
                            self.process_order_placed(&event).await;
                        }
                    }
                    self.consumer.commit_message(&message, rdkafka::consumer::CommitMode::Async).unwrap();
                }
                Err(e) => eprintln!("Kafka error: {}", e),
            }
        }
    }

    async fn process_order_placed(&self, event: &OrderPlacedEvent) {
        for item in &event.items {
            sqlx::query(
                "UPDATE inventory SET quantity = quantity - $1 WHERE product_id = $2"
            )
            .bind(item.quantity)
            .bind(item.product_id)
            .execute(&self.db_pool)
            .await
            .ok();
        }
    }
}
```

The consumer disables auto-commit and commits offsets manually only after successfully processing each message. This ensures at-least-once delivery: if the process crashes after updating inventory but before committing, Kafka will redeliver the message and the inventory update will execute again. Idempotency is crucial—implement it by tracking processed `order_id` values in a separate table and skipping duplicates.

```rust
async fn process_order_placed(&self, event: &OrderPlacedEvent) {
    // Check if already processed
    let exists: bool = sqlx::query_scalar(
        "SELECT EXISTS(SELECT 1 FROM processed_orders WHERE order_id = $1)"
    )
    .bind(event.order_id)
    .fetch_one(&self.db_pool)
    .await
    .unwrap_or(false);

    if exists {
        return; // Duplicate message, skip processing
    }

    let mut tx = self.db_pool.begin().await.unwrap();

    for item in &event.items {
        sqlx::query("UPDATE inventory SET quantity = quantity - $1 WHERE product_id = $2")
            .bind(item.quantity)
            .bind(item.product_id)
            .execute(&mut *tx)
            .await
            .ok();
    }

    sqlx::query("INSERT INTO processed_orders (order_id) VALUES ($1)")
        .bind(event.order_id)
        .execute(&mut *tx)
        .await
        .ok();

    tx.commit().await.ok();
}
```

By wrapping inventory updates and deduplication in a single transaction, the consumer achieves idempotent processing: redeliveries have no effect because the `processed_orders` check prevents duplicate execution.

The failure modes in event-driven systems revolve around eventual consistency and message ordering. After a customer places an order, the inventory service may take seconds to process the event, during which the product page shows stale stock counts. If the consumer crashes or falls behind, this lag extends to minutes or hours. Mitigate by exposing lag metrics—the difference between the latest message offset and the consumer's committed offset—and alerting when lag exceeds thresholds. Partition assignment failures occur when consumers in a group rebalance due to crashes or deployments, pausing message processing until the rebalance completes. Use cooperative rebalancing protocols to minimize downtime.

Message ordering is guaranteed only within a partition, not across partitions. If two `OrderPlaced` events for the same product land in different partitions, they may be processed out of order, causing incorrect stock counts. Enforce ordering by using the `product_id` as the partition key, ensuring all events for a product are routed to the same partition and processed sequentially.

## 3. High-Performance Optimization & Failure Modes

### Layered Architecture: Combating Rigid Boundaries and Excessive Indirection

The layered pattern's strength—strict dependency flow—becomes a weakness when business requirements demand cross-layer optimization. Consider a reporting dashboard that needs to join orders with inventory data across 50,000 rows. The naive layered approach forces the query through the repository interface, which returns domain entities, which the service layer transforms, which the controller serializes. This path materializes 50,000 objects in memory and traverses three abstraction layers.

The optimization is to introduce a query facade that bypasses the service layer for read-only operations requiring denormalized data. Define a `ReportingQuery` interface in the presentation layer that the persistence layer implements directly.

```java
// com.example.web.ReportingQuery.java
package com.example.web;

import java.util.List;

public interface ReportingQuery {
    List<OrderSummary> getOrderSummaryByDateRange(String startDate, String endDate);
}
```

```java
// com.example.persistence.JdbcReportingQuery.java
package com.example.persistence;

import com.example.web.ReportingQuery;
import com.example.web.OrderSummary;
import org.springframework.jdbc.core.JdbcTemplate;

public class JdbcReportingQuery implements ReportingQuery {
    private final JdbcTemplate jdbc;

    public JdbcReportingQuery(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public List<OrderSummary> getOrderSummaryByDateRange(String startDate, String endDate) {
        return jdbc.query(
            "SELECT o.id, o.customer_id, o.total, i.product_name, i.quantity " +
            "FROM orders o JOIN order_items i ON o.id = i.order_id " +
            "WHERE o.created_at BETWEEN ? AND ?",
            (rs, rowNum) -> new OrderSummary(
                rs.getLong("id"),
                rs.getLong("customer_id"),
                rs.getBigDecimal("total"),
                rs.getString("product_name"),
                rs.getInt("quantity")
            ),
            startDate,
            endDate
        );
    }
}
```

This bypasses the domain layer entirely, executing a single SQL join and streaming results directly to the controller. The trade-off is that reporting queries are no longer enforced by business invariants—this is acceptable for read-only analytics where performance trumps consistency.

Another failure mode is excessive transaction scope creep. In a layered architecture, the transaction boundary typically begins in the service layer and spans repository calls. If a service method orchestrates five repository operations, all five must succeed or roll back atomically. This causes lock contention when concurrent transactions attempt to modify the same rows. Optimize by splitting long transactions into smaller units with explicit isolation levels. Use `READ_COMMITTED` for queries that tolerate stale reads and `SERIALIZABLE` only for critical invariants like preventing double charges.

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public Order placeOrder(long customerId, List<OrderItem> items) {
    // Read-only validation queries use READ_COMMITTED
    if (!inventoryService.isAvailable(items)) {
        throw new OutOfStockException();
    }

    // Write operations upgrade to SERIALIZABLE within a nested transaction
    return performAtomicOrderCreation(customerId, items);
}

@Transactional(isolation = Isolation.SERIALIZABLE, propagation = Propagation.REQUIRES_NEW)
private Order performAtomicOrderCreation(long customerId, List<OrderItem> items) {
    Order order = new Order(customerId, items);
    repository.save(order);
    inventoryService.reserveStock(items);
    return order;
}
```

This reduces contention by allowing concurrent reads to proceed without blocking while still guaranteeing atomicity for critical writes.

### Hexagonal Architecture: Managing Adapter Proliferation and Port Explosion

As hexagonal systems mature, the number of ports and adapters multiplies. A payment gateway port might need adapters for Stripe, PayPal, Square, and a dozen regional processors. Each adapter duplicates configuration logic, error handling, and retry policies. Consolidate this logic into an abstract base adapter that implements common cross-cutting concerns.

```rust
// adapters/base_gateway.rs
use crate::domain::{PaymentGateway, PaymentRequest, PaymentResult};
use std::error::Error;
use std::time::Duration;

pub trait GatewayClient: Send + Sync {
    fn execute_charge(&self, request: &PaymentRequest) -> Result<PaymentResult, Box<dyn Error>>;
}

pub struct RetryingGateway<T: GatewayClient> {
    client: T,
    max_retries: u32,
    backoff: Duration,
}

impl<T: GatewayClient> RetryingGateway<T> {
    pub fn new(client: T, max_retries: u32, backoff: Duration) -> Self {
        Self { client, max_retries, backoff }
    }
}

impl<T: GatewayClient> PaymentGateway for RetryingGateway<T> {
    fn charge(&self, request: &PaymentRequest) -> Result<PaymentResult, Box<dyn Error>> {
        let mut attempts = 0;
        loop {
            match self.client.execute_charge(request) {
                Ok(result) => return Ok(result),
                Err(e) if attempts < self.max_retries && is_retryable(&e) => {
                    attempts += 1;
                    std::thread::sleep(self.backoff * attempts);
                }
                Err(e) => return Err(e),
            }
        }
    }
}

fn is_retryable(err: &Box<dyn Error>) -> bool {
    let msg = err.to_string();
    msg.contains("timeout") || msg.contains("503") || msg.contains("connection reset")
}
```

Now each concrete adapter implements only the `GatewayClient` trait with minimal boilerplate, and wrapping it in `RetryingGateway` adds retry logic automatically.

```rust
// adapters/stripe.rs
use crate::adapters::base_gateway::GatewayClient;
use crate::domain::{PaymentRequest, PaymentResult, PaymentStatus};
use std::error::Error;

pub struct StripeClient {
    api_key: String,
}

impl StripeClient {
    pub fn new(api_key: String) -> Self {
        Self { api_key }
    }
}

impl GatewayClient for StripeClient {
    fn execute_charge(&self, request: &PaymentRequest) -> Result<PaymentResult, Box<dyn Error>> {
        // Stripe-specific HTTP call logic
        Ok(PaymentResult {
            transaction_id: "stripe-txn".to_string(),
            status: PaymentStatus::Approved,
        })
    }
}
```

Compose the final gateway by wrapping the client.

```rust
let stripe_client = StripeClient::new(api_key);
let gateway: Box<dyn PaymentGateway> = Box::new(RetryingGateway::new(stripe_client, 3, Duration::from_secs(1)));
```

This composition pattern prevents duplication and keeps adapters focused on protocol translation rather than operational concerns.

Another failure mode is port fragmentation where different parts of the domain define overlapping interfaces. The order service might define a `NotificationPort` for sending emails, while the inventory service defines a `MessagingPort` for SMS alerts. Both ultimately send messages but through separate abstractions. Unify them into a single `MessageDelivery` port with a channel-agnostic interface.

```rust
pub enum MessageChannel {
    Email,
    Sms,
    Push,
}

pub struct Message {
    pub recipient: String,
    pub subject: String,
    pub body: String,
    pub channel: MessageChannel,
}

pub trait MessageDelivery: Send + Sync {
    fn send(&self, message: &Message) -> Result<(), Box<dyn Error>>;
}
```

A single adapter can now route messages to the appropriate backend based on the channel field, eliminating redundant abstractions and simplifying dependency injection.

### Microservices Architecture: Taming Operational Complexity and Observability Overhead

Microservices introduce operational complexity that monoliths avoid. A typical production cluster runs dozens of services with independent deployment pipelines, configuration manifests, and monitoring dashboards. This complexity explodes without standardization. Establish a service template repository that codifies golden paths for observability, health checks, and resource management.

Every service inherits a base Dockerfile with security hardening and minimal layers.

```dockerfile
# templates/Dockerfile.base
FROM rust:1.75-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /build
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release && rm -rf src

COPY src ./src
RUN touch src/main.rs && cargo build --release

FROM scratch
COPY --from=builder /build/target/release/service /service
EXPOSE 8080
USER 65534:65534
ENTRYPOINT ["/service"]
```

This multi-stage build caches dependencies separately from application code, reducing rebuild times. The final stage uses a `scratch` base image with no shell or package manager, minimizing attack surface. Running as user `65534` (the `nobody` UID) prevents privilege escalation if the container is compromised.

Standardize health check endpoints across all services to enable Kubernetes liveness and readiness probes.

```rust
// templates/health.rs
use axum::{Router, Json, http::StatusCode};
use serde_json::json;

pub fn health_routes() -> Router {
    Router::new()
        .route("/health", axum::routing::get(liveness))
        .route("/ready", axum::routing::get(readiness))
}

async fn liveness() -> StatusCode {
    StatusCode::OK
}

async fn readiness() -> Result<Json<serde_json::Value>, StatusCode> {
    // Check database connectivity, message queue availability, etc.
    Ok(Json(json!({ "status": "ready" })))
}
```

Embed structured logging with correlation IDs to enable request tracing across service boundaries.

```rust
use tracing::{info, error};
use uuid::Uuid;

#[axum::debug_handler]
async fn handler(req: axum::http::Request<axum::body::Body>) -> axum::response::Response {
    let correlation_id = req.headers()
        .get("X-Correlation-ID")
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string())
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    info!(correlation_id = %correlation_id, "Request received");
    // Process request
    info!(correlation_id = %correlation_id, "Request completed");
}
```

Propagate the correlation ID to downstream services so distributed traces can be reconstructed from log aggregation systems.

Network failures between services require defensive programming. Implement timeouts, circuit breakers, and bulkheads to prevent cascading failures. Use the `tower` middleware stack for resiliency patterns.

```rust
use tower::{ServiceBuilder, timeout::Timeout, limit::ConcurrencyLimit};
use std::time::Duration;

let client = ServiceBuilder::new()
    .timeout(Duration::from_secs(5))
    .concurrency_limit(100)
    .service(reqwest::Client::new());
```

This wraps the HTTP client with a 5-second timeout and limits concurrent requests to 100, preventing resource exhaustion when downstream services slow down.

For inter-service communication at scale, replace synchronous HTTP with gRPC and Protobuf for reduced serialization overhead and built-in streaming.

```protobuf
// inventory-service/proto/inventory.proto
syntax = "proto3";

package inventory;

service InventoryService {
  rpc ReserveStock(ReserveRequest) returns (ReserveResponse);
  rpc ReleaseStock(ReleaseRequest) returns (ReleaseResponse);
}

message ReserveRequest {
  repeated Item items = 1;
}

message Item {
  int64 product_id = 1;
  int32 quantity = 2;
}

message ReserveResponse {
  string reservation_id = 1;
  bool success = 2;
}

message ReleaseRequest {
  string reservation_id = 1;
}

message ReleaseResponse {
  bool success = 1;
}
```

Generate Rust bindings with `tonic` and implement the service.

```rust
// inventory-service/src/grpc.rs
use tonic::{Request, Response, Status};
use inventory::{inventory_service_server::{InventoryService, InventoryServiceServer}, ReserveRequest, ReserveResponse};

pub struct InventoryServer;

#[tonic::async_trait]
impl InventoryService for InventoryServer {
    async fn reserve_stock(&self, request: Request<ReserveRequest>) -> Result<Response<ReserveResponse>, Status> {
        let items = request.into_inner().items;
        // Perform reservation logic
        Ok(Response::new(ReserveResponse {
            reservation_id: "res-123".to_string(),
            success: true,
        }))
    }
}
```

gRPC reduces serialization overhead by 3-5x compared to JSON and provides bi-directional streaming for high-throughput scenarios.

### Event-Driven Architecture: Handling Backpressure and Poison Pills

Event-driven systems must handle backpressure when consumers process messages slower than producers emit them. Without backpressure management, message queues grow unbounded until brokers run out of disk or memory. Kafka mitigates this with partition-level flow control: producers block when a partition's buffer fills, applying backpressure to the source. Configure `buffer.memory` and `batch.size` to balance throughput and latency.

```rust
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::ClientConfig;

let producer: FutureProducer = ClientConfig::new()
    .set("bootstrap.servers", "localhost:9092")
    .set("buffer.memory", "67108864")  // 64 MB buffer
    .set("batch.size", "16384")        // 16 KB batches
    .set("linger.ms", "10")            // Wait 10ms for batching
    .set("compression.type", "snappy") // Compress payloads
    .create()
    .unwrap();
```

Consumers must handle poison pills—messages that consistently fail processing due to malformed data or application bugs. After a configurable number of retries, route poison pills to a dead-letter queue for manual inspection.

```rust
async fn process_message(&self, message: &rdkafka::message::BorrowedMessage<'_>) {
    let retry_count = self.get_retry_count(message).await;

    match self.handle_event(message).await {
        Ok(_) => self.consumer.commit_message(message, rdkafka::consumer::CommitMode::Async).unwrap(),
        Err(e) if retry_count < 3 => {
            self.increment_retry_count(message).await;
            self.republish_to_retry_topic(message).await;
        }
        Err(e) => {
            error!("Poison pill detected: {:?}", e);
            self.send_to_dead_letter_queue(message).await;
            self.consumer.commit_message(message, rdkafka::consumer::CommitMode::Async).unwrap();
        }
    }
}
```

This three-tier strategy—retry, dead-letter, commit—prevents a single bad message from blocking all subsequent messages in the partition.

Event schema evolution requires forward and backward compatibility. Use Avro or Protobuf schemas registered in a schema registry, and enforce compatibility rules that prevent breaking changes.

```json
{
  "type": "record",
  "name": "OrderPlaced",
  "namespace": "com.example.events",
  "fields": [
    {"name": "order_id", "type": "long"},
    {"name": "customer_id", "type": "long"},
    {"name": "total_cents", "type": "long"},
    {"name": "items", "type": {"type": "array", "items": "string"}},
    {"name": "timestamp", "type": "long"},
    {"name": "payment_method", "type": ["null", "string"], "default": null}
  ]
}
```

Adding `payment_method` with a default of `null` maintains backward compatibility: old consumers ignore the field, and new consumers handle its presence or absence. Removing a required field or changing a field's type breaks compatibility and requires deploying a new topic with a version suffix like `order-events-v2`.

Exactly-once semantics require idempotent consumers and transactional producers. Kafka's transactional API ensures that a batch of messages is either fully committed or fully rolled back, preventing duplicate deliveries even across process crashes.

```rust
let producer: FutureProducer = ClientConfig::new()
    .set("bootstrap.servers", "localhost:9092")
    .set("transactional.id", "order-producer-1")
    .set("enable.idempotence", "true")
    .create()
    .unwrap();

producer.init_transactions(std::time::Duration::from_secs(10)).await.unwrap();
producer.begin_transaction().unwrap();

let record = FutureRecord::to("order-events")
    .key("order")
    .payload("event payload");

producer.send(record, std::time::Duration::from_secs(5)).await.unwrap();
producer.commit_transaction(std::time::Duration::from_secs(10)).await.unwrap();
```

Consumers enable exactly-once by setting `isolation.level=read_committed` to ignore uncommitted messages.

Architectural patterns are not theoretical constructs but battle-tested solutions to structural complexity. The layered pattern provides simplicity and cognitive familiarity at the cost of rigidity. The hexagonal pattern achieves testability and decoupling through dependency inversion. The microservices pattern enables organizational scaling and independent deployment at the cost of operational complexity. The event-driven pattern delivers throughput and temporal decoupling through eventual consistency. Production systems blend these patterns strategically, applying each where its trade-offs align with the problem domain. Mastery lies not in dogmatic adherence to a single pattern but in recognizing which invariants matter for each subsystem and composing patterns to satisfy them.
