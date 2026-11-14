# Operational Verification Labs: Event Driven

## Objective & Environment Setup

Event-driven architectures represent a fundamental departure from synchronous request-response models, replacing blocking call chains with asynchronous message flows mediated by brokers, queues, and publish-subscribe fabrics. In cloud-native infrastructure, these patterns manifest through Kubernetes Jobs triggered by cron schedules, NATS JetStream persisting ordered event logs, Kafka partitions distributing load across consumer groups, and Knative Eventing routing CloudEvents through broker meshes. The operational challenge lies not in the API abstractions but in verifying the invisible state machines: message ordering guarantees, at-least-once delivery semantics, backpressure propagation through congested channels, and partition rebalancing storms that cascade across consumer lag metrics.

This lab sequence instruments event-driven systems at the Linux kernel boundary and Kubernetes control plane layer. You will trace message flows from userspace socket writes through TCP send queues into container network namespaces, correlate application-level event timestamps with kernel scheduler preemption points, measure broker partition leadership election latencies through etcd Raft quorum commits, and inject network partitions to validate consumer group rebalance protocols. The exercises synthesize tcpdump packet capture with eBPF kprobe instrumentation, Kubernetes event streams with cgroup resource accounting, and application metrics with kernel perf counters to build a coherent mental model of distributed event propagation under failure.

Your diagnostic environment requires a Kubernetes cluster with at least three worker nodes to demonstrate distributed event broker topologies. Install the core toolchain: `kubectl` for control plane interrogation, `iproute2` for network namespace traversal and traffic shaping, `tcpdump` for packet-level wire inspection, `perf` for kernel profiling, and `strace` for system call tracing. Deploy a representative event-driven stack: a NATS JetStream cluster with three replicas for fault-tolerant stream storage, a Kafka StatefulSet with three brokers and ZooKeeper coordination, or a Knative Eventing installation with in-memory and persistent broker backends. Ensure your container runtime exposes `crictl` for direct container inspection and that the kernel provides eBPF support with BTF debugging information. Each exercise builds on the previous instrumentation layer, starting with static configuration validation, progressing through dynamic runtime profiling, and culminating in destructive fault injection with automated recovery verification.

## Exercise 1: Live State & Internal Subsystem Inspection

Event-driven systems hide their complexity behind message broker abstractions, but operational reliability depends on understanding the kernel-level resource allocation and network stack behavior beneath those abstractions. Begin by deploying a three-replica NATS JetStream cluster into your Kubernetes environment using Helm, which installs a StatefulSet with persistent volume claims for stream storage and headless services for peer discovery. The NATS server process binds to TCP port 4222 for client connections and 6222 for inter-server clustering, establishing a full mesh topology where each replica maintains persistent TCP connections to every other replica for Raft consensus and stream replication.

```bash
helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm install nats nats/nats --set cluster.enabled=true --set cluster.replicas=3 \
  --set nats.jetstream.enabled=true --set nats.jetstream.fileStorage.size=10Gi
```

Once the StatefulSet rolls out, inspect the pod network topology to understand how container networking enables the service mesh. Kubernetes assigns each pod a virtual ethernet pair connecting the pod's network namespace to the node's root namespace through a CNI bridge. Retrieve the three NATS pod names and select one for detailed inspection, then exec into that pod to examine its network interface configuration.

```bash
kubectl get pods -l app.kubernetes.io/name=nats -o wide
POD_NAME=$(kubectl get pod -l app.kubernetes.io/name=nats -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD_NAME -- ip addr show
```

Inside the pod, the `eth0` interface carries an RFC1918 private address from the cluster's pod CIDR range, with a point-to-point link to the node's bridge. Note the interface MTU, typically 1500 bytes for standard Ethernet or 9000 bytes if jumbo frames are enabled. The kernel routing table reveals a default gateway pointing to the CNI bridge, which performs SNAT translation for pod-to-external traffic and maintains conntrack state for bidirectional flow association. Exit the pod and inspect the corresponding virtual ethernet peer on the node by correlating the pod's `eth0` interface index with the host's `veth` devices.

```bash
kubectl get pod $POD_NAME -o jsonpath='{.status.hostIP}'
NODE_IP=$(kubectl get pod $POD_NAME -o jsonpath='{.status.hostIP}')
ssh $NODE_IP "ip link show | grep -A1 veth"
```

The `veth` interface on the host side plugs into the CNI bridge, typically named `cni0` or `cbr0` depending on the network plugin. Inspect the bridge forwarding database to see learned MAC addresses from active pods, and examine the bridge's iptables FORWARD chain rules that enforce Kubernetes NetworkPolicies through conntrack matching and packet marking. This layer-2 topology determines message latency for intra-node pod-to-pod communication, while inter-node traffic traverses the underlay network through VXLAN or IP-in-IP encapsulation.

Return to the NATS pod and establish a direct TCP connection test to another replica using the stateful pod's predictable DNS name. NATS StatefulSets generate FQDNs in the form `nats-0.nats.default.svc.cluster.local`, allowing each server to resolve its peers during bootstrap. From inside `nats-0`, use `telnet` or `nc` to verify TCP reachability to `nats-1` on the clustering port.

```bash
kubectl exec -it nats-0 -- nc -zv nats-1.nats.default.svc.cluster.local 6222
```

Successful connection proves that the headless service's DNS records and the CNI's packet forwarding are operational. Now instrument the TCP connection state to measure actual message propagation latency. The `ss` utility from `iproute2` exposes kernel socket buffer statistics, including send and receive queue depths, congestion window sizes, round-trip time measurements, and retransmission counters. Execute `ss` with extended TCP information flags to capture a snapshot of the NATS server's established connections.

```bash
kubectl exec -it nats-0 -- ss -tinp | grep :6222
```

The output shows each connection's state (ESTAB for established), local and remote socket addresses, send and receive queue byte counts, and the associated process PID. The send queue (`Send-Q`) should remain near zero under steady state, indicating that the application is not overproducing data faster than the network can transmit. Non-zero receive queue (`Recv-Q`) values signal that the NATS server process has not read all available data from the kernel socket buffer, potentially indicating CPU saturation or event loop blocking. The `timer` field reveals active TCP timers: `on` with a value means a retransmission timer is armed due to unacknowledged segments, while `keepalive` indicates idle connection probing.

To correlate these TCP metrics with application-level message throughput, publish a test stream and consume it while monitoring socket buffer dynamics. Install the NATS CLI client inside the pod or from your local machine with cluster access, then create a JetStream stream named `test` with file storage and a single replica for simplicity.

```bash
kubectl exec -it nats-0 -- nats stream add test --subjects="events.>" \
  --storage=file --replicas=1 --retention=limits --max-msgs=100000
```

Generate a sustained message load using the `nats` CLI benchmark utility, publishing 1000 messages per second with 512-byte payloads to the `events.lab` subject. In a separate terminal, maintain a continuous `ss` watch loop to observe send queue accumulation and RTT variance under load.

```bash
kubectl exec -it nats-0 -- nats bench events.lab --pub 5 --msgs=10000 --size=512
# In parallel:
kubectl exec -it nats-0 -- watch -n 1 'ss -tinp | grep :4222'
```

Under healthy conditions, send queues remain below the socket buffer maximum (typically 16 KB to 256 KB), and RTT values stabilize around the physical network's baseline latency. If send queues grow unbounded, the publisher is overwhelming the broker's ingestion rate, and the kernel's TCP congestion control algorithm (CUBIC or BBR) will throttle transmission by reducing the congestion window. If RTT spikes occur, correlate them with kernel network stack drops using `ip -s link` to check the pod's `eth0` interface statistics.

```bash
kubectl exec -it nats-0 -- ip -s link show eth0
```

The `RX errors`, `TX dropped`, and `overrun` counters reveal packet loss at the network interface level. Non-zero `overrun` values indicate that the kernel's network receive queue (the softirq backlog) is saturating, dropping packets before the NATS process can consume them. This pathology typically appears when interrupt rate exceeds the CPU's packet processing capacity, and can be mitigated by tuning the kernel's `net.core.netdev_max_backlog` sysctl or enabling hardware offload features like GRO (Generic Receive Offload) and GSO (Generic Segmentation Offload).

Transition from network layer inspection to application-level event stream verification. NATS JetStream maintains stream metadata in a Raft-replicated key-value store, accessible through the `nats stream info` command. Query the `test` stream's state to observe message count, byte count, first and last sequence numbers, and the current consumer lag.

```bash
kubectl exec -it nats-0 -- nats stream info test
```

The `First Sequence` and `Last Sequence` fields define the stream's available message window, while `Deleted` counts messages that have been explicitly removed or expired due to retention policies. The `Num Acks Pending` metric under consumer groups indicates messages that have been delivered but not yet acknowledged, a critical signal for detecting stalled consumers or message processing failures. Create a durable consumer on the stream and let it lag intentionally by consuming slowly, then observe how JetStream tracks the consumer's position.

```bash
kubectl exec -it nats-0 -- nats consumer add test slow --filter="" \
  --ack=explicit --max-deliver=3 --deliver=all
kubectl exec -it nats-0 -- nats consumer next test slow --no-ack --count=10
# Wait, then check info:
kubectl exec -it nats-0 -- nats consumer info test slow
```

The `Num Ack Pending` counter increments as messages are delivered without acknowledgment, and `Num Redeliveries` tracks how many times JetStream has re-sent unacknowledged messages when the `max-deliver` threshold is approached. This state machine is critical for at-least-once delivery semantics: if a consumer crashes after receiving a message but before acknowledging it, JetStream will redeliver the message to another instance in the consumer group after the acknowledgment timeout expires.

To observe how JetStream persists this state across process restarts, force a pod restart by deleting it and allow Kubernetes to reschedule it on a potentially different node. The StatefulSet controller ensures that the new pod reattaches to the same persistent volume, preserving stream and consumer state across the restart boundary.

```bash
kubectl delete pod nats-0
kubectl wait --for=condition=ready pod/nats-0 --timeout=120s
kubectl exec -it nats-0 -- nats stream info test
```

The stream's sequence numbers and consumer positions remain intact, demonstrating that file-backed streams survive pod failures as long as the underlying persistent volume is available. This durability contract breaks down under node failures or volume detachment, where Kubernetes must reschedule the pod to a different node and reattach the volume through the CSI driver. To verify recovery time, measure the interval between pod deletion and readiness probe success, capturing the volume attach latency and NATS server startup time.

Extend this inspection methodology to Kafka by deploying a three-broker cluster with ZooKeeper coordination. Kafka's partition leadership election and consumer group rebalancing generate observable Kubernetes events and etcd state transitions. Install Kafka using the Strimzi operator, which manages StatefulSets, ConfigMaps, and Services through custom resources.

```bash
kubectl create namespace kafka
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
kubectl apply -f - <<EOF
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: lab-cluster
  namespace: kafka
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
    storage:
      type: persistent-claim
      size: 10Gi
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 5Gi
EOF
```

The operator creates `lab-cluster-kafka-0`, `lab-cluster-kafka-1`, and `lab-cluster-kafka-2` pods, each running a Kafka broker JVM process. Wait for all pods to reach ready state, then inspect the ZooKeeper ensemble state to verify quorum formation. ZooKeeper uses a majority quorum protocol where a cluster of three nodes tolerates one failure, requiring at least two nodes for write availability.

```bash
kubectl wait --for=condition=ready pod/lab-cluster-kafka-0 -n kafka --timeout=300s
kubectl exec -n kafka lab-cluster-zookeeper-0 -- bin/zkCli.sh get /controller
```

The `/controller` znode stores the broker ID of the current Kafka controller, the broker responsible for partition leadership election and cluster metadata propagation. Note the `cZxid` transaction ID, which increments whenever the controller is re-elected due to failures or session expirations. Kafka clients and brokers watch this znode for changes, triggering metadata refresh when leadership transitions occur.

Create a test topic with three partitions and a replication factor of three, ensuring that each partition has replicas on all three brokers. This topology maximizes fault tolerance: each partition remains available as long as at least one replica is alive, and Kafka's ISR (in-sync replica) protocol ensures that only replicas that have caught up to the leader's log offset participate in acknowledgment decisions.

```bash
kubectl exec -n kafka lab-cluster-kafka-0 -- bin/kafka-topics.sh \
  --create --topic events --partitions 3 --replication-factor 3 \
  --bootstrap-server localhost:9092
kubectl exec -n kafka lab-cluster-kafka-0 -- bin/kafka-topics.sh \
  --describe --topic events --bootstrap-server localhost:9092
```

The `--describe` output lists each partition's leader broker ID, replica set, and ISR set. Under steady state, the ISR should match the replica set, indicating that all replicas are synchronizing within the `replica.lag.time.max.ms` window. If a broker falls behind due to network latency or disk I/O saturation, Kafka removes it from the ISR to prevent blocking producer acknowledgments waiting for slow replicas. Produce a batch of messages to the topic and monitor partition leadership stability.

```bash
kubectl exec -n kafka lab-cluster-kafka-0 -- bin/kafka-producer-perf-test.sh \
  --topic events --num-records 10000 --record-size 512 --throughput 1000 \
  --producer-props bootstrap.servers=localhost:9092 acks=all
```

While the producer runs, open a second terminal and stream Kubernetes events related to the Kafka cluster, filtering for leadership election and replica lag warnings emitted by the Strimzi operator's metrics aggregation.

```bash
kubectl get events -n kafka --watch | grep -E 'leader|replica|lag'
```

Healthy operations produce no events; warnings about under-replicated partitions or ISR shrinkage signal operational anomalies. Correlate these high-level events with broker-level metrics by inspecting JMX MBean counters exposed through the Kafka broker's JMX port. The Strimzi operator does not expose JMX by default, but you can enable it by adding a `jmxOptions` stanza to the Kafka resource spec. For immediate diagnostics without reconfiguration, exec into a broker pod and query the internal metrics endpoint using `curl` and `jq`.

```bash
kubectl exec -n kafka lab-cluster-kafka-0 -- curl -s localhost:9404/metrics | grep kafka_server_replicamanager
```

The `kafka_server_replicamanager_underreplicatedpartitions` gauge counts partitions where the ISR is smaller than the replica set, a critical indicator of data durability risk. The `kafka_server_replicamanager_leadercount` gauge tracks how many partition leaders reside on this broker, which should be roughly balanced across the cluster. Imbalanced leadership creates hotspots, overloading a single broker's network and CPU resources while underutilizing others.

## Exercise 2: Benchmarking & Saturation Profiling

Event-driven systems scale horizontally by distributing partitions across brokers and consumer groups across instances, but the true performance ceiling emerges from kernel-level resource contention: CPU scheduler latency, memory allocator fragmentation, network interrupt coalescence, and disk I/O queue depths. This exercise instruments message throughput under increasing load, identifying the saturation point where latency degrades non-linearly and correlating that inflection with kernel subsystem behavior through `perf` profiling and eBPF tracing.

Begin by establishing a baseline throughput measurement for the NATS JetStream cluster deployed in Exercise 1. The `nats bench` utility generates controlled load with specified message rates and sizes, measuring end-to-end latency from publish to acknowledgment. Run a benchmark with a conservative rate of 5000 messages per second using 1 KB payloads, which approximates a moderate real-world event rate for logging or telemetry ingestion.

```bash
kubectl exec -it nats-0 -- nats bench events.perf \
  --pub 5 --sub 5 --msgs 50000 --size 1024 --no-progress
```

The utility spawns five publisher goroutines and five subscriber goroutines, distributing the target message rate across them. Record the reported average latency, 50th percentile, 95th percentile, and 99th percentile values. Healthy systems show tight latency distributions with p99 values within 2-3x of the median, indicating consistent message propagation without queuing delays. Wide distributions with high p99 values suggest intermittent congestion or CPU scheduling delays.

Increase the load incrementally by doubling the message rate to 10000, 20000, and 40000 messages per second, repeating the benchmark at each step and recording latency percentiles. Plot the relationship between throughput and tail latency; the saturation point manifests as a hockey-stick curve where latency explodes once the system exceeds its service capacity. At saturation, the NATS server's event loop cannot dequeue and process messages as fast as they arrive, causing send queues to build up in publisher TCP sockets and receive queues to accumulate in the server's socket buffers.

While running the high-load benchmark, attach a `perf` profiler to the NATS server process to capture CPU cycles spent in different kernel and userspace code paths. First, identify the NATS server's PID inside the pod by parsing the container's process tree, then use `perf record` to sample the call stack at 99 Hz for 30 seconds.

```bash
kubectl exec -it nats-0 -- sh -c 'ps aux | grep nats-server | grep -v grep'
NATS_PID=$(kubectl exec -it nats-0 -- sh -c 'pidof nats-server')
kubectl exec -it nats-0 -- perf record -F 99 -p $NATS_PID --call-graph dwarf -o /tmp/perf.data sleep 30
kubectl exec -it nats-0 -- perf report -i /tmp/perf.data --stdio
```

The `perf report` output shows a hierarchical breakdown of sampled call stacks, ordered by CPU consumption. In a saturated NATS server, expect to see significant time spent in the Go runtime's scheduler (`runtime.mcall`, `runtime.schedule`), network syscalls (`runtime.syscall`, `net.(*netFD).Read`), and memory allocation (`runtime.mallocgc`, `runtime.growslice`). High scheduler overhead indicates goroutine thrashing, where the runtime spends more time context-switching between goroutines than executing application logic. High syscall overhead suggests that the server is blocked waiting for I/O, either disk writes for JetStream persistence or network reads from client connections.

If `perf` is unavailable inside the container image, install it by exec-ing into the pod and using the package manager, or build a custom container image with debugging tools preinstalled. For production environments where modifying containers is impractical, use eBPF-based profiling from the host node without entering the container. The `bpftool` utility can attach kprobe or uprobe programs to kernel functions or userspace symbols and collect stack traces across all processes, including those inside containers.

Write a simple BPF program that counts the frequency of `tcp_sendmsg` calls, the kernel function invoked whenever userspace writes data to a TCP socket. This provides a proxy for message transmission rate at the kernel boundary. Use `bpftrace` for rapid prototyping, which compiles high-level scripts into BPF bytecode and injects them into the kernel.

```bash
# On the node hosting nats-0:
kubectl get pod nats-0 -o jsonpath='{.status.hostIP}'
ssh $NODE_IP
bpftrace -e 'kprobe:tcp_sendmsg { @sends = count(); }'
```

While the NATS benchmark runs, the `@sends` counter increments every time any process on the node calls `tcp_sendmsg`, including the NATS server and unrelated background traffic. Filter the probe to a specific PID by retrieving the NATS server's PID in the host's PID namespace, which differs from the PID inside the container's PID namespace. Use `crictl` to inspect the container and extract its host-visible PID.

```bash
CONTAINER_ID=$(crictl ps --name=nats -q | head -n1)
NATS_HOST_PID=$(crictl inspect $CONTAINER_ID | jq -r '.info.pid')
bpftrace -e "kprobe:tcp_sendmsg /pid == $NATS_HOST_PID/ { @sends = count(); }"
```

Now the probe exclusively counts `tcp_sendmsg` calls originating from the NATS server process. Extend the script to capture the number of bytes written per call by reading the `size` argument from the kernel function signature, and compute a histogram of write sizes to understand message batching behavior.

```bash
bpftrace -e "kprobe:tcp_sendmsg /pid == $NATS_HOST_PID/ { @bytes = hist(arg2); }"
```

The histogram reveals whether the server is issuing many small writes (low batching efficiency) or coalescing multiple messages into larger writes. Small writes amplify syscall overhead and prevent the kernel from leveraging TCP segmentation offload (TSO) to aggregate multiple packets into a single DMA operation. If the histogram shows a preponderance of writes below 1500 bytes, consider enabling the NATS server's write buffering or increasing the client's batch size configuration.

Shift focus to disk I/O profiling for JetStream file-backed streams. Under write-heavy workloads, the NATS server issues `fsync` or `fdatasync` calls to flush message data from kernel page cache to persistent storage, ensuring durability. Use `strace` to capture the system call trace of the NATS server process, filtering for file-related operations.

```bash
kubectl exec -it nats-0 -- strace -p $NATS_PID -e trace=write,fsync,fdatasync -c
```

The `-c` flag produces a summary table showing the number of calls, total time spent, and average time per call for each syscall. High `fsync` latencies (above 10 ms) indicate that the storage backend is saturating, either due to limited IOPS capacity on network-attached volumes or write amplification in the underlying filesystem. NVMe SSDs typically sustain sub-millisecond `fsync` latencies, while spinning disks and some cloud block storage APIs introduce multi-millisecond delays per sync operation.

Measure the storage backend's raw throughput using `fio` to isolate whether the bottleneck lies in the NATS server's I/O patterns or the volume's physical performance. Exec into the pod and write a `fio` job file that mimics JetStream's workload: sequential writes with periodic `fsync` calls.

```bash
kubectl exec -it nats-0 -- fio --name=jetstream-sim --rw=write --ioengine=sync \
  --fsync=1 --size=1G --bs=4k --directory=/data/jetstream --numjobs=1 --runtime=60
```

The output reports achieved throughput and IOPS, along with latency percentiles for write and sync operations. Compare these values to the volume's provisioned IOPS limits specified in the PersistentVolumeClaim. If `fio` achieves significantly higher throughput than the NATS server under load, the application-level batching or serialization logic is the bottleneck, not the storage. Conversely, if `fio` latencies match or exceed the NATS server's observed write latencies, the volume is the constraint, and scaling requires provisioning faster storage classes or enabling write-back caching.

Replicate this profiling methodology for Kafka by benchmarking the `lab-cluster` deployed in Exercise 1. Kafka's performance profile differs from NATS due to its log-structured storage, partition-based parallelism, and JVM runtime. Use the included `kafka-producer-perf-test.sh` script to drive load, specifying the target throughput, message size, and acknowledgment mode.

```bash
kubectl exec -n kafka lab-cluster-kafka-0 -- bin/kafka-producer-perf-test.sh \
  --topic events --num-records 100000 --record-size 1024 --throughput 10000 \
  --producer-props bootstrap.servers=localhost:9092 acks=1
```

The `acks=1` setting requires acknowledgment only from the partition leader, sacrificing durability for lower latency compared to `acks=all`, which waits for all ISR replicas. Record the reported throughput and average latency, then increase the target throughput until the actual achieved rate plateaus, indicating saturation. Kafka's throughput ceiling is typically limited by disk I/O bandwidth for log appends or network bandwidth for replica synchronization, rather than CPU as in NATS.

Profile the Kafka broker's JVM process using the `async-profiler` tool, which attaches to a running JVM and samples both Java call stacks and native code including the JVM runtime and kernel. Download the `async-profiler` release into the broker pod and run it against the Kafka JVM's PID.

```bash
kubectl exec -n kafka lab-cluster-kafka-0 -- sh -c 'curl -L -o /tmp/async-profiler.tar.gz https://github.com/async-profiler/async-profiler/releases/download/v2.9/async-profiler-2.9-linux-x64.tar.gz'
kubectl exec -n kafka lab-cluster-kafka-0 -- tar -xzf /tmp/async-profiler.tar.gz -C /tmp
KAFKA_PID=$(kubectl exec -n kafka lab-cluster-kafka-0 -- jps | grep Kafka | awk '{print $1}')
kubectl exec -n kafka lab-cluster-kafka-0 -- /tmp/async-profiler-2.9-linux-x64/profiler.sh -d 30 -f /tmp/flamegraph.html $KAFKA_PID
kubectl cp kafka/lab-cluster-kafka-0:/tmp/flamegraph.html ./kafka-flamegraph.html
```

Open the flamegraph HTML file in a browser to visualize the CPU profile as an interactive stack trace. Wide rectangles represent functions that consume significant CPU time, while tall stacks indicate deep call chains. In a saturated Kafka broker, expect to see time in log append operations (`kafka.log.Log.append`), network I/O (`kafka.network.SocketServer`), and JVM garbage collection (`G1YoungGeneration`, `G1MixedGeneration`). Excessive GC time (above 5% of CPU) suggests heap pressure from high allocation rates, which can be mitigated by increasing the JVM heap size or tuning the G1GC settings.

Instrument disk I/O at the block layer using `blktrace` to capture detailed per-request latencies, queue depths, and merge statistics. Install `blktrace` on the node and attach it to the persistent volume's block device. First, identify the device by correlating the PersistentVolumeClaim's backing PersistentVolume to the node's device tree.

```bash
PV_NAME=$(kubectl get pvc -n kafka datadir-lab-cluster-kafka-0 -o jsonpath='{.spec.volumeName}')
kubectl get pv $PV_NAME -o jsonpath='{.spec.csi.volumeHandle}'
# On the node:
lsblk -o NAME,MOUNTPOINT,SIZE,TYPE | grep <volumeHandle>
blktrace -d /dev/sdX -o /tmp/kafka-blktrace
# Run benchmark, then stop trace with Ctrl-C
blkparse -i /tmp/kafka-blktrace -o /tmp/kafka-io.txt
```

The `blkparse` output lists every I/O operation with timestamps, sector offsets, and latencies broken down into queuing delay (time in the block layer queue before dispatch), service time (time the disk controller took to complete the request), and completion delay (time waiting for the I/O scheduler to notify the kernel). High queuing delays indicate that the block device's queue is saturating, while high service times point to slow physical media or high network latency for remote-attached volumes.

## Exercise 3: Fault Injection & Recovery Analysis

Event-driven architectures promise resilience through replication and consumer group failover, but operational validation requires injecting failures and measuring recovery time. This exercise uses network partitioning, pod termination, and volume detachment to simulate node failures, verifying that Kubernetes reschedules workloads, persistent volumes reattach correctly, and message consumers resume from their committed offsets without data loss.

Start by creating a multi-consumer deployment that processes messages from the NATS JetStream `events` stream created in Exercise 1. Write a simple Go consumer that subscribes to the stream with a durable consumer configuration, explicitly acknowledging each message after simulated processing. This code must be production-ready with zero placeholders, including proper error handling and graceful shutdown.

```go
package main

import (
    "context"
    "log"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/nats-io/nats.go"
)

func main() {
    natsURL := os.Getenv("NATS_URL")
    if natsURL == "" {
        natsURL = "nats://nats.default.svc.cluster.local:4222"
    }

    nc, err := nats.Connect(natsURL, nats.RetryOnFailedConnect(true), nats.MaxReconnects(-1))
    if err != nil {
        log.Fatalf("failed to connect to NATS: %v", err)
    }
    defer nc.Close()

    js, err := nc.JetStream()
    if err != nil {
        log.Fatalf("failed to get JetStream context: %v", err)
    }

    consumerName := "fault-test-consumer"
    _, err = js.AddConsumer("events", &nats.ConsumerConfig{
        Durable:       consumerName,
        AckPolicy:     nats.AckExplicitPolicy,
        DeliverPolicy: nats.DeliverAllPolicy,
        MaxDeliver:    3,
        AckWait:       30 * time.Second,
    })
    if err != nil && err != nats.ErrConsumerNameAlreadyInUse {
        log.Fatalf("failed to create consumer: %v", err)
    }

    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    sub, err := js.PullSubscribe("events.>", consumerName, nats.Bind("events", consumerName))
    if err != nil {
        log.Fatalf("failed to subscribe: %v", err)
    }

    go func() {
        for {
            select {
            case <-ctx.Done():
                return
            default:
                msgs, err := sub.Fetch(10, nats.MaxWait(5*time.Second))
                if err != nil && err != nats.ErrTimeout {
                    log.Printf("fetch error: %v", err)
                    continue
                }
                for _, msg := range msgs {
                    log.Printf("received message: %s", string(msg.Data))
                    time.Sleep(100 * time.Millisecond) // simulate processing
                    if err := msg.Ack(); err != nil {
                        log.Printf("ack error: %v", err)
                    }
                }
            }
        }
    }()

    sig := make(chan os.Signal, 1)
    signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
    <-sig
    log.Println("shutting down gracefully")
    cancel()
    time.Sleep(1 * time.Second)
}
```

Build this consumer into a container image and deploy it as a Kubernetes Deployment with three replicas, ensuring that each replica subscribes to the same durable consumer name. NATS JetStream uses a round-robin delivery strategy for pull-based consumers, distributing messages across active subscribers within the consumer group.

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 go build -o consumer main.go

FROM alpine:3.18
RUN apk add --no-cache ca-certificates
COPY --from=builder /src/consumer /consumer
CMD ["/consumer"]
```

```bash
docker build -t event-consumer:v1 .
docker tag event-consumer:v1 localhost:5000/event-consumer:v1
docker push localhost:5000/event-consumer:v1

kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-consumer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: event-consumer
  template:
    metadata:
      labels:
        app: event-consumer
    spec:
      containers:
      - name: consumer
        image: localhost:5000/event-consumer:v1
        env:
        - name: NATS_URL
          value: "nats://nats.default.svc.cluster.local:4222"
EOF
```

Once the deployment rolls out, verify that all three pods are consuming messages by tailing their logs. Publish a burst of messages to the `events.>` subject and confirm that messages are distributed across the consumer replicas.

```bash
kubectl logs -l app=event-consumer --tail=10 -f
# In another terminal:
kubectl exec -it nats-0 -- nats pub events.test --count=30 "msg {{.Count}}"
```

The logs should show each consumer receiving roughly one-third of the messages, demonstrating load balancing. Now inject a failure by forcibly deleting one of the consumer pods to simulate a node failure or OOMKill event. Kubernetes will immediately schedule a replacement pod on another node.

```bash
POD_TO_DELETE=$(kubectl get pods -l app=event-consumer -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $POD_TO_DELETE --grace-period=0 --force
```

The `--grace-period=0` and `--force` flags bypass the normal termination sequence, simulating a hard crash. Publish another burst of messages immediately after the deletion and observe consumer logs. The remaining two pods continue processing messages without interruption, and the new pod joins the consumer group within seconds after passing readiness checks. Verify that no messages were lost by querying the consumer's pending acknowledgment count.

```bash
kubectl exec -it nats-0 -- nats consumer info events fault-test-consumer
```

The `Num Ack Pending` should remain low (under 10), indicating that the consumer group acknowledged messages promptly even during the pod restart. The `Num Redelivered` counter increments only for messages that were delivered to the crashed pod but not acknowledged before termination, and those messages are re-delivered to the surviving pods within the `AckWait` timeout.

Escalate the fault severity by partitioning the network between the NATS cluster and the consumer deployment. Use `iptables` on the node hosting one consumer pod to drop packets destined for the NATS service IP, simulating a network split or firewall misconfiguration.

```bash
NATS_SERVICE_IP=$(kubectl get svc nats -o jsonpath='{.spec.clusterIP}')
CONSUMER_NODE=$(kubectl get pod -l app=event-consumer -o jsonpath='{.items[0].spec.nodeName}' | head -n1)
CONSUMER_POD=$(kubectl get pod -l app=event-consumer --field-selector spec.nodeName=$CONSUMER_NODE -o jsonpath='{.items[0].metadata.name}')

ssh $CONSUMER_NODE "iptables -I OUTPUT -d $NATS_SERVICE_IP -j DROP"
```

Watch the consumer pod's logs to observe connection failures and reconnection attempts. The NATS Go client retries connections indefinitely by default, logging errors until connectivity is restored. Meanwhile, the other two consumer replicas on unaffected nodes continue processing messages, demonstrating that partial network failures do not bring down the entire consumer group.

```bash
kubectl logs $CONSUMER_POD --tail=20 -f
```

After observing retry behavior for 30 seconds, restore connectivity by removing the iptables rule and verify that the consumer reconnects and resumes processing.

```bash
ssh $CONSUMER_NODE "iptables -D OUTPUT -d $NATS_SERVICE_IP -j DROP"
```

The consumer logs should show a successful reconnection message, and the NATS server's connection count increments back to the original value. Inspect the TCP connection state on the recovered node using `ss` to confirm that the socket transitioned from `SYN-SENT` or `CLOSE-WAIT` back to `ESTABLISHED`.

```bash
ssh $CONSUMER_NODE "ss -tnp | grep $NATS_SERVICE_IP"
```

Now test Kafka consumer group rebalancing by deploying a consumer deployment that subscribes to the `events` topic with a consumer group ID. Kafka's rebalancing protocol automatically redistributes partition assignments when consumers join or leave the group, ensuring that all partitions remain assigned to active consumers.

Write a simple Kafka consumer in Python using the `confluent-kafka` library, configured for automatic offset commit and graceful shutdown.

```python
#!/usr/bin/env python3
import os
import signal
import sys
from confluent_kafka import Consumer, KafkaException

running = True

def signal_handler(signum, frame):
    global running
    print(f"Received signal {signum}, shutting down", file=sys.stderr)
    running = False

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP", "lab-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092")
group_id = os.getenv("GROUP_ID", "fault-test-group")

config = {
    'bootstrap.servers': bootstrap_servers,
    'group.id': group_id,
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
}

consumer = Consumer(config)
consumer.subscribe(['events'])

try:
    while running:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())
        print(f"Received message: {msg.value().decode('utf-8')}", flush=True)
finally:
    consumer.close()
    print("Consumer closed", file=sys.stderr)
```

Package this consumer into a container image and deploy it with three replicas.

```dockerfile
FROM python:3.11-slim
RUN pip install --no-cache-dir confluent-kafka==2.3.0
COPY consumer.py /consumer.py
RUN chmod +x /consumer.py
CMD ["/consumer.py"]
```

```bash
docker build -t kafka-consumer:v1 -f Dockerfile.kafka .
docker tag kafka-consumer:v1 localhost:5000/kafka-consumer:v1
docker push localhost:5000/kafka-consumer:v1

kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-consumer
  namespace: kafka
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kafka-consumer
  template:
    metadata:
      labels:
        app: kafka-consumer
    spec:
      containers:
      - name: consumer
        image: localhost:5000/kafka-consumer:v1
        env:
        - name: KAFKA_BOOTSTRAP
          value: "lab-cluster-kafka-bootstrap:9092"
        - name: GROUP_ID
          value: "fault-test-group"
EOF
```

Verify that the three replicas have divided the three partitions among themselves by checking the consumer group state using the Kafka CLI.

```bash
kubectl exec -n kafka lab-cluster-kafka-0 -- bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --group fault-test-group --describe
```

The output shows each partition assigned to a specific consumer identified by its client ID and host. With three partitions and three consumers, each consumer handles exactly one partition. Scale the deployment to five replicas and observe the rebalance.

```bash
kubectl scale deployment -n kafka kafka-consumer --replicas=5
sleep 10
kubectl exec -n kafka lab-cluster-kafka-0 -- bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --group fault-test-group --describe
```

Kafka reassigns partitions such that three consumers each own one partition, and the remaining two consumers remain idle with no partition assignments. This demonstrates that the number of active consumers cannot exceed the number of partitions. Scale back to three replicas and delete one pod to trigger another rebalance.

```bash
kubectl scale deployment -n kafka kafka-consumer --replicas=3
sleep 10
POD_TO_DELETE=$(kubectl get pods -n kafka -l app=kafka-consumer -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod -n kafka $POD_TO_DELETE
```

Watch the consumer group description and logs to observe the rebalancing protocol in action. Kafka suspends message delivery to all consumers in the group during rebalancing, reassigns partitions according to the configured strategy (RangeAssignor or RoundRobinAssignor), and resumes delivery once all consumers confirm their assignments. The entire rebalance completes within a few seconds, and no messages are lost because Kafka tracks offsets per partition-group pair in the `__consumer_offsets` internal topic.

To simulate a broker failure, cordon and drain the node hosting one of the Kafka broker pods, forcing Kubernetes to reschedule it on a different node. This tests both the StatefulSet's volume reattachment behavior and Kafka's partition leadership election.

```bash
BROKER_NODE=$(kubectl get pod -n kafka lab-cluster-kafka-0 -o jsonpath='{.spec.nodeName}')
kubectl cordon $BROKER_NODE
kubectl drain $BROKER_NODE --ignore-daemonsets --delete-emptydir-data --force --timeout=120s
```

The drain operation terminates the `lab-cluster-kafka-0` pod, triggering the StatefulSet controller to recreate it on an available node. Meanwhile, Kafka's controller broker detects the lost broker through ZooKeeper session expiration and triggers partition leadership elections for all partitions that had leaders on the failed broker. Query the topic description to observe leadership changes.

```bash
kubectl exec -n kafka lab-cluster-kafka-1 -- bin/kafka-topics.sh \
  --describe --topic events --bootstrap-server localhost:9092
```

The leader broker IDs for some partitions have changed from broker 0 to broker 1 or 2. Producer and consumer clients automatically handle this transition because the Kafka protocol includes metadata refresh logic: clients query the cluster for partition leadership when they receive `NOT_LEADER_FOR_PARTITION` errors and retry the operation against the new leader. Wait for the `lab-cluster-kafka-0` pod to reschedule and rejoin the cluster, then uncordon the node.

```bash
kubectl wait --for=condition=ready pod/lab-cluster-kafka-0 -n kafka --timeout=300s
kubectl uncordon $BROKER_NODE
```

Once the pod is ready, Kafka replicates partition data back to broker 0, and the controller may reassign some partition leaderships to rebalance load. This entire failure and recovery sequence occurs transparently to clients as long as at least one broker remains available to serve each partition's ISR.

## Diagnostic Cheat Sheet & Verification Checklist

This section consolidates the diagnostic commands and verification procedures introduced throughout the exercises into a quick reference for operational troubleshooting.

**Event Broker Connectivity & State Inspection**
- List all event broker pods: `kubectl get pods -l app.kubernetes.io/name=nats` or `kubectl get pods -n kafka -l app.kubernetes.io/name=kafka`
- Inspect pod network interface: `kubectl exec -it <pod> -- ip addr show`
- Check TCP connection state to peers: `kubectl exec -it <pod> -- ss -tinp | grep <port>`
- Verify Kubernetes service DNS resolution: `kubectl exec -it <pod> -- nslookup <service-name>`
- Query NATS stream metadata: `kubectl exec -it nats-0 -- nats stream info <stream-name>`
- Query Kafka topic partition assignments: `kubectl exec -n kafka <broker-pod> -- bin/kafka-topics.sh --describe --topic <topic> --bootstrap-server localhost:9092`

**Performance Profiling & Saturation Analysis**
- Run NATS benchmark: `kubectl exec -it nats-0 -- nats bench <subject> --pub <N> --sub <N> --msgs <count> --size <bytes>`
- Run Kafka producer benchmark: `kubectl exec -n kafka <broker> -- bin/kafka-producer-perf-test.sh --topic <topic> --num-records <count> --record-size <bytes> --throughput <rate> --producer-props bootstrap.servers=localhost:9092 acks=all`
- Profile CPU with perf: `kubectl exec -it <pod> -- perf record -F 99 -p <pid> --call-graph dwarf -o /tmp/perf.data sleep 30 && perf report -i /tmp/perf.data`
- Trace TCP syscalls: `bpftrace -e 'kprobe:tcp_sendmsg /pid == <host-pid>/ { @bytes = hist(arg2); }'`
- Measure disk I/O latency: `kubectl exec -it <pod> -- fio --name=test --rw=write --ioengine=sync --fsync=1 --size=1G --bs=4k --directory=<path>`

**Fault Injection & Recovery Verification**
- Force-delete a pod: `kubectl delete pod <pod-name> --grace-period=0 --force`
- Partition network to a service: `ssh <node> "iptables -I OUTPUT -d <service-ip> -j DROP"`
- Restore network connectivity: `ssh <node> "iptables -D OUTPUT -d <service-ip> -j DROP"`
- Cordon and drain a node: `kubectl cordon <node> && kubectl drain <node> --ignore-daemonsets --delete-emptydir-data --force`
- Verify consumer group state (Kafka): `kubectl exec -n kafka <broker> -- bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group <group-id> --describe`
- Check message redelivery count (NATS): `kubectl exec -it nats-0 -- nats consumer info <stream> <consumer>`

**Kernel & Network Stack Diagnostics**
- Inspect interface packet statistics: `kubectl exec -it <pod> -- ip -s link show eth0`
- Monitor socket buffer dynamics: `kubectl exec -it <pod> -- watch -n 1 'ss -tinp | grep <port>'`
- Capture packets on pod interface: `kubectl exec -it <pod> -- tcpdump -i eth0 -w /tmp/capture.pcap`
- Check container network namespace: `crictl inspect <container-id> | jq -r '.info.pid'` then `nsenter -t <pid> -n ip addr`
- Verify cgroup resource limits: `kubectl exec -it <pod> -- cat /sys/fs/cgroup/memory/memory.limit_in_bytes`

**ZooKeeper & etcd State Inspection**
- Query ZooKeeper controller znode: `kubectl exec -n kafka <zk-pod> -- bin/zkCli.sh get /controller`
- List Kafka broker registrations: `kubectl exec -n kafka <zk-pod> -- bin/zkCli.sh ls /brokers/ids`
- Query etcd cluster health: `kubectl exec -it <etcd-pod> -- etcdctl endpoint health --cluster`
- Watch Kubernetes events for cluster state changes: `kubectl get events --watch | grep -E 'leader|replica|rebalance'`

**Verification Checklist for Event-Driven System Health**
1. All broker pods are in `Running` state with passing readiness probes
2. TCP connections between broker replicas show `ESTABLISHED` state with zero retransmissions
3. Stream or topic replication factor matches the configured value in metadata
4. Consumer group lag remains bounded under steady load (NATS `Num Ack Pending` < 100, Kafka lag < 10000)
5. Message latency percentiles remain stable across load increments (p99 < 3x p50)
6. CPU profiling shows less than 30% time in runtime scheduler or GC
7. Disk `fsync` latency remains below 10 ms for local SSDs, below 50 ms for network volumes
8. Pod restarts do not lose messages or reset consumer offsets
9. Network partitions trigger automatic reconnection within 30 seconds
10. Broker failures trigger partition leadership election within 5 seconds

This diagnostic toolkit provides the operational foundation for maintaining event-driven infrastructure in production, enabling engineers to validate message delivery semantics, profile resource contention, and verify failover mechanisms through systematic instrumentation and fault injection.
