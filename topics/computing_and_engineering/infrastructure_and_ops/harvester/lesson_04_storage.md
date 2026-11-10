# Lesson 4: Distributed Block Storage Mechanics with Longhorn

## 1. Storage Architecture: Microservice Block Storage vs. Monolithic SAN

Traditional enterprise virtualization relies on centralized storage fabrics (FC/iSCSI SANs or NFS NAS appliances). While robust, centralized arrays present single points of failure, introduce expensive proprietary hardware lock-in, and can bottleneck total cluster throughput when tens of thousands of random I/O operations queue up against a shared dual-controller head.

Distributed storage systems like Ceph solve scalability by clustering raw disks, but Ceph OSDs demand substantial CPU/memory footprints and complex CRUSH-map tuning.

Longhorn adopts a **microservice-oriented storage architecture**:
* Instead of running one massive cluster-wide storage daemon that manages all disk I/O, Longhorn shards the storage controller into **per-volume microservices**.
* Each Kubernetes PersistentVolume (PV) gets its own dedicated controller process (`Longhorn Engine`) and multiple isolated storage endpoints (`Longhorn Replicas`).
* If an engine process crashes or stalls due to high I/O wait, it impacts **only that single volume**, isolating failure domains and avoiding cluster-wide cascading I/O freezes.

---

## 2. The Engine and Replica Model

Longhorn decouples the frontend volume presentation from backend block persistence through two primary primitives running inside `instance-manager` pods on each node:

```
  Node A (VM Execution Node)                      Node B (Replica Node)           Node C (Replica Node)
  +-------------------------------------+         +---------------------+         +---------------------+
  | virt-launcher Pod                   |         |                     |         |                     |
  |  [QEMU / KVM Guest]                 |         |                     |         |                     |
  |          | (virtio-blk)             |         |                     |         |                     |
  |          v                          |         |                     |         |                     |
  |  [/dev/longhorn/<vol-name>]         |         |                     |         |                     |
  +-------------------------------------+         |                     |         |                     |
             |                                    |                     |         |                     |
             | Linux Block Device I/O             |                     |         |                     |
             v                                    |                     |         |                     |
  +-------------------------------------+         |                     |         |                     |
  | instance-manager-e (Engine Pod)     |         |                     |         |                     |
  |  +-------------------------------+  |         |                     |         |                     |
  |  | Longhorn Engine Process       |  |         |                     |         |                     |
  |  | - Handles reads/writes        |  |         |                     |         |                     |
  |  | - Manages snapshot tree       |  |         |                     |         |                     |
  |  +-------------------------------+  |         |                     |         |                     |
  +---|-----------------------------|---+         +---------------------+         +---------------------+
      |                             |                        ^                               ^
      | Local IPC / TCP             | Synchronous Network TCP|                               | Synchronous Network TCP
      v                             +------------------------|-------------------------------+
  +-------------------------------------+                    |                               |
  | instance-manager-r (Replica Pod)    |                    v                               v
  |  +-------------------------------+  |         +---------------------+         +---------------------+
  |  | Replica 1 (Local)             |  |         | Replica 2 (Remote)  |         | Replica 3 (Remote)  |
  |  | writes to sparse disk files   |  |         | writes to sparse    |         | writes to sparse    |
  |  +-------------------------------+  |         | disk files          |         | disk files          |
  +-------------------------------------+         +---------------------+         +---------------------+
```

### 2.1. Longhorn Engine
* Scheduled on the node where the consumer workload (the `virt-launcher` pod) executes.
* Exposes a Linux block device `/dev/longhorn/<volume-name>` directly on the host using either the kernel **TGT (Linux SCSI target framework)**, **NBD (Network Block Device)**, or **vhost-user-blk**.
* Acts as an active I/O dispatcher. For reads, it reads from the closest healthy replica (typically the local one to minimize network traversal). For writes, it synchronously broadcasts block payloads across all designated active replicas over TCP.

### 2.2. Longhorn Replicas
* Placed across distinct physical nodes and disk domains based on affinity and anti-affinity rules.
* Replicas are not raw partition block images; they are stored as **Linux sparse files** (`volume-head-xxx.img`) on the underlying host filesystem (typically formatted ext4 or XFS on the dedicated data disk).
* When a write request arrives from the Engine, the Replica appends or updates the requested offset in its active volume head file and returns an acknowledgment (ACK).
* A write operation is declared successful **only when all healthy replicas return an ACK** to the Engine.

---

## 3. Thin Provisioning, Differentials & Snapshot Trees

Longhorn volumes are inherently **thin-provisioned**. When a user allocates a 500 GiB volume, the underlying host filesystem consumes only the storage footprint actively written by the guest OS.

```
  Snapshot 1 (Base)        Snapshot 2 (State A)       Volume Head (Active)
  +------------------+     +--------------------+     +---------------------+
  | volume-snap-1    | <-- | volume-snap-2      | <-- | volume-head-001.img |
  | (Read-Only Diff) |     | (Read-Only Diff)   |     | (Active Read/Write) |
  +------------------+     +--------------------+     +---------------------+
```

### 3.1. Snapshot Mechanics
1. When a snapshot is taken, the current active `volume-head-001.img` is frozen and converted into a read-only snapshot delta file (`volume-snap-001.img`).
2. A fresh, empty `volume-head-002.img` is instantiated to absorb all new writes.
3. Reads traverse backwards: if a sector is requested, the Engine checks `volume-head`. If absent, it queries the immediate parent snapshot, traversing back to the base until the sector is found.

### 3.2. Deletion, Coalescing & Reclaiming (TRIM/DISCARD)
* **Snapshot Deletion:** Deleting an intermediate snapshot does not wipe blocks immediately; it marks the snapshot for coalescing. Background workers merge the delta blocks into the child snapshot file.
* **Space Reclamation:** Guest OS filesystems often delete files without clearing physical sectors. Enabling `discard` or running `fstrim` inside the virtual machine passes the SCSI `UNMAP` command down through `virtio-blk` to the Longhorn Engine, allowing Longhorn to punch holes (via `fallocate -p`) in the replica sparse files, returning disk space to the host.

---

## 4. Fault Tolerance, Failure Domains & Quorum Rebuilds

### 4.1. Replica Failure & Degradation
If a network blip or disk error prevents a replica from acknowledging a write:
1. The Longhorn Engine marks that replica as `ERR` (faulty) and disconnects it.
2. The volume status drops from `Healthy` to `Degraded`.
3. Workload I/O continues uninterrupted on the remaining healthy replicas.
4. The disconnected replica is deleted and deregistered from the engine.

### 4.2. Automatic Rebuild Pipeline
Once a volume enters `Degraded` status, the Longhorn Controller coordinates a rebuild:
1. **Scheduling:** The controller scans available nodes to locate a healthy storage node meeting disk-tag and failure-domain anti-affinity constraints.
2. **Replica Instantiation:** An empty replica placeholder is created in the target node's `instance-manager-r`.
3. **Sync Phase:** The engine initiates a live point-to-point block synchronization between one of the healthy source replicas and the new target replica using efficient block hashing.
4. **Catch-up Phase:** During the rebuild, writes from the running VM continue. The engine buffers incoming delta writes and applies them to the new replica until its state matches the live head.
5. **Promotion:** Once fully synchronized, the new replica is registered with the engine, and the volume returns to `Healthy`.

---

## 5. StorageClasses & Volume Modes in Harvester

In Kubernetes, pods typically use `ReadWriteOnce` (RWO) for block storage attached to a single node. However, KubeVirt VMs present distinct operational requirements:

* **Live Migration Needs `ReadWriteMany` (RWX):**
  During live migration, both the source and target `virt-launcher` pods must access the underlying storage volume simultaneously for a brief handover window.
* **Block Volume Mode:**
  Instead of mounting a filesystem inside a container (`volumeMode: Filesystem`), Harvester attaches volumes as raw block devices (`volumeMode: Block`). This gives QEMU direct, unbuffered I/O control (`cache=none, aio=native`), eliminating double-caching overhead in host page caches.

### Data Locality Strategies
Longhorn offers three settings for `dataLocality`:
* `disabled` (Default): Replicas are distributed evenly across nodes based on available disk space. The Engine reads from a local replica if available, or across the network if not.
* `best-effort`: The scheduler attempts to place at least one replica on the exact node where the consumer VM is running. If the VM moves, Longhorn attempts to rebuild a replica locally.
* `strict-local`: Enforces that only 1 replica exists and it *must* reside strictly on the local node. Eliminates network replication latency, but node failure causes storage unavailability until the node returns.

---

## 6. Infrastructure as Code: High-Performance StorageClass & Persistent Volume

Below is an enterprise-grade `StorageClass` tuned for virtualized database engines, along with a corresponding `PersistentVolumeClaim` consuming raw block storage.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-fast-nvme
provisioner: driver.longhorn.io
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: Immediate
parameters:
  numberOfReplicas: "3"
  staleReplicaTimeout: "2880" # 48 hours in minutes before deleting orphan data
  dataLocality: "best-effort"
  migratable: "true" # Enables live migration handling
  fsType: "ext4"
  diskSelector: "nvme,fast-tier"
  nodeSelector: "storage-node"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-nvme-volume-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteMany # Required for KubeVirt Live Migration
  volumeMode: Block # Raw block allocation bypasses filesystem double-caching
  storageClassName: longhorn-fast-nvme
  resources:
    requests:
      storage: 100Gi
```

---

## 7. Operational Lab: Inspecting Longhorn Internals

Follow these commands in your Harvester cluster to inspect storage controllers, locate physical replica files, and trace underlying block attachments.

### Step 1: Identify Longhorn Volume CRDs
Longhorn manages custom resources for every Kubernetes PVC:
```bash
# List all volumes, their current health, and frontend bindings
kubectl get volumes.longhorn.io -n longhorn-system -o custom-columns=\
NAME:.metadata.name,\
STATE:.status.state,\
ROBUSTNESS:.status.robustness,\
FRONTEND:.status.frontend,\
NODES:.status.currentNode
```

### Step 2: Trace the Active Engine and Replicas
Select one volume and verify where the engine and replicas are actively scheduled:
```bash
TARGET_VOL="<your-volume-name>"

# Inspect the Engine process hosting this volume
kubectl get engines.longhorn.io -n longhorn-system -l longhorn.io/volume=$TARGET_VOL

# List all distributed Replicas associated with the volume
kubectl get replicas.longhorn.io -n longhorn-system -l longhorn.io/volume=$TARGET_VOL -o wide
```

### Step 3: Inspect Physical Replica Files on the Host Node
Using a debug pod or SSH on the node hosting one of the replicas:
```bash
# Find the mount location of the Longhorn storage disk
df -h | grep harvester

# Locate the replica directory on disk
find /var/lib/harvester/defaultdisk/replicas/ -maxdepth 2 -name "${TARGET_VOL}*"

# Inspect sparse image files and snapshot chains within the replica
REPLICA_PATH=$(find /var/lib/harvester/defaultdisk/replicas/ -maxdepth 2 -name "${TARGET_VOL}*" | head -n 1)
ls -lhs $REPLICA_PATH
```
*Key files observed:*
* `volume-head-000.img`: Current active writable sparse file.
* `volume.meta`: Header containing volume UUID, size, and parent snapshot links.

### Step 4: Verify Host Block Device Attachment
Inside the node running the `virt-launcher` pod:
```bash
# Trace the active Longhorn block device
lsblk | grep longhorn

# Inspect SCSI/Longhorn controller properties
kubectl debug node/<node-name> -it --image=alpine -- chroot /host ls -la /dev/longhorn/
```

### Step 5: Test TRIM / Sparse Space Reclamation
Inside the running guest VM:
```bash
# Write a 1GB temporary file of random zeros
dd if=/dev/zero of=/test_zero.img bs=1M count=1024 status=progress
sync

# Check space consumed on host sparse file (it will grow by ~1GB)

# Delete the file and issue TRIM
rm -f /test_zero.img
fstrim -v /

# Check the host sparse file again: the hole-punching restores freed space.
```

---
*End of Lesson 4. In Lesson 5, we transition to advanced datacenter networking: VLAN interfaces, Multus CNI, and configuring trunk bridges for guest VMs.*