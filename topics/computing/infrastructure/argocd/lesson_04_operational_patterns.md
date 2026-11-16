# Lesson 4: Operational Patterns and Multi-Cluster Deployment

## 1. First-Principles Intuition & Invariants

The entire ArgoCD control plane exists to answer one question with mechanical precision: does the live state of a Kubernetes cluster match the declarative state expressed in a Git repository? Every operational pattern, every RBAC rule, every notification trigger, and every multi-cluster deployment strategy is a consequence of how that question is answered, how often, and against how many targets. Understanding the invariants that govern this reconciliation is what separates a working ArgoCD installation from a production-grade one.

The first invariant is that Git is the single source of truth. This is not a preference or a recommendation; it is a hard constraint that propagates through every layer of the system. When an operator runs `kubectl apply` directly against a cluster under ArgoCD management with auto-sync enabled, the controller detects the divergence on its next reconciliation pass and reverts the change. The system has no concept of "intent" outside the repository. This means that every operational action—scaling a deployment, updating a ConfigMap, rolling back a release—must be expressed as a Git commit. The practical consequence is that your Git infrastructure (repository hosting, branch protection, CI pipelines) becomes part of your cluster control plane. A Git outage is functionally equivalent to a control plane outage for new deployments, though existing applications continue to be reconciled against the last-known revision cached in the repository server.

The second invariant is that reconciliation is level-triggered, not edge-triggered. ArgoCD does not respond to events; it responds to state. The application controller maintains a watch on three independent signal sources: Application CRD changes in the ArgoCD cluster, Git revision changes reported by the repository server, and live resource changes reported by the target cluster's API server. When any of these signals indicate a potential divergence, the controller performs a full diff between the desired state (manifests rendered from Git) and the live state (resources fetched from the target cluster). This level-triggered model means that the system is self-correcting: if a resource is deleted out-of-band, the next reconciliation pass recreates it. If a field is modified, it is overwritten. The cost of this property is continuous polling and diffing, which is why scaling the controller is fundamentally about managing the computational expense of those diffs across thousands of applications and dozens of clusters.

The third invariant is that the reconciliation loop must be idempotent and convergent. Applying the same Git revision to the same cluster twice must produce the same result. The system must converge toward the desired state regardless of the starting state. This is why ArgoCD uses server-side apply semantics and why the sync engine tracks the concept of a "sync operation" as a discrete, auditable unit rather than a streaming mutation. Each sync operation is recorded in the Application's status with a revision, a timestamp, an initiator, and a phase (Running, Succeeded, Failed, Error). The operation history is bounded but provides an audit trail that is independent of Git history—the sync operation records what ArgoCD actually did to the cluster, not what was committed to the repository.

When you extend these invariants across multiple clusters, the topology decision becomes the central architectural question. ArgoCD supports two fundamental deployment topologies: a hub-and-spoke model where a single ArgoCD instance manages multiple target clusters, and a distributed model where each cluster runs its own ArgoCD instance. The hub-and-spoke model centralizes control, provides a single pane of glass for observability, and simplifies RBAC management, but it creates a single point of failure and introduces network latency between the control plane and the target clusters. The distributed model eliminates the cross-cluster network dependency and contains blast radius to individual clusters, but it multiplies operational overhead and complicates consistency across environments.

In practice, most production deployments adopt a hybrid: a few hub-and-spoke ArgoCD instances, each managing a bounded set of clusters within a region or organizational boundary. The boundary is drawn based on network latency (the repo server must be able to clone repositories and the controller must be able to query cluster APIs within acceptable timeout windows), organizational trust (different teams may require isolated control planes), and blast radius (a single ArgoCD instance managing 200 clusters creates an unacceptable concentration of risk). The ApplicationSet controller, which we will examine in detail, is the mechanism that makes the hub-and-spoke model scalable: it generates Application resources from templates and generators, allowing a single Git repository to fan out deployments across dozens of clusters without manually creating individual Application manifests.

## 2. Core Architecture & Mechanics

### 2.1 The Application Controller Reconciliation Engine

The application controller is the beating heart of ArgoCD. It is a single binary (running as a Kubernetes Deployment or StatefulSet) that embeds multiple independent reconciliation loops, each running as a pool of goroutines with configurable parallelism. Understanding the internal architecture of this controller is essential for capacity planning and failure diagnosis.

The controller maintains three internal processor pools. The status processor pool, sized by `--status-processors`, handles the core reconciliation: comparing desired state against live state and updating the Application's status. The operation processor pool, sized by `--operation-processors`, handles sync operations: the actual apply, delete, and hook execution against target clusters. The kubectl parallelism limiter, controlled by `--kubectl-parallelism-limit`, caps the number of concurrent kubectl operations during a single sync, preventing API server overload on target clusters.

The reconciliation flow for a single Application proceeds as follows. The controller watches for changes to Application CRDs, Git repository revisions (reported by the repo server), and live resource states (reported by informers against target cluster API servers). When a change is detected, the Application is enqueued into the status processor's work queue. The status processor fetches the rendered manifests from the repo server (either directly or via the Redis cache), fetches the live resources from the target cluster, and performs a structural diff. The diff result determines the sync status: `Synced` if desired and live match, `OutOfSync` if they diverge. Health status is computed separately by applying health check Lua functions to each resource in the live state.

```mermaid
graph TB
    GitRepo[Git Repository] -->|"fetch revision"| RepoServer[Repo Server]
    RepoServer -->|"render manifests"| Redis["(Redis Cache)"]
    Redis -->|"cached manifests"| AppController[Application Controller]
    AppController -->|"status processors"| Diff[Structural Diff Engine]
    TargetCluster1[Target Cluster A] -->|"live state informers"| AppController
    TargetCluster2[Target Cluster B] -->|"live state informers"| AppController
    Diff -->|"update status"| AppCRD[Application CRD Status]
    Diff -->|"trigger sync"| SyncEngine[Sync Operation Engine]
    SyncEngine -->|"kubectl apply"| TargetCluster1
    SyncEngine -->|"kubectl apply"| TargetCluster2
    SyncEngine -->|"hooks/pre/post"| TargetCluster1
```

The diff engine itself is a structural comparison, not a textual one. ArgoCD normalizes both the desired and live manifests before comparison: it removes server-generated fields (resourceVersion, uid, creationTimestamp, managedFields), applies `ignoreDifferences` rules from the Application spec and from the `argocd-cm` ConfigMap, and strips fields known to be mutated by admission controllers or other in-cluster controllers. This normalization is critical because without it, every reconciliation would report false positives due to fields like `status` that are maintained by the cluster, not by Git.

### 2.2 Multi-Cluster Registration and the Trust Model

Registering a target cluster with ArgoCD is an act of establishing trust: the target cluster must trust ArgoCD with credentials sufficient to manage resources, and ArgoCD must trust the target cluster's API server certificate. The registration process creates a Kubernetes Secret in the ArgoCD namespace that encodes both sides of this trust relationship.

The simplest registration path uses the `argocd cluster add` CLI, which creates a ServiceAccount on the target cluster, binds it to a ClusterRole (by default `cluster-admin`, which should never be used in production), generates a bearer token, and stores the connection details as a Secret in the ArgoCD namespace:

```bash
argocd cluster add prod-us-east-1-context \
  --label environment=production \
  --label platform=payments \
  --label region=us-east-1 \
  --service-account argocd-manager \
  --system-namespace argocd-system
```

This command performs several operations. It creates a ServiceAccount named `argocd-manager` in the `argocd-system` namespace on the target cluster, generates a long-lived bearer token for that ServiceAccount, creates a ClusterRoleBinding granting that ServiceAccount the specified role, and stores the resulting kubeconfig as a Secret in the ArgoCD control plane namespace. The labels applied here are not cosmetic: they are selectors used by ApplicationSet cluster generators to determine which clusters should receive which applications.

For production, the default `cluster-admin` binding is unacceptable. The target cluster needs a precisely scoped ClusterRole that grants ArgoCD the minimum permissions to manage the resources it will deploy. The following manifest defines a ServiceAccount, a least-privilege ClusterRole, and a binding that should be applied to every target cluster before registration:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argocd-manager
  namespace: argocd-system
---
apiVersion: v1
kind: Secret
metadata:
  name: argocd-manager-token
  namespace: argocd-system
  annotations:
    kubernetes.io/service-account.name: argocd-manager
type: kubernetes.io/service-account-token
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: argocd-manager-role
rules:
  - apiGroups: [""]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["apps"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["extensions"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["policy"]
    resources: ["poddisruptionbudgets"]
    verbs: ["*"]
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["*"]
  - apiGroups: ["batch"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["argoproj.io"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["cert-manager.io"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["external-secrets.io"]
    resources: ["*"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: argocd-manager-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: argocd-manager-role
subjects:
  - kind: ServiceAccount
    name: argocd-manager
    namespace: argocd-system
```

The resulting cluster Secret in the ArgoCD namespace has a specific structure. Rather than relying on the CLI, you can create it manually for clusters that cannot be reached by `argocd cluster add` (for example, clusters behind a bastion host or in a different network partition):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cluster-prod-us-east-1
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: cluster
    environment: production
    platform: payments
    region: us-east-1
type: Opaque
stringData:
  name: prod-us-east-1
  server: https://10.0.1.100:6443
  config: |
    {
      "bearerToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ik1D...",
      "tlsClientConfig": {
        "insecureSkipVerify": false,
        "caData": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t..."
      }
    }
```

The `config` field is a JSON-encoded kubeconfig that contains the authentication credentials and TLS settings. The `caData` field holds the base64-encoded CA certificate of the target cluster's API server. Setting `insecureSkipVerify` to `true` disables TLS certificate validation, which should never be done in production because it exposes the control plane to man-in-the-middle attacks against cluster API traffic.

The trust model has a subtle but important implication for cluster retirement. When you remove a cluster from ArgoCD by deleting its Secret, the ServiceAccount and its token on the target cluster remain. The cluster is no longer managed, but the credentials are still valid. A proper decommissioning process must revoke the ServiceAccount token on the target cluster as well as deleting the Secret in the ArgoCD namespace. For environments using short-lived tokens via the TokenRequest API, this is handled automatically by token expiry, which is why token rotation should be a first-class operational concern.

### 2.3 AppProject: The Isolation Boundary

An AppProject is ArgoCD's primary mechanism for multi-tenancy and blast-radius containment. It defines a closed set of permissions: which Git repositories can be used as sources, which clusters and namespaces can be targeted, which Kubernetes resource types can be deployed, and which users can perform which actions. Every Application must belong to exactly one AppProject, and the AppProject's constraints are enforced at the controller level—the controller will refuse to sync an Application whose source repository is not listed in the project's `sourceRepos`, or whose target namespace is not in the project's `destinations`.

The AppProject is not a namespace-level resource; it lives in the `argocd` namespace and is cluster-scoped in terms of its authority. This means that an AppProject can govern applications deployed to any namespace on any registered cluster, but the project itself is managed by ArgoCD administrators. The separation between project administration (who can create and modify AppProjects) and project usage (who can create Applications within a project) is the foundation of the multi-tenancy model.

The following AppProject definition demonstrates all of the major isolation controls:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: payments-platform
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  description: Payments platform multi-cluster deployment project
  sourceRepos:
    - https://github.com/payments-org/manifests.git
    - https://github.com/payments-org/helm-charts.git
    - ssh://git@internal-git.payments.org:2224/payments/sealed-secrets.git
  destinations:
    - server: https://10.0.1.100:6443
      namespace: payments-*
    - server: https://10.0.2.100:6443
      namespace: payments-*
    - server: https://kubernetes.default.svc
      namespace: payments-*
  clusterResourceWhitelist:
    - group: ""
      kind: Namespace
    - group: rbac.authorization.k8s.io
      kind: ClusterRole
    - group: rbac.authorization.k8s.io
      kind: ClusterRoleBinding
    - group: cert-manager.io
      kind: ClusterIssuer
  clusterResourceBlacklist:
    - group: ""
      kind: ""
  namespaceResourceWhitelist:
    - group: ""
      kind: ConfigMap
    - group: ""
      kind: Secret
    - group: ""
      kind: Service
    - group: ""
      kind: ServiceAccount
    - group: apps
      kind: Deployment
    - group: apps
      kind: StatefulSet
    - group: apps
      kind: DaemonSet
    - group: networking.k8s.io
      kind: Ingress
    - group: networking.k8s.io
      kind: NetworkPolicy
    - group: policy
      kind: PodDisruptionBudget
    - group: autoscaling
      kind: HorizontalPodAutoscaler
    - group: argoproj.io
      kind: Rollout
    - group: argoproj.io
      kind: AnalysisTemplate
    - group: external-secrets.io
      kind: ExternalSecret
    - group: external-secrets.io
      kind: SecretStore
  namespaceResourceBlacklist:
    - group: ""
      kind: ResourceQuota
    - group: ""
      kind: LimitRange
  orphanedResources:
    warn: true
  roles:
    - name: deployer
      description: Can sync and sync applications within payments-platform
      policies:
        - p, proj:payments-platform:deployer, applications, get, payments-platform/*, allow
        - p, proj:payments-platform:deployer, applications, sync, payments-platform/*, allow
        - p, proj:payments-platform:deployer, applications, action/*, payments-platform/*, allow
      groups:
        - payments-engineering
        - sre-payments
    - name: viewer
      description: Read-only access to payments-platform applications
      policies:
        - p, proj:payments-platform:viewer, applications, get, payments-platform/*, allow
        - p, proj:payments-platform:viewer, logs, get, payments-platform/*, allow
      groups:
        - payments-qa
        - payments-incidents
  syncWindows:
    - kind: allow
      schedule: "0 9 * * 1-5"
      duration: 8h
      applications:
        - "*"
      namespaces:
        - "payments-*"
      clusters:
        - "prod-us-east-1"
        - "prod-eu-west-1"
      manualSync: true
    - kind: deny
      schedule: "0 0 * * 6,0"
      duration: 48h
      applications:
        - "*"
      namespaces:
        - "payments-*"
      clusters:
        - "prod-us-east-1"
        - "prod-eu-west-1"
      manualSync: false
```

The `sourceRepos` list is an allowlist: only Applications whose `repoURL` matches one of these entries can be created in this project. This prevents a team from accidentally deploying manifests from an uncontrolled repository. The `destinations` list constrains where applications can be deployed, using glob patterns for namespace matching. The `clusterResourceWhitelist` and `namespaceResourceWhitelist` restrict which Kubernetes resource types the project can manage. When a whitelist is non-empty, any resource type not listed is implicitly denied. The `clusterResourceBlacklist` and `namespaceResourceBlacklist` provide additional deny rules that take precedence over whitelists. This whitelist-blacklist combination allows you to express policies like "this project can deploy anything except LimitRange and ResourceQuota objects," which prevents a team from clobbering platform-level resource governance.

The `orphanedResources` field with `warn: true` instructs ArgoCD to report but not block when a sync operation would orphan resources (resources that exist in the cluster but not in Git). This is a safety net for pruning operations, which we will discuss in the context of sync policies.

The `syncWindows` section defines time-based restrictions on when syncs can occur. The example above allows syncs only during business hours on weekdays (9:00 to 17:00) and blocks all syncs on weekends. The `manualSync: true` on the allow window means that even during the allowed window, automated syncs are suppressed and only manual syncs are permitted. This is useful for environments where you want human approval for every deployment but still want to restrict when deployments can happen.

### 2.4 RBAC Policy Model

ArgoCD's RBAC system uses a policy definition language based on Casbin, expressed as a CSV-formatted policy embedded in the `argocd-rbac-cm` ConfigMap. The policy model defines subjects (users or groups), resources (applications, clusters, projects, repositories, certificates, accounts, logs, exec), actions (get, create, update, delete, sync, action/*), and objects (resource identifiers, often with glob patterns). The policy resolution order is: project-level policies take precedence for application-scoped resources, then global policies in the ConfigMap, then the default policy.

The global RBAC ConfigMap is the entry point for cluster-wide authorization rules:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    p, role:platform-admin, *, *, *, *, allow
    p, role:payments-deployer, applications, get, payments-platform/*, allow
    p, role:payments-deployer, applications, sync, payments-platform/*, allow
    p, role:payments-deployer, applications, create, payments-platform/*, allow
    p, role:payments-deployer, applications, update, payments-platform/*, allow
    p, role:payments-deployer, applications, delete, payments-platform/*, allow
    p, role:payments-deployer, applications, action/*, payments-platform/*, allow
    p, role:payments-deployer, projects, get, payments-platform, allow
    p, role:payments-deployer, logs, get, payments-platform/*, allow
    p, role:payments-deployer, exec, create, payments-platform/*, allow
    p, role:viewer, applications, get, */*, allow
    p, role:viewer, projects, get, *, allow
    p, role:viewer, clusters, get, *, allow
    p, role:viewer, repositories, get, *, allow
    p, role:viewer, logs, get, */*, allow
    p, role:viewer, applicationsets, get, */*, allow
    p, role:security-auditor, applications, get, */*, allow
    p, role:security-auditor, clusters, get, *, allow
    p, role:security-auditor, certificates, get, *, allow
    p, role:security-auditor, repositories, get, *, allow
    p, role:security-auditor, accounts, get, *, allow
    g, payments-engineering, role:payments-deployer
    g, sre-payments, role:payments-deployer
    g, payments-qa, role:viewer
    g, payments-incidents, role:viewer
    g, platform-team, role:platform-admin
    g, security-team, role:security-auditor
  scopes: "[groups, email]"
```

The policy CSV follows a five-field format: `p, subject, resource, action, object, effect`. The `g` lines define group memberships, mapping OIDC/SAML groups to roles. The `scopes` field determines which claims from the authentication token are used for group resolution; listing `groups` first means the OIDC `groups` claim is the primary source of group identity.

The `action/*` permission in the policy is worth attention. ArgoCD supports custom actions on applications, such as "restart," "refresh," and any custom actions registered via resource customizations. Granting `action/*` allows a user to perform all registered actions, which in practice means they can trigger refreshes, restart pods, and run any custom action defined in Lua. This is broader than `sync` alone, which only permits sync operations.

The `policy.default` field sets the role assigned to any authenticated user who does not match any group mapping. Setting it to `role:readonly` is the standard production posture: authenticated users can see everything but change nothing. Setting it to an empty string denies all access by default, which is appropriate for environments where every user must be explicitly assigned to a role.

Validating the policy before applying it is critical because a syntax error in the policy CSV silently disables all RBAC, potentially granting unintended access. The ArgoCD CLI includes a validation command:

```bash
argocd admin settings rbac validate argocd-rbac-cm
```

This command parses the ConfigMap and reports any policy syntax errors, ensuring that a malformed policy never makes it to production. It should be run as a pre-commit check or CI step on any repository that manages the RBAC ConfigMap.

### 2.5 ApplicationSet for Multi-Cluster Fan-Out

The ApplicationSet controller is what makes large-scale multi-cluster deployment tractable. Instead of creating individual Application resources for each service on each cluster, you define a template and a set of generators that produce Application resources automatically. The controller watches the generators for changes and creates, updates, or deletes Application resources to match.

The cluster generator is the primary tool for multi-cluster fan-out. It enumerates clusters registered in ArgoCD, optionally filtered by label selectors, and produces a parameter set for each matching cluster. The following ApplicationSet deploys a payments platform stack to every production cluster tagged with the `platform: payments` label:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: payments-platform-multi-cluster
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
    - clusters:
        selector:
          matchLabels:
            environment: production
            platform: payments
        values:
          baseRef: main
          valuesFiles: |
            - values-{{metadata.labels.region}}.yaml
            - values-{{metadata.labels.environment}}.yaml
  template:
    metadata:
      name: 'payments-{{.name}}'
      annotations:
        notifications.argoproj.io/subscribe.on-deployed.slack: payments-deployments
        notifications.argoproj.io/subscribe.on-health-degraded.slack: payments-alerts
        notifications.argoproj.io/subscribe.on-sync-failed.slack: payments-alerts
      finalizers:
        - resources-finalizer.argocd.argoproj.io
    spec:
      project: payments-platform
      source:
        repoURL: https://github.com/payments-org/manifests.git
        targetRevision: '{{.values.baseRef}}'
        path: helm/payments-platform
        helm:
          valueFiles:
            - values-base.yaml
            - 'values-{{.metadata.labels.region}}.yaml'
          parameters:
            - name: cluster.name
              value: '{{.name}}'
            - name: cluster.region
              value: '{{.metadata.labels.region}}'
            - name: cluster.environment
              value: '{{.metadata.labels.environment}}'
          releaseName: payments
          namespace: payments-platform
          ignoreMissingValueFiles: false
      destination:
        server: '{{.server}}'
        namespace: payments-platform
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
          allowEmpty: false
        syncOptions:
          - CreateNamespace=true
          - PrunePropagationPolicy=foreground
          - PruneLast=true
          - ApplyOutOfSyncOnly=true
          - ServerSideApply=true
        retry:
          limit: 5
          backoff:
            duration: 5s
            factor: 2
            maxDuration: 3m
      revisionHistoryLimit: 20
```

The `goTemplate: true` field enables Go template syntax (instead of the older fasttemplate syntax) for parameter substitution, which provides richer expression capabilities including conditionals, range loops, and string functions. The `goTemplateOptions: ["missingkey=error"]` setting causes template rendering to fail if a referenced key does not exist, which prevents silent deployment of default values when an expected label or annotation is missing from a cluster.

The `values` block in the generator provides user-defined parameters that are available in the template under the `.values` key. This is distinct from the cluster's own metadata (available under `.metadata`) and its connection details (available under `.server`, `.name`). The separation allows you to inject deployment-specific parameters (like which Git branch to track) alongside cluster-specific parameters (like region and environment).

For environments where different services need to be deployed to different subsets of clusters, the matrix generator combines multiple generators. The following ApplicationSet deploys every service directory from a Git repository to every production cluster, creating a cartesian product of services and clusters:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: payments-services-multi-region
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
    - matrix:
        generators:
          - clusters:
              selector:
                matchLabels:
                  environment: production
                  platform: payments
          - git:
              repoURL: https://github.com/payments-org/manifests.git
              revision: main
              directories:
                - path: services/*
                  exclude: true
                - path: services/payments-api
                - path: services/transactions-service
                - path: services/fraud-detection
                - path: services/settlement-worker
  template:
    metadata:
      name: '{{.path.basename}}-{{.name}}'
      labels:
        app.kubernetes.io/name: '{{.path.basename}}'
        app.kubernetes.io/managed-by: argocd
      annotations:
        notifications.argoproj.io/subscribe.on-deployed.slack: payments-deployments
    spec:
      project: payments-platform
      source:
        repoURL: https://github.com/payments-org/manifests.git
        targetRevision: main
        path: '{{.path.path}}/overlays/{{.metadata.labels.environment}}'
      destination:
        server: '{{.server}}'
        namespace: '{{.path.basename}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - ServerSideApply=true
      revisionHistoryLimit: 10
```

The matrix generator produces one Application per combination of cluster and Git directory. With four service directories and three production clusters, this generates twelve Application resources. The `exclude: true` on the `services/*` path combined with the explicit path entries creates a whitelist: only the listed directories are included, excluding any other directories that might exist under `services/`. This prevents accidental deployment of a new service directory before it has been reviewed and added to the ApplicationSet.

### 2.6 The Notification System

ArgoCD's notification subsystem operates as a separate controller (deployed as `argocd-notifications-controller`) that watches Application and ApplicationSet resources for state changes and dispatches messages to configured services. The configuration is split across two resources: a ConfigMap (`argocd-notifications-cm`) that defines triggers, templates, and services, and a Secret (`argocd-notifications-secret`) that holds credentials for those services.

The notification pipeline works as follows. The controller watches Application CRD changes. When a change occurs, it evaluates each trigger's condition expression against the new Application state. If the condition matches, the trigger's referenced templates are rendered using Go templates with the Application object as context, and the rendered messages are sent to the services specified in the subscription annotation on the Application.

The ConfigMap defines the notification catalog. Each key follows the pattern `service.<type>`, `trigger.<name>`, or `template.<name>`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
    username: ArgoCD Deployments
    icon: ":rocket:"
    timeout: 30s
  service.webhook.paymentops: |
    url: http://paymentops-webhook.internal.svc:8080/argocd-events
    headers:
      - name: Authorization
        value: Bearer $webhook-token
      - name: Content-Type
        value: application/json
  service.webhook.pagerduty: |
    url: https://events.pagerduty.com/v2/enqueue
    headers:
      - name: Content-Type
        value: application/json
  context: |
    region: us-east-1
    platform: payments
    dashboard_url: https://argocd.payments.internal/applications
  trigger.on-deployed: |
    - when: app.status.operationState.phase in ["Succeeded"]
      send: [app-deployed, deploy-summary]
    - when: app.status.health.status == "Healthy"
      send: [app-healthy]
  trigger.on-health-degraded: |
    - when: app.status.health.status == "Degraded"
      send: [app-degraded, deploy-summary]
  trigger.on-sync-failed: |
    - when: app.status.operationState.phase in ["Error", "Failed"]
      send: [app-sync-failed, sync-error-detail]
  trigger.on-sync-running: |
    - when: app.status.operationState.phase in ["Running"]
      send: [app-sync-running]
  trigger.on-deleted: |
    - when: app.metadata.deletionTimestamp != nil
      send: [app-deleted]
  trigger.on-created: |
    - when: app.metadata.creationTimestamp != nil && app.status.operationState == nil
      send: [app-created]
  template.app-deployed: |
    message: |
      {{ .app.metadata.name }} deployed to {{ .app.spec.destination.server }}
      Sync revision: {{ .app.status.sync.revision | truncate 7 "" }}
      Author: {{ .app.status.operationState.operation.initiatedBy.username }}
      Project: {{ .app.spec.project }}
  template.app-degraded: |
    message: |
      HEALTH DEGRADED: {{ .app.metadata.name }}
      Cluster: {{ .app.spec.destination.server }}
      Namespace: {{ .app.spec.destination.namespace }}
      Status: {{ .app.status.health.status }}
      Message: {{ .app.status.health.message }}
      Last sync: {{ .app.status.operationState.finishedAt }}
      Dashboard: https://argocd.payments.internal/applications/{{ .app.metadata.name }}
  template.app-sync-failed: |
    message: |
      SYNC FAILED: {{ .app.metadata.name }}
      Phase: {{ .app.status.operationState.phase }}
      Message: {{ .app.status.operationState.message }}
      Revision: {{ .app.status.sync.revision | truncate 7 "" }}
      Started: {{ .app.status.operationState.startedAt }}
      Dashboard: https://argocd.payments.internal/applications/{{ .app.metadata.name }}
  template.deploy-summary: |
    message: |
      Deployment: {{ .app.metadata.name }}
      Target: {{ .app.spec.destination.server }}/{{ .app.spec.destination.namespace }}
      Revision: {{ .app.status.sync.revision | truncate 7 "" }}
      Resources: {{ len .app.status.resources }} total, {{ .app.status.summary.images | len }} images
      Sync status: {{ .app.status.sync.status }}
      Health: {{ .app.status.health.status }}
  template.app-deleted: |
    message: |
      APPLICATION DELETED: {{ .app.metadata.name }}
      Project: {{ .app.spec.project }}
      The application and all its managed resources are being pruned.
```

The corresponding Secret holds the credential references used by the services. The `$`-prefixed values in the service definitions are environment variable references resolved from this Secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: argocd-notifications-secret
  namespace: argocd
type: Opaque
stringData:
  slack-token: xoxb-YOUR-SLACK-BOT-TOKEN
  webhook-token: 7f4a8c2e9b1d3f5a8c2e9b1d3f5a8c2e
  pagerduty-routing-key: 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d
```

The subscription mechanism is what connects applications to notification triggers and services. Subscriptions are expressed as annotations on the Application or ApplicationSet resource. The annotation key follows the pattern `notifications.argoproj.io/subscribe.<trigger-name>.<service-type>` and the value specifies the destination (for Slack, the channel name; for webhooks, an empty string since the URL is in the service definition):

```yaml
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-deployed.slack: payments-deployments
    notifications.argoproj.io/subscribe.on-health-degraded.slack: payments-alerts
    notifications.argoproj.io/subscribe.on-sync-failed.slack: payments-alerts
    notifications.argoproj.io/subscribe.on-deployed.webhook.paymentops: ""
    notifications.argoproj.io/subscribe.on-health-degraded.webhook.pagerduty: ""
```

This annotation-based subscription model means that notification routing is decentralized: each application team configures its own notification destinations through annotations in its Application manifests, without requiring changes to the global notification ConfigMap. The ConfigMap defines what triggers and services exist; the annotations define which applications use them.

### 2.7 Progressive Delivery with Sync Waves and Argo Rollouts

ArgoCD's sync engine provides ordering control through sync waves. A sync wave is an integer annotation on a resource: `argocd.argoproj.io/sync-wave`. The controller sorts all resources in an Application by their wave value (ascending) and syncs them in that order, waiting for each resource in a wave to reach a healthy state before proceeding to the next wave. This allows you to express dependencies that the Kubernetes object model cannot express natively: for example, ensuring that a database Secret is created before a Deployment that references it, or that a namespace is created before any resources are deployed into it.

The following multi-document manifest demonstrates sync wave ordering for a typical service stack:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "-30"
---
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: payments-vault
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "-25"
spec:
  provider:
    vault:
      server: https://vault.payments.internal:8200
      path: payments
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes
          role: payments-api
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: payments-db-credentials
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "-20"
spec:
  secretStoreRef:
    name: payments-vault
    kind: SecretStore
  target:
    name: payments-db-credentials
    creationPolicy: Owner
  data:
    - secretKey: postgres-host
      remoteRef:
        key: payments/database
        property: host
    - secretKey: postgres-password
      remoteRef:
        key: payments/database
        property: password
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: payments-api-config
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "-15"
data:
  config.yaml: |
    database:
      hostSecret: payments-db-credentials
      hostKey: postgres-host
      passwordKey: postgres-password
      poolSize: 20
    redis:
      addr: redis.payments-api.svc:6379
    logging:
      level: info
      format: json
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: payments-api
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "-10"
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: payments-api
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "-10"
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: payments-api
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "-5"
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: payments-api
subjects:
  - kind: ServiceAccount
    name: payments-api
    namespace: payments-api
---
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: payments-api
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "0"
spec:
  replicas: 12
  strategy:
    canary:
      canaryService: payments-api-canary
      stableService: payments-api-stable
      trafficRouting:
        nginx:
          stableIngress: payments-api-ingress
          annotationPrefix: nginx.ingress.kubernetes.io
      steps:
        - setWeight: 5
        - pause:
            duration: 2m
        - analysis:
            templates:
              - templateName: success-rate-check
            args:
              - name: service-name
                value: payments-api-canary
        - setWeight: 25
        - pause:
            duration: 5m
        - setWeight: 50
        - analysis:
            templates:
              - templateName: success-rate-check
            args:
              - name: service-name
                value: payments-api-canary
        - setWeight: 75
        - pause:
            duration: 5m
  selector:
    matchLabels:
      app: payments-api
  template:
    metadata:
      labels:
        app: payments-api
    spec:
      serviceAccountName: payments-api
      containers:
        - name: api
          image: registry.payments.org/payments-api:v2.3.1
          ports:
            - containerPort: 8080
              name: http
              protocol: TCP
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
          envFrom:
            - secretRef:
                name: payments-db-credentials
            - configMapRef:
                name: payments-api-config
          readinessProbe:
            httpGet:
              path: /healthz/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 3
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: payments-api-stable
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "5"
spec:
  selector:
    app: payments-api
  ports:
    - port: 80
      targetPort: http
      name: http
---
apiVersion: v1
kind: Service
metadata:
  name: payments-api-canary
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "5"
spec:
  selector:
    app: payments-api
  ports:
    - port: 80
      targetPort: http
      name: http
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payments-api-ingress
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "10"
    nginx.ingress.kubernetes.io/canary: "false"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.payments.internal
      secretName: payments-api-tls
  rules:
    - host: api.payments.internal
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: payments-api-stable
                port:
                  name: http
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate-check
  namespace: payments-api
  annotations:
    argocd.argoproj.io/sync-wave: "15"
spec:
  args:
    - name: service-name
      value: ""
  metrics:
    - name: success-rate
      interval: 30s
      count: 10
      successCondition: result[0] >= 0.95
      failureLimit: 2
      inconclusiveLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",code!~"5.."}[2m]))
            /
            sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
    - name: latency-p99
      interval: 30s
      count: 10
      successCondition: result[0] <= 0.5
      failureLimit: 2
      inconclusiveLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}"}[2m]))
              by (le)
            )
```

This manifest ordering ensures that the namespace exists before anything else, the SecretStore is created before the ExternalSecret that references it, database credentials are available before the application starts, RBAC is in place before the pod is created, the Rollout and its supporting Services and Ingress are created in sequence, and the AnalysisTemplate (used by the Rollout's canary steps) is available before the Rollout reaches the analysis step.

The Rollout resource replaces a standard Deployment and is managed by the Argo Rollouts controller, which is a separate controller from ArgoCD. ArgoCD deploys the Rollout manifest; the Rollouts controller manages the canary progression. This separation is important because it means that ArgoCD's sync operation and the Rollout's progressive delivery are independent state machines. ArgoCD considers the Rollout "synced" when the manifest is applied; the health of the Rollout (which ArgoCD reports via a custom health check) reflects the canary progress.

To make ArgoCD understand Rollout health, you must register a health check in the `argocd-cm` ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  resource.customizations.health.argoproj.io_Rollout: |
    hs = {}
    if obj.status ~= nil then
      if obj.status.phase == "Healthy" then
        hs.status = "Healthy"
        hs.message = "Rollout is healthy"
        return hs
      end
      if obj.status.phase == "Degraded" then
        hs.status = "Degraded"
        hs.message = obj.status.message or "Rollout is degraded"
        return hs
      end
      if obj.status.phase == "Paused" then
        hs.status = "Suspended"
        hs.message = "Rollout is paused"
        return hs
      end
      if obj.status.phase == "Progressing" then
        hs.status = "Progressing"
        hs.message = obj.status.message or "Rollout is in progress"
        return hs
      end
    end
    hs.status = "Progressing"
    hs.message = "Waiting for rollout status"
    return hs
  resource.customizations.ignoreDifferences.argoproj.io_Rollout: |
    jsonPointers:
      - /spec/replicas
      - /status
  resource.customizations.ignoreDifferences.apps_Deployment: |
    jsonPointers:
      - /spec/replicas
      - /metadata/annotations/kubectl.kubernetes.io~1last-applied-configuration
      - /metadata/managedFields
  resource.customizations.ignoreDifferences.apps_StatefulSet: |
    jsonPointers:
      - /spec/replicas
      - /spec/podManagementPolicy
      - /status
  resource.customizations.ignoreDifferences.kubectl.kubernetes.io_last-applied-configuration: |
    jsonPointers:
      - /metadata/annotations
```

The `ignoreDifferences` entry for Rollout replicas is necessary because the Rollouts controller modifies the replica count during canary progression, and without this ignore rule, ArgoCD would report the Rollout as perpetually out-of-sync. The `~1` in the JSON pointer path escapes the forward slash in the annotation key, which is a detail of RFC 6901 JSON Pointer syntax that is easy to get wrong.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Controller Tuning and Sharding

The application controller is the primary bottleneck in large ArgoCD installations. Its performance is governed by three dimensions: the number of applications, the number of clusters, and the complexity of each application's manifest set. The controller's configuration must be tuned along all three axes.

The `--status-processors` flag controls the number of goroutines dedicated to status reconciliation (the diffing loop). The default is 20, which is adequate for approximately 100 applications. For larger installations, the heuristic is roughly one processor per 50 applications, capped by the controller pod's CPU allocation. The `--operation-processors` flag controls the number of goroutines dedicated to sync operations. The default is 10, and since syncs are I/O-bound (waiting for API server responses), this can be set higher relative to status processors. The `--kubectl-parallelism-limit` flag caps concurrent kubectl operations during a single sync, which protects target cluster API servers from thundering-herd sync operations.

The following controller deployment manifest shows a production-tuned configuration for an installation managing approximately 500 applications across 15 clusters:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: argocd-application-controller
  namespace: argocd
spec:
  replicas: 3
  serviceName: argocd-application-controller
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-application-controller
  template:
    metadata:
      labels:
        app.kubernetes.io/name: argocd-application-controller
    spec:
      serviceAccountName: argocd-application-controller
      containers:
        - name: argocd-application-controller
          image: quay.io/argoproj/argocd:v2.11.0
          command:
            - argocd-application-controller
          args:
            - --status-processors=40
            - --operation-processors=20
            - --kubectl-parallelism-limit=20
            - --app-resync=300s
            - --self-heal-timeout-seconds=300
            - --repo-server-timeout-seconds=120s
            - --redis-compress=true
            - --sharding-method=round-robin
            - --loglevel=info
            - --logformat=json
            - --sentinel
            - --redis
            argocd-redis-ha-announce-0.argocd-redis-ha.argocd:6379
            - --redis
            argocd-redis-ha-announce-1.argocd-redis-ha.argocd:6379
            - --redis
            argocd-redis-ha-announce-2.argocd-redis-ha.argocd:6379
          env:
            - name: ARGOCD_CONTROLLER_REPLICA
              value: "3"
            - name: ARGOCD_APPLICATION_NAMESPACES
              value: "payments-team,platform-team,security-team"
          ports:
            - containerPort: 8082
              name: metrics
            - containerPort: 8083
              name: grpc
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8082
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8082
            initialDelaySeconds: 30
            periodSeconds: 30
          resources:
            requests:
              cpu: 2000m
              memory: 4Gi
            limits:
              cpu: 4000m
              memory: 8Gi
          volumeMounts:
            - name: var-files
              mountPath: /var/run/argocd
      volumes:
        - name: var-files
          emptyDir: {}
```

The sharding mechanism is what makes the 3-replica StatefulSet work. Each replica is assigned a shard index (0, 1, 2) based on its ordinal in the StatefulSet. The `ARGOCD_CONTROLLER_REPLICA` environment variable tells each replica how many total shards exist. The `--sharding-method=round-robin` flag determines how clusters are assigned to shards: round-robin distributes clusters evenly, while the legacy method uses a hash of the cluster identifier. Each replica only reconciles Applications targeting clusters assigned to its shard, distributing the reconciliation load across the three pods.

The `ARGOCD_APPLICATION_NAMESPACES` environment variable enables Application resources to be created in namespaces other than `argocd`, which is essential for multi-tenancy. Without this, all Application resources must live in the `argocd` namespace, creating a single namespace that grows linearly with the number of applications. With it, each team can manage its Application resources in its own namespace, and the controller still reconciles them.

The `--app-resync=300s` flag sets the full reconciliation interval to 5 minutes. This is the interval at which every Application is fully re-reconciled regardless of whether a change was detected, serving as a safety net for missed watch events. The default is 3 minutes, but at scale, a 3-minute interval can create a perpetual CPU spike as the controller re-diffs all applications. Increasing to 5 minutes smooths the load at the cost of slower detection of drift caused by out-of-band changes.

### 3.2 Repository Server Scaling

The repository server is stateless and horizontally scalable. It clones Git repositories to local disk, renders manifests (Kustomize build, Helm template, Jsonnet eval), and returns the result to the application controller. Because it is stateless, scaling is simply a matter of increasing replicas:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: argocd-repo-server
  namespace: argocd
spec:
  replicas: 6
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-repo-server
  template:
    metadata:
      labels:
        app.kubernetes.io/name: argocd-repo-server
    spec:
      serviceAccountName: argocd-repo-server
      containers:
        - name: argocd-repo-server
          image: quay.io/argoproj/argocd:v2.11.0
          command:
            - argocd-repo-server
          args:
            - --repo-cache-expiration=24h
            - --parallelismlimit=8
            - --loglevel=info
            - --logformat=json
            - --redis
            argocd-redis-ha-announce-0.argocd-redis-ha.argocd:6379
            - --redis
            argocd-redis-ha-announce-1.argocd-redis-ha.argocd:6379
            - --redis
            argocd-redis-ha-announce-2.argocd-redis-ha.argocd:6379
          ports:
            - containerPort: 8081
              name: grpc
            - containerPort: 8082
              name: metrics
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8082
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8082
            initialDelaySeconds: 30
            periodSeconds: 30
          resources:
            requests:
              cpu: 1000m
              memory: 1Gi
            limits:
              cpu: 2000m
              memory: 2Gi
          volumeMounts:
            - name: repos
              mountPath: /tmp/argocd-local
            - name: gpg-keys
              mountPath: /app/config/gpg/keys
            - name: tls-certs
              mountPath: /app/config/tls
      volumes:
        - name: repos
          emptyDir:
            medium: Memory
            sizeLimit: 1Gi
        - name: gpg-keys
          configMap:
            name: argocd-gpg-keys-cm
        - name: tls-certs
          configMap:
            name: argocd-tls-certs-cm
```

The `--parallelismlimit=8` flag caps the number of concurrent manifest generation operations per repo server pod. This is critical because Kustomize and Helm rendering is CPU-intensive, and without a limit, a burst of sync requests can exhaust CPU and cause the pod to become unresponsive. The `--repo-cache-expiration=24h` flag controls how long rendered manifests are cached in Redis, reducing redundant Git clones and manifest rendering for applications that have not changed.

The `emptyDir` with `medium: Memory` mounts the repo working directory as a tmpfs, which is significantly faster than disk for the small, short-lived files that the repo server creates during cloning and rendering. The `sizeLimit: 1Gi` prevents a runaway clone from consuming all node memory. This is safe because the repo server cleans up its working directory after each operation, and Git repos for Kubernetes manifests are typically small.

The repo server uses a Kubernetes Service with client-side load balancing: the application controller connects to the Service, and kube-proxy distributes connections across the available pods. There is no affinity, so consecutive requests from the same controller may hit different repo server pods, which is fine because the Redis cache provides the shared state that makes the repo servers interchangeable.

### 3.3 Redis HA and Cache Integrity

Redis is ArgoCD's shared cache and is a critical-path dependency. If Redis is unavailable, the application controller falls back to fetching rendered manifests directly from the repo server on every reconciliation, which dramatically increases repo server load and sync latency. For production, Redis must run in HA mode with sentinel-managed failover.

The Redis HA setup uses a StatefulSet with three Redis pods and three Sentinel pods (which can be sidecars or separate pods depending on the chart). The following Service definitions expose the Redis instances with stable network identities:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-redis-ha-config
  namespace: argocd
data:
  redis.conf: |
    bind 0.0.0.0
    port 6379
    maxmemory 2147483648
    maxmemory-policy allkeys-lru
    timeout 300
    tcp-keepalive 60
    appendonly yes
    appendfsync everysec
    save 900 1
    save 300 10
    save 60 10000
    replica-serve-stale-data yes
    replica-read-only yes
    repl-diskless-sync yes
    repl-diskless-sync-delay 5
    repl-ping-replica-period 10
    repl-timeout 60
    repl-backlog-size 1mb
    repl-backlog-ttl 3600
    client-output-buffer-limit replica 256mb 64mb 60
    client-output-buffer-limit pubsub 32mb 8mb 60
    hz 10
    aof-rewrite-incremental-fsync yes
    rdb-save-incremental-fsync yes
    lazyfree-lazy-eviction yes
    lazyfree-lazy-expire yes
    lazyfree-lazy-server-del yes
    io-threads 2
    io-threads-do-reads yes
  sentinel.conf: |
    bind 0.0.0.0
    port 26379
    sentinel monitor mymaster argocd-redis-ha-announce-0.argocd-redis-ha.argocd 6379 2
    sentinel down-after-milliseconds mymaster 5000
    sentinel failover-timeout mymaster 30000
    sentinel parallel-syncs mymaster 1
    sentinel deny-scripts-reconfig yes
    sentinel announce-hostnames yes
```

The `maxmemory 2147483648` setting (2GB) combined with `maxmemory-policy allkeys-lru` means Redis will evict the least-recently-used keys when it reaches 2GB of memory. This is preferable to allowing Redis to run out of memory and return errors, because cache misses (which result in a fallback to the repo server) are recoverable while cache errors can cause sync failures. The `appendonly yes` with `appendfsync everysec` provides durability with a worst-case 1-second data loss window, which is acceptable because Redis is a cache, not a source of truth.

The eviction policy has an important operational consequence: when keys are evicted, the controller must re-fetch from the repo server, which increases load. If eviction is frequent, it indicates that either the Redis memory limit is too low or the cache expiration is too aggressive. Monitoring the `evicted_keys` metric in Redis is essential for detecting this condition before it causes performance degradation.

### 3.4 Failure Modes and Mitigations

The most common production failure mode is repo server timeout under concurrent sync load. When multiple Applications sync simultaneously (for example, after a commit to a shared base manifest that many Applications reference), the repo server's CPU is saturated by concurrent Kustomize and Helm rendering. The application controller waits for responses with the timeout specified by `--repo-server-timeout-seconds`, and when the timeout fires, the sync fails. The failure is visible in the Application status as a sync error with the message "context deadline exceeded."

The mitigation is multi-layered. First, scale repo server replicas to handle the burst. Second, increase `--repo-server-timeout-seconds` on the controller to give the repo server more time under load. Third, enable `--redis-compress` on the controller to reduce the size of cached manifests, which reduces Redis memory pressure and cache eviction frequency. Fourth, use the sync retry policy (shown in the ApplicationSet template above) with exponential backoff so that transient timeouts are retried rather than surfacing as failures.

The second common failure mode is the self-heal loop. This occurs when a resource is continuously modified by an in-cluster controller (for example, the Horizontal Pod Autoscaler modifying `spec.replicas`, or the kube-controller-manager annotating Service accounts with token rotation timestamps). ArgoCD detects the modification as drift, reverts it, and the in-cluster controller modifies it again. The result is a rapid oscillation between `Synced` and `OutOfSync` states, with sync operations firing continuously.

The mitigation is the `ignoreDifferences` configuration, which tells the diff engine to ignore specific fields. The `argocd-cm` ConfigMap entries shown earlier handle the most common cases (Deployment replicas, StatefulSet replicas, managed fields). For application-specific mutations, you can add `ignoreDifferences` directly to the Application spec:

```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
        - /metadata/annotations/deployment.kubernetes.io~1revision
        - /metadata/annotations/kubectl.kubernetes.io~1last-applied-configuration
    - group: ""
      kind: ServiceAccount
      jsonPointers:
        - /metadata/annotations
    - group: ""
      kind: Service
      jsonPointers:
        - /spec/clusterIP
        - /spec/clusterIPs
        - /metadata/annotations
    - group: networking.k8s.io
      kind: Ingress
      jsonPointers:
        - /status
        - /metadata/annotations/nginx.ingress.kubernetes.io~1rewrite-target
```

The third failure mode is cluster connectivity loss. When a target cluster's API server becomes unreachable, the controller's informers stop receiving events. The controller retries connection establishment with an exponential backoff. Applications targeting the unreachable cluster show as `Unknown` health status and `OutOfSync` sync status (because the controller cannot determine the live state). When connectivity is restored, the controller's informers re-establish, the cache is rebuilt, and reconciliation resumes.

The critical operational concern during a connectivity loss is that auto-sync is still enabled. If the controller had a cached state that showed the Application as `Synced` before the connectivity loss, it will not attempt to re-sync until it detects a change (either a Git revision change or a live state change from the now-stale informers). When connectivity is restored, the informers rebuild and the first reconciliation may detect drift, triggering a sync. This is usually the desired behavior, but it means that a connectivity loss followed by restoration can trigger a burst of sync operations. The `--kubectl-parallelism-limit` flag on the controller is the primary defense against this burst overwhelming the target cluster's API server.

The fourth failure mode is Git repository unavailability. The repo server clones repositories on first access and maintains a local copy, but it periodically fetches to detect new revisions. If the Git server is unreachable, the repo server cannot detect new commits, and syncs triggered by new commits will fail. However, existing Applications continue to be reconciled against the last-known revision because the repo server's local copy is still available. This means that a Git outage does not affect the reconciliation of existing state; it only prevents the deployment of new state.

### 3.5 Observability and Diagnostics

The application controller exposes Prometheus metrics on port 8082. The key metrics for capacity planning and alerting are:

| Metric | Type | Description |
|--------|------|-------------|
| `argocd_app_info` | Gauge | Per-application info with labels for sync status, health status, project. Use this to count apps by status. |
| `argocd_app_sync_total` | Counter | Total sync operations, labeled by phase (Succeeded, Failed, Error). Rate this for sync failure alerting. |
| `argocd_app_health_status` | Gauge | Health status (1 for Healthy, 0 otherwise), labeled by app. |
| `argocd_app_k8s_request_total` | Counter | Kubernetes API requests by status code. Rate 4xx/5xx responses for API server issues. |
| `argocd_kubectl_exec_total` | Counter | Kubectl operations executed during syncs. |
| `argocd_cluster_info` | Gauge | Per-cluster info with labels for server and name. |
| `argocd_repo_request_total` | Counter | Repository server requests by operation. |
| `argocd_redis_request_total` | Counter | Redis requests by operation and status. |

The following Prometheus rules provide the essential production alerts:

```yaml
groups:
  - name: argocd
    rules:
      - alert: ArgoCDSyncFailures
        expr: |
          increase(argocd_app_sync_total{phase=~"Error|Failed"}[15m]) > 3
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "ArgoCD sync failures for {{ $labels.application }}"
          description: "Application {{ $labels.application }} has had {{ $value }} sync failures in the last 15 minutes"
      - alert: ArgoCDAppDegraded
        expr: |
          argocd_app_health_status{health_status="Degraded"} == 1
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Application {{ $labels.application }} is degraded"
          description: "Application {{ $labels.application }} has been degraded for 10 minutes"
      - alert: ArgoCDRepoServerUnavailable
        expr: |
          up{job="argocd-repo-server"} == 0
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "ArgoCD repo server is unavailable"
          description: "Repo server {{ $labels.instance }} has been down for 2 minutes"
      - alert: ArgoCDRedisEvictions
        expr: |
          increase(redis_evicted_keys_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Redis is evicting keys"
          description: "Redis instance {{ $labels.instance }} has evicted {{ $value }} keys in 5 minutes, cache may be undersized"
      - alert: ArgoCDControllerReconcileStuck
        expr: |
          time() - argocd_app_info{} * 0 + histogram_quantile(0.95, rate(argocd_app_reconcile_duration_seconds_bucket[5m])) > 30
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "ArgoCD reconciliation is slow"
          description: "95th percentile reconcile time is {{ $value }}s, controller may be overloaded"
```

For day-to-day diagnostics, the `argocd` CLI provides several commands for inspecting the state of the system:

```bash
# List all clusters and their connection status
argocd cluster list

# Get detailed information about a specific cluster including its resources
argocd cluster get prod-us-east-1 --output yaml

# Check the sync status and diff of a specific application
argocd app get payments-prod-us-east-1
argocd app diff payments-prod-us-east-1 --revision HEAD

# View recent sync operations and their logs
argocd app history payments-prod-us-east-1
argocd app logs payments-prod-us-east-1 --sync-operation-id <operation-id>

# Force a refresh of the application state (bypassing the cache)
argocd app get payments-prod-us-east-1 --refresh

# Trigger a manual sync with options
argocd app sync payments-prod-us-east-1 \
  --dry-run \
  --prune \
  --apply-out-of-sync-only \
  --server-side \
  --timeout 300

# Validate RBAC policy changes before applying
argocd admin settings rbac validate argocd-rbac-cm

# Check project sync windows
argocd proj sync-windows list payments-platform

# Manage project roles
argocd proj role list payments-platform
argocd proj role add-policy payments-platform --role deployer \
  --action sync --permission allow --application "*"
```

The `--refresh` flag on `argocd app get` forces the controller to bypass the Redis cache and fetch fresh manifests from the repo server and fresh resource state from the target cluster. This is the first diagnostic step when an application's status appears stale or incorrect, because it eliminates cache corruption as a cause.

The `--dry-run` flag on `argocd app sync` performs the sync planning phase (rendering manifests, computing the diff, determining the operation plan) without applying any changes. This is invaluable for verifying that a sync will do what you expect before committing to it, especially for prune operations that would delete resources.

### 3.6 Disaster Recovery

The disaster recovery posture for ArgoCD depends on understanding what is authoritative and what is derived. Git repositories are the source of truth for application manifests. The ArgoCD configuration itself (AppProjects, RBAC, notification config, cluster secrets) is stored in Kubernetes resources in the ArgoCD namespace. Redis is a cache and can be rebuilt. The repo server's local clones are ephemeral and can be re-fetched.

The recovery-critical resources are the ArgoCD namespace Secrets (cluster credentials, repo credentials, notification credentials) and ConfigMaps (argocd-cm, argocd-rbac-cm, argocd-notifications-cm, argocd-ssh-known-hosts-cm, argocd-tls-certs-cm). These should be backed up using a tool like Velero or a scheduled `kubectl` export:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backups/argocd/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

NAMESPACE="argocd"

# Export all ConfigMaps
kubectl get configmap -n "$NAMESPACE" -o json | jq -c '.items[]' > "$BACKUP_DIR/configmaps.json"

# Export all Secrets (excluding service account tokens which are auto-generated)
kubectl get secret -n "$NAMESPACE" \
  -l 'app.kubernetes.io/part-of=argocd' \
  -o json | jq -c '.items[]' > "$BACKUP_DIR/secrets.json"

# Export AppProjects
kubectl get appproject -n "$NAMESPACE" -o json | jq -c '.items[]' > "$BACKUP_DIR/appprojects.json"

# Export ApplicationSets
kubectl get applicationset -n "$NAMESPACE" -o json | jq -c '.items[]' > "$BACKUP_DIR/applicationsets.json"

# Export Applications across all allowed namespaces
ALLOWED_NAMESPACES="argocd payments-team platform-team security-team"
for ns in $ALLOWED_NAMESPACES; do
  kubectl get application -n "$ns" -o json 2>/dev/null | jq -c '.items[]' >> "$BACKUP_DIR/applications.json" || true
done

# Create a checksum for verification
sha256sum "$BACKUP_DIR"/*.json > "$BACKUP_DIR/checksums.sha256"

echo "Backup complete: $BACKUP_DIR"
```

For cluster secrets specifically, the credentials stored in them are the most sensitive data in the ArgoCD installation. These should be encrypted at rest using a tool like Sealed Secrets or SOPS, and the decryption keys should be stored in a vault separate from the Kubernetes cluster. A backup of the cluster Secret without the corresponding decryption key is useless during recovery.

The recovery procedure itself is straightforward because ArgoCD is designed to be stateless with respect to the applications it manages: the Application resources and their status are derived from Git and cluster state. To recover ArgoCD into a new cluster, you deploy the ArgoCD control plane (from Helm or manifests), restore the ConfigMaps and Secrets from backup, re-register the target clusters (or restore the cluster Secrets if the target clusters' ServiceAccounts are still valid), and the controller will begin reconciling. Applications will appear as `OutOfSync` initially because the controller has no cached state, and the first reconciliation pass will sync them.

The key insight for disaster recovery is that ArgoCD's design eliminates the need for a complex backup-and-restore procedure for application state. The application state is fully reconstructable from Git and the live cluster state. Only the control plane configuration (which is a bounded, well-defined set of Secrets and ConfigMaps) requires explicit backup. This is a direct consequence of the GitOps invariant: Git is the source of truth, and everything else is derived.
