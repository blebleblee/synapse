# Lesson 1: Cloud Native Architectures Overview

## 1. First-Principles Intuition & Invariants

Cloud native architectures represent a fundamental shift in distributed systems design, driven by the necessity to operate at scale in dynamic, heterogeneous infrastructure. The core insight is that traditional monolithic systems, which couple deployment lifecycle with application lifecycle, cannot adapt to the velocity and scale demands of modern applications. Cloud native decouples these concerns through a convergent control loop architecture where desired state is continuously reconciled against actual state.

### Declarative State Management and Reconciliation

The foundational invariant is **declarative state reconciliation**. Unlike imperative systems where operations are sequences of commands, declarative systems express intent as a target state. A control loop continuously observes actual state, compares it to desired state, and takes corrective action. This is a level-triggered system rather than edge-triggered: the reconciler responds to the existence of a condition (state mismatch) rather than events (state change notifications). This design provides inherent self-healing and drift correction.

Mathematically, the reconciliation loop implements a control system:

```text
e(t) = s_desired - s_actual(t)
u(t) = K * e(t)
s_actual(t+1) = s_actual(t) + Δs(u(t))
```

Where `e(t)` is error, `u(t)` is control signal (corrective actions), and `K` is the controller gain determining response aggressiveness. Kubernetes controllers implement proportional control with bounded retry backoff to prevent oscillation.

**Why this works:** Level-triggered reconciliation is robust to transient failures. If a corrective action fails or a notification is lost, the next reconciliation cycle will detect the same mismatch and retry. This contrasts with event-driven systems where lost events require complex compensation logic. The tradeoff is latency—reconciliation occurs on a polling interval (typically 30-60 seconds) rather than instantaneously.

### Microservices Architecture and Domain Boundaries

Microservices decompose systems by **bounded context**, a domain-driven design concept where each service encapsulates a cohesive business capability with clear ownership. The critical insight is that loose coupling at the architectural level enables organizational scalability. Conway's Law—"organizations which design systems are constrained to produce designs which are copies of the communication structures of these organizations"—is inverted: by designing loosely coupled services, organizations can structure teams around independent deployment units.

The invariant is **interface stability over implementation flexibility**. Services communicate through versioned APIs (typically REST or gRPC) with backward compatibility guarantees. This allows independent evolution: service A can be rewritten in a different language or refactored internally without affecting service B, provided the contract remains stable.

**Failure mode:** The network is now inside the application. Microservices introduce distributed systems problems—partial failures, network latency, consistency challenges—that do not exist in monoliths. The CAP theorem applies: in the presence of network partitions, you must choose between consistency and availability. Most cloud native systems prioritize availability and embrace eventual consistency through patterns like CQRS and event sourcing.

### Containerization: Process Isolation via Kernel Primitives

Containers provide **hermetic, reproducible execution environments** by leveraging Linux kernel isolation primitives. The key primitives are:

- **Namespaces**: Partition kernel resources (PIDs, network, mounts, IPC, users, cgroups) to create isolated views. A process in a PID namespace sees only processes in that namespace, enabling process tree isolation.
- **Cgroups (Control Groups)**: Hierarchical resource accounting and limits. A cgroup tracks and constrains CPU, memory, I/O, and network usage for a process tree. This prevents noisy neighbor problems in multi-tenant clusters.
- **Capabilities**: Fine-grained privilege decomposition. Rather than root vs non-root, capabilities partition superuser powers (e.g., `CAP_NET_ADMIN` for network config, `CAP_SYS_TIME` for clock modification) allowing processes to run with minimal privileges.
- **seccomp (Secure Computing Mode)**: Syscall filtering. A seccomp profile restricts the system calls a process can invoke, reducing attack surface.

A container image is a layered filesystem (typically OverlayFS or AUFS) combining a base OS layer with application layers. Layers are content-addressable (SHA-256 hashes) and immutable, enabling efficient distribution and caching. The OCI (Open Container Initiative) specification defines the image format and runtime interface, ensuring portability across container runtimes (Docker, containerd, CRI-O, rkt).

**Why this works:** Containers provide stronger isolation than traditional processes but lower overhead than virtual machines. VM isolation requires a full guest kernel and hypervisor, while containers share the host kernel. The tradeoff is that containers on the same host share a kernel and thus a security boundary—a kernel exploit in one container can potentially compromise the host.

### Orchestration: Declarative Cluster Management

Orchestration abstracts individual machines into a cluster-wide resource pool. The scheduler solves a bin-packing problem: given a set of pods (workload units) with resource requests and constraints, assign them to nodes to optimize resource utilization while satisfying constraints (affinity, anti-affinity, taints, tolerations).

Kubernetes implements a two-phase commit scheduler:

1. **Filtering**: Eliminate nodes that cannot satisfy the pod's requirements (insufficient resources, taints without matching tolerations, node selectors).
2. **Scoring**: Rank remaining nodes using weighted scoring functions (resource balance, pod spreading, affinity preferences). The node with the highest score is selected.

The scheduler is pluggable—custom schedulers or scheduler extenders can implement domain-specific placement logic (e.g., GPU affinity, network topology awareness).

**Invariant:** The scheduler operates on resource requests, not actual usage. A pod requesting 1 CPU is guaranteed 1 CPU regardless of whether it uses it. This reserves capacity and prevents overcommitment, but can lead to resource underutilization. Cluster autoscaling addresses this by adding nodes when pending pods exist, and removing underutilized nodes.

## 2. Core Architecture & Mechanics

### Kubernetes Control Plane: Distributed State Machine

The Kubernetes control plane implements a distributed state machine where the state of the cluster (all objects: pods, services, deployments, config maps, secrets) is stored in etcd and managed by controllers that drive the system toward declared state.

```mermaid
graph TB
    Client["kubectl / API Client"]
    APIServer["API Server<br/>(Validation, Authentication, RBAC)"]
    etcd["etcd Cluster<br/>(Raft Consensus, MVCC)"]
    Scheduler["Scheduler<br/>(Predicate & Priority)"]
    ControllerMgr["Controller Manager<br/>(Deployment, ReplicaSet, Service, etc.)"]
    CloudController["Cloud Controller Manager<br/>(Node, Route, Service LB)"]
    Kubelet["Kubelet (Node Agent)"]
    ContainerRuntime["Container Runtime<br/>(containerd, CRI-O)"]
    Proxy["kube-proxy<br/>(Service Routing)"]
    
    Client -->|"1. POST /api/v1/pods"| APIServer
    APIServer -->|"2. Write"| etcd
    APIServer -->|"3. Watch"| Scheduler
    Scheduler -->|"4. Bind Pod to Node"| APIServer
    APIServer -->|"5. Watch"| ControllerMgr
    ControllerMgr -->|"6. Reconcile"| APIServer
    APIServer -->|"7. Watch"| Kubelet
    Kubelet -->|"8. Run Container"| ContainerRuntime
    Kubelet -->|"9. Status Update"| APIServer
    Proxy -.->|"Service Rules"| APIServer
    CloudController -.->|"Cloud Resources"| APIServer
```

#### API Server: Central Coordination Point

The API server is the only component that directly communicates with etcd. All other components watch the API server for changes. This design centralizes authorization, authentication, and admission control. The API server processes requests through a chain:

1. **Authentication**: Verify identity (client certificates, bearer tokens, service account tokens).
2. **Authorization**: Check permissions (RBAC—Role-Based Access Control, ABAC—Attribute-Based Access Control, Webhook).
3. **Admission Control**: Mutating webhooks modify requests (e.g., inject sidecar containers), validating webhooks reject invalid requests (e.g., enforce security policies).
4. **Validation**: Schema validation ensures object structure matches API definitions.
5. **Persistence**: Write to etcd via a two-phase protocol (propose → commit).

The API server exposes RESTful HTTP/2 APIs following a resource-oriented design. Each Kubernetes object is a resource with a unique URI (e.g., `/api/v1/namespaces/default/pods/nginx`). Operations are standard HTTP verbs (GET, POST, PUT, PATCH, DELETE). The API supports watching resources via long-polling or streaming to receive real-time updates—controllers use this to react to changes.

#### etcd: Distributed Consensus and MVCC

etcd is a strongly consistent, distributed key-value store implementing the Raft consensus algorithm. Raft ensures that writes are replicated across a majority quorum before being committed, providing linearizable consistency. The quorum size is `Q = ⌊N/2⌋ + 1`. With 3 nodes, 2 must agree; with 5 nodes, 3 must agree. Odd numbers are preferred to maximize fault tolerance (5 nodes tolerate 2 failures; 6 nodes also tolerate only 2 failures but add cost).

Raft operates through leader election: one node is elected leader and handles all writes. The leader replicates log entries to followers. If the leader fails, followers detect the timeout and start a new election. The election term is incremented, preventing split-brain scenarios (two leaders in the same term). Raft's safety property guarantees that once a log entry is committed, it will be present in all future leaders' logs.

etcd uses Multi-Version Concurrency Control (MVCC) to provide lock-free, point-in-time consistent reads. Each write increments a global revision number. Readers specify a revision and receive a snapshot of the database at that revision. This enables:

- **Watch**: Clients watch a key prefix for changes since a revision, receiving a stream of updates.
- **Transactions**: Optimistic concurrency control via compare-and-swap (CAS). A transaction specifies conditions (e.g., key version equals X) and operations (e.g., write new value). If conditions fail, the transaction aborts.

**Performance characteristics:** etcd is optimized for reads (thousands/sec) but write throughput is limited by Raft replication and fsync latency (typically hundreds to low thousands/sec). Large clusters use leader lease optimizations (lease-based reads bypass quorum for recent values) and partitioning (separate etcd clusters for different object types or namespaces).

#### Controller Manager: Reconciliation Engine

The controller manager runs multiple controllers, each implementing the reconciliation loop for a specific resource type. Controllers watch the API server for changes and take corrective actions. Key controllers:

- **ReplicaSet Controller**: Ensures the desired number of pod replicas. If actual < desired, creates pods. If actual > desired, deletes excess pods. Deletion is ordered (oldest first, unready before ready).
- **Deployment Controller**: Manages ReplicaSets to provide declarative updates. Rolling update strategy creates a new ReplicaSet, incrementally scales it up while scaling down the old ReplicaSet. MaxSurge and MaxUnavailable parameters control update velocity and availability.
- **Endpoint Controller**: Watches Services and Pods, populates Endpoints objects with pod IPs that match the service selector and are ready. kube-proxy uses Endpoints to configure iptables or IPVS rules.
- **Node Controller**: Monitors node heartbeats (kubelet posts NodeStatus every 10s). If heartbeats stop, marks node NotReady after 40s, and evicts pods after 5 minutes (configurable). This prevents stale workload assignments.

Controllers use **work queues** with rate limiting to handle events. When a controller receives a watch notification, it enqueues the object key. Worker threads dequeue keys and process them. Rate limiting prevents thundering herd—if reconciliation fails, the item is requeued with exponential backoff (initial 5ms, max 1000s). This smooths load during mass failures (e.g., network partition recovery).

#### Scheduler: Constraint Satisfaction and Optimization

The scheduler assigns pods to nodes by solving a constraint satisfaction problem. The algorithm:

1. **Snapshot**: Fetch current cluster state (nodes, pods, resource usage).
2. **Filtering (Predicates)**: Eliminate infeasible nodes. Predicates include:
   - **PodFitsResources**: Node has sufficient CPU/memory.
   - **PodMatchNodeSelector**: Node labels match pod's nodeSelector.
   - **PodToleratesNodeTaints**: Pod tolerates all node taints.
   - **NoDiskConflict**: No volume conflicts (e.g., EBS volume already mounted on another node).
   - **PodFitsHostPorts**: Host ports are available.
3. **Scoring (Priorities)**: Rank feasible nodes using weighted scoring functions:
   - **LeastRequestedPriority**: Prefer nodes with lower resource utilization (balanced spreading).
   - **BalancedResourceAllocation**: Prefer nodes where CPU and memory usage are balanced (avoid resource fragmentation).
   - **SelectorSpreadPriority**: Spread pods matching the same service selector across nodes (improve availability).
   - **NodeAffinityPriority**: Prefer nodes matching affinity rules.
   - **InterPodAffinityPriority**: Co-locate or separate pods based on inter-pod affinity/anti-affinity.
4. **Selection**: Choose the highest-scoring node. If multiple nodes tie, select randomly.
5. **Binding**: Write pod binding to API server (atomic operation assigning pod to node).

**Preemption:** If no nodes satisfy the pod's requirements, the scheduler may preempt (evict) lower-priority pods to make room. Priority classes assign numeric priorities to pods. Preemption selects the node where evicting the fewest lower-priority pods satisfies the pending pod's requirements.

**Failure mode:** Scheduler decisions are based on stale state (snapshot from step 1). A node may become full between scoring and binding. The kubelet rejects the pod, and it returns to the scheduling queue. The scheduler uses optimistic concurrency—it assumes state changes are rare enough that retries are infrequent.

### Container Runtimes and CRI

The Container Runtime Interface (CRI) is a gRPC API standardizing communication between kubelet and container runtimes. CRI defines two services:

- **RuntimeService**: Manages pod sandboxes and containers (create, start, stop, remove, inspect).
- **ImageService**: Manages images (pull, list, remove, inspect).

A pod sandbox is a shared namespace (network, IPC, UTS) for containers in a pod. The runtime creates a sandbox, then creates containers within it. The pause container (infrastructure container) holds the sandbox namespace—it does nothing except sleep indefinitely. Other containers in the pod share the pause container's namespace, enabling localhost communication and shared volumes.

**containerd** is the dominant CRI runtime. It manages the complete container lifecycle, from image pull to execution. containerd uses runc (OCI-compliant runtime) to spawn containers. runc forks, sets up namespaces/cgroups, executes the container entrypoint, then exits—containerd shims monitor the container process and report status to kubelet.

**Networking:** Each pod receives a unique IP address. The Container Network Interface (CNI) abstracts network setup. When kubelet starts a pod, it invokes a CNI plugin to configure networking (create veth pair, attach to bridge, assign IP, configure routes). Popular CNI plugins include Calico (BGP-based routing), Flannel (VXLAN overlay), Cilium (eBPF-based), and Weave.

The Kubernetes network model imposes three requirements:

1. Pods can communicate with all other pods without NAT.
2. Nodes can communicate with all pods without NAT.
3. The IP a pod sees itself as is the same IP others see it as.

This flat network model simplifies service discovery and load balancing but requires careful IP address management (IPAM) and routing configuration.

**Storage:** Volumes provide persistent storage to containers. Kubernetes abstracts storage through PersistentVolume (PV) and PersistentVolumeClaim (PVC). A PVC is a request for storage (size, access mode, storage class). The PV controller binds the PVC to a PV that satisfies the request. Storage providers implement the Container Storage Interface (CSI), a gRPC API for volume provisioning, attachment, and mounting. CSI drivers handle cloud-specific operations (e.g., creating EBS volumes, attaching to EC2 instances).

### Service Mesh: Transparent Service Communication

A service mesh provides observability, security, and reliability for service-to-service communication. Envoy is the dominant sidecar proxy, deployed alongside each application container. Envoy intercepts all inbound and outbound traffic, implementing:

- **Load Balancing**: Client-side load balancing with health checking. Envoy periodically probes backends and removes unhealthy instances from the load balancing pool.
- **Retries and Timeouts**: Automatic retry with exponential backoff and jitter. Circuit breaking prevents cascading failures by failing fast when error rates exceed thresholds.
- **mTLS**: Mutual TLS authentication and encryption. Each service receives a certificate from a certificate authority (e.g., Istio CA). Envoy automatically rotates certificates and enforces identity-based access control.
- **Telemetry**: Envoy exports metrics (request rate, latency, error rate) and traces (distributed request tracing via OpenTelemetry). This enables observability without application instrumentation.

**Control plane:** Istio, Linkerd, and Consul provide control planes that configure Envoy sidecars. The control plane exposes a high-level API (e.g., VirtualService, DestinationRule) and translates it into low-level Envoy configuration (Listener, Cluster, Route). Configuration is pushed to Envoy via xDS (discovery service) protocols—LDS (listener discovery), CDS (cluster discovery), RDS (route discovery), EDS (endpoint discovery).

```mermaid
sequenceDiagram
    participant Client as Client Pod
    participant EnvoyC as Envoy Sidecar (Client)
    participant EnvoyS as Envoy Sidecar (Server)
    participant Server as Server Pod
    participant ControlPlane as Istio Control Plane

    ControlPlane->>EnvoyC: Push Route Config (xDS)
    ControlPlane->>EnvoyS: Push Listener Config (xDS)
    
    Client->>EnvoyC: HTTP Request
    EnvoyC->>EnvoyC: Apply Retry Policy
    EnvoyC->>EnvoyC: mTLS Handshake
    EnvoyC->>EnvoyS: Encrypted Request
    EnvoyS->>EnvoyS: Verify Certificate
    EnvoyS->>Server: Decrypted Request
    Server->>EnvoyS: Response
    EnvoyS->>EnvoyC: Encrypted Response
    EnvoyC->>Client: Response
    EnvoyC->>ControlPlane: Export Telemetry
```

**Failure mode:** Service meshes add latency (typically 1-5ms per hop for encryption/decryption) and operational complexity (sidecar resource overhead, version skew between control and data plane). Envoy crashes can break service communication. Circuit breakers and retries can mask underlying issues, delaying detection of systemic problems.

## 3. High-Performance Optimization & Failure Modes

### Concurrency and Parallelism

Kubernetes components are designed for high concurrency. The API server handles thousands of concurrent requests using an event-driven architecture with goroutines (Go's lightweight threads). Each request is processed in a separate goroutine, and goroutines are multiplexed onto OS threads by the Go runtime.

**Work queues** decouple event producers (watchers) from consumers (controllers). Controllers use multiple worker goroutines pulling from the queue, enabling parallel processing of reconciliation tasks. The number of workers is tunable—more workers increase throughput but also contention for API server access and etcd write capacity.

**Leader election** ensures only one instance of a controller is active. Controllers use a lease object in etcd to coordinate leadership. The leader periodically renews the lease; if it fails to renew, another instance acquires the lease and becomes leader. This prevents split-brain (two controllers acting on the same resource simultaneously) but introduces failover latency (typically 15-30 seconds).

### Resource Scaling: Horizontal and Vertical

**Horizontal Pod Autoscaling (HPA)**: Adjusts the number of pod replicas based on observed metrics (CPU utilization, memory, custom metrics). The HPA controller queries the metrics server every 15 seconds, calculates the desired replica count using:

```text
desiredReplicas = ceil(currentReplicas * (currentMetric / targetMetric))
```

If desired replicas differ from current replicas, the HPA updates the deployment. The algorithm includes stabilization windows to prevent flapping (rapid scaling up and down). The scaleDown window (default 5 minutes) requires metrics to remain below the threshold before scaling down, while scaleUp reacts immediately.

**Vertical Pod Autoscaling (VPA)**: Adjusts pod resource requests and limits. The VPA recommender analyzes historical usage and suggests optimal requests. The VPA updater evicts pods that need resizing, triggering recreation with updated requests. The VPA admission controller injects updated requests into newly created pods. VPA is disruptive (requires pod restart) and can conflict with HPA (both modify the same deployment).

**Cluster Autoscaling**: Adds or removes nodes based on pending pods and node utilization. The cluster autoscaler watches for unschedulable pods (no node has sufficient resources) and provisions new nodes. It removes underutilized nodes (utilization below threshold, typically 50%, for 10+ minutes) by safely evicting pods with PodDisruptionBudgets (PDBs) ensuring minimum availability.

**Performance pitfall:** Autoscaling reacts to past load, introducing lag. A sudden traffic spike may overwhelm the application before new pods start (cold start latency: image pull + container start + application initialization, typically 30s-2min). Mitigations: pre-warmed node pools, predictive autoscaling (scaling based on historical patterns or calendar events), and overprovisioning (keeping spare capacity).

### Boundary Conditions and Edge Cases

**Network Partitions:** A network partition splits the cluster into isolated segments. In a partition, nodes in the minority partition cannot reach the API server (if the API server is in the majority partition). Kubelet continues running existing pods but cannot update status or receive new assignments. After 5 minutes (default), the node controller evicts pods from the partitioned nodes, rescheduling them to reachable nodes. If the partition heals quickly, pods may be double-scheduled (running on both the original and new nodes). Applications must be idempotent or use distributed locking to handle this.

**Resource Exhaustion:** A pod exceeding its memory limit is OOM-killed by the kernel's OOM killer. A pod exceeding its CPU limit is throttled (cgroup CPU quota enforced). Pods without limits can starve other pods on the same node. BestEffort pods (no requests or limits) are evicted first during node pressure. Guaranteed pods (requests == limits) are evicted last.

**etcd Outage:** If etcd becomes unavailable (majority of nodes down), the control plane stops processing writes but continues serving reads from cached state. The cluster continues operating (existing pods run, services route traffic) but cannot schedule new pods, update configurations, or react to failures. The recovery time objective (RTO) depends on etcd backup strategy—restoring from a backup can take minutes to hours depending on data size.

**Cascading Failures:** A failure in one component can cascade. Example: a pod crash loop increases kubelet load (repeated restarts) → kubelet slows down → API server marks node NotReady → node controller evicts all pods from the node → other nodes receive evicted pods → increased load triggers crashes on other nodes → cluster-wide failure. Mitigations: PodDisruptionBudgets limit concurrent evictions, PriorityClasses ensure critical workloads are scheduled first, and resource quotas prevent a single tenant from exhausting cluster capacity.

### Failure Mitigations and Resilience Patterns

**Self-Healing:** Kubernetes automatically restarts failed containers (restartPolicy: Always). Liveness probes detect application deadlocks—if a liveness probe fails, kubelet restarts the container. Readiness probes detect when a container is ready to serve traffic—unready containers are removed from service endpoints, preventing requests from reaching them. Startup probes allow slow-starting containers (e.g., large JVM applications) extra time before liveness probes begin.

**Rolling Updates:** Deployments update pods incrementally. The RollingUpdate strategy controls the update:

- **maxSurge**: Maximum number of pods above the desired count during update (default 25%). Allows rapid rollout but increases resource usage.
- **maxUnavailable**: Maximum number of pods below the desired count during update (default 25%). Trades availability for resource efficiency.

If a new pod fails readiness checks, the rollout pauses automatically (progressDeadlineSeconds, default 600s). Rollback is manual or automated (using `kubectl rollout undo` or CI/CD pipelines monitoring metrics).

**Canary Deployments:** Deploy a new version to a small subset of users. This can be implemented with deployments (two deployments with a service selector matching both) or via service mesh routing rules (Istio VirtualService with weight-based routing). Monitor metrics (error rate, latency) for the canary. If metrics degrade, route traffic back to the stable version.

**Circuit Breaking:** Prevent cascading failures by failing fast when a downstream service is unhealthy. Envoy circuit breakers track connection pool usage and error rates. When thresholds are exceeded (e.g., 5 consecutive errors), Envoy opens the circuit and returns errors immediately without attempting requests. After a timeout, the circuit transitions to half-open and retries a single request to test recovery.

**Rate Limiting and Backpressure:** Prevent overload by limiting request rates. API server rate limiting (API Priority and Fairness, APF) ensures that no single client overwhelms the server. Application-level rate limiting (e.g., token bucket algorithm) protects services from traffic spikes. Backpressure—rejecting requests when queues are full—prevents unbounded buffering and latency accumulation.

**Chaos Engineering:** Deliberately inject failures to validate resilience. Tools like Chaos Mesh, Litmus, and Gremlin inject faults (pod kills, network latency, resource exhaustion) in production-like environments. This identifies weaknesses before real failures occur. Common experiments: kill random pods, partition network segments, exhaust node resources, introduce DNS failures.

### Observability: Metrics, Logs, and Traces

**Metrics:** Prometheus is the de facto standard. Applications expose metrics via `/metrics` HTTP endpoint (Prometheus text format). Prometheus scrapes endpoints periodically (default 30s) and stores time series data. PromQL (Prometheus Query Language) enables aggregation, filtering, and alerting. Key metrics:

- **RED**: Rate (requests/sec), Errors (error rate), Duration (latency percentiles).
- **USE**: Utilization (resource usage %), Saturation (queue depth), Errors.

Kubernetes components expose metrics (e.g., kubelet exposes node resource usage, API server exposes request latency).

**Logs:** Centralized logging aggregates logs from all pods. Kubernetes logs are written to stdout/stderr and captured by the container runtime. Log shippers (Fluentd, Fluent Bit, Promtail) tail log files and forward to a backend (Elasticsearch, Loki, Splunk). Structured logging (JSON) enables efficient querying and correlation.

**Traces:** Distributed tracing tracks requests across services. OpenTelemetry instruments applications to emit trace spans (operation name, start/end time, parent span ID). Spans are exported to a backend (Jaeger, Zipkin, Tempo). Tracing reveals latency bottlenecks and call paths in complex request flows.

**Practical example:** A request takes 2 seconds. Metrics show 99th percentile latency is 2s. Logs reveal frequent database query timeouts. Traces pinpoint that 1.8s is spent in a single database query. The root cause is a missing index—adding the index reduces latency to 200ms.

### Production-Grade Example: Resilient Stateful Application

Deploy a highly available PostgreSQL cluster using StatefulSets, persistent volumes, and backups.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None  # Headless service for stable pod DNS
  selector:
    app: postgres
  ports:
  - port: 5432
    name: postgres
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      initContainers:
      - name: init-replica
        image: postgres:15
        command:
        - bash
        - -c
        - |
          if [ "$HOSTNAME" != "postgres-0" ]; then
            until pg_isready -h postgres-0.postgres; do sleep 1; done
            pg_basebackup -h postgres-0.postgres -D /var/lib/postgresql/data -U replicator -Fp -Xs -P -R
          fi
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: app
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: POSTGRES_INITDB_ARGS
          value: "--data-checksums"  # Detect corruption
        ports:
        - containerPort: 5432
          name: postgres
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
      - name: metrics-exporter
        image: prometheuscommunity/postgres-exporter:latest
        env:
        - name: DATA_SOURCE_NAME
          value: "postgresql://postgres:$(POSTGRES_PASSWORD)@localhost:5432/postgres?sslmode=disable"
        ports:
        - containerPort: 9187
          name: metrics
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
data:
  username: cG9zdGdyZXM=  # base64: postgres
  password: c2VjdXJlUGFzczEyMyE=  # base64: securePass123!
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: postgres-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: postgres
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - bash
            - -c
            - |
              BACKUP_FILE="/backup/postgres-$(date +%Y%m%d-%H%M%S).sql.gz"
              pg_dumpall -h postgres-0.postgres -U postgres | gzip > "$BACKUP_FILE"
              # Upload to S3 (requires AWS credentials)
              aws s3 cp "$BACKUP_FILE" s3://my-backups/postgres/
              # Retain only last 30 days
              find /backup -name "postgres-*.sql.gz" -mtime +30 -delete
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            volumeMounts:
            - name: backup
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: postgres-backup-pvc
```

**Architectural decisions:**

- **StatefulSet**: Provides stable pod identities (postgres-0, postgres-1, postgres-2) and ordered provisioning. Each pod gets a unique PersistentVolume.
- **Headless Service**: Enables direct pod addressing via DNS (postgres-0.postgres.default.svc.cluster.local).
- **Init Container**: Configures replicas by performing streaming replication from the primary (postgres-0).
- **PodDisruptionBudget**: Ensures at least 2 replicas are available during voluntary disruptions (node drains, rolling updates).
- **Backups**: CronJob performs daily backups using pg_dumpall, compressed and uploaded to S3. Retention policy deletes backups older than 30 days.
- **Metrics**: Sidecar container runs postgres_exporter, exposing metrics for Prometheus.
- **Resource Limits**: Prevent resource starvation. Requests guarantee minimum resources; limits enforce maximum.

**Failure scenarios:**

- **Pod failure**: Kubelet restarts the container. Persistent volume preserves data.
- **Node failure**: StatefulSet controller reschedules the pod to another node. Persistent volume reattaches (cloud provider-specific, typically 1-5 minutes).
- **Primary failure**: Manual or automated failover promotes a replica. Clients reconnect to the new primary via updated DNS or a connection pooler (PgBouncer, HAProxy).
- **Data corruption**: Checksums (--data-checksums) detect corruption. Restore from backup.
- **Split-brain**: Replicas in a network partition may diverge. PostgreSQL replication slots and synchronous replication prevent data loss but sacrifice availability during partitions. The tradeoff is configured via synchronous_commit setting.

This example demonstrates production-grade resilience: redundancy (3 replicas), automated recovery (StatefulSet, liveness probes), data durability (persistent volumes, backups), observability (metrics), and disruption tolerance (PodDisruptionBudget).
