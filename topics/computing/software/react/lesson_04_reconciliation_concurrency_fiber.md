# Lesson 4: Reconciliation, Concurrency, Fiber Architecture

## 1. First-Principles Intuition & Invariants

React's reconciliation engine solves a deceptively hard problem: how do we transform one tree-structured representation of a user interface into another while minimizing both computational cost and observable flicker? The naive approach—tearing down the entire DOM and rebuilding it from scratch—produces correct results but obliterates performance and destroys browser state like scroll positions, focus, and input values. Conversely, attempting to compute the minimal edit distance between arbitrary trees is an O(n³) problem that would grind even modest interfaces to a halt. React's reconciler threads the needle by exploiting structural assumptions about component trees to achieve O(n) reconciliation while preserving enough DOM stability to feel instant.

At its heart, reconciliation is a diffing algorithm operating on two trees: the current fiber tree representing what's rendered, and the work-in-progress tree representing what should be rendered. The reconciler walks these trees in tandem, comparing each node to determine whether it can be reused, must be updated, or should be replaced entirely. This process generates a linear sequence of side effects—DOM mutations, lifecycle method invocations, ref updates—that the renderer commits in a single synchronous pass. The key insight is that most UI updates are localized: a button click changes one subtree, not the entire application. By reusing unchanged subtrees and their associated DOM nodes, React amortizes the cost of updates across the stable portions of the tree.

The diffing algorithm's efficiency rests on two assumptions that hold true for virtually all UI code. First, elements of different types produce fundamentally different trees. If a component renders a `<div>` in one update and a `<span>` in the next, React assumes the entire subtree beneath that element has changed and tears it down rather than attempting a fine-grained comparison. Second, developers can signal stable identity across renders through explicit keys. When rendering lists, keys tell React which items correspond across updates even when their positions change. Without keys, React falls back to positional matching, which produces pathological behavior when items are reordered or inserted at the beginning of a list.

These assumptions reduce reconciliation to a linear scan with local decisions at each node. When comparing two elements, React first checks their types. If the types differ, it schedules deletion of the old subtree and creation of the new one. If the types match, it marks the fiber for update and proceeds to reconcile children. Child reconciliation handles three cases: single children (compared by type), arrays of children (matched by keys or position), and iterables (converted to arrays). The key matching algorithm builds a map of old children by key, then walks the new children in order, attempting to reuse fibers from the map before creating new ones. Unmatched old children are scheduled for deletion.

This design makes reconciliation fast but imposes invariants that developers must respect. Keys must be stable across renders—generating keys from indices or random values defeats the optimization. Keys must be unique among siblings—duplicates cause React to discard one arbitrarily. Element types must be consistent—returning `null` versus `false` from a component produces different trees despite both representing "no content." These constraints rarely surface as problems in normal code, but they become critical when debugging why a list re-renders incorrectly or why a component's state disappears unexpectedly.

The original React reconciler operated synchronously, blocking the JavaScript thread until reconciliation completed. For small updates this worked fine, but large component trees could lock the UI for hundreds of milliseconds, causing dropped frames and sluggish interactions. The Fiber architecture, introduced in React 16, decomposed reconciliation into incremental units of work that could be paused and resumed. Each fiber represents one unit of work—updating a component, processing its children, committing side effects. The scheduler prioritizes work by urgency, ensuring high-priority updates like text input preempt low-priority updates like analytics logging. This enables React to maintain 60fps even during heavy rendering, distributing work across multiple frames rather than blocking until completion.

Fiber's concurrency model is cooperative rather than preemptive. React doesn't forcibly interrupt work; instead it checks after each fiber whether higher-priority work has arrived. If so, it saves progress and switches to the urgent work. Once complete, it resumes the paused work from where it left off. This approach avoids the complexity of true preemption—locking shared state, handling partial mutations—while still providing responsive behavior. The tradeoff is that long-running work in a single fiber (like a component rendering thousands of elements) can still block the thread. React mitigates this by encouraging composition—breaking large components into smaller ones—so each fiber represents a small quantum of work.

Priority lanes encode urgency as bitmasks representing categories like synchronous (must complete immediately), user-blocking (user is waiting), normal (routine updates), and idle (background work). When scheduling work, React assigns it to the appropriate lane based on the event that triggered it. Discrete events like clicks and key presses use user-blocking priority. Continuous events like scroll and mouse move use lower priority to avoid overwhelming the system. Transitions, explicitly marked via the `useTransition` hook, use normal priority to keep the UI responsive during expensive operations. The scheduler processes lanes in order, draining high-priority work before moving to lower priorities.

Suspense boundaries introduce another dimension to concurrency by allowing components to wait for asynchronous data without blocking the entire tree. When a component suspends—typically by throwing a Promise—React catches the Promise at the nearest Suspense boundary, rendering the fallback UI while the Promise settles. Once resolved, React retries the suspended component, integrating its content into the tree. Suspense decouples data fetching from rendering, enabling components to declare their data dependencies imperatively while React handles the coordination. This moves React from purely synchronous rendering into an asynchronous model where the rendered tree reflects data availability.

The invariants governing Suspense are subtle. A component can suspend during render but not during commit—side effects must remain synchronous. Suspense boundaries must be idempotent since suspended subtrees may be retried multiple times if dependencies change. Promises thrown from components must be cache-keyed properly or React may thrash, repeatedly suspending and resolving the same data. Error boundaries and Suspense boundaries interact: if a suspended Promise rejects, the error propagates to the nearest error boundary, not the Suspense boundary. These mechanics reward careful boundary placement and disciplined data fetching patterns.

Concurrent rendering introduces tearing risks where different parts of the UI reflect different versions of external state. If a component reads from a global store during render and that store updates before the render completes, later components may see the new value while earlier components saw the old value. React's solution is `useSyncExternalStore`, which forces synchronous reads from external sources and triggers immediate re-renders if the value changes mid-render. This trades some concurrency for consistency, ensuring the rendered tree represents a single snapshot of state rather than a chimera of multiple versions.

## 2. Core Architecture & Mechanics

The fiber data structure is the fundamental unit of React's reconciler. Each fiber corresponds to one component instance, DOM node, or fragment, forming a tree that mirrors the component hierarchy. Unlike the virtual DOM representation, which is ephemeral and regenerated on each render, fibers persist across updates, accumulating state and side effects as the reconciler processes them. A fiber contains pointers to its parent (`return`), first child (`child`), and next sibling (`sibling`), forming a linked tree traversable without recursion. This structure enables incremental traversal: the reconciler can pause at any fiber, save its position, and resume later without maintaining a call stack.

```
Fiber Node Structure (Conceptual)

┌─────────────────────────────────────────────────┐
│ Fiber                                           │
├─────────────────────────────────────────────────┤
│ tag: WorkTag          // ClassComponent, etc    │
│ type: any             // Component function/class│
│ stateNode: any        // DOM node or instance    │
│ return: Fiber         // Parent fiber            │
│ child: Fiber          // First child             │
│ sibling: Fiber        // Next sibling            │
│ alternate: Fiber      // Other buffer            │
│ effectTag: SideEffectTag // Update, Placement    │
│ nextEffect: Fiber     // Effect list pointer     │
│ lanes: Lanes          // Priority bitmask        │
│ memoizedState: any    // Current state           │
│ pendingProps: any     // New props               │
│ memoizedProps: any    // Previous props          │
│ updateQueue: UpdateQueue // State updates        │
└─────────────────────────────────────────────────┘
```

React maintains two fiber trees: the current tree representing the last committed state, and the work-in-progress tree representing the next state. Each fiber in the current tree has an `alternate` pointer to its counterpart in the work-in-progress tree, and vice versa. During reconciliation, React clones fibers from the current tree into the work-in-progress tree, modifying them as needed. Once reconciliation completes, the work-in-progress tree becomes the current tree via a pointer swap. This double-buffering strategy allows React to build the next frame entirely in memory before committing it, preventing partially-rendered state from being visible.

The reconciliation loop begins at the root fiber and proceeds through four phases. The render phase traverses the work-in-progress tree, calling component functions, diffing elements, and accumulating side effects. This phase is interruptible—React can pause between fibers to handle higher-priority work. The render phase produces an effect list: a linked list of fibers that require DOM mutations, lifecycle calls, or ref updates. The commit phase processes this effect list in three sub-phases: before mutation (calling `getSnapshotBeforeUpdate`), mutation (applying DOM changes), and layout (calling `useLayoutEffect` and `componentDidMount`). The commit phase is synchronous and uninterruptible to ensure the DOM never reflects an inconsistent state.

Child reconciliation is where keys and identity matter most. Consider a simple list render:

```javascript
function TodoList({ items }) {
  return (
    <ul>
      {items.map(item => (
        <li key={item.id}>{item.text}</li>
      ))}
    </ul>
  );
}
```

On the initial render, React creates three fibers: one for the `<ul>`, and one for each `<li>`. Each fiber stores its key (the item ID) and its position in the list. On subsequent renders, if `items` changes, React executes a two-pass reconciliation. First, it scans both the old and new child lists, attempting to match elements with identical keys and positions. If key and position match, React reuses the fiber, updating its props but preserving its stateNode (DOM element) and internal state. Elements that moved position but have matching keys are collected into a map for later reuse.

The second pass handles insertions, deletions, and moves. React walks the new child list, checking if each element was matched in the first pass. If matched, the fiber moves to the new position. If not matched but a fiber with that key exists in the map, React reuses that fiber, marking it for repositioning. If no fiber exists with that key, React creates a new one, marking it for insertion. Fibers remaining in the old list after this process are marked for deletion. This algorithm runs in O(n) time with respect to the number of children, making list reconciliation fast even for hundreds of items.

Without keys, React falls back to positional matching, comparing the first old child to the first new child, the second to the second, and so on. This works fine if the list order is stable and items are only appended or removed from the end. But if items are reordered or inserted at the beginning, positional matching produces catastrophic behavior. Inserting an item at index 0 causes React to think every subsequent item changed, triggering updates for the entire list and destroying component state. Keys fix this by decoupling logical identity from positional order.

The Fiber scheduler coordinates work execution across multiple priorities. When an update is scheduled—via `setState`, `useState`, or `useReducer`—React computes its priority based on the triggering event. Discrete events like clicks receive `UserBlockingPriority` (priority level 2). Continuous events like scroll receive `NormalPriority` (level 3). `useTransition` wraps updates in `TransitionPriority` (level 4). The scheduler maintains a priority queue of pending work, processing high-priority lanes before low-priority ones.

Time-slicing emerges from the scheduler's work loop structure. React processes fibers until either the work completes or a deadline expires. The deadline defaults to 5 milliseconds, leaving 11ms of each 16ms frame for browser layout, paint, and script execution. When the deadline expires, React checks for higher-priority work. If none exists and the frame budget remains, React continues processing the current priority. Otherwise, it yields control to the browser via `MessageChannel` or `setTimeout`, resuming work in a future event loop turn.

```
Time-Slicing Execution Flow

Frame 1 (16ms):                Frame 2 (16ms):
┌─────────────────┐            ┌─────────────────┐
│ React Work (5ms)│            │ React Work (5ms)│
├─────────────────┤            ├─────────────────┤
│ Layout (4ms)    │            │ Layout (4ms)    │
├─────────────────┤            ├─────────────────┤
│ Paint (3ms)     │            │ Paint (3ms)     │
├─────────────────┤            ├─────────────────┤
│ Idle (4ms)      │            │ Idle (4ms)      │
└─────────────────┘            └─────────────────┘
     ↓ Yield                        ↓ Yield
     Resume →                       Resume →
```

Priority inversion—where low-priority work blocks high-priority work—is avoided through lane expiration. If a lane remains unprocessed for too long, its priority escalates to prevent starvation. This ensures background work eventually completes even when high-priority updates continuously arrive. The escalation threshold varies by lane: user-blocking work expires after 250ms, normal work after 5 seconds, idle work after 10 seconds. Once expired, the work is processed at `ImmediatePriority`, bypassing all other lanes.

Suspense boundaries integrate with the Fiber scheduler through a suspend-and-retry mechanism. When a component throws a Promise, React's error handling catches it, identifies the nearest Suspense boundary, and marks that subtree as suspended. The boundary's fallback fiber is inserted into the work-in-progress tree, replacing the suspended subtree. React attaches a `then` handler to the Promise, scheduling a retry once it resolves. On retry, React clones the suspended subtree's fibers, replaying their render functions with fresh props and context.

The retry mechanism must handle racing Promises carefully. If a component suspends on Promise A, then props change and it suspends on Promise B, React must ignore Promise A's resolution and only respond to Promise B. React achieves this by versioning Suspense boundaries. Each suspend increments the boundary's version, and each retry checks whether the Promise's version matches the current boundary version. Stale Promises are ignored, preventing thrash from outdated data.

Suspense interacts with concurrent rendering in subtle ways. During a concurrent render, React may suspend, render the fallback, then resume the original render if high-priority work interrupts. When the concurrent render completes, React must decide whether to commit the fallback or wait for suspended data. If the suspense timeout (typically 150ms) has elapsed, React commits the fallback to avoid perceived latency. If the data resolves before the timeout, React commits the content directly, skipping the fallback. This heuristic balances responsiveness with avoiding flicker from transient fallbacks.

Error boundaries and Suspense boundaries form orthogonal hierarchies in the fiber tree. When a component throws an error during render, React searches upward for an error boundary, unwinding fibers until it finds one. If a Suspense boundary is encountered first, React checks whether the thrown value is a Promise. If so, it treats it as suspension. If not, it continues searching for an error boundary. This allows errors in suspended components to propagate correctly while distinguishing between recoverable suspension and fatal errors.

The effect list is a singly-linked list of fibers that require side effects, built during the render phase. As React traverses the work-in-progress tree, it appends fibers with pending effects to this list via their `nextEffect` pointers. Effects include DOM mutations (`Placement`, `Update`, `Deletion`), lifecycle calls (`Snapshot`, `Layout`, `Passive`), and ref updates. By collecting effects into a linear list, React can process them during commit without re-traversing the entire tree. The effect list preserves tree order, ensuring effects are applied in a predictable sequence: parents before children for creation, children before parents for cleanup.

Passive effects, triggered by `useEffect`, are deferred until after the browser paints. React schedules them via `requestIdleCallback` or a fallback timer, ensuring they don't block the commit phase. This design keeps paint fast while still running effects promptly. If a passive effect schedules an update, that update is treated as normal priority, not synchronous, preventing effects from causing cascading synchronous renders. Active effects, triggered by `useLayoutEffect`, run synchronously during the layout phase, allowing them to read layout and synchronously trigger re-renders before paint.

## 3. High-Performance Optimization & Failure Modes

Reconciliation performance degrades when component trees violate React's assumptions or when developers misuse keys and memoization. The most common failure mode is rendering deeply nested components that return large arrays without keys. Without keys, inserting an item at the beginning of a 1000-item list forces React to update 999 components unnecessarily. The fix is straightforward—add stable keys—but the performance cliff is steep enough that developers often only discover the problem in production with real data volumes.

Key stability is critical but often violated in practice. Using array indices as keys appears to work until items are reordered, at which point component state sticks to the wrong items. Consider a list of input fields keyed by index: reordering items causes the input values to remain in their original positions while the data moves, producing confusing behavior where typing in one field updates a different item. The solution is using stable identifiers from the data itself—database IDs, UUIDs, content hashes—rather than positional information.

Keys must also be unique among siblings, not globally. Two unrelated lists can use overlapping keys without conflict since reconciliation only compares siblings. However, moving a component with the same key from one parent to another causes React to treat it as the same component, reusing state unexpectedly. This subtlety matters when implementing features like tabs or accordions where components move between containers. The fix is scoping keys by container or using compound keys that include parent identity.

Memoization via `React.memo`, `useMemo`, and `useCallback` reduces reconciliation work by preventing unnecessary renders. `React.memo` wraps functional components, shallow-comparing props to determine if a re-render is needed. If props are referentially equal, React reuses the previous render result, skipping the component and its subtree. This optimization is powerful but requires disciplined prop management. Passing inline functions or object literals as props defeats memoization since they create new references on each render. The solution is hoisting stable references outside the component or wrapping them in `useCallback` and `useMemo`.

```javascript
// Anti-pattern: inline function defeats memoization
function Parent() {
  const [count, setCount] = useState(0);
  return <MemoizedChild onClick={() => console.log('click')} />;
}

// Correct: stable reference enables memoization
function Parent() {
  const [count, setCount] = useState(0);
  const handleClick = useCallback(() => console.log('click'), []);
  return <MemoizedChild onClick={handleClick} />;
}
```

Over-memoization is equally problematic. Wrapping every component in `React.memo` and every callback in `useCallback` adds overhead—both memory from cached references and CPU from comparison logic—that can exceed the cost of the renders being avoided. The rule of thumb is to memoize components that are expensive to render (hundreds of elements), frequently re-render despite stable props, or appear many times (list items). Leaf components that render a single DOM element rarely benefit from memoization.

Concurrent rendering's interruptibility creates new failure modes around external state. If a component reads from a mutable global store during render, concurrent renders may observe different values at different points in the tree, producing tearing. The canonical example is a Redux store that updates mid-render: early components see the old value, late components see the new value, and the UI reflects an inconsistent snapshot. React's `useSyncExternalStore` forces synchronous consistency by triggering an immediate re-render if the store changes during a render, ensuring the entire tree reflects the same snapshot.

Suspense boundaries must be placed carefully to balance granularity and user experience. Too few boundaries cause large portions of the UI to disappear during data fetching, creating jarring transitions. Too many boundaries produce a popcorn effect where sections of the UI appear in rapid succession, feeling unstable. The optimal placement depends on the UI structure: boundaries should encompass semantically cohesive regions that are meaningful to load independently. For example, a product page might have boundaries around the product details, reviews, and recommendations, allowing each section to load at its own pace.

Suspense timeouts prevent flicker from fast-resolving Promises while still showing fallbacks for slow ones. React defaults to 150ms: if a Promise resolves faster, the fallback never appears; if slower, the fallback renders until resolution. This timeout is tunable via experimental APIs but rarely needs adjustment. The failure mode is setting the timeout too long, causing perceived latency as users wait for data that could have been displayed incrementally. The opposite failure—too short a timeout—causes visible flicker as fallbacks flash briefly before content appears.

Error boundaries must account for asynchronous errors that occur outside the render phase. Errors thrown in event handlers, `setTimeout` callbacks, or Promise rejections don't propagate to error boundaries since they occur outside React's call stack. The solution is explicit error handling: wrapping async operations in try-catch, using Promise `.catch()` handlers, or setting error state that components can render. Some teams centralize error handling in a global error service, logging failures and displaying user-friendly messages without relying on error boundaries.

Suspense's retry mechanism can cause infinite loops if not implemented carefully. If a component suspends, retries, and suspends again on the same data, React will continue retrying indefinitely, burning CPU and memory. The root cause is typically missing cache invalidation or stale dependency arrays in data fetching hooks. The solution is ensuring that suspended Promises are cached by a key that includes all dependencies, and that cache entries are invalidated when dependencies change. Libraries like SWR and React Query handle this automatically, but custom implementations require discipline.

Priority lanes can interact poorly with side effects that trigger synchronous updates. If a low-priority render triggers a `useLayoutEffect` that calls `setState`, that update is processed at synchronous priority, potentially blocking high-priority work. The scheduler attempts to detect these patterns and batch the updates, but pathological cases can still occur. The mitigation is avoiding synchronous updates in effects, preferring passive effects (`useEffect`) or queuing updates via `startTransition` to signal they should be processed at lower priority.

Profiling reconciliation performance requires React DevTools' Profiler, which records flame graphs showing component render times and update causes. The profiler highlights components that re-render unnecessarily, indicating where memoization could help, and shows which props changed to trigger each render. When debugging slow updates, enable the "Record why each component rendered" option to see precise causality. For production monitoring, React's experimental `<Profiler>` component reports render timings via callback, enabling integration with analytics systems.

Large fiber trees consume significant memory—roughly 1KB per fiber—which matters for applications rendering thousands of components. Virtualization libraries like `react-window` and `react-virtualized` solve this by rendering only the visible portion of large lists, recycling fibers as the user scrolls. These libraries integrate with Suspense, allowing infinite scrolling lists that load data on-demand without mounting thousands of components upfront. The tradeoff is complexity: virtualization requires knowing item sizes upfront or measuring them dynamically, and it complicates accessibility since off-screen items aren't in the DOM.

Concurrent rendering's partial-tree updates can cause observers like React DevTools or third-party monitoring to see intermediate states that never commit. If a render is interrupted and discarded due to higher-priority work, any logging or metrics collected during that render reflect wasted work. The solution is hooking into React's commit phase rather than render phase, ensuring observations reflect only committed state. React's Profiler API provides commit callbacks for this purpose, reporting only completed updates.

The Fiber architecture's cooperative scheduling depends on components yielding control frequently. A single component that runs a tight loop for 100ms will block the scheduler, preventing concurrent updates and causing dropped frames. React can't preempt JavaScript execution, so long-running synchronous work must be broken into smaller chunks manually. Web Workers offer an escape hatch for CPU-intensive tasks, offloading computation from the main thread entirely, but they require careful message passing since Workers can't access the DOM or React state directly.

Suspense's async model requires rethinking error handling and loading states. Traditional imperative patterns—`try/catch` blocks, loading flags, error states—become declarative boundaries in the tree. This shift is powerful but unfamiliar, causing confusion around where errors surface and how to handle partial failures. The mental model is that Suspense boundaries are async try-catch blocks: errors thrown from within propagate to the nearest error boundary, while Promises are caught by the nearest Suspense boundary. Combining both creates robust data-loading patterns that gracefully degrade across network failures and slow connections.

React's scheduler is fundamentally cooperative, relying on components to be well-behaved. Malicious or buggy components can monopolize the thread, degrading the experience for all users. React provides no hard guarantees about interruptibility or fairness—only best-effort scheduling. In adversarial environments, this requires sandboxing untrusted components via iframes or Web Workers, preventing them from affecting the main application. For trusted code, thorough testing and performance budgets ensure components stay within acceptable bounds.

The transition from synchronous to concurrent rendering is opt-in via `createRoot` instead of `render`. Existing applications using legacy rendering continue working unchanged, but they miss concurrent benefits. Migrating requires auditing external state subscriptions, ensuring they use `useSyncExternalStore`, and reviewing error boundaries and Suspense placement. React provides a gradual migration path: `createRoot` enables concurrent rendering at the root, but legacy subtrees can coexist by mounting them via `ReactDOM.render`, allowing incremental adoption across large codebases.
