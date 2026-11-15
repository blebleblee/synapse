# Lesson 1: QA Foundations, Testing Theory, Defect Lifecycle

## 1. First-Principles Intuition & Invariants

Software quality is not a property you add to a system after it is built. It is a structural invariant that either exists in the architecture, the process, and the team's shared mental model, or it does not exist at all. This distinction is not philosophical posturing — it has direct, measurable consequences on defect escape rates, regression density, and the cost of change over time. For senior engineers and systems programmers, the temptation is to treat QA as a downstream activity: something testers handle after the compiler says yes. That framing is the original sin of software quality, and understanding why requires going back to the theoretical foundations of what "quality" actually means in a formal sense.

### What Quality Means, Formally

David Garvin's 1984 framework, developed at Harvard and later canonized in manufacturing and software literature, defines quality across five competing perspectives. The **transcendent view** holds that quality is an innate excellence you recognize but cannot precisely define — this is the perspective of the craftsman and is largely useless for engineering contracts. The **product-based view** treats quality as a precisely measurable variable tied to specific attributes: mean time between failures, cyclomatic complexity, branch coverage, and so on. The **user-based view** is entirely subjective — quality is fitness for purpose as perceived by the end user, which means two correct implementations of the same specification can differ wildly in perceived quality. The **manufacturing-based view** defines quality as conformance to requirements, the dominant perspective in industrial software: if the spec says the response latency must be under 100ms and it is, the product has quality in this dimension regardless of elegance. The **value-based view** ties quality to cost: a product is high quality if it delivers acceptable performance at an acceptable price.

Garvin further decomposed product quality into eight dimensions — performance, features, reliability, conformance, durability, serviceability, aesthetics, and perceived quality — and the tension between these dimensions is precisely where most real engineering debates live. A systems programmer optimizing a memory allocator for throughput may sacrifice serviceability (the ability to debug it under field conditions) and conformance (strict adherence to `malloc` semantics in edge cases). Those are explicit quality trade-offs, and naming them in Garvin's vocabulary lets a team reason about them deliberately rather than accidentally.

ISO 25010, the successor to ISO 9126 and the current international standard for software product quality, refines this further into two top-level quality models. The **product quality model** defines eight characteristics: functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability, and portability. Each characteristic decomposes into sub-characteristics with associated metrics. Maintainability, for instance, decomposes into modularity, reusability, analysability, modifiability, and testability. For a compiler engineer, testability has a direct architectural implication: an IR lowering pass that cannot be tested in isolation because it reaches into global mutable state has measurably lower quality under ISO 25010 than one with clean input/output boundaries. The standard gives you a formal argument for a design decision. The **quality in use model** defines five characteristics — effectiveness, efficiency, freedom from risk, context coverage, and satisfaction — and measures quality as experienced by real users in real operational contexts. These two models together capture the full contract: what the software is and how it behaves in the hands of its users.

### Verification vs. Validation: The Boehm Dichotomy

Barry Boehm's formulation remains the clearest statement of the fundamental QA duality. **Verification** asks: "Are we building the product right?" It is a static or dynamic analysis of the system against its specification — does the implementation conform to the design? **Validation** asks: "Are we building the right product?" It is an evaluation of the system against the actual needs of the user, independent of whether the specification accurately captured those needs.

These are genuinely orthogonal failure modes. A cryptographic library can be perfectly verified — every function implements its specification exactly, every test case in the test suite passes — and still fail validation catastrophically if the API design makes it easy for callers to misuse nonces, as happened with early GCM implementations. Conversely, a rapidly prototyped system that users love may be entirely unverified: inconsistent internal behavior, undocumented state transitions, latent integer overflows waiting to become security vulnerabilities. Neither error class subsumes the other.

For a systems programmer, verification maps naturally to static analysis (compiler warnings, sanitizers, formal type systems, model checkers like SPIN or TLA+), unit testing, and code review against a formal specification. Validation maps to integration testing, user acceptance testing, A/B testing in production, and the more expensive forms of usability research. The critical engineering discipline is knowing which question you are answering at any given moment, because the tools and the evidence each provides are fundamentally different in character.

### The Error–Fault–Failure Chain

The IEEE standard 610.12 vocabulary, now incorporated into ISO/IEC/IEEE 24765, establishes a precise causal chain that every practitioner must internalize before any test design work is meaningful.

An **error** is a human action that produces an incorrect result. It is cognitive and exists in the mind of the developer: a misunderstanding of two's complement arithmetic, an incorrect assumption about mutex reentrance, a mental model of `realloc` that doesn't account for the case where the new size is zero. Errors are unobservable directly; they only manifest through their downstream effects.

A **fault** (also called a defect or bug) is the representation of an error in the software artifact — the actual incorrect line of code, the missing null check, the off-by-one in a loop bound. A single error in a developer's mental model can produce multiple faults across different parts of a codebase. Faults are static; they exist in the artifact whether or not the software is running.

A **failure** is an observable deviation of the system from its specified or expected behavior at runtime. A fault produces a failure only under specific execution conditions. A latent buffer overflow in a path that handles malformed input may never trigger during normal operation, but when the input arrives, the fault activates, corrupts memory, and the subsequent dereference of a dangled pointer produces a failure — a segfault, a silent data corruption, or a security breach.

This three-stage chain has a profound implication for test design: the goal of testing is not to find faults directly (you cannot observe source code execute) but to create execution conditions under which faults manifest as observable failures. A test that never exercises the fault-containing path will never find the fault, regardless of how many times it runs. This is the first-principles argument for coverage-guided testing: branch coverage, path coverage, and mutation testing are all strategies for ensuring your test inputs actually reach the faults that exist. The chain also explains why static analysis (which finds faults without executing code) and dynamic testing (which finds failures and infers faults) are complementary rather than redundant — they operate at different points in the causal chain.

### Defect Taxonomy and Classification

Classifying defects systematically is not bookkeeping. It is the feedback mechanism that closes the quality loop. The IBM Orthogonal Defect Classification (ODC) scheme, developed by Ram Chillarege in the early 1990s and still one of the most rigorous industry frameworks, classifies defects along two orthogonal axes: the **defect type** (what was wrong in the code — missing logic, wrong algorithm, incorrect initialization, timing/serialization, interface mismatch) and the **defect trigger** (the execution condition that caused the fault to become a failure — simple path, complex path, variation in workload, boundary conditions, hardware configuration). The power of ODC is that the distribution of defect types tells you something about the quality of the development process, while the distribution of triggers tells you something about the quality of the test process.

For systems-level code, a taxonomy aligned with the error–fault–failure chain is particularly useful. Memory safety defects (buffer overflows, use-after-free, double-free, uninitialized reads) form one class, characterized by the fact that the fault and the failure are often separated in time and space — the memory is corrupted in one stack frame, the failure manifests many function calls later when the corrupted value is dereferenced. Concurrency defects (data races, deadlocks, priority inversions, atomicity violations) form a second class, where the trigger is timing-dependent and therefore non-deterministic from run to run. Logic defects (incorrect branch predicates, wrong arithmetic, missed edge cases) form a third class. Interface defects (mismatched calling conventions, incorrect API semantics, violated preconditions) form a fourth. Each class has different detection strategies: AddressSanitizer and Valgrind target memory safety, ThreadSanitizer targets concurrency, symbolic execution and mutation testing target logic, and contract-based testing targets interfaces. A practitioner who classifies defects systematically will discover which class dominates their codebase and can then allocate test investment accordingly rather than treating all defects as equivalent.

---

## 2. Core Architecture & Mechanics

### The Defect Lifecycle as a State Machine

The defect lifecycle is not an administrative formality — it is a formal state machine whose transitions define the information flow that enables a quality-managed process. Understanding it mechanically helps you identify where defects stall, age, and silently expire without resolution.

```
                        ┌─────────────────────────────────────────────────────────┐
                        │                   DEFECT LIFECYCLE                       │
                        └─────────────────────────────────────────────────────────┘

   ┌──────────┐   report    ┌──────────┐  triage    ┌──────────┐  assign    ┌──────────┐
   │  Latent  │ ──────────► │   New    │ ─────────► │ Triaged  │ ─────────► │  Open /  │
   │  (Fault) │             │          │             │          │             │  Active  │
   └──────────┘             └──────────┘             └──────────┘             └────┬─────┘
                                 │                        │                        │
                             duplicate              reject / WONTFIX           fix applied
                             not repro              out of scope                   │
                                 │                        │                        ▼
                                 ▼                        ▼                   ┌──────────┐
                            ┌──────────┐            ┌──────────┐             │  Fixed / │
                            │  Closed  │◄───────────│ Rejected │             │  Pending │
                            │(Duplicate│            │          │             │  Verify  │
                            │ /Invalid)│            └──────────┘             └────┬─────┘
                            └──────────┘                                          │
                                                                        verify passes │ verify fails
                                                                                  │         │
                                                                                  ▼         ▼
                                                                             ┌────────┐ ┌────────┐
                                                                             │ Closed │ │Reopened│
                                                                             │Verified│ │        │
                                                                             └────────┘ └────────┘
```

Each state transition carries a constraint. A defect moves from **New** to **Triaged** only after a human (or automated classifier) has confirmed it is reproducible and belongs to this codebase's scope. The triage step is a gate against noise: without it, engineers spend time on duplicate reports, misconfigured environments, and user errors. A defect moves from **Active** to **Fixed / Pending Verify** when the developer believes the fault has been corrected and a fix has been integrated — critically, the fault is removed but the failure has not yet been confirmed absent. The transition to **Closed Verified** requires a verifier, ideally independent of the developer who made the fix, to confirm that the original failure-producing test case now passes and that no regression has been introduced. The **Reopened** transition is not a failure of process — it is evidence that the fix was incomplete, introduced a secondary fault, or that the test coverage was insufficient to confirm the fix. Tracking reopened-defect rate is one of the most informative process metrics a team can collect.

### The Test Oracle Problem

Defining whether a test has passed or failed requires an **oracle**: a mechanism that determines whether the observed output matches the expected output. This seems trivially obvious — you run the program, compare the output to the expected value, done. But the oracle problem is one of the genuinely hard theoretical problems in software testing, and systems programmers encounter it in acute forms regularly.

The classical formulation, stated by Howden in 1978, is that for a large class of programs, there is no general automated procedure for determining whether an output is correct. Consider a compiler's code generator: given an input program, the oracle must verify not just that the output is valid machine code but that it is semantically equivalent to the input. That equivalence check is at least as hard as compilation itself, and in the general case it is undecidable. Differential testing — compiling the same program with two different compilers and comparing outputs — sidesteps the oracle problem by replacing a ground-truth check with a consistency check: if both compilers agree, the output is probably correct. If they disagree, at least one is wrong. This is the technique John Regehr and colleagues used in Csmith to find hundreds of bugs in GCC and LLVM: not by knowing the correct answer but by exploiting the fact that two independent implementations should not disagree.

Partial oracles handle this in practice. A **crash oracle** requires only that the program not crash or raise a signal — it detects a subset of failures but requires no knowledge of correct output. A **sanitizer oracle** (AddressSanitizer, UndefinedBehaviorSanitizer) detects behavioral invariant violations without requiring a full specification of correct output. A **metamorphic oracle** exploits known relationships between inputs and outputs: if the program computes `f(x)`, then `f(-x)` for a symmetric function should equal `f(x)`, and any violation is a failure even without knowing the true value of `f(x)`. Metamorphic testing is particularly powerful for numerical code, compression algorithms, and search engines where the full output is too expensive to specify but input–output relationships are well-understood.

### The Pesticide Paradox and Coverage Saturation

Boris Beizer articulated the **pesticide paradox** in 1990 with an agricultural analogy that has aged well: if you spray the same pesticide repeatedly, the bugs that survive each application breed, and over time your pest population becomes resistant. The analogy maps cleanly to software — a fixed test suite exercises a fixed set of program paths. Every time the suite runs and all tests pass, two things are true: the paths covered by the suite have not regressed, and the paths not covered by the suite have received no verification at all. As the codebase evolves, new code is written to paths the suite never exercises, and the passing test suite provides a false signal of safety.

The engineering response to the pesticide paradox is systematic test evolution driven by coverage data. A team that tracks branch coverage over time and treats coverage degradation as a build failure is mechanically implementing pesticide paradox mitigation. But branch coverage is a necessary, not sufficient, condition. Two test suites can achieve identical branch coverage while testing completely different value partitions — one might cover the branch but only with inputs in the normal range, leaving boundary conditions and malformed inputs untested. **Mutation testing** addresses this more precisely: artificial faults (mutations) are injected into the codebase — an `>` becomes `>=`, an `&&` becomes `||`, a `return 0` becomes `return 1` — and the test suite is evaluated on its ability to detect these mutations. A mutation that is not killed by any test case reveals a gap in test precision that coverage metrics would not expose. Tools like `mutmut` for Python and `cargo-mutants` for Rust operationalize this for production test suites.

The pesticide paradox has a subtler implication for regression testing specifically. When a defect is fixed, the team typically adds a test case that reproduces the original failure. This is correct practice. But it means the regression suite asymptotically approaches a comprehensive test of historical failure modes while remaining silent about the class of failures that have not yet been observed. For safety-critical systems programming work, the response is to treat the regression suite as a lower bound and invest continuously in exploratory testing, fuzzing, and property-based testing to discover the class of failures that historical defects have not yet revealed.

### Testing Principles as Engineering Invariants

The seven principles articulated in ISTQB's foundation syllabus, though aimed at a general audience, have specific mechanical interpretations for systems-level work that make them worth examining precisely.

**Exhaustive testing is impossible** is not an opinion — it is a formal consequence of the state space explosion that occurs when you consider all possible inputs to any non-trivial function. A 32-bit integer input has 2³² possible values. A function taking two 32-bit inputs has 2⁶⁴. A function operating over a 1KB buffer has an input space that dwarfs the number of atoms in the observable universe. The engineering implication is that test design is fundamentally a problem of selecting maximally informative test cases from a space too large to enumerate, which requires risk-based reasoning: which inputs are most likely to trigger faults given what you know about the implementation? Equivalence partitioning and boundary value analysis are analytical techniques for this selection. Fuzzing is a stochastic technique. Property-based testing (QuickCheck, Hypothesis, `proptest` in Rust) generates random inputs within a specified domain and checks invariant properties. All of these are responses to the impossibility of exhaustive testing, and a mature QA process uses all of them in proportion to the risk and criticality of the component.

**Early testing saves exponential cost** is an empirical finding, not just a slogan. Barry Boehm's empirical studies in the 1970s and 1980s, later confirmed by Capers Jones and others, showed that the cost of fixing a defect grows by roughly an order of magnitude for each phase of development it escapes. A logic error caught in design review costs essentially nothing — a discussion and a correction to a document. The same error caught in unit testing costs some engineer hours. Caught in integration testing it may require rearchitecting a component boundary. Caught in production in a safety-critical system, it costs regulatory proceedings, recalls, or worse. For compiler engineers, this translates directly to the investment in formal specification of IR semantics and aggressive use of debug assertions (`assert()`, Rust's `debug_assert!`, LLVM's `llvm_unreachable`) to catch incorrect assumptions at the earliest possible execution point rather than allowing corrupted state to propagate silently until it manifests far from its source.

**Testing is context-dependent** is the principle that destroys the idea of a universal test strategy. The testing appropriate for a web application handling user preferences is categorically different from the testing appropriate for a memory allocator, a network packet parser, or a cryptographic primitive. For a memory allocator, the most important testing investment is in sanitizer-instrumented builds, fuzz testing with AFL++ or libFuzzer, and formal verification of key invariants (free list consistency, header integrity, alignment guarantees). For a cryptographic primitive, the most important investment is in test vector validation against published standard test vectors, timing analysis to detect secret-dependent branching, and fault injection testing. For a distributed consensus algorithm, the most important investment is in chaos testing, partition simulation, and linearizability checking with tools like Jepsen. No single test methodology is universally optimal — the correct strategy follows from a sober analysis of what can go wrong and what the consequences of failure are.

---

## 3. High-Performance Optimization & Failure Modes

### Operationalizing Quality Models with Testability Metrics

ISO 25010's testability sub-characteristic is not abstract — it has concrete, measurable proxies that experienced teams track and act on. For systems-level code, the most actionable testability metric is **test surface area per module boundary**: a module with clean, narrow interfaces (small number of public symbols, explicit preconditions and postconditions, no access to global mutable state) has exponentially higher testability than one with wide interfaces and implicit side effects. This is a design quality metric that can be measured automatically by parsing symbol tables and control flow graphs.

Consider a concrete workflow for evaluating testability in a C codebase. The `lcov` toolchain, combined with `gcov`-instrumented builds, gives you branch-level coverage maps. Pairing this with `lizard` (a static complexity analyzer) gives you cyclomatic complexity per function. The correlation between high cyclomatic complexity and low branch coverage is a reliable indicator of undertested complexity. A function with cyclomatic complexity above 15 and branch coverage below 60% is a high-priority testability debt item — the complexity makes it hard to test, and the low coverage means the complexity is hiding untested faults.

```makefile
# Makefile fragment for coverage-instrumented build and reporting
CC      = gcc
CFLAGS  = -O0 -g --coverage -fprofile-arcs -ftest-coverage \
          -fsanitize=address,undefined \
          -Wall -Wextra -Wpedantic
LDFLAGS = --coverage -fsanitize=address,undefined

SRCS    = allocator.c arena.c freelist.c
OBJS    = $(SRCS:.c=.o)
TARGET  = allocator_test

.PHONY: all coverage clean

all: $(TARGET)

$(TARGET): $(OBJS) test_main.o
	$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

coverage: all
	./$(TARGET)
	lcov --capture --directory . --output-file coverage.info \
	     --exclude '/usr/include/*'
	genhtml coverage.info --output-directory coverage_report
	@echo "Coverage report generated in coverage_report/index.html"

clean:
	rm -f $(OBJS) test_main.o $(TARGET) *.gcno *.gcda coverage.info
	rm -rf coverage_report
```

The `--coverage` flag instruments every branch in the generated object code with counter updates that `gcov` reads after the test run. The `-fsanitize=address,undefined` flags add the sanitizer oracles discussed earlier, so a single test run simultaneously measures coverage and detects memory and UB failures. This is the minimum instrumented build configuration for any non-trivial systems component entering a QA process.

### Mutation Testing at Scale with cargo-mutants

For a Rust systems component — a memory-safe parser, a lock-free data structure, a protocol codec — mutation testing provides the most precise measure of test suite effectiveness available. The `cargo-mutants` tool inserts mutations at the source level (flipping boolean conditions, replacing arithmetic operators, deleting return expressions) and measures which mutations the test suite kills.

The following `cargo-mutants` configuration (`mutants.toml`) is appropriate for a performance-critical Rust systems library where you want to scope mutations to the core logic and exclude generated or trivially correct code:

```toml
# mutants.toml — cargo-mutants configuration for a systems library
[mutants]

# Directories to mutate; excludes fuzz targets and benchmarks
source_dir = "src"

# Functions matching these patterns are excluded from mutation
# (generated code, trivial accessors, panic handlers)
skip_calls = [
    "unreachable",
    "panic",
    "unwrap",
    "expect",
    "debug_assert",
]

# Timeout per mutant in seconds; set generously for integration-heavy tests
timeout = 60

# Run tests in parallel across available cores
jobs = 8

# Output directory for mutation report
output_dir = "target/mutants"
```

Running `cargo mutants --workspace` against a production allocator or parser will typically reveal several categories of surviving mutants. The most informative are **equivalent mutants** — mutations that do not change observable behavior because the mutated expression is never evaluated on any input in the test suite. Surviving mutants in a range-check function, for instance, almost always indicate that the test suite lacks inputs that probe the boundary condition the check guards against. The fix is not to suppress the surviving mutant but to add test inputs that exercise the boundary, then verify the mutant now dies. This closes the pesticide paradox loop mechanically: mutation testing tells you exactly what the test suite is not testing.

### Defect Escape Rate Analysis and Root Cause Feedback

The highest-value QA process improvement a senior engineering team can make is treating defect escape rates as a continuous control system. A **defect escape** is a fault that passes through one phase of testing and is found in a later phase or in production. Tracking escapes by origin phase and detection phase creates the **defect detection matrix**, and the off-diagonal entries (faults originating in phase N but found in phase M > N) are the signal.

```
Defect Detection Matrix (example, 90-day period)

                   │ Found in Unit │ Found in Integ │ Found in System │ Found in Prod │
───────────────────┼───────────────┼────────────────┼─────────────────┼───────────────┤
Originated in Req  │      0        │       3        │        5        │       2       │
Originated in Arch │      1        │       4        │        2        │       1       │
Originated in Code │     22        │       8        │        3        │       4       │
Originated in Test │      3        │       1        │        0        │       0       │
───────────────────┼───────────────┼────────────────┼─────────────────┼───────────────┤
Totals             │     26        │      16        │       10        │       7       │
```

Reading this matrix: the 4 code-origin defects found in production represent the highest-cost failures — these are the ones that escaped unit testing (22 caught), integration testing (8 more caught), and system testing (3 more caught). The root cause question is not "why were these 4 defects in the code?" but "what property of these 4 defects caused them to be invisible to the previous three test phases?" Answering that question requires examining the specific faults, classifying them by the ODC defect type taxonomy, and asking whether the test design for each phase had the coverage to detect their trigger conditions.

If the 4 production escapes are all concurrency defects triggered under high-load timing conditions, the answer is clear: the unit and integration test environments do not simulate concurrent load. The fix is to add stress tests that inject timing pressure and to include ThreadSanitizer in the CI pipeline. If they are all logic defects in a specific subsystem, the answer may be insufficient mutation testing coverage in that subsystem. If they are all defects in error-handling paths, the answer may be that the test suite exercises only the happy path and never injects faults. The matrix converts an intuitive sense that "we have too many bugs in production" into a precise, actionable signal about where the QA process is failing to detect what classes of defects.

### The Failure Mode of Verification Without Validation

The most dangerous failure mode in a mature QA process is not insufficient testing. It is the false confidence produced by comprehensive verification metrics — high coverage, low defect escape rate, clean static analysis — in the presence of a specification that does not accurately capture what users actually need. This is the gap between verification and validation operationalized as a failure mode.

For a systems programmer, the concrete manifestation is an API that is completely correct by its own specification but whose specification is wrong. A memory allocator that correctly implements its documented alignment guarantees for `malloc` but documents the wrong alignment guarantee — say, 4-byte rather than 8-byte alignment for a platform where `double` requires 8-byte alignment — will pass every test against the specification and silently corrupt data in every caller that stores a `double`. Every test passes. Every coverage metric is green. The fault is in the specification, not the code, and it will only be found through validation — testing the allocator in real calling contexts with real data types — or through integration testing that includes sanitizer instrumentation at the call sites.

This failure mode argues for treating integration testing and end-to-end testing not as redundant layers but as validation layers that test the system against user-level expectations rather than internal specifications. The Rust ecosystem's pattern of documentation tests (doctests) that execute the examples in API documentation is a lightweight form of specification-level validation: if the documented usage is itself a test case, the gap between specification and verification narrows to zero at the documented interface. Combined with property-based testing that generates inputs a human would never think to specify, this multi-layer approach closes the verification/validation gap as tightly as a software engineering process can practically achieve.

### Building a Defect-Aware CI Pipeline

The final practical integration of everything in this lesson is a CI pipeline that makes the error–fault–failure chain, the oracle problem, and the pesticide paradox visible as automated feedback. A minimal but complete pipeline for a systems C/C++ library should include, in order of execution speed, a static analysis gate (clang-tidy, cppcheck, or the Clang Static Analyzer via scan-build), a sanitizer-instrumented build and test run (ASan, UBSan, TSan in separate runs because their instrumentation is not fully composable), a coverage gate that fails the build below a configured threshold, a mutation testing run (at least for the highest-risk modules, since mutation testing is compute-intensive), and a fuzzing regression corpus replay (AFL++ or libFuzzer corpus entries from prior fuzzing campaigns run as deterministic regression tests in CI, with new fuzzing campaigns run on a separate long-duration schedule).

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on: [push, pull_request]

jobs:
  static-analysis:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Install tools
        run: |
          sudo apt-get update
          sudo apt-get install -y clang clang-tidy cppcheck \
            lcov libasan6 llvm

      - name: Configure (compile_commands for clang-tidy)
        run: |
          cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
                -DCMAKE_C_COMPILER=clang \
                -DCMAKE_BUILD_TYPE=Debug

      - name: clang-tidy
        run: |
          run-clang-tidy -p build -header-filter='src/.*' \
            -checks='clang-analyzer-*,bugprone-*,cert-*,performance-*' \
            $(find src -name '*.c')

      - name: cppcheck
        run: |
          cppcheck --enable=all --error-exitcode=1 \
            --suppress=missingIncludeSystem \
            --inline-suppr \
            -I include src/

  asan-ubsan:
    runs-on: ubuntu-24.04
    needs: static-analysis
    steps:
      - uses: actions/checkout@v4

      - name: Install tools
        run: sudo apt-get update && sudo apt-get install -y clang lcov llvm

      - name: Build with ASan + UBSan + coverage
        run: |
          cmake -B build_asan \
            -DCMAKE_C_COMPILER=clang \
            -DCMAKE_BUILD_TYPE=Debug \
            -DCMAKE_C_FLAGS="-O1 -g -fsanitize=address,undefined \
                              --coverage -fprofile-arcs -ftest-coverage" \
            -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined --coverage"

          cmake --build build_asan --parallel $(nproc)

      - name: Run test suite
        env:
          ASAN_OPTIONS: "halt_on_error=1:detect_leaks=1"
          UBSAN_OPTIONS: "halt_on_error=1:print_stacktrace=1"
        run: |
          cd build_asan
          ctest --output-on-failure --parallel $(nproc)

      - name: Generate coverage report
        run: |
          lcov --capture --directory build_asan \
               --output-file coverage.info \
               --exclude '/usr/include/*' \
               --exclude '*/test/*'
          lcov --list coverage.info

      - name: Enforce coverage threshold (85% branch)
        run: |
          BRANCH_COV=$(lcov --summary coverage.info 2>&1 \
            | grep "branches" | grep -oP '[0-9]+\.[0-9]+(?=%)' | head -1)
          echo "Branch coverage: ${BRANCH_COV}%"
          python3 -c "
          import sys
          cov = float('${BRANCH_COV}')
          if cov < 85.0:
              print(f'FAIL: branch coverage {cov:.1f}% < 85.0% threshold')
              sys.exit(1)
          print(f'PASS: branch coverage {cov:.1f}%')
          "

  tsan:
    runs-on: ubuntu-24.04
    needs: static-analysis
    steps:
      - uses: actions/checkout@v4

      - name: Install tools
        run: sudo apt-get update && sudo apt-get install -y clang

      - name: Build with TSan
        run: |
          cmake -B build_tsan \
            -DCMAKE_C_COMPILER=clang \
            -DCMAKE_BUILD_TYPE=Debug \
            -DCMAKE_C_FLAGS="-O1 -g -fsanitize=thread" \
            -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread"

          cmake --build build_tsan --parallel $(nproc)

      - name: Run threaded tests
        env:
          TSAN_OPTIONS: "halt_on_error=1:second_deadlock_stack=1"
        run: |
          cd build_tsan
          ctest --output-on-failure --parallel 1 -L threaded

  fuzz-corpus-regression:
    runs-on: ubuntu-24.04
    needs: asan-ubsan
    steps:
      - uses: actions/checkout@v4

      - name: Install tools
        run: sudo apt-get update && sudo apt-get install -y clang

      - name: Build fuzz target
        run: |
          clang -O1 -g \
            -fsanitize=address,fuzzer \
            -o fuzz_parser \
            src/parser.c fuzz/fuzz_parser.c

      - name: Replay corpus
        run: |
          # Replay previously discovered corpus entries as deterministic
          # regression tests — no new fuzzing, just confirming old finds
          # are fixed and don't regress.
          ./fuzz_parser -runs=0 fuzz/corpus/ fuzz/crashes_fixed/
```

This pipeline encodes the full theoretical framework of this lesson in automated form. Static analysis catches faults before execution (the error–fault chain at its earliest intervention point). Sanitizer builds create the oracle apparatus that makes failures observable for the classes of defect most common in systems code. The coverage gate enforces the pesticide paradox mitigation by preventing coverage regression over time. The TSan job specifically targets the concurrency defect class that sanitizer oracle coverage would otherwise miss. The fuzz corpus regression ensures that past failures — faults that produced observed failures and were fixed — cannot silently regress when the codebase changes. Each component of the pipeline traces directly back to a specific theoretical principle from the first section of this lesson, and that is precisely the point: QA theory divorced from tooling is commentary, and tooling divorced from theory is cargo-culting. The discipline is in holding both together.
