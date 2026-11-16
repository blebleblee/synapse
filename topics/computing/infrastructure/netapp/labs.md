# Operational Verification Labs: Netapp

## Objective & Environment Setup

These labs verify the operational integrity of a NetApp ONTAP storage backend integrated with Kubernetes through NetApp Astra Trident, the CSI-compliant dynamic provisioner that bridges container orchestration to ONTAP's NAS and SAN data planes. The objective is not merely to confirm that volumes mount, but to trace the full path from a Kubernetes PersistentVolumeClaim through the CSI gRPC control plane, across the storage network, and into ONTAP's WAFL filesystem — then to stress that path, break it deliberately, and confirm deterministic recovery.

The environment assumes a Kubernetes cluster (version 1.24 or later) with at least one worker node that has network reachability to an ONTAP Storage Virtual Machine via NFS or iSCSI. Trident (version 23.04 or later) must already be installed, though we will verify its installation state as part of the first exercise. The ONTAP cluster should be running version 9.10 or later, with an SVM configured for either NFS export or iSCSI igroup membership. Administrative credentials for the ONTAP cluster are required for deep backend verification but are not needed for most Kubernetes-side diagnostics.

### Toolchain Installation

Install the complete diagnostic toolchain on a worker node with storage connectivity. These tools cover the full verification stack: Kubernetes orchestration, Linux network and block I/O inspection, packet capture, kernel tracing, and NetApp-specific CLI utilities.

```bash
# Core infrastructure diagnostics
sudo apt-get update && sudo apt-get install -y \
    iproute2 ethtool tcpdump strace fio sysstat \
    nfs-common open-iscsi multipath-tools jq socat

# perf and BPF tooling (kernel-specific)
sudo apt-get install -y \
    linux-tools-$(uname -r) linux-tools-generic bpftool

# Helm 3 (if not already present)
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# tridentctl — NetApp Astra Trident CLI
TRIDENT_VERSION="23.10.0"
wget -qO- \
    "https://github.com/NetApp/trident/releases/download/v${TRIDENT_VERSION}/trident-installer-${TRIDENT_VERSION}.tar.gz" \
    | sudo tar xzf - -C /usr/local/bin/ --strip-components=1 \
       trident-installer/tridentctl
sudo chmod +x /usr/local/bin/tridentctl

# Verify every required tool is on PATH
for tool in kubectl ss ip ethtool tcpdump perf strace bpftool \
            fio tridentctl etcdctl helm crictl; do
    command -v "$tool" >/dev/null 2>&1 \
        && echo "OK  $tool  $(command -v "$tool")" \
        || echo "MISSING  $tool"
done
```

### Environment Variables and Baseline Connectivity

Before running any diagnostic, establish the network identity of the ONTAP endpoints and the worker node's storage-facing interface. ONTAP presents two distinct Logical Interface types: the management LIF, which Trident uses for ZAPI or REST API calls to the cluster, and the data LIF, which the client uses for actual NFS or iSCSI traffic. Confusing these is a common source of silent failures, because the management LIF may be reachable while the data LIF is not, or vice versa.

```bash
# Export environment variables (adjust to your deployment)
export ONTAP_MGMT_LIF="10.10.0.10"
export ONTAP_DATA_LIF="10.10.0.20"
export WORKER_IFACE="eth0"
export TRIDENT_NS="trident"
export ONTAP_USER="admin"
export ONTAP_PASS="Netapp123!"
export ONTAP_SVM="svm1"

# Verify L2/L3 connectivity to both LIFs
ping -c 3 -W 2 "$ONTAP_MGMT_LIF"
ping -c 3 -W 2 "$ONTAP_DATA_LIF"

# Inspect the storage-facing interface for link state, speed, and error counters
ip -s link show "$WORKER_IFACE"
ethtool "$WORKER_IFACE"
ethtool -S "$WORKER_IFACE" | grep -E "rx_crc|rx_err|tx_err|rx_drop|tx_drop|rx_length"

# Confirm NFS data port is reachable (TCP 2049)
ss -tipn | grep ":2049"
```

The `ethtool -S` output is the first thing to check when storage performance is degraded. Persistent `rx_crc_errors` or `rx_length_errors` indicate a physical layer problem — bad cable, faulty SFP, or a misconfigured switch port — that will manifest as silent I/O corruption and retransmissions long before any application-layer retry logic fires. A clean baseline means zero errors on all counters. If errors are present, escalate to the network team before proceeding; no amount of Kubernetes or Trident configuration will compensate for a dirty cable.

### Kubernetes Cluster State Verification

Confirm that the cluster itself is healthy and that Trident is installed. The `kubectl get pods -A` command provides a cluster-wide sweep that reveals any pod-level failures across all namespaces, including Trident's.

```bash
# Cluster-wide pod health
kubectl get pods -A -o wide | grep -vE "Running|Completed"

# Node health and taints
kubectl get nodes -o wide
kubectl describe nodes | grep -A5 "Taints\|Conditions\|Allocated"

# Verify Trident Helm release (if installed via Helm)
helm list -n "$TRIDENT_NS"
helm status trident -n "$TRIDENT_NS" | head -20

# Verify Trident pods specifically
kubectl get pods -n "$TRIDENT_NS" -o wide

# Verify storage classes provisioned by csi.netapp.io
kubectl get sc -o json | jq '.items[] | select(.provisioner == "csi.netapp.io") | .metadata.name'

# Verify Trident backends
tridentctl get backends -n "$TRIDENT_NS"
```

A healthy Trident installation shows three categories of pods: the `trident-operator` deployment (one replica), the `trident-controller` deployment (one replica), and the `trident-node-linux` daemonset (one pod per worker node). All should be in the `Running` state with `1/1` readiness. If any pod is in `CrashLoopBackOff`, the first diagnostic step is to inspect the pod events with `kubectl describe pod <name> -n trident` and then check the container logs.

---

## Exercise 1: Live State & Internal Subsystem Inspection

This exercise maps the full control and data plane topology from Kubernetes objects down to the ONTAP volume, leaving no link in the chain unverified. Trident operates as a CSI provisioner: its controller pod handles provisioning, attaching, and snapshot gRPC calls from Kubernetes sidecar containers, while its node daemonset runs on every worker node to handle mount and unmount operations via the CSI identity and node service. Both must be healthy for the volume lifecycle to function, and a failure in either will surface as a stuck PVC or a pod trapped in `ContainerCreating`.

### Step 1: Inspect Trident Operator and CSI Driver Registration

Begin by verifying the operator and its managed resources. The Trident operator is responsible for reconciling the desired state of the Trident installation: if the controller or node daemonset is deleted or fails, the operator restarts it.

```bash
# Inspect the Trident operator deployment
kubectl get deployment -n "$TRIDENT_NS" trident-operator -o wide
kubectl describe deployment -n "$TRIDENT_NS" trident-operator | \
    grep -A10 "Replicas\|Image\|Strategy"

# Inspect the controller deployment and its CSI sidecar containers
kubectl get deployment -n "$TRIDENT_NS" trident-controller -o wide
kubectl get deployment -n "$TRIDENT_NS" trident-controller -o json | \
    jq '.spec.template.spec.containers[] | {name, image}'

# Inspect the node daemonset
kubectl get daemonset -n "$TRIDENT_NS" trident-node-linux -o wide
kubectl get daemonset -n "$TRIDENT_NS" trident-node-linux -o json | \
    jq '.spec.template.spec.containers[] | {name, image}'

# Verify the CSI driver object — kubelet uses this to route CSI gRPC calls
kubectl get csidriver csi.netapp.io -o yaml
```

The `csidriver` object tells Kubernetes how to interact with the driver. For NFS-backed volumes, `attachRequired: false` is common because NFS mounts do not require a separate controller-side attach operation; the node plugin handles the mount directly. For iSCSI-backed volumes, `attachRequired: true` is mandatory because the node must log into the iSCSI target and present a block device before the filesystem can be mounted. The `podInfoOnMount` field should be `true` so that Trident receives pod metadata (name, namespace, UID) in the mount request, which it uses for volume ownership tracking.

### Step 2: Verify the CSI Node Plugin Socket

The kubelet discovers CSI drivers through a Unix domain socket in its plugin directory. On each worker node, the Trident node daemonset registers itself with the kubelet by creating a socket file and a registration file. If the socket is missing or stale, the kubelet cannot route mount requests to Trident, and any new pod scheduled on that node with a NetApp-backed PVC will fail to start.

```bash
# Verify the CSI socket exists on the current node
ls -la /var/lib/kubelet/plugins/csi.netapp.io/
# Expected: csi.sock (Unix domain socket file)

# Verify the socket file type
file /var/lib/kubelet/plugins/csi.netapp.io/csi.sock
# Expected: "socket"

# Check the kubelet plugin registration record
ls -la /var/lib/kubelet/plugins_registry/ | grep netapp

# Use crictl to find the Trident node container and verify it is running
sudo crictl ps | grep trident
TRIDENT_CTR_ID=$(sudo crictl ps --state Running | grep trident-main | awk '{print $1}')
echo "Trident node container ID: $TRIDENT_CTR_ID"

# Inspect the container for its host PID and runtime details
sudo crictl inspect "$TRIDENT_CTR_ID" | \
    jq '{pid: .info.pid, name: .status.metadata.name, state: .status.state}'

# Verify the socket is accepting connections by checking its inode
ls -i /var/lib/kubelet/plugins/csi.netapp.io/csi.sock
```

### Step 3: Verify Backend Configuration and Storage Classes

Trident backends define the connection to ONTAP. In Trident 21.04 and later, backends are managed as `TridentBackendConfig` custom resources. The backend configuration includes the ONTAP management LIF, data LIF, SVM name, and credentials. A backend in a non-online state means Trident cannot provision or manage volumes on that ONTAP system.

```bash
# List all Trident backends with their state
tridentctl get backends -n "$TRIDENT_NS" -o json | \
    jq '.items[] | {name, driver: .config.storageDriverName, state: .state, online: .online}'

# Detailed backend inspection — verify ONTAP connection parameters
tridentctl get backend ontap-nas-backend -n "$TRIDENT_NS" -o yaml

# Check for any backend in a non-online state
tridentctl get backends -n "$TRIDENT_NS" -o json | \
    jq '.items[] | select(.online != true) | {name, state, error: .state}'

# Inspect storage classes provisioned by csi.netapp.io
kubectl get sc -o json | \
    jq '.items[] | select(.provisioner == "csi.netapp.io") | {name, parameters, allowVolumeExpansion}'

# Detailed storage class view
kubectl get sc ontap-nfs -o yaml
```

If a backend shows a non-online state, the most common causes are authentication failure (wrong credentials or expired password), management LIF unreachability (network firewall or routing issue), or an SVM configuration mismatch (wrong SVM name or SVM is stopped). Check the Trident controller logs for the specific error:

```bash
kubectl logs -n "$TRIDENT_NS" deployment/trident-controller -c trident-main --tail=100 | \
    grep -E "ERROR|WARN|backend|failed"
```

### Step 4: Trace PVC to PV to ONTAP Volume

This is the critical diagnostic path: trace a single PersistentVolumeClaim from the Kubernetes API through Trident's provisioning to the actual ONTAP volume. First, create a test PVC if one does not already exist.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: netapp-verify-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: ontap-nfs
  resources:
    requests:
      storage: 50Gi
EOF
```

Wait for the PVC to bind and then trace the full chain:

```bash
# Wait for PVC to reach Bound state
kubectl wait pvc netapp-verify-pvc --for=condition=Bound --timeout=60s

# Extract the PV name bound to this PVC
PV_NAME=$(kubectl get pvc netapp-verify-pvc -o jsonpath='{.spec.volumeName}')
echo "Bound PV: $PV_NAME"

# Extract the CSI volume handle — this is Trident's internal volume name
VOLUME_HANDLE=$(kubectl get pv "$PV_NAME" -o jsonpath='{.spec.csi.volumeHandle}')
echo "Trident volume handle: $VOLUME_HANDLE"

# Query Trident for the volume details
tridentctl get volume "$VOLUME_HANDLE" -n "$TRIDENT_NS" -o json | \
    jq '{name, backend, accessProtocol: .config.accessProtocol, size: .config.size, state: .state}'

# Query ONTAP REST API to confirm the volume exists on the array
ONTAP_VOL_NAME=$(tridentctl get volume "$VOLUME_HANDLE" -n "$TRIDENT_NS" \
    -o json | jq -r '.config.name')

curl -s -u "${ONTAP_USER}:${ONTAP_PASS}" \
    "https://${ONTAP_MGMT_LIF}/api/storage/volumes?name=${ONTAP_VOL_NAME}&fields=name,size,state,junction_path,svm.name" \
    -k | jq '.records[0]'
```

The ONTAP REST API response should confirm the volume exists, its state is `online`, the junction path is set (for NFS volumes, this is where the export is mounted in the SVM's namespace), and the SVM name matches the backend configuration. If the volume exists in ONTAP but the PVC was stuck in `Pending`, the problem is likely in the CSI gRPC call chain. Check the `csi-provisioner` sidecar logs in the Trident controller pod:

```bash
kubectl logs -n "$TRIDENT_NS" deployment/trident-controller -c csi-provisioner --tail=30
```

### Step 5: Verify the Data Plane Mount on the Worker Node

Once a pod is consuming the PVC, verify the actual NFS mount on the node. The kernel NFS client creates an entry in `/proc/mounts` when a volume is mounted, and the TCP connection to the ONTAP data LIF appears in the `ss` output.

```bash
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: netapp-verify-pod
  namespace: default
spec:
  containers:
    - name: app
      image: nginx:1.25
      volumeMounts:
        - name: data
          mountPath: /mnt/netapp
      command: ["sleep", "3600"]
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: netapp-verify-pvc
EOF

kubectl wait pod netapp-verify-pod --for=condition=Ready --timeout=30s

# Identify the node hosting the pod
NODE_NAME=$(kubectl get pod netapp-verify-pod -o jsonpath='{.spec.nodeName}')
echo "Pod scheduled on node: $NODE_NAME"

# If this is the current node, inspect the mount directly
grep "netapp\|nfs" /proc/mounts | grep "$(echo "$PV_NAME" | cut -c1-12)"

# Show the full mount entry with all NFS mount options
findmnt -T /mnt/netapp -o SOURCE,TARGET,FSTYPE,OPTIONS -n

# Inspect NFS mount statistics (retransmissions, read/write sizes)
nfsstat -m 2>/dev/null | grep -A10 "$(echo "$PV_NAME" | cut -c1-12)"

# Verify active NFS TCP connections with internal TCP state and memory
ss -tipm | grep ":2049"
```

The `ss -tipm` output reveals the TCP-level health of the NFS connection. Look for the `rtt` (round-trip time) and `rto` (retransmission timeout) values in the internal TCP information block. A healthy connection shows a stable RTT with zero retransmissions. If `retrans` is non-zero, the network path is experiencing packet loss or congestion, which will manifest as elevated I/O latency in application-level measurements.

For iSCSI-backed volumes, the verification path differs. Instead of an NFS mount entry, you should see an iSCSI session and a multipath device:

```bash
# Verify the iSCSI session is active
iscsiadm -m session

# Inspect multipath devices mapped to ONTAP targets
multipath -ll | grep -A5 -i netapp

# Verify the block device is present and mounted
lsblk -o NAME,SIZE,MOUNTPOINT,TYPE,MODEL | grep -B1 -A1 "$(echo "$PV_NAME" | cut -c1-8)"

# Check the SCSI device queue depth and I/O scheduler
DEV_NAME=$(lsblk -n -o NAME | grep -m1 "$(multipath -ll | grep -oP 'dm-\d+' | head -1)")
cat /sys/block/"$DEV_NAME"/queue/scheduler
cat /sys/block/"$DEV_NAME"/queue/nr_requests
```

### Step 6: Verify etcd Persistence of Storage Objects

All Kubernetes objects — PVCs, PVs, storage classes, and Trident CRDs — are persisted in etcd. Verifying their state in etcd is useful when diagnosing cases where the API server reports an object but its state is inconsistent with the underlying data store, or when the MVCC revision history reveals pathological update churn.

```bash
# Define etcd connection parameters (adjust to your cluster)
export ETCD_ENDPOINT="https://127.0.0.1:2379"
export ETCD_CA="/etc/kubernetes/pki/etcd/ca.crt"
export ETCD_CERT="/etc/kubernetes/pki/etcd/server.crt"
export ETCD_KEY="/etc/kubernetes/pki/etcd/server.key"

# Verify etcd cluster health
etcdctl --endpoints="$ETCD_ENDPOINT" \
    --cacert="$ETCD_CA" --cert="$ETCD_CERT" --key="$ETCD_KEY" \
    endpoint health

# List all storage-related keys in etcd (default Kubernetes prefix is /registry)
etcdctl --endpoints="$ETCD_ENDPOINT" \
    --cacert="$ETCD_CA" --cert="$ETCD_CERT" --key="$ETCD_KEY" \
    get --prefix "/registry/storageclasses" --keys-only

# Verify the PVC object is persisted
etcdctl --endpoints="$ETCD_ENDPOINT" \
    --cacert="$ETCD_CA" --cert="$ETCD_CERT" --key="$ETCD_KEY" \
    get "/registry/persistentvolumeclaims/default/netapp-verify-pvc" | head -5

# Verify the PV object and its MVCC revision
etcdctl --endpoints="$ETCD_ENDPOINT" \
    --cacert="$ETCD_CA" --cert="$ETCD_CERT" --key="$ETCD_KEY" \
    get "/registry/persistentvolumes/${PV_NAME}" -w json | \
    jq '{revision: .header.revision, value_length: (.data | length)}'

# Count total CSI-related objects in etcd
echo "StorageClasses: $(etcdctl --endpoints="$ETCD_ENDPOINT" \
    --cacert="$ETCD_CA" --cert="$ETCD_CERT" --key="$ETCD_KEY" \
    get --prefix "/registry/storageclasses" --keys-only | grep -c .)"

echo "PersistentVolumes: $(etcdctl --endpoints="$ETCD_ENDPOINT" \
    --cacert="$ETCD_CA" --cert="$ETCD_CERT" --key="$ETCD_KEY" \
    get --prefix "/registry/persistentvolumes" --keys-only | grep -c .)"

echo "VolumeAttachments: $(etcdctl --endpoints="$ETCD_ENDPOINT" \
    --cacert="$ETCD_CA" --cert="$ETCD_CERT" --key="$ETCD_KEY" \
    get --prefix "/registry/volumeattachments" --keys-only | grep -c .)"
```

The MVCC revision number from etcd tells you how many times the key has been modified since creation. A PV that has been repeatedly attached, detached, and expanded will have a higher revision than a freshly provisioned one. An abnormally high revision count for a recently created PV can indicate a pathological reattachment loop caused by a flaky CSI driver or kubelet.

### Step 7: strace the I/O Path

To understand what happens at the system call level when an application performs I/O on a NetApp-backed volume, use `strace` on the application container's process. This reveals the actual `read`, `write`, `openat`, and `close` calls, along with their return values and any errors.

```bash
# Find the container's host PID using crictl
CONTAINER_ID=$(sudo crictl ps --state Running | grep "netapp-verify-pod" | awk '{print $1}')
HOST_PID=$(sudo crictl inspect "$CONTAINER_ID" | jq -r '.info.pid')
echo "Container host PID: $HOST_PID"

# Trace I/O system calls for 10 seconds while generating I/O
kubectl exec netapp-verify-pod -- sh -c 'dd if=/dev/zero of=/mnt/netapp/strace-test bs=4k count=1000 oflag=direct' &
sudo strace -e trace=openat,read,write,close,fsync -p "$HOST_PID" -c -f 2>&1 | tail -20
wait

# Verify the test file was written
kubectl exec netapp-verify-pod -- ls -la /mnt/netapp/strace-test
kubectl exec netapp-verify-pod -- rm /mnt/netapp/strace-test
```

The strace summary shows how many `write` syscalls were issued, their total time, and any errors. For NFS-backed volumes, each `write` may translate to one or more NFS WRITE operations over the network. A high syscall count for a small total data volume indicates the application is issuing many small writes rather than batching, which is inefficient for network storage.

---

## Exercise 2: Benchmarking & Saturation Profiling

Verifying that a volume mounts is necessary but insufficient. Storage performance is characterized by three orthogonal axes: IOPS (operations per second), throughput (bytes per second), and latency (time per operation). A volume that delivers acceptable IOPS at 4K block sizes may saturate at 256K block sizes, or it may show low average latency with a long tail at the 99th percentile. This exercise instruments the storage path to surface those characteristics and identify where bottlenecks occur: in the application, in the kernel block layer, in the network protocol, or in ONTAP itself.

### Step 1: Comprehensive I/O Benchmark with fio

The Flexible I/O Tester (`fio`) is the industry standard for storage benchmarking because it reproduces specific workload patterns with precise control over block size, queue depth, concurrency, and access pattern. The following job file runs four distinct workload profiles sequentially: sequential read (large block, high throughput), random read (small block, high IOPS), sequential write, and random write. Each profile runs for 60 seconds with a 10-second ramp time to stabilize the working set before measurement begins.

```bash
# Ensure fio is installed
which fio || sudo apt-get install -y fio

# Write the fio job file
cat <<'EOF' > /tmp/netapp-fio-profile.fio
[global]
ioengine=libaio
direct=1
runtime=60
time_based=1
ramp_time=10
group_reporting=1
directory=/mnt/netapp
filename_format=fio-test.$jobnum.$filenum

[seq-read]
rw=read
bs=256k
size=1G
numjobs=1
iodepth=8

[rand-read]
rw=randread
bs=4k
size=1G
numjobs=4
iodepth=32

[seq-write]
rw=write
bs=256k
size=1G
numjobs=1
iodepth=8

[rand-write]
rw=randwrite
bs=4k
size=1G
numjobs=4
iodepth=32

[rand-read-1m]
rw=randread
bs=1m
size=1G
numjobs=2
iodepth=16
EOF

# Execute the benchmark (approximately 5 minutes total)
sudo fio /tmp/netapp-fio-profile.fio --output-format=json+ > /tmp/netapp-fio-results.json 2>/dev/null

# Extract summary metrics for each job
jq '.jobs[] | {
    jobname,
    read_iops: .read.iops,
    read_bw_mbs: (.read.bw / 1024 | floor),
    read_lat_us: (.read.lat_ns / 1000 | floor),
    write_iops: .write.iops,
    write_bw_mbs: (.write.bw / 1024 | floor),
    write_lat_us: (.write.lat_ns / 1000 | floor)
}' /tmp/netapp-fio-results.json

# Extract latency percentile distribution for random 4K writes
jq '.jobs[] | select(.jobname == "rand-write") | .write.latency_ns | {
    p50_ns: .ns_50000,
    p90_ns: .ns_100000,
    p99_ns: .ns_1000000,
    p999_ns: .ns_10000000
}' /tmp/netapp-fio-results.json
```

Interpreting the results requires context about ONTAP's architecture. ONTAP's WAFL filesystem is log-structured: writes are first written to NVRAM (non-volatile RAM) and acknowledged to the client, then lazily flushed to disk. This means write latency is dominated by the network round trip and the NVRAM acknowledgment path, not by disk seek time. Random 4K write IOPS on an ONTAP NAS volume should typically be in the range of 5,000 to 50,000 depending on the backend model and configuration. Read latency is more variable because reads may require a disk access if the data is not cached in WAFL's buffer cache or in the client's page cache. With `direct=1` (O_DIRECT), the page cache is bypassed, so every read goes over the network to ONTAP.

### Step 2: Profile the Kernel I/O Path with perf

While fio characterizes the application-visible performance, `perf` traces the kernel block I/O subsystem to identify where time is spent in the I/O path. The block layer sits between the filesystem and the network storage protocol. For NFS, the block layer is thin because NFS writes go through the NFS client directly, but for iSCSI-backed volumes, the block layer manages the request queue to the SCSI device, which maps to an iSCSI session.

```bash
# List available block and NFS tracepoints
sudo perf list 'block:*' | head -20
sudo perf list 'nfs:*' | head -20

# Start a random write workload in the background
sudo fio --name=randwrite --ioengine=libaio --direct=1 --bs=4k \
    --rw=randwrite --size=1G --runtime=30 --time_based \
    --directory=/mnt/netapp --numjobs=1 --iodepth=32 &
FIO_PID=$!

# Trace block I/O events — count issue and completion events
sudo perf stat -e block:block_rq_issue,block:block_rq_complete,block:block_rq_insert -a sleep 15

# Trace NFS-specific events (for NFS-backed volumes)
sudo perf stat -e nfs:nfs_initiate_read,nfs:nfs_readpage_done,nfs:nfs_initiate_write,nfs:nfs_writepage_done -a sleep 15

# Record block I/O completion events for detailed analysis
sudo perf record -e block:block_rq_complete -a -- sleep 15
sudo perf report --stdio | head -50

kill $FIO_PID 2>/dev/null
wait $FIO_PID 2>/dev/null
```

If the count of `block:block_rq_issue` events is significantly higher than `block:block_rq_complete` events during the measurement window, the block layer is queuing requests faster than the backend can complete them. This indicates that ONTAP is the bottleneck, not the client. Conversely, if issue and completion counts are balanced but latency is high, the bottleneck is in the network path or in ONTAP's processing pipeline.

### Step 3: Capture Storage Protocol Traffic with tcpdump

Network-level inspection of the storage protocol reveals protocol-level latency, retransmissions, and unexpected behavior that are invisible at the kernel tracepoint level. For NFS, the key protocol is NFSv4 over TCP 2049. Each NFS operation consists of a request packet and a reply packet, and the time delta between them is the round-trip latency for that operation.

```bash
# Start a random write workload
sudo fio --name=randwrite --ioengine=libaio --direct=1 --bs=4k \
    --rw=randwrite --size=1G --runtime=30 --time_based \
    --directory=/mnt/netapp --numjobs=1 --iodepth=16 &
FIO_PID=$!

# Capture NFS traffic with high-precision timestamps
sudo tcpdump -i "$WORKER_IFACE" -nn -tttt -c 10000 "port 2049" -w /tmp/nfs-fio.pcap &
TCPDUMP_PID=$!

# Let the capture run for 20 seconds
sleep 20
kill $FIO_PID 2>/dev/null
wait $FIO_PID 2>/dev/null
kill $TCPDUMP_PID 2>/dev/null
wait $TCPDUMP_PID 2>/dev/null

# Analyze the capture — count NFS operations by type
sudo tcpdump -r /tmp/nfs-fio.pcap -nn | \
    grep -oP 'NFS v[34] \w+' | sort | uniq -c | sort -rn | head -10

# Check for TCP retransmissions (indicates network congestion)
RETRANS=$(sudo tcpdump -r /tmp/nfs-fio.pcap -nn | grep -ci "retransmission\|dup ack")
echo "TCP retransmissions: $RETRANS"

# Extract NFS WRITE operation latencies (request to reply delta)
sudo tcpdump -r /tmp/nfs-fio.pcap -nn -tttt | \
    awk '/NFS v[34] WRITE.*call/ {split($0,a,"xid"); xid=a[2]; gsub(/[^0-9a-f]/,"",xid);
         start[xid]=$1" "$2}
         /NFS v[34] WRITE.*reply/ {split($0,a,"xid"); xid=a[2]; gsub(/[^0-9a-f]/,"",xid);
         if (xid in start) {print "WRITE latency (raw):", $1" "$2, start[xid]}}' | head -20

# Summarize TCP connection statistics from the capture
sudo tcpdump -r /tmp/nfs-fio.pcap -nn | \
    awk '{split($3,src,":"); split($5,dst,":"); print src[1]" -> "dst[1]}' | \
    sort | uniq -c | sort -rn | head -5
```

A high retransmission count means TCP is struggling to deliver data reliably, which will cause I/O stalls as the protocol waits for retransmission timeouts. On a healthy 10GbE or 25GbE link with a clean switch path, retransmissions should be zero or near-zero during a sustained workload.

For iSCSI-backed volumes, the capture and analysis differ:

```bash
# Start a random write workload
sudo fio --name=randwrite --ioengine=libaio --direct=1 --bs=4k \
    --rw=randwrite --size=1G --runtime=30 --time_based \
    --directory=/mnt/netapp --numjobs=1 --iodepth=16 &
FIO_PID=$!

# Capture iSCSI traffic (TCP port 3260)
sudo tcpdump -i "$WORKER_IFACE" -nn -c 10000 "port 3260" -w /tmp/iscsi-fio.pcap &
TCPDUMP_PID=$!

sleep 20
kill $FIO_PID 2>/dev/null
wait $FIO_PID 2>/dev/null
kill $TCPDUMP_PID 2>/dev/null
wait $TCPDUMP_PID 2>/dev/null

# Analyze SCSI command distribution
sudo tcpdump -r /tmp/iscsi-fio.pcap -nn -V 2>/dev/null | \
    grep -oP 'SCSI (?:Read|Write|Read10|Write10|Read16|Write16)' | \
    sort | uniq -c | sort -rn

# Check for TCP retransmissions on the iSCSI connection
sudo tcpdump -r /tmp/iscsi-fio.pcap -nn | grep -ci "retransmission"
```

### Step 4: Network Interface Saturation Analysis

During the fio workload, monitor the network interface for saturation. ONTAP volumes are backed by network, so I/O throughput is bounded by interface bandwidth. A 10GbE link can theoretically deliver approximately 1,250 MB/s, but practical throughput is typically 70 to 80 percent of that due to protocol overhead, TCP windowing, and NFS RPC framing.

```bash
# Start a sustained sequential write workload (high throughput)
sudo fio --name=seqwrite --ioengine=libaio --direct=1 --bs=1m \
    --rw=write --size=4G --runtime=60 --time_based \
    --directory=/mnt/netapp --numjobs=4 --iodepth=8 &
FIO_PID=$!

# Monitor interface statistics every 5 seconds for 30 seconds
for i in $(seq 1 6); do
    echo "=== Sample $i ($(date +%H:%M:%S)) ==="
    ip -s link show "$WORKER_IFACE" | tail -5
    ethtool -S "$WORKER_IFACE" | grep -E "rx_bytes|tx_bytes|rx_packets|tx_packets"
    echo ""
    sleep 5
done

# Calculate throughput from interface counters
RX_START=$(ethtool -S "$WORKER_IFACE" | grep "rx_bytes" | head -1 | awk '{print $2}')
TX_START=$(ethtool -S "$WORKER_IFACE" | grep "tx_bytes" | head -1 | awk '{print $2}')
sleep 10
RX_END=$(ethtool -S "$WORKER_IFACE" | grep "rx_bytes" | head -1 | awk '{print $2}')
TX_END=$(ethtool -S "$WORKER_IFACE" | grep "tx_bytes" | head -1 | awk '{print $2}')

RX_MBPS=$(( (RX_END - RX_START) / 10 / 1024 / 1024 ))
TX_MBPS=$(( (TX_END - TX_START) / 10 / 1024 / 1024 ))
echo "RX throughput: ${RX_MBPS} MB/s"
echo "TX throughput: ${TX_MBPS} MB/s"

# Inspect TCP connection memory during the workload
ss -tipm | grep ":2049" | head -5

kill $FIO_PID 2>/dev/null
wait $FIO_PID 2>/dev/null
```

The `ss -tipm` output during the workload shows the TCP send and receive buffer occupancy. If the send buffer (`Send-Q`) is consistently near the window size, the client is generating data faster than ONTAP can absorb it, which means the bottleneck is on the ONTAP side. If the receive buffer (`Recv-Q`) is near zero and the RTT is stable, the client is waiting for ONTAP to respond, which confirms the bottleneck is on the storage side.

### Step 5: Inspect BPF Programs for I/O Tracing

The kernel's BPF subsystem can attach tracepoint programs to block I/O events for low-overhead, continuous monitoring. If any BPF programs are already loaded (by system daemons like `bpftrace`, `bcc`, or `tetragon`), `bpftool` can inspect them. If no I/O tracing program is loaded, `perf trace` provides a similar capability through the perf event subsystem.

```bash
# List all loaded BPF programs
sudo bpftool prog show

# Filter for block I/O or network-related programs
sudo bpftool prog show | grep -B2 -A5 "block\|nfs\|tcp\|skb"

# Inspect BPF program maps (if block I/O programs are loaded)
PROG_ID=$(sudo bpftool prog show | grep -B5 "block_rq" | grep -oP '^\d+:' | head -1 | tr -d ':')
if [ -n "$PROG_ID" ]; then
    sudo bpftool prog show id "$PROG_ID"
    sudo bpftool map show
fi

# Use perf trace to trace block I/O completion events with timing
sudo perf trace -e block:block_rq_complete -a sleep 10 2>&1 | head -30

# If BCC tools are available, use biolatency for a histogram
if command -v biolatency &>/dev/null; then
    sudo biolatency -d 10 2>&1
fi
```

---

## Exercise 3: Fault Injection & Recovery Analysis

The previous exercises verified the system in a steady state. This exercise deliberately breaks the storage path to verify that Kubernetes and Trident recover deterministically. Each fault injection tests a specific failure mode in the CSI lifecycle, and recovery should be automatic — no manual intervention should be required if the system is configured correctly. If recovery is not automatic, the fault injection has surfaced a configuration weakness that should be addressed before it occurs in production.

### Step 1: Kill the Trident Node Daemonset Pod

The Trident node pod handles mount and unmount operations on each worker node. Killing it forces Kubernetes to restart it through the daemonset controller. During the restart window, any new PVC mounts on that node will fail, but existing mounts should remain functional because the kernel NFS mount persists independently of the CSI driver process.

```bash
# Identify the Trident node pod on the current node
NODE_NAME=$(hostname)
TRIDENT_NODE_POD=$(kubectl get pods -n "$TRIDENT_NS" -l app=trident-node-linux \
    --field-selector spec.nodeName="$NODE_NAME" \
    -o jsonpath='{.items[0].metadata.name}')
echo "Trident node pod: $TRIDENT_NODE_POD"

# Verify a test file exists before the kill (written in Exercise 1)
kubectl exec netapp-verify-pod -- ls -la /mnt/netapp/survival-test 2>/dev/null || \
    kubectl exec netapp-verify-pod -- touch /mnt/netapp/survival-test

# Delete the pod — Kubernetes daemonset controller will restart it
kubectl delete pod -n "$TRIDENT_NS" "$TRIDENT_NODE_POD"

# Measure restart time
START_TIME=$(date +%s)
while ! kubectl get pods -n "$TRIDENT_NS" -l app=trident-node-linux \
    --field-selector spec.nodeName="$NODE_NAME" \
    -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q Running; do
    sleep 1
done
END_TIME=$(date +%s)
echo "Trident node pod restarted in $((END_TIME - START_TIME)) seconds"

# Wait for the pod to be fully ready
kubectl wait pod -n "$TRIDENT_NS" -l app=trident-node-linux \
    --field-selector spec.nodeName="$NODE_NAME" \
    --for=condition=Ready --timeout=60s

# Verify the CSI socket is re-registered
ls -la /var/lib/kubelet/plugins/csi.netapp.io/csi.sock

# Verify existing mounts survived the restart
kubectl exec netapp-verify-pod -- ls /mnt/netapp/survival-test

# Verify I/O still works after restart
kubectl exec netapp-verify-pod -- sh -c 'echo "post-restart $(date)" > /mnt/netapp/survival-test && cat /mnt/netapp/survival-test'
```

The existing mount survives because the NFS mount is managed by the kernel, not by the Trident process. Trident's role in the mount operation is to call the `mount` syscall with the correct parameters, but once the mount is established, the kernel maintains it independently. The Trident node pod is only needed for new mount and unmount operations.

### Step 2: Network Latency Injection

Inject artificial latency between the worker node and the ONTAP data LIF using `tc` (traffic control) with the `netem` (network emulator) qdisc. This tests how the NFS or iSCSI client handles degraded network conditions. A well-configured system should detect the degradation and either tolerate it with elevated latency or fail over to a secondary data LIF if multipathing is configured.

```bash
# Baseline: verify I/O is working and measure baseline latency
kubectl exec netapp-verify-pod -- sh -c \
    'time dd if=/dev/zero of=/mnt/netapp/lat-test bs=4k count=1000 oflag=direct' 2>&1

# Inject 500ms one-way delay (1 second round trip) on the storage interface
sudo tc qdisc del dev "$WORKER_IFACE" root 2>/dev/null
sudo tc qdisc add dev "$WORKER_IFACE" root netem delay 500ms

# Verify the qdisc is in place
tc qdisc show dev "$WORKER_IFACE"

# Test I/O under degraded conditions — this should be very slow but may still succeed
timeout 30 kubectl exec netapp-verify-pod -- sh -c \
    'time dd if=/dev/zero of=/mnt/netapp/lat-test-2 bs=4k count=100 oflag=direct' 2>&1
echo "Exit code: $?"

# Check NFS mount state during latency
cat /proc/mounts | grep "$(echo "$PV_NAME" | cut -c1-12)" | head -1

# Inspect TCP connection state under latency
ss -tipn | grep ":2049"

# Remove the latency injection
sudo tc qdisc del dev "$WORKER_IFACE" root

# Verify recovery — I/O should return to normal
kubectl exec netapp-verify-pod -- sh -c \
    'time dd if=/dev/zero of=/mnt/netapp/lat-test-3 bs=4k count=1000 oflag=direct' 2>&1
```

With 500ms one-way latency, each NFS operation requires at least 1 second round trip. With `direct=1`, each 4K write is a synchronous NFS WRITE RPC, so 100 writes should take at least 100 seconds. If the `timeout 30` command kills the `dd` before it completes, the NFS client is correctly waiting for each operation to complete (no pipelining), which is expected behavior for direct I/O. If the `dd` completes quickly despite the latency, something is wrong — either the qdisc is not applied, or the traffic is not flowing through the expected interface.

### Step 3: Network Packet Loss Injection

Inject packet loss to simulate a more severe network degradation. With 50 percent packet loss, NFS operations will stall because TCP cannot reliably deliver data. The NFS client should eventually time out and the mount may become stale, but it should recover once the packet loss is removed.

```bash
# Baseline I/O verification
kubectl exec netapp-verify-pod -- ls /mnt/netapp/ 2>&1

# Inject 50% packet loss
sudo tc qdisc del dev "$WORKER_IFACE" root 2>/dev/null
sudo tc qdisc add dev "$WORKER_IFACE" root netem loss 50%

# Verify the qdisc
tc qdisc show dev "$WORKER_IFACE"

# I/O should stall or fail
timeout 10 kubectl exec netapp-verify-pod -- ls /mnt/netapp/ 2>&1
echo "I/O exit code under 50% loss: $?"

# Check the NFS mount state — it may show as stale
cat /proc/mounts | grep "$(echo "$PV_NAME" | cut -c1-12)"
ss -tipn | grep ":2049"

# Remove packet loss
sudo tc qdisc del dev "$WORKER_IFACE" root

# Wait for NFS to recover (NFSv4 lease recovery typically takes 60-90 seconds)
echo "Waiting for NFS recovery..."
sleep 90

# Verify recovery
kubectl exec netapp-verify-pod -- ls /mnt/netapp/ 2>&1
echo "Recovery exit code: $?"

# Test I/O after recovery
kubectl exec netapp-verify-pod -- sh -c \
    'echo "recovered $(date)" > /mnt/netapp/recovery-test && cat /mnt/netapp/recovery-test'
```

NFSv4 uses leases to maintain consistency. When the network is partitioned, the client's lease expires on the server side, and the server may recall delegations. When the network is restored, the client must re-establish its lease before I/O can resume. This recovery is handled by the kernel NFS client automatically, but it takes time proportional to the lease period (typically 30 to 90 seconds). If the mount does not recover after 120 seconds, the client may need a forced unmount and remount, which indicates a configuration problem with the NFS mount options (insufficient `timeo` or `retrans` values).

### Step 4: Pod Deletion and Volume Reattachment

Deleting the consuming pod forces the CSI driver to unmount the volume. When a new pod is scheduled, it must remount. This tests the full unmount to mount cycle through the CSI node service and the Kubernetes attach/detach controller.

```bash
# Record the current PV attachment state
PV_NAME=$(kubectl get pvc netapp-verify-pvc -o jsonpath='{.spec.volumeName}')
kubectl get volumeattachment -o json | \
    jq --arg pv "$PV_NAME" \
    '.items[] | select(.spec.source.persistentVolumeName == $pv) | {name: .metadata.name, attached: .status.attached, node: .spec.node}'

# Delete the pod
kubectl delete pod netapp-verify-pod --grace-period=0 --force

# Wait for the volume to detach
sleep 5
VA_COUNT=$(kubectl get volumeattachment -o json | \
    jq --arg pv "$PV_NAME" \
    '[.items[] | select(.spec.source.persistentVolumeName == $pv)] | length')
echo "VolumeAttachments for this PV after pod deletion: $VA_COUNT"

# Create a new pod to trigger remount
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: netapp-verify-pod-2
  namespace: default
spec:
  containers:
    - name: app
      image: nginx:1.25
      volumeMounts:
        - name: data
          mountPath: /mnt/netapp
      command: ["sleep", "3600"]
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: netapp-verify-pvc
EOF

# Measure remount time
START_NS=$(date +%s%N)
kubectl wait pod netapp-verify-pod-2 --for=condition=Ready --timeout=60s
END_NS=$(date +%s%N)
echo "Pod start (including volume remount): $(( (END_NS - START_NS) / 1000000 )) ms"

# Verify data persisted across the remount cycle
kubectl exec netapp-verify-pod-2 -- cat /mnt/netapp/survival-test

# Verify the new volumeattachment
kubectl get volumeattachment -o json | \
    jq --arg pv "$PV_NAME" \
    '.items[] | select(.spec.source.persistentVolumeName == $pv) | {name: .metadata.name, attached: .status.attached, node: .spec.node}'
```

The remount time is the critical metric here. For NFS, it should be under 5 seconds: the CSI node plugin calls the `mount` syscall, which negotiates the NFS handshake with ONTAP, and the pod starts. For iSCSI, the remount time may be longer (10 to 30 seconds) because the node must log into the iSCSI target, scan for the SCSI device, and wait for multipath to converge before mounting the filesystem.

### Step 5: Volume Expansion

Volume expansion tests the CSI `ControllerExpandVolume` and `NodeExpandVolume` gRPC calls. Trident must call the ONTAP REST API to grow the volume, and then the node plugin must trigger a filesystem resize on the worker node. The `allowVolumeExpansion: true` field in the storage class must be set for this to work.

```bash
# Current PVC size
CURRENT_SIZE=$(kubectl get pvc netapp-verify-pvc -o jsonpath='{.spec.resources.requests.storage}')
echo "Current PVC size: $CURRENT_SIZE"

# Request expansion from 50Gi to 100Gi
kubectl patch pvc netapp-verify-pvc --type=merge -p \
    '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Poll for expansion completion
echo "Waiting for volume expansion..."
for i in $(seq 1 12); do
    CAPACITY=$(kubectl get pvc netapp-verify-pvc \
        -o jsonpath='{.status.capacity.storage}' 2>/dev/null)
    echo "  Attempt $i: capacity=$CAPACITY"
    if [ "$CAPACITY" = "100Gi" ]; then
        echo "Expansion complete after $((i * 5)) seconds"
        break
    fi
    sleep 5
done

# Verify the filesystem inside the pod sees the expanded size
kubectl exec netapp-verify-pod-2 -- df -h /mnt/netapp

# Verify ONTAP reflects the expanded volume size
ONTAP_VOL_NAME=$(tridentctl get volume \
    "$(kubectl get pv "$PV_NAME" -o jsonpath='{.spec.csi.volumeHandle}')" \
    -n "$TRIDENT_NS" -o json | jq -r '.config.name')

curl -s -u "${ONTAP_USER}:${ONTAP_PASS}" \
    "https://${ONTAP_MGMT_LIF}/api/storage/volumes?name=${ONTAP_VOL_NAME}&fields=name,size" \
    -k | jq '.records[0] | {name, size_bytes: .size}'

# Check the CSI resizer sidecar logs for the expansion operation
kubectl logs -n "$TRIDENT_NS" deployment/trident-controller -c csi-resizer --tail=20
```

Volume expansion involves two separate operations. The `ControllerExpandVolume` gRPC call tells Trident to grow the ONTAP volume, which is a metadata-only operation in WAFL (it simply increases the volume's size attribute). The `NodeExpandVolume` gRPC call tells the node plugin to run `resize2fs` (or `xfs_growfs` for XFS) on the mounted filesystem so the kernel sees the new size. If the PVC shows the new capacity but `df` inside the pod shows the old size, the node-side expansion failed. Check the Trident node pod logs for the `resize2fs` error.

### Step 6: CSI Snapshot Creation and Restoration

Trident supports CSI volume snapshots, which map to ONTAP Snapshot copies. A Snapshot copy in ONTAP is a point-in-time, read-only, space-efficient copy of the volume's data that is stored in the volume's Snapshot copy reserve. It is created by locking the WAFL consistency point, so the snapshot is crash-consistent without requiring any application-level quiescing.

```bash
# Verify or create a VolumeSnapshotClass for the NetApp CSI driver
kubectl get volumesnapshotclass -o json | \
    jq '.items[] | select(.driver == "csi.netapp.io") | .metadata.name'

# Create a VolumeSnapshotClass if none exists
cat <<'EOF' | kubectl apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ontap-nfs-snapshot
driver: csi.netapp.io
deletionPolicy: Retain
EOF

# Create a VolumeSnapshot of the test PVC
cat <<'EOF' | kubectl apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: netapp-verify-snap
  namespace: default
spec:
  volumeSnapshotClassName: ontap-nfs-snapshot
  source:
    persistentVolumeClaimName: netapp-verify-pvc
EOF

# Wait for the snapshot to become ready
kubectl wait volumesnapshot netapp-verify-snap \
    --for=condition=Ready --timeout=60s

# Verify the snapshot
kubectl get volumesnapshot netapp-verify-snap -o yaml
VSC_NAME=$(kubectl get volumesnapshot netapp-verify-snap \
    -o jsonpath='{.status.boundVolumeSnapshotContentName}')
kubectl get volumesnapshotcontent "$VSC_NAME" -o json | \
    jq '.spec | {driver, volumeHandle, source: .source}'

# Write a marker file after the snapshot to verify point-in-time consistency
kubectl exec netapp-verify-pod-2 -- sh -c \
    'echo "post-snapshot $(date)" > /mnt/netapp/post-snap-marker'

# Restore the snapshot to a new PVC
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: netapp-verify-pvc-restored
  namespace: default
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: ontap-nfs
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: netapp-verify-snap
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
EOF

# Wait for the restored PVC to bind
kubectl wait pvc netapp-verify-pvc-restored --for=condition=Bound --timeout=60s

# Mount the restored PVC
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: netapp-verify-pod-restored
  namespace: default
spec:
  containers:
    - name: app
      image: nginx:1.25
      volumeMounts:
        - name: data
          mountPath: /mnt/netapp
      command: ["sleep", "3600"]
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: netapp-verify-pvc-restored
EOF

kubectl wait pod netapp-verify-pod-restored --for=condition=Ready --timeout=30s

# Verify data from before the snapshot exists
kubectl exec netapp-verify-pod-restored -- cat /mnt/netapp/survival-test

# Verify the post-snapshot marker does NOT exist (confirming point-in-time copy)
kubectl exec netapp-verify-pod-restored -- cat /mnt/netapp/post-snap-marker 2>&1 || \
    echo "Post-snapshot marker not found (correct: snapshot is point-in-time)"
```

The restored PVC should contain all data that existed at the moment the snapshot was created. The `survival-test` file (created in Exercise 1 or Step 1 of this exercise) should be present, but the `post-snap-marker` file (written after the snapshot) should not exist. This confirms the snapshot is a true point-in-time copy. In ONTAP, snapshots are stored in the volume's Snapshot copy reserve (default 5 percent of volume size) and do not consume additional space until data blocks are overwritten, at which point the old blocks are preserved in the snapshot.

---

## Diagnostic Cheat Sheet & Verification Checklist

### Quick Diagnostic Command Reference

| Symptom | First Command | Then Check |
|---|---|---|
| PVC stuck in Pending | `kubectl describe pvc <name>` | `kubectl logs -n trident deployment/trident-controller -c trident-main` |
| Pod stuck in ContainerCreating | `kubectl describe pod <name>` | `kubectl get volumeattachment` and `ls -la /var/lib/kubelet/plugins/csi.netapp.io/csi.sock` |
| Volume mount fails | `kubectl describe pod <name>` | `dmesg | tail -30` and `grep nfs /proc/mounts` |
| I/O latency high | `perf stat -e block:block_rq_complete -a sleep 10` | `tcpdump -i eth0 -nn port 2049 -c 100` and `ethtool -S eth0` |
| PVC won't expand | `kubectl describe pvc <name>` | `kubectl logs -n trident deployment/trident-controller -c csi-resizer` |
| Snapshot stuck in Creating | `kubectl get volumesnapshot` | `kubectl get volumesnapshotcontent` and `kubectl logs -n trident deployment/trident-controller -c csi-snapshotter` |
| Backend offline | `tridentctl get backends -n trident` | `kubectl logs -n trident deployment/trident-controller -c trident-main` and `ping $ONTAP_MGMT_LIF` |

### Network Path Verification One-Liner

```bash
export ONTAP_DATA_LIF="10.10.0.20"
export WORKER_IFACE="eth0"

echo "=== L2/L3 ==="
ping -c 3 -W 2 "$ONTAP_DATA_LIF" && echo "PASS" || echo "FAIL"

echo "=== L4 (NFS 2049) ==="
ss -tipn | grep -q ":2049" && echo "PASS" || echo "FAIL"

echo "=== L4 (iSCSI 3260) ==="
ss -tipn | grep -q ":3260" && echo "PASS" || echo "no iSCSI session"

echo "=== Interface Errors ==="
ethtool -S "$WORKER_IFACE" | grep -E "rx_crc|rx_err|tx_err|rx_drop|tx_drop" | grep -v ": 0$" || echo "PASS (no errors)"

echo "=== Link Speed ==="
ethtool "$WORKER_IFACE" | grep Speed
```

### Full Verification Checklist

```text
[ ] Trident operator pod running (1/1 Ready)
[ ] Trident controller pod running (1/1 Ready)
[ ] Trident node pod running on all storage worker nodes (1/1 Ready)
[ ] CSI driver csi.netapp.io registered in the cluster
[ ] CSI socket present at /var/lib/kubelet/plugins/csi.netapp.io/csi.sock
[ ] At least one Trident backend in "online" state
[ ] Storage class exists with provisioner csi.netapp.io
[ ] allowVolumeExpansion=true on the storage class
[ ] Test PVC binds within 60 seconds
[ ] Test pod reaches Ready state within 30 seconds
[ ] NFS mount visible in /proc/mounts on the hosting node
[ ] NFS sessions visible in ss output (port 2049)
[ ] No rx_crc_errors or tx_crc_errors on the storage interface
[ ] fio random 4K write IOPS within expected range for the ONTAP model
[ ] fio random 4K write p99 latency < 10ms
[ ] TCP retransmissions during workload = 0
[ ] Deleting application pod triggers clean volume detach (volumeattachment removed)
[ ] New pod remounts volume within 30 seconds
[ ] Data persists across pod deletion and remount cycle
[ ] Volume expansion succeeds and filesystem reflects new size
[ ] VolumeSnapshot reaches Ready state within 60 seconds
[ ] Restored PVC from snapshot contains pre-snapshot data
[ ] Post-snapshot data is absent from restored volume
[ ] Trident node pod recovery time < 60 seconds after deletion
[ ] NFS mount survives 500ms network latency injection (I/O slow but succeeds)
[ ] NFS mount recovers after 50% packet loss injection removed (< 120s)
```

### Trident Log Inspection Quick Reference

```bash
# Controller logs (provisioning, attachment, expansion, snapshots)
kubectl logs -n trident deployment/trident-controller -c trident-main --tail=100
kubectl logs -n trident deployment/trident-controller -c csi-provisioner --tail=50
kubectl logs -n trident deployment/trident-controller -c csi-attacher --tail=50
kubectl logs -n trident deployment/trident-controller -c csi-snapshotter --tail=50
kubectl logs -n trident deployment/trident-controller -c csi-resizer --tail=50

# Node logs (mount, unmount, node-side expansion)
kubectl logs -n trident daemonset/trident-node-linux -c trident-main --tail=100
kubectl logs -n trident daemonset/trident-node-linux -c csi-node-driver-registrar --tail=50

# Filter for errors only
kubectl logs -n trident deployment/trident-controller -c trident-main --tail=500 | grep -E "ERROR|FATAL"
kubectl logs -n trident daemonset/trident-node-linux -c trident-main --tail=500 | grep -E "ERROR|FATAL"

# Watch logs in real-time during operations
kubectl logs -n trident deployment/trident-controller -c trident-main -f
```

### Cleanup

```bash
# Remove all test resources
kubectl delete pod netapp-verify-pod netapp-verify-pod-2 netapp-verify-pod-restored --ignore-not-found
kubectl delete pvc netapp-verify-pvc netapp-verify-pvc-restored --ignore-not-found
kubectl delete volumesnapshot netapp-verify-snap --ignore-not-found
kubectl delete volumesnapshotclass ontap-nfs-snapshot --ignore-not-found

# Remove test files
rm -f /tmp/netapp-fio-profile.fio /tmp/netapp-fio-results.json
rm -f /tmp/nfs-fio.pcap /tmp/iscsi-fio.pcap /tmp/nfs-baseline.pcap

# Restore network (remove any tc qdisc rules)
sudo tc qdisc del dev "$WORKER_IFACE" root 2>/dev/null
```
