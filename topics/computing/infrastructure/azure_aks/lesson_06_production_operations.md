# Lesson 6: Production Operations, Observability, and Resilience

## 1. First-Principles Intuition & Invariants

Operating a production Azure Kubernetes Service cluster transcends the mechanics of declarative deployment manifests and imperative kubectl commands. The true engineering challenge emerges at the intersection of distributed systems theory, cloud infrastructure reliability, and organizational operational discipline. When we commit workloads to a managed Kubernetes control plane backed by Azure's global infrastructure, we inherit both the resilience guarantees of Microsoft's datacenter fabric and the operational complexity of orchestrating hundreds of microservices across dozens of node pools, each subject to transient failures, cascading degradations, and the fundamental impossibility of simultaneous consistency and availability under network partitions.

The first principle governing production operations is that **all systems eventually fail**, and the operational maturity of an organization manifests in how gracefully it degrades under partial failure. Azure AKS provides the substrate for resilience—regional availability zones, managed control plane high availability with 99.95% SLA, automatic node repair—but the application layer must be architected to exploit these primitives. A stateless web frontend tolerates pod evictions and node terminations through horizontal scaling and readiness probes, but a stateful PostgreSQL database demands careful orchestration of persistent volume snapshots, write-ahead log archival, and synchronized failover coordination. The operational delta between these workloads shapes monitoring strategies, backup procedures, and disaster recovery runbooks.

The second invariant concerns **observability as a first-class architectural constraint**. Traditional monitoring systems poll metrics at fixed intervals and trigger threshold-based alerts, a paradigm borrowed from monolithic application servers where all state resides within process memory. Kubernetes inverts this model: the actual runtime state of the cluster exists as a continuous stream of API server events reflecting the reconciliation delta between desired and observed states. When a deployment scales from three replicas to ten, the Kubernetes scheduler emits pod creation events, kubelet agents publish container lifecycle transitions, and the endpoints controller broadcasts service topology changes. Observability in AKS means reconstructing the causal chain of state transitions across control plane API audit logs, node-level systemd journal entries, container stdout streams, and application-layer structured logs. The engineering challenge is correlation: when a user reports elevated latency for transaction processing, the root cause might be a memory pressure eviction on a worker node triggered by a misbehaving sidecar container, surfaced only by correlating pod eviction events in kube-system namespace with node condition changes and container OOMKilled status codes.

The third principle is that **disaster recovery is not a technology but a testable operational contract**. Azure provides infrastructure-level resilience through geo-redundant storage, zone-redundant managed disks, and cross-region virtual network peering, but application-level disaster recovery demands explicit engineering: persistent volume snapshots scheduled through VolumeSnapshot CRDs, cluster state backups via etcd exports or Velero, and tested failover procedures documented in executable runbooks. The Recovery Time Objective (RTO) and Recovery Point Objective (RPO) are not business requirements handed to infrastructure teams but mathematical constraints derived from data durability guarantees, network replication lag, and human reaction time during incident response. A database replicated to a secondary region with asynchronous commit achieves RPO bounded by replication lag—typically seconds to minutes—while RTO includes detection time, failover decision latency, and DNS propagation delays. Production operational excellence means quantifying these bounds through failure injection testing and chaos engineering, not inferring them from vendor marketing collateral.

The fourth invariant recognizes that **zero-downtime upgrades are a composable property, not an atomic operation**. Azure automatically patches AKS control plane components during maintenance windows, preserving API server availability through rolling upgrades of etcd quorum members and controller manager replicas. However, upgrading the Kubernetes minor version from 1.28 to 1.29 requires coordinated node pool upgrades, which evict running pods and reschedule them onto upgraded nodes. The operational contract here is subtle: Kubernetes guarantees that PodDisruptionBudgets prevent excessive simultaneous evictions, but applications must implement graceful shutdown handlers that drain in-flight requests before terminating. A web service that terminates immediately upon SIGTERM without waiting for active HTTP connections to close will drop requests during node pool upgrades, violating the zero-downtime invariant despite correct infrastructure orchestration.

The final principle is that **operational complexity scales superlinearly with state**. Stateless workloads achieve horizontal scalability through replica sets and horizontal pod autoscalers, requiring minimal operational discipline beyond health checks and resource quotas. Stateful workloads—databases, message queues, distributed caches—demand consensus protocols, leader election, quorum maintenance, and data rebalancing, each introducing failure modes that propagate across the dependency graph. When a three-node Cassandra cluster loses quorum due to simultaneous node failures, the operational response is not simply "restart the pods" but "restore quorum through seed node rebootstrapping while preserving consistency level guarantees." The observability and recovery procedures for stateful systems must therefore capture distributed protocol state: Raft leader terms, ZooKeeper zxid monotonic counters, Kafka ISR (in-sync replica) membership, and transaction log sequence numbers.

These five invariants—universal failure, observability as architectural primitive, disaster recovery as testable contract, zero-downtime as composable property, and superlinear complexity of state—define the operational challenge space. Production AKS operations synthesize Azure-native monitoring integrations (Azure Monitor, Log Analytics, Application Insights), Kubernetes-native diagnostics (resource metrics API, event streams, controller logs), and application-layer instrumentation (OpenTelemetry traces, Prometheus metrics, structured logging) into a coherent operational telemetry plane. The subsequent sections dissect the mechanical implementation of this synthesis through concrete runbooks, configuration manifests, and debugging workflows.

## 2. Core Architecture & Mechanics

### Observability Architecture: Metrics, Logs, Traces, and Events

The observability architecture for production AKS clusters operates across four orthogonal telemetry dimensions, each capturing distinct facets of runtime behavior. **Metrics** represent scalar time-series measurements of resource utilization and performance: CPU throttling percentage, memory working set size, network packet drop rates, persistent volume IOPS. **Logs** capture discrete event records with structured or unstructured payloads: application exception stack traces, authentication failures, API request/response bodies. **Traces** model the causal propagation of distributed transactions across service boundaries through span hierarchies annotated with timing breakdowns and error conditions. **Events** encode Kubernetes control plane state transitions: pod scheduling decisions, container restarts, config map updates, persistent volume claim binding.

Azure Monitor Container Insights provides the foundational metrics pipeline for AKS clusters. When enabled through the Azure CLI or portal, it deploys a DaemonSet running the containerized Azure Monitor agent (ama-logs) onto every cluster node. This agent scrapes the kubelet read-only metrics endpoint exposed on port 10255, which aggregates resource usage statistics from cAdvisor—the container advisor daemon embedded in kubelet that queries cgroup accounting files in /sys/fs/cgroup/. The metrics flow follows this data path:

```
cgroup accounting (/sys/fs/cgroup/cpu,cpuacct,memory/)
    ↓
cAdvisor (embedded in kubelet)
    ↓
Kubelet metrics endpoint (:10255/stats/summary)
    ↓
ama-logs DaemonSet (scrapes every 60s)
    ↓
Azure Monitor ingestion endpoint (regional)
    ↓
Log Analytics workspace (KubeNodeInventory, KubePodInventory, Perf tables)
```

The ama-logs agent enriches raw cgroup metrics with Kubernetes metadata by querying the API server's `/api/v1/pods` endpoint, joining resource usage samples with namespace, pod name, controller owner references, and node assignments. This enrichment enables dimensional queries in Log Analytics: "show me memory usage for all pods in the production namespace owned by the payment-processor deployment." The agent batches telemetry into 64KB compressed payloads transmitted over HTTPS to the regional Azure Monitor ingestion endpoint, typically achieving sub-minute latency from metric sample to queryable storage.

Log collection follows a parallel architecture. The ama-logs agent tail-follows container logs stored by the container runtime in `/var/log/containers/*.log`, which are symlinks to the actual log files in `/var/log/pods/<namespace>_<pod>_<uid>/<container>/`. Docker runtime writes logs to JSON-formatted files, while containerd outputs CRI-compliant logs with timestamp prefixes. The agent parses these formats, extracts multiline log records (handling Java stack traces spanning dozens of lines), and forwards them to the ContainerLog table in Log Analytics. For performance-sensitive workloads generating high log volumes, the agent supports sampling and filtering through ConfigMaps, dropping verbose debug logs before egress to minimize ingestion costs.

Application-level distributed tracing requires explicit instrumentation. Azure Application Insights provides an OpenTelemetry-compatible tracing backend when configured with the appropriate connection string. Applications instrumented with the OpenTelemetry SDK emit trace spans—annotated with service name, operation name, start time, duration, and parent span ID—to the Application Insights ingestion endpoint. The backend reconstructs the full transaction topology by building a directed acyclic graph from parent-child span relationships, exposing the end-to-end latency breakdown in the Application Insights portal. For a multi-tier web application where an ingress request triggers downstream calls to authentication, database, and cache services, the trace waterfall reveals whether latency concentrates in database query execution, network round-trip time, or lock contention in the authentication service.

Kubernetes events represent the fourth telemetry stream, surfacing control plane decisions and error conditions. When a pod fails to schedule due to insufficient CPU resources, the scheduler emits a `FailedScheduling` event with a human-readable message describing the constraint violation. When a node transitions to NotReady state due to disk pressure, the kubelet publishes a `NodeNotReady` event. These events persist in etcd for one hour by default before automatic garbage collection, but the ama-logs agent continuously watches the API server's `/api/v1/events` stream and archives events to the KubeEvents table in Log Analytics for long-term retention and correlation with metrics and logs.

### Health Checks and Self-Healing Primitives

Kubernetes implements three orthogonal health check mechanisms: **liveness probes** detect unrecoverable failure states requiring container restart, **readiness probes** gate service endpoint inclusion to prevent traffic routing to degraded instances, and **startup probes** tolerate slow initialization for legacy applications with extended boot times.

Liveness probes execute at a configured interval (default 10 seconds) after an initial delay period. A probe failure increments a failure counter, and when the counter exceeds the configured threshold (default 3 consecutive failures), kubelet terminates the container and restarts it according to the pod's restart policy. The probe failure threshold prevents spurious restarts from transient network glitches or momentary CPU saturation. Consider an HTTP liveness probe configured as:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
    httpHeaders:
    - name: X-Probe-Type
      value: liveness
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
  successThreshold: 1
```

Kubelet issues an HTTP GET request to the container's port 8080 at `/health/live` every 10 seconds, waiting up to 5 seconds for a response. If three consecutive probes timeout or return non-2xx status codes, kubelet sends SIGTERM to the container's PID 1, waits for the grace period (default 30 seconds), then sends SIGKILL if the process has not exited. The container runtime (containerd) removes the container filesystem layers and creates a fresh container from the image, preserving the pod's IP address and persistent volume mounts. The application developer's responsibility is ensuring the `/health/live` endpoint returns 200 only when the application can recover from transient errors independently—a deadlocked thread pool or exhausted database connection pool warrants liveness failure and forced restart, while temporary cache unavailability does not.

Readiness probes govern service endpoint registration. When a pod transitions to Running phase, kubelet begins executing readiness probes at the configured interval. Only after the probe succeeds does kubelet set the pod's Ready condition to True, which triggers the endpoints controller to add the pod's IP to the service's endpoints list. Ingress controllers and kube-proxy iptables rules then begin forwarding traffic to the pod. If a readiness probe subsequently fails, the endpoints controller removes the pod IP from the service, draining in-flight requests without terminating the container. This allows the application to self-heal from transient overload or dependency unavailability without restart overhead.

Startup probes address the challenge of applications requiring extended initialization—legacy monoliths loading large configuration files, JVM applications performing class loading and JIT compilation, databases recovering transaction logs on startup. A startup probe disables liveness and readiness probes until it succeeds, allowing the application 30 × 10 = 300 seconds to initialize before liveness probing begins:

```yaml
startupProbe:
  httpGet:
    path: /health/startup
    port: 8080
  periodSeconds: 10
  failureThreshold: 30
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  periodSeconds: 5
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  periodSeconds: 10
```

The three probe types compose to express nuanced availability contracts. A web service might implement `/health/startup` to verify database schema migrations completed successfully, `/health/ready` to check that the cache is warmed and accepting connections, and `/health/live` to detect application deadlock through a watchdog goroutine that increments a counter every second—if the counter stops incrementing, the application has deadlocked and requires restart.

### Disaster Recovery Patterns: Backup and Restore

Disaster recovery for AKS clusters decomposes into three layers: **control plane state backup** (etcd snapshots, API resources), **persistent volume data backup** (PVC snapshots, cross-region replication), and **configuration-as-code versioning** (Helm charts, Kustomize overlays, Terraform state). The operational contract defines Recovery Point Objective (RPO)—maximum tolerable data loss—and Recovery Time Objective (RTO)—maximum tolerable downtime—which constrain the backup frequency and restoration procedures.

Azure AKS control plane state is backed up automatically by Microsoft's managed service, with etcd snapshots stored in geo-redundant Azure Storage. In the event of a regional outage affecting the control plane, Azure support can restore the cluster control plane from these backups, typically within hours. However, this restore operation does not recover application data in persistent volumes—it only restores the Kubernetes API resources (deployments, services, config maps) defining the cluster workloads.

Application data residing in persistent volumes requires explicit backup orchestration. Azure Disk-backed PersistentVolumes support point-in-time snapshots through the VolumeSnapshot API, a Kubernetes-native abstraction over cloud provider snapshot capabilities. Creating a VolumeSnapshot requires a VolumeSnapshotClass defining the snapshot provisioner and a VolumeSnapshot resource referencing the source PVC:

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: azure-disk-snapshot-class
driver: disk.csi.azure.com
deletionPolicy: Retain
parameters:
  incremental: "true"
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot-20250115
  namespace: production
spec:
  volumeSnapshotClassName: azure-disk-snapshot-class
  source:
    persistentVolumeClaimName: postgres-data-pvc
```

The Azure Disk CSI driver receives the snapshot request, invokes the Azure Compute API to create an incremental disk snapshot, and updates the VolumeSnapshot status with the snapshot handle. Incremental snapshots capture only the changed blocks since the last snapshot, reducing snapshot creation time and storage costs. Restoring from a snapshot involves creating a new PVC with the snapshot as the data source:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data-pvc-restored
  namespace: production
spec:
  storageClassName: managed-csi-premium
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: postgres-snapshot-20250115
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

The CSI provisioner clones the snapshot into a new managed disk, provisions a PersistentVolume backed by that disk, and binds it to the restored PVC. The stateful application (StatefulSet) mounts the restored PVC and resumes operation from the snapshot recovery point. The RPO equals the snapshot frequency—hourly snapshots provide one-hour RPO, but introduce operational complexity of snapshot lifecycle management and garbage collection of obsolete snapshots.

For multi-region disaster recovery, cross-region persistent volume replication requires either application-level replication (PostgreSQL streaming replication, MySQL binlog replication) or storage-level replication using Azure NetApp Files with cross-region replication. Application-level replication achieves lower RPO (seconds) at the cost of operational complexity: managing replication lag, handling split-brain scenarios, coordinating failover with application-layer leader election. Storage-level replication simplifies operations but introduces higher RPO (minutes to hours) due to asynchronous snapshot replication between regions.

The third disaster recovery layer is configuration-as-code versioning. All Kubernetes manifests—deployments, services, ingress rules, RBAC policies—should be versioned in Git and deployed through GitOps controllers like Flux or ArgoCD. In a disaster scenario requiring cluster rebuild in a secondary region, the GitOps controller reconciles the desired state from Git into the new cluster, recreating all application workloads. Helm charts and Kustomize overlays parameterize environment-specific configurations (replica counts, resource limits, ingress hostnames), enabling identical application topology across development, staging, and production clusters. Terraform state for AKS infrastructure (node pools, virtual networks, managed identities) must be stored in remote backends like Azure Storage with versioning enabled, allowing infrastructure-as-code rollback to known-good states.

### Upgrade Orchestration and Zero-Downtime Deployments

AKS cluster upgrades operate at two levels: **control plane upgrades** (API server, controller manager, scheduler, etcd) and **node pool upgrades** (kubelet, container runtime, kernel patches). Azure orchestrates control plane upgrades transparently during maintenance windows, maintaining API server availability through rolling upgrades of replicas. The operational contract guarantees that the API server remains responsive to kubectl commands and reconciliation loops continue executing, but etcd leadership transitions may introduce brief (~1 second) latency spikes for write operations.

Node pool upgrades evict running pods and reschedule them onto upgraded nodes, requiring careful coordination to preserve availability. The upgrade procedure follows this sequence for each node:

1. **Cordon** the node to prevent new pod scheduling while allowing existing pods to continue running
2. **Drain** the node by evicting pods in accordance with PodDisruptionBudgets, which constrain the maximum number of simultaneously unavailable replicas for each application
3. **Upgrade** the node by applying OS patches, upgrading kubelet and container runtime, and rebooting if required
4. **Uncordon** the node to re-enable pod scheduling

The drain operation respects PodDisruptionBudgets, which encode availability requirements:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-frontend-pdb
  namespace: production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web-frontend
```

This PDB requires that at least two replicas of the web-frontend deployment remain available during disruptions. When the node drain evicts a web-frontend pod, the eviction API checks whether evicting this pod would violate the PDB. If only two replicas are currently running, the eviction is blocked until a replacement pod schedules onto a different node and transitions to Ready. This prevents cascading availability loss from simultaneous pod evictions.

Applications must implement graceful shutdown to achieve zero-downtime during node upgrades. When kubelet evicts a pod, it sends SIGTERM to the container's PID 1 and waits for the configured `terminationGracePeriodSeconds` (default 30) before sending SIGKILL. A graceful shutdown handler performs these steps:

1. Stop accepting new requests by failing readiness probes
2. Wait for existing requests to complete (drain in-flight connections)
3. Flush buffered data to persistent storage
4. Close database connections and release distributed locks
5. Exit with status code 0

For HTTP services, graceful shutdown means coordinating with the readiness probe and connection draining:

```go
// Go HTTP server with graceful shutdown
func main() {
    srv := &http.Server{Addr: ":8080", Handler: handler}
    
    stop := make(chan os.Signal, 1)
    signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
    
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()
    
    <-stop
    log.Println("Received SIGTERM, starting graceful shutdown")
    
    // Allow up to 25 seconds for connections to drain
    ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
    defer cancel()
    
    if err := srv.Shutdown(ctx); err != nil {
        log.Printf("Forced shutdown after timeout: %v", err)
    }
    log.Println("Server stopped")
}
```

The readiness probe should fail immediately upon receiving SIGTERM, causing the endpoints controller to remove the pod IP from the service endpoints within ~2 seconds. The 25-second shutdown timeout allows existing connections to complete while ensuring the process exits before kubelet's SIGKILL deadline.

AKS node pool upgrades support multiple strategies: **manual** (operator triggers upgrade explicitly), **unattended** (automated patch management during maintenance windows), and **node image upgrade** (in-place OS updates without node replacement). The surge upgrade strategy provisions new nodes before draining old nodes, temporarily exceeding the desired node count to minimize scheduling pressure:

```bash
az aks nodepool upgrade \
  --resource-group production-rg \
  --cluster-name production-aks \
  --name systempool \
  --kubernetes-version 1.29.0 \
  --max-surge 33%
```

A 33% max-surge setting on a 6-node pool provisions two additional nodes during upgrade, allowing three nodes to drain simultaneously while maintaining baseline capacity. This accelerates upgrade duration at the cost of temporary compute overprovisioning.

### Troubleshooting Methodologies and Diagnostic Workflows

Production incident response follows a structured diagnostic workflow progressing from high-level symptoms to root cause identification through iterative hypothesis testing. The methodology synthesizes cluster-level metrics, node-level diagnostics, pod-level logs, and control plane event streams into a causal narrative explaining the observed failure.

The first diagnostic step is establishing the **failure domain**: is this a cluster-wide issue affecting all workloads, a node-specific problem impacting pods on certain nodes, or an application-level bug isolated to specific pod replicas? Cluster-wide issues manifest as API server latency, etcd quorum loss, or control plane component failures. Node-specific issues present as NotReady node conditions, disk pressure, memory pressure, or network partition. Application-level issues appear as pod CrashLoopBackOff, container OOMKilled status, or elevated error rates in application logs.

For cluster-wide issues, query the API server health endpoint and control plane component status:

```bash
# Check API server responsiveness
kubectl get --raw /healthz

# Inspect control plane component logs (requires cluster admin access)
kubectl logs -n kube-system -l component=kube-apiserver --tail=100

# Check etcd cluster health
kubectl exec -n kube-system etcd-<node> -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
```

API server latency correlates with etcd disk I/O saturation, which manifests as elevated fsync duration in etcd metrics. Azure-managed AKS control planes provision etcd storage on Premium SSD with provisioned IOPS, but extremely high churn rates (thousands of API writes per second) can exhaust disk bandwidth. The mitigation is reducing API write load through request batching, client-side caching, and informer-based watches instead of polling.

For node-specific issues, the diagnostic workflow begins with node condition inspection:

```bash
# List nodes with conditions
kubectl get nodes -o wide

# Detailed node status
kubectl describe node <node-name>

# Node resource pressure conditions
kubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type=="MemoryPressure")].status}'
```

Node conditions reflect kubelet's assessment of resource availability. MemoryPressure condition triggers pod eviction based on memory.available falling below the eviction threshold (default 100Mi). DiskPressure triggers eviction when nodefs.available (root filesystem) or imagefs.available (container image storage) falls below thresholds. PIDPressure indicates the node is approaching the maximum PID limit, preventing new process creation. NetworkUnavailable indicates CNI plugin failure preventing pod networking.

When a node enters MemoryPressure, kubelet evicts pods in priority order: BestEffort pods (no resource requests/limits) are evicted first, followed by Burstable pods exceeding their memory requests, and finally Guaranteed pods (requests equal limits). The eviction decision uses the pod's memory working set size relative to its memory request, favoring eviction of pods consuming memory disproportionate to their reservations.

Application-level troubleshooting begins with pod status inspection:

```bash
# List pods with phase and ready status
kubectl get pods -n production -o wide

# Detailed pod events and conditions
kubectl describe pod <pod-name> -n production

# Container logs (stdout/stderr)
kubectl logs <pod-name> -n production -c <container-name> --tail=100 --timestamps

# Previous container logs (after restart)
kubectl logs <pod-name> -n production -c <container-name> --previous
```

A pod in CrashLoopBackOff phase indicates repeated container failures. The exit code provides initial diagnostic direction: exit code 0 indicates clean termination (possibly incorrect command), exit code 1 indicates application error (inspect logs), exit code 137 (128+9) indicates SIGKILL termination (likely OOMKilled), and exit code 143 (128+15) indicates SIGTERM termination during graceful shutdown.

For OOMKilled containers, compare the container's memory usage against its memory limit:

```bash
# Container resource usage
kubectl top pod <pod-name> -n production --containers

# Memory limit from pod spec
kubectl get pod <pod-name> -n production -o jsonpath='{.spec.containers[0].resources.limits.memory}'
```

If memory usage approaches or exceeds the limit, the kernel OOM killer terminates the container. The mitigation is either increasing the memory limit or optimizing application memory consumption. Java applications commonly require JVM heap size tuning through -Xmx flags, ensuring heap size plus native memory (thread stacks, metaspace, direct buffers) remains below the container memory limit.

For networking issues, verify pod IP allocation and service endpoint registration:

```bash
# Pod IP and node assignment
kubectl get pod <pod-name> -n production -o jsonpath='{.status.podIP}{"\n"}{.status.hostIP}'

# Service endpoints
kubectl get endpoints <service-name> -n production

# DNS resolution from within pod
kubectl exec <pod-name> -n production -- nslookup <service-name>
```

If a pod is not appearing in service endpoints despite being in Running phase with Ready condition, the label selector likely does not match. Verify the service selector matches pod labels exactly. If DNS resolution fails, check CoreDNS pod status in kube-system namespace and inspect its logs for resolution errors.

For persistent volume issues, check PVC binding status and underlying storage health:

```bash
# PVC status
kubectl get pvc -n production

# PV details
kubectl get pv <pv-name> -o yaml

# Azure Disk attachment status (requires node SSH access)
lsblk
```

A PVC stuck in Pending status indicates provisioning failure. Common causes include storage class misconfiguration, zone mismatch (PVC in one zone, node in another, violating zonal storage constraints), or Azure subscription quota exhaustion. The event stream on the PVC provides detailed error messages from the CSI provisioner.

Advanced troubleshooting scenarios require direct node access through Azure Bastion or kubectl debug node sessions. The kubectl debug command creates a privileged pod with host namespaces, allowing inspection of node-level system state:

```bash
# Create debug pod with host network/PID namespaces
kubectl debug node/<node-name> -it --image=ubuntu

# Inspect systemd journal for kubelet errors
chroot /host journalctl -u kubelet -n 100

# Container runtime logs
chroot /host journalctl -u containerd -n 100

# Kernel messages
chroot /host dmesg | tail -100
```

This privileged access enables diagnosing kernel-level issues (OOM killer invocations, TCP connection tracking table exhaustion), container runtime failures (containerd crashes, image pull errors), and CNI plugin problems (IPAM address exhaustion, routing table corruption).

## 3. High-Performance Optimization & Failure Modes

### Scaling Architecture and Resource Right-Sizing

Production workload performance tuning begins with empirical resource profiling under realistic load, establishing baseline resource consumption patterns, and configuring autoscaling policies that maintain performance SLOs while minimizing cost. The Kubernetes Horizontal Pod Autoscaler (HPA) dynamically adjusts replica counts based on observed metrics, while the Vertical Pod Autoscaler (VPA) adjusts resource requests and limits, and the Cluster Autoscaler provisions additional nodes when resource capacity is exhausted.

Horizontal scaling effectiveness depends on workload characteristics. Stateless web services scale linearly with replica count until bottlenecks emerge in downstream dependencies—database connection pools saturate, backend API rate limits trigger, or load balancer throughput caps are reached. Stateful workloads require careful partitioning strategies: sharded databases scale through consistent hashing schemes that distribute keyspace across replicas, while queue-based workers scale through competing consumers pulling from a shared work queue. The HPA configuration must align with application scaling characteristics:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-frontend-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-frontend
  minReplicas: 3
  maxReplicas: 30
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
```

This HPA scales based on both CPU utilization (target 70%) and application-level request rate (target 1000 req/s per pod). The scaling behavior configuration introduces asymmetric policies: scale-up can double replica count every 30 seconds when thresholds are exceeded, while scale-down is rate-limited to 50% every 60 seconds with a 5-minute stabilization window preventing thrashing from transient load spikes. The selectPolicy: Max for scale-up chooses the most aggressive policy when multiple policies trigger simultaneously, ensuring rapid response to load surges.

Custom metrics for HPA require exposing application metrics through a Prometheus adapter or Azure Monitor integration. The application must instrument request rate counters and export them in a format the metrics adapter can scrape and aggregate. For HTTP services, this typically involves incrementing a counter on each request handler invocation and exposing the counter through a /metrics endpoint.

Vertical Pod Autoscaler complements HPA by adjusting resource requests and limits based on observed usage patterns. VPA operates in three modes: Off (recommendations only), Initial (sets requests on pod creation), and Auto (updates running pods through eviction and recreation). The Auto mode disrupts workloads by restarting pods, so production usage typically employs Initial mode with manual review of recommendations:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: db-worker-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: db-worker
  updatePolicy:
    updateMode: "Initial"
  resourcePolicy:
    containerPolicies:
    - containerName: postgres
      minAllowed:
        cpu: 500m
        memory: 1Gi
      maxAllowed:
        cpu: 8000m
        memory: 32Gi
      controlledResources:
      - cpu
      - memory
```

VPA analyzes historical resource usage stored in Prometheus or Azure Monitor, calculating P95 and P99 percentiles to set requests that accommodate typical usage while allowing headroom for spikes. The minAllowed and maxAllowed constraints prevent pathological recommendations—a container with a memory leak should not receive unlimited memory allocation, and a CPU-bound workload should not be capped below minimum viable CPU for responsiveness.

Cluster Autoscaler operates at the node pool level, adding nodes when pods are unschedulable due to insufficient resources and removing nodes when utilization falls below thresholds. The autoscaler respects node affinity rules, pod topology spread constraints, and PodDisruptionBudgets when making scaling decisions:

```bash
az aks nodepool update \
  --resource-group production-rg \
  --cluster-name production-aks \
  --name workerpool \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 20
```

Cluster autoscaler scale-up latency is bounded by Azure VM provisioning time, typically 2-4 minutes for standard instance types. This latency necessitates buffer capacity: configuring minimum node counts above steady-state requirements ensures immediate capacity for bursty workloads. Over-provisioning one or two nodes above minimum reduces the probability of pod scheduling delays during traffic surges.

Autoscaler scale-down is conservative to prevent thrashing. A node is considered for removal only if all running pods can be rescheduled onto other nodes without violating constraints, the node has been underutilized for at least 10 minutes (configurable), and removing the node does not trigger immediate scale-up. System pods with local storage or pods with PodDisruptionBudgets set to zero available replicas prevent scale-down, as do nodes running pods with hostPath volumes or local storage.

### Cost Optimization Through Resource Efficiency

Azure AKS compute costs derive from node pool VM instance charges, with additional costs for persistent storage, load balancers, and data egress. Optimizing total cost of ownership requires balancing resource efficiency (high utilization per node) against resilience (sufficient spare capacity for failover) and performance (low scheduling latency).

Spot instance node pools reduce compute costs by 70-90% compared to on-demand pricing, at the cost of potential eviction when Azure needs capacity for on-demand workloads. Spot nodes suit batch processing, stateless workers, and development environments where workload interruption is tolerable:

```bash
az aks nodepool add \
  --resource-group production-rg \
  --cluster-name production-aks \
  --name spotpool \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --node-count 5 \
  --enable-cluster-autoscaler \
  --min-count 0 \
  --max-count 20
```

Setting spot-max-price to -1 configures the maximum price to the current on-demand price, ensuring the instances are never evicted due to price fluctuations (only capacity shortages trigger eviction). Workloads on spot nodes must tolerate eviction through graceful shutdown handlers and should not require strict availability guarantees.

Azure Reserved Instances provide 40-60% discounts for one- or three-year commitments, suitable for predictable baseline capacity. The cost optimization strategy combines reserved instances for minimum capacity, on-demand instances for moderate overprovisioning, and spot instances for burst capacity. This three-tier model minimizes costs while maintaining availability.

Resource quotas and LimitRanges prevent resource exhaustion from rogue workloads. Namespace-level ResourceQuotas cap aggregate resource consumption:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    limits.cpu: "200"
    limits.memory: "400Gi"
    persistentvolumeclaims: "20"
    services.loadbalancers: "5"
```

LimitRanges enforce per-pod and per-container constraints, preventing individual pods from monopolizing node resources:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
spec:
  limits:
  - max:
      cpu: "8"
      memory: "16Gi"
    min:
      cpu: "100m"
      memory: "128Mi"
    default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "250m"
      memory: "256Mi"
    type: Container
```

These constraints enforce resource discipline: developers must specify resource requests and limits, and workloads exceeding quotas are rejected at admission time rather than causing cluster-wide resource contention.

### Failure Mode Analysis and Resilience Patterns

Production AKS clusters encounter failures across multiple domains: infrastructure (Azure region outages, network partitions, VM failures), software (kubelet crashes, containerd bugs, kernel panics), and application (memory leaks, deadlocks, cascading failures). Resilience engineering involves anticipating failure modes, implementing defense-in-depth mitigations, and practicing recovery through chaos engineering.

**Infrastructure failure modes** include Azure availability zone failures, regional outages, and network backbone disruptions. Zone-redundant node pools distribute nodes across three availability zones within a region, ensuring cluster capacity survives zone-level failures:

```bash
az aks nodepool add \
  --resource-group production-rg \
  --cluster-name production-aks \
  --name zoneredundant \
  --zones 1 2 3 \
  --node-count 9 \
  --enable-cluster-autoscaler \
  --min-count 9 \
  --max-count 30
```

Pod topology spread constraints distribute replicas across zones to prevent availability loss from zone failure:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-processor
  namespace: production
spec:
  replicas: 9
  template:
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: payment-processor
```

This constraint ensures replicas are evenly distributed across zones (maxSkew: 1 allows at most one replica difference between zones). If a zone fails, the two remaining zones continue serving requests with 6 out of 9 replicas, degrading capacity by 33% rather than causing total outage.

Regional outages require multi-region disaster recovery architecture. Active-passive configurations maintain a cold standby cluster in a secondary region, restored from periodic backups during outage. Active-active configurations distribute traffic across regions through Azure Traffic Manager or Azure Front Door, requiring cross-region data replication and conflict resolution. The operational complexity and cost scale with the desired RTO and RPO: sub-minute RTO demands synchronous replication and automated failover, while hourly RTO tolerates asynchronous backups and manual failover coordination.

**Software failure modes** include kubelet memory leaks, containerd socket unresponsiveness, and kernel deadlocks. Azure AKS applies automatic node repair, detecting unhealthy nodes through missed kubelet heartbeats and replacing them after a threshold period (typically 10-15 minutes). This self-healing is opaque to workloads: pods on the failed node transition to Unknown status, the scheduler reschedules them onto healthy nodes, and StatefulSets rebuild persistent volume attachments on the replacement node.

Container runtime failures manifest as inability to start new pods or exec into running containers. The containerd socket (/run/containerd/containerd.sock) may become unresponsive due to deadlock or resource exhaustion. The mitigation is systemd watchdog monitoring: systemd detects containerd unresponsiveness through missed watchdog heartbeats and restarts the containerd service. Existing containers continue running during restart, but new pod scheduling blocks until containerd recovers.

**Application failure modes** include memory leaks, thread pool exhaustion, database connection leaks, and cascading timeouts. Circuit breaker patterns prevent cascading failures by detecting elevated error rates and temporarily failing fast rather than overwhelming degraded downstream services:

```go
// Circuit breaker pattern for resilient service calls
type CircuitBreaker struct {
    maxFailures  int
    timeout      time.Duration
    state        int32 // 0=closed, 1=open, 2=half-open
    failures     int32
    lastFailTime time.Time
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    state := atomic.LoadInt32(&cb.state)
    
    if state == 1 { // Open
        if time.Since(cb.lastFailTime) > cb.timeout {
            atomic.StoreInt32(&cb.state, 2) // Half-open
        } else {
            return errors.New("circuit breaker open")
        }
    }
    
    err := fn()
    
    if err != nil {
        failures := atomic.AddInt32(&cb.failures, 1)
        cb.lastFailTime = time.Now()
        if failures >= int32(cb.maxFailures) {
            atomic.StoreInt32(&cb.state, 1) // Open
        }
        return err
    }
    
    atomic.StoreInt32(&cb.failures, 0)
    atomic.StoreInt32(&cb.state, 0) // Closed
    return nil
}
```

The circuit breaker transitions from closed (normal operation) to open (failing fast) after consecutive failures exceed a threshold. After a timeout period, it enters half-open state, allowing a single probe request. Success returns to closed state, while failure returns to open state. This prevents a degraded database from overwhelming the connection pool with retry storms, instead failing fast at the application layer and preserving capacity for other operations.

Bulkhead patterns isolate failure domains by partitioning resources into independent pools. Thread pools dedicated to specific service calls prevent one slow dependency from exhausting all threads:

```go
// Bulkhead pattern with dedicated goroutine pools
type Bulkhead struct {
    semaphore chan struct{}
    timeout   time.Duration
}

func NewBulkhead(maxConcurrent int, timeout time.Duration) *Bulkhead {
    return &Bulkhead{
        semaphore: make(chan struct{}, maxConcurrent),
        timeout:   timeout,
    }
}

func (b *Bulkhead) Execute(fn func() error) error {
    select {
    case b.semaphore <- struct{}{}:
        defer func() { <-b.semaphore }()
        
        done := make(chan error, 1)
        go func() { done <- fn() }()
        
        select {
        case err := <-done:
            return err
        case <-time.After(b.timeout):
            return errors.New("bulkhead timeout")
        }
    case <-time.After(b.timeout):
        return errors.New("bulkhead full")
    }
}
```

The bulkhead limits concurrent executions of a function to a fixed pool size. When the pool is exhausted, additional requests fail fast rather than queuing indefinitely. This isolates slow dependencies: a database query timeout affects only the bulkhead dedicated to that database, while other bulkheads (cache, external API) continue operating normally.

Chaos engineering validates resilience through controlled failure injection. Azure Chaos Studio provides managed fault injection for AKS, simulating pod failures, network latency, and disk I/O degradation. A typical chaos experiment injects pod failures into a percentage of replicas while monitoring service-level indicators:

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: payment-processor-chaos
  namespace: production
spec:
  action: pod-kill
  mode: fixed-percent
  value: "25"
  duration: "5m"
  selector:
    namespaces:
    - production
    labelSelectors:
      app: payment-processor
  scheduler:
    cron: "@every 1h"
```

This experiment kills 25% of payment-processor pods every hour, validating that the service maintains availability with reduced capacity. Observing SLO violations during chaos experiments reveals inadequate replication, missing PodDisruptionBudgets, or slow pod startup times requiring longer readiness probe initial delays.

Chaos experiments should progress from low-impact (pod restarts) to high-impact (zone failures, region failover) as confidence in system resilience grows. The operational goal is discovering failure modes in controlled conditions rather than during customer-facing incidents, building organizational muscle memory for incident response and runbook execution.

### Operational Excellence and Production Readiness

Production readiness encompasses technical preparedness (infrastructure automation, monitoring coverage, runbook documentation) and organizational preparedness (on-call rotation, incident response procedures, post-incident reviews). A production-ready AKS cluster exhibits these characteristics:

**Infrastructure as Code** with versioned Terraform/Bicep/ARM templates for all Azure resources, GitOps-managed Kubernetes manifests, and automated deployment pipelines. Infrastructure changes flow through pull requests with peer review and automated validation, ensuring reproducibility and preventing configuration drift.

**Comprehensive observability** with metrics, logs, and traces covering all critical paths. Service-level indicators (SLI) and service-level objectives (SLO) are defined, measured, and reviewed quarterly. Dashboards provide real-time visibility into golden signals (latency, traffic, errors, saturation) and alert thresholds trigger before SLO violations.

**Disaster recovery validation** through quarterly failover drills testing backup restoration, cross-region failover, and emergency runbook execution. RTO and RPO are measured during drills and compared against business requirements, with gaps driving infrastructure improvements.

**Security hardening** including Pod Security Standards enforcement, network policies restricting pod-to-pod communication, Azure AD workload identity for pod authentication, and regular vulnerability scanning of container images. Secrets are stored in Azure Key Vault and injected into pods through CSI secret drivers, never committed to Git.

**Capacity planning** with projected growth models, load testing validating scaling limits, and proactive resource procurement preventing quota exhaustion. Cost tracking attributes cluster spend to business units and applications, enabling chargeback and optimization.

**Incident response** with defined severity levels, escalation procedures, communication templates, and post-incident review processes. Incidents are treated as learning opportunities: blameless post-mortems identify systemic weaknesses and generate action items for resilience improvements.

Production operations transform from reactive firefighting to proactive reliability engineering when these practices become organizational habits, embedded in team culture through automation, documentation, and continuous improvement. The operational maturity of an AKS deployment reflects not only technical architecture but the discipline with which teams execute infrastructure lifecycle management, respond to incidents, and evolve systems under changing business requirements.
