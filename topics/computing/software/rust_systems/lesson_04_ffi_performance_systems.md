# Lesson 4: Foreign Function Interface, Performance, and Systems Integration

## 1. First-Principles Intuition & Invariants

Rust's promise of memory safety and zero-cost abstractions confronts a fundamental architectural reality: the overwhelming majority of operating system interfaces, hardware abstraction layers, device drivers, cryptographic libraries, and high-performance numerical computing frameworks are written in C. The Foreign Function Interface (FFI) exists as the critical boundary layer where Rust's ownership semantics, lifetime enforcement, and borrow checker invariants must negotiate with C's raw pointer model, manual memory management, and implicit aliasing assumptions. This boundary is not merely a technical convenience—it represents the seam between two fundamentally incompatible type systems and memory models that must coexist within the same address space.

The core architectural tension arises from Rust's semantic guarantees, which are enforced statically at compile time through affine types and region-based memory safety, versus C's explicit trust in programmer discipline where every pointer dereference is an unchecked assertion about memory validity. When Rust code invokes a C function, the compiler cannot reason about the safety of operations occurring within that foreign frame. The C function might retain pointers to Rust-allocated memory, mutate data through aliased pointers that violate Rust's exclusivity rules, or trigger undefined behavior through null dereferences, buffer overruns, or use-after-free accesses. Conversely, when C code calls into Rust through exported functions, the C caller has no awareness of ownership transfers, lifetime constraints, or drop semantics that govern the Rust heap.

The fundamental invariant governing all FFI interactions is the Application Binary Interface (ABI), which defines calling conventions, stack frame layouts, register allocation for function arguments, structure padding and alignment rules, and exception propagation mechanisms. The C ABI has achieved de facto standardization across platforms through decades of compiler evolution and operating system API contracts. On x86-64 System V (Linux, macOS, BSD), the calling convention passes the first six integer or pointer arguments in registers RDI, RSI, RDX, RCX, R8, and R9, with floating-point arguments in XMM0 through XMM7, while the Windows x64 calling convention uses RCX, RDX, R8, R9 for the first four arguments with shadow space reserved on the stack. Structure returns larger than two machine words typically involve the caller allocating stack space and passing a hidden pointer in the first argument register. Rust must precisely replicate these mechanical details to achieve binary compatibility, which necessitates explicit ABI annotations on every foreign function declaration.

Memory layout guarantees form the second critical invariant. Rust's default structure representation applies reordering optimizations to minimize padding and cache line waste, but C compilers follow strictly sequential field layout as declared in the source. A Rust struct with fields of types `u8, u64, u8` might be reordered to `u64, u8, u8` to eliminate six bytes of padding, but the corresponding C struct will always maintain declaration order with explicit padding inserted by the compiler. The `#[repr(C)]` attribute instructs the Rust compiler to adopt C's layout algorithm, disabling field reordering and applying platform-specific padding rules. Enumerations present additional complexity: Rust's default enum representation uses discriminant optimization where `Option<&T>` occupies the same space as a raw pointer by leveraging null as the None discriminant, but `#[repr(C)]` enums must use explicit integer tags compatible with C's enum-to-int conversion rules.

Alignment requirements impose physical constraints rooted in CPU memory access semantics. Most architectures prohibit or severely penalize misaligned loads: an x86-64 processor accessing a u64 at an address not divisible by eight may require splitting the load across cache line boundaries, and ARM processors historically trapped misaligned accesses as hardware exceptions. The alignment of a structure in C is determined by its most strictly aligned member, and the total size must be a multiple of that alignment to enable correct array indexing. Rust inherits these rules when `#[repr(C)]` is applied, but unsafe code that manually constructs references from raw pointers bears the burden of ensuring alignment correctness. Creating a reference to misaligned data is immediate undefined behavior in Rust, even if the reference is never dereferenced, because the compiler assumes all references satisfy alignment invariants when generating code.

The unsafe keyword delimits the trust boundary where the compiler cannot enforce safety invariants and transfers responsibility to the programmer. Every FFI function declaration is implicitly unsafe because the Rust compiler cannot verify the preconditions that the foreign implementation assumes. A C function declared as `void process_buffer(const char *data, size_t len)` encodes several implicit contracts: the data pointer must be valid for reads of len bytes, the memory region must remain valid for the duration of the call, and len must accurately represent the buffer size. Violating any of these preconditions invokes undefined behavior, but the Rust type system provides no mechanism to encode or verify these requirements. The programmer must manually establish that these preconditions hold at every call site by reasoning about ownership, lifetime validity, and pointer provenance.

Pointer provenance, formalized through the Stacked Borrows model, dictates that every pointer carries an invisible tag representing its derivation chain from an original allocation. In Rust's abstract machine, creating a reference borrows from a parent pointer and pushes a new tag onto a permission stack. Raw pointer casts and FFI boundaries discard these tags, forcing the programmer to reason about aliasing correctness without compiler assistance. When passing a mutable reference across FFI, the foreign code may create arbitrary aliased pointers to the same memory, violating Rust's exclusivity guarantee. The programmer must ensure that no Rust code accesses the data through the original reference while foreign aliases exist, effectively creating a manual critical section where Rust's type system is suspended.

Lifetime elision across FFI boundaries presents another fundamental challenge. Rust references encode lifetimes as compile-time region constraints, but raw pointers erased through FFI carry no lifetime information. A function signature like `extern "C" fn get_name() -> *const c_char` provides no indication of how long the returned pointer remains valid. The caller must consult external documentation to determine whether the pointer references static storage, thread-local storage with implicit lifetime bounds, or heap memory requiring explicit deallocation. Incorrect lifetime assumptions manifest as use-after-free vulnerabilities that the borrow checker cannot detect because the unsafe boundary has severed the lifetime tracking chain.

The zero-cost abstraction principle, Rust's foundational performance invariant, demands that high-level abstractions compile to machine code identical to hand-written unsafe alternatives. FFI represents the ultimate test of this principle: wrapping foreign C libraries in safe Rust interfaces must impose no runtime overhead beyond the irreducible cost of the ABI transition itself. This requirement drives the design of inline functions, monomorphization strategies, and link-time optimization techniques that enable the compiler to see through abstraction boundaries and generate optimal calling sequences. When successful, a safe Rust wrapper around a C cryptographic primitive should compile to exactly the same assembly as calling the C function directly with raw pointers, preserving both safety and performance.

## 2. Core Architecture & Mechanics

The mechanical foundation of FFI begins with function declarations annotated with extern blocks that specify the calling convention and symbol linkage. The extern "C" annotation instructs the compiler to use the C calling convention and disable name mangling, allowing the linker to resolve symbols against C object files or shared libraries. A minimal FFI declaration binding the standard C library `strlen` function appears as:

```rust
extern "C" {
    fn strlen(s: *const std::os::raw::c_char) -> std::os::raw::c_ulong;
}
```

The `c_char` and `c_ulong` types from `std::os::raw` provide platform-portable aliases for C's `char` and `unsigned long`, which vary in size and signedness across targets. On most Unix platforms, `c_char` maps to `i8`, but on ARM and PowerPC, it maps to `u8` because the hardware sign-extends byte loads differently. The `c_ulong` type is 32 bits on 32-bit systems and Windows x64, but 64 bits on Unix x64, reflecting C's `long` type semantics. Using these aliases ensures that structure layouts match the platform's C ABI regardless of target architecture.

Invoking foreign functions requires wrapping the call in an unsafe block because the compiler cannot verify the preconditions. A safe wrapper that exposes `strlen` to Rust code must establish the necessary invariants:

```rust
pub fn safe_strlen(s: &std::ffi::CStr) -> usize {
    unsafe {
        strlen(s.as_ptr()) as usize
    }
}
```

The `CStr` type from `std::ffi` represents a borrowed view of a null-terminated C string, encoding the invariant that the byte sequence contains a null terminator and is valid UTF-8 or arbitrary bytes depending on usage context. By accepting a reference to `CStr`, the wrapper leverages Rust's lifetime system to ensure the string remains valid for the duration of the call, transforming the implicit precondition of the raw C function into an explicit type constraint that the compiler can verify.

Passing Rust data structures to C requires careful attention to representation attributes and ownership semantics. Consider a scenario where C code expects a structure representing a network packet header:

```rust
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct PacketHeader {
    pub version: u8,
    pub flags: u8,
    pub length: u16,
    pub timestamp: u64,
    pub source_addr: u32,
    pub dest_addr: u32,
}

extern "C" {
    fn process_packet(header: *const PacketHeader, payload: *const u8, payload_len: usize) -> i32;
}

pub fn send_packet(header: &PacketHeader, payload: &[u8]) -> Result<(), i32> {
    let result = unsafe {
        process_packet(header as *const PacketHeader, payload.as_ptr(), payload.len())
    };
    if result == 0 {
        Ok(())
    } else {
        Err(result)
    }
}
```

The `#[repr(C)]` attribute ensures that field layout matches C's expectations with explicit padding inserted between `flags` and `length` to satisfy `u16` alignment, and between `length` and `timestamp` to satisfy `u64` alignment. The `Copy` trait allows the structure to be safely duplicated through bitwise copy, which is essential for FFI types that C functions may duplicate internally. The wrapper function converts Rust references into raw pointers at the FFI boundary, transferring temporary ownership to the foreign function while maintaining lifetime correctness through Rust's borrow checker enforcement at the call site.

Returning structures from C requires understanding whether the value is returned directly or through a hidden pointer parameter. Small structures that fit within two registers typically use direct return, while larger structures trigger the hidden pointer mechanism. A C function declared as `struct LargeResult compute(int input)` where `LargeResult` exceeds 16 bytes is actually called with the signature `void compute(struct LargeResult *ret, int input)` at the ABI level. Rust handles this automatically when the structure has `#[repr(C)]`:

```rust
#[repr(C)]
pub struct LargeResult {
    pub status: i32,
    pub data: [u8; 256],
    pub checksum: u64,
}

extern "C" {
    fn compute(input: i32) -> LargeResult;
}

pub fn safe_compute(input: i32) -> LargeResult {
    unsafe { compute(input) }
}
```

The compiler generates code that allocates stack space for `LargeResult`, passes a pointer as a hidden first argument, and the C function populates the structure in place, avoiding unnecessary copies.

Callbacks represent the inverse problem where C code invokes Rust functions through function pointers. The Rust function must be declared with the C ABI to ensure correct calling convention, and must be careful about panics and unwinding. C code has no understanding of Rust's panic mechanism, and unwinding through foreign frames is undefined behavior. Every Rust callback must catch panics at the boundary:

```rust
extern "C" fn rust_callback(user_data: *mut std::os::raw::c_void, value: i32) -> i32 {
    let result = std::panic::catch_unwind(|| {
        let data = unsafe { &mut *(user_data as *mut CallbackState) };
        data.accumulator += value;
        0
    });
    result.unwrap_or(-1)
}

pub struct CallbackState {
    pub accumulator: i32,
}

extern "C" {
    fn register_callback(callback: extern "C" fn(*mut std::os::raw::c_void, i32) -> i32, user_data: *mut std::os::raw::c_void);
}

pub fn setup_callback(state: &mut CallbackState) {
    unsafe {
        register_callback(rust_callback, state as *mut CallbackState as *mut std::os::raw::c_void);
    }
}
```

The `catch_unwind` call establishes a panic boundary that prevents unwinding from escaping into C frames. The callback signature uses `*mut c_void` for type-erased context, a common C pattern for passing arbitrary user data through library interfaces. The Rust code casts the void pointer back to a typed reference inside the unsafe block, relying on the invariant that the pointer originated from a valid `CallbackState` reference and remains live for the callback's duration.

Opaque types, where C exposes structures without defining their internal layout, require special handling. Many C libraries define handle types as incomplete structures:

```c
typedef struct Connection Connection;
Connection* connection_open(const char *addr);
void connection_close(Connection *conn);
int connection_send(Connection *conn, const void *data, size_t len);
```

Rust binds these using zero-sized or single-field wrapper types marked with `#[repr(C)]`:

```rust
#[repr(C)]
pub struct Connection {
    _private: [u8; 0],
}

extern "C" {
    fn connection_open(addr: *const std::os::raw::c_char) -> *mut Connection;
    fn connection_close(conn: *mut Connection);
    fn connection_send(conn: *mut Connection, data: *const std::os::raw::c_void, len: usize) -> i32;
}

pub struct SafeConnection {
    inner: *mut Connection,
}

impl SafeConnection {
    pub fn open(addr: &std::ffi::CStr) -> Option<Self> {
        let ptr = unsafe { connection_open(addr.as_ptr()) };
        if ptr.is_null() {
            None
        } else {
            Some(SafeConnection { inner: ptr })
        }
    }

    pub fn send(&mut self, data: &[u8]) -> Result<(), i32> {
        let result = unsafe {
            connection_send(self.inner, data.as_ptr() as *const std::os::raw::c_void, data.len())
        };
        if result == 0 {
            Ok(())
        } else {
            Err(result)
        }
    }
}

impl Drop for SafeConnection {
    fn drop(&mut self) {
        unsafe {
            connection_close(self.inner);
        }
    }
}
```

The zero-sized array `[u8; 0]` in the `Connection` structure prevents the type from being instantiated in Rust while maintaining correct pointer semantics. The `SafeConnection` wrapper owns the opaque pointer and implements `Drop` to ensure the C resource is freed when the Rust object goes out of scope, integrating foreign resources into Rust's ownership system. The constructor returns `Option` to handle allocation failures where the C function returns null, converting C's error convention into Rust's type-based error handling.

Inline assembly provides direct access to CPU instructions for performance-critical code paths and hardware interfacing that cannot be expressed in Rust. The `asm!` macro embeds assembly using AT&T or Intel syntax with explicit register constraints:

```rust
use std::arch::asm;

pub fn rdtsc() -> u64 {
    let low: u32;
    let high: u32;
    unsafe {
        asm!(
            "rdtsc",
            out("eax") low,
            out("edx") high,
            options(nomem, nostack, preserves_flags)
        );
    }
    ((high as u64) << 32) | (low as u64)
}

pub fn cpuid(leaf: u32) -> (u32, u32, u32, u32) {
    let eax: u32;
    let ebx: u32;
    let ecx: u32;
    let edx: u32;
    unsafe {
        asm!(
            "cpuid",
            inout("eax") leaf => eax,
            out("ebx") ebx,
            out("ecx") ecx,
            out("edx") edx,
            options(nomem, nostack, preserves_flags)
        );
    }
    (eax, ebx, ecx, edx)
}
```

The `rdtsc` instruction reads the processor's time-stamp counter, a monotonically increasing 64-bit value split across EDX:EAX registers. The `out` constraints specify that the instruction writes to EAX and EDX, and the compiler allocates these registers and generates code to move the results into Rust variables. The `options` clause declares that the assembly does not access memory, does not modify the stack pointer, and preserves all CPU flags, enabling the optimizer to reorder surrounding code more aggressively. The `cpuid` instruction provides processor identification and feature flags, taking a leaf value in EAX and returning data across all four registers. The `inout` constraint indicates that EAX serves as both input and output, with the compiler handling the register allocation and data flow.

Memory barriers and atomic operations at the hardware level require inline assembly when Rust's `std::sync::atomic` primitives are insufficient. A full memory fence on x86-64 uses the `mfence` instruction:

```rust
pub fn memory_fence_full() {
    unsafe {
        asm!("mfence", options(nostack, preserves_flags));
    }
}

pub fn atomic_swap_relaxed(ptr: *mut u64, new_value: u64) -> u64 {
    let old_value: u64;
    unsafe {
        asm!(
            "xchg [{ptr}], {new}",
            ptr = in(reg) ptr,
            new = inout(reg) new_value => old_value,
            options(nostack, preserves_flags)
        );
    }
    old_value
}
```

The `xchg` instruction performs an atomic exchange with implicit lock prefix on all x86 processors, swapping the memory location with a register. The bracket syntax `[{ptr}]` dereferences the pointer in the specified register as a memory operand, and the `inout` constraint reflects that the register holds the new value on entry and the old value on exit.

Link-time optimization (LTO) enables cross-language inlining where the compiler can see through FFI boundaries when building the entire program. Rust's LTO infrastructure uses LLVM's intermediate representation (IR) to merge modules:

```toml
[profile.release]
lto = "fat"
codegen-units = 1
```

The `lto = "fat"` setting performs whole-program optimization across all Rust and C code linked into the binary, provided that C components are compiled with `-flto` to generate LLVM bitcode. This allows the optimizer to inline small C functions directly into Rust call sites, eliminate unused C functions based on Rust's actual usage, and optimize across the ABI boundary by transforming calling conventions or eliminating indirection when the full call graph is visible. Reducing `codegen-units` to one forces sequential code generation, increasing compile time but maximizing optimization potential by giving the optimizer complete visibility into all generated code.

Platform-specific intrinsics expose SIMD instructions and specialized CPU features through zero-cost wrappers defined in `std::arch`. The x86-64 AVX2 intrinsics provide 256-bit vector operations:

```rust
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

#[target_feature(enable = "avx2")]
pub unsafe fn simd_sum_avx2(data: &[f32]) -> f32 {
    assert!(data.len() % 8 == 0);
    let mut sum = _mm256_setzero_ps();
    let chunks = data.chunks_exact(8);
    for chunk in chunks {
        let vec = _mm256_loadu_ps(chunk.as_ptr());
        sum = _mm256_add_ps(sum, vec);
    }
    let mut result = [0.0f32; 8];
    _mm256_storeu_ps(result.as_mut_ptr(), sum);
    result.iter().sum()
}
```

The `_mm256_loadu_ps` intrinsic loads eight f32 values into a 256-bit YMM register using unaligned load, `_mm256_add_ps` performs parallel addition across all eight lanes, and `_mm256_storeu_ps` writes the vector back to memory. The `#[target_feature]` attribute indicates that the function requires AVX2 support, and the compiler generates code that assumes these instructions are available, including using the VEX encoding prefix. The function is marked unsafe because calling it on a CPU without AVX2 will trigger an illegal instruction exception, transferring the responsibility of runtime feature detection to the caller.

Dynamic linking against system libraries uses the build script `build.rs` to emit linker directives:

```rust
// build.rs
fn main() {
    println!("cargo:rustc-link-lib=ssl");
    println!("cargo:rustc-link-lib=crypto");
    println!("cargo:rustc-link-search=native=/usr/local/lib");
}
```

The `rustc-link-lib` directive adds `-lssl` and `-lcrypto` to the linker invocation, and `rustc-link-search` adds a library search path. For static linking, the directive `println!("cargo:rustc-link-lib=static=mylib")` forces the linker to prefer the static archive `libmylib.a` over the shared object `libmylib.so`. Build scripts can also invoke external build systems like `make` or `cmake` to compile C dependencies as part of the Rust build:

```rust
// build.rs
use std::process::Command;

fn main() {
    let dst = cmake::Config::new("vendor/libfoo")
        .define("BUILD_SHARED_LIBS", "OFF")
        .build();
    println!("cargo:rustc-link-search=native={}/lib", dst.display());
    println!("cargo:rustc-link-lib=static=foo");
}
```

The `cmake` crate provides a builder interface for invoking CMake, configuring the project with static library output, and returning the installation prefix where the linker can find the compiled artifacts.

## 3. High-Performance Optimization & Failure Modes

The performance characteristics of FFI code diverge sharply from pure Rust due to optimizer visibility constraints and ABI transition overhead. Every function call across the FFI boundary incurs the full cost of the C calling convention: saving callee-saved registers to the stack, passing arguments through the designated register or stack slots, performing the indirect call through the procedure linkage table (PLT) for shared libraries, and restoring registers on return. These mechanical costs are irreducible when the compiler cannot see the foreign function's implementation, but inlining and LTO can eliminate the boundary entirely when both sides are visible at link time.

The most critical optimization technique is minimizing FFI transitions by batching operations. Consider a scenario where Rust code processes an array by calling a C function for each element:

```rust
extern "C" {
    fn process_element(x: f64) -> f64;
}

pub fn process_array_naive(data: &mut [f64]) {
    for x in data.iter_mut() {
        *x = unsafe { process_element(*x) };
    }
}
```

This approach invokes the FFI overhead for every array element, incurring PLT indirection, register spilling, and instruction cache pressure. A vectorized alternative passes the entire array, amortizing the transition cost:

```rust
extern "C" {
    fn process_elements(data: *mut f64, len: usize);
}

pub fn process_array_batch(data: &mut [f64]) {
    unsafe {
        process_elements(data.as_mut_ptr(), data.len());
    }
}
```

The C implementation can then apply SIMD optimizations and loop unrolling across the contiguous buffer, and the single FFI call eliminates thousands of individual transitions. The performance difference scales linearly with array size, easily reaching orders of magnitude for large datasets.

Pointer aliasing rules create subtle optimization barriers at FFI boundaries. Rust's `&mut T` references guarantee exclusive access, enabling aggressive optimization through alias analysis, but raw pointers passed to C functions are assumed to alias arbitrarily. The compiler must conservatively assume that any C function might write to any accessible memory through aliased pointers, forcing it to reload values from memory after FFI calls rather than keeping them in registers. Consider a loop that accumulates results while calling a foreign function:

```rust
extern "C" {
    fn transform(x: f64) -> f64;
}

pub fn accumulate(data: &[f64]) -> f64 {
    let mut sum = 0.0;
    for &x in data {
        sum += unsafe { transform(x) };
    }
    sum
}
```

The compiler must reload `sum` from the stack after every `transform` call because it cannot prove that the foreign function does not modify the stack frame through some hidden pointer. If `transform` is pure and the C source is available, annotating it with `__attribute__((const))` in C or wrapping it in a Rust inline function that the optimizer can reason about allows the compiler to keep `sum` in an XMM register throughout the loop.

Cache locality degradation occurs when FFI calls disrupt sequential access patterns. Rust's iterator chains and closures often compile to tight, cache-friendly loops where data prefetching and speculative execution provide substantial speedups, but opaque FFI calls disrupt instruction and data prefetch streams. A function that interleaves Rust and C operations will suffer from instruction cache misses as the CPU alternates between Rust-generated code and C library code that may reside in different pages. Structuring code to complete all C operations in one phase before returning to Rust processing improves locality.

String conversion overhead represents a common performance trap in FFI-heavy code. Rust's `String` and `&str` use UTF-8 encoding and store length explicitly, while C's `char*` strings are null-terminated with implicit length. Converting between representations requires allocation and validation:

```rust
use std::ffi::{CString, CStr};

extern "C" {
    fn c_function(s: *const std::os::raw::c_char) -> *const std::os::raw::c_char;
}

pub fn string_roundtrip(input: &str) -> Result<String, std::ffi::NulError> {
    let c_string = CString::new(input)?;
    let result_ptr = unsafe { c_function(c_string.as_ptr()) };
    let result_cstr = unsafe { CStr::from_ptr(result_ptr) };
    Ok(result_cstr.to_string_lossy().into_owned())
}
```

The `CString::new` call scans the input for null bytes and allocates a new buffer with an appended null terminator, and `to_string_lossy` performs UTF-8 validation and copies the data into a Rust `String`. For high-throughput string processing, maintaining buffers in C-compatible format throughout the pipeline eliminates repeated conversions. Alternatively, using byte slices `&[u8]` and agreeing on length-prefixed encoding avoids null-terminator scanning entirely.

Memory allocator mismatches constitute a critical failure mode when heap memory crosses FFI boundaries. Rust's global allocator, typically the system allocator on Unix or a custom allocator on embedded platforms, must match the allocator used by the C library. Allocating memory with Rust's allocator and freeing it with C's `free()`, or vice versa, corrupts the heap metadata and triggers undefined behavior. The safe approach uses allocator-specific free functions:

```rust
extern "C" {
    fn create_buffer(size: usize) -> *mut u8;
    fn free_buffer(ptr: *mut u8);
}

pub struct ForeignBuffer {
    ptr: *mut u8,
    len: usize,
}

impl ForeignBuffer {
    pub fn new(size: usize) -> Option<Self> {
        let ptr = unsafe { create_buffer(size) };
        if ptr.is_null() {
            None
        } else {
            Some(ForeignBuffer { ptr, len: size })
        }
    }

    pub fn as_slice(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.ptr, self.len) }
    }
}

impl Drop for ForeignBuffer {
    fn drop(&mut self) {
        unsafe {
            free_buffer(self.ptr);
        }
    }
}
```

The wrapper always pairs allocation and deallocation through the same API, ensuring allocator consistency. When C libraries provide opaque handles that encapsulate memory management, this pattern naturally emerges.

Thread safety at FFI boundaries requires understanding C libraries' threading models. Many legacy C libraries are not thread-safe and require external synchronization. The Rust wrapper must enforce this through types, typically using a `Mutex`:

```rust
use std::sync::Mutex;

pub struct ThreadSafeLibrary {
    _private: (),
}

static LIBRARY_LOCK: Mutex<()> = Mutex::new(());

extern "C" {
    fn non_thread_safe_operation(data: *const u8, len: usize) -> i32;
}

impl ThreadSafeLibrary {
    pub fn operate(&self, data: &[u8]) -> Result<(), i32> {
        let _guard = LIBRARY_LOCK.lock().unwrap();
        let result = unsafe {
            non_thread_safe_operation(data.as_ptr(), data.len())
        };
        if result == 0 {
            Ok(())
        } else {
            Err(result)
        }
    }
}
```

The static mutex ensures that only one thread can execute the foreign function at a time, preventing data races within the C library's global state. The cost of lock acquisition is significant, but correctness demands it when the library lacks internal synchronization.

Signal safety represents an acute hazard when FFI code interacts with Unix signal handlers. Async-signal-safe functions are the limited subset of library functions guaranteed safe to call from signal handlers, excluding most of the standard library. Rust's panic mechanism and unwinding infrastructure are emphatically not signal-safe. A signal arriving during a Rust allocation, a foreign function call, or any unsafe operation can trigger undefined behavior if the signal handler calls non-reentrant code:

```rust
extern "C" {
    fn register_signal_handler(signum: i32, handler: extern "C" fn(i32));
}

extern "C" fn signal_handler(_signum: i32) {
    // UNSAFE: Most operations are forbidden here
    // Only async-signal-safe C functions are legal
    // Absolutely NO Rust allocations, panics, or unwinding
    unsafe {
        let msg = b"Signal received\n";
        libc::write(libc::STDOUT_FILENO, msg.as_ptr() as *const _, msg.len());
    }
}
```

The handler uses only the async-signal-safe `write` system call, avoiding all higher-level I/O. Signal handlers in FFI contexts should set atomic flags or write to self-pipe fds, deferring actual processing to the main event loop.

Panic unwinding across FFI is undefined behavior and must be prevented with `catch_unwind` at every callback boundary. The C standard library and most platform ABIs have no concept of unwinding through foreign frames, and attempting to do so corrupts the C call stack:

```rust
extern "C" fn ffi_callback(user_data: *mut std::os::raw::c_void) -> i32 {
    let result = std::panic::catch_unwind(|| {
        // Rust code that might panic
        let data = unsafe { &mut *(user_data as *mut State) };
        risky_operation(data)?;
        Ok(0)
    });
    match result {
        Ok(Ok(value)) => value,
        Ok(Err(e)) => {
            // Log error through FFI-safe mechanism
            -1
        }
        Err(_) => {
            // Panic occurred, return error code
            -2
        }
    }
}
```

The outer `catch_unwind` traps panics, and the inner `Result` handles explicit errors, ensuring that all failure modes map to C-compatible integer error codes rather than unwinding through foreign frames.

Alignment violations manifest as hard-to-diagnose crashes or silent corruption on architectures with strict alignment requirements. Creating a reference to misaligned data is immediate undefined behavior:

```rust
#[repr(C, packed)]
struct PackedStruct {
    a: u8,
    b: u64,
}

extern "C" {
    fn process_u64(value: *const u64);
}

pub fn process_packed(s: &PackedStruct) {
    // UNDEFINED BEHAVIOR: &s.b creates misaligned reference
    // unsafe { process_u64(&s.b as *const u64); }
    
    // CORRECT: Use raw pointer without creating reference
    unsafe {
        let ptr = std::ptr::addr_of!(s.b);
        process_u64(ptr);
    }
}
```

The `packed` attribute removes all padding, causing `b` to reside at offset one, misaligned for a u64. The `addr_of!` macro obtains a raw pointer without creating an intermediate reference, avoiding undefined behavior. The C function must handle potentially misaligned pointers appropriately, typically by copying to an aligned temporary.

Type confusion across FFI occurs when Rust and C disagree on structure layout or integer signedness. A C enum declared as `enum Status { OK = 0, ERROR = -1 }` is a signed integer, but Rust's `#[repr(C)] enum` defaults to the smallest unsigned integer that can hold all discriminants. Explicit `#[repr(i32)]` or matching the C declaration's underlying type resolves the mismatch:

```rust
#[repr(i32)]
#[derive(Debug, Copy, Clone, PartialEq, Eq)]
pub enum Status {
    Ok = 0,
    Error = -1,
}

extern "C" {
    fn get_status() -> Status;
}
```

The signed representation ensures that negative discriminants are correctly interpreted, preventing the value -1 from being reinterpreted as a large positive integer.

Lifetime extension errors occur when FFI functions retain pointers beyond the scope of the original borrow. A C library that stores a pointer in a global or thread-local variable for later use violates Rust's borrowing rules if the original data is dropped:

```rust
extern "C" {
    fn register_buffer(data: *const u8, len: usize);
    fn clear_buffer();
}

pub fn unsafe_registration() {
    let data = vec![1, 2, 3, 4];
    unsafe {
        register_buffer(data.as_ptr(), data.len());
    }
    // UNDEFINED BEHAVIOR: data is dropped here, but C library still holds pointer
}

pub fn safe_registration() -> Box<Vec<u8>> {
    let data = Box::new(vec![1, 2, 3, 4]);
    unsafe {
        register_buffer(data.as_ptr(), data.len());
    }
    data // Caller must keep this alive until clear_buffer() is called
}
```

The safe version returns the boxed vector to the caller, forcing explicit lifetime management. The caller owns the data and must ensure it outlives the C library's usage, typically by calling `clear_buffer()` before dropping the box. For truly static buffers, leaking memory with `Box::leak` converts an owned allocation into a static reference:

```rust
pub fn permanent_registration(data: Vec<u8>) {
    let leaked: &'static [u8] = Box::leak(data.into_boxed_slice());
    unsafe {
        register_buffer(leaked.as_ptr(), leaked.len());
    }
}
```

The leaked reference has infinite lifetime, satisfying any foreign lifetime requirements at the cost of permanent memory allocation. This pattern is appropriate for configuration data or buffers that logically exist for the program's entire lifetime.

Debugging FFI code requires specialized tools because errors manifest as memory corruption or crashes in foreign code. Using `valgrind` or `AddressSanitizer` detects use-after-free and buffer overruns that cross the language boundary:

```bash
RUSTFLAGS="-Z sanitizer=address" cargo build --target x86_64-unknown-linux-gnu
./target/x86_64-unknown-linux-gnu/debug/program
```

AddressSanitizer instruments both Rust and C code to detect spatial and temporal memory errors, reporting the allocation site, free site, and use site with stack traces across the FFI boundary. Similarly, `ThreadSanitizer` detects data races in multithreaded FFI code:

```bash
RUSTFLAGS="-Z sanitizer=thread" cargo build --target x86_64-unknown-linux-gnu
```

These tools impose significant runtime overhead, typically 2-5x slowdown for AddressSanitizer and 5-15x for ThreadSanitizer, but are invaluable for validating unsafe code correctness.

The ultimate optimization technique for FFI-heavy workloads is eliminating the boundary entirely through static linking and link-time optimization. Compiling both Rust and C components to LLVM IR and merging them at link time allows the optimizer to inline across languages, eliminate dead code, and apply interprocedural optimizations:

```toml
[profile.release]
lto = "fat"
codegen-units = 1
panic = "abort"
```

Disabling unwinding with `panic = "abort"` eliminates the unwinding metadata and landing pads, reducing binary size and improving instruction cache efficiency. The resulting binary treats Rust and C as a single monolithic program where the FFI boundary is an internal implementation detail that the optimizer can see through, approaching the theoretical zero-cost ideal where abstraction imposes no runtime penalty.
