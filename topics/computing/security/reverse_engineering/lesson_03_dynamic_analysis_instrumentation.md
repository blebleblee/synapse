# Lesson 3: Dynamic Analysis and Instrumentation

## 1. First-Principles Intuition & Invariants

Static analysis reads the map. Dynamic analysis walks the terrain. The distinction is not merely methodological convenience but reflects a fundamental epistemological divide: no amount of disassembly fully predicts the runtime behavior of code that unpacks itself, resolves imports lazily, branches on hardware-specific conditions, or deliberately misleads static tooling with opaque predicates. For the reverse engineer, the program must run to reveal itself completely, and that revelation demands a disciplined framework for observing, interrupting, and modifying execution without destroying the very state you are trying to understand.

The central invariant of dynamic analysis is non-interference fidelity: your instrumentation must perturb the target as little as possible while extracting as much information as possible. This invariant is perpetually under tension. Every observer effect matters. A software breakpoint changes the opcode stream. A watchpoint stalls the memory bus. A timing-sensitive anti-debug check detects the microsecond latency introduced by a trap. Understanding dynamic analysis at the level demanded by offensive security work means understanding *why* each instrumentation primitive costs what it costs, at the hardware and operating system level, so you can reason precisely about where the fidelity budget is being spent.

Modern processors execute instructions on behalf of privilege rings, and the entire debugger ecosystem rests on the hardware's willingness to transfer control to a more privileged context when certain conditions are met. On x86-64, the debug architecture provides four address-breakpoint registers (DR0–DR3), a control register (DR7) that specifies their trigger conditions, and a status register (DR6) that records which condition fired. When the CPU honors a debug condition, it delivers a debug exception (#DB, vector 1) before or after the faulting instruction, depending on the breakpoint type. The operating system fields that exception through its IDT handler, translates it into a signal (SIGTRAP on POSIX) or a debug event (on Windows), and routes it to the debugger process, which then pauses the target and waits for commands. This four-layer stack — CPU exception → OS handler → debug API → debugger front-end — is the substrate on which every tool from GDB to WinDbg to a custom PIN pintool is built. Mastery of dynamic analysis begins with the ability to reason about all four layers simultaneously.

The same hardware architecture that enables debugging also defines the attack surface for anti-analysis. Packed malware, firmware rootkits, and obfuscated binaries use a consistent playbook: they check for the presence of debug registers with non-zero values, measure execution time across critical sections with RDTSC, probe for the INT3 (0xCC) byte that software breakpoints write into the opcode stream, and test OS-visible state like the PEB.NtGlobalFlag on Windows. Each of these attacks targets a specific layer of the debug stack, and defeating them requires interventions at the corresponding layer — not at the front end of your debugger GUI.

For embedded and hardware security work, the problem space shifts meaningfully. A microcontroller running bare-metal firmware has no operating system to mediate debug events. The hardware debug port — JTAG, SWD, or a vendor-specific variant — is the only practical path to observation. The CPU's debug unit speaks directly with an external probe, and the communication protocol (OpenOCD over JTAG, pyOCD over SWD, Segger J-Link over its proprietary wire) replaces the OS debug API entirely. Everything that a Linux kernel does to serialize debug events and present them as ptrace calls, the debug probe firmware does instead. When the target CPU halts on a hardware breakpoint, the probe reads register state over the debug transport and surfaces it to your host toolchain. The latency is higher, the bandwidth is lower, and the target's clock may stop entirely during the halt, making timing measurements from RDTSC meaningless — which is precisely why hardware breakpoints defeat many timing-based anti-debug strategies that plague software-only analysis.

## 2. Core Architecture & Mechanics

### The Debugger Execution Loop

Every interactive debugger, regardless of front-end complexity, implements the same fundamental loop: attach to a process, wait for a debug event, present state to the analyst, accept a command, resume execution. The sophistication lies entirely in the mechanics of each step.

On Linux, the ptrace system call is the kernel's debug API. A tracer process invokes `ptrace(PTRACE_ATTACH, pid, ...)` to seize a target, which delivers SIGSTOP to the tracee and blocks it. From that point, the tracer drives the target entirely through ptrace requests: `PTRACE_GETREGS` to read the full general-purpose register file, `PTRACE_PEEKDATA` to read arbitrary words from the target's address space (one word per syscall, an expensive design that hints at the kernel's assumption that this interface is used sparingly), `PTRACE_POKEDATA` to write, and `PTRACE_SINGLESTEP` to advance exactly one instruction by setting the x86 Trap Flag (TF, RFLAGS bit 8) before resuming, which causes the CPU to generate a #DB after the next instruction retires.

```
PTRACE_ATTACH
      │
      ▼
┌─────────────────────────────────────┐
│          Tracer (debugger)          │
│                                     │
│  waitpid() ◄──── SIGTRAP/SIGSTOP    │
│      │                              │
│  ptrace(GETREGS)                    │
│  ptrace(PEEKDATA/POKEDATA)          │
│      │                              │
│  ptrace(CONT / SINGLESTEP / ...)    │
└─────────────┬───────────────────────┘
              │  kernel debug events
              ▼
┌─────────────────────────────────────┐
│           Tracee (target)           │
│                                     │
│  User-mode execution                │
│  ┌─ SIGTRAP on INT3 breakpoint      │
│  ├─ SIGTRAP on TF single-step       │
│  └─ SIGTRAP on hardware watchpoint  │
└─────────────────────────────────────┘
```

The design has a critical performance implication: every single-step transition requires two context switches (tracee→kernel→tracer to deliver the event, tracer→kernel→tracee to resume), plus the ptrace syscall overhead on the tracer side. On a modern system this costs roughly 2–10 microseconds per instruction. At 10⁸ instructions per second of target throughput, full single-step tracing slows execution by four to five orders of magnitude. For short code paths this is acceptable; for unpacking loops that execute millions of instructions before producing useful output, it is not. This cost structure forces the analyst to think strategically about *where* to drop into single-step mode rather than applying it globally.

### Software Breakpoints: INT3 and the 0xCC Patch

The software breakpoint is the most common and cheapest dynamic analysis primitive. The mechanism is a single-byte opcode patch: the debugger saves the byte at the target address, writes 0xCC (INT3) in its place, and resumes the target. When execution reaches the patched address, the CPU decodes 0xCC as a single-byte breakpoint instruction, generates interrupt vector 3, and the OS delivers SIGTRAP (Linux) or a EXCEPTION_BREAKPOINT event (Windows) to the debugger. The debugger then restores the original byte, backs up RIP by one (because the saved RIP points to the byte *after* INT3, but the original instruction may be longer), and presents the halt to the analyst.

A complete, production-grade software breakpoint manager in C demonstrates the full lifecycle:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/user.h>

#define MAX_BREAKPOINTS 64

typedef struct {
    unsigned long addr;
    uint8_t       saved_byte;
    int           active;
} breakpoint_t;

static breakpoint_t bp_table[MAX_BREAKPOINTS];
static int          bp_count = 0;

/*
 * Write a single byte into the tracee's address space without
 * disturbing the surrounding bytes. ptrace works in word-sized
 * units, so we must read-modify-write around the target byte.
 */
static int poke_byte(pid_t pid, unsigned long addr, uint8_t byte, uint8_t *old_byte) {
    long word = ptrace(PTRACE_PEEKDATA, pid, (void *)addr, NULL);
    if (errno != 0) return -1;
    *old_byte = (uint8_t)(word & 0xFF);
    long patched = (word & ~0xFFL) | byte;
    if (ptrace(PTRACE_POKEDATA, pid, (void *)addr, (void *)patched) < 0) return -1;
    return 0;
}

int bp_set(pid_t pid, unsigned long addr) {
    if (bp_count >= MAX_BREAKPOINTS) return -1;
    breakpoint_t *bp = &bp_table[bp_count++];
    bp->addr = addr;
    bp->active = 1;
    if (poke_byte(pid, addr, 0xCC, &bp->saved_byte) < 0) {
        bp->active = 0;
        bp_count--;
        return -1;
    }
    printf("[bp] set at 0x%lx (saved byte: 0x%02x)\n", addr, bp->saved_byte);
    return 0;
}

/*
 * Restore the original byte and step past the instruction so
 * the breakpoint location can be re-armed on the next pass.
 */
int bp_hit(pid_t pid, unsigned long rip) {
    unsigned long bp_addr = rip - 1; /* RIP advanced past INT3 */
    for (int i = 0; i < bp_count; i++) {
        breakpoint_t *bp = &bp_table[i];
        if (!bp->active || bp->addr != bp_addr) continue;

        /* Restore original byte */
        uint8_t discard;
        if (poke_byte(pid, bp_addr, bp->saved_byte, &discard) < 0) return -1;

        /* Rewind RIP to the original instruction */
        struct user_regs_struct regs;
        if (ptrace(PTRACE_GETREGS, pid, NULL, &regs) < 0) return -1;
        regs.rip = bp_addr;
        if (ptrace(PTRACE_SETREGS, pid, NULL, &regs) < 0) return -1;

        printf("[bp] hit at 0x%lx | rip=0x%llx rsp=0x%llx rax=0x%llx\n",
               bp_addr, regs.rip, regs.rsp, regs.rax);
        return 0;
    }
    return -1; /* not our breakpoint */
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <pid> <hex_addr>\n", argv[0]);
        return 1;
    }
    pid_t pid = (pid_t)atoi(argv[1]);
    unsigned long addr = strtoul(argv[2], NULL, 16);

    if (ptrace(PTRACE_ATTACH, pid, NULL, NULL) < 0) {
        perror("ptrace attach"); return 1;
    }
    int status;
    waitpid(pid, &status, 0);

    bp_set(pid, addr);
    ptrace(PTRACE_CONT, pid, NULL, NULL);

    while (1) {
        waitpid(pid, &status, 0);
        if (WIFEXITED(status)) {
            printf("[*] tracee exited with code %d\n", WEXITSTATUS(status));
            break;
        }
        if (WIFSTOPPED(status) && WSTOPSIG(status) == SIGTRAP) {
            struct user_regs_struct regs;
            ptrace(PTRACE_GETREGS, pid, NULL, &regs);
            if (bp_hit(pid, regs.rip) == 0) {
                /* Re-arm: single-step past the original instruction, then
                 * re-write INT3. For brevity we just continue here. */
            }
        }
        ptrace(PTRACE_CONT, pid, NULL, NULL);
    }
    return 0;
}
```

This code is intentionally minimal but complete. The read-modify-write in `poke_byte` is the canonical pattern for single-byte injection because ptrace operates on natural-word-aligned units. The RIP adjustment in `bp_hit` reflects the CPU's behavior: after executing INT3, RIP points one byte past the 0xCC, so restoring the original opcode and subtracting one positions the program counter exactly on the original instruction. A production debugger would re-arm the breakpoint by single-stepping past the restored instruction and then re-patching, but the structural pattern is identical.

### Hardware Breakpoints and Watchpoints

Where software breakpoints modify the instruction stream, hardware breakpoints use the CPU's debug register file without touching memory at all. This makes them invisible to byte-scanning anti-debug checks and applicable to ROM or write-protected pages where the target cannot be patched. The x86-64 debug architecture provides four address comparators (DR0–DR3) and a control register (DR7) that specifies, for each comparator, the break condition (instruction fetch, one-byte write, one-byte read/write, two-byte read/write, four-byte read/write, or eight-byte read/write) and whether the breakpoint is globally or locally enabled.

Setting a hardware breakpoint via ptrace requires writing directly to the debug registers, which are accessible only from the kernel:

```c
#include <sys/ptrace.h>
#include <sys/user.h>

/*
 * Set a hardware execution breakpoint in DR0.
 * DR7 layout: L0 (bit 0) enables DR0 locally.
 * Condition bits for DR0 are at bits [17:16] (00 = execute).
 * Size bits for DR0 are at bits [19:18] (00 = 1-byte / execute).
 */
int hw_bp_set_exec(pid_t pid, unsigned long addr) {
    /* Write target address into DR0 */
    if (ptrace(PTRACE_POKEUSER, pid,
               offsetof(struct user, u_debugreg[0]),
               (void *)addr) < 0) {
        perror("set DR0"); return -1;
    }
    /* Enable DR0 locally; condition=execute (00), size=00 */
    unsigned long dr7 = 0;
    dr7 |= (1UL << 0);  /* L0: local enable for DR0 */
    /* bits [17:16] = 00 (execute), bits [19:18] = 00 (implicit for execute) */
    if (ptrace(PTRACE_POKEUSER, pid,
               offsetof(struct user, u_debugreg[7]),
               (void *)dr7) < 0) {
        perror("set DR7"); return -1;
    }
    printf("[hwbp] execution breakpoint at 0x%lx via DR0\n", addr);
    return 0;
}

/*
 * Set a hardware write watchpoint in DR1 for a 4-byte memory location.
 * DR7 condition bits for DR1 at [21:20]: 01 = write.
 * Size bits for DR1 at [23:22]: 11 = 4 bytes.
 */
int hw_bp_set_watch4(pid_t pid, unsigned long addr) {
    if (ptrace(PTRACE_POKEUSER, pid,
               offsetof(struct user, u_debugreg[1]),
               (void *)addr) < 0) {
        perror("set DR1"); return -1;
    }
    unsigned long dr7 = 0;
    dr7 |= (1UL << 2);       /* L1: local enable for DR1 */
    dr7 |= (0x1UL << 20);    /* condition: 01 = data write */
    dr7 |= (0x3UL << 22);    /* size: 11 = 4 bytes */
    if (ptrace(PTRACE_POKEUSER, pid,
               offsetof(struct user, u_debugreg[7]),
               (void *)dr7) < 0) {
        perror("set DR7"); return -1;
    }
    printf("[hwbp] 4-byte write watchpoint at 0x%lx via DR1\n", addr);
    return 0;
}
```

The four-register limit is a frequent constraint in practice. When reversing firmware that has more points of interest than available debug registers, the analyst must either multiplex breakpoints (set, hit, clear, set next) or rely on software breakpoints for lower-priority locations. For read watchpoints specifically, the hardware provides read/write (condition bits 11) but not read-only triggering on x86-64 — a subtle limitation that forces the use of software memory protection tricks (mprotect PROT_NONE on the page, trap the SIGSEGV, inspect the faulting address) when you need a pure read watchpoint.

### Memory Inspection and Register State

Reading the register file is straightforward through PTRACE_GETREGS, but interpreting register state demands context. On x86-64, general-purpose registers carry arguments (rdi, rsi, rdx, rcx, r8, r9 per the System V ABI), return values (rax, rdx for 128-bit returns), and frame pointers (rbp when the compiler preserves them, increasingly optional with frame-pointer-omission optimizations). The control registers accessible through PTRACE_GETREGS also include the segment registers (cs, ss, ds, es, fs, gs) and the RFLAGS register, whose individual bits carry the results of the most recent comparison: ZF (zero), SF (sign), OF (overflow), CF (carry). Reading RFLAGS at a conditional branch tells you exactly which way the branch will go before it executes, which is indispensable when stepping through obfuscated code that uses flag manipulation as a control flow primitive.

```c
#include <sys/ptrace.h>
#include <sys/user.h>
#include <stdio.h>

void dump_regs(pid_t pid) {
    struct user_regs_struct r;
    if (ptrace(PTRACE_GETREGS, pid, NULL, &r) < 0) {
        perror("GETREGS"); return;
    }
    printf("RIP: 0x%016llx  RSP: 0x%016llx  RBP: 0x%016llx\n",
           r.rip, r.rsp, r.rbp);
    printf("RAX: 0x%016llx  RBX: 0x%016llx  RCX: 0x%016llx\n",
           r.rax, r.rbx, r.rcx);
    printf("RDX: 0x%016llx  RSI: 0x%016llx  RDI: 0x%016llx\n",
           r.rdx, r.rsi, r.rdi);
    printf(" R8: 0x%016llx   R9: 0x%016llx  R10: 0x%016llx\n",
           r.r8,  r.r9,  r.r10);
    printf("R11: 0x%016llx  R12: 0x%016llx  R13: 0x%016llx\n",
           r.r11, r.r12, r.r13);
    printf("R14: 0x%016llx  R15: 0x%016llx\n", r.r14, r.r15);

    unsigned long long eflags = r.eflags;
    printf("RFLAGS: 0x%08llx  CF=%llu PF=%llu AF=%llu ZF=%llu SF=%llu OF=%llu\n",
           eflags,
           (eflags >> 0) & 1,  /* carry */
           (eflags >> 2) & 1,  /* parity */
           (eflags >> 4) & 1,  /* adjust */
           (eflags >> 6) & 1,  /* zero */
           (eflags >> 7) & 1,  /* sign */
           (eflags >> 11) & 1  /* overflow */
    );
}

/*
 * Read a contiguous region from the tracee's address space.
 * PTRACE_PEEKDATA delivers one machine word per call, so reading
 * N bytes requires ceil(N/8) syscalls on x86-64.
 */
void dump_mem(pid_t pid, unsigned long addr, size_t len) {
    printf("Memory at 0x%lx (%zu bytes):\n", addr, len);
    for (size_t off = 0; off < len; off += 8) {
        long word = ptrace(PTRACE_PEEKDATA, pid, (void *)(addr + off), NULL);
        uint8_t *b = (uint8_t *)&word;
        printf("  %016lx: ", addr + off);
        size_t chunk = (len - off < 8) ? len - off : 8;
        for (size_t j = 0; j < chunk; j++) printf("%02x ", b[j]);
        for (size_t j = chunk; j < 8; j++) printf("   ");
        printf(" |");
        for (size_t j = 0; j < chunk; j++)
            printf("%c", (b[j] >= 0x20 && b[j] < 0x7f) ? b[j] : '.');
        printf("|\n");
    }
}
```

For reading large memory regions efficiently, process_vm_readv and process_vm_writev bypass ptrace's one-word-per-syscall constraint entirely, transferring memory in bulk through two iovec arrays. This is the preferred approach for dumping packed or encrypted memory regions once a breakpoint has halted execution at a convenient post-unpack point.

### Runtime Code Patching

Runtime patching — overwriting instructions in the target's address space while it runs — is one of the most powerful techniques in the reverse engineer's toolkit and one of the most dangerous to execute carelessly. The canonical use cases are NOP-patching anti-debug checks, forcing branches to always-taken or never-taken, and disabling integrity verification loops in firmware. The mechanics are identical to software breakpoint injection (read-modify-write through ptrace or process_vm_writev) but the intent is permanent modification rather than temporary halting.

```c
/*
 * Force a conditional jump at `addr` to always be taken
 * by replacing the two-byte Jcc opcode with a two-byte JMP rel8.
 *
 * Most short conditional jumps are encoded as:
 *   0x74 <rel8>  (JE / JZ)
 *   0x75 <rel8>  (JNE / JNZ)
 *   0x7c <rel8>  (JL)  ... etc.
 * JMP rel8 is 0xEB <rel8>, same displacement, same size.
 */
int patch_jcc_to_jmp(pid_t pid, unsigned long addr) {
    long word = ptrace(PTRACE_PEEKDATA, pid, (void *)addr, NULL);
    if (errno != 0) { perror("peek"); return -1; }

    uint8_t *b = (uint8_t *)&word;
    uint8_t opcode = b[0];

    /* Verify this looks like a short Jcc before patching */
    if (!((opcode >= 0x70 && opcode <= 0x7F) || opcode == 0xE3)) {
        fprintf(stderr, "patch_jcc_to_jmp: unexpected opcode 0x%02x at 0x%lx\n",
                opcode, addr);
        return -1;
    }
    printf("[patch] replacing Jcc 0x%02x at 0x%lx with JMP (0xEB)\n", opcode, addr);
    b[0] = 0xEB; /* JMP rel8 */
    /* b[1] (the displacement) stays identical */
    if (ptrace(PTRACE_POKEDATA, pid, (void *)addr, (void *)word) < 0) {
        perror("poke"); return -1;
    }
    return 0;
}

/*
 * NOP out `count` bytes at `addr`. Useful for disabling integrity
 * checks, anti-debug probes, or licensing verifications.
 * Operates word by word, handling unaligned start and end.
 */
int patch_nop(pid_t pid, unsigned long addr, size_t count) {
    for (size_t i = 0; i < count; i++) {
        uint8_t discard;
        if (poke_byte(pid, addr + i, 0x90, &discard) < 0) return -1;
    }
    printf("[patch] NOP'd %zu bytes at 0x%lx\n", count, addr);
    return 0;
}
```

One hazard specific to code patching on SMP systems deserves explicit attention. If a multi-threaded target has another thread executing near the patch site, there is a window between the word-read and the word-write during which the other thread may execute the half-modified instruction. For single-byte patches (like the 0xCC software breakpoint), this is safe because x86 guarantees that single-byte writes are atomic at the cache-coherency level. For multi-byte patches, the write is not atomic and the other thread can observe a partially written opcode — typically an illegal instruction — which will fault. The safe approach is to halt all threads (via PTRACE_ATTACH on each tid in /proc/<pid>/task/) before applying multi-byte patches and resume them only after the patch is complete.

### In-Process vs. Out-of-Process Instrumentation

The architectural divide between in-process and out-of-process instrumentation is one of the most consequential design decisions in dynamic analysis tooling, and each approach carries a fundamentally different threat model.

Out-of-process instrumentation, exemplified by ptrace-based debuggers and hardware debug probes, runs the analysis engine in a separate context from the target. The kernel (or the debug hardware) mediates every interaction, which means the target's corrupted heap cannot overwrite the debugger's data structures, the target's anti-debug code cannot directly read the debugger's presence, and the target's crashes do not take the analysis engine down. The cost is the context-switch overhead described earlier — every halt, every register read, every memory peek crosses the user-kernel boundary at minimum once — and the relatively coarse granularity of observation available through the standard interfaces. The ptrace PEEKDATA interface delivers one word per syscall, and there is no built-in mechanism for conditional logging without halting.

```
Out-of-Process Model:

  ┌──────────────────┐     ptrace / JTAG      ┌──────────────────┐
  │   Debugger       │ ◄──────────────────►   │   Target Process │
  │   (separate PID) │                        │   (or bare-metal)│
  │                  │   kernel mediated       │                  │
  │  analysis logic  │                        │  code under test │
  │  cannot be       │                        │  cannot see      │
  │  corrupted by    │                        │  debugger memory │
  │  target heap     │                        │                  │
  └──────────────────┘                        └──────────────────┘

In-Process Model:

  ┌─────────────────────────────────────────────────────────────┐
  │                      Single Process                         │
  │                                                             │
  │   ┌─────────────────┐          ┌─────────────────────────┐  │
  │   │  Analysis Engine│          │  Target Code            │  │
  │   │  (DLL injection │◄────────►│  (original .text, heap) │  │
  │   │   or PIN tool)  │  shared  │                         │  │
  │   │                 │   addr   │  anti-analysis code can │  │
  │   │                 │   space  │  scan for tool presence │  │
  │   └─────────────────┘          └─────────────────────────┘  │
  └─────────────────────────────────────────────────────────────┘
```

In-process instrumentation — frameworks like Intel PIN, DynamoRIO, Frida's JavaScript runtime, or a manually injected DLL — runs analysis code within the target's own address space. This eliminates context-switch overhead entirely: a PIN analysis callback fires as a native function call within the target's execution context, with direct pointer access to all target memory. The throughput is orders of magnitude higher than ptrace single-stepping, making in-process instrumentation the practical choice for instruction-level tracing, taint tracking, or execution coverage collection over millions of instructions.

The tradeoff is exposure. The analysis engine and the target share the same memory mappings, the same heap, and the same thread scheduler. A sophisticated target that scans its own virtual address space for unexpected mappings (walking the PEB's LDR_DATA_TABLE_ENTRY list on Windows, reading /proc/self/maps on Linux) will find the instrumentation framework's loaded modules. Frida, for instance, loads a GumJS agent library and a V8-derived JavaScript engine into the target process — both appear in the module list with identifiable characteristics. DynamoRIO maintains its own private heap for the code cache, but that heap's allocation pattern is detectable if the target enumerates memory regions with VirtualQuery or /proc/self/maps. Defeating these detections requires either patching the enumeration routines themselves (a recursive problem) or operating at a layer below the target's visibility, such as a hypervisor or hardware debug unit.

Frida's stalker engine is worth examining in depth because it represents the current state of the art in transparent in-process instruction-level tracing. Rather than single-stepping, stalker translates basic blocks of the target's machine code into an internal code cache, inserting analysis callbacks between the original instructions. The translated code runs at near-native speed, with callbacks firing only at the granularity the analyst requests (block entry, instruction execution, call/return). This is functionally identical to DynamoRIO's approach and to Intel PIN's JIT compilation model. The key performance difference from ptrace is that no kernel crossing occurs during the trace — the callbacks are ordinary function calls in user space.

```javascript
// Frida stalker: trace all basic blocks in a target function,
// collecting the unique block addresses executed (coverage map).

const coverage = new Set();
const targetAddr = Module.getExportByName(null, 'verify_license');

Interceptor.attach(targetAddr, {
    onEnter: function(args) {
        const tid = Process.getCurrentThreadId();
        Stalker.follow(tid, {
            events: {
                block: true,   // fire on every basic block entry
                call:  false,
                ret:   false,
            },
            onReceive: function(events) {
                // events is an ArrayBuffer of GumEvent structures.
                // Parse block events: each is { type, begin, end }.
                const reader = Stalker.parse(events, {
                    annotate: false,
                    stringify: false
                });
                for (const ev of reader) {
                    if (ev.type === 'block') {
                        coverage.add(ev.begin.toString());
                    }
                }
            }
        });
    },
    onLeave: function(retval) {
        Stalker.unfollow(Process.getCurrentThreadId());
        console.log('[coverage] blocks visited: ' + coverage.size);
        coverage.forEach(addr => console.log('  ' + addr));
    }
});
```

Frida's `Stalker.parse` returns structured event records from the internal ring buffer that the stalker fills during execution. The coverage set built here is directly usable as input to a fuzzer's coverage map, to identify which branches inside `verify_license` were exercised on a given input, or to compare execution paths between a successful and a failing license check — a classic differential analysis workflow.

## 3. High-Performance Optimization & Failure Modes

### Scaling the Observation Rate

The limiting factor in any high-volume dynamic analysis campaign is the ratio of observation density to execution overhead. For unpacking and decryption analysis, the analyst's goal is typically to identify the moment at which a packed payload writes self-consistent executable code into a memory region and then transfers control there. Full instruction-level tracing to find that moment is wasteful. The efficient strategy is to instrument at the page granularity: mark the target heap region as non-executable with mprotect, trap the SIGSEGV when the packer writes the final byte, then switch to instruction-level tracing only for the final few hundred instructions before the jump to unpacked code.

For firmware analysis over JTAG, the equivalent optimization is trace buffer exploitation. Many ARM Cortex-M and Cortex-A cores include an Embedded Trace Macrocell (ETM) that records a compressed instruction trace in a hardware circular buffer without halting the CPU. The OpenOCD `tpiu config` and `itm` commands configure the trace output port; the resulting trace stream can be decoded offline to reconstruct the full execution history between two hardware breakpoints. This is non-halting observation — the target runs at full speed while the ETM silently captures every branch taken — and it completely eliminates the halt-latency problem for the trace collection phase. The limitation is buffer depth: on most microcontrollers the ETM trace buffer is 4–32 KB, so it captures only the most recent execution history at the moment you halt.

A concrete OpenOCD session for Cortex-M ETM trace configuration:

```
# Connect to target via SWD
target remote | openocd -f interface/cmsis-dap.cfg -f target/stm32f4x.cfg --pipe

# Configure the TPIU for SWO output on pin PA2 at 2 MHz
monitor tpiu config internal trace.bin uart off 168000000

# Enable ITM stimulus port 0 for printf-style trace output
monitor itm port 0 on

# Enable ETM instruction trace
monitor etm config cortex_m 2 normal full

# Set a hardware breakpoint at the suspected unpack completion address
monitor bp 0x20001000 2 hw

# Run; halt when the breakpoint fires; dump ETM trace buffer
monitor resume
monitor halt
monitor etm dump trace.bin
```

Offline decoding of the ETM trace binary with `trace-decoder` or the Arm DS-5 trace decoder reconstructs the full instruction sequence between the previous halt and the breakpoint, exposing the unpack loop's iteration count, the memory regions it touched, and the exact address it computed as the jump target.

### Anti-Analysis Countermeasures and Their Defeats

Timing attacks on the debug loop are the most reliable anti-analysis technique and the hardest to defeat cleanly. The canonical RDTSC-based check computes the number of cycles elapsed between two reference points; under a ptrace-based debugger, the context-switch overhead inflates the measurement by thousands of cycles, triggering the check. The clean defeat is to execute the RDTSC instruction itself inside a Frida `Interceptor.replace` hook that always returns a plausible, monotonically increasing value regardless of real elapsed time:

```javascript
// Intercept RDTSC via inline hook on the RDTSC opcode.
// Frida can't directly intercept a bare opcode, but many anti-debug
// stubs call a wrapper function. Here we hook that wrapper.

const rdtsc_wrapper = Module.findExportByName(null, 'measure_timing');
if (rdtsc_wrapper) {
    let fake_counter = 0n;
    Interceptor.replace(rdtsc_wrapper, new NativeCallback(function() {
        fake_counter += 100n;         // simulate 100 cycle increments
        return fake_counter;
    }, 'uint64', []));
    console.log('[*] RDTSC wrapper hooked at ' + rdtsc_wrapper);
}
```

When the anti-debug check is a raw RDTSC instruction rather than a wrapper call, the approach shifts to Frida's `MemoryAccessMonitor` or to a custom stalker transformer that recognizes the two-byte RDTSC encoding (0x0F 0x31) in the instruction stream and rewrites it on the fly:

```javascript
Stalker.follow(Process.getCurrentThreadId(), {
    transform: function(iterator) {
        let instruction;
        while ((instruction = iterator.next()) !== null) {
            // Detect RDTSC (0F 31) and replace with XOR RAX,RAX / NOP
            if (instruction.mnemonic === 'rdtsc') {
                // Emit a constant-time substitute: set rax=100, rdx=0
                iterator.putBytesAt(instruction.address,
                    new Uint8Array([
                        0x48, 0x31, 0xC0,  // XOR RAX, RAX
                        0x48, 0x31, 0xD2,  // XOR RDX, RDX
                        0x48, 0x83, 0xC0, 0x64  // ADD RAX, 100
                    ])
                );
            }
            iterator.keep();
        }
    }
});
```

The IsDebuggerPresent / PEB.BeingDebugged check on Windows targets is defeated by writing zero to offset 0x2 of the PEB directly:

```c
// On a Windows target attached with CreateRemoteThread injection:
// PEB is at TEB + 0x60 (x64). PEB.BeingDebugged is at PEB + 0x2.
// Use NtQueryInformationProcess to locate the PEB base first.
#include <windows.h>
#include <winternl.h>

void clear_being_debugged(HANDLE hProcess, PVOID peb_base) {
    BYTE zero = 0;
    SIZE_T written;
    // PEB.BeingDebugged is at offset 2 in the PEB structure
    WriteProcessMemory(hProcess, (LPVOID)((ULONG_PTR)peb_base + 2),
                       &zero, 1, &written);
}
```

The NtGlobalFlag check (PEB offset 0xBC on x64, non-zero under a debugger) and the heap flags check (heap header ForceFlagsOffset, process heap flags set to 0x40000060 under a debugger) are cleared with analogous one-byte writes. These PEB-patching techniques defeat the entire class of userland presence checks with minimal code, and they illustrate the broader principle: anti-analysis techniques are themselves data structures that can be patched once you understand their memory layout.

### Failure Modes in Long-Running Traces

Three failure modes recur reliably in production dynamic analysis work and each requires a specific mitigation.

The first is trace buffer saturation. Frida's stalker maintains an internal code cache and event ring buffer. Under a trace of a tight inner loop, the ring buffer fills faster than the `onReceive` callback drains it, causing events to be dropped silently. The mitigation is to call `Stalker.garbageCollect()` periodically from the `onReceive` callback and to increase the `queueCapacity` option when creating the stalker session, trading memory against loss rate.

The second failure mode is TOCTOU corruption of patched bytes. If a target binary has a background thread that periodically re-reads a checksum of its own .text section and re-patches it from a clean copy stored in .data, your software breakpoints will be overwritten on the next integrity check cycle. The analysis loop will see SIGTRAP at an address it no longer has a breakpoint record for, lose synchronization, and either crash or miss the intended halt. Detection is straightforward: set a watchpoint on the saved-byte storage location in your breakpoint table's backing array and observe whether it changes unexpectedly. The mitigation is to disable the integrity thread by NOP-patching its checksum loop before setting any software breakpoints.

The third failure mode is the page alignment trap in multi-byte patches. When you NOP-patch across a page boundary (a surprisingly common case when the instruction stream is dense and your patch range is several tens of bytes), the second page may be mapped read-only or copy-on-write. The ptrace POKEDATA to the second page will succeed silently on Linux because the kernel faults in a private copy, but the target may still be computing checksums over the original shared mapping. If the binary uses shared text segments (e.g., multiple processes sharing a mapped library with MAP_SHARED), the POKEDATA will force a COW fork of the page for the target process only, and the other processes continue executing the original bytes — which is usually the desired behavior in targeted patching but will confuse analysis if you are tracing multiple cooperating processes simultaneously. Enumerate all mappings via /proc/<pid>/maps before applying cross-page patches and verify that each target page is MAP_PRIVATE before writing.

The discipline that unifies all of these mitigations is the same discipline that makes the best reverse engineers effective: they reason from the hardware up. Every observable failure — dropped events, overwritten breakpoints, silent COW forks — is a consequence of a physical mechanism that the hardware or operating system is performing exactly as designed. When the analysis breaks, the question is never "why is the tool misbehaving?" It is always "what is the system doing that I haven't accounted for?" The answer is always in the architecture.
