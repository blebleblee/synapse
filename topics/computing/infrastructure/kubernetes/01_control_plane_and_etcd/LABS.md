# Hands-On Operational Lab: Kubernetes Microservice Deployment, Zero-Downtime Rollouts & Diagnostic Debugging

## Objective & Lab Prerequisites
In this lab, you will deploy a hardened microservice with zero-downtime rolling updates, inspect control plane reconciliation mechanisms, intentionally induce real-world failure domains (`CrashLoopBackOff`, `OOMKilled`), and isolate root-cause events using standard Kubernetes diagnostics.

### Prerequisites
* A running Kubernetes cluster (e.g., Rancher Desktop, Minikube, Kind, or a bare-metal K3s/RKE2 cluster).
* `kubectl` configured with cluster administrator privileges.
* Verify cluster connectivity before beginning:
  ```bash
  kubectl cluster-info
  kubectl get nodes -o wide
  ```

---

## Exercise 1: Cluster State & API Discovery

Inspect the exposed API surface and control plane state machine:

```bash
# 1. Discover all registered API groups, versions, and whether resources are namespaced
kubectl api-resources --sort-by=name

# 2. Inspect the raw OpenAPI schema definition for PodSpecs
kubectl explain pod.spec.containers.securityContext

# 3. Check node allocatable resources vs physical capacity
kubectl describe nodes | grep -A 8 "Allocatable:"

# 4. Create an isolated lab namespace
kubectl create namespace k8s-deep-dive
kubectl config set-context --current --namespace=k8s-deep-dive
```

---

## Exercise 2: Zero-Downtime Deployment & Canary Rollout

### Step 1: Deploy the Microservice Manifest

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo-service
  namespace: k8s-deep-dive
  labels:
    app: echo-service
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: echo-service
  template:
    metadata:
      labels:
        app: echo-service
    spec:
      containers:
        - name: echo
          image: hashicorp/http-echo:0.2.3
          args:
            - "-text=v1.0.0-production"
            - "-listen=:5678"
          ports:
            - containerPort: 5678
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "250m"
              memory: "128Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 5678
            initialDelaySeconds: 2
            periodSeconds: 3
---
apiVersion: v1
kind: Service
metadata:
  name: echo-service
  namespace: k8s-deep-dive
spec:
  type: ClusterIP
  selector:
    app: echo-service
  ports:
    - port: 80
      targetPort: 5678
EOF
```

### Step 2: Validate Pod Lifecycle & EndpointSlice Registration

```bash
# Verify all 4 replicas are Running and Ready
kubectl get pods -l app=echo-service -o wide

# Inspect the EndpointSlice controller's mapping of Pod IPs to Service IP
kubectl get endpointslices -l kubernetes.io/service-name=echo-service -o yaml
```

### Step 3: Execute a Live Zero-Downtime Rolling Update

```bash
# Trigger an image update with a new version flag
kubectl set args deployment/echo-service echo="-text=v2.0.0-canary" "-listen=:5678"

# Monitor the rollout in real-time
kubectl rollout status deployment/echo-service

# Check rollout history and revisions
kubectl rollout history deployment/echo-service
```

Observe how `maxUnavailable: 0` ensured existing pods continued serving traffic while new pods passed their `readinessProbe` before old pods were sent `SIGTERM`.

---

## Exercise 3: Inducing and Debugging `CrashLoopBackOff`

We will deliberately induce a configuration failure to inspect how the `kubelet` detects and records crashing containers.

### Step 1: Deploy a Crashing Container

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: crash-demo
  namespace: k8s-deep-dive
spec:
  restartPolicy: Always
  containers:
    - name: failing-app
      image: alpine:3.19
      command: ["/bin/sh", "-c"]
      args:
        - |
          echo "Booting payment validation subsystem..."
          sleep 2
          echo "FATAL: Database connection timeout (ECONNREFUSED 10.0.0.1:5432)" >&2
          exit 1
EOF
```

### Step 2: Diagnose the Failure with Event and Log Inspection

```bash
# 1. Watch the pod state transition to CrashLoopBackOff
kubectl get pod crash-demo -w

# 2. Inspect the Pod's lifecycle events
kubectl describe pod crash-demo | grep -A 10 "Events:"

# Notice the Back-off restarting failed container event emitted by kubelet

# 3. Read the crash logs from the previous failed execution instance
kubectl logs crash-demo --previous
```

---

## Exercise 4: Inducing and Debugging `OOMKilled` (Exit Code 137)

Now we will examine how Linux kernel cgroups enforce memory limits when container memory consumption exceeds boundaries.

### Step 1: Deploy a Memory Leaking Pod

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: oom-demo
  namespace: k8s-deep-dive
spec:
  restartPolicy: Never
  containers:
    - name: memory-eater
      image: python:3.11-alpine
      command: ["python3", "-c"]
      args:
        - |
          import time
          print("Allocating memory rapidly...")
          chunks = []
          for i in range(100):
              chunks.append(b"A" * (10 * 1024 * 1024)) # 10MB chunk per iteration
              print(f"Allocated {(i+1)*10} MB")
              time.sleep(0.1)
      resources:
        limits:
          memory: "50Mi" # Hard limit: 50MB
EOF
```

### Step 2: Validate the OOMKiller Eviction Event

```bash
# Wait for the pod to terminate
sleep 5
kubectl get pod oom-demo

# Inspect container exit status
kubectl get pod oom-demo -o jsonpath='{.status.containerStatuses[0].state.terminated}'
```

### Expected Output Analysis:
```json
{
  "exitCode": 137,
  "reason": "OOMKilled",
  "finishedAt": "..."
}
```

* **Exit Code 137 Meaning:** The application did not call `exit(137)`. In Linux, an exit code $> 128$ represents termination by a signal ($128 + N$). Signal 9 is `SIGKILL` ($128 + 9 = 137$).
* The Linux kernel's cgroup memory subsystem observed the container crossing its 50Mi memory ceiling and instantly sent uncatchable `SIGKILL` to prevent host starvation.

---

## Exercise 5: Clean Up

```bash
# Delete all resources created in this lab
kubectl delete namespace k8s-deep-dive
```

---

## Challenge Lab: Socratic Exploration
1. In `Exercise 2`, modify the Deployment to set `readinessProbe` to query an invalid endpoint (`/does-not-exist`). Trigger a rollout. Why does `kubectl rollout status` hang indefinitely, and why does the existing Service continue serving traffic without dropping requests?
2. If a Pod is stuck in `Terminating` for 15 minutes, what Linux kernel process states (e.g., Uninterruptible Sleep `D` state on NFS/storage mounts) prevent the `kubelet` from unmounting volumes? How do you diagnose this via `dmesg`?
