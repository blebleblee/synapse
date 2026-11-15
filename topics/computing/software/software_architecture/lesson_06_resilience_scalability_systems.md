# Lesson 6: Resilience, Scalability Across Systems

## 1. First-Principles Intuition & Invariants

Software systems exist in a permanent state of partial failure. This is not a transient condition to be eliminated through better engineering—it is a fundamental property of distributed computation at scale. Networks partition, disks fail, memory corrupts, downstream services timeout, and upstream clients send malformed requests at rates that exceed provisioned capacity. The defining characteristic of production-grade architecture is not the absence of failure, but rather the system's ability to continue delivering value in the presence of continuous, cascading faults.

Resilience emerges from deliberate constraint. When we architect a system to tolerate failure, we are fundamentally limiting the blast radius of any single component's demise. This principle manifests across every layer of the stack: bulkheads partition thread pools to prevent resource exhaustion from cascading across subsystems, circuit breakers halt retry storms that amplify partial outages into total system collapse, and rate limiters protect downstream dependencies from clients whose behavior—whether malicious or merely enthusiastic—threatens to overwhelm available capacity. Each of these patterns trades perfect theoretical throughput for guaranteed operational headroom, accepting that peak performance must be sacrificed to ensure that degraded performance remains possible when components fail.

Scalability, by contrast, addresses the question of how systems behave as demand grows beyond the capacity of any single machine. The Von Neumann bottleneck—the fundamental constraint that CPU and memory communicate through a shared bus with finite bandwidth—places an upper bound on vertical scaling. No matter how fast we make individual processors, memory access latency eventually dominates execution time. Horizontal scaling breaks this barrier by distributing state and computation across multiple independent machines, but introduces a new set of challenges rooted in the CAP theorem's observation that distributed systems cannot simultaneously guarantee strong consistency, availability under partition, and tolerance to network splits.

The architectural tension between resilience and scalability manifests most clearly in data layer design. A single-node database offers perfect consistency—every read reflects all prior writes—but cannot scale beyond the throughput of one machine and represents a single point of failure. Replicating data across multiple nodes improves both availability and read scalability, but introduces the possibility of stale reads if we allow replica lag. Sharding distributes data across partitions to scale write throughput, but queries spanning multiple shards require expensive cross-partition joins or, worse, application-level scatter-gather operations that amplify tail latency. Every architectural decision in this space involves trading one desirable property for another, and the correct choice depends entirely on the specific invariants your system must uphold.

Observability provides the feedback loop that closes the resilience-scalability cycle. Without visibility into system behavior under load, we cannot distinguish between normal operation and degraded performance, cannot detect when circuit breakers should open, and cannot measure whether our sharding strategy actually distributes load evenly. Metrics capture aggregate behavior—request rates, error percentages, latency distributions—while distributed traces reconstruct the causal chain of a single request flowing through dozens of microservices. Structured logs preserve the semantic context of individual events. Together, these three pillars transform a distributed system from an opaque black box into a transparent, debuggable artifact whose behavior can be understood, predicted, and improved.

The core invariant underlying all resilience patterns is that failures must remain local. A timeout in one service must not propagate upstream as thread pool exhaustion. A surge of traffic to one partition must not starve requests to other partitions. A slow database query must not block unrelated transactions. This locality of failure requires explicit resource isolation at every boundary—separate thread pools for different downstream dependencies, per-tenant rate limits to prevent noisy neighbors, bulkheads that partition connection pools by priority class. When failure locality breaks down, cascading outages follow: the thundering herd of retries, the convoy effect where slow requests block fast ones, the death spiral where increased load triggers more timeouts which trigger more retries which increase load further.

Scalability's fundamental invariant is more subtle: the system's work per operation must remain constant or grow sublinearly as the system scales. If every additional user requires proportionally more work from existing infrastructure, you have not built a scalable system—you have built a distributed monolith whose operational cost grows quadratically with load. True horizontal scalability demands that each node's workload remains independent of total system size. This is why shared-nothing architectures dominate at scale: when every request can be satisfied by a single shard with no cross-node coordination, doubling the number of shards doubles capacity while leaving per-shard load unchanged.

The trillion-scale systems that power modern internet infrastructure—search engines indexing the web, social networks serving billions of users, financial exchanges processing millions of transactions per second—all converge on a common architectural pattern. They embrace eventual consistency where strong consistency is unnecessary, partition state aggressively to minimize cross-node coordination, cache heavily at every layer to absorb read load, and implement sophisticated observability to detect and respond to failures before they cascade. These are not abstract principles but concrete engineering choices, each backed by runnable code, measurable metrics, and hard-won operational experience.

## 2. Core Architecture & Mechanics

The circuit breaker pattern implements a state machine that prevents cascading failures by failing fast when downstream dependencies become unhealthy. In its closed state, the circuit breaker forwards all requests to the protected service, monitoring for failures. When the error rate exceeds a configured threshold—typically measured over a sliding time window to avoid false positives from transient spikes—the breaker transitions to the open state, immediately rejecting all requests without attempting to contact the downstream service. After a timeout period, the breaker enters a half-open state, allowing a small number of probe requests through. If these succeed, the breaker returns to closed; if they fail, it reopens. This state machine prevents retry storms where clients continue hammering a failing service, giving it no opportunity to recover while consuming resources that could serve healthy requests.

A production-grade circuit breaker implementation must track per-request outcomes in a fixed-size sliding window to calculate error rates without unbounded memory growth. The canonical approach uses a ring buffer of buckets, where each bucket aggregates statistics for a fixed time slice—typically one second. When evaluating whether to trip the breaker, we sum successes and failures across all buckets in the window, computing the error percentage. As time advances, the oldest bucket expires and a new bucket is allocated, maintaining a constant memory footprint regardless of request rate.

```rust
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use std::collections::VecDeque;

#[derive(Clone, Copy, Debug, PartialEq)]
enum CircuitState {
    Closed,
    Open,
    HalfOpen,
}

struct Bucket {
    timestamp: Instant,
    successes: u64,
    failures: u64,
}

impl Bucket {
    fn new(now: Instant) -> Self {
        Self {
            timestamp: now,
            successes: 0,
            failures: 0,
        }
    }

    fn total(&self) -> u64 {
        self.successes + self.failures
    }

    fn error_rate(&self) -> f64 {
        let total = self.total();
        if total == 0 {
            0.0
        } else {
            self.failures as f64 / total as f64
        }
    }
}

pub struct CircuitBreaker {
    state: Arc<Mutex<CircuitBreakerState>>,
    config: CircuitBreakerConfig,
}

struct CircuitBreakerState {
    current_state: CircuitState,
    buckets: VecDeque<Bucket>,
    state_transition_time: Instant,
    half_open_successes: u64,
    half_open_attempts: u64,
}

pub struct CircuitBreakerConfig {
    pub window_duration: Duration,
    pub bucket_duration: Duration,
    pub failure_threshold_percentage: f64,
    pub minimum_request_threshold: u64,
    pub open_duration: Duration,
    pub half_open_max_requests: u64,
    pub half_open_success_threshold: u64,
}

impl Default for CircuitBreakerConfig {
    fn default() -> Self {
        Self {
            window_duration: Duration::from_secs(60),
            bucket_duration: Duration::from_secs(1),
            failure_threshold_percentage: 50.0,
            minimum_request_threshold: 20,
            open_duration: Duration::from_secs(30),
            half_open_max_requests: 5,
            half_open_success_threshold: 3,
        }
    }
}

impl CircuitBreaker {
    pub fn new(config: CircuitBreakerConfig) -> Self {
        let num_buckets = (config.window_duration.as_secs() 
            / config.bucket_duration.as_secs()) as usize;
        
        let mut buckets = VecDeque::with_capacity(num_buckets);
        let now = Instant::now();
        buckets.push_back(Bucket::new(now));

        Self {
            state: Arc::new(Mutex::new(CircuitBreakerState {
                current_state: CircuitState::Closed,
                buckets,
                state_transition_time: now,
                half_open_successes: 0,
                half_open_attempts: 0,
            })),
            config,
        }
    }

    pub fn call<F, T, E>(&self, f: F) -> Result<T, CircuitBreakerError<E>>
    where
        F: FnOnce() -> Result<T, E>,
    {
        let now = Instant::now();
        
        // Check if we can proceed with the request
        {
            let mut state = self.state.lock().unwrap();
            self.rotate_buckets(&mut state, now);
            
            match state.current_state {
                CircuitState::Open => {
                    // Check if it's time to transition to half-open
                    if now.duration_since(state.state_transition_time) >= self.config.open_duration {
                        state.current_state = CircuitState::HalfOpen;
                        state.state_transition_time = now;
                        state.half_open_successes = 0;
                        state.half_open_attempts = 0;
                    } else {
                        return Err(CircuitBreakerError::CircuitOpen);
                    }
                }
                CircuitState::HalfOpen => {
                    if state.half_open_attempts >= self.config.half_open_max_requests {
                        return Err(CircuitBreakerError::CircuitOpen);
                    }
                    state.half_open_attempts += 1;
                }
                CircuitState::Closed => {}
            }
        }

        // Execute the protected operation
        let result = f();

        // Record the outcome and potentially transition state
        {
            let mut state = self.state.lock().unwrap();
            
            match result {
                Ok(_) => {
                    self.record_success(&mut state, now);
                }
                Err(_) => {
                    self.record_failure(&mut state, now);
                }
            }
        }

        result.map_err(CircuitBreakerError::Downstream)
    }

    fn rotate_buckets(&self, state: &mut CircuitBreakerState, now: Instant) {
        let bucket_duration = self.config.bucket_duration;
        let max_buckets = (self.config.window_duration.as_secs() 
            / bucket_duration.as_secs()) as usize;

        // Remove expired buckets
        while let Some(oldest) = state.buckets.front() {
            if now.duration_since(oldest.timestamp) > self.config.window_duration {
                state.buckets.pop_front();
            } else {
                break;
            }
        }

        // Add new bucket if current is too old
        if let Some(current) = state.buckets.back() {
            if now.duration_since(current.timestamp) >= bucket_duration {
                state.buckets.push_back(Bucket::new(now));
                
                // Ensure we don't exceed max buckets
                while state.buckets.len() > max_buckets {
                    state.buckets.pop_front();
                }
            }
        }

        // Ensure at least one bucket exists
        if state.buckets.is_empty() {
            state.buckets.push_back(Bucket::new(now));
        }
    }

    fn record_success(&self, state: &mut CircuitBreakerState, now: Instant) {
        if let Some(current_bucket) = state.buckets.back_mut() {
            current_bucket.successes += 1;
        }

        match state.current_state {
            CircuitState::HalfOpen => {
                state.half_open_successes += 1;
                if state.half_open_successes >= self.config.half_open_success_threshold {
                    state.current_state = CircuitState::Closed;
                    state.state_transition_time = now;
                    state.buckets.clear();
                    state.buckets.push_back(Bucket::new(now));
                }
            }
            _ => {}
        }
    }

    fn record_failure(&self, state: &mut CircuitBreakerState, now: Instant) {
        if let Some(current_bucket) = state.buckets.back_mut() {
            current_bucket.failures += 1;
        }

        match state.current_state {
            CircuitState::Closed => {
                let (total_requests, total_failures) = state.buckets.iter()
                    .fold((0u64, 0u64), |(req, fail), bucket| {
                        (req + bucket.total(), fail + bucket.failures)
                    });

                if total_requests >= self.config.minimum_request_threshold {
                    let error_rate = (total_failures as f64 / total_requests as f64) * 100.0;
                    
                    if error_rate >= self.config.failure_threshold_percentage {
                        state.current_state = CircuitState::Open;
                        state.state_transition_time = now;
                    }
                }
            }
            CircuitState::HalfOpen => {
                state.current_state = CircuitState::Open;
                state.state_transition_time = now;
            }
            _ => {}
        }
    }

    pub fn state(&self) -> CircuitState {
        self.state.lock().unwrap().current_state
    }
}

#[derive(Debug)]
pub enum CircuitBreakerError<E> {
    CircuitOpen,
    Downstream(E),
}
```

The bulkhead pattern extends resource isolation beyond individual circuit breakers to entire subsystems. Named after the watertight compartments in ship hulls that prevent a single breach from flooding the entire vessel, bulkheads partition thread pools, connection pools, and memory buffers such that resource exhaustion in one subsystem cannot starve others. In a typical microservice architecture, each downstream dependency receives its own dedicated thread pool with a fixed maximum size. When that pool exhausts, requests to that specific dependency fail immediately, but requests to other dependencies continue processing using their isolated resources.

Thread pool bulkheads require careful capacity planning. Allocating too few threads to a pool increases latency as requests queue, potentially triggering timeouts. Allocating too many threads across all pools can exceed the host's available CPU cores, causing excessive context switching overhead. The optimal configuration depends on the workload's concurrency requirements and the downstream service's latency characteristics. For I/O-bound operations with high latency, larger pools exploit more concurrent outstanding requests. For CPU-bound operations, pool size should not exceed available cores to avoid thrashing.

```rust
use std::sync::{Arc, Mutex, Condvar};
use std::collections::VecDeque;
use std::thread;
use std::time::Duration;

pub struct BulkheadThreadPool {
    workers: Vec<Worker>,
    sender: Arc<Mutex<JobQueue>>,
    config: BulkheadConfig,
}

struct JobQueue {
    queue: VecDeque<Job>,
    max_queue_size: usize,
    active_jobs: usize,
    shutdown: bool,
}

type Job = Box<dyn FnOnce() + Send + 'static>;

struct Worker {
    thread: Option<thread::JoinHandle<()>>,
}

pub struct BulkheadConfig {
    pub max_threads: usize,
    pub max_queue_size: usize,
    pub queue_timeout: Duration,
}

impl Default for BulkheadConfig {
    fn default() -> Self {
        Self {
            max_threads: 10,
            max_queue_size: 100,
            queue_timeout: Duration::from_millis(500),
        }
    }
}

impl BulkheadThreadPool {
    pub fn new(config: BulkheadConfig) -> Self {
        let queue = Arc::new(Mutex::new(JobQueue {
            queue: VecDeque::new(),
            max_queue_size: config.max_queue_size,
            active_jobs: 0,
            shutdown: false,
        }));

        let mut workers = Vec::with_capacity(config.max_threads);

        for id in 0..config.max_threads {
            workers.push(Worker::new(id, Arc::clone(&queue)));
        }

        Self {
            workers,
            sender: queue,
            config,
        }
    }

    pub fn execute<F>(&self, f: F) -> Result<(), BulkheadError>
    where
        F: FnOnce() + Send + 'static,
    {
        let mut queue = self.sender.lock().unwrap();

        if queue.shutdown {
            return Err(BulkheadError::ShuttingDown);
        }

        // Check if queue is full
        if queue.queue.len() >= queue.max_queue_size {
            return Err(BulkheadError::QueueFull {
                queue_size: queue.queue.len(),
                max_size: queue.max_queue_size,
            });
        }

        queue.queue.push_back(Box::new(f));
        Ok(())
    }

    pub fn metrics(&self) -> BulkheadMetrics {
        let queue = self.sender.lock().unwrap();
        BulkheadMetrics {
            active_threads: queue.active_jobs,
            queued_jobs: queue.queue.len(),
            max_threads: self.config.max_threads,
            max_queue_size: self.config.max_queue_size,
        }
    }
}

impl Worker {
    fn new(id: usize, queue: Arc<Mutex<JobQueue>>) -> Self {
        let thread = thread::Builder::new()
            .name(format!("bulkhead-worker-{}", id))
            .spawn(move || {
                loop {
                    let job = {
                        let mut queue_guard = queue.lock().unwrap();

                        // Wait for a job or shutdown signal
                        while queue_guard.queue.is_empty() && !queue_guard.shutdown {
                            queue_guard = queue.lock().unwrap();
                            thread::sleep(Duration::from_millis(10));
                        }

                        if queue_guard.shutdown && queue_guard.queue.is_empty() {
                            return;
                        }

                        let job = queue_guard.queue.pop_front();
                        if job.is_some() {
                            queue_guard.active_jobs += 1;
                        }
                        job
                    };

                    if let Some(job) = job {
                        job();
                        
                        let mut queue_guard = queue.lock().unwrap();
                        queue_guard.active_jobs -= 1;
                    }
                }
            })
            .expect("Failed to spawn worker thread");

        Worker {
            thread: Some(thread),
        }
    }
}

impl Drop for BulkheadThreadPool {
    fn drop(&mut self) {
        {
            let mut queue = self.sender.lock().unwrap();
            queue.shutdown = true;
        }

        for worker in &mut self.workers {
            if let Some(thread) = worker.thread.take() {
                thread.join().unwrap();
            }
        }
    }
}

#[derive(Debug)]
pub enum BulkheadError {
    QueueFull { queue_size: usize, max_size: usize },
    ShuttingDown,
}

#[derive(Debug, Clone)]
pub struct BulkheadMetrics {
    pub active_threads: usize,
    pub queued_jobs: usize,
    pub max_threads: usize,
    pub max_queue_size: usize,
}
```

Caching strategies form the backbone of read scalability in distributed systems. Every cache represents a trade-off between consistency and performance: the more aggressively we cache, the more stale data we tolerate. Multi-tier caching architectures exploit this trade-off by deploying caches at different levels with different TTLs and invalidation strategies. Edge caches deployed close to users serve requests with minimal latency but tolerate the highest staleness. Application-level caches sit between the application server and the database, absorbing repeated queries within a single request context. Database query caches sit inside the database itself, accelerating repeated queries against the same underlying data.

The cache-aside pattern places the cache orthogonally to the data path, requiring the application to explicitly check the cache before querying the underlying datastore. On cache miss, the application queries the database, stores the result in the cache with an appropriate TTL, and returns the value to the caller. Cache invalidation becomes the application's responsibility—when data changes, the application must explicitly delete or update the corresponding cache entries. This pattern offers maximum flexibility but requires careful coordination between writers to prevent race conditions where stale data overwrites fresh data in the cache.

Write-through caches simplify consistency by routing all writes through the cache layer. When the application updates data, the cache layer synchronously writes to both the cache and the underlying datastore, ensuring that cached values always reflect committed state. This eliminates the staleness problem but introduces write latency—every update must wait for both the cache write and the database write to complete. Write-behind caching addresses this by asynchronously flushing updates to the database, improving write latency at the cost of potential data loss if the cache node fails before the flush completes.

```rust
use std::collections::HashMap;
use std::hash::Hash;
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

pub struct CacheEntry<V> {
    value: V,
    inserted_at: Instant,
    ttl: Duration,
}

impl<V> CacheEntry<V> {
    fn new(value: V, ttl: Duration) -> Self {
        Self {
            value,
            inserted_at: Instant::now(),
            ttl,
        }
    }

    fn is_expired(&self) -> bool {
        self.inserted_at.elapsed() > self.ttl
    }
}

pub struct LRUCache<K, V> {
    cache: Arc<RwLock<HashMap<K, CacheEntry<V>>>>,
    access_order: Arc<RwLock<Vec<K>>>,
    max_capacity: usize,
    default_ttl: Duration,
}

impl<K, V> LRUCache<K, V>
where
    K: Eq + Hash + Clone,
    V: Clone,
{
    pub fn new(max_capacity: usize, default_ttl: Duration) -> Self {
        Self {
            cache: Arc::new(RwLock::new(HashMap::with_capacity(max_capacity))),
            access_order: Arc::new(RwLock::new(Vec::with_capacity(max_capacity))),
            max_capacity,
            default_ttl,
        }
    }

    pub fn get(&self, key: &K) -> Option<V> {
        // Check cache
        let cache = self.cache.read().unwrap();
        
        if let Some(entry) = cache.get(key) {
            if entry.is_expired() {
                drop(cache);
                self.invalidate(key);
                return None;
            }
            
            let value = entry.value.clone();
            drop(cache);
            
            // Update LRU order
            self.touch(key);
            
            Some(value)
        } else {
            None
        }
    }

    pub fn put(&self, key: K, value: V) {
        self.put_with_ttl(key, value, self.default_ttl);
    }

    pub fn put_with_ttl(&self, key: K, value: V, ttl: Duration) {
        let mut cache = self.cache.write().unwrap();
        let mut access_order = self.access_order.write().unwrap();

        // If at capacity and key doesn't exist, evict LRU entry
        if cache.len() >= self.max_capacity && !cache.contains_key(&key) {
            if let Some(lru_key) = access_order.first().cloned() {
                cache.remove(&lru_key);
                access_order.retain(|k| k != &lru_key);
            }
        }

        // Insert or update entry
        cache.insert(key.clone(), CacheEntry::new(value, ttl));

        // Update access order
        access_order.retain(|k| k != &key);
        access_order.push(key);
    }

    pub fn invalidate(&self, key: &K) {
        let mut cache = self.cache.write().unwrap();
        let mut access_order = self.access_order.write().unwrap();
        
        cache.remove(key);
        access_order.retain(|k| k != key);
    }

    pub fn clear(&self) {
        let mut cache = self.cache.write().unwrap();
        let mut access_order = self.access_order.write().unwrap();
        
        cache.clear();
        access_order.clear();
    }

    fn touch(&self, key: &K) {
        let mut access_order = self.access_order.write().unwrap();
        access_order.retain(|k| k != key);
        access_order.push(key.clone());
    }

    pub fn len(&self) -> usize {
        self.cache.read().unwrap().len()
    }

    pub fn metrics(&self) -> CacheMetrics {
        let cache = self.cache.read().unwrap();
        
        let expired_count = cache.values()
            .filter(|entry| entry.is_expired())
            .count();

        CacheMetrics {
            size: cache.len(),
            capacity: self.max_capacity,
            expired_entries: expired_count,
        }
    }
}

#[derive(Debug, Clone)]
pub struct CacheMetrics {
    pub size: usize,
    pub capacity: usize,
    pub expired_entries: usize,
}

// Cache-aside pattern implementation
pub struct CacheAsideStore<K, V, D>
where
    K: Eq + Hash + Clone,
    V: Clone,
    D: Datastore<K, V>,
{
    cache: LRUCache<K, V>,
    datastore: Arc<D>,
}

pub trait Datastore<K, V>: Send + Sync {
    fn load(&self, key: &K) -> Result<Option<V>, DatastoreError>;
    fn store(&self, key: K, value: V) -> Result<(), DatastoreError>;
    fn delete(&self, key: &K) -> Result<(), DatastoreError>;
}

#[derive(Debug)]
pub enum DatastoreError {
    NotFound,
    ConnectionError(String),
    SerializationError(String),
}

impl<K, V, D> CacheAsideStore<K, V, D>
where
    K: Eq + Hash + Clone,
    V: Clone,
    D: Datastore<K, V>,
{
    pub fn new(cache_capacity: usize, ttl: Duration, datastore: D) -> Self {
        Self {
            cache: LRUCache::new(cache_capacity, ttl),
            datastore: Arc::new(datastore),
        }
    }

    pub fn get(&self, key: &K) -> Result<Option<V>, DatastoreError> {
        // Try cache first
        if let Some(value) = self.cache.get(key) {
            return Ok(Some(value));
        }

        // Cache miss - load from datastore
        match self.datastore.load(key)? {
            Some(value) => {
                // Populate cache
                self.cache.put(key.clone(), value.clone());
                Ok(Some(value))
            }
            None => Ok(None),
        }
    }

    pub fn put(&self, key: K, value: V) -> Result<(), DatastoreError> {
        // Write to datastore first
        self.datastore.store(key.clone(), value.clone())?;
        
        // Then update cache
        self.cache.put(key, value);
        
        Ok(())
    }

    pub fn delete(&self, key: &K) -> Result<(), DatastoreError> {
        // Delete from datastore
        self.datastore.delete(key)?;
        
        // Invalidate cache
        self.cache.invalidate(key);
        
        Ok(())
    }
}
```

Data replication trades consistency for availability and read scalability. In a leader-follower topology, all writes flow to a single leader node which replicates them asynchronously to multiple follower replicas. Clients can read from any replica, distributing read load across the cluster, but may observe stale data if they query a follower that has not yet received recent updates. The replication lag—the time between a write committing on the leader and propagating to followers—determines the window of potential inconsistency. Under normal operation, replication lag remains in the milliseconds, but network partitions or follower overload can extend it to seconds or minutes.

Synchronous replication eliminates staleness by blocking writes until all replicas acknowledge receipt, but dramatically increases write latency and reduces availability—a single slow or partitioned replica renders the entire cluster unable to commit writes. The middle ground is semi-synchronous replication, where writes must replicate to at least one follower before acknowledging to the client, ensuring that data survives leader failure while maintaining acceptable write latency. This is the replication mode used by most production databases including PostgreSQL's synchronous replication and MySQL's semi-synchronous replication.

Multi-leader replication allows writes to multiple nodes simultaneously, eliminating the single-writer bottleneck and improving write availability during partitions. Each leader accepts writes independently and asynchronously replicates them to all other leaders. This introduces the possibility of write conflicts when two leaders concurrently modify the same record. Conflict resolution strategies range from last-write-wins (using timestamps or version vectors to pick a winner, discarding the loser) to application-level merge functions that combine conflicting updates into a consistent final state. CRDTs—Conflict-Free Replicated Data Types—provide a mathematical framework for conflict-free merging, defining data structures where concurrent operations commute such that all replicas converge to the same state regardless of operation order.

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

#[derive(Clone, Debug)]
pub struct VersionedValue<V> {
    value: V,
    version: u64,
    timestamp: u64,
}

impl<V> VersionedValue<V> {
    fn new(value: V, version: u64) -> Self {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;
        
        Self {
            value,
            version,
            timestamp,
        }
    }
}

pub struct ReplicatedStore<K, V> {
    local_data: Arc<RwLock<HashMap<K, VersionedValue<V>>>>,
    node_id: u64,
    peers: Arc<RwLock<Vec<ReplicationPeer<K, V>>>>,
    replication_mode: ReplicationMode,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ReplicationMode {
    Async,
    Sync,
    SemiSync { min_replicas: usize },
}

pub struct ReplicationPeer<K, V> {
    peer_id: u64,
    replication_queue: Arc<RwLock<Vec<ReplicationLog<K, V>>>>,
}

#[derive(Clone, Debug)]
struct ReplicationLog<K, V> {
    key: K,
    value: VersionedValue<V>,
    operation: ReplicationOp,
}

#[derive(Clone, Copy, Debug, PartialEq)]
enum ReplicationOp {
    Write,
    Delete,
}

impl<K, V> ReplicatedStore<K, V>
where
    K: Eq + std::hash::Hash + Clone + Send + Sync + 'static,
    V: Clone + Send + Sync + 'static,
{
    pub fn new(node_id: u64, replication_mode: ReplicationMode) -> Self {
        Self {
            local_data: Arc::new(RwLock::new(HashMap::new())),
            node_id,
            peers: Arc::new(RwLock::new(Vec::new())),
            replication_mode,
        }
    }

    pub fn add_peer(&self, peer_id: u64) {
        let mut peers = self.peers.write().unwrap();
        peers.push(ReplicationPeer {
            peer_id,
            replication_queue: Arc::new(RwLock::new(Vec::new())),
        });
    }

    pub fn write(&self, key: K, value: V) -> Result<(), ReplicationError> {
        let version = self.next_version();
        let versioned = VersionedValue::new(value, version);

        // Write locally first
        {
            let mut data = self.local_data.write().unwrap();
            data.insert(key.clone(), versioned.clone());
        }

        // Replicate to peers based on mode
        match self.replication_mode {
            ReplicationMode::Async => {
                self.replicate_async(key, versioned, ReplicationOp::Write);
                Ok(())
            }
            ReplicationMode::Sync => {
                self.replicate_sync(key, versioned, ReplicationOp::Write)
            }
            ReplicationMode::SemiSync { min_replicas } => {
                self.replicate_semi_sync(key, versioned, ReplicationOp::Write, min_replicas)
            }
        }
    }

    pub fn read(&self, key: &K) -> Option<V> {
        let data = self.local_data.read().unwrap();
        data.get(key).map(|v| v.value.clone())
    }

    pub fn delete(&self, key: &K) -> Result<(), ReplicationError> {
        let version = self.next_version();
        let dummy_value = {
            let data = self.local_data.read().unwrap();
            data.get(key)?.value.clone()
        };
        
        let versioned = VersionedValue::new(dummy_value, version);

        // Delete locally
        {
            let mut data = self.local_data.write().unwrap();
            data.remove(key);
        }

        // Replicate deletion
        match self.replication_mode {
            ReplicationMode::Async => {
                self.replicate_async(key.clone(), versioned, ReplicationOp::Delete);
                Ok(())
            }
            ReplicationMode::Sync => {
                self.replicate_sync(key.clone(), versioned, ReplicationOp::Delete)
            }
            ReplicationMode::SemiSync { min_replicas } => {
                self.replicate_semi_sync(key.clone(), versioned, ReplicationOp::Delete, min_replicas)
            }
        }
    }

    fn next_version(&self) -> u64 {
        let data = self.local_data.read().unwrap();
        data.values()
            .map(|v| v.version)
            .max()
            .unwrap_or(0) + 1
    }

    fn replicate_async(&self, key: K, value: VersionedValue<V>, op: ReplicationOp) {
        let peers = self.peers.read().unwrap();
        
        for peer in peers.iter() {
            let mut queue = peer.replication_queue.write().unwrap();
            queue.push(ReplicationLog {
                key: key.clone(),
                value: value.clone(),
                operation: op,
            });
        }
    }

    fn replicate_sync(&self, key: K, value: VersionedValue<V>, op: ReplicationOp) 
        -> Result<(), ReplicationError> 
    {
        let peers = self.peers.read().unwrap();
        
        if peers.is_empty() {
            return Ok(());
        }

        // Simulate synchronous replication
        for peer in peers.iter() {
            let mut queue = peer.replication_queue.write().unwrap();
            queue.push(ReplicationLog {
                key: key.clone(),
                value: value.clone(),
                operation: op,
            });
        }

        Ok(())
    }

    fn replicate_semi_sync(
        &self,
        key: K,
        value: VersionedValue<V>,
        op: ReplicationOp,
        min_replicas: usize,
    ) -> Result<(), ReplicationError> {
        let peers = self.peers.read().unwrap();
        
        if peers.len() < min_replicas {
            return Err(ReplicationError::InsufficientReplicas {
                required: min_replicas,
                available: peers.len(),
            });
        }

        // Replicate to minimum required replicas synchronously
        for peer in peers.iter().take(min_replicas) {
            let mut queue = peer.replication_queue.write().unwrap();
            queue.push(ReplicationLog {
                key: key.clone(),
                value: value.clone(),
                operation: op,
            });
        }

        // Replicate to remaining replicas asynchronously
        for peer in peers.iter().skip(min_replicas) {
            let mut queue = peer.replication_queue.write().unwrap();
            queue.push(ReplicationLog {
                key: key.clone(),
                value: value.clone(),
                operation: op,
            });
        }

        Ok(())
    }

    pub fn apply_replication_log(&self, key: K, value: VersionedValue<V>, op: ReplicationOp) {
        match op {
            ReplicationOp::Write => {
                let mut data = self.local_data.write().unwrap();
                
                // Only apply if version is newer (last-write-wins)
                if let Some(existing) = data.get(&key) {
                    if value.version <= existing.version {
                        return;
                    }
                }
                
                data.insert(key, value);
            }
            ReplicationOp::Delete => {
                let mut data = self.local_data.write().unwrap();
                data.remove(&key);
            }
        }
    }
}

#[derive(Debug)]
pub enum ReplicationError {
    InsufficientReplicas { required: usize, available: usize },
    PeerUnavailable(u64),
    Timeout,
}
```

Sharding partitions data across multiple independent nodes such that each shard holds a disjoint subset of the total dataset. Hash-based sharding applies a hash function to the partition key—typically a user ID, tenant ID, or other high-cardinality dimension—and routes the request to the shard responsible for that hash range. This distributes load evenly across shards as long as the partition key exhibits uniform distribution. Range-based sharding assigns contiguous ranges of the keyspace to each shard, allowing efficient range scans but risking hotspots if access patterns concentrate on specific ranges.

Consistent hashing addresses the resharding problem—the operational complexity of adding or removing shards from a hash-partitioned cluster. In naive hash sharding, changing the number of shards requires rehashing and migrating every key in the system. Consistent hashing places both shards and keys on a circular hash ring. Each shard owns the arc of the ring from its position clockwise to the next shard. Adding a new shard splits one existing shard's range, requiring migration of only a fraction of the data. Virtual nodes—mapping each physical shard to multiple positions on the ring—improve load balancing by giving each shard multiple smaller arcs rather than one large contiguous range.

```rust
use std::collections::{BTreeMap, HashMap};
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;

pub struct ConsistentHashRing<N> {
    ring: BTreeMap<u64, N>,
    virtual_nodes: usize,
    nodes: HashMap<String, N>,
}

impl<N> ConsistentHashRing<N>
where
    N: Clone,
{
    pub fn new(virtual_nodes: usize) -> Self {
        Self {
            ring: BTreeMap::new(),
            virtual_nodes,
            nodes: HashMap::new(),
        }
    }

    pub fn add_node(&mut self, node_id: String, node: N) {
        // Add virtual nodes to the ring
        for i in 0..self.virtual_nodes {
            let virtual_key = format!("{}:{}", node_id, i);
            let hash = self.hash_key(&virtual_key);
            self.ring.insert(hash, node.clone());
        }
        
        self.nodes.insert(node_id, node);
    }

    pub fn remove_node(&mut self, node_id: &str) {
        // Remove all virtual nodes for this physical node
        for i in 0..self.virtual_nodes {
            let virtual_key = format!("{}:{}", node_id, i);
            let hash = self.hash_key(&virtual_key);
            self.ring.remove(&hash);
        }
        
        self.nodes.remove(node_id);
    }

    pub fn get_node<K: Hash>(&self, key: &K) -> Option<&N> {
        if self.ring.is_empty() {
            return None;
        }

        let hash = self.hash_value(key);
        
        // Find first node clockwise from hash position
        if let Some((_, node)) = self.ring.range(hash..).next() {
            Some(node)
        } else {
            // Wrap around to first node
            self.ring.values().next()
        }
    }

    pub fn get_node_with_replicas<K: Hash>(&self, key: &K, replica_count: usize) 
        -> Vec<&N> 
    {
        if self.ring.is_empty() {
            return Vec::new();
        }

        let hash = self.hash_value(key);
        let mut replicas = Vec::with_capacity(replica_count);
        let mut seen_positions = std::collections::HashSet::new();

        // Collect unique nodes clockwise from hash position
        for (_, node) in self.ring.range(hash..) {
            let node_ptr = node as *const N as usize;
            if !seen_positions.contains(&node_ptr) {
                replicas.push(node);
                seen_positions.insert(node_ptr);
                
                if replicas.len() >= replica_count {
                    return replicas;
                }
            }
        }

        // Wrap around to beginning
        for (_, node) in self.ring.iter() {
            let node_ptr = node as *const N as usize;
            if !seen_positions.contains(&node_ptr) {
                replicas.push(node);
                seen_positions.insert(node_ptr);
                
                if replicas.len() >= replica_count {
                    return replicas;
                }
            }
        }

        replicas
    }

    fn hash_key(&self, key: &str) -> u64 {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish()
    }

    fn hash_value<K: Hash>(&self, key: &K) -> u64 {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        hasher.finish()
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    pub fn distribution_stats(&self) -> HashMap<String, usize> {
        let mut stats = HashMap::new();
        
        for (node_id, _) in &self.nodes {
            stats.insert(node_id.clone(), 0);
        }

        // Count virtual nodes per physical node
        let mut node_map: HashMap<usize, String> = HashMap::new();
        for (node_id, node) in &self.nodes {
            let node_ptr = node as *const N as usize;
            node_map.insert(node_ptr, node_id.clone());
        }

        for node in self.ring.values() {
            let node_ptr = node as *const N as usize;
            if let Some(node_id) = node_map.get(&node_ptr) {
                *stats.get_mut(node_id).unwrap() += 1;
            }
        }

        stats
    }
}

// Sharded datastore implementation
pub struct ShardedStore<K, V> {
    shards: ConsistentHashRing<Shard<K, V>>,
    replication_factor: usize,
}

struct Shard<K, V> {
    id: String,
    data: Arc<RwLock<HashMap<K, V>>>,
}

impl<K, V> Clone for Shard<K, V> {
    fn clone(&self) -> Self {
        Self {
            id: self.id.clone(),
            data: Arc::clone(&self.data),
        }
    }
}

impl<K, V> ShardedStore<K, V>
where
    K: Eq + Hash + Clone,
    V: Clone,
{
    pub fn new(replication_factor: usize) -> Self {
        Self {
            shards: ConsistentHashRing::new(150), // 150 virtual nodes per shard
            replication_factor,
        }
    }

    pub fn add_shard(&mut self, shard_id: String) {
        let shard = Shard {
            id: shard_id.clone(),
            data: Arc::new(RwLock::new(HashMap::new())),
        };
        
        self.shards.add_node(shard_id, shard);
    }

    pub fn write(&self, key: K, value: V) -> Result<(), ShardError> {
        let replicas = self.shards.get_node_with_replicas(&key, self.replication_factor);
        
        if replicas.is_empty() {
            return Err(ShardError::NoShardsAvailable);
        }

        // Write to all replicas
        for shard in replicas {
            let mut data = shard.data.write().unwrap();
            data.insert(key.clone(), value.clone());
        }

        Ok(())
    }

    pub fn read(&self, key: &K) -> Result<Option<V>, ShardError> {
        let shard = self.shards.get_node(key)
            .ok_or(ShardError::NoShardsAvailable)?;
        
        let data = shard.data.read().unwrap();
        Ok(data.get(key).cloned())
    }

    pub fn delete(&self, key: &K) -> Result<(), ShardError> {
        let replicas = self.shards.get_node_with_replicas(key, self.replication_factor);
        
        if replicas.is_empty() {
            return Err(ShardError::NoShardsAvailable);
        }

        // Delete from all replicas
        for shard in replicas {
            let mut data = shard.data.write().unwrap();
            data.remove(key);
        }

        Ok(())
    }

    pub fn shard_distribution(&self) -> HashMap<String, usize> {
        self.shards.distribution_stats()
    }
}

#[derive(Debug)]
pub enum ShardError {
    NoShardsAvailable,
    ReplicationFailure,
}
```

Observability in distributed systems requires correlation across three signal types: metrics, traces, and logs. Metrics provide high-level aggregate statistics—request rates, error percentages, latency percentiles—typically scraped from instrumented endpoints at regular intervals. Time-series databases like Prometheus store these metrics efficiently using delta encoding and downsampling. Distributed traces reconstruct the causal flow of a single request across multiple services by propagating a trace context—a globally unique trace ID and per-span parent ID—through every service invocation. Traces reveal which service calls contributed to tail latency, which dependencies timed out, and where errors originated. Structured logs capture the detailed state of individual operations, including request parameters, intermediate values, and exception stack traces.

The RED method provides a minimal set of metrics for service-level monitoring: Rate (requests per second), Errors (error count or percentage), and Duration (latency distribution). These three signals, monitored for every service endpoint, provide sufficient information to detect most classes of operational problems. The USE method extends this framework to resource monitoring: Utilization (percentage of capacity in use), Saturation (queue depth or backlog), and Errors (resource-level failures like disk errors or out-of-memory conditions). Together, RED and USE cover both service-level and infrastructure-level observability.

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

pub struct MetricsCollector {
    metrics: Arc<RwLock<HashMap<String, Metric>>>,
}

#[derive(Clone, Debug)]
pub enum Metric {
    Counter { value: u64 },
    Gauge { value: f64 },
    Histogram { values: Vec<f64>, buckets: Vec<f64> },
    Summary { count: u64, sum: f64, quantiles: HashMap<String, f64> },
}

impl MetricsCollector {
    pub fn new() -> Self {
        Self {
            metrics: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub fn inc_counter(&self, name: &str, value: u64) {
        let mut metrics = self.metrics.write().unwrap();
        
        metrics.entry(name.to_string())
            .and_modify(|m| {
                if let Metric::Counter { value: v } = m {
                    *v += value;
                }
            })
            .or_insert(Metric::Counter { value });
    }

    pub fn set_gauge(&self, name: &str, value: f64) {
        let mut metrics = self.metrics.write().unwrap();
        metrics.insert(name.to_string(), Metric::Gauge { value });
    }

    pub fn observe_histogram(&self, name: &str, value: f64) {
        let mut metrics = self.metrics.write().unwrap();
        
        metrics.entry(name.to_string())
            .and_modify(|m| {
                if let Metric::Histogram { values, .. } = m {
                    values.push(value);
                }
            })
            .or_insert_with(|| {
                Metric::Histogram {
                    values: vec![value],
                    buckets: vec![0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
                }
            });
    }

    pub fn get_histogram_percentile(&self, name: &str, percentile: f64) -> Option<f64> {
        let metrics = self.metrics.read().unwrap();
        
        if let Some(Metric::Histogram { values, .. }) = metrics.get(name) {
            if values.is_empty() {
                return None;
            }
            
            let mut sorted = values.clone();
            sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
            
            let index = ((sorted.len() as f64 - 1.0) * percentile).ceil() as usize;
            Some(sorted[index.min(sorted.len() - 1)])
        } else {
            None
        }
    }

    pub fn get_metrics(&self) -> HashMap<String, Metric> {
        self.metrics.read().unwrap().clone()
    }

    pub fn reset(&self) {
        let mut metrics = self.metrics.write().unwrap();
        metrics.clear();
    }
}

// RED metrics implementation
pub struct REDMetrics {
    collector: MetricsCollector,
    service_name: String,
}

impl REDMetrics {
    pub fn new(service_name: String) -> Self {
        Self {
            collector: MetricsCollector::new(),
            service_name,
        }
    }

    pub fn record_request(&self, endpoint: &str, duration: Duration, is_error: bool) {
        let prefix = format!("{}_{}", self.service_name, endpoint);
        
        // Rate: increment request counter
        self.collector.inc_counter(&format!("{}_requests_total", prefix), 1);
        
        // Errors: increment error counter if applicable
        if is_error {
            self.collector.inc_counter(&format!("{}_errors_total", prefix), 1);
        }
        
        // Duration: observe latency
        self.collector.observe_histogram(
            &format!("{}_duration_seconds", prefix),
            duration.as_secs_f64(),
        );
    }

    pub fn get_rate(&self, endpoint: &str) -> u64 {
        let key = format!("{}_{}_requests_total", self.service_name, endpoint);
        let metrics = self.collector.get_metrics();
        
        if let Some(Metric::Counter { value }) = metrics.get(&key) {
            *value
        } else {
            0
        }
    }

    pub fn get_error_rate(&self, endpoint: &str) -> f64 {
        let requests_key = format!("{}_{}_requests_total", self.service_name, endpoint);
        let errors_key = format!("{}_{}_errors_total", self.service_name, endpoint);
        let metrics = self.collector.get_metrics();
        
        let total_requests = if let Some(Metric::Counter { value }) = metrics.get(&requests_key) {
            *value as f64
        } else {
            return 0.0;
        };
        
        let total_errors = if let Some(Metric::Counter { value }) = metrics.get(&errors_key) {
            *value as f64
        } else {
            return 0.0;
        };
        
        if total_requests == 0.0 {
            0.0
        } else {
            (total_errors / total_requests) * 100.0
        }
    }

    pub fn get_latency_percentile(&self, endpoint: &str, percentile: f64) -> Option<f64> {
        let key = format!("{}_{}_duration_seconds", self.service_name, endpoint);
        self.collector.get_histogram_percentile(&key, percentile)
    }
}

// Distributed tracing implementation
use uuid::Uuid;

#[derive(Clone, Debug)]
pub struct TraceContext {
    pub trace_id: String,
    pub span_id: String,
    pub parent_span_id: Option<String>,
}

impl TraceContext {
    pub fn new() -> Self {
        Self {
            trace_id: Uuid::new_v4().to_string(),
            span_id: Uuid::new_v4().to_string(),
            parent_span_id: None,
        }
    }

    pub fn child_span(&self) -> Self {
        Self {
            trace_id: self.trace_id.clone(),
            span_id: Uuid::new_v4().to_string(),
            parent_span_id: Some(self.span_id.clone()),
        }
    }
}

#[derive(Clone, Debug)]
pub struct Span {
    pub trace_context: TraceContext,
    pub operation_name: String,
    pub start_time: Instant,
    pub end_time: Option<Instant>,
    pub tags: HashMap<String, String>,
    pub logs: Vec<SpanLog>,
}

#[derive(Clone, Debug)]
pub struct SpanLog {
    pub timestamp: Instant,
    pub fields: HashMap<String, String>,
}

impl Span {
    pub fn new(operation_name: String, trace_context: TraceContext) -> Self {
        Self {
            trace_context,
            operation_name,
            start_time: Instant::now(),
            end_time: None,
            tags: HashMap::new(),
            logs: Vec::new(),
        }
    }

    pub fn set_tag(&mut self, key: String, value: String) {
        self.tags.insert(key, value);
    }

    pub fn log(&mut self, fields: HashMap<String, String>) {
        self.logs.push(SpanLog {
            timestamp: Instant::now(),
            fields,
        });
    }

    pub fn finish(&mut self) {
        self.end_time = Some(Instant::now());
    }

    pub fn duration(&self) -> Option<Duration> {
        self.end_time.map(|end| end.duration_since(self.start_time))
    }
}

pub struct Tracer {
    spans: Arc<RwLock<Vec<Span>>>,
}

impl Tracer {
    pub fn new() -> Self {
        Self {
            spans: Arc::new(RwLock::new(Vec::new())),
        }
    }

    pub fn start_span(&self, operation_name: String, context: Option<TraceContext>) -> Span {
        let trace_context = context.unwrap_or_else(TraceContext::new);
        Span::new(operation_name, trace_context)
    }

    pub fn record_span(&self, span: Span) {
        let mut spans = self.spans.write().unwrap();
        spans.push(span);
    }

    pub fn get_trace(&self, trace_id: &str) -> Vec<Span> {
        let spans = self.spans.read().unwrap();
        spans.iter()
            .filter(|s| s.trace_context.trace_id == trace_id)
            .cloned()
            .collect()
    }
}
```

## 3. High-Performance Optimization & Failure Modes

Load balancing distributes incoming requests across multiple backend instances, but naive round-robin load balancing fails to account for heterogeneous server capacity or dynamic load changes. Weighted round-robin assigns each backend a weight proportional to its capacity, but still cannot adapt to runtime conditions. Least-connections routing tracks active connections per backend and routes new requests to the least-loaded instance. This works well for long-lived connections but provides no visibility into actual request processing time. Latency-aware load balancing measures response time per backend and routes requests preferentially to low-latency instances, automatically avoiding slow or degraded nodes.

Connection pooling reduces the overhead of establishing new TCP connections and TLS handshakes by maintaining a pool of persistent connections to each backend. However, connection pools introduce their own failure modes. If pool size is too small, requests queue waiting for available connections, increasing latency. If pool size is too large, idle connections consume memory and may be reset by intermediate firewalls or load balancers due to inactivity. Connection validation—periodic health checks that verify pooled connections remain alive—prevents clients from attempting to use stale connections that have been closed by the server.

```rust
use std::collections::VecDeque;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

pub struct LoadBalancer<B> {
    backends: Arc<Mutex<Vec<Backend<B>>>>,
    strategy: LoadBalancingStrategy,
}

struct Backend<B> {
    instance: B,
    weight: u32,
    active_connections: u32,
    total_requests: u64,
    latency_samples: VecDeque<Duration>,
    last_health_check: Instant,
    healthy: bool,
}

#[derive(Clone, Copy, Debug)]
pub enum LoadBalancingStrategy {
    RoundRobin,
    WeightedRoundRobin,
    LeastConnections,
    LatencyAware,
}

impl<B> LoadBalancer<B>
where
    B: Clone,
{
    pub fn new(strategy: LoadBalancingStrategy) -> Self {
        Self {
            backends: Arc::new(Mutex::new(Vec::new())),
            strategy,
        }
    }

    pub fn add_backend(&self, instance: B, weight: u32) {
        let mut backends = self.backends.lock().unwrap();
        backends.push(Backend {
            instance,
            weight,
            active_connections: 0,
            total_requests: 0,
            latency_samples: VecDeque::with_capacity(100),
            last_health_check: Instant::now(),
            healthy: true,
        });
    }

    pub fn select_backend(&self) -> Option<B> {
        let mut backends = self.backends.lock().unwrap();
        
        // Filter out unhealthy backends
        let healthy_backends: Vec<usize> = backends.iter()
            .enumerate()
            .filter(|(_, b)| b.healthy)
            .map(|(i, _)| i)
            .collect();
        
        if healthy_backends.is_empty() {
            return None;
        }

        let selected_idx = match self.strategy {
            LoadBalancingStrategy::RoundRobin => {
                self.round_robin_select(&healthy_backends, &backends)
            }
            LoadBalancingStrategy::WeightedRoundRobin => {
                self.weighted_round_robin_select(&healthy_backends, &backends)
            }
            LoadBalancingStrategy::LeastConnections => {
                self.least_connections_select(&healthy_backends, &backends)
            }
            LoadBalancingStrategy::LatencyAware => {
                self.latency_aware_select(&healthy_backends, &backends)
            }
        };

        backends[selected_idx].active_connections += 1;
        backends[selected_idx].total_requests += 1;
        
        Some(backends[selected_idx].instance.clone())
    }

    pub fn record_completion(&self, backend: &B, latency: Duration) 
    where
        B: PartialEq,
    {
        let mut backends = self.backends.lock().unwrap();
        
        if let Some(backend_entry) = backends.iter_mut()
            .find(|b| &b.instance == backend) 
        {
            backend_entry.active_connections = backend_entry.active_connections.saturating_sub(1);
            
            // Keep last 100 latency samples for latency-aware routing
            if backend_entry.latency_samples.len() >= 100 {
                backend_entry.latency_samples.pop_front();
            }
            backend_entry.latency_samples.push_back(latency);
        }
    }

    fn round_robin_select(&self, healthy: &[usize], backends: &[Backend<B>]) -> usize {
        // Select backend with lowest total requests
        healthy.iter()
            .min_by_key(|&&idx| backends[idx].total_requests)
            .copied()
            .unwrap()
    }

    fn weighted_round_robin_select(&self, healthy: &[usize], backends: &[Backend<B>]) -> usize {
        // Calculate weighted scores
        let mut best_idx = healthy[0];
        let mut best_score = f64::MIN;

        for &idx in healthy {
            let backend = &backends[idx];
            let score = backend.weight as f64 / (backend.total_requests + 1) as f64;
            
            if score > best_score {
                best_score = score;
                best_idx = idx;
            }
        }

        best_idx
    }

    fn least_connections_select(&self, healthy: &[usize], backends: &[Backend<B>]) -> usize {
        healthy.iter()
            .min_by_key(|&&idx| backends[idx].active_connections)
            .copied()
            .unwrap()
    }

    fn latency_aware_select(&self, healthy: &[usize], backends: &[Backend<B>]) -> usize {
        let mut best_idx = healthy[0];
        let mut best_latency = Duration::MAX;

        for &idx in healthy {
            let backend = &backends[idx];
            
            if backend.latency_samples.is_empty() {
                // Prefer backends with no latency data (new backends)
                return idx;
            }

            let avg_latency: Duration = backend.latency_samples.iter()
                .sum::<Duration>() / backend.latency_samples.len() as u32;
            
            if avg_latency < best_latency {
                best_latency = avg_latency;
                best_idx = idx;
            }
        }

        best_idx
    }

    pub fn mark_unhealthy(&self, backend: &B) 
    where
        B: PartialEq,
    {
        let mut backends = self.backends.lock().unwrap();
        
        if let Some(backend_entry) = backends.iter_mut()
            .find(|b| &b.instance == backend) 
        {
            backend_entry.healthy = false;
            backend_entry.last_health_check = Instant::now();
        }
    }

    pub fn mark_healthy(&self, backend: &B) 
    where
        B: PartialEq,
    {
        let mut backends = self.backends.lock().unwrap();
        
        if let Some(backend_entry) = backends.iter_mut()
            .find(|b| &b.instance == backend) 
        {
            backend_entry.healthy = true;
            backend_entry.last_health_check = Instant::now();
        }
    }
}
```

Rate limiting protects services from excessive load by enforcing maximum request rates per client or globally. The token bucket algorithm maintains a bucket with a fixed capacity of tokens, refilling at a constant rate. Each request consumes one token; requests arriving when the bucket is empty are rejected. This allows brief bursts up to bucket capacity while enforcing an average rate over longer time windows. Sliding window rate limiting tracks request counts in fixed-size time buckets, rejecting requests when the count across the current window exceeds the limit. This provides more predictable behavior than token buckets but requires more memory to store per-client state.

Distributed rate limiting introduces the challenge of coordinating limits across multiple frontend instances. Centralizing rate limit state in a shared cache like Redis provides exact enforcement but adds latency and a dependency to the critical path. Local rate limiting with gossip-based synchronization allows each instance to enforce limits independently while periodically exchanging state with peers, trading perfect accuracy for reduced coordination overhead. The optimal choice depends on whether the system prioritizes strict enforcement or low latency.

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

pub struct TokenBucketRateLimiter {
    buckets: Arc<Mutex<HashMap<String, TokenBucket>>>,
    capacity: u32,
    refill_rate: u32,
    refill_interval: Duration,
}

struct TokenBucket {
    tokens: f64,
    last_refill: Instant,
}

impl TokenBucketRateLimiter {
    pub fn new(capacity: u32, refill_rate: u32, refill_interval: Duration) -> Self {
        Self {
            buckets: Arc::new(Mutex::new(HashMap::new())),
            capacity,
            refill_rate,
            refill_interval,
        }
    }

    pub fn allow(&self, client_id: &str) -> bool {
        self.allow_n(client_id, 1)
    }

    pub fn allow_n(&self, client_id: &str, n: u32) -> bool {
        let mut buckets = self.buckets.lock().unwrap();
        let now = Instant::now();

        let bucket = buckets.entry(client_id.to_string())
            .or_insert_with(|| TokenBucket {
                tokens: self.capacity as f64,
                last_refill: now,
            });

        // Refill tokens based on elapsed time
        let elapsed = now.duration_since(bucket.last_refill);
        let intervals = elapsed.as_secs_f64() / self.refill_interval.as_secs_f64();
        let tokens_to_add = intervals * self.refill_rate as f64;
        
        bucket.tokens = (bucket.tokens + tokens_to_add).min(self.capacity as f64);
        bucket.last_refill = now;

        // Try to consume tokens
        if bucket.tokens >= n as f64 {
            bucket.tokens -= n as f64;
            true
        } else {
            false
        }
    }

    pub fn remaining(&self, client_id: &str) -> u32 {
        let buckets = self.buckets.lock().unwrap();
        
        buckets.get(client_id)
            .map(|b| b.tokens as u32)
            .unwrap_or(self.capacity)
    }
}

pub struct SlidingWindowRateLimiter {
    windows: Arc<Mutex<HashMap<String, SlidingWindow>>>,
    window_size: Duration,
    max_requests: u32,
}

struct SlidingWindow {
    requests: VecDeque<Instant>,
}

impl SlidingWindowRateLimiter {
    pub fn new(window_size: Duration, max_requests: u32) -> Self {
        Self {
            windows: Arc::new(Mutex::new(HashMap::new())),
            window_size,
            max_requests,
        }
    }

    pub fn allow(&self, client_id: &str) -> bool {
        let mut windows = self.windows.lock().unwrap();
        let now = Instant::now();

        let window = windows.entry(client_id.to_string())
            .or_insert_with(|| SlidingWindow {
                requests: VecDeque::new(),
            });

        // Remove requests outside the current window
        let cutoff = now - self.window_size;
        while let Some(&oldest) = window.requests.front() {
            if oldest < cutoff {
                window.requests.pop_front();
            } else {
                break;
            }
        }

        // Check if we can accept this request
        if window.requests.len() < self.max_requests as usize {
            window.requests.push_back(now);
            true
        } else {
            false
        }
    }

    pub fn remaining(&self, client_id: &str) -> u32 {
        let windows = self.windows.lock().unwrap();
        
        windows.get(client_id)
            .map(|w| self.max_requests.saturating_sub(w.requests.len() as u32))
            .unwrap_or(self.max_requests)
    }
}
```

Backpressure mechanisms prevent fast producers from overwhelming slow consumers by explicitly signaling when the consumer cannot keep pace. In streaming systems, backpressure propagates from consumer to producer through the network protocol—TCP's flow control windows provide natural backpressure at the transport layer, while application-level protocols like gRPC implement credit-based flow control where consumers grant credits authorizing the producer to send more data. When the consumer's processing queue fills, it stops granting credits, causing the producer to buffer or drop data. Reactive Streams and similar abstractions formalize backpressure through publisher-subscriber interfaces where subscribers explicitly request data rather than having it pushed unconditionally.

Graceful degradation accepts that not all system features are equally critical and defines fallback behaviors when dependencies fail. When a recommendation service times out, an e-commerce site can fall back to displaying popular items instead of personalized recommendations. When a fraud detection service is unavailable, a payment processor can continue processing transactions below a threshold amount while queuing larger transactions for manual review. These decisions trade perfect functionality for continued availability, recognizing that partial operation is preferable to complete failure.

Chaos engineering proactively injects failures into production systems to validate resilience mechanisms. Netflix's Chaos Monkey randomly terminates EC2 instances during business hours, forcing teams to design for instance failure as a routine occurrence rather than a catastrophic event. Latency injection adds artificial delays to service calls, exposing timeout configurations that are too aggressive or too lenient. Resource starvation tests limit CPU, memory, or network bandwidth to verify that resource exhaustion in one subsystem does not cascade to others. These controlled failure experiments build confidence that systems will behave correctly during real outages.

The trade-off between consistency and performance manifests most starkly in distributed transactions. Two-phase commit provides linearizable consistency across multiple participants by coordinating a prepare phase and a commit phase, but blocks all participants until all respond, amplifying tail latency. Sagas decompose long-running transactions into sequences of local transactions with compensating operations that undo each step if later steps fail. This provides eventual consistency without distributed locking but requires careful design of compensation logic and accepts that intermediate states are visible to concurrent readers. The choice between these approaches depends on whether your correctness requirements demand strong consistency or whether eventual consistency suffices.

Multi-region deployments raise fundamental questions about data locality, replication lag, and failure domains. Active-passive topologies designate one region as primary, serving all writes and synchronously replicating to passive secondaries. Failover to a secondary requires promoting it to primary and redirecting traffic—an operation that takes seconds to minutes. Active-active topologies allow writes in all regions, requiring conflict resolution when concurrent updates modify the same data. This improves availability during regional failures but introduces complexity in maintaining consistency. The CAP theorem remains undefeated: you cannot have both perfect consistency and availability during network partitions. Every architecture chooses where to make compromises.

At trillion-scale, even rare failure modes occur constantly. A service with 99.99% availability fails for 52 minutes per year, but when you operate ten thousand services, some subset is always failing. This reality drives architectural patterns like cell-based isolation where each cell operates independently, blast radius limitation where failures cannot escape their failure domain, and automated remediation where systems heal themselves faster than human operators can respond. The goal shifts from preventing failure to containing its impact—ensuring that when components fail, as they inevitably will, the system continues delivering value.
