# Lesson 1: Service Mesh Architecture Fundamentals

## 1. First-Principles Intuition & Invariants

Before Istio existed, before the term "service mesh" entered the infrastructure lexicon, distributed systems engineers were solving the same set of problems repeatedly inside every application they wrote. Load balancing, mutual TLS, circuit breaking, retry logic, timeout propagation, telemetry collection—each team reimplemented these concerns in their language of choice, with varying degrees of correctness, and no guarantee of behavioral consistency across service boundaries. A Java service might retry on 503 three times with exponential backoff while its Go upstream partner treated the same status code as terminal. The result was a distributed system whose operational properties were emergent and undocumented, embedded invisibly inside application code rather than expressed as explicit infrastructure policy.

The invariant that motivates the service mesh pattern is deceptively simple: **cross-cutting network concerns belong to the infrastructure layer, not the application layer**. This is the same separation-of-concerns principle that gave us operating system kernels to manage hardware, and it deserves the same level of rigor. Just as an application should not need to implement its own memory allocator to run on Linux, it should not need to implement its own mTLS handshake to participate safely in a zero-trust network. The service mesh materializes this invariant into an operational reality.

Istio's architecture rests on two foundational ideas that together constitute its design contract. The first is the strict separation of the **control plane** from the **data plane**. The control plane is the seat of policy, configuration, and intent; it reasons about the entire mesh as a system, translates high-level operator intent into concrete per-proxy configuration, and distributes that configuration to every participating workload. The data plane is the seat of execution; it intercepts every packet, enforces every policy, generates every metric, and terminates every mTLS handshake—entirely without consulting the control plane at runtime. This decoupling is not merely architectural elegance. It is an operational necessity. In a production mesh spanning hundreds of services across multiple clusters, the control plane may become temporarily unreachable. The data plane must continue to serve traffic correctly based on its last known good configuration, because the alternative—dropping traffic until connectivity is restored—is operationally catastrophic. The data plane's resilience to control plane outages is a first-class invariant of Istio's design.

The second foundational idea is **transparency**. The service mesh must be invisible to the application process. The application binds to a port, writes bytes to a socket, and reads bytes from a socket. It does not know that those bytes are being intercepted by a proxy, re-encrypted with a mesh-issued certificate, forwarded over a multiplexed HTTP/2 connection, retried on transient failure, and tagged with distributed trace headers. This transparency is achieved through a specific kernel-level traffic interception mechanism using `iptables` rules (or the newer eBPF-based datapath in ambient mode, discussed in later lessons) that redirect all inbound and outbound TCP traffic through the sidecar proxy before it reaches, or leaves, the application's network socket. From the application's perspective, it is talking to `localhost`. From the mesh's perspective, every byte the application sends or receives is a policy enforcement point.

Understanding these two invariants—control/data plane separation and transparent interception—is prerequisite to reasoning about every other architectural decision Istio makes.

---

## 2. Core Architecture & Mechanics

### The Control Plane: Istiod as a Unified Brain

In Istio versions prior to 1.5, the control plane was a collection of separately deployed microservices: Pilot for service discovery and routing, Citadel for certificate management, Galley for configuration validation and distribution, and Mixer for policy and telemetry. This decomposition had appeal on paper but created significant operational complexity. Each component required its own deployment, scaling profile, and health monitoring, and the inter-component communication added latency to configuration propagation.

Istio 1.5 collapsed all of these concerns into a single binary and deployment: **Istiod**. This consolidation was not a philosophical retreat from microservices—it was a pragmatic recognition that for infrastructure components with tight operational coupling, a monolithic deployment model reduces failure surface and simplifies operations. Istiod is now the single control plane process that every Envoy proxy in the mesh communicates with.

Inside Istiod, three functional subsystems coexist:

The **service discovery subsystem** (the successor to Pilot) connects to the Kubernetes API server via a shared-informer watch on `Service`, `Endpoints`/`EndpointSlice`, `Pod`, `Node`, and Istio's own CRD types (`VirtualService`, `DestinationRule`, `Gateway`, `ServiceEntry`, and others). It maintains an in-memory model of the entire mesh topology—which workload instances are healthy, what versions they carry, what subsets they belong to, and what traffic policies apply to them. This model is continuously reconciled against the Kubernetes API state; when a pod is rescheduled, its endpoint is drained from the model and all affected proxies receive a configuration update.

The **certificate authority subsystem** (the successor to Citadel) implements an in-process X.509 certificate signing authority. When a new Envoy sidecar initializes, it generates an elliptic-curve key pair locally, constructs a Certificate Signing Request embedding a SPIFFE SVID (the workload's identity, encoded as a URI SAN of the form `spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>`), and sends this CSR to Istiod over a mutually authenticated gRPC connection. Istiod signs the certificate with its intermediate CA, returns the signed certificate along with the root CA bundle, and the sidecar uses these materials to perform mTLS with peer sidecars. Certificate rotation occurs automatically before expiry without any application involvement.

The **configuration validation and distribution subsystem** (the successor to Galley) watches Istio CRD resources in Kubernetes, validates them through an admission webhook before they are persisted to etcd, and translates them into the internal `Istio Discovery Service` model that gets compiled into xDS responses.

### Envoy: The Data Plane Engine

The data plane in Istio is implemented entirely by **Envoy**, an open-source L4/L7 proxy originally developed at Lyft. Choosing Envoy was not incidental; Envoy was designed from the ground up for the specific requirements of service mesh data planes: programmatic configuration via a stable API, support for HTTP/2 and gRPC natively, extensible filter chains, and a threading model that achieves high throughput without lock contention.

Envoy's internal architecture deserves careful examination because its design directly determines Istio's performance characteristics. Envoy runs a single main thread responsible for all configuration updates and a fixed-size worker thread pool, where each worker thread runs a non-blocking event loop using `libevent`. When a new TCP connection arrives, it is assigned to a worker thread and remains pinned to that thread for its entire lifetime. This eliminates per-request locking on connection state. The threading model means that adding CPU cores linearly scales Envoy's connection handling capacity, which is why Istio sidecar resource requests are sensitive to CPU allocation.

Traffic flows through Envoy via a **listener → filter chain → cluster → endpoint** pipeline. A listener is a bound socket address. When a connection arrives on a listener, Envoy evaluates the listener's filter chain match criteria—which may include the destination port, the SNI value from a TLS ClientHello, or an application protocol detected via ALPN—to select the appropriate filter chain. The filter chain contains an ordered sequence of network filters and HTTP filters. For mesh traffic, the most important filter is the **HTTP Connection Manager (HCM)**, which terminates HTTP/1.1 or HTTP/2, parses the request, and routes it through a chain of HTTP filters including `router`, `cors`, `fault`, `ratelimit`, and Istio's custom telemetry and authorization filters. The HCM's route configuration selects a **cluster**, which represents an upstream service and contains load balancing policy, circuit breaker thresholds, and outlier detection configuration. The cluster resolves to a set of **endpoints**—the actual IP:port pairs of upstream instances—and uses a load balancing algorithm (round-robin, least-request, random, or ring hash) to select one for each request.

```
Inbound Connection (Transparent Interception via iptables)
│
▼
┌─────────────────────────────────────────────┐
│              Envoy Sidecar                  │
│                                             │
│  Listener (0.0.0.0:15006 inbound)           │
│      │                                      │
│      ▼                                      │
│  Filter Chain Match                         │
│  (SNI / ALPN / DestPort)                   │
│      │                                      │
│      ▼                                      │
│  Network Filters                            │
│  ┌──────────────────────────────┐           │
│  │ TLS Inspector                │           │
│  │ HTTP Connection Manager      │           │
│  │  ├─ Fault Injection Filter   │           │
│  │  ├─ RBAC Authorization Filter│           │
│  │  ├─ Telemetry Filter         │           │
│  │  └─ Router Filter            │           │
│  └──────────────────────────────┘           │
│      │                                      │
│      ▼                                      │
│  Route → Cluster → Endpoint Selection       │
│      │                                      │
│      ▼                                      │
│  Upstream Connection Pool (HTTP/2 mux)      │
└─────────────────────────────────────────────┘
│
▼
Application Process (127.0.0.1:<app-port>)
```

The critical implementation detail here is that Envoy maintains **separate listener configurations for inbound and outbound traffic**. Inbound traffic, intercepted by `iptables` rule `ISTIO_IN_REDIRECT` and redirected to port 15006, is processed by inbound listeners that enforce authorization policy and generate inbound telemetry. Outbound traffic, intercepted by `iptables` rule `ISTIO_OUTPUT` and redirected to port 15001, is processed by virtual outbound listeners that perform service discovery-based routing, enforce egress policy, and initiate mTLS connections to the destination sidecar's inbound listener. This two-sidecar-hop model means that a single application-to-application request traverses four Envoy filter chains total: through the client's outbound sidecar, through the wire, and through the server's inbound sidecar.

### The xDS Protocol: Configuration as a Stream

The mechanism by which Istiod distributes configuration to Envoy sidecars is the **xDS API**, a family of gRPC streaming protocols that Envoy exposes as its management plane interface. The name xDS is a collective abbreviation for a family of individual Discovery Services, each responsible for a specific category of configuration:

**LDS (Listener Discovery Service)** delivers listener configurations—the set of socket addresses Envoy should bind and their associated filter chains. When a new service is deployed in the mesh, all sidecars receive updated LDS responses adding the new service's virtual outbound listener.

**RDS (Route Discovery Service)** delivers HTTP route configurations—the mapping from request attributes (`:authority`, `:path`, headers) to upstream clusters. `VirtualService` CRDs in Istio translate directly into RDS route configurations, which is why traffic splitting, header-based routing, and fault injection are expressed in `VirtualService` rather than directly in proxy config.

**CDS (Cluster Discovery Service)** delivers cluster configurations—the upstream service definitions including load balancing policy, circuit breaker settings, and health check parameters. `DestinationRule` CRDs translate into CDS cluster configurations.

**EDS (Endpoint Discovery Service)** delivers endpoint configurations—the actual healthy instance IP:port pairs for each cluster. EDS is updated continuously as pods are created, destroyed, and pass or fail health checks. This is the most frequently updated of the xDS channels in a dynamic Kubernetes environment.

**SDS (Secret Discovery Service)** delivers TLS certificates and private keys to Envoy, enabling certificate rotation without process restart. The sidecar's mTLS certificates are delivered via SDS, and Istiod pushes new certificates before the existing ones expire.

The protocol operates in one of two modes: **State of the World (SoTW)**, where each response contains the complete current set of resources, and **Incremental (Delta xDS)**, where responses contain only added, modified, or removed resources since the last ACK. For large meshes with hundreds of services, Delta xDS is critical for reducing control plane CPU and network overhead, since a change to a single `VirtualService` should not require retransmitting the entire route table to every proxy in the mesh.

```
┌──────────────────────────────────────────────────────────┐
│                        Istiod                            │
│                                                          │
│  ┌────────────────┐    ┌──────────────────────────────┐  │
│  │ K8s API Watch  │───▶│  Internal Mesh Model          │  │
│  │ (Informers)    │    │  (Services, Endpoints, Cfg)   │  │
│  └────────────────┘    └──────────────┬───────────────┘  │
│                                       │                  │
│                              xDS Config Compiler        │
│                                       │                  │
│                       ┌───────────────▼──────────────┐  │
│                       │      xDS gRPC Server          │  │
│                       │  (LDS / RDS / CDS / EDS / SDS)│  │
│                       └───────────────┬───────────────┘  │
└───────────────────────────────────────┼──────────────────┘
                                        │ Bidirectional gRPC Stream
              ┌─────────────────────────┼──────────────────────┐
              │                         │                      │
              ▼                         ▼                      ▼
     ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
     │ Envoy Sidecar│        │ Envoy Sidecar│        │ Envoy Sidecar│
     │  (svc-a pod) │        │  (svc-b pod) │        │  (svc-c pod) │
     └──────────────┘        └──────────────┘        └──────────────┘
```

Each Envoy sidecar initiates a persistent bidirectional gRPC stream to Istiod at startup. It sends a `DiscoveryRequest` naming the resource type it wants (using the type URL as the discriminator, e.g., `type.googleapis.com/envoy.config.listener.v3.Listener`) and the version of the last configuration it successfully applied. Istiod responds with a `DiscoveryResponse` containing the current configuration. The sidecar applies the configuration, ACKs the response with the version nonce, and waits for push notifications of changes. If the sidecar fails to apply the configuration, it NACKs the response with an error message, causing Istiod to retain the previous version for that proxy. This ACK/NACK mechanism means Istiod has real-time visibility into which configuration version each proxy has successfully applied—a property that becomes essential for debugging configuration propagation failures.

### Sidecar Injection: Mechanics of Transparent Interception

The sidecar injection process is the mechanism by which Envoy proxies are automatically colocated with application containers inside every Kubernetes pod in a meshed namespace. It operates at two levels: the injection of the sidecar container itself, and the injection of an init container that installs `iptables` rules to redirect traffic through the sidecar.

When a pod creation request reaches the Kubernetes API server, it passes through the admission control pipeline. Istio registers a **MutatingAdmissionWebhook** that intercepts pod creation requests in namespaces labeled with `istio-injection: enabled`. The webhook handler—running as an HTTPS endpoint served by Istiod—receives the pod spec, validates that the pod does not explicitly opt out (via the `sidecar.istio.io/inject: "false"` annotation), and mutates the pod spec to inject two additional containers:

The **init container** (`istio-init`, or `istio-iptables` in newer versions) runs with `NET_ADMIN` and `NET_RAW` capabilities and executes the `istio-iptables` binary before any application containers start. This binary installs a set of `iptables` rules in the pod's network namespace using the following logic: it creates the custom chains `ISTIO_INBOUND`, `ISTIO_REDIRECT`, `ISTIO_IN_REDIRECT`, and `ISTIO_OUTPUT` in the `nat` table. It redirects all inbound TCP traffic (excluding traffic to ports explicitly excluded, such as the Kubelet health check port) to port 15006, where Envoy's inbound listener waits. It redirects all outbound TCP traffic (excluding traffic from the Envoy process itself, identified by the `istio-proxy` UID `1337`, to prevent redirect loops) to port 15001, where Envoy's virtual outbound listener waits.

```bash
# The core iptables rules installed by istio-init (illustrative, simplified)
# Redirect all inbound TCP to Envoy's inbound port
iptables -t nat -A ISTIO_INBOUND -p tcp --dport 8080 -j ISTIO_IN_REDIRECT
iptables -t nat -A ISTIO_IN_REDIRECT -p tcp -j REDIRECT --to-ports 15006

# Redirect all outbound TCP to Envoy's outbound virtual port
# EXCEPT traffic from UID 1337 (the envoy process itself)
iptables -t nat -A ISTIO_OUTPUT -m owner --uid-owner 1337 -j RETURN
iptables -t nat -A ISTIO_OUTPUT -p tcp -j REDIRECT --to-ports 15001
```

The **sidecar container** (`istio-proxy`) is the Envoy binary wrapped in Istio's proxy agent. It runs as UID `1337`, the same UID that the `iptables` rules exempt from outbound redirect, closing the redirect loop. At startup, the proxy agent dials Istiod over gRPC, receives its bootstrap configuration, certificate, and initial xDS configuration, and only then signals readiness. The `istio-proxy` container declares a `readinessProbe` on port 15021 (`/healthz/ready`) so that Kubernetes does not mark the pod as ready until Envoy has received and applied its initial configuration from Istiod. This startup synchronization prevents the application from receiving traffic before the data plane policy is enforced.

The init container approach has one significant operational constraint: it requires the `NET_ADMIN` capability, which some security-conscious organizations restrict via `PodSecurityPolicy` or its successor, `Pod Security Admission`. Istio's ambient mode (a separate architectural mode introduced in Istio 1.15) eliminates the sidecar entirely in favor of a per-node eBPF or `iptables`-based datapath, but that is a topic for a later lesson.

---

## 3. High-Performance Optimization & Failure Modes

### Configuration Propagation Latency and Push Storms

In a mesh with hundreds of services and thousands of pods, the latency between a configuration change—say, applying a `VirtualService` that shifts 10% of traffic to a canary version—and that change being reflected in every proxy's routing table is a first-order operational concern. This latency has two components: the time for Istiod to detect the change and compile new xDS responses, and the time to push those responses to all connected proxies and receive ACKs.

The first component is bounded by Istiod's Kubernetes informer watch latency, which is typically under 100 milliseconds for a healthy API server. The compilation step is CPU-bound and scales with the complexity of the mesh model; in a mesh with thousands of services, a single `VirtualService` change may require recomputing route configurations for a large fraction of proxies.

The second component—fan-out push time—is the more dangerous one. Istiod uses a **push debouncing** mechanism: when a configuration change arrives, it waits for a configurable debounce period (default 100ms, controlled by `PILOT_DEBOUNCE_AFTER`) before compiling and pushing, so that a burst of rapid changes (such as a rolling deployment that creates and destroys many pods in quick succession) is coalesced into a single push rather than generating a storm of individual pushes. Without debouncing, a deployment event that triggers 50 endpoint updates in rapid succession would cause 50 sequential push cycles, multiplying control plane CPU load and proxy churn.

The pathological failure mode here is a **push storm**: a large-scale topology change—cluster-wide deployment, namespace recreation, or a Kubernetes API server restart—that invalidates the entire xDS cache and forces Istiod to push full configuration to every proxy simultaneously. At sufficient mesh scale, this saturates Istiod's gRPC server bandwidth and can cause proxies to queue configuration updates, temporarily operating on stale routing state. The mitigation strategy is to tune the `PILOT_MAX_REQUESTS_PER_SECOND` and `PILOT_PUSH_THROTTLE` environment variables on Istiod, which rate-limit the number of concurrent push operations. For meshes exceeding 1,000 services or 5,000 pods, it is also advisable to partition the mesh into multiple control plane instances using Istio's multi-cluster or revision-based isolation models.

You can observe the current xDS push state in real time using `istioctl`:

```bash
# Inspect xDS configuration sync status for all proxies
istioctl proxy-status

# Retrieve the full Envoy xDS configuration for a specific pod
istioctl proxy-config all deploy/my-service -n production -o json

# Inspect the listener configuration Envoy has applied
istioctl proxy-config listeners deploy/my-service -n production

# Inspect the route table Envoy has applied for outbound traffic
istioctl proxy-config routes deploy/my-service -n production --name 8080

# Inspect cluster and endpoint state
istioctl proxy-config clusters deploy/my-service -n production
istioctl proxy-config endpoints deploy/my-service -n production
```

The `proxy-status` command is particularly valuable for diagnosing propagation lag. Its output shows, for each proxy, whether its LDS, RDS, CDS, and EDS configurations are `Synced`, `Stale`, or `NOT SENT`. A `Stale` status means Istiod has pushed a new configuration that the proxy has not yet ACKed. A `NOT SENT` status can indicate that the proxy's initial connection to Istiod has not completed, often caused by network policy blocking the proxy's connection to Istiod on port 15012.

### Envoy Resource Sizing and the Sidecar CRD

The default Envoy sidecar configuration in Istio is designed for correctness across any mesh topology, which means every Envoy proxy in the mesh receives configuration for every service in the mesh. In a mesh with 500 services, each Envoy process holds the route table, cluster table, and endpoint table for all 500 services, regardless of whether the pod it protects ever talks to more than 5 of them. This creates memory and CPU overhead that scales linearly with mesh size, not with the actual communication topology of the workload.

Istio's `Sidecar` CRD directly addresses this by allowing operators to scope each proxy's configuration to only the services it actually needs to reach. This is one of the highest-impact optimizations available in a large Istio deployment.

```yaml
apiVersion: networking.istio.io/v1beta1
kind: Sidecar
metadata:
  name: productpage-sidecar
  namespace: production
spec:
  workloadSelector:
    labels:
      app: productpage
  egress:
  - hosts:
    - "production/reviews.production.svc.cluster.local"
    - "production/details.production.svc.cluster.local"
    - "istio-system/*"
  ingress:
  - port:
      number: 9080
      protocol: HTTP
      name: http
    defaultEndpoint: 127.0.0.1:9080
```

This `Sidecar` resource instructs Istiod to generate configuration for the `productpage` pods that includes outbound clusters and routes only for the `reviews` and `details` services, plus everything in the `istio-system` namespace (required for Istiod and telemetry endpoints). Istio will not push route or cluster configuration for any other service in the mesh to these pods. In a 500-service mesh where the `productpage` workload communicates with only 2 upstream services, this `Sidecar` resource can reduce Envoy's memory footprint by over 90%.

### Circuit Breaking, Outlier Detection, and the Cost of Misconfiguration

Envoy's `DestinationRule` circuit breaker is implemented as a **connection pool limit** combined with an **outlier detection** algorithm operating at the upstream cluster level. The connection pool limit (`connectionPool`) sets hard caps on the number of concurrent TCP connections and pending HTTP requests Envoy will allow to accumulate toward an upstream cluster. When these limits are exceeded, Envoy returns a `503 Upstream Overflow` immediately rather than queuing the request indefinitely. This is the correct behavior for a system under load—fast failure preserves the caller's ability to retry against a different upstream or return a degraded response to the user.

Outlier detection (`outlierDetection`) is a statistical algorithm that monitors the error rates of individual upstream endpoints and ejects endpoints that exceed a configured error threshold from the load balancing set for a configurable ejection duration. An endpoint that returns 5 consecutive `5xx` responses is ejected; requests are distributed among the remaining healthy endpoints. The ejected endpoint is periodically rechecked and re-admitted when it returns healthy responses.

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews-circuit-breaker
  namespace: production
spec:
  host: reviews.production.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 30ms
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 50
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
        maxRetries: 3
    outlierDetection:
      consecutiveGatewayErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
```

The `maxEjectionPercent: 50` setting is a critical safety parameter that is frequently misconfigured. It caps the maximum percentage of endpoints in a cluster that outlier detection is permitted to eject simultaneously. Without this cap, a correlated failure mode—such as a misconfigured deployment that causes all instances of a service to begin returning errors simultaneously—would cause outlier detection to eject every endpoint in the cluster, leaving Envoy with no healthy upstream and failing every request with a `503 No healthy upstream`. With `maxEjectionPercent: 50`, at least half the endpoints remain in service, and the problem manifests as elevated error rates rather than a complete outage. The `minHealthPercent: 30` parameter provides a complementary guarantee: if the percentage of healthy endpoints in the cluster falls below 30%, outlier detection is disabled entirely, and all endpoints—healthy and unhealthy—are restored to the load balancing set. This panic mode trades quality for availability, which is the correct trade-off when a cluster-wide failure event means there are no healthy endpoints to prefer.

### Diagnosing Data Plane Misconfiguration with `istioctl analyze`

The most common class of production incident in Istio deployments is not a software bug but a configuration error: a `VirtualService` that references a host not defined by any `ServiceEntry` or Kubernetes `Service`, a `DestinationRule` subset that references a pod label that no running pod carries, or a `Gateway` that references a credential name whose `Secret` does not exist. These errors are silent at the Kubernetes API level—the resources are accepted and stored—but result in Envoy proxies either ignoring the misconfigured resource or entering a degraded state where some subset of routing rules are not applied.

`istioctl analyze` performs static analysis of the mesh configuration, detecting these classes of errors before they cause production impact:

```bash
# Analyze the entire mesh configuration across all namespaces
istioctl analyze --all-namespaces

# Analyze a specific namespace and include suppressed messages
istioctl analyze -n production --failure-threshold WARNING

# Analyze a set of local manifest files before applying them (dry-run validation)
istioctl analyze -n production ./manifests/virtualservice.yaml ./manifests/destinationrule.yaml

# Output analysis results as JSON for CI pipeline integration
istioctl analyze --all-namespaces -o json
```

Integrating `istioctl analyze` into the CI/CD pipeline's pre-deployment gate is one of the highest-value operational practices available to Istio operators. It converts a class of silent runtime failures into explicit pre-deployment build failures, closing the feedback loop from hours to seconds.

A complete diagnostic workflow for a suspected routing misconfiguration typically proceeds as follows. Begin with `istioctl proxy-status` to verify that the affected pod's proxy is synchronized with Istiod's current configuration version. If the proxy shows `Stale` on RDS, the routing configuration change has not yet propagated; wait and re-check. If the proxy shows `Synced`, the configuration has been applied and the issue is in the configuration itself. Use `istioctl proxy-config routes <pod> --name <port>` to inspect the exact route table Envoy has compiled and confirm that the expected routing rules are present. If the route is missing, use `istioctl analyze -n <namespace>` to identify any validation errors in the `VirtualService` or `DestinationRule` that would cause Istio to silently discard the resource. If the route is present but traffic is not behaving as expected, use `istioctl proxy-config endpoints <pod>` to verify that the target cluster has healthy endpoints, and check the `outlierDetection` state to confirm that endpoint ejection has not removed all viable upstreams.

This diagnostic discipline—moving systematically from control plane sync state, to compiled proxy configuration, to live endpoint health—covers the majority of data plane operational failures in production Istio deployments and builds the intuition necessary to reason about the mesh as a system rather than a black box.
