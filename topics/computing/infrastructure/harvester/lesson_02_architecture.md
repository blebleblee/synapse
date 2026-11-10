# Lesson 2: Architecture Deep Dive & The KubeVirt Control Plane

## 1. The Core Abstraction: Kubernetes as the Hypervisor Control Plane

In traditional enterprise virtualization (such as VMware ESXi or standalone KVM/libvirt deployments), a centralized daemon or hypervisor agent runs directly on the host OS. This agent manages hardware virtualization extensions (`/dev/kvm`), binds to host networking interfaces, and directly spawns QEMU processes.

KubeVirt fundamentally alters this operational model:
* It replaces host-level VM daemons with Kubernetes-native primitives (CRDs and controllers).
* It encapsulates the hypervisor layer (`libvirtd` and `qemu-kvm`) **inside an unprivileged (or minimally privileged) Kubernetes Pod**.
* The Linux kernel on the bare-metal node enforces CPU limits, memory boundaries, and namespaces on the VM process using standard container primitives: **cgroups v2**, **seccomp profiles**, and **Linux namespaces** (PID, mount, network, IPC).

By treating a virtual machine as an execution workload inside a Pod, Kubernetes features—such as scheduling, affinity, tolerations, ResourceQuotas, horizontal scaling, and CSI/CNI bindings—apply natively to virtual machines without custom hypervisor middleware.

---

## 2. KubeVirt Custom Resource Definitions (CRDs)

KubeVirt introduces several core CRDs that decouple the *desired configuration* of a virtual machine from its *active runtime instantiation*.

```
  +-------------------------------------------------------+
  |              VirtualMachine (VM) CRD                  |
  |  - Persistent Spec (vCPU, RAM, Disks, Networks)       |
  |  - Desired State: running: true | false               |
  +-------------------------------------------------------+
                             |
                             | (virt-controller reconciles)
                             v
  +-------------------------------------------------------+
  |          VirtualMachineInstance (VMI) CRD             |
  |  - Ephemeral Runtime State                            |
  |  - Pod phase binding, IP allocations, guest status    |
  +-------------------------------------------------------+
                             |
                             | (triggers Pod creation)
                             v
  +-------------------------------------------------------+
  |          virt-launcher-<name>-<hash> Pod              |
  |  - Container running libvirtd + QEMU process          |
  +-------------------------------------------------------+
```

### 2.1. `VirtualMachine` (VM) vs. `VirtualMachineInstance` (VMI)
The distinction mirrors the relationship between a Kubernetes `Deployment` and a `Pod`:
* **`VirtualMachine` (VM):** The declarative, persistent record. It defines whether the machine should be powered on (`spec.running: true`), its hardware configuration, and restart policies. If a node crashes, the VM object remains intact.
* **`VirtualMachineInstance` (VMI):** The ephemeral runtime object. It represents an active instance executing on a specific node. If a user deletes a VMI or powers down the VM, the VMI object is destroyed. When powered back on, a new VMI is generated from the VM specification.

### 2.2. Supplementary CRDs
* **`VirtualMachineInstanceMigration` (VMIM):** Manages live migration operations between nodes.
* **`VirtualMachineSnapshot` & `VirtualMachineRestore`:** Coordinates point-in-time state captures and disk rollbacks with underlying CSI storage drivers.
* **`VirtualMachineInstanceReplicaSet`:** Allows declarative scaling of identical, ephemeral stateless VMs (ideal for horizontally scaled virtual appliances).

---

## 3. Control Plane Daemons & Component Architecture

KubeVirt distributes responsibility across three primary components:

```
 +-------------------------------------------------------------------------------+
 |                         Kubernetes Control Plane                              |
 |                                                                               |
 |  [Client / kubectl] ---> [ kube-apiserver ] <---> [ virt-api ]                |
 |                                  ^                      |                     |
 |                                  |                      v                     |
 |                         [ virt-controller ] <--- (Watches CRDs)               |
 +----------------------------------|--------------------------------------------+
                                    | Schedules virt-launcher Pod
                                    v
 +-------------------------------------------------------------------------------+
 |                         Worker / Bare-Metal Node                              |
 |                                                                               |
 |  +-------------------------------------------------------------------------+  |
 |  | virt-handler (DaemonSet, privileged host PID)                           |  |
 |  |  - Communicates via Unix Domain Socket: /var/run/kubevirt-private/...   |  |
 |  +------------------------------------|------------------------------------+  |
 |                                       | IPC via Domain Socket                 |
 |                                       v                                       |
 |  +-------------------------------------------------------------------------+  |
 |  | Pod: virt-launcher-<vm-name>                                            |  |
 |  |  +-------------------------------------------------------------------+  |  |
 |  |  | Container: compute                                                |  |  |
 |  |  |   -> libvirtd (manages local domain)                              |  |  |
 |  |  |   -> qemu-system-x86_64 (executes guest OS via /dev/kvm)          |  |  |
 |  |  +-------------------------------------------------------------------+  |  |
 |  +-------------------------------------------------------------------------+  |
 +-------------------------------------------------------------------------------+
```

### 3.1. `virt-api`
* Serves as the entrance gate for KubeVirt operations.
* Operates as an aggregated API server and admission webhook (`ValidatingAdmissionWebhook` and `MutatingAdmissionWebhook`).
* Intercepts VM/VMI requests to validate hardware specs, set defaults, and authorize non-standard subresources (such as `virtctl vnc`, `virtctl console`, and VM power state transitions).

### 3.2. `virt-controller`
* Cluster-level controller running in high-availability mode (active/passive with leader election).
* Observes lifecycle events on `VirtualMachine` and `VirtualMachineInstance` CRDs.
* When a VMI is created, `virt-controller` synthesizes and creates the matching `virt-launcher` Pod manifest, handing off actual placement to `kube-scheduler`.

### 3.3. `virt-handler`
* Deployed as a `DaemonSet` on every node capable of virtualization.
* Runs with elevated privileges to access node-level hardware (`/dev/kvm`, `/dev/net/tun`, sysfs).
* Watches the local node for newly scheduled `virt-launcher` pods.
* Establishes a bidirectional IPC channel with `virt-launcher` via a Unix domain socket residing in `/var/run/kubevirt-private`.
* Configures host cgroups, network interfaces, and host-device pass-through before signalling QEMU execution.

### 3.4. `virt-launcher`
* A standard Kubernetes Pod designed to house a single guest VM.
* Contains the `compute` container where `libvirtd` runs in encapsulation.
* Spawns `qemu-system-x86_64` to execute guest code via hardware acceleration (`/dev/kvm`).
* Forwards shutdown signals (SIGTERM/SIGINT) to ACPI guest commands for clean OS shutdown.

---

## 4. Hardware Sizing: Memory Overhead, CPU Pinning, and NUMA

Running virtual machines inside containers requires precise resource tuning to prevent node instability and process eviction.

### 4.1. Memory Overhead Calculation
When allocating 8 GiB of RAM to a VM, the `virt-launcher` pod requires **more** than 8 GiB from the host. The cgroup limit must account for:
1. **Guest RAM Allocation:** The memory exposed directly to the guest OS.
2. **QEMU Process Overhead:** Memory pages consumed by QEMU data structures, page tables, and emulation buffers.
3. **Video RAM (VRAM):** Allocated for virtual displays.

KubeVirt dynamically calculates this overhead and adds it to the Pod's resource request:

$$\text{Memory Request} = \text{Guest RAM} + \text{Overhead}$$

If the memory limit is configured incorrectly or overhead is artificially constrained, the Linux Out-Of-Memory (OOM) killer will terminate the `qemu-system-x86_64` process, crashing the VM.

### 4.2. CPU Pinning & Dedicated Cores
By default, Kubernetes shares CPU cores among containers using CFS (Completely Fair Scheduler) quotas. For high-performance enterprise workloads, context switching between shared cores degrades VM performance.

KubeVirt provides dedicated CPU assignment:
* Sets `spec.template.spec.domain.cpu.dedicatedCpuPlacement: true`.
* The Kubernetes CPU Manager assigns exclusive physical cores to the `virt-launcher` pod.
* KubeVirt configures `numactl` and QEMU CPU affinity mappings to lock vCPU threads to physical pCPUs.

### 4.3. Hugepages
Standard Linux memory pages are 4 KiB. A 64 GiB VM requires $16{,}777{,}216$ page table entries, consuming gigabytes of host memory solely for MMU page tables.
* By using **Hugepages** (2 MiB or 1 GiB), the number of entries is reduced dramatically.
* This reduces Translation Lookaside Buffer (TLB) misses and guest memory access latency.

---

## 5. Live Migration Mechanics

Live migration allows moving a running VMI from one physical node to another with sub-second switchover and zero perceived network interruption.

```
  Node A (Source)                                      Node B (Target)
  +------------------------------------+               +------------------------------------+
  | virt-launcher (Source)             |               | virt-launcher (Target)             |
  | [QEMU Process: Active RAM]         |               | [QEMU Process: Listening State]    |
  +------------------------------------+               +------------------------------------+
             \                                                    ^
              \  1. Dirty RAM Pre-Copy (TCP migration stream)     /
               ==================================================
             /                                                    \
  +------------------------------------+               +------------------------------------+
  | Longhorn Volume (Shared Block RWX) |               | Longhorn Volume (Shared Block RWX) |
  +------------------------------------+               +------------------------------------+
```

### Prerequisites
1. **Shared Storage:** The underlying PVC must support `ReadWriteMany` (RWX), typically provided by Longhorn distributed block volumes.
2. **Identical CPU Models:** The source and target nodes must expose compatible CPU flag sets, or the VM must use a normalized CPU model (e.g., `qemu64` or `Nehalem`).
3. **Network Connectivity:** Uninterrupted L2 network reachability via Multus or cluster overlay.

### Migration Execution Sequence
1. A user or node-drain controller posts a `VirtualMachineInstanceMigration` (VMIM) object.
2. `virt-controller` creates a second `virt-launcher` pod on the target node.
3. The target pod initializes storage connections to the same Longhorn volume.
4. Source `virt-handler` opens an encrypted migration channel to the target node's `virt-handler`.
5. QEMU transmits guest RAM via pre-copy iteration:
   * An initial iteration copies all memory pages.
   * Subsequent iterations transfer only pages marked dirty during the previous pass.
6. When remaining dirty pages reach a minimal threshold, the source VM is briefly paused, the remaining CPU register state is synced, and the target VM is resumed.
7. The source `virt-launcher` pod is cleanly terminated.

---

## 6. Infrastructure as Code: Production VirtualMachine Manifest

Below is a fully validated, production-grade KubeVirt manifest demonstrating dedicated CPU placement, hugepages, and persistent block storage.

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: production-db-node
  namespace: default
  labels:
    app.kubernetes.io/name: database-vm
spec:
  running: true
  template:
    metadata:
      labels:
        kubevirt.io/vm: production-db-node
    spec:
      domain:
        cpu:
          cores: 4
          sockets: 1
          threads: 1
          dedicatedCpuPlacement: true
          isolateEmulatorThread: true
        memory:
          guest: 8Gi
          hugepages:
            pageSize: 2Mi
        devices:
          disks:
            - name: rootdisk
              disk:
                bus: virtio
            - name: cloudinitdisk
              disk:
                bus: virtio
          interfaces:
            - name: default
              masquerade: {}
      networks:
        - name: default
          pod: {}
      volumes:
        - name: rootdisk
          persistentVolumeClaim:
            claimName: production-db-rootfs
        - name: cloudinitdisk
          cloudInitNoCloud:
            userData: |
              #cloud-config
              user: admin
              password: SecurePassword123!
              chpasswd: { expire: False }
              ssh_pwauth: True
```

---

## 7. Operational Lab: Verifying Control Plane Internals

Execute these verification steps against an active Harvester/KubeVirt cluster to inspect runtime state.

### Step 1: Inspect Custom Resource Objects
```bash
# Check both parent VM and active runtime VMI objects
kubectl get vm,vmi -n default

# Extract detailed phase and scheduling node
kubectl get vmi production-db-node -n default -o jsonpath='{.status.phase}{" on node "}{.status.nodeName}{"\n"}'
```

### Step 2: Locate the Underlying `virt-launcher` Pod
```bash
# Find the Pod encapsulating your VM
kubectl get pods -n default -l kubevirt.io=virt-launcher

# Inspect container processes inside the launcher
VM_POD=$(kubectl get pods -n default -l kubevirt.io/vm=production-db-node -o jsonpath='{.items[0].metadata.name}')
kubectl top pod $VM_POD -n default
```

### Step 3: Inspect QEMU Directly via `virsh` Inside the Pod
Since `virt-launcher` encapsulates libvirt, you can query runtime statistics using `virsh`:
```bash
# List internal libvirt domains running in the compute container
kubectl exec -it $VM_POD -n default -c compute -- virsh list --all

# View hypervisor-level domain statistics (vCPU and memory metrics)
kubectl exec -it $VM_POD -n default -c compute -- virsh domstats
```

### Step 4: Trace the Unix IPC Socket on the Host Node
Log in via SSH or debug pod to the worker node running the VM:
```bash
# Verify the communication socket created by virt-handler for virt-launcher
ls -la /var/run/kubevirt-private/
```

### Step 5: Trigger and Observe a Live Migration
```bash
# Initiate live migration via virtctl or VMIM manifest
virtctl migrate production-db-node -n default

# Watch the migration object progress
kubectl get vmim -n default -w
```

---
*End of Lesson 2. In Lesson 3, we move to bare-metal bootstrapping: analyzing PXE boot chains, ISO installs, and automating configuration with Harvester config files.*