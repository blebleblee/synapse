# Hands-On Operational Lab: Kubernetes

## Objective & Prerequisites

**Objective**: Gain hands-on experience with Kubernetes by building, deploying, and debugging a production-grade application while understanding the underlying system mechanics (node scheduling, pod lifecycle, network policies, and failure recovery).

**Prerequisites**:
- Linux environment (Ubuntu 22.04 LTS recommended)
- `minikube` v1.28+ installed (`minikube version` should show ≥1.28)
- `kubectl` v1.28+ installed
- Basic understanding of Docker concepts
- 2GB+ RAM (for minikube)
- **Critical Safety Note**: Always run `minikube stop` after lab completion to prevent resource leaks

> 💡 *Why this matters*: Kubernetes operates at the kernel level (cgroups, namespaces, cgroups v2) and requires understanding of how pods map to physical nodes. This lab avoids abstract concepts by focusing on observable system states.

---

## Exercise 1: Exploration & System State Inspection

*Verify your cluster's operational state with explicit verification commands and expected outputs.*

### Step 1: Confirm cluster health
```bash
minikube status
```
**Expected Output**:
```
minikube: running
cluster: minikube
nodes: 1
docker: 24.0.7
kubectl: 1.28.0
```

### Step 2: Inspect node scheduling mechanics
```bash
kubectl get nodes -o wide
```
**Expected Output**:
```
NAME       STATUS   ROLES    AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OSIMAGE              KERNEL
minikube   Ready    <none>   10m  v1.28.0   192.168.49.2   <none>       ubuntu@22.04.3        5.15.0-103-generic
```
*Why this matters*: The `INTERNAL-IP` shows the node's physical address (not virtual). Kubernetes uses this for pod scheduling decisions.

### Step 3: Verify kubelet process (critical for node health)
```bash
minikube ssh -- sudo ps aux | grep kubelet
```
**Expected Output**:
```
root      1234     0.1  0.5  1234567  523456 ?        S    10:15   0:00 /usr/local/bin/kubelet --address=192.168.49.2 --pod-ip=192.168.49.2 --kubeconfig=/etc/kubernetes/kubeconfig --cert-dir=/etc/kubernetes/pki
```
*Why this matters*: The kubelet is the node agent that communicates with the control plane. Its presence confirms the node is operational.

### Step 4: Check container runtime status
```bash
minikube ssh -- sudo systemctl status docker
```
**Expected Output**:
```
● docker.service - Docker Container Engine
     Loaded: loaded (/lib/systemd/system/docker.service; enabled; preset: enabled)
     Active: active (running) since Mon 2024-03-11 10:15:22 UTC
```
*Why this matters*: Docker is the container runtime that executes pods. Its status affects pod scheduling.

> ✅ **Verification**: All outputs confirm your cluster is healthy and ready for deployment.

---

## Exercise 2: Building & Deploying / Modeling Scenario

*Deploy a production-grade Python web service with proper resource constraints and liveness probes.*

### Step 1: Create Dockerfile (infrastructure as code)
```dockerfile
# Dockerfile for production-grade Python app
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

### Step 2: Create requirements.txt (infrastructure as code)
```text
flask==2.3.2
gunicorn==20.1.0
```

### Step 3: Build and push to local registry (reproducible)
```bash
minikube docker-env  # Sets up Docker for minikube
docker build -t python-web:1.0 .
docker tag python-web:1.0 docker.io/library/python-web:1.0
```

### Step 4: Create Kubernetes deployment manifest (infrastructure as code)
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: python-web
  template:
    metadata:
      labels:
        app: python-web
    spec:
      containers:
      - name: python-web
        image: docker.io/library/python-web:1.0
        ports:
        - containerPort: 8000
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 15
```

### Step 5: Deploy to cluster (interactive workflow)
```bash
kubectl apply -f deployment.yaml
```

### Step 6: Verify deployment status
```bash
kubectl get pods -l app=python-web
```
**Expected Output**:
```
NAME                         READY   STATUS    RESTARTS   AGE
python-web-7d9f8b8c4b-5qj4k  2/2     Running   0          15s
python-web-7d9f8b8c4b-9z2l5  2/2     Running   0          15s
```

### Step 7: Check resource usage (critical for production)
```bash
kubectl top pods -l app=python-web
```
**Expected Output**:
```
NAME                         CPU(cores)   MEMORY(bytes)
python-web-7d9f8b8c4b-5qj4k  150m         350Mi
python-web-7d9f8b8c4b-9z2l5  120m         320Mi
```
*Why this matters*: The liveness/readiness probes ensure the application stays healthy. The `150m` CPU shows the pod is using 150m of CPU (as expected).

> ✅ **Verification**: All outputs confirm the deployment is healthy and meeting resource constraints.

---

## Exercise 3: Fault Injection, Failure Analysis & Debugging

*Simulate a failure and analyze the self-healing mechanism.*

### Step 1: Inject failure (simulating pod crash)
```bash
kubectl delete pod -l app=python-web --force
```
*Why this matters*: This simulates a pod crash (common in production). Kubernetes will automatically recreate the pod.

### Step 2: Observe self-healing
```bash
kubectl get pods -l app=python-web -w
```
**Expected Output**:
```
NAME                         READY   STATUS    RESTARTS   AGE
python-web-7d9f8b8c4b-5qj4k  2/2     Running   0          15s
python-web-7d9f8b8c4b-9z2l5  2/2     Running   0          15s
python-web-7d9f8b8c4b-5qj4k  0/2     CrashLoopBackOff   1          12s
python-web-7d9f8b8c4b-9z2l5  2/2     Running   0          12s
python-web-7d9f8b8c4b-5qj4k  2/2     Running   1          10s
```
*Why this matters*: The `CrashLoopBackOff` state shows the pod failed its liveness probe. Kubernetes automatically restarts it.

### Step 3: Analyze failure root cause
```bash
kubectl describe pod -l app=python-web
```
**Expected Output** (partial):
```
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  10s   default-scheduler  Successfully assigned default/python-web-7d9f8b8c4b-5qj4k to minikube
  Normal  Pulled     5s    kubelet            Container image docker.io/library/python-web:1.0 already present
  Normal  Created    5s    kubelet            Created container python-web
  Normal  Started    5s    kubelet            Started container python-web
  Warning FailedScheduling  2s   default-scheduler  0/1 nodes are available: 1 node(s) had insufficient cpu (100m).
  Warning FailedScheduling  2s   default-scheduler  0/1 nodes are available: 1 node(s) had insufficient memory (512Mi).
```
*Why this matters*: The `FailedScheduling` events show the node ran out of resources. Kubernetes uses the `resources.limits` to enforce this.

### Step 4: Verify recovery
```bash
kubectl get pods -l app=python-web -w
```
**Expected Output**:
```
NAME                         READY   STATUS    RESTARTS   AGE
python-web-7d9f8b8c4b-5qj4k  2/2     Running   1          15s
python-web-7d9f8b8c4b-9z2l5  2/2     Running   0          15s
```
*Why this matters*: Kubernetes automatically recreated the pod after the node recovered.

> ✅ **Verification**: The cluster self-healed without manual intervention.

---

## Challenge Lab: Independent Problem for Socratic Discussion with the AI Tutor

**Problem**:  
*Your cluster is experiencing high latency (500ms+ response times) for the `python-web` service. The `kubectl top pods` shows 100% CPU usage on the node. Analyze the root cause using the following tools:*
1. `kubectl describe pod` (for the failing pod)
2. `minikube ssh` (to check kernel-level metrics)
3. `strace` (to trace system calls)

**Socratic Questions for Discussion**:
1. Why does `kubectl top pods` show 100% CPU usage but the pod is still "Running"?
2. What kernel metrics would indicate a CPU bottleneck (hint: `top` in minikube)?
3. How would you modify the deployment to prevent this failure?
4. What happens if you don't set `livenessProbe`? (Try it with `kubectl apply -f deployment.yaml`)

**Expected Outcome**:  
You should identify that the pod is using 100% CPU due to a memory leak in the application (common in Python apps). The fix involves adding `memory` limits and increasing `livenessProbe` thresholds.

> 💡 **Why this matters**: Real-world production failures often stem from unbounded resource usage. This exercise teaches you to diagnose at the kernel level (via `strace` and `top`).

---

**Final Verification Command**:  
```bash
minikube stop  # Clean up after lab
```
