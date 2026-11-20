# Lesson 4: Multi-Container Orchestration, Security Boundaries, Production Hardening

## 1. First-Principles Intuition & Invariants

The evolution from single-container experimentation to production-grade multi-container systems represents a fundamental shift in reasoning about distributed process coordination. While a lone container encapsulates a single process boundary with its own filesystem namespace and network stack, real-world applications demand intricate choreography: a web frontend must discover its API backend, which in turn requires access to persistent database state, all while respecting strict security boundaries that prevent lateral movement during compromise.

Docker Compose emerged as a declarative orchestration layer that models multi-container applications as directed acyclic graphs of service dependencies. Unlike imperative scripts that launch containers in sequence, Compose interprets YAML manifests as desired-state specifications and reconciles them against the current runtime topology. This reconciliation model follows a single invariant: every service declaration establishes a vertex in the dependency graph, and every `depends_on` clause creates a directed edge that constrains the partial ordering of container lifecycle operations. When you invoke `docker-compose up`, the engine performs a topological sort to determine the legal startup sequence, then proceeds to create networks, volumes, and containers in dependency order while respecting parallel launch opportunities where no ordering constraint exists.

Service discovery within a Compose network leverages Docker's embedded DNS resolver, which runs as a userspace process inside each container's network namespace. When a container queries a service name like `api` or `database`, the resolver intercepts the DNS A or AAAA record request, consults the Docker daemon's internal service registry, and returns the IP address of the target container's virtual ethernet interface. This design choice—embedding DNS resolution rather than relying on `/etc/hosts` static mappings—enables dynamic topology changes: containers can restart with new IP addresses, and the DNS resolver will transparently update its responses without requiring filesystem synchronization across namespaces. The resolver listens on `127.0.0.11:53` within each container's network namespace, a detail that becomes critical when debugging resolution failures or implementing custom DNS policies.

Security boundaries in production Docker deployments rest on three concentric layers of isolation. The outermost layer is the Linux kernel namespace subsystem, which partitions global system resources—process IDs, mount points, network stacks, IPC message queues, UTS hostnames, and user ID mappings—into isolated views. Within this foundation, cgroups enforce resource limits and accounting, preventing a single container from monopolizing CPU cycles, memory pages, or I/O bandwidth. The innermost layer consists of Mandatory Access Control frameworks like AppArmor and SELinux, which implement policy-driven restrictions on system call arguments and filesystem access patterns regardless of the process's user ID or capabilities.

AppArmor profiles define state machines that govern process behavior through allow-lists of permitted operations. When a container launches with an AppArmor profile attached, the kernel's Linux Security Module hooks intercept every system call and evaluate it against the profile's rule set before allowing execution to proceed. A typical Docker default profile permits common operations like reading from `/proc` and `/sys`, executing binaries from the container's filesystem, and establishing network connections, but denies dangerous operations like mounting filesystems, loading kernel modules, or accessing raw block devices. The profile is enforced at the kernel level through LSM hooks that execute in the context of the calling process, meaning even a root user inside the container cannot bypass the restrictions without first escaping the container boundary entirely.

Seccomp, the secure computing mode framework, operates at a lower level of abstraction by filtering individual system calls based on their opcode and argument values. While AppArmor evaluates high-level operations like "open this file" or "bind this socket," seccomp inspects the raw `syscall` instruction's register state before the kernel dispatches to the appropriate handler function. A seccomp profile consists of a Berkeley Packet Filter program—a sequence of instructions in the same architecture-neutral bytecode format used for network packet filtering—that returns ALLOW, KILL, or ERRNO verdicts for each intercepted system call. Docker's default seccomp profile blacklists approximately 44 system calls out of the roughly 330 available on x86-64 Linux, including dangerous operations like `keyctl` for kernel key management, `add_key` and `request_key` for cryptographic material, and architecture-specific calls like `modify_ldt` that can manipulate process memory layout descriptors.

The shift to rootless containers represents a fundamental rearchitecting of the container runtime's privilege model. Traditional Docker requires the daemon to run as root because creating namespaces, configuring cgroups, and manipulating network interfaces are privileged operations. Rootless mode exploits user namespaces—a relatively recent kernel feature that allows unprivileged processes to create nested UID mappings—to delegate these operations to a daemon running as an ordinary user. Inside the user namespace, the daemon process believes it is root (UID 0), but the kernel's user namespace implementation transparently maps this to an unprivileged UID in the parent namespace. This mapping introduces constraints: the rootless daemon cannot bind to privileged ports below 1024 without additional configuration, cannot manipulate the host's network interfaces, and faces reduced cgroup control depending on the kernel's cgroup v2 delegation policies.

Image signing and supply chain integrity build cryptographic provenance chains from source code repositories through CI pipelines to production registries. Docker Content Trust, Docker's implementation of The Update Framework (TUF), establishes a hierarchy of signing keys where offline root keys delegate authority to timestamp, snapshot, and targets keys with limited validity periods. When a developer pushes an image with content trust enabled, the Docker client generates a cryptographic hash of each layer's content, signs the collection of hashes with the targets key, and publishes both the image layers and the detached signature to the registry. Clients configured to require content trust will refuse to pull images unless they can verify the signature chain back to a trusted root key, and they will detect tampering by comparing the registry's layer digests against the signed manifest's recorded values.

The security invariant underlying all these mechanisms is defense in depth through layered isolation: if an attacker compromises the application process, they still face namespace boundaries; if they escape the namespace, AppArmor and seccomp policies constrain their system call surface; if they bypass those policies, user namespace UID mapping prevents host filesystem tampering; if they achieve host access, image signing reveals supply chain compromise before the image enters production. Each layer assumes the failure of layers above it, creating a security architecture resilient to single-point failures.

## 2. Core Architecture & Mechanics

Docker Compose orchestrates multi-container topologies through a declarative YAML schema that the Compose engine parses into an internal directed graph structure. Each service definition becomes a vertex annotated with resource requirements, environment variables, volume mounts, and network attachments. Dependency edges created by `depends_on` clauses establish partial ordering constraints that the engine respects during both startup and shutdown sequences. Consider a canonical three-tier application manifest:

```yaml
version: '3.8'

services:
  database:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_USER: appuser
      POSTGRES_DB: production
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    secrets:
      - db_password
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/run/postgresql

  api:
    build:
      context: ./api
      dockerfile: Dockerfile
      args:
        RUST_VERSION: 1.75
    environment:
      DATABASE_URL: postgresql://appuser@database:5432/production
      RUST_LOG: info
      RUST_BACKTRACE: 1
    secrets:
      - db_password
      - api_signing_key
    networks:
      - backend
      - frontend
    depends_on:
      database:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 15s
      timeout: 3s
      retries: 3
    security_opt:
      - no-new-privileges:true
      - apparmor=docker-default
      - seccomp=./profiles/api-seccomp.json
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.production
    environment:
      API_ENDPOINT: http://api:8080
      NODE_ENV: production
    networks:
      - frontend
    depends_on:
      api:
        condition: service_healthy
    ports:
      - "443:8443"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8443/health"]
      interval: 20s
      timeout: 5s
      retries: 3
    security_opt:
      - no-new-privileges:true
      - apparmor=docker-default
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache/nginx

networks:
  backend:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.28.0.0/16
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.29.0.0/16

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/storage/postgres

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_signing_key:
    file: ./secrets/api_signing_key.pem
```

The dependency graph encoded in this manifest establishes a strict ordering: the database service must reach a healthy state before the API service starts, and the API must achieve health before the frontend launches. The `condition: service_healthy` constraint transforms a simple dependency edge into a health-gated edge, where Compose polls the dependent service's health check endpoint before proceeding with the next stage of the topology. The health check mechanism itself deserves detailed examination. Docker executes the health check command inside the container's namespace at the specified interval, captures its exit code, and updates the container's health status metadata accordingly. A status of `starting` persists during the `start_period` window, during which failed checks do not count against the `retries` limit. Once the start period elapses or the first successful check occurs, the status transitions to `healthy`. Subsequent failures decrement the retry counter, and when it reaches zero, the status becomes `unhealthy`. This state machine enables sophisticated orchestration patterns where downstream services only launch after upstream dependencies have passed their health checks, preventing cascading failures from race conditions during startup.

Service discovery operates through Docker's bridge network driver, which creates a virtual switch in the kernel's network stack and attaches each container's `veth` interface to it. When Compose creates the `backend` and `frontend` networks, the daemon invokes the bridge driver to allocate new bridge interfaces on the host, assigns them IP addresses from the specified subnets, and configures iptables rules to enable masquerading for outbound traffic. The `internal: true` flag on the backend network instructs the bridge driver to omit the masquerading rules, effectively isolating that network from external connectivity. Containers attached to the backend network can communicate with each other through the bridge but cannot reach the internet or the host's physical interfaces, implementing network segmentation at the packet routing layer.

The embedded DNS resolver that powers service discovery listens on `127.0.0.11:53` within each container's network namespace. This special address is injected into the container's `/etc/resolv.conf` during creation. When the API service issues a DNS query for `database`, the kernel routes the UDP packet to the resolver, which consults the Docker daemon's internal registry mapping service names to IP addresses. The daemon maintains this registry in memory, updating it whenever containers join or leave networks. For multi-replica services, the resolver returns multiple A records in round-robin fashion, implementing client-side load balancing. The resolver also supports reverse DNS lookups, allowing containers to query IP addresses and receive service names, which proves invaluable when analyzing packet captures or debugging connection errors.

Secrets management through Docker's secrets abstraction layers cryptographic material handling atop the existing volume mount mechanism. When Compose processes the `secrets` top-level key, it reads the specified files from the host filesystem, computes their content hashes, and registers them with the daemon. At container creation time, the daemon mounts each secret as a read-only tmpfs filesystem at `/run/secrets/<secret_name>` inside the container. This approach keeps secrets out of environment variables, which are visible to all processes via `/proc/<pid>/environ`, and out of the container's writable layer, which could be committed to an image and inadvertently leaked. The tmpfs mount ensures secrets reside only in memory, never touching persistent storage where forensic recovery might be possible after deletion. Applications read secrets by opening files in `/run/secrets`, a pattern that works seamlessly across development and production environments with appropriate secret provisioning differences handled externally.

Resource limits defined in the `deploy.resources` section translate directly to cgroup constraints. When the daemon creates the API container with a memory limit of 512 megabytes, it writes this value to the `memory.max` file in the container's dedicated cgroup directory under the cgroup v2 hierarchy, typically mounted at `/sys/fs/cgroup`. The kernel's memory controller then tracks all pages charged to this cgroup, including the process's resident set, page cache, and kernel allocations like network buffers. When the accumulated charge approaches the limit, the memory reclaim logic attempts to free pages by evicting clean cache pages and swapping out anonymous pages. If reclaim cannot free sufficient memory, the OOM killer selects a victim process within the cgroup based on its `oom_score_adj` value and terminates it with a SIGKILL. The CPU limit similarly writes to `cpu.max`, which specifies a quota (in microseconds of CPU time) and a period (typically 100,000 microseconds). A limit of 1.0 CPU translates to a quota equal to the period, allowing the container to consume one full CPU's worth of time per period. The kernel's Completely Fair Scheduler enforces this by throttling the cgroup when it exhausts its quota, forcing its processes to sleep until the next period begins.

AppArmor profile attachment occurs at container creation through the `security_opt` directive. The `apparmor=docker-default` value instructs the daemon to load the default Docker AppArmor profile and apply it to the container's initial process. This profile resides at `/etc/apparmor.d/docker-default` on most systems and consists of allow rules expressed in AppArmor's policy language. A representative fragment:

```text
profile docker-default flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  network,
  capability,
  file,
  umount,

  deny @{PROC}/* w,
  deny @{PROC}/sys/fs/** wklx,
  deny @{PROC}/sys/kernel/shm* wklx,
  deny @{PROC}/sysrq-trigger rwklx,
  deny @{PROC}/mem rwklx,
  deny @{PROC}/kmem rwklx,

  deny /sys/[^f]*/** wklx,
  deny /sys/f[^s]*/** wklx,
  deny /sys/fs/[^c]*/** wklx,
  deny /sys/fs/c[^g]*/** wklx,
  deny /sys/fs/cg[^r]*/** wklx,
  deny /sys/firmware/** rwklx,
  deny /sys/kernel/security/** rwklx,

  deny mount,
  deny pivot_root,
  deny remount,
  deny umount,

  ptrace (trace,read) peer=docker-default,
}
```

The profile's `attach_disconnected` flag allows AppArmor to enforce the profile even when the process's initial profile was unconfined, which occurs when the daemon itself runs unconfined. The `mediate_deleted` flag ensures AppArmor continues mediating access to files that have been deleted from the filesystem, preventing processes from escaping confinement by unlinking files and manipulating orphaned inodes. The deny rules explicitly block writes to sensitive `/proc` and `/sys` locations that could allow privilege escalation or information disclosure, while the trailing deny rules prevent mount operations that could be used to overlay new filesystems atop the namespace's mount tree.

Seccomp filtering provides finer-grained control by intercepting system calls before the kernel processes them. A custom seccomp profile for the API service might restrict the system call surface to only those required for a typical web server:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_X86",
    "SCMP_ARCH_X32"
  ],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "arch_prctl", "bind", "brk",
        "capget", "capset", "chdir", "chmod", "chown", "clone",
        "close", "connect", "dup", "dup2", "dup3", "epoll_create",
        "epoll_create1", "epoll_ctl", "epoll_wait", "epoll_pwait",
        "execve", "exit", "exit_group", "faccessat", "fadvise64",
        "fallocate", "fchdir", "fchmod", "fchmodat", "fchown", "fchownat",
        "fcntl", "fdatasync", "flock", "fork", "fstat", "fstatfs",
        "fsync", "ftruncate", "futex", "getcwd", "getdents", "getdents64",
        "getegid", "geteuid", "getgid", "getgroups", "getpeername",
        "getpgrp", "getpid", "getppid", "getpriority", "getrandom",
        "getresgid", "getresuid", "getrlimit", "getrusage", "getsid",
        "getsockname", "getsockopt", "gettid", "gettimeofday", "getuid",
        "getxattr", "ioctl", "kill", "lchown", "lgetxattr", "link",
        "linkat", "listen", "lseek", "lstat", "madvise", "memfd_create",
        "mkdir", "mkdirat", "mknod", "mknodat", "mlock", "mlock2",
        "mlockall", "mmap", "mprotect", "mremap", "msync", "munlock",
        "munlockall", "munmap", "nanosleep", "newfstatat", "open",
        "openat", "pause", "pipe", "pipe2", "poll", "ppoll", "prctl",
        "pread64", "preadv", "preadv2", "prlimit64", "pselect6",
        "pwrite64", "pwritev", "pwritev2", "read", "readahead",
        "readlink", "readlinkat", "readv", "recvfrom", "recvmsg",
        "recvmmsg", "rename", "renameat", "renameat2", "restart_syscall",
        "rmdir", "rt_sigaction", "rt_sigpending", "rt_sigprocmask",
        "rt_sigqueueinfo", "rt_sigreturn", "rt_sigsuspend", "rt_sigtimedwait",
        "rt_tgsigqueueinfo", "sched_getaffinity", "sched_setaffinity",
        "sched_getparam", "sched_get_priority_max", "sched_get_priority_min",
        "sched_getscheduler", "sched_setscheduler", "sched_yield",
        "seccomp", "select", "semctl", "semget", "semop", "semtimedop",
        "send", "sendfile", "sendmmsg", "sendmsg", "sendto", "setfsgid",
        "setfsuid", "setgid", "setgroups", "setitimer", "setpgid",
        "setpriority", "setregid", "setresgid", "setresuid", "setreuid",
        "setrlimit", "setsid", "setsockopt", "setuid", "shmat", "shmctl",
        "shmdt", "shmget", "shutdown", "sigaltstack", "socket", "socketpair",
        "splice", "stat", "statfs", "symlink", "symlinkat", "sync",
        "sync_file_range", "syncfs", "sysinfo", "tee", "tgkill",
        "time", "timer_create", "timer_delete", "timer_getoverrun",
        "timer_gettime", "timer_settime", "timerfd_create", "timerfd_gettime",
        "timerfd_settime", "times", "tkill", "truncate", "umask",
        "uname", "unlink", "unlinkat", "utime", "utimensat", "utimes",
        "vfork", "wait4", "waitid", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

The `defaultAction` of `SCMP_ACT_ERRNO` causes any system call not explicitly allowed to return `-EPERM` to the calling process, preventing execution without crashing the container. The architecture array restricts the profile to x86-64 and related architectures, preventing abuse of compatibility layers that might allow 32-bit system calls to bypass filtering. The allowed system calls represent a carefully curated set that permits typical userspace operations—file I/O, network communication, memory management, process creation, and signal handling—while blocking dangerous operations like `ptrace` for process debugging, `reboot` for system control, `mount` for filesystem manipulation, and `bpf` for loading eBPF programs.

Capability dropping through `cap_drop: ALL` and selective re-addition with `cap_add: NET_BIND_SERVICE` implements least-privilege security at the Linux capabilities granularity level. Capabilities partition the monolithic root privilege into approximately 40 distinct capabilities like `CAP_NET_ADMIN` for network configuration, `CAP_SYS_MODULE` for kernel module loading, and `CAP_SYS_PTRACE` for process tracing. By default, Docker grants containers a reduced set of capabilities that excludes the most dangerous ones. Dropping all capabilities with `cap_drop: ALL` creates a maximally restricted environment where even a root process cannot perform privileged operations, then selectively adding `CAP_NET_BIND_SERVICE` allows binding to ports below 1024 without granting broader network administration rights. The kernel checks capabilities at every privileged operation, consulting the process's effective capability set stored in the task struct. A process attempting a privileged operation without the necessary capability receives an `-EPERM` error, just as if it were running as a non-root user.

Rootless container operation restructures the entire daemon architecture to avoid requiring root privileges. The rootless daemon runs as an ordinary user and creates a user namespace as its foundational isolation mechanism. Inside this namespace, the daemon's UID 0 maps to an unprivileged UID in the parent namespace, typically the user's actual UID plus an offset. Child namespaces inherit this mapping, so containers believe they are running as various UIDs, but the kernel remaps all filesystem and IPC operations according to the user namespace's UID mapping table. This table resides in `/proc/<pid>/uid_map` and `/proc/<pid>/gid_map` and must be configured before the namespace can create child processes. A typical mapping might allocate a range of 65536 subordinate UIDs starting at 100000, allowing the rootless daemon to map container UIDs 0-65535 to host UIDs 100000-165535. The kernel enforces that these subordinate ranges do not overlap with other users' allocations, preventing UID collision attacks where one user's container could impersonate another user's processes.

Network connectivity in rootless mode requires special handling because unprivileged users cannot create bridge interfaces or manipulate iptables rules. Docker rootless employs `slirp4netns`, a user-mode TCP/IP stack that runs as a separate process and provides NAT-style connectivity to containers. The rootless daemon creates a TAP interface inside the container's network namespace and connects it to the `slirp4netns` process via a Unix socket. The `slirp4netns` process forwards packets between the TAP interface and the host's network stack, translating addresses and ports to make it appear as if the container's connections originate from the user running the daemon. This approach incurs performance overhead compared to kernel-mode bridge networking but enables container networking without privileged access. Port publishing works similarly: `slirp4netns` listens on a high-numbered port on the host, which the daemon can bind without privilege, and forwards incoming connections into the container's namespace.

Image signing through Docker Content Trust establishes a cryptographic chain of custody from image build to deployment. The trust model derives from The Update Framework, which defines four key types: root keys that establish the trust anchor, targets keys that sign image manifests, snapshot keys that sign the collection of all targets at a point in time, and timestamp keys that sign the snapshot to prevent freeze attacks where an attacker serves stale metadata. The key hierarchy enables key rotation without requiring clients to update their trust anchors: if a targets key becomes compromised, the root key can sign a new delegation that revokes the old targets key and establishes a new one. Clients need only possess the root key's public fingerprint to verify the entire chain.

When a developer pushes an image with content trust enabled, the Docker client performs a multi-step protocol. First, it computes the SHA-256 digest of each layer by reading the compressed tar archive and feeding it through the hash algorithm. These digests form a content-addressable index where the digest uniquely identifies the layer's contents. Second, the client constructs a manifest that lists all layer digests along with the image's configuration blob digest. Third, it signs this manifest with the targets key using RSA or ECDSA signature algorithms. Fourth, it uploads both the unsigned image layers and the detached signature to the registry, storing signatures in a separate namespace from the image blobs themselves. The registry stores signatures in the notary service, a separate API endpoint dedicated to managing trust metadata.

Pulling an image with content trust verification reverses this protocol. The Docker client first fetches the trust metadata from the notary service, retrieves the signed manifest, and verifies the signature chain back to the locally stored root key fingerprint. Only after signature verification succeeds does the client request the actual image layers from the registry. As each layer downloads, the client recomputes its SHA-256 digest and compares it against the digest recorded in the signed manifest. If any digest mismatches, indicating tampering or corruption, the client aborts the pull and reports a verification failure. This ensures that every byte of every layer matches exactly what the original signer intended, preventing man-in-the-middle attacks, compromised registries, or accidental corruption from serving malicious content.

## 3. High-Performance Optimization & Failure Modes

Optimizing multi-container orchestration begins with understanding the startup sequence's critical path through the dependency graph. Health checks introduce latency by design, forcing downstream services to wait until upstream dependencies pass their health criteria. Tuning the health check parameters requires balancing rapid failure detection against false positives from transient startup delays. The `start_period` parameter provides a grace window during which health check failures do not count against the retry limit, accommodating services with long initialization phases like database schema migrations or cache warm-up routines. Setting this window too short causes premature health check failures that reset the retry counter, while setting it too long delays detecting genuine failures. Production deployments often set `start_period` to the 95th percentile of observed startup times, measured from container creation to the first successful health check, then add a 20 percent margin for variability.

The health check interval and timeout parameters similarly require tuning based on the service's expected response latency and failure detection requirements. Aggressive intervals like five seconds provide rapid failure detection but increase CPU and network overhead from frequent health check executions. Conservative intervals like 60 seconds reduce overhead but delay failure detection, potentially allowing a failed service to process requests for nearly a minute before orchestration systems react. The timeout parameter must exceed the service's worst-case health check response time under load, including queuing delays from thread pool saturation, to avoid false negatives. Monitoring health check execution times during load testing reveals the appropriate timeout value, typically set to the 99th percentile plus a small buffer.

Network segmentation through multiple Compose networks enables defense-in-depth topology design where compromised services cannot pivot to unrelated systems. The `internal: true` flag on the backend network prevents database containers from initiating outbound connections to the internet, blocking data exfiltration attempts that would otherwise use the container's network stack to establish reverse shells or tunnel data through DNS queries. Containers require explicit attachment to multiple networks to communicate across network boundaries, creating an explicit topology map that security teams can audit. This design prevents lateral movement: an attacker who compromises the frontend service gains access only to the frontend network and cannot directly reach the database because no network path exists between the frontend and backend networks. The API service, attached to both networks, acts as a controlled bridge that enforces application-level access control.

DNS resolver caching within the embedded resolver improves service discovery performance by eliminating repeated registry lookups for frequently queried names. The resolver maintains an in-memory cache with a default TTL of 600 seconds, storing both positive and negative responses. Positive responses cache the IP address mappings, while negative responses cache NXDOMAIN results indicating that a service name does not exist. Cache invalidation occurs automatically when containers join or leave networks, ensuring that the resolver never serves stale mappings after topology changes. However, the cache persists across container restarts if the container retains the same IP address, potentially serving outdated entries if a service's configuration changes without triggering network operations. Forcing cache invalidation requires restarting the resolver itself, which occurs only when the Docker daemon restarts or when all containers detach from a network.

Volume performance critically impacts database and stateful service workloads. Bind mounts configured through the `driver_opts` section with `type: none` and `o: bind` allow precise control over the backing filesystem and mount options. Production databases typically require XFS or ext4 filesystems with specific mount options like `noatime` to disable access time updates, which cause write operations on every read and degrade throughput on high-IOPS workloads. The `device` path should point to a dedicated disk or LVM logical volume rather than a subdirectory of the root filesystem to isolate I/O contention and enable independent tuning of filesystem parameters. Direct-attached NVMe storage provides the lowest latency and highest throughput, while networked storage like NFS introduces additional latency from the network round-trip and the remote filesystem's locking semantics.

Read-only root filesystems combined with tmpfs mounts for ephemeral writable directories create an immutable infrastructure pattern that prevents persistent compromise. An attacker who achieves code execution inside a container with a read-only root cannot install backdoors, modify configuration files, or plant webshells that would survive container restarts. The `read_only: true` directive instructs the container runtime to mount all non-volume filesystems with the read-only flag, causing write attempts to fail with `-EROFS`. Applications require writable directories for temporary files, lock files, and runtime caches, which the `tmpfs` directive provides by mounting memory-backed filesystems at the specified paths. These tmpfs mounts exist only in memory and vanish when the container stops, ensuring that any malicious modifications disappear at the next restart. Sizing tmpfs mounts correctly requires profiling the application's temporary storage usage under peak load to avoid out-of-memory conditions when the tmpfs grows beyond available memory.

Secrets rotation patterns require coordination between external secret stores and container restarts. Docker's file-based secrets persist for the container's lifetime, preventing runtime updates when secrets change. Production systems typically implement secrets rotation by updating the secret file on the host, then performing a rolling restart of affected services through `docker-compose up --force-recreate --no-deps <service>`. The `--no-deps` flag prevents restarting dependent services, confining the disruption to the target service alone. More sophisticated rotation schemes integrate with external secrets managers like HashiCorp Vault or AWS Secrets Manager by running a sidecar container that fetches secrets from the external API and writes them to a shared volume, then signals the main application container to reload its configuration. This pattern avoids container restarts but requires application support for configuration reloading, typically through signal handling where the application catches SIGHUP and re-reads its configuration files.

Resource limit enforcement through cgroups can produce counterintuitive behavior when limits interact with application concurrency models. A CPU limit of 1.0 CPU allows the container to consume one full CPU's worth of time per scheduling period, but if the application spawns eight worker threads, each thread receives approximately 12.5 percent of a CPU's time, causing the entire application to appear slower than a single-threaded version despite theoretical parallelism. The kernel's throttling mechanism pauses all processes in the cgroup when the quota exhausts, regardless of which specific threads consumed the time. Applications optimized for high-CPU environments may need tuning for CPU-limited containers, often by reducing thread pool sizes to match the available CPU quota rather than the number of physical cores.

Memory limits interact with the kernel's memory reclaim and OOM killing logic in subtle ways. When a container approaches its memory limit, the kernel attempts to reclaim memory by evicting clean pages from the page cache and swapping out anonymous pages if swap is enabled. Page cache eviction reduces I/O performance because subsequent reads must fetch data from the underlying storage rather than from memory. Swap eviction introduces latency spikes when swapped-out pages are accessed and must be read back from disk. Disabling swap with `--memory-swap` equal to `--memory` prevents swap-induced latency spikes but increases OOM kill risk because the kernel cannot use swap as a relief valve. Monitoring the `memory.stat` file in the container's cgroup reveals detailed breakdowns of memory usage across different categories, enabling precise diagnosis of whether limit exhaustion stems from the working set size, page cache bloat, or kernel allocations.

AppArmor profile customization enables tightening security boundaries beyond the default profile by analyzing the application's actual system call patterns and filesystem access. Tools like `aa-genprof` generate profiles by running the application under observation mode, recording all operations, then converting the observed behavior into policy rules. This learning phase requires exercising all code paths through comprehensive test suites to avoid creating overly restrictive profiles that break rarely executed features. The resulting profile explicitly lists every file path the application accesses, every network operation it performs, and every capability it requires. Deploying custom profiles requires loading them into the kernel with `apparmor_parser` and referencing the profile name in the `security_opt` directive. Profile violations appear in the kernel audit log at `/var/log/audit/audit.log` or the system journal, enabling post-deployment monitoring to detect both security violations and profile bugs.

Seccomp profile debugging follows a similar workflow of observation and refinement. Running a container without seccomp restrictions while tracing system calls with `strace` reveals the complete set of system calls the application invokes during normal operation. Converting this trace into a seccomp profile requires careful analysis to distinguish between essential calls and incidental calls that occur only during startup or error paths. The default action of `SCMP_ACT_ERRNO` provides safer failure modes than `SCMP_ACT_KILL`, which terminates the process immediately without opportunity for error handling or logging. However, `SCMP_ACT_ERRNO` can cause difficult-to-diagnose failures when applications do not properly check system call return values and proceed with stale data after a blocked call. Testing seccomp profiles under failure injection scenarios ensures that blocked system calls produce observable errors rather than silent data corruption.

Rootless container limitations around port binding below 1024 can be addressed through several strategies. The `sysctl net.ipv4.ip_unprivileged_port_start` kernel parameter lowers the privileged port boundary, allowing unprivileged processes to bind to ports above the configured threshold. Setting this to 80 enables rootless containers to bind to HTTP's standard port without requiring capabilities. Alternatively, running a reverse proxy like nginx on the host as a privileged service and forwarding traffic to high-numbered ports in rootless containers maintains the separation of concerns while accommodating standard port expectations. The proxy can perform TLS termination, request routing, and rate limiting before forwarding to backend containers, consolidating security-sensitive operations in a single auditable component.

Image layer caching optimization reduces build times and registry bandwidth by maximizing cache hit rates across builds. Dockerfile instructions execute sequentially, and Docker caches the resulting layer after each instruction. Subsequent builds reuse cached layers until an instruction's inputs change, then invalidate all downstream layers. Placing frequently changing operations like application code copies after infrequently changing operations like dependency installation maximizes cache reuse. Multi-stage builds extend this principle by separating build-time dependencies from runtime artifacts, copying only the compiled binaries into the final image while discarding source code, compilers, and development tools. This reduces final image size and attack surface while maintaining efficient build caching across the stages.

Content trust verification failures in production registries require careful diagnosis to distinguish between legitimate security events and operational issues. Signature verification can fail due to clock skew between the client and notary service causing timestamp validation errors, expired snapshot or timestamp keys requiring rotation, or genuine tampering attempts. Monitoring notary service metrics like signature verification latency and failure rates provides early warning of operational issues before they impact deployments. Implementing automated key rotation schedules prevents expiration-related outages by rotating targets and snapshot keys before their validity periods expire, while keeping the root key offline in hardware security modules or secure enclaves to prevent compromise.

Supply chain security extends beyond image signing to include build environment integrity and base image provenance. Reproducible builds ensure that compiling the same source code twice produces bit-for-bit identical binaries, allowing independent verification that a published image matches its claimed source. Tools like Buildpacks and Nix enable reproducible builds by controlling all inputs including compiler versions, library versions, and build flags. Base image scanning with tools like Trivy or Clair detects known vulnerabilities in the packages installed in base images, enabling proactive patching before deployment. Regularly rebuilding images from updated base images prevents drift where long-lived images accumulate unpatched vulnerabilities while newer images benefit from security updates. Implementing automated rebuild pipelines that trigger on base image updates or CVE database updates ensures that security patches propagate to production images within hours rather than weeks or months.
