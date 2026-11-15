# Lesson 4: Behavioral Patterns

## 1. First-Principles Intuition & Invariants

Behavioral patterns represent a fundamental shift in how we think about software architecture. Where structural patterns concern themselves with the static topology of object graphs and creational patterns address the controlled instantiation of objects, behavioral patterns encode the *temporal dynamics* of computation itself—the flow of control, the propagation of state changes, and the protocols by which objects communicate. They capture not what the system *is*, but what it *does* and how it *evolves* through time.

At their core, behavioral patterns emerge from a single invariant: complex computational behavior should be decomposed into interchangeable, composable units that can be reasoned about independently. This principle mirrors the mathematical notion of functions as first-class values, but extends it into the object-oriented domain where behavior couples tightly with state. When we implement a Strategy pattern, we are not merely selecting an algorithm—we are reifying a computational *trajectory* as an object that can be passed, stored, and substituted. When we build a Chain of Responsibility, we are constructing a linked computational pipeline where each node makes a localized decision about whether to process, transform, or forward a request.

The tension that behavioral patterns resolve is between *flexibility* and *predictability*. Raw procedural code with conditional branches and function pointers offers maximum flexibility but quickly becomes incomprehensible as complexity grows. Conversely, rigid class hierarchies with fixed method dispatch provide predictability but lock behavior into compile-time decisions. Behavioral patterns occupy the Pareto-optimal frontier: they provide runtime flexibility through polymorphism while maintaining compile-time type safety and architectural clarity through well-defined interfaces.

Consider the fundamental problem of *control flow inversion*. In traditional procedural code, the application controls when and how libraries are invoked—the application sits at the top of the call stack and pushes control downward. Behavioral patterns like Template Method and Command invert this relationship: the framework or infrastructure layer defines the overall flow, while application-specific behavior slots in through polymorphic dispatch. This inversion enables powerful abstractions like event loops, transactional systems, and undo/redo mechanisms that would be intractable with direct procedural control.

The Observer pattern exemplifies another invariant: *decoupling through indirection*. When one object's state change must trigger updates in multiple dependent objects, the naive solution creates a tightly coupled mesh where the subject holds direct references to all observers. This violates the Open/Closed Principle and makes the system brittle. Observer introduces an indirection layer—a registration protocol and notification interface—that allows observers to attach and detach dynamically without the subject knowing their concrete types. This pattern appears throughout systems programming: POSIX signals, GUI event systems, reactive streams, and publish-subscribe message buses all implement Observer semantics.

Behavioral patterns also encode *separation of concerns* at a finer granularity than traditional architectural layering. The Visitor pattern, for instance, separates the traversal logic of a composite data structure from the operations performed at each node. This allows adding new operations without modifying the structure classes, a critical property when working with abstract syntax trees, scene graphs, or any domain where the structure is stable but the operations evolve. The double-dispatch mechanism at Visitor's heart—where both the visitor type and the element type participate in method selection—elegantly solves the expression problem in languages without multiple dispatch.

The State pattern addresses a particularly insidious source of bugs: implicit finite state machines embedded in conditional logic. When an object's behavior depends on its internal state, naive implementations scatter conditionals throughout multiple methods, creating hidden state transitions that are difficult to test and debug. State reifies each logical state as an explicit class, making transitions visible, testable, and subject to invariant checking. This transformation from implicit to explicit state machines mirrors the principle in compiler design where ad-hoc lexical analysis gives way to formal automata theory.

Memento tackles the orthogonal concern of *temporal logic*—the ability to snapshot, restore, and reason about an object's state at different points in time. By externalizing an object's internal state into an opaque token, Memento enables undo mechanisms, checkpointing, and transactional rollback without violating encapsulation. The pattern's invariant is simple but powerful: state capture must be atomic and the captured state must be sufficient for complete restoration. This principle underlies database snapshots, virtual machine checkpoints, and version control systems.

The Iterator pattern solves the fundamental problem of *traversal abstraction*. Collections can be implemented using arrays, linked lists, trees, or hash tables, each with different traversal characteristics. Iterator provides a uniform interface for sequential access, hiding the underlying structure and enabling collection-agnostic algorithms. This abstraction appears in C++ Standard Template Library iterators, Java's `Iterable` interface, Python's iterator protocol, and Rust's `Iterator` trait. The key invariant is that iterators must preserve the collection's logical ordering while allowing efficient traversal of the physical representation.

Chain of Responsibility embodies the principle of *successive refinement*. Rather than centralizing request handling in a monolithic dispatcher that must know about all possible handlers, Chain distributes the responsibility across a linked sequence where each handler has the autonomy to process, delegate, or refuse. This pattern appears in middleware stacks, exception handling mechanisms, and event bubbling in DOM hierarchies. The invariant is that each handler maintains a single successor reference and makes a local decision without global knowledge, enabling dynamic reconfiguration and graceful degradation.

The Command pattern reifies *actions as values*, transforming imperative procedure calls into serializable, queueable, and reversible objects. This transformation unlocks powerful capabilities: macro recording, transactional systems, job queues, and remote procedure calls. Command objects capture both the operation and its parameters, effectively creating a closure that can be executed in a different context—a different thread, a different process, or a different point in time. The pattern's invariant is that command execution must be idempotent with respect to command creation, meaning command objects can be created early and executed later without state corruption.

Mediator addresses the *communication explosion* problem in systems where multiple objects interact. When N objects can communicate with any other, the coupling grows as O(N²), creating a maintenance nightmare. Mediator centralizes communication logic in a hub object, reducing coupling to O(N). This pattern appears in GUI dialog controllers, chat room servers, and air traffic control systems—any domain where complex interaction protocols must be coordinated. The tradeoff is that the mediator itself can become a bottleneck or a god object, requiring careful design to maintain cohesion.

The Strategy pattern separates *policy from mechanism*. When an algorithm's implementation must vary based on runtime conditions or client preferences, Strategy encapsulates each variation as an interchangeable object conforming to a common interface. This enables A/B testing, runtime configuration, and adaptive algorithms without conditional logic pollution. The pattern's power lies in its simplicity: rather than embedding algorithmic choice in control flow, we make it a data-driven selection of which object to use.

Template Method defines the *skeleton of an algorithm*, deferring specific steps to subclasses. This pattern enforces algorithmic structure while allowing customization at well-defined extension points. Unlike Strategy which swaps entire algorithms, Template Method maintains a fixed overall flow with variable steps. This appears in framework lifecycle hooks, parsing pipelines, and protocol implementations where the high-level procedure is invariant but individual phases require specialization.

These patterns share a common meta-pattern: they transform runtime behavior from implicit control flow into explicit data structures that can be inspected, modified, and composed. By reifying temporal dynamics as objects, behavioral patterns make the invisible visible and the implicit explicit, enabling powerful forms of metaprogramming and architectural flexibility that remain type-safe and maintainable.

## 2. Core Architecture & Mechanics

### Chain of Responsibility: Linked Request Processing

Chain of Responsibility constructs a pipeline of handler objects, each maintaining a reference to its successor. When a request enters the chain, each handler examines it and decides whether to process it, delegate to the next handler, or both. The mechanical implementation requires three components: a handler interface defining the processing contract, concrete handler implementations encoding specific processing logic, and a client that initiates the chain by sending requests to the first handler.

The handler interface typically declares an abstract method `handleRequest(request)` and maintains a `next` reference to the successor handler. Concrete handlers implement the processing logic by first checking whether they can handle the request. If so, they process it and may optionally pass it to the successor for further processing. If not, they immediately delegate to the successor. The chain terminates when a handler with no successor is reached or when a handler explicitly stops propagation.

```rust
trait Handler {
    fn set_next(&mut self, next: Box<dyn Handler>);
    fn handle(&self, request: &Request) -> Option<Response>;
}

struct AuthenticationHandler {
    next: Option<Box<dyn Handler>>,
}

impl Handler for AuthenticationHandler {
    fn set_next(&mut self, next: Box<dyn Handler>) {
        self.next = Some(next);
    }
    
    fn handle(&self, request: &Request) -> Option<Response> {
        if !request.has_valid_token() {
            return Some(Response::Unauthorized);
        }
        // Authenticated - pass to next handler
        self.next.as_ref().and_then(|h| h.handle(request))
    }
}

struct RateLimitHandler {
    next: Option<Box<dyn Handler>>,
    limit: RateLimiter,
}

impl Handler for RateLimitHandler {
    fn set_next(&mut self, next: Box<dyn Handler>) {
        self.next = Some(next);
    }
    
    fn handle(&self, request: &Request) -> Option<Response> {
        if !self.limit.check(request.client_id()) {
            return Some(Response::TooManyRequests);
        }
        self.next.as_ref().and_then(|h| h.handle(request))
    }
}

struct BusinessLogicHandler;

impl Handler for BusinessLogicHandler {
    fn set_next(&mut self, _: Box<dyn Handler>) {}
    
    fn handle(&self, request: &Request) -> Option<Response> {
        Some(process_business_logic(request))
    }
}
```

The chain assembly occurs at initialization, creating a linked sequence where each handler knows only its immediate successor. This topology enables dynamic reconfiguration—handlers can be inserted, removed, or reordered at runtime without affecting other handlers. The request flows through the chain like a packet through a network pipeline, with each handler acting as a filter or transformer.

```
Request → [Auth] → [RateLimit] → [Validation] → [BusinessLogic] → Response
           ↓ reject   ↓ reject      ↓ reject       ↓ process
        401 Unauthorized  429 TooManyRequests  400 BadRequest
```

The pattern's mechanical elegance lies in its locality property: each handler implements a focused concern without knowledge of the overall pipeline structure. This enables concerns like logging, metrics collection, and circuit breaking to be injected as handlers without modifying existing code. The chain can also implement short-circuiting behavior where early handlers reject requests before expensive operations occur, a critical optimization for high-throughput services.

### Command: Reifying Actions as Objects

Command encapsulates a request as an object, decoupling the operation's invocation from its execution. Each command object holds the receiver (the object that will perform the action), the method to invoke, and any necessary parameters. This transformation from procedure call to data structure enables queuing, logging, undoing, and remote execution of operations.

The core architecture consists of four participants: the Command interface declaring an `execute()` method, concrete Command implementations that bind a receiver and action, the Invoker that triggers command execution, and the Receiver that implements the actual business logic. The separation between invoker and receiver means the invoker knows nothing about what operations are being performed—it merely calls `execute()` on command objects.

```rust
trait Command {
    fn execute(&mut self) -> Result<(), Error>;
    fn undo(&mut self) -> Result<(), Error>;
}

struct TextEditor {
    content: String,
    cursor: usize,
}

impl TextEditor {
    fn insert_at(&mut self, pos: usize, text: &str) {
        self.content.insert_str(pos, text);
        self.cursor = pos + text.len();
    }
    
    fn delete_range(&mut self, start: usize, end: usize) -> String {
        self.content.drain(start..end).collect()
    }
}

struct InsertCommand {
    editor: Rc<RefCell<TextEditor>>,
    position: usize,
    text: String,
}

impl Command for InsertCommand {
    fn execute(&mut self) -> Result<(), Error> {
        self.editor.borrow_mut().insert_at(self.position, &self.text);
        Ok(())
    }
    
    fn undo(&mut self) -> Result<(), Error> {
        let end = self.position + self.text.len();
        self.editor.borrow_mut().delete_range(self.position, end);
        Ok(())
    }
}

struct DeleteCommand {
    editor: Rc<RefCell<TextEditor>>,
    start: usize,
    end: usize,
    deleted_text: String,
}

impl Command for DeleteCommand {
    fn execute(&mut self) -> Result<(), Error> {
        self.deleted_text = self.editor.borrow_mut()
            .delete_range(self.start, self.end);
        Ok(())
    }
    
    fn undo(&mut self) -> Result<(), Error> {
        self.editor.borrow_mut().insert_at(self.start, &self.deleted_text);
        Ok(())
    }
}

struct CommandHistory {
    executed: Vec<Box<dyn Command>>,
    undone: Vec<Box<dyn Command>>,
}

impl CommandHistory {
    fn execute(&mut self, mut cmd: Box<dyn Command>) -> Result<(), Error> {
        cmd.execute()?;
        self.executed.push(cmd);
        self.undone.clear(); // Clear redo stack on new command
        Ok(())
    }
    
    fn undo(&mut self) -> Result<(), Error> {
        if let Some(mut cmd) = self.executed.pop() {
            cmd.undo()?;
            self.undone.push(cmd);
            Ok(())
        } else {
            Err(Error::NothingToUndo)
        }
    }
    
    fn redo(&mut self) -> Result<(), Error> {
        if let Some(mut cmd) = self.undone.pop() {
            cmd.execute()?;
            self.executed.push(cmd);
            Ok(())
        } else {
            Err(Error::NothingToRedo)
        }
    }
}
```

The command history maintains two stacks: executed commands (for undo) and undone commands (for redo). Each command stores sufficient state to reverse its effects, enabling bidirectional traversal through the operation history. This mechanism underlies every undo system in text editors, graphics programs, and CAD tools.

Commands can be composed into macro commands that execute multiple operations atomically. A "bold text" command might compose a "select range" command with a "apply formatting" command. Macro commands execute their sub-commands in sequence during `execute()` and reverse them during `undo()`, implementing transaction-like all-or-nothing semantics.

```
CommandQueue: [Insert("h")] → [Insert("e")] → [Insert("l")] → [Delete(2,3)] → [Insert("lp")]
                    ↓              ↓              ↓               ↓                ↓
State:         ""  → "h"        → "he"         → "hel"         → "he"          → "help"

Undo sequence: help → he → hel → he → h → ""
```

Command objects serialize naturally, enabling distributed transaction logs, event sourcing architectures, and command replay for debugging. In distributed systems, commands sent over the network become a form of remote procedure call where the receiver reconstructs the command object and executes it in its local context.

### Iterator: Traversal Abstraction

Iterator provides a uniform protocol for sequential access to elements in a collection, hiding the underlying representation. The pattern separates traversal logic from the collection's storage mechanism, enabling algorithms written against the iterator interface to work with any collection type. This abstraction is fundamental to generic programming and appears in every modern language's standard library.

The iterator protocol requires two interfaces: Iterator (providing `next()` to retrieve elements) and Iterable (providing `iterator()` to create iterators). The iterator maintains traversal state—typically a position or cursor—and returns elements on demand. When no elements remain, `next()` returns a sentinel value or raises an exception, depending on language conventions.

```rust
trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;
}

struct BinaryTreeNode<T> {
    value: T,
    left: Option<Box<BinaryTreeNode<T>>>,
    right: Option<Box<BinaryTreeNode<T>>>,
}

enum TreeTraversal {
    InOrder,
    PreOrder,
    PostOrder,
}

struct TreeIterator<'a, T> {
    stack: Vec<(&'a BinaryTreeNode<T>, u8)>, // (node, visit_count)
    traversal: TreeTraversal,
}

impl<'a, T> TreeIterator<'a, T> {
    fn new(root: &'a BinaryTreeNode<T>, traversal: TreeTraversal) -> Self {
        let mut iter = TreeIterator {
            stack: Vec::new(),
            traversal,
        };
        if matches!(traversal, TreeTraversal::InOrder | TreeTraversal::PreOrder) {
            iter.stack.push((root, 0));
        } else {
            iter.stack.push((root, 0));
        }
        iter
    }
}

impl<'a, T> Iterator for TreeIterator<'a, T> {
    type Item = &'a T;
    
    fn next(&mut self) -> Option<Self::Item> {
        while let Some((node, visit_count)) = self.stack.pop() {
            match (self.traversal, visit_count) {
                (TreeTraversal::PreOrder, 0) => {
                    // Visit node first
                    if let Some(ref right) = node.right {
                        self.stack.push((right, 0));
                    }
                    if let Some(ref left) = node.left {
                        self.stack.push((left, 0));
                    }
                    return Some(&node.value);
                }
                (TreeTraversal::InOrder, 0) => {
                    // Traverse left, then visit, then right
                    if let Some(ref right) = node.right {
                        self.stack.push((right, 0));
                    }
                    self.stack.push((node, 1)); // Mark for visit
                    if let Some(ref left) = node.left {
                        self.stack.push((left, 0));
                    }
                }
                (TreeTraversal::InOrder, 1) => {
                    return Some(&node.value);
                }
                (TreeTraversal::PostOrder, 0) => {
                    self.stack.push((node, 1)); // Mark for visit after children
                    if let Some(ref right) = node.right {
                        self.stack.push((right, 0));
                    }
                    if let Some(ref left) = node.left {
                        self.stack.push((left, 0));
                    }
                }
                (TreeTraversal::PostOrder, 1) => {
                    return Some(&node.value);
                }
                _ => {}
            }
        }
        None
    }
}
```

The tree iterator demonstrates how complex traversal state—in this case, an explicit stack replacing the implicit call stack of recursive traversal—hides behind the simple `next()` interface. Clients iterate without knowing whether they're traversing an array, linked list, or tree, and without knowing the traversal order.

Iterators compose elegantly with higher-order operations like `map`, `filter`, and `fold`. These combinators create iterator chains that process elements lazily without materializing intermediate collections. A filter iterator wraps another iterator and skips elements that don't satisfy a predicate. A map iterator transforms each element using a function. These compositions fuse at the machine code level, eliminating allocation overhead.

```rust
// Iterator pipeline with zero intermediate allocations
let result: Vec<u32> = tree.iter()
    .filter(|x| **x % 2 == 0)      // Keep even numbers
    .map(|x| x * x)                 // Square them
    .take(10)                       // Take first 10
    .collect();                     // Materialize into Vec
```

Internal iteration—where the collection controls the loop and calls a user-provided closure for each element—contrasts with external iteration where the client controls the loop. Languages like Java support both through `forEach` methods (internal) and `Iterator` interfaces (external). External iteration offers more control, enabling early termination and element skipping, while internal iteration enables better optimization through inlining.

### Mediator: Centralized Communication Protocol

Mediator defines an object that encapsulates how a set of objects interact, promoting loose coupling by preventing objects from referring to each other explicitly. Rather than objects maintaining direct references to collaborators, they hold a reference to a mediator that coordinates interactions. This pattern appears in GUI dialog boxes where widget changes trigger updates to other widgets, in chat systems where the chat room mediates message delivery, and in air traffic control where the tower coordinates aircraft without aircraft communicating directly.

The architecture consists of the Mediator interface defining communication operations, concrete Mediator implementations encoding coordination logic, and Colleague classes that communicate through the mediator. Each colleague holds a mediator reference and notifies it of state changes rather than directly calling methods on other colleagues.

```rust
trait Mediator {
    fn notify(&self, sender: &str, event: Event);
}

enum Event {
    ButtonClicked(String),
    TextChanged(String),
    CheckboxToggled(bool),
}

struct DialogMediator {
    submit_button: RefCell<Button>,
    email_field: RefCell<TextField>,
    terms_checkbox: RefCell<Checkbox>,
}

impl Mediator for DialogMediator {
    fn notify(&self, sender: &str, event: Event) {
        match (sender, event) {
            ("email_field", Event::TextChanged(text)) => {
                // Enable submit button only if email is valid and terms accepted
                let valid_email = text.contains('@');
                let terms_accepted = self.terms_checkbox.borrow().is_checked();
                self.submit_button.borrow_mut()
                    .set_enabled(valid_email && terms_accepted);
            }
            ("terms_checkbox", Event::CheckboxToggled(checked)) => {
                // Enable submit button only if email is valid and terms accepted
                let valid_email = self.email_field.borrow().text().contains('@');
                self.submit_button.borrow_mut()
                    .set_enabled(valid_email && checked);
            }
            ("submit_button", Event::ButtonClicked(_)) => {
                // Perform submission logic
                let email = self.email_field.borrow().text();
                self.submit_form(email);
            }
            _ => {}
        }
    }
}

impl DialogMediator {
    fn submit_form(&self, email: String) {
        // Submission logic here
    }
}

struct Button {
    mediator: Rc<dyn Mediator>,
    enabled: bool,
}

impl Button {
    fn click(&self) {
        if self.enabled {
            self.mediator.notify("submit_button", Event::ButtonClicked(String::new()));
        }
    }
    
    fn set_enabled(&mut self, enabled: bool) {
        self.enabled = enabled;
    }
}

struct TextField {
    mediator: Rc<dyn Mediator>,
    text: String,
}

impl TextField {
    fn set_text(&mut self, text: String) {
        self.text = text.clone();
        self.mediator.notify("email_field", Event::TextChanged(text));
    }
    
    fn text(&self) -> String {
        self.text.clone()
    }
}

struct Checkbox {
    mediator: Rc<dyn Mediator>,
    checked: bool,
}

impl Checkbox {
    fn toggle(&mut self) {
        self.checked = !self.checked;
        self.mediator.notify("terms_checkbox", Event::CheckboxToggled(self.checked));
    }
    
    fn is_checked(&self) -> bool {
        self.checked
    }
}
```

The mediator centralizes coordination logic that would otherwise be distributed across multiple widgets. Without the mediator, the email field would need references to both the checkbox and submit button, the checkbox would need a reference to the button, and so on, creating a densely coupled mesh. The mediator reduces this coupling to a star topology where each widget connects only to the mediator.

```
Without Mediator (N*(N-1)/2 connections):
EmailField ←→ SubmitButton
     ↕            ↕
  Checkbox ←→ TermsLabel

With Mediator (N connections):
  EmailField → Mediator ← SubmitButton
                 ↕
              Checkbox
```

The tradeoff is that the mediator can become a bottleneck or a monolithic god object if not carefully designed. Effective mediators partition coordination logic into cohesive methods corresponding to specific interaction protocols rather than implementing a single massive `notify()` method. Domain events can be typed as enum variants (as shown) or as distinct classes in languages without algebraic data types, enabling exhaustive pattern matching and compile-time verification of event handling.

### Memento: State Snapshot and Restoration

Memento externalizes an object's internal state so it can be restored later without violating encapsulation. The pattern provides a way to capture snapshots at arbitrary points and roll back to them, enabling undo mechanisms, checkpointing, and transactional semantics. The key invariant is that the memento itself is opaque—only the originator can interpret its contents, preventing external code from depending on internal representation details.

The architecture involves three participants: the Originator (the object whose state is being captured), the Memento (an opaque token holding the state), and the Caretaker (which stores mementos without examining them). The originator creates mementos through a `save()` or `create_memento()` method and restores state through a `restore(memento)` method. The caretaker manages memento lifecycle—storing them in undo stacks, persistent storage, or network transmission—without understanding their structure.

```rust
// Originator: Complex editor state
struct Editor {
    content: String,
    cursor: usize,
    selection: Option<(usize, usize)>,
    syntax_mode: SyntaxMode,
}

// Memento: Opaque snapshot (private fields)
struct EditorMemento {
    content: String,
    cursor: usize,
    selection: Option<(usize, usize)>,
    syntax_mode: SyntaxMode,
}

impl Editor {
    fn create_memento(&self) -> EditorMemento {
        EditorMemento {
            content: self.content.clone(),
            cursor: self.cursor,
            selection: self.selection,
            syntax_mode: self.syntax_mode.clone(),
        }
    }
    
    fn restore_from_memento(&mut self, memento: EditorMemento) {
        self.content = memento.content;
        self.cursor = memento.cursor;
        self.selection = memento.selection;
        self.syntax_mode = memento.syntax_mode;
    }
    
    fn insert(&mut self, text: &str) {
        self.content.insert_str(self.cursor, text);
        self.cursor += text.len();
    }
    
    fn delete(&mut self, start: usize, end: usize) {
        self.content.drain(start..end);
        self.cursor = start;
    }
}

// Caretaker: Manages undo history
struct EditorHistory {
    snapshots: Vec<EditorMemento>,
    current_index: usize,
}

impl EditorHistory {
    fn new() -> Self {
        EditorHistory {
            snapshots: Vec::new(),
            current_index: 0,
        }
    }
    
    fn save(&mut self, editor: &Editor) {
        // Truncate redo history when new edit occurs
        self.snapshots.truncate(self.current_index);
        self.snapshots.push(editor.create_memento());
        self.current_index = self.snapshots.len();
    }
    
    fn undo(&mut self, editor: &mut Editor) -> bool {
        if self.current_index > 1 {
            self.current_index -= 1;
            editor.restore_from_memento(
                self.snapshots[self.current_index - 1].clone()
            );
            true
        } else {
            false
        }
    }
    
    fn redo(&mut self, editor: &mut Editor) -> bool {
        if self.current_index < self.snapshots.len() {
            editor.restore_from_memento(
                self.snapshots[self.current_index].clone()
            );
            self.current_index += 1;
            true
        } else {
            false
        }
    }
}
```

The memento's opacity is critical: the caretaker stores mementos in a vector and manipulates the current index without ever inspecting memento contents. In languages without access control, this encapsulation can be enforced through inner classes or friend relationships. In Rust, the memento's fields can be private while still allowing the originator module to access them.

Mementos can be optimized through copy-on-write semantics or delta compression. Rather than storing complete snapshots, each memento can store only the changes from the previous state. This reduces memory overhead but increases restoration time, as restoring requires replaying all deltas from the nearest full snapshot. Text editors often use a hybrid approach: full snapshots every N operations with deltas in between, balancing memory usage and restore performance.

```
Snapshot Strategy:
Time:    t0     t1     t2     t3     t4     t5     t6
State:  [Full] [Δ1]  [Δ2]  [Full] [Δ3]  [Δ4]  [Full]
                       ↑
                    Restore t2: Apply Δ1, Δ2 to t0 snapshot
```

Mementos can be serialized for persistence or network transmission, enabling cross-session undo, distributed checkpointing, or event sourcing architectures where the entire application state is reconstructed by replaying a memento sequence. The pattern decouples state persistence from the originator's internal structure, allowing storage format changes without affecting application logic.

### Observer: Decoupled Event Notification

Observer defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified and updated automatically. This pattern decouples the subject (the object being observed) from its observers, allowing observers to attach and detach dynamically without the subject knowing their concrete types. Observer is the foundation of event-driven architectures, reactive programming, and GUI frameworks.

The architecture consists of the Subject interface defining subscription methods (`attach()`, `detach()`, `notify()`), concrete Subject implementations maintaining an observer list, the Observer interface defining the update protocol, and concrete Observer implementations responding to notifications. The subject iterates through its observer list during `notify()`, calling each observer's `update()` method with relevant state information.

```rust
trait Observer {
    fn update(&mut self, event: &Event);
}

trait Subject {
    fn attach(&mut self, observer: Rc<RefCell<dyn Observer>>);
    fn detach(&mut self, observer: Rc<RefCell<dyn Observer>>);
    fn notify(&self, event: &Event);
}

struct StockTicker {
    observers: Vec<Rc<RefCell<dyn Observer>>>,
    symbol: String,
    price: f64,
}

impl StockTicker {
    fn set_price(&mut self, price: f64) {
        self.price = price;
        self.notify(&Event::PriceChanged {
            symbol: self.symbol.clone(),
            price,
        });
    }
}

impl Subject for StockTicker {
    fn attach(&mut self, observer: Rc<RefCell<dyn Observer>>) {
        self.observers.push(observer);
    }
    
    fn detach(&mut self, observer: Rc<RefCell<dyn Observer>>) {
        self.observers.retain(|o| !Rc::ptr_eq(o, &observer));
    }
    
    fn notify(&self, event: &Event) {
        for observer in &self.observers {
            observer.borrow_mut().update(event);
        }
    }
}

enum Event {
    PriceChanged { symbol: String, price: f64 },
    VolumeChanged { symbol: String, volume: u64 },
}

struct PortfolioDisplay {
    holdings: HashMap<String, f64>,
}

impl Observer for PortfolioDisplay {
    fn update(&mut self, event: &Event) {
        if let Event::PriceChanged { symbol, price } = event {
            if let Some(shares) = self.holdings.get(symbol) {
                let value = shares * price;
                println!("Portfolio value for {}: ${:.2}", symbol, value);
            }
        }
    }
}

struct AlertSystem {
    thresholds: HashMap<String, f64>,
}

impl Observer for AlertSystem {
    fn update(&mut self, event: &Event) {
        if let Event::PriceChanged { symbol, price } = event {
            if let Some(&threshold) = self.thresholds.get(symbol) {
                if *price > threshold {
                    println!("ALERT: {} exceeded threshold ${:.2}", symbol, threshold);
                }
            }
        }
    }
}

struct LoggingObserver {
    log_file: File,
}

impl Observer for LoggingObserver {
    fn update(&mut self, event: &Event) {
        let timestamp = SystemTime::now();
        writeln!(self.log_file, "{:?}: {:?}", timestamp, event).unwrap();
    }
}
```

The observer list enables dynamic subscription—observers can attach and detach at any time without modifying the subject. This flexibility is critical in GUI systems where UI components subscribe to model changes during creation and unsubscribe during destruction, or in reactive systems where data flows are constructed and torn down dynamically.

Observer can be implemented in push or pull styles. In push style (shown above), the subject sends detailed event information to observers. In pull style, the subject only notifies observers of a change, and observers query the subject for specific information they need. Push style reduces coupling at the cost of sending data observers might not need. Pull style minimizes data transfer but requires observers to know the subject's query interface.

```
Push Style:
Subject: notify(Event { symbol: "AAPL", price: 150.0 })
Observer: receives complete event data

Pull Style:
Subject: notify()
Observer: subject.get_price("AAPL")
```

The notification protocol must handle observer removal during notification. If an observer detaches itself in response to an event, the subject's iteration can invalidate, causing use-after-free or skipped notifications. Defensive implementations clone the observer list before iterating or use generation counters to detect modifications. Weak references prevent circular dependencies where subjects and observers reference each other, avoiding memory leaks in garbage-collected languages.

Observer composes with other patterns: Command can encapsulate observer subscriptions for undo/redo, Mediator can implement observer protocols for complex coordination, and Strategy can vary the notification algorithm (immediate vs batched vs throttled). The pattern scales to distributed systems through message queues and pub-sub buses where subjects publish to topics and observers subscribe to channels.

### State: Explicit Finite State Machines

State allows an object to alter its behavior when its internal state changes, making the object appear to change its class. Rather than scattering conditionals throughout methods that check state flags, State reifies each state as an explicit class with its own behavior. The context delegates behavior to the current state object, which responds to method calls and transitions the context to new states.

The architecture consists of the State interface defining methods corresponding to state-dependent behaviors, concrete State implementations encoding behavior for specific states, and the Context that holds a reference to the current state. When the context receives a request, it delegates to the current state object. State transitions occur when a state object changes the context's state reference to point to a different state object.

```rust
trait ConnectionState {
    fn open(&self, ctx: &mut Connection) -> Result<(), Error>;
    fn close(&self, ctx: &mut Connection) -> Result<(), Error>;
    fn send(&self, ctx: &mut Connection, data: &[u8]) -> Result<(), Error>;
    fn receive(&self, ctx: &mut Connection) -> Result<Vec<u8>, Error>;
}

struct Connection {
    state: Box<dyn ConnectionState>,
    socket: Option<TcpStream>,
}

impl Connection {
    fn new() -> Self {
        Connection {
            state: Box::new(ClosedState),
            socket: None,
        }
    }
    
    fn set_state(&mut self, state: Box<dyn ConnectionState>) {
        self.state = state;
    }
    
    pub fn open(&mut self) -> Result<(), Error> {
        self.state.open(self)
    }
    
    pub fn close(&mut self) -> Result<(), Error> {
        self.state.close(self)
    }
    
    pub fn send(&mut self, data: &[u8]) -> Result<(), Error> {
        self.state.send(self, data)
    }
    
    pub fn receive(&mut self) -> Result<Vec<u8>, Error> {
        self.state.receive(self)
    }
}

struct ClosedState;

impl ConnectionState for ClosedState {
    fn open(&self, ctx: &mut Connection) -> Result<(), Error> {
        let socket = TcpStream::connect("127.0.0.1:8080")?;
        ctx.socket = Some(socket);
        ctx.set_state(Box::new(OpenState));
        Ok(())
    }
    
    fn close(&self, _ctx: &mut Connection) -> Result<(), Error> {
        Err(Error::AlreadyClosed)
    }
    
    fn send(&self, _ctx: &mut Connection, _data: &[u8]) -> Result<(), Error> {
        Err(Error::NotConnected)
    }
    
    fn receive(&self, _ctx: &mut Connection) -> Result<Vec<u8>, Error> {
        Err(Error::NotConnected)
    }
}

struct OpenState;

impl ConnectionState for OpenState {
    fn open(&self, _ctx: &mut Connection) -> Result<(), Error> {
        Err(Error::AlreadyOpen)
    }
    
    fn close(&self, ctx: &mut Connection) -> Result<(), Error> {
        if let Some(socket) = ctx.socket.take() {
            drop(socket); // Close socket
        }
        ctx.set_state(Box::new(ClosedState));
        Ok(())
    }
    
    fn send(&self, ctx: &mut Connection, data: &[u8]) -> Result<(), Error> {
        if let Some(ref mut socket) = ctx.socket {
            socket.write_all(data)?;
            Ok(())
        } else {
            Err(Error::SocketLost)
        }
    }
    
    fn receive(&self, ctx: &mut Connection) -> Result<Vec<u8>, Error> {
        if let Some(ref mut socket) = ctx.socket {
            let mut buffer = vec![0u8; 1024];
            let n = socket.read(&mut buffer)?;
            buffer.truncate(n);
            Ok(buffer)
        } else {
            Err(Error::SocketLost)
        }
    }
}
```

The State pattern transforms the state machine from implicit (conditional logic) to explicit (class hierarchy), making states visible in the type system. State transitions become object reassignments rather than flag modifications, and invariants can be enforced at state class boundaries. For example, the `ClosedState` implementation makes it impossible to send data because the socket field is inaccessible—the compiler enforces the invariant that closed connections cannot transmit.

```
State Transition Diagram:
┌─────────┐  open()   ┌──────────┐
│ Closed  │ ────────→ │   Open   │
│         │ ←──────── │          │
└─────────┘  close()  └──────────┘
     ↑                      │
     │  send()/receive()    │ send()/receive()
     └──── Error ───────    └────── Success
```

State objects can maintain their own internal state beyond the context's fields. A `ListeningState` in a server connection might track pending accept requests, while a `TransmittingState` might maintain a send buffer. This localized state prevents the context from becoming a dumping ground for state-specific data.

State composes with Strategy when state transitions depend on configurable policies. For example, a connection might transition to different retry states based on a reconnection strategy. State also composes with Memento to enable snapshotting and restoring the entire state machine, useful for debugging or distributed checkpointing.

The pattern introduces overhead through dynamic dispatch and heap allocation for state objects. High-frequency state machines can optimize by using enum-based state representations with match expressions, sacrificing extensibility for performance. This tradeoff mirrors the tension between polymorphism and inline code throughout object-oriented design.

### Strategy: Pluggable Algorithms

Strategy defines a family of algorithms, encapsulates each one, and makes them interchangeable. Strategy lets the algorithm vary independently from clients that use it. This pattern extracts algorithmic logic into separate classes implementing a common interface, allowing runtime selection and substitution without conditional logic in the client code.

The architecture consists of the Strategy interface declaring the algorithm's contract, concrete Strategy implementations providing different algorithm variants, and the Context that uses a strategy through the interface. The context is parameterized with a strategy object, typically through constructor injection or setter methods, and delegates algorithm execution to the strategy without knowing which concrete implementation is active.

```rust
trait CompressionStrategy {
    fn compress(&self, data: &[u8]) -> Vec<u8>;
    fn decompress(&self, data: &[u8]) -> Vec<u8>;
    fn name(&self) -> &str;
}

struct GzipCompression;

impl CompressionStrategy for GzipCompression {
    fn compress(&self, data: &[u8]) -> Vec<u8> {
        let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(data).unwrap();
        encoder.finish().unwrap()
    }
    
    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        let mut decoder = GzDecoder::new(data);
        let mut result = Vec::new();
        decoder.read_to_end(&mut result).unwrap();
        result
    }
    
    fn name(&self) -> &str {
        "gzip"
    }
}

struct Lz4Compression;

impl CompressionStrategy for Lz4Compression {
    fn compress(&self, data: &[u8]) -> Vec<u8> {
        lz4::compress(data)
    }
    
    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        lz4::decompress(data).unwrap()
    }
    
    fn name(&self) -> &str {
        "lz4"
    }
}

struct NoCompression;

impl CompressionStrategy for NoCompression {
    fn compress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }
    
    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        data.to_vec()
    }
    
    fn name(&self) -> &str {
        "none"
    }
}

struct FileArchiver {
    strategy: Box<dyn CompressionStrategy>,
}

impl FileArchiver {
    fn new(strategy: Box<dyn CompressionStrategy>) -> Self {
        FileArchiver { strategy }
    }
    
    fn set_compression(&mut self, strategy: Box<dyn CompressionStrategy>) {
        self.strategy = strategy;
    }
    
    fn archive_file(&self, path: &Path) -> Result<Vec<u8>, Error> {
        let data = std::fs::read(path)?;
        let compressed = self.strategy.compress(&data);
        
        // Prepend metadata header
        let mut archive = Vec::new();
        archive.extend_from_slice(self.strategy.name().as_bytes());
        archive.push(0); // Null terminator
        archive.extend_from_slice(&compressed);
        
        Ok(archive)
    }
    
    fn extract_file(&self, archive: &[u8]) -> Result<Vec<u8>, Error> {
        // Parse metadata header
        let name_end = archive.iter().position(|&b| b == 0).unwrap();
        let compressed = &archive[name_end + 1..];
        
        Ok(self.strategy.decompress(compressed))
    }
}

// Strategy selection based on configuration
fn create_archiver(config: &Config) -> FileArchiver {
    let strategy: Box<dyn CompressionStrategy> = match config.compression {
        "gzip" => Box::new(GzipCompression),
        "lz4" => Box::new(Lz4Compression),
        "none" => Box::new(NoCompression),
        _ => Box::new(GzipCompression), // Default
    };
    
    FileArchiver::new(strategy)
}
```

The strategy pattern enables runtime algorithm selection based on context. An HTTP client might choose compression strategies based on payload size: no compression for small payloads to avoid overhead, gzip for moderate payloads balancing compression ratio and speed, and brotli for large payloads prioritizing maximum compression. This policy decision lives in application configuration rather than being hardcoded.

Strategy also facilitates A/B testing and gradual rollouts. A recommendation system can deploy multiple ranking algorithms as strategies and allocate traffic percentages to each, measuring performance metrics and gradually shifting traffic to better-performing strategies. The strategy interface provides the seam for experimentation without modifying the calling code.

```rust
// Adaptive strategy selection
struct AdaptiveCompression {
    fast: Box<dyn CompressionStrategy>,
    optimal: Box<dyn CompressionStrategy>,
    size_threshold: usize,
}

impl CompressionStrategy for AdaptiveCompression {
    fn compress(&self, data: &[u8]) -> Vec<u8> {
        if data.len() < self.size_threshold {
            self.fast.compress(data)
        } else {
            self.optimal.compress(data)
        }
    }
    
    fn decompress(&self, data: &[u8]) -> Vec<u8> {
        // Metadata must encode which strategy was used
        // Implementation details omitted for brevity
        unimplemented!()
    }
    
    fn name(&self) -> &str {
        "adaptive"
    }
}
```

Strategy composes with Factory patterns to encapsulate strategy selection logic, with Decorator to layer multiple algorithmic behaviors, and with State when algorithmic choice depends on object state. The pattern trades a proliferation of strategy classes for elimination of conditional logic, a tradeoff that favors maintainability and testability in most contexts.

### Template Method: Algorithmic Skeleton with Customization Points

Template Method defines the skeleton of an algorithm in a base class, deferring specific steps to subclasses. Subclasses override particular steps without changing the algorithm's overall structure. This pattern inverts control: the framework calls into application code at well-defined extension points rather than application code calling framework APIs.

The architecture consists of an abstract base class declaring a template method that defines the algorithmic structure, concrete methods implementing invariant steps, and abstract or hook methods that subclasses override to customize behavior. The template method calls both types of methods in a fixed sequence, enforcing the algorithmic protocol while allowing step-level variation.

```rust
trait DataProcessor {
    // Template method - defines algorithm structure
    fn process(&mut self, input: &Path, output: &Path) -> Result<(), Error> {
        let data = self.read_data(input)?;
        let parsed = self.parse_data(&data)?;
        let transformed = self.transform_data(parsed)?;
        let serialized = self.serialize_data(&transformed)?;
        self.write_data(output, &serialized)?;
        Ok(())
    }
    
    // Concrete method - common implementation
    fn read_data(&self, path: &Path) -> Result<Vec<u8>, Error> {
        std::fs::read(path).map_err(Error::IoError)
    }
    
    // Concrete method - common implementation
    fn write_data(&self, path: &Path, data: &[u8]) -> Result<(), Error> {
        std::fs::write(path, data).map_err(Error::IoError)
    }
    
    // Abstract methods - subclasses must implement
    fn parse_data(&self, data: &[u8]) -> Result<Self::DataType, Error>;
    fn transform_data(&self, data: Self::DataType) -> Result<Self::DataType, Error>;
    fn serialize_data(&self, data: &Self::DataType) -> Result<Vec<u8>, Error>;
    
    // Hook method - subclasses may override
    fn validate_input(&self, _data: &Self::DataType) -> Result<(), Error> {
        Ok(()) // Default: no validation
    }
    
    type DataType;
}

// Concrete implementation for CSV processing
struct CsvProcessor {
    delimiter: char,
    header_row: bool,
}

impl DataProcessor for CsvProcessor {
    type DataType = Vec<Vec<String>>;
    
    fn parse_data(&self, data: &[u8]) -> Result<Self::DataType, Error> {
        let text = String::from_utf8_lossy(data);
        let mut rows = Vec::new();
        
        for (idx, line) in text.lines().enumerate() {
            if idx == 0 && self.header_row {
                continue; // Skip header
            }
            let fields: Vec<String> = line
                .split(self.delimiter)
                .map(|s| s.trim().to_string())
                .collect();
            rows.push(fields);
        }
        
        Ok(rows)
    }
    
    fn transform_data(&self, mut data: Self::DataType) -> Result<Self::DataType, Error> {
        // Example: Remove empty rows
        data.retain(|row| !row.is_empty() && row.iter().any(|s| !s.is_empty()));
        Ok(data)
    }
    
    fn serialize_data(&self, data: &Self::DataType) -> Result<Vec<u8>, Error> {
        let mut output = String::new();
        for row in data {
            output.push_str(&row.join(&self.delimiter.to_string()));
            output.push('\n');
        }
        Ok(output.into_bytes())
    }
}

// Concrete implementation for JSON processing
struct JsonProcessor;

impl DataProcessor for JsonProcessor {
    type DataType = serde_json::Value;
    
    fn parse_data(&self, data: &[u8]) -> Result<Self::DataType, Error> {
        serde_json::from_slice(data).map_err(Error::JsonError)
    }
    
    fn transform_data(&self, data: Self::DataType) -> Result<Self::DataType, Error> {
        // Example: Remove null values
        if let serde_json::Value::Object(mut map) = data {
            map.retain(|_, v| !v.is_null());
            Ok(serde_json::Value::Object(map))
        } else {
            Ok(data)
        }
    }
    
    fn serialize_data(&self, data: &Self::DataType) -> Result<Vec<u8>, Error> {
        serde_json::to_vec_pretty(data).map_err(Error::JsonError)
    }
    
    fn validate_input(&self, data: &Self::DataType) -> Result<(), Error> {
        if !data.is_object() && !data.is_array() {
            return Err(Error::InvalidFormat);
        }
        Ok(())
    }
}
```

The template method enforces the processing pipeline: read → parse → transform → serialize → write. Subclasses cannot reorder these steps or skip the parsing phase, guaranteeing invariants that depend on the sequence. This constraint prevents bugs where a developer forgets to validate input or omits cleanup steps.

Hook methods provide optional customization points with default no-op implementations. The `validate_input()` hook allows subclasses to inject validation logic without overriding the entire template method. This pattern appears in GUI frameworks where `onInit()`, `onDestroy()`, and lifecycle hooks allow application code to participate in framework-managed sequences.

```
Processing Pipeline:
read_data() ────→ [Raw Bytes]
                       ↓
parse_data() ───→ [Structured Data] ← subclass implements
                       ↓
validate_input() → [Validated] ← hook (optional)
                       ↓
transform_data() → [Transformed] ← subclass implements
                       ↓
serialize_data() → [Serialized] ← subclass implements
                       ↓
write_data() ────→ [Output File]
```

Template Method composes with Strategy when algorithmic steps themselves vary independently. Rather than a single strategy object, each customization point can accept its own strategy. Template Method also composes with Factory Method when the template method needs to instantiate objects of subclass-specific types, delegating object creation to factory methods that subclasses override.

The pattern's primary weakness is that it couples subclasses to the base class's algorithmic structure. Changing the template method's sequence requires modifying all subclasses if new abstract methods are introduced. Favor composition over inheritance when algorithmic flexibility is paramount, but use Template Method when the sequence itself is a critical invariant that must be preserved across variants.

### Visitor: Double Dispatch for Heterogeneous Operations

Visitor separates an algorithm from the object structure on which it operates, enabling new operations to be added without modifying the classes of the elements being visited. The pattern implements double dispatch: the operation executed depends on both the visitor type and the element type. This solves the expression problem—adding new operations to a closed set of types—without modifying existing code.

The architecture consists of the Visitor interface declaring a visit method for each element type, concrete Visitor implementations defining operations, the Element interface declaring an `accept(visitor)` method, and concrete Element implementations that call the appropriate visitor method. The double dispatch occurs in two steps: first, the client calls `element.accept(visitor)`, then the element calls `visitor.visit_concrete_element(self)`, selecting the correct overload based on its concrete type.

```rust
// Element hierarchy: Abstract syntax tree nodes
trait AstNode {
    fn accept(&self, visitor: &mut dyn AstVisitor);
}

struct NumberLiteral {
    value: f64,
}

impl AstNode for NumberLiteral {
    fn accept(&self, visitor: &mut dyn AstVisitor) {
        visitor.visit_number(self);
    }
}

struct BinaryOperation {
    left: Box<dyn AstNode>,
    operator: Operator,
    right: Box<dyn AstNode>,
}

impl AstNode for BinaryOperation {
    fn accept(&self, visitor: &mut dyn AstVisitor) {
        visitor.visit_binary_op(self);
    }
}

struct VariableReference {
    name: String,
}

impl AstNode for VariableReference {
    fn accept(&self, visitor: &mut dyn AstVisitor) {
        visitor.visit_variable(self);
    }
}

enum Operator {
    Add, Subtract, Multiply, Divide,
}

// Visitor interface
trait AstVisitor {
    fn visit_number(&mut self, node: &NumberLiteral);
    fn visit_binary_op(&mut self, node: &BinaryOperation);
    fn visit_variable(&mut self, node: &VariableReference);
}

// Concrete visitor: Expression evaluator
struct Evaluator {
    variables: HashMap<String, f64>,
    result: f64,
}

impl AstVisitor for Evaluator {
    fn visit_number(&mut self, node: &NumberLiteral) {
        self.result = node.value;
    }
    
    fn visit_binary_op(&mut self, node: &BinaryOperation) {
        node.left.accept(self);
        let left = self.result;
        
        node.right.accept(self);
        let right = self.result;
        
        self.result = match node.operator {
            Operator::Add => left + right,
            Operator::Subtract => left - right,
            Operator::Multiply => left * right,
            Operator::Divide => left / right,
        };
    }
    
    fn visit_variable(&mut self, node: &VariableReference) {
        self.result = *self.variables.get(&node.name).unwrap_or(&0.0);
    }
}

// Concrete visitor: Code generator
struct CodeGenerator {
    output: String,
}

impl AstVisitor for CodeGenerator {
    fn visit_number(&mut self, node: &NumberLiteral) {
        self.output.push_str(&format!("{}", node.value));
    }
    
    fn visit_binary_op(&mut self, node: &BinaryOperation) {
        self.output.push('(');
        node.left.accept(self);
        
        let op_str = match node.operator {
            Operator::Add => " + ",
            Operator::Subtract => " - ",
            Operator::Multiply => " * ",
            Operator::Divide => " / ",
        };
        self.output.push_str(op_str);
        
        node.right.accept(self);
        self.output.push(')');
    }
    
    fn visit_variable(&mut self, node: &VariableReference) {
        self.output.push_str(&node.name);
    }
}

// Concrete visitor: Type checker
struct TypeChecker {
    variables: HashMap<String, Type>,
    current_type: Option<Type>,
}

#[derive(Clone, PartialEq)]
enum Type {
    Number,
    Boolean,
    Unknown,
}

impl AstVisitor for TypeChecker {
    fn visit_number(&mut self, _node: &NumberLiteral) {
        self.current_type = Some(Type::Number);
    }
    
    fn visit_binary_op(&mut self, node: &BinaryOperation) {
        node.left.accept(self);
        let left_type = self.current_type.clone();
        
        node.right.accept(self);
        let right_type = self.current_type.clone();
        
        if left_type == right_type && left_type == Some(Type::Number) {
            self.current_type = Some(Type::Number);
        } else {
            self.current_type = Some(Type::Unknown);
        }
    }
    
    fn visit_variable(&mut self, node: &VariableReference) {
        self.current_type = self.variables.get(&node.name).cloned();
    }
}
```

The Visitor pattern allows adding new operations (evaluation, code generation, type checking) without modifying the AST node classes. Each visitor implements a complete traversal strategy, encapsulating the algorithm separately from the data structure. This separation is critical in compilers where the AST structure stabilizes early but new optimization passes and analyses are added continuously.

The double dispatch mechanism resolves method selection at runtime based on two types. Without Visitor, implementing evaluation would require adding an `evaluate()` method to each node class. Adding code generation would require adding `generate()`, and so on, polluting node classes with unrelated concerns. Visitor inverts this: node classes remain focused on structure, while visitors focus on operations.

```
Method Dispatch Flow:
Client: root.accept(&mut evaluator)
           ↓
BinaryOp::accept(visitor): visitor.visit_binary_op(self)
                                      ↓
Evaluator::visit_binary_op(node):
    node.left.accept(self)  → recurse left subtree
    node.right.accept(self) → recurse right subtree
    compute result
```

Visitor's weakness is that adding new element types breaks all existing visitors—each visitor must implement a visit method for every element type. This makes Visitor suitable when the element hierarchy is stable but operations evolve, the opposite of when Strategy is appropriate. In languages with pattern matching (Rust, ML, Haskell), algebraic data types with match expressions provide similar benefits with less boilerplate.

Visitor composes with Composite when traversing tree structures, with Iterator when traversing linear collections, and with Interpreter when implementing domain-specific languages. The pattern appears in compilers (optimization passes), graphics systems (scene graph traversal), and document processing (element export to various formats).

## 3. High-Performance Optimization & Failure Modes

Behavioral patterns introduce indirection and dynamic dispatch, which can impact performance in tight loops or latency-sensitive code paths. Understanding the overhead of each pattern and applying targeted optimizations is critical for systems programming where microsecond latencies and cache efficiency matter.

The Observer pattern's primary performance concern is notification overhead. When a subject notifies observers, it iterates through the observer list and calls each observer's update method through a virtual dispatch. For N observers, this incurs N virtual calls plus the overhead of each observer's processing. In GUI systems where model changes trigger hundreds of UI updates, this overhead compounds. Optimizations include batching notifications—accumulating multiple state changes and notifying once—and dirty flags where observers mark themselves for update but defer processing until explicitly flushed. Reactive frameworks like RxJava implement backpressure mechanisms to prevent observer queues from overwhelming consumers.

```rust
// Optimized observer with batching
struct BatchingSubject {
    observers: Vec<Rc<RefCell<dyn Observer>>>,
    pending_events: Vec<Event>,
    batch_size: usize,
}

impl BatchingSubject {
    fn notify_event(&mut self, event: Event) {
        self.pending_events.push(event);
        if self.pending_events.len() >= self.batch_size {
            self.flush();
        }
    }
    
    fn flush(&mut self) {
        if self.pending_events.is_empty() {
            return;
        }
        
        let events = std::mem::take(&mut self.pending_events);
        for observer in &self.observers {
            for event in &events {
                observer.borrow_mut().update(event);
            }
        }
    }
}
```

Observer list iteration during notification creates a synchronization bottleneck in concurrent systems. If observers modify the subject's state or attach/detach during notification, data races occur. Lock-based solutions serialize all notifications, destroying concurrency. Lock-free implementations use atomic operations and hazard pointers to allow concurrent iteration and modification, but at the cost of complexity. An alternative is message-passing architectures where subjects publish events to lock-free queues that observers consume asynchronously, decoupling notification from processing.

The Chain of Responsibility pattern suffers from worst-case linear time complexity when requests traverse the entire chain without finding a handler. For authorization chains with dozens of rules, this becomes a bottleneck. Optimizations include caching handler selection results keyed by request attributes, reordering handlers to place frequently matching rules early, and implementing hybrid dispatch where a hash table maps request types to handler chains, avoiding iteration through irrelevant handlers.

```rust
// Cached chain of responsibility
struct CachedHandlerChain {
    handlers: Vec<Box<dyn Handler>>,
    cache: RwLock<HashMap<RequestKey, usize>>,
}

impl CachedHandlerChain {
    fn handle(&self, request: &Request) -> Option<Response> {
        let key = request.cache_key();
        
        // Check cache
        if let Some(&index) = self.cache.read().unwrap().get(&key) {
            return self.handlers[index].handle(request);
        }
        
        // Find handler
        for (idx, handler) in self.handlers.iter().enumerate() {
            if let Some(response) = handler.handle(request) {
                // Cache successful handler
                self.cache.write().unwrap().insert(key, idx);
                return Some(response);
            }
        }
        None
    }
}
```

Command pattern overhead comes from heap allocation and virtual dispatch for each command object. In undo systems processing thousands of edits per second, allocation overhead dominates. Object pooling reuses command objects: after undo/redo, commands return to a pool rather than being deallocated. For performance-critical commands, inline storage in a fixed-size array avoids heap allocation entirely, though this limits command history depth. Command compression merges consecutive similar commands—ten single-character insertions become one ten-character insertion—reducing memory and improving undo responsiveness.

The Iterator pattern's abstraction can prevent compiler optimizations. Virtual dispatch through trait objects disables inlining and prevents vectorization. In Rust, concrete iterator types enable zero-cost abstractions through monomorphization—the compiler generates specialized code for each iterator chain, eliminating virtual dispatch. Iterator chains should be constructed such that map, filter, and fold operations fuse into tight loops without intermediate allocations. Using `collect()` too early materializes intermediate results, destroying this optimization.

```rust
// Zero-cost iteration - compiles to tight loop
let sum: u32 = data.iter()
    .filter(|&&x| x % 2 == 0)    // Inline, no allocation
    .map(|&x| x * x)              // Inline, no allocation
    .sum();                       // Single pass

// Inefficient - materializes intermediates
let filtered: Vec<_> = data.iter().filter(|&&x| x % 2 == 0).collect();
let squared: Vec<_> = filtered.iter().map(|&x| x * x).collect();
let sum: u32 = squared.iter().sum();
```

State pattern virtual dispatch introduces overhead in state-intensive systems like network protocol handlers that transition states on every packet. For protocols with fewer than 16 states, an enum-based state machine with match expressions eliminates virtual dispatch and enables exhaustive case checking at compile time. The tradeoff is loss of extensibility—adding states requires modifying the enum—but for stable protocols, the performance gain justifies this constraint.

Visitor pattern performance degrades with deep recursion. Evaluating deeply nested expressions causes stack overflow and destroys instruction cache locality. Iterative traversal using an explicit stack avoids recursion overhead and allows visitor implementation to control memory allocation. For tree structures with millions of nodes, cache-oblivious layouts like van Emde Boas trees improve spatial locality, reducing cache misses during traversal.

Strategy pattern overhead is minimal—a single virtual dispatch per algorithm invocation—but strategy selection logic can become a bottleneck. Decision trees or lookup tables enable constant-time selection compared to linear chains of conditionals. For adaptive strategies that change based on runtime metrics, caching the selected strategy across multiple invocations amortizes selection overhead. Profile-guided optimization identifies hot paths where strategy selection should be inlined or specialized.

Mediator pattern centralization creates a bottleneck in high-concurrency systems. When all communication flows through a single mediator instance, contention on the mediator's lock destroys parallelism. Sharded mediators partition communication domains, allowing independent mediation of disjoint object groups. Event-driven mediators using message queues eliminate synchronous locking, though they introduce queueing latency. Careful domain decomposition ensures that objects within a shard interact frequently while cross-shard communication remains rare.

Memory overhead for behavioral patterns varies by implementation. Observer lists, command histories, and state object allocations accumulate memory over time. Weak references in observer lists prevent memory leaks when observers outlive subjects. Command history pruning limits undo depth, discarding old commands based on time or count thresholds. Memory pools preallocate fixed-size buffers for state objects, avoiding fragmentation and improving allocation performance. Profiling tools like Valgrind and heaptrack identify memory bloat caused by pattern overuse.

Testing behavioral patterns requires careful attention to temporal logic and state space exploration. Observer notification order affects correctness when observers have interdependencies. Tests should verify that notifications occur in deterministic order or that observers tolerate arbitrary ordering. Command undo/redo tests must verify idempotence—executing, undoing, and redoing a command sequence produces the same final state. State machine tests require coverage of all state transitions and validation that illegal transitions are rejected. Property-based testing generates random event sequences to uncover edge cases that manual testing misses.

Debugging behavioral patterns is challenging due to indirection and dynamic dispatch. Logging frameworks should instrument pattern entry/exit points: observer notification start/end, chain handler invocation, state transitions, and strategy selection. Trace logs reconstruct execution flow when debugging race conditions or unexpected behavior. Debugger conditional breakpoints trigger on specific observer types or state transitions, filtering noise in complex systems. Static analysis tools detect common pitfalls: observers that modify subject state during notification, command objects that don't properly implement undo, or state machines with unreachable states.

Failure modes specific to behavioral patterns include circular dependencies in Observer where subjects and observers reference each other, preventing garbage collection. Weak references or explicit cleanup during object destruction break these cycles. Chain of Responsibility failure occurs when no handler processes a request and the chain lacks a default handler—requests silently drop. A terminal handler that logs unprocessed requests provides visibility. State pattern failure happens when state transition logic is incomplete, leaving objects in invalid states. Exhaustive state enumeration and invariant checking in debug builds catch these errors early.

Behavioral patterns interact with concurrency models in subtle ways. Observer pattern requires careful synchronization: are notifications synchronous (blocking) or asynchronous (non-blocking)? Synchronous notifications preserve causality but risk deadlock if observers wait on the subject. Asynchronous notifications avoid blocking but complicate reasoning about state consistency—observers see stale state. Command pattern naturally supports undo/redo in concurrent systems through command queuing, but interleaving commands from multiple sources requires conflict resolution. Operational transformation or conflict-free replicated data types (CRDTs) resolve these conflicts deterministically. State pattern in concurrent systems must use atomic state transitions to prevent race conditions where multiple threads transition state simultaneously. Compare-and-swap operations ensure that only one transition succeeds, while losers retry.

Distributed systems extend behavioral patterns across network boundaries. Distributed Observer becomes publish-subscribe messaging with brokers mediating between publishers and subscribers. Topic partitioning and consumer groups enable parallel processing while maintaining ordering guarantees within partitions. Distributed Command uses event logs (Kafka, Kinesis) to store command sequences persistently, enabling replay for disaster recovery. Exactly-once semantics require idempotent command execution or deduplication mechanisms. Distributed State uses replicated state machines where each replica maintains a local state and applies commands deterministically to achieve consensus. Raft and Paxos protocols coordinate state transitions across replicas, ensuring that all replicas converge to the same state despite network partitions and failures.

Performance tuning requires profiling to identify bottlenecks. CPU profilers like perf and Intel VTune reveal hot methods—frequently called functions consuming significant CPU time. If observer notification dominates, consider batching or parallelization. Memory profilers identify excessive allocations—if command object allocation is hot, apply object pooling. Cache profilers like cachegrind reveal cache miss patterns—if visitor traversal has high miss rates, restructure data layout for better locality. Latency profilers measure end-to-end request processing—if chain traversal adds milliseconds, optimize handler ordering or cache results.

Architectural evolution sometimes requires replacing behavioral patterns with simpler mechanisms. When a system's flexibility is underutilized—Strategy with only one implementation, State with two states—eliminate the pattern and inline the logic. Conversely, when conditional logic proliferates, introduce patterns to restore structure. The decision hinges on whether the flexibility justifies the complexity. In domain-stable systems like embedded firmware, patterns may be overkill. In plugin architectures and frameworks where extensibility is paramount, patterns are essential. The art lies in recognizing when abstraction pays dividends and when it merely obscures intent.
