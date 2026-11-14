# Operational Verification Labs: OCI

## Objective & Environment Setup

The Open Container Initiative governs the container ecosystem through three interlocking specifications: the Runtime Specification, which defines how a container's filesystem, namespaces, cgroups, and process are assembled into a running isolated environment; the Image Specification, which defines how container filesystems and configuration are serialized into a content-addressable, layered archive; and the Distribution Specification, which defines how registries serve those images over HTTP. This lab series exercises all three layers against a live containerd runtime, tracing the full lifecycle from registry pull through image unpacking, namespace and cgroup construction, process execution, resource enforcement, and fault recovery. Every verification uses production diagnostic tools—crictl for the CRI interface, runc for the OCI runtime, skopeo for image and registry inspection, and kernel-level instruments including ip, ss, perf, strace, and bpftool for subsystem-level inspection.

The environment requires a Linux host running kernel 5.15 or later with cgroup v2 enabled, containerd as the container runtime, and the full diagnostic toolchain installed. The following setup script installs every required package and configures the containerd CRI socket for crictl access.

```bash
#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
  containerd runc skopeo iproute2 ethtool tcpdump strace \
  linux-tools-common linux-tools-$(uname -r) \
  bpfcc-tools jq curl libcap2-bin

CRICTL_VERSION="v1.29.0"
wget -qO /tmp/crictl.tar.gz \
  "https://github.com/kubernetes-sigs/cri-tools/releases/download/${CRICTL_VERSION}/crictl-${CRICTL_VERSION}-linux-amd64.tar.gz"
sudo tar -xzf /tmp/crictl.tar.gz -C /usr/local/bin
rm /tmp/crictl.tar.gz

sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd

sudo tee /etc/crictl.yaml >/dev/null <<'EOF'
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 30
debug: false
EOF

echo "=== cgroup v2 verification ==="
mount | grep cgroup2 | head -1
cat /sys/fs/cgroup/cgroup.controllers

echo "=== toolchain verification ==="
containerd --version
runc --version
crictl version
skopeo --version
crictl info | jq '.status'
```

After running the setup, confirm that `crictl info` returns the containerd runtime status and that `crictl images` executes without error, proving the CRI socket is reachable. The `cgroup.controllers` file should list `cpu`, `memory`, `io`, `pids`, and `rdma` at minimum, confirming that cgroup v2 resource controllers are available for the isolation and resource-limit exercises that follow.

## Exercise 1: Live State & Internal Subsystem Inspection

### Part A: OCI Image Format Verification

The OCI Image Specification defines a content-addressable image layout consisting of an `index.json` that references one or more manifests, each manifest in turn referencing a config blob and a set of layer blobs. Every artifact is identified by its SHA-256 digest, and the integrity of the entire image depends on the hash chain running from index through manifest through config and layers. The following procedure pulls an image into a local OCI image layout using `skopeo` and traverses the full digest chain by hand, verifying that every blob matches its declared hash and that the manifest's media types conform to the OCI specification rather than the legacy Docker v2 schema.

```bash
mkdir -p /tmp/oci-images
skopeo copy docker://docker.io/library/nginx:1.25-alpine \
  oci:/tmp/oci-images/nginx:latest

cat /tmp/oci-images/nginx/latest/oci-layout
# Expected: {"imageLayoutVersion":"1.0.0"}

cat /tmp/oci-images/nginx/latest/index.json | jq .

MANIFEST_DIGEST=$(cat /tmp/oci-images/nginx/latest/index.json \
  | jq -r '.manifests[0].digest')
echo "Manifest digest: ${MANIFEST_DIGEST}"

MANIFEST_BLOB="/tmp/oci-images/nginx/latest/blobs/${MANIFEST_DIGEST/:/\/}"
cat "${MANIFEST_BLOB}" | jq '.mediaType, .config, .layers | length'

COMPUTED_DIGEST=$(sha256sum "${MANIFEST_BLOB}" | cut -d' ' -f1)
echo "Computed: sha256:${COMPUTED_DIGEST}"
echo "Declared: ${MANIFEST_DIGEST}"
test "sha256:${COMPUTED_DIGEST}" = "${MANIFEST_DIGEST}" \
  && echo "PASS: manifest digest verified" \
  || echo "FAIL: digest mismatch"

CONFIG_DIGEST=$(cat "${MANIFEST_BLOB}" | jq -r '.config.digest')
CONFIG_BLOB="/tmp/oci-images/nginx/latest/blobs/${CONFIG_DIGEST/:/\/}"
cat "${CONFIG_BLOB}" | jq '{architecture, os, config: .config, rootfs: .rootfs}'

echo "=== Layer digest chain ==="
cat "${MANIFEST_BLOB}" | jq -r '.layers[].digest'
cat "${CONFIG_BLOB}" | jq -r '.rootfs.diff_ids[]'

echo "=== Blob inventory ==="
find /tmp/oci-images/nginx/latest/blobs -type f \
  -exec sha256sum {} \; | awk '{print $1, $2}'
```

The manifest's `mediaType` field should read `application/vnd.oci.image.manifest.v1+json`, confirming OCI Image Specification compliance. The config blob's `rootfs.diff_ids` array lists the uncompressed SHA-256 hashes of each layer, while the manifest's `layers` array lists the compressed hashes. This distinction matters because the diff_ids are used for filesystem layer reconstruction via overlayfs mounting, while the compressed digests are used for content verification during the pull phase. A mismatch in either chain indicates image corruption or a non-conforming registry.

To verify the OCI Distribution Specification, query the registry directly and confirm that it serves OCI media types:

```bash
TOKEN=$(curl -s \
  "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/nginx:pull" \
  | jq -r .token)

curl -sI "https://registry-1.docker.io/v2/library/nginx/manifests/1.25-alpine" \
  -H "Accept: application/vnd.oci.image.manifest.v1+json" \
  -H "Authorization: Bearer ${TOKEN}" | grep -iE '(HTTP/|Content-Type|Docker-Content-Digest)'
```

The response should include `Content-Type: application/vnd.oci.image.manifest.v1+json` and a `Docker-Content-Digest` header matching the manifest digest we computed locally, confirming end-to-end distribution spec compliance.

### Part B: OCI Runtime State and Namespace Mapping

When containerd starts a container through its CRI interface, it invokes an OCI-compliant runtime—typically `runc`—with a `config.json` bundle that the runtime generates from the CRI request. The following procedure creates a pod sandbox and a container via `crictl`, then uses `runc` to inspect the resulting OCI runtime state and manually maps every Linux namespace the container inhabits.

Create the configuration files that crictl consumes:

```json
// /tmp/oci-lab/pod-config.json
{
  "metadata": {
    "name": "oci-verify-pod",
    "namespace": "default",
    "attempt": 1,
    "uid": "oci-verify-001"
  },
  "log_directory": "/tmp/oci-verify-logs",
  "linux": {}
}
```

```json
// /tmp/oci-lab/container-config.json
{
  "metadata": {
    "name": "oci-verify-container",
    "attempt": 1
  },
  "image": {
    "image": "docker.io/library/busybox:1.36"
  },
  "command": ["sleep", "3600"],
  "log_path": "oci-verify.log",
  "linux": {
    "securityContext": {
      "capabilities": {
        "addCapabilities": ["CAP_NET_BIND_SERVICE"],
        "dropCapabilities": ["CAP_SYS_ADMIN", "CAP_SYS_MODULE", "CAP_SYS_PTRACE"]
      }
    }
  }
}
```

Execute the container lifecycle and inspect the OCI runtime state:

```bash
mkdir -p /tmp/oci-lab /tmp/oci-verify-logs
crictl pull docker.io/library/busybox:1.36

POD_ID=$(crictl runp /tmp/oci-lab/pod-config.json)
echo "Pod sandbox ID: ${POD_ID}"

CONTAINER_ID=$(crictl create "${POD_ID}" \
  /tmp/oci-lab/container-config.json \
  /tmp/oci-lab/pod-config.json)
echo "Container ID: ${CONTAINER_ID}"

crictl start "${CONTAINER_ID}"
crictl ps --name oci-verify-container

# Inspect the OCI runtime state that runc manages underneath containerd.
# Containerd stores runc state under /run/containerd/runc/k8s.io for CRI containers.
runc --root /run/containerd/runc/k8s.io state "${CONTAINER_ID}"
runc --root /run/containerd/runc/k8s.io list

CONTAINER_PID=$(crictl inspect "${CONTAINER_ID}" | jq -r '.info.pid')
echo "Container init PID (host namespace): ${CONTAINER_PID}"

BUNDLE_PATH=$(runc --root /run/containerd/runc/k8s.io state "${CONTAINER_ID}" \
  | jq -r '.bundle')
echo "OCI bundle path: ${BUNDLE_PATH}"
cat "${BUNDLE_PATH}/config.json" | jq '.linux.namespaces'
cat "${BUNDLE_PATH}/config.json" | jq '.process | {user, capabilities, noNewPrivileges}'
cat "${BUNDLE_PATH}/config.json" | jq '.mounts | length'
cat "${BUNDLE_PATH}/config.json" | jq '.mounts[] | select(.destination=="/proc")'
```

The `config.json` in the bundle path is the actual OCI Runtime Specification document that runc executed. Its `linux.namespaces` array lists every namespace the container was placed into. The following commands map each namespace to its kernel-level inode and enter the container's namespaces to inspect the internal view, contrasting it against the host's namespace inodes to prove isolation.

```bash
echo "=== Container namespace inodes ==="
ls -la /proc/${CONTAINER_PID}/ns/

echo "=== Host namespace inodes (for contrast) ==="
ls -la /proc/$$/ns/

echo "=== Network namespace internal view ==="
nsenter -t "${CONTAINER_PID}" -n -- ip -s link
nsenter -t "${CONTAINER_PID}" -n -- ip addr
nsenter -t "${CONTAINER_PID}" -n -- ip route
nsenter -t "${CONTAINER_PID}" -n -- ss -tipn

echo "=== Mount namespace internal view ==="
nsenter -t "${CONTAINER_PID}" -m -- cat /proc/mounts | head -25

echo "=== PID namespace: container's own init ==="
nsenter -t "${CONTAINER_PID}" -p -- ps aux

echo "=== UTS namespace ==="
nsenter -t "${CONTAINER_PID}" -u -- hostname

echo "=== IPC namespace ==="
nsenter -t "${CONTAINER_PID}" -i -- ipcs -m 2>/dev/null || \
  echo "No shared memory segments in container IPC namespace"
```

Each namespace inode printed by `ls -la /proc/<pid>/ns/` is a symlink of the form `[<type>:[<inode>]]`. A container with proper isolation will show different inode numbers for `mnt`, `net`, `pid`, `ipc`, `uts`, and `cgroup` compared to the host's `$$` process. If any namespace inode matches the host's, that namespace is shared rather than isolated—a security regression for the container's threat model.

### Part C: Network Namespace and Cgroup Verification

The container's network namespace contains a virtual ethernet pair: one end resides in the host's network namespace, and the other (`eth0`) resides in the container's namespace. The CNI plugin creates this pair, assigns an IP address to the container's end, and configures routing through a bridge or point-to-point link. The following commands verify this topology and inspect the cgroup v2 resource controllers that bound the container.

```bash
CONTAINER_IFINDEX=$(nsenter -t "${CONTAINER_PID}" -n -- \
  cat /sys/class/net/eth0/ifindex)
echo "Container eth0 ifindex: ${CONTAINER_IFINDEX}"

# Find the host-side veth whose peer_ifindex matches the container's eth0
HOST_VETH=""
for IFACE in /sys/class/net/veth*; do
  IFNAME=$(basename "${IFACE}" 2>/dev/null) || continue
  PEER_PEER=$(cat "${IFACE}/peer_ifindex" 2>/dev/null || echo "none")
  if [ "${PEER_PEER}" = "${CONTAINER_IFINDEX}" ]; then
    HOST_VETH="${IFNAME}"
    break
  fi
done
echo "Host veth peer: ${HOST_VETH}"

ip -s link show "${HOST_VETH}"
ethtool -S "${HOST_VETH}"
ethtool -k "${HOST_VETH}" 2>/dev/null | grep -E '^(tx-checksumming|rx-checksumming|scatter-gather|tcp-segmentation-offload|generic-segmentation-offload):'

# Capture a brief packet sample from inside the container's namespace
timeout 5 nsenter -t "${CONTAINER_PID}" -n -- \
  tcpdump -i eth0 -nn -c 10 2>&1 || echo "No traffic captured in 5s window"

# Locate the container's cgroup v2 path
echo "=== Cgroup path ==="
cat /proc/${CONTAINER_PID}/cgroup
CGROUP_RELATIVE=$(cat /proc/${CONTAINER_PID}/cgroup | cut -d: -f3)
CGROUP_PATH="/sys/fs/cgroup${CGROUP_RELATIVE}"
echo "Cgroup path: ${CGROUP_PATH}"

echo "=== Controllers available ==="
cat "${CGROUP_PATH}/cgroup.controllers"

echo "=== CPU controller ==="
echo "cpu.max: $(cat ${CGROUP_PATH}/cpu.max)"
echo "cpu.weight: $(cat ${CGROUP_PATH}/cpu.weight)"
echo "cpu.stat: $(cat ${CGROUP_PATH}/cpu.stat)"

echo "=== Memory controller ==="
echo "memory.max: $(cat ${CGROUP_PATH}/memory.max)"
echo "memory.current: $(cat ${CGROUP_PATH}/memory.current)"
echo "memory.events: $(cat ${CGROUP_PATH}/memory.events)"

echo "=== PID controller ==="
echo "pids.max: $(cat ${CGROUP_PATH}/pids.max)"
echo "pids.current: $(cat ${CGROUP_PATH}/pids.current)"

echo "=== IO controller ==="
cat "${CGROUP_PATH}/io.max" 2>/dev/null || echo "No IO limits set"
cat "${CGROUP_PATH}/io.stat" 2>/dev/null || echo "No IO stats available"
```

The `memory.events` file is particularly informative. It contains counters for `oom`, `oom_kill`, `oom_group_kill`, and memory pressure events. A container that has never been OOM-killed will show zero across all counters. The `cpu.stat` file shows `usage_usec`, `user_usec`, `system_usec`, and `nr_periods`/`nr_throttled` for CFS bandwidth tracking. If `nr_throttled` is zero, the container has never hit its CPU limit; if non-zero, the kernel's CFS bandwidth controller has actively throttled the container's execution.

### Part D: Security Boundary Verification

OCI containers derive their security posture from three kernel-level mechanisms: Linux capabilities (a bitmask of privileged operations the process may perform), seccomp BPF programs (a filter attached to the process that restricts which syscalls it may invoke), and namespaces (which partition kernel resources so the process sees an isolated view). The `config.json` we inspected earlier declared a subset of capabilities and a seccomp profile; the following commands verify that these declarations were actually enforced by the kernel.

```bash
echo "=== Container capability bitmasks ==="
grep -E 'Cap(Inh|Prm|Eff|Bnd|Amb)' /proc/${CONTAINER_PID}/status

CAP_HEX=$(grep CapEff /proc/${CONTAINER_PID}/status | awk '{print $2}')
echo "Effective capabilities (hex): ${CAP_HEX}"
capsh --decode="${CAP_HEX}"

echo "=== Host capabilities (for contrast) ==="
HOST_CAP_HEX=$(grep CapEff /proc/$$/status | awk '{print $2}')
capsh --decode="${HOST_CAP_HEX}"

echo "=== Seccomp filter status ==="
grep Seccomp /proc/${CONTAINER_PID}/status
# 0 = disabled, 1 = strict, 2 = filter (BPF program active)

echo "=== NoNewPrivs flag ==="
grep NoNewPrivs /proc/${CONTAINER_PID}/status
# Should be 1: prevents setuid binaries from escalating privileges

echo "=== BPF programs (including seccomp filters) ==="
bpftool prog show 2>/dev/null | head -40

echo "=== Cgroup BPF attachments ==="
bpftool cgroup tree 2>/dev/null | head -20

echo "=== MAC profile (AppArmor/SELinux) ==="
cat /proc/${CONTAINER_PID}/attr/current 2>/dev/null || \
  echo "No MAC profile attribute readable"

echo "=== Verifying dropped capabilities ==="
# Attempt a privileged operation that requires CAP_SYS_ADMIN (which we dropped)
nsenter -t "${CONTAINER_PID}" -m -p -- mount -t tmpfs none /mnt 2>&1 \
  || echo "PASS: mount denied (CAP_SYS_ADMIN dropped)"

# Attempt a ptrace operation that requires CAP_SYS_PTRACE (which we dropped)
nsenter -t "${CONTAINER_PID}" -m -p -- cat /proc/1/environ 2>&1 | head -1 \
  || echo "INFO: /proc/1/environ not readable (expected with container init)"
```

The `NoNewPrivs` flag should read `1` for any properly configured OCI container, preventing setuid binaries from granting elevated privileges. The seccomp status should show `2` (filter mode), meaning a BPF program is actively filtering syscalls. If seccomp shows `0`, the container is running without syscall filtering—a security regression from the OCI default profile. The `bpftool prog show` output will list the seccomp BPF program attached to the container's init process, typically showing a program of type `Seccomp` with a filter count matching the number of syscall rules in the OCI seccomp profile.

If a Kubernetes cluster is available, the same verification can be performed through kubectl as an alternative interface:

```bash
kubectl get pods -A -o wide
kubectl exec <pod-name> -- cat /proc/1/status | grep -E 'Seccomp|NoNewPrivs|CapEff'
kubectl exec <pod-name> -- ip addr
kubectl exec <pod-name> -- mount | head -10
```

## Exercise 2: Benchmarking & Saturation Profiling

### Part A: Cold-Start Latency Measurement

Container cold-start latency measures the time from the OCI runtime receiving the `create` command to the container process beginning execution. This metric directly affects autoscaling decisions and serverless platform responsiveness. The following procedure isolates and measures each phase of the container lifecycle: pod sandbox creation, container creation, and container start.

```bash
echo "=== Single cold-start profile ==="
T0=$(date +%s%N)
POD_ID=$(crictl runp /tmp/oci-lab/pod-config.json)
T1=$(date +%s%N)
CTR_ID=$(crictl create "${POD_ID}" \
  /tmp/oci-lab/container-config.json \
  /tmp/oci-lab/pod-config.json)
T2=$(date +%s%N)
crictl start "${CTR_ID}"
T3=$(date +%s%N)

echo "Pod sandbox creation: $(( (T1 - T0) / 1000000 )) ms"
echo "Container creation:   $(( (T2 - T1) / 1000000 )) ms"
echo "Container start:      $(( (T3 - T2) / 1000000 )) ms"
echo "Total cold-start:     $(( (T3 - T0) / 1000000 )) ms"

crictl stop "${CTR_ID}" 2>/dev/null || true
crictl rm "${CTR_ID}" 2>/dev/null || true
crictl rmp "${POD_ID}" 2>/dev/null || true

echo "=== Variance measurement (5 runs) ==="
for i in $(seq 1 5); do
  P=$(crictl runp /tmp/oci-lab/pod-config.json)
  C=$(crictl create "${P}" \
    /tmp/oci-lab/container-config.json \
    /tmp/oci-lab/pod-config.json)
  S0=$(date +%s%N)
  crictl start "${C}"
  S1=$(date +%s%N)
  echo "Run ${i}: start phase $(( (S1 - S0) / 1000000 )) ms"
  crictl stop "${C}" 2>/dev/null || true
  crictl rm "${C}" 2>/dev/null || true
  crictl rmp "${P}" 2>/dev/null || true
  sleep 0.5
done
```

Typical results on a warm host with containerd and runc show pod sandbox creation at 200–500 milliseconds (dominated by CNI plugin execution and network namespace setup), container creation at 50–150 milliseconds (image layer mounting via overlayfs), and container start at 20–80 milliseconds (namespace entry and execve). The variance across runs should be low if the host is not under memory pressure. If pod creation consistently exceeds one second, investigate CNI configuration latency or containerd's image snapshot operations.

### Part B: Syscall Activity Profiling

Every container startup triggers a burst of syscalls: `clone3` to create new namespaces, `unshare` to detach shared resources, `mount` to assemble the overlay filesystem, `setns` to enter namespaces, `execve` to start the container process, and dozens of file descriptor and memory mapping operations. Profiling this burst reveals the kernel-level cost of container isolation and identifies unnecessary overhead.

```bash
echo "=== Strace: container startup syscall trace ==="
# Trace the crictl start command, which internally invokes runc create + runc start
strace -f -e trace=clone,clone3,unshare,mount,umount2,setns,execve,prctl,seccomp,mmap,mprotect,openat \
  -tt -o /tmp/oci-lab/strace-startup.log \
  crictl start "${CTR_ID}" 2>&1 || true

echo "=== First 50 syscalls ==="
head -50 /tmp/oci-lab/strace-startup.log
echo "..."
echo "=== Total syscalls traced: $(wc -l < /tmp/oci-lab/strace-startup.log) ==="

echo "=== Syscall frequency summary ==="
awk '{for(i=1;i<=NF;i++) if($i ~ /^[a-z_]+\(/) print $i}' \
  /tmp/oci-lab/strace-startup.log \
  | sed 's/(.*//' | sort | uniq -c | sort -rn | head -20

echo "=== Perf stat: container startup hardware counters ==="
perf stat -e task-switches,cpu-migrations,page-faults,context-switches \
  -o /tmp/oci-lab/perf-startup.log \
  crictl start "${CTR_ID}" 2>&1
cat /tmp/oci-lab/perf-startup.log

# Profile a running container's syscall rate over 10 seconds
RUNNING_PID=$(crictl inspect "${CTR_ID}" | jq -r '.info.pid')
echo "=== Perf stat: running container (10s sample) ==="
perf stat -e task-switches,cpu-migrations,page-faults,context-switches \
  -p "${RUNNING_PID}" -- sleep 10 2>&1
```

The strace output reveals the exact sequence of kernel operations that transform an OCI runtime spec into a running process. The `clone3` call with flags `CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWIPC|CLONE_NEWUTS` creates the namespace set. The `mount` calls assemble the overlay filesystem by mounting the image's read-only layers beneath a writable upper directory. The `execve` call replaces the runc init process with the container's command. The total syscall count for a minimal busybox container typically falls between 200 and 400.

### Part C: CPU Cgroup Enforcement Verification

The cgroup v2 CPU controller enforces resource limits through two mechanisms: `cpu.max` applies hard bandwidth throttling via the CFS quota and period parameters, while `cpu.weight` controls proportional fair scheduling among cgroups sharing the same parent. A `cpu.max` value of `50000 100000` means the container may use 50 milliseconds of CPU time per 100-millisecond period, effectively capping it at 50 percent of a single core. The following exercise creates a container with this limit and verifies that the kernel throttles execution when the container exceeds its quota.

```bash
cat > /tmp/oci-lab/pod-stress.json <<'EOF'
{
  "metadata": {
    "name": "cpu-stress-pod",
    "namespace": "default",
    "attempt": 1,
    "uid": "cpu-stress-001"
  },
  "log_directory": "/tmp/oci-verify-logs",
  "linux": {}
}
EOF

cat > /tmp/oci-lab/container-cpu-stress.json <<'EOF'
{
  "metadata": {
    "name": "cpu-stress",
    "attempt": 1
  },
  "image": {
    "image": "docker.io/library/alpine:3.19"
  },
  "command": ["sh", "-c", "apk add --no-cache stress-ng > /dev/null 2>&1; sleep 3600"],
  "log_path": "cpu-stress.log",
  "linux": {
    "resources": {
      "cpuQuota": 50000,
      "cpuPeriod": 100000,
      "cpuShares": 512
    }
  }
}
EOF

crictl pull docker.io/library/alpine:3.19
STRESS_POD=$(crictl runp /tmp/oci-lab/pod-stress.json)
STRESS_CTR=$(crictl create "${STRESS_POD}" \
  /tmp/oci-lab/container-cpu-stress.json \
  /tmp/oci-lab/pod-stress.json)
crictl start "${STRESS_CTR}"
sleep 8  # Allow stress-ng to install

STRESS_PID=$(crictl inspect "${STRESS_CTR}" | jq -r '.info.pid')
STRESS_CGROUP=$(cat /proc/${STRESS_PID}/cgroup | cut -d: -f3)
STRESS_CG_PATH="/sys/fs/cgroup${STRESS_CGROUP}"

echo "=== Cgroup CPU configuration ==="
echo "cpu.max: $(cat ${STRESS_CG_PATH}/cpu.max)"
echo "cpu.weight: $(cat ${STRESS_CG_PATH}/cpu.weight)"
echo "cpu.stat (before): $(cat ${STRESS_CG_PATH}/cpu.stat)"

echo "=== Running CPU stress: 2 workers, 100% load, 20s ==="
crictl exec "${STRESS_CTR}" \
  stress-ng --cpu 2 --cpu-load 100 --timeout 20s --metrics-brief 2>&1 | tail -20

echo "=== CPU throttling after stress ==="
cat "${STRESS_CG_PATH}/cpu.stat"

# Monitor CPU usage in real-time while stressing
crictl exec "${STRESS_CTR}" \
  stress-ng --cpu 2 --cpu-load 100 --timeout 10s &
sleep 3
echo "=== CPU usage snapshot (3s into stress) ==="
cat "${STRESS_CG_PATH}/cpu.stat" | grep usage_usec
sleep 3
echo "=== CPU usage snapshot (6s into stress) ==="
cat "${STRESS_CG_PATH}/cpu.stat" | grep usage_usec
wait

echo "=== Final throttle summary ==="
cat "${STRESS_CG_PATH}/cpu.stat"

crictl stop "${STRESS_CTR}" 2>/dev/null || true
crictl rm "${STRESS_CTR}" 2>/dev/null || true
crictl rmp "${STRESS_POD}" 2>/dev/null || true
```

The `nr_throttled` counter in `cpu.stat` should be non-zero after the stress run, confirming that the CFS bandwidth controller actively throttled the container. The `throttled_usec` value indicates the total time the container was prevented from running because it had exhausted its quota. On a multi-core system, a `cpu.max` of `50000 100000` limits the container to 50 percent of one core's throughput, so two CPU-bound workers should show approximately 0.5 CPU-seconds of work per wall-clock second.

### Part D: Memory Cgroup Enforcement and OOM Profiling

The cgroup v2 memory controller enforces a hard limit via `memory.max`. When a container's resident set exceeds this limit, the kernel's OOM killer selects a victim process within the cgroup and terminates it. The `memory.events` file records `oom` (OOM event entered) and `oom_kill` (process actually killed) counters, allowing precise verification that the limit was enforced.

```bash
cat > /tmp/oci-lab/container-mem-stress.json <<'EOF'
{
  "metadata": {
    "name": "mem-stress",
    "attempt": 1
  },
  "image": {
    "image": "docker.io/library/alpine:3.19"
  },
  "command": ["sh", "-c", "apk add --no-cache stress-ng > /dev/null 2>&1; sleep 3600"],
  "log_path": "mem-stress.log",
  "linux": {
    "resources": {
      "memoryLimitInBytes": 134217728
    }
  }
}
EOF

MEM_POD=$(crictl runp /tmp/oci-lab/pod-stress.json)
MEM_CTR=$(crictl create "${MEM_POD}" \
  /tmp/oci-lab/container-mem-stress.json \
  /tmp/oci-lab/pod-stress.json)
crictl start "${MEM_CTR}"
sleep 8

MEM_PID=$(crictl inspect "${MEM_CTR}" | jq -r '.info.pid')
MEM_CGROUP=$(cat /proc/${MEM_PID}/cgroup | cut -d: -f3)
MEM_CG_PATH="/sys/fs/cgroup${MEM_CGROUP}"

echo "=== Memory configuration ==="
echo "memory.max: $(cat ${MEM_CG_PATH}/memory.max)"
echo "memory.current: $(cat ${MEM_CG_PATH}/memory.current)"
echo "memory.events (before): $(cat ${MEM_CG_PATH}/memory.events)"

echo "=== Injecting memory stress: 256M allocation against 128M limit ==="
crictl exec "${MEM_CTR}" \
  stress-ng --vm 1 --vm-bytes 256M --vm-method all --timeout 30s \
  --metrics-brief 2>&1 || true

sleep 2
echo "=== Memory events after OOM stress ==="
cat "${MEM_CG_PATH}/memory.events"

echo "=== Container status after OOM ==="
crictl ps -a --name mem-stress
crictl inspect "${MEM_CTR}" | jq -r '.status | {state, exitCode, reason}'

# Verify the container's init process survived (stress-ng worker was OOM-killed,
# but the sleep process should continue)
echo "=== Container process status ==="
test -d /proc/${MEM_PID} && echo "Init process alive" || echo "Init process dead"

crictl stop "${MEM_CTR}" 2>/dev/null || true
crictl rm "${MEM_CTR}" 2>/dev/null || true
crictl rmp "${MEM_POD}" 2>/dev/null || true
```

The `oom_kill` counter in `memory.events` should increment by at least one after the stress run, confirming that the memory cgroup enforced the 128 MiB limit and the kernel OOM-killed the stress-ng worker. If the container's init process (the `sleep` command) survives, the container remains in a running state. If the init process itself is killed, the container exits with a non-zero exit code, and the `reason` field in `crictl inspect` will indicate `OOMKilled`.

### Part E: Network Throughput Profiling

Container network performance depends on the veth pair bridging, the CNI plugin's configuration, and kernel network stack parameters. The following exercise measures throughput between the host and a container and verifies that the network namespace provides isolation while maintaining reasonable transfer rates.

```bash
cat > /tmp/oci-lab/container-nettest.json <<'EOF'
{
  "metadata": {
    "name": "nettest",
    "attempt": 1
  },
  "image": {
    "image": "docker.io/library/busybox:1.36"
  },
  "command": ["sh", "-c", "mkdir -p /www; dd if=/dev/zero of=/www/largefile bs=1M count=100 2>/dev/null; httpd -f -p 8080 -h /www"],
  "log_path": "nettest.log",
  "linux": {
    "securityContext": {
      "capabilities": {
        "addCapabilities": ["CAP_NET_BIND_SERVICE"]
      }
    }
  }
}
EOF

NET_POD=$(crictl runp /tmp/oci-lab/pod-config.json)
NET_CTR=$(crictl create "${NET_POD}" \
  /tmp/oci-lab/container-nettest.json \
  /tmp/oci-lab/pod-config.json)
crictl start "${NET_CTR}"
sleep 3

NET_PID=$(crictl inspect "${NET_CTR}" | jq -r '.info.pid')
CONTAINER_IP=$(nsenter -t "${NET_PID}" -n -- ip -4 addr show eth0 \
  | grep -oP 'inet \K[\d.]+')
echo "Container IP: ${CONTAINER_IP}"

echo "=== HTTP connectivity ==="
curl -s -o /dev/null -w "HTTP %{http_code} | %{time_total}s | %{size_download} bytes\n" \
  "http://${CONTAINER_IP}:8080/"

echo "=== Throughput: 100MB download ==="
curl -s -o /dev/null \
  -w "Download: %{size_download} bytes in %{time_total}s = %{speed_download} bytes/s\n" \
  "http://${CONTAINER_IP}:8080/largefile"

echo "=== Network isolation: container cannot reach host SSH ==="
nsenter -t "${NET_PID}" -n -- nc -z -w2 172.17.0.1 22 2>&1 \
  && echo "WARNING: host SSH reachable from container" \
  || echo "PASS: host SSH unreachable from container"

echo "=== TCP socket state (container) ==="
nsenter -t "${NET_PID}" -n -- ss -tipn

echo "=== Interface statistics (container) ==="
nsenter -t "${NET_PID}" -n -- ip -s link show eth0

crictl stop "${NET_CTR}" 2>/dev/null || true
crictl rm "${NET_CTR}" 2>/dev/null || true
crictl rmp "${NET_POD}" 2>/dev/null || true
```

Throughput between host and container on a veth bridge typically reaches 5–15 Gbps for large transfers, limited by kernel stack overhead and the bridge's packet forwarding path. If throughput is significantly lower, check whether `tcp-segmentation-offload` is disabled on the veth interface, as TSO is essential for high-throughput transfers on virtual network devices.

## Exercise 3: Fault Injection & Recovery Analysis

### Part A: OOM Kill and Container Recovery

When the kernel's OOM killer terminates a process inside a container's cgroup, the container's init process (PID 1 in the container's PID namespace) may or may not survive. If the init process is killed, the container exits and the container runtime must restart it. The following exercise injects memory pressure that exceeds the cgroup limit, observes the kernel's OOM response, and verifies that crictl reports the container's exit status correctly.

```bash
cat > /tmp/oci-lab/container-oom.json <<'EOF'
{
  "metadata": {
    "name": "oom-test",
    "attempt": 1
  },
  "image": {
    "image": "docker.io/library/alpine:3.19"
  },
  "command": ["sh", "-c", "apk add --no-cache stress-ng > /dev/null 2>&1; exec sleep 3600"],
  "log_path": "oom-test.log",
  "linux": {
    "resources": {
      "memoryLimitInBytes": 67108864
    }
  }
}
EOF

OOM_POD=$(crictl runp /tmp/oci-lab/pod-stress.json)
OOM_CTR=$(crictl create "${OOM_POD}" \
  /tmp/oci-lab/container-oom.json \
  /tmp/oci-lab/pod-stress.json)
crictl start "${OOM_CTR}"
sleep 8

OOM_PID=$(crictl inspect "${OOM_CTR}" | jq -r '.info.pid')
OOM_CGROUP=$(cat /proc/${OOM_PID}/cgroup | cut -d: -f3)
OOM_CG_PATH="/sys/fs/cgroup${OOM_CGROUP}"

echo "=== Before OOM ==="
echo "memory.max: $(cat ${OOM_CG_PATH}/memory.max)"
echo "memory.events: $(cat ${OOM_CG_PATH}/memory.events)"
crictl ps --name oom-test

echo "=== Injecting OOM: 128M allocation against 64M limit ==="
crictl exec "${OOM_CTR}" sh -c \
  'stress-ng --vm 1 --vm-bytes 128M --vm-method all --timeout 60s' 2>&1 || true
sleep 2

echo "=== After OOM ==="
echo "memory.events: $(cat ${OOM_CG_PATH}/memory.events)"
crictl ps -a --name oom-test
echo "=== Container exit status ==="
crictl inspect "${OOM_CTR}" | jq -r '.status | {state, exitCode, finishedAt, reason}'

echo "=== Attempt restart ==="
crictl start "${OOM_CTR}" 2>&1 || echo "Container cannot be restarted (expected for exited containers)"

crictl rm "${OOM_CTR}" 2>/dev/null || true
crictl rmp "${OOM_POD}" 2>/dev/null || true
```

The `oom_kill` counter in `memory.events` should increment by at least one. If the stress-ng worker process is killed but the container's `sleep` init process survives, the container remains running and `crictl ps` shows it in the `Running` state. If the OOM killer targets the init process itself, the container exits with exit code 137 (128 + 9, indicating SIGKILL) and the `reason` field reads `OOMKilled`.

### Part B: PID 1 Termination and Container Exit

In a container's PID namespace, the init process (PID 1) has special kernel semantics: if PID 1 exits, all other processes in the namespace receive `SIGKILL` and the namespace is destroyed. This exercise verifies that killing PID 1 inside the container causes the entire container to exit and that the runtime correctly reports the exit status.

```bash
PID1_POD=$(crictl runp /tmp/oci-lab/pod-config.json)
PID1_CTR=$(crictl create "${PID1_POD}" \
  /tmp/oci-lab/container-config.json \
  /tmp/oci-lab/pod-config.json)
crictl start "${PID1_CTR}"

PID1_PID=$(crictl inspect "${PID1_CTR}" | jq -r '.info.pid')
echo "Container PID 1 (host PID): ${PID1_PID}"
crictl ps --name oci-verify-container

echo "=== Killing container PID 1 with SIGKILL ==="
kill -9 "${PID1_PID}" 2>/dev/null || true
sleep 2

echo "=== Container status after PID 1 kill ==="
crictl ps -a --name oci-verify-container
crictl inspect "${PID1_CTR}" | jq -r '.status | {state, exitCode, reason}'

# The container should show state "Exited" with exitCode 137 and reason referencing the signal

crictl rm "${PID1_CTR}" 2>/dev/null || true
crictl rmp "${PID1_POD}" 2>/dev/null || true
```

The container should exit with `exitCode: 137` (128 + 9, representing SIGKILL) and the `state` should transition from `CONTAINER_RUNNING` to `CONTAINER_EXITED`. The `reason` field typically reads `OOMKilled` only for memory-induced exits; for a direct SIGKILL, it may be empty or report the signal.

### Part C: Cgroup Freeze and Thaw

Cgroup v2 supports a freeze operation that suspends all processes within a cgroup by preventing them from being scheduled. This is distinct from `SIGSTOP` because it operates at the cgroup level rather than the process level, does not affect signal handlers or timer state, and is used for container checkpointing and live migration. The following exercise freezes and thaws a container and verifies that the process state is preserved across the freeze boundary.

```bash
cat > /tmp/oci-lab/container-freeze.json <<'EOF'
{
  "metadata": {
    "name": "freeze-test",
    "attempt": 1
  },
  "image": {
    "image": "docker.io/library/busybox:1.36"
  },
  "command": ["sh", "-c", "i=0; while true; do echo \"count=$i\"; i=$((i+1)); sleep 1; done"],
  "log_path": "freeze-test.log"
}
EOF

FREEZE_POD=$(crictl runp /tmp/oci-lab/pod-config.json)
FREEZE_CTR=$(crictl create "${FREEZE_POD}" \
  /tmp/oci-lab/container-freeze.json \
  /tmp/oci-lab/pod-config.json)
crictl start "${FREEZE_CTR}"
sleep 3

FREEZE_PID=$(crictl inspect "${FREEZE_CTR}" | jq -r '.info.pid')
FREEZE_CGROUP=$(cat /proc/${FREEZE_PID}/cgroup | cut -d: -f3)
FREEZE_CG_PATH="/sys/fs/cgroup${FREEZE_CGROUP}"

echo "=== Before freeze ==="
crictl logs "${FREEZE_CTR}" | tail -3
echo "cgroup.freeze: $(cat ${FREEZE_CG_PATH}/cgroup.freeze)"
echo "process state: $(cat /proc/${FREEZE_PID}/status | grep State)"

echo "=== Freezing container ==="
echo 1 > "${FREEZE_CG_PATH}/cgroup.freeze"
echo "cgroup.freeze: $(cat ${FREEZE_CG_PATH}/cgroup.freeze)"
echo "process state: $(cat /proc/${FREEZE_PID}/status | grep State)"

sleep 5
echo "=== Logs during freeze (should be unchanged) ==="
crictl logs "${FREEZE_CTR}" | tail -3

echo "=== Thawing container ==="
echo 0 > "${FREEZE_CG_PATH}/cgroup.freeze"
echo "cgroup.freeze: $(cat ${FREEZE_CG_PATH}/cgroup.freeze)"

sleep 3
echo "=== Logs after thaw (counter should resume from where it left off) ==="
crictl logs "${FREEZE_CTR}" | tail -3

crictl stop "${FREEZE_CTR}" 2>/dev/null || true
crictl rm "${FREEZE_CTR}" 2>/dev/null || true
crictl rmp "${FREEZE_POD}" 2>/dev/null || true
```

During the freeze, the container's process state should transition from `R (running)` or `S (sleeping)` to `D (disk sleep)` or `T (stopped)`, and no new log lines should appear. After thawing, the counter should resume from approximately where it left off, though there may be a small gap due to the sleep timer not firing during the frozen period. The `cgroup.freeze` file reads `1` while frozen and `0` when thawed.

### Part D: Container Restart and State Recovery

The final exercise verifies that a fully stopped container can be removed and recreated, and that the underlying OCI runtime state is properly cleaned up. This simulates a pod restart in a production environment and verifies that no residual state—network interfaces, cgroup directories, mount points—leaks into the host.

```bash
RESTART_POD=$(crictl runp /tmp/oci-lab/pod-config.json)
RESTART_CTR=$(crictl create "${RESTART_POD}" \
  /tmp/oci-lab/container-config.json \
  /tmp/oci-lab/pod-config.json)
crictl start "${RESTART_CTR}"

RESTART_PID=$(crictl inspect "${RESTART_CTR}" | jq -r '.info.pid')
RESTART_CGROUP=$(cat /proc/${RESTART_PID}/cgroup | cut -d: -f3)
RESTART_CG_PATH="/sys/fs/cgroup${RESTART_CGROUP}"
CONTAINER_IP=$(nsenter -t "${RESTART_PID}" -n -- ip -4 addr show eth0 \
  | grep -oP 'inet \K[\d.]+')

echo "=== Before stop ==="
echo "Container IP: ${CONTAINER_IP}"
echo "Cgroup exists: $(test -d "${RESTART_CG_PATH}" && echo yes || echo no)"
echo "Process exists: $(test -d /proc/${RESTART_PID} && echo yes || echo no)"
echo "veth interfaces on host:"
ip link show type veth 2>/dev/null | grep -c veth || echo "0"

echo "=== Stopping and removing container ==="
crictl stop "${RESTART_CTR}"
crictl rm "${RESTART_CTR}"
crictl rmp "${RESTART_POD}"
sleep 2

echo "=== After cleanup ==="
echo "Cgroup exists: $(test -d "${RESTART_CG_PATH}" && echo yes || echo no)"
echo "Process exists: $(test -d /proc/${RESTART_PID} && echo yes || echo no)"
echo "veth interfaces on host:"
ip link show type veth 2>/dev/null | grep -c veth || echo "0"
echo "Runc state:"
runc --root /run/containerd/runc/k8s.io list 2>/dev/null || echo "No runc containers"
echo "Orphaned overlay mounts:"
mount | grep overlay | head -5

echo "=== Recreating container ==="
RESTART_POD2=$(crictl runp /tmp/oci-lab/pod-config.json)
RESTART_CTR2=$(crictl create "${RESTART_POD2}" \
  /tmp/oci-lab/container-config.json \
  /tmp/oci-lab/pod-config.json)
crictl start "${RESTART_CTR2}"
sleep 2

RESTART_PID2=$(crictl inspect "${RESTART_CTR2}" | jq -r '.info.pid')
NEW_IP=$(nsenter -t "${RESTART_PID2}" -n -- ip -4 addr show eth0 \
  | grep -oP 'inet \K[\d.]+')
echo "New container IP: ${NEW_IP}"
echo "IP changed: $([ "${CONTAINER_IP}" != "${NEW_IP}" ] && echo yes || echo no)"
echo "Container running: $(crictl ps --name oci-verify-container -q | wc -l) instance(s)"

crictl stop "${RESTART_CTR2}" 2>/dev/null || true
crictl rm "${RESTART_CTR2}" 2>/dev/null || true
crictl rmp "${RESTART_POD2}" 2>/dev/null || true
```

After cleanup, the cgroup directory should be gone, the process should no longer exist in `/proc`, and the veth interface count should decrease. Any orphaned overlay mounts indicate a leak in containerd's snapshotter cleanup. The recreated container should receive a different IP address from the CNI IPAM plugin, confirming that the previous container's network allocation was properly released.

## Diagnostic Cheat Sheet & Verification Checklist

The following reference table consolidates the primary diagnostic commands used throughout this lab series. Each command maps to a specific OCI subsystem and produces a specific verification signal.

| Subsystem | Command | Expected Signal |
|---|---|---|
| OCI Image Layout | `cat oci-layout` | `{"imageLayoutVersion":"1.0.0"}` |
| Image Manifest Media Type | `jq .mediaType manifest-blob` | `application/vnd.oci.image.manifest.v1+json` |
| Image Digest Integrity | `sha256sum <blob>` vs. declared digest | Exact match |
| Runtime State | `runc --root /run/containerd/runc/k8s.io state <id>` | `status: running`, `ociVersion: 1.x` |
| Namespace Isolation | `ls -la /proc/<pid>/ns/` | Inodes differ from host |
| Network Namespace | `nsenter -t <pid> -n -- ip -s link` | Only `eth0` and `lo`, no host interfaces |
| PID Namespace | `nsenter -t <pid> -p -- ps aux` | Container init is PID 1 |
| CPU Cgroup Limit | `cat <cgpath>/cpu.max` | Format: `<quota> <period>` |
| CPU Throttling | `cat <cgpath>/cpu.stat` | `nr_throttled > 0` when limit exceeded |
| Memory Cgroup Limit | `cat <cgpath>/memory.max` | Numeric bytes or `max` |
| OOM Events | `cat <cgpath>/memory.events` | `oom_kill` counter for OOM history |
| PID Limit | `cat <cgpath>/pids.max` | Numeric or `max` |
| Capabilities | `grep CapEff /proc/<pid>/status` | Bounded subset of host |
| Seccomp | `grep Seccomp /proc/<pid>/status` | Value `2` (filter mode) |
| NoNewPrivs | `grep NoNewPrivs /proc/<pid>/status` | Value `1` |
| BPF Programs | `bpftool prog show` | Lists seccomp and cgroup programs |
| Container Status | `crictl inspect <id> \| jq .status` | `state`, `exitCode`, `reason` |
| Cgroup Freeze | `echo 1 > <cgpath>/cgroup.freeze` | Process state transitions to frozen |
| veth Peer Discovery | `cat /sys/class/net/veth*/peer_ifindex` | Matches container `eth0` ifindex |
| Network Isolation | `nsenter -t <pid> -n -- nc -z <host-ip> 22` | Connection refused/unreachable |
| Distribution Spec | `curl -sI registry/v2/<img>/manifests/<tag>` | `Content-Type: application/vnd.oci.image.manifest.v1+json` |

| Verification Check | Pass Criteria |
|---|---|
| Image digest chain integrity | Every blob's computed SHA-256 matches its declared digest |
| Container namespace isolation | All namespace inodes differ from host process inodes |
| Network namespace isolation | Container cannot reach host's loopback services directly |
| CPU cgroup enforcement | `nr_throttled` in `cpu.stat` is non-zero after CPU stress |
| Memory cgroup enforcement | `oom_kill` in `memory.events` is non-zero after memory stress |
| PID 1 kill propagation | Container exits with code 137 when PID 1 receives SIGKILL |
| Cgroup freeze preservation | No new log lines during freeze; counter resumes after thaw |
| Container cleanup completeness | No orphaned cgroups, veth interfaces, or runc state after removal |
| Cold-start latency | Pod creation under 500ms, container start under 100ms on warm host |
| Seccomp active | `Seccomp` field shows `2` in `/proc/<pid>/status` |
| NoNewPrivs enforced | `NoNewPrivs` field shows `1` in `/proc/<pid>/status` |
| Image media type compliance | Manifest `mediaType` matches OCI spec, not Docker v2 schema |
