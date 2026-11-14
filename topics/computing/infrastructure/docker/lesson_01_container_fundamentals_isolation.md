# Lesson 1: Container Fundamentals, Namespaces, Control Groups

## 1. First-Principles Intuition & Invariants

The story of containers begins not with Docker, not with dotCloud, and not even with the cgroups patch that Rohith Srinivas and Paul Menage submitted to Linus Torvalds in 2007. It begins with a philosophical problem that has shadowed multi-tenant computing since the earliest timesharing systems: how do you run multiple, mutually distrusting workloads on a single machine without letting them see, starve, or destroy each other?

The classical answer was the virtual machine. A hypervisor interposes a full hardware abstraction layer between guest and host, giving each guest its own emulated CPU, memory controller, NIC, and storage bus. The isolation is genuine and deep — a compromised guest kernel cannot read host memory without exploiting a hypervisor vulnerability — but the cost is proportional to the depth of that abstraction. Every VM boots a full kernel, initializes a complete device model, and wastes hundreds of megabytes on duplicate OS images. When you need to pack two hundred microservices onto a single host, the VM model breaks down economically and operationally.

The container model answers with a different invariant: rather than virtualizing hardware beneath the kernel, isolate processes *within* the same running kernel using the kernel's own namespace and resource-accounting machinery. This is not a compromise — it is a fundamentally different point in the design space. A container process is a real Linux process, with a real PID, a real file descriptor table, and a real set of credentials. What the kernel does is project a *filtered view* of its global namespaces onto that process, making it appear to live in an isolated world while actually sharing the same scheduler, the same system call interface, and the same physical memory allocator with every other process on the host.

This architectural choice has two profound consequences that every infrastructure engineer must internalize as invariants. First, the container's security boundary is the kernel itself. If a container process can exploit a kernel vulnerability to escape its namespace restrictions, it has root on the host. There is no hypervisor to absorb the fall. The attack surface is the entire Linux kernel system call table. Second, the performance characteristics of a container are essentially bare-metal. A process inside a container does not pay a virtualization tax on CPU instructions, memory accesses, or network packets. It pays only the cost of the kernel's own namespace lookup and cgroup accounting, which on modern kernels amounts to a handful of pointer dereferences per syscall.

Understanding containers at this depth requires holding three separate abstractions simultaneously in mind: **namespaces**, which control what a process can *see*; **cgroups**, which control what a process can *consume*; and **capabilities**, which control what a process can *do*. Docker orchestrates all three, but Docker is not any of them. Docker is a process lifecycle manager, an image distribution mechanism, and a configuration frontend sitting on top of machinery that the Linux kernel has provided since version 3.8.

### The Namespace Invariant

A Linux namespace wraps a particular global system resource and makes it appear to processes within that namespace as though they have their own isolated instance of that resource. The kernel currently ships seven distinct namespace types, each isolating a different dimension of the system's global state.

The **PID namespace** isolates the process ID number space. When a container runtime creates a new PID namespace and forks a child into it, that child sees itself as PID 1. It has no visibility into the host's PID table. It cannot send signals to, or even enumerate, processes outside its namespace. The host, however, sees the full picture: the container's PID 1 appears in the host's process table with some high PID number, and all of its children are visible as ordinary host processes. This asymmetry — the container is blind to the host, the host sees the container — is a fundamental property of namespace hierarchies.

The **net namespace** gives each container a completely private network stack: its own set of network interfaces, routing tables, iptables rules, and socket table. When Docker creates a bridge network, it creates a `veth` pair — a virtual Ethernet cable with one end inside the container's net namespace and the other end in the host's root net namespace attached to a bridge device. The container's end appears as `eth0` from inside the container. The host's end appears as a `vethXXXXXX` interface in `brctl show`. Packets flow through this veth pair and are NAT-translated by the host's iptables `MASQUERADE` rule, letting the container reach the internet via the host's physical NIC.

The **mount namespace** isolates the filesystem hierarchy. Each container gets its own mount table, populated initially by cloning the parent and then applying the container's layered filesystem image — typically an overlayfs mount — as its root. The container's `/proc`, `/sys`, and `/dev` are freshly bind-mounted tmpfs and devtmpfs instances. The host's real `/proc` and `/sys` are invisible. This is what allows a container to claim it has 1 GB of RAM and a 10-core CPU when inspecting `/proc/meminfo` and `/proc/cpuinfo` — provided the runtime has set up those virtual filesystem entries appropriately (though by default, without a tool like `lxcfs`, these files reflect host values, which is a common source of confusion in production).

The **UTS namespace** isolates the hostname and NIS domain name. A container can call `sethostname("my-service")` without affecting the host or any other container. This matters for distributed services that derive their identity from `hostname`, such as Consul-based service registration.

The **IPC namespace** isolates System V IPC objects — shared memory segments, semaphores, and message queues — along with POSIX message queues. Processes in different IPC namespaces cannot communicate through these primitives, preventing a classic lateral movement path where a compromised container writes to a shared memory region observed by a privileged host process.

The **user namespace** is the most architecturally significant from a security standpoint, and also the most operationally complex. It allows a process to have UID 0 (root) *inside* its namespace while mapping to an unprivileged UID outside. A container that believes it is running as root is actually running as UID 65534 from the host's perspective. If it escapes its mount namespace and writes a file, that file is owned by UID 65534, not UID 0. Docker's default configuration does *not* enable user namespaces because they interact poorly with volume mounts and certain kernel subsystems, but rootless Docker and Podman both use user namespaces as their primary security primitive. For security-sensitive deployments, enabling user namespace remapping is non-optional.

The **cgroup namespace** was added in Linux 4.6 and isolates the view of the cgroup hierarchy. Without it, a process inside a container can read `/proc/self/cgroup` and discover the full host cgroup path, leaking information about the container orchestration topology. With a cgroup namespace, the container's own cgroup root appears as `/` inside the namespace.

### The Cgroup Invariant

Where namespaces answer the question of visibility, cgroups answer the question of resource ownership. A control group is a hierarchical accounting unit in the kernel that tracks the resource consumption of all processes assigned to it and enforces configurable limits on that consumption. The cgroup subsystem is split into *controllers*, each governing a resource axis: `cpu`, `cpuset`, `memory`, `blkio`, `net_cls`, `net_prio`, `pids`, `freezer`, and others.

The kernel exposes the cgroup hierarchy as a virtual filesystem, mounted at `/sys/fs/cgroup`. Creating a container's cgroup is as simple as `mkdir /sys/fs/cgroup/memory/my-container`, writing the memory limit in bytes to `memory.limit_in_bytes`, and writing the container's PID to `cgroup.procs`. The kernel then tracks every page fault, every anonymous mapping, and every file-backed page touched by that PID (and its descendants) against that accounting entry. When the process group crosses the limit, the kernel invokes the OOM killer against processes within that cgroup — not against the entire host. This scoped OOM behavior is the difference between a container running out of memory causing its own death and causing a host-wide cascade.

The modern cgroup v2 unified hierarchy, which replaces the chaotic per-controller cgroup v1 mount forest, anchors everything under a single tree at `/sys/fs/cgroup`. The `memory.max` file replaces `memory.limit_in_bytes`, the `cpu.max` file replaces the interaction between `cpu.cfs_quota_us` and `cpu.cfs_period_us`, and the unified `cgroup.procs` file governs membership across all controllers simultaneously. Docker transitioned to cgroup v2 support with the `cgroupns=host` flag, and Kubernetes defaulted to cgroup v2 in 1.25. Any infrastructure engineer still mentally modeled on cgroup v1's split mount forest should update their mental model immediately.

### The Capability Invariant

The POSIX capability model breaks the traditional Unix binary — root can do anything, non-root cannot — into sixty-some discrete privilege bits. `CAP_NET_ADMIN` lets a process manipulate network interfaces and routing tables. `CAP_SYS_PTRACE` lets it trace arbitrary processes. `CAP_SYS_ADMIN` is effectively a catch-all that grants permission to mount filesystems, manipulate namespaces, and perform dozens of other privileged operations, which is why the Linux man page drily notes that "this capability is so broad that it essentially grants root-equivalent access."

Docker's default capability set drops approximately twenty capabilities from the full root set, including `CAP_SYS_ADMIN`, `CAP_NET_ADMIN`, `CAP_SYS_PTRACE`, and `CAP_SYS_RAWIO`. A process running as root inside a container with the default capability set cannot modify iptables rules, cannot trace other processes, and cannot perform raw disk I/O. This matters in production: a container process that achieves code execution via an application vulnerability starts with this restricted capability set, not full kernel privileges.

The practical implication is that capabilities, namespaces, and cgroups form a layered defense stack. Namespaces reduce *visibility*, limiting what the attacker can target. Capabilities reduce *privilege*, limiting what the attacker can instruct the kernel to do. Cgroups reduce *blast radius*, preventing resource exhaustion from propagating to neighboring workloads. No single layer is sufficient; the intersection of all three is what makes the Docker security model coherent, even if it remains weaker than hypervisor isolation.

---

## 2. Core Architecture & Mechanics

### The Container Lifecycle: From `docker run` to Kernel State

Tracing a single `docker run` invocation from the CLI to kernel state reveals the full mechanical path. When you execute `docker run --rm -it --memory=512m ubuntu:22.04 bash`, the Docker CLI encodes this as an HTTP POST to the Docker daemon's Unix socket at `/var/run/docker.sock`. The daemon is a long-running process (dockerd) that manages image storage, network configuration, and container lifecycle. It delegates the actual container creation to **containerd**, a CNCF-graduated runtime daemon, which in turn delegates process spawning to **runc**, an OCI-compliant low-level runtime that is a direct descendent of libcontainer.

The separation between dockerd, containerd, and runc is architecturally significant. containerd owns the image pull, the overlayfs snapshot, and the OCI bundle preparation. runc owns the namespace creation, cgroup assignment, and final `exec`. This layering means you can replace runc with a different OCI runtime (gVisor's `runsc`, Kata Containers' `kata-runtime`) without changing any higher-level infrastructure. The OCI Runtime Specification precisely defines the interface between containerd and the low-level runtime: a directory containing a `config.json` file and a `rootfs` subdirectory.

The sequence from containerd's perspective proceeds in this order. First, containerd resolves the image to a manifest, pulls the layer blobs from the registry if not cached, and assembles them into an overlayfs snapshot. The overlayfs driver stacks the image's read-only layers (called `lowerdir` entries) beneath a fresh empty writable layer (`upperdir`), presenting a merged view as the container's root filesystem. This is the union-mount machinery that makes Docker's layer caching model possible — every instruction in a Dockerfile that produces a filesystem change creates one `lowerdir` entry, and sharing `lowerdir` entries between containers that use the same base image costs zero additional storage for those shared layers.

Second, containerd generates the OCI `config.json`, which specifies the namespace types to create, the cgroup path to assign, the capability bounding set, the root filesystem path, the entry point, and the environment. This JSON document is the complete specification of the container's isolation configuration; every security property discussed in Section 1 is expressed here.

Third, containerd invokes runc, which performs the namespace creation and process execution. runc calls `clone(2)` with a combination of `CLONE_NEWPID`, `CLONE_NEWNET`, `CLONE_NEWNS`, `CLONE_NEWUTS`, `CLONE_NEWIPC` flags, creating a new process that is born into fresh instances of all those namespaces simultaneously. runc then walks the cgroup hierarchy, creates the container's cgroup directory, and writes the memory limit, CPU quota, and PID limit according to the `config.json` specification before writing the container's PID into `cgroup.procs`.

After namespace and cgroup setup, runc calls `pivot_root(2)` (or `chroot(2)` in environments where `pivot_root` is unavailable) to swap the container process's root filesystem to the overlayfs mount. It then drops capabilities, sets the user and group IDs, and executes the container's entry point via `execve(2)`. From this point forward, the container process is running. It is an ordinary Linux process with a filtered namespace view, bounded resource consumption, and a reduced capability set.

The following diagram depicts the relationships between the Docker toolchain components, the kernel namespace and cgroup state, and the container process:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  User Space                                                             │
│                                                                         │
│  ┌────────────┐  HTTP/Unix Socket  ┌────────────────────────────────┐  │
│  │ docker CLI │ ────────────────▶  │          dockerd               │  │
│  └────────────┘                    │  (image mgmt, API, networking) │  │
│                                    └───────────────┬────────────────┘  │
│                                                    │ gRPC               │
│                                    ┌───────────────▼────────────────┐  │
│                                    │          containerd             │  │
│                                    │  (snapshots, OCI bundle,        │  │
│                                    │   image pull, shim lifecycle)   │  │
│                                    └───────────────┬────────────────┘  │
│                                                    │ exec()             │
│                                    ┌───────────────▼────────────────┐  │
│                                    │  containerd-shim-runc-v2       │  │
│                                    │  (per-container shim process)  │  │
│                                    └───────────────┬────────────────┘  │
│                                                    │ OCI bundle         │
│                                    ┌───────────────▼────────────────┐  │
│                                    │             runc               │  │
│                                    │  (namespace clone, pivot_root, │  │
│                                    │   cgroup write, cap drop,      │  │
│                                    │   execve entry point)          │  │
│                                    └───────────────┬────────────────┘  │
└───────────────────────────────────────────────────┼─────────────────────┘
                                                    │ syscalls
┌──────────────────────────── Kernel Space ─────────▼─────────────────────┐
│                                                                          │
│   clone(CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWNS|CLONE_NEWUTS|CLONE_NEWIPC)│
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  Namespace Layer                                                  │  │
│   │  PID ns ── NET ns ── MNT ns ── UTS ns ── IPC ns ── USER ns       │  │
│   └────────────────────────────────┬─────────────────────────────────┘  │
│                                    │                                     │
│   ┌────────────────────────────────▼─────────────────────────────────┐  │
│   │  Cgroup v2 Hierarchy                                              │  │
│   │  /sys/fs/cgroup/system.slice/docker-<id>.scope/                  │  │
│   │      memory.max = 536870912                                       │  │
│   │      cpu.max = 100000 100000                                      │  │
│   │      pids.max = 1024                                              │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │  Overlayfs Mount                                                  │  │
│   │  lowerdir=/var/lib/docker/overlay2/<id>/diff (read-only layers)  │  │
│   │  upperdir=/var/lib/docker/overlay2/<id>/work/upper (writable)    │  │
│   │  merged  =/var/lib/docker/overlay2/<id>/merged  (container root) │  │
│   └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Inspecting the Live Kernel State

The most valuable skill a container infrastructure engineer can develop is the ability to read the kernel's actual state for a running container, independent of the Docker daemon. This builds the mental model that makes debugging possible when Docker's own tooling gives misleading or incomplete output.

Given a running container, the first thing to examine is its PID as seen from the host. `docker inspect --format '{{.State.Pid}}' <container_id>` returns the host-visible PID of the container's init process. With that PID in hand, the entire kernel state for the container is accessible under `/proc/<PID>/`.

The namespace memberships of a process live at `/proc/<PID>/ns/`. Each entry there is a symbolic link whose target encodes the namespace type and inode number.

```bash
# Identify host-side PID of a running container
CPID=$(docker inspect --format '{{.State.Pid}}' $(docker ps -q --filter name=mycontainer))
echo "Container init PID on host: $CPID"

# List all namespace memberships for the container process
ls -la /proc/$CPID/ns/
# Expected output resembles:
# lrwxrwxrwx 1 root root 0 ... cgroup -> cgroup:[4026531835]
# lrwxrwxrwx 1 root root 0 ... ipc    -> ipc:[4026532512]
# lrwxrwxrwx 1 root root 0 ... mnt    -> mnt:[4026532510]
# lrwxrwxrwx 1 root root 0 ... net    -> net:[4026532515]
# lrwxrwxrwx 1 root root 0 ... pid    -> pid:[4026532513]
# lrwxrwxrwx 1 root root 0 ... uts    -> uts:[4026532511]

# Compare with the host init process (PID 1) namespace inodes
ls -la /proc/1/ns/
# Any inode that differs between the container and PID 1 is an isolated namespace.
# Any inode that matches is SHARED with the host -- a potential security concern.
```

Two namespaces sharing the same inode number means they are the same namespace object in the kernel, and isolation between those two processes along that dimension does not exist. This is how you audit whether a container is running with `--network=host` (the net namespace inode will match PID 1's) or `--pid=host` (the pid namespace inode will match).

The cgroup membership and limits are equally readable from the host filesystem without any Docker tooling:

```bash
# Confirm the cgroup path the container's init process belongs to
cat /proc/$CPID/cgroup
# On a cgroup v2 system:
# 0::/system.slice/docker-<full_container_id>.scope

# Read the memory limit enforced by the kernel
CGROUP_PATH=$(cat /proc/$CPID/cgroup | grep -oP '(?<=::).*')
cat /sys/fs/cgroup${CGROUP_PATH}/memory.max
# If Docker was started with --memory=512m, this should print 536870912

# Read the current memory consumption
cat /sys/fs/cgroup${CGROUP_PATH}/memory.current

# Read the CPU quota: format is "quota_us period_us"
# "100000 100000" means 100ms quota per 100ms period = 1 full CPU
# "50000 100000" means 50ms quota per 100ms period = 0.5 CPU
cat /sys/fs/cgroup${CGROUP_PATH}/cpu.max

# Read the PID limit
cat /sys/fs/cgroup${CGROUP_PATH}/pids.max
```

The capabilities of the container process are equally auditable. `/proc/<PID>/status` contains several capability sets: `CapInh` (inheritable), `CapPrm` (permitted), `CapEff` (effective), `CapBnd` (bounding), and `CapAmb` (ambient). The effective set is what the kernel checks on privileged system calls. These values are hex-encoded bitmasks.

```bash
# Read capability bitmasks for the container process
grep Cap /proc/$CPID/status

# Decode the bitmask into human-readable capability names
# capsh is part of the libcap2-bin package
CAPEFF=$(grep CapEff /proc/$CPID/status | awk '{print $2}')
capsh --decode=$CAPEFF
# A default Docker container will show something like:
# 0x00000000a80425fb = cap_chown,cap_dac_override,cap_fowner,cap_fsetid,
#                      cap_kill,cap_setgid,cap_setuid,cap_setpcap,
#                      cap_net_bind_service,cap_net_raw,cap_sys_chroot,
#                      cap_mknod,cap_audit_write,cap_setfcap
```

Notice that `cap_sys_admin`, `cap_net_admin`, `cap_sys_ptrace`, and `cap_sys_rawio` are absent. This is the Docker default drop list in action.

### The Overlayfs Layer Mechanics

The container's filesystem view deserves mechanical examination because misunderstanding overlayfs is a persistent source of production incidents, particularly around image layer bloat, `docker build` cache invalidation, and unexpected write amplification.

Overlayfs operates by stacking a list of read-only lower directories beneath a single writable upper directory. When a process inside the container reads a file, the kernel walks the layer stack from upper to lower, returning the first matching inode it finds. When a process writes to a file that exists only in the lower layers, the kernel performs a **copy-on-write**: it copies the entire file from the lower layer into the upper layer, then applies the write to the upper copy. The lower layer is never modified. This copy-on-write semantic applies to entire files, not pages or blocks, which means writing one byte to a large file in a lower layer incurs the full copy cost of that file into the upper layer. For a 50 MB binary, that is a 50 MB write on first modification.

Deletions in overlayfs are represented by **whiteout entries**: special device files with device number 0/0 placed in the upper layer at the path of the deleted file. When the kernel encounters a whiteout during path resolution, it stops the layer walk and returns `ENOENT` as if the file never existed, without touching the lower layers.

```bash
# Inspect the overlayfs mounts for all running containers
mount | grep overlay
# Output:
# overlay on /var/lib/docker/overlay2/<id>/merged type overlay
#   (rw,relatime,lowerdir=<l1>:<l2>:<l3>,upperdir=<upper>,workdir=<work>)

# Examine the actual layer directories on disk for a specific container
docker inspect --format '{{json .GraphDriver.Data}}' <container_id> | python3 -m json.tool
# This prints:
# {
#   "LowerDir": "/var/lib/docker/overlay2/<id-1>/diff:/var/lib/docker/overlay2/<id-2>/diff",
#   "MergedDir": "/var/lib/docker/overlay2/<id-N>/merged",
#   "UpperDir": "/var/lib/docker/overlay2/<id-N>/diff",
#   "WorkDir": "/var/lib/docker/overlay2/<id-N>/work"
# }

# Measure the actual disk usage of a container's writable layer
# (what the container has written since it started)
du -sh /var/lib/docker/overlay2/<id-N>/diff
```

Understanding this layout directly enables production decisions: the writable `diff` directory is where all container writes accumulate, it is per-container and not shared, and it disappears when the container is removed. Any data you need to persist must live on a bind mount or volume, which bypasses overlayfs entirely and writes directly to the host filesystem or a volume driver's backend.

### Virtual Ethernet Pairs and Bridge Networking

The networking architecture of a standard Docker container involves four distinct kernel objects working in concert: a network namespace, a veth pair, a Linux bridge, and an iptables NAT rule. These four objects together implement the full data path from a container process making a TCP connection to receiving a response from a server on the internet.

When Docker creates a container connected to its default `bridge` network, it first ensures the `docker0` bridge interface exists in the host's root net namespace (Docker creates this bridge at daemon startup). It then creates a `veth` pair — a pair of linked virtual network interfaces that act as a pipe: any packet written into one end immediately appears at the other end. One interface of this pair is moved into the container's net namespace (where it appears as `eth0`) and given the container's IP address. The other interface remains in the host's root namespace (where it appears as `vethXXXXXX`) and is attached as a port on the `docker0` bridge.

```bash
# On the host, observe the docker0 bridge and attached veth interfaces
ip link show docker0
brctl show docker0

# List all veth interfaces on the host (one per running bridge-networked container)
ip link show type veth

# From inside a running container, confirm the container-side interface
docker exec -it <container_id> ip addr show eth0
docker exec -it <container_id> ip route show

# The container's default route points to the bridge gateway IP (usually 172.17.0.1)
# That IP is assigned to docker0 on the host, which serves as the container's gateway

# Observe the NAT masquerade rule that enables internet access
iptables -t nat -L POSTROUTING -n -v
# You will see a rule masquerading traffic from the Docker bridge subnet:
# MASQUERADE  all  --  172.17.0.0/16  !172.17.0.0/16
```

This architecture explains why container-to-container communication on the same bridge is fast (packets traverse the bridge in-kernel without hitting iptables NAT) while container-to-external traffic incurs conntrack and NAT overhead. It also explains why `--network=host` bypasses all of this: the container process simply has no net namespace boundary and writes directly into the host's network stack, gaining performance at the cost of network isolation.

---

## 3. High-Performance Optimization & Failure Modes

### CPU Throttling and the CFS Quota Trap

The most common and most damaging performance failure mode in containerized production environments is CPU throttling, and it is almost always a consequence of misunderstanding how the Linux Completely Fair Scheduler enforces cgroup CPU quotas.

The CFS CPU controller enforces limits through a token bucket mechanism. Each cgroup has a quota (expressed in microseconds) that replenishes every period (also expressed in microseconds). The Docker `--cpus=0.5` flag translates to `cpu.max = 50000 100000` in cgroup v2: the cgroup may consume 50,000 µs of CPU time within any 100,000 µs window. When a process exhausts its quota, the kernel marks the cgroup as *throttled* and prevents any process within it from being scheduled until the next period boundary. The throttled process cannot make forward progress even if CPU cores are sitting entirely idle.

This manifests catastrophically for latency-sensitive services. A request handler that needs 60 ms of CPU time within a 100 ms window will be throttled for the last 10 ms of that window, potentially causing a 50–90 ms additional tail latency spike even on a host with 95% idle CPU. The metric to watch is `cpu.stat`'s `throttled_time` field (cgroup v2) or the `nr_throttled` and `throttled_time` fields in `cpu.stat` on cgroup v1 mounts.

```bash
# Read CPU throttling statistics for a running container (cgroup v2)
CGROUP_PATH=$(cat /proc/$(docker inspect --format '{{.State.Pid}}' <container_id>)/cgroup | grep -oP '(?<=::).*')
cat /sys/fs/cgroup${CGROUP_PATH}/cpu.stat
# Fields of interest:
# nr_periods          -- number of enforcement periods elapsed
# nr_throttled        -- number of periods where the cgroup was throttled
# throttled_usec      -- cumulative throttled time in microseconds
# throttled_usec / (nr_periods * period_duration) = throttle ratio

# Compute period duration from cpu.max
cat /sys/fs/cgroup${CGROUP_PATH}/cpu.max
# Format: quota_us period_us
# A throttle ratio above 5% on a latency-sensitive service warrants investigation
```

The mitigation strategies fall into two categories. The first is to increase the quota, either by raising `--cpus` or by switching to `--cpu-shares` (which is a soft weight-based scheduler hint that never throttles, only deprioritizes relative to competing cgroups during CPU contention). The second, more principled approach is to increase the CFS period itself. A period of 10 ms instead of 100 ms gives the same average quota but allows the application to burst within shorter windows without hitting the throttling boundary, reducing tail latency significantly. This is not exposed through Docker's CLI but can be written directly to the cgroup filesystem.

```bash
# Reduce CFS period to 10ms while keeping the same average quota (0.5 CPU)
# This reduces throttling granularity from 100ms windows to 10ms windows
CGROUP_PATH=$(cat /proc/$(docker inspect --format '{{.State.Pid}}' <container_id>)/cgroup | grep -oP '(?<=::).*')
# 5000 quota / 10000 period = 0.5 CPU average, same as 50000/100000
echo "5000 10000" | sudo tee /sys/fs/cgroup${CGROUP_PATH}/cpu.max
```

### Memory OOM Behavior and the Limit Misconfiguration Failure Mode

The memory controller's OOM killer behavior has a subtle but critical property: when a container hits its memory limit, the kernel invokes the OOM killer scoped to that cgroup, selecting the process within the cgroup with the highest `oom_score_adj`-weighted RSS. This kills a process inside the container, not necessarily the container's PID 1. If PID 1 survives (because it has a low `oom_score` or small RSS), the container continues running in a degraded state with dead worker processes. Docker will not mark the container as unhealthy or restart it. The container appears running to `docker ps`, but it is functionally broken.

The correct production behavior requires two things. First, container entry points must be PID 1 processes that act as proper init systems — either by using `tini` as an init shim, or by using Docker's `--init` flag, which injects tini as PID 1 and runs the specified entry point as a child. A proper PID 1 reaps zombie children and propagates signals, so when the OOM killer kills a critical child process, PID 1 receives a `SIGCHLD`, detects the abnormal exit, and exits itself, triggering Docker's restart policy. Second, container memory limits should be set to `memory.max` only (the hard limit that triggers OOM), and `memory.high` (the soft limit that triggers reclaim pressure without OOM) should be set to roughly 80% of `memory.max` to allow graceful reclaim before hitting the hard boundary.

```bash
# Inspect OOM kill events for a container
docker inspect --format '{{.State.OOMKilled}}' <container_id>

# Monitor OOM events in real time from the kernel's perspective
dmesg -wT | grep -i "oom\|killed process"

# Set memory limits appropriately in a production Dockerfile / compose manifest
# --memory sets memory.max (hard limit)
# --memory-reservation sets memory.high (soft limit / reclaim trigger)
docker run \
  --memory=512m \
  --memory-reservation=400m \
  --memory-swap=512m \
  --init \
  --name production-service \
  myimage:latest
```

Setting `--memory-swap` equal to `--memory` disables swap for the container entirely (the swap allowance above the memory limit is zero). For latency-sensitive services, disabling swap prevents the kernel from paging out the application's working set to disk under memory pressure, which would otherwise cause multi-millisecond latency spikes on page fault resolution.

### Namespace Escape Vectors and Hardening

The critical failure mode in production namespace security is not a sophisticated kernel exploit — it is a misconfigured container that voluntarily surrenders its isolation. The three most common misconfigurations in production are `--privileged`, `--pid=host`, and volume mounts of sensitive host paths.

`--privileged` grants the container's init process the full capability set, removes the seccomp filter, disables AppArmor confinement, and removes device cgroup restrictions, giving the container process unrestricted access to every device node. A privileged container can mount the host filesystem, modify iptables rules, load kernel modules, and in most configurations trivially escape to full host root. The common justification — "we needed it for Docker-in-Docker" — is addressable with targeted capability grants (`--cap-add SYS_ADMIN`) combined with a seccomp profile that permits only the specific syscalls required.

A container running with `--pid=host` shares the host's PID namespace. From inside such a container, `ps aux` shows all host processes. More critically, `kill -9 <host_pid>` works. A malicious or buggy process inside the container can send signals to the Docker daemon itself, to the kernel's kthreads, or to any critical system service. This configuration should never appear in production outside of specialized debugging tools, and even then it should be gated behind time-limited, audited access.

Volume mounts are the third and most pervasive escape vector. Mounting the Docker socket (`-v /var/run/docker.sock:/var/run/docker.sock`) gives the container complete control over the Docker daemon, which is equivalent to host root. Mounting `/etc` or `/` as writable gives the container trivial filesystem escape. Mounting `/proc` or `/sys` from the host exposes the host's kernel interfaces. The correct policy is to never mount host paths into containers without explicit review, to use Docker named volumes for persistent data (which live under `/var/lib/docker/volumes/` and are managed by the daemon), and to use bind mounts only for explicitly reviewed host directories with the `:ro` read-only flag wherever write access is not strictly required.

```bash
# Audit running containers for dangerous configurations
# Check for privileged containers
docker ps -q | xargs docker inspect --format '{{.Name}}: Privileged={{.HostConfig.Privileged}}'

# Check for host PID namespace sharing
docker ps -q | xargs docker inspect --format '{{.Name}}: PidMode={{.HostConfig.PidMode}}'

# Check for host network namespace sharing
docker ps -q | xargs docker inspect --format '{{.Name}}: NetworkMode={{.HostConfig.NetworkMode}}'

# List all bind mounts for all running containers
docker ps -q | xargs -I{} docker inspect --format '{{.Name}}: {{range .Mounts}}{{if eq .Type "bind"}}{{.Source}}->{{.Destination}}({{.Mode}}) {{end}}{{end}}' {}

# Check for Docker socket mount (critical escalation path)
docker ps -q | xargs docker inspect --format '{{.Name}}' \
  $(docker ps -q | xargs docker inspect --format '{{range .Mounts}}{{if eq .Source "/var/run/docker.sock"}}{{$.Id}}{{end}}{{end}}')
```

### Image Layer Optimization and Build Cache Mechanics

Dockerfile layer ordering is not merely an aesthetic concern — it has direct implications for build cache hit rates, image pull times, and registry storage costs. The overlayfs pull model downloads layers independently and in parallel, so the total pull time is bounded by the largest individual layer, not their sum. A single 800 MB layer will always be slower to pull than eight 100 MB layers, regardless of total size, because parallel transfer cannot be exploited within a single layer blob.

The build cache invalidation rule is simple but its consequences are non-obvious: any instruction whose content changes (or whose preceding instruction was cache-missed) invalidates the cache for all subsequent instructions. This means a Dockerfile that copies the entire application source tree before installing dependencies will rebuild all dependencies on every source change, even if the dependency manifest (`package.json`, `requirements.txt`, `go.mod`) is unchanged. The correct pattern is to copy only the dependency manifest first, run the dependency installation step, and then copy the full source, so the dependency installation layer is cache-valid on pure source changes.

```dockerfile
# Suboptimal: copies all source before dependency install
# Any source file change invalidates the pip install layer
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]


# Optimized: dependency manifest copied first, source second
# pip install layer is cache-valid when only source files change
FROM python:3.12-slim AS runtime
WORKDIR /app

# Layer 1: system dependencies (rarely change, cache almost always valid)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: Python dependency manifest only (changes only when deps change)
COPY requirements.txt .

# Layer 3: dependency installation (cache-valid across pure source changes)
RUN pip install --no-cache-dir -r requirements.txt

# Layer 4: application source (changes frequently, fine — it's the last layer)
COPY src/ ./src/

# Non-root user: drop privileges for the runtime process
RUN adduser --disabled-password --gecos '' appuser
USER appuser

CMD ["python", "src/main.py"]
```

Multi-stage builds extend this further by using intermediate build stages whose toolchains (compilers, linkers, test frameworks) are discarded from the final image. The final image contains only the runtime artifacts, keeping attack surface and image size minimal.

```dockerfile
# Multi-stage build for a Go service
# Stage 1: builder -- contains the full Go toolchain, discarded at the end
FROM golang:1.22-bookworm AS builder

WORKDIR /build

# Cache module downloads separately from source compilation
COPY go.mod go.sum ./
RUN go mod download

# Copy source and compile a fully static binary
COPY cmd/ ./cmd/
COPY internal/ ./internal/

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s -extldflags '-static'" \
    -o /build/server \
    ./cmd/server

# Stage 2: final image -- scratch has zero attack surface, zero CVE footprint
# No shell, no package manager, no libc, no nothing except the binary
FROM scratch AS final

# Copy only the compiled binary and the CA cert bundle for TLS
COPY --from=builder /build/server /server
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Document the port (does not publish it; use -p at runtime)
EXPOSE 8080

ENTRYPOINT ["/server"]
```

The `scratch` base image is literally an empty filesystem. The resulting image contains exactly two files: the binary and the CA certificates. It has no shell, no package manager, no interpreter, and no standard library files. An attacker who achieves code execution via an application vulnerability finds themselves in a container with no tools to work with and a minimal capability set. This is defense in depth applied at the image construction layer.

### Seccomp and the System Call Filter

The final hardening layer worth mechanical understanding is the seccomp (Secure Computing Mode) filter. Docker's default seccomp profile is a JSON-encoded BPF filter specification that blocks approximately 44 of the ~300+ Linux system calls, including `keyctl`, `add_key`, `request_key` (kernel keyring manipulation), `ptrace` (process tracing), `reboot` (system reboot), `kexec_load` (kernel replacement), and `mount` (filesystem mounting). The filter is loaded into the kernel via `prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ...)` before `execve` runs the container entry point, and it cannot be removed by the container process after that point.

The practical engineering decision is whether to run with Docker's default profile (which provides meaningful baseline protection for most workloads), a custom profile (which requires enumerating all syscalls your application actually makes, typically via `strace -c`), or no profile (`--security-opt seccomp=unconfined`, which is appropriate only in debugging scenarios and should never reach production).

```bash
# Verify that a container has a seccomp filter applied
# A container without seccomp will show "unconfined"; with default or custom profile, it shows the profile name
docker inspect --format '{{.HostConfig.SecurityOpt}}' <container_id>

# Profile a container's actual syscall usage to build a minimal custom seccomp profile
# Run the container with strace wrapping the entry point
docker run --rm \
  --cap-add SYS_PTRACE \
  --security-opt seccomp=unconfined \
  --entrypoint strace \
  myimage:latest \
  -c -f -S name \
  /actual-entrypoint --actual-args
# The -c flag prints a summary table of syscall frequencies at exit
# Feed this list into a custom seccomp JSON profile that allows only those syscalls
```

The resulting custom profile reduces the kernel attack surface available to the container process to exactly the system calls its workload legitimately requires. Any exploit that requires a syscall not in the allowlist will fail with `EPERM` at the seccomp filter boundary, before the kernel even evaluates the capability check or namespace restrictions. Seccomp, capabilities, namespaces, and cgroups together form a defense-in-depth stack where each layer operates independently, ensuring that bypassing one does not automatically compromise the others.

The discipline of understanding containers at this kernel level — reading namespace inodes, interpreting cgroup accounting files, auditing capability bitmasks, and tracing overlayfs layer composition — is what separates infrastructure engineers who can diagnose production failures from those who can only observe them. Docker's command-line interface abstracts all of this, by design. But the underlying kernel state is always there, always readable, and always telling the truth about what is actually happening on the machine.
