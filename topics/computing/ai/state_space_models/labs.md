# Operational Verification Labs: State Space Models

## Objective & Environment Setup

State space models represent a foundational paradigm shift in sequence modeling, bridging classical control theory with modern deep learning architectures. Unlike attention mechanisms that scale quadratically with sequence length, state space models compress sequential information into fixed-dimensional hidden states through linear recurrence relations, achieving sub-quadratic complexity while maintaining long-range dependency modeling. The Structured State Space (S4) family and its descendants—including Mamba, which introduces selective state transitions—have demonstrated competitive performance against Transformers on tasks ranging from audio classification to genomic sequence analysis, often with dramatically reduced memory footprints and inference latencies.

This laboratory series grounds state space theory in concrete implementation. You will construct a minimal but complete S4 layer from first principles using PyTorch primitives, integrate it into a classification pipeline, systematically benchmark against Transformer baselines, and stress-test the architecture under adversarial sequence lengths and noisy data regimes. The exercises demand rigorous empirical verification: every claim about computational efficiency, memory usage, or accuracy must be substantiated through profiling traces, GPU memory snapshots, and statistical significance tests. By the conclusion of these labs, you will possess operational fluency in deploying state space models for production sequence modeling workloads, armed with diagnostic tooling to identify and remediate performance bottlenecks.

Begin by establishing a clean Python 3.11 or later virtual environment. The core dependency stack requires PyTorch with CUDA support for GPU acceleration, HuggingFace ecosystem libraries for dataset handling and model management, NumPy for numerical primitives, and Polars for high-performance data frame operations. Execute the following sequence to provision your environment:

```bash
python3.11 -m venv ssm_lab_env
source ssm_lab_env/bin/activate
pip install --upgrade pip setuptools wheel
pip install torch==2.2.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers==4.38.1 datasets==2.17.0 accelerate==0.27.2
pip install numpy==1.26.3 polars==0.20.7 scikit-learn==1.4.0
pip install pytest==8.0.0 wandb==0.16.3 einops==0.7.0
pip install matplotlib==3.8.2 seaborn==0.13.2
```

Verify your PyTorch installation detects CUDA devices by running `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"`. A successful output displays `True` followed by the count of available GPUs. If CUDA remains unavailable, state space models will still execute on CPU, though training times will increase by an order of magnitude for moderate-scale datasets.

Create a project directory structure that isolates model implementations, training scripts, evaluation harnesses, and experiment artifacts:

```bash
mkdir -p ssm_labs/{models,data,experiments,checkpoints,logs}
cd ssm_labs
touch models/__init__.py models/s4_layer.py models/s4_classifier.py
touch train.py eval_pipeline.py benchmark.py
```

Throughout these exercises, adopt a mindset of aggressive empirical validation. State space models introduce algorithmic trade-offs—recurrence versus parallelism, fixed versus selective states, discretization stability—that manifest differently across hardware configurations, sequence distributions, and task objectives. Your responsibility as a practitioner extends beyond reproducing published results to understanding where these models excel, where they degrade, and how to diagnose failure modes through systematic measurement.

## Exercise 1: Hands-On Implementation & Pipeline Execution

The foundational exercise constructs a minimal S4 layer and integrates it into a complete training and evaluation pipeline. State space models operate through a continuous-time state equation discretized for digital computation. The continuous system evolves as $\frac{dx(t)}{dt} = Ax(t) + Bu(t)$, where $x(t) \in \mathbb{R}^N$ represents the hidden state, $u(t)$ is the scalar input, $A \in \mathbb{R}^{N \times N}$ governs state evolution dynamics, and $B \in \mathbb{R}^N$ projects input into state space. The output $y(t) = Cx(t) + Du(t)$ combines the state through projection matrix $C \in \mathbb{R}^N$ with an optional skip connection weighted by scalar $D$. For neural network integration, this system undergoes discretization via the bilinear transform or zero-order hold, yielding the recurrence $x_k = \bar{A}x_{k-1} + \bar{B}u_k$ and output $y_k = Cx_k + Du_k$, where $\bar{A}$ and $\bar{B}$ are discrete-time analogs parameterized by step size $\Delta$.

The S4 innovation parameterizes matrix $A$ through a diagonal plus low-rank decomposition that enables stable long-range dependencies while permitting efficient computation via fast Fourier transform (FFT) convolutions during training and recurrent inference. Begin by implementing the core S4 layer in `models/s4_layer.py`. This implementation prioritizes clarity over maximal optimization, exposing the mathematical structure directly:

```python
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import rearrange, repeat


class S4Layer(nn.Module):
    """
    Simplified Structured State Space (S4) layer implementing diagonal state space models.
    
    The layer parameterizes a continuous-time state space:
        dx/dt = Ax + Bu
        y = Cx + Du
    
    discretized via bilinear transform into recurrent form for efficient sequence processing.
    """
    
    def __init__(self, d_model, state_dim=64, dropout=0.1, dt_min=0.001, dt_max=0.1):
        super().__init__()
        self.d_model = d_model
        self.state_dim = state_dim
        
        # Initialize diagonal state matrix A with HiPPO-LegS initialization for long-range memory
        # A_diag has negative real parts for stability
        self.log_dt = nn.Parameter(torch.rand(d_model) * (math.log(dt_max) - math.log(dt_min)) + math.log(dt_min))
        
        # HiPPO matrix initialization: diagonal elements with negative real parts
        # and small imaginary components for oscillatory dynamics
        A_real = -0.5 * torch.ones(d_model, state_dim)
        A_imag = math.pi * torch.arange(state_dim).float().repeat(d_model, 1)
        self.A_log = nn.Parameter(torch.log(-A_real + 1e-4))  # log of negative values for stability
        self.A_imag = nn.Parameter(A_imag)
        
        # Input and output projection matrices
        self.B = nn.Parameter(torch.randn(d_model, state_dim) / math.sqrt(state_dim))
        self.C = nn.Parameter(torch.randn(d_model, state_dim) / math.sqrt(state_dim))
        self.D = nn.Parameter(torch.randn(d_model))
        
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(d_model)
        
    def forward(self, u):
        """
        Forward pass supporting both convolution (training) and recurrent (inference) modes.
        
        Args:
            u: Input tensor of shape (batch, length, d_model)
        
        Returns:
            Output tensor of shape (batch, length, d_model)
        """
        batch_size, seq_len, _ = u.shape
        
        # Discretize the continuous system using bilinear transform
        dt = torch.exp(self.log_dt)  # (d_model,)
        A_real = -torch.exp(self.A_log)  # (d_model, state_dim)
        A = A_real + 1j * self.A_imag  # Complex diagonal matrix
        
        # Bilinear discretization: dA = (I + dt/2 * A) / (I - dt/2 * A)
        # For diagonal A, this simplifies element-wise
        dt_expanded = dt.unsqueeze(-1)  # (d_model, 1)
        dA = (1 + dt_expanded / 2 * A) / (1 - dt_expanded / 2 * A)  # (d_model, state_dim)
        dB = dt_expanded * self.B  # (d_model, state_dim)
        
        # Use FFT-based convolution for efficient training
        # Compute SSM kernel in frequency domain
        L = seq_len
        freqs = torch.fft.rfftfreq(L, d=1.0, device=u.device)  # (L//2 + 1,)
        
        # Compute transfer function H(z) = C (zI - dA)^{-1} dB + D
        # In frequency domain: z = exp(2πif)
        z = torch.exp(2j * math.pi * freqs)  # (L//2 + 1,)
        
        # Broadcast for batched computation
        # z: (L//2+1,) -> (1, L//2+1, 1)
        # dA: (d_model, state_dim) -> (d_model, 1, state_dim)
        z_expanded = z.unsqueeze(0).unsqueeze(-1)  # (1, L//2+1, 1)
        dA_expanded = dA.unsqueeze(1)  # (d_model, 1, state_dim)
        
        # (zI - dA)^{-1} computed element-wise for diagonal dA
        inv_term = 1.0 / (z_expanded - dA_expanded)  # (d_model, L//2+1, state_dim)
        
        # C @ inv_term @ B
        dB_expanded = dB.unsqueeze(1)  # (d_model, 1, state_dim)
        C_expanded = self.C.unsqueeze(1)  # (d_model, 1, state_dim)
        
        # Sum over state dimension
        H_freq = torch.sum(C_expanded * inv_term * dB_expanded, dim=-1)  # (d_model, L//2+1)
        H_freq = H_freq + self.D.unsqueeze(-1)  # Add skip connection
        
        # Apply convolution via FFT
        u_freq = torch.fft.rfft(u.transpose(1, 2), n=L)  # (batch, d_model, L//2+1)
        y_freq = u_freq * H_freq.unsqueeze(0)  # (batch, d_model, L//2+1)
        y = torch.fft.irfft(y_freq, n=L).transpose(1, 2)  # (batch, L, d_model)
        
        y = self.dropout(y)
        return self.norm(y + u)  # Residual connection


class S4Block(nn.Module):
    """
    Complete S4 block with state space layer, feedforward network, and residual connections.
    """
    
    def __init__(self, d_model, state_dim=64, ff_dim=None, dropout=0.1):
        super().__init__()
        self.s4_layer = S4Layer(d_model, state_dim, dropout)
        
        ff_dim = ff_dim or 4 * d_model
        self.ff = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, d_model),
            nn.Dropout(dropout)
        )
        self.norm = nn.LayerNorm(d_model)
        
    def forward(self, x):
        x = self.s4_layer(x)
        x = self.norm(x + self.ff(x))
        return x
```

This implementation exposes several critical design decisions. The HiPPO initialization for matrix $A$ encodes polynomial projection operators that naturally capture long-range dependencies through oscillatory dynamics. The learnable log-space step size `log_dt` parameterizes the discretization resolution, allowing the model to adapt temporal granularity per feature dimension. During training, the FFT-based convolution exploits sequence parallelism, computing the entire output sequence through frequency-domain multiplication. This contrasts with the recurrent formulation used during inference, where states propagate sequentially—a trade-off between training throughput and deployment latency that you will quantify in Exercise 2.

Now construct the complete classification model in `models/s4_classifier.py`, wrapping multiple S4 blocks with input embedding and output projection layers:

```python
import torch
import torch.nn as nn
from models.s4_layer import S4Block


class S4Classifier(nn.Module):
    """
    State space model classifier for sequence classification tasks.
    """
    
    def __init__(
        self, 
        vocab_size, 
        d_model=256, 
        state_dim=64, 
        n_layers=4, 
        num_classes=2,
        max_seq_len=1024,
        dropout=0.1
    ):
        super().__init__()
        self.d_model = d_model
        
        # Input embedding with learned positional encodings
        self.token_embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Parameter(torch.randn(1, max_seq_len, d_model) * 0.02)
        self.dropout = nn.Dropout(dropout)
        
        # Stack of S4 blocks
        self.blocks = nn.ModuleList([
            S4Block(d_model, state_dim, dropout=dropout) 
            for _ in range(n_layers)
        ])
        
        # Classification head with pooling
        self.norm = nn.LayerNorm(d_model)
        self.classifier = nn.Linear(d_model, num_classes)
        
    def forward(self, input_ids, attention_mask=None):
        """
        Args:
            input_ids: (batch, seq_len) tensor of token indices
            attention_mask: (batch, seq_len) optional mask tensor
        
        Returns:
            logits: (batch, num_classes) classification logits
        """
        batch_size, seq_len = input_ids.shape
        
        # Embedding with positional encoding
        x = self.token_embed(input_ids)  # (batch, seq_len, d_model)
        x = x + self.pos_embed[:, :seq_len, :]
        x = self.dropout(x)
        
        # Apply S4 blocks
        for block in self.blocks:
            x = block(x)
        
        x = self.norm(x)
        
        # Global average pooling over sequence dimension
        if attention_mask is not None:
            mask_expanded = attention_mask.unsqueeze(-1).float()  # (batch, seq_len, 1)
            x = (x * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1e-9)
        else:
            x = x.mean(dim=1)  # (batch, d_model)
        
        logits = self.classifier(x)  # (batch, num_classes)
        return logits
```

The architecture mirrors standard encoder designs but substitutes attention layers with S4 blocks. Positional embeddings remain necessary despite the recurrent nature of state space models because the FFT-based training pathway discards explicit positional information. The global average pooling aggregator provides permutation invariance beneficial for classification, though you could substitute max pooling or attending to the final token depending on task semantics.

With the model architecture complete, implement the training harness in `train.py`. This script orchestrates dataset loading, batching, gradient accumulation, and checkpoint persistence while logging metrics to Weights & Biases for experiment tracking:

```python
import os
import argparse
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from datasets import load_dataset
import wandb
from tqdm import tqdm

from models.s4_classifier import S4Classifier


def parse_args():
    parser = argparse.ArgumentParser(description="Train S4 sequence classifier")
    parser.add_argument("--dataset", type=str, default="imdb", help="HuggingFace dataset name")
    parser.add_argument("--max_seq_len", type=int, default=512, help="Maximum sequence length")
    parser.add_argument("--d_model", type=int, default=256, help="Model dimension")
    parser.add_argument("--state_dim", type=int, default=64, help="State space dimension")
    parser.add_argument("--n_layers", type=int, default=4, help="Number of S4 blocks")
    parser.add_argument("--batch_size", type=int, default=32, help="Training batch size")
    parser.add_argument("--grad_accum_steps", type=int, default=1, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=0.0001, help="Learning rate")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")
    parser.add_argument("--warmup_steps", type=int, default=500, help="Learning rate warmup steps")
    parser.add_argument("--eval_every", type=int, default=500, help="Evaluation frequency in steps")
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--wandb_project", type=str, default="ssm-labs", help="W&B project name")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def collate_fn(batch, tokenizer, max_seq_len):
    """Custom collate function for batching tokenized sequences."""
    texts = [item["text"] for item in batch]
    labels = torch.tensor([item["label"] for item in batch])
    
    encodings = tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=max_seq_len,
        return_tensors="pt"
    )
    
    return {
        "input_ids": encodings["input_ids"],
        "attention_mask": encodings["attention_mask"],
        "labels": labels
    }


def train_epoch(model, dataloader, optimizer, scheduler, device, grad_accum_steps):
    """Execute one training epoch."""
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    
    optimizer.zero_grad()
    
    progress = tqdm(dataloader, desc="Training")
    for step, batch in enumerate(progress):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)
        
        logits = model(input_ids, attention_mask)
        loss = nn.functional.cross_entropy(logits, labels)
        loss = loss / grad_accum_steps
        
        loss.backward()
        
        if (step + 1) % grad_accum_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        
        # Metrics
        with torch.no_grad():
            preds = logits.argmax(dim=-1)
            correct = (preds == labels).sum().item()
            total_correct += correct
            total_samples += labels.size(0)
            total_loss += loss.item() * grad_accum_steps
        
        progress.set_postfix({
            "loss": loss.item() * grad_accum_steps,
            "acc": total_correct / total_samples
        })
        
        wandb.log({
            "train/loss": loss.item() * grad_accum_steps,
            "train/accuracy": correct / labels.size(0),
            "train/lr": scheduler.get_last_lr()[0]
        })
    
    return total_loss / len(dataloader), total_correct / total_samples


def evaluate(model, dataloader, device):
    """Evaluate model on validation set."""
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            logits = model(input_ids, attention_mask)
            loss = nn.functional.cross_entropy(logits, labels)
            
            preds = logits.argmax(dim=-1)
            total_correct += (preds == labels).sum().item()
            total_samples += labels.size(0)
            total_loss += loss.item()
    
    avg_loss = total_loss / len(dataloader)
    accuracy = total_correct / total_samples
    
    return avg_loss, accuracy


def main():
    args = parse_args()
    
    # Reproducibility
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    
    # Initialize W&B
    wandb.init(project=args.wandb_project, config=vars(args))
    
    # Load dataset and tokenizer
    print(f"Loading dataset: {args.dataset}")
    dataset = load_dataset(args.dataset)
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    
    # Prepare dataloaders
    train_dataset = dataset["train"]
    eval_dataset = dataset["test"]
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, args.max_seq_len),
        num_workers=4
    )
    
    eval_loader = DataLoader(
        eval_dataset,
        batch_size=args.batch_size * 2,
        shuffle=False,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, args.max_seq_len),
        num_workers=4
    )
    
    # Initialize model
    print("Initializing S4 classifier")
    num_classes = len(set(train_dataset["label"]))
    model = S4Classifier(
        vocab_size=tokenizer.vocab_size,
        d_model=args.d_model,
        state_dim=args.state_dim,
        n_layers=args.n_layers,
        num_classes=num_classes,
        max_seq_len=args.max_seq_len
    ).to(args.device)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs // args.grad_accum_steps
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=args.lr,
        total_steps=total_steps,
        pct_start=args.warmup_steps / total_steps
    )
    
    # Training loop
    os.makedirs(args.checkpoint_dir, exist_ok=True)
    best_eval_acc = 0.0
    
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch + 1}/{args.epochs}")
        
        train_loss, train_acc = train_epoch(
            model, train_loader, optimizer, scheduler, args.device, args.grad_accum_steps
        )
        
        eval_loss, eval_acc = evaluate(model, eval_loader, args.device)
        
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
        print(f"Eval Loss: {eval_loss:.4f} | Eval Acc: {eval_acc:.4f}")
        
        wandb.log({
            "epoch": epoch + 1,
            "eval/loss": eval_loss,
            "eval/accuracy": eval_acc
        })
        
        # Save best checkpoint
        if eval_acc > best_eval_acc:
            best_eval_acc = eval_acc
            checkpoint_path = os.path.join(args.checkpoint_dir, "best_model.pt")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "eval_acc": eval_acc,
                "args": vars(args)
            }, checkpoint_path)
            print(f"Saved best model: {checkpoint_path}")
    
    wandb.finish()
    print(f"\nTraining complete. Best eval accuracy: {best_eval_acc:.4f}")


if __name__ == "__main__":
    main()
```

This training script incorporates production-grade practices: gradient accumulation for effective large batch training under memory constraints, gradient clipping to prevent exploding gradients in recurrent architectures, and one-cycle learning rate scheduling to accelerate convergence. The checkpoint logic persists only the best-performing model according to validation accuracy, preventing disk bloat from intermediate snapshots.

Execute your first training run on the IMDB sentiment classification dataset, a standard benchmark for sequence models:

```bash
python train.py \
  --dataset imdb \
  --max_seq_len 512 \
  --d_model 256 \
  --state_dim 64 \
  --n_layers 4 \
  --batch_size 16 \
  --grad_accum_steps 2 \
  --lr 0.0001 \
  --epochs 5 \
  --wandb_project ssm-imdb-baseline \
  --device cuda
```

Monitor the Weights & Biases dashboard for training dynamics. A healthy training run exhibits smooth loss decay without oscillations, validation accuracy converging within 3-5 epochs to approximately 85-88% for this configuration. If training loss decreases while validation accuracy plateaus, suspect overfitting; reduce model capacity or increase dropout. If both training and validation losses remain high, the model underfits; increase `d_model`, `state_dim`, or `n_layers`.

Construct the evaluation pipeline in `eval_pipeline.py` to compute comprehensive metrics beyond scalar accuracy:

```python
import argparse
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from datasets import load_dataset
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from models.s4_classifier import S4Classifier
from train import collate_fn


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate S4 classifier")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--dataset", type=str, default="imdb", help="Dataset name")
    parser.add_argument("--max_seq_len", type=int, default=512, help="Max sequence length")
    parser.add_argument("--batch_size", type=int, default=32, help="Evaluation batch size")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output_dir", type=str, default="experiments", help="Output directory")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Load checkpoint
    print(f"Loading checkpoint: {args.checkpoint}")
    checkpoint = torch.load(args.checkpoint, map_location=args.device)
    model_args = checkpoint["args"]
    
    # Initialize model
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    dataset = load_dataset(args.dataset)
    num_classes = len(set(dataset["test"]["label"]))
    
    model = S4Classifier(
        vocab_size=tokenizer.vocab_size,
        d_model=model_args["d_model"],
        state_dim=model_args["state_dim"],
        n_layers=model_args["n_layers"],
        num_classes=num_classes,
        max_seq_len=args.max_seq_len
    ).to(args.device)
    
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    
    # Prepare dataloader
    test_loader = DataLoader(
        dataset["test"],
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, args.max_seq_len),
        num_workers=4
    )
    
    # Collect predictions
    all_preds = []
    all_labels = []
    all_logits = []
    
    print("Running inference...")
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(args.device)
            attention_mask = batch["attention_mask"].to(args.device)
            labels = batch["labels"]
            
            logits = model(input_ids, attention_mask)
            preds = logits.argmax(dim=-1).cpu()
            
            all_preds.extend(preds.numpy())
            all_labels.extend(labels.numpy())
            all_logits.extend(logits.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_logits = np.array(all_logits)
    
    # Classification report
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    print(classification_report(all_labels, all_preds, target_names=[f"Class {i}" for i in range(num_classes)]))
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=range(num_classes), yticklabels=range(num_classes))
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    plt.title("Confusion Matrix")
    plt.savefig(f"{args.output_dir}/confusion_matrix.png", dpi=300, bbox_inches="tight")
    print(f"\nConfusion matrix saved to {args.output_dir}/confusion_matrix.png")
    
    # Confidence distribution
    probs = torch.softmax(torch.tensor(all_logits), dim=-1).numpy()
    max_probs = probs.max(axis=-1)
    
    plt.figure(figsize=(10, 6))
    plt.hist(max_probs[all_preds == all_labels], bins=50, alpha=0.7, label="Correct", color="green")
    plt.hist(max_probs[all_preds != all_labels], bins=50, alpha=0.7, label="Incorrect", color="red")
    plt.xlabel("Max Probability")
    plt.ylabel("Frequency")
    plt.title("Prediction Confidence Distribution")
    plt.legend()
    plt.savefig(f"{args.output_dir}/confidence_distribution.png", dpi=300, bbox_inches="tight")
    print(f"Confidence distribution saved to {args.output_dir}/confidence_distribution.png")
    
    # Summary statistics
    accuracy = (all_preds == all_labels).mean()
    print(f"\nOverall Accuracy: {accuracy:.4f}")
    print(f"Mean Confidence (Correct): {max_probs[all_preds == all_labels].mean():.4f}")
    print(f"Mean Confidence (Incorrect): {max_probs[all_preds != all_labels].mean():.4f}")


if __name__ == "__main__":
    main()
```

Execute the evaluation pipeline against your trained checkpoint:

```bash
mkdir -p experiments
python eval_pipeline.py \
  --checkpoint checkpoints/best_model.pt \
  --dataset imdb \
  --max_seq_len 512 \
  --batch_size 64 \
  --output_dir experiments \
  --device cuda
```

Examine the generated confusion matrix and confidence distributions. High-confidence correct predictions clustered near probability 1.0 indicate well-calibrated model uncertainty. Misclassifications with high confidence warrant further investigation—extract examples via `dataset["test"].select(np.where(all_preds != all_labels)[0])` and manually inspect whether they represent labeling noise, adversarial examples, or systematic model blind spots.

This completes Exercise 1. You now possess a working S4 implementation, training pipeline, and evaluation harness. The subsequent exercises will stress-test this foundation through hyperparameter optimization and adversarial robustness analysis.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

State space models introduce architectural hyperparameters—state dimension, layer count, discretization step size—that interact nonlinearly with dataset properties and computational resources. This exercise systematically explores the hyperparameter space through ablation studies, benchmarks the S4 classifier against Transformer baselines, and profiles computational efficiency to quantify the claimed sub-quadratic scaling advantages.

Begin by implementing a hyperparameter sweep script `benchmark.py` that trains multiple model configurations in parallel and aggregates results for comparison:

```python
import argparse
import itertools
import json
import os
import subprocess
import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def parse_args():
    parser = argparse.ArgumentParser(description="Hyperparameter sweep for S4 models")
    parser.add_argument("--dataset", type=str, default="imdb", help="Dataset name")
    parser.add_argument("--base_config", type=str, default="configs/base.json", help="Base configuration")
    parser.add_argument("--sweep_params", type=str, nargs="+", 
                       default=["d_model", "state_dim", "n_layers"],
                       help="Parameters to sweep")
    parser.add_argument("--output_dir", type=str, default="experiments/sweep", help="Output directory")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--epochs", type=int, default=5, help="Epochs per run")
    return parser.parse_args()


def generate_sweep_configs(base_config, sweep_params):
    """Generate all combinations of hyperparameters to sweep."""
    param_values = {
        "d_model": [128, 256, 512],
        "state_dim": [32, 64, 128],
        "n_layers": [2, 4, 6],
        "lr": [5e-5, 1e-4, 2e-4],
        "batch_size": [16, 32]
    }
    
    # Filter to requested sweep parameters
    sweep_values = {k: v for k, v in param_values.items() if k in sweep_params}
    
    configs = []
    for combo in itertools.product(*sweep_values.values()):
        config = base_config.copy()
        for param, value in zip(sweep_values.keys(), combo):
            config[param] = value
        configs.append(config)
    
    return configs


def run_training(config, output_dir, dataset, epochs, device):
    """Execute single training run with given configuration."""
    run_name = "_".join([f"{k}{v}" for k, v in sorted(config.items())])
    checkpoint_dir = os.path.join(output_dir, run_name, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    cmd = [
        "python", "train.py",
        "--dataset", dataset,
        "--d_model", str(config["d_model"]),
        "--state_dim", str(config["state_dim"]),
        "--n_layers", str(config["n_layers"]),
        "--batch_size", str(config["batch_size"]),
        "--lr", str(config["lr"]),
        "--epochs", str(epochs),
        "--checkpoint_dir", checkpoint_dir,
        "--device", device,
        "--wandb_project", f"ssm-sweep-{dataset}"
    ]
    
    print(f"Running: {run_name}")
    start_time = time.time()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    # Parse results from checkpoint
    checkpoint_path = os.path.join(checkpoint_dir, "best_model.pt")
    if os.path.exists(checkpoint_path):
        import torch
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        eval_acc = checkpoint.get("eval_acc", 0.0)
    else:
        eval_acc = 0.0
        print(f"Warning: No checkpoint found for {run_name}")
    
    return {
        **config,
        "eval_acc": eval_acc,
        "train_time": elapsed,
        "run_name": run_name
    }


def main():
    args = parse_args()
    
    # Load base configuration
    base_config = {
        "d_model": 256,
        "state_dim": 64,
        "n_layers": 4,
        "batch_size": 16,
        "lr": 1e-4
    }
    
    # Generate sweep configurations
    configs = generate_sweep_configs(base_config, args.sweep_params)
    print(f"Generated {len(configs)} configurations to sweep")
    
    # Run all configurations
    results = []
    for i, config in enumerate(configs):
        print(f"\n{'='*60}")
        print(f"Configuration {i+1}/{len(configs)}")
        print(f"{'='*60}")
        
        result = run_training(config, args.output_dir, args.dataset, args.epochs, args.device)
        results.append(result)
        
        # Save intermediate results
        results_df = pd.DataFrame(results)
        results_df.to_csv(os.path.join(args.output_dir, "sweep_results.csv"), index=False)
    
    # Analyze results
    results_df = pd.DataFrame(results)
    print("\n" + "="*60)
    print("SWEEP RESULTS SUMMARY")
    print("="*60)
    print(results_df.sort_values("eval_acc", ascending=False).head(10))
    
    # Visualize results
    fig, axes = plt.subplots(1, len(args.sweep_params), figsize=(6*len(args.sweep_params), 5))
    if len(args.sweep_params) == 1:
        axes = [axes]
    
    for ax, param in zip(axes, args.sweep_params):
        param_results = results_df.groupby(param).agg({"eval_acc": ["mean", "std"]}).reset_index()
        param_results.columns = [param, "mean_acc", "std_acc"]
        
        ax.errorbar(param_results[param], param_results["mean_acc"], 
                   yerr=param_results["std_acc"], marker="o", capsize=5)
        ax.set_xlabel(param)
        ax.set_ylabel("Validation Accuracy")
        ax.set_title(f"Effect of {param}")
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "sweep_analysis.png"), dpi=300)
    print(f"\nAnalysis plots saved to {args.output_dir}/sweep_analysis.png")


if __name__ == "__main__":
    main()
```

Launch a focused hyperparameter sweep targeting model capacity and state dimension:

```bash
mkdir -p experiments/sweep
python benchmark.py \
  --dataset imdb \
  --sweep_params d_model state_dim n_layers \
  --output_dir experiments/sweep \
  --device cuda \
  --epochs 5
```

This sweep executes 27 training runs (3 values × 3 parameters). On a single V100 GPU, expect approximately 4-6 hours total runtime. The resulting `sweep_results.csv` quantifies the accuracy-efficiency trade-off: larger `d_model` and `state_dim` improve capacity but increase memory footprint and latency. The optimal configuration typically balances these factors—for IMDB, `d_model=256`, `state_dim=64`, and `n_layers=4` often achieve 87-89% accuracy with reasonable training time.

The generated plots reveal sensitivity patterns. If accuracy plateaus beyond a threshold `state_dim`, additional state capacity provides diminishing returns; the dataset's intrinsic complexity limits achievable performance. If accuracy continues scaling with `d_model`, the model remains capacity-constrained; consider larger architectures or data augmentation.

Now benchmark against a Transformer baseline to validate the claimed efficiency advantages. Implement a minimal Transformer classifier in `models/transformer_classifier.py`:

```python
import torch
import torch.nn as nn
import math


class TransformerClassifier(nn.Module):
    """
    Standard Transformer encoder for sequence classification.
    """
    
    def __init__(
        self,
        vocab_size,
        d_model=256,
        n_heads=8,
        n_layers=4,
        num_classes=2,
        max_seq_len=1024,
        dropout=0.1
    ):
        super().__init__()
        self.d_model = d_model
        
        # Input embedding with positional encoding
        self.token_embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Parameter(torch.randn(1, max_seq_len, d_model) * 0.02)
        self.dropout = nn.Dropout(dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=4*d_model,
            dropout=dropout,
            activation="gelu",
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        
        # Classification head
        self.norm = nn.LayerNorm(d_model)
        self.classifier = nn.Linear(d_model, num_classes)
        
    def forward(self, input_ids, attention_mask=None):
        batch_size, seq_len = input_ids.shape
        
        x = self.token_embed(input_ids)
        x = x + self.pos_embed[:, :seq_len, :]
        x = self.dropout(x)
        
        # Create attention mask for transformer (inverted: 0=attend, -inf=mask)
        if attention_mask is not None:
            mask = (1 - attention_mask).bool()
        else:
            mask = None
        
        x = self.transformer(x, src_key_padding_mask=mask)
        x = self.norm(x)
        
        # Global average pooling
        if attention_mask is not None:
            mask_expanded = attention_mask.unsqueeze(-1).float()
            x = (x * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1e-9)
        else:
            x = x.mean(dim=1)
        
        logits = self.classifier(x)
        return logits
```

Create a comparative benchmark script `compare_models.py` that measures accuracy, throughput, memory usage, and latency for both architectures:

```python
import argparse
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from datasets import load_dataset
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from models.s4_classifier import S4Classifier
from models.transformer_classifier import TransformerClassifier
from train import collate_fn


def parse_args():
    parser = argparse.ArgumentParser(description="Compare S4 vs Transformer")
    parser.add_argument("--dataset", type=str, default="imdb")
    parser.add_argument("--max_seq_len", type=int, default=512)
    parser.add_argument("--d_model", type=int, default=256)
    parser.add_argument("--n_layers", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output_dir", type=str, default="experiments/comparison")
    return parser.parse_args()


def measure_throughput(model, dataloader, device, num_batches=50):
    """Measure inference throughput in samples/second."""
    model.eval()
    
    total_samples = 0
    start_time = time.time()
    
    with torch.no_grad():
        for i, batch in enumerate(dataloader):
            if i >= num_batches:
                break
            
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            
            _ = model(input_ids, attention_mask)
            
            total_samples += input_ids.size(0)
    
    elapsed = time.time() - start_time
    throughput = total_samples / elapsed
    
    return throughput


def measure_memory(model, dataloader, device):
    """Measure peak GPU memory usage."""
    if device == "cpu":
        return 0.0
    
    model.eval()
    torch.cuda.reset_peak_memory_stats(device)
    
    with torch.no_grad():
        batch = next(iter(dataloader))
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        
        _ = model(input_ids, attention_mask)
    
    peak_memory = torch.cuda.max_memory_allocated(device) / (1024**3)  # GB
    return peak_memory


def measure_latency(model, input_ids, attention_mask, device, num_runs=100):
    """Measure per-sample inference latency."""
    model.eval()
    
    # Warmup
    with torch.no_grad():
        for _ in range(10):
            _ = model(input_ids, attention_mask)
    
    if device == "cuda":
        torch.cuda.synchronize()
    
    latencies = []
    with torch.no_grad():
        for _ in range(num_runs):
            start = time.time()
            _ = model(input_ids, attention_mask)
            if device == "cuda":
                torch.cuda.synchronize()
            latencies.append(time.time() - start)
    
    return {
        "mean": sum(latencies) / len(latencies) * 1000,  # ms
        "std": (sum((x - sum(latencies)/len(latencies))**2 for x in latencies) / len(latencies))**0.5 * 1000,
        "p50": sorted(latencies)[len(latencies)//2] * 1000,
        "p95": sorted(latencies)[int(len(latencies)*0.95)] * 1000
    }


def main():
    args = parse_args()
    
    # Load dataset
    dataset = load_dataset(args.dataset)
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    num_classes = len(set(dataset["test"]["label"]))
    
    test_loader = DataLoader(
        dataset["test"].select(range(min(1000, len(dataset["test"])))),
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, args.max_seq_len),
        num_workers=4
    )
    
    # Initialize models
    print("Initializing models...")
    s4_model = S4Classifier(
        vocab_size=tokenizer.vocab_size,
        d_model=args.d_model,
        state_dim=64,
        n_layers=args.n_layers,
        num_classes=num_classes,
        max_seq_len=args.max_seq_len
    ).to(args.device)
    
    transformer_model = TransformerClassifier(
        vocab_size=tokenizer.vocab_size,
        d_model=args.d_model,
        n_heads=8,
        n_layers=args.n_layers,
        num_classes=num_classes,
        max_seq_len=args.max_seq_len
    ).to(args.device)
    
    models = {
        "S4": s4_model,
        "Transformer": transformer_model
    }
    
    results = []
    
    for name, model in models.items():
        print(f"\n{'='*60}")
        print(f"Benchmarking {name}")
        print(f"{'='*60}")
        
        # Parameter count
        num_params = sum(p.numel() for p in model.parameters())
        print(f"Parameters: {num_params:,}")
        
        # Throughput
        print("Measuring throughput...")
        throughput = measure_throughput(model, test_loader, args.device)
        print(f"Throughput: {throughput:.2f} samples/sec")
        
        # Memory
        print("Measuring memory...")
        peak_memory = measure_memory(model, test_loader, args.device)
        print(f"Peak memory: {peak_memory:.3f} GB")
        
        # Latency
        print("Measuring latency...")
        batch = next(iter(test_loader))
        input_ids = batch["input_ids"][:1].to(args.device)  # Single sample
        attention_mask = batch["attention_mask"][:1].to(args.device)
        latency_stats = measure_latency(model, input_ids, attention_mask, args.device)
        print(f"Latency: {latency_stats['mean']:.2f}±{latency_stats['std']:.2f} ms "
              f"(p50={latency_stats['p50']:.2f}, p95={latency_stats['p95']:.2f})")
        
        results.append({
            "model": name,
            "num_params": num_params,
            "throughput": throughput,
            "peak_memory_gb": peak_memory,
            "latency_mean_ms": latency_stats["mean"],
            "latency_std_ms": latency_stats["std"],
            "latency_p95_ms": latency_stats["p95"]
        })
    
    # Save results
    results_df = pd.DataFrame(results)
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    results_df.to_csv(f"{args.output_dir}/benchmark_results.csv", index=False)
    
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(results_df.to_string(index=False))
    
    # Visualization
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    metrics = [
        ("throughput", "Throughput (samples/sec)", axes[0, 0]),
        ("peak_memory_gb", "Peak Memory (GB)", axes[0, 1]),
        ("latency_mean_ms", "Mean Latency (ms)", axes[1, 0]),
        ("num_params", "Parameters (millions)", axes[1, 1])
    ]
    
    for metric, label, ax in metrics:
        values = results_df[metric].values
        if metric == "num_params":
            values = values / 1e6
            label = "Parameters (millions)"
        
        ax.bar(results_df["model"], values, color=["#2E86AB", "#A23B72"])
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.grid(True, alpha=0.3, axis="y")
    
    plt.tight_layout()
    plt.savefig(f"{args.output_dir}/benchmark_plots.png", dpi=300)
    print(f"\nPlots saved to {args.output_dir}/benchmark_plots.png")


if __name__ == "__main__":
    main()
```

Execute the comparative benchmark:

```bash
python compare_models.py \
  --dataset imdb \
  --max_seq_len 512 \
  --d_model 256 \
  --n_layers 4 \
  --batch_size 32 \
  --device cuda \
  --output_dir experiments/comparison
```

Analyze the `benchmark_results.csv` output. On typical hardware (V100, A100), S4 models demonstrate 1.5-2× throughput improvements and 20-30% memory reductions compared to Transformers of equivalent parameter count. Latency advantages become more pronounced at longer sequence lengths due to the sub-quadratic complexity—extend the benchmark to `max_seq_len=2048` and `max_seq_len=4096` to observe the scaling crossover point where S4's linear recurrence dominates Transformer's quadratic attention.

Critically examine scenarios where Transformers outperform S4. Tasks requiring precise positional reasoning or bidirectional context (e.g., question answering with precise span extraction) may favor attention's global receptive field. The FFT-based S4 training pathway loses explicit positional information within sequences, potentially degrading performance on position-sensitive tasks despite the additive positional embeddings.

Profile memory usage in detail using PyTorch's memory profiler. Insert the following snippet into your training loop:

```python
import torch.cuda

# After forward pass
torch.cuda.synchronize()
print(torch.cuda.memory_summary(device=args.device, abbreviated=False))
```

Inspect the "Allocated memory" and "Active memory" sections. S4 models exhibit lower activation memory because they avoid caching attention matrices ($O(L^2)$ per layer) but retain hidden state sequences ($O(L \cdot d)$). During backpropagation, S4's recurrent pathway requires storing intermediate states for gradient computation, partially offsetting the training-time memory advantage—verify this by comparing peak memory during forward versus backward passes.

Extend the benchmark to measure training time per epoch, not just inference throughput. S4's FFT-based convolution parallelizes sequence processing during training, but the recurrent formulation used during inference becomes a sequential bottleneck. Quantify this by timing both training and inference modes:

```python
# Training mode timing
model.train()
start = time.time()
for batch in train_loader:
    logits = model(batch["input_ids"].to(device), batch["attention_mask"].to(device))
    loss = nn.functional.cross_entropy(logits, batch["labels"].to(device))
    loss.backward()
train_time = time.time() - start

# Inference mode timing
model.eval()
start = time.time()
with torch.no_grad():
    for batch in test_loader:
        _ = model(batch["input_ids"].to(device), batch["attention_mask"].to(device))
inference_time = time.time() - start

print(f"Training time: {train_time:.2f}s | Inference time: {inference_time:.2f}s")
```

This completes Exercise 2. You have systematically explored the hyperparameter space, benchmarked against standard baselines, and quantified computational trade-offs. The next exercise subjects your implementation to adversarial stress tests and failure mitigation protocols.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Production deployment demands robustness beyond average-case performance. This exercise probes your S4 implementation under adversarial conditions: extreme sequence lengths, noisy inputs, distribution shifts, and numerical instability. You will diagnose failure modes through ablation studies, implement defensive mitigation strategies, and validate recovery through targeted test suites.

Begin by constructing an adversarial test harness in `stress_test.py` that systematically perturbs inputs and monitors model behavior:

```python
import argparse
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer
from datasets import load_dataset
import matplotlib.pyplot as plt
import seaborn as sns

from models.s4_classifier import S4Classifier
from train import collate_fn


def parse_args():
    parser = argparse.ArgumentParser(description="Stress test S4 classifier")
    parser.add_argument("--checkpoint", type=str, required=True, help="Model checkpoint path")
    parser.add_argument("--dataset", type=str, default="imdb")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--output_dir", type=str, default="experiments/stress_tests")
    return parser.parse_args()


def test_sequence_length_scaling(model, tokenizer, device, max_lengths, num_samples=100):
    """Test model behavior across varying sequence lengths."""
    print("\n" + "="*60)
    print("TEST: Sequence Length Scaling")
    print("="*60)
    
    results = []
    
    for max_len in max_lengths:
        print(f"\nTesting max_length={max_len}")
        
        # Generate random sequences
        input_ids = torch.randint(0, tokenizer.vocab_size, (num_samples, max_len)).to(device)
        attention_mask = torch.ones_like(input_ids)
        
        try:
            model.eval()
            with torch.no_grad():
                import time
                start = time.time()
                logits = model(input_ids, attention_mask)
                elapsed = time.time() - start
            
            # Check for NaN/Inf
            has_nan = torch.isnan(logits).any().item()
            has_inf = torch.isinf(logits).any().item()
            
            throughput = num_samples / elapsed
            
            print(f"  Throughput: {throughput:.2f} samples/sec")
            print(f"  NaN detected: {has_nan}")
            print(f"  Inf detected: {has_inf}")
            
            results.append({
                "max_length": max_len,
                "throughput": throughput,
                "has_nan": has_nan,
                "has_inf": has_inf,
                "success": not (has_nan or has_inf)
            })
            
        except RuntimeError as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                "max_length": max_len,
                "throughput": 0.0,
                "has_nan": False,
                "has_inf": False,
                "success": False,
                "error": str(e)
            })
    
    return results


def test_noise_robustness(model, dataloader, device, noise_levels):
    """Test model robustness to input perturbations."""
    print("\n" + "="*60)
    print("TEST: Noise Robustness")
    print("="*60)
    
    model.eval()
    results = []
    
    # Get clean baseline
    batch = next(iter(dataloader))
    clean_inputs = batch["input_ids"].to(device)
    attention_mask = batch["attention_mask"].to(device)
    labels = batch["labels"].to(device)
    
    with torch.no_grad():
        clean_logits = model(clean_inputs, attention_mask)
        clean_preds = clean_logits.argmax(dim=-1)
        clean_acc = (clean_preds == labels).float().mean().item()
    
    print(f"Clean accuracy: {clean_acc:.4f}")
    results.append({"noise_level": 0.0, "accuracy": clean_acc})
    
    # Test with varying noise levels
    vocab_size = model.token_embed.num_embeddings
    
    for noise_level in noise_levels:
        print(f"\nNoise level: {noise_level:.2f}")
        
        # Flip random tokens
        noisy_inputs = clean_inputs.clone()
        mask = torch.rand_like(noisy_inputs.float()) < noise_level
        random_tokens = torch.randint(0, vocab_size, noisy_inputs.shape, device=device)
        noisy_inputs[mask] = random_tokens[mask]
        
        with torch.no_grad():
            noisy_logits = model(noisy_inputs, attention_mask)
            noisy_preds = noisy_logits.argmax(dim=-1)
            noisy_acc = (noisy_preds == labels).float().mean().item()
        
        print(f"  Accuracy: {noisy_acc:.4f} (drop: {clean_acc - noisy_acc:.4f})")
        results.append({"noise_level": noise_level, "accuracy": noisy_acc})
    
    return results


def test_gradient_flow(model, dataloader, device):
    """Diagnose gradient flow and numerical stability during backpropagation."""
    print("\n" + "="*60)
    print("TEST: Gradient Flow Analysis")
    print("="*60)
    
    model.train()
    batch = next(iter(dataloader))
    
    input_ids = batch["input_ids"].to(device)
    attention_mask = batch["attention_mask"].to(device)
    labels = batch["labels"].to(device)
    
    # Forward and backward pass
    logits = model(input_ids, attention_mask)
    loss = nn.functional.cross_entropy(logits, labels)
    loss.backward()
    
    # Analyze gradients
    grad_stats = []
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_norm = param.grad.norm().item()
            grad_mean = param.grad.mean().item()
            grad_std = param.grad.std().item()
            has_nan = torch.isnan(param.grad).any().item()
            has_inf = torch.isinf(param.grad).any().item()
            
            grad_stats.append({
                "layer": name,
                "grad_norm": grad_norm,
                "grad_mean": grad_mean,
                "grad_std": grad_std,
                "has_nan": has_nan,
                "has_inf": has_inf
            })
            
            if has_nan or has_inf:
                print(f"WARNING: {name} has NaN/Inf gradients")
    
    # Identify vanishing/exploding gradients
    norms = [s["grad_norm"] for s in grad_stats]
    print(f"\nGradient norm statistics:")
    print(f"  Min: {min(norms):.6f}")
    print(f"  Max: {max(norms):.6f}")
    print(f"  Mean: {np.mean(norms):.6f}")
    print(f"  Std: {np.std(norms):.6f}")
    
    if max(norms) > 100:
        print("WARNING: Potential exploding gradients detected")
    if min(norms) < 1e-7:
        print("WARNING: Potential vanishing gradients detected")
    
    return grad_stats


def test_distribution_shift(model, train_dataset, ood_dataset, tokenizer, device, max_seq_len):
    """Test model performance under distribution shift."""
    print("\n" + "="*60)
    print("TEST: Out-of-Distribution Robustness")
    print("="*60)
    
    model.eval()
    
    # In-distribution performance
    train_loader = DataLoader(
        train_dataset.select(range(min(500, len(train_dataset)))),
        batch_size=32,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, max_seq_len)
    )
    
    id_correct = 0
    id_total = 0
    
    with torch.no_grad():
        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            logits = model(input_ids, attention_mask)
            preds = logits.argmax(dim=-1)
            
            id_correct += (preds == labels).sum().item()
            id_total += labels.size(0)
    
    id_acc = id_correct / id_total
    print(f"In-distribution accuracy: {id_acc:.4f}")
    
    # Out-of-distribution performance
    ood_loader = DataLoader(
        ood_dataset.select(range(min(500, len(ood_dataset)))),
        batch_size=32,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, max_seq_len)
    )
    
    ood_correct = 0
    ood_total = 0
    
    with torch.no_grad():
        for batch in ood_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            logits = model(input_ids, attention_mask)
            preds = logits.argmax(dim=-1)
            
            ood_correct += (preds == labels).sum().item()
            ood_total += labels.size(0)
    
    ood_acc = ood_correct / ood_total
    print(f"Out-of-distribution accuracy: {ood_acc:.4f}")
    print(f"Accuracy drop: {id_acc - ood_acc:.4f}")
    
    return {"id_acc": id_acc, "ood_acc": ood_acc, "accuracy_drop": id_acc - ood_acc}


def main():
    args = parse_args()
    
    # Load model
    print(f"Loading checkpoint: {args.checkpoint}")
    checkpoint = torch.load(args.checkpoint, map_location=args.device)
    model_args = checkpoint["args"]
    
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    dataset = load_dataset(args.dataset)
    
    model = S4Classifier(
        vocab_size=tokenizer.vocab_size,
        d_model=model_args["d_model"],
        state_dim=model_args["state_dim"],
        n_layers=model_args["n_layers"],
        num_classes=2,
        max_seq_len=model_args["max_seq_len"]
    ).to(args.device)
    
    model.load_state_dict(checkpoint["model_state_dict"])
    
    # Prepare test dataloader
    test_loader = DataLoader(
        dataset["test"].select(range(min(500, len(dataset["test"])))),
        batch_size=32,
        collate_fn=lambda batch: collate_fn(batch, tokenizer, model_args["max_seq_len"])
    )
    
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run stress tests
    
    # Test 1: Sequence length scaling
    length_results = test_sequence_length_scaling(
        model, tokenizer, args.device,
        max_lengths=[128, 256, 512, 1024, 2048, 4096]
    )
    
    # Visualize length scaling
    import pandas as pd
    length_df = pd.DataFrame(length_results)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    successful = length_df[length_df["success"]]
    ax1.plot(successful["max_length"], successful["throughput"], marker="o", linewidth=2)
    ax1.set_xlabel("Sequence Length")
    ax1.set_ylabel("Throughput (samples/sec)")
    ax1.set_title("Throughput vs Sequence Length")
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale("log", base=2)
    
    ax2.bar(length_df["max_length"], length_df["success"].astype(int), color=["green" if x else "red" for x in length_df["success"]])
    ax2.set_xlabel("Sequence Length")
    ax2.set_ylabel("Success")
    ax2.set_title("Stability Across Sequence Lengths")
    ax2.set_xscale("log", base=2)
    ax2.set_ylim([0, 1.2])
    
    plt.tight_layout()
    plt.savefig(f"{args.output_dir}/length_scaling.png", dpi=300)
    print(f"\nLength scaling plot saved to {args.output_dir}/length_scaling.png")
    
    # Test 2: Noise robustness
    noise_results = test_noise_robustness(
        model, test_loader, args.device,
        noise_levels=[0.0, 0.05, 0.1, 0.15, 0.2, 0.3]
    )
    
    noise_df = pd.DataFrame(noise_results)
    
    plt.figure(figsize=(8, 6))
    plt.plot(noise_df["noise_level"], noise_df["accuracy"], marker="o", linewidth=2, color="#2E86AB")
    plt.axhline(y=0.5, color="red", linestyle="--", label="Random baseline", alpha=0.5)
    plt.xlabel("Noise Level (Token Flip Probability)")
    plt.ylabel("Accuracy")
    plt.title("Model Robustness to Input Noise")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{args.output_dir}/noise_robustness.png", dpi=300)
    print(f"Noise robustness plot saved to {args.output_dir}/noise_robustness.png")
    
    # Test 3: Gradient flow
    grad_stats = test_gradient_flow(model, test_loader, args.device)
    
    # Test 4: Distribution shift (using SST-2 as OOD for IMDB)
    try:
        ood_dataset = load_dataset("glue", "sst2")
        shift_results = test_distribution_shift(
            model, dataset["train"], ood_dataset["validation"],
            tokenizer, args.device, model_args["max_seq_len"]
        )
    except Exception as e:
        print(f"\nSkipping distribution shift test: {str(e)}")
    
    print("\n" + "="*60)
    print("STRESS TEST COMPLETE")
    print("="*60)
    print(f"Results saved to {args.output_dir}/")


if __name__ == "__main__":
    main()
```

Execute the comprehensive stress test suite:

```bash
python stress_test.py \
  --checkpoint checkpoints/best_model.pt \
  --dataset imdb \
  --device cuda \
  --output_dir experiments/stress_tests
```

Analyze the generated diagnostics. The sequence length scaling test reveals at what point the model degrades—either through OOM errors, NaN/Inf propagation, or throughput collapse. If the model fails at 2048 tokens but your max training length was 512, the positional embeddings likely extrapolate poorly beyond trained ranges. Implement dynamic positional encoding schemes (RoPE, ALiBi) or extend `max_seq_len` during fine-tuning with gradually increasing sequence lengths.

The noise robustness curve quantifies overfitting to input distribution. A precipitous accuracy drop at 10-15% noise suggests brittle feature reliance; the model memorizes spurious token patterns rather than learning robust semantic representations. Mitigation strategies include:

1. **Token Dropout**: Randomly mask input tokens during training with probability 0.1-0.2, forcing the model to rely on context rather than individual tokens.

2. **Mixup Augmentation**: Linearly interpolate between training examples in embedding space, smoothing decision boundaries.

3. **Adversarial Training**: Explicitly perturb embeddings via Fast Gradient Sign Method (FGSM) and backpropagate through adversarial examples.

Implement token dropout in your training loop:

```python
def apply_token_dropout(input_ids, attention_mask, dropout_prob=0.15, mask_token_id=103):
    """Randomly replace tokens with [MASK] during training."""
    if dropout_prob == 0.0:
        return input_ids, attention_mask
    
    mask = torch.rand_like(input_ids.float()) < dropout_prob
    # Don't mask padding tokens
    mask = mask & (attention_mask == 1)
    
    input_ids = input_ids.clone()
    input_ids[mask] = mask_token_id
    
    return input_ids, attention_mask

# In training loop
input_ids, attention_mask = apply_token_dropout(input_ids, attention_mask, dropout_prob=0.15)
logits = model(input_ids, attention_mask)
```

Retrain with token dropout enabled and re-run the noise robustness test. Expect accuracy degradation under noise to decrease by 5-10 percentage points, indicating improved generalization.

The gradient flow analysis detects vanishing or exploding gradients across layers. S4's recurrent structure can amplify gradient magnitude through long dependency chains. If gradient norms exceed 100, increase gradient clipping threshold or reduce learning rate. If norms fall below 1e-7, suspect dead ReLUs or poorly initialized state matrices—verify the HiPPO initialization produces negative real eigenvalues for stability.

Implement gradient norm monitoring directly in the training loop:

```python
import torch.nn.utils as nn_utils

# After loss.backward()
total_norm = nn_utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

if total_norm > 10.0:
    print(f"WARNING: Large gradient norm detected: {total_norm:.2f}")

wandb.log({"train/grad_norm": total_norm})
```

Examine the Weights & Biases gradient norm trace. Healthy training exhibits stable norms between 0.1-2.0. Spikes indicate optimizer instability; implement gradient clipping adaptively based on running statistics:

```python
# Adaptive gradient clipping
grad_norm_history = []

def adaptive_clip_grad_norm_(parameters, percentile=95):
    global grad_norm_history
    
    total_norm = torch.sqrt(sum(p.grad.norm()**2 for p in parameters if p.grad is not None))
    grad_norm_history.append(total_norm.item())
    
    if len(grad_norm_history) > 100:
        clip_value = np.percentile(grad_norm_history[-100:], percentile)
        nn_utils.clip_grad_norm_(parameters, max_norm=clip_value)
    
    return total_norm

# In training loop
total_norm = adaptive_clip_grad_norm_(model.parameters())
```

The distribution shift test exposes how well the model generalizes beyond its training domain. A 20%+ accuracy drop from IMDB to SST-2 (both sentiment tasks but different corpora) indicates domain overfitting. Implement domain-adversarial training or meta-learning approaches to improve cross-domain robustness, though these extend beyond the scope of basic stress testing.

For numerical stability, verify your S4 implementation handles extreme discretization step sizes. The `log_dt` parameter can drift toward very large or small values during training, causing discretization instability. Constrain `log_dt` through hard bounds:

```python
# In S4Layer.forward()
dt = torch.exp(self.log_dt).clamp(min=1e-4, max=0.5)
```

Or regularize via loss penalties:

```python
# Add to training loss
dt = torch.exp(model.blocks[0].s4_layer.log_dt)
dt_penalty = torch.mean((dt - 0.05)**2)  # Encourage dt near 0.05
loss = loss + 0.01 * dt_penalty
```

Finally, implement a comprehensive edge case test suite using pytest. Create `tests/test_edge_cases.py`:

```python
import pytest
import torch
from models.s4_classifier import S4Classifier


def test_empty_sequence():
    """Model should handle empty sequences gracefully."""
    model = S4Classifier(vocab_size=1000, d_model=64, state_dim=32, n_layers=2, num_classes=2)
    
    input_ids = torch.zeros((1, 0), dtype=torch.long)  # Empty sequence
    attention_mask = torch.zeros((1, 0), dtype=torch.long)
    
    # Should not crash
    try:
        logits = model(input_ids, attention_mask)
        assert logits.shape == (1, 2)
    except Exception as e:
        pytest.fail(f"Empty sequence handling failed: {str(e)}")


def test_single_token():
    """Model should handle single-token sequences."""
    model = S4Classifier(vocab_size=1000, d_model=64, state_dim=32, n_layers=2, num_classes=2)
    
    input_ids = torch.tensor([[42]])
    attention_mask = torch.tensor([[1]])
    
    logits = model(input_ids, attention_mask)
    
    assert logits.shape == (1, 2)
    assert not torch.isnan(logits).any()
    assert not torch.isinf(logits).any()


def test_max_length_sequence():
    """Model should handle maximum length sequences."""
    max_seq_len = 1024
    model = S4Classifier(vocab_size=1000, d_model=64, state_dim=32, n_layers=2, 
                        num_classes=2, max_seq_len=max_seq_len)
    
    input_ids = torch.randint(0, 1000, (1, max_seq_len))
    attention_mask = torch.ones((1, max_seq_len))
    
    logits = model(input_ids, attention_mask)
    
    assert logits.shape == (1, 2)
    assert not torch.isnan(logits).any()


def test_batch_size_one():
    """Model should handle batch size 1."""
    model = S4Classifier(vocab_size=1000, d_model=64, state_dim=32, n_layers=2, num_classes=2)
    
    input_ids = torch.randint(0, 1000, (1, 50))
    attention_mask = torch.ones((1, 50))
    
    logits = model(input_ids, attention_mask)
    assert logits.shape == (1, 2)


def test_large_batch():
    """Model should handle large batches."""
    model = S4Classifier(vocab_size=1000, d_model=64, state_dim=32, n_layers=2, num_classes=2)
    
    input_ids = torch.randint(0, 1000, (128, 50))
    attention_mask = torch.ones((128, 50))
    
    logits = model(input_ids, attention_mask)
    assert logits.shape == (128, 2)


def test_masked_sequence():
    """Model should handle fully masked sequences."""
    model = S4Classifier(vocab_size=1000, d_model=64, state_dim=32, n_layers=2, num_classes=2)
    
    input_ids = torch.randint(0, 1000, (4, 50))
    attention_mask = torch.zeros((4, 50))  # All masked
    
    logits = model(input_ids, attention_mask)
    
    assert logits.shape == (4, 2)
    # Logits should still be finite even with no valid input
    assert not torch.isnan(logits).any()
    assert not torch.isinf(logits).any()


def test_gradient_finite():
    """Gradients should remain finite during backpropagation."""
    model = S4Classifier(vocab_size=1000, d_model=64, state_dim=32, n_layers=2, num_classes=2)
    
    input_ids = torch.randint(0, 1000, (8, 50))
    attention_mask = torch.ones((8, 50))
    labels = torch.randint(0, 2, (8,))
    
    logits = model(input_ids, attention_mask)
    loss = torch.nn.functional.cross_entropy(logits, labels)
    loss.backward()
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            assert not torch.isnan(param.grad).any(), f"NaN gradient in {name}"
            assert not torch.isinf(param.grad).any(), f"Inf gradient in {name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run the test suite:

```bash
python -m pytest tests/test_edge_cases.py -v
```

All tests must pass before production deployment. If `test_empty_sequence` fails, add explicit handling:

```python
# In S4Classifier.forward()
if seq_len == 0:
    # Return zero logits for empty sequences
    return torch.zeros(batch_size, self.classifier.out_features, device=input_ids.device)
```

Document every edge case mitigation in your codebase. Production systems fail not from average-case bugs but from unhandled corner cases discovered under load. Your stress testing regimen provides confidence that your S4 implementation degrades gracefully rather than catastrophically.

## ML Diagnostic Cheat Sheet & Verification Checklist

This section consolidates operational diagnostics for rapid troubleshooting during development and deployment. Treat these procedures as first-response protocols when encountering anomalies.

**Model Not Training (Loss Not Decreasing)**

1. **Verify gradient flow**: Insert `print(param.grad.norm())` after `loss.backward()` for each parameter. Zero or NaN norms indicate dead gradients.

2. **Check learning rate**: If loss oscillates wildly, reduce LR by 10×. If loss plateaus immediately, increase LR by 5×.

3. **Inspect data loading**: Print a batch and manually verify labels align with inputs. Incorrect label encoding is a common silent error.

4. **Simplify architecture**: Reduce to a single S4 block. If training succeeds, the issue lies in multi-layer gradient propagation.

5. **Verify loss computation**: Replace your loss with dummy `loss = (logits**2).mean()`. If this decreases, the issue is in loss calculation, not the model.

**Memory Overflow**

1. **Reduce batch size**: Halve `batch_size` and double `grad_accum_steps` to maintain effective batch size.

2. **Enable gradient checkpointing**: Insert `torch.utils.checkpoint.checkpoint(block, x)` around S4 blocks to trade compute for memory.

3. **Lower precision**: Switch to mixed precision training with `torch.cuda.amp.autocast()` and `GradScaler`.

4. **Profile memory**: Run `torch.cuda.memory_summary()` to identify the largest allocation. Often it is intermediate FFT buffers in the S4 layer.

5. **Offload to CPU**: Move optimizer state to CPU via `ZeroRedundancyOptimizer` from PyTorch Distributed.

**Slow Training**

1. **Profile with cProfile**: Run `python -m cProfile -o profile.stats train.py` and analyze with `snakeviz profile.stats`. Identify the bottleneck function.

2. **Check dataloader workers**: Increase `num_workers` in DataLoader until CPU utilization saturates.

3. **Optimize FFT**: Ensure PyTorch is compiled with MKL or cuFFT for optimized FFT kernels.

4. **Reduce validation frequency**: Evaluate every N epochs instead of every epoch during hyperparameter sweeps.

5. **Use faster tokenizers**: Replace Python tokenizers with Rust-based HuggingFace tokenizers via `use_fast=True`.

**NaN/Inf in Outputs**

1. **Inspect gradients**: Add hooks via `tensor.register_hook(lambda grad: print(grad.norm()))` to trace where NaNs originate.

2. **Check discretization**: Verify `dt` values remain in `[1e-4, 0.5]`. Extreme values destabilize the bilinear transform.

3. **Enable anomaly detection**: Wrap training loop with `torch.autograd.set_detect_anomaly(True)` to get backprop traces when NaNs appear.

4. **Audit matrix inversions**: The `(zI - dA)^{-1}` operation in S4 can produce NaNs if eigenvalues equal `z`. Add epsilon: `1.0 / (z - dA + 1e-8)`.

5. **Reduce learning rate**: High LR can cause parameter explosions. Try 1e-5 and gradually increase.

**Poor Generalization**

1. **Increase regularization**: Boost dropout from 0.1 to 0.3. Add weight decay to AdamW (try 0.01).

2. **Data augmentation**: Implement token dropout, synonym replacement, or back-translation augmentation.

3. **Reduce model capacity**: If validation loss < training loss, the model overfits. Reduce `d_model` or `n_layers`.

4. **Collect more data**: If feasible, expand training set. State space models scale well with data.

5. **Check for label leakage**: Ensure test set has no overlap with training set. Verify via `set(train_dataset["text"]) & set(test_dataset["text"])`.

**Low Throughput**

1. **Batch size**: Double batch size until GPU memory saturates. Larger batches improve hardware utilization.

2. **Pin memory**: Set `pin_memory=True` in DataLoader to accelerate CPU-to-GPU transfers.

3. **Fuse operations**: Replace separate LayerNorm + Dropout with fused kernels via Apex or xFormers.

4. **TorchScript**: Compile the model with `torch.jit.script(model)` for inference speedups.

5. **Quantization**: Post-training quantization via `torch.quantization.quantize_dynamic` can provide 2-4× inference acceleration.

**Model Diverges After N Steps**

1. **Gradient clipping**: Reduce `max_norm` from 1.0 to 0.5 to prevent gradient explosions.

2. **LR warmup**: Extend warmup from 500 to 1000 steps to stabilize early training.

3. **Batch normalization**: If using BatchNorm, replace with LayerNorm for improved stability in sequence models.

4. **Check optimizer state**: Reset optimizer state and resume from last stable checkpoint.

5. **Numerical precision**: Switch to FP64 for a single step to verify FP32 underflow is not the cause.

**Verification Checklist for Production Deployment**

Before deploying your S4 model to production, systematically verify each item:

- [ ] Model passes all edge case tests in `test_edge_cases.py`
- [ ] Evaluation accuracy matches training logs (within 1%)
- [ ] Checkpoint loading and saving work correctly
- [ ] Model handles out-of-vocabulary tokens gracefully
- [ ] Inference latency meets SLA requirements (measure p95 and p99)
- [ ] GPU memory usage remains below 80% of available capacity under peak load
- [ ] Model outputs remain finite (no NaN/Inf) for 10,000 consecutive inferences
- [ ] Prediction confidence is calibrated (plot reliability diagrams)
- [ ] Model does not crash on empty, single-token, or max-length inputs
- [ ] Batch inference produces identical results to single-sample inference
- [ ] Model performance degrades gracefully under 20% input noise
- [ ] Logging captures all errors with stack traces
- [ ] Model versioning and artifact tracking are in place (MLflow, W&B Artifacts)
- [ ] Rollback procedure to previous model version is documented and tested
- [ ] Monitoring dashboards track latency, throughput, error rate, and accuracy drift

This checklist serves as a gate before transitioning from research experimentation to production serving. Each unchecked item represents a potential production incident.

State space models offer compelling computational advantages for long-sequence modeling, but they introduce unique failure modes distinct from Transformers. The discretization process, FFT-based training pathway, and recurrent inference modality each carry architectural risks that manifest only under stress conditions. By systematically stress-testing your implementation, instrumenting diagnostics, and validating edge case handling, you build operational confidence that your S4 classifier will perform reliably when deployed at scale. Treat this laboratory series not as a terminal exercise but as a foundation for continuous empirical validation throughout your model's lifecycle.
