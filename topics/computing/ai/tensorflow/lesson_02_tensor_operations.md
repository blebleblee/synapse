# Lesson 2: Tensor Algebra, Broadcasting, and Shape Manipulation

## 1. First-Principles Intuition & Invariants

At the foundation of every modern deep learning system lies a single unifying abstraction: the tensor. While neural network architectures may appear as elaborate computational graphs with layers, activations, and loss functions, the runtime execution model collapses entirely into sequences of tensor operations—multidimensional array transformations that exploit parallelism across data and computation. TensorFlow, like all production machine learning frameworks, exposes this computational substrate through a rank-polymorphic algebra where operations automatically generalize across dimensional hierarchies, enabling practitioners to write model code that seamlessly scales from single training examples to distributed mini-batches across accelerator clusters.

Understanding tensor semantics begins with recognizing that a tensor is fundamentally a contiguous memory buffer paired with a shape descriptor and data type specification. The shape, represented as an integer tuple, defines the extent along each axis—a rank-0 tensor (scalar) possesses an empty shape `()`, a rank-1 tensor (vector) carries shape `(n,)`, a rank-2 tensor (matrix) bears shape `(m, n)`, and higher-rank tensors extend this pattern arbitrarily. This shape metadata governs memory layout through stride calculation: TensorFlow defaults to row-major (C-contiguous) ordering where the rightmost index varies fastest in linear memory, though certain operations may produce tensors with non-contiguous views that delay physical copying until absolutely necessary.

The rank-polymorphic nature of tensor operations introduces a critical design principle: broadcasting. Rather than requiring exact shape matches for element-wise operations, TensorFlow implements a set of automatic shape alignment rules that extend operands along dimensions of size one, or prepend singleton dimensions to lower-rank tensors. This mechanism, inherited from NumPy's semantics but refined for distributed execution, transforms `(3, 1) + (4,)` into a valid operation producing shape `(3, 4)` by implicitly replicating data along broadcast axes. The broadcasting protocol follows three invariant rules: dimensions are aligned from right to left, each pair of dimensions must either match exactly or one must equal one, and missing dimensions are treated as trailing ones. This design choice profoundly impacts both API ergonomics and runtime performance—broadcasting eliminates the need for explicit tiling operations in user code, but it also introduces invisible memory amplification that can trigger out-of-memory failures when careless broadcasting produces unexpectedly large intermediate tensors.

The mathematical semantics of tensor operations rest on a foundation of element-wise primitives and structured reductions. Element-wise operations—addition, multiplication, exponentiation, and transcendental functions—map directly to SIMD vector instructions on CPUs or massively parallel thread blocks on GPUs, achieving peak throughput when operands exhibit spatial locality and aligned memory access patterns. Reductions, by contrast, collapse one or more axes through associative operations like summation, maximum selection, or logical conjunction, producing lower-rank output tensors. The interaction between broadcasting and reductions forms the computational backbone of neural network training: forward propagation broadcasts learned parameters across batch dimensions, while backward propagation reduces gradients from per-example losses back to parameter-shaped updates.

Shape manipulation operations—reshaping, transposition, expansion, and squeezing—provide the structural glue that connects layers in a computational graph. Unlike element-wise operations that preserve shape, these transformations reinterpret the dimensional hierarchy of existing data or explicitly copy memory into new layouts. A reshape operation reinterprets the same linear memory buffer under a new shape tuple, requiring only that the total element count remains invariant; this zero-copy transformation executes in constant time but imposes strict stride compatibility constraints. Transposition, conversely, reorders axes by permuting the shape tuple and adjusting strides accordingly, often deferring the physical memory rearrangement until a subsequent operation forces materialization. Modern TensorFlow leverages lazy evaluation and graph-level optimization passes to fuse sequences of shape manipulations, eliminating redundant copies and minimizing data movement overhead.

The practical implications of these algebraic primitives extend far beyond mathematical elegance. In production training pipelines, the overwhelming majority of numerical instability, performance degradation, and silent correctness bugs trace back to shape mismatches, unintended broadcasting, or naive reduction axes. A misplaced `axis=-1` in a softmax operation transforms a per-token probability distribution into a meaningless per-batch aggregate. An accidental broadcast during gradient accumulation silently corrupts parameter updates by replicating gradients across phantom dimensions. A reshape that violates memory contiguity forces an unexpected copy, fragmenting GPU memory and triggering allocation failures in long-running training jobs. Mastery of tensor algebra therefore demands not just conceptual understanding but operational vigilance—the ability to inspect shapes at every graph node, reason about memory layout transformations, and predict the physical execution consequences of high-level API calls.

## 2. Core Architecture & Mechanics

TensorFlow represents tensors as instances of `tf.Tensor`, an immutable handle to a typed multidimensional array stored in device memory. Each tensor carries three essential attributes: `shape`, a `tf.TensorShape` object encoding dimensional extents; `dtype`, a `tf.DType` specifying element type (typically `float32`, `int32`, or `bool`); and `device`, a placement specification identifying the physical memory location (CPU, GPU, or TPU). The tensor itself does not directly contain data—it functions as a symbolic reference within a computational graph, with actual buffer allocation and population deferred until graph execution. This lazy evaluation model enables TensorFlow's optimizer to perform global transformations: constant folding eliminates compile-time-known subgraphs, common subexpression elimination deduplicates redundant operations, and layout optimization inserts transpositions to maximize hardware efficiency.

The shape system in TensorFlow supports both static and dynamic dimensions. Static shapes, known at graph construction time, enable compile-time verification and optimized kernel selection—a convolution operation can specialize its algorithm choice based on known spatial dimensions. Dynamic shapes, represented by `None` entries in the shape tuple, accommodate variable-length sequences or batch sizes determined at runtime, at the cost of deferring kernel specialization and disabling certain graph optimizations. The `tf.shape()` operation bridges this gap by computing the runtime shape as a rank-1 integer tensor, enabling dynamic shape-dependent control flow through `tf.cond()` and `tf.while_loop()` constructs.

Broadcasting mechanics operate through a two-phase protocol: shape compatibility checking followed by implicit stride manipulation. When TensorFlow encounters an element-wise binary operation, it first aligns operand shapes by prepending ones to the lower-rank tensor, then walks backward through dimension pairs. For each pair `(d1, d2)`, the operation succeeds if `d1 == d2`, `d1 == 1`, or `d2 == 1`, with the output dimension taking the maximum. If `d1 == 1` and `d2 > 1`, the runtime conceptually tiles the first operand by repeating data `d2` times along that axis—though the actual implementation reuses the same memory addresses across iterations, achieving zero-copy broadcasting. This stride manipulation, visible through the internal `strides` attribute on eager tensors, transforms a shape `(3, 1, 5)` tensor into an effective `(3, 4, 5)` broadcast view by setting the middle stride to zero, causing index increments along that axis to read the same memory location repeatedly.

```
Original tensor: shape (3, 1, 5), strides (5, 5, 1) bytes
Memory layout: [a₀ a₁ a₂ a₃ a₄] [b₀ b₁ b₂ b₃ b₄] [c₀ c₁ c₂ c₃ c₄]

Broadcast view: shape (3, 4, 5), strides (5, 0, 1) bytes
Logical access: [a₀ a₁ a₂ a₃ a₄] [a₀ a₁ a₂ a₃ a₄] [a₀ a₁ a₂ a₃ a₄] [a₀ a₁ a₂ a₃ a₄]
                [b₀ b₁ b₂ b₃ b₄] [b₀ b₁ b₂ b₃ b₄] [b₀ b₁ b₂ b₃ b₄] [b₀ b₁ b₂ b₃ b₄]
                [c₀ c₁ c₂ c₃ c₄] [c₀ c₁ c₂ c₃ c₄] [c₀ c₁ c₂ c₃ c₄] [c₀ c₁ c₂ c₃ c₄]
Physical memory unchanged, stride[1] = 0 causes repeated reads
```

Reduction operations collapse dimensions through parallel tree aggregation on accelerators. A `tf.reduce_sum(x, axis=1)` operation on a GPU tensor partitions the reduction axis across thread blocks, with each block performing a local reduction into shared memory, followed by a cross-block reduction phase that writes final results to global memory. TensorFlow's XLA compiler optimizes reduction patterns by fusing sequences of reductions and element-wise operations into single GPU kernels, eliminating intermediate materialization. The `keepdims=True` parameter preserves reduced dimensions as size-one axes, maintaining rank for subsequent broadcasting—a critical pattern in numerically stable softmax implementations where per-row maximum subtraction requires broadcasting the reduced maximum back across the original axis.

Shape manipulation operations expose the tension between logical views and physical layout. The `tf.reshape(x, new_shape)` operation validates that `tf.size(x) == tf.reduce_prod(new_shape)`, then returns a tensor sharing the underlying buffer but reinterpreted under the new shape. This succeeds only when the reshape preserves memory contiguity—specifically, when the transformation can be expressed purely through stride adjustment without reordering elements. Non-contiguous reshapes, such as reshaping a transposed matrix, trigger an implicit copy. The `tf.transpose(x, perm)` operation reorders axes according to the permutation vector `perm`, producing a view with permuted shape and strides; subsequent operations may force materialization depending on whether downstream kernels support strided access patterns. The `tf.expand_dims(x, axis)` and `tf.squeeze(x, axis)` operations insert and remove size-one dimensions respectively, enabling explicit control over broadcasting compatibility without memory movement.

```python
import tensorflow as tf

# Demonstrate broadcasting mechanics
a = tf.constant([[1.0, 2.0, 3.0]])  # shape (1, 3)
b = tf.constant([[1.0], [2.0]])     # shape (2, 1)

# Broadcasting produces (2, 3) output
c = a + b  # [[2, 3, 4], [3, 4, 5]]

# Explicit shape verification
tf.debugging.assert_equal(tf.shape(c), [2, 3])

# Reduction with keepdims for stable softmax
x = tf.constant([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])  # shape (2, 3)
x_max = tf.reduce_max(x, axis=1, keepdims=True)       # shape (2, 1)
x_shifted = x - x_max  # broadcasts to (2, 3), numerically stable
x_exp = tf.exp(x_shifted)
x_sum = tf.reduce_sum(x_exp, axis=1, keepdims=True)   # shape (2, 1)
softmax = x_exp / x_sum  # final broadcast division

# Reshape validation: total elements must match
original = tf.range(24, dtype=tf.float32)       # shape (24,)
reshaped = tf.reshape(original, [2, 3, 4])      # valid: 24 = 2*3*4
# tf.reshape(original, [2, 5, 3])  # runtime error: 24 ≠ 30

# Transpose produces non-contiguous view
matrix = tf.constant([[1, 2], [3, 4], [5, 6]])  # shape (3, 2)
transposed = tf.transpose(matrix)                # shape (2, 3), may defer copy
print(transposed)  # [[1, 3, 5], [2, 4, 6]]

# Explicit dimension manipulation
vector = tf.constant([1.0, 2.0, 3.0])           # shape (3,)
col_vector = tf.expand_dims(vector, axis=1)     # shape (3, 1)
row_vector = tf.expand_dims(vector, axis=0)     # shape (1, 3)
outer_product = col_vector * row_vector         # broadcasts to (3, 3)
```

Indexing and slicing operations extract subregions from tensors through multidimensional subscripting. Basic slicing with `tensor[start:stop:step]` syntax produces views sharing the original buffer, while advanced indexing with integer or boolean tensors triggers copies. The `tf.gather()` operation performs indexed selection along a specified axis, gathering elements according to an integer index tensor—a fundamental primitive for embedding lookups and attention mechanisms. The `tf.scatter_nd()` operation inverts this pattern, writing values into specified index locations within a zero-initialized output tensor. These gather-scatter pairs enable non-contiguous memory access patterns required for sparse operations, though they sacrifice the spatial locality that maximizes hardware throughput.

The interaction between eager execution and graph mode profoundly affects tensor manipulation semantics. In eager mode, every operation executes immediately and returns a concrete tensor with materialized values, enabling interactive debugging through Python print statements and NumPy interoperability via `.numpy()`. In graph mode, operations construct a deferred computational graph where tensors are symbolic placeholders, with actual execution postponed until `sess.run()` or function invocation under `@tf.function` decoration. This duality requires careful attention to shape inference: eager mode resolves shapes immediately through kernel execution, while graph mode relies on static shape propagation through registered shape functions. Operations with data-dependent output shapes—such as `tf.unique()` or `tf.where()`—necessarily produce partial shapes in graph mode, deferring full shape resolution to runtime.

## 3. High-Performance Optimization & Failure Modes

Production-grade tensor manipulation demands awareness of memory layout, computational intensity, and device placement constraints that determine whether a training loop saturates hardware throughput or stalls on data movement overhead. The single most impactful optimization involves minimizing host-device transfers: moving tensors between CPU and GPU memory incurs PCIe bandwidth limits (typically 16 GB/s on PCIe 4.0 x16), introducing millisecond-scale latencies that dwarf nanosecond-scale arithmetic. Effective TensorFlow programs construct entire forward and backward passes as device-resident computational graphs, crossing the host-device boundary only for final loss logging or checkpoint serialization. This principle extends to shape computation—invoking `tf.shape(x).numpy()` in a tight loop forces synchronization points that serialize GPU execution, while graph-mode shape inference propagates dimensions symbolically without runtime queries.

Broadcasting introduces invisible computational costs through memory bandwidth amplification. A broadcast operation that expands a shape `(1000,)` vector into a `(1000, 1000)` tensor for element-wise multiplication does not physically allocate 1 million elements, but the resulting operation still reads and writes that full 1 million element result. The memory traffic matches the broadcasted shape, not the compact source shape. This becomes pathological when nested broadcasting produces intermediate tensors with explosively large shapes—computing `(A + B) * C` where `A` is `(1000, 1, 1000)`, `B` is `(1, 1000, 1)`, and `C` is `(1, 1, 1000)` broadcasts to a `(1000, 1000, 1000)` intermediate consuming 4 GB for a single float32 operation. Profiling with TensorFlow's profiler reveals such cases through "memory high-water mark" spikes that occur during specific operations. The solution involves manual factorization: rewriting expressions to defer broadcasts until after reductions have collapsed dimensions, or introducing explicit reshapes that force compact computation before broadcast expansion.

Reduction axis specification demands rigorous verification to prevent silent correctness bugs. Consider a batch of image data with shape `(batch, height, width, channels)` where the goal is computing per-channel statistics. Reducing over `axis=(0, 1, 2)` correctly aggregates across batch and spatial dimensions, preserving the channel axis. Accidentally reducing over `axis=(1, 2, 3)` aggregates across spatial dimensions and channels while preserving batch, producing nonsensical per-batch statistics that contaminate normalization layers. The `keepdims=True` parameter provides shape self-documentation: a reduction that should preserve rank for broadcasting should always keep dimensions, making accidental axis errors immediately visible through shape mismatch exceptions rather than silent numerical corruption.

```python
import tensorflow as tf

# Demonstrate pathological broadcasting amplification
A = tf.ones([1000, 1, 1000], dtype=tf.float32)     # 4 MB
B = tf.ones([1, 1000, 1], dtype=tf.float32)         # 4 KB
C = tf.ones([1, 1, 1000], dtype=tf.float32)         # 4 KB

# Naive computation: broadcasts to (1000, 1000, 1000) = 4 GB intermediate
# result = (A + B) * C  # OOM risk on GPU with < 4 GB memory

# Optimized factorization: reduce dimensions before broadcast
A_sum = tf.reduce_sum(A, axis=2, keepdims=True)    # (1000, 1, 1)
B_scaled = B * C                                     # broadcasts to (1, 1000, 1000)
result_opt = A_sum + tf.reduce_sum(B_scaled, axis=(1, 2), keepdims=True)

# Correct reduction axis for per-channel normalization
images = tf.random.normal([32, 224, 224, 3])       # batch of RGB images
mean = tf.reduce_mean(images, axis=(0, 1, 2), keepdims=True)  # shape (1, 1, 1, 3)
variance = tf.reduce_mean(tf.square(images - mean), axis=(0, 1, 2), keepdims=True)
normalized = (images - mean) / tf.sqrt(variance + 1e-5)

# Verify shape preservation with keepdims
tf.debugging.assert_equal(tf.shape(mean), [1, 1, 1, 3])
tf.debugging.assert_equal(tf.shape(normalized), [32, 224, 224, 3])
```

Shape compatibility errors manifest as runtime exceptions in eager mode but can propagate silently through graph construction in graph mode. A shape mismatch during graph building produces a static graph with invalid connections, but the error only surfaces during `sess.run()` or `@tf.function` execution. Defensive programming requires explicit shape assertions at graph boundaries: `tf.debugging.assert_equal(tf.shape(logits), tf.shape(labels))` validates input assumptions, failing fast with actionable error messages rather than propagating invalid shapes through dozens of downstream operations. These assertions compile away in production builds when configured with `tf.config.run_functions_eagerly(False)` and graph optimization enabled, imposing zero runtime cost.

Memory fragmentation plagues long-running training jobs when reshape operations trigger unexpected copies. TensorFlow's memory allocator, particularly the GPU BFC (Best Fit with Coalescing) allocator, maintains a pool of preallocated device memory to amortize allocation overhead. However, frequent non-contiguous reshapes that force copies fragment this pool, leading to allocation failures even when total memory usage remains below capacity. The `tf.debugging.set_log_device_placement(True)` configuration exposes when operations fall back to CPU execution due to unsupported GPU kernels, often indicating layout incompatibilities. Profiling with `TF_CPP_MIN_LOG_LEVEL=0` reveals allocator warnings about fragmentation. The remediation involves auditing reshape sequences: replacing transpose-then-reshape chains with fused operations, or explicitly copying tensors with `tf.identity()` to defragment memory layout before entering memory-intensive computation phases.

XLA (Accelerated Linear Algebra) compilation provides automatic optimization through just-in-time kernel fusion and layout optimization. Decorating functions with `@tf.function(jit_compile=True)` enables XLA to fuse sequences of element-wise and reduction operations into single GPU kernels, eliminating intermediate tensor materialization. XLA's layout optimizer automatically inserts transposes to maximize memory coalescing, often outperforming hand-tuned operation sequences. However, XLA compilation introduces cold-start latency—the first invocation of a compiled function incurs seconds of compilation time as LLVM optimizes generated code. Production deployments mitigate this through ahead-of-time compilation with saved model serialization, or by warming up compiled functions during service initialization before accepting inference requests.

Dynamic shape tensors require special handling under XLA compilation. Operations with data-dependent output shapes—`tf.unique()`, `tf.where()`, or `tf.RaggedTensor` manipulations—cannot be fully optimized by XLA's static shape analysis. Wrapping such operations in `tf.function` without `jit_compile=True` allows TensorFlow to optimize surrounding static-shape computation while preserving correctness for dynamic regions. For cases where dynamic shapes are unavoidable but performance is critical, explicitly padding to static upper bounds and masking invalid entries trades memory for predictable kernel performance.

The ultimate diagnostic tool for tensor manipulation pathologies remains the TensorFlow profiler. Capturing a trace with `tf.profiler.experimental.start()` and visualizing through TensorBoard's profile plugin exposes per-operation execution time, memory allocation patterns, and data transfer bottlenecks. The trace timeline reveals unexpected host-device synchronization points—visible as gaps in GPU utilization—that often trace back to premature `.numpy()` conversions or Python control flow that forces graph breaks. The memory profile tab identifies operations triggering large allocations, guiding optimization toward reducing intermediate tensor sizes through earlier reductions or deferred broadcasts. In distributed training contexts, the profile plugin's input pipeline analyzer quantifies whether training loops are bottlenecked on accelerator computation or data loading, informing decisions about prefetching, parallel map operations, or data format choices that maximize end-to-end throughput.
