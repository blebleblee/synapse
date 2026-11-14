# Operational Verification Labs: Serverless

## Objective & Environment Setup

Serverless on Kubernetes is not magic. It is a distributed state machine composed of reconciling controllers, a sidecar-mediated data plane, an autoscaler that consumes queue-depth telemetry, and an ingress controller that translates high-level routing intentions into low-level network rules. Knative Serving — the canonical serverless framework for Kubernetes — implements this state machine through four control-plane Deployments (`controller`, `autoscaler`, `webhook`, `activator`), a set of Custom Resource Definitions (`Service`, `Configuration`, `Revision`, `Route`, `PodAutoscaler`), a queue-proxy sidecar injected into every Revision pod, and an ingress controller that routes external traffic. The objective of this lab series is to verify each of these subsystems with the same kernel and cluster toolchain used for any production workload: `kubectl` for declarative state, `crictl` for the container runtime, `ss` and `iproute2` for the network plane, `etcdctl` for the consensus store, `perf` and `strace` for runtime profiling, `bpftool` for in-kernel programs, and `tcpdump` for packet-level evidence. By the end you will have measured cold-start latency from the activator's perspective, profiled the queue-proxy under saturation, and observed the system's response when the autoscaler is removed.

### Cluster provisioning with kind

We use a `kind` cluster with Knative Serving and the Kourier ingress. The Kourier gateway is exposed as a NodePort on port 31080, mapped to the host. The commands below are complete and reproducible on any Linux host with Docker and `kind` installed.

```bash
# Install kind and kubectl if not present
curl -sLo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x kind && sudo mv kind /usr/local/bin/
curl -sLO "https://dl.k8s.io/release/v1.29.2/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Create the cluster with port mappings for Kourier
cat > /tmp/knative-kind.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: knative-lab
nodes:
- role: control-plane
  image: kindest/node:v1.29.2@sha256:51a1434a53971934e1320bd019c2ec5fbb8d8e5f463611f45fd405c8db4e0c83
  extraPortMappings:
  - containerPort: 31080
    hostPort: 31080
    protocol: TCP
  - containerPort: 31443
    hostPort: 31443
    protocol: TCP
EOF

kind create cluster --config /tmp/knative-kind.yaml
kubectl cluster-info --context kind-knative-lab
```

### Knative Serving installation

Install Knative Serving CRDs, the core control plane, and the Kourier ingress. Configure the network layer and DNS for local access via `sslip.io`, then patch Kourier to use the NodePort we mapped in the kind config.

```bash
# Knative Serving CRDs and core
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.13.2/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.13.2/serving-core.yaml

# Kourier ingress
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.13.0/kourier.yaml

# Configure Knative to use Kourier as the ingress class
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

# Configure DNS for local resolution
kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"127.0.0.1.sslip.io":""}}'

# Patch Kourier service to NodePort on 31080
kubectl patch svc kourier -n kourier-system \
  --type='json' \
  --patch='[{"op":"replace","path":"/spec/type","value":"NodePort"},{"op":"replace","path":"/spec/ports/0/nodePort","value":31080}]'

# Wait for all control-plane components
kubectl wait --for=condition=Ready --timeout=300s -n knative-serving \
  deploy/controller deploy/autoscaler deploy/webhook deploy/activator
kubectl wait --for=condition=Ready --timeout=300s -n kourier-system \
  deploy/3scale-kourier-gateway deploy/kourier-control

# Install kn CLI for convenience (optional — all lab steps use kubectl)
curl -sLO "https://github.com/knative/client/releases/download/kn-v1.13.0/kn-linux-amd64"
chmod +x kn-linux-amd64 && sudo mv kn-linux-amd64 /usr/local/bin/kn
```

### Diagnostic toolchain installation

Install the diagnostic tools on the host and inside the kind node container. The kind node is a Docker container named `knative-lab-control-plane`; we exec into it to use `crictl`, `perf`, `bpftool`, and `strace` directly against kubelet-managed processes.

```bash
# Host-side tools
sudo apt-get install -y iproute2 ethtool tcpdump strace jq curl || \
  brew install iproute2mac ethtool tcpdump jq

# perf on the host (may require linux-tools for the running kernel)
sudo apt-get install -y linux-tools-generic || true

# Node-side tools (inside the kind container)
docker exec -it knative-lab-control-plane bash -c \
  "apt-get update && apt-get install -y jq iproute2 ethtool tcpdump strace linux-tools-generic bpftool"

# Install hey for HTTP load generation on the host
curl -sL https://hey-release.s3.us-east-2.amazonaws.com/hey_linux_amd64 -o /tmp/hey
chmod +x /tmp/hey && sudo mv /tmp/hey /usr/local/bin/hey
hey 2>&1 | head -3

# Verify the complete toolchain
echo "=== Host tools ==="
kubectl version --client --short 2>/dev/null || kubectl version --client
ss --version
tcpdump --version 2>&1 | head -1
perf --version 2>&1 | head -1
bpftool version 2>&1 | head -1
hey 2>&1 | head -1

echo "=== Node tools ==="
docker exec knative-lab-control-plane bash -c \
  "crictl --version && ss --version && tcpdump --version 2>&1 | head -1 && perf --version 2>&1 | head -1 && bpftool version 2>&1 | head -1"
```

### Component inventory verification

Verify that all Knative Serving control-plane components are running and that the five core CRDs are registered with the Kubernetes API server. The four Deployments in `knative-serving` are the `controller` (reconciles Service, Configuration, Revision, and Route resources), the `autoscaler` (consumes metrics from queue-proxy sidecars and adjusts the desired pod count via the Knative Pod Autoscaler), the `webhook` (validating and mutating admission for Knative CRDs), and the `activator` (data-plane proxy that holds traffic during scale-from-zero). The Kourier ingress controller lives in `kourier-system` as two Deployments: `3scale-kourier-gateway` (the Envoy-based data plane) and `kourier-control` (the control plane that translates Knative Routes into Envoy configuration).

```bash
kubectl get deploy -n knative-serving -o wide
kubectl get deploy -n kourier-system -o wide
kubectl get crd | grep -E 'services\.serving|revisions\.serving|routes\.serving|configurations\.serving|podautoscalers\.autoscaling'
kubectl get pods -A | grep -E 'knative-serving|kourier'
```

The expected output is four Ready Deployments in `knative-serving`, two Ready Deployments in `kourier-system`, and five registered CRDs. If any Deployment is not Ready, inspect its events with `kubectl describe deploy <name> -n knative-serving` before proceeding.

---

## Exercise 1: Live State & Internal Subsystem Inspection

The objective of this exercise is to map the full lifecycle of a Knative Service from its declaration as a CRD through its reconciliation into a Revision, Route, Deployment, and pod, then drop into the node with `crictl`, `ss`, `bpftool`, and `etcdctl` to inspect the queue-proxy sidecar, its network listeners, its cgroup resource limits, and its storage in etcd's MVCC revision history.

### Deploying the lab workload

We deploy a CPU-bound Python service that computes the Nth Fibonacci number iteratively. This gives us a controllable amount of work per request so we can saturate the queue-proxy's concurrency limit and exercise the KPA's scaling decision in Exercise 2. The service uses `ThreadingTCPServer` so each request runs in its own thread, allowing the user container to handle concurrent requests up to the `containerConcurrency` limit enforced by the queue-proxy.

```bash
kubectl create namespace serverless-lab

cat > /tmp/ksvc-fib.yaml <<'YAML'
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fib-stream
  namespace: serverless-lab
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/class: kpa.autoscaling.knative.dev
        autoscaling.knative.dev/metric: concurrency
        autoscaling.knative.dev/target: "10"
        autoscaling.knative.dev/min-scale: "0"
        autoscaling.knative.dev/max-scale: "12"
        autoscaling.knative.dev/scale-down-delay: "30s"
        autoscaling.knative.dev/window: "60s"
    spec:
      containerConcurrency: 10
      timeoutSeconds: 60
      serviceAccountName: default
      containers:
      - image: python:3.11-slim
        name: user-container
        ports:
        - containerPort: 8080
        env:
        - name: BIND
          value: "0.0.0.0:8080"
        command: ["python3", "-u", "-c"]
        args:
        - |
          import http.server, socketserver, json, os
          bind = os.environ.get('BIND', '0.0.0.0:8080').split(':')
          host, port = bind[0], int(bind[1])
          class H(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  n = int(self.path.split('/')[-1] or '30')
                  a, b = 0, 1
                  for _ in range(n):
                      a, b = b, a + b
                  body = json.dumps({"n": n, "fib": a}).encode()
                  self.send_response(200)
                  self.send_header('Content-Type', 'application/json')
                  self.send_header('Content-Length', str(len(body)))
                  self.end_headers()
                  self.wfile.write(body)
              def log_message(self, *a): pass
          socketserver.ThreadingTCPServer.allow_reuse_address = True
          with socketserver.ThreadingTCPServer((host, port), H) as srv:
              srv.serve_forever()
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
          limits:
            cpu: 1000m
            memory: 256Mi
YAML

kubectl apply -f /tmp/ksvc-fib.yaml
kubectl wait ksvc/fib-stream -n serverless-lab --for=condition=Ready --timeout=180s
```

### Reconciliation state inspection

The Knative Service's `status` field is the reconciled output of the controller's level-triggered reconciliation loop. Each condition — `ConfigurationsReady`, `RoutesReady`, `Ready` — is recomputed on every reconcile pass. The controller creates a Configuration (which produces a Revision) and a Route (which assigns traffic to that Revision). The Revision is then materialized as a Kubernetes Deployment with a queue-proxy sidecar. Examine the full status document and the four subresources:

```bash
kubectl get ksvc fib-stream -n serverless-lab -o jsonpath='{.status}' | jq .
kubectl get configuration -n serverless-lab -o wide
kubectl get revision -n serverless-lab -o wide
kubectl get route -n serverless-lab -o wide
kubectl get podautoscaler -n serverless-lab -o wide
```

The Route status reveals the ingress URL and the traffic split. In a freshly deployed Service, 100 percent of traffic flows to the latest Revision. The Route is the resource that the Kourier controller translates into Envoy routing configuration inside the `3scale-kourier-gateway` Deployment. Verify the URL is correctly formed:

```bash
SVC_URL=$(kubectl get ksvc fib-stream -n serverless-lab -o jsonpath='{.status.url}')
echo "Service URL: $SVC_URL"
SVC_HOST=$(echo $SVC_URL | sed 's|http://||; s|/.*||')
echo "Service Host: $SVC_HOST"
```

### etcd storage and MVCC revision inspection

Knative CRDs are stored in etcd like any other Kubernetes resource. The Knative controller's reconciliation loop reads these resources, computes the desired state, and writes updates back. Each write increments the MVCC revision, creating a monotonic history of changes. Use `etcdctl` inside the kind control-plane container to inspect the raw storage and verify the revision history.

```bash
docker exec -it knative-lab-control-plane bash -c '
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/serving.knative.dev/services/serverless-lab/fib-stream -w json \
  | jq "{key: (.kvs[0].key | @base64d), create_revision: .kvs[0].create_revision, mod_revision: .kvs[0].mod_revision, version: .kvs[0].version}"
'
```

The output shows the etcd key (the full resource path), the `create_revision` (the MVCC revision at which the key was first created), the `mod_revision` (the latest revision at which the key was modified), and the `version` (the number of times the key has been modified since creation). Every time the Knative controller reconciles the Service and updates its status, the `mod_revision` increments. List all Knative-related keys to see the full storage footprint:

```bash
docker exec -it knative-lab-control-plane bash -c '
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/serving.knative.dev/ --prefix --keys-only | head -20
'
```

This reveals the keys for every Service, Configuration, Revision, and Route stored under the `/registry/serving.knative.dev/` prefix. The etcd Raft consensus quorum for this single-node cluster is Q = ⌊1/2⌋ + 1 = 1, meaning every write is immediately committed. In a production multi-node etcd cluster with N = 3 or N = 5 members, the quorum would be 2 or 3 respectively, and writes would require majority acknowledgment before being considered durable.

### Deployment, ReplicaSet, and queue-proxy sidecar

Beneath the Knative CRDs sits a standard Kubernetes Deployment created by the Revision reconciler. Inspect it. The Deployment's pod template contains two containers: the user container and the queue-proxy sidecar. The queue-proxy is the component that gives Knative its scale-to-zero and concurrency-limiting primitives. It terminates the data-plane connection from the activator or ingress, applies per-revision concurrency limits, and reports metrics to the autoscaler over a bidirectional gRPC stream. Every request to the user container flows through the queue-proxy first.

```bash
kubectl get deploy -n serverless-lab -l serving.knative.dev/service=fib-stream -o wide
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream -o wide
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream \
  -o jsonpath='{range .items[0].spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}'
```

The output shows two containers: `user-container` running `python:3.11-slim` and `queue-proxy` running the Knative queue-proxy image. Both share the pod's network namespace (anchored by the `pause` container), so they communicate over `localhost`.

### Node-side container runtime inspection

To inspect the containers from the containerd runtime's perspective, exec into the kind control-plane node and use `crictl`. The kind node is a Docker container; inside it, containerd is the runtime and `crictl` talks to it through the Unix socket at `/run/containerd/containerd.sock`.

```bash
docker exec -it knative-lab-control-plane bash

# Inside the node container:
# List all containers related to our Knative Service
crictl ps --name queue-proxy
crictl ps --name user-container

# Inspect the queue-proxy container
QP_ID=$(crictl ps --name queue-proxy -q | head -1)
crictl inspect $QP_ID | jq '{pid: .status.pid, state: .status.state, image: .status.image.image}'
QP_PID=$(crictl inspect $QP_ID | jq -r '.status.pid')
echo "queue-proxy PID: $QP_PID"

# Inspect the user container
UC_ID=$(crictl ps --name user-container -q | head -1)
UC_PID=$(crictl inspect $UC_ID | jq -r '.status.pid')
echo "user-container PID: $UC_PID"

# View the full runtime spec including cgroup path
crictl inspect $UC_ID | jq '.info.runtimeSpec.linux.cgroupsPath'
```

Record both PIDs. We will use them with `ss`, `perf`, and `strace` throughout the remaining exercises.

### Network listener inspection with ss

The queue-proxy and user container share the pod's network namespace. The queue-proxy binds data-plane ports (8012 for HTTP/1.1 and 8022 for h2c) and a metrics port. The user container listens on the port declared in the Knative Service spec — 8080 in our manifest. Use `nsenter` to enter the pod's network namespace and inspect the listening sockets with `ss`.

```bash
# Inside the node container, with QP_PID from the previous step:
nsenter -t $QP_PID -n ss -tipn -l
nsenter -t $UC_PID -n ss -tipn -l

# Verify both containers see the same network namespace
nsenter -t $QP_PID -n ss -tipn -l | grep -E '8012|8022|8080'
```

The output should show three listening sockets: the queue-proxy on port 8012 (HTTP data plane), the queue-proxy on port 8022 (h2c data plane), and the user container on port 8080. The queue-proxy receives all inbound traffic and forwards it to the user container over `localhost:8080`.

Examine the established connections during a live request to see the forwarding path:

```bash
# In one terminal, start a request from the host:
curl -H "Host: $SVC_HOST" http://localhost:31080/fib/30 &

# Inside the node container, immediately inspect established connections:
nsenter -t $QP_PID -n ss -tipmn | grep -A4 'ESTAB'
```

The `ss -tipmn` output shows every established TCP connection with internal TCP state information (rtt, rto, snd_wnd, rcv_wnd) and socket memory allocation. You should see two established connections: one from the ingress to the queue-proxy on port 8012, and one from the queue-proxy to the user container on port 8080.

### Cgroup resource enforcement

Knative enforces the user container's resource limits via the pod's cgroup hierarchy. The kind node uses cgroups v2. Verify that the CPU and memory limits declared in the Knative Service spec are correctly applied at the cgroup level.

```bash
# Inside the node container:
CGPATH=$(crictl inspect $UC_ID | jq -r '.info.runtimeSpec.linux.cgroupsPath')
echo "cgroup path: $CGPATH"

# On cgroups v2, the path may be relative — prefix with /sys/fs/cgroup
[[ "$CGPATH" != /* ]] && CGPATH="/$CGPATH"

echo "=== CPU limit (quota period) ==="
cat /sys/fs/cgroup$CGPATH/cpu.max
echo "=== Memory limit ==="
cat /sys/fs/cgroup$CGPATH/memory.max
echo "=== CPU weight (derived from request) ==="
cat /sys/fs/cgroup$CGPATH/cpu.weight
echo "=== Current memory usage ==="
cat /sys/fs/cgroup$CGPATH/memory.current
echo "=== CPU throttling stats ==="
cat /sys/fs/cgroup$CGPATH/cpu.stat
```

The `cpu.max` file should read `100000 100000`, meaning a quota of 100,000 microseconds per 100,000-microsecond period — exactly 1 CPU, matching the `1000m` limit we declared. The `memory.max` should be `268435456` (256 MiB). The `cpu.weight` is derived from the CPU request (100m) and is used by the CFS scheduler when the node is contended. The `cpu.stat` file shows whether the container has been throttled (`nr_throttled` greater than 0 indicates CFS quota exhaustion).

### eBPF and CNI inspection with bpftool

The kind cluster uses a bridge CNI by default. If no BPF programs are attached, `bpftool prog show` will return only system-level programs (cgroup attachment points from kubelet, socket filtering from containerd). Run the following inside the node container to inventory any BPF programs and inspect cgroup attachment points:

```bash
# Inside the node container:
echo "=== BPF programs loaded ==="
bpftool prog show

echo "=== BPF maps loaded ==="
bpftool map show

echo "=== Cgroup attachment tree ==="
bpftool cgroup tree

echo "=== Network interface inventory ==="
ip link show
ip -s link show
```

The `bpftool cgroup tree` output shows BPF programs attached at cgroup level — typically `cgroup_sock` and `cgroup_connect` programs from kubelet's socket binding. The `ip -s link` output provides per-interface statistics: `cni0` (the bridge), `veth*` pairs (pod endpoints), and `eth0` (the node's own interface). These statistics become the baseline for correlating packet counts with request throughput in Exercise 2.

### Activator data plane verification

The activator is the critical component during scale-from-zero. It is a data-plane proxy that receives requests when no Revision pods exist. Verify its Deployment, Service, and Endpoints:

```bash
kubectl get deploy -n knative-serving -l app=activator -o wide
kubectl get svc -n knative-serving -l app=activator
kubectl get endpoints -n knative-serving -l app=activator -o yaml | jq '.subsets[0].addresses'
```

The activator runs as a Deployment (typically 1–3 replicas on the quickstart). Its Service is how the Kourier ingress reaches it when a Revision is at scale zero. The autoscaler watches for Revisions at zero and registers them with the activator so the ingress controller routes to the activator instead of the (non-existent) Revision pods. When a request arrives, the activator signals the autoscaler to spin up pods, holds the request, and forwards it once a pod is ready.

### Scale-to-zero and PodAutoscaler state

Force the Service to scale to zero by waiting past the `scale-down-delay` annotation (30 seconds). Then inspect the PodAutoscaler resource — this is the KPA's view of the Service:

```bash
# Wait for scale-to-zero
sleep 65
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream
# Expected: No resources found

# Inspect the PodAutoscaler status
kubectl get podautoscaler -n serverless-lab fib-stream -o yaml | grep -A15 status

# Verify the Service status still shows Ready (the Service is still routable via activator)
kubectl get ksvc fib-stream -n serverless-lab -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

The PodAutoscaler's status should show `desiredScale: 0` and `active: false`. The Service's Ready condition remains `True` because the Route still resolves — it just points to the activator instead of a pod. This is the fundamental design property of Knative's scale-to-zero: the Service is always "ready" from the client's perspective, but the cost of a cold start is paid on the first request.

---

## Exercise 2: Benchmarking & Saturation Profiling

This exercise measures two operational phenomena: cold-start latency as experienced through the activator path, and steady-state saturation as the KPA scales the Revision out under load. We use `hey` for HTTP load generation, `perf stat` to measure CPU cycles consumed by the queue-proxy during cold-start ramp-up, `strace` to capture the system calls the queue-proxy makes while forwarding a request, `tcpdump` to capture the request path through the ingress and activator, and `ethtool` to correlate interface statistics with observed throughput.

### Cold-start latency measurement

The Service is currently at scale zero. We will issue a single request, measure its end-to-end latency, and observe the activator-to-autoscaler-to-pod lifecycle. Open three terminals to observe the system from three vantage points simultaneously.

**Terminal 1 — watch the pod appear:**
```bash
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream -w
```

**Terminal 2 — watch the PodAutoscaler reconcile:**
```bash
kubectl get podautoscaler -n serverless-lab fib-stream -o yaml -w | \
  grep -E 'desiredScale|actualScale|active'
```

**Terminal 3 — trigger the cold start and measure latency:**
```bash
SVC_HOST=$(kubectl get ksvc fib-stream -n serverless-lab -o jsonpath='{.status.url}' | sed 's|http://||; s|/.*||')

# Single cold-start request
curl -H "Host: $SVC_HOST" \
     "http://localhost:31080/fib/30" \
     -w "\nDNS: %{time_namelookup}s  Connect: %{time_connect}s  TLS: %{time_appconnect}s  TTFB: %{time_starttransfer}s  Total: %{time_total}s\n" \
     -o /dev/null -s
```

The `time_total` is the cold-start latency. It includes the activator receiving the request, the autoscaler creating a Pod via the KPA, kubelet scheduling the Pod, containerd starting the queue-proxy and user containers, the queue-proxy reporting readiness, and the activator forwarding the buffered request. With the image already cached on the kind node, this should be 1–4 seconds. The `time_starttransfer` (time to first byte) is the most informative metric: it captures the full cold-start overhead before any response data arrives.

Run five cold starts to build a distribution. Between each, wait for the scale-down-delay to return the Service to zero:

```bash
for i in 1 2 3 4 5; do
  sleep 65  # wait for scale-to-zero
  curl -H "Host: $SVC_HOST" \
       "http://localhost:31080/fib/30" \
       -w "cold start $i: TTFB=%{time_starttransfer}s Total=%{time_total}s\n" \
       -o /dev/null -s
done
```

### Warm-start latency baseline

Immediately after a cold start (while the pod is still warm), measure warm-start latency. The difference between cold and warm is the container startup cost:

```bash
for i in 1 2 3 4 5; do
  curl -H "Host: $SVC_HOST" \
       "http://localhost:31080/fib/30" \
       -w "warm start $i: TTFB=%{time_starttransfer}s Total=%{time_total}s\n" \
       -o /dev/null -s
done
```

Warm-start latency should be in the 2–20 millisecond range, roughly two orders of magnitude faster than cold start. This ratio is the fundamental economic argument for serverless: you trade a cold-start penalty for not paying for idle compute.

### Profiling the queue-proxy with perf stat

During a cold start, capture the queue-proxy's CPU activity with `perf stat`. The queue-proxy is written in Go and starts a gRPC client to the autoscaler, an HTTP server on the data port, and a metrics exporter. The first ten seconds of its life are the most CPU-intensive. We need to capture perf during this window.

```bash
docker exec -it knative-lab-control-plane bash

# Inside the node container — wait for queue-proxy to appear, then capture perf
# Run this BEFORE triggering the cold start from the host
QP_ID=""
for i in $(seq 1 120); do
  QP_ID=$(crictl ps --name queue-proxy -q 2>/dev/null | head -1)
  [[ -n "$QP_ID" ]] && break
  sleep 0.5
done

if [[ -n "$QP_ID" ]]; then
  QP_PID=$(crictl inspect $QP_ID | jq -r '.status.pid')
  echo "Capturing perf stat for queue-proxy PID $QP_PID"
  perf stat -p $QP_PID -- sleep 10
else
  echo "queue-proxy not found — trigger a cold start from the host first"
fi
```

Trigger the cold start from the host terminal before the `perf stat` command times out. The perf output shows cycles, instructions, branches, branch misses, cache misses, context switches, and CPU migrations during the first ten seconds of the queue-proxy's life. The `task-clock` and `context-switches` metrics are the most diagnostic: a high context-switch count (hundreds in 10 seconds) indicates the queue-proxy is simultaneously communicating with the autoscaler over gRPC and accepting the buffered request from the activator. If `perf stat` fails due to permission issues, run `perf stat` with `--per-core` or use `strace -c` as a fallback.

### strace of the request-forwarding path

To see exactly which system calls the queue-proxy executes to forward a single request to the user container, attach `strace` to the queue-proxy PID and issue one request. Filter for network-related syscalls to keep the output readable.

```bash
# Inside the node container, with QP_PID from the previous step:
# If the pod was recreated, get the new PID
QP_ID=$(crictl ps --name queue-proxy -q | head -1)
QP_PID=$(crictl inspect $QP_ID | jq -r '.status.pid')

# Start strace in the background, tracing forked children
strace -p $QP_PID -f -e trace=network,read,write,epoll_wait -o /tmp/qp.strace &
STRACE_PID=$!

# From the HOST terminal, trigger a single request:
curl -H "Host: $SVC_HOST" "http://localhost:31080/fib/30"

# Back inside the node container, stop strace and review
kill $STRACE_PID
wait $STRACE_PID 2>/dev/null

# Examine the strace output
wc -l /tmp/qp.strace
head -100 /tmp/qp.strace
grep -c 'accept4\|connect\|sendto\|recvfrom\|write\|read' /tmp/qp.strace
```

The strace output shows the queue-proxy accepting the inbound connection on port 8012 via `accept4`, opening a new socket to `127.0.0.1:8080` via `connect`, copying the request bytes from the inbound socket to the outbound socket via `read`/`write` pairs, and closing the file descriptors. The `epoll_wait` calls reveal the event-driven loop: the queue-proxy uses a single-threaded event loop (Go's netpoller, which maps to epoll on Linux) to multiplex many connections. Every request traverses this proxy path, which is why the queue-proxy's efficiency is critical to Knative's overhead.

### Saturation profiling with concurrent load

Now exercise the KPA's scaling decision. We use `hey` to generate sustained concurrent load against a Service with `containerConcurrency: 10` and `target: 10`. The autoscaler should observe queue depth exceeding the target and scale out the Revision.

```bash
# From the host, generate 60 seconds of sustained load with 50 concurrent workers
hey -n 6000 -c 50 -q 20 -t 30 \
    -H "Host: $SVC_HOST" \
    "http://localhost:31080/fib/25"
```

In a second terminal, watch the KPA scale out and observe the scaling decision in real time:

```bash
# Watch pods scale out
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream -w

# Watch the PodAutoscaler status update
kubectl get podautoscaler -n serverless-lab fib-stream -o yaml -w | \
  grep -E 'desiredScale|actualScale|target|scaling'

# Watch the Kourier gateway connections
kubectl exec -n kourier-system deploy/3scale-kourier-gateway -- \
  ss -tipn | grep -c ESTAB
```

The KPA's scaling decision is based on observed concurrency over the 60-second window (the `autoscaling.knative.dev/window` annotation). With 50 concurrent requests and a target of 10, the autoscaler computes `desiredScale = ceil(50 / 10) = 5` and scales the Deployment accordingly. The `hey` output summary shows the latency distribution: the 99th percentile reveals how the queue-proxy handles burst traffic while the autoscaler is still scaling out. Watch the `desiredScale` field update in the PodAutoscaler status as the autoscaler observes the sustained concurrency.

### Packet-level flow capture with tcpdump

To see the actual request flow through the ingress, activator, and queue-proxy, capture packets on the kind node. The Kourier gateway, activator, and Revision pods all live on the pod network, which is bridged through `cni0`.

```bash
# Inside the node container:
tcpdump -i any -nn -w /tmp/knative-saturation.pcap \
  'tcp port 8080 or tcp port 8012 or tcp port 8022 or tcp port 80 or tcp port 443' &
TCPDUMP_PID=$!

# From the host, generate load
hey -n 200 -c 20 -q 10 -t 30 \
    -H "Host: $SVC_HOST" \
    "http://localhost:31080/fib/20"

# Stop the capture
kill $TCPDUMP_PID
wait $TCPDUMP_PID 2>/dev/null

# Analyze the capture
echo "=== Total packets ==="
tcpdump -r /tmp/knative-saturation.pcap -nn | wc -l
echo "=== SYN packets (new connections) ==="
tcpdump -r /tmp/knative-saturation.pcap -nn 'tcp[tcpflags] & tcp-syn != 0' | wc -l
echo "=== Sample flow ==="
tcpdump -r /tmp/knative-saturation.pcap -nn | head -40
echo "=== Connection pairs ==="
tcpdump -r /tmp/knative-saturation.pcap -nn 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack != 0' | awk '{print $5, "->", $3}' | sort | uniq -c | sort -rn | head -10
```

The SYN count is a proxy for connection count. Each SYN establishes a new TCP connection to either the Kourier gateway, the activator, or the queue-proxy. The connection pairs show which endpoints are communicating: you should see traffic from the Kourier gateway to the queue-proxy on port 8012, and from the queue-proxy to the user container on port 8080.

### Interface statistics correlation

Use `ip -s link` and `ethtool` to correlate packet counters with the throughput observed by `hey`. The pod network on a kind cluster uses a bridge (`cni0`) and veth pairs. Take a snapshot before and after the load test to compute deltas.

```bash
# Inside the node container — BEFORE the load test:
echo "=== BEFORE: cni0 stats ==="
ip -s link show cni0

echo "=== BEFORE: veth interfaces ==="
ip -s link show | grep -E 'veth|cni0' -A5

echo "=== BEFORE: ethtool cni0 ==="
ethtool -S cni0 2>/dev/null || echo "cni0 is virtual — ethtool stats not available"

# Run the load test from the host
hey -n 500 -c 20 -q 10 -t 30 -H "Host: $SVC_HOST" "http://localhost:31080/fib/20"

# AFTER the load test:
echo "=== AFTER: cni0 stats ==="
ip -s link show cni0

echo "=== AFTER: veth interfaces ==="
ip -s link show | grep -E 'veth|cni0' -A5

echo "=== Queue-proxy socket memory (during/after load) ==="
nsenter -t $(crictl inspect $(crictl ps --name queue-proxy -q | head -1) | jq -r '.status.pid') -n ss -tipmn | grep -A4 ':8012'
```

The `ip -s link` output shows RX/TX packet counts and byte counts. The difference between BEFORE and AFTER gives the total packets and bytes that traversed the bridge during the load test. Divide by the test duration to get approximate throughput. The `ss -tipmn` output for port 8012 shows the queue-proxy's accepted connections with per-socket memory allocation (`skmem` field). High `skmem` values indicate the queue-proxy is buffering requests, which happens when the user container is saturated and cannot keep up with the incoming rate.

---

## Exercise 3: Fault Injection & Recovery Analysis

The final exercise injects four classes of fault: control-plane removal (kill the autoscaler), network latency (`tc netem`), forced scale-to-zero with activator-path verification, and queue-proxy resource exhaustion. For each we measure the system's response and recovery time. The goal is to determine which faults the Knative control plane tolerates gracefully and which degrade the data plane.

### Fault 1: Autoscaler removal

The autoscaler is a single Deployment (one replica on the kind quickstart). If we remove it, the KPA's reconciliation loop stops: existing Revisions stay at their current scale, but no new scaling decisions are made. The activator still functions, but scale-from-zero will hang because the activator cannot signal a controller that does not exist. This fault tests the data-plane/control-plane decoupling.

```bash
# Pre-fault: confirm the Service is warm and serving
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream
curl -H "Host: $SVC_HOST" "http://localhost:31080/fib/10" -w "pre-fault: %{time_total}s\n" -o /dev/null -s

# Remove the autoscaler
kubectl scale deploy -n knative-serving autoscaler --replicas=0
kubectl get deploy -n knative-serving autoscaler
# Expected: 0/0

# Wait and confirm existing pods persist (no scale-down occurs without the autoscaler)
sleep 65
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream
# Expected: pods still present — the scale-down-delay annotation is acted on by the
# autoscaler controller, so without it, scale-to-zero does not occur.

# Generate load — the Service still serves, but does not scale out
hey -n 1000 -c 80 -q 30 -t 30 \
    -H "Host: $SVC_HOST" \
    "http://localhost:31080/fib/20"

# Observe: pods do not scale out beyond current count
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream
kubectl get podautoscaler -n serverless-lab fib-stream -o yaml | grep -E 'desiredScale|actualScale'

# Restore the autoscaler
kubectl scale deploy -n knative-serving autoscaler --replicas=1
kubectl rollout status deploy/autoscaler -n knative-serving --timeout=120s

# Verify recovery — the autoscaler should begin reconciling immediately
sleep 10
kubectl get podautoscaler -n serverless-lab fib-stream -o yaml | grep -E 'desiredScale|actualScale'
kubectl logs -n knative-serving deploy/autoscaler --tail=10 | grep -i 'reconcile\|scale'
```

The expected behavior: with the autoscaler removed, the Revision stays at whatever scale it was when the autoscaler was killed. Requests still flow through the queue-proxy and are served. The system is degraded (no scaling, no scale-to-zero) but available. The data plane is decoupled from the autoscaling control plane, which is a deliberate design choice: a failed autoscaler does not take down running services. The `hey` output will show higher latency under load because the Service cannot scale out to meet demand, and the queue-proxy will buffer excess requests up to `containerConcurrency`.

### Fault 2: Network latency injection with tc netem

Inject network latency on the pod bridge interface to simulate a slow CNI or congested node. Use `tc` with the `netem` qdisc on `cni0` inside the kind node. This fault tests the queue-proxy's behavior under elevated round-trip times and the autoscaler's response to the resulting increase in observed concurrency.

```bash
# Inside the node container:
# Baseline measurement — no latency
tc qdisc show dev cni0

# From the host, measure baseline latency
hey -n 100 -c 10 -H "Host: $SVC_HOST" "http://localhost:31080/fib/10" 2>&1 | \
  grep -E 'Average|Slowest|Fastest'

# Inject 200ms one-way latency on cni0
tc qdisc add dev cni0 root netem delay 200ms

# Verify the qdisc is applied
tc qdisc show dev cni0

# Measure latency under injected delay
hey -n 100 -c 10 -H "Host: $SVC_HOST" "http://localhost:31080/fib/10" 2>&1 | \
  grep -E 'Average|Slowest|Fastest'

# The average request time should increase by approximately 400ms (200ms each way,
# request and response both traverse cni0).

# Now test autoscaler response under latency + load
# The increased per-request latency means each request holds a concurrency slot
# longer, so observed concurrency rises and the autoscaler should scale out.
hey -n 2000 -c 30 -q 10 -t 30 -H "Host: $SVC_HOST" "http://localhost:31080/fib/15" &

# In another terminal, watch the KPA scale out
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream -w
kubectl get podautoscaler -n serverless-lab fib-stream -o yaml -w | \
  grep -E 'desiredScale|actualScale'

# Wait for the load test to complete
wait

# Clean up — remove the latency
tc qdisc del dev cni0 root
tc qdisc show dev cni0

# Verify latency returns to baseline
hey -n 100 -c 10 -H "Host: $SVC_HOST" "http://localhost:31080/fib/10" 2>&1 | \
  grep -E 'Average|Slowest|Fastest'
```

With 200ms one-way latency, each request takes at least 400ms longer (round trip through the bridge). The queue-proxy holds each concurrency slot for the duration of the request, so observed concurrency rises proportionally. With `target: 10` and 30 concurrent connections each taking ~400ms, the autoscaler sees higher concurrency and scales out. This demonstrates how network latency, not just CPU load, drives autoscaling decisions in a concurrency-based system.

### Fault 3: Forced scale-to-zero and activator path verification

Force the Revision to scale to zero and verify that the activator intercepts traffic. We use `kubectl debug` to run `tcpdump` inside the activator pod, then trigger a cold start and confirm the traffic path.

```bash
# Ensure the Service is at scale zero
sleep 65
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream
# Expected: No resources found

# Identify the activator pod
ACTIVATOR_POD=$(kubectl get pod -n knative-serving -l app=activator \
  -o jsonpath='{.items[0].metadata.name}')
echo "Activator pod: $ACTIVATOR_POD"

# Attach a debug container with tcpdump to the activator pod
kubectl debug -n knative-serving $ACTIVATOR_POD \
  --image=nicolaka/netshoot \
  --target=$ACTIVATOR_POD \
  -- tcpdump -i any -nn -c 30 'tcp port 8012 or tcp port 8080 or tcp port 80' &

DEBUG_PID=$!
sleep 3

# From the host, trigger a cold-start request
echo "Triggering cold start..."
curl -H "Host: $SVC_HOST" \
     "http://localhost:31080/fib/30" \
     -w "cold start via activator: TTFB=%{time_starttransfer}s Total=%{time_total}s\n" \
     -o /dev/null -s

# Wait for the debug container to finish capturing
wait $DEBUG_PID 2>/dev/null

# Verify the activator pod saw traffic
kubectl logs -n knative-serving $ACTIVATOR_POD --tail=20 | grep -i 'request\|forward\|activat'

# Confirm the pod was created
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream
```

The `tcpdump` capture inside the activator pod should show inbound traffic from the Kourier gateway (on port 80 or 8012) and outbound traffic to the newly-created Revision pod's queue-proxy (port 8012). The activator is the bridge between the cold state (no pods) and the warm state (pod ready). The cold-start latency measured here should match the values from Exercise 2, confirming the activator path is deterministic.

### Fault 4: Queue-proxy resource exhaustion under max-scale cap

Deploy a second Knative Service with deliberately low resource limits and a low max-scale cap. Saturate it and observe the system's behavior when the autoscaler hits the max-scale ceiling. This fault tests what happens when the system cannot scale out fast enough to meet demand — the queue-proxy must buffer or reject requests.

```bash
cat > /tmp/ksvc-starve.yaml <<'YAML'
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fib-starve
  namespace: serverless-lab
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/class: kpa.autoscaling.knative.dev
        autoscaling.knative.dev/metric: concurrency
        autoscaling.knative.dev/target: "5"
        autoscaling.knative.dev/min-scale: "1"
        autoscaling.knative.dev/max-scale: "3"
    spec:
      containerConcurrency: 20
      timeoutSeconds: 30
      containers:
      - image: python:3.11-slim
        name: user-container
        ports:
        - containerPort: 8080
        env:
        - name: BIND
          value: "0.0.0.0:8080"
        command: ["python3", "-u", "-c"]
        args:
        - |
          import http.server, socketserver, json, os, time
          bind = os.environ.get('BIND', '0.0.0.0:8080').split(':')
          host, port = bind[0], int(bind[1])
          class H(http.server.BaseHTTPRequestHandler):
              def do_GET(self):
                  n = int(self.path.split('/')[-1] or '35')
                  a, b = 0, 1
                  for _ in range(n):
                      a, b = b, a + b
                  time.sleep(0.1)
                  body = json.dumps({"n": n, "fib": a}).encode()
                  self.send_response(200)
                  self.send_header('Content-Type', 'application/json')
                  self.send_header('Content-Length', str(len(body)))
                  self.end_headers()
                  self.wfile.write(body)
              def log_message(self, *a): pass
          socketserver.ThreadingTCPServer.allow_reuse_address = True
          with socketserver.ThreadingTCPServer((host, port), H) as srv:
              srv.serve_forever()
        resources:
          requests:
            cpu: 25m
            memory: 32Mi
          limits:
            cpu: 50m
            memory: 64Mi
YAML

kubectl apply -f /tmp/ksvc-starve.yaml
kubectl wait ksvc/fib-starve -n serverless-lab --for=condition=Ready --timeout=180s

STARVE_HOST=$(kubectl get ksvc fib-starve -n serverless-lab -o jsonpath='{.status.url}' | sed 's|http://||; s|/.*||')

# Saturate the starved service
hey -n 300 -c 50 -q 20 -t 30 \
    -H "Host: $STARVE_HOST" \
    "http://localhost:31080/fib/20"

# Observe the autoscaler hitting the max-scale cap
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-starve
kubectl get podautoscaler -n serverless-lab fib-starve -o yaml | grep -A15 status

# The status should show desiredScale=3 (capped from the computed value of 10)
# and a condition indicating the max-scale limit was reached.
kubectl get podautoscaler -n serverless-lab fib-starve -o jsonpath='{.status.conditions}' | jq .

# Check CPU throttling at the cgroup level
docker exec -it knative-lab-control-plane bash -c '
UC_ID=$(crictl ps --name user-container -q | head -1)
CGPATH=$(crictl inspect $UC_ID | jq -r ".info.runtimeSpec.linux.cgroupsPath")
[[ "$CGPATH" != /* ]] && CGPATH="/$CGPATH"
echo "=== CPU throttling ==="
cat /sys/fs/cgroup$CGPATH/cpu.stat
echo "=== CPU limit ==="
cat /sys/fs/cgroup$CGPATH/cpu.max
echo "=== Memory usage ==="
cat /sys/fs/cgroup$CGPATH/memory.current
cat /sys/fs/cgroup$CGPATH/memory.max
'
```

With a 50m CPU limit and `containerConcurrency: 20`, the user container will be throttled by CFS. The `cpu.stat` output will show `nr_throttled` greater than zero, indicating the container hit its CPU quota and was forced to wait. The queue-proxy will buffer requests up to its concurrency limit, and the autoscaler will try to scale out. With `target: 5` and 50 concurrent requests, the desired scale is `ceil(50 / 5) = 10`, but `max-scale: 3` caps it. The PodAutoscaler status will show `desiredScale: 3` with a condition message indicating the max-scale annotation limited the scaling. This is the production signal that the Service is max-scaled and requests are being queued — the operator must either raise `max-scale` or optimize the container's resource efficiency.

### Recovery verification

After each fault, verify the system returns to steady state:

```bash
# Restore the autoscaler if it was removed
kubectl scale deploy -n knative-serving autoscaler --replicas=1

# Remove any tc qdisc
docker exec knative-lab-control-plane tc qdisc del dev cni0 root 2>/dev/null

# Delete the starved service
kubectl delete ksvc fib-starve -n serverless-lab

# Wait for the autoscaler to reconcile
sleep 15

# Final health check
kubectl get deploy -n knative-serving
kubectl get pod -n serverless-lab -l serving.knative.dev/service=fib-stream
kubectl get podautoscaler -n serverless-lab fib-stream -o yaml | grep -E 'desiredScale|actualScale'

# Functional verification
curl -H "Host: $SVC_HOST" "http://localhost:31080/fib/30" \
     -w "recovery check: %{time_total}s HTTP %{http_code}\n" -o /dev/null -s
```

---

## Diagnostic Cheat Sheet & Verification Checklist

This section consolidates the verification commands used throughout the labs into a quick-reference form. Each command targets a specific subsystem and produces a specific verification signal.

### Control plane verification

```bash
# All Knative Serving control-plane Deployments are Ready
kubectl get deploy -n knative-serving
kubectl rollout status deploy/controller -n knative-serving
kubectl rollout status deploy/autoscaler -n knative-serving
kubectl rollout status deploy/webhook -n knative-serving
kubectl rollout status deploy/activator -n knative-serving

# CRDs are registered
kubectl get crd | grep -E 'serving\.knative\.dev|autoscaling\.knative\.dev'

# Webhooks are configured
kubectl get validatingwebhookconfigurations.admissionregistration.k8s.io \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep -i knative
kubectl get mutatingwebhookconfigurations.admissionregistration.k8s.io \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep -i knative

# Kourier ingress is ready
kubectl get deploy -n kourier-system
kubectl get svc -n kourier-system
kubectl get svc kourier -n kourier-system -o jsonpath='{.spec.ports[0].nodePort}'
```

### Reconciliation verification

```bash
# A Knative Service is fully reconciled when Ready=True
kubectl get ksvc -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Each Revision is Ready
kubectl get revision -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Each Route has a URL and traffic split
kubectl get route -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.url}{"\n"}{end}'

# PodAutoscaler shows desired and actual scale
kubectl get podautoscaler -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}desired={.status.desiredScale}{"\t"}actual={.status.actualScale}{"\n"}{end}'
```

### etcd storage verification

```bash
# Verify Knative CRDs are stored in etcd with MVCC revisions
docker exec knative-lab-control-plane bash -c '
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/serving.knative.dev/ --prefix --keys-only | head -20
'

# Check MVCC revision for a specific Service
docker exec knative-lab-control-plane bash -c '
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/serving.knative.dev/services/serverless-lab/fib-stream -w json \
  | jq "{create_revision: .kvs[0].create_revision, mod_revision: .kvs[0].mod_revision, version: .kvs[0].version}"
'
```

### Data plane verification

```bash
# queue-proxy sidecar is present in every Revision pod
kubectl get pod -A -l serving.knative.dev/service \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{range .spec.containers[*]}{.name}{" "}{end}{"\n"}{end}'

# queue-proxy is listening on data ports (run on the node)
docker exec knative-lab-control-plane bash -c '
QP_ID=$(crictl ps --name queue-proxy -q | head -1)
QP_PID=$(crictl inspect $QP_ID | jq -r ".status.pid")
nsenter -t $QP_PID -n ss -tipn -l
'

# User container is listening on the declared port
docker exec knative-lab-control-plane bash -c '
UC_ID=$(crictl ps --name user-container -q | head -1)
UC_PID=$(crictl inspect $UC_ID | jq -r ".status.pid")
nsenter -t $UC_PID -n ss -tipn -l
'

# Established connections during a live request
docker exec knative-lab-control-plane bash -c '
QP_ID=$(crictl ps --name queue-proxy -q | head -1)
QP_PID=$(crictl inspect $QP_ID | jq -r ".status.pid")
nsenter -t $QP_PID -n ss -tipmn | grep ESTAB
'
```

### Cgroup resource verification

```bash
# CPU and memory limits on the user container
docker exec knative-lab-control-plane bash -c '
UC_ID=$(crictl ps --name user-container -q | head -1)
CGPATH=$(crictl inspect $UC_ID | jq -r ".info.runtimeSpec.linux.cgroupsPath")
[[ "$CGPATH" != /* ]] && CGPATH="/$CGPATH"
echo "cgroup: $CGPATH"
echo "cpu.max: $(cat /sys/fs/cgroup$CGPATH/cpu.max)"
echo "memory.max: $(cat /sys/fs/cgroup$CGPATH/memory.max)"
echo "cpu.weight: $(cat /sys/fs/cgroup$CGPATH/cpu.weight)"
echo "cpu.stat: $(cat /sys/fs/cgroup$CGPATH/cpu.stat)"
echo "memory.current: $(cat /sys/fs/cgroup$CGPATH/memory.current)"
'
```

### Autoscaler verification

```bash
# Autoscaler is receiving metrics and making decisions
kubectl logs -n knative-serving deploy/autoscaler --tail=30 | grep -E 'metric|scale|decision|reconcile'

# KPA is reconciling
kubectl get podautoscaler -A -o yaml | grep -E 'desiredScale|actualScale|target'

# Activator is registered as a backend for scale-zero Revisions
kubectl get endpoints -n knative-serving -l app=activator -o yaml | jq '.subsets[0].addresses'

# Activator logs during a cold start
kubectl logs -n knative-serving -l app=activator --tail=20 | grep -i 'request\|forward\|activat'
```

### Performance verification

```bash
SVC_HOST=$(kubectl get ksvc fib-stream -n serverless-lab -o jsonpath='{.status.url}' | sed 's|http://||; s|/.*||')

# Cold-start latency (scale-to-zero state)
sleep 65
curl -H "Host: $SVC_HOST" "http://localhost:31080/fib/30" \
     -w "cold: TTFB=%{time_starttransfer}s Total=%{time_total}s\n" -o /dev/null -s

# Warm-start latency (already-scaled state)
for i in 1 2 3; do
  curl -H "Host: $SVC_HOST" "http://localhost:31080/fib/30" \
       -w "warm: TTFB=%{time_starttransfer}s Total=%{time_total}s\n" -o /dev/null -s
done

# Saturation throughput
hey -n 1000 -c 50 -q 20 -t 30 -H "Host: $SVC_HOST" "http://localhost:31080/fib/25"

# Queue-proxy perf profile (10 seconds)
docker exec knative-lab-control-plane bash -c '
QP_ID=$(crictl ps --name queue-proxy -q | head -1)
QP_PID=$(crictl inspect $QP_ID | jq -r ".status.pid")
perf stat -p $QP_PID -- sleep 10
'

# Queue-proxy strace (single request)
docker exec knative-lab-control-plane bash -c '
QP_ID=$(crictl ps --name queue-proxy -q | head -1)
QP_PID=$(crictl inspect $QP_ID | jq -r ".status.pid")
timeout 5 strace -p $QP_PID -f -e trace=network,read,write -o /tmp/qp.strace 2>/dev/null
wc -l /tmp/qp.strace
head -50 /tmp/qp.strace
'
```

### Network verification

```bash
# Interface statistics
docker exec knative-lab-control-plane ip -s link show cni0
docker exec knative-lab-control-plane ip -s link show | grep -E 'veth|cni0' -A5

# ethtool statistics
docker exec knative-lab-control-plane ethtool -S cni0 2>/dev/null || \
  echo "cni0 is virtual — ethtool stats not available"

# Socket memory inspection
docker exec knative-lab-control-plane bash -c '
QP_ID=$(crictl ps --name queue-proxy -q | head -1)
QP_PID=$(crictl inspect $QP_ID | jq -r ".status.pid")
nsenter -t $QP_PID -n ss -tipmn | grep -A4 ":8012"
'

# Packet capture
docker exec knative-lab-control-plane bash -c '
tcpdump -i any -nn -c 100 -w /tmp/knative.pcap "tcp port 8080 or tcp port 8012" &
sleep 5
tcpdump -r /tmp/knative.pcap -nn | head -30
'
```

### Final verification checklist

| Subsystem | Verification Signal | Command |
|---|---|---|
| Control plane | 4 Deployments Ready in `knative-serving` | `kubectl get deploy -n knative-serving` |
| Ingress | 2 Deployments Ready in `kourier-system` | `kubectl get deploy -n kourier-system` |
| CRDs | 5 Knative CRDs registered | `kubectl get crd \| grep serving.knative.dev` |
| Service | `Ready=True` within 180s | `kubectl get ksvc -A` |
| Pod template | Contains `user-container` and `queue-proxy` | `kubectl get pod -l serving.knative.dev/service -o jsonpath='{.items[0].spec.containers[*].name}'` |
| Queue-proxy listeners | Ports 8012 and 8022 listening | `nsenter -t $QP_PID -n ss -tipn -l` |
| User container listener | Port 8080 listening | `nsenter -t $UC_PID -n ss -tipn -l` |
| Cgroup CPU limit | `cpu.max` matches spec | `cat /sys/fs/cgroup$CGPATH/cpu.max` |
| Cgroup memory limit | `memory.max` matches spec | `cat /sys/fs/cgroup$CGPATH/memory.max` |
| Cold-start latency | Below 5s with cached image | `curl -w "%{time_total}s"` |
| Warm-start latency | Below 50ms | `curl -w "%{time_total}s"` |
| KPA scale-out | `desiredScale` increases under load | `kubectl get podautoscaler -w` |
| Autoscaler removal | Data plane survives | `curl` still returns 200 |
| Network latency | Request time increases by ~2× injected RTT | `hey` Average |
| Max-scale cap | `desiredScale` capped in PodAutoscaler status | `kubectl get podautoscaler -o yaml` |
| etcd storage | MVCC revisions increment on status updates | `etcdctl get -w json` |
| CPU throttling | `nr_throttled > 0` under saturation | `cat /sys/fs/cgroup$CGPATH/cpu.stat` |
