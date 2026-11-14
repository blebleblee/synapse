# Lesson 3: Node Groups, Compute Orchestration, and Instance Management

## 1. First-Principles Intuition & Invariants

Amazon Elastic Kubernetes Service abstracts the Kubernetes control plane into a managed, highly available service distributed across multiple AWS Availability Zones, but the compute layer—the worker nodes that execute containerized workloads—remains firmly in the operator's domain of responsibility. Understanding node groups, their lifecycle, and their orchestration mechanics is the foundation of production EKS cluster operation. A node group represents a fleet of EC2 instances running the kubelet agent, container runtime, and necessary CNI plugins, bound together by shared configuration and scaling policy. The conceptual separation between control plane and data plane is not merely organizational: it reflects a fundamental division of state management, where the API server maintains desired cluster state in etcd, while worker nodes reconcile that state into running processes, mounted volumes, and active network sockets.

EKS offers two primary node group paradigms: managed node groups, which delegate EC2 instance provisioning, Auto Scaling Group orchestration, and lifecycle event handling to AWS automation, and self-managed node groups, which place the operator in direct control of instance launch templates, security group rules, IAM instance profiles, and kubelet bootstrap procedures. The distinction is not merely one of convenience but of control surface and operational contract. Managed node groups guarantee automated AMI updates, graceful node draining during termination, and automatic registration with the cluster API server, but they impose constraints on instance metadata, bootstrap script customization, and tag propagation. Self-managed node groups demand rigorous attention to IAM role trust policies, user data script correctness, and `aws-auth` ConfigMap synchronization, but they permit fine-grained control over instance placement, block device mappings, and pre-flight initialization logic.

The compute orchestration layer in EKS revolves around the interplay of three subsystems: the EC2 Auto Scaling Group, which maintains a target instance count and responds to scaling events; the Kubernetes cluster autoscaler, which observes pod scheduling failures due to insufficient resources and adjusts the desired ASG capacity; and the kubelet, which registers the node with the API server, establishes a watch stream for assigned pods, and invokes the container runtime to instantiate workloads. These three components operate asynchronously and independently, yet must converge to a consistent state where cluster capacity matches workload demand without excessive waste or latency. The invariant that governs this convergence is the capacity equation: total allocatable CPU and memory across all nodes must exceed the sum of pod resource requests, plus reserve capacity for daemon sets, system services, and kubelet overhead. Violating this invariant results in pending pods, evicted workloads, or cascading node pressure conditions.

Spot instances introduce a probabilistic dimension to capacity planning. AWS offers spare EC2 capacity at discounts reaching seventy percent relative to on-demand pricing, but the exchange is interruptibility: AWS may reclaim spot instances with a two-minute interruption notice when market demand rises. The operational challenge is not whether spot instances will be interrupted—they will—but whether the cluster can absorb terminations gracefully without violating workload availability guarantees. The solution lies in architectural redundancy and workload topology: stateless services distributed across multiple node groups, pod disruption budgets that constrain voluntary evictions, and node affinity rules that spread replicas across instance types and Availability Zones. The mathematical invariant is straightforward: for a service requiring N replicas to meet availability SLAs, the cluster must maintain at least N healthy instances capable of scheduling those pods, even after losing any single node group or spot capacity pool.

Node lifecycle events—launch, ready, update, drain, terminate—are state transitions governed by finite state machines in both the EC2 Auto Scaling service and the Kubernetes node controller. When an instance launches, the kubelet executes a bootstrap sequence: retrieves cluster CA certificate and API server endpoint from user data or instance metadata, authenticates using the node IAM role via the AWS IAM Authenticator, registers the node object with initial capacity and labels, and begins reconciling assigned pods. The node transitions from NotReady to Ready once the CNI plugin configures the pod network, kubelet health checks pass, and the container runtime reports operational status. During updates, managed node groups orchestrate a rolling replacement: new instances launch with updated AMI versions, register as Ready, receive workload scheduling via normal Kubernetes mechanisms, while old instances are cordoned, drained, and terminated. The drain operation respects pod disruption budgets, gracefully shuts down containers via SIGTERM signals, and waits for terminating pods to exit before proceeding. The invariant is zero unschedulable pods during updates, achieved through surge capacity: temporarily exceeding the target node count to ensure replacement capacity is available before decommissioning old nodes.

Container runtime selection historically centered on Docker, but the Kubernetes community deprecated the dockershim component in favor of the Container Runtime Interface specification, which decouples kubelet from specific runtime implementations. EKS supports containerd as the default runtime, a lightweight daemon that implements CRI directly without the overhead of Docker's layered architecture. The choice of runtime affects performance, security posture, and operational tooling: containerd offers lower memory overhead, faster pod startup latency, and tighter integration with Kubernetes resource accounting, while Docker provided familiar debugging commands like `docker exec` and `docker logs`. In production EKS clusters, containerd is the standard, and operators interact with containers via `crictl`, the CRI-compatible CLI tool that queries container status, retrieves logs, and inspects image layers. The runtime invariant is isolation: each container executes in a dedicated Linux namespace hierarchy (mount, PID, network, IPC, UTS, cgroup) with resource limits enforced by cgroup v2 controllers, ensuring that a single misbehaving workload cannot exhaust node-level CPU, memory, or file descriptor pools.

Kubelet configuration defines the contract between the Kubernetes control plane and the node operating system. Parameters such as `maxPods` establish hard limits on schedulable pod density, `evictionHard` thresholds trigger proactive pod eviction when node resources fall below critical levels, and `imageGCHighThresholdPercent` controls disk space reclamation for unused container images. These settings are not arbitrary tuning knobs but capacity invariants that prevent cascading failure: if disk usage exceeds ninety-five percent, the kubelet cannot pull new images, pod scheduling stalls, and the node becomes unusable. Similarly, setting `maxPods` too high relative to the instance's network interface elastic network interface attachment limit causes pod creation to fail with IP address exhaustion. The correct kubelet configuration for a given instance type derives from the intersection of AWS infrastructure constraints—ENI limits, IP addresses per ENI, instance storage IOPS—and workload characteristics—average pod resource requests, image sizes, and churn rates.

Capacity planning for EKS node groups is a constraint satisfaction problem with multiple interacting dimensions: compute cost, workload availability, scaling latency, and operational complexity. The objective function balances minimizing EC2 spend against maintaining sufficient headroom for pod scheduling and absorbing spot interruptions. The constraints include Kubernetes resource requests, daemon set overhead, kubelet and system reserved capacity, and the discrete granularity of EC2 instance types. A common error is provisioning nodes based solely on vCPU count without accounting for allocatable capacity: a `m5.large` instance provides two vCPUs, but kubelet reserves CPU for system daemons and the kubelet itself, leaving approximately 1.9 vCPU allocatable for pods. If each pod requests 500m CPU, only three pods fit per node, not four. The planning invariant is bin packing efficiency: maximize pod density per dollar spent while maintaining the reserve capacity required to handle node failures and scaling delays.

The financial dimension of spot instance optimization cannot be separated from availability engineering. Spot instances are priced dynamically per instance type and Availability Zone, creating a complex market where capacity and cost fluctuate independently. The optimal strategy diversifies across multiple instance families and sizes, leveraging the capacity-optimized allocation strategy in Auto Scaling Groups to select pools with the lowest interruption rate rather than the lowest price. This approach inverts the traditional cost-minimization heuristic: paying slightly more per hour to access more stable capacity pools reduces operational toil from frequent interruptions and improves workload availability. The invariant is interruption rate times operational cost exceeds savings: if spot interruptions require manual intervention, trigger cascading failures, or violate customer SLAs, the discount is illusory.

## 2. Core Architecture & Mechanics

The architecture of an EKS node group is a composition of AWS primitives: an Auto Scaling Group defines instance lifecycle policy, a Launch Template encodes instance configuration, an IAM instance profile grants AWS API permissions, and security groups constrain network traffic. When an operator creates a managed node group via the EKS API, AWS constructs these resources automatically, injecting cluster-specific parameters and maintaining internal bookkeeping that links the node group to the parent cluster. The Launch Template specifies AMI identifier, instance type, key pair, block device mappings, and user data script, which executes during instance initialization to bootstrap the kubelet and join the cluster. The Auto Scaling Group monitors instance health, maintains the desired capacity, and integrates with EC2 Spot to request capacity across multiple instance types and Availability Zones.

```
EKS Cluster (API Server Endpoint, CA Certificate)
    │
    ├─── Managed Node Group
    │      ├─── Auto Scaling Group (desired: 3, min: 1, max: 10)
    │      │      ├─── Launch Template (AMI, instance type, user data)
    │      │      ├─── Mixed Instances Policy (instance types, spot/on-demand ratio)
    │      │      └─── Lifecycle Hooks (node drain on termination)
    │      │
    │      ├─── EC2 Instances (worker nodes)
    │      │      ├─── kubelet (node registration, pod reconciliation)
    │      │      ├─── containerd (container runtime)
    │      │      ├─── kube-proxy (service network routing)
    │      │      ├─── AWS VPC CNI (pod networking, ENI management)
    │      │      └─── CloudWatch Agent (metrics, logs)
    │      │
    │      └─── IAM Instance Profile
    │             ├─── Policies (ECR pull, EC2 describe, CloudWatch logs)
    │             └─── Assume Role (allow EC2 to assume this role)
    │
    └─── Self-Managed Node Group
           ├─── Auto Scaling Group (manual configuration)
           ├─── Launch Template (custom user data, bootstrap script)
           ├─── Security Groups (cluster control plane SG, node SG)
           └─── aws-auth ConfigMap (map IAM role to RBAC group)
```

The kubelet bootstrap sequence on a managed node follows a deterministic initialization path. The EKS-optimized AMI includes a bootstrap script at `/etc/eks/bootstrap.sh` that the Launch Template user data invokes with cluster name and optional arguments. This script retrieves the cluster API server endpoint and base64-encoded CA certificate from the EKS DescribeCluster API, generates a kubeconfig file at `/var/lib/kubelet/kubeconfig` with the IAM authenticator configured as the authentication exec plugin, writes kubelet systemd unit overrides, and starts the kubelet service. The kubelet immediately begins a registration loop: it constructs a Node object with capacity information derived from instance metadata, submits a certificate signing request to the API server, and authenticates using the AWS IAM Authenticator, which validates the instance's IAM role against the `aws-auth` ConfigMap. Once authenticated, the node controller in the control plane approves the CSR, the kubelet obtains a client certificate, and the Node object transitions to Ready status.

```yaml
# Managed Node Group Definition
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: production-cluster
  region: us-west-2
  version: "1.28"

managedNodeGroups:
  - name: system-pool
    instanceType: m5.large
    desiredCapacity: 3
    minSize: 1
    maxSize: 10
    volumeSize: 100
    volumeType: gp3
    volumeIOPS: 3000
    volumeThroughput: 125
    labels:
      role: system
      workload-type: critical
    tags:
      Environment: production
      ManagedBy: eksctl
    iam:
      withAddonPolicies:
        autoScaler: true
        ebs: true
        fsx: true
        efs: true
        albIngress: true
        cloudWatch: true
    ssh:
      allow: true
      publicKeyPath: ~/.ssh/eks-nodes.pub
    privateNetworking: true
    subnets:
      - subnet-0a1b2c3d4e5f6g7h8
      - subnet-1b2c3d4e5f6g7h8i9
      - subnet-2c3d4e5f6g7h8i9j0
    securityGroups:
      attachIDs:
        - sg-0123456789abcdef0
    preBootstrapCommands:
      - "yum install -y amazon-cloudwatch-agent"
      - "systemctl enable amazon-cloudwatch-agent"
    overrideBootstrapCommand: |
      #!/bin/bash
      set -o xtrace
      /etc/eks/bootstrap.sh production-cluster \
        --kubelet-extra-args '--max-pods=110 --eviction-hard=memory.available<500Mi,nodefs.available<10%' \
        --b64-cluster-ca LS0tLS1CRUdJTi... \
        --apiserver-endpoint https://EXAMPLE.gr7.us-west-2.eks.amazonaws.com
```

For self-managed node groups, the operator assumes responsibility for all bootstrap logic. The Launch Template user data must explicitly invoke the EKS bootstrap script with correct cluster name and parameters, or implement equivalent logic to generate kubeconfig, configure kubelet, and start services. The IAM instance profile must include policies granting `eks:DescribeCluster`, `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:GetDownloadUrlForLayer`, and `ecr:BatchGetImage` permissions for image pulls, plus `ec2:DescribeInstances` for ENI management by the VPC CNI plugin. The operator must also update the `aws-auth` ConfigMap in the `kube-system` namespace to map the node IAM role ARN to the `system:bootstrappers` and `system:nodes` groups, enabling authentication and RBAC authorization.

```yaml
# Self-Managed Node Group Launch Template User Data
#!/bin/bash
set -o xtrace

# Install SSM agent for session manager access
yum install -y amazon-ssm-agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Configure kernel parameters for networking performance
cat <<EOF >> /etc/sysctl.conf
net.ipv4.tcp_max_syn_backlog = 8096
net.core.somaxconn = 32768
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.core.netdev_max_backlog = 16384
EOF
sysctl -p

# Configure containerd for performance
mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
systemctl restart containerd

# Bootstrap kubelet with custom configuration
CLUSTER_NAME="production-cluster"
REGION="us-west-2"
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d ' ' -f 2)

/etc/eks/bootstrap.sh ${CLUSTER_NAME} \
  --kubelet-extra-args '--node-labels=node.kubernetes.io/lifecycle=spot,workload-type=batch --register-with-taints=spot=true:NoSchedule --max-pods=110 --kube-reserved=cpu=250m,memory=1Gi,ephemeral-storage=1Gi --system-reserved=cpu=250m,memory=0.2Gi,ephemeral-storage=1Gi --eviction-hard=memory.available<500Mi,nodefs.available<10%,imagefs.available<10% --eviction-soft=memory.available<1Gi,nodefs.available<15%,imagefs.available<15% --eviction-soft-grace-period=memory.available=2m,nodefs.available=2m,imagefs.available=2m --image-gc-high-threshold=85 --image-gc-low-threshold=80'

# Install and configure node monitoring agent
yum install -y amazon-cloudwatch-agent
cat <<EOF > /opt/aws/amazon-cloudwatch-agent/etc/config.json
{
  "metrics": {
    "namespace": "EKS/NodeMetrics",
    "metrics_collected": {
      "cpu": {
        "measurement": [{"name": "cpu_usage_idle", "rename": "CPU_IDLE", "unit": "Percent"}],
        "totalcpu": false
      },
      "disk": {
        "measurement": [{"name": "used_percent", "rename": "DISK_USED", "unit": "Percent"}],
        "resources": ["*"]
      },
      "mem": {
        "measurement": [{"name": "mem_used_percent", "rename": "MEM_USED", "unit": "Percent"}]
      }
    }
  }
}
EOF
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

The `aws-auth` ConfigMap is the authoritative mapping between IAM principals and Kubernetes RBAC groups. When the kubelet authenticates using the AWS IAM Authenticator, the authenticator validates the signed request against AWS STS, extracts the IAM role ARN, and consults the `aws-auth` ConfigMap to determine which Kubernetes groups the authenticated identity should join. For nodes, the mapping grants membership in `system:bootstrappers` to allow CSR submission and `system:nodes` to enable node-specific API operations like status updates and secret retrieval for mounted volumes.

```yaml
# aws-auth ConfigMap for self-managed node authentication
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/EKSNodeInstanceRole
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::123456789012:role/EKSFargateExecutionRole
      username: system:node:{{SessionName}}
      groups:
        - system:bootstrappers
        - system:nodes
        - system:node-proxier
  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/admin
      username: admin
      groups:
        - system:masters
```

Spot instance integration in EKS node groups leverages Auto Scaling Group mixed instances policies to allocate capacity across multiple instance types and purchasing options. The capacity-optimized allocation strategy queries real-time spot capacity availability across all specified instance types and Availability Zones, selecting pools with the deepest capacity to minimize interruption probability. The operator specifies a base on-demand capacity count and a percentage of additional capacity to fulfill with spot instances, allowing deterministic placement of critical workloads on stable on-demand nodes while opportunistically scaling batch workloads on spot capacity.

```yaml
# Auto Scaling Group with Spot Instance Diversification
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: production-cluster
  region: us-west-2

managedNodeGroups:
  - name: batch-pool
    minSize: 2
    maxSize: 50
    desiredCapacity: 10
    instanceTypes:
      - m5.xlarge
      - m5a.xlarge
      - m5n.xlarge
      - m4.xlarge
      - m5d.xlarge
      - c5.xlarge
      - c5a.xlarge
      - c5n.xlarge
    spot: true
    labels:
      workload-type: batch
      node.kubernetes.io/lifecycle: spot
    taints:
      - key: spot
        value: "true"
        effect: NoSchedule
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/production-cluster: "owned"
    iam:
      withAddonPolicies:
        autoScaler: true
        cloudWatch: true
```

The Cluster Autoscaler observes pod scheduling failures and scales node groups to meet demand. It operates as a Kubernetes deployment running in the cluster, querying the API server for pending pods, calculating required additional capacity, and invoking Auto Scaling Group APIs to adjust desired capacity. The autoscaler respects expander policies that prioritize certain node groups, skip nodes with local storage or specific taints, and delay scale-down to prevent thrashing. The scale-down logic is conservative: it simulates pod rescheduling to verify all pods can fit on remaining nodes, respects pod disruption budgets, and avoids terminating nodes running pods with `cluster-autoscaler.kubernetes.io/safe-to-evict=false` annotations.

```yaml
# Cluster Autoscaler Deployment
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
            - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/production-cluster
            - --balance-similar-node-groups
            - --skip-nodes-with-system-pods=false
            - --scale-down-delay-after-add=10m
            - --scale-down-unneeded-time=10m
            - --scale-down-utilization-threshold=0.5
            - --max-node-provision-time=15m
          resources:
            limits:
              cpu: 100m
              memory: 600Mi
            requests:
              cpu: 100m
              memory: 600Mi
          env:
            - name: AWS_REGION
              value: us-west-2
---
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
```

Node lifecycle hooks enable graceful draining before termination. AWS Auto Scaling Groups support lifecycle hooks that pause instance termination, sending notifications to SNS topics or invoking Lambda functions. The operator deploys a controller that subscribes to these notifications, cordons the terminating node, drains pods with configurable timeout and pod disruption budget enforcement, waits for pod termination, and completes the lifecycle action to allow instance shutdown. This automation prevents abrupt termination that leaves pods in Terminating state indefinitely or causes workload interruptions exceeding pod disruption budget constraints.

```python
# Lambda function for ASG lifecycle hook node draining
import boto3
import json
import subprocess
from base64 import b64decode

asg_client = boto3.client('autoscaling')
ec2_client = boto3.client('ec2')

def lambda_handler(event, context):
    """
    Handle ASG lifecycle hook for graceful node drain.
    Triggered by CloudWatch Events when instance enters TERMINATING:WAIT state.
    """
    message = json.loads(event['Records'][0]['Sns']['Message'])
    lifecycle_hook_name = message['LifecycleHookName']
    auto_scaling_group_name = message['AutoScalingGroupName']
    lifecycle_action_token = message['LifecycleActionToken']
    instance_id = message['EC2InstanceId']
    
    # Retrieve private DNS name for node identification
    instance_info = ec2_client.describe_instances(InstanceIds=[instance_id])
    private_dns = instance_info['Reservations'][0]['Instances'][0]['PrivateDnsName']
    node_name = private_dns
    
    # Cordon and drain node using kubectl via EKS API
    cluster_name = 'production-cluster'
    region = 'us-west-2'
    
    try:
        # Update kubeconfig for cluster access
        subprocess.run([
            'aws', 'eks', 'update-kubeconfig',
            '--name', cluster_name,
            '--region', region
        ], check=True)
        
        # Cordon node to prevent new pod scheduling
        subprocess.run([
            'kubectl', 'cordon', node_name
        ], check=True)
        
        # Drain node with grace period and PDB respect
        subprocess.run([
            'kubectl', 'drain', node_name,
            '--ignore-daemonsets',
            '--delete-emptydir-data',
            '--force',
            '--grace-period=120',
            '--timeout=300s'
        ], check=True)
        
        # Complete lifecycle action to proceed with termination
        asg_client.complete_lifecycle_action(
            LifecycleHookName=lifecycle_hook_name,
            AutoScalingGroupName=auto_scaling_group_name,
            LifecycleActionToken=lifecycle_action_token,
            LifecycleActionResult='CONTINUE',
            InstanceId=instance_id
        )
        
        return {'statusCode': 200, 'body': f'Node {node_name} drained successfully'}
        
    except subprocess.CalledProcessError as e:
        # Abandon lifecycle action on drain failure
        asg_client.complete_lifecycle_action(
            LifecycleHookName=lifecycle_hook_name,
            AutoScalingGroupName=auto_scaling_group_name,
            LifecycleActionToken=lifecycle_action_token,
            LifecycleActionResult='ABANDON',
            InstanceId=instance_id
        )
        return {'statusCode': 500, 'body': f'Drain failed: {str(e)}'}
```

The AWS Node Termination Handler provides a more robust alternative to custom Lambda functions, running as a DaemonSet on every node to monitor EC2 metadata for spot interruption notices, scheduled maintenance events, and instance rebalance recommendations. When it detects an impending termination, it cordons the node locally and drains pods using the Kubernetes client library, ensuring graceful shutdown even if the control plane is temporarily unreachable. The handler respects pod disruption budgets, retries transient failures, and logs detailed telemetry for post-incident analysis.

```yaml
# AWS Node Termination Handler DaemonSet
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
    rollingUpdate:
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: aws-node-termination-handler
    spec:
      serviceAccountName: aws-node-termination-handler
      hostNetwork: true
      priorityClassName: system-node-critical
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: kubernetes.io/os
                    operator: In
                    values:
                      - linux
                  - key: node.kubernetes.io/lifecycle
                    operator: In
                    values:
                      - spot
      containers:
        - name: aws-node-termination-handler
          image: public.ecr.aws/aws-ec2/aws-node-termination-handler:v1.21.0
          imagePullPolicy: IfNotPresent
          securityContext:
            privileged: true
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
            - name: DELETE_LOCAL_DATA
              value: "true"
            - name: IGNORE_DAEMON_SETS
              value: "true"
            - name: POD_TERMINATION_GRACE_PERIOD
              value: "120"
            - name: WEBHOOK_URL
              value: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-node-termination-handler
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aws-node-termination-handler
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "patch", "update"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  - apiGroups: [""]
    resources: ["pods/eviction"]
    verbs: ["create"]
  - apiGroups: ["apps"]
    resources: ["daemonsets"]
    verbs: ["get", "list"]
  - apiGroups: ["policy"]
    resources: ["poddisruptionbudgets"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: aws-node-termination-handler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: aws-node-termination-handler
subjects:
  - kind: ServiceAccount
    name: aws-node-termination-handler
    namespace: kube-system
```

Kubelet configuration in EKS is partially controlled by the bootstrap script and partially overridable via `kubelet-extra-args`. Critical parameters include `maxPods`, which is calculated from the instance ENI limit and IP addresses per ENI using the formula `(ENI_count - 1) * (IPs_per_ENI - 1) + 2`, reserving one ENI for the primary instance network interface and one IP per ENI for the interface itself. For example, an `m5.large` instance supports three ENIs with ten IPs each, yielding `(3 - 1) * (10 - 1) + 2 = 20` maximum pods. Operators can override this with custom CNI configurations or alternative networking plugins, but must ensure the kubelet limit matches CNI capacity to avoid scheduling pods that fail due to IP exhaustion.

```bash
# Calculate maxPods for common instance types
# m5.large: 3 ENIs, 10 IPs per ENI
# (3 - 1) * (10 - 1) + 2 = 20 pods

# m5.xlarge: 4 ENIs, 15 IPs per ENI
# (4 - 1) * (15 - 1) + 2 = 44 pods

# m5.2xlarge: 4 ENIs, 15 IPs per ENI
# (4 - 1) * (15 - 1) + 2 = 44 pods

# m5.4xlarge: 8 ENIs, 30 IPs per ENI
# (8 - 1) * (30 - 1) + 2 = 205 pods

# For custom CNI prefix delegation mode:
# m5.large: 3 ENIs, 1 /28 prefix per ENI = 16 IPs per prefix
# (3 - 1) * 16 + 2 = 34 pods (but AWS limits to 110 max)
```

Eviction thresholds prevent node resource exhaustion by proactively terminating pods when disk, memory, or process ID limits approach critical levels. Hard eviction thresholds trigger immediate pod termination without grace period, while soft thresholds allow configurable grace periods. The kubelet monitors node resource usage at five-second intervals, comparing against thresholds and selecting eviction candidates based on QoS class (BestEffort terminated first, then Burstable, then Guaranteed) and resource usage relative to requests. The operator must tune these thresholds based on workload characteristics: batch jobs with large temporary disk usage require higher `nodefs.available` thresholds, while memory-intensive workloads need larger `memory.available` buffers.

```yaml
# Comprehensive kubelet configuration flags
--max-pods=110
--kube-reserved=cpu=250m,memory=1Gi,ephemeral-storage=1Gi,pid=1000
--system-reserved=cpu=250m,memory=0.2Gi,ephemeral-storage=1Gi,pid=1000
--eviction-hard=memory.available<500Mi,nodefs.available<10%,imagefs.available<10%,pid.available<5%
--eviction-soft=memory.available<1Gi,nodefs.available<15%,imagefs.available<15%
--eviction-soft-grace-period=memory.available=2m,nodefs.available=2m,imagefs.available=2m
--eviction-max-pod-grace-period=120
--image-gc-high-threshold=85
--image-gc-low-threshold=80
--feature-gates=RotateKubeletServerCertificate=true,CSIMigration=true
--container-runtime-endpoint=unix:///run/containerd/containerd.sock
--node-labels=node.kubernetes.io/instance-type=m5.xlarge,topology.kubernetes.io/zone=us-west-2a,workload-type=general
--register-with-taints=node.kubernetes.io/unschedulable=true:NoSchedule
--pod-infra-container-image=602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/pause:3.5
```

The CNI plugin is responsible for allocating IP addresses to pods and configuring network routes. The AWS VPC CNI plugin manages ENI attachment and IP address allocation, attaching additional ENIs to the instance as pod density increases and assigning secondary IPs from the VPC subnet CIDR. The CNI maintains a warm pool of pre-allocated IPs to reduce pod startup latency, configurable via `WARM_IP_TARGET` and `MINIMUM_IP_TARGET` environment variables in the `aws-node` DaemonSet. Operators must ensure VPC subnets have sufficient IP address capacity for peak pod counts across all nodes, accounting for warm pool overhead. A subnet with a /24 CIDR provides 251 usable IPs (256 minus five AWS-reserved addresses), supporting approximately twelve `m5.xlarge` nodes with 20 pods each if warm pools are disabled, fewer with warm pools enabled.

```yaml
# AWS VPC CNI DaemonSet configuration
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: aws-node
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: aws-node
  template:
    metadata:
      labels:
        k8s-app: aws-node
    spec:
      hostNetwork: true
      priorityClassName: system-node-critical
      serviceAccountName: aws-node
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: kubernetes.io/os
                    operator: In
                    values:
                      - linux
                  - key: kubernetes.io/arch
                    operator: In
                    values:
                      - amd64
                      - arm64
                  - key: eks.amazonaws.com/compute-type
                    operator: NotIn
                    values:
                      - fargate
      containers:
        - name: aws-node
          image: 602401143452.dkr.ecr.us-west-2.amazonaws.com/amazon-k8s-cni:v1.16.0
          ports:
            - containerPort: 61678
              name: metrics
          env:
            - name: ADDITIONAL_ENI_TAGS
              value: '{"ClusterName":"production-cluster","Environment":"production"}'
            - name: AWS_VPC_CNI_NODE_PORT_SUPPORT
              value: "true"
            - name: AWS_VPC_ENI_MTU
              value: "9001"
            - name: AWS_VPC_K8S_CNI_CONFIGURE_RPFILTER
              value: "false"
            - name: AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG
              value: "false"
            - name: AWS_VPC_K8S_CNI_EXTERNALSNAT
              value: "false"
            - name: AWS_VPC_K8S_CNI_LOG_FILE
              value: "/host/var/log/aws-routed-eni/ipamd.log"
            - name: AWS_VPC_K8S_CNI_LOGLEVEL
              value: "DEBUG"
            - name: AWS_VPC_K8S_CNI_RANDOMIZESNAT
              value: "prng"
            - name: AWS_VPC_K8S_CNI_VETHPREFIX
              value: "eni"
            - name: AWS_VPC_K8S_PLUGIN_LOG_FILE
              value: "/var/log/aws-routed-eni/plugin.log"
            - name: AWS_VPC_K8S_PLUGIN_LOG_LEVEL
              value: "DEBUG"
            - name: DISABLE_INTROSPECTION
              value: "false"
            - name: DISABLE_METRICS
              value: "false"
            - name: DISABLE_NETWORK_RESOURCE_PROVISIONING
              value: "false"
            - name: ENABLE_IPv4
              value: "true"
            - name: ENABLE_IPv6
              value: "false"
            - name: ENABLE_POD_ENI
              value: "false"
            - name: ENABLE_PREFIX_DELEGATION
              value: "false"
            - name: WARM_ENI_TARGET
              value: "1"
            - name: WARM_IP_TARGET
              value: "3"
            - name: MINIMUM_IP_TARGET
              value: "10"
            - name: MY_NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          resources:
            requests:
              cpu: 25m
              memory: 256Mi
            limits:
              cpu: 100m
              memory: 512Mi
          securityContext:
            capabilities:
              add:
                - NET_ADMIN
                - NET_RAW
          volumeMounts:
            - mountPath: /host/opt/cni/bin
              name: cni-bin-dir
            - mountPath: /host/etc/cni/net.d
              name: cni-net-dir
            - mountPath: /host/var/log/aws-routed-eni
              name: log-dir
            - mountPath: /var/run/aws-node
              name: run-dir
      volumes:
        - name: cni-bin-dir
          hostPath:
            path: /opt/cni/bin
        - name: cni-net-dir
          hostPath:
            path: /etc/cni/net.d
        - name: log-dir
          hostPath:
            path: /var/log/aws-routed-eni
            type: DirectoryOrCreate
        - name: run-dir
          hostPath:
            path: /var/run/aws-node
            type: DirectoryOrCreate
```

## 3. High-Performance Optimization & Failure Modes

The performance profile of an EKS node group is determined by the interaction of instance type selection, pod density, network throughput, and disk IOPS. The optimal instance type balances compute, memory, and network capacity with cost efficiency, but the relationship is nonlinear: doubling vCPU count does not double pod capacity due to kubelet overhead, daemon set resource consumption, and ENI/IP address limits. A common error is selecting compute-optimized instances for memory-intensive workloads or memory-optimized instances for network-intensive services. The operator must profile workload resource usage patterns using metrics-server data, Prometheus histograms, and CloudWatch Container Insights to identify bottlenecks and match instance families to actual usage.

Network performance in EKS is constrained by instance ENI limits, bandwidth caps, and packets-per-second (PPS) thresholds. Each instance type supports a maximum network bandwidth and PPS rate, with larger instances offering proportionally higher limits but not always better per-dollar efficiency. For example, `m5.xlarge` provides up to 10 Gbps bandwidth and 1 million PPS, while `m5.2xlarge` offers 10 Gbps but higher baseline throughput due to dedicated EBS bandwidth. The AWS VPC CNI plugin adds latency overhead for inter-pod communication when pods reside on different ENIs, as packets traverse the kernel network stack twice. Operators can mitigate this by enabling prefix delegation mode, which allocates entire /28 IP prefixes to ENIs instead of individual secondary IPs, increasing pod density and reducing ENI churn but consuming more VPC IP address space.

Disk performance depends on EBS volume type, IOPS, and throughput limits. The default `gp3` volumes provide 3,000 IOPS and 125 MB/s baseline throughput, sufficient for most container images and logs, but workloads with heavy local disk activity—such as build agents, data processing pipelines, or machine learning training—require provisioned IOPS `io2` volumes with custom IOPS and throughput settings. The kubelet's ephemeral storage accounting tracks disk usage for pod emptyDir volumes, container writable layers, and image layers, triggering evictions when `nodefs.available` thresholds are breached. Operators must size root volumes based on the sum of all container images, maximum concurrent pod count multiplied by average emptyDir usage, and container log retention policy. A conservative estimate is 100 GB root volume plus 10 GB per 10 pods, adjusted for workload-specific disk patterns.

The failure mode space for node groups encompasses instance failures, network partitions, API server connectivity loss, and Auto Scaling Group scaling failures. Instance failures manifest as node NotReady status when kubelet heartbeats cease, typically due to kernel panics, out-of-memory kills, or EC2 host hardware failure. The node controller in the control plane tolerates five minutes of missed heartbeats before marking the node NotReady and evicting pods to other nodes. Operators reduce blast radius by distributing replicas across multiple Availability Zones and ensuring pod disruption budgets constrain simultaneous evictions. Network partitions isolate nodes from the API server, preventing kubelet from updating pod status, retrieving secrets, or acknowledging new pod assignments. The kubelet continues running existing pods but cannot create new ones, eventually triggering pod evictions due to liveness probe failures or resource pressure.

Auto Scaling Group scaling failures occur when EC2 capacity is unavailable in specified instance types and Availability Zones, a common issue during AWS region-wide demand spikes or when requesting large instance types with limited availability. The mixed instances policy mitigates this by specifying multiple instance types, but scaling can still fail if all pools are exhausted. The operator must monitor CloudWatch metrics for `GroupInServiceInstances` versus `GroupDesiredCapacity` divergence, alerting when the gap persists beyond five minutes, indicating sustained capacity shortage. The mitigation is to broaden instance type diversity, add on-demand base capacity to ensure minimum viable cluster size, and implement workload scheduling policies that gracefully degrade during capacity constraints rather than failing hard.

Spot instance interruptions require architectural resilience at both the infrastructure and application layers. The two-minute interruption notice provides a narrow window for graceful shutdown, insufficient for long-running batch jobs or stateful workloads with complex shutdown sequences. The operator must classify workloads by interruption tolerance: stateless web services can tolerate arbitrary interruptions if sufficient replicas remain, batch jobs must implement checkpointing and restart logic, and stateful services should run on on-demand nodes with persistent volume reattachment orchestration. The AWS Node Termination Handler drains nodes during interruptions, but pod disruption budgets must be configured to permit evictions without blocking drain operations indefinitely. A common error is setting minimum available replicas equal to total replicas, preventing any evictions and causing drain timeouts.

Capacity planning for mixed on-demand and spot fleets requires calculating the minimum on-demand capacity required to maintain service availability guarantees during worst-case spot interruption scenarios. If a service requires five replicas to meet SLA and spot instances comprise eighty percent of capacity, the cluster must maintain at least two on-demand nodes capable of running all five replicas during a complete spot pool interruption. The formula is `on_demand_capacity >= ceiling(required_replicas * (1 / (1 - spot_fraction)))`, where `spot_fraction` is the target percentage of spot instances. For eighty percent spot, `on_demand_capacity >= ceiling(5 * (1 / 0.2)) = 25` replicas worth of capacity, ensuring five replicas can always schedule even if all spot capacity disappears. This conservative estimate assumes uniform pod sizes; heterogeneous workloads require bin-packing simulation to determine actual capacity requirements.

The kubelet CPU throttling failure mode occurs when pod CPU limits are set significantly lower than requests, causing containers to hit cgroup CPU quota limits during brief usage spikes. The Linux kernel enforces CPU limits by throttling the cgroup when it exhausts its quota within the CFS period (typically 100 milliseconds), even if the node has idle CPU capacity. This manifests as increased request latency, timeout errors, and poor performance despite low average CPU utilization. The mitigation is to set CPU limits at two to four times the request value for burstable workloads, or omit limits entirely for latency-sensitive services, relying on QoS classes and eviction to manage node resource contention. Monitoring throttled CPU time via the `container_cpu_cfs_throttled_seconds_total` metric identifies affected workloads.

Memory pressure eviction failures arise when the kubelet cannot evict pods quickly enough to reclaim memory before the kernel out-of-memory (OOM) killer terminates processes. The OOM killer selects victims based on per-process OOM scores, which factor memory usage, process priority, and OOM adjust values set by the kubelet. Kubernetes sets lower OOM scores for higher-priority pods, protecting system components and Guaranteed QoS pods from premature termination. However, the OOM killer operates independently of pod disruption budgets and grace periods, potentially violating availability guarantees during severe memory pressure. The operator must tune `eviction-hard` and `eviction-soft` thresholds to trigger pod eviction before memory exhaustion, provide sufficient `kube-reserved` and `system-reserved` capacity to buffer kernel and kubelet overhead, and monitor `node_memory_MemAvailable_bytes` to detect trending exhaustion before OOM events.

Image pull performance impacts pod startup latency, particularly for large container images or when launching many pods simultaneously. The kubelet pulls images serially by default, with configurable parallelism via `serializeImagePulls=false` and `maxParallelImagePulls` settings. Each pull consumes network bandwidth and disk IOPS, potentially saturating node resources during rapid scaling events. The mitigation is to use image pull secrets with Amazon ECR, enable VPC endpoints for ECR to avoid NAT gateway bandwidth costs, pre-pull common base images via DaemonSets, and employ image layering strategies that maximize layer reuse across workloads. Monitoring `kubelet_runtime_operations_duration_seconds` histogram for `image_pull` operations identifies performance bottlenecks.

Cluster autoscaler lag causes delayed scaling responses when workload demand spikes, leaving pods pending until new nodes launch, register, and become Ready—a process requiring three to five minutes for standard instances, longer for large instance types or custom AMIs with complex bootstrap logic. The operator reduces lag by maintaining warm node pools with minimum instance counts set above zero, configuring aggressive scale-up policies in the autoscaler (lower `scale-down-utilization-threshold`, shorter `scale-down-unneeded-time`), and using overprovisioning pods that reserve capacity but run at lowest priority, evicting instantly when real workloads need resources. The overprovision strategy maintains N idle slots across the cluster, ensuring immediate scheduling for bursty workloads while autoscaling replaces the evicted overprovision pods in the background.

```yaml
# Overprovisioning deployment to maintain warm capacity
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-overprovisioner
  namespace: kube-system
spec:
  replicas: 5
  selector:
    matchLabels:
      app: cluster-overprovisioner
  template:
    metadata:
      labels:
        app: cluster-overprovisioner
    spec:
      priorityClassName: overprovisioning
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.9
          resources:
            requests:
              cpu: 1000m
              memory: 4Gi
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: overprovisioning
value: -1
globalDefault: false
description: "Priority class for cluster overprovisioning pods"
```

The node registration delay failure mode occurs when kubelet bootstrap scripts fail due to network issues, IAM permission errors, or incorrect cluster configuration parameters. Symptoms include instances launching successfully in the Auto Scaling Group but never appearing as Nodes in the Kubernetes API, causing autoscaling to continuously launch replacement instances without increasing cluster capacity. The diagnostic process involves SSH or SSM Session Manager access to the instance, reviewing `/var/log/cloud-init-output.log` and `journalctl -u kubelet` for bootstrap errors, verifying IAM instance profile permissions, confirming security group rules allow kubelet to reach the API server on port 443, and validating the `aws-auth` ConfigMap contains the correct node IAM role mapping. The permanent fix ensures bootstrap scripts are tested in staging environments, implement retry logic for transient AWS API failures, and include health checks that prevent instance registration until kubelet is confirmed running and node is Ready.

Pod eviction during node updates can violate application availability requirements if replica counts, pod disruption budgets, and anti-affinity rules are not correctly configured. The drain operation evicts pods respecting disruption budgets, but if a deployment has two replicas with a disruption budget allowing zero unavailable pods, draining any node running a replica blocks until another replica schedules elsewhere—potentially impossible if all nodes are cordoned. The operator must ensure `maxUnavailable` in disruption budgets is nonzero for stateless services, maintain surplus capacity to accept evicted pods, and use pod anti-affinity to spread replicas across nodes and Availability Zones, preventing all replicas from landing on nodes targeted for simultaneous updates. The update strategy should configure managed node group updates with surge capacity, launching replacement nodes before draining old nodes.

```yaml
# Pod Disruption Budget for stateless service
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-service-pdb
  namespace: production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web-service
---
# Deployment with anti-affinity and replica spread
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-service
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: web-service
  template:
    metadata:
      labels:
        app: web-service
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: web-service
              topologyKey: kubernetes.io/hostname
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: web-service
                topologyKey: topology.kubernetes.io/zone
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: web-service
      containers:
        - name: web
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
```

The CNI IP address exhaustion failure mode occurs when VPC subnet CIDR ranges cannot accommodate the desired pod density across all nodes. The AWS VPC CNI allocates secondary IPs from the subnet CIDR to pods, competing with other EC2 instances, load balancers, and RDS databases for IP address space. The operator must calculate total IP requirements as `(node_count * maxPods) + warm_pool_overhead + non_k8s_resources`, ensuring each subnet has sufficient free IPs. For example, a subnet with /24 CIDR provides 251 usable IPs; with ten nodes each running twenty pods, the requirement is 200 IPs for pods plus ten for node primary interfaces plus thirty for warm pools, totaling 240 IPs, leaving minimal headroom. The mitigation is to allocate dedicated /20 or /19 subnets for EKS node groups, enable CNI prefix delegation to increase pod density without consuming more IPs, or adopt custom CNI plugins like Calico that use overlay networking and do not require VPC IP address allocation per pod.

Monitoring and alerting for node group health requires instrumentation at multiple layers: EC2 Auto Scaling Group metrics for instance launch failures and scaling activity, Kubernetes node metrics for NotReady status and resource pressure conditions, kubelet metrics for pod eviction rates and image pull latency, and workload-specific metrics for application performance degradation. Critical alerts include node NotReady for more than five minutes, pod pending due to insufficient CPU or memory for more than two minutes, autoscaler scaling activity failure, spot instance interruption rate exceeding twenty percent per hour, and node disk usage above eighty percent. These alerts should trigger automated remediation where possible—such as scaling up node groups, clearing disk space via image garbage collection, or terminating unhealthy instances—and escalate to on-call engineers for unresolvable failures.

The final operational invariant is continuous verification: node groups must be tested under realistic load and failure scenarios in staging environments before deploying configuration changes to production. This includes chaos engineering experiments that terminate random nodes, exhaust node resources, and simulate network partitions, verifying that workloads remain available, autoscaling responds correctly, and alerts fire as expected. The discipline of infrastructure-as-code captured in version-controlled configuration manifests, tested via CI/CD pipelines, and deployed through controlled rollout processes is not optional bureaucracy but the foundation of reliable, scalable Kubernetes operations on AWS EKS.
