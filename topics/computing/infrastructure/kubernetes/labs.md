# Operational Verification Labs: Kubernetes Architecture & Etcd Diagnostics

## Objective & Environment Setup

This operational lab provides hands-on diagnostic verification of the Kubernetes control plane's foundational consensus layer. We dissect etcd's Raft protocol implementation, inspect its MVCC storage engine, profile leader election mechanics under partition scenarios, and analyze the apiserver's watch stream coherence guarantees. The exercises require direct access to control plane nodes, etcd cluster members, and the ability to inject controlled network faults.

The etcd cluster underpins all Kubernetes state. Every resource—Pods, Services, ConfigMaps—exists as a versioned key-value pair in etcd's persistent B+tree. The Raft consensus algorithm ensures that writes propagate through a quorum (floor(N/2) + 1 nodes) before acknowledging success. The apiserver acts as the sole gateway to etcd, translating RESTful HTTP requests into etcd transactions and streaming Watch events derived from etcd's monotonically increasing revision counter. Understanding this transactional boundary is critical for diagnosing split-brain conditions, stale reads, and cascading control plane failures.

### Required Diagnostic Utilities

Verify that standard Kubernetes administration and diagnostic tools are available on your control plane:

```bash
kubectl version --client
etcdctl version
```

For environments using kubeadm, the etcd static pod manifests reside in `/etc/kubernetes/manifests/etcd.yaml`. The etcd data directory defaults to `/var/lib/etcd`. Verify etcd process binding and TLS certificate paths:

```bash
ps aux | grep etcd | grep -v grep
```

Expected output shows `--listen-client-urls`, `--advertise-client-urls`, and TLS certificate paths (`--cert-file`, `--key-file`, `--trusted-ca-file`). The peer communication ports (default 2380) and client API ports (default 2379) must be reachable across all control plane nodes.

Configure environment variables for etcdctl CLI access. If using TLS-secured etcd (the production standard), export certificate paths and API version:

```bash
export ETCDCTL_API=3
export ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
```

Verify cluster health and member list to confirm quorum connectivity:

```bash
etcdctl endpoint health --cluster
etcdctl member list -w table
```

The output must show all members in the `started` state with reachable peer URLs. Any member showing `false` for `ISLEARNER` is a full voting member contributing to quorum calculations.

For kernel-level observation of etcd's I/O patterns and scheduling behavior, ensure the `perf` subsystem and BPF Type Format (BTF) debug symbols are available:

```bash
ls /sys/kernel/btf/vmlinux
sudo sysctl kernel.perf_event_paranoid=-1
```

This configuration permits unprivileged users to attach BPF probes and record perf events without root privileges in subsequent exercises.

### Network Topology and Control Plane Architecture

In a highly available Kubernetes cluster, the control plane typically spans three or five nodes to tolerate (N-1)/2 simultaneous failures. Each node runs four critical components: etcd as the consensus storage engine, kube-apiserver as the RESTful API gateway and watch aggregator, kube-controller-manager as the closed-loop reconciliation engine, and kube-scheduler as the Pod placement decision engine.

The kube-apiserver maintains persistent HTTP/2 connections to etcd for all CRUD operations and establishes long-lived gRPC Watch streams to propagate resource change events. Controller-manager and scheduler instances continuously watch apiserver endpoints, racing to acquire leadership via etcd lease-based elections. Only the leader instance performs write operations; followers remain in hot-standby watch-only mode.

Verify apiserver to etcd connectivity by inspecting active TCP connections:

```bash
sudo ss -tanp | grep :2379
```

Expected output shows multiple `ESTAB` connections from the apiserver process (identifiable by `/usr/local/bin/kube-apiserver` or the static pod container ID) to the local etcd endpoint. The connection count scales with the number of active Watch streams and periodic health checks.

### Storage Backend and MVCC Semantics

Etcd implements MVCC through a monotonically increasing 64-bit revision counter. Every write transaction increments the global revision and attaches that revision to all modified keys. Reads can specify a historical revision to retrieve point-in-time snapshots. This time-travel capability powers Kubernetes resource version semantics: the `metadata.resourceVersion` field in every API object corresponds directly to the etcd revision at which that object was last modified.

Inspect the current etcd database revision and key count:

```bash
etcdctl endpoint status -w table
```

The `REVISION` column displays the current global revision watermark. The `DB SIZE` column shows the on-disk database file size in bytes. As etcd accumulates historical revisions, the database grows indefinitely unless compaction is performed. The `DB SIZE IN USE` metric indicates post-compaction active data size.

Etcd stores all keys in a single B+tree namespace. Kubernetes organizes its keyspace with hierarchical prefixes: `/registry/pods/<namespace>/<name>` for Pods, `/registry/services/specs/<namespace>/<name>` for Services, and `/registry/configmaps/<namespace>/<name>` for ConfigMaps. This prefixing scheme enables efficient range queries and watch filtering at the etcd layer.

Enumerate all root-level prefixes to understand keyspace organization:

```bash
etcdctl get / --prefix --keys-only | cut -d'/' -f1-3 | sort -u | head -20
```

This command lists unique three-level path prefixes, revealing how the apiserver partitions different resource types into logical namespaces.

## Exercise 1: Live State & Internal Subsystem Inspection

### Task 1.1: Dissecting Raft Leader Election and Heartbeat Cadence

Etcd's Raft implementation elects a single leader responsible for appending entries to the replicated log. Followers transition to candidate state if they fail to receive heartbeats within the election timeout window (default 1000ms). The leader sends periodic heartbeats (default interval 100ms) to suppress elections and maintain authority. This heartbeat mechanism is visible in etcd's peer-to-peer traffic and internal metrics.

Identify the current Raft leader by querying member status:

```bash
etcdctl endpoint status -w table
```

The `IS LEADER` column marks the leader node with `true`. The `RAFT TERM` reflects the current election term number, which increments each time a new leader is elected. In a stable cluster, the term remains constant indefinitely.

Attach a network packet capture to observe Raft heartbeat traffic between etcd peers. On the leader node, capture outbound traffic to peer port 2380:

```bash
sudo tcpdump -i any -nn 'tcp port 2380' -w /tmp/etcd-raft.pcap &
TCPDUMP_PID=$!
sleep 30
sudo kill $TCPDUMP_PID
```

Analyze the captured traffic to measure heartbeat interval:

```bash
tcpdump -r /tmp/etcd-raft.pcap -nn 'tcp[tcpflags] & tcp-push != 0' | \
  awk '{print $1}' | \
  awk 'NR>1 {print $1 - prev} {prev=$1}'
```

This pipeline extracts TCP PSH flag timestamps and computes inter-packet deltas. The resulting intervals should cluster around 100ms, confirming the default heartbeat cadence. Deviations indicate network latency spikes or CPU scheduling delays that could destabilize the cluster.

Inspect etcd's internal Raft metrics via its metrics endpoint. The etcd process exposes Prometheus-compatible metrics on port 2381 by default (configurable via `--listen-metrics-urls`):

```bash
curl -sk https://127.0.0.1:2381/metrics | grep etcd_server_leader_changes_seen_total
```

The `etcd_server_leader_changes_seen_total` counter tracks the number of leader transitions since process startup. In a healthy cluster, this value should remain at 1 after initial election. Incrementing values indicate cluster instability, often caused by network partitions, overloaded nodes, or misconfigured election timeouts.

Extract the current Raft applied index and committed index:

```bash
curl -sk https://127.0.0.1:2381/metrics | grep -E 'etcd_server_has_leader|etcd_debugging_mvcc_db_total_size_in_bytes|etcd_server_proposals_committed_total|etcd_server_proposals_applied_total'
```

The `etcd_server_has_leader` gauge reports 1 when the node sees an active leader, 0 otherwise. The `etcd_server_proposals_committed_total` and `etcd_server_proposals_applied_total` counters track the Raft log's committed and applied watermarks. The applied index lags slightly behind committed as the state machine processes entries asynchronously. Large divergences between these counters suggest apply-side bottlenecks, often caused by slow disk I/O or snapshot restoration overhead.

To observe leader election in real time, force a leader failure by terminating the etcd process on the leader node. On the identified leader, locate the etcd container and send SIGTERM:

```bash
sudo crictl ps | grep etcd
sudo crictl stop <container-id>
```

Immediately query the remaining nodes to observe term increment and leader transition:

```bash
watch -n 0.5 'etcdctl endpoint status -w table --endpoints=https://<follower-1>:2379,https://<follower-2>:2379'
```

Within the election timeout window (1000ms default), one follower should increment the term and claim leadership. The `IS LEADER` column will flip to `true` on the new leader. Restart the stopped etcd container to restore full cluster capacity:

```bash
sudo crictl start <container-id>
```

The restarted node rejoins as a follower and replicates missing log entries from the new leader. Monitor the `RAFT INDEX` column to confirm the node catches up to the cluster's committed index.

### Task 1.2: MVCC Storage Engine and Compaction Mechanics

Etcd's storage layer consists of two B+trees: the key index and the revision index. The key index maps user-facing keys to their latest revision. The revision index maps revision numbers to the actual key-value data and metadata. This dual-index structure enables efficient point lookups, range scans, and historical queries.

Query a specific Kubernetes resource and observe its revision encoding. Create a test ConfigMap:

```bash
kubectl create configmap lab-test --from-literal=key=value -n default
```

Retrieve the ConfigMap and extract its resource version:

```bash
kubectl get configmap lab-test -n default -o json | jq -r '.metadata.resourceVersion'
```

The resource version is a base64-encoded protobuf representation of the etcd revision. Decode it to extract the numeric revision:

```bash
RESOURCE_VERSION=$(kubectl get configmap lab-test -n default -o json | jq -r '.metadata.resourceVersion')
echo $RESOURCE_VERSION
```

The numeric resource version corresponds directly to the etcd revision at which the ConfigMap was written. Query etcd directly to retrieve the raw key-value pair:

```bash
etcdctl get /registry/configmaps/default/lab-test --print-value-only | hexdump -C | head -20
```

The output shows the protobuf-serialized ConfigMap object. The etcd key embeds the namespace and name, enabling prefix-based queries for all ConfigMaps in a namespace or across all namespaces.

Etcd accumulates historical revisions indefinitely, causing the database to grow without bound. Compaction discards revisions older than a specified watermark, reclaiming storage. The apiserver triggers periodic compaction via the `--etcd-compaction-interval` flag (default 5 minutes) and the `--etcd-compaction-mode` setting (periodic or revision-based).

Check the current database size and revision count:

```bash
etcdctl endpoint status -w table
```

Manually trigger compaction to discard all revisions older than the current revision minus 1000:

```bash
CURRENT_REV=$(etcdctl endpoint status --write-out=json | jq -r '.[0].Status.header.revision')
COMPACT_REV=$((CURRENT_REV - 1000))
etcdctl compact $COMPACT_REV
```

The compact operation returns immediately, but the physical storage reclamation occurs asynchronously. Force defragmentation to reclaim disk space:

```bash
etcdctl defrag
```

Defragmentation rewrites the database file, eliminating fragmentation and reclaiming space occupied by tombstoned keys. This operation blocks all reads and writes to the target member, so execute it during maintenance windows or one node at a time in multi-member clusters.

Verify the database size decreased after defragmentation:

```bash
etcdctl endpoint status -w table
```

The `DB SIZE` column should reflect the reduced on-disk footprint. The `DB SIZE IN USE` column shows the active data size, which remains unchanged since compaction only affects historical revisions.

### Task 1.3: Watch Stream Coherence and Resourceversion Semantics

The apiserver maintains long-lived Watch streams that propagate etcd change events to clients. Each Watch request specifies a starting resource version; the apiserver replays all events from that revision forward. This replay mechanism enables clients to build consistent local caches without polling.

Create a Watch stream for all ConfigMaps in the default namespace:

```bash
kubectl get configmaps -n default --watch -o json &
WATCH_PID=$!
```

In a separate terminal, create, update, and delete a ConfigMap:

```bash
kubectl create configmap watch-test --from-literal=iteration=1 -n default
kubectl patch configmap watch-test -n default --type=merge -p '{"data":{"iteration":"2"}}'
kubectl delete configmap watch-test -n default
```

Observe the Watch stream output. Each event contains a `type` field (ADDED, MODIFIED, DELETED) and an `object` field with the full resource state at that revision. The `metadata.resourceVersion` field increments with each modification, reflecting the underlying etcd revision.

Terminate the Watch process:

```bash
kill $WATCH_PID
```

Watch streams can experience transient failures due to apiserver restarts, network interruptions, or etcd leader elections. Clients must handle `410 Gone` errors by restarting the Watch from the last observed resource version. Kubernetes client libraries implement automatic reconnection with exponential backoff.

Simulate a Watch resumption scenario by creating a ConfigMap, extracting its resource version, and starting a new Watch from that revision:

```bash
kubectl create configmap resume-test --from-literal=state=initial -n default
INITIAL_RV=$(kubectl get configmap resume-test -n default -o json | jq -r '.metadata.resourceVersion')
kubectl patch configmap resume-test -n default --type=merge -p '{"data":{"state":"updated"}}'
kubectl get configmaps -n default --watch --resource-version=$INITIAL_RV -o json
```

The Watch stream starts at the specified resource version and replays all subsequent events, including the MODIFIED event from the patch operation. This replay behavior ensures clients observe a consistent event sequence even after reconnection.

The apiserver caches recent events in a fixed-size circular buffer (default 5 minutes of history). Watch requests with resource versions older than the cache window fail with `410 Gone`, forcing clients to perform a full LIST to rebuild their cache. Monitor the apiserver's watch cache metrics to detect cache eviction pressure:

```bash
kubectl get --raw /metrics | grep apiserver_watch_cache
```

The `apiserver_watch_cache_events_dispatched_total` counter tracks the total number of events delivered to Watch clients. The `apiserver_watch_cache_events_received_total` counter tracks events ingested from etcd. Divergence between these counters indicates client processing delays or network congestion.

### Task 1.4: Lease-Based Leader Election and Controller Coordination

Kubernetes controllers use etcd leases to coordinate leadership. The kube-controller-manager and kube-scheduler deploy multiple replicas for high availability, but only the leader instance actively reconciles resources. Followers watch the leader's lease; when it expires, they compete to acquire a new lease and claim leadership.

Inspect the active controller-manager leader by querying its lease object:

```bash
kubectl get lease kube-controller-manager -n kube-system -o yaml
```

The `spec.holderIdentity` field identifies the current leader by hostname. The `spec.leaseDurationSeconds` field specifies the lease validity period (default 15 seconds). The `spec.renewTime` field shows the last successful renewal timestamp. If the leader fails to renew within the lease duration, followers detect expiration and initiate a new election.

Observe leader election in real time by terminating the controller-manager leader pod:

```bash
kubectl delete pod -n kube-system -l component=kube-controller-manager,tier=control-plane --field-selector spec.nodeName=<leader-node>
```

Query the lease object repeatedly to observe the leadership transition:

```bash
watch -n 1 'kubectl get lease kube-controller-manager -n kube-system -o jsonpath="{.spec.holderIdentity}"'
```

Within seconds, a follower instance acquires the lease and updates the `holderIdentity` field with its own hostname. The transition is atomic and serialized through etcd's compare-and-swap primitive, preventing split-brain scenarios where multiple instances believe they are the leader.

Inspect the etcd lease backing the controller-manager's leadership token:

```bash
etcdctl lease list
```

The output lists all active leases by their hexadecimal lease IDs. Identify the controller-manager lease by correlating the lease TTL with the `leaseDurationSeconds` value from the Kubernetes Lease object. Retrieve detailed lease information:

```bash
etcdctl lease timetolive <lease-id> --keys
```

The `keys` field lists all etcd keys attached to the lease. When the lease expires, etcd automatically deletes these keys, triggering Watch events that notify followers of the leadership vacancy.

## Exercise 2: Fault Injection and Recovery Pathways

### Task 2.1: Network Partition and Split-Brain Prevention

Etcd's Raft implementation prevents split-brain by requiring a majority quorum for all write operations. In a three-node cluster, any two nodes form a quorum; in a five-node cluster, any three nodes suffice. Partitioning the cluster into minority and majority segments isolates the minority, rendering it unable to process writes while the majority continues operating.

Simulate a network partition by dropping packets between the leader and a follower. Identify the leader and a follower node:

```bash
etcdctl endpoint status -w table
```

On the follower node, install an iptables rule to drop all traffic from the leader:

```bash
sudo iptables -A INPUT -s <leader-ip> -j DROP
sudo iptables -A OUTPUT -d <leader-ip> -j DROP
```

The follower loses connectivity to the leader but remains reachable from the third node. Monitor the cluster state on all three nodes:

```bash
watch -n 1 'etcdctl endpoint status -w table'
```

The partitioned follower remains in follower state, unable to communicate with the leader. The leader and the third node maintain quorum and continue processing writes. Verify write availability by updating a test key:

```bash
etcdctl put /test-partition "write-during-partition"
```

The write succeeds on the majority partition (leader and third node). Query the key from the isolated follower:

```bash
etcdctl get /test-partition
```

The isolated node returns stale data or no data, depending on when the partition occurred. Reads from minority members are not guaranteed to reflect committed writes.

Heal the partition by removing the iptables rules:

```bash
sudo iptables -D INPUT -s <leader-ip> -j DROP
sudo iptables -D OUTPUT -d <leader-ip> -j DROP
```

The isolated node reconnects to the leader and replicates missing log entries. Verify consistency by querying the test key from all nodes:

```bash
etcdctl get /test-partition --endpoints=https://<node-1>:2379,https://<node-2>:2379,https://<node-3>:2379
```

All nodes return the same value, confirming eventual consistency after partition healing.

### Task 2.2: Leader Failure and Automatic Failover Latency

Leader failure triggers an automatic election. The election duration depends on the election timeout, network round-trip time, and the number of candidate nodes competing for leadership. Measure failover latency by inducing leader failure and tracking the time until a new leader is elected.

On the leader node, identify the etcd process and send SIGKILL to simulate a hard crash:

```bash
sudo pkill -9 etcd
```

Immediately start a timer and query the cluster state until a new leader is elected:

```bash
START=$(date +%s%3N)
while true; do
  LEADER=$(etcdctl endpoint status -w json --endpoints=https://<node-1>:2379,https://<node-2>:2379 2>/dev/null | jq -r '.[] | select(.Status.leader != 0) | .Status.leader')
  if [ -n "$LEADER" ]; then
    END=$(date +%s%3N)
    echo "Failover duration: $((END - START)) ms"
    break
  fi
  sleep 0.1
done
```

The failover duration should be slightly greater than the election timeout (1000ms default). The first follower to time out transitions to candidate, increments the term, and requests votes from other followers. Upon receiving votes from a majority, the candidate claims leadership and begins sending heartbeats.

Restart the failed etcd node and observe its rejoin process:

```bash
sudo systemctl start etcd
```

The restarted node queries peers for the current term and leader, appends itself to the cluster as a follower, and replicates missing log entries. Monitor the `RAFT INDEX` to confirm the node catches up:

```bash
watch -n 1 'etcdctl endpoint status -w table'
```

### Task 2.3: Disk Latency and Write Amplification Under Load

Etcd's performance is I/O-bound. Every write operation appends to the WAL (write-ahead log) and updates the B+tree index. Slow disks induce write latency, increasing the likelihood of election timeouts and cluster instability. Measure etcd's write latency and throughput under synthetic load.

Install the etcd benchmark tool:

```bash
git clone https://github.com/etcd-io/etcd.git
cd etcd/tools/benchmark
go build -o etcd-benchmark
```

Run a write-heavy workload with 10 concurrent clients, each issuing 1000 PUT operations:

```bash
./etcd-benchmark put --total=10000 --clients=10 --key-size=8 --val-size=256 \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

The benchmark reports average latency, throughput (requests per second), and latency percentiles. Healthy etcd clusters on SSD-backed storage should achieve single-digit millisecond p99 latencies and thousands of writes per second. Elevated p99 latencies (> 50ms) indicate disk contention, underpowered hardware, or competing I/O from other processes.

Profile etcd's write path using strace to observe syscall-level behavior:

```bash
sudo strace -p $(pgrep etcd) -e trace=write,fsync,fdatasync -c
```

Allow the trace to run for 30 seconds, then examine the summary. The `fsync` and `fdatasync` calls dominate the latency budget, as etcd must flush WAL entries to disk before acknowledging writes. The ratio of `write` to `fsync` calls indicates write batching efficiency. High `fsync` counts relative to `write` calls suggest small, unbatched writes, which amplify I/O load.

Monitor etcd's internal WAL fsync latency metrics:

```bash
curl -sk https://127.0.0.1:2381/metrics | grep etcd_disk_wal_fsync_duration_seconds
```

The `etcd_disk_wal_fsync_duration_seconds` histogram tracks fsync latency distribution. The p99 bucket should remain below 10ms on SSD storage. Values exceeding 50ms indicate disk saturation or degraded hardware. The `etcd_disk_backend_commit_duration_seconds` histogram tracks B+tree commit latency, which should remain below 25ms under normal load.

### Task 2.4: Snapshot and Restore Operations

Etcd periodically snapshots its state to compact the WAL and enable fast node recovery. Snapshots capture the entire keyspace at a specific revision, enabling point-in-time backups and disaster recovery. The snapshot interval is controlled by the `--snapshot-count` flag (default 100,000 applied log entries).

Manually trigger a snapshot to capture the current cluster state:

```bash
etcdctl snapshot save /tmp/etcd-snapshot.db
etcdctl snapshot status /tmp/etcd-snapshot.db -w table
```

The snapshot file contains the complete B+tree and metadata at the captured revision. The `HASH` field provides a checksum for integrity verification. The `REVISION` field shows the revision watermark captured in the snapshot.

Simulate a disaster recovery scenario by destroying the etcd data directory and restoring from the snapshot. On a test node (never production), stop etcd and remove the data directory:

```bash
sudo systemctl stop etcd
sudo rm -rf /var/lib/etcd
```

Restore the data directory from the snapshot:

```bash
sudo etcdctl snapshot restore /tmp/etcd-snapshot.db \
  --name=etcd-test \
  --initial-cluster=etcd-test=https://127.0.0.1:2380 \
  --initial-advertise-peer-urls=https://127.0.0.1:2380 \
  --data-dir=/var/lib/etcd
```

The restore operation recreates the data directory and initializes a new single-member cluster from the snapshot. For multi-member clusters, restore the snapshot on all nodes simultaneously, specifying the full initial cluster topology. Restart etcd and verify the restored revision matches the snapshot:

```bash
sudo systemctl start etcd
etcdctl endpoint status -w table
```

The `REVISION` column should match the snapshot's revision. Query a known key to confirm data integrity:

```bash
etcdctl get /registry/configmaps/default/lab-test
```

## Exercise 3: Apiserver Watch Mechanics and Event Propagation

### Task 3.1: Watch Cache Architecture and Bookmark Events

The apiserver maintains an in-memory watch cache for each resource type, storing recent events in a circular buffer. When a client establishes a Watch, the apiserver serves events from this cache rather than querying etcd repeatedly. The cache size is controlled by the `--watch-cache-sizes` flag, which specifies per-resource buffer sizes (default 100 objects per resource type).

Query the apiserver's watch cache metrics to inspect cache utilization:

```bash
kubectl get --raw /metrics | grep apiserver_watch_cache
```

The `apiserver_watch_cache_capacity_increase_total` counter tracks cache resizing events. Frequent resizing indicates undersized caches, leading to cache misses and increased etcd query load. The `apiserver_watch_cache_events_dispatched_total` counter shows the cumulative number of events delivered to Watch clients, segmented by resource type.

Watch streams include periodic bookmark events that update the client's resource version without transmitting object data. Bookmarks enable clients to checkpoint progress and resume from a recent revision even if no objects have changed. Observe bookmark events by establishing a Watch on an infrequently modified resource:

```bash
kubectl get pods -n kube-system --watch -o json | jq 'select(.type == "BOOKMARK")'
```

Bookmark events contain a `metadata.resourceVersion` field reflecting the current apiserver cache revision. The apiserver sends bookmarks every 60 seconds (configurable via `--watch-bookmark-interval`). Clients that store bookmark resource versions can resume watches without replaying the full event history.

### Task 3.2: Event Ordering and Causality Guarantees

Etcd guarantees linearizable reads and writes: every operation appears to execute atomically at a single point in time, and all clients observe operations in the same order. The apiserver preserves this ordering for Watch events, ensuring that clients observe a causally consistent event stream.

Verify event ordering by creating a sequence of dependent resources and observing the Watch stream order. Create a ConfigMap that references a Secret:

```bash
kubectl create secret generic secret-test --from-literal=password=secret123 -n default
kubectl create configmap configmap-test --from-literal=secret-ref=secret-test -n default
```

Establish a Watch on both resource types simultaneously:

```bash
kubectl get secrets,configmaps -n default --watch -o json | jq '{type: .type, kind: .object.kind, name: .object.metadata.name, rv: .object.metadata.resourceVersion}'
```

Delete both resources and observe the event stream order:

```bash
kubectl delete secret secret-test -n default
kubectl delete configmap configmap-test -n default
```

The DELETED event for the Secret appears before the DELETED event for the ConfigMap, reflecting the order in which the deletions were committed to etcd. The apiserver cannot reorder events without violating causality, as downstream controllers depend on this ordering to maintain referential integrity.

### Task 3.3: Watch Stream Reconnection and Backoff Strategies

Network interruptions, apiserver restarts, and etcd leader elections can disrupt Watch streams. Kubernetes client libraries implement automatic reconnection with exponential backoff to avoid overwhelming the apiserver during outages. Observe this behavior by forcibly terminating an apiserver instance and monitoring client reconnection attempts.

Establish a Watch stream using a raw HTTP client to control reconnection logic:

```bash
kubectl proxy --port=8001 &
PROXY_PID=$!
curl -sN http://localhost:8001/api/v1/namespaces/default/configmaps?watch=true &
WATCH_PID=$!
```

Identify the apiserver pod handling the Watch connection and delete it:

```bash
kubectl delete pod -n kube-system -l component=kube-apiserver --field-selector spec.nodeName=$(kubectl get pod -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].spec.nodeName}' | head -1)
```

The Watch stream terminates with a connection reset or HTTP 410 Gone error. The client must reconnect using the last observed resource version. Manually reconnect by extracting the resource version from the last event before disconnection:

```bash
LAST_RV=$(kubectl get configmaps -n default -o json | jq -r '.metadata.resourceVersion')
curl -sN "http://localhost:8001/api/v1/namespaces/default/configmaps?watch=true&resourceVersion=$LAST_RV"
```

Production clients implement exponential backoff with jitter to prevent thundering herd effects when many clients reconnect simultaneously. The Kubernetes client-go library defaults to a minimum backoff of 1 second, doubling on each failure up to a maximum of 300 seconds.

Terminate the background processes:

```bash
kill $WATCH_PID $PROXY_PID
```

## Exercise 4: Advanced Diagnostics and Performance Tuning

### Task 4.1: BPF-Based Latency Profiling of Etcd Write Path

Etcd's write latency is dominated by three operations: WAL append, B+tree update, and network replication to followers. Use BPF tracing to profile these stages and identify bottlenecks.

Install bpftrace and verify kernel BTF availability:

```bash
sudo bpftrace --info | grep BTF
```

Trace etcd's write latency by attaching to the `pwrite64` syscall and measuring time spent in disk I/O:

```bash
sudo bpftrace -e '
kprobe:vfs_write /comm == "etcd"/ {
  @start[tid] = nsecs;
}
kretprobe:vfs_write /comm == "etcd"/ {
  @latency_us = hist((nsecs - @start[tid]) / 1000);
  delete(@start[tid]);
}
interval:s:30 {
  print(@latency_us);
  clear(@latency_us);
  exit();
}
'
```

The histogram output shows the distribution of write latencies in microseconds. Most writes should complete within 100-500μs on SSD storage. Tail latencies exceeding 10ms indicate disk contention, inadequate I/O scheduler configuration, or hardware degradation.

Profile etcd's CPU utilization to identify hot code paths:

```bash
sudo perf record -F 99 -p $(pgrep etcd) -g -- sleep 30
sudo perf report --stdio
```

The report lists functions sorted by CPU time. The Raft message handling loop (`rafthttp.Raft.Process`) and B+tree traversal (`mvcc.index.Get`) typically dominate CPU usage. Elevated time in lock acquisition functions (`sync.Mutex.Lock`) suggests lock contention, often caused by excessive concurrent client requests.

### Task 4.2: Etcd Alarm System and Quota Management

Etcd enforces a configurable database size quota (default 2GB) to prevent uncontrolled disk usage. When the database exceeds the quota, etcd enters an alarm state and rejects all write operations, returning `etcdserver: mvcc: database space exceeded` errors. The apiserver cannot create or update resources while the alarm is active, causing cascading control plane failures.

Simulate a quota violation by artificially lowering the quota and filling the database:

```bash
etcdctl member list -w json | jq -r '.[0].ID' | xargs -I {} etcdctl member update {} --quota-backend-bytes=10485760
```

This command sets the quota to 10MB. Write large values to exhaust the quota:

```bash
for i in {1..1000}; do
  etcdctl put /test/quota-$i "$(head -c 10000 /dev/urandom | base64)"
done
```

Query the alarm state to confirm the quota violation:

```bash
etcdctl alarm list
```

The output shows an active `NOSPACE` alarm. Verify that write operations fail:

```bash
etcdctl put /test/verify "should-fail"
```

The operation returns an error: `etcdserver: mvcc: database space exceeded`. Read operations continue to function, but the cluster is effectively read-only.

Resolve the alarm by compacting old revisions and defragmenting the database:

```bash
CURRENT_REV=$(etcdctl endpoint status --write-out=json | jq -r '.[0].Status.header.revision')
etcdctl compact $CURRENT_REV
etcdctl defrag
```

Disarm the alarm to restore write capability:

```bash
etcdctl alarm disarm
```

Verify that writes succeed:

```bash
etcdctl put /test/verify "should-succeed"
```

Restore the original quota:

```bash
etcdctl member list -w json | jq -r '.[0].ID' | xargs -I {} etcdctl member update {} --quota-backend-bytes=2147483648
```

### Task 4.3: Distributed Tracing of Apiserver-to-Etcd Request Flow

The apiserver's interaction with etcd involves multiple layers: HTTP request parsing, authentication, authorization, admission control, and finally the etcd transaction. Distributed tracing captures end-to-end latency across these stages, identifying which layer contributes the most delay.

Enable the apiserver's OpenTelemetry tracing by modifying the static pod manifest at `/etc/kubernetes/manifests/kube-apiserver.yaml`. Add the tracing flags:

```yaml
spec:
  containers:
  - command:
    - kube-apiserver
    - --tracing-config-file=/etc/kubernetes/tracing-config.yaml
    volumeMounts:
    - name: tracing-config
      mountPath: /etc/kubernetes/tracing-config.yaml
      readOnly: true
  volumes:
  - name: tracing-config
    hostPath:
      path: /etc/kubernetes/tracing-config.yaml
      type: File
```

Create the tracing configuration file at `/etc/kubernetes/tracing-config.yaml`:

```yaml
apiVersion: apiserver.config.k8s.io/v1alpha1
kind: TracingConfiguration
endpoint: localhost:4317
samplingRatePerMillion: 1000000
```

Deploy a local OpenTelemetry collector to receive traces. The collector exports traces to Jaeger for visualization:

```bash
docker run -d --name otel-collector \
  -p 4317:4317 \
  -p 16686:16686 \
  otel/opentelemetry-collector-contrib:latest
```

Restart the apiserver to apply the tracing configuration. The kubelet detects the modified manifest and recreates the static pod. Perform a kubectl operation to generate traces:

```bash
kubectl create configmap trace-test --from-literal=key=value -n default
```

Access the Jaeger UI at `http://localhost:16686` and search for traces with the `kube-apiserver` service name. The trace spans show request latency breakdown: authentication (< 1ms), authorization (< 5ms), admission control (varies by webhook count), and etcd transaction (5-50ms). High etcd transaction latency indicates slow disk I/O, network delays to etcd members, or etcd cluster overload.

### Task 4.4: Tuning Election Timeout and Heartbeat Interval

Etcd's default election timeout (1000ms) and heartbeat interval (100ms) balance responsiveness and stability. In networks with high latency or jitter, these defaults may cause spurious elections. Conversely, low-latency environments can reduce these values to achieve faster failover.

Measure network round-trip time between control plane nodes:

```bash
ping -c 100 <peer-node-ip> | tail -1 | awk -F'/' '{print $5}'
```

The average RTT should be well under 10ms for a stable cluster. If RTT exceeds 50ms, increase the election timeout and heartbeat interval to compensate.

Modify the etcd static pod manifest at `/etc/kubernetes/manifests/etcd.yaml` to adjust timing parameters:

```yaml
spec:
  containers:
  - command:
    - etcd
    - --heartbeat-interval=200
    - --election-timeout=2000
```

The heartbeat interval must be less than the election timeout, typically 1/10th to avoid spurious elections. Restart etcd by deleting the pod and allowing the kubelet to recreate it:

```bash
sudo crictl stopp $(sudo crictl pods --name=etcd -q)
```

Verify the updated parameters by inspecting etcd logs:

```bash
sudo journalctl -u kubelet | grep "heartbeat-interval\|election-timeout"
```

Monitor the cluster for stability. If the `etcd_server_leader_changes_seen_total` counter remains at 1 after the change, the new parameters are appropriate. Incrementing counters indicate the values are still too aggressive for the network conditions.
