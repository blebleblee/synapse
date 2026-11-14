# Operational Verification Labs: Cilium

## Objective & Environment Setup

Cilium stands as a production-grade eBPF-native CNI plugin that replaces traditional iptables-based packet filtering with compiled BPF programs loaded directly into the Linux kernel's network datapath. Unlike legacy container networking solutions that suffer from O(n) rule traversal and userspace context switches, Cilium leverages kernel-space packet processing, XDP (eXpress Data Path) for line-rate forwarding, and CO-RE (Compile Once – Run Everywhere) relocations to achieve microsecond-latency service mesh capabilities without sidecar proxies. This operational verification lab series grounds your understanding in the physical mechanics of eBPF map lookups, connection tracking state machines, policy verdict rendering, and observability data extraction—all anchored in measurable kernel-level instrumentation.

Your verification environment requires a running Kubernetes cluster with Cilium installed as the CNI provider. The cluster may be a local kind or minikube instance, a managed GKE/EKS/AKS deployment, or a bare-metal installation. Critically, you must have root or privileged access to the worker nodes to inspect BPF programs, attach tracepoints, and capture raw packet flows. The toolchain spans multiple diagnostic layers: `kubectl` for orchestration-level state inspection, `cilium` CLI for agent introspection, `bpftool` for kernel BPF program enumeration, `crictl` for CRI-level container runtime queries, `tcpdump` for packet-level traffic capture, `perf` for CPU profiling of eBPF execution, and `etcdctl` for examining Cilium's persistent identity and policy state in the etcd backing store.

Begin by verifying the Cilium agent DaemonSet is running across all nodes. Execute `kubectl get pods -n kube-system -l k8s-app=cilium` and confirm one agent pod per worker node with `Running` status and zero restarts. A restart count above zero indicates transient failures—cross-reference timestamps with `kubectl logs` to diagnose the root cause. Next, validate that the Cilium agent has successfully connected to the Kubernetes API server and initialized its identity allocator. Run `kubectl exec -n kube-system ds/cilium -- cilium status` to retrieve the agent's self-reported health. Look for `KVStore: Ok` confirming etcd connectivity, `Kubernetes: Ok` for API server sync, `Cilium: Ok` for datapath readiness, and `IPAM: IPv4` or `IPv6` depending on your cluster addressing scheme. Any component reporting `Disabled` or `Error` demands immediate investigation—common culprits include misconfigured RBAC preventing service account access, firewall rules blocking Cilium's 4244 or 4245 agent ports, or missing kernel BPF subsystem support (`CONFIG_BPF_SYSCALL`, `CONFIG_BPF_JIT`, `CONFIG_CGROUP_BPF`).

Install the `cilium` CLI binary on your workstation or control-plane node. On Linux, download the latest release from the Cilium GitHub repository and place it in `/usr/local/bin`. Verify the installation with `cilium version` which should report both the CLI version and the detected cluster agent version. This tool serves as your primary interface for agent introspection, policy trace simulation, and datapath troubleshooting. Supplement this with `bpftool`, the canonical utility for inspecting BPF programs and maps loaded in the kernel. Install `bpftool` via your distribution's package manager: `apt-get install linux-tools-common linux-tools-generic` on Ubuntu, or `yum install bpftool` on RHEL-based systems. Confirm functionality with `bpftool prog list` which enumerates all loaded BPF programs by program ID, type (XDP, TC, cgroup, tracepoint), and attach point.

Establish baseline connectivity by deploying a simple test workload. Apply the following manifest to create a client and server pod in the `default` namespace:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cilium-test
---
apiVersion: v1
kind: Pod
metadata:
  name: client
  namespace: cilium-test
  labels:
    app: client
spec:
  containers:
  - name: netshoot
    image: nicolaka/netshoot:latest
    command: ["sleep", "infinity"]
    securityContext:
      capabilities:
        add: ["NET_ADMIN", "NET_RAW"]
---
apiVersion: v1
kind: Pod
metadata:
  name: server
  namespace: cilium-test
  labels:
    app: server
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
      protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: server
  namespace: cilium-test
spec:
  selector:
    app: server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

Wait for both pods to reach `Running` state with `kubectl wait --for=condition=Ready pod/client pod/server -n cilium-test --timeout=60s`. From the client pod, verify HTTP connectivity to the server Service ClusterIP: `kubectl exec -n cilium-test client -- curl -s http://server`. A successful response confirms end-to-end datapath forwarding through Cilium's eBPF socket layer, service load balancing via BPF maps, and connection tracking state establishment. If the request times out, proceed to Exercise 1's detailed packet flow tracing to isolate the failure point.

Before diving into live state inspection, ensure your kernel meets Cilium's minimum version requirements. Cilium demands at least Linux 4.19 for stable eBPF support, though 5.10 or newer is strongly recommended for features like BPF ring buffers, bounded loops, and CO-RE relocations. Check your kernel version with `uname -r`. If running below 4.19, upgrade your distribution or container host image. Verify BPF subsystem availability by inspecting loaded kernel modules: `lsmod | grep bpf` should show no results since BPF is compiled into the kernel, but `zgrep BPF /proc/config.gz` must return `CONFIG_BPF_SYSCALL=y`, `CONFIG_BPF_JIT=y`, `CONFIG_CGROUP_BPF=y`, and `CONFIG_BPF_EVENTS=y`. Missing configurations require a kernel recompile or a switch to a distribution with proper BPF support such as Ubuntu 20.04+, Debian 11+, or Red Hat 8+.

Your verification environment is now operational. The following exercises systematically stress-test Cilium's datapath, policy enforcement, observability stack, and failure recovery mechanisms using production-grade diagnostic workflows. Each exercise builds on kernel-level instrumentation, extracting timing histograms, packet drop counters, and BPF map occupancy metrics that expose Cilium's internal behavior under normal load, artificial saturation, and deliberate fault injection.

## Exercise 1: Live State & Internal Subsystem Inspection

Cilium's operational state spans three distinct layers: the Kubernetes orchestration plane visible through `kubectl`, the Cilium agent's internal BPF datapath managed via the `cilium` CLI, and the kernel's raw BPF program state exposed through `bpftool`. This exercise dissects each layer using targeted diagnostic commands, correlating agent-reported endpoint identities with kernel-level BPF map contents and confirming policy verdict rendering against actual packet forwarding behavior.

Start by enumerating Cilium's endpoint state. An endpoint represents a uniquely identified network entity—typically a pod—that Cilium tracks for policy enforcement and observability. From any node, execute `kubectl exec -n kube-system ds/cilium -- cilium endpoint list`. The output displays a table with columns for `ENDPOINT ID`, `IDENTITY`, `IPv4`, `IPv6`, `STATUS`, and `POLICY (ingress/egress)`. Each endpoint receives a numeric identity derived from its Kubernetes labels via Cilium's identity allocator backed by etcd. Two pods with identical label sets share the same identity, enabling efficient policy aggregation—Cilium compiles a single BPF program per identity pair rather than per pod pair, reducing kernel memory consumption from O(n²) to O(k²) where k is the number of unique identities.

Select a specific endpoint from the list, noting its numeric ID. Query detailed endpoint state with `kubectl exec -n kube-system ds/cilium -- cilium endpoint get <ENDPOINT_ID>`. The output reveals the endpoint's MAC address, IPv4/IPv6 addresses, attached BPF programs (ingress and egress), policy enforcement mode (`default: none`, `default: deny`, or explicit rules), connection tracking entries, and identity labels. Cross-reference the identity number against the global identity allocation with `kubectl exec -n kube-system ds/cilium -- cilium identity list`. This command enumerates all active identities and their associated Kubernetes label selectors. Confirm that the endpoint's labels match the identity's label set—any mismatch indicates stale agent state requiring a `cilium endpoint regenerate <ENDPOINT_ID>` to force BPF program recompilation.

Descend to the kernel layer by inspecting the actual BPF programs attached to the endpoint's network interfaces. First, identify the endpoint's virtual ethernet pair. From the node where the endpoint's pod is scheduled, list all network namespaces with `ip netns list`. Container network namespaces follow the pattern `cni-<CONTAINER_ID>`. Locate the correct namespace by correlating the endpoint's pod UID via `crictl inspect <CONTAINER_ID> | jq .info.sandboxID`. Once identified, enter the namespace with `ip netns exec <NAMESPACE> ip link show` and note the `eth0` interface inside the pod and its peer `lxc<HASH>` interface in the host namespace.

Back in the host namespace, enumerate BPF programs attached to the `lxc<HASH>` interface using `bpftool net show`. This command lists all TC (Traffic Control) and XDP programs attached to network interfaces. Look for entries like `tc/ingress` and `tc/egress` with program IDs. Extract detailed program information with `bpftool prog show id <PROG_ID>`. The output includes the program type (`sched_cls` for TC programs), loaded time, memory consumption, number of instructions (in BPF bytecode), and JIT-compiled status. A program marked `jited` confirms that the kernel's JIT compiler has translated the BPF bytecode into native x86-64 or ARM64 machine code for optimal execution speed.

Inspect the BPF program's bytecode and translated machine code with `bpftool prog dump xlated id <PROG_ID>`. The output displays the raw BPF instruction sequence as a series of `mov`, `ld`, `add`, `jmp`, and `call` operations operating on registers `r0` through `r10`. While interpreting raw bytecode is challenging, focus on key patterns: frequent `map_lookup_elem` calls indicate heavy reliance on BPF maps for policy lookups and connection tracking, while `redirect` and `drop` instructions reveal packet fate decisions. For human-readable context, dump the program's line-level information with `bpftool prog dump xlated id <PROG_ID> linum` which annotates each instruction with source file and line numbers if the program was compiled with debug symbols.

Cilium's datapath relies on BPF maps—kernel-space key-value stores shared between BPF programs and the Cilium agent userspace process. List all maps with `bpftool map list` and identify Cilium-specific maps by their names: `cilium_policy_<ID>` for policy verdict caches, `cilium_ipcache` for IP-to-identity mappings, `cilium_lxc` for endpoint state, `cilium_ct4_global` and `cilium_ct6_global` for IPv4 and IPv6 connection tracking, and `cilium_lb4_services` for service load balancing. Dump the contents of the connection tracking map with `bpftool map dump name cilium_ct4_global`. Each entry represents an active TCP or UDP flow, encoding the source and destination IP:port tuples, protocol, connection state (established, closing), and associated security identity pair. A high entry count indicates heavy connection churn—monitor map occupancy over time to detect leaks or misconfigurations preventing garbage collection.

Simulate a policy lookup by tracing packet flow with the `cilium` CLI's policy tracing feature. From the client pod, initiate a connection to the server: `kubectl exec -n cilium-test client -- curl -v http://server`. Simultaneously, on the node hosting the server pod, run `kubectl exec -n kube-system <CILIUM_POD> -- cilium monitor -t policy-verdict` to observe real-time policy verdict events. Each verdict log entry shows the source and destination identities, traffic direction, L3/L4 headers (IP addresses, TCP/UDP ports), and the final action (`allowed` or `denied`). An `allowed` verdict confirms that Cilium's policy engine successfully matched the connection against an explicit allow rule or the default-allow behavior. A `denied` verdict with no corresponding NetworkPolicy often indicates a stale identity allocation—regenerate the endpoint to refresh policy compilation.

Correlate policy verdicts with kernel-level BPF map lookups by enabling debug logging on the Cilium agent. Edit the Cilium DaemonSet to add the `--debug` flag to the agent's command arguments: `kubectl edit ds cilium -n kube-system`, locate the `args:` section, and append `--debug`. Restart the agent pods with `kubectl rollout restart ds/cilium -n kube-system`. Debug logs expose internal decision trees including identity resolution, map lookup results, and connection tracking state transitions. Retrieve logs with `kubectl logs -n kube-system <CILIUM_POD> --tail=1000 | grep policy` and search for entries containing the client and server identities. The logs reveal whether policy compilation occurred, which BPF programs were loaded, and the exact map keys used for verdict lookups.

Test Cilium's service load balancing by inspecting the BPF map backing ClusterIP services. Retrieve the server Service's ClusterIP with `kubectl get svc server -n cilium-test -o jsonpath='{.spec.clusterIP}'`. On a worker node, dump the service backend map with `bpftool map dump name cilium_lb4_services`. Locate the entry matching the ClusterIP and port 80—the value field contains a list of backend pod IPs and ports. Verify that the server pod's IP appears in this list. If missing, check the Cilium agent's endpoint synchronization status with `cilium service list` and confirm that the Kubernetes Service and Endpoints objects are correctly reflected in Cilium's internal state. Mismatches indicate API server watch failures or race conditions during endpoint creation.

Measure policy lookup latency by attaching a kprobe to the BPF program's entry point using `perf`. Identify the BPF program's kernel symbol with `bpftool prog show id <PROG_ID> | grep name` which outputs the program's name such as `cil_from_netdev`. Attach a kprobe with `perf probe 'bpf:cil_from_netdev'` followed by `perf record -e probe:cil_from_netdev -a -g -- sleep 10` to collect samples during a 10-second window. Generate traffic from the client pod to saturate the datapath: `kubectl exec -n cilium-test client -- ab -n 10000 -c 10 http://server/`. After the sampling window, analyze the flamegraph with `perf script | stackcollapse-perf.pl | flamegraph.pl > cilium_perf.svg`. The flamegraph visualizes the call stack and CPU time distribution—look for hotspots in `map_lookup_elem`, `__bpf_prog_run`, and `bpf_redirect`. Excessive time in map lookups suggests hash collision issues or oversized maps requiring tuning via `--bpf-ct-global-max-entries` and `--bpf-nat-global-max-entries` Cilium agent flags.

Validate connection tracking state persistence by inspecting the `cilium_ct4_global` map before and after a connection. Initiate a TCP connection from the client pod to the server: `kubectl exec -n cilium-test client -- nc -zv server 80`. Immediately dump the connection tracking map: `bpftool map dump name cilium_ct4_global > ct_before.txt`. Wait 60 seconds for the connection to enter TIME_WAIT and dump again: `bpftool map dump name cilium_ct4_global > ct_after.txt`. Diff the two snapshots with `diff ct_before.txt ct_after.txt` to observe connection state transitions. The entry should persist in TIME_WAIT for the TCP timeout duration (default 60 seconds) before garbage collection removes it. Premature removal indicates aggressive timeout settings or kernel memory pressure forcing early eviction.

Conclude this exercise by verifying Cilium's identity synchronization with etcd. Install `etcdctl` on a control-plane node or configure remote access to the etcd cluster. Export the necessary environment variables: `export ETCDCTL_API=3`, `export ETCDCTL_ENDPOINTS=<ETCD_IP>:2379`, `export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt`, `export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt`, and `export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key`. List all Cilium identity keys with `etcdctl get /cilium/state/identities/ --prefix --keys-only`. Each key follows the pattern `/cilium/state/identities/v1/<IDENTITY_ID>`. Retrieve a specific identity's label set with `etcdctl get /cilium/state/identities/v1/<IDENTITY_ID>` and confirm the labels match the Kubernetes pod's labels. Identity allocation failures often stem from etcd write conflicts under high pod churn—monitor etcd's Raft commit latency with `etcdctl endpoint status --write-out=table` and verify that commit times remain below 10ms under normal load.

## Exercise 2: Benchmarking & Saturation Profiling

Performance validation under saturation conditions exposes Cilium's bottlenecks: CPU-bound BPF execution, memory-constrained map sizes, and packet drops due to insufficient processing capacity. This exercise benchmarks Cilium's datapath throughput, latency distribution, and resource utilization using synthetic traffic generators, kernel-level profilers, and Cilium's built-in metrics exporter. You will stress-test the system to identify the point at which BPF program execution time exceeds the packet arrival rate, causing drops and latency spikes.

Begin by establishing baseline throughput measurements between two pods. Deploy a dedicated iperf3 server pod in the `cilium-test` namespace:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: iperf3-server
  namespace: cilium-test
  labels:
    app: iperf3-server
spec:
  containers:
  - name: iperf3
    image: networkstatic/iperf3:latest
    args: ["-s"]
    ports:
    - containerPort: 5201
      protocol: TCP
---
apiVersion: v1
kind: Service
metadata:
  name: iperf3-server
  namespace: cilium-test
spec:
  selector:
    app: iperf3-server
  ports:
  - protocol: TCP
    port: 5201
    targetPort: 5201
  type: ClusterIP
```

Wait for the server pod to become ready, then initiate a 60-second TCP throughput test from the client pod: `kubectl exec -n cilium-test client -- iperf3 -c iperf3-server -t 60 -P 10`. The `-P 10` flag spawns 10 parallel TCP streams to saturate the datapath. Observe the reported throughput in Gbps and note the CPU utilization on the worker nodes using `kubectl top nodes`. For clusters without metrics-server, SSH into the node and use `top` or `htop` to monitor CPU cores. Cilium's BPF datapath is CPU-bound—throughput scales linearly with available CPU cycles until map lookup latency or packet processing overhead dominates.

Capture packet-level statistics during the iperf3 run to quantify drop rates. On the node hosting the iperf3-server pod, identify the pod's network interface using `crictl inspect <CONTAINER_ID> | jq .info.pid` to obtain the process ID, then `ip netns identify <PID>` to get the network namespace. Use `ip netns exec <NAMESPACE> ip -s link show eth0` to display interface statistics including `RX packets`, `TX packets`, `RX dropped`, and `TX dropped`. A non-zero drop count under saturation indicates insufficient BPF processing capacity—the kernel is discarding packets faster than Cilium can render policy verdicts. Compare drop rates against the node's NIC ring buffer size with `ethtool -g <HOST_INTERFACE>` where `<HOST_INTERFACE>` is the physical NIC (e.g., `eth0`, `ens3`). Increase the ring buffer if the pre-set maximum allows: `ethtool -G <HOST_INTERFACE> rx 4096 tx 4096`.

Profile BPF execution overhead using `perf` to measure cycles consumed per packet. Attach to all CPUs with `perf stat -e cycles,instructions,cache-references,cache-misses -a -- sleep 30` while running the iperf3 benchmark. The output reports total CPU cycles, instructions retired, cache references, and cache misses. Calculate instructions per cycle (IPC) as `instructions / cycles`—an IPC below 1.0 indicates memory stalls, likely from BPF map lookups suffering cache misses. Cilium's connection tracking and policy maps can grow large under high connection churn, fragmenting across multiple cache lines. Tune map sizes via the Cilium agent's `--bpf-ct-global-max-entries` flag to balance memory overhead and lookup performance. For example, reducing from the default 524288 entries to 131072 entries decreases memory footprint at the cost of earlier connection eviction.

Measure per-packet latency distribution with timestamping. Deploy a custom latency measurement tool using the `sockperf` utility from the client pod. First, extend the client pod to include sockperf by replacing the netshoot image with a custom container:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: latency-client
  namespace: cilium-test
  labels:
    app: latency-client
spec:
  containers:
  - name: sockperf
    image: mellanox/sockperf:latest
    command: ["sleep", "infinity"]
    securityContext:
      capabilities:
        add: ["NET_ADMIN"]
```

Launch a sockperf server on the iperf3-server pod: `kubectl exec -n cilium-test iperf3-server -- sockperf sr --tcp -p 5001`. From the latency-client pod, run a ping-pong latency test: `kubectl exec -n cilium-test latency-client -- sockperf pp --tcp -i iperf3-server -p 5001 -t 60`. The output reports min, max, average, and percentile latencies (p50, p90, p99, p99.9). Under no load, expect p99 latencies below 100 microseconds on modern hardware. Under concurrent iperf3 saturation, p99 latencies may spike to milliseconds—this inflation comes from CPU contention between BPF program execution and userspace application processing.

Isolate BPF-specific latency by tracing the `bpf_prog_run` kernel function with `bpftrace`. Install bpftrace if not present: `apt-get install bpftrace` on Ubuntu or `yum install bpftrace` on RHEL. Execute the following script to histogram BPF program execution times:

```bash
#!/usr/bin/env bpftrace

kprobe:bpf_prog_run
{
    @start[tid] = nsecs;
}

kretprobe:bpf_prog_run
/@start[tid]/
{
    @exec_time = hist(nsecs - @start[tid]);
    delete(@start[tid]);
}

interval:s:10
{
    print(@exec_time);
    clear(@exec_time);
}
```

Save this as `bpf_latency.bt` and run `bpftrace bpf_latency.bt` while the iperf3 benchmark is active. Every 10 seconds, bpftrace prints a histogram of BPF execution times in nanoseconds. Look for the distribution—median execution times should remain under 5 microseconds. A heavy tail extending into tens of microseconds indicates map lookup contention or excessive program complexity. Simplify NetworkPolicies to reduce the number of BPF instructions, or enable Cilium's host firewall mode to offload policy enforcement to iptables for specific workloads.

Stress-test Cilium's connection tracking capacity by simulating high connection churn. Use the `wrk` HTTP load generator from the client pod to spawn thousands of short-lived connections: `kubectl exec -n cilium-test client -- wrk -t 10 -c 1000 -d 60s http://server`. The `-c 1000` flag creates 1000 concurrent connections, each making rapid HTTP requests. Monitor connection tracking map occupancy with `bpftool map dump name cilium_ct4_global | wc -l` in a loop: `watch -n 1 "bpftool map dump name cilium_ct4_global | wc -l"`. If the count approaches the configured maximum (default 524288), connections will be dropped to prevent map overflow. Increase the limit by editing the Cilium ConfigMap: `kubectl edit cm cilium-config -n kube-system`, add `bpf-ct-global-max-entries: "1048576"`, and restart the Cilium agents.

Evaluate Cilium's policy enforcement overhead by comparing throughput with and without NetworkPolicies. First, measure baseline throughput without policies: `kubectl exec -n cilium-test client -- iperf3 -c iperf3-server -t 30 -P 5` and record the result. Next, apply a restrictive NetworkPolicy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: server-policy
  namespace: cilium-test
spec:
  podSelector:
    matchLabels:
      app: server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: client
    ports:
    - protocol: TCP
      port: 80
```

Wait 10 seconds for Cilium to recompile and reload the BPF programs, then re-run the iperf3 test. Observe any throughput degradation—policy enforcement typically imposes a 5-10% overhead due to additional map lookups and identity checks. A drop exceeding 20% suggests inefficient policy compilation or excessive rule complexity. Review the policy with `kubectl exec -n kube-system <CILIUM_POD> -- cilium policy get` and simplify overly broad selectors or redundant rules.

Saturate Cilium's DNS proxy by flooding DNS queries. Cilium intercepts DNS requests to enforce FQDN-based policies via an in-agent DNS proxy. Deploy a DNS query generator:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-client
  namespace: cilium-test
  labels:
    app: dns-client
spec:
  containers:
  - name: dnsperf
    image: ns1labs/dnsperf:latest
    command: ["sleep", "infinity"]
```

Create a query file containing 10000 random domain lookups: `kubectl exec -n cilium-test dns-client -- sh -c 'for i in $(seq 1 10000); do echo "test$i.example.com A"; done > /tmp/queries.txt'`. Run dnsperf to flood the DNS proxy: `kubectl exec -n cilium-test dns-client -- dnsperf -d /tmp/queries.txt -s <CLUSTER_DNS_IP> -c 100 -l 60` where `<CLUSTER_DNS_IP>` is typically `10.96.0.10` (retrieve with `kubectl get svc kube-dns -n kube-system -o jsonpath='{.spec.clusterIP}'`). Monitor the Cilium agent's CPU usage during the flood—DNS proxy processing occurs in userspace, consuming agent CPU proportionally to query rate. If CPU usage exceeds 80%, consider disabling the DNS proxy for non-FQDN workloads by setting `--disable-cnp-status-updates=true` in the agent configuration.

Verify that Cilium's metrics exporter correctly reports datapath statistics. Cilium exposes Prometheus metrics on port 9090 of each agent pod. Forward the port to your local machine: `kubectl port-forward -n kube-system <CILIUM_POD> 9090:9090`. Query key metrics with `curl localhost:9090/metrics | grep cilium_datapath`. Focus on `cilium_datapath_errors_total` (packet drop counters), `cilium_forward_count_total` (successful forwards), and `cilium_policy_verdict_total` (policy allow/deny counts). A high error rate correlates with the drop counts observed earlier via `ip -s link`. Cross-reference error types—drops labeled `unknown` indicate unidentified traffic not matching any endpoint, while `policy_denied` confirms explicit NetworkPolicy blocks.

Conclude the benchmarking phase by generating a comprehensive performance report. Collect the following metrics: iperf3 throughput (Gbps), sockperf p99 latency (microseconds), connection tracking map size (entries), BPF execution histogram median (nanoseconds), CPU utilization (percent), and packet drop rate (percent). Document any configuration changes applied to mitigate bottlenecks—increased map sizes, ring buffer tuning, or policy simplifications. This baseline serves as the reference for detecting performance regressions after Cilium upgrades or NetworkPolicy modifications.

## Exercise 3: Fault Injection & Recovery Analysis

Production resilience demands validating Cilium's behavior under failure conditions: agent crashes, network partitions, BPF program load failures, and kernel resource exhaustion. This exercise injects deliberate faults into the system, monitors failure propagation, and verifies automatic recovery mechanisms including BPF program regeneration, endpoint state reconciliation, and connection tracking failover.

Start by simulating a Cilium agent crash. Identify an agent pod running on a worker node hosting active workloads: `kubectl get pods -n kube-system -l k8s-app=cilium -o wide`. Delete the pod to trigger a crash: `kubectl delete pod -n kube-system <CILIUM_POD>`. Kubernetes immediately schedules a replacement pod via the DaemonSet. Monitor the new pod's startup with `kubectl logs -n kube-system <NEW_CILIUM_POD> -f`. Observe the initialization sequence: BPF filesystem mount, identity allocation synchronization from etcd, endpoint discovery from the Kubernetes API, BPF program compilation, and datapath activation. Startup typically completes within 30 seconds on modern hardware.

During the agent crash window, verify that existing connections remain functional. From the client pod, maintain a persistent TCP connection to the server: `kubectl exec -n cilium-test client -- sh -c 'while true; do curl -s http://server && sleep 1; done'`. The connection should continue forwarding packets without interruption because BPF programs remain loaded in the kernel even after the userspace agent process dies. Packet forwarding is stateless—the kernel executes the compiled BPF bytecode independently of the agent. However, new connection establishment during the crash window will fail if the agent is unavailable to process SYN packets requiring policy lookups against stale or missing identity state.

Test connection tracking failover by exhausting the connection tracking map. Lower the map size to accelerate exhaustion: edit the Cilium ConfigMap to set `bpf-ct-global-max-entries: "1024"` and restart the agents. From the client pod, spawn a flood of connections using `wrk`: `kubectl exec -n cilium-test client -- wrk -t 10 -c 2000 -d 60s http://server`. Monitor the connection tracking map occupancy: `watch -n 1 "bpftool map dump name cilium_ct4_global | wc -l"`. When the map reaches 1024 entries, Cilium's garbage collector begins evicting the oldest entries to make room for new connections. Check the Cilium agent logs for eviction events: `kubectl logs -n kube-system <CILIUM_POD> | grep -i "conntrack table full"`. Evicted connections terminate abruptly—the client receives RST packets. This behavior is expected under extreme conditions but indicates a need for capacity planning: monitor map occupancy in production and scale the `bpf-ct-global-max-entries` parameter proportionally to peak connection rates.

Inject a BPF program load failure by corrupting the Cilium agent's BPF object file cache. SSH into a worker node and locate the BPF object cache directory: `ls /var/run/cilium/state/templates/`. This directory contains compiled BPF ELF binaries for each endpoint. Corrupt one file by writing random data: `dd if=/dev/urandom of=/var/run/cilium/state/templates/bpf_lxc.o bs=1024 count=1 conv=notrunc`. Trigger endpoint regeneration by deleting and recreating the client pod: `kubectl delete pod client -n cilium-test && kubectl apply -f client-pod.yaml`. The Cilium agent attempts to load the corrupted BPF program and fails with a verifier error. Retrieve the error from agent logs: `kubectl logs -n kube-system <CILIUM_POD> | grep -A 20 "BPF verification failed"`. The kernel verifier rejects invalid bytecode—common errors include unreachable instructions, unbounded loops, or invalid register states. The agent automatically falls back to recompiling the BPF program from source templates stored in `/opt/cilium/`. Verify recovery by checking endpoint status: `kubectl exec -n kube-system <CILIUM_POD> -- cilium endpoint list` should show the client pod with `ready` status after recompilation completes.

Simulate network partition between the Cilium agent and the Kubernetes API server. Use iptables to block API server communication on a worker node: `iptables -A OUTPUT -d <API_SERVER_IP> -p tcp --dport 6443 -j DROP` where `<API_SERVER_IP>` is the control-plane IP (retrieve with `kubectl cluster-info | grep control-plane`). The Cilium agent loses connectivity to the API server, preventing endpoint discovery and identity synchronization. Monitor the agent's status: `kubectl exec -n kube-system <CILIUM_POD> -- cilium status` now reports `Kubernetes: Unavailable`. However, existing endpoints continue forwarding traffic because BPF programs operate independently of API server connectivity. The agent caches endpoint state locally in `/var/run/cilium/state/` and continues enforcing policies based on the last-known identity mappings. New pod creations on the partitioned node fail to receive network connectivity because the agent cannot allocate identities without etcd access.

Verify identity allocation resilience by partitioning the agent from etcd. Block etcd communication: `iptables -A OUTPUT -d <ETCD_IP> -p tcp --dport 2379 -j DROP`. The agent reports `KVStore: Unavailable` in its status output. Identity allocation requests fail, causing new endpoint creation to stall. Existing endpoints remain functional, but label changes on pods trigger regeneration failures. Check the agent logs for identity allocation errors: `kubectl logs -n kube-system <CILIUM_POD> | grep -i "identity allocation failed"`. Remove the iptables rule to restore connectivity: `iptables -D OUTPUT -d <ETCD_IP> -p tcp --dport 2379 -j DROP`. The agent automatically reconnects to etcd and resynchronizes identity state within seconds. Verify recovery by deploying a new test pod and confirming it receives network connectivity.

Inject a kernel-level BPF map update failure by filling the system's BPF map memory quota. Linux enforces per-user limits on BPF map memory via `RLIMIT_MEMLOCK`. Lower the limit artificially: `ulimit -l 64` (sets the limit to 64 KB). As the Cilium agent, running as root, attempts to create large BPF maps, the kernel returns `ENOMEM` errors. The agent logs the failure: `kubectl logs -n kube-system <CILIUM_POD> | grep "failed to create BPF map"`. Cilium cannot operate without its core maps—the agent enters a crash loop. Restore the memory limit by editing the systemd service file for containerd or the Kubernetes kubelet, adding `LimitMEMLOCK=infinity` under the `[Service]` section, then reloading systemd: `systemctl daemon-reload && systemctl restart containerd kubelet`. The agent recovers and successfully loads BPF maps. This failure mode highlights the importance of system-level BPF resource limits—ensure production nodes have adequate `RLIMIT_MEMLOCK` capacity to accommodate Cilium's memory footprint, typically 512 MB to 2 GB depending on cluster scale.

Test Cilium's response to BPF verifier rejections due to kernel version incompatibility. Deploy Cilium on a node running an outdated kernel (e.g., Linux 4.14). The agent attempts to load BPF programs using features unavailable in older kernels, such as bounded loops or BPF-to-BPF calls. The verifier rejects the program with errors like "back-edge in program" or "function calls are not supported". Retrieve the full verifier log: `kubectl logs -n kube-system <CILIUM_POD> | grep -A 100 "Verifier log"`. Cilium's fallback mechanism disables advanced features and recompiles a legacy-compatible BPF program. Confirm successful fallback by checking endpoint status—the endpoint should reach `ready` state despite the verifier rejection, though with degraded performance (e.g., no connection tracking, reduced policy expressiveness). For production deployments, mandate kernel versions 5.10 or newer to avoid feature degradation.

Validate Cilium's behavior during node-level resource exhaustion. Consume all available CPU cores on a worker node using a stress container:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cpu-stress
  namespace: cilium-test
spec:
  containers:
  - name: stress
    image: polinux/stress:latest
    args: ["--cpu", "16", "--timeout", "300s"]
    resources:
      requests:
        cpu: "16"
      limits:
        cpu: "16"
```

Apply the manifest and monitor packet drop rates on the stressed node: `ip -s link show <HOST_INTERFACE>`. As CPU cores saturate, BPF programs compete with the stress workload for execution time. Packet processing latency increases, leading to drops when the NIC's ring buffer overflows. Cilium's control plane (the agent) also suffers—policy compilation and endpoint regeneration slow significantly. Measure agent responsiveness by timing an endpoint regeneration command: `time kubectl exec -n kube-system <CILIUM_POD> -- cilium endpoint regenerate <ENDPOINT_ID>`. Under normal conditions, regeneration completes in under 5 seconds. Under CPU saturation, it may exceed 30 seconds. Delete the stress pod to restore normal operation: `kubectl delete pod cpu-stress -n cilium-test`. Packet drops cease and agent responsiveness returns. This scenario underscores the importance of reserving CPU capacity for system components via Kubernetes resource reservations and cgroup limits.

Conclude the fault injection exercise by validating Cilium's full-cluster recovery from a catastrophic etcd failure. Simulate etcd data loss by scaling the etcd StatefulSet to zero replicas (in a test cluster only): `kubectl scale statefulset etcd -n kube-system --replicas=0`. The Cilium agents lose access to identity and policy state. All endpoints enter `not-ready` state as identity allocations expire. Restore etcd by scaling back to three replicas: `kubectl scale statefulset etcd -n kube-system --replicas=3`. Wait for etcd quorum re-establishment: `etcdctl endpoint status --write-out=table`. The Cilium agents automatically reconnect, but identity state is lost—all identities must be reallocated. Force global regeneration across all endpoints: `kubectl exec -n kube-system ds/cilium -- cilium endpoint regenerate --all`. Monitor recovery progress: `kubectl exec -n kube-system <CILIUM_POD> -- cilium endpoint list` should show all endpoints returning to `ready` state over several minutes. Test end-to-end connectivity: `kubectl exec -n cilium-test client -- curl http://server`. Successful responses confirm full recovery. This exercise demonstrates Cilium's stateful dependency on etcd—production deployments must implement etcd backups and disaster recovery procedures to prevent identity state loss.

## Diagnostic Cheat Sheet & Verification Checklist

The following command reference consolidates the critical diagnostic operations covered in this lab series. Integrate these workflows into your operational runbooks for rapid troubleshooting during production incidents.

**Endpoint State Inspection:**
Enumerate all Cilium-managed endpoints with `kubectl exec -n kube-system ds/cilium -- cilium endpoint list`. For detailed inspection of a specific endpoint, query its full state via `kubectl exec -n kube-system ds/cilium -- cilium endpoint get <ENDPOINT_ID>`. Correlate endpoint identities with Kubernetes label selectors using `kubectl exec -n kube-system ds/cilium -- cilium identity list`. If an endpoint shows stale policy or identity mismatches, force regeneration with `kubectl exec -n kube-system ds/cilium -- cilium endpoint regenerate <ENDPOINT_ID>`.

**BPF Program Enumeration:**
List all BPF programs loaded on a node with `bpftool prog list`. Identify programs attached to specific network interfaces using `bpftool net show`. Extract detailed program metadata including instruction count and JIT status via `bpftool prog show id <PROG_ID>`. Dump human-readable bytecode with `bpftool prog dump xlated id <PROG_ID> linum`. For performance analysis, trace BPF execution latency with the bpftrace script provided in Exercise 2.

**BPF Map Inspection:**
Enumerate all BPF maps with `bpftool map list`. Dump connection tracking state using `bpftool map dump name cilium_ct4_global`. Monitor map occupancy in real-time via `watch -n 1 "bpftool map dump name cilium_ct4_global | wc -l"`. Inspect service load balancing backend mappings with `bpftool map dump name cilium_lb4_services`. If maps approach capacity limits, adjust thresholds in the Cilium ConfigMap (`bpf-ct-global-max-entries`, `bpf-nat-global-max-entries`) and restart agents.

**Policy Verdict Tracing:**
Monitor real-time policy decisions with `kubectl exec -n kube-system <CILIUM_POD> -- cilium monitor -t policy-verdict`. For persistent logging, enable debug mode on the Cilium agent by adding `--debug` to the DaemonSet arguments and tailing logs with `kubectl logs -n kube-system <CILIUM_POD> --tail=1000 | grep policy`. Validate policy compilation by retrieving the active policy set: `kubectl exec -n kube-system <CILIUM_POD> -- cilium policy get`.

**Network Interface Statistics:**
Capture packet and drop counters for a pod's network interface by first identifying the namespace (`crictl inspect <CONTAINER_ID> | jq .info.pid` then `ip netns identify <PID>`), then querying the interface: `ip netns exec <NAMESPACE> ip -s link show eth0`. For host-side statistics, inspect the corresponding `lxc<HASH>` interface with `ip -s link show <LXC_INTERFACE>`. Compare drop rates against NIC ring buffer capacity using `ethtool -g <HOST_NIC>` and tune with `ethtool -G <HOST_NIC> rx 4096 tx 4096`.

**Throughput & Latency Benchmarking:**
Measure TCP throughput between pods with `kubectl exec -n cilium-test client -- iperf3 -c iperf3-server -t 60 -P 10`. Assess latency distribution using `kubectl exec -n cilium-test latency-client -- sockperf pp --tcp -i iperf3-server -p 5001 -t 60`. Profile CPU overhead during saturation with `perf stat -e cycles,instructions,cache-references,cache-misses -a -- sleep 30` while traffic generators run. Analyze BPF execution hotspots via flamegraphs generated from `perf record` sessions.

**Cilium Metrics Collection:**
Forward the Cilium agent's Prometheus endpoint to your local machine: `kubectl port-forward -n kube-system <CILIUM_POD> 9090:9090`. Query key datapath metrics with `curl localhost:9090/metrics | grep cilium_datapath`. Focus on `cilium_datapath_errors_total` for drop counts, `cilium_forward_count_total` for successful forwards, and `cilium_policy_verdict_total` for policy enforcement statistics. Integrate these metrics into your monitoring stack (Prometheus, Grafana) for continuous visibility.

**Connection Tracking Health:**
Verify connection tracking map health by dumping entries before and after connection establishment, diffing the snapshots to observe state transitions. Ensure entries persist for appropriate timeout durations (TCP TIME_WAIT = 60s, UDP idle = 60s). If connections disappear prematurely, check for aggressive garbage collection settings or kernel memory pressure. Tune timeout parameters via `--bpf-ct-tcp-timeout-time-wait` and `--bpf-ct-udp-timeout` Cilium agent flags.

**Identity Synchronization Validation:**
Confirm identity allocations are correctly persisted in etcd by querying the keyspace: `etcdctl get /cilium/state/identities/ --prefix --keys-only`. Retrieve specific identity labels with `etcdctl get /cilium/state/identities/v1/<IDENTITY_ID>`. Cross-reference against the Cilium agent's in-memory cache: `kubectl exec -n kube-system <CILIUM_POD> -- cilium identity list`. Mismatches indicate synchronization failures—force re-sync by restarting the agent: `kubectl delete pod -n kube-system <CILIUM_POD>`.

**Fault Injection & Recovery:**
Simulate agent crashes by deleting pods: `kubectl delete pod -n kube-system <CILIUM_POD>`. Verify that existing connections remain functional during the crash window and new connections establish after agent restart. Test network partitions by blocking API server or etcd connectivity with iptables: `iptables -A OUTPUT -d <IP> -p tcp --dport <PORT> -j DROP`. Confirm the agent caches endpoint state locally and continues forwarding traffic despite control-plane disconnection. Restore connectivity by removing the iptables rule: `iptables -D OUTPUT -d <IP> -p tcp --dport <PORT> -j DROP`.

**Kernel Compatibility Checks:**
Validate kernel version with `uname -r`—Cilium requires Linux 4.19 minimum, 5.10+ recommended. Confirm BPF subsystem support by checking kernel config: `zgrep BPF /proc/config.gz` should return `CONFIG_BPF_SYSCALL=y`, `CONFIG_BPF_JIT=y`, `CONFIG_CGROUP_BPF=y`, and `CONFIG_BPF_EVENTS=y`. Verify BPF memory limits allow Cilium's map footprint: `ulimit -l` should report `unlimited` or a value exceeding 524288 KB. Adjust via systemd service files if necessary.

**Verification Checklist:**
Before declaring a Cilium deployment production-ready, confirm the following: (1) All Cilium agent pods are `Running` with zero restarts. (2) `cilium status` reports all components `Ok` on every node. (3) Endpoint list shows all pods with `ready` status and correct identity assignments. (4) BPF programs are successfully loaded (`bpftool prog list` shows non-zero program IDs). (5) Connection tracking maps are not approaching capacity limits. (6) Policy verdicts log expected allow/deny decisions. (7) Throughput benchmarks meet application SLAs (target 10 Gbps or higher on modern NICs). (8) Latency p99 remains below 100 microseconds under normal load. (9) Packet drop rates are zero under typical traffic patterns. (10) Cilium metrics are exported to your monitoring system and alerting rules are configured. (11) Fault injection tests confirm recovery within SLA windows (agent crash recovery < 30s, network partition recovery < 60s). (12) Identity synchronization with etcd is stable with no allocation failures in logs. (13) Kernel version meets minimum requirements and BPF subsystem is fully enabled. (14) Documentation is updated with cluster-specific tuning parameters and known limitations.

This diagnostic framework transforms abstract Cilium architecture into measurable, actionable operational practices. By mastering these tools and workflows, you gain the precision required to operate Cilium at scale—identifying performance bottlenecks before they degrade user experience, troubleshooting policy enforcement failures through BPF map inspection, and validating resilience through controlled fault injection. The kernel-level visibility provided by bpftool, perf, and bpftrace elevates your diagnostic capability beyond surface-level Kubernetes abstractions, exposing the raw packet processing mechanics that determine whether your service mesh meets its latency and throughput SLAs.
