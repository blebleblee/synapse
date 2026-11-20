# Lesson 2: State, Props, Unidirectional Data Flow

## 1. First-Principles Intuition & Invariants

React's architecture rests on a fundamental constraint derived from decades of user interface engineering: mutable shared state kills maintainability at scale. The framework enforces a strict unidirectional data flow model where information moves downward through the component tree via immutable props, while state mutations propagate upward through callback functions. This design emerges from formal functional programming principles, specifically the concept that user interfaces are pure functions mapping application state to DOM representations: `UI = f(state)`. Every re-render constitutes a complete re-evaluation of this function, rather than imperative manipulation of individual DOM nodes.

State encapsulation within React components creates isolated mutation boundaries. Each component owns a private slice of application state through the `useState` hook or class-based `this.state`, ensuring that no external entity can directly mutate that data. This ownership model mirrors operating systems memory protection, where each process maintains its own address space. When a component needs to modify state, it calls a setter function that schedules a reconciliation pass. The reconciler computes a minimal set of DOM mutations by diffing the new virtual DOM tree against the previous snapshot, applying changes through a commit phase that batches updates for optimal browser performance.

Props represent the immutable interface contract between parent and child components. When a parent passes data or callbacks downward, those props become read-only within the child's scope. This immutability guarantee allows React's reconciliation algorithm to perform shallow equality checks (`Object.is` semantics) to determine whether a component requires re-rendering. If props maintain referential stability between renders, React can safely skip subtree reconciliation, dramatically reducing computational overhead. The immutability contract also enables time-travel debugging and replay systems, since every state transition produces a new immutable snapshot rather than mutating existing structures in place.

Unidirectional flow creates deterministic rendering pipelines. Data originates from a single source of truth—typically lifted to the lowest common ancestor component that needs to coordinate multiple children—and flows downward through props. Child components communicate upward exclusively through callback functions passed as props, never by directly mutating parent state. This constraint eliminates circular dependencies and makes the entire component tree a directed acyclic graph where information flows from root to leaves during rendering, and events propagate from leaves to root during interaction handling. The asymmetry mirrors signal processing systems where sensors (child components) emit events to controllers (parent components) that compute new control signals (state updates) propagated back to actuators (re-rendered children).

Controlled components surrender all state authority to their parent, maintaining zero internal state and deriving all behavior from props. An input field becomes controlled when its `value` prop binds to parent state and its `onChange` handler invokes a parent callback that updates that state. Every keystroke triggers a full render cycle: event fires, parent updates state, reconciler computes diffs, DOM commits changes, browser repaints input. This seemingly inefficient round-trip ensures the parent maintains perfect synchronization with UI state, enabling features like validation, formatting, and derived computations. Uncontrolled components, conversely, manage their own internal state through DOM refs, trading React's declarative model for direct imperative DOM access. Use uncontrolled components only for file inputs or when integrating third-party DOM libraries that conflict with React's rendering model.

The state lifting pattern emerges when sibling components need coordinated access to shared data. Rather than duplicating state across siblings or implementing complex message passing, you identify the nearest common ancestor and elevate state to that level. The ancestor becomes the authoritative source, passing state downward as props and callbacks that siblings invoke to request mutations. This pattern scales hierarchically: as coordination requirements expand, state lifts progressively higher until reaching application-level state management systems like Redux or Zustand. The key insight is that state should live at the lowest point in the tree that satisfies all coordination requirements—premature lifting creates unnecessary prop drilling, while insufficient lifting forces awkward workarounds.

## 2. Core Architecture & Mechanics

React's state management implementation revolves around fiber nodes, the internal data structure representing component instances in the reconciliation tree. Each fiber maintains a `memoizedState` field storing the component's current state, implemented as a linked list of state hooks for functional components. When you call `useState`, React appends a new state cell to this list during the initial render. Subsequent renders traverse the same list in order, which explains why hooks must execute in consistent sequence—reordering breaks the position-based lookup mechanism.

```text
Component Fiber Node Memory Layout:

┌─────────────────────────────┐
│ Fiber {                     │
│   memoizedState: StateNode  │◄─── Linked list head
│   updateQueue: UpdateQueue  │
│   memoizedProps: Props      │
│   pendingProps: Props       │
│   ...                       │
└─────────────────────────────┘
                │
                ├──► StateNode { value: 42, next: StateNode }
                │                                  │
                │                                  ├──► StateNode { value: "text", next: null }
                │
                └──► UpdateQueue {
                       pending: Update ──► Update ──► Update (circular)
                     }
```

State updates queue into a circular linked list attached to the fiber's `updateQueue`. When you call a setter function like `setCount(count + 1)`, React doesn't immediately mutate state. Instead, it enqueues an update object containing either the new value or an updater function. During the next reconciliation pass, React processes this queue sequentially, computing the final state by applying each update to the previous result. This batching mechanism allows React to coalesce multiple `setState` calls within the same event handler into a single re-render, avoiding cascading updates that would thrash the DOM.

```javascript
// State update batching mechanics demonstration
function Counter() {
  const [count, setCount] = useState(0);

  function handleClick() {
    // All three updates batch into single render
    setCount(count + 1);  // Enqueues: state => 0 + 1 = 1
    setCount(count + 1);  // Enqueues: state => 0 + 1 = 1  (count still 0!)
    setCount(count + 1);  // Enqueues: state => 0 + 1 = 1
    // Result: count becomes 1, not 3
    
    // Use functional updates for correct accumulation
    setCount(c => c + 1);  // Enqueues: state => prevState + 1
    setCount(c => c + 1);  // Enqueues: state => prevState + 1
    setCount(c => c + 1);  // Enqueues: state => prevState + 1
    // Result: count becomes 3 (sequential reduction over queue)
  }

  return <button onClick={handleClick}>Count: {count}</button>;
}
```

Props flow through the reconciliation tree via the `pendingProps` and `memoizedProps` fiber fields. During render, React invokes your component function with `pendingProps`, then stores the result in `memoizedProps` after commit. The reconciler compares `pendingProps` against `memoizedProps` using shallow equality to determine whether re-rendering is necessary. For object and array props, this check compares memory addresses rather than deep structural equality. If you construct a new object literal or array on every parent render, React sees different references and re-renders the child even if contents match. This behavior motivates the `useMemo` hook, which caches computed values across renders and returns the same reference when dependencies remain stable.

```javascript
// Props referential stability and memoization
function ParentComponent() {
  const [count, setCount] = useState(0);
  
  // ❌ Bad: New object every render, child always re-renders
  const config = { theme: 'dark', locale: 'en' };
  
  // ✓ Good: Stable reference unless dependencies change
  const config = useMemo(
    () => ({ theme: 'dark', locale: 'en' }),
    []  // Empty deps = never recreate
  );
  
  // ❌ Bad: New function every render
  const handleClick = () => setCount(count + 1);
  
  // ✓ Good: Stable callback reference
  const handleClick = useCallback(
    () => setCount(c => c + 1),
    []  // No external dependencies
  );
  
  return <ExpensiveChild config={config} onClick={handleClick} />;
}

// Child only re-renders when props actually change
const ExpensiveChild = React.memo(({ config, onClick }) => {
  console.log('ExpensiveChild rendered');
  return <button onClick={onClick}>{config.theme}</button>;
});
```

Controlled component implementation requires precise synchronization between props and DOM state. When you bind an input's `value` prop to React state, you create a one-way data binding where React owns the authoritative value. Every DOM mutation event must flow through your `onChange` handler, update parent state, trigger reconciliation, and commit the new value back to the input's DOM node. This round-trip takes typically 16ms on modern hardware (one frame at 60Hz), imperceptible to users but measurable in performance profiling.

```javascript
// Controlled input implementation with validation and formatting
function PhoneInput() {
  const [rawValue, setRawValue] = useState('');
  
  // Derived state: format for display, validate for submission
  const formattedValue = useMemo(() => {
    const digits = rawValue.replace(/\D/g, '');
    if (digits.length <= 3) return digits;
    if (digits.length <= 6) return `(${digits.slice(0,3)}) ${digits.slice(3)}`;
    return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6,10)}`;
  }, [rawValue]);
  
  const isValid = /^\d{10}$/.test(rawValue.replace(/\D/g, ''));
  
  function handleChange(event) {
    const input = event.target.value;
    // Strip formatting, store raw digits
    const digits = input.replace(/\D/g, '').slice(0, 10);
    setRawValue(digits);
  }
  
  return (
    <div>
      <input 
        type="text"
        value={formattedValue}  // Display formatted version
        onChange={handleChange}
        aria-invalid={!isValid}
      />
      <button disabled={!isValid}>Submit</button>
    </div>
  );
}
```

Uncontrolled components operate through DOM refs that provide imperative access to underlying nodes. The `useRef` hook creates a mutable container whose `.current` property persists across renders without triggering reconciliation. For form inputs, you access values directly from the DOM rather than tracking them in React state. This approach suits file inputs (which can't be controlled due to security restrictions) and integration with legacy jQuery plugins or imperative animation libraries that mutate DOM outside React's knowledge.

```javascript
// Uncontrolled component with ref-based access
function UncontrolledForm() {
  const emailRef = useRef(null);
  const fileRef = useRef(null);
  
  function handleSubmit(event) {
    event.preventDefault();
    
    // Read current values directly from DOM
    const email = emailRef.current.value;
    const file = fileRef.current.files[0];
    
    console.log('Submitting:', { email, fileName: file?.name });
    
    // Imperative DOM manipulation (React won't know about this)
    emailRef.current.style.backgroundColor = 'green';
    setTimeout(() => {
      emailRef.current.style.backgroundColor = '';
    }, 500);
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input 
        ref={emailRef}
        type="email"
        defaultValue="user@example.com"  // Note: defaultValue, not value
      />
      <input 
        ref={fileRef}
        type="file"  // Must be uncontrolled
      />
      <button type="submit">Submit</button>
    </form>
  );
}
```

State lifting manifests concretely through callback prop threading. When sibling components need synchronized state, you identify their lowest common ancestor, move state declarations upward, and pass both state values and setter functions downward as props. The pattern scales through multiple levels: grandchild components receive deeply nested callbacks that eventually invoke state setters defined many layers above. This creates "prop drilling" where intermediate components pass props they don't use, purely to relay them deeper. While sometimes unavoidable, excessive drilling signals a need for context providers or external state management.

```javascript
// State lifting pattern with coordinated siblings
function TodoApp() {
  const [todos, setTodos] = useState([
    { id: 1, text: 'Learn React', done: false },
    { id: 2, text: 'Build project', done: false },
  ]);
  const [filter, setFilter] = useState('all');  // 'all' | 'active' | 'done'
  
  // Derived state: compute filtered view
  const filteredTodos = useMemo(() => {
    switch(filter) {
      case 'active': return todos.filter(t => !t.done);
      case 'done': return todos.filter(t => t.done);
      default: return todos;
    }
  }, [todos, filter]);
  
  // Callback passed to AddTodo child
  function handleAdd(text) {
    setTodos([...todos, { 
      id: Date.now(), 
      text, 
      done: false 
    }]);
  }
  
  // Callback passed to TodoList child
  function handleToggle(id) {
    setTodos(todos.map(t => 
      t.id === id ? { ...t, done: !t.done } : t
    ));
  }
  
  function handleDelete(id) {
    setTodos(todos.filter(t => t.id !== id));
  }
  
  return (
    <div>
      <AddTodo onAdd={handleAdd} />
      <FilterBar filter={filter} onFilterChange={setFilter} />
      <TodoList 
        todos={filteredTodos} 
        onToggle={handleToggle}
        onDelete={handleDelete}
      />
      <TodoStats todos={todos} />
    </div>
  );
}

function AddTodo({ onAdd }) {
  const [input, setInput] = useState('');
  
  function handleSubmit(e) {
    e.preventDefault();
    if (input.trim()) {
      onAdd(input.trim());  // Call parent callback
      setInput('');
    }
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input 
        value={input} 
        onChange={e => setInput(e.target.value)}
        placeholder="What needs doing?"
      />
      <button>Add</button>
    </form>
  );
}

function FilterBar({ filter, onFilterChange }) {
  return (
    <div>
      {['all', 'active', 'done'].map(f => (
        <button 
          key={f}
          disabled={filter === f}
          onClick={() => onFilterChange(f)}
        >
          {f}
        </button>
      ))}
    </div>
  );
}

function TodoList({ todos, onToggle, onDelete }) {
  return (
    <ul>
      {todos.map(todo => (
        <TodoItem 
          key={todo.id}
          todo={todo}
          onToggle={() => onToggle(todo.id)}
          onDelete={() => onDelete(todo.id)}
        />
      ))}
    </ul>
  );
}

function TodoItem({ todo, onToggle, onDelete }) {
  return (
    <li>
      <input 
        type="checkbox"
        checked={todo.done}
        onChange={onToggle}
      />
      <span style={{ 
        textDecoration: todo.done ? 'line-through' : 'none' 
      }}>
        {todo.text}
      </span>
      <button onClick={onDelete}>Delete</button>
    </li>
  );
}

function TodoStats({ todos }) {
  const active = todos.filter(t => !t.done).length;
  const done = todos.filter(t => t.done).length;
  
  return (
    <div>
      {active} active, {done} completed, {todos.length} total
    </div>
  );
}
```

## 3. High-Performance Optimization & Failure Modes

State update batching breaks down in asynchronous contexts outside React's control. Calls to `setState` inside native event handlers, promises, or `setTimeout` callbacks don't automatically batch in React 17 and earlier. React 18 introduces automatic batching for all updates via the new concurrent rendering engine, but understanding the legacy behavior remains critical for maintaining older codebases. When batching fails, each `setState` triggers a separate render pass, potentially causing visible UI flashing or degraded frame rates.

```javascript
// Batching behavior across React versions
function AsyncUpdates() {
  const [count, setCount] = useState(0);
  const [flag, setFlag] = useState(false);
  
  function handleClick() {
    // React 17: Batched (single render)
    // React 18: Batched (single render)
    setCount(c => c + 1);
    setFlag(f => !f);
    console.log('Synchronous updates batched');
  }
  
  function handleAsyncClick() {
    setTimeout(() => {
      // React 17: NOT batched (two renders)
      // React 18: Batched (single render)
      setCount(c => c + 1);
      setFlag(f => !f);
      console.log('Async updates behavior varies by version');
    }, 100);
  }
  
  function handlePromiseClick() {
    fetch('/api/data')
      .then(() => {
        // React 17: NOT batched (two renders)
        // React 18: Batched (single render)
        setCount(c => c + 1);
        setFlag(f => !f);
      });
  }
  
  // React 17 workaround: manual batching
  function handleAsyncBatched() {
    setTimeout(() => {
      ReactDOM.unstable_batchedUpdates(() => {
        setCount(c => c + 1);
        setFlag(f => !f);
      });
    }, 100);
  }
  
  return (
    <div>
      <div>Count: {count}, Flag: {flag.toString()}</div>
      <button onClick={handleClick}>Sync Update</button>
      <button onClick={handleAsyncClick}>Async Update</button>
      <button onClick={handlePromiseClick}>Promise Update</button>
    </div>
  );
}
```

Object and array state updates require careful immutability discipline. Directly mutating state objects or arrays breaks React's shallow equality checks, causing the reconciler to skip re-renders since memory addresses match. You must create new object or array instances using spread syntax, `Object.assign`, or immutable update libraries. For deeply nested structures, immutability becomes tedious and error-prone. Consider using Immer, which provides a draft-based API that tracks mutations and produces immutable outputs automatically.

```javascript
// Immutable update patterns for complex state
function UserProfile() {
  const [user, setUser] = useState({
    name: 'Alice',
    email: 'alice@example.com',
    preferences: {
      theme: 'dark',
      notifications: {
        email: true,
        push: false,
      },
    },
    friends: ['Bob', 'Carol'],
  });
  
  // ❌ Wrong: Direct mutation doesn't trigger re-render
  function wrongUpdate() {
    user.preferences.theme = 'light';
    setUser(user);  // Same reference, React skips render
  }
  
  // ✓ Correct: Manual immutable update (verbose)
  function correctUpdate() {
    setUser({
      ...user,
      preferences: {
        ...user.preferences,
        theme: 'light',
      },
    });
  }
  
  // ✓ Better: Using Immer for clean mutation syntax
  function immerUpdate() {
    setUser(produce(draft => {
      draft.preferences.theme = 'light';  // Mutate draft freely
    }));  // Immer returns new immutable object
  }
  
  // Array updates: always create new array
  function addFriend(name) {
    // ❌ Wrong: push mutates original array
    // user.friends.push(name);
    // setUser(user);
    
    // ✓ Correct: spread creates new array
    setUser({
      ...user,
      friends: [...user.friends, name],
    });
  }
  
  function removeFriend(name) {
    setUser({
      ...user,
      friends: user.friends.filter(f => f !== name),
    });
  }
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>Theme: {user.preferences.theme}</p>
      <ul>
        {user.friends.map(f => (
          <li key={f}>
            {f} <button onClick={() => removeFriend(f)}>Remove</button>
          </li>
        ))}
      </ul>
      <button onClick={correctUpdate}>Toggle Theme</button>
    </div>
  );
}
```

Stale closures plague state updates in event handlers and effects. When you capture state variables in a callback function, JavaScript creates a closure over those values at definition time. If the callback executes later, it references the stale values from the render when it was created, not the current state. Use functional updates (`setState(prev => ...)`) to access the latest state within the setter, or include state variables in `useCallback` dependency arrays to recreate callbacks when state changes.

```javascript
// Stale closure debugging and resolution
function Timer() {
  const [count, setCount] = useState(0);
  const [running, setRunning] = useState(false);
  
  // ❌ Stale closure: captures count = 0 forever
  function wrongInterval() {
    setInterval(() => {
      setCount(count + 1);  // Always sets to 0 + 1 = 1
    }, 1000);
  }
  
  // ✓ Correct: functional update accesses latest state
  function correctInterval() {
    setInterval(() => {
      setCount(prev => prev + 1);  // Always increments current value
    }, 1000);
  }
  
  // ❌ Stale closure in effect
  useEffect(() => {
    if (!running) return;
    
    const timer = setInterval(() => {
      console.log('Count:', count);  // Logs initial count forever
      setCount(count + 1);  // Broken increment
    }, 1000);
    
    return () => clearInterval(timer);
  }, [running]);  // Missing count in deps
  
  // ✓ Correct: include all closure dependencies
  useEffect(() => {
    if (!running) return;
    
    const timer = setInterval(() => {
      console.log('Count:', count);  // Logs current count
      setCount(prev => prev + 1);  // Functional update
    }, 1000);
    
    return () => clearInterval(timer);
  }, [running, count]);  // Effect re-runs when count changes
  
  // ✓ Alternative: useRef for stable mutable container
  const countRef = useRef(count);
  countRef.current = count;  // Update ref every render
  
  useEffect(() => {
    if (!running) return;
    
    const timer = setInterval(() => {
      console.log('Count:', countRef.current);  // Always latest
      setCount(prev => prev + 1);
    }, 1000);
    
    return () => clearInterval(timer);
  }, [running]);  // Only re-run when running changes
  
  return (
    <div>
      <div>Count: {count}</div>
      <button onClick={() => setRunning(!running)}>
        {running ? 'Pause' : 'Start'}
      </button>
    </div>
  );
}
```

Props drilling creates maintenance burden and couples components unnecessarily. When callbacks thread through five levels of components, intermediate layers become fragile to refactoring. Three primary solutions exist: Context API for application-wide state (theme, authentication), composition through `children` props to avoid intermediate pass-through, and external state libraries like Redux or Zustand for complex coordination. Context provides elegant ergonomics but triggers re-renders of all consumers when any context value changes. For high-frequency updates, split contexts by update frequency or use selector-based libraries.

```javascript
// Solving prop drilling with Context and composition
const ThemeContext = createContext();
const UserContext = createContext();

// Context provider at app root
function App() {
  const [theme, setTheme] = useState('dark');
  const [user, setUser] = useState(null);
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <UserContext.Provider value={{ user, setUser }}>
        <Layout>
          <Dashboard />
        </Layout>
      </UserContext.Provider>
    </ThemeContext.Provider>
  );
}

// Deep child accesses context without prop drilling
function ThemeToggle() {
  const { theme, setTheme } = useContext(ThemeContext);
  
  return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      Current: {theme}
    </button>
  );
}

// Composition pattern: pass complete UI as children
function Layout({ children }) {
  const { theme } = useContext(ThemeContext);
  
  return (
    <div className={`layout-${theme}`}>
      <Header />
      <main>{children}</main>  {/* No prop drilling needed */}
      <Footer />
    </div>
  );
}

// Context re-render optimization: split by update frequency
const ThemeContext = createContext();
const ThemeUpdateContext = createContext();

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('dark');
  
  // Theme value changes rarely, update function never changes
  return (
    <ThemeContext.Provider value={theme}>
      <ThemeUpdateContext.Provider value={setTheme}>
        {children}
      </ThemeUpdateContext.Provider>
    </ThemeContext.Provider>
  );
}

// Component only re-renders when theme value changes
function ThemedComponent() {
  const theme = useContext(ThemeContext);
  return <div className={theme}>Content</div>;
}

// Component never re-renders (setTheme reference stable)
function ThemeControls() {
  const setTheme = useContext(ThemeUpdateContext);
  return <button onClick={() => setTheme('light')}>Light Mode</button>;
}
```

Controlled components introduce input latency when state updates execute expensive computations. Every keystroke triggers the full render pipeline, and if your `onChange` handler performs slow validation or formatting, users experience visible lag between typing and character appearance. Debounce expensive operations using timers, or maintain separate `inputValue` and `validatedValue` state slices where the former updates immediately for responsive typing while the latter updates after a delay for heavy processing.

```javascript
// Optimizing controlled input responsiveness
function SearchInput() {
  const [inputValue, setInputValue] = useState('');
  const [debouncedValue, setDebouncedValue] = useState('');
  const [results, setResults] = useState([]);
  
  // Debounce expensive search operation
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(inputValue);
    }, 300);
    
    return () => clearTimeout(timer);
  }, [inputValue]);
  
  // Heavy operation only runs on debounced value
  useEffect(() => {
    if (!debouncedValue) {
      setResults([]);
      return;
    }
    
    async function search() {
      const response = await fetch(`/api/search?q=${debouncedValue}`);
      const data = await response.json();
      setResults(data);
    }
    
    search();
  }, [debouncedValue]);
  
  return (
    <div>
      <input 
        value={inputValue}  // Immediate update for responsive typing
        onChange={e => setInputValue(e.target.value)}
        placeholder="Search..."
      />
      <ul>
        {results.map(r => <li key={r.id}>{r.title}</li>)}
      </ul>
    </div>
  );
}

// Optimizing expensive validation/formatting
function FormattedInput() {
  const [rawValue, setRawValue] = useState('');
  
  // Heavy computation deferred using useMemo
  const formattedValue = useMemo(() => {
    // Expensive formatting logic here
    return expensiveFormat(rawValue);
  }, [rawValue]);
  
  // Validation runs on debounced value, not every keystroke
  const [debouncedRaw, setDebouncedRaw] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedRaw(rawValue), 500);
    return () => clearTimeout(timer);
  }, [rawValue]);
  
  const validationErrors = useMemo(() => 
    expensiveValidation(debouncedRaw),
    [debouncedRaw]
  );
  
  return (
    <div>
      <input 
        value={formattedValue}
        onChange={e => setRawValue(e.target.value)}
      />
      {validationErrors.length > 0 && (
        <ul>
          {validationErrors.map((err, i) => <li key={i}>{err}</li>)}
        </ul>
      )}
    </div>
  );
}
```

State synchronization bugs emerge when derived state falls out of sync with its source. Never store computed values in separate state—derive them inline or via `useMemo`. If you cache a filtered list in state and forget to update it when the source array changes, your UI displays stale data. Similarly, lifting state incorrectly can create split-brain scenarios where sibling components operate on inconsistent snapshots. Always maintain a single source of truth and compute views on demand.

```javascript
// Avoiding derived state anti-patterns
function ProductList({ products }) {
  const [filter, setFilter] = useState('');
  
  // ❌ Wrong: Derived state can desync
  const [filteredProducts, setFilteredProducts] = useState(products);
  
  useEffect(() => {
    setFilteredProducts(
      products.filter(p => p.name.includes(filter))
    );
  }, [products, filter]);  // Easy to forget dependencies
  
  // ✓ Correct: Compute derived value inline
  const filteredProducts = useMemo(
    () => products.filter(p => p.name.includes(filter)),
    [products, filter]
  );
  
  return (
    <div>
      <input value={filter} onChange={e => setFilter(e.target.value)} />
      <ul>
        {filteredProducts.map(p => <li key={p.id}>{p.name}</li>)}
      </ul>
    </div>
  );
}

// Maintaining single source of truth across siblings
function InventoryManager() {
  // ✓ Single source of truth at common ancestor
  const [inventory, setInventory] = useState([
    { id: 1, name: 'Widget', stock: 10, reserved: 2 },
    { id: 2, name: 'Gadget', stock: 5, reserved: 1 },
  ]);
  
  // Derived state: compute available stock
  const availableStock = useMemo(
    () => inventory.map(item => ({
      ...item,
      available: item.stock - item.reserved,
    })),
    [inventory]
  );
  
  function handleReserve(id, quantity) {
    setInventory(inventory.map(item =>
      item.id === id
        ? { ...item, reserved: item.reserved + quantity }
        : item
    ));
  }
  
  function handleRestock(id, quantity) {
    setInventory(inventory.map(item =>
      item.id === id
        ? { ...item, stock: item.stock + quantity }
        : item
    ));
  }
  
  return (
    <div>
      <StockDisplay items={availableStock} />
      <ReservationForm items={availableStock} onReserve={handleReserve} />
      <RestockForm items={inventory} onRestock={handleRestock} />
    </div>
  );
}
```

React's state model scales from simple counters to complex applications through consistent application of these architectural invariants: unidirectional flow eliminates circular dependencies, immutable props enable efficient reconciliation, and state encapsulation creates isolated mutation boundaries. Master these fundamentals before reaching for external state management libraries—most applications require only local state, Context API, and disciplined component composition.
