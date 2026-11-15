# Lesson 4: Concurrency Threading Models

## 1. First-Principles Intuition & Invariants

Mobile platforms present a concurrency challenge fundamentally different from server or desktop environments. Where a backend service can spawn threads liberally and scale horizontally across cores, mobile applications operate under strict power budgets, thermal constraints, and user interface responsiveness guarantees. The central invariant governing mobile concurrency is the **main thread must never block**. This seemingly simple rule cascades into architectural constraints that shape every aspect of how we structure concurrent work.

The main thread—sometimes called the UI thread—is the single execution context responsible for processing user input events, rendering frame buffers to the display, and maintaining the sixty-frame-per-second contract that defines perceived fluidity. On iOS, this is the thread where `UIApplication` dispatches touch events and `CADisplayLink` fires display refresh callbacks. On Android, it's where the `Looper` processes messages from the `MessageQueue` and the choreographer schedules vsync-aligned frame rendering. Any work that consumes more than approximately sixteen milliseconds on this thread introduces dropped frames, perceived lag, and application non-responsiveness warnings from the operating system.

This constraint forces a partition of computation into two categories: latency-sensitive work that must execute synchronously on the main thread, and everything else that must be offloaded to background execution contexts. The latency-sensitive category is surprisingly narrow—updating view hierarchies, layout calculation for visible elements, and immediate response to touch gestures. All other computation—network requests, database queries, image decoding, cryptographic operations, JSON parsing—must migrate to background threads or risk violating the frame budget.

The architectural complexity emerges from coordination between these execution contexts. Pure parallelism is insufficient; mobile applications require structured concurrency primitives that express dependencies, cancellation propagation, and thread affinity constraints. A network response must be parsed on a background thread, but the resulting data structure must update the view hierarchy on the main thread. An image decode operation should cancel if the user scrolls past the corresponding cell before decoding completes. A database transaction spanning multiple queries needs atomic visibility guarantees across thread boundaries.

Mobile platforms provide layered abstractions to manage this complexity. At the lowest level sit platform threading primitives—POSIX threads with priority inheritance, kernel-level dispatch queues with quality-of-service classifications, and work stealing schedulers that balance load across heterogeneous CPU cores. Middle layers provide structured concurrency—Grand Central Dispatch on iOS, `Executor` and `WorkManager` on Android—that abstract thread management behind queue semantics and async/await language constructs. Top layers offer domain-specific frameworks: `UIKit` main thread assertions, `RxSwift` observable streams, Kotlin coroutines with structured scopes.

The power budget constraint introduces a second-order effect: not all background threads are equivalent. Mobile processors implement heterogeneous multi-core architectures with high-performance cores clocked at three gigahertz alongside efficiency cores running at one-and-a-half gigahertz. Background work scheduled with user-interactive priority may execute on performance cores, consuming battery rapidly but completing within milliseconds. Work scheduled as background utility or maintenance may be deferred until the device is charging or throttled to efficiency cores, trading latency for power efficiency.

Threading models must also account for process lifecycle transitions. Mobile operating systems aggressively suspend applications that transition to the background, freezing all threads except those explicitly granted background execution time. On iOS, background execution is limited to specific categories—audio playback, location updates, background fetch—with strict time limits enforced by process assertions. Android provides background services with similar constraints but different lifecycle semantics tied to foreground service notifications and doze mode exemptions.

Race conditions in mobile environments carry unique consequences beyond data corruption. A race between a background network callback and view controller deallocation can trigger use-after-free crashes when the callback attempts to update deallocated UI objects. A race between a database write and application suspension can corrupt SQLite journals if the write doesn't complete before process termination. A race between concurrent image decodes for the same URL can waste battery decoding the same image multiple times in parallel.

The invariants governing correct concurrent mobile applications therefore include: main thread work must complete within the vsync interval; background work must respect quality-of-service priorities and power budgets; inter-thread communication must preserve strong reference lifetimes; cancellation must propagate through async operation graphs; and background execution must coordinate with process lifecycle transitions. These invariants inform the architecture of production threading models.

## 2. Core Architecture & Mechanics

Grand Central Dispatch represents the foundational concurrency primitive on Apple platforms, providing a work queue abstraction over kernel thread pools. At its core, GCD maintains a hierarchy of dispatch queues—serial queues that execute blocks in FIFO order on a single thread, concurrent queues that execute blocks in parallel across multiple threads, and the singular main queue that executes on the main thread. Each queue has an associated quality-of-service class that maps to scheduling priority and CPU core selection.

The dispatch queue architecture builds on `libdispatch`, a kernel extension that implements lightweight work items and thread pool management. When you submit a block to a concurrent queue, `libdispatch` wraps it in a `dispatch_continuation_t` structure containing the block pointer, a reference to the target queue, and quality-of-service metadata. The runtime then consults the thread pool state, selecting an idle thread or spawning a new one if the pool hasn't reached its limit. Thread pool sizing adapts dynamically based on system load, core availability, and thermal state.

Quality-of-service propagation flows through the queue hierarchy. When you create a queue with `QOS_CLASS_USER_INITIATED`, blocks dispatched to that queue inherit user-initiated priority unless they explicitly override it. If a user-initiated block dispatches work to a utility queue, the runtime may elevate the utility work's priority to avoid priority inversion—a scenario where high-priority work blocks waiting for low-priority work to complete. This priority inheritance extends through synchronization primitives; if a background thread holds a lock needed by the main thread, the background thread temporarily inherits main-thread priority to resolve the inversion.

```c
// Core GCD dispatch patterns showing queue hierarchy and QoS inheritance
#include <dispatch/dispatch.h>

// Global concurrent queues keyed by QoS class
dispatch_queue_t high_priority = dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0);
dispatch_queue_t background = dispatch_get_global_queue(QOS_CLASS_UTILITY, 0);

// Custom serial queue for synchronized access to shared state
dispatch_queue_t serial = dispatch_queue_create("com.example.serializer", 
                                                 DISPATCH_QUEUE_SERIAL);

// Async dispatch to background with main-thread callback
dispatch_async(background, ^{
    // Decode image on background thread (may take 50-100ms)
    UIImage *decoded = [self decodeImageFromDiskAtPath:path];
    
    // Hop to main queue for UI update (must complete in <16ms)
    dispatch_async(dispatch_get_main_queue(), ^{
        self.imageView.image = decoded;
        [self.imageView setNeedsDisplay];
    });
});

// Dispatch barrier for atomic read-modify-write on concurrent queue
dispatch_barrier_async(high_priority, ^{
    // This block executes exclusively; no other blocks on this queue
    // run concurrently with it
    [self.mutableDictionary setObject:value forKey:key];
});

// Dispatch groups for work synchronization across multiple queues
dispatch_group_t group = dispatch_group_create();

dispatch_group_async(group, high_priority, ^{
    [self fetchUserProfile];
});

dispatch_group_async(group, high_priority, ^{
    [self fetchUserPosts];
});

// Main thread blocks until both operations complete
dispatch_group_wait(group, DISPATCH_TIME_FOREVER);
// Alternatively, register async notification
dispatch_group_notify(group, dispatch_get_main_queue(), ^{
    [self updateUIWithFetchedData];
});
```

The dispatch barrier mechanism provides synchronized access to shared mutable state without explicit locks. When you submit a barrier block to a concurrent queue, the runtime ensures no other blocks execute on that queue concurrently with the barrier. Reads can proceed in parallel using regular `dispatch_async`, but writes use `dispatch_barrier_async` to establish mutual exclusion. This pattern implements a multiple-reader-single-writer lock using only queue semantics.

Android's concurrency model centers on the `Looper` and `Handler` message-passing primitives. Each thread can host a `Looper` that processes messages from a `MessageQueue`, implementing an event loop pattern similar to JavaScript's microtask queue. The main thread's `Looper` is created automatically by the Android runtime, but background threads must explicitly call `Looper.prepare()` to initialize their message queue and `Looper.loop()` to start processing.

```kotlin
// Android Looper-based message passing and HandlerThread pattern
class NetworkHandler : Handler(Looper.getMainLooper()) {
    override fun handleMessage(msg: Message) {
        when (msg.what) {
            MSG_REQUEST_COMPLETE -> {
                val response = msg.obj as HttpResponse
                updateUIWithResponse(response)
            }
            MSG_REQUEST_FAILED -> {
                val error = msg.obj as Exception
                displayErrorAlert(error.message)
            }
        }
    }
}

// HandlerThread encapsulates thread + Looper initialization
class DatabaseThread : HandlerThread("db-thread", THREAD_PRIORITY_BACKGROUND) {
    private lateinit var dbHandler: Handler
    
    override fun onLooperPrepared() {
        dbHandler = Handler(looper) { msg ->
            when (msg.what) {
                MSG_INSERT -> {
                    val record = msg.obj as Record
                    database.insert(record)
                    // Post result back to main thread
                    mainHandler.obtainMessage(MSG_INSERT_COMPLETE, record.id)
                        .sendToTarget()
                }
            }
            true
        }
    }
    
    fun insertRecord(record: Record) {
        dbHandler.obtainMessage(MSG_INSERT, record).sendToTarget()
    }
}

// Executor-based background work with explicit thread pool configuration
class ImageProcessor(context: Context) {
    // Fixed thread pool sized to CPU core count
    private val executor = ThreadPoolExecutor(
        /* corePoolSize */ Runtime.getRuntime().availableProcessors(),
        /* maximumPoolSize */ Runtime.getRuntime().availableProcessors(),
        /* keepAliveTime */ 60L, TimeUnit.SECONDS,
        /* workQueue */ LinkedBlockingQueue<Runnable>(),
        /* threadFactory */ object : ThreadFactory {
            private val counter = AtomicInteger(0)
            override fun newThread(r: Runnable) = Thread(r).apply {
                name = "image-processor-${counter.getAndIncrement()}"
                priority = Thread.NORM_PRIORITY - 1 // Slightly below normal
            }
        }
    )
    
    fun decodeAsync(path: String, callback: (Bitmap?) -> Unit) {
        executor.execute {
            val bitmap = try {
                BitmapFactory.decodeFile(path, BitmapFactory.Options().apply {
                    inPreferredConfig = Bitmap.Config.RGB_565
                })
            } catch (e: OutOfMemoryError) {
                null
            }
            
            // Callback executes on main thread
            mainHandler.post { callback(bitmap) }
        }
    }
}
```

The `HandlerThread` abstraction encapsulates thread creation, `Looper` initialization, and message queue processing in a single reusable component. You typically create one or more long-lived `HandlerThread` instances for background work categories—database operations, file I/O, network processing—and communicate with them via message passing. This avoids the overhead of repeatedly spawning and tearing down threads while maintaining clear thread affinity for operations that require it.

Thread pools provide batch-oriented parallelism for CPU-intensive work. Android's `ThreadPoolExecutor` allows explicit control over core pool size, maximum pool size, keep-alive time, and work queue type. For embarrassingly parallel workloads like image batch processing or data transformation, a fixed-size thread pool scaled to the device's CPU core count maximizes throughput without over-subscription. For workloads with variable arrival rates and latencies, a cached thread pool that grows and shrinks dynamically prevents thread starvation under load.

Modern mobile platforms increasingly surface async/await language constructs that abstract away manual thread management. Swift's async/await, built on top of structured concurrency and cooperative scheduling, allows you to write asynchronous code with linear control flow while the compiler and runtime handle thread transitions and suspension points.

```swift
// Swift structured concurrency with async/await and TaskGroup parallelism
actor ImageCache {
    private var cache: [URL: UIImage] = [:]
    
    // Actor methods execute serially, preventing concurrent mutations
    func cached(for url: URL) -> UIImage? {
        return cache[url]
    }
    
    func store(_ image: UIImage, for url: URL) {
        cache[url] = image
    }
}

class ImageLoader {
    private let cache = ImageCache()
    private let session = URLSession.shared
    
    // Async function can suspend without blocking underlying thread
    func loadImage(from url: URL) async throws -> UIImage {
        // Check cache on actor's serial executor
        if let cached = await cache.cached(for: url) {
            return cached
        }
        
        // Suspend while network fetch completes on background thread
        let (data, _) = try await session.data(from: url)
        
        // Image decode happens on background cooperative thread pool
        guard let image = UIImage(data: data) else {
            throw ImageError.invalidData
        }
        
        // Store in cache
        await cache.store(image, for: url)
        return image
    }
    
    // TaskGroup for parallel batch loading with automatic cancellation
    func loadImages(urls: [URL]) async throws -> [UIImage] {
        try await withThrowingTaskGroup(of: (Int, UIImage).self) { group in
            for (index, url) in urls.enumerated() {
                group.addTask {
                    let image = try await self.loadImage(from: url)
                    return (index, image)
                }
            }
            
            var results = [UIImage?](repeating: nil, count: urls.count)
            for try await (index, image) in group {
                results[index] = image
            }
            
            return results.compactMap { $0 }
        }
    }
}
```

The `actor` keyword defines a reference type that serializes access to its mutable state. When you await a call to an actor method, the runtime suspends the current task, enqueues the method invocation on the actor's serial executor, and resumes execution once the method completes. This eliminates data races on actor-isolated state without requiring explicit locks or dispatch queues. Actors integrate with Swift's global cooperative thread pool, which maintains a worker thread per CPU core and suspends tasks rather than blocking threads when awaiting async operations.

Kotlin coroutines provide similar structured concurrency on Android through suspending functions and coroutine scopes. The `suspend` modifier marks functions that can suspend execution at await points, and `CoroutineScope` defines structured lifetimes that automatically cancel child coroutines when the scope is canceled.

```kotlin
// Kotlin coroutines with structured concurrency and lifecycle awareness
class PostRepository(
    private val api: ApiService,
    private val database: PostDao
) {
    // Dispatcher determines execution thread
    suspend fun fetchPosts(): List<Post> = withContext(Dispatchers.IO) {
        // Suspends on IO dispatcher thread pool
        val response = api.getPosts()
        database.insertAll(response)
        response
    }
    
    suspend fun fetchPostsConcurrently(userIds: List<String>): List<Post> {
        return coroutineScope {
            // Creates structured child scope; parent waits for all children
            val deferredPosts = userIds.map { userId ->
                async(Dispatchers.IO) {
                    api.getUserPosts(userId)
                }
            }
            deferredPosts.awaitAll().flatten()
        }
    }
}

class PostViewModel(
    private val repository: PostRepository
) : ViewModel() {
    private val _posts = MutableStateFlow<List<Post>>(emptyList())
    val posts: StateFlow<List<Post>> = _posts.asStateFlow()
    
    // viewModelScope tied to ViewModel lifecycle; auto-cancels on clear
    fun loadPosts() {
        viewModelScope.launch {
            try {
                _posts.value = repository.fetchPosts()
            } catch (e: CancellationException) {
                // Coroutine was cancelled, no action needed
                throw e
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    // Flow operators transform streams with automatic cancellation
    fun searchPosts(query: StateFlow<String>): Flow<List<Post>> {
        return query
            .debounce(300) // Debounce user input
            .distinctUntilChanged()
            .flatMapLatest { searchQuery ->
                flow {
                    emit(repository.search(searchQuery))
                }
            }
            .flowOn(Dispatchers.IO) // Execute upstream on IO dispatcher
    }
}
```

Dispatchers map coroutines to underlying thread pools. `Dispatchers.Main` uses the Android main `Looper` and executes only on the UI thread. `Dispatchers.IO` maintains a large thread pool sized for blocking I/O operations like network requests and disk access. `Dispatchers.Default` sizes its pool to CPU core count for CPU-bound work. You can create custom dispatchers wrapping existing `Executor` instances for specialized workloads.

The structured concurrency model ensures that when a parent coroutine scope cancels, all child coroutines cancel cooperatively. Suspending functions check cancellation state at suspension points and throw `CancellationException` to unwind the stack. This prevents leaking background work that continues executing after the originating UI component has been destroyed, a common source of crashes when background work attempts to access deallocated view references.

## 3. High-Performance Optimization & Failure Modes

Thread pool sizing directly impacts performance and power consumption. Undersized pools introduce queueing latency as work items wait for idle threads. Oversized pools waste memory on thread stacks—typically one megabyte per thread—and introduce context switching overhead as the kernel scheduler time-slices threads across cores. The optimal size depends on workload characteristics: I/O-bound work benefits from large pools since threads spend most of their time blocked on I/O, while CPU-bound work should size pools to match physical core counts to avoid over-subscription.

Heterogeneous multi-core architectures complicate thread pool optimization. Apple's A-series and M-series processors combine high-performance and efficiency cores with different clock speeds and power envelopes. Quality-of-service classes map to these core types: user-interactive work scheduled with `.userInitiated` QoS runs on performance cores, while background work with `.utility` or `.background` QoS runs on efficiency cores. Incorrectly classifying work can either waste battery by running background tasks on performance cores or introduce latency by running user-facing work on efficiency cores.

You can query the system's performance core count using `ProcessInfo`:

```swift
let performanceCoreCount = ProcessInfo.processInfo.performanceCoreCount
let efficiencyCoreCount = ProcessInfo.processInfo.processorCount - performanceCoreCount

// Size thread pool for CPU-bound work to performance cores
let cpuBoundPool = DispatchQueue(label: "cpu-bound", 
                                  attributes: .concurrent,
                                  qos: .userInitiated)
```

Android exposes similar information through `CpuFeatures` and allows you to set thread affinity using `ThreadUtils.setThreadPriority()` and native `sched_setaffinity()` calls, though direct core pinning is rarely beneficial and can conflict with the kernel scheduler's global view.

Main thread contention represents the most critical performance failure mode. Even if your background work completes quickly, contention on the main thread's message queue delays rendering. Common sources of main thread contention include excessive view layout passes triggered by rapid state updates, synchronous disk access through `NSUserDefaults` or `SharedPreferences`, and large JSON or Protobuf parsing on the main thread after network callbacks.

Instruments on iOS and Profiler on Android provide frame timing analysis that exposes main thread stalls. On iOS, the `os_signpost` API allows you to instrument critical paths:

```swift
import os.signpost

let log = OSLog(subsystem: "com.example.app", category: "rendering")

func renderComplexView() {
    let signpostID = OSSignpostID(log: log)
    os_signpost(.begin, log: log, name: "render", signpostID: signpostID)
    
    // Complex rendering logic
    performExpensiveLayout()
    
    os_signpost(.end, log: log, name: "render", signpostID: signpostID)
}
```

Instruments visualizes these signposts on a timeline aligned with frame rendering markers, exposing precisely which operations caused frame drops. Android's systrace provides similar capabilities through `Trace.beginSection()` and `Trace.endSection()` calls.

Priority inversion deadlocks occur when high-priority work blocks waiting for low-priority work that holds a required resource. Consider a scenario where the main thread acquires a lock on shared state, then a background thread with higher QoS than the lock holder attempts to acquire the same lock. Without priority inheritance, the background thread blocks indefinitely waiting for the main thread, which may be deprioritized because the scheduler views it as low-priority work. Grand Central Dispatch automatically applies priority inheritance when synchronizing through dispatch queues and barriers, but explicit `NSLock` or `pthread_mutex_t` locks require manual priority inheritance configuration:

```c
pthread_mutexattr_t attr;
pthread_mutexattr_init(&attr);
pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);

pthread_mutex_t mutex;
pthread_mutex_init(&mutex, &attr);
```

On Android, priority inversion is less common because the `Looper` message queue doesn't implement priority-based scheduling, but can still occur with explicit `ReentrantLock` instances shared across threads.

Lifecycle-related race conditions plague mobile applications because view controllers and activities have complex lifecycles that don't align with background work completion. A common pattern involves initiating network request in `viewDidLoad` and updating UI in the completion handler, but if the user navigates away before the request completes, the view controller may be deallocated while the network callback still holds a strong reference. The callback then attempts to access deallocated UI objects, triggering a crash.

The canonical solution uses weak reference captures:

```swift
class ProfileViewController: UIViewController {
    func loadProfile() {
        networkService.fetchProfile { [weak self] result in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                self.updateUI(with: result)
            }
        }
    }
}
```

Structured concurrency eliminates this entire class of bugs by tying task lifetimes to scope lifetimes. When a view controller deallocates, its associated `Task` or coroutine scope cancels automatically:

```swift
class ProfileViewController: UIViewController {
    private var loadTask: Task<Void, Never>?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        loadTask = Task {
            do {
                let profile = try await networkService.fetchProfile()
                updateUI(with: profile)
            } catch {
                if error is CancellationError {
                    // Task was cancelled, view controller likely deallocated
                    return
                }
                handleError(error)
            }
        }
    }
    
    deinit {
        loadTask?.cancel()
    }
}
```

Background execution limits on iOS enforce strict time budgets for work that continues after the app transitions to the background. Applications receive approximately thirty seconds of background execution time by default, after which the system suspends all threads. Long-running background work must use `beginBackgroundTask(withName:expirationHandler:)` to request additional time:

```swift
var backgroundTaskID: UIBackgroundTaskIdentifier = .invalid

func performCriticalUpload() {
    backgroundTaskID = UIApplication.shared.beginBackgroundTask(withName: "upload") {
        // Expiration handler called ~5 seconds before time limit
        // Clean up and end task gracefully
        cleanup()
        UIApplication.shared.endBackgroundTask(self.backgroundTaskID)
        self.backgroundTaskID = .invalid
    }
    
    uploadService.upload { result in
        // Upload completed
        UIApplication.shared.endBackgroundTask(self.backgroundTaskID)
        self.backgroundTaskID = .invalid
    }
}
```

Failing to end background tasks before expiration results in forced process termination. Monitoring `UIApplication.backgroundTimeRemaining` allows you to detect approaching deadlines and pause work that can resume later.

Android's background execution model differs significantly. Services can request foreground status with persistent notifications, granting unlimited execution time. WorkManager handles deferrable background work with constraints like network availability and charging state:

```kotlin
class UploadWorker(context: Context, params: WorkerParameters) 
    : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        val fileUri = inputData.getString(KEY_FILE_URI) ?: return Result.failure()
        
        return try {
            withContext(Dispatchers.IO) {
                uploadService.upload(Uri.parse(fileUri))
            }
            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) {
                Result.retry()
            } else {
                Result.failure()
            }
        }
    }
}

// Schedule work with constraints
val uploadRequest = OneTimeWorkRequestBuilder<UploadWorker>()
    .setInputData(workDataOf(KEY_FILE_URI to uri.toString()))
    .setConstraints(Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .build())
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 10, TimeUnit.SECONDS)
    .build()

WorkManager.getInstance(context).enqueue(uploadRequest)
```

WorkManager schedules work through JobScheduler on modern Android versions, batching tasks to minimize wakeups and optimize battery life. Work persists across process death and device reboots, making it suitable for critical background operations like analytics uploads or content synchronization.

Memory pressure during background execution compounds threading challenges. When the system experiences memory pressure, it sends warnings to the application before resorting to process termination. Canceling expensive background work and flushing caches in response to memory warnings prevents termination:

```swift
NotificationCenter.default.addObserver(
    forName: UIApplication.didReceiveMemoryWarningNotification,
    object: nil,
    queue: .main
) { _ in
    imageCache.removeAll()
    cancelNonCriticalBackgroundWork()
}
```

Profiling concurrent code requires tooling beyond traditional CPU profilers. Thread sanitizer detects data races by tracking memory accesses across threads and flagging unsynchronized concurrent writes. Enable it through scheme settings in Xcode or build configuration flags on Android:

```bash
# Android: Enable Thread Sanitizer in CMakeLists.txt
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=thread")
```

Thread sanitizer introduces significant runtime overhead—typically two-to-three times slowdown—and should only run in development builds. It detects races that may not manifest as visible bugs, flagging potential issues before they cause production crashes.

Lock-free algorithms provide race-free synchronization without mutual exclusion, but require deep understanding of memory ordering and atomic operations. Mobile processors implement relaxed memory models where reads and writes can be reordered by both the compiler and CPU unless explicit barriers enforce ordering. C11 and C++11 atomics expose memory ordering through `memory_order` parameters:

```c
#include <stdatomic.h>

typedef struct {
    atomic_int ref_count;
    void *data;
} shared_object_t;

void retain(shared_object_t *obj) {
    // Relaxed ordering sufficient for increment
    atomic_fetch_add_explicit(&obj->ref_count, 1, memory_order_relaxed);
}

void release(shared_object_t *obj) {
    // Acquire ordering ensures prior writes visible before deallocating
    if (atomic_fetch_sub_explicit(&obj->ref_count, 1, memory_order_acquire) == 1) {
        free(obj->data);
        free(obj);
    }
}
```

Swift's atomic primitives landed in Swift 5.9 through the Atomics package, providing similar capabilities:

```swift
import Atomics

class RefCounted {
    let refCount = ManagedAtomic<Int>(1)
    
    func retain() {
        refCount.wrappingIncrement(ordering: .relaxed)
    }
    
    func release() {
        if refCount.wrappingDecrementThenLoad(ordering: .acquiring) == 0 {
            destroy()
        }
    }
}
```

The performance benefit of lock-free algorithms is context-dependent. On uncontended paths, atomics eliminate kernel transitions required by locks, but under high contention, repeated compare-and-swap retries can degrade into busy-waiting that wastes CPU cycles.

Production threading models synthesize these primitives into coherent patterns: dispatch work to quality-of-service-appropriate queues, tie task lifetimes to component lifecycles through structured concurrency, instrument critical paths with signposts, detect races with sanitizers, and handle background execution limits through explicit task management. These patterns compose into robust concurrent systems that maintain frame rate, respect power budgets, and survive aggressive process lifecycle management.
