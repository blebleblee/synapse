# Lesson 1: Mandatory Access Control Foundations

## 1. First-Principles Intuition & Invariants

Every access control system in computing answers the same question: who is allowed to do what to which resource? The answer to that question determines whether a system is fundamentally secure or merely *convenient*. For decades, Unix and its descendants answered that question through Discretionary Access Control, a model so embedded in the culture of open systems that most engineers treat it as a law of nature rather than a design choice. Understanding why DAC is structurally insufficient is not an academic exercise. It is the prerequisite for understanding why SELinux exists at all.

In a DAC system, the owner of a resource controls its access policy. When you create a file on a Linux system, you become its owner, and you decide who can read it, write it, or execute it through the classic `rwxrwxrwx` permission bits and ACLs. The kernel enforces what you declare. This is the discretionary part: access policy is at the discretion of the resource owner. The model is intuitive and workable for a personal workstation, but it contains a structural flaw that scales catastrophically in multi-tenant, multi-process production environments. That flaw is *transitivity of privilege*.

Consider what happens when a privileged daemon, running as root, is compromised through a memory corruption vulnerability. Under DAC, the attacker inheriting that process's credentials inherits *all* of root's privileges across the entire system. The file permission bits the administrator so carefully set are now meaningless. The daemon was trusted by DAC because DAC trusts the user identity, and root is the universal trust anchor. There is no mechanism in pure DAC to say that the NGINX process should read `/etc/nginx/nginx.conf` but should never under any circumstances open `/etc/shadow`, even though both are reachable by root. The policy is coarse-grained at the user level, not the process or object level.

Mandatory Access Control solves this by inverting the trust model. In MAC, the *system administrator* defines global policy, and no process, regardless of its Unix credentials, can grant itself or another subject permissions that the central policy does not explicitly allow. The word "mandatory" is precise: a process running as root cannot discretionarily grant itself access to a type it was not labeled to interact with. The kernel enforces the policy, and the policy is not negotiable at runtime by any userspace process short of a policy reload by a privileged administrator.

SELinux, developed by the NSA and merged into the Linux kernel in 2003, implements MAC through a framework called **Type Enforcement**. The fundamental intuition behind TE is that security-relevant properties of subjects and objects are encoded in *labels*, not identity. A process is not simply "root" or "www-data". It carries a label like `system_u:system_r:httpd_t:s0`. An object like a file carries a corresponding label like `system_u:object_r:httpd_config_t:s0`. The kernel's security server consults a policy database to determine whether the subject's type (`httpd_t`) may perform the requested operation (read, write, execute, connect) on the object's type (`httpd_config_t`). If no rule in the policy explicitly allows the interaction, the kernel denies it and logs the denial. This is the *default-deny* invariant: in SELinux, everything that is not explicitly permitted is forbidden.

The security context, the four-field label that SELinux attaches to every subject and object, is the atomic unit of the entire system. Its structure is `user:role:type:level`. The `user` field is an SELinux user identity, distinct from the Unix UID. The `role` field implements Role-Based Access Control constraints, governing which types a user may transition into. The `type` field is the operative element for most policy decisions under Type Enforcement. For processes, the type is often called a *domain*; for files and other objects, it is simply called a type, though mechanically these are the same construct. The `level` field implements Multi-Level Security using Bell-LaPadula sensitivity labels, expressed in the `sensitivity:category` notation of MLS/MCS policies, with `s0` being the baseline sensitivity in a standard targeted policy deployment.

The invariant that makes TE coherent is *type immutability within a process's lifetime unless a domain transition is explicitly authorized*. When the kernel `exec`s a new binary, it consults the policy for a type transition rule. If the policy declares that a process in domain `initrc_t` executing a binary labeled `httpd_exec_t` should transition to domain `httpd_t`, the new process inherits `httpd_t`. Without such a rule, the domain is preserved from the parent. This transition mechanism is the enforcement point that ensures a web server cannot simply re-exec itself into a more privileged domain: the target binary must have the right label, and the policy must explicitly authorize the specific source-domain-to-target-domain transition for that specific executable type.

For hardware security researchers and embedded engineers, the practical implication of these invariants is significant. When you are auditing a system or building a custom embedded Linux image, the security context is not an abstract concept. It is physically stored in the extended attributes of the filesystem (`security.selinux` xattr), and it is propagated through process creation at the kernel level via the LSM hook architecture. If your filesystem was imaged without preserving xattrs, or if you booted a kernel without SELinux compiled in, every file on that filesystem will carry no label, and SELinux will treat unlabeled objects according to its `unlabeled_t` policy, which is typically maximally restrictive. Understanding this matters deeply for firmware analysis, container rootfs construction, and any workflow where you are transferring filesystems across trust boundaries.

---

## 2. Core Architecture & Mechanics

SELinux does not exist as a monolithic kernel module that intercepts system calls by patching syscall handlers. It operates through the **Linux Security Module** framework, a series of hook functions embedded throughout the kernel at security-relevant decision points. The LSM framework was itself designed to accommodate multiple MAC implementations, and SELinux uses it to register callbacks that the kernel calls before completing any security-sensitive operation: opening a file, creating a socket, sending a signal, loading a kernel module. The architectural relationship between a system call, the LSM hooks, and the SELinux decision engine looks like this:

```
Userspace Process
       │
       │  syscall (e.g., open(2))
       ▼
┌──────────────────────────────────────────────────────┐
│  Kernel VFS Layer                                    │
│   - inode lookup, path resolution                   │
│         │                                            │
│         ▼                                            │
│  DAC Check (uid/gid/permission bits)                 │
│         │  [if DAC denies → EACCES, SELinux skipped]│
│         ▼                                            │
│  LSM Hook: security_inode_permission()               │
│         │                                            │
│         ▼                                            │
│  SELinux Hook Implementation                         │
│    - extract subject SID (from task_security)        │
│    - extract object SID (from inode_security)        │
│    - query AVC (Access Vector Cache)                 │
│         │                                            │
│         ├── HIT: return cached allow/deny            │
│         │                                            │
│         └── MISS: query Security Server              │
│                  │                                   │
│                  ▼                                   │
│         Policy Database (policydb)                   │
│          - type enforcement rules                    │
│          - role transition table                     │
│          - MLS dominance relations                   │
│                  │                                   │
│                  └──▶ AVC: cache result, return      │
└──────────────────────────────────────────────────────┘
       │
       ▼
  Return to Userspace (success) or EACCES/EPERM
```

Every subject (process) and object (file, socket, IPC object, network interface) carries a **Security ID**, or SID. This is a 32-bit integer that is an in-kernel index into the security context table. The full `user:role:type:level` string is the human-readable representation; the SID is what the kernel actually stores in task structures and inode security blobs to minimize memory overhead. The SID is assigned during process creation from the parent's context (or via a type transition rule) and during object creation from the creating process's context (or via a file type transition rule or explicit label). You can inspect the SID-to-context mapping directly:

```bash
# Read the SID-to-context mapping table from selinuxfs
cat /sys/fs/selinux/policy
# More usefully, dump all active SID mappings
cat /proc/self/attr/current          # your shell's security context
cat /proc/1/attr/current             # init/systemd's security context
# Enumerate all running processes with their SELinux context
ps auxZ
# List files with security contexts in a directory
ls -Z /etc/nginx/
# Check the context of a specific binary
stat -c '%C' /usr/sbin/nginx
```

The critical performance component of SELinux is the **Access Vector Cache**. Without it, every permission check would require a full policy database traversal, which would impose an unacceptable latency on file I/O, socket operations, and IPC. The AVC is an in-kernel hash table keyed by `(source_SID, target_SID, target_class)` tuples. Its value is an *access vector*, a bitmask of `allow`ed permissions for that subject/object/class triple. When NGINX reads a configuration file, the kernel computes the AVC key `(httpd_t, httpd_config_t, file)` and retrieves the access vector. If the `read` bit is set in the allowed vector, the operation proceeds without touching the policy database at all.

The AVC has a hit rate that typically exceeds 99% on a running system because the set of unique subject/object/class interactions on a stable workload is small. The misses occur during cold starts, after policy reloads, or when new object types are encountered. A policy reload forces the AVC to flush entirely, which causes a brief spike in policy evaluation latency. On embedded systems with constrained CPUs, this flush can be measurable. The AVC also maintains per-entry statistics accessible via `/sys/fs/selinux/avc/cache_stats`:

```bash
# Inspect AVC hit/miss/lookup statistics
cat /sys/fs/selinux/avc/cache_stats

# Force an AVC cache flush (requires setenforce privilege)
echo 1 > /sys/fs/selinux/avc/cache_threshold

# View current AVC threshold (number of entries before LRU eviction)
cat /sys/fs/selinux/avc/cache_threshold
```

Type Enforcement policy is compiled from human-readable `.te` source files into a binary policy blob using the `checkpolicy` and `semodule_package` toolchain. The compiled binary is loaded into the kernel via `/sys/fs/selinux/load`. The policydb data structure inside the kernel organizes rules into a set of access vector tables indexed by source type, target type, and object class. The object class system is what gives SELinux its granularity beyond filesystem permissions: there are distinct classes for `file`, `dir`, `lnk_file`, `chr_file`, `blk_file`, `fifo_file`, `sock_file`, `tcp_socket`, `udp_socket`, `rawip_socket`, `netif`, `node`, `process`, `capability`, `ipc`, `sem`, `msgq`, `shm`, and dozens more. Each class has its own permission bit vocabulary. The `process` class, for example, includes permissions like `fork`, `transition`, `ptrace`, `signal`, `signull`, `getsched`, and `execmem`.

The domain transition mechanism deserves closer examination because it is the mechanism offensive security practitioners will probe most aggressively. A domain transition occurs when a process executes a new binary. For the transition to succeed, three conditions must simultaneously hold in the policy: the source domain must have `execute` permission on the executable's type, the source domain must have `transition` permission on the target domain in the `process` class, and the executable type must be declared an `entrypoint` for the target domain. This three-way lock prevents an attacker who controls a process in domain `A` from arbitrarily transitioning into domain `B` just by exec-ing the right binary; the policy must explicitly declare all three relationships. You can audit transition rules directly:

```bash
# Show all domain transitions reachable from httpd_t
sesearch --type_trans --source httpd_t /etc/selinux/targeted/policy/policy.*

# Show what httpd_t is allowed to do to httpd_config_t files
sesearch --allow --source httpd_t --target httpd_config_t --class file

# Check if a specific access would be allowed
seinfo -t httpd_t -x  # expand httpd_t type attributes

# Generate a human-readable audit of what is blocked
audit2why < /var/log/audit/audit.log
```

Labeling invariants extend beyond filesystem xattrs. Network packets carry SELinux labels through the SECMARK mechanism, where `iptables`/`nftables` rules stamp matching packets with a security context that SELinux then enforces at the socket level. IPsec security associations can carry MLS labels via the NETLABEL and CIPSO/CALIPSO frameworks. These mechanisms matter for embedded networking appliances where process-to-network-interface policy must be enforced at kernel level without relying on userspace firewall daemons that themselves could be compromised.

---

## 3. High-Performance Optimization & Failure Modes

The most consequential operational failure mode in SELinux deployments is not a denial in enforcing mode, but the quiet accumulation of unreviewed `dontaudit` rules and over-broad `permissive` domain declarations that hollow out the security model while leaving it superficially intact. A domain in permissive mode has SELinux checks applied and denials logged, but the operations are *not blocked*. This is essential for policy development but lethal if permissive domains are left in production policy. Audit this aggressively:

```bash
# List all domains currently in permissive mode
semanage permissive -l

# Check if a specific domain is permissive
seinfo --permissive -x

# Identify dontaudit rules that are suppressing audit messages
# (these hide policy violations from logs)
sesearch --dontaudit --source httpd_t | head -40

# Rebuild policy with dontaudit rules disabled to expose all denials
semodule -DB   # -D disables dontaudit, -B rebuilds and reloads
# After auditing, re-enable dontaudit rules
semodule -B
```

The `semodule -DB` technique is indispensable for security researchers auditing a production system. By disabling `dontaudit` rules, every access vector that the policy silently ignores becomes visible in the audit log. On a heavily customized enterprise system, this often reveals domains with far more implicit access than their stated purpose requires, which is the SELinux equivalent of finding processes with excessive Linux capabilities.

AVC performance degrades under three specific conditions: extremely high process churn (thousands of short-lived processes per second, common in container orchestration workloads), policy reloads on systems with large numbers of active SID pairs, and deeply nested MLS category sets that make SID comparison expensive. For embedded engineers building deterministic real-time systems, the AVC threshold is tunable. The default cache size is 512 entries, and on a system with a small, well-defined policy and a stable process set, this is more than sufficient. For systems under high churn, increasing the threshold reduces miss rates at the cost of kernel memory:

```bash
# Check current cache size
cat /sys/fs/selinux/avc/cache_threshold

# Increase AVC cache to 2048 entries (must be root with mac_admin capability)
echo 2048 > /sys/fs/selinux/avc/cache_threshold
```

For offensive practitioners, the AVC miss storm during policy reload is a potential timing window. While the kernel is re-evaluating permissions from the policy database, the system is operating under a brief window of elevated latency and, in edge cases involving race conditions in LSM hook ordering, potential TOCTOU conditions. These are not vulnerabilities in SELinux itself, but they are the kind of transient state that matters when you are modeling the attack surface of a hardened system under active administrative operation.

A more fundamental failure mode is *context mismatch after filesystem restore*. When a filesystem backup is restored from an archive that did not preserve extended attributes, all SELinux labels are lost. Files revert to `unlabeled_t`, and the system's confined services immediately begin generating AVC denials. The standard recovery path is a full filesystem relabel, triggered by creating `/.autorelabel` and rebooting, which causes the init system to run `restorecon -R /` against the file contexts database. On large filesystems this takes minutes; on embedded eMMC with millions of inodes, it can be prohibitively slow. The engineering mitigation for embedded targets is to bake correct labels into the filesystem image at build time using the `mkfs.ext4 -E root_owner=` and SELinux-aware image generation tools like `mkosi` or Yocto's `IMAGE_FSTYPES` with SELinux context preservation:

```bash
# Manually restore contexts for a specific directory tree
restorecon -Rv /etc/nginx/

# Check what context a file *should* have per policy (without changing it)
matchpathcon /etc/nginx/nginx.conf

# Compare current labels against policy-specified labels for a directory
restorecon -Rnv /var/www/html/   # -n = dry run, -v = verbose

# Relabel a single process's object (file) to match the policy specification
chcon -t httpd_sys_content_t /var/www/html/index.html
# Note: chcon changes are not persistent across full relabels; use semanage fcontext for persistence
semanage fcontext -a -t httpd_sys_content_t "/var/www/html(/.*)?"
restorecon -Rv /var/www/html/
```

The distinction between `chcon` and `semanage fcontext` followed by `restorecon` is an operational invariant that trips up engineers working under time pressure. `chcon` directly modifies the xattr on the inode, but it has no memory in the policy database. When `restorecon` next runs, whether during boot relabeling, automated policy enforcement, or a manual call by an administrator, the `chcon` label will be overwritten by the policy-specified context. The durable path is always `semanage fcontext` to record the rule and `restorecon` to apply it.

For hardware security researchers doing firmware extraction and analysis, the SELinux label state of a filesystem image is a first-order indicator of security posture. An embedded Linux firmware where all files carry `system_u:object_r:unlabeled_t:s0` tells you immediately that SELinux was either never enforcing or that the image was built without xattr support in the packaging toolchain. An image with correctly labeled system binaries but `unlabeled_t` on application binaries is a partial deployment, suggesting MAC enforcement stops at the system boundary and application processes run in a confined but loosely typed domain. The most hardened posture you will find in production embedded systems is a fully labeled image with every application binary assigned its own type, every writable data directory labeled with a type distinct from the executable type, and no `permissive` domain declarations in the loaded policy. This configuration provides the strongest guarantee: a compromised application process cannot read executable memory from another domain, cannot write to system configuration directories, and cannot signal processes outside its declared signal permission set, even if the attacker achieves arbitrary code execution within the process's address space.

The architectural invariant to internalize before proceeding further in this curriculum is this: SELinux's security guarantee is only as strong as the completeness of its labeling and the tightness of its policy. A perfect MAC implementation on a system with unlabeled files, permissive domains, or wildcard type attributes is not a hardened system. It is a paperwork system that provides audit logs of violations it does not prevent. The engineering discipline of SELinux is not in learning the syntax of policy modules; it is in building and maintaining the invariant that every subject and every object on the system carries a label, and that every label interaction in production has been explicitly reviewed and authorized.
