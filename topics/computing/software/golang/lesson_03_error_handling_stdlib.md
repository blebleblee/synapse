# Lesson 3: Error Handling Patterns, Context, Standard Library

## 1. First-Principles Intuition & Invariants

Go's error handling model represents a deliberate rejection of exception-based control flow in favor of explicit error values as first-class return data. Where languages like Java, Python, and C++ employ exception mechanisms that unwind the call stack through dynamically dispatched catch blocks, Go treats errors as ordinary values returned alongside successful results. This design choice stems from a fundamental philosophical position: errors are not exceptional circumstances requiring special runtime machinery, but rather predictable outcomes of operations that callers must consciously handle at each invocation site.

The consequences of this design permeate Go's semantics. Every function that can fail returns an error value—typically as the final return parameter—forcing callers to make an explicit decision about error propagation, recovery, or termination. This eliminates the hidden control flow paths that exceptions introduce, where any statement might invisibly transfer control to a distant handler based on dynamic type matching. In Go's model, the program's control flow graph remains statically analyzable: every branch point is syntactically visible as an `if err != nil` check or equivalent conditional.

At the type level, the `error` interface establishes the contract for all error values through a single method signature: `Error() string`. This minimal interface allows any type implementing a string representation to serve as an error, enabling rich semantic information to travel through error returns without prescribing a rigid hierarchy. The standard library's `errors` package provides `errors.New(string)` and `fmt.Errorf(format, args...)` for constructing simple error values, while custom types can embed additional context—stack traces, error codes, wrapped causes—while remaining compatible with the universal `error` interface.

The invariant that emerges from this design is straightforward yet profound: error handling is never implicit. There are no uncaught exceptions, no surprise panics from library code under normal failure conditions, and no hidden resource cleanup logic triggered by stack unwinding. Instead, cleanup must be explicitly managed through `defer` statements that execute in LIFO order during function exit, whether that exit occurs normally or via an early return after an error check. This places the burden of correctness on the programmer—a deliberate trade-off prioritizing transparency and local reasoning over automatic safety nets.

Go does provide a panic-recover mechanism for truly exceptional conditions—unrecoverable errors like out-of-memory, nil pointer dereferences, or explicit `panic()` calls—but idiomatic Go code reserves panics for programming bugs and catastrophic failures, not operational errors. A database connection timeout, a missing file, or invalid user input are all expected failure modes that should flow through explicit error returns, not panic the entire process. This distinction shapes how robust Go programs are structured: panics represent broken invariants requiring immediate attention, while errors represent the normal spectrum of outcomes that business logic must accommodate.

The `context` package extends this error-centric philosophy to concurrent and distributed systems by providing a standardized mechanism for propagating cancellation signals, deadlines, and request-scoped values across goroutine boundaries and RPC calls. A `context.Context` carries a cancellation channel, an optional deadline, and a thread-safe value store, enabling parent operations to cancel descendant work without shared mutable state or complex synchronization primitives. When a context is cancelled—either explicitly via a cancel function or implicitly when its deadline expires—any blocking operation receiving that context should immediately cease work and return a context error, allowing graceful shutdown cascades through the entire call graph.

This design creates a powerful invariant for distributed systems: every long-running operation or blocking I/O call should accept a `context.Context` as its first parameter and respect cancellation signals by periodically checking `ctx.Done()` or passing the context to lower-level operations that perform the check. Database drivers, HTTP clients, and network listeners throughout the standard library honor this contract, making timeout enforcement and request cancellation a composable, library-level concern rather than ad-hoc application logic. The result is a uniform pattern where resource leaks and unbounded latency become architectural failures rather than implementation oversights.

The standard library embodies these principles through consistent API design across packages. Functions that can fail return `(result, error)` tuples. Functions that perform I/O or can block accept contexts. Cleanup logic uses `defer` with explicit error checks in defer functions when necessary. This uniformity reduces cognitive load: once a programmer internalizes the error-checking pattern and context propagation rules, these patterns recur identically across file I/O, network operations, database queries, and HTTP handlers. The lack of language-level exceptions means there are no invisible control flow edges to track, no surprise error types to catch, and no implicit conversions between error representations.

## 2. Core Architecture & Mechanics

The `error` interface itself is the foundation of Go's error system, defined in the `builtin` package as:

```go
type error interface {
    Error() string
}
```

Any type implementing this method satisfies the interface and can be returned as an error. The standard library's `errors` package provides the simplest concrete implementation through `errors.errorString`, an unexported struct wrapping a string. When you call `errors.New("disk full")`, the returned error is a pointer to this struct, ensuring that identical error strings produce distinct error values—each allocation creates a unique pointer, so `errors.New("x") != errors.New("x")` even though their string representations match. This pointer semantics enables sentinel errors—exported package-level error variables like `io.EOF` or `sql.ErrNoRows`—to be reliably compared with `==` for control flow decisions.

The `fmt.Errorf` function extends this by supporting format strings with the special `%w` verb, introduced in Go 1.13 to standardize error wrapping. When you write `fmt.Errorf("failed to open config: %w", err)`, the returned error wraps the original `err` while adding contextual information. This wrapping relationship is formalized through the `Unwrap() error` method: any error type implementing this method participates in the error chain, allowing inspection tools to traverse from the outermost context down to the root cause. The `errors.Is` and `errors.As` functions exploit this chain to provide robust error inspection without fragile string matching.

The `errors.Is(err, target)` function walks the error chain—repeatedly calling `Unwrap()` if present—comparing each error against `target` using equality checks or custom `Is(error) bool` methods. This allows robust sentinel comparison even when errors have been wrapped multiple layers deep. Consider a typical error propagation chain:

```go
func readConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("readConfig: %w", err)
    }
    // ... parse data ...
}

func initApp() error {
    cfg, err := readConfig("/etc/app.conf")
    if err != nil {
        return fmt.Errorf("initApp: %w", err)
    }
    // ... use cfg ...
}

func main() {
    if err := initApp(); err != nil {
        if errors.Is(err, os.ErrNotExist) {
            log.Println("Config file missing, using defaults")
            return
        }
        log.Fatalf("Fatal: %v", err)
    }
}
```

Here, `os.ErrNotExist` might be wrapped twice—once in `readConfig`, again in `initApp`—yet `errors.Is` successfully identifies it by unwrapping the chain. Without this mechanism, the caller would need to perform brittle string matching or manually unwrap errors, breaking encapsulation when intermediate layers add context.

The `errors.As(err, &target)` function provides type-based extraction, traversing the chain until it finds an error assignable to the target pointer type. This enables recovering rich error details from custom error types while preserving wrapping chains:

```go
type NetworkError struct {
    Op   string
    Addr string
    Err  error
}

func (e *NetworkError) Error() string {
    return fmt.Sprintf("%s %s: %v", e.Op, e.Addr, e.Err)
}

func (e *NetworkError) Unwrap() error { return e.Err }

// Later, in error handling code:
var netErr *NetworkError
if errors.As(err, &netErr) {
    log.Printf("Network operation %s to %s failed", netErr.Op, netErr.Addr)
    // Possibly retry or fail over to different address
}
```

This pattern appears throughout production systems for extracting structured error information—HTTP status codes, database constraint violations, filesystem error codes—without coupling error handling logic to the precise wrapping structure.

The `context` package introduces a tree-structured cancellation mechanism built on channels and interface composition. The root type is:

```go
type Context interface {
    Deadline() (deadline time.Time, ok bool)
    Done() <-chan struct{}
    Err() error
    Value(key interface{}) interface{}
}
```

The `Done()` method returns a receive-only channel that closes when the context is cancelled, enabling select-based cancellation checks. The `Err()` method reports why the context was cancelled—returning `context.Canceled` for explicit cancellation or `context.DeadlineExceeded` when a timeout expires. This separation of signal (channel closure) and reason (error value) allows efficient polling in hot loops while preserving semantic information for error reporting.

Contexts form a hierarchy through four standard constructors. The `context.Background()` function returns the root context—never cancelled, no deadline, no values—serving as the top-level parent for request processing or background tasks. From any context, you can derive child contexts with additional constraints:

```go
ctx := context.Background()

// WithCancel returns a child context and a cancel function.
// Calling cancel closes the Done channel.
ctx1, cancel1 := context.WithCancel(ctx)

// WithTimeout returns a child with an absolute deadline.
// The context cancels itself when the timeout expires.
ctx2, cancel2 := context.WithTimeout(ctx, 5*time.Second)

// WithDeadline is similar but takes an explicit time.Time.
ctx3, cancel3 := context.WithDeadline(ctx, time.Now().Add(10*time.Second))

// WithValue returns a child carrying a key-value pair.
// Lookups walk the chain toward the root.
ctx4 := context.WithValue(ctx, "requestID", "abc-123")
```

The critical invariant is that cancelling a parent context cancels all descendants, but cancelling a child never affects its parent or siblings. This enables scoped cancellation: an HTTP handler can create a request-scoped context, spawn worker goroutines that respect that context, and ensure all workers terminate when the request completes or times out, without affecting unrelated requests.

The internal implementation relies on a goroutine spawned by `WithTimeout` and `WithDeadline` that sleeps until the deadline, then calls the cancel function. This goroutine holds a reference to the context, preventing garbage collection until either the deadline fires or the cancel function is called. This is why the cancel function must be called even when the timeout hasn't expired—failing to call cancel leaks the goroutine and its associated resources. Idiomatic Go always pairs context creation with a deferred cancel call:

```go
func processRequest(parent context.Context) error {
    ctx, cancel := context.WithTimeout(parent, 10*time.Second)
    defer cancel() // Ensures cleanup regardless of return path

    result, err := expensiveOperation(ctx)
    if err != nil {
        return err
    }
    return saveResult(ctx, result)
}
```

The `context.Value` method provides request-scoped storage for values that cross API boundaries—authentication tokens, trace IDs, or request-scoped loggers. Values are stored in an immutable linked list: each `WithValue` call creates a new context node pointing to its parent, and `Value(key)` lookups walk the chain from child to root until a matching key is found. This makes value storage allocation-free (no map mutations) and goroutine-safe (no shared state), but lookups are O(n) in the chain depth. Best practice restricts context values to metadata that naturally spans the entire request lifetime, avoiding the temptation to use contexts as a general-purpose parameter-passing mechanism.

Select-based cancellation checking forms the operational core of context-aware code. A typical pattern for periodic work checks the context in each iteration:

```go
func worker(ctx context.Context, data <-chan Item) {
    for {
        select {
        case <-ctx.Done():
            log.Println("Worker cancelled:", ctx.Err())
            return
        case item, ok := <-data:
            if !ok {
                return // Channel closed
            }
            process(item)
        }
    }
}
```

This select statement blocks until either the context is cancelled (channel closure on `ctx.Done()`) or data arrives. If the context cancels first, the goroutine immediately returns, preventing work on stale requests. For blocking operations without channel integration, the context must be explicitly passed down:

```go
func fetchData(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return io.ReadAll(resp.Body)
}
```

The `http.NewRequestWithContext` function ties the HTTP request lifetime to the context, ensuring that if `ctx` is cancelled during the request, the underlying network connection is closed and `Do` returns `context.Canceled`. This pattern recurs across the standard library: `sql.DB.QueryContext`, `exec.CommandContext`, `net.Dialer.DialContext`, and many others accept contexts as their first parameter, propagating cancellation into platform-level I/O operations.

## 3. High-Performance Optimization & Failure Modes

Error handling performance in Go depends critically on allocation behavior and control flow locality. The zero-allocation path for common errors uses sentinel variables: an exported `var ErrNotFound = errors.New("not found")` allocates once during package initialization, and all subsequent returns share that single pointer. Comparing errors with `==` or `errors.Is` then becomes a pointer comparison—a single register load and comparison instruction—making error checks as cheap as integer conditionals.

However, when errors carry dynamic context via `fmt.Errorf`, each error construction allocates. A high-throughput service processing millions of requests per second must minimize error allocations in hot paths. One technique is pre-allocated error pools with context added only in exceptional cases:

```go
var (
    ErrRateLimited   = errors.New("rate limited")
    ErrInvalidInput  = errors.New("invalid input")
    ErrQuotaExceeded = errors.New("quota exceeded")
)

func handleRequest(ctx context.Context, req *Request) error {
    if !req.Validate() {
        return ErrInvalidInput // Zero-cost sentinel return
    }
    if !rateLimit.Allow() {
        // Only allocate when returning to client for logging
        return fmt.Errorf("request %s: %w", req.ID, ErrRateLimited)
    }
    // ... process request ...
}
```

For errors that require rich metadata, custom error types avoid repeated allocations through struct reuse or sync pools:

```go
type RequestError struct {
    Code    int
    Message string
    Details map[string]interface{}
}

func (e *RequestError) Error() string {
    return fmt.Sprintf("%d: %s", e.Code, e.Message)
}

var requestErrorPool = sync.Pool{
    New: func() interface{} { return &RequestError{Details: make(map[string]interface{})} },
}

func borrowRequestError(code int, msg string) *RequestError {
    e := requestErrorPool.Get().(*RequestError)
    e.Code = code
    e.Message = msg
    clear(e.Details) // Reset map without reallocation
    return e
}

func returnRequestError(e *RequestError) {
    requestErrorPool.Put(e)
}
```

This pattern trades some ergonomic convenience—callers must remember to return errors to the pool—for significant allocation reduction in error-heavy workloads. Profiling with `pprof` heap profiles will reveal whether error allocations dominate; if `runtime.mallocgc` samples concentrate in error construction, pooling or sentinel reuse becomes worthwhile.

Context propagation overhead centers on the interface method dispatch for `Done()` and `Err()` calls. Each context method involves an indirect function call through the interface vtable, but modern CPUs predict these branches accurately once hot paths stabilize. The larger cost is goroutine scheduling when `WithTimeout` spawns its timer goroutine. For extremely latency-sensitive paths processing thousands of sub-millisecond operations, creating a new context per operation can introduce measurable overhead. The solution is context reuse within a single request:

```go
func handleBatch(ctx context.Context, items []Item) error {
    // Create timeout context once for entire batch
    batchCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    for _, item := range items {
        // Reuse batchCtx across iterations
        if err := processItem(batchCtx, item); err != nil {
            return fmt.Errorf("item %v: %w", item.ID, err)
        }
    }
    return nil
}
```

This amortizes the timer goroutine cost across all items. For even tighter loops, some high-frequency systems precompute deadlines and manually check `time.Now()` against them, avoiding context overhead entirely:

```go
func processHighFrequency(items []Item) error {
    deadline := time.Now().Add(5 * time.Second)
    for _, item := range items {
        if time.Now().After(deadline) {
            return context.DeadlineExceeded
        }
        if err := process(item); err != nil {
            return err
        }
    }
    return nil
}
```

This trades the composability of contexts—no automatic cancellation propagation—for raw throughput when the caller controls the entire execution context.

Failure modes in error handling cluster around three categories: ignored errors, mishandled wrapping chains, and context misuse. Ignored errors manifest as unchecked error returns—`io.Copy(dst, src)` without inspecting the returned error can silently truncate data if the write fails partway through. The `go vet` tool and third-party linters like `errcheck` catch many instances, but the fundamental discipline is cultural: every error return must be either checked and handled or explicitly discarded with a comment explaining why the error is irrelevant.

Mishandled wrapping chains typically involve losing error context through naive string formatting. Writing `fmt.Errorf("failed: %v", err)` instead of `fmt.Errorf("failed: %w", err)` breaks the chain, preventing `errors.Is` and `errors.As` from traversing to the root cause. This forces callers to resort to substring matching—`strings.Contains(err.Error(), "not found")`—which breaks when intermediate messages change. The corrected pattern always uses `%w` when wrapping operational errors, reserving `%v` for truly terminal error formatting in logs where no further programmatic inspection will occur.

Context misuse falls into several antipatterns. Storing contexts in struct fields creates lifetime mismatches: a context scoped to a single request outlives its purpose if stored in a long-lived server object, causing cancellation signals to fire unexpectedly or, worse, never fire because the context is replaced before cancellation. The idiomatic pattern passes contexts as function parameters, ensuring lexical scope matches operational scope. Similarly, passing `context.Background()` when a parent context exists defeats cancellation propagation—an HTTP handler that creates a background context for database calls isolates those calls from request cancellation, allowing them to continue indefinitely even after the client disconnects.

Context value misuse treats contexts as a dumping ground for configuration or dependency injection, leading to implicit coupling between layers. A function that silently retrieves a database handle from `ctx.Value("db")` makes its dependencies invisible in the signature, hindering testing and violating explicit dependency principles. Reserve context values for truly cross-cutting concerns—trace IDs, authentication credentials, request deadlines—that every layer needs but no single layer owns.

Deadlock potential exists when context cancellation and channel communication interact incorrectly. Consider this flawed worker pattern:

```go
func worker(ctx context.Context, in <-chan int, out chan<- int) {
    for val := range in {
        select {
        case <-ctx.Done():
            return
        case out <- val * 2:
        }
    }
}
```

If the downstream consumer of `out` stops reading but the context is not cancelled, the worker goroutine blocks indefinitely on the `out <- val` send. The corrected pattern incorporates both cancellation and send in the same select:

```go
func worker(ctx context.Context, in <-chan int, out chan<- int) {
    for val := range in {
        select {
        case <-ctx.Done():
            return
        case out <- val * 2:
        }
    }
}
```

But even this has subtleties: if `in` never closes and `ctx` never cancels, the goroutine leaks. Robust designs ensure that contexts and channels have matching lifetimes, typically by tying worker goroutines to a supervisor that cancels contexts and closes input channels in tandem during shutdown.

Profiling error-heavy code paths uses `pprof` CPU and allocation profiles to identify bottlenecks. Run the service under load with profiling enabled:

```go
import _ "net/http/pprof"

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    // ... start service ...
}
```

Then capture profiles with `go tool pprof http://localhost:6060/debug/pprof/heap` for allocation-heavy error construction or `go tool pprof http://localhost:6060/debug/pprof/profile` for CPU time in error checking. The flame graph will reveal whether error handling appears in hot paths, guiding optimization decisions. For most services, error handling overhead is negligible compared to I/O and business logic, but for in-memory data structures processing millions of operations per second—caches, routers, parsers—error allocation elimination becomes measurable.

Testing error paths demands deliberate injection. The standard library's `testing` package provides no built-in error injection, so production code must design for testability. One pattern injects errors through interfaces:

```go
type Store interface {
    Get(ctx context.Context, key string) ([]byte, error)
}

type FailingStore struct {
    Err error
}

func (f *FailingStore) Get(ctx context.Context, key string) ([]byte, error) {
    return nil, f.Err
}

func TestErrorHandling(t *testing.T) {
    store := &FailingStore{Err: errors.New("disk failure")}
    svc := NewService(store)
    if err := svc.Process(context.Background(), "key"); err == nil {
        t.Fatal("Expected error, got nil")
    }
}
```

This isolates error handling logic from I/O dependencies, enabling unit tests to verify that every error return path behaves correctly—rollback transactions, release locks, log diagnostics—without provisioning real databases or filesystems.

Context testing requires controlled deadline expiration. The `context.WithTimeout` function uses real wall-clock time, making tests nondeterministic. Production code that needs testable timeouts should accept both a context and an explicit `time.Duration`, allowing tests to inject zero or very short durations:

```go
func FetchWithRetry(ctx context.Context, url string, timeout time.Duration) error {
    for attempt := 0; attempt < 3; attempt++ {
        reqCtx, cancel := context.WithTimeout(ctx, timeout)
        defer cancel()
        if err := fetch(reqCtx, url); err == nil {
            return nil
        }
    }
    return errors.New("max retries exceeded")
}

func TestFetchTimeout(t *testing.T) {
    // Inject 1ms timeout to force immediate expiration
    err := FetchWithRetry(context.Background(), "http://example.com", time.Millisecond)
    if !errors.Is(err, context.DeadlineExceeded) {
        t.Errorf("Expected DeadlineExceeded, got %v", err)
    }
}
```

This pattern separates business logic (retry loop) from clock dependency (timeout duration), making tests fast and deterministic while preserving production behavior.

The Go 1.20 introduction of `errors.Join` enables combining multiple errors into a single error value that unwraps to all constituent errors. This addresses a long-standing gap: operations that fail in multiple independent ways—closing multiple file descriptors, shutting down multiple network listeners—can now return a single error capturing all failures:

```go
func Shutdown(ctx context.Context, listeners []net.Listener) error {
    var errs []error
    for _, ln := range listeners {
        if err := ln.Close(); err != nil {
            errs = append(errs, err)
        }
    }
    return errors.Join(errs...)
}
```

The returned error satisfies `errors.Is` for any of the wrapped errors, enabling callers to check for specific failure modes without enumerating all possible errors. This pattern is particularly valuable in cleanup paths where partial failures should not prevent attempting subsequent cleanups.

Practical production services balance explicit error checking with operational simplicity. A microservice handling HTTP requests might structure its error handling as a layered pipeline: business logic returns rich errors with context, middleware unwraps and classifies errors into HTTP status codes, and observability layers extract structured fields for logging and metrics. This separation ensures that business logic remains decoupled from HTTP concerns while still providing actionable diagnostics at the API boundary. The `error` interface's minimal contract enables this flexibility—errors can carry whatever structured information the application needs, yet remain interoperable across package boundaries.
