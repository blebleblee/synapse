# Operational Verification Labs: Load Balancers

## Objective & Environment Setup

Load balancers represent the fundamental control plane for distributed traffic management, implementing algorithmic request distribution across backend server pools while maintaining session affinity, health state machines, and connection tracking at wire speed. In production infrastructure, load balancers operate as stateful network middleboxes that must reconcile the tension between horizontal scale-out (distributing load) and vertical fault isolation (detecting and ejecting unhealthy backends). This lab guide develops rigorous operational verification skills through hands-on inspection of Layer 4 TCP load balancers, Layer 7 HTTP reverse proxies, and cloud-native Kubernetes Service abstractions that compile down to kernel-space iptables NAT rules or eBPF connection tracking maps.

The modern load balancer exists in multiple architectural incarnations. At the lowest level, Linux kernel netfilter implements stateful NAT through conntrack hash tables, tracking five-tuple flows and rewriting packet headers as they traverse the `PREROUTING` and `POSTROUTING` chains. Above this, userspace proxies like HAProxy and NGINX implement sophisticated Layer 7 logic—HTTP header routing, TLS termination, adaptive health checks—at the cost of context-switching overhead and buffer copies between kernel and userspace. Cloud-native environments introduce another abstraction: Kubernetes Services compile declarative endpoint lists into iptables DNAT rules or IPVS virtual servers, with kube-proxy watching the API server and continuously reconciling the datapath. Each architectural layer introduces verification complexity: kernel-space requires `conntrack` and `bpftool` inspection, userspace proxies expose Prometheus metrics and admin sockets, and Kubernetes demands `kubectl` API queries cross-referenced against actual packet flows.

Effective load balancer verification demands understanding the full request path from client SYN packet through backend connection establishment. A client initiates a TCP handshake to the load balancer's virtual IP (VIP). The load balancer's connection tracking subsystem records the five-tuple (source IP, source port, destination IP, destination port, protocol) and selects a backend using its scheduling algorithm—round-robin, least connections, consistent hashing. For Layer 4 load balancers, the VIP is rewritten via Destination NAT (DNAT) to the chosen backend's real IP, and return packets undergo Source NAT (SNAT) to preserve session symmetry. For Layer 7 proxies, the load balancer terminates the client TCP connection, parses HTTP headers, selects a backend based on URL path or Host header, and opens a separate backend connection. This dual-connection model enables sophisticated routing but doubles memory overhead and introduces proxy-induced latency. Understanding this architecture informs every verification technique: packet captures must inspect both client-facing and backend-facing interfaces, connection state must reconcile frontend sessions with backend mappings, and performance profiling must attribute latency to network transport versus proxy processing.

To construct a realistic verification environment, we deploy a three-tier Kubernetes stack: a frontend LoadBalancer Service exposing a virtual IP, an NGINX Ingress Controller implementing Layer 7 HTTP routing, and a backend Deployment running multiple replicas of a simple HTTP echo server. This topology exercises both kernel-space NAT (the LoadBalancer Service) and userspace proxy logic (the Ingress Controller). The echo server returns diagnostic metadata—pod name, source IP, request headers—enabling precise verification of routing decisions and session affinity. We supplement the Kubernetes control plane with raw Linux network namespaces to simulate multi-tenant environments and demonstrate low-level packet flow inspection without orchestration abstractions.

Begin by provisioning a Kubernetes cluster with at least three worker nodes. Any conformant distribution suffices—minikube, kind, k3s, or a managed service like GKE or EKS. Ensure the cluster supports LoadBalancer Services; for local clusters, deploy MetalLB to allocate VIPs from a reserved IP pool. Install diagnostic utilities on the worker nodes themselves, not just within containers, because load balancer verification requires inspecting host network namespaces and kernel state inaccessible from pod sandboxes. The essential toolkit includes `iproute2` for interface statistics and routing tables, `conntrack-tools` for NAT session inspection, `tcpdump` and `tshark` for packet capture, `ss` for socket state enumeration, `iptables` and `ipvsadm` for kernel datapath introspection, and `bpftool` for eBPF map examination if the cluster uses Cilium or other BPF-based CNI plugins. For userspace proxy verification, install `curl` with HTTP/2 support, `wrk` for HTTP load generation, and `strace` for system call tracing.

Deploy the backend echo server as a Kubernetes Deployment with three replicas, each running a lightweight HTTP server that responds with JSON metadata. The following manifest creates the Deployment and exposes it via a ClusterIP Service, which serves as the backend target for our load balancer tests.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: echo-backend
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: echo
  template:
    metadata:
      labels:
        app: echo
    spec:
      containers:
      - name: echo
        image: hashicorp/http-echo:latest
        args:
        - "-text={\"pod\":\"$(POD_NAME)\",\"node\":\"$(NODE_NAME)\",\"ip\":\"$(POD_IP)\"}"
        - "-listen=:8080"
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: 10m
            memory: 16Mi
          limits:
            cpu: 100m
            memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: echo-backend
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: echo
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
```

Apply this manifest and verify all three pods reach `Running` state with `kubectl get pods -l app=echo`. Each pod must schedule on a different node if possible; use pod anti-affinity rules if your cluster has sufficient capacity. Retrieve the ClusterIP assigned to the Service with `kubectl get svc echo-backend`, and confirm basic connectivity by exec-ing into any pod and curling the Service IP. The response should rotate among the three backend pods due to kube-proxy's default round-robin NAT rules.

Next, deploy an NGINX Ingress Controller to implement Layer 7 HTTP load balancing. The Ingress Controller runs as a Deployment with a hostNetwork pod, listening on ports 80 and 443 on every node. It watches Ingress resources via the Kubernetes API and dynamically generates NGINX configuration files, reloading the NGINX master process when routes change. Install the official NGINX Ingress Controller using Helm, pinning a specific chart version to ensure reproducibility.

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.metrics.enabled=true \
  --set controller.metrics.serviceMonitor.enabled=false \
  --set controller.admissionWebhooks.enabled=false \
  --set controller.config.use-forwarded-headers="true" \
  --set controller.config.compute-full-forwarded-for="true" \
  --set controller.config.log-format-upstream='$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" $request_length $request_time [$proxy_upstream_name] [$proxy_alternative_upstream_name] $upstream_addr $upstream_response_length $upstream_response_time $upstream_status $req_id' \
  --version 4.9.0
```

Wait for the Ingress Controller pod to reach `Running` state and for the LoadBalancer Service to provision an external IP. If using MetalLB on a local cluster, the external IP comes from your configured address pool. If using a cloud provider, the LoadBalancer Service triggers provisioning of a cloud load balancer (AWS ELB, GCP forwarding rule) that forwards traffic to the Ingress Controller's NodePort. Retrieve the LoadBalancer IP with `kubectl get svc -n ingress-nginx ingress-nginx-controller` and verify HTTP connectivity by curling port 80. Without an Ingress resource, NGINX returns a default 404 backend response.

Create an Ingress resource that routes HTTP traffic to the echo-backend Service, implementing path-based routing and session affinity annotations. The following manifest configures the Ingress to forward all requests under `/echo` to the backend Service, stripping the path prefix so the echo server receives requests at its root path.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: echo-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "route"
    nginx.ingress.kubernetes.io/session-cookie-hash: "sha1"
    nginx.ingress.kubernetes.io/session-cookie-max-age: "3600"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "5"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "30"
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /echo
        pathType: Prefix
        backend:
          service:
            name: echo-backend
            port:
              number: 80
```

Apply the Ingress resource and wait approximately 10 seconds for the NGINX Ingress Controller to detect the change and reload its configuration. The controller's reconciliation loop polls the Kubernetes API every few seconds, generates updated NGINX config files in `/etc/nginx/nginx.conf` and `/etc/nginx/conf.d/`, and issues a graceful reload via `nginx -s reload`. Verify the Ingress configuration by curling the LoadBalancer IP with the `/echo` path. The response JSON should identify one of the three backend pods. Issue multiple requests and observe the pod name field—without session affinity cookies, responses should round-robin across backends. With affinity enabled, the NGINX response includes a `Set-Cookie: route=<hash>` header, and subsequent requests with that cookie consistently route to the same backend.

The verification environment now spans three load balancing layers: the cloud LoadBalancer Service forwarding external traffic to Ingress Controller NodePorts, the NGINX proxy performing Layer 7 HTTP routing and session affinity, and the kube-proxy iptables rules distributing backend connections across pod IPs. Each layer introduces state machines and failure modes that demand distinct verification techniques. The subsequent exercises systematically inspect each layer, correlating userspace metrics with kernel state and packet captures to build a complete operational model.

## Exercise 1: Live State & Internal Subsystem Inspection

Load balancer verification begins with comprehensive state enumeration: which connections are active, how are backends selected, what health state does each backend report, and where does kernel NAT state diverge from userspace proxy configuration? This exercise constructs a layered inspection methodology, starting at the kernel conntrack tables that underpin all stateful NAT, proceeding through iptables and IPVS rules that implement kube-proxy load balancing, and culminating in NGINX Ingress Controller internal state and metrics. Each layer's state must reconcile with the others; discrepancies indicate stale mappings, missed reconciliation loops, or asymmetric routing failures.

Begin at the lowest level: the Linux kernel conntrack subsystem that tracks all stateful connections. Conntrack maintains a hash table of flows indexed by five-tuple (source IP, source port, destination IP, destination port, protocol). Each flow entry records the connection state (NEW, ESTABLISHED, RELATED, INVALID), NAT translations (SNAT and DNAT), and timeout values. When a packet arrives, netfilter hashes its five-tuple and looks up the corresponding conntrack entry. If the entry exists and the packet's sequence number falls within the expected window, the kernel applies any configured NAT rewrites and forwards the packet. If no entry exists, the packet is considered NEW, and iptables rules in the `PREROUTING` chain determine whether to create a new conntrack entry with DNAT to a backend. This stateful tracking is essential for load balancer operation: without conntrack, every packet would undergo independent routing decisions, breaking TCP session continuity.

To inspect conntrack state, use the `conntrack` command-line tool, which queries the kernel's nf_conntrack hash table via netlink. SSH into a worker node hosting backend pods and run `conntrack -L` to list all tracked connections. The output is verbose, containing every active TCP connection, UDP datagram tracking entry, and ICMP echo association. Filter the output to show only connections involving the echo-backend Service ClusterIP. First, retrieve the Service IP with `kubectl get svc echo-backend -o jsonpath='{.spec.clusterIP}'`, then grep the conntrack output for that IP.

```bash
CLUSTER_IP=$(kubectl get svc echo-backend -o jsonpath='{.spec.clusterIP}')
sudo conntrack -L -p tcp --dport 80 | grep $CLUSTER_IP
```

Each line in the output represents a single conntrack entry with the format `tcp 6 <timeout> <state> src=<client-ip> dst=<cluster-ip> sport=<client-port> dport=80 src=<pod-ip> dst=<client-ip> sport=8080 dport=<client-port>`. The first five-tuple represents the original packet as seen by the client, and the second five-tuple represents the reply packet after DNAT rewriting. Notice that the destination IP in the original tuple matches the Service ClusterIP, while the source IP in the reply tuple matches one of the backend pod IPs. This confirms that kube-proxy's iptables DNAT rules successfully rewrote the destination address to distribute load across pods.

Conntrack entries have finite lifetimes controlled by protocol-specific timeout values. For TCP connections in the ESTABLISHED state, the default timeout is 432000 seconds (5 days), but idle connections may be reaped earlier if conntrack table pressure is high. To inspect timeout values and connection states, add the `-o extended` option to include all metadata fields.

```bash
sudo conntrack -L -p tcp --dport 80 -o extended | grep $CLUSTER_IP
```

Look for the `[ASSURED]` flag in the output. This flag indicates that the conntrack entry has seen bidirectional traffic (both original and reply packets) and will not be prematurely reaped. Connections lacking this flag are in a half-open state, meaning the client initiated the connection but the backend has not yet responded. This condition can indicate packet loss, backend unavailability, or SYN flood attacks. Count the number of ESTABLISHED versus SYN_SENT entries to assess backend health at the TCP layer.

Next, inspect the iptables NAT rules that created these conntrack entries. Kube-proxy programs iptables chains in the `nat` table to implement Kubernetes Service load balancing. Each Service receives a dedicated chain named `KUBE-SVC-<hash>` containing DNAT rules that randomly select a backend pod. For ClusterIP Services, the `KUBE-SERVICES` chain matches on the Service IP and port, then jumps to the Service's specific chain. Dump the entire `nat` table and grep for the echo-backend Service.

```bash
sudo iptables -t nat -L -n -v | grep -A 10 $CLUSTER_IP
```

The output shows a rule in the `KUBE-SERVICES` chain matching destination IP equal to the ClusterIP and destination port 80, jumping to a chain like `KUBE-SVC-ABCDEF123456`. Follow this chain by running `sudo iptables -t nat -L KUBE-SVC-ABCDEF123456 -n -v`. The Service chain contains multiple rules, each implementing a probability-weighted random selection. For a Service with three endpoints, the first rule matches with probability 0.33333 and jumps to `KUBE-SEP-<hash1>` (the first Service Endpoint), the second rule matches with probability 0.5 (because 1/2 of the remaining traffic) and jumps to `KUBE-SEP-<hash2>`, and the final rule unconditionally jumps to `KUBE-SEP-<hash3>`. This statistical round-robin ensures approximately equal load distribution over many connections.

Each `KUBE-SEP-*` chain performs the actual DNAT rewrite, translating the Service ClusterIP to a specific pod IP and port. List one of the endpoint chains to see the DNAT rule.

```bash
sudo iptables -t nat -L KUBE-SEP-ABCDEF123456 -n -v
```

You should see a rule with target `DNAT` and `to-destination <pod-ip>:8080`. This rule rewrites the destination IP and port of matching packets, creating a new conntrack entry that maps the Service ClusterIP to the pod IP. Return packets automatically undergo reverse SNAT because conntrack maintains bidirectional mappings.

Now examine the NGINX Ingress Controller's internal state, which operates independently of kube-proxy's iptables rules. The Ingress Controller maintains its own upstream server lists, health check state machines, and connection pools. NGINX exposes this state via a Prometheus metrics endpoint and an internal status API. Access the metrics endpoint by port-forwarding to the Ingress Controller pod.

```bash
NGINX_POD=$(kubectl get pods -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward -n ingress-nginx $NGINX_POD 10254:10254 &
curl -s http://localhost:10254/metrics | grep nginx_ingress
```

The metrics output includes counters for total requests handled, request duration histograms, backend connection states, and upstream response status codes. Key metrics for load balancer verification include `nginx_ingress_controller_requests` (total request count labeled by ingress, status, and method), `nginx_ingress_controller_request_duration_seconds` (latency histogram), and `nginx_ingress_controller_backend_up` (binary health status per backend). To correlate these metrics with actual backend pod states, retrieve the pod IPs and cross-reference them with NGINX's upstream server list.

```bash
kubectl get pods -l app=echo -o wide
kubectl exec -n ingress-nginx $NGINX_POD -- cat /etc/nginx/nginx.conf | grep -A 5 "upstream upstream_balancer"
```

The NGINX configuration file contains an `upstream` block named `upstream_balancer` that lists all backend servers. Each server entry includes the pod IP, port, weight, and health check parameters. NGINX dynamically updates this configuration whenever the Ingress Controller's reconciliation loop detects changes in the Kubernetes API. Compare the upstream server list against the output of `kubectl get pods` to verify that all running pods appear in the NGINX config and that terminated pods have been removed.

NGINX also exposes a JSON status API at `/nginx_status` that provides real-time connection statistics: active connections, total requests, current request rate, and upstream server states. Query this API to capture a snapshot of live traffic.

```bash
curl -s http://localhost:10254/nginx_status | jq .
```

The JSON response includes fields for `connections.active`, `connections.reading`, `connections.writing`, and `connections.waiting`. Active connections represent the total number of client sockets currently open, including idle HTTP keep-alive connections. Reading connections are those for which NGINX is currently receiving request headers or body data. Writing connections are those for which NGINX is transmitting response data. Waiting connections are idle keep-alive connections awaiting the next request. High waiting counts indicate clients holding connections open without sending requests, which can exhaust file descriptor limits under sustained load.

To inspect individual backend connection states, NGINX Plus (the commercial version) exposes an extended API with per-upstream statistics, but the open-source version requires parsing internal data structures. As an alternative, trace NGINX's backend connection activity using `ss` to enumerate sockets in the Ingress Controller's network namespace. The Ingress Controller pod runs in the host network namespace, so its sockets appear in the host's socket table.

```bash
sudo ss -tnp | grep nginx | grep :8080
```

This command lists all TCP sockets owned by NGINX worker processes that are connected to port 8080 (the echo-backend container port). Each line shows the local socket (NGINX's source IP and ephemeral port) and remote socket (pod IP and port 8080). The `ESTAB` state indicates a live connection, while `TIME-WAIT` indicates a recently closed connection awaiting final ACK packets. Count the number of ESTABLISHED connections per backend pod IP to verify that NGINX is distributing connections evenly.

For deeper inspection, use `strace` to observe NGINX's system calls in real time. Attach `strace` to an NGINX worker process PID and filter for `connect` and `sendto` calls that establish backend connections and transmit HTTP requests.

```bash
NGINX_WORKER_PID=$(pgrep -f "nginx: worker process" | head -1)
sudo strace -p $NGINX_WORKER_PID -e trace=connect,sendto,recvfrom -s 256 2>&1 | grep 8080
```

The output shows `connect()` calls to backend pod IPs on port 8080, followed by `sendto()` calls transmitting HTTP request bytes, and `recvfrom()` calls receiving HTTP response bytes. Each `connect()` call corresponds to NGINX opening a new backend connection, while `sendto()` and `recvfrom()` represent request and response forwarding. Observe the sequence of system calls to understand NGINX's connection pooling behavior: does it reuse persistent backend connections, or does it open a new connection for every request? By default, NGINX maintains a connection pool per upstream server and reuses idle connections for subsequent requests, reducing the overhead of TCP handshakes and TLS session establishment.

Finally, correlate all three layers of state—conntrack entries, iptables rules, and NGINX metrics—to construct a complete picture of request flow. Generate sustained HTTP load using `wrk` or `curl` in a loop, then simultaneously inspect conntrack, iptables counters, and NGINX metrics.

```bash
LB_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
for i in {1..100}; do curl -s http://$LB_IP/echo; done &

sudo conntrack -L -p tcp --dport 80 | grep $CLUSTER_IP | wc -l
sudo iptables -t nat -L KUBE-SERVICES -n -v | grep $CLUSTER_IP
curl -s http://localhost:10254/metrics | grep nginx_ingress_controller_requests
```

The conntrack output should show a growing number of ESTABLISHED connections as clients send requests. The iptables counter column (the first numeric column in the verbose output) increments with each matched packet, confirming that kube-proxy's NAT rules are actively processing traffic. The NGINX metrics counter increases in lockstep, verifying that the Ingress Controller is receiving and forwarding requests to backends. If any layer shows stale or zero counters, investigate potential data plane failures: misconfigured routes, blocked network policies, or crashed backend pods.

This multi-layer inspection methodology reveals load balancer operation at unprecedented granularity. By cross-referencing kernel conntrack state, iptables NAT rules, and userspace proxy metrics, you can pinpoint exactly where packets flow, how backends are selected, and where bottlenecks or failures occur. Mastery of these tools transforms load balancer troubleshooting from guesswork into deterministic diagnosis.

## Exercise 2: Benchmarking & Saturation Profiling

Load balancer performance is fundamentally constrained by three resources: CPU cycles for packet processing and connection scheduling, memory for connection tracking tables and proxy buffers, and network bandwidth for packet forwarding. Under saturation, each resource exhibits distinct failure modes: CPU exhaustion manifests as increased request latency and dropped connections, memory exhaustion triggers conntrack table evictions and out-of-memory kills, and bandwidth saturation causes packet loss and TCP retransmissions. This exercise develops rigorous benchmarking techniques to characterize load balancer performance under increasing load, profile resource consumption at saturation, and identify bottlenecks using kernel tracing and performance counters.

Begin by establishing baseline performance metrics under low load. Use `wrk`, a modern HTTP benchmarking tool, to generate a controlled request rate against the NGINX Ingress LoadBalancer IP. Start with a modest load of 100 requests per second sustained for 30 seconds, using a single thread and 10 concurrent connections.

```bash
LB_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
wrk -t 1 -c 10 -d 30s -R 100 --latency http://$LB_IP/echo
```

The `-R 100` flag configures a constant 100 requests per second rate limit, preventing `wrk` from saturating the target and allowing baseline latency measurement. The `--latency` flag prints detailed latency distribution percentiles. Record the output, focusing on the mean latency, 50th percentile (median), 95th percentile, and 99th percentile latency values. Baseline latencies should be low—single-digit milliseconds for the median and sub-100ms for the 99th percentile—because the echo backend performs minimal processing.

While the benchmark runs, monitor NGINX Ingress Controller resource usage using `kubectl top` and `perf`. First, capture CPU and memory consumption from the Kubernetes metrics server.

```bash
kubectl top pod -n ingress-nginx
```

The output shows CPU usage in millicores and memory usage in mebibytes. At 100 req/s, the NGINX controller should consume minimal CPU—likely under 50 millicores—and stable memory around 50-100 MiB. Next, profile NGINX's CPU usage at the function level using `perf record`. Identify the NGINX master process PID on the worker node and record a 10-second CPU profile.

```bash
NGINX_MASTER_PID=$(pgrep -f "nginx: master process" | head -1)
sudo perf record -F 99 -p $NGINX_MASTER_PID -g -- sleep 10
sudo perf report --stdio | head -40
```

The `perf record` command samples the call stack 99 times per second (`-F 99`) for the specified process and its children (the NGINX worker processes). The resulting `perf.data` file is analyzed with `perf report`, which displays a flame graph of CPU hotspots. Under low load, the top functions should be kernel networking code—`tcp_recvmsg`, `tcp_sendmsg`, `__sys_epoll_wait`—along with NGINX's event loop (`ngx_epoll_process_events`) and HTTP parsing functions (`ngx_http_process_request_line`). Significant time in memory allocation functions (`malloc`, `free`) or string manipulation indicates inefficient request handling.

Now gradually increase the request rate and observe latency degradation. Run `wrk` at 500 req/s, then 1000 req/s, then 2000 req/s, each time recording latency distributions and resource consumption.

```bash
wrk -t 2 -c 50 -d 30s -R 500 --latency http://$LB_IP/echo
wrk -t 4 -c 100 -d 30s -R 1000 --latency http://$LB_IP/echo
wrk -t 8 -c 200 -d 30s -R 2000 --latency http://$LB_IP/echo
```

Plot the 99th percentile latency against request rate to identify the saturation point—the rate beyond which latency increases super-linearly. For a typical NGINX Ingress Controller on a 2-core pod, saturation occurs around 2000-4000 req/s depending on request size and backend latency. Beyond saturation, latency spikes as NGINX's event loop falls behind, request queues grow, and connections time out.

At saturation, diagnose the bottleneck using kernel-level tracing. Use `perf stat` to capture hardware performance counters during a high-load benchmark.

```bash
sudo perf stat -p $NGINX_MASTER_PID -e cycles,instructions,cache-references,cache-misses,L1-dcache-load-misses,LLC-load-misses,branches,branch-misses -- sleep 10
```

The output reports raw counter values and derived metrics. The instructions-per-cycle (IPC) ratio indicates CPU efficiency: values above 1.0 suggest compute-bound workloads, while values below 0.5 indicate memory-bound workloads stalled on cache misses. High cache miss rates (over 10% of references) suggest poor data locality, common when processing many small HTTP requests that thrash the CPU cache. High branch misprediction rates (over 5%) indicate unpredictable control flow, such as parsing variable-length HTTP headers.

To pinpoint memory bottlenecks, inspect conntrack table utilization and NGINX worker memory usage. The conntrack table is sized by the kernel parameter `net.netfilter.nf_conntrack_max`, typically set to 65536 or 262144 entries. Query the current table size and usage.

```bash
sudo sysctl net.netfilter.nf_conntrack_max
sudo conntrack -L | wc -l
sudo cat /proc/sys/net/netfilter/nf_conntrack_count
```

If the conntrack count approaches the max value, the table is near exhaustion. New connection attempts will fail with "nf_conntrack: table full" errors logged to `dmesg`. To observe this failure mode, launch an aggressive connection flood that exceeds the conntrack limit.

```bash
sudo dmesg -wH &
wrk -t 8 -c 5000 -d 30s --latency http://$LB_IP/echo
```

The `wrk` command opens 5000 concurrent connections, each generating requests continuously. Monitor `dmesg` for conntrack table full errors. If errors appear, increase the conntrack table size and retry.

```bash
sudo sysctl -w net.netfilter.nf_conntrack_max=524288
sudo sysctl -w net.netfilter.nf_conntrack_buckets=131072
```

The `nf_conntrack_buckets` parameter controls the hash table's bucket count; it should be set to approximately `nf_conntrack_max / 4` to minimize collision chains. After increasing the limits, re-run the high-connection benchmark and verify that conntrack errors disappear.

Next, profile NGINX worker memory usage under load using `pmap` and `/proc` filesystem inspection. Identify a worker process PID and dump its memory map.

```bash
NGINX_WORKER_PID=$(pgrep -f "nginx: worker process" | head -1)
sudo pmap -x $NGINX_WORKER_PID | tail -1
```

The final line shows total RSS (resident set size) and dirty memory. Under moderate load, NGINX workers typically consume 50-200 MB RSS. Under extreme load with thousands of concurrent connections, memory usage can exceed 1 GB due to connection buffers, request parsing structures, and upstream response bodies buffered in memory. If RSS approaches the pod's memory limit, the Linux OOM killer may terminate the process, causing catastrophic service interruption.

To simulate memory pressure, reduce the NGINX Ingress Controller's memory limit and observe OOM kill behavior.

```bash
kubectl set resources deployment -n ingress-nginx ingress-nginx-controller --limits=memory=128Mi
kubectl rollout status deployment -n ingress-nginx ingress-nginx-controller
```

After the new pod starts, run a high-load benchmark and monitor for OOM events.

```bash
kubectl get events -n ingress-nginx --watch &
wrk -t 8 -c 2000 -d 60s --latency http://$LB_IP/echo
```

If the NGINX pod is OOM-killed, `kubectl get events` will log an event with reason `OOMKilled`. The pod restarts automatically, but existing connections are lost, causing client errors. This failure mode demonstrates the critical importance of accurate memory capacity planning and resource limit tuning.

For network bandwidth saturation, measure throughput using large request and response bodies. Deploy a modified echo server that returns a 1 MB response body, then benchmark download throughput.

```bash
kubectl set image deployment echo-backend echo=nginx:alpine
kubectl set env deployment echo-backend NGINX_ENTRYPOINT_QUIET_LOGS=1
kubectl wait --for=condition=available deployment/echo-backend --timeout=60s
```

Configure the NGINX deployment to serve a 1 MB static file by creating a ConfigMap and mounting it into the pod.

```bash
dd if=/dev/urandom of=/tmp/payload.bin bs=1M count=1
kubectl create configmap large-payload --from-file=/tmp/payload.bin
kubectl set volume deployment/echo-backend --add --name=payload --type=configmap --configmap-name=large-payload --mount-path=/usr/share/nginx/html/payload.bin --sub-path=payload.bin
```

Now benchmark download throughput by requesting the 1 MB file repeatedly.

```bash
wrk -t 4 -c 50 -d 30s --latency http://$LB_IP/echo/payload.bin
```

The throughput, reported in `wrk` output as total bytes transferred divided by duration, should approach the network interface's bandwidth limit. For a 1 Gbps NIC, expect around 120 MB/s throughput accounting for TCP and HTTP overhead. Monitor interface statistics using `ip -s link` to observe transmitted byte counters and packet drops.

```bash
IFACE=$(ip route get $LB_IP | grep -oP 'dev \K\S+')
watch -n 1 "ip -s link show $IFACE"
```

The TX (transmit) counters increment rapidly during the benchmark, showing bytes and packets sent. If the TX drop counter increments, the network interface's transmit queue is full, indicating bandwidth saturation. This condition causes TCP retransmissions and increased latency as packets are buffered or dropped.

Finally, stress-test backend connection pooling by introducing artificial latency into the echo server. Use `tc` (traffic control) to add 100ms delay to packets destined for backend pods, simulating a slow backend.

```bash
BACKEND_PODS=$(kubectl get pods -l app=echo -o jsonpath='{.items[*].metadata.name}')
for POD in $BACKEND_PODS; do
  kubectl exec $POD -- apk add --no-cache iproute2
  kubectl exec $POD -- tc qdisc add dev eth0 root netem delay 100ms
done
```

Re-run the `wrk` benchmark and observe latency increases. The median latency should rise by approximately 100ms due to the injected delay. More importantly, monitor NGINX's upstream connection state to verify that it correctly handles slow backends without exhausting connection pools.

```bash
curl -s http://localhost:10254/metrics | grep nginx_ingress_controller_backend_up
```

All backends should remain marked as `up` despite the added latency, because NGINX's health checks use timeout values (configured in the Ingress annotations) that exceed the injected delay. If backends are incorrectly marked as down, adjust the `proxy-read-timeout` and `proxy-send-timeout` annotations to accommodate backend response times.

This benchmarking exercise reveals load balancer behavior under stress: how latency scales with request rate, where resource exhaustion occurs, and how configuration parameters govern saturation points. Armed with performance profiles and saturation characteristics, you can accurately capacity-plan load balancer resources and tune kernel and userspace parameters to maximize throughput.

## Exercise 3: Fault Injection & Recovery Analysis

Production load balancers must gracefully handle failure conditions—crashed backends, network partitions, transient errors—without dropping client connections or returning errors. This exercise systematically injects faults into the load balancer stack and validates recovery behavior: backend pod crashes, network policy blocks, control plane API server unavailability, and load balancer process restarts. Each fault scenario tests a different layer of the high-availability architecture, from kube-proxy's endpoint reconciliation to NGINX's passive health checking and circuit-breaking logic.

Begin by testing backend pod failure handling. While generating sustained traffic, forcibly delete one of the three echo-backend pods and observe how quickly the load balancer detects the failure and stops routing traffic to the terminated pod.

```bash
wrk -t 2 -c 20 -d 120s --latency http://$LB_IP/echo &
sleep 5
BACKEND_POD=$(kubectl get pods -l app=echo -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $BACKEND_POD --grace-period=0 --force
```

The `--grace-period=0 --force` flags immediately terminate the pod without waiting for graceful shutdown, simulating a crash. Monitor the `wrk` output for error rates and latency spikes. Simultaneously, watch the conntrack table and iptables counters to observe stale connection cleanup.

```bash
sudo watch -n 1 "conntrack -L -p tcp --dport 80 | grep $CLUSTER_IP | wc -l"
```

Immediately after pod deletion, the conntrack count remains unchanged because existing conntrack entries have not yet timed out. However, new connection attempts to the deleted pod fail, causing NGINX to receive TCP RST packets or connection timeouts. NGINX's passive health checking logic detects these failures and marks the upstream server as down, removing it from the load balancing rotation. Measure the failure detection latency by observing when error rates return to zero in the `wrk` output. Typical detection times range from 1-10 seconds depending on NGINX's `fail_timeout` and `max_fails` configuration.

Inspect NGINX's upstream server state during the failure window.

```bash
kubectl exec -n ingress-nginx $NGINX_POD -- cat /etc/nginx/nginx.conf | grep -A 5 "upstream upstream_balancer"
curl -s http://localhost:10254/metrics | grep nginx_ingress_controller_backend_up
```

The backend marked as down in the metrics should correspond to the deleted pod's IP. After the Kubernetes control plane detects the pod termination and updates the Endpoints resource, kube-proxy removes the stale iptables DNAT rules, preventing new conntrack entries. The Ingress Controller's reconciliation loop also detects the Endpoints change and regenerates the NGINX configuration, removing the terminated pod from the upstream block. Verify the updated configuration by re-examining `nginx.conf` and confirming that the deleted pod's IP no longer appears.

Next, test recovery when the pod is automatically recreated by the Deployment controller. Because the Deployment specifies `replicas: 3`, the controller immediately schedules a replacement pod. Monitor pod creation and observe how quickly it rejoins the load balancer pool.

```bash
kubectl get pods -l app=echo --watch
```

The new pod transitions through `Pending`, `ContainerCreating`, and finally `Running` states. Once `Running`, the kubelet updates the pod's status, triggering the Endpoints controller to add the new pod IP to the echo-backend Service's Endpoints resource. Kube-proxy detects this change and programs new iptables DNAT rules. The NGINX Ingress Controller's reconciliation loop also detects the Endpoints update and adds the new pod IP to its upstream configuration. Measure the time from pod `Running` to the pod receiving traffic by observing the pod's access logs.

```bash
NEW_POD=$(kubectl get pods -l app=echo --field-selector=status.phase=Running -o jsonpath='{.items[-1].metadata.name}')
kubectl logs -f $NEW_POD
```

The first log entry indicates when the pod received its first HTTP request. Compare this timestamp to the pod's start time (`kubectl get pod $NEW_POD -o jsonpath='{.status.startTime}'`) to calculate the end-to-end recovery latency. Typical recovery times range from 5-30 seconds depending on image pull speed, container startup time, and control plane propagation delays.

Now test network partition scenarios using Kubernetes NetworkPolicy. Deploy a policy that blocks ingress traffic to one backend pod, simulating a firewall rule or network segmentation failure.

```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-one-backend
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: echo
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 8080
EOF

BLOCKED_POD=$(kubectl get pods -l app=echo -o jsonpath='{.items[1].metadata.name}')
kubectl label pod $BLOCKED_POD blocked=true

kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-specific-backend
  namespace: default
spec:
  podSelector:
    matchLabels:
      blocked: "true"
  policyTypes:
  - Ingress
  ingress: []
EOF
```

This NetworkPolicy denies all ingress traffic to the labeled pod. Because the NGINX Ingress Controller runs in the host network namespace and thus outside the pod network, it is unaffected by the policy and continues to route traffic to the blocked pod. However, those connection attempts time out because the pod's iptables rules (programmed by the CNI plugin's NetworkPolicy implementation) drop incoming SYN packets.

Run a benchmark and observe connection timeout errors.

```bash
wrk -t 2 -c 20 -d 60s --latency http://$LB_IP/echo 2>&1 | grep -i timeout
```

The error count should be approximately one-third of total requests, corresponding to the fraction of requests routed to the blocked pod. NGINX's default `proxy_connect_timeout` is 60 seconds, so affected requests hang for up to a minute before failing. This behavior is unacceptable in production, where failed backends must be ejected within seconds. Reduce the connect timeout to 2 seconds by updating the Ingress annotations.

```bash
kubectl annotate ingress echo-ingress nginx.ingress.kubernetes.io/proxy-connect-timeout=2 --overwrite
kubectl rollout restart deployment -n ingress-nginx ingress-nginx-controller
kubectl rollout status deployment -n ingress-nginx ingress-nginx-controller
```

Re-run the benchmark and verify that timeout errors resolve within 2 seconds. The error rate should drop to near zero as NGINX quickly detects the unreachable backend and removes it from rotation.

Next, test control plane failure scenarios by disrupting the Kubernetes API server. The load balancer's data plane—iptables rules, conntrack entries, NGINX configuration—should continue operating even when the control plane is unavailable, but updates (new pods, configuration changes) cannot propagate. Simulate API server unavailability by blocking network access to the API server endpoint.

```bash
KUBE_API_IP=$(kubectl cluster-info | grep -oP 'https://\K[^:]+')
sudo iptables -I OUTPUT -d $KUBE_API_IP -j REJECT
```

This iptables rule blocks all outbound traffic from the worker node to the API server. The kube-proxy and Ingress Controller processes lose connectivity and log errors, but existing iptables rules and NGINX configuration remain active. Generate traffic and verify that requests continue to succeed.

```bash
wrk -t 2 -c 20 -d 30s --latency http://$LB_IP/echo
```

Request success demonstrates that the data plane operates independently of the control plane. However, if a backend pod crashes during the API server outage, the Ingress Controller cannot detect the failure and update its configuration, causing persistent errors until connectivity is restored. Test this by deleting a backend pod while the API server is unreachable.

```bash
BACKEND_POD=$(kubectl get pods -l app=echo -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $BACKEND_POD --grace-period=0 --force
```

The delete command fails because the API server is unreachable. However, you can forcibly kill the pod's container process from the worker node to simulate a crash.

```bash
CONTAINER_ID=$(sudo crictl ps --name echo --pod $BACKEND_POD -q)
sudo crictl stop $CONTAINER_ID
```

Now traffic to the killed pod fails, but NGINX cannot detect the failure because it cannot query the Kubernetes API to discover the updated Endpoints. The error rate remains at approximately one-third of requests until API connectivity is restored. Restore connectivity by removing the iptables rule.

```bash
sudo iptables -D OUTPUT -d $KUBE_API_IP -j REJECT
```

Within seconds, the Ingress Controller's reconciliation loop detects the stale pod and updates NGINX configuration, restoring full availability.

Finally, test load balancer process crash recovery by forcibly killing the NGINX Ingress Controller pod and observing how Kubernetes restarts it and restores traffic flow.

```bash
wrk -t 2 -c 20 -d 120s --latency http://$LB_IP/echo &
sleep 5
kubectl delete pod -n ingress-nginx $NGINX_POD --grace-period=0 --force
```

The `wrk` output shows a brief spike in errors as existing connections are aborted. Kubernetes immediately schedules a replacement pod, which starts, loads the current Ingress configuration from the API, generates NGINX config files, and begins accepting traffic. Measure the downtime by observing when error rates return to zero. Typical downtime is 10-30 seconds depending on image pull time and NGINX startup duration.

For zero-downtime upgrades, deploy the Ingress Controller as a DaemonSet or multi-replica Deployment behind a LoadBalancer Service, ensuring that at least one replica remains available during rolling updates. Configure pod disruption budgets to prevent simultaneous termination of all replicas.

```bash
kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ingress-nginx-pdb
  namespace: ingress-nginx
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
EOF
```

This PodDisruptionBudget ensures that at least one Ingress Controller replica remains running during voluntary disruptions (drains, upgrades), preventing total service outage.

Through systematic fault injection and recovery analysis, this exercise validates load balancer high-availability mechanisms and exposes configuration weaknesses. Production-grade load balancers require careful tuning of health check intervals, timeout values, and failover policies to minimize client-visible errors during backend failures. The techniques demonstrated here—forced pod deletion, network partition, control plane disruption—should be incorporated into regular chaos engineering drills to ensure continuous operational readiness.

## Diagnostic Cheat Sheet & Verification Checklist

This reference section consolidates essential commands and verification procedures for rapid load balancer diagnosis in production environments. Each command is accompanied by expected output patterns and interpretation guidelines, enabling systematic troubleshooting workflows.

**Conntrack State Inspection**

List all active TCP connections through a specific Service ClusterIP:
```bash
CLUSTER_IP=$(kubectl get svc <service-name> -o jsonpath='{.spec.clusterIP}')
sudo conntrack -L -p tcp --dport <port> | grep $CLUSTER_IP
```
Expected: Each line shows original and reply five-tuples with `[ASSURED]` flag for established bidirectional connections. Missing `[ASSURED]` indicates half-open connections or packet loss.

Count total conntrack entries and compare to system limits:
```bash
sudo cat /proc/sys/net/netfilter/nf_conntrack_count
sudo cat /proc/sys/net/netfilter/nf_conntrack_max
```
Expected: Count should be well below max (under 80% utilization). Approaching max triggers `nf_conntrack: table full` errors in `dmesg`.

Monitor conntrack entry creation rate:
```bash
sudo conntrack -E | grep NEW
```
Expected: Steady stream of NEW entries during active traffic. Bursts indicate connection spikes or SYN floods.

**Iptables NAT Rule Verification**

List all Service chains and packet counts:
```bash
sudo iptables -t nat -L KUBE-SERVICES -n -v
```
Expected: Each Service has a jump rule to `KUBE-SVC-*` chain with non-zero packet counters under active traffic.

Inspect per-endpoint DNAT rules:
```bash
sudo iptables -t nat -L KUBE-SVC-<hash> -n -v
sudo iptables -t nat -L KUBE-SEP-<hash> -n -v
```
Expected: Probability-weighted rules in SVC chain, DNAT to pod IP in SEP chain. Packet counters should be roughly balanced across endpoints.

Trace packet through NAT chains for specific destination:
```bash
sudo iptables -t raw -A PREROUTING -d $CLUSTER_IP -p tcp --dport <port> -j TRACE
sudo iptables -t raw -A OUTPUT -d $CLUSTER_IP -p tcp --dport <port> -j TRACE
sudo tail -f /var/log/kern.log | grep TRACE
```
Expected: Log entries show packet traversing `PREROUTING → KUBE-SERVICES → KUBE-SVC-* → KUBE-SEP-* → DNAT`. Missing chains indicate stale kube-proxy rules.

**Kubernetes Service and Endpoint Validation**

Verify Service configuration and assigned ClusterIP:
```bash
kubectl get svc <service-name> -o yaml
kubectl get endpoints <service-name> -o yaml
```
Expected: Service `spec.clusterIP` matches iptables rules. Endpoints `subsets[].addresses[]` contains all ready pod IPs.

Check for NotReady endpoints indicating failed health checks:
```bash
kubectl get endpoints <service-name> -o jsonpath='{.subsets[].notReadyAddresses[]}'
```
Expected: Empty output if all pods pass readiness probes. Non-empty indicates failing health checks.

Watch live endpoint updates:
```bash
kubectl get endpoints <service-name> --watch
```
Expected: Immediate updates when pods start/stop or readiness state changes. Delays over 5 seconds indicate control plane latency.

**NGINX Ingress Controller Diagnostics**

Access Prometheus metrics:
```bash
NGINX_POD=$(kubectl get pods -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward -n ingress-nginx $NGINX_POD 10254:10254 &
curl -s http://localhost:10254/metrics | grep -E "nginx_ingress_controller_(requests|connections|backend)"
```
Expected: Non-zero request counters, connection counts matching `ss` socket enumeration, all backends reporting `up=1`.

Query live connection statistics:
```bash
curl -s http://localhost:10254/nginx_status | jq .
```
Expected: `connections.active` matches current client count. `connections.waiting` should be low (under 100) except during keep-alive bursts.

Inspect generated NGINX configuration:
```bash
kubectl exec -n ingress-nginx $NGINX_POD -- cat /etc/nginx/nginx.conf | grep -A 10 "upstream upstream_balancer"
```
Expected: Upstream block lists all current backend pod IPs with correct ports. Missing pods indicate stale configuration.

Test configuration reload without downtime:
```bash
kubectl exec -n ingress-nginx $NGINX_POD -- nginx -t
kubectl exec -n ingress-nginx $NGINX_POD -- nginx -s reload
```
Expected: `nginx -t` reports `syntax is ok` and `test is successful`. Reload completes in under 1 second with zero dropped connections.

**Socket State and Connection Tracking**

List all established connections to backend pods:
```bash
sudo ss -tnp | grep :<backend-port> | grep ESTAB
```
Expected: Roughly equal distribution of connections across backend pod IPs. Skewed distribution indicates load balancing failures.

Monitor socket state transitions:
```bash
sudo ss -tan | awk '{print $1}' | sort | uniq -c
```
Expected: Majority in ESTAB state. High TIME-WAIT counts indicate rapid connection churn. High SYN-SENT indicates backend connection failures.

Trace system calls for proxy process:
```bash
sudo strace -p $(pgrep -f "nginx: worker process" | head -1) -e trace=network -f 2>&1 | grep connect
```
Expected: `connect()` calls to backend pod IPs succeeding with return value 0 or -1 EINPROGRESS (non-blocking connect).

**Network Interface Statistics**

Monitor packet transmit/receive counters and errors:
```bash
ip -s -s link show <interface>
watch -n 1 "ethtool -S <interface> | grep -E '(rx|tx)_(packets|bytes|errors|dropped)'"
```
Expected: Steady increase in packet/byte counters under traffic. Non-zero `rx_errors`, `tx_errors`, or `dropped` indicates hardware issues or buffer overruns.

Capture live packet trace:
```bash
sudo tcpdump -i <interface> -n "tcp port <port>" -w /tmp/capture.pcap
tcpdump -r /tmp/capture.pcap -n | grep -E "(SYN|RST|FIN)"
```
Expected: Matching SYN/ACK pairs for successful connections. Lone SYN packets indicate connection timeouts. RST packets indicate immediate connection rejection.

**Performance Profiling**

Capture CPU profile of load balancer process:
```bash
sudo perf record -F 99 -p $(pgrep -f "nginx: master process") -g -- sleep 10
sudo perf report --stdio --no-children | head -40
```
Expected: Top functions are kernel networking (`tcp_sendmsg`, `__sys_epoll_wait`) and NGINX event loop. High percentage in memory allocation indicates inefficiency.

Measure hardware performance counters:
```bash
sudo perf stat -p $(pgrep -f "nginx: master process") -e cycles,instructions,cache-references,cache-misses -- sleep 10
```
Expected: IPC (instructions per cycle) above 0.5. Cache miss rate under 10%. High miss rates indicate poor data locality.

Profile memory allocation patterns:
```bash
sudo perf record -e syscalls:sys_enter_mmap -p $(pgrep -f "nginx: worker") -- sleep 10
sudo perf script | grep mmap | wc -l
```
Expected: Low mmap call frequency (under 100/sec). High frequency indicates excessive dynamic allocation.

**Load Balancer Health Check**

End-to-end request path verification:
```bash
LB_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -v -H "Host: example.com" http://$LB_IP/echo
```
Expected: HTTP 200 response with backend pod metadata. `X-Forwarded-For` header contains client IP. Response time under 50ms for local backends.

Session affinity validation:
```bash
for i in {1..10}; do curl -s -b cookies.txt -c cookies.txt http://$LB_IP/echo | jq -r .pod; done | uniq
```
Expected: All responses return same pod name when session affinity enabled. Multiple pod names indicate affinity failure.

Backend health endpoint monitoring:
```bash
kubectl get pods -l app=<backend-app> -o wide
for POD in $(kubectl get pods -l app=<backend-app> -o jsonpath='{.items[*].metadata.name}'); do
  kubectl exec $POD -- wget -q -O- http://localhost:<port>/health || echo "$POD FAILED"
done
```
Expected: All backends return HTTP 200 on health endpoint. Failures indicate application-level issues distinct from network reachability.

**Verification Checklist for Production Deployment**

1. **Service Configuration**: Verify `selector` matches backend pod labels. Confirm `type: LoadBalancer` allocates external IP.
2. **Endpoint Readiness**: Ensure all backend pods report `Ready` in `kubectl get pods`. Check endpoint count matches replica count.
3. **Conntrack Limits**: Confirm `nf_conntrack_max` exceeds expected concurrent connections (minimum 2x peak connection count).
4. **Iptables Rules**: Validate KUBE-SVC and KUBE-SEP chains exist for Service. Verify packet counters increment under traffic.
5. **Proxy Health**: Check NGINX/HAProxy process status, configuration syntax, and metrics endpoint accessibility.
6. **Session Affinity**: Test cookie-based or IP-based affinity with repeated requests from same client.
7. **Timeout Configuration**: Validate `proxy_connect_timeout`, `proxy_send_timeout`, and `proxy_read_timeout` match backend SLAs.
8. **Resource Limits**: Confirm load balancer pod memory/CPU limits accommodate peak traffic with 50% headroom.
9. **TLS Termination**: Verify certificate validity and cipher suite configuration if proxy handles HTTPS.
10. **Health Check Intervals**: Tune active and passive health check frequencies to detect failures within acceptable SLA bounds.

This diagnostic framework provides systematic pathways from symptom observation to root cause identification. By layering kernel state inspection, userspace metrics, and end-to-end request tracing, you construct complete operational visibility into load balancer behavior under all conditions—normal operation, high load, and failure scenarios.
