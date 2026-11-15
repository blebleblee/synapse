# Lesson 2: Type Systems, Formal Semantics, Program Correctness

## 1. First-Principles Intuition & Invariants

A type system is not merely a syntactic discipline preventing the addition of a string to an integer; it is a formal proof system embedded in the compiler. Through the Curry-Howard correspondence, types correspond to logical propositions, and programs correspond to proofs. When a compiler accepts a well-typed program, it is effectively verifying a mathematical proof that certain kinds of undefined behavior—memory corruption, invalid state transitions, dereferencing null pointers—are impossible within the execution of that program. This is the foundational invariant of static typing: shifting the burden of correctness from runtime observation to compile-time proof.

The dichotomy between static and dynamic typing is frequently misrepresented as an ideological conflict. In mechanical terms, it is a scheduling decision regarding when invariants are enforced. Static typing enforces invariants at compile time by constructing a proof, rejecting programs that cannot be proven safe. Dynamic typing defers enforcement to runtime, injecting tag checks and dispatch logic into the execution path. Both approaches validate behavior, but static typing provides a stronger guarantee: if a program is well-typed and the type system is sound, the program cannot "go wrong" regardless of the input it receives. Dynamic typing, conversely, guarantees only that invalid operations will be caught and halted, often leaving the system in an unpredictable state before the halt occurs.

Type inference bridges the gap between mathematical rigor and human engineering effort. Rather than forcing the programmer to manually annotate every proof (type), inference algorithms like Hindley-Milner or Rust's bidirectional constraint-based solver deduce types by unifying constraints gathered from usage. The compiler infers the most general type that satisfies all constraints, allowing the programmer to write succinct code while retaining the full static safety guarantee.

To reason formally about program correctness, we require mathematical models of execution. Operational semantics defines execution as a sequence of state transitions, modeling the program as an abstract machine stepping through configurations. Denotational semantics, by contrast, maps programs directly to mathematical objects, defining the meaning of a program as a function from inputs to outputs. Operational semantics tells us *how* the machine computes; denotational semantics tells us *what* the computation means.

The reliability of a type system rests on the properties of soundness and type safety. A type system is sound if it satisfies two theorems: Progress and Preservation. Progress states that a well-typed term is either a value (fully evaluated) or can take a step (evaluate further); it is never "stuck" in an invalid state. Preservation states that if a well-typed term takes a step, the resulting term is also well-typed. Together, these theorems guarantee that a well-typed program will never attempt an invalid operation, such as interpreting an integer as a pointer. Modern systems programming languages like Rust elevate this to memory safety, where the type system's soundness guarantees the absence of use-after-free, double-free, and data races.

When basic types are insufficient to prove correctness, we turn to dependent types and Hoare logic. Dependent types allow types to depend on runtime values, enabling the compiler to verify, for instance, that a matrix multiplication function receives matrices with compatible dimensions. Hoare logic provides an axiomatic basis for imperative program verification, using triples $\{P\} C \{Q\}$ to assert that if precondition $P$ holds before command $C$ executes, postcondition $Q$ will hold afterward, assuming $C$ terminates. Loop invariants act as the critical bridge in this logic, asserting predicates that hold before and after every iteration, ensuring the postcondition is reached upon loop termination.

## 2. Core Architecture & Mechanics

The implementation of these formal concepts requires concrete compiler architectures. In Rust, the type system's ability to enforce protocol invariants is demonstrated through the type-state pattern, leveraging affine types and zero-sized marker types. By encoding the state of a resource into its type, the compiler makes illegal state transitions unrepresentable.

```rust
// A type-state pattern enforcing a compile-time protocol.
// Transitions consume the previous state, preventing reuse.

pub struct Uninitialized;
pub struct Initialized;
pub struct Running;
pub struct Stopped;

pub struct Device<State> {
    id: u32,
    _state: std::marker::PhantomData<State>,
}

impl Device<Uninitialized> {
    pub fn new(id: u32) -> Self {
        Device { id, _state: std::marker::PhantomData }
    }
    pub fn initialize(self) -> Device<Initialized> {
        Device { id: self.id, _state: std::marker::PhantomData }
    }
}
impl Device<Initialized> {
    pub fn start(self) -> Device<Running> {
        Device { id: self.id, _state: std::marker::PhantomData }
    }
}
impl Device<Running> {
    pub fn stop(self) -> Device<Stopped> {
        Device { id: self.id, _state: std::marker::PhantomData }
    }
}

fn main() {
    let dev = Device::new(0);
    let dev = dev.initialize();
    let dev = dev.start();
    // dev.start(); // Compile error: method `start` not found for `Device<Running>`
    let dev = dev.stop();
    // dev.stop();  // Compile error: method `stop` not found for `Device<Stopped>`
}
```

Under the hood, the Rust compiler operationalizes these semantics through the Mid-level IR (MIR). MIR is a drastically simplified abstract machine representation. It models the program as a control-flow graph of basic blocks, where execution is defined by a small set of deterministic transition rules. The borrow checker operates directly on this MIR, performing an abstract interpretation to track the liveness, initializedness, and aliasing status of every memory location. This is operational semantics applied to compiler engineering: the borrow checker proves Preservation by ensuring that no transition violates the ownership invariants, and Progress by ensuring all memory accesses resolve to valid, initialized locations.

For more complex invariants involving values, Rust approximates dependent types via const generics. This allows the compiler to verify mathematical relationships between data structures at compile time, such as the dimensional compatibility of matrices.

```rust
// Compile-time verification of matrix dimension compatibility using const generics.
#[derive(Debug)]
pub struct Matrix<const ROWS: usize, const COLS: usize> {
    data: [[f64; COLS]; ROWS],
}

impl<const R: usize, const C: usize> Matrix<R, C> {
    pub fn new(data: [[f64; C]; R]) -> Self {
        Matrix { data }
    }
}

impl<const R: usize, const K: usize, const C: usize> std::ops::Mul<&Matrix<K, C>> for &Matrix<R, K> {
    type Output = Matrix<R, C>;
    fn mul(self, rhs: &Matrix<K, C>) -> Self::Output {
        let mut result = [[0.0f64; C]; R];
        for i in 0..R {
            for j in 0..C {
                for k in 0..K {
                    result[i][j] += self.data[i][k] * rhs.data[k][j];
                }
            }
        }
        Matrix::new(result)
    }
}

fn main() {
    let a: Matrix<2, 3> = Matrix::new([
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
    ]);
    let b: Matrix<3, 2> = Matrix::new([
        [7.0, 8.0],
        [9.0, 10.0],
        [11.0, 12.0],
    ]);
    let c: Matrix<2, 2> = &a * &b; // Compiles successfully
    
    // let d: Matrix<2, 2> = Matrix::new([[1.0, 2.0], [3.0, 4.0]]);
    // let e = &a * &d; // Compile error: expected Matrix<2, 2>, found Matrix<3, 2>
}
```

In C, where the type system is too weak to express these invariants, we rely on Hoare logic to structure our reasoning about memory operations. The following C code demonstrates a bounded memory copy. The preconditions specify non-null pointers, and the loop invariant asserts that the prefix copied so far remains valid. We use runtime assertions to enforce these contracts dynamically.

```c
#include <stdint.h>
#include <stddef.h>
#include <assert.h>

// Hoare Triple:
// Precondition: dst and src are valid, non-null pointers.
// Postcondition: dst[0..n] == src[0..n], returns dst.
void* bounded_copy(void* dst, const void* src, size_t n) {
    assert(dst != NULL);
    assert(src != NULL);
    
    uint8_t* d = (uint8_t*)dst;
    const uint8_t* s = (const uint8_t*)src;
    
    // Loop invariant: 0 <= i <= n, and dst[0..i] == src[0..i]
    for (size_t i = 0; i < n; ++i) {
        // Invariant holds at the start of the iteration
        d[i] = s[i];
        // Invariant re-established for i+1
    }
    
    // Postcondition check
    assert(n == 0 || d[n-1] == s[n-1]);
    return dst;
}

int main() {
    char src[] = "compile_time_proof";
    char dst[19];
    bounded_copy(dst, src, 19);
    assert(dst[18] == '\0');
    return 0;
}
```

## 3. High-Performance Optimization & Failure Modes

The soundness of a type system is bounded by the halting problem. No sufficiently expressive type system can decide all properties of all programs. When the compiler's static analysis is insufficient to prove safety—such as when interacting with raw hardware, foreign function interfaces, or implementing custom data structures—Rust provides the `unsafe` escape hatch. `unsafe` does not disable the type system; it merely shifts the burden of proof from the compiler to the programmer, introducing a soundness hole that must be manually sealed.

The architectural pattern for managing this failure mode is strict encapsulation. The `unsafe` code is confined to a private module, and a safe public API is exposed that maintains the invariants the compiler cannot see. This localizes the danger and preserves soundness globally.

```rust
// A safe abstraction over unsafe pointer manipulation.
// Maintains the invariant that the internal pointer is never aliased mutably.
pub struct RawBuffer {
    ptr: *mut u8,
    len: usize,
    capacity: usize,
}

impl RawBuffer {
    pub fn new(capacity: usize) -> Self {
        let layout = std::alloc::Layout::array::<u8>(capacity).unwrap();
        let ptr = if capacity == 0 {
            std::ptr::null_mut()
        } else {
            // Safety: layout is valid and non-zero
            unsafe { std::alloc::alloc(layout) }
        };
        RawBuffer { ptr, len: 0, capacity }
    }

    // Safe API: encapsulates the unsafe write, enforcing bounds invariant
    pub fn push(&mut self, byte: u8) -> bool {
        if self.len >= self.capacity {
            return false;
        }
        // Safety: len < capacity guarantees ptr + len is valid
        unsafe {
            std::ptr::write(self.ptr.add(self.len), byte);
        }
        self.len += 1;
        true
    }
}

impl Drop for RawBuffer {
    fn drop(&mut self) {
        if self.capacity > 0 {
            let layout = std::alloc::Layout::array::<u8>(self.capacity).unwrap();
            // Safety: ptr was allocated with this layout
            unsafe { std::alloc::dealloc(self.ptr as *mut u8, layout) }
        }
    }
}

fn main() {
    let mut buf = RawBuffer::new(4);
    assert!(buf.push(10));
    assert!(buf.push(20));
    assert!(buf.push(30));
    assert!(buf.push(40));
    assert!(!buf.push(50)); // Returns false, capacity full, soundness preserved
}
```

Performance trade-offs manifest directly in how the type system implements polymorphism. Monomorphization, used by Rust's generics, generates a distinct copy of the code for every concrete type used. This produces highly optimized, statically dispatched machine code but risks code bloat, increasing binary size and instruction cache pressure. Dynamic dispatch, used by trait objects (`dyn Trait`), relies on vtables, embedding type information at runtime. This reduces binary size but introduces an indirection that defeats branch prediction and prevents inlining.

```rust
// Static Dispatch (Monomorphization): zero-cost, code duplicated per type
pub fn process_static<T: Behavior>(item: &T) {
    item.execute();
}

// Dynamic Dispatch (VTable): indirection, single code path
pub fn process_dynamic(item: &dyn Behavior) {
    item.execute();
}

pub trait Behavior {
    fn execute(&self);
}

struct FastImpl;
impl Behavior for FastImpl {
    fn execute(&self) { /* direct call */ }
}

fn main() {
    let fast = FastImpl;
    process_static(&fast);     // Compiles to direct call
    process_dynamic(&fast);    // Compiles to indirect call via vtable
}
```

Because static type systems cannot prove total correctness, runtime verification remains necessary. Fuzzing complements static types by dynamically validating the denotational semantics of a program against arbitrary inputs. It searches for panics—runtime invariant violations that the type system could not statically prevent. A typical fuzzing workflow in Rust uses `cargo-fuzz` to generate malformed inputs and monitor for crashes.

```bash
# Initialize a fuzz target in a Rust project
cargo add cargo-fuzz
cargo fuzz init
cargo fuzz add copy_fuzz
```

The fuzz target defines the invariant to be checked. If the assertion fails, the fuzzer has discovered an input that violates the program's correctness contract.

```rust
// fuzz_targets/copy_fuzz.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if data.len() < 2 { return; }
    let n = data.len() / 2;
    let src = &data[..n];
    let mut dst = vec![0u8; n];
    dst.copy_from_slice(src);
    // Denotational invariant: the destination must equal the source
    assert_eq!(src, dst.as_slice());
});
```

By integrating static proofs via the type system, strict encapsulation of unsound escape hatches, and dynamic fuzzing for boundary edge cases, the systems engineer constructs a layered defense against program incorrectness. This approach acknowledges the fundamental limits of formal verification while maximizing the mechanical guarantees available at compile time.
