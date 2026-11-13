# Operational Verification Labs: Cloud Native Systems

**Discipline:** Infrastructure
**Standard:** Production-Grade Operational Verification
**Prerequisites:** Linux CLI proficiency, basic Kubernetes familiarity, a cluster (kind/k3s/EKS acceptable)

---

## Lab Environment Setup

Before beginning any lab, verify your toolchain:

```bash
# Verify core toolchain
docker version --format '{{.Server.Version}}'
kubectl version --client --output=yaml
crictl version
helm version --short

# Confirm cluster connectivity
kubectl cluster-info
kubectl get nodes -o wide

# Confirm containerd socket is accessible
sudo ls -la /run/containerd/containerd.sock
```

All labs are designed to run sequentially. Each lab builds conceptual depth from the previous one. YAML manifests are complete and deployable as written.

---

## Lab 1: Cloud Native Architectures & Twelve-Factor Systems

### Objective

Verify that a twelve-factor application is correctly structured, that configuration is externalized into the environment, and that backing services are treated as attached resources. You will deploy a multi-tier application and inspect its runtime configuration binding.

### Background

The twelve-factor methodology is not a checklist — it is a set of constraints that make a service operable at scale. The most commonly violated factors in production are **III (Config)**, **IV (Backing Services)**, and **XI (Logs)**. This lab forces you to verify each one at the infrastructure level.

```mermaid
graph TD
    subgraph twelve_factor ["Twelve-Factor App Runtime Model"]
        subgraph config_plane ["Config Plane"]
            ENV["Environment Variables\n(ConfigMap / Secret)"]
            VAULT["External Secret Store\n(Vault / ASM)"]
        end
        subgraph app_plane ["Application Plane"]
            APP["12-Factor App Container"]
            LOG["stdout / stderr\n(Factor XI)"]
        end
        subgraph backing ["Backing Services (Factor IV)"]
            DB["PostgreSQL\n(attached resource)"]
            CACHE["Redis\n(attached resource)"]
            QUEUE["AMQP Broker\n(attached resource)"]
        end
        ENV -->|"injected at start"| APP
        VAULT -->|"dynamic secret"| APP
        APP -->|"Factor XI"| LOG
        APP -->|"connection string from env"| DB
        APP -->|"connection string from env"| CACHE
        APP -->|"connection string from env"| QUEUE
    end
```

### Step 1: Deploy a Twelve-Factor Reference Application

The following manifest encodes Factors III, IV, VI (processes), VII (port binding), VIII (concurrency), and XI (logs) directly into Kubernetes primitives.

```yaml
# twelve-factor-app.yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: twelve-factor
  labels:
    lab: "01"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: twelve-factor
data:
  # Factor III: Config stored in environment, not in code
  LOG_LEVEL: "info"
  APP_PORT: "8080"
  CACHE_TTL_SECONDS: "300"
  # Factor IV: Backing services identified by URL, not host alias
  DATABASE_URL: "postgresql://appuser:$(DB_PASSWORD)@postgres-svc.twelve-factor.svc.cluster.local:5432/appdb?sslmode=require"
  CACHE_URL: "redis://redis-svc.twelve-factor.svc.cluster.local:6379/0"
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: twelve-factor
type: Opaque
stringData:
  DB_PASSWORD: "s3cur3-lab-p4ssword"
  API_KEY: "lab-api-key-do-not-use-in-prod"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: twelve-factor-app
  namespace: twelve-factor
  annotations:
    # Factor X: Dev/prod parity annotation
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: "kubectl"
spec:
  # Factor VIII: Concurrency via process model (replicas = horizontal scale)
  replicas: 2
  selector:
    matchLabels:
      app: twelve-factor-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: twelve-factor-app
        version: "1.0.0"
    spec:
      # Factor VI: Stateless process — no local disk state
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: app
          # Using nginx as a stand-in; replace with your 12-factor app image
          image: nginx:1.25.3-alpine
          ports:
            # Factor VII: Port binding — app binds its own port
            - name: http
              containerPort: 8080
              protocol: TCP
          env:
            # Factor III: All config from ConfigMap and Secret
            - name: LOG_LEVEL
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: LOG_LEVEL
            - name: APP_PORT
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: APP_PORT
            - name: CACHE_TTL_SECONDS
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: CACHE_TTL_SECONDS
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secrets
                  key: DB_PASSWORD
            - name: DATABASE_URL
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: DATABASE_URL
            - name: CACHE_URL
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: CACHE_URL
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 15
            periodSeconds: 20
          # Factor XI: Logs to stdout/stderr — no log files
          # The container runtime captures stdout and routes to your log aggregator
          lifecycle:
            preStop:
              exec:
                # Factor IX: Fast shutdown — drain connections before SIGTERM
                command: ["/bin/sh", "-c", "sleep 5"]
      terminationGracePeriodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: twelve-factor-svc
  namespace: twelve-factor
spec:
  selector:
    app: twelve-factor-app
  ports:
    - name: http
      port: 80
      targetPort: 80
  type: ClusterIP
```

```bash
kubectl apply -f twelve-factor-app.yaml
kubectl -n twelve-factor rollout status deployment/twelve-factor-app
```

### Step 2: Verify Configuration Externalization (Factor III)

Inspect the running environment to confirm no configuration is baked into the container image.

```bash
# Get a running pod name
POD=$(kubectl -n twelve-factor get pods -l app=twelve-factor-app -o jsonpath='{.items[0].metadata.name}')

# Inspect injected environment variables — these must come from ConfigMap/Secret only
kubectl -n twelve-factor exec "$POD" -- env | sort

# Verify: DATABASE_URL and CACHE_URL are present and point to cluster-internal DNS
# They must NOT contain hardcoded IP addresses — only DNS names (Factor IV)
kubectl -n twelve-factor exec "$POD" -- env | grep -E 'DATABASE_URL|CACHE_URL|LOG_LEVEL'

# Confirm the secret value is accessible but not logged (Factor III compliance check)
kubectl -n twelve-factor exec "$POD" -- env | grep DB_PASSWORD
```

Expected output pattern:
```
CACHE_TTL_SECONDS=300
CACHE_URL=redis://redis-svc.twelve-factor.svc.cluster.local:6379/0
DATABASE_URL=postgresql://appuser:s3cur3-lab-p4ssword@postgres-svc.twelve-factor.svc.cluster.local:5432/appdb?sslmode=require
DB_PASSWORD=s3cur3-lab-p4ssword
LOG_LEVEL=info
```

### Step 3: Verify Log Routing (Factor XI)

```bash
# Factor XI: Logs are event streams to stdout — the platform routes them
kubectl -n twelve-factor logs "$POD" --tail=20

# Verify log stream goes to stdout (fd=1) not a file
kubectl -n twelve-factor exec "$POD" -- ls -la /proc/1/fd/1
# Expected: /proc/1/fd/1 -> /dev/pts/0  (or similar tty/pipe — NOT a file path)

# Confirm no log files are written to local disk (Factor VI: stateless process)
kubectl -n twelve-factor exec "$POD" -- find /var/log -type f 2>/dev/null | head -20
```

### Step 4: Verify Disposability (Factor IX)

```bash
# Measure graceful shutdown time — must be < terminationGracePeriodSeconds
time kubectl -n twelve-factor delete pod "$POD" --grace-period=30

# Observe rolling update respects health probes before cutover
kubectl -n twelve-factor set image deployment/twelve-factor-app app=nginx:1.25.4-alpine
kubectl -n twelve-factor rollout status deployment/twelve-factor-app --timeout=120s
kubectl -n twelve-factor rollout history deployment/twelve-factor-app
```

### Verification Checklist

```bash
# Full twelve-factor compliance sweep
echo "=== Factor III: Config externalized ==="
kubectl -n twelve-factor exec "$POD" -- env | grep -c "DATABASE_URL\|CACHE_URL\|LOG_LEVEL"

echo "=== Factor IV: Backing services as attached resources (DNS, not IP) ==="
kubectl -n twelve-factor exec "$POD" -- env | grep URL | grep -v "[0-9]\{1,3\}\.[0-9]\{1,3\}"

echo "=== Factor VI: No local state (no PVC attached) ==="
kubectl -n twelve-factor get pod "$POD" -o jsonpath='{.spec.volumes}' | python3 -m json.tool

echo "=== Factor XI: Logs to stdout ==="
kubectl -n twelve-factor logs "$POD" --tail=5 | wc -l
```

---

## Lab 2: Containerization Technologies (OCI, containerd, cgroups v2, Namespaces)

### Objective

Inspect the OCI bundle of a running container, examine containerd's internal state via its gRPC socket, verify cgroup v2 resource enforcement, and walk the Linux namespace tree of a pod. You will understand what Kubernetes pods look like below the abstraction layer.

### Background

A "container" is not a kernel primitive — it is a user-space construct made of three kernel features: **namespaces** (isolation), **cgroups** (resource accounting and limits), and a **root filesystem** (from an OCI image). containerd is the shim between Kubernetes and these kernel primitives.

```mermaid
graph TD
    subgraph container_stack ["Container Runtime Stack"]
        subgraph k8s_layer ["Kubernetes Layer"]
            KUBELET["kubelet"]
            CRI["CRI Interface\n(gRPC)"]
        end
        subgraph containerd_layer ["containerd Layer"]
            CTD["containerd daemon\n(/run/containerd/containerd.sock)"]
            SHIM["containerd-shim-runc-v2\n(per-container process)"]
            SNAPSHOTTER["Snapshotter\n(overlayfs)"]
        end
        subgraph kernel_layer ["Linux Kernel Layer"]
            RUNC["runc\n(OCI runtime)"]
            NS["Namespaces\n(net, pid, mnt, uts, ipc, user)"]
            CG["cgroups v2\n(/sys/fs/cgroup)"]
            OVL["OverlayFS\n(lowerdir + upperdir + workdir)"]
        end
        KUBELET -->|"CRI calls"| CRI
        CRI -->|"UNIX socket"| CTD
        CTD -->|spawns| SHIM
        SHIM -->|exec| RUNC
        RUNC -->|"clone() syscall"| NS
        RUNC -->|cgroup.procs| CG
        CTD -->|"layer management"| SNAPSHOTTER
        SNAPSHOTTER -->|mount| OVL
    end
```

### Step 1: Inspect containerd via crictl

```bash
# Confirm containerd runtime endpoint
sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock version

# List all pods known to containerd (bypasses Kubernetes API — ground truth)
sudo crictl pods

# List all containers with their state
sudo crictl ps -a

# Get a specific container ID for deep inspection
CONTAINER_ID=$(sudo crictl ps --name nginx -q | head -1)
echo "Target container: $CONTAINER_ID"

# Inspect the full container spec as seen by containerd
# This reveals the OCI runtime spec, mounts, namespaces, and cgroup path
sudo crictl inspect "$CONTAINER_ID" | python3 -m json.tool | head -100
```

### Step 2: Walk the OCI Runtime Bundle

```bash
# Find the bundle directory for the container
# containerd stores bundles under its state directory
BUNDLE_DIR=$(sudo crictl inspect "$CONTAINER_ID" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d['info']['runtimeSpec'].get('root',{}).get('path',''))" 2>/dev/null || \
  echo "not directly accessible")

# Alternative: find via containerd state path
sudo find /run/containerd -name "config.json" 2>/dev/null | head -5

# Inspect an OCI config.json — this IS the container's runtime specification
# It defines every aspect of the container's execution environment
CONFIG=$(sudo find /run/containerd -name "config.json" 2>/dev/null | head -1)
if [ -n "$CONFIG" ]; then
  echo "=== OCI Runtime Spec: $CONFIG ==="
  sudo cat "$CONFIG" | python3 -m json.tool
fi
```

The `config.json` output you should analyze:

```bash
# Key fields to verify in the OCI spec:
# 1. ociVersion — must be >= 1.0.0
# 2. process.args — the command the container runs
# 3. process.env — environment variables
# 4. mounts — bind mounts from host into container
# 5. linux.namespaces — namespace types used
# 6. linux.cgroupsPath — the cgroup path for resource enforcement

sudo find /run/containerd -name "config.json" 2>/dev/null | head -1 | xargs sudo cat | \
  python3 -c "
import sys, json
spec = json.load(sys.stdin)
print('=== OCI Version:', spec.get('ociVersion'))
print('=== Process Args:', spec.get('process', {}).get('args'))
print('=== Namespaces:')
for ns in spec.get('linux', {}).get('namespaces', []):
    print(f'  type={ns[\"type\"]} path={ns.get(\"path\",\"new\")}')
print('=== Cgroup Path:', spec.get('linux', {}).get('cgroupsPath'))
print('=== Mounts (first 5):')
for m in spec.get('mounts', [])[:5]:
    print(f'  {m[\"destination\"]} <- {m[\"source\"]} [{m.get(\"type\",\"bind\")}]')
"
```

### Step 3: Inspect cgroup v2 Resource Enforcement

Deploy a container with explicit resource limits so you can observe cgroup enforcement:

```yaml
# cgroup-verify-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: cgroup-verify
  namespace: default
  labels:
    lab: "02"
spec:
  containers:
    - name: stress
      image: polinux/stress:latest
      command: ["stress"]
      args:
        - "--cpu"
        - "2"       # Request 2 CPUs — cgroup will throttle to limit
        - "--vm"
        - "1"
        - "--vm-bytes"
        - "64M"     # Request 64MB memory
        - "--timeout"
        - "300s"
      resources:
        requests:
          cpu: "250m"
          memory: "64Mi"
        limits:
          cpu: "500m"      # This becomes cpu.max in cgroup v2
          memory: "128Mi"  # This becomes memory.max in cgroup v2
  restartPolicy: Never
```

```bash
kubectl apply -f cgroup-verify-pod.yaml
kubectl wait --for=condition=Running pod/cgroup-verify --timeout=60s

# Get the container ID
STRESS_ID=$(sudo crictl ps --name stress -q | head -1)

# Get the cgroup path from the OCI spec
CGROUP_PATH=$(sudo crictl inspect "$STRESS_ID" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('info',{}).get('runtimeSpec',{}).get('linux',{}).get('cgroupsPath',''))")

echo "cgroup path: $CGROUP_PATH"

# Navigate to cgroup v2 filesystem
# kubelet creates cgroups under: /sys/fs/cgroup/kubepods/
FULL_CG_PATH="/sys/fs/cgroup${CGROUP_PATH}"
echo "Full cgroup path: $FULL_CG_PATH"

# If the path exists, inspect resource controls
if [ -d "$FULL_CG_PATH" ]; then
  echo "=== CPU Quota (cpu.max) ==="
  # Format: "max_quota period" — 500m CPU = 50000/100000
  sudo cat "$FULL_CG_PATH/cpu.max"

  echo "=== Memory Limit (memory.max) ==="
  # 128Mi = 134217728 bytes
  sudo cat "$FULL_CG_PATH/memory.max"

  echo "=== Current Memory Usage ==="
  sudo cat "$FULL_CG_PATH/memory.current"

  echo "=== CPU Throttle Statistics ==="
  sudo cat "$FULL_CG_PATH/cpu.stat" | grep -E "throttled|usage"

  echo "=== PIDs in this cgroup ==="
  sudo cat "$FULL_CG_PATH/cgroup.procs"
fi
```

Expected cgroup v2 output interpretation:
```
cpu.max:    50000 100000   # 500m CPU = 50ms per 100ms period
memory.max: 134217728      # 128Mi in bytes
```

### Step 4: Walk the Linux Namespace Tree

```bash
# Get the PID of the container's init process (PID 1 inside container)
CONTAINER_PID=$(sudo crictl inspect "$STRESS_ID" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('info',{}).get('pid',''))")

echo "Container PID on host: $CONTAINER_PID"

# Inspect all namespaces for this process
# /proc/<pid>/ns/ contains symlinks to the namespace inode
sudo ls -la "/proc/$CONTAINER_PID/ns/"

# Compare namespace inodes with the host's init process
echo "=== Host init (PID 1) namespaces ==="
sudo ls -la /proc/1/ns/

echo "=== Container namespaces ==="
sudo ls -la "/proc/$CONTAINER_PID/ns/"

# Key observation: net, pid, mnt, uts namespaces differ (new for container)
# ipc namespace may be shared between containers in the same pod
# The numbers in the symlinks are inode IDs — matching inode = shared namespace

# Inspect network namespace: what interfaces does the container see?
sudo nsenter -t "$CONTAINER_PID" -n ip link show
sudo nsenter -t "$CONTAINER_PID" -n ip route show

# Inspect the mount namespace: what does the filesystem tree look like?
sudo nsenter -t "$CONTAINER_PID" -m mount | grep -E "overlay|proc|sys" | head -10

# Inspect the UTS namespace: what hostname does the container see?
sudo nsenter -t "$CONTAINER_PID" -u hostname
# Expected: pod name (e.g., "cgroup-verify"), not the host's hostname
```

### Step 5: Inspect the OverlayFS Layers

```bash
# Find the overlayfs mount for this container
# The upper layer is where all container writes land
sudo mount | grep overlay | head -5

# Inspect a specific overlay mount
# lowerdir = image layers (read-only)
# upperdir = container's write layer (ephemeral)
# workdir  = overlayfs internal work directory
OVERLAY_MOUNT=$(sudo mount | grep overlay | head -1)
echo "$OVERLAY_MOUNT"

# Parse the overlayfs options
sudo mount | grep overlay | head -1 | grep -oP 'lowerdir=\S+' | head -1

# Count the number of image layers (lowerdir is colon-separated)
LOWER=$(sudo mount | grep overlay | head -1 | grep -oP '(?<=lowerdir=)[^,]+')
echo "Number of image layers: $(echo "$LOWER" | tr ':' '\n' | wc -l)"
```

### Verification Checklist

```bash
echo "=== Lab 2 Verification ==="

echo "1. containerd socket accessible:"
sudo crictl version > /dev/null 2>&1 && echo "PASS" || echo "FAIL"

echo "2. OCI config.json found:"
sudo find /run/containerd -name "config.json" 2>/dev/null | wc -l | xargs -I{} sh -c '[ {} -gt 0 ] && echo "PASS: {} bundles" || echo "FAIL"'

echo "3. cgroup v2 mounted:"
mount | grep "cgroup2" > /dev/null && echo "PASS" || echo "FAIL (may be cgroup v1)"

echo "4. cpu.max enforced:"
sudo find /sys/fs/cgroup -name "cpu.max" 2>/dev/null | wc -l | xargs -I{} sh -c '[ {} -gt 0 ] && echo "PASS: {} cgroups with cpu.max" || echo "FAIL"'
```

---

## Lab 3: Orchestration Platforms (Kubernetes Scheduling, Pod Disruption Budgets)

### Objective

Verify Kubernetes scheduling decisions at the node level, implement and validate a Pod Disruption Budget under a simulated drain, test topology spread constraints, and inspect the scheduler's scoring logic via events. You will force scheduling failures and observe the system's recovery behavior.

### Background

The Kubernetes scheduler is a constraint-satisfaction solver. It runs in two phases: **filtering** (eliminates nodes that cannot host the pod) and **scoring** (ranks remaining nodes). PodDisruptionBudgets encode availability invariants as first-class API objects — the scheduler and the eviction API both respect them.

```mermaid
graph LR
    subgraph sched_pipeline ["Scheduler Pipeline"]
        subgraph filter_phase ["Filter Phase"]
            NR["NodeResourcesFit"]
            NA["NodeAffinity"]
            TA["TaintToleration"]
            TSC["TopologySpread"]
        end
        subgraph score_phase ["Score Phase"]
            LB["LeastAllocated"]
            BAL["BalancedAllocation"]
            IA["ImageLocality"]
        end
        subgraph bind_phase ["Bind Phase"]
            BIND["DefaultBinder\n(writes spec.nodeName)"]
        end
        POD["Unscheduled Pod\n(PodSpec)"] --> NR
        NR --> NA --> TA --> TSC
        TSC -->|"filtered nodes"| LB
        LB --> BAL --> IA
        IA -->|"highest score"| BIND
        BIND -->|"nodeName set"| KUBELET["kubelet on target node"]
    end
```

### Step 1: Deploy a High-Availability Application

```yaml
# ha-deployment.yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: ha-lab
  labels:
    lab: "03"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ha-app
  namespace: ha-lab
spec:
  replicas: 4
  selector:
    matchLabels:
      app: ha-app
  template:
    metadata:
      labels:
        app: ha-app
        version: "stable"
    spec:
      # Topology Spread Constraints: spread across zones and nodes
      # This is the production pattern for HA — not just replicas > 1
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: ha-app
        - maxSkew: 1
          # Requires zone labels on nodes; skip on single-node clusters
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: ha-app
      # Pod Anti-Affinity: hard rule — no two pods on same node
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: ha-app
                topologyKey: kubernetes.io/hostname
      containers:
        - name: app
          image: nginx:1.25.3-alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "32Mi"
            limits:
              cpu: "200m"
              memory: "64Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 3
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ha-app-svc
  namespace: ha-lab
spec:
  selector:
    app: ha-app
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
```

```bash
kubectl apply -f ha-deployment.yaml
kubectl -n ha-lab rollout status deployment/ha-app --timeout=120s

# Verify spread across nodes
kubectl -n ha-lab get pods -o wide
```

### Step 2: Implement and Test a Pod Disruption Budget

```yaml
# pdb.yaml
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ha-app-pdb
  namespace: ha-lab
spec:
  # minAvailable: the minimum number of pods that must be RUNNING
  # during any voluntary disruption (drain, eviction, rolling update)
  # Setting to 75% of replicas (3/4) means at most 1 pod can be disrupted at once
  minAvailable: 3
  selector:
    matchLabels:
      app: ha-app
```

```bash
kubectl apply -f pdb.yaml

# Inspect PDB status — this shows current disruption budget
kubectl -n ha-lab get pdb ha-app-pdb -o yaml

# Key fields in the output:
# status.currentHealthy:   pods currently healthy
# status.desiredHealthy:   minimum required (minAvailable)
# status.disruptionsAllowed: how many pods can be disrupted right now
# status.expectedPods:    total pods selected by the PDB

kubectl -n ha-lab describe pdb ha-app-pdb
```

### Step 3: Simulate a Node Drain Against the PDB

```bash
# Identify nodes running ha-app pods
kubectl -n ha-lab get pods -o wide | awk 'NR>1 {print $7}' | sort -u

# Pick a node that has an ha-app pod
TARGET_NODE=$(kubectl -n ha-lab get pods -o wide | awk 'NR==2 {print $7}')
echo "Draining node: $TARGET_NODE"

# Drain with --dry-run first — observe what WOULD be evicted
kubectl drain "$TARGET_NODE" \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --dry-run=client \
  --pod-selector='app=ha-app'

# Actual drain — the PDB will block eviction if it would violate minAvailable
# In another terminal, watch pod events:
# kubectl -n ha-lab get pods -w
kubectl drain "$TARGET_NODE" \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --timeout=120s

# Observe: eviction proceeds one pod at a time, respecting PDB
# If the PDB would be violated, the drain waits until a pod is rescheduled

# Check disruption events
kubectl -n ha-lab get events --sort-by='.lastTimestamp' | grep -i "disrupt\|evict"

# Uncordon the node after the lab
kubectl uncordon "$TARGET_NODE"
```

### Step 4: Force a Scheduling Failure and Observe Events

```yaml
# unschedulable-pod.yaml
# This pod intentionally cannot be scheduled — for diagnostic purposes
apiVersion: v1
kind: Pod
metadata:
  name: unschedulable-pod
  namespace: ha-lab
spec:
  containers:
    - name: app
      image: nginx:1.25.3-alpine
      resources:
        requests:
          # Request more memory than any node has — will trigger Unschedulable
          memory: "999999Gi"
          cpu: "1m"
  # Also add a toleration for a taint that doesn't exist
  tolerations:
    - key: "dedicated"
      operator: "Equal"
      value: "nonexistent-pool"
      effect: "NoSchedule"
```

```bash
kubectl apply -f unschedulable-pod.yaml

# Watch the pod enter Pending state
kubectl -n ha-lab get pod unschedulable-pod -w &
WATCH_PID=$!
sleep 15
kill $WATCH_PID

# Inspect scheduler events — this reveals WHICH filter rejected it
kubectl -n ha-lab describe pod unschedulable-pod | grep -A 20 "Events:"

# Expected output shows InsufficientMemory from NodeResourcesFit filter
# The message contains the node name and the specific rejection reason

# Check scheduler logs if you have access
kubectl -n kube-system logs -l component=kube-scheduler --tail=30 | grep unschedulable-pod

# Clean up
kubectl -n ha-lab delete pod unschedulable-pod
```

### Step 5: Verify Topology Spread in Action

```bash
# Display current pod distribution across nodes
echo "=== Pod distribution by node ==="
kubectl -n ha-lab get pods -o wide | awk 'NR>1 {nodes[$7]++} END {for (n in nodes) print n": "nodes[n]" pods"}'

# Scale up and observe spread enforcement
kubectl -n ha-lab scale deployment ha-app --replicas=6
kubectl -n ha-lab rollout status deployment/ha-app --timeout=60s

echo "=== Pod distribution after scale-up ==="
kubectl -n ha-lab get pods -o wide | awk 'NR>1 {nodes[$7]++} END {for (n in nodes) print n": "nodes[n]" pods"}'

# Verify maxSkew=1 is maintained: no node should have more than 1 extra pod vs others
# If you have 3 nodes and 6 pods, each node should have exactly 2
```

### Verification Checklist

```bash
echo "=== Lab 3 Verification ==="

echo "1. PDB status:"
kubectl -n ha-lab get pdb ha-app-pdb -o jsonpath='{.status.currentHealthy}' | xargs -I{} sh -c '[ {} -ge 3 ] && echo "PASS: {} healthy pods" || echo "WARN: {} healthy pods"'

echo "2. disruptionsAllowed:"
kubectl -n ha-lab get pdb ha-app-pdb -o jsonpath='{.status.disruptionsAllowed}'

echo "3. Pod spread across nodes:"
kubectl -n ha-lab get pods -o wide | awk 'NR>1 {nodes[$7]++} END {for (n in nodes) print "Node "n": "nodes[n]" pods"}'

echo "4. No pods in Pending state:"
kubectl -n ha-lab get pods | grep -c Pending | xargs -I{} sh -c '[ {} -eq 0 ] && echo "PASS" || echo "WARN: {} pods pending"'
```

---

## Lab 4: Service Meshes (Envoy Data Plane, Istio Traffic Routing)

### Objective

Deploy Istio, verify sidecar injection, inspect Envoy's xDS configuration state, implement traffic splitting for a canary deployment, configure circuit breaking via an OutlierDetection policy, and analyze Envoy's access log format to confirm routing decisions.

### Background

A service mesh interposes a proxy (Envoy) on every network path. The proxy is configured dynamically via the **xDS API** — a set of gRPC streaming APIs: **LDS** (listener discovery), **RDS** (route discovery), **CDS** (cluster discovery), and **EDS** (endpoint discovery). Understanding the xDS state is the core skill for mesh debugging.

```mermaid
graph TD
    subgraph mesh_control_plane ["Control Plane (Istiod)"]
        PILOT["Pilot\n(xDS server)"]
        CITADEL["Citadel\n(mTLS cert mgmt)"]
        GALLEY["Galley\n(config validation)"]
    end
    subgraph mesh_data_plane ["Data Plane"]
        subgraph pod_a ["Pod A"]
            APP_A["App Container"]
            PROXY_A["Envoy Sidecar\n(port 15001)"]
        end
        subgraph pod_b_stable ["Pod B - stable (v1)"]
            APP_B1["App Container"]
            PROXY_B1["Envoy Sidecar"]
        end
        subgraph pod_b_canary ["Pod B - canary (v2)"]
            APP_B2["App Container"]
            PROXY_B2["Envoy Sidecar"]
        end
    end
    PILOT -->|"LDS/RDS/CDS/EDS"| PROXY_A
    PILOT -->|"LDS/RDS/CDS/EDS"| PROXY_B1
    PILOT -->|"LDS/RDS/CDS/EDS"| PROXY_B2
    CITADEL -->|"mTLS certs"| PROXY_A
    APP_A -->|"all egress"| PROXY_A
    PROXY_A -->|"90% weight"| PROXY_B1
    PROXY_A -->|"10% weight"| PROXY_B2
```

### Step 1: Install Istio (Minimal Profile)

```bash
# Download istioctl
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
export PATH="$PWD/istio-1.20.0/bin:$PATH"
istioctl version

# Install with the minimal profile to understand what each component does
# demo profile adds extras; minimal is what production teams strip down to
istioctl install --set profile=minimal -y

# Verify control plane is running
kubectl -n istio-system get pods
kubectl -n istio-system get svc

# Confirm istiod is healthy
istioctl verify-install
```

### Step 2: Deploy the Service Mesh Application

```yaml
# mesh-app.yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: mesh-lab
  labels:
    # This label triggers automatic sidecar injection for all pods in namespace
    istio-injection: enabled
    lab: "04"
---
# Stable version (v1)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-v1
  namespace: mesh-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
      version: v1
  template:
    metadata:
      labels:
        app: backend
        version: v1
    spec:
      containers:
        - name: backend
          image: kennethreitz/httpbin:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
---
# Canary version (v2)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-v2
  namespace: mesh-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
      version: v2
  template:
    metadata:
      labels:
        app: backend
        version: v2
    spec:
      containers:
        - name: backend
          image: kennethreitz/httpbin:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-svc
  namespace: mesh-lab
spec:
  selector:
    # Selects BOTH v1 and v2 — Istio's DestinationRule splits them
    app: backend
  ports:
    - name: http
      port: 80
      targetPort: 80
---
# Client pod for generating traffic
apiVersion: v1
kind: Pod
metadata:
  name: client
  namespace: mesh-lab
  labels:
    app: client
spec:
  containers:
    - name: client
      image: curlimages/curl:8.5.0
      command: ["sleep", "3600"]
      resources:
        requests:
          cpu: "10m"
          memory: "16Mi"
```

```bash
kubectl apply -f mesh-app.yaml
kubectl -n mesh-lab rollout status deployment/backend-v1 --timeout=120s
kubectl -n mesh-lab rollout status deployment/backend-v2 --timeout=120s

# Verify sidecar injection — each pod should have 2/2 containers (app + envoy)
kubectl -n mesh-lab get pods
# Expected: READY column shows 2/2 for each pod
```

### Step 3: Implement Traffic Splitting (90/10 Canary)

```yaml
# traffic-split.yaml
---
# DestinationRule: defines subsets based on labels
# This is the mesh's way of grouping endpoints into named subsets
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: backend-dr
  namespace: mesh-lab
spec:
  host: backend-svc
  # Traffic policy applies to all subsets unless overridden
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: UPGRADE
        idleTimeout: 90s
    # OutlierDetection: circuit breaker configuration
    # Ejects endpoints that return 5xx errors
    outlierDetection:
      consecutiveGatewayErrors: 5
      consecutive5xxErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
---
# VirtualService: defines routing rules
# Weights here are enforced by Envoy, not by DNS or service selectors
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: backend-vs
  namespace: mesh-lab
spec:
  hosts:
    - backend-svc
  http:
    # Header-based routing: allow testers to force v2 traffic
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: backend-svc
            subset: v2
          weight: 100
    # Default: 90% stable, 10% canary
    - route:
        - destination:
            host: backend-svc
            subset: v1
          weight: 90
        - destination:
            host: backend-svc
            subset: v2
          weight: 10
      # Retry policy: retry on 5xx, do not retry on 4xx
      retries:
        attempts: 3
        perTryTimeout: 5s
        retryOn: "5xx,reset,connect-failure,retriable-4xx"
      # Timeout for the entire request (all retries included)
      timeout: 15s
```

```bash
kubectl apply -f traffic-split.yaml

# Verify the VirtualService is accepted
kubectl -n mesh-lab get vs backend-vs -o yaml | grep -A 10 "status:"

# Generate traffic and observe distribution
kubectl -n mesh-lab exec client -- sh -c '
  v1=0; v2=0
  for i in $(seq 1 100); do
    # httpbin /headers returns the pod hostname in Server header
    result=$(curl -s -o /dev/null -w "%{http_code}" http://backend-svc/status/200)
    echo -n "."
  done
  echo ""
  echo "Traffic generation complete"
'
```

### Step 4: Inspect Envoy xDS Configuration State

```bash
# Get a sidecar pod
CLIENT_POD="client"
BACKEND_POD=$(kubectl -n mesh-lab get pods -l app=backend,version=v1 -o jsonpath='{.items[0].metadata.name}')

# istioctl proxy-config is the primary tool for inspecting xDS state
# It queries the Envoy admin API (port 15000) through istio's tooling

echo "=== Listeners (LDS) ==="
# Listeners are the entry points into Envoy's filter chain
# Port 15006 = inbound (all inbound traffic intercepted by iptables)
# Port 15001 = outbound virtual listener
istioctl proxy-config listeners "$CLIENT_POD.mesh-lab" --port 15001

echo "=== Routes (RDS) — outbound routes from client ==="
# Routes map request attributes (host, path, headers) to clusters
istioctl proxy-config routes "$CLIENT_POD.mesh-lab" --name "80"

echo "=== Clusters (CDS) — backend service clusters ==="
# Clusters represent upstream services
# Istio creates one cluster per subset: backend-svc|80|v1|mesh-lab, |v2|...
istioctl proxy-config clusters "$CLIENT_POD.mesh-lab" | grep backend

echo "=== Endpoints (EDS) — actual pod IPs in each cluster ==="
# Endpoints are the actual IP:port pairs of healthy pods
istioctl proxy-config endpoints "$CLIENT_POD.mesh-lab" | grep backend

echo "=== Full xDS dump for deep inspection ==="
# This is the raw xDS state — useful for debugging misconfigured routing
istioctl proxy-config all "$CLIENT_POD.mesh-lab" -o json | \
  python3 -m json.tool | grep -A 5 '"name"' | head -60
```

### Step 5: Inspect Envoy Filter Chain

```bash
# Inspect the filter chain on the backend pod's inbound listener
# This reveals mTLS enforcement, header manipulation, and observability filters
echo "=== Backend inbound listener filter chain ==="
istioctl proxy-config listeners "$BACKEND_POD.mesh-lab" --port 80 -o json | \
  python3 -c "
import sys, json
listeners = json.load(sys.stdin)
for l in listeners:
    for fc in l.get('filterChains', []):
        print('--- Filter Chain ---')
        for f in fc.get('filters', []):
            print(f'  Filter: {f[\"name\"]}')
        tls = fc.get('transportSocket', {})
        if tls:
            print(f'  TLS: {tls.get(\"name\",\"none\")}')
"

# Verify mTLS is enforced (PeerAuthentication)
echo "=== Check mTLS mode ==="
istioctl authn tls-check "$CLIENT_POD.mesh-lab" backend-svc.mesh-lab.svc.cluster.local

# Inspect Envoy access log for routing decisions
# Envoy access logs confirm which cluster/subset each request hit
kubectl -n mesh-lab logs "$CLIENT_POD" -c istio-proxy --tail=20
```

### Step 6: Trigger and Observe Circuit Breaker (OutlierDetection)

```bash
# Generate errors from one endpoint to trigger outlier detection
# The OutlierDetection policy ejects hosts that return consecutive errors

# First, observe healthy endpoint state
istioctl proxy-config endpoints "$CLIENT_POD.mesh-lab" | grep backend

# Generate controlled traffic with the canary header to force v2
kubectl -n mesh-lab exec client -- sh -c '
  for i in $(seq 1 20); do
    curl -s -H "x-canary: true" -o /dev/null -w "v2 response: %{http_code}\n" \
      http://backend-svc/status/500
    sleep 0.5
  done
'

# After consecutive errors, check if the endpoint is ejected
# ejectedHosts field in the cluster status indicates circuit-breaker activation
kubectl -n mesh-lab exec client -- \
  curl -s http://localhost:15000/stats | grep -E "outlier|ejected" | grep backend

# Check via istioctl
istioctl proxy-config endpoints "$CLIENT_POD.mesh-lab" | grep backend
# ejected endpoints show as UNHEALTHY or have a non-zero ejection count
```

### Verification Checklist

```bash
echo "=== Lab 4 Verification ==="

echo "1. Sidecar injection active:"
kubectl -n mesh-lab get pods -o jsonpath='{range .items[*]}{.metadata.name}{" ready="}{.status.containerStatuses[*].ready}{"\n"}{end}'

echo "2. VirtualService accepted:"
kubectl -n mesh-lab get vs backend-vs -o jsonpath='{.status.conditions[0].status}' 2>/dev/null || echo "Check istio status"

echo "3. DestinationRule subsets defined:"
kubectl -n mesh-lab get dr backend-dr -o jsonpath='{.spec.subsets[*].name}'

echo "4. Envoy clusters for both subsets:"
istioctl proxy-config clusters "$CLIENT_POD.mesh-lab" 2>/dev/null | grep -c "backend" | xargs echo "backend clusters:"

echo "5. mTLS check:"
istioctl authn tls-check "$CLIENT_POD.mesh-lab" backend-svc.mesh-lab.svc.cluster.local 2>/dev/null | grep -E "STATUS|ok|mTLS"
```

---

## Lab 5: Serverless Architectures (Knative, Event-Driven Functions)

### Objective

Deploy Knative Serving and Eventing, verify scale-to-zero behavior by watching the activator and queue-proxy components, configure concurrency and autoscaling parameters, deploy an event source with a CloudEvents trigger, and verify the event delivery chain end-to-end.

### Background

Knative Serving extends Kubernetes with **Revision**-based immutable deployments and a request-driven autoscaler (KPA). When no requests arrive, pods scale to zero and the **Activator** buffers incoming requests while cold-starting a pod. The Eventing component implements the **CloudEvents** specification and provides a broker/trigger model for event routing.

```mermaid
graph TD
    subgraph knative_serving ["Knative Serving"]
        subgraph autoscaling ["Autoscaling Path"]
            QUEUE["Queue Proxy\n(port 8012 metrics)"]
            ACTIVATOR["Activator\n(buffers at scale=0)"]
            KPA["KPA / HPA\n(autoscaler)"]
        end
        subgraph serving ["Revision Path"]
            INGRESS["Kourier / Istio Ingress"]
            REV["Revision\n(immutable pod template)"]
            CONTAINER["User Container"]
        end
    end
    subgraph knative_eventing ["Knative Eventing"]
        subgraph event_plane ["Event Plane"]
            SOURCE["EventSource\n(PingSource / ApiServerSource)"]
            BROKER["Broker\n(InMemoryChannel)"]
            TRIGGER["Trigger\n(filter + subscriber)"]
            SINK["Knative Service\n(event handler)"]
        end
    end
    HTTP_REQ["Inbound HTTP"] --> INGRESS
    INGRESS -->|"pods > 0"| CONTAINER
    INGRESS -->|"pods = 0"| ACTIVATOR
    ACTIVATOR -->|"cold start signal"| KPA
    ACTIVATOR -->|"forward after start"| CONTAINER
    QUEUE -->|metrics| KPA
    KPA -->|"scale replicas"| REV
    SOURCE -->|CloudEvent| BROKER
    BROKER -->|"matches filter"| TRIGGER
    TRIGGER -->|deliver| SINK
```

### Step 1: Install Knative Serving

```bash
# Install Knative Serving CRDs
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-crds.yaml

# Install Knative Serving core components
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-core.yaml

# Install Kourier as the network layer (lightweight alternative to Istio ingress)
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.12.0/kourier.yaml

# Configure Knative to use Kourier
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Verify installation
kubectl -n knative-serving get pods
kubectl -n kourier-system get pods

# Wait for all components
kubectl -n knative-serving wait --for=condition=Ready pod --all --timeout=180s
```

### Step 2: Deploy a Knative Service with Scale-to-Zero

```yaml
# knative-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: event-handler
  namespace: default
  labels:
    lab: "05"
  annotations:
    # serving.knative.dev/rollout-duration controls canary rollout time
    serving.knative.dev/rolloutDuration: "10s"
spec:
  template:
    metadata:
      annotations:
        # KPA autoscaling annotations — these are the core knobs
        # Target: scale when avg concurrent requests per pod exceeds this
        autoscaling.knative.dev/target: "10"
        # Min/max scale: 0 = scale to zero; adjust for prod
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "5"
        # Scale-to-zero grace period: how long to wait before scaling to zero
        autoscaling.knative.dev/scaleToZeroPodRetentionPeriod: "1m"
        # Metric: concurrency (requests in-flight) vs rps (requests per second)
        autoscaling.knative.dev/metric: "concurrency"
        # Scale-down delay: prevent thrashing
        autoscaling.knative.dev/scaleDownDelay: "30s"
      labels:
        app: event-handler
    spec:
      # containerConcurrency: max concurrent requests per container
      # 0 = unlimited; setting this enables KPA to calculate pod count
      containerConcurrency: 10
      # timeoutSeconds: request timeout enforced by queue-proxy
      timeoutSeconds: 60
      containers:
        - name: user-container
          image: gcr.io/knative-samples/helloworld-go:v1.0.0
          ports:
            - name: h2c
              containerPort: 8080
          env:
            - name: TARGET
              value: "CloudNative Lab 5"
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "500m"
              memory: "256Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 8080
            initialDelaySeconds: 3
            periodSeconds: 5
```

```bash
kubectl apply -f knative-service.yaml

# Watch the Service reach Ready state
kubectl get ksvc event-handler -w &
WATCH_PID=$!
sleep 30
kill $WATCH_PID

# Inspect the generated Kubernetes objects
# Knative creates: Revision, Route, Configuration, Deployment, Service
kubectl get revision,route,configuration -l serving.knative.dev/service=event-handler

# Get the URL
kubectl get ksvc event-handler -o jsonpath='{.status.url}'
```

### Step 3: Observe Scale-to-Zero

```bash
# After deploy, watch the pod count drop to zero (takes ~90s with defaults)
echo "=== Watching pods scale to zero ==="
kubectl get pods -l serving.knative.dev/service=event-handler -w &
WATCH_PID=$!

# Wait for scale-to-zero (observe pod reaching Terminating then disappearing)
sleep 120
kill $WATCH_PID

# Confirm zero pods running
kubectl get pods -l serving.knative.dev/service=event-handler

# Get the service URL
SVC_URL=$(kubectl get ksvc event-handler -o jsonpath='{.status.url}')
echo "Service URL: $SVC_URL"

# Send a request — this triggers cold start via Activator
# Measure cold start latency
echo "=== Cold start request (pod was at zero) ==="
time curl -f "$SVC_URL" 2>&1 || echo "Note: DNS may need /etc/hosts if no external LB"

# Observe scale-up event
kubectl get pods -l serving.knative.dev/service=event-handler -w &
WATCH_PID=$!

# Send traffic burst to trigger scale-up
for i in $(seq 1 30); do curl -s "$SVC_URL" > /dev/null & done
wait
sleep 10
kill $WATCH_PID 2>/dev/null
```

### Step 4: Inspect the Queue Proxy and Activator

```bash
# The queue-proxy sidecar is injected by Knative into every revision pod
# It sits in-line with traffic and reports metrics to the autoscaler
HANDLER_POD=$(kubectl get pods -l serving.knative.dev/service=event-handler -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -n "$HANDLER_POD" ]; then
  echo "=== Queue-proxy containers in pod ==="
  kubectl get pod "$HANDLER_POD" -o jsonpath='{.spec.containers[*].name}'

  echo ""
  echo "=== Queue-proxy metrics endpoint ==="
  # Port 9090 exposes Prometheus metrics including queue depth and concurrency
  kubectl exec "$HANDLER_POD" -c queue-proxy -- \
    wget -q -O - http://localhost:9090/metrics 2>/dev/null | \
    grep -E "queue_depth|concurrent_requests|request_count" | head -20

  echo "=== Queue-proxy admin endpoint ==="
  # Port 8022 is the queue-proxy's admin port
  kubectl exec "$HANDLER_POD" -c queue-proxy -- \
    wget -q -O - http://localhost:8022/ 2>/dev/null | head -20
fi

# Inspect activator component metrics
echo "=== Activator pods ==="
kubectl -n knative-serving get pods -l app=activator

ACTIVATOR_POD=$(kubectl -n knative-serving get pods -l app=activator -o jsonpath='{.items[0].metadata.name}')

echo "=== Activator logs (last 20 lines) ==="
kubectl -n knative-serving logs "$ACTIVATOR_POD" --tail=20 | grep -v "^$"
```

### Step 5: Deploy Knative Eventing with CloudEvents

```bash
# Install Knative Eventing
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.12.0/eventing-crds.yaml
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.12.0/eventing-core.yaml

# Install in-memory channel (suitable for labs; use Kafka/NATS in production)
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.12.0/in-memory-channel.yaml

# Install MT-Channel-based Broker
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.12.0/mt-channel-broker.yaml

kubectl -n knative-eventing wait --for=condition=Ready pod --all --timeout=180s
```

```yaml
# eventing-pipeline.yaml
---
apiVersion: eventing.knative.dev/v1
kind: Broker
metadata:
  name: default-broker
  namespace: default
  annotations:
    eventing.knative.dev/broker.class: MTChannelBasedBroker
spec:
  config:
    apiVersion: v1
    kind: ConfigMap
    name: config-br-default-channel
    namespace: knative-eventing
  delivery:
    # Dead letter sink: events that fail delivery go here
    deadLetterSink:
      ref:
        apiVersion: v1
        kind: Service
        name: dead-letter-sink
    # Retry configuration for failed deliveries
    backoffDelay: "PT2S"
    backoffPolicy: exponential
    timeout: "PT10S"
    retry: 3
---
# PingSource: emits a CloudEvent on a schedule (like cron)
apiVersion: sources.knative.dev/v1
kind: PingSource
metadata:
  name: heartbeat-source
  namespace: default
spec:
  # Every 30 seconds, emit a CloudEvent
  schedule: "*/1 * * * *"
  contentType: "application/json"
  data: '{"message": "heartbeat", "source": "ping-source", "lab": "05"}'
  sink:
    ref:
      apiVersion: eventing.knative.dev/v1
      kind: Broker
      name: default-broker
---
# Trigger: routes events from broker to subscriber based on filter
# Only events with type "dev.knative.sources.ping" reach the event-handler
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  name: ping-trigger
  namespace: default
spec:
  broker: default-broker
  filter:
    attributes:
      # CloudEvents attribute filtering
      type: dev.knative.sources.ping
      # source filtering would go here if needed
  subscriber:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: event-handler
---
# Simple dead letter sink service
apiVersion: v1
kind: Service
metadata:
  name: dead-letter-sink
  namespace: default
spec:
  selector:
    app: event-handler
  ports:
    - port: 80
      targetPort: 8080
```

```bash
kubectl apply -f eventing-pipeline.yaml

# Verify broker is ready
kubectl get broker default-broker -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'

# Verify trigger is ready
kubectl get trigger ping-trigger -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'

# Watch events arrive at the handler (wait for PingSource to fire)
echo "=== Waiting for first event (up to 90s) ==="
kubectl get pods -l serving.knative.dev/service=event-handler -w &
WATCH_PID=$!
sleep 90
kill $WATCH_PID 2>/dev/null

# Check handler logs for CloudEvent receipt
HANDLER_POD=$(kubectl get pods -l serving.knative.dev/service=event-handler -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$HANDLER_POD" ]; then
  kubectl logs "$HANDLER_POD" -c user-container --tail=20
fi

# Inspect CloudEvent metadata on the broker
kubectl get broker default-broker -o yaml | grep -A 10 "status:"
```

### Verification Checklist

```bash
echo "=== Lab 5 Verification ==="

echo "1. Knative Serving components:"
kubectl -n knative-serving get pods -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.phase}{"\n"}{end}'

echo "2. Knative Service ready:"
kubectl get ksvc event-handler -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'

echo "3. Latest revision ready:"
kubectl get revision -l serving.knative.dev/service=event-handler -o jsonpath='{.items[-1:].status.conditions[?(@.type=="Ready")].status}'

echo "4. Broker ready:"
kubectl get broker default-broker -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'

echo "5. Trigger ready:"
kubectl get trigger ping-trigger -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'

echo "6. PingSource ready:"
kubectl get pingsource heartbeat-source -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

---

## Lab 6: Advanced Cloud Native Practices (GitOps, ArgoCD, OpenTelemetry)

### Objective

Install ArgoCD and synchronize an application from a Git repository, verify reconciliation loops and drift detection, deploy the OpenTelemetry Collector as a DaemonSet, instrument a service to emit traces, and verify the complete trace pipeline from application through collector to a backend. You will understand how GitOps enforces desired state and how distributed traces are assembled from spans.

### Background

GitOps treats Git as the single source of truth for desired system state. The GitOps controller (ArgoCD) continuously compares **desired state** (Git) against **actual state** (cluster) and either alerts on drift or reconciles it. OpenTelemetry provides a vendor-neutral instrumentation standard — the **Collector** is the deployment-side aggregation and routing component.

```mermaid
graph TD
    subgraph gitops_loop ["GitOps Reconciliation Loop"]
        subgraph git_plane ["Source of Truth"]
            GIT["Git Repository\n(manifests, Helm charts)"]
            PR["Pull Request\n(change proposal)"]
        end
        subgraph argocd_plane ["ArgoCD Control Plane"]
            REPO_SERVER["Repo Server\n(renders manifests)"]
            APP_CONTROLLER["Application Controller\n(diff + sync)"]
            API_SERVER["API Server\n(RBAC + webhooks)"]
        end
        subgraph cluster_plane ["Cluster (Actual State)"]
            K8S["Kubernetes API"]
            WORKLOADS["Workloads"]
        end
        PR -->|merge| GIT
        GIT -->|"poll every 3min\nor webhook"| REPO_SERVER
        REPO_SERVER -->|"rendered manifests"| APP_CONTROLLER
        APP_CONTROLLER -->|"kubectl diff"| K8S
        K8S -->|"actual state"| APP_CONTROLLER
        APP_CONTROLLER -->|"OutOfSync alert\nor auto-sync"| K8S
        K8S -->|deploy| WORKLOADS
    end
    subgraph otel_pipeline ["OpenTelemetry Pipeline"]
        subgraph app_layer ["Application Layer"]
            APP_INST["Instrumented App\n(OTLP SDK)"]
        end
        subgraph collector_layer ["Collector Layer"]
            OTEL_COL["OTel Collector\n(DaemonSet)"]
            subgraph pipeline ["Collector Pipeline"]
                RECV["Receivers\n(OTLP, Jaeger, Zipkin)"]
                PROC["Processors\n(batch, memory_limiter,\nresource, sampling)"]
                EXP["Exporters\n(Jaeger, OTLP, Prometheus)"]
            end
        end
        subgraph backend_layer ["Observability Backends"]
            JAEGER["Jaeger\n(trace storage + UI)"]
            PROM["Prometheus\n(metrics)"]
        end
        APP_INST -->|"OTLP gRPC/HTTP"| OTEL_COL
        RECV --> PROC --> EXP
        EXP -->|traces| JAEGER
        EXP -->|metrics| PROM
    end
```

### Step 1: Install ArgoCD

```bash
# Create namespace and install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.9.3/manifests/install.yaml

# Wait for all pods to be ready
kubectl -n argocd wait --for=condition=Ready pod --all --timeout=300s
kubectl -n argocd get pods

# Get the initial admin password (auto-generated, stored in a secret)
ARGOCD_PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d)
echo "ArgoCD admin password: $ARGOCD_PASS"

# Port-forward to access the UI (or use LoadBalancer in production)
kubectl -n argocd port-forward svc/argocd-server 8080:443 &
PF_PID=$!
echo "ArgoCD UI: https://localhost:8080 (admin / $ARGOCD_PASS)"

# CLI login
argocd login localhost:8080 \
  --username admin \
  --password "$ARGOCD_PASS" \
  --insecure
```

### Step 2: Deploy an Application via ArgoCD (GitOps Pattern)

```yaml
# argocd-application.yaml
# This Application CRD is itself stored in Git — the "app of apps" pattern
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cloud-native-lab
  namespace: argocd
  # Finalizer ensures ArgoCD resources are cleaned up when app is deleted
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    # Using the official ArgoCD example repository for lab reproducibility
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: gitops-lab
  syncPolicy:
    # Automated sync: ArgoCD reconciles drift automatically
    automated:
      # prune: delete resources that exist in cluster but NOT in Git
      prune: true
      # selfHeal: re-apply if someone manually changes cluster state
      selfHeal: true
      # allowEmpty: prevent accidental deletion of all resources
      allowEmpty: false
    syncOptions:
      # Create namespace if it doesn't exist
      - CreateNamespace=true
      # Apply resources with server-side apply (better conflict detection)
      - ServerSideApply=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

```bash
kubectl apply -f argocd-application.yaml

# Watch sync status
argocd app get cloud-native-lab
argocd app wait cloud-native-lab --sync --health --timeout 120

# Verify application status
argocd app list
kubectl -n gitops-lab get all
```

### Step 3: Verify Drift Detection (GitOps Core Behavior)

```bash
# Simulate configuration drift: manually scale the deployment
# (This is what happens when someone runs kubectl in production without GitOps approval)
kubectl -n gitops-lab scale deployment guestbook-ui --replicas=5

# Immediately check ArgoCD status — it will detect OutOfSync
sleep 10
argocd app get cloud-native-lab | grep -E "Status|Health|Sync"

# With selfHeal=true, ArgoCD should revert this within ~3 minutes
# Watch the reconciliation:
kubectl -n gitops-lab get deployment guestbook-ui -w &
WATCH_PID=$!

echo "Waiting for ArgoCD to self-heal (reconcile back to 1 replica)..."
sleep 180
kill $WATCH_PID 2>/dev/null

# Verify drift was corrected
kubectl -n gitops-lab get deployment guestbook-ui -o jsonpath='{.spec.replicas}'
# Should be 1 (the value in Git), not 5

# Inspect sync history — shows each reconciliation event
argocd app history cloud-native-lab
```

### Step 4: Deploy OpenTelemetry Collector as DaemonSet

```yaml
# otel-collector.yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: observability
  labels:
    lab: "06"
---
# ConfigMap containing the Collector's pipeline configuration
# This is the most important file for understanding OTel Collector behavior
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: observability
data:
  config.yaml: |
    # Receivers: how the collector ingests telemetry data
    receivers:
      # OTLP receiver accepts traces, metrics, and logs
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
            # CORS for browser-based instrumentation
            cors:
              allowed_origins:
                - "http://*"
                - "https://*"
      # Collect the collector's own metrics for self-monitoring
      prometheus:
        config:
          scrape_configs:
            - job_name: otel-collector
              scrape_interval: 10s
              static_configs:
                - targets: ['0.0.0.0:8888']

    # Processors: transform data between receivers and exporters
    processors:
      # memory_limiter: prevent OOM by dropping data under memory pressure
      # Place this FIRST in every pipeline — it's a circuit breaker
      memory_limiter:
        check_interval: 1s
        limit_mib: 400
        spike_limit_mib: 128
      # batch: group spans into batches for efficient export
      batch:
        timeout: 5s
        send_batch_size: 1024
        send_batch_max_size: 2048
      # resource: add k8s metadata to all telemetry
      resource:
        attributes:
          - key: deployment.environment
            value: "lab"
            action: upsert
          - key: k8s.cluster.name
            value: "cloud-native-lab"
            action: upsert
      # Probabilistic tail sampling — keep 100% of error traces, 10% of success
      # Note: tail sampling requires all spans of a trace to arrive at the same collector
      # For DaemonSet deployments, use a Gateway collector for tail sampling
      probabilistic_sampler:
        sampling_percentage: 100  # Keep all for lab; tune in production

    # Exporters: where the collector sends processed data
    exporters:
      # OTLP exporter to Jaeger (Jaeger v1.35+ accepts OTLP natively)
      otlp/jaeger:
        endpoint: jaeger-collector.observability.svc.cluster.local:4317
        tls:
          insecure: true
      # Debug exporter: prints to stdout (useful for lab verification)
      debug:
        verbosity: detailed
        sampling_initial: 2
        sampling_thereafter: 500
      # Prometheus exporter: exposes metrics at /metrics
      prometheus:
        endpoint: "0.0.0.0:8889"
        namespace: otel

    # Service: assembles receivers, processors, exporters into named pipelines
    service:
      telemetry:
        logs:
          level: "info"
        metrics:
          address: 0.0.0.0:8888
      pipelines:
        traces:
          receivers: [otlp]
          # Order matters: memory_limiter first, batch last before export
          processors: [memory_limiter, resource, probabilistic_sampler, batch]
          exporters: [otlp/jaeger, debug]
        metrics:
          receivers: [otlp, prometheus]
          processors: [memory_limiter, batch]
          exporters: [prometheus]
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: otel-collector
  namespace: observability
  labels:
    app: otel-collector
spec:
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
      annotations:
        # Prevent Istio from intercepting collector's own traffic (avoid loops)
        traffic.sidecar.istio.io/excludeInboundPorts: "4317,4318"
        traffic.sidecar.istio.io/excludeOutboundPorts: "4317"
    spec:
      serviceAccountName: otel-collector
      tolerations:
        # Run on all nodes including control-plane
        - operator: Exists
      containers:
        - name: otel-collector
          image: otel/opentelemetry-collector-contrib:0.91.0
          args: ["--config=/etc/otelcol-contrib/config.yaml"]
          ports:
            - name: otlp-grpc
              containerPort: 4317
              protocol: TCP
            - name: otlp-http
              containerPort: 4318
              protocol: TCP
            - name: metrics
              containerPort: 8888
              protocol: TCP
            - name: prom-export
              containerPort: 8889
              protocol: TCP
          env:
            - name: K8S_NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
            - name: K8S_POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: K8S_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
          volumeMounts:
            - name: otel-config
              mountPath: /etc/otelcol-contrib/
          resources:
            requests:
              cpu: "100m"
              memory: "200Mi"
            limits:
              cpu: "500m"
              memory: "500Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 13133
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: 13133
            initialDelaySeconds: 10
            periodSeconds: 15
      volumes:
        - name: otel-config
          configMap:
            name: otel-collector-config
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: otel-collector
  namespace: observability
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: otel-collector
rules:
  - apiGroups: [""]
    resources: ["pods", "namespaces", "nodes"]
    verbs: ["get", "watch", "list"]
  - apiGroups: ["apps"]
    resources: ["replicasets"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: otel-collector
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: otel-collector
subjects:
  - kind: ServiceAccount
    name: otel-collector
    namespace: observability
---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
  namespace: observability
  labels:
    app: otel-collector
spec:
  selector:
    app: otel-collector
  ports:
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
      protocol: TCP
    - name: otlp-http
      port: 4318
      targetPort: 4318
      protocol: TCP
    - name: metrics
      port: 8888
      targetPort: 8888
    - name: prom-export
      port: 8889
      targetPort: 8889
```

```bash
kubectl apply -f otel-collector.yaml
kubectl -n observability rollout status daemonset/otel-collector --timeout=120s
kubectl -n observability get pods -l app=otel-collector -o wide
```

### Step 5: Deploy Jaeger for Trace Storage and Visualization

```yaml
# jaeger.yaml
# Jaeger all-in-one for lab use — use jaeger-operator + distributed storage in production
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
        - name: jaeger
          image: jaegertracing/all-in-one:1.52
          ports:
            - containerPort: 16686  # UI
            - containerPort: 4317   # OTLP gRPC
            - containerPort: 4318   # OTLP HTTP
            - containerPort: 14268  # Jaeger HTTP collector
          env:
            - name: COLLECTOR_OTLP_ENABLED
              value: "true"
            - name: SPAN_STORAGE_TYPE
              value: "memory"
          resources:
            requests:
              cpu: "100m"
              memory: "200Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger-collector
  namespace: observability
spec:
  selector:
    app: jaeger
  ports:
    - name: otlp-grpc
      port: 4317
      targetPort: 4317
    - name: otlp-http
      port: 4318
      targetPort: 4318
    - name: http
      port: 14268
      targetPort: 14268
---
apiVersion: v1
kind: Service
metadata:
  name: jaeger-query
  namespace: observability
spec:
  selector:
    app: jaeger
  ports:
    - name: ui
      port: 16686
      targetPort: 16686
  type: ClusterIP
```

```bash
kubectl apply -f jaeger.yaml
kubectl -n observability rollout status deployment/jaeger --timeout=120s
```

### Step 6: Deploy an Instrumented Service and Verify Traces

```yaml
# instrumented-app.yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: traced-app
  namespace: observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: traced-app
  template:
    metadata:
      labels:
        app: traced-app
    spec:
      containers:
        - name: app
          # OpenTelemetry demo application — pre-instrumented
          image: otel/opentelemetry-collector-contrib:0.91.0
          args:
            - "--config=/etc/otelcol-contrib/generator.yaml"
          env:
            # Point to the DaemonSet collector on the same node
            # In production, use the node's IP or a headless service
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://otel-collector.observability.svc.cluster.local:4317"
            - name: OTEL_SERVICE_NAME
              value: "traced-app"
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: "service.version=1.0.0,deployment.environment=lab"
            # SDK-level sampling: send all traces to collector,
            # let collector's tail sampler make final decisions
            - name: OTEL_TRACES_SAMPLER
              value: "parentbased_always_on"
          volumeMounts:
            - name: generator-config
              mountPath: /etc/otelcol-contrib/
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "128Mi"
      volumes:
        - name: generator-config
          configMap:
            name: trace-generator-config
---
# This ConfigMap makes the collector act as a trace generator for lab purposes
apiVersion: v1
kind: ConfigMap
metadata:
  name: trace-generator-config
  namespace: observability
data:
  generator.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: localhost:4317
    processors:
      batch: {}
    exporters:
      otlp:
        endpoint: otel-collector.observability.svc.cluster.local:4317
        tls:
          insecure: true
    extensions:
      health_check: {}
    service:
      extensions: [health_check]
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [otlp]
```

```bash
kubectl apply -f instrumented-app.yaml

# Generate a trace manually using the OTLP HTTP API
# This sends a minimal valid trace directly to the collector
COLLECTOR_SVC="otel-collector.observability.svc.cluster.local"

# From a pod inside the cluster, send a trace
kubectl -n observability run trace-gen --image=curlimages/curl:8.5.0 \
  --restart=Never \
  --rm \
  --attach \
  -- curl -s -X POST \
     -H "Content-Type: application/json" \
     http://otel-collector.observability.svc.cluster.local:4318/v1/traces \
     -d '{
       "resourceSpans": [{
         "resource": {
           "attributes": [{
             "key": "service.name",
             "value": {"stringValue": "lab-trace-generator"}
           }]
         },
         "scopeSpans": [{
           "scope": {"name": "lab-manual-trace"},
           "spans": [{
             "traceId": "a3c50d4a30e3ec94b8a2ef90dde7b92d",
             "spanId": "1b2a3c4d5e6f7a8b",
             "name": "lab-verification-span",
             "kind": 2,
             "startTimeUnixNano": "1704067200000000000",
             "endTimeUnixNano": "1704067200500000000",
             "attributes": [{
               "key": "lab.number",
               "value": {"intValue": "6"}
             }, {
               "key": "http.method",
               "value": {"stringValue": "GET"}
             }],
             "status": {"code": 1}
           }]
         }]
       }]
     }'
```

### Step 7: Verify the Trace Pipeline End-to-End

```bash
# Check collector received the trace (debug exporter writes to stdout)
COLLECTOR_POD=$(kubectl -n observability get pods -l app=otel-collector -o jsonpath='{.items[0].metadata.name}')

echo "=== Collector logs (trace receipt) ==="
kubectl -n observability logs "$COLLECTOR_POD" --tail=50 | \
  grep -E "ResourceSpans|ScopeSpans|Spans|lab-verification|trace"

# Check collector's internal metrics — spans received, exported, dropped
echo "=== Collector pipeline metrics ==="
kubectl -n observability exec "$COLLECTOR_POD" -- \
  wget -q -O - http://localhost:8888/metrics 2>/dev/null | \
  grep -E "otelcol_receiver_accepted|otelcol_exporter_sent|otelcol_processor_batch" | \
  grep -v "^#"

# Verify spans reached Jaeger
JAEGER_POD=$(kubectl -n observability get pods -l app=jaeger -o jsonpath='{.items[0].metadata.name}')

echo "=== Jaeger services (should contain lab-trace-generator) ==="
kubectl -n observability exec "$JAEGER_POD" -- \
  wget -q -O - "http://localhost:16686/api/services" 2>/dev/null | \
  python3 -m json.tool 2>/dev/null | grep -E "data|lab-trace"

echo "=== Traces in Jaeger ==="
kubectl -n observability exec "$JAEGER_POD" -- \
  wget -q -O - "http://localhost:16686/api/traces?service=lab-trace-generator&limit=5" 2>/dev/null | \
  python3 -m json.tool 2>/dev/null | grep -E "traceID|operationName|duration" | head -20

# Access Jaeger UI
echo "Port-forwarding Jaeger UI to localhost:16686"
kubectl -n observability port-forward svc/jaeger-query 16686:16686 &
echo "Open http://localhost:16686 and search for service: lab-trace-generator"
```

### Step 8: Inspect ArgoCD Reconciliation Metrics

```bash
# ArgoCD exposes Prometheus metrics — verify reconciliation loop health
ARGOCD_METRICS_POD=$(kubectl -n argocd get pods -l app.kubernetes.io/name=argocd-application-controller \
  -o jsonpath='{.items[0].metadata.name}')

echo "=== ArgoCD application controller metrics ==="
kubectl -n argocd exec "$ARGOCD_METRICS_POD" -- \
  wget -q -O - http://localhost:8082/metrics 2>/dev/null | \
  grep -E "argocd_app_info|argocd_app_sync_total|argocd_reconcile" | head -20

# Check application health and sync status via API
argocd app get cloud-native-lab --output json | \
  python3 -c "
import sys, json
app = json.load(sys.stdin)
status = app.get('status', {})
print('Health:', status.get('health', {}).get('status'))
print('Sync:', status.get('sync', {}).get('status'))
print('Revision:', status.get('sync', {}).get('revision', '')[:8])
print('Resources:', len(status.get('resources', [])))
"
```

### Final Verification Checklist

```bash
echo "========================================"
echo "=== Lab 6 Final Verification ==="
echo "========================================"

echo ""
echo "--- ArgoCD ---"
echo "ArgoCD pods running:"
kubectl -n argocd get pods --field-selector=status.phase=Running --no-headers | wc -l

echo "Application sync status:"
argocd app get cloud-native-lab -o json 2>/dev/null | \
  python3 -c "import sys,json; a=json.load(sys.stdin); print(a['status']['sync']['status'])" 2>/dev/null || \
  kubectl -n argocd get application cloud-native-lab -o jsonpath='{.status.sync.status}'

echo ""
echo "--- OpenTelemetry Collector ---"
echo "Collector pods per node:"
kubectl -n observability get pods -l app=otel-collector -o wide --no-headers | wc -l

echo "Spans accepted (receiver metric):"
COLLECTOR_POD=$(kubectl -n observability get pods -l app=otel-collector -o jsonpath='{.items[0].metadata.name}')
kubectl -n observability exec "$COLLECTOR_POD" -- \
  wget -q -O - http://localhost:8888/metrics 2>/dev/null | \
  grep 'otelcol_receiver_accepted_spans_total' | \
  grep -v '^#' | awk '{print "  "$0}'

echo ""
echo "--- Jaeger ---"
echo "Jaeger pod running:"
kubectl -n observability get pods -l app=jaeger --field-selector=status.phase=Running --no-headers | wc -l

echo ""
echo "--- End-to-End Trace Pipeline ---"
echo "Trace pipeline: App -> OTLP -> Collector -> Jaeger"
echo "Verify at: http://localhost:16686 (after port-forward)"
```

---

## Cross-Lab Integration Verification

This section ties all six labs together into a single observable system. Run after completing all individual labs.

```mermaid
graph LR
    subgraph integration ["Full Stack Integration Verification"]
        subgraph layer1 ["Layer 1: Twelve-Factor"]
            TF["twelve-factor ns\n(Factor III/IV/XI)"]
        end
        subgraph layer2 ["Layer 2: Container Runtime"]
            CT["containerd\ncrictl inspection"]
        end
        subgraph layer3 ["Layer 3: Orchestration"]
            K8S_HA["ha-lab ns\nPDB + Topology Spread"]
        end
        subgraph layer4 ["Layer 4: Service Mesh"]
            MESH["mesh-lab ns\nEnvoy xDS + mTLS"]
        end
        subgraph layer5 ["Layer 5: Serverless"]
            KN["Knative Serving\nscale-to-zero"]
        end
        subgraph layer6 ["Layer 6: GitOps + OTel"]
            GITOPS["ArgoCD\ndrift detection"]
            OTEL["OTel Collector\ntrace pipeline"]
        end
        TF --> CT --> K8S_HA --> MESH --> KN --> GITOPS
        GITOPS --> OTEL
    end
```

```bash
#!/usr/bin/env bash
# integration-verify.sh — run after completing all labs
set -euo pipefail

PASS=0
FAIL=0

check() {
  local desc="$1"
  local cmd="$2"
  local expected="$3"
  result=$(eval "$cmd" 2>/dev/null || echo "ERROR")
  if echo "$result" | grep -q "$expected"; then
    echo "  PASS: $desc"
    ((PASS++))
  else
    echo "  FAIL: $desc (got: $result)"
    ((FAIL++))
  fi
}

echo "========================================"
echo "Cloud Native Systems — Integration Check"
echo "========================================"

echo ""
echo "[Lab 1] Twelve-Factor App"
check "namespace exists" \
  "kubectl get ns twelve-factor -o jsonpath='{.status.phase}'" \
  "Active"
check "deployment running" \
  "kubectl -n twelve-factor get deployment twelve-factor-app -o jsonpath='{.status.readyReplicas}'" \
  "[1-9]"
check "config externalized" \
  "kubectl -n twelve-factor get configmap app-config -o jsonpath='{.data.LOG_LEVEL}'" \
  "info"

echo ""
echo "[Lab 2] Container Runtime"
check "containerd socket accessible" \
  "sudo crictl version 2>&1" \
  "RuntimeVersion"
check "cgroup v2 mounted" \
  "mount | grep cgroup2" \
  "cgroup2"
check "overlayfs in use" \
  "mount | grep overlay" \
  "overlay"

echo ""
echo "[Lab 3] Orchestration"
check "ha-lab namespace active" \
  "kubectl get ns ha-lab -o jsonpath='{.status.phase}'" \
  "Active"
check "PDB healthy" \
  "kubectl -n ha-lab get pdb ha-app-pdb -o jsonpath='{.status.currentHealthy}'" \
  "[1-9]"
check "pods spread across nodes" \
  "kubectl -n ha-lab get pods -o wide | awk 'NR>1{print \$7}' | sort -u | wc -l" \
  "[1-9]"

echo ""
echo "[Lab 4] Service Mesh"
check "istio-system active" \
  "kubectl get ns istio-system -o jsonpath='{.status.phase}'" \
  "Active"
check "istiod running" \
  "kubectl -n istio-system get pods -l app=istiod --field-selector=status.phase=Running --no-headers | wc -l" \
  "[1-9]"
check "mesh-lab sidecar injection enabled" \
  "kubectl get ns mesh-lab -o jsonpath='{.metadata.labels.istio-injection}'" \
  "enabled"

echo ""
echo "[Lab 5] Serverless"
check "knative-serving active" \
  "kubectl get ns knative-serving -o jsonpath='{.status.phase}'" \
  "Active"
check "knative service ready" \
  "kubectl get ksvc event-handler -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}'" \
  "True"

echo ""
echo "[Lab 6] GitOps + OpenTelemetry"
check "argocd namespace active" \
  "kubectl get ns argocd -o jsonpath='{.status.phase}'" \
  "Active"
check "argocd application synced" \
  "kubectl -n argocd get application cloud-native-lab -o jsonpath='{.status.sync.status}'" \
  "Synced"
check "otel collector running" \
  "kubectl -n observability get pods -l app=otel-collector --field-selector=status.phase=Running --no-headers | wc -l" \
  "[1-9]"
check "jaeger running" \
  "kubectl -n observability get pods -l app=jaeger --field-selector=status.phase=Running --no-headers | wc -l" \
  "[1-9]"

echo ""
echo "========================================"
echo "Results: ${PASS} passed, ${FAIL} failed"
echo "========================================"
[ "$FAIL" -eq 0 ] && echo "All checks passed." || echo "Review failures above."
```

```bash
chmod +x integration-verify.sh
./integration-verify.sh
```

---

## Lab Teardown

```bash
# Remove all lab namespaces and resources in dependency order
kubectl delete namespace mesh-lab --ignore-not-found
kubectl delete namespace ha-lab --ignore-not-found
kubectl delete namespace twelve-factor --ignore-not-found
kubectl delete namespace gitops-lab --ignore-not-found
kubectl delete namespace observability --ignore-not-found
kubectl delete pod cgroup-verify --ignore-not-found

# Remove ArgoCD application first (respects finalizer, cleans up gitops-lab)
argocd app delete cloud-native-lab --cascade 2>/dev/null || \
  kubectl -n argocd delete application cloud-native-lab --ignore-not-found

# Remove Knative
kubectl delete -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-core.yaml 2>/dev/null || true
kubectl delete namespace knative-serving --ignore-not-found
kubectl delete namespace knative-eventing --ignore-not-found

# Remove Istio
istioctl uninstall --purge -y 2>/dev/null || true
kubectl delete namespace istio-system --ignore-not-found

# Remove ArgoCD
kubectl delete namespace argocd --ignore-not-found

echo "Teardown complete."
```

---

## Reference: Key Commands Quick Sheet

| Task | Command |
|---|---|
| Inspect container via containerd | `sudo crictl inspect <id>` |
| View cgroup v2 CPU limit | `cat /sys/fs/cgroup/<path>/cpu.max` |
| Check OCI bundle | `sudo find /run/containerd -name config.json` |
| Enter container's network namespace | `sudo nsenter -t <pid> -n ip link` |
| Check PDB disruption budget | `kubectl get pdb -A` |
| Inspect Envoy listeners | `istioctl proxy-config listeners <pod>` |
| Inspect Envoy routes | `istioctl proxy-config routes <pod>` |
| Check mTLS status | `istioctl authn tls-check <pod> <svc>` |
| Watch Knative scale | `kubectl get pods -l serving.knative.dev/service=<name> -w` |
| ArgoCD sync status | `argocd app get <name>` |
| Check OTel collector metrics | `curl localhost:8888/metrics` |
| Send manual OTLP trace | `curl -X POST :4318/v1/traces -d '{...}'` |
