# Lesson 4: Security, RBAC, and Workload Isolation

## 1. First-Principles Intuition & Invariants

Azure Kubernetes Service exists at the confluence of two profoundly different security paradigms: the identity-centric access control model of Azure Active Directory, rooted in OAuth 2.0 bearer tokens and delegated authorization flows, and the declarative, resource-oriented Role-Based Access Control system native to Kubernetes, governed by API server admission chains and etcd-persisted policy objects. The tension between these models—one designed for human operators navigating enterprise organizational hierarchies, the other for programmatic service accounts making millions of API calls per second—defines the security architecture of every production AKS cluster. Understanding this tension is not an academic exercise; it determines whether a single compromised pod can pivot laterally across namespaces, whether a malicious container image can exfiltrate cluster credentials, and whether your multi-tenant platform survives its first encounter with a determined adversary.

The foundational invariant of Kubernetes security is that every API request, whether originating from kubectl, an in-cluster pod, or an external admission webhook, passes through three sequential gates: authentication, authorization, and admission control. Authentication answers the question "who are you?" by extracting cryptographic proof from bearer tokens, X.509 client certificates, or federated identity providers. Authorization answers "what are you allowed to do?" by consulting RBAC policies, attribute-based access control rules, or webhook-based decision engines. Admission control answers "is this request semantically valid and compliant with organizational policy?" by invoking mutating and validating webhooks that can modify or reject resource manifests before they reach etcd. This three-phase model is a level-triggered control loop: the API server does not remember previous decisions, does not maintain session state, and re-evaluates every request against the current policy snapshot stored in etcd. This statelessness is both a strength—policy changes propagate instantly without requiring client reconnection—and a vulnerability surface, because credential theft grants immediate, irrevocable access until the token expires or is explicitly revoked.

Azure Active Directory integration introduces a fourth dimension: federated identity mapping. When you enable AAD integration on an AKS cluster, the API server trusts Azure AD as an OpenID Connect identity provider, delegating the entire authentication problem to Microsoft's global identity fabric. The mechanics are subtle but consequential. A user authenticating to an AAD-integrated cluster does not receive a long-lived client certificate, as in traditional kubeconfig workflows; instead, the Azure CLI or kubeconfig credential helper initiates an OAuth 2.0 authorization code flow, obtains a short-lived JWT access token signed by Azure AD, and presents that token to the kube-apiserver via the Authorization: Bearer header. The API server validates the token's cryptographic signature against Azure AD's published JWKS (JSON Web Key Set), extracts the user's object ID and group memberships from JWT claims, and maps those Azure identities to Kubernetes RBAC subjects. This indirection—Azure AD as the source of truth for identity, Kubernetes RBAC as the source of truth for authorization—means that user provisioning and group membership changes in Azure AD propagate to AKS clusters without any manifest updates or secret rotation, but also means that a compromised Azure AD tenant grants an attacker unfettered access to every integrated cluster.

The second invariant is namespace-level resource isolation. Kubernetes namespaces are not security boundaries in the kernel sense—they do not map to Linux namespaces, do not enforce memory isolation, and do not provide any defense against a container breakout—but they are the primary unit of RBAC scope and network policy enforcement. A Role or RoleBinding in Kubernetes is always namespace-scoped, meaning that granting a service account the ability to create pods in namespace "team-a" does not confer any permissions in namespace "team-b". This scoping model mirrors the hierarchical resource organization of Azure Resource Manager, where RBAC assignments cascade through subscription, resource group, and individual resource scopes. The critical difference is that Kubernetes RBAC is additive and non-hierarchical: there is no implicit inheritance of permissions from a parent namespace, and a user with cluster-admin privileges in one namespace cannot automatically assume equivalent powers in another unless explicitly granted a ClusterRole or a second RoleBinding. This additive model eliminates ambient authority but demands rigorous automation to maintain policy consistency across hundreds of namespaces in large-scale multi-tenant clusters.

The third invariant is the principle of least privilege applied to service accounts. Every pod in Kubernetes runs with an associated service account, and that service account's token is automatically mounted into the pod's filesystem at `/var/run/secrets/kubernetes.io/serviceaccount/token`. This token is a signed JWT with a fixed audience claim, issued by the API server's TokenRequest API, and valid for a default duration of one hour with automatic rotation. The token grants the pod the ability to authenticate to the API server and perform any actions authorized by the service account's RBAC bindings. The security implication is immediate: any process with filesystem access inside the pod—including a compromised application, a supply chain backdoor, or a remote code execution exploit—can read that token and impersonate the service account. Defense against this threat vector requires two layers: first, minimizing the permissions granted to each service account through fine-grained RoleBindings that specify exact resource types, verbs, and namespaces; second, disabling automatic token mounting for pods that do not require API access by setting `automountServiceAccountToken: false` in the pod specification. This second defense is underutilized in practice, because most deployment templates and Helm charts blindly accept default service account behavior, leading to a sprawl of overprivileged pods with unnecessary API credentials.

The fourth invariant is that workload isolation is a property of the network policy controller and the container runtime, not of the Kubernetes control plane. The kube-apiserver does not intercept pod-to-pod traffic, does not enforce firewall rules, and does not prevent a compromised pod from scanning the cluster's internal network or attempting to connect to the kubelet's read-write API port. Network segmentation must be imposed by a CNI plugin with NetworkPolicy support—in AKS, this is typically Azure Network Policy or Calico—which programs iptables rules or eBPF maps on each node to drop packets that violate declared policies. The critical detail is that NetworkPolicy objects are declarative intent, not active enforcement: creating a NetworkPolicy that denies all ingress to a namespace does not retroactively terminate existing TCP connections, does not prevent a pod from accepting connections before the policy is instantiated, and does not defend against an attacker with host-level access who can bypass iptables entirely. This gap between declarative policy and runtime enforcement is where most multi-tenant isolation failures occur.

The final invariant is that secrets in Kubernetes are not encrypted at rest by default. A Secret object is merely a base64-encoded blob stored in etcd, and anyone with read access to etcd—whether through a compromised control plane node, a misconfigured backup, or a supply chain attack on the etcd container image—can trivially decode every secret in the cluster. AKS addresses this through Azure's encryption-at-rest layer, which uses AES-256-XTS to encrypt etcd disks with keys managed by Azure Key Vault, but this defense is transparent to the cluster administrator and does not prevent an attacker with legitimate API access from reading secrets via kubectl. The production-grade mitigation is to bypass Kubernetes Secrets entirely and integrate Azure Key Vault directly into pod workloads via the Secrets Store CSI driver, which mounts secrets as ephemeral volumes without persisting them to etcd. This approach shifts the security perimeter from Kubernetes RBAC to Azure IAM, leveraging managed identities and Key Vault access policies to enforce cryptographic access control at the hardware security module level.

## 2. Core Architecture & Mechanics

The API server authentication chain in an AAD-integrated AKS cluster operates as a sequential waterfall of credential validators, each attempting to extract and verify identity from the incoming HTTP request. The first validator examines the Authorization header for a Bearer token. If present, the token is passed to the OIDC authenticator plugin, configured at cluster creation time with Azure AD's tenant-specific issuer URL, client ID for the AKS cluster's registered application, and the public JWKS endpoint for signature verification. The authenticator performs three cryptographic checks: it verifies the token's RSA-256 or ECDSA signature against Azure AD's published public keys, confirms that the `iss` claim matches the expected tenant issuer, and validates that the `aud` claim includes the AKS cluster's client ID. If all checks pass, the authenticator extracts the `oid` claim—the user's immutable object ID in Azure AD—and the `groups` claim, which contains an array of Azure AD group object IDs to which the user belongs.

These extracted claims are transformed into a Kubernetes user object with the username set to the Azure AD object ID and groups populated from the groups claim. This user object is then passed to the authorization phase, where the API server consults its in-memory RBAC policy cache—a projection of all Role, ClusterRole, RoleBinding, and ClusterRoleBinding objects from etcd—to determine whether the user has permission to perform the requested verb on the specified resource. The authorization decision is computed by iterating through all RoleBindings and ClusterRoleBindings, checking whether any binding references the user's name, any of the user's groups, or the catch-all `system:authenticated` group, and then aggregating the union of all granted permissions. This aggregation is purely additive: there is no concept of deny rules or negative permissions in Kubernetes RBAC, meaning that a single overly permissive binding can grant broad access that cannot be revoked by more restrictive bindings.

The admission control phase introduces programmatic policy enforcement through mutating and validating webhooks. AKS pre-installs several critical admission controllers, including the PodSecurityPolicy admission controller (deprecated in Kubernetes 1.21 and removed in 1.25), the Azure Policy admission webhook, and the Secrets Store CSI Driver webhook. The Azure Policy webhook is particularly important for enterprise governance because it allows centralized enforcement of organization-wide policies authored in Azure Policy's Rego-like constraint language, then compiled into Open Policy Agent bundles and evaluated server-side during admission. A typical policy might enforce that all pods in production namespaces must specify resource limits, must not run as root, must use images from an approved container registry, and must not mount host paths. The webhook operates synchronously in the API request path, meaning that policy violations block resource creation immediately, but this synchronous evaluation introduces latency—typically 50–200 milliseconds per admission request—and creates a single point of failure: if the webhook is unreachable due to network partition or pod crash, the API server's failurePolicy configuration determines whether requests are admitted (fail-open) or rejected (fail-closed).

Service account token issuance in modern Kubernetes (1.22+) uses the TokenRequest API and projected volume tokens, a significant security improvement over legacy static tokens. When a pod is created with a service account reference, the kubelet on the node calls the API server's TokenRequest endpoint, specifying the service account name, namespace, and requested token expiration (default one hour). The API server generates a signed JWT containing the service account identity, the pod's name and UID, and an expiration timestamp, signs it with a rotating private key, and returns the token to the kubelet. The kubelet writes this token to a tmpfs-backed projected volume at `/var/run/secrets/kubernetes.io/serviceaccount/token`, and the token is automatically rotated by the kubelet when 80% of its lifetime has elapsed. This rotation mechanism is critical because it limits the blast radius of token theft: an attacker exfiltrating a token from a compromised pod has at most 12 minutes (20% of one hour) to use the token before it becomes invalid. The rotation is transparent to the application, which simply re-reads the file to obtain a fresh token, but applications that cache the token in memory or persist it to disk will fail authentication after rotation.

Azure Active Directory group membership synchronization introduces eventual consistency concerns. When an administrator adds a user to an Azure AD group that is referenced in a Kubernetes RoleBinding, the user does not immediately gain the associated permissions. The delay has three components: first, Azure AD's internal replication latency, typically under one second for global catalog updates; second, the token refresh interval, which depends on the client's credential caching strategy but typically ranges from 5 to 60 minutes for cached access tokens; third, the API server's group membership cache, which is populated from the `groups` claim in the JWT and does not refresh until the user obtains a new token. This means that in practice, group membership changes can take up to an hour to propagate to active sessions. The workaround for urgent access grants is to force credential refresh by running `az aks get-credentials --overwrite-existing`, which discards cached tokens and initiates a new OAuth flow.

Network policy enforcement in AKS with Azure CNI operates at the iptables layer on each node. When a NetworkPolicy object is created, the network policy controller—either the Azure-native implementation or Calico—watches the API server for policy changes, computes the set of iptables rules required to implement the policy, and programs those rules into the kernel's netfilter subsystem on every node. The rule generation algorithm is complex because it must handle dynamic pod IP assignment, pod label selectors, namespace selectors, and CIDR-based ingress/egress rules. A typical policy denying all ingress to pods labeled `app=database` in namespace `production` translates to an iptables rule that matches destination IP addresses in the pod CIDR range assigned to `app=database` pods and has a jump target of DROP. The policy controller maintains a mapping from pod labels to IP addresses by watching pod events, and when a pod is created or its IP changes, the controller updates the iptables rules accordingly.

The critical implementation detail is that iptables rule updates are not atomic across the cluster. When a new NetworkPolicy is created, there is a propagation window—typically 1–5 seconds—during which some nodes have installed the new rules and others have not. During this window, network connectivity is inconsistent: a client pod on an updated node will have its traffic blocked, while a client pod on a non-updated node can still reach the target. This inconsistency is usually harmless for deny policies, because the worst-case outcome is delayed enforcement, but it becomes problematic for allow policies that carve out exceptions to a default-deny baseline. The production-grade solution is to always apply allow policies before deny policies, and to introduce a delay—typically 10 seconds—between policy creation and workload deployment to ensure convergence.

Azure Key Vault integration via the Secrets Store CSI Driver replaces the traditional Kubernetes Secret workflow with a direct mount of Key Vault secrets into pod filesystems. The architecture consists of three components: the CSI driver DaemonSet, which runs a privileged pod on every node and implements the CSI volume plugin interface; the Azure Key Vault provider, which handles authentication to Key Vault using pod-assigned managed identities; and the SecretProviderClass custom resource, which declares which secrets to fetch and how to expose them as files. When a pod referencing a SecretProviderClass volume is scheduled, the kubelet invokes the CSI driver's NodePublishVolume gRPC method, passing the pod's service account and the SecretProviderClass specification. The CSI driver extracts the pod's Azure managed identity by calling the Azure Instance Metadata Service (IMDS) endpoint on the node, exchanges the managed identity token for a Key Vault access token, and uses that token to call the Key Vault API to retrieve secret values. The secrets are written to a tmpfs volume, mounted into the pod, and never touch etcd.

The authentication flow for managed identities merits detailed examination because it eliminates the need for shared secrets entirely. Each pod can be assigned a user-assigned managed identity via the `aadpodidbinding` label or the newer workload identity federation mechanism. When the pod starts, the CSI driver intercepts authentication requests and proxies them to the node's managed identity endpoint at `http://169.254.169.254/metadata/identity/oauth2/token`. This endpoint is implemented by the node's VM extension, which has privileged access to Azure's identity infrastructure and can mint OAuth tokens on behalf of the VM's assigned identities. The token minting process involves a secure hardware attestation flow where the Azure fabric controller verifies the VM's cryptographic identity before issuing tokens, ensuring that a compromised pod cannot impersonate a different VM or tenant. The issued token has a fixed audience claim for Key Vault and a one-hour expiration, after which the CSI driver automatically refreshes it.

Pod Security Standards, which replaced PodSecurityPolicies in Kubernetes 1.25, are enforced through namespace labels rather than admission webhooks. Each namespace is labeled with one of three security profiles: Privileged, which allows unrestricted pod creation; Baseline, which prohibits known privilege escalation paths such as hostPath mounts, host networking, and running as root; and Restricted, which enforces a hardened configuration including mandatory seccomp profiles, read-only root filesystems, and dropped Linux capabilities. The API server's PodSecurity admission plugin evaluates these labels synchronously during pod creation, comparing the pod's security context against the namespace's required profile and rejecting the pod if it violates constraints. The enforcement is deterministic and does not depend on external webhooks, eliminating the latency and availability concerns of PodSecurityPolicy, but it also eliminates the ability to write custom policy logic or generate audit events in external systems.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         AAD-Integrated AKS Cluster                      │
└─────────────────────────────────────────────────────────────────────────┘

  User: kubectl get pods -n production

    │
    │ 1. OAuth2 Authorization Code Flow
    ├──────────────────────────────────────────┐
    │                                          │
    v                                          v
┌─────────────────┐                  ┌──────────────────┐
│  Azure CLI /    │                  │   Azure Active   │
│  kubeconfig     │◄─────────────────│    Directory     │
│  exec plugin    │   JWT Token      │  (OIDC Provider) │
└─────────────────┘                  └──────────────────┘
    │
    │ 2. HTTP: Authorization Bearer <JWT>
    │
    v
┌─────────────────────────────────────────────────────────┐
│                     kube-apiserver                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Authentication Chain                             │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │ OIDC Authenticator                          │  │  │
│  │  │  - Verify JWT signature (JWKS)              │  │  │
│  │  │  - Validate iss, aud, exp claims            │  │  │
│  │  │  - Extract oid → username                   │  │  │
│  │  │  - Extract groups[] → group memberships     │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         v                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Authorization (RBAC)                             │  │
│  │  - Query etcd RBAC cache                          │  │
│  │  - Match user/groups against RoleBindings         │  │
│  │  - Compute union of allowed verbs/resources       │  │
│  └─────────────────────┬─────────────────────────────┘  │
│                        v                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Admission Control                                │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │ Mutating Webhooks (ordered)                  │ │  │
│  │  │  - Azure Policy webhook                      │ │  │
│  │  │  - Secrets Store CSI webhook                 │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │ Validating Webhooks                          │ │  │
│  │  │  - OPA Gatekeeper                            │ │  │
│  │  │  - Custom admission logic                    │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │ PodSecurity Admission                        │ │  │
│  │  │  - Evaluate namespace security profile       │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  └──────────────────────┬────────────────────────────┘  │
└─────────────────────────┼───────────────────────────────┘
                          v
                    ┌──────────┐
                    │   etcd   │
                    │  (MVCC)  │
                    └──────────┘
```

The interaction between Azure RBAC and Kubernetes RBAC introduces a double-authorization pattern that many operators find confusing. An AKS cluster can be configured with Azure RBAC integration, which adds a second authorization layer before Kubernetes RBAC evaluation. In this mode, every API request must pass two separate authorization checks: first, Azure Resource Manager verifies that the user has the appropriate Azure role assignment (such as Azure Kubernetes Service Cluster User Role) scoped to the AKS cluster resource; second, the Kubernetes API server evaluates RBAC as described above. The intent is to provide centralized governance at the Azure subscription level, allowing security teams to enforce organization-wide access policies without modifying hundreds of individual Kubernetes RoleBindings. The cost is increased latency—every API call now requires a round-trip to Azure's ARM control plane—and a new failure mode where users with correct Kubernetes RBAC permissions are denied access due to missing Azure role assignments.

## 3. High-Performance Optimization & Failure Modes

The primary performance bottleneck in large-scale RBAC deployments is the API server's authorization cache invalidation algorithm. Every time a RoleBinding or ClusterRoleBinding is created, updated, or deleted, the API server must rebuild its internal authorization index, a process that involves traversing all bindings, expanding group memberships, and recomputing the permission matrix for potentially thousands of subjects. This recomputation is synchronous and holds a global lock, meaning that during the rebuild, all authorization decisions are blocked and API requests queue. In clusters with thousands of RoleBindings—common in multi-tenant platforms with namespace-per-customer isolation—a burst of binding updates can stall the API server for several seconds. The production-grade mitigation is to batch RoleBinding updates and apply them during maintenance windows, and to use ClusterRoleBindings sparingly, since each ClusterRoleBinding affects the global authorization index and triggers a full rebuild.

The second performance consideration is webhook admission latency. Every mutating and validating webhook operates synchronously in the API request path, and the API server enforces a default 30-second timeout per webhook. In high-throughput environments—such as continuous deployment pipelines creating thousands of pods per minute—webhook latency compounds multiplicatively. If you have three mutating webhooks with 100-millisecond latency each and two validating webhooks with 50-millisecond latency each, every pod creation incurs at least 400 milliseconds of overhead before reaching etcd. The mitigation strategies are threefold: first, optimize webhook implementations to minimize external API calls and database lookups, targeting sub-50-millisecond response times; second, use namespace selectors and object selectors in webhook configurations to limit evaluation to only relevant resources, avoiding unnecessary invocations; third, deploy webhook backends with sufficient horizontal scaling and health probing to ensure availability under load.

Network policy performance degrades non-linearly with the number of policies and the complexity of label selectors. Each NetworkPolicy translates to a set of iptables rules, and iptables rule evaluation is linear: every packet traverses the entire rule chain until a matching rule is found. In clusters with hundreds of NetworkPolicies, each targeting different label selectors, the iptables rule count can exceed tens of thousands of rules per node. At this scale, packet processing latency becomes measurable, and high-throughput workloads—such as database replicas or message queue consumers—experience throughput degradation. The production-grade solution is to migrate from iptables-based policy enforcement to eBPF-based enforcement using Cilium, which uses hash-table lookups instead of linear rule traversal and achieves constant-time policy evaluation regardless of policy count. However, Cilium requires Linux kernel 4.19+ with eBPF support, and AKS's default Ubuntu node images satisfy this requirement only in recent releases.

The most insidious failure mode in AAD-integrated clusters is token expiration during long-running operations. The default access token lifetime from Azure AD is one hour, and kubeconfig exec plugins cache tokens in memory. If an operator starts a long-running kubectl command—such as `kubectl logs -f` or `kubectl port-forward`—the initial authentication succeeds, but the underlying HTTP/2 connection remains open. When the token expires after one hour, the API server begins rejecting subsequent requests on that connection, but kubectl does not automatically re-authenticate because the connection is still alive. The user experiences intermittent failures with cryptic authentication errors, and the only resolution is to terminate the kubectl process and restart. The workaround is to use the `--token-cache-path` flag in the kubeconfig exec plugin to persist tokens to disk and enable background refresh, or to switch to a service account-based kubeconfig for automated tooling.

Secrets Store CSI Driver introduces a new failure domain: Key Vault availability. Because secrets are fetched at pod startup, any Key Vault outage or throttling event delays pod scheduling. Azure Key Vault enforces per-vault rate limits—typically 1000 requests per 10 seconds for secret reads—and a cluster with high pod churn can exhaust these limits, causing pod creation to fail with `FailedMount` events. The mitigation is to implement exponential backoff in the CSI driver configuration and to enable Key Vault's soft-delete and purge protection features, which maintain a 90-day recovery window for accidentally deleted secrets. For critical workloads, consider replicating Key Vault secrets to multiple vaults across regions and configuring the SecretProviderClass to fail over automatically.

The Pod Security Standards enforcement introduces a subtle breaking change for legacy workloads that relied on default security contexts. A pod that previously ran without an explicit security context—implicitly running as root, with all capabilities, and without resource limits—will be rejected in a namespace labeled with the Baseline or Restricted profile. The error message is often unhelpful, simply stating "pod does not meet policy requirements" without enumerating which specific constraints failed. The debugging workflow requires examining the pod's security context field by field and cross-referencing it against the Pod Security Standards specification. The production-grade approach is to enable the audit and warn modes first, which log violations without blocking pod creation, allowing you to identify affected workloads and remediate their security contexts before switching to enforce mode.

RBAC policy sprawl is the most common operational failure mode in mature clusters. Over months and years, as teams provision new namespaces, onboard new services, and grant temporary access for incident response, the number of RoleBindings grows without bound. Many organizations accumulate thousands of bindings, many referencing long-departed users or deprecated service accounts. This sprawl has three negative consequences: it increases API server authorization cache rebuild time, it obscures the actual permission landscape making security audits intractable, and it violates least-privilege principles by leaving stale permissions active. The mitigation requires tooling for RBAC audit and cleanup. The kubectl-who-can plugin allows querying "who can perform verb X on resource Y in namespace Z?" by brute-force enumerating all bindings, but this approach does not scale beyond a few hundred bindings. The production-grade solution is to export all RBAC objects to a graph database, model subjects, roles, and bindings as nodes and edges, and use graph traversal queries to identify unused bindings, over-privileged service accounts, and transitive permission escalation paths.

Azure Policy enforcement introduces a failure mode where policies authored in Azure Portal do not propagate to AKS clusters due to misconfigured policy assignments or scope inheritance issues. Azure Policy operates through a two-tier architecture: policies are authored and assigned at the Azure Resource Manager level, then compiled into Open Policy Agent constraint templates and deployed to clusters via the Azure Policy add-on. If the add-on is unhealthy—due to image pull failures, webhook certificate expiration, or conflicting admission webhooks—policies appear active in Azure Portal but are not enforced in the cluster. The debugging workflow requires examining the `gatekeeper-system` namespace, checking the status of ConstraintTemplate and Constraint objects, and tailing the gatekeeper-audit pod logs to identify policy evaluation errors.

The final critical failure mode is RBAC escalation via impersonation. Kubernetes RBAC includes a rarely-used feature allowing a user to impersonate another user or service account by including `Impersonate-User` and `Impersonate-Group` headers in API requests. If a RoleBinding grants the `impersonate` verb on user or serviceaccount resources, the bound user can effectively assume the identity of any other principal in the cluster, including cluster-admin. This is an intentional privilege escalation vector, designed for building delegated authentication proxies, but it is frequently granted accidentally by over-broad bindings such as `verbs: ["*"]` or copy-pasted example manifests. The production-grade defense is to audit all RoleBindings for the `impersonate` verb and remove it unless explicitly justified, and to implement admission webhooks that deny RoleBindings granting impersonation outside of designated system namespaces.

Concrete production configuration for a multi-tenant AKS cluster with hardened security posture follows:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-alpha
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: workload-identity
  namespace: tenant-alpha
  annotations:
    azure.workload.identity/client-id: "12345678-1234-1234-1234-123456789abc"
automountServiceAccountToken: false
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tenant-alpha-developer
  namespace: tenant-alpha
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "jobs", "services", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["get", "create"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
  resourceNames: ["app-config-secret"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-alpha-developers
  namespace: tenant-alpha
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: tenant-alpha-developer
subjects:
- kind: Group
  name: "a1b2c3d4-5678-90ab-cdef-1234567890ab"
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: tenant-alpha
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-to-database
  namespace: tenant-alpha
spec:
  podSelector:
    matchLabels:
      app: web-frontend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
---
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-keyvault-tenant-alpha
  namespace: tenant-alpha
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "false"
    clientID: "12345678-1234-1234-1234-123456789abc"
    keyvaultName: "tenant-alpha-vault"
    cloudName: "AzurePublicCloud"
    objects: |
      array:
        - |
          objectName: database-password
          objectType: secret
          objectVersion: ""
        - |
          objectName: api-key
          objectType: secret
          objectVersion: ""
    tenantId: "87654321-4321-4321-4321-cba987654321"
  secretObjects:
  - secretName: app-config-secret
    type: Opaque
    data:
    - objectName: database-password
      key: DB_PASSWORD
    - objectName: api-key
      key: API_KEY
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
  namespace: tenant-alpha
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-frontend
  template:
    metadata:
      labels:
        app: web-frontend
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: workload-identity
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: tenantalpharegistry.azurecr.io/web-frontend:v2.1.0
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        ports:
        - containerPort: 8080
          protocol: TCP
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-config-secret
              key: DB_PASSWORD
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: app-config-secret
              key: API_KEY
        volumeMounts:
        - name: secrets-store
          mountPath: "/mnt/secrets-store"
          readOnly: true
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: secrets-store
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: azure-keyvault-tenant-alpha
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
```

The deployment manifest demonstrates defense-in-depth layering: the namespace enforces Pod Security Standards at the Restricted level, rejecting any pod that violates hardened security constraints; the service account disables automatic token mounting, eliminating API credential exposure to the application; the RBAC Role grants only specific verbs on specific resources, avoiding wildcard permissions; the default-deny NetworkPolicy blocks all traffic by default, with a second policy carving out an explicit allow path from frontend to database; the SecretProviderClass fetches secrets from Azure Key Vault using workload identity federation, bypassing Kubernetes Secrets entirely; the pod security context enforces non-root execution, read-only root filesystem, and dropped capabilities; resource limits prevent unbounded CPU or memory consumption; and the CSI volume mount provides secrets without storing them in etcd.

The critical operational invariant is that security posture degrades over time without active maintenance. Role bindings accumulate, network policies become stale as workload topologies evolve, and container images age and accumulate vulnerabilities. Production-grade security requires continuous audit tooling: scanning RoleBindings for over-privileged grants, validating NetworkPolicy coverage with connectivity tests, rotating secrets on fixed schedules, and scanning container images for CVEs at build time and runtime. The investment in automation for these continuous verification workflows far exceeds the initial cluster setup cost, but it is the only path to maintaining security posture across the multi-year lifecycle of a production platform.
