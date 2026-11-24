# Operational Verification Labs: PyTorch

## Objective & Environment Setup

These operational verification labs ground PyTorch development in production-grade engineering discipline. The objective is not to produce toy notebooks that overfit on MNIST, but to build robust, auditable training pipelines that expose failure modes, quantify generalization gaps, and survive adversarial stress testing. You will implement complete training harnesses from scratch, instrument them with profiling and memory diagnostics, tune hyperparameters through systematic grid search, and validate model behavior under distribution shift and adversarial perturbation. Every exercise produces runnable Python scripts that log metrics to disk, checkpoint model state, and emit reproducible benchmark results.

PyTorch sits at the boundary between imperative Python control flow and compiled CUDA kernel dispatch. Understanding this duality is essential for operational verification. The autograd engine constructs dynamic computation graphs by recording tensor operations into a directed acyclic graph (DAG) of `Function` nodes, each carrying forward and backward methods. When you call `.backward()`, the engine performs reverse-mode automatic differentiation by traversing this DAG in topological order, accumulating gradients into the `.grad` attribute of leaf tensors. This design enables eager execution for debugging while maintaining compatibility with JIT compilation via TorchScript and graph optimization passes. The CUDA backend dispatches kernels asynchronously, meaning CPU-side Python continues executing while GPU operations queue in CUDA streams. Profiling tools like `torch.profiler` capture this asynchrony by recording kernel launches, memory allocations, and CPU-GPU synchronization points, exposing bottlenecks invisible to wall-clock timing alone.

Modern deep learning workflows span data ingestion, model definition, training loop execution, checkpoint persistence, and evaluation harness orchestration. Data loaders must prefetch batches asynchronously using multiprocess workers to saturate GPU compute, requiring careful management of shared memory and file descriptor limits. Model definitions must balance expressiveness with JIT traceability, avoiding dynamic control flow that breaks static graph compilation. Training loops must checkpoint state at regular intervals, log metrics to structured backends like TensorBoard or Weights & Biases, and implement early stopping to prevent overfitting. Evaluation harnesses must compute calibrated metrics on held-out test sets, measure inference latency under realistic serving conditions, and quantify robustness to distribution shift. These components form a production pipeline that transforms raw data into deployable model artifacts with provable performance guarantees.

The lab environment requires a clean Python 3.11+ virtual environment with PyTorch 2.0+, HuggingFace Transformers for pretrained model access, NumPy for numerical primitives, Polars for high-performance data manipulation, and diagnostic tools including pytest for unit testing and Weights & Biases for experiment tracking. Install dependencies via pip in an isolated environment to avoid version conflicts. The following commands establish a reproducible workspace on a Linux host with CUDA 11.8+ drivers installed. If running on CPU-only hardware, PyTorch will fall back gracefully to CPU tensors, though training will be significantly slower.

```bash
python3.11 -m venv pytorch_lab_env
source pytorch_lab_env/bin/activate
pip install --upgrade pip wheel setuptools
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers datasets accelerate tokenizers sentencepiece
pip install numpy polars scikit-learn matplotlib seaborn
pip install pytest pytest-cov pytest-benchmark
pip install tensorboard wandb
pip install torch-tb-profiler
```

Verify the installation by launching a Python REPL and executing `import torch; print(torch.__version__); print(torch.cuda.is_available())`. The version should report 2.0.0 or later, and CUDA availability should return `True` if GPU drivers are properly configured. If CUDA is unavailable, confirm that `nvidia-smi` reports GPU visibility and that the installed PyTorch wheel matches your CUDA driver version. Mismatched CUDA runtime and driver versions produce cryptic errors during kernel launch, so always cross-reference PyTorch's CUDA version against `nvidia-smi` output.

Create a working directory structure that separates source code, data artifacts, checkpoints, logs, and evaluation results. This hierarchy mirrors production ML repositories and facilitates reproducible experiment tracking.

```bash
mkdir -p pytorch_labs/{src,data,checkpoints,logs,results,configs}
cd pytorch_labs
```

Within the `src/` directory, you will author Python modules for data loading, model architecture, training orchestration, and evaluation harness. The `data/` directory caches downloaded datasets to avoid redundant network transfers. The `checkpoints/` directory persists model state dictionaries and optimizer state for resumable training. The `logs/` directory stores TensorBoard event files and structured JSON logs. The `results/` directory accumulates benchmark metrics, confusion matrices, and performance plots. The `configs/` directory holds hyperparameter YAML files and sweep configurations for reproducible experiments.

The labs progress from foundational pipeline construction to adversarial robustness testing. Exercise 1 implements a complete image classification pipeline on CIFAR-10, exposing the mechanics of data augmentation, gradient accumulation, and checkpoint persistence. Exercise 2 extends this pipeline with systematic hyperparameter search, early stopping, and metric logging to Weights & Biases. Exercise 3 stress-tests the trained model under distribution shift and adversarial attack, quantifying failure modes and implementing defensive countermeasures. Each exercise builds on the previous, culminating in a production-grade training harness that survives real-world deployment.

## Exercise 1: Hands-On Implementation & Pipeline Execution

This exercise constructs a complete image classification pipeline from scratch, exposing every operational detail required for production deployment. You will implement a custom ResNet-18 variant, author a PyTorch Lightning training module with gradient accumulation, integrate mixed-precision training via `torch.cuda.amp`, and orchestrate multi-GPU data parallelism. The dataset is CIFAR-10, a canonical 10-class image classification benchmark with 50,000 training images and 10,000 test images at 32×32 resolution. Despite its modest size, CIFAR-10 exhibits sufficient complexity to expose overfitting, augmentation sensitivity, and optimization pathologies.

Begin by authoring a data module that encapsulates dataset download, preprocessing, augmentation, and DataLoader construction. The module must implement separate pipelines for training and validation, applying aggressive augmentation during training while preserving original images during evaluation. PyTorch's `torchvision.transforms` provides composable transformations, but many practitioners overlook normalization statistics. CIFAR-10 images must be normalized by the channel-wise mean and standard deviation computed over the training set: `mean = [0.4914, 0.4822, 0.4465]`, `std = [0.2470, 0.2435, 0.2616]`. Skipping this step degrades convergence by forcing the network to learn invariant features from raw pixel intensities.

Create the file `src/cifar10_datamodule.py` with the following complete implementation:

```python
import torch
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms
from pathlib import Path


class CIFAR10DataModule:
    """
    Encapsulates CIFAR-10 data loading with train/val split, augmentation,
    and multi-worker prefetching.
    """

    def __init__(
        self,
        data_dir: str = "./data",
        batch_size: int = 128,
        num_workers: int = 4,
        pin_memory: bool = True,
        train_val_split: float = 0.9,
    ):
        self.data_dir = Path(data_dir)
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.pin_memory = pin_memory
        self.train_val_split = train_val_split

        # CIFAR-10 normalization statistics (computed over training set)
        self.cifar10_mean = [0.4914, 0.4822, 0.4465]
        self.cifar10_std = [0.2470, 0.2435, 0.2616]

        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None

    def setup(self):
        """Download datasets and apply transforms."""
        # Training augmentation: random crop, horizontal flip, normalization
        train_transform = transforms.Compose(
            [
                transforms.RandomCrop(32, padding=4),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.ToTensor(),
                transforms.Normalize(self.cifar10_mean, self.cifar10_std),
            ]
        )

        # Validation/test transform: only normalization
        eval_transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize(self.cifar10_mean, self.cifar10_std),
            ]
        )

        # Download training set and split into train/val
        full_train = datasets.CIFAR10(
            root=self.data_dir,
            train=True,
            download=True,
            transform=train_transform,
        )

        train_size = int(len(full_train) * self.train_val_split)
        val_size = len(full_train) - train_size
        self.train_dataset, val_dataset_temp = random_split(
            full_train,
            [train_size, val_size],
            generator=torch.Generator().manual_seed(42),
        )

        # Re-apply eval transform to validation split
        val_dataset_base = datasets.CIFAR10(
            root=self.data_dir,
            train=True,
            download=False,
            transform=eval_transform,
        )
        self.val_dataset = torch.utils.data.Subset(
            val_dataset_base, val_dataset_temp.indices
        )

        # Download test set
        self.test_dataset = datasets.CIFAR10(
            root=self.data_dir,
            train=False,
            download=True,
            transform=eval_transform,
        )

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=True,
            drop_last=True,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=True,
        )

    def test_dataloader(self):
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=True,
        )
```

The `persistent_workers=True` flag prevents worker process teardown between epochs, eliminating startup overhead. The `pin_memory=True` flag allocates page-locked host memory, enabling asynchronous DMA transfers to GPU via PCIe without CPU synchronization stalls. The `drop_last=True` flag discards incomplete final batches during training, preventing batch normalization statistics from being corrupted by variable-size batches. These are not optional optimizations; they are required for saturating modern GPU throughput.

Next, implement a ResNet-18 architecture with batch normalization, ReLU activation, and residual skip connections. The original ResNet paper demonstrated that skip connections enable training of arbitrarily deep networks by providing gradient highways that bypass saturated activation functions. The architecture consists of four stages with progressively increasing channel counts (64, 128, 256, 512) and spatial downsampling via strided convolutions. Each stage contains two residual blocks, where each block performs two 3×3 convolutions with batch normalization and ReLU activation, followed by element-wise addition with the input.

Create the file `src/resnet.py` with the following complete implementation:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    """
    Residual block with two 3x3 convolutions, batch norm, and skip connection.
    Implements identity mapping when stride=1, projection when stride=2.
    """

    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
            bias=False,
        )
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(
            out_channels,
            out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False,
        )
        self.bn2 = nn.BatchNorm2d(out_channels)

        # Projection shortcut for dimension matching
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(
                    in_channels,
                    out_channels,
                    kernel_size=1,
                    stride=stride,
                    bias=False,
                ),
                nn.BatchNorm2d(out_channels),
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class ResNet18(nn.Module):
    """
    ResNet-18 variant for CIFAR-10 (32x32 input).
    Architecture: stem -> 4 stages (2 blocks each) -> global pool -> fc
    """

    def __init__(self, num_classes=10):
        super().__init__()
        self.in_channels = 64

        # Initial conv (no pooling for CIFAR-10's small 32x32 images)
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)

        # Four stages with progressively increasing channels
        self.layer1 = self._make_layer(64, 2, stride=1)
        self.layer2 = self._make_layer(128, 2, stride=2)
        self.layer3 = self._make_layer(256, 2, stride=2)
        self.layer4 = self._make_layer(512, 2, stride=2)

        # Global average pooling and classifier
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def _make_layer(self, out_channels, num_blocks, stride):
        layers = []
        # First block may downsample
        layers.append(ResidualBlock(self.in_channels, out_channels, stride))
        self.in_channels = out_channels
        # Remaining blocks maintain spatial dimensions
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels, stride=1))
        return nn.Sequential(*layers)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.avgpool(out)
        out = torch.flatten(out, 1)
        out = self.fc(out)
        return out
```

This architecture omits the initial 7×7 convolution and max pooling present in the original ImageNet ResNet, as CIFAR-10's 32×32 images are too small to tolerate aggressive downsampling. The adaptive average pooling layer spatially reduces feature maps to 1×1 regardless of input size, making the architecture invariant to spatial resolution. The final fully connected layer projects the 512-dimensional feature vector to 10 logits, one per class.

Now implement the training orchestration script that instantiates the data module and model, configures the optimizer and learning rate scheduler, implements the training loop with mixed-precision training, and checkpoints model state at regular intervals. The training loop must compute loss on each batch, accumulate gradients across multiple micro-batches for effective batch size scaling, perform gradient clipping to prevent exploding gradients, and log metrics to TensorBoard for visualization.

Create the file `src/train_cifar10.py` with the following complete implementation:

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from torch.utils.tensorboard import SummaryWriter
from pathlib import Path
import time
import json
from resnet import ResNet18
from cifar10_datamodule import CIFAR10DataModule


class Trainer:
    """
    Training orchestration with gradient accumulation, mixed precision,
    checkpointing, and metric logging.
    """

    def __init__(
        self,
        model,
        train_loader,
        val_loader,
        optimizer,
        scheduler,
        device,
        num_epochs=100,
        grad_accum_steps=1,
        checkpoint_dir="./checkpoints",
        log_dir="./logs",
        max_grad_norm=1.0,
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.device = device
        self.num_epochs = num_epochs
        self.grad_accum_steps = grad_accum_steps
        self.checkpoint_dir = Path(checkpoint_dir)
        self.log_dir = Path(log_dir)
        self.max_grad_norm = max_grad_norm

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.criterion = nn.CrossEntropyLoss()
        self.scaler = GradScaler()
        self.writer = SummaryWriter(log_dir=self.log_dir)

        self.global_step = 0
        self.best_val_acc = 0.0

    def train_epoch(self, epoch):
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        self.optimizer.zero_grad()

        for batch_idx, (inputs, targets) in enumerate(self.train_loader):
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Mixed precision forward pass
            with autocast():
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets) / self.grad_accum_steps

            # Backward pass with gradient scaling
            self.scaler.scale(loss).backward()

            # Gradient accumulation
            if (batch_idx + 1) % self.grad_accum_steps == 0:
                # Gradient clipping
                self.scaler.unscale_(self.optimizer)
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.max_grad_norm
                )

                # Optimizer step
                self.scaler.step(self.optimizer)
                self.scaler.update()
                self.optimizer.zero_grad()

                self.global_step += 1

            # Metrics
            running_loss += loss.item() * self.grad_accum_steps
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

            # Log every 100 batches
            if batch_idx % 100 == 0:
                self.writer.add_scalar(
                    "train/batch_loss", loss.item() * self.grad_accum_steps, self.global_step
                )

        epoch_loss = running_loss / len(self.train_loader)
        epoch_acc = 100.0 * correct / total
        self.writer.add_scalar("train/epoch_loss", epoch_loss, epoch)
        self.writer.add_scalar("train/epoch_acc", epoch_acc, epoch)

        return epoch_loss, epoch_acc

    def validate(self, epoch):
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in self.val_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        epoch_loss = running_loss / len(self.val_loader)
        epoch_acc = 100.0 * correct / total
        self.writer.add_scalar("val/epoch_loss", epoch_loss, epoch)
        self.writer.add_scalar("val/epoch_acc", epoch_acc, epoch)

        return epoch_loss, epoch_acc

    def save_checkpoint(self, epoch, val_acc, is_best=False):
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "scaler_state_dict": self.scaler.state_dict(),
            "val_acc": val_acc,
            "global_step": self.global_step,
        }

        # Save latest checkpoint
        latest_path = self.checkpoint_dir / "checkpoint_latest.pth"
        torch.save(checkpoint, latest_path)

        # Save best checkpoint
        if is_best:
            best_path = self.checkpoint_dir / "checkpoint_best.pth"
            torch.save(checkpoint, best_path)
            print(f"  → New best model saved (val_acc={val_acc:.2f}%)")

    def train(self):
        print(f"Training on device: {self.device}")
        print(f"Total epochs: {self.num_epochs}")
        print(f"Gradient accumulation steps: {self.grad_accum_steps}")
        print(f"Effective batch size: {self.train_loader.batch_size * self.grad_accum_steps}")

        for epoch in range(1, self.num_epochs + 1):
            start_time = time.time()

            train_loss, train_acc = self.train_epoch(epoch)
            val_loss, val_acc = self.validate(epoch)
            self.scheduler.step()

            epoch_time = time.time() - start_time

            print(
                f"Epoch {epoch:03d}/{self.num_epochs} | "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
                f"Time: {epoch_time:.2f}s"
            )

            # Checkpointing
            is_best = val_acc > self.best_val_acc
            if is_best:
                self.best_val_acc = val_acc
            self.save_checkpoint(epoch, val_acc, is_best)

        self.writer.close()
        print(f"\nTraining complete. Best validation accuracy: {self.best_val_acc:.2f}%")


def main():
    # Hyperparameters
    config = {
        "batch_size": 128,
        "num_epochs": 100,
        "learning_rate": 0.1,
        "momentum": 0.9,
        "weight_decay": 5e-4,
        "grad_accum_steps": 1,
        "num_workers": 4,
        "max_grad_norm": 1.0,
    }

    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")

    # Data module
    data_module = CIFAR10DataModule(
        batch_size=config["batch_size"],
        num_workers=config["num_workers"],
    )
    data_module.setup()

    # Model
    model = ResNet18(num_classes=10)
    num_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {num_params:,}")

    # Optimizer and scheduler
    optimizer = optim.SGD(
        model.parameters(),
        lr=config["learning_rate"],
        momentum=config["momentum"],
        weight_decay=config["weight_decay"],
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config["num_epochs"]
    )

    # Trainer
    trainer = Trainer(
        model=model,
        train_loader=data_module.train_dataloader(),
        val_loader=data_module.val_dataloader(),
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        num_epochs=config["num_epochs"],
        grad_accum_steps=config["grad_accum_steps"],
        max_grad_norm=config["max_grad_norm"],
    )

    # Save config
    config_path = Path("./logs/config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # Train
    trainer.train()


if __name__ == "__main__":
    main()
```

This training script implements gradient accumulation by dividing the loss by the number of accumulation steps and only performing optimizer steps after accumulating gradients from multiple micro-batches. This technique enables training with effective batch sizes larger than GPU memory permits. The `GradScaler` applies loss scaling to prevent gradient underflow in mixed-precision training, where float16 has limited dynamic range. The cosine annealing scheduler decays the learning rate from the initial value to zero following a cosine curve, promoting convergence without manual tuning. The checkpoint logic persists the model, optimizer, scheduler, and scaler state, enabling training resumption after interruption.

Execute the training script from the repository root:

```bash
python src/train_cifar10.py
```

Training will proceed for 100 epochs, logging metrics to TensorBoard and saving checkpoints to `./checkpoints/`. Monitor training progress via TensorBoard:

```bash
tensorboard --logdir=./logs --port=6006
```

Navigate to `http://localhost:6006` to visualize loss curves, accuracy trajectories, and learning rate schedules. Expect training accuracy to exceed 95% and validation accuracy to reach approximately 92-93% on CIFAR-10, with overfitting becoming apparent as the gap between training and validation accuracy widens. This gap quantifies the model's generalization capacity and signals the need for stronger regularization or early stopping.

After training completes, implement an evaluation harness that loads the best checkpoint, computes per-class accuracy, generates a confusion matrix, and measures inference latency under realistic serving conditions. The confusion matrix reveals which classes the model confuses, exposing dataset biases and annotation errors.

Create the file `src/eval_cifar10.py` with the following complete implementation:

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import time
from pathlib import Path
import json
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from resnet import ResNet18
from cifar10_datamodule import CIFAR10DataModule


class Evaluator:
    """
    Evaluation harness with per-class metrics, confusion matrix,
    and inference latency profiling.
    """

    def __init__(self, model, test_loader, device, class_names):
        self.model = model.to(device)
        self.test_loader = test_loader
        self.device = device
        self.class_names = class_names
        self.criterion = nn.CrossEntropyLoss()

    def evaluate(self):
        self.model.eval()
        all_preds = []
        all_targets = []
        running_loss = 0.0
        inference_times = []

        with torch.no_grad():
            for inputs, targets in self.test_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                # Measure inference time
                start_time = time.perf_counter()
                outputs = self.model(inputs)
                torch.cuda.synchronize()  # Wait for GPU kernels to complete
                end_time = time.perf_counter()
                inference_times.append(end_time - start_time)

                loss = self.criterion(outputs, targets)
                running_loss += loss.item()

                _, predicted = outputs.max(1)
                all_preds.extend(predicted.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())

        # Aggregate metrics
        all_preds = np.array(all_preds)
        all_targets = np.array(all_targets)

        avg_loss = running_loss / len(self.test_loader)
        accuracy = 100.0 * (all_preds == all_targets).sum() / len(all_targets)

        # Per-class metrics
        print("\n" + "=" * 60)
        print("Classification Report")
        print("=" * 60)
        print(
            classification_report(
                all_targets,
                all_preds,
                target_names=self.class_names,
                digits=4,
            )
        )

        # Confusion matrix
        cm = confusion_matrix(all_targets, all_preds)
        self.plot_confusion_matrix(cm)

        # Inference latency
        avg_latency = np.mean(inference_times) * 1000  # Convert to ms
        p50_latency = np.percentile(inference_times, 50) * 1000
        p95_latency = np.percentile(inference_times, 95) * 1000
        p99_latency = np.percentile(inference_times, 99) * 1000

        print("\n" + "=" * 60)
        print("Inference Latency (per batch)")
        print("=" * 60)
        print(f"Mean:   {avg_latency:.2f} ms")
        print(f"P50:    {p50_latency:.2f} ms")
        print(f"P95:    {p95_latency:.2f} ms")
        print(f"P99:    {p99_latency:.2f} ms")

        # Summary metrics
        results = {
            "test_loss": avg_loss,
            "test_accuracy": accuracy,
            "per_class_accuracy": {},
            "inference_latency_ms": {
                "mean": avg_latency,
                "p50": p50_latency,
                "p95": p95_latency,
                "p99": p99_latency,
            },
        }

        for i, class_name in enumerate(self.class_names):
            class_mask = all_targets == i
            class_acc = 100.0 * (all_preds[class_mask] == all_targets[class_mask]).sum() / class_mask.sum()
            results["per_class_accuracy"][class_name] = class_acc

        return results

    def plot_confusion_matrix(self, cm):
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=self.class_names,
            yticklabels=self.class_names,
        )
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.title("Confusion Matrix")
        plt.tight_layout()
        plt.savefig("./results/confusion_matrix.png", dpi=300)
        print("\nConfusion matrix saved to ./results/confusion_matrix.png")


def main():
    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # CIFAR-10 class names
    class_names = [
        "airplane",
        "automobile",
        "bird",
        "cat",
        "deer",
        "dog",
        "frog",
        "horse",
        "ship",
        "truck",
    ]

    # Data module
    data_module = CIFAR10DataModule(batch_size=128, num_workers=4)
    data_module.setup()

    # Load model
    model = ResNet18(num_classes=10)
    checkpoint_path = Path("./checkpoints/checkpoint_best.pth")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    print(f"Loaded checkpoint from epoch {checkpoint['epoch']}")

    # Create results directory
    Path("./results").mkdir(exist_ok=True)

    # Evaluate
    evaluator = Evaluator(
        model=model,
        test_loader=data_module.test_dataloader(),
        device=device,
        class_names=class_names,
    )
    results = evaluator.evaluate()

    # Save results
    results_path = Path("./results/eval_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")

    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Test Loss:     {results['test_loss']:.4f}")
    print(f"Test Accuracy: {results['test_accuracy']:.2f}%")


if __name__ == "__main__":
    main()
```

Execute the evaluation script after training completes:

```bash
python src/eval_cifar10.py
```

The script will load the best checkpoint, compute classification metrics, generate a confusion matrix heatmap, and report inference latency statistics. The confusion matrix reveals systematic misclassifications, such as confusing cats with dogs or automobiles with trucks, indicating that the model struggles with fine-grained distinctions within superordinate categories. Inference latency measurements include percentiles to capture tail latency, which dominates user-perceived performance in production serving systems.

This completes Exercise 1. You have implemented a production-grade training pipeline with gradient accumulation, mixed-precision training, checkpointing, metric logging, and comprehensive evaluation. The pipeline is fully operational and ready for hyperparameter tuning and robustness testing in subsequent exercises.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Hyperparameter optimization transforms ad-hoc trial-and-error into systematic exploration of the configuration space. The previous exercise hardcoded a single hyperparameter configuration, yielding approximately 92-93% validation accuracy on CIFAR-10. This exercise implements a grid search over learning rates, weight decay coefficients, and augmentation strategies, logging all experiments to Weights & Biases for comparative analysis. You will quantify the sensitivity of validation accuracy to each hyperparameter, identify interactions between parameters, and establish empirical best practices for ResNet training on small-scale image classification tasks.

The hyperparameter space for deep learning is high-dimensional and non-convex, making exhaustive search intractable. However, many hyperparameters exhibit low sensitivity or redundant effects, enabling practitioners to focus on the most impactful dimensions. For ResNet training on CIFAR-10, the critical hyperparameters are initial learning rate, weight decay (L2 regularization coefficient), learning rate schedule, batch size, and data augmentation intensity. Optimizer choice (SGD vs Adam) and momentum coefficient also matter, but SGD with momentum 0.9 is the de facto standard for vision tasks and rarely requires tuning.

Begin by registering a free Weights & Biases account at `https://wandb.ai` and obtaining an API key. Export the key as an environment variable to avoid embedding credentials in source code:

```bash
export WANDB_API_KEY="your_api_key_here"
```

Modify the training script to integrate Weights & Biases logging and accept hyperparameters via command-line arguments. The refactored script must initialize a wandb run at the start of training, log metrics after each epoch, and upload checkpoint artifacts to the wandb cloud storage backend for reproducibility.

Create the file `src/train_sweep.py` with the following complete implementation:

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from pathlib import Path
import time
import argparse
import wandb
from resnet import ResNet18
from cifar10_datamodule import CIFAR10DataModule


class TrainerWithWandB:
    """
    Training orchestration with Weights & Biases integration for
    hyperparameter sweep experiments.
    """

    def __init__(
        self,
        model,
        train_loader,
        val_loader,
        optimizer,
        scheduler,
        device,
        config,
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.device = device
        self.config = config

        self.criterion = nn.CrossEntropyLoss()
        self.scaler = GradScaler()

        self.global_step = 0
        self.best_val_acc = 0.0

    def train_epoch(self, epoch):
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        self.optimizer.zero_grad()

        for batch_idx, (inputs, targets) in enumerate(self.train_loader):
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            with autocast():
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
            self.optimizer.zero_grad()

            self.global_step += 1

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

        epoch_loss = running_loss / len(self.train_loader)
        epoch_acc = 100.0 * correct / total

        return epoch_loss, epoch_acc

    def validate(self, epoch):
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in self.val_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        epoch_loss = running_loss / len(self.val_loader)
        epoch_acc = 100.0 * correct / total

        return epoch_loss, epoch_acc

    def train(self):
        print(f"Training on device: {self.device}")
        print(f"Config: {self.config}")

        for epoch in range(1, self.config["num_epochs"] + 1):
            start_time = time.time()

            train_loss, train_acc = self.train_epoch(epoch)
            val_loss, val_acc = self.validate(epoch)
            self.scheduler.step()

            epoch_time = time.time() - start_time

            # Log to wandb
            wandb.log(
                {
                    "epoch": epoch,
                    "train/loss": train_loss,
                    "train/accuracy": train_acc,
                    "val/loss": val_loss,
                    "val/accuracy": val_acc,
                    "learning_rate": self.scheduler.get_last_lr()[0],
                    "epoch_time": epoch_time,
                },
                step=epoch,
            )

            print(
                f"Epoch {epoch:03d}/{self.config['num_epochs']} | "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
                f"Time: {epoch_time:.2f}s"
            )

            # Track best model
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc

        wandb.log({"best_val_accuracy": self.best_val_acc})
        print(f"\nTraining complete. Best validation accuracy: {self.best_val_acc:.2f}%")


def train_single_run(config):
    """Execute a single training run with given hyperparameters."""
    # Initialize wandb run
    run = wandb.init(project="cifar10-hyperparameter-sweep", config=config)

    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Data module
    data_module = CIFAR10DataModule(
        batch_size=config["batch_size"],
        num_workers=4,
    )
    data_module.setup()

    # Model
    model = ResNet18(num_classes=10)

    # Optimizer
    optimizer = optim.SGD(
        model.parameters(),
        lr=config["learning_rate"],
        momentum=config["momentum"],
        weight_decay=config["weight_decay"],
    )

    # Scheduler
    if config["scheduler"] == "cosine":
        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=config["num_epochs"]
        )
    elif config["scheduler"] == "step":
        scheduler = optim.lr_scheduler.MultiStepLR(
            optimizer, milestones=[60, 120, 160], gamma=0.2
        )
    else:
        scheduler = optim.lr_scheduler.ConstantLR(optimizer, factor=1.0)

    # Trainer
    trainer = TrainerWithWandB(
        model=model,
        train_loader=data_module.train_dataloader(),
        val_loader=data_module.val_dataloader(),
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        config=config,
    )

    # Train
    trainer.train()

    run.finish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--learning_rate", type=float, default=0.1)
    parser.add_argument("--weight_decay", type=float, default=5e-4)
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--num_epochs", type=int, default=200)
    parser.add_argument("--momentum", type=float, default=0.9)
    parser.add_argument("--scheduler", type=str, default="cosine", choices=["cosine", "step", "constant"])
    args = parser.parse_args()

    config = {
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "batch_size": args.batch_size,
        "num_epochs": args.num_epochs,
        "momentum": args.momentum,
        "scheduler": args.scheduler,
    }

    train_single_run(config)


if __name__ == "__main__":
    main()
```

This refactored script accepts hyperparameters via command-line arguments and initializes a wandb run to track metrics. Each run is tagged with its hyperparameter configuration, enabling comparative analysis across the sweep. The script removes checkpointing logic for brevity, as the focus is on metric collection rather than model persistence.

Now implement a grid search driver that launches multiple training runs with different hyperparameter configurations. The driver must iterate over a predefined grid, spawn a separate process for each configuration to isolate CUDA state, and collect results into a summary table.

Create the file `src/run_sweep.py` with the following complete implementation:

```python
import subprocess
import itertools
from pathlib import Path


def run_sweep():
    """
    Execute hyperparameter grid search by launching separate training
    processes for each configuration.
    """
    # Define hyperparameter grid
    param_grid = {
        "learning_rate": [0.01, 0.05, 0.1],
        "weight_decay": [1e-4, 5e-4, 1e-3],
        "scheduler": ["cosine", "step"],
        "batch_size": [128],
        "num_epochs": [100],
        "momentum": [0.9],
    }

    # Generate all combinations
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = list(itertools.product(*values))

    print(f"Total experiments: {len(combinations)}")
    print("=" * 60)

    for idx, combo in enumerate(combinations, 1):
        config = dict(zip(keys, combo))
        print(f"\nExperiment {idx}/{len(combinations)}")
        print(f"Config: {config}")

        # Build command
        cmd = [
            "python",
            "src/train_sweep.py",
            "--learning_rate", str(config["learning_rate"]),
            "--weight_decay", str(config["weight_decay"]),
            "--batch_size", str(config["batch_size"]),
            "--num_epochs", str(config["num_epochs"]),
            "--momentum", str(config["momentum"]),
            "--scheduler", config["scheduler"],
        ]

        # Execute training run
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            print(f"  ERROR: Experiment {idx} failed")
        else:
            print(f"  SUCCESS: Experiment {idx} completed")

    print("\n" + "=" * 60)
    print("Sweep complete. View results at https://wandb.ai")


if __name__ == "__main__":
    run_sweep()
```

Execute the sweep from the repository root:

```bash
python src/run_sweep.py
```

The sweep will launch 18 experiments (3 learning rates × 3 weight decay values × 2 schedulers), each training for 100 epochs. Expect the entire sweep to take several hours on a single GPU. Monitor progress via the wandb web interface, which provides real-time loss curves, accuracy trajectories, and hyperparameter correlation plots.

After the sweep completes, analyze the results to identify optimal hyperparameters. Log into the wandb dashboard and navigate to the sweep project. Use the parallel coordinates plot to visualize how each hyperparameter affects final validation accuracy. Key insights typically include: (1) Learning rate is the most sensitive parameter, with values above 0.1 causing divergence and values below 0.01 slowing convergence. (2) Weight decay acts as a regularizer, with higher values (1e-3) reducing overfitting but also lowering peak accuracy. (3) Cosine annealing consistently outperforms step decay by smoothly reducing the learning rate without abrupt drops. (4) Batch size has minimal impact within the range 64-256, as the effective batch size is determined by gradient accumulation.

To quantify hyperparameter sensitivity, compute the variance in validation accuracy across configurations that differ only in a single hyperparameter. For example, compare all runs with `learning_rate=0.1` against all runs with `learning_rate=0.05`, holding other parameters constant. High variance indicates high sensitivity, guiding prioritization in future tuning efforts.

Implement a script that queries the wandb API to extract sweep results and generate a sensitivity analysis report. Create the file `src/analyze_sweep.py`:

```python
import wandb
import pandas as pd
import numpy as np
from pathlib import Path


def analyze_sweep():
    """
    Query wandb API to extract sweep results and compute
    hyperparameter sensitivity metrics.
    """
    api = wandb.Api()
    
    # Replace with your actual project path
    runs = api.runs("your-username/cifar10-hyperparameter-sweep")

    data = []
    for run in runs:
        if run.state == "finished":
            config = run.config
            summary = run.summary._json_dict
            data.append(
                {
                    "learning_rate": config.get("learning_rate"),
                    "weight_decay": config.get("weight_decay"),
                    "scheduler": config.get("scheduler"),
                    "best_val_accuracy": summary.get("best_val_accuracy", 0.0),
                }
            )

    df = pd.DataFrame(data)
    
    # Save raw results
    results_path = Path("./results/sweep_results.csv")
    df.to_csv(results_path, index=False)
    print(f"Results saved to {results_path}")

    # Compute mean accuracy by hyperparameter
    print("\n" + "=" * 60)
    print("Mean Validation Accuracy by Hyperparameter")
    print("=" * 60)
    
    for param in ["learning_rate", "weight_decay", "scheduler"]:
        grouped = df.groupby(param)["best_val_accuracy"].agg(["mean", "std"])
        print(f"\n{param}:")
        print(grouped)

    # Best configuration
    best_idx = df["best_val_accuracy"].idxmax()
    best_config = df.iloc[best_idx]
    print("\n" + "=" * 60)
    print("Best Configuration")
    print("=" * 60)
    print(best_config)


if __name__ == "__main__":
    analyze_sweep()
```

Execute the analysis script after updating the project path:

```bash
python src/analyze_sweep.py
```

The script will generate a CSV file with all sweep results and print summary statistics. The best configuration typically achieves 93-94% validation accuracy with `learning_rate=0.1`, `weight_decay=5e-4`, and `scheduler=cosine`. Configurations with lower learning rates converge slower but may reach similar final accuracy if trained longer. Configurations with higher weight decay exhibit lower training accuracy but similar validation accuracy, confirming the regularization effect.

This completes Exercise 2. You have implemented a systematic hyperparameter sweep, logged results to Weights & Biases, and analyzed sensitivity to each parameter. The empirical best practices derived from this sweep generalize to other image classification tasks on similar-scale datasets.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Production ML systems fail in ways that clean benchmark datasets never expose. Models trained on curated datasets encounter distribution shift when deployed against real-world data with different lighting conditions, occlusion, compression artifacts, and adversarial perturbations. This exercise implements a comprehensive stress testing suite that evaluates model robustness under corrupted inputs, measures performance degradation under distribution shift, and implements adversarial attack and defense mechanisms. You will quantify the model's vulnerability to gradient-based attacks, implement input sanitization defenses, and establish operational SLAs for acceptable failure rates.

Distribution shift occurs when the test distribution diverges from the training distribution, violating the i.i.d. assumption underlying empirical risk minimization. Common sources of distribution shift in image classification include: (1) Covariate shift: changes in input features (brightness, contrast, blur) while label distribution remains constant. (2) Label shift: changes in class prevalence (rare classes becoming common) while feature distribution per class remains constant. (3) Concept drift: changes in the underlying relationship between features and labels (e.g., fashion trends making old clothing styles unrecognizable). CIFAR-10-C is a standard robustness benchmark that applies 15 types of corruption at 5 severity levels to the CIFAR-10 test set, simulating real-world degradation.

Begin by downloading CIFAR-10-C and implementing a corruption evaluation harness. Create the file `src/eval_corruptions.py`:

```python
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import json
from resnet import ResNet18


class CorruptionEvaluator:
    """
    Evaluate model robustness on CIFAR-10-C corrupted test set.
    """

    def __init__(self, model, device, data_dir="./data"):
        self.model = model.to(device)
        self.device = device
        self.data_dir = Path(data_dir)
        self.criterion = nn.CrossEntropyLoss()

        self.corruption_types = [
            "gaussian_noise",
            "shot_noise",
            "impulse_noise",
            "defocus_blur",
            "glass_blur",
            "motion_blur",
            "zoom_blur",
            "snow",
            "frost",
            "fog",
            "brightness",
            "contrast",
            "elastic_transform",
            "pixelate",
            "jpeg_compression",
        ]

    def load_corrupted_data(self, corruption_type, severity):
        """Load CIFAR-10-C data for specific corruption and severity."""
        data_path = self.data_dir / "CIFAR-10-C" / f"{corruption_type}.npy"
        labels_path = self.data_dir / "CIFAR-10-C" / "labels.npy"

        if not data_path.exists():
            raise FileNotFoundError(
                f"CIFAR-10-C not found. Download from: "
                "https://zenodo.org/record/2535967"
            )

        # Load data (shape: [50000, 32, 32, 3])
        data = np.load(data_path)
        labels = np.load(labels_path)

        # Select severity level (5000 images per severity)
        start_idx = (severity - 1) * 10000
        end_idx = start_idx + 10000
        data = data[start_idx:end_idx]
        labels = labels[start_idx:end_idx]

        # Convert to torch tensors and normalize
        data = torch.from_numpy(data).float().permute(0, 3, 1, 2) / 255.0
        mean = torch.tensor([0.4914, 0.4822, 0.4465]).view(1, 3, 1, 1)
        std = torch.tensor([0.2470, 0.2435, 0.2616]).view(1, 3, 1, 1)
        data = (data - mean) / std

        labels = torch.from_numpy(labels).long()

        return torch.utils.data.TensorDataset(data, labels)

    def evaluate_corruption(self, corruption_type, severity):
        """Evaluate model on a specific corruption type and severity."""
        dataset = self.load_corrupted_data(corruption_type, severity)
        loader = torch.utils.data.DataLoader(
            dataset, batch_size=128, shuffle=False, num_workers=4
        )

        self.model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                outputs = self.model(inputs)
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        accuracy = 100.0 * correct / total
        return accuracy

    def run_full_evaluation(self):
        """Evaluate model on all corruption types and severities."""
        results = {}

        print("=" * 60)
        print("CIFAR-10-C Robustness Evaluation")
        print("=" * 60)

        for corruption in self.corruption_types:
            results[corruption] = {}
            print(f"\n{corruption}:")

            for severity in range(1, 6):
                try:
                    acc = self.evaluate_corruption(corruption, severity)
                    results[corruption][f"severity_{severity}"] = acc
                    print(f"  Severity {severity}: {acc:.2f}%")
                except FileNotFoundError as e:
                    print(f"  Error: {e}")
                    break

        # Compute mean corruption error (mCE)
        all_accuracies = []
        for corruption in results:
            for severity in results[corruption]:
                all_accuracies.append(results[corruption][severity])

        mean_accuracy = float(np.mean(all_accuracies))
        results["mean_corruption_accuracy"] = mean_accuracy

        print("\n" + "=" * 60)
        print(f"Mean Corruption Accuracy: {mean_accuracy:.2f}%")
        print("=" * 60)

        return results


def main():
    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load model
    model = ResNet18(num_classes=10)
    checkpoint_path = Path("./checkpoints/checkpoint_best.pth")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    # Evaluate
    evaluator = CorruptionEvaluator(model, device)
    results = evaluator.run_full_evaluation()

    # Save results
    Path("./results").mkdir(exist_ok=True)
    results_path = Path("./results/corruption_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    main()
```

Download CIFAR-10-C from `https://zenodo.org/record/2535967` and extract it to `./data/CIFAR-10-C/`. Then execute the corruption evaluation:

```bash
python src/eval_corruptions.py
```

Expect significant accuracy degradation on corrupted images, with mean corruption accuracy dropping to 70-75% compared to 92-93% on clean data. Gaussian noise and motion blur cause the largest degradation, as these corruptions obliterate high-frequency edge features that CNNs rely on. Brightness and contrast perturbations cause less degradation, as batch normalization partially normalizes these distortions. This evaluation quantifies the model's robustness and establishes a baseline for defensive training techniques like data augmentation with corruption.

Next, implement adversarial attack and defense mechanisms. Adversarial examples are inputs crafted by adding imperceptible perturbations that maximize the model's prediction error. The Fast Gradient Sign Method (FGSM) is the simplest attack, computing the gradient of the loss with respect to the input and perturbing the input in the direction that increases loss. More sophisticated attacks like Projected Gradient Descent (PGD) iteratively refine the perturbation within an L-infinity ball around the original input.

Create the file `src/adversarial_eval.py` with the following complete implementation:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
from resnet import ResNet18
from cifar10_datamodule import CIFAR10DataModule


class AdversarialEvaluator:
    """
    Evaluate model robustness against adversarial attacks (FGSM, PGD).
    """

    def __init__(self, model, test_loader, device):
        self.model = model.to(device)
        self.test_loader = test_loader
        self.device = device
        self.criterion = nn.CrossEntropyLoss()

    def fgsm_attack(self, inputs, targets, epsilon):
        """
        Fast Gradient Sign Method (FGSM) attack.
        Perturb input in the direction of the gradient sign.
        """
        inputs.requires_grad = True

        outputs = self.model(inputs)
        loss = self.criterion(outputs, targets)
        self.model.zero_grad()
        loss.backward()

        # Generate adversarial example
        perturbation = epsilon * inputs.grad.sign()
        adv_inputs = inputs + perturbation
        adv_inputs = torch.clamp(adv_inputs, 0, 1)

        return adv_inputs.detach()

    def pgd_attack(self, inputs, targets, epsilon, alpha, num_steps):
        """
        Projected Gradient Descent (PGD) attack.
        Iteratively refine perturbation within L-infinity ball.
        """
        adv_inputs = inputs.clone().detach()

        for _ in range(num_steps):
            adv_inputs.requires_grad = True

            outputs = self.model(adv_inputs)
            loss = self.criterion(outputs, targets)
            self.model.zero_grad()
            loss.backward()

            # Update adversarial example
            perturbation = alpha * adv_inputs.grad.sign()
            adv_inputs = adv_inputs.detach() + perturbation

            # Project back into epsilon ball
            perturbation = torch.clamp(adv_inputs - inputs, -epsilon, epsilon)
            adv_inputs = torch.clamp(inputs + perturbation, 0, 1).detach()

        return adv_inputs

    def evaluate_attack(self, attack_fn, **attack_params):
        """Evaluate model accuracy under adversarial attack."""
        self.model.eval()
        correct_clean = 0
        correct_adv = 0
        total = 0

        for inputs, targets in self.test_loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Clean accuracy
            outputs_clean = self.model(inputs)
            _, pred_clean = outputs_clean.max(1)
            correct_clean += pred_clean.eq(targets).sum().item()

            # Adversarial accuracy
            adv_inputs = attack_fn(inputs, targets, **attack_params)
            outputs_adv = self.model(adv_inputs)
            _, pred_adv = outputs_adv.max(1)
            correct_adv += pred_adv.eq(targets).sum().item()

            total += targets.size(0)

        clean_acc = 100.0 * correct_clean / total
        adv_acc = 100.0 * correct_adv / total

        return clean_acc, adv_acc

    def run_full_evaluation(self):
        """Evaluate robustness across multiple attack configurations."""
        results = {}

        print("=" * 60)
        print("Adversarial Robustness Evaluation")
        print("=" * 60)

        # FGSM attack with varying epsilon
        print("\nFGSM Attack:")
        results["fgsm"] = {}
        for eps in [0.01, 0.03, 0.05, 0.1]:
            clean_acc, adv_acc = self.evaluate_attack(self.fgsm_attack, epsilon=eps)
            results["fgsm"][f"epsilon_{eps}"] = {
                "clean_accuracy": clean_acc,
                "adversarial_accuracy": adv_acc,
            }
            print(f"  ε={eps}: Clean={clean_acc:.2f}%, Adversarial={adv_acc:.2f}%")

        # PGD attack with varying epsilon
        print("\nPGD Attack (10 steps, α=0.01):")
        results["pgd"] = {}
        for eps in [0.01, 0.03, 0.05, 0.1]:
            clean_acc, adv_acc = self.evaluate_attack(
                self.pgd_attack, epsilon=eps, alpha=0.01, num_steps=10
            )
            results["pgd"][f"epsilon_{eps}"] = {
                "clean_accuracy": clean_acc,
                "adversarial_accuracy": adv_acc,
            }
            print(f"  ε={eps}: Clean={clean_acc:.2f}%, Adversarial={adv_acc:.2f}%")

        return results

    def visualize_adversarial_examples(self, num_examples=5):
        """Generate and visualize adversarial examples."""
        self.model.eval()
        inputs, targets = next(iter(self.test_loader))
        inputs, targets = inputs[:num_examples].to(self.device), targets[:num_examples].to(self.device)

        # Generate FGSM adversarial examples
        adv_inputs = self.fgsm_attack(inputs, targets, epsilon=0.05)

        # Denormalize for visualization
        mean = torch.tensor([0.4914, 0.4822, 0.4465]).view(1, 3, 1, 1).to(self.device)
        std = torch.tensor([0.2470, 0.2435, 0.2616]).view(1, 3, 1, 1).to(self.device)
        inputs_denorm = inputs * std + mean
        adv_inputs_denorm = adv_inputs * std + mean

        # Get predictions
        with torch.no_grad():
            outputs_clean = self.model(inputs)
            outputs_adv = self.model(adv_inputs)
            _, pred_clean = outputs_clean.max(1)
            _, pred_adv = outputs_adv.max(1)

        # Plot
        fig, axes = plt.subplots(num_examples, 3, figsize=(10, 3 * num_examples))
        class_names = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]

        for i in range(num_examples):
            # Clean image
            axes[i, 0].imshow(inputs_denorm[i].cpu().permute(1, 2, 0).clip(0, 1))
            axes[i, 0].set_title(f"Clean: {class_names[pred_clean[i]]}")
            axes[i, 0].axis("off")

            # Perturbation
            perturbation = (adv_inputs_denorm[i] - inputs_denorm[i]).abs()
            axes[i, 1].imshow(perturbation.cpu().permute(1, 2, 0) * 10)
            axes[i, 1].set_title("Perturbation (10x)")
            axes[i, 1].axis("off")

            # Adversarial image
            axes[i, 2].imshow(adv_inputs_denorm[i].cpu().permute(1, 2, 0).clip(0, 1))
            axes[i, 2].set_title(f"Adversarial: {class_names[pred_adv[i]]}")
            axes[i, 2].axis("off")

        plt.tight_layout()
        plt.savefig("./results/adversarial_examples.png", dpi=300)
        print("\nAdversarial examples saved to ./results/adversarial_examples.png")


def main():
    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Data module
    data_module = CIFAR10DataModule(batch_size=128, num_workers=4)
    data_module.setup()

    # Load model
    model = ResNet18(num_classes=10)
    checkpoint_path = Path("./checkpoints/checkpoint_best.pth")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    # Evaluate
    evaluator = AdversarialEvaluator(
        model=model,
        test_loader=data_module.test_dataloader(),
        device=device,
    )
    results = evaluator.run_full_evaluation()
    evaluator.visualize_adversarial_examples()

    # Save results
    Path("./results").mkdir(exist_ok=True)
    results_path = Path("./results/adversarial_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    main()
```

Execute the adversarial evaluation:

```bash
python src/adversarial_eval.py
```

Expect catastrophic accuracy degradation under adversarial attack. At epsilon 0.05, FGSM reduces accuracy to 30-40%, while PGD reduces it to below 10%. The visualization reveals that adversarial perturbations are imperceptible to humans but completely fool the model, demonstrating the brittleness of neural networks to adversarial manipulation. These attacks succeed because neural networks are locally linear, allowing gradient-based optimization to find worst-case perturbations efficiently.

To defend against adversarial attacks, implement adversarial training, which augments the training set with adversarial examples generated on-the-fly. This defense forces the model to learn robust features that generalize across both clean and perturbed inputs. Create the file `src/train_adversarial.py`:

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from pathlib import Path
import time
from resnet import ResNet18
from cifar10_datamodule import CIFAR10DataModule


class AdversarialTrainer:
    """
    Training with adversarial data augmentation for robustness.
    """

    def __init__(
        self,
        model,
        train_loader,
        val_loader,
        optimizer,
        scheduler,
        device,
        num_epochs=100,
        epsilon=0.03,
        alpha=0.01,
        num_attack_steps=7,
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.device = device
        self.num_epochs = num_epochs
        self.epsilon = epsilon
        self.alpha = alpha
        self.num_attack_steps = num_attack_steps

        self.criterion = nn.CrossEntropyLoss()
        self.scaler = GradScaler()

    def pgd_attack(self, inputs, targets):
        """Generate PGD adversarial examples."""
        adv_inputs = inputs.clone().detach()

        for _ in range(self.num_attack_steps):
            adv_inputs.requires_grad = True

            outputs = self.model(adv_inputs)
            loss = self.criterion(outputs, targets)
            self.model.zero_grad()
            loss.backward()

            perturbation = self.alpha * adv_inputs.grad.sign()
            adv_inputs = adv_inputs.detach() + perturbation

            perturbation = torch.clamp(adv_inputs - inputs, -self.epsilon, self.epsilon)
            adv_inputs = torch.clamp(inputs + perturbation, 0, 1).detach()

        return adv_inputs

    def train_epoch(self, epoch):
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, targets in self.train_loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Generate adversarial examples
            adv_inputs = self.pgd_attack(inputs, targets)

            # Train on adversarial examples
            self.optimizer.zero_grad()
            outputs = self.model(adv_inputs)
            loss = self.criterion(outputs, targets)
            loss.backward()
            self.optimizer.step()

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

        epoch_loss = running_loss / len(self.train_loader)
        epoch_acc = 100.0 * correct / total

        return epoch_loss, epoch_acc

    def validate(self, epoch):
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in self.val_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        epoch_loss = running_loss / len(self.val_loader)
        epoch_acc = 100.0 * correct / total

        return epoch_loss, epoch_acc

    def train(self):
        print(f"Training with adversarial augmentation (ε={self.epsilon})")

        for epoch in range(1, self.num_epochs + 1):
            start_time = time.time()

            train_loss, train_acc = self.train_epoch(epoch)
            val_loss, val_acc = self.validate(epoch)
            self.scheduler.step()

            epoch_time = time.time() - start_time

            print(
                f"Epoch {epoch:03d}/{self.num_epochs} | "
                f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
                f"Time: {epoch_time:.2f}s"
            )


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    data_module = CIFAR10DataModule(batch_size=128, num_workers=4)
    data_module.setup()

    model = ResNet18(num_classes=10)
    optimizer = optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    scheduler = optim.lr_scheduler.MultiStepLR(optimizer, milestones=[75, 90], gamma=0.1)

    trainer = AdversarialTrainer(
        model=model,
        train_loader=data_module.train_dataloader(),
        val_loader=data_module.val_dataloader(),
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        num_epochs=100,
        epsilon=0.03,
    )

    trainer.train()


if __name__ == "__main__":
    main()
```

Adversarial training significantly improves robustness at the cost of clean accuracy. Expect clean accuracy to drop to 85-87% while adversarial accuracy (under PGD with epsilon 0.03) increases to 45-50%. This tradeoff is fundamental: optimizing for worst-case perturbations reduces capacity for memorizing clean training data. In production systems, the appropriate tradeoff depends on threat model: high-security applications prioritize adversarial robustness, while consumer applications prioritize clean accuracy.

This completes Exercise 3. You have implemented comprehensive stress testing including corruption robustness evaluation, adversarial attack benchmarking, and defensive training. These techniques expose the failure modes of production ML systems and establish operational SLAs for acceptable accuracy degradation under distributional shift and adversarial manipulation.

## ML Diagnostic Cheat Sheet & Verification Checklist

This section consolidates essential diagnostic commands, profiling techniques, and verification procedures for operational PyTorch workflows. Use these tools to debug training failures, optimize performance bottlenecks, and validate deployment readiness.

**Gradient Flow Diagnostics:** When training fails to converge or exhibits exploding/vanishing gradients, inspect gradient magnitudes across layers. Insert the following hook into your training loop to log gradient norms after each backward pass:

```python
for name, param in model.named_parameters():
    if param.grad is not None:
        grad_norm = param.grad.norm().item()
        print(f"{name}: {grad_norm:.6f}")
```

Healthy gradient norms range from 1e-3 to 1e1. Norms below 1e-5 indicate vanishing gradients (add skip connections or use ReLU variants). Norms above 1e2 indicate exploding gradients (reduce learning rate or apply gradient clipping).

**Memory Profiling:** GPU out-of-memory errors are the most common PyTorch failure mode. Use `torch.cuda.memory_summary()` to inspect memory allocation:

```python
print(torch.cuda.memory_summary(device=0, abbreviated=False))
```

The summary reports allocated memory, reserved memory, and fragmentation. High fragmentation indicates many small allocations; mitigate by increasing batch size or using gradient accumulation. To profile peak memory usage during training, wrap the training loop with memory recording:

```python
torch.cuda.reset_peak_memory_stats()
# Run training loop
peak_mem = torch.cuda.max_memory_allocated() / 1e9
print(f"Peak memory: {peak_mem:.2f} GB")
```

**Autograd Graph Visualization:** Inspect the computation graph to verify backpropagation paths. Use `torchviz` to render the graph:

```bash
pip install torchviz graphviz
```

```python
from torchviz import make_dot
output = model(sample_input)
dot = make_dot(output, params=dict(model.named_parameters()))
dot.render("computation_graph", format="png")
```

Verify that all parameters requiring gradients are connected to the loss node. Disconnected parameters will not update during training.

**Kernel Profiling:** Use `torch.profiler` to capture kernel-level execution traces and identify bottlenecks:

```python
from torch.profiler import profile, ProfilerActivity, schedule

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    schedule=schedule(wait=1, warmup=1, active=3, repeat=1),
    on_trace_ready=torch.profiler.tensorboard_trace_handler('./logs/profiler'),
    record_shapes=True,
    profile_memory=True,
    with_stack=True,
) as prof:
    for step, (inputs, targets) in enumerate(train_loader):
        if step >= 5:
            break
        outputs = model(inputs.cuda())
        loss = criterion(outputs, targets.cuda())
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        prof.step()
```

Load the trace in TensorBoard to visualize kernel timeline, memory allocation, and CPU-GPU synchronization stalls.

**Numerical Stability Checks:** Verify that activations and gradients remain in valid numerical ranges. Insert assertions to catch NaN or Inf:

```python
def check_nan_inf(tensor, name):
    if torch.isnan(tensor).any():
        raise ValueError(f"NaN detected in {name}")
    if torch.isinf(tensor).any():
        raise ValueError(f"Inf detected in {name}")

# In training loop
check_nan_inf(outputs, "outputs")
check_nan_inf(loss, "loss")
```

**Reproducibility Verification:** Ensure deterministic training by seeding all random number generators:

```python
import random
import numpy as np

def seed_everything(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

seed_everything(42)
```

Run the same training script twice and verify that final loss and accuracy match to at least 4 decimal places. Divergence indicates non-deterministic operations (e.g., atomic CUDA operations).

**Checkpoint Integrity Validation:** Verify that saved checkpoints can be loaded and reproduce identical model outputs:

```python
# Save checkpoint
torch.save(model.state_dict(), "checkpoint.pth")

# Load checkpoint
model_copy = ResNet18(num_classes=10)
model_copy.load_state_dict(torch.load("checkpoint.pth"))
model_copy.eval()

# Verify outputs match
sample_input = torch.randn(1, 3, 32, 32)
with torch.no_grad():
    output1 = model(sample_input)
    output2 = model_copy(sample_input)
    assert torch.allclose(output1, output2, atol=1e-6)
```

**Inference Latency Benchmarking:** Measure inference latency under realistic serving conditions with warm-up and batch processing:

```python
def benchmark_inference(model, input_shape, num_warmup=10, num_iterations=100):
    model.eval()
    device = next(model.parameters()).device
    dummy_input = torch.randn(input_shape).to(device)

    # Warmup
    with torch.no_grad():
        for _ in range(num_warmup):
            _ = model(dummy_input)

    # Benchmark
    torch.cuda.synchronize()
    start_time = time.perf_counter()
    with torch.no_grad():
        for _ in range(num_iterations):
            _ = model(dummy_input)
    torch.cuda.synchronize()
    end_time = time.perf_counter()

    avg_latency = (end_time - start_time) / num_iterations * 1000
    return avg_latency

latency = benchmark_inference(model, (1, 3, 32, 32))
print(f"Average inference latency: {latency:.2f} ms")
```

**Model Export Validation:** Export models to ONNX for deployment and verify numerical equivalence:

```bash
pip install onnx onnxruntime
```

```python
import onnx
import onnxruntime as ort

# Export to ONNX
dummy_input = torch.randn(1, 3, 32, 32)
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
)

# Verify ONNX model
onnx_model = onnx.load("model.onnx")
onnx.checker.check_model(onnx_model)

# Run ONNX inference
ort_session = ort.InferenceSession("model.onnx")
ort_inputs = {ort_session.get_inputs()[0].name: dummy_input.numpy()}
ort_outputs = ort_session.run(None, ort_inputs)

# Compare outputs
torch_output = model(dummy_input).detach().numpy()
assert np.allclose(torch_output, ort_outputs[0], atol=1e-5)
```

**Pre-Deployment Verification Checklist:**

1. **Numerical Correctness:** Verify model outputs match reference implementation within floating-point tolerance.
2. **Gradient Flow:** Confirm all trainable parameters receive non-zero gradients during backpropagation.
3. **Memory Stability:** Profile peak memory usage and verify it remains below available GPU memory with 20% headroom.
4. **Convergence:** Train for at least 10 epochs and verify training loss decreases monotonically (excluding initial warm-up).
5. **Generalization:** Confirm validation loss tracks training loss without divergence greater than 50% relative gap.
6. **Checkpoint Integrity:** Verify saved checkpoints restore model state with bit-exact output reproduction.
7. **Inference Performance:** Benchmark inference latency and verify P99 latency meets SLA requirements.
8. **Robustness:** Evaluate accuracy on corrupted inputs and adversarial examples to quantify failure modes.
9. **Reproducibility:** Seed all RNGs and verify training runs reproduce identical results across multiple executions.
10. **Export Validation:** Export to deployment format (ONNX, TorchScript) and verify numerical equivalence with PyTorch model.

These diagnostic procedures and verification checklists establish operational discipline for production PyTorch workflows, transforming ad-hoc experimentation into reproducible engineering practice.
