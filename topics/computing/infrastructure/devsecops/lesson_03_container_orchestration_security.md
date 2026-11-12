# Lesson 3: Container Security, Orchestration, Runtime Protection

## 1. First-Principles Intuition & Invariants

The container security problem is fundamentally a problem of controlled resource sharing and privilege delegation across multiple trust boundaries. Before containers, the Unix operating system solved isolation through process boundaries: each process received its own address space, file descriptor table, and signal handlers. The kernel enforced these boundaries through page tables, capability bits, and system call filters. Containers do not introduce new isolation mechanisms; rather, they compose existing OS primitives—namespaces, cgroups, and seccomp filters—into a coherent isolation layer that sits between the application and the kernel.

To understand why this matters, consider the threat model. A containerized application running as root inside a container can theoretically escape that container and compromise the host kernel or sibling containers if isolation is misconfigured. The attack surface expands at three layers: first, the container runtime itself (runc, containerd) executes privileged operations to set up namespaces and cgroups; second, the orchestrator (Kubernetes) manages policy and admission control across a cluster of nodes; third, the application inside the container can exploit kernel vulnerabilities or misconfigured permissions. Each layer introduces both opportunity for defense and vectors for compromise.

The invariant that governs all container security is this: isolation is only as strong as the weakest primitive in the stack. If cgroups do not enforce memory limits correctly, a container can exhaust host memory and trigger out-of-memory kills across the entire node. If seccomp filters are incomplete, a container can invoke privileged syscalls and manipulate kernel data structures. If namespaces do not properly unshare the network stack, a container can sniff or inject packets on the host network. If the container image contains a vulnerable library, no amount of runtime protection can eliminate the vulnerability—only detection and response.

This lesson treats container security as a series of concentric rings, each with specific guarantees and failure modes. The innermost ring is the Linux kernel primitive layer: namespaces (UTS, Mount, PID, IPC, Network, User) and cgroups (v1 and v2 unified hierarchy). These are the enforcement mechanisms. The next ring is the container runtime (runc, cri-o), which translates image specifications into kernel primitives and manages the lifecycle of container processes. The third ring is the orchestrator (Kubernetes), which defines policy, admission control, network policies, and service mesh integration. The outermost ring is the supply chain: image scanning, signed artifacts, and runtime threat detection.

### The Namespace-Cgroup Duality

Namespaces provide logical isolation: they virtualize kernel resources so that a process sees a constrained view of the system. A process in a new PID namespace sees only its own process tree, not the host's process tree. A process in a new Network namespace sees only its own network interfaces and routing table. Cgroups provide resource accounting and enforcement: they limit CPU shares, memory, disk I/O, and other resources that a group of processes can consume.

The duality is asymmetric in power but complementary in scope. Namespaces cannot prevent a container from consuming all CPU time—that is the cgroup's job. Cgroups cannot hide the presence of other processes on the system—that is the namespace's job. Together, they form the isolation boundary. A container escape typically requires breaking out of both: either by finding a namespace bypass (a kernel bug that allows cross-namespace communication) or by exploiting a kernel subsystem that is not properly namespaced (such as certain device drivers or the keyring subsystem).

### The User Namespace Privilege Boundary

The User namespace deserves special attention because it is the mechanism by which containers can run unprivileged. Inside a User namespace, a process can have UID 0 (root) without possessing capabilities on the host. The kernel maintains uid_map and gid_map files that define the mapping between container UIDs and host UIDs. If a container process has UID 0 inside the namespace but the mapping assigns it UID 65534 (nobody) on the host, then any capability checks performed by the kernel use the mapped UID, not the container UID.

This is a crucial invariant: running a container with a User namespace does not prevent the container from gaining UID 0 inside the namespace, but it does prevent the container from obtaining host-level privileges even if it escapes the namespace. This is why production Kubernetes clusters should always use User namespaces for untrusted workloads. The security trade-off is runtime overhead (the kernel must perform UID/GID translation on every capability check) and complexity (shared volumes require careful uid/gid handling).

### Threat Model & Attack Surface

The attack surface for container security spans multiple vectors. At the image layer, a malicious or vulnerable container image may contain backdoors, vulnerable libraries, or rootkits. At the runtime layer, a bug in runc or containerd could allow a container to escape its isolation boundary. At the kernel layer, a vulnerability in the Linux kernel—particularly in namespace or cgroup implementations—could allow a container to break isolation. At the orchestration layer, misconfigured admission controllers, network policies, or RBAC could allow an attacker to deploy a privileged container or move laterally between pods. At the supply chain layer, a compromised build pipeline or image registry could inject malicious code into container images before they reach the cluster.

The threat model must assume that an attacker can run arbitrary code inside a container. The goal of defense is to limit what that code can achieve: it should not escape the container, compromise other containers, compromise the host, or exfiltrate sensitive data. This is why defense-in-depth is essential: multiple layers of protection ensure that a single bypass does not compromise the system.

---

## 2. Core Architecture & Mechanics

### Namespace Implementation & Kernel Data Structures

Linux namespaces are implemented through kernel data structures that maintain per-namespace state. The `nsproxy` structure is the entry point: it is a per-process structure that holds pointers to namespace-specific state. A task_struct (the kernel representation of a process) contains a pointer to its nsproxy. When a process is forked or calls clone(2) with the CLONE_NEW* flags, the kernel allocates new namespace structures and updates the nsproxy.

```c
// Simplified nsproxy structure (from linux/nsproxy.h)
struct nsproxy {
    atomic_t count;
    struct uts_namespace *uts_ns;
    struct ipc_namespace *ipc_ns;
    struct mnt_namespace *mnt_ns;
    struct pid_namespace *pid_ns_for_children;
    struct net *net_ns;
    struct user_namespace *user_ns;
    struct cgroup_namespace *cgroup_ns;
};
```

Each namespace type maintains its own data structures. The PID namespace, for example, uses a hierarchical tree of `pid` structures. When a process in a child PID namespace calls getpid(2), the kernel returns the virtual PID (allocated within the child namespace) rather than the global kernel PID. The PID namespace hierarchy allows a parent namespace to observe and manage child namespaces, while processes in child namespaces cannot see processes in sibling or parent namespaces.

The Mount namespace maintains a per-namespace mount tree. When a process calls mount(2) within a new Mount namespace, the filesystem changes are visible only to processes within that namespace. This is critical for container isolation: a container can mount volumes, change the root filesystem with chroot(2) or pivot_root(2), and modify device nodes without affecting the host or sibling containers.

The Network namespace virtualizes the entire network stack: network interfaces, routing tables, firewall rules, and socket tables. Processes in a Network namespace see only network interfaces and routes that belong to that namespace. To communicate across namespaces, packets must traverse a virtual ethernet pair (veth) or pass through network bridges that connect namespaces. This is the basis for container networking: each container receives a virtual interface, and the container runtime configures routing so that packets destined for the container reach it through the veth pair.

The User namespace maps UIDs and GIDs from the container namespace to the host namespace. The mapping is stored in /proc/[pid]/uid_map and /proc/[pid]/gid_map. These are newline-separated lists of three space-separated integers: the first is the start of the range in the container namespace, the second is the start of the range in the host namespace, and the third is the length of the range. A container running as UID 0 with a uid_map of "0 100000 65536" means that UID 0 in the container maps to UID 100000 on the host. If the container escapes the namespace boundary, it will have the privileges of UID 100000, not UID 0.

### Cgroups: Resource Accounting and Enforcement

Cgroups (control groups) organize processes into hierarchical groups and apply resource limits to each group. Cgroups v1 uses separate subsystems for CPU, memory, I/O, devices, and other resources. Each subsystem maintains its own hierarchy and rules. A process belongs to exactly one cgroup in each subsystem hierarchy.

Cgroups v2 (the unified hierarchy) consolidates all subsystems into a single hierarchy, reducing complexity and improving consistency. In v2, a process belongs to one cgroup, and all resource limits are managed through that single cgroup. The memory controller in v2 uses a page_counter that tracks anonymous pages, file-backed pages, and kernel memory. When a process or cgroup reaches its memory limit, the kernel can either trigger reclamation (evicting page-backed pages to swap) or invoke the out-of-memory (OOM) killer, which terminates processes in the cgroup.

The CPU controller uses CPU shares (in v1) or CPU weight (in v2) to allocate CPU time proportionally. If two cgroups are running on the same CPU, one with weight 100 and another with weight 50, the first cgroup will receive approximately twice as much CPU time as the second. Additionally, the cpu.max setting in v2 allows hard limits: a cgroup can be limited to a maximum number of microseconds per period. If a cgroup exceeds this limit, the scheduler will throttle it until the period resets.

The I/O controller (blkio in v1, io in v2) manages disk I/O bandwidth. The io.max setting allows per-device I/O limits. The io.stat setting exposes I/O statistics: read/write bytes, read/write operations, and discard operations. Containers can be limited to prevent a single container from saturating disk bandwidth and starving other containers.

The device controller restricts access to character and block devices. By default, containers are granted access only to essential devices: /dev/null, /dev/zero, /dev/full, /dev/random, /dev/urandom, /dev/tty, and /dev/console. Access to /dev/mem, /dev/kmem, /dev/port, and raw block devices is denied. This prevents a container from reading arbitrary kernel memory or writing to raw disks.

### Container Runtimes: From Image to Process

Container runtimes translate container image specifications into running processes. The Open Container Initiative (OCI) defines a standard image format (OCI Image Spec) and runtime format (OCI Runtime Spec). The OCI Runtime Spec defines a JSON configuration file (config.json) that specifies the process to run, the root filesystem, environment variables, mounts, and resource limits.

When a container runtime (such as runc or cri-o) starts a container, it performs the following steps:

1. Extract or mount the container image layers into a root filesystem bundle.
2. Allocate a user namespace (if enabled) and compute UID/GID mappings.
3. Allocate namespaces for PID, IPC, UTS, Mount, and Network.
4. Create cgroups and apply resource limits.
5. Set up the mount namespace: pivot_root(2) into the container root filesystem, mount /proc, /sys, and other essential filesystems.
6. Set up the network namespace: create veth pairs, move them into the namespace, configure IP addresses and routing.
7. Apply seccomp filters, AppArmor profiles, or SELinux policies.
8. Transition to the specified UID/GID inside the container namespace.
9. Execute the entrypoint process.

The runtime maintains a state file that tracks the container's lifecycle: created, running, paused, stopped. If the container process exits, the runtime cleans up the namespace, cgroup, and temporary mounts.

A critical invariant during this process is that the runtime must execute all privileged operations (namespace and cgroup setup) before dropping privileges. If the runtime drops privileges too early, it will not be able to set up namespaces or cgroups. If it drops privileges too late, a malicious or buggy runtime could expose privileged code paths that the container can exploit.

### Seccomp Filters: System Call Sandboxing

Seccomp (secure computing mode) allows processes to restrict the system calls they can invoke. Seccomp operates in two modes: strict and filter. In strict mode, a process can only invoke read(2), write(2), exit(2), and sigreturn(2). Strict mode is rarely used because it is too restrictive. Filter mode uses BPF (Berkeley Packet Filter) to allow fine-grained control over system calls based on their arguments.

A seccomp filter is a BPF program that receives a seccomp_data structure containing the system call number, architecture, and arguments. The BPF program returns a seccomp action: SECCOMP_RET_ALLOW (allow the call), SECCOMP_RET_ERRNO (return an error), SECCOMP_RET_TRACE (invoke a tracer, typically for debugging), or SECCOMP_RET_KILL_PROCESS (terminate the process).

Container runtimes typically apply a default seccomp profile that allows most system calls but denies dangerous ones. Dangerous calls include arch_prctl(2) (which can be used to disable seccomp), ptrace(2) (which can be used to attach to host processes), kexec_load(2) (which can replace the kernel), and mount(2) and umount(2) (which can be used to break out of the container filesystem isolation). A container can define a custom seccomp profile to allow or deny specific calls based on its needs.

The security trade-off of seccomp is that it adds overhead: every system call must be checked against the BPF program. For system calls that are invoked frequently (such as read(2) or write(2)), this overhead can be measurable. Additionally, seccomp filters can break applications that rely on denied system calls. A container that attempts to call a denied system call will receive an error (typically EPERM or ENOSYS), which may cause the application to crash or behave unexpectedly.

---

## 3. Kubernetes Security Primitives

### Pod Security Standards & Admission Control

Kubernetes Pod Security Standards (PSS) define three security policies: Restricted, Baseline, and Privileged. The Restricted policy is the strictest: it requires that containers run as non-root, drop dangerous capabilities, disallow privilege escalation, enforce read-only root filesystems, and use a defined seccomp profile. The Baseline policy is permissive: it allows most configurations but blocks the most dangerous ones (such as running with privileged: true). The Privileged policy allows all configurations and is intended only for system components.

Pod Security Standards are enforced through admission controllers. An admission controller intercepts API requests before they are persisted in etcd. A Pod Security Standards admission controller examines the pod specification and compares it against the policy. If the pod violates the policy, the admission controller rejects the pod.

This mechanism is coarse-grained: it operates at the pod level, not the individual container level. A pod with multiple containers can have different security contexts for each container, and the admission controller evaluates all containers against the policy. If any container violates the policy, the entire pod is rejected.

### Network Policies & Service Mesh Integration

Kubernetes Network Policies define ingress and egress rules at the pod level. By default, all traffic is allowed. A Network Policy specifies a pod selector and rules that restrict traffic to and from selected pods. Rules can filter by namespace, pod labels, IP CIDR blocks, and port/protocol.

A typical Network Policy denies all ingress traffic by default, then selectively allows specific traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - protocol: TCP
      port: 8080
```

Network Policies are enforced by the container network interface (CNI) plugin. The CNI plugin (such as Calico, Cilium, or Weave) intercepts packets at the host or pod network interface and applies the policy rules. If a packet does not match any allow rule, it is dropped.

Service meshes (such as Istio or Linkerd) extend network policies with more sophisticated control: traffic splitting, circuit breaking, retry logic, and distributed tracing. A service mesh injects a sidecar proxy (typically Envoy) into each pod, and all traffic flows through the proxy. The mesh control plane configures the proxies to enforce policies. Service meshes can provide fine-grained control over traffic, including mutual TLS (mTLS) for pod-to-pod communication.

The security benefit of a service mesh is that mTLS provides cryptographic proof of identity. Instead of relying on IP addresses or Kubernetes service names (which can be spoofed), pods authenticate each other using certificates. The mesh control plane issues certificates to each pod, and pods verify the certificate of the peer before accepting a connection.

### RBAC and Secret Management

Role-Based Access Control (RBAC) in Kubernetes defines who can perform which actions on which resources. RBAC consists of four objects: Role, ClusterRole, RoleBinding, and ClusterRoleBinding. A Role defines a set of permissions (verbs like get, list, create, delete) on resources (like pods, services, secrets). A RoleBinding connects a Role to a user, group, or service account within a namespace. A ClusterRole and ClusterRoleBinding operate at the cluster level.

An attacker who gains execution inside a container will typically try to read Kubernetes secrets (which may contain database passwords, API keys, or other sensitive data) and then use the Kubernetes API to move laterally to other containers or escalate privileges. Kubernetes prevents this through several mechanisms.

First, RBAC restricts which secrets a service account can read. By default, a service account has minimal permissions. A pod can only read secrets in its own namespace and only if the service account bound to the pod has permission to read those secrets.

Second, Kubernetes manages the service account's credentials through a projected volume: the service account token is mounted into the pod at /var/run/secrets/kubernetes.io/serviceaccount/token. The token is a signed JWT that identifies the service account. When the pod makes a request to the Kubernetes API, it includes the token in an Authorization header. The API server verifies the token and checks the RBAC rules to see if the service account is authorized to perform the requested action.

Third, secrets are stored in etcd, which is the Kubernetes datastore. Etcd can be configured to encrypt secrets at rest using a key encryption key (KEK). By default, secrets are stored unencrypted in etcd. To encrypt secrets at rest, the cluster administrator must configure the kube-apiserver with an encryption provider, such as aescbc or kmip. When a secret is stored, the API server encrypts it using the encryption provider. When the secret is retrieved, the API server decrypts it.

A best practice for secret management is to use an external secret store, such as HashiCorp Vault or AWS Secrets Manager, rather than storing secrets in Kubernetes. The pod can authenticate to the external secret store using a Kubernetes service account token or a pod identity mechanism (such as IRSA on AWS EKS or Workload Identity on GKE). The pod retrieves the secret from the external store and uses it in memory, without storing the secret in Kubernetes.

---

## 4. Runtime Threat Detection and Response

### Process and System Call Monitoring

Runtime threat detection works by monitoring process behavior and system call patterns to detect anomalies that may indicate a compromise. Tools such as Falco and Sysdig attach eBPF (extended Berkeley Packet Filter) programs to the kernel to capture system calls, file access, network connections, and process execution events.

An eBPF program is a program written in a restricted C dialect that runs in the kernel. The kernel JIT-compiles the program to native machine code and executes it in the kernel. eBPF programs can read kernel data structures, filter events, and send events to userspace. Because eBPF programs run in the kernel, they capture events with minimal overhead and minimal visibility to userspace processes.

A typical threat detection policy monitors for suspicious system calls or patterns. For example:

- A process executing a shell (such as /bin/bash or /bin/sh) in a container that should only run a single application process.
- A process reading sensitive files (such as /etc/shadow or /proc/self/environ) that it should not have access to.
- A process attempting to escape the container by accessing /proc/sys or /proc/sysrq-trigger.
- A process attempting to load kernel modules (insmod or modprobe).
- A process opening a raw socket or attempting to sniff network traffic.

When a policy violation is detected, the runtime threat detection tool can trigger a response: log the event, create an alert, or isolate the container.

### Container Escapes: Exploitation Patterns and Mitigations

A container escape is an attack in which a process inside a container gains execution outside the container's isolation boundary. Container escapes fall into several categories based on the mechanism.

Kernel vulnerability exploits target bugs in the Linux kernel that affect namespace or cgroup implementations. For example, CVE-2022-0847 ("Dirty COW") allowed a process to overwrite arbitrary files by exploiting a race condition in the copy-on-write mechanism. A container running with an unpatched kernel could exploit this vulnerability to overwrite host files or escape the container. The mitigation is to regularly patch the kernel and run a vulnerability scanner to detect unpatched systems.

Privileged container escapes occur when a container is run with --privileged or with dangerous capabilities such as CAP_SYS_ADMIN. A privileged container has access to the host's devices, network namespaces, and other resources. An attacker inside a privileged container can often mount the host filesystem, chroot into it, and achieve effective host-level code execution. The mitigation is to avoid running privileged containers and to drop unnecessary capabilities.

Runtime bugs in runc or containerd can allow a container to escape. For example, CVE-2019-5736 (the runc vulnerability) allowed a container to overwrite the runc binary itself and achieve code execution on the host. The vulnerability was in the open(2) call used to open the runc binary: the container could create a symlink to the runc binary before it was opened, causing runc to open and execute the symlink target instead. The mitigation is to keep the container runtime up to date.

Device driver vulnerabilities can expose privileged operations through device files. For example, if a container is granted access to /dev/mem or /dev/kmem, it can read and write arbitrary kernel memory. The mitigation is to restrict device access through cgroup device controller rules and AppArmor or SELinux policies.

The shared kernel limitation is the fundamental constraint of containers: all containers on a host share the same kernel. A kernel vulnerability affects all containers. Virtual machines (VMs) do not have this limitation because each VM runs its own kernel. This is why some organizations use kata containers, which run each container in its own lightweight VM. The security trade-off is overhead: VMs have higher memory and CPU overhead than containers.

### Detection-Response Orchestration

Modern container platforms integrate threat detection with automated response. When a threat is detected, the platform can take actions such as:

- Immediately terminate the compromised container and trigger pod restart.
- Isolate the container by applying a network policy that blocks all traffic.
- Dump the process memory for forensic analysis.
- Record the system call trace leading up to the attack.
- Trigger a security incident workflow that notifies security teams and creates a ticket in the incident management system.

An example orchestration workflow in Kubernetes might use Falco to detect a suspicious system call, then use a webhook to trigger a response policy:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-rules
data:
  custom-rules.yaml: |
    - rule: Suspicious Shell in Container
      desc: Detect shell execution in production containers
      condition: >
        spawned_process and container and
        proc.name in (bash, sh, dash) and
        container.labels[environment] = production
      output: >
        Suspicious shell spawned
        (user=%user.name command=%proc.cmdline container=%container.name)
      priority: WARNING
```

When Falco detects the rule match, it sends a webhook notification to a response service. The response service examines the event, verifies that the pod should not spawn shells, and takes action:

```python
def respond_to_threat(event):
    namespace = event['container']['namespace']
    pod_name = event['container']['pod_name']
    
    # Immediately terminate the pod
    v1 = client.CoreV1Api()
    v1.delete_namespaced_pod(
        pod_name, 
        namespace, 
        grace_period_seconds=0
    )
    
    # Apply a deny-all network policy to the namespace
    apply_network_isolation(namespace)
    
    # Log to security event store
    log_security_event(event)
```

This approach provides defense-in-depth: the attack is detected, the compromised container is immediately removed, and further lateral movement is prevented.

---

## 5. Supply Chain Security

### Image Scanning and Vulnerability Management

Container image vulnerability scanning inspects images for known vulnerabilities in their dependencies. A scanner typically maintains a vulnerability database (such as the National Vulnerability Database, NVD) and compares each package in the image against the database. For each vulnerability, the scanner reports the package name, installed version, vulnerable version range, and severity.

Vulnerability scanning can occur at multiple points in the pipeline:

- During development, scanning in the build pipeline catches vulnerabilities before the image is pushed to a registry.
- At registry admission, a policy can reject images with critical vulnerabilities or require remediation before deployment.
- At runtime, a continuous scanner re-scans deployed images to detect newly disclosed vulnerabilities in already-deployed containers.

A limitation of vulnerability scanning is that it only detects known vulnerabilities. A zero-day vulnerability (one that is not yet in the vulnerability database) will not be detected. Additionally, a vulnerability database entry may have a long latency: a vulnerability may exist for months before it is discovered and added to the database.

### Image Signing and Supply Chain Attestation

Image signing provides cryptographic proof that an image has not been tampered with. A container image is signed using a private key, and the signature is verified using the corresponding public key. Tools such as Cosign (part of sigstore) allow developers to sign container images and attestations.

A Cosign signature is stored as an OCI artifact in the container registry. When a cluster administrator wants to verify an image, they provide Cosign with the image reference and the public key. Cosign retrieves the signature artifact from the registry and verifies the signature using the public key.

An attestation is a statement about the image, signed by the entity that made the statement. An attestation might assert that the image has been scanned for vulnerabilities, that it has passed security tests, or that it has been built from a specific source commit. Attestations are stored in the registry and can be verified using the signer's public key.

A policy engine can enforce image signing requirements: a cluster can reject any image that is not signed or that does not have required attestations. For example, a policy might require that an image is signed by the development team, has been scanned for vulnerabilities, and has a SBOM (software bill of materials) attestation.

An SBOM lists all the dependencies (libraries, frameworks, tools) included in the image. An SBOM can be generated during the build process using tools such as syft. When a new vulnerability is disclosed, the SBOM can be used to quickly identify which images are affected.

### Build System Hardening and Attestation

The container build system is a critical part of the supply chain. A compromised build system can inject malicious code into all images built by that system. Therefore, the build system must be hardened and monitored.

Best practices for build system security include:

- Signing all build artifacts with a signing key that is stored in a hardware security module (HSM) or a key management service (KMS).
- Logging all build operations, including inputs, outputs, and builder identity.
- Restricting who can trigger builds and who can approve image deployment.
- Using ephemeral build environments that are destroyed after each build, so no state persists between builds.
- Scanning all source code for secrets before the build begins, to prevent accidental inclusion of API keys or passwords.

Build provenance is metadata about how an image was built: which source repository and commit, which builder, which build tools and their versions. Provenance is used to audit the build process and detect compromised builds. Tools such as Tekton or GitHub Actions can generate provenance attestations that are signed and stored in the registry.

---

## 6. Operational Patterns and Production Hardening

### Zero-Trust Architecture in Container Clusters

Zero-trust security assumes that no entity (user, service, or container) should be trusted by default. Instead, all entities must authenticate and their actions must be authorized before they are allowed. In a container cluster, zero-trust means:

- All pod-to-pod communication is authenticated and encrypted (mutual TLS).
- All API calls to the Kubernetes API are authenticated and authorized (RBAC).
- All network traffic is explicitly allowed (default deny network policies).
- All container images are verified to be signed by a trusted authority.
- All container behavior is monitored and deviations are detected and responded to.

Implementing zero-trust requires multiple layers of control. A service mesh provides mTLS for pod-to-pod communication. RBAC provides authorization for API access. Network policies provide allow-listing for network traffic. Image signing provides verification of container images. Runtime threat detection provides behavioral monitoring.

The advantage of zero-trust is that it limits the impact of a compromise. If a single container is compromised, the attacker cannot immediately access other containers (they must first compromise the mTLS certificate), cannot modify the cluster (they must first bypass RBAC), and cannot exfiltrate data over the network (network policies restrict egress traffic). Each layer adds time and complexity to the attack, increasing the likelihood of detection.

### Multi-Tenancy Isolation

Kubernetes supports multi-tenancy: multiple independent teams or customers can use the same cluster, with strong isolation between tenants. Isolation is achieved through a combination of namespaces, RBAC, network policies, and resource quotas.

Each tenant is assigned a Kubernetes namespace. RBAC rules restrict each service account to its own namespace: a service account in one namespace cannot read or modify resources in another namespace. Network policies prevent pods in one namespace from communicating with pods in another namespace. Resource quotas limit the CPU, memory, and storage that each namespace can consume, preventing one tenant from starving other tenants of resources.

A critical security consideration in multi-tenancy is node security: if an attacker compromises a container and gains node-level access, they can access containers from other tenants on the same node. To mitigate this, nodes should be dedicated to a single tenant, or node affinity rules should be used to restrict which pods can be scheduled on a node.

Another consideration is storage: if multiple tenants share the same storage backend, an attacker might exploit the storage driver to access data from other tenants. To mitigate this, each tenant should have a dedicated storage controller or storage volumes should be encrypted separately for each tenant.

### Encryption at Rest and in Transit

All sensitive data should be encrypted at rest (when stored) and in transit (when transmitted). For data at rest, Kubernetes stores all data in etcd. Etcd can be configured to encrypt secrets at rest using a KEK. Additionally, persistent volumes (PVs) can be encrypted using a storage provider's encryption mechanism. For example, AWS EBS volumes can be encrypted using AWS KMS, and Google Cloud Persistent Disks can be encrypted using Google Cloud KMS.

For data in transit, all communication should use TLS. The Kubernetes API server should be accessed over HTTPS (port 443), not HTTP (port 80). Service mesh mTLS provides encryption for pod-to-pod communication. Ingress controllers should terminate TLS connections from external clients and establish TLS connections to backend services.

Certificate management is critical: certificates must be renewed before they expire, and compromised certificates must be revoked immediately. Kubernetes can automatically rotate service account tokens, and certificate provisioning tools like cert-manager can automatically issue and renew TLS certificates for ingress controllers and service mesh mTLS.

### Compliance and Audit Logging

Container platforms should maintain audit logs of all API calls and significant events. Kubernetes maintains an audit log that records who called which API endpoint with which parameters and what the result was. Audit logs can be sent to a centralized log aggregation service (such as Splunk, ELK, or Datadog) for analysis and compliance reporting.

Critical events to log include:

- All API calls to the Kubernetes API (create, read, update, delete operations).
- All changes to RBAC rules, network policies, and security policies.
- All container lifecycle events (creation, deletion, restart).
- All security events detected by threat detection tools.
- All access to secrets, configmaps, and sensitive data.

Compliance frameworks such as PCI-DSS, HIPAA, and SOC 2 require that audit logs be retained for a minimum period (typically 1-3 years) and that access to audit logs be restricted. A best practice is to send audit logs to a separate, isolated system that is not managed by the same team that manages the cluster. This prevents attackers who compromise the cluster from tampering with the audit logs.

---

## 7. Emerging Threats and Advanced Mitigations

### Supply Chain Attacks and Dependency Confusion

Supply chain attacks target the software dependencies that a container image includes. A dependency confusion attack injects a malicious package into a package registry (such as npm, PyPI, or Maven) with the same name as an internal, private package. When a build process installs dependencies, it may install the malicious package from the public registry instead of the private package, if the build process is not configured to prioritize private registries.

To mitigate dependency confusion attacks:

- Configure package managers to check private registries before public registries.
- Use package namespaces: prefix private packages with a unique namespace (e.g., @company/package-name) that is unlikely to conflict with public packages.
- Pin dependency versions to specific versions rather than version ranges, so unexpected versions are not installed.
- Scan dependencies for known vulnerabilities before building the image.

### Lateral Movement and Privilege Escalation

A compromised container typically attempts lateral movement: exploiting the container escape, gaining node access, and then compromising other containers or the Kubernetes control plane. Privilege escalation involves gaining higher levels of access within the container (e.g., from a non-root user to root) or on the node (e.g., from a user to a system administrator).

To mitigate lateral movement:

- Run containers as non-root users, so if a single container is compromised, the attacker does not have root access.
- Use least-privilege RBAC: grant service accounts only the permissions they need.
- Restrict network traffic: use network policies to block traffic between namespaces and restrict egress traffic.
- Use pod security policies to prevent privileged containers and other dangerous configurations.
- Monitor for signs of lateral movement: unauthorized API calls, unexpected network connections, or unusual process creation.

### Data Exfiltration and Persistence

A compromised container may attempt to exfiltrate sensitive data from the cluster or establish persistence so that it can maintain access even if the container is restarted.

To mitigate data exfiltration:

- Use network policies to restrict egress traffic: only allow traffic to destinations that are known to be legitimate.
- Use service mesh encryption to prevent eavesdropping on pod-to-pod communication.
- Audit access to sensitive data: log whenever a container accesses secrets, configmaps, or sensitive files.

To prevent persistence:

- Use ephemeral storage: containers should not store state on disk, so if a container is restarted, any attacker modifications are lost.
- Use immutable infrastructure: rebuild containers rather than patching them, so containers are always in a known-good state.
- Restrict write access to the root filesystem: use read-only root filesystems where possible.
- Monitor for unexpected files or process modifications: if a file is created or modified that should not be there, trigger an alert.

---

## 8. Practical Implementation Checklist

### Development Stage

- Use minimal base images (Alpine, distroless) to reduce the attack surface.
- Scan container images for vulnerabilities in the build pipeline.
- Sign container images and attestations to provide proof of provenance.
- Generate software bill of materials (SBOM) for dependency tracking.
- Run containers as non-root users in the Dockerfile (USER directive).
- Drop unnecessary Linux capabilities (RUN setcap or use seccomp profiles).
- Use multi-stage builds to keep final images small and free of build tools.

### Cluster Configuration

- Enforce Pod Security Standards or Pod Security Policies.
- Enable RBAC and grant least-privilege permissions to service accounts.
- Define network policies to implement zero-trust networking.
- Enable seccomp or AppArmor profiles by default.
- Configure cgroup resource limits to prevent resource exhaustion.
- Enable container image signing and verification at admission time.
- Encrypt secrets at rest in etcd.

### Runtime Monitoring

- Deploy a runtime threat detection tool (Falco, Sysdig, Tracee).
- Monitor for container escapes, privilege escalation, and lateral movement.
- Log all API calls and significant events to a centralized audit system.
- Implement automated responses to detected threats.
- Regularly scan deployed images for newly disclosed vulnerabilities.
- Maintain an incident response playbook for container security incidents.

### Operational Resilience

- Keep the Kubernetes cluster and container runtime up to date with security patches.
- Regularly audit RBAC rules, network policies, and security configurations.
- Conduct security assessments and penetration testing.
- Maintain a runbook for responding to container security incidents.
- Document the threat model and security assumptions for the cluster.

---

## Summary

Container security is a layered problem requiring defense-in-depth across the image, runtime, orchestration, and cluster infrastructure layers. The fundamental invariant is that isolation is only as strong as the weakest primitive in the stack: namespace bypass, cgroup evasion, runtime bugs, or kernel vulnerabilities can all compromise the entire isolation boundary.

Effective container security combines preventive controls (image scanning, pod security standards, RBAC), detective controls (runtime threat detection, audit logging), and responsive controls (automated container termination, network isolation). Zero-trust architecture—assuming no entity is trusted by default and requiring authentication and authorization at every step—provides the strongest posture for protecting containerized applications.

Production environments should enforce signed images, implement network policies, monitor runtime behavior, maintain audit logs, and respond automatically to detected threats. Regular security assessments, vulnerability scanning, and incident response training ensure that the organization can detect and respond to security incidents before they cause damage.
