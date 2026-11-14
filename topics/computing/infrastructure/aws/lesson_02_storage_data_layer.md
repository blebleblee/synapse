# Lesson 2: Storage Abstractions and Data Persistence

## 1. First-Principles Intuition & Invariants

Storage is the most consequential design decision in any distributed system. Compute is fungible and stateless — a failed EC2 instance is replaced in seconds. Data is neither. When a byte is lost, no amount of horizontal scaling recovers it, and when a storage abstraction leaks its internal consistency model, entire classes of application bugs emerge that are nearly impossible to reproduce under normal load. Understanding AWS storage at the level of its physical invariants — not its marketing abstractions — is what separates architects who build systems that survive production from those who discover failure modes during an incident.

The fundamental tension in storage design is the CAP theorem as lived experience rather than academic exercise. Every storage primitive AWS offers makes an explicit trade between consistency, availability, and partition tolerance, and the system prompt these services expose — the API contract — often obscures which side of that trade they sit on. EBS delivers block-level storage with strong consistency within a single Availability Zone, trading geographic resilience for the synchronous write acknowledgment that databases demand. S3 delivers object storage with strong read-after-write consistency (a guarantee that was not always true — it arrived for new objects in 2020 and was extended to overwrites and deletes), trading the latency of a local disk for virtually unbounded horizontal scale. RDS abstracts an entire relational engine behind a managed control plane, hiding synchronous and asynchronous replication topologies that have precise, documented failure semantics you must internalize before you trust them with transactional data.

The physical intuition to anchor before diving into each service is this: a storage write is an acknowledgment chain. When your application calls `write()`, that syscall travels through a network stack, a storage protocol, one or more physical or virtual drives, and optionally a replication channel to a second host. The service's durability guarantee is defined by exactly how far along that chain the acknowledgment waits before returning to your caller. EBS Multi-Attach with `io2` volumes waits for the write to land on NVMe SSD on the host side before acknowledging. S3 Standard waits for the object to be written to multiple Availability Zones across redundant hardware before returning HTTP 200. An RDS synchronous replica (Multi-AZ) waits for the standby to confirm the write before the primary acknowledges the transaction. Each of these is a contract, and violating the assumptions of that contract — running a database on `gp2` volumes with burst credits exhausted, or relying on eventual consistency in S3 for a list operation that feeds a state machine — produces failures that are insidious precisely because they are intermittent.

The invariant that governs durable storage design across all AWS primitives is: **the acknowledgment depth must match the application's failure domain requirement**. If you can tolerate losing a write on instance failure, instance store is fastest. If you need AZ-level durability, EBS suffices. If you need region-level durability with eleven nines of object safety, S3's replication engine provides it. If you need synchronous transactional consistency across an AZ failure, RDS Multi-AZ is the minimum viable configuration. These are not performance optimizations; they are correctness invariants.

---

## 2. Core Architecture & Mechanics

### EBS: Block Storage from First Principles

Amazon EBS presents a virtual block device to an EC2 instance. From the operating system's perspective, it is indistinguishable from a local NVMe drive: the kernel interacts with it through the standard block layer, the filesystem sits atop it, and writes flow through the page cache and block I/O scheduler exactly as they would on bare metal. What actually happens beneath that abstraction is a network-attached storage protocol running over AWS's internal high-bandwidth, low-latency network fabric — a purpose-built Nitro subsystem that offloads EBS I/O entirely from the host CPU, eliminating the hypervisor tax that plagued earlier generation instances.

The EBS volume type determines the physical storage medium, the performance envelope, and the IOPS and throughput credits model. Understanding the differences is not a matter of reading a pricing table; it requires understanding the hardware characteristics behind each tier.

`gp3` is the current general-purpose SSD baseline. It delivers 3,000 IOPS and 125 MiB/s baseline throughput regardless of volume size, with the ability to provision IOPS and throughput independently up to 16,000 IOPS and 1,000 MiB/s. This decoupling from size is the critical architectural change from `gp2`, where IOPS scaled at 3 per GiB, meaning you would routinely over-provision storage capacity just to satisfy IOPS requirements. With `gp3`, you size for capacity and provision for performance separately, reducing cost substantially.

`io2 Block Express` targets latency-sensitive databases. It is backed by NVMe SSD with sub-millisecond latency, supports up to 256,000 IOPS per volume, and provides 99.999% durability — one additional nine over `gp3`. The practical implication of that durability number is that you can build an RDS instance with a single-AZ `io2` volume and still have more raw durability than a `gp3` Multi-AZ setup on a per-volume basis, though that reasoning ignores the AZ-level failure domain entirely.

`st1` and `sc1` are HDD-backed tiers optimized for throughput-intensive sequential workloads. They use credit-based burst throughput, making them appropriate for log archives, cold analytical datasets, or Kafka log segments where sequential scan dominates over random access. Random I/O on HDD is catastrophically expensive: a single random read forces a physical seek, costing approximately 5 milliseconds on average. For any workload with a random I/O component, HDD-backed volumes are functionally inappropriate.

The EBS snapshot mechanism is a cornerstone of disaster recovery architecture on AWS, and it operates on a copy-on-write model that has precise implications for backup cost and restore latency. When you create the first snapshot of a 1 TiB `gp3` volume, EBS does not immediately copy 1 TiB of data to S3. It initiates an incremental capture that reads dirty blocks from the volume's backing storage and writes them to S3 in an internal chunked format. Each subsequent snapshot is incremental: only blocks that have changed since the previous snapshot are written. The snapshot chain is maintained by EBS's internal metadata layer, and when you restore a volume from any snapshot in the chain, EBS reconstructs the full block map by walking the chain and materializing the latest version of each block.

This has a critical operational implication: restoring a volume from a snapshot does not produce a fully populated volume immediately. EBS lazy-populates the volume on first access — blocks that have not yet been pulled from the snapshot store incur a one-time penalty on first read, which looks like latency spikes in production if you restore a volume and immediately put it under database load. The mitigation is `fio` or `dd` pre-warming:

```bash
# Pre-warm a restored EBS volume before attaching to production workload
# Run this on the instance after attaching the restored volume at /dev/xvdf
sudo fio \
  --filename=/dev/xvdf \
  --rw=read \
  --bs=128k \
  --iodepth=32 \
  --ioengine=libaio \
  --direct=1 \
  --name=ebs_prewarm \
  --numjobs=4 \
  --runtime=0 \
  --size=100% \
  --output=/tmp/prewarm_results.json \
  --output-format=json
```

This forces every block on the volume to be fetched from the snapshot store before any application traffic touches it, eliminating the cold-read penalty entirely. For large volumes under tight recovery time objectives, run multiple `fio` jobs in parallel across different offset ranges.

The EBS encryption model uses AES-256 with keys managed by AWS KMS. Encryption is applied at the volume level, meaning every read and write is transparently encrypted and decrypted by the Nitro hypervisor — the EC2 instance and its operating system see plaintext data, but nothing crossing the network fabric between the instance and EBS storage is unencrypted. Snapshots of encrypted volumes are themselves encrypted with the same KMS key, and copying a snapshot to another region requires re-encrypting it with a key accessible in the target region.

```
EBS I/O Path on Nitro:
┌─────────────────────────────────────────────────────────────┐
│                      EC2 Instance                           │
│  Application                                                │
│      │  write(fd, buf, n)                                   │
│      ▼                                                      │
│  Linux VFS / Page Cache                                     │
│      │  block I/O request                                   │
│      ▼                                                      │
│  NVMe Driver (virtio-blk / NVMe over Nitro fabric)          │
└──────────────────────┬──────────────────────────────────────┘
                       │  NVMe Command over Nitro Network
┌──────────────────────▼──────────────────────────────────────┐
│                   Nitro Card (Host Hardware)                 │
│  AES-256 Encryption                                         │
│      │                                                      │
│      ▼                                                      │
│  EBS Storage Node (NVMe SSD Fleet)                          │
│      │  Write acknowledged after landing on SSD             │
│      ▼                                                      │
│  Acknowledgment → EC2 Instance                              │
└─────────────────────────────────────────────────────────────┘
```

The key insight in this diagram is that the acknowledgment fires after the write lands on the EBS storage node's NVMe SSD, not after any replication to a second node. EBS durability comes from the redundancy built into the SSD fleet itself — multiple copies of each block exist within the EBS storage layer — not from synchronous cross-AZ replication. For AZ-level fault tolerance, that must come from the application layer: RDS Multi-AZ, application-level replication, or EBS snapshot-based recovery.

### S3: Object Storage and Consistency Semantics

S3 is not a filesystem. This is not a platitude — it has mechanical consequences that must drive architecture decisions. S3 stores objects in a flat namespace under a bucket, addressed by key. There is no directory tree in the storage layer; the slash delimiter in key names is a client-side convention that the S3 console and many SDKs simulate as a hierarchy. The underlying storage is a distributed key-value store with keys hashed across a massive fleet of storage nodes partitioned by prefix.

The consistency model S3 offers today, following the December 2020 update, is strong read-after-write consistency for all operations: PUTs, DELETEs, and LIST operations. This means that immediately after a successful PUT to `s3://my-bucket/data/file.parquet`, any subsequent GET for that key will return the new object. Immediately after a DELETE, any subsequent GET will return 404. And LIST operations are consistent — if you PUT 1,000 objects and immediately list the bucket, all 1,000 will appear. This was not true before 2020. Prior to that, S3 offered eventual consistency for overwrites and deletes, and LIST operations were eventually consistent for new objects in some regions. Architectures built before 2020 often include consistency workarounds — DynamoDB-based conditional locking, retry loops on LIST, or external coordination — that are now unnecessary but harmless to leave in place.

The practical limit that architects must understand is that S3 strong consistency is scoped to a single key. The model provides no cross-key transactional atomicity. You cannot PUT two objects and guarantee that a concurrent reader sees both or neither. If you need atomic multi-object updates, you must implement a separate coordination mechanism — DynamoDB conditional writes for metadata, or S3's own object versioning combined with application-level two-phase commit patterns.

S3's partitioning model is critical for high-throughput workloads. Each unique prefix in a bucket is served by a partition, and each partition supports approximately 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD requests per second. If you write all your objects with keys that begin with a date prefix like `2024/01/15/`, all writes on a given day hit the same partition and you will throttle at scale. The mitigation is key prefix randomization: prepend a hash of the object's content or a random UUID prefix to distribute writes across partitions uniformly.

```bash
# Generate a randomly-prefixed S3 key for high-throughput ingestion
# Compute SHA-256 of the file, take the first 8 hex characters as prefix
FILE="sensor_reading_20240115_143022.json"
HASH_PREFIX=$(sha256sum "$FILE" | cut -c1-8)
S3_KEY="${HASH_PREFIX}/${FILE}"

aws s3api put-object \
  --bucket my-iot-data-bucket \
  --key "${S3_KEY}" \
  --body "${FILE}" \
  --storage-class STANDARD \
  --server-side-encryption aws:kms \
  --ssekms-key-id "arn:aws:kms:us-east-1:123456789012:key/mrk-abc123"

echo "Stored at: s3://my-iot-data-bucket/${S3_KEY}"
```

S3 Intelligent-Tiering automates cost optimization by monitoring access patterns and moving objects between access tiers: Frequent Access, Infrequent Access, Archive Instant Access, and optionally the Glacier tiers. The critical invariant is that objects in the Archive tiers have non-trivial restore latency: Glacier Instant Retrieval is milliseconds, Glacier Flexible Retrieval is minutes to hours, and Glacier Deep Archive is hours. Routing objects into the wrong tier for their access pattern produces either over-spending (keeping cold data in Standard) or operational failure (attempting real-time reads from Glacier Deep Archive).

Multipart upload is the mechanical feature that makes large object uploads reliable and performant. For objects larger than 100 MiB in practice (AWS's hard requirement is 5 GiB for single-part uploads, but the latency and reliability argument applies much sooner), multipart upload splits the object into parts of at least 5 MiB each, uploads them in parallel, and completes with a manifest that assembles the final object. The critical operational detail is that incomplete multipart uploads consume storage capacity and generate charges. A lifecycle rule to abort incomplete multipart uploads after a defined number of days is not optional for cost governance:

```bash
# Apply a lifecycle policy to abort incomplete multipart uploads after 7 days
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-iot-data-bucket \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "abort-incomplete-mpu",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "AbortIncompleteMultipartUpload": {
          "DaysAfterInitiation": 7
        }
      },
      {
        "ID": "transition-to-ia",
        "Status": "Enabled",
        "Filter": {"Prefix": ""},
        "Transitions": [
          {
            "Days": 30,
            "StorageClass": "STANDARD_IA"
          },
          {
            "Days": 90,
            "StorageClass": "GLACIER_IR"
          }
        ]
      }
    ]
  }'
```

### RDS: Relational Storage and Replication Topology

RDS abstracts a relational database engine — PostgreSQL, MySQL, Oracle, SQL Server, or MariaDB — behind a managed control plane that handles provisioning, patching, automated backups, and failover. The storage layer beneath an RDS instance is EBS, which means everything from the previous section applies: volume type selection, IOPS provisioning, and snapshot mechanics all govern RDS performance and recovery characteristics.

The replication topology in RDS Multi-AZ (not to be confused with Multi-AZ DB Cluster, which is a different product) is synchronous block-level replication. The primary instance writes to its EBS volume, and that write is synchronously replicated to a standby instance in a different Availability Zone using Amazon's internal replication protocol before the transaction is acknowledged to the application. This is not logical replication at the SQL level; it is physical block-level mirroring, which means the standby is an exact block-for-block copy of the primary at all times.

```
RDS Multi-AZ Synchronous Replication:

AZ-A                                    AZ-B
┌─────────────────────┐                ┌─────────────────────┐
│   RDS Primary       │                │   RDS Standby       │
│                     │                │                     │
│  Application Write  │                │                     │
│         │           │                │                     │
│         ▼           │                │                     │
│  InnoDB/PG Engine   │                │  Block-Level Mirror │
│         │           │                │         │           │
│         ▼           │                │         ▼           │
│  EBS Volume (gp3)   │◄──sync repl───►│  EBS Volume (gp3)  │
│                     │                │                     │
│  ACK to App only    │                │  Write confirmed    │
│  after standby      │                │  before primary     │
│  confirms write     │                │  ACKs               │
└─────────────────────┘                └─────────────────────┘
         │
         │  Automated Failover (60-120 seconds)
         │  DNS CNAME flips to standby endpoint
         ▼
  Application reconnects to same endpoint hostname
  Standby promoted to primary
  New standby provisioned in AZ-A
```

The failover timeline is the invariant that determines whether RDS Multi-AZ meets an application's recovery time objective. AWS guarantees failover completion in under two minutes in typical cases, though the actual observable impact on a connected application is determined by the JDBC/psql connection timeout settings, the DNS TTL on the RDS endpoint (which is 5 seconds), and whether the application implements proper connection retry logic. An application that opens a connection pool at startup and never reconnects will hang until TCP keepalive times out — which on a default Linux kernel configuration can take over ten minutes. Connection pool configuration is therefore a correctness requirement for Multi-AZ deployments, not a performance tuning detail.

RDS Read Replicas use asynchronous replication, which inverts the consistency model entirely. A Read Replica receives replication events from the primary after the primary has already acknowledged the write. The replica lag — the time between a write being committed on the primary and becoming visible on the replica — is measured in milliseconds under normal load but can grow to seconds or minutes under heavy write workloads, replica maintenance, or network congestion. Any application that reads from a Read Replica and depends on seeing its own writes will produce incorrect results intermittently. The correct architectural pattern for read replicas is eventual-read workloads: reporting queries, analytics, search indexing, or cache population — anything where reading slightly stale data is acceptable.

The backup mechanism in RDS combines automated daily snapshots with continuous transaction log archiving to S3. The retention window governs how far back you can perform a point-in-time restore. When you initiate a point-in-time restore, RDS provisions a new DB instance, restores the most recent automated snapshot that precedes your target time, and then replays transaction logs forward to the exact second you specified. The result is a new DB instance — not a modification of the existing one — with its own endpoint. This non-destructive restore model is critical: you cannot accidentally overwrite a running production database by initiating a point-in-time restore.

```bash
# Restore RDS PostgreSQL instance to a point in time
# Identify the available restore window first
aws rds describe-db-instances \
  --db-instance-identifier prod-postgres-primary \
  --query 'DBInstances[0].{
    LatestRestoreTime: LatestRestorableTime,
    Engine: Engine,
    EngineVersion: EngineVersion,
    DBInstanceClass: DBInstanceClass,
    MultiAZ: MultiAZ,
    StorageType: StorageType,
    AllocatedStorage: AllocatedStorage
  }' \
  --output table

# Perform point-in-time restore to a new instance
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier prod-postgres-primary \
  --target-db-instance-identifier prod-postgres-pitr-20240115t1430 \
  --restore-time "2024-01-15T14:30:00Z" \
  --db-instance-class db.r6g.2xlarge \
  --multi-az \
  --storage-type gp3 \
  --no-publicly-accessible \
  --db-subnet-group-name prod-db-subnet-group \
  --vpc-security-group-ids sg-0abc123def456 \
  --tags '[{"Key":"Purpose","Value":"PITR-Recovery"},{"Key":"SourceInstance","Value":"prod-postgres-primary"}]'

# Poll for instance availability
aws rds wait db-instance-available \
  --db-instance-identifier prod-postgres-pitr-20240115t1430

# Retrieve the new endpoint for validation
aws rds describe-db-instances \
  --db-instance-identifier prod-postgres-pitr-20240115t1430 \
  --query 'DBInstances[0].Endpoint.{Address:Address,Port:Port}' \
  --output table
```

### Object Storage vs. Block Storage: The Architectural Decision

The distinction between S3 and EBS is not primarily about durability or cost — it is about the access model and what that access model implies about the data's structure and usage pattern. Block storage exposes a raw byte-addressable device. The operating system mounts a filesystem on it, and applications read and write arbitrary byte ranges through POSIX file I/O. This random-access, byte-granular model is what databases require: PostgreSQL writes 8 KiB pages at specific offsets, maintains write-ahead logs as append-only streams, and performs fsync to guarantee durability. None of this is possible on S3, which is an object store: the atomic unit is the entire object, there is no partial write, and an overwrite replaces the entire object.

Object storage excels when data is written once and read many times in its entirety, when it must be accessed by many independent systems simultaneously without coordination, or when it must scale to virtually unbounded capacity without pre-provisioning. A data lake holding Parquet files, a static website's assets, a backup repository, or a machine learning training dataset are natural fits. The access pattern is: produce an object, store it, retrieve it whole. The EBS use case is: maintain a mutable data structure that evolves through fine-grained writes over time, with strict ordering and consistency guarantees. Databases, message queues backed by disk, and stateful streaming systems live here.

The practical error that emerges most frequently in production is using S3 as a database — writing small, frequently updated objects in a hot loop, depending on consistent list semantics for coordination, or attempting to implement record-level updates through whole-object replacement. Each PUT to S3 carries meaningful per-request latency (single-digit milliseconds minimum) compared to a local disk write (hundreds of microseconds on NVMe). At 10,000 record updates per second, the difference between EBS and S3 is the difference between operational software and a system that burns request quota and falls behind indefinitely.

---

## 3. High-Performance Optimization & Failure Modes

### EBS Performance Pathology and Mitigation

The most common EBS performance failure in production is IOPS exhaustion on `gp2` volumes that relied on the burst credit model. `gp2` volumes smaller than 1,000 GiB operate at a baseline of 3 IOPS per GiB and burst up to 3,000 IOPS by consuming burst credits accumulated at the baseline rate. A 100 GiB `gp2` volume has a 300 IOPS baseline; a database workload that sustains 2,000 IOPS will drain its burst credit bucket within minutes and throttle to 300 IOPS, producing a latency cliff that looks like a sudden application slowdown with no obvious cause in application-level metrics. The CloudWatch metric `BurstBalance` exposes the remaining credit percentage, but it is rarely alarmed on. The correct mitigation is migrating to `gp3` and explicitly provisioning IOPS independent of volume size.

Measuring actual EBS performance requires distinguishing between volume-level limits and instance-level EBS bandwidth limits. Every EC2 instance type has a maximum EBS bandwidth and IOPS ceiling that is shared across all attached volumes. An `r6g.large` instance supports up to 10,000 IOPS and 4,750 MiB/s of EBS throughput regardless of how many `io2` volumes you attach or how many IOPS are provisioned on them. If your database's EBS volume is provisioned for 32,000 IOPS but the instance type only supports 16,000, the provisioned IOPS are irrelevant.

```bash
# Benchmark EBS volume performance with fio
# Measures random read latency, random write IOPS, and sequential read throughput
# Run on a dedicated test instance with the EBS volume mounted at /dev/nvme1n1

# Random 4K read latency (simulates database random page access)
sudo fio \
  --name=rand_read_latency \
  --filename=/dev/nvme1n1 \
  --rw=randread \
  --bs=4k \
  --iodepth=1 \
  --ioengine=libaio \
  --direct=1 \
  --numjobs=1 \
  --runtime=60 \
  --time_based \
  --group_reporting \
  --output-format=json \
  --output=/tmp/rand_read_lat.json

# Random 4K write IOPS (simulates OLTP write workload)
sudo fio \
  --name=rand_write_iops \
  --filename=/dev/nvme1n1 \
  --rw=randwrite \
  --bs=4k \
  --iodepth=64 \
  --ioengine=libaio \
  --direct=1 \
  --numjobs=4 \
  --runtime=60 \
  --time_based \
  --group_reporting \
  --output-format=json \
  --output=/tmp/rand_write_iops.json

# Sequential 128K read throughput (simulates analytics scan / backup)
sudo fio \
  --name=seq_read_throughput \
  --filename=/dev/nvme1n1 \
  --rw=read \
  --bs=128k \
  --iodepth=32 \
  --ioengine=libaio \
  --direct=1 \
  --numjobs=4 \
  --runtime=60 \
  --time_based \
  --group_reporting \
  --output-format=json \
  --output=/tmp/seq_read_tput.json

# Parse latency results (p99 latency in microseconds)
python3 -c "
import json, sys
for fname, label in [
    ('/tmp/rand_read_lat.json', 'Random Read'),
    ('/tmp/rand_write_iops.json', 'Random Write'),
    ('/tmp/seq_read_tput.json', 'Sequential Read')
]:
    with open(fname) as f:
        d = json.load(f)
    job = d['jobs'][0]
    rw = job.get('read') or job.get('write')
    if rw:
        print(f'{label}: IOPS={rw[\"iops\"]:.0f}, '
              f'BW={rw[\"bw_bytes\"]/1024/1024:.1f} MiB/s, '
              f'p50={rw[\"lat_ns\"][\"percentile\"][\"50.000000\"]/1000:.0f}us, '
              f'p99={rw[\"lat_ns\"][\"percentile\"][\"99.000000\"]/1000:.0f}us, '
              f'p999={rw[\"lat_ns\"][\"percentile\"][\"99.900000\"]/1000:.0f}us')
"
```

Volume-level EBS CloudWatch metrics to monitor in production include `VolumeReadOps`, `VolumeWriteOps`, `VolumeQueueLength`, `VolumeThroughput`, and `VolumeIdleTime`. The queue length metric is the most important leading indicator of saturation: a sustained queue depth greater than 1 per provisioned 1,000 IOPS indicates that the volume's service rate cannot absorb the incoming I/O, and writes are accumulating in the kernel's block I/O scheduler. This produces increased tail latency before it produces throughput reduction, which is why database p99 latency often spikes before average latency shows any change.

### S3 Throttling, Consistency Boundaries, and Failure Patterns

S3 returns HTTP 503 `SlowDown` responses when request rates exceed per-prefix partition limits. The AWS SDK's built-in retry logic handles these with exponential backoff by default, but naive application code that constructs its own S3 client without configuring retry behavior will surface these as transient errors during high-throughput ingestion. The correct configuration for the AWS SDK v2 for Java, Python, Go, or any other supported language is to enable adaptive retry mode, which uses a token bucket to self-regulate request rates based on observed 503 responses:

```python
import boto3
from botocore.config import Config

# Configure S3 client with adaptive retry and connection pooling
# for high-throughput multi-threaded workloads
s3_config = Config(
    region_name='us-east-1',
    retries={
        'mode': 'adaptive',       # adjusts retry rate based on 503 feedback
        'max_attempts': 10        # maximum total attempts including initial
    },
    max_pool_connections=50,       # match to thread pool size
    tcp_keepalive=True,
    connect_timeout=5,
    read_timeout=60
)

s3_client = boto3.client('s3', config=s3_config)

# S3 Transfer Manager for concurrent multipart upload
# handles part sizing, concurrency, and retry automatically
from boto3.s3.transfer import TransferConfig

transfer_config = TransferConfig(
    multipart_threshold=1024 * 1024 * 64,    # 64 MiB: use multipart above this
    multipart_chunksize=1024 * 1024 * 32,    # 32 MiB parts
    max_concurrency=20,                        # parallel part uploads
    use_threads=True
)

def upload_large_object(local_path: str, bucket: str, key: str) -> None:
    s3_client.upload_file(
        Filename=local_path,
        Bucket=bucket,
        Key=key,
        Config=transfer_config,
        ExtraArgs={
            'ServerSideEncryption': 'aws:kms',
            'StorageClass': 'STANDARD'
        }
    )
```

The S3 Event Notification system is a common integration point for data pipelines, and it has a failure mode that is frequently overlooked: S3 event delivery is at-least-once. If S3 delivers a notification to SQS or SNS and the downstream consumer fails to process it, the message is retried — but if the consumer processes it and then S3 internally retries delivery due to a transient failure, the event will be delivered a second time. Any consumer of S3 event notifications must implement idempotent processing: checking whether the object has already been processed before performing the downstream action.

A subtler consistency boundary involves S3 and ETL pipelines that use the prefix listing pattern to discover new files for processing. Because S3 LIST is now strongly consistent, listing a prefix immediately after a batch of writes will return all written objects. However, in distributed ingestion pipelines where multiple producers write to the same prefix concurrently, there is no atomic "snapshot" of the prefix at a given moment. A consumer that lists the prefix and then processes the listed keys may miss objects written between the LIST call and the start of processing, or may process objects out of order relative to their creation sequence. The robust pattern is to stage objects into a landing prefix, process from an SQS queue populated by S3 notifications rather than prefix listing, and move objects to a processed prefix atomically using S3's `CopyObject` API followed by `DeleteObject`.

### RDS Failover Invariants and Recovery Anti-Patterns

The two-minute Multi-AZ failover SLA is a property of the control plane decision and DNS propagation, not of database recovery. After the primary fails, the standby must complete its role promotion sequence: mounting the replicated EBS volume as writable, starting the database engine, running crash recovery if the primary failed mid-write, and accepting connections. The database engine's crash recovery time is proportional to the size of the redo log and the number of dirty pages in the buffer pool at the time of failure. For a heavily loaded PostgreSQL or MySQL instance, this can add tens of seconds to the failover timeline.

The DNS TTL on the RDS endpoint CNAME is 5 seconds, but clients with aggressive DNS caching — particularly Java applications using the default `java.security.security` DNS caching behavior, which caches positive results for 30 seconds by default — will continue connecting to the failed primary's IP address until the cache expires. The mitigation on JVM-based stacks is to set `networkaddress.cache.ttl=1` in the Java security properties, forcing DNS re-resolution on every connection attempt.

Connection pool exhaustion is the most common secondary failure during an RDS Multi-AZ event. When the primary fails, all existing connections drop. The connection pool attempts to reconnect all idle connections simultaneously, producing a connection storm against the newly promoted standby. If the max connections parameter on the RDS instance is sized tightly — which is common since `max_connections` in PostgreSQL defaults to a function of available memory — this reconnection storm will exceed the limit, causing connection refused errors that look like the database is still down. The correct mitigation is a combination of pgBouncer or RDS Proxy as a connection pooler, which absorbs the reconnection storm against a local pool rather than the database, and application-level exponential backoff with jitter on connection acquisition failures.

```bash
# Monitor RDS Multi-AZ failover in real time using CloudWatch Events / EventBridge
# Create an EventBridge rule to capture RDS failover events

aws events put-rule \
  --name rds-failover-monitor \
  --event-pattern '{
    "source": ["aws.rds"],
    "detail-type": ["RDS DB Instance Event"],
    "detail": {
      "EventCategories": ["failover", "availability", "recovery"]
    }
  }' \
  --state ENABLED \
  --description "Capture RDS failover and availability events"

# Target the rule to an SNS topic for alerting
aws events put-targets \
  --rule rds-failover-monitor \
  --targets '[
    {
      "Id": "rds-failover-sns-target",
      "Arn": "arn:aws:sns:us-east-1:123456789012:rds-ops-alerts",
      "InputTransformer": {
        "InputPathsMap": {
          "dbinstance": "$.detail.SourceIdentifier",
          "message": "$.detail.Message",
          "time": "$.time"
        },
        "InputTemplate": "\"RDS Event on <dbinstance> at <time>: <message>\""
      }
    }
  ]'

# Check current Multi-AZ status and pending maintenance
aws rds describe-db-instances \
  --db-instance-identifier prod-postgres-primary \
  --query 'DBInstances[0].{
    Status: DBInstanceStatus,
    MultiAZ: MultiAZ,
    SecondaryAZ: SecondaryAvailabilityZone,
    PendingModified: PendingModifiedValues,
    MaintenanceWindow: PreferredMaintenanceWindow,
    BackupWindow: PreferredBackupWindow,
    BackupRetentionDays: BackupRetentionPeriod,
    LatestRestore: LatestRestorableTime
  }' \
  --output table
```

The read replica promotion path — promoting a Read Replica to a standalone primary during a regional disaster — carries a critical data loss risk that many teams underestimate. Because Read Replicas use asynchronous replication, there is no guarantee that the replica has applied all transactions from the primary at the moment of failure. The `ReplicaLag` CloudWatch metric measures the lag in seconds, but it is an average measurement; under heavy write bursts, the actual unapplied transaction count can be significant. After promotion, the new primary will have applied only the transactions it had received before the failure. Any transactions acknowledged by the original primary but not yet replicated to the replica are permanently lost. This is an intrinsic property of asynchronous replication — it is not a bug in RDS, and it cannot be mitigated by infrastructure changes alone. Applications that cannot tolerate this loss must use synchronous replication (Multi-AZ) or design their transaction processing to tolerate the possibility of replaying the last N seconds of work after a failover.

The practical takeaway from examining these three storage primitives together is that AWS storage is not a uniform abstraction — it is a spectrum of consistency, latency, and durability trade-offs, each optimized for a distinct class of workload. EBS gives you the semantics of a local disk with network-attached durability and AZ-scoped failure isolation. S3 gives you infinitely scalable object storage with strong per-key consistency but no cross-key atomicity. RDS gives you managed relational storage with configurable consistency windows determined by replication topology. The engineer who understands these trade-offs precisely — not at the level of "S3 is for objects, EBS is for databases" but at the level of acknowledgment depth, partition topology, and failure domain semantics — is the engineer who can design systems that are correct under the full distribution of real-world failure modes rather than only under the happy path.
