# Lesson 3: Hooks, Lifecycle, Effect Semantics

## 1. First-Principles Intuition & Invariants

React's hooks system represents a fundamental departure from the class-based component model, replacing instance methods and lifecycle callbacks with a composable function-based architecture that captures stateful logic through closures. To understand hooks at a systems level, we must first recognize that every functional component invocation creates a fresh execution context—a new stack frame with its own lexical scope—yet React maintains persistent state across these ephemeral invocations through a stable fiber tree structure that outlives individual function calls.

The core invariant governing hooks is positional stability. When React encounters a hook call during component execution, it does not rely on variable names or any form of runtime identification. Instead, it maintains an ordered linked list of hook nodes attached to each fiber, and matches hooks to their persisted state purely by invocation order within the component body. This design decision has profound implications: hooks cannot be called conditionally, cannot appear inside loops whose iteration count varies, and cannot be invoked after early returns. Every render must traverse the same sequence of hook calls in identical order, establishing a deterministic correspondence between the component's source code structure and the runtime hook chain.

Consider the mechanical reality of what happens when a functional component executes. React maintains a global work-in-progress fiber that represents the component currently being rendered. Before invoking the component function, React positions an internal cursor at the head of this fiber's hook list. Each hook call—whether `useState`, `useEffect`, `useRef`, or a custom composition—advances this cursor forward, either initializing a new hook node on mount or retrieving the existing node on subsequent renders. The hook implementation reads and writes to the node at the current cursor position, then increments the cursor for the next hook call. This cursor mechanism is why hook call order must remain invariant: any permutation would cause hooks to read state belonging to a different logical hook, violating the contract between component source code and runtime state.

The `useState` hook exemplifies this architecture. When first invoked, it allocates a hook node containing a queue structure for pending state updates and initializes the state value. It returns a tuple: the current state value from the hook node, and a dispatch function that enqueues updates. Critically, the dispatch function is not a lexically scoped closure over the current state—it is a stable reference that enqueues update objects onto the hook's queue. These updates are not applied synchronously; React processes them during the next render cycle, computing the new state by reducing the queue with each update function in sequence. This queue-based model enables React to batch multiple `setState` calls within a single event handler into one render, and to implement features like concurrent rendering where state updates can be interrupted and resumed.

Effects introduce temporal semantics into the functional component model. An effect registered via `useEffect` does not execute during render; instead, React schedules it to run asynchronously after the browser has painted the committed fiber tree to the DOM. This sequencing ensures that effects never block the render-commit pipeline, maintaining UI responsiveness even when effects perform expensive operations. The effect hook node stores both the effect function and its dependency array. After each render, React performs a shallow equality comparison between the previous and current dependency arrays. Only if a dependency has changed—determined by `Object.is` semantics—does React schedule the effect for execution. If an effect returns a cleanup function, React invokes this cleanup before running the effect again on subsequent renders, and before the component unmounts.

The dependency array represents a contract between the developer and React's reconciliation engine. It declares which values from the component's closure the effect actually reads, enabling React to determine when the effect must re-run. This contract is strictly mechanical: React does not analyze the effect function body to detect captured variables. The responsibility falls entirely on the developer to list every closure-captured value that could change between renders. An incomplete dependency array creates a closure staleness bug where the effect continues referencing old values even after the component has re-rendered with new props or state. This is not a React bug—it is the fundamental nature of JavaScript closures combined with React's optimization strategy.

The distinction between `useEffect` and `useLayoutEffect` hinges on synchronization semantics. While `useEffect` executes after paint in a non-blocking manner, `useLayoutEffect` executes synchronously after React commits mutations to the DOM but before the browser paints. This synchronous execution allows layout effects to read DOM geometry and apply immediate corrections before the user perceives any visual inconsistency. However, this power comes at a cost: layout effects block painting, and expensive computations within them directly degrade frame rate. The correct mental model is that layout effects participate in the same synchronous flush as the render-commit cycle, while standard effects run in a subsequent asynchronous phase.

## 2. Core Architecture & Mechanics

React's fiber architecture provides the structural foundation for hooks. Each component instance corresponds to a fiber node, and each fiber maintains a `memoizedState` field that points to the head of a linked list of hook objects. The hook list is constructed during the initial mount render and remains structurally stable across subsequent updates, with individual hook nodes being mutated in place rather than reconstructed.

A single hook node conforms to this internal structure:

```text
Hook Node {
    memoizedState: any,           // Current state value or effect descriptor
    baseState: any,               // Base state for update queue reduction
    queue: UpdateQueue | null,    // Pending state updates or effect dependencies
    baseQueue: Update | null,     // Prioritized update queue segment
    next: Hook | null             // Pointer to next hook in component's list
}
```

When `useState` initializes, it creates a hook node where `memoizedState` holds the current state value and `queue` contains an update queue structure. The update queue accumulates dispatch calls between renders. Each queued update stores either a new state value or an updater function that derives the new state from the previous state. During the next render, React processes this queue in the order updates were enqueued, computing the final state through sequential application of each update.

The dispatch function returned by `useState` has a stable identity across renders, achieved through binding it to the hook node during initialization. When invoked, dispatch does not immediately mutate state. Instead, it constructs an update object and links it into the hook's circular update queue. It then schedules a re-render of the component by marking the fiber as having work and triggering React's reconciliation scheduler. This indirection through a queue enables React to batch multiple state updates from a single event handler into one render pass, and to implement features like automatic batching across async boundaries in React 18.

Effect hooks operate through a distinct mechanism. When `useEffect` executes during render, it creates or updates a hook node where `memoizedState` holds an effect descriptor object:

```text
Effect Descriptor {
    tag: number,                  // Bitfield indicating effect lifecycle phase
    create: () => void | (() => void),  // Effect function
    destroy: (() => void) | null, // Cleanup function from previous execution
    deps: Array<any> | null,      // Dependency array
    next: Effect | null           // Circular linked list of fiber's effects
}
```

React maintains a separate circular linked list of effects on each fiber, threaded through the `next` pointers. After the commit phase completes and the browser has painted, React traverses this effect list, invoking each effect function asynchronously. The `tag` bitfield encodes whether the effect has dependencies, whether it needs to fire, and which lifecycle phase it belongs to (mount, update, unmount). Before invoking an effect on update or unmount, React calls its stored `destroy` cleanup function if one exists, ensuring proper resource teardown.

The dependency comparison algorithm is purely shallow. React iterates both the previous and current dependency arrays simultaneously, comparing each element with `Object.is`. If any element differs, or if the array lengths differ, React marks the effect as needing to fire by setting the appropriate bit in its `tag` field. This comparison happens during render, while scheduling whether to execute the effect happens during commit. The separation of concerns allows React to bail out of effect execution early if dependencies haven't changed, without the overhead of setting up asynchronous effect scheduling.

Custom hooks are simply functions that call built-in hooks, with no special runtime representation. They compose by executing during the component's render phase, invoking built-in hooks in sequence and advancing the same global hook cursor that the component's own hook calls advance. This composition model is why custom hooks must follow the same ordering rules as built-in hooks—they participate in the same positional correspondence mechanism. A custom hook cannot dynamically change which hooks it calls any more than the component itself can.

Consider the execution flow when a component with multiple hooks re-renders:

```text
Component Render Invocation
  ↓
React positions hook cursor at fiber.memoizedState
  ↓
useState call → advance cursor, read state from current node, return state + dispatch
  ↓
useEffect call → advance cursor, compare dependencies, update effect descriptor
  ↓
useRef call → advance cursor, return stable ref object from node.memoizedState
  ↓
Custom hook invocation → executes inline, advances cursor through its own hook calls
  ↓
Component returns JSX
  ↓
React commits fiber tree mutations to DOM
  ↓
Browser paints
  ↓
React asynchronously invokes scheduled effects
```

The `useRef` hook demonstrates the simplest hook pattern. Its hook node's `memoizedState` field directly stores the ref object `{ current: value }`. This object is allocated once during mount and persists across all subsequent renders. The ref object itself is mutable—setting `ref.current` does not trigger re-renders—because React never reads it during reconciliation. Refs provide an escape hatch for storing mutable state that must persist across renders but does not participate in the reactive data flow.

The `useMemo` and `useCallback` hooks implement memoization through dependency-tracked caching. Their hook nodes store both the memoized value (or callback) and the dependency array from the previous render. On each render, React performs a shallow dependency comparison identical to `useEffect`. If dependencies are unchanged, React returns the cached value without recomputing. If dependencies changed, React invokes the factory function, caches the new result in the hook node, and returns it. The memoization is purely an optimization—it never affects correctness, only performance.

React 18 introduced new hook primitives that interact with concurrent rendering. The `useTransition` hook provides access to React's concurrent mode scheduling, allowing developers to mark state updates as non-urgent. Internally, this hook modifies the priority lane assigned to updates enqueued by the returned `startTransition` function, causing React's scheduler to defer them in favor of more urgent interactive updates. The `useDeferredValue` hook implements a similar pattern but at the value level, maintaining two copies of a value—one current, one deferred—and scheduling lower-priority renders when the deferred value lags behind.

## 3. High-Performance Optimization & Failure Modes

The most pernicious failure mode in hooks-based React is stale closure capture. When an effect or callback captures variables from the component scope, it creates a closure over those variables at the time the function is defined. If React does not re-run the effect or redefine the callback when those variables change, the function continues referencing the old values indefinitely. This manifests as subtle bugs where event handlers reference stale props, effects read outdated state, or callbacks invoke old versions of other callbacks. The root cause is always an incomplete dependency array that fails to list all closure-captured variables.

Consider this common antipattern:

```javascript
function MessageDisplay({ messageId }) {
  const [message, setMessage] = useState(null);
  
  useEffect(() => {
    fetchMessage(messageId).then(data => setMessage(data));
  }, []); // BUG: messageId not in dependencies
  
  return <div>{message}</div>;
}
```

The empty dependency array tells React to run the effect only once after mount. When the component re-renders with a new `messageId` prop, the effect does not re-run because React sees no dependency changes. The effect function itself is a stale closure—it still references the `messageId` value from the initial render. The fix requires listing `messageId` in the dependency array, causing the effect to re-run whenever the prop changes. The corrected version must also handle race conditions where a fast prop change causes a previous fetch to complete after a subsequent fetch, requiring request cancellation or response sequencing logic.

The ESLint plugin `eslint-plugin-react-hooks` provides exhaustive static analysis for dependency array correctness. It traverses the abstract syntax tree of effect and callback functions, identifies all closure-captured variables, and validates that every captured variable appears in the dependency array. While this analysis is conservative and occasionally produces false positives for stable references, the correctness benefit vastly outweighs the minor inconvenience of occasionally adding unnecessary dependencies or extracting logic to avoid captures.

Effect cleanup functions are essential for preventing resource leaks and race conditions. When an effect establishes a subscription, starts a timer, initiates a network request, or allocates any resource that requires explicit teardown, it must return a cleanup function that performs the corresponding teardown. React invokes this cleanup before running the effect again on subsequent renders and before the component unmounts. Omitting cleanup for subscriptions causes event handlers to accumulate on each render, multiplying memory usage and causing duplicate event processing. Omitting cleanup for async operations causes completed requests to invoke callbacks against unmounted components, typically manifesting as "Can't perform state update on unmounted component" warnings.

A correct async effect with cleanup and race condition handling:

```javascript
function UserProfile({ userId }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    let cancelled = false;
    
    setLoading(true);
    fetchUserProfile(userId)
      .then(data => {
        if (!cancelled) {
          setProfile(data);
          setLoading(false);
        }
      })
      .catch(error => {
        if (!cancelled) {
          setProfile(null);
          setLoading(false);
        }
      });
    
    return () => {
      cancelled = true;
    };
  }, [userId]);
  
  if (loading) return <div>Loading...</div>;
  return <div>{profile?.name}</div>;
}
```

The `cancelled` flag implements request cancellation semantics. When the effect re-runs due to a `userId` change, React invokes the previous effect's cleanup function before executing the new effect. The cleanup sets `cancelled` to true, causing the pending promise callback to bail out without updating state. This prevents a race condition where a slow fetch for `userId=1` completes after a fast fetch for `userId=2`, overwriting the correct profile with stale data.

For more sophisticated cancellation, particularly with fetch requests, use `AbortController`:

```javascript
useEffect(() => {
  const controller = new AbortController();
  
  fetch(`/api/users/${userId}`, { signal: controller.signal })
    .then(response => response.json())
    .then(data => setProfile(data))
    .catch(error => {
      if (error.name !== 'AbortError') {
        // Handle actual errors, ignore cancellation
      }
    });
  
  return () => controller.abort();
}, [userId]);
```

The `AbortController` provides browser-level cancellation, terminating the network request immediately rather than merely ignoring its result. This conserves bandwidth and reduces server load when users rapidly navigate between profiles.

State update batching in React 18 introduced automatic batching across async boundaries, but this can create subtle timing issues. Prior to React 18, multiple `setState` calls within an async callback like a promise handler would each trigger separate renders. React 18 batches them by default, but developers accustomed to the old behavior might rely on synchronous state updates being visible immediately after each `setState` call. When state updates are batched, intermediate state values never render, and refs or DOM queries performed between `setState` calls read stale values. The solution is to recognize that state updates are always asynchronous and use effects or callbacks to react to state changes rather than assuming synchronous visibility.

The `useCallback` hook is frequently misused as a premature optimization. Wrapping every function in `useCallback` adds overhead without benefit unless the callback is passed to a memoized child component or used as an effect dependency. The callback itself is cheap to recreate on each render—JavaScript function allocation is extremely fast. The expense comes from unnecessary child re-renders when an unstable callback reference invalidates memoization. The optimization pattern is to memoize callbacks only when they flow into `React.memo` components or appear in dependency arrays:

```javascript
function ParentList({ items }) {
  // Expensive child component wrapped in React.memo
  const MemoizedItem = React.memo(ItemComponent);
  
  // Without useCallback, ItemComponent re-renders on every parent render
  // because handleClick is a new function reference each time
  const handleClick = useCallback((id) => {
    console.log('Clicked item:', id);
  }, []); // Stable reference across renders
  
  return items.map(item => (
    <MemoizedItem key={item.id} item={item} onClick={handleClick} />
  ));
}
```

Conversely, over-specifying dependencies in `useCallback` defeats its purpose. If the callback captures state or props that change frequently, wrapping it in `useCallback` with those dependencies provides no benefit—the callback is redefined on every render anyway. The optimization only matters when the callback can remain stable across many renders by depending on rarely-changing or no values.

Custom hooks enable powerful abstraction patterns but require discipline around dependency management and separation of concerns. A well-designed custom hook encapsulates a cohesive piece of stateful logic, exposes a clean interface, and handles its own effect cleanup. Poorly designed custom hooks expose internal state that forces consumers to manage dependencies manually, or fail to properly clean up resources.

A production-grade custom hook for debounced values demonstrates best practices:

```javascript
function useDebouncedValue(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return debouncedValue;
}
```

This hook correctly lists all dependencies, provides cleanup for the timer, and presents a simple interface where consumers need only pass the value and delay without managing any internal state. A more sophisticated version might add immediate updates on unmount or support for async values:

```javascript
function useDebouncedValue(value, delay, options = {}) {
  const { leading = false, maxWait = null } = options;
  const [debouncedValue, setDebouncedValue] = useState(value);
  const timeoutRef = useRef(null);
  const maxWaitRef = useRef(null);
  const lastCallTime = useRef(Date.now());
  
  useEffect(() => {
    const currentTime = Date.now();
    const timeSinceLastCall = currentTime - lastCallTime.current;
    
    if (leading && timeSinceLastCall > delay) {
      setDebouncedValue(value);
      lastCallTime.current = currentTime;
      return;
    }
    
    if (maxWait && maxWaitRef.current === null) {
      maxWaitRef.current = setTimeout(() => {
        setDebouncedValue(value);
        lastCallTime.current = Date.now();
        maxWaitRef.current = null;
      }, maxWait);
    }
    
    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(value);
      lastCallTime.current = Date.now();
      if (maxWaitRef.current !== null) {
        clearTimeout(maxWaitRef.current);
        maxWaitRef.current = null;
      }
    }, delay);
    
    return () => {
      if (timeoutRef.current !== null) {
        clearTimeout(timeoutRef.current);
      }
      if (maxWaitRef.current !== null) {
        clearTimeout(maxWaitRef.current);
      }
    };
  }, [value, delay, leading, maxWait]);
  
  return debouncedValue;
}
```

This extended version adds leading-edge triggering and maximum wait guarantees, both critical for production search inputs and autosave features. It maintains multiple refs to track timer state without triggering re-renders, demonstrating proper use of `useRef` for mutable instance data.

The interaction between effects and concurrent rendering introduces new timing considerations. In concurrent mode, React may start rendering a component, pause midway to handle higher-priority work, then resume or restart the render. Effects still fire only after commit, but the component may render multiple times before a single commit occurs. This means effects must be idempotent or properly sequenced to avoid inconsistent state. Similarly, cleanup functions may run while a component is suspended but not yet committed, requiring careful resource management.

The `useLayoutEffect` hook mitigates some concurrent rendering complexity by executing synchronously during commit, but at the cost of blocking paint. Use it only for DOM measurements or mutations that must be visually synchronous with the render. For most state and data management, prefer `useEffect` and design logic to be resilient to concurrent execution.

Effects that depend on previous renders' data require careful state management. A common pattern is the "previous value" hook that tracks the prior render's value:

```javascript
function usePrevious(value) {
  const ref = useRef();
  
  useEffect(() => {
    ref.current = value;
  });
  
  return ref.current;
}
```

This hook exploits effect timing: effects run after render, so `ref.current` contains the value from the previous render during the current render, and gets updated to the current value after render completes. Consumers can compare current and previous values to detect changes or compute deltas.

Memory leaks in hooks-based code almost always trace back to uncleaned subscriptions or abandoned async operations. Every `addEventListener`, `setInterval`, WebSocket connection, or long-running promise chain must have a corresponding cleanup in an effect return function. The pattern is systematic: identify resource allocation in effect body, return cleanup function that releases the resource. React guarantees cleanup invocation before re-running effects and before unmount.

Performance profiling with React DevTools Profiler reveals expensive renders caused by unnecessary hook recalculation. The Profiler tracks how long each component takes to render and why it rendered (props change, state change, parent render). High render times in components using many hooks often indicate missing memoization. Apply `useMemo` to expensive computations, `useCallback` to functions passed to memoized children, and `React.memo` to components that render the same output for the same props. Profile before and after to validate that memoization actually improves performance—premature memoization adds complexity without benefit.

The dependency array exhaustive check has one intentional escape hatch: the ESLint rule allows omitting dependencies that React guarantees to be stable, specifically `setState` functions from `useState`, `dispatch` from `useReducer`, and refs from `useRef`. React ensures these identities never change across renders, making them safe to omit from dependency arrays. However, any other value—props, state, derived values, or variables from parent scopes—must be listed or explicitly excluded with an ESLint disable comment that documents why omission is safe.

Understanding hooks at this mechanical level transforms them from magic into predictable, composable building blocks. The positional correspondence between hook calls and hook nodes, the asynchronous effect scheduling, the shallow dependency comparison, and the closure capture semantics are all deterministic consequences of React's fiber architecture and JavaScript's lexical scoping. Mastery requires internalizing these invariants and designing components that work with rather than against the hook execution model.
