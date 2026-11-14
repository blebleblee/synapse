# Lesson 1: RBAC Fundamentals: Principals, Roles, Permissions

## 1. First-Principles Intuition & Invariants

Every production system eventually confronts a deceptively simple question: who is allowed to do what, and to which resource? The answer to that question determines whether a compromised service account can drain your production database, whether a junior engineer can accidentally delete a Kubernetes namespace, and whether a regulatory audit finds your access controls coherent and auditable. Access control is not a feature you bolt on after the architecture is stable. It is the architecture's immune system, and understanding it at the level of its formal model is what separates infrastructure engineers who configure RBAC from those who reason about it under pressure.

The oldest and most intuitive access control model is Discretionary Access Control, or DAC. In DAC, the owner of a resource decides who may access it. Linux file permissions are the canonical example: when you create a file, you own it, and you may `chmod` it however you like, granting read or write to your group or to the world. The owner holds discretion, hence the name. DAC is flexible and maps naturally to individual ownership, but it scales poorly. In a system with thousands of files and hundreds of users, the access control matrix—the theoretical construct listing every subject, every object, and every permitted operation between them—becomes unmanageable. Worse, DAC is vulnerable to the confused deputy problem and to privilege leakage through copied permissions.

Mandatory Access Control, or MAC, emerged from the United States military's work on multilevel security in the 1970s and was formalized in the Bell-LaPadula model. Under MAC, a central authority assigns security labels to both subjects and objects, and the system enforces rules that no individual user can override. A process running at SECRET clearance cannot write to an UNCLASSIFIED file (the *-property, preventing downward writes), and an UNCLASSIFIED process cannot read a SECRET file (the simple security property, preventing upward reads). SELinux and AppArmor are the practical Linux implementations of MAC thinking. The strength of MAC is precisely its rigidity: no user can inadvertently or maliciously relax a constraint. Its weakness is administrative overhead and brittleness, since every new resource and process requires explicit labeling from a central policy authority.

Role-Based Access Control, introduced formally by Ferraiolo and Kuhn at NIST in 1992 and later standardized as NIST RBAC in 2004, threads the needle between DAC's flexibility and MAC's rigor. The core insight is that permissions should not attach to individual users but to *roles*, which represent job functions or operational responsibilities within an organization. Users are then assigned to roles, and roles carry permissions. This indirection through the role layer is not merely organizational tidiness; it has profound engineering consequences for how systems scale, how audits work, and how access changes propagate when someone joins, moves between teams, or leaves an organization.

The formal RBAC model defines three primary entity types. Subjects are the principals—the active entities that initiate operations. In Kubernetes, subjects include human users authenticated through an identity provider, service accounts running inside pods, and groups that aggregate multiple users. Roles are named containers of permissions with no identity of their own; they exist purely as a mapping from a name to a set of allowed operations. Permissions are the atomic authorizations: the right to perform a specific verb on a specific resource type within a specific scope. The relationship between these entities is governed by two assignment relations: user-role assignment (UA), which maps subjects to roles, and permission-role assignment (PA), which maps permissions to roles. Access is granted when the transitive composition of UA and PA confirms that a subject's assigned roles carry the requested permission.

The access control matrix is the theoretical substrate beneath all of these models. Imagine a two-dimensional matrix where rows are subjects and columns are objects. Each cell contains the set of rights that the subject holds over that object. In a system with one thousand users and ten thousand resources, this matrix has ten million cells, the vast majority of which are empty. DAC stores this matrix by rows, as access control lists attached to users, or by columns, as capability lists attached to objects. RBAC compresses it radically by factoring the matrix through roles: instead of representing every (subject, object) pair explicitly, you store which roles each subject holds and which permissions each role grants. The number of unique roles in a real organization is typically orders of magnitude smaller than the number of (subject, resource) pairs, so the compression ratio is enormous in practice.

Kubernetes RBAC is the dominant production implementation that infrastructure engineers work with daily, and its design maps precisely onto the NIST model. A `Role` or `ClusterRole` object is the PA relation made concrete: it lists API groups, resource types, and verbs. A `RoleBinding` or `ClusterRoleBinding` is the UA relation: it names subjects and binds them to a role. The scope distinction matters: a `Role` is namespace-scoped, meaning its permissions apply only within a single Kubernetes namespace, while a `ClusterRole` is cluster-scoped and can authorize access to cluster-level resources like `nodes`, `persistentvolumes`, and `namespaces` themselves.

Three invariants govern correct RBAC behavior and you should hold them as mental constraints whenever you design or audit a role system. The first is *least privilege*: every principal should hold only the permissions necessary to perform its stated function, nothing more. A pod that reads ConfigMaps for its own namespace should not hold `get` on `secrets` or `list` on `nodes`. The second is *role minimality*: roles should be defined around job functions, not around individuals, and the number of roles should be the minimum needed to cover the operational space without creating roles that differ only in a single permission. Role explosion—hundreds of nearly identical roles—is a failure mode that defeats the compression benefit of RBAC and renders audit impossible. The third invariant is *separation of duties*: no single principal should hold roles that together grant the ability to both perform an action and authorize that same action. In practice, this means the service account that deploys workloads should not also hold the ability to modify the RBAC policies that govern its own permissions.

---

## 2. Core Architecture & Mechanics

Understanding Kubernetes RBAC mechanically requires tracing the request path from a client's TLS connection through the API server's authorization chain down to the etcd storage layer. When `kubectl` or an in-cluster client sends an API request, it carries an authentication credential—a client certificate, a bearer token, or a projected service account token signed by the cluster's OIDC-compatible token issuer. Authentication happens first and resolves the credential to a username, a UID, and a set of groups. These attributes together form the authenticated subject. Authorization then consults the RBAC authorizer to decide whether that subject may perform the requested verb on the requested resource in the requested namespace.

The RBAC authorizer performs a pure, stateless lookup. It retrieves all `RoleBindings` and `ClusterRoleBindings` that reference the subject (by username or any of the subject's groups), collects the referenced `Roles` and `ClusterRoles`, and checks whether any permission rule in those roles matches the incoming request tuple of `(apiGroup, resource, verb, namespace)`. The first matching allow wins; there is no explicit deny mechanism in Kubernetes RBAC. If no rule matches, the request is denied by default. This allow-only model means that permissions are additive: a subject's effective permissions are the union of all permissions carried by all of its bound roles.

The data structures backing this are straightforward. A `ClusterRole` is an etcd document whose core payload is a list of `PolicyRule` objects. Each `PolicyRule` names one or more API groups, one or more resource types (optionally scoped to specific resource names), and one or more verbs. The verbs are drawn from the standard set: `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`, `deletecollection`, and the special `*` wildcard.

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
```

This role is narrow by design. It grants read-only access to pod objects and their logs across any namespace where it is bound, but it grants nothing over secrets, configmaps, deployments, or any other resource type. The empty string in `apiGroups` refers to the core API group, which is where pods, services, configmaps, secrets, and persistentvolumes live. Custom resources and extension APIs live in named groups like `apps`, `batch`, or `networking.k8s.io`.

A `ClusterRoleBinding` establishes the UA relation:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: pod-reader-global
subjects:
- kind: ServiceAccount
  name: log-collector
  namespace: monitoring
- kind: Group
  name: sre-team
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

Two aspects of this binding are worth examining carefully. First, the `roleRef` is immutable after creation. If you need to point a binding at a different role, you must delete and recreate the binding; the API server rejects in-place `roleRef` mutations. This immutability is a deliberate safety constraint that prevents silent privilege escalation through binding modification. Second, binding a `ClusterRole` with a `RoleBinding` (not a `ClusterRoleBinding`) scopes the granted permissions to the namespace of the `RoleBinding`, even though the role itself is cluster-scoped. This pattern—defining reusable `ClusterRoles` and instantiating them into specific namespaces via `RoleBindings`—is the idiomatic way to share role definitions across namespaces without granting cluster-wide access.

The request authorization flow is best understood as a decision pipeline:

```
Client Request
     │
     ▼
┌──────────────────────────────────┐
│   Authentication Middleware      │
│   (resolve credential → subject) │
└────────────────┬─────────────────┘
                 │  username, groups, uid
                 ▼
┌──────────────────────────────────┐
│   Authorization Chain            │
│                                  │
│   ┌──────────────────────────┐   │
│   │  Node Authorizer         │   │
│   │  (kubelet credentials)   │   │
│   └────────────┬─────────────┘   │
│                │ deny → next     │
│   ┌────────────▼─────────────┐   │
│   │  RBAC Authorizer         │   │
│   │                          │   │
│   │  For each RoleBinding /  │   │
│   │  ClusterRoleBinding that │   │
│   │  references the subject: │   │
│   │    resolve Role →        │   │
│   │    match PolicyRule →    │   │
│   │    allow if match found  │   │
│   └────────────┬─────────────┘   │
│                │ deny → next     │
│   ┌────────────▼─────────────┐   │
│   │  Webhook Authorizer      │   │
│   │  (optional OPA/Kyverno)  │   │
│   └──────────────────────────┘   │
└──────────────────────────────────┘
                 │
                 ▼
           Allow / Deny
```

The RBAC authorizer's internal resolution follows a specific lookup pattern. When a request arrives for subject `system:serviceaccount:monitoring:log-collector`, the authorizer queries the in-memory cache (backed by informers watching etcd) for all bindings whose subject list contains either that exact service account or any group the service account belongs to, including the synthetic `system:serviceaccounts` group and `system:serviceaccounts:monitoring`. It collects the referenced roles, iterates over their rules, and performs a match against the request's (apiGroup, resource, resourceName, verb, namespace) tuple. The evaluation short-circuits on first match, and the RBAC authorizer's decision feeds into the broader chain of authorizers configured via `--authorization-modes` on the API server.

Service account tokens in modern Kubernetes (1.21+) are issued as projected volumes with bounded lifetimes, audience constraints, and namespace binding. The token's claims include `sub` in the form `system:serviceaccount:<namespace>:<name>`, which is what the RBAC lookup resolves against. Understanding this token format is critical when debugging authorization failures: a pod using an
