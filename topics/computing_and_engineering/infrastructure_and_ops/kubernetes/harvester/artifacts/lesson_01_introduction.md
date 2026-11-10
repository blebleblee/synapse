# Lesson 1: The Evolution of Infrastructure & Harvester Stack Deep Dive

## 1. Introduction to Hyperconverged Infrastructure (HCI)

To understand Harvester, we must first understand the architectural paradigm it seeks to disrupt and improve upon: Hyperconverged Infrastructure (HCI). Traditionally, enterprise datacenters were built using a 3-tier architecture. This consisted of separate compute servers, a dedicated Storage Area Network (SAN) or Network Attached Storage (NAS), and a complex fabric of networking switches to connect them together. Scaling this architecture required precise forecasting, massive capital expenditure, and specialized engineers for each silo (storage admins, network admins, virtualization admins).

HCI collapses this 3-tier architecture into a single, unified software-defined tier. In an HCI cluster, every node contributes compute, storage, and networking capabilities to the overall pool. Software layers abstract the physical disks into a distributed storage pool and virtualize the network. This allows organizations to scale linearly—if you need more capacity, you simply add another standard x86 server to the cluster.

### The HCI Promise vs. Reality
While proprietary HCI solutions like VMware vSAN and Nutanix successfully collapsed the hardware tiers, they introduced a new problem: extreme vendor lock-in and high licensing costs. Furthermore, as the world moved toward containerization and Kubernetes, these legacy HCI platforms treated containers as a secondary workload, bolting Kubernetes management on top of their aging virtual machine control planes.

This impedance mismatch is exactly where Harvester enters the picture.

## 2. Legacy Virtualization vs. Cloud-Native Virtualization

For the last two decades, the hypervisor (like ESXi, Hyper-V, or KVM) was the unquestioned king of the datacenter. The paradigm was simple: an operating system running on bare metal, executing virtual hardware containers, which in turn ran their own operating systems.

When Kubernetes emerged, it revolutionized application deployment by abstracting the infrastructure entirely. Applications were packaged as containers and orchestrated dynamically. However, Kubernetes was fundamentally designed to orchestrate Linux containers, not full virtual machines. 

### The Dual-Stack Dilemma
Most enterprises today run a "dual-stack" environment:
1.  **A Virtualization Stack:** (e.g., VMware vSphere) to run legacy applications, stateful databases, and virtual appliances.
2.  **A Cloud-Native Stack:** (e.g., SUSE Rancher, Red Hat OpenShift, or raw Kubernetes) deployed *on top* of the virtualization stack to run modern containerized applications.

This dual-stack approach is incredibly inefficient. You are paying the "hypervisor tax" (overhead and licensing) simply to run a Linux VM that exists only to run Kubernetes worker nodes. You also have to manage two completely different control planes, network overlays, and storage drivers.

### Cloud-Native Virtualization (CNV)
Cloud-Native Virtualization flips the dual-stack model on its head. Instead of running Kubernetes inside VMs, **we run VMs inside Kubernetes**. By leveraging technologies like KubeVirt, the Kubernetes API becomes the master control plane for both containers and virtual machines. 

## 3. The Birth of Harvester

Harvester was created by SUSE (originally Rancher Labs) as a 100% free, open-source modern HCI solution. It is built explicitly for operators who want a single, unified control plane based on Kubernetes but still need to run legacy virtual machines alongside their modern container workloads.

Harvester is not just a collection of upstream projects; it is an integrated, opinionated appliance. It abstracts the immense complexity of Kubernetes, Longhorn, and KubeVirt behind a clean, intuitive UI and API, making it feel like a traditional hypervisor to operators while remaining entirely cloud-native under the hood.

## 4. Deep Dive into the Harvester Software Stack

To master Harvester, you must understand its constituent components. Harvester is essentially an aggressively tuned, bare-metal Kubernetes cluster bundled with specialized operators.

### 4.1. The Operating System: SLE Micro
At the very bottom of the stack sits SUSE Linux Enterprise Micro (SLE Micro). This is an ultra-reliable, lightweight OS purpose-built for edge and container hosts.
*   **Immutable Infrastructure:** SLE Micro uses a read-only root filesystem. You do not patch it by running `zypper update`. Instead, it uses transactional updates. If an update fails, the system automatically rolls back to the previous Btrfs snapshot.
*   **Minimal Attack Surface:** It contains only the packages necessary to run containers and virtualization, significantly reducing security vulnerabilities.

### 4.2. The Container Engine & Orchestrator: RKE2 / K3s
Historically, Harvester used K3s, but it has transitioned towards robust enterprise implementations similar to RKE2 for enhanced security profiles. This layer provides the Kubernetes API server, the scheduler, and the controller managers.
*   **Embedded Etcd:** For state management and cluster consensus.
*   **Containerd:** The underlying container runtime that manages the lifecycle of the pods.

### 4.3. The Virtualization Engine: KubeVirt
KubeVirt is a Cloud Native Computing Foundation (CNCF) project that extends Kubernetes with Custom Resource Definitions (CRDs) to manage Virtual Machines.
*   Instead of talking directly to a hypervisor like libvirt, KubeVirt launches a standard Kubernetes Pod.
*   Inside this Pod, KubeVirt runs a highly stripped-down QEMU/KVM process.
*   The VM's operating system runs inside this QEMU process, which is constrained and scheduled by Kubernetes exactly like a standard container.

### 4.4. The Distributed Storage Fabric: Longhorn
You cannot have HCI without a distributed SAN. Longhorn is a lightweight, reliable, and powerful distributed block storage system for Kubernetes.
*   **Block Device Provisioning:** Longhorn aggregates local direct-attached storage (NVMe, SSD, HDD) from all Harvester nodes.
*   **Replication:** When a VM writes to its virtual disk, Longhorn synchronously replicates those blocks across multiple nodes to ensure data survives a total node failure.
*   **Snapshots and Backups:** Longhorn manages crash-consistent snapshots and can offload backups to S3-compatible endpoints.

### 4.5. The Networking Layer: Multus CNI & Canal
Networking in a Kubernetes cluster is typically flat (every pod can talk to every other pod). VMs, however, usually require complex Layer 2 networking, VLAN tagging, and dedicated MAC addresses.
*   **Canal:** Provides the default pod network and network policies.
*   **Multus:** A "meta-plugin" that allows a Pod (and therefore a KubeVirt VM) to have multiple network interfaces.
*   Harvester uses Multus to bridge physical NICs directly into the VM, allowing VMs to participate in external VLANs natively, bypassing the standard Kubernetes NAT.

## 5. Harvester vs. Legacy HCI (vSphere / Nutanix)

Understanding the competitive landscape helps crystallize Harvester's value proposition.

| Feature | VMware vSphere | Nutanix | SUSE Harvester |
| :--- | :--- | :--- | :--- |
| **Control Plane** | vCenter (Proprietary) | Prism (Proprietary) | Kubernetes API (Open Source) |
| **Underlying OS** | ESXi (Proprietary) | AHV (CentOS-based) | SLE Micro (Immutable OS) |
| **Storage Engine** | vSAN | AOS Storage | Longhorn (Cloud Native) |
| **Container Native?** | Tanzu (Bolted on) | Karbon (Bolted on) | Yes, Native (KubeVirt) |
| **Licensing Cost** | High / Core-based | High / Appliance-based | Free / Open Source (Support Optional) |

## 6. Hardware Requirements and Sizing Considerations

Because Harvester runs everything (the OS, the Kubernetes control plane, Longhorn storage controllers, and your workloads) on the same metal, proper sizing is critical.

### Minimum vs. Production Specs
*   **Minimum (PoC only):** 8 Cores, 32GB RAM, 1x SSD (250GB+), 1x 1Gbps NIC.
*   **Production Standard:** 32+ Cores, 256GB+ RAM, 2x NVMe for Storage, 1x SSD for OS, 2x 10/25Gbps NICs (LACP bonded).

### The Longhorn Tax
Distributed storage requires CPU and network bandwidth. For every block of data written, Longhorn must compress, encrypt (optionally), and replicate it across the network. A 10Gbps dedicated storage network is highly recommended to prevent latency spikes during high I/O operations.

## 7. Use Cases & Edge Deployments

1.  **The Remote Edge:** Retail stores, factories, and cell towers. Environments where you need a 3-node HA cluster that is highly resilient, can run legacy point-of-sale VMs alongside modern AI-inferencing containers, and requires zero on-site IT staff.
2.  **DevOps & CI/CD:** Developers who want an API-driven infrastructure to spin up VMs programmatically via Terraform without submitting IT tickets.
3.  **Modernizing Datacenters:** Organizations looking to escape punitive virtualization licensing renewals by migrating standard tier-2/tier-3 workloads to a free stack.

## 8. Lab: Exploring the Infrastructure API

In this lab, we will use standard tools to interact with the Harvester foundation. This demonstrates that Harvester is just Kubernetes under the hood.

*Requirement: Access to a terminal with `kubectl` configured to your Harvester cluster's kubeconfig.*

**Step 1: Verify the Cluster Nodes**
Run the following command to see the physical nodes acting as Kubernetes workers.
```bash
kubectl get nodes -o wide
```
*Notice the OS-Image field will report SLE Micro or openSUSE, and the container-runtime will show containerd.*

**Step 2: Inspecting the Storage Engine**
Longhorn runs entirely as pods. Let's look at the Longhorn components.
```bash
kubectl get pods -n longhorn-system
```
*You will see `longhorn-manager` (the control plane), `instance-manager` (handles read/write to physical disks), and `engine-image` pods.*

**Step 3: Finding the Virtualization Components**
KubeVirt is the engine making VMs possible.
```bash
kubectl get pods -n harvester-system
```
*You will see pods related to `virt-controller`, `virt-api`, and `virt-handler`. We will deep dive into these exact binaries in Lesson 2.*

---
*End of Lesson 1. In Lesson 2, we will tear down the virtualization abstraction and analyze how KubeVirt manages memory, CPU pinning, and live migrations via the Kubernetes API.*
