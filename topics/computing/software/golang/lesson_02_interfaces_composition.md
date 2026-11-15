# Lesson 2: Interfaces, Composition, Embedding

## 1. First-Principles Intuition & Invariants

Go's approach to polymorphism and type abstraction represents a deliberate departure from the class-based inheritance hierarchies that dominated object-oriented design for decades. Where languages like C++ and Java require explicit declaration of interface implementation through inheritance keywords, Go introduces a radical simplification: implicit interface satisfaction through structural typing. This design choice fundamentally alters the coupling dynamics between abstraction and implementation, enabling what Rob Pike describes as "the ability to describe behavior without prescribing structure."

At its core, an interface in Go defines a contract of behavior expressed purely as a method set. Any concrete type that implements all methods in that set satisfies the interface automatically, without ever naming or importing the interface definition. This inversion of dependency direction enables libraries to define interfaces for types they do not own, consumers to specify minimal contracts without forcing implementation details, and systems to evolve independently across module boundaries. The compiler enforces satisfaction at compile time through static method-set analysis, but the assignment of concrete values to interface variables occurs dynamically, with runtime type information stored in a two-word structure containing a type descriptor pointer and a data pointer.

The absence of inheritance in Go flows from a recognition that implementation reuse through subclass hierarchies creates brittle coupling and the notorious fragile base class problem. Instead, Go embraces composition as the primary mechanism for code reuse, allowing types to aggregate other types through embedding. When a struct embeds another type, the embedded type's methods are promoted to the outer struct's method set, creating a form of automatic delegation without the complexity of virtual method tables or diamond inheritance ambiguities. This promotion mechanism operates through simple name resolution rules: if the outer type does not define a method with a given name, the compiler searches embedded fields in breadth-first order, resolving to the first match.

The duality between value receivers and pointer receivers introduces subtle but critical semantics for method set membership. A method defined on a value receiver belongs to both the value method set and the pointer method set of that type, because the compiler can trivially take the address of a value to satisfy pointer semantics. Conversely, a method defined on a pointer receiver belongs only to the pointer method set, as creating a pointer from an arbitrary value would be semantically unsafe for addressable values. This asymmetry explains why interface satisfaction behaves differently depending on whether the concrete type is stored as a value or a pointer, a distinction that frequently surfaces in production code when generic container types or reflection-based serialization libraries fail to invoke expected methods.

Type assertions and type switches provide controlled mechanisms for recovering concrete type information from interface variables, enabling runtime polymorphism patterns such as discriminated unions, capability detection, and performance-critical fast paths. The comma-ok idiom for type assertions returns both the extracted value and a boolean success indicator, preventing runtime panics when the assertion fails. This explicit error-checking pattern aligns with Go's broader philosophy of making control flow visible and forcing developers to acknowledge failure modes rather than relying on exception-based unwinding.

The invariant that governs all interface mechanics is this: an interface value is nil if and only if both its type descriptor and its data pointer are nil. A common pitfall arises when a nil pointer of a concrete type is assigned to an interface variable; the resulting interface is non-nil because it contains a valid type descriptor, even though the data pointer is nil. This semantic subtlety manifests in conditional checks where `if err != nil` succeeds unexpectedly, leading to production bugs that surface only under specific error-handling paths.

## 2. Core Architecture & Mechanics

The runtime representation of an interface value consists of a two-word structure known as an `iface` for non-empty interfaces or `eface` for the empty interface. The first word points to an `itab` structure, which contains a pointer to the interface type metadata and a pointer to the concrete type metadata, along with a function pointer table mapping each interface method to the corresponding concrete implementation. The second word holds the actual data pointer to the concrete value. This indirection layer enables dynamic dispatch: when a method is invoked on an interface variable, the runtime indexes into the `itab` function table, retrieves the concrete function pointer, and invokes it with the data pointer as the receiver.

```
┌─────────────────┐
│ Interface Value │
├─────────────────┤
│  *itab          │──────┐
├─────────────────┤      │
│  *data          │──┐   │
└─────────────────┘  │   │
                      │   │
                      │   └──▶ ┌──────────────┐
                      │        │ itab         │
                      │        ├──────────────┤
                      │        │ *interfaceT  │
                      │        │ *concreteT   │
                      │        │ hash         │
                      │        │ [fun ptrs]   │
                      │        └──────────────┘
                      │
                      └──────▶ ┌──────────────┐
                               │ Concrete Data│
                               └──────────────┘
```

When the compiler encounters an assignment of a concrete value to an interface variable, it generates code to construct the `itab` structure if one does not already exist in the runtime's `itab` cache. This construction process involves computing the concrete type's method set, verifying that it satisfies the interface's method set, and building the function pointer table by looking up each interface method in the concrete type's method table. The resulting `itab` is cached in a global hash table keyed by the pair of interface type and concrete type, amortizing the cost of repeated assignments across the program's lifetime.

Consider the canonical example of an I/O abstraction layer where multiple concrete implementations satisfy a common interface contract:

```go
package io

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type ReadWriter interface {
    Reader
    Writer
}
```

The `ReadWriter` interface embeds both `Reader` and `Writer`, creating a composite interface whose method set is the union of its embedded interfaces. This composition operates at the type system level, not through runtime delegation. The compiler expands the embedded interface names into their constituent method signatures, producing a single flattened method set that any concrete type must satisfy.

A production-grade file abstraction might compose behavior through embedding:

```go
package storage

import (
    "io"
    "os"
    "sync"
)

type BufferedFile struct {
    *os.File
    mu     sync.Mutex
    buffer []byte
    offset int
}

func NewBufferedFile(path string, bufSize int) (*BufferedFile, error) {
    f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE, 0644)
    if err != nil {
        return nil, err
    }
    return &BufferedFile{
        File:   f,
        buffer: make([]byte, bufSize),
    }, nil
}

func (bf *BufferedFile) Write(p []byte) (int, error) {
    bf.mu.Lock()
    defer bf.mu.Unlock()
    
    if len(p) > len(bf.buffer)-bf.offset {
        if err := bf.Flush(); err != nil {
            return 0, err
        }
    }
    
    if len(p) > len(bf.buffer) {
        return bf.File.Write(p)
    }
    
    n := copy(bf.buffer[bf.offset:], p)
    bf.offset += n
    return n, nil
}

func (bf *BufferedFile) Flush() error {
    if bf.offset == 0 {
        return nil
    }
    _, err := bf.File.Write(bf.buffer[:bf.offset])
    bf.offset = 0
    return err
}

func (bf *BufferedFile) Close() error {
    bf.mu.Lock()
    defer bf.mu.Unlock()
    
    if err := bf.Flush(); err != nil {
        bf.File.Close()
        return err
    }
    return bf.File.Close()
}
```

Here the `BufferedFile` type embeds `*os.File`, promoting all of its methods to `BufferedFile`'s method set. When a method like `Read` is invoked on a `BufferedFile`, and no explicit `Read` implementation exists, the compiler resolves the call to the embedded `*os.File`'s `Read` method. Methods that are explicitly defined, such as `Write` and `Close`, override the promoted methods through simple name precedence, allowing selective interception of behavior while delegating the remainder to the embedded type.

Method receivers determine addressability and mutability semantics. A value receiver operates on a copy of the receiver value, making it safe for concurrent invocation but preventing mutation of the original value. A pointer receiver operates on the original value through indirection, enabling mutation but requiring careful synchronization in concurrent contexts. The distinction surfaces in interface satisfaction:

```go
package geometry

import "math"

type Point struct {
    X, Y float64
}

func (p Point) Distance() float64 {
    return math.Sqrt(p.X*p.X + p.Y*p.Y)
}

func (p *Point) Scale(factor float64) {
    p.X *= factor
    p.Y *= factor
}

type Scaler interface {
    Scale(factor float64)
}

func TestMethodSets() {
    p := Point{3, 4}
    
    // p.Distance() works: Point has Distance in its value method set
    _ = p.Distance()
    
    // p.Scale(2) works: compiler takes address automatically
    p.Scale(2)
    
    // But interface assignment reveals the asymmetry:
    // var s Scaler = p    // COMPILE ERROR: Point does not implement Scaler
    var s Scaler = &p   // OK: *Point implements Scaler
    s.Scale(0.5)
}
```

The method set rules dictate that `Point` has `Distance` in its method set, while only `*Point` has `Scale`. When assigning `p` directly to a `Scaler` interface, the compiler rejects the operation because creating a pointer to an unnamed temporary would violate Go's addressability guarantees. Taking the address explicitly (`&p`) produces a pointer value that satisfies the interface, as `*Point`'s method set includes both `Distance` (promoted from `Point`) and `Scale`.

Type assertions enable runtime recovery of concrete types from interface values:

```go
package network

import (
    "io"
    "net"
)

type Conn interface {
    io.ReadWriter
    io.Closer
}

func SetReadBuffer(c Conn, bytes int) error {
    // Type assertion with comma-ok idiom
    if tc, ok := c.(*net.TCPConn); ok {
        return tc.SetReadBuffer(bytes)
    }
    // Fallback for types that don't support buffer sizing
    return nil
}

func HandleConnection(c Conn) {
    // Type switch for multiple concrete types
    switch v := c.(type) {
    case *net.TCPConn:
        v.SetKeepAlive(true)
    case *net.UDPConn:
        v.SetReadBuffer(65536)
    case *net.UnixConn:
        // Unix domain socket specific logic
    default:
        // Generic connection handling
    }
}
```

Type assertions of the form `v, ok := i.(T)` return the concrete value `v` of type `T` and a boolean `ok` indicating success. If the assertion fails and the comma-ok form is not used, the operation panics. Type switches extend this pattern to discriminate among multiple concrete types, binding each case's variable to the asserted type within that case's scope.

The empty interface `interface{}` (or its modern alias `any`) specifies zero methods, making it satisfied by every type. This universal container enables generic data structures and reflection-based serialization but sacrifices compile-time type safety:

```go
package container

type Cache struct {
    data map[string]interface{}
}

func (c *Cache) Store(key string, value interface{}) {
    c.data[key] = value
}

func (c *Cache) Load(key string) (interface{}, bool) {
    v, ok := c.data[key]
    return v, ok
}

func (c *Cache) LoadInt(key string) (int, bool) {
    v, ok := c.data[key]
    if !ok {
        return 0, false
    }
    i, ok := v.(int)
    return i, ok
}
```

Before Go 1.18's introduction of type parameters, `interface{}` served as the only mechanism for writing container types that operated on arbitrary element types. The resulting API requires explicit type assertions at every extraction point, pushing type safety checking to runtime and burdening callers with error handling. Modern Go code should prefer type parameters for compile-time generic data structures, reserving `any` for truly heterogeneous collections or when interfacing with reflection-based libraries.

Interface composition through embedding enables fine-grained capability expression:

```go
package codec

import "io"

type Encoder interface {
    Encode(v interface{}) error
}

type Decoder interface {
    Decode(v interface{}) error
}

type Codec interface {
    Encoder
    Decoder
}

type Flusher interface {
    Flush() error
}

type FlushingEncoder interface {
    Encoder
    Flusher
}

func EncodeAndFlush(e Encoder, v interface{}) error {
    if err := e.Encode(v); err != nil {
        return err
    }
    // Capability detection through type assertion
    if f, ok := e.(Flusher); ok {
        return f.Flush()
    }
    return nil
}
```

This pattern allows functions to accept minimal interface contracts while opportunistically exploiting additional capabilities when present. The `EncodeAndFlush` function requires only an `Encoder`, but if the concrete type also implements `Flusher`, it invokes the flush operation. This design enables extensibility without forcing all implementations to support optional features or polluting the primary interface with methods that many implementations would stub out.

## 3. High-Performance Optimization & Failure Modes

Interface dispatch introduces indirection that the compiler cannot always devirtualize. Each method invocation through an interface value requires loading the `itab` pointer, indexing into the function table, and performing an indirect call. Modern Go compilers apply intra-procedural devirtualization when the concrete type can be proven through static analysis, but cross-package boundaries and function call chains defeat this optimization. Performance-critical code paths should measure whether interface abstraction imposes unacceptable overhead and consider concrete type parameters or monomorphization strategies when dispatch costs dominate.

The nil interface pitfall manifests when error handling returns typed nil pointers:

```go
package service

import "errors"

type DatabaseError struct {
    Query string
    Err   error
}

func (e *DatabaseError) Error() string {
    return e.Query + ": " + e.Err.Error()
}

func QueryUser(id int) (*User, error) {
    var dbErr *DatabaseError
    
    // Some error condition
    if id < 0 {
        dbErr = &DatabaseError{
            Query: "SELECT * FROM users WHERE id = ?",
            Err:   errors.New("negative ID"),
        }
        return nil, dbErr
    }
    
    // Success case: dbErr is nil
    return &User{ID: id}, dbErr
}

func main() {
    u, err := QueryUser(10)
    
    // BUG: err is non-nil even though dbErr was nil!
    // The interface contains (*DatabaseError, nil)
    if err != nil {
        // This branch executes unexpectedly
        panic(err) // panics with nil pointer dereference in Error()
    }
}
```

The function returns `dbErr` of type `*DatabaseError`, which is `nil` in the success case. However, assigning a typed nil pointer to an interface creates an interface value with a non-nil type descriptor and a nil data pointer. The subsequent `err != nil` check evaluates to true, and attempting to call methods on the nil pointer panics. The fix requires returning an untyped nil on success paths:

```go
func QueryUser(id int) (*User, error) {
    if id < 0 {
        return nil, &DatabaseError{
            Query: "SELECT * FROM users WHERE id = ?",
            Err:   errors.New("negative ID"),
        }
    }
    return &User{ID: id}, nil
}
```

Alternatively, test the concrete error value for nil before returning:

```go
func QueryUser(id int) (*User, error) {
    var dbErr *DatabaseError
    
    if id < 0 {
        dbErr = &DatabaseError{
            Query: "SELECT * FROM users WHERE id = ?",
            Err:   errors.New("negative ID"),
        }
    }
    
    if dbErr != nil {
        return nil, dbErr
    }
    return &User{ID: id}, nil
}
```

Interface values holding large concrete types can induce heap allocation and garbage collection pressure. When a concrete value larger than a pointer is assigned to an interface, the runtime allocates heap memory to hold the value and stores the allocation pointer in the interface's data field. For performance-critical code that assigns small structs to interfaces repeatedly, storing pointers to the structs rather than the structs themselves eliminates the per-assignment allocation:

```go
package metrics

type Metric struct {
    Name  string
    Value float64
    Tags  map[string]string
}

func RecordValueSemantics(m Metric) {
    var i interface{} = m // Heap allocation if Metric exceeds pointer size
    processMetric(i)
}

func RecordPointerSemantics(m *Metric) {
    var i interface{} = m // No allocation, stores pointer directly
    processMetric(i)
}
```

Profiling with `go test -bench . -benchmem` reveals the allocation difference. Production metrics pipelines that process millions of events per second must carefully manage this allocation pattern to avoid saturating the garbage collector.

Embedding introduces name collision risks when multiple embedded types define methods or fields with identical names. The compiler resolves ambiguity through depth-first search with tie-breaking by declaration order, but relying on these rules produces fragile code. Explicit forwarding methods eliminate ambiguity:

```go
package ambiguous

type A struct{}

func (a A) Method() string { return "A" }

type B struct{}

func (b B) Method() string { return "B" }

type Composite struct {
    A
    B
}

func (c Composite) CallAMethod() string {
    return c.A.Method()
}

func (c Composite) CallBMethod() string {
    return c.B.Method()
}
```

The `Composite` type does not have `Method` promoted to its method set because both `A` and `B` define it, creating an ambiguity. Explicit forwarding methods `CallAMethod` and `CallBMethod` disambiguate the intent.

Interface segregation improves testability and modularity. Functions that accept large interfaces force test doubles to implement many methods, most of which are irrelevant to the test case. Defining narrow interfaces at the point of use inverts the dependency:

```go
package processor

import "io"

// Bad: Accepts a large interface, hard to test
func ProcessData(db *sql.DB) error {
    // Uses only one method of *sql.DB
    rows, err := db.Query("SELECT * FROM data")
    // ...
}

// Good: Defines minimal interface at point of use
type Queryer interface {
    Query(query string, args ...interface{}) (*sql.Rows, error)
}

func ProcessDataWithInterface(q Queryer) error {
    rows, err := q.Query("SELECT * FROM data")
    // ...
}
```

Test code can now provide a minimal mock that implements only `Query`, avoiding the complexity of mocking the entire `*sql.DB` surface area.

Type assertion failure modes require deliberate handling. The comma-ok idiom prevents panics but introduces branching that may complicate control flow. When a type assertion must succeed for program correctness, omitting the boolean return produces a panic with a clear error message rather than silently propagating incorrect state. Consider the semantics carefully: is the absence of the expected type a recoverable error or a programming invariant violation?

Interface comparison semantics depend on the comparability of the concrete type. Two interface values are equal if they hold the same concrete type and that type's values compare equal. If the concrete type is not comparable (e.g., slices, maps, functions), comparing interface values holding those types panics at runtime. Defensive code should avoid storing non-comparable types in interfaces that may be used as map keys or in equality comparisons, or explicitly handle the panic through recovery if such usage is unavoidable.

The implicit satisfaction model enables evolutionary design but complicates interface discovery. Unlike languages with explicit `implements` declarations, Go provides no compiler-enforced documentation of which interfaces a type satisfies. Developers rely on static analysis tools like `go doc` and IDE integrations to identify interface implementations. Documenting interface satisfaction explicitly in comments aids maintainability:

```go
package storage

import "io"

// FileStore implements io.Reader, io.Writer, io.Closer, and io.Seeker.
type FileStore struct {
    // ...
}
```

Compile-time interface satisfaction checks can be enforced through assignment to blank identifiers:

```go
var (
    _ io.Reader = (*FileStore)(nil)
    _ io.Writer = (*FileStore)(nil)
    _ io.Closer = (*FileStore)(nil)
    _ io.Seeker = (*FileStore)(nil)
)
```

These declarations force the compiler to verify that `*FileStore` satisfies the specified interfaces without allocating any variables. If the type fails to implement a method, compilation fails with a clear diagnostic.

Interface-driven architecture in production systems manifests in layered designs where each layer depends only on the abstractions defined by the layer below, not on concrete implementations. A typical web service might define repository interfaces in the domain layer, implemented by concrete types in the infrastructure layer, with the application layer depending only on the interfaces. This structure enables testing domain logic with in-memory fakes, swapping database implementations without changing business logic, and evolving layers independently as long as interface contracts remain stable. The cost is additional indirection and the cognitive overhead of tracking which concrete types satisfy which interfaces across module boundaries, but the decoupling benefits outweigh these costs in systems that evolve over years and require isolated testing of complex subsystems.
