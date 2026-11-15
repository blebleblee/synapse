# Lesson 2: Asynchronous Control Flow

## 1. First-Principles Intuition & Invariants

JavaScript was designed with a single, non-negotiable constraint: it runs on a single thread. When Brendan Eich prototyped the language in ten days at Netscape in 1995, the target environment was a browser whose primary job was to render a document and respond to user gestures. Blocking that thread — say, by waiting synchronously for a network response — would freeze the entire UI, making the browser feel dead. The solution was not to introduce threads (with all the attendant complexity of locks, mutexes, and data races) but to invert the control model entirely. Instead of a program waiting for I/O to complete, I/O completes and notifies the program. This is the event loop, and every asynchronous primitive JavaScript has ever shipped — callbacks, promises, async/await — is ultimately a syntactic and semantic layer built on top of it.

Understanding this requires holding one invariant firmly in mind: **JavaScript code itself never runs concurrently**. The runtime executes one task at a time on the call stack. What appears to be concurrency is really interleaving — the event loop dequeues a task, runs it to completion, then dequeues the next. The browser or Node.js runtime offloads genuinely parallel work (network I/O, file system access, timers) to operating-system facilities or worker threads, and when that work finishes, it posts a completion callback onto a queue. The JavaScript engine processes that queue only after the current call stack is empty. This "run-to-completion" guarantee is the foundational invariant that makes JavaScript programs easier to reason about than multi-threaded systems, but it also means a single long-running synchronous computation starves everything else — a failure mode we will return to in detail.

The historical arc of JavaScript's async model is a story of progressively raising the level of abstraction to match programmer intent. Callbacks were the first idiom: pass a function as an argument, and the runtime calls it when the work is done. This works, but it composes poorly. Nesting callbacks to sequence asynchronous operations produces the infamous "callback pyramid" — deeply indented, error-prone code where control flow is implicit and error handling is fragmented across every level of the nesting. The community recognized this as a structural problem, not merely a style preference, which led to the formalization of the Promise in ES2015. A Promise represents a value that will exist at some future point, allowing you to chain `.then()` calls in a flat, left-to-right sequence. ES2017 then introduced `async/await`, which is syntactic sugar over Promises that lets you write asynchronous code with the sequential appearance of synchronous code, without blocking the thread. Each layer does not replace the one below it — async/await compiles down to Promises, and Promises are scheduled via the microtask queue, which is itself a component of the event loop. To optimize or debug any of this, you need a working model of every layer.

---

## 2. Core Architecture & Mechanics

### The Event Loop Execution Model

The JavaScript runtime manages three distinct memory and scheduling structures simultaneously: the call stack, the macrotask queue (commonly called the task queue), and the microtask queue. Their interaction determines every aspect of when your code runs and in what order.

The **call stack** is a LIFO structure of execution contexts. Each function call pushes a frame containing local variables, the current program counter, and a reference to the outer lexical environment. When a function returns, its frame is popped. This is standard stack semantics, identical in concept to the C or Rust call stack, though JavaScript engines like V8 implement it atop their own managed heap for the sake of closures and garbage collection.

The **macrotask queue** holds callbacks scheduled by the host environment's APIs: `setTimeout`, `setInterval`, `setImmediate` (Node.js only), I/O completion callbacks, and UI rendering tasks in the browser. When you write `setTimeout(fn, 0)`, you are not scheduling `fn` to run immediately — you are asking the timer subsystem to enqueue `fn` as a macrotask after a minimum delay of 0 milliseconds. It will not run until the current task finishes and the microtask queue is fully drained.

The **microtask queue** holds callbacks scheduled by Promise resolutions and the explicit `queueMicrotask()` API. Its behavior is fundamentally different from the macrotask queue: after every macrotask completes, the event loop drains the microtask queue **entirely** before processing the next macrotask or rendering frame. This means microtasks can starve macrotasks if they continuously enqueue more microtasks, a subtle but severe failure mode.

The event loop's execution order can be stated precisely:

```
1. Dequeue one macrotask from the task queue and run it to completion.
2. Drain the entire microtask queue (process all pending microtasks,
   including any that are added during this drain).
3. If a rendering opportunity is available (browser only), perform
   style/layout/paint.
4. Return to step 1.
```

This diagram illustrates the relationships between these structures:

```
┌─────────────────────────────────────────────────────────────┐
│                        V8 / JS Engine                        │
│                                                              │
│   ┌──────────────┐        ┌──────────────────────────────┐  │
│   │  Call Stack  │        │       Microtask Queue        │  │
│   │              │        │  (Promise .then, queueMT)    │  │
│   │  [frame n]   │◄───────│  [resolve cb] [resolve cb]   │  │
│   │  [frame n-1] │        └──────────────────────────────┘  │
│   │  [frame 0]   │                      ▲                   │
│   └──────┬───────┘                      │                   │
│          │  run-to-completion           │ drain after each  │
│          ▼                              │  macrotask        │
└──────────┼──────────────────────────────┼───────────────────┘
           │          Event Loop          │
           ▼                              │
┌──────────────────────┐                 │
│   Macrotask Queue    │─────────────────┘
│  (setTimeout, I/O,   │
│   setInterval, ...)  │
└──────────────────────┘
           ▲
           │  enqueue on completion
┌──────────────────────┐
│  Web APIs / libuv    │
│  (Timers, XHR,       │
│   fs, net, ...)      │
└──────────────────────┘
```

### Callbacks: Mechanics and Structural Limits

A callback is nothing more than a first-class function passed as an argument to another function, which calls it at some later point. The runtime overhead is minimal — it is a closure allocation and a function pointer. The pathology is entirely structural.

Consider the classic Node.js pattern for reading a file, transforming its content, and writing the result:

```javascript
const fs = require('fs');

fs.readFile('./input.txt', 'utf8', (readErr, data) => {
  if (readErr) {
    console.error('Read failed:', readErr.message);
    return;
  }

  const transformed = data.toUpperCase();

  fs.writeFile('./output.txt', transformed, 'utf8', (writeErr) => {
    if (writeErr) {
      console.error('Write failed:', writeErr.message);
      return;
    }
    console.log('Done.');
  });
});
```

Each callback is an independent closure. The `readErr` and `data` bindings exist only within the first callback's scope; `writeErr` exists only in the second. Error handling is replicated at every level because there is no mechanism for a failure in a nested callback to automatically propagate to an outer handler. As the depth grows, the fan-out of error checks grows with it, and the logical sequence of operations — read, transform, write — is obscured by the nesting structure. This is not a cosmetic problem; it is a representational mismatch between the linear intent of the program and the tree structure imposed by callbacks.

### Promises: Explicit State and Chainable Composition

A Promise is a state machine with three states: `pending`, `fulfilled`, and `rejected`. It can transition from `pending` to `fulfilled` exactly once, or from `pending` to `rejected` exactly once. These transitions are irreversible. The `.then(onFulfilled, onRejected)` method registers handlers for each outcome and always returns a new Promise, whose resolution depends on what the handler returns. This chain structure is what allows sequential async operations to be expressed as a flat pipeline rather than a nested tree.

```javascript
const { promises: fsp } = require('fs');

fsp.readFile('./input.txt', 'utf8')
  .then((data) => {
    const transformed = data.toUpperCase();
    return fsp.writeFile('./output.txt', transformed, 'utf8');
  })
  .then(() => {
    console.log('Done.');
  })
  .catch((err) => {
    // A single handler catches rejection from any stage above.
    console.error('Pipeline failed:', err.message);
  });
```

The critical mechanical detail is that `.then()` callbacks are **always scheduled as microtasks**, even when the Promise is already resolved at the moment `.then()` is called. This means `.then()` handlers never run synchronously mid-stack. Consider this:

```javascript
const p = Promise.resolve(42);

p.then((value) => {
  console.log('Microtask:', value); // prints second
});

console.log('Synchronous'); // prints first
```

The output is `Synchronous` then `Microtask: 42`, because the `.then()` callback is enqueued as a microtask and the current synchronous code runs to completion before the microtask queue is drained. This is a spec invariant (ECMA-262 §27.2.5.4), not an implementation detail — every conformant engine must behave this way.

Promise chaining composes via return values. If a `.then()` handler returns a plain value, the next handler in the chain receives that value. If it returns a Promise (a "thenable"), the chain waits for that inner Promise to resolve before continuing. This flattening behavior is what makes it possible to pipeline async operations without nesting:

```javascript
function fetchUserProfile(userId) {
  return fetch(`/api/users/${userId}`)
    .then((response) => {
      if (!response.ok) {
        return Promise.reject(new Error(`HTTP ${response.status}`));
      }
      return response.json();
    })
    .then((profile) => {
      return fetch(`/api/teams/${profile.teamId}`);
    })
    .then((response) => response.json())
    .then((team) => ({ userId, team }))
    .catch((err) => {
      console.error('fetchUserProfile failed:', err.message);
      throw err; // re-throw to propagate to callers
    });
}
```

Notice the `.catch()` at the end. Because each `.then()` returns a new Promise that propagates rejections forward, a single `.catch()` acts as a unified error handler for the entire chain. This is the Promise equivalent of a `try/catch` around a synchronous block, and it eliminates the per-callback error duplication that plagues the callback model.

### async/await: Coroutine Semantics on Top of Promises

`async/await` is a syntactic transformation. An `async` function, when called, always returns a Promise. The `await` keyword suspends the execution of the async function at that point, registers the continuation as a microtask on the awaited Promise's resolution, and returns control to the event loop. When the awaited Promise resolves, the async function resumes from the suspension point with the resolved value. The function does not block the thread — it simply yields.

The previous pipeline written with async/await:

```javascript
const { promises: fsp } = require('fs');

async function transformFile(inputPath, outputPath) {
  const data = await fsp.readFile(inputPath, 'utf8');
  const transformed = data.toUpperCase();
  await fsp.writeFile(outputPath, transformed, 'utf8');
  console.log('Done.');
}

transformFile('./input.txt', './output.txt').catch((err) => {
  console.error('transformFile failed:', err.message);
});
```

This reads exactly like synchronous code, but it is not. Each `await` is a suspension point. After `await fsp.readFile(...)`, the function is suspended, the read I/O is dispatched to the OS, and the event loop is free to process other tasks. When the read completes, the continuation is scheduled as a microtask, and the function resumes on the next microtask drain.

Error propagation is handled with ordinary `try/catch`:

```javascript
async function fetchWithRetry(url, maxRetries = 3) {
  let lastError;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      lastError = err;
      const backoffMs = 100 * Math.pow(2, attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, backoffMs));
    }
  }

  throw new Error(`Failed after ${maxRetries} retries: ${lastError.message}`);
}
```

The `try/catch` here wraps an `await` expression, meaning it catches both synchronous exceptions thrown before the await and Promise rejections produced by the awaited operation. This unification is the principal ergonomic gain of async/await over raw Promise chains, where you must separately handle thrown exceptions and `.catch()` rejections.

### Microtask Queue Mechanics: The Full Interaction

To cement the interaction between all three layers, trace the following program manually:

```javascript
console.log('A');

setTimeout(() => console.log('B'), 0);

Promise.resolve()
  .then(() => console.log('C'))
  .then(() => console.log('D'));

console.log('E');
```

The expected output is `A`, `E`, `C`, `D`, `B`. The synchronous code `A` and `E` runs first as part of the initial script evaluation task. `setTimeout` enqueues `B` as a macrotask. The Promise chain enqueues `C` as a microtask. After the script task completes, the microtask queue drains: `C` runs, its `.then()` enqueues `D` as a new microtask, `D` runs. The microtask queue is now empty, so the event loop picks up the next macrotask: `B`. The order is entirely determined by the structural rules above, not by the order the code was written.

A more demanding example involves an async function interleaved with a timer:

```javascript
async function trace() {
  console.log('1');           // synchronous, inside async fn body
  await Promise.resolve();    // suspension point; resumes as microtask
  console.log('3');           // resumes here
}

console.log('start');
trace();
setTimeout(() => console.log('timeout'), 0);
console.log('2');
```

Output: `start`, `1`, `2`, `3`, `timeout`. The async function begins executing synchronously until the first `await`, printing `1`. It then suspends and returns its Promise to the caller. Execution continues synchronously: `2` prints. The script task ends. Microtask queue drains, resuming the async function which prints `3`. Then the macrotask queue runs, printing `timeout`.

---

## 3. High-Performance Optimization & Failure Modes

### Parallelizing Independent Promises

The most common performance mistake in async/await code is sequentializing operations that could run in parallel. Because `await` suspends the function until a single Promise resolves, chaining `await` calls for independent operations serializes them unnecessarily:

```javascript
// Slow: sequential — total latency ≈ latency(A) + latency(B) + latency(C)
async function sequential() {
  const a = await fetchA();
  const b = await fetchB();
  const c = await fetchC();
  return combine(a, b, c);
}

// Fast: parallel — total latency ≈ max(latency(A), latency(B), latency(C))
async function parallel() {
  const [a, b, c] = await Promise.all([fetchA(), fetchB(), fetchC()]);
  return combine(a, b, c);
}
```

`Promise.all()` takes an array of Promises, starts all of them immediately (since the calls to `fetchA()`, `fetchB()`, and `fetchC()` happen synchronously before any `await`), and returns a Promise that resolves when all of them resolve, or rejects immediately if any one of them rejects. For N independent network requests with average latency L, `Promise.all()` reduces the critical path from N×L to L.

When you need all results regardless of individual failures, `Promise.allSettled()` resolves with an array of `{ status: 'fulfilled', value }` or `{ status: 'rejected', reason }` objects, allowing you to inspect each outcome without a short-circuit rejection.

For fan-out scenarios where you need the first successful result, `Promise.any()` resolves with the first fulfilled value and only rejects if every input Promise rejects, with an `AggregateError` collecting all reasons. This is the right primitive for hedged requests — sending the same query to multiple servers and taking whichever responds first.

### Controlling Concurrency at Scale

`Promise.all()` with a large input array launches every Promise simultaneously, which creates a problem when the underlying resource has a capacity constraint: a database connection pool, a rate-limited API, or a fixed-size worker thread pool. Sending 1,000 concurrent requests to an endpoint that permits 10 concurrent connections will produce timeouts and failures, not speed.

The idiomatic solution is a concurrency-limited scheduler. The following implementation processes an array of tasks with a configurable maximum concurrency:

```javascript
async function pooledMap(items, asyncFn, concurrency = 8) {
  const results = new Array(items.length);
  let index = 0;

  async function worker() {
    while (index < items.length) {
      const i = index++;
      results[i] = await asyncFn(items[i], i);
    }
  }

  const workers = Array.from(
    { length: Math.min(concurrency, items.length) },
    () => worker()
  );

  await Promise.all(workers);
  return results;
}

// Usage: process up to 5 files simultaneously
const fileContents = await pooledMap(
  filePaths,
  (path) => fsp.readFile(path, 'utf8'),
  5
);
```

Each `worker` coroutine loops over the shared `index` counter, claiming work atomically (the `index++` post-increment returns the current value then increments, and because all this runs on a single thread, there is no race). `Promise.all(workers)` waits until every worker has exhausted the work queue. The effective concurrency is exactly `Math.min(concurrency, items.length)`.

### Microtask Starvation

Because the microtask queue drains completely between every macrotask, it is possible to starve the macrotask queue — and therefore I/O, timers, and rendering — by continuously enqueuing microtasks from within microtask handlers. The following is a demonstration of this failure mode:

```javascript
function infiniteMicrotasks() {
  Promise.resolve().then(infiniteMicrotasks);
}

infiniteMicrotasks();
setTimeout(() => console.log('This will never print'), 0);
```

The `infiniteMicrotasks` function enqueues itself as a new microtask each time it runs. The event loop drains the microtask queue before processing any macrotask, so the `setTimeout` callback never executes. In a browser, this manifests as a completely frozen UI. In Node.js, it means no I/O callbacks ever fire. The fix is straightforward when you genuinely need to yield to the event loop: use `setImmediate()` in Node.js or `setTimeout(fn, 0)` in browsers, both of which schedule work as macrotasks and allow the event loop to process pending I/O and rendering between iterations.

### Unhandled Promise Rejections

An unhandled Promise rejection is a silent failure in older runtimes and a process-terminating event in modern Node.js (since v15, `--unhandled-rejections=throw` is the default). A rejection becomes "unhandled" when no `.catch()` or rejection handler is attached to a Promise before the current microtask drain completes. The most common source is a floating `async` function call whose returned Promise is ignored:

```javascript
// BAD: rejection from doWork() is unhandled
async function doWork() {
  throw new Error('failure');
}

doWork(); // returned Promise discarded — nobody is listening

// GOOD: always handle or propagate
doWork().catch((err) => console.error('doWork failed:', err.message));
```

In production Node.js applications, you should attach a process-level listener as a final safeguard, while understanding that it should never be the primary error-handling mechanism:

```javascript
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
  // In most production scenarios, crash fast and let the process manager restart.
  process.exit(1);
});
```

### async/await and Error Boundary Precision

A `try/catch` around an `await` catches both the case where the awaited Promise rejects and the case where the async function's body throws synchronously before yielding. This is usually correct, but it can produce over-broad error handling if you are not deliberate about placement. Consider an async function that constructs a URL from parameters, then fetches it:

```javascript
async function fetchResource(id) {
  try {
    const url = buildUrl(id);    // may throw synchronously if id is invalid
    const response = await fetch(url);
    return await response.json();
  } catch (err) {
    // This catches both a bad id AND a network failure.
    // If you need to distinguish them, restructure the try/catch boundaries.
    logError(err);
    throw err;
  }
}
```

If you need to distinguish a validation failure from a network failure, place the synchronous validation before the `try` block, or use separate `try/catch` regions. Blending synchronous and asynchronous error handling in a single catch clause obscures the failure mode and makes upstream error classification harder.

### The Event Loop Tick as a Scheduling Primitive

Senior engineers reaching for async primitives should maintain a precise mental model of scheduling cost. A resolved `Promise.resolve().then(fn)` incurs zero I/O wait but still defers `fn` to the next microtask drain — a useful property when you need to yield to allow other microtasks to interleave. `queueMicrotask(fn)` is a lower-level version that enqueues a function as a microtask without the Promise allocation overhead, appropriate in hot paths where thousands of microtasks per second are being scheduled.

In Node.js, `process.nextTick(fn)` occupies a privileged position: its queue is drained even before the Promise microtask queue, before any I/O callbacks, and before any `setImmediate` callbacks. This makes it useful for ensuring a callback fires before any I/O in the current iteration, but it carries the same starvation risk as an infinite microtask loop. The Node.js documentation explicitly warns against recursive `process.nextTick` calls for this reason. The correct mental model for Node.js scheduling priority, from highest to lowest, is: `process.nextTick` queue → Promise microtask queue → I/O callbacks → `setImmediate` callbacks → timer callbacks (`setTimeout`, `setInterval`).

### V8 Promise Internals and the Cost of Async Stack Traces

A consequence of the coroutine model is that stack traces across `await` boundaries are discontinuous. When an async function throws after an `await`, the call stack captured in the Error object contains only the frames from the most recent synchronous segment, not the full call chain leading to the original invocation. Modern V8 (Chrome 73+, Node.js 12+) reconstructs "async stack traces" by tracking the Promise chain in the hidden `[[PromiseReactionJobs]]` slots, but this reconstruction carries a small runtime overhead and is disabled in production builds of some frameworks.

To preserve diagnostic context in production, the established pattern is to annotate errors at the point of creation and re-throw with enriched messages rather than relying solely on stack traces:

```javascript
async function processOrder(orderId) {
  let order;

  try {
    order = await db.orders.findById(orderId);
  } catch (err) {
    const enriched = new Error(`Failed to load order ${orderId}: ${err.message}`);
    enriched.cause = err;         // ES2022 error cause chaining
    enriched.code = 'ORDER_LOAD_FAILURE';
    throw enriched;
  }

  try {
    await inventory.reserve(order.items);
  } catch (err) {
    const enriched = new Error(`Inventory reservation failed for order ${orderId}`);
    enriched.cause = err;
    enriched.code = 'INVENTORY_RESERVE_FAILURE';
    throw enriched;
  }
}
```

The `cause` property, standardized in ES2022 and supported natively in Node.js 16.9+ and all modern browsers, allows you to build an error chain that survives async context boundaries. When you log `enriched.cause.stack` alongside `enriched.message`, you recover the full diagnostic picture that the async boundary would otherwise sever.
