# Lesson 3: Storage and Persistent Data

## 1. First-Principles Intuition & Invariants

The fundamental tension in distributed systems is that compute is designed to be ephemeral while data is designed to outlive the processes that created it. Kubernetes, as an orchestration platform, was architected around stateless workloads first. Its scheduler treats pods as cattle: disposable units that can be killed, rescheduled, and replaced anywhere in the cluster. This model works beautifully for HTTP frontends and event processors, but it collides directly with the requirements of databases, message brokers, and any workload whose correctness depends on durable state.

Understanding storage in AKS requires you to internalize one foundational invariant before anything else: **the lifecycle of a pod and the lifecycle of its data are orthogonal concerns, and the entire Kubernetes storage subsystem exists to manage that orthogonality**. When a pod dies, its writable container layer evaporates. The union filesystem that overlayfs assembled at container start, with its upper write layer sitting above the read-only image layers, is torn down and discarded. If your application wrote anything to its local filesystem, that data is gone. This is not a bug; it is the correct behavior for a system designed around declarative state and horizontal scaling. The question is how you opt specific volumes out of this lifecycle and bind them instead to the lifecycle of data.

Linux itself gives us the primitives. A volume, in the kernel's view, is a block device or filesystem that gets mounted into a process's mount namespace. When you run a container, the container runtime establishes a new mount namespace, mounts the overlayfs union at `/`, then bind-mounts or directly mounts additional volumes into specific directories within that namespace. The container sees a coherent filesystem. The kubelet is responsible for orchestrating these mounts: it calls the Container Storage Interface (CSI) driver to provision or attach a device, formats it if necessary, and then hands the mount path to the container runtime before the pod's init containers run. The CSI driver is not an abstraction you interact with directly day-to-day, but understanding that it sits between the kubelet and the actual Azure infrastructure explains why storage operations carry observable latency at pod startup and why failures in that path manifest as pods stuck in `ContainerCreating`.

Azure AKS runs atop Azure's storage infrastructure, which means your persistent volumes are ultimately backed by one of two physical realities: Azure Managed Disks or Azure Files. Managed Disks are block devices: Azure provisions a VHD stored in Azure Storage, attaches it to a VM as a SCSI or NVMe device, and the OS formats and mounts it like any local disk. This gives you full block-layer semantics, including the ability to run filesystems with strong consistency guarantees like ext4 or XFS. The critical constraint of this model is **exclusive attachment**: a managed disk can only be attached to one VM node at a time, which maps directly to `ReadWriteOnce` access mode in Kubernetes. Azure Files, by contrast, is a managed SMB or NFS share. Because it is a network filesystem, multiple nodes can mount it simultaneously, enabling `ReadWriteMany` semantics at the cost of higher latency and the behavioral differences inherent in network filesystems versus local block devices.

The Kubernetes persistent volume subsystem adds a layer of abstraction over these physical resources through three interrelated objects: `StorageClass`, `PersistentVolume`, and `PersistentVolumeClaim`. The `StorageClass` encodes policy: it tells the system which CSI driver to call, which parameters to pass during provisioning (disk SKU, redundancy tier, encryption settings), and what reclamation behavior to apply when a claim is deleted. The `PersistentVolume` represents an actual provisioned storage resource, whether that was created dynamically by the CSI driver in response to a claim or pre-provisioned manually by an operator. The `PersistentVolumeClaim` is what a pod declares it needs: a request for a certain amount of storage with a certain access mode and, optionally, a certain storage class. The control plane's `PersistentVolumeController` runs a continuous reconciliation loop that binds claims to volumes, finding the best matching available volume or triggering dynamic provisioning if the storage class permits it.

One invariant that trips up engineers coming from VM-centric infrastructure is the relationship between redundancy and availability in this model. Azure Managed Disks with `LRS` (Locally Redundant Storage) replicate data within a single availability zone. If your AKS cluster spans multiple availability zones and a pod using an LRS disk gets rescheduled to a node in a different zone, the kubelet will fail to attach the disk because the underlying Azure storage is not accessible from that zone. This is not a Kubernetes bug; it is a consequence of the physical topology of Azure's datacenter architecture bleeding through every abstraction layer above it. Solving this requires either zone-pinning your pods, using ZRS (Zone-Redundant Storage) disk SKUs, or accepting the operational model that stateful workloads in a zonal cluster are inherently zone-local.

---

## 2. Core Architecture & Mechanics

### The CSI Driver and the Kubelet Attachment Pipeline

When you submit a `PersistentVolumeClaim`, the reconciliation path that leads to a mounted filesystem in a running container traverses several distinct components. Understanding this path is essential for diagnosing the class of failures that manifest as pods stuck in `Pending` or `ContainerCreating`.

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Control Plane                       │
│                                                                        │
│  ┌─────────────────┐      ┌──────────────────────────────────────┐    │
│  │   API Server    │◄────►│  PersistentVolumeController           │    │
│  └────────┬────────┘      │  (Bind PVC → PV, trigger provision)  │    │
│           │               └──────────────────────────────────────┘    │
│           │               ┌──────────────────────────────────────┐    │
│           └──────────────►│  AttachDetachController               │    │
│                           │  (Triggers CSI ControllerPublish)    │    │
│                           └──────────────────────────────────────┘    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ gRPC
                        ┌──────────▼──────────────┐
                        │   CSI Controller Plugin  │
                        │   (azuredisk-csi-driver) │
                        │                          │
                        │  CreateVolume()           │
                        │  ControllerPublishVolume()│
                        └──────────┬───────────────┘
                                   │ Azure ARM API
                        ┌──────────▼───────────────┐
                        │   Azure Managed Disk API  │
                        │   (SCSI attach to VM)     │
                        └──────────┬───────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                            Node (VM)                                   │
│                                                                        │
│  ┌────────────┐    ┌────────────────────┐    ┌──────────────────────┐  │
│  │  kubelet   │───►│  CSI Node Plugin   │───►│  Linux Mount Stack   │  │
│  │            │    │  NodeStageVolume() │    │                      │  │
│  │            │    │  NodePublishVolume │    │  mkfs.ext4 /dev/sdX  │  │
│  └────────────┘    └────────────────────┘    │  mount --bind        │  │
│                                              │  → pod mount ns      │  │
│                                              └──────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

The CSI driver for Azure Disks (`disk.csi.azure.com`) implements two logical roles: a controller plugin running as a deployment on the control plane side, and a node plugin running as a DaemonSet on every worker node. The controller handles volume lifecycle operations that require Azure API calls: `CreateVolume`, `DeleteVolume`, `ControllerPublishVolume` (which calls the Azure Compute API to attach the disk to the target VM). The node plugin handles the operations that require direct access to the node's block devices: `NodeStageVolume` formats the disk if needed and mounts it to a global staging directory, and `NodePublishVolume` bind-mounts that staged path into the pod's specific volume directory within the container's mount namespace.

This two-phase mount design exists because a disk might be shared between multiple pods on the same node (though for managed disks this is rare), and staging allows the format and initial mount to happen once while pod-level bind mounts are cheap. The staging path is `/var/lib/kubelet/plugins/kubernetes.io/csi/disk.csi.azure.com/<volume-id>/globalmount`, and the pod-specific bind mount lands at `/var/lib/kubelet/pods/<pod-uid>/volumes/kubernetes.io~csi/<pvc-name>/mount`. You can observe this directly on a node:

```bash
# SSH onto a node or use a privileged debug pod
findmnt -t ext4,xfs | grep kubelet
```

### StorageClass Configuration for Azure Disks

AKS ships with several default `StorageClass` objects. The `managed-csi` class provisions Premium SSD LRS disks using the in-tree CSI driver, while `managed-csi-premium` targets Premium SSD v2. For production workloads you should define your own storage classes that encode your specific requirements explicitly rather than depending on defaults that Microsoft may change between AKS versions.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-disk-premium-zrs
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_ZRS
  kind: Managed
  cachingMode: ReadOnly
  fsType: ext4
  enableBursting: "true"
  networkAccessPolicy: AllowAll
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
allowedTopologies:
  - matchLabelExpressions:
      - key: topology.disk.csi.azure.com/zone
        values:
          - eastus-1
          - eastus-2
          - eastus-3
```

The `volumeBindingMode: WaitForFirstConsumer` field deserves careful attention. When set to `Immediate`, the control plane provisions the disk as soon as the PVC is created, before any pod has been scheduled. The scheduler then has no say in the provisioning zone, and you can end up with a pod scheduled to zone 2 and a disk provisioned in zone 1 because the PVC was created first. `WaitForFirstConsumer` defers provisioning until a pod claiming that PVC is being scheduled, giving the scheduler the chance to communicate its topology decision to the provisioner. The scheduler passes topology constraints to the CSI provisioner via `AllowedTopologies` after considering node affinity, pod anti-affinity, and resource availability. For any multi-zone cluster running non-ZRS disks, `WaitForFirstConsumer` is not optional — it is the mechanism that prevents the zone-mismatch failure class described earlier.

The `cachingMode` parameter maps directly to Azure's host caching configuration on the VM's disk attachment. `ReadOnly` caching is appropriate for data that is read frequently and written infrequently: the Azure host will cache disk reads in the VM's local memory, reducing latency for reads while writes pass through directly to the managed disk. `ReadWrite` caching caches both reads and writes but introduces a data durability risk: if the VM is forcibly deallocated before the write cache is flushed, recently written data can be lost. For database transaction logs and WAL files, the correct setting is `None`.

### PersistentVolume and PersistentVolumeClaim Mechanics

The binding between a PVC and a PV is a one-to-one relationship enforced by the control plane. Once a PV is bound to a PVC, the PV's `claimRef` field points to that PVC and the PV is unavailable to any other claim. The status transitions are: `Available` (provisioned but unbound), `Bound` (matched to a PVC), `Released` (the PVC was deleted, but the PV still holds data and is awaiting reclamation), and `Failed` (reclamation failed).

A complete PVC for a PostgreSQL primary instance using the storage class defined above looks like:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-primary
  namespace: databases
  labels:
    app.kubernetes.io/name: postgresql
    app.kubernetes.io/component: primary
  annotations:
    volume.kubernetes.io/storage-provisioner: disk.csi.azure.com
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: azure-disk-premium-zrs
  resources:
    requests:
      storage: 256Gi
  volumeMode: Filesystem
```

The `volumeMode: Filesystem` field instructs Kubernetes and the CSI driver to format the block device with the filesystem specified in the StorageClass (`ext4` in our case) and present a mounted directory to the pod. Setting this to `Block` instead exposes the raw block device path to the pod, which is appropriate for applications that implement their own I/O stack, such as Ceph OSD processes or databases like ScyllaDB that prefer direct I/O to bypass the kernel's page cache.

### StatefulSets: Stable Identity and Ordered Lifecycle

A `Deployment` is fundamentally incompatible with stateful workloads because every pod it creates is anonymous and interchangeable. Pods get randomly generated name suffixes, there is no guaranteed ordering to their creation or deletion, and there is no mechanism to give each pod its own independent storage claim. `StatefulSet` exists to address each of these deficiencies systematically.

A StatefulSet assigns each pod a stable, predictable ordinal identity: `postgres-0`, `postgres-1`, `postgres-2`. This identity persists across rescheduling. If `postgres-1` is killed, the replacement pod will also be named `postgres-1`, will get the same PVC (`postgres-data-1`), and will mount the same underlying disk. This is not just a naming convenience; it is the mechanism by which a database replica knows it is a replica and can locate its own data directory after recovering from a failure.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: databases
spec:
  serviceName: postgres-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      terminationGracePeriodSeconds: 60
      securityContext:
        fsGroup: 999
        runAsUser: 999
        runAsNonRoot: true
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: postgres
      containers:
        - name: postgres
          image: postgres:16.2
          ports:
            - containerPort: 5432
              name: postgres
          env:
            - name: POSTGRES_DB
              value: appdb
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          resources:
            requests:
              cpu: "2"
              memory: 4Gi
            limits:
              cpu: "4"
              memory: 8Gi
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
            - name: postgres-wal
              mountPath: /var/lib/postgresql/wal
          livenessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - postgres
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 6
          readinessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - postgres
            initialDelaySeconds: 5
            periodSeconds: 5
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: azure-disk-premium-zrs
        resources:
          requests:
            storage: 256Gi
    - metadata:
        name: postgres-wal
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: azure-disk-premium-zrs
        resources:
          requests:
            storage: 64Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: databases
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
    - port: 5432
      name: postgres
```

The `volumeClaimTemplates` field is what distinguishes a StatefulSet from a Deployment at the storage layer. For each replica, the StatefulSet controller creates individual PVCs by interpolating the pod's ordinal: `postgres-data-postgres-0`, `postgres-data-postgres-1`, and so on. Each of these PVCs triggers an independent provisioning operation, resulting in three completely separate Azure Managed Disks. The WAL volume is on a separate disk intentionally: placing the PostgreSQL write-ahead log on a dedicated disk isolates its sequential write pattern from the random read-write pattern of the data directory, eliminating I/O contention between the two workloads.

The `fsGroup: 999` in the pod security context instructs the kubelet to `chown` the mounted volume to GID 999 (the `postgres` group in the official image) before the container starts. Without this, the postgres process running as UID 999 would encounter permission errors attempting to write to a volume formatted as `root:root`. This `chown` operation runs for every pod start, and on large volumes or volumes with many files it can add significant startup latency — a point we will return to in the optimization section.

The headless service (`clusterIP: None`) is a prerequisite for DNS-based pod discovery within the StatefulSet. Each pod gets a stable DNS record of the form `<pod-name>.<service-name>.<namespace>.svc.cluster.local`. Replication tooling like `patroni` or `pg_basebackup` can address individual replicas by name rather than by IP, which is essential because pod IPs are ephemeral while ordinal-based DNS names are stable.

### Storage Topology and Zone-Aware Scheduling

The `topologySpreadConstraints` block in the StatefulSet ensures that the scheduler distributes pods across availability zones with a maximum skew of 1. Combined with `WaitForFirstConsumer` binding mode in the StorageClass, this means: the scheduler picks a zone for each pod first, then the CSI driver provisions the disk in that same zone. The result is that `postgres-0` ends up in zone 1 with its disk in zone 1, `postgres-1` in zone 2 with its disk in zone 2, and `postgres-2` in zone 3 with its disk in zone 3.

You can verify the topology binding on any provisioned PV:

```bash
kubectl get pv -l app=postgres -o custom-columns=\
"NAME:.metadata.name,\
ZONE:.metadata.labels.topology\.disk\.csi\.azure\.com/zone,\
CAPACITY:.spec.capacity.storage,\
STATUS:.status.phase"
```

The CSI driver populates the `topology.disk.csi.azure.com/zone` label on PVs during provisioning. The scheduler then uses this label, via the `nodeAffinity` field the CSI driver writes into the PV spec, to ensure that subsequent pod scheduling only considers nodes in the matching zone.

---

## 3. High-Performance Optimization & Failure Modes

### Disk SKU Selection and I/O Characteristics

Azure Managed Disks span several performance tiers, and choosing the wrong one is the most common cause of storage-related performance problems in AKS. The selection is not purely about IOPS headroom; it is about understanding the relationship between provisioned disk size, the IOPS and throughput limits that Azure applies per disk, and the limits imposed by the VM SKU's storage controller.

Premium SSD v1 delivers IOPS proportional to disk size, capped at 20,000 IOPS and 900 MB/s throughput for the largest tiers. Premium SSD v2 decouples IOPS from capacity: you provision capacity, IOPS, and throughput independently, which is valuable for workloads where you need high IOPS on a relatively small dataset. Ultra Disk goes further, delivering sub-millisecond latency by using NVMe-attached storage with no host caching at all, which makes it appropriate for latency-sensitive OLTP databases.

The critical invariant that many engineers miss is that the VM SKU caps aggregate disk I/O across all attached volumes. A `Standard_D8s_v5` node has an uncached disk throughput limit of 192 MB/s. If you attach four 1TB Premium SSD P30 disks (each rated for 200 MB/s), their aggregate throughput still cannot exceed 192 MB/s because the VM's storage controller is the bottleneck, not any individual disk. If your database workload approaches this limit, you must either move to a larger VM SKU or shard the workload across more nodes rather than simply adding a faster disk.

You can observe the current I/O saturation on a node by running `iostat` in a privileged debug pod or by querying Azure Monitor metrics:

```bash
# Deploy a privileged debug pod to a specific node
kubectl debug node/<node-name> -it --image=mcr.microsoft.com/cbl-mariner/busybox:2.0

# Inside the debug pod, pivot to the host
chroot /host

# Check disk I/O stats across all attached block devices
iostat -xz 2 10 | grep -E "^(Device|sd|nvme)"
```

The `%util` column in `iostat` output is the most direct indicator of disk saturation. When a device reaches 100% utilization, writes begin queuing in the I/O scheduler's request queue, and latency climbs non-linearly. For databases, this is the difference between a 2ms write latency and a 200ms one.

### The fsGroup chown Latency Problem

As mentioned earlier, the kubelet's `fsGroup` handling causes a recursive `chown` and `chmod` traversal of the entire volume before the first container starts. On a volume containing millions of files (a large PostgreSQL data directory, for instance), this traversal can take many minutes, rendering the pod unresponsive during that time and causing readiness probe failures.

Kubernetes 1.20 introduced the `fsGroupChangePolicy` field on the pod's security context to address this. Setting it to `OnRootMismatch` instructs the kubelet to skip the recursive traversal if the volume's root directory already has the correct ownership and permissions, which is the common case after the first pod start:

```yaml
spec:
  securityContext:
    fsGroup: 999
    runAsUser: 999
    runAsNonRoot: true
    fsGroupChangePolicy: OnRootMismatch
```

This single field change can reduce StatefulSet pod startup time from several minutes to seconds for large data volumes. It is safe for virtually all workloads because the case it skips (the root already matches) is precisely the case where the traversal would have made no changes anyway.

### Volume Expansion in Production

AKS supports online volume expansion for managed disks without pod restart as of Kubernetes 1.24 with the `allowVolumeExpansion: true` field on the StorageClass. The workflow is to edit the PVC's `spec.resources.requests.storage` field upward. The CSI driver calls the Azure Disk API to resize the underlying managed disk, then signals the kubelet to trigger an online filesystem resize via `resize2fs` (for ext4) or `xfs_growfs` (for XFS). You do not need to restart the pod.

```bash
# Expand a specific PVC from 256Gi to 512Gi
kubectl patch pvc postgres-data-postgres-0 \
  -n databases \
  --type=merge \
  -p '{"spec":{"resources":{"requests":{"storage":"512Gi"}}}}'

# Monitor the expansion condition
kubectl get pvc postgres-data-postgres-0 -n databases \
  -o jsonpath='{.status.conditions}' | python3 -m json.tool
```

You can only expand a PVC; you cannot shrink it. Azure will reject a disk resize to a smaller capacity. If you need to reduce storage footprint, you must provision a new PVC, migrate data, and delete the original, which is an operational procedure rather than a Kubernetes-native workflow.

### Failure Mode: Volume Attachment Timeout

When a node becomes unhealthy (kernel panic, out-of-memory kill of critical processes, network partition), the pods running on it enter `Terminating` state, but their PVCs remain bound to the PVs that hold their disks. The problematic scenario is this: the node is unreachable but not terminated, so its pods are stuck `Terminating` indefinitely. The scheduler will not reschedule those pods elsewhere because the PVCs are still bound to PVs that have a `claimRef` to nodes in an ambiguous state.

The Azure Disk CSI driver handles this through a `force-detach` mechanism. When the `AttachDetachController` detects that an attachment has been pending beyond a threshold (configurable via `--detach-volume-map-max-retention-duration`, defaulting to 6 minutes), it forces an Azure API-level detach of the disk from the unreachable VM. This allows the disk to be attached to the new target VM and the replacement pod to start. The risk is data corruption if the original node's kernel was still writing to the disk at the moment of forced detach, which is why this mechanism is bounded by a timeout rather than applied immediately.

For StatefulSets specifically, you can accelerate recovery in confirmed node failure scenarios by manually deleting the stuck pod:

```bash
# Force-delete the stuck pod after confirming the node is truly dead
kubectl delete pod postgres-1 -n databases --force --grace-period=0

# Verify the PV transitions to Released and then back to Bound
kubectl get pv -w | grep postgres-data-1
```

Deleting the pod with `--force --grace-period=0` bypasses the graceful termination sequence. The kubelet on the failed node is unreachable and would never execute the graceful shutdown anyway. The control plane removes the pod object, freeing the PVC to rebind, and the CSI controller can proceed with detaching and reattaching the disk. Use this only when you have confirmed that the original node is truly dead and not simply experiencing a transient network partition, since a split-brain scenario where both the original pod and its replacement are writing to the same disk is unrecoverable without a backup.

### Snapshot-Based Backup with VolumeSnapshot

AKS clusters with the CSI driver snapshot extension enabled can take crash-consistent point-in-time snapshots of managed disks through native Kubernetes APIs, which are then stored as Azure Disk Snapshots.

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: azure-disk-snapshot-class
  annotations:
    snapshot.storage.kubernetes.io/is-default-class: "true"
driver: disk.csi.azure.com
deletionPolicy: Retain
parameters:
  incremental: "true"
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-data-snap-20240610
  namespace: databases
spec:
  volumeSnapshotClassName: azure-disk-snapshot-class
  source:
    persistentVolumeClaimName: postgres-data-postgres-0
```

Setting `incremental: "true"` instructs Azure to store only the changed blocks since the last snapshot rather than a full copy, which dramatically reduces both snapshot time and storage cost for large disks. Restoring from a snapshot is performed by creating a PVC with a `dataSource` referencing the `VolumeSnapshot` object, at which point the CSI driver calls the Azure Snapshot API to provision a new managed disk pre-populated with the snapshot's contents.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-restored
  namespace: databases
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: azure-disk-premium-zrs
  resources:
    requests:
      storage: 256Gi
  dataSource:
    name: postgres-data-snap-20240610
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

The restored PVC can be mounted by a new pod immediately, and Azure handles the background hydration of disk blocks lazily. Initial I/O performance may be slightly reduced during hydration as blocks are fetched from the snapshot on first access, but the pod does not wait for full hydration before it can operate.

### Observability and Diagnostic Commands

Effective storage operations in production require a set of habitual diagnostic queries. The following commands form a minimal but complete triage sequence when a storage-related incident is reported.

```bash
# 1. Check PVC status and binding across a namespace
kubectl get pvc -n databases -o wide

# 2. Inspect PV topology and reclaim policy
kubectl describe pv $(kubectl get pvc postgres-data-postgres-0 \
  -n databases -o jsonpath='{.spec.volumeName}')

# 3. Watch CSI controller logs for provisioning failures
kubectl logs -n kube-system \
  -l app=csi-azuredisk-controller \
  -c azuredisk \
  --since=10m \
  --follow

# 4. Watch node CSI plugin logs for mount failures
kubectl logs -n kube-system \
  -l app=csi-azuredisk-node \
  -c azuredisk \
  --since=10m \
  | grep -E "ERROR|WARN|failed|timeout"

# 5. Check events for a stuck PVC
kubectl get events -n databases \
  --field-selector reason=FailedMount \
  --sort-by='.lastTimestamp'

# 6. Verify disk attachment from the Azure CLI
az vm show \
  --resource-group <node-resource-group> \
  --name <node-vm-name> \
  --query "storageProfile.dataDisks[].{name:name,lun:lun,state:statuses[0].displayStatus}" \
  --output table
```

The `az vm show` query bridges the Kubernetes and Azure layers, confirming whether the managed disk is actually attached at the Azure infrastructure level independent of what Kubernetes believes. When `kubectl describe pod` shows `FailedMount` but the CSI logs show no errors, checking the Azure VM disk attachment state directly is the fastest path to root cause, because the attachment may have succeeded at the Azure layer but timed out before the CSI driver registered the success back to the kubelet.

Storage in AKS is ultimately the discipline of managing the intersection between Kubernetes's declarative object model and Azure's stateful infrastructure APIs, mediated by a CSI driver that must handle partial failures, timeout-based recovery, and cross-zone topology simultaneously. Mastering it means developing intuition for where in this pipeline a given failure occurred and which layer's tooling gives you the most direct visibility.
