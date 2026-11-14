# Lesson 5: Security: RBAC, Network Policies, Pod Security, Encryption

## 1. First-Principles Intuition & Invariants

Security in distributed systems emerges from the composition of multiple independent authorization boundaries, each enforcing a distinct invariant across the attack surface. Google Kubernetes Engine inherits Kubernetes' declarative security model while integrating deeply with Google Cloud Platform's identity and access management primitives, creating a layered defense architecture where every API operation, network packet, and storage transaction traverses multiple verification gates. The fundamental insight that distinguishes production-grade cluster security from toy deployments is the recognition that authentication answers "who are you?" while authorization answers "what are you allowed to do?"—and these questions must be answered independently at the API server, network fabric, pod runtime, and data plane layers.

Role-Based Access Control establishes the authorization graph for Kubernetes API operations. At its core, RBAC models permissions as a bipartite graph connecting subjects (users, service accounts, groups) to resources (pods, deployments, secrets) through verbs (get, list, create, delete). This graph is materialized through four API resources: Role, ClusterRole, RoleBinding, and ClusterRoleBinding. The critical invariant is that permissions are purely additive—there exists no "deny" primitive in the Kubernetes RBAC model. Every API request carries a subject identity extracted from the client certificate, bearer token, or OpenID Connect claims, and the API server evaluates whether any path exists through the RBAC graph that grants the requested verb on the target resource. The evaluation algorithm performs a breadth-first traversal of all RoleBindings and ClusterRoleBindings referencing the subject, collecting the union of granted permissions, and returns success if the requested operation exists in that set.

In GKE, service account token projection replaces long-lived static secrets with time-bounded, audience-scoped tokens that integrate with GCP's Workload Identity Federation. Traditional Kubernetes service accounts mount a static JWT token at `/var/run/secrets/kubernetes.io/serviceaccount/token`, valid for the pod's entire lifetime. Workload Identity binds a Kubernetes ServiceAccount to a Google Service Account through an IAM policy binding, allowing pods to authenticate to GCP APIs using short-lived OAuth2 tokens obtained through the GKE metadata server. The security invariant is that the Kubernetes ServiceAccount becomes a credential-less identifier—it cannot directly access GCP resources. Only when bound to a Google Service Account through an explicit IAM policy does the mapping become active. This design eliminates the need to distribute GCP service account keys as Kubernetes Secrets, removing an entire class of credential exfiltration attacks.

Network policies enforce microsegmentation at Layer 3 and Layer 4 by programming the Linux kernel's netfilter subsystem on every cluster node. The Kubernetes NetworkPolicy API is declarative: you specify allowed ingress and egress flows using pod label selectors, namespace selectors, IP blocks, and port ranges. The GKE datapath implementation uses Calico or Cilium (depending on cluster configuration) to translate these high-level policies into iptables rules or eBPF programs attached to the virtual ethernet interfaces of each pod's network namespace. The default-deny invariant is crucial: by default, all pods can communicate freely. Once you attach a NetworkPolicy selecting a pod, that pod enters isolated mode and only explicitly allowed traffic is permitted. This behavior is asymmetric—the NetworkPolicy only affects the selected pods, not the peers they communicate with.

Pod Security Standards replace the deprecated PodSecurityPolicy admission controller with a three-tier classification system: Privileged, Baseline, and Restricted. These standards are enforced through the Pod Security Admission controller, which evaluates pod specifications against a policy profile at namespace granularity. The Privileged profile imposes no restrictions—containers can run as root, mount host paths, and use all Linux capabilities. The Baseline profile blocks the most dangerous privilege escalations: host namespaces, privileged containers, and host path mounts. The Restricted profile enforces defense-in-depth: non-root users, read-only root filesystems, dropped capabilities, and seccomp profiles. GKE allows you to set these policies in three enforcement modes: enforce (reject violating pods), audit (log violations but allow), and warn (return warnings to clients but allow). The security invariant is that namespace-level policies compose additively—a pod must satisfy all applicable policies across all enforcement modes.

Encryption at rest in GKE protects etcd data and persistent volumes through Google Cloud's default encryption layer, but sensitive workload data requires application-layer secrets management. Kubernetes Secrets are base64-encoded values stored in etcd, encrypted at the volume layer by Cloud KMS when Application-Layer Secrets Encryption (ALSE) is enabled. The encryption envelope model uses a two-tier key hierarchy: a Cloud KMS key encrypts a data encryption key (DEK), which in turn encrypts the actual secret values. Key rotation is transparent—GKE periodically generates new DEKs and re-encrypts secrets in the background. The security boundary is clear: cluster administrators with etcd access can read encrypted blobs, but only principals with Cloud KMS decrypt permissions can recover plaintext. For secrets requiring hardware security module (HSM) protection or fine-grained access control, Google Secret Manager provides an external secret store accessible through Workload Identity.

Audit logging captures the complete provenance of cluster state mutations. GKE writes Kubernetes audit logs to Cloud Logging, recording every API request with request metadata (user, source IP, timestamp), resource identifiers, and request/response payloads. The audit policy determines which events are logged at which detail level: None, Metadata, Request, or RequestResponse. The default GKE audit policy logs metadata for all requests and full request/response bodies for secret operations and authentication events. The retention and analysis invariant is that audit logs are immutable append-only records—even cluster administrators cannot delete or modify log entries. This property is enforced by Cloud Logging's IAM-protected log sinks and storage buckets, providing forensic integrity for incident response and compliance audits.

## 2. Core Architecture & Mechanics

RBAC policy evaluation begins when a client presents credentials to the kube-apiserver. GKE supports multiple authentication strategies: X.509 client certificates for cluster-admin access, service account bearer tokens for in-cluster workloads, and OpenID Connect tokens for human users via Google Cloud IAM. The authentication layer extracts the username, user ID, and group memberships from the credential and attaches them to the request context. For Workload Identity, the authentication flow involves a token exchange: the pod's kubelet mounts a Kubernetes service account token, the application exchanges it for a GCP access token via the metadata server at `169.254.169.254`, and the GKE metadata server validates the Kubernetes token, checks the IAM binding, and mints a time-scoped OAuth2 token for the bound Google Service Account.

The RBAC authorizer evaluates the request against the policy graph stored in etcd. A Role defines permissions within a single namespace, while a ClusterRole operates cluster-wide or grants permissions to non-namespaced resources like nodes. Each role contains an array of rules, where each rule specifies API groups, resources, and verbs. For example, the rule `{"apiGroups": [""], "resources": ["pods"], "verbs": ["get", "list"]}` grants read access to pods in the core API group. RoleBindings attach these roles to subjects. A RoleBinding referencing a ClusterRole applies that ClusterRole's permissions only within the binding's namespace—this pattern allows you to define a common set of permissions in a ClusterRole and instantiate them per-namespace without duplication.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
- kind: ServiceAccount
  name: app-backend
  namespace: production
roleRef:
  kind: ClusterRole
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

This configuration grants the `app-backend` ServiceAccount in the `production` namespace read-only access to pods and pod logs, but only within that namespace. The API server evaluates this by first checking if any RoleBinding in the `production` namespace references `app-backend`, collecting all referenced roles, and verifying that the union of rules covers the requested operation. The evaluation is cached in memory with a time-bounded invalidation on policy changes—RBAC policy updates typically take effect within one second.

Workload Identity configuration requires three components: a Kubernetes ServiceAccount, a Google Service Account, and an IAM policy binding. The GKE cluster must be created with Workload Identity enabled, which configures the metadata server and node identity. Within the cluster, you annotate the Kubernetes ServiceAccount with the email of the Google Service Account it should impersonate:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gcs-writer
  namespace: data-pipeline
  annotations:
    iam.gke.io/gcp-service-account: gcs-writer@project-id.iam.gserviceaccount.com
```

On the GCP side, you grant the Kubernetes ServiceAccount permission to impersonate the Google Service Account using the Workload Identity User role:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  gcs-writer@project-id.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:project-id.svc.id.goog[data-pipeline/gcs-writer]"
```

The member identifier follows the format `serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]`, establishing a cryptographic binding between the Kubernetes cluster, namespace, and ServiceAccount. At runtime, when the pod makes a request to a GCP API, the Google Cloud client library automatically retrieves credentials from the metadata server at `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token`. The GKE metadata server validates the pod's projected service account token, verifies the IAM binding exists, and returns a short-lived OAuth2 access token scoped to the Google Service Account's permissions.

Network policies materialize as iptables chains or eBPF programs on the host network namespace. When you create a NetworkPolicy, the CNI plugin's policy controller watches the API server for policy and pod events, computing the effective rule set for each node. For a simple ingress policy restricting access to a web frontend:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-ingress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: web-frontend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080
```

This policy selects pods labeled `app=web-frontend` in the `production` namespace and allows ingress traffic only from pods labeled `app=api-gateway` on TCP port 8080. The CNI plugin translates this into iptables rules in the `KUBE-NWPLCY-*` chains. Each selected pod's virtual ethernet interface gets a corresponding chain that implements default-deny followed by explicit allow rules. The iptables rules match on source IP addresses corresponding to the IPs of pods matching the `api-gateway` label selector. As pods are created and destroyed, the policy controller continuously updates the IP address sets, maintaining eventual consistency between the declarative policy and the datapath forwarding rules.

For clusters using Dataplane V2 (Cilium-based), the enforcement mechanism shifts from iptables to eBPF programs attached to the pod's network interfaces. Cilium compiles NetworkPolicy objects into BPF programs that perform direct packet filtering in the kernel's TC (traffic control) hook, bypassing the Netfilter stack entirely. The advantage is performance—eBPF avoids the linear rule evaluation of iptables—and observability—Cilium exposes detailed flow logs and metrics. The policy semantics remain identical, but the implementation achieves microsecond-latency policy enforcement through in-kernel BPF maps indexed by pod identity.

Pod Security Standards enforcement operates through the Pod Security Admission controller, a validating admission webhook compiled into the API server. When enabled at the namespace level via labels, every pod creation or update request triggers policy evaluation:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: secure-workloads
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

The `enforce` mode rejects pods that violate the Restricted standard. The `audit` mode logs violations to the audit log without blocking. The `warn` mode returns warnings in the API response. The Restricted profile checks dozens of fields: `spec.securityContext.runAsNonRoot` must be true, `spec.containers[*].securityContext.allowPrivilegeEscalation` must be false, `spec.containers[*].securityContext.capabilities.drop` must include `ALL`, and `spec.securityContext.seccompProfile.type` must be `RuntimeDefault` or `Localhost`. If a pod specification sets `hostNetwork: true`, `hostPID: true`, `hostIPC: true`, or mounts a `hostPath` volume, it fails the Baseline standard and is automatically rejected under Restricted enforcement.

Application-Layer Secrets Encryption integrates Cloud KMS into the etcd encryption pipeline. When enabled, GKE configures the kube-apiserver with an encryption provider configuration pointing to a Cloud KMS key:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - kms:
      name: cloudkms
      endpoint: unix:///var/run/kmsplugin/socket.sock
      cachesize: 1000
      timeout: 3s
  - identity: {}
```

The KMS plugin runs as a sidecar to the API server, communicating over a Unix domain socket. When writing a Secret to etcd, the API server generates a random 32-byte data encryption key, encrypts the secret value using AES-GCM with the DEK, sends the DEK to the KMS plugin for encryption with the Cloud KMS key, and stores both the encrypted DEK and encrypted secret in etcd. Reading reverses the flow: retrieve the encrypted DEK, decrypt it via KMS, decrypt the secret value with the DEK. The KMS plugin caches decrypted DEKs in memory for the configured duration, amortizing the latency of Cloud KMS calls across multiple secret reads.

Audit log structure follows the Kubernetes Event API schema. Each log entry is a JSON object containing the request stage (`RequestReceived`, `ResponseStarted`, `ResponseComplete`, `Panic`), user identity, source IP, request URI, HTTP verb, and resource metadata. For `RequestResponse` level logging, the entry includes the full request and response bodies:

```json
{
  "kind": "Event",
  "apiVersion": "audit.k8s.io/v1",
  "level": "RequestResponse",
  "auditID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "stage": "ResponseComplete",
  "requestURI": "/api/v1/namespaces/production/secrets",
  "verb": "create",
  "user": {
    "username": "system:serviceaccount:production:app-backend",
    "uid": "12345678-1234-1234-1234-123456789abc",
    "groups": ["system:serviceaccounts", "system:serviceaccounts:production", "system:authenticated"]
  },
  "sourceIPs": ["10.128.0.5"],
  "userAgent": "kubectl/v1.28.0",
  "objectRef": {
    "resource": "secrets",
    "namespace": "production",
    "name": "database-credentials",
    "apiVersion": "v1"
  },
  "responseStatus": {
    "metadata": {},
    "code": 201
  },
  "requestObject": {
    "kind": "Secret",
    "apiVersion": "v1",
    "metadata": {"name": "database-credentials", "namespace": "production"},
    "type": "Opaque",
    "data": {"password": "c2VjcmV0"}
  },
  "responseObject": {
    "kind": "Secret",
    "apiVersion": "v1",
    "metadata": {
      "name": "database-credentials",
      "namespace": "production",
      "uid": "abcdef01-2345-6789-abcd-ef0123456789",
      "resourceVersion": "123456",
      "creationTimestamp": "2025-01-15T10:30:00Z"
    },
    "type": "Opaque",
    "data": {"password": "c2VjcmV0"}
  },
  "requestReceivedTimestamp": "2025-01-15T10:30:00.123456Z",
  "stageTimestamp": "2025-01-15T10:30:00.234567Z"
}
```

GKE streams these logs to Cloud Logging's `cloudaudit.googleapis.com/activity` log, queryable through the Logs Explorer or exportable to BigQuery for long-term compliance analysis.

## 3. High-Performance Optimization & Failure Modes

RBAC policy design at scale requires minimizing the number of RoleBindings evaluated per request. The API server caches RBAC policy in memory and performs incremental updates on policy changes, but large numbers of fine-grained RoleBindings increase cache memory pressure and evaluation latency. The optimal pattern is to define a small number of broad ClusterRoles representing logical job functions (developer, operator, security-auditor) and bind them at namespace scope. Avoid creating per-user or per-application Roles—instead, group users by function and bind them to shared ClusterRoles. For multi-tenant clusters, namespace-level RoleBindings provide sufficient isolation without the overhead of ClusterRoleBindings, which must be evaluated for every request regardless of target namespace.

Excessive RBAC permissions violate the principle of least privilege and expand the blast radius of compromised credentials. A common antipattern is granting `get`, `list`, and `watch` on all resources cluster-wide for debugging convenience. This allows any compromised ServiceAccount to enumerate secrets, configmaps, and pod specifications across all namespaces. The defense is to grant permissions scoped to specific resource types and namespaces. For example, application pods rarely need to `list` secrets—they should be granted `get` on specifically named secrets via `resourceNames`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-secret-reader
  namespace: production
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["database-password", "api-key"]
  verbs: ["get"]
```

This configuration allows the ServiceAccount to read only the two named secrets, preventing lateral movement to unrelated secrets in the same namespace.

Workload Identity latency overhead comes from the token exchange round trip to the metadata server and the IAM policy evaluation. The first token request incurs approximately 100-200 milliseconds of latency, but subsequent requests benefit from client-side token caching. Google Cloud client libraries automatically refresh tokens before expiration (typically 1 hour lifetime). For high-throughput workloads making thousands of GCP API calls per second, the token refresh becomes negligible amortized cost. However, cold-start latency matters for short-lived batch jobs—Kubernetes CronJobs spinning up pods every minute will incur the token exchange delay on every invocation. The mitigation is to enable Workload Identity Federation's metadata cache warming, which pre-fetches tokens during pod startup before the application begins making API calls.

Network policy enforcement scales poorly with pod density and policy complexity on iptables-based clusters. Each NetworkPolicy generates multiple iptables rules, and each pod selected by a policy gets its own chain in the Netfilter stack. With thousands of pods and dozens of policies, the iptables rule count can exceed 100,000 entries, causing packet processing latency to degrade linearly. The symptom is elevated conntrack table occupancy and dropped packets due to rule evaluation timeout. GKE Dataplane V2 with Cilium solves this through BPF maps—policies are compiled into hash lookups with constant-time complexity. Migrating existing clusters to Dataplane V2 requires node pool recreation but eliminates the iptables scaling wall.

NetworkPolicy default-deny semantics create subtle failure modes when incomplete policies are deployed. A common scenario: you deploy a NetworkPolicy allowing ingress from the API gateway to the web frontend but forget to allow egress from the frontend to the database. The frontend pods can receive requests but cannot initiate database connections. The symptom is connection timeouts with no clear indication in application logs. The diagnosis requires checking whether any NetworkPolicy selects the source pod and inspecting the egress rules. The defensive pattern is to deploy policies in audit mode first: add the namespace label `pod-security.kubernetes.io/audit: restricted` and monitor the audit logs for violations before switching to `enforce` mode.

Pod Security Standard violations often surface during migration from legacy clusters without PSS enforcement. The Restricted profile's requirement for non-root users breaks container images built with `USER root` or no `USER` directive at all. The fix requires rebuilding images with an explicit non-root user:

```dockerfile
FROM debian:12-slim
RUN useradd -u 1000 -m appuser
USER 1000
COPY --chown=1000:1000 app /app
ENTRYPOINT ["/app"]
```

The `runAsUser` field in the pod's `securityContext` can override the image default, but this approach fragments the security configuration between Dockerfiles and Kubernetes manifests. The production-hardened pattern is to bake the non-root user into the image and enforce `runAsNonRoot: true` at the namespace level via Pod Security Standards.

Application-Layer Secrets Encryption introduces latency and availability dependencies on Cloud KMS. Each secret read requires decrypting the DEK via KMS, adding 10-50 milliseconds per secret depending on regional KMS endpoint proximity. The API server's KMS plugin caches decrypted DEKs, but cache misses during secret-heavy workloads (e.g., deployments mounting dozens of secrets) can amplify latency. The failure mode is catastrophic: if Cloud KMS becomes unavailable, the API server cannot decrypt secrets and pod creation fails cluster-wide. GKE mitigates this through multi-regional KMS keys and the API server's in-memory DEK cache, but applications should minimize secret reads by caching decrypted values at the application layer when security requirements allow.

Secrets stored in etcd remain visible to anyone with direct etcd access, even with ALSE enabled. Cloud KMS encryption protects against physical disk theft and unauthorized etcd database dumps but does not prevent cluster administrators with `kubectl exec` access to the control plane from reading encrypted data. The threat model requires distinguishing between cluster infrastructure administrators (who manage GKE control plane nodes) and application developers (who deploy workloads). For secrets requiring isolation from cluster admins, Google Secret Manager provides a separate security boundary—secrets are stored outside etcd, and access control is enforced through Cloud IAM, independent of Kubernetes RBAC.

Audit log volume scales with API request rate and audit policy detail level. A moderately active GKE cluster generates hundreds of megabytes of audit logs daily. The default GKE audit policy logs at `Metadata` level for most operations, omitting request/response bodies to reduce volume. Enabling `RequestResponse` logging for all API calls can exceed Cloud Logging ingestion quotas and incur substantial storage costs. The optimization is to use advanced audit policy with per-resource rules:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  resources:
  - group: ""
    resources: ["secrets"]
- level: Metadata
  resources:
  - group: ""
    resources: ["pods", "services"]
- level: None
  resources:
  - group: ""
    resources: ["events"]
  verbs: ["get", "list", "watch"]
```

This policy logs full request/response for secret operations, metadata only for pods and services, and omits high-volume read-only event queries. The log export sink should route logs to Cloud Storage or BigQuery for long-term retention, as Cloud Logging retains logs for only 30 days by default.

IAM integration between GKE and Google Cloud Platform creates permission propagation delays. When you modify an IAM policy binding, the change takes up to 80 seconds to propagate to all GKE metadata servers due to Cloud IAM's eventual consistency model. During this window, Workload Identity authentication may fail intermittently as different nodes observe different policy states. The mitigation is to implement exponential backoff and retry logic in application startup code when obtaining GCP credentials. For zero-downtime deployments, create the IAM binding before deploying the workload and allow the propagation window to complete before scaling traffic.

Binary Authorization provides an additional admission control layer, verifying that container images are signed by trusted authorities before allowing deployment. When enabled, GKE's Binary Authorization admission controller intercepts pod creation requests and queries the Binary Authorization policy stored in the project metadata. The policy specifies attestation requirements: each image must have a cryptographic signature from a designated attestor. The attestor is backed by a Cloud KMS signing key or a PGP key pair. During CI/CD, the image build pipeline signs the image digest and uploads the attestation to the Container Analysis API. At deployment time, GKE retrieves the attestation, verifies the signature against the attestor's public key, and only admits pods whose images satisfy all attestation requirements. This prevents the deployment of unsigned or unvetted images, even by cluster administrators.

The security boundaries in GKE are not absolute. Node-level compromise via kernel exploits or container escape can bypass all Kubernetes-layer security controls. The defense in depth relies on Google's hardened GKE node OS (Container-Optimized OS or Ubuntu with automatic security patches), Secure Boot and vTPM for boot integrity verification, and GKE Shielded Nodes, which enable Secure Boot, vTPM, and integrity monitoring by default. At the workload layer, gVisor sandboxing via GKE Sandbox provides an additional isolation layer by interposing a userspace kernel between containers and the host kernel, mitigating many classes of kernel exploits.

Production GKE security posture requires layering these controls: RBAC for API authorization, Workload Identity for credential management, NetworkPolicy for microsegmentation, Pod Security Standards for runtime hardening, Application-Layer Secrets Encryption for data protection, and continuous audit logging for forensic accountability. Each control enforces a distinct invariant, and their composition creates a defense-in-depth architecture resistant to single-point compromises. The operational discipline is to treat security policies as code—version them in Git, review changes through pull requests, and test in staging environments before production rollout. GKE's declarative security model makes this workflow natural, transforming security hardening from ad-hoc checklist items into automated, reproducible infrastructure.
