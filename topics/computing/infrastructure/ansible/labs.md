Operational Verification Labs: Ansible
=====================================

### Objective and Environment Setup

The primary objective of this guide is to provide hands-on, step-by-step diagnostic verification using real tools specific to Ansible. This guide is designed for hands-on systems engineers and infrastructure practitioners who require a deep understanding of Ansible's operational behavior.

To begin, ensure you have a cloud infrastructure setup with the following tools installed:

*   `kubectl`
*   `iproute2`
*   `etcdctl`
*   `crictl`
*   `helm`
*   `ss`
*   `ethtool`
*   `tcpdump`
*   `perf`

Install these tools using your preferred package manager or by following the installation instructions for each tool.

### Exercise 1: Live State and Internal Subsystem Inspection

In this exercise, we will inspect the live state of an Ansible-managed infrastructure and analyze the internal subsystems.

**Step 1: Inspect the Ansible Inventory**

Create an Ansible inventory file (`hosts`) with the following content:

```yaml
[controllers]
controller1 ansible_host=192.168.1.1

[workers]
worker1 ansible_host=192.168.1.2
worker2 ansible_host=192.168.1.3

[all:vars]
ansible_user=root
ansible_password=password
```

**Step 2: Run Ansible Playbook**

Run the following Ansible playbook (`playbook.yml`) to inspect the live state of the infrastructure:

```yaml
---
- name: Inspect Live State
  hosts: all
  gather_facts: true
  tasks:
  - name: Inspect system facts
    debug:
      var: ansible_facts
```

Run the playbook using the following command:

```bash
ansible-playbook -i hosts playbook.yml
```

**Step 3: Analyze System Facts**

Analyze the system facts collected by Ansible using the following command:

```bash
ansible-playbook -i hosts playbook.yml --list-tasks
```

This will display the list of tasks executed by the playbook, including the system facts collected.

**Step 4: Inspect Internal Subsystems**

Inspect the internal subsystems of the Ansible-managed infrastructure using the following commands:

```bash
kubectl get pods -A
kubectl get svc -A
kubectl get deployments -A
```

These commands will display the list of pods, services, and deployments in the Kubernetes cluster.

### Exercise 2: Benchmarking and Saturation Profiling

In this exercise, we will benchmark the performance of an Ansible-managed infrastructure and analyze the saturation profiles.

**Step 1: Create a Benchmarking Playbook**

Create an Ansible playbook (`benchmarking.yml`) with the following content:

```yaml
---
- name: Benchmarking
  hosts: all
  gather_facts: true
  tasks:
  - name: Benchmark CPU usage
    shell: "perf stat -e cpu-cycles /bin/true"
  - name: Benchmark memory usage
    shell: "perf stat -e cache-references /bin/true"
```

**Step 2: Run the Benchmarking Playbook**

Run the benchmarking playbook using the following command:

```bash
ansible-playbook -i hosts benchmarking.yml
```

**Step 3: Analyze Benchmarking Results**

Analyze the benchmarking results using the following command:

```bash
perf stat -e cpu-cycles /bin/true
perf stat -e cache-references /bin/true
```

These commands will display the benchmarking results, including the CPU and memory usage.

### Exercise 3: Fault Injection and Recovery Analysis

In this exercise, we will inject faults into an Ansible-managed infrastructure and analyze the recovery mechanisms.

**Step 1: Create a Fault Injection Playbook**

Create an Ansible playbook (`fault_injection.yml`) with the following content:

```yaml
---
- name: Fault Injection
  hosts: all
  gather_facts: true
  tasks:
  - name: Inject CPU fault
    shell: "echo 'cpu fault' > /sys/devices/system/cpu/cpu0/cpufreq/scaling_setspeed"
  - name: Inject memory fault
    shell: "echo 'memory fault' > /sys/devices/system/memory/memory0/state"
```

**Step 2: Run the Fault Injection Playbook**

Run the fault injection playbook using the following command:

```bash
ansible-playbook -i hosts fault_injection.yml
```

**Step 3: Analyze Recovery Mechanisms**

Analyze the recovery mechanisms using the following commands:

```bash
kubectl get pods -A
kubectl get svc -A
kubectl get deployments -A
```

These commands will display the list of pods, services, and deployments in the Kubernetes cluster, including the recovery mechanisms.

### Diagnostic Cheat Sheet and Verification Checklist

| Diagnostic Tool | Command | Description |
| --- | --- | --- |
| `kubectl` | `kubectl get pods -A` | List pods in the Kubernetes cluster |
| `kubectl` | `kubectl get svc -A` | List services in the Kubernetes cluster |
| `kubectl` | `kubectl get deployments -A` | List deployments in the Kubernetes cluster |
| `ss` | `ss -tipm` | Display socket statistics |
| `ethtool` | `ethtool -S eth0` | Display Ethernet statistics |
| `tcpdump` | `tcpdump -i eth0` | Capture network traffic |
| `perf` | `perf stat -e cpu-cycles /bin/true` | Benchmark CPU usage |
| `perf` | `perf stat -e cache-references /bin/true` | Benchmark memory usage |
| `strace` | `strace -p <pid>` | Display system calls |
| `bpftool` | `bpftool list` | Display BPF programs |

Verification Checklist:

*   Verify that the Ansible inventory file is correctly configured.
*   Verify that the Ansible playbook is correctly executed.
*   Verify that the system facts are correctly collected.
*   Verify that the internal subsystems are correctly inspected.
*   Verify that the benchmarking results are correctly analyzed.
*   Verify that the fault injection playbook is correctly executed.
*   Verify that the recovery mechanisms are correctly analyzed.
