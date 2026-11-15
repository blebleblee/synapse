# Lesson 6: Concurrency Models, Synchronization Primitives, Parallel Execution

## 1. First-Principles Intuition & Invariants

Concurrency represents one of the most intellectually demanding domains in software engineering because it forces us to reason about multiple independent execution flows that share mutable state across a single address space or distributed system. The fundamental challenge emerges from the physical reality of modern computer architectures: even on single-core systems, the operating system scheduler interleaves thread execution at unpredictable intervals, and on multi-core processors, true parallel execution introduces race conditions at the nanosecond scale where memory coherence protocols and CPU caches become the primary sources of non-deterministic behavior.

The conceptual foundation of concurrency rests on distinguishing between two related but distinct concepts: concurrency and parallelism. Concurrency describes the composition of independently executing computational processes—threads, coroutines, or actors—that may or may not execute simultaneously. Parallelism, by contrast, represents the simultaneous execution of multiple computations, typically to improve throughput or reduce latency. A single-core system can support concurrent execution through time-slicing but cannot achieve true parallelism. Modern multi-core architectures provide both: concurrency through the abstraction of multiple execution contexts and parallelism through physical hardware resources that execute instructions simultaneously.

At the hardware level, every modern processor implements a memory consistency model that defines the ordering guarantees for memory operations across different cores. The x86-64 architecture provides a relatively strong memory model called Total Store Ordering (TSO), which ensures that all writes from a single processor appear in program order to all other processors, though reads may bypass earlier writes in the store buffer. ARM and RISC-V implement weaker models that allow more aggressive reordering for performance, requiring explicit memory barrier instructions to enforce ordering constraints. These hardware realities manifest in software through the memory models defined by programming languages: C11, C++11, and Rust all expose atomic operations with explicit ordering semantics—relaxed, acquire, release, acquire-release, and sequentially consistent—that map directly to the underlying processor's memory fence instructions.

The first invariant of concurrent programming states that any mutable state shared between execution contexts without proper synchronization will exhibit data races, where the final program state depends on the non-deterministic interleaving of memory operations. A data race occurs when two threads access the same memory location, at least one access is a write, and the accesses are not ordered by synchronization. Data races produce undefined behavior in C and C++, and in Rust, the type system and borrow checker are explicitly designed to prevent data races at compile time through the `Send` and `Sync` marker traits that enforce single-ownership and synchronized-access invariants respectively.

The second invariant concerns the relationship between synchronization and visibility. Synchronization primitives like mutexes, semaphores, and condition variables serve two distinct purposes: mutual exclusion and memory visibility. Mutual exclusion ensures that only one thread executes within a critical section at any given time, preventing concurrent modification of shared state. Memory visibility, enforced through acquire-release semantics, guarantees that memory writes performed before releasing a lock become visible to any thread that subsequently acquires the same lock. Without these visibility guarantees, even properly locked code could observe stale values due to CPU cache hierarchies and speculative execution.

The third invariant addresses the composability of concurrent operations. Unlike sequential code where function composition naturally preserves correctness, concurrent operations do not compose unless explicitly designed with composability in mind. Taking two thread-safe functions and invoking them sequentially does not guarantee thread safety at the composition level because another thread may interleave between the two calls and observe or modify intermediate state. This fundamental limitation leads to the design principle that critical sections should be atomic with respect to invariants: a thread must acquire all necessary locks, perform its state transition, and release locks such that observers never witness an inconsistent intermediate state.

Deadlock represents a catastrophic failure mode where two or more threads wait indefinitely for resources held by each other, forming a circular dependency that prevents forward progress. The classical formulation identifies four necessary conditions for deadlock: mutual exclusion (resources cannot be shared), hold and wait (threads hold resources while waiting for others), no preemption (resources cannot be forcibly taken), and circular wait (a circular chain of threads each waiting for a resource held by the next). Preventing deadlock requires breaking at least one of these conditions, typically through lock ordering protocols that establish a global total order on lock acquisitions, or through timeout-based acquisition with rollback and retry.

Livelock, a less obvious failure mode, occurs when threads continuously change state in response to each other without making progress toward completion. Unlike deadlock where threads are blocked, livelocked threads remain active but trapped in a state-transition loop. Priority inversion represents another subtle pathology where a high-priority thread waits for a resource held by a low-priority thread, which itself is preempted by medium-priority threads, effectively inverting the scheduling priorities. Operating systems mitigate priority inversion through priority inheritance protocols where a low-priority thread temporarily inherits the priority of any high-priority thread waiting on its resources.

The actor model and message-passing concurrency offer an alternative paradigm that eliminates shared mutable state entirely. In the actor model, each actor maintains private state and communicates with other actors exclusively through asynchronous message passing. This design prevents data races by construction because no memory is shared, and eliminates the need for locks because each actor processes messages sequentially. The Erlang virtual machine and the Akka framework implement actor-based concurrency with lightweight processes that are scheduled cooperatively and communicate through immutable message passing with pattern matching.

Asynchronous programming with async/await syntax represents a form of cooperative concurrency where execution contexts voluntarily yield control at explicit await points rather than being preemptively scheduled by the operating system. This model maps naturally to I/O-bound workloads where threads spend most of their time waiting for network packets, disk reads, or timer expiration. Under the hood, async runtimes like Tokio in Rust or asyncio in Python maintain an event loop that polls file descriptors for readiness, schedules ready tasks, and yields to the operating system when no work is available. The primary advantage of async/await over thread-per-request models lies in memory efficiency: a thread requires a megabyte or more for its stack, while an async task requires only the memory needed to store its state machine between await points, typically measured in kilobytes.

## 2. Core Architecture & Mechanics

The fundamental building block of concurrent execution on Unix-like systems is the thread, represented in Linux by a `task_struct` that shares the same memory space as its parent process but maintains its own stack, registers, and scheduling state. Creating a thread through the POSIX `pthread_create` API results in a clone system call with the `CLONE_VM`, `CLONE_FS`, `CLONE_FILES`, and `CLONE_SIGHAND` flags set, instructing the kernel to share the virtual memory descriptor, filesystem information, file descriptor table, and signal handlers between the parent and child tasks.

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>

// Shared counter with atomic operations demonstrating sequentially consistent ordering
atomic_int global_counter = ATOMIC_VAR_INIT(0);

// Mutex protecting a non-atomic critical section
pthread_mutex_t section_mutex = PTHREAD_MUTEX_INITIALIZER;
int protected_value = 0;

void* worker_thread(void* arg) {
    int thread_id = *(int*)arg;
    free(arg);
    
    // Atomic increment with sequential consistency
    for (int i = 0; i < 100000; i++) {
        atomic_fetch_add_explicit(&global_counter, 1, memory_order_seq_cst);
    }
    
    // Mutex-protected critical section
    pthread_mutex_lock(&section_mutex);
    protected_value += thread_id;
    printf("Thread %d: protected_value = %d\n", thread_id, protected_value);
    pthread_mutex_unlock(&section_mutex);
    
    return NULL;
}

int main(void) {
    pthread_t threads[4];
    
    for (int i = 0; i < 4; i++) {
        int* thread_id = malloc(sizeof(int));
        *thread_id = i;
        pthread_create(&threads[i], NULL, worker_thread, thread_id);
    }
    
    for (int i = 0; i < 4; i++) {
        pthread_join(threads[i], NULL);
    }
    
    printf("Final counter: %d (expected 400000)\n", atomic_load(&global_counter));
    printf("Final protected value: %d\n", protected_value);
    
    pthread_mutex_destroy(&section_mutex);
    return 0;
}
```

The mutex implementation above relies on the kernel's futex (fast userspace mutex) mechanism on Linux. When a thread attempts to lock an uncontended mutex, it performs an atomic compare-and-swap operation in userspace without kernel involvement. If the mutex is already locked, the thread issues a futex system call to block on a kernel wait queue associated with the mutex's memory address. When the owning thread releases the mutex, it performs another futex wake operation to notify one waiting thread. This two-level design amortizes the cost of system calls across the common case of uncontended locks while providing kernel-mediated blocking for contention.

Condition variables extend mutexes to support complex synchronization patterns where threads must wait for a predicate to become true. The canonical use case involves a producer-consumer queue where consumers must wait when the queue is empty and producers must signal when they enqueue items.

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>

#define QUEUE_SIZE 10

typedef struct {
    int items[QUEUE_SIZE];
    int head;
    int tail;
    int count;
    pthread_mutex_t mutex;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
    bool shutdown;
} BoundedQueue;

void queue_init(BoundedQueue* q) {
    q->head = 0;
    q->tail = 0;
    q->count = 0;
    q->shutdown = false;
    pthread_mutex_init(&q->mutex, NULL);
    pthread_cond_init(&q->not_empty, NULL);
    pthread_cond_init(&q->not_full, NULL);
}

void queue_destroy(BoundedQueue* q) {
    pthread_mutex_destroy(&q->mutex);
    pthread_cond_destroy(&q->not_empty);
    pthread_cond_destroy(&q->not_full);
}

void queue_enqueue(BoundedQueue* q, int value) {
    pthread_mutex_lock(&q->mutex);
    
    // Wait while queue is full (spurious wakeup handling via while loop)
    while (q->count == QUEUE_SIZE && !q->shutdown) {
        pthread_cond_wait(&q->not_full, &q->mutex);
    }
    
    if (q->shutdown) {
        pthread_mutex_unlock(&q->mutex);
        return;
    }
    
    q->items[q->tail] = value;
    q->tail = (q->tail + 1) % QUEUE_SIZE;
    q->count++;
    
    // Signal waiting consumers
    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->mutex);
}

bool queue_dequeue(BoundedQueue* q, int* value) {
    pthread_mutex_lock(&q->mutex);
    
    // Wait while queue is empty
    while (q->count == 0 && !q->shutdown) {
        pthread_cond_wait(&q->not_empty, &q->mutex);
    }
    
    if (q->shutdown && q->count == 0) {
        pthread_mutex_unlock(&q->mutex);
        return false;
    }
    
    *value = q->items[q->head];
    q->head = (q->head + 1) % QUEUE_SIZE;
    q->count--;
    
    // Signal waiting producers
    pthread_cond_signal(&q->not_full);
    pthread_mutex_unlock(&q->mutex);
    return true;
}

void queue_shutdown(BoundedQueue* q) {
    pthread_mutex_lock(&q->mutex);
    q->shutdown = true;
    pthread_cond_broadcast(&q->not_empty);
    pthread_cond_broadcast(&q->not_full);
    pthread_mutex_unlock(&q->mutex);
}

void* producer(void* arg) {
    BoundedQueue* q = (BoundedQueue*)arg;
    for (int i = 0; i < 50; i++) {
        queue_enqueue(q, i);
        printf("Produced: %d\n", i);
        usleep(10000); // 10ms
    }
    return NULL;
}

void* consumer(void* arg) {
    BoundedQueue* q = (BoundedQueue*)arg;
    int value;
    while (queue_dequeue(q, &value)) {
        printf("Consumed: %d\n", value);
        usleep(20000); // 20ms
    }
    return NULL;
}

int main(void) {
    BoundedQueue queue;
    queue_init(&queue);
    
    pthread_t prod_thread, cons_threads[2];
    
    pthread_create(&prod_thread, NULL, producer, &queue);
    for (int i = 0; i < 2; i++) {
        pthread_create(&cons_threads[i], NULL, consumer, &queue);
    }
    
    pthread_join(prod_thread, NULL);
    sleep(1); // Allow consumers to drain queue
    queue_shutdown(&queue);
    
    for (int i = 0; i < 2; i++) {
        pthread_join(cons_threads[i], NULL);
    }
    
    queue_destroy(&queue);
    return 0;
}
```

The condition variable implementation demonstrates several critical patterns. First, the wait predicate is checked in a while loop rather than an if statement to handle spurious wakeups, where `pthread_cond_wait` may return even though no thread called `pthread_cond_signal`. This behavior results from implementation details in the kernel's futex mechanism and signal delivery, and robust code must recheck predicates after waking. Second, `pthread_cond_wait` atomically releases the mutex and blocks the thread, then reacquires the mutex before returning. This atomicity prevents the race condition where a signal could be lost between releasing the mutex and blocking. Third, the shutdown mechanism uses `pthread_cond_broadcast` rather than `pthread_cond_signal` to wake all waiting threads simultaneously, ensuring that all producers and consumers receive the shutdown notification.

Read-write locks optimize the common case where data structures are read far more frequently than they are written. The `pthread_rwlock_t` type allows multiple readers to hold the lock simultaneously or a single writer to hold exclusive access. The implementation typically uses a combination of atomic operations for the fast path and a futex-based wait queue for contention.

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int* data;
    size_t size;
    pthread_rwlock_t lock;
} SharedArray;

void array_init(SharedArray* arr, size_t size) {
    arr->data = calloc(size, sizeof(int));
    arr->size = size;
    pthread_rwlock_init(&arr->lock, NULL);
}

void array_destroy(SharedArray* arr) {
    free(arr->data);
    pthread_rwlock_destroy(&arr->lock);
}

int array_read(SharedArray* arr, size_t index) {
    pthread_rwlock_rdlock(&arr->lock);
    int value = arr->data[index];
    pthread_rwlock_unlock(&arr->lock);
    return value;
}

void array_write(SharedArray* arr, size_t index, int value) {
    pthread_rwlock_wrlock(&arr->lock);
    arr->data[index] = value;
    pthread_rwlock_unlock(&arr->lock);
}

void* reader_thread(void* arg) {
    SharedArray* arr = (SharedArray*)arg;
    for (int i = 0; i < 1000000; i++) {
        int value = array_read(arr, i % arr->size);
        (void)value;
    }
    return NULL;
}

void* writer_thread(void* arg) {
    SharedArray* arr = (SharedArray*)arg;
    for (int i = 0; i < 10000; i++) {
        array_write(arr, i % arr->size, i);
    }
    return NULL;
}

int main(void) {
    SharedArray arr;
    array_init(&arr, 100);
    
    pthread_t readers[8], writers[2];
    
    for (int i = 0; i < 8; i++) {
        pthread_create(&readers[i], NULL, reader_thread, &arr);
    }
    for (int i = 0; i < 2; i++) {
        pthread_create(&writers[i], NULL, writer_thread, &arr);
    }
    
    for (int i = 0; i < 8; i++) {
        pthread_join(readers[i], NULL);
    }
    for (int i = 0; i < 2; i++) {
        pthread_join(writers[i], NULL);
    }
    
    array_destroy(&arr);
    return 0;
}
```

Modern Rust provides a compelling type-system approach to concurrency safety through its ownership model and marker traits. The `Send` trait indicates that a type can be safely transferred between threads, while `Sync` indicates that a type can be safely shared between threads through immutable references. Most primitive types are both `Send` and `Sync`, raw pointers are neither, and types like `Rc<T>` (reference-counted smart pointer) are neither because they use non-atomic reference counting. The `Arc<T>` type (atomic reference counting) is `Send + Sync` when `T` is `Send + Sync`, providing thread-safe shared ownership.

```rust
use std::sync::{Arc, Mutex, Condvar};
use std::thread;
use std::collections::VecDeque;

struct BoundedQueue<T> {
    queue: Mutex<VecDeque<T>>,
    not_empty: Condvar,
    not_full: Condvar,
    capacity: usize,
}

impl<T> BoundedQueue<T> {
    fn new(capacity: usize) -> Self {
        BoundedQueue {
            queue: Mutex::new(VecDeque::with_capacity(capacity)),
            not_empty: Condvar::new(),
            not_full: Condvar::new(),
            capacity,
        }
    }
    
    fn enqueue(&self, item: T) {
        let mut queue = self.queue.lock().unwrap();
        
        // Wait while queue is full
        while queue.len() >= self.capacity {
            queue = self.not_full.wait(queue).unwrap();
        }
        
        queue.push_back(item);
        self.not_empty.notify_one();
    }
    
    fn dequeue(&self) -> T {
        let mut queue = self.queue.lock().unwrap();
        
        // Wait while queue is empty
        while queue.is_empty() {
            queue = self.not_empty.wait(queue).unwrap();
        }
        
        let item = queue.pop_front().unwrap();
        self.not_full.notify_one();
        item
    }
}

fn main() {
    let queue = Arc::new(BoundedQueue::new(10));
    let mut handles = vec![];
    
    // Spawn producer threads
    for i in 0..2 {
        let q = Arc::clone(&queue);
        let handle = thread::spawn(move || {
            for j in 0..50 {
                q.enqueue(i * 50 + j);
                println!("Producer {} enqueued {}", i, i * 50 + j);
            }
        });
        handles.push(handle);
    }
    
    // Spawn consumer threads
    for i in 0..4 {
        let q = Arc::clone(&queue);
        let handle = thread::spawn(move || {
            for _ in 0..25 {
                let value = q.dequeue();
                println!("Consumer {} dequeued {}", i, value);
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

The Rust implementation demonstrates the language's safety guarantees: the `Mutex<T>` type enforces that the contained data can only be accessed while holding the lock through its `lock()` method which returns a `MutexGuard` that implements `Deref` and `DerefMut`. When the guard goes out of scope, its `Drop` implementation automatically releases the lock, preventing the common C mistake of forgetting to unlock. The `Arc<T>` type ensures that the queue remains valid as long as any thread holds a reference, and the type system prevents data races at compile time by requiring that shared mutable state is protected by synchronization primitives.

Lock-free data structures eliminate blocking entirely through atomic compare-and-swap operations that allow threads to make progress independently. The canonical example is a lock-free stack implemented using the Treiber algorithm, where the head pointer is updated atomically and each operation retries on failure using a compare-and-swap loop.

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;
use std::sync::Arc;
use std::thread;

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

impl<T> LockFreeStack<T> {
    fn new() -> Self {
        LockFreeStack {
            head: AtomicPtr::new(ptr::null_mut()),
        }
    }
    
    fn push(&self, data: T) {
        let new_node = Box::into_raw(Box::new(Node {
            data,
            next: ptr::null_mut(),
        }));
        
        loop {
            let head = self.head.load(Ordering::Acquire);
            unsafe {
                (*new_node).next = head;
            }
            
            if self.head.compare_exchange(
                head,
                new_node,
                Ordering::Release,
                Ordering::Acquire
            ).is_ok() {
                break;
            }
        }
    }
    
    fn pop(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Acquire);
            if head.is_null() {
                return None;
            }
            
            let next = unsafe { (*head).next };
            
            if self.head.compare_exchange(
                head,
                next,
                Ordering::Release,
                Ordering::Acquire
            ).is_ok() {
                let data = unsafe { Box::from_raw(head).data };
                return Some(data);
            }
        }
    }
}

impl<T> Drop for LockFreeStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}

fn main() {
    let stack = Arc::new(LockFreeStack::new());
    let mut handles = vec![];
    
    for i in 0..4 {
        let s = Arc::clone(&stack);
        let handle = thread::spawn(move || {
            for j in 0..10000 {
                s.push(i * 10000 + j);
            }
        });
        handles.push(handle);
    }
    
    for i in 0..4 {
        let s = Arc::clone(&stack);
        let handle = thread::spawn(move || {
            let mut count = 0;
            for _ in 0..10000 {
                if s.pop().is_some() {
                    count += 1;
                }
            }
            println!("Thread {} popped {} items", i, count);
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

The lock-free stack uses acquire-release ordering to establish synchronization: the release store in `push` ensures that the node's data and next pointer are visible to any thread that subsequently performs an acquire load of the head pointer. The compare-and-swap retry loop handles the race condition where multiple threads attempt to update the head simultaneously—only one succeeds, and the others retry with the updated head value. This approach eliminates blocking but introduces the ABA problem: if a thread reads head pointer A, another thread pops A and pushes a new node that happens to be allocated at the same address A, the first thread's compare-and-swap will spuriously succeed. Production implementations address ABA through tagged pointers that include a version counter in the unused high bits of the pointer.

Asynchronous programming with the async/await model transforms blocking I/O operations into cooperative yields that allow an event loop to multiplex thousands of concurrent tasks onto a small thread pool. The Rust async ecosystem centers on the `Future` trait, which represents a computation that may not have completed yet, and the `async fn` syntax that desugars into a state machine implementing `Future`.

```rust
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::error::Error;

async fn handle_connection(mut socket: TcpStream) -> Result<(), Box<dyn Error>> {
    let mut buffer = [0; 1024];
    
    loop {
        let n = socket.read(&mut buffer).await?;
        
        if n == 0 {
            return Ok(());
        }
        
        socket.write_all(&buffer[0..n]).await?;
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    println!("Server listening on 127.0.0.1:8080");
    
    loop {
        let (socket, addr) = listener.accept().await?;
        println!("Accepted connection from {}", addr);
        
        tokio::spawn(async move {
            if let Err(e) = handle_connection(socket).await {
                eprintln!("Connection error: {}", e);
            }
        });
    }
}
```

The Tokio runtime maintains an event loop that polls registered futures for progress. When a future performs an async operation like `socket.read().await`, the runtime registers interest in the file descriptor with the OS through `epoll` on Linux or `kqueue` on BSD, then suspends the task and schedules another ready task. When the OS signals that the file descriptor is readable, the runtime resumes the suspended task, which continues execution after the await point. This design allows tens of thousands of concurrent connections with minimal memory overhead because each task only allocates stack space for its state machine rather than a full thread stack.

The actor model provides message-passing concurrency where each actor processes messages sequentially from a mailbox. The `actix` framework implements actors in Rust with typed message handlers and an async runtime.

```rust
use actix::prelude::*;
use std::time::Duration;

#[derive(Message)]
#[rtype(result = "()")]
struct Ping {
    count: usize,
}

#[derive(Message)]
#[rtype(result = "usize")]
struct GetCount;

struct PingActor {
    count: usize,
}

impl Actor for PingActor {
    type Context = Context<Self>;
    
    fn started(&mut self, _ctx: &mut Self::Context) {
        println!("PingActor started");
    }
}

impl Handler<Ping> for PingActor {
    type Result = ();
    
    fn handle(&mut self, msg: Ping, _ctx: &mut Context<Self>) -> Self::Result {
        self.count += msg.count;
        println!("Received ping, total count: {}", self.count);
    }
}

impl Handler<GetCount> for PingActor {
    type Result = usize;
    
    fn handle(&mut self, _msg: GetCount, _ctx: &mut Context<Self>) -> Self::Result {
        self.count
    }
}

#[actix::main]
async fn main() {
    let addr = PingActor { count: 0 }.start();
    
    for i in 0..10 {
        addr.do_send(Ping { count: i + 1 });
    }
    
    tokio::time::sleep(Duration::from_millis(100)).await;
    
    let count = addr.send(GetCount).await.unwrap();
    println!("Final count: {}", count);
    
    System::current().stop();
}
```

The actor implementation guarantees sequential message processing within each actor, eliminating data races on the actor's internal state. The `do_send` method delivers a message asynchronously without waiting for a response, while `send` returns a future that resolves when the actor handles the message and produces a result. Actors can maintain references to other actors' addresses and send messages to coordinate distributed computation without shared memory.

## 3. High-Performance Optimization & Failure Modes

The primary performance concern in concurrent systems lies in the interplay between cache coherence protocols and false sharing. Modern processors maintain cache coherency through the MESI protocol (Modified, Exclusive, Shared, Invalid) or its variants, where each cache line exists in one of these states across all CPU cores. When one core writes to a cache line, all other cores holding that line must invalidate their copies, forcing them to reload the line on the next access. False sharing occurs when two threads access independent variables that happen to reside on the same cache line—typically 64 bytes on x86-64—causing unnecessary cache invalidation storms that serialize execution despite the absence of logical data races.

The solution to false sharing involves explicit padding to ensure that frequently-written variables occupy distinct cache lines. Modern Rust provides the `#[repr(align(64))]` attribute to enforce cache line alignment.

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::thread;
use std::sync::Arc;

// Without padding - suffers from false sharing
struct UnpaddedCounters {
    counter1: AtomicUsize,
    counter2: AtomicUsize,
}

// With padding - each counter on separate cache line
#[repr(align(64))]
struct PaddedCounter {
    counter: AtomicUsize,
}

struct PaddedCounters {
    counter1: PaddedCounter,
    counter2: PaddedCounter,
}

fn benchmark_counters<T>(counters: Arc<T>, accessor1: fn(&T) -> &AtomicUsize, accessor2: fn(&T) -> &AtomicUsize) {
    let c1 = Arc::clone(&counters);
    let c2 = Arc::clone(&counters);
    
    let t1 = thread::spawn(move || {
        for _ in 0..10_000_000 {
            accessor1(&c1).fetch_add(1, Ordering::Relaxed);
        }
    });
    
    let t2 = thread::spawn(move || {
        for _ in 0..10_000_000 {
            accessor2(&c2).fetch_add(1, Ordering::Relaxed);
        }
    });
    
    t1.join().unwrap();
    t2.join().unwrap();
}

fn main() {
    let unpadded = Arc::new(UnpaddedCounters {
        counter1: AtomicUsize::new(0),
        counter2: AtomicUsize::new(0),
    });
    
    let padded = Arc::new(PaddedCounters {
        counter1: PaddedCounter { counter: AtomicUsize::new(0) },
        counter2: PaddedCounter { counter: AtomicUsize::new(0) },
    });
    
    println!("Benchmarking unpadded counters...");
    let start = std::time::Instant::now();
    benchmark_counters(unpadded, |c| &c.counter1, |c| &c.counter2);
    println!("Unpadded: {:?}", start.elapsed());
    
    println!("Benchmarking padded counters...");
    let start = std::time::Instant::now();
    benchmark_counters(padded, |c| &c.counter1.counter, |c| &c.counter2.counter);
    println!("Padded: {:?}", start.elapsed());
}
```

Lock contention represents another critical performance bottleneck where multiple threads repeatedly acquire and release the same lock. The naive solution of simply adding more locks often makes the problem worse by increasing the total time spent in lock acquisition and release. The fundamental optimization strategy involves reducing the critical section size—the amount of code executed while holding a lock—by performing as much computation as possible outside the lock and only protecting the minimal state update.

For read-heavy workloads, read-copy-update (RCU) provides a lock-free synchronization mechanism where readers access data structures without any synchronization overhead while writers create new versions of modified data and defer reclamation of old versions until all readers have completed. The Linux kernel extensively uses RCU for scalable read access to shared data structures. User-space implementations like the `crossbeam-epoch` crate in Rust provide epoch-based memory reclamation that amortizes the cost of tracking readers across batches of operations.

```rust
use crossbeam_epoch::{self as epoch, Atomic, Owned, Shared};
use std::sync::atomic::Ordering;
use std::sync::Arc;
use std::thread;

struct Node<T> {
    data: T,
    next: Atomic<Node<T>>,
}

struct LockFreeList<T> {
    head: Atomic<Node<T>>,
}

impl<T> LockFreeList<T> {
    fn new() -> Self {
        LockFreeList {
            head: Atomic::null(),
        }
    }
    
    fn push(&self, data: T) {
        let new_node = Owned::new(Node {
            data,
            next: Atomic::null(),
        });
        
        let guard = epoch::pin();
        loop {
            let head = self.head.load(Ordering::Acquire, &guard);
            new_node.next.store(head, Ordering::Relaxed);
            
            match self.head.compare_exchange(
                head,
                new_node,
                Ordering::Release,
                Ordering::Acquire,
                &guard
            ) {
                Ok(_) => break,
                Err(e) => {
                    new_node = e.new;
                }
            }
        }
    }
    
    fn iter(&self) -> ListIterator<T> {
        ListIterator {
            guard: epoch::pin(),
            current: self.head.load(Ordering::Acquire, &epoch::pin()),
        }
    }
}

struct ListIterator<'g, T> {
    guard: epoch::Guard,
    current: Shared<'g, Node<T>>,
}

impl<'g, T> Iterator for ListIterator<'g, T> {
    type Item = &'g T;
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.current.is_null() {
            return None;
        }
        
        unsafe {
            let node = self.current.deref();
            let data = &node.data;
            self.current = node.next.load(Ordering::Acquire, &self.guard);
            Some(data)
        }
    }
}

fn main() {
    let list = Arc::new(LockFreeList::new());
    let mut handles = vec![];
    
    for i in 0..4 {
        let l = Arc::clone(&list);
        let handle = thread::spawn(move || {
            for j in 0..1000 {
                l.push(i * 1000 + j);
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    let count = list.iter().count();
    println!("List contains {} elements", count);
}
```

The epoch-based reclamation works by dividing time into epochs and tracking which threads are active in each epoch. A thread pins the current epoch when it begins accessing shared data structures, preventing any objects retired in that epoch or earlier from being reclaimed. When a thread modifies a data structure, it retires the old version to the current epoch's garbage list. Periodically, the runtime scans all threads and advances the global epoch when no thread remains pinned to older epochs, allowing deferred reclamation of retired objects from those epochs. This design amortizes tracking overhead across many operations and provides wait-free read access at the cost of bounded memory overhead for pending reclamations.

Deadlock avoidance in complex systems requires establishing a total ordering on lock acquisitions. The simplest approach assigns a unique numeric identifier to each lock and requires that threads always acquire locks in ascending order. When a function needs to acquire multiple locks, it sorts them by ID before acquisition.

```rust
use std::sync::{Mutex, Arc};
use std::thread;

#[derive(Debug)]
struct Account {
    id: usize,
    balance: Mutex<i64>,
}

impl Account {
    fn new(id: usize, initial_balance: i64) -> Self {
        Account {
            id,
            balance: Mutex::new(initial_balance),
        }
    }
}

fn transfer_deadlock_prone(from: &Account, to: &Account, amount: i64) {
    let mut from_balance = from.balance.lock().unwrap();
    let mut to_balance = to.balance.lock().unwrap();
    
    if *from_balance >= amount {
        *from_balance -= amount;
        *to_balance += amount;
    }
}

fn transfer_deadlock_free(from: &Account, to: &Account, amount: i64) {
    let (first, second) = if from.id < to.id {
        (&from.balance, &to.balance)
    } else {
        (&to.balance, &from.balance)
    };
    
    let mut first_guard = first.lock().unwrap();
    let mut second_guard = second.lock().unwrap();
    
    let (from_balance, to_balance) = if from.id < to.id {
        (&mut *first_guard, &mut *second_guard)
    } else {
        (&mut *second_guard, &mut *first_guard)
    };
    
    if *from_balance >= amount {
        *from_balance -= amount;
        *to_balance += amount;
    }
}

fn main() {
    let account1 = Arc::new(Account::new(1, 1000));
    let account2 = Arc::new(Account::new(2, 1000));
    
    let a1 = Arc::clone(&account1);
    let a2 = Arc::clone(&account2);
    
    let t1 = thread::spawn(move || {
        for _ in 0..1000 {
            transfer_deadlock_free(&a1, &a2, 10);
        }
    });
    
    let a1 = Arc::clone(&account1);
    let a2 = Arc::clone(&account2);
    
    let t2 = thread::spawn(move || {
        for _ in 0..1000 {
            transfer_deadlock_free(&a2, &a1, 10);
        }
    });
    
    t1.join().unwrap();
    t2.join().unwrap();
    
    println!("Account 1: {}", *account1.balance.lock().unwrap());
    println!("Account 2: {}", *account2.balance.lock().unwrap());
}
```

The deadlock-free implementation establishes a global ordering by always acquiring locks in ascending ID order regardless of the logical direction of the transfer. This prevents the circular wait condition where thread T1 holds lock L1 and waits for L2 while thread T2 holds L2 and waits for L1. The tradeoff involves additional complexity in the locking protocol and potential for reduced parallelism when many threads contend for the same low-ID locks.

For applications requiring both high throughput and strong consistency guarantees, two-phase locking (2PL) provides serializability by dividing each transaction into a growing phase where locks are acquired but never released and a shrinking phase where locks are released but never acquired. Strict 2PL further requires holding all write locks until transaction commit, preventing cascading aborts. Database systems implement 2PL variants with deadlock detection through wait-for graphs and automatic transaction rollback when cycles are detected.

Work stealing schedulers optimize parallel task execution by allowing idle threads to steal work from busy threads' task queues. The Tokio runtime implements work stealing for async tasks, and Rayon provides a work-stealing thread pool for data parallel computations.

```rust
use rayon::prelude::*;

fn parallel_sum(data: &[i32]) -> i64 {
    data.par_iter()
        .map(|&x| x as i64)
        .sum()
}

fn parallel_quicksort(data: &mut [i32]) {
    if data.len() <= 1 {
        return;
    }
    
    let pivot_index = partition(data);
    let (left, right) = data.split_at_mut(pivot_index);
    
    rayon::join(
        || parallel_quicksort(left),
        || parallel_quicksort(&mut right[1..])
    );
}

fn partition(data: &mut [i32]) -> usize {
    let pivot = data[data.len() - 1];
    let mut i = 0;
    
    for j in 0..data.len() - 1 {
        if data[j] <= pivot {
            data.swap(i, j);
            i += 1;
        }
    }
    
    data.swap(i, data.len() - 1);
    i
}

fn main() {
    let data: Vec<i32> = (0..10_000_000).map(|x| x % 1000).collect();
    let sum = parallel_sum(&data);
    println!("Sum: {}", sum);
    
    let mut sort_data: Vec<i32> = (0..1_000_000).rev().collect();
    parallel_quicksort(&mut sort_data);
    println!("Sorted first 10 elements: {:?}", &sort_data[..10]);
}
```

The work-stealing implementation maintains a double-ended queue (deque) for each thread where the thread pushes and pops tasks from one end (LIFO) while other threads steal from the opposite end (FIFO). This design exploits locality: the thread works on recently created tasks that likely share cache lines, while stolen tasks are typically older and their data has likely been evicted from the stealer's cache. The Rayon `join` combinator spawns the left task and executes the right task inline, then waits for the left task to complete. If all threads are busy, the spawned task executes on the current thread; otherwise, an idle thread steals and executes it in parallel.

Priority inversion mitigation requires priority inheritance protocols where a low-priority thread temporarily inherits the priority of any high-priority thread waiting on its locks. The real-time Linux kernel patch (PREEMPT_RT) implements priority inheritance for mutexes and spinlocks to provide bounded latency for time-critical tasks. In userspace, careful system design that segregates real-time and non-real-time components into separate processes with appropriate scheduling policies (SCHED_FIFO or SCHED_RR) and CPU affinity prevents priority inversion at the cost of increased complexity.

Memory ordering optimizations allow relaxed atomic operations that do not enforce synchronization when only atomicity is required. The `Ordering::Relaxed` mode on atomic operations provides no ordering guarantees beyond atomicity, allowing the CPU and compiler maximum freedom to reorder operations. This suffices for counters and statistics where the exact ordering of increments does not matter.

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;

struct Statistics {
    requests_total: AtomicU64,
    requests_success: AtomicU64,
    requests_error: AtomicU64,
}

impl Statistics {
    fn new() -> Self {
        Statistics {
            requests_total: AtomicU64::new(0),
            requests_success: AtomicU64::new(0),
            requests_error: AtomicU64::new(0),
        }
    }
    
    fn record_request(&self, success: bool) {
        self.requests_total.fetch_add(1, Ordering::Relaxed);
        if success {
            self.requests_success.fetch_add(1, Ordering::Relaxed);
        } else {
            self.requests_error.fetch_add(1, Ordering::Relaxed);
        }
    }
    
    fn get_snapshot(&self) -> (u64, u64, u64) {
        (
            self.requests_total.load(Ordering::Relaxed),
            self.requests_success.load(Ordering::Relaxed),
            self.requests_error.load(Ordering::Relaxed),
        )
    }
}

fn main() {
    let stats = Arc::new(Statistics::new());
    let mut handles = vec![];
    
    for i in 0..8 {
        let s = Arc::clone(&stats);
        let handle = thread::spawn(move || {
            for j in 0..1_000_000 {
                s.record_request((i + j) % 10 != 0);
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    let (total, success, error) = stats.get_snapshot();
    println!("Total: {}, Success: {}, Error: {}", total, success, error);
}
```

The relaxed ordering provides maximum performance for statistics because the precise timing of when one thread observes another thread's increments does not affect correctness. The final snapshot may observe increments in an arbitrary order, but all increments are guaranteed to eventually become visible. When synchronization is required—for example, signaling that initialization is complete—acquire-release ordering establishes happens-before relationships without the full sequential consistency overhead.

Async runtime tuning involves configuring the thread pool size and work-stealing strategy based on workload characteristics. I/O-bound workloads benefit from larger thread pools that can handle blocking syscalls without starving other tasks, while CPU-bound workloads should use thread pools sized to the number of physical cores to avoid context-switching overhead. The Tokio runtime provides tunable parameters for these scenarios.

```rust
use tokio::runtime::Builder;
use tokio::time::{sleep, Duration};

fn main() {
    // I/O-bound runtime with large thread pool
    let io_runtime = Builder::new_multi_thread()
        .worker_threads(16)
        .thread_name("io-worker")
        .enable_all()
        .build()
        .unwrap();
    
    // CPU-bound runtime sized to physical cores
    let cpu_runtime = Builder::new_multi_thread()
        .worker_threads(num_cpus::get())
        .thread_name("cpu-worker")
        .enable_all()
        .build()
        .unwrap();
    
    io_runtime.block_on(async {
        let mut handles = vec![];
        for i in 0..100 {
            handles.push(tokio::spawn(async move {
                sleep(Duration::from_millis(100)).await;
                println!("I/O task {} completed", i);
            }));
        }
        
        for handle in handles {
            handle.await.unwrap();
        }
    });
    
    cpu_runtime.block_on(async {
        let result: u64 = tokio::task::spawn_blocking(|| {
            (0..1_000_000_000_u64).sum()
        }).await.unwrap();
        
        println!("CPU-intensive result: {}", result);
    });
}
```

The blocking task spawned with `spawn_blocking` executes on a dedicated thread pool separate from the async executor to prevent blocking the event loop. This design isolates CPU-intensive or blocking operations that cannot be made async from affecting the responsiveness of I/O-bound tasks. Production systems often deploy multiple Tokio runtimes with different configurations for different workload classes, routing tasks based on their expected resource consumption patterns.
