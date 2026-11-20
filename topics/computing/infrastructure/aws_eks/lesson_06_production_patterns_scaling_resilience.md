# Lesson 6: Production Patterns, Multi-AZ Scaling, Disaster Recovery, and Large-Scale Operations

## 1. First-Principles Intuition & Invariants

Operating Amazon EKS at scale transforms the cluster from a single stateful system into a distributed, multi-region state machine with thousands of concurrent reconciliation loops, autonomous scaling decisions, and complex failure boundaries. The transition from prototype to production-grade infrastructure demands rigorous attention to availability zones as failure domains, autoscaling as a control theory problem, and disaster recovery as a formal state replication protocol. This lesson establishes the engineering foundations for running EKS clusters that serve critical workloads across availability zones, survive datacenter failures, and scale elastically from dozens to thousands of nodes while maintaining cost efficiency and operational predictability.

The core invariant governing production EKS architectures is the separation between control plane state and data plane capacity. AWS manages the Kubernetes control plane—etcd, API server, controller manager, and scheduler—across multiple availability zones within a region, replicating state through Raft consensus and exposing a single regional API endpoint. This managed control plane provides a guaranteed SLA but introduces a critical constraint: the customer cannot directly observe or tune control plane resource allocation, etcd disk IOPS, or API server request queuing. All operational interventions occur through the data plane, where worker nodes execute pods, route traffic, and store ephemeral state. The distinction matters because control plane availability depends on AWS's internal replication mechanisms, while data plane resilience requires explicit multi-AZ node placement, pod topology constraints, and storage redundancy.

Availability zones represent physically isolated datacenters within an AWS region, connected by low-latency fiber links but designed to fail independently. Each zone has separate power grids, cooling systems, and network backbones. When designing multi-AZ EKS clusters, engineers must reason about failure domains at multiple layers: individual EC2 instances fail due to hardware degradation, entire availability zones fail during infrastructure events, and regional endpoints degrade during large-scale AWS service disruptions. The statistical independence of zone failures forms the mathematical foundation for high availability. If a single zone has annual failure probability $p$, deploying workloads across $n$ independent zones reduces total failure probability to approximately $p^n$ for services that can tolerate $n-1$ zone failures. This exponential reduction justifies the operational complexity and cost overhead of multi-AZ architectures.

Autoscaling in Kubernetes operates through two distinct control loops with different time constants and optimization objectives. Horizontal Pod Autoscaling (HPA) adjusts the replica count of Deployments and StatefulSets based on observed CPU utilization, memory consumption, or custom metrics, responding within seconds to traffic spikes by spawning additional pods on existing nodes. Cluster Autoscaling (CA) provisions or deprovisions EC2 instances in response to pod scheduling failures or sustained resource underutilization, operating at minute-scale latency due to EC2 launch times and kubelet registration delays. These loops interact through the scheduler's resource allocation decisions: when HPA scales up but no nodes have sufficient capacity, pending pods trigger CA to launch new instances; when workload demand drops, CA drains nodes and terminates instances to reduce costs. The coupling between HPA and CA creates emergent behaviors that require careful tuning to avoid oscillations, where rapid pod scaling causes node thrashing, or deadlocks, where CA cannot find suitable instance types to satisfy pending pod resource requests.

Disaster recovery for stateful systems running on EKS requires distinguishing between ephemeral cluster state, recoverable application state, and non-reconstructible persistent data. Ephemeral state includes Kubernetes objects like Deployments, Services, and ConfigMaps, which can be reconstructed from version-controlled manifests stored in Git repositories or Helm charts. Recoverable application state includes metrics, logs, and temporary caches, which degrade gracefully during outages and rebuild automatically after recovery. Non-reconstructible persistent data—customer databases, object storage references, and cryptographic key material—must be replicated continuously across regions through backup snapshots, cross-region replication, or active-active multi-cluster architectures. The recovery time objective (RTO) and recovery point objective (RPO) determine the appropriate disaster recovery strategy: RTO measures the maximum tolerable downtime before service restoration, while RPO defines the maximum acceptable data loss measured in time. Achieving RTO under 15 minutes and RPO under 5 minutes typically requires active-active clusters with synchronous data replication, while RTO of several hours and RPO of one day can be satisfied by periodic snapshots and manual cluster reconstruction.

Blue-green deployment strategies extend the Kubernetes rolling update model by provisioning an entirely separate cluster or node group, deploying the new application version, performing validation, and atomically switching traffic through DNS updates or load balancer target group changes. This approach eliminates the gradual rollout risk inherent in rolling updates, where partial deployments run mixed versions simultaneously and may expose compatibility bugs. Blue-green deployments also enable zero-downtime rollbacks by simply reverting traffic to the previous cluster, bypassing the time required to undeploy bad pods and redeploy good ones. However, the strategy doubles infrastructure cost during the transition period and requires sophisticated traffic management to ensure database schema compatibility and distributed transaction consistency across the blue and green environments.

Cost optimization in large-scale EKS clusters requires modeling the economic tradeoffs between on-demand instances, reserved instances, and spot instances. On-demand instances provide guaranteed availability at standard pricing but lack cost efficiency for steady-state workloads. Reserved instances require upfront capacity commitments in exchange for 30-70% discounts, optimal for predictable baseline load. Spot instances offer 50-90% discounts by reclaiming unused EC2 capacity, but AWS can terminate instances with two-minute warning when capacity becomes constrained. The optimal cost structure typically combines reserved instances for the minimum sustained workload, on-demand instances for burst capacity during autoscaling events, and spot instances for fault-tolerant batch processing or stateless services that tolerate interruptions. Spot instance lifecycle management requires pod disruption budgets, graceful termination handling, and multi-instance-type node groups to diversify interruption risk across EC2 capacity pools.

Federation architectures distribute a single logical Kubernetes API across multiple independent clusters, enabling global traffic routing, regulatory data residency compliance, and blast radius reduction. Cluster federation introduces a control plane hierarchy where a federated API server aggregates resources from member clusters and distributes high-level policies while allowing each cluster to maintain local scheduling autonomy. The architectural challenge lies in managing cross-cluster service discovery, load balancing, and state synchronization. Modern federation implementations rely on multi-cluster service mesh technologies that establish encrypted tunnels between cluster networks and provide unified observability, while avoiding the tight coupling and operational complexity of earlier KubeFed projects. Large enterprises often adopt hub-and-spoke federation topologies where regional EKS clusters run tenant workloads and a central management cluster hosts cluster-scoped controllers, continuous deployment pipelines, and policy enforcement engines.

## 2. Core Architecture & Mechanics

### Multi-Availability Zone Node Topology and Pod Scheduling Constraints

Achieving genuine high availability requires distributing both worker nodes and application pods across multiple availability zones while ensuring that critical workloads survive complete zone failures. EKS node groups can span multiple subnets, each associated with a distinct availability zone within the region. When launching a managed node group, AWS automatically distributes EC2 instances across the specified subnets using balanced placement algorithms that maintain approximately equal node counts per zone. However, balanced node distribution alone does not guarantee workload resilience—pods must be explicitly scheduled with zone-awareness through topology spread constraints and pod anti-affinity rules.

Kubernetes topology spread constraints provide declarative control over how pods distribute across failure domains defined by node labels. Every EKS worker node receives the `topology.kubernetes.io/zone` label identifying its availability zone. A topology spread constraint specifies a label selector to identify the pods being spread, a topology key indicating the failure domain dimension, and a maximum skew value defining the acceptable imbalance between zones. Consider a critical API service that must maintain at least two replicas in each zone:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-api
  namespace: production
spec:
  replicas: 6
  selector:
    matchLabels:
      app: critical-api
  template:
    metadata:
      labels:
        app: critical-api
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: critical-api
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: critical-api
      containers:
      - name: api
        image: registry.example.com/critical-api:v2.1.4
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        ports:
        - containerPort: 8080
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 2
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 2
          failureThreshold: 2
```

The first topology spread constraint ensures that pod distribution across zones never exceeds a skew of one replica, enforcing near-perfect balance. Setting `whenUnsatisfiable` to `DoNotSchedule` makes this constraint hard—the scheduler will leave pods pending rather than violate zone balance, preventing scenarios where all replicas land in a single zone. The second constraint spreads pods across individual nodes with `ScheduleAnyway` as a soft preference, improving resilience against single-node failures without blocking scheduling when perfect spread cannot be achieved. This layered approach balances strict zone distribution with practical scheduling flexibility.

Pod anti-affinity rules provide an alternative mechanism for spreading workloads, particularly when combined with required versus preferred affinity weights. Required anti-affinity prevents pods from co-locating on nodes matching specific label selectors, useful for ensuring that database replicas never share physical hardware:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-ha
  namespace: database
spec:
  serviceName: postgres-ha
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: postgres
            topologyKey: kubernetes.io/hostname
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: postgres
              topologyKey: topology.kubernetes.io/zone
      containers:
      - name: postgres
        image: postgres:15.4-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 4000m
            memory: 8Gi
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: gp3-encrypted
      resources:
        requests:
          storage: 100Gi
```

The required anti-affinity rule on `kubernetes.io/hostname` guarantees that no two Postgres replicas run on the same node, protecting against individual EC2 instance failures. The preferred anti-affinity rule on zone topology biases scheduling toward different zones with a weight of 100, but allows violations when insufficient nodes exist across zones. This design acknowledges that StatefulSets with persistent volumes face additional constraints—EBS volumes are zone-locked, meaning a pod can only mount a volume in the same zone where the volume resides. Migration across zones requires volume snapshots and restoration in the target zone, a process too slow for automatic failover.

### Horizontal Pod Autoscaling with Custom Metrics

While CPU-based horizontal pod autoscaling suffices for compute-bound workloads, production systems often exhibit bottlenecks in application-specific dimensions like request queue depth, database connection pool saturation, or cache miss rates. The Kubernetes Metrics API provides a standardized interface for autoscaling based on custom metrics collected from Prometheus, Datadog, or application-native exporters. Implementing custom metric autoscaling requires deploying a metrics adapter that bridges the external metrics source to the Kubernetes API server.

The KEDA (Kubernetes Event-Driven Autoscaling) project provides a production-grade implementation supporting dozens of metric sources. After installing KEDA through Helm, defining a ScaledObject resource enables autoscaling based on metrics like AWS SQS queue depth:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: sqs-processor-scaler
  namespace: messaging
spec:
  scaleTargetRef:
    name: sqs-processor
  minReplicaCount: 2
  maxReplicaCount: 50
  pollingInterval: 15
  cooldownPeriod: 60
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-west-2.amazonaws.com/123456789012/high-priority-tasks
      queueLength: "10"
      awsRegion: us-west-2
      identityOwner: operator
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sqs-processor
  namespace: messaging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sqs-processor
  template:
    metadata:
      labels:
        app: sqs-processor
    spec:
      serviceAccountName: sqs-processor-sa
      containers:
      - name: processor
        image: registry.example.com/sqs-processor:v3.2.1
        env:
        - name: SQS_QUEUE_URL
          value: https://sqs.us-west-2.amazonaws.com/123456789012/high-priority-tasks
        - name: AWS_REGION
          value: us-west-2
        - name: MAX_MESSAGES_PER_POLL
          value: "10"
        - name: VISIBILITY_TIMEOUT
          value: "300"
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
```

KEDA queries the SQS queue depth every 15 seconds and adjusts the Deployment replica count to maintain approximately 10 messages per pod, calculated as `ceil(queueDepth / targetQueueLength)`. The cooldown period prevents rapid scaling oscillations by enforcing a minimum 60-second delay between scale-down operations. This architecture decouples message ingestion from processing capacity, enabling the system to absorb traffic spikes by queuing messages while autoscaling provisions additional processing pods. The IAM role associated with the `sqs-processor-sa` service account must include `sqs:GetQueueAttributes` permissions for KEDA's metric polling and `sqs:ReceiveMessage`, `sqs:DeleteMessage` for the processor pods.

For workloads requiring sub-second autoscaling response, the Horizontal Pod Autoscaler can consume metrics directly from Prometheus using the Prometheus Adapter. Consider an HTTP API where 99th percentile latency serves as the scaling signal:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-latency-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: latency-sensitive-api
  minReplicas: 5
  maxReplicas: 100
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_request_duration_p99_seconds
      target:
        type: AverageValue
        averageValue: "0.5"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 10
        periodSeconds: 15
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

The HPA targets a 99th percentile latency of 500 milliseconds averaged across all pods. The scaling behavior configuration fine-tunes the autoscaler's aggressiveness: scale-up policies allow doubling pod count or adding 10 pods every 15 seconds, whichever is larger, with zero stabilization window for immediate response to latency degradation. Scale-down policies restrict contraction to 10% every 60 seconds with a 5-minute stabilization window, preventing premature capacity reduction during transient load dips. This asymmetric tuning reflects the operational reality that scaling up too slowly causes user-visible latency violations, while scaling down too quickly risks cascading failures when load returns.

### Cluster Autoscaling and EC2 Auto Scaling Group Configuration

The Cluster Autoscaler adjusts worker node count by modifying EC2 Auto Scaling Group desired capacity in response to unschedulable pods or sustained low node utilization. Deploying the Cluster Autoscaler requires careful configuration to prevent conflicts with AWS Auto Scaling Group scaling policies and ensure cost-efficient instance type selection.

The following manifest installs the Cluster Autoscaler with production-grade tuning:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/EKSClusterAutoscalerRole
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-autoscaler
rules:
- apiGroups: [""]
  resources: ["events", "endpoints"]
  verbs: ["create", "patch"]
- apiGroups: [""]
  resources: ["pods/eviction"]
  verbs: ["create"]
- apiGroups: [""]
  resources: ["pods/status"]
  verbs: ["update"]
- apiGroups: [""]
  resources: ["endpoints"]
  resourceNames: ["cluster-autoscaler"]
  verbs: ["get", "update"]
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["watch", "list", "get", "update"]
- apiGroups: [""]
  resources: ["namespaces", "pods", "services", "replicationcontrollers", "persistentvolumeclaims", "persistentvolumes"]
  verbs: ["watch", "list", "get"]
- apiGroups: ["extensions"]
  resources: ["replicasets", "daemonsets"]
  verbs: ["watch", "list", "get"]
- apiGroups: ["policy"]
  resources: ["poddisruptionbudgets"]
  verbs: ["watch", "list"]
- apiGroups: ["apps"]
  resources: ["statefulsets", "replicasets", "daemonsets"]
  verbs: ["watch", "list", "get"]
- apiGroups: ["storage.k8s.io"]
  resources: ["storageclasses", "csinodes", "csidrivers", "csistoragecapacities"]
  verbs: ["watch", "list", "get"]
- apiGroups: ["batch", "extensions"]
  resources: ["jobs"]
  verbs: ["get", "list", "watch", "patch"]
- apiGroups: ["coordination.k8s.io"]
  resources: ["leases"]
  verbs: ["create"]
- apiGroups: ["coordination.k8s.io"]
  resourceNames: ["cluster-autoscaler"]
  resources: ["leases"]
  verbs: ["get", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cluster-autoscaler
  namespace: kube-system
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["create", "list", "watch"]
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["cluster-autoscaler-status", "cluster-autoscaler-priority-expander"]
  verbs: ["delete", "get", "update", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-autoscaler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-autoscaler
subjects:
- kind: ServiceAccount
  name: cluster-autoscaler
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cluster-autoscaler
  namespace: kube-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: cluster-autoscaler
subjects:
- kind: ServiceAccount
  name: cluster-autoscaler
  namespace: kube-system
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    app: cluster-autoscaler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      priorityClassName: system-cluster-critical
      nodeSelector:
        node-role.kubernetes.io/control-plane-workload: "true"
      tolerations:
      - key: CriticalAddonsOnly
        operator: Exists
      - effect: NoSchedule
        key: node-role.kubernetes.io/control-plane-workload
      containers:
      - image: registry.k8s.io/autoscaling/cluster-autoscaler:v1.28.2
        name: cluster-autoscaler
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/prod-eks-cluster
        - --balance-similar-node-groups=true
        - --skip-nodes-with-system-pods=false
        - --scale-down-enabled=true
        - --scale-down-delay-after-add=10m
        - --scale-down-unneeded-time=10m
        - --scale-down-utilization-threshold=0.5
        - --max-node-provision-time=15m
        resources:
          requests:
            cpu: 100m
            memory: 300Mi
          limits:
            cpu: 200m
            memory: 600Mi
        env:
        - name: AWS_REGION
          value: us-west-2
```

The Cluster Autoscaler discovers Auto Scaling Groups through tags rather than explicit configuration, enabling dynamic node group management. Every ASG that should participate in autoscaling must carry two tags: `k8s.io/cluster-autoscaler/enabled` with value `true` and `k8s.io/cluster-autoscaler/<cluster-name>` with the cluster identifier. The `--expander=least-waste` strategy selects the node group that minimizes unused capacity after placing pending pods, optimizing cost efficiency in multi-instance-type clusters.

The scale-down parameters control how aggressively the autoscaler removes idle nodes. Setting `--scale-down-delay-after-add=10m` prevents immediate removal of newly launched nodes, allowing time for additional pods to schedule onto fresh capacity. The utilization threshold of 0.5 marks nodes for termination when their requested CPU and memory fall below 50% of allocatable capacity, accounting for system reservations. This threshold balances cost savings against the risk of premature scale-down causing scheduling thrash when load fluctuates.

Configuring the EC2 Auto Scaling Group requires setting minimum, maximum, and desired capacity values along with mixed instance policies for cost optimization:

```bash
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name prod-eks-compute-optimized \
  --min-size 3 \
  --max-size 50 \
  --desired-capacity 6 \
  --vpc-zone-identifier subnet-abc123,subnet-def456,subnet-ghi789 \
  --mixed-instances-policy '{
    "LaunchTemplate": {
      "LaunchTemplateSpecification": {
        "LaunchTemplateId": "lt-0a1b2c3d4e5f6g7h8",
        "Version": "$Latest"
      },
      "Overrides": [
        {
          "InstanceType": "c6i.2xlarge",
          "WeightedCapacity": "8"
        },
        {
          "InstanceType": "c6i.4xlarge",
          "WeightedCapacity": "16"
        },
        {
          "InstanceType": "c6a.2xlarge",
          "WeightedCapacity": "8"
        }
      ]
    },
    "InstancesDistribution": {
      "OnDemandBaseCapacity": 2,
      "OnDemandPercentageAboveBaseCapacity": 30,
      "SpotAllocationStrategy": "capacity-optimized",
      "SpotInstancePools": 3
    }
  }' \
  --tags Key=k8s.io/cluster-autoscaler/enabled,Value=true \
         Key=k8s.io/cluster-autoscaler/prod-eks-cluster,Value=owned \
         Key=Name,Value=prod-eks-compute-node

aws autoscaling put-scaling-policy \
  --auto-scaling-group-name prod-eks-compute-optimized \
  --policy-name cluster-autoscaler-controlled \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "CustomizedMetricSpecification": {
      "MetricName": "ClusterAutoscalerControlled",
      "Namespace": "EKS/ClusterAutoscaler",
      "Statistic": "Average"
    },
    "TargetValue": 1.0,
    "DisableScaleIn": true
  }'
```

The mixed instances policy combines on-demand and spot instances to achieve cost savings without sacrificing reliability. Reserving two on-demand instances as base capacity ensures critical system pods always have guaranteed compute resources. Above the base, 30% of instances launch on-demand while 70% use spot capacity, selected through the capacity-optimized allocation strategy that chooses instance types from pools with the lowest interruption probability. Weighted capacity allows heterogeneous instance types to contribute proportionally to the total compute capacity—a c6i.4xlarge counts as two c6i.2xlarge instances when the Cluster Autoscaler calculates node group size.

The dummy Target Tracking Scaling policy prevents AWS Auto Scaling from interfering with Cluster Autoscaler decisions. By setting `DisableScaleIn: true` and using a metric that never triggers scale-in, the policy effectively disables native Auto Scaling while retaining health checks and instance replacement for failed nodes. This configuration is critical because simultaneous control by AWS Auto Scaling and Cluster Autoscaler causes oscillations, where the autoscaler adds nodes to satisfy pending pods, but AWS Auto Scaling immediately removes them based on CPU metrics that do not account for pod resource reservations.

### Persistent Volume Snapshot-Based Disaster Recovery

Stateful applications depend on persistent volumes backed by EBS or EFS storage. Disaster recovery for these workloads requires automated snapshot creation, cross-region replication, and tested restoration procedures. The CSI snapshot controller and external snapshotter sidecar enable declarative volume snapshots through Kubernetes APIs.

First, create a VolumeSnapshotClass defining the snapshot provider:

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-snapshot-class
  annotations:
    snapshot.storage.kubernetes.io/is-default-class: "true"
driver: ebs.csi.aws.com
deletionPolicy: Retain
parameters:
  tagSpecification_1: "Name=EKSVolumeSnapshot"
  tagSpecification_2: "Environment=Production"
```

The `Retain` deletion policy ensures that EBS snapshots persist even after deleting the VolumeSnapshot Kubernetes object, preventing accidental data loss during resource cleanup. Applications can trigger on-demand snapshots imperatively or schedule recurring snapshots through CronJobs:

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-backup-20250115
  namespace: database
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: postgres-storage-postgres-ha-0
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-snapshot-cron
  namespace: database
spec:
  schedule: "0 2 * * *"
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: snapshot-creator
          restartPolicy: OnFailure
          containers:
          - name: snapshot
            image: bitnami/kubectl:1.28
            command:
            - /bin/bash
            - -c
            - |
              TIMESTAMP=$(date +%Y%m%d-%H%M%S)
              cat <<EOF | kubectl apply -f -
              apiVersion: snapshot.storage.k8s.io/v1
              kind: VolumeSnapshot
              metadata:
                name: postgres-backup-${TIMESTAMP}
                namespace: database
              spec:
                volumeSnapshotClassName: ebs-snapshot-class
                source:
                  persistentVolumeClaimName: postgres-storage-postgres-ha-0
              EOF
              echo "Created snapshot postgres-backup-${TIMESTAMP}"
```

This CronJob creates daily snapshots at 2:00 AM, embedding timestamps in snapshot names to facilitate point-in-time recovery. The snapshot operation is crash-consistent for most applications, capturing the volume state at the instant AWS creates the EBS snapshot. For databases requiring transaction-consistent backups, applications must implement pre-snapshot hooks that flush write-ahead logs and acquire read locks before snapshotting.

Restoring from snapshots in the same cluster and availability zone requires creating a PVC that references the snapshot:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-storage-restored
  namespace: database
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: gp3-encrypted
  dataSource:
    name: postgres-backup-20250115
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  resources:
    requests:
      storage: 100Gi
```

The CSI provisioner detects the `dataSource` field and creates a new EBS volume by restoring from the specified snapshot. This restored volume can then be mounted by a pod, typically a temporary debugging pod or a StatefulSet replica during disaster recovery. Cross-region disaster recovery requires copying EBS snapshots to a secondary region through AWS APIs, then creating a new cluster in that region and restoring volumes from the replicated snapshots. This process cannot be fully automated through Kubernetes APIs alone—operator scripts must invoke AWS CLI or SDKs to copy snapshots and provision the remote cluster.

### Multi-Cluster Service Mesh and Cross-Cluster Traffic Management

Operating multiple EKS clusters across regions or availability zones for redundancy requires solving cross-cluster service discovery and traffic routing. Traditional Kubernetes Services operate within cluster boundaries—DNS names resolve only to endpoints in the local cluster, and kube-proxy load balancing cannot distribute traffic to pods in remote clusters. Multi-cluster service meshes extend the data plane across cluster boundaries by establishing encrypted tunnels and federating service identity.

Istio multi-cluster architectures provide several topology options. The simplest production pattern uses separate control planes per cluster with cross-network connectivity, where each cluster maintains its own Istio control plane but shares service discovery through a common root certificate authority and synchronized service registries. Installing Istio in multi-cluster mode requires generating a shared root CA and configuring remote secrets for cross-cluster API access:

```bash
# Generate root CA for multi-cluster federation
mkdir -p certs
cd certs
make -f ../tools/certs/Makefile.selfsigned.mk root-ca

# Install Istio in primary cluster (us-west-2)
kubectl config use-context prod-eks-us-west-2
istioctl install --set profile=production \
  --set values.global.meshID=prod-mesh \
  --set values.global.multiCluster.clusterName=us-west-2 \
  --set values.global.network=us-west-2-network \
  --set values.pilot.env.EXTERNAL_ISTIOD=false

# Install Istio in secondary cluster (us-east-1)
kubectl config use-context prod-eks-us-east-1
istioctl install --set profile=production \
  --set values.global.meshID=prod-mesh \
  --set values.global.multiCluster.clusterName=us-east-1 \
  --set values.global.network=us-east-1-network \
  --set values.pilot.env.EXTERNAL_ISTIOD=false

# Create remote secrets for cross-cluster discovery
istioctl create-remote-secret --context=prod-eks-us-west-2 --name=us-west-2 | \
  kubectl apply -f - --context=prod-eks-us-east-1

istioctl create-remote-secret --context=prod-eks-us-east-1 --name=us-east-1 | \
  kubectl apply -f - --context=prod-eks-us-west-2
```

Remote secrets contain kubeconfig credentials that allow each cluster's Istio control plane to watch services and endpoints in the remote cluster. This bidirectional connectivity enables automatic service discovery—when a service is created in the us-west-2 cluster, pods in us-east-1 can resolve its DNS name and route traffic through the Istio sidecar proxies. The mesh data plane establishes encrypted mTLS tunnels between clusters, routing traffic through Istio ingress gateways that terminate at the network boundary.

For applications requiring explicit control over multi-cluster routing, ServiceEntry resources define external endpoints:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: api-us-east-1
  namespace: production
spec:
  hosts:
  - api.production.svc.cluster.local
  location: MESH_INTERNAL
  ports:
  - number: 80
    name: http
    protocol: HTTP
  resolution: DNS
  endpoints:
  - address: api-gateway.us-east-1.example.com
    locality: us-east-1/us-east-1a
    labels:
      region: us-east-1
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api-cross-region-lb
  namespace: production
spec:
  host: api.production.svc.cluster.local
  trafficPolicy:
    loadBalancer:
      localityLbSetting:
        enabled: true
        failover:
        - from: us-west-2
          to: us-east-1
    outlierDetection:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 60s
      maxEjectionPercent: 50
```

The DestinationRule configures locality-aware load balancing with automatic failover. Under normal conditions, requests from pods in us-west-2 route to local endpoints, minimizing cross-region latency and data transfer costs. When outlier detection identifies unhealthy endpoints—defined as three consecutive errors within 30 seconds—traffic fails over to the us-east-1 region. Ejected endpoints remain out of rotation for 60 seconds before reintegration, preventing cascading failures when transient errors affect entire clusters.

### Blue-Green Cluster Deployments and Traffic Cutover

Blue-green deployment at the cluster level provisions an entirely separate EKS cluster running the new application version, performs validation, then atomically redirects traffic from the old cluster to the new cluster. This strategy provides the fastest rollback mechanism and eliminates the complexity of managing mixed-version deployments, but requires doubling infrastructure cost during the transition period.

The operational workflow for blue-green cluster deployments begins with provisioning the green cluster through infrastructure-as-code:

```hcl
resource "aws_eks_cluster" "green" {
  name     = "prod-eks-cluster-green"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids              = aws_subnet.private[*].id
    endpoint_private_access = true
    endpoint_public_access  = false
    security_group_ids      = [aws_security_group.eks_cluster_sg.id]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]
}

resource "aws_eks_node_group" "green_compute" {
  cluster_name    = aws_eks_cluster.green.name
  node_group_name = "compute-optimized-green"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = aws_subnet.private[*].id
  version         = "1.28"

  scaling_config {
    desired_size = 6
    max_size     = 50
    min_size     = 3
  }

  instance_types = ["c6i.2xlarge", "c6i.4xlarge"]

  launch_template {
    id      = aws_launch_template.eks_node_template.id
    version = "$Latest"
  }

  labels = {
    environment = "production"
    deployment  = "green"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry,
  ]
}
```

After provisioning the green cluster, deploy all application workloads using identical manifests and configuration as the blue cluster, but without routing production traffic. Validation includes synthetic transaction tests, load testing with production-scale traffic replay, and database migration dry runs. Once validation confirms the green cluster meets production readiness criteria, traffic cutover occurs through DNS updates or load balancer target group modifications.

For Route53-based traffic management, create weighted routing policies that gradually shift traffic:

```bash
# Initial state: 100% traffic to blue cluster
aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "blue-cluster",
      "Weight": 100,
      "AliasTarget": {
        "HostedZoneId": "Z215JYRZR1TBD5",
        "DNSName": "blue-alb-1234567890.us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }, {
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "green-cluster",
      "Weight": 0,
      "AliasTarget": {
        "HostedZoneId": "Z215JYRZR1TBD5",
        "DNSName": "green-alb-0987654321.us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'

# Canary: 10% traffic to green cluster
aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "blue-cluster",
      "Weight": 90,
      "AliasTarget": {
        "HostedZoneId": "Z215JYRZR1TBD5",
        "DNSName": "blue-alb-1234567890.us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }, {
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "green-cluster",
      "Weight": 10,
      "AliasTarget": {
        "HostedZoneId": "Z215JYRZR1TBD5",
        "DNSName": "green-alb-0987654321.us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'

# Full cutover: 100% traffic to green cluster
aws route53 change-resource-record-sets --hosted-zone-id Z1234567890ABC --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "blue-cluster",
      "Weight": 0,
      "AliasTarget": {
        "HostedZoneId": "Z215JYRZR1TBD5",
        "DNSName": "blue-alb-1234567890.us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }, {
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "api.example.com",
      "Type": "A",
      "SetIdentifier": "green-cluster",
      "Weight": 100,
      "AliasTarget": {
        "HostedZoneId": "Z215JYRZR1TBD5",
        "DNSName": "green-alb-0987654321.us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'
```

Weighted routing policies distribute traffic proportionally between clusters, enabling gradual canary rollouts. DNS TTLs introduce latency in traffic shifting—clients cache DNS responses for the TTL duration, meaning a 60-second TTL results in traffic gradually migrating over several minutes rather than instantaneously. For near-instantaneous cutover, configure Application Load Balancer target groups and modify listener rules:

```bash
# Register green cluster nodes in standby target group
GREEN_NODE_IPS=$(kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}' --context prod-eks-green)
for ip in $GREEN_NODE_IPS; do
  aws elbv2 register-targets --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/prod-api-green/abc123 \
    --targets Id=$ip,Port=30080
done

# Wait for target health checks to pass
aws elbv2 wait target-in-service --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/prod-api-green/abc123

# Modify listener to route to green target group
aws elbv2 modify-listener --listener-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:listener/app/prod-api-alb/def456/ghi789 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/prod-api-green/abc123
```

This approach routes 100% of traffic to the green cluster within seconds, limited only by ALB listener rule propagation delay. If post-cutover monitoring reveals regressions, reverting the listener modification immediately restores traffic to the blue cluster. After confirming the green cluster operates correctly under production load for the defined soak period (typically 24-72 hours), decommission the blue cluster to eliminate duplicate infrastructure costs.

## 3. High-Performance Optimization & Failure Modes

### Cluster Autoscaler Optimization and Pod Bin-Packing

The Cluster Autoscaler's effectiveness depends critically on efficient pod bin-packing—the scheduler's ability to pack pods densely onto nodes to minimize wasted capacity. Poor bin-packing manifests as excessive fragmentation, where nodes run at low utilization because remaining capacity cannot accommodate pending pods due to mismatched resource requests. The scheduler's default algorithm prioritizes spreading pods across nodes for fault tolerance, but this conflicts with cost optimization objectives in autoscaling clusters.

Tuning scheduler priority functions improves bin-packing by biasing placement toward nodes with higher utilization. Create a custom scheduler configuration enabling the `NodeResourcesFit` plugin with `MostAllocated` scoring:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scheduler-config
  namespace: kube-system
data:
  scheduler-config.yaml: |
    apiVersion: kubescheduler.config.k8s.io/v1
    kind: KubeSchedulerConfiguration
    leaderElection:
      leaderElect: true
    profiles:
    - schedulerName: bin-packing-scheduler
      plugins:
        score:
          enabled:
          - name: NodeResourcesFit
            weight: 10
          - name: ImageLocality
            weight: 1
          disabled:
          - name: NodeResourcesBalancedAllocation
      pluginConfig:
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
            resources:
            - name: cpu
              weight: 1
            - name: memory
              weight: 1
```

Deploying a secondary scheduler with this configuration allows workloads to opt into bin-packing behavior by setting `schedulerName: bin-packing-scheduler` in pod specs. The `MostAllocated` strategy assigns higher scores to nodes with greater resource utilization, concentrating pods onto fewer nodes and leaving others empty for the Cluster Autoscaler to remove. The tradeoff is reduced blast radius for node failures—when a densely packed node fails, more pods experience simultaneous disruption. Production systems balance bin-packing efficiency with resilience by applying the custom scheduler only to stateless, easily replaceable workloads while using the default scheduler for critical services.

Pod priority and preemption provide another mechanism for optimizing cluster utilization. High-priority pods can evict lower-priority pods when resource contention prevents scheduling, enabling critical workloads to seize capacity from batch jobs or background tasks:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: production-critical
value: 1000000
globalDefault: false
description: "Reserved for customer-facing production services"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: batch-processing
value: 100
globalDefault: false
preemptionPolicy: Never
description: "Batch jobs that should never preempt other workloads"
---
apiVersion: batch/v1
kind: Job
metadata:
  name: data-processing
  namespace: analytics
spec:
  parallelism: 20
  completions: 100
  template:
    spec:
      priorityClassName: batch-processing
      restartPolicy: OnFailure
      containers:
      - name: processor
        image: registry.example.com/data-processor:v1.2.3
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 4Gi
```

Batch jobs assigned low-priority classes act as elastic capacity consumers—they utilize available nodes during off-peak periods but yield capacity when production traffic spikes, avoiding the need to overprovision for peak load. Setting `preemptionPolicy: Never` prevents batch jobs from evicting each other, ensuring that only higher-priority pods can trigger preemption.

The Cluster Autoscaler's `--expander` flag controls which node group scales when multiple groups can satisfy pending pods. The default `random` expander provides no optimization, while `least-waste` minimizes unused capacity by selecting the node group where pod resource requests most closely match instance capacity. For complex multi-tier applications, the `priority` expander enables explicit control:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |
    10:
      - .*-spot-.*
    50:
      - .*-compute-optimized-.*
    100:
      - .*-memory-optimized-.*
```

This priority configuration prefers spot instance node groups (priority 10) for maximum cost savings, falls back to compute-optimized instances (priority 50) when spot capacity is unavailable, and uses expensive memory-optimized instances (priority 100) only as a last resort. The priorities apply during scale-up events when the Cluster Autoscaler must choose between multiple node groups capable of running pending pods.

### Spot Instance Integration and Graceful Termination

Spot instances reduce compute costs by 50-90% compared to on-demand pricing, but AWS can reclaim them with two-minute warning when capacity becomes constrained. Integrating spot instances into production EKS clusters requires handling termination notices gracefully to minimize service disruption. The AWS Node Termination Handler runs as a DaemonSet, monitoring EC2 metadata endpoints and CloudWatch Events for termination signals, then cordoning and draining affected nodes before shutdown.

Install the termination handler with configuration for spot and scheduled maintenance handling:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: aws-node-termination-handler
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: aws-node-termination-handler
  updateStrategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: aws-node-termination-handler
    spec:
      serviceAccountName: aws-node-termination-handler
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      priorityClassName: system-node-critical
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: eks.amazonaws.com/capacityType
                operator: In
                values:
                - SPOT
      tolerations:
      - operator: Exists
      containers:
      - name: aws-node-termination-handler
        image: public.ecr.aws/aws-ec2/aws-node-termination-handler:v1.21.0
        env:
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: ENABLE_SPOT_INTERRUPTION_DRAINING
          value: "true"
        - name: ENABLE_SCHEDULED_EVENT_DRAINING
          value: "true"
        - name: ENABLE_REBALANCE_MONITORING
          value: "true"
        - name: ENABLE_REBALANCE_DRAINING
          value: "false"
        - name: DELETE_LOCAL_DATA
          value: "true"
        - name: IGNORE_DAEMON_SETS
          value: "true"
        - name: POD_TERMINATION_GRACE_PERIOD
          value: "90"
        - name: NODE_TERMINATION_GRACE_PERIOD
          value: "120"
        - name: EMIT_KUBERNETES_EVENTS
          value: "true"
        - name: ENABLE_PROMETHEUS_SERVER
          value: "true"
        - name: PROMETHEUS_SERVER_PORT
          value: "9092"
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 100m
            memory: 128Mi
```

The termination handler polls the EC2 instance metadata endpoint every second for spot interruption notices. Upon detecting a termination warning, the handler cordons the node to prevent new pod scheduling, then drains all pods with a 90-second grace period. Critical pods define `terminationGracePeriodSeconds` in their spec to extend the default 30-second shutdown window, allowing time for connection draining and graceful state persistence:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stateful-api
  namespace: production
spec:
  replicas: 10
  selector:
    matchLabels:
      app: stateful-api
  template:
    metadata:
      labels:
        app: stateful-api
    spec:
      terminationGracePeriodSeconds: 90
      containers:
      - name: api
        image: registry.example.com/stateful-api:v1.3.2
        lifecycle:
          preStop:
            exec:
              command:
              - /bin/sh
              - -c
              - |
                # Signal application to stop accepting new requests
                kill -TERM 1
                # Wait for in-flight requests to complete
                sleep 30
                # Flush pending writes to database
                curl -X POST http://localhost:8080/admin/flush
                # Allow remaining grace period for final cleanup
                sleep 20
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
```

The `preStop` hook executes before Kubernetes sends the TERM signal to the main container process. This hook implements graceful shutdown by stopping request acceptance, waiting for active transactions to complete, and flushing cached data to persistent storage. The 90-second termination grace period must exceed the total preStop execution time plus application shutdown duration to prevent forceful SIGKILL termination of pods with incomplete cleanup.

Spot instance diversity across multiple instance types and availability zones reduces interruption correlation—when AWS reclaims capacity in one pool, other pools remain available. The Auto Scaling Group mixed instances policy configured earlier achieves this diversity by specifying multiple instance types and using the capacity-optimized allocation strategy. Monitoring spot interruption rates and dynamically adjusting on-demand versus spot ratios provides additional resilience:

```python
import boto3
import datetime

cloudwatch = boto3.client('cloudwatch', region_name='us-west-2')
autoscaling = boto3.client('autoscaling', region_name='us-west-2')

# Query spot interruption rate over past hour
response = cloudwatch.get_metric_statistics(
    Namespace='AWS/EC2Spot',
    MetricName='SpotInstanceInterruptions',
    Dimensions=[
        {'Name': 'InstanceType', 'Value': 'c6i.2xlarge'}
    ],
    StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
    EndTime=datetime.datetime.utcnow(),
    Period=3600,
    Statistics=['Sum']
)

interruptions = response['Datapoints'][0]['Sum'] if response['Datapoints'] else 0

# Increase on-demand percentage if interruptions exceed threshold
if interruptions > 5:
    autoscaling.update_auto_scaling_group(
        AutoScalingGroupName='prod-eks-compute-optimized',
        MixedInstancesPolicy={
            'InstancesDistribution': {
                'OnDemandBaseCapacity': 2,
                'OnDemandPercentageAboveBaseCapacity': 50,  # Increased from 30
                'SpotAllocationStrategy': 'capacity-optimized'
            }
        }
    )
    print(f"Increased on-demand percentage due to {interruptions} spot interruptions")
```

This adaptive policy monitors spot interruption CloudWatch metrics and temporarily increases on-demand instance usage during periods of high spot volatility, trading cost efficiency for reliability. The policy automatically reverts to higher spot utilization once interruption rates normalize.

### Handling etcd Performance Limits and Control Plane Scaling

While AWS manages the EKS control plane and scales etcd capacity automatically, the distributed consensus algorithm imposes fundamental performance limits that manifest as API server latency degradation when cluster object count or write throughput exceeds thresholds. Each etcd write requires acknowledgment from a quorum of replicas before committing, introducing latency proportional to inter-AZ network round-trip time plus disk fsync overhead. At scale, these limits require reducing API server write load through client-side caching, informer resync tuning, and minimizing object churn.

Kubernetes clients should leverage SharedInformer caches rather than repeatedly listing objects from the API server. Informers maintain local caches synchronized through watch streams, reducing API server load from $O(n \cdot m)$ list operations (where $n$ is client count and $m$ is sync frequency) to $O(n)$ watch connections with incremental updates. However, excessive informer count from poorly designed operators causes watch connection exhaustion. Audit watch connections using:

```bash
kubectl get --raw /metrics | grep apiserver_watch_events_total

# Example output showing watch event rates by resource type
apiserver_watch_events_total{group="",version="v1",kind="Pod"} 847293
apiserver_watch_events_total{group="apps",version="v1",kind="Deployment"} 12847
apiserver_watch_events_total{group="",version="v1",kind="Service"} 8934
```

High watch event rates indicate object churn triggering excessive cache invalidations. Controllers creating and deleting temporary objects at high frequency should batch operations and use OwnerReferences for garbage collection rather than explicit deletion to reduce API server write load.

Node heartbeats represent another significant etcd write source, as the kubelet updates Node status every 10 seconds by default. At 1000 nodes, this generates 100 QPS of sustained writes. Increasing the `--node-status-update-frequency` parameter on kubelets reduces write load at the cost of slower failure detection:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubelet-config
  namespace: kube-system
data:
  kubelet-config.json: |
    {
      "kind": "KubeletConfiguration",
      "apiVersion": "kubelet.config.k8s.io/v1beta1",
      "nodeStatusUpdateFrequency": "30s",
      "nodeStatusReportFrequency": "5m",
      "evictionHard": {
        "memory.available": "200Mi",
        "nodefs.available": "10%"
      }
    }
```

Setting update frequency to 30 seconds reduces etcd write QPS by 66% while increasing node failure detection latency from 40 seconds to 90 seconds (accounting for kube-controller-manager's `--node-monitor-grace-period`). The tradeoff is acceptable for most workloads since pod eviction and rescheduling already require 60+ seconds for graceful termination and startup.

API priority and fairness (APF) configuration protects the control plane from overload by queuing and rate-limiting requests based on client identity and request attributes. The default APF configuration allocates priority levels for system components, built-in controllers, and general user requests. Custom FlowSchemas and PriorityLevelConfigurations enable fine-grained control:

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: FlowSchema
metadata:
  name: batch-job-scheduler
spec:
  distinguisherMethod:
    type: ByUser
  matchingPrecedence: 500
  priorityLevelConfiguration:
    name: batch-job-priority
  rules:
  - resourceRules:
    - apiGroups: ["batch"]
      resources: ["jobs"]
      verbs: ["*"]
    subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: batch-scheduler
        namespace: analytics
---
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: PriorityLevelConfiguration
metadata:
  name: batch-job-priority
spec:
  type: Limited
  limited:
    assuredConcurrencyShares: 10
    limitResponse:
      type: Queue
      queuing:
        queues: 8
        queueLengthLimit: 50
        handSize: 4
```

This configuration assigns batch job creation requests from the `batch-scheduler` service account to a dedicated priority level with limited concurrency. The `assuredConcurrencyShares` parameter allocates a proportional share of total API server capacity, while the queuing configuration buffers excess requests during bursts. Monitoring APF metrics reveals when clients encounter rate limiting:

```bash
kubectl get --raw /metrics | grep apiserver_flowcontrol

# Key metrics indicating request queuing or rejection
apiserver_flowcontrol_current_executing_requests{priority_level="batch-job-priority"} 8
apiserver_flowcontrol_request_wait_duration_seconds_bucket{priority_level="batch-job-priority"} 234
apiserver_flowcontrol_rejected_requests_total{priority_level="batch-job-priority"} 12
```

Persistent high wait durations or rejected request counts indicate that either the priority level needs increased concurrency shares or the client must reduce request rate.

### Cross-Region Disaster Recovery Architecture and Failover Automation

Comprehensive disaster recovery requires replicating both cluster infrastructure and application state across independent AWS regions. The recovery strategy depends on RTO and RPO requirements. For RTO under 15 minutes, operate active-active clusters in multiple regions with continuous data replication and automated traffic failover. For RTO of several hours, maintain warm standby clusters with recent snapshots and manual activation procedures.

An active-active multi-region architecture deploys identical EKS clusters in two regions, both serving production traffic through global load balancing:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Global Accelerator                       │
│              (Anycast IPs: 1.2.3.4, 5.6.7.8)                   │
└────────────────┬─────────────────────┬──────────────────────────┘
                 │                     │
                 │                     │
    ┌────────────▼──────────┐    ┌────▼────────────────────┐
    │   us-west-2 Region    │    │   us-east-1 Region     │
    │  ┌──────────────────┐ │    │  ┌──────────────────┐  │
    │  │  EKS Cluster     │ │    │  │  EKS Cluster     │  │
    │  │  Control Plane   │ │    │  │  Control Plane   │  │
    │  └──────────────────┘ │    │  └──────────────────┘  │
    │  ┌──────────────────┐ │    │  ┌──────────────────┐  │
    │  │  Worker Nodes    │ │    │  │  Worker Nodes    │  │
    │  │  (us-west-2a/b/c)│ │    │  │  (us-east-1a/b/c)│  │
    │  └──────────────────┘ │    │  └──────────────────┘  │
    │  ┌──────────────────┐ │    │  ┌──────────────────┐  │
    │  │  RDS Primary     │◄├────┤──┤  RDS Replica     │  │
    │  │  (Multi-AZ)      │ │ Async│  │  (Read Replica) │  │
    │  └──────────────────┘ │ Repl │  └──────────────────┘  │
    │  ┌──────────────────┐ │    │  ┌──────────────────┐  │
    │  │  S3 Bucket       │◄├────┤──┤  S3 Bucket       │  │
    │  │  (Versioned)     │ │ CRR │  │  (Replica)       │  │
    │  └──────────────────┘ │    │  └──────────────────┘  │
    └───────────────────────┘    └─────────────────────────┘
```

AWS Global Accelerator provides static Anycast IP addresses that route traffic to the nearest healthy regional endpoint based on BGP route advertisement. Health checks monitor each region's Application Load Balancer and automatically withdraw routes from failed regions, achieving sub-minute failover without DNS propagation delays. Configuring Global Accelerator requires:

```bash
# Create accelerator
ACCELERATOR_ARN=$(aws globalaccelerator create-accelerator \
  --name prod-api-accelerator \
  --ip-address-type IPV4 \
  --enabled \
  --query 'Accelerator.AcceleratorArn' \
  --output text)

# Create listener
LISTENER_ARN=$(aws globalaccelerator create-listener \
  --accelerator-arn $ACCELERATOR_ARN \
  --port-ranges FromPort=443,ToPort=443 \
  --protocol TCP \
  --query 'Listener.ListenerArn' \
  --output text)

# Create endpoint group for us-west-2
aws globalaccelerator create-endpoint-group \
  --listener-arn $LISTENER_ARN \
  --endpoint-group-region us-west-2 \
  --traffic-dial-percentage 50 \
  --health-check-interval-seconds 30 \
  --health-check-path /health \
  --threshold-count 3 \
  --endpoint-configurations \
    EndpointId=arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/prod-api-alb/abc123,Weight=100

# Create endpoint group for us-east-1
aws globalaccelerator create-endpoint-group \
  --listener-arn $LISTENER_ARN \
  --endpoint-group-region us-east-1 \
  --traffic-dial-percentage 50 \
  --health-check-interval-seconds 30 \
  --health-check-path /health \
  --threshold-count 3 \
  --endpoint-configurations \
    EndpointId=arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/prod-api-alb/def456,Weight=100
```

The `traffic-dial-percentage` controls the proportion of traffic routed to each region under normal conditions, enabling active-active 50/50 split or active-passive 100/0 configurations. Health checks probe the ALB endpoint every 30 seconds; after three consecutive failures, Global Accelerator removes the unhealthy region from routing tables and redistributes traffic to remaining healthy endpoints.

Database replication across regions requires careful consideration of consistency models and failover procedures. Amazon RDS supports cross-region read replicas with asynchronous replication, introducing replication lag typically under one second but potentially extending to minutes during high write throughput or network disruptions. Applications must tolerate eventual consistency when reading from replicas or implement read-after-write consistency by directing reads to the primary database after write operations.

Promoting a read replica to primary during failover requires manual intervention:

```bash
# Promote us-east-1 replica to standalone primary
aws rds promote-read-replica \
  --db-instance-identifier prod-db-us-east-1-replica \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00"

# Wait for promotion to complete
aws rds wait db-instance-available \
  --db-instance-identifier prod-db-us-east-1-replica

# Update application ConfigMap to point to new primary endpoint
kubectl patch configmap database-config -n production --type merge -p '{
  "data": {
    "DB_HOST": "prod-db-us-east-1-replica.c9akciq32.us-east-1.rds.amazonaws.com"
  }
}'

# Restart application pods to pickup new database endpoint
kubectl rollout restart deployment/api -n production
```

This procedure promotes the replica, breaking replication link to the original primary and enabling writes to the new primary. The RPO equals the replication lag at the time of failover—typically seconds of data loss for planned failovers, potentially minutes for unplanned regional outages. After restoring service in the original region, reverse replication by creating a new read replica from the promoted instance and repeating the promotion process during the next failover exercise.

For object storage, S3 Cross-Region Replication (CRR) provides automated asynchronous replication of objects between buckets:

```json
{
  "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
  "Rules": [
    {
      "Status": "Enabled",
      "Priority": 1,
      "Filter": {
        "Prefix": ""
      },
      "Destination": {
        "Bucket": "arn:aws:s3:::prod-data-us-east-1-replica",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {
            "Minutes": 15
          }
        },
        "Metrics": {
          "Status": "Enabled",
          "EventThreshold": {
            "Minutes": 15
          }
        }
      },
      "DeleteMarkerReplication": {
        "Status": "Enabled"
      }
    }
  ]
}
```

Enabling S3 Replication Time Control (RTC) guarantees 99.99% of objects replicate within 15 minutes, with metrics tracking replication lag per object. Applications reading from replica buckets must handle temporary inconsistency during the replication window. S3 bucket versioning prevents accidental data loss by retaining all object versions, enabling point-in-time recovery by restoring specific versions after unintended deletions or corruptions.

### Cost Optimization Through Reserved Instances and Savings Plans

Sustained EKS workloads benefit dramatically from EC2 Reserved Instances or Savings Plans, which offer 30-72% discounts in exchange for capacity commitments. The optimal strategy depends on workload stability and growth projections. Reserved Instances require committing to specific instance families, regions, and tenancy for one or three years. Savings Plans provide more flexibility by committing to a dollar amount of compute usage regardless of instance type, allowing dynamic adjustment as workload patterns evolve.

Analyzing historical cluster resource utilization reveals baseline capacity suitable for Reserved Instance purchases:

```bash
# Query Prometheus for 90-day CPU usage across all nodes
curl -G 'http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query' \
  --data-urlencode 'query=quantile_over_time(0.10, sum(rate(node_cpu_seconds_total{mode!="idle"}[5m]))[90d:1h])' \
  | jq '.data.result[0].value[1]'

# Output: "28.4" (CPU cores representing 10th percentile usage)
```

The 10th percentile usage represents the sustained baseline load that rarely drops below this level, suitable for covering with Reserved Instances or Savings Plans. If the analysis shows 28.4 cores sustained over 90 days, purchasing Reserved Instances covering 28 cores provides optimal savings. The remaining capacity above baseline should use on-demand or spot instances to handle variable load without overcommitting fixed costs.

Compute Savings Plans offer superior flexibility for dynamic EKS clusters. Rather than committing to specific instance types, Savings Plans commit to a dollar amount per hour, automatically applying discounts to any EC2 usage up to the commitment amount:

```bash
# Calculate recommended Savings Plan commitment
aws ce get-savings-plans-purchase-recommendation \
  --savings-plans-type COMPUTE_SP \
  --term-in-years ONE_YEAR \
  --payment-option NO_UPFRONT \
  --lookback-period-in-days 60 \
  --query 'SavingsPlansPurchaseRecommendation.SavingsPlansPurchaseRecommendationDetails[0]'
```

This command analyzes 60 days of usage and recommends an hourly commitment that maximizes savings while minimizing over-commitment risk. The recommendation output includes estimated savings percentage, upfront costs for different payment options, and monthly commitment amounts. Compute Savings Plans apply across instance families (c6i, m6i, r6i, etc.), operating systems, and tenancy, providing optimal flexibility for clusters that adjust instance types as autoscaling requirements evolve.

Graviton-based ARM instances (c7g, m7g, r7g families) offer additional 20-40% savings over x86 equivalents while providing comparable or superior performance for many workloads. Migrating to Graviton requires recompiling applications for ARM64 architecture and validating that all dependencies support ARM. For containerized workloads, building multi-architecture images enables seamless deployment across x86 and ARM nodes:

```dockerfile
# Multi-architecture Dockerfile using buildx
FROM --platform=$BUILDPLATFORM golang:1.21-alpine AS builder
ARG TARGETOS TARGETARCH
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o /api-server ./cmd/api

FROM --platform=$TARGETPLATFORM alpine:3.19
RUN apk add --no-cache ca-certificates
COPY --from=builder /api-server /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/api-server"]
```

Building and pushing multi-arch images:

```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t registry.example.com/api-server:v1.2.3 --push .
```

Kubernetes automatically schedules pods to nodes matching the image architecture, enabling heterogeneous clusters mixing x86 and Graviton nodes. Spot instance integration with Graviton instances amplifies savings, achieving 70-85% cost reduction compared to x86 on-demand instances while maintaining production reliability through diversified spot pools.

The compounding effect of multiple optimization strategies—Savings Plans covering baseline capacity, spot instances for variable load, Graviton instances where supported, and aggressive cluster autoscaling—regularly achieves 60-80% cost reduction compared to naive all-on-demand x86 deployments. However, the operational complexity of managing mixed instance types, handling spot interruptions, and validating ARM compatibility requires investment in automation and monitoring infrastructure. Production-grade cost optimization demands treating infrastructure cost as a first-class operational metric, continuously monitored and optimized through automated policies and regular architecture reviews.
