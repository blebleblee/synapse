# Operational Verification Labs: 03 Longhorn Distributed Storage

## Objective & Environment Setup

The Longhorn distributed storage system is a modern, cloud-native block storage solution designed for Kubernetes environments. This lab focuses on operational verification of Longhorn's core subsystems, including its distributed consensus, storage replication, and fault recovery mechanisms. The environment is configured with a Kubernetes cluster running Longhorn v1.6+, and all diagnostic tools are installed on the control plane node.

### Required CLI Tools:
- `kubectl` (v1.28+)
- `bpftool` (v6.1+)
- `iproute2` (v5.15+)
- `tcpdump` (v4.99+)
- `strace` (v6.0+)
- `perf` (v6.1+)
- `bpftrace` (v0.18+)

### Environment Configuration:
```bash
# Verify Kubernetes cluster status
kubectl cluster-info
kubectl get nodes -o wide

# Confirm Longhorn installation
kubectl get pods -n longhorn-system
kubectl get storageclass
kubectl get pvc -A

# Set up monitoring namespace
kubectl create namespace longhorn-monitoring
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.0/deploy/longhorn.yaml
```

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise involves inspecting the live state of Longhorn's internal subsystems, including its consensus engine, replica management, and storage node health. The inspection uses kernel-level tools to observe BPF maps and memory structures, as well as Kubernetes-native tools to inspect pod states and metrics.

### 1.1 Inspect Longhorn Controller and Replica Processes

```bash
# Identify Longhorn controller and replica processes
kubectl get pods -n longhorn-system -l app=longhorn-manager
kubectl get pods -n longhorn-system -l app=longhorn-engine

# Inspect controller logs for consensus state
kubectl logs -n longhorn-system -l app=longhorn-manager --tail=100

# Inspect replica logs for storage state
kubectl logs -n longhorn-system -l app=longhorn-engine --tail=100

# Monitor controller process memory usage
kubectl exec -it -n longhorn-system <controller-pod-name> -- ps aux | grep longhorn
```

### 1.2 Analyze BPF Maps for Storage I/O Tracking

```bash
# Inspect BPF maps used for I/O tracking (requires kernel 5.10+)
sudo bpftool map show

# List BPF programs attached to storage I/O paths
sudo bpftool prog show

# Monitor BPF ring buffer for I/O events
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_write { printf("Write syscall to fd %d\n", args->fd); }'
```

### 1.3 Examine Storage Node Metrics

```bash
# Get detailed metrics from Longhorn manager
kubectl exec -it -n longhorn-system <manager-pod-name> -- curl -s http://localhost:9500/v1/ | jq

# Inspect replica health and sync status
kubectl exec -it -n longhorn-system <manager-pod-name> -- curl -s http://localhost:9500/v1/replicas | jq

# Monitor storage node disk usage
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.storage}{"\n"}{end}'

# Inspect kernel memory usage for storage subsystem
cat /proc/meminfo | grep -E "(MemTotal|MemFree|Cached|Buffers)"
```

### 1.4 Validate Storage Volume State

```bash
# List all Longhorn volumes
kubectl get volumes.longhorn.io -A

# Inspect volume configuration and status
kubectl describe volume.longhorn.io <volume-name> -n <namespace>

# Check volume replica distribution
kubectl exec -it -n longhorn-system <manager-pod-name> -- curl -s http://localhost:9500/v1/volumes/<volume-name> | jq '.replicas'
```

## Exercise 2: Benchmarking & Saturation Profiling

This exercise generates synthetic load to test Longhorn's performance under saturation conditions. It uses `fio` for I/O benchmarking and `perf` for profiling kernel-level performance bottlenecks.

### 2.1 Generate I/O Load with fio

```bash
# Create a test pod with a Longhorn volume mounted
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: fio-test-pod
spec:
  containers:
  - name: fio
    image: busybox
    command: ["/bin/sh", "-c"]
    args:
      - |
        mkdir -p /mnt/test && \
        fio --name=test --direct=1 --rw=randrw --bs=4k --size=1G --numjobs=4 --time_based=1 --runtime=60 --group_reporting --output-format=json
    volumeMounts:
    - name: test-volume
      mountPath: /mnt/test
  volumes:
  - name: test-volume
    persistentVolumeClaim:
      claimName: test-pvc
  restartPolicy: Never
EOF

# Monitor I/O performance during test
kubectl exec -it fio-test-pod -- fio --name=test --direct=1 --rw=randrw --bs=4k --size=1G --numjobs=4 --time_based=1 --runtime=60 --group_reporting --output-format=json
```

### 2.2 Profile Kernel-Level Performance

```bash
# Profile Longhorn I/O path with perf
sudo perf record -g -e syscalls:sys_enter_write,syscalls:sys_enter_read -p $(pgrep longhorn-manager)

# Analyze performance profile
sudo perf report

# Monitor network I/O during storage operations
sudo tcpdump -i any -n port 9500 -w /tmp/longhorn.pcap &
kubectl exec -it <manager-pod-name> -- curl -s http://localhost:9500/v1/volumes/<volume-name>/action/sync
sudo killall tcpdump
```

### 2.3 Stress Test with Concurrent Operations

```bash
# Simulate concurrent volume operations
for i in {1..10}; do
  kubectl exec -it <manager-pod-name> -- curl -s http://localhost:9500/v1/volumes/<volume-name>/action/sync &
done

# Monitor system load during concurrent operations
kubectl top nodes
kubectl top pods -n longhorn-system
```

## Exercise 3: Fault Injection & Recovery Analysis

This exercise simulates various failure scenarios to test Longhorn's resilience and recovery mechanisms. It includes network partitions, node failures, and disk corruption.

### 3.1 Simulate Network Partition

```bash
# Create a network partition using iptables
sudo iptables -A INPUT -p tcp --dport 9500 -j DROP
sudo iptables -A OUTPUT -p tcp --sport 9500 -j DROP

# Monitor recovery behavior
kubectl logs -n longhorn-system -l app=longhorn-manager --tail=100 | grep -i "recovery\|fail"

# Restore network connectivity
sudo iptables -D INPUT -p tcp --dport 9500 -j DROP
sudo iptables -D OUTPUT -p tcp --sport 9500 -j DROP
```

### 3.2 Simulate Node Failure

```bash
# Drain a node to simulate failure
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Monitor volume state during node failure
kubectl get pods -A -o wide | grep <node-name>
kubectl get volumes.longhorn.io -A

# Rebalance volumes after node recovery
kubectl uncordon <node-name>
kubectl get pods -A -o wide | grep <node-name>
```

### 3.3 Simulate Disk Failure

```bash
# Create a mock disk failure by unmounting a storage directory
kubectl exec -it -n longhorn-system <manager-pod-name> -- umount /var/lib/longhorn

# Monitor replica state and recovery
kubectl logs -n longhorn-system -l app=longhorn-manager --tail=100 | grep -i "disk\|failure"

# Reattach disk and verify recovery
kubectl exec -it -n longhorn-system <manager-pod-name> -- mount /dev/sdb /var/lib/longhorn
kubectl get pods -A -o wide
```

## Diagnostic Cheat Sheet & Verification Checklist

| Task | Command | Expected Output |
|------|---------|-----------------|
| Verify Longhorn installation | `kubectl get pods -n longhorn-system` | All pods in Running state |
| Check volume status | `kubectl get volumes.longhorn.io -A` | Volumes in Healthy state |
| Monitor controller logs | `kubectl logs -n longhorn-system -l app=longhorn-manager` | No error messages |
| Inspect replica health | `kubectl exec -it -n longhorn-system <manager-pod-name> -- curl -s http://localhost:9500/v1/replicas` | All replicas in Healthy state |
| Validate BPF maps | `sudo bpftool map show` | BPF maps for I/O tracking present |
| Profile I/O performance | `sudo perf record -g -e syscalls:sys_enter_write` | Performance data collected |
| Simulate network partition | `iptables -A INPUT -p tcp --dport 9500 -j DROP` | Recovery logs in manager |
| Test node failure recovery | `kubectl drain <node-name>` | Volumes rebalanced after uncordon |
| Test disk failure recovery | `umount /var/lib/longhorn` | Replica recovery initiated |

This lab provides a comprehensive operational verification framework for Longhorn distributed storage, enabling practitioners to validate system behavior under various conditions and ensure robust operation in production environments.
