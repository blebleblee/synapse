# Lesson 4: Storage, StatefulSets, Persistent Volumes: Data Durability

## 1. First-Principles Intuition & Invariants

The ephemeral nature of container filesystems represents one of the fundamental architectural tensions in cloud-native infrastructure. Every container inherits a copy-on-write filesystem layer atop its base image, and when that container terminates—whether through graceful shutdown, crash, or eviction—all writes to that layer vanish. This design emerges directly from the stateless microservices paradigm, where horizontally scalable workloads treat individual instances as cattle rather than pets. Yet real distributed systems demand durable state: databases must persist transaction logs, message queues require offset tracking, machine learning pipelines checkpoint training state, and analytics platforms accumulate petabytes of time-series telemetry. Kubernetes resolves this tension through a declarative storage abstraction that decouples the lifecycle of data from the lifecycle of pods.

The Persistent Volume subsystem introduces three layers of indirection between application workloads and physical storage backends. At the lowest layer, PersistentVolumes represent actual storage capacity provisioned from Google Cloud infrastructure—block devices carved from Compute Engine Persistent Disks, NFS exports from Filestore instances, or object storage buckets in Cloud Storage. These volumes exist independently in the cluster as first-class API resources with their own lifecycle, just as nodes represent physical compute capacity. The middle abstraction layer consists of PersistentVolumeClaims, which function as resource requests expressed by application developers who declare "I need 50 gigabytes of SSD-backed storage with read-write-once semantics" without coupling to specific disk identifiers or availability zones. The Kubernetes control plane acts as a continuous matchmaker, binding claims to volumes that satisfy capacity, access mode, and storage class constraints. Finally, StorageClasses codify provisioning policies as reusable templates, embedding cloud-provider-specific parameters like disk type, replication strategy, and encryption configuration into named policies such as "fast-ssd" or "regional-replicated."

This three-tier architecture embodies the declarative reconciliation philosophy that pervades all Kubernetes subsystems. Application manifests describe desired state—a StatefulSet declares "I require three replicas, each with 100GB of persistent storage"—and the storage controller continuously drives actual state toward that specification. When a PersistentVolumeClaim appears, the controller searches for an unbound PersistentVolume meeting the claim's requirements, or triggers dynamic provisioning through the specified StorageClass. On Google Kubernetes Engine, dynamic provisioning translates into Compute Engine API calls that create zonal or regional Persistent Disks, then formats them with ext4 or xfs filesystems before exposing them through the kubelet's volume plugin framework. The binding between claim and volume establishes a durable association tracked in etcd, surviving pod rescheduling and node failures.

The critical invariant governing persistent storage concerns the difference between attachment and mounting. A Persistent Disk attached to a Compute Engine VM node appears as a block device in /dev, but remains inaccessible until mounted into the container's filesystem namespace at the declared volume mount path. The kubelet orchestrates this two-phase process through the Container Storage Interface, first calling ControllerPublishVolume to attach the disk at the node level, then NodeStageVolume to format and prepare the filesystem, and finally NodePublishVolume to bind-mount the volume into the pod's mount namespace. This staged approach allows the kubelet to perform expensive operations like filesystem checks and quota enforcement once per node attachment, amortizing cost across multiple pod lifecycles on that node.

Access modes encode concurrency constraints that emerge from the physical limitations of shared storage technologies. ReadWriteOnce semantics reflect the reality that Compute Engine zonal Persistent Disks can only attach to a single VM instance at any moment—attempting simultaneous attachment to multiple nodes triggers SCSI reservation conflicts at the block layer. ReadOnlyMany mode permits concurrent attachment because read-only mounts impose no write coordination overhead, enabling shared configuration volumes or static dataset distribution. ReadWriteMany represents true shared filesystem semantics, requiring networked storage like Google Cloud Filestore, which implements locking protocols and cache coherency across NFS clients. The access mode declared in a PersistentVolumeClaim acts as a binding contract: the scheduler will only place pods on nodes where the volume can satisfy the requested concurrency model.

Reclaim policies determine the fate of data when applications release their claims. The Retain policy preserves the PersistentVolume and its underlying disk after claim deletion, requiring manual inspection and cleanup—a safeguard against accidental data loss during development iteration. Delete policy triggers automatic destruction of both the volume API object and the backing storage resource, streamlining ephemeral environment teardown at the cost of permanence. Recycle policy, now deprecated in favor of dynamic provisioning, attempted in-place data scrubbing through basic filesystem removal, but provided insufficient guarantees for sensitive workloads. On GKE, the default dynamic provisioner applies Delete reclaim, coupling volume lifecycle tightly to claim lifecycle and ensuring that unused disks do not accumulate unbounded cloud spend.

StatefulSets extend the declarative storage model into the realm of ordered, stateful application topology. Unlike Deployments, which treat replicas as interchangeable and assign random pod names, StatefulSets impose deterministic identity through predictable naming—pods receive ordinal indices from zero to N-1, creating stable network identities like "cassandra-0.cassandra-headless.production.svc.cluster.local." Each pod in a StatefulSet binds to its own PersistentVolumeClaim generated from a volumeClaimTemplate, establishing a durable one-to-one mapping between pod identity and storage. When cassandra-1 restarts after a crash, it reattaches to the same PersistentVolume that held its commit logs and SSTables before failure, preserving local state across pod recreation. This stable identity foundation enables distributed databases to implement consistent hash rings, quorum-based replication, and leader election without external coordination services.

The StatefulSet controller enforces strict ordering guarantees during scaling and rolling updates. Pods deploy sequentially from index zero upward, with each pod reaching Ready state before the controller creates the next. During scale-down, the controller deletes pods in reverse order from highest index downward, ensuring that systems like ZooKeeper or Kafka maintain majority quorums throughout the operation. Rolling updates proceed similarly—the controller terminates and recreates pods one at a time in descending order, waiting for each new pod to report healthy before proceeding. This ordered choreography prevents split-brain conditions and data loss in systems that assume stable leader election or replica membership. The podManagementPolicy knob offers an escape hatch: setting it to Parallel sacrifices ordering for faster deployment, suitable for stateful workloads that handle their own convergence protocols.

The container storage interface specification decouples Kubernetes from cloud-provider-specific volume implementations through a gRPC-based plugin architecture. GKE bundles the GCE Persistent Disk CSI driver as a privileged DaemonSet running on every node, implementing the required RPC endpoints for provisioning, attaching, mounting, and monitoring volumes. When dynamic provisioning occurs, the CSI external-provisioner sidecar watches for PersistentVolumeClaims referencing the appropriate StorageClass, then invokes CreateVolume against the driver, passing topology constraints derived from pod affinity and zone labels. The driver translates these abstract requests into Compute Engine API calls, respecting regional replication preferences and encryption key specifications encoded in StorageClass parameters. This plugin boundary allows Google to ship storage enhancements—like faster snapshot cloning or adaptive IOPS scaling—through driver updates without waiting for upstream Kubernetes releases.

## 2. Core Architecture & Mechanics

The lifecycle of a dynamically provisioned volume begins when a StatefulSet controller creates a PersistentVolumeClaim from its volumeClaimTemplate. The claim specifies requested capacity through the resources.requests.storage field, access mode through accessModes array, and provisioning policy through the storageClassName reference. The persistent volume controller, running as part of kube-controller-manager, watches for unbound claims and attempts to satisfy them through existing unbound volumes matching size, access mode, and label selector constraints. When no suitable volume exists and the StorageClass enables dynamic provisioning (allowVolumeExpansion defaults true), the controller triggers the external-provisioner component through a Provision event.

```
┌─────────────────────────────────────────────────────────────────┐
│  StatefulSet Controller (kube-controller-manager)               │
│                                                                   │
│  1. Generate PVC from volumeClaimTemplate for each replica      │
│     metadata.name: data-postgresql-0                            │
│     spec.resources.requests.storage: 100Gi                      │
│     spec.storageClassName: fast-ssd                             │
│     spec.accessModes: [ReadWriteOnce]                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PersistentVolume Controller (kube-controller-manager)          │
│                                                                   │
│  2. Watch for unbound PVCs with storageClassName set            │
│  3. No matching PV found → trigger dynamic provisioning         │
│  4. Annotate PVC: volume.beta.kubernetes.io/storage-provisioner │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CSI External-Provisioner (sidecar for pd.csi.storage.gke.io)  │
│                                                                   │
│  5. Receive Provision request with StorageClass parameters:     │
│     parameters:                                                  │
│       type: pd-ssd                                               │
│       replication-type: regional-pd                              │
│       disk-encryption-kms-key: projects/.../cryptoKeys/key1     │
│  6. Invoke CSI Driver CreateVolume RPC with topology prefs      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  GCE PD CSI Driver (DaemonSet pod on node)                      │
│                                                                   │
│  7. Compute Engine API: disks.insert                            │
│     {                                                            │
│       "name": "pvc-a3f9d8e7-4b2c-11ef-9c8a-42010a8a0002",      │
│       "type": "pd-ssd",                                         │
│       "sizeGb": 100,                                            │
│       "replicaZones": ["us-central1-a", "us-central1-b"]       │
│     }                                                            │
│  8. Poll for disk READY state                                   │
│  9. Return CreateVolumeResponse with volumeId and topology      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CSI External-Provisioner                                        │
│                                                                   │
│  10. Create PersistentVolume object:                            │
│      spec.csi.driver: pd.csi.storage.gke.io                     │
│      spec.csi.volumeHandle: projects/.../disks/pvc-a3f9...      │
│      spec.capacity.storage: 100Gi                               │
│      spec.claimRef: {name: data-postgresql-0, ...}              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  PersistentVolume Controller                                    │
│                                                                   │
│  11. Bind PVC to PV by setting pv.spec.claimRef and            │
│      pvc.spec.volumeName, updating phase to Bound               │
└─────────────────────────────────────────────────────────────────┘
```

Once the PersistentVolumeClaim enters Bound phase, the Kubernetes scheduler can place the StatefulSet pod on a node that satisfies topology constraints. Regional Persistent Disks replicate synchronously across two zones within a region, and the CSI driver populates the PersistentVolume's allowedTopologies field with the replica zone list. The scheduler filters nodes to those residing in allowed zones, preventing a pod from landing on a node in us-central1-c when its disk replicas exist only in us-central1-a and us-central1-b. This topology-aware scheduling prevents attachment failures that would leave pods in ContainerCreating state indefinitely.

When the kubelet on the target node begins pod initialization, it delegates volume operations to the CSI node plugin running as a privileged DaemonSet pod. The attach-detach controller, running centrally in kube-controller-manager, first invokes the ControllerPublishVolume RPC, which translates to a Compute Engine instance.attachDisk API call. This operation exposes the Persistent Disk as a SCSI device on the VM, typically appearing as /dev/disk/by-id/google-{disk-name}. The kubelet's volume manager polls for attachment completion by monitoring /dev, then proceeds to the node-level staging phase.

```go
// Simplified CSI Driver NodeStageVolume implementation
func (d *Driver) NodeStageVolume(ctx context.Context, req *csi.NodeStageVolumeRequest) (*csi.NodeStageVolumeResponse, error) {
    volumeID := req.GetVolumeId()
    stagingTargetPath := req.GetStagingTargetPath() // e.g., /var/lib/kubelet/plugins/kubernetes.io/csi/pv/{pvName}/globalmount
    
    // Find device path from volumeID
    devicePath, err := d.findDeviceByVolumeID(volumeID)
    if err != nil {
        return nil, status.Errorf(codes.Internal, "failed to find device: %v", err)
    }
    
    // Check if device already has a filesystem
    fsType := req.GetVolumeCapability().GetMount().GetFsType()
    if fsType == "" {
        fsType = "ext4"
    }
    
    existingFS, err := d.detectFilesystem(devicePath)
    if err != nil {
        return nil, status.Errorf(codes.Internal, "filesystem detection failed: %v", err)
    }
    
    // Format device if unformatted
    if existingFS == "" {
        if err := d.formatDevice(devicePath, fsType); err != nil {
            return nil, status.Errorf(codes.Internal, "format failed: %v", err)
        }
    }
    
    // Create staging mount point
    if err := os.MkdirAll(stagingTargetPath, 0750); err != nil {
        return nil, status.Errorf(codes.Internal, "failed to create staging path: %v", err)
    }
    
    // Mount device to staging path
    mountOptions := req.GetVolumeCapability().GetMount().GetMountFlags()
    if err := d.mount(devicePath, stagingTargetPath, fsType, mountOptions); err != nil {
        return nil, status.Errorf(codes.Internal, "staging mount failed: %v", err)
    }
    
    // Apply filesystem quotas if requested
    if capacityBytes := req.GetVolumeCapability().GetMountVolume().GetVolumeMountGroup(); capacityBytes != "" {
        if err := d.setQuota(stagingTargetPath, capacityBytes); err != nil {
            return nil, status.Errorf(codes.Internal, "quota setup failed: %v", err)
        }
    }
    
    return &csi.NodeStageVolumeResponse{}, nil
}

// NodePublishVolume bind-mounts staging path into pod's mount namespace
func (d *Driver) NodePublishVolume(ctx context.Context, req *csi.NodePublishVolumeRequest) (*csi.NodePublishVolumeResponse, error) {
    stagingTargetPath := req.GetStagingTargetPath()
    targetPath := req.GetTargetPath() // e.g., /var/lib/kubelet/pods/{pod-uid}/volumes/kubernetes.io~csi/{pvc-name}/mount
    
    if err := os.MkdirAll(targetPath, 0750); err != nil {
        return nil, status.Errorf(codes.Internal, "failed to create target path: %v", err)
    }
    
    // Bind mount from staging to pod-specific path
    mountOptions := []string{"bind"}
    if req.GetReadonly() {
        mountOptions = append(mountOptions, "ro")
    }
    
    if err := d.mount(stagingTargetPath, targetPath, "", mountOptions); err != nil {
        return nil, status.Errorf(codes.Internal, "publish mount failed: %v", err)
    }
    
    return &csi.NodePublishVolumeResponse{}, nil
}
```

The two-phase mounting protocol—NodeStageVolume followed by NodePublishVolume—optimizes the common case where a node hosts multiple pods from the same StatefulSet over time. Staging performs the expensive format-and-mount operation once per node per volume, leaving the formatted filesystem accessible at a global staging path. Publishing then creates lightweight bind mounts from the staging path into each pod's unique volume directory. When a pod terminates and a new pod with the same PersistentVolumeClaim schedules to the same node, the kubelet skips staging and proceeds directly to publishing, reducing pod startup latency from seconds to milliseconds.

Volume expansion exemplifies the declarative reconciliation model applied to storage capacity. An operator edits the PersistentVolumeClaim, increasing resources.requests.storage from 100Gi to 200Gi. The persistent volume controller detects the capacity mismatch, validates that the StorageClass permits expansion, and invokes the CSI ControllerExpandVolume RPC. For GCE Persistent Disks, this triggers a Compute Engine disks.resize API call, which increases the block device size without detaching it from the running VM. The CSI driver then calls NodeExpandVolume on the kubelet, which invands filesystem-specific resize tools—resize2fs for ext4, xfs_growfs for XFS—to expand the filesystem to fill the newly available blocks. Throughout this process, the application continues reading and writing; modern filesystems support online expansion without unmounting or interrupting I/O.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-regional-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
  disk-encryption-kms-key: projects/my-project/locations/us-central1/keyRings/gke-ring/cryptoKeys/gke-key
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql-headless
spec:
  clusterIP: None
  selector:
    app: postgresql
  ports:
  - port: 5432
    name: postgres
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
spec:
  serviceName: postgresql-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  podManagementPolicy: OrderedReady
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: postgresql
            topologyKey: topology.kubernetes.io/zone
      containers:
      - name: postgres
        image: postgres:15.3
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres -h 127.0.0.1
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres -h 127.0.0.1
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-regional-ssd
      resources:
        requests:
          storage: 100Gi
```

The WaitForFirstConsumer volume binding mode delays PersistentVolume provisioning until a pod requiring the claim is scheduled. This deferred binding allows the scheduler to consider all pod constraints—CPU requests, memory limits, node selectors, affinity rules—before committing to a specific zone for volume creation. Without this delay, the dynamic provisioner might create a disk in us-central1-a, but the scheduler could later determine that the only node satisfying the pod's eight-core CPU request resides in us-central1-c, creating an unsatisfiable binding. WaitForFirstConsumer collapses volume topology selection and pod placement into a single atomic decision, preventing such misalignments.

Integrating managed Google Cloud services like Cloud SQL or Firestore into GKE workloads requires a different architectural pattern, since these services do not expose block storage or filesystem interfaces. Instead, applications connect over network protocols—libpq for PostgreSQL, gRPC for Firestore—using service endpoints and authentication credentials. The recommended integration path provisions a Cloud SQL instance through Terraform or Config Connector, then injects connection parameters into pods via environment variables sourced from Kubernetes Secrets. The Cloud SQL Auth Proxy, deployed as a sidecar container, establishes an authenticated tunnel between the pod and the database using the GKE Workload Identity federation, eliminating the need to manage long-lived service account keys.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  annotations:
    iam.gke.io/gcp-service-account: app-sa@my-project.iam.gserviceaccount.com
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: application
spec:
  replicas: 3
  selector:
    matchLabels:
      app: application
  template:
    metadata:
      labels:
        app: application
    spec:
      serviceAccountName: app-service-account
      containers:
      - name: app
        image: gcr.io/my-project/application:v1.2.3
        env:
        - name: DB_HOST
          value: "127.0.0.1"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "production"
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: cloudsql-db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: cloudsql-db-credentials
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.7.0
        args:
        - "--structured-logs"
        - "--port=5432"
        - "my-project:us-central1:production-db"
        securityContext:
          runAsNonRoot: true
          runAsUser: 65532
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

The Cloud SQL Proxy authenticates to the database instance using the pod's Kubernetes ServiceAccount, which the GKE metadata server exchanges for a short-lived Google Cloud service account token through Workload Identity federation. This token-based authentication eliminates secrets sprawl and automatically rotates credentials every hour, reducing the blast radius of credential compromise. The proxy listens on localhost within the pod's network namespace, so the application container connects to 127.0.0.1:5432 as if accessing a local database, while the proxy transparently handles TLS termination and authentication with the Cloud SQL backend.

Volume snapshots provide point-in-time copies of PersistentVolumes, enabling backup workflows and rapid cloning for development environments. The VolumeSnapshot API introduces another layer of indirection: VolumeSnapshotClass defines snapshot provisioning policies, while VolumeSnapshot represents an actual snapshot request bound to a source PersistentVolumeClaim. The CSI external-snapshotter controller watches for new VolumeSnapshot objects and invokes the driver's CreateSnapshot RPC, which translates to a Compute Engine snapshots.insert call for Persistent Disks. Restoring from a snapshot requires creating a new PersistentVolumeClaim with a dataSource reference pointing to the VolumeSnapshot, triggering the CSI driver to provision a new disk pre-populated with the snapshot's data.

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: fast-snapshot
driver: pd.csi.storage.gke.io
deletionPolicy: Delete
parameters:
  storage-locations: us-central1
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgresql-backup-20240815
spec:
  volumeSnapshotClassName: fast-snapshot
  source:
    persistentVolumeClaimName: data-postgresql-0
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-restore-dev
spec:
  dataSource:
    name: postgresql-backup-20240815
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-regional-ssd
  resources:
    requests:
      storage: 100Gi
```

Google Cloud Storage integration follows a different model, since GCS buckets provide object storage rather than block or file semantics. The GCS FUSE CSI driver mounts buckets into pod filesystems through a FUSE (Filesystem in Userspace) implementation, translating POSIX operations into GCS API calls. This approach enables workloads to read and write objects using standard file I/O syscalls, but imposes significant performance penalties—GCS FUSE achieves roughly 50-100 MB/s sequential throughput compared to 1200 MB/s for local SSD—and lacks true POSIX consistency guarantees. Metadata operations like directory listings require enumerating object prefixes, making recursive scans of large buckets prohibitively expensive. For these reasons, GCS FUSE serves specialized use cases like infrequent bulk data loading, while high-throughput workloads should interact with GCS directly through the native API or client libraries.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: gcs-trained-models
spec:
  capacity:
    storage: 1Ti
  accessModes:
  - ReadOnlyMany
  mountOptions:
  - implicit-dirs
  - max-conns-per-host=100
  csi:
    driver: gcsfuse.csi.storage.gke.io
    volumeHandle: my-ml-models-bucket
    readOnly: true
    volumeAttributes:
      bucketName: my-ml-models-bucket
      mountOptions: "implicit-dirs,max-conns-per-host=100"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gcs-trained-models
spec:
  accessModes:
  - ReadOnlyMany
  storageClassName: ""
  volumeName: gcs-trained-models
  resources:
    requests:
      storage: 1Ti
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-server
spec:
  replicas: 5
  selector:
    matchLabels:
      app: inference
  template:
    metadata:
      labels:
        app: inference
    spec:
      containers:
      - name: server
        image: gcr.io/my-project/inference:v2.1.0
        volumeMounts:
        - name: models
          mountPath: /models
          readOnly: true
        env:
        - name: MODEL_PATH
          value: /models/bert-large-v3
        resources:
          requests:
            memory: "8Gi"
            cpu: "4000m"
          limits:
            memory: "16Gi"
            cpu: "8000m"
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: gcs-trained-models
```

## 3. High-Performance Optimization & Failure Modes

Persistent Disk performance scales linearly with provisioned capacity, following Google's documented performance limits: pd-standard delivers 0.75 IOPS per GB and 0.12 MB/s per GB for sequential throughput, while pd-ssd achieves 30 IOPS per GB and 0.48 MB/s per GB. A 100GB pd-ssd volume sustains 3,000 IOPS and 48 MB/s, whereas a 1000GB volume reaches 30,000 IOPS and 480 MB/s. These limits apply per-disk, so workloads requiring higher performance must provision larger volumes or use extreme Persistent Disks (pd-extreme) with configurable IOPS independent of capacity. Extreme disks support provisioning up to 100,000 IOPS on a 1000GB volume, enabling single-instance databases to saturate 10 Gbps network bandwidth.

However, network bandwidth imposes a hard ceiling above disk-level IOPS limits. GKE nodes inherit the network egress limits of their underlying VM instance types: n1-standard-8 instances cap at 16 Gbps, while n2-standard-96 instances reach 100 Gbps. Since each I/O operation carries metadata overhead beyond raw payload bytes, the effective IOPS ceiling falls below the arithmetic throughput divided by I/O size. A workload issuing 4KB random reads against a pd-ssd observes roughly 75,000 IOPS on an n2-standard-32 (32 Gbps network), not the 120,000 IOPS suggested by disk provisioning, due to protocol overhead and CPU scheduling jitter.

Regional Persistent Disks replicate every write synchronously to two zones before acknowledging the I/O to the application, effectively doubling write latency compared to zonal disks. A zonal pd-ssd write completes in approximately 1-3 milliseconds at the 50th percentile and 5-10 milliseconds at the 99th percentile, while regional pd-ssd writes extend to 3-5 milliseconds and 10-20 milliseconds respectively. This latency increase reflects the speed-of-light delay across 10-50 kilometers between zonal datacenters plus the quorum acknowledgment protocol. Latency-sensitive databases like in-memory key-value stores should prefer zonal disks colocated with the node, accepting lower durability in exchange for sub-millisecond write latency. Conversely, systems that batch writes or use asynchronous replication—like PostgreSQL with commit_delay or Kafka with producer batching—tolerate regional disk latency in exchange for automatic cross-zone redundancy.

Filesystem selection significantly impacts both performance and operational complexity. The ext4 filesystem remains the default for most workloads due to maturity and broad compatibility, but exhibits write amplification under certain access patterns—small random writes trigger read-modify-write cycles at the block layer, degrading IOPS efficiency. The XFS filesystem optimizes for large files and parallel I/O through delayed allocation and aggressive metadata caching, making it preferable for data warehouses and log aggregation pipelines that write multi-gigabyte files. XFS also supports online defragmentation through xfs_fsr, whereas ext4 requires offline e4defrag runs that necessitate pod downtime. Both filesystems support quotas for enforcing storage limits per-PVC, though quota accounting imposes 3-5% CPU overhead during metadata-heavy workloads.

```bash
# Verify CSI driver volume provisioning and attachment
kubectl get pv -o wide
kubectl get pvc -n production -o wide

# Inspect StatefulSet pod volume mounts and bindings
kubectl describe statefulset postgresql -n production
kubectl get pods -n production -l app=postgresql -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.volumes[?(@.persistentVolumeClaim)]}{"\n"}{end}'

# Check CSI driver logs for provisioning errors
kubectl logs -n kube-system -l app=gcp-compute-persistent-disk-csi-driver --tail=100

# Force detach a volume stuck in "Terminating" on a failed node
# First, identify the VolumeAttachment
kubectl get volumeattachment
# Delete the VolumeAttachment to trigger detach
kubectl delete volumeattachment csi-<volume-id>

# Verify disk attachment at the node level via Compute Engine API
gcloud compute instances describe <node-name> --zone us-central1-a --format="value(disks[].source)"

# Expand a PersistentVolumeClaim and verify filesystem resize
kubectl patch pvc data-postgresql-0 -n production -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'
kubectl describe pvc data-postgresql-0 -n production | grep -A5 Conditions

# SSH into a node and verify filesystem size
gcloud compute ssh <node-name> --zone us-central1-a
df -h /var/lib/kubelet/plugins/kubernetes.io/csi/pv/pvc-<uid>/globalmount

# Trigger a volume snapshot for backup
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgresql-backup-$(date +%Y%m%d-%H%M%S)
  namespace: production
spec:
  volumeSnapshotClassName: fast-snapshot
  source:
    persistentVolumeClaimName: data-postgresql-0
EOF

# Monitor snapshot creation progress
kubectl describe volumesnapshot postgresql-backup-<timestamp> -n production

# Restore from snapshot to a new PVC for disaster recovery
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-restore-dr
  namespace: production
spec:
  dataSource:
    name: postgresql-backup-<timestamp>
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-regional-ssd
  resources:
    requests:
      storage: 200Gi
EOF
```

Volume mount failures manifest in pods stuck in ContainerCreating phase with events reporting "Unable to attach or mount volumes." The root cause often involves topology mismatches where the PersistentVolume's allowedTopologies list does not include the scheduled node's zone. Zonal disks can only attach to nodes within the same zone, so a disk in us-central1-a will never mount on a node in us-central1-b. Regional disks avoid this problem by maintaining replicas across two zones, but the initial provisioning step must choose which two zones based on the StorageClass topology parameters or the pod's volumeBindingMode=WaitForFirstConsumer scheduler decision. When a volume repeatedly fails to mount, inspect the VolumeAttachment object to identify attachment errors returned by the Compute Engine API, which may reveal quota exhaustion, insufficient IAM permissions, or concurrent attachment attempts violating ReadWriteOnce constraints.

StatefulSet scaling operations can deadlock when persistent volume provisioning fails midway through a scale-up. The StatefulSet controller creates pods sequentially, and each pod requires a bound PersistentVolumeClaim before transitioning to Running. If dynamic provisioning fails for pod-3's volume—perhaps due to Compute Engine API rate limits or exceeded regional disk quotas—pod-3 remains in Pending state indefinitely, blocking the creation of pod-4 through pod-N. The podManagementPolicy=Parallel setting bypasses sequential ordering, allowing all pods to provision concurrently, but this risks overwhelming the provisioning system with a thundering herd of volume creation requests. A middle ground uses a custom init container that probes for volume readiness and fails fast with a clear error message, enabling the StatefulSet controller to reschedule the pod rather than waiting silently.

Data corruption risks emerge when nodes fail abruptly during active I/O, particularly for databases relying on write-ahead logs. Compute Engine provides a best-effort graceful shutdown through the shutdown-script metadata attribute, which executes before VM termination. GKE nodes include a pre-installed shutdown script that drains pods—invoking the kubelet's eviction API—and waits up to five minutes for termination. However, this mechanism fails during hard kernel panics or live migration timeouts, where the node disappears without flushing buffered writes. PostgreSQL and MySQL mitigate this through their respective transaction log protocols—WAL and redo log—which force synchronous disk flushes (fsync) at commit boundaries, ensuring durability despite ungraceful shutdowns. Tuning these parameters requires balancing durability against write latency: PostgreSQL's synchronous_commit=remote_apply provides the strongest guarantee at the cost of replication latency, while commit_delay batches multiple transactions into a single fsync call, improving throughput by 30-50% with a small durability tradeoff.

Persistent volume leaks occur when PersistentVolumeClaim objects are deleted without proper cleanup of their bound volumes. The StorageClass reclaimPolicy controls this behavior: Delete policy automatically removes both the PV API object and the underlying disk when the PVC is deleted, while Retain preserves both for manual recovery. In production environments, Retain policy prevents accidental data loss but requires vigilant monitoring to avoid accumulating orphaned disks that continue accruing storage costs. Implementing a scheduled job that lists unbound PersistentVolumes older than seven days and correlates them with Compute Engine disks provides an automated detection mechanism, flagging candidates for manual review and deletion.

```go
// Implementing a custom CSI driver health checker for operational visibility
package main

import (
    "context"
    "fmt"
    "time"
    
    "google.golang.org/grpc"
    "github.com/container-storage-interface/spec/lib/go/csi"
)

type VolumeHealthChecker struct {
    nodeClient csi.NodeClient
    identityClient csi.IdentityClient
}

func (c *VolumeHealthChecker) CheckVolumeHealth(ctx context.Context, volumeID string, targetPath string) error {
    // Verify driver is responsive
    pluginInfo, err := c.identityClient.GetPluginInfo(ctx, &csi.GetPluginInfoRequest{})
    if err != nil {
        return fmt.Errorf("driver health check failed: %w", err)
    }
    
    // Query volume stats to verify mount is accessible
    statsReq := &csi.NodeGetVolumeStatsRequest{
        VolumeId: volumeID,
        VolumePath: targetPath,
    }
    
    statsResp, err := c.nodeClient.NodeGetVolumeStats(ctx, statsReq)
    if err != nil {
        return fmt.Errorf("volume stats query failed: %w", err)
    }
    
    // Check for capacity exhaustion
    usage := statsResp.GetUsage()
    for _, u := range usage {
        if u.Unit == csi.VolumeUsage_BYTES {
            usedPercent := float64(u.Used) / float64(u.Total) * 100
            if usedPercent > 90.0 {
                return fmt.Errorf("volume %s is %.1f%% full (used: %d, total: %d)", 
                    volumeID, usedPercent, u.Used, u.Total)
            }
        }
    }
    
    return nil
}

func (c *VolumeHealthChecker) MonitorAllVolumes(ctx context.Context, interval time.Duration) {
    ticker := time.NewTicker(interval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            // List all volumes from node plugin (requires custom CSI extension)
            // Standard CSI spec does not include ListVolumes for node service
            // This would be a driver-specific RPC
            
            // For each volume, perform health check
            // Log warnings for degraded volumes
            // Emit Prometheus metrics for capacity and I/O latency
        }
    }
}
```

Network partition scenarios test the resilience of distributed systems built on StatefulSets. When a node loses connectivity to the Kubernetes API server but continues running, the kubelet can no longer receive pod updates or report health status. The controller manager's node controller marks the node as NotReady after a grace period (default 40 seconds), and begins evicting pods after an additional five minutes. However, if the node retains connectivity to other nodes and databases, those pods continue serving traffic through their Service endpoints until forcibly terminated. This split-brain condition allows two instances of a StatefulSet pod to run concurrently—one on the partitioned node with stale state, another on a healthy node with current state—potentially violating single-writer assumptions in databases. The solution involves configuring podAntiAffinity rules that spread StatefulSet replicas across nodes and fault domains, combined with application-level distributed locks (etcd leases, ZooKeeper ephemeral nodes) that prevent dual-primary scenarios.

Regional Persistent Disk replication lag introduces subtle consistency challenges during node failures. While synchronous replication ensures that acknowledged writes exist on both replica disks before returning to the application, the replica in the secondary zone lags slightly behind due to network propagation delay and disk write scheduling. When a primary zone fails and the surviving replica promotes to active, a small window of writes committed to the primary but not yet applied to the secondary may disappear. The magnitude of this loss window typically spans 10-50 milliseconds, encompassing tens to hundreds of writes for throughput-intensive workloads. Transaction-oriented databases mitigate this through commit protocols that wait for quorum acknowledgment across multiple replicas—PostgreSQL synchronous replication, MySQL semi-synchronous replication—trading additional latency for stronger durability guarantees.

Monitoring volume performance requires instrumenting both the application layer and the infrastructure layer. Application metrics should track I/O latency histograms at operation boundaries—database query duration, cache miss penalties, log write times—to identify regressions. Infrastructure metrics focus on disk-level IOPS, throughput, and queue depth, exposed through the GKE observability stack via the GCE Persistent Disk metrics in Cloud Monitoring. Correlating spikes in disk queue depth with application latency percentiles pinpoints whether performance degradation stems from saturated disk bandwidth or application-level lock contention. Setting alerts on disk utilization thresholds (80% capacity, 90% IOPS) provides early warning before hard limits trigger errors, allowing proactive volume expansion through kubectl patch commands.
