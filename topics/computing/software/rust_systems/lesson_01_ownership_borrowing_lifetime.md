# Lesson 1: Ownership, Borrowing, and Lifetimes

## 1. First-Principles Intuition & Invariants

Every memory safety bug in systems software—use-after-free, double-free, data races, dangling pointers—traces back to a single failure: the program retained a reference to memory whose lifetime the runtime no longer guaranteed. C delegates this guarantee to the programmer's discipline. C++ introduces RAII and smart pointers to encode it structurally but still permits raw pointer escape. Garbage-collected languages reclaim memory automatically but pay in nondeterministic pause times, bounded throughput, and the surrender of manual control over deallocation timing. Rust proposes a different contract. It enforces memory safety at compile time through a static analysis called the borrow checker, which operates over three interlocking invariants: ownership, borrowing, and lifetimes. Together they form a type system discipline that proves, before the program ever runs, that no reference outlives the data it points to and that no two threads mutate the same memory without synchronization.

Ownership is the foundational axiom. Every value in Rust has exactly one owning variable, and when that variable goes out of scope, the value is dropped. Drop is deterministic: the compiler inserts a call to the `Drop::drop` trait method at the precise lexical point where the owner exits scope, and this call deallocates memory, closes file handles, and releases locks. There is no finalizer thread, no mark phase, no write barrier. The deallocation is synchronous with control flow. When an owner is moved—assigned to another variable, passed to a function, or returned—the ownership of the underlying resource transfers to the new location, and the old location is statically invalidated. Any subsequent use of the moved-from binding is a compile error. This is move semantics by default, and it eliminates double-free at the type level: you cannot free what you no longer own, and you cannot use what you have given away.

Borrowing relaxes ownership without copying. A borrow is a temporary, non-owning reference—a pointer with an attached lifetime that the compiler tracks through every control-flow path. The borrow checker enforces two rules. First, you may have either one mutable reference (`&mut T`) or any number of immutable references (`&T`) to the same data at the same time, never both. This is aliasing XOR mutability, and it is the mechanism by which Rust prevents data races without runtime locks. Second, every reference must not outlive the data it borrows. The compiler performs a constraint-solving pass over lifetime annotations—explicit or inferred—to prove that no reference's reach extends past its referent's drop point. Lifetimes are therefore not runtime constructs; they are compile-time variables over scopes, threaded through type signatures so that function and struct contracts propagate borrow validity across module boundaries.

The borrow checker has evolved substantially since Rust 1.0. The introduction of Non-Lexical Lifetimes (NLL) in Rust 2018 replaced the older lexical-scope-based analysis with one rooted in control-flow analysis. A reference now expires at its last use rather than at the closing brace of its enclosing block, which unblocks a large class of natural patterns that the lexical model rejected. The 2021 edition further refined this with closure disjoint capture, and ongoing work on Polonius aims to make the analysis more precise still. But the invariant is unchanged: the compiler rejects any program it cannot prove safe, and it does so with zero runtime cost.

## 2. Core Architecture & Mechanics

To understand how the compiler enforces these invariants, we must trace the borrow checker's internal model. At a conceptual level, the compiler maintains a constraint graph across every control-flow path. Each reference and each variable has a region (a set of program points at which it is live). The checker's job is to show that for every reference `r: &'a T`, the region of `r` is a subset of the region `'a`, and that the region `'a` does not overlap the drop point of the referent. If no such assignment of regions satisfies all constraints simultaneously, the program is rejected.

Consider the mechanics of a move. When you bind `let s1 = String::from("data");` and then `let s2 = s1;`, the compiler does not copy the `String`'s heap allocation. Instead it performs a bitwise move of the stack-allocated `String` struct—three words: a pointer to the heap buffer, a length, and a capacity—into `s2`'s slot and marks `s1` as moved. The MIR (Mid-level Intermediate Representation) for this sequence records `s1` as `DEAD` after the move statement, and any subsequent read of `s1` triggers error E0382. A `String` on the stack is a fixed-size struct: `{ ptr: *mut u8, len: usize, cap: usize }`. Moving it copies the three words but does not duplicate the heap allocation, so when `s2` is dropped, the heap frees exactly once.

```
Stack                           Heap
+-------------------+          +----+----+----+----+
| s1 (moved)        |    .---->| 'd'| 'a'| 't'| 'a'|
|  ptr: 0x... ----+--+        +----+----+----+----+
|  len: 4          |           cap: 4 (capacity)
|  cap: 4          |
+-------------------+
| s2 (owner)       |
|  ptr: 0x... -----+--------->^ (same allocation)
|  len: 4          |
|  cap: 4          |
+-------------------+
```

Borrowing introduces references whose validity the compiler threads through scope analysis. The canonical example:

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() {
        x
    } else {
        y
    }
}
```

The lifetime parameter `'a` declares a constraint: the returned reference lives at most as long as the shorter of the two input lifetimes. The compiler unifies `'a` with the call-site lifetimes of both `x` and `y` and then verifies that the returned reference is not used beyond that boundary. If the caller writes `let result = longest(&s1, &s2); drop(s1); println!("{}", result);`, the compiler detects that `result` borrows from `s1` and `s1` is dropped before `result`'s last use, producing error E0597.

The borrow rules become particularly precise around mutable borrows. A `&mut T` grants exclusive access: no other reference, mutable or immutable, may coexist in the same region. This is enforced by the borrow checker tracking the "loan" and its active region. Consider this realistic example that NLL unblocks but lexical lifetimes would reject:

```rust
let mut data = vec![1, 2, 3];
let first = &data[0];          // immutable borrow starts
println!("first element: {}", first);
data.push(4);                  // mutable borrow — OK under NLL
// first is no longer used here, so the immutable borrow expired
```

Under pre-NLL rules, the immutable borrow `first` would extend to the end of the block, colliding with the `push` call. NLL sees that `first` is last used at the `println!` and expires the borrow there, allowing the mutation. This is control-flow analysis, not lexical matching.

For structs containing references, lifetimes become part of the type. A struct holding a reference must declare its lifetime, and any instance of that struct is constrained to not outlive that lifetime:

```rust
struct Parser<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> Parser<'a> {
    fn new(input: &'a str) -> Self {
        Parser { input, position: 0 }
    }

    fn peek(&self) -> Option<char> {
        self.input[self.position..].chars().next()
    }

    fn advance(&mut self) {
        self.position += 1;
    }

    fn remaining(&self) -> &'a str {
        &self.input[self.position..]
    }
}
```

The `Parser` borrows the input string for lifetime `'a`. The compiler will reject any attempt to create a `Parser` that outlives the string it parses. This is proven statically—no reference count, no GC root scan.

Now consider the mechanics of interior mutability, which provides a controlled escape hatch from the aliasing XOR mutability rule. `Cell<T>` allows mutation through a shared reference by performing a bitwise copy on get and a bitwise replace on set, safe because `T: Copy` guarantees no aliasing of interior pointers. `RefCell<T>` moves the borrow check to runtime: `borrow()` and `borrow_mut()` increment and decrement a borrow counter, and violation (calling `borrow_mut` while a shared borrow is active) panics rather than corrupts. This is a deliberate trade-off: the type system cannot prove safety in all patterns, so `RefCell` defers to a runtime guard with zero-cost-if-not-violated semantics.

For thread-safe interior mutability, `Mutex<T>` and `RwLock<T>` provide the same borrow-dynamic discipline but through OS-level synchronization. The distinction is encoded in the `Send` and `Sync` marker traits. `RefCell<T>` is `Send` but not `Sync`: it cannot be shared between threads because its borrow counter is non-atomic. `Mutex<T>` is both `Send` and `Sync` (when `T: Send`) because the lock provides the synchronization the borrow counter requires. This is the deep connection between the type system and concurrency safety: `Send` marks types safe to move between threads, `Sync` marks types safe to share by reference between threads, and both are automatically derived by the compiler from the structural composition of fields, unless overridden by an unsafe impl.

The interaction of lifetimes and trait objects introduces a subtlety. A trait object `dyn Trait` has a default lifetime of `'static` when boxed, but borrowed trait objects (`&dyn Trait`) carry the lifetime of the reference. When a struct stores a `Box<dyn Trait>`, the trait object must be `'static` unless you parameterize: `Box<dyn Trait + 'a>`. This is essential in parser combinators, async runtimes, and plugin systems where you store heterogenous objects behind a vtable:

```rust
trait Source {
    fn next_token(&mut self) -> Option<Token>;
}

struct Lexer<'a> {
    source: Box<dyn Source + 'a>,
    buffer: String,
}

impl<'a> Lexer<'a> {
    fn from_reader(reader: &'a mut dyn std::io::Read) -> Self {
        // reader is borrowed for 'a; the trait object cannot outlive it
        Lexer {
            source: Box::new(ReaderSource { reader }),
            buffer: String::new(),
        }
    }
}

struct ReaderSource<'r> {
    reader: &'r mut dyn std::io::Read,
}

impl<'r> Source for ReaderSource<'r> {
    fn next_token(&mut self) -> Option<Token> {
        let mut byte = [0u8; 1];
        match self.reader.read(&mut byte) {
            Ok(0) => None,
            Ok(_) => Some(Token::Byte(byte[0])),
            Err(_) => None,
        }
    }
}
```

The lifetime `'r` on `ReaderSource` propagates through the trait object's `+ 'a` bound, ensuring the `Box<dyn Source + 'a>` cannot escape the borrow on the reader. If you omitted `+ 'a`, the compiler would default to `'static` and reject the construction because `&'r mut dyn Read` is not `'static`.

## 3. High-Performance Optimization & Failure Modes

The borrow checker is not merely a safety tool; it is a performance contract. Because the compiler proves that a `&mut T` is exclusive, it can elide aliasing-based memory barriers that C and C++ compilers must conservatively emit. In C, the `restrict` keyword provides a manual aliasing assertion that, if violated, is undefined behavior. In Rust, `&mut T` is `restrict` by type, proven by the compiler. This unlocks auto-vectorization and load reordering that LLVM would otherwise suppress.

To observe this concretely, compare two implementations of a loop that updates two slices. In C, without `restrict`, the compiler must assume `dst` and `src` might overlap (alias), forcing conservative loads. In Rust, the signature `fn transform(dst: &mut [f32], src: &[f32])` carries the exclusivity proof, and LLVM auto-vectorizes with no aliasing guards:

```rust
use std::arch::x86_64::*;

pub fn saxpy(dst: &mut [f32], src: &[f32], alpha: f32) {
    assert_eq!(dst.len(), src.len());
    let n = dst.len();
    let mut i = 0;

    // Scalar tail-safe loop; compiler auto-vectorizes under -O2/-C opt-level=3
    while i < n {
        dst[i] = alpha * src[i] + dst[i];
        i += 1;
    }
}

// Explicit SIMD for demonstration of the no-aliasing guarantee
#[target_feature(enable = "avx2")]
pub unsafe fn saxpy_avx2(dst: &mut [f32], src: &[f32], alpha: f32) {
    let n = dst.len();
    let alpha_v = _mm256_set1_ps(alpha);
    let mut i = 0;

    while i + 8 <= n {
        let s = _mm256_loadu_ps(src.as_ptr().add(i));
        let d = _mm256_loadu_ps(dst.as_ptr().add(i));
        let result = _mm256_fmadd_ps(alpha_v, s, d);
        _mm256_storeu_ps(dst.as_ptr().add(i), result);
        i += 8;
    }

    while i < n {
        dst[i] = alpha * src[i] + dst[i];
        i += 1;
    }
}
```

The `unsafe` block here is not for aliasing; it is for the `avx2` target feature, which requires a runtime CPU feature check in production code. The borrow checker has already proven that `dst` and `src` do not alias, so the SIMD loads and stores are correct without additional guards. You can verify the generated assembly has no aliasing checks:

```bash
RUSTFLAGS="--emit=asm -C llvm-args=-x86-asm-syntax=intel" \
  cargo rustc --release -- --emit asm -C opt-level=3
# Inspect the output in target/release/deps/*.s for vectorized loops
# with no runtime alias guards
```

A common failure mode arises when the borrow checker rejects code that is actually safe but whose safety the analysis cannot prove. The classic example is the "mutable iterator over a self-referential method call":

```rust
struct Database {
    cache: std::collections::HashMap<u64, String>,
}

impl Database {
    fn get_or_insert(&mut self, key: u64) -> &String {
        if let Some(val) = self.cache.get(&key) {
            return val;
        }
        self.cache.insert(key, String::from("default"));
        self.cache.get(&key).unwrap()
    }
}
```

Under the older lexical borrow checker, the immutable borrow from `self.cache.get(&key)` would extend to the end of the function, colliding with `self.cache.insert`. NLL resolves this by expiring the immutable borrow at the `return val` branch. But a more stubborn variant appears when you need to return a reference obtained through a mutable method chain:

```rust
struct Graph {
    nodes: Vec<Node>,
}

struct Node {
    edges: Vec<usize>,
}

impl Graph {
    fn node_and_edges(&mut self, idx: usize) -> (&Node, &mut [usize]) {
        let node = &self.nodes[idx];       // immutable borrow of self
        let edges = &mut self.nodes[idx].edges; // mutable borrow of self
        (node, edges)
    }
}
```

This fails because `node` borrows `self.nodes` immutably while `edges` borrows it mutably, and the returned tuple extends both borrows to the call site. The compiler emits E0502. The fix is to split the borrows at the field level, which the compiler supports through disjoint field borrows:

```rust
impl Graph {
    fn node_and_edges(&mut self, idx: usize) -> (&Node, &mut [usize]) {
        let node = &self.nodes[idx];
        let edges = &mut self.nodes[idx].edges;
        (node, edges)
    }
}
```

This still fails because `self.nodes[idx]` is borrowed twice with conflicting mutability. The correct approach is to restructure so the borrows are provably disjoint, typically by splitting the slice or by using index-based indirection rather than holding two references into the same `Vec`:

```rust
impl Graph {
    fn edges_mut(&mut self, idx: usize) -> &mut [usize] {
        &mut self.nodes[idx].edges
    }

    fn node(&self, idx: usize) -> &Node {
        &self.nodes[idx]
    }
}

// At the call site, obtain them sequentially or use split_at_mut on the Vec
// if you need simultaneous access to different elements:
impl Graph {
    fn two_nodes_mut(&mut self, a: usize, b: usize) -> (&mut Node, &mut Node) {
        assert!(a < self.nodes.len() && b < self.nodes.len() && a != b);
        let (left, right) = self.nodes.split_at_mut(std::cmp::max(a, b));
        // safe because a != b and both in bounds; split_at_mut guarantees disjoint
        let (node_a, node_b) = if a < b {
            (&mut left[a], &mut right[0])
        } else {
            (&mut right[0], &mut left[b])
        };
        (node_a, node_b)
    }
}
```

`split_at_mut` is the standard library's escape hatch for borrowing two mutable references from the same slice. It is implemented with `unsafe` internally, relying on the fact that the two halves of a slice are provably disjoint in memory. This is the pattern you use when the borrow checker's analysis is too coarse for your data structure.

A more subtle failure mode involves self-referential structs. Rust does not permit safe self-referential types because moving the struct would invalidate the internal pointer, and Rust does move by default. The `Pin<T>` type was introduced to solve this for async generators, but `Pin` does not make self-referential structs safe to construct; it only makes them safe to use after construction. You must use `unsafe` or a library like `ouroboros` to construct them. The async runtime produces `Pin` through the `Future` trait's polling mechanism, and the compiler-generated state machines for `async fn` are the primary consumers:

```rust
use std::pin::Pin;
use std::marker::PhantomPinned;
use std::ptr::NonNull;

struct SelfReferential {
    data: String,
    slice: NonNull<String>,
    _pin: PhantomPinned,
}

impl SelfReferential {
    fn new(data: String) -> Pin<Box<Self>> {
        let mut boxed = Box::pin(SelfReferential {
            slice: NonNull::dangling(),
            data,
            _pin: PhantomPinned,
        });

        // SAFETY: boxed is pinned, will not move; we compute the pointer
        // to our own field, which is stable for the lifetime of the Pin.
        let mut_ref: &mut SelfReferential = unsafe {
            boxed.as_mut().get_unchecked_mut()
        };
        mut_ref.slice = NonNull::from(&mut_ref.data);

        boxed
    }

    fn slice(&self) -> &str {
        // SAFETY: slice was initialized in new() and points to self.data,
        // which is pinned and will not move.
        unsafe { self.slice.as_ref() }
    }
}
```

The `PhantomPinned` marker makes the type `!Unpin`, which prevents safe code from obtaining a `&mut SelfReferential` and moving it. `Pin<Box<T>>` is the type that enforces this: you can only get a `&mut T` through `unsafe` once the value is pinned. This is the mechanism behind `async fn` state machines, which are self-referential across `await` points.

For the diagnostic workflow when the borrow checker rejects your code, the key tools are the error messages themselves (which, since the NLL rewrite, include precise span highlights and suggestions) and `cargo` with the `--explain` flag:

```bash
cargo --explain E0597   # borrowed value does not live long enough
cargo --explain E0502   # cannot borrow as mutable because it is also borrowed as immutable
cargo --explain E0382   # use of moved value
```

When you face a lifetime error in a complex generic context, the most effective technique is to annotate lifetimes explicitly in the function signature, removing inference, and let the compiler report which lifetime constraint fails. This isolates the problem to a specific relationship. For structs with multiple lifetime parameters, consider whether they are truly independent or whether one should outlive the other (`'a: 'b` means `'a` outlives `'b`, a subtyping constraint on lifetimes):

```rust
struct Config<'src, 'pat> {
    source: &'src str,
    patterns: &'pat [&'pat str],
}

// If patterns reference into source, you need:
struct LinkedConfig<'src> {
    source: &'src str,
    patterns: &'src [&'src str],
}

// If source outlives patterns (patterns borrowed from a shorter-lived store):
struct ScopedConfig<'src, 'pat: 'src> {
    source: &'src str,
    patterns: &'pat [&'pat str],
}
```

Lifetime subtyping follows a contravariant rule: a longer lifetime can be used where a shorter one is expected, because a reference valid for a longer scope is certainly valid for a shorter one. The compiler uses this to allow flexible borrowing where the concrete lifetimes at the call site are shorter than the abstract lifetimes in the function signature. The variance rules are: `&'a T` is covariant in `'a` and `T`; `&'a mut T` is covariant in `'a` but invariant in `T` (because mutation through the reference could store a `T` with a shorter lifetime); `fn(T) -> U` is contravariant in `T` and covariant in `U`. These rules determine which subtype relationships the compiler accepts without explicit coercion.

The practical takeaway for systems programmers is that the borrow checker is a theorem prover for a specific class of memory safety properties. Its rejections are not stylistic opinions; they are proofs that your code, as written, permits undefined behavior under some execution path. When you reach for `unsafe`, you are taking on the proof obligation yourself. The discipline that makes Rust's safety story hold in practice is treating every `unsafe` block as a local invariant you must document and maintain, and every `unsafe impl` as a contract you are asserting about a type's internal representation. The type system does the rest, and it does it at zero runtime cost, which is the property that makes Rust viable for kernel modules, real-time audio, embedded firmware, and high-throughput network services where GC pauses are unacceptable.
