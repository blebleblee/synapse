# Operational Verification Labs: AWS EKS

## Objective & Environment Setup

This guide treats your EKS cluster as a layered system: a Linux kernel running inside each EC2 worker node, a container runtime (containerd) managed by the kubelet, a control plane served from managed etcd and Kubernetes API server endpoints, and a VPC-native CNI (aws-node, implementing the AWS VPC CNI plugin) stitching pod IPs directly into the node's network interface card via elastic network interfaces (ENIs). Every diagnostic in these labs works from that mental model outward — from kernel socket state through container namespaces, into the Kubernetes control-plane API, and finally into the data-plane network fabric.

The goal is not merely to confirm that workloads are running, but to verify *why* they are running correctly, to quantify the headroom before they will fail, and to understand exactly what happens when they do fail and what the cluster does to recover. Each exercise is designed to be run against a live EKS cluster with real workloads. You will need a cluster with at least two managed node groups (one for system workloads, one for a sample application), internet egress, and AWS IAM permissions for EKS, EC2, and CloudWatch.

### Toolchain Installation

On a Linux workstation or a Cloud9 instance co-located in the same VPC as your cluster, install the full diagnostic stack. The commands below target Amazon Linux 2023 / Ubuntu 22.04 interchangeably; substitute `dnf` for `apt` as needed.

```bash
# kubectl — Kubernetes CLI
curl -Lo kubectl \
  "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip awscliv2.zip && sudo ./aws/install

# eksctl
curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz"
tar -xzf eksctl_Linux_amd64.tar.gz && sudo mv eksctl /usr/local/bin/

# Helm v3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# iproute2, ethtool, tcpdump, perf, strace, bpftool, ss (ss ships with iproute2)
sudo apt-get update && sudo apt-get install -y \
  iproute2 ethtool tcpdump linux-tools-common linux-tools-$(uname -r) \
  strace bpfcc-tools bpftool netcat-openbsd jq curl

# crictl — CRI-compatible container runtime CLI
VERSION="v1.30.0"
curl -Lo crictl.tar.gz \
  "https://github.com/kubernetes-sigs/cri-tools/releases/download/${VERSION}/crictl-${VERSION}-linux-amd64.tar.gz"
sudo tar -xzf crictl.tar.gz -C /usr/local/bin/
```

Configure kubectl and validate cluster connectivity:

```bash
aws eks update-kubeconfig \
  --region us-east-1 \
  --name prod-eks-cluster \
  --alias prod

kubectl cluster-info
kubectl get nodes -o wide
```

Configure crictl to speak to the containerd socket. On EKS nodes running AL2023, containerd is the default runtime since EKS 1.24:

```bash
# On the worker node (SSH via SSM or EC2 Instance Connect)
sudo tee /etc/crictl.yaml <<'EOF'
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
debug: false
EOF

sudo crictl version
```

Deploy the reference workload that all three exercises will diagnose. This is a three-tier application: an NGINX frontend, a Go-based API server, and a Redis cache, all in a dedicated namespace.

```bash
kubectl create namespace lab-workload

# Redis
kubectl apply -n lab-workload -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: lab-workload
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: lab-workload
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
EOF

# Go API server (using a prebuilt echo-server image for reproducibility)
kubectl apply -n lab-workload -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: lab-workload
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
      - name: api
        image: ealen/echo-server:0.9.2
        ports:
        - containerPort: 80
        env:
        - name: PORT
          value: "80"
        resources:
          requests:
            cpu: "200m"
            memory: "128Mi"
          limits:
            cpu: "1000m"
            memory: "256Mi"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: api-server
  namespace: lab-workload
spec:
  selector:
    app: api-server
  ports:
  - port: 80
    targetPort: 80
EOF

# NGINX frontend
kubectl apply -n lab-workload -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: lab-workload
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "500m"
            memory: "128Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: lab-workload
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "external"
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl -n lab-workload wait --for=condition=available --timeout=120s deployment/redis
kubectl -n lab-workload wait --for=condition=available --timeout=120s deployment/api-server
kubectl -n lab-workload wait --for=condition=available --timeout=120s deployment/frontend
```

---

## Exercise 1: Live State & Internal Subsystem Inspection

The discipline of live-state inspection is methodical archaeology. You are reading the runtime truth of a system that has no pause button, correlating what the kernel sees at the socket and namespace level against what the Kubernetes control plane believes, and against what the CNI data plane has actually programmed. These three views routinely diverge in a production EKS cluster after a botched rolling update, a node NotReady event, or a CNI plugin restart, which is precisely why you must be able to read all three simultaneously.

### 1.1 Control Plane API State

Begin at the top of the stack. The Kubernetes API server on EKS is fully managed by AWS and exposed through a private or public endpoint backed by a Network Load Balancer. Your first task is to confirm reachability, latency, and the consistency of object state across all three API server replicas (EKS runs three for HA). The `--v=6` flag on kubectl requests exposes the full HTTP method, URL, and round-trip timing for each API call, which reveals whether the latency budget of your control plane is healthy:

```bash
# Confirm API server endpoint and check response latency
kubectl cluster-info --v=6 2>&1 | grep -E "(GET|POST|PATCH|round_trip)"

# Full object snapshot — all namespaces, all resource types relevant to our workload
kubectl get pods,svc,endpoints,deployments -n lab-workload -o wide

# Check pod conditions in depth — Initialized, Ready, ContainersReady, PodScheduled
kubectl describe pod -n lab-workload -l app=api-server | \
  grep -A 20 "^Conditions:"

# Node-level capacity, allocatable resources, and taints
kubectl get nodes -o custom-columns=\
"NAME:.metadata.name,\
STATUS:.status.conditions[-1].type,\
CPU_CAP:.status.capacity.cpu,\
CPU_ALLOC:.status.allocatable.cpu,\
MEM_CAP:.status.capacity.memory,\
MEM_ALLOC:.status.allocatable.memory,\
PODS:.status.allocatable.pods"

# Per-node pod allocation pressure
kubectl describe nodes | grep -A 5 "Allocated resources:"
```

The `Endpoints` object is frequently overlooked but is the most honest representation of which pod IPs the kube-proxy (or VPC CNI eBPF datapath) has actually programmed into forwarding rules. If a pod is `Running` but its IP is absent from the endpoint slice, traffic is not reaching it regardless of what the Deployment says:

```bash
# Inspect EndpointSlices directly — more granular than the legacy Endpoints object
kubectl get endpointslices -n lab-workload -o yaml | \
  python3 -c "
import sys, yaml
data = yaml.safe_load(sys.stdin)
for ep in data.get('items', []):
    svc = ep['metadata']['labels'].get('kubernetes.io/service-name')
    for endpoint in ep.get('endpoints', []):
        print(f\"Service={svc} IP={endpoint['addresses'][0]} Ready={endpoint['conditions']['ready']}\")
"
```

### 1.2 Node-Level Network Interface Inspection

SSH into one of the worker nodes. On EKS with the AWS VPC CNI plugin, every pod IP is a secondary private IPv4 address assigned to one of the node's ENIs. The kernel routes packets between pod namespaces and the primary ENI using a combination of `veth` pairs, `iptables` rules (or eBPF programs), and policy-based routing tables. Understanding this topology lets you trace any packet from a pod all the way to the wire:

```bash
# List all network interfaces with traffic counters — look for eni* and veth* interfaces
ip -s link show

# Show the full routing table including per-ENI policy tables
ip route show table all | grep -v "^default" | sort

# The VPC CNI creates a separate routing table per ENI (table 2, 3, ... N)
# Table 2 corresponds to eth1, table 3 to eth2, etc.
ip route show table 2
ip route show table 3

# Show policy routing rules — each pod subnet is routed via its owning ENI
ip rule show

# Map ENI interface names to MAC addresses and confirm they match EC2 metadata
for iface in $(ip link show | grep "eni\|eth" | awk -F': ' '{print $2}' | tr -d '@NET'); do
  mac=$(cat /sys/class/net/${iface}/address 2>/dev/null)
  echo "Interface: ${iface}  MAC: ${mac}"
done
```

The `ethtool` command reveals the physical and driver-level properties of each ENI interface. On Nitro-based EC2 instances, all ENIs are backed by the ENA (Elastic Network Adapter) driver. Confirming driver version and feature negotiation matters when diagnosing intermittent TCP resets or unexpected MTU fragmentation:

```bash
# Driver info and firmware version for the primary ENI
sudo ethtool -i eth0

# Ring buffer sizes — small rings cause packet drops under burst traffic
sudo ethtool -g eth0

# Offload features — verify TSO, GRO, checksum offload are enabled
sudo ethtool -k eth0 | grep -E "(tcp-segmentation|generic-receive|rx-checksumming|tx-checksumming)"

# NIC statistics — look for rx_missed_errors, rx_fifo_errors, tx_dropped
sudo ethtool -S eth0 | grep -E "(error|drop|miss|fifo)"

# Confirm MTU — EKS VPC CNI sets pod MTU to node MTU minus overhead (typically 9001 - 50 = 8951)
ip link show eth0 | grep mtu
kubectl -n kube-system get daemonset aws-node -o jsonpath='{.spec.template.spec.containers[0].env}' | \
  python3 -c "import sys,json; [print(e['name'],'=',e.get('value','<from_field_ref>')) for e in json.load(sys.stdin)]" | \
  grep -i mtu
```

### 1.3 Container Runtime Inspection with crictl

On EKS nodes, the kubelet delegates all container lifecycle operations to containerd via the Container Runtime Interface (CRI) gRPC socket. The `crictl` tool speaks this same protocol and can enumerate containers, inspect their state, and read their logs independently of the kubelet. This matters during partial kubelet failures, where the control plane shows pods as `Unknown` but the containers are actually still running:

```bash
# List all running pods from containerd's perspective
sudo crictl pods --state Running

# List containers with their images and state
sudo crictl ps -a

# Inspect a specific container — get its PID, namespaces, and mounts
CONTAINER_ID=$(sudo crictl ps --name api | awk 'NR==2{print $1}')
sudo crictl inspect ${CONTAINER_ID} | python3 -c "
import sys, json
d = json.load(sys.stdin)
info = d['info']['runtimeSpec']
print('PID:', d['info']['pid'])
print('Namespaces:')
for ns in info.get('linux', {}).get('namespaces', []):
    print(' ', ns['type'], '->', ns.get('path', 'private'))
print('CgroupsPath:', info.get('linux', {}).get('cgroupsPath', 'N/A'))
"

# Stream live logs from the container
sudo crictl logs --tail 50 --follow ${CONTAINER_ID}

# Pull the container's PID and enter its network namespace directly
CONTAINER_PID=$(sudo crictl inspect ${CONTAINER_ID} | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['info']['pid'])")

# Now run ip commands inside the pod's network namespace
sudo nsenter -t ${CONTAINER_PID} -n -- ip addr show
sudo nsenter -t ${CONTAINER_PID} -n -- ip route show
sudo nsenter -t ${CONTAINER_PID} -n -- ss -tipm
```

Entering the pod's network namespace with `nsenter -n` is the most precise way to verify what a pod actually sees at the network layer, independent of kubectl exec, which routes through the API server and kubelet. Inside the namespace you will see the `veth` peer address, the pod's own IP, and the default gateway, which should always be a link-local address (`169.254.1.1`) served by the VPC CNI's `aws-cni-support` ARP proxy.

### 1.4 Socket State and Connection Tracking

The `ss` utility reads kernel socket state from the netlink socket directly, bypassing `/proc/net/tcp` and offering substantially lower overhead at scale. For a production EKS node handling hundreds of pods, understanding socket distribution across TIME_WAIT, ESTABLISHED, CLOSE_WAIT, and LISTEN states reveals connection leak patterns, misconfigured keepalive timers, and load balancer health-check overhead:

```bash
# From within the api-server pod's network namespace (continuing from above)
sudo nsenter -t ${CONTAINER_PID} -n -- ss -tipm state established

# Summarized socket counts by state across the entire node (outside namespaces)
ss -s

# Detailed TCP socket table — show timers, retransmits, RTT, and buffer usage
ss -tipm 'sport = :80 or dport = :80'

# Check for CLOSE_WAIT accumulation — a classic sign of the application not closing sockets
ss -tn state close-wait | wc -l

# TIME_WAIT count — elevated under high short-connection rates from NLB health checks
ss -tn state time-wait | wc -l

# Full connection detail for the Redis port
ss -tipm 'dport = :6379' 
```

The `ti` flags on `ss` produce the per-socket TCP info struct, which includes `rto` (retransmission timeout), `rtt` (smoothed round-trip time), `ato` (delayed ACK timeout), `cwnd` (congestion window in segments), and `retrans` (outstanding retransmit count). An `rtt` above 1ms on a same-AZ pod-to-pod connection signals either ENI contention, CPU steal time on a noisy-neighbor instance, or a cgroups networking throttle.

---

## Exercise 2: Benchmarking & Saturation Profiling

Saturation is the condition where a resource has work queued because demand exceeds its throughput. In an EKS cluster, saturation manifests in four primary locations: CPU cgroup throttling inside containers, memory pressure causing OOM kills or swap reclaim, ENI bandwidth exhaustion on the node NIC, and kube-apiserver request queuing when admission webhooks or large list operations saturate the control plane's goroutine pool. This exercise instruments all four.

### 2.1 CPU cgroup Throttling Analysis

The Linux CFS bandwidth controller enforces CPU limits by accounting CPU time in quota periods (default 100ms). When a container's `limits.cpu` is `1000m`, it may consume 100ms of CPU per 100ms period. If the application bursts past this within the period, the kernel throttles the cgroup until the next period begins. This is entirely invisible from inside the container — the process simply stops being scheduled — but it shows up clearly in cgroup statistics and in `perf`:

```bash
# On the worker node, find the cgroup path for the api-server container
API_POD=$(kubectl get pod -n lab-workload -l app=api-server -o jsonpath='{.items[0].metadata.name}')
API_CONTAINER_ID=$(kubectl get pod -n lab-workload ${API_POD} \
  -o jsonpath='{.status.containerStatuses[?(@.name=="api")].containerID}' | \
  sed 's|containerd://||')

# Navigate to the cgroup directory (cgroup v2 on AL2023)
CGROUP_PATH="/sys/fs/cgroup/kubepods.slice"
find ${CGROUP_PATH} -name "cpu.stat" | \
  xargs -I{} bash -c 'echo "=== {} ===" && cat {}'

# For the specific container:
CONTAINER_CGROUP=$(find /sys/fs/cgroup -name "*.scope" | \
  grep "${API_CONTAINER_ID:0:12}" | head -1 | xargs dirname)

watch -n 1 "cat ${CONTAINER_CGROUP}/cpu.stat"
```

The `cpu.stat` file reports `throttled_usec` cumulatively. Scrape it twice with a one-second interval and compute the delta to get per-second throttle time. A ratio of `throttled_usec / (nr_periods * period_duration_usec)` above 25% means your CPU limit is undersized for the workload's burst profile:

```bash
# Generate CPU load to trigger throttling, then observe
kubectl exec -n lab-workload ${API_POD} -c api -- \
  sh -c "for i in \$(seq 1 4); do dd if=/dev/urandom bs=1M count=100 | md5sum & done; wait"

# Concurrently, on the node, watch the throttle counter climb
CGROUP_CPU_STAT="${CONTAINER_CGROUP}/cpu.stat"
prev_throttled=0
for i in $(seq 1 10); do
  sleep 1
  curr=$(grep throttled_usec ${CGROUP_CPU_STAT} | awk '{print $2}')
  delta=$((curr - prev_throttled))
  echo "$(date +%T)  throttled_usec delta/s: ${delta}"
  prev_throttled=${curr}
done
```

Instrument the CPU scheduler directly with `perf stat` to measure IPC (instructions per clock), cache miss rates, and context switch frequency for the container's PID tree:

```bash
# perf stat on the entire cgroup (requires perf with cgroup support)
sudo perf stat -a --cgroup ${CONTAINER_CGROUP} \
  -e cycles,instructions,cache-misses,cache-references,context-switches \
  -- sleep 10

# If cgroup-based perf is unavailable, attach to the container PID directly
sudo perf stat -p ${CONTAINER_PID} \
  -e cycles,instructions,cache-misses,cache-references \
  -- sleep 5
```

### 2.2 Memory Pressure and OOM Analysis

EKS containers are OOM-killed by the kernel when their cgroup memory usage reaches `limits.memory`. The sequence is: the allocator calls `kmalloc` or `mmap`, the cgroup memory counter increments, the kernel checks the limit, finds it exceeded, invokes the OOM killer, selects the highest `oom_score_adj` process within the cgroup, and sends `SIGKILL`. The kubelet then observes the container's exit code `137` (128 + SIGKILL) and reports `OOMKilled: true` in the pod's `containerStatuses`:

```bash
# Check for recent OOM kills in the cluster
kubectl get pods -A --field-selector=status.phase=Failed | \
  grep -i oom

kubectl get events -A --field-selector=reason=OOMKilling

# On the node, the kernel also records OOM kills in dmesg
sudo dmesg --ctime | grep -i "killed process\|oom_kill\|out of memory"

# Real-time memory usage for the container cgroup
watch -n 1 "cat ${CONTAINER_CGROUP}/memory.current && \
            echo 'limit:' && cat ${CONTAINER_CGROUP}/memory.max && \
            echo 'swap:' && cat ${CONTAINER_CGROUP}/memory.swap.current"

# Memory stat breakdown — anon, file, shmem, kernel, sock
cat ${CONTAINER_CGROUP}/memory.stat
```

Apply controlled memory pressure to observe the OOM kill lifecycle and measure recovery time. This requires temporarily reducing the api-server's memory limit, which we do via a patch that triggers a rolling update:

```bash
# Save original limit
ORIGINAL_LIMIT=$(kubectl get deployment -n lab-workload api-server \
  -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}')
echo "Original: ${ORIGINAL_LIMIT}"

# Patch down the memory limit to force OOM under load
kubectl patch deployment -n lab-workload api-server --type=json -p='[
  {"op": "replace",
   "path": "/spec/template/spec/containers/0/resources/limits/memory",
   "value": "32Mi"}
]'

# Wait for rollout, then generate allocation pressure
kubectl -n lab-workload rollout status deployment/api-server --timeout=60s

# Record the timestamp and watch for OOMKill
START=$(date +%s)
kubectl get events -n lab-workload --watch &
WATCH_PID=$!

# Allocate memory inside the container until it is killed
NEW_POD=$(kubectl get pod -n lab-workload -l app=api-server \
  -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n lab-workload ${NEW_POD} -c api -- \
  sh -c "cat /dev/zero | head -c 40M > /dev/null" 2>&1 || true

KILL_TIME=$(date +%s)
echo "OOM kill latency: $((KILL_TIME - START))s"
kill ${WATCH_PID} 2>/dev/null

# Confirm exit reason
kubectl get pod -n lab-workload ${NEW_POD} \
  -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'

# Restore original limit
kubectl patch deployment -n lab-workload api-server --type=json -p="[
  {\"op\": \"replace\",
   \"path\": \"/spec/template/spec/containers/0/resources/limits/memory\",
   \"value\": \"${ORIGINAL_LIMIT}\"}
]"
kubectl -n lab-workload rollout status deployment/api-server --timeout=90s
```

### 2.3 Network Bandwidth Saturation and ENI Throughput

Each EC2 instance type has a documented network bandwidth ceiling. A `m5.xlarge` provides a baseline of 2.5 Gbps with burst to 10 Gbps, managed by the ENA driver's token bucket. When a node runs many pods generating aggregate traffic near this ceiling, you will observe increased `retrans` values in `ss -ti`, elevated `ethtool -S` drop counters, and degraded pod-to-pod latency even though no individual pod appears to have breached a limit. The node-level NIC is the shared bottleneck:

```bash
# Install iperf3 if not present
sudo apt-get install -y iperf3

# Launch an iperf3 server pod
kubectl apply -n lab-workload -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: iperf-server
  namespace: lab-workload
  labels:
    app: iperf-server
spec:
  containers:
  - name: iperf
    image: networkstatic/iperf3:latest
    command: ["iperf3", "-s", "-p", "5201"]
    ports:
    - containerPort: 5201
    resources:
      requests:
        cpu: "500m"
        memory: "128Mi"
      limits:
        cpu: "2000m"
        memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: iperf-server
  namespace: lab-workload
spec:
  selector:
    app: iperf-server
  ports:
  - port: 5201
    targetPort: 5201
EOF

kubectl -n lab-workload wait --for=condition=Ready pod/iperf-server --timeout=60s

# Launch an iperf3 client and saturate the path
kubectl run iperf-client --rm -it --restart=Never \
  --namespace=lab-workload \
  --image=networkstatic/iperf3:latest \
  -- iperf3 -c iperf-server -p 5201 -t 30 -P 8 --get-server-output
```

While iperf3 runs, instrument the node's NIC in a parallel terminal:

```bash
# On the worker node — sample NIC counters at 1-second intervals
while true; do
  date +%T
  ip -s link show eth0 | grep -A 2 "RX:\|TX:"
  sudo ethtool -S eth0 | grep -E "(tx_bytes|rx_bytes|bw_in_allowance|bw_out_allowance|conntrack_allowance|linklocal_allowance|pps_allowance)" 
  echo "---"
  sleep 1
done
```

The `bw_in_allowance_exceeded`, `bw_out_allowance_exceeded`, and `pps_allowance_exceeded` counters in the ENA driver statistics are the definitive signal for EC2 network throttling. Any non-zero delta on these counters during your workload confirms that the instance type is network-bound and must be scaled up or the workload must be rebalanced across more nodes.

```bash
# Compute per-second bandwidth from ip -s link counters
prev_rx=0; prev_tx=0
while true; do
  stats=$(ip -s link show eth0 | grep -A 1 "RX:" | tail -1)
  rx=$(echo $stats | awk '{print $1}')
  tx_stats=$(ip -s link show eth0 | grep -A 1 "TX:" | tail -1)
  tx=$(echo $tx_stats | awk '{print $1}')
  if [ ${prev_rx} -ne 0 ]; then
    rx_mbps=$(( (rx - prev_rx) * 8 / 1024 / 1024 ))
    tx_mbps=$(( (tx - prev_tx) * 8 / 1024 / 1024 ))
    echo "$(date +%T)  RX: ${rx_mbps} Mbps  TX: ${tx_mbps} Mbps"
  fi
  prev_rx=${rx}; prev_tx=${tx}
  sleep 1
done
```

### 2.4 Kubernetes API Server Saturation

The managed EKS control plane's API server runs behind a rate limiter. Each client (kubelet, kube-controller-manager, cluster-autoscaler, your CI tooling) is subject to per-verb and per-resource priority and fairness (APF) queuing. When the API server is saturated, `kubectl` commands return `HTTP 429 Too Many Requests` or stall for seconds at a time. This is detectable by watching the latency histogram exposed on the metrics endpoint:

```bash
# Check if metrics-server is installed (required for HPA and kubectl top)
kubectl get deployment -n kube-system metrics-server

# If not, install via Helm
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm upgrade --install metrics-server metrics-server/metrics-server \
  --namespace kube-system \
  --set args="{--kubelet-insecure-tls}"

# Node and pod resource usage snapshot
kubectl top nodes
kubectl top pods -n lab-workload --sort-by=cpu

# Simulate API server load — 50 parallel kubectl list operations
for i in $(seq 1 50); do
  kubectl get pods -A &
done
time wait

# Measure API server latency under load
time kubectl get pods -A -o json > /dev/null
```

If you have Prometheus deployed in the cluster (via kube-prometheus-stack), the most precise saturation signal comes from the `apiserver_request_duration_seconds` histogram and `apiserver_flowcontrol_request_concurrency_in_use` gauge:

```bash
# Deploy kube-prometheus-stack if not present
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.enabled=true \
  --set alertmanager.enabled=false \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Port-forward Prometheus and query
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &

# Query API server p99 latency
curl -sG 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb!="WATCH"}[5m])) by (le, verb, resource))' | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data['data']['result']:
  m = r['metric']
  v = float(r['value'][1])
  if v > 0.5:
    print(f\"verb={m.get('verb')} resource={m.get('resource')} p99={v:.3f}s  *** HIGH ***\")
  else:
    print(f\"verb={m.get('verb')} resource={m.get('resource')} p99={v:.3f}s\")
"
```

---

## Exercise 3: Fault Injection & Recovery Analysis

The recovery path of a distributed system reveals its true architecture far more accurately than its nominal path. This exercise injects four categories of fault — node failure, CNI disruption, control-plane connectivity loss, and pod crash-loop — and instruments the detection, propagation, and remediation timing for each. The goal is to build a precise empirical model of your cluster's MTTR (mean time to recovery) under each failure class so that you can set SLOs that match the system's actual behavior rather than its theoretical guarantees.

### 3.1 Pod Crash-Loop: Detection and Restart Timing

The simplest fault is a container that exits non-zero. The kubelet detects the exit via its CRI watch on the containerd event stream, records the exit code and timestamp, computes the next restart delay using exponential backoff (10s, 20s, 40s, 80s, 160s, capped at 300s), and updates the pod status object in the API server. During each backoff window, the pod's status is `CrashLoopBackOff`, which means no traffic reaches it and its IP remains in the endpoint slice (a critical correctness issue: the VPC CNI does not remove an IP from the endpoint until the pod's `Ready` condition becomes false, which only happens after the first failed liveness probe):

```bash
# Inject a crash loop — override the api-server command to exit immediately
kubectl patch deployment -n lab-workload api-server --type=json -p='[
  {"op": "add",
   "path": "/spec/template/spec/containers/0/command",
   "value": ["/bin/sh", "-c", "echo crashing && exit 1"]}
]'

# Watch events stream in real time
kubectl get events -n lab-workload \
  --watch \
  --field-selector involvedObject.kind=Pod &
EVENTS_PID=$!

# Measure restart timing
kubectl get pods -n lab-workload -l app=api-server --watch &
PODS_PID=$!

sleep 90

kill ${EVENTS_PID} ${PODS_PID} 2>/dev/null

# Check backoff state
kubectl describe pod -n lab-workload \
  $(kubectl get pod -n lab-workload -l app=api-server -o jsonpath='{.items[0].metadata.name}') | \
  grep -E "(Restart Count|Last State|Back-off)"

# Restore deployment
kubectl patch deployment -n lab-workload api-server --type=json -p='[
  {"op": "remove", "path": "/spec/template/spec/containers/0/command"}
]'
kubectl -n lab-workload rollout status deployment/api-server --timeout=120s
```

Track the precise restart sequence using `strace` on the kubelet process to observe the CRI call that triggers each restart:

```bash
# On the worker node — attach strace to the kubelet
KUBELET_PID=$(pgrep kubelet)
sudo strace -p ${KUBELET_PID} \
  -e trace=read,write,sendto,recvfrom \
  -f -s 256 2>&1 | \
  grep -E "(containerd|CRI|RunPodSandbox|CreateContainer)" | \
  head -40
```

### 3.2 Node Failure Simulation: Cordon, Drain, and Pod Rescheduling

A node failure in EKS manifests as a loss of kubelet heartbeats to the API server. The node controller waits `node-monitor-grace-period` (default 40s) before marking the node `NotReady`, then waits `pod-eviction-timeout` (default 5 minutes in vanilla Kubernetes, reduced to 2 minutes in EKS with the Node Problem Detector and eviction manager) before evicting pods. During this window, pods on the failed node continue to show as `Running` in the API server — a stale cache state — while their actual workload has halted:

```bash
# Select a worker node and cordon it (marks it unschedulable without evicting)
TARGET_NODE=$(kubectl get nodes \
  --selector=!node-role.kubernetes.io/master \
  -o jsonpath='{.items[1].metadata.name}')

echo "Target node: ${TARGET_NODE}"

# Record which pods are on this node
kubectl get pods -A --field-selector="spec.nodeName=${TARGET_NODE}" \
  -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phase"

# Cordon the node
kubectl cordon ${TARGET_NODE}

# Verify — node now shows SchedulingDisabled
kubectl get node ${TARGET_NODE}

# Drain the node — evict all pods with grace period
# PodDisruptionBudgets are respected; pods with no PDB are forcibly evicted after timeout
kubectl drain ${TARGET_NODE} \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=30 \
  --timeout=120s \
  --pod-selector='app notin (iperf-server)' \
  2>&1

# Watch rescheduling events
kubectl get pods -n lab-workload --watch &
WATCH_PID=$!
sleep 45
kill ${WATCH_PID}

# Confirm pods are rescheduled to remaining nodes
kubectl get pods -n lab-workload -o wide | grep api-server

# Uncordon the node to restore capacity
kubectl uncordon ${TARGET_NODE}
```

For a harder simulation, use SSM to stop the kubelet service on the node without terminating the instance, which produces a genuine `NotReady` condition without triggering an EC2 auto-scaling event. This reveals the full node-monitor-grace-period → eviction pipeline:

```bash
# Get instance ID for the target node
INSTANCE_ID=$(kubectl get node ${TARGET_NODE} \
  -o jsonpath='{.spec.providerID}' | awk -F'/' '{print $NF}')

# Stop kubelet via SSM Run Command
aws ssm send-command \
  --instance-ids "${INSTANCE_ID}" \
  --document-name "AWS-RunShellScript" \
  --parameters commands=["sudo systemctl stop kubelet"] \
  --region us-east-1

# Record start time and watch node condition
START_TS=$(date +%s)
while true; do
  CONDITION=$(kubectl get node ${TARGET_NODE} \
    -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
  ELAPSED=$(( $(date +%s) - START_TS ))
  echo "$(date +%T)  elapsed=${ELAPSED}s  Ready=${CONDITION}"
  if [ "${CONDITION}" = "False" ] || [ "${CONDITION}" = "Unknown" ]; then
    echo "NODE MARKED NOT-READY after ${ELAPSED} seconds"
    break
  fi
  sleep 2
done

# Watch pod eviction after node-monitor-grace-period
kubectl get pods -n lab-workload --watch &
WATCH_PID=$!
sleep 180
kill ${WATCH_PID}

# Restart kubelet to restore the node
aws ssm send-command \
  --instance-ids "${INSTANCE_ID}" \
  --document-name "AWS-RunShellScript" \
  --parameters commands=["sudo systemctl start kubelet"] \
  --region us-east-1

# Wait for node to rejoin
kubectl wait --for=condition=Ready node/${TARGET_NODE} --timeout=120s
```

### 3.3 CNI Fault Injection: ENI IP Exhaustion and aws-node Recovery

The AWS VPC CNI plugin runs as a DaemonSet (`aws-node`) on each worker node. It maintains a warm pool of pre-allocated secondary IP addresses on each ENI so that pod startup does not require a synchronous EC2 `AssignPrivateIpAddresses` API call. If the warm pool is exhausted (high pod churn, undersized instance with limited ENI slots) or if the `aws-node` pod itself crashes, new pods will be stuck in `ContainerCreating` with the error `failed to assign an IP address to container`:

```bash
# Inspect aws-node DaemonSet health
kubectl get pods -n kube-system -l k8s-app=aws-node -o wide
kubectl describe daemonset -n kube-system aws-node | \
  grep -E "(Desired|Ready|Available|Image:)"

# Check aws-node logs for IP allocation errors
AWS_NODE_POD=$(kubectl get pods -n kube-system -l k8s-app=aws-node \
  --field-selector="spec.nodeName=${TARGET_NODE}" \
  -o jsonpath='{.items[0].metadata.name}')

kubectl logs -n kube-system ${AWS_NODE_POD} --tail=100 | \
  grep -E "(error|WARN|failed|ENI|IP|assign|warm)"

# Inspect the ipamd state directly via its local gRPC debug endpoint
# (requires being on the node or having port-forward to the node)
kubectl exec -n kube-system ${AWS_NODE_POD} -- \
  curl -s http://localhost:61678/v1/enis | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for eni_id, eni_info in data.items():
    total = len(eni_info.get('IPv4Addresses', {}))
    assigned = sum(1 for v in eni_info.get('IPv4Addresses', {}).values() if v.get('Assigned'))
    print(f'ENI: {eni_id}  total_IPs={total}  assigned={assigned}  free={total-assigned}')
"

# Simulate IP exhaustion by deploying a large number of pods rapidly
kubectl apply -n lab-workload -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ip-exhauster
  namespace: lab-workload
spec:
  replicas: 50
  selector:
    matchLabels:
      app: ip-exhauster
  template:
    metadata:
      labels:
        app: ip-exhauster
    spec:
      containers:
      - name: pause
        image: 602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/pause:3.5
        resources:
          requests:
            cpu: "10m"
            memory: "16Mi"
          limits:
            cpu: "50m"
            memory: "32Mi"
EOF

# Observe allocation failures
kubectl get events -n lab-workload --watch | grep -i "failed\|IP\|CNI" &
EVENTS_PID=$!

# Check how many pods are stuck in ContainerCreating
sleep 30
kubectl get pods -n lab-workload | grep ContainerCreating | wc -l

kill ${EVENTS_PID} 2>/dev/null

# Clean up the exhauster
kubectl delete deployment -n lab-workload ip-exhauster

# Force aws-node to reconcile its warm pool
kubectl rollout restart daemonset -n kube-system aws-node
kubectl rollout status daemonset -n kube-system aws-node --timeout=120s
```

### 3.4 tcpdump-Based Network Fault Tracing

When pod-to-pod connectivity fails silently — no kernel error, no application log, just timeouts — the most reliable diagnostic is to capture the actual packet exchange at the veth level on the sending node. The VPC CNI routes traffic through the host network namespace, so capturing on the veth pair of the source pod captures both directions of the flow before any iptables or eBPF manipulation:

```bash
# Identify the veth interface for the api-server pod
API_POD_IP=$(kubectl get pod -n lab-workload \
  $(kubectl get pod -n lab-workload -l app=api-server \
    -o jsonpath='{.items[0].metadata.name}') \
  -o jsonpath='{.status.podIP}')

echo "api-server pod IP: ${API_POD_IP}"

# On the worker node hosting this pod, find its veth peer
# The VPC CNI names veth interfaces as "eniXXX" or routes them via a veth
ip route show | grep "${API_POD_IP}"
VETH_IFACE=$(ip route show | grep "${API_POD_IP}" | awk '{print $3}')

echo "veth interface: ${VETH_IFACE}"

# Capture all traffic to/from this pod with full packet content
sudo tcpdump -i ${VETH_IFACE} \
  -n \
  -s 0 \
  -w /tmp/pod-capture.pcap \
  host ${API_POD_IP} &
TCPDUMP_PID=$!

# Generate traffic to the pod (from another pod in the same namespace)
kubectl run curl-test --rm -it --restart=Never \
  --namespace=lab-workload \
  --image=curlimages/curl:8.5.0 \
  -- curl -v --connect-timeout 5 http://${API_POD_IP}/

sleep 2
sudo kill ${TCPDUMP_PID}

# Analyze the capture — look for SYN, SYN-ACK, RST sequences
sudo tcpdump -r /tmp/pod-capture.pcap \
  -n \
  -q \
  'tcp[tcpflags] & (tcp-syn|tcp-rst|tcp-fin) != 0'

# Count retransmissions
sudo tcpdump -r /tmp/pod-capture.pcap -n | \
  awk '/retransmission|dup ack/ {count++} END {print "Retransmissions:", count}'
```

For connectivity faults caused by security group rules (which are enforced at the ENI hardware level, below the kernel's visibility), `tcpdump` will show SYN packets leaving the veth with no SYN-ACK returning. This distinguishes a security-group-level drop from an application-level rejection (`RST`), a DNS resolution failure (which would show UDP to port 53 with no response), or a routing misconfiguration (which would show ICMP unreachable from the gateway).

---

## Diagnostic Cheat Sheet & Verification Checklist

This reference consolidates every command from the exercises into a structured runbook. Organize your diagnostic sessions by working top-down from the control plane through the data plane to the kernel, so that each layer's output informs the hypothesis you bring to the next.

### Control Plane Health

| Diagnostic Goal | Command |
|---|---|
| API server reachability and version | `kubectl cluster-info && kubectl version` |
| Node conditions (Ready, MemoryPressure, DiskPressure, PIDPressure) | `kubectl get nodes -o custom-columns="NAME:.metadata.name,STATUS:.status.conditions[-1].type,REASON:.status.conditions[-1].reason"` |
| All pods across all namespaces with node placement | `kubectl get pods -A -o wide` |
| Deployment rollout status | `kubectl rollout status deployment/<name> -n <ns>` |
| Pod restart counts and OOMKill flag | `kubectl get pods -n <ns> -o custom-columns="NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,OOM:.status.containerStatuses[0].lastState.terminated.reason"` |
| Recent events sorted by timestamp | `kubectl get events -A --sort-by='.lastTimestamp'` |
| EndpointSlice readiness for a service | `kubectl get endpointslices -n <ns> -l kubernetes.io/service-name=<svc> -o yaml` |
| API request latency (verbose) | `kubectl get pods -A --v=6 2>&1 \| grep round_trip` |
| Node resource allocation pressure | `kubectl describe nodes \| grep -A 5 "Allocated resources:"` |

### Container Runtime (crictl)

| Diagnostic Goal | Command |
|---|---|
| List all pods in containerd | `sudo crictl pods` |
| List all containers with state | `sudo crictl ps -a` |
| Inspect container PID and namespaces | `sudo crictl inspect <container-id> \| python3 -c "import sys,json; d=json.load(sys.stdin); print('PID:', d['info']['pid'])"` |
| Container logs | `sudo crictl logs --tail 100 <container-id>` |
| Pull image manually | `sudo crictl pull <image>` |
| Remove a stopped container | `sudo crictl rm <container-id>` |

### Node Network Layer

| Diagnostic Goal | Command |
|---|---|
| All interfaces with traffic counters | `ip -s link show` |
| Full routing table including policy tables | `ip route show table all` |
| Policy routing rules (per-ENI routes) | `ip rule show` |
| Socket summary by state | `ss -s` |
| TCP sockets with RTT, cwnd, retransmit | `ss -tipm 'dport = :80'` |
| CLOSE_WAIT accumulation count | `ss -tn state close-wait \| wc -l` |
| TIME_WAIT count | `ss -tn state time-wait \| wc -l` |
| NIC driver and firmware version | `sudo ethtool -i eth0` |
| NIC ring buffer sizes | `sudo ethtool -g eth0` |
| NIC offload features | `sudo ethtool -k eth0` |
| NIC statistics (drops, errors) | `sudo ethtool -S eth0 \| grep -E "(error\|drop\|miss\|allowance)"` |
| Live packet capture on pod veth | `sudo tcpdump -i <veth> -n -s 0 host <pod-ip>` |

### cgroup Resource Inspection

| Diagnostic Goal | Command |
|---|---|
| CPU throttle state | `cat /sys/fs/cgroup/kubepods.slice/.../cpu.stat` |
| Memory current usage | `cat /sys/fs/cgroup/kubepods.slice/.../memory.current` |
| Memory hard limit | `cat /sys/fs/cgroup/kubepods.slice/.../memory.max` |
| Memory stat breakdown | `cat /sys/fs/cgroup/kubepods.slice/.../memory.stat` |
| CPU performance counters on container | `sudo perf stat -p <container-pid> -e cycles,instructions,cache-misses -- sleep 5` |
| OOM kills in kernel log | `sudo dmesg --ctime \| grep -i "oom_kill\|killed process"` |

### VPC CNI and ENI Diagnostics

| Diagnostic Goal | Command |
|---|---|
| aws-node DaemonSet pod health | `kubectl get pods -n kube-system -l k8s-app=aws-node -o wide` |
| aws-node logs for IP allocation errors | `kubectl logs -n kube-system <aws-node-pod> --tail=200 \| grep -iE "(error\|fail\|warm\|ENI)"` |
| ipamd ENI and IP pool state | `kubectl exec -n kube-system <aws-node-pod> -- curl -s http://localhost:61678/v1/enis` |
| Pods stuck in ContainerCreating | `kubectl get pods -A \| grep ContainerCreating` |
| CNI configuration on node | `cat /etc/cni/net.d/10-aws.conflist` |
| IP route for a specific pod IP | `ip route get <pod-ip>` |

### Recovery and Rollout Verification Checklist

Work through this checklist in sequence after any fault injection or production incident before declaring a service healthy:

1. All target pods report `STATUS=Running` and `READY=N/N` with zero recent restarts: `kubectl get pods -n <ns> -o wide`
2. No pod shows `OOMKilled` in its last-state terminated reason: `kubectl get pods -n <ns> -o custom-columns="NAME:.metadata.name,LAST_REASON:.status.containerStatuses[0].lastState.terminated.reason"`
3. All pod IPs appear in their service's EndpointSlice with `ready=true`: `kubectl get endpointslices -n <ns> -o yaml`
4. Node remains in `Ready` state with no `MemoryPressure` or `DiskPressure` conditions: `kubectl get nodes`
5. CPU throttle delta is below 25% over a 60-second window: check `cpu.stat` → `throttled_usec` delta
6. ENA allowance counters show zero per-second increments: `sudo ethtool -S eth0 | grep allowance_exceeded`
7. No CLOSE_WAIT sockets accumulating beyond baseline: `ss -tn state close-wait | wc -l`
8. aws-node pod logs contain no IP assignment errors in the last 10 minutes: `kubectl logs -n kube-system <aws-node-pod> --since=10m | grep -ci error`
9. Deployment rollout reports `successfully rolled out`: `kubectl rollout status deployment/<name> -n <ns>`
10. `kubectl top nodes` shows all nodes below 80% CPU and 80% memory allocatable consumption: `kubectl top nodes`

The diagnostic discipline these labs encode is iterative and evidence-driven: begin at the control plane's view of object state, descend to the runtime's view of container state, then descend further to the kernel's view of socket and cgroup state, and finally descend to the wire with tcpdump when all higher layers look nominal. EKS does not hide complexity — it moves the control plane management boundary. The kernel, the ENI, and the cgroup are still entirely yours to instrument.
