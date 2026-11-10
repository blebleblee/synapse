# In-Depth Technical Lesson: eBPF Architecture, Verifier Internals & CO-RE

## 1. Virtual Machine Architecture & Instruction Set (ISA)

eBPF is implemented as an in-kernel, 64-bit RISC register machine. Its design closely mirrors modern hardware instruction sets (x86-64 and aarch64), enabling the in-kernel JIT compiler to map virtual registers to physical CPU registers with near zero translation overhead.

```
eBPF 64-Bit RISC Register Allocation & Calling Convention
=========================================================

  +----------+--------------------------------------------------------+
  | Register | ABI Role / Calling Convention                          |
  +----------+--------------------------------------------------------+
  | R0       | Function return value; exit status of BPF program      |
  | R1       | Argument 1 to in-kernel helper function / Context ptr  |
  | R2       | Argument 2 to in-kernel helper function                |
  | R3       | Argument 3 to in-kernel helper function                |
  | R4       | Argument 4 to in-kernel helper function                |
  | R5       | Argument 5 to in-kernel helper function                |
  | R6       | Callee-saved register (preserved across helper calls)  |
  | R7       | Callee-saved register (preserved across helper calls)  |
  | R8       | Callee-saved register (preserved across helper calls)  |
  | R9       | Callee-saved register (preserved across helper calls)  |
  | R10      | Read-only stack frame pointer (points to 512B stack)   |
  +----------+--------------------------------------------------------+
```

### Register File Specifications
* **Registers `R0`–`R10`:** Eleven 64-bit registers.
* **`R0`:** Stores the return value of helper function calls and determines the verdict when exiting the eBPF program (e.g., `XDP_PASS`, `XDP_DROP`, or `0`/`1` for filter verdicts).
* **`R1`–`R5` (Scratch Registers):** Function argument registers. When an eBPF program starts, `R1` contains the pointer to the program's context structure (e.g., `struct xdp_md *` for XDP, `struct __sk_buff *` for TC, or `struct pt_regs *` for kprobes).
* **`R6`–`R9` (Callee-Saved Registers):** Preserved across in-kernel helper calls. Values placed here survive helper function execution.
* **`R10` (Frame Pointer):** Strictly **read-only**. Points to the base of the eBPF program's local stack frame. Any instruction attempting to write to `R10` is immediately rejected by the verifier with `-EACCES`.
* **Stack Size:** Fixed at exactly **512 bytes**. eBPF programs cannot dynamically grow their stack. Attempting to allocate stack variables exceeding 512 bytes fails verification.

### 64-Bit Instruction Encoding
Every standard eBPF instruction is encoded as a fixed 64-bit (8-byte) struct (`struct bpf_insn` defined in `<linux/bpf.h>`):

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    opcode     |   dst   |   src   |            offset             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                              imm                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

* **`opcode` (8 bits):** Specifies the operation, encoding the instruction class (e.g., `BPF_ALU64`, `BPF_JMP`, `BPF_LDX`), operation code (e.g., `BPF_ADD`, `BPF_K`, `BPF_X`), and source modifier.
* **`dst_reg` (4 bits):** Destination register number (`0` to `10`).
* **`src_reg` (4 bits):** Source register number (`0` to `10`).
* **`offset` (16 bits, signed):** Relative jump displacement or memory load/store byte offset.
* **`imm` (32 bits, signed):** Immediate scalar value (constant integer operand).

*(Note: Wide 64-bit immediate loads, `BPF_LD | BPF_DW | BPF_IMM`, consume two consecutive 64-bit instruction slots, spanning 128 bits total).*

---

## 2. The In-Kernel Static Verifier Pipeline

The verifier (`kernel/bpf/verifier.c`) is the mathematical bedrock of eBPF safety. It operates as an abstract interpreter that analyzes the program's control-flow graph (CFG).

```
                 Bytecode Ingestion (bpf(BPF_PROG_LOAD))
                                    |
                                    v
                  Phase 1: DAG Control-Flow Analysis
                   - Reject unreachable instructions
                   - Detect unconstrained back-edges
                                    |
                                    v
                 Phase 2: Abstract State Exploration (DFS)
                   - Simulate every execution branch
                   - Track Register Types & Bounds (tnum)
                   - Enforce Pointer Alignment & Bounds
                   - State Equivalence Pruning (states_equal)
                                    |
                  +-----------------+-----------------+
                  |                                   |
                  v (Safety Invariant Violated)        v (All Paths Proven Safe)
           REJECT Program                     PASS to JIT Compiler
       (Emit Verifier Error Log)           (Emit Native CPU Machine Code)
```

### Phase 1: Directed Acyclic Graph (DAG) Check
* Constructs the program's control flow graph.
* Verifies there are no unreachable dead instructions.
* Historically, all loops were completely forbidden. Since Linux 5.3, **bounded loops** are supported if the verifier can prove they terminate within a provable iteration bound.

### Phase 2: Abstract State Exploration
The verifier performs a Depth-First Search (DFS) traversing all possible execution paths. At every step, it maintains a simulated machine state for all eleven registers and the 512-byte stack frame.

#### Register Type Tracking
Every register is tagged with an abstract type:
* `NOT_INIT`: Uninitialized register. Reading from it causes immediate verification failure.
* `SCALAR_VALUE`: Holds a known integer or bounded range.
* `PTR_TO_CTX`: Points to the program context (e.g., `struct xdp_md`).
* `PTR_TO_STACK`: Points into the local 512-byte stack.
* `PTR_TO_MAP_VALUE`: Points directly to an element inside an eBPF map.
* `PTR_TO_MAP_KEY`: Points to a key buffer for map lookups.
* `PTR_TO_PACKET`: Points to network packet data (`ctx->data`).
* `PTR_TO_PACKET_END`: Points to the end boundary of network packet data (`ctx->data_end`).

#### Range and Bound Propagation
The verifier tracks both signed (`smin_value`, `smax_value`) and unsigned (`umin_value`, `umax_value`) 64-bit bounds, alongside a **trinary number** (`tnum`) representing known bits (`value` and `mask`).
When an instruction executes (e.g., `if (r2 > 1024) goto exit`), the verifier forks the simulated state:
* On the branch where the jump is taken, `r2->umin_value = 1025`.
* On the fallthrough branch, `r2->umax_value = 1024`.
If the program later attempts to write `r2` bytes into a buffer, the verifier checks whether `r2->umax_value` exceeds the buffer capacity.

#### State Equivalence Pruning
Simulating every branch of a complex program would lead to state space explosion ($O(2^N)$ paths). To prevent this, the verifier caches explored states. If execution reaches an instruction with a state that is a subset or equivalent (`states_equal()`) to an already-verified state, the verifier prunes that branch, guaranteeing verification completion in linear time. The current complexity limit is **1,000,000 processed instructions** (increased from 4,096 in Linux 5.2).

---

## 3. High-Performance In-Kernel Data Structures: eBPF Maps

eBPF programs cannot use global variables in arbitrary memory. They store and share state via kernel-managed **eBPF Maps**.

```
eBPF Map Memory Architecture
============================

+--------------------------------------------------------------+
| User Space                                                   |
|   libbpf / Go cilium/ebpf / BCC                              |
|   Polls metrics, writes configuration                        |
+--------------------------------------------------------------+
         |                                           ^
         | bpf(BPF_MAP_UPDATE_ELEM)                  | bpf(BPF_MAP_LOOKUP_ELEM)
         v                                           |
+--------------------------------------------------------------+
| Linux Kernel Heap Memory (kmalloc / vmalloc)                 |
|                                                              |
|   [BPF_MAP_TYPE_HASH]                                        |
|   Bucket Array -> Linked Buckets (RCU Protected)             |
|                                                              |
|   [BPF_MAP_TYPE_RINGBUF]                                     |
|   Single Lockless Circular Memory Page (Zero-Copy Mmap)      |
|   Multi-Producer In-Kernel, Single-Consumer User Space       |
+--------------------------------------------------------------+
         ^                                           |
         | bpf_map_update_elem()                     | bpf_ringbuf_output()
         |                                           v
+--------------------------------------------------------------+
| eBPF Programs (XDP / TC / kprobes)                           |
| Running concurrently across CPU cores                        |
+--------------------------------------------------------------+
```

### Critical Map Implementations

#### 1. `BPF_MAP_TYPE_HASH` vs. `BPF_MAP_TYPE_PERCPU_HASH`
* **`BPF_MAP_TYPE_HASH`:** Standard associative hash table with bucket chaining. Synchronized across CPU cores using Read-Copy-Update (RCU) and bucket spinlocks. Concurrent writes across cores incur cache line invalidation and lock contention.
* **`BPF_MAP_TYPE_PERCPU_HASH`:** Allocates an independent hash table per CPU core. Lookups and updates require zero locking and cause zero cross-core cache invalidations. Ideal for metrics, packet counters, and high-frequency event aggregation.

#### 2. `BPF_MAP_TYPE_RINGBUF` (Linux 5.8+)
Replaces the legacy `BPF_MAP_TYPE_PERF_EVENT_ARRAY`.
* **Architecture:** A single, memory-mapped circular buffer shared across all CPU cores.
* **Zero-Copy Reservation:** An eBPF program calls `bpf_ringbuf_reserve()`, writes data directly into the allocated memory slot, and invokes `bpf_ringbuf_submit()`.
* **Consumer Efficiency:** User space memory-maps the ring buffer (`epoll` or `poll`), reading events with zero memory copying and dramatically lower CPU overhead than the per-CPU perf buffer.

#### 3. `BPF_MAP_TYPE_LPM_TRIE`
* Longest Prefix Match trie. Used for high-speed IP routing tables, CIDR subnet matching, and firewall subnet rule lookups in $O(K)$ time where $K$ is the IP bit length (32 for IPv4, 128 for IPv6).

---

## 4. Compile Once – Run Everywhere (CO-RE) & BTF

### The Legacy Problem: BCC Compiler Burden
Early eBPF tools (BCC) embedded Clang and LLVM inside the user-space runtime daemon. On every target server, BCC parsed kernel C headers (`/usr/src/linux-headers-$(uname -r)`) and compiled eBPF bytecode on the fly.
* **Drawbacks:** Production servers had to install 200MB+ compiler toolchains, kernel headers often did not match the running kernel, and compilation consumed gigabytes of RAM during container startup.

### The Modern Solution: BPF Type Format (BTF) & CO-RE
Modern eBPF uses CO-RE, eliminating user-space compilation entirely.

```
CO-RE Relocation Pipeline
=========================

1. Development Machine:
   Kernel BTF (/sys/kernel/btf/vmlinux) -> bpftool -> vmlinux.h
   prog.c + vmlinux.h -> Clang (-target bpf -g) -> prog.o (with .BTF and .BTF.ext)

2. Target Server (Any Linux Kernel with CONFIG_DEBUG_INFO_BTF=y):
   libbpf loads prog.o -> Reads target /sys/kernel/btf/vmlinux
   Resolves struct field byte offsets dynamically -> Patches bytecode in memory
   Calls bpf(BPF_PROG_LOAD) with relocated offsets -> Verifier succeeds!
```

* **`vmlinux.h`:** A single header file generated via `bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h`. Contains every single type, struct, union, and enum definition in the kernel.
* **Clang Built-ins:** Clang records relocatable field accesses (`__builtin_preserve_access_index()`). If an eBPF program accesses `task->pid`, Clang writes a relocation record into the `.BTF.ext` ELF section specifying: *"Access field `pid` in `struct task_struct`"*.
* **Load-Time Relocation by `libbpf`:** When `libbpf` loads the precompiled ELF object onto a production machine, it reads `/sys/kernel/btf/vmlinux` on that host. If `pid` moved from offset `1240` to offset `1256` in that kernel version, `libbpf` patches the instruction offset before submitting it to the `bpf()` system call.

---

## 5. Production Implementations

### Example 1: High-Performance XDP Syn-Flood Packet Dropper
This production XDP program inspects incoming IPv4 TCP packets directly at the NIC driver layer, dropping TCP SYN packets targeting port 80 without allocating an `sk_buff`.

```c
// packet_filter.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define ETH_P_IP 0x0800
#define IPPROTO_TCP 6

// Counter map: Key = dropped packet count
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} drop_stats SEC(".maps");

SEC("xdp")
int filter_syn_flood(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    // 1. Boundary check Ethernet Header (MANDATORY FOR VERIFIER)
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    // 2. Boundary check IPv4 Header
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;

    // 3. Boundary check TCP Header
    struct tcphdr *tcp = (void *)((__u32 *)ip + ip->ihl);
    if ((void *)(tcp + 1) > data_end)
        return XDP_PASS;

    // 4. Inspect TCP Flags: Drop SYN packets to Port 80
    if (bpf_ntohs(tcp->dest) == 80 && tcp->syn && !tcp->ack) {
        __u32 key = 0;
        __u64 *count = bpf_map_lookup_elem(&drop_stats, &key);
        if (count) {
            *count += 1;
        }
        return XDP_DROP;
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

### Example 2: Observability Ring-Buffer Tracepoint
This program attaches to the kernel's `sys_enter_execve` tracepoint to capture command executions across all processes.

```c
// exec_tracer.bpf.c
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>

struct event_t {
    __u32 pid;
    __u32 uid;
    char comm[16];
    char filename[256];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024); // 256KB buffer
} events SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_execve")
int trace_execve(struct trace_event_raw_sys_enter *ctx) {
    struct event_t *event;

    // Reserve space in lockless ring buffer
    event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);
    if (!event)
        return 0; // Buffer full, drop event

    __u64 pid_tgid = bpf_get_current_pid_tgid();
    event->pid = pid_tgid >> 32;
    event->uid = bpf_get_current_uid_gid();

    bpf_get_current_comm(&event->comm, sizeof(event->comm));

    // Safely read user-space filename pointer
    const char *filename_ptr = (const char *)ctx->args[0];
    bpf_probe_read_user_str(&event->filename, sizeof(event->filename), filename_ptr);

    // Commit event to ring buffer for user-space consumption
    bpf_ringbuf_submit(event, 0);
    return 0;
}

char _license[] SEC("license") = "GPL";
```

---

## 6. Failure Domains, Edge Cases & Verification Traps

### Traps that Break the Verifier

| Failure Manifestation | In-Kernel Root Cause | Engineering Solution |
| :--- | :--- | :--- |
| `invalid access to packet, memptr=...` | Dereferencing a packet header without first checking `(ptr + sizeof(hdr)) <= ctx->data_end`. | Always place an explicit `if ((void*)(hdr + 1) > data_end) return XDP_PASS;` guard immediately before accessing memory. |
| `Look up in map failed: R1 type=scalar expected=map_ptr` | Passing a regular integer variable instead of a reference to a map struct into `bpf_map_lookup_elem()`. | Pass the address of the map symbol: `bpf_map_lookup_elem(&map_name, &key)`. |
| `R10 is read only` | Code attempted to increment or write to stack pointer `R10`. | Never modify `R10`. Allocate local stack arrays/structs and allow Clang to reference them relative to `R10`. |
| `math between PTR_TO_STACK and SCALAR_VALUE failed` | Dynamic, variable-length indexing into stack arrays (e.g., `buf[var_idx] = x;`). | The verifier requires statically provable stack offsets. Unroll loops with `#pragma unroll` or use a per-CPU array map as scratch space. |
| `program size exceeds 1000000 instructions` | Complex loop or deep function inlining exceeding the verifier's instruction complexity limit. | Split logic into multiple programs chained via `BPF_MAP_TYPE_PROG_ARRAY` (tail calls) or use BPF-to-BPF subprograms. |

---

## 7. Key Takeaways

1. **Bare-Metal Speed with Proven Safety:** eBPF combines native JIT execution speeds with absolute kernel memory safety proven at load time by the static verifier.
2. **Event-Driven Architecture:** eBPF hooks into network drivers (XDP), kernel schedulers (sched_switch), system call tables (tracepoints), and hardware probes (kprobes/uprobes).
3. **Decoupled State via Maps:** All state persistence and user-kernel communication is handled by specialized, lockless data structures (e.g., `BPF_MAP_TYPE_RINGBUF` and `PERCPU_HASH`).
4. **Binary Portability:** CO-RE and BTF allow compiling a single ELF binary on a development machine that runs reliably across any modern Linux distribution without local compiler dependencies.
