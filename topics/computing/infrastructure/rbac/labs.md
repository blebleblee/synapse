# Operational Verification Labs: Rbac

## Objective & Environment Setup

Role-Based Access Control (RBAC) in Kubernetes represents a critical security boundary enforced through a declarative authorization model that gates every API request before the kube-apiserver processes it. Unlike traditional Unix permission systems that operate on filesystem inodes, Kubernetes RBAC evaluates request tuples consisting of a subject (user, group, or ServiceAccount), a verb (get, list, create, delete, patch, update, watch), and a resource (pods, services, configmaps, secrets, or custom resources). The authorization decision occurs after authentication resolves the caller's identity but before admission controllers and validation logic execute. This makes RBAC verification essential for both security posture assessment and operational troubleshooting, since misconfigured roles often manifest as cryptic 403 Forbidden errors that block legitimate workloads from functioning.

The exercises in this lab guide will teach you to inspect live RBAC policy state, trace authorization decisions through audit logs, profile the performance characteristics of the authorizer subsystem, and inject realistic misconfigurations to validate detection and recovery workflows. You will work exclusively with production-grade tooling: kubectl for declarative resource inspection and imperative probing, jq for JSON manipulation of API server audit events, perf for CPU profiling of the authorization code paths within the apiserver binary, and strace for tracing syscalls during authentication token validation and certificate parsing. This operational focus ensures that you develop the muscle memory required to diagnose RBAC issues in live clusters under time pressure, rather than relying on theoretical policy documents or static configuration reviews.

Your verification environment assumes a functional Kubernetes cluster running version 1.28 or newer, with audit logging enabled on the kube-apiserver. The audit policy must capture RequestResponse level detail for authorization events, which requires passing `--audit-log-path=/var/log/kubernetes/audit.log` and `--audit-policy-file=/etc/kubernetes/audit-policy.yaml` to the apiserver. The audit policy should include a rule that logs all requests at the Metadata level as a baseline, with RequestResponse logging for create, update, patch, and delete verbs. Install kubectl version-matched to your cluster, jq for JSON processing, and Linux perf tools from your distribution's kernel-tools or linux-tools package. If you are running a managed Kubernetes service like GKE, EKS, or AKS, audit logs will be exported to the cloud provider's logging service (Cloud Logging, CloudWatch Logs, or Azure Monitor), and you will retrieve them via provider-specific CLI tools rather than direct filesystem access.

To establish a reproducible baseline, create a dedicated namespace called `rbac-lab` and deploy a minimal workload consisting of a Deployment running nginx and a ServiceAccount with no explicit RoleBindings. This configuration allows you to inject controlled RBAC constraints and observe the resulting authorization failures. Use `kubectl create namespace rbac-lab` followed by `kubectl create serviceaccount test-sa -n rbac-lab` to initialize the test environment. Deploy the workload with a minimal Pod spec that references the ServiceAccount and attempts to list Pods within its own namespace during initialization. This synthetic read operation will fail unless you explicitly grant the necessary permissions, providing a clear signal for verification workflows.

The diagnostic cheat sheet at the end of this document consolidates all verification commands into a quick-reference format optimized for incident response scenarios. When troubleshooting production RBAC issues, start with the live state inspection commands in Exercise 1 to identify the gap between expected and actual permissions, then move to the audit log analysis techniques in Exercise 2 to trace the specific API requests that triggered authorization denials. Reserve fault injection exercises for pre-production staging environments or controlled maintenance windows, as deliberate RBAC misconfigurations can render cluster management interfaces inaccessible if applied carelessly.

## Exercise 1: Live State & Internal Subsystem Inspection

The first operational skill required for RBAC verification is the ability to enumerate and inspect the four core resource types that define the authorization policy graph: Roles, ClusterRoles, RoleBindings, and ClusterBindings. Kubernetes treats these as standard API resources, meaning you can retrieve them with kubectl and manipulate them as YAML or JSON documents. However, the relational structure connecting subjects to permissions across namespaces and cluster-wide scopes creates subtle dependencies that are not immediately visible in raw resource listings. A production cluster typically contains hundreds of RoleBindings and dozens of ClusterRoleBindings, many of which are created automatically by controllers and operators. Learning to filter this noise and trace the effective permissions granted to a specific ServiceAccount or user requires mastering kubectl's field selectors, JSON path queries, and the `auth can-i` subcommand that simulates authorization checks without executing actual API operations.

Begin by listing all ClusterRoles in the cluster with `kubectl get clusterroles`. The output will include system-managed roles like `cluster-admin`, `edit`, `view`, and `system:*` roles used by control plane components. These built-in roles follow a naming convention where `system:` prefixed roles are reserved for internal components, while user-facing roles like `admin`, `edit`, and `view` provide standard permission templates for common access patterns. Inspect the `view` ClusterRole with `kubectl get clusterrole view -o yaml` to observe its rule structure. Each rule consists of an `apiGroups` list, a `resources` list, and a `verbs` list. For example, the view role grants `get`, `list`, and `watch` verbs on `pods`, `services`, and `configmaps` within the core API group (represented as an empty string in the apiGroups field), while explicitly excluding write verbs like `create`, `update`, `patch`, and `delete`. This read-only policy ensures that users with view permissions can observe cluster state but cannot modify it, which is the correct default for monitoring and observability tooling.

To understand how subjects receive permissions, examine RoleBindings and ClusterRoleBindings. Run `kubectl get rolebindings -A` to list all namespace-scoped RoleBindings across the cluster. The output displays the RoleBinding name, the Role or ClusterRole it references, and the namespace where it applies. Note that RoleBindings can reference either a Role in the same namespace or a ClusterRole, with the binding's namespace constraining the scope of the ClusterRole's permissions to that namespace only. This design pattern allows cluster administrators to define reusable permission templates as ClusterRoles and then selectively grant them in specific namespaces through RoleBindings. To see this in action, create a RoleBinding that grants the `view` ClusterRole to the `test-sa` ServiceAccount in the `rbac-lab` namespace:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: test-sa-view
  namespace: rbac-lab
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
subjects:
- kind: ServiceAccount
  name: test-sa
  namespace: rbac-lab
```

Apply this manifest with `kubectl apply -f rolebinding-view.yaml` and then verify the binding with `kubectl get rolebinding test-sa-view -n rbac-lab -o yaml`. The `subjects` field contains an array of identity references, each specifying a `kind` (User, Group, or ServiceAccount), a `name`, and optionally a `namespace` for ServiceAccounts. The `roleRef` field is immutable after creation, meaning you cannot change which Role or ClusterRole a binding references without deleting and recreating the binding. This immutability constraint exists because Kubernetes treats roleRef changes as semantically equivalent to deleting the old binding and creating a new one, which could introduce transient authorization failures during the transition.

To verify the effective permissions granted to the ServiceAccount, use `kubectl auth can-i` with the `--as` flag to impersonate the ServiceAccount. The can-i subcommand queries the authorization subsystem without performing the actual operation, making it safe to test hypothetical permissions without side effects. Run `kubectl auth can-i list pods --as=system:serviceaccount:rbac-lab:test-sa -n rbac-lab` to check whether the ServiceAccount can list Pods in its own namespace. The command should return `yes` because the view ClusterRole grants the `list` verb on pods. Now test a write operation with `kubectl auth can-i create pods --as=system:serviceaccount:rbac-lab:test-sa -n rbac-lab`, which should return `no` because the view role excludes write verbs. This impersonation technique allows you to validate RBAC policy without deploying test workloads or generating audit log noise.

For cluster-scoped permissions, examine ClusterRoleBindings with `kubectl get clusterrolebindings`. Unlike RoleBindings, ClusterRoleBindings grant permissions across all namespaces and on cluster-scoped resources like Nodes, PersistentVolumes, and CustomResourceDefinitions. The `cluster-admin` ClusterRoleBinding typically grants full administrative access to the `system:masters` group, which is mapped to client certificates with the Organization field set to `system:masters`. This design allows bootstrap administrators to retain cluster-admin privileges through certificate-based authentication, even if all other authentication mechanisms fail. Inspect the cluster-admin binding with `kubectl get clusterrolebinding cluster-admin -o yaml` to see this configuration.

To trace the permissions granted to a specific user or ServiceAccount across multiple bindings, you must aggregate the rules from all applicable RoleBindings and ClusterRoleBindings. Kubernetes does not provide a built-in command for this aggregation, so you must extract and merge the data manually. Start by listing all RoleBindings that reference the target subject with a field selector. For ServiceAccounts, this requires filtering by the subject name and namespace. Use `kubectl get rolebindings -A -o json | jq -r '.items[] | select(.subjects[]? | select(.kind=="ServiceAccount" and .name=="test-sa" and .namespace=="rbac-lab")) | .metadata.namespace + "/" + .metadata.name'` to find all RoleBindings that grant permissions to the test-sa ServiceAccount. This jq query iterates over all RoleBindings, filters for those with a subject matching the ServiceAccount, and outputs the namespace and name of each binding. Repeat the process for ClusterRoleBindings with `kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.subjects[]? | select(.kind=="ServiceAccount" and .name=="test-sa" and .namespace=="rbac-lab")) | .metadata.name'`.

Once you have identified the relevant bindings, retrieve the referenced Roles and ClusterRoles to extract the actual permission rules. For each RoleBinding, fetch the Role or ClusterRole with `kubectl get role <role-name> -n <namespace> -o yaml` or `kubectl get clusterrole <clusterrole-name> -o yaml`. Examine the `rules` array to identify the API groups, resources, and verbs granted. Pay attention to wildcard entries, where `*` in the apiGroups, resources, or verbs fields grants permissions to all values in that category. For example, a rule with `apiGroups: ["*"]`, `resources: ["*"]`, and `verbs: ["*"]` is equivalent to cluster-admin access and should trigger immediate security review.

To inspect the internal authorization decision process, enable verbose logging on kubectl by adding the `-v=8` flag to any command. This verbosity level logs the full HTTP request and response, including the authorization headers and status codes. Run `kubectl get pods -n rbac-lab --as=system:serviceaccount:rbac-lab:test-sa -v=8` and examine the output. You will see the HTTP GET request to `/api/v1/namespaces/rbac-lab/pods` with an `Authorization: Bearer <token>` header, followed by the response status code. If the ServiceAccount lacks permissions, the response will be `403 Forbidden` with a JSON body containing an error message like `pods is forbidden: User "system:serviceaccount:rbac-lab:test-sa" cannot list resource "pods" in API group "" in the namespace "rbac-lab"`. This error message explicitly identifies the subject, verb, resource, and namespace involved in the authorization denial, providing all the information needed to diagnose the policy gap.

For deeper inspection of the apiserver's authorization subsystem, examine the apiserver process arguments to confirm which authorization modes are enabled. SSH to a control plane node (or use `kubectl describe pod kube-apiserver-<node> -n kube-system` in a kubeadm cluster) and locate the `--authorization-mode` flag in the apiserver command line. The default configuration for most clusters is `--authorization-mode=Node,RBAC`, which enables the Node authorizer (for kubelet-to-apiserver requests) and the RBAC authorizer (for all other requests). The order matters because authorization modes are evaluated sequentially, and the first mode that returns an explicit allow or deny decision terminates the evaluation chain. If you see additional modes like `Webhook` or `ABAC`, trace their configuration files to understand the full authorization policy stack.

To validate that RBAC is functioning correctly at the control plane level, inspect the apiserver metrics endpoint exposed on port 6443 at `/metrics`. Use `kubectl proxy` to establish a local forwarding connection, then query the metrics with `curl http://localhost:8001/metrics | grep apiserver_authorization`. The relevant metrics include `apiserver_authorization_duration_seconds`, which histograms the latency of authorization decisions, and `apiserver_authorization_attempts_total`, which counts the number of authorization checks by result (allowed or denied). High denial rates or elevated latency values indicate either RBAC misconfigurations causing excessive retries or authorization policy complexity degrading apiserver performance.

## Exercise 2: Benchmarking & Saturation Profiling

RBAC authorization decisions execute synchronously in the kube-apiserver request path, meaning every API call blocks until the authorizer subsystem evaluates the request against the policy graph. In clusters with thousands of Roles, RoleBindings, and ClusterRoleBindings, the authorization evaluation can become a bottleneck, particularly when subjects have many bindings or when policies include complex regular expression matchers in resource names. Understanding the performance characteristics of the RBAC authorizer requires profiling the apiserver under realistic load patterns, measuring the CPU cost of authorization checks, and identifying policy configurations that trigger worst-case evaluation paths.

Start by establishing a performance baseline for the RBAC authorizer using the `kubectl auth can-i` command in a tight loop. This synthetic benchmark isolates the authorization subsystem from other apiserver responsibilities like admission control, validation, and storage writes. Create a shell script that repeatedly queries the same permission check:

```bash
#!/bin/bash
for i in {1..1000}; do
  kubectl auth can-i list pods --as=system:serviceaccount:rbac-lab:test-sa -n rbac-lab > /dev/null
done
```

Run this script with `time bash benchmark-authz.sh` to measure the total execution time. On a healthy cluster with minimal policy complexity, 1000 authorization checks should complete in under 10 seconds, yielding an average latency of approximately 10 milliseconds per check. This baseline reflects the combined cost of TLS handshake overhead, authentication token parsing, RBAC policy evaluation, and HTTP response serialization. If the benchmark significantly exceeds this threshold, investigate whether the cluster has excessive RoleBindings, complex regex matchers, or high apiserver CPU contention from other request types.

To profile the CPU cost of the RBAC authorizer within the apiserver process, use Linux perf to capture stack traces during the authorization benchmark. SSH to the control plane node hosting the kube-apiserver and identify the apiserver process ID with `pidof kube-apiserver`. Start perf recording with `sudo perf record -g -p <apiserver-pid> -F 99 -- sleep 30`, which samples the process at 99 Hz for 30 seconds. While perf is recording, execute the authorization benchmark script from a remote host to generate load. After the recording completes, generate a flame graph with `sudo perf script | stackcollapse-perf.pl | flamegraph.pl > rbac-flamegraph.svg`. The flame graph visualizes the CPU time spent in each function, with wider bars representing more expensive code paths. Look for functions in the `k8s.io/apiserver/pkg/authorization/authorizer` package, particularly `Authorize` and the RBAC-specific evaluators like `VisitRulesFor`. If these functions dominate the flame graph, the RBAC policy is the bottleneck.

The RBAC authorizer evaluates permissions by iterating over all RoleBindings and ClusterRoleBindings that reference the request subject, then checking whether any of the bound Roles or ClusterRoles contain a rule matching the request verb and resource. This iteration has linear complexity with respect to the number of bindings per subject, making subjects with many bindings more expensive to authorize. To quantify this effect, create a test ServiceAccount with progressively more RoleBindings and measure the authorization latency. Start by creating 10 RoleBindings that grant the view ClusterRole in different namespaces:

```bash
for i in {1..10}; do
  kubectl create namespace rbac-lab-$i
  kubectl create rolebinding test-sa-view-$i \
    --clusterrole=view \
    --serviceaccount=rbac-lab:test-sa \
    -n rbac-lab-$i
done
```

Rerun the authorization benchmark and record the execution time. Repeat the process with 50, 100, and 500 RoleBindings, plotting the latency against the binding count. You should observe sublinear growth, as the RBAC authorizer implements caching and indexing optimizations that reduce the cost of repeated lookups. However, cache invalidation occurs whenever any RBAC resource changes, so frequent policy updates degrade performance by forcing cache rebuilds.

To stress-test the authorization subsystem under concurrent load, use a tool like `hey` or `ab` (ApacheBench) to generate parallel HTTP requests directly to the apiserver. Construct a curl command that performs an authorization check via the SubjectAccessReview API, which the apiserver uses internally to evaluate `kubectl auth can-i` queries:

```bash
curl -X POST https://<apiserver>:6443/apis/authorization.k8s.io/v1/subjectaccessreviews \
  --header "Authorization: Bearer <token>" \
  --header "Content-Type: application/json" \
  --cacert /etc/kubernetes/pki/ca.crt \
  --data '{
    "apiVersion": "authorization.k8s.io/v1",
    "kind": "SubjectAccessReview",
    "spec": {
      "user": "system:serviceaccount:rbac-lab:test-sa",
      "resourceAttributes": {
        "namespace": "rbac-lab",
        "verb": "list",
        "resource": "pods"
      }
    }
  }'
```

Replace `<apiserver>` with your cluster's API server address and `<token>` with a valid authentication token (extract one from `kubectl config view --raw`). Run this curl command through `hey` with 10 concurrent workers issuing 1000 total requests: `hey -n 1000 -c 10 -m POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d @sar.json https://<apiserver>:6443/apis/authorization.k8s.io/v1/subjectaccessreviews`. The `hey` output reports latency distribution (p50, p95, p99) and throughput (requests per second). Healthy clusters should sustain at least 200 requests per second with p99 latency under 50 milliseconds. Degraded performance indicates either CPU saturation on the apiserver or inefficient RBAC policy structures.

To identify specific policy configurations that degrade performance, profile the apiserver with `strace` to trace syscalls during authorization. The RBAC authorizer reads ClusterRoles and ClusterRoleBindings from etcd via the apiserver's internal storage interface, which translates to gRPC calls to etcd. Attach strace to the apiserver process with `sudo strace -f -p <apiserver-pid> -e trace=network,read,write -o apiserver-strace.log` and trigger an authorization benchmark. After capturing a representative trace, search the log for repeated `recvfrom` syscalls that indicate etcd queries. Excessive etcd round trips suggest that the apiserver's RBAC cache is thrashing, possibly due to rapid policy updates or insufficient cache size. Check the apiserver's `--authorization-mode` and `--authorization-webhook-cache-authorized-ttl` flags to confirm cache tuning parameters.

The apiserver exposes detailed authorization metrics at `/metrics` that allow continuous monitoring of RBAC performance. Query the `apiserver_authorization_duration_seconds` histogram with `curl -s http://localhost:8001/metrics | grep apiserver_authorization_duration_seconds` (assuming kubectl proxy is running). The histogram buckets show the distribution of authorization latencies, with buckets labeled by upper bounds (e.g., 0.001, 0.01, 0.1, 1.0 seconds). Calculate the p99 latency by finding the smallest bucket where the cumulative count exceeds 99% of the total sample count. If p99 latency exceeds 100 milliseconds, investigate RBAC policy complexity and consider simplifying role structures or reducing the number of bindings per subject.

Another critical metric is `apiserver_authorization_attempts_total`, a counter labeled by `result` (allowed or denied). High denial counts indicate either legitimate authorization failures (misconfigured workloads attempting unauthorized operations) or malicious probing attempts. To correlate denials with specific subjects, enable audit logging with RequestResponse level detail and aggregate the audit logs by subject. Use `jq` to extract authorization failures: `jq -r 'select(.verb=="list" and .responseStatus.code==403) | [.user.username, .objectRef.resource, .objectRef.namespace] | @tsv' /var/log/kubernetes/audit.log | sort | uniq -c | sort -rn`. This pipeline extracts the username, resource, and namespace from each 403 response, then counts occurrences to identify the most frequently denied subjects. High denial rates for legitimate ServiceAccounts indicate RBAC misconfigurations that require policy updates.

## Exercise 3: Fault Injection & Recovery Analysis

Understanding RBAC behavior under failure conditions requires deliberately introducing misconfigurations and observing their impact on cluster operations and workload availability. Production RBAC issues often manifest as cascading failures where a single incorrect RoleBinding blocks a controller or operator from reconciling resources, which then triggers dependent workloads to fail health checks and enter crash loops. Learning to diagnose and recover from these scenarios in a controlled environment builds the operational intuition needed to respond effectively during real incidents.

Begin by simulating a common misconfiguration: deleting the RoleBinding that grants a workload's ServiceAccount permission to read ConfigMaps. Deploy a sample application that reads its configuration from a ConfigMap during startup. Create the namespace, ServiceAccount, ConfigMap, and Deployment:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: rbac-fault-inject
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: config-reader-sa
  namespace: rbac-fault-inject
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: rbac-fault-inject
data:
  config.json: |
    {
      "feature_flags": {
        "enable_metrics": true
      }
    }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-reader
  namespace: rbac-fault-inject
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: config-reader-binding
  namespace: rbac-fault-inject
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: configmap-reader
subjects:
- kind: ServiceAccount
  name: config-reader-sa
  namespace: rbac-fault-inject
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: config-reader-app
  namespace: rbac-fault-inject
spec:
  replicas: 1
  selector:
    matchLabels:
      app: config-reader
  template:
    metadata:
      labels:
        app: config-reader
    spec:
      serviceAccountName: config-reader-sa
      containers:
      - name: app
        image: curlimages/curl:8.5.0
        command:
        - /bin/sh
        - -c
        - |
          set -e
          APISERVER=https://kubernetes.default.svc
          SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount
          TOKEN=$(cat ${SERVICEACCOUNT}/token)
          CACERT=${SERVICEACCOUNT}/ca.crt
          
          echo "Fetching ConfigMap..."
          curl --cacert ${CACERT} \
               --header "Authorization: Bearer ${TOKEN}" \
               -X GET ${APISERVER}/api/v1/namespaces/rbac-fault-inject/configmaps/app-config
          
          echo "ConfigMap fetch succeeded. Starting main loop..."
          while true; do sleep 3600; done
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "64Mi"
            cpu: "100m"
```

Apply this manifest with `kubectl apply -f config-reader-app.yaml` and verify that the Pod starts successfully with `kubectl get pods -n rbac-fault-inject`. Check the Pod logs with `kubectl logs -n rbac-fault-inject deployment/config-reader-app` to confirm that the ConfigMap fetch succeeded. The log output should include the full JSON response from the apiserver containing the ConfigMap data.

Now inject the fault by deleting the RoleBinding: `kubectl delete rolebinding config-reader-binding -n rbac-fault-inject`. The existing Pod continues running because it already fetched the ConfigMap during initialization, but if you delete the Pod to force a restart, the new Pod will fail to start. Delete the Pod with `kubectl delete pod -n rbac-fault-inject -l app=config-reader` and watch the replacement Pod with `kubectl get pods -n rbac-fault-inject -w`. The Pod will enter CrashLoopBackOff as the container repeatedly fails during initialization.

To diagnose the failure, retrieve the Pod logs with `kubectl logs -n rbac-fault-inject -l app=config-reader`. The curl command will fail with a 403 Forbidden response containing a JSON error body. The error message will state: `configmaps "app-config" is forbidden: User "system:serviceaccount:rbac-fault-inject:config-reader-sa" cannot get resource "configmaps" in API group "" in the namespace "rbac-fault-inject"`. This message provides the complete context needed to identify the authorization failure: the subject (the ServiceAccount), the verb (get), the resource (configmaps), and the namespace.

To confirm the diagnosis, use `kubectl auth can-i` to verify the missing permission: `kubectl auth can-i get configmaps --as=system:serviceaccount:rbac-fault-inject:config-reader-sa -n rbac-fault-inject`. The command returns `no`, confirming that the ServiceAccount lacks the required permission. Restore functionality by recreating the RoleBinding with `kubectl apply -f config-reader-app.yaml` (since the manifest includes the RoleBinding definition). The next Pod restart will succeed because the authorization check now passes.

To trace the authorization failure through the audit logs, query the apiserver audit log for 403 responses involving the ServiceAccount. If using filesystem-based audit logging, run `jq -r 'select(.user.username=="system:serviceaccount:rbac-fault-inject:config-reader-sa" and .responseStatus.code==403) | [.requestReceivedTimestamp, .verb, .objectRef.resource, .objectRef.name, .responseStatus.message] | @tsv' /var/log/kubernetes/audit.log | tail -20`. This query extracts the timestamp, verb, resource, resource name, and error message for all 403 responses from the ServiceAccount. The output will show the failed GET request for the configmaps/app-config resource, along with the exact timestamp when the failure occurred. This audit trail is critical for post-incident analysis, as it provides a complete record of authorization decisions that can be correlated with application-level errors and metrics.

To simulate a more subtle misconfiguration, modify the Role to grant the wrong verb. Edit the configmap-reader Role to replace `get` with `list`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-reader
  namespace: rbac-fault-inject
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["list"]
```

Apply the change with `kubectl apply -f role-wrong-verb.yaml` and delete the Pod to force a restart. The Pod will again fail during initialization, but the error message will be different: `configmaps "app-config" is forbidden: User "system:serviceaccount:rbac-fault-inject:config-reader-sa" cannot get resource "configmaps"`. Notice that the error message explicitly states the verb (`get`) that was denied, even though the Role grants `list`. This is because the application's curl command performs a GET request for a specific ConfigMap by name, which requires the `get` verb, while the `list` verb only allows fetching the entire collection of ConfigMaps without specifying a name.

To recover, update the Role to include both `get` and `list` verbs:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-reader
  namespace: rbac-fault-inject
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
```

Apply the corrected Role and verify that the Pod starts successfully. This exercise demonstrates the importance of understanding the semantic difference between Kubernetes API verbs. The `list` verb allows retrieving a collection of resources, while `get` allows retrieving a single resource by name. Many applications require both verbs, and granting only one will cause subtle failures that are easy to misdiagnose if you rely solely on trial-and-error rather than understanding the underlying RBAC semantics.

To inject a cluster-scoped fault, simulate the scenario where a controller loses permission to watch CustomResourceDefinitions (CRDs). Many operators rely on watching CRDs to detect when new custom resource types are installed, and losing this permission causes the operator to become stuck in a degraded state where it cannot reconcile new CRDs. Create a test operator that watches CRDs and logs their names:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: crd-watcher-sa
  namespace: rbac-fault-inject
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: crd-watcher
rules:
- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: crd-watcher-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: crd-watcher
subjects:
- kind: ServiceAccount
  name: crd-watcher-sa
  namespace: rbac-fault-inject
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crd-watcher
  namespace: rbac-fault-inject
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crd-watcher
  template:
    metadata:
      labels:
        app: crd-watcher
    spec:
      serviceAccountName: crd-watcher-sa
      containers:
      - name: watcher
        image: curlimages/curl:8.5.0
        command:
        - /bin/sh
        - -c
        - |
          set -e
          APISERVER=https://kubernetes.default.svc
          SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount
          TOKEN=$(cat ${SERVICEACCOUNT}/token)
          CACERT=${SERVICEACCOUNT}/ca.crt
          
          echo "Starting CRD watch..."
          curl --cacert ${CACERT} \
               --header "Authorization: Bearer ${TOKEN}" \
               -X GET "${APISERVER}/apis/apiextensions.k8s.io/v1/customresourcedefinitions?watch=true" \
          | while read -r line; do
              echo "CRD event: $line"
            done
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "64Mi"
            cpu: "100m"
```

Apply the manifest and verify that the watcher Pod starts successfully. Delete the ClusterRoleBinding with `kubectl delete clusterrolebinding crd-watcher-binding` and then delete the watcher Pod to force a restart. The new Pod will fail with a 403 Forbidden error when attempting to establish the watch stream. Retrieve the logs to see the error: `kubectl logs -n rbac-fault-inject -l app=crd-watcher`. The curl command will fail with a message stating that the ServiceAccount cannot watch CRDs.

Recovery requires recreating the ClusterRoleBinding, but this scenario illustrates a critical operational pattern: cluster-scoped permissions are granted through ClusterRoleBindings, and deleting a ClusterRoleBinding immediately revokes permissions for all subjects across all namespaces. This makes ClusterRoleBinding modifications high-risk operations that should be performed with caution in production environments. Always verify that you have alternative administrative access paths (such as a different ServiceAccount or user with cluster-admin permissions) before modifying ClusterRoleBindings that grant critical controller permissions.

To test recovery workflows, practice recreating the ClusterRoleBinding using only kubectl and the information available in the error message. The error message specifies the subject (ServiceAccount name and namespace) and the resource (customresourcedefinitions), which is sufficient to reconstruct the binding. Create the binding imperatively with `kubectl create clusterrolebinding crd-watcher-binding --clusterrole=crd-watcher --serviceaccount=rbac-fault-inject:crd-watcher-sa`. Verify that the watcher Pod restarts successfully after the binding is restored.

## Diagnostic Cheat Sheet & Verification Checklist

The following command sequences provide a rapid diagnostic workflow for troubleshooting RBAC issues in production environments. Execute these commands in order when responding to authorization failures reported by workloads or controllers.

**Identify the subject experiencing authorization failures:**

Extract the subject from error messages in Pod logs. Common patterns include `User "system:serviceaccount:<namespace>:<name>" cannot <verb> resource "<resource>"` or `Forbidden: User "<user>" cannot <verb> resource "<resource>"`. Note the subject type (User, Group, or ServiceAccount), the verb, the resource, and the namespace.

**Verify effective permissions using impersonation:**

```bash
kubectl auth can-i <verb> <resource> \
  --as=system:serviceaccount:<namespace>:<serviceaccount-name> \
  -n <target-namespace>
```

Replace `<verb>` with the failed operation (get, list, create, update, patch, delete, watch), `<resource>` with the API resource type (pods, configmaps, secrets, etc.), and `<target-namespace>` with the namespace where the operation was attempted. If the command returns `no`, the subject lacks the required permission.

**List all RoleBindings referencing the subject:**

```bash
kubectl get rolebindings -A -o json \
  | jq -r '.items[] | select(.subjects[]? | select(.kind=="ServiceAccount" and .name=="<sa-name>" and .namespace=="<sa-namespace>")) | "\(.metadata.namespace)/\(.metadata.name) -> \(.roleRef.kind)/\(.roleRef.name)"'
```

Replace `<sa-name>` and `<sa-namespace>` with the ServiceAccount name and namespace. This command outputs all RoleBindings that grant permissions to the ServiceAccount, along with the Role or ClusterRole they reference.

**List all ClusterRoleBindings referencing the subject:**

```bash
kubectl get clusterrolebindings -o json \
  | jq -r '.items[] | select(.subjects[]? | select(.kind=="ServiceAccount" and .name=="<sa-name>" and .namespace=="<sa-namespace>")) | "\(.metadata.name) -> \(.roleRef.kind)/\(.roleRef.name)"'
```

**Inspect the rules in a Role or ClusterRole:**

```bash
kubectl get role <role-name> -n <namespace> -o yaml
kubectl get clusterrole <clusterrole-name> -o yaml
```

Examine the `rules` array to identify granted API groups, resources, and verbs. Verify that the failed verb and resource appear in at least one rule.

**Search audit logs for authorization denials:**

For filesystem-based audit logs:

```bash
jq -r 'select(.user.username=="<subject>" and .responseStatus.code==403) | [.requestReceivedTimestamp, .verb, .objectRef.resource, .objectRef.namespace, .objectRef.name, .responseStatus.message] | @tsv' /var/log/kubernetes/audit.log | tail -50
```

Replace `<subject>` with the full subject identifier (e.g., `system:serviceaccount:namespace:name` for ServiceAccounts or the username for Users).

For GKE Cloud Logging:

```bash
gcloud logging read 'resource.type="k8s_cluster" AND protoPayload.status.code=403 AND protoPayload.authenticationInfo.principalEmail="<subject>"' --limit=50 --format=json | jq -r '.[] | [.timestamp, .protoPayload.methodName, .protoPayload.status.message] | @tsv'
```

**Measure authorization latency from apiserver metrics:**

```bash
kubectl proxy &
curl -s http://localhost:8001/metrics \
  | grep apiserver_authorization_duration_seconds \
  | grep -v '#'
```

Calculate p99 latency by identifying the smallest bucket where the cumulative count exceeds 99% of the `_count` value.

**Count authorization denials by subject:**

```bash
jq -r 'select(.responseStatus.code==403) | .user.username' /var/log/kubernetes/audit.log \
  | sort | uniq -c | sort -rn | head -20
```

**Create a minimally-privileged Role for common operations:**

For read-only access to Pods and ConfigMaps:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: reader
  namespace: <namespace>
rules:
- apiGroups: [""]
  resources: ["pods", "configmaps"]
  verbs: ["get", "list", "watch"]
```

For write access to Pods (typically required by controllers):

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-manager
  namespace: <namespace>
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: [""]
  resources: ["pods/status"]
  verbs: ["get", "update", "patch"]
```

**Bind a Role to a ServiceAccount:**

```bash
kubectl create rolebinding <binding-name> \
  --role=<role-name> \
  --serviceaccount=<namespace>:<serviceaccount-name> \
  -n <namespace>
```

**Verification checklist for RBAC policy changes:**

1. Confirm the subject type (User, Group, or ServiceAccount) and full identifier.
2. Verify that the RoleBinding or ClusterRoleBinding references the correct Role or ClusterRole.
3. Inspect the Role or ClusterRole rules to confirm that the required verb and resource are granted.
4. For namespace-scoped permissions, verify that the RoleBinding exists in the correct namespace.
5. For cluster-scoped permissions, verify that the ClusterRoleBinding exists and references the correct subject.
6. Use `kubectl auth can-i` to simulate the authorization check before deploying workload changes.
7. Monitor audit logs after policy changes to detect unexpected authorization denials.
8. If a policy change degrades authorization performance, check the `apiserver_authorization_duration_seconds` metric and consider simplifying role structures or reducing the number of bindings per subject.

**Common failure modes and recovery procedures:**

- **Missing RoleBinding:** Create the binding with `kubectl create rolebinding` or apply a YAML manifest.
- **Incorrect verb:** Update the Role to include the required verb (get, list, create, update, patch, delete, watch).
- **Incorrect resource:** Update the Role to include the required resource type. Use `kubectl api-resources` to verify the correct resource name.
- **Incorrect namespace:** Verify that the RoleBinding exists in the same namespace where the operation is being performed. For cluster-scoped resources, use a ClusterRoleBinding instead.
- **Immutable roleRef:** If you need to change which Role a RoleBinding references, delete the RoleBinding and recreate it with the correct roleRef. The same applies to ClusterRoleBindings.
- **High authorization latency:** Reduce the number of RoleBindings per subject, simplify Role rules by removing regex matchers, and ensure the apiserver RBAC cache is sized appropriately.
