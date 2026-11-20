# Lesson 4: Platform Architecture

## 1. First-Principles Intuition & Invariants

GitHub exists at the intersection of distributed version control, multi-tenant web application architecture, and high-throughput API infrastructure. Understanding GitHub's platform architecture requires peeling back the veneer of its user interface to examine the mechanical underpinnings: how Git protocol negotiations traverse network boundaries, how access control decisions flow through layered permission models, how webhook payloads achieve at-least-once delivery semantics, and how GraphQL resolvers balance expressivity against denial-of-service attack surfaces.

At its core, GitHub is a sharded, distributed system that presents a unified interface to millions of repositories while internally partitioning data across storage clusters, coordinating permission checks through replicated caches, and enforcing rate limits through hierarchical token bucket algorithms. The platform must reconcile Git's content-addressable object model—where commits, trees, and blobs are identified by SHA-1 or SHA-256 hashes—with relational metadata that tracks issues, pull requests, and repository permissions. This duality manifests in the storage backend abstraction, where Git packfiles coexist with MySQL and memcached clusters, and where repository synchronization protocols must maintain eventual consistency across geographically distributed replicas.

The access control model operates on a hierarchical principle: organizations contain teams, teams contain members, and repositories grant permissions through explicit collaborator assignments or inherited team memberships. Every API request or Git protocol operation triggers a permission check that traverses this graph, querying cached ACLs and falling back to authoritative database shards when cache misses occur. This architecture enforces the invariant that permission denials fail closed—an unavailable cache or database shard results in an HTTP 503 or Git protocol error, never an inadvertent grant of unauthorized access.

Webhook delivery represents a distributed systems challenge distinct from synchronous API requests. When a repository event occurs—a push, pull request, or issue comment—GitHub must fan out HTTP POST requests to potentially hundreds of registered webhook endpoints. The delivery subsystem operates as a durable queue with exponential backoff and retry semantics, persisting payloads to disk and replaying failed deliveries across multiple attempts. The platform guarantees at-least-once delivery but not exactly-once, placing the burden of idempotency on webhook consumers. This design choice stems from the CAP theorem's constraints: in the face of network partitions, GitHub prioritizes availability and partition tolerance over strict consistency in webhook ordering.

Rate limiting constitutes the platform's primary defense against resource exhaustion and denial-of-service attacks. GitHub enforces multiple overlapping rate limit policies: per-user limits on REST API calls, per-repository limits on Git protocol operations, per-IP address limits on unauthenticated requests, and secondary rate limits on mutation-heavy GraphQL queries. These limits operate through hierarchical token buckets, where each bucket refills at a predetermined rate and each request consumes one or more tokens. When a bucket depletes, the platform returns HTTP 403 with a `Retry-After` header indicating when capacity will replenish. The token bucket algorithm provides smooth rate limiting without hard cutoffs, allowing brief bursts while enforcing average throughput constraints.

GraphQL schema design introduces unique challenges because clients can construct arbitrarily complex queries that traverse deeply nested relationships. A single GraphQL query might request a repository's last 100 pull requests, each pull request's review comments, and each comment author's profile details—triggering thousands of database queries through naive resolution. GitHub mitigates this through schema-level complexity limits, resolver-level batching via DataLoader patterns, and maximum depth constraints that reject queries exceeding a predefined nesting threshold. The platform also employs cost analysis, assigning each field a static cost and rejecting queries whose total cost exceeds a per-request budget.

Git protocol negotiations occur when clients execute `git clone`, `git fetch`, or `git push`, initiating a multi-phase handshake that determines which objects the client possesses and which objects the server must transmit. The protocol operates in two modes: the legacy "dumb" HTTP protocol, which serves static packfiles without server-side intelligence, and the modern "smart" HTTP or SSH protocols, which execute `git-upload-pack` or `git-receive-pack` processes that dynamically compute minimal packfile deltas. Smart protocol negotiations rely on reference advertisement, where the server sends a list of all branch and tag refs with their current commit SHAs, followed by client-initiated "want" and "have" negotiations that converge on the minimal object set requiring transfer.

Storage backend abstractions allow GitHub to evolve its underlying infrastructure without disrupting the Git protocol interface. Early GitHub architectures stored repositories as bare Git directories on NFS mounts, but modern implementations employ distributed object stores like DGit, GitHub's internal Git storage layer built atop replicated filesystems and eventually consistent synchronization protocols. This abstraction layer intercepts Git object reads and writes, routing them through caching tiers and replication logic transparent to Git clients. The platform maintains the invariant that every repository exists in at least three physical replicas across distinct failure domains, ensuring durability even during datacenter outages.

Distributed repository synchronization becomes critical for global content delivery and disaster recovery. GitHub maintains read replicas in multiple geographic regions, streaming repository updates through a change data capture pipeline that tails the authoritative database's transaction log and applies mutations to remote replicas. This synchronization operates with eventual consistency—a push to a repository in the US-East datacenter might not propagate to an Asia-Pacific replica for hundreds of milliseconds—but the platform ensures monotonic read consistency for individual clients by routing subsequent requests to the same replica through session affinity cookies.

The architectural invariants that govern GitHub's platform design can be summarized as follows: permission checks always fail closed in the presence of unavailable dependencies; webhook delivery guarantees at-least-once semantics with unbounded retry windows; rate limits enforce average throughput constraints through hierarchical token buckets; GraphQL queries undergo static cost analysis before execution; Git protocol negotiations minimize object transfer through interactive want/have exchanges; storage backends abstract physical replication details behind a logical Git interface; and distributed replicas achieve eventual consistency through change data capture pipelines with session affinity for read-your-writes semantics.

## 2. Core Architecture & Mechanics

The repository access control model begins with the fundamental entity graph: users, organizations, teams, and repositories. Every repository has an owner—either a user or an organization—and permissions flow through explicit grants or inherited memberships. When a user attempts to access a repository, GitHub resolves their effective permissions by querying the intersection of direct collaborator permissions, team memberships, and organization-level role assignments. This resolution occurs in a specific precedence order: repository-specific collaborator permissions override team permissions, and explicit denials take precedence over any grants.

```text
Repository Permission Resolution Flow:

User → Organization Membership → Base Role (Owner, Member)
  ↓
Team Memberships → Team Repository Permissions (Admin, Write, Read)
  ↓
Direct Collaborator → Repository-Specific Role (Admin, Write, Triage, Read)
  ↓
Branch Protection Rules → Required Status Checks, Review Requirements
  ↓
Final Permission Decision → Cached in Memcached for 60s TTL
```

The permission cache operates as a multi-tiered hierarchy. The first tier caches ACL decisions in memcached clusters with short TTLs, reducing database load for repeated permission checks within a user session. The second tier maintains a precomputed materialized view of team memberships in MySQL read replicas, denormalized to avoid expensive recursive queries. When a cache miss occurs, the platform queries the authoritative database shard responsible for that organization or user, computes the permission set, and backfills the cache. This architecture means that permission changes—adding a collaborator or updating a team—may require up to 60 seconds to propagate globally due to cache invalidation lag.

Webhook delivery begins when repository events trigger the creation of webhook job records in a persistent queue. Each job contains the event payload serialized as JSON, the target URL, and metadata including the repository ID and event type. The webhook worker pool continuously polls this queue, claiming jobs through optimistic locking and dispatching HTTP POST requests with HMAC-SHA256 signatures in the `X-Hub-Signature-256` header. These signatures allow consumers to verify payload authenticity by recomputing the HMAC using a shared secret configured during webhook registration.

```text
Webhook Delivery State Machine:

Event Occurs → Job Enqueued (State: Pending)
  ↓
Worker Claims Job → HTTP POST Dispatch
  ↓
Success (2xx) → Job Marked Complete → Delivery Log Persisted
  ↓
Failure (5xx, Timeout) → Exponential Backoff → Retry
  ↓
Max Retries Exceeded → Job Marked Failed → Alert Sent
```

The exponential backoff algorithm doubles the retry interval after each failure, starting at one second and capping at one hour. GitHub attempts delivery up to three times, after which the webhook enters a failed state visible in the repository's webhook delivery dashboard. Importantly, the platform does not guarantee ordered delivery across multiple webhooks registered to the same repository—concurrent events may trigger simultaneous HTTP requests that complete out of order due to network variability.

API rate limiting employs the token bucket algorithm with distinct buckets for authenticated and unauthenticated requests. Each authenticated user receives a bucket of 5,000 tokens that refills at a constant rate, while unauthenticated requests share a single bucket per originating IP address with a capacity of 60 tokens per hour. When a request arrives, the platform consumes tokens equal to the request's cost—typically one token for read endpoints and higher costs for mutation or search endpoints—and decrements the bucket. If insufficient tokens remain, the request fails immediately with HTTP 403 and response headers indicating the bucket's reset timestamp.

```c
// Token bucket rate limiting pseudocode
typedef struct {
    int capacity;
    int tokens;
    time_t last_refill;
    double refill_rate; // tokens per second
} TokenBucket;

bool consume_tokens(TokenBucket *bucket, int cost, time_t now) {
    // Calculate tokens to add based on elapsed time
    double elapsed = difftime(now, bucket->last_refill);
    int new_tokens = (int)(elapsed * bucket->refill_rate);
    
    bucket->tokens = min(bucket->capacity, bucket->tokens + new_tokens);
    bucket->last_refill = now;
    
    if (bucket->tokens >= cost) {
        bucket->tokens -= cost;
        return true;
    }
    return false;
}
```

The platform maintains separate buckets for different API families. REST API requests consume tokens from the primary bucket, GraphQL requests consume tokens from a secondary bucket with distinct capacity and refill rates, and Git protocol operations consume tokens from a tertiary bucket with per-repository granularity. This segmentation prevents a single client from exhausting rate limits across all API surfaces through a single request pattern.

GraphQL schema design at GitHub balances expressivity with performance by constraining query complexity through static analysis. Before executing any query, the platform's GraphQL engine computes a complexity score by traversing the query's abstract syntax tree and summing per-field costs. Simple scalar fields carry zero cost, but connection fields—which return paginated lists—carry costs proportional to the requested page size. Nested connections multiply costs, so requesting 100 issues each with 100 comments would accumulate 10,000 in complexity cost.

```graphql
# Example GraphQL query with complexity analysis
query {
  repository(owner: "torvalds", name: "linux") {  # Cost: 1
    issues(first: 100) {  # Cost: 100
      nodes {
        comments(first: 50) {  # Cost: 100 * 50 = 5000
          nodes {
            author {
              login  # Cost: 0 (scalar)
            }
          }
        }
      }
    }
  }
}
# Total query complexity: 5101
# Rejected if exceeds limit (typically 500,000)
```

The resolver layer employs DataLoader batching to prevent N+1 query problems. When multiple GraphQL fields require fetching the same type of related entity—such as user profiles for commit authors—the DataLoader collects all requested IDs during a single event loop tick, batches them into a single database query, and distributes results back to individual resolvers. This batching occurs transparently within the resolver execution engine, ensuring that deeply nested queries translate to a bounded number of database round trips.

Git protocol negotiations begin with reference advertisement, where the server sends all branch and tag refs along with their current commit SHAs. In the smart HTTP protocol, this occurs during the initial GET request to `/info/refs?service=git-upload-pack`, which returns a text-based protocol stream containing lines of the form `<sha1> <refname>`. The client parses this advertisement, compares it against local refs, and constructs a "want" list of missing commits alongside a "have" list of commits it already possesses.

```text
Git Protocol Negotiation (Smart HTTP):

Client → GET /info/refs?service=git-upload-pack
Server → 001e# service=git-upload-pack
Server → 00000032a86f <refs/heads/main> (first ref)
Server → 0032f3b2 <refs/heads/feature> (additional refs)
Server → 0000 (flush packet)

Client → POST /git-upload-pack
Client → 0032want a86f... (missing commits)
Client → 0032have f3b2... (possessed commits)
Client → 0000 (flush)

Server → Computes minimal packfile delta
Server → Streams packfile with objects not in "have" set
Server → 0000 (completion)
```

The server's `git-upload-pack` process performs a reachability analysis, computing the set of objects reachable from the "want" commits but not reachable from the "have" commits. This analysis traverses the commit DAG backward, marking objects as required until it reaches commits present in the client's "have" set. The resulting object set is packed into a packfile with delta compression, where objects are encoded as deltas against similar objects to minimize transfer size.

Storage backend abstractions isolate Git protocol logic from the physical storage layer. GitHub's DGit system intercepts Git object reads and writes, translating them into operations against a distributed object store. When a client pushes new commits, the platform unpacks incoming objects, validates their integrity by recomputing SHA hashes, and writes them to multiple storage replicas before acknowledging the push. This write path employs a quorum protocol—a push succeeds only after a majority of replicas confirm durable persistence, ensuring that subsequent reads will observe the new state even if individual replicas fail.

```text
Storage Backend Write Path:

Client Push → git-receive-pack Process
  ↓
Unpack Objects → Validate SHA Hashes → Check Object Connectivity
  ↓
Write to DGit Layer → Fan-Out to 3 Replicas
  ↓
Quorum Wait (2 of 3 ACKs) → Return Success to Client
  ↓
Async: Update Reference Pointers → Invalidate Caches → Trigger Webhooks
```

Read operations traverse the inverse path. When a client clones or fetches a repository, the platform routes the request to the nearest healthy replica, retrieves objects from the distributed store, and streams them as a packfile. The read path employs aggressive caching at multiple tiers: object metadata resides in memcached, hot packfiles persist in SSD-based local caches on Git frontend servers, and cold objects lazily migrate from archival storage tiers. This hierarchical caching ensures that popular repositories serve clone requests from memory or local disk without touching the authoritative object store.

Distributed repository synchronization propagates updates from the primary datacenter to global read replicas through a change data capture pipeline. Every mutation to repository state—pushes, branch updates, tag creations—generates a changelog event containing the repository ID, reference name, old SHA, and new SHA. These events stream through Kafka topics partitioned by repository ID, ensuring that updates to a single repository arrive at replicas in causal order. Replica consumers apply updates by fetching missing objects from the primary datacenter's object store and updating local reference pointers, eventually converging to consistency with the authoritative state.

```text
Distributed Synchronization Flow:

Primary DC: Push Event → Changelog Record → Kafka Topic
  ↓
Replica DC: Consume Changelog → Fetch Missing Objects → Update Refs
  ↓
Replica DC: Mark Replication Lag Metric → Update Health Check
  ↓
Router Layer: Direct Reads to Lowest-Lag Replica with Session Affinity
```

Session affinity ensures monotonic reads by routing subsequent requests from the same client to the same replica. When a user pushes to a repository and immediately navigates to the repository's web interface, the platform sets a session cookie that pins the user to the replica that processed the push. This prevents the user from observing stale state on a lagging replica, maintaining the illusion of strong consistency despite the underlying eventual consistency model.

## 3. High-Performance Optimization & Failure Modes

Optimizing repository access control checks requires precomputing permission materialized views and aggressively caching results. GitHub's team membership resolution queries can trigger expensive recursive database joins when teams nest within teams or when organizations contain thousands of members. To mitigate this, the platform maintains a denormalized `team_memberships` table that flattens the hierarchy, storing each user's transitive team memberships as explicit rows. This denormalization trades write amplification—adding a user to a parent team requires updating rows for all descendant teams—for read performance, reducing permission checks to indexed lookups rather than recursive graph traversals.

Cache invalidation introduces consistency challenges. When an organization owner revokes a user's access, the platform must purge all cached permission decisions involving that user across potentially thousands of repositories. GitHub solves this through hierarchical cache namespaces: each organization and repository has a cache version number that increments on permission changes. Cached permission decisions include the version number, and cache lookups first verify that the cached version matches the current authoritative version. If versions diverge, the platform discards the stale cache entry and recomputes permissions from the database. This approach bounds cache invalidation overhead to a single version number update rather than scanning and purging individual cache entries.

Webhook delivery scaling demands horizontal partitioning of the job queue. As GitHub's repository count grew from thousands to hundreds of millions, a single monolithic queue became a bottleneck. The modern architecture partitions webhook jobs across 256 queue shards, hashing each job's repository ID to a consistent shard. Each shard has a dedicated worker pool that independently polls and dispatches jobs, allowing the platform to scale webhook throughput linearly by adding workers. Shard rebalancing occurs automatically when workers fail—other workers in the pool claim jobs from the failed worker's shard, preventing delivery delays during transient failures.

Webhook failure modes extend beyond simple network errors. Consumers may return HTTP 2xx success codes but fail to process payloads idempotently, leading to duplicate side effects when GitHub retries after transient connection resets. The platform mitigates this by including a unique delivery GUID in the `X-GitHub-Delivery` header, allowing consumers to detect and discard duplicate deliveries. Additionally, GitHub enforces a five-second response timeout—consumers that exceed this threshold trigger a delivery failure and retry, even if the consumer eventually returns success. This timeout prevents slow consumers from exhausting webhook worker capacity.

API rate limiting optimization focuses on minimizing token bucket update latency. Naively, each API request would require a database transaction to read the current token count, decrement it, and write the new value—a synchronization bottleneck that limits throughput to database transaction rates. GitHub optimizes this through in-memory token buckets maintained in Redis with atomic increment operations. Each rate limit bucket corresponds to a Redis key storing the current token count and last refill timestamp. Requests execute a Lua script atomically within Redis that computes refill, decrements tokens, and returns success or failure, eliminating cross-region database round trips for every rate limit check.

```lua
-- Redis Lua script for atomic token bucket consumption
local key = KEYS[1]
local cost = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local refill_rate = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local state = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(state[1]) or capacity
local last_refill = tonumber(state[2]) or now

local elapsed = now - last_refill
local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)

if new_tokens >= cost then
    redis.call('HMSET', key, 'tokens', new_tokens - cost, 'last_refill', now)
    redis.call('EXPIRE', key, 3600)
    return 1
else
    return 0
end
```

Secondary rate limits address abuse patterns that conform to primary rate limits but still exhaust platform resources. A client could issue 5,000 API requests within an hour by spreading them evenly, each request creating a new repository or issue. Such mutation-heavy workloads impose disproportionate database write load compared to read-heavy workloads. GitHub's secondary rate limits dynamically throttle requests that exceed mutation thresholds, returning HTTP 403 even when primary rate limit tokens remain. These secondary limits operate with shorter time windows—tracking mutation counts over five-minute intervals rather than hourly—and apply progressive penalties that increase backoff durations for repeated violations.

GraphQL query optimization relies on aggressive resolver batching and strategic use of deferred execution. When a query requests multiple connection fields—such as a repository's issues, pull requests, and branches—naive execution would sequentially fetch each connection, blocking subsequent field resolution until prior connections complete. GitHub's GraphQL engine employs parallel execution, dispatching independent field resolvers concurrently and awaiting their completion before assembling the response. For deeply nested queries, the engine uses DataLoader batching to collect all pending database queries across resolvers and execute them in a single round trip.

Complexity analysis prevents denial-of-service attacks where adversaries craft maximally nested queries to exhaust server resources. GitHub's schema enforces a maximum query depth of 10 and a total complexity budget of 500,000 points. These limits were empirically tuned through load testing: a budget of 500,000 permits legitimate use cases like fetching a repository's issue list with comments while rejecting pathological queries that request thousands of nested relationships. The platform also tracks per-field execution time, aborting queries that exceed a wall-clock timeout of 60 seconds even if complexity analysis approved them.

Git protocol negotiation performance hinges on minimizing round trips during the want/have exchange. The naive protocol requires multiple client-server round trips as the client incrementally reports "have" commits and the server responds with "ACK" or "NAK" packets. Modern Git implementations employ multi-ack modes where the client batches hundreds of "have" lines in a single packet, and the server responds with multiple ACKs indicating which commits it can use as delta bases. GitHub's protocol implementation further optimizes this by maintaining a bitmap index mapping commits to reachable objects, allowing the server to instantly compute object reachability without traversing the commit graph.

```text
Optimized Git Protocol with Multi-Ack:

Client → want <sha1> (single round trip with all wants)
Client → have <sha1> have <sha2> have <sha3> ... (batched)
Client → done

Server → Consults bitmap index for reachability
Server → Computes minimal packfile delta in parallel
Server → Streams packfile (single response)
```

Bitmap indexes are precomputed data structures stored alongside Git packfiles, mapping each commit to the set of objects reachable from that commit. When a client reports "have <sha>", the server looks up the corresponding bitmap and unions all "have" bitmaps together, producing the complete set of objects the client possesses. The server then computes the objects reachable from "want" commits, subtracts the "have" bitmap, and generates a packfile containing only the difference. This bitmap-accelerated reachability analysis reduces protocol negotiation time from seconds to milliseconds for large repositories.

Storage backend failure modes manifest when replicas diverge or quorum writes fail. If a replica falls behind due to network partitions, subsequent reads routed to that replica observe stale state. GitHub detects replica lag by tracking replication checkpoint positions—each replica periodically reports the highest changelog sequence number it has processed. The routing layer excludes replicas whose lag exceeds a threshold, redirecting traffic to healthier replicas. For repositories with all replicas lagging—often due to widespread network failures—the platform falls back to the primary datacenter, accepting higher latency over serving stale data.

Quorum write failures occur when insufficient replicas acknowledge a push within the timeout window. GitHub's write protocol requires two of three replicas to confirm before returning success to the client. If only one replica acknowledges, the push fails with an error, and the client retries. This conservative approach prioritizes durability over availability: the platform refuses writes rather than risk data loss. However, partial writes can leave repositories in an inconsistent state where some replicas contain the new commit while others do not. The platform's reconciliation protocol periodically scans for such inconsistencies, fetching missing objects from other replicas and repairing divergence without operator intervention.

Distributed synchronization lag spikes when changelog consumers fall behind due to bursty write traffic or consumer process failures. GitHub monitors replication lag per replica and per repository, emitting metrics when lag exceeds 10 seconds. Automated alerting triggers when lag persists beyond 60 seconds, indicating a systemic problem rather than transient variance. The platform's remediation strategy involves horizontally scaling changelog consumers—adding consumer processes that partition the Kafka topic's consumer group—and temporarily throttling write traffic to the primary datacenter if lag threatens to exhaust disk space allocated for changelog retention.

Session affinity breaks down when replicas fail or when users switch between devices or network contexts that cause cookie loss. To handle these cases, GitHub implements best-effort read-your-writes consistency by embedding version vectors in web application responses. When a user pushes a commit, the platform records the changelog sequence number and embeds it in the next HTTP response as a cookie. Subsequent requests include this sequence number, and the routing layer directs the request only to replicas that have processed changelog events up to that sequence number. If no such replica is available, the platform routes to the primary datacenter, ensuring the user always observes their own writes despite eventual consistency.

Platform architecture at GitHub ultimately reflects the tension between Git's decentralized content-addressable design and the centralized access control and metadata management required for collaborative software development at global scale. The system succeeds by introducing abstraction layers—permission caches, webhook queues, rate limit buckets, GraphQL complexity analyzers, protocol negotiation optimizers, storage backend quorums, and synchronization pipelines—that insulate clients from the distributed systems complexity beneath. Every architectural decision trades off consistency for availability, immediacy for durability, or expressivity for security, carefully calibrated to the empirical workload patterns of millions of repositories and developers orchestrating the continuous integration and deployment pipelines that define modern software engineering.
