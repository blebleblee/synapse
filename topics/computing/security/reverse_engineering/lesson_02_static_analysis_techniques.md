# Lesson 2: Static Analysis Techniques and Disassembly

## 1. First-Principles Intuition & Invariants

Reverse engineering, in its most fundamental form, is the art of reconstructing intent from artifact. When a compiler finishes its work and the linker closes its output file, the source code, the comments, the variable names, the architectural diagrams on some engineer's whiteboard, all of it vanishes. What remains is a sequence of bytes that a processor will interpret as instructions, data, and addresses. Static analysis is the discipline of recovering meaning from that sequence without executing a single instruction.

The philosophical foundation of static analysis rests on a deceptively simple invariant: a compiled binary is not random noise. It is the deterministic output of a translation pipeline that maps high-level semantics onto a specific instruction set architecture. Because that mapping is governed by well-documented rules, the calling conventions of a platform's ABI, the code-generation patterns of a compiler, the layout rules of an object format, a skilled analyst can reverse that translation and recover much of the original structure. The analysis is lossy — you will not recover variable names or comments — but the control flow, the data transformations, and the algorithmic logic are largely preserved and recoverable.

Understanding why static analysis is both powerful and fundamentally limited requires grounding the discussion in what a binary actually is. A compiled ELF binary on Linux, or a PE image on Windows, is a structured container. It carries multiple segments: an executable text segment containing machine instructions, read-only data segments holding string literals and jump tables, writable data segments for globals, and metadata sections describing relocations, symbol tables, and dynamic linking information. The linker resolves inter-module references and assigns virtual addresses according to the memory layout the operating system will establish at load time. Static analysis begins by parsing this container, mapping its contents into a coherent address space, and then interpreting the bytes in the executable sections as instructions.

The correctness of that interpretation depends entirely on the target ISA. An x86-64 processor decodes instructions using a variable-length encoding scheme derived from the original 8086 design and extended through decades of backward-compatible additions. Instructions range from one to fifteen bytes in length, and the starting offset of an instruction is determined dynamically as the processor decodes the preceding one. This encoding property, often called the complex instruction set, creates a fundamental ambiguity for static disassemblers: without knowing the correct entry points, an analysis tool cannot reliably determine where valid instructions begin. The ARM family, in contrast, uses a fixed 32-bit encoding in AArch64 mode, which makes linear disassembly straightforward, though the interleaving of Thumb and ARM states in 32-bit ARM code reintroduces alignment ambiguity. RISC-V uses fixed-width encoding in its base integer ISA, with the compressed extension (RVC) reintroducing 16-bit instructions that complicate naive linear sweep. Each architecture imposes its own constraints on what an analysis tool can know statically, and understanding those constraints is not academic pedantry. It directly determines the confidence an analyst can assign to any disassembly listing.

The core invariant that underpins all static analysis is called the Code-Data Separation Problem, and it is formally undecidable in the general case. Halting-problem reductions show that there is no algorithm that can correctly classify every byte in an arbitrary binary as either code or data for all possible programs. What practitioners work with instead is a set of heuristics and conservative approximations that are correct for the vast majority of real-world binaries produced by mainstream compilers, while remaining explicitly incomplete in the face of hostile obfuscation or unusual code generation strategies.

A second fundamental invariant governs what static analysis can and cannot determine about data values: at static analysis time, the values of memory and registers are unknown. An analyst can determine that a function reads four bytes from an address computed as `rbp - 0x18` and passes that value as the first argument to `malloc`, but they cannot determine what integer value that read will produce at runtime. This distinction separates static analysis from dynamic analysis and defines the boundary of what symbolic reasoning must approximate through abstraction.

---

## 2. Core Architecture & Mechanics

### 2.1 Disassembly Engines and Lifting Pipelines

Modern static analysis toolchains are built in stages. The first stage is disassembly, which converts raw machine bytes into a structured representation of individual instructions, each with an opcode, operands, and an associated address. The second stage is lifting, which translates those architecture-specific instructions into an intermediate representation (IR) that is architecture-independent and amenable to formal analysis. The third stage applies analysis passes over the IR to recover higher-level structures: functions, control flow graphs, data flow, and ultimately, decompiled pseudocode.

The two dominant open-source disassembly engines used in professional toolchains are Capstone and Zydis. Capstone is a multi-architecture disassembly library with bindings for C, Python, and most major languages, and it serves as the disassembly backend for radare2 and many custom analysis frameworks. Zydis is a pure x86/x86-64 disassembler with a focus on semantic accuracy and low latency, used in performance-sensitive contexts. Binary Ninja uses a custom LLIL/MLIL lifting pipeline. Ghidra, NSA's open-source reverse engineering platform, implements its own disassembly and lifts to its p-code IR. IDA Pro, the commercial standard, lifts to a microcode representation for its decompiler (Hex-Rays) while exposing IDC and Python APIs for scripting analysis.

The disassembly process begins with identifying entry points. For a standard ELF binary, the most reliable entry point is the address stored in the ELF header's `e_entry` field, which points to the runtime startup code (`_start`). The symbol table, if present and not stripped, provides additional function entry points. Dynamic symbol tables (`.dynsym`) survive stripping because they are required by the dynamic linker. For stripped binaries, an analyst must fall back to heuristic pattern matching: searching for function prologues, scanning the contents of `.eh_frame` sections (which encode call frame information for unwinding and reliably enumerate function starts on x86-64 Linux), and following call references from known code.

```c
/* Example: parsing ELF e_entry and section headers to seed disassembly
   Compile: gcc -O2 -o elf_seed elf_seed.c */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <elf.h>

typedef struct {
    uint64_t vaddr;
    uint64_t size;
    char     name[64];
} SeedEntry;

int collect_seeds(const char *path, SeedEntry *out, int cap) {
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror("open"); return -1; }

    struct stat st;
    fstat(fd, &st);
    uint8_t *base = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);

    if (base == MAP_FAILED) { perror("mmap"); return -1; }

    Elf64_Ehdr *ehdr = (Elf64_Ehdr *)base;
    if (memcmp(ehdr->e_ident, ELFMAG, 4) != 0) {
        fprintf(stderr, "Not an ELF binary\n");
        munmap(base, st.st_size);
        return -1;
    }

    int n = 0;

    /* Seed 1: ELF entry point */
    if (n < cap) {
        out[n].vaddr = ehdr->e_entry;
        out[n].size  = 0;
        snprintf(out[n].name, sizeof(out[n].name), "_start");
        n++;
    }

    /* Seed 2: .eh_frame_hdr gives compiler-generated function list */
    Elf64_Shdr *shdrs  = (Elf64_Shdr *)(base + ehdr->e_shoff);
    char       *strtab = (char *)(base +
                          shdrs[ehdr->e_shstrndx].sh_offset);

    for (int i = 0; i < ehdr->e_shnum && n < cap; i++) {
        const char *sname = strtab + shdrs[i].sh_name;
        if (strcmp(sname, ".dynsym") == 0) {
            Elf64_Sym *syms  = (Elf64_Sym *)(base + shdrs[i].sh_offset);
            int        nsyms = shdrs[i].sh_size / sizeof(Elf64_Sym);
            Elf64_Shdr *dsstr = &shdrs[shdrs[i].sh_link];
            char       *dyn_strtab = (char *)(base + dsstr->sh_offset);

            for (int j = 0; j < nsyms && n < cap; j++) {
                if (ELF64_ST_TYPE(syms[j].st_info) == STT_FUNC &&
                    syms[j].st_value != 0) {
                    out[n].vaddr = syms[j].st_value;
                    out[n].size  = syms[j].st_size;
                    snprintf(out[n].name, sizeof(out[n].name),
                             "%s", dyn_strtab + syms[j].st_name);
                    n++;
                }
            }
        }
    }

    munmap(base, st.st_size);
    return n;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "Usage: %s <elf>\n", argv[0]); return 1; }
    SeedEntry seeds[1024];
    int count = collect_seeds(argv[1], seeds, 1024);
    if (count < 0) return 1;
    printf("%-6s  %-18s  %-10s  %s\n", "Idx", "VAddr", "Size", "Name");
    for (int i = 0; i < count; i++)
        printf("%-6d  0x%016lx  %-10lu  %s\n",
               i, seeds[i].vaddr, seeds[i].size, seeds[i].name);
    return 0;
}
```

### 2.2 Linear Sweep vs. Recursive Descent Disassembly

Two fundamentally different algorithms govern how a disassembler traverses an executable region, and their trade-offs define the accuracy of everything that follows.

**Linear sweep** begins at the lowest address in an executable section and decodes instructions sequentially, advancing the program counter by the byte length of each decoded instruction until the section boundary is reached. Its implementation is trivial, its throughput is extremely high, and it is guaranteed to visit every byte in the region. Its fatal flaw is that it treats data embedded within code sections, padding bytes, alignment NOP sleds, and jump table entries as instructions, producing spurious decode results that corrupt the instruction stream. On x86 and x86-64, where instructions are variable width, a single misaligned start causes a cascade of incorrect decodes that can persist for dozens of instructions. Linux kernel tools like `objdump -d` use linear sweep by default, which is why analysts who rely on `objdump` for adversarial binaries routinely encounter corrupted disassembly.

**Recursive descent** treats disassembly as a reachability problem over a directed graph. It begins at a set of known entry points, decodes the instruction at each entry point, and then follows all possible successors: the fall-through address for non-branching instructions, the target of direct branches, and both successor paths for conditional branches. When a call instruction is encountered, the target address is added to a worklist of function entry points to analyze, and disassembly continues at the fall-through (since the call eventually returns, in the non-tail-call case). Code that is not reachable from any seed entry point will not be disassembled at all, which is both a strength and a limitation: data interspersed in code regions will be skipped if no branch targets them, eliminating false decode cascades, but dead code or code reachable only through indirect control flow will also be missed.

Both IDA Pro and Ghidra implement recursive descent with a battery of supplementary heuristics that run when the primary reachability analysis terminates. These heuristics scan unreached regions for function prologue patterns, analyze exception handling data, examine the contents of data sections for pointers into code, and apply machine-learning classifiers trained on compiler output. Neither tool will ever achieve 100% coverage on a hostile binary, but on typical stripped release binaries produced by GCC or LLVM with standard optimization settings, the coverage is high enough to reconstruct the full call graph.

### 2.3 Control Flow Graph Construction

The control flow graph (CFG) is the central data structure of static analysis. A CFG for a single function is a directed graph in which each node is a **basic block**, defined as a maximal sequence of instructions with exactly one entry point and exactly one exit point. No instruction within a basic block other than the last one can be a branch target, and no instruction within a basic block other than the last one can be a branch. This definition guarantees that if execution enters a basic block at its first instruction, it will execute every instruction in the block in order, with no possibility of jumping into the middle or leaving before the end.

The CFG edges encode the successor relationship between basic blocks. A direct unconditional jump from block A to block B creates a single edge A → B. A conditional branch from block A creates two edges: one to the taken target and one to the fall-through. A call instruction nominally creates an edge to the callee, though at the intra-procedural CFG level it is typically modeled as a single block that falls through to the return address. A return instruction creates edges to all call sites that could have invoked the function, which requires an inter-procedural call graph to resolve.

The following diagram illustrates the CFG of a simple conditional function:

```
  FUNCTION: check_bounds(int x)
  ┌─────────────────────────────────┐
  │  ENTRY BLOCK                    │
  │  push rbp                       │
  │  mov  rbp, rsp                  │
  │  mov  DWORD PTR [rbp-4], edi    │
  │  cmp  DWORD PTR [rbp-4], 0      │
  │  jl   .LBB_NEG                  │
  └────────────┬────────────────────┘
               │ (fall-through: x >= 0)
               ▼
  ┌────────────────────────────┐
  │  BLOCK_POS                 │
  │  cmp  DWORD PTR [rbp-4],100│
  │  jg   .LBB_OOB             │
  └──────┬─────────────────────┘
         │ (fall-through: 0 <= x <= 100)
         ▼
  ┌──────────────┐    ┌────────────────┐    ┌──────────────┐
  │  BLOCK_OK    │    │  BLOCK_NEG     │    │  BLOCK_OOB   │
  │  mov eax, 1  │    │  mov eax, 0    │    │  mov eax, 0  │
  │  jmp .exit   │    │  jmp .exit     │    │  jmp .exit   │
  └──────┬───────┘    └───────┬────────┘    └──────┬───────┘
         │                    │                     │
         └──────────┬─────────┘─────────────────────┘
                    ▼
           ┌─────────────────┐
           │  EXIT BLOCK     │
           │  pop rbp        │
           │  ret            │
           └─────────────────┘
```

Building a CFG in practice requires identifying all basic block boundaries. A boundary begins at the first instruction of the function, at every branch target, and at every fall-through address following a branch. It ends at every branch instruction, every call instruction that is treated as a terminator (such as `noreturn` calls to `abort` or `__stack_chk_fail`), and every return instruction. Modern tools like Binary Ninja and IDA Pro compute CFGs incrementally during disassembly, using the recursive descent algorithm to simultaneously drive code discovery and block splitting.

### 2.4 Practical Disassembly with Ghidra and Radare2

Working through a concrete example grounds the theoretical framework in the tools an analyst actually reaches for. Consider a stripped x86-64 ELF binary suspected of containing a custom encryption routine.

In Ghidra, the analysis pipeline runs automatically after import. The disassembler seeds from the ELF entry point, the dynamic symbol table, and `.eh_frame` data. Ghidra's auto-analysis then applies its `AggressiveInstructionFinder` and `FunctionStartSearch` analyzers to recover functions unreachable from explicit exports. After analysis completes, the **Symbol Tree** pane shows all identified functions, initially named by their address (e.g., `FUN_00401a20`). The Listing view presents the disassembly with cross-references, and the Function Graph view renders the CFG for any selected function. The Decompiler window, powered by Ghidra's p-code IR and type propagation engine, produces C-like pseudocode from the CFG.

For scripted or headless analysis, Ghidra exposes the full analysis pipeline through its `analyzeHeadless` command-line tool and its Java/Python (Jython) scripting API:

```python
# Ghidra Python script: enumerate all functions and their block counts
# Run via: Window > Script Manager > Run Script
# Compatible with Ghidra 10.x (Jython 2.7 environment)

from ghidra.program.model.block import BasicBlockModel
from ghidra.util.task import ConsoleTaskMonitor

monitor   = ConsoleTaskMonitor()
bbmodel   = BasicBlockModel(currentProgram)
fm        = currentProgram.getFunctionManager()

print("{:<12}  {:>8}  {:>8}  {}".format(
    "Entry", "Blocks", "Size", "Name"))

for func in fm.getFunctionsNoStubs(True):
    entry  = func.getEntryPoint()
    size   = func.getBody().getNumAddresses()
    nblocks = 0
    it = bbmodel.getCodeBlocksContaining(func.getBody(), monitor)
    while it.hasNext():
        it.next()
        nblocks += 1
    print("{:<12}  {:>8}  {:>8}  {}".format(
        str(entry), nblocks, size, func.getName()))
```

Radare2 offers an entirely command-line-driven workflow that integrates well into automated pipelines. After opening a binary with `r2 -A ./target`, which triggers recursive analysis (`aaa`), the analyst has access to the full analysis graph through a consistent command namespace. Function listing, CFG visualization in ASCII art, cross-reference queries, and binary patching all operate through the same interface.

```bash
# Full radare2 static analysis workflow for a stripped ELF
# Step 1: Open and auto-analyze (recursive descent + heuristics)
r2 -A ./target_binary

# Step 2: List all identified functions sorted by size
afl~[0,2,3] | sort -k3 -n -r | head -20

# Step 3: Seek to the largest function and print its disassembly
s `afl~[0,2,3] | sort -k3 -n -r | head -1 | awk '{print $1}'`
pdf

# Step 4: Print the CFG of the current function in ASCII art
agf

# Step 5: Export the full call graph in DOT format for Graphviz
agCd > callgraph.dot
dot -Tsvg callgraph.dot -o callgraph.svg

# Step 6: Find all cross-references to a specific virtual address
axt 0x00401a20

# Step 7: Search for a known byte pattern (e.g., AES S-box first row)
/x 637c777b

# Step 8: Dump the disassembly of the 10 instructions at a hit address
pd 10 @ hit0_0

# Step 9: Extract all strings and filter by minimum length 8
iz~[0,2] | awk 'length($2) >= 8'

# Step 10: Identify function prologues missed by auto-analysis (heuristic sweep)
/aF
afl | wc -l
```

### 2.5 Data Flow Analysis and Use-Def Chains

Control flow analysis tells you where execution can go. Data flow analysis tells you what values travel between those locations. For reverse engineers, data flow is often more informative: it reveals how an input buffer is transformed into an output ciphertext, how a user-controlled value propagates into a memory allocation size, or how a network-received integer reaches a vulnerable `memcpy` call site.

The formal foundation of data flow analysis is the **use-definition chain** (UD chain). A definition of a variable `v` at program point `p` is any instruction at `p` that writes to `v`. A use of `v` at program point `q` is any instruction at `q` that reads `v`. A UD chain connects each use of a variable to all definitions that may have produced its value at that use point. Computing UD chains over a CFG requires solving a system of dataflow equations using iterative fixed-point analysis, propagating reaching-definition sets through the basic blocks of the CFG until no set changes between iterations.

Modern analysis tools implement data flow on their intermediate representations rather than directly on machine instructions. Ghidra's p-code IR uses Static Single Assignment (SSA) form, which makes UD chains trivially explicit: every variable in SSA has exactly one definition, and the SSA `phi` nodes at CFG join points enumerate all reaching definitions. Binary Ninja's MLIL (Medium-Level IL) similarly constructs SSA and exposes it through its API. The decompiler then leverages SSA to perform copy propagation, dead code elimination, and type inference, transforming the raw instruction sequence into comprehensible pseudocode.

For manual taint tracking, radare2's ESIL (Evaluable Strings Intermediate Language) allows symbolic emulation of individual instructions:

```bash
# Enable ESIL VM and trace data flow through 50 instructions from a function entry
aei         # initialize ESIL VM
aeim        # initialize memory map for emulation
aeip        # set instruction pointer to current seek address

# Emulate 50 instructions and print register states after each
aes 50
aer         # dump all register values after emulation

# Trace how rdi (first argument) propagates through the function
# Set a watchpoint on rdi and step until it changes
ar rdi=0xdeadbeef    # seed rdi with a recognizable sentinel
aes 100
aer rdi              # observe where the sentinel ended up
```

### 2.6 Graph-Based Code Representations Beyond the CFG

The CFG captures intra-procedural control flow, but it is insufficient for whole-program reasoning. Three graph representations extend the analysis scope.

The **call graph** (CG) is a directed graph where each node is a function and each edge represents a possible call from caller to callee. For direct calls (`call 0x401a20`), edges are precise. For indirect calls (`call rax`), the target is unknown until points-to analysis or dynamic profiling resolves the value of `rax`. Building a precise call graph for a production binary is one of the core hard problems in static analysis. Practical tools use a conservative approximation: they include all addresses that have been identified as function entry points as potential targets of any indirect call, producing an over-approximation that is sound (no real edges missing) but imprecise (many spurious edges present).

The **Program Dependence Graph** (PDG) superimposes control dependence and data dependence edges over the CFG. A node `B` is control-dependent on node `A` if the branch decision at `A` determines whether `B` executes. A node `B` is data-dependent on node `A` if `A` produces a value that `B` consumes. The PDG is the substrate for program slicing: given a slicing criterion (a specific variable at a specific program point), the backward slice is the subgraph of all PDG nodes that may have influenced that variable's value. For a vulnerability analyst, slicing a suspicious `memcpy` size argument backward through the PDG reveals the full chain of computations that produced it, which is precisely the information needed to reason about exploitability.

The **Inter-procedural Control Flow Graph** (ICFG) connects function-level CFGs through call and return edges, enabling analysis that follows execution across function boundaries. The ICFG is expensive to compute and even more expensive to analyze, because path explosion across call sites grows exponentially with call depth. Practical tools approximate it through **summaries**: a function summary captures the effect of a function on its inputs and outputs without inlining the full function body at every call site, enabling efficient inter-procedural analysis at scale.

```
INTER-PROCEDURAL DATA FLOW (ICFG PARTIAL VIEW)

main()                      decrypt()                   memcpy()
  ┌──────────┐    call         ┌──────────────┐  call    ┌───────────┐
  │ read_buf │ ──────────────► │ load_key     │          │  dst      │
  │ (input)  │                 │ xor_round×16 │ ────────►│  src      │
  └────┬─────┘                 │ write_output │          │  len ◄─── vulnerable if
       │                       └──────┬───────┘          │          len = f(input)
       │ (buf_len = attacker)         │ return            └───────────┘
       └────────────────────────────► len propagates
```

---

## 3. High-Performance Optimization & Failure Modes

### 3.1 Scaling Static Analysis to Large Binaries

A naive full-program static analysis over a large binary, say a 20 MB stripped firmware image or a 50 MB Windows PE, can consume hours of analysis time and gigabytes of memory when tool defaults are applied without discipline. The performance bottlenecks are well-understood, and practitioners apply several strategies to manage them.

The most effective optimization is **demand-driven analysis**: rather than computing data flow information for the entire program upfront, the analyst specifies a set of target functions or program points of interest and runs analysis only for the backward slice reaching those targets. Binary Ninja's API supports this pattern directly, allowing a script to identify all call sites to `malloc`, `memcpy`, or `recv`, and then perform backward taint analysis from those call sites without analyzing the entire binary first.

```python
# Binary Ninja Python API: find all calls to memcpy and trace their size argument
# Run via Binary Ninja's script console or as a headless plugin
# Requires: pip install binaryninja (with valid license)

import binaryninja as bn

def find_memcpy_size_sources(bv_path: str):
    bv = bn.load(bv_path)
    if bv is None:
        raise RuntimeError(f"Failed to load binary: {bv_path}")

    # Locate the memcpy symbol (handles PLT stubs in ELF)
    memcpy_syms = bv.get_symbols_by_name("memcpy")
    if not memcpy_syms:
        # Try the PLT entry name used by some linkers
        memcpy_syms = bv.get_symbols_by_name("memcpy@plt")
    if not memcpy_syms:
        print("memcpy not found in symbol table; aborting")
        return

    memcpy_addr = memcpy_syms[0].address
    print(f"memcpy resolved at 0x{memcpy_addr:x}\n")

    # Iterate all call sites referencing memcpy
    for ref in bv.get_code_refs(memcpy_addr):
        caller_func = bv.get_functions_containing(ref.address)
        if not caller_func:
            continue
        func = caller_func[0]

        # Get the HLIL (High-Level IL) instruction at the call site
        hlil_func = func.hlil
        for block in hlil_func:
            for instr in block:
                # Match call instructions targeting memcpy
                if (instr.operation == bn.HighLevelILOperation.HLIL_CALL and
                        instr.dest.operation == bn.HighLevelILOperation.HLIL_CONST and
                        instr.dest.constant == memcpy_addr):

                    # Argument order: memcpy(dst, src, size) -> index 2
                    if len(instr.params) >= 3:
                        size_arg = instr.params[2]
                        print(f"  Call site:  0x{instr.address:x} in {func.name}")
                        print(f"  Size arg:   {size_arg} (op={size_arg.operation.name})")

                        # Follow SSA defs backward if the size is a variable
                        if hasattr(size_arg, 'var'):
                            ssa_var = size_arg.ssa_form
                            print(f"  SSA var:    {ssa_var}")
                        print()

find_memcpy_size_sources("/path/to/target.elf")
```

For firmware images that contain multiple concatenated binaries, file systems, or compressed regions, pre-processing with **binwalk** to extract and identify sub-regions before applying analysis tools to individual components dramatically reduces both false positives and analysis time. Each extracted ELF or PE binary can then be analyzed independently with its own seed entry points.

```bash
# Firmware extraction and component isolation workflow
binwalk -e -M --dd='.*' firmware.bin     # recursive extraction with all signatures
ls _firmware.bin.extracted/              # examine extracted components

# Identify ELF files within extracted components
find _firmware.bin.extracted/ -type f | xargs file | grep ELF

# For each identified ELF, generate a function list with radare2 in batch mode
for elf in $(find _firmware.bin.extracted/ -type f | xargs file | grep ELF | cut -d: -f1); do
    echo "=== $elf ==="
    r2 -q -e anal.timeout=120 -c 'aaa; afl' "$elf" 2>/dev/null | tail -n +3
done
```

### 3.2 Defeating Obfuscation: Indirect Jumps and Dynamic Code

The deepest failures of static analysis arise not from tool limitations but from deliberate adversarial construction. Obfuscators and packers exploit the precise boundaries of what static analysis can resolve, and an analyst who does not understand those boundaries will confidently report incorrect disassembly.

**Indirect control flow** is the most common and most damaging obstruction. When a compiler generates a switch statement over a dense range of values, it typically produces a jump table: a contiguous array of target addresses in the read-only data section, with a single indirect jump instruction that indexes into the table using the switch variable. A static analyzer can resolve this if it recognizes the idiom and can verify that the pointer calculation produces addresses within the table's bounds. But a custom obfuscator can defeat this analysis by computing jump targets through arithmetic transforms, XOR encoding, or hash table lookups that have no obvious structure. When the analysis cannot determine the set of possible targets for `jmp rax`, it must either insert a conservative edge to every function entry point (massively overapproximating) or leave the edge unresolved (underapproximating and missing reachable code entirely).

**Self-modifying code** breaks the static analysis invariant that the bytes in the text segment are the instructions that will execute. A packer overwrites its own code with the decrypted payload during the unpack stub's execution, replacing the bytes the disassembler saw with entirely different instructions. No static analysis of the packed binary reflects the actual executed code. The correct response is hybrid analysis: use static analysis to identify the unpack stub's structure and the write-then-execute pattern, then trigger the unpack under a debugger or emulator (QEMU, Unicorn, or Frida's inline hooks) and dump the decrypted image for static analysis of the actual payload.

**Opaque predicates** are branch conditions whose value is statically constant (always taken or never taken) but whose computation is sufficiently complex that static analysis cannot determine the constant. The obfuscator inserts dead branches pointing to corrupted or misleading code, and static disassemblers that follow both sides of the conditional produce nonsense disassembly for the dead branch. Detecting opaque predicates requires either symbolic execution with a constraint solver (Z3-based tools like angr can resolve many common opaque predicate patterns) or statistical recognition based on the fact that the dead branch code is typically never modified by cross-references and contains suspicious instruction patterns.

The angr binary analysis framework provides a Python-accessible symbolic execution engine that can resolve many indirect control flow targets that pure disassemblers cannot:

```python
# angr: resolve indirect call targets in a function via symbolic execution
# Install: pip install angr
# Usage: python3 resolve_indirect.py ./target_binary 0x401a20

import sys
import angr
import claripy

def resolve_indirect_targets(binary_path: str, func_addr: int):
    proj = angr.Project(binary_path,
                        auto_load_libs=False,
                        load_options={"rebase_granularity": 0x1000})

    # Build a CFG using CFGFast for initial function identification
    cfg = proj.analyses.CFGFast(normalize=True,
                                 resolve_indirect_jumps=True,
                                 collect_data_references=True)

    target_func = cfg.kb.functions.get(func_addr)
    if target_func is None:
        print(f"Function at 0x{func_addr:x} not found in CFG")
        return

    print(f"Function: {target_func.name} at 0x{func_addr:x}")
    print(f"Basic blocks: {len(list(target_func.blocks))}")

    # Identify indirect jumps within this function
    indirect_jumps = []
    for block in target_func.blocks:
        cap_block = proj.factory.block(block.addr)
        for insn in cap_block.capstone.insns:
            # jmp with register operand indicates indirect jump
            if insn.mnemonic == 'jmp' and insn.op_str.startswith('r'):
                indirect_jumps.append(insn.address)
                print(f"  Indirect jump at 0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

    # Use CFGEmulated (symbolic) to attempt resolution of indirect jumps
    if indirect_jumps:
        print("\nRunning CFGEmulated for symbolic resolution (may take time)...")
        cfg_emu = proj.analyses.CFGEmulated(
            starts=[func_addr],
            context_sensitivity_level=2,
            call_depth=3,
            normalize=True)

        for jmp_addr in indirect_jumps:
            node = cfg_emu.get_any_node(jmp_addr)
            if node and cfg_emu.graph.successors(node):
                succs = list(cfg_emu.graph.successors(node))
                print(f"  0x{jmp_addr:x} resolved to: "
                      f"{[hex(s.addr) for s in succs]}")
            else:
                print(f"  0x{jmp_addr:x} could not be resolved symbolically")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <binary> <func_addr_hex>")
        sys.exit(1)
    resolve_indirect_targets(sys.argv[1], int(sys.argv[2], 16))
```

### 3.3 ISA-Specific Failure Modes

ARM Cortex-M binaries present a failure mode specific to the Thumb ISA interleaving common in embedded firmware. Function pointers in Thumb mode are stored with the least significant bit set to 1, indicating Thumb state rather than ARM state. If a disassembler does not mask this bit before treating a stored value as a code address, it will attempt to disassemble at an odd address and produce incorrect results. The `objdump -marm --disassemble-all` invocation correctly handles this, but custom parsers that extract addresses from `.data` sections and attempt to disassemble them must explicitly clear the LSB.

RISC-V binaries with the C (compressed) extension pose a similar challenge. The compressed extension allows 16-bit instruction encodings to coexist with the standard 32-bit encoding in the same instruction stream. A disassembler that is unaware of the C extension will decode the high 16 bits of a 32-bit instruction as a compressed instruction and misalign all subsequent decodes. The ELF header's flags field (`EF_RISCV_RVC` in `e_flags`) indicates whether the binary uses the compressed extension, and a correct disassembler checks this flag before selecting the decoding mode.

MIPS delay slots create another category of failure. In the MIPS architecture, the instruction immediately following a branch or jump (the **delay slot**) always executes before the branch takes effect. A disassembler that models MIPS as branch-then-execute rather than execute-delay-slot-then-branch will produce incorrect CFG edges, misattribute the delay slot instruction to the wrong basic block, and generate incorrect pseudocode in which the delay slot operation appears to execute conditionally when it in fact executes unconditionally.

### 3.4 Identifying Cryptographic Primitives Through Pattern Recognition

One of the highest-value applications of static analysis in offensive security research is the identification of cryptographic primitives from their characteristic constant patterns. AES round keys, the SHA-256 initialization constants, the RC4 KSA loop, the DES S-boxes, and the ChaCha20 quarter-round structure all produce recognizable signatures in disassembled code that survive even significant obfuscation, because the mathematical constants themselves cannot be transformed without breaking the algorithm.

The findcrypt plugin for IDA Pro, and its equivalent `aes` and `crypto` commands in radare2, scan the binary for known cryptographic constants. The `yara` tool allows writing custom rules that match these byte sequences across both the data sections and inline constants embedded in immediate operands:

```bash
# YARA rule to detect AES key expansion constants in a binary
cat > aes_detect.yar << 'EOF'
rule AES_SBox_Constants {
    meta:
        description = "Detects AES S-Box forward lookup table"
        author      = "re_analyst"
    strings:
        // First 16 bytes of the AES forward S-box
        $sbox_start = { 63 7c 77 7b f2 6b 6f c5 30 01 67 2b fe d7 ab 76 }
        // AES Rcon table first 4 entries
        $rcon       = { 01 00 00 00 02 00 00 00 04 00 00 00 08 00 00 00 }
    condition:
        any of them
}

rule ChaCha20_Constants {
    meta:
        description = "Detects ChaCha20 'expand 32-byte k' constant"
    strings:
        // ASCII "expand 32-byte k" as little-endian 32-bit words
        $sigma = { 65 78 70 61 6e 64 20 33 32 2d 62 79 74 65 20 6b }
    condition:
        $sigma
}
EOF

yara -r aes_detect.yar /path/to/firmware_extract/

# radare2 crypto search
r2 -q -c '/c aes' firmware.bin   # search for AES-related constants
r2 -q -c 'iz~sha' firmware.bin   # search string references to SHA variants
```

When a cryptographic constant search returns a hit, the analyst notes the address of the constant, then uses cross-references to find which code accesses it. In Ghidra, right-clicking a data address and selecting **References → Show References to Address** produces the complete list of code locations that read the constant. Each such location is a likely entry into the cryptographic primitive's implementation, providing a precise starting point for CFG analysis and decompilation of the full algorithm.

The discipline of static analysis ultimately culminates in this kind of targeted investigation: not the heroic attempt to understand every instruction in a 50 MB binary, but the systematic application of seeding strategies, graph analysis, pattern recognition, and demand-driven data flow tracing to answer specific, well-formed questions about a target binary's behavior. The practitioner who internalizes the invariants of ISA encoding, the mechanics of CFG construction, the limits of indirect call resolution, and the characteristic signatures of common algorithms is equipped to extract high-confidence answers from binaries that yield nothing to casual inspection.
