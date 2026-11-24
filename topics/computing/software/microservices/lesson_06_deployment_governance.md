# Lesson 6: Deployment, Governance, and Production Maturity

## 1. First-Principles Intuition & Invariants

The transition from microservices development to production operation represents a fundamental shift in the problem domain. Where earlier lessons addressed logical service boundaries, communication protocols, and data consistency models, production deployment confronts the physical realities of compute resource allocation, network topology, failure domains, and organizational coordination. A microservices architecture that functions correctly in a development environment may exhibit catastrophic failure modes under production load, not due to algorithmic defects, but because the deployment model fails to account for the distributed systems invariants that govern real-world operation.

At its conceptual core, production deployment transforms stateless application code into stateful runtime processes that consume finite physical resources—CPU cycles, memory pages, network bandwidth, and persistent storage—within a bounded failure domain. The fundamental challenge emerges from the impedance mismatch between the developer's mental model of infinite, reliable resources and the operator's reality of finite, failure-prone infrastructure. Container orchestration platforms like Kubernetes exist precisely to bridge this gap, providing declarative APIs that abstract physical resource management while exposing control surfaces for capacity planning, failure recovery, and gradual rollout strategies.

The first-principles invariant that governs all production deployment is the **declarative state reconciliation loop**. Unlike imperative deployment scripts that execute a sequence of mutations and terminate, declarative systems continuously observe actual runtime state, compare it against desired state expressed in configuration manifests, and drive the system toward convergence through automated corrective actions. This level-triggered model, borrowed from control theory, ensures that transient failures—node crashes, network partitions, process OOM kills—do not leave the system in undefined states requiring manual intervention. The reconciliation loop operates as a persistent background process, making it fundamentally more robust than imperative deployment pipelines that assume linear execution in a failure-free environment.

The second invariant concerns **immutable infrastructure and process isolation**. Traditional deployment models that modify running processes in place—hot-patching binaries, editing configuration files on live servers, applying incremental updates—introduce unbounded state spaces that make rollback, debugging, and capacity planning effectively impossible. Container images, built as immutable filesystem layers with cryptographic content addressing, eliminate this problem by making every deployment artifact a pure function of its build-time inputs. When combined with process-level isolation via Linux namespaces and resource limits via cgroups, containers provide the foundational unit of deployment that can be scheduled, migrated, replicated, and terminated without side effects on other workloads sharing the same physical host.

The third invariant addresses **API contract stability and evolutionary change**. Microservices deployed to production serve external clients and internal consumers that expect stable interfaces over long time horizons. The tension between rapid service iteration and interface stability resolves through versioning schemes that allow multiple interface versions to coexist, graceful deprecation windows that give consumers time to migrate, and backward compatibility constraints that prevent breaking changes from propagating as cascading failures. The Postel principle—"be conservative in what you send, be liberal in what you accept"—becomes a formal design constraint, encoded in schema validation rules, content negotiation headers, and version negotiation protocols.

The organizational dimension of production deployment introduces the fourth invariant: **Conway's Law and team topology alignment**. Microservices architectures inevitably mirror the communication structures of the organizations that build them. A service boundary that crosses team boundaries introduces coordination overhead, deployment coupling, and operational friction that undermines the autonomy benefits microservices promise. Production maturity therefore requires not just technical infrastructure but organizational structures that align service ownership with team boundaries, establish clear operational responsibilities through RACI matrices, and codify cross-team interfaces through service-level objectives (SLOs) rather than ad-hoc coordination.

The deployment strategies that emerge from these invariants—blue-green deployments, canary releases, feature flags, progressive rollouts—all instantiate the same core principle: **minimize blast radius by controlling the rate of change propagation**. Rather than deploying new code atomically across all instances, production systems gradually shift traffic to new versions while continuously monitoring error rates, latency distributions, and resource utilization. When anomalies appear, automated rollback mechanisms revert to the last known-good version without human intervention. This approach transforms deployment from a discrete event requiring change control board approval into a continuous background process constrained by automated safety checks.

## 2. Core Architecture & Mechanics

### Container Image Build Pipeline and Layer Caching

The container build process transforms application source code into an executable image through a sequence of filesystem layer operations. Each instruction in a Dockerfile—`FROM`, `COPY`, `RUN`, `ENV`—produces an immutable layer identified by a SHA-256 content hash. The Docker image format stores these layers as tarballs containing filesystem diffs, with metadata tracking layer ancestry and merge semantics. When a container runtime instantiates an image, it constructs a union filesystem that overlays these read-only layers with a writable top layer, allowing the running process to modify its view of the filesystem without mutating the underlying image.

The layering model enables aggressive caching during iterative development. Because each layer's hash depends only on its contents and parent hash, unchanged layers can be reused across builds. A well-structured Dockerfile places rarely-changing dependencies (base OS packages, language runtimes, third-party libraries) in early layers and frequently-changing application code in late layers, minimizing rebuild time. Consider a Python microservice Dockerfile:

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Install system dependencies (rarely changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies (changes occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

# Copy only the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code (changes frequently)
WORKDIR /app
COPY src/ ./src/
COPY config/ ./config/

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
ENTRYPOINT ["python", "-m", "src.main"]
```

This multi-stage build separates dependency compilation from runtime execution, producing a minimal final image that contains only the virtual environment and application code. The `--no-cache-dir` flag prevents pip from storing downloaded packages in the image layer, reducing size. The explicit user creation and `USER` directive ensure the container process runs without root privileges, constraining the damage radius if an attacker achieves code execution.

### Kubernetes Control Plane Architecture and Reconciliation

Kubernetes implements the declarative reconciliation model through a distributed control plane composed of several specialized components. The API server (`kube-apiserver`) serves as the central coordination point, exposing a RESTful HTTP API backed by etcd, a distributed key-value store that maintains all cluster state. Client requests—whether from `kubectl`, CI/CD pipelines, or internal controllers—modify desired state by writing JSON or YAML manifests to the API server, which validates the schema, enforces admission policies, and persists the data to etcd with a monotonically increasing revision number.

Controllers run as independent processes that watch the API server for changes to specific resource types and drive actual state toward desired state. The scheduler controller watches for Pods in the Pending phase, evaluates resource requests against available node capacity, applies affinity rules and taints/tolerations, and binds Pods to nodes by writing a `nodeName` field to the Pod spec. The kubelet agent running on each node watches for Pods bound to its hostname, pulls container images from configured registries, configures network namespaces through the Container Network Interface (CNI), and starts container processes through the Container Runtime Interface (CRI).

The ReplicaSet controller demonstrates the reconciliation pattern in its purest form. Given a ReplicaSet manifest specifying three replicas of a Pod template, the controller continuously queries the API server for running Pods matching the selector labels. If fewer than three exist, it creates new Pod objects; if more than three exist, it deletes excess Pods. The controller does not track which specific Pods it created—it operates purely on current observed state, making it resilient to controller crashes and eliminating the need for complex state machines tracking in-progress operations.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: order-service
      version: v2.3.1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: order-service
        version: v2.3.1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      serviceAccountName: order-service
      containers:
      - name: order-service
        image: registry.example.com/order-service:v2.3.1
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: order-db-credentials
              key: connection-string
        - name: KAFKA_BROKERS
          value: "kafka-0.kafka-headless:9092,kafka-1.kafka-headless:9092"
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: order-service-config
              key: log-level
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: tls-certs
          mountPath: /etc/tls
          readOnly: true
      volumes:
      - name: tls-certs
        secret:
          secretName: order-service-tls
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: order-service
              topologyKey: kubernetes.io/hostname
```

The Deployment resource wraps ReplicaSets to provide declarative rollout semantics. When the image tag changes from `v2.3.0` to `v2.3.1`, the Deployment controller creates a new ReplicaSet with the updated Pod template and gradually scales it up while scaling down the old ReplicaSet. The `maxSurge: 1` parameter allows one additional Pod beyond the desired count during rollout, while `maxUnavailable: 0` ensures that all five replicas remain available throughout the update, trading rollout speed for zero-downtime deployment.

Resource requests and limits establish the contract between Pods and the scheduler. The `requests` values determine initial Pod placement—the scheduler only assigns a Pod to a node if the node has at least 500m CPU (half a core) and 512 MiB memory available. The `limits` values constrain runtime resource consumption through cgroups: if the Pod attempts to allocate more than 2 GiB memory, the kernel OOM killer terminates its processes. CPU limits throttle rather than kill, using the Completely Fair Scheduler's bandwidth control to cap CPU time at two cores worth of cycles per scheduling period.

The liveness and readiness probes implement different failure detection semantics. Liveness probes detect processes that have entered unrecoverable states—deadlocked threads, corrupted internal data structures—and trigger Pod restarts. Readiness probes detect temporary unavailability—waiting for database connections, loading large datasets into memory—and remove Pods from Service load balancer pools without restarting them. The distinction prevents restart loops during legitimate initialization delays while ensuring that truly broken Pods get recycled quickly.

### Service Discovery and Load Balancing

Kubernetes Services abstract Pod IP addresses, which change on every restart, behind stable virtual IPs and DNS names. The Service controller watches Service and Endpoint objects, programs iptables or IPVS rules on each node to implement cluster-internal load balancing, and writes DNS records to the cluster DNS server (typically CoreDNS). When a client Pod makes a DNS query for `order-service.production.svc.cluster.local`, CoreDNS returns the Service's cluster IP. When the client connects to that IP, the node's kube-proxy intercepts the packet and rewrites the destination to one of the backing Pod IPs using round-robin selection.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: order-service
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: 9090
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

The `sessionAffinity: ClientIP` configuration enables sticky sessions by hashing the client IP address to select the same backend Pod for subsequent connections within the timeout window. This breaks Kubernetes' default stateless load balancing model but proves necessary for services that maintain client-specific in-memory state, such as WebSocket connections or server-side session caches.

For external traffic ingress, Kubernetes Ingress resources define HTTP routing rules that map hostnames and URL paths to backend Services. Ingress controllers—NGINX, Traefik, Envoy-based implementations like Contour or Istio—run as DaemonSets or Deployments with NodePort or LoadBalancer Services, watch Ingress resources, and dynamically reconfigure their routing tables.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-gateway
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 80
      - path: /inventory
        pathType: Prefix
        backend:
          service:
            name: inventory-service
            port:
              number: 80
      - path: /payments
        pathType: Prefix
        backend:
          service:
            name: payment-service
            port:
              number: 80
```

The `cert-manager.io/cluster-issuer` annotation triggers automatic TLS certificate provisioning through Let's Encrypt ACME protocol. The cert-manager controller detects new Ingress resources with this annotation, completes the HTTP-01 or DNS-01 challenge by temporarily configuring additional Ingress rules or DNS records, retrieves the signed certificate, and stores it in the specified Secret. The NGINX ingress controller watches the Secret and reloads its TLS configuration without dropping existing connections.

### API Versioning and Schema Evolution

Production microservices must evolve their interfaces without breaking existing clients. The challenge intensifies in distributed systems where services and clients deploy independently—a service upgrade that changes request schemas can cause client failures hours or days before clients redeploy with updated code. The solution combines multiple versioning strategies applied at different protocol layers.

URL path versioning embeds the API version in the HTTP path, making version selection explicit and enabling parallel deployment of multiple versions. A client calling `GET /v2/orders/12345` explicitly selects the v2 API, while legacy clients continue using `/v1/orders/12345`. The service routes requests to different handler implementations based on path prefix, allowing v1 and v2 code to coexist in the same binary or run as separate Deployments behind the same Ingress.

```go
// Version-specific request and response types
type V1Order struct {
    ID        string    `json:"id"`
    Items     []string  `json:"items"`
    Total     float64   `json:"total"`
    CreatedAt time.Time `json:"created_at"`
}

type V2Order struct {
    ID        string       `json:"id"`
    Items     []V2LineItem `json:"items"`
    Subtotal  int64        `json:"subtotal_cents"`
    Tax       int64        `json:"tax_cents"`
    Total     int64        `json:"total_cents"`
    Currency  string       `json:"currency"`
    CreatedAt time.Time    `json:"created_at"`
    UpdatedAt time.Time    `json:"updated_at"`
}

type V2LineItem struct {
    SKU      string `json:"sku"`
    Quantity int    `json:"quantity"`
    Price    int64  `json:"price_cents"`
}

// Version-agnostic internal domain model
type Order struct {
    ID        uuid.UUID
    Items     []LineItem
    Subtotal  money.Money
    Tax       money.Money
    CreatedAt time.Time
    UpdatedAt time.Time
}

// V1 handler translates between external and internal representations
func (s *OrderService) GetOrderV1(w http.ResponseWriter, r *http.Request) {
    orderID := chi.URLParam(r, "id")
    
    order, err := s.repo.GetByID(r.Context(), uuid.MustParse(orderID))
    if err != nil {
        http.Error(w, "Order not found", http.StatusNotFound)
        return
    }
    
    // Convert internal model to V1 external format
    v1Order := V1Order{
        ID:        order.ID.String(),
        Items:     make([]string, len(order.Items)),
        Total:     float64(order.Subtotal.Add(order.Tax).Cents()) / 100.0,
        CreatedAt: order.CreatedAt,
    }
    
    for i, item := range order.Items {
        v1Order.Items[i] = item.SKU
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(v1Order)
}

// V2 handler provides richer data model
func (s *OrderService) GetOrderV2(w http.ResponseWriter, r *http.Request) {
    orderID := chi.URLParam(r, "id")
    
    order, err := s.repo.GetByID(r.Context(), uuid.MustParse(orderID))
    if err != nil {
        http.Error(w, "Order not found", http.StatusNotFound)
        return
    }
    
    v2Order := V2Order{
        ID:        order.ID.String(),
        Items:     make([]V2LineItem, len(order.Items)),
        Subtotal:  order.Subtotal.Cents(),
        Tax:       order.Tax.Cents(),
        Total:     order.Subtotal.Add(order.Tax).Cents(),
        Currency:  order.Subtotal.Currency().Code,
        CreatedAt: order.CreatedAt,
        UpdatedAt: order.UpdatedAt,
    }
    
    for i, item := range order.Items {
        v2Order.Items[i] = V2LineItem{
            SKU:      item.SKU,
            Quantity: item.Quantity,
            Price:    item.Price.Cents(),
        }
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(v2Order)
}
```

The key insight here is that both API versions translate to and from a canonical internal domain model. The service maintains a single implementation of business logic operating on `Order` structs, with thin versioned adapters at the HTTP boundary. This architecture eliminates duplication of business logic while supporting multiple external representations.

Protocol buffer definitions enable similar versioning through field numbers and backward compatibility rules. Adding new optional fields to a proto definition does not break existing clients, which ignore unknown fields during deserialization. Renaming fields without changing field numbers preserves wire compatibility. Removing fields requires deprecation windows—marking fields as deprecated, ensuring all clients migrate to alternatives, then finally removing the field definition in a subsequent release.

```protobuf
syntax = "proto3";

package orders.v2;

import "google/protobuf/timestamp.proto";
import "google/type/money.proto";

service OrderService {
  rpc GetOrder(GetOrderRequest) returns (Order);
  rpc CreateOrder(CreateOrderRequest) returns (Order);
  rpc UpdateOrder(UpdateOrderRequest) returns (Order);
}

message GetOrderRequest {
  string order_id = 1;
  
  // Added in v2.1 - optional fields maintain backward compatibility
  bool include_audit_log = 2;
}

message Order {
  string id = 1;
  repeated LineItem items = 2;
  google.type.Money subtotal = 3;
  google.type.Money tax = 4;
  google.type.Money total = 5;
  google.protobuf.Timestamp created_at = 6;
  google.protobuf.Timestamp updated_at = 7;
  
  // Added in v2.1 - clients on v2.0 ignore this field
  repeated AuditEntry audit_log = 8;
  
  // Deprecated in v2.2 - replaced by structured status
  string status = 9 [deprecated = true];
  OrderStatus status_v2 = 10;
}

message LineItem {
  string sku = 1;
  int32 quantity = 2;
  google.type.Money unit_price = 3;
}

message AuditEntry {
  google.protobuf.Timestamp timestamp = 1;
  string user_id = 2;
  string action = 3;
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
  ORDER_STATUS_SHIPPED = 3;
  ORDER_STATUS_DELIVERED = 4;
  ORDER_STATUS_CANCELLED = 5;
}
```

The protobuf compiler generates client and server stubs that handle serialization, RPC invocation, and error handling. gRPC clients specify which service methods to call through strongly-typed interfaces, eliminating entire classes of integration bugs that plague JSON-over-HTTP APIs with stringly-typed endpoints and implicit schema contracts.

### Blue-Green and Canary Deployment Strategies

Blue-green deployment maintains two complete production environments—blue (current) and green (next)—and switches traffic atomically between them. In Kubernetes, this pattern manifests as two separate Deployments with different selector labels. The Service resource acts as the traffic switch by updating its selector to point at either the blue or green Deployment.

```yaml
# Blue deployment (current production)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-blue
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: order-service
      slot: blue
  template:
    metadata:
      labels:
        app: order-service
        slot: blue
        version: v2.3.0
    spec:
      containers:
      - name: order-service
        image: registry.example.com/order-service:v2.3.0
        # ... container spec ...

---
# Green deployment (new version, inactive)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-green
  namespace: production
spec:
  replicas: 5
  selector:
    matchLabels:
      app: order-service
      slot: green
  template:
    metadata:
      labels:
        app: order-service
        slot: green
        version: v2.3.1
    spec:
      containers:
      - name: order-service
        image: registry.example.com/order-service:v2.3.1
        # ... container spec ...

---
# Service pointing to blue (current state)
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: production
spec:
  selector:
    app: order-service
    slot: blue  # Change to 'green' to switch traffic
  ports:
  - port: 80
    targetPort: 8080
```

The deployment process proceeds in distinct phases. First, deploy the green Deployment with the new version and wait for all Pods to become ready. Second, run integration tests against the green Pods directly by creating a temporary Service or using `kubectl port-forward`. Third, if tests pass, update the main Service selector to point at the green slot, switching all production traffic instantly. Fourth, monitor error rates and latency for the configured observation window. If anomalies appear, revert by changing the selector back to blue. If the green deployment remains stable, decommission the blue Deployment and promote green to become the new blue in the next cycle.

This strategy provides instant rollback at the cost of doubling resource consumption during the deployment window. It works well for stateless services but struggles with stateful workloads where the database schema must remain compatible with both versions simultaneously during the cutover window.

Canary deployments offer finer-grained control by gradually shifting traffic to the new version while monitoring key metrics. Rather than maintaining two full deployments, a canary strategy runs a small number of Pods with the new version alongside the stable version, directing a percentage of traffic to the canary cohort. Progressive delivery platforms like Flagger automate this pattern by manipulating Service mesh traffic policies or Ingress weights.

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: order-service
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
    webhooks:
    - name: load-test
      url: http://flagger-loadtester/
      timeout: 5s
      metadata:
        type: cmd
        cmd: "hey -z 1m -q 10 -c 2 http://order-service-canary/health"
```

Flagger implements the canary rollout as a state machine. When it detects a change to the `order-service` Deployment (image tag update, environment variable change), it creates a canary Deployment with the new Pod template and a canary Service pointing to it. Every minute (the `interval`), Flagger queries Prometheus for the configured metrics—request success rate and P99 latency. If metrics remain within thresholds, Flagger increases the canary weight by 10%, directing more traffic to the new version. If metrics degrade, Flagger rolls back by scaling the canary Deployment to zero and emitting an alert. If the canary reaches 50% weight (`maxWeight`) without issues, Flagger promotes it by updating the primary Deployment with the canary Pod template and scaling down the canary Deployment.

The load test webhook ensures that the canary receives sufficient traffic for statistical significance. In low-traffic environments, a canary might show perfect metrics simply because it serves too few requests to trigger latent bugs. The webhook runs a synthetic load generator that creates a baseline request volume, making metric anomalies detectable within the one-minute analysis interval.

## 3. High-Performance Optimization & Failure Modes

### Resource Sizing and Autoscaling

Undersized resource requests cause Pods to be scheduled on nodes with insufficient capacity, leading to CPU throttling and OOM kills. Oversized requests waste cluster capacity and inflate infrastructure costs. The optimal sizing emerges from empirical measurement under representative load, not guesswork or defaults copied from tutorials.

The workflow begins with load testing in a staging environment using tools like k6 or Gatling to generate realistic traffic patterns. Instrument the service with Prometheus metrics exposing CPU usage (`process_cpu_seconds_total`), memory allocation (`process_resident_memory_bytes`), and Go runtime metrics (`go_memstats_*` for garbage collection). Deploy the service with generous resource limits and observe actual resource consumption at different traffic levels—baseline idle, average load, and peak traffic scenarios.

```javascript
# k6 load test script simulating realistic order creation traffic
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const failureRate = new Rate('failed_requests');

export let options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 RPS
    { duration: '5m', target: 50 },   // Sustain 50 RPS
    { duration: '2m', target: 100 },  // Ramp up to 100 RPS
    { duration: '5m', target: 100 },  // Sustain 100 RPS
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'failed_requests': ['rate<0.01'],
  },
};

export default function () {
  const payload = JSON.stringify({
    items: [
      { sku: 'WIDGET-001', quantity: 2 },
      { sku: 'GADGET-042', quantity: 1 },
    ],
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post('http://order-service/v2/orders', payload, params);
  
  check(res, {
    'status is 201': (r) => r.status === 201,
    'response time < 500ms': (r) => r.timings.duration < 500,
  }) || failureRate.add(1);

  sleep(1);
}
```

Running this load test while querying Prometheus for CPU and memory metrics reveals the actual resource consumption profile. A Python service might show 200m CPU (0.2 cores) and 384 MiB memory at 50 RPS, 450m CPU and 512 MiB at 100 RPS. Set resource requests at the 50th percentile usage with a 20% margin for variance, and limits at the 95th percentile with a larger margin to absorb traffic bursts without OOM kills.

Horizontal Pod Autoscaler (HPA) automatically adjusts replica counts based on observed metrics. The HPA controller queries metrics every 15 seconds (configurable), calculates the desired replica count using the formula `desiredReplicas = ceil(currentReplicas * (currentMetricValue / targetMetricValue))`, and updates the Deployment's `replicas` field if the ratio exceeds a 10% tolerance threshold.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-service
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 5
        periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

The `behavior` section controls scaling velocity. Scale-up policies respond quickly to load spikes—allowing up to 50% replica increase or adding five Pods per minute, whichever is greater. Scale-down policies act conservatively with a five-minute stabilization window, reducing replicas by at most 10% per minute. This asymmetry prevents premature scale-down that could trigger cascading failures if traffic rebounds quickly, while ensuring rapid scale-up to handle traffic surges.

Custom metrics from Prometheus, exposed via the Prometheus Adapter, enable scaling on application-specific signals. An order service might scale based on Kafka consumer lag—the number of unprocessed messages in input topics—rather than CPU utilization, ensuring that the service maintains low end-to-end latency even when processing batches of deferred work.

### Circuit Breaking and Graceful Degradation

Distributed systems fail in complex, cascading ways. A database experiencing high query latency causes upstream services to accumulate blocked threads waiting for responses, exhausting their thread pools and rejecting new requests. The failure propagates upstream through the call graph, eventually reaching user-facing APIs that return 500 errors. Circuit breakers interrupt this cascade by detecting repeated failures and failing fast rather than waiting for timeouts.

The circuit breaker pattern implements a state machine with three states: Closed (normal operation), Open (failing fast), and Half-Open (testing recovery). In the Closed state, the breaker forwards all requests to the downstream service and monitors failure rates. When failures exceed a configured threshold within a time window, the breaker transitions to Open, immediately returning errors without invoking the downstream service. After a timeout period, the breaker enters Half-Open, allowing a limited number of probe requests through. If probes succeed, the breaker returns to Closed; if they fail, it returns to Open and resets the timeout.

```go
type CircuitBreaker struct {
    mu              sync.Mutex
    state           State
    failures        int
    successes       int
    lastFailureTime time.Time
    
    failureThreshold int
    successThreshold int
    timeout          time.Duration
}

type State int

const (
    StateClosed State = iota
    StateOpen
    StateHalfOpen
)

func (cb *CircuitBreaker) Call(ctx context.Context, fn func() error) error {
    cb.mu.Lock()
    
    switch cb.state {
    case StateOpen:
        if time.Since(cb.lastFailureTime) > cb.timeout {
            cb.state = StateHalfOpen
            cb.successes = 0
            cb.failures = 0
        } else {
            cb.mu.Unlock()
            return ErrCircuitOpen
        }
    case StateClosed:
        // Normal operation
    case StateHalfOpen:
        // Allow probes through
    }
    
    cb.mu.Unlock()
    
    err := fn()
    
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    if err != nil {
        cb.failures++
        cb.lastFailureTime = time.Now()
        
        if cb.state == StateHalfOpen || 
           (cb.state == StateClosed && cb.failures >= cb.failureThreshold) {
            cb.state = StateOpen
            cb.failures = 0
        }
        
        return err
    }
    
    cb.successes++
    
    if cb.state == StateHalfOpen && cb.successes >= cb.successThreshold {
        cb.state = StateClosed
        cb.failures = 0
    }
    
    return nil
}
```

Production implementations use more sophisticated failure detection heuristics. Hystrix and resilience4j implement sliding window counters that track success/failure rates over configurable time windows, preventing single transient errors from tripping the breaker. They also expose metrics for observability—current state, failure counts, latency histograms—enabling operators to diagnose incidents and tune breaker parameters.

Graceful degradation complements circuit breakers by providing fallback behavior when downstream dependencies fail. An order service that cannot reach the inventory service might still accept orders with a warning that inventory checks are degraded, rather than rejecting all order submissions. A product catalog service might serve stale cached data when the database is unreachable, trading freshness for availability.

```go
func (s *OrderService) CreateOrder(ctx context.Context, req *CreateOrderRequest) (*Order, error) {
    // Validate request
    if err := s.validator.Validate(req); err != nil {
        return nil, status.Errorf(codes.InvalidArgument, "invalid request: %v", err)
    }
    
    // Check inventory with circuit breaker and fallback
    var inventoryOK bool
    err := s.inventoryCircuit.Call(ctx, func() error {
        ok, err := s.inventoryClient.CheckAvailability(ctx, req.Items)
        inventoryOK = ok
        return err
    })
    
    if err != nil {
        // Inventory service is down - degrade gracefully
        s.logger.Warn("inventory check failed, accepting order with unverified stock",
            "error", err)
        inventoryOK = false
    }
    
    // Create order in database
    order := &Order{
        ID:               uuid.New(),
        Items:            req.Items,
        InventoryChecked: inventoryOK,
        Status:           OrderStatusPending,
        CreatedAt:        time.Now(),
    }
    
    if err := s.repo.Create(ctx, order); err != nil {
        return nil, status.Errorf(codes.Internal, "failed to create order: %v", err)
    }
    
    // Publish order created event
    event := &OrderCreatedEvent{
        OrderID: order.ID,
        Items:   order.Items,
    }
    
    if err := s.eventBus.Publish(ctx, "orders.created", event); err != nil {
        s.logger.Error("failed to publish order created event", "error", err)
        // Don't fail the request - event publishing is best-effort
    }
    
    return order, nil
}
```

The key decision point is the `InventoryChecked` flag. When inventory verification succeeds, the flag is true and downstream fulfillment systems can trust that items are in stock. When the inventory service is unavailable, the flag is false, signaling to fulfillment systems that they must verify inventory themselves before shipping. This approach maintains order acceptance availability while providing explicit degradation semantics that prevent incorrect business logic from executing under failure conditions.

### Observability and Distributed Tracing

Production microservices require comprehensive observability—structured logging, metrics, and distributed tracing—to diagnose incidents and understand system behavior. The three pillars address different questions: logs answer "what happened?", metrics answer "how much?", and traces answer "where did time go?".

Structured logging replaces printf-style messages with key-value pairs that are machine-parseable and queryable. Rather than `log.Printf("user %s created order %s", userID, orderID)`, emit `logger.Info("order created", "user_id", userID, "order_id", orderID)`. Log aggregation systems like Elasticsearch or Loki can then index the user_id and order_id fields, enabling queries like "find all orders created by user X" or "find all errors containing order Y".

```go
func (s *OrderService) CreateOrder(ctx context.Context, req *CreateOrderRequest) (*Order, error) {
    logger := s.logger.With(
        "method", "CreateOrder",
        "user_id", req.UserID,
        "trace_id", trace.SpanFromContext(ctx).SpanContext().TraceID(),
    )
    
    logger.Info("creating order", "item_count", len(req.Items))
    
    order, err := s.createOrderInternal(ctx, req)
    if err != nil {
        logger.Error("failed to create order",
            "error", err,
            "error_type", fmt.Sprintf("%T", err))
        return nil, err
    }
    
    logger.Info("order created successfully",
        "order_id", order.ID,
        "total_cents", order.Total.Cents())
    
    return order, nil
}
```

Metrics expose time-series data for monitoring and alerting. Prometheus histograms track request latency distributions, counters track request counts and error counts, and gauges track instantaneous values like queue depth or connection pool size. Instrumentation libraries like `prometheus/client_golang` provide automatic HTTP middleware that records metrics for every request.

```go
var (
    httpRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "path", "status"},
    )
    
    httpRequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request latency in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "path", "status"},
    )
)

func init() {
    prometheus.MustRegister(httpRequestsTotal)
    prometheus.MustRegister(httpRequestDuration)
}

func MetricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        recorder := &statusRecorder{ResponseWriter: w, statusCode: http.StatusOK}
        next.ServeHTTP(recorder, r)
        
        duration := time.Since(start).Seconds()
        status := strconv.Itoa(recorder.statusCode)
        
        httpRequestsTotal.WithLabelValues(r.Method, r.URL.Path, status).Inc()
        httpRequestDuration.WithLabelValues(r.Method, r.URL.Path, status).Observe(duration)
    })
}
```

Distributed tracing instruments service-to-service calls to reconstruct end-to-end request flows. When a request enters the system through an API gateway, the gateway creates a trace context containing a unique trace ID and a root span ID. As the request propagates through services, each service extracts the trace context from HTTP headers or gRPC metadata, creates a child span representing its processing, and propagates the updated context to downstream calls. The resulting span hierarchy forms a tree that visualization tools like Jaeger render as a waterfall diagram showing where time was spent.

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

func (s *OrderService) CreateOrder(ctx context.Context, req *CreateOrderRequest) (*Order, error) {
    // Create a span for this operation
    ctx, span := otel.Tracer("order-service").Start(ctx, "CreateOrder")
    defer span.End()
    
    // Add attributes to the span
    span.SetAttributes(
        attribute.String("user_id", req.UserID),
        attribute.Int("item_count", len(req.Items)),
    )
    
    // Database operation gets its own child span
    order, err := s.createOrderInDB(ctx, req)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "failed to create order in database")
        return nil, err
    }
    
    // Inventory check gets its own child span
    if err := s.checkInventory(ctx, order.Items); err != nil {
        span.RecordError(err)
        // Non-fatal error - continue processing
    }
    
    span.SetAttributes(attribute.String("order_id", order.ID.String()))
    return order, nil
}

func (s *OrderService) checkInventory(ctx context.Context, items []LineItem) error {
    ctx, span := otel.Tracer("order-service").Start(ctx, "checkInventory")
    defer span.End()
    
    // Propagate trace context in gRPC metadata
    req := &inventory.CheckRequest{Items: items}
    resp, err := s.inventoryClient.Check(ctx, req)
    
    if err != nil {
        span.RecordError(err)
        return err
    }
    
    span.SetAttributes(attribute.Bool("all_available", resp.AllAvailable))
    return nil
}
```

The OpenTelemetry SDK automatically propagates trace context through instrumented HTTP and gRPC clients, injecting `traceparent` headers or gRPC metadata fields. When the inventory service receives the request, its instrumentation extracts the trace context and creates a child span, linking it to the parent span in the order service. The result is a complete trace showing the order creation request entering the API gateway, being routed to the order service, the order service calling the inventory service, and both services performing database queries.

### Deployment Readiness Checklist

Production deployment of a new microservice requires verifying dozens of operational concerns beyond functional correctness. The following checklist enumerates critical success criteria, organized by category.

**Containerization and Image Security:**
- Base image sourced from official, actively maintained registry (e.g., `python:3.11-slim`, `golang:1.21-alpine`)
- Multi-stage build separates compilation from runtime, minimizing final image size
- Image layers rebuilt on dependency updates, not just application code changes
- Dockerfile runs containers as non-root user with explicit UID/GID
- No secrets (credentials, API keys, certificates) baked into image layers
- Vulnerability scan passed using Trivy, Clair, or equivalent scanner
- Image tagged with semantic version or commit SHA, never `latest`
- Image signed with cosign or equivalent tool for supply chain verification

**Kubernetes Resource Definitions:**
- Deployment specifies CPU and memory requests based on load test measurements
- Deployment specifies CPU and memory limits to prevent resource exhaustion
- Liveness probe configured with appropriate thresholds to detect unrecoverable failures
- Readiness probe configured to detect temporary unavailability during startup
- Pod anti-affinity rules distribute replicas across failure domains (nodes, availability zones)
- SecurityContext enforces read-only root filesystem, drops all capabilities, enables seccomp profile
- ServiceAccount created with minimal RBAC permissions required for operation
- All sensitive configuration stored in Secrets, not ConfigMaps or environment variables
- Resource labels follow naming conventions (app, component, version, managed-by)

**Observability and Monitoring:**
- Prometheus metrics endpoint exposed on dedicated port (typically 9090)
- Metrics include RED method (Rate, Errors, Duration) for all inbound requests
- Metrics include resource utilization (CPU, memory, goroutines, database connections)
- Structured JSON logs written to stdout/stderr for aggregation by cluster logging
- Log entries include trace_id, user_id, and request_id for correlation
- Distributed tracing instrumented using OpenTelemetry with > 1% sampling rate
- Health check endpoints return 200 OK when ready, 503 Service Unavailable otherwise
- Dashboards created in Grafana showing key service metrics
- Alerts configured for error rate > 1%, P99 latency > 1000ms, 5xx response rate > 0.1%

**Networking and Service Discovery:**
- Service resource created with appropriate selector labels
- Ingress rules configured for external traffic with TLS certificates
- Network policies restrict ingress to known callers, egress to required dependencies
- DNS resolution tested for internal service dependencies
- Circuit breakers configured for all downstream HTTP/gRPC calls
- Timeouts set for all outbound requests (recommended: 3s for internal, 10s for external)
- Retry policies configured with exponential backoff and jitter
- Rate limiting applied at ingress layer to prevent abuse

**Data and State Management:**
- Database connection pool sized appropriately for replica count (e.g., 10 connections per Pod)
- Database migrations run automatically on deployment or manually in maintenance window
- Schema changes designed for backward compatibility (additive, not breaking)
- Stateful data stored in external data stores (PostgreSQL, Redis, S3), not in Pod volumes
- Secrets rotated automatically using tools like External Secrets Operator or Vault
- Backup and restore procedures documented and tested quarterly
- Data retention policies implemented for PII and sensitive data

**Deployment Strategy and Rollback:**
- Blue-green or canary deployment configured to minimize blast radius
- Pre-deployment smoke tests verify basic functionality in staging environment
- Load tests run in staging demonstrating service meets latency and throughput SLOs
- Canary analysis configured with automatic rollback on metric degradation
- Rollback procedure documented with maximum time-to-rollback < 5 minutes
- Feature flags implemented for high-risk features to allow runtime disable
- Database migration rollback scripts tested for schema changes

**Security and Compliance:**
- Authentication required for all non-health-check endpoints
- Authorization checks enforce principle of least privilege for resource access
- Input validation prevents SQL injection, XSS, command injection attacks
- Output encoding applied to all user-controlled data in responses
- Rate limiting prevents brute force attacks on authentication endpoints
- Audit logs capture all mutations with user identity and timestamp
- PII handling complies with GDPR, CCPA, or relevant regulations
- Security review completed by AppSec team for internet-facing services

**Documentation and Runbooks:**
- README documents service purpose, architecture, and dependencies
- API documentation generated from OpenAPI spec or protobuf definitions
- Runbook documents common operational tasks (scaling, log analysis, cache invalidation)
- Incident response playbook documents escalation paths and mitigation procedures
- Architecture decision records (ADRs) capture key design decisions and tradeoffs
- On-call rotation established with primary and secondary responders
- Service ownership documented with Slack channel and PagerDuty escalation

This checklist is not exhaustive but represents a baseline production readiness standard. Organizations must adapt it to their specific compliance requirements, risk tolerance, and operational maturity. The critical insight is that production readiness encompasses far more than functional correctness—it requires systematic attention to operational concerns that prevent incidents, accelerate debugging, and enable teams to iterate safely.
