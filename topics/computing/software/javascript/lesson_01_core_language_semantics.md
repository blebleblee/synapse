# Lesson 1: Core Language Semantics

## 1. First-Principles Intuition & Invariants

JavaScript's core semantics emerge from a profound tension between its original design as a lightweight scripting language for browser manipulation and its current role as a general-purpose systems language powering server infrastructure, embedded systems, and distributed applications. Understanding JavaScript at a systems level requires dismantling the comfortable abstractions most practitioners rely upon and reconstructing the language from its fundamental execution model: a single-threaded, event-driven runtime with automatic memory management, dynamic typing through tagged unions, and prototype-based object composition.

At its foundation, JavaScript implements a specification-driven abstract machine defined by ECMA-262. Every observable behavior—from type coercion rules to property lookup chains—derives from algorithmic steps enumerated in this specification. Unlike statically-typed systems languages where types constrain values at compile time, JavaScript operates on dynamically-typed values where each runtime value carries both data and a type tag. This design choice cascades through every semantic layer: operators must perform runtime type discrimination, property access must traverse prototype chains at execution time, and function invocation must construct execution contexts with dynamic scope bindings.

The central invariant governing all JavaScript execution is the single-threaded event loop model with run-to-completion semantics. No JavaScript code executing on the main thread can be preempted by other JavaScript code. This architectural constraint eliminates data races and lock contention within JavaScript code itself, but introduces profound implications for how asynchronous operations integrate with the language. Every potentially-blocking operation—network I/O, file access, timer expiration—must delegate to native runtime facilities and signal completion through the event queue. The JavaScript thread pulls events from this queue only when the current task completes, processing each callback to completion before considering the next queued event.

Type coercion represents JavaScript's most controversial semantic domain because it embodies a fundamental trade-off: maximizing expressiveness and minimizing boilerplate at the cost of introducing subtle correctness hazards. When an operator encounters operands of incompatible types, the language specifies deterministic coercion algorithms rather than raising type errors. These algorithms follow from the language's origin as a weakly-typed scripting environment where implicit conversions reduce friction for non-expert programmers. However, the coercion rules encode non-obvious precedence: the `+` operator prefers string concatenation over numeric addition when either operand is a string, while comparison operators apply numeric coercion with asymmetric special cases for `null` and `undefined`. These rules are not arbitrary; they reflect specific design decisions made during JavaScript's initial ten-day implementation period that became locked in by backward compatibility requirements.

Prototypal inheritance diverges fundamentally from the class-based inheritance models that dominate systems programming languages. Where C++ and Rust implement inheritance through vtable pointers and trait dispatch at compile time, JavaScript implements object composition through runtime prototype chain traversal. Every object carries an internal `[[Prototype]]` slot referencing another object (or `null` for the chain terminus). Property access that fails to find a property on the object itself recursively searches the prototype chain until finding the property or reaching `null`. This delegation model enables powerful patterns: objects can share behavior without copying method implementations, prototype chains can be modified at runtime to change object behavior, and objects can serve as prototypes for other objects without requiring class declarations. The cost appears in property access performance—each failed property lookup traverses potentially long prototype chains—and in the cognitive overhead of reasoning about prototype mutation and shadowing.

Execution contexts and scope chains form the semantic foundation for variable binding and function invocation. When JavaScript invokes a function, the runtime constructs an execution context encapsulating the function's lexical environment (variable bindings), the `this` binding, and the reference to the outer lexical environment. Lexical environments form a linked list terminating at the global environment, and identifier resolution walks this chain from innermost to outermost scope. Closures emerge naturally from this model: when a function object is created, it captures a reference to the lexical environment in which it was defined. If that function outlives the execution context that created it, the captured environment remains reachable through the closure, preventing garbage collection and allowing the function to access outer variables even after the outer function returns.

The event loop mechanism governs how JavaScript integrates synchronous execution with asynchronous operations. The runtime maintains distinct queues for different event priorities: microtasks (Promise resolution callbacks, `queueMicrotask` entries) and macrotasks (timers, I/O callbacks, UI events). After each macrotask completes, the runtime drains the entire microtask queue before pulling the next macrotask. This priority inversion enables Promise-based code to achieve deterministic ordering: a resolved Promise's `.then()` callback executes before any pending timer or I/O callback, even if that timer has already expired. Understanding this queuing discipline is essential for reasoning about execution order in asynchronous code and for diagnosing performance pathologies where long microtask chains starve macrotask processing.

## 2. Core Architecture & Mechanics

JavaScript's type system builds upon seven primitive types (`Undefined`, `Null`, `Boolean`, `Number`, `String`, `Symbol`, `BigInt`) and one reference type (`Object`). Modern engines implement values using NaN-boxing or pointer tagging to encode type information within the value itself, avoiding separate type tag storage. A 64-bit IEEE 754 double-precision float has specific bit patterns that represent NaN (Not-a-Number), and engines exploit the fact that only one canonical NaN representation is needed. The remaining NaN encodings—billions of them—become available to encode pointers, small integers, and type tags. This encoding enables passing values in registers without heap allocation for immediate values like small integers, booleans, and special constants.

Type coercion algorithms follow strict specification rules that cascade through operator evaluation. Consider the abstract equality operator `==`, which implements the following decision tree for operands `x` and `y`:

```text
If Type(x) === Type(y): perform strict equality check
If x is null and y is undefined (or vice versa): return true
If x is Number and y is String: coerce y to Number, retry
If x is String and y is Number: coerce x to Number, retry
If x is Boolean: coerce x to Number, retry
If y is Boolean: coerce y to Number, retry
If x is Object and y is primitive: coerce x to primitive via ToPrimitive, retry
If y is Object and x is primitive: coerce y to primitive via ToPrimitive, retry
Otherwise: return false
```

The `ToPrimitive` abstract operation attempts to convert an object to a primitive value by invoking the object's `[Symbol.toPrimitive]` method (if present), then falling back to `valueOf()` and `toString()` in a hint-dependent order. This recursive coercion system produces non-obvious results: `[] == ![]` evaluates to `true` because the right side coerces to `false`, then `0`, while the left side coerces to the empty string, then `0`. These behaviors are deterministic and testable, but they violate mathematical properties like transitivity, making equality comparison unsuitable for sorting or maintaining invariants.

Numeric coercion via `ToNumber` implements specific rules for each input type. Strings undergo decimal parsing with leading/trailing whitespace stripped, supporting exponential notation and signed values. Objects invoke `ToPrimitive` with numeric hint, then recursively coerce the resulting primitive. The special values `undefined`, `null`, `true`, and `false` map to `NaN`, `0`, `1`, and `0` respectively. Understanding these coercion paths is critical for debugging unexpected arithmetic: `"5" - "2"` yields `3` (string coercion to numbers for subtraction), while `"5" + "2"` yields `"52"` (numeric coercion to string for addition). The asymmetry stems from `+` serving double duty as both numeric addition and string concatenation, with concatenation taking precedence when either operand is a string.

Prototype chains implement the fundamental mechanism for property access and inheritance. Every object maintains an internal `[[Prototype]]` reference accessible via `Object.getPrototypeOf()` or the non-standard but widely-implemented `__proto__` accessor. Property access follows this chain until finding the property or reaching `null`:

```text
GetProperty(object, key):
  current = object
  while current !== null:
    if HasOwnProperty(current, key):
      return current[key]
    current = [[Prototype]] of current
  return undefined
```

Setting a property never traverses the prototype chain for the write operation—it always creates or updates an own property on the object itself. However, if the property exists in the prototype chain as an accessor (getter/setter) or a non-writable data property, the write may be intercepted or rejected. This asymmetry between reads (which traverse the chain) and writes (which don't) enables the shadowing pattern where a child object masks a prototype property by defining its own property with the same key.

Constructor functions and the `new` operator implement a mechanical translation of class-like patterns into prototype manipulation. When evaluating `new Constructor(args)`, the runtime performs this sequence:

```text
1. Create new object: obj = Object.create(Constructor.prototype)
2. Bind this to obj for the constructor call
3. Execute: result = Constructor.apply(obj, args)
4. If result is an object: return result
5. Otherwise: return obj
```

The critical insight is that `Constructor.prototype` becomes the prototype of instances, not `Constructor` itself. The constructor function's own prototype (typically `Function.prototype`) is irrelevant to instance prototype chains. This design enables method sharing: defining methods on `Constructor.prototype` makes them available to all instances without copying method implementations per instance.

Execution contexts form a stack-based activation record system. Each function invocation pushes a new execution context containing:

- **Lexical Environment**: A record of variable bindings and a reference to the outer environment
- **Variable Environment**: Stores `var` declarations and function declarations (distinct from lexical environment only for complex scoping like `eval` and `with`)
- **This Binding**: The value of `this` for the current execution
- **Code Reference**: The function body or script being executed

Lexical environments implement nested scope through environment record chaining. When a function is created, it captures a reference to the lexical environment active at creation time (the "outer environment reference"). Identifier resolution walks from the current environment to outer environments until finding the binding or reaching the global environment:

```text
ResolveBinding(identifier):
  env = current lexical environment
  while env !== null:
    if env.HasBinding(identifier):
      return env.GetBindingValue(identifier)
    env = env.outer environment reference
  throw ReferenceError
```

This structure enables closures: when a function object captures its creation environment, variables in that environment remain reachable even after the creating function returns. The captured environment persists in memory, maintaining variable state across invocations of the closure.

The event loop integrates synchronous JavaScript execution with asynchronous operations through a structured queuing system. The conceptual model consists of:

```text
while (true) {
  task = dequeue_next_macrotask()
  if (task === null) break
  
  execute_task(task)
  
  while (microtask_queue_not_empty()) {
    microtask = dequeue_microtask()
    execute_task(microtask)
  }
  
  if (render_required()) {
    perform_render()
  }
}
```

Macrotasks include script execution, timer callbacks (`setTimeout`, `setInterval`), I/O callbacks, and UI events. Microtasks include Promise resolution handlers (`.then`, `.catch`, `.finally`) and `queueMicrotask` callbacks. The critical invariant is that the entire microtask queue drains after each macrotask before the next macrotask begins. This ensures that Promise chains settle atomically from the perspective of macrotask execution, preventing interleaving of Promise callbacks with timer or I/O callbacks.

Promise state machines implement asynchronous control flow as first-class language primitives. A Promise exists in one of three states: pending, fulfilled, or rejected. State transitions are unidirectional and permanent—once settled (fulfilled or rejected), a Promise's state and value never change. The Promise constructor receives an executor function that provides `resolve` and `reject` callbacks:

```javascript
const promise = new Promise((resolve, reject) => {
  // Asynchronous operation
  asyncOperation((error, result) => {
    if (error) reject(error);
    else resolve(result);
  });
});
```

Calling `resolve(value)` transitions the Promise to fulfilled, while `reject(reason)` transitions to rejected. The `.then()` method registers reaction callbacks that execute when the Promise settles. If the Promise is already settled when `.then()` is called, the callback queues as a microtask immediately. This design enables composition: `.then()` returns a new Promise resolved with the callback's return value (or rejected if the callback throws), enabling method chaining and sequential asynchronous operations.

Async functions and await expressions provide syntactic sugar over Promise-based control flow. An async function always returns a Promise, wrapping non-Promise return values automatically. The `await` keyword pauses execution of the async function, queues a microtask to resume when the awaited Promise settles, and returns control to the caller. This transformation converts sequential-looking code into Promise chain composition:

```javascript
async function fetchData() {
  const response = await fetch(url);
  const data = await response.json();
  return data;
}

// Equivalent to:
function fetchData() {
  return fetch(url)
    .then(response => response.json())
    .then(data => data);
}
```

The transformation maintains the microtask queue semantics: each `await` suspension point queues the continuation as a microtask, ensuring deterministic execution order within an event loop iteration.

## 3. High-Performance Optimization & Failure Modes

JavaScript engines apply aggressive runtime optimization to overcome the performance overhead of dynamic typing and prototype chain traversal. Modern engines like V8, SpiderMonkey, and JavaScriptCore implement multi-tier compilation: an interpreter executes code initially while a profiling runtime collects type feedback, then a baseline JIT compiler generates optimized machine code for hot functions, and finally a speculative optimizing compiler generates highly-optimized code based on observed type patterns. This architecture enables engines to approach statically-typed language performance for monomorphic code paths while maintaining JavaScript's dynamic semantics.

Inline caching optimizes property access by recording observed object shapes at each call site. When accessing `obj.property`, the engine checks if the object's shape (its property layout and prototype chain) matches the cached shape. If so, the cached property offset enables direct memory access without prototype traversal or hash table lookup. Mismatches trigger shape updates and cache invalidation, degrading to slower lookup paths. Writing performance-critical code therefore requires maintaining shape consistency: adding properties in the same order across objects, avoiding property deletion, and avoiding dynamic property addition after construction. The hidden class optimization depends on predictable object evolution—engines assign objects to hidden classes based on their property set and order, enabling aggressive inlining and devirtualization.

Type specialization in optimizing compilers assumes type stability based on profiling feedback. If a function always receives numbers as arguments, the compiler generates machine code specialized for number arithmetic, eliminating type checks and unboxing operations. However, if the function later receives a string, the optimized code must deoptimize: bail out to the interpreter, reconstruct the execution state, and mark the function for recompilation with more conservative assumptions. Deoptimization is expensive—it discards compiled code and loses optimization investment. High-performance code avoids polymorphism: functions should receive consistent types across invocations, operators should encounter predictable operand types, and property access should encounter stable object shapes.

Closure allocation and capture impose memory and garbage collection overhead that becomes significant in tight loops or frequently-instantiated code paths. Each closure captures its lexical environment, and if that environment contains large data structures or references to long-lived objects, the closure prevents garbage collection of the entire environment. Performance-critical code should minimize closure allocation: hoist function definitions outside loops when possible, use bound methods sparingly, and be deliberate about what variables are captured. Event handler registration is a common closure leak source—failing to unregister event handlers leaves closures and their captured environments reachable indefinitely.

The event loop's single-threaded nature creates pathological failure modes when long-running synchronous code blocks the thread. A tight loop, expensive computation, or synchronous I/O call prevents the event loop from processing pending events, freezing UI updates, delaying timer callbacks, and blocking new I/O operations. Defensive programming requires partitioning work into chunks and yielding control back to the event loop periodically. Techniques include using `setImmediate()` or `setTimeout(0)` to break work into macrotasks, structuring computations as async iterators that yield between iterations, and offloading CPU-intensive operations to worker threads via the Web Worker or Worker Threads API.

Microtask queue starvation occurs when microtasks continuously enqueue new microtasks, preventing the event loop from reaching the next macrotask. Since the runtime drains the entire microtask queue after each macrotask, an unbounded recursive microtask enqueue pattern effectively hangs the event loop:

```javascript
function starveEventLoop() {
  Promise.resolve().then(starveEventLoop);
}
starveEventLoop(); // Never yields to macrotask queue
```

This pattern appears in real code through Promise chains that recursively generate new Promises without allowing macrotask processing. Mitigations require interspersing macrotask yields: replacing some Promise resolutions with `setImmediate()` or `setTimeout()` calls to break out of the microtask queue and allow other events to process.

Memory leaks in garbage-collected environments stem from unintentional reference retention. Common patterns include: closures capturing large objects in outer scopes, event listeners never unregistered, growing arrays or caches without bounds, and circular references between DOM nodes and JavaScript objects (in browser environments). Detecting leaks requires heap profiling: capturing heap snapshots, comparing object retention between snapshots, and tracing reference paths from GC roots to leaked objects. Modern engines implement generational garbage collection where short-lived objects are collected frequently and long-lived objects are collected rarely. Objects that survive multiple young-generation collections promote to the old generation, where collection is infrequent but expensive. High-allocation code can trigger frequent garbage collection pauses—optimizations include object pooling to reuse allocations, using typed arrays for numeric data to reduce allocation overhead, and preallocating buffers to avoid incremental growth.

Prototype pollution represents a critical security vulnerability where attackers inject properties into `Object.prototype` or other prototype objects, affecting all objects that inherit from the polluted prototype. Unsafe merging of user-provided objects can introduce properties like `__proto__` or `constructor.prototype` that modify prototype chains:

```javascript
function merge(target, source) {
  for (let key in source) {
    target[key] = source[key]; // Dangerous: allows __proto__ injection
  }
}

const userInput = JSON.parse('{"__proto__": {"isAdmin": true}}');
merge({}, userInput);
// All objects now inherit isAdmin: true
```

Mitigations require validating property names, using `Object.create(null)` for dictionary objects to avoid inheriting from `Object.prototype`, and employing safe merging libraries that explicitly deny prototype property names. The risk extends to any code that dynamically accesses object properties based on external input without validating property names against prototype pollution vectors.

Asynchronous error handling demands explicit attention because unhandled Promise rejections fail silently in many environments. When a Promise rejects and no rejection handler is attached, the error can disappear without notification. Modern environments emit `unhandledRejection` events (Node.js) or log warnings (browsers), but these are debugging aids, not error-recovery mechanisms. Production code must attach rejection handlers to every Promise chain, either through `.catch()` calls, `try/catch` blocks around `await` expressions, or global rejection handlers. Additionally, async functions that lack error handling allow exceptions to propagate as rejected Promises, potentially causing unhandled rejections in calling code that expects a resolved Promise.

Engine-specific behavior and specification ambiguities create portability hazards. While ECMA-262 defines JavaScript semantics, implementers make different optimization trade-offs and interpret specification edge cases differently. Performance characteristics vary wildly: V8's hidden class optimization behaves differently from JavaScriptCore's structure representation, property access performance varies by property name (integer indices optimize differently than string keys), and garbage collection pause characteristics differ across engines. Portable high-performance code requires profiling on target engines, avoiding reliance on unspecified behavior, and testing across multiple JavaScript runtimes to detect engine-specific assumptions.

The temporal dead zone for `let` and `const` declarations creates a failure mode absent from `var` declarations. Variables declared with `let` or `const` are hoisted to the top of their block scope but remain uninitialized until the declaration statement executes. Accessing the variable before the declaration throws a ReferenceError:

```javascript
{
  console.log(x); // ReferenceError: Cannot access 'x' before initialization
  let x = 5;
}
```

This behavior prevents the confusing hoisting semantics of `var` but introduces a new hazard: variables in the temporal dead zone are in scope (shadowing outer declarations) but inaccessible. Static analysis tools can detect TDZ violations, but runtime errors still occur in code paths that conditionally access variables before declaration.

Function invocation patterns determine `this` binding in non-arrow functions through complex context-dependent rules. A function call `fn()` binds `this` to the global object (or `undefined` in strict mode), a method call `obj.fn()` binds `this` to `obj`, a constructor call `new Fn()` binds `this` to the newly created object, and explicit binding via `call`, `apply`, or `bind` overrides default behavior. Arrow functions ignore these rules, lexically capturing `this` from the enclosing scope. Mixing arrow functions and regular functions creates subtle `this` binding bugs, especially in callbacks and event handlers where the invocation context differs from the definition context. Defensive patterns include explicitly binding methods in constructors, using arrow functions for callbacks that need to preserve instance context, and enabling strict mode to make accidental global `this` binding fail fast rather than silently polluting the global object.
