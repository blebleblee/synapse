# Operational Verification Labs: Docker

## Objective & Environment Setup

Docker has become the de facto standard for application containerization, abstracting away the complexity of Linux kernel primitives—namespaces, cgroups, union filesystems, and network isolation—into a declarative interface that developers and operators can reason about. Yet beneath this abstraction lies a sophisticated runtime architecture built on containerd, runc, and the Linux kernel itself. When containers fail to start, networks become unreachable, or resource limits behave unexpectedly, operators must pierce through the abstraction and engage directly with the underlying mechanisms.

This laboratory guide equips infrastructure practitioners with the diagnostic rigor required to verify Docker's operational integrity in production environments. You will learn to inspect the container lifecycle from image pull through runtime execution, profile resource consumption against kernel-imposed limits, inject deliberate failures to validate recovery pathways, and construct a mental model of how Docker translates high-level API calls into low-level kernel operations. The exercises assume a Linux host with Docker Engine installed and root or sudo privileges, as many diagnostic operations require access to kernel subsystems and privileged namespaces.

Begin by establishing your baseline environment. Install Docker Engine following the official distribution-specific instructions, ensuring you have at least version 20.10 or later to access modern containerd integration and cgroup v2 support. Verify the installation by checking the daemon status and client connectivity. The Docker daemon, `dockerd`, orchestrates container lifecycle operations by delegating to containerd, which in turn invokes runc to spawn isolated processes. Understanding this delegation chain is critical for diagnosing failures at the correct layer.

```bash
# Verify Docker daemon status and version
sudo systemctl status docker
docker version
docker info
```

The `docker info` command reveals essential configuration details: storage driver (overlay2, btrfs, devicemapper), logging driver (json-file, journald, syslog), cgroup driver (cgroupfs or systemd), and containerd runtime socket location. Note the storage driver carefully, as it determines how container image layers are managed on disk. The overlay2 driver, which uses the Linux OverlayFS union filesystem, is the recommended choice for modern kernels due to its performance characteristics and efficient copy-on-write semantics.

Install supplementary diagnostic tools that provide visibility into kernel subsystems and network stack behavior. The `iproute2` package supplies `ip` and `ss` for network namespace inspection. The `perf` suite enables CPU profiling and system call tracing. The `strace` utility allows you to observe system calls made by container processes. The `tcpdump` packet analyzer lets you capture and inspect network traffic between containers and the host. Finally, `bpftool` provides introspection into eBPF programs if your kernel supports them, which Docker and containerd increasingly leverage for resource accounting and network policy enforcement.

```bash
# Install diagnostic toolchain on Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y iproute2 net-tools tcpdump strace linux-perf bpftool ethtool

# Install diagnostic toolchain on RHEL/CentOS/Fedora
sudo dnf install -y iproute net-tools tcpdump strace perf bpftool ethtool
```

Configure your shell environment to enable efficient workflow. Many Docker commands require elevated privileges, so consider adding your user to the `docker` group to avoid prefixing every command with `sudo`. Be mindful that group membership grants effective root access, as Docker's daemon socket provides unrestricted control over the host kernel's namespace and cgroup subsystems. In production environments, prefer explicit sudo invocations and audit all Docker API access through appropriate logging mechanisms.

```bash
# Add current user to docker group (logout required to take effect)
sudo usermod -aG docker $USER

# Verify group membership after re-login
groups
```

Establish a dedicated directory for this laboratory session where you will place Dockerfiles, test scripts, and diagnostic output. This workspace will accumulate logs, performance profiles, and network captures that serve as forensic artifacts when diagnosing container failures.

```bash
# Create laboratory workspace
mkdir -p ~/docker-verification-labs
cd ~/docker-verification-labs
```

With the environment prepared, you are ready to engage in rigorous operational verification. Each exercise builds upon the previous, constructing a comprehensive understanding of how Docker manages container isolation, resource allocation, and network connectivity through direct interaction with Linux kernel subsystems.

## Exercise 1: Live State & Internal Subsystem Inspection

The first step in mastering Docker diagnostics is learning to inspect the live state of running containers and their relationship to underlying kernel primitives. When a container appears to be running according to `docker ps` but exhibits unexpected behavior—network inaccessibility, missing filesystem mounts, or incorrect resource limits—you must verify that the kernel has correctly instantiated the intended isolation boundaries. This exercise teaches you to traverse the boundary between Docker's high-level API and the low-level process model, namespace hierarchy, and cgroup resource controllers that implement container isolation.

Begin by launching a long-running container that you can inspect without it immediately terminating. Use the official nginx image, which provides a well-behaved HTTP server that remains active until explicitly stopped. The nginx process will bind to port 80 inside the container's network namespace, giving you a concrete service to verify through multiple diagnostic lenses.

```bash
# Launch nginx container with explicit resource limits
docker run -d \
  --name lab-nginx \
  --memory=512m \
  --cpus=1.5 \
  --publish 8080:80 \
  nginx:latest

# Verify container is running
docker ps -a
```

The `docker ps` output shows the container ID (a hexadecimal identifier), image name, creation time, status, exposed ports, and assigned name. Note the `PORTS` column, which displays `0.0.0.0:8080->80/tcp`, indicating that the Docker daemon has configured iptables rules to forward traffic from the host's port 8080 to the container's port 80. This port forwarding mechanism relies on iptables NAT (Network Address Translation) chains that rewrite packet headers as they traverse network namespaces.

Now inspect the container's detailed configuration using `docker inspect`, which returns a comprehensive JSON document containing every aspect of the container's runtime state. This output includes network settings, mounted volumes, environment variables, resource limits translated into cgroup parameters, and the process ID (PID) of the containerized process as seen from the host's PID namespace.

```bash
# Retrieve full container configuration
docker inspect lab-nginx | jq '.[0] | {
  Id: .Id,
  State: .State,
  Pid: .State.Pid,
  NetworkSettings: .NetworkSettings.IPAddress,
  Memory: .HostConfig.Memory,
  NanoCpus: .HostConfig.NanoCpus
}'
```

The `State.Pid` field reveals the container's init process PID in the host namespace. This is the entry point you need to access the container's namespaces directly using Linux's `/proc` filesystem. Every process on Linux exposes its namespace memberships through symbolic links in `/proc/<pid>/ns/`, where each link points to a kernel namespace object identified by an inode number. Containers sharing the same namespace will show identical inode numbers, while isolated containers will have distinct values.

Examine the container's namespace configuration by reading these symbolic links. The mount namespace (`mnt`) isolates the container's filesystem view, the network namespace (`net`) provides an independent network stack, the PID namespace (`pid`) creates a separate process ID space, the IPC namespace (`ipc`) isolates System V IPC and POSIX message queues, the UTS namespace (`uts`) allows independent hostname and domain name, and the user namespace (`user`) enables UID/GID remapping for rootless containers.

```bash
# Extract container PID
CONTAINER_PID=$(docker inspect -f '{{.State.Pid}}' lab-nginx)
echo "Container PID: $CONTAINER_PID"

# Inspect namespace memberships
sudo ls -la /proc/$CONTAINER_PID/ns/

# Compare container network namespace to host
readlink /proc/$CONTAINER_PID/ns/net
readlink /proc/self/ns/net
```

The network namespace warrants particular scrutiny because it underpins container connectivity. Docker creates a virtual Ethernet pair (veth pair) for each container, with one end attached to the container's network namespace and the other connected to the `docker0` bridge on the host. Packets transmitted from the container traverse the veth pair, cross the bridge, and are either forwarded to another container or routed through the host's network stack via iptables rules and IP masquerading.

Enumerate the network interfaces inside the container's namespace using `nsenter`, a utility that executes commands within specified namespaces. This allows you to run standard network diagnostic tools like `ip` and `ss` as if you were inside the container, but from the host's perspective.

```bash
# Enter container's network namespace and list interfaces
sudo nsenter -t $CONTAINER_PID -n ip addr show

# Display routing table inside container namespace
sudo nsenter -t $CONTAINER_PID -n ip route show

# Show listening sockets inside container
sudo nsenter -t $CONTAINER_PID -n ss -tlnp
```

The `ip addr show` output inside the container reveals at minimum two interfaces: `lo` (the loopback interface) and `eth0` (the veth endpoint). The `eth0` interface will have an IP address allocated from Docker's default subnet, typically `172.17.0.0/16`. The routing table will show a default route pointing to the Docker bridge gateway, usually `172.17.0.1`. The `ss -tlnp` command displays TCP listening sockets, where you should observe nginx bound to `0.0.0.0:80`, confirming it is ready to accept connections on all interfaces within the container's namespace.

To understand how packets reach the container from the host, trace the veth pair from the host side. Each veth interface is paired, and you can identify the peer using the `ip link` command with the interface index. The container's `eth0` corresponds to a `veth` interface on the host, typically named `veth<random>`, which is enslaved to the `docker0` bridge.

```bash
# Find veth peer on host connected to container
sudo ip link | grep -A 1 veth

# Show docker0 bridge configuration
ip addr show docker0

# Display bridge forwarding database (MAC address table)
bridge fdb show br docker0
```

The bridge forwarding database maps MAC addresses to bridge ports, revealing which veth interfaces are attached and where packets destined for the container's MAC address will be forwarded. This is the Layer 2 switching fabric that enables inter-container communication on the same Docker network.

Next, examine how Docker enforces resource limits using Linux cgroups (control groups). Cgroups are hierarchical structures in the kernel that track and constrain resource consumption for process groups. Docker creates a cgroup hierarchy for each container under `/sys/fs/cgroup/`, with separate controllers for memory, CPU, block I/O, and network. Modern systems may use cgroup v1 (multiple hierarchies) or cgroup v2 (unified hierarchy); Docker adapts its behavior accordingly.

Locate the container's cgroup directories and inspect the memory and CPU limit files. The memory controller exposes files like `memory.limit_in_bytes` (cgroup v1) or `memory.max` (cgroup v2) that specify the hard memory cap, and `memory.usage_in_bytes` or `memory.current` showing real-time consumption. The CPU controller uses `cpu.cfs_quota_us` and `cpu.cfs_period_us` (v1) or `cpu.max` (v2) to implement Completely Fair Scheduler (CFS) bandwidth control, ensuring the container cannot exceed its allocated CPU time slices.

```bash
# Determine cgroup version
stat -fc %T /sys/fs/cgroup/

# For cgroup v1 (shows 'tmpfs')
CGROUP_MEMORY=/sys/fs/cgroup/memory/docker/$CONTAINER_ID
CGROUP_CPU=/sys/fs/cgroup/cpu/docker/$CONTAINER_ID

# For cgroup v2 (shows 'cgroup2fs')
CGROUP_BASE=/sys/fs/cgroup/system.slice/docker-$CONTAINER_ID.scope

# Inspect memory limits (adjust path based on cgroup version)
# cgroup v1:
sudo cat /sys/fs/cgroup/memory/docker/$(docker inspect -f '{{.Id}}' lab-nginx)/memory.limit_in_bytes
sudo cat /sys/fs/cgroup/memory/docker/$(docker inspect -f '{{.Id}}' lab-nginx)/memory.usage_in_bytes

# cgroup v2:
CONTAINER_FULL_ID=$(docker inspect -f '{{.Id}}' lab-nginx)
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/memory.max
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/memory.current
```

The memory limit should match the `--memory=512m` parameter you specified during `docker run`, translated to bytes (536870912). If the container attempts to allocate memory beyond this limit, the kernel's out-of-memory (OOM) killer will terminate processes within the cgroup, preserving system stability at the expense of the container's availability.

Verify CPU limit enforcement by examining the CFS quota parameters. Docker translates the `--cpus=1.5` flag into a quota-to-period ratio: with a default period of 100ms (100,000 microseconds), a limit of 1.5 CPUs corresponds to a quota of 150ms (150,000 microseconds). This means the container's processes can consume up to 150ms of CPU time every 100ms period, effectively utilizing 1.5 CPU cores worth of processing capacity.

```bash
# Inspect CPU limits (cgroup v1)
sudo cat /sys/fs/cgroup/cpu/docker/$CONTAINER_FULL_ID/cpu.cfs_quota_us
sudo cat /sys/fs/cgroup/cpu/docker/$CONTAINER_FULL_ID/cpu.cfs_period_us

# Inspect CPU limits (cgroup v2)
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/cpu.max
```

Cgroup v2 presents these values in a single file as `$QUOTA $PERIOD`, for example `150000 100000`. The ratio determines the effective CPU limit: `150000 / 100000 = 1.5` CPUs.

To observe namespace isolation in action, execute a shell inside the running container using `docker exec`, which spawns a new process inside the container's existing namespaces. From within this shell, examine the process tree, filesystem layout, network configuration, and hostname, all of which should reflect the isolated environment rather than the host's state.

```bash
# Execute interactive shell inside container
docker exec -it lab-nginx /bin/bash

# Inside container: inspect process tree (only containerized processes visible)
ps aux

# Inside container: check hostname (matches container ID or --hostname flag)
hostname

# Inside container: view filesystem root (overlay mount)
df -h /

# Inside container: confirm isolated network namespace
ip addr show

# Exit container shell
exit
```

The `ps aux` output inside the container shows only processes running within the container's PID namespace. The nginx master and worker processes will be visible with PIDs starting from 1, despite having entirely different PIDs in the host namespace. The hostname will match the container ID's short form unless overridden with the `--hostname` flag. The filesystem root will show an OverlayFS mount representing the union of the image's read-only layers and the container's read-write layer, isolated from the host's filesystem.

Finally, trace the complete path of an HTTP request from an external client through the host's network stack, across the Docker bridge, and into the container. Use `tcpdump` to capture packets on both the host's external interface and the veth pair, observing how NAT rules rewrite the destination address and port as the packet traverses namespaces.

```bash
# Start packet capture on host's external interface (adjust interface name)
sudo tcpdump -i eth0 -n tcp port 8080 -w host-external.pcap &
TCPDUMP_PID=$!

# Start packet capture on docker0 bridge
sudo tcpdump -i docker0 -n -w docker-bridge.pcap &
TCPDUMP2_PID=$!

# Generate HTTP request from another terminal or machine
curl http://localhost:8080

# Stop packet captures
sudo kill $TCPDUMP_PID $TCPDUMP2_PID

# Analyze captured packets
tcpdump -r host-external.pcap -nn
tcpdump -r docker-bridge.pcap -nn
```

In the `host-external.pcap` capture, you will see packets with destination port 8080 arriving at the host's IP address. In the `docker-bridge.pcap` capture, those same packets reappear with the destination IP rewritten to the container's IP address (`172.17.0.x`) and destination port rewritten to 80, demonstrating Docker's iptables DNAT (Destination NAT) rule in action. This NAT translation is the mechanism by which Docker implements port publishing, allowing containers to expose services without requiring direct host-network mode.

Examine the iptables rules Docker has created to enable this translation. Docker inserts rules into the `nat` table's `PREROUTING` and `POSTROUTING` chains, as well as the `filter` table's `FORWARD` chain. These rules intercept packets, rewrite addresses, and enforce network policy before the kernel's routing decision.

```bash
# Display NAT rules for port forwarding
sudo iptables -t nat -L -n -v | grep 8080

# Display DOCKER chain in filter table
sudo iptables -t filter -L DOCKER -n -v

# Display DOCKER chain in nat table
sudo iptables -t nat -L DOCKER -n -v
```

You should observe a DNAT rule that matches packets destined for the host's IP on port 8080 and redirects them to the container's IP on port 80. Additionally, a MASQUERADE rule in the `POSTROUTING` chain ensures that packets originating from the container and destined for external networks have their source address rewritten to the host's IP, enabling return traffic to route correctly.

This deep inspection establishes a foundational understanding: Docker containers are not virtual machines with emulated hardware, but rather isolated process groups governed by kernel namespaces and cgroups, connected via virtual Ethernet pairs and managed by iptables rules. When containers misbehave, you can now systematically verify each isolation boundary—namespace membership, cgroup limits, network interfaces, and packet forwarding rules—to identify where the actual state diverges from the intended configuration.

## Exercise 2: Benchmarking & Saturation Profiling

Understanding Docker's performance characteristics under load requires moving beyond static inspection to dynamic profiling under controlled saturation conditions. Containers are frequently deployed with resource limits intended to ensure fair sharing in multi-tenant environments, but misconfigured limits can cause cryptic failures: applications that hang, requests that timeout, or processes that crash without informative error messages. This exercise teaches you to measure container resource consumption, induce saturation conditions, and correlate high-level application behavior with low-level kernel metrics.

Construct a test container that allows you to programmatically saturate CPU, memory, disk I/O, and network bandwidth. The `stress-ng` utility is purpose-built for this task, providing fine-grained control over workload characteristics. Build a custom Docker image that includes stress-ng and auxiliary diagnostic tools, ensuring you can reproduce stress tests across environments.

Create a Dockerfile that packages stress-ng and related utilities into a container image:

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    stress-ng \
    sysstat \
    iproute2 \
    iperf3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
```

Build and tag this image for use in subsequent stress tests:

```bash
# Build stress test container image
docker build -t stress-test:latest -f- . <<'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    stress-ng \
    sysstat \
    iproute2 \
    iperf3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
EOF

# Verify image creation
docker images stress-test
```

Launch a stress test container with explicit CPU and memory limits that you will intentionally exceed to observe enforcement behavior. Set the CPU limit to 1.0 CPU and memory limit to 256 MiB, constraints that are easily saturated by stress-ng's workload generators.

```bash
# Launch stress container with restrictive resource limits
docker run -d \
  --name lab-stress \
  --memory=256m \
  --memory-swap=256m \
  --cpus=1.0 \
  stress-test:latest \
  sleep infinity

# Verify container is running
docker ps -f name=lab-stress
```

Begin CPU saturation profiling by spawning multiple worker threads within the container, each executing tight arithmetic loops designed to maximize CPU utilization. Use stress-ng's `--cpu` stressor with a worker count exceeding the CPU limit to force CFS throttling.

```bash
# Saturate CPU with 4 workers (exceeding 1.0 CPU limit)
docker exec -d lab-stress stress-ng --cpu 4 --cpu-method all --timeout 60s

# Monitor CPU throttling in real-time
watch -n 1 "docker stats lab-stress --no-stream"
```

The `docker stats` command displays real-time resource consumption, including CPU percentage, memory usage, network I/O, and block I/O. Observe that the CPU percentage plateaus near 100% despite having four workers attempting to consume more. This ceiling is the CFS throttle in action: the kernel tracks each cgroup's cumulative CPU time consumption per period, and when the quota is exhausted, it dequeues the cgroup's tasks from the scheduler's run queue until the next period begins.

Validate this throttling behavior by inspecting the cgroup's CPU statistics, which expose throttling counters maintained by the kernel. The `cpu.stat` file (cgroup v1) or `cpu.stat` within the unified hierarchy (cgroup v2) reports the number of throttling periods (`nr_throttled`) and the total time processes were throttled (`throttled_time`).

```bash
# Extract container cgroup CPU statistics (cgroup v2)
CONTAINER_FULL_ID=$(docker inspect -f '{{.Id}}' lab-stress)
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/cpu.stat

# Continuously monitor throttling events
watch -n 1 "sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/cpu.stat | grep throttled"
```

You should observe `nr_throttled` incrementing steadily and `throttled_time` accumulating microseconds, confirming that the kernel is actively enforcing the CPU quota. This throttling manifests as latency spikes and reduced throughput in latency-sensitive applications, making it critical to right-size CPU limits based on actual workload profiles.

Next, induce memory pressure to observe the OOM killer's behavior when a container exceeds its memory limit. Memory limits in Docker are hard constraints: unlike CPU limits, which throttle but allow continued execution, memory limits trigger immediate process termination when breached. The kernel's OOM killer selects a victim process within the cgroup based on heuristics like memory consumption, process age, and OOM score adjustments.

```bash
# Allocate memory exceeding the 256 MiB limit
docker exec -d lab-stress stress-ng --vm 1 --vm-bytes 512m --vm-method all --timeout 30s

# Monitor memory usage and watch for OOM kill
docker stats lab-stress --no-stream

# Check for OOM kill events in kernel logs
sudo dmesg | grep -i "oom.*lab-stress"
```

Within seconds, you should observe the stress-ng process being killed. The `docker stats` output will show memory usage approaching the limit, then resetting as the process is terminated. The kernel log (`dmesg`) will contain an entry indicating the OOM killer invoked the `oom_reaper` to reclaim memory, listing the killed process and its OOM score. Docker itself will detect the exit due to signal 9 (SIGKILL) and may restart the container depending on the restart policy.

Inspect the container's memory cgroup to observe the `oom_control` and `memory.events` (cgroup v2) or `memory.oom_control` (cgroup v1) files, which record OOM events and allow you to configure OOM killer behavior.

```bash
# Check memory events for OOM occurrences (cgroup v2)
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/memory.events | grep oom

# Display OOM kill count
docker inspect lab-stress -f '{{.State.OOMKilled}}'
```

The `memory.events` file increments counters like `oom_kill` each time the kernel terminates a process due to memory pressure. This counter is invaluable for diagnosing intermittent application crashes that occur without clear application logs, as the OOM kill may appear as a sudden SIGKILL with no stack trace.

Proceed to disk I/O saturation profiling by writing large amounts of data to the container's filesystem, observing how the storage driver handles concurrent writes and how block I/O throttling (if configured) shapes throughput. Docker's overlay2 storage driver uses OverlayFS, which merges read-only image layers with a read-write layer, introducing copy-on-write overhead on first modification of a file from a lower layer.

```bash
# Saturate disk I/O with sequential writes
docker exec -d lab-stress stress-ng --hdd 2 --hdd-bytes 1G --timeout 60s

# Monitor block I/O in real-time
docker stats lab-stress --no-stream --format "table {{.Container}}\t{{.BlockIO}}"

# Inspect block I/O throttle settings (if configured)
docker inspect lab-stress -f '{{.HostConfig.BlkioWeight}}'
```

The `docker stats` output shows cumulative block I/O read and write bytes. Unlike CPU and memory, Docker does not apply default disk I/O limits unless explicitly configured via `--device-read-bps`, `--device-write-bps`, or `--blkio-weight` flags. Without these limits, containers can monopolize disk bandwidth, starving other containers or the host's own I/O operations.

You can optionally configure I/O limits and observe throttling by recreating the container with explicit constraints:

```bash
# Stop and remove existing stress container
docker stop lab-stress
docker rm lab-stress

# Launch with disk I/O throttle (limit writes to 10 MB/s)
docker run -d \
  --name lab-stress \
  --memory=256m \
  --cpus=1.0 \
  --device-write-bps /dev/sda:10mb \
  stress-test:latest \
  sleep infinity

# Re-run disk I/O stress test
docker exec -d lab-stress stress-ng --hdd 2 --hdd-bytes 1G --timeout 60s

# Observe throttled write rate
docker stats lab-stress --no-stream --format "table {{.Container}}\t{{.BlockIO}}"
```

The write rate should now be capped near 10 MB/s, demonstrating that the kernel's block I/O controller is enforcing the configured limit. This throttling is implemented via the `blkio` cgroup controller, which tracks per-device I/O and delays I/O requests when quotas are exceeded.

Finally, benchmark network throughput between two containers to measure the overhead of virtual Ethernet pairs and bridge forwarding. Network performance in Docker is generally excellent for local container-to-container communication, as packets traverse only the kernel's software bridge without leaving the host. However, packet forwarding, NAT, and iptables rule evaluation introduce latency and CPU overhead that can become bottlenecks under high throughput or high packet-per-second (PPS) workloads.

Launch a second container running an `iperf3` server to act as the network benchmark target:

```bash
# Launch iperf3 server container
docker run -d \
  --name lab-iperf-server \
  --network bridge \
  stress-test:latest \
  iperf3 -s

# Verify server is listening
docker exec lab-iperf-server ss -tlnp | grep 5201
```

From the stress container, run an `iperf3` client test to measure TCP throughput between containers on the same Docker bridge network:

```bash
# Retrieve iperf3 server container IP address
SERVER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lab-iperf-server)

# Run iperf3 client benchmark (10-second test)
docker exec lab-stress iperf3 -c $SERVER_IP -t 10

# Run UDP benchmark to measure packet loss and jitter
docker exec lab-stress iperf3 -c $SERVER_IP -u -b 1G -t 10
```

The iperf3 output reports TCP throughput in Gbps or Mbps, typically achieving near line-rate for local bridge networking on modern hosts. UDP tests reveal packet loss and jitter metrics, which are sensitive to CPU scheduling and buffer sizes. Compare these results to host-to-host throughput over physical NICs to quantify the overhead of Docker's networking stack.

Use `perf` to profile CPU usage during the network benchmark, identifying whether the bottleneck is in the kernel's networking stack, iptables rule evaluation, or the veth pair's packet forwarding logic:

```bash
# Profile CPU during iperf3 test
sudo perf record -a -g -- sleep 10 &
PERF_PID=$!

# Run iperf3 test during profiling
docker exec lab-stress iperf3 -c $SERVER_IP -t 10

# Wait for perf to complete
wait $PERF_PID

# Generate perf report
sudo perf report --stdio | head -50
```

The `perf report` flame graph will highlight hot functions in the kernel, such as `ip_forward`, `nf_hook_slow` (iptables), `__netif_receive_skb`, and `dev_queue_xmit`. High sample counts in `nf_hook_slow` indicate iptables overhead, while time spent in `tcp_sendmsg` or `tcp_recvmsg` points to TCP stack processing. This granular visibility allows you to correlate application-level throughput with kernel-level execution paths, informing decisions about network mode selection (bridge vs. host vs. macvlan) and iptables rule optimization.

Aggregate your findings into a performance profile for the container, documenting the resource consumption baseline, saturation thresholds, and observed kernel enforcement behaviors. This profile serves as a reference when sizing production workloads, ensuring that resource limits are neither so restrictive that they cause throttling under normal load, nor so permissive that they allow runaway processes to destabilize the host.

```bash
# Generate comprehensive resource consumption report
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" > container-resource-profile.txt

# Capture cgroup statistics for forensic analysis
CONTAINER_FULL_ID=$(docker inspect -f '{{.Id}}' lab-stress)
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/cpu.stat > cpu-stat.txt
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_FULL_ID.scope/memory.stat > memory-stat.txt

# Archive diagnostic artifacts
tar -czf saturation-profile-$(date +%Y%m%d-%H%M%S).tar.gz \
  container-resource-profile.txt \
  cpu-stat.txt \
  memory-stat.txt \
  host-external.pcap \
  docker-bridge.pcap
```

Clean up the stress test containers to free resources:

```bash
# Stop and remove stress containers
docker stop lab-stress lab-iperf-server
docker rm lab-stress lab-iperf-server
```

This exercise equips you with the methodology to quantify Docker's resource management overhead, identify performance bottlenecks at the kernel level, and tune container configurations for optimal throughput and latency. The ability to correlate high-level metrics like `docker stats` output with low-level cgroup counters and perf profiles is essential for operating containerized workloads at scale.

## Exercise 3: Fault Injection & Recovery Analysis

Production container environments must tolerate a spectrum of failures: network partitions, resource exhaustion, daemon crashes, and corrupted filesystem state. Docker provides restart policies, health checks, and logging mechanisms to recover from failures automatically, but understanding the recovery pathways requires deliberately inducing faults and observing the system's response. This exercise guides you through systematic fault injection targeting different failure modes, teaching you to distinguish between transient failures that self-heal and persistent failures that require operator intervention.

Begin by launching a container with a restart policy that instructs Docker to automatically restart the container upon exit. The `unless-stopped` policy is particularly useful for long-running services, as it will restart the container on daemon restarts or after crashes, but respects explicit `docker stop` commands.

```bash
# Launch container with automatic restart on failure
docker run -d \
  --name lab-fault-injection \
  --restart unless-stopped \
  --memory=256m \
  --cpus=1.0 \
  nginx:latest

# Verify container is running
docker ps -f name=lab-fault-injection
```

Inject a process-level fault by forcibly killing the nginx master process inside the container using `docker exec` to send a SIGKILL signal. This simulates an application crash due to a segmentation fault, unhandled exception, or manual kill command.

```bash
# Identify nginx master process PID inside container
docker exec lab-fault-injection ps aux | grep "nginx: master"

# Kill nginx master process
docker exec lab-fault-injection kill -9 1

# Observe container restart
docker ps -a -f name=lab-fault-injection
```

Docker detects that the container's init process (PID 1) has exited and immediately invokes the restart policy. The `docker ps` output will briefly show the container in an `Exited` state, then transition back to `Up` as Docker recreates the container. Inspect the container's restart count to confirm that recovery occurred:

```bash
# Check restart count
docker inspect lab-fault-injection -f '{{.RestartCount}}'

# View container event log showing stop and start events
docker events --since 5m --filter "container=lab-fault-injection"
```

The `RestartCount` field increments with each automatic restart. The `docker events` stream shows timestamped events: `die`, `stop`, and `start`, providing a timeline of the container lifecycle. This event log is critical for correlating container restarts with external events like host resource pressure or network failures.

Examine the container logs to determine whether application state was preserved across the restart. For stateless applications like nginx serving static content, restarts are transparent to clients after a brief unavailability window. For stateful applications, restart behavior depends on whether persistent volumes are mounted and whether the application implements crash recovery logic.

```bash
# Retrieve container logs, including logs from before the restart
docker logs lab-fault-injection --tail 50

# Verify nginx restarted cleanly
docker exec lab-fault-injection curl -s http://localhost:80 | head -5
```

Next, induce a resource exhaustion fault by forcing the container to exceed its memory limit, triggering the OOM killer. Unlike the previous fault where the restart policy recovered the container, OOM kills can indicate systemic under-provisioning that will recur unless the root cause—either excessive application memory usage or insufficient limits—is addressed.

```bash
# Trigger OOM kill by allocating excessive memory
docker exec -d lab-fault-injection stress-ng --vm 1 --vm-bytes 512m --timeout 30s

# Monitor container status during OOM
watch -n 1 "docker ps -a -f name=lab-fault-injection"

# Check if container was OOM killed
docker inspect lab-fault-injection -f '{{.State.OOMKilled}}'
```

The container should restart automatically after the OOM kill, as the restart policy treats OOM kills as a failure condition. However, if the memory limit is too restrictive for the application's working set, the container will enter a crash loop, repeatedly starting and being OOM killed. To diagnose this, examine the time between restarts, which Docker exponentially backs off to avoid rapid restart storms.

```bash
# View restart timestamps
docker inspect lab-fault-injection -f '{{.State.StartedAt}} {{.State.FinishedAt}}'

# Calculate time between restarts
docker inspect lab-fault-injection --format='{{json .State}}' | jq '{StartedAt, FinishedAt, RestartCount}'
```

If the restart interval grows exponentially (Docker's default backoff policy), the container is repeatedly failing to remain stable. Resolve this by increasing the memory limit or modifying the application to reduce memory consumption.

Inject a network partition fault by manipulating iptables rules to drop packets to and from the container, simulating a network outage or misconfigured firewall. This tests whether the application gracefully handles connection timeouts and whether clients can recover once connectivity is restored.

```bash
# Block all traffic to/from container
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' lab-fault-injection)
sudo iptables -I DOCKER-USER -s $CONTAINER_IP -j DROP
sudo iptables -I DOCKER-USER -d $CONTAINER_IP -j DROP

# Verify network partition
docker exec lab-fault-injection ping -c 3 8.8.8.8

# Attempt to access nginx from host (should timeout)
curl --max-time 5 http://$CONTAINER_IP:80
```

The ping and curl commands should fail due to the iptables DROP rules. Observe application behavior during this partition: does nginx log connection attempts? Does it degrade gracefully, or does it accumulate resource leaks?

Restore network connectivity and verify the container recovers without requiring a restart:

```bash
# Remove iptables DROP rules
sudo iptables -D DOCKER-USER -s $CONTAINER_IP -j DROP
sudo iptables -D DOCKER-USER -d $CONTAINER_IP -j DROP

# Verify connectivity restored
docker exec lab-fault-injection ping -c 3 8.8.8.8
curl http://$CONTAINER_IP:80
```

The application should immediately respond to new requests without manual intervention, demonstrating stateless recovery from network partitions.

Inject a Docker daemon fault by stopping the dockerd process and observing container behavior. Containers managed by containerd continue running when dockerd stops, as containerd operates as a separate daemon. However, Docker API operations like `docker ps`, `docker exec`, and `docker logs` will fail until dockerd is restarted.

```bash
# Stop Docker daemon
sudo systemctl stop docker

# Verify dockerd is stopped
sudo systemctl status docker

# Attempt Docker API operations (should fail)
docker ps

# Verify container process is still running on host
ps aux | grep nginx | grep -v grep

# Restart Docker daemon
sudo systemctl start docker

# Verify Docker API restored
docker ps -f name=lab-fault-injection
```

The nginx process persists because containerd, not dockerd, manages the container runtime. This separation of concerns ensures that Docker daemon upgrades and restarts do not disrupt running containers, a critical property for zero-downtime operations.

Inject a filesystem fault by filling the container's writable layer to capacity, simulating disk exhaustion. Docker's overlay2 storage driver allocates a writable layer atop the read-only image layers, and this writable layer shares the host's filesystem. When the host filesystem fills, container write operations fail with `ENOSPC` (no space left on device).

```bash
# Fill container filesystem by writing large file
docker exec lab-fault-injection dd if=/dev/zero of=/tmp/fill bs=1M count=10000 || true

# Verify disk space exhaustion
docker exec lab-fault-injection df -h /

# Observe application behavior under ENOSPC
docker logs lab-fault-injection --tail 20
```

Applications that do not handle `ENOSPC` gracefully may crash or enter undefined states. Nginx, for example, may fail to write access logs or cache files, but continue serving requests from memory. Recover by removing the large file:

```bash
# Remove fill file to free space
docker exec lab-fault-injection rm -f /tmp/fill

# Verify filesystem space recovered
docker exec lab-fault-injection df -h /
```

Finally, validate Docker's health check mechanism by configuring a custom health check that executes a command inside the container at regular intervals. Docker marks the container as unhealthy if the health check fails consecutively, allowing orchestration systems like Kubernetes or Docker Swarm to replace unhealthy containers.

```bash
# Stop and remove existing container
docker stop lab-fault-injection
docker rm lab-fault-injection

# Launch container with custom health check
docker run -d \
  --name lab-fault-injection \
  --restart unless-stopped \
  --health-cmd="curl -f http://localhost:80 || exit 1" \
  --health-interval=10s \
  --health-timeout=5s \
  --health-retries=3 \
  nginx:latest

# Monitor health status
watch -n 2 "docker ps -f name=lab-fault-injection | grep -E 'STATUS|lab-fault'"
```

The `STATUS` column will display `health: starting` initially, then transition to `healthy` once the health check succeeds. Inject a fault by stopping nginx inside the container:

```bash
# Stop nginx to trigger health check failure
docker exec lab-fault-injection nginx -s stop

# Observe container transitioning to unhealthy
watch -n 2 "docker ps -f name=lab-fault-injection"
```

After three consecutive health check failures, Docker marks the container as `unhealthy`. The restart policy will trigger, restarting the container and restoring nginx.

Inspect the health check logs to understand the failure timeline:

```bash
# View health check results
docker inspect lab-fault-injection --format='{{json .State.Health}}' | jq
```

The `State.Health` object contains an array of recent health check results, each with an exit code, output, and timestamp. This detailed logging is essential for diagnosing intermittent failures that do not correlate with obvious resource exhaustion or network issues.

Clean up the fault injection container:

```bash
# Stop and remove container
docker stop lab-fault-injection
docker rm lab-fault-injection
```

This exercise demonstrates Docker's resilience mechanisms and exposes their limitations. Restart policies recover from process crashes and OOM kills but cannot resolve systemic under-provisioning. Health checks detect application-level failures but rely on well-designed check commands. Network partitions are transparent to stateless applications but require careful timeout and retry logic in stateful systems. Operator skill in fault diagnosis determines whether failures result in brief service disruptions or prolonged outages.

## Diagnostic Cheat Sheet & Verification Checklist

This diagnostic reference consolidates the essential commands and verification steps for rapidly assessing Docker container health, isolating failure modes, and confirming that the system's actual state matches its intended configuration. Commit these patterns to memory so you can execute them reflexively during incident response.

**Container Lifecycle & State Inspection**

```bash
# List all containers (running and stopped)
docker ps -a

# Inspect full container configuration as JSON
docker inspect <container_name_or_id>

# Extract specific fields from inspection output
docker inspect -f '{{.State.Pid}}' <container>
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container>

# View container resource limits
docker inspect -f '{{.HostConfig.Memory}} {{.HostConfig.NanoCpus}}' <container>

# Check container restart count and OOM status
docker inspect -f '{{.RestartCount}} {{.State.OOMKilled}}' <container>

# View container event timeline
docker events --since 1h --filter "container=<container>"
```

**Namespace & Cgroup Inspection**

```bash
# Find container's host PID
CONTAINER_PID=$(docker inspect -f '{{.State.Pid}}' <container>)

# List container's namespace memberships
sudo ls -la /proc/$CONTAINER_PID/ns/

# Enter container's network namespace
sudo nsenter -t $CONTAINER_PID -n ip addr show
sudo nsenter -t $CONTAINER_PID -n ss -tlnp

# Inspect cgroup resource limits (cgroup v2)
CONTAINER_ID=$(docker inspect -f '{{.Id}}' <container>)
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_ID.scope/memory.max
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_ID.scope/cpu.max

# Monitor cgroup statistics for throttling
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_ID.scope/cpu.stat
sudo cat /sys/fs/cgroup/system.slice/docker-$CONTAINER_ID.scope/memory.events
```

**Network Connectivity & Packet Flow**

```bash
# Show Docker bridge configuration
ip addr show docker0
bridge fdb show br docker0

# Identify veth pair connected to container
sudo ip link | grep veth

# Display iptables NAT rules for port forwarding
sudo iptables -t nat -L DOCKER -n -v

# Capture packets on Docker bridge
sudo tcpdump -i docker0 -w docker-bridge.pcap

# Trace packet flow from host to container
sudo tcpdump -i any -n host <container_ip> -w packet-trace.pcap
```

**Resource Utilization & Performance Profiling**

```bash
# Real-time resource consumption
docker stats --no-stream
docker stats <container> --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Profile CPU during workload
sudo perf record -a -g -- sleep 10
sudo perf report --stdio

# Trace system calls made by container process
sudo strace -p $CONTAINER_PID -f -e trace=network,file

# Monitor disk I/O
iostat -x 1
```

**Fault Diagnosis & Recovery Verification**

```bash
# Check for OOM kill events in kernel log
sudo dmesg | grep -i "oom.*<container>"

# View container logs (including rotated logs)
docker logs <container> --timestamps --tail 100

# Execute command inside container for interactive diagnosis
docker exec -it <container> /bin/bash

# Verify health check status
docker inspect --format='{{json .State.Health}}' <container> | jq

# Restart container and observe recovery time
time docker restart <container>
```

**Storage Driver & Filesystem Inspection**

```bash
# Show storage driver configuration
docker info | grep -i storage

# Inspect overlay2 layers for container
sudo ls -la /var/lib/docker/overlay2/

# Check disk space usage by Docker
docker system df
docker system df -v

# Prune unused containers, images, and volumes
docker system prune -a --volumes
```

**Verification Checklist for Container Deployment**

When deploying a new container or debugging an existing one, systematically verify each isolation boundary:

1. **Process Isolation**: Confirm the container's init process (PID 1) is running and healthy via `docker exec <container> ps aux`.

2. **Namespace Isolation**: Verify distinct namespace IDs in `/proc/<pid>/ns/` compared to the host, ensuring mount, network, PID, IPC, UTS, and user namespaces are correctly isolated.

3. **Cgroup Resource Limits**: Confirm memory and CPU limits in cgroup files match the configured values, and check for throttling or OOM events.

4. **Network Connectivity**: Verify the container's IP address is allocated, default route is configured, veth pair is attached to the bridge, and iptables rules enable port forwarding if required.

5. **Filesystem Integrity**: Confirm the container's root filesystem is mounted as an overlay, check disk space availability, and verify volume mounts are present and writable.

6. **Log Availability**: Ensure container logs are being written via `docker logs` and that the logging driver is correctly configured for centralized log aggregation if used.

7. **Health Check Status**: If a health check is configured, verify it transitions to `healthy` state and does not oscillate due to misconfigured thresholds.

8. **Restart Policy Behavior**: Validate that the restart policy triggers correctly on process exit, OOM kill, and daemon restart by simulating each failure mode.

By executing this checklist, you establish a baseline of known-good state that can be referenced when troubleshooting deviations. The discipline of verification—confirming that intended configuration matches actual runtime state—is the foundation of reliable container operations. Docker abstracts kernel complexity, but when abstractions leak, the operator who understands the underlying mechanisms will diagnose and resolve failures an order of magnitude faster than one who treats containers as opaque black boxes.
