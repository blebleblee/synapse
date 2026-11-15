# Lesson 3: RESTful API Design, GraphQL Query Resolution, Backend Data Processing Pipelines

## 1. First-Principles Intuition & Invariants

Modern backend architectures rest on a deceptively simple premise: distributed systems communicate by exchanging structured representations of application state over network boundaries. The Representational State Transfer (REST) architectural style, articulated by Roy Fielding in his 2000 dissertation, formalizes this intuition through a constraint-based model where clients and servers negotiate over **resources**—abstract entities identified by Uniform Resource Identifiers (URIs) and manipulated through a small, fixed vocabulary of standardized verbs. REST is not a protocol but a set of architectural constraints that, when satisfied, yield systems exhibiting desirable properties of scalability, simplicity, modifiability, and reliability.

At the heart of REST lies the resource-oriented worldview. Every entity that merits independent addressability—a user profile, an invoice, a telemetry event stream—becomes a first-class resource with a canonical URI. The HTTP protocol provides the uniform interface: `GET` retrieves representations, `POST` creates new resources, `PUT` replaces existing state wholesale, `PATCH` applies partial modifications, and `DELETE` removes resources. This semantic mapping is not arbitrary. HTTP verbs carry intrinsic contracts about **idempotence** and **safety**. A safe operation, such as `GET` or `HEAD`, must not alter server-side state; repeated invocations yield identical observable outcomes. An idempotent operation, including `PUT`, `DELETE`, and `GET`, guarantees that performing it multiple times produces the same effect as performing it once. Understanding these invariants is foundational: idempotence enables safe automatic retries in the face of network partitions, and safety allows aggressive client-side caching without violating correctness.

Resource identifiers must be hierarchical and semantically transparent. A well-designed URI reflects the domain's entity graph: `/users/42` denotes a specific user, `/users/42/orders` enumerates that user's orders, and `/orders/1337/items/5` addresses a line item within an order. This hierarchical structure mirrors the composition of domain aggregates and supports intuitive reasoning about scope, ownership, and lifecycle. Crucially, URIs should be opaque to clients beyond their structural semantics; embedding implementation details such as database primary keys or internal service names violates the principle of information hiding and couples clients to transient server internals.

REST's statelessness constraint mandates that each request from client to server must contain all information necessary to understand and process that request. The server holds no session context between requests; authentication credentials, transaction identifiers, and pagination cursors travel with each message. Statelessness simplifies server implementation, enables horizontal scaling through trivial load balancing, and improves fault tolerance since any server replica can handle any request. However, statelessness imposes bandwidth overhead and shifts session management complexity to the client or to external session stores, a tradeoff that must be consciously evaluated.

GraphQL emerges from a fundamentally different set of constraints. Developed at Facebook in 2012 and open-sourced in 2015, GraphQL addresses the **overfetching** and **underfetching** pathologies endemic to REST APIs serving rich client applications. In REST, each endpoint returns a fixed shape of data; a mobile client rendering a user profile might require sequential requests to `/users/42`, `/users/42/posts`, and `/users/42/friends`, each returning fields the client does not need while omitting fields it does. GraphQL inverts this model: the client specifies an exact query describing the shape and depth of required data, and the server assembles a bespoke response matching that specification. This declarative approach collapses multiple round trips into a single request and eliminates payload bloat, trading REST's operational simplicity for query expressiveness and bandwidth efficiency.

The GraphQL type system is introspective and strongly typed. Every API exposes a schema—a directed acyclic graph of object types, scalar fields, enumerations, and relationships—that clients can programmatically query and traverse. Fields are resolved lazily and compositionally through **resolver functions**, small, single-purpose functions that compute field values by delegating to data sources, invoking microservices, or transforming upstream results. This resolver architecture naturally aligns with microservice topologies and domain-driven design, allowing the GraphQL layer to function as a **Backend for Frontend (BFF)** façade that orchestrates heterogeneous backend systems.

Backend data processing pipelines constitute the third pillar of modern full-stack architectures. APIs expose synchronous request-response interfaces suited to interactive workloads, but many backend operations—ETL transformations, batch analytics, asynchronous notifications, durable workflow orchestration—require different concurrency models and durability guarantees. Processing pipelines decouple producers from consumers through message queues or event streams, enabling asynchronous communication, buffering under load spikes, and at-least-once delivery semantics. The conceptual model is straightforward: stages in a pipeline consume messages from an input channel, perform transformations, and emit results to an output channel, composing into directed acyclic computation graphs.

Critical invariants govern pipeline correctness. **Exactly-once processing** is generally impossible in distributed systems without transactional integration between the messaging substrate and application state stores; practical systems settle for at-least-once delivery combined with idempotent processing logic. **Ordering guarantees** vary by substrate: Kafka preserves order within a partition but not across partitions, RabbitMQ offers per-queue FIFO, and SQS provides only eventual ordering. Backpressure mechanisms prevent fast producers from overwhelming slow consumers by applying flow control, either through explicit acknowledgment protocols or by monitoring queue depth and throttling ingestion rates. Understanding these guarantees and their failure modes is essential for designing correct distributed data pipelines.


## 2. Core Architecture & Mechanics

### REST Resource Modeling and Endpoint Semantics

The design of a RESTful API begins with identifying domain entities and their relationships, then mapping that domain model onto a URI hierarchy. Consider a simplified e-commerce domain comprising users, products, orders, and reviews. The resource model emerges from entity lifecycle and ownership:

```
/users                    (collection)
/users/{userId}           (singleton)
/users/{userId}/orders    (sub-collection, scoped by user)
/products                 (collection)
/products/{productId}     (singleton)
/products/{productId}/reviews   (sub-collection)
/orders                   (global collection, for admin queries)
/orders/{orderId}         (singleton)
/orders/{orderId}/items   (sub-collection, line items)
```

Each endpoint implements a subset of the HTTP method vocabulary according to the affordances of that resource. A collection endpoint such as `/users` typically supports `GET` for listing with pagination and filtering, and `POST` for creating new users. A singleton endpoint like `/users/42` supports `GET` for retrieval, `PUT` or `PATCH` for updates, and `DELETE` for removal. The choice between `PUT` and `PATCH` hinges on update semantics: `PUT` replaces the entire resource representation, requiring the client to send all fields, while `PATCH` applies a partial modification, often encoded as a JSON Patch (RFC 6902) or JSON Merge Patch (RFC 7396) document.

HTTP status codes carry precise semantic meaning and must be chosen carefully. `200 OK` indicates successful `GET`, `PUT`, or `PATCH` with a response body. `201 Created` confirms successful resource creation via `POST`, with a `Location` header containing the new resource's URI. `204 No Content` signals success without a response body, appropriate for `DELETE` or updates that return nothing. `400 Bad Request` indicates malformed syntax or failed validation, `401 Unauthorized` signals missing or invalid authentication, `403 Forbidden` denies access to an authenticated principal lacking authorization, `404 Not Found` means the resource does not exist, and `409 Conflict` flags constraint violations such as unique key collisions. `500 Internal Server Error` is a last resort for unhandled exceptions; well-engineered APIs translate anticipated failure modes into appropriate 4xx codes with actionable error payloads.

Content negotiation via `Accept` and `Content-Type` headers allows endpoints to serve multiple representation formats—JSON, XML, Protocol Buffers, MessagePack—though modern APIs converge on JSON for its balance of human readability and tooling ubiquity. Hypermedia controls (HATEOAS) embed navigational links in responses, enabling clients to discover available transitions without hardcoding URLs. For example, a `GET /users/42` response might include:

```json
{
  "id": 42,
  "name": "Alice",
  "email": "alice@example.com",
  "_links": {
    "self": { "href": "/users/42" },
    "orders": { "href": "/users/42/orders" },
    "deactivate": { "href": "/users/42/deactivate", "method": "POST" }
  }
}
```

Hypermedia decouples clients from URI construction logic and enables server-driven evolution of the API topology, though adoption remains limited due to increased payload size and client complexity.

Pagination is essential for collection endpoints. Offset-based pagination (`?offset=100&limit=20`) is simple but fragile under concurrent writes; inserting items before the cursor causes duplicates, deleting items causes skips. Cursor-based pagination encodes an opaque position token that survives insertions and deletions. Keyset pagination uses the last seen primary key as a range predicate (`?after=uuid&limit=20`), combining efficiency with correctness at the cost of requiring indexed, unique, sortable keys. The HTTP `Link` header can encode pagination URIs following RFC 5988:

```
Link: </users?after=uuid123&limit=20>; rel="next",
      </users?before=uuid098&limit=20>; rel="prev"
```

Filtering and sorting parameters must be carefully scoped to prevent injection attacks and excessive database load. A whitelist approach restricts filterable fields and permitted operators (`/products?category=electronics&price_lt=500&sort=-rating`) and translates query parameters into parameterized SQL or ORM queries, never into raw string interpolation.

### GraphQL Schema, Execution Model, and Resolver Chains

A GraphQL schema defines the contract between client and server through a type system built from scalars, objects, interfaces, unions, and enums. The schema designates a root `Query` type for read operations, a `Mutation` type for writes, and optionally a `Subscription` type for real-time event streams. Consider a simplified schema:

```graphql
type User {
  id: ID!
  username: String!
  email: String!
  posts(first: Int, after: String): PostConnection!
  friends: [User!]!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments(first: Int): [Comment!]!
}

type Comment {
  id: ID!
  body: String!
  author: User!
}

type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
}

type PostEdge {
  cursor: String!
  node: Post!
}

type PageInfo {
  hasNextPage: Boolean!
  endCursor: String
}

type Query {
  user(id: ID!): User
  posts(first: Int, after: String): PostConnection!
}

type Mutation {
  createPost(title: String!, content: String!): Post!
  deletePost(id: ID!): Boolean!
}
```

Non-null types are marked with `!`, signaling that the field always returns a value or the query fails. Nullable fields allow null returns, providing graceful degradation. The schema is self-describing; clients issue introspection queries to discover available types, fields, and arguments, enabling rich developer tooling such as autocomplete and type checking.

Query execution proceeds in phases. The parser validates the query string against GraphQL grammar, producing an Abstract Syntax Tree. The validator checks the AST against the schema, ensuring referenced types and fields exist, arguments match parameter signatures, and fragments target compatible types. The executor then traverses the AST depth-first, invoking resolver functions for each field.

A resolver function accepts four arguments: the parent object (the resolved value of the enclosing field), the arguments object (field-specific parameters), the context object (request-scoped data such as authentication tokens, database connections, and service clients), and an info object (metadata about the query and schema). Resolvers return values, promises, or throw errors. The execution engine awaits promises concurrently within a level of the tree, maximizing parallelism.

Consider a query:

```graphql
query {
  user(id: "42") {
    username
    posts(first: 5) {
      edges {
        node {
          title
          author {
            username
          }
        }
      }
    }
  }
}
```

Execution begins by invoking the `Query.user` resolver with `args = {id: "42"}`. This resolver queries the user database and returns a user object. Next, the engine invokes resolvers for `User.username` (trivial: returns `parent.username`) and `User.posts` (queries the posts database filtered by `author_id = 42`, implements cursor pagination, returns a connection object). For each post edge, the engine resolves `Post.title` (trivial) and `Post.author` (potentially redundant: the author is known to be user 42, but the resolver might naively query the database again). Finally, `User.username` is resolved again for the post author.

This traversal exposes the infamous **N+1 query problem**: fetching a user and their five posts naively triggers 1 query for the user, 1 query for the posts collection, and 5 queries for post authors—seven database round trips when two would suffice. The solution is **dataloader batching and caching**. A dataloader is a request-scoped cache that accumulates field resolutions within a single tick of the event loop, batches them into a single bulk query, and distributes results back to callers. Implemented correctly, the post author resolver enqueues `loadUser(42)` five times; the dataloader deduplicates to a single request, queries `SELECT * FROM users WHERE id IN (42)`, and returns the cached result to all five callsites.

Resolver middleware composes cross-cutting concerns such as authentication, authorization, logging, and error handling. Middleware functions wrap resolvers, inspecting the context and arguments before delegating to the underlying resolver or short-circuiting with an error. For example, an authorization middleware checks whether `context.user` has permission to access the requested resource:

```javascript
function authorize(requiredRole) {
  return function (resolver) {
    return function (parent, args, context, info) {
      if (!context.user || !context.user.roles.includes(requiredRole)) {
        throw new Error('Forbidden');
      }
      return resolver(parent, args, context, info);
    };
  };
}

const resolvers = {
  Mutation: {
    deletePost: authorize('admin')(async (parent, { id }, context) => {
      await context.db.posts.delete(id);
      return true;
    }),
  },
};
```

Directive-based middleware, specified in the schema with `@auth(role: "admin")`, provides a declarative alternative that moves policy closer to the type definitions.

GraphQL subscriptions enable server-pushed updates over WebSocket or Server-Sent Events connections. A subscription resolver returns an asynchronous iterable, typically backed by a pub-sub system. When an event occurs—a mutation updates a post, an external system sends a notification—the pub-sub broadcasts to all active subscriptions matching the event topic. The GraphQL server invokes the subscription resolver's payload transformation, applies field selection, and pushes the result to the client. Subscriptions introduce stateful connection management, requiring careful handling of backpressure, reconnection logic, and resource cleanup.

### Backend Data Processing Pipeline Architecture

Data pipelines decouple synchronous request-response flows from asynchronous, durable, and parallelizable computation. The canonical pattern involves message-oriented middleware connecting producer and consumer processes. Producers publish messages to named topics or queues; consumers subscribe to these channels, process messages, and optionally publish derivative messages downstream.

A concrete pipeline might look like:

```
[HTTP API] --enqueue--> [RabbitMQ: raw_events] 
    --> [Validator Worker] --validate--> [RabbitMQ: validated_events]
    --> [Enrichment Worker] --enrich--> [RabbitMQ: enriched_events]
    --> [Aggregator Worker] --aggregate--> [TimescaleDB: metrics]
```

Each stage is an independent process or pod, horizontally scalable, reading from an input queue and writing to an output queue. Messages carry immutable payloads, often serialized as JSON, Protocol Buffers, or Avro, with metadata headers for correlation IDs, timestamps, and schema versions.

Message acknowledgment semantics govern durability. In RabbitMQ, a consumer explicitly acknowledges (`ack`) a message after successful processing, signaling the broker to remove it from the queue. Failing to acknowledge (or sending a negative acknowledgment, `nack`) returns the message to the queue for redelivery, implementing at-least-once delivery. Auto-acknowledgment on receipt trades durability for throughput, acceptable only for non-critical workloads.

Exactly-once semantics require idempotent processing logic. Each message carries a unique identifier; consumers maintain a deduplication cache (often Redis or a database table) mapping message IDs to processing outcomes. Before processing, the consumer checks the cache; if the ID exists, the consumer skips processing and immediately acknowledges. Otherwise, it processes the message, writes the outcome to the cache transactionally with any side effects, and acknowledges. This pattern requires transactional coordination between the deduplication store and the business logic's data store, achievable through distributed transactions (2PC), saga patterns, or single-database transactions when both stores coexist.

Kafka partitions provide ordering within a partition but not across partitions. Producers assign messages to partitions via a key hash; messages with the same key land in the same partition, preserving order for related events (e.g., all events for user 42). Consumers within a consumer group claim exclusive ownership of partitions, enabling parallelism while maintaining per-partition order. Kafka stores offsets—the index of the last consumed message per partition—enabling consumers to resume after failure or restart. Committing offsets after successful processing ensures at-least-once; committing before processing risks message loss; committing transactionally with database writes using Kafka transactions approaches exactly-once.

Dead-letter queues (DLQs) handle poison messages that repeatedly fail processing. After exceeding a retry threshold, the infrastructure moves the message to a DLQ for manual inspection or automated remediation. DLQs prevent a single bad message from blocking the entire pipeline but require monitoring and operational runbooks.

Backpressure mechanisms prevent resource exhaustion. Consumers configure prefetch limits (RabbitMQ) or poll batch sizes (Kafka) to bound in-flight work. When processing slows, the consumer stops fetching new messages, causing queue depth to grow, signaling upstream producers to throttle. Application-level backpressure, propagated via HTTP 429 responses or circuit breakers, prevents cascading overload.

Error handling distinguishes transient failures (network timeouts, temporary unavailability) from permanent failures (validation errors, malformed data). Transient failures warrant exponential backoff and retry; permanent failures require immediate rejection, logging, and routing to a DLQ. Libraries such as Polly (C#), resilience4j (Java), or custom middleware implement retry policies with jitter to avoid thundering herds.


## 3. High-Performance Optimization & Failure Modes

### REST API Performance and Caching Strategies

REST's statelessness and uniform interface enable aggressive caching at multiple layers. HTTP caching semantics, codified in RFC 7234, leverage headers to control cache behavior. `Cache-Control` directives govern freshness: `max-age=3600` permits caching for one hour, `public` allows shared proxies to cache, `private` restricts caching to the client, and `no-store` forbids caching altogether. `Expires` provides an absolute timestamp, superseded by `max-age`. Conditional requests minimize bandwidth: a client caches a response with an `ETag` (entity tag, a hash or version identifier) or `Last-Modified` timestamp, then revalidates with `If-None-Match` or `If-Modified-Since` headers. If the resource is unchanged, the server responds with `304 Not Modified` and an empty body, confirming cache validity.

Server-side caching layers include reverse proxies (Nginx, Varnish), CDNs (Cloudflare, Fastly), and application caches (Redis, Memcached). Cache invalidation strategies trade freshness for complexity: time-based expiration is simple but may serve stale data; event-driven invalidation (broadcasting cache purge messages on mutation) ensures consistency but couples services. Surrogate keys allow fine-grained invalidation: tagging responses with logical keys (e.g., `user:42`, `product:1337`) enables purging all related entries when an entity changes.

Database query optimization underpins API performance. N+1 query patterns, common in ORM-heavy codebases, arise when lazy-loading relationships trigger per-row queries. Solutions include eager loading via joins or subqueries, batch loading (similar to GraphQL dataloaders), and denormalization. Indexing query predicates (`WHERE`, `JOIN`, `ORDER BY` clauses) is fundamental; missing indexes force full table scans, degrading linearly with table size. Composite indexes optimize multi-column filters but require careful column ordering to match query access patterns. Covering indexes include all columns needed by a query, enabling index-only scans that avoid heap lookups.

Connection pooling amortizes the cost of establishing database connections. A pool maintains a fixed number of persistent connections, lending them to request handlers and reclaiming them on completion. Pool exhaustion under load causes requests to block or fail, necessitating monitoring of pool size, wait times, and timeout configurations. Misconfigured pools with excessive idle connections waste resources; undersized pools bottleneck throughput.

Rate limiting protects APIs from abuse and ensures fair resource allocation. Token bucket algorithms permit bursts while enforcing average rates: a bucket holds tokens (credits), refilled at a fixed rate; each request consumes a token; requests arriving when the bucket is empty are rejected with `429 Too Many Requests`. Distributed rate limiting requires shared state (Redis) to coordinate decisions across replicas. Adaptive rate limiting adjusts thresholds based on observed latency or error rates, tightening limits under degradation to shed load gracefully.

### GraphQL Query Optimization and Cost Analysis

GraphQL's flexibility enables clients to request deeply nested, expensive queries that overwhelm backend systems. Query cost analysis assigns weights to fields and enforces budget limits, rejecting queries exceeding thresholds. A naive cost model assigns uniform weights; sophisticated models account for collection sizes, join complexities, and downstream service latencies. For example:

```
Query cost = 1 (baseline)
           + count(scalar fields) × 1
           + count(list fields) × (size × 10)
           + count(nested objects) × 5
```

A query fetching a user and 100 posts with 50 comments each would accumulate prohibitive cost, triggering rejection before execution.

Query depth limiting prevents pathological cyclic queries (e.g., `user { friends { friends { friends { ... } } } }`). A maximum depth of 5–7 levels balances expressiveness and safety. Complexity analysis generalizes beyond depth, inspecting list field multiplicities: a query requesting 1000 users, each with 1000 posts, represents a 1,000,000-node result set and must be rejected.

Persisted queries precompile and whitelist allowed operations, clients transmitting only a query ID instead of the full query string. Benefits include reduced bandwidth, protection against malicious queries, and opportunities for server-side optimization. Automatic Persisted Queries (APQ) hash query strings, clients sending the hash and falling back to the full query on cache misses.

Field-level caching memoizes resolver results per request or across requests. Request-scoped caches (dataloaders) deduplicate within a query; global caches store computed values with TTLs. Cache keys must incorporate all inputs affecting the result: arguments, authentication context, and upstream data versions. Naive caching of `user(id: $id)` without invalidation on user updates serves stale data; event-driven or versioned caching solves this at the cost of infrastructure complexity.

Response streaming and deferred fields (experimental GraphQL features) allow the server to send partial results progressively, reducing time-to-first-byte and improving perceived latency for slow fields. A query annotates expensive fields with `@defer`; the server responds with non-deferred data immediately, streaming deferred data as it becomes available.

### Pipeline Failure Modes and Resilience Patterns

Data pipelines face diverse failure modes: transient network partitions, cascading service outages, data corruption, and resource exhaustion. Designing resilient pipelines requires explicit handling of each class.

Retry logic with exponential backoff mitigates transient failures. A consumer encountering a retriable error (HTTP 503, connection timeout) waits before retrying, doubling the wait interval on successive failures, capped at a maximum. Jitter—adding random variance to wait times—prevents synchronized retries from overwhelming recovering services. After exceeding a retry limit, messages route to a DLQ.

Circuit breakers prevent cascading failures by detecting unhealthy downstream dependencies and failing fast. A circuit breaker tracks success and failure rates over a sliding window; after exceeding an error threshold, it transitions to an open state, immediately rejecting requests without invoking the dependency. After a timeout, it enters a half-open state, permitting a single probe request; success closes the circuit, failure reopens it. Circuit breakers trade availability for stability, shedding load to protect degraded systems from collapse.

Bulkheads isolate failures through resource partitioning. A service handling multiple tenants or pipelines allocates separate thread pools, connection pools, or process replicas per partition. If one partition exhausts resources, others continue operating. Bulkheading trades resource efficiency for fault isolation.

Timeouts are critical for preventing resource leaks and bounding latency. Every network call, database query, and external service invocation must enforce a deadline. In distributed pipelines, timeouts propagate: an HTTP handler with a 5-second timeout must set tighter timeouts (e.g., 4 seconds) on downstream calls to reserve time for processing and response transmission.

Monitoring and observability expose pipeline health through metrics, logs, and traces. Key metrics include queue depth (backlog size), processing latency (time from enqueue to completion), error rates, and throughput (messages per second). Alerting on queue depth growth detects consumer lag or capacity issues; spikes in error rates signal code defects or downstream failures. Distributed tracing (OpenTelemetry, Jaeger) correlates logs and spans across services, reconstructing request flows through microservice topologies.

Idempotency enforcement at the application layer—assigning globally unique message IDs, maintaining deduplication tables, and transactionally committing processing outcomes—ensures correctness under redelivery. Without idempotency, at-least-once delivery semantics cause duplicate side effects: double-charging customers, sending redundant notifications, or corrupting aggregate state.

Versioning strategies enable non-breaking evolution of message schemas. Producer and consumer processes deploy asynchronously; a schema change in the producer must not crash existing consumers. Avro and Protobuf support backward and forward compatibility: adding optional fields, removing deprecated fields, and encoding defaults allow old consumers to parse new messages and new consumers to parse old messages. Schema registries (Confluent Schema Registry) enforce compatibility rules and version schemas centrally, preventing incompatible changes from reaching production.

Graceful shutdown logic ensures in-flight messages are not lost during deployments or scaling events. On receiving a termination signal, a consumer stops fetching new messages, completes processing of in-flight messages, commits offsets or acknowledges messages, closes connections, and exits. Kubernetes graceful shutdown periods (default 30 seconds) must exceed maximum message processing time to prevent premature termination.
