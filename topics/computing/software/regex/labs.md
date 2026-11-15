# Operational Verification Labs: Regex

## Objective & Toolchain Setup

Regular expression engines constitute finite automata implementations that transform declarative pattern specifications into executable state machines operating on character streams. This laboratory sequence dissects regex engine internals through compiler intermediate representations, runtime performance profiling under catastrophic backtracking conditions, and memory safety verification of raw pointer manipulation in zero-copy parsing implementations. You will construct a minimal NFA-based regex engine in Rust, benchmark it against production implementations using CPU performance counters, and instrument it with AddressSanitizer to detect buffer overruns in character class matching. The exercises ground abstract automata theory in concrete x86-64 assembly, cache line behavior, and LLVM optimization passes.

The verification workflow requires a complete systems programming toolchain. Install Rust's stable and nightly channels through rustup to access both cargo-bench for criterion-based microbenchmarking and cargo-miri for abstract interpretation of unsafe code. The LLVM toolchain provides llvm-mca for static instruction throughput analysis and opt for viewing intermediate representations. Clang with AddressSanitizer support enables detection of spatial memory safety violations that manifest only under specific input patterns. Valgrind's Cachegrind tool profiles L1/L2/L3 cache misses during backtracking explosions, revealing performance cliffs invisible to wall-clock timers. Finally, perf on Linux exposes CPU performance monitoring counters for branch misprediction rates and instruction retirement throughput.

Begin by establishing the Rust environment. Execute `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` to install rustup if not already present, then run `rustup install nightly` to acquire the nightly toolchain required for Miri and unstable profiling features. Install LLVM tools with your system package manager: on Debian-based distributions run `apt-get install llvm clang valgrind linux-tools-generic`, on Fedora use `dnf install llvm clang valgrind perf`, and on macOS execute `brew install llvm valgrind`. Verify the installation by running `cargo --version`, `clang --version`, `lldb --version`, and `valgrind --version`. Create a workspace directory and initialize a new Rust project with `cargo new --lib regex-lab && cd regex-lab`. Add criterion for benchmarking and proptest for property-based fuzzing by appending to Cargo.toml:

```toml
[dependencies]
regex = "1.10"

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
proptest = "1.4"

[[bench]]
name = "regex_bench"
harness = false
```

This configuration establishes criterion as the benchmarking harness with HTML report generation enabled, allowing visualization of throughput distributions and performance regressions across regex pattern classes. The proptest dependency enables generation of adversarial input strings that trigger worst-case backtracking behavior in naive implementations.

## Exercise 1: AST, IR & Disassembly Analysis

Regex engines transform textual patterns into executable state machines through a multi-stage compilation pipeline. The frontend parser constructs an abstract syntax tree representing the regex's hierarchical structure of concatenation, alternation, and quantification operators. An intermediate lowering pass converts this AST into either a nondeterministic finite automaton with epsilon transitions or a bytecode instruction stream for a virtual machine. The backend then compiles these representations into native machine code or interprets them through a dispatch loop. This exercise constructs a minimal NFA-based matcher, emits LLVM IR to examine optimization passes, and disassembles the final x86-64 code to correlate high-level regex semantics with instruction-level execution.

Implement a Thompson NFA construction algorithm that translates regex patterns into state graphs with explicit epsilon transitions. Create `src/nfa.rs` with the following complete implementation:

```rust
use std::collections::{HashMap, HashSet, VecDeque};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct StateId(usize);

#[derive(Debug, Clone)]
pub enum Transition {
    Epsilon,
    Char(char),
    Range(char, char),
}

#[derive(Debug)]
pub struct NFA {
    states: Vec<State>,
    start: StateId,
    accept: StateId,
}

#[derive(Debug, Clone)]
struct State {
    transitions: Vec<(Transition, StateId)>,
}

impl NFA {
    pub fn new() -> Self {
        let start = State { transitions: vec![] };
        let accept = State { transitions: vec![] };
        Self {
            states: vec![start, accept],
            start: StateId(0),
            accept: StateId(1),
        }
    }

    fn add_state(&mut self) -> StateId {
        let id = StateId(self.states.len());
        self.states.push(State { transitions: vec![] });
        id
    }

    fn add_transition(&mut self, from: StateId, trans: Transition, to: StateId) {
        self.states[from.0].transitions.push((trans, to));
    }

    pub fn from_char(c: char) -> Self {
        let mut nfa = Self::new();
        nfa.add_transition(nfa.start, Transition::Char(c), nfa.accept);
        nfa
    }

    pub fn from_range(start: char, end: char) -> Self {
        let mut nfa = Self::new();
        nfa.add_transition(nfa.start, Transition::Range(start, end), nfa.accept);
        nfa
    }

    pub fn concatenate(mut first: Self, mut second: Self) -> Self {
        let offset = first.states.len();
        for state in &mut second.states {
            for (_, target) in &mut state.transitions {
                target.0 += offset;
            }
        }
        first.add_transition(first.accept, Transition::Epsilon, StateId(offset + second.start.0));
        first.states.extend(second.states);
        first.accept = StateId(offset + second.accept.0);
        first
    }

    pub fn alternate(mut first: Self, mut second: Self) -> Self {
        let mut nfa = Self::new();
        let new_start = nfa.start;
        let new_accept = nfa.accept;
        
        let offset = nfa.states.len();
        for state in &mut first.states {
            for (_, target) in &mut state.transitions {
                target.0 += offset;
            }
        }
        nfa.states.extend(first.states);
        let first_start = StateId(offset + first.start.0);
        let first_accept = StateId(offset + first.accept.0);

        let offset = nfa.states.len();
        for state in &mut second.states {
            for (_, target) in &mut state.transitions {
                target.0 += offset;
            }
        }
        nfa.states.extend(second.states);
        let second_start = StateId(offset + second.start.0);
        let second_accept = StateId(offset + second.accept.0);

        nfa.add_transition(new_start, Transition::Epsilon, first_start);
        nfa.add_transition(new_start, Transition::Epsilon, second_start);
        nfa.add_transition(first_accept, Transition::Epsilon, new_accept);
        nfa.add_transition(second_accept, Transition::Epsilon, new_accept);

        nfa
    }

    pub fn star(mut inner: Self) -> Self {
        let mut nfa = Self::new();
        let new_start = nfa.start;
        let new_accept = nfa.accept;

        let offset = nfa.states.len();
        for state in &mut inner.states {
            for (_, target) in &mut state.transitions {
                target.0 += offset;
            }
        }
        nfa.states.extend(inner.states);
        let inner_start = StateId(offset + inner.start.0);
        let inner_accept = StateId(offset + inner.accept.0);

        nfa.add_transition(new_start, Transition::Epsilon, inner_start);
        nfa.add_transition(new_start, Transition::Epsilon, new_accept);
        nfa.add_transition(inner_accept, Transition::Epsilon, inner_start);
        nfa.add_transition(inner_accept, Transition::Epsilon, new_accept);

        nfa
    }

    fn epsilon_closure(&self, states: &HashSet<StateId>) -> HashSet<StateId> {
        let mut closure = states.clone();
        let mut queue: VecDeque<StateId> = states.iter().copied().collect();

        while let Some(state) = queue.pop_front() {
            for (trans, target) in &self.states[state.0].transitions {
                if matches!(trans, Transition::Epsilon) && closure.insert(*target) {
                    queue.push_back(*target);
                }
            }
        }

        closure
    }

    pub fn matches(&self, input: &str) -> bool {
        let mut current_states = HashSet::new();
        current_states.insert(self.start);
        current_states = self.epsilon_closure(&current_states);

        for ch in input.chars() {
            let mut next_states = HashSet::new();
            for state in &current_states {
                for (trans, target) in &self.states[state.0].transitions {
                    let matches = match trans {
                        Transition::Char(c) => *c == ch,
                        Transition::Range(start, end) => ch >= *start && ch <= *end,
                        Transition::Epsilon => false,
                    };
                    if matches {
                        next_states.insert(*target);
                    }
                }
            }
            current_states = self.epsilon_closure(&next_states);
        }

        current_states.contains(&self.accept)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_single_char() {
        let nfa = NFA::from_char('a');
        assert!(nfa.matches("a"));
        assert!(!nfa.matches("b"));
        assert!(!nfa.matches("aa"));
    }

    #[test]
    fn test_concatenation() {
        let a = NFA::from_char('a');
        let b = NFA::from_char('b');
        let ab = NFA::concatenate(a, b);
        assert!(ab.matches("ab"));
        assert!(!ab.matches("a"));
        assert!(!ab.matches("ba"));
    }

    #[test]
    fn test_alternation() {
        let a = NFA::from_char('a');
        let b = NFA::from_char('b');
        let a_or_b = NFA::alternate(a, b);
        assert!(a_or_b.matches("a"));
        assert!(a_or_b.matches("b"));
        assert!(!a_or_b.matches("c"));
    }

    #[test]
    fn test_star() {
        let a = NFA::from_char('a');
        let a_star = NFA::star(a);
        assert!(a_star.matches(""));
        assert!(a_star.matches("a"));
        assert!(a_star.matches("aaa"));
        assert!(!a_star.matches("b"));
    }

    #[test]
    fn test_range() {
        let digit = NFA::from_range('0', '9');
        assert!(digit.matches("5"));
        assert!(!digit.matches("a"));
    }
}
```

This implementation materializes Thompson's construction as explicit Rust data structures. Each NFA state maintains a vector of outgoing transitions labeled with either epsilon, single characters, or character ranges. The constructor functions build NFAs bottom-up through structural recursion over the regex abstract syntax tree. The concatenate operation merges two NFAs by adding an epsilon transition from the first's accept state to the second's start state, then adjusting all state identifiers in the second NFA to account for the offset. Alternation creates a new start state with epsilon transitions to both sub-NFAs and a new accept state receiving epsilon transitions from both sub-accepts. The Kleene star adds epsilon transitions creating a loop back to the start and a bypass directly to accept. The epsilon_closure function computes the transitive closure of epsilon transitions using breadth-first search, while matches simulates the NFA by maintaining the set of currently reachable states and advancing through the input character by character.

Examine the LLVM intermediate representation to understand how Rust's ownership system and abstraction layers compile down to register allocation and memory operations. Build the library in release mode with debug symbols preserved and emit LLVM IR by executing `RUSTFLAGS="--emit=llvm-ir -C debuginfo=2" cargo build --release --lib`. Navigate to `target/release/deps/` and identify the `.ll` file corresponding to regex_lab. Open this file and search for the `matches` function. You will observe LLVM's SSA form with explicit basic blocks, phi nodes for merging control flow, and getelementptr instructions for struct field access. The HashSet operations compile to calls into the standard library's hashbrown implementation, revealing the abstraction cost of high-level collections. Note how the Transition enum discriminant checks translate to switch statements with jump tables, and observe that the epsilon closure loop materializes as a combination of vector push/pop operations and hash table insertions.

Generate native assembly to correlate regex semantics with x86-64 instructions. Execute `cargo rustc --release --lib -- --emit=asm` to produce assembly output, then locate the `.s` file in `target/release/deps/`. Search for the mangled name of the `matches` function using `grep -A 100 "regex_lab.*NFA.*matches" target/release/deps/*.s`. The assembly reveals the register allocation strategy: the current_states HashSet typically resides in heap memory accessed through a pointer in `rdi` or `rsi`, while the input string iterator state occupies registers like `rcx` and `rdx`. The inner character matching loop compiles to a sequence of `cmp` instructions comparing the input character against transition labels, followed by conditional jumps that implement the state transition logic. The epsilon closure BFS materializes as a tight loop with hash table probe sequences visible as load-compare-branch chains. Count the number of conditional branch instructions in the character matching hot path and correlate them with the number of outgoing transitions per state in your NFA construction.

Profile the instruction-level throughput using LLVM's machine code analyzer. Extract the assembly for the matches function into a standalone file `matches.s`, then analyze it with `llvm-mca -mcpu=skylake -timeline matches.s`. The tool reports instruction dispatch rates, execution port pressure, and critical path latency through the pipeline. For typical NFA matching code, you will observe high port 2/3 pressure from memory operations as the matcher probes the transition table and the HashSet backing array. Branch instructions create bubbles in the pipeline when predictions fail, especially during alternation handling where control flow depends on runtime input. The timeline view shows instruction-level parallelism opportunities: independent hash table probes and character comparisons can execute out-of-order on separate ports. Record the estimated cycles per iteration of the character matching loop and the bottleneck resource identified by llvm-mca.

Validate the implementation with property-based testing to explore the input space systematically. Add to `src/nfa.rs`:

```rust
#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #[test]
        fn star_accepts_any_repetition(c in '[a-z]', n in 0usize..20) {
            let nfa = NFA::star(NFA::from_char(c));
            let input: String = std::iter::repeat(c).take(n).collect();
            assert!(nfa.matches(&input));
        }

        #[test]
        fn concat_preserves_order(c1 in '[a-z]', c2 in '[a-z]') {
            let nfa1 = NFA::from_char(c1);
            let nfa2 = NFA::from_char(c2);
            let concat = NFA::concatenate(nfa1, nfa2);
            let input = format!("{}{}", c1, c2);
            assert!(concat.matches(&input));
            if c1 != c2 {
                let reversed = format!("{}{}", c2, c1);
                assert!(!concat.matches(&reversed));
            }
        }

        #[test]
        fn alternate_accepts_either(c1 in '[a-z]', c2 in '[a-z]') {
            let nfa1 = NFA::from_char(c1);
            let nfa2 = NFA::from_char(c2);
            let alt = NFA::alternate(nfa1, nfa2);
            assert!(alt.matches(&c1.to_string()));
            assert!(alt.matches(&c2.to_string()));
        }
    }
}
```

Run `cargo test` to execute both unit tests and property-based tests. Proptest generates hundreds of randomized inputs satisfying the specified strategies, checking that the NFA construction invariants hold across the input space. Failed tests emit shrunk counterexamples that isolate minimal failing inputs, enabling rapid diagnosis of construction bugs.

## Exercise 2: Cache Miss & Throughput Profiling

Regex matching performance degrades catastrophically when backtracking algorithms encounter adversarial input patterns that trigger exponential time complexity. Even NFA-based engines suffer from cache miss penalties when the state set explodes during alternation-heavy patterns or when epsilon closures force repeated traversals of large state graphs. This exercise instruments a backtracking regex matcher with CPU performance counters to measure L1/L2/L3 cache miss rates, branch mispredictions, and instruction retirement throughput. You will construct patterns that stress different cache levels, use perf to expose the microarchitectural bottlenecks, and apply Valgrind's Cachegrind to attribute misses to specific functions and data structures.

Implement a recursive backtracking matcher that exhibits worst-case exponential behavior. Create `src/backtrack.rs`:

```rust
#[derive(Debug, Clone)]
pub enum Pattern {
    Char(char),
    Concat(Box<Pattern>, Box<Pattern>),
    Alternate(Box<Pattern>, Box<Pattern>),
    Star(Box<Pattern>),
}

impl Pattern {
    pub fn matches(&self, input: &str) -> bool {
        self.matches_at(input, 0).is_some()
    }

    fn matches_at(&self, input: &str, pos: usize) -> Option<usize> {
        match self {
            Pattern::Char(c) => {
                let chars: Vec<char> = input.chars().collect();
                if pos < chars.len() && chars[pos] == *c {
                    Some(pos + 1)
                } else {
                    None
                }
            }
            Pattern::Concat(first, second) => {
                let mid = first.matches_at(input, pos)?;
                second.matches_at(input, mid)
            }
            Pattern::Alternate(first, second) => {
                first.matches_at(input, pos).or_else(|| second.matches_at(input, pos))
            }
            Pattern::Star(inner) => {
                let mut current = pos;
                loop {
                    if let Some(next) = inner.matches_at(input, current) {
                        if next == current {
                            break;
                        }
                        current = next;
                    } else {
                        break;
                    }
                }
                Some(current)
            }
        }
    }
}

pub fn parse_simple(pattern: &str) -> Pattern {
    let chars: Vec<char> = pattern.chars().collect();
    parse_expr(&chars, &mut 0)
}

fn parse_expr(chars: &[char], pos: &mut usize) -> Pattern {
    let mut left = parse_term(chars, pos);
    while *pos < chars.len() && chars[*pos] == '|' {
        *pos += 1;
        let right = parse_term(chars, pos);
        left = Pattern::Alternate(Box::new(left), Box::new(right));
    }
    left
}

fn parse_term(chars: &[char], pos: &mut usize) -> Pattern {
    let mut factors = vec![parse_factor(chars, pos)];
    while *pos < chars.len() && chars[*pos] != '|' && chars[*pos] != ')' {
        factors.push(parse_factor(chars, pos));
    }
    factors.into_iter().reduce(|a, b| Pattern::Concat(Box::new(a), Box::new(b))).unwrap()
}

fn parse_factor(chars: &[char], pos: &mut usize) -> Pattern {
    let mut base = if chars[*pos] == '(' {
        *pos += 1;
        let inner = parse_expr(chars, pos);
        *pos += 1;
        inner
    } else {
        let c = chars[*pos];
        *pos += 1;
        Pattern::Char(c)
    };
    
    if *pos < chars.len() && chars[*pos] == '*' {
        *pos += 1;
        base = Pattern::Star(Box::new(base));
    }
    
    base
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_backtrack_simple() {
        let pat = parse_simple("ab");
        assert!(pat.matches("ab"));
        assert!(!pat.matches("ac"));
    }

    #[test]
    fn test_backtrack_alternate() {
        let pat = parse_simple("a|b");
        assert!(pat.matches("a"));
        assert!(pat.matches("b"));
    }

    #[test]
    fn test_backtrack_star() {
        let pat = parse_simple("a*");
        assert!(pat.matches(""));
        assert!(pat.matches("aaa"));
    }
}
```

This recursive descent parser constructs a pattern AST that the matches_at method traverses depth-first. The Alternate case attempts the first branch, and upon failure backtracks to try the second. The Star quantifier greedily consumes input until the inner pattern fails, creating nested recursion when patterns like `(a|b)*` encounter alternating characters. This implementation lacks memoization and will re-explore the same (pattern, position) pairs exponentially many times on adversarial inputs.

Construct a benchmark suite that exercises different cache pressure scenarios. Create `benches/regex_bench.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId, Throughput};
use regex_lab::backtrack::{Pattern, parse_simple};
use regex_lab::nfa::NFA;

fn bench_backtrack_pathological(c: &mut Criterion) {
    let mut group = c.benchmark_group("backtrack_pathological");
    
    for size in [10, 15, 20, 25].iter() {
        let pattern = format!("{}x", "a*".repeat(*size));
        let input = "a".repeat(*size);
        
        group.throughput(Throughput::Bytes(*size as u64));
        group.bench_with_input(BenchmarkId::new("exponential", size), size, |b, _| {
            let pat = parse_simple(&pattern);
            b.iter(|| {
                black_box(pat.matches(black_box(&input)));
            });
        });
    }
    group.finish();
}

fn bench_nfa_vs_backtrack(c: &mut Criterion) {
    let mut group = c.benchmark_group("nfa_vs_backtrack");
    let pattern = "a*a*a*b";
    let input = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaac";
    
    group.bench_function("backtrack", |b| {
        let pat = parse_simple(pattern);
        b.iter(|| {
            black_box(pat.matches(black_box(input)));
        });
    });
    
    group.bench_function("nfa", |b| {
        let a = NFA::from_char('a');
        let a_star1 = NFA::star(a.clone());
        let a_star2 = NFA::star(NFA::from_char('a'));
        let a_star3 = NFA::star(NFA::from_char('a'));
        let b = NFA::from_char('b');
        let nfa = NFA::concatenate(
            NFA::concatenate(
                NFA::concatenate(a_star1, a_star2),
                a_star3
            ),
            b
        );
        b.iter(|| {
            black_box(nfa.matches(black_box(input)));
        });
    });
    
    group.finish();
}

fn bench_alternation_depth(c: &mut Criterion) {
    let mut group = c.benchmark_group("alternation_depth");
    
    for depth in [2, 4, 8, 16].iter() {
        let pattern: String = (0..*depth).map(|i| format!("a{}", i)).collect::<Vec<_>>().join("|");
        let input = format!("a{}", depth - 1);
        
        group.bench_with_input(BenchmarkId::new("backtrack", depth), depth, |b, _| {
            let pat = parse_simple(&pattern);
            b.iter(|| {
                black_box(pat.matches(black_box(&input)));
            });
        });
    }
    group.finish();
}

criterion_group!(benches, bench_backtrack_pathological, bench_nfa_vs_backtrack, bench_alternation_depth);
criterion_main!(benches);
```

Execute the benchmarks with `cargo bench` to establish baseline throughput measurements. Criterion generates HTML reports in `target/criterion/` showing throughput distributions and regression analysis across runs. The pathological backtracking benchmark reveals exponential scaling as input size increases: processing 25 characters may take seconds while 10 characters complete in microseconds. The NFA comparison demonstrates linear scaling independent of input length when the pattern fails to match.

Profile the backtracking implementation with Linux perf to expose cache miss behavior. Build the benchmark binary with `cargo bench --no-run` to produce an executable without running tests, then locate it in `target/release/deps/`. Run perf with cache event sampling: `perf stat -e cycles,instructions,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses ./target/release/deps/regex_bench-* --bench --profile-time=10 bench_backtrack_pathological`. The output reports L1 data cache load misses as a percentage of total loads, typically 5-15% for the recursive backtracking code as it thrashes the call stack and pattern AST pointers across cache lines. Last-level cache misses indicate pressure on L3 and main memory, usually below 1% for small patterns but rising to 10-20% when alternation creates large state spaces. The instructions per cycle metric drops below 1.0 during backtracking explosions, indicating pipeline stalls from branch mispredictions and memory latency.

Use Valgrind's Cachegrind tool to attribute cache misses to specific functions and data structures. Execute `valgrind --tool=cachegrind --cache-sim=yes ./target/release/deps/regex_bench-* --bench bench_backtrack_pathological/exponential/20` to simulate L1, L2, and L3 cache behavior and generate a detailed miss report in `cachegrind.out.<pid>`. Annotate the source code with miss counts using `cg_annotate cachegrind.out.<pid> src/backtrack.rs`. The output shows instruction fetch misses, data read misses, and data write misses per source line. The matches_at function accumulates the highest data read miss counts as it dereferences the Pattern enum and traverses boxed children. The Vec allocation in the Char pattern case generates write misses as it initializes heap memory for the character vector. The Alternate case shows elevated instruction misses as the recursive calls fragment the instruction stream across cache lines.

Generate flamegraphs to visualize the call stack time distribution during pathological backtracking. Install cargo-flamegraph with `cargo install flamegraph`, then run `cargo flamegraph --bench --bench-bin regex_bench-* -- --bench bench_backtrack_pathological/exponential/25`. This produces an interactive SVG showing the call tree with widths proportional to CPU time. The graph reveals that matches_at dominates execution time with self-time concentrated in the Alternate branch where backtracking occurs. Nested within matches_at you observe repeated stack frames as the recursion depth increases, with the deepest frames corresponding to exhaustive exploration of alternation possibilities. The flamegraph exposes that 90% of cycles occur within the pattern matching logic while less than 5% reside in allocation or string manipulation.

Compare the NFA implementation's cache behavior under the same workload. Run `valgrind --tool=cachegrind ./target/release/deps/regex_bench-* --bench nfa_vs_backtrack/nfa` and examine the annotated output. The NFA matcher exhibits higher L1 hit rates (95-98%) because it maintains a compact HashSet of states and iterates linearly through input characters without recursion. Data read misses concentrate in the HashSet probe sequences and the epsilon closure BFS queue operations. The lack of deep call stacks eliminates instruction cache thrashing, resulting in 3-5x higher instructions per cycle compared to backtracking. Last-level cache misses remain under 1% even for large patterns because the NFA state graph fits entirely in L3.

Measure branch prediction accuracy to correlate with control flow complexity. Execute `perf stat -e branches,branch-misses ./target/release/deps/regex_bench-* --bench bench_alternation_depth/backtrack/16`. The backtracking implementation suffers 15-25% branch misprediction rates in the alternation case because the or_else combinator creates data-dependent control flow that defeats the CPU's pattern-based predictor. The NFA matcher achieves under 5% mispredictions because its tight character matching loop executes predictably with consistent iteration counts.

## Exercise 3: Data Race Stress Testing & Leak Sanitizer Diagnostics

Concurrent regex matching requires thread-safe state management and careful synchronization around shared transition tables and compiled pattern caches. Unsafe implementations that share mutable state across threads trigger data races detectable by ThreadSanitizer. Memory leaks arise when regex engines allocate pattern ASTs or compiled state machines without corresponding deallocations. This exercise constructs a concurrent regex cache with intentional race conditions, instruments it with ThreadSanitizer to isolate unsynchronized accesses, and applies Valgrind's Memcheck and Rust's leak sanitizer to detect memory leaks in pattern compilation. You will observe how subtle pointer aliasing in unsafe code defeats Rust's ownership system and requires dynamic analysis to uncover.

Implement a naive thread-unsafe pattern cache that multiple threads access concurrently. Create `src/cache.rs`:

```rust
use std::collections::HashMap;
use std::sync::Arc;
use std::thread;
use crate::nfa::NFA;

pub struct PatternCache {
    cache: HashMap<String, Arc<NFA>>,
}

impl PatternCache {
    pub fn new() -> Self {
        Self {
            cache: HashMap::new(),
        }
    }

    pub fn get_or_compile(&mut self, pattern: &str) -> Arc<NFA> {
        if let Some(nfa) = self.cache.get(pattern) {
            return Arc::clone(nfa);
        }
        
        let nfa = Arc::new(Self::compile_pattern(pattern));
        self.cache.insert(pattern.to_string(), Arc::clone(&nfa));
        nfa
    }

    fn compile_pattern(pattern: &str) -> NFA {
        let chars: Vec<char> = pattern.chars().collect();
        if chars.is_empty() {
            return NFA::new();
        }
        
        chars.into_iter()
            .map(|c| NFA::from_char(c))
            .reduce(|a, b| NFA::concatenate(a, b))
            .unwrap()
    }
}

pub fn stress_test_cache(num_threads: usize, iterations: usize) {
    let cache_ptr = Box::into_raw(Box::new(PatternCache::new()));
    
    let handles: Vec<_> = (0..num_threads)
        .map(|_| {
            thread::spawn(move || {
                let cache = unsafe { &mut *cache_ptr };
                for i in 0..iterations {
                    let pattern = format!("test{}", i % 10);
                    let nfa = cache.get_or_compile(&pattern);
                    let input = format!("test{}", i % 10);
                    let _ = nfa.matches(&input);
                }
            })
        })
        .collect();
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    unsafe {
        let _ = Box::from_raw(cache_ptr);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cache_basic() {
        let mut cache = PatternCache::new();
        let nfa1 = cache.get_or_compile("abc");
        let nfa2 = cache.get_or_compile("abc");
        assert!(Arc::ptr_eq(&nfa1, &nfa2));
    }

    #[test]
    #[ignore]
    fn test_concurrent_access() {
        stress_test_cache(4, 100);
    }
}
```

This cache implementation intentionally violates thread safety by exposing a raw mutable pointer to multiple threads without synchronization. The HashMap accesses race as threads simultaneously read the cache map during lookups while other threads insert new entries. The unsafe block defeats Rust's borrow checker, making this code compile despite the inherent data race.

Detect the data race using ThreadSanitizer. Build the test binary with TSan instrumentation: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu test_concurrent_access`. ThreadSanitizer instruments all memory accesses and synchronization operations at runtime, maintaining shadow state to track happens-before relationships. When the test executes, TSan detects the race and emits a report:

```
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 8 at 0x7b0400000000 by thread T2:
    #0 hashbrown::raw::RawTable::insert
    #1 std::collections::HashMap::insert
    #2 regex_lab::cache::PatternCache::get_or_compile
    
  Previous read of size 8 at 0x7b0400000000 by thread T1:
    #0 hashbrown::raw::RawTable::find
    #1 std::collections::HashMap::get
    #2 regex_lab::cache::PatternCache::get_or_compile
```

The report identifies the conflicting accesses with call stacks showing that thread T2 writes to the HashMap's internal table while thread T1 reads from it. The memory address corresponds to the HashMap's bucket array. TSan confirms that no synchronization operation orders these accesses, establishing the race.

Correct the cache using mutex-based synchronization. Replace the cache field type with `Arc<Mutex<HashMap<String, Arc<NFA>>>>` and refactor get_or_compile to acquire the lock before accessing the map:

```rust
use std::sync::{Arc, Mutex};

pub struct PatternCache {
    cache: Arc<Mutex<HashMap<String, Arc<NFA>>>>,
}

impl PatternCache {
    pub fn new() -> Self {
        Self {
            cache: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn get_or_compile(&self, pattern: &str) -> Arc<NFA> {
        let mut cache = self.cache.lock().unwrap();
        if let Some(nfa) = cache.get(pattern) {
            return Arc::clone(nfa);
        }
        
        let nfa = Arc::new(Self::compile_pattern(pattern));
        cache.insert(pattern.to_string(), Arc::clone(&nfa));
        nfa
    }

    fn compile_pattern(pattern: &str) -> NFA {
        let chars: Vec<char> = pattern.chars().collect();
        if chars.is_empty() {
            return NFA::new();
        }
        
        chars.into_iter()
            .map(|c| NFA::from_char(c))
            .reduce(|a, b| NFA::concatenate(a, b))
            .unwrap()
    }
}

impl Clone for PatternCache {
    fn clone(&self) -> Self {
        Self {
            cache: Arc::clone(&self.cache),
        }
    }
}

pub fn stress_test_cache_safe(num_threads: usize, iterations: usize) {
    let cache = PatternCache::new();
    
    let handles: Vec<_> = (0..num_threads)
        .map(|_| {
            let cache = cache.clone();
            thread::spawn(move || {
                for i in 0..iterations {
                    let pattern = format!("test{}", i % 10);
                    let nfa = cache.get_or_compile(&pattern);
                    let input = format!("test{}", i % 10);
                    let _ = nfa.matches(&input);
                }
            })
        })
        .collect();
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

Rebuild and run with TSan: `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu test_concurrent_access`. ThreadSanitizer reports no races because the Mutex::lock call establishes a happens-before edge between the unlock in one thread and the subsequent lock in another.

Introduce a memory leak by failing to deallocate compiled patterns in specific error paths. Modify compile_pattern to allocate patterns on the heap without proper cleanup:

```rust
fn compile_pattern_leaky(pattern: &str) -> NFA {
    let chars: Vec<char> = pattern.chars().collect();
    if chars.is_empty() {
        let nfa = Box::new(NFA::new());
        return *Box::leak(nfa);
    }
    
    let nfa = chars.into_iter()
        .map(|c| NFA::from_char(c))
        .reduce(|a, b| NFA::concatenate(a, b))
        .unwrap();
    
    let boxed = Box::new(nfa);
    if pattern.contains("leak") {
        let leaked = Box::leak(boxed);
        return leaked.clone();
    }
    
    *boxed
}
```

Detect the leak using AddressSanitizer's leak detection. Build with LeakSanitizer enabled: `RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu -- --test-threads=1`. ASan tracks all heap allocations and reports unreachable memory at process exit. When the test terminates, LSan emits a report:

```
==12345==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 96 byte(s) in 1 object(s) allocated from:
    #0 0x7f1234567890 in __interceptor_malloc
    #1 0x7f1234567900 in alloc::alloc::alloc
    #2 0x7f1234567910 in alloc::boxed::Box::new
    #3 0x7f1234567920 in regex_lab::cache::PatternCache::compile_pattern_leaky
```

The report confirms that the Box::leak call prevents the NFA from being deallocated, leaving 96 bytes unreachable. The stack trace identifies the allocation site in compile_pattern_leaky.

Use Valgrind's Memcheck for comprehensive leak detection including reachable-but-not-freed memory. Run `valgrind --leak-check=full --show-leak-kinds=all ./target/debug/deps/regex_lab-* test_concurrent_access`. Memcheck categorizes leaks as definitely lost (no pointers remaining), indirectly lost (pointed to by other leaked memory), possibly lost (interior pointers exist), or still reachable (pointers remain but not freed). The output distinguishes intentional leaks like static allocations from genuine bugs:

```
==12345== HEAP SUMMARY:
==12345==     in use at exit: 96 bytes in 1 blocks
==12345==   total heap usage: 1,543 allocs, 1,542 frees, 125,432 bytes allocated
==12345== 
==12345== 96 bytes in 1 blocks are definitely lost in loss record 1 of 1
==12345==    at 0x4C2FB0F: malloc (in /usr/lib/valgrind/vgpreload_memcheck-amd64-linux.so)
==12345==    by 0x10A2C3: alloc::alloc::alloc (alloc.rs:98)
==12345==    by 0x10A2F1: regex_lab::cache::compile_pattern_leaky (cache.rs:45)
```

Memcheck confirms the leak originates from the Box::leak call in compile_pattern_leaky and that no remaining pointers reference the allocation.

Profile memory allocation behavior under load using Massif heap profiler. Execute `valgrind --tool=massif ./target/release/deps/regex_bench-* --bench bench_nfa_vs_backtrack` to record heap usage over time. Massif generates `massif.out.<pid>` containing snapshots of heap allocations at regular intervals. Visualize the profile with `ms_print massif.out.<pid>`, which shows peak memory usage and the call stacks responsible for the largest allocations. For the NFA matcher, peak usage corresponds to the HashSet state vector during epsilon closure explosions. The allocation timeline reveals spikes during pattern compilation followed by stable memory usage during matching as the NFA state is reused across inputs.

Verify memory safety invariants using Miri, Rust's interpreter for detecting undefined behavior. Run `cargo +nightly miri test` to execute the test suite under abstract interpretation. Miri detects violations like use-after-free, buffer overruns, and uninitialized reads by tracking pointer provenance and allocation validity. For the unsafe cache implementation, Miri reports undefined behavior when threads access the raw pointer concurrently without proper aliasing rules. Miri's diagnostic pinpoints the unsafe block and explains that the mutable reference violates Rust's aliasing guarantees even though the code compiles.

## Developer Cheat Sheet & Toolchain Checklist

### Compilation & IR Inspection Commands

| Task | Command | Notes |
|------|---------|-------|
| Emit LLVM IR with debug info | `RUSTFLAGS="--emit=llvm-ir -C debuginfo=2" cargo build --release --lib` | Outputs `.ll` files in `target/release/deps/` |
| Generate assembly | `cargo rustc --release --lib -- --emit=asm` | Produces `.s` files for architecture-specific inspection |
| Analyze instruction throughput | `llvm-mca -mcpu=skylake -timeline file.s` | Requires LLVM tools; reports port pressure and IPC estimates |
| View optimized IR passes | `opt -O3 -print-after-all input.ll -o output.bc 2>&1 \| less` | Shows transformation sequence through optimization pipeline |
| Disassemble to annotated assembly | `objdump -d -S -M intel target/release/libregex_lab.so` | Interleaves source lines with assembly when debuginfo present |

### Performance Profiling

| Task | Command | Notes |
|------|---------|-------|
| Microbenchmark with criterion | `cargo bench` | HTML reports in `target/criterion/` with regression analysis |
| Profile CPU cache behavior | `perf stat -e L1-dcache-load-misses,LLC-load-misses cargo bench` | Requires Linux with perf support and kernel.perf_event_paranoid ≤ 2 |
| Cache miss attribution | `valgrind --tool=cachegrind --cache-sim=yes ./binary` | Generates `cachegrind.out.<pid>` for per-line miss counts |
| Annotate source with cache misses | `cg_annotate cachegrind.out.<pid> src/file.rs` | Shows data/instruction misses per source line |
| Generate flamegraph | `cargo flamegraph --bench --bench-bin binary -- --bench pattern` | Produces interactive SVG of call tree CPU time |
| Measure branch mispredictions | `perf stat -e branches,branch-misses ./binary` | Reports misprediction rate as percentage of total branches |
| Profile heap allocations | `valgrind --tool=massif ./binary` | Creates `massif.out.<pid>`; visualize with `ms_print` |

### Sanitizer & Memory Safety

| Task | Command | Notes |
|------|---------|-------|
| Detect data races | `RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test --target x86_64-unknown-linux-gnu` | ThreadSanitizer tracks happens-before relations; requires nightly |
| Detect memory leaks | `RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu` | LeakSanitizer reports unreachable allocations at exit |
| Check undefined behavior | `cargo +nightly miri test` | Abstract interpreter for Rust; detects UB beyond what compiler catches |
| Comprehensive leak analysis | `valgrind --leak-check=full --show-leak-kinds=all ./binary` | Categorizes leaks as definite/indirect/possible/reachable |
| Profile memory operations | `valgrind --tool=memcheck --track-origins=yes ./binary` | Tracks uninitialized value propagation; slower but thorough |

### Regex-Specific Verification

| Task | Command | Purpose |
|------|---------|---------|
| Property-based fuzzing | `cargo test --release` | Proptest generates adversarial inputs automatically |
| Verify NFA correctness | `cargo test --lib nfa::tests` | Unit tests for Thompson construction invariants |
| Stress concurrent cache | `cargo test cache::tests::test_concurrent_access -- --ignored` | Exposes data races in unsynchronized shared state |
| Benchmark exponential backtracking | `cargo bench backtrack_pathological` | Measures scaling behavior under adversarial patterns |
| Compare NFA vs backtracking | `cargo bench nfa_vs_backtrack` | Quantifies linear vs exponential time complexity |

### Common Pitfalls & Solutions

**ThreadSanitizer reports false positives with println! macros:** TSan instruments standard library IO operations, which use internal locks that appear as races. Suppress with `TSAN_OPTIONS="suppressions=tsan.supp"` and a suppression file containing `race:std::io::stdio::print`.

**Cachegrind output overwhelmed by allocator noise:** Filter to application code with `cg_annotate --auto=no cachegrind.out.<pid> src/`. The `--auto=no` flag excludes standard library and allocator annotations.

**Miri fails with unsupported platform-specific code:** Miri cannot interpret FFI or inline assembly. Isolate unsafe blocks in separate modules and test safe wrappers under Miri while using integration tests for full validation.

**Criterion benchmarks vary >20% between runs:** Disable CPU frequency scaling with `sudo cpupower frequency-set --governor performance`. Ensure the system is idle and run `cargo bench` multiple times to establish confidence intervals.

**Valgrind reports leaks from Rust's thread_local!:** Thread-local storage allocations appear as reachable but not freed. These are intentional and should be ignored. Focus on definitely lost or indirectly lost categories.

### Optimization Workflow

1. Establish baseline performance with `cargo bench`, recording throughput and latency distributions.
2. Profile with `perf stat` to identify high-level bottlenecks: cache misses, branch mispredictions, or IPC below 1.0.
3. Generate flamegraph to locate hot functions consuming majority of CPU time.
4. Use Cachegrind to attribute cache misses to specific data structures and access patterns.
5. Examine LLVM IR and assembly to verify expected optimizations: loop unrolling, inlining, vectorization.
6. Apply targeted changes: prefetch hints, data structure compaction, branch elimination.
7. Re-benchmark to quantify improvement and ensure no performance regressions in other scenarios.
8. Run full sanitizer suite to verify safety invariants remain intact after unsafe optimizations.

This workflow grounds optimization decisions in empirical measurements rather than intuition, ensuring that changes address actual bottlenecks and preserve correctness guarantees.
