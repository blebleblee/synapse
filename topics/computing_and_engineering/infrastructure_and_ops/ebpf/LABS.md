# Hands-On Operational Lab: eBPF Diagnostics, XDP Filtering & Verifier Debugging

## Objective & Lab Prerequisites
In this lab, you will inspect the running kernel's eBPF subsystem, compile and load an XDP program, query kernel BPF maps using `bpftool`, intentionally trigger and diagnose a real in-kernel verifier rejection, and inspect JIT-compiled x86_64 machine code directly from kernel memory.

### Prerequisites
* A Linux environment with kernel v5.4+ (v5.8+ recommended for ring buffer support).
* Root privileges (`sudo`).
* Package requirements:
  ```bash
  # Debian / Ubuntu / SUSE
  sudo apt-get install -y clang llvm libbpf-dev linux-tools-common linux-tools-$(uname -r) bpftool iproute2
  # Or Fedora / RHEL
  sudo dnf install -y clang llvm libbpf-devel bpftool kernel-devel iproute
  ```

---

## Exercise 1: In-Kernel Subsystem & JIT Inspection

Before compiling programs, inspect your kernel's eBPF JIT compiler and BTF (BPF Type Format) exposure.

```bash
# 1. Verify that eBPF JIT Compilation is enabled (1 = enabled, 2 = enabled with debugging)
sysctl net.core.bpf_jit_enable

# Expected output:
# net.core.bpf_jit_enable = 1

# 2. Check JIT Hardening (protects against JIT spraying attacks; 0=off, 1=unprivileged only, 2=all)
sysctl net.core.bpf_jit_harden

# 3. Check if your kernel has exposed BPF Type Format (BTF) for CO-RE
ls -lh /sys/kernel/btf/vmlinux

# Expected output:
# -r--r--r-- 1 root root 4.8M ... /sys/kernel/btf/vmlinux

# 4. List all currently loaded eBPF programs on the system
sudo bpftool prog list

# 5. List all active eBPF maps allocated in kernel memory
sudo bpftool map list
```

---

## Exercise 2: Building and Attaching an XDP Packet Counter

We will create a standalone, working XDP packet counter that tracks incoming IPv4 vs. non-IPv4 traffic on a virtual network interface.

### Step 1: Create the Virtual Ethernet Pair
To avoid disrupting physical network adapters, build a sandboxed network namespace:

```bash
# Create namespace and veth pair
sudo ip netns add ebpf-lab
sudo ip link add veth-host type veth peer name veth-guest
sudo ip link set veth-guest netns ebpf-lab

# Assign IP addresses
sudo ip addr add 10.200.1.1/24 dev veth-host
sudo ip link set veth-host up

sudo ip netns exec ebpf-lab ip addr add 10.200.1.2/24 dev veth-guest
sudo ip netns exec ebpf-lab ip link set veth-guest up
```

### Step 2: Write the eBPF Source (`xdp_counter.c`)

```bash
cat << 'EOF' > xdp_counter.c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

// Array map with 2 elements:
// Index 0: IPv4 packet count
// Index 1: Other packet count
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 2);
    __type(key, __u32);
    __type(value, __u64);
} packet_stats SEC(".maps");

SEC("xdp")
int count_packets(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    // MANDATORY: Safety boundary check against data_end
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    __u32 key;
    if (bpf_ntohs(eth->h_proto) == ETH_P_IP) {
        key = 0; // IPv4
    } else {
        key = 1; // Other (ARP, IPv6, etc.)
    }

    __u64 *val = bpf_map_lookup_elem(&packet_stats, &key);
    if (val) {
        __sync_fetch_and_add(val, 1); // Atomic increment
    }

    return XDP_PASS; // Forward packet up the network stack
}

char _license[] SEC("license") = "GPL";
EOF
```

### Step 3: Compile into eBPF Bytecode
Compile directly to an ELF object targeting the BPF virtual machine:

```bash
clang -O2 -target bpf -c xdp_counter.c -o xdp_counter.o

# Inspect the generated ELF sections and BTF info
llvm-objdump -h xdp_counter.o
```

### Step 4: Load and Attach to Interface

```bash
# Attach the compiled XDP program to veth-host in generic mode
sudo ip link set dev veth-host xdpgeneric obj xdp_counter.o sec xdp

# Verify that the XDP program is attached
ip link show dev veth-host | grep -i xdp
# Expected: ... xdpgeneric id <PROG_ID> ...
```

### Step 5: Generate Traffic and Query In-Kernel Map Counters

```bash
# Send 5 ICMP echo packets from the namespace to host
sudo ip netns exec ebpf-lab ping -c 5 10.200.1.1

# Locate the map ID associated with your program
MAP_ID=$(sudo bpftool map list | grep packet_stats | awk -F: '{print $1}')
echo "Inspecting Map ID: $MAP_ID"

# Dump the contents of the BPF map directly from kernel memory
sudo bpftool map dump id $MAP_ID

# Expected output shows key 0 (IPv4) incremented by at least 5!
```

---

## Exercise 3: Inspecting JIT-Compiled Machine Code

Inspect the actual bare-metal x86_64 (or ARM64) machine instructions emitted by the in-kernel JIT compiler:

```bash
# Get the program ID of our loaded filter
PROG_ID=$(sudo bpftool prog list | grep count_packets | awk -F: '{print $1}')

# Dump the translated BPF bytecode instructions:
sudo bpftool prog dump xlated id $PROG_ID

# Dump the raw, JIT-compiled native hardware machine code:
sudo bpftool prog dump jited id $PROG_ID
```

Observe how virtual BPF registers (`R1`, `R2`, etc.) were directly translated into native CPU registers (`%rdi`, `%rsi`, `%rax`).

---

## Exercise 4: Fault Injection & Verifier Failure Analysis

To understand why the verifier rejects code, we will deliberately inject a common software error: accessing memory past a packet header without verifying the offset against `data_end`.

### Step 1: Create Faulty Code (`faulty_xdp.c`)

```bash
cat << 'EOF' > faulty_xdp.c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int broken_filter(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;

    // ERROR: Directly casting and reading without comparing (data + sizeof) <= data_end!
    struct iphdr *ip = (struct iphdr *)(data + sizeof(struct ethhdr));

    // DANGEROUS DEREFERENCE: The packet might be smaller than 34 bytes!
    if (ip->protocol == 6) {
        return XDP_DROP;
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
EOF
```

### Step 2: Attempt to Load and Observe Verifier Rejection

```bash
clang -O2 -target bpf -c faulty_xdp.c -o faulty_xdp.o

# Attempt to load the faulty object
sudo ip link set dev veth-host xdpgeneric obj faulty_xdp.o sec xdp
```

### Expected Verifier Rejection Log:
```
libbpf: prog 'broken_filter': BPF program load failed: Permission denied
libbpf: -- BEGIN PROG LOAD LOG --
0: (79) r2 = *(u64 *)(r1 +0)
1: (79) r1 = *(u64 *)(r1 +8)
2: (0f) r2 += 14
3: (71) r3 = *(u8 *)(r2 +9)
invalid access to packet, memptr=r2, off=9, size=1
R2 doesn't have packet bounds checked!
verification time 24 us
stack depth 0
processed 4 insns (limit 1000000)
-- END PROG LOAD LOG --
```

### Analysis of the Rejection:
* At instruction `3: r3 = *(u8 *)(r2 + 9)` (reading `ip->protocol` at offset 14 + 9 = 23 bytes), register `R2` has type `PTR_TO_PACKET`.
* The verifier inspects its internal range table and discovers that no branch instruction has validated `R2 + 1 <= R1` (`R1` is `PTR_TO_PACKET_END`).
* Because a malformed or fragmented network packet could be shorter than 23 bytes, executing this dereference could read past the physical network buffer, causing a kernel page fault.
* **The verifier rejects the program at load time, completely preventing a potential kernel panic.**

---

## Exercise 5: Clean Up

```bash
# Detach XDP program from interface
sudo ip link set dev veth-host xdpgeneric off

# Remove network namespace and veth links
sudo ip link delete veth-host
sudo ip netns delete ebpf-lab

# Clean up local object files
rm -f xdp_counter.c xdp_counter.o faulty_xdp.c faulty_xdp.o
```

---

## Challenge Lab: Socratic Exploration
1. Modify `xdp_counter.c` to use `BPF_MAP_TYPE_PERCPU_ARRAY` instead of `BPF_MAP_TYPE_ARRAY`. How does the memory footprint and CPU cache behavior change when querying the map via `bpftool map dump`?
2. If an eBPF program needs to store a temporary 4096-byte string buffer, why does allocating `char buf[4096]` on the stack cause the verifier to reject the program? How can you solve this using a single-entry `BPF_MAP_TYPE_PERCPU_ARRAY` map?
