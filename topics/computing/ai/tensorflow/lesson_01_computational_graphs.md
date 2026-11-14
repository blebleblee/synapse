# Lesson 1: Computational Graphs as Tensors in Motion

## 1. First-Principles Intuition & Invariants

Every modern deep learning framework is, at its core, a machine for computing derivatives at scale. This is not an incidental feature — it is the entire purpose of the system. To train a neural network is to solve an optimization problem in a parameter space that may contain hundreds of billions of dimensions, and the only tractable path through that space is gradient descent. Before TensorFlow can train anything, it must first be a system that can answer one fundamental question with mechanical precision: given a scalar loss value that is the product of a long chain of composed mathematical operations, what is the partial derivative of that loss with respect to every trainable parameter in the graph? The computational graph is TensorFlow's answer to that question, and understanding it at the level of a systems architect — not merely as an abstract concept but as a concrete data structure with specific memory layout and execution semantics — is the prerequisite for everything that follows.

The intuition begins with function composition. Consider a function $f(x) = \sigma(Wx + b)$, where $\sigma$ is the sigmoid activation, $W$ is a weight matrix, and $b$ is a bias vector. A mathematician sees this as a single expression. TensorFlow sees it as a directed acyclic graph (DAG) where each node is an **operation** (MatMul, BiasAdd, Sigmoid) and each directed edge carries a **tensor** — a typed, shaped, densely-packed multi-dimensional array — from the output of one operation to the input of the next. The word "tensor" here is used in the engineering sense: a generalization of scalars (rank-0), vectors (rank-1), and matrices (rank-2) to arbitrary rank, with a specific dtype and a device-resident memory buffer. The graph's topology encodes the data dependency structure of the computation, and that topology is precisely what enables automatic differentiation: by traversing the graph in reverse (backward pass), TensorFlow can apply the chain rule at each node to propagate gradients from the loss back to every leaf parameter.

This insight predates TensorFlow. The lineage runs through Theano (2010), which pioneered the concept of a symbolic computation graph compiled to efficient C/CUDA code, through Torch (2011) and its tensor library, through early TensorFlow 1.x (2015), which adopted a **static graph** (define-then-run) model, and finally to TensorFlow 2.x (2019), which made **eager execution** the default while preserving the ability to compile static graphs via `tf.function`. Understanding why both models exist — and what each costs and buys at the systems level — is not academic history. It is the mechanical knowledge you need to make correct architectural decisions about when to compile a graph and when not to.

### The Two Execution Models and Their Invariants

In TensorFlow 1.x, every computation was described symbolically before any data flowed through it. You constructed a graph as a data structure — a `tf.Graph` object containing `tf.Operation` nodes and `tf.Tensor` edge descriptors — and then executed it by feeding concrete `numpy` arrays into a `tf.Session`. The session managed the runtime: it determined which device (CPU, GPU, TPU) each operation ran on, allocated memory for intermediate tensors, dispatched kernel launches, and returned numpy arrays to Python. The separation between graph construction and graph execution was absolute. This model's invariant is **deferred execution with global graph state**: operations built outside a session context are purely symbolic; they produce no numerical output and consume no device memory until a session runs them.

The practical consequence of this model was that TensorFlow 1.x graphs were portable, serializable, and highly optimizable. The runtime could apply graph-level transformations — constant folding, operation fusion, dead node elimination, layout optimization — before a single kernel launched. A graph saved to a `SavedModel` or `GraphDef` protobuf was a complete, self-contained description of the computation, independent of the Python process that generated it. Production deployment was therefore a matter of deserializing the graph and running it in a lightweight C++ runtime with no Python dependency. This is an enormous systems advantage for serving at scale, and it remains the model that TensorFlow Serving, TensorFlow Lite, and TensorFlow.js use internally.

TensorFlow 2.x inverted the default. Eager execution means that every operation executes immediately when called, returning a concrete `EagerTensor` with a populated value buffer rather than a symbolic handle. This makes the interactive development loop vastly more productive: you can inspect intermediate values, use standard Python control flow (`if`, `for`, `while`) without wrapping it in `tf.cond` or `tf.while_loop`, and get readable Python tracebacks that point to the actual offending line of code. The invariant of eager mode is **immediate execution with Python-level control flow**: every `tf.matmul`, every `tf.nn.relu`, every arithmetic operation on a `tf.Tensor` triggers a synchronous dispatch to the appropriate device kernel and returns a filled tensor. The graph is implicit — it exists in the Python call stack — but it is never materialized as a persistent data structure unless you explicitly request it.

The cost is real. Pure eager execution cannot perform graph-level optimizations. Each Python function call crossing the eager runtime boundary carries interpreter overhead. Control flow and data flow are entangled in the Python interpreter, so the runtime cannot see the structure of a loop across multiple calls. For research and debugging these costs are acceptable. For production inference at thousands of requests per second, they are not. This is why `tf.function` exists: it bridges both worlds.

### `tf.function` as a Tracing JIT Compiler

The decorator `tf.function` turns a Python function into a TensorFlow **ConcreteFunction** by **tracing** it. The first time a `tf.function`-decorated callable is invoked with a given input signature (a combination of dtypes and shapes), TensorFlow executes the Python function body in a special tracing context. In this context, all `tf.` operations do not execute eagerly — they record themselves into a `FuncGraph`, which is a `tf.Graph` subclass scoped to that function. Python arithmetic on `tf.Tensor` objects is similarly captured. The resulting `FuncGraph` is then optimized by Grappler (TensorFlow's graph optimization system), potentially XLA-compiled, and cached. Subsequent calls with matching signatures dispatch directly to the compiled artifact, completely bypassing the Python interpreter.

The critical invariant to internalize is this: **Python code runs at trace time; TensorFlow ops run at call time.** This distinction is the source of a large class of subtle bugs. A Python `print()` inside a `tf.function` will execute exactly once during tracing, not on every forward pass. A Python `if condition` where `condition` is a Python boolean will bake the branch taken at trace time permanently into the graph; if you want a data-dependent conditional — one that takes different branches based on the value of a tensor — you must use `tf.cond`. Similarly, a Python `for i in range(n)` will unroll the loop at trace time, generating `n` copies of the body in the graph. `tf.while_loop` is required for loops whose trip count depends on tensor values known only at runtime.

Retracing — the creation of a new `ConcreteFunction` for a new input signature — is expensive. For a large model, a single trace can take several seconds and allocate significant memory. If you inadvertently call a `tf.function` with Python integers as arguments that change on every call (instead of using `tf.constant` or specifying `input_signature`), you will retrace on every call and negate all performance benefits. This failure mode is covered in depth in Section 3.

---

## 2. Core Architecture & Mechanics

### The Tensor: Memory Layout and Type System

A `tf.Tensor` is a handle to a typed, shaped, device-resident buffer. Its dtype encodes both the numeric type (`float32`, `float16`, `int32`, `bfloat16`) and its size in bytes, which directly determines memory bandwidth requirements during computation. Its shape is a `TensorShape` — an ordered tuple of dimensions, each of which may be statically known at graph construction time (e.g., `[32, 784]`) or dynamic (represented as `None`). The rank is the length of this tuple.

Under eager execution, a `tf.EagerTensor` holds a reference to a `tensorflow::Tensor` object in the C++ runtime, which in turn wraps a `tensorflow::TensorBuffer` — a reference-counted heap allocation aligned to satisfy SIMD requirements (typically 64-byte cache-line alignment). When a tensor lives on a GPU, this buffer is a CUDA device allocation managed by the TF memory allocator, which maintains a pool of free blocks to avoid the latency of `cudaMalloc` on the critical path. Copy between host and device is explicit, triggered by operations that require cross-device data movement, and profiled as `MemcpyH2D` / `MemcpyD2H` events in the TensorBoard trace viewer.

The following program demonstrates the core tensor mechanics a practitioner must be fluent with before reasoning about graphs:

```python
import tensorflow as tf
import numpy as np

# Rank-0 through rank-3 tensors with explicit dtypes
scalar   = tf.constant(3.14159, dtype=tf.float32)          # shape: ()
vector   = tf.constant([1.0, 2.0, 3.0], dtype=tf.float32)  # shape: (3,)
matrix   = tf.constant(np.eye(4, dtype=np.float32))        # shape: (4, 4)
batch    = tf.zeros([32, 224, 224, 3], dtype=tf.float16)   # shape: (32, 224, 224, 3)

# Tensor metadata
print(scalar.dtype)        # tf.float32
print(batch.shape)         # (32, 224, 224, 3)
print(batch.device)        # /job:localhost/replica:0/task:0/device:GPU:0  (if available)
print(batch.numpy().nbytes)  # 32 * 224 * 224 * 3 * 2 = 9,633,792 bytes (~9.2 MB)

# Shape manipulation — no data copy occurs; a new view is produced
reshaped = tf.reshape(batch, [32, -1, 3])  # (32, 50176, 3)
transposed = tf.transpose(matrix, perm=[1, 0])

# dtype casting — allocates a new buffer on the same device
promoted = tf.cast(batch, tf.float32)      # fp16 -> fp32 doubles memory footprint
```

### The FuncGraph: Operation Nodes and Edge Tensors

When `tf.function` traces a Python callable, it populates a `FuncGraph` with `tf.Operation` objects. Each operation has a name (e.g., `"MatMul:0"`), a list of input `tf.Tensor` objects (output edges from upstream ops), a list of output `tf.Tensor` descriptors (its own output edges), a set of attributes (compile-time constants like `transpose_a=False`), and a device placement (either explicitly assigned or resolved by the placer). The graph is a DAG: tensors flow from source operations (variables, placeholders, constants) through transform operations (MatMul, Add, ReLU) to sink operations (loss computation, metric updates).

The following ASCII diagram represents a single-layer forward pass through a linear transformation followed by softmax:

```
 [Input Placeholder]       [Weight Variable]    [Bias Variable]
       x: (B, 784)              W: (784, 128)       b: (128,)
           |                         |                   |
           +-----------> MatMul <----+                   |
                           |                             |
                           +-----------> BiasAdd <-------+
                                            |
                                            v
                                          ReLU
                                            |
                                   [Weight2: (128,10)]  [Bias2: (10,)]
                                            |                |
                                            +---> MatMul <---+
                                                     |
                                                   Softmax
                                                     |
                                             [Loss: SparseCategoricalCE]
                                                     |
                                             scalar loss tensor
```

Each arrow in this diagram is a `tf.Tensor` edge — a typed, shaped buffer that is allocated exactly once per execution by the runtime memory allocator and freed (returned to the pool) as soon as the last downstream consumer of that tensor has completed. This is the **BFS-ordered tensor lifetime management** that the runtime uses to minimize peak device memory usage during a forward pass.

### Tape-Based Automatic Differentiation

The backward pass — gradient computation — is implemented in TensorFlow 2.x via `tf.GradientTape`. The tape is a context manager that records the forward pass operations in the order they execute, building a gradient tape trace. When you call `tape.gradient(loss, variables)`, it traverses this trace in reverse, calling the registered gradient function for each operation and accumulating partial derivatives via the chain rule.

The design is fundamentally **reverse-mode automatic differentiation** (reverse-mode AD, also called backpropagation). For a function $f: \mathbb{R}^n \rightarrow \mathbb{R}$ — which every training loss is, mapping a high-dimensional parameter space to a scalar — reverse-mode AD computes the full gradient $\nabla f$ in a single backward pass with $O(1)$ overhead relative to the forward pass, regardless of the number of input dimensions $n$. This is why reverse-mode AD is the only practical choice for neural network training: forward-mode AD would require $n$ separate passes for $n$ parameters.

Each operation in TensorFlow registers both a **forward kernel** and a **gradient function** (sometimes called the "op gradient" or "vjp" — vector-Jacobian product). The gradient function for `MatMul(A, B) -> C` is defined as: given the upstream gradient $\partial L / \partial C$, compute $\partial L / \partial A = (\partial L / \partial C) \cdot B^T$ and $\partial L / \partial B = A^T \cdot (\partial L / \partial C)$. The tape orchestrates these calls automatically. The intermediate activations saved during the forward pass for use in the backward pass are called the **tape residuals**, and they represent a significant portion of training memory usage, particularly for large sequence models.

```python
import tensorflow as tf

# A simple two-layer network forward pass with explicit gradient tape
W1 = tf.Variable(tf.random.normal([784, 256], stddev=0.02), name="W1")
b1 = tf.Variable(tf.zeros([256]), name="b1")
W2 = tf.Variable(tf.random.normal([256, 10], stddev=0.02), name="W2")
b2 = tf.Variable(tf.zeros([10]), name="b2")

@tf.function(input_signature=[
    tf.TensorSpec(shape=[None, 784], dtype=tf.float32),
    tf.TensorSpec(shape=[None],      dtype=tf.int32),
])
def train_step(x_batch, y_batch):
    with tf.GradientTape() as tape:
        # Forward pass — all ops are recorded by the tape
        h1     = tf.nn.relu(tf.matmul(x_batch, W1) + b1)   # (B, 256)
        logits = tf.matmul(h1, W2) + b2                     # (B, 10)
        loss   = tf.reduce_mean(
            tf.nn.sparse_softmax_cross_entropy_with_logits(
                labels=y_batch, logits=logits
            )
        )

    # Backward pass — reverse traversal of the recorded tape
    gradients = tape.gradient(loss, [W1, b1, W2, b2])

    # Gradient clipping to prevent exploding gradients
    clipped, global_norm = tf.clip_by_global_norm(gradients, clip_norm=1.0)

    return loss, clipped, global_norm


# Synthetic batch
x = tf.random.normal([64, 784])
y = tf.random.uniform([64], minval=0, maxval=10, dtype=tf.int32)

loss_val, grads, norm = train_step(x, y)
print(f"Loss: {loss_val.numpy():.4f} | Gradient norm: {norm.numpy():.4f}")
print(f"∇W1 shape: {grads[0].shape} | ∇W2 shape: {grads[2].shape}")
```

The `input_signature` argument to `@tf.function` is essential in production code. It tells the tracing system the exact dtype and shape contract of the inputs, preventing retracing when the batch size changes (the `None` dimension allows variable batch sizes under a single trace). Without it, every new Python integer or new batch size triggers an expensive retrace.

### Gradient Flow Through Non-Differentiable Operations

Not every operation is smooth. `tf.argmax`, `tf.round`, and boolean masks are not differentiable. When a tape encounters a non-differentiable node during backward traversal, it returns `None` for that gradient. If you are using custom discrete operations — say, a straight-through estimator for binary neural networks — you must implement a custom gradient using `@tf.custom_gradient`:

```python
import tensorflow as tf

@tf.custom_gradient
def straight_through_round(x):
    """
    Forward: rounds x to nearest integer.
    Backward: passes gradient through as if the op were identity (STE).
    This is the Straight-Through Estimator, used in quantization-aware training.
    """
    def grad(upstream):
        # Gradient of identity is 1; multiply by upstream (chain rule)
        return upstream

    return tf.round(x), grad


# Verify gradient flows through the otherwise-zero-gradient round op
x = tf.Variable([0.3, 0.7, 1.2, 1.9], dtype=tf.float32)
with tf.GradientTape() as tape:
    y = straight_through_round(x)
    loss = tf.reduce_sum(y)

grad = tape.gradient(loss, x)
print(f"Input:    {x.numpy()}")
print(f"Rounded:  {y.numpy()}")
print(f"Gradient: {grad.numpy()}")  # [1. 1. 1. 1.] — straight-through
```

### Grappler: The Graph Optimization Pass

Before a traced `FuncGraph` runs for the first time, TensorFlow's Grappler optimization system applies a sequence of graph rewrites. The most consequential are **constant folding** (sub-graphs with no variable inputs are evaluated at trace time and replaced with constant nodes, eliminating runtime computation), **op fusion** (adjacent element-wise operations like `BiasAdd + ReLU` are merged into a single fused kernel, reducing kernel launch overhead and improving cache locality), **layout optimization** (tensor dimension orders are transformed from NHWC to NCHW where hardware prefers it, without changing semantics), and **remapping** (common sub-graph patterns like `Conv2D + BiasAdd + Activation` are replaced by cuDNN-backed fused implementations).

Grappler operates on the `GraphDef` protobuf representation, applying each optimizer in a configurable pipeline. You can inspect the pre- and post-optimization graphs programmatically, and you can control the Grappler configuration via `tf.config.optimizer.set_jit(True)` (which enables the XLA JIT compiler as a Grappler post-pass) or by constructing a `tf.ConfigProto` with explicit `graph_options.optimizer_options` fields. For most practitioners, the default Grappler configuration is correct — the important thing is knowing that it exists, what it does, and that it is the reason a `tf.function`-compiled model is significantly faster than its eager equivalent without any manual code changes.

---

## 3. High-Performance Optimization & Failure Modes

### Identifying and Eliminating Retracing

The single most common performance regression in TensorFlow 2.x production code is unintended retracing. A retrace is triggered whenever `tf.function` sees a new **trace cache key**, which is determined by the dtypes, shapes, and Python-level values of all inputs. Calling a `tf.function` with a Python `int` instead of a `tf.Tensor` causes each distinct integer value to become its own trace cache key, because Python scalars are treated as compile-time constants that may be baked into the graph. The fix is consistent: always pass data as tensors, and always specify `input_signature` for functions that will be called from a training loop.

```python
import tensorflow as tf

@tf.function
def bad_fn(x, n_steps):
    # n_steps is a Python int — a new trace occurs for every distinct value
    result = x
    for _ in range(n_steps):
        result = result * 2.0
    return result

@tf.function(input_signature=[
    tf.TensorSpec(shape=[None], dtype=tf.float32),
    tf.TensorSpec(shape=(),     dtype=tf.int32),
])
def good_fn(x, n_steps):
    # n_steps is a tf.Tensor — tf.while_loop handles it at runtime, single trace
    result = x
    result = tf.while_loop(
        cond=lambda i, r: i < n_steps,
        body=lambda i, r: (i + 1, r * 2.0),
        loop_vars=[tf.constant(0, dtype=tf.int32), result]
    )[1]
    return result
```

You can instrument retrace events by enabling the `tf.debugging.set_log_device_placement(True)` flag and monitoring Python function call patterns, or by wrapping your `tf.function` body with:

```python
@tf.function
def monitored_fn(x):
    tf.print("Tracing!", output_stream="file://trace_log.txt")
    return x * 2.0
```

The `tf.print` op is recorded into the graph and executes at graph runtime — not at trace time. A Python `print()` in the same location would fire only during tracing. When you see `tf.print` output on the first call but not subsequent identical calls, the graph is caching correctly. If `tf.print` fires on every call, you are retracing.

### Memory Pressure from Tape Residuals

During a `tf.GradientTape` forward pass, TensorFlow retains all intermediate tensors needed to compute gradients. For a transformer with $L$ layers, this means retaining the query/key/value projections, attention weights, and FFN activations for all $L$ layers simultaneously. At batch size 32 with sequence length 512 and hidden dimension 1024, each activation tensor is `32 × 512 × 1024 × 4 bytes ≈ 67 MB`. Retaining activations for 24 transformer layers simultaneously uses roughly 1.6 GB of device memory before accounting for parameters or optimizer states.

**Gradient checkpointing** (also called activation recomputation) trades compute for memory by releasing intermediate activations after the forward pass and recomputing them during the backward pass as needed. TensorFlow implements this via `tf.recompute_grad`:

```python
import tensorflow as tf

class TransformerBlock(tf.keras.layers.Layer):
    def __init__(self, d_model, num_heads, dff, **kwargs):
        super().__init__(**kwargs)
        self.attn  = tf.keras.layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=d_model // num_heads
        )
        self.ffn1  = tf.keras.layers.Dense(dff, activation="relu")
        self.ffn2  = tf.keras.layers.Dense(d_model)
        self.norm1 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
        self.norm2 = tf.keras.layers.LayerNormalization(epsilon=1e-6)

    def call(self, x, training=False):
        attn_out = self.attn(x, x, training=training)
        x        = self.norm1(x + attn_out)
        ffn_out  = self.ffn2(self.ffn1(x))
        return self.norm2(x + ffn_out)


def build_checkpointed_model(d_model=512, num_heads=8, dff=2048, num_layers=12):
    inputs = tf.keras.Input(shape=(None, d_model))
    x      = inputs
    for _ in range(num_layers):
        block   = TransformerBlock(d_model, num_heads, dff)
        # tf.recompute_grad wraps the layer's call so that its activations
        # are discarded after the forward pass and recomputed during backward.
        # This reduces peak activation memory from O(L) to O(sqrt(L)) with
        # a ~33% compute overhead.
        x = tf.recompute_grad(block)(x)
    return tf.keras.Model(inputs=inputs, outputs=x)
```

The `tf.recompute_grad` wrapper stores only the layer's inputs rather than its activations. During the backward pass, it re-executes the forward computation using the stored inputs to reconstruct the activations needed for the gradient computation. For a 12-layer model, this reduces activation memory by approximately 10× at the cost of one additional forward pass per layer during backpropagation.

### Mixed Precision and dtype Discipline

NVIDIA Volta and later architectures (A100, H100) contain Tensor Core hardware units that execute matrix multiplications on `float16` operands 8–16× faster than `float32` on CUDA cores. Enabling mixed-precision training captures this throughput gain while maintaining numerical stability by keeping the master weights and loss scaling in `float32`:

```python
import tensorflow as tf

# Configure mixed precision globally before constructing any layers
policy = tf.keras.mixed_precision.Policy("mixed_float16")
tf.keras.mixed_precision.set_global_policy(policy)

# Verify the compute and variable dtypes
print(policy.compute_dtype)   # float16
print(policy.variable_dtype)  # float32

# Build a model — Keras automatically casts compute to fp16, stores weights in fp32
inputs  = tf.keras.Input(shape=(784,))
hidden  = tf.keras.layers.Dense(256, activation="relu")(inputs)
outputs = tf.keras.layers.Dense(10)(hidden)
model   = tf.keras.Model(inputs=inputs, outputs=outputs)

# The output of the final Dense layer is fp16; softmax must be cast to fp32
# before the loss to avoid numerical underflow in the CE computation
x       = tf.keras.Input(shape=(784,))
h       = tf.keras.layers.Dense(256, activation="relu")(x)
logits  = tf.keras.layers.Dense(10)(h)
# Cast output to float32 for numerically stable loss
logits_fp32 = tf.keras.layers.Activation("linear", dtype="float32")(logits)
mp_model    = tf.keras.Model(inputs=x, outputs=logits_fp32)

# LossScaleOptimizer wraps any optimizer and applies dynamic loss scaling
# to prevent fp16 gradient underflow (gradients < 2^-14 flush to zero in fp16)
base_optimizer  = tf.keras.optimizers.Adam(learning_rate=1e-3)
scaled_optimizer = tf.keras.mixed_precision.LossScaleOptimizer(base_optimizer)
```

The `LossScaleOptimizer` dynamically adjusts a loss scale factor (initially 2^15) to keep fp16 gradients in the representable range. When a gradient overflow is detected (NaN or Inf in any gradient tensor), the optimizer skips the weight update and reduces the scale factor by half. When updates proceed without overflow for a configurable number of consecutive steps (default 2000), the scale factor doubles. This dynamic scaling converges to the largest stable scale for the specific model and batch size, maximizing precision while preventing overflow.

### Profiling the Graph with TensorBoard Trace View

Optimization without measurement is speculation. TensorFlow provides a first-class profiling API that integrates directly with TensorBoard's Trace Viewer, which renders a Perfetto-format trace showing each op kernel, memory allocation, and device-host synchronization event as a timeline:

```python
import tensorflow as tf
import datetime

# Synthetic model and data for profiling demonstration
model     = tf.keras.Sequential([
    tf.keras.layers.Dense(512, activation="relu", input_shape=(784,)),
    tf.keras.layers.Dense(256, activation="relu"),
    tf.keras.layers.Dense(10),
])
optimizer = tf.keras.optimizers.Adam()
loss_fn   = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
x_batch   = tf.random.normal([128, 784])
y_batch   = tf.random.uniform([128], 0, 10, dtype=tf.int32)

@tf.function
def profiled_step(x, y):
    with tf.GradientTape() as tape:
        preds = model(x, training=True)
        loss  = loss_fn(y, preds)
    grads = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))
    return loss

log_dir = f"logs/profile/{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

# Warm up — the first call traces the function; profile after warmup
for _ in range(5):
    profiled_step(x_batch, y_batch)

# Profile steps 10–15 of a training run
tf.profiler.experimental.start(log_dir)
for step in range(20):
    with tf.profiler.experimental.Trace("train_step", step_num=step, _r=1):
        loss = profiled_step(x_batch, y_batch)
tf.profiler.experimental.stop()

print(f"TensorBoard trace written to: {log_dir}")
print("Run: tensorboard --logdir logs/profile")
```

In the resulting TensorBoard trace, look for three failure patterns. **Device idle gaps** between consecutive op kernels indicate either excessive host-device synchronization (often caused by `tensor.numpy()` calls inside a `tf.function`, which force eager evaluation) or a CPU bottleneck in the data pipeline starving the GPU. **Small kernel launches** — ops lasting less than 10 microseconds — suggest that the model has too many small operations that should be fused; Grappler often handles this, but custom ops or non-standard layer architectures can defeat fusion. **Memory copy events** that consume a significant fraction of step time indicate that tensors are living on the wrong device, or that the input pipeline is not prefetching — both of which are solved by moving data preprocessing into `tf.data.Dataset` with `.prefetch(tf.data.AUTOTUNE)`.

The computational graph is not an abstraction that sits above your hardware. It is a precisely specified data structure that the runtime translates into a sequence of kernel launches, memory allocations, and synchronization primitives on real silicon. Every decision you make about graph construction — how you structure your `tf.function` boundaries, how you manage dtype, how you configure the tape — has a deterministic consequence on memory bandwidth, kernel utilization, and training throughput. Working at this level of mechanical clarity is what separates engineers who tune models from engineers who understand them.
