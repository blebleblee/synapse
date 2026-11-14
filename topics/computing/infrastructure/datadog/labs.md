# Operational Verification Labs: Datadog

## Objective & Environment Setup

Datadog represents a modern observability platform that aggregates metrics, traces, and logs from distributed infrastructure through a unified agent architecture. In production environments, the Datadog Agent operates as a privileged daemon that collects telemetry from kernel subsystems, container runtimes, and application processes, then forwards this data to Datadog's backend via HTTPS. Understanding how to verify the agent's operational state, diagnose collection pipeline failures, and validate metric accuracy requires deep familiarity with Linux process instrumentation, network socket state machines, and container runtime interfaces.

This laboratory guide grounds Datadog verification in first-principles systems engineering. You will inspect the agent's internal HTTP server endpoints, trace metric collection paths through kernel interfaces, profile the agent's resource consumption under load, inject network and container runtime failures, and validate recovery behaviors. Each exercise builds toward complete operational mastery: the ability to diagnose agent outages, optimize collection overhead, and ensure reliable telemetry pipelines in multi-tenant Kubernetes clusters.

Before beginning these exercises, establish a representative test environment. Deploy a Kubernetes cluster with at least three worker nodes running kernel version 5.10 or newer to ensure modern eBPF support. Install the Datadog Agent as a DaemonSet using the official Helm chart, configuring it with a valid API key and enabling the cluster agent for orchestrator metrics. Ensure your workstation has `kubectl`, `crictl`, `ss`, `tcpdump`, `perf`, `strace`, and `bpftool` installed. The Datadog Agent exposes internal diagnostics on port 5000 by default; verify network policies permit pod-to-pod communication on this port. For container runtime inspection, configure `crictl` to communicate with your containerd or CRI-O socket, typically located at `/run/containerd/containerd.sock` or `/run/crio/crio.sock`. Finally, deploy several representative workloads—such as an Nginx pod, a Redis StatefulSet, and a batch Job—to generate diverse telemetry streams for verification.

The Datadog Agent's architecture partitions responsibilities across multiple processes. The core agent process collects infrastructure metrics via integrations called checks, manages configuration, and communicates with the Datadog backend. The trace agent receives APM spans from instrumented applications, performs sampling and aggregation, then forwards enriched traces. The process agent collects live process tables and container metadata. The system-probe runs as a privileged sidecar, using eBPF programs to capture network flows and security events at the kernel level. Understanding this process topology and the communication channels between components forms the foundation for systematic verification.

## Exercise 1: Live State & Internal Subsystem Inspection

Begin by confirming the Datadog Agent's runtime topology within your Kubernetes cluster. Execute `kubectl get pods -n datadog -o wide` to enumerate all agent pods across worker nodes. Each node should host exactly one agent pod in Running state with all containers ready. Note the pod names and their assigned nodes; you will reference these throughout the lab. For a specific agent pod, drill into its multi-container structure with `kubectl get pod <agent-pod-name> -n datadog -o jsonpath='{.spec.containers[*].name}'`. You should observe containers named `agent`, `trace-agent`, `process-agent`, and `system-probe`, each with distinct lifecycle responsibilities.

The core agent process exposes a comprehensive diagnostics HTTP server on port 5000 that surfaces internal state without requiring external API calls. Establish a port-forward tunnel to this endpoint with `kubectl port-forward -n datadog <agent-pod-name> 5000:5000`, then query the status endpoint from your workstation using `curl http://localhost:5000/agent/status`. This endpoint returns a multi-section plain-text report detailing the agent version, runtime configuration, active checks, and forwarder state. Parse this output carefully. The `Agent (v7.x.x)` header confirms the deployed version. The `Hostname` field reveals the node's canonical identifier used to tag all metrics. The `Forwarder` section displays API connectivity state, showing the number of successful transactions and any retry queue depths. A healthy forwarder reports `API Keys status: API key ending with xxxxx: API Key valid` and zero retries in the queue. If you observe `Error` states or growing retry queues, investigate network connectivity to Datadog intake endpoints or API key validity.

Scroll through the status output to the `Collector` section, which enumerates all active checks and their execution states. Each check corresponds to an integration—such as `cpu`, `disk`, `network`, `kubelet`, or custom application checks—and reports its last execution status, metric count, and any error messages. A properly functioning check displays `Instance #0 [OK]` with a recent timestamp and a non-zero metric count. When a check fails, the error message often pinpoints the root cause: permission denials indicate missing RBAC bindings, connection timeouts suggest misconfigured service endpoints, and authentication errors point to invalid credentials in the check configuration. For example, the `kubelet` check must successfully query the node's kubelet API on port 10250 with bearer token authentication; failures here often stem from expired certificates or restrictive PodSecurityPolicies.

To inspect metric collection at the kernel interface level, examine the agent's interaction with the `/proc` and `/sys` pseudo-filesystems. Execute `kubectl exec -n datadog <agent-pod-name> -c agent -- ls -la /proc` to verify the agent container can access the host's process table. The presence of subdirectories numbered by PID confirms proper PID namespace configuration; the agent must run in the host PID namespace (specified via `hostPID: true` in the DaemonSet spec) to collect process-level metrics. Similarly, check `/sys/class/net` access with `kubectl exec -n datadog <agent-pod-name> -c agent -- ls /sys/class/net`, which should list all network interfaces on the host node. The agent reads interface statistics from files like `/sys/class/net/eth0/statistics/rx_bytes` to emit network throughput metrics. If these directories are missing or empty, the agent's volume mounts are misconfigured; verify that the DaemonSet mounts the host's `/proc` and `/sys` filesystems as read-only volumes.

Network connectivity between the agent and Datadog intake endpoints represents a critical dependency. The agent forwards metrics to `https://api.datadoghq.com` (or regional equivalents like `datadoghq.eu`) using HTTPS on port 443. Inspect active TCP connections from the agent process with `kubectl exec -n datadog <agent-pod-name> -c agent -- ss -tnp`. Look for ESTABLISHED connections to remote addresses on port 443; these represent active metric forwarder sessions. The output format `ESTAB 0 0 10.244.1.5:54321 34.98.72.45:443 users:(("agent",pid=1234,fd=7))` confirms that the `agent` process maintains an open socket to Datadog's backend. If no such connections exist, perform DNS resolution checks with `kubectl exec -n datadog <agent-pod-name> -c agent -- nslookup api.datadoghq.com` to rule out DNS failures, then test raw TCP connectivity with `kubectl exec -n datadog <agent-pod-name> -c agent -- nc -zv api.datadoghq.com 443`. Corporate firewalls and egress network policies frequently block these connections; resolution requires explicit allow rules for Datadog's IP ranges.

The trace agent operates as a separate process within the same pod, listening on port 8126 for incoming APM spans from instrumented applications. Verify the trace agent's listener state with `kubectl exec -n datadog <agent-pod-name> -c trace-agent -- ss -tlnp | grep 8126`. You should observe a LISTEN socket bound to `0.0.0.0:8126` or `[::]:8126`, indicating readiness to accept connections from any pod IP. If the listener is absent, the trace agent has failed to start; inspect its logs with `kubectl logs -n datadog <agent-pod-name> -c trace-agent` for initialization errors such as port conflicts or configuration parsing failures. To validate end-to-end trace ingestion, deploy a simple instrumented application. For example, run a Python Flask app with `ddtrace-run` that sends spans to `http://<node-ip>:8126`. After generating traffic, query the trace agent's internal stats endpoint with `kubectl exec -n datadog <agent-pod-name> -c trace-agent -- curl http://localhost:8126/debug/stats` to confirm non-zero span reception counts.

The system-probe container deploys eBPF programs to capture low-level kernel events for Network Performance Monitoring and Cloud Workload Security. Confirm that system-probe has successfully loaded its eBPF programs by inspecting the BPF filesystem. Execute `kubectl exec -n datadog <agent-pod-name> -c system-probe -- bpftool prog list` to enumerate all loaded eBPF programs. Look for entries with names like `netflow_classifier`, `tcp_sendmsg_kprobe`, or `sys_enter_execve`; these correspond to Datadog's network and process monitoring instrumentation. The output format `123: kprobe name tcp_sendmsg_kprobe tag 9a8b7c6d5e4f3210 gpl` confirms successful program attachment. If no Datadog programs appear, the system-probe has failed to load eBPF code, often due to insufficient kernel capabilities (requires `CAP_SYS_ADMIN` and `CAP_BPF` on kernels 5.8+) or kernel version incompatibilities. Validate the container's security context with `kubectl get pod <agent-pod-name> -n datadog -o jsonpath='{.spec.containers[?(@.name=="system-probe")].securityContext}'`; it must specify `privileged: true` or the necessary capability grants.

For deeper eBPF verification, inspect the maps that system-probe uses to store collected data. Execute `kubectl exec -n datadog <agent-pod-name> -c system-probe -- bpftool map list` to display all BPF maps. Datadog's network monitoring uses hash maps to track per-connection statistics, keyed by tuples of source/destination IPs and ports. Select a map ID from the list, then dump its contents with `kubectl exec -n datadog <agent-pod-name> -c system-probe -- bpftool map dump id <map-id>`. The output reveals active network flows as key-value pairs, where keys encode connection tuples and values store byte and packet counters. If maps remain empty despite active network traffic, the eBPF programs are attached but not triggering correctly, suggesting a mismatch between kernel function names and kprobe attachment points. This commonly occurs when running outdated agent versions against newer kernels that have renamed internal symbols.

Configuration validation represents another critical inspection path. The Datadog Agent constructs its runtime configuration from multiple sources: environment variables, Kubernetes annotations, ConfigMaps, and Secrets. Retrieve the effective configuration with `kubectl exec -n datadog <agent-pod-name> -c agent -- agent configcheck`. This command parses all configuration sources and displays the resolved settings for each integration check. Review the output for each check to confirm that autodiscovery has correctly matched pod annotations to integration templates. For instance, a Redis pod annotated with `ad.datadoghq.com/redis.check_names: '["redisdb"]'` should appear in the configcheck output with the full `redisdb` check configuration, including the correct connection host and port. Misconfigurations often arise from typos in annotation keys, incorrect YAML escaping, or missing required parameters like authentication credentials.

The agent also maintains internal metrics about its own performance, accessible via the `agent status` output's `Aggregator` section. This section reports metrics such as the number of series flushed per interval, aggregation overhead, and memory usage. Pay particular attention to the `Metrics processed` counter, which should increase steadily with each flush interval (default 15 seconds). If this counter stagnates while checks report successful execution, the aggregator has stalled, typically due to extreme cardinality explosions that exhaust internal buffers. The `Number of times a flush could not complete` counter tracks aggregator overruns; non-zero values indicate that the agent cannot serialize metrics fast enough to keep pace with collection volume, necessitating check tuning or instance scaling.

Finally, validate that the agent correctly resolves its hostname, which serves as the primary tag for all emitted metrics. The agent determines hostname through a precedence chain: explicit `DD_HOSTNAME` environment variable, cloud provider metadata APIs, kernel hostname, and finally DNS reverse lookup. Query the resolved hostname with `kubectl exec -n datadog <agent-pod-name> -c agent -- agent hostname`. The output should match the node's Kubernetes name, ensuring that metrics aggregate correctly in the Datadog UI. Hostname mismatches fragment metric timeseries across multiple artificial hosts, complicating dashboard construction and alerting. If the hostname does not align with expectations, override it explicitly via the `DD_HOSTNAME` environment variable in the DaemonSet configuration, or adjust the hostname resolution method using the `hostname_fqdn` config option.

## Exercise 2: Benchmarking & Saturation Profiling

Operational verification extends beyond functional correctness to performance characterization under load. The Datadog Agent's resource footprint scales with the number of monitored integrations, metric cardinality, and telemetry volume. Systematic profiling reveals whether the agent can sustain production workloads without degrading node performance or dropping metrics. This exercise guides you through CPU and memory benchmarking, network throughput measurement, and identification of saturation thresholds.

Begin by establishing baseline resource consumption for an idle agent. Deploy a minimal cluster with the Datadog Agent but no application workloads. Allow the agent to stabilize for several minutes, then capture its resource usage with `kubectl top pod -n datadog`. Note the CPU and memory figures for each agent pod; a typical idle agent consumes 50-150 millicores of CPU and 200-400 MiB of memory. These baselines depend on the number of enabled checks and the node's hardware specifications. Next, inspect per-container resource usage with `kubectl exec -n datadog <agent-pod-name> -- ps aux`. The output reveals the relative resource demands of the core agent, trace-agent, process-agent, and system-probe processes. The core agent typically dominates CPU usage due to check execution and metric aggregation, while system-probe claims the most memory for eBPF map storage.

To profile the agent under realistic load, deploy a representative application suite. Create a namespace with 50 pods running varied workloads: web servers, databases, message queues, and batch jobs. Ensure these pods emit diverse telemetry: high-cardinality custom metrics via DogStatsD, distributed traces via the trace agent, and log streams to stdout. Annotate each pod with autodiscovery templates to activate Datadog's integrations, such as `nginx`, `postgres`, `redis`, and `kafka`. Allow this environment to generate traffic for 10-15 minutes to warm up metric aggregation buffers and establish steady-state operation. During this period, the agent's CPU and memory usage will climb as it discovers new checks, builds aggregation contexts, and buffers outbound payloads.

After the warm-up phase, measure the agent's sustained resource consumption. Execute `kubectl top pod -n datadog --containers` to retrieve per-container metrics. Compare these figures against the idle baseline to quantify the marginal cost of monitoring your workload. A well-tuned agent should exhibit near-linear scaling: doubling the number of monitored pods approximately doubles resource usage. If you observe super-linear growth or sudden spikes, investigate metric cardinality explosions. The agent aggregates metrics by unique tag combinations; a single misbehaving integration that generates unbounded tag values (for example, including timestamps or UUIDs in tags) can inflate memory usage by orders of magnitude. Query the agent's internal cardinality metrics with `kubectl exec -n datadog <agent-pod-name> -c agent -- curl http://localhost:5000/agent/tagger-list` to enumerate all known tags and their propagation to metrics.

Network throughput represents another critical dimension. The agent batches metrics into compressed payloads and forwards them to Datadog intake endpoints every 15 seconds by default. Measure the outbound traffic rate with `kubectl exec -n datadog <agent-pod-name> -c agent -- ss -ti | grep api.datadoghq.com`. The `ss -ti` output includes TCP_INFO statistics for each connection, displaying metrics like `bytes_sent`, `cwnd` (congestion window), and `rtt` (round-trip time). Record the `bytes_sent` value, wait precisely 60 seconds, then query again to compute the average throughput in bytes per second. Divide by 1024 to convert to kilobytes per second. A typical agent forwards 10-50 KB/s per node under moderate workload, scaling with metric volume. If throughput approaches the node's egress bandwidth limit, consider enabling additional compression via the `compression_level` setting or increasing the flush interval to reduce payload frequency.

To stress-test the agent's aggregation capacity, inject a burst of high-cardinality metrics. Deploy a simple DogStatsD client that generates custom metrics with randomized tag values at high frequency. For example, run a Python script that emits 1000 unique metrics per second, each tagged with a random UUID:

```python
import random
import time
from datadog import initialize, statsd

initialize(statsd_host='localhost', statsd_port=8125)

while True:
    for _ in range(1000):
        metric_name = f"stress.test.metric.{random.randint(0, 100)}"
        tag_value = f"uuid:{random.uuid4()}"
        statsd.increment(metric_name, tags=[tag_value])
    time.sleep(1)
```

Execute this script within a pod that has network access to the Datadog Agent's DogStatsD port (UDP 8125). Monitor the agent's memory usage with `kubectl top pod -n datadog --containers` at 30-second intervals. You will observe rapid memory growth as the aggregator buffers each unique metric-tag combination. Eventually, the agent will reach its internal cardinality limit (default 3000 timeseries per context) and begin dropping metrics. Confirm this behavior by checking the `agent status` output for warnings like `Timeseries dropped (too many timeseries)`. This exercise demonstrates the importance of cardinality control: instrumentation code must avoid high-cardinality tags such as user IDs, request paths, or timestamps.

CPU profiling reveals hotspots in the agent's execution. The Datadog Agent is written in Go, which includes a built-in pprof HTTP server for runtime profiling. Enable CPU profiling by setting the `DD_EXPVAR_PORT` environment variable to expose internal metrics on port 5000. Execute `kubectl port-forward -n datadog <agent-pod-name> 5000:5000`, then initiate a 30-second CPU profile with `curl http://localhost:5000/debug/pprof/profile?seconds=30 > agent-cpu.prof`. Transfer this profile to your workstation and analyze it with Go's pprof tool: `go tool pprof -http=:8080 agent-cpu.prof`. The interactive web interface displays a flame graph and call graph, highlighting which functions consume the most CPU time. Common hotspots include metric serialization in the forwarder, check execution in the collector, and tag resolution in the tagger. If a single check dominates the profile, consider reducing its collection frequency or optimizing its implementation.

Memory profiling follows a similar workflow. Capture a heap profile with `curl http://localhost:5000/debug/pprof/heap > agent-heap.prof`, then analyze it with `go tool pprof -http=:8080 agent-heap.prof`. The heap profile reveals which data structures consume the most memory. Pay particular attention to aggregator contexts and check instances; memory leaks in custom checks or integrations often manifest as unbounded growth in these structures. The pprof interface allows you to toggle between absolute allocation sizes and in-use memory, helping distinguish between temporary allocation churn and persistent leaks.

The system-probe's eBPF instrumentation introduces additional performance considerations. eBPF programs execute in the kernel context on every monitored event, such as TCP send/receive or process fork. Excessive event frequency can impose measurable CPU overhead. Quantify this overhead with the `perf` tool, which samples CPU activity and attributes it to specific kernel functions. Execute `perf record -a -g -p $(kubectl exec -n datadog <agent-pod-name> -c system-probe -- pidof system-probe) -- sleep 30` to capture a 30-second profile of the system-probe process and its triggered kernel functions. Analyze the results with `perf report`, focusing on the percentage of time spent in BPF program execution versus native kernel code. If BPF programs account for more than 5% of total CPU time, consider reducing the scope of monitored events via system-probe configuration, such as limiting network monitoring to specific interfaces or disabling unused security features.

Finally, validate the agent's behavior under network saturation. Simulate a network partition by using `iptables` to drop outbound packets to Datadog intake endpoints. Execute `kubectl exec -n datadog <agent-pod-name> -c agent -- iptables -A OUTPUT -d api.datadoghq.com -j DROP` to block egress traffic. Observe the agent's response with `kubectl logs -n datadog <agent-pod-name> -c agent --follow`. The forwarder will log connection failures and begin buffering metrics in its retry queue. Query the retry queue depth with `curl http://localhost:5000/agent/status | grep -A5 "Forwarder"`. The queue should grow linearly as metrics accumulate. After several minutes, remove the iptables rule with `kubectl exec -n datadog <agent-pod-name> -c agent -- iptables -D OUTPUT -d api.datadoghq.com -j DROP`. The agent will resume forwarding, draining the retry queue over subsequent flush intervals. This exercise confirms that the agent gracefully handles transient network failures without data loss, provided the outage duration does not exceed the queue's memory capacity.

## Exercise 3: Fault Injection & Recovery Analysis

Production infrastructure experiences frequent transient failures: network partitions, container restarts, kernel OOM kills, and resource exhaustion. Robust telemetry pipelines must degrade gracefully under these conditions, maintaining partial functionality and recovering automatically when failures resolve. This exercise systematically injects failures into the Datadog Agent's operating environment and validates its resilience mechanisms.

Begin with a simple container restart scenario. Kubernetes DaemonSets automatically restart failed containers, but the restart process temporarily interrupts metric collection. Simulate a core agent crash by killing its main process: `kubectl exec -n datadog <agent-pod-name> -c agent -- kill -9 1`. Kubernetes immediately detects the exit and schedules a container restart. Monitor the recovery process with `kubectl get pod -n datadog <agent-pod-name> -w` to observe the transition from Running to CrashLoopBackOff and back to Running. The agent typically restarts within 5-10 seconds. After recovery, query the agent's uptime with `kubectl exec -n datadog <agent-pod-name> -c agent -- agent version` and verify that check execution has resumed by inspecting the `agent status` output. Confirm that no metrics were lost during the outage by checking the forwarder's retry queue; buffered metrics from the previous session should flush successfully after the restart.

Next, induce a resource exhaustion failure by constraining the agent's memory allocation. Kubernetes resource limits enforce hard caps on container memory usage; exceeding the limit triggers an OOM kill. Edit the agent DaemonSet to impose a restrictive memory limit, such as 100 MiB: `kubectl edit daemonset -n datadog datadog-agent`, then modify the agent container's resources section to include `limits: memory: 100Mi`. Apply the change and wait for the DaemonSet to roll out new pods. The constrained agent will function normally under light load but will exhaust memory when metric cardinality or buffer sizes grow. Generate high-cardinality metrics using the DogStatsD stress test from Exercise 2. Within minutes, the agent will hit its memory limit and terminate with an OOM error. Verify this failure mode by examining the pod's events with `kubectl describe pod -n datadog <agent-pod-name>`, which will display a termination reason of `OOMKilled`. Kubernetes restarts the pod, but the cycle repeats under continued high-cardinality load. This demonstrates that resource limits must account for worst-case metric volumes, not just steady-state averages.

Network failures represent a common operational challenge. Unlike transient packet loss, sustained network partitions prevent the agent from forwarding metrics to Datadog's backend. Simulate a partition by injecting a NetworkPolicy that blocks egress traffic to Datadog intake endpoints. Create a policy that denies all outbound connections except DNS:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-datadog-egress
  namespace: datadog
spec:
  podSelector:
    matchLabels:
      app: datadog-agent
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

Apply this policy with `kubectl apply -f block-datadog-egress.yaml`. The agent immediately loses connectivity to Datadog's API. Monitor the forwarder's behavior with `kubectl logs -n datadog <agent-pod-name> -c agent --follow`. You will observe repeated connection timeout errors and growing retry queue depths. The agent continues collecting metrics locally, buffering them in memory. Query the retry queue size every 60 seconds with `curl http://localhost:5000/agent/status | grep "Transactions in the retry queue"`. The queue depth should increase linearly, demonstrating that the agent preserves metrics during outages. However, if the partition persists longer than the queue's capacity (determined by the `forwarder_retry_queue_payloads_max_size` setting), the agent will begin dropping the oldest payloads to prevent memory exhaustion. To observe this behavior, wait until the retry queue exceeds its configured limit, then check for dropped transaction logs in the agent output.

Recovery from network partitions should occur automatically when connectivity restores. Delete the blocking NetworkPolicy with `kubectl delete networkpolicy -n datadog block-datadog-egress`. The agent's next forwarder attempt will succeed, and it will begin draining the retry queue. Monitor the queue depth as it decreases over subsequent flush intervals. Full recovery time depends on the queue size and flush frequency; a queue with 100 payloads will require approximately 25 minutes to drain at the default 15-second flush interval. This exercise highlights the importance of tuning the retry queue size to accommodate realistic outage durations while balancing memory constraints.

Container runtime failures can disrupt the agent's ability to collect container-level metrics. The agent queries the container runtime (containerd or CRI-O) via a Unix socket to enumerate running containers and their resource usage. Simulate a runtime socket failure by removing the socket's mount from the agent pod. Edit the DaemonSet to comment out the volume mount for `/var/run/containerd/containerd.sock`, then let the pod restart. After recovery, the agent will fail to communicate with the runtime. Confirm this failure by checking the `agent status` output; the `container` check will report errors like `Unable to connect to containerd socket`. Despite this failure, the agent continues collecting node-level metrics from `/proc` and `/sys`, demonstrating partial degradation rather than total failure. Restore full functionality by re-enabling the socket mount and allowing the pod to restart again.

Kernel-level failures impact the system-probe's eBPF instrumentation. eBPF programs can fail to load due to verifier rejections, capability restrictions, or incompatible kernel versions. Simulate a verifier rejection by deploying a version of system-probe built against an incompatible kernel ABI. The simplest approach is to downgrade the agent to an older version that predates your kernel release. After the downgrade, inspect system-probe logs with `kubectl logs -n datadog <agent-pod-name> -c system-probe`. You will observe verifier errors detailing which instructions were rejected and why. Common failure modes include unbounded loops, uninitialized register reads, and invalid memory accesses. The system-probe should fail gracefully, disabling network monitoring but leaving the core agent functional for non-eBPF telemetry. Verify this partial degradation by confirming that infrastructure metrics continue to flow while network flow data ceases.

Finally, test the agent's behavior under sustained CPU throttling. Kubernetes CPU limits enforce throttling by capping the container's CPU quota over a fixed period. Edit the agent DaemonSet to impose a restrictive CPU limit, such as 50 millicores. Under load, the agent will consume its quota rapidly, then wait for quota replenishment, elongating check execution times. Generate sustained load by deploying many annotated pods to activate numerous autodiscovered checks. Monitor the agent's CPU throttling with `kubectl exec -n datadog <agent-pod-name> -c agent -- cat /sys/fs/cgroup/cpu/cpu.stat`. The `nr_throttled` and `throttled_time` counters reveal how often and for how long the container has been throttled. Compare check execution times in the `agent status` output before and after imposing the limit; throttled checks will report longer durations. Excessive throttling can cause checks to time out, resulting in missed metric collections. This demonstrates that CPU limits must account for peak check execution concurrency, not just average utilization.

## Diagnostic Cheat Sheet & Verification Checklist

This consolidated reference provides rapid-access commands and decision trees for field troubleshooting. Use it as a first-response guide when diagnosing Datadog Agent issues in production environments.

**Pod and Container Health**

- List all agent pods: `kubectl get pods -n datadog -o wide`
- Check pod events for restart or OOM reasons: `kubectl describe pod -n datadog <agent-pod-name>`
- Inspect per-container resource usage: `kubectl top pod -n datadog --containers`
- View container logs: `kubectl logs -n datadog <agent-pod-name> -c <container-name> --tail=100`
- Restart a specific container: `kubectl delete pod -n datadog <agent-pod-name>`

**Agent Internal State**

- Full status report: `kubectl exec -n datadog <agent-pod-name> -c agent -- agent status`
- Resolved hostname: `kubectl exec -n datadog <agent-pod-name> -c agent -- agent hostname`
- Active configuration: `kubectl exec -n datadog <agent-pod-name> -c agent -- agent configcheck`
- Forwarder state: `curl http://localhost:5000/agent/status | grep -A10 "Forwarder"`
- Tagger cardinality: `kubectl exec -n datadog <agent-pod-name> -c agent -- curl http://localhost:5000/agent/tagger-list`

**Network Connectivity**

- Active TCP connections: `kubectl exec -n datadog <agent-pod-name> -c agent -- ss -tnp`
- DNS resolution: `kubectl exec -n datadog <agent-pod-name> -c agent -- nslookup api.datadoghq.com`
- TCP port reachability: `kubectl exec -n datadog <agent-pod-name> -c agent -- nc -zv api.datadoghq.com 443`
- Trace agent listener: `kubectl exec -n datadog <agent-pod-name> -c trace-agent -- ss -tlnp | grep 8126`
- DogStatsD listener: `kubectl exec -n datadog <agent-pod-name> -c agent -- ss -ulnp | grep 8125`

**eBPF and System-Probe**

- List loaded eBPF programs: `kubectl exec -n datadog <agent-pod-name> -c system-probe -- bpftool prog list`
- List eBPF maps: `kubectl exec -n datadog <agent-pod-name> -c system-probe -- bpftool map list`
- Dump map contents: `kubectl exec -n datadog <agent-pod-name> -c system-probe -- bpftool map dump id <map-id>`
- System-probe logs: `kubectl logs -n datadog <agent-pod-name> -c system-probe --tail=100`
- Verify security context: `kubectl get pod <agent-pod-name> -n datadog -o jsonpath='{.spec.containers[?(@.name=="system-probe")].securityContext}'`

**Performance Profiling**

- CPU profile (30s): `curl http://localhost:5000/debug/pprof/profile?seconds=30 > agent-cpu.prof`
- Heap profile: `curl http://localhost:5000/debug/pprof/heap > agent-heap.prof`
- Goroutine dump: `curl http://localhost:5000/debug/pprof/goroutine > agent-goroutine.prof`
- Analyze profile: `go tool pprof -http=:8080 <profile-file>`
- System-probe CPU trace: `perf record -a -g -p $(pidof system-probe) -- sleep 30 && perf report`

**Verification Checklist**

When validating a Datadog Agent deployment, systematically work through this checklist to confirm operational readiness:

1. **DaemonSet rollout complete**: Every node hosts exactly one Running agent pod with all containers in Ready state.
2. **Agent version matches deployment specification**: `agent version` output aligns with the intended release.
3. **Hostname resolution correct**: `agent hostname` matches the Kubernetes node name and dashboard expectations.
4. **Forwarder connected**: `agent status` shows `API Key valid` and zero retries in the queue.
5. **All checks running**: `agent status` lists all expected integrations with `[OK]` status and recent timestamps.
6. **No check errors**: No `[ERROR]` or `[WARNING]` entries in check execution logs.
7. **Metric flow confirmed**: The `Aggregator` section reports steadily increasing `Metrics processed` counters.
8. **Network listeners active**: Trace agent listening on port 8126, DogStatsD on port 8125.
9. **eBPF programs loaded**: `bpftool prog list` shows Datadog-owned kprobes and tracepoints.
10. **Container runtime connected**: The `container` check successfully enumerates pods and containers.
11. **Resource usage within limits**: CPU and memory consumption stay well below configured limits under typical load.
12. **No CPU throttling**: `cpu.stat` shows zero or minimal `nr_throttled` increments.
13. **Retry queue empty under normal operation**: Transient queue growth during brief outages is acceptable, but sustained growth indicates connectivity issues.
14. **Log collection functional**: If log collection is enabled, verify that pod logs appear in Datadog's Log Explorer.
15. **Custom metrics arriving**: If applications emit DogStatsD metrics, confirm they appear in Datadog with correct tags.

**Common Failure Modes and Resolutions**

*Forwarder stuck in retry loop*: Network policy, firewall, or DNS misconfiguration blocks egress to Datadog intake endpoints. Verify connectivity with `nc -zv api.datadoghq.com 443` and check for blocking NetworkPolicies.

*Check execution failures*: Missing RBAC permissions, incorrect service endpoint configuration, or expired credentials. Review check error messages in `agent status` and validate RBAC bindings with `kubectl auth can-i list pods --as=system:serviceaccount:datadog:datadog-agent`.

*High memory usage*: Cardinality explosion from unbounded tags or excessive check configurations. Query `tagger-list` to identify high-cardinality tag sources and refactor instrumentation to limit tag value diversity.

*CPU throttling*: CPU limits set too low for the number of active checks. Increase CPU limits or reduce check frequency and concurrency.

*eBPF programs not loading*: Insufficient kernel capabilities, incompatible kernel version, or missing BTF type information. Ensure `privileged: true` or explicit `CAP_SYS_ADMIN` / `CAP_BPF` grants, and verify kernel version compatibility with the agent release.

*Hostname mismatch*: Hostname resolution precedence selects an unexpected source. Override explicitly via `DD_HOSTNAME` environment variable or adjust resolution method with `hostname_fqdn`.

*No metrics from specific pods*: Autodiscovery annotations incorrectly formatted or missing required parameters. Validate annotation syntax with `kubectl get pod <name> -o jsonpath='{.metadata.annotations}'` and cross-reference against official integration documentation.

*Trace agent not receiving spans*: Applications misconfigured to send traces to wrong endpoint or port. Verify application instrumentation points to the node IP (via downward API) on port 8126, or use Kubernetes service discovery to resolve the agent's ClusterIP.

This diagnostic framework equips you to maintain reliable Datadog observability pipelines across diverse production failure scenarios, ensuring continuous telemetry flow and rapid recovery from operational disruptions.
