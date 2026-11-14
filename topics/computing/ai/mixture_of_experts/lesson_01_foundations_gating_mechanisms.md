# Lesson 1: Foundations of Sparse Expert Systems

## 1. First-Principles Intuition & Invariants

The central tension in deep learning has never been expressiveness — it has been compute. A sufficiently wide, sufficiently deep network can approximate any function. The question practitioners have wrestled with since the first multilayer perceptrons is not *whether* a model can represent a target distribution, but whether the cost of *evaluating* that representation is acceptable at training time, at inference time, and at the scale of data required to make the representation useful.

Dense neural networks resolve this tension by ignoring it. Every parameter participates in every forward pass. A transformer block with 7 billion parameters consumes every one of those parameters when it processes the word "the" and equally when it processes a fragment of Python source code or a snippet of Mandarin poetry. The model learns specialization through its weights, but the *execution* of the model is resolutely non-specialized. This is simultaneously the great strength of dense models — training signal flows through every parameter on every example — and their fundamental inefficiency.

Mixture of Experts (MoE) architectures dissolve this coupling. They assert that a model's total parameter count and its per-token floating-point cost need not be the same quantity. The core invariant is elegant: partition the model's capacity into a collection of independent subnetworks called experts, then learn a routing function that activates only a small subset of those experts for any given input. The model acquires the representational capacity of its full expert population, but pays the computational cost of only the activated subset. This is *conditional computation* — the graph of executed operations is a function of the input, not a static property of the architecture.

The intellectual lineage of this idea is longer than the recent literature suggests. Jacobs, Jordan, Nowlan, and Hinton introduced the original Mixture of Experts model in 1991, framing it explicitly as a system in which different experts compete to handle different regions of the input space, mediated by a gating network that learns the partition. Their formulation was probabilistic: the gating network produced a full distribution over experts, and the final output was a weighted sum of all expert outputs. This is a *soft* mixture, and it is not sparse — every expert contributes to every prediction, weighted by the gate. The computational saving is zero; the benefit is purely in the inductive bias that encourages specialization.

The leap to *sparse* conditional computation came much later, formalized at scale by Shazeer and colleagues in the 2017 paper "Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer." The key modification was surgical: replace the soft-sum over all experts with a hard top-$k$ selection. If the gating network emits scores over $E$ experts and you retain only $k = 2$, then $E - 2$ experts receive exactly zero gradient and zero compute for that token. The forward pass now has a data-dependent execution graph, and the memory and FLOP profile of a single forward pass is decoupled from the total model size in a concrete, measurable way.

To understand why this matters at the scale modern infrastructure operates at, consider the arithmetic. A dense feed-forward sublayer in a transformer with hidden dimension $d_{model} = 4096$ and expansion ratio 4 performs approximately $2 \times 4096 \times 16384 = 134$ million multiply-add operations per token. Replace that layer with 64 experts of the same individual size and activate $k = 2$ of them: the per-token cost of the FFN is unchanged, but the total FFN parameter count has grown by a factor of 64, from roughly 134M to 8.6B parameters in that layer alone. The model's *capacity* scaled by 64×; the *cost* scaled by 1×. This asymmetry is the founding invariant of sparse expert systems, and every design decision in MoE engineering flows from it.

Three invariants deserve to be stated explicitly before the architecture is dissected, because violating any one of them produces either a model that fails to train or one that fails to deploy.

The first invariant is **load balance**. If the gating network is free to route all tokens to the same two experts, it will. The loss surface rewards expert quality, and nothing in the basic top-$k$ formulation penalizes the routing collapse where one or two experts accumulate all capacity while the remaining $E - k$ experts atrophy through lack of gradient signal. A sparse MoE without an explicit load-balancing mechanism degenerates to an expensive dense model with $k$ active subnetworks and $E - k$ dead parameters.

The second invariant is **expert capacity**. Because tokens arrive in batches and routing is determined per-token, the number of tokens assigned to any expert is a random variable. Hardware requires static memory allocation. The engineering resolution is the *capacity factor*: each expert is allocated a fixed buffer of $C = \lceil \alpha \cdot T / E \rceil$ token slots per batch, where $T$ is the batch token count, $E$ is the number of experts, and $\alpha \geq 1$ is the capacity factor. Tokens routed to an expert that has filled its buffer are dropped. This introduces a tradeoff between memory overhead (larger $\alpha$) and token drop rate (smaller $\alpha$), and the dropped-token rate is a critical training metric that must be monitored continuously.

The third invariant is **routing differentiability**. Top-$k$ selection is not differentiable at the selection boundary. The gradient of the gating scores is defined for the selected experts but undefined for the routing decision itself. Every practical sparse MoE architecture must resolve this: either by using the continuous gating scores as multiplicative weights on the expert outputs (preserving gradient flow into the gate), by using straight-through estimators, or by reformulating routing as a relaxed optimization. The choices made here have profound implications for training stability and expert utilization.

---

## 2. Core Architecture & Mechanics

A sparse MoE transformer replaces every other feed-forward sublayer (or in some designs, every FFN sublayer) with a MoE layer. The surrounding architecture — multi-head attention, layer normalization, residual connections — is unmodified. This modularity is deliberate and significant: it means sparse MoE is not a different kind of model, it is a *drop-in capacity amplifier* for the transformer FFN.

The anatomy of a single MoE layer has three functional components: the gating network, the expert pool, and the dispatch/combine mechanism. Understanding each requires following a token's journey from layer input to layer output.

```
 Layer Input  x  ∈  R^[T × d_model]
        │
        ▼
 ┌──────────────────────────────────────────────────────┐
 │               GATING NETWORK                         │
 │   G(x) = Softmax( TopK( x·W_g + ε, k ) )            │
 │   W_g  ∈  R^[d_model × E]                           │
 │   Output: scores S ∈ R^[T × k],                     │
 │           indices I ∈ Z^[T × k]                     │
 └──────────────────────────────────────────────────────┘
        │  S, I
        ▼
 ┌──────────────────────────────────────────────────────┐
 │               DISPATCH (Scatter)                     │
 │   For each expert e: collect tokens where I[t,·] = e │
 │   Respect capacity buffer C per expert               │
 │   Drop overflow tokens                               │
 └──────────────────────────────────────────────────────┘
        │  per-expert token batches
        ▼
 ┌────────────┐  ┌────────────┐      ┌────────────┐
 │  Expert 0  │  │  Expert 1  │ ...  │  Expert E-1│
 │  FFN(x)    │  │  FFN(x)    │      │  FFN(x)    │
 │  W1,W2 ∈  │  │  W1,W2 ∈  │      │  W1,W2 ∈  │
 │R^[d×d_ff] │  │R^[d×d_ff] │      │R^[d×d_ff] │
 └────────────┘  └────────────┘      └────────────┘
        │  per-expert outputs
        ▼
 ┌──────────────────────────────────────────────────────┐
 │               COMBINE (Gather + Weighted Sum)        │
 │   y[t] = Σ_{j=0}^{k-1} S[t,j] · Expert_I[t,j](x[t])│
 └──────────────────────────────────────────────────────┘
        │
        ▼
 Layer Output  y  ∈  R^[T × d_model]  (+residual)
```

### The Gating Network

The gating network is a linear projection from token representation space to expert score space, $W_g \in \mathbb{R}^{d_{model} \times E}$, followed by a top-$k$ masking operation and softmax renormalization over the selected scores. In PyTorch, the core mechanics are:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Tuple

@dataclass
class MoEConfig:
    d_model: int = 1024
    d_ff: int = 4096
    n_experts: int = 64
    top_k: int = 2
    capacity_factor: float = 1.25
    noise_std: float = 1e-2
    aux_loss_coef: float = 1e-2


class TopKGate(nn.Module):
    """
    Sparse top-k gating network as formulated in Shazeer et al. (2017).
    Applies additive Gaussian noise during training to encourage exploration,
    then selects the top-k experts by logit score.
    """

    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.cfg = cfg
        # Linear projection: d_model -> n_experts (no bias, following ST-MoE convention)
        self.w_gate = nn.Linear(cfg.d_model, cfg.n_experts, bias=False)

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            x: Token representations, shape [T, d_model].
        Returns:
            gates:   Sparse gate weights,     shape [T, n_experts].
            indices: Top-k expert indices,    shape [T, top_k].
            scores:  Top-k renormalized scores shape [T, top_k].
        """
        T, _ = x.shape
        cfg = self.cfg

        # Raw logits
        logits = self.w_gate(x)  # [T, E]

        # Additive noise during training: encourages uniform load distribution
        # by perturbing logits before top-k selection.
        if self.training:
            noise = torch.randn_like(logits) * cfg.noise_std
            logits = logits + noise

        # Top-k selection: retain only the k highest logits per token
        top_k_logits, top_k_indices = torch.topk(logits, cfg.top_k, dim=-1)  # [T, k]

        # Renormalize selected scores via softmax so they sum to 1 per token
        top_k_scores = F.softmax(top_k_logits, dim=-1)  # [T, k]

        # Build a sparse [T, E] gate tensor for the combine step
        gates = torch.zeros_like(logits)  # [T, E]
        gates.scatter_(-1, top_k_indices, top_k_scores)

        return gates, top_k_indices, top_k_scores
```

The additive Gaussian noise before top-$k$ selection is not cosmetic. During early training the gating network has no preference signal, so logits are nearly uniform. Without noise, identical logits produce a deterministic tie-breaking that depends on hardware implementation details, and the resulting routing is essentially fixed for the first few hundred steps. The noise breaks this symmetry and introduces enough stochasticity to give all experts initial exposure, which seeds the specialization process. As training progresses and the gate weights acquire meaningful signal, the noise becomes relatively small and its effect fades.

### The Expert Pool

Each expert is structurally identical to a standard transformer FFN: a two-layer MLP with a nonlinearity between them. In a model using SwiGLU activation (as in LLaMA-style transformers), each expert has three weight matrices rather than two. The key implementation requirement is that all experts be computed in parallel, not sequentially. The dispatch mechanism groups tokens by their assigned expert, then each expert processes its assigned batch as a single matrix multiplication.

```python
class Expert(nn.Module):
    """
    Single FFN expert with SwiGLU activation.
    Uses the standard 2/3 * 4 * d_model intermediate dimension
    convention for SwiGLU to match parameter count with ReLU 4x expansion.
    """

    def __init__(self, cfg: MoEConfig):
        super().__init__()
        # For SwiGLU: d_ff should be 2/3 * expansion to maintain FLOP parity
        self.w_gate_proj = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.w_up_proj   = nn.Linear(cfg.d_model, cfg.d_ff, bias=False)
        self.w_down_proj = nn.Linear(cfg.d_ff,    cfg.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [n_tokens_for_this_expert, d_model]
        gate = F.silu(self.w_gate_proj(x))
        up   = self.w_up_proj(x)
        return self.w_down_proj(gate * up)
```

### Dispatch, Capacity Enforcement, and Combine

The dispatch and combine steps are where sparse MoE crosses from linear algebra into systems engineering. The capacity constraint requires that each expert process at most $C = \lceil \alpha \cdot T / E \rceil$ tokens. When more tokens are routed to an expert than its buffer allows, the overflow tokens are dropped: they pass through the layer unchanged (or are zeroed out, depending on the implementation). The routing priority among competing tokens is typically determined by their gating score — higher-scoring tokens are admitted first, lower-scoring ones are dropped.

```python
class SparseMoELayer(nn.Module):
    """
    Complete sparse MoE FFN replacement layer.
    Implements capacity-constrained dispatch with top-k gating.
    """

    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.cfg = cfg
        self.gate = TopKGate(cfg)
        self.experts = nn.ModuleList([Expert(cfg) for _ in range(cfg.n_experts)])

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: [T, d_model] — sequence of token representations.
        Returns:
            output:   [T, d_model] — MoE layer output.
            aux_loss: scalar       — load-balancing auxiliary loss.
        """
        T, d = x.shape
        cfg = self.cfg
        E = cfg.n_experts
        C = int(cfg.capacity_factor * T / E) + 1  # capacity per expert

        gates, indices, scores = self.gate(x)  # [T,E], [T,k], [T,k]

        # Compute auxiliary load-balancing loss before capacity masking,
        # using the full (pre-drop) routing distribution.
        aux_loss = self._auxiliary_loss(gates)

        # output buffer: accumulates weighted expert outputs per token
        output = torch.zeros_like(x)

        # Per-expert token counter for capacity enforcement
        expert_counts = torch.zeros(E, dtype=torch.long, device=x.device)

        for k_idx in range(cfg.top_k):
            expert_idx = indices[:, k_idx]    # [T] — which expert for this k slot
            token_scores = scores[:, k_idx]   # [T] — weight for this k slot

            for e in range(E):
                # Mask: tokens routed to expert e at this k position
                token_mask = (expert_idx == e).nonzero(as_tuple=False).squeeze(-1)
                if token_mask.numel() == 0:
                    continue

                # Sort by descending score to prioritize high-confidence tokens
                priority_scores = token_scores[token_mask]
                sorted_order = torch.argsort(priority_scores, descending=True)
                token_mask = token_mask[sorted_order]

                # Enforce capacity: drop tokens exceeding the buffer
                capacity_remaining = C - expert_counts[e].item()
                if capacity_remaining <= 0:
                    continue
                admitted = token_mask[:capacity_remaining]
                expert_counts[e] += admitted.numel()

                # Compute expert output for admitted tokens
                expert_out = self.experts[e](x[admitted])  # [n_admitted, d]

                # Accumulate weighted output
                output[admitted] += (
                    token_scores[admitted].unsqueeze(-1) * expert_out
                )

        return output, aux_loss

    def _auxiliary_loss(self, gates: torch.Tensor) -> torch.Tensor:
        """
        Switch Transformer auxiliary loss (Fedus et al., 2021).
        Minimizes the dot product of expert fraction and expert routing probability,
        driving the router toward uniform load.
        """
        E = self.cfg.n_experts
        # f_i: fraction of tokens dispatched to expert i  [E]
        expert_mask = (gates > 0).float()
        f = expert_mask.mean(dim=0)                 # [E]
        # P_i: mean routing probability for expert i across tokens  [E]
        P = gates.mean(dim=0)                       # [E]
        # Loss = E * sum(f_i * P_i), scaled by E so target is 1.0
        return E * torch.dot(f, P)
```

The nested Python loop over experts is correct but pedagogically simplified. Production implementations replace this loop with a single batched `torch.einsum` or a custom CUDA kernel that uses the one-hot expert assignment tensor to perform grouped matrix multiplications in one pass, achieving orders-of-magnitude better hardware utilization. The key primitive in frameworks like Megatron-LM and Tutel is `all_to_all` communication (in distributed settings) combined with `segment_reduce` for the grouped GEMM. The loop above correctly captures the semantics; Section 3 addresses the performance-correct implementation.

### Load Balancing in Depth

The auxiliary loss shown above follows the Switch Transformer formulation from Fedus, Zoph, and Shazeer (2021). Its derivation deserves careful examination because understanding it is prerequisite to tuning it. Let $f_i$ be the fraction of tokens in a batch routed to expert $i$, and let $P_i$ be the mean softmax probability assigned to expert $i$ across all tokens. Perfect balance means $f_i = P_i = 1/E$ for all $i$. The loss $\mathcal{L}_{aux} = E \cdot \sum_{i=1}^{E} f_i \cdot P_i$ is minimized when this product is minimized for all pairs simultaneously, which occurs at the uniform distribution. The factor of $E$ normalizes the loss so that its value at perfect balance is $1.0$ regardless of $E$, making the coefficient $\lambda_{aux}$ interpretable across model scales.

The critical subtlety is that $f_i$ is not differentiable — it involves the hard routing decision (argmax/top-k). The gradient of $\mathcal{L}_{aux}$ flows only through $P_i$, which depends on the softmax output of the gate. This means the auxiliary loss teaches the gate's weight matrix $W_g$ to produce more uniform probabilities, which indirectly encourages uniform routing, but the gradient does not directly penalize the routing decisions themselves. This indirect coupling is why the coefficient $\lambda_{aux}$ must be tuned carefully: too small and load collapses; too large and the auxiliary loss dominates the task loss, forcing uniform routing that destroys expert specialization.

```
Expert Load Distribution (ideal vs. collapsed)

Ideal (uniform):
Expert:  0   1   2   3   4   5   6   7
Load:  ■■■ ■■■ ■■■ ■■■ ■■■ ■■■ ■■■ ■■■
         12% 13% 12% 13% 12% 12% 13% 13%

Collapsed (aux_loss_coef too small):
Expert:  0   1   2   3   4   5   6   7
Load:  ░░░ ■■■ ░░░ ░░░ ■■■■■░░░ ░░░ ░░░
          2%  38%  1%  2%  51%  2%  2%  2%

Dead experts (no gradient, no specialization):
         ^^^                      ^^^
```

An alternative load-balancing strategy, used in models like GShard and later in Mixtral, is the **auxiliary-free** or **expert-choice** routing paradigm. Rather than having each token select its top-$k$ experts, each expert selects its top-$C$ tokens from the batch. This mechanically guarantees perfect load balance — every expert processes exactly $C$ tokens — at the cost of two changes in semantics: tokens are no longer guaranteed to be processed by any expert (some may be selected by zero experts), and the assignment is batch-global rather than token-local, which complicates autoregressive inference. Expert-choice routing is therefore more common in encoder or training-only contexts than in decoder inference pipelines.

---

## 3. High-Performance Optimization & Failure Modes

### From Correct to Fast: The Grouped GEMM Problem

The reference implementation above is semantically correct but computationally catastrophic at production scale. The problem is serialization: processing each expert sequentially with a Python loop means the GPU sits idle waiting for each small matrix multiplication to complete before beginning the next. Modern accelerators achieve high utilization through large, contiguous matrix operations. A sequence of small GEMMs (each of size $[n_{admitted}, d_{ff}]$ where $n_{admitted} \ll T$) has extremely poor hardware utilization because the GEMM kernels spend most of their time in overhead rather than arithmetic.

The production solution is a *grouped GEMM* (also called a batched GEMM with variable-size segments or a "megakernel"). All tokens are sorted by their assigned expert, producing a contiguous layout in memory, and then a single kernel processes all expert computations in parallel. The routing indices are transformed into a permutation matrix and segment boundaries, and the expert weight matrices are stacked into a 3D tensor enabling batched matrix multiplication.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

def permute_tokens(
    x: torch.Tensor,
    expert_indices: torch.Tensor,
    n_experts: int,
    capacity: int,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Sort tokens by their primary expert assignment to produce
    a contiguous layout for grouped GEMM.

    Args:
        x:              [T, d_model]
        expert_indices: [T, top_k]  — expert assignment per token per k slot
        n_experts:      E
        capacity:       C per expert

    Returns:
        permuted_x:     [E * C, d_model] — tokens sorted by expert, padded to capacity
        expert_counts:  [E]              — actual token count per expert (pre-padding)
        unpermute_idx:  [T, top_k]       — inverse permutation to restore output ordering
    """
    T, top_k = expert_indices.shape
    device = x.device

    # Flatten [T, k] -> [T*k] assignments and track source (token, k_slot) pairs
    flat_indices = expert_indices.reshape(-1)        # [T*k]
    token_ids    = torch.arange(T, device=device).unsqueeze(1).expand(T, top_k).reshape(-1)

    # Sort by expert assignment to group tokens for each expert
    sort_order = torch.argsort(flat_indices, stable=True)
    sorted_experts = flat_indices[sort_order]
    sorted_tokens  = token_ids[sort_order]

    # Count tokens per expert (before capacity clipping)
    expert_counts = torch.bincount(sorted_experts, minlength=n_experts)  # [E]

    # Build permuted input: [E * C, d_model], zero-padded for under-capacity experts
    permuted_x = torch.zeros(n_experts * capacity, x.shape[-1], device=device, dtype=x.dtype)

    for e in range(n_experts):
        count = min(expert_counts[e].item(), capacity)
        if count == 0:
            continue
        # Tokens assigned to expert e in sorted order
        start = (sorted_experts == e).nonzero(as_tuple=False)[0].item()
        src_tokens = sorted_tokens[start : start + count]
        permuted_x[e * capacity : e * capacity + count] = x[src_tokens]

    # Build inverse permutation index for the combine (unpermute) step
    unpermute_idx = torch.full((T, top_k), -1, dtype=torch.long, device=device)
    for e in range(n_experts):
        count = min(expert_counts[e].item(), capacity)
        start = (sorted_experts == e).nonzero(as_tuple=False)[0].item() if expert_counts[e] > 0 else 0
        for local_i in range(count):
            global_flat_i = sort_order[start + local_i].item()
            orig_token = global_flat_i // top_k
            orig_k     = global_flat_i  % top_k
            unpermute_idx[orig_token, orig_k] = e * capacity + local_i

    return permuted_x, expert_counts, unpermute_idx


class EfficientMoELayer(nn.Module):
    """
    MoE layer using stacked expert weights for a single batched GEMM.
    Exploits torch.bmm on a [E, C, d_model] input tensor.
    """

    def __init__(self, cfg: MoEConfig):
        super().__init__()
        self.cfg = cfg
        self.gate = TopKGate(cfg)
        E, d, ff = cfg.n_experts, cfg.d_model, cfg.d_ff

        # Stack all expert weights into 3D tensors for batched matmul:
        # w1: [E, d_model, d_ff], w2: [E, d_ff, d_model]
        self.w1 = nn.Parameter(torch.empty(E, d, ff))
        self.w2 = nn.Parameter(torch.empty(E, ff, d))
        nn.init.kaiming_uniform_(self.w1, a=0.0, mode='fan_in', nonlinearity='relu')
        nn.init.kaiming_uniform_(self.w2, a=0.0, mode='fan_in', nonlinearity='relu')

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        T, d = x.shape
        cfg  = self.cfg
        E, k = cfg.n_experts, cfg.top_k
        C    = int(cfg.capacity_factor * T / E) + 1

        gates, indices, scores = self.gate(x)
        aux_loss = self._auxiliary_loss(gates)

        # Permute tokens into [E, C, d_model] layout
        permuted_x, expert_counts, unpermute_idx = permute_tokens(x, indices, E, C)
        # Reshape for batched GEMM: [E, C, d_model]
        px = permuted_x.reshape(E, C, d)

        # First projection: [E, C, d_model] x [E, d_model, d_ff] -> [E, C, d_ff]
        h = torch.bmm(px, self.w1)
        h = F.relu(h)

        # Second projection: [E, C, d_ff] x [E, d_ff, d_model] -> [E, C, d_model]
        expert_out = torch.bmm(h, self.w2)   # [E, C, d_model]
        expert_out_flat = expert_out.reshape(E * C, d)

        # Combine: scatter expert outputs back to original token positions
        output = torch.zeros(T, d, device=x.device, dtype=x.dtype)
        for t in range(T):
            for ki in range(k):
                src_idx = unpermute_idx[t, ki].item()
                if src_idx >= 0:
                    output[t] += scores[t, ki] * expert_out_flat[src_idx]

        return output, aux_loss

    def _auxiliary_loss(self, gates: torch.Tensor) -> torch.Tensor:
        E = self.cfg.n_experts
        f = (gates > 0).float().mean(dim=0)
        P = gates.mean(dim=0)
        return E * torch.dot(f, P)
```

The `torch.bmm` on the stacked `[E, C, d_model]` tensor issues a single CUDA kernel that processes all expert computations in parallel. The critical requirement is that the input tensor be contiguous in the expert dimension, which the permutation step ensures. In practice, production frameworks like Tutel, DeepSpeed-MoE, and Megatron-Core replace the Python-level permutation loop with a custom CUDA kernel that performs the scatter/gather in a single pass, eliminating the last Python-level bottleneck.

### Distributed Expert Parallelism

A MoE model with 64 experts and 2 activated per token has 32× more parameters than its dense FFN equivalent. At the scale of a 70B-parameter dense model, the equivalent MoE might have 1.5 trillion parameters in its expert layers. This exceeds single-node memory by several orders of magnitude, requiring a parallelism strategy specific to the MoE structure.

The standard approach is **Expert Parallelism (EP)**, where the $E$ experts are sharded across $P$ devices such that each device holds $E / P$ experts. All devices hold identical copies of the non-expert layers (attention, layer norm, embeddings). The forward pass proceeds in four phases: local attention (all devices process their token shard), `all_to_all` communication (each device sends its tokens to the device hosting the target expert), local expert computation (each device processes the tokens it received), and a second `all_to_all` communication (expert outputs are returned to the originating devices). This `all_to_all` collective is the dominant communication bottleneck and must be overlapped with computation where possible.

```
Distributed Expert Parallelism (4 devices, 8 experts, top-2)

Device 0: [E0, E1]       Device 1: [E2, E3]
Device 2: [E4, E5]       Device 3: [E6, E7]

Step 1: Each device runs attention on its local token shard.
        Device 0 tokens: t0, t1, t2, t3
        Device 1 tokens: t4, t5, t6, t7
        ...

Step 2: Routing: t0 -> (E3, E5), t1 -> (E0, E6), ...

Step 3: all_to_all — tokens cross device boundaries to reach their experts.
        t0 travels from Device 0 to Devices 1 and 2.
        t1 stays on Device 0 (E0) and travels to Device 3 (E6).

Step 4: Local expert computation on each device.

Step 5: all_to_all — expert outputs return to originating devices.

Step 6: Combine weighted outputs on originating devices.
```

Implementing EP without carefully metering the `all_to_all` volume leads to network saturation. The volume of data exchanged in one `all_to_all` is proportional to $T \cdot d_{model}$, and this occurs *twice per MoE layer* per forward pass. For a 32-layer MoE model with 16 MoE layers, 32 all-to-all collectives execute per forward step. At batch size 1M tokens and $d_{model} = 8192$, each collective moves approximately $1M \times 8192 \times 2$ bytes (bfloat16) ≈ 16 GB of data across the interconnect. InfiniBand HDR at 200 Gbps handles this in roughly 640ms per collective — clearly unacceptable. Production systems achieve tolerable latency through a combination of token drop (reducing volume), careful batch size tuning, and overlapping the two all-to-all phases with local attention computation.

### Critical Failure Modes

**Routing collapse** is the most common and dangerous training failure in sparse MoE. It manifests as one or two experts accumulating 70–90% of all tokens within the first few thousand training steps. By the time the collapse is detectable in validation loss curves, the dead experts have weeks of specialized parameters to unlearn. Early detection requires logging the coefficient of variation (CV) of the per-expert token count at every training step: $CV = \sigma(f_1, \ldots, f_E) / \mu(f_1, \ldots, f_E)$. A healthy MoE has $CV < 0.3$; values above 1.0 indicate severe collapse. The remediation is increasing $\lambda_{aux}$ and optionally warming up the auxiliary loss from 0 during the first few thousand steps to prevent the gate from collapsing before the experts have had time to diverge.

**Expert homogenization** is the inverse problem: with an auxiliary loss coefficient that is too large, all experts converge to nearly identical weight configurations. The model achieves perfect load balance but zero specialization. Measuring expert homogenization requires computing the pairwise cosine similarity between expert weight matrices $W^{(i)}_1$ and $W^{(j)}_1$ periodically during training. A healthy model should show decreasing mean similarity over time; similarity plateau or increase indicates the auxiliary loss is dominating.

```python
def expert_similarity_diagnostic(moe_layer: EfficientMoELayer) -> dict:
    """
    Compute pairwise cosine similarity between expert first-layer weight matrices.
    Returns mean, max, and histogram of similarities.
    Low mean similarity (< 0.3) indicates healthy specialization.
    High mean similarity (> 0.7) indicates homogenization.
    """
    w1 = moe_layer.w1.detach()          # [E, d_model, d_ff]
    E  = w1.shape[0]

    # Flatten each expert's W1 into a vector, then normalize
    w1_flat = w1.reshape(E, -1)                               # [E, d_model * d_ff]
    w1_norm = F.normalize(w1_flat, dim=-1)                    # [E, d_model * d_ff]

    # Pairwise cosine similarity matrix
    sim_matrix = torch.mm(w1_norm, w1_norm.T)                 # [E, E]

    # Extract upper triangle (exclude diagonal)
    upper_tri_mask = torch.triu(torch.ones(E, E, dtype=torch.bool), diagonal=1)
    pairwise_sims  = sim_matrix[upper_tri_mask]

    return {
        "mean_similarity":   pairwise_sims.mean().item(),
        "max_similarity":    pairwise_sims.max().item(),
        "std_similarity":    pairwise_sims.std().item(),
        "n_pairs_above_0p7": (pairwise_sims > 0.7).sum().item(),
    }
```

**Token drop cascade** occurs when the capacity factor is set too low relative to the actual routing distribution variance. If the routing distribution is not perfectly uniform (which it never is in practice), some experts will frequently overflow their buffers. Dropped tokens bypass the MoE layer entirely, so heavily-routed experts produce less output per token of information than they should, and the model compensates by routing even more tokens to those experts in subsequent steps — a feedback loop that worsens the imbalance. The diagnostic is the per-step fraction of dropped tokens: values above 5% produce measurable perplexity degradation; values above 15% typically indicate that the capacity factor or the number of experts needs to be tuned.

**Gradient variance explosion** in the gating network is a subtler failure. Because $W_g$ is updated based on the aggregate routing behavior across the entire batch, its gradients have high variance when the batch size is small or when training data is heterogeneous. The standard mitigation is gradient clipping applied specifically to $W_g$ with a tighter bound than the rest of the model, combined with a lower learning rate on the gate weights. Some implementations use a separate optimizer group for the gate with a reduced learning rate multiplier of 0.1–0.3 relative to the expert weights.

Taken together, these failure modes illustrate that a sparse MoE is not merely a larger model — it is a system with its own stability requirements, monitoring surface, and operational discipline. Building one correctly requires treating the routing network as a first-class component that must be diagnosed and tuned with the same rigor applied to the expert computations themselves. The reward for getting it right is a model that scales its capacity with parameter count while holding its compute cost constant: the defining asymmetry that makes sparse expert architectures one of the most consequential structural innovations in modern deep learning.
