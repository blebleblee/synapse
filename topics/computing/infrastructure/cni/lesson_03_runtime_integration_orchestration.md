# Lesson 3: Runtime Integration and Orchestration

## 1. First-Principles Intuition & Invariants

The container networking problem is, at its core, an identity and connectivity problem. When a process is confined to a Linux network namespace, it becomes invisible to the broader network fabric. It owns no IP address, holds no routes, and cannot exchange packets with any peer unless something outside the namespace reaches in, constructs the plumbing, and hands it the keys. That "something" is the Container Network Interface, but CNI itself is entirely passive: it is a specification, a set of conventions, and a directory of executables. The entity that decides *when* to invoke those executables, with *what arguments*, and in *what sequence*, is the container runtime. Understanding CNI at production depth therefore demands that you understand the precise moment in the runtime's lifecycle when network setup is delegated, what invariants must hold at that moment, and what the consequences are when they break.

The fundamental invariant of CNI is that network attachment is always sandboxed to a network namespace path, and that path must exist before any plugin is invoked. This sounds obvious until you trace the kernel-level mechanics. A network namespace is a first-class kernel object, created with `clone(CLONE_NEWNET)` or `unshare(1)`, and it persists as a reference-counted file descriptor. The runtime's responsibility is to create this namespace, pin it to the filesystem under `/var/run/netns/` or a CRI-managed equivalent path, and then pass that path as the `netns` parameter in the CNI invocation. The plugin opens that path, calls `setns(2)` to enter the namespace, configures the veth pair, assigns the IP address, writes routes, and exits. The process that will eventually run inside the container does not exist yet, or, in the Kubernetes pod model, is represented by the pause container. This decoupling of network setup from process execution is the most important architectural fact in CNI: networking is configured for a namespace, not for a process.

Kubernetes codifies this decoupling through its pod model. Every pod owns exactly one network namespace, shared by every container in the pod, anchored by the infra container (commonly called the pause container). The pause container does nothing but sleep, holding the namespace open. When `containerd` or CRI-O creates a pod sandbox in response to a `RunPodSandbox` CRI call from kubelet, they create the pause container first, establish its network namespace, invoke CNI to configure that namespace, and only then create application containers that join the same namespace via `clone(CLONE_NEWNET)` with no new network namespace flag. From the CNI plugin's perspective, it is always configuring a namespace owned by pause, never by your application. This is a critical debugging invariant: if you are tracing a network misconfiguration, the namespace you need to inspect belongs to the pause container, not to `nginx` or `envoy`.

The CNI specification defines the calling convention through three mandatory inputs: the CNI command (`ADD`, `DEL`, `CHECK`, or `VERSION`), the network configuration JSON passed over stdin, and a small set of environment variables. The variables `CNI_COMMAND`, `CNI_NETNS`, `CNI_IFNAME`, `CNI_PATH`, `CNI_ARGS`, and `CNI_CONTAINERID` collectively constitute the runtime-to-plugin contract. `CNI_CONTAINERID` is not a cgroup ID or a PID — it is an opaque string the runtime chooses to uniquely identify the attachment. `CNI_NETNS` is the filesystem path to the network namespace. `CNI_IFNAME` is the name the plugin should give the interface inside the namespace, conventionally `eth0`. `CNI_PATH` is a colon-delimited list of directories the runtime will search for plugin executables. The runtime forks the plugin binary directly, waits for it to exit, reads the JSON result from stdout, and interprets the exit code. Exit code zero means success; nonzero means the plugin's error JSON on stderr should be surfaced.

What makes this architecture both elegant and treacherous is that it is entirely synchronous and single-threaded from the plugin's perspective. There are no daemons, no sockets, no message buses. The plugin binary runs, mutates kernel networking state, and exits. This means that any plugin bug — a leaked goroutine, an unclosed file descriptor, a panic — affects exactly one pod attachment and no others. It also means that plugin execution latency directly impacts pod startup time. In clusters with high pod churn, CNI invocation latency is a first-class scheduling performance concern, not an afterthought.

## 2. Core Architecture & Mechanics

### The CRI Sandbox Lifecycle and CNI Invocation

To understand exactly when CNI fires, you must trace the `RunPodSandbox` code path in a production runtime. Consider `containerd`, whose CRI plugin is the dominant runtime in managed Kubernetes services. When kubelet calls `RunPodSandbox` over gRPC, containerd's CRI server begins a multi-phase sandbox construction sequence. It creates the OCI runtime bundle for the pause container, then calls `netPlugin.Setup()` from its internal CNI manager before calling `task.Start()` to actually start the pause process. The network namespace is created and pinned before the pause container's main process runs, and CNI is invoked against that namespace while it is still empty of any running processes. This ordering is mandatory: if you start the pause process before CNI runs, the process may attempt network operations that fail because no interface exists, and some init systems will interpret that failure as fatal.

The containerd CNI library (`github.com/containerd/go-cni`) wraps the raw plugin invocation. It reads `/etc/cni/net.d/` to discover network configurations, sorts them lexicographically to determine invocation order, and serializes them into `ADD` calls for each plugin in the chain. The library passes `prevResult` from each plugin's output as the `prevResult` field in the next plugin's stdin configuration, threading the allocation state forward through the chain. This is the chained plugin model defined in CNI spec 0.3.0 and later: plugins do not operate in isolation but in a pipeline where each plugin augments, validates, or records the work of its predecessors.

Here is the exact directory and configuration layout a production containerd node expects:

```
/etc/cni/net.d/
├── 10-calico.conflist          ← Primary network (lexicographically first)
├── 99-loopback.conf            ← Loopback plugin

/opt/cni/bin/
├── calico
├── calico-ipam
├── loopback
├── portmap
├── bandwidth
├── host-local
```

A `conflist` file encodes an ordered chain. The following is a production-grade Calico conflist demonstrating a full plugin chain with IPAM, loopback, port mapping, and bandwidth shaping:

```json
{
  "name": "k8s-pod-network",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "calico",
      "log_level": "info",
      "log_file_path": "/var/log/calico/cni/cni.log",
      "datastore_type": "kubernetes",
      "nodename": "__KUBERNETES_NODE_NAME__",
      "mtu": 0,
      "ipam": {
        "type": "calico-ipam",
        "assign_ipv4": "true",
        "assign_ipv6": "false"
      },
      "policy": {
        "type": "k8s"
      },
      "kubernetes": {
        "kubeconfig": "/etc/cni/net.d/calico-kubeconfig"
      }
    },
    {
      "type": "bandwidth",
      "capabilities": {
        "bandwidth": true
      }
    },
    {
      "type": "portmap",
      "snat": true,
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}
```

The `bandwidth` plugin uses Linux Traffic Control (`tc`) with Token Bucket Filter (TBF) qdiscs to enforce ingress/egress rate limits specified in the pod's annotations (`kubernetes.io/egress-bandwidth`). The `portmap` plugin programs `iptables` DNAT rules for `hostPort` mappings. Neither plugin makes sense in isolation; both depend on the veth interface and IP address that Calico established in the first step of the chain.

### CRI-O and Its CNI Invocation Path

CRI-O delegates CNI management to a component called the network-nens driver, backed by the `cni` package at `github.com/cri-o/ocicni`. The behavioral contract is identical to containerd's: `RunPodSandbox` calls `ocicni.SetUpPod()` before the pause container's process starts. CRI-O differs in one operationally significant way: it uses a network namespace manager that pre-creates a pool of network namespaces to amortize namespace creation overhead. When a pod is scheduled, CRI-O can claim a pre-existing namespace from the pool rather than calling `clone(CLONE_NEWNET)` synchronously. This reduces the critical path of `RunPodSandbox` by roughly the time of namespace creation and any associated kernel accounting, which under load can be measurable in the tens of milliseconds.

You can inspect CRI-O's network setup with `crictl`:

```bash
# List all pod sandboxes and their network state
crictl pods --no-trunc

# Inspect a specific sandbox and retrieve the network namespace path
crictl inspectp <SANDBOX_ID> | jq '.info.runtimeSpec.linux.namespaces[] | select(.type == "network")'

# Verify CNI-assigned IP from the sandbox info
crictl inspectp <SANDBOX_ID> | jq '.status.network.ip'
```

For containerd, the equivalent inspection path goes through `ctr`:

```bash
# List sandboxes (containerd CRI namespaces are under k8s.io)
ctr --namespace k8s.io containers list

# Inspect the container spec to find the network namespace path
ctr --namespace k8s.io containers info <CONTAINER_ID> | \
  jq '.Spec.linux.namespaces[] | select(.type == "network")'
```

The network namespace path recovered from either runtime can then be passed to `nsenter` or `ip` for direct kernel-level inspection, which is the fastest path to diagnosing a CNI misconfiguration:

```bash
# Given namespace path /var/run/netns/cni-abc123
ip netns exec cni-abc123 ip addr show
ip netns exec cni-abc123 ip route show
ip netns exec cni-abc123 ip neigh show

# Check the veth pair from the host side
ip link show | grep veth

# Trace the peer index to find which pod owns which veth
ip netns exec cni-abc123 ip link show eth0
# Note the "link-netnsid" value, then:
ip netns identify <peer-netns-id>
```

### Kubernetes Node-Agent CNI Coordination and the DaemonSet Pattern

Kubernetes itself does not call CNI. This is a point of frequent architectural confusion. CNI is invoked by the runtime (containerd or CRI-O) on the node. Kubernetes's role is to ensure that the CNI binaries and configuration files are present on every node before any pod scheduling can succeed. CNI plugins achieve this through a DaemonSet that runs a privileged init container to copy binaries into `/opt/cni/bin/` and write configuration files into `/etc/cni/net.d/`. The main DaemonSet container then runs the plugin's node agent (Calico's `calico-node`, Cilium's `cilium-agent`, Flannel's `flanneld`) which maintains the per-node routing state.

The following is a production-ready Calico node DaemonSet fragment demonstrating the binary installation init container pattern and the volume mounts that make CNI work at the node level:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: calico-node
  namespace: kube-system
  labels:
    k8s-app: calico-node
spec:
  selector:
    matchLabels:
      k8s-app: calico-node
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template:
    metadata:
      labels:
        k8s-app: calico-node
    spec:
      nodeSelector:
        kubernetes.io/os: linux
      tolerations:
        - effect: NoSchedule
          operator: Exists
        - key: CriticalAddonsOnly
          operator: Exists
        - effect: NoExecute
          operator: Exists
      serviceAccountName: calico-node
      terminationGracePeriodSeconds: 0
      priorityClassName: system-node-critical
      hostNetwork: true
      initContainers:
        - name: install-cni
          image: docker.io/calico/cni:v3.26.1
          command: ["/opt/cni/bin/install"]
          envFrom:
            - configMapRef:
                name: calico-config
          env:
            - name: CNI_CONF_NAME
              value: "10-calico.conflist"
            - name: SLEEP
              value: "false"
            - name: CNI_NET_DIR
              value: "/etc/cni/net.d"
            - name: KUBERNETES_NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          volumeMounts:
            - mountPath: /host/opt/cni/bin
              name: cni-bin-dir
            - mountPath: /host/etc/cni/net.d
              name: cni-net-dir
          securityContext:
            privileged: true
        - name: mount-bpffs
          image: docker.io/calico/node:v3.26.1
          command: ["calico-node", "-init", "-best-effort"]
          volumeMounts:
            - mountPath: /sys/fs
              name: sys-fs
              mountPropagation: Bidirectional
            - mountPath: /var/run/calico
              name: var-run-calico
              mountPropagation: Bidirectional
          securityContext:
            privileged: true
      containers:
        - name: calico-node
          image: docker.io/calico/node:v3.26.1
          env:
            - name: DATASTORE_TYPE
              value: "kubernetes"
            - name: WAIT_FOR_DATASTORE
              value: "true"
            - name: NODENAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
            - name: CALICO_NETWORKING_BACKEND
              value: "bird"
            - name: CLUSTER_TYPE
              value: "k8s,bgp"
            - name: IP
              value: "autodetect"
            - name: IP_AUTODETECTION_METHOD
              value: "first-found"
            - name: CALICO_IPV4POOL_CIDR
              value: "192.168.0.0/16"
            - name: CALICO_IPV4POOL_IPIP
              value: "Always"
            - name: CALICO_DISABLE_FILE_LOGGING
              value: "true"
            - name: FELIX_DEFAULTENDPOINTTOHOSTACTION
              value: "ACCEPT"
            - name: FELIX_IPV6SUPPORT
              value: "false"
            - name: FELIX_HEALTHENABLED
              value: "true"
          securityContext:
            privileged: true
          resources:
            requests:
              cpu: 250m
              memory: 128Mi
            limits:
              cpu: "1"
              memory: 512Mi
          livenessProbe:
            exec:
              command:
                - /bin/calico-node
                - -felix-live
                - -bird-live
            periodSeconds: 10
            initialDelaySeconds: 10
            failureThreshold: 6
            timeoutSeconds: 10
          readinessProbe:
            exec:
              command:
                - /bin/calico-node
                - -felix-ready
                - -bird-ready
            periodSeconds: 10
            timeoutSeconds: 10
          volumeMounts:
            - mountPath: /lib/modules
              name: lib-modules
              readOnly: true
            - mountPath: /run/xtables.lock
              name: xtables-lock
            - mountPath: /var/run/calico
              name: var-run-calico
            - mountPath: /var/lib/calico
              name: var-lib-calico
            - mountPath: /var/run/nodeagent
              name: policysync
            - mountPath: /var/log/calico/cni
              name: cni-log-dir
              readOnly: false
      volumes:
        - name: lib-modules
          hostPath:
            path: /lib/modules
        - name: var-run-calico
          hostPath:
            path: /var/run/calico
        - name: var-lib-calico
          hostPath:
            path: /var/lib/calico
        - name: xtables-lock
          hostPath:
            path: /run/xtables.lock
            type: FileOrCreate
        - name: sys-fs
          hostPath:
            path: /sys/fs
        - name: cni-bin-dir
          hostPath:
            path: /opt/cni/bin
        - name: cni-net-dir
          hostPath:
            path: /etc/cni/net.d
        - name: cni-log-dir
          hostPath:
            path: /var/log/calico/cni
        - name: policysync
          hostPath:
            path: /var/run/nodeagent
            type: DirectoryOrCreate
```

### Signal Flow Diagram

The following diagram captures the complete invocation sequence from kubelet through the runtime to CNI, showing the namespace lifecycle and the dataplane programming steps:

```
kubelet                 containerd/CRI-O         Linux Kernel          CNI Plugin Chain
   │                          │                       │                       │
   │── RunPodSandbox ────────>│                       │                       │
   │                          │── clone(CLONE_NEWNET)─>│                       │
   │                          │<── netns fd ──────────│                       │
   │                          │── bind mount netns ──>│                       │
   │                          │   /var/run/netns/cni-XYZ                      │
   │                          │                       │                       │
   │                          │── fork plugin #1 ─────────────────────────── >│ (calico)
   │                          │   CNI_COMMAND=ADD      │                      │
   │                          │   CNI_NETNS=/var/run/netns/cni-XYZ            │
   │                          │   CNI_IFNAME=eth0      │                      │
   │                          │   stdin: conflist[0]   │                      │
   │                          │                        │                      │
   │                          │                        │<── setns(netns_fd) ──│
   │                          │                        │<── ip link add veth0 │
   │                          │                        │    type veth         │
   │                          │                        │    peer name eth0    │
   │                          │                        │<── ip link set eth0  │
   │                          │                        │    netns <cni-XYZ>   │
   │                          │                        │<── ip addr add       │
   │                          │                        │    192.168.1.5/32    │
   │                          │                        │    dev eth0          │
   │                          │                        │<── ip route add      │
   │                          │                        │    169.254.1.1       │
   │                          │                        │    dev eth0          │
   │                          │                        │<── arp set           │
   │                          │                        │    169.254.1.1 proxy │
   │                          │<── stdout: result JSON ─────────────────────  │
   │                          │   (IPs, routes, interfaces)                   │
   │                          │                        │                      │
   │                          │── fork plugin #2 ─────────────────────────── >│ (bandwidth)
   │                          │   stdin: conf + prevResult                    │
   │                          │                        │<── tc qdisc add      │
   │                          │                        │    dev veth0 tbf     │
   │                          │<── stdout: result JSON ─────────────────────  │
   │                          │                        │                      │
   │                          │── fork plugin #3 ─────────────────────────── >│ (portmap)
   │                          │   stdin: conf + prevResult                    │
   │                          │                        │<── iptables -t nat   │
   │                          │                        │    -A CNI-HOSTPORT-  │
   │                          │                        │    DNAT ...          │
   │                          │<── stdout: result JSON ─────────────────────  │
   │                          │                        │                      │
   │                          │── start pause process ─>│                     │
   │<── RunPodSandbox OK ─────│                        │                      │
   │                          │                        │                      │
```

### kube-proxy Integration and Its Relationship to CNI

kube-proxy operates at a layer above and orthogonal to CNI. CNI is responsible for pod-level network identity: it assigns an IP address to a pod's namespace and programs the dataplane so that IP is reachable from the rest of the cluster. kube-proxy is responsible for service-level virtual IP translation: it watches the Kubernetes API server for `Service` and `Endpoints` (or `EndpointSlice`) objects and programs the kernel's packet processing pipeline to redirect traffic destined for a ClusterIP to one of the backing pod IPs.

In `iptables` mode, kube-proxy writes rules into the `nat` table's `PREROUTING` and `OUTPUT` chains. Each `ClusterIP:port` tuple gets a chain in the form `KUBE-SVC-<hash>`, which then uses statistically weighted `DNAT` rules to select a backend pod. The critical integration point with CNI is that kube-proxy's backend IPs must be the same IPs that CNI assigned. There is no handshake between kube-proxy and CNI; they both treat the pod IP as the shared identifier. If CNI assigns `192.168.1.5` to a pod, kube-proxy will program DNAT rules pointing to `192.168.1.5`, and those rules are only valid if CNI's dataplane programming ensures that traffic to `192.168.1.5` actually reaches the pod's network namespace.

In `ipvs` mode, kube-proxy creates a virtual server entry per ClusterIP using the IPVS kernel module and attaches real server entries for each backend pod. IPVS operates at a lower level than iptables, using hash tables in the kernel for O(1) lookup rather than O(n) iptables chain traversal, which matters significantly at scale (thousands of services). The integration with CNI remains identical: IPVS still depends on pod IPs that CNI assigned and programmed into the kernel routing tables.

Inspecting kube-proxy's view of service endpoints and correlating it with CNI-assigned addresses is a standard diagnostics procedure:

```bash
# View iptables rules for a service (iptables mode)
iptables -t nat -L KUBE-SERVICES -n --line-numbers | grep <service-cluster-ip>
iptables -t nat -L KUBE-SVC-<hash> -n -v

# View IPVS virtual servers and real servers (ipvs mode)
ipvsadm -Ln | grep -A 20 <service-cluster-ip>

# Cross-reference with actual pod IPs from CNI
kubectl get endpoints <service-name> -n <namespace> -o wide

# Verify pod IP from kubelet's perspective
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.podIP}'

# Verify the same IP from inside the namespace (via node-exec or crictl)
crictl inspectp <sandbox-id> | jq '.status.network.ip'
```

The two IPs must match. When they diverge — which can happen during rapid pod restarts if CNI's DEL and ADD are racing with kube-proxy's watch-and-reprogram loop — you will see DNAT rules pointing to stale pod IPs that the routing fabric no longer serves, producing intermittent connection failures on exactly the pods that cycled most recently.

### NetworkPolicy Enforcement Architecture

Kubernetes `NetworkPolicy` objects are API-layer constructs. The API server stores them in etcd; it does not enforce them. Enforcement is entirely the CNI plugin's responsibility. This is one of the most important facts to internalize about the Kubernetes security model: if you install a CNI plugin that does not implement NetworkPolicy (Flannel's basic VXLAN mode, for example), your `NetworkPolicy` objects will be silently ignored and all pods will communicate freely regardless of what you have declared.

Plugins that implement NetworkPolicy — Calico, Cilium, Weave Net, Antrea — do so through two fundamentally different dataplane mechanisms. The iptables-based approach, used by Calico's default Felix agent, translates each policy into a set of `filter` table chains attached to the veth interface endpoints. When a packet enters or leaves a pod's veth, it traverses a chain named after the pod's workload endpoint (e.g., `cali-tw-caliXXXXXXXXXX` for traffic to workload, `cali-fw-caliXXXXXXXXXX` for traffic from workload). Felix watches the Kubernetes API for NetworkPolicy, Pod, and Namespace changes, translates the policy into iptables rules, and atomically applies them using `iptables-restore`. The kernel's netfilter framework then enforces these rules at packet processing time.

The rule translation logic is non-trivial. A NetworkPolicy `spec.ingress` rule with `podSelector`, `namespaceSelector`, and `ports` becomes a chain that first jumps to a named ipset containing all matching source pod IPs (maintained by Felix as `ipset` objects for O(log n) lookup), then checks the destination port, and either accepts or drops. Consider the following policy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
      tier: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              env: production
          podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              env: production
          podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

This policy selects all pods labeled `app: backend, tier: api` in the `production` namespace and enforces two-way default-deny with explicit allow rules. When Felix processes this, it creates an ipset containing all IPs of pods matching `app: frontend` in namespaces matching `env: production`, and a separate ipset for all IPs of pods matching `app: postgres` in production namespaces. The iptables chains for each backend pod's veth endpoint then reference these ipsets in ACCEPT rules, with a default DROP at the chain tail. The DNS egress rule (port 53/UDP to any namespace) exists because without it, DNS would be blocked by the default-deny egress policy, breaking service discovery entirely — a mistake that silently takes down an application and is diagnosed by checking CoreDNS reachability before anything else.

You can inspect how Felix has translated a policy into kernel state:

```bash
# List all Calico-managed ipsets
ipset list | grep cali

# Show the contents of a specific ipset (source IPs for a policy rule)
ipset list cali40s:frontend-production

# View the iptables chains Felix created for a specific pod's veth
VETH=$(ip link show | grep cali | head -1 | awk '{print $2}' | tr -d ':')
iptables -t filter -L cali-tw-${VETH} -n -v
iptables -t filter -L cali-fw-${VETH} -n -v

# Check Felix's own policy programming logs
kubectl logs -n kube-system -l k8s-app=calico-node -c calico-node | \
  grep -i "policy\|endpoint\|ipset" | tail -50
```

## 3. High-Performance Optimization & Failure Modes

### CNI Latency Under High Pod Churn

In production clusters with aggressive horizontal pod autoscaling, the CNI invocation path becomes a throughput bottleneck. Each `RunPodSandbox` call serializes through IPAM (which must allocate an IP, often writing to an etcd or Kubernetes API backend), plugin fork-exec overhead, and iptables/ipset reprogramming. In clusters running hundreds of pods per minute — common in batch workloads, CI/CD systems, or machine learning training jobs — this serialization manifests as elevated `RunPodSandbox` P99 latency, which Kubernetes surfaces as pod scheduling lag.

The primary optimization levers are IPAM backend locality, plugin chain minimalism, and iptables atomicity. For IPAM, moving from a centralized etcd-backed allocation scheme to a per-node IP block assignment model (Calico's IP block allocation, where each node owns a /26 of the pod CIDR and allocates IPs locally) eliminates the network round-trip from every IPAM call. The node agent fetches a block from the API server once and then services hundreds of local `ADD` calls against its in-memory bitmap before needing another block. Under a purely local IPAM model, the IP allocation step drops from tens of milliseconds to microseconds.

Plugin chain length directly multiplies the fork-exec cost. Each plugin in a conflist requires the runtime to `fork()`, `exec()`, read config from stdin, and collect output from stdout. A chain of four plugins imposes four sequential fork-exec cycles. Keeping chains minimal — preferring plugins that consolidate functions over chains of many single-purpose plugins — meaningfully reduces per-pod startup time under load.

The iptables atomicity problem is more subtle. Felix (and kube-proxy in iptables mode) use `iptables-restore --noflush` to atomically apply rule updates. Under high pod churn, multiple iptables writers can race, causing `iptables-restore` calls to fail with `Another app is currently holding the xtables lock`. This failure is retriable, but the retry backoff adds latency. You can observe this with:

```bash
# Monitor xtables lock contention
watch -n 1 'cat /proc/locks | grep xtables | wc -l'

# Check for iptables-restore failures in Felix logs
kubectl logs -n kube-system -l k8s-app=calico-node -c calico-node | \
  grep -c "xtables lock"

# Measure the time Felix spends in iptables-restore
kubectl logs -n kube-system -l k8s-app=calico-node -c calico-node | \
  grep "iptables-restore" | awk '{print $NF}' | sort -n | tail -20
```

The architectural mitigation is to move to nftables or IPVS, which both offer batch update semantics without the xtables lock. Calico's `nftables` mode and kube-proxy's `ipvs` mode both reduce lock contention at scale. The tradeoff is operational familiarity: most platform engineers know iptables syntax and can read a chain dump in an incident. nftables rules require learning a different mental model, and IPVS debugging requires `ipvsadm` proficiency.

### Failure Mode: Stale CNI State on Node Drain

When a node is drained and pods are evicted, kubelet calls `StopPodSandbox` on each sandbox, which triggers the runtime to invoke CNI with `DEL` to remove network configuration. If the runtime crashes, is killed, or the node loses power between pod eviction and `StopPodSandbox` completion, CNI's `DEL` never fires. The IPAM backend retains the IP allocation, and the IP is effectively leaked. On node restart, the network namespace no longer exists, so CNI cannot clean up. IPAM backends handle this differently: `host-local` stores allocations in flat files under `/var/lib/cni/networks/<network-name>/` keyed by container ID; if those files survive a reboot, the leaked IPs can be manually recovered. Calico's calico-ipam stores allocations in `IPAMBlock` custom resources in the Kubernetes API and provides a reconciliation tool:

```bash
# Check for leaked IP allocations in Calico IPAM
calicoctl ipam check --show-problem-ips

# Release a specific leaked IP
calicoctl ipam release --ip=192.168.1.47

# Full IPAM garbage collection (use with caution in production)
calicoctl ipam gc --config=/etc/calico/calicoctl.cfg
```

For `host-local` IPAM, leaked allocations are files in the allocations directory. Any file whose name matches a container ID that no longer exists (verified against `crictl ps -a`) is a leaked allocation and can be safely removed:

```bash
# List host-local IPAM allocations for a network
ls -la /var/lib/cni/networks/cbr0/

# Cross-reference with active container IDs
crictl ps -a --output json | jq -r '.[].id' > /tmp/active_containers.txt

# Find leaked allocations (files with no matching running container)
for f in /var/lib/cni/networks/cbr0/*; do
  cid=$(basename "$f")
  if [[ "$cid" != "lock" ]] && ! grep -qF "$cid" /tmp/active_containers.txt; then
    echo "Leaked allocation: $f (IP: $(cat $f))"
  fi
done
```

### Failure Mode: CNI Plugin Binary Missing or Misconfigured

When the CNI binary is absent from `CNI_PATH`, the runtime receives a nonzero exit code with an error JSON blob. This error propagates up through the CRI call, and kubelet marks the sandbox creation as failed. The pod enters `ContainerCreating` state permanently, and the event stream shows the error message verbatim. The diagnostic sequence is:

```bash
# Check pod events for CNI errors
kubectl describe pod <pod-name> -n <namespace> | grep -A 20 "Events:"

# Verify CNI binaries are present on the node
# (exec into the node via kubectl debug or SSH)
ls -la /opt/cni/bin/
ls -la /etc/cni/net.d/

# Validate the conflist is syntactically correct JSON
python3 -m json.tool /etc/cni/net.d/10-calico.conflist

# Check containerd's CNI initialization status
journalctl -u containerd | grep -i "cni\|network" | tail -30

# Check CRI-O's CNI status
journalctl -u crio | grep -i "cni\|network" | tail -30
```

A silent failure mode deserves special attention: a conflist that is syntactically valid JSON but semantically wrong (a misspelled plugin `type`, a missing required field) will cause the first `ADD` invocation to fail with an application-level error, but the runtime may successfully parse the config file at startup without detecting the error. The failure only surfaces when the first pod is created. The practical preventive measure is to run `cnitool` from the CNI test utilities against a test namespace before deploying a new conflist to production:

```bash
# Install cnitool from go install github.com/containernetworking/cni/cnitool@latest
# Create a test namespace
ip netns add test-cni-validate

# Test ADD operation
CNI_PATH=/opt/cni/bin NETCONFPATH=/etc/cni/net.d \
  cnitool add k8s-pod-network /var/run/netns/test-cni-validate

# Test DEL operation (cleanup)
CNI_PATH=/opt/cni/bin NETCONFPATH=/etc/cni/net.d \
  cnitool del k8s-pod-network /var/run/netns/test-cni-validate

# Remove test namespace
ip netns del test-cni-validate
```

### Multi-Runtime CNI Orchestration with RuntimeClass

Kubernetes 1.14 introduced `RuntimeClass`, which allows a cluster to run multiple container runtimes simultaneously and assign pods to specific runtimes via `spec.runtimeClassName`. A common production pattern is running security-sensitive workloads in gVisor (`runsc`) or Kata Containers while running standard workloads in runc, all on the same cluster. This creates a multi-runtime CNI orchestration problem: each runtime must be configured with the same CNI plugin, but different runtimes may have different requirements for network namespace management or may not support certain plugin capabilities.

The configuration is managed at the containerd level through `runtime` handlers defined in `/etc/containerd/config.toml`:

```toml
version = 2

[plugins."io.containerd.grpc.v1.cri"]
  [plugins."io.containerd.grpc.v1.cri".cni]
    bin_dir = "/opt/cni/bin"
    conf_dir = "/etc/cni/net.d"
    max_conf_num = 1
    conf_template = ""

  [plugins."io.containerd.grpc.v1.cri".containerd]
    default_snapshotter = "overlayfs"

    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes]

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
        runtime_type = "io.containerd.runc.v2"
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
          SystemdCgroup = true

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.gvisor]
        runtime_type = "io.containerd.runsc.v1"
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.gvisor.options]
          TypeUrl = "io.containerd.runsc.v1.options"
          ConfigPath = "/etc/containerd/runsc.toml"

      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
        runtime_type = "io.containerd.kata.v2"
        privileged_without_host_devices = true
        [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata.options]
          ConfigPath = "/opt/kata/share/defaults/kata-containers/configuration.toml"
```

The corresponding `RuntimeClass` objects in the cluster:

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: gvisor
scheduling:
  nodeSelector:
    runtime.gvisor/sandbox: "true"
---
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata-containers
handler: kata
scheduling:
  nodeSelector:
    kata-containers.io/kata-runtime: "true"
  tolerations:
    - key: "kata-containers.io/kata-runtime"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"
```

In this configuration, containerd uses the same CNI conflist for all runtimes, but the sandbox creation path differs. gVisor creates a standard Linux network namespace and then runs the guest kernel inside it, so CNI operates identically to runc from the namespace perspective. Kata Containers creates a network namespace and then passes its configuration to the guest VM through a network model (macvtap or TC-redirect), requiring the Kata runtime to translate CNI's result JSON into VM network configuration. The veth that CNI creates ends up bridged or mirrored into the VM's virtual NIC, and the pod IP exists inside the VM's own network stack rather than directly in the host namespace. This has implications for NetworkPolicy enforcement: Calico's iptables rules apply to the host-side veth, which sees all VM traffic, so policy enforcement remains intact even though the application processes are inside a VM.

The observability command to verify which runtime is handling which sandbox in a multi-runtime cluster, and that CNI operated correctly for each:

```bash
# List pods with their runtime class
kubectl get pods -A -o custom-columns=\
"NAMESPACE:.metadata.namespace,\
NAME:.metadata.name,\
RUNTIME:.spec.runtimeClassName,\
IP:.status.podIP,\
NODE:.spec.nodeName"

# For gVisor pods, verify the runsc sandbox is running and has network
crictl pods | grep <gvisor-pod-name>
crictl inspectp <sandbox-id> | jq '{
  runtimeHandler: .info.runtimeHandler,
  networkNamespace: .info.runtimeSpec.linux.namespaces[] | select(.type == "network"),
  ip: .status.network.ip
}'

# Verify CNI created the veth on the host side regardless of runtime
ip link show type veth | grep -c veth
```

The invariant across all runtimes is that CNI operates on a network namespace path and returns a valid result JSON. As long as the runtime correctly creates a network namespace and passes its path to CNI, the plugin chain is unaware of whether runc, gVisor, or Kata will occupy that namespace. This namespace-centric abstraction is what makes CNI composable across the entire spectrum of container execution environments.
