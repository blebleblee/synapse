# Operational Verification Labs: DNS

## Objective & Environment Setup

DNS operates as the distributed hierarchical namespace resolution protocol underpinning all networked application communication. Every TCP connection, every HTTP request, every Kubernetes service discovery event begins with a DNS query traversing recursive resolvers, authoritative nameservers, and local caching layers. For the infrastructure practitioner, DNS represents both the most fundamental and most fragile component of modern distributed systems. A misconfigured search domain, a cache poisoning vulnerability, or a recursive resolver timeout cascades into application-layer failures that manifest as mysterious connection timeouts, intermittent service unavailability, and cryptic "name resolution failed" errors.

This operational verification guide grounds DNS troubleshooting in the actual packet flows, cache state machines, and resolver configuration hierarchies present in production Kubernetes clusters, Linux network namespaces, and cloud infrastructure. You will interrogate live DNS resolver state using `dig`, `nslookup`, and `host`, capture raw UDP port 53 traffic with `tcpdump`, analyze systemd-resolved and CoreDNS forwarding chains, inject artificial latency and packet loss to observe timeout behavior, and validate DNSSEC cryptographic signature chains. The exercises progress from basic query mechanics through cache coherence analysis to active fault injection, mirroring the diagnostic workflow required when responding to production incidents.

Your verification environment requires a Linux system with root privileges, a running Kubernetes cluster accessible via `kubectl`, and the standard DNS diagnostic toolkit. Install the prerequisite components with the following sequence. First, ensure the BIND DNS utilities are present, providing `dig`, `host`, and `nslookup`. On Debian-based distributions, execute `apt-get install -y dnsutils bind9-host`, while Red Hat systems require `dnf install -y bind-utils`. Verify installation by running `dig -v` and confirming BIND version output. Second, install `tcpdump` for packet capture with `apt-get install -y tcpdump` or `dnf install -y tcpdump`, then validate with `tcpdump --version`. Third, install `iproute2` for network namespace manipulation with `apt-get install -y iproute2` or `dnf install -y iproute2`, confirming via `ip -V`. Fourth, ensure `kubectl` is configured and authenticated to your target Kubernetes cluster by executing `kubectl get nodes` and verifying successful node enumeration.

For Kubernetes-specific DNS verification, you must identify the DNS service implementation deployed in your cluster. CoreDNS dominates modern Kubernetes distributions, having replaced kube-dns as the default in Kubernetes 1.13 and later. Confirm CoreDNS presence by running `kubectl get pods -n kube-system -l k8s-app=kube-dns` and observing pods named `coredns-*`. Retrieve the CoreDNS service ClusterIP with `kubectl get svc -n kube-system kube-dns -o jsonpath='{.spec.clusterIP}'`, noting this IP address for subsequent query testing. Extract the CoreDNS configuration by executing `kubectl get configmap -n kube-system coredns -o yaml`, examining the Corefile plugins, upstream nameserver forwarding rules, and cache TTL parameters. This Corefile defines the complete DNS resolution policy for in-cluster service discovery, external domain forwarding, and negative caching behavior.

On the host system level, Linux DNS resolution flows through either the traditional `/etc/resolv.conf` file or the systemd-resolved stub resolver. Inspect your resolver configuration by examining `cat /etc/resolv.conf`. If the file contains `nameserver 127.0.0.53`, your system employs systemd-resolved as a local caching stub resolver, forwarding queries to upstream servers defined in `/etc/systemd/resolved.conf` or network-manager-provided configurations. Query the current systemd-resolved state with `resolvectl status`, displaying per-interface DNS servers, search domains, DNSSEC validation status, and cache statistics. If `/etc/resolv.conf` instead lists external IP addresses like `8.8.8.8` or `1.1.1.1`, your system performs direct recursive queries without a local caching layer. This distinction fundamentally alters cache coherence behavior, query latency characteristics, and timeout failure modes.

Create a dedicated network namespace for isolated DNS experimentation to avoid polluting production resolver state. Execute `ip netns add dnslab` to instantiate a new namespace, then verify creation with `ip netns list`. Configure a minimal loopback interface within this namespace by running `ip netns exec dnslab ip link set lo up`. This isolated environment permits artificial packet loss injection, latency manipulation via `tc`, and resolver configuration changes without affecting the host system or other containers. You will leverage this namespace throughout Exercise 3 for controlled fault injection scenarios.

Establish a test DNS zone for querying throughout the exercises. If you control a domain, configure a simple authoritative nameserver with A records, MX records, and TXT records for comprehensive testing. Alternatively, utilize public test zones specifically designed for DNS diagnostics. The domain `example.com` serves as an IANA-reserved documentation domain with predictable A record responses. For DNSSEC validation testing, employ `dnssec-tools.org`, which maintains valid DNSSEC signatures. For negative response testing, query intentionally non-existent subdomains under controlled zones. Record these test domains in a shell variable for convenient reuse: `export TEST_DOMAIN=example.com`.

## Exercise 1: Live State & Internal Subsystem Inspection

DNS resolution begins with the application issuing a query through the system resolver, which traverses local caches, recursive resolvers, and ultimately authoritative nameservers in a hierarchical delegation chain. Each layer maintains stateful cache entries governed by TTL expirations, introduces latency from network round-trips and cryptographic validation, and exposes failure modes from timeouts, NXDOMAIN responses, and SERVFAIL errors. This exercise dissects the complete query path from application socket through CoreDNS pod to upstream recursive resolver, inspecting cache state, packet structure, and response timing at each layer.

Begin by executing a baseline DNS query using the `dig` utility, which provides verbose output detailing every aspect of the resolution process. Run `dig @8.8.8.8 $TEST_DOMAIN +noall +answer +stats` to query Google Public DNS directly. The output displays the ANSWER section containing the resolved A record IP address, along with query statistics including query time in milliseconds, message size in bytes, and the responding server address. The query time represents the complete round-trip latency from query transmission through response reception, encompassing network propagation delay, server processing time, and any upstream recursive resolution if the answer was not cached. Execute the command a second time immediately and observe the query time drop significantly, often from 50-100ms to under 10ms. This latency reduction proves the resolver served the response from cache rather than performing fresh upstream resolution.

Expand the query to request additional record types and verbose diagnostic output. Execute `dig @8.8.8.8 $TEST_DOMAIN ANY +trace +noall +answer +authority` to perform iterative resolution starting from the root nameservers. The `+trace` flag forces `dig` to walk the delegation chain manually, querying root servers for the TLD nameservers, then TLD servers for the authoritative nameservers, then authoritative servers for the final answer. Observe the output progression: first, responses from root servers (a.root-servers.net through m.root-servers.net) with NS records for the `.com` TLD; second, responses from `.com` TLD servers with NS records for `example.com`; third, responses from `example.com` authoritative servers with the final A record. Each delegation step introduces additional network round-trips and potential failure points. Note the TTL values on each NS record delegation, which govern how long recursive resolvers cache delegation information before re-querying parent zones.

Transition to querying your Kubernetes cluster's internal CoreDNS service to analyze service discovery resolution. From within the cluster, Kubernetes injects DNS resolver configuration into every pod via the kubelet, which writes `/etc/resolv.conf` with `nameserver <CoreDNS-ClusterIP>` and `search` directives for namespace-qualified service names. Launch a diagnostic pod with `kubectl run dnstest --image=nicolaka/netshoot --restart=Never -- sleep 3600`, which provides a full network diagnostic toolkit including `dig`, `nslookup`, `curl`, and `tcpdump`. Once the pod reaches Running state, confirmed with `kubectl get pod dnstest`, execute commands within its context using `kubectl exec -it dnstest -- bash`.

Inside the pod, inspect the injected resolver configuration with `cat /etc/resolv.conf`. You should observe a `nameserver` line pointing to the CoreDNS service ClusterIP, followed by multiple `search` directives constructing the DNS search path. For a pod in namespace `default`, the search path typically includes `default.svc.cluster.local`, `svc.cluster.local`, and `cluster.local`, enabling short-name service lookups. This search path means a query for hostname `nginx` automatically expands to `nginx.default.svc.cluster.local` before querying. Verify this behavior by running `dig +search nginx` inside the pod, then examining the QUESTION section to confirm the fully-qualified domain name (FQDN) constructed from the search path.

Query a Kubernetes service directly by its FQDN to observe service discovery resolution. If you have a service named `kubernetes` in the `default` namespace (present in all clusters), execute `dig kubernetes.default.svc.cluster.local` from within the `dnstest` pod. The response should contain an A record pointing to the service's ClusterIP, demonstrating CoreDNS translating the service name into its virtual IP. Now query the same service using just its short name with `dig kubernetes`, and observe identical resolution via the search path expansion. Capture the response time for both queries, noting that FQDN queries avoid search path iteration and thus exhibit marginally lower latency (typically 1-2ms difference).

Inspect CoreDNS cache state to understand TTL-based invalidation behavior. CoreDNS exposes a Prometheus metrics endpoint on port 9153 providing detailed cache statistics. From your host system, forward the CoreDNS metrics port with `kubectl port-forward -n kube-system deployment/coredns 9153:9153`, then query the metrics endpoint with `curl http://localhost:9153/metrics | grep coredns_dns_cache`. The output displays cache hit and miss counters, cache size metrics, and per-record-type statistics. Execute several queries from the `dnstest` pod using `kubectl exec dnstest -- dig kubernetes.default.svc.cluster.local +noall +answer` repeatedly, then re-query the metrics endpoint and observe the `coredns_dns_cache_hits_total` counter increment, proving cache hits are occurring.

Analyze the actual DNS packets traversing the network using `tcpdump` to capture raw UDP port 53 traffic. On the Kubernetes node hosting your `dnstest` pod, identify the pod's network namespace by first determining the pod's node with `kubectl get pod dnstest -o jsonpath='{.spec.nodeName}'`, then SSH to that node. Locate the pod's container ID with `crictl ps | grep dnstest`, then derive its network namespace ID with `crictl inspect <container-id> | jq -r '.info.runtimeSpec.linux.namespaces[] | select(.type=="network") | .path'`. Enter the pod's network namespace with `nsenter --net=<namespace-path>`, then launch `tcpdump -i any -n port 53 -v` to capture DNS traffic. In a separate terminal, trigger a DNS query from within the pod using `kubectl exec dnstest -- dig google.com`, and observe the packet capture in the `tcpdump` terminal.

The `tcpdump` output displays the complete DNS query and response exchange. Examine the query packet first, noting the source port (ephemeral port above 32768), destination IP (CoreDNS ClusterIP), destination port (53), UDP protocol, and the DNS question section containing the queried domain name and record type (A). The response packet reverses source and destination, includes the transaction ID matching the query, sets the QR (query/response) flag to 1, and contains the ANSWER section with the resolved IP address and TTL. Measure the time delta between query and response packets directly from the timestamp column, providing the authoritative query latency excluding application-layer processing overhead. If the query requires upstream resolution beyond CoreDNS cache, capture additional packets showing CoreDNS forwarding the query to its configured upstream nameserver (typically the host's resolver or a cloud provider's DNS service).

Validate DNSSEC cryptographic signature chains to ensure DNS responses have not been tampered with during transit. Execute `dig @8.8.8.8 dnssec-tools.org +dnssec +multiline` to request DNSSEC-signed records. The response includes both the standard A record and an RRSIG (resource record signature) record containing a cryptographic signature generated by the authoritative nameserver's private key. The RRSIG record specifies the signature algorithm (typically RSASHA256 or ECDSAP256SHA256), key tag identifying the signing key, signature inception and expiration timestamps, and the base64-encoded signature itself. Verify the signature by querying the DNSKEY records with `dig @8.8.8.8 dnssec-tools.org DNSKEY +dnssec`, which returns the public key used to validate the signature. Modern recursive resolvers perform this validation automatically when DNSSEC is enabled, returning SERVFAIL if validation fails.

Check whether your system resolver performs DNSSEC validation by querying a domain with intentionally broken DNSSEC signatures. The domain `dnssec-failed.org` is specifically configured with invalid signatures for testing purposes. Execute `dig dnssec-failed.org` using your system's default resolver (without specifying `@server`). If your resolver performs DNSSEC validation, the query returns SERVFAIL with no answer section. If validation is disabled, the query succeeds with a normal A record response, indicating your resolver accepted the invalid signature without verification. On systemd-resolved systems, enable DNSSEC validation by editing `/etc/systemd/resolved.conf`, setting `DNSSEC=yes`, then restarting the service with `systemctl restart systemd-resolved`. Re-query `dnssec-failed.org` and confirm SERVFAIL responses after enabling validation.

Inspect CoreDNS forwarding configuration to understand the upstream resolver chain. Retrieve the CoreDNS ConfigMap with `kubectl get configmap -n kube-system coredns -o yaml` and examine the Corefile. The `forward` plugin line specifies upstream nameservers, typically `/etc/resolv.conf` (which reads the host node's resolver configuration) or explicit IP addresses like `8.8.8.8` and `1.1.1.1`. The `cache` plugin defines cache TTL limits, typically `cache 30` for a 30-second cache duration. The `kubernetes` plugin handles in-cluster service discovery by querying the Kubernetes API for Service and Endpoint objects, synthesizing DNS records dynamically without requiring separate authoritative nameserver infrastructure. Modify the Corefile to change upstream resolvers by editing the ConfigMap with `kubectl edit configmap -n kube-system coredns`, changing the `forward` line to `forward . 1.1.1.1`, saving, and triggering a CoreDNS pod restart with `kubectl rollout restart -n kube-system deployment/coredns`. Query an external domain from the `dnstest` pod and capture packets to confirm CoreDNS now forwards to Cloudflare's 1.1.1.1 resolver.

Measure query latency breakdown across the resolution chain to identify bottlenecks. Execute `time dig @<CoreDNS-ClusterIP> google.com +noall +answer` from within the `dnstest` pod, recording the real time reported by the `time` command. This measures end-to-end latency including CoreDNS processing and upstream forwarding. Compare this to querying the upstream resolver directly with `time dig @1.1.1.1 google.com +noall +answer` from the host system. The latency difference quantifies CoreDNS overhead, typically 1-3ms for cached responses and 5-10ms for cache misses requiring upstream forwarding. If CoreDNS latency significantly exceeds upstream latency, suspect cache inefficiency, resource contention on CoreDNS pods, or network policy overhead from Kubernetes NetworkPolicy iptables rules.

## Exercise 2: Benchmarking & Saturation Profiling

DNS resolution performance directly governs application startup time, connection establishment latency, and retry loop behavior during failures. A slow or overloaded resolver cascades into application-layer timeouts, connection pool exhaustion, and cascading failures across microservice dependency graphs. This exercise quantifies resolver throughput using parallel query load generators, profiles cache hit rates under realistic query distributions, identifies resource bottlenecks in CoreDNS pod CPU and memory allocation, and establishes baseline latency percentiles for anomaly detection in production monitoring.

Begin by establishing single-threaded query latency baselines using `dig` with repeated measurements. Create a shell script that executes 100 consecutive queries and records timing statistics. Write the following script to `~/dns_baseline.sh`:

```bash
#!/bin/bash
NAMESERVER=${1:-8.8.8.8}
DOMAIN=${2:-example.com}
ITERATIONS=100

echo "Querying $DOMAIN via $NAMESERVER for $ITERATIONS iterations"
total_time=0

for i in $(seq 1 $ITERATIONS); do
  output=$(dig @$NAMESERVER $DOMAIN +noall +stats | grep "Query time")
  query_time=$(echo $output | awk '{print $4}')
  echo "Query $i: $query_time ms"
  total_time=$((total_time + query_time))
done

avg_time=$((total_time / ITERATIONS))
echo "Average query time: $avg_time ms"
```

Make the script executable with `chmod +x ~/dns_baseline.sh`, then execute it targeting your CoreDNS service from within the `dnstest` pod. First, copy the script into the pod with `kubectl cp ~/dns_baseline.sh dnstest:/tmp/dns_baseline.sh`, then run it with `kubectl exec dnstest -- bash /tmp/dns_baseline.sh <CoreDNS-ClusterIP> kubernetes.default.svc.cluster.local`. The output displays per-query latency and calculates average latency across all iterations. For cached responses, expect latencies below 5ms. For cache misses requiring upstream resolution, expect 20-50ms depending on network conditions and upstream resolver performance.

Introduce parallel query load to measure resolver throughput and saturation behavior. Install the `dnsperf` benchmarking tool, which generates configurable query loads with precise throughput control and latency histogram collection. On Debian systems, install with `apt-get install -y dnsperf`, or compile from source by cloning the repository with `git clone https://github.com/DNS-OARC/dnsperf.git`, then building with `cd dnsperf && ./configure && make && sudo make install`. Verify installation with `dnsperf -h`.

Create a query dataset file containing realistic domain names for benchmarking. Generate a file with 1000 unique domain names by executing the following script:

```bash
#!/bin/bash
OUTPUT_FILE=~/dns_queries.txt
> $OUTPUT_FILE

for i in $(seq 1 1000); do
  echo "example${i}.com A" >> $OUTPUT_FILE
done

echo "Generated $OUTPUT_FILE with $(wc -l < $OUTPUT_FILE) queries"
```

Save this to `~/generate_queries.sh`, execute `chmod +x ~/generate_queries.sh && ~/generate_queries.sh`, and verify the output file with `head ~/dns_queries.txt`. Each line follows the format `<domain> <record-type>`, which `dnsperf` parses to construct DNS queries.

Run a baseline throughput test targeting your CoreDNS service. Execute `dnsperf -s <CoreDNS-ClusterIP> -d ~/dns_queries.txt -l 30 -Q 100` to send 100 queries per second for 30 seconds. The `-l` flag specifies test duration in seconds, while `-Q` sets the target query rate (queries per second). The output displays real-time statistics including queries sent, responses received, query latency percentiles (50th, 90th, 95th, 99th percentiles), and throughput in queries per second. Record the 95th and 99th percentile latencies as critical SLO metrics, as these represent tail latency experienced by slowest requests.

Increase query load progressively to identify the saturation point where latency degrades nonlinearly. Run successive tests with increasing query rates: 100 QPS, 500 QPS, 1000 QPS, 2000 QPS, and 5000 QPS. For each test, record the achieved throughput (which may fall below target rate at saturation) and 99th percentile latency. Plot these metrics to identify the knee in the latency curve, representing the maximum sustainable query rate before resolver saturation. For typical CoreDNS deployments with 2-3 replicas and 100m CPU requests, expect saturation around 2000-3000 QPS, beyond which latency climbs exponentially and packet loss begins.

Profile CoreDNS resource consumption during load testing to identify bottlenecks. In a separate terminal, monitor CoreDNS pod CPU and memory utilization with `kubectl top pod -n kube-system -l k8s-app=kube-dns --containers`. During the high-QPS benchmarks, observe CPU percentage approaching the pod's CPU limit and memory climbing as cache size expands. If CPU reaches 100% of the limit, CoreDNS becomes CPU-bound, throttling query processing and introducing queuing latency. If memory approaches the limit, the Linux OOM killer may terminate CoreDNS pods, causing catastrophic service disruption.

Retrieve detailed CoreDNS metrics to analyze cache efficiency and upstream query distribution. Forward the CoreDNS metrics port with `kubectl port-forward -n kube-system deployment/coredns 9153:9153`, then scrape Prometheus metrics with `curl -s http://localhost:9153/metrics > ~/coredns_metrics.txt`. Extract cache hit rate by calculating the ratio of cache hits to total queries using `grep coredns_dns_cache_hits_total ~/coredns_metrics.txt` and `grep coredns_dns_requests_total ~/coredns_metrics.txt`. A healthy cache hit rate exceeds 90% for typical workloads, indicating effective TTL-based caching reduces upstream forwarding load. If hit rate falls below 80%, investigate whether TTL values are too short, query patterns are too diverse (long-tail distribution), or cache size limits are too restrictive.

Analyze query latency distribution by record type and query status to identify slow query patterns. Extract per-record-type metrics with `grep coredns_dns_request_duration_seconds_bucket ~/coredns_metrics.txt`, which provides histogram buckets for A, AAAA, SRV, and other record types. Compare median and tail latencies across record types. SRV record queries typically exhibit higher latency due to additional Kubernetes API lookups for Endpoint objects. NXDOMAIN responses (queries for non-existent domains) introduce upstream timeouts when resolvers wait for authoritative negative responses before caching.

Simulate cache-miss scenarios to measure worst-case latency when CoreDNS must forward all queries upstream. Clear CoreDNS cache by restarting pods with `kubectl rollout restart -n kube-system deployment/coredns`, waiting for pods to reach Running state with `kubectl rollout status -n kube-system deployment/coredns`, then immediately running `dnsperf -s <CoreDNS-ClusterIP> -d ~/dns_queries.txt -l 10 -Q 100`. The initial queries exhibit elevated latency as CoreDNS populates its cache from upstream responses. After the cache warms (typically 5-10 seconds), latency drops to baseline levels. This warm-up latency represents the application startup penalty when pods initialize before cache population completes.

Benchmark parallel query performance from multiple client pods to simulate realistic microservice loads. Create a Kubernetes Job that launches 10 concurrent pods, each running `dnsperf` against CoreDNS. Write the following Job manifest to `~/dns_load_job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: dns-load-test
spec:
  parallelism: 10
  completions: 10
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: dnsperf
        image: nicolaka/netshoot
        command:
        - /bin/bash
        - -c
        - |
          cat > /tmp/queries.txt <<EOF
          example1.com A
          example2.com A
          example3.com A
          example4.com A
          example5.com A
          EOF
          dnsperf -s $(grep nameserver /etc/resolv.conf | awk '{print $2}') -d /tmp/queries.txt -l 30 -Q 50
```

Apply the Job with `kubectl apply -f ~/dns_load_job.yaml`, then monitor pod creation with `kubectl get pods -l job-name=dns-load-test -w`. Once all pods reach Completed state, retrieve logs from each pod with a loop: `for pod in $(kubectl get pods -l job-name=dns-load-test -o name); do echo "=== $pod ==="; kubectl logs $pod; done`. Aggregate throughput and latency metrics across all pods to measure total cluster-wide DNS query capacity. Delete the Job afterward with `kubectl delete job dns-load-test`.

Measure DNS resolver failover latency when primary upstream nameservers become unavailable. Modify the CoreDNS Corefile to include multiple upstream servers with `forward . 1.1.1.1 8.8.8.8` (space-separated list), apply the change, and restart CoreDNS. Introduce artificial latency on the first upstream resolver by running `tc qdisc add dev eth0 root netem delay 2000ms` on a test VM acting as a forwarding resolver (or use network policy to drop packets to 1.1.1.1). Execute queries from the `dnstest` pod and observe whether CoreDNS automatically fails over to the second upstream (8.8.8.8) after a timeout period, and measure the additional latency introduced by the failover attempt. CoreDNS employs a 5-second upstream timeout by default, meaning failover introduces 5 seconds of additional latency for the first query after upstream failure.

## Exercise 3: Fault Injection & Recovery Analysis

DNS resolution failures manifest in cryptic and application-specific ways: connection timeouts, service mesh circuit breaker activation, Kubernetes pod CrashLoopBackOff states due to failed liveness probes, and intermittent "no such host" errors in logs. This exercise injects controlled DNS failures including packet loss, resolver unavailability, authoritative nameserver timeouts, cache poisoning attempts, and DNSSEC validation failures, then observes application-layer failure modes and recovery behavior. You will harden resolver configurations against these failure modes through timeout tuning, negative caching, and fallback resolver chains.

Begin by simulating packet loss on DNS traffic to observe timeout and retry behavior. Enter the network namespace created during environment setup with `ip netns exec dnslab bash`, then configure a DNS resolver within the namespace by writing `/etc/resolv.conf` manually: `echo "nameserver 8.8.8.8" > /etc/resolv.conf`. Verify basic connectivity with `ping 8.8.8.8` to confirm ICMP reachability, then execute a baseline query with `dig example.com +time=5 +tries=1` to ensure resolution succeeds. The `+time=5` flag sets a 5-second query timeout, while `+tries=1` disables retries, forcing immediate failure on timeout.

Introduce 50% packet loss on UDP port 53 traffic using `iptables` stateless random packet dropping. Execute `iptables -A OUTPUT -p udp --dport 53 -m statistic --mode random --probability 0.5 -j DROP` to drop half of all outbound DNS queries probabilistically. This simulates network congestion, failing hardware, or overloaded resolvers experiencing packet drops. Run a series of queries with `for i in $(seq 1 20); do timeout 5 dig example.com +short +time=2 +tries=1 || echo "TIMEOUT"; done`, which attempts 20 queries with a 2-second timeout each. Approximately half of the queries timeout, demonstrating how packet loss directly translates to resolution failures. Application retries typically mitigate transient packet loss, but sustained loss causes cascading failures.

Increase packet loss to 90% to simulate severe network degradation or an approaching resolver outage. Flush the previous iptables rule with `iptables -F OUTPUT`, then apply the higher loss rate with `iptables -A OUTPUT -p udp --dport 53 -m statistic --mode random --probability 0.9 -j DROP`. Re-run the query loop and observe that nearly all queries timeout. Applications using the default glibc resolver timeout (5 seconds per nameserver) would experience 5-second delays on every DNS query, effectively halting all network communication. This failure mode explains mysterious application startup hangs and periodic timeout spikes in microservice call graphs.

Simulate complete DNS resolver unavailability to observe fallback behavior in multi-resolver configurations. Write a `/etc/resolv.conf` with primary and secondary nameservers: `echo -e "nameserver 192.0.2.1\nnameserver 8.8.8.8" > /etc/resolv.conf`. The IP address 192.0.2.1 is from the RFC 5737 documentation range and intentionally unreachable. Execute `time dig example.com +time=2 +tries=1` and observe the query hang for 2 seconds before failing, then retrying with the second nameserver and succeeding. The total time approaches 2-3 seconds, demonstrating that resolver failover incurs significant latency penalties. Applications using synchronous DNS resolution in the hot request path amplify this latency into user-facing delays.

Test DNS query timeout behavior under various timeout configurations to understand resolver resilience tuning. Execute queries with progressively shorter timeouts: `dig example.com +time=1 +tries=1`, then `+time=0.5`, then `+time=0.2`. Observe that sub-second timeouts result in resolution failures even without packet loss, as network RTT plus resolver processing time exceeds the timeout threshold. Production systems must balance timeout values against typical query latency: too short causes spurious failures during transient network congestion, too long delays failure detection and recovery. A typical production configuration uses 2-5 second timeouts with 2-3 retry attempts across multiple nameservers.

Inject SERVFAIL responses from an authoritative nameserver to observe negative caching and retry behavior. Deploy a local authoritative nameserver that intentionally returns SERVFAIL using the BIND9 nameserver. Install BIND with `apt-get install -y bind9`, then configure a minimal zone file `/etc/bind/named.conf.local`:

```
zone "testfail.local" {
    type master;
    file "/etc/bind/db.testfail.local";
};
```

Create the zone database file `/etc/bind/db.testfail.local`:

```
$TTL    60
@       IN      SOA     ns.testfail.local. admin.testfail.local. (
                        1         ; Serial
                        3600      ; Refresh
                        1800      ; Retry
                        604800    ; Expire
                        60 )      ; Negative Cache TTL
@       IN      NS      ns.testfail.local.
ns      IN      A       127.0.0.1
```

Modify BIND configuration to return SERVFAIL for all queries by adding `rate-limit { responses-per-second 0; };` to `/etc/bind/named.conf.options`. Restart BIND with `systemctl restart bind9`, verify it is listening on UDP port 53 with `ss -ulnp | grep :53`, then query it with `dig @127.0.0.1 test.testfail.local`. The response contains status SERVFAIL instead of NOERROR or NXDOMAIN. Execute repeated queries and observe that resolvers cache SERVFAIL responses briefly (typically 30-60 seconds) before retrying, reducing load on failing authoritative servers but also extending outage duration.

Simulate DNS cache poisoning by deploying a rogue DNS server responding with incorrect A records, then testing whether DNSSEC validation prevents acceptance of forged responses. Deploy a second BIND instance on an alternate port (5353) configured to return attacker-controlled IP addresses for legitimate domains. Modify `/etc/bind/named.conf.local` to add a zone hijacking `google.com`:

```
zone "google.com" {
    type master;
    file "/etc/bind/db.google.com.poisoned";
};
```

Create `/etc/bind/db.google.com.poisoned`:

```
$TTL    300
@       IN      SOA     ns.google.com. admin.google.com. (
                        1         ; Serial
                        3600      ; Refresh
                        1800      ; Retry
                        604800    ; Expire
                        300 )     ; Negative Cache TTL
@       IN      NS      ns.google.com.
@       IN      A       192.0.2.100
```

Configure BIND to listen on port 5353 by editing `/etc/bind/named.conf.options` and adding `listen-on port 5353 { any; };`, then restart BIND. Query the rogue server with `dig @127.0.0.1 -p 5353 google.com +short` and observe it returns `192.0.2.100` instead of Google's legitimate IP addresses. Now query using a DNSSEC-validating resolver with `dig @8.8.8.8 google.com +dnssec` and confirm it returns legitimate IPs, rejecting the poisoned responses due to missing valid RRSIG signatures. This demonstrates DNSSEC's protection against cache poisoning and man-in-the-middle attacks.

Test CoreDNS resilience to upstream resolver failures by terminating upstream connections and observing fallback behavior. Identify CoreDNS upstream nameservers from the Corefile (typically host node's `/etc/resolv.conf`), then block connectivity to those IPs using iptables on the Kubernetes node. SSH to the node hosting a CoreDNS pod, then execute `iptables -A OUTPUT -d 8.8.8.8 -j DROP` to block connectivity to Google Public DNS. From the `dnstest` pod, attempt to query an external domain with `kubectl exec dnstest -- dig google.com`. The query hangs for the upstream timeout period (default 5 seconds), then returns SERVFAIL if no fallback upstream is configured. Restore connectivity with `iptables -D OUTPUT -d 8.8.8.8 -j DROP`, then re-query to confirm recovery.

Introduce artificial latency on DNS traffic to observe how slow resolution cascades into application-layer timeouts. Within the `dnslab` network namespace, apply 1-second delay to all DNS traffic with `tc qdisc add dev lo root netem delay 1000ms`. Execute a query with `dig example.com` and observe it completes successfully but with significantly elevated latency (over 1000ms). Now launch a simple HTTP client that performs DNS resolution before connecting: `timeout 3 curl -v http://example.com/`. The connection attempt times out because the 1-second DNS delay plus TCP handshake time exceeds the 3-second curl timeout. This failure mode explains why microservice call chains experience timeout avalanches when DNS latency increases, even if DNS queries technically succeed.

Test negative caching behavior to understand how NXDOMAIN responses affect application retry logic. Query an intentionally non-existent subdomain with `dig nonexistent123456789.example.com`. The authoritative nameserver returns NXDOMAIN (status 3), indicating the domain does not exist. Execute the same query immediately again and observe the response still comes from cache despite the negative result, evidenced by minimal query time (under 5ms). Extract the negative cache TTL from the SOA record in the AUTHORITY section of the response, which specifies how long resolvers cache negative responses. Typical values range from 60 to 3600 seconds. Applications retrying failed DNS queries during this period receive cached NXDOMAIN responses immediately rather than re-querying upstream, preserving resolver capacity but also extending perceived outage duration for legitimate domains that were temporarily unavailable.

Simulate split-horizon DNS failures where internal and external resolvers provide inconsistent responses for the same domain. Configure the rogue BIND instance to return private IP addresses for internal service discovery domains while external resolvers return NXDOMAIN. Create a zone `internal.example.com` in BIND returning `10.0.0.100`, then query it from within the cluster using CoreDNS (which forwards to external resolvers) versus querying the local BIND instance directly. The inconsistency causes application failures when pods attempt to resolve service names that exist in internal DNS but not external DNS, or vice versa. This failure mode occurs frequently in hybrid cloud environments where Kubernetes clusters must resolve both on-premises and cloud-based service names.

Measure DNS resolution failure impact on Kubernetes pod startup time. Create a pod with an init container that performs DNS resolution before the main container starts, simulating application dependencies on external services. Write the following Pod manifest to `~/dns_init_pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dns-init-test
spec:
  restartPolicy: Never
  initContainers:
  - name: wait-for-dns
    image: busybox:1.36
    command:
    - /bin/sh
    - -c
    - |
      echo "Starting DNS resolution check at $(date)"
      nslookup example.com || exit 1
      echo "DNS resolution successful at $(date)"
  containers:
  - name: main
    image: busybox:1.36
    command: ["sleep", "3600"]
```

Apply the pod with `kubectl apply -f ~/dns_init_pod.yaml`, then monitor startup events with `kubectl get pod dns-init-test -w` and examine logs with `kubectl logs dns-init-test -c wait-for-dns`. The init container blocks main container startup until DNS resolution succeeds. Introduce DNS failures by blocking CoreDNS (e.g., scaling CoreDNS to 0 replicas with `kubectl scale -n kube-system deployment/coredns --replicas=0`), then recreate the pod. The init container hangs indefinitely, preventing the pod from reaching Ready state. This demonstrates how DNS failures translate into application startup failures, especially for applications with eager DNS resolution in initialization code.

Restore DNS service by scaling CoreDNS back to operational replica count with `kubectl scale -n kube-system deployment/coredns --replicas=2`, then verify pods recover with `kubectl get pods -n kube-system -l k8s-app=kube-dns`. Clean up test resources by deleting the DNS init test pod with `kubectl delete pod dns-init-test`, removing the dnstest pod with `kubectl delete pod dnstest`, and removing the DNS load test job if still present with `kubectl delete job dns-load-test --ignore-not-found=true`.

## Diagnostic Cheat Sheet & Verification Checklist

This reference section provides condensed command sequences for rapid DNS troubleshooting in production incidents, organized by symptom and diagnostic objective. Commit these patterns to memory for immediate deployment during outage response.

**Basic Connectivity & Query Validation**
Query a domain using a specific nameserver and display only the answer section: `dig @8.8.8.8 example.com +noall +answer`. Measure query latency explicitly with statistics: `dig @8.8.8.8 example.com +stats`. Trace full delegation chain from root servers through TLD to authoritative nameservers: `dig example.com +trace`. Request DNSSEC-signed records and validate cryptographic signatures: `dig example.com +dnssec +multiline`. Query a specific record type (MX, TXT, SRV): `dig example.com MX +short`. Force TCP instead of UDP to bypass UDP packet size limits or test firewall rules: `dig @8.8.8.8 example.com +tcp`.

**Kubernetes CoreDNS Service Discovery**
Retrieve CoreDNS service ClusterIP: `kubectl get svc -n kube-system kube-dns -o jsonpath='{.spec.clusterIP}'`. Inspect CoreDNS configuration Corefile: `kubectl get configmap -n kube-system coredns -o yaml`. Query Kubernetes service from within a pod using FQDN: `kubectl exec <pod-name> -- dig kubernetes.default.svc.cluster.local`. Verify CoreDNS pod health and resource utilization: `kubectl top pod -n kube-system -l k8s-app=kube-dns --containers`. Retrieve CoreDNS Prometheus metrics for cache analysis: `kubectl port-forward -n kube-system deployment/coredns 9153:9153 && curl http://localhost:9153/metrics | grep coredns_dns`. Restart CoreDNS to clear cache and apply configuration changes: `kubectl rollout restart -n kube-system deployment/coredns`.

**Network Packet Analysis**
Capture DNS traffic on all interfaces with verbose output: `tcpdump -i any -n port 53 -v`. Capture DNS traffic and write to pcap file for offline analysis: `tcpdump -i any -n port 53 -w /tmp/dns.pcap`. Filter captured traffic to specific domain: `tcpdump -i any -n port 53 -v | grep example.com`. Display packet contents in ASCII for query/response inspection: `tcpdump -i any -n port 53 -A`. Capture only DNS queries (QR flag = 0): `tcpdump -i any -n 'udp port 53 and udp[10] & 0x80 = 0'`. Capture only DNS responses (QR flag = 1): `tcpdump -i any -n 'udp port 53 and udp[10] & 0x80 = 128'`.

**System Resolver Configuration**
Display current resolver configuration: `cat /etc/resolv.conf`. Query systemd-resolved status including cache statistics and DNSSEC validation state: `resolvectl status`. Flush systemd-resolved cache: `resolvectl flush-caches`. Query systemd-resolved statistics: `resolvectl statistics`. Display DNS servers assigned to specific network interface: `resolvectl dns <interface-name>`. Override DNS servers temporarily for testing: `export DNS_OVERRIDE=8.8.8.8 && dig @${DNS_OVERRIDE} example.com`.

**Performance Benchmarking & Load Testing**
Run single-threaded query latency test: `dig @<resolver-ip> example.com +noall +stats | grep "Query time"`. Execute 100 serial queries and calculate average latency: `for i in $(seq 1 100); do dig @<resolver-ip> example.com +noall +stats | grep "Query time" | awk '{print $4}'; done | awk '{s+=$1; c++} END {print "Average:", s/c, "ms"}'`. Run parallel load test with dnsperf: `dnsperf -s <resolver-ip> -d queries.txt -l 30 -Q 1000`. Generate synthetic query dataset: `for i in $(seq 1 1000); do echo "example${i}.com A"; done > queries.txt`. Measure DNS resolver throughput under saturation: `dnsperf -s <resolver-ip> -d queries.txt -l 60 -Q 5000 | grep "Queries per second"`.

**Fault Injection & Resilience Testing**
Introduce packet loss on DNS traffic using iptables: `iptables -A OUTPUT -p udp --dport 53 -m statistic --mode random --probability 0.5 -j DROP`. Remove packet loss rule: `iptables -D OUTPUT -p udp --dport 53 -m statistic --mode random --probability 0.5 -j DROP`. Block connectivity to specific upstream resolver: `iptables -A OUTPUT -d 8.8.8.8 -j DROP`. Add artificial latency to DNS queries using tc: `tc qdisc add dev eth0 root netem delay 500ms`. Remove tc latency: `tc qdisc del dev eth0 root`. Test query timeout behavior: `dig @<resolver-ip> example.com +time=1 +tries=1`. Simulate resolver unavailability by scaling CoreDNS to zero: `kubectl scale -n kube-system deployment/coredns --replicas=0`.

**DNSSEC Validation & Security**
Query DNSSEC-signed domain and verify signature: `dig @8.8.8.8 dnssec-tools.org +dnssec +multiline`. Retrieve DNSKEY public key records: `dig @8.8.8.8 dnssec-tools.org DNSKEY +short`. Test DNSSEC validation failure handling: `dig dnssec-failed.org`. Enable DNSSEC validation in systemd-resolved: `echo "DNSSEC=yes" >> /etc/systemd/resolved.conf && systemctl restart systemd-resolved`. Verify DNSSEC chain of trust from root to target domain: `dig +trace +dnssec example.com`.

**Cache Behavior & TTL Analysis**
Extract TTL value from DNS response: `dig example.com +noall +answer | awk '{print $2}'`. Query immediately after clearing cache to measure upstream latency: `resolvectl flush-caches && dig example.com +stats | grep "Query time"`. Monitor TTL countdown by querying repeatedly: `watch -n 1 'dig example.com +noall +answer'`. Force cache bypass by querying with random subdomain: `dig $(uuidgen).example.com +short`. Analyze CoreDNS cache hit rate from metrics: `curl -s http://localhost:9153/metrics | grep coredns_dns_cache_hits_total`.

**Troubleshooting Checklist for Production Incidents**
When responding to DNS-related outages, execute this diagnostic workflow systematically. First, verify basic connectivity to DNS resolvers with `ping <resolver-ip>` and confirm UDP port 53 reachability with `nc -u -v <resolver-ip> 53`. Second, test resolution of known-good external domains like `dig @8.8.8.8 google.com +short` to isolate resolver versus domain-specific issues. Third, inspect system resolver configuration with `cat /etc/resolv.conf` and verify nameserver IPs are correct and reachable. Fourth, check CoreDNS pod health with `kubectl get pods -n kube-system -l k8s-app=kube-dns` and examine logs for errors with `kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100`. Fifth, verify CoreDNS upstream forwarding configuration with `kubectl get configmap -n kube-system coredns -o yaml` and confirm upstream IPs are accessible from nodes. Sixth, capture live DNS traffic with `tcpdump -i any -n port 53 -c 20` while reproducing the failure to observe actual query/response exchange. Seventh, measure query latency and timeout behavior with `dig +time=2 +tries=1` to quantify degradation. Eighth, check for resource exhaustion with `kubectl top pod -n kube-system -l k8s-app=kube-dns` and scale CoreDNS if CPU or memory saturated. Ninth, review recent configuration changes in CoreDNS ConfigMap with `kubectl rollout history -n kube-system deployment/coredns` and rollback if necessary with `kubectl rollout undo -n kube-system deployment/coredns`. Finally, verify application-layer DNS resolution by executing queries from within affected pods using `kubectl exec <pod> -- dig <domain>`, confirming injected `/etc/resolv.conf` matches expected CoreDNS ClusterIP.

This verification framework provides the operational foundation for DNS mastery in production infrastructure, enabling rapid incident response, proactive performance optimization, and resilient resolver architecture design. The combination of live state inspection, controlled benchmarking, and fault injection prepares you to diagnose and remediate DNS failures across cloud-native distributed systems.
