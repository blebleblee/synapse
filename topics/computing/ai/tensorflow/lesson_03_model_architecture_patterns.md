# Lesson 3: Layers, Models, and Compositional Architecture

## 1. First-Principles Intuition & Invariants

Every neural network, regardless of its depth, purpose, or topology, reduces to a single mechanical principle: a parameterized function that transforms an input tensor into an output tensor, where the parameters themselves are learned by minimizing a differentiable objective. TensorFlow's entire architecture is built around making this principle composable. A layer is a function. A model is a function composed from layers. Training is the process of discovering the parameter assignment that minimizes loss, and the entire computational graph exists to make that discovery tractable via automatic differentiation.

This sounds abstract until you internalize what it means at the memory level. When you instantiate a `tf.keras.layers.Dense(128, activation='relu')` layer, TensorFlow allocates a weight matrix `W` of shape `[input_dim, 128]` and a bias vector `b` of shape `[128]`, both as `tf.Variable` objects backed by device memory, whether CPU RAM or GPU VRAM. The forward pass computes `output = activation(input @ W + b)`, where `@` is a batched matrix multiplication dispatched to cuBLAS or oneDNN depending on the available hardware. The activation function, the matrix multiply, and the bias addition are each registered as operations in the computation graph, and TensorFlow's automatic differentiation engine, GradientTape, records these operations so their Jacobians can be composed during the backward pass via the chain rule.

The invariant that holds throughout every abstraction layer in TensorFlow is this: a layer is both a callable and a stateful container. It owns variables, exposes them via `layer.trainable_variables` and `layer.non_trainable_variables`, and declares a `call(inputs, training=False)` method that defines its forward computation. This dual identity as a callable and a variable container is what enables the entire ecosystem of composability, serialization, and distributed training. Every complex architecture, from a ResNet to a Transformer, is ultimately a tree of objects that all satisfy this contract.

Understanding weight initialization is non-negotiable for practitioners who want to train deep networks reliably. The pathologies of poor initialization were studied empirically long before they were understood theoretically. If weights are initialized too small, activations contract as they propagate forward through each layer, and gradients vanish during backpropagation. If weights are initialized too large, activations explode and the gradient signal similarly becomes numerically unstable. The fundamental insight of Glorot (Xavier) initialization is that for a linear layer connecting `n_in` inputs to `n_out` outputs, the variance of the weight distribution should be set to `2 / (n_in + n_out)`, which preserves the variance of activations in the forward pass and the variance of gradients in the backward pass simultaneously, under the assumption of a linear or nearly-linear activation function.

He initialization modifies this for the asymmetry introduced by ReLU, which zeroes out half its input distribution, thereby halving the effective variance. He initialization sets the weight variance to `2 / n_in`, compensating for that truncation. In TensorFlow, `tf.initializers.GlorotUniform()` is the default for most layers, while `tf.initializers.HeNormal()` is the correct choice for layers followed by ReLU or its variants. These are not interchangeable. Using Glorot initialization with deep ReLU networks is a subtle bug that manifests as slow convergence or training stagnation, particularly in networks deeper than roughly fifteen layers, because the variance mismatch accumulates multiplicatively across the depth of the network.

Batch Normalization complicates the initialization story in an important way. When BatchNorm is inserted between a linear layer and its activation, the activation's input distribution is normalized before it reaches the nonlinearity. This makes the network more robust to weight scale but does not eliminate the need for thoughtful initialization. The BatchNorm layer itself has four parameters per feature: a learned scale `gamma` initialized to ones, a learned shift `beta` initialized to zeros, and two running statistics, `moving_mean` and `moving_variance`, which are non-trainable variables updated during training via an exponential moving average. The distinction between trainable and non-trainable variables is architecturally significant because only trainable variables are exposed to the optimizer, while non-trainable variables must be updated explicitly through side effects in the layer's `call` method when `training=True`.

## 2. Core Architecture & Mechanics

TensorFlow exposes two primary paradigms for constructing models: the Sequential API and the Functional API. A third paradigm, model subclassing, provides maximum flexibility at the cost of reduced static analysis. Each paradigm encodes a different set of assumptions about the graph topology, and choosing the wrong one for a given architecture creates friction that compounds over time.

The Sequential API is the most constrained. It assumes a linear chain of layers where each layer has exactly one input tensor and one output tensor, and each layer's output is the next layer's input. This constraint is not a limitation for simple feedforward classifiers or basic convolutional networks, but it becomes a hard boundary the moment you need residual connections, multi-input layers, or branching topologies. The Sequential model builds its computation graph lazily; it defers shape inference until the first call to `model.build(input_shape)` or the first forward pass. This means that until the model has seen input shapes, `model.summary()` will show unknown output dimensions and `model.trainable_variables` will return an empty list.

```python
import tensorflow as tf

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(784,)),
    tf.keras.layers.Dense(512, activation='relu',
                          kernel_initializer='he_normal',
                          bias_initializer='zeros'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(256, activation='relu',
                          kernel_initializer='he_normal',
                          bias_initializer='zeros'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(10, activation='softmax',
                          kernel_initializer='glorot_uniform',
                          bias_initializer='zeros'),
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
)

model.summary()
```

The explicit `Input` layer is the correct production practice even for Sequential models because it forces eager shape inference at construction time, so `model.summary()` immediately reflects concrete output shapes. The `he_normal` initializer on the ReLU layers and `glorot_uniform` on the final softmax layer follow directly from the initialization theory established in Section 1.

The Functional API abandons the linear-chain assumption entirely by treating tensor construction as explicit data flow. You create a symbolic input tensor, pass it through layers as if executing eagerly, and then declare a model by specifying which symbolic tensors are inputs and which are outputs. TensorFlow records the entire data flow graph between those endpoints and uses it to construct the model. Because the graph is fully specified at construction time, Functional models support static analysis, enable `model.get_layer(name)` navigation, and serialize cleanly to SavedModel format without ambiguity.

The following example implements a residual block architecture using the Functional API, demonstrating the kind of topology that the Sequential API cannot express.

```python
import tensorflow as tf

def residual_block(x, filters, stride=1, name_prefix="res"):
    shortcut = x

    x = tf.keras.layers.Conv2D(
        filters, kernel_size=3, strides=stride, padding='same',
        use_bias=False,
        kernel_initializer='he_normal',
        name=f"{name_prefix}_conv1"
    )(x)
    x = tf.keras.layers.BatchNormalization(name=f"{name_prefix}_bn1")(x)
    x = tf.keras.layers.Activation('relu', name=f"{name_prefix}_relu1")(x)

    x = tf.keras.layers.Conv2D(
        filters, kernel_size=3, strides=1, padding='same',
        use_bias=False,
        kernel_initializer='he_normal',
        name=f"{name_prefix}_conv2"
    )(x)
    x = tf.keras.layers.BatchNormalization(name=f"{name_prefix}_bn2")(x)

    if shortcut.shape[-1] != filters or stride != 1:
        shortcut = tf.keras.layers.Conv2D(
            filters, kernel_size=1, strides=stride, padding='same',
            use_bias=False,
            kernel_initializer='he_normal',
            name=f"{name_prefix}_proj"
        )(shortcut)
        shortcut = tf.keras.layers.BatchNormalization(
            name=f"{name_prefix}_proj_bn"
        )(shortcut)

    x = tf.keras.layers.Add(name=f"{name_prefix}_add")([x, shortcut])
    x = tf.keras.layers.Activation('relu', name=f"{name_prefix}_relu2")(x)
    return x


def build_resnet_small(input_shape=(32, 32, 3), num_classes=10):
    inputs = tf.keras.Input(shape=input_shape, name="image_input")

    x = tf.keras.layers.Conv2D(
        64, kernel_size=3, strides=1, padding='same',
        use_bias=False, kernel_initializer='he_normal', name="stem_conv"
    )(inputs)
    x = tf.keras.layers.BatchNormalization(name="stem_bn")(x)
    x = tf.keras.layers.Activation('relu', name="stem_relu")(x)

    x = residual_block(x, 64,  stride=1, name_prefix="stage1_block1")
    x = residual_block(x, 64,  stride=1, name_prefix="stage1_block2")
    x = residual_block(x, 128, stride=2, name_prefix="stage2_block1")
    x = residual_block(x, 128, stride=1, name_prefix="stage2_block2")
    x = residual_block(x, 256, stride=2, name_prefix="stage3_block1")
    x = residual_block(x, 256, stride=1, name_prefix="stage3_block2")

    x = tf.keras.layers.GlobalAveragePooling2D(name="gap")(x)
    x = tf.keras.layers.Dense(
        num_classes, activation='softmax',
        kernel_initializer='glorot_uniform', name="classifier"
    )(x)

    return tf.keras.Model(inputs=inputs, outputs=x, name="ResNetSmall")


model = build_resnet_small()
model.summary(line_length=100)
```

The projection shortcut in `residual_block` is a critical correctness detail that many implementations get wrong. When the residual branch changes either the spatial resolution (via `stride > 1`) or the channel depth, the skip connection tensor and the residual tensor have incompatible shapes, and the `Add` layer cannot broadcast them. The projection convolution with `kernel_size=1` and matching strides resolves the shape mismatch without introducing spatial mixing, while BatchNormalization after the projection ensures the shortcut's distribution is normalized on the same scale as the residual branch before the element-wise addition.

The data flow through this model's construction can be visualized as a directed acyclic graph where each node is a layer invocation and each edge is a tensor:

```mermaid
flowchart TD
    input["image_input\n(None, 32, 32, 3)"]

    stem_conv["stem_conv"]
    stem_bn["stem_bn"]
    stem_relu["stem_relu"]

    input --> stem_conv --> stem_bn --> stem_relu

    subgraph block1 ["stage1_block1 — Residual Block"]
        direction TB
        b1_conv1["conv1"] --> b1_bn1["bn1"] --> b1_relu1["relu1"]
        b1_relu1 --> b1_conv2["conv2"] --> b1_bn2["bn2"]
        b1_bn2 --> b1_add(("Add"))
        b1_add --> b1_relu2["relu2"]
    end

    stem_relu --> b1_conv1
    stem_relu --> b1_add

    subgraph block2 ["stage1_block2 — Residual Block"]
        direction TB
        b2_conv1["conv1"] --> b2_bn1["bn1"] --> b2_relu1["relu1"]
        b2_relu1 --> b2_conv2["conv2"] --> b2_bn2["bn2"]
        b2_bn2 --> b2_add(("Add"))
        b2_add --> b2_relu2["relu2"]
    end

    b1_relu2 --> b2_conv1
    b1_relu2 --> b2_add

    subgraph block3 ["stage2_block1 — Residual Block (stride=2, projection shortcut)"]
        direction TB
        b3_conv1["conv1 (stride=2)"] --> b3_bn1["bn1"] --> b3_relu1["relu1"]
        b3_relu1 --> b3_conv2["conv2"] --> b3_bn2["bn2"]
        b3_bn2 --> b3_add(("Add"))
        b3_proj["proj_conv\n(1×1, stride=2)"] --> b3_proj_bn["proj_bn"] --> b3_add
        b3_add --> b3_relu2["relu2"]
    end

    b2_relu2 --> b3_conv1
    b2_relu2 --> b3_proj

    ellipsis["... additional stages (same pattern) ..."]
    b3_relu2 --> ellipsis

    gap["GlobalAveragePooling2D"]
    ellipsis --> gap

    output["Dense(10, softmax)"]
    gap --> output
```

The model subclassing API provides the greatest expressive power by letting you define forward logic as an arbitrary Python function inside `call()`. This is appropriate for architectures whose computation graph cannot be statically determined from tensor shapes alone, such as recurrent networks with dynamic sequence lengths, models with conditional branching based on input values, or research architectures in rapid flux. The cost is that subclassed models are harder to serialize, their internal layer graph is not fully visible to `model.summary()` without calling `model.build()`, and they cannot be visualized with `tf.keras.utils.plot_model` without an explicit `Input` layer.

```python
import tensorflow as tf

class MultiHeadAttentionBlock(tf.keras.layers.Layer):
    def __init__(self, d_model, num_heads, dropout_rate=0.1, **kwargs):
        super().__init__(**kwargs)
        assert d_model % num_heads == 0, \
            f"d_model ({d_model}) must be divisible by num_heads ({num_heads})"
        self.d_model = d_model
        self.num_heads = num_heads
        self.depth = d_model // num_heads

        self.wq = tf.keras.layers.Dense(d_model, use_bias=False,
                                        kernel_initializer='glorot_uniform')
        self.wk = tf.keras.layers.Dense(d_model, use_bias=False,
                                        kernel_initializer='glorot_uniform')
        self.wv = tf.keras.layers.Dense(d_model, use_bias=False,
                                        kernel_initializer='glorot_uniform')
        self.dense = tf.keras.layers.Dense(d_model, use_bias=False,
                                           kernel_initializer='glorot_uniform')
        self.dropout = tf.keras.layers.Dropout(dropout_rate)
        self.layernorm = tf.keras.layers.LayerNormalization(epsilon=1e-6)

    def split_heads(self, x, batch_size):
        seq_len = tf.shape(x)[1]
        x = tf.reshape(x, (batch_size, seq_len, self.num_heads, self.depth))
        return tf.transpose(x, perm=[0, 2, 1, 3])

    def call(self, x, mask=None, training=False):
        batch_size = tf.shape(x)[0]

        q = self.split_heads(self.wq(x), batch_size)
        k = self.split_heads(self.wk(x), batch_size)
        v = self.split_heads(self.wv(x), batch_size)

        scale = tf.math.sqrt(tf.cast(self.depth, tf.float32))
        scores = tf.matmul(q, k, transpose_b=True) / scale

        if mask is not None:
            scores += (mask * -1e9)

        weights = tf.nn.softmax(scores, axis=-1)
        weights = self.dropout(weights, training=training)

        context = tf.matmul(weights, v)
        context = tf.transpose(context, perm=[0, 2, 1, 3])
        seq_len = tf.shape(context)[2]
        context = tf.reshape(context, (batch_size, seq_len, self.d_model))

        output = self.dense(context)
        output = self.layernorm(x + output)
        return output

    def get_config(self):
        config = super().get_config()
        config.update({
            "d_model": self.d_model,
            "num_heads": self.num_heads,
            "dropout_rate": self.dropout.rate,
        })
        return config


class TransformerEncoder(tf.keras.Model):
    def __init__(self, num_layers, d_model, num_heads,
                 vocab_size, max_seq_len, num_classes,
                 dropout_rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.embedding = tf.keras.layers.Embedding(vocab_size, d_model)
        self.pos_encoding = self.positional_encoding(max_seq_len, d_model)
        self.dropout = tf.keras.layers.Dropout(dropout_rate)
        self.attn_blocks = [
            MultiHeadAttentionBlock(d_model, num_heads, dropout_rate,
                                    name=f"attn_block_{i}")
            for i in range(num_layers)
        ]
        self.ffn_layers = [
            tf.keras.layers.Dense(d_model * 4, activation='relu',
                                  kernel_initializer='he_normal',
                                  name=f"ffn_dense1_{i}")
            for i in range(num_layers)
        ]
        self.ffn_proj = [
            tf.keras.layers.Dense(d_model,
                                  kernel_initializer='glorot_uniform',
                                  name=f"ffn_dense2_{i}")
            for i in range(num_layers)
        ]
        self.ffn_norms = [
            tf.keras.layers.LayerNormalization(epsilon=1e-6, name=f"ffn_norm_{i}")
            for i in range(num_layers)
        ]
        self.pool = tf.keras.layers.GlobalAveragePooling1D()
        self.classifier = tf.keras.layers.Dense(num_classes)
        self.d_model = d_model

    @staticmethod
    def positional_encoding(max_seq_len, d_model):
        """Sinusoidal encodings (Vaswani et al., 2017), shape (1, max_seq_len, d_model)."""
        positions = tf.range(max_seq_len, dtype=tf.float32)[:, tf.newaxis]
        dims = tf.range(d_model, dtype=tf.float32)[tf.newaxis, :]
        angle_rates = 1.0 / tf.pow(10000.0, (2.0 * tf.floor(dims / 2.0)) / tf.cast(d_model, tf.float32))
        angles = positions * angle_rates
        # Even dimensions use sin, odd dimensions use cos
        encoding = tf.where(tf.cast(dims % 2, tf.bool), tf.cos(angles), tf.sin(angles))
        return encoding[tf.newaxis, ...]

    def call(self, token_ids, mask=None, training=False):
        seq_len = tf.shape(token_ids)[1]
        x = self.embedding(token_ids)
        x *= tf.math.sqrt(tf.cast(self.d_model, tf.float32))
        x += self.pos_encoding[:, :seq_len, :]
        x = self.dropout(x, training=training)

        for attn, ffn1, ffn2, norm in zip(self.attn_blocks, self.ffn_layers,
                                          self.ffn_proj, self.ffn_norms):
            x = attn(x, mask=mask, training=training)        # residual + norm inside
            x = norm(x + ffn2(self.dropout(ffn1(x), training=training)))

        return self.classifier(self.pool(x))                # logits
```


## 3. High-Performance Optimization & Failure Modes

### 3.1 Mixed-Precision Training

Both the ResNet-small and the Transformer encoder described above are compute-bound at batch sizes typical of GPU training (≥ 64). The dominant cost in the residual blocks is the 3 × 3 convolution; in the Transformer it is the `tf.matmul` calls inside `MultiHeadAttentionBlock.call`. Enabling mixed precision lets TensorFlow cast these operations to `float16` (or `bfloat16` on Ampere+ GPUs) while keeping the master weights in `float32`, roughly halving memory bandwidth and doubling throughput on Tensor Cores.

```python
import tensorflow as tf

# Must be called before any model is built or compiled.
tf.keras.mixed_precision.set_global_policy('mixed_float16')

# Re-build the model so that all layers adopt the new policy.
model = build_resnet_small()
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy'],
)

# With model.compile()/fit(), Keras wraps the optimizer in a
# LossScaleOptimizer automatically. A custom training loop must wrap it
# itself: tf.keras.mixed_precision.LossScaleOptimizer(optimizer).
# Keep the final softmax in float32: Dense(..., dtype='float32').
```

The critical invariant is that **loss values must remain finite in `float32`**.  When the policy is `mixed_float16`, the `LossScaleOptimizer` multiplies the loss by a dynamic scale factor before back-propagation and divides the gradients back, preventing subnormal `float16` gradients from underflowing to zero.  If you observe `NaN` losses after enabling mixed precision, the first diagnostic is to print `tf.keras.mixed_precision.global_policy().name` and confirm that the loss is not being computed in `float16` directly.

For the Transformer, the softmax inside `MultiHeadAttentionBlock` is the most sensitive operation: `float16` has a maximum representable value of 65 504, so the pre-softmax scores `Q Kᵀ / √d` can overflow when `d` is large or when attention weights concentrate.  The standard mitigation is to compute the softmax in `float32` explicitly:

```python
# Inside MultiHeadAttentionBlock.call, replace the softmax line with:
weights = tf.nn.softmax(tf.cast(scores, tf.float32), axis=-1)
weights = tf.cast(weights, scores.dtype)
```

### 3.2 XLA Compilation and Graph Optimisation

`tf.function` with `jit_compile=True` (or the `@tf.function(jit_compile=True)` decorator) lowers the traced graph to HLO and then to the target backend (GPU or CPU).  For the residual blocks, this fuses the `Conv2D → BatchNormalization → ReLU` triple into a single kernel launch, eliminating two intermediate tensor materialisations per block.  For the Transformer, it fuses the `matmul → scale → mask → softmax → matmul` sequence, which is the single largest source of kernel-launch overhead at small sequence lengths.

```python
import tensorflow as tf

# Wrap the training step so that the entire forward + backward pass
# is compiled once and replayed.
@tf.function(jit_compile=True)
def train_step(model, x_batch, y_batch, optimizer):
    with tf.GradientTape() as tape:
        logits = model(x_batch, training=True)   # TransformerEncoder returns logits
        loss = tf.reduce_mean(tf.keras.losses.sparse_categorical_crossentropy(
            y_batch, logits, from_logits=True
        ))
    grads = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))
    return loss
```

A practical caveat: `jit_compile=True` increases the first-iteration latency by 10–60 s (XLA compilation) but reduces steady-state step time by 15–35 % on GPU.  For short training runs (< 500 steps) the amortisation may not pay off; profile with `tf.profiler` before committing.

### 3.3 Failure Modes Specific to Residual Architectures

| Symptom | Root cause | Diagnostic | Fix |
|---|---|---|---|
| Training loss plateaus at ~ ln(C) for C classes | Identity shortcut dominates; residual branch contributes ≈ 0 | Plot `‖residual‖ / ‖shortcut‖` per block; if < 0.01 the block is effectively a pass-through | Increase learning rate, add weight decay, or replace `glorot_uniform` with `he_normal` for the residual convolutions |
| Gradient norm explodes past step 500 in a 20-layer variant | No gradient clipping; deep stacks amplify the Jacobian | Log `tf.linalg.global_norm(grads)` with `tf.summary.scalar` in the training step | Add `clipnorm=1.0` to the optimizer, or insert a `tf.keras.layers.Lambda(lambda x: tf.clip_by_norm(x, 5.0))` after the final block |
| `Add` layer raises `InvalidArgumentError: Shapes are not broadcastable` | Projection shortcut missing when `stride > 1` or channel count changes | Inspect `model.summary()` for the `Add` layer's input shapes | Ensure the `proj_conv` path exists in every block where `in_channels ≠ out_channels` or `stride ≠ 1` |

The third row is the most common implementation error.  In the `residual_block` shown in § 2, the projection path is created only when `stride != 1 or in_channels != out_channels`.  If a developer copies the block and hard-codes `stride=1` for a stage that actually needs `stride=2`, the skip tensor retains the old spatial resolution and the `Add` layer fails at graph-construction time (functional API) or at the first `call` (subclassing API).

### 3.4 Failure Modes Specific to Transformer Encoders

**Attention-pattern collapse.**  When all heads converge to the same attention distribution (often uniform or fully-attentive), the model effectively reduces to a single-head network.  Detect this by computing the entropy of each head's weight matrix:

```python
import tensorflow as tf
import numpy as np

def head_entropy(model, x_batch):
    """Per-head attention entropy (nats) of the first attention block.

    Deeper blocks need the output of the blocks before them as input."""
    attn_block = model.attn_blocks[0]
    batch_size = tf.shape(x_batch)[0]
    x = model.embedding(x_batch)
    x *= tf.math.sqrt(tf.cast(model.d_model, tf.float32))
    x += model.pos_encoding[:, :tf.shape(x_batch)[1], :]

    q = attn_block.split_heads(attn_block.wq(x), batch_size)
    k = attn_block.split_heads(attn_block.wk(x), batch_size)
    scale = tf.math.sqrt(tf.cast(attn_block.depth, tf.float32))
    scores = tf.matmul(q, k, transpose_b=True) / scale
    weights = tf.nn.softmax(scores, axis=-1)  # (B, H, T, T)

    # Entropy per head, averaged over batch and query positions
    entropy = -tf.reduce_sum(weights * tf.math.log(weights + 1e-10), axis=-1)
    return tf.reduce_mean(entropy, axis=[0, 2]).numpy()  # shape (num_heads,)
```

If two or more heads report entropy within 0.05 nats of each other across 100+ steps, the heads are redundant.  Remedies include increasing `d_model`, adding a relative-position bias to the scores, or initialising the `W_Q`, `W_K`, `W_V` matrices with a smaller variance so that early-training scores are more peaked.

**Positional-encoding imbalance.**  The sinusoidal encoding in `TransformerEncoder.positional_encoding` produces values in [−1, 1], while the `x *= √d_model` scaling multiplies the token embeddings by about 11 for `d_model = 128` and 32 for `d_model = 1024`.  That scaling is applied *before* the positional encoding is added (as in § 2) so that position information neither drowns the token signal nor disappears in it.  If you change the embedding initialisation or `d_model`, compare `tf.math.reduce_std` of the scaled embeddings with that of `pos_encoding`: when one is orders of magnitude larger, the model effectively loses either word identity or word order.

### 3.5 Checkpointing, Distributed Training, and Model Export

For production pipelines the model must survive process restarts and be deployable to inference runtimes.  The following pattern covers all three (create the checkpoint after the model is built inside the strategy scope, so it tracks the replicated variables):

```python
import tensorflow as tf
import os

# --- Distributed strategy ----------------------------------------------------
strategy = tf.distribute.MirroredStrategy()  # multi-GPU on one node
# For multi-node: tf.distribute.MultiWorkerMirroredStrategy()

with strategy.scope():
    model = build_resnet_small()
    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
    model.compile(optimizer=optimizer,
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

# The `with strategy.scope()` block ensures that all layers are replicated
# across devices.  For subclassed models (TransformerEncoder), the same
# pattern applies, but you must call model.build() inside the scope so that
# the replicated variables are created:
#
#   with strategy.scope():
#       model = TransformerEncoder(num_layers=4, d_model=128, num_heads=4,
#                                  vocab_size=10000, max_seq_len=128,
#                                  num_classes=10)
#       model.build(input_shape=(None, 128))   # forces variable creation
#       optimizer = tf.keras.optimizers.Adam(1e-3)

# --- Checkpointing -----------------------------------------------------------
ckpt_dir = "./checkpoints/resnet_small"
ckpt = tf.train.Checkpoint(model=model, optimizer=optimizer, step=tf.Variable(0))
ckpt_manager = tf.train.CheckpointManager(ckpt, ckpt_dir, max_to_keep=3)

# Restore the latest checkpoint if it exists.
if ckpt_manager.latest_checkpoint:
    ckpt.restore(ckpt_manager.latest_checkpoint)
    print(f"Restored from step {ckpt.step.numpy()}")

# --- Export for inference ----------------------------------------------------
# SavedModel is the canonical format for TFServing, TF Lite, and Keras
# production serving.
export_dir = "./exported/resnet_small"
tf.saved_model.save(model, export_dir)

# For TF Lite (mobile / edge), convert with a representative dataset:
# converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
# converter.optimizations = [tf.lite.Optimize.DEFAULT]
# tflite_model = converter.convert()
```

A subtle correctness issue with `MirroredStrategy` and subclassed models: the `call` method must be **deterministic with respect to the batch dimension**.  The `MultiHeadAttentionBlock.call` uses `tf.shape(x)[0]` to obtain the batch size, which is a *symbolic* value during tracing.  Under `MirroredStrategy` the per-replica batch size is `global_batch // num_replicas`, so the reshape in `split_heads` must use the *local* batch size, not a hard-coded global one.  Using `tf.shape(x)[0]` (as shown in § 2) is correct; hard-coding `batch_size = 64` would break when the strategy splits the batch.

### 3.6 Validation and Sanity Checks Before Training

Before launching a multi-hour training run, execute the following checks:

```python
import tensorflow as tf
import numpy as np

def pre_train_checks(model, dummy_input, num_classes=10):
    """Run a forward pass and verify output shape, finiteness, and gradient flow."""
    # 1. Output shape
    out = model(dummy_input, training=False)
    assert out.shape[1] == num_classes, f"Expected {num_classes} classes, got {out.shape[1]}"

    # 2. Finiteness
    assert tf.reduce_all(tf.math.is_finite(out)), "Non-finite values in output"

    # 3. Gradient flow: every trainable variable must receive a non-zero gradient
    with tf.GradientTape() as tape:
        logits = model(dummy_input, training=True)
        loss = tf.reduce_mean(tf.square(logits))
    grads = tape.gradient(loss, model.trainable_variables)
    dead = [v.name for v, g in zip(model.trainable_variables, grads)
            if g is None or tf.reduce_all(g == 0)]
    if dead:
        print(f"WARNING: {len(dead)} variables received zero gradient: {dead[:5]}")
    else:
        print("All trainable variables received non-zero gradients.")

    # 4. Parameter count sanity
    total = sum(np.prod(v.shape) for v in model.trainable_variables)
    print(f"Total trainable parameters: {total:,}")
```

Running this on a single dummy batch (e.g., `tf.random.normal((2, 32, 32, 3))` for the ResNet or `tf.random.uniform((2, 128), 0, 10000, dtype=tf.int32)` for the Transformer) catches shape mismatches, missing projection shortcuts, and dead layers before any GPU time is consumed.

---

## Summary

This lesson established the two dominant model-construction patterns in TensorFlow Keras—**functional API** for statically-defined graphs (ResNet-small) and **subclassing API** for dynamic computation (Transformer encoder)—and showed how the residual connection, the projection shortcut, and the multi-head attention mechanism are implemented as concrete layer compositions.  The key invariants are: (1) every residual block must have a shape-compatible skip path; (2) the projection convolution uses `kernel_size=1` to avoid spatial mixing; (3) the `call` method of a subclassed layer must be deterministic in the batch dimension for distributed strategies; and (4) mixed-precision training requires explicit `float32` softmax in attention to prevent `float16` overflow.  The failure-mode tables and pre-training checks in § 3 provide a diagnostic checklist that separates architectural bugs (shape mismatches, dead gradients) from optimisation bugs (learning-rate mismatch, attention collapse) before they manifest as non-converging training curves.

## Key Terms

| Term | Definition |
|---|---|
| **Residual block** | A sub-network that computes `y = F(x) + x` (or `y = F(x) + W·x` when shapes differ), enabling gradient flow through an identity path. |
| **Projection shortcut** | A 1 × 1 convolution (optionally with stride > 1) that maps the skip-connection tensor to the same shape as the residual branch, used when channel count or spatial resolution changes. |
| **Functional API** | Keras model construction by composing `tf.keras.layers` objects into a directed acyclic graph; the graph is fixed at build time. |
| **Subclassing API** | Keras model construction by overriding `call()` in a `tf.keras.Model` subclass; the computation graph is determined at runtime. |
| **Multi-head attention** | Parallel attention sub-spaces (`num_heads` copies of `Q Kᵀ V / √d`) that are concatenated and projected, allowing the model to attend to different representation subspaces simultaneously. |
| **Sinusoidal positional encoding** | Fixed, non-learned position embeddings using `sin`/`cos` at geometrically-spaced frequencies (Vaswani et al., 2017), added to token embeddings before the first attention layer. |
| **Mixed precision** | Training with `float16` (or `bfloat16`) activations and `float32` master weights, coordinated by a loss-scaling mechanism to prevent gradient underflow. |
| **XLA (Accelerated Linear Algebra)** | A compiler that lowers a traced `tf.function` graph to HLO IR and then to the target hardware, enabling kernel fusion and vectorisation. |
| **MirroredStrategy** | A `tf.distribute.Strategy` that replicates the model across multiple GPUs on a single node, synchronising gradients via an all-reduce. |
| **Attention-pattern collapse** | A degenerate training regime in which multiple attention heads converge to identical (often uniform) weight distributions, reducing effective model capacity. |
| **SavedModel** | The canonical TensorFlow serialization format (a directory of `saved_model.pb` + `variables/`) for serving, TF Lite conversion, and cross-language inference. |