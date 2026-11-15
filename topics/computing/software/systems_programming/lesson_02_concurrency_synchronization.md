# Lesson 2: Concurrency and Synchronization Primitives

## 1. First-Principles Intuition & Invariants

The central challenge of concurrent programming emerges from a deceptively simple observation: modern processors execute instructions out of order, compilers reorder memory operations for optimization, and multiple execution contexts share mutable state through a memory hierarchy with multiple levels of caching. When two threads attempt to increment the same counter, what appears to be a single logical operation—read, add one, write back—decomposes into three distinct memory transactions. Without coordination, these transactions interleave arbitrarily, producing lost updates where both threads read the same initial value, increment it independently, and write back identical results, permanently losing one increment.

This fundamental race condition illustrates the core invariant that all synchronization primitives exist to preserve: **sequential consistency of shared state mutations**. In the absence of synchronization, the hardware and compiler are free to reorder operations across threads in ways that violate program order as perceived by the programmer. A store to one memory location may become visible to other cores after a subsequent store to a different location, creating causality inversions. A load may be satisfied from stale cache lines rather than observing the most recent store from another core. The C and C++ memory models formalize these behaviors through the concept of data races: unsynchronized conflicting accesses where at least one is a write constitute undefined behavior, permitting the compiler to assume such races never occur and optimize accordingly.

Synchronization primitives restore order through two complementary mechanisms: mutual exclusion and memory ordering. Mutual exclusion, exemplified by mutexes and semaphores, ensures that critical sections execute atomically with respect to one another by serializing access. Only one thread may hold a mutex at any time, transforming concurrent execution into sequential execution for protected regions. Memory ordering, enforced through atomic operations and memory barriers, constrains how stores and loads may be reordered, establishing happens-before relationships that guarantee visibility across threads. An atomic store with release semantics ensures that all prior writes become visible before the atomic write itself, while an atomic load with acquire semantics ensures that all subsequent reads observe memory state at least as recent as the atomic load.

The happens-before relation forms the foundational partial order over operations in concurrent systems. When operation A happens-before operation B, A's effects are guaranteed visible to B. This relation is established through synchronization edges: releasing a mutex happens-before acquiring the same mutex, an atomic store-release happens-before an atomic load-acquire that reads the stored value, and thread creation happens-before the first operation in the created thread. Transitive closure of these edges produces the global happens-before order, which must respect program order within each thread while permitting arbitrary interleavings that preserve the happens-before constraints.

The hardware mechanisms underlying these abstractions vary across architectures but converge on similar principles. x86-64 provides a relatively strong total store order (TSO) model where stores from one processor become visible to other processors in program order, requiring only store-load barriers for full sequential consistency. ARM and RISC-V implement weaker memory models permitting extensive reordering, requiring explicit barrier instructions (DMB, DSB on ARM; FENCE on RISC-V) to enforce ordering. Cache coherence protocols like MESI (Modified, Exclusive, Shared, Invalid) maintain consistency across processor caches through invalidation messages on stores to shared lines, but coherence alone does not guarantee ordering—two independent cache lines may propagate updates in different orders without violating coherence.

Lock-free programming pushes beyond mutual exclusion by constructing algorithms that guarantee system-wide progress even when individual threads are delayed indefinitely. A lock-free algorithm ensures that some thread always makes progress in bounded time, typically through atomic compare-and-swap (CAS) operations that retry on contention rather than blocking. Wait-free algorithms provide the strongest guarantee: every thread makes progress in bounded time regardless of other threads' behavior, a property achievable through helping mechanisms where threads complete operations on behalf of delayed peers.

The performance characteristics of synchronization primitives scale with contention patterns. Uncontended locks on modern systems require only a handful of atomic instructions and can complete in tens of nanoseconds. Contended locks force threads into the kernel for suspension and wakeup, incurring microseconds of latency plus context switching overhead. Spinning vs. blocking trade-offs depend on critical section duration: spinning wastes CPU cycles but avoids syscall overhead for brief critical sections, while blocking conserves CPU but adds kernel transition costs. Adaptive mutexes spin briefly before blocking, adjusting behavior based on lock-holding patterns.

## 2. Core Architecture & Mechanics

Mutex implementations build on atomic compare-and-swap to provide mutual exclusion with kernel fallback for contended cases. The classic two-phase mutex maintains an atomic state word encoding both the lock bit and a count of waiting threads. Lock acquisition begins with an atomic CAS attempting to set the lock bit; success grants immediate entry. On contention, the thread increments the waiter count, then invokes a futex syscall (on Linux) to suspend until wakeup. Unlock clears the lock bit and, if waiters exist, invokes futex wake to resume one suspended thread. This design minimizes syscall frequency: uncontended operations remain entirely in userspace, while contended operations batch multiple lock attempts into single kernel transitions.

```c
typedef struct {
    atomic_int state;  // bit 0: locked, bits 1-31: waiter count
} mutex_t;

void mutex_lock(mutex_t *m) {
    int expected = 0;
    if (atomic_compare_exchange_strong(&m->state, &expected, 1)) {
        return;  // Fast path: acquired uncontended lock
    }
    
    // Slow path: increment waiter count and wait
    while (1) {
        int old_state = atomic_fetch_add(&m->state, 2) | 1;  // Set lock bit, add to waiter count
        if ((old_state & 1) == 0) {
            // Lock became available during increment
            return;
        }
        futex_wait(&m->state, old_state);  // Suspend until woken
        
        // Retry acquisition after wakeup
        expected = 0;
        if (atomic_compare_exchange_strong(&m->state, &expected, 1)) {
            atomic_fetch_sub(&m->state, 2);  // Decrement waiter count
            return;
        }
    }
}

void mutex_unlock(mutex_t *m) {
    int old_state = atomic_fetch_sub(&m->state, 1);
    if (old_state > 1) {
        // Waiters exist: wake one
        futex_wake(&m->state, 1);
    }
}
```

The futex primitive exposes a memory address to the kernel scheduler, enabling userspace-managed synchronization with kernel-provided blocking. `futex_wait(addr, expected_val)` atomically checks that `*addr == expected_val` and, if true, suspends the calling thread on a kernel wait queue associated with that address. This atomicity prevents races where the condition changes between userspace check and kernel suspension. `futex_wake(addr, n)` wakes up to `n` threads waiting on that address. The kernel maintains a hash table of wait queues indexed by physical address, requiring no pre-registration or explicit lifecycle management.

Semaphores generalize mutexes to permit multiple concurrent accessors, maintaining an atomic counter representing available resources. Acquiring a semaphore decrements the counter; if the result remains non-negative, the operation succeeds immediately. Negative results indicate resource exhaustion, triggering suspension until a release operation increments the counter and wakes a waiter. Binary semaphores (initial count 1) behave identically to mutexes but lack ownership semantics—any thread may release a semaphore regardless of which thread acquired it, enabling signaling patterns where one thread signals completion to another.

```c
typedef struct {
    atomic_int count;
    atomic_int waiters;
} semaphore_t;

void semaphore_init(semaphore_t *sem, int initial) {
    atomic_store(&sem->count, initial);
    atomic_store(&sem->waiters, 0);
}

void semaphore_wait(semaphore_t *sem) {
    if (atomic_fetch_sub(&sem->count, 1) > 0) {
        return;  // Resource available
    }
    
    // Out of resources: wait for signal
    atomic_fetch_add(&sem->waiters, 1);
    while (atomic_load(&sem->count) <= 0) {
        futex_wait(&sem->count, atomic_load(&sem->count));
    }
    atomic_fetch_sub(&sem->waiters, 1);
}

void semaphore_post(semaphore_t *sem) {
    if (atomic_fetch_add(&sem->count, 1) < 0) {
        // Waiters exist: wake one
        if (atomic_load(&sem->waiters) > 0) {
            futex_wake(&sem->count, 1);
        }
    }
}
```

Read-write locks optimize for scenarios where reads vastly outnumber writes by permitting concurrent readers while ensuring exclusive writer access. The challenge lies in preventing writer starvation under continuous read load while maintaining fairness. Phase-fair RW locks partition time into read phases and write phases, granting all pending reads access during a read phase but blocking new reads once a writer arrives, ensuring bounded wait time for writers. The implementation tracks reader count, writer presence, and phase state through carefully orchestrated atomic operations.

```c
typedef struct {
    atomic_int state;  // bits 0-15: reader count, bit 16: write locked, bit 17: writer waiting
} rwlock_t;

#define READER_MASK 0xFFFF
#define WRITE_LOCKED (1 << 16)
#define WRITER_WAITING (1 << 17)

void rwlock_read_lock(rwlock_t *lock) {
    while (1) {
        int state = atomic_load(&lock->state);
        if (state & WRITER_WAITING) {
            // Writer pending: yield to avoid reader bias
            futex_wait(&lock->state, state);
            continue;
        }
        if (atomic_compare_exchange_weak(&lock->state, &state, state + 1)) {
            return;  // Acquired read lock
        }
    }
}

void rwlock_read_unlock(rwlock_t *lock) {
    if ((atomic_fetch_sub(&lock->state, 1) & READER_MASK) == 1) {
        // Last reader: wake waiting writers
        futex_wake(&lock->state, 1);
    }
}

void rwlock_write_lock(rwlock_t *lock) {
    // Set writer-waiting bit to block new readers
    int state = atomic_fetch_or(&lock->state, WRITER_WAITING);
    
    // Wait for all readers to drain
    while ((state & READER_MASK) != 0) {
        futex_wait(&lock->state, state);
        state = atomic_load(&lock->state);
    }
    
    // Acquire write lock
    while (!atomic_compare_exchange_weak(&lock->state, &state, WRITE_LOCKED)) {
        futex_wait(&lock->state, state);
        state = atomic_load(&lock->state);
    }
}

void rwlock_write_unlock(rwlock_t *lock) {
    atomic_store(&lock->state, 0);
    futex_wake(&lock->state, INT_MAX);  // Wake all waiters
}
```

Atomic operations provide the foundation for all higher-level synchronization through hardware-supported read-modify-write instructions. Compare-and-swap atomically reads a memory location, compares its value against an expected value, and conditionally writes a new value only if the comparison succeeds, returning the original value. This semantic enables lock-free algorithms through optimistic concurrency: read shared state, compute a proposed update, attempt CAS, and retry if another thread modified the state concurrently.

```c
// Lock-free stack using CAS
typedef struct node {
    void *data;
    struct node *next;
} node_t;

typedef struct {
    atomic_uintptr_t head;
} stack_t;

void stack_push(stack_t *stack, node_t *node) {
    uintptr_t old_head = atomic_load(&stack->head);
    do {
        node->next = (node_t *)old_head;
    } while (!atomic_compare_exchange_weak(&stack->head, &old_head, (uintptr_t)node));
}

node_t *stack_pop(stack_t *stack) {
    uintptr_t old_head = atomic_load(&stack->head);
    node_t *node;
    do {
        node = (node_t *)old_head;
        if (node == NULL) return NULL;
    } while (!atomic_compare_exchange_weak(&stack->head, &old_head, (uintptr_t)node->next));
    return node;
}
```

Memory ordering semantics attached to atomic operations control reordering constraints. Sequentially consistent atomics (the default in C11/C++11) impose total ordering across all threads—all threads observe the same order of sequentially consistent operations. This strongest guarantee eliminates counterintuitive reorderings but incurs performance costs through memory barriers on weakly-ordered architectures. Release-acquire semantics weaken the guarantee: a store-release synchronizes-with a load-acquire that reads the stored value, establishing happens-before from all operations before the release to all operations after the acquire. Relaxed atomics provide atomicity without ordering, useful for counters where operation order is irrelevant.

```c
// Producer-consumer using acquire-release
typedef struct {
    atomic_int data;
    atomic_int ready;
} message_t;

// Producer
void produce(message_t *msg, int value) {
    atomic_store_explicit(&msg->data, value, memory_order_relaxed);
    atomic_store_explicit(&msg->ready, 1, memory_order_release);  // Publish data
}

// Consumer
int consume(message_t *msg) {
    while (atomic_load_explicit(&msg->ready, memory_order_acquire) == 0) {
        // Spin-wait for data
    }
    return atomic_load_explicit(&msg->data, memory_order_relaxed);  // Data visible after acquire
}
```

Condition variables enable threads to efficiently wait for arbitrary predicates over shared state. The classic pattern combines a mutex protecting the predicate, atomic predicate evaluation under the mutex, and conditional suspension on the condition variable. The critical insight is that `pthread_cond_wait` atomically releases the mutex and suspends, preventing races where the predicate becomes true between checking and sleeping. Spurious wakeups—wakeups without corresponding signals—require predicates to be rechecked in loops rather than single if statements.

```c
typedef struct {
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    int count;
} bounded_queue_t;

void queue_wait_non_empty(bounded_queue_t *q) {
    pthread_mutex_lock(&q->mutex);
    while (q->count == 0) {  // Loop handles spurious wakeups
        pthread_cond_wait(&q->cond, &q->mutex);  // Atomically unlock and wait
    }
    // Predicate holds, mutex locked
    q->count--;
    pthread_mutex_unlock(&q->mutex);
}

void queue_signal_non_empty(bounded_queue_t *q) {
    pthread_mutex_lock(&q->mutex);
    q->count++;
    pthread_cond_signal(&q->cond);  // Wake one waiter
    pthread_mutex_unlock(&q->mutex);
}
```

The ABA problem plagues naive CAS-based algorithms when a value changes from A to B and back to A, causing a CAS expecting A to succeed despite intervening modifications. Consider a lock-free stack where thread 1 reads head pointer A, thread 2 pops A and pushes B then A, then thread 1's CAS succeeds despite structural changes. Solutions include tagged pointers (combining the pointer with a version counter in a double-word CAS) or hazard pointers (threads publish pointers they're accessing, preventing reclamation of in-use nodes).

```c
// Double-word CAS for ABA protection (x86-64)
typedef struct {
    node_t *ptr;
    uint64_t tag;
} tagged_ptr_t;

typedef struct {
    _Atomic tagged_ptr_t head;
} aba_safe_stack_t;

void stack_push_aba_safe(aba_safe_stack_t *stack, node_t *node) {
    tagged_ptr_t old_head, new_head;
    old_head = atomic_load(&stack->head);
    do {
        node->next = old_head.ptr;
        new_head.ptr = node;
        new_head.tag = old_head.tag + 1;  // Increment version
    } while (!atomic_compare_exchange_weak(&stack->head, &old_head, new_head));
}
```

## 3. High-Performance Optimization & Failure Modes

Lock granularity fundamentally determines scalability under contention. Coarse-grained locking protects large data structures with a single lock, simplifying correctness reasoning but serializing all operations. Fine-grained locking partitions structures into independently locked regions, permitting concurrent operations on disjoint data at the cost of increased complexity and potential deadlock. Hash tables exemplify this trade-off: a per-table lock forces sequential inserts even to different buckets, while per-bucket locks enable parallel operations across buckets but require careful ordering to prevent deadlock when operations span multiple buckets.

```c
// Fine-grained hash table with bucket-level locking
#define BUCKETS 1024

typedef struct {
    pthread_mutex_t locks[BUCKETS];
    node_t *buckets[BUCKETS];
} hash_table_t;

void hash_insert(hash_table_t *table, uint32_t key, void *value) {
    uint32_t bucket = key % BUCKETS;
    pthread_mutex_lock(&table->locks[bucket]);
    
    node_t *node = malloc(sizeof(node_t));
    node->key = key;
    node->value = value;
    node->next = table->buckets[bucket];
    table->buckets[bucket] = node;
    
    pthread_mutex_unlock(&table->locks[bucket]);
}

void hash_move(hash_table_t *table, uint32_t from_key, uint32_t to_key) {
    uint32_t from_bucket = from_key % BUCKETS;
    uint32_t to_bucket = to_key % BUCKETS;
    
    // Lock in consistent order to prevent deadlock
    uint32_t first = (from_bucket < to_bucket) ? from_bucket : to_bucket;
    uint32_t second = (from_bucket < to_bucket) ? to_bucket : from_bucket;
    
    pthread_mutex_lock(&table->locks[first]);
    if (first != second) {
        pthread_mutex_lock(&table->locks[second]);
    }
    
    // Perform move operation under both locks
    // ...
    
    pthread_mutex_unlock(&table->locks[second]);
    if (first != second) {
        pthread_mutex_unlock(&table->locks[first]);
    }
}
```

False sharing destroys parallel performance through unintended cache line contention. When independent variables accessed by different threads reside on the same cache line, writes from one thread invalidate the entire line in other cores' caches, forcing cache coherence protocol traffic despite logical independence. The solution is padding or alignment to ensure frequently written variables occupy distinct cache lines, trading memory overhead for parallelism.

```c
// False sharing example
typedef struct {
    atomic_int counter_a;  // Thread 1 increments
    atomic_int counter_b;  // Thread 2 increments
} bad_counters_t;  // counter_a and counter_b share cache line

// Cache-line aligned counters
typedef struct {
    atomic_int counter_a;
    char pad[64 - sizeof(atomic_int)];  // Pad to cache line boundary
} aligned_counter_t;

typedef struct {
    aligned_counter_t a;
    aligned_counter_t b;
} good_counters_t;  // counter_a and counter_b on separate cache lines
```

Lock convoy pathologies arise when multiple threads queue behind a lock protecting a brief critical section, with each thread experiencing full context switch overhead despite minimal work. The convoy forms when the first thread blocks, forcing subsequent threads into the kernel even though the lock would become available microseconds later. Spinning briefly before blocking amortizes syscall costs: if the lock-holder completes during the spin window, the waiter acquires immediately without kernel involvement. Modern adaptive mutexes spin while the lock-holder is actively running (observable via scheduler state) but block immediately if the holder is itself suspended, avoiding wasted spin cycles.

Priority inversion occurs when a high-priority thread blocks on a lock held by a low-priority thread, which cannot execute because medium-priority threads monopolize the CPU. The high-priority thread suffers unbounded delay despite no direct contention with medium-priority work. Priority inheritance protocols solve this by temporarily elevating the lock-holder's priority to match the highest-priority waiter, ensuring the lock-holder can complete its critical section and release the lock.

```c
// Priority inheritance mutex (conceptual)
typedef struct {
    atomic_int locked;
    pthread_t owner;
    int owner_priority;
    int inherited_priority;
} pi_mutex_t;

void pi_mutex_lock(pi_mutex_t *m) {
    int expected = 0;
    while (!atomic_compare_exchange_weak(&m->locked, &expected, 1)) {
        // Boost owner priority to current thread's priority if higher
        int my_priority = get_thread_priority(pthread_self());
        if (my_priority > m->inherited_priority) {
            atomic_store(&m->inherited_priority, my_priority);
            set_thread_priority(m->owner, my_priority);
        }
        futex_wait(&m->locked, 1);
        expected = 0;
    }
    m->owner = pthread_self();
    m->owner_priority = get_thread_priority(pthread_self());
    m->inherited_priority = m->owner_priority;
}
```

Deadlock prevention requires establishing a total order over locks and acquiring them consistently in that order across all code paths. Global lock ordering by memory address provides a simple solution: `lock_pair(lock1, lock2)` always locks the lower address first. Hand-over-hand locking in linked structures releases the previous lock before acquiring the next, maintaining at most one lock held at any time but requiring careful validation that the unlocked state remains consistent.

Lock-free data structures eliminate blocking entirely but introduce complexity in memory reclamation. The fundamental challenge: a node removed from a structure cannot be freed immediately because concurrent readers may still traverse pointers to it. Epoch-based reclamation defers deallocation until all threads that might have observed the node have passed through a quiescent state (crossed an epoch boundary). Hazard pointers allow threads to explicitly protect pointers they're dereferencing, with deallocation proceeding only when no thread protects a given pointer.

```c
// Epoch-based reclamation
#define MAX_THREADS 64
atomic_int global_epoch = 0;
__thread int local_epoch = 0;
__thread node_t *retire_list = NULL;

void epoch_enter(void) {
    local_epoch = atomic_load(&global_epoch);
}

void epoch_exit(void) {
    // Check if all threads have advanced past our epoch
    int current = atomic_load(&global_epoch);
    for (int i = 0; i < MAX_THREADS; i++) {
        if (thread_epochs[i] < local_epoch) {
            return;  // Some thread still in old epoch
        }
    }
    
    // Safe to reclaim nodes from retire_list
    while (retire_list) {
        node_t *next = retire_list->next;
        free(retire_list);
        retire_list = next;
    }
}

void retire_node(node_t *node) {
    node->next = retire_list;
    retire_list = node;
}
```

Transactional memory promises composable atomic operations through software or hardware support for speculative execution with rollback on conflict. Hardware transactional memory (HTM) on x86 (TSX extensions, now deprecated), PowerPC, and ARM exposes speculative regions via begin/commit primitives. The CPU buffers stores and monitors loads within the transaction; conflicting access from another core aborts the transaction, discarding buffered stores and re-executing the region. Capacity limits (typically L1 cache size) and interrupt-induced aborts require fallback paths using conventional locks, limiting practical applicability.

```c
// Intel TSX (historical example)
#include <immintrin.h>

void transactional_transfer(account_t *from, account_t *to, int amount) {
    int retries = 0;
    while (retries < 5) {
        unsigned status = _xbegin();
        if (status == _XBEGIN_STARTED) {
            // Speculative execution: no locks needed
            if (from->balance >= amount) {
                from->balance -= amount;
                to->balance += amount;
            }
            _xend();
            return;
        }
        retries++;
    }
    
    // Fallback: use locks
    pthread_mutex_lock(&from->lock);
    pthread_mutex_lock(&to->lock);
    if (from->balance >= amount) {
        from->balance -= amount;
        to->balance += amount;
    }
    pthread_mutex_unlock(&to->lock);
    pthread_mutex_unlock(&from->lock);
}
```

Profiling contention requires tools that observe lock hold times, wait times, and contention rates. Linux `perf` can sample on lock functions (`perf record -e sched:sched_stat_sleep,sched:sched_stat_blocked`), while dedicated lock profilers instrument mutex operations to track per-lock statistics. High wait-to-hold-time ratios indicate excessive contention amenable to finer-grained locking. Uneven lock hold time distributions suggest algorithmic improvements: if 90% of acquisitions complete in microseconds but 10% take milliseconds, splitting the slow path into a separate lock reduces average contention.

Memory model violations manifest as rare, non-deterministic bugs difficult to reproduce. ThreadSanitizer (TSan) instruments every memory access to detect races dynamically, tracking happens-before edges and reporting conflicting accesses lacking synchronization. Formal verification tools like CBMC perform bounded model checking, exhaustively exploring thread interleavings up to a depth bound. For deployed systems, diagnostic tooling includes atomic counters tracking unexpected state transitions, assert-based invariant checks on shared data structure traversal, and logging of interleavings around suspected races.

The performance spectrum of synchronization scales from lock-free (tens of nanoseconds for uncontended atomic operations) through userspace mutexes (50-100ns uncontended, microseconds contended) to kernel-mediated semaphores and condition variables (microseconds minimum). Selecting appropriate primitives requires profiling actual contention patterns: uncontended locks cost little, while contended locks demand either fine-grained partitioning or redesign toward lock-free algorithms. The ultimate optimization is avoiding shared mutable state entirely through message passing, thread-local storage, or immutable data structures copied on write—synchronization-free architectures where possible, carefully synchronized where necessary.
