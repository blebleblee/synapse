# Lesson 02: Kafka Producers and Consumers

## 1. First-Principles Intuition & Invariants

### 1.1 The Fundamental Asymmetry

Kafka's producer-consumer model rests on a single architectural invariant: **writes are append-only, reads are position-based**. This asymmetry unlocks all performance characteristics:

- **Producers** transform application events into immutable log entries with monotonic offsets
- **Consumers** maintain independent cursors (offsets) into the shared immutable log
- **The log itself** is the only shared state, and it never mutates—only appends

This design eliminates coordination between readers and writers. A producer writing at offset 1,000,000 has zero runtime interaction with a consumer reading offset 500,000.

### 1.2 Physical Invariants

**Sequential I/O Dominance**: Modern storage achieves 500+ MB/s sequential writes but only 100 IOPS for random writes. Kafka's append-only log transforms all writes into sequential I/O, mapping directly to hardware strengths.

**Zero-Copy Transfer**: Data flows from disk to network socket without passing through user-space buffers. This eliminates 2-4 memory copies per message, reducing per-message latency from microseconds to nanoseconds at the OS level.

**Page Cache Utilization**: Kafka delegates caching to the OS page cache rather than maintaining its own heap-based cache. This doubles effective memory (no JVM overhead) and survives process restarts.

### 1.3 The Offset Ledger

Every message in Kafka has exactly three offset values:

1. **Log offset**: Immutable position within the partition (0, 1, 2, ...)
2. **Consumer offset**: Last offset successfully processed by a consumer group
3. **High-water mark**: Highest offset replicated to all in-sync replicas

The log offset is assigned by the broker on write. The consumer offset is committed by consumers. The high-water mark determines visibility: consumers cannot read beyond it, ensuring they never see unreplicated data that could vanish on broker failure.

### 1.4 Partitioning as a Physical Constraint

Partitions are Kafka's unit of parallelism. Key invariants:

- **Ordering guarantee**: Messages within a single partition are strictly ordered by offset
- **Parallelism boundary**: Each partition is consumed by exactly one consumer within a group
- **Independence**: Partitions have no cross-dependencies; partition 3's offset has no relationship to partition 7's offset

This creates a mathematical tradeoff: `throughput = partitions × per-partition-throughput`, but `max-parallelism = partition-count`. More partitions enable more parallel consumers, but each partition is a separate file, with associated file descriptor and memory overhead.

## 2. Core Architecture & Mechanics

### 2.1 Producer Architecture

#### 2.1.1 The Producer Buffer Chain

```text
Application Thread → Serializer → Partitioner → Accumulator → Sender Thread → Network
```

**Accumulator (RecordAccumulator)**: A memory buffer organized by topic-partition. Default size is 32 MB (`buffer.memory`). When full, `send()` blocks up to `max.block.ms` (default 60s).

**Batching**: Messages to the same partition accumulate into batches. Batch size controlled by:
- `batch.size` (default 16 KB): Target size per batch
- `linger.ms` (default 0): Artificial delay to collect more messages

A batch sends when it reaches `batch.size` OR `linger.ms` expires, whichever comes first.

**Sender Thread**: Single background thread that:
1. Drains ready batches from the accumulator
2. Groups batches by broker
3. Constructs `ProduceRequest` protocol messages
4. Manages TCP connections to brokers
5. Handles retries and error responses

#### 2.1.2 Message Production Protocol

```java
ProducerRecord<K, V> record = new ProducerRecord<>(
    "topic-name",      // topic
    partition,         // partition (optional)
    timestamp,         // timestamp (optional)
    key,               // key
    value,             // value
    headers            // headers (optional)
);

Future<RecordMetadata> future = producer.send(record);
```

**Partitioning Logic** (when partition not explicitly specified):

1. If key is null: Round-robin or sticky partition (Kafka 2.4+)
2. If key is present: `partition = hash(key) % partition-count`

The hash function is `murmur2` by default, ensuring deterministic routing: same key → same partition → preserved order for that key.

**Timestamp Assignment**:
- `CreateTime` (default): Producer assigns timestamp
- `LogAppendTime`: Broker overwrites with broker time on receipt

Timestamp affects log retention: segments are deleted based on message timestamps, not write time.

#### 2.1.3 Delivery Semantics

Controlled by `acks` configuration:

- **acks=0**: Fire-and-forget. No acknowledgment. Maximum throughput, zero durability.
- **acks=1**: Leader acknowledges after writing to its local log. Durability depends on replication lag. If leader fails before replication, message lost.
- **acks=all** (or `-1`): Leader waits for all in-sync replicas (ISR) to acknowledge. Maximum durability, higher latency.

**Idempotence** (`enable.idempotence=true`):
- Producer assigns sequence numbers to messages
- Broker deduplicates based on `(ProducerID, Sequence)`
- Prevents duplicates from network retries
- Requires `acks=all`, `max.in.flight.requests.per.connection ≤ 5`, `retries > 0`

**Transactions** (`transactional.id`):
- Atomic multi-partition writes
- Exactly-once semantics across partitions
- Read-committed isolation level for consumers
- Performance cost: ~3x latency increase due to 2PC protocol

### 2.2 Consumer Architecture

#### 2.2.1 Consumer Group Protocol

**Group Coordinator**: Special broker role managing consumer group membership and partition assignment. Each group is managed by one coordinator, determined by `hash(group.id) % 50`, mapping to the internal `__consumer_offsets` topic partition.

**Rebalance Triggers**:
1. Consumer joins group
2. Consumer leaves (clean shutdown or heartbeat timeout)
3. Topic metadata changes (partition added)

**Rebalance Protocol** (Eager Rebalancing, pre-2.4):

```text
1. Consumer sends JoinGroup request to coordinator
2. Coordinator waits for all consumers to join (within session.timeout.ms)
3. Coordinator selects leader consumer
4. Leader receives all consumer metadata, runs partition assignment strategy
5. Leader sends assignment back to coordinator
6. Coordinator distributes assignments via SyncGroup response
7. All consumers revoke old partitions, then consume new partitions
```

**Incremental Cooperative Rebalancing** (Kafka 2.4+):
- Only revokes partitions being reassigned
- Consumers retain stable partitions throughout rebalance
- Eliminates the "stop-the-world" pause

#### 2.2.2 Partition Assignment Strategies

**RangeAssignor** (default):
- Assigns consecutive partition ranges per topic
- Can cause imbalance across topics: Consumer 1 gets [0-2] on all topics

**RoundRobinAssignor**:
- Distributes partitions across consumers uniformly
- Better balance but breaks co-partitioning patterns

**StickyAssignor**:
- Maximizes retention of existing assignments during rebalance
- Minimizes partition movement

**CooperativeStickyAssignor** (Kafka 2.4+):
- Implements incremental cooperative rebalancing
- Only revokes partitions that must move

#### 2.2.3 Offset Management

**Offset Commit Storage**: `__consumer_offsets` internal topic (50 partitions, compacted). Each consumer group's offsets are stored as keyed messages: `(group, topic, partition) → offset`.

**Commit Strategies**:

**Auto-commit** (`enable.auto.commit=true`, `auto.commit.interval.ms=5000`):
```java
while (true) {
    ConsumerRecords<K, V> records = consumer.poll(Duration.ofMillis(100));
    // Process records
    // Offsets committed automatically in background every 5s
}
```
Risk: If consumer crashes after auto-commit but before processing, messages are lost (at-most-once).

**Manual commit**:
```java
while (true) {
    ConsumerRecords<K, V> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<K, V> record : records) {
        process(record);
    }
    consumer.commitSync(); // Blocks until coordinator confirms
}
```
`commitSync()` blocks, `commitAsync()` returns immediately with callback.

**Per-partition offset control**:
```java
Map<TopicPartition, OffsetAndMetadata> offsets = new HashMap<>();
for (ConsumerRecord<K, V> record : records) {
    process(record);
    TopicPartition tp = new TopicPartition(record.topic(), record.partition());
    offsets.put(tp, new OffsetAndMetadata(record.offset() + 1));
}
consumer.commitSync(offsets);
```

Critical: Commit `offset + 1` because the committed offset is the *next* offset to read, not the last processed.

#### 2.2.4 Consumer Polling Model

```java
KafkaConsumer<K, V> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Arrays.asList("topic1", "topic2"));

while (true) {
    ConsumerRecords<K, V> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<K, V> record : records) {
        System.out.printf("offset=%d, key=%s, value=%s%n",
            record.offset(), record.key(), record.value());
    }
}
```

**poll() Behavior**:
1. Sends heartbeat to coordinator (if needed)
2. Triggers rebalance participation (if needed)
3. Fetches data from broker
4. Returns up to `max.poll.records` (default 500)
5. Must be called within `max.poll.interval.ms` (default 5 minutes) or consumer is kicked

**Fetch Parameters**:
- `fetch.min.bytes` (default 1): Minimum data before broker responds
- `fetch.max.wait.ms` (default 500): Maximum wait if `fetch.min.bytes` not satisfied
- `max.partition.fetch.bytes` (default 1 MB): Maximum data per partition per fetch

### 2.3 Message Format & Serialization

#### 2.3.1 Record Batch Format (v2, Kafka 2.1+)

```text
RecordBatch:
  baseOffset: int64           # First offset in batch
  batchLength: int32          # Bytes in batch
  partitionLeaderEpoch: int32 # Epoch for fencing
  magic: int8                 # Version (2)
  crc: uint32                 # CRC of batch
  attributes: int16           # Compression, timestamps, transactional
  lastOffsetDelta: int32      # Offset delta of last record
  firstTimestamp: int64       # Base timestamp
  maxTimestamp: int64         # Max timestamp in batch
  producerId: int64           # For idempotence
  producerEpoch: int16        # For idempotence
  baseSequence: int32         # For idempotence
  records: [Record]           # Array of records

Record:
  length: varint
  attributes: int8
  timestampDelta: varint      # Delta from firstTimestamp
  offsetDelta: varint         # Delta from baseOffset
  keyLength: varint
  key: bytes
  valueLength: varint
  value: bytes
  headers: [Header]
```

**Compression**: Applied per-batch, not per-message. Supported codecs: none, gzip, snappy, lz4, zstd. Producer compresses before sending; broker stores compressed; consumer decompresses.

**Batching Efficiency**: A 1,000-message batch shares a single 61-byte overhead (vs. 61,000 bytes if sent individually). Within batch, records use variable-length encoding for offsets and timestamps.

#### 2.3.2 Serialization

**Built-in Serializers**:
- `StringSerializer`, `ByteArraySerializer`, `IntegerSerializer`, `LongSerializer`, `DoubleSerializer`

**Custom Serialization**:
```java
public class UserSerializer implements Serializer<User> {
    @Override
    public byte[] serialize(String topic, User user) {
        ByteBuffer buffer = ByteBuffer.allocate(8 + user.name.length());
        buffer.putInt(user.id);
        buffer.putInt(user.name.length());
        buffer.put(user.name.getBytes(StandardCharsets.UTF_8));
        return buffer.array();
    }
}
```

**Schema Registry Pattern** (Confluent):
- Centralized schema storage with versioning
- Producer embeds schema ID in message (4 bytes)
- Consumer fetches schema by ID, caches locally
- Supports Avro, Protobuf, JSON Schema
- Enforces compatibility rules (backward, forward, full)

## 3. High-Performance Implementation & Failure Modes

### 3.1 Producer Optimization

#### 3.1.1 Throughput Tuning

**Batch Size vs. Latency**:
```text
batch.size=16384          # 16 KB (default)
linger.ms=10              # Wait 10ms for batch to fill
```
Larger batches improve compression ratio and reduce per-message overhead. `linger.ms=0` sends immediately (latency-optimized). `linger.ms=100` waits longer (throughput-optimized).

**Compression**:
```text
compression.type=lz4      # Fast compression, good ratio
```
Benchmarks (1 KB messages, 1000-message batches):
- `none`: 0 µs CPU, 16 MB wire
- `lz4`: 15 µs CPU, 4 MB wire (4x reduction)
- `gzip`: 250 µs CPU, 3 MB wire (5.3x reduction)
- `zstd`: 80 µs CPU, 2.8 MB wire (5.7x reduction)

**Buffer Memory**:
```text
buffer.memory=67108864    # 64 MB (double default)
```
Larger buffer prevents blocking under load, but increases producer-side memory.

**In-Flight Requests**:
```text
max.in.flight.requests.per.connection=5
```
Default is 5. Higher values increase throughput but can reorder messages if retries occur (unless idempotence enabled).

#### 3.1.2 Partitioning Strategy

**Keyed Messages**:
```java
// Hash partitioning (default)
ProducerRecord<String, String> record = 
    new ProducerRecord<>("topic", "user-12345", event);
// All events for user-12345 → same partition → ordered
```

**Custom Partitioner**:
```java
public class PriorityPartitioner implements Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes,
                        Object value, byte[] valueBytes, Cluster cluster) {
        int partitions = cluster.partitionCountForTopic(topic);
        if (((String) value).contains("CRITICAL")) {
            return 0; // Route critical messages to partition 0
        }
        return Utils.toPositive(Utils.murmur2(keyBytes)) % (partitions - 1) + 1;
    }
}
```

**Sticky Partitioning** (Kafka 2.4+, keyless messages):
- Pre-2.4: Round-robin per message → poor batching
- Post-2.4: Stick to one partition until batch full → better batching

### 3.2 Consumer Optimization

#### 3.2.1 Parallelism Scaling

**Single Consumer Group**:
```text
Partitions: 12
Consumers: 4
Assignment: 3 partitions per consumer
```

**Multiple Consumer Groups**:
```text
Group A: Real-time processing (4 consumers)
Group B: Analytics (2 consumers)
Group C: Archival (1 consumer)
All groups read same data independently
```

**Over-Provisioning**:
```text
Partitions: 12
Consumers: 20
Active: 12 (one per partition)
Idle: 8 (on standby for rebalance)
```
Idle consumers react immediately to failures but waste resources.

#### 3.2.2 Fetch Optimization

**Throughput Configuration**:
```text
fetch.min.bytes=1048576        # 1 MB
fetch.max.wait.ms=500          # 500ms max wait
max.partition.fetch.bytes=10485760  # 10 MB
```
Consumer waits until 1 MB available OR 500 ms elapsed, then fetches up to 10 MB per partition.

**Latency Configuration**:
```text
fetch.min.bytes=1              # Return immediately
fetch.max.wait.ms=100          # Short timeout
```
Minimizes latency at cost of more frequent requests.

**Read Isolation**:
```text
isolation.level=read_committed  # Only see committed transactional messages
isolation.level=read_uncommitted  # See all messages (default)
```

#### 3.2.3 Processing Patterns

**At-Most-Once**:
```java
consumer.commitSync();        // Commit first
processRecords(records);      // Then process
```
If processing fails, messages are lost (already committed).

**At-Least-Once**:
```java
processRecords(records);      // Process first
consumer.commitSync();        // Then commit
```
If commit fails, messages reprocessed (duplicate processing).

**Exactly-Once** (with Kafka Streams or manual transactions):
```java
producer.initTransactions();
while (true) {
    ConsumerRecords<K, V> records = consumer.poll(Duration.ofMillis(100));
    producer.beginTransaction();
    for (ConsumerRecord<K, V> record : records) {
        ProducerRecord<K, V> output = transform(record);
        producer.send(output);
    }
    producer.sendOffsetsToTransaction(offsets, consumer.groupMetadata());
    producer.commitTransaction();
}
```
Input consumption and output production committed atomically.

### 3.3 Failure Modes & Recovery

#### 3.3.1 Producer Failures

**Network Timeout**:
```text
request.timeout.ms=30000      # 30s timeout for broker response
delivery.timeout.ms=120000    # 2min total time including retries
```
If broker doesn't respond within `request.timeout.ms`, request retried. After `delivery.timeout.ms`, message fails.

**Broker Failure**:
- Producer receives `NotLeaderForPartitionException`
- Refreshes metadata to find new leader
- Retries message to new leader
- Retry count: `retries=2147483647` (infinite by default)

**Buffer Full**:
```text
buffer.memory=33554432        # 32 MB
max.block.ms=60000            # Block 60s if buffer full
```
If buffer full, `send()` blocks up to `max.block.ms`, then throws `TimeoutException`.

**Message Too Large**:
```text
max.request.size=1048576      # 1 MB (default)
```
Broker has `message.max.bytes` (default 1 MB). If producer message exceeds, broker rejects with `RecordTooLargeException`.

#### 3.3.2 Consumer Failures

**Heartbeat Timeout**:
```text
session.timeout.ms=45000      # 45s (default 10s in older versions)
heartbeat.interval.ms=3000    # Heartbeat every 3s
```
If coordinator doesn't receive heartbeat for `session.timeout.ms`, consumer ejected, rebalance triggered.

**Poll Interval Timeout**:
```text
max.poll.interval.ms=300000   # 5 minutes
```
If `poll()` not called within 5 minutes, consumer assumed dead, rebalance triggered. Prevents slow processing from blocking group.

**Rebalance Storm**:
- Consumer joins → rebalance
- Rebalance takes 30s → consumers timeout → more rebalances
- Mitigation: Increase `max.poll.interval.ms`, reduce `max.poll.records`, optimize processing

**Offset Reset**:
```text
auto.offset.reset=earliest    # Start from beginning if no committed offset
auto.offset.reset=latest      # Skip to end (lose data)
auto.offset.reset=none        # Throw exception
```

**Duplicate Processing**:
- Consumer processes messages, crashes before committing
- After restart, reprocesses same messages
- Solution: Idempotent processing or transactional reads

#### 3.3.3 Data Loss Scenarios

**Unclean Leader Election**:
```text
unclean.leader.election.enable=false  # (default)
```
If true and all ISRs fail, out-of-sync replica becomes leader → data loss. If false, partition unavailable until ISR replica recovers.

**Producer acks=1**:
- Producer writes to leader
- Leader acknowledges, then crashes before replication
- New leader doesn't have message
- Solution: `acks=all`

**Consumer Auto-Commit + Crash**:
- Consumer polls, auto-commits offset 1000
- Crashes before processing messages 990-999
- Messages 990-999 lost
- Solution: Manual commit after processing

### 3.4 Monitoring & Observability

#### 3.4.1 Producer Metrics

**JMX Metrics**:
- `record-send-rate`: Messages/sec sent
- `record-error-rate`: Messages/sec failed
- `request-latency-avg`: Average request latency
- `batch-size-avg`: Average batch size
- `compression-rate-avg`: Compression ratio
- `buffer-available-bytes`: Available memory in buffer

**Logs**:
```text
WARN NetworkClient: [Producer] Got error produce response with correlation id X on topic-partition, retrying
```

#### 3.4.2 Consumer Metrics

**JMX Metrics**:
- `records-consumed-rate`: Messages/sec consumed
- `fetch-latency-avg`: Average fetch latency
- `records-lag`: Messages behind latest offset
- `records-lag-max`: Max lag across partitions
- `commit-latency-avg`: Average commit latency

**Consumer Lag Monitoring**:
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group my-group

GROUP     TOPIC     PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
my-group  events    0          1000            1500            500
my-group  events    1          2000            2000            0
```
Lag = LOG-END-OFFSET - CURRENT-OFFSET. Rising lag indicates consumer can't keep up.

#### 3.4.3 Broker Metrics

- `UnderReplicatedPartitions`: Partitions not fully replicated (ISR < replication factor)
- `OfflinePartitionsCount`: Partitions with no leader
- `ActiveControllerCount`: Should be 1 across cluster
- `BytesInPerSec`, `BytesOutPerSec`: Throughput
- `RequestHandlerAvgIdlePercent`: Broker thread pool saturation

## 4. Summary & Verification Matrix

### 4.1 Conceptual Summary

Kafka producers and consumers implement a **decoupled append-read model** with three core properties:

1. **Immutability**: Written messages never change; offsets are stable identifiers
2. **Independence**: Producers and consumers operate without runtime coordination
3. **Durability**: Configurable replication and acknowledgment trade throughput for fault tolerance

The producer pipeline (application → serializer → partitioner → accumulator → sender) batches and compresses messages, then uses a single-threaded network layer to interact with brokers. The consumer pipeline (poll → deserialize → process → commit) manages group membership, partition assignment, and offset tracking through a coordinator protocol.

Delivery semantics are configured, not intrinsic: `acks=0` gives at-most-once, `acks=all` with idempotence gives at-least-once, and transactions enable exactly-once.

### 4.2 Verification Matrix

| **Concept** | **Test Method** | **Expected Outcome** |
|-------------|----------------|---------------------|
| **Producer batching** | Send 10,000 messages with `linger.ms=100`, inspect `batch-size-avg` metric | Batch size >1, compression ratio visible if enabled |
| **Partition ordering** | Send keyed messages, consume, verify offsets monotonic per partition | Messages with same key in offset order |
| **Consumer group rebalance** | Start 2 consumers in group, kill one, observe partition reassignment | Surviving consumer takes all partitions within `session.timeout.ms` |
| **Offset commit** | Process messages, commit, restart consumer | Consumer resumes from committed offset, no reprocessing |
| **Idempotent producer** | Enable idempotence, send duplicate `ProducerRecord` | Broker deduplicates, single message in log |
| **Transaction** | Produce within transaction, abort | Messages not visible to `read_committed` consumers |
| **Consumer lag** | Produce 10,000 messages, consume slowly, check `records-lag` | Lag increases, decreases as consumer catches up |
| **Leader failure** | Produce with `acks=all`, kill leader broker | New leader elected from ISR, no data loss |
| **Unclean shutdown** | Consumer processes, kill -9 before commit | After restart, reprocesses same messages (at-least-once) |
| **Max message size** | Send message exceeding `max.request.size` | `RecordTooLargeException` thrown |

### 4.3 Design Decision Checklist

**Producer**:
- [ ] Serialization format chosen (Avro/Protobuf for schema evolution)
- [ ] Partitioning strategy defined (keyed for ordering, keyless for throughput)
- [ ] `acks` level selected (0 for speed, all for durability)
- [ ] Idempotence enabled if deduplication needed
- [ ] Batch size and linger tuned for throughput vs. latency tradeoff
- [ ] Compression codec selected (lz4 for speed, zstd for ratio)
- [ ] Retry and timeout configuration set
- [ ] Monitoring configured (send rate, error rate, latency)

**Consumer**:
- [ ] Consumer group or standalone subscription chosen
- [ ] Partition count >= expected consumer count for parallelism
- [ ] Offset commit strategy selected (auto, manual, per-partition)
- [ ] Delivery semantics understood (at-most, at-least, exactly-once)
- [ ] Processing idempotence designed if at-least-once
- [ ] Rebalance strategy chosen (eager, incremental cooperative)
- [ ] `max.poll.interval.ms` set for processing time
- [ ] Lag monitoring configured
- [ ] Error handling and retry logic implemented

**Operational**:
- [ ] Replication factor >= 3 for production
- [ ] `unclean.leader.election.enable=false` for durability
- [ ] `min.insync.replicas >= 2` with `acks=all`
- [ ] Partition count tuned for throughput and consumer parallelism
- [ ] Retention configured (time and size based)
- [ ] Monitoring alerts for lag, under-replicated partitions, broker health

This matrix serves as a pre-flight checklist before deploying Kafka producers and consumers to production.
