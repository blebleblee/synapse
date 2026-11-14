# Lesson 5: Scaling, Scheduling, and Resource Management

## 1. First-Principles Intuition & Invariants

Kubernetes clusters exist in a state of perpetual tension between declared desired state and observed runtime reality. The control plane's reconciliation loops—etcd-backed state machines that continuously drive the cluster toward its declared configuration—must solve a fundamentally intractable problem: packing irregular, multi-dimensional workloads onto finite hardware resources while simultaneously optimizing for cost efficiency, fault tolerance, application performance, and operational simplicity. Azure Kubernetes Service (AKS) inherits this core Kubernetes challenge but layers additional complexity through its integration with Azure's hyperscale infrastructure, introducing cloud-native elasticity primitives that dynamically resize both the application tier (horizontal pod autoscaling) and the infrastructure tier (cluster autoscaling).

At the foundation of all resource management decisions lies the scheduler, a deterministic algorithm that evaluates every unbound pod against every eligible node in the cluster, computing a fitness score through a multi-stage filtering and scoring pipeline. The scheduler operates on a snapshot of cluster state at scheduling time, making decisions based on declared resource requests and limits, node capacity, existing pod placements, affinity and anti-affinity rules, taints and tolerations, and a constellation of policy constraints. Critically, the scheduler does not guarantee optimal global placement—it seeks only locally optimal decisions for each individual pod at the moment of scheduling. Once a pod binds to a node, it remains there until evicted or terminated, creating placement entropy over time as workloads scale up and down. This scheduling model produces a fundamental invariant: **resource allocation is declarative and forward-looking at scheduling time, but execution is imperative and backward-constrained by historical placement decisions**.

Resource requests and limits form the contract between application developers and the cluster infrastructure. A resource request represents the minimum guaranteed allocation—the scheduler will only place a pod on a node if the node has sufficient unallocated capacity to satisfy the request. A resource limit defines the maximum consumption ceiling—the kubelet will throttle CPU usage at this boundary and terminate pods that exceed memory limits. This two-tier model enables statistical multiplexing: by setting limits higher than requests, operators can overcommit cluster capacity, betting that not all workloads will simultaneously spike to their maximum resource consumption. Azure AKS node pools calculate allocatable capacity by subtracting system reservations (kubelet, OS, AKS control plane agents) from the VM's total capacity, and the scheduler's resource accounting operates strictly in terms of pod requests, ignoring actual runtime consumption.

The autoscaling subsystems—both horizontal pod autoscaling (HPA) and cluster autoscaling (CA)—close the feedback loop between observed metrics and declared cluster state by programmatically mutating Kubernetes resources in response to load. HPA monitors metrics from the Metrics Server (resource metrics like CPU and memory utilization) or custom metrics providers (application-specific metrics from Azure Monitor or Prometheus), computing target replica counts through proportional control algorithms and updating the replica count field in Deployment or StatefulSet specifications. Cluster Autoscaler monitors unschedulable pods—those rejected by the scheduler due to insufficient node capacity—and provisions new nodes from Azure Virtual Machine Scale Sets, expanding the cluster's resource envelope. Conversely, when nodes become underutilized and all running pods can be rescheduled elsewhere, CA drains and deletes nodes to reduce infrastructure costs.

These autoscaling mechanisms introduce temporal coupling and feedback instability. HPA scale-up decisions trigger pod creation, which may render the cluster resource-constrained and activate Cluster Autoscaler to provision new nodes, which incurs multi-minute VM boot latency before new capacity becomes schedulable. During this provisioning window, pending pods remain unscheduled, and application capacity lags behind demand. Similarly, CA scale-down requires careful coordination with pod disruption budgets and graceful termination periods to avoid violating application availability guarantees. The interaction between HPA's exponential backoff on scaling decisions and CA's conservative node removal heuristics creates a complex dynamical system where configuration parameters—cooldown periods, utilization thresholds, stability windows—directly determine the cluster's responsiveness, cost efficiency, and resilience to cascading failures.

Azure AKS extends baseline Kubernetes scheduling and autoscaling with cloud-native integration points. Node pools map to Azure Virtual Machine Scale Sets, enabling heterogeneous cluster topologies where different workload classes run on nodes with different VM SKUs, disk configurations, and network policies. System node pools host critical cluster infrastructure (CoreDNS, metrics-server, AKS monitoring agents) and are typically tainted to prevent user workload placement, while user node pools serve application pods. AKS supports multiple node pool scaling modes: manual scaling where operators explicitly set node counts, autoscaling where Cluster Autoscaler manages scale sets dynamically, and integration with Azure Virtual Machine Scale Set's native autoscaling when workloads can tolerate the simplified, node-centric scaling model without Kubernetes awareness.

The scheduler's filtering and scoring phases implement a pipeline architecture that progressively narrows the set of candidate nodes for each pod. During filtering, predicate functions eliminate nodes that fail hard constraints: insufficient CPU or memory to satisfy resource requests, mismatched node selectors or taints without corresponding tolerations, violated pod affinity or anti-affinity rules, or unavailable persistent volumes. The surviving candidate nodes enter the scoring phase, where priority functions assign numerical weights based on resource balance (preferring nodes with balanced CPU-to-memory ratios after placement), pod spreading (preferring nodes that increase replica distribution across failure domains), and configured scheduling policies. The node with the highest aggregate score wins the pod binding, and the scheduler writes a Binding object to etcd, atomically associating the pod with the node.

Taints and tolerations implement a negative constraint system that inverts the default scheduling model. A taint applied to a node repels all pods unless those pods explicitly tolerate the taint. AKS applies system taints to nodes during maintenance operations, cordoning them from new pod placements while allowing existing pods to continue running. Custom taints enable workload isolation patterns: tainting GPU nodes ensures only GPU-dependent workloads can schedule there, preventing resource waste from general-purpose pods consuming expensive accelerated compute. Tolerations in pod specifications must match the taint's key, value, and effect—NoSchedule (prevent scheduling), PreferNoSchedule (soft constraint), or NoExecute (evict running pods). This mechanism provides coarse-grained admission control at the node level, complementing the fine-grained resource-based filtering in the scheduler's predicate phase.

Affinity and anti-affinity rules encode topological preferences and constraints using label selectors and topology keys. Pod affinity attracts related pods to co-locate on the same node or within the same availability zone, reducing inter-pod network latency for tightly coupled microservices. Pod anti-affinity repels pods, forcing the scheduler to distribute replicas across nodes or zones to improve fault tolerance. Node affinity constrains pod placement to nodes matching label criteria, enabling patterns like placing data-intensive workloads on nodes with locally attached NVMe drives. AKS clusters use topology keys like `topology.kubernetes.io/zone` to map Kubernetes abstractions to Azure infrastructure, allowing applications to declare zone-spreading requirements without directly coupling to Azure-specific APIs. The scheduler evaluates affinity rules during both filtering (required rules eliminate non-matching nodes) and scoring (preferred rules increase node scores), creating a flexible constraint satisfaction system that balances operator policy with resource availability.

Capacity planning in elastic cloud environments requires reasoning about multiple resource dimensions simultaneously. CPU and memory are compressible and incompressible resources respectively—CPU throttling degrades performance but does not crash processes, while memory exhaustion triggers OOM kills and pod evictions. Network bandwidth and disk I/O represent additional resource axes that Kubernetes models only indirectly through pod resource requests and quality-of-service classes. Azure VM SKUs present heterogeneous resource profiles: compute-optimized instances provide high CPU-to-memory ratios, memory-optimized instances invert this ratio, and general-purpose instances balance both. Selecting appropriate VM SKUs for node pools becomes an optimization problem constrained by workload resource request profiles, scaling elasticity requirements, and Azure's per-VM pricing model.

The Kubernetes quality-of-service model classifies pods into three tiers based on resource specification completeness. Guaranteed pods declare identical requests and limits for all containers, ensuring they receive dedicated resource allocations and face eviction only when node resource pressure reaches critical levels. Burstable pods specify requests lower than limits or omit limits entirely, allowing them to consume unused node capacity opportunistically but facing eviction before Guaranteed pods during resource contention. BestEffort pods omit resource specifications entirely, operating in the residual capacity margins and facing immediate eviction when any resource pressure emerges. AKS node agents (kubelet) implement this eviction hierarchy through cgroup-based resource enforcement and kernel-level OOM score adjustments, ensuring that critical system workloads survive resource starvation scenarios.

Pod disruption budgets (PDBs) formalize the contract between application owners and cluster infrastructure regarding voluntary disruptions—node drains for upgrades, cluster autoscaler scale-downs, or manual evictions. A PDB specifies either the minimum number of replicas that must remain available or the maximum number that can be unavailable during disruptions, preventing operations that would violate application availability guarantees. When Cluster Autoscaler evaluates a node for scale-down, it simulates evicting all pods and verifies that no PDB would be violated. If eviction would breach a PDB, the node remains in the cluster. This coordination mechanism prevents autoscaling from inadvertently degrading application availability, but it also introduces a failure mode: overly restrictive PDBs can render clusters unscalable, trapping underutilized nodes in the cluster because pod eviction always violates availability constraints.

Azure AKS introduces additional architectural considerations through its managed control plane model. The control plane components—API server, etcd, scheduler, controller manager—run on infrastructure managed by Microsoft, introducing resource capacity limits distinct from user node pools. API server rate limits throttle excessive client requests, and etcd storage quotas bound the cluster's total object count. Large-scale AKS clusters must account for control plane overhead: each pod, service, and ConfigMap consumes etcd storage and API server processing capacity. At extreme scales, control plane bottlenecks can manifest as scheduling latency increases, failed API write operations due to etcd transaction timeouts, or webhook admission controller failures under heavy load. Azure manages control plane capacity scaling transparently, but operators must architect workloads to minimize control plane load—batching API operations, caching frequently read objects client-side, and avoiding excessive pod churn.

## 2. Core Architecture & Mechanics

The Kubernetes scheduler implements a two-phase algorithm: filtering followed by scoring. Each scheduling cycle begins when the scheduler's watch stream observes a pod in the `Pending` state with no `spec.nodeName` binding. The scheduler pulls a consistent snapshot of cluster state from its cache—synchronized continuously from etcd via the API server's watch mechanism—and enters the filtering phase.

**Filtering Phase Pipeline**:

```
Pod (Pending, nodeName="")
    ↓
  Cache Snapshot (Nodes, Pods, PVs, PVCs)
    ↓
  Predicate: PodFitsResources
    → Σ(pod.requests) + newPod.requests ≤ node.allocatable
    → Filter nodes with insufficient CPU/memory
    ↓
  Predicate: PodMatchNodeSelector
    → node.labels ⊇ pod.spec.nodeSelector
    ↓
  Predicate: PodToleratesNodeTaints
    → ∀ taint ∈ node.taints: ∃ toleration ∈ pod.tolerations
    ↓
  Predicate: CheckVolumeBinding
    → Verify PVC → PV bindings satisfy zone constraints
    ↓
  Predicate: PodAffinityMatches
    → Evaluate required affinity/anti-affinity rules
    ↓
  Candidate Nodes (survivors of all predicate filters)
```

If the candidate set is empty after filtering, the scheduler marks the pod as `Unschedulable` and emits a scheduling failure event. Cluster Autoscaler listens for these events and evaluates whether provisioning additional nodes would make the pod schedulable. If CA determines a new node from an available node pool would satisfy the pod's constraints, it increments the corresponding Azure Virtual Machine Scale Set's desired capacity, triggering VM provisioning.

**Scoring Phase**:

The scoring phase assigns numerical weights to each candidate node by evaluating priority functions. Each function returns a score in [0, 100], which the scheduler normalizes and combines using configurable weights.

```
For each candidate node n:
  score(n) = Σ [weight_i × priorityFunc_i(n, pod)]

Common Priority Functions:
  - LeastRequestedPriority: 
      score = 100 × (1 - (Σ allocated / capacity))
      Prefers nodes with most free resources
  
  - BalancedResourceAllocation:
      cpuFraction = Σ cpu_requests / cpu_capacity
      memFraction = Σ mem_requests / mem_capacity
      score = 100 - |cpuFraction - memFraction| × 100
      Prefers balanced CPU/memory utilization
  
  - SelectorSpreadPriority:
      score = 100 × (1 - (podCount_on_node / max_podCount_on_any_node))
      Spreads pods across nodes for replica distribution
  
  - NodeAffinityPriority:
      score = weight × (preferred affinity match strength)
```

After computing scores, the scheduler selects the highest-scoring node and performs an optimistic bind operation: it writes a `Binding` object to etcd, atomically setting `pod.spec.nodeName`. If the bind fails due to concurrent modification (another scheduler instance scheduled a different pod to the node, exhausting remaining capacity), the scheduler retries the entire cycle. Once bound, the pod transitions to the kubelet on the target node, which pulls container images, provisions volumes, configures cgroups, and launches containers.

**Resource Request and Limit Enforcement**:

Kubelet translates Kubernetes resource specifications into Linux cgroup hierarchies on each node:

```
/sys/fs/cgroup/
├── cpu/
│   └── kubepods/
│       ├── burstable/
│       │   └── pod<uid>/
│       │       ├── cpu.shares = (request_millicores / 1024) × 1024
│       │       └── cpu.cfs_quota_us = (limit_millicores / 1000) × cfs_period_us
│       ├── besteffort/
│       │   └── pod<uid>/
│       │       └── cpu.shares = 2  (minimal allocation)
│       └── guaranteed/
│           └── pod<uid>/
│               ├── cpu.shares = (request_millicores / 1024) × 1024
│               └── cpu.cfs_quota_us = (limit_millicores / 1000) × 100000
└── memory/
    └── kubepods/
        ├── burstable/
        │   └── pod<uid>/
        │       └── memory.limit_in_bytes = limit_bytes
        ├── besteffort/
        │   └── pod<uid>/
        │       └── memory.limit_in_bytes = node_allocatable
        └── guaranteed/
            └── pod<uid>/
                └── memory.limit_in_bytes = request_bytes (== limit_bytes)
```

CPU requests map to `cpu.shares`, implementing proportional CPU allocation during contention: a pod with 1000m CPU shares receives twice the CPU time of a 500m pod when both compete for cycles. CPU limits map to CFS (Completely Fair Scheduler) bandwidth control via `cpu.cfs_quota_us` and `cpu.cfs_period_us`, hard-capping CPU consumption. If a pod's containers exhaust their quota within a period, the kernel throttles them until the next period begins.

Memory limits map directly to `memory.limit_in_bytes`. When a container exceeds its memory limit, the kernel's OOM killer selects a process to terminate based on OOM score adjustments—kubelet sets lower OOM scores for Guaranteed pods and higher scores for BestEffort pods. The killed container triggers a pod restart according to the container's restart policy.

**Horizontal Pod Autoscaler Control Loop**:

HPA implements a proportional controller that adjusts replica counts based on observed metric values:

```
desiredReplicas = ceil(currentReplicas × (currentMetric / targetMetric))
```

For CPU utilization-based scaling:

```
currentMetricValue = Σ(pod CPU usage) / Σ(pod CPU requests)
desiredReplicas = ceil(currentReplicas × (currentMetricValue / targetUtilization))
```

HPA queries the Metrics Server API every 15 seconds (configurable via `--horizontal-pod-autoscaler-sync-period`), retrieves pod resource metrics, computes the desired replica count, and updates the target resource's `spec.replicas` field if the calculated change exceeds a tolerance threshold (default 10%). To prevent flapping, HPA implements exponential backoff: after a scale-up event, it delays scale-down decisions for a stabilization window (default 5 minutes). After a scale-down, it delays further scale-downs for 5 minutes but allows immediate scale-up if metrics spike.

**Cluster Autoscaler Decision Logic**:

Cluster Autoscaler runs as a Deployment in the cluster, watching for unschedulable pods and underutilized nodes. Its core algorithm evaluates scale-up and scale-down conditions independently:

**Scale-Up Logic**:

```
For each unschedulable pod p:
  For each node pool (Azure VMSS):
    Simulate: if we added a node from this pool, could p schedule?
    Compute: cost = VM price per hour
  
  Select node pool with lowest cost that satisfies p's constraints
  If no pool satisfies constraints: pod remains unschedulable
  
  Increment VMSS desired capacity by N nodes (batch expansion)
  Wait for Azure to provision VMs and join cluster
```

CA batches expansion requests to reduce Azure API call overhead and improve provisioning parallelism. It will not scale up if the node pool has reached its maximum size or if adding nodes would exceed Azure quota limits.

**Scale-Down Logic**:

```
For each node n:
  If node utilization > threshold (default 50%): skip
  If node age < 10 minutes: skip (prevent flapping)
  
  Simulate: can all pods on n be rescheduled to other nodes?
  For each pod on n:
    If pod has local storage: check if other nodes satisfy constraints
    If evicting pod would violate PDB: abort scale-down
    If pod is a DaemonSet: allow (will recreate on remaining nodes)
  
  If all pods can reschedule: cordon and drain node
  After drain completes: delete Azure VM from VMSS
```

CA calculates node utilization as:

```
utilization = max(
  Σ(pod CPU requests) / node.allocatable.cpu,
  Σ(pod memory requests) / node.allocatable.memory
)
```

Critically, CA uses resource requests, not actual consumption, to evaluate utilization. A node running pods with high requests but low actual usage appears highly utilized to CA and will not be scaled down, even though it consumes minimal physical resources. This request-based accounting aligns with the scheduler's placement decisions but can lead to resource waste if pods over-request resources.

**Node Pool Management in AKS**:

Azure AKS clusters consist of one or more node pools, each backed by a Virtual Machine Scale Set:

```
AKS Cluster
├── System Node Pool (tainted CriticalAddonsOnly=true:NoSchedule)
│   └── VMSS: Standard_D4s_v5 × 3 nodes
│       ├── CoreDNS pods
│       ├── metrics-server
│       ├── azure-cni-manager
│       └── kube-proxy DaemonSet
├── User Node Pool: workload-general
│   └── VMSS: Standard_D8s_v5 × 5–20 nodes (autoscaling)
│       └── Application pods
└── User Node Pool: workload-memory
    └── VMSS: Standard_E16s_v5 × 2–10 nodes (autoscaling)
        └── In-memory cache pods
```

System node pools host cluster infrastructure and should not autoscale to zero to prevent control plane dependency failures. User node pools run application workloads and can autoscale to zero if cost optimization is critical, though this incurs cold-start latency when scaling from zero.

**Taints and Tolerations Workflow**:

```
# Node with GPU, tainted to prevent general workload placement
Node: gpu-node-01
  Taints:
    - key: nvidia.com/gpu
      value: "true"
      effect: NoSchedule

# Pod requiring GPU, with matching toleration
Pod: ml-training-job
  Tolerations:
    - key: nvidia.com/gpu
      operator: Equal
      value: "true"
      effect: NoSchedule
  Resources:
    Limits:
      nvidia.com/gpu: 1

Scheduler Evaluation:
  1. Filter Phase: PodToleratesNodeTaints
     → Pod has toleration matching nvidia.com/gpu taint
     → gpu-node-01 remains in candidate set
  
  2. Scoring Phase: NodeResourcesFit
     → Verify nvidia.com/gpu resource available
     → Assign score based on resource balance
  
  3. Bind pod to gpu-node-01
```

Without the toleration, the scheduler would eliminate `gpu-node-01` during filtering, and the pod would remain unschedulable if no other nodes provide GPU resources.

**Affinity and Anti-Affinity Rules**:

Pod affinity uses label selectors to match existing pods and topology keys to define co-location domains:

```yaml
# Deploy web pods anti-affinity to spread across availability zones
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
spec:
  replicas: 6
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - web-frontend
              topologyKey: topology.kubernetes.io/zone
```

This configuration forces the scheduler to place each replica in a different Azure availability zone (if sufficient zones exist). The `requiredDuringScheduling` constraint makes this a hard requirement—if fewer than six zones are available, excess replicas remain unscheduled. Using `preferredDuringScheduling` softens this into a scoring preference rather than a hard filter.

**Pod Disruption Budget Coordination**:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: cache-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: redis-cache
```

When Cluster Autoscaler evaluates a node for scale-down:

```
Node: workload-node-05
Running Pods:
  - redis-cache-1 (app=redis-cache)
  - redis-cache-2 (app=redis-cache)
  - web-frontend-3 (app=web-frontend)

CA Scale-Down Simulation:
  1. Check PDB for redis-cache
     Current available replicas: 5 (across all nodes)
     MinAvailable: 2
     
  2. Simulate evicting redis-cache-1 and redis-cache-2
     Remaining available replicas: 3
     3 ≥ 2 → PDB satisfied
  
  3. Check if pods can reschedule to other nodes
     Scheduler simulation: sufficient capacity exists
  
  4. Proceed with drain and scale-down
```

If evicting pods from the node would leave fewer than two `redis-cache` replicas available cluster-wide, CA aborts the scale-down and marks the node as unremovable.

**Azure VMSS Integration**:

AKS node pools map directly to Azure Virtual Machine Scale Sets, and Cluster Autoscaler interacts with VMSS via the Azure Resource Manager API:

```
CA observes unschedulable pod → determine required VM SKU
CA API call: PUT /subscriptions/{sub}/resourceGroups/{rg}/providers/
             Microsoft.Compute/virtualMachineScaleSets/{vmss-name}
             ?api-version=2023-09-01
Body:
  {
    "sku": { "capacity": current + N }
  }

Azure provisions VMs from scale set template
VMs boot, kubelet starts, nodes register with API server
Scheduler observes new nodes, schedules pending pods
```

VMSS supports multiple scaling modes: uniform (all VMs identical, common for AKS) and flexible (heterogeneous VMs, advanced scenarios). AKS uses uniform scale sets with fixed VM configurations defined at node pool creation time. To change VM SKU or OS image, operators must create a new node pool and migrate workloads, as VMSS does not support in-place VM reconfiguration.

**Quality-of-Service Enforcement**:

When kubelet detects node memory pressure (available memory falls below `memory.available` threshold), it triggers eviction:

```
Memory Pressure Thresholds:
  - Soft: memory.available < 1.5Gi for 90s → evict BestEffort pods
  - Hard: memory.available < 750Mi → immediate eviction cascade

Eviction Order:
  1. BestEffort pods (no memory request/limit)
  2. Burstable pods exceeding requests (usage > request)
  3. Burstable pods within requests (usage ≤ request)
  4. Guaranteed pods (only as last resort)

Within each QoS tier, evict pods with highest:
  priority = (memory_usage - memory_request) / memory_request
```

Kubelet also adjusts OOM scores for processes in each cgroup:

```
BestEffort:     oom_score_adj = 1000 (highest, killed first)
Burstable:      oom_score_adj = min(1000, 1000 - (request/limit × 1000))
Guaranteed:     oom_score_adj = -998 (lowest, killed last)
System (kubelet, containerd): oom_score_adj = -999 (nearly unkillable)
```

When the kernel OOM killer activates (global memory exhaustion), it selects the process with the highest OOM score, ensuring BestEffort pods are sacrificed before critical system components.

## 3. High-Performance Optimization & Failure Modes

Production AKS deployments require careful tuning of scheduler policies, autoscaler parameters, and resource specifications to balance cost, performance, and resilience. The default configurations optimize for general-purpose workloads but often produce suboptimal behavior in specialized scenarios: batch processing jobs, stateful data systems, latency-sensitive user-facing services, and high-throughput data pipelines each demand distinct optimization strategies.

**Optimizing Scheduler Performance**:

The default scheduler performs well for clusters with hundreds of nodes and thousands of pods, but at hyperscale (10k+ nodes), scheduling latency becomes a bottleneck. The scheduler's O(N) filtering and scoring complexity—where N is the number of nodes—grows linearly with cluster size. For extremely large clusters, enable scheduler performance tuning via `--kube-scheduler-config`:

Create a scheduler configuration file limiting the percentage of nodes evaluated during scoring:

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: default-scheduler
    plugins:
      score:
        disabled:
          - name: NodeResourcesBalancedAllocation  # Disable expensive scoring
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated  # Bin-pack aggressively to maximize node density
      - name: InterPodAffinity
        args:
          hardPodAffinityWeight: 1
```

For workloads with strict latency requirements, implement node affinity to constrain scheduling to a subset of pre-warmed nodes, reducing scheduler search space:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: latency-sensitive-api
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: workload-class
                operator: In
                values:
                  - latency-optimized
  containers:
    - name: api
      image: api-server:v2.1
      resources:
        requests:
          cpu: "4"
          memory: 8Gi
        limits:
          cpu: "4"
          memory: 8Gi
```

This configuration pre-filters the node set to only those labeled `workload-class=latency-optimized`, bypassing scheduler evaluation of hundreds of irrelevant nodes.

**Tuning Horizontal Pod Autoscaler**:

HPA's default CPU utilization target (80%) and metric resolution (15s polling interval) suit general web services but fail for workloads with bursty traffic patterns or slow scale-up latency. For traffic-driven services with predictable daily patterns, combine HPA with scheduled scaling to pre-warm capacity before load spikes:

```yaml
# Base HPA for reactive scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment
  minReplicas: 10
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0  # Immediate scale-up
      policies:
        - type: Percent
          value: 100  # Double replicas each cycle
          periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scale-down
      policies:
        - type: Pods
          value: 4  # Remove 4 pods per cycle
          periodSeconds: 60
```

The `behavior` section configures asymmetric scaling: aggressive scale-up (doubling capacity every 15 seconds) and conservative scale-down (removing 4 pods per minute). This prevents capacity shortfalls during traffic surges while avoiding over-aggressive scale-down that would cause replica churn.

For custom metrics (e.g., request queue depth from Azure Application Insights), configure HPA with external metrics:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: queue-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: queue-processor
  minReplicas: 5
  maxReplicas: 200
  metrics:
    - type: External
      external:
        metric:
          name: azure_servicebus_queue_messages
          selector:
            matchLabels:
              queue: orders-processing
        target:
          type: AverageValue
          averageValue: "30"  # Scale to maintain ~30 messages per pod
```

This configuration scales based on Service Bus queue depth, maintaining approximately 30 messages per pod. When queue depth exceeds 30 × current replicas, HPA scales up proportionally.

**Cluster Autoscaler Configuration**:

Cluster Autoscaler's default parameters optimize for cost over performance, introducing multi-minute latency during scale-up events. For latency-sensitive workloads, reduce scale-up delay by enabling faster node provisioning:

```yaml
# Cluster Autoscaler ConfigMap override
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |
    10:
      - .*-spot-.*  # Prefer spot instances first (lowest cost)
    50:
      - .*-general-.*  # Fall back to general-purpose on-demand
    100:
      - .*-performance-.*  # Use high-performance nodes as last resort
```

Configure CA command-line flags for aggressive scaling:

```
--scale-down-delay-after-add=1m         # Scale down 1 min after scale-up
--scale-down-unneeded-time=2m           # Mark node unneeded after 2 min underutilization
--scale-down-utilization-threshold=0.5  # Scale down if utilization < 50%
--max-node-provision-time=10m           # Fail scale-up if VM takes >10 min
--scan-interval=10s                     # Evaluate scaling every 10s
```

These settings reduce scale-down stabilization time from the default 10 minutes to 2 minutes, improving cost efficiency at the expense of increased scaling churn. For production systems with steady-state load, use longer stabilization windows (10–15 minutes) to prevent oscillation.

**Failure Mode: Scheduler Thrashing**:

When pod resource requests greatly exceed actual usage, the cluster appears full to the scheduler while nodes remain mostly idle. This triggers Cluster Autoscaler to provision new nodes, but newly scheduled pods also under-consume their requests, perpetuating expansion. The cluster grows unbounded until hitting Azure quota limits or budget caps.

**Mitigation**: Implement Vertical Pod Autoscaler (VPA) to right-size resource requests based on observed usage:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment
  updatePolicy:
    updateMode: "Auto"  # Automatically apply recommendations
  resourcePolicy:
    containerPolicies:
      - containerName: api
        minAllowed:
          cpu: 100m
          memory: 128Mi
        maxAllowed:
          cpu: "4"
          memory: 8Gi
```

VPA monitors pod resource consumption over time and updates resource requests to match the 90th percentile of observed usage plus a safety margin. This prevents request inflation while maintaining headroom for traffic spikes.

**Failure Mode: Cluster Autoscaler Deadlock**:

When PodDisruptionBudgets are too restrictive, Cluster Autoscaler cannot scale down underutilized nodes because evicting any pod would violate availability constraints. The cluster remains over-provisioned indefinitely, wasting cost.

**Example**:

```
Node Pool: 10 nodes
Workload: Redis StatefulSet with 10 replicas (one per node)
PDB: minAvailable: 10

CA Scale-Down Logic:
  For each node:
    Evicting pod would reduce available replicas to 9
    9 < 10 → PDB violated
    Abort scale-down
  
  Result: All 10 nodes marked as unremovable
```

**Mitigation**: Use `maxUnavailable` instead of `minAvailable` for StatefulSets, allowing temporary unavailability during voluntary disruptions:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: redis-pdb
spec:
  maxUnavailable: 1  # Allow one replica unavailable during disruptions
  selector:
    matchLabels:
      app: redis
```

This permits CA to scale down one node at a time, evicting one Redis replica and allowing the StatefulSet controller to reschedule it on a remaining node before proceeding with further scale-down.

**Failure Mode: Scheduling Hot Spots**:

The scheduler's score-based placement creates uneven load distribution over time. Nodes that happen to have balanced CPU and memory after pod placement receive higher scores, attracting more pods and becoming oversubscribed. Meanwhile, nodes with imbalanced utilization (high CPU, low memory or vice versa) score poorly and remain underutilized.

**Mitigation**: Enable pod topology spread constraints to enforce even distribution:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
spec:
  replicas: 30
  template:
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: web-frontend
```

This constraint ensures that the difference in pod count between any two nodes never exceeds 1, enforcing uniform distribution. If achieving perfect balance is impossible (e.g., 30 pods across 7 nodes), the scheduler will leave some replicas unscheduled rather than violating the constraint.

**Capacity Planning and Node Pool Sizing**:

Azure VM SKUs present a discrete optimization problem: selecting the optimal SKU requires modeling workload resource profiles and pack density. For applications with heterogeneous resource requirements, multiple node pools with specialized SKUs outperform a single general-purpose pool.

**Example Analysis**:

```
Workload Profile:
  - API Pods: 2 CPU, 4 GiB memory (CPU-heavy)
  - Cache Pods: 0.5 CPU, 16 GiB memory (memory-heavy)
  - Workers: 1 CPU, 2 GiB memory (balanced)

Single Node Pool (Standard_D8s_v5: 8 CPU, 32 GiB):
  Best case: 3 API + 1 Cache + 2 Workers = 8.5 CPU, 30 GiB
  → Underutilizes memory, wastes 2 GiB per node

Specialized Node Pools:
  - Pool A (Standard_F8s_v2: 8 CPU, 16 GiB): API pods
    4 API pods = 8 CPU, 16 GiB (perfect fit)
  - Pool B (Standard_E16s_v5: 16 CPU, 128 GiB): Cache pods
    7 Cache pods = 3.5 CPU, 112 GiB (memory-optimized)
  - Pool C (Standard_D4s_v5: 4 CPU, 16 GiB): Workers
    4 Workers = 4 CPU, 8 GiB (general-purpose)

Result: 15–20% cost reduction through improved pack density
```

Implement this via multiple AKS node pools with node affinity:

```bash
# Create compute-optimized pool for API
az aks nodepool add \
  --resource-group prod-rg \
  --cluster-name prod-aks \
  --name apipool \
  --node-count 3 \
  --node-vm-size Standard_F8s_v2 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 20 \
  --labels workload=api \
  --node-taints workload=api:NoSchedule

# Create memory-optimized pool for cache
az aks nodepool add \
  --resource-group prod-rg \
  --cluster-name prod-aks \
  --name cachepool \
  --node-count 2 \
  --node-vm-size Standard_E16s_v5 \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --labels workload=cache \
  --node-taints workload=cache:NoSchedule
```

Deploy workloads with node affinity and tolerations:

```yaml
# API Deployment targeting compute-optimized pool
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 12
  template:
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: workload
                    operator: In
                    values:
                      - api
      tolerations:
        - key: workload
          operator: Equal
          value: api
          effect: NoSchedule
      containers:
        - name: api
          image: api-server:v3.2
          resources:
            requests:
              cpu: "2"
              memory: 4Gi
            limits:
              cpu: "2"
              memory: 4Gi
```

**Advanced: Binpacking vs. Spreading Strategies**:

The scheduler's default `LeastRequestedPriority` spreads pods across nodes to maximize available capacity for future workloads. For batch processing jobs that should pack densely onto nodes to minimize total node count (and cost), override with `MostRequestedPriority`:

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
  - schedulerName: batch-scheduler
    plugins:
      score:
        enabled:
          - name: NodeResourcesFit
            weight: 100
        disabled:
          - name: NodeResourcesLeastAllocated
    pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
```

Deploy batch jobs using this custom scheduler:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processing
spec:
  template:
    spec:
      schedulerName: batch-scheduler
      containers:
        - name: processor
          image: data-processor:v2.0
          resources:
            requests:
              cpu: "1"
              memory: 2Gi
            limits:
              cpu: "1"
              memory: 2Gi
```

This configuration packs jobs onto the fewest nodes, allowing Cluster Autoscaler to scale down unused nodes aggressively after jobs complete.

**Monitoring and Observability**:

Effective capacity planning requires continuous monitoring of scheduler decisions, autoscaler actions, and resource utilization. Key metrics to track:

```
Scheduler Metrics (from kube-scheduler):
  - scheduler_pending_pods: unscheduled pod count
  - scheduler_schedule_attempts_total: total scheduling attempts
  - scheduler_scheduling_duration_seconds: scheduling latency

Cluster Autoscaler Metrics:
  - cluster_autoscaler_unschedulable_pods_count: pods triggering scale-up
  - cluster_autoscaler_nodes_count: current node count by pool
  - cluster_autoscaler_scaled_up_nodes_total: cumulative scale-up events
  - cluster_autoscaler_scaled_down_nodes_total: cumulative scale-down events

Node Resource Metrics (from kubelet):
  - node_cpu_usage_seconds_total: actual CPU consumption
  - node_memory_working_set_bytes: memory in use
  - kube_node_status_allocatable: allocatable capacity per node
  - kube_pod_container_resource_requests: requested resources
```

Integrate these metrics into Azure Monitor or Prometheus and create alerting rules for anomalies:

```yaml
# Prometheus alerting rule
groups:
  - name: autoscaling
    rules:
      - alert: PersistentUnschedulablePods
        expr: scheduler_pending_pods > 0
        for: 5m
        annotations:
          summary: "Pods unschedulable for >5 minutes"
          description: "{{ $value }} pods cannot be scheduled. Check node capacity and CA status."
      
      - alert: ClusterAutoscalerDisabled
        expr: absent(cluster_autoscaler_nodes_count)
        for: 2m
        annotations:
          summary: "Cluster Autoscaler not reporting metrics"
          description: "CA may have crashed or is disabled."
```

**Graceful Node Shutdown and Draining**:

During node maintenance or scale-down, kubelet must drain pods gracefully to prevent service disruptions. The drain process involves:

1. Mark node as unschedulable (cordon)
2. Evict all pods respecting PodDisruptionBudgets and termination grace periods
3. Wait for pod termination to complete
4. Shut down kubelet and remove node from cluster

Azure AKS automatically handles drain during VMSS scale-down, but manual node maintenance requires explicit draining:

```bash
# Drain node for maintenance
kubectl drain aks-nodepool-12345-vmss000003 \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=300 \
  --timeout=10m

# Perform maintenance (Azure Portal or CLI)

# Uncordon node when ready
kubectl uncordon aks-nodepool-12345-vmss000003
```

For applications with long shutdown sequences (database checkpoints, cache flushes), configure extended termination grace periods:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: database
spec:
  terminationGracePeriodSeconds: 600  # 10 minutes
  containers:
    - name: postgres
      image: postgres:16
      lifecycle:
        preStop:
          exec:
            command:
              - /bin/sh
              - -c
              - |
                # Wait for connections to drain
                sleep 30
                # Initiate graceful shutdown
                pg_ctl stop -D /var/lib/postgresql/data -m smart
```

The `preStop` hook executes before SIGTERM, allowing the container to perform clean shutdown procedures. Kubernetes waits up to `terminationGracePeriodSeconds` before sending SIGKILL.

**Cost Optimization: Spot Node Pools**:

Azure Spot VMs offer significant discounts (up to 90%) for interruptible workloads. AKS supports spot node pools for fault-tolerant batch processing, CI/CD runners, and stateless services:

```bash
az aks nodepool add \
  --resource-group prod-rg \
  --cluster-name prod-aks \
  --name spotpool \
  --node-count 5 \
  --node-vm-size Standard_D8s_v5 \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --enable-cluster-autoscaler \
  --min-count 0 \
  --max-count 50 \
  --labels workload=batch priority=spot \
  --node-taints priority=spot:NoSchedule
```

Deploy tolerant workloads with spot tolerations:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-processing
spec:
  template:
    spec:
      tolerations:
        - key: priority
          operator: Equal
          value: spot
          effect: NoSchedule
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                  - key: priority
                    operator: In
                    values:
                      - spot
      containers:
        - name: processor
          image: batch-processor:v1.0
```

When Azure evicts a spot VM (typically with 30 seconds notice), pods receive SIGTERM and must terminate within their grace period. Jobs with checkpointing can resume on replacement nodes, minimizing wasted computation.

Scaling and resource management in AKS demands a systems-level understanding of how Kubernetes scheduler decisions, autoscaler control loops, Azure infrastructure provisioning, and application resource profiles interact to determine cluster behavior. Operators must carefully balance competing objectives—cost efficiency, performance, availability, and operational simplicity—through deliberate configuration of resource requests, QoS classes, autoscaling parameters, node pool topology, and workload placement policies. The default configurations provide a reasonable starting point, but production deployments require continuous measurement, analysis, and tuning to achieve optimal outcomes in dynamic cloud environments.
