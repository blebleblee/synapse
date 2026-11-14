# Operational Verification Labs: Mixture of Experts

## Objective & Environment Setup

This lab guide treats the Mixture of Experts (MoE) architecture not as an abstract research curiosity but as a production inference and training system that demands rigorous engineering discipline. You will build a sparse MoE transformer layer from scratch in PyTorch, wire it into a training harness, instrument it for expert utilization diagnostics, tune its routing hyperparameters under controlled benchmark conditions, and then systematically break it to understand the failure modes that have sunk real deployments. By the end of these exercises, you will have a reproducible, instrumented MoE stack that you can extend, adapt, or audit against larger pretrained models served through HuggingFace.

The mechanical intuition you need before writing a single line of code is this: a standard dense feedforward layer applies the same learned transformation to every token in every batch. A sparse MoE layer instead maintains $N$ independent expert networks (typically feedforward sublayers), and for each token selects only $k$ of them via a learned router. The token is processed only by those $k$ experts, and their outputs are combined by the router's softmax weights. The computational cost per token scales with $k$ rather than $N$, so the model can grow in parameter count without growing proportionally in FLOPs. The challenge — and the entire substance of these labs — is that the router is itself a learned function, and without auxiliary constraints it will collapse to routing every token to the same one or two experts, wasting capacity and defeating the purpose entirely.

The router's output is a probability distribution over experts, typically produced by a linear projection of the token's hidden state followed by a softmax. At inference time the top-$k$ experts by probability are selected. During training, a load-balancing auxiliary loss is added to the main task loss. This auxiliary loss penalizes routing distributions that deviate from uniform across experts, computed as the dot product of the fraction of tokens dispatched to each expert and the mean router probability assigned to each expert. This term — first formalized in the Switch Transformer paper — is what prevents expert collapse, and tuning its coefficient is the central empirical challenge you will address in Exercise 2.

### Environment Setup

Create a dedicated virtual environment to isolate this lab's dependencies from your system Python. The commands below assume a POSIX shell and a machine with at least one CUDA-capable GPU, though the code paths include CPU fallbacks for every exercise.

```bash
python3.11 -m venv moe_lab_env
source moe_lab_env/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets accelerate numpy polars scikit-learn wandb tensorboard pytest
```

Verify the environment before proceeding. The following script serves as your environment canary — if it exits cleanly, every subsequent exercise will have its hardware and software prerequisites satisfied.

```python
# verify_env.py
import sys
import torch
import transformers
import datasets
import numpy as np
import polars as pl
import sklearn

def check_env():
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"
    print(f"Python:          {sys.version}")
    print(f"PyTorch:         {torch.__version__}")
    print(f"CUDA available:  {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device:     {torch.cuda.get_device_name(0)}")
        print(f"CUDA version:    {torch.version.cuda}")
    print(f"Transformers:    {transformers.__version__}")
    print(f"Datasets:        {datasets.__version__}")
    print(f"NumPy:           {np.__version__}")
    print(f"Polars:          {pl.__version__}")
    print(f"Scikit-Learn:    {sklearn.__version__}")
    print("Environment OK.")

if __name__ == "__main__":
    check_env()
```

```bash
python verify_env.py
```

Create the lab directory structure that the remaining exercises will reference:

```bash
mkdir -p moe_lab/{models,data,checkpoints,logs,tests}
cd moe_lab
```

---

## Exercise 1: Hands-On Implementation & Pipeline Execution

### 1.1 Building the Core MoE Layer

The expert network itself is an ordinary two-layer feedforward sublayer — the same structure you would find in a vanilla transformer. What distinguishes the MoE layer is the router that sits in front of the experts and the dispatch logic that routes each token to only $k$ of them. You will implement the router, the auxiliary load-balancing loss, and the full MoE feedforward sublayer in a single module, then validate its output shapes and routing behavior with a focused test suite before integrating it into a training loop.

```python
# models/moe_layer.py
"""
Sparse Mixture-of-Experts feedforward layer with Top-K routing and
auxiliary load-balancing loss.  Compatible with PyTorch >= 2.1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class MoEConfig:
    d_model: int = 512          # Hidden dimension of the transformer
    d_ff: int = 2048            # Inner dimension of each expert FFN
    num_experts: int = 8        # Total number of expert networks (N)
    top_k: int = 2              # Experts activated per token (k)
    aux_loss_coeff: float = 1e-2  # Weight of load-balancing loss
    dropout: float = 0.1
    activation: str = "gelu"    # "gelu" | "relu" | "silu"


class ExpertFFN(nn.Module):
    """Single expert: a two-layer feedforward network."""

    def __init__(self, cfg: MoEConfig) -> None:
        super().__init__()
        act_map = {"gelu": nn.GELU(), "relu": nn.ReLU(), "silu": nn.SiLU()}
        self.net = nn.Sequential(
            nn.Linear(cfg.d_model, cfg.d_ff, bias=True),
            act_map[cfg.activation],
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.d_ff, cfg.d_model, bias=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TopKRouter(nn.Module):
    """
    Learned router that projects each token to a distribution over experts
    and selects the top-k.  Returns the dispatch indices, the combining
    weights, and the auxiliary load-balancing loss.
    """

    def __init__(self, cfg: MoEConfig) -> None:
        super().__init__()
        self.num_experts = cfg.num_experts
        self.top_k = cfg.top_k
        self.aux_loss_coeff = cfg.aux_loss_coeff
        # Linear gate: maps [B, T, d_model] -> [B, T, num_experts]
        self.gate = nn.Linear(cfg.d_model, cfg.num_experts, bias=False)

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            x: [batch, seq_len, d_model]
        Returns:
            top_k_indices:  [batch, seq_len, top_k]  — expert indices chosen
            top_k_weights:  [batch, seq_len, top_k]  — combining weights (sum to 1)
            aux_loss:       scalar tensor              — load-balancing penalty
        """
        B, T, D = x.shape
        # Router logits: [B, T, N]
        logits = self.gate(x)
        # Full softmax for auxiliary loss computation (must use pre-topk probs)
        router_probs = F.softmax(logits, dim=-1)  # [B, T, N]

        # Select top-k experts
        top_k_logits, top_k_indices = torch.topk(logits, self.top_k, dim=-1)
        # Re-normalise among selected experts so weights sum to 1 per token
        top_k_weights = F.softmax(top_k_logits, dim=-1)  # [B, T, k]

        # --- Auxiliary load-balancing loss (Switch Transformer formulation) ---
        # f_i: fraction of tokens routed to expert i (computed via argmax dispatch)
        # P_i: mean router probability assigned to expert i across all tokens
        # loss = aux_coeff * N * sum_i(f_i * P_i)
        # We use the top-1 dispatch for f_i to avoid gradient issues.
        num_tokens = float(B * T)
        # one-hot of the top-1 expert selection per token for f_i
        top1_indices = top_k_indices[:, :, 0]  # [B, T]
        # Compute f_i as the fraction of tokens dispatched to each expert
        expert_counts = torch.zeros(
            self.num_experts, device=x.device, dtype=x.dtype
        )
        for e in range(self.num_experts):
            expert_counts[e] = (top1_indices == e).sum().float()
        f_i = expert_counts / num_tokens  # [N]
        # Compute P_i: mean router probability per expert
        P_i = router_probs.view(-1, self.num_experts).mean(dim=0)  # [N]
        aux_loss = self.aux_loss_coeff * self.num_experts * (f_i * P_i).sum()

        return top_k_indices, top_k_weights, aux_loss


class MoELayer(nn.Module):
    """
    Sparse MoE feedforward layer.  Dispatches each token to its top-k
    experts, runs the expert computations, and combines the results with
    the router weights.
    """

    def __init__(self, cfg: MoEConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.experts = nn.ModuleList([ExpertFFN(cfg) for _ in range(cfg.num_experts)])
        self.router = TopKRouter(cfg)

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: [batch, seq_len, d_model]
        Returns:
            output:    [batch, seq_len, d_model]
            aux_loss:  scalar tensor
        """
        B, T, D = x.shape
        top_k_indices, top_k_weights, aux_loss = self.router(x)

        # Flatten tokens for dispatch: [B*T, d_model]
        x_flat = x.view(B * T, D)
        output = torch.zeros_like(x_flat)

        # Flatten routing info: [B*T, k]
        indices_flat = top_k_indices.view(B * T, self.cfg.top_k)
        weights_flat = top_k_weights.view(B * T, self.cfg.top_k)

        # Dispatch to experts.  For each expert, gather the tokens assigned
        # to it, run the expert, and scatter-add the weighted result back.
        for expert_idx, expert in enumerate(self.experts):
            # Find token positions routed to this expert (across all k slots)
            token_mask = (indices_flat == expert_idx)  # [B*T, k]
            # At least one k-slot must match for this token to use this expert
            active_tokens = token_mask.any(dim=-1)     # [B*T]
            if not active_tokens.any():
                continue
            # Gather active tokens
            active_x = x_flat[active_tokens]           # [n_active, D]
            expert_out = expert(active_x)              # [n_active, D]
            # For each active token, sum over the k slots that chose this expert
            # (top-k=2 means a token can in theory have both slots choose the same
            # expert if N < k; we guard against that here)
            slot_weights = weights_flat[active_tokens]  # [n_active, k]
            expert_weight = (token_mask[active_tokens].float() * slot_weights).sum(
                dim=-1, keepdim=True
            )  # [n_active, 1]
            output[active_tokens] += expert_weight * expert_out

        return output.view(B, T, D), aux_loss

    def get_routing_stats(self, x: torch.Tensor) -> dict:
        """
        Compute per-expert token distribution statistics for diagnostics.
        Does not contribute to the computation graph.
        """
        with torch.no_grad():
            B, T, D = x.shape
            top_k_indices, top_k_weights, _ = self.router(x)
            top1 = top_k_indices[:, :, 0].view(-1)
            counts = torch.bincount(top1, minlength=self.cfg.num_experts).float()
            fractions = counts / counts.sum()
            return {
                "expert_fractions": fractions.cpu().tolist(),
                "max_load": fractions.max().item(),
                "min_load": fractions.min().item(),
                "load_imbalance": (fractions.max() - fractions.min()).item(),
                "effective_experts": (1.0 / (fractions ** 2).sum()).item(),
            }
```

The `get_routing_stats` method computes the effective number of experts using the inverse Simpson diversity index, $\text{eff} = 1 / \sum_i f_i^2$. When all $N$ experts receive equal load this equals $N$; when load collapses to one expert it equals 1. This scalar is your primary routing health diagnostic throughout all subsequent exercises.

### 1.2 Integrating MoE into a Minimal Transformer

A single MoE layer is not useful in isolation. You need a training harness around it to observe how the router learns. The model below is a small transformer language model that substitutes every other feedforward sublayer with a MoE layer, following the interleaved pattern used in Mixtral. This interleaving retains dense layers for syntactic pattern recognition while giving high-capacity MoE layers responsibility for the associative, knowledge-intensive processing that benefits from specialization.

```python
# models/moe_transformer.py
"""
Small MoE transformer for language modelling experiments.
Interleaves dense FFN and MoE FFN layers.
"""
from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from .moe_layer import MoEConfig, MoELayer


class TransformerConfig:
    def __init__(
        self,
        vocab_size: int = 10000,
        d_model: int = 256,
        num_heads: int = 4,
        num_layers: int = 4,
        max_seq_len: int = 256,
        dropout: float = 0.1,
        moe_cfg: Optional[MoEConfig] = None,
    ) -> None:
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.max_seq_len = max_seq_len
        self.dropout = dropout
        self.moe_cfg = moe_cfg or MoEConfig(
            d_model=d_model,
            d_ff=d_model * 4,
            num_experts=8,
            top_k=2,
            aux_loss_coeff=1e-2,
            dropout=dropout,
        )


class DenseFFN(nn.Module):
    def __init__(self, cfg: TransformerConfig) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(cfg.d_model, cfg.d_model * 4),
            nn.GELU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.d_model * 4, cfg.d_model),
            nn.Dropout(cfg.dropout),
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # Return zero aux loss for uniform interface with MoELayer
        return self.net(x), torch.tensor(0.0, device=x.device)


class TransformerBlock(nn.Module):
    def __init__(self, cfg: TransformerConfig, use_moe: bool) -> None:
        super().__init__()
        self.attn = nn.MultiheadAttention(
            cfg.d_model, cfg.num_heads, dropout=cfg.dropout, batch_first=True
        )
        self.ffn = MoELayer(cfg.moe_cfg) if use_moe else DenseFFN(cfg)
        self.norm1 = nn.LayerNorm(cfg.d_model)
        self.norm2 = nn.LayerNorm(cfg.d_model)
        self.dropout = nn.Dropout(cfg.dropout)

    def forward(
        self, x: torch.Tensor, attn_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # Causal self-attention with pre-norm
        normed = self.norm1(x)
        attn_out, _ = self.attn(normed, normed, normed, attn_mask=attn_mask)
        x = x + self.dropout(attn_out)
        # FFN (dense or MoE)
        normed = self.norm2(x)
        ffn_out, aux_loss = self.ffn(normed)
        x = x + self.dropout(ffn_out)
        return x, aux_loss


class MoETransformer(nn.Module):
    def __init__(self, cfg: TransformerConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.embed = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.pos_embed = nn.Embedding(cfg.max_seq_len, cfg.d_model)
        self.drop = nn.Dropout(cfg.dropout)
        # Interleave: even-indexed layers are dense, odd-indexed are MoE
        self.blocks = nn.ModuleList(
            [
                TransformerBlock(cfg, use_moe=(i % 2 == 1))
                for i in range(cfg.num_layers)
            ]
        )
        self.norm = nn.LayerNorm(cfg.d_model)
        self.head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        # Weight tying
        self.head.weight = self.embed.weight
        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, mean=0.0, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def _make_causal_mask(self, T: int, device: torch.device) -> torch.Tensor:
        mask = torch.triu(torch.ones(T, T, device=device), diagonal=1).bool()
        return mask

    def forward(
        self, input_ids: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            input_ids: [batch, seq_len]
        Returns:
            logits:    [batch, seq_len, vocab_size]
            total_aux_loss: scalar
        """
        B, T = input_ids.shape
        positions = torch.arange(T, device=input_ids.device).unsqueeze(0)
        x = self.drop(self.embed(input_ids) + self.pos_embed(positions))
        causal_mask = self._make_causal_mask(T, input_ids.device)
        total_aux = torch.tensor(0.0, device=input_ids.device)
        for block in self.blocks:
            x, aux = block(x, attn_mask=causal_mask)
            total_aux = total_aux + aux
        x = self.norm(x)
        logits = self.head(x)
        return logits, total_aux
```

### 1.3 Synthetic Data Generation and Training Pipeline

For controlled lab conditions, a synthetic character-level language modeling task over repeating structured sequences gives you a ground truth about what specialization the router *should* learn. Experts should specialize by token type. You can verify this directly.

```python
# data/synthetic_dataset.py
"""
Synthetic token-sequence dataset with structured pattern classes.
Tokens 0–99 are 'type A' (arithmetic context), 100–199 are 'type B' (structural),
200–299 are 'type C' (repetition). The model must predict the next token.
"""
from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import Dataset


class SyntheticMoEDataset(Dataset):
    """
    Generates sequences where token types follow learnable transition rules.
    This encourages the MoE router to specialize by token type.
    """

    def __init__(
        self,
        num_sequences: int = 10000,
        seq_len: int = 128,
        vocab_size: int = 300,
        seed: int = 42,
    ) -> None:
        self.seq_len = seq_len
        self.vocab_size = vocab_size
        rng = np.random.default_rng(seed)

        # Transition matrix: 3 token classes with structured within-class transitions
        # and rare cross-class transitions (5% probability)
        sequences = []
        for _ in range(num_sequences):
            seq = np.zeros(seq_len + 1, dtype=np.int64)
            # Start in a random type
            current_class = rng.integers(0, 3)
            for t in range(seq_len + 1):
                if rng.random() < 0.05:          # 5% chance to switch class
                    current_class = rng.integers(0, 3)
                offset = current_class * 100
                seq[t] = offset + rng.integers(0, 100)
            sequences.append(seq)

        self.data = torch.tensor(np.array(sequences), dtype=torch.long)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        seq = self.data[idx]
        return seq[:-1], seq[1:]   # input, target


# Re-export Tuple for annotation
from typing import Tuple
```

```python
# train.py
"""
Training harness for the MoE transformer.  Logs task loss, aux loss,
and routing statistics to TensorBoard and stdout.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torch.utils.tensorboard import SummaryWriter

from data.synthetic_dataset import SyntheticMoEDataset
from models.moe_layer import MoEConfig
from models.moe_transformer import MoETransformer, TransformerConfig


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MoE Transformer Training")
    p.add_argument("--d_model", type=int, default=256)
    p.add_argument("--num_layers", type=int, default=4)
    p.add_argument("--num_experts", type=int, default=8)
    p.add_argument("--top_k", type=int, default=2)
    p.add_argument("--aux_loss_coeff", type=float, default=1e-2)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--seq_len", type=int, default=128)
    p.add_argument("--log_dir", type=str, default="logs/run_baseline")
    p.add_argument("--checkpoint_dir", type=str, default="checkpoints/baseline")
    p.add_argument("--device", type=str, default="auto")
    return p.parse_args()


def build_model(args: argparse.Namespace) -> MoETransformer:
    moe_cfg = MoEConfig(
        d_model=args.d_model,
        d_ff=args.d_model * 4,
        num_experts=args.num_experts,
        top_k=args.top_k,
        aux_loss_coeff=args.aux_loss_coeff,
    )
    cfg = TransformerConfig(
        vocab_size=300,
        d_model=args.d_model,
        num_heads=max(1, args.d_model // 64),
        num_layers=args.num_layers,
        max_seq_len=args.seq_len,
        moe_cfg=moe_cfg,
    )
    return MoETransformer(cfg)


def train_epoch(
    model: MoETransformer,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.CrossEntropyLoss,
    device: torch.device,
    writer: SummaryWriter,
    global_step: list,
) -> dict:
    model.train()
    total_task_loss = 0.0
    total_aux_loss = 0.0
    total_tokens = 0

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits, aux_loss = model(x)
        # logits: [B, T, V]  y: [B, T]
        task_loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))
        loss = task_loss + aux_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        step = global_step[0]
        writer.add_scalar("loss/task", task_loss.item(), step)
        writer.add_scalar("loss/aux", aux_loss.item(), step)
        writer.add_scalar("loss/total", loss.item(), step)
        global_step[0] += 1

        total_task_loss += task_loss.item() * y.numel()
        total_aux_loss += aux_loss.item()
        total_tokens += y.numel()

    return {
        "task_loss": total_task_loss / total_tokens,
        "aux_loss": total_aux_loss / len(loader),
    }


@torch.no_grad()
def evaluate(
    model: MoETransformer,
    loader: DataLoader,
    criterion: nn.CrossEntropyLoss,
    device: torch.device,
) -> dict:
    model.eval()
    total_task_loss = 0.0
    total_tokens = 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits, _ = model(x)
        loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))
        total_task_loss += loss.item() * y.numel()
        total_tokens += y.numel()
    return {
        "val_loss": total_task_loss / total_tokens,
        "val_ppl": torch.exp(torch.tensor(total_task_loss / total_tokens)).item(),
    }


@torch.no_grad()
def log_routing_stats(
    model: MoETransformer,
    loader: DataLoader,
    device: torch.device,
    writer: SummaryWriter,
    epoch: int,
) -> None:
    """Sample one batch and log per-expert load distribution for all MoE layers."""
    model.eval()
    x, _ = next(iter(loader))
    x = x.to(device)

    for block_idx, block in enumerate(model.blocks):
        if isinstance(block.ffn, type(block.ffn)) and hasattr(block.ffn, "router"):
            # This is a MoE block; we need the hidden state at this layer.
            # Re-run a partial forward to extract the intermediate activations.
            pass

    # Targeted routing probe: run full forward and extract router states
    # by temporarily hooking the MoE layers.
    for block_idx, block in enumerate(model.blocks):
        if not hasattr(block.ffn, "router"):
            continue
        # Register a forward hook on the router to capture its input
        captured = {}

        def hook_fn(module, inp, out, bname=f"block_{block_idx}"):
            captured["indices"] = out[0].cpu()
            captured["weights"] = out[1].cpu()

        h = block.ffn.router.register_forward_hook(hook_fn)
        # Run forward on this batch
        positions = torch.arange(x.size(1), device=device).unsqueeze(0)
        emb = model.embed(x) + model.pos_embed(positions)
        cur = model.drop(emb)
        mask = model._make_causal_mask(x.size(1), device)
        for i, blk in enumerate(model.blocks):
            cur, _ = blk(cur, attn_mask=mask)
            if i == block_idx:
                break
        h.remove()

        if "indices" in captured:
            stats = block.ffn.get_routing_stats(
                # Approximate: use embedding as proxy for hidden state shape check
                x.float().unsqueeze(-1).expand(-1, -1, model.cfg.d_model)
            )
            writer.add_scalar(f"routing/block_{block_idx}/eff_experts", stats["effective_experts"], epoch)
            writer.add_scalar(f"routing/block_{block_idx}/max_load", stats["max_load"], epoch)
            writer.add_scalar(f"routing/block_{block_idx}/imbalance", stats["load_imbalance"], epoch)
            print(
                f"  [Block {block_idx}] eff_experts={stats['effective_experts']:.2f}  "
                f"max_load={stats['max_load']:.3f}  imbalance={stats['load_imbalance']:.3f}"
            )


def main() -> None:
    args = parse_args()
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    Path(args.checkpoint_dir).mkdir(parents=True, exist_ok=True)

    dataset = SyntheticMoEDataset(num_sequences=20000, seq_len=args.seq_len)
    n_val = int(0.1 * len(dataset))
    train_ds, val_ds = random_split(dataset, [len(dataset) - n_val, n_val])
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2, pin_memory=True)

    model = build_model(args).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {n_params:,}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss()
    writer = SummaryWriter(log_dir=args.log_dir)
    global_step = [0]

    best_val_loss = float("inf")
    for epoch in range(1, args.epochs + 1):
        t0 = time.perf_counter()
        train_metrics = train_epoch(model, train_loader, optimizer, criterion, device, writer, global_step)
        val_metrics = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.perf_counter() - t0

        print(
            f"Epoch {epoch:02d} | "
            f"task_loss={train_metrics['task_loss']:.4f}  "
            f"aux_loss={train_metrics['aux_loss']:.4f}  "
            f"val_loss={val_metrics['val_loss']:.4f}  "
            f"val_ppl={val_metrics['val_ppl']:.2f}  "
            f"time={elapsed:.1f}s"
        )
        log_routing_stats(model, val_loader, device, writer, epoch)

        if val_metrics["val_loss"] < best_val_loss:
            best_val_loss = val_metrics["val_loss"]
            ckpt_path = Path(args.checkpoint_dir) / "best_model.pt"
            torch.save(
                {
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "val_loss": best_val_loss,
                    "args": vars(args),
                },
                ckpt_path,
            )
            print(f"  Saved checkpoint to {ckpt_path}")

    writer.close()
    print(f"Training complete. Best val_loss={best_val_loss:.4f}")


if __name__ == "__main__":
    main()
```

Run the baseline training:

```bash
python train.py \
  --d_model 256 \
  --num_layers 4 \
  --num_experts 8 \
  --top_k 2 \
  --aux_loss_coeff 0.01 \
  --lr 3e-4 \
  --batch_size 64 \
  --epochs 10 \
  --log_dir logs/run_baseline \
  --checkpoint_dir checkpoints/baseline
```

Inspect the TensorBoard logs:

```bash
tensorboard --logdir logs/ --port 6006
```

### 1.4 Unit Tests for Correctness

Before trusting any downstream experiment result, verify that the MoE layer's mathematical contracts hold. The tests below check output shape, aux loss sign and magnitude, weight normalization, gradient flow, and that increasing `num_experts` or decreasing `top_k` does not break the dispatch logic.

```python
# tests/test_moe_layer.py
"""
pytest suite for MoELayer correctness verification.
Run: python -m pytest tests/test_moe_layer.py -v
"""
import pytest
import torch
import torch.nn as nn

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.moe_layer import MoEConfig, MoELayer, TopKRouter


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def make_moe(num_experts=8, top_k=2, aux_coeff=1e-2) -> MoELayer:
    cfg = MoEConfig(
        d_model=64,
        d_ff=256,
        num_experts=num_experts,
        top_k=top_k,
        aux_loss_coeff=aux_coeff,
    )
    return MoELayer(cfg).to(DEVICE)


class TestOutputShape:
    def test_basic_shape(self):
        moe = make_moe()
        x = torch.randn(4, 32, 64, device=DEVICE)
        out, aux = moe(x)
        assert out.shape == (4, 32, 64), f"Expected (4, 32, 64), got {out.shape}"

    def test_single_token(self):
        moe = make_moe()
        x = torch.randn(1, 1, 64, device=DEVICE)
        out, aux = moe(x)
        assert out.shape == (1, 1, 64)

    def test_large_batch(self):
        moe = make_moe()
        x = torch.randn(32, 128, 64, device=DEVICE)
        out, aux = moe(x)
        assert out.shape == (32, 128, 64)


class TestAuxLoss:
    def test_aux_loss_is_positive(self):
        moe = make_moe(aux_coeff=1e-2)
        x = torch.randn(4, 16, 64, device=DEVICE)
        _, aux = moe(x)
        assert aux.item() >= 0.0, "Auxiliary loss must be non-negative"

    def test_aux_loss_scales_with_coefficient(self):
        x = torch.randn(4, 16, 64, device=DEVICE)
        moe_lo = make_moe(aux_coeff=1e-4)
        moe_hi = make_moe(aux_coeff=1.0)
        # Share weights to isolate coefficient effect
        moe_lo.load_state_dict(moe_hi.state_dict())
        moe_lo.cfg.aux_loss_coeff = 1e-4
        moe_lo.router.aux_loss_coeff = 1e-4
        moe_hi.cfg.aux_loss_coeff = 1.0
        moe_hi.router.aux_loss_coeff = 1.0
        _, aux_lo = moe_lo(x)
        _, aux_hi = moe_hi(x)
        assert aux_hi.item() > aux_lo.item(), "Higher coefficient must yield higher aux loss"

    def test_aux_loss_zero_coeff(self):
        moe = make_moe(aux_coeff=0.0)
        x = torch.randn(4, 16, 64, device=DEVICE)
        _, aux = moe(x)
        assert aux.item() == pytest.approx(0.0, abs=1e-8)


class TestRouterWeights:
    def test_weights_sum_to_one(self):
        cfg = MoEConfig(d_model=64, d_ff=256, num_experts=8, top_k=2)
        router = TopKRouter(cfg).to(DEVICE)
        x = torch.randn(4, 16, 64, device=DEVICE)
        _, weights, _ = router(x)
        # weights: [B, T, k]
        sums = weights.sum(dim=-1)  # [B, T]
        assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5), \
            "Top-k weights must sum to 1 per token"

    def test_indices_in_range(self):
        for n_experts in [4, 8, 16]:
            for top_k in [1, 2]:
                cfg = MoEConfig(d_model=64, d_ff=256, num_experts=n_experts, top_k=top_k)
                router = TopKRouter(cfg).to(DEVICE)
                x = torch.randn(2, 8, 64, device=DEVICE)
                indices, _, _ = router(x)
                assert indices.min() >= 0
                assert indices.max() < n_experts


class TestGradientFlow:
    def test_gradients_reach_gate(self):
        moe = make_moe()
        x = torch.randn(4, 16, 64, device=DEVICE, requires_grad=True)
        out, aux = moe(x)
        (out.sum() + aux).backward()
        assert x.grad is not None
        assert not torch.isnan(x.grad).any(), "NaN gradient detected in input"
        gate_grad = moe.router.gate.weight.grad
        assert gate_grad is not None
        assert not torch.isnan(gate_grad).any(), "NaN gradient in router gate"

    def test_all_expert_parameters_receive_grad(self):
        moe = make_moe(num_experts=4, top_k=1)
        # With top_k=1 and small batch, some experts may not be activated.
        # Use a large batch to ensure all experts activate.
        x = torch.randn(64, 32, 64, device=DEVICE)
        out, aux = moe(x)
        (out.sum() + aux).backward()
        for i, expert in enumerate(moe.experts):
            for name, p in expert.named_parameters():
                # Allow None for experts not activated in this batch
                if p.grad is not None:
                    assert not torch.isnan(p.grad).any(), \
                        f"NaN gradient in expert {i}, param {name}"


class TestRoutingStats:
    def test_stats_keys_present(self):
        moe = make_moe()
        x = torch.randn(8, 32, 64, device=DEVICE)
        stats = moe.get_routing_stats(x)
        for key in ["expert_fractions", "max_load", "min_load", "load_imbalance", "effective_experts"]:
            assert key in stats

    def test_fractions_sum_to_one(self):
        moe = make_moe()
        x = torch.randn(8, 32, 64, device=DEVICE)
        stats = moe.get_routing_stats(x)
        total = sum(stats["expert_fractions"])
        assert abs(total - 1.0) < 1e-5, f"Expert fractions sum to {total}, expected 1.0"

    def test_effective_experts_bounds(self):
        moe = make_moe(num_experts=8)
        x = torch.randn(8, 32, 64, device=DEVICE)
        stats = moe.get_routing_stats(x)
        assert 1.0 <= stats["effective_experts"] <= 8.0
```

```bash
python -m pytest tests/test_moe_layer.py -v
```

All tests should pass on a freshly initialized model. The gradient flow tests are particularly important: in MoE layers, experts that receive no tokens in a given batch have zero gradient, and the router must still receive a gradient through the auxiliary loss to push it toward uniform routing. If the router gate's gradient is zero, expert collapse is guaranteed.

---

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

### 2.1 The Routing Hyperparameter Landscape

The two most consequential hyperparameters in a MoE system are the auxiliary loss coefficient (`aux_loss_coeff`) and the number of active experts per token (`top_k`). Their interaction is nonlinear and counterintuitive. A very large `aux_loss_coeff` forces uniform routing but at the cost of task performance, because the router is penalized so heavily for any divergence from uniformity that it can no longer learn meaningful specialization. A very small coefficient allows specialization to emerge but risks collapse. The optimal value lies in a window that depends on the number of experts, the dataset's token type diversity, and the model's capacity relative to the task. Finding that window empirically, with instrumented benchmarks, is the purpose of this exercise.

The `top_k` parameter has a similarly nuanced effect. With `top_k=1` (Switch Transformer style), each token has exactly one expert and the routing is maximally sparse but also maximally unstable during early training, because a single bad routing decision for a token is not corrected by any other expert's output. With `top_k=2`, the combining weights provide a soft signal that stabilizes gradients. With `top_k=4` or higher, the sparsity benefit diminishes while the routing complexity increases. The standard finding from the GShard and Mixtral papers is that `top_k=2` offers the best trade-off, but you should verify this empirically on your task.

### 2.2 Automated Hyperparameter Sweep Harness

```python
# sweep.py
"""
Grid sweep over aux_loss_coeff and top_k.  Runs multiple training configurations
and writes results to a Polars DataFrame for analysis.
"""
from __future__ import annotations

import argparse
import itertools
import subprocess
import sys
from pathlib import Path

import polars as pl
import json
import re


SWEEP_CONFIGS = {
    "aux_loss_coeff": [0.0, 1e-4, 1e-3, 1e-2, 1e-1, 0.5],
    "top_k":          [1, 2, 4],
}

BASE_ARGS = {
    "d_model":    256,
    "num_layers": 4,
    "num_experts": 8,
    "lr":         3e-4,
    "batch_size": 64,
    "epochs":     8,
    "seq_len":    128,
}


def run_config(config: dict, run_id: str) -> dict:
    args = {**BASE_ARGS, **config}
    log_dir = f"logs/sweep/{run_id}"
    ckpt_dir = f"checkpoints/sweep/{run_id}"
    cmd = [sys.executable, "train.py"]
    for k, v in args.items():
        cmd += [f"--{k}", str(v)]
    cmd += ["--log_dir", log_dir, "--checkpoint_dir", ckpt_dir]

    print(f"\n{'='*60}")
    print(f"Running: {run_id}")
    print(f"Config:  {config}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr

    # Parse final val_loss from last "Training complete" line
    val_loss = None
    for line in output.split("\n"):
        m = re.search(r"Best val_loss=([\d.]+)", line)
        if m:
            val_loss = float(m.group(1))
        # Also try to extract from epoch lines
        m2 = re.search(r"val_ppl=([\d.]+)", line)

    if val_loss is None:
        # Fallback: parse last epoch's val_loss
        for line in reversed(output.split("\n")):
            m = re.search(r"val_loss=([\d.]+)", line)
            if m:
                val_loss = float(m.group(1))
                break

    return {
        "run_id": run_id,
        "aux_loss_coeff": config["aux_loss_coeff"],
        "top_k": config["top_k"],
        "val_loss": val_loss,
        "returncode": result.returncode,
        "stdout_tail": output[-500:],
    }


def main() -> None:
    Path("logs/sweep").mkdir(parents=True, exist_ok=True)
    Path("checkpoints/sweep").mkdir(parents=True, exist_ok=True)

    keys = list(SWEEP_CONFIGS.keys())
    values = list(SWEEP_CONFIGS.values())
    combinations = list(itertools.product(*values))

    results = []
    for combo in combinations:
        config = dict(zip(keys, combo))
        run_id = "aux{}-topk{}".format(
            str(config["aux_loss_coeff"]).replace(".", "p"),
            config["top_k"],
        )
        result = run_config(config, run_id)
        results.append(result)
        # Save intermediate results
        df = pl.DataFrame(
            {k: [r[k] for r in results] for k in results[0].keys() if k != "stdout_tail"}
        )
        df.write_csv("logs/sweep_results.csv")
        print(f"\nIntermediate results saved to logs/sweep_results.csv")

    df = pl.DataFrame(
        {k: [r[k] for r in results] for k in results[0].keys() if k != "stdout_tail"}
    )
    df = df.sort("val_loss")
    print("\n" + "="*60)
    print("SWEEP RESULTS (sorted by val_loss):")
    print("="*60)
    print(df.to_pandas().to_string(index=False))
    df.write_csv("logs/sweep_results_final.csv")


if __name__ == "__main__":
    main()
```

```bash
python sweep.py
```

### 2.3 Result Analysis and Visualization

After the sweep completes, the following script reads the CSV, computes the best configuration per `top_k` value, and plots the validation loss surface as a function of `aux_loss_coeff` for each `top_k`.

```python
# analysis/analyze_sweep.py
"""
Analyze sweep results and produce a formatted report.
"""
from __future__ import annotations

import polars as pl
import numpy as np


def analyze(csv_path: str = "logs/sweep_results_final.csv") -> None:
    df = pl.read_csv(csv_path)
    df = df.filter(pl.col("val_loss").is_not_null())

    print("\n=== SWEEP RESULTS ANALYSIS ===\n")

    # Best overall
    best = df.sort("val_loss").head(1)
    print("Best configuration:")
    print(f"  aux_loss_coeff = {best['aux_loss_coeff'][0]}")
    print(f"  top_k          = {best['top_k'][0]}")
    print(f"  val_loss       = {best['val_loss'][0]:.4f}\n")

    # Best per top_k
    print("Best val_loss per top_k value:")
    for k in sorted(df["top_k"].unique().to_list()):
        sub = df.filter(pl.col("top_k") == k).sort("val_loss").head(1)
        print(
            f"  top_k={k}: best_val_loss={sub['val_loss'][0]:.4f}  "
            f"best_aux_coeff={sub['aux_loss_coeff'][0]}"
        )

    # Effect of aux_loss_coeff=0 (no load balancing)
    print("\nNo-balancing baseline (aux_loss_coeff=0):")
    no_bal = df.filter(pl.col("aux_loss_coeff") == 0.0)
    for row in no_bal.iter_rows(named=True):
        print(f"  top_k={row['top_k']}: val_loss={row['val_loss']:.4f}")

    # Marginal effect of aux coefficient
    print("\nMarginal effect of aux_loss_coeff (averaged over top_k):")
    for coeff in sorted(df["aux_loss_coeff"].unique().to_list()):
        mean_loss = df.filter(pl.col("aux_loss_coeff") == coeff)["val_loss"].mean()
        print(f"  aux_coeff={coeff:.0e}: mean_val_loss={mean_loss:.4f}")

    # Compute relative degradation from best
    best_loss = df["val_loss"].min()
    print(f"\nRelative degradation from best ({best_loss:.4f}):")
    for row in df.sort("val_loss").iter_rows(named=True):
        rel = (row["val_loss"] - best_loss) / best_loss * 100
        print(
            f"  aux={row['aux_loss_coeff']:.0e} top_k={row['top_k']}: "
            f"val_loss={row['val_loss']:.4f}  (+{rel:.1f}%)"
        )


if __name__ == "__main__":
    analyze()
```

```bash
python analysis/analyze_sweep.py
```

### 2.4 Memory and Throughput Benchmarking

Expert count directly impacts GPU memory, and the relationship is not proportional to `num_experts` alone — the dispatch buffers scale with batch size times sequence length times expert count. This benchmark measures tokens per second and peak GPU memory for different expert counts, giving you the data you need to make a principled decision about model scale.

```python
# benchmarks/throughput_bench.py
"""
Measure forward-pass throughput and GPU memory for varying expert counts.
"""
from __future__ import annotations

import time
from typing import List

import torch
import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.moe_layer import MoEConfig, MoELayer


def benchmark_moe(
    num_experts: int,
    top_k: int,
    batch_size: int = 32,
    seq_len: int = 128,
    d_model: int = 256,
    n_warmup: int = 10,
    n_iters: int = 50,
    device: torch.device = torch.device("cpu"),
) -> dict:
    cfg = MoEConfig(
        d_model=d_model,
        d_ff=d_model * 4,
        num_experts=num_experts,
        top_k=top_k,
        aux_loss_coeff=0.01,
    )
    moe = MoELayer(cfg).to(device)
    moe.eval()
    x = torch.randn(batch_size, seq_len, d_model, device=device)

    # Warmup
    with torch.no_grad():
        for _ in range(n_warmup):
            _ = moe(x)

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)

    latencies = []
    with torch.no_grad():
        for _ in range(n_iters):
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            t0 = time.perf_counter()
            out, aux = moe(x)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            latencies.append(time.perf_counter() - t0)

    total_tokens = batch_size * seq_len
    mean_lat = np.mean(latencies)
    p99_lat = np.percentile(latencies, 99)
    throughput = total_tokens / mean_lat

    peak_mem_mb = 0.0
    if device.type == "cuda":
        peak_mem_mb = torch.cuda.max_memory_allocated(device) / 1024**2

    return {
        "num_experts": num_experts,
        "top_k": top_k,
        "mean_latency_ms": mean_lat * 1000,
        "p99_latency_ms": p99_lat * 1000,
        "throughput_tok_per_s": throughput,
        "peak_gpu_mem_mb": peak_mem_mb,
    }


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(torch.cuda.memory_summary(device=device, abbreviated=True))

    configs = [
        (4,  1), (4,  2),
        (8,  1), (8,  2), (8,  4),
        (16, 1), (16, 2), (16, 4),
        (32, 2), (32, 4),
    ]

    print(f"\n{'num_experts':>12} {'top_k':>6} {'mean_lat_ms':>12} "
          f"{'p99_lat_ms':>11} {'tok/s':>10} {'peak_mem_mb':>12}")
    print("-" * 70)

    for n_exp, k in configs:
        try:
            r = benchmark_moe(num_experts=n_exp, top_k=k, device=device)
            print(
                f"{r['num_experts']:>12} {r['top_k']:>6} "
                f"{r['mean_latency_ms']:>12.2f} {r['p99_latency_ms']:>11.2f} "
                f"{r['throughput_tok_per_s']:>10.0f} {r['peak_gpu_mem_mb']:>12.1f}"
            )
        except RuntimeError as e:
            print(f"{n_exp:>12} {k:>6}  OOM: {e}")

    if device.type == "cuda":
        print("\nFinal GPU memory summary:")
        print(torch.cuda.memory_summary(device=device, abbreviated=True))


if __name__ == "__main__":
    main()
```

```bash
python benchmarks/throughput_bench.py
```

### 2.5 Profiling with cProfile

The Python-level dispatch loop in `MoELayer.forward` is a hotspot when `num_experts` is large. Use `cProfile` to identify where time is being spent, particularly to quantify the overhead of the expert dispatch loop versus the actual linear algebra.

```python
# benchmarks/profile_moe.py
"""
cProfile analysis of MoELayer forward pass.
"""
from __future__ import annotations

import cProfile
import pstats
import io
import torch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.moe_layer import MoEConfig, MoELayer


def profiled_forward():
    device = torch.device("cpu")  # cProfile on CPU for clean stack traces
    cfg = MoEConfig(d_model=512, d_ff=2048, num_experts=16, top_k=2)
    moe = MoELayer(cfg).to(device)
    moe.eval()
    x = torch.randn(16, 64, 512, device=device)

    with torch.no_grad():
        for _ in range(20):
            moe(x)


def main():
    pr = cProfile.Profile()
    pr.enable()
    profiled_forward()
    pr.disable()

    stream = io.StringIO()
    stats = pstats.Stats(pr, stream=stream)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(30)
    print(stream.getvalue())

    # Also dump to file for offline analysis
    pr.dump_stats("logs/moe_profile.prof")
    print("Profile saved to logs/moe_profile.prof")
    print("Visualize with: python -m snakeviz logs/moe_profile.prof")


if __name__ == "__main__":
    main()
```

```bash
python benchmarks/profile_moe.py
```

The profile will show you that the Python-level `for expert_idx, expert in enumerate(self.experts)` loop dominates for large `num_experts`. This is the fundamental scalability bottleneck of naive dispatch and motivates the batched dispatch implementations used in production MoE systems (einsum-based dispatch, grouped GEMM, or `torch.scatter_add` over a padded token buffer). The exercise in the next section exposes this bottleneck deliberately.

---

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

### 3.1 Expert Collapse: Inducing and Detecting It

Expert collapse is the pathological equilibrium of MoE training. The router learns to send all tokens to a single expert, the other experts receive no gradient, and the system effectively degrades to a dense model with one active expert. The root cause is a feedback loop: a slightly more capable expert receives more tokens, which trains it more, which makes it better, which attracts more tokens. Without the auxiliary loss, this positive feedback is unconstrained.

The following script deliberately removes the auxiliary loss and trains for enough steps to trigger collapse, then measures the collapse severity using the effective experts metric:

```python
# tests/test_expert_collapse.py
"""
Stress test: verify that aux_loss_coeff=0.0 leads to measurable expert
collapse, and that aux_loss_coeff=1e-2 prevents it.
"""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.synthetic_dataset import SyntheticMoEDataset
from models.moe_layer import MoEConfig
from models.moe_transformer import MoETransformer, TransformerConfig


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NUM_STEPS = 500
BATCH_SIZE = 32
SEQ_LEN = 64


def build_model(aux_coeff: float) -> MoETransformer:
    moe_cfg = MoEConfig(
        d_model=128,
        d_ff=512,
        num_experts=8,
        top_k=2,
        aux_loss_coeff=aux_coeff,
    )
    cfg = TransformerConfig(
        vocab_size=300,
        d_model=128,
        num_heads=2,
        num_layers=2,
        max_seq_len=SEQ_LEN,
        moe_cfg=moe_cfg,
    )
    return MoETransformer(cfg).to(DEVICE)


def measure_routing_health(
    model: MoETransformer, loader: DataLoader
) -> float:
    """Return mean effective_experts across all MoE blocks, averaged over
    the first 4 batches of the loader."""
    model.eval()
    all_eff = []
    with torch.no_grad():
        for i, (x, _) in enumerate(loader):
            if i >= 4:
                break
            x = x.to(DEVICE)
            for block in model.blocks:
                if hasattr(block.ffn, "router"):
                    # Use a random tensor of correct shape as proxy for the
                    # intermediate hidden state — sufficient to probe load distribution.
                    h = torch.randn(x.size(0), x.size(1), model.cfg.d_model, device=DEVICE)
                    stats = block.ffn.get_routing_stats(h)
                    all_eff.append(stats["effective_experts"])
    return sum(all_eff) / len(all_eff) if all_eff else 0.0


def run_collapse_experiment(aux_coeff: float) -> dict:
    model = build_model(aux_coeff)
    dataset = SyntheticMoEDataset(num_sequences=4000, seq_len=SEQ_LEN, seed=99)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    criterion = nn.CrossEntropyLoss()

    model.train()
    step = 0
    for x, y in loader:
        if step >= NUM_STEPS:
            break
        x, y = x.to(DEVICE), y.to(DEVICE)
        logits, aux = model(x)
        loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1)) + aux
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        step += 1

    eff_experts = measure_routing_health(model, loader)
    return {"aux_coeff": aux_coeff, "effective_experts": eff_experts, "steps": step}


def test_collapse_without_aux_loss():
    """With no auxiliary loss, effective experts should collapse significantly."""
    result = run_collapse_experiment(aux_coeff=0.0)
    print(f"\nNo aux loss: effective_experts={result['effective_experts']:.3f} / 8.0")
    # Empirically, collapse to <3.0 effective experts is common after 500 steps
    assert result["effective_experts"] < 5.0, (
        f"Expected expert collapse (eff < 5.0) without aux loss, "
        f"got {result['effective_experts']:.3f}"
    )


def test_no_collapse_with_aux_loss():
    """With proper aux loss, effective experts should stay close to N=8."""
    result = run_collapse_experiment(aux_coeff=1e-2)
    print(f"\nWith aux loss: effective_experts={result['effective_experts']:.3f} / 8.0")
    # Effective experts should stay above 5.0 with proper balancing
    assert result["effective_experts"] > 4.0, (
        f"Expected balanced routing (eff > 4.0) with aux loss, "
        f"got {result['effective_experts']:.3f}"
    )


if __name__ == "__main__":
    r_no_aux = run_collapse_experiment(aux_coeff=0.0)
    r_aux = run_collapse_experiment(aux_coeff=1e-2)
    print("\nCollapse Experiment Results:")
    print(f"  aux_coeff=0.0 -> effective_experts = {r_no_aux['effective_experts']:.3f}")
    print(f"  aux_coeff=0.01 -> effective_experts = {r_aux['effective_experts']:.3f}")
    delta = r_aux["effective_experts"] - r_no_aux["effective_experts"]
    print(f"  Improvement from aux loss: +{delta:.3f} effective experts")
```

```bash
python tests/test_expert_collapse.py
python -m pytest tests/test_expert_collapse.py -v -s
```

### 3.2 Numerical Stability Under Extreme Inputs

MoE routers are vulnerable to numerical instability when input activations are very large (e.g., early training with poorly initialized weights) or when mixed precision is used without appropriate dtype handling. The router's `softmax` can saturate to one-hot distributions under large logits, producing the same collapse dynamics as an insufficient auxiliary loss. The following tests probe these boundary conditions.

```python
# tests/test_numerical_stability.py
"""
Numerical stability tests for MoELayer under extreme input conditions.
"""
from __future__ import annotations

import pytest
import torch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.moe_layer import MoEConfig, MoELayer


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def make_moe() -> MoELayer:
    cfg = MoEConfig(d_model=64, d_ff=256, num_experts=8, top_k=2, aux_loss_coeff=0.01)
    return MoELayer(cfg).to(DEVICE)


class TestNumericalStability:
    def test_large_input_values(self):
        """Large activations must not produce NaN outputs."""
        moe = make_moe()
        x = torch.randn(4, 16, 64, device=DEVICE) * 100.0
        out, aux = moe(x)
        assert not torch.isnan(out).any(), "NaN in output with large inputs"
        assert not torch.isinf(out).any(), "Inf in output with large inputs"

    def test_very_small_input_values(self):
        """Near-zero activations must not produce NaN via division."""
        moe = make_moe()
        x = torch.randn(4, 16, 64, device=DEVICE) * 1e-6
        out, aux = moe(x)
        assert not torch.isnan(out).any(), "NaN in output with tiny inputs"

    def test_all_zero_input(self):
        """All-zero input should produce a finite output (not NaN)."""
        moe = make_moe()
        x = torch.zeros(4, 16, 64, device=DEVICE)
        out, aux = moe(x)
        assert not torch.isnan(out).any(), "NaN in output for all-zero input"
        # Router should still produce a valid distribution (uniform, since all logits equal)

    def test_single_expert_receives_all_tokens_no_crash(self):
        """
        Simulate collapsed routing: manually bias router gate weights so all
        tokens go to expert 0.  The layer must still produce valid output.
        """
        moe = make_moe()
        with torch.no_grad():
            # Set all gate weights to zero except column 0, which gets large weight
            moe.router.gate.weight.zero_()
            moe.router.gate.weight[0] = 10.0  # Expert 0 always wins
        x = torch.randn(4, 16, 64, device=DEVICE)
        out, aux = moe(x)
        assert not torch.isnan(out).any()
        assert not torch.isinf(out).any()

    def test_fp16_mixed_precision(self):
        """AMP autocast must not produce NaN in the router softmax."""
        if not torch.cuda.is_available():
            pytest.skip("CUDA required for AMP test")
        moe = make_moe()
        x = torch.randn(8, 32, 64, device=DEVICE)
        with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
            out, aux = moe(x)
        # Cast back to float32 for NaN check
        out_f32 = out.float()
        assert not torch.isnan(out_f32).any(), "NaN in AMP forward pass"

    def test_gradient_clipping_prevents_explosion(self):
        """Verify that gradient clipping prevents router gate weight explosion."""
        moe = make_moe()
        x = torch.randn(4, 16, 64, device=DEVICE, requires_grad=True)
        # Large input to amplify gradients
        x_large = x * 50.0
        out, aux = moe(x_large)
        (out.sum() + aux).backward()
        # Clip at norm=1.0
        gate_grad_before = moe.router.gate.weight.grad.norm().item()
        torch.nn.utils.clip_grad_norm_(moe.parameters(), max_norm=1.0)
        gate_grad_after = moe.router.gate.weight.grad.norm().item()
        assert gate_grad_after <= 1.0 + 1e-5, \
            f"Gradient clipping failed: norm after={gate_grad_after:.4f}"
        print(f"\nGrad norm before clip: {gate_grad_before:.4f}")
        print(f"Grad norm after clip:  {gate_grad_after:.4f}")
```

```bash
python -m pytest tests/test_numerical_stability.py -v -s
```

### 3.3 Checkpoint Integrity and Resume

A model that cannot reliably save and restore its state is not production-ready. The router gate weights are especially important to preserve exactly — a router restored with the wrong weights will exhibit a completely different routing pattern than what was trained, potentially causing silent accuracy degradation with no error message.

```python
# tests/test_checkpoint_integrity.py
"""
Verify that MoETransformer checkpoint save/restore preserves:
1. Exact logit outputs (deterministic forward pass)
2. Router gate weights (no floating point rounding on save)
3. Expert weights
4. Routing statistics
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import torch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.moe_layer import MoEConfig
from models.moe_transformer import MoETransformer, TransformerConfig


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_small_model() -> MoETransformer:
    moe_cfg = MoEConfig(d_model=64, d_ff=256, num_experts=4, top_k=2)
    cfg = TransformerConfig(
        vocab_size=100, d_model=64, num_heads=2, num_layers=2, max_seq_len=32, moe_cfg=moe_cfg
    )
    return MoETransformer(cfg).to(DEVICE)


def test_checkpoint_exact_reproducibility():
    model = build_small_model()
    model.eval()
    x = torch.randint(0, 100, (2, 16), device=DEVICE)

    with torch.no_grad():
        logits_before, aux_before = model(x)

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt_path = Path(tmpdir) / "model.pt"
        torch.save(model.state_dict(), ckpt_path)

        # Load into a fresh model
        model2 = build_small_model()
        model2.load_state_dict(torch.load(ckpt_path, map_location=DEVICE))
        model2.eval()

        with torch.no_grad():
            logits_after, aux_after = model2(x)

    assert torch.allclose(logits_before, logits_after, atol=0.0, rtol=0.0), \
        "Logits changed after checkpoint round-trip (bit-exact failure)"
    print("\nCheckpoint bit-exact reproducibility: PASSED")
    print(f"  Max logit deviation: {(logits_before - logits_after).abs().max().item():.2e}")


def test_router_gate_weights_preserved():
    model = build_small_model()

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt_path = Path(tmpdir) / "model.pt"
        torch.save(model.state_dict(), ckpt_path)
        model2 = build_small_model()
        model2.load_state_dict(torch.load(ckpt_path, map_location=DEVICE))

    for i, (blk1, blk2) in enumerate(zip(model.blocks, model2.blocks)):
        if hasattr(blk1.ffn, "router"):
            w1 = blk1.ffn.router.gate.weight
            w2 = blk2.ffn.router.gate.weight
            assert torch.equal(w1, w2), f"Router gate mismatch in block {i}"

    print("Router gate weight preservation: PASSED")


def test_routing_stats_preserved():
    model = build_small_model()
    model.eval()

    # Get routing stats before save
    h = torch.randn(4, 16, 64, device=DEVICE)
    stats_before = {}
    for i, blk in enumerate(model.blocks):
        if hasattr(blk.ffn, "router"):
            stats_before[i] = blk.ffn.get_routing_stats(h)

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt_path = Path(tmpdir) / "model.pt"
        torch.save(model.state_dict(), ckpt_path)
        model2 = build_small_model()
        model2.load_state_dict(torch.load(ckpt_path, map_location=DEVICE))
        model2.eval()

    for i, blk in enumerate(model2.blocks):
        if hasattr(blk.ffn, "router") and i in stats_before:
            stats_after = blk.ffn.get_routing_stats(h)
            diff = abs(stats_before[i]["effective_experts"] - stats_after["effective_experts"])
            assert diff < 1e-5, \
                f"Routing stats changed after checkpoint in block {i}: diff={diff}"

    print("Routing statistics preservation: PASSED")


if __name__ == "__main__":
    test_checkpoint_exact_reproducibility()
    test_router_gate_weights_preserved()
    test_routing_stats_preserved()
    print("\nAll checkpoint integrity tests PASSED.")
```

```bash
python -m pytest tests/test_checkpoint_integrity.py -v -s
```

### 3.4 The Evaluation Pipeline

The final integration of all exercises is a standalone eval pipeline that loads a saved checkpoint and runs a comprehensive benchmark, outputting a structured report. This is the script you would run in CI to gate a model release.

```python
# eval_pipeline.py
"""
Standalone evaluation pipeline for MoE transformer checkpoints.
Produces a structured benchmark report covering:
  - Task loss and perplexity
  - Expert routing health (effective experts, load imbalance)
  - Throughput (tokens/sec)
  - Peak GPU memory
  - Numerical stability probe

Usage:
  python eval_pipeline.py --checkpoint checkpoints/baseline/best_model.pt
  python eval_pipeline.py --benchmark  (runs against a randomly initialized model)
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.synthetic_dataset import SyntheticMoEDataset
from models.moe_layer import MoEConfig
from models.moe_transformer import MoETransformer, TransformerConfig


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model(checkpoint_path: Optional[str]) -> MoETransformer:
    if checkpoint_path and Path(checkpoint_path).exists():
        ckpt = torch.load(checkpoint_path, map_location=DEVICE)
        saved_args = ckpt.get("args", {})
        moe_cfg = MoEConfig(
            d_model=saved_args.get("d_model", 256),
            d_ff=saved_args.get("d_model", 256) * 4,
            num_experts=saved_args.get("num_experts", 8),
            top_k=saved_args.get("top_k", 2),
            aux_loss_coeff=saved_args.get("aux_loss_coeff", 0.01),
        )
        cfg = TransformerConfig(
            vocab_size=300,
            d_model=saved_args.get("d_model", 256),
            num_heads=max(1, saved_args.get("d_model", 256) // 64),
            num_layers=saved_args.get("num_layers", 4),
            max_seq_len=saved_args.get("seq_len", 128),
            moe_cfg=moe_cfg,
        )
        model = MoETransformer(cfg).to(DEVICE)
        model.load_state_dict(ckpt["model_state"])
        print(f"Loaded checkpoint from {checkpoint_path}")
        print(f"  Checkpoint epoch: {ckpt.get('epoch', 'unknown')}")
        print(f"  Checkpoint val_loss: {ckpt.get('val_loss', 'unknown'):.4f}")
    else:
        print("No checkpoint provided. Using randomly initialized model.")
        moe_cfg = MoEConfig(d_model=256, d_ff=1024, num_experts=8, top_k=2)
        cfg = TransformerConfig(vocab_size=300, d_model=256, num_heads=4, num_layers=4, moe_cfg=moe_cfg)
        model = MoETransformer(cfg).to(DEVICE)
    return model


def eval_task_metrics(model: MoETransformer, loader: DataLoader) -> dict:
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    total_tokens = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            logits, _ = model(x)
            loss = criterion(logits.view(-1, logits.size(-1)), y.view(-1))
            total_loss += loss.item() * y.numel()
            total_tokens += y.numel()
    mean_loss = total_loss / total_tokens
    return {
        "task_loss": mean_loss,
        "perplexity": float(np.exp(mean_loss)),
        "tokens_evaluated": total_tokens,
    }


def eval_routing_health(model: MoETransformer, loader: DataLoader) -> dict:
    model.eval()
    all_stats = []
    with torch.no_grad():
        for i, (x, _) in enumerate(loader):
            if i >= 8:
                break
            x = x.to(DEVICE)
            for block in model.blocks:
                if hasattr(block.ffn, "router"):
                    h = torch.randn(x.size(0), x.size(1), model.cfg.d_model, device=DEVICE)
                    stats = block.ffn.get_routing_stats(h)
                    all_stats.append(stats)

    if not all_stats:
        return {"error": "No MoE layers found"}

    return {
        "mean_effective_experts": np.mean([s["effective_experts"] for s in all_stats]),
        "mean_max_load": np.mean([s["max_load"] for s in all_stats]),
        "mean_imbalance": np.mean([s["load_imbalance"] for s in all_stats]),
        "routing_health_score": np.mean([s["effective_experts"] for s in all_stats])
            / model.cfg.moe_cfg.num_experts,
    }


def eval_throughput(model: MoETransformer, batch_size: int = 32, seq_len: int = 128) -> dict:
    model.eval()
    x = torch.randint(0, 300, (batch_size, seq_len), device=DEVICE)

    if DEVICE.type == "cuda":
        torch.cuda.reset_peak_memory_stats(DEVICE)
        for _ in range(5):
            with torch.no_grad():
                model(x)
        torch.cuda.synchronize(DEVICE)

    latencies = []
    with torch.no_grad():
        for _ in range(30):
            if DEVICE.type == "cuda":
                torch.cuda.synchronize(DEVICE)
            t0 = time.perf_counter()
            model(x)
            if DEVICE.type == "cuda":
                torch.cuda.synchronize(DEVICE)
            latencies.append(time.perf_counter() - t0)

    total_tokens = batch_size * seq_len
    mean_lat = np.mean(latencies)
    peak_mem_mb = torch.cuda.max_memory_allocated(DEVICE) / 1024**2 if DEVICE.type == "cuda" else 0.0

    return {
        "mean_latency_ms": mean_lat * 1000,
        "p50_latency_ms": np.percentile(latencies, 50) * 1000,
        "p99_latency_ms": np.percentile(latencies, 99) * 1000,
        "throughput_tok_per_s": total_tokens / mean_lat,
        "peak_gpu_mem_mb": peak_mem_mb,
    }


def eval_numerical_stability(model: MoETransformer) -> dict:
    model.eval()
    results = {}
    test_cases = {
        "normal": torch.randn(4, 32, model.cfg.d_model, device=DEVICE),
        "large_activation": torch.randn(4, 32, model.cfg.d_model, device=DEVICE) * 100,
        "tiny_activation": torch.randn(4, 32, model.cfg.d_model, device=DEVICE) * 1e-6,
        "all_zeros": torch.zeros(4, 32, model.cfg.d_model, device=DEVICE),
    }
    for name, h in test_cases.items():
        with torch.no_grad():
            # Test through any MoE layer
            for block in model.blocks:
                if hasattr(block.ffn, "router"):
                    out, aux = block.ffn(h)
                    results[name] = {
                        "has_nan": torch.isnan(out).any().item(),
                        "has_inf": torch.isinf(out).any().item(),
                        "out_max": out.abs().max().item(),
                        "aux_loss": aux.item(),
                    }
                    break
    return results


def print_report(task: dict, routing: dict, throughput: dict, stability: dict) -> None:
    sep = "=" * 65
    print(f"\n{sep}")
    print("  MOE TRANSFORMER EVALUATION REPORT")
    print(sep)

    print("\n── Task Performance ──────────────────────────────────────────")
    print(f"  Task Loss:         {task['task_loss']:.4f}")
    print(f"  Perplexity:        {task['perplexity']:.2f}")
    print(f"  Tokens Evaluated:  {task['tokens_evaluated']:,}")

    print("\n── Routing Health ────────────────────────────────────────────")
    if "error" not in routing:
        print(f"  Effective Experts: {routing['mean_effective_experts']:.2f}")
        print(f"  Max Load:          {routing['mean_max_load']:.3f}")
        print(f"  Load Imbalance:    {routing['mean_imbalance']:.3f}")
        health_pct = routing['routing_health_score'] * 100
        health_label = "HEALTHY" if health_pct > 50 else "DEGRADED" if health_pct > 25 else "COLLAPSED"
        print(f"  Health Score:      {health_pct:.1f}%  [{health_label}]")

    print("\n── Throughput & Memory ───────────────────────────────────────")
    print(f"  Mean Latency:      {throughput['mean_latency_ms']:.2f} ms")
    print(f"  P50 Latency:       {throughput['p50_latency_ms']:.2f} ms")
    print(f"  P99 Latency:       {throughput['p99_latency_ms']:.2f} ms")
    print(f"  Throughput:        {throughput['throughput_tok_per_s']:.0f} tok/s")
    print(f"  Peak GPU Mem:      {throughput['peak_gpu_mem_mb']:.1f} MB")

    print("\n── Numerical Stability ───────────────────────────────────────")
    for name, result in stability.items():
        status = "PASS" if not result["has_nan"] and not result["has_inf"] else "FAIL"
        print(
            f"  [{status}] {name:25s}  "
            f"max={result['out_max']:.3e}  "
            f"aux={result['aux_loss']:.4f}  "
            f"nan={result['has_nan']}  inf={result['has_inf']}"
        )

    print(f"\n{sep}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="MoE Evaluation Pipeline")
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--benchmark", action="store_true",
                        help="Run with randomly initialized model (no checkpoint)")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--seq_len", type=int, default=128)
    args = parser.parse_args()

    model = load_model(None if args.benchmark else args.checkpoint)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"\nModel parameters: {n_params:,}")
    print(f"Device: {DEVICE}")

    dataset = SyntheticMoEDataset(num_sequences=2000, seq_len=args.seq_len, seed=0)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=2)

    print("\nRunning evaluations...")
    task_metrics = eval_task_metrics(model, loader)
    routing_metrics = eval_routing_health(model, loader)
    throughput_metrics = eval_throughput(model, args.batch_size, args.seq_len)
    stability_metrics = eval_numerical_stability(model)

    print_report(task_metrics, routing_metrics, throughput_metrics, stability_metrics)


if __name__ == "__main__":
    main()
```

```bash
# Against a trained checkpoint
python eval_pipeline.py --checkpoint checkpoints/baseline/best_model.pt

# Benchmark mode (random init, sanity-check the pipeline itself)
python eval_pipeline.py --benchmark
```

---

## ML Diagnostic Cheat Sheet & Verification Checklist

### Quick Reference: MoE Health Diagnostics

The table below maps observable symptoms to their diagnostic commands and the most likely root cause in a MoE system. Keep it visible during any debugging session.

| Symptom | Diagnostic Command | Most Likely Cause |
|---|---|---|
| `effective_experts` < 2.0 after 1k steps | `python eval_pipeline.py --benchmark` | `aux_loss_coeff` too small or zero |
| Task loss not decreasing, aux loss near zero | Inspect TensorBoard `loss/aux` | `aux_loss_coeff` too large (>0.5) suppressing task gradient |
| NaN in logits during early training | `python -m pytest tests/test_numerical_stability.py -v` | Missing gradient clipping or extreme LR |
| p99 latency >> p50 latency | `python benchmarks/throughput_bench.py` | Expert load imbalance causing serial dispatch stalls |
| Val loss recovers after checkpoint load | `python -m pytest tests/test_checkpoint_integrity.py -v` | Router gate weights corrupted or mismatched |
| GPU OOM with large `num_experts` | `torch.cuda.memory_summary()` | Dispatch buffer allocation scales with N×B×T |

### Routing Health: Interpreting `effective_experts`

The effective number of experts $\text{eff} = 1 / \sum_i f_i^2$ where $f_i$ is the fraction of tokens routed to expert $i$. A healthy training run with $N=8$ experts and `top_k=2` should maintain an effective experts score above 5.0 after the first few hundred steps. A score below 3.0 indicates significant imbalance; below 1.5 indicates near-total collapse to one or two experts. The load imbalance metric $\max_i(f_i) - \min_i(f_i)$ should stay below 0.3 for a well-balanced 8-expert model.

### Full Verification Checklist

The following sequence is the complete operational verification pass. Run it in order after any change to router architecture, training hyperparameters, or model scale.

```bash
# Step 1: Environment sanity
python verify_env.py

# Step 2: Unit correctness — shape, aux loss, gradients, weight normalization
python -m pytest tests/test_moe_layer.py -v

# Step 3: Expert collapse stress test
python -m pytest tests/test_expert_collapse.py -v -s

# Step 4: Numerical stability under edge-case inputs
python -m pytest tests/test_numerical_stability.py -v -s

# Step 5: Checkpoint integrity
python -m pytest tests/test_checkpoint_integrity.py -v -s

# Step 6: Run all tests together and produce coverage summary
python -m pytest tests/ -v --tb=short

# Step 7: Throughput benchmark (reports tok/s and peak GPU memory)
python benchmarks/throughput_bench.py

# Step 8: CPU profiling of dispatch hotspot
python benchmarks/profile_moe.py

# Step 9: Train baseline model
python train.py --epochs 10 --log_dir logs/run_baseline --checkpoint_dir checkpoints/baseline

# Step 10: Full evaluation report against trained checkpoint
python eval_pipeline.py --checkpoint checkpoints/baseline/best_model.pt

# Step 11: Hyperparameter sweep (long-running; run overnight or on a compute cluster)
python sweep.py

# Step 12: Analyze sweep results
python analysis/analyze_sweep.py

# Step 13: Inspect training curves in TensorBoard
tensorboard --logdir logs/ --port 6006
```

### Core Invariants to Enforce in Production

The auxiliary loss coefficient is not a set-and-forget hyperparameter. It requires monitoring throughout training, because the optimal value shifts as the router's distribution shifts. If your effective experts metric drops below $N/2$ at any point during training beyond the first 500 steps, treat it as a P1 alert: either increase `aux_loss_coeff` by 5× or switch to Z-score router noise injection (adding Gaussian noise to the router logits, as in the original MoE paper by Shazeer et al., 2017) to break the feedback loop.

Expert dropout during training — randomly masking one expert from the top-k selection with probability 0.1 — is a regularization technique that is distinct from the auxiliary loss. It forces the router to maintain at least some familiarity with non-dominant experts, preventing the degenerate case where an expert's weights become so stale that routing even one token to it after a period of neglect produces garbage output. Neither technique alone is sufficient; the auxiliary loss provides the gradient signal to maintain balance, while expert dropout provides the forced exploration that prevents premature specialization.

The checkpoint verification tests in Exercise 3.3 must be part of your model release gate. A MoE model with correctly saved task weights but slightly corrupted router weights is indistinguishable from a healthy model by loss metrics alone — it will produce valid-looking output with a completely different internal routing pattern, making reproducibility impossible and behavioral analysis unreliable.
