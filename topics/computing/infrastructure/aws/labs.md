# Operational Verification Labs: AWS Infrastructure

## Objective & Environment Setup

This guide treats your AWS environment as a living system under observation. The goal is not to click through the console but to instrument the infrastructure at the kernel, network, and orchestration layers simultaneously, correlating signals across tools the way a senior SRE would during an active incident. Every exercise runs against real AWS resources: a VPC with at least one EC2 instance (Amazon Linux 2 or Ubuntu 22.04), an EKS cluster, and an RDS instance accessible from within the VPC.

The diagnostic philosophy here is layered verification. When a symptom appears, the worst thing you can do is jump to conclusions. Instead, you descend through abstraction layers: from the Kubernetes control plane, into the container runtime, through the Linux network stack, down to the NIC driver and hardware counters. Each layer either confirms or narrows the hypothesis.

### Toolchain Installation

On your EC2 bastion or worker node, install the full diagnostic stack. On Amazon Linux 2:

```bash
sudo yum update -y
sudo yum install -y iproute tc iproute-tc ethtool tcpdump perf strace \
    bind-utils nc socat jq git python3-pip

# Install kubectl matching your EKS cluster version (adjust 1.29 as needed)
curl -Lo /usr/local/bin/kubectl \
  "https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl"
chmod +x /usr/local/bin/kubectl

# Install Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install crictl matching your container runtime (containerd on EKS 1.24+)
VERSION="v1.29.0"
curl -Lo /tmp/crictl.tar.gz \
  "https://github.com/kubernetes-sigs/cri-tools/releases/download/${VERSION}/crictl-${VERSION}-linux-amd64.tar.gz"
tar -xzf /tmp/crictl.tar.gz -C /usr/local/bin
chmod +x /usr/local/bin/crictl

# Install bpftool (kernel BPF introspection)
sudo yum install -y kernel-devel-$(uname -r) bpftool

# Install aws-cli v2 for control-plane and metadata correlation
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install

# Configure crictl to target containerd socket on EKS nodes
cat <<EOF | sudo tee /etc/crictl.yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF
```

On Ubuntu 22.04 worker nodes, replace `yum` with `apt-get` and install `linux-tools-$(uname -r)` for `perf`. Verify the environment is coherent before proceeding:

```bash
kubectl version --client
crictl version
perf --version
bpftool version
aws sts get-caller-identity --query Account --output text
```

Configure your kubeconfig to reach the EKS cluster, substituting your actual cluster name and region:

```bash
aws eks update-kubeconfig \
  --region us-east-1 \
  --name prod-cluster \
  --alias prod

kubectl config current-context
kubectl get nodes -o wide
```

---

## Exercise 1: Live State & Internal Subsystem Inspection

The first discipline of operational verification is reading the system's current state without altering it. This exercise walks through three nested scopes: the Kubernetes control plane, the container runtime layer, and the Linux network subsystem beneath them. The objective is to build a complete, correlated picture of a running EKS workload from the outside in.

### 1.1 EKS Control Plane and Node State

Begin by surveying the cluster-wide pod state. The `-A` flag exposes all namespaces, and `-o wide` adds the node placement and IP assignment, which you will need when correlating with VPC flow logs:

```bash
kubectl get pods -A -o wide --sort-by='.status.startTime'
```

Filter for non-Running pods immediately, as these represent either an admission failure, a scheduling constraint violation, or a crashloop that may be masking a deeper resource or configuration fault:

```bash
kubectl get pods -A --field-selector='status.phase!=Running' -o wide
```

Examine node resource pressure and taint state. A node reporting `MemoryPressure=True` will begin evicting pods by priority class, and you need to know this before attributing application instability to application code:

```bash
kubectl describe nodes | grep -A 10 "Conditions:"
kubectl get nodes -o json | jq '.items[] | {
  name: .metadata.name,
  allocatable_cpu: .status.allocatable.cpu,
  allocatable_mem: .status.allocatable.memory,
  conditions: [.status.conditions[] | select(.status == "True") | .type]
}'
```

For a specific node showing pressure, pull its full event stream. Events are timestamped and ordered, giving you a causal sequence without requiring log aggregation:

```bash
NODE_NAME=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl describe node "${NODE_NAME}" | grep -A 5 "Events:"
```

Inspect the VPC CNI plugin state, which on EKS is `aws-node` running as a DaemonSet. VPC CNI is responsible for attaching secondary ENIs and allocating per-pod IP addresses from the VPC CIDR. If `aws-node` is in a crashloop, pods will be stuck in `ContainerCreating` because IP allocation fails silently from the scheduler's perspective:

```bash
kubectl get pods -n kube-system -l k8s-app=aws-node -o wide
kubectl logs -n kube-system -l k8s-app=aws-node --tail=50 | grep -E "ERROR|WARN|failed"
```

### 1.2 Container Runtime Inspection with crictl

`kubectl` communicates with the API server, which in turn delegates to the kubelet, which calls the container runtime interface (CRI). `crictl` bypasses the Kubernetes control plane entirely and talks directly to `containerd` via its gRPC socket. This is essential when the API server or kubelet itself is degraded.

SSH directly onto a worker node and enumerate all running containers at the runtime level:

```bash
sudo crictl ps --state Running
sudo crictl pods --state Ready
```

Take a pod ID from the output above and inspect its full sandbox configuration. The sandbox encapsulates the network namespace, the cgroup path, and the DNS configuration injected by kubelet:

```bash
# Replace POD_ID with actual ID from crictl pods output
POD_ID=$(sudo crictl pods --name nginx --quiet | head -1)
sudo crictl inspectp "${POD_ID}" | jq '{
  network: .status.network,
  linux: .status.linux,
  state: .status.state
}'
```

The `network.ip` field returned here is the VPC-routable pod IP. Cross-reference it against the ENI attachment in AWS:

```bash
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
aws ec2 describe-network-interfaces \
  --filters "Name=attachment.instance-id,Values=${INSTANCE_ID}" \
  --query 'NetworkInterfaces[*].{ENI:NetworkInterfaceId,PrivateIPs:PrivateIpAddresses[*].PrivateIpAddress}' \
  --output json
```

If the pod IP appears in the ENI's secondary private IP list, VPC CNI allocated it correctly. If it does not, the IPAMD daemon has a stale state, and the fix is to restart `aws-node` on that specific node.

Inspect the container's cgroup resource limits as actually enforced by the kernel, not as declared in the YAML manifest. These numbers are what the kernel scheduler and OOM killer actually see:

```bash
CONTAINER_ID=$(sudo crictl ps --name nginx --quiet | head -1)
sudo crictl inspect "${CONTAINER_ID}" | jq '.info.runtimeSpec.linux.resources'

# Verify against the cgroup filesystem directly
CGROUP_PATH=$(sudo crictl inspect "${CONTAINER_ID}" | \
  jq -r '.info.runtimeSpec.linux.cgroupsPath')
cat /sys/fs/cgroup/memory/${CGROUP_PATH}/memory.limit_in_bytes
cat /sys/fs/cgroup/cpu/${CGROUP_PATH}/cpu.cfs_quota_us
cat /sys/fs/cgroup/cpu/${CGROUP_PATH}/cpu.cfs_period_us
```

The CPU limit in cores equals `cfs_quota_us / cfs_period_us`. A pod declared with `limits.cpu: 500m` will show `50000 / 100000`. Any discrepancy between the manifest value and the cgroup value indicates a kubelet configuration or container runtime bug.

### 1.3 Linux Network Stack Verification

Move now below the runtime layer into the Linux network subsystem. The VPC CNI plugin creates one `veth` pair per pod: one end lives in the pod's network namespace, the other lives in the host namespace. Understanding this topology is essential for diagnosing any connectivity issue.

Enumerate all `veth` interfaces on the host, correlate them to pods by inspecting the pod network namespaces:

```bash
# List all host-side veth interfaces
ip link show type veth

# For a specific pod, find its network namespace PID and inspect its interface
POD_PID=$(sudo crictl inspectp "${POD_ID}" | jq -r '.info.pid')
sudo nsenter -t "${POD_PID}" -n ip addr show
sudo nsenter -t "${POD_PID}" -n ip route show
```

The pod's default route will point through its `eth0` to the host-side veth address. EKS VPC CNI uses a secondary routing table per ENI to avoid policy routing conflicts. Verify the host routing tables:

```bash
# View all routing tables
ip route show table all | grep -v "^default" | head -40

# View ENI-specific routing tables (aws-cni adds tables 2 through N+1 for N ENIs)
ip route show table 2
ip rule show
```

Now apply `ss` with full socket statistics to observe active TCP connections, their buffer states, and retransmit counters. This is the most information-dense single command for TCP health assessment:

```bash
ss -tipm 'dport :443 or sport :443'
```

The fields you are looking for in the `ss` extended output are `rtt`, `rttvar`, `cwnd` (congestion window), `ssthresh`, `retrans`, and `lost`. A high `retrans` counter with a collapsed `cwnd` indicates congestion or packet loss between the node and the VPC endpoint. A high `rttvar` (variance) with stable `rtt` mean suggests intermittent path instability, often caused by an overloaded NAT Gateway or a misconfigured Elastic Load Balancer health check storm.

Examine the NIC driver statistics at the hardware level for the primary ENI. On AWS, the ENA (Elastic Network Adapter) driver exposes rich counters:

```bash
PRIMARY_IF=$(ip route show default | awk '/default/ {print $5}')
ethtool -S "${PRIMARY_IF}" | grep -E "queue_\d+_(tx|rx)_(drops|errors|cnt|bytes)"
```

The ENA driver reports per-queue statistics. If `queue_0_tx_drops` is nonzero, the driver is dropping at the transmit ring because the ring buffer is full, which indicates CPU scheduling starvation on the IRQ affinity core. Check which CPU core handles the ENI IRQ:

```bash
grep "${PRIMARY_IF}" /proc/interrupts
cat /proc/irq/$(grep "${PRIMARY_IF}" /proc/interrupts | awk '{print $1}' | tr -d ':')/smp_affinity_list
```

If all queues map to CPU 0, RSS (Receive Side Scaling) is not configured, and all interrupt processing is serialized onto a single core. Rebalance with `irqbalance` or manually set affinity:

```bash
sudo systemctl enable --now irqbalance
# Verify post-rebalance
grep "${PRIMARY_IF}" /proc/interrupts
```

Finally, capture a live packet sample at the ENI level and correlate it with an `ss` observation. Run both simultaneously in separate terminals:

```bash
# Terminal 1: capture 500 packets on port 443, write to pcap for offline analysis
sudo tcpdump -i "${PRIMARY_IF}" -n -c 500 -w /tmp/capture_$(date +%s).pcap \
  'tcp port 443 and (tcp-syn or tcp-rst or tcp-fin)'

# Terminal 2: watch socket state changes in real time during the capture window
watch -n 1 'ss -s'
```

After the capture completes, read the pcap statistics without Wireshark:

```bash
tcpdump -r /tmp/capture_*.pcap -n -q | awk '{print $NF}' | sort | uniq -c | sort -rn | head -20
```

A high count of `RST` packets originating from your node's IP toward an RDS endpoint typically means the connection pool is exhausted and the kernel is rejecting new TCP connections with RST because the application's `listen` backlog is full.

---

## Exercise 2: Benchmarking & Saturation Profiling

Knowing that a system is running is not the same as knowing it is running well. Saturation is invisible to availability checks: a service answers health probes while grinding through throttled IOPS, CPU-throttled containers, or a congested inter-AZ path. This exercise instruments performance at three layers simultaneously.

### 2.1 CPU Saturation: perf stat and CFS Throttle Analysis

Begin with a baseline CPU profile of a production workload container. `perf stat` reads hardware performance counters and provides the most accurate measure of actual CPU utilization versus scheduler throttling:

```bash
CONTAINER_PID=$(sudo crictl inspect "${CONTAINER_ID}" | jq -r '.info.pid')

sudo perf stat -p "${CONTAINER_PID}" -e \
  cycles,instructions,cache-misses,cache-references,\
  branch-misses,context-switches,cpu-migrations,\
  page-faults,minor-faults -a -- sleep 10
```

The instructions-per-cycle (IPC) ratio (`instructions / cycles`) is your CPU efficiency indicator. On modern AWS Graviton3 or Intel Ice Lake instances, a healthy compute workload should achieve IPC between 2.0 and 3.5. An IPC below 1.0 means the CPU is stalling on memory latency, cache misses, or lock contention, not actually doing useful work. High `cache-misses` relative to `cache-references` (miss rate above 5%) points to working set sizes exceeding the L3 cache, which is a data structure or algorithmic issue.

Now instrument the CFS throttle counters directly. When a container's CPU limit is enforced, the kernel removes the container's cgroup from the run queue for the remainder of the quota period. This is invisible to the application: from its perspective, time simply stops and resumes. The cumulative throttle duration is recorded in the cgroup statistics:

```bash
CGROUP_PATH=$(sudo crictl inspect "${CONTAINER_ID}" | \
  jq -r '.info.runtimeSpec.linux.cgroupsPath')

# Read throttle statistics
cat /sys/fs/cgroup/cpu/${CGROUP_PATH}/cpu.stat
```

The fields `throttled_time` (in nanoseconds) and `nr_throttled` (count of throttle events) reveal how much wall clock time the container lost to CPU limiting. If `throttled_time` grows by more than 10% of elapsed time over a 60-second window, the CPU limit is set too low for the workload's actual demand. Record the baseline:

```bash
T1=$(cat /sys/fs/cgroup/cpu/${CGROUP_PATH}/cpu.stat | grep throttled_time | awk '{print $2}')
sleep 60
T2=$(cat /sys/fs/cgroup/cpu/${CGROUP_PATH}/cpu.stat | grep throttled_time | awk '{print $2}')
echo "Throttled nanoseconds in 60s window: $((T2 - T1))"
echo "Throttle percentage: $(echo "scale=4; ($T2 - $T1) / 60000000000 * 100" | bc)%"
```

A throttle percentage above 15% during normal operation means you need to either raise the CPU limit or horizontally scale the deployment. For EKS workloads, patch the deployment resource limits without a full rollout:

```bash
kubectl patch deployment nginx-deployment -n default \
  --type='json' \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/cpu","value":"1000m"}]'
```

### 2.2 Network Throughput and Latency Profiling

The EC2 network performance envelope depends on instance type and baseline bandwidth allocation. ENA burst bandwidth is available for short durations; sustained transfer above the baseline is throttled at the hypervisor. You need to know both values for your instance and compare them against observed throughput.

Query the instance's network performance specification:

```bash
INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
aws ec2 describe-instance-types \
  --instance-types "${INSTANCE_TYPE}" \
  --query 'InstanceTypes[0].NetworkInfo.{
    NetworkPerformance:NetworkPerformance,
    MaxNetworkInterfaces:MaximumNetworkInterfaces,
    MaxIpv4PerInterface:Ipv4AddressesPerInterface
  }' \
  --output table
```

Now measure actual TCP throughput between two nodes in the same VPC. Deploy a lightweight `iperf3` server as a Kubernetes pod and run the client from the worker node:

```bash
# Deploy iperf3 server pod
kubectl apply -f - <<'MANIFEST'
apiVersion: v1
kind: Pod
metadata:
  name: iperf3-server
  namespace: default
  labels:
    app: iperf3-server
spec:
  containers:
  - name: iperf3
    image: networkstatic/iperf3:latest
    args: ["-s"]
    ports:
    - containerPort: 5201
      protocol: TCP
    resources:
      requests:
        cpu: "500m"
        memory: "128Mi"
      limits:
        cpu: "1000m"
        memory: "256Mi"
  restartPolicy: Never
---
apiVersion: v1
kind: Service
metadata:
  name: iperf3-server-svc
  namespace: default
spec:
  selector:
    app: iperf3-server
  ports:
  - port: 5201
    targetPort: 5201
    protocol: TCP
  clusterIP: None
MANIFEST

# Wait for pod readiness
kubectl wait --for=condition=Ready pod/iperf3-server --timeout=60s

IPERF_SERVER_IP=$(kubectl get pod iperf3-server -o jsonpath='{.status.podIP}')
echo "iperf3 server IP: ${IPERF_SERVER_IP}"

# Run iperf3 client from the host network namespace (bypasses CNI overhead)
sudo iperf3 -c "${IPERF_SERVER_IP}" \
  -t 30 \
  -P 8 \
  -b 0 \
  --json | jq '.end.sum_sent + .end.sum_received | {
    bits_per_second: .bits_per_second,
    gbps: (.bits_per_second / 1e9)
  }'
```

Compare the measured Gbps against the instance's advertised network performance. If the measured value is significantly below the advertised baseline (not burst), the hypervisor is throttling the instance due to sustained high utilization. Check ENA driver-level byte counters to confirm:

```bash
# Sample ENA byte counters across a 10-second interval
ethtool -S "${PRIMARY_IF}" | grep "tx_bytes\|rx_bytes" > /tmp/ena_t1.txt
sleep 10
ethtool -S "${PRIMARY_IF}" | grep "tx_bytes\|rx_bytes" > /tmp/ena_t2.txt
paste /tmp/ena_t1.txt /tmp/ena_t2.txt | awk '{
  bytes_delta = $4 - $2
  mbps = (bytes_delta * 8) / 10 / 1e6
  printf "%s delta=%d bytes = %.2f Mbps\n", $1, bytes_delta, mbps
}'
```

For cross-AZ latency measurement, which is critical for RDS Multi-AZ and cross-AZ Kubernetes service traffic, use `hping3` or `ping` with high-frequency sampling:

```bash
# Install hping3
sudo yum install -y hping3

# Measure TCP handshake latency to RDS endpoint on port 5432 (replace with your RDS endpoint)
RDS_ENDPOINT="your-rds-instance.cluster-xxxx.us-east-1.rds.amazonaws.com"
sudo hping3 -S -p 5432 -c 100 -i u100000 "${RDS_ENDPOINT}" 2>&1 | \
  grep -E "rtt|seq" | tail -5
```

The TCP SYN-ACK round-trip time to an RDS Multi-AZ endpoint in a different AZ should be between 0.3ms and 1.5ms within the same AWS region. Values above 2ms indicate either a routing anomaly, a Network ACL rule forcing traffic through an inspection appliance, or VPC peering across regions.

### 2.3 Disk I/O Saturation on EBS

EBS volumes have both throughput (MiB/s) and IOPS limits that are enforced independently. A volume can be throughput-saturated without hitting its IOPS ceiling if the I/O request size is large, or IOPS-saturated with low throughput if the application issues many small random reads. Distinguishing between these two saturation modes requires reading the block device queue statistics:

```bash
# Identify the EBS block device backing the container's volume
kubectl get pv -o json | jq '.items[] | {
  name: .metadata.name,
  volumeId: .spec.csi.volumeHandle,
  capacity: .spec.capacity.storage,
  node: .spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]
}'

# Map the EBS volume ID to the block device on this node
lsblk -d -o NAME,SIZE,MODEL,SERIAL

# Read live I/O statistics for a specific block device (e.g., nvme1n1)
BLOCK_DEV="nvme1n1"
iostat -xdz 2 10 "${BLOCK_DEV}" | awk '/^nvme1n1/ {
  printf "util=%s%% await=%sms r_iops=%s w_iops=%s r_MBps=%s w_MBps=%s\n",
    $NF, $10, $4, $5, $6, $7
}'
```

The utilization percentage (`util`) from `iostat` represents the fraction of time the device was busy processing at least one I/O request. A `util` above 80% over a sustained window means the device queue is non-empty continuously, which will manifest as increased `await` latency. For gp3 EBS volumes, the default baseline is 3000 IOPS and 125 MiB/s; for io2 Block Express, up to 256,000 IOPS. If your `r_iops + w_iops` total approaches the provisioned IOPS ceiling, you have confirmed IOPS saturation.

Verify at the CloudWatch level to get a second source of truth that is not subject to OS-level caching effects:

```bash
VOLUME_ID=$(aws ec2 describe-volumes \
  --filters "Name=attachment.instance-id,Values=${INSTANCE_ID}" \
  --query 'Volumes[0].VolumeId' \
  --output text)

# Query CloudWatch for VolumeQueueLength over the last 15 minutes
aws cloudwatch get-metric-statistics \
  --namespace AWS/EBS \
  --metric-name VolumeQueueLength \
  --dimensions "Name=VolumeId,Value=${VOLUME_ID}" \
  --start-time "$(date -u -d '15 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --period 60 \
  --statistics Average Maximum \
  --query 'sort_by(Datapoints, &Timestamp)[-5:].{time:Timestamp,avg:Average,max:Maximum}' \
  --output table
```

A `VolumeQueueLength` above 1.0 on average means I/O requests are queuing at the EBS layer. If the value spikes to 10+ during your performance test, the volume is severely saturated and you should either provision higher IOPS or investigate the application's I/O access pattern for sequential versus random characteristics.

---

## Exercise 3: Fault Injection & Recovery Analysis

Understanding recovery behavior requires introducing failures deliberately and measuring how long each layer takes to detect, respond, and restore service. This exercise injects three classes of fault: a network partition, a container crash loop, and a node draining event, then measures the system's response at each diagnostic layer.

### 3.1 Network Partition Simulation Using iptables

Simulate a loss of connectivity between a pod and its external dependency by manipulating `iptables` rules inside the pod's network namespace. This is safer than modifying host-level rules because the fault is fully contained to a single pod and reversible with one command.

Identify the target pod and its outbound destination IP (here, an RDS endpoint):

```bash
TARGET_POD="nginx-deployment-xxxxxxx-yyyyy"
TARGET_NS="default"
RDS_IP=$(dig +short "${RDS_ENDPOINT}" | head -1)
echo "RDS IP: ${RDS_IP}"

# Get the pod's PID for namespace entry
POD_PID=$(kubectl get pod "${TARGET_POD}" -n "${TARGET_NS}" \
  -o jsonpath='{.status.containerStatuses[0].containerID}' | \
  sed 's|containerd://||' | xargs -I{} sudo crictl inspect {} | jq -r '.info.pid')

# Inject a DROP rule for all traffic to the RDS IP, inside the pod's netns
sudo nsenter -t "${POD_PID}" -n \
  iptables -A OUTPUT -d "${RDS_IP}" -j DROP

# Verify the rule is active inside the pod
sudo nsenter -t "${POD_PID}" -n iptables -L OUTPUT -n -v
```

Now measure how long the application takes to detect the connectivity loss. The TCP connection does not reset immediately; the kernel will retransmit SYN packets according to the `tcp_syn_retries` and `tcp_retries2` parameters before giving up. Observe the retransmission behavior in real time:

```bash
# In a separate terminal, watch TCP socket state changes
sudo nsenter -t "${POD_PID}" -n \
  watch -n 0.5 'ss -tipm dst '"${RDS_IP}"

# In another terminal, strace the application's connect() system calls to measure the delay
sudo strace -p "${POD_PID}" -e trace=connect,sendto,recvfrom -T -tt 2>&1 | \
  grep -E "connect|ETIMEDOUT|ECONNREFUSED"
```

The `ss` output will show the socket transition from `ESTABLISHED` to `SYN_SENT` as the application attempts reconnection, and eventually the connection will be removed from the socket table when the kernel abandons retransmission. The `strace` output will show the wall-clock timestamp of `connect()` and the duration until `ETIMEDOUT` appears. This duration is determined by the kernel's TCP timeout ladder: approximately 127 seconds at default `tcp_retries2=15` on a fresh connection attempt.

For a production system, 127 seconds of undetected failure is catastrophic. This is why connection pools must configure application-level timeouts well below the kernel default:

```bash
# Check current TCP timeout parameters on the node
sysctl net.ipv4.tcp_syn_retries
sysctl net.ipv4.tcp_retries2
sysctl net.ipv4.tcp_keepalive_time
sysctl net.ipv4.tcp_keepalive_intvl
sysctl net.ipv4.tcp_keepalive_probes
```

After observing the failure behavior, remove the fault injection:

```bash
sudo nsenter -t "${POD_PID}" -n \
  iptables -D OUTPUT -d "${RDS_IP}" -j DROP

# Confirm rule removed
sudo nsenter -t "${POD_PID}" -n iptables -L OUTPUT -n -v
```

Measure the TCP recovery time from the moment the rule is removed to the moment the first successful `SELECT 1` returns from RDS. If using a connection pool like `pgBouncer` or `HikariCP`, the recovery should complete within one health-check interval plus one TCP handshake. If the pool does not recover automatically, the pool's `connection-test-query` or `keepaliveTime` is not configured.

### 3.2 Container Crash Loop Injection and Kubelet Recovery Analysis

Inject a crash loop by sending `SIGKILL` directly to the container's init process. This bypasses the application's signal handler and simulates an OOM kill, which the kernel also delivers as `SIGKILL` with exit code 137:

```bash
# Get the container's PID 1 inside the pod's namespace
CONTAINER_INIT_PID=$(sudo nsenter -t "${POD_PID}" -n \
  sh -c 'cat /proc/1/status | grep Pid | awk "{print \$2}"')

# Terminate it; kubelet will observe the container exit and restart it
sudo kill -9 "${CONTAINER_INIT_PID}"
```

Immediately begin watching the kubelet's restart counter and backoff behavior:

```bash
# Watch restart count increment in real time
kubectl get pod "${TARGET_POD}" -n "${TARGET_NS}" -w &
WATCH_PID=$!

# Simultaneously capture kubelet logs showing container lifecycle events
journalctl -u kubelet -f --no-pager | \
  grep -E "Started container|Back-off|Error response|OOMKilling" &
JOURNAL_PID=$!

# Let both run for 5 minutes to observe the full backoff sequence
sleep 300
kill "${WATCH_PID}" "${JOURNAL_PID}"
```

The kubelet implements an exponential backoff for crashlooping containers starting at 10 seconds and doubling up to a maximum of 5 minutes: 10s, 20s, 40s, 80s, 160s, 300s. After 300 seconds the interval is capped. Record the actual observed restart intervals from the `kubectl get pod -w` output and compare them against this theoretical sequence. Any deviation indicates a modification to the kubelet's `--pod-infra-container-image` or `--max-pods` settings that alters default behavior.

Examine how the kubelet reports the OOM event through the pod's status conditions and observe what the container runtime records:

```bash
kubectl describe pod "${TARGET_POD}" -n "${TARGET_NS}" | \
  grep -A 20 "Last State:"

# Check containerd's event log for the container lifecycle event
sudo journalctl -u containerd --since "5 minutes ago" | \
  grep -E "exit|OOM|container_id"
```

After the pod recovers from the crash loop (you can accelerate this by patching the deployment to remove the `restartPolicy: Always` temporarily and re-applying), verify that the VPC CNI plugin correctly retained the pod IP or allocated a new one:

```bash
NEW_POD_IP=$(kubectl get pod "${TARGET_POD}" -n "${TARGET_NS}" \
  -o jsonpath='{.status.podIP}')
echo "Pod IP after recovery: ${NEW_POD_IP}"

# Confirm the IP is allocated in the ENI secondary addresses
aws ec2 describe-network-interfaces \
  --filters "Name=attachment.instance-id,Values=${INSTANCE_ID}" \
  --query 'NetworkInterfaces[*].PrivateIpAddresses[*].PrivateIpAddress' \
  --output text | tr '\t' '\n' | grep "${NEW_POD_IP}"
```

### 3.3 Node Drain and EBS Volume Reattachment Timing

The final fault scenario measures the full recovery path when a node is taken out of service. This is the most complex failure mode because it involves the Kubernetes control plane, the EC2 API, and the EBS attachment API all operating concurrently with hard timeout constraints.

Before draining, capture the current state of PersistentVolumeClaims and their volume attachments:

```bash
kubectl get pvc -A -o json | jq '.items[] | {
  name: .metadata.name,
  namespace: .metadata.namespace,
  phase: .status.phase,
  volumeName: .spec.volumeName,
  storageClass: .spec.storageClassName
}'

kubectl get volumeattachments -o json | jq '.items[] | {
  pv: .spec.source.persistentVolumeName,
  node: .spec.nodeName,
  attached: .status.attached
}'
```

Record the current time and begin the drain sequence. The `--grace-period=30` gives pods 30 seconds to terminate cleanly, flushing in-flight writes to EBS before the volume detaches:

```bash
DRAIN_NODE="${NODE_NAME}"
START_TIME=$(date +%s%N)  # nanoseconds for high-resolution measurement

kubectl drain "${DRAIN_NODE}" \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=30 \
  --timeout=5m \
  --force

DRAIN_COMPLETE_TIME=$(date +%s%N)
DRAIN_DURATION_MS=$(( (DRAIN_COMPLETE_TIME - START_TIME) / 1000000 ))
echo "Node drain completed in ${DRAIN_DURATION_MS}ms"
```

Watch the EBS volume detachment and reattachment from the AWS API perspective in a parallel terminal:

```bash
# Poll volume attachment state every 2 seconds
while true; do
  aws ec2 describe-volumes \
    --volume-ids "${VOLUME_ID}" \
    --query 'Volumes[0].Attachments[0].{State:State,InstanceId:InstanceId,Time:AttachTime}' \
    --output json
  sleep 2
done
```

The EBS volume will transition through `detaching`, `available`, and then `attaching` as Kubernetes reschedules the pod onto a healthy node and the EBS CSI driver calls `ControllerPublishVolume` via the gRPC interface to the EBS CSI controller pod. Measure the time the volume spends in `available` state: this is the window during which no I/O is possible, which is the actual application downtime for stateful workloads.

After the pod reschedules, verify the mount propagation:

```bash
NEW_NODE=$(kubectl get pod "${TARGET_POD}" -n "${TARGET_NS}" \
  -o jsonpath='{.spec.nodeName}')
echo "Pod rescheduled to node: ${NEW_NODE}"

# SSH to the new node and verify the EBS device is mounted
ssh "${NEW_NODE}" "mount | grep nvme"
ssh "${NEW_NODE}" "lsblk -d -o NAME,SIZE,TYPE,MOUNTPOINT | grep nvme"
```

If the pod is stuck in `ContainerCreating` after rescheduling, the EBS volume is likely still in `detaching` state because the previous node did not fully release it. This happens when the node loses network connectivity before completing the detachment handshake. Resolve it by forcing the detachment from the AWS API (this is safe only after confirming the original node is fully terminated):

```bash
aws ec2 detach-volume \
  --volume-id "${VOLUME_ID}" \
  --force
```

Document the total observed recovery time from drain initiation to successful pod readiness:

```bash
kubectl wait --for=condition=Ready pod -l "app=your-app-label" \
  -n "${TARGET_NS}" \
  --timeout=10m

RECOVERY_TIME=$(date +%s%N)
TOTAL_RECOVERY_MS=$(( (RECOVERY_TIME - START_TIME) / 1000000 ))
echo "Total recovery time: ${TOTAL_RECOVERY_MS}ms ($(( TOTAL_RECOVERY_MS / 1000 ))s)"
```

This end-to-end recovery duration is your actual RTO for this failure scenario. If it exceeds your SLA, the levers are: pre-warming pod scheduling on standby nodes, using `ReadWriteMany` EFS volumes instead of `ReadWriteOnce` EBS to eliminate reattachment delay, or switching stateful workloads to RDS Aurora with application-level connection retry logic.

---

## Diagnostic Cheat Sheet & Verification Checklist

The following reference consolidates the highest-signal commands from the exercises above into a systematic runbook ordered by diagnostic layer, from the control plane down to hardware. Run these in sequence during any AWS infrastructure incident before forming a hypothesis about root cause.

### Control Plane and Scheduling Layer

| Verification Target | Command | Expected Healthy Output |
|---|---|---|
| All pods running | `kubectl get pods -A --field-selector='status.phase!=Running'` | Zero rows returned |
| Node conditions | `kubectl get nodes` | All nodes `Ready`, no `NotReady` |
| VPC CNI health | `kubectl logs -n kube-system -l k8s-app=aws-node --tail=20` | No `ERROR` lines |
| Volume attachments | `kubectl get volumeattachments` | All `attached: true` |
| Pending pods cause | `kubectl describe pod <pod> \| grep -A 5 Events` | No `FailedScheduling` events |
| ENI IP pool depth | `kubectl logs -n kube-system -l k8s-app=aws-node \| grep IPAMD` | `Warm pool` has at least 2 available IPs |

### Container Runtime Layer

| Verification Target | Command | Expected Healthy Output |
|---|---|---|
| Runtime pod state | `sudo crictl pods --state Ready` | All expected pods listed |
| Cgroup CPU limit | `cat /sys/fs/cgroup/cpu/<path>/cpu.stat` | `throttled_time` delta < 10% of elapsed ns |
| Cgroup memory limit | `cat /sys/fs/cgroup/memory/<path>/memory.limit_in_bytes` | Matches manifest `limits.memory` in bytes |
| OOM kill history | `sudo journalctl -k \| grep oom_kill_process` | No recent OOM kills |
| Container restart reason | `sudo crictl inspect <id> \| jq .info.runtimeSpec` | `exitCode: 0` on last exit |

### Linux Network Stack Layer

```bash
# Five-command network health sweep — run on every incident

# 1. Interface error counters (non-zero values demand investigation)
ip -s link show "${PRIMARY_IF}" | grep -E "RX:|TX:|errors|dropped|overrun"

# 2. TCP socket summary with retransmit visibility
ss -s && ss -tipm 'state established' | grep -E "retrans|lost" | head -20

# 3. ENA hardware queue drops
ethtool -S "${PRIMARY_IF}" | grep -E "_drops|_errors" | awk '$2 != 0'

# 4. Routing table integrity check (all expected routes present)
ip route show table main
ip route show table 2  # EKS VPC CNI secondary ENI table

# 5. conntrack table utilization (exhaustion causes silent packet drops)
cat /proc/net/nf_conntrack | wc -l
sysctl net.netfilter.nf_conntrack_max
```

### EBS and Storage Layer

```bash
# Storage health sweep — run when application latency is elevated

# 1. I/O utilization and await latency
iostat -xdz 1 5 | awk '/^nvme/ {print $1, "util="$NF"%", "await="$10"ms"}'

# 2. EBS volume queue depth from CloudWatch (replace VOLUME_ID)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EBS \
  --metric-name VolumeQueueLength \
  --dimensions "Name=VolumeId,Value=${VOLUME_ID}" \
  --start-time "$(date -u -d '5 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --period 60 \
  --statistics Average \
  --query 'max_by(Datapoints, &Average).Average'

# 3. Filesystem inode exhaustion (a full inode table causes ENOSPC with available space)
df -ih | grep -v tmpfs

# 4. Block device error kernel messages
sudo dmesg | grep -E "I/O error|blk_update_request|nvme"
```

### EC2 and VPC Infrastructure Layer

```bash
# EC2 and VPC health sweep — run when network-level anomalies appear

# 1. Instance status checks (must both show passed)
aws ec2 describe-instance-status \
  --instance-ids "${INSTANCE_ID}" \
  --query 'InstanceStatuses[0].{SystemStatus:SystemStatus.Status,InstanceStatus:InstanceStatus.Status}'

# 2. Security Group rules audit for a specific port (replace 5432 and SG ID)
aws ec2 describe-security-group-rules \
  --filters "Name=group-id,Values=sg-xxxxxxxxxxxxxxxxx" \
  --query 'SecurityGroupRules[?ToPort==`5432`].{FromPort:FromPort,ToPort:ToPort,CidrIpv4:CidrIpv4,IsEgress:IsEgress}'

# 3. VPC flow log query for rejected traffic in the last 10 minutes (requires Athena or Insights)
aws logs filter-log-events \
  --log-group-name "/aws/vpc/flowlogs" \
  --start-time "$(date -d '10 minutes ago' +%s000)" \
  --filter-pattern "REJECT" \
  --query 'events[*].message' \
  --output text | head -20

# 4. NAT Gateway packet drop counter
aws cloudwatch get-metric-statistics \
  --namespace AWS/NatGateway \
  --metric-name PacketsDropCount \
  --dimensions "Name=NatGatewayId,Value=${NAT_GW_ID}" \
  --start-time "$(date -u -d '15 minutes ago' '+%Y-%m-%dT%H:%M:%SZ')" \
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
  --period 60 \
  --statistics Sum \
  --query 'sum(Datapoints[*].Sum)'

# 5. ENI attachment count versus instance type limit
aws ec2 describe-instances \
  --instance-ids "${INSTANCE_ID}" \
  --query 'Reservations[0].Instances[0].NetworkInterfaces | length(@)'
aws ec2 describe-instance-types \
  --instance-types "${INSTANCE_TYPE}" \
  --query 'InstanceTypes[0].NetworkInfo.MaximumNetworkInterfaces'
```

### Incident Decision Tree

When a production alert fires, the fastest path to root cause follows this verification sequence. Start at the control plane and descend only when the layer above clears.

Does `kubectl get pods -A` show non-Running pods? If yes, describe the pod events and check VPC CNI logs before looking anywhere else. If no, check node conditions for memory or disk pressure.

Are node conditions clean but application latency is elevated? Run the five-command network sweep. If `ss` shows retransmits against the backend, check the EBS I/O sweep and the VPC flow log for rejects. If the EBS utilization is below 70% and flow logs show no rejects, the fault is application-layer.

Are ENA hardware drops nonzero? Check IRQ affinity and `irqbalance` status. A single-queue IRQ on CPU 0 under sustained throughput is the most common cause of ENA drop under load on `m5` and `c5` instance families.

Does CloudWatch show `VolumeQueueLength` above 1.0? The fault is IOPS saturation. Either the provisioned IOPS is insufficient, or the application's I/O pattern changed from sequential to random without a corresponding volume reconfiguration.

Working through this layered verification sequence consistently, instrument-first rather than hypothesis-first, is what distinguishes a systematic infrastructure engineer from one who guesses and applies random fixes under pressure. Every command in this guide produces a specific measurable signal. Collect the signals before drawing conclusions.
