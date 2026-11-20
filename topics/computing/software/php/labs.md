# Operational Verification Labs: PHP

## Objective & Toolchain Setup

PHP remains one of the most widely deployed server-side scripting languages, powering a substantial fraction of web infrastructure. While often dismissed as a "glue language," production PHP deployments exhibit the same operational demands as any systems software: memory efficiency, cache locality, concurrency correctness, and predictable performance under load. This laboratory guide treats PHP as a first-class systems programming target, instrumenting the Zend Engine runtime with profilers, sanitizers, and low-level diagnostics to expose optimization opportunities, memory corruption vulnerabilities, and concurrency defects that manifest only under stress.

Modern PHP development operates across two distinct runtime contexts. The traditional Apache `mod_php` or PHP-FPM process model uses shared-nothing request isolation, where each request executes in an independent memory space, trades memory safety for operational simplicity, and relies on the operating system's process scheduler for concurrency. The newer asynchronous runtimes like Swoole, ReactPHP, and RoadRunner introduce shared-memory persistent state, cooperative multitasking, and long-lived event loops, exposing developers to data races, use-after-free conditions, and subtle memory leaks that accumulate over millions of requests. These labs instrument both execution models, teaching engineers to profile CPU cache behavior, detect memory corruption with AddressSanitizer-equivalent tooling, stress-test concurrent workloads, and interpret disassembled opcode sequences to understand runtime bottlenecks.

The primary diagnostic toolchain for PHP operational verification consists of Xdebug for execution tracing and profiling output in Cachegrind format, Valgrind for memory leak detection and cache simulation, `perf` for Linux hardware performance counter sampling, `gdb` for live process introspection and core dump analysis, and OPcache for bytecode emission and JIT compilation diagnostics. For asynchronous runtimes, we layer in ThreadSanitizer instrumentation via custom PHP extensions, Swoole's coroutine tracing facilities, and `strace` system call analysis to observe I/O patterns and blocking behavior. Every exercise in this guide produces quantitative diagnostic output—cache miss rates, allocation graphs, race condition reports, opcode execution histograms—that directly informs architectural decisions and optimization strategies.

Begin by establishing a complete diagnostic environment. Install PHP 8.3 or later from source to enable debug symbols and sanitizer instrumentation. The distribution package managers often strip symbols and disable assertions, rendering low-level analysis impossible. Download the PHP source tarball from php.net, extract it, and configure the build with full debugging support and thread sanitizer hooks. The configuration invocation requires explicit flags for debug symbols, AddressSanitizer integration via LLVM instrumentation, and Valgrind-friendly memory allocation patterns. Execute the following sequence in a clean build directory, ensuring that all dependencies including libxml2, libssl, and libcurl development headers are present.

```bash
wget https://www.php.net/distributions/php-8.3.14.tar.xz
tar -xf php-8.3.14.tar.xz
cd php-8.3.14
./configure \
  --enable-debug \
  --enable-maintainer-zts \
  --with-valgrind \
  --enable-opcache \
  --enable-opcache-jit \
  --with-pear \
  CFLAGS="-O0 -g3 -fsanitize=address -fno-omit-frame-pointer" \
  LDFLAGS="-fsanitize=address"
make -j$(nproc)
sudo make install
```

This build configuration disables compiler optimizations with `-O0` to preserve exact source-to-machine correspondence in debugger sessions, includes full DWARF-3 debug metadata via `-g3`, and instruments every memory allocation and access with AddressSanitizer boundary checks. The `--enable-maintainer-zts` flag activates Zend Thread Safety, a prerequisite for running PHP in multi-threaded environments like Apache's worker MPM or Swoole's coroutine scheduler. The Valgrind integration flag inserts metadata annotations that allow Valgrind's Memcheck tool to distinguish between intentional uninitialized reads in the Zend allocator and genuine bugs. After installation, verify that the debug build produces meaningful stack traces and sanitizer reports by deliberately triggering a heap buffer overflow.

Construct a minimal PHP script that writes beyond an allocated array boundary, then execute it under the instrumented runtime. The AddressSanitizer runtime will intercept the out-of-bounds write, print a detailed report including the allocation stack trace, the violation address, and surrounding memory shadow bytes, then terminate the process. This immediate feedback loop is the foundation of all subsequent verification exercises.

```php
<?php
// verify_asan.php
$buffer = array_fill(0, 10, 0);
for ($i = 0; $i <= 10; $i++) {
    $buffer[$i] = $i * 2;  // Off-by-one: writes at index 10
}
echo "Completed\n";
```

Run this script with the instrumented PHP binary and observe the sanitizer report. The output will include the exact source line, the allocation backtrace showing the `array_fill` internal allocation path, and the violation type indicating a heap buffer overflow. This establishes that the toolchain correctly instruments PHP's internal memory management layer, not just C extensions, and that sanitizer diagnostics will surface even subtle memory safety violations that occur within the Zend Engine's hashtable or zval reference counting logic.

```bash
./sapi/cli/php verify_asan.php
```

Next, install Xdebug 3.x for execution profiling and opcode tracing. Xdebug operates as a Zend extension, hooking into the engine's opcode execution pipeline to emit profiling data in Cachegrind-compatible format. Compile Xdebug from source against the debug-enabled PHP installation, ensuring version compatibility by checking the Xdebug release matrix. The build process uses `phpize` to generate a configure script that inherits the PHP API version and threading model, then compiles a position-independent shared object that loads at runtime.

```bash
git clone https://github.com/xdebug/xdebug.git
cd xdebug
phpize
./configure --enable-xdebug
make -j$(nproc)
sudo make install
```

After installation, enable Xdebug in the PHP configuration by adding its extension directive to `php.ini`. Configure profiler output to write Cachegrind files to a dedicated directory with unique filenames incorporating the process ID and request timestamp. Enable function trace output and opcode-level step debugging for granular execution analysis. The configuration fragment below activates all diagnostic modes without triggering profiling on every request, reserving activation for explicit environment variable triggers.

```ini
zend_extension=xdebug.so
xdebug.mode=develop,debug,profile,trace
xdebug.start_with_request=trigger
xdebug.output_dir=/var/tmp/xdebug
xdebug.profiler_output_name=cachegrind.out.%p.%r
xdebug.trace_output_name=trace.%p.%r
xdebug.collect_assignments=1
xdebug.collect_return=1
```

Verify Xdebug integration by running a trivial script with profiling enabled. Set the `XDEBUG_TRIGGER` environment variable to activate the profiler, execute a function with measurable work, then inspect the resulting Cachegrind file with KCachegrind or a text viewer. The profile will show function call counts, inclusive and self-time measurements, and a call graph exposing the execution hierarchy. This confirms that the profiling infrastructure correctly attributes execution time to user-defined functions, internal engine operations, and C extension calls.

```bash
XDEBUG_TRIGGER=1 php -r 'for ($i=0; $i<1000000; $i++) { strlen("test"); }'
ls -lh /var/tmp/xdebug/
```

Complete the toolchain installation with Valgrind for memory leak detection and cache simulation. Install Valgrind 3.23 or later from your distribution's package manager or compile from source if custom suppression rules are needed. Valgrind's Memcheck tool intercepts every memory allocation and access at the instruction level, maintaining shadow metadata that tracks initialization state and ownership. Running PHP under Valgrind incurs a 10–30× slowdown, making it suitable for leak detection in test suites but impractical for production profiling. The Cachegrind and Callgrind tools simulate L1/L2 cache behavior and branch prediction, generating cache miss statistics that inform data structure layout and access pattern optimizations.

With the complete toolchain assembled—AddressSanitizer-instrumented PHP runtime, Xdebug profiler, Valgrind memory checker, and `perf` hardware counter integration—engineers gain observability into every layer of PHP execution: from source syntax to opcode bytecode, from bytecode to machine instructions, and from memory allocations to cache line evictions. The following exercises operationalize this toolchain against realistic workloads, teaching systematic verification workflows that surface bugs, bottlenecks, and optimization opportunities invisible to naive testing.

## Exercise 1: AST, IR & Disassembly Analysis

PHP's execution model transforms source code through multiple intermediate representations before reaching machine instructions. Understanding this compilation pipeline is essential for performance optimization and debugging, as bottlenecks often manifest in unexpected places—an innocent-looking array access may trigger hashtable resizing, a string concatenation may invoke copy-on-write logic, or a function call may traverse a multi-level scope chain. This exercise instruments each stage of the transformation: from lexical tokens to abstract syntax tree (AST) nodes, from AST to Zend opcode bytecode, from opcodes to JIT-compiled machine code, and finally to disassembled x86-64 instructions. By observing how high-level constructs map to low-level operations, engineers develop intuition for which language features incur hidden costs and which optimizations the JIT compiler successfully applies.

The PHP lexer and parser construct an abstract syntax tree representation that preserves syntactic structure without semantic analysis. The AST phase performs type inference, constant folding, and early error detection before lowering to opcodes. Each AST node carries metadata including source line numbers, variable scopes, and compile-time constant expressions. The Zend compiler then translates AST nodes into a linear sequence of opcodes—a stack-based bytecode instruction set that operates on zvals (Zend values), the universal representation for PHP variables. Opcodes include arithmetic operations, control flow instructions, function calls, array accesses, and object property lookups. The opcode sequence is stored in OPcache's shared memory segment, where it persists across requests, eliminating repeated parsing and compilation overhead.

For hot code paths identified by the JIT compiler, opcodes are further translated into machine code via LLVM's optimization pipeline. PHP 8's JIT operates in two modes: function JIT compiles entire functions when their call count exceeds a threshold, while tracing JIT compiles hot loops by recording opcode execution traces and specializing them based on observed types. The JIT output is position-independent x86-64 or ARM64 code that directly manipulates CPU registers, bypassing the opcode interpreter's dispatch overhead. However, JIT compilation introduces subtle semantic differences—type specialization may assume invariants that dynamic execution violates, guard conditions may deoptimize back to interpreted mode, and register allocation may expose cache line conflicts invisible in the interpreter.

Begin by examining the AST for a simple function definition. PHP provides `php -r 'opcache_compile_file("script.php"); opcache_get_status(true);'` to trigger compilation, but accessing the AST directly requires using the `ast` PECL extension developed by Nikita Popov. Install the extension via PECL, then write a script that pretty-prints AST nodes with indentation showing tree structure. The AST for a function definition includes a `AST_FUNC_DECL` root node, a `AST_PARAM_LIST` for parameters, a `AST_STMT_LIST` for the body, and leaf nodes for variable fetches, constants, and operators.

```bash
pecl install ast
```

Create a PHP script that defines a function performing scalar arithmetic, array construction, and a conditional branch. Use the `ast\parse_code` function to obtain the AST, then recursively traverse it, printing node types, attributes, and child relationships. The output reveals that seemingly atomic operations like `$a + $b` decompose into multiple AST nodes representing variable fetch operations and a binary arithmetic node.

```php
<?php
// ast_analysis.php
require 'vendor/autoload.php';

function compute_discount(float $price, int $quantity): float {
    $subtotal = $price * $quantity;
    $discount_rate = ($quantity >= 10) ? 0.15 : 0.05;
    return $subtotal * (1.0 - $discount_rate);
}

$ast = ast\parse_code('<?php ' . file_get_contents(__FILE__), 70);

function print_ast($node, $indent = 0) {
    if (!($node instanceof ast\Node)) {
        echo str_repeat('  ', $indent) . "Literal: " . var_export($node, true) . "\n";
        return;
    }
    
    echo str_repeat('  ', $indent) . ast\get_kind_name($node->kind);
    if (isset($node->flags)) {
        echo " [flags=" . $node->flags . "]";
    }
    echo "\n";
    
    foreach ($node->children as $key => $child) {
        echo str_repeat('  ', $indent + 1) . "[$key]:\n";
        print_ast($child, $indent + 2);
    }
}

print_ast($ast);
```

Execute this script and observe the hierarchical output. The `AST_FUNC_DECL` node for `compute_discount` contains a `AST_PARAM_LIST` with three `AST_PARAM` children, each carrying type declarations encoded in the `flags` attribute. The function body's `AST_STMT_LIST` shows a sequence of assignments, conditional expressions, and return statements. The conditional `($quantity >= 10) ? 0.15 : 0.05` appears as a `AST_CONDITIONAL` node with three children: the condition, the true branch, and the false branch. This structure exposes opportunities for constant folding—if `$quantity` were a compile-time constant, the entire conditional could collapse to a single literal.

Next, lower the AST to opcode bytecode using Xdebug's function trace or the VLD (Vulcan Logic Dumper) extension. VLD intercepts opcode execution and prints a human-readable disassembly showing opcode names, operands, and jump targets. Install VLD via PECL, enable it in `php.ini`, and configure it to emit opcode listings without executing the script. The output format resembles assembly language, with line numbers, opcode mnemonics, and operand descriptions.

```bash
pecl install vld-beta
```

Configure VLD to dump opcodes without execution by setting `vld.active=1` and `vld.execute=0` in `php.ini`, then run the `compute_discount` function through the disassembler. The opcode sequence will include `MUL` for floating-point multiplication, `IS_SMALLER` for the comparison, `JMPZ` for conditional branching, and `RETURN` for the function epilogue. Observe that register allocation is implicit—opcodes reference temporary variables (`$T0`, `$T1`) that the VM allocates on the executor stack.

```php
<?php
// opcode_dump.php
function compute_discount(float $price, int $quantity): float {
    $subtotal = $price * $quantity;
    $discount_rate = ($quantity >= 10) ? 0.15 : 0.05;
    return $subtotal * (1.0 - $discount_rate);
}

// VLD will dump opcodes when this file is loaded
```

Run the script with VLD active and examine the opcode listing. Each line shows the opcode offset, the instruction name, and its operands. The `INIT_FCALL` opcode prepares the call frame, `SEND_VAR` pushes arguments onto the stack, and `DO_FCALL` invokes the function. Internal functions compiled into the PHP binary use `DO_ICALL` instead, avoiding the overhead of userspace call frame construction. The opcode sequence exposes the cost of PHP's dynamic typing—every arithmetic operation includes implicit type coercion guards that check whether operands are integers, floats, or strings requiring conversion.

```bash
php -d vld.active=1 -d vld.execute=0 opcode_dump.php
```

The disassembly output will resemble the following structure, showing exact opcode offsets and operand addressing modes. The `CV` prefix denotes compiled variables allocated in the function's local variable table, while `TMP` indicates temporaries allocated on the VM stack. Jump targets appear as absolute offsets, and the opcode sequence reveals that the conditional expression uses a computed jump—the comparison result determines whether execution falls through or jumps to the false branch assignment.

```text
function compute_discount:
line     #* I O op                       fetch  ext  return  operands
-------------------------------------------------------------------------------------
   3     0  >   RECV                                             1      $price
         1      RECV                                             2      $quantity
   4     2      MUL                                      ~0      $price, $quantity
         3      ASSIGN                                           $subtotal, ~0
   5     4      IS_SMALLER_OR_EQUAL                      ~2      10, $quantity
         5      JMPZ                                             ~2, ->8
         6  >   QM_ASSIGN                                ~3      0.15
         7      JMP                                              ->9
         8  >   QM_ASSIGN                                ~3      0.05
         9  >   ASSIGN                                           $discount_rate, ~3
   6    10      SUB                                      ~5      1, $discount_rate
        11      MUL                                      ~6      $subtotal, ~5
        12    > RETURN                                           ~6
```

Now enable OPcache's JIT compiler and observe the native code generation. The JIT configuration requires specifying a buffer size for compiled code, a compilation threshold that determines when hot functions are compiled, and a JIT mode selecting between function-level and tracing strategies. Configure OPcache to use function JIT with a conservative threshold, allowing immediate compilation for test functions. The JIT output directory must be writable, and debug flags should be enabled to generate disassembly listings.

```ini
opcache.enable=1
opcache.enable_cli=1
opcache.jit_buffer_size=128M
opcache.jit=1255
opcache.jit_debug=1
```

The `opcache.jit=1255` setting encodes multiple configuration flags in a four-digit bitmask. The first digit enables the JIT, the second selects tracing vs. function mode, the third controls register allocation strategy, and the fourth sets optimization level. The value 1255 activates function JIT with aggressive optimization and complete register allocation. Run the `compute_discount` function in a tight loop to trigger JIT compilation, then inspect the generated machine code using `gdb` or by examining the JIT debug output.

```php
<?php
// jit_trigger.php
function compute_discount(float $price, int $quantity): float {
    $subtotal = $price * $quantity;
    $discount_rate = ($quantity >= 10) ? 0.15 : 0.05;
    return $subtotal * (1.0 - $discount_rate);
}

// Warm up the JIT by invoking the function repeatedly
for ($i = 0; $i < 10000; $i++) {
    compute_discount(99.99, 15);
}

echo "JIT compilation triggered\n";
```

Execute this script with JIT debugging enabled. The runtime will emit messages indicating when functions are compiled, along with disassembly of the generated machine code. The x86-64 output will include SSE floating-point instructions (`mulsd`, `subsd`), conditional move instructions (`cmovge`), and optimized register allocation that eliminates memory traffic for temporary variables. Compare this to the opcode sequence—the JIT compiler has eliminated the opcode dispatch loop, inlined type checks, and specialized arithmetic operations based on observed type profiles.

```bash
php -d opcache.jit_debug=0x1FF jit_trigger.php 2>&1 | less
```

The disassembly output, found in the debug trace or by attaching `gdb` to the running process, reveals the compiled function's machine code. The prologue establishes a stack frame, the body contains vectorized floating-point operations, and the epilogue restores registers and returns. Notice that the conditional branch has been transformed into a branchless conditional move when possible, eliminating pipeline stalls from misprediction. The JIT also hoists invariant computations—since `1.0` is a compile-time constant, the subtraction `1.0 - $discount_rate` can be optimized by precomputing `1.0` in a register.

To connect machine code back to source, use `gdb` to set breakpoints on the JIT-compiled function. Attach `gdb` to the PHP process, locate the JIT region in memory via `/proc/[pid]/maps`, and disassemble the function at its entry point. The debugger will show the exact instruction sequence, register assignments, and memory operands. Single-step through the function while printing register values to observe how data flows from function arguments to the return value.

```bash
php jit_trigger.php &
PID=$!
gdb -p $PID
```

Within `gdb`, identify the JIT code region by examining the memory map. OPcache allocates an executable memory region for compiled code, typically marked with `rwx` permissions. Disassemble the function by name if symbols are available, or by address if working with stripped binaries. The disassembly command `disas/r [address]` shows raw bytes alongside instructions, enabling manual verification of instruction encoding and alignment.

```gdb
(gdb) info proc mappings
(gdb) disas/r [JIT_region_start_address]
(gdb) break *[function_entry_point]
(gdb) continue
(gdb) stepi
(gdb) info registers xmm0 xmm1
```

The register dump reveals that SSE registers hold floating-point operands, general-purpose registers hold integer arguments, and the instruction pointer advances through the compiled function. Compare this execution trace to the opcode listing—the JIT compiler has transformed a stack-based bytecode interpreter loop into a register-based direct execution model, eliminating the overhead of opcode fetch, decode, and dispatch. This direct observation of the compilation pipeline's output builds intuition for when JIT optimization succeeds and when deoptimization traps force fallback to interpreted execution.

For a complete verification workflow, construct a test suite that compares opcode execution counts, JIT compilation success rates, and native code efficiency. Write a benchmark function performing a known number of operations—say, one million array accesses—then profile it under three conditions: interpreted mode with OPcache disabled, cached opcode execution with JIT disabled, and JIT-compiled execution. Use Xdebug profiling to measure opcode execution overhead, `perf` to count hardware events like instruction retirement and cache misses, and `time` to measure wall-clock duration. The results quantify the optimization impact at each compilation stage, revealing where the PHP runtime invests its execution budget.

```php
<?php
// benchmark_pipeline.php
function array_sum_manual(array $data): float {
    $sum = 0.0;
    $count = count($data);
    for ($i = 0; $i < $count; $i++) {
        $sum += $data[$i];
    }
    return $sum;
}

$data = array_fill(0, 1000000, 3.14159);

$start = hrtime(true);
$result = array_sum_manual($data);
$duration = (hrtime(true) - $start) / 1e9;

printf("Result: %.2f, Duration: %.4fs\n", $result, $duration);
```

Run this benchmark under different OPcache and JIT configurations, recording execution time and `perf stat` counters. The measurements will show that interpreted execution consumes hundreds of millions of instructions, cached opcode execution reduces this by an order of magnitude, and JIT compilation achieves another 5–10× improvement by eliminating the opcode dispatcher. The cache miss rate should decrease under JIT execution as hot code fits in the L1 instruction cache, whereas opcode interpretation scatters cache lines across the dispatcher, opcode handlers, and data accesses.

```bash
php -d opcache.enable=0 benchmark_pipeline.php
php -d opcache.enable=1 -d opcache.jit_buffer_size=0 benchmark_pipeline.php
php -d opcache.enable=1 -d opcache.jit_buffer_size=128M benchmark_pipeline.php

perf stat -e instructions,cycles,cache-references,cache-misses php benchmark_pipeline.php
```

This exercise establishes the diagnostic foundation for all subsequent optimization work. By observing how source code transforms through AST, opcodes, and machine instructions, engineers learn to predict performance characteristics from syntax alone, recognize when JIT compilation will succeed, and identify language constructs that resist optimization. The ability to read opcode listings and disassembly output becomes essential when profiling reveals unexpected bottlenecks or when debugging runtime crashes that occur only in JIT-compiled code.

## Exercise 2: Cache Miss & Throughput Profiling

Modern CPU performance depends critically on memory hierarchy behavior—an L1 cache hit delivers data in 4 cycles, an L2 hit takes 12 cycles, an L3 hit costs 40 cycles, and a main memory access stalls the pipeline for 200 cycles. PHP's dynamic data structures, reference counting, and copy-on-write semantics create unpredictable memory access patterns that thrash CPU caches, degrading throughput by orders of magnitude compared to cache-friendly code. This exercise instruments PHP applications with hardware performance counters, cache simulators, and memory profilers to identify data structure layouts, access patterns, and algorithmic choices that cause cache pollution. Engineers learn to correlate source-level operations—array iteration, object property access, string concatenation—with micro-architectural events like L1 misses, TLB shootdowns, and memory bandwidth saturation.

PHP's zval structure is the root cause of many cache inefficiencies. Each zval occupies 16 bytes and contains a type tag, a union holding the actual value (integer, float, pointer to string/array/object), and reference counting metadata. Operations on zvals frequently dereference pointers, chasing linked structures across cache lines. Arrays are implemented as hash tables that store zval pointers, not inline values, so iterating an array of integers triggers one cache miss per element to fetch the zval, plus additional misses to access the hash table buckets. Objects introduce another indirection layer—property lookups traverse the object's property table hashtable, then dereference the resulting zval pointer. These pointer chasing patterns are antithetical to cache locality, yet they are unavoidable in PHP's execution model. The goal is not to eliminate cache misses—that is impossible—but to minimize them through data structure choice, access ordering, and algorithmic redesign.

Begin by establishing baseline cache behavior for a representative workload. Write a PHP script that constructs a large array of integers, iterates it sequentially, sums the values, and then iterates it in random order. The sequential iteration should exhibit good spatial locality with predictable prefetch, while random access should cause cache thrashing as each lookup hits an unpredictable cache line. Profile both patterns with `perf` hardware counters, recording L1 data cache loads, L1 data cache misses, L2 cache misses, and instructions retired. The ratio of misses to loads quantifies cache efficiency, and the comparison between sequential and random access isolates the cost of poor locality.

```php
<?php
// cache_locality.php
function sequential_sum(array $data): int {
    $sum = 0;
    $count = count($data);
    for ($i = 0; $i < $count; $i++) {
        $sum += $data[$i];
    }
    return $sum;
}

function random_sum(array $data, array $indices): int {
    $sum = 0;
    $count = count($indices);
    for ($i = 0; $i < $count; $i++) {
        $sum += $data[$indices[$i]];
    }
    return $sum;
}

$size = 1000000;
$data = range(0, $size - 1);
$indices = range(0, $size - 1);
shuffle($indices);

echo "Sequential access:\n";
$start = hrtime(true);
$result = sequential_sum($data);
$seq_duration = (hrtime(true) - $start) / 1e9;
printf("  Result: %d, Duration: %.4fs\n", $result, $seq_duration);

echo "Random access:\n";
$start = hrtime(true);
$result = random_sum($data, $indices);
$rand_duration = (hrtime(true) - $start) / 1e9;
printf("  Result: %d, Duration: %.4fs\n", $result, $rand_duration);

printf("Random slowdown: %.2fx\n", $rand_duration / $seq_duration);
```

Execute this benchmark with `perf stat` to collect hardware counter samples. The sequential access pattern should show an L1 miss rate under 5%, as the CPU's hardware prefetcher anticipates the linear traversal and preloads cache lines. The random access pattern will exhibit a 50–80% miss rate, stalling on nearly every array element. The instructions-per-cycle (IPC) metric collapses under random access, often falling below 0.5, indicating that the CPU spends most of its time waiting for memory rather than executing instructions.

```bash
perf stat -e L1-dcache-loads,L1-dcache-load-misses,L2-cache-loads,L2-cache-misses,instructions,cycles php cache_locality.php
```

The `perf stat` output will include absolute event counts and derived metrics. Compare the L1 miss rate (misses / loads) between the two functions. Sequential access typically achieves 2–5% miss rates, while random access exceeds 50%. The cycle count for random access will be 3–5× higher despite executing the same number of instructions, proving that memory latency, not computation, dominates execution time. This baseline establishes that PHP's array iteration is memory-bound and highly sensitive to access patterns.

To visualize cache behavior at finer granularity, use Valgrind's Cachegrind tool to simulate CPU cache hierarchy. Cachegrind models L1 instruction and data caches, plus a unified L2 cache, tracking every memory reference and computing miss rates per function. The simulation incurs 50–100× slowdown, but it produces detailed reports showing which functions and source lines cause the most cache misses. Run the cache locality benchmark under Cachegrind, then inspect the output with `cg_annotate` to see per-line cache miss attribution.

```bash
valgrind --tool=cachegrind --cache-sim=yes php cache_locality.php
cg_annotate cachegrind.out.[pid]
```

The Cachegrind output includes a summary showing global miss rates for instruction fetches (Ir, I1mr, ILmr) and data accesses (Dr, D1mr, DLmr). The annotated source listing attributes misses to individual lines, revealing that the array access `$data[$indices[$i]]` in the random path incurs the majority of L1 data misses. The instruction cache remains largely unaffected—PHP's opcode loops are small and fit in L1 icache—confirming that data access patterns, not code size, drive cache behavior.

Next, investigate how PHP's internal data structures contribute to cache pollution. PHP arrays are implemented as ordered hash tables that maintain insertion order while providing O(1) lookup. Each bucket contains a 32-byte structure holding the key, value zval, hash code, and linked list pointers. When an array grows, PHP allocates a larger bucket array and rehashes all elements, touching every cache line in the old and new arrays. Write a benchmark that grows an array incrementally by appending elements, forcing periodic rehashing, and measure cache behavior during growth. Compare this to pre-allocating the array with `array_fill`, which avoids rehashing entirely.

```php
<?php
// array_growth.php
function incremental_growth(int $size): array {
    $arr = [];
    for ($i = 0; $i < $size; $i++) {
        $arr[] = $i;
    }
    return $arr;
}

function preallocated_growth(int $size): array {
    $arr = array_fill(0, $size, 0);
    for ($i = 0; $i < $size; $i++) {
        $arr[$i] = $i;
    }
    return $arr;
}

$size = 1000000;

echo "Incremental growth:\n";
$start = hrtime(true);
$arr = incremental_growth($size);
$inc_duration = (hrtime(true) - $start) / 1e9;
printf("  Duration: %.4fs\n", $inc_duration);

echo "Preallocated growth:\n";
$start = hrtime(true);
$arr = preallocated_growth($size);
$pre_duration = (hrtime(true) - $start) / 1e9;
printf("  Duration: %.4fs\n", $pre_duration);

printf("Preallocation speedup: %.2fx\n", $inc_duration / $pre_duration);
```

Profile this benchmark with `perf` and Cachegrind to quantify the cost of dynamic rehashing. Incremental growth will show elevated L2 miss rates during rehash events, as the old and new bucket arrays exceed L2 capacity and spill to main memory. The total allocation count, measured via `perf` memory access counters, will be higher for incremental growth due to intermediate allocations. Preallocation eliminates rehashing, reducing cache misses and achieving 2–3× faster execution.

```bash
perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses php array_growth.php
```

Extend the analysis to object property access patterns, which exhibit even worse cache behavior than arrays. PHP objects store properties in a hashtable indexed by property name, requiring a hash computation, bucket traversal, and zval dereference for every access. Unlike arrays, which can be iterated via integer indices, object properties force hashtable lookups even in hot loops. Create a benchmark that accesses object properties in a tight loop, comparing struct-like objects (few properties, accessed frequently) to dictionary-like objects (many properties, accessed sparsely). Measure the cache miss rate and instruction count for each pattern.

```php
<?php
// object_access.php
class StructLike {
    public int $x = 0;
    public int $y = 0;
    public int $z = 0;
}

class DictLike {
    private array $data = [];
    
    public function __construct(int $count) {
        for ($i = 0; $i < $count; $i++) {
            $this->data["prop_$i"] = 0;
        }
    }
    
    public function get(string $key): int {
        return $this->data[$key] ?? 0;
    }
}

$iterations = 1000000;

echo "Struct-like access:\n";
$obj = new StructLike();
$start = hrtime(true);
for ($i = 0; $i < $iterations; $i++) {
    $sum = $obj->x + $obj->y + $obj->z;
    $obj->x = $sum % 1000;
}
$struct_duration = (hrtime(true) - $start) / 1e9;
printf("  Duration: %.4fs\n", $struct_duration);

echo "Dict-like access:\n";
$obj = new DictLike(100);
$start = hrtime(true);
for ($i = 0; $i < $iterations; $i++) {
    $sum = $obj->get('prop_0') + $obj->get('prop_50') + $obj->get('prop_99');
}
$dict_duration = (hrtime(true) - $start) / 1e9;
printf("  Duration: %.4fs\n", $dict_duration);

printf("Dict-like slowdown: %.2fx\n", $dict_duration / $struct_duration);
```

Profile this benchmark with `perf` to observe that struct-like access benefits from compact memory layout—three integer properties fit in a single cache line—while dictionary-like access suffers from hashtable overhead and poor locality. The struct-like object achieves an L1 miss rate under 10%, whereas the dictionary-like object exceeds 40% misses due to hashtable bucket traversal. The instruction count for dictionary access is 5–10× higher, reflecting the hash computation and linked list traversal overhead.

```bash
perf stat -e L1-dcache-loads,L1-dcache-load-misses,instructions,cycles php object_access.php
```

To complete the cache profiling workflow, use `perf record` to capture sample-based profiles that attribute cache misses to specific functions and source lines. The `perf record` command records hardware event samples at a fixed frequency, capturing instruction pointers, call stacks, and event counts. After recording, use `perf report` to generate a flame graph or annotated source view showing where cache misses occur. This differential profiling workflow identifies optimization targets—functions with high miss rates are candidates for data structure redesign, access pattern reordering, or caching.

```bash
perf record -e L1-dcache-load-misses -g php cache_locality.php
perf report --stdio
```

The `perf report` output ranks functions by cache miss count, showing that `sequential_sum` and `random_sum` dominate. Drill into the annotated source view to see that the array access expression accounts for most misses. Use this information to guide optimization: replace random access with sequential scans where possible, batch lookups to improve temporal locality, or replace arrays with SplFixedArray for unboxed integer storage that eliminates zval indirection.

Apply the cache profiling methodology to a real-world workload: a JSON deserialization benchmark. JSON parsing in PHP allocates numerous small objects and arrays, creating a fragmented heap with poor cache locality. Write a benchmark that parses a large JSON document, measures cache behavior, and compares the performance of `json_decode` to a custom parser that preallocates arrays and reuses buffers. The custom parser should exhibit better cache behavior due to reduced allocation churn and improved spatial locality.

```php
<?php
// json_cache_profile.php
$json = json_encode(array_fill(0, 10000, [
    'id' => 12345,
    'name' => 'Test Item',
    'price' => 99.99,
    'tags' => ['tag1', 'tag2', 'tag3']
]));

echo "Standard json_decode:\n";
$start = hrtime(true);
for ($i = 0; $i < 100; $i++) {
    $data = json_decode($json, true);
}
$decode_duration = (hrtime(true) - $start) / 1e9;
printf("  Duration: %.4fs\n", $decode_duration);

echo "\nRunning under perf profiling...\n";
```

Profile this workload with `perf` and Cachegrind to identify whether JSON parsing is CPU-bound or memory-bound. If cache miss rates exceed 20%, the parser is memory-bound, and optimizations should focus on reducing allocation count and improving object layout. If miss rates remain low, the parser is CPU-bound, and optimizations should target the parsing algorithm itself—reducing branch mispredictions, vectorizing string operations, or JIT-compiling the parser state machine.

```bash
perf stat -d php json_cache_profile.php
valgrind --tool=cachegrind --cache-sim=yes php json_cache_profile.php
```

This exercise equips engineers with systematic cache profiling workflows that translate micro-architectural metrics into actionable optimization strategies. By connecting source-level data structure choices to hardware performance counters, engineers learn to write PHP code that respects cache hierarchy constraints, minimizing memory latency and maximizing instruction throughput. The profiling techniques generalize beyond PHP—any dynamic language runtime with heap-allocated data structures and pointer-chasing semantics exhibits similar cache behavior, making these skills transferable to Python, Ruby, JavaScript, and JVM languages.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

PHP's traditional shared-nothing architecture provides memory safety by isolating requests into independent processes, but modern asynchronous runtimes like Swoole, ReactPHP, and RoadRunner introduce shared-memory concurrency that exposes data races, use-after-free bugs, and memory leaks. Coroutines in Swoole execute cooperatively within a single thread, but they share heap-allocated data structures without synchronization primitives, creating race windows where concurrent coroutine switches corrupt shared state. Long-lived event loops accumulate leaked resources over millions of requests, causing gradual memory exhaustion that manifests as out-of-memory crashes hours or days after deployment. This exercise instruments asynchronous PHP applications with ThreadSanitizer, Valgrind's leak detector, and custom coroutine tracing to detect concurrency bugs, quantify leak rates, and verify correctness under stress testing.

Swoole's coroutine model implements M:N scheduling—multiple user-space coroutines multiplex onto a pool of OS threads managed by an internal scheduler. When a coroutine issues a blocking I/O call, the scheduler suspends it, switches to another runnable coroutine, and resumes the original coroutine when I/O completes. This cooperative multitasking eliminates explicit locking for many workloads but creates subtle race conditions when coroutines interleave operations on shared data structures. Consider an HTTP request handler that increments a shared counter—if two coroutines read the counter value, increment it, and write it back without synchronization, one increment is lost. The race window is narrow, often nanoseconds, but at scale it manifests as statistically significant data corruption: missing cache invalidations, dropped metrics, or inconsistent session state.

Begin by constructing a minimal data race scenario using Swoole coroutines. Install Swoole via PECL, ensuring thread safety is enabled in the PHP build. Write a script that spawns multiple coroutines, each incrementing a shared counter without locking. The counter is a plain PHP integer variable shared across coroutines—Swoole's coroutine scheduler makes no guarantees about atomicity, so concurrent increments will race. Run the script repeatedly and observe that the final counter value is consistently lower than the expected total, proving that increments are lost.

```bash
pecl install swoole
```

Verify that Swoole is installed and functional by checking the extension in `php -m`. Then write the race condition test, spawning 1000 coroutines that each increment a shared counter 1000 times. The expected result is 1,000,000, but without synchronization, the actual result will be lower due to lost updates.

```php
<?php
// race_condition.php
use Swoole\Coroutine;

$counter = 0;
$iterations = 1000;
$coroutines = 1000;

for ($i = 0; $i < $coroutines; $i++) {
    Coroutine::create(function () use (&$counter, $iterations) {
        for ($j = 0; $j < $iterations; $j++) {
            $counter++;  // RACE: read-modify-write is not atomic
        }
    });
}

Swoole\Event::wait();
printf("Expected: %d, Actual: %d, Lost: %d\n", 
       $coroutines * $iterations, $counter, ($coroutines * $iterations) - $counter);
```

Execute this script multiple times and record the discrepancy between expected and actual counter values. The lost update count varies with each run due to nondeterministic scheduling, but it typically ranges from hundreds to tens of thousands, representing a 1–5% data loss rate. This demonstrates that PHP's `++` operator is not atomic under concurrent execution—it compiles to a read, increment, and write sequence with an exposed race window.

```bash
php race_condition.php
```

To detect data races systematically, instrument Swoole with ThreadSanitizer (TSan). TSan is a dynamic race detector that tracks memory accesses and synchronization operations, reporting conflicts where two threads (or coroutines) access the same memory location without intervening synchronization. TSan requires recompiling both PHP and Swoole with TSan instrumentation, which intercepts every memory read, write, lock, and unlock operation. The instrumentation incurs 5–15× slowdown and 5–10× memory overhead, but it detects races with near-zero false positives and minimal false negatives.

Recompile PHP with TSan enabled by adding `-fsanitize=thread` to CFLAGS and LDFLAGS. This flags conflicts with AddressSanitizer, so use a separate build. Then recompile Swoole with the same flags, ensuring that both the PHP runtime and Swoole extension are instrumented consistently. The build process is identical to the AddressSanitizer build, replacing `address` with `thread`.

```bash
cd php-8.3.14
make distclean
./configure \
  --enable-debug \
  --enable-maintainer-zts \
  --with-valgrind \
  CFLAGS="-O1 -g3 -fsanitize=thread -fno-omit-frame-pointer" \
  LDFLAGS="-fsanitize=thread"
make -j$(nproc)
sudo make install

cd ../swoole-src
phpize --clean
phpize
./configure
make clean
make CFLAGS="-fsanitize=thread" LDFLAGS="-fsanitize=thread" -j$(nproc)
sudo make install
```

Run the race condition test under the TSan-instrumented runtime. TSan will detect the concurrent unsynchronized accesses to `$counter` and emit a detailed race report showing the conflicting access stacks, the data type and address, and the synchronization epoch that proves the accesses are concurrent. The report pinpoints the exact source line where the race occurs, enabling immediate diagnosis.

```bash
php race_condition.php
```

The TSan output will include a report like the following, showing two conflicting writes to the counter variable. The access stacks trace back through the Swoole coroutine scheduler and into the user code, proving that the increments from different coroutines interleave without synchronization. The `Previous write` section shows the stack trace of the earlier conflicting access, while the `Write` section shows the current access that triggered the race detection.

```text
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7fff1234abcd by thread T2:
    #0 zend_increment_i_zval_handler php-src/Zend/zend_execute.c:1234
    #1 ZEND_PRE_INC_SPEC_CV_HANDLER php-src/Zend/zend_vm_execute.h:5678
    #2 execute_ex php-src/Zend/zend_vm_execute.h:9012
    #3 zend_execute php-src/Zend/zend_vm_execute.h:9234
    #4 zend_call_function php-src/Zend/zend_execute_API.c:567
    ...
  Previous write of size 8 at 0x7fff1234abcd by thread T1:
    #0 zend_increment_i_zval_handler php-src/Zend/zend_execute.c:1234
    ...
==================
```

Fix the race condition by introducing synchronization. Swoole provides a `Swoole\Lock` class that implements mutexes, but for simple counters, PHP's `SplFixedArray` with atomic operations or a custom extension using `__sync_fetch_and_add` is more efficient. For this exercise, use `Swoole\Atomic` as a drop-in replacement for the plain integer counter. `Swoole\Atomic` wraps an atomic integer implementation that uses CPU compare-and-swap instructions to ensure atomicity.

```php
<?php
// race_fixed.php
use Swoole\Coroutine;
use Swoole\Atomic;

$counter = new Atomic(0);
$iterations = 1000;
$coroutines = 1000;

for ($i = 0; $i < $coroutines; $i++) {
    Coroutine::create(function () use ($counter, $iterations) {
        for ($j = 0; $j < $iterations; $j++) {
            $counter->add(1);  // Atomic increment
        }
    });
}

Swoole\Event::wait();
printf("Expected: %d, Actual: %d, Lost: %d\n", 
       $coroutines * $iterations, $counter->get(), ($coroutines * $iterations) - $counter->get());
```

Run the fixed version under TSan to verify that no data races are detected. The output should be clean, with the final counter value matching the expected total. This confirms that `Swoole\Atomic` correctly synchronizes concurrent accesses, eliminating the race condition.

```bash
php race_fixed.php
```

Next, investigate memory leaks in long-lived event loop applications. PHP-FPM's process-per-request model naturally bounds leak impact—a leaked allocation is reclaimed when the process terminates after handling the request. But asynchronous runtimes run indefinitely, serving millions of requests in a single process, so even tiny per-request leaks accumulate into gigabytes of wasted memory. Common leak sources include circular references in closures, unclosed file handles, dangling zval references in C extensions, and forgotten event loop timers. Valgrind's Memcheck tool detects leaks by tracking every allocation and reporting blocks that remain reachable but not freed at program exit.

Write a Swoole HTTP server that deliberately leaks memory on every request by accumulating unreferenced objects in a global array. The leak is subtle—objects are added to an array but never removed, so they remain reachable and are not freed by garbage collection. Over time, the array grows indefinitely, consuming memory proportional to request count. This pattern mimics real-world leaks like forgotten cache entries, unclosed database connections, or event listener registrations.

```php
<?php
// leak_server.php
use Swoole\Http\Server;
use Swoole\Http\Request;
use Swoole\Http\Response;

$leaks = [];  // Global array that accumulates leaked objects

$server = new Server('127.0.0.1', 9501);

$server->on('request', function (Request $request, Response $response) use (&$leaks) {
    // Leak: create an object and store it globally without ever removing it
    $leaks[] = [
        'timestamp' => microtime(true),
        'uri' => $request->server['request_uri'],
        'data' => str_repeat('x', 1024)  // 1KB of data per request
    ];
    
    $response->header('Content-Type', 'text/plain');
    $response->end("Request handled. Leaks: " . count($leaks) . "\n");
});

$server->start();
```

Start the server and send it a continuous stream of HTTP requests using `ab` (ApacheBench) or `wrk`. Monitor the process memory usage with `top` or `/proc/[pid]/status` to observe linear memory growth over time. After 10,000 requests, the process will have leaked approximately 10MB (10,000 requests × 1KB per request), proving that the leak is proportional to request volume.

```bash
php leak_server.php &
ab -n 10000 -c 10 http://127.0.0.1:9501/
ps aux | grep php
```

To diagnose the leak systematically, run the server under Valgrind's Memcheck tool. Memcheck tracks every `malloc`, `free`, and pointer operation, building a graph of allocated blocks and their reachability. At program exit (or when explicitly requested via `VALGRIND_DO_LEAK_CHECK`), Memcheck reports all allocated blocks that are still reachable from global variables or stack frames but were never freed. The report categorizes leaks as "definitely lost" (no pointers remain), "indirectly lost" (reachable only through lost blocks), "possibly lost" (ambiguous pointers), or "still reachable" (intentional globals).

```bash
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes php leak_server.php
```

Let the server handle a small number of requests (100–1000 to keep the Valgrind run duration manageable), then terminate it with `SIGINT`. Valgrind will emit a leak report showing that the `$leaks` array and its contents are "still reachable" but likely unintentional. The report includes allocation stack traces showing where the leaked blocks were created, pointing directly to the line `$leaks[] = [...]`.

The Valgrind output will resemble the following, showing the total leaked bytes and the allocation call stacks. The `still reachable` category indicates memory that was allocated but not freed, though it remained accessible via global pointers. In a long-lived server, "still reachable" leaks are as problematic as "definitely lost" leaks because they accumulate indefinitely.

```text
==12345== LEAK SUMMARY:
==12345==    definitely lost: 0 bytes in 0 blocks
==12345==    indirectly lost: 0 bytes in 0 blocks
==12345==      possibly lost: 0 bytes in 0 blocks
==12345==    still reachable: 10,485,760 bytes in 10,000 blocks
==12345==         suppressed: 0 bytes in 0 blocks
==12345== 
==12345== 1,024 bytes in 1 blocks are still reachable in loss record 1 of 10,000
==12345==    at 0x4C2FB0F: malloc (vg_replace_malloc.c:299)
==12345==    by 0x6A8F12: zend_string_alloc (zend_string.h:123)
==12345==    by 0x6A9034: zend_new_array (zend_hash.c:234)
==12345==    by 0x5F8A21: ZEND_ASSIGN_DIM_SPEC_VAR_CONST_HANDLER (zend_vm_execute.h:4567)
==12345==    by 0x5E9123: execute_ex (zend_vm_execute.h:9012)
==12345==    by 0x5E9234: zend_execute (zend_vm_execute.h:9234)
==12345==    by 0x5A7890: zend_call_function (zend_execute_API.c:567)
```

Fix the leak by adding a request counter and evicting old entries from the `$leaks` array once it exceeds a threshold. This pattern is common in production caches—keep the most recent N entries and discard older ones. Alternatively, use a weak reference mechanism (via `WeakMap` in PHP 8) to allow garbage collection of objects even when they remain in the global array.

```php
<?php
// leak_fixed.php
use Swoole\Http\Server;
use Swoole\Http\Request;
use Swoole\Http\Response;

$leaks = [];
$max_leaks = 1000;  // Bound the array size

$server = new Server('127.0.0.1', 9501);

$server->on('request', function (Request $request, Response $response) use (&$leaks, $max_leaks) {
    $leaks[] = [
        'timestamp' => microtime(true),
        'uri' => $request->server['request_uri'],
        'data' => str_repeat('x', 1024)
    ];
    
    // Evict oldest entries if array exceeds threshold
    if (count($leaks) > $max_leaks) {
        array_shift($leaks);
    }
    
    $response->header('Content-Type', 'text/plain');
    $response->end("Request handled. Leaks: " . count($leaks) . "\n");
});

$server->start();
```

Run the fixed version under Valgrind and verify that memory usage stabilizes after reaching the threshold. The "still reachable" leak count should plateau at approximately `$max_leaks × 1KB`, proving that the bounded array size prevents unbounded growth. This pattern applies broadly—bounded LRU caches, connection pools, and circular buffers all trade memory overhead for leak prevention.

For production leak debugging, integrate the `memory_get_usage()` and `memory_get_peak_usage()` functions into health check endpoints. Log memory usage periodically and alert when it exceeds expected thresholds. Combine this with heap profiling tools like `valgrind --tool=massif` to generate time-series graphs of memory allocation over the server's lifetime. Massif tracks allocation call stacks and produces output files that visualize which functions allocate the most memory and how heap size evolves over time.

```bash
valgrind --tool=massif --massif-out-file=massif.out php leak_server.php
# After some requests, terminate the server
ms_print massif.out > massif_report.txt
less massif_report.txt
```

The Massif report shows a timeline of heap allocations, with peaks and valleys indicating allocation bursts and garbage collection cycles. The call stack attribution identifies which functions contribute most to peak memory usage, guiding optimization efforts. For the leak server, the report will show a monotonically increasing heap size with the `$leaks[] = ` assignment as the primary contributor.

Extend the leak analysis to detect resource leaks beyond memory—unclosed file handles, database connections, and sockets. PHP's garbage collector reclaims memory but does not close file descriptors, so forgetting to call `fclose()` or connection close methods exhausts the process's file descriptor limit. Use `lsof` to list open file descriptors, filtering for the PHP process, and watch the count grow over time if resources are leaked. Write a test that opens files in a loop without closing them, then run `lsof` periodically to observe descriptor accumulation.

```php
<?php
// fd_leak.php
for ($i = 0; $i < 1000; $i++) {
    $fp = fopen('/tmp/test.txt', 'r');
    // Missing fclose($fp) - file descriptor leaks
    usleep(10000);  // 10ms delay
}

echo "Completed\n";
sleep(10);  // Keep process alive for inspection
```

Run this script in the background and monitor file descriptor count with `lsof`. The descriptor count will grow linearly, eventually hitting the `ulimit -n` limit and causing `fopen` to fail with "Too many open files."

```bash
php fd_leak.php &
PID=$!
watch -n 1 "lsof -p $PID | wc -l"
```

Fix the leak by explicitly closing file handles with `fclose()` or using resource-managing constructs like `try-finally` blocks. For database connections, use connection pooling libraries that enforce resource limits and automatic cleanup.

This exercise establishes rigorous verification workflows for concurrent and long-lived PHP applications. By combining ThreadSanitizer for race detection, Valgrind for leak diagnosis, and resource monitoring for descriptor exhaustion, engineers build confidence that asynchronous PHP code is memory-safe and concurrency-correct under production workloads. The techniques generalize to any runtime supporting shared-memory concurrency—Node.js, Python asyncio, and Go goroutines all require similar sanitizer instrumentation and stress testing to surface latent bugs before they corrupt production data.

## Developer Cheat Sheet & Toolchain Checklist

This section consolidates the verification commands, diagnostic flags, and operational workflows from the preceding exercises into a reference guide for daily development practice. Bookmark these commands for immediate access during debugging sessions, performance investigations, and pre-deployment verification.

### Environment Setup Verification

Confirm that the diagnostic toolchain is correctly installed and accessible. Each command should execute without errors and report version information.

```bash
php -v                          # PHP version and build flags
php -m | grep -E 'xdebug|Zend OPcache|swoole'  # Extensions loaded
valgrind --version              # Valgrind availability
perf --version                  # Linux perf tools
gdb --version                   # GNU debugger
pecl list                       # Installed PECL extensions
```

Verify that debug symbols are present in the PHP binary by running `gdb` and checking for source file information. If symbols are missing, recompile PHP with `--enable-debug` and `-g3` CFLAGS.

```bash
gdb --batch -ex 'file /usr/local/bin/php' -ex 'info sources' | head -20
```

### Quick Diagnostic Commands

Execute these one-liners during development to catch issues before they reach code review or production.

```bash
# Syntax check without execution
php -l script.php

# Display opcode disassembly
php -d vld.active=1 -d vld.execute=0 script.php

# Profile with Xdebug (requires XDEBUG_TRIGGER=1)
XDEBUG_TRIGGER=1 php script.php
ls -lh /var/tmp/xdebug/  # Cachegrind files

# Leak check with Valgrind
valgrind --leak-check=full --show-leak-kinds=all php script.php

# Cache simulation with Cachegrind
valgrind --tool=cachegrind php script.php
cg_annotate cachegrind.out.[pid]

# Hardware counter profiling with perf
perf stat -d php script.php
perf record -g php script.php
perf report --stdio

# ThreadSanitizer race detection (requires TSan build)
php script.php  # TSan reports races to stderr

# File descriptor leak monitoring
lsof -p $(pgrep -f 'php script.php') | wc -l
```

### OPcache & JIT Configuration Templates

Place these configuration blocks in `php.ini` or a dedicated `99-opcache.ini` file in the configuration directory. Adjust `opcache.memory_consumption` and `opcache.jit_buffer_size` based on application code size and available RAM.

```ini
; Production OPcache settings
opcache.enable=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=10000
opcache.validate_timestamps=0  ; Disable for production
opcache.revalidate_freq=0
opcache.save_comments=0
opcache.enable_file_override=1

; JIT compiler settings (function mode, high optimization)
opcache.jit_buffer_size=128M
opcache.jit=1255

; Development debugging flags
opcache.jit_debug=0x1FF  ; Enable only for JIT diagnostics
```

For development environments, enable timestamp validation to reload code on file changes, and activate JIT debugging to observe compilation decisions.

```ini
; Development OPcache settings
opcache.enable=1
opcache.validate_timestamps=1
opcache.revalidate_freq=2
opcache.jit_buffer_size=64M
opcache.jit=1255
opcache.jit_debug=0xFF
```

### Xdebug Profiling Workflow

Activate profiling selectively via environment variables to avoid overhead on non-profiled requests. The `XDEBUG_TRIGGER` variable works with web requests via cookies or query parameters, and with CLI scripts via the environment.

```bash
# CLI profiling
XDEBUG_TRIGGER=1 php script.php

# Web profiling via query parameter
curl 'http://localhost/script.php?XDEBUG_TRIGGER=1'

# Web profiling via cookie
curl -b 'XDEBUG_TRIGGER=1' http://localhost/script.php

# View profiler output
kcachegrind /var/tmp/xdebug/cachegrind.out.* &
```

Analyze the Cachegrind file programmatically to extract top time-consuming functions. Parse the file with `awk` to sort by self-time.

```bash
grep -E '^fl=|^fn=|^[0-9]+ [0-9]+' cachegrind.out.12345 | \
  awk '/^fn=/{fn=$2} /^[0-9]+ [0-9]+/{time+=$2} END{print time, fn}' | \
  sort -rn | head -20
```

### Memory Leak Detection Workflow

Run leak detection in development environments before merging code. For long-lived servers, sample leak checks periodically by running Valgrind on a subset of production traffic mirrored to a test instance.

```bash
# Full leak report with allocation traces
valgrind \
  --leak-check=full \
  --show-leak-kinds=all \
  --track-origins=yes \
  --log-file=valgrind.log \
  php script.php

# Suppress known false positives (PHP internals, Zend allocator)
valgrind \
  --leak-check=full \
  --suppressions=/usr/local/lib/php/valgrind.supp \
  php script.php

# Heap profiling with Massif
valgrind --tool=massif --massif-out-file=massif.out php script.php
ms_print massif.out > massif_report.txt
```

Create a custom suppression file for recurring false positives. Valgrind generates suppression entries when you mark a leak as intentional during interactive debugging.

```bash
valgrind --leak-check=full --gen-suppressions=all php script.php 2>&1 | \
  tee valgrind_output.txt
# Manually extract suppression blocks and append to suppressions file
```

### Performance Counter Analysis

Collect comprehensive hardware event data to diagnose performance bottlenecks. The `-d` flag enables detailed mode, including L1/L2/L3 cache events, TLB misses, and branch mispredictions.

```bash
# Basic event counters
perf stat php script.php

# Detailed cache and memory statistics
perf stat -d php script.php

# Record sample-based profile for flame graphs
perf record -F 99 -g php script.php
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg

# List available hardware events
perf list

# Profile specific events (cache misses, branch mispredictions)
perf stat -e L1-dcache-load-misses,L1-dcache-loads,branch-misses,branches \
  php script.php
```

Interpret the output by computing derived metrics. An L1 miss rate above 5% indicates poor cache locality, and a branch misprediction rate above 2% suggests unpredictable control flow.

```bash
# Compute cache miss rate
perf stat -e L1-dcache-loads,L1-dcache-load-misses php script.php 2>&1 | \
  awk '/L1-dcache-loads/{loads=$1} /L1-dcache-load-misses/{misses=$1} \
       END{print "Miss rate:", (misses/loads)*100 "%"}'
```

### Data Race Detection with ThreadSanitizer

Run all concurrent code paths under TSan during development. The instrumentation overhead is acceptable for test suites but prohibitive for production.

```bash
# Run under TSan (requires TSan-instrumented PHP build)
php script.php 2>&1 | tee tsan.log

# Filter TSan output for race warnings
grep -A 20 'WARNING: ThreadSanitizer: data race' tsan.log
```

Integrate TSan checks into CI pipelines by running concurrent test suites with TSan enabled and failing the build if races are detected.

```bash
#!/bin/bash
# ci_tsan_check.sh
export TSAN_OPTIONS="halt_on_error=1 history_size=7"
php run_tests.php
if [ $? -ne 0 ]; then
  echo "ThreadSanitizer detected data races!"
  exit 1
fi
```

### GDB Debugging Recipes

Attach to a running PHP process to inspect live state, including variable values, call stacks, and memory contents. Useful for debugging infinite loops, hangs, or crashes that only occur in production.

```bash
# Attach to running process
gdb -p $(pgrep -f 'php-fpm.*pool')

# Within GDB, print current stack trace
(gdb) thread apply all bt

# Print variable value (requires debug symbols)
(gdb) print (char*)executor_globals.current_execute_data->func->common.function_name->val

# Set breakpoint on function
(gdb) break zif_some_function
(gdb) continue

# Dump core file for offline analysis
(gdb) generate-core-file
(gdb) quit

# Analyze core file later
gdb /usr/local/bin/php core.12345
(gdb) bt full
```

For crashes, enable core dumps system-wide and configure the core file pattern to include timestamps.

```bash
ulimit -c unlimited
echo '/tmp/core.%e.%p.%t' | sudo tee /proc/sys/kernel/core_pattern
```

### Resource Monitoring & Alerting

Instrument production services to export memory usage, file descriptor counts, and request latency metrics. Use these queries during incident response.

```bash
# Current memory usage
ps aux | awk '/php-fpm.*pool/{print $6/1024 " MB"}'

# File descriptor count per process
lsof -p $(pgrep -f 'php-fpm.*pool') | wc -l

# Peak memory usage from /proc
grep VmPeak /proc/$(pgrep -f 'php-fpm.*pool')/status

# OPcache statistics (requires opcache status endpoint)
curl -s http://localhost/opcache-status.php | jq '.memory_usage'
```

Create a monitoring script that logs these metrics periodically and alerts when thresholds are exceeded.

```bash
#!/bin/bash
# monitor_php.sh
while true; do
  PID=$(pgrep -f 'php-fpm.*pool' | head -1)
  MEM=$(awk '/VmRSS/{print $2}' /proc/$PID/status)
  FDS=$(lsof -p $PID 2>/dev/null | wc -l)
  echo "$(date) PID=$PID MEM=${MEM}KB FDS=$FDS"
  
  if [ "$MEM" -gt $((2 * 1024 * 1024)) ]; then  # 2GB threshold
    echo "ALERT: Memory usage exceeded 2GB"
  fi
  
  sleep 60
done
```

### Benchmarking Standards

Establish repeatable benchmark conditions by disabling CPU frequency scaling, pinning processes to specific cores, and isolating test machines from production workloads.

```bash
# Disable CPU frequency scaling (requires root)
sudo cpupower frequency-set -g performance

# Pin PHP process to specific cores
taskset -c 0,1 php benchmark.php

# Run benchmark multiple times and compute statistics
for i in {1..10}; do
  php benchmark.php 2>&1 | tee run_$i.log
done
awk '/Duration:/{sum+=$2; count++} END{print "Mean:", sum/count "s"}' run_*.log
```

Use `ab` or `wrk` for HTTP benchmarking, ensuring that the load generator runs on a separate machine to avoid interference.

```bash
# ApacheBench with concurrency
ab -n 100000 -c 100 http://target.local/endpoint

# wrk with Lua scripting for complex scenarios
wrk -t 4 -c 100 -d 30s --script post_request.lua http://target.local/endpoint
```

This cheat sheet serves as operational muscle memory, encoding the diagnostic procedures from the exercises into commands ready for immediate execution. Keep it accessible during development, code review, and incident response. Mastery of these tools transforms debugging from guesswork into systematic root cause analysis, and performance optimization from trial-and-error into data-driven engineering.
