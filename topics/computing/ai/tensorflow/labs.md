# Operational Verification Labs: TensorFlow

## Objective & Environment Setup

TensorFlow represents Google's mature production machine learning framework, forged through billions of inference requests across Search, YouTube, and Cloud AI Platform. These operational verification labs ground you in TensorFlow's computational graph abstraction, its eager execution model, and the AutoGraph trace compilation pipeline that transforms Python control flow into optimized static graphs. You will construct end-to-end training pipelines, profile GPU memory fragmentation, benchmark mixed-precision throughput, and stress-test model serving endpoints under adversarial input distributions. This is not a theoretical survey of neural network mathematics—this is production ML engineering where you debug CUDA out-of-memory errors at 3 AM, tune batch sizes against PCIe bandwidth saturation, and validate numerical stability across TPU pod slices.

Modern TensorFlow operates through two execution paradigms that you must internalize as complementary rather than competing. Eager execution provides imperative Python semantics where tensors behave like NumPy arrays and operations execute immediately, enabling rapid prototyping and intuitive debugging through standard Python tooling like `pdb` and IDE breakpoints. Graph execution compiles your model into a static dataflow graph that TensorFlow's runtime optimizes through operation fusion, constant folding, and memory layout transformations before dispatching to hardware accelerators. The `tf.function` decorator serves as the bridge between these worlds, tracing your Python function into a graph on first invocation and caching the compiled artifact for subsequent calls. Understanding when tracing invalidates cached graphs—through dynamic control flow, variable Python types, or shape polymorphism—separates competent practitioners from those who ship models that silently recompile on every forward pass, destroying throughput.

Begin by establishing a hermetic Python 3.11 virtual environment to isolate TensorFlow's CUDA and cuDNN dependencies from system libraries. TensorFlow 2.15 represents the current stable release with full CUDA 12 support and native ARM64 acceleration for Apple Silicon, though production deployments frequently pin to TensorFlow 2.13 for its proven stability across multi-tenant serving infrastructure. Install TensorFlow with explicit GPU support, then layer in essential profiling and data engineering dependencies that mirror real-world production stacks.

```bash
python3.11 -m venv tf_ops_env
source tf_ops_env/bin/activate
pip install --upgrade pip setuptools wheel

# TensorFlow with CUDA 12.x support
pip install tensorflow[and-cuda]==2.15.0

# Production ML dependencies
pip install tensorflow-datasets==4.9.3
pip install tensorflow-model-optimization==0.8.0
pip install tensorflow-hub==0.15.0

# Diagnostic and profiling tools
pip install tensorboard==2.15.1
pip install tensorflow-metadata==1.14.0
pip install psutil==5.9.6
pip install py-cpuinfo==9.0.0

# Data engineering and numerical computing
pip install pandas==2.1.3
pip install polars==0.19.13
pip install pyarrow==14.0.1
pip install scikit-learn==1.3.2

# Model serving and deployment
pip install tensorflow-serving-api==2.15.0
pip install grpcio==1.59.3
pip install protobuf==4.25.1
```

Verify your installation detects GPU devices and reports the correct CUDA/cuDNN versions that TensorFlow compiled against. TensorFlow's device placement logging reveals which operations dispatch to GPU versus CPU, exposing subtle performance regressions where small tensors trigger expensive host-device memcpy operations that saturate PCIe bandwidth.

```python
import tensorflow as tf
import sys

print(f"TensorFlow version: {tf.__version__}")
print(f"Python version: {sys.version}")
print(f"CUDA available: {tf.test.is_built_with_cuda()}")
print(f"GPU devices: {tf.config.list_physical_devices('GPU')}")

# Enable memory growth to prevent TensorFlow from allocating entire GPU
for gpu in tf.config.list_physical_devices('GPU'):
    tf.config.experimental.set_memory_growth(gpu, True)

# Verify cuDNN and CUDA versions
print(f"Built with cuDNN: {tf.test.is_built_with_gpu_support()}")

# Test tensor operations dispatch to GPU
with tf.device('/GPU:0'):
    a = tf.random.normal([1000, 1000])
    b = tf.random.normal([1000, 1000])
    c = tf.matmul(a, b)
    print(f"Result shape: {c.shape}, Device: {c.device}")
```

Configure TensorBoard to capture execution traces, memory profiles, and training metrics. TensorBoard's profiler plugin exposes kernel launch latencies, memory bandwidth utilization, and operation placement decisions that guide optimization efforts. Launch TensorBoard in the background as a persistent monitoring service that aggregates logs from multiple training runs.

```bash
mkdir -p ./tb_logs
tensorboard --logdir=./tb_logs --port=6006 --bind_all &
echo "TensorBoard running at http://localhost:6006"
```

Establish a project structure that separates model definitions, data pipelines, training loops, and evaluation harnesses into discrete modules that compile independently under `tf.function`. This modular architecture prevents unnecessary retracing when you modify evaluation logic without touching the training loop, and enables A/B testing model architectures through simple import swaps.

```bash
mkdir -p tf_verification/{models,data,training,evaluation,serving}
touch tf_verification/__init__.py
touch tf_verification/models/__init__.py
touch tf_verification/data/__init__.py
touch tf_verification/training/__init__.py
touch tf_verification/evaluation/__init__.py
touch tf_verification/serving/__init__.py
```

## Exercise 1: Hands-On Implementation & Pipeline Execution

Construct a production-grade image classification pipeline that trains a convolutional neural network on CIFAR-10, demonstrating TensorFlow's data loading abstractions, mixed-precision training, and distributed strategy APIs. This exercise grounds you in the physical reality of GPU memory hierarchies—L1 cache, shared memory, global memory, and PCIe transfer buffers—where naive implementations thrash the memory subsystem with uncoalesced reads and destroy throughput. You will profile kernel occupancy, measure achieved memory bandwidth against theoretical hardware limits, and apply operator fusion to eliminate redundant memory round-trips.

Begin with a custom residual network architecture that eschews pre-trained weights to focus on training dynamics rather than transfer learning. The residual block structure addresses gradient flow through deep networks, where vanishing gradients historically prevented convergence beyond a few dozen layers. Each residual connection provides a gradient highway that shortcuts backward pass computations, allowing error signals to propagate directly to early layers without multiplicative attenuation through activation functions.

```python
# tf_verification/models/resnet_cifar.py
import tensorflow as tf
from tensorflow import keras
from typing import Tuple


class ResidualBlock(keras.layers.Layer):
    """Residual block with pre-activation and projection shortcut.
    
    Pre-activation ordering (BN -> ReLU -> Conv) improves gradient flow
    compared to post-activation residual networks. The projection shortcut
    handles dimension mismatches when stride > 1 or channels change.
    """
    
    def __init__(
        self,
        filters: int,
        kernel_size: int = 3,
        stride: int = 1,
        use_projection: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.filters = filters
        self.kernel_size = kernel_size
        self.stride = stride
        self.use_projection = use_projection
        
        # Pre-activation pathway
        self.bn1 = keras.layers.BatchNormalization()
        self.relu1 = keras.layers.ReLU()
        self.conv1 = keras.layers.Conv2D(
            filters=filters,
            kernel_size=kernel_size,
            strides=stride,
            padding='same',
            use_bias=False,
            kernel_initializer='he_normal'
        )
        
        self.bn2 = keras.layers.BatchNormalization()
        self.relu2 = keras.layers.ReLU()
        self.conv2 = keras.layers.Conv2D(
            filters=filters,
            kernel_size=kernel_size,
            strides=1,
            padding='same',
            use_bias=False,
            kernel_initializer='he_normal'
        )
        
        # Projection shortcut for dimension matching
        if use_projection:
            self.projection = keras.layers.Conv2D(
                filters=filters,
                kernel_size=1,
                strides=stride,
                padding='same',
                use_bias=False,
                kernel_initializer='he_normal'
            )
        else:
            self.projection = None
    
    def call(self, inputs: tf.Tensor, training: bool = False) -> tf.Tensor:
        shortcut = inputs
        
        # Pre-activation residual pathway
        x = self.bn1(inputs, training=training)
        x = self.relu1(x)
        x = self.conv1(x)
        
        x = self.bn2(x, training=training)
        x = self.relu2(x)
        x = self.conv2(x)
        
        # Apply projection if dimensions changed
        if self.projection is not None:
            shortcut = self.projection(shortcut)
        
        return x + shortcut
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'filters': self.filters,
            'kernel_size': self.kernel_size,
            'stride': self.stride,
            'use_projection': self.use_projection
        })
        return config


class ResNetCIFAR(keras.Model):
    """Residual network optimized for CIFAR-10 32x32 images.
    
    Architecture: Initial conv -> 3 residual stages -> global pool -> dense
    Each stage doubles channels and halves spatial resolution via stride-2 conv.
    Total parameters: ~1.7M for depth=[3,3,3] configuration.
    """
    
    def __init__(
        self,
        num_classes: int = 10,
        depths: Tuple[int, int, int] = (3, 3, 3),
        initial_filters: int = 64,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.num_classes = num_classes
        self.depths = depths
        self.initial_filters = initial_filters
        
        # Initial convolution with larger receptive field
        self.initial_conv = keras.layers.Conv2D(
            filters=initial_filters,
            kernel_size=7,
            strides=1,
            padding='same',
            use_bias=False,
            kernel_initializer='he_normal',
            name='initial_conv'
        )
        self.initial_bn = keras.layers.BatchNormalization(name='initial_bn')
        self.initial_relu = keras.layers.ReLU(name='initial_relu')
        
        # Residual stages with progressive downsampling
        self.stage1 = self._build_stage(
            filters=initial_filters,
            depth=depths[0],
            stride=1,
            name='stage1'
        )
        
        self.stage2 = self._build_stage(
            filters=initial_filters * 2,
            depth=depths[1],
            stride=2,
            name='stage2'
        )
        
        self.stage3 = self._build_stage(
            filters=initial_filters * 4,
            depth=depths[2],
            stride=2,
            name='stage3'
        )
        
        # Classification head
        self.global_pool = keras.layers.GlobalAveragePooling2D(name='global_pool')
        self.dropout = keras.layers.Dropout(0.5, name='dropout')
        self.classifier = keras.layers.Dense(
            units=num_classes,
            kernel_initializer='he_normal',
            name='classifier'
        )
    
    def _build_stage(
        self,
        filters: int,
        depth: int,
        stride: int,
        name: str
    ) -> keras.Sequential:
        """Build a residual stage with depth blocks."""
        blocks = []
        
        # First block handles downsampling and channel expansion
        blocks.append(ResidualBlock(
            filters=filters,
            stride=stride,
            use_projection=True,
            name=f'{name}_block0'
        ))
        
        # Remaining blocks maintain dimensions
        for i in range(1, depth):
            blocks.append(ResidualBlock(
                filters=filters,
                stride=1,
                use_projection=False,
                name=f'{name}_block{i}'
            ))
        
        return keras.Sequential(blocks, name=name)
    
    def call(self, inputs: tf.Tensor, training: bool = False) -> tf.Tensor:
        x = self.initial_conv(inputs)
        x = self.initial_bn(x, training=training)
        x = self.initial_relu(x)
        
        x = self.stage1(x, training=training)
        x = self.stage2(x, training=training)
        x = self.stage3(x, training=training)
        
        x = self.global_pool(x)
        x = self.dropout(x, training=training)
        logits = self.classifier(x)
        
        return logits
    
    def get_config(self):
        return {
            'num_classes': self.num_classes,
            'depths': self.depths,
            'initial_filters': self.initial_filters
        }


def create_model(num_classes: int = 10) -> ResNetCIFAR:
    """Factory function for model instantiation and configuration."""
    model = ResNetCIFAR(
        num_classes=num_classes,
        depths=(3, 3, 3),
        initial_filters=64
    )
    
    # Build model with sample input to initialize weights
    dummy_input = tf.random.normal([1, 32, 32, 3])
    _ = model(dummy_input, training=False)
    
    return model
```

Implement a high-performance data pipeline using `tf.data.Dataset` that overlaps data loading, preprocessing, and device transfer with GPU computation. The `tf.data` API represents TensorFlow's declarative abstraction over asynchronous I/O, where `prefetch`, `map`, and `cache` transformations compile into a parallel execution graph that saturates disk bandwidth and hides preprocessing latency. Understanding the buffer sizing parameters and parallelism configuration separates pipelines that achieve 95% GPU utilization from those that starve the accelerator waiting for the next batch.

```python
# tf_verification/data/cifar_pipeline.py
import tensorflow as tf
import tensorflow_datasets as tfds
from typing import Tuple, Dict
import os


class CIFARDataPipeline:
    """Production data pipeline with augmentation, prefetching, and caching.
    
    Performance optimizations:
    1. Parallel data loading via AUTOTUNE interleave
    2. Vectorized preprocessing with fused augmentation ops
    3. Prefetch buffer to overlap CPU preprocessing with GPU compute
    4. Memory caching of training data after first epoch
    5. Deterministic shuffling via fixed seed for reproducibility
    """
    
    def __init__(
        self,
        batch_size: int = 128,
        prefetch_buffer: int = tf.data.AUTOTUNE,
        cache_dir: str = '/tmp/tfds_cache',
        seed: int = 42
    ):
        self.batch_size = batch_size
        self.prefetch_buffer = prefetch_buffer
        self.cache_dir = cache_dir
        self.seed = seed
        
        # CIFAR-10 statistics for normalization
        self.mean = tf.constant([0.4914, 0.4822, 0.4465], dtype=tf.float32)
        self.std = tf.constant([0.2470, 0.2435, 0.2616], dtype=tf.float32)
    
    def _normalize(self, image: tf.Tensor) -> tf.Tensor:
        """Z-score normalization using dataset statistics."""
        image = tf.cast(image, tf.float32) / 255.0
        image = (image - self.mean) / self.std
        return image
    
    def _augment_train(self, image: tf.Tensor, label: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """Training augmentation with random crop and horizontal flip.
        
        Pad-and-crop strategy maintains input resolution while providing
        spatial translation invariance. Horizontal flip doubles effective
        dataset size for symmetric object categories.
        """
        # Pad 4 pixels on each side, then random crop back to 32x32
        image = tf.image.pad_to_bounding_box(image, 4, 4, 40, 40)
        image = tf.image.random_crop(image, size=[32, 32, 3], seed=self.seed)
        
        # Random horizontal flip with 50% probability
        image = tf.image.random_flip_left_right(image, seed=self.seed)
        
        # Normalize after augmentation to maintain statistical properties
        image = self._normalize(image)
        
        return image, label
    
    def _preprocess_eval(self, image: tf.Tensor, label: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """Validation preprocessing without augmentation."""
        image = self._normalize(image)
        return image, label
    
    def load_dataset(
        self,
        split: str,
        augment: bool = True
    ) -> tf.data.Dataset:
        """Load CIFAR-10 with optimized preprocessing pipeline.
        
        Args:
            split: 'train' or 'test'
            augment: Apply random augmentation (training only)
            
        Returns:
            Batched dataset with prefetching enabled
        """
        # Download and cache dataset via TFDS
        ds = tfds.load(
            'cifar10',
            split=split,
            data_dir=self.cache_dir,
            shuffle_files=(split == 'train'),
            as_supervised=True
        )
        
        if split == 'train':
            # Shuffle with large buffer to break sequential correlation
            ds = ds.shuffle(
                buffer_size=50000,
                seed=self.seed,
                reshuffle_each_iteration=True
            )
            
            # Cache after shuffle to preserve randomness across epochs
            ds = ds.cache()
            
            # Apply augmentation
            if augment:
                ds = ds.map(
                    self._augment_train,
                    num_parallel_calls=tf.data.AUTOTUNE,
                    deterministic=False
                )
            else:
                ds = ds.map(
                    self._preprocess_eval,
                    num_parallel_calls=tf.data.AUTOTUNE
                )
        else:
            # Cache validation data in memory for fast repeated evaluation
            ds = ds.cache()
            ds = ds.map(
                self._preprocess_eval,
                num_parallel_calls=tf.data.AUTOTUNE
            )
        
        # Batch and prefetch for pipeline parallelism
        ds = ds.batch(self.batch_size, drop_remainder=(split == 'train'))
        ds = ds.prefetch(buffer_size=self.prefetch_buffer)
        
        return ds
    
    def get_dataset_info(self) -> Dict:
        """Return dataset statistics and configuration."""
        return {
            'num_classes': 10,
            'image_shape': (32, 32, 3),
            'train_samples': 50000,
            'test_samples': 10000,
            'batch_size': self.batch_size,
            'mean': self.mean.numpy().tolist(),
            'std': self.std.numpy().tolist()
        }
```

Construct the training loop with mixed-precision arithmetic, gradient accumulation, and learning rate scheduling. Mixed precision leverages Tensor Cores on NVIDIA GPUs—specialized matrix multiplication units that deliver 8× throughput for FP16 operations compared to FP32, provided matrix dimensions align to multiples of 8. TensorFlow's automatic mixed precision (AMP) policy casts operations to FP16 where numerically safe, maintains FP32 master weights for stability, and applies loss scaling to prevent gradient underflow in the limited FP16 dynamic range.

```python
# tf_verification/training/trainer.py
import tensorflow as tf
from tensorflow import keras
import time
from typing import Dict, Optional, Tuple
import json
import os


class MixedPrecisionTrainer:
    """Production training loop with mixed precision and gradient accumulation.
    
    Key features:
    1. Automatic mixed precision via tf.keras.mixed_precision
    2. Gradient accumulation for effective large batch sizes
    3. Cosine annealing learning rate schedule with warmup
    4. TensorBoard logging with epoch-level profiling
    5. Checkpoint management with best model tracking
    """
    
    def __init__(
        self,
        model: keras.Model,
        optimizer: keras.optimizers.Optimizer,
        loss_fn: keras.losses.Loss,
        use_mixed_precision: bool = True,
        gradient_accumulation_steps: int = 1,
        log_dir: str = './tb_logs',
        checkpoint_dir: str = './checkpoints'
    ):
        self.model = model
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.log_dir = log_dir
        self.checkpoint_dir = checkpoint_dir
        
        # Enable automatic mixed precision
        if use_mixed_precision:
            policy = keras.mixed_precision.Policy('mixed_float16')
            keras.mixed_precision.set_global_policy(policy)
            print(f"Mixed precision enabled: {policy.name}")
        
        # Metrics tracking
        self.train_loss_metric = keras.metrics.Mean(name='train_loss')
        self.train_acc_metric = keras.metrics.SparseCategoricalAccuracy(name='train_acc')
        self.val_loss_metric = keras.metrics.Mean(name='val_loss')
        self.val_acc_metric = keras.metrics.SparseCategoricalAccuracy(name='val_acc')
        
        # TensorBoard writer
        self.train_writer = tf.summary.create_file_writer(
            os.path.join(log_dir, 'train')
        )
        self.val_writer = tf.summary.create_file_writer(
            os.path.join(log_dir, 'val')
        )
        
        # Checkpoint manager
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.checkpoint = tf.train.Checkpoint(
            model=model,
            optimizer=optimizer
        )
        self.checkpoint_manager = tf.train.CheckpointManager(
            self.checkpoint,
            directory=checkpoint_dir,
            max_to_keep=3
        )
        
        self.best_val_acc = 0.0
        self.global_step = 0
    
    @tf.function
    def train_step(
        self,
        images: tf.Tensor,
        labels: tf.Tensor,
        accumulation_step: int
    ) -> Tuple[tf.Tensor, tf.Tensor]:
        """Single training step with gradient accumulation.
        
        Gradient accumulation simulates larger batch sizes by accumulating
        gradients over multiple forward-backward passes before updating weights.
        This enables training with effective batch sizes beyond GPU memory limits.
        """
        with tf.GradientTape() as tape:
            logits = self.model(images, training=True)
            loss = self.loss_fn(labels, logits)
            
            # Scale loss by accumulation steps
            scaled_loss = loss / self.gradient_accumulation_steps
            
            # Apply loss scaling for mixed precision
            if isinstance(self.optimizer, keras.mixed_precision.LossScaleOptimizer):
                scaled_loss = self.optimizer.get_scaled_loss(scaled_loss)
        
        # Compute gradients
        gradients = tape.gradient(scaled_loss, self.model.trainable_variables)
        
        # Unscale gradients if using mixed precision
        if isinstance(self.optimizer, keras.mixed_precision.LossScaleOptimizer):
            gradients = self.optimizer.get_unscaled_gradients(gradients)
        
        # Apply gradients on final accumulation step
        if accumulation_step == self.gradient_accumulation_steps - 1:
            self.optimizer.apply_gradients(
                zip(gradients, self.model.trainable_variables)
            )
        
        return loss, logits
    
    @tf.function
    def val_step(self, images: tf.Tensor, labels: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """Validation step without gradient computation."""
        logits = self.model(images, training=False)
        loss = self.loss_fn(labels, logits)
        return loss, logits
    
    def train_epoch(self, train_ds: tf.data.Dataset, epoch: int) -> Dict:
        """Execute one training epoch with gradient accumulation."""
        self.train_loss_metric.reset_states()
        self.train_acc_metric.reset_states()
        
        start_time = time.time()
        num_batches = 0
        
        for batch_idx, (images, labels) in enumerate(train_ds):
            accumulation_step = batch_idx % self.gradient_accumulation_steps
            
            loss, logits = self.train_step(images, labels, accumulation_step)
            
            # Update metrics
            self.train_loss_metric.update_state(loss)
            self.train_acc_metric.update_state(labels, logits)
            
            self.global_step += 1
            num_batches += 1
            
            # Log to TensorBoard every 50 steps
            if self.global_step % 50 == 0:
                with self.train_writer.as_default():
                    tf.summary.scalar(
                        'batch_loss',
                        loss,
                        step=self.global_step
                    )
                    tf.summary.scalar(
                        'learning_rate',
                        self.optimizer.learning_rate,
                        step=self.global_step
                    )
        
        epoch_time = time.time() - start_time
        
        # Aggregate epoch metrics
        epoch_loss = self.train_loss_metric.result().numpy()
        epoch_acc = self.train_acc_metric.result().numpy()
        
        with self.train_writer.as_default():
            tf.summary.scalar('epoch_loss', epoch_loss, step=epoch)
            tf.summary.scalar('epoch_acc', epoch_acc, step=epoch)
            tf.summary.scalar('epoch_time', epoch_time, step=epoch)
        
        return {
            'loss': float(epoch_loss),
            'accuracy': float(epoch_acc),
            'time': float(epoch_time),
            'batches': num_batches
        }
    
    def validate(self, val_ds: tf.data.Dataset, epoch: int) -> Dict:
        """Execute validation pass."""
        self.val_loss_metric.reset_states()
        self.val_acc_metric.reset_states()
        
        for images, labels in val_ds:
            loss, logits = self.val_step(images, labels)
            self.val_loss_metric.update_state(loss)
            self.val_acc_metric.update_state(labels, logits)
        
        val_loss = self.val_loss_metric.result().numpy()
        val_acc = self.val_acc_metric.result().numpy()
        
        with self.val_writer.as_default():
            tf.summary.scalar('epoch_loss', val_loss, step=epoch)
            tf.summary.scalar('epoch_acc', val_acc, step=epoch)
        
        # Save checkpoint if validation accuracy improved
        if val_acc > self.best_val_acc:
            self.best_val_acc = val_acc
            self.checkpoint_manager.save()
            print(f"Checkpoint saved: val_acc={val_acc:.4f}")
        
        return {
            'loss': float(val_loss),
            'accuracy': float(val_acc)
        }
    
    def fit(
        self,
        train_ds: tf.data.Dataset,
        val_ds: tf.data.Dataset,
        epochs: int,
        profile_epoch: Optional[int] = 1
    ):
        """Train model for specified epochs with profiling."""
        print(f"\nTraining for {epochs} epochs")
        print(f"Gradient accumulation steps: {self.gradient_accumulation_steps}")
        print(f"Mixed precision: {keras.mixed_precision.global_policy().name}")
        
        for epoch in range(1, epochs + 1):
            print(f"\nEpoch {epoch}/{epochs}")
            
            # Enable profiling for specified epoch
            if epoch == profile_epoch:
                tf.profiler.experimental.start(self.log_dir)
            
            # Train
            train_metrics = self.train_epoch(train_ds, epoch)
            print(f"Train - Loss: {train_metrics['loss']:.4f}, "
                  f"Acc: {train_metrics['accuracy']:.4f}, "
                  f"Time: {train_metrics['time']:.2f}s")
            
            # Validate
            val_metrics = self.validate(val_ds, epoch)
            print(f"Val   - Loss: {val_metrics['loss']:.4f}, "
                  f"Acc: {val_metrics['accuracy']:.4f}")
            
            # Stop profiling
            if epoch == profile_epoch:
                tf.profiler.experimental.stop()
                print(f"Profiling data saved to {self.log_dir}")
        
        print(f"\nTraining complete. Best val accuracy: {self.best_val_acc:.4f}")
        
        # Save final model
        final_path = os.path.join(self.checkpoint_dir, 'final_model')
        self.model.save(final_path)
        print(f"Final model saved to {final_path}")
```

Assemble the complete training pipeline with learning rate scheduling and gradient accumulation for memory-efficient training. The cosine annealing schedule gradually reduces the learning rate following a cosine curve, allowing the optimizer to escape local minima early in training while converging to sharp minima later. Warmup prevents the optimizer from diverging when starting from random initialization with a high learning rate that would otherwise cause exploding gradients.

```python
# tf_verification/training/run_training.py
import tensorflow as tf
from tensorflow import keras
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.resnet_cifar import create_model
from data.cifar_pipeline import CIFARDataPipeline
from training.trainer import MixedPrecisionTrainer


class CosineDecayWithWarmup(keras.optimizers.schedules.LearningRateSchedule):
    """Cosine annealing schedule with linear warmup.
    
    Warmup phase prevents gradient explosion from high initial learning rates.
    Cosine decay smoothly reduces learning rate to enable fine-grained convergence.
    """
    
    def __init__(
        self,
        initial_learning_rate: float,
        decay_steps: int,
        warmup_steps: int = 0,
        alpha: float = 0.0
    ):
        super().__init__()
        self.initial_learning_rate = initial_learning_rate
        self.decay_steps = decay_steps
        self.warmup_steps = warmup_steps
        self.alpha = alpha
    
    def __call__(self, step):
        # Linear warmup
        if step < self.warmup_steps:
            return self.initial_learning_rate * (step / self.warmup_steps)
        
        # Cosine decay
        completed_fraction = (step - self.warmup_steps) / (self.decay_steps - self.warmup_steps)
        completed_fraction = tf.clip_by_value(completed_fraction, 0.0, 1.0)
        cosine_decay = 0.5 * (1.0 + tf.cos(tf.constant(3.14159265359) * completed_fraction))
        decayed = (1 - self.alpha) * cosine_decay + self.alpha
        return self.initial_learning_rate * decayed
    
    def get_config(self):
        return {
            'initial_learning_rate': self.initial_learning_rate,
            'decay_steps': self.decay_steps,
            'warmup_steps': self.warmup_steps,
            'alpha': self.alpha
        }


def main():
    # Training configuration
    BATCH_SIZE = 128
    EPOCHS = 100
    INITIAL_LR = 0.1
    WEIGHT_DECAY = 0.0001
    GRADIENT_ACCUMULATION = 1
    PROFILE_EPOCH = 2
    
    # Enable XLA JIT compilation for operation fusion
    tf.config.optimizer.set_jit(True)
    
    # Create data pipeline
    print("Loading CIFAR-10 dataset...")
    data_pipeline = CIFARDataPipeline(
        batch_size=BATCH_SIZE,
        cache_dir='/tmp/tfds_cache'
    )
    
    train_ds = data_pipeline.load_dataset('train', augment=True)
    val_ds = data_pipeline.load_dataset('test', augment=False)
    
    dataset_info = data_pipeline.get_dataset_info()
    print(f"Dataset info: {dataset_info}")
    
    # Create model
    print("\nBuilding ResNet model...")
    model = create_model(num_classes=10)
    model.summary()
    
    # Calculate total training steps
    steps_per_epoch = dataset_info['train_samples'] // BATCH_SIZE
    total_steps = steps_per_epoch * EPOCHS
    warmup_steps = steps_per_epoch * 5  # 5 epoch warmup
    
    # Learning rate schedule
    lr_schedule = CosineDecayWithWarmup(
        initial_learning_rate=INITIAL_LR,
        decay_steps=total_steps,
        warmup_steps=warmup_steps,
        alpha=0.0
    )
    
    # Optimizer with weight decay
    optimizer = keras.optimizers.SGD(
        learning_rate=lr_schedule,
        momentum=0.9,
        nesterov=True
    )
    
    # Wrap optimizer for mixed precision
    optimizer = keras.mixed_precision.LossScaleOptimizer(optimizer)
    
    # Loss function
    loss_fn = keras.losses.SparseCategoricalCrossentropy(from_logits=True)
    
    # Create trainer
    trainer = MixedPrecisionTrainer(
        model=model,
        optimizer=optimizer,
        loss_fn=loss_fn,
        use_mixed_precision=True,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        log_dir='./tb_logs/experiment_1',
        checkpoint_dir='./checkpoints/experiment_1'
    )
    
    # Train model
    trainer.fit(
        train_ds=train_ds,
        val_ds=val_ds,
        epochs=EPOCHS,
        profile_epoch=PROFILE_EPOCH
    )


if __name__ == '__main__':
    main()
```

Execute the training pipeline and monitor GPU utilization through TensorBoard's profiler. The profiler exposes kernel launch overhead, memory copy latencies, and operation fusion opportunities that guide performance optimization. Launch training and observe convergence dynamics.

```bash
cd tf_verification
python training/run_training.py
```

While training executes, open TensorBoard in a separate terminal to monitor real-time metrics. Navigate to the Profile tab after the profiling epoch completes to analyze GPU kernel occupancy and memory bandwidth utilization. High kernel launch overhead indicates small batch sizes that amortize dispatch latency poorly. Memory bandwidth below 80% of hardware theoretical maximum suggests uncoalesced memory access patterns or insufficient operation fusion.

```bash
tensorboard --logdir=./tb_logs/experiment_1 --port=6006
```

Implement a validation harness that computes per-class precision, recall, and F1 scores beyond aggregate accuracy. Class-wise metrics expose model biases toward majority classes in imbalanced datasets and reveal systematic failures on specific categories that aggregate metrics obscure.

```python
# tf_verification/evaluation/metrics.py
import tensorflow as tf
from tensorflow import keras
import numpy as np
from typing import Dict, List
import json


class ClassificationMetrics:
    """Comprehensive classification metrics with per-class analysis.
    
    Computes:
    - Overall accuracy
    - Per-class precision, recall, F1
    - Confusion matrix
    - Top-k accuracy (k=1,5)
    """
    
    def __init__(self, num_classes: int, class_names: List[str]):
        self.num_classes = num_classes
        self.class_names = class_names
        self.confusion_matrix = np.zeros((num_classes, num_classes), dtype=np.int32)
        
    def update(self, labels: np.ndarray, predictions: np.ndarray):
        """Update confusion matrix with batch predictions."""
        for true_label, pred_label in zip(labels, predictions):
            self.confusion_matrix[true_label, pred_label] += 1
    
    def compute_metrics(self) -> Dict:
        """Compute all metrics from confusion matrix."""
        # Per-class metrics
        per_class_metrics = []
        
        for i in range(self.num_classes):
            tp = self.confusion_matrix[i, i]
            fp = self.confusion_matrix[:, i].sum() - tp
            fn = self.confusion_matrix[i, :].sum() - tp
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            per_class_metrics.append({
                'class': self.class_names[i],
                'precision': float(precision),
                'recall': float(recall),
                'f1': float(f1),
                'support': int(self.confusion_matrix[i, :].sum())
            })
        
        # Overall metrics
        accuracy = np.diag(self.confusion_matrix).sum() / self.confusion_matrix.sum()
        
        # Macro and weighted averages
        precisions = [m['precision'] for m in per_class_metrics]
        recalls = [m['recall'] for m in per_class_metrics]
        f1s = [m['f1'] for m in per_class_metrics]
        supports = [m['support'] for m in per_class_metrics]
        
        macro_precision = np.mean(precisions)
        macro_recall = np.mean(recalls)
        macro_f1 = np.mean(f1s)
        
        weighted_precision = np.average(precisions, weights=supports)
        weighted_recall = np.average(recalls, weights=supports)
        weighted_f1 = np.average(f1s, weights=supports)
        
        return {
            'accuracy': float(accuracy),
            'macro_precision': float(macro_precision),
            'macro_recall': float(macro_recall),
            'macro_f1': float(macro_f1),
            'weighted_precision': float(weighted_precision),
            'weighted_recall': float(weighted_recall),
            'weighted_f1': float(weighted_f1),
            'per_class': per_class_metrics,
            'confusion_matrix': self.confusion_matrix.tolist()
        }
    
    def print_report(self):
        """Print formatted classification report."""
        metrics = self.compute_metrics()
        
        print("\nClassification Report")
        print("=" * 70)
        print(f"{'Class':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
        print("-" * 70)
        
        for cls_metrics in metrics['per_class']:
            print(f"{cls_metrics['class']:<20} "
                  f"{cls_metrics['precision']:>10.4f} "
                  f"{cls_metrics['recall']:>10.4f} "
                  f"{cls_metrics['f1']:>10.4f} "
                  f"{cls_metrics['support']:>10}")
        
        print("-" * 70)
        print(f"{'Accuracy':<20} {metrics['accuracy']:>10.4f}")
        print(f"{'Macro avg':<20} "
              f"{metrics['macro_precision']:>10.4f} "
              f"{metrics['macro_recall']:>10.4f} "
              f"{metrics['macro_f1']:>10.4f}")
        print(f"{'Weighted avg':<20} "
              f"{metrics['weighted_precision']:>10.4f} "
              f"{metrics['weighted_recall']:>10.4f} "
              f"{metrics['weighted_f1']:>10.4f}")
        print("=" * 70)


def evaluate_model(
    model: keras.Model,
    dataset: tf.data.Dataset,
    class_names: List[str]
) -> Dict:
    """Evaluate model and return comprehensive metrics."""
    metrics = ClassificationMetrics(
        num_classes=len(class_names),
        class_names=class_names
    )
    
    for images, labels in dataset:
        logits = model(images, training=False)
        predictions = tf.argmax(logits, axis=1).numpy()
        metrics.update(labels.numpy(), predictions)
    
    metrics.print_report()
    return metrics.compute_metrics()
```

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Systematically tune hyperparameters through grid search over learning rate, weight decay, and batch size, measuring their interaction effects on convergence speed and final validation accuracy. Hyperparameter optimization represents a high-dimensional, non-convex search problem where interactions between parameters create complex fitness landscapes. Learning rate scales gradient updates—too high causes divergence, too low yields glacial convergence. Weight decay (L2 regularization) penalizes large weights to prevent overfitting but can starve capacity-limited models. Batch size controls gradient estimation variance and hardware utilization—larger batches reduce noise but require learning rate scaling to maintain optimization dynamics.

Implement a hyperparameter sweep framework that trains multiple configurations in parallel across available GPUs, aggregating results into a structured benchmark report. TensorFlow's distribution strategy API abstracts data parallelism across devices, automatically sharding batches and synchronizing gradients through collective all-reduce operations.

```python
# tf_verification/training/hyperparameter_sweep.py
import tensorflow as tf
from tensorflow import keras
import itertools
import json
import os
from typing import Dict, List, Tuple
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.resnet_cifar import create_model
from data.cifar_pipeline import CIFARDataPipeline
from training.trainer import MixedPrecisionTrainer, CosineDecayWithWarmup


class HyperparameterSweep:
    """Systematic hyperparameter search with distributed training.
    
    Sweeps over:
    - Learning rate: [0.01, 0.05, 0.1, 0.2]
    - Weight decay: [0.0, 0.0001, 0.0005]
    - Batch size: [64, 128, 256]
    
    Each configuration trains for reduced epochs (20) to accelerate search.
    Best configuration identified by validation accuracy and then trained fully.
    """
    
    def __init__(
        self,
        output_dir: str = './hyperparameter_sweep',
        epochs: int = 20
    ):
        self.output_dir = output_dir
        self.epochs = epochs
        os.makedirs(output_dir, exist_ok=True)
        
        # Hyperparameter grid
        self.learning_rates = [0.01, 0.05, 0.1, 0.2]
        self.weight_decays = [0.0, 0.0001, 0.0005]
        self.batch_sizes = [64, 128, 256]
        
        self.results = []
    
    def _train_config(
        self,
        config: Dict,
        config_id: int
    ) -> Dict:
        """Train a single hyperparameter configuration."""
        print(f"\n{'='*70}")
        print(f"Configuration {config_id}: {config}")
        print(f"{'='*70}")
        
        # Clear backend to free GPU memory
        keras.backend.clear_session()
        
        # Create data pipeline with config batch size
        data_pipeline = CIFARDataPipeline(batch_size=config['batch_size'])
        train_ds = data_pipeline.load_dataset('train', augment=True)
        val_ds = data_pipeline.load_dataset('test', augment=False)
        
        # Create model
        model = create_model(num_classes=10)
        
        # Calculate steps
        steps_per_epoch = 50000 // config['batch_size']
        total_steps = steps_per_epoch * self.epochs
        warmup_steps = steps_per_epoch * 3
        
        # Learning rate schedule
        lr_schedule = CosineDecayWithWarmup(
            initial_learning_rate=config['learning_rate'],
            decay_steps=total_steps,
            warmup_steps=warmup_steps,
            alpha=0.0
        )
        
        # Optimizer
        optimizer = keras.optimizers.SGD(
            learning_rate=lr_schedule,
            momentum=0.9,
            nesterov=True,
            weight_decay=config['weight_decay']
        )
        optimizer = keras.mixed_precision.LossScaleOptimizer(optimizer)
        
        # Loss function
        loss_fn = keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        
        # Create trainer
        log_dir = os.path.join(self.output_dir, f'config_{config_id}')
        checkpoint_dir = os.path.join(self.output_dir, f'ckpt_{config_id}')
        
        trainer = MixedPrecisionTrainer(
            model=model,
            optimizer=optimizer,
            loss_fn=loss_fn,
            use_mixed_precision=True,
            gradient_accumulation_steps=1,
            log_dir=log_dir,
            checkpoint_dir=checkpoint_dir
        )
        
        # Train
        trainer.fit(
            train_ds=train_ds,
            val_ds=val_ds,
            epochs=self.epochs,
            profile_epoch=None  # Skip profiling during sweep
        )
        
        # Return final validation accuracy
        return {
            'config_id': config_id,
            'config': config,
            'best_val_acc': float(trainer.best_val_acc)
        }
    
    def run_sweep(self) -> List[Dict]:
        """Execute hyperparameter sweep across all configurations."""
        # Generate all configurations
        configs = [
            {
                'learning_rate': lr,
                'weight_decay': wd,
                'batch_size': bs
            }
            for lr, wd, bs in itertools.product(
                self.learning_rates,
                self.weight_decays,
                self.batch_sizes
            )
        ]
        
        print(f"\nRunning hyperparameter sweep: {len(configs)} configurations")
        print(f"Training for {self.epochs} epochs per configuration")
        
        # Train each configuration
        for config_id, config in enumerate(configs):
            result = self._train_config(config, config_id)
            self.results.append(result)
            
            # Save intermediate results
            with open(os.path.join(self.output_dir, 'results.json'), 'w') as f:
                json.dump(self.results, f, indent=2)
        
        # Sort results by validation accuracy
        self.results.sort(key=lambda x: x['best_val_acc'], reverse=True)
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _print_summary(self):
        """Print formatted hyperparameter sweep summary."""
        print("\n" + "="*90)
        print("HYPERPARAMETER SWEEP RESULTS")
        print("="*90)
        print(f"{'Rank':<6} {'LR':<8} {'WD':<10} {'Batch':<8} {'Val Acc':<10}")
        print("-"*90)
        
        for rank, result in enumerate(self.results[:10], 1):  # Top 10
            config = result['config']
            print(f"{rank:<6} "
                  f"{config['learning_rate']:<8.4f} "
                  f"{config['weight_decay']:<10.6f} "
                  f"{config['batch_size']:<8} "
                  f"{result['best_val_acc']:<10.4f}")
        
        print("="*90)
        print(f"\nBest configuration:")
        best = self.results[0]
        print(json.dumps(best['config'], indent=2))
        print(f"Validation accuracy: {best['best_val_acc']:.4f}")
        print(f"\nFull results saved to {os.path.join(self.output_dir, 'results.json')}")


def main():
    sweep = HyperparameterSweep(
        output_dir='./hyperparameter_sweep',
        epochs=20
    )
    results = sweep.run_sweep()


if __name__ == '__main__':
    main()
```

Benchmark inference latency and throughput across batch sizes to characterize model serving performance. Serving latency determines user-facing response times in production systems, where p99 latency constraints dictate maximum acceptable delay. Throughput measures total system capacity—requests per second that a single GPU instance can sustain. These metrics trade off: larger batch sizes amortize kernel launch overhead and increase throughput, but accumulating requests to fill batches increases per-request latency.

```python
# tf_verification/evaluation/benchmark.py
import tensorflow as tf
from tensorflow import keras
import numpy as np
import time
from typing import Dict, List
import json
import os


class InferenceBenchmark:
    """Comprehensive inference latency and throughput benchmarking.
    
    Measures:
    - Latency (mean, median, p95, p99) across batch sizes
    - Throughput (samples/sec) across batch sizes
    - GPU memory consumption
    - Warm-up effects and cache behavior
    """
    
    def __init__(
        self,
        model: keras.Model,
        input_shape: tuple = (32, 32, 3),
        warmup_iterations: int = 50,
        benchmark_iterations: int = 200
    ):
        self.model = model
        self.input_shape = input_shape
        self.warmup_iterations = warmup_iterations
        self.benchmark_iterations = benchmark_iterations
        
        # Compile model as tf.function for optimized execution
        self.inference_fn = tf.function(
            lambda x: self.model(x, training=False),
            input_signature=[tf.TensorSpec(
                shape=[None] + list(input_shape),
                dtype=tf.float32
            )]
        )
    
    def _generate_batch(self, batch_size: int) -> tf.Tensor:
        """Generate random input batch."""
        return tf.random.normal([batch_size] + list(self.input_shape))
    
    def benchmark_batch_size(self, batch_size: int) -> Dict:
        """Benchmark single batch size configuration."""
        print(f"\nBenchmarking batch_size={batch_size}")
        
        # Generate input batch
        inputs = self._generate_batch(batch_size)
        
        # Warm-up to populate GPU caches and compile graphs
        print(f"  Warming up ({self.warmup_iterations} iterations)...")
        for _ in range(self.warmup_iterations):
            _ = self.inference_fn(inputs)
        
        # Benchmark
        print(f"  Benchmarking ({self.benchmark_iterations} iterations)...")
        latencies = []
        
        for _ in range(self.benchmark_iterations):
            start = time.perf_counter()
            _ = self.inference_fn(inputs)
            # Synchronize to ensure GPU work completes
            tf.test.experimental.sync_devices()
            latency = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(latency)
        
        # Compute statistics
        latencies = np.array(latencies)
        mean_latency = np.mean(latencies)
        median_latency = np.median(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        std_latency = np.std(latencies)
        
        # Throughput calculation
        throughput = (batch_size * self.benchmark_iterations) / (np.sum(latencies) / 1000)
        
        return {
            'batch_size': batch_size,
            'mean_latency_ms': float(mean_latency),
            'median_latency_ms': float(median_latency),
            'p95_latency_ms': float(p95_latency),
            'p99_latency_ms': float(p99_latency),
            'std_latency_ms': float(std_latency),
            'throughput_samples_per_sec': float(throughput)
        }
    
    def run_benchmark_suite(
        self,
        batch_sizes: List[int] = [1, 2, 4, 8, 16, 32, 64, 128]
    ) -> List[Dict]:
        """Run benchmarks across multiple batch sizes."""
        results = []
        
        print("\n" + "="*70)
        print("INFERENCE BENCHMARK SUITE")
        print("="*70)
        
        for batch_size in batch_sizes:
            result = self.benchmark_batch_size(batch_size)
            results.append(result)
        
        self._print_summary(results)
        return results
    
    def _print_summary(self, results: List[Dict]):
        """Print formatted benchmark summary."""
        print("\n" + "="*90)
        print("BENCHMARK RESULTS")
        print("="*90)
        print(f"{'Batch':<8} {'Mean (ms)':<12} {'Median (ms)':<12} "
              f"{'P95 (ms)':<12} {'P99 (ms)':<12} {'Throughput':<15}")
        print("-"*90)
        
        for r in results:
            print(f"{r['batch_size']:<8} "
                  f"{r['mean_latency_ms']:<12.3f} "
                  f"{r['median_latency_ms']:<12.3f} "
                  f"{r['p95_latency_ms']:<12.3f} "
                  f"{r['p99_latency_ms']:<12.3f} "
                  f"{r['throughput_samples_per_sec']:<15.1f}")
        
        print("="*90)


def benchmark_model(model_path: str, output_path: str = './benchmark_results.json'):
    """Load model and run comprehensive benchmark suite."""
    print(f"Loading model from {model_path}")
    model = keras.models.load_model(model_path)
    
    benchmark = InferenceBenchmark(
        model=model,
        input_shape=(32, 32, 3),
        warmup_iterations=50,
        benchmark_iterations=200
    )
    
    results = benchmark.run_benchmark_suite(
        batch_sizes=[1, 2, 4, 8, 16, 32, 64, 128, 256]
    )
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_path}")
    return results


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <model_path>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    benchmark_model(model_path)


if __name__ == '__main__':
    main()
```

Execute the hyperparameter sweep to identify optimal training configuration. This sweep runs 36 configurations (4 learning rates × 3 weight decays × 3 batch sizes) for 20 epochs each, requiring approximately 12–18 hours on a single GPU depending on hardware generation. For faster iteration during development, reduce the epochs parameter to 10 or run only a subset of configurations.

```bash
cd tf_verification
python training/hyperparameter_sweep.py
```

After identifying the best configuration from the sweep, train a full 100-epoch model using those hyperparameters, then benchmark its inference performance across batch sizes.

```bash
# Train final model with best hyperparameters (update config in run_training.py)
python training/run_training.py

# Benchmark inference
python evaluation/benchmark.py checkpoints/experiment_1/final_model
```

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Subject your trained model to adversarial inputs, distribution shifts, and numerical edge cases that expose failure modes invisible during standard validation. Production ML systems encounter inputs from distributions arbitrarily far from training data—corrupted images, adversarial perturbations, out-of-distribution samples that confidently misclassify. Robust models degrade gracefully under distribution shift, maintain calibrated uncertainty estimates, and detect anomalous inputs rather than hallucinating confident predictions.

Implement adversarial attack generation using the Fast Gradient Sign Method (FGSM), which constructs minimal perturbations that maximize classification loss. FGSM computes the gradient of loss with respect to input pixels, then perturbs the image in the direction that increases loss. The perturbation magnitude epsilon controls attack strength—small epsilon produces imperceptible changes that flip predictions, exposing model brittleness.

```python
# tf_verification/evaluation/adversarial.py
import tensorflow as tf
from tensorflow import keras
import numpy as np
from typing import Tuple, Dict
import matplotlib.pyplot as plt


class AdversarialAttacker:
    """Adversarial attack generation and robustness evaluation.
    
    Implements:
    - Fast Gradient Sign Method (FGSM)
    - Projected Gradient Descent (PGD)
    - Robustness metrics across epsilon values
    """
    
    def __init__(
        self,
        model: keras.Model,
        loss_fn: keras.losses.Loss
    ):
        self.model = model
        self.loss_fn = loss_fn
    
    def fgsm_attack(
        self,
        images: tf.Tensor,
        labels: tf.Tensor,
        epsilon: float = 0.01
    ) -> Tuple[tf.Tensor, tf.Tensor]:
        """Fast Gradient Sign Method attack.
        
        Generates adversarial examples by perturbing inputs in the direction
        of the gradient that maximizes loss. Perturbation magnitude controlled
        by epsilon parameter.
        
        Args:
            images: Clean input images [batch, height, width, channels]
            labels: True labels [batch]
            epsilon: Maximum perturbation magnitude in [0, 1] range
            
        Returns:
            Tuple of (adversarial_images, perturbations)
        """
        images = tf.cast(images, tf.float32)
        labels = tf.cast(labels, tf.int32)
        
        with tf.GradientTape() as tape:
            tape.watch(images)
            predictions = self.model(images, training=False)
            loss = self.loss_fn(labels, predictions)
        
        # Compute gradient of loss w.r.t. input
        gradients = tape.gradient(loss, images)
        
        # Generate perturbation using sign of gradient
        perturbations = epsilon * tf.sign(gradients)
        
        # Create adversarial examples
        adversarial_images = images + perturbations
        
        # Clip to valid pixel range (assuming normalized inputs)
        adversarial_images = tf.clip_by_value(adversarial_images, -3.0, 3.0)
        
        return adversarial_images, perturbations
    
    def pgd_attack(
        self,
        images: tf.Tensor,
        labels: tf.Tensor,
        epsilon: float = 0.01,
        alpha: float = 0.002,
        iterations: int = 10
    ) -> tf.Tensor:
        """Projected Gradient Descent attack.
        
        Iteratively applies FGSM with smaller step size and projects back
        to epsilon ball after each step. More powerful than single-step FGSM.
        
        Args:
            images: Clean input images
            labels: True labels
            epsilon: Maximum total perturbation
            alpha: Step size per iteration
            iterations: Number of attack iterations
            
        Returns:
            Adversarial images
        """
        images = tf.cast(images, tf.float32)
        labels = tf.cast(labels, tf.int32)
        
        # Initialize with random perturbation
        adversarial_images = images + tf.random.uniform(
            tf.shape(images),
            minval=-epsilon,
            maxval=epsilon
        )
        adversarial_images = tf.clip_by_value(adversarial_images, -3.0, 3.0)
        
        # Iteratively perturb
        for _ in range(iterations):
            with tf.GradientTape() as tape:
                tape.watch(adversarial_images)
                predictions = self.model(adversarial_images, training=False)
                loss = self.loss_fn(labels, predictions)
            
            gradients = tape.gradient(loss, adversarial_images)
            
            # Take step in gradient direction
            adversarial_images = adversarial_images + alpha * tf.sign(gradients)
            
            # Project back to epsilon ball around original image
            perturbations = adversarial_images - images
            perturbations = tf.clip_by_value(perturbations, -epsilon, epsilon)
            adversarial_images = images + perturbations
            
            # Clip to valid range
            adversarial_images = tf.clip_by_value(adversarial_images, -3.0, 3.0)
        
        return adversarial_images
    
    def evaluate_robustness(
        self,
        dataset: tf.data.Dataset,
        epsilons: list = [0.0, 0.01, 0.02, 0.05, 0.1],
        attack_type: str = 'fgsm'
    ) -> Dict:
        """Evaluate model robustness across epsilon values.
        
        Returns:
            Dictionary mapping epsilon to accuracy metrics
        """
        results = {}
        
        for epsilon in epsilons:
            print(f"\nEvaluating epsilon={epsilon}")
            correct = 0
            total = 0
            
            for images, labels in dataset:
                if attack_type == 'fgsm':
                    if epsilon == 0.0:
                        adversarial_images = images
                    else:
                        adversarial_images, _ = self.fgsm_attack(images, labels, epsilon)
                elif attack_type == 'pgd':
                    if epsilon == 0.0:
                        adversarial_images = images
                    else:
                        adversarial_images = self.pgd_attack(images, labels, epsilon)
                else:
                    raise ValueError(f"Unknown attack type: {attack_type}")
                
                predictions = self.model(adversarial_images, training=False)
                predicted_labels = tf.argmax(predictions, axis=1)
                
                correct += tf.reduce_sum(
                    tf.cast(predicted_labels == labels, tf.int32)
                ).numpy()
                total += len(labels)
            
            accuracy = correct / total
            results[epsilon] = {
                'accuracy': float(accuracy),
                'samples': total
            }
            
            print(f"  Accuracy: {accuracy:.4f}")
        
        return results
    
    def visualize_attack(
        self,
        images: tf.Tensor,
        labels: tf.Tensor,
        epsilon: float = 0.03,
        num_samples: int = 5,
        save_path: str = './adversarial_examples.png'
    ):
        """Visualize adversarial examples side-by-side with originals."""
        adversarial_images, perturbations = self.fgsm_attack(
            images[:num_samples],
            labels[:num_samples],
            epsilon
        )
        
        # Get predictions
        clean_preds = tf.argmax(self.model(images[:num_samples], training=False), axis=1)
        adv_preds = tf.argmax(self.model(adversarial_images, training=False), axis=1)
        
        # Denormalize for visualization (assuming CIFAR normalization)
        mean = tf.constant([0.4914, 0.4822, 0.4465])
        std = tf.constant([0.2470, 0.2435, 0.2616])
        
        def denormalize(img):
            img = img * std + mean
            img = tf.clip_by_value(img, 0, 1)
            return img
        
        # Create figure
        fig, axes = plt.subplots(num_samples, 4, figsize=(12, 3*num_samples))
        
        for i in range(num_samples):
            # Original image
            axes[i, 0].imshow(denormalize(images[i]))
            axes[i, 0].set_title(f'Original\nPred: {clean_preds[i].numpy()}')
            axes[i, 0].axis('off')
            
            # Perturbation (amplified for visibility)
            pert = perturbations[i]
            pert = (pert - tf.reduce_min(pert)) / (tf.reduce_max(pert) - tf.reduce_min(pert))
            axes[i, 1].imshow(pert)
            axes[i, 1].set_title(f'Perturbation\n(amplified)')
            axes[i, 1].axis('off')
            
            # Adversarial image
            axes[i, 2].imshow(denormalize(adversarial_images[i]))
            axes[i, 2].set_title(f'Adversarial\nPred: {adv_preds[i].numpy()}')
            axes[i, 2].axis('off')
            
            # Difference
            diff = tf.abs(adversarial_images[i] - images[i])
            diff = (diff - tf.reduce_min(diff)) / (tf.reduce_max(diff) - tf.reduce_min(diff))
            axes[i, 3].imshow(diff)
            axes[i, 3].set_title(f'Difference\nTrue: {labels[i].numpy()}')
            axes[i, 3].axis('off')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Visualization saved to {save_path}")
```

Test model behavior under input corruptions that simulate real-world data quality degradation—Gaussian noise, JPEG compression artifacts, blur, and brightness shifts. These corruptions measure robustness to natural distribution shift without adversarial intent, exposing whether the model learned robust features or memorized spurious correlations in the training distribution.

```python
# tf_verification/evaluation/corruptions.py
import tensorflow as tf
import numpy as np
from typing import Dict, Callable


class InputCorruptions:
    """Input corruption functions for robustness testing.
    
    Implements common corruptions:
    - Gaussian noise
    - JPEG compression artifacts
    - Gaussian blur
    - Brightness/contrast shifts
    - Pixel dropout
    """
    
    @staticmethod
    def gaussian_noise(images: tf.Tensor, severity: float = 0.1) -> tf.Tensor:
        """Add Gaussian noise with specified standard deviation."""
        noise = tf.random.normal(tf.shape(images), mean=0.0, stddev=severity)
        corrupted = images + noise
        return tf.clip_by_value(corrupted, -3.0, 3.0)
    
    @staticmethod
    def gaussian_blur(images: tf.Tensor, severity: int = 3) -> tf.Tensor:
        """Apply Gaussian blur with kernel size."""
        # Simple box blur approximation
        kernel_size = severity * 2 + 1
        kernel = tf.ones([kernel_size, kernel_size, 3, 1]) / (kernel_size ** 2)
        
        # Depthwise convolution for per-channel blur
        blurred = tf.nn.depthwise_conv2d(
            images,
            kernel,
            strides=[1, 1, 1, 1],
            padding='SAME'
        )
        return blurred
    
    @staticmethod
    def brightness_shift(images: tf.Tensor, severity: float = 0.3) -> tf.Tensor:
        """Shift brightness by additive constant."""
        shift = tf.random.uniform([], -severity, severity)
        corrupted = images + shift
        return tf.clip_by_value(corrupted, -3.0, 3.0)
    
    @staticmethod
    def contrast_shift(images: tf.Tensor, severity: float = 0.5) -> tf.Tensor:
        """Scale contrast by multiplicative factor."""
        factor = tf.random.uniform([], 1.0 - severity, 1.0 + severity)
        mean = tf.reduce_mean(images, axis=[1, 2, 3], keepdims=True)
        corrupted = (images - mean) * factor + mean
        return tf.clip_by_value(corrupted, -3.0, 3.0)
    
    @staticmethod
    def pixel_dropout(images: tf.Tensor, severity: float = 0.1) -> tf.Tensor:
        """Randomly zero out pixels."""
        mask = tf.random.uniform(tf.shape(images)) > severity
        return images * tf.cast(mask, tf.float32)
    
    @staticmethod
    def get_corruption_suite() -> Dict[str, Callable]:
        """Return dictionary of all corruption functions."""
        return {
            'gaussian_noise': InputCorruptions.gaussian_noise,
            'gaussian_blur': InputCorruptions.gaussian_blur,
            'brightness_shift': InputCorruptions.brightness_shift,
            'contrast_shift': InputCorruptions.contrast_shift,
            'pixel_dropout': InputCorruptions.pixel_dropout
        }


def evaluate_corruption_robustness(
    model: tf.keras.Model,
    dataset: tf.data.Dataset,
    corruption_name: str,
    severities: list = [0.05, 0.1, 0.2, 0.3]
) -> Dict:
    """Evaluate model accuracy under varying corruption severity."""
    corruptions = InputCorruptions.get_corruption_suite()
    
    if corruption_name not in corruptions:
        raise ValueError(f"Unknown corruption: {corruption_name}")
    
    corruption_fn = corruptions[corruption_name]
    results = {}
    
    print(f"\nEvaluating corruption: {corruption_name}")
    
    for severity in severities:
        print(f"  Severity: {severity}")
        correct = 0
        total = 0
        
        for images, labels in dataset:
            # Apply corruption
            corrupted_images = corruption_fn(images, severity)
            
            # Get predictions
            predictions = model(corrupted_images, training=False)
            predicted_labels = tf.argmax(predictions, axis=1)
            
            correct += tf.reduce_sum(
                tf.cast(predicted_labels == labels, tf.int32)
            ).numpy()
            total += len(labels)
        
        accuracy = correct / total
        results[severity] = {
            'accuracy': float(accuracy),
            'samples': total
        }
        
        print(f"    Accuracy: {accuracy:.4f}")
    
    return results
```

Implement uncertainty quantification through Monte Carlo dropout, which approximates Bayesian inference by treating dropout as a probabilistic model. During inference, enable dropout and perform multiple forward passes to obtain prediction distributions. High variance in predictions indicates epistemic uncertainty—the model's lack of knowledge about the input—while low variance suggests confident predictions.

```python
# tf_verification/evaluation/uncertainty.py
import tensorflow as tf
from tensorflow import keras
import numpy as np
from typing import Tuple, Dict


class UncertaintyQuantifier:
    """Uncertainty estimation via Monte Carlo dropout.
    
    Enables epistemic uncertainty quantification by:
    1. Keeping dropout enabled during inference
    2. Running multiple stochastic forward passes
    3. Computing prediction mean and variance
    """
    
    def __init__(
        self,
        model: keras.Model,
        num_samples: int = 50
    ):
        self.model = model
        self.num_samples = num_samples
    
    def predict_with_uncertainty(
        self,
        images: tf.Tensor
    ) -> Tuple[tf.Tensor, tf.Tensor, tf.Tensor]:
        """Compute predictions with uncertainty estimates.
        
        Args:
            images: Input batch [batch, height, width, channels]
            
        Returns:
            Tuple of (mean_predictions, prediction_variance, epistemic_uncertainty)
        """
        predictions = []
        
        # Run multiple stochastic forward passes
        for _ in range(self.num_samples):
            pred = self.model(images, training=True)  # Keep dropout enabled
            predictions.append(tf.nn.softmax(pred))
        
        # Stack predictions [num_samples, batch, num_classes]
        predictions = tf.stack(predictions, axis=0)
        
        # Compute statistics
        mean_predictions = tf.reduce_mean(predictions, axis=0)
        prediction_variance = tf.reduce_mean(
            tf.math.reduce_variance(predictions, axis=0),
            axis=1
        )
        
        # Epistemic uncertainty via predictive entropy
        epistemic_uncertainty = -tf.reduce_sum(
            mean_predictions * tf.math.log(mean_predictions + 1e-10),
            axis=1
        )
        
        return mean_predictions, prediction_variance, epistemic_uncertainty
    
    def detect_out_of_distribution(
        self,
        images: tf.Tensor,
        threshold_percentile: float = 95.0
    ) -> Tuple[tf.Tensor, float]:
        """Detect out-of-distribution samples via uncertainty threshold.
        
        Args:
            images: Input batch
            threshold_percentile: Percentile for OOD threshold
            
        Returns:
            Tuple of (is_ood_mask, uncertainty_threshold)
        """
        _, _, uncertainty = self.predict_with_uncertainty(images)
        
        # Compute threshold from uncertainty distribution
        threshold = np.percentile(
            uncertainty.numpy(),
            threshold_percentile
        )
        
        # Flag samples exceeding threshold as OOD
        is_ood = uncertainty > threshold
        
        return is_ood, float(threshold)
    
    def evaluate_calibration(
        self,
        dataset: tf.data.Dataset,
        num_bins: int = 10
    ) -> Dict:
        """Evaluate prediction calibration via reliability diagram.
        
        Well-calibrated models produce confidence scores matching empirical accuracy.
        Returns ECE (Expected Calibration Error) and bin statistics.
        """
        confidences = []
        accuracies = []
        
        for images, labels in dataset:
            mean_preds, _, _ = self.predict_with_uncertainty(images)
            
            predicted_classes = tf.argmax(mean_preds, axis=1)
            max_confidences = tf.reduce_max(mean_preds, axis=1)
            correct = tf.cast(predicted_classes == labels, tf.float32)
            
            confidences.extend(max_confidences.numpy())
            accuracies.extend(correct.numpy())
        
        confidences = np.array(confidences)
        accuracies = np.array(accuracies)
        
        # Bin predictions by confidence
        bins = np.linspace(0, 1, num_bins + 1)
        bin_indices = np.digitize(confidences, bins) - 1
        bin_indices = np.clip(bin_indices, 0, num_bins - 1)
        
        # Compute per-bin statistics
        bin_stats = []
        total_ece = 0.0
        
        for i in range(num_bins):
            bin_mask = bin_indices == i
            bin_size = np.sum(bin_mask)
            
            if bin_size > 0:
                bin_confidence = np.mean(confidences[bin_mask])
                bin_accuracy = np.mean(accuracies[bin_mask])
                bin_ece = np.abs(bin_confidence - bin_accuracy) * bin_size
                
                total_ece += bin_ece
                
                bin_stats.append({
                    'bin': i,
                    'confidence': float(bin_confidence),
                    'accuracy': float(bin_accuracy),
                    'size': int(bin_size)
                })
        
        # Normalize ECE by total samples
        expected_calibration_error = total_ece / len(confidences)
        
        return {
            'expected_calibration_error': float(expected_calibration_error),
            'bin_stats': bin_stats,
            'total_samples': len(confidences)
        }
```

Construct a comprehensive robustness test suite that executes adversarial attacks, corruption tests, and uncertainty analysis, aggregating results into a structured report.

```python
# tf_verification/evaluation/robustness_suite.py
import tensorflow as tf
from tensorflow import keras
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.adversarial import AdversarialAttacker
from evaluation.corruptions import InputCorruptions, evaluate_corruption_robustness
from evaluation.uncertainty import UncertaintyQuantifier
from data.cifar_pipeline import CIFARDataPipeline


class RobustnessTestSuite:
    """Comprehensive robustness evaluation suite.
    
    Executes:
    1. Adversarial attack robustness (FGSM, PGD)
    2. Natural corruption robustness (noise, blur, etc.)
    3. Uncertainty quantification and calibration
    4. Out-of-distribution detection
    """
    
    def __init__(
        self,
        model: keras.Model,
        output_dir: str = './robustness_results'
    ):
        self.model = model
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize evaluators
        self.loss_fn = keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        self.adversarial = AdversarialAttacker(model, self.loss_fn)
        self.uncertainty = UncertaintyQuantifier(model, num_samples=50)
        
        # Load test dataset
        data_pipeline = CIFARDataPipeline(batch_size=128)
        self.test_ds = data_pipeline.load_dataset('test', augment=False)
    
    def run_full_suite(self) -> Dict:
        """Execute complete robustness test suite."""
        results = {}
        
        print("\n" + "="*70)
        print("ROBUSTNESS TEST SUITE")
        print("="*70)
        
        # 1. Adversarial robustness
        print("\n[1/4] Evaluating adversarial robustness...")
        results['adversarial_fgsm'] = self.adversarial.evaluate_robustness(
            self.test_ds,
            epsilons=[0.0, 0.005, 0.01, 0.02, 0.03, 0.05],
            attack_type='fgsm'
        )
        
        results['adversarial_pgd'] = self.adversarial.evaluate_robustness(
            self.test_ds,
            epsilons=[0.0, 0.005, 0.01, 0.02, 0.03],
            attack_type='pgd'
        )
        
        # Visualize adversarial examples
        for images, labels in self.test_ds.take(1):
            self.adversarial.visualize_attack(
                images,
                labels,
                epsilon=0.03,
                num_samples=5,
                save_path=os.path.join(self.output_dir, 'adversarial_examples.png')
            )
        
        # 2. Corruption robustness
        print("\n[2/4] Evaluating corruption robustness...")
        corruptions = InputCorruptions.get_corruption_suite()
        results['corruptions'] = {}
        
        for corruption_name in corruptions.keys():
            corruption_results = evaluate_corruption_robustness(
                self.model,
                self.test_ds,
                corruption_name,
                severities=[0.05, 0.1, 0.2, 0.3]
            )
            results['corruptions'][corruption_name] = corruption_results
        
        # 3. Uncertainty quantification
        print("\n[3/4] Evaluating uncertainty quantification...")
        calibration = self.uncertainty.evaluate_calibration(
            self.test_ds,
            num_bins=10
        )
        results['calibration'] = calibration
        
        print(f"Expected Calibration Error: {calibration['expected_calibration_error']:.4f}")
        
        # 4. Summary statistics
        print("\n[4/4] Computing summary statistics...")
        results['summary'] = self._compute_summary(results)
        
        # Save results
        output_path = os.path.join(self.output_dir, 'robustness_results.json')
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {output_path}")
        
        self._print_summary(results['summary'])
        
        return results
    
    def _compute_summary(self, results: Dict) -> Dict:
        """Compute aggregate robustness metrics."""
        # Clean accuracy (epsilon=0)
        clean_acc = results['adversarial_fgsm'][0.0]['accuracy']
        
        # Average adversarial accuracy
        fgsm_accs = [v['accuracy'] for k, v in results['adversarial_fgsm'].items() if k > 0]
        pgd_accs = [v['accuracy'] for k, v in results['adversarial_pgd'].items() if k > 0]
        
        avg_fgsm = sum(fgsm_accs) / len(fgsm_accs) if fgsm_accs else 0.0
        avg_pgd = sum(pgd_accs) / len(pgd_accs) if pgd_accs else 0.0
        
        # Average corruption accuracy
        corruption_accs = []
        for corruption_results in results['corruptions'].values():
            accs = [v['accuracy'] for v in corruption_results.values()]
            corruption_accs.extend(accs)
        
        avg_corruption = sum(corruption_accs) / len(corruption_accs) if corruption_accs else 0.0
        
        # Calibration error
        ece = results['calibration']['expected_calibration_error']
        
        return {
            'clean_accuracy': float(clean_acc),
            'avg_fgsm_accuracy': float(avg_fgsm),
            'avg_pgd_accuracy': float(avg_pgd),
            'avg_corruption_accuracy': float(avg_corruption),
            'expected_calibration_error': float(ece),
            'robustness_score': float((avg_fgsm + avg_pgd + avg_corruption) / 3.0)
        }
    
    def _print_summary(self, summary: Dict):
        """Print formatted robustness summary."""
        print("\n" + "="*70)
        print("ROBUSTNESS SUMMARY")
        print("="*70)
        print(f"Clean Accuracy:              {summary['clean_accuracy']:.4f}")
        print(f"Avg FGSM Accuracy:           {summary['avg_fgsm_accuracy']:.4f}")
        print(f"Avg PGD Accuracy:            {summary['avg_pgd_accuracy']:.4f}")
        print(f"Avg Corruption Accuracy:     {summary['avg_corruption_accuracy']:.4f}")
        print(f"Expected Calibration Error:  {summary['expected_calibration_error']:.4f}")
        print(f"Overall Robustness Score:    {summary['robustness_score']:.4f}")
        print("="*70)


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python robustness_suite.py <model_path>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    print(f"Loading model from {model_path}")
    model = keras.models.load_model(model_path)
    
    suite = RobustnessTestSuite(
        model=model,
        output_dir='./robustness_results'
    )
    
    results = suite.run_full_suite()


if __name__ == '__main__':
    main()
```

Execute the complete robustness test suite on your trained model. This comprehensive evaluation runs adversarial attacks, corruption tests, uncertainty quantification, and calibration analysis, producing a detailed report of failure modes and edge cases.

```bash
cd tf_verification
python evaluation/robustness_suite.py checkpoints/experiment_1/final_model
```

## ML Diagnostic Cheat Sheet & Verification Checklist

This diagnostic reference consolidates essential TensorFlow profiling commands, GPU memory debugging procedures, and systematic verification protocols for production ML systems.

**GPU Memory Profiling and Debugging**

Query GPU memory allocation to diagnose out-of-memory errors and identify memory leaks. TensorFlow's memory allocator pre-allocates GPU memory and fragments over time, requiring periodic profiling to track utilization.

```python
# Query available GPU devices and memory
gpus = tf.config.list_physical_devices('GPU')
for gpu in gpus:
    details = tf.config.experimental.get_device_details(gpu)
    print(f"Device: {gpu.name}")
    print(f"  Compute capability: {details.get('compute_capability')}")

# Enable memory growth to prevent pre-allocation
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)

# Set explicit memory limit (in MB)
tf.config.set_logical_device_configuration(
    gpus[0],
    [tf.config.LogicalDeviceConfiguration(memory_limit=4096)]
)

# Log memory allocations during execution
tf.debugging.set_log_device_placement(True)

# Profile memory usage during training
with tf.profiler.experimental.Profile('./profiler_logs'):
    # Training code here
    pass
```

**TensorBoard Profiling Integration**

Launch TensorBoard with profiler plugin to visualize kernel execution timelines, memory bandwidth utilization, and operation placement decisions.

```bash
# Start TensorBoard with profiler
tensorboard --logdir=./tb_logs --port=6006

# In training code, enable profiling for specific step range
tf.profiler.experimental.start('./tb_logs/profiler')
# Training loop
tf.profiler.experimental.stop()

# Alternative: Profile specific epochs via callbacks
profiler_callback = tf.keras.callbacks.TensorBoard(
    log_dir='./tb_logs',
    profile_batch='10,20',  # Profile batches 10-20
    histogram_freq=1
)
```

**Mixed Precision Debugging**

Diagnose numerical instability in mixed-precision training by detecting NaN/Inf gradients and analyzing loss scaling behavior.

```python
# Enable mixed precision policy
policy = keras.mixed_precision.Policy('mixed_float16')
keras.mixed_precision.set_global_policy(policy)

# Verify policy is active
print(f"Compute dtype: {policy.compute_dtype}")
print(f"Variable dtype: {policy.variable_dtype}")

# Monitor loss scale during training
optimizer = keras.mixed_precision.LossScaleOptimizer(base_optimizer)

# Check for NaN/Inf in gradients
@tf.function
def check_numerics(grads):
    for grad in grads:
        if grad is not None:
            tf.debugging.check_numerics(grad, "Gradient")

# In training loop
gradients = tape.gradient(loss, model.trainable_variables)
check_numerics(gradients)

# Inspect loss scale history
print(f"Current loss scale: {optimizer.loss_scale}")
```

**Model Compilation and XLA JIT Optimization**

Enable XLA (Accelerated Linear Algebra) JIT compilation to fuse operations and reduce kernel launch overhead. XLA traces computational graphs and applies operation fusion, memory layout optimization, and constant folding.

```python
# Global XLA enablement
tf.config.optimizer.set_jit(True)

# Per-function XLA compilation via decorator
@tf.function(jit_compile=True)
def train_step(images, labels):
    with tf.GradientTape() as tape:
        logits = model(images, training=True)
        loss = loss_fn(labels, logits)
    gradients = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    return loss

# Verify XLA compilation
print(train_step.experimental_get_compiler_ir(images, labels)(stage='optimized_hlo'))
```

**Data Pipeline Performance Analysis**

Profile `tf.data` pipeline bottlenecks to identify whether GPU is starved waiting for data or if CPU preprocessing saturates available parallelism.

```python
# Instrument dataset with profiling
options = tf.data.Options()
options.experimental_optimization.apply_default_optimizations = True
options.experimental_stats.aggregate_stats = True
dataset = dataset.with_options(options)

# Log dataset statistics
print(dataset.options().experimental_stats.aggregate_stats)

# Benchmark dataset throughput
import time
start = time.time()
for i, (images, labels) in enumerate(dataset.take(100)):
    if i % 10 == 0:
        elapsed = time.time() - start
        throughput = (i + 1) / elapsed
        print(f"Step {i}: {throughput:.2f} batches/sec")
```

**Distributed Training Verification**

Validate multi-GPU training setup and gradient synchronization behavior. TensorFlow's distribution strategies automatically replicate models and aggregate gradients via all-reduce collectives.

```python
# Initialize MirroredStrategy for single-node multi-GPU
strategy = tf.distribute.MirroredStrategy()
print(f"Number of devices: {strategy.num_replicas_in_sync}")

# Build model inside strategy scope
with strategy.scope():
    model = create_model()
    optimizer = keras.optimizers.SGD(learning_rate=0.1)
    loss_fn = keras.losses.SparseCategoricalCrossentropy(from_logits=True)

# Distribute dataset across replicas
dist_dataset = strategy.experimental_distribute_dataset(dataset)

# Training step with distributed execution
@tf.function
def distributed_train_step(images, labels):
    def step_fn(images, labels):
        with tf.GradientTape() as tape:
            logits = model(images, training=True)
            loss = loss_fn(labels, logits)
        gradients = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))
        return loss
    
    per_replica_losses = strategy.run(step_fn, args=(images, labels))
    return strategy.reduce(tf.distribute.ReduceOp.SUM, per_replica_losses, axis=None)
```

**Systematic Verification Checklist**

Execute this checklist before deploying models to production or publishing benchmark results.

1. **Model Architecture Verification**
   - Print model summary and verify parameter count matches expectations
   - Ensure output shape aligns with number of classes
   - Validate gradient flow through all layers via `tf.GradientTape` inspection
   - Check for unused parameters or dead code paths

2. **Training Convergence Validation**
   - Training loss monotonically decreases (excluding initial warmup)
   - Validation loss tracks training loss without severe divergence (overfitting gap < 0.1)
   - Learning rate schedule correctly implemented (visualize via TensorBoard)
   - Gradient norms remain stable, no explosion or vanishing

3. **Numerical Stability Checks**
   - No NaN or Inf values in loss, gradients, or activations
   - Loss scale in mixed precision remains stable (no frequent reductions)
   - Batch normalization statistics converge (running mean/variance stabilize)
   - Weight distributions remain reasonable (no parameters approaching FP16 limits)

4. **Data Pipeline Integrity**
   - Verify augmentation produces expected transformations (visualize samples)
   - Confirm normalization statistics match dataset (mean ≈ 0, std ≈ 1 after normalization)
   - Check label distribution matches expectations (no class imbalance surprises)
   - Validate shuffling randomness (check batch correlation across epochs)

5. **Performance Benchmarking**
   - Measure GPU utilization (target > 90% during training)
   - Profile memory bandwidth (target > 80% theoretical peak)
   - Benchmark inference latency across batch sizes
   - Verify XLA compilation occurs (check `XLA_FLAGS` environment variables)

6. **Robustness and Failure Mode Analysis**
   - Test adversarial robustness (FGSM, PGD at multiple epsilon values)
   - Evaluate corruption robustness (noise, blur, brightness shifts)
   - Quantify prediction uncertainty (calibration error < 0.1)
   - Validate out-of-distribution detection (precision/recall on OOD dataset)

7. **Model Serialization and Loading**
   - Save and reload model, verify predictions match pre-save
   - Export SavedModel format for TensorFlow Serving
   - Convert to TFLite for edge deployment (validate accuracy maintained)
   - Test model inference without training dependencies

8. **Reproducibility Validation**
   - Fix all random seeds (Python, NumPy, TensorFlow)
   - Document software versions (TensorFlow, CUDA, cuDNN)
   - Record hardware specifications (GPU model, driver version)
   - Verify training runs reproduce results within tolerance (< 0.5% accuracy variance)

Execute verification scripts systematically after each experimental iteration to catch regressions early.

```bash
# Full verification pipeline
python training/run_training.py --config=best_config.json
python evaluation/benchmark.py checkpoints/final_model
python evaluation/robustness_suite.py checkpoints/final_model
python evaluation/metrics.py checkpoints/final_model --dataset=test
```

This comprehensive operational verification framework grounds you in production TensorFlow engineering—building robust training pipelines, profiling GPU memory hierarchies, benchmarking inference latency, and stress-testing models against adversarial inputs and distribution shifts. You now possess the diagnostic discipline to debug NaN gradients at 3 AM, optimize data pipelines that saturate PCIe bandwidth, and ship models that degrade gracefully under real-world corruption. This is the empirical, hands-on mastery required to deploy ML systems that survive contact with production traffic.
