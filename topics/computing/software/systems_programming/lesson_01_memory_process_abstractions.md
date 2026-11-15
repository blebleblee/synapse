# Lesson 1: Memory and Process Abstractions

## 1. First-Principles Intuition & Invariants

Every operating system is, at its core, a trusted intermediary between competing programs and finite hardware. When you run two processes simultaneously on the same machine, each one behaves as though it owns the CPU and all of memory. This illusion does not come cheap. It is the product of hardware mechanisms, kernel bookkeeping, and decades of carefully negotiated abstractions—and understanding it at the mechanical level is the difference between a programmer who uses a system and one who can reason about, debug, or build one.

The foundational problem is simple to state: memory is a single, flat array of addressable bytes, but we want multiple programs to use it concurrently, in isolation, without the ability to corrupt one another or the kernel itself. The naive solution—dividing physical RAM into static partitions assigned to each process—fails almost immediately. Programs do not know at compile time where they will be loaded. Libraries must be shared across processes without duplication. A process's memory footprint grows and shrinks dynamically. And a buggy or malicious process cannot be permitted to index outside its assigned region.

Virtual memory is the mechanism that resolves all of these constraints simultaneously. Rather than giving each process a slice of physical RAM, the hardware gives every process its own private, uniform address space—64-bit x86 Linux processes see a space from `0x0000000000000000` through `0x00007fffffffffff` for user space, with the upper half reserved for the kernel—and the CPU performs address translation on every memory access, mapping virtual addresses to physical ones through a structure called the page table. Physical RAM is subdivided into fixed-size units called page frames, typically 4 KiB, and virtual memory is subdivided into pages of the same size. The kernel populates page table entries to describe which physical frame backs each virtual page, what permissions the page carries (readable, writable, executable), and whether the page is currently resident in RAM at all.

The critical invariant here is that virtual addresses are process-local. The same virtual address `0x401000` in two different processes maps to two entirely different physical frames, or possibly to the same frame if they share a read-only mapping (as with shared libraries). The hardware enforces this isolation without any software involvement at the moment of access: the Memory Management Unit (MMU) is a dedicated silicon component on the CPU die that walks the page table in hardware, translates every load and store, and raises a page fault exception if the access is invalid. The kernel never sees correct memory accesses; it only gets called when something is wrong or missing.

This design has a profound consequence for systems programmers. Memory safety bugs are not caught at the source of the write; they are caught at the point of access, if at all, by hardware that only knows about pages and permissions. A stack buffer overflow that overwrites adjacent memory within the same page produces no fault. The x86 MMU has no concept of arrays, structs, or return addresses—it only knows about 4 KiB-aligned pages with rwx bits. This is precisely why stack canaries, ASLR, shadow stacks, and compiler sanitizers exist: they layer software-level invariant checking on top of a hardware model that is too coarse-grained to provide it natively.

The second major abstraction layered on top of virtual memory is the process itself. A process is not a program. A program is an ELF binary sitting on disk, a static artifact containing machine code, relocation tables, and metadata. A process is the runtime instantiation of that program: it has a virtual address space, one or more threads of execution, open file descriptors, signal dispositions, a working directory, credentials, resource limits, and a kernel-managed control structure called the `task_struct` in Linux. Processes are the kernel's unit of isolation. Threads within the same process share the address space, file descriptors, and signal handlers but have independent stacks, register contexts, and scheduling state. The kernel's scheduler operates on threads (`task_struct` nodes), but isolation policy—seccomp filters, namespaces, cgroups—is enforced at process granularity.

Understanding these two invariants—virtual memory as the isolation substrate and the process as the resource management unit—is the prerequisite for every systems programming topic that follows. TLB shootdowns, fork-on-write semantics, ELF loading, `mmap` internals, and context switching all make mechanical sense only when you can visualize the page table, the kernel's per-process metadata, and the hardware that intermediates every access.

---

## 2. Core Architecture & Mechanics

### The x86-64 Page Table Hierarchy

Modern x86-64 hardware uses a four-level page table (PML4, PDP, PD, PT) under the 4-level paging mode, or five levels (PML5) when LA57 is enabled on processors that support it. We will work with the standard four-level structure, which covers 48-bit virtual addresses and is what every mainstream Linux distribution uses unless explicitly configured otherwise.

A 48-bit virtual address is decoded by the hardware as five fields:

```
Bits [47:39]  →  PML4 index     (9 bits, 512 entries)
Bits [38:30]  →  PDP index      (9 bits, 512 entries)
Bits [29:21]  →  PD index       (9 bits, 512 entries)
Bits [20:12]  →  PT index       (9 bits, 512 entries)
Bits [11:0]   →  Page offset    (12 bits, 4096 bytes)
```

Each level is a 4 KiB table of 512 eight-byte entries. The root PML4 table's physical address is stored in the `CR3` register, which the kernel loads on every context switch to swap address spaces. Each entry at every level holds the physical base address of the next-level table (or the final physical frame at the PT level), along with control bits: Present (P), Read/Write (R/W), User/Supervisor (U/S), Execute-Disable (NX), Accessed (A), and Dirty (D).

```
Virtual Address (48-bit):
┌──────────┬──────────┬──────────┬──────────┬────────────┐
│ PML4[9b] │  PDP[9b] │  PD[9b]  │  PT[9b]  │ Offset[12] │
└──────────┴──────────┴──────────┴──────────┴────────────┘
     │            │         │         │
     ▼            ▼         ▼         ▼
   CR3──►PML4──►PDP──►PD──►PT──►Physical Frame
                                        │
                                        ▼
                               Physical Address = Frame Base + Offset
```

The MMU performs this walk autonomously in hardware, caching the result in the Translation Lookaside Buffer (TLB). The TLB is a small, fully-associative cache—typically 64 entries for the L1 iTLB, 64 for L1 dTLB, and a 1024-entry L2 stlb on recent Intel microarchitectures—that maps recently used virtual-to-physical page translations. On a TLB hit, translation costs zero cycles beyond the normal cache access. On a miss, the hardware page table walker performs a full four-level walk, touching four distinct cache lines from four tables scattered across physical memory, costing tens to hundreds of cycles depending on whether those entries are in the L2/L3 cache or require DRAM access.

The kernel manages the page tables it creates per process. In Linux, the top of this structure is `mm_struct`, the memory management descriptor embedded (by pointer) in every `task_struct`. The `mm_struct` holds the PGD (Page Global Directory, the kernel's name for the PML4 root), the VMA (Virtual Memory Area) red-black tree, memory statistics, and the reference count for shared address spaces (threads sharing the same `mm_struct`). The VMA tree maps contiguous ranges of the virtual address space to their backing: anonymous memory, file-backed mappings, device memory, or special regions like the vDSO.

```
task_struct
  └─► mm_struct
        ├─ pgd              ← physical address of PML4 (loaded into CR3)
        ├─ mmap            ← linked list head of VMAs
        ├─ mm_rb            ← red-black tree root for O(log n) VMA lookup
        ├─ start_code / end_code
        ├─ start_data / end_data
        ├─ start_brk / brk ← heap boundaries
        └─ start_stack
```

Each `vm_area_struct` (VMA) records the virtual start and end address, the `vm_flags` (VM_READ, VM_WRITE, VM_EXEC, VM_SHARED), and a pointer to a `vm_operations_struct` that provides the fault handler called when a page in that region is accessed without a valid PTE. This layering—MMU raises fault, kernel looks up VMA, VMA's fault handler resolves the backing—is the architecture that makes demand paging, copy-on-write, and memory-mapped files all composable on the same code path.

### Process Lifecycle: fork, exec, and ELF Loading

The process lifecycle in Unix is built from three primitives: `fork(2)`, `exec(2)`, and `exit(2)`. Their interaction is not incidental—it is a deliberate design that separates process creation from program loading, giving the shell (and any other process manager) a window to manipulate file descriptors, signal masks, and namespaces between the two calls.

`fork()` creates a child process by duplicating the calling process's `task_struct`, `mm_struct`, and all VMAs. The critical optimization is copy-on-write (COW): rather than copying every page of the parent's address space at fork time, the kernel marks all writable pages in both parent and child as read-only. When either process first writes to such a page, the MMU raises a protection fault. The kernel's fault handler detects the COW condition from the VMA flags, allocates a fresh physical frame, copies the content of the original frame into it, installs a new writeable PTE in the faulting process's page table pointing to the new frame, and restores the write permission on the original frame for the other process. The result is that fork is O(1) in terms of data copied—only page table entries are duplicated, not data—and pages are individualized lazily only when actually modified.

`execve()` replaces the current process's address space entirely. The kernel reads the ELF header of the target binary to determine the program interpreter (usually `/lib64/ld-linux-x86-64.so.2`), tears down all existing VMAs (calling `munmap` equivalents on each), and builds a new address space. It creates VMAs backed by the ELF binary's file for the text and rodata segments (VM_READ | VM_EXEC), anonymous writeable VMAs for BSS and the initial heap, and a stack VMA. Crucially, it does not load any of these pages into RAM at this point. The VMAs exist, the PTEs do not. Every page access on the new process triggers a page fault, which the VMA's fault handler resolves by reading from the ELF file on demand.

The dynamic linker is mapped into the process's address space by the kernel's ELF loader and receives control before `main()`. It resolves shared library dependencies, maps them into the address space (again, demand-paged from their on-disk ELF files), performs relocations, and executes constructor functions before transferring control to the program's entry point. Shared library text segments are mapped VM_SHARED and read-only, meaning a single physical copy of `libc`'s code backs all processes using it simultaneously—the same physical frames appear in thousands of page tables under different virtual addresses, all marked non-writeable with the NX bit set only in page directories where the kernel configures it.

The following C program lets you observe the VMA layout of a live process directly from its own address space:

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

#define MAPS_PATH "/proc/self/maps"
#define BUF_SIZE  4096

int main(void) {
    char *heap_alloc = malloc(1024);
    if (!heap_alloc) {
        perror("malloc");
        return 1;
    }

    memset(heap_alloc, 0xAB, 1024);  /* dirty the heap page */

    int fd = open(MAPS_PATH, O_RDONLY);
    if (fd < 0) {
        perror("open");
        free(heap_alloc);
        return 1;
    }

    char buf[BUF_SIZE];
    ssize_t n;
    printf("=== /proc/self/maps (PID %d) ===\n", getpid());
    while ((n = read(fd, buf, sizeof(buf) - 1)) > 0) {
        buf[n] = '\0';
        fputs(buf, stdout);
    }

    close(fd);
    free(heap_alloc);
    return 0;
}
```

Compile and run this with `gcc -O0 -o vma_inspect vma_inspect.c && ./vma_inspect`. The output maps every VMA in the process: the ELF text segment (`r-xp`), rodata (`r--p`), writeable data (`rw-p`), the heap (`[heap]`), each mapped shared library with its own text/data/bss regions, the stack (`[stack]`), and the kernel-injected vDSO and vvar pages. The permissions column (`r-xp`, `rw-p`, `r--p`) maps directly to the `vm_flags` field in each `vm_area_struct`. The final character—`p` for private (COW) or `s` for shared—indicates whether writes will be isolated to this process or propagated through the mapping.

For deeper inspection, `/proc/self/pagemap` provides a 64-bit entry per virtual page that includes the physical frame number (PFN), soft-dirty bit, and whether the page is present in RAM or swapped out. Reading it requires root on most systems to prevent cross-process physical address inference, but it is invaluable for performance analysis and debugging:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>

#define PAGE_SIZE       4096UL
#define PAGEMAP_ENTRY   8UL
#define PM_PRESENT      (1ULL << 63)
#define PM_PFN_MASK     ((1ULL << 55) - 1)

static uint64_t virt_to_phys(int pagemap_fd, uintptr_t vaddr) {
    off_t offset = (vaddr / PAGE_SIZE) * PAGEMAP_ENTRY;
    uint64_t entry = 0;

    if (pread(pagemap_fd, &entry, PAGEMAP_ENTRY, offset) != (ssize_t)PAGEMAP_ENTRY) {
        perror("pread pagemap");
        return 0;
    }

    if (!(entry & PM_PRESENT)) {
        fprintf(stderr, "Page at vaddr %p is not present in RAM\n", (void *)vaddr);
        return 0;
    }

    uint64_t pfn = entry & PM_PFN_MASK;
    return (pfn * PAGE_SIZE) + (vaddr & (PAGE_SIZE - 1));
}

int main(void) {
    char *buf = aligned_alloc(PAGE_SIZE, PAGE_SIZE * 4);
    if (!buf) { perror("aligned_alloc"); return 1; }

    /* Write to each page to fault it in and make it present. */
    for (size_t i = 0; i < 4; i++) {
        buf[i * PAGE_SIZE] = (char)(i + 1);
    }

    int pm_fd = open("/proc/self/pagemap", O_RDONLY);
    if (pm_fd < 0) { perror("open pagemap"); free(buf); return 1; }

    printf("%-20s  %-20s\n", "Virtual Address", "Physical Address");
    for (size_t i = 0; i < 4; i++) {
        uintptr_t vaddr = (uintptr_t)(buf + i * PAGE_SIZE);
        uint64_t paddr  = virt_to_phys(pm_fd, vaddr);
        printf("0x%016lx  0x%016lx\n", vaddr, paddr);
    }

    close(pm_fd);
    free(buf);
    return 0;
}
```

Compile with `gcc -O0 -o pagemap_probe pagemap_probe.c` and run as root. The output will show four virtually contiguous pages mapped to physically discontiguous frames—a direct demonstration that the kernel's physical allocator makes no guarantees about physical contiguity for anonymous mappings, and why DMA buffers and certain device drivers must use `dma_alloc_coherent()` to obtain physically contiguous memory.

### Context Switching: Register State and CR3 Reload

A context switch is the act of suspending one thread's execution and resuming another's. On x86-64 Linux, it occurs in the scheduler's `__schedule()` function, which calls `context_switch()`, which in turn calls `switch_mm()` (to swap address spaces if the new thread belongs to a different process) and `switch_to()` (to swap CPU register state).

`switch_mm()` is where `CR3` is reloaded. Writing a new value to `CR3` immediately invalidates all TLB entries tagged with the previous PCID (Process Context Identifier) if PCID support is not in use, or switches the hardware's active PCID context if it is. PCID is a 12-bit tag that the CPU appends to TLB entries, allowing TLB entries from multiple address spaces to coexist in the TLB simultaneously. When switching from process A to process B, with PCID support, the kernel can avoid flushing the entire TLB and instead simply change the active PCID; subsequent accesses by B will fill TLB entries tagged with B's PCID, while A's entries remain and can be reused when A is next scheduled without a full TLB rebuild. Without PCID (or when deliberately flushing with `CR4.PCIDE=0`), every context switch to a different process incurs a full TLB flush, meaning the first N accesses in the new process must each pay for a hardware page table walk.

`switch_to()` saves and restores the general-purpose registers, the instruction pointer (via the `ret` trick on the kernel stack), the stack pointer, and the FPU/SSE/AVX state (lazily, using the TS bit in CR0 to trap on first FP instruction after a switch). The full register context is not stored in a monolithic struct; instead, the kernel stack itself encodes the return point. When `switch_to()` suspends thread A, it pushes `RIP` onto A's kernel stack and saves `RSP` into `task_struct->thread.sp`. When A is next scheduled, `switch_to()` restores `RSP` and executes `ret`, which pops `RIP` and resumes A exactly where it left off in `__schedule()`.

```
Thread A kernel stack                Thread B kernel stack
(suspended mid-schedule)            (about to be resumed)

   ┌───────────────────┐               ┌───────────────────┐
   │  saved RIP        │◄── RSP(A)     │  saved RIP        │◄── RSP(B)
   │  saved RBP        │               │  saved RBP        │
   │  saved RBX        │               │  saved RBX        │
   │  saved R12–R15    │               │  saved R12–R15    │
   │  ...              │               │  ...              │
   └───────────────────┘               └───────────────────┘

switch_to(A, B):
  1. Push callee-saved regs onto A's kernel stack
  2. Save RSP → task_struct(A)->thread.sp
  3. Load RSP ← task_struct(B)->thread.sp
  4. Pop callee-saved regs from B's kernel stack
  5. ret  →  resumes execution in B at its saved RIP
```

The user-visible register state (all general-purpose registers, `RFLAGS`, segment registers, and the FPU context) is captured on the kernel stack in a `pt_regs` structure when the process enters the kernel via a syscall, interrupt, or exception. When the kernel returns to user space, it restores these registers and executes `sysretq` or `iretq`. This means the kernel never needs to know the user process's register state during scheduling—it only needs to manage the kernel-mode execution context. The user registers are preserved on the per-thread kernel stack, insulated from scheduler activity.

---

## 3. High-Performance Optimization & Failure Modes

### TLB Pressure, Huge Pages, and NUMA Topology

The most consequential performance variable in memory-intensive systems programs is TLB pressure. A process whose working set spans thousands of 4 KiB pages will incur TLB misses at a rate that depends on the ratio of its active page count to the TLB's capacity. For large-scale in-memory databases, scientific computing kernels, or JVM heaps, this can account for 20–40% of total execution time—the CPU is spending a substantial fraction of its cycles walking page tables in hardware rather than executing application logic.

The primary mitigation is transparent huge pages (THP) or explicit `mmap` with `MAP_HUGETLB`. A 2 MiB huge page requires only a single TLB entry instead of 512, reducing TLB pressure by that factor for sequential access patterns. On x86-64, 2 MiB huge pages are encoded in the PD level by setting the PS (Page Size) bit in the PDE, bypassing the PT level entirely. The page offset field expands to 21 bits, and the physical base address in the PDE must be 2 MiB-aligned. The kernel's THP daemon (`khugepaged`) scans anonymous VMAs and collapses adjacent 512 4 KiB pages into a single huge page when physical memory permits the allocation of a contiguous 2 MiB frame. For latency-sensitive workloads, the collapse operation itself—which requires taking the VMA lock and performing a TLB shootdown across all CPUs that have mapped the region—is a source of tail latency jitter, which is why some production systems (PostgreSQL's `huge_pages=try`, certain JVM flags) control huge page allocation explicitly rather than relying on THP.

For NUMA (Non-Uniform Memory Access) systems, physical frame placement matters as much as huge page status. The kernel's NUMA balancing subsystem periodically unmaps pages from NUMA-remote processes (by clearing the PTE's Present bit without freeing the frame), waits for the resulting page faults to identify which NUMA node the faulting thread runs on, and migrates the frame to local memory if the access pattern warrants it. This is called NUMA hinting faults or AutoNUMA. For latency-critical applications, the correct approach is to control NUMA placement explicitly using `mbind(2)`, `set_mempolicy(2)`, or `numactl` at process launch—and to validate placement with `numastat` and `perf stat -e dTLB-load-misses,node-load-misses`.

The following program demonstrates the measurable cost of TLB pressure by comparing sequential access over 4 KiB pages versus 2 MiB huge pages at the same total allocation size:

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <unistd.h>

#define ALLOC_SIZE   (512UL * 1024 * 1024)   /* 512 MiB */
#define PAGE_4K      4096UL
#define PAGE_2M      (2UL * 1024 * 1024)
#define ITERATIONS   4

static double ns_per_byte(void *buf, size_t len, size_t stride) {
    struct timespec t0, t1;
    volatile char sink = 0;

    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (int iter = 0; iter < ITERATIONS; iter++) {
        for (size_t off = 0; off < len; off += stride) {
            sink += ((volatile char *)buf)[off];
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &t1);

    double elapsed_ns = (t1.tv_sec - t0.tv_sec) * 1e9 +
                        (t1.tv_nsec - t0.tv_nsec);
    size_t total_bytes = (len / stride) * ITERATIONS;
    (void)sink;
    return elapsed_ns / (double)total_bytes;
}

int main(void) {
    /* Standard anonymous mapping: kernel uses 4 KiB pages. */
    void *buf_4k = mmap(NULL, ALLOC_SIZE,
                        PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS,
                        -1, 0);
    if (buf_4k == MAP_FAILED) { perror("mmap 4k"); return 1; }
    memset(buf_4k, 1, ALLOC_SIZE);   /* fault in all pages */

    /* Huge page mapping: each page is 2 MiB, 512x fewer TLB entries needed. */
    void *buf_2m = mmap(NULL, ALLOC_SIZE,
                        PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                        -1, 0);
    if (buf_2m == MAP_FAILED) {
        perror("mmap hugetlb (is vm.nr_hugepages set?)");
        munmap(buf_4k, ALLOC_SIZE);
        return 1;
    }
    memset(buf_2m, 1, ALLOC_SIZE);

    /*
     * Stride = 4096 to touch every page, maximizing TLB pressure.
     * With 4K pages: 131072 unique pages → TLB thrashing guaranteed.
     * With 2M pages: 256 unique pages   → fits comfortably in L2 TLB.
     */
    double t4k = ns_per_byte(buf_4k, ALLOC_SIZE, PAGE_4K);
    double t2m = ns_per_byte(buf_2m, ALLOC_SIZE, PAGE_4K);

    printf("4 KiB pages:  %.3f ns/access\n", t4k);
    printf("2 MiB pages:  %.3f ns/access\n", t2m);
    printf("Speedup:      %.2fx\n", t4k / t2m);

    munmap(buf_4k, ALLOC_SIZE);
    munmap(buf_2m, ALLOC_SIZE);
    return 0;
}
```

Before running, reserve huge pages with `sudo sysctl -w vm.nr_hugepages=256`. Compile with `gcc -O2 -o tlb_bench tlb_bench.c` and run as a user that has access to huge pages (check `/proc/meminfo` for `HugePages_Free`). On an Intel Core i7 or similar, expect the 2 MiB variant to run 3–8× faster at this access pattern, with the gap widening as the working set exceeds the L2 TLB capacity.

### Fork Bomb and VMA Exhaustion

The COW mechanism that makes `fork()` efficient under normal workloads becomes a liability under adversarial or accidental pressure. A process with a large heap that immediately mutates most of its pages after forking will trigger COW faults at a rate proportional to its dirty working set size, causing the kernel to allocate one new physical frame per faulting page. If multiple children fork simultaneously and all modify the same pages, physical memory demand scales as `parent_dirty_pages × child_count`. This is the OOM (Out-of-Memory) killer scenario that terminates production database processes: a monitoring script forks a child of a 32 GiB PostgreSQL process, the child immediately triggers tens of thousands of COW faults, the kernel runs out of overcommit budget, and the OOM killer selects the largest process—the database—as its victim.

The mitigation at the application level is to minimize the dirty footprint before forking—flush writable caches, call `madvise(MADV_DONTNEED)` on memory regions the child does not need, or use `posix_spawn()` which on Linux takes a `vfork()`-style shortcut that avoids duplicating the address space entirely at the cost of blocking the parent until the child execs. At the system level, `vm.overcommit_memory=2` with an appropriate `vm.overcommit_ratio` prevents the kernel from promising memory it cannot back, causing `mmap` and `brk` to fail early rather than OOM-killing processes later.

VMA exhaustion is a subtler failure mode. The kernel limits the number of VMAs per process via `/proc/sys/vm/max_map_count`, which defaults to 65530. Each `mmap` call that creates a non-adjacent, non-mergeable region consumes one VMA. JVMs, Rust programs using jemalloc, and applications performing fine-grained `mmap`-based I/O can exhaust this limit, causing `mmap` to return `ENOMEM` even when physical memory is plentiful. The diagnostic is to check `cat /proc/<pid>/maps | wc -l` and compare against `max_map_count`. Raising the limit is straightforward (`sysctl -w vm.max_map_count=262144`), but the correct fix is usually to audit why so many discrete mappings are being created—each VMA lookup on a page fault is an O(log N) operation on the red-black tree, so a process with 60,000 VMAs will pay measurably higher fault latency than one with 600.

### Page Fault Latency and mlock

For real-time and latency-sensitive applications, demand paging itself is the enemy. The first access to any page in a demand-paged VMA triggers a fault, which requires a kernel entry, a VMA lookup, potentially a file read, a PTE installation, and a TLB fill—a path that can take microseconds, an eternity for a low-latency trading system or a time-sensitive audio callback. The solution is `mlock(2)` or `mlockall(MCL_CURRENT | MCL_FUTURE)`, which instructs the kernel to fault in and wire all pages in the specified range, pinning them in physical RAM and prohibiting the swap daemon from evicting them. After `mlockall`, a second-pass write over the entire allocation forces every page fault to occur during initialization, leaving the application's steady-state path free of kernel entries for memory access.

```c
#define _GNU_SOURCE
#include <sys/mman.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int lock_and_prefault(void *addr, size_t len) {
    if (mlock(addr, len) != 0) {
        perror("mlock");
        return -1;
    }
    /*
     * mlock guarantees pages are resident after the first fault.
     * We write to every page now to trigger those faults during
     * initialization rather than during the latency-sensitive path.
     */
    volatile char *p = (volatile char *)addr;
    for (size_t i = 0; i < len; i += 4096) {
        p[i] = 0;
    }
    return 0;
}

int main(void) {
    const size_t buf_size = 64UL * 1024 * 1024;  /* 64 MiB */

    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0) {
        perror("mlockall (requires CAP_IPC_LOCK or sufficient RLIMIT_MEMLOCK)");
        return 1;
    }

    void *buf = aligned_alloc(4096, buf_size);
    if (!buf) { perror("aligned_alloc"); return 1; }

    if (lock_and_prefault(buf, buf_size) != 0) {
        free(buf);
        return 1;
    }

    printf("Buffer at %p (%zu MiB) locked and pre-faulted.\n",
           buf, buf_size / (1024 * 1024));

    /* Application hot path: no page faults will occur here. */
    memset(buf, 0xFF, buf_size);

    free(buf);
    return 0;
}
```

`mlockall` requires either `CAP_IPC_LOCK` or a `RLIMIT_MEMLOCK` large enough to cover the requested range. In production, grant the binary `CAP_IPC_LOCK` via file capabilities (`setcap cap_ipc_lock=ep ./binary`) rather than running as root. Verify that no faults occur in the hot path with `perf stat -e page-faults ./binary`—after correct prefaulting, the page fault counter should be zero (or bounded to kernel-internal bookkeeping) during the steady-state execution phase.

The habit of thinking in page tables, VMAs, CR3 reloads, and fault paths is not an academic exercise. It is the operational vocabulary that lets you diagnose why a JVM GC pause is 40% TLB-miss overhead, why a `fork`-based job server OOM-kills under load, or why a lock-free data structure still exhibits false sharing because two independent objects share a cache line within the same physical page. Every abstraction the kernel offers—`mmap`, `fork`, threads, shared libraries—is a composition of the page table mechanics and process metadata described here. Mastering these layers means you are reasoning about what the hardware actually does, not just what the documentation claims it does.
