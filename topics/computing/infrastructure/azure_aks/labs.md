# Operational Verification Labs: Azure AKS

## Objective & Environment Setup

This guide treats your Azure Kubernetes Service cluster as a living system whose internal state must be interrogated directly, not inferred from dashboards. Every exercise in this lab forces you to reason from raw kernel instrumentation, network socket tables, container runtime metadata, and scheduler telemetry outward to cluster-level behavior. The goal is not to verify that AKS "works" in the abstract but to build the specific diagnostic muscle memory required to identify, characterize, and confirm the resolution of real production failures.

The lab assumes a three-node AKS cluster (`Standard_D4s_v3` SKU or equivalent with 4 vCPUs and 16 GB RAM per node), Azure CNI with Calico network policy, and a managed system node pool. You will work from a Linux workstation or Azure Cloud Shell with direct `kubectl` access and SSH access to individual node VMs via either a bastion host or `kubectl debug node`. All verification commands are issued against a live cluster carrying synthetic load from a `stress-ng` deployment defined below.

### Toolchain Installation

Install the full diagnostic stack on each AKS worker node. Because AKS nodes run a hardened Azure Linux (Mariner) or Ubuntu image, some packages require the Microsoft package repository. Connect to each node via `kubectl debug node` and run the following:

```bash
# From workstation: open a privileged shell on a node
NODE=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
kubectl debug node/${NODE} -it --image=mcr.microsoft.com/cbl-mariner/base/core:2.0 -- bash

# Inside the debug pod, chroot into the host filesystem
chroot /host

# Install diagnostic tools (Azure Linux / Mariner)
tdnf install -y iproute2 ethtool tcpdump perf bpftool util-linux strace procps
tdnf install -y kernel-headers-$(uname -r) || true

# Confirm kernel version and BPF support
uname -r
bpftool version
bpftool feature probe | grep -E "bpf_prog_type|map_type"
```

Install the Kubernetes-side toolchain on your workstation:

```bash
# kubectl (latest stable)
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# kubelogin for AAD-integrated AKS clusters
wget https://github.com/Azure/kubelogin/releases/download/v0.1.3/kubelogin-linux-amd64.zip
unzip kubelogin-linux-amd64.zip && sudo mv bin/linux_amd64/kubelogin /usr/local/bin/

# Merge AKS credentials
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster --overwrite-existing
kubelogin convert-kubeconfig -l azurecli

kubectl cluster-info
kubectl get nodes -o wide
```

### Synthetic Load Deployment

Deploy the following manifests before beginning any exercise. This `stress-ng` DaemonSet generates CPU, memory, and I/O pressure across every node, giving you a realistic signal environment rather than idle-cluster noise.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: stress-load
  namespace: default
  labels:
    app: stress-load
spec:
  selector:
    matchLabels:
      app: stress-load
  template:
    metadata:
      labels:
        app: stress-load
    spec:
      tolerations:
        - key: "node-role.kubernetes.io/control-plane"
          operator: "Exists"
          effect: "NoSchedule"
      containers:
        - name: stress
          image: docker.io/alexeiled/stress-ng:latest
          args:
            - "--cpu"
            - "2"
            - "--vm"
            - "1"
            - "--vm-bytes"
            - "512M"
            - "--io"
            - "1"
            - "--timeout"
            - "0"
          resources:
            requests:
              cpu: "500m"
              memory: "600Mi"
            limits:
              cpu: "2"
              memory: "768Mi"
          securityContext:
            privileged: false
            capabilities:
              add: ["SYS_RESOURCE"]
```

Apply with `kubectl apply -f stress-daemonset.yaml` and confirm pods are running on every node with `kubectl get pods -o wide`. Give the cluster sixty seconds to settle before proceeding.

---

## Exercise 1: Live State & Internal Subsystem Inspection

The discipline of live-state inspection is built on a single principle: every observable cluster behavior has a corresponding kernel-level artifact, and your job is to build the chain of evidence from API object to syscall. This exercise walks that chain end to end for three subsystems: the container runtime, the network data plane, and the scheduling and cgroup hierarchy.

### 1.1 Container Runtime Inspection with crictl

AKS uses containerd as its container runtime interface (CRI) implementation. The kubelet speaks to containerd over a Unix domain socket at `/run/containerd/containerd.sock`, and `crictl` is the CRI-native CLI that lets you query that socket directly without going through the Kubernetes API. This distinction matters: a pod can be live and healthy from containerd's perspective while the kubelet's watch loop has not yet reconciled it, or conversely a pod can appear `Running` in the API while containerd has already marked the container's init process as exited.

SSH into the first worker node and inspect the runtime state directly:

```bash
# Point crictl at the containerd socket
export CONTAINER_RUNTIME_ENDPOINT=unix:///run/containerd/containerd.sock

# List all pods known to the runtime (bypasses kube-apiserver)
crictl pods

# List all containers with their state and exit codes
crictl ps -a

# Grab a specific container ID from the stress-load pod
CONTAINER_ID=$(crictl ps | grep stress | awk '{print $1}' | head -1)

# Inspect full OCI runtime spec: namespaces, cgroups, capabilities, mounts
crictl inspect ${CONTAINER_ID} | python3 -m json.tool | less

# Check the OCI state machine: should be "running" with a valid PID
crictl inspect ${CONTAINER_ID} | python3 -c "
import sys, json
data = json.load(sys.stdin)
pid  = data['info']['pid']
st   = data['status']['state']
img  = data['status']['image']['image']
print(f'State: {st}  PID: {pid}  Image: {img}')
"

# Retrieve recent container logs directly from containerd (no kubelet buffering)
crictl logs --tail 50 ${CONTAINER_ID}

# Verify that the sandbox (pause container) is healthy
SANDBOX_ID=$(crictl pods | grep stress | awk '{print $1}' | head -1)
crictl inspectp ${SANDBOX_ID} | python3 -m json.tool | grep -A5 '"state"'
```

The `crictl inspect` output for the OCI runtime spec reveals the exact Linux namespace set that the container occupies. Each namespace entry in the `linux.namespaces` array corresponds to a `/proc/PID/ns/` symlink. The pause container (sandbox) holds the network, IPC, and UTS namespace file descriptors, and the application container joins them at startup. If a container restart has incremented its `restartCount` in the Kubernetes API but the sandbox shows no corresponding state transition, the problem is inside the container's init process rather than in the network or storage plumbing.

Verify the namespace inheritance directly from the host:

```bash
# Get the PID of the stress-ng container
STRESS_PID=$(crictl inspect ${CONTAINER_ID} | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['pid'])")

# Get the PID of the pause container for the same pod
PAUSE_PID=$(crictl inspectp ${SANDBOX_ID} | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['pid'])")

# Confirm the network namespace is shared between pause and stress-ng
ls -la /proc/${STRESS_PID}/ns/net
ls -la /proc/${PAUSE_PID}/ns/net
# Both symlinks must point to the same inode: net:[NNNNNNNN]

# Inspect cgroup hierarchy for CPU throttling
cat /proc/${STRESS_PID}/cgroup
# Note the cgroup v2 path, then inspect throttling counters
CGROUP_PATH=$(cat /proc/${STRESS_PID}/cgroup | grep -oP '(?<=0::).*')
cat /sys/fs/cgroup${CGROUP_PATH}/cpu.stat
# Fields: usage_usec, user_usec, system_usec, nr_throttled, throttled_usec
```

The `throttled_usec` counter in `cpu.stat` is the most direct evidence of CFS bandwidth throttling. When a container's CPU request is `500m` (5ms of CPU time per 100ms period by default) but workload demand exceeds that, the kernel's CFS bandwidth controller fires and increments `nr_throttled`. This manifests in the application as random latency spikes rather than reduced throughput, because the entire cgroup is frozen mid-execution.

### 1.2 Network Data Plane Inspection with iproute2 and ss

Azure CNI assigns a real VNet IP directly to each pod, meaning pods are first-class citizens in the Azure virtual network rather than occupying an overlay network. Each pod's network interface is a synthetic vNIC backed by a VNet IP from the node's subnet. The kernel sees this as a standard `veth` pair: one end lives in the pod's network namespace, the other lives on the host, attached to an Azure-managed bridge or directly routed depending on the CNI plugin version.

Establish the full network path from pod interface to node interface to Azure VNet:

```bash
# From the host: list all network interfaces including pod veth endpoints
ip -s link show
# Look for entries like eth0, azv<hash>, cali<hash> (Calico) or veth<hash> (bridge mode)

# Show the full routing table with protocol and metric
ip route show table all | grep -v "table local" | sort

# Enumerate all pod veth endpoints and their peer namespaces
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
    ns=$(readlink /proc/$pid/ns/net 2>/dev/null)
    if [ -n "$ns" ]; then
        echo "PID $pid -> ns $ns"
    fi
done | sort -u | head -20

# Enter a specific pod's network namespace and inspect its interface
nsenter --net=/proc/${STRESS_PID}/ns/net ip addr show
nsenter --net=/proc/${STRESS_PID}/ns/net ip route show
nsenter --net=/proc/${STRESS_PID}/ns/net ss -s
```

The `ss` socket summary from inside the pod's namespace gives you the ground truth on socket state at the moment of inspection, independent of anything the application reports. Now run a detailed socket inspection from the host to characterize all established connections cluster-wide:

```bash
# Full socket table: TCP state, send/recv queue depths, timer state, process
ss -tipm 'state established'

# Focus on sockets with non-zero send queues (send buffer backpressure)
ss -tipm 'state established' | awk 'NR==1 || /snd_wnd/ && /skmem/ {print}'

# Count socket states across all namespaces (approximate via /proc/net)
awk 'NR>1 {print $4}' /proc/net/tcp | sort | uniq -c | sort -rn
# State 0A=LISTEN, 01=ESTABLISHED, 06=TIME_WAIT, 08=CLOSE_WAIT

# Inspect interface error counters for the primary node NIC
PRIMARY_NIC=$(ip route show default | awk '/default/ {print $5}' | head -1)
ip -s -s link show ${PRIMARY_NIC}
ethtool -S ${PRIMARY_NIC} | grep -E "rx_errors|tx_errors|rx_dropped|tx_dropped|missed|no_buffer"
```

The `ethtool -S` output from the Azure synthetic NIC driver (`hv_netvsc`) exposes per-queue ring buffer statistics that the standard `ip -s link` counter set does not. The fields `rx_no_direct_rx_buf` and `tx_send_full` indicate that the VF ring buffer is exhausted, which causes the kernel to drop packets before they reach the socket layer. This is a hardware-level saturation condition that no amount of socket buffer tuning will fix; it requires increasing the number of VNet queues or upgrading to a larger VM SKU.

Now verify Calico or Azure CNI network policy enforcement by confirming that iptables or eBPF rules are installed correctly:

```bash
# Check which dataplane Calico is using
kubectl get felixconfiguration default -o jsonpath='{.spec.dataplaneDriver}' 2>/dev/null || echo "Using iptables"

# For iptables dataplane: verify Calico chains exist
iptables-save | grep -c "cali-"
iptables-save | grep "cali-INPUT" | head -5

# Count total iptables rules (high counts >10000 cause measurable kube-proxy latency)
iptables-save | wc -l

# For eBPF dataplane: verify BPF programs are attached to interfaces
bpftool net show | grep -E "xdp|tc"
bpftool prog list | grep -E "classifier|xdp" | wc -l
```

### 1.3 Control Plane and etcd State Inspection

In AKS, the control plane (API server, etcd, controller-manager, scheduler) runs in a Microsoft-managed Azure subscription and is not directly accessible via SSH. However, you can probe API server latency and etcd revision drift indirectly through the API server's `/metrics` and `/readyz` endpoints, and directly observe the effects of control plane pressure on watch latency and resource version monotonicity.

```bash
# Confirm API server health and latency to all three endpoints
kubectl get --raw /healthz
kubectl get --raw /readyz
kubectl get --raw /livez/etcd

# Stream API server metrics: focus on etcd request duration and watch counts
kubectl get --raw /metrics | grep -E "^etcd_request_duration|^apiserver_watch_events|^etcd_object_counts"

# Observe resource version monotonicity: each LIST response increments the global revision
for i in $(seq 1 5); do
    kubectl get pods -A -o jsonpath='{.metadata.resourceVersion}' 2>/dev/null
    echo ""
    sleep 2
done
# Resource version must strictly increase. A non-monotonic value indicates etcd compaction
# or leader election during the observation window.

# Check API server audit log for recent error rates (requires diagnostic settings enabled)
# If Log Analytics is configured:
az monitor log-analytics query \
  --workspace $(az aks show -g myResourceGroup -n myAKSCluster \
    --query addonProfiles.omsagent.config.logAnalyticsWorkspaceResourceID -o tsv) \
  --analytics-query "AzureDiagnostics | where Category == 'kube-apiserver' | where httpStatusCode_d >= 500 | summarize count() by bin(TimeGenerated, 1m), httpStatusCode_d | order by TimeGenerated desc | take 20" \
  --output table

# Watch the scheduler queue depth indirectly: pods stuck in Pending with no events
kubectl get pods -A --field-selector=status.phase=Pending
kubectl describe pod $(kubectl get pods -A --field-selector=status.phase=Pending -o jsonpath='{.items[0].metadata.name}' 2>/dev/null) 2>/dev/null | grep -A10 "Events:"

# Confirm node heartbeat freshness: status.conditions[Ready] lastHeartbeatTime
kubectl get nodes -o json | python3 -c "
import sys, json, datetime
nodes = json.load(sys.stdin)
now = datetime.datetime.now(datetime.timezone.utc)
for n in nodes['items']:
    name = n['metadata']['name']
    for cond in n['status']['conditions']:
        if cond['type'] == 'Ready':
            ts = datetime.datetime.fromisoformat(cond['lastHeartbeatTime'].replace('Z','+00:00'))
            delta = (now - ts).total_seconds()
            print(f'{name}: Ready={cond[\"status\"]}  heartbeat_age={delta:.1f}s')
"
```

The node heartbeat age calculation is critical: the kubelet sends a heartbeat to the API server every `nodeStatusUpdateFrequency` seconds (default 10s). The node controller marks a node `NotReady` after `node-monitor-grace-period` (default 40s) elapses without a heartbeat. If your heartbeat ages are consistently above 20 seconds, you are operating with a narrow margin before the node controller begins pod eviction. This symptom typically points to either API server throttling (HTTP 429 responses to the kubelet's lease update) or high `kube-apiserver` to `etcd` latency exceeding 100ms.

---

## Exercise 2: Benchmarking & Saturation Profiling

Saturation profiling on AKS requires you to instrument three distinct resource planes simultaneously: the CPU scheduler inside the pod's cgroup, the kernel's network send and receive paths, and the storage I/O path through Azure Premium SSD or Azure Files. The challenge is that AKS isolates workloads across VM boundaries, so saturation in one pod can produce nonlinear latency effects in another pod on the same node due to shared L3 cache, NIC interrupt affinity, and cgroup bandwidth controller contention.

### 2.1 CPU Profiling with perf and cgroup Throttle Analysis

`perf stat` measures hardware performance counter events at the process or cgroup level, giving you a quantitative view of instruction-level efficiency, cache behavior, and branch misprediction rates. Run it against the stress-ng process to establish a baseline, then compare against an application container:

```bash
# Get the stress-ng PID again (it may have changed after pod restart)
STRESS_PID=$(crictl inspect ${CONTAINER_ID} | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['pid'])")

# Attach perf stat to the existing process for 10 seconds
perf stat -p ${STRESS_PID} --timeout 10000 \
  -e cycles,instructions,cache-misses,cache-references,branch-misses,branch-instructions,\
page-faults,context-switches,cpu-migrations,LLC-loads,LLC-load-misses 2>&1

# Expected output interpretation:
#   instructions/cycle (IPC) < 1.0 means memory-bound workload
#   LLC-load-misses / LLC-loads > 10% means working set exceeds L3 cache
#   context-switches / second > 10000 means scheduler is under heavy pressure

# Measure CPU scheduler latency: how long runnable tasks wait on the run queue
perf sched record -p ${STRESS_PID} -- sleep 5
perf sched latency | head -30
# Column "Max Latency" > 1ms on a loaded node indicates CFS starvation

# Flame graph via perf record + stackcollapse
perf record -F 99 -p ${STRESS_PID} -g -- sleep 10
perf script | \
  awk '
    /^[^\t]/ { if (stack != "") print stack; stack = $1; next }
    { stack = stack "\n" $0 }
    END { if (stack != "") print stack }
  ' > /tmp/perf.stacks
# Transfer /tmp/perf.stacks to your workstation and process with flamegraph.pl
# This flame graph will show if CPU time is dominated by kernel overhead vs userspace work
```

Now quantify CFS throttling programmatically by polling `cpu.stat` over a 30-second window and computing the throttle ratio:

```bash
CGROUP_PATH=$(cat /proc/${STRESS_PID}/cgroup | grep -oP '(?<=0::).*')

python3 - <<'EOF'
import time, re

path = "/sys/fs/cgroup" + open(f"/proc/$(pgrep -n stress-ng)/cgroup").read().strip().split("::")[-1] + "/cpu.stat"

def read_stat(p):
    d = {}
    with open(p) as f:
        for line in f:
            k, v = line.split()
            d[k] = int(v)
    return d

s1 = read_stat(path)
time.sleep(30)
s2 = read_stat(path)

throttled_us = s2["throttled_usec"] - s1["throttled_usec"]
usage_us     = s2["usage_usec"]     - s1["usage_usec"]
nr_throttled = s2["nr_throttled"]   - s1["nr_throttled"]
ratio        = throttled_us / (usage_us + throttled_us) * 100 if (usage_us + throttled_us) > 0 else 0

print(f"Window: 30s")
print(f"CPU usage:          {usage_us/1e6:.3f}s")
print(f"CPU throttled:      {throttled_us/1e6:.3f}s")
print(f"Throttle events:    {nr_throttled}")
print(f"Throttle ratio:     {ratio:.2f}%")
print(f"Verdict: {'THROTTLED - increase CPU limit or reduce load' if ratio > 5 else 'OK'}")
EOF
```

A throttle ratio above 5% is a production concern. The correct remediation depends on the direction: if the container's CPU request is well below its actual steady-state consumption, increase the request to match (this also adjusts scheduling priority). If the limit is artificially low for burst protection, consider removing the CPU limit entirely and relying on requests alone for scheduling, which is a valid production pattern for latency-sensitive workloads in AKS.

### 2.2 Network Throughput and Latency Profiling

The Azure synthetic NIC on a `Standard_D4s_v3` node provides up to 8 Gbps of expected network bandwidth with a baseline of 2 Gbps. The accelerated networking path (SR-IOV VF bypass) is enabled by default on AKS nodes of `Standard_Ds_v3` and larger. When SR-IOV is active, NIC interrupts are delivered directly to the VM vCPU without the Hyper-V VSP/VSC overhead. You can confirm SR-IOV status by checking for the Mellanox (`mlx5`) or `hv_netvsc` with VF driver:

```bash
# Check for SR-IOV VF interface (mlx4/mlx5 = Mellanox SR-IOV)
lspci | grep -i ethernet
ip link show | grep -E "mlx|enP|mana"

# Confirm ring buffer sizes (larger = better throughput, more memory)
ethtool -g ${PRIMARY_NIC}
# Pre-set maximums vs current: if current RX < maximum, increase it
ethtool -G ${PRIMARY_NIC} rx 4096 tx 4096 2>/dev/null || echo "Cannot modify (managed VF)"

# Measure inter-pod UDP throughput using iperf3 deployed as a Job pair
kubectl apply -f - <<'MANIFEST'
apiVersion: v1
kind: Pod
metadata:
  name: iperf-server
  namespace: default
  labels:
    role: iperf-server
spec:
  containers:
    - name: iperf3
      image: networkstatic/iperf3:latest
      args: ["-s", "-p", "5201"]
      ports:
        - containerPort: 5201
          protocol: TCP
  restartPolicy: Always
---
apiVersion: v1
kind: Service
metadata:
  name: iperf-server
  namespace: default
spec:
  selector:
    role: iperf-server
  ports:
    - port: 5201
      targetPort: 5201
  type: ClusterIP
MANIFEST

# Wait for the server pod to be ready
kubectl wait pod/iperf-server --for=condition=Ready --timeout=60s

IPERF_SERVER_IP=$(kubectl get svc iperf-server -o jsonpath='{.spec.clusterIP}')

# Run iperf3 client from a different node (use nodeSelector to enforce placement)
kubectl run iperf-client \
  --image=networkstatic/iperf3:latest \
  --restart=Never \
  --overrides='{"spec":{"nodeName":"'"$(kubectl get nodes -o jsonpath='{.items[1].metadata.name}')"'"}}' \
  -- iperf3 -c ${IPERF_SERVER_IP} -p 5201 -t 20 -P 8 -J

# Wait and retrieve results
kubectl wait pod/iperf-client --for=condition=Ready --timeout=30s || true
kubectl logs iperf-client --follow
```

While iperf3 runs, capture the kernel TCP send path statistics on the server node simultaneously:

```bash
# On the server node: watch TCP retransmit and congestion window behavior
watch -n 1 'ss -tipm "dport == 5201 or sport == 5201" | grep -E "cwnd|rtt|retrans|bytes_sent"'

# Also monitor NIC queue depths during the test
watch -n 1 "ethtool -S ${PRIMARY_NIC} | grep -E 'tx_queue|rx_queue|no_buffer'"
```

### 2.3 Storage I/O Profiling for PersistentVolume Workloads

Azure Premium SSD P30 (1 TB) delivers 5,000 IOPS and 200 MB/s. The CSI driver (`disk.csi.azure.com`) exposes these disks as block devices through the kernel's block layer. Measure actual delivered I/O performance against the provisioned tier:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: bench-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: managed-premium
  resources:
    requests:
      storage: 32Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: fio-bench
  namespace: default
spec:
  containers:
    - name: fio
      image: ljishen/fio:latest
      command: ["/bin/sh", "-c"]
      args:
        - |
          fio --name=randread4k --filename=/data/testfile \
              --rw=randread --bs=4k --direct=1 --numjobs=4 \
              --iodepth=32 --size=4G --runtime=60 --time_based \
              --group_reporting --output-format=json > /tmp/fio_randread.json && \
          fio --name=seqwrite128k --filename=/data/testfile \
              --rw=write --bs=128k --direct=1 --numjobs=1 \
              --iodepth=16 --size=4G --runtime=60 --time_based \
              --group_reporting --output-format=json > /tmp/fio_seqwrite.json && \
          python3 -c "
import json, sys
for fname, label in [('/tmp/fio_randread.json','4K RandRead'), ('/tmp/fio_seqwrite.json','128K SeqWrite')]:
    with open(fname) as f:
        d = json.load(f)
    j = d['jobs'][0]
    op = 'read' if 'RandRead' in label else 'write'
    iops = j[op]['iops']
    bw   = j[op]['bw'] / 1024
    lat  = j[op]['lat_ns']['mean'] / 1e6
    print(f'{label}: IOPS={iops:.0f}  BW={bw:.1f}MB/s  LatMean={lat:.3f}ms')
          "
      volumeMounts:
        - name: bench-vol
          mountPath: /data
  volumes:
    - name: bench-vol
      persistentVolumeClaim:
        claimName: bench-pvc
  restartPolicy: Never
```

Apply and tail the pod logs:

```bash
kubectl apply -f fio-bench.yaml
kubectl wait pod/fio-bench --for=condition=Ready --timeout=120s
kubectl logs fio-bench --follow
```

While fio runs, verify that the kernel block layer is not introducing additional latency through I/O scheduler queuing. Azure disk devices in AKS use the `none` or `mq-deadline` scheduler. Check this from the node:

```bash
# Find the block device backing the PVC
kubectl get pv $(kubectl get pvc bench-pvc -o jsonpath='{.spec.volumeName}') \
  -o jsonpath='{.spec.csi.volumeHandle}'
# The volume handle contains the Azure disk name.
```
