# Lesson 2: Routing Mechanisms

## 1. First-Principles Intuition & Invariants

The central promise of a Mixture of Experts architecture is conditional computation: for any given input, only a small fraction of the network's total parameter count is activated. This promise is only as good as the mechanism that decides *which* fraction. The routing mechanism is therefore not a peripheral component of a MoE system—it is the load-bearing wall. Get it wrong and the entire structure collapses, not dramatically but quietly, through expert collapse, training instability, and inference throughput that never materializes into actual speedup.

To understand why routing is hard, start from the problem it must solve simultaneously on three axes. First, it must be *discriminative*: it must learn to send semantically meaningful signals to the right experts, so that experts can specialize and become genuinely better at a subproblem than a dense network would be. Second, it must be *balanced*: if one expert receives 80% of all tokens and others receive almost nothing, the unused experts contribute no capacity and the loaded expert becomes a bottleneck that annihilates the latency benefits of sparsity. Third, it must be *differentiable enough* to train end-to-end via gradient descent, which creates an immediate tension with the discrete, combinatorial nature of expert selection.

These three axes are not independently optimizable. Routing decisions that maximize discriminability tend toward hard, winner-take-all assignments—the network routes each token to the single most relevant expert. But hard discrete selection is a step function with zero gradient almost everywhere, making it effectively invisible to backpropagation. Softening the selection to restore gradient flow blurs the specialization signal and can cause expert representations to converge. Enforcing balance via auxiliary losses changes the optimization landscape in ways that interact nonlinearly with the primary task loss, introducing instabilities that only manifest after thousands of training steps. The practitioner navigating these trade-offs is simultaneously a machine learning researcher, a numerical analyst, and a distributed systems engineer, because the wrong routing choice at training time is reflected in GPU communication patterns at inference time.

The foundational invariant of any routing mechanism can be stated precisely. Given a token representation $\mathbf{x} \in \mathbb{R}^d$, a set of $E$ expert networks $\{f_1, \ldots, f_E\}$, and a router that produces weights $\mathbf{w} = \text{Router}(\mathbf{x}) \in \mathbb{R}^E$, the output of the MoE layer is:

$$\mathbf{y} = \sum_{i \in \mathcal{S}(\mathbf{x})} w_i \cdot f_i(\mathbf{x})$$

where $\mathcal{S}(\mathbf{x})$ is the selected subset of experts. The entire research program of routing mechanisms is the study of what $\text{Router}$ and $\mathcal{S}$ should be, how $w_i$ should be normalized, and how the system should be penalized when $\mathcal{S}$ develops pathological structure across a batch of tokens.

---

## 2. Core Architecture & Mechanics

### The Gating Function and Its Variants

The gating function is the parametric heart of the router. In its simplest form, as introduced by Shazeer et al. in the 2017 "Outrageously Large Neural Networks" paper, the gate is a linear projection followed by a softmax:

$$\mathbf{g}(\mathbf{x}) = \text{Softmax}(\mathbf{x} \cdot W_g)$$

where $W_g \in \mathbb{R}^{d \times E}$. The gate projects the token from the model's hidden dimension $d$ into the $E$-dimensional expert logit space, and softmax normalizes these into a probability distribution over experts. This is the *learned, dense gate*—every expert receives a nonzero weight, and the selection of a sparse subset happens afterward by taking the top-$K$ values and zeroing the rest:

$$\mathbf{g}_K(\mathbf{x})_i = \begin{cases} g_i(\mathbf{x}) & \text{if } i \in \text{Top-}K(\mathbf{g}(\mathbf{x})) \\ 0 & \text{otherwise} \end{cases}$$

The result is re-normalized over the selected set before weighting the expert outputs. In practice, $K = 1$ or $K = 2$ is used in nearly all production systems. Switch Transformer (Fedus et al., 2021) demonstrated that $K=1$ is not only viable but can outperform $K=2$ because the reduced communication overhead and simpler load balancing more than compensate for the loss of ensemble benefit. GLaM (Du et al., 2021) used $K=2$ and found that the two-expert mixture provides a meaningful quality improvement at the cost of roughly twice the per-token FLOPs from the expert networks, though the router itself remains cheap.

The critical subtlety of Top-K gating is that the top-K selection operator itself is not differentiable with respect to the gate weights that determine *which* experts are selected. The gradient flows through the gate weights only for selected experts and only through the continuous weight values, not through the routing decision itself. This means the router learns from feedback about *how much* to weight an expert it has already selected, not whether to select it in the first place. This partial gradient is nonetheless sufficient in practice: the gate values and the selection decisions are coupled through the softmax normalization, so improving the gap between selected and unselected logits propagates gradient information that gradually sharpens the routing decisions.

**Noisy Top-K Gating** extends the base formulation by injecting learned Gaussian noise into the logits before the top-K operation:

$$\tilde{g}_i(\mathbf{x}) = (\mathbf{x} \cdot W_g)_i + \epsilon \cdot \text{Softplus}((\mathbf{x} \cdot W_{noise})_i), \quad \epsilon \sim \mathcal{N}(0, 1)$$

The noise magnitude is itself a learned function of the input, parameterized by a second projection $W_{noise} \in \mathbb{R}^{d \times E}$. During training, this noise serves as a stochastic exploration mechanism: tokens near expert decision boundaries get randomly routed to different experts across training steps, which prevents experts near the decision boundary from never receiving gradient signal. At inference, the noise is disabled, and the deterministic gate is used. The practical effect is that the learned gate values are smoother and better calibrated at initialization, before the routing has stabilized.

**Soft Gating** abandons sparsity entirely during training and allows all experts to contribute a weighted sum to every token. This is the purest gradient signal—every expert receives feedback from every token—but it completely forfeits the computational savings of sparse routing. Soft gating is used in some mixture architectures as a training warm-up strategy, transitioning to sparse routing once the expert specializations have stabilized. It is also the basis of soft MoE (Puigcerver et al., 2023), which reframes the routing problem: instead of routing tokens to experts, it routes *linear combinations* of tokens to experts, then recombines. This eliminates the load imbalance problem entirely but changes the semantics of expert computation from token-wise to slot-wise, which complicates autoregressive inference.

**Expert Choice Routing** (Zhou et al., 2022) inverts the selection direction. Rather than each token selecting its top-$K$ experts, each expert selects its top-$C$ tokens from the batch, where $C$ is a fixed buffer capacity. This mechanically guarantees perfect load balance with zero auxiliary loss because the constraint is built into the selection operator. The trade-off is that tokens are no longer guaranteed any expert will process them—a token that ranks below the capacity threshold for all experts is simply dropped. This is acceptable in encoder-only or non-autoregressive settings where the loss is computed over all positions and dropped tokens simply contribute zero gradient, but it is problematic for autoregressive decoders where every output token must be generated.

### Fixed vs. Learned Routing

The distinction between fixed and learned routing is more consequential than it appears. Fixed routing assigns tokens to experts by a deterministic function of the token's content that does not depend on trained parameters. The simplest variant is **hash routing**: a hash function maps the token identity (its embedding index, for example) to an expert index, distributing tokens uniformly by construction. Hash routing is perfectly load-balanced by design and requires zero auxiliary loss. It was explored by Roller et al. (2021) as a baseline, and the surprising finding is that it is often competitive with learned routing, particularly at large scale. This challenges the assumption that the router must learn meaningful semantic routing to achieve expert specialization—it turns out that consistent, stable routing (even if semantically arbitrary) may be sufficient for experts to find useful specializations, because the specialization emerges from gradient pressure on the expert weights, not from the routing policy.

Learned routing, by contrast, allows the gating function to develop semantic structure: different token types, syntactic roles, or frequency characteristics tend to route to different experts. Analysis of routing decisions in trained models (e.g., from Switch Transformer ablations) shows that routing is moderately but not perfectly correlated with token identity—the same token receives consistent routes across different contexts. This consistency is valuable; wildly inconsistent routing prevents experts from accumulating a stable training distribution, which is one source of the instability discussed in Section 3.

A third category, **Mixture of Experts with Expert Prototypes** (from BASE Layers, Lewis et al., 2021), uses a linear assignment algorithm to find the globally optimal matching between tokens and experts under a balance constraint. This is a fully differentiable, balanced, learned routing strategy, but computing the optimal assignment requires solving a transportation problem over the entire batch, which is expensive and limits minibatch granularity. It is primarily relevant for pre-training research rather than production inference pipelines.

### Signal Flow Through a MoE Layer

The concrete data-flow through a MoE transformer layer is worth tracing precisely, because the shape transformations reveal why routing interacts so heavily with distributed memory layout.

```
Input Tensor:  [B, T, D]
                 │
                 ▼
         ┌──────────────┐
         │   Gate (Wg)  │   Linear: [D → E], Softmax over E
         └──────────────┘
                 │
         g ∈ [B, T, E]  (dense logits)
                 │
                 ▼
         ┌──────────────┐
         │  Top-K Select│   Produces: indices [B, T, K],
         │              │             weights [B, T, K]
         └──────────────┘
                 │
         ┌───────┴────────────────────────────────────┐
         │  Dispatch: scatter tokens to expert buffers │
         │  Buffer per expert: [capacity C, D]         │
         └───────┬────────────────────────────────────┘
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
  Expert_1    Expert_2  ... Expert_E
  FFN([C,D]) FFN([C,D])    FFN([C,D])
     │           │           │
     └───────────┼───────────┘
                 │
         ┌───────┴────────────────────────────────────┐
         │  Combine: gather expert outputs, weight sum │
         └───────┬────────────────────────────────────┘
                 │
         Output: [B, T, D]
```

The dispatch and combine steps are the architecturally expensive operations. In a single-device setting, dispatch is a scatter operation: for each token, write its hidden state into the input buffer of each expert it was routed to. In a multi-device setting where experts are distributed across devices (Expert Parallelism), dispatch becomes an all-to-all collective communication: each device holds a subset of experts and must receive tokens from all other devices that were routed to its experts. The all-to-all over $E$ experts on $N$ devices transfers $O(B \cdot T \cdot D)$ bytes and is typically the dominant communication cost in a MoE training run.

The **expert buffer capacity** $C$ is a critical parameter that mediates the tension between load balance and token dropping. Capacity is typically set as $C = \text{capacity\_factor} \times (B \cdot T / E)$, where the capacity factor is a hyperparameter slightly above 1.0 (e.g., 1.25). Tokens routed to an expert that has already filled its buffer are dropped—their hidden states are set to zero or passed through unchanged via a residual bypass. Setting capacity factor too low increases drops and degrades quality. Setting it too high wastes memory and compute on empty buffer slots.

### Auxiliary Loss Formulations for Load Balancing

Without explicit regularization, learned routing in a Top-K gating scheme almost universally collapses: a small number of experts receive nearly all tokens, and the remaining experts effectively die. This occurs because the gate is initialized approximately uniformly, but any small initial perturbation causes some experts to receive slightly more tokens, receive more gradient updates, become slightly better, and therefore attract still more tokens. This is a positive feedback loop—a routing rich-get-richer dynamic that left unchecked produces near-zero expert utilization within the first few hundred training steps.

The standard mitigation is an auxiliary load balancing loss added to the primary task loss with a small coefficient $\alpha$:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{task}} + \alpha \cdot \mathcal{L}_{\text{balance}}$$

The Switch Transformer formulation defines the balance loss as the dot product between the fraction of tokens dispatched to each expert and the fraction of router probability assigned to each expert:

$$\mathcal{L}_{\text{balance}} = E \cdot \sum_{i=1}^{E} f_i \cdot P_i$$

where $f_i = \frac{1}{T} \sum_{t=1}^{T} \mathbf{1}[\text{argmax}(\mathbf{g}(\mathbf{x}_t)) = i]$ is the fraction of tokens routed to expert $i$ (computed with a straight-through estimator since it involves argmax), and $P_i = \frac{1}{T} \sum_{t=1}^{T} g_i(\mathbf{x}_t)$ is the mean softmax probability assigned to expert $i$. The product $f_i \cdot P_i$ is minimized when both quantities are equal to $1/E$, i.e., when load is perfectly balanced. The factor $E$ is a normalization constant ensuring the loss is scale-invariant to the number of experts.

The coefficient $\alpha$ requires careful tuning. Switch Transformer found $\alpha = 10^{-2}$ effective for language model pre-training. Values too large cause the balance loss to dominate, forcing uniform routing that destroys expert specialization. Values too small allow collapse to proceed. In practice, $\alpha$ is often treated as a schedule-dependent hyperparameter, starting at a higher value to prevent early collapse and annealing as routing stabilizes.

GLaM and later work proposed a variant that penalizes the variance of load distribution rather than the covariance of $f$ and $P$, arguing that the variance formulation has better gradient properties when the distribution is already nearly balanced. The auxiliary loss from DeepSeek-MoE separates experts into shared experts (always activated) and routed experts, requiring a modified balance loss that only penalizes imbalance among the routed subset—a refinement that matters when a large fraction of capacity is allocated to shared computation.

The following PyTorch implementation captures the Switch Transformer balance loss precisely:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Tuple

@dataclass
class MoEConfig:
    hidden_dim: int = 1024
    num_experts: int = 8
    top_k: int = 2
    capacity_factor: float = 1.25
    balance_loss_coeff: float = 1e-2
    noise_std: float = 1e-2


class TopKRouter(nn.Module):
    """
    Top-K sparse router with noisy gating and Switch Transformer auxiliary
    load-balancing loss. Supports expert buffer capacity enforcement.
    """

    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.cfg = cfg
        self.gate = nn.Linear(cfg.hidden_dim, cfg.num_experts, bias=False)
        # Learned noise magnitude projection (noisy top-k gating)
        self.noise_scale = nn.Linear(cfg.hidden_dim, cfg.num_experts, bias=False)

    def forward(
        self,
        x: torch.Tensor,          # [B, T, D]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
          dispatch_weights  [B, T, K]  – gating weights for top-K experts
          dispatch_indices  [B, T, K]  – expert indices for top-K experts
          router_probs      [B, T, E]  – full softmax distribution (for aux loss)
          balance_loss      scalar     – Switch Transformer auxiliary loss
        """
        B, T, D = x.shape
        E = self.cfg.num_experts
        K = self.cfg.top_k

        logits = self.gate(x)  # [B, T, E]

        if self.training and self.cfg.noise_std > 0.0:
            noise_mag = F.softplus(self.noise_scale(x))          # [B, T, E]
            noise = torch.randn_like(logits) * noise_mag * self.cfg.noise_std
            logits = logits + noise

        router_probs = F.softmax(logits, dim=-1)  # [B, T, E]

        # ----- Top-K selection -----
        topk_weights, topk_indices = torch.topk(router_probs, K, dim=-1)
        # Re-normalize selected weights so they sum to 1 per token
        topk_weights = topk_weights / (topk_weights.sum(dim=-1, keepdim=True) + 1e-9)

        # ----- Switch Transformer Auxiliary Loss -----
        # f_i: fraction of tokens whose top-1 expert is i (straight-through)
        top1_indices = topk_indices[..., 0]                        # [B, T]
        # one_hot over top-1 assignment, averaged over B*T
        token_assignments = F.one_hot(top1_indices, num_classes=E).float()  # [B, T, E]
        f = token_assignments.mean(dim=[0, 1])                     # [E]
        # P_i: mean router probability for expert i over B*T
        P = router_probs.mean(dim=[0, 1])                          # [E]
        balance_loss = self.cfg.balance_loss_coeff * E * (f * P).sum()

        return topk_weights, topk_indices, router_probs, balance_loss


class ExpertFFN(nn.Module):
    """Single expert: position-wise FFN with gated activation (SwiGLU)."""

    def __init__(self, hidden_dim: int, ffn_dim: int):
        super().__init__()
        self.w1 = nn.Linear(hidden_dim, ffn_dim, bias=False)
        self.w2 = nn.Linear(ffn_dim, hidden_dim, bias=False)
        self.w_gate = nn.Linear(hidden_dim, ffn_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w2(F.silu(self.w1(x)) * self.w_gate(x))


class MoELayer(nn.Module):
    """
    Full Mixture-of-Experts layer.

    Dispatch: scatter tokens to per-expert capacity buffers.
    Expert compute: each expert processes its buffer independently.
    Combine: weighted sum of expert outputs back into [B, T, D].

    Tokens that overflow expert capacity are passed through unchanged
    via residual bypass (no drop, to preserve autoregressive correctness).
    """

    def __init__(self, cfg: MoEConfig, ffn_dim: int):
        super().__init__()
        self.cfg = cfg
        self.router = TopKRouter(cfg)
        self.experts = nn.ModuleList([
            ExpertFFN(cfg.hidden_dim, ffn_dim)
            for _ in range(cfg.num_experts)
        ])

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape
        E = self.cfg.num_experts
        K = self.cfg.top_k
        capacity = int(self.cfg.capacity_factor * B * T / E)

        topk_weights, topk_indices, _, balance_loss = self.router(x)
        # topk_weights: [B, T, K], topk_indices: [B, T, K]

        # Flatten batch and sequence for dispatch
        x_flat = x.view(B * T, D)                          # [N, D]  N = B*T
        idx_flat = topk_indices.view(B * T, K)              # [N, K]
        w_flat = topk_weights.view(B * T, K)                # [N, K]

        output_flat = torch.zeros_like(x_flat)              # [N, D]

        for expert_id, expert in enumerate(self.experts):
            # For each k-slot, find tokens that chose this expert
            for k in range(K):
                token_mask = (idx_flat[:, k] == expert_id)  # [N] bool
                token_indices = token_mask.nonzero(as_tuple=False).squeeze(1)

                if token_indices.numel() == 0:
                    continue

                # Enforce capacity: truncate if overflow
                if token_indices.numel() > capacity:
                    token_indices = token_indices[:capacity]

                expert_input = x_flat[token_indices]                   # [C', D]
                expert_output = expert(expert_input)                   # [C', D]
                weights = w_flat[token_indices, k].unsqueeze(-1)       # [C', 1]
                output_flat.index_add_(0, token_indices, expert_output * weights)

        output = output_flat.view(B, T, D)
        # Residual: tokens that received no expert output retain their input
        return output + x, balance_loss
```

This implementation is production-valid for single-device training. It correctly handles capacity enforcement, re-normalized Top-K weights, and the balance loss formulation. For multi-device Expert Parallelism, the dispatch and combine steps are replaced with `torch.distributed.all_to_all` calls over the token dimension, which is examined in Lesson 4.

---

## 3. High-Performance Optimization & Failure Modes

### Routing Stability and the Cold-Start Problem

Routing instability manifests in two distinct phases of training, and they require different interventions. The first is the cold-start instability in early training, when router weights are near-random. With random gates, token assignments fluctuate wildly across batches, which means experts receive inconsistent token distributions and their weights receive inconsistent gradient directions. The network is trying to specialize experts and train a router that exploits that specialization simultaneously, but neither can proceed until the other provides a stable signal. This is a chicken-and-egg problem.

The standard solution is **router warm-up**: for the first several thousand steps, either use a uniform softmax temperature (high temperature flattens the distribution, reducing sensitivity to random initial perturbations) or disable the top-K mask and train with full soft routing before transitioning to sparse. Mesh TensorFlow experiments from the Switch Transformer paper suggest that a linear schedule from temperature $\tau = 10$ down to $\tau = 1$ over the first 1% of training steps resolves most cold-start instability without requiring architectural changes. Some practitioners instead apply a linear schedule on the balance loss coefficient, starting at $10\alpha$ and annealing to $\alpha$ over the warm-up period, which has the same stabilizing effect through a different mechanism.

A second form of instability appears in mid-to-late training: **routing oscillation**, where a token's routing assignment flips between two experts at alternating gradient steps. This occurs when the router logits for two experts are close in value and the balance loss gradient is pushing load away from one, nudging the other into first place, which then receives more tokens and triggers the balance loss in the other direction. The result is a persistent cycle where neither expert accumulates a consistent training distribution. Detecting oscillation requires logging the token-level routing decisions across consecutive steps and computing a routing consistency metric:

```python
import torch

def routing_consistency(
    indices_t0: torch.Tensor,   # [B, T] top-1 assignments at step t
    indices_t1: torch.Tensor,   # [B, T] top-1 assignments at step t+1
) -> float:
    """
    Fraction of tokens that route to the same expert on consecutive steps.
    Values below ~0.85 in mid-training suggest routing oscillation.
    """
    agreement = (indices_t0 == indices_t1).float()
    return agreement.mean().item()
```

Values below approximately 0.85 for a well-trained router at mid-training signal oscillation. Mitigations include reducing $\alpha$, increasing the router's learning rate warm-up, or applying a router-specific gradient clipping value tighter than the global clip norm.

### Expert Collapse and Its Diagnostic Signature

Expert collapse—the routing rich-get-richer failure described earlier—produces a characteristic diagnostic signature in training logs. The effective number of experts, computed as the exponential of the routing entropy $H = -\sum_i f_i \log f_i$, should remain close to $E$ throughout training if routing is healthy. When collapse is occurring, this quantity drops sharply, often reaching an effective expert count of 2–3 out of 16 or 32 actual experts, within the first few thousand steps.

```python
import torch
import math

def effective_expert_count(
    router_probs: torch.Tensor,   # [B, T, E] full softmax distribution
) -> float:
    """
    Computes exp(H(f)) where f_i is the mean router probability for expert i.
    Equals E when routing is perfectly uniform; approaches 1.0 under collapse.
    """
    f = router_probs.mean(dim=[0, 1])               # [E]
    f = f.clamp(min=1e-9)
    entropy = -(f * f.log()).sum()
    return math.exp(entropy.item())
```

Log this metric every N steps and alert when it falls below $0.5 \times E$. At that point, the most reliable recovery—short of restarting training—is to reinitialize the router weights from a small-scale Gaussian and reduce the task loss learning rate temporarily so that the router warm-up procedure can stabilize the assignments before the expert weights drift further from a recoverable initialization.

### Token Dropping and Its Quality Impact

Token dropping—the silent loss of tokens that overflow expert capacity—is one of the more insidious failure modes because it rarely raises an error and its quality impact accumulates gradually. In an autoregressive decoder, a dropped token at position $t$ means the model produces a zero vector in place of a computed representation, which propagates corrupted context through the subsequent self-attention layers. The severity depends on the drop rate: empirical results from Switch Transformer and GShard suggest that up to 10–15% token dropping causes only marginal perplexity degradation, but above 20% the effect becomes significant.

Monitoring drop rate requires instrumenting the dispatch step:

```python
import torch

def compute_drop_rate(
    topk_indices: torch.Tensor,  # [B, T, K]
    capacity: int,
    num_experts: int,
) -> float:
    """
    Fraction of (token, expert) routing assignments that would be dropped
    due to expert buffer overflow given the specified capacity.
    """
    B, T, K = topk_indices.shape
    N = B * T
    total_assignments = N * K
    dropped = 0

    idx_flat = topk_indices.view(N, K)
    for e in range(num_experts):
        for k in range(K):
            count = (idx_flat[:, k] == e).sum().item()
            overflow = max(0, count - capacity)
            dropped += overflow

    return dropped / total_assignments
```

If the observed drop rate exceeds 10% at a given capacity factor, the correct intervention is to increase the capacity factor rather than the balance loss coefficient. Increasing the balance loss to reduce drops creates a subtler problem: the routing becomes artificially uniform, experts lose their specialization, and you have effectively degraded the architecture to a noisy dense FFN with extra overhead.

### Interaction Between Routing and Optimizer State

An underappreciated failure mode arises from the interaction between routing decisions and the optimizer's first- and second-moment estimates. Adam and AdamW maintain per-parameter momentum statistics that are updated on every step regardless of whether the parameter received a meaningful gradient. For expert parameters, this assumption breaks down: an expert that is rarely selected accumulates stale momentum that reflects its gradient history from the last time it was significantly routed to, which may have been thousands of steps earlier. When the routing suddenly shifts and that expert receives many tokens, the stale momentum vectors pull its weights in directions that are no longer meaningful, causing a transient degradation in loss.

The fix is to implement **expert-specific gradient zeroing**: when an expert's effective token count falls below a threshold (e.g., 10% of its expected load), zero its gradient rather than applying it. This prevents the optimizer from accumulating momentum from degenerate gradient estimates:

```python
def zero_underloaded_expert_gradients(
    experts: torch.nn.ModuleList,
    expert_load_fractions: torch.Tensor,  # [E] fraction of capacity used
    threshold: float = 0.10,
) -> None:
    """
    Zero gradients for experts whose load falls below `threshold` of
    their expected allocation. Prevents stale optimizer momentum accumulation.
    """
    for i, expert in enumerate(experts):
        if expert_load_fractions[i].item() < threshold:
            for param in expert.parameters():
                if param.grad is not None:
                    param.grad.zero_()
```

Call this function after the backward pass and before the optimizer step. It is not a substitute for load balancing—underloaded experts should be addressed by improving the routing policy—but it prevents a secondary failure mode from compounding the primary one.

### Scaling the Router at Inference

At inference, the router must be fast enough that it does not become the latency bottleneck in a system designed around the premise that sparse computation is cheaper than dense computation. The gate projection is $O(D \times E)$, which at large scale (say, $D = 4096$, $E = 64$) is a $4096 \times 64 = 262{,}144$-parameter matrix-vector product per token. This is small compared to the expert FFN, but under autoregressive generation with batch size one, every FLOP counts.

Several inference-time optimizations are effective. First, the top-K selection over $E$ logits at $K \ll E$ can use a partial sort (nth_element in C++) rather than a full sort, reducing selection from $O(E \log E)$ to $O(E)$ on average. Second, for systems where routing decisions are consistent across positions of the same token type (as observed empirically in well-trained models), caching the routing decision for the KV-cache-reused prefix eliminates redundant gate computations for prefill tokens. Third, kernel fusion—merging the gate linear, softmax, top-K select, and dispatch index generation into a single CUDA kernel—eliminates multiple round-trips through GPU global memory and can reduce routing latency by 3–4x on V100/A100 hardware.

The routing mechanism is the intelligence that makes sparse computation possible and the fragility that makes it difficult. Understanding it at the level of gradient flow, optimizer dynamics, and dispatch mechanics—not just the high-level formula—is the prerequisite for building MoE systems that deliver their theoretical efficiency in practice. The next lesson applies this understanding to the distributed execution layer: how expert parallelism, all-to-all communication, and device topology interact to determine whether the latency and throughput projections derived from FLOP counts ever materialize in wall-clock time.
