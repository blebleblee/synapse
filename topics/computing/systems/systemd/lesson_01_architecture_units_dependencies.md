# Lesson 1: System Architecture, Unit Abstraction, and the Dependency Graph

## 1. First-Principles Intuition & Invariants

To understand why systemd was designed the way it was, you have to understand the specific failure mode it was designed to correct. SysV init, the dominant init system on Linux from the mid-1990s through the late 2000s, operated on a model that was conceptually simple to the point of naivety: a numbered sequence of shell scripts executed one after another, organized into runlevels. The kernel hands control to `/sbin/init`, which consults `/etc/inittab`, which triggers `rc` scripts in `/etc/rc.d/` or `/etc/init.d/` in strict serial order. Script `S20networking` finishes, then `S30syslog` starts, then `S40cron`, and so on. The simplicity is seductive until you operate a system that needs to boot quickly, recover gracefully from partial failure, or manage hundreds of interdependent services dynamically across its lifetime.

The fundamental invariant of SysV is ordering through global sequence numbers. This encoding carries two compounding problems. First, it is brittle: the dependency between two services is implied by their numeric position in a flat namespace, not declared explicitly. If you need a new service to start after the network is up but before the application server, you must pick a number between two existing numbers and hope no other administrator has already claimed it. The dependency model is an artifact of filename collision, not formal graph theory. Second, it is maximally conservative about parallelism: because dependencies are only implicit, the init system cannot know which services are truly independent. It serializes everything. A machine with eight cores boots as if it has one.

Lennart Poettering and Kay Sievers began work on systemd in 2010 with a different set of axioms. The root insight, articulated in Poettering's original announcement blog post, is that the boot process on a modern system is a dependency graph problem, and dependency graph problems have been solved rigorously by computer science for decades. The correct tool is not shell scripts with sequence numbers; it is a directed acyclic graph (DAG) over declarative unit definitions, traversed by a scheduler that can aggressively parallelize along topologically independent edges.

This architectural decision propagates into everything systemd does. Because services declare their dependencies explicitly, the init system can compute the full transitive closure of what must be running before any given unit activates. Because it holds the complete graph in memory, it can determine which subgraphs are independent and dispatch their activation concurrently. Because units are first-class objects with known states rather than opaque scripts with unknown side effects, the init system can track health, restart failed services, and reason about what must be torn down when any given unit fails.

The other foundational invariant distinguishing systemd from its predecessors is the rejection of polling in favor of socket activation. SysV services that depended on each other had to either sleep and retry until a dependency was available, or embed explicit ordering that forced sequential startup. Systemd adopted a technique pioneered by Apple's launchd: pre-create the listening socket for a service before the service itself starts, and hand that socket to the service process when it eventually launches. Because the socket exists before the service, any client that connects during the startup window simply blocks in the kernel's connection queue. The service starts in parallel with its dependents rather than in sequence, and the kernel serializes them transparently. The wall-clock time for a fully parallelized systemd boot on modern hardware with SSD storage is measured in seconds where SysV took tens of seconds to minutes on equivalent workloads.

Understanding these two invariants, the DAG dependency model and socket activation, is the prerequisite for every other concept in this lesson. Everything else is elaboration on how they are implemented and what breaks when they are misused.

---

## 2. Core Architecture & Mechanics

### The Unit as the Atomic Object

Systemd's fundamental abstraction is the **unit**. A unit is a named, typed configuration object that describes some resource or behavior the init system manages. Units live in text files whose suffix encodes their type: `nginx.service`, `postgresql.socket`, `local-fs.target`, `dev-sda1.device`, `home.mount`, `logrotate.timer`. Systemd scans a layered set of directories to discover unit files: `/lib/systemd/system/` for vendor-supplied units, `/etc/systemd/system/` for administrator-defined units, and `/run/systemd/system/` for runtime-generated units. Files in `/etc/` override files of the same name in `/lib/`, which is how you customize or mask vendor units without modifying package-managed files.

Each unit file is an INI-style configuration document with sections that differ by unit type, but all share a mandatory `[Unit]` section containing metadata and dependency declarations. The separation between metadata, dependency graph edges, and type-specific configuration is deliberate. Consider a minimal service unit:

```ini
[Unit]
Description=Application Server
Documentation=https://example.com/docs
After=network-online.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=appuser
ExecStart=/usr/bin/app-server --config /etc/app/config.toml
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
```

The `[Unit]` section encodes two conceptually distinct things: ordering constraints (`After=`, `Before=`) and dependency constraints (`Requires=`, `Wants=`, `BindsTo=`). This distinction matters enormously in practice, and conflating the two is the most common systemd configuration error made by experienced engineers.

An `After=` declaration says: if both this unit and the named unit are being activated in the same transaction, activate the named unit first. It says nothing about whether the named unit must exist or be active. A `Requires=` declaration says: this unit cannot run without the named unit; if the named unit fails or is explicitly deactivated, stop this unit too. The two declarations are orthogonal. If you specify `Requires=postgresql.service` without `After=postgresql.service`, systemd may start both units simultaneously, satisfying the requirement (both are being activated) while creating a race condition where your application starts before PostgreSQL is ready. The correct expression of "I need PostgreSQL running before I start" is the conjunction of both.

The dependency vocabulary has four main ordering and four main requirement keywords, which form the complete edge grammar of the unit graph:

| Keyword | Type | Effect |
|---|---|---|
| `After=` | Ordering | This unit activates after the listed units in the same transaction |
| `Before=` | Ordering | This unit activates before the listed units in the same transaction |
| `Requires=` | Requirement (hard) | Listed units must activate successfully; if they stop, this unit stops |
| `Wants=` | Requirement (soft) | Listed units are started alongside this one, but failure does not propagate |
| `BindsTo=` | Requirement (strict) | Like `Requires=`, but also stops this unit if the dependency stops for any reason |
| `PartOf=` | Propagation | Stopping or restarting the listed unit stops or restarts this one |
| `Conflicts=` | Anti-dependency | This unit and the listed units cannot be active simultaneously |
| `Upholds=` | Active maintenance | Continuously ensures listed units remain active while this unit is running |

### Unit State Machine

Each unit is a state machine. The possible states vary by unit type, but the core set that all units share is: `inactive`, `activating`, `active`, `deactivating`, `failed`, and `maintenance`. The transition from `inactive` to `activating` is triggered by an activation request, which may come from the dependency resolver, a user calling `systemctl start`, D-Bus activation, or socket activity. The transition from `activating` to `active` depends on the service type: for `Type=simple`, it occurs when the main process forks; for `Type=exec`, after the binary executes; for `Type=forking`, after the parent process exits (the traditional daemon model); for `Type=notify`, after the process sends `sd_notify(READY=1)` through the notification socket; for `Type=dbus`, after the process claims its configured D-Bus bus name.

The notification socket protocol (`Type=notify`) deserves particular attention because it is the most correct choice for well-behaved services and is frequently misused or skipped. When a service declares `Type=notify`, systemd creates a Unix domain socket before forking the service and passes its path in the `NOTIFY_SOCKET` environment variable. The service writes `READY=1\n` to this socket when it has completed initialization and is genuinely ready to accept connections. This is the precise handshake that eliminates the boot race condition: systemd does not transition the unit to `active` until the service itself signals readiness, so any dependent unit that declares `After=` this service will not start until the service is truly operational, not merely forked.

### The Dependency Resolver and Transaction Engine

When systemd receives an activation request for a unit, it does not simply start that unit. It builds a **transaction**: a minimal, consistent set of job operations required to bring the requested unit into the requested state while satisfying all graph constraints. This transaction engine is the core of systemd's correctness guarantee.

A job in systemd's internal representation is a tuple of `(unit, operation)` where operation is one of `start`, `stop`, `reload`, `restart`, or `verify-active`. Building a transaction begins with the requested job and recursively traverses the dependency graph. For every hard dependency encountered via `Requires=` or `BindsTo=`, a corresponding `start` job is added. For every `Conflicts=` edge, a `stop` job for the conflicting unit is added. For every `After=`/`Before=` edge, an ordering constraint is recorded between jobs rather than a new job being added, because ordering edges don't require the referenced unit to be started unless something else demands it.

After the job set is assembled, the transaction is validated for consistency. A transaction is inconsistent if it contains both a `start` and a `stop` job for the same unit with no way to resolve the conflict, or if its ordering constraints form a cycle. Cycles in ordering constraints are a configuration error that systemd detects and reports with a detailed conflict trace. The resolution algorithm attempts to merge conflicting jobs by promoting a `start` to override a conflicting `stop` when the requesting unit has sufficient priority, but if no consistent resolution is possible, the entire transaction is aborted and an error is reported before any unit state changes.

```
Activation Request: app-server.service
│
├─ Requires: postgresql.service → add job: start postgresql.service
│   └─ Requires: network.target → add job: start network.target (already active, verify-active)
│
├─ After: postgresql.service → record ordering constraint
├─ After: network-online.target → record ordering constraint
│
└─ Transaction:
   [1] start network.target       (verify-active, already satisfied)
   [2] start postgresql.service   (After: [1])
   [3] start app-server.service   (After: [2])
```

Once the transaction is validated, jobs are dispatched to the job queue. The job runner processes jobs in dependency order, running all jobs whose ordering constraints are satisfied concurrently. This is the mechanism by which systemd achieves parallel activation: independent subgraphs in the dependency DAG produce independent jobs with no mutual ordering constraints, and the job runner dispatches them simultaneously.

### Socket Activation Architecture

The socket activation mechanism deserves a precise mechanical explanation because it drives so much of systemd's boot performance. When systemd processes a `.socket` unit, it calls `socket(2)`, `bind(2)`, and `listen(2)` on behalf of the eventual service process, then holds the file descriptor open in its own process table. The corresponding `.service` unit is not started immediately. When the first connection or datagram arrives, the kernel queues it in the socket's receive buffer. Systemd detects this via `epoll(7)` and starts the service, passing the already-bound, already-listening socket file descriptor via `SD_LISTEN_FDS`. The service calls `sd_listen_fds(0)` to retrieve the count of passed file descriptors and then uses them directly without calling `socket()`, `bind()`, or `listen()` itself.

The implication for boot parallelism is significant. Because the socket exists before the service, all units that depend on that socket's availability can proceed concurrently with the service startup. The kernel's connection queue acts as a rendezvous buffer: requests that arrive during service initialization are held in kernel space and delivered once the service's first `accept(2)` call runs. No userspace polling or retry logic is required.

The `.socket` unit and its corresponding `.service` unit are linked by a naming convention: `foo.socket` activates `foo.service` by default, though this is configurable via `Service=` in the socket unit. The two units can declare independent ordering and dependency relationships, giving operators precise control over when the socket becomes available versus when the backing service starts.

### Target Units and the Boot Graph

Targets are the systemd equivalent of SysV runlevels, but they are architecturally richer because they are just ordinary units participating in the dependency graph rather than a separate indexing mechanism. `multi-user.target` is not a runlevel number; it is a synchronization point that other units declare a dependency on via `WantedBy=` in their `[Install]` section. When you run `systemctl enable nginx.service`, systemd creates a symlink from `/etc/systemd/system/multi-user.target.wants/nginx.service` to the unit file, dynamically adding a `Wants=nginx.service` edge to `multi-user.target` without modifying any unit file.

The standard boot sequence is itself a chain of targets, each representing a stable system state:

```
sysinit.target
    │  (mounts, kernel modules, udev)
    ▼
basic.target
    │  (timers, paths, local sockets)
    ▼
multi-user.target ──► network-online.target
    │                        │
    │                   (network stack fully configured)
    ▼
graphical.target
```

This graph encodes the invariant that you cannot reach `multi-user.target` without passing through `basic.target`, and you cannot reach `basic.target` without `sysinit.target`. The targets act as ordering fences: any unit that declares `After=network-online.target` is guaranteed to start after all units that have propagated their completion into that target's activation.

---

## 3. High-Performance Optimization & Failure Modes

### Diagnosing Boot Performance with systemd-analyze

The first tool every systems programmer should internalize is `systemd-analyze`. Its output is not merely diagnostic; it encodes the structure of the boot DAG in a form you can act on.

```bash
# Overall boot time breakdown: firmware, loader, kernel, userspace
systemd-analyze time

# Rank units by time spent in activating state
systemd-analyze blame

# Generate a detailed SVG of the boot timeline with dependency arrows
systemd-analyze plot > boot-timeline.svg

# Compute the critical path: the longest dependency chain determining total boot time
systemd-analyze critical-chain multi-user.target

# Verify unit file syntax and configuration consistency
systemd-analyze verify /etc/systemd/system/app-server.service
```

The `critical-chain` subcommand is the most operationally useful. It performs a longest-path traversal of the dependency DAG from the target unit backwards, identifying which chain of sequential `After=` constraints is responsible for the total activation time. A well-optimized boot graph has a short critical path with many wide parallel branches. A poorly configured one is a long spine of sequential dependencies where nearly every unit has `After=` pointing at the previous unit, recreating the SysV serial boot in modern configuration syntax.

### Eliminating Spurious `network-online.target` Dependencies

One of the most common and damaging performance mistakes in production systemd configurations is declaring `After=network-online.target` for services that do not genuinely require a fully configured network stack before they can start. `network-online.target` is a synchronization point that blocks until the network manager has confirmed IP address assignment on all configured interfaces. On systems using DHCP, particularly in cloud environments where DHCP response latency varies, this target can add five to thirty seconds to the critical path.

The correct discipline is to use `After=network.target` for services that need the network namespace to exist and routing tables to be configured, `After=network-online.target` only for services that must resolve hostnames or connect to remote endpoints during their startup sequence, and no network ordering at all for services that are purely local or that handle network unavailability gracefully in their own code. Services that use `Type=notify` and implement proper reconnection logic should almost never block on `network-online.target`.

### Unit File Hardening and Resource Control

Production service units should declare resource limits and security constraints in the `[Service]` section. These are not stylistic recommendations; they directly affect kernel-level enforcement of process isolation through cgroups and Linux security modules:

```ini
[Service]
# Cgroup-based resource limits
CPUQuota=200%
MemoryMax=2G
MemorySwapMax=0
TasksMax=512
IOWeight=100

# Filesystem namespace restrictions
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/app /var/log/app
PrivateTmp=true
PrivateDevices=true

# Capability and system call filtering
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
SystemCallFilter=@system-service
SystemCallArchitectures=native

# Network namespace isolation
PrivateNetwork=false
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
```

`ProtectSystem=strict` remounts the entire filesystem hierarchy read-only for the service's filesystem namespace, with exceptions for `/proc`, `/dev`, and any paths listed in `ReadWritePaths=`. Combined with `PrivateTmp=true`, which gives the service an isolated `/tmp` backed by a new tmpfs mount, these directives constrain the blast radius of a compromised service process without container overhead, using only Linux mount namespaces.

`SystemCallFilter=@system-service` restricts the service to a curated set of system calls appropriate for well-behaved daemons. Systemd maintains named filter sets (prefixed with `@`) that group related syscalls: `@system-service` excludes `ptrace`, `mount`, `reboot`, kernel module operations, and other syscalls that a normal application daemon has no business invoking. A service that attempts a filtered syscall receives `EPERM`, which typically causes it to crash in a contained way rather than succeed in an unexpected operation.

### Debugging Activation Failures

When a service fails to activate, the diagnostic workflow proceeds through three layers. The first layer is the journal:

```bash
# Show all log entries for a unit, most recent first
journalctl -u app-server.service -r

# Follow a service's journal output during startup
journalctl -u app-server.service -f

# Show the last 50 lines including kernel and systemd messages
journalctl -u app-server.service -n 50 --no-pager

# Show only error and critical messages across all units
journalctl -p err..emerg -b
```

The second layer is unit status introspection:

```bash
# Full unit status including active state, cgroup membership, recent log
systemctl status app-server.service

# Show all properties of a unit as key-value pairs
systemctl show app-server.service

# List all jobs currently in the job queue
systemctl list-jobs

# Show dependency tree from a unit
systemctl list-dependencies app-server.service --all
```

The third layer is dependency graph validation for cases where a unit never enters `activating` state despite being requested. If `systemctl start app-server.service` returns immediately without the service reaching `active`, the transaction may have been merged, conflicted, or the unit may be masked. The distinction between `masked` and `disabled` is critical: a disabled unit has no `[Install]` symlinks but can still be started manually. A masked unit has its unit file replaced by a symlink to `/dev/null`, which causes any attempt to start it, whether manual or via dependency, to fail immediately with `Unit app-server.service is masked`. Masking is the correct mechanism for permanently preventing a unit from running, and it cannot be overridden by dependency resolution.

### Failure Propagation and Restart Policy

The interaction between restart policy in the `[Service]` section and dependency propagation in the `[Unit]` section creates subtle failure modes that cause production incidents. The `Restart=on-failure` directive instructs systemd to restart the service's main process when it exits with a non-zero exit code, with timing controlled by `RestartSec=`. This restart happens outside the normal transaction engine: it is a local unit-level policy, not a graph operation.

The dangerous edge case is a service that restarts repeatedly in a tight loop. Systemd applies a rate limiter controlled by `StartLimitIntervalSec=` and `StartLimitBurst=`: if the service is started more than `Burst` times within `IntervalSec` seconds, systemd stops attempting restarts and transitions the unit to `failed`. At that point, any unit that declared `Requires=` on this service will also transition to `failed`, propagating the failure through the dependency graph.

The correct production configuration for a service that should be kept running indefinitely is to combine conservative restart timing with an explicit acknowledgment of rate limiting:

```ini
[Service]
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=120
StartLimitBurst=5
StartLimitAction=reboot-force
```

`StartLimitAction=reboot-force` causes the system to perform an immediate non-graceful reboot when the rate limit is hit, which is the appropriate response for a service whose continued operation is a system invariant. For less critical services, `StartLimitAction=none` disables the automatic transition to `failed` after the burst limit, though this can mask persistent configuration errors that need human intervention.

The property that distinguishes well-architected systemd configurations from haphazard ones is the same property that distinguishes well-designed distributed systems: explicit declarations of dependency and failure semantics rather than implicit assumptions about ordering and state. Every `After=` and `Requires=` clause is a theorem about system invariants. The dependency graph is not documentation; it is the specification from which systemd derives its operational behavior, and its correctness determines whether your system boots reliably, restarts cleanly, and fails in containable ways.
