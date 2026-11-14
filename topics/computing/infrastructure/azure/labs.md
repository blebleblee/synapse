# Operational Verification Labs: Azure

## Objective & Environment Setup

This guide arms you with the diagnostic precision of a staff-level infrastructure engineer operating AKS-backed workloads on Azure. Every exercise uses real tooling against a live environment: no mocked outputs, no placeholder commands, no handwavy abstractions. You will verify the actual state of a running Azure Kubernetes Service cluster, its underlying node operating system, and the network fabric that connects it — using the same instruments you would reach for during a production incident at 2 AM.

The mental model underpinning all Azure infrastructure verification is the layered state machine. At the bottom sits the Azure fabric controller, which manages hypervisor placement, SR-IOV NIC provisioning, and disk I/O scheduling on the host. Above that, the AKS node pool runs Ubuntu 22.04 (or Azure Linux 2.0) with `containerd` as the CRI, `kubelet` as the node agent, and `kube-proxy` or Cilium as the dataplane. At the top, your workload Pods live inside Linux cgroups v2 hierarchies and network namespaces that are anchored by the pause container's infra namespace. When something breaks, you traverse this stack from top to bottom: the control plane API first, then the node OS, then the kernel data structures.

### Environment Provisioning

You need an AKS cluster with at least two nodes in the system pool and one user node pool. Run the following to create a reproducible lab environment. Set your subscription and resource group first:

```bash
az account set --subscription "your-subscription-id"
az group create --name aks-lab-rg --location eastus2

az aks create \
  --resource-group aks-lab-rg \
  --name aks-lab-cluster \
  --node-count 2 \
  --node-vm-size Standard_D4s_v5 \
  --os-sku Ubuntu \
  --network-plugin azure \
  --network-policy calico \
  --enable-managed-identity \
  --enable-addons monitoring \
  --workspace-resource-id "" \
  --generate-ssh-keys \
  --kubernetes-version 1.29.2

az aks get-credentials \
  --resource-group aks-lab-rg \
  --name aks-lab-cluster \
  --overwrite-existing
```

Install the full diagnostic toolchain on your workstation. On Ubuntu 22.04:

```bash
sudo apt-get update && sudo apt-get install -y \
  iproute2 \
  ethtool \
  tcpdump \
  linux-tools-$(uname -r) \
  linux-tools-generic \
  bpftool \
  nmap \
  netcat-openbsd \
  jq \
  curl

# Install kubectl if not present
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install crictl (matches your cluster's CRI version)
VERSION="v1.29.0"
curl -LO https://github.com/kubernetes-sigs/cri-tools/releases/download/${VERSION}/crictl-${VERSION}-linux-amd64.tar.gz
tar -C /usr/local/bin -xzf crictl-${VERSION}-linux-amd64.tar.gz
rm crictl-${VERSION}-linux-amd64.tar.gz

# Install Azure CLI if not present
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

Deploy a reference workload that will serve as your diagnostic target throughout all three exercises. This manifest creates a Deployment, a ClusterIP Service, and a stress-capable debug DaemonSet:

```yaml
# reference-workload.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-lab
  namespace: default
  labels:
    app: nginx-lab
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx-lab
  template:
    metadata:
      labels:
        app: nginx-lab
    spec:
      containers:
      - name: nginx
        image: nginx:1.25.3
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "250m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-lab-svc
  namespace: default
spec:
  selector:
    app: nginx-lab
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: diag-node
  namespace: kube-system
  labels:
    app: diag-node
spec:
  selector:
    matchLabels:
      app: diag-node
  template:
    metadata:
      labels:
        app: diag-node
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
      - operator: Exists
      containers:
      - name: diag
        image: nicolaka/netshoot:v0.11
        command: ["sleep", "infinity"]
        securityContext:
          privileged: true
        volumeMounts:
        - name: host-proc
          mountPath: /host/proc
          readOnly: true
        - name: host-sys
          mountPath: /host/sys
          readOnly: true
        - name: host-run
          mountPath: /run
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
      volumes:
      - name: host-proc
        hostPath:
          path: /proc
      - name: host-sys
        hostPath:
          path: /sys
      - name: host-run
        hostPath:
          path: /run
```

Apply and verify:

```bash
kubectl apply -f reference-workload.yaml
kubectl rollout status deployment/nginx-lab --timeout=120s
kubectl get pods -A -o wide
```

---

## Exercise 1: Live State & Internal Subsystem Inspection

### 1.1 Control Plane API State Verification

The Kubernetes API server is the authoritative source of cluster truth, but its responses reflect the desired state stored in etcd — not necessarily what is running on nodes at this instant. Your first discipline is learning to distinguish **spec** (desired) from **status** (observed), and **observed** from **actual kernel state**. These three layers can diverge silently, and every serious incident stems from a gap between them.

Begin with a full cluster snapshot. The `-o wide` flag on `kubectl get pods` surfaces the node assignment and Pod IP, which you will cross-reference against the network namespace state on the node itself:

```bash
# Full cluster snapshot: all Pods, their IPs, nodes, and status
kubectl get pods -A -o wide

# Identify which nodes your nginx-lab Pods landed on
kubectl get pods -n default -l app=nginx-lab \
  -o custom-columns="NAME:.metadata.name,NODE:.spec.nodeName,IP:.status.podIP,PHASE:.status.phase"

# Inspect a single Pod's full status object — pay attention to conditions
POD=$(kubectl get pod -l app=nginx-lab -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod $POD

# Surface the conditions array explicitly — Ready, Initialized, ContainersReady, PodScheduled
kubectl get pod $POD -o jsonpath='{range .status.conditions[*]}{.type}{"\t"}{.status}{"\t"}{.lastTransitionTime}{"\n"}{end}'
```

The `conditions` array is your primary signal. `PodScheduled=True` confirms the scheduler wrote a binding to etcd and the node was available. `Initialized=True` confirms all init containers ran to completion. `ContainersReady=True` and `Ready=True` confirm that the readiness probe passed and that this Pod endpoint has been enrolled in the Service's EndpointSlice. When a Pod shows `Running` phase but `Ready=False`, its IP is **not** present in the EndpointSlice, meaning kube-proxy has not installed the iptables rule that would route Service traffic to it. This is a common source of partial traffic loss that never surfaces as an outright crash.

Verify the EndpointSlice registration directly:

```bash
# Confirm Pod IPs are enrolled in the Service's EndpointSlice
kubectl get endpointslice -n default -l kubernetes.io/service-name=nginx-lab-svc -o yaml

# Check whether iptables rules reflect the same IPs on a node
NODE=$(kubectl get pods -l app=nginx-lab -o jsonpath='{.items[0].spec.nodeName}')
DIAG_POD=$(kubectl get pod -n kube-system -l app=diag-node \
  --field-selector spec.nodeName=$NODE -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n kube-system $DIAG_POD -- iptables-save | grep nginx-lab-svc
```

The iptables output will show a chain named `KUBE-SVC-*` with individual `KUBE-SEP-*` (Service Endpoint) rules that DNAT traffic to each Pod IP. The number of `KUBE-SEP-*` rules must equal the number of `Ready` Pods. A mismatch here means kube-proxy's sync loop is behind, which you can verify with:

```bash
kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=50 | grep -E "syncProxyRules|error|warn"
```

### 1.2 Node OS and CRI Subsystem Inspection

SSH into one of the AKS nodes using the debug pod as a jump host, or use the `az aks command invoke` shortcut for read-only inspection. For full diagnostic access, use `kubectl debug`:

```bash
NODE=$(kubectl get pods -l app=nginx-lab -o jsonpath='{.items[0].spec.nodeName}')

# Open a privileged shell on the node via node debug pod
kubectl debug node/$NODE -it --image=ubuntu:22.04 -- bash
```

Inside the node debug shell, your first diagnostic target is the CRI. AKS uses `containerd` and you interact with it via `crictl`. Configure the endpoint and inspect running containers:

```bash
# Inside the node debug shell, set crictl runtime endpoint
export CONTAINER_RUNTIME_ENDPOINT=unix:///run/containerd/containerd.sock

# List all running pods on this node as the CRI sees them
crictl pods

# List all running containers — confirm nginx-lab containers are present
crictl ps

# Inspect a specific container's low-level state — get OCI config, cgroup path, PID
CONTAINER_ID=$(crictl ps --name nginx | awk 'NR==2{print $1}')
crictl inspect $CONTAINER_ID | jq '{
  pid: .info.pid,
  cgroupsPath: .info.runtimeSpec.linux.cgroupsPath,
  namespaces: [.info.runtimeSpec.linux.namespaces[].type],
  memoryLimit: .info.runtimeSpec.linux.resources.memory.limit,
  cpuQuota: .info.runtimeSpec.linux.resources.cpu.quota
}'
```

The `cgroupsPath` field reveals where this container lives in the cgroup hierarchy. On AKS nodes running cgroup v2, the path maps to `/sys/fs/cgroup/kubepods/burstable/pod<uid>/<container-id>/`. Verify the actual enforced limits versus what the Pod spec requested:

```bash
# Get the container PID from crictl inspect
PID=$(crictl inspect $CONTAINER_ID | jq '.info.pid')

# Read the enforced cgroup v2 memory limit
cat /sys/fs/cgroup/kubepods/burstable/pod*/$(echo $CONTAINER_ID)/memory.max

# Read the enforced CPU quota (in microseconds per 100ms period)
cat /sys/fs/cgroup/kubepods/burstable/pod*/$(echo $CONTAINER_ID)/cpu.max
# Output format: "quota period" — e.g., "50000 100000" means 50% of one CPU (500m)

# Verify actual memory usage right now
cat /sys/fs/cgroup/kubepods/burstable/pod*/$(echo $CONTAINER_ID)/memory.current
```

A CPU quota of `50000 100000` corresponds precisely to `500m` in the Pod spec: 50,000 microseconds out of every 100,000-microsecond period. This is how the kernel throttles a container that exceeds its CPU limit. If `memory.current` approaches `memory.max`, the kernel's OOM killer is imminent and you will see `OOMKilled` in the Pod's `lastState`.

### 1.3 Network Namespace and Interface Inspection

Each Pod gets its own network namespace, anchored by the pause container. The network interface inside the Pod namespace is a veth pair: one end lives in the Pod namespace and the other end lives in the root network namespace of the node, connected to the Azure CNI bridge or directly routed depending on the network plugin.

Find the veth peer for your nginx-lab Pod:

```bash
# Get the Pod's network namespace path via the pause container
PAUSE_ID=$(crictl ps --name pause | grep nginx-lab | awk '{print $1}')
# Pause containers are named "pause" in containerd
# Alternative: find via Pod UID
POD_UID=$(kubectl get pod $POD -o jsonpath='{.metadata.uid}')

# Enter the Pod's network namespace and read the interface index
nsenter --net=/proc/$PID/ns/net -- ip link show eth0
nsenter --net=/proc/$PID/ns/net -- ip addr show eth0
nsenter --net=/proc/$PID/ns/net -- ip route show

# The "if_index" field on eth0 inside the Pod tells you the peer's index on the host
PEER_INDEX=$(nsenter --net=/proc/$PID/ns/net -- ip link show eth0 | grep -o 'if[0-9]*' | tr -d 'if')
echo "Peer veth index on host: $PEER_INDEX"

# Find that interface on the host
ip link show | grep "^${PEER_INDEX}:"
```

Now use `ip -s link` to read the per-interface statistics on the host-side veth. These counters are the ground truth for packet flow — more reliable than any application-layer metric:

```bash
VETH=$(ip link show | grep "^${PEER_INDEX}:" | awk '{print $2}' | tr -d ':')
ip -s link show $VETH
```

The output shows `RX` and `TX` byte/packet counters, `errors`, `dropped`, and `overrun`. Nonzero `dropped` on RX indicates the kernel's socket receive buffer is saturating. Nonzero `errors` on TX indicates hardware-level issues on the veth or the underlying Azure VF (virtual function). On SR-IOV-enabled VM sizes (Standard_D4s_v5 uses accelerated networking), you can inspect the VF statistics directly:

```bash
# Check if accelerated networking VF is present
ethtool -i eth0 | grep driver
# Should show "hv_netvsc" or "mlx5_core" for SR-IOV

# Read ethtool statistics for the physical NIC
ethtool -S eth0 | grep -E "tx_|rx_|drop|error" | head -40

# Check ring buffer sizes — small rings cause drops under burst traffic
ethtool -g eth0
```

Use `ss -tipm` to inspect the state of all TCP sockets on the node at kernel depth. The `-t` flag selects TCP, `-i` shows internal TCP state (retransmits, RTT, send/receive window), `-p` shows the owning process, and `-m` shows socket memory usage:

```bash
# All TCP sockets with internal kernel state
ss -tipm

# Filter to connections involving the nginx Pod's IP
POD_IP=$(kubectl get pod $POD -o jsonpath='{.status.podIP}')
ss -tipm dst $POD_IP or src $POD_IP

# Check for sockets in TIME_WAIT (normal) versus CLOSE_WAIT (application bug)
ss -tan state time-wait | wc -l
ss -tan state close-wait | wc -l
```

A large number of `CLOSE_WAIT` sockets indicates the application received a FIN from the remote side but never called `close()` on the socket — a classic application-layer connection leak. `TIME_WAIT` accumulation is normal under high connection churn and resolves within 60 seconds via the kernel's MSL timer.

---

## Exercise 2: Benchmarking & Saturation Profiling

### 2.1 CPU Saturation: perf stat and CFS Throttling

The goal of CPU profiling on a Kubernetes node is not to find slow code — it is to verify that the kernel's CFS scheduler is distributing CPU time correctly across cgroup hierarchies, that your containers are not being throttled by the CPU quota enforcer, and that the system's hardware performance counters tell a consistent story.

Deploy a CPU-intensive workload to generate measurable load:

```bash
# Deploy a CPU stress Pod
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: cpu-stress
  namespace: default
spec:
  containers:
  - name: stress
    image: progrium/stress:latest
    args: ["--cpu", "2", "--timeout", "300s"]
    resources:
      requests:
        cpu: "500m"
        memory: "64Mi"
      limits:
        cpu: "1000m"
        memory: "128Mi"
EOF

kubectl wait --for=condition=Ready pod/cpu-stress --timeout=60s
NODE=$(kubectl get pod cpu-stress -o jsonpath='{.spec.nodeName}')
```

SSH into the node via the debug DaemonSet and run `perf stat` against the stress process for 10 seconds. `perf stat` reads hardware PMU counters directly — these are CPU register values, not estimates:

```bash
DIAG_POD=$(kubectl get pod -n kube-system -l app=diag-node \
  --field-selector spec.nodeName=$NODE -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n kube-system $DIAG_POD -- bash -c "
  STRESS_PID=\$(pgrep -f 'stress --cpu')
  perf stat -p \$STRESS_PID \
    -e cycles,instructions,cache-misses,cache-references,\
branch-misses,branch-instructions,\
task-clock,context-switches,cpu-migrations,page-faults \
    -- sleep 10 2>&1
"
```

Interpret the output by computing the Instructions Per Cycle (IPC): `instructions / cycles`. An IPC above 2.0 on a modern x86 Skylake-derived core (which Azure D-series uses) indicates efficient scalar execution. An IPC below 0.5 indicates memory-bound execution where the CPU is stalling waiting for data from DRAM. A high `cache-misses / cache-references` ratio (above 10%) confirms a memory bandwidth bottleneck.

Now measure whether the stress Pod's container is being throttled by the CFS quota enforcer. The kernel exposes this through the cgroup cpu controller's throttle statistics:

```bash
kubectl exec -n kube-system $DIAG_POD -- bash -c "
  POD_UID=\$(crictl pods --name cpu-stress --output json | jq -r '.items[0].id')
  CGROUP_PATH=\$(find /sys/fs/cgroup/kubepods -name 'cpu.stat' | xargs grep -l throttled_periods | head -1)
  
  # Sample throttle stats before and after 5 seconds
  echo '--- T=0 ---'
  cat \$CGROUP_PATH
  sleep 5
  echo '--- T=5 ---'
  cat \$CGROUP_PATH
"
```

The `throttled_periods` and `throttled_time` fields tell you how many 100ms scheduler periods the container was forced to pause. If `throttled_periods` grows by more than 20% of total `nr_periods` during your 5-second window, your container is severely CPU-limited and your p99 latency will be correspondingly unpredictable. The correct response is to either increase `resources.limits.cpu` or profile the application to reduce its CPU demand.

### 2.2 Memory Pressure and OOM Telemetry

Memory saturation on a Kubernetes node is more subtle than CPU saturation because the Linux kernel aggressively uses free physical RAM for page cache, and the OOM killer only fires when both anonymous memory (heap/stack) and swap are exhausted. The critical diagnostic signal is not "is memory usage high" but "is the kernel reclaiming pages under pressure, and from whose cgroup."

Deploy a memory stress Pod:

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: mem-stress
  namespace: default
spec:
  containers:
  - name: stress
    image: progrium/stress:latest
    args: ["--vm", "1", "--vm-bytes", "200M", "--timeout", "300s"]
    resources:
      requests:
        memory: "128Mi"
      limits:
        memory: "256Mi"
EOF
```

On the node, monitor the cgroup memory controller's pressure and working set:

```bash
kubectl exec -n kube-system $DIAG_POD -- bash -c "
  # Watch memory pressure stall information — a Linux kernel PSI metric
  # 'some' means at least one task was stalled waiting for memory
  # 'full' means all tasks were stalled (complete memory pressure)
  cat /proc/pressure/memory
  
  # Read node-level memory stats from /proc/meminfo
  grep -E 'MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree|Dirty|Writeback|Slab|KernelStack|PageTables|AnonPages|Mapped|Cached' /proc/meminfo

  # Find the mem-stress cgroup and read its current working set
  CGROUP=\$(find /sys/fs/cgroup/kubepods -name 'memory.current' | xargs grep -lv '^0$' | head -5)
  for c in \$CGROUP; do echo \$c: \$(cat \$c | numfmt --to=iec); done
"
```

The PSI (Pressure Stall Information) output from `/proc/pressure/memory` gives you three fields per line: `avg10`, `avg60`, `avg300` (exponentially weighted moving averages over 10s, 60s, and 300s windows) and `total` (cumulative stall time in microseconds). A `full avg10` above 5% means your node is experiencing serious memory contention that will cause p99 latency spikes across all Pods on the node — not just the one consuming memory. Azure Monitor can ingest PSI metrics via the Container Insights agent, but reading `/proc/pressure/memory` directly is the fastest ground-truth signal.

### 2.3 Network Throughput and Latency Benchmarking

Install `iperf3` into the lab namespace and run a bidirectional throughput test between two Pods on different nodes. This test validates that the Azure CNI data path is operating at its expected bandwidth and that the veth-to-physical-NIC path is not introducing unexpected overhead:

```bash
# Deploy iperf3 server on node 1
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: iperf3-server
  namespace: default
  labels:
    role: iperf3-server
spec:
  containers:
  - name: iperf3
    image: networkstatic/iperf3:latest
    args: ["-s"]
    ports:
    - containerPort: 5201
  nodeSelector:
    kubernetes.io/hostname: "REPLACE_WITH_NODE1_NAME"
EOF

# Deploy iperf3 client on node 2
NODE1=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
NODE2=$(kubectl get nodes -o jsonpath='{.items[1].metadata.name}')

# Patch nodeSelector for the server
kubectl patch pod iperf3-server --type=json \
  -p="[{\"op\":\"replace\",\"path\":\"/spec/nodeSelector/kubernetes.io~1hostname\",\"value\":\"$NODE1\"}]" 2>/dev/null || true

kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: iperf3-server
  namespace: default
spec:
  containers:
  - name: iperf3
    image: networkstatic/iperf3:latest
    args: ["-s"]
    ports:
    - containerPort: 5201
  nodeName: $NODE1
EOF

kubectl wait --for=condition=Ready pod/iperf3-server --timeout=60s
SERVER_IP=$(kubectl get pod iperf3-server -o jsonpath='{.status.podIP}')

# Run iperf3 client from node 2: 10 parallel streams, 30 seconds, with reverse mode
kubectl run iperf3-client \
  --image=networkstatic/iperf3:latest \
  --restart=Never \
  --overrides="{\"spec\":{\"nodeName\":\"$NODE2\"}}" \
  -- iperf3 -c $SERVER_IP -P 10 -t 30 -R

kubectl wait --for=condition=Ready pod/iperf3-client --timeout=60s
kubectl logs -f iperf3-client
```

A Standard_D4s_v5 with Accelerated Networking enabled should achieve approximately 8–10 Gbps cross-node throughput within the same Azure availability zone. If you observe less than 4 Gbps, the accelerated networking VF may not be active on one of the VMs. Verify with:

```bash
kubectl exec -n kube-system $DIAG_POD -- bash -c "
  # Check if accelerated networking is active — mlx5_core means SR-IOV VF
  ethtool -i eth0
  # Read the interrupt affinity to verify RSS queues are spread across CPUs
  cat /proc/interrupts | grep mlx5
  # Check the number of RSS queues
  ethtool -l eth0
"
```

Accelerated Networking is enabled at the Azure fabric level and surfaced to the VM as a Mellanox ConnectX VF via DPDK-compatible `mlx5_core`. If `ethtool -i eth0` shows `hv_netvsc` instead, the VM is falling back to the synthetic NIC, which is limited to approximately 2 Gbps and adds 100–300 µs of additional latency.

For latency profiling, use `netperf` or simply measure the RTT with `ping` at high frequency to establish a baseline for intra-cluster Pod-to-Pod latency. Within a single availability zone on Azure, expected Pod-to-Pod RTT is 100–300 µs for accelerated networking versus 1–3 ms for synthetic NIC:

```bash
kubectl exec -n kube-system $DIAG_POD -- bash -c "
  ping -c 100 -i 0.01 $SERVER_IP | tail -3
"
```

---

## Exercise 3: Fault Injection & Recovery Analysis

### 3.1 Simulating a CrashLoopBackOff and Tracing the Recovery Path

Understanding how AKS recovers from container crashes requires watching the kubelet's reconciliation loop in real time. The kubelet's core loop is level-triggered: it continuously computes the delta between the desired Pod spec it fetched from the API server and the actual state of running containers reported by containerd via the CRI. When a container exits, the kubelet detects the discrepancy in its `syncPod` call and restarts it after an exponential backoff (10s, 20s, 40s, 80s, 160s, capped at 300s).

Inject a crash by deploying a Pod that exits immediately:

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: crash-loop-demo
  namespace: default
spec:
  containers:
  - name: crasher
    image: busybox:1.36
    command: ["sh", "-c", "echo 'Starting'; sleep 2; exit 1"]
    resources:
      requests:
        cpu: "10m"
        memory: "16Mi"
EOF
```

Now watch the state machine transition in real time, in a separate terminal:

```bash
# Terminal 1: watch Pod state transitions
kubectl get pod crash-loop-demo -w

# Terminal 2: stream kubelet events for this Pod
kubectl get events -n default --field-selector involvedObject.name=crash-loop-demo -w

# Terminal 3: watch the restart count and backoff timer
watch -n 1 "kubectl get pod crash-loop-demo \
  -o jsonpath='{.status.containerStatuses[0].restartCount}{\" restarts, state: \"}{.status.containerStatuses[0].state}'"
```

On the node, intercept the kubelet's decision-making with `strace` on the containerd socket. This reveals the exact CRI calls the kubelet makes when it detects a crashed container:

```bash
kubectl exec -n kube-system $DIAG_POD -- bash -c "
  # Trace containerd's inbound gRPC calls during a crash/restart cycle
  strace -f -e trace=network -p \$(pgrep containerd) -s 256 2>&1 | \
    grep -A2 'sendmsg\|recvmsg' | head -60
" &

# Alternatively, trace the kubelet's interaction with the CRI socket
kubectl exec -n kube-system $DIAG_POD -- bash -c "
  strace -f -e trace=openat,read,write,close \
    -p \$(pgrep kubelet) -s 128 2>&1 | \
    grep -E 'containerd|cri' | head -40
"
```

After the Pod enters `CrashLoopBackOff`, examine the full container exit history that containerd maintains. The last exit code and the last started timestamp tell you the actual failure mode:

```bash
NODE=$(kubectl get pod crash-loop-demo -o jsonpath='{.spec.nodeName}')
kubectl get pod crash-loop-demo -o jsonpath='{
  .status.containerStatuses[0].lastState.terminated.exitCode}
  {" exited at: "}
  {.status.containerStatuses[0].lastState.terminated.finishedAt}
  {"\n"}'

# On the node, check the OOM kill log if exit code was 137
kubectl exec -n kube-system $DIAG_POD -- bash -c "
  dmesg | grep -E 'OOM|oom_kill|killed process' | tail -10
"
```

An exit code of `1` from `sh -c` is a standard non-zero exit. An exit code of `137` is SIGKILL, which indicates the OOM killer fired. An exit code of `143` is SIGTERM from a graceful shutdown. An exit code of `139` is SIGSEGV — a segmentation fault in the application code.

Delete the crash loop Pod and restore the environment:

```bash
kubectl delete pod crash-loop-demo --grace-period=0
```

### 3.2 Network Partition Simulation via Network Policy

Azure with Calico network policy allows you to simulate a network partition between application tiers by injecting a deny-all NetworkPolicy and observing how the application behaves. This tests both your application's resilience and your ability to diagnose a silent connectivity failure using kernel-level tools.

First, verify baseline connectivity from one nginx Pod to another:

```bash
SRC_POD=$(kubectl get pod -l app=nginx-lab -o jsonpath='{.items[0].metadata.name}')
DST_POD=$(kubectl get pod -l app=nginx-lab -o jsonpath='{.items[1].metadata.name}')
DST_IP=$(kubectl get pod $DST_POD -o jsonpath='{.status.podIP}')

kubectl exec $SRC_POD -- curl -s --connect-timeout 2 http://$DST_IP/
# Should return nginx HTML
```

Now inject a partition by denying all ingress to the nginx-lab Pods:

```bash
kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: nginx-lab
  policyTypes:
  - Ingress
EOF
```

The partition takes effect within seconds as Calico's Felix agent recalculates the iptables chain for the affected Pods. Verify the connectivity failure and diagnose its cause layer by layer:

```bash
# Step 1: Confirm the application-layer failure
kubectl exec $SRC_POD -- curl -s --connect-timeout 2 http://$DST_IP/
# Should time out with no response

# Step 2: Confirm it is a network-layer drop, not a DNS or service failure
kubectl exec $SRC_POD -- ping -c 3 $DST_IP
# ICMP is also blocked by the NetworkPolicy

# Step 3: On the destination node, verify iptables DROP rule exists
DST_NODE=$(kubectl get pod $DST_POD -o jsonpath='{.spec.nodeName}')
DST_DIAG=$(kubectl get pod -n kube-system -l app=diag-node \
  --field-selector spec.nodeName=$DST_NODE -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n kube-system $DST_DIAG -- bash -c "
  iptables -L FORWARD -n -v | grep DROP
  iptables-save | grep -A5 'deny-all-ingress\|CALICO-TO-ENDPOINT\|cali'
"

# Step 4: Capture the dropped packets with tcpdump — you should see SYN packets arriving but no SYN-ACK
kubectl exec -n kube-system $DST_DIAG -- bash -c "
  tcpdump -i any -n dst $DST_IP and tcp and 'tcp[tcpflags] & (tcp-syn) != 0' -c 10
" &
kubectl exec $SRC_POD -- bash -c "for i in \$(seq 1 5); do curl -s --connect-timeout 1 http://$DST_IP/ 2>&1; done"
```

The `tcpdump` output will show TCP SYN packets arriving at the destination node's NIC but no corresponding SYN-ACK being generated. This confirms the packet is being dropped by an iptables rule in the `FORWARD` chain before reaching the network namespace of the target Pod. The kernel's `netfilter` framework processes packets in this order: `PREROUTING` → routing decision → `FORWARD` (for packets transiting the kernel) → `POSTROUTING`. Calico installs its deny rules in `FORWARD` via the `cali-FORWARD` chain.

Remove the network partition and verify recovery:

```bash
kubectl delete networkpolicy deny-all-ingress -n default

# Give Calico's Felix ~5 seconds to resync
sleep 5

kubectl exec $SRC_POD -- curl -s --connect-timeout 2 http://$DST_IP/ | head -5
# Should return nginx HTML again
```

### 3.3 Node Drain and Pod Eviction Verification

Simulating a node drain reproduces the most common maintenance scenario in AKS: a node is cordoned (marked unschedulable), Pods are evicted with a termination grace period, and the scheduler rescheduled them onto remaining nodes. The critical verification is that the Service's EndpointSlice is updated before the Pod's network namespace is torn down, preventing traffic from being sent to an IP that no longer has a listening process.

```bash
NODE_TO_DRAIN=$(kubectl get pods -l app=nginx-lab \
  -o jsonpath='{.items[0].spec.nodeName}')

# Record the Pod IPs before drain
echo "Pre-drain Pod IPs:"
kubectl get pods -l app=nginx-lab -o wide

# Cordon the node — no new Pods will schedule here
kubectl cordon $NODE_TO_DRAIN

# Confirm the node is now unschedulable
kubectl get node $NODE_TO_DRAIN -o jsonpath='{.spec.unschedulable}{"\n"}'

# Start a continuous traffic probe in a separate terminal
kubectl run traffic-probe \
  --image=busybox:1.36 \
  --restart=Never \
  -- sh -c "while true; do wget -qO- --timeout=1 nginx-lab-svc.default.svc.cluster.local && echo OK || echo FAIL; sleep 0.5; done" &

# Drain the node — evicts all Pods with a 30-second grace period
kubectl drain $NODE_TO_DRAIN \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=30 \
  --timeout=120s \
  --force

# Monitor EndpointSlice updates during the drain
kubectl get endpointslice -n default \
  -l kubernetes.io/service-name=nginx-lab-svc -w &

# After drain completes, check traffic probe for FAIL counts
kubectl logs traffic-probe --tail=50
```

During the drain, the endpoint controller running in `kube-controller-manager` removes the evicted Pod's IP from the EndpointSlice as soon as the Pod's `deletionTimestamp` is set. `kube-proxy` on each node then receives this update via its watch on the EndpointSlice API and removes the corresponding `iptables` DNAT rule. This propagation chain takes a finite time — typically 1–3 seconds in a healthy cluster. If your traffic probe shows `FAIL` responses during the drain, it means traffic hit an iptables rule that was routing to an IP whose process had already exited. The fix is to implement a `preStop` hook with a sleep in your container spec, which delays the SIGTERM and gives the control plane time to drain the endpoint:

```yaml
# Add this to your container spec to prevent connection drops during eviction
lifecycle:
  preStop:
    exec:
      command: ["sh", "-c", "sleep 5"]
terminationGracePeriodSeconds: 35
```

Uncordon the node to restore full capacity:

```bash
kubectl uncordon $NODE_TO_DRAIN
kubectl delete pod traffic-probe --ignore-not-found
kubectl get pods -l app=nginx-lab -o wide
```

---

## Diagnostic Cheat Sheet & Verification Checklist

This section consolidates every command into a structured reference organized by the layer of the stack you are diagnosing. Use it as your incident runbook.

### Control Plane State

```bash
# Cluster-wide Pod state with node placement and IP
kubectl get pods -A -o wide

# Full node status including pressure conditions and allocatable resources
kubectl get nodes -o custom-columns=\
"NAME:.metadata.name,\
STATUS:.status.conditions[-1].type,\
CPU:.status.allocatable.cpu,\
MEM:.status.allocatable.memory,\
VERSION:.status.nodeInfo.kubeletVersion"

# API server health and latency
kubectl get --raw /healthz
kubectl get --raw /metrics | grep apiserver_request_duration_seconds_bucket | \
  awk '{sum+=$NF; count++} END {print "avg:", sum/count, "count:", count}'

# etcd health via API server proxy
kubectl get --raw /metrics | grep -E 'etcd_request_duration|etcd_object_counts'

# Cluster events sorted by time — most recent first
kubectl get events -A --sort-by='.lastTimestamp' | tail -30

# Check all Pods not in Running/Completed state
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded

# Component statuses (scheduler, controller-manager)
kubectl get componentstatuses

# Deployment rollout and replica state
kubectl rollout status deployment/nginx-lab
kubectl get replicaset -l app=nginx-lab

# EndpointSlice membership vs Ready Pods
kubectl get endpointslice -n default -l kubernetes.io/service-name=nginx-lab-svc
```

### Node and CRI Layer

```bash
# CRI Pod list on a specific node
crictl --runtime-endpoint unix:///run/containerd/containerd.sock pods

# CRI container list with state
crictl --runtime-endpoint unix:///run/containerd/containerd.sock ps -a

# Full container inspect: cgroup path, PID, resource limits
crictl inspect <container-id> | jq '{pid:.info.pid,cgroupsPath:.info.runtimeSpec.linux.cgroupsPath}'

# kubelet node summary: CPU/memory requests and limits per Pod
kubectl get --raw /api/v1/nodes/<node-name>/proxy/stats/summary | \
  jq '.pods[] | {name:.podRef.name, cpuUsage:.cpu.usageNanoCores, memUsage:.memory.workingSetBytes}'

# Check kubelet configuration for resource reservation
kubectl get --raw /api/v1/nodes/<node-name>/proxy/configz | \
  jq '.kubeletconfig | {cpuManagerPolicy, memoryManagerPolicy, kubeReserved, systemReserved, evictionHard}'

# CFS CPU throttle statistics for all cgroups
find /sys/fs/cgroup/kubepods -name 'cpu.stat' | while read f; do
  THROTTLED=$(grep throttled_periods $f | awk '{print $2}')
  TOTAL=$(grep nr_periods $f | awk '{print $2}')
  if [ "$TOTAL" -gt 0 ] && [ "$THROTTLED" -gt 0 ]; then
    PCT=$(echo "scale=1; $THROTTLED*100/$TOTAL" | bc)
    echo "$f: ${PCT}% throttled"
  fi
done

# OOM kill history from kernel ring buffer
dmesg | grep -E 'oom_kill|Out of memory|Killed process' | tail -20

# Node memory pressure stall information
cat /proc/pressure/memory

# Process-level memory and CPU stats
top -b -n 1 -o %CPU | head -20
```

### Network Layer

```bash
# Interface statistics — errors and drops for all interfaces
ip -s link show

# TCP socket state with internal kernel metrics (RTT, retransmits, window)
ss -tipm

# Count sockets by state — identify CLOSE_WAIT and TIME_WAIT accumulation
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn

# Active connection counts per remote IP
ss -tn | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20

# NIC hardware statistics — look for dropped, missed, errors
ethtool -S eth0 | grep -E 'drop|miss|error|pause' | grep -v ' 0$'

# NIC ring buffer configuration
ethtool -g eth0

# NIC driver — verify mlx5_core for SR-IOV (accelerated networking)
ethtool -i eth0

# Calico/kube-proxy iptables rules for a specific Service
iptables-save | grep -A20 "KUBE-SVC-"

# Live packet capture on Pod interface — replace vethXXX with actual veth
tcpdump -i vethXXX -n -s 128 'tcp port 80' -c 50

# Capture DNS queries on the node
tcpdump -i any -n 'udp port 53' -c 20

# Verify Pod DNS resolution
kubectl exec $POD -- nslookup kubernetes.default.svc.cluster.local
kubectl exec $POD -- cat /etc/resolv.conf
```

### Performance Profiling

```bash
# System-wide perf stat for 10 seconds — hardware counters
perf stat -a \
  -e cycles,instructions,cache-misses,cache-references,\
branch-misses,context-switches,cpu-migrations \
  -- sleep 10

# Per-process CPU profile with call graph (requires debug symbols)
perf record -g -p <pid> -- sleep 10
perf report --stdio --no-pager | head -60

# bpftool — list all loaded eBPF programs (Calico, Container Insights)
bpftool prog list

# bpftool — show eBPF maps used by a specific program
bpftool map list
bpftool map dump id <map-id> | head -20

# iostat — disk I/O saturation (useful for etcd volumes on node)
iostat -xz 1 5

# Disk I/O per cgroup — identify which Pod is saturating disk
cat /sys/fs/cgroup/kubepods/blkio.io_service_bytes_recursive 2>/dev/null || \
  find /sys/fs/cgroup/kubepods -name 'io.stat' | while read f; do
    echo "=== $f ==="; cat "$f"
  done
```

### Verification Checklist

The following checklist represents the minimum verification pass for a healthy AKS cluster. Work through it top to bottom during any infrastructure change or incident triage.

**Control Plane:**
Run `kubectl get componentstatuses` and confirm Scheduler and ControllerManager show `Healthy`. Run `kubectl get nodes` and confirm all nodes show `Ready`. Confirm zero Pods in `Pending` state for more than 60 seconds with `kubectl get pods -A --field-selector=status.phase=Pending`. Confirm zero Pods in `CrashLoopBackOff` with `kubectl get pods -A | grep CrashLoopBackOff`.

**Data Plane and Networking:**
Confirm Pod IP count in EndpointSlice equals the Deployment's `readyReplicas`. Confirm iptables KUBE-SVC chains on each node list the same Pod IPs as the EndpointSlice. Confirm `ss -tipm` shows no unexpected `CLOSE_WAIT` accumulation for application ports. Confirm ethtool `-S eth0` shows zero `dropped` frames growing under steady-state load. Confirm accelerated networking is active with `ethtool -i eth0` returning `mlx5_core`.

**Resource and Saturation:**
Confirm `cpu.stat` throttled percentage below 10% for all application cgroups. Confirm `/proc/pressure/memory full avg10` below 5% on all nodes. Confirm `dmesg` shows no OOM kills in the past 24 hours. Confirm disk I/O on the OS disk and any PVC-backed volumes is below 80% utilization via `iostat -xz`.

**Recovery Posture:**
Confirm all Deployments have a `preStop` sleep hook and `terminationGracePeriodSeconds` set to at least 35 seconds. Confirm PodDisruptionBudgets are configured for all stateful workloads. Confirm `kubectl drain --dry-run` on each node completes without errors, verifying that no Pod will be evicted without a replacement destination.
