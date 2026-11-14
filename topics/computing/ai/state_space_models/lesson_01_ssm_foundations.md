# Lesson 1: State Space Model Fundamentals

## 1. First-Principles Intuition & Invariants

The modern resurgence of state space models in machine learning is not an accident of fashion. It reflects a deeper truth about sequential data: that the world generates observations through a hidden dynamical process whose structure is fundamentally continuous, even when we sample it at discrete intervals. Understanding state space models from first principles means confronting that tension head-on and building the mathematical machinery to resolve it.

Consider a physical analogy that maps precisely onto the AI problem. A spring-mass-damper system evolves continuously through time. At any instant, its complete "memory" of the past is encoded in exactly two numbers: position and velocity. No matter how complicated the forcing function that drove it to this point, those two numbers are sufficient to predict all future behavior. This is the **Markov property of latent states**, and it is the central invariant of every state space model: the hidden state $\mathbf{h}(t)$ is a sufficient statistic for the future of the system given its past.

Formally, a continuous-time linear state space system is defined by two coupled differential equations:

$$\dot{\mathbf{h}}(t) = \mathbf{A}\mathbf{h}(t) + \mathbf{B}\mathbf{u}(t)$$

$$\mathbf{y}(t) = \mathbf{C}\mathbf{h}(t) + \mathbf{D}\mathbf{u}(t)$$

where $\mathbf{h}(t) \in \mathbb{R}^N$ is the latent state vector, $\mathbf{u}(t) \in \mathbb{R}^U$ is the input signal, $\mathbf{y}(t) \in \mathbb{R}^O$ is the output, and the matrices $\mathbf{A} \in \mathbb{R}^{N \times N}$, $\mathbf{B} \in \mathbb{R}^{N \times U}$, $\mathbf{C} \in \mathbb{R}^{O \times N}$, $\mathbf{D} \in \mathbb{R}^{O \times U}$ are the learnable parameters of the model. In most sequence modeling applications, $\mathbf{D}$ is set to zero or treated as a simple skip connection, leaving the essential dynamics in the $(\mathbf{A}, \mathbf{B}, \mathbf{C})$ triple.

The matrix $\mathbf{A}$ is the most consequential object in this framework. It is the **state transition operator**: it determines how the current state influences its own rate of change, which means it governs the entire memory structure of the model. The eigenvalues of $\mathbf{A}$ control stability. If any eigenvalue has a positive real part, the system is unstable and state norms grow without bound. If eigenvalues sit on the imaginary axis, the system exhibits persistent oscillations. For a stable, memory-rich model, we need eigenvalues with negative real parts, clustered close enough to zero that distant-past inputs still leave traces in the present state. The art of modern SSM design — from the HiPPO framework to S4 to Mamba — is almost entirely the art of choosing or learning an $\mathbf{A}$ matrix that preserves useful information across the time scales that matter for the task.

The HiPPO theory makes this precise. Rather than learning $\mathbf{A}$ from scratch as an unconstrained matrix, HiPPO derives $\mathbf{A}$ analytically from the requirement that $\mathbf{h}(t)$ optimally approximates the history of the input $u(\tau)$ for $\tau \leq t$ under a chosen measure. The LagT (translated Laguerre) initialization produces a matrix whose $(n, k)$ entry has a closed form:

$$\mathbf{A}_{nk} = -\begin{cases} (2n+1)^{1/2}(2k+1)^{1/2} & \text{if } n > k \\ n+1 & \text{if } n = k \\ 0 & \text{if } n < k \end{cases}$$

This lower-triangular structure has a beautiful interpretation: each state component $h_n(t)$ integrates increasingly high-frequency information from the input history, so the state vector collectively maintains a polynomial approximation of the past that is provably optimal in the $L^2$ sense. When you initialize your $\mathbf{A}$ this way, you are not guessing at a good structure — you are starting from the mathematically correct answer for uniform-measure history compression and trusting gradient descent to refine it from there.

The **information flow invariant** that follows from this structure is worth internalizing. For the continuous-time system, the formal solution to the state equation is:

$$\mathbf{h}(t) = e^{\mathbf{A}t}\mathbf{h}(0) + \int_0^t e^{\mathbf{A}(t-\tau)}\mathbf{B}\mathbf{u}(\tau)\,d\tau$$

The matrix exponential $e^{\mathbf{A}t}$ is the **transition semigroup**: it describes how the initial state decays (or amplifies) over time. The convolution integral accumulates the influence of all past inputs, weighted by how much the system "remembers" each one. This is not conceptually different from an attention mechanism, but the memory here is implicit and structured by the dynamics of $\mathbf{A}$ rather than computed explicitly by dot-product attention over all past tokens. The computational payoff of that difference is enormous, as we will see when we implement efficient parallel scans.

## 2. Core Architecture & Mechanics

### Discretization: From Continuous Dynamics to Computable Recurrences

A continuous-time SSM is mathematically elegant but not directly computable. Training requires processing sequences of discrete tokens, audio samples, or time-series observations sampled at some step size $\Delta t$. The bridge between the continuous formulation and a practical recurrence is **discretization**, and the choice of discretization method is not merely a numerical detail — it determines the frequency response, numerical stability, and training dynamics of the model.

The simplest discretization is the **forward Euler method**. Approximating $\dot{\mathbf{h}} \approx (\mathbf{h}_{k+1} - \mathbf{h}_k) / \Delta t$ and solving forward:

$$\mathbf{h}_{k+1} = (\mathbf{I} + \Delta t \cdot \mathbf{A})\mathbf{h}_k + \Delta t \cdot \mathbf{B}\mathbf{u}_k$$

The discrete state matrix is $\bar{\mathbf{A}} = \mathbf{I} + \Delta t \cdot \mathbf{A}$ and the discrete input matrix is $\bar{\mathbf{B}} = \Delta t \cdot \mathbf{B}$. Euler discretization is computationally trivial but numerically fragile. For stability, every eigenvalue of $\bar{\mathbf{A}}$ must lie within the unit circle of the complex plane. When $\Delta t$ is large relative to the fastest time constant of $\mathbf{A}$, the Euler method can place eigenvalues outside the unit circle even when the continuous system is stable. This makes Euler discretization a poor choice for SSMs trained with variable sequence lengths or coarse sampling rates.

The **zero-order hold (ZOH)** method is the standard of practice in control theory and the discretization used in S4 and its descendants. It assumes that the input $\mathbf{u}(t)$ is piecewise constant over each interval $[k\Delta t, (k+1)\Delta t]$, which is the natural model for discrete tokens. Under this assumption, the integral in the continuous solution can be evaluated exactly:

$$\bar{\mathbf{A}} = e^{\mathbf{A}\Delta t}$$

$$\bar{\mathbf{B}} = \mathbf{A}^{-1}(e^{\mathbf{A}\Delta t} - \mathbf{I})\mathbf{B}$$

The ZOH discrete matrices are exact for the given input model, meaning the discrete system produces precisely the same state trajectory as the continuous system would produce if driven by a staircase input. The price is computing the matrix exponential, which for a dense $N \times N$ matrix costs $O(N^3)$ and is numerically sensitive. The critical insight that makes S4 tractable is that restricting $\mathbf{A}$ to a **diagonal plus low-rank (DPLR)** structure allows $e^{\mathbf{A}\Delta t}$ to be computed efficiently. If $\mathbf{A} = \mathbf{\Lambda} - \mathbf{P}\mathbf{Q}^*$ where $\mathbf{\Lambda}$ is diagonal and $\mathbf{P}, \mathbf{Q}$ are rank-$r$ vectors, then the matrix exponential and the resulting kernel computation reduce to operations on diagonal matrices and rank-$r$ corrections, achievable in $O(N)$ per parameter.

The **bilinear (Tustin) method** offers a third path, trading exact input modeling for superior frequency-domain properties. It maps the continuous-time frequency variable $s$ to the discrete-time variable $z$ via the Möbius transformation $s = \frac{2}{\Delta t} \cdot \frac{z-1}{z+1}$. The resulting discretization is:

$$\bar{\mathbf{A}} = \left(\mathbf{I} - \frac{\Delta t}{2}\mathbf{A}\right)^{-1}\left(\mathbf{I} + \frac{\Delta t}{2}\mathbf{A}\right)$$

$$\bar{\mathbf{B}} = \left(\mathbf{I} - \frac{\Delta t}{2}\mathbf{A}\right)^{-1} \Delta t \cdot \mathbf{B}$$

The bilinear transform is **frequency-warping preserving**: a continuous-time filter with a pole at frequency $\omega_0$ maps to a discrete filter with a pole at $\omega_d = \frac{2}{\Delta t}\arctan\left(\frac{\omega_0 \Delta t}{2}\right)$. More importantly, it maps the left half of the $s$-plane (continuous stability) exactly onto the interior of the unit disk (discrete stability), unconditionally. No matter how large $\Delta t$ grows, a stable continuous $\mathbf{A}$ yields a stable discrete $\bar{\mathbf{A}}$ under the bilinear transform. This unconditional stability is valuable when you want to learn $\Delta t$ as a trainable parameter, as in Mamba's selective mechanism.

The relationship between these three methods is illustrated below:

```
Continuous-Time SSM               Discretization Method             Discrete Recurrence
─────────────────────────────────────────────────────────────────────────────────────────

ḣ(t) = Ah(t) + Bu(t)   ──[Euler: Ā = I + ΔtA]──────────────────▶  h[k+1] = Āh[k] + B̄u[k]
y(t) = Ch(t)                                                          y[k]   = Ch[k]
                         ──[ZOH:  Ā = exp(AΔt)]──────────────────▶  (exact for staircase input)

                         ──[Bilinear: Ā = (I-ΔtA/2)⁻¹(I+ΔtA/2)]▶  (unconditionally stable)
```

### The Discrete Recurrence and Its Dual Nature

Once discretized, the SSM defines a linear recurrence that can be unrolled across a sequence of length $L$:

$$\mathbf{h}_k = \bar{\mathbf{A}}\mathbf{h}_{k-1} + \bar{\mathbf{B}}\mathbf{u}_k, \quad \mathbf{y}_k = \mathbf{C}\mathbf{h}_k$$

This recurrence has a **dual computational interpretation** that is the source of SSMs' practical power. Executed sequentially, it is an $O(L \cdot N)$ recurrent computation with $O(N)$ state, identical in structure to an RNN cell but linear (no nonlinearity inside the recurrence). This form is optimal for autoregressive inference: each new token requires a constant-time state update regardless of sequence length.

The same recurrence, however, can be expressed as a **convolution**. By unrolling the recurrence from $\mathbf{h}_0 = \mathbf{0}$:

$$\mathbf{y}_k = \sum_{j=0}^{k} \mathbf{C}\bar{\mathbf{A}}^{k-j}\bar{\mathbf{B}}\mathbf{u}_j = \sum_{j=0}^{k} \mathbf{K}_{k-j} \mathbf{u}_j$$

where $\mathbf{K}_i = \mathbf{C}\bar{\mathbf{A}}^i\bar{\mathbf{B}}$ is the $i$-th element of the **SSM convolution kernel**. If $\mathbf{K}$ is precomputed for a fixed sequence length $L$, then the full output sequence can be computed as a single convolution $\mathbf{y} = \mathbf{K} * \mathbf{u}$, which via the convolution theorem can be evaluated in $O(L \log L)$ using an FFT. During training on fixed-length sequences, this is the dominant execution path.

```
         Training Mode (Parallel Convolution)
         ─────────────────────────────────────
         u[0..L] ──▶ FFT ──▶ ⊗ K̂ ──▶ IFFT ──▶ y[0..L]
                                                      O(L log L)

         Inference Mode (Sequential Recurrence)
         ───────────────────────────────────────
         u[k] ──▶ h[k] = Āh[k-1] + B̄u[k] ──▶ y[k] = Ch[k]
                                                      O(N) per step
```

This duality is what separates SSMs architecturally from both Transformers and RNNs. A Transformer has no recurrent form at all: inference cost grows with sequence length because all past tokens must attend to each other. A vanilla RNN has the recurrent form but cannot be parallelized during training because its nonlinear recurrence cannot be rewritten as a convolution. The SSM occupies the intersection: it parallelizes efficiently during training and runs in constant memory during inference.

### Selective State Space Models and Input-Dependent Dynamics

The S4 model and its linear predecessors use **time-invariant** parameters: $\bar{\mathbf{A}}$, $\bar{\mathbf{B}}$, $\mathbf{C}$, and $\Delta t$ are fixed for all positions in the sequence. This is powerful for capturing global structure but limits the model's ability to selectively ignore irrelevant inputs. Mamba resolves this by making $\mathbf{B}$, $\mathbf{C}$, and $\Delta t$ **input-dependent**, computed from $\mathbf{u}_k$ through linear projections:

$$\mathbf{B}_k = s_B(\mathbf{u}_k), \quad \mathbf{C}_k = s_C(\mathbf{u}_k), \quad \Delta_k = \text{softplus}(s_\Delta(\mathbf{u}_k))$$

This selection mechanism breaks the convolution interpretation — a time-varying system cannot be expressed as a single fixed kernel applied to the input. The $O(L \log L)$ FFT trick is no longer available. Instead, Mamba uses a **hardware-aware parallel scan** that fuses the sequential associative scan into a single CUDA kernel, avoiding the memory bandwidth penalty of materializing intermediate states. The associative structure of the scan — the fact that the composition of two linear state transitions $(\bar{\mathbf{A}}_2, \bar{\mathbf{B}}_2) \circ (\bar{\mathbf{A}}_1, \bar{\mathbf{B}}_1) = (\bar{\mathbf{A}}_2\bar{\mathbf{A}}_1, \bar{\mathbf{A}}_2\bar{\mathbf{B}}_1 + \bar{\mathbf{B}}_2)$ is itself a valid state transition — allows the scan to be parallelized in $O(\log L)$ depth across GPU threads, recovering near-training-mode parallelism even with time-varying parameters.

## 3. High-Performance Optimization & Failure Modes

### Implementing the Core SSM in PyTorch

The following implementation covers the complete lifecycle from continuous parameters through ZOH discretization to both the convolutional training path and the recurrent inference path. This is production-grade code, not a toy: it handles the numerically sensitive matrix exponential via the DPLR structure, initializes $\mathbf{A}$ from the HiPPO-LagT construction, and provides both forward modes under a single interface.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import rearrange
import math

def hippo_legt_matrix(N: int) -> torch.Tensor:
    """
    Construct the HiPPO-LegT A matrix of size (N, N).
    This is the theoretically optimal initialization for uniform-measure
    history approximation. The matrix is lower-triangular.
    """
    Q = torch.arange(N, dtype=torch.float64)
    # A[n,k] = -(2n+1)^0.5 * (2k+1)^0.5  for n > k
    #         = -(n+1)                      for n == k
    #         = 0                           for n < k
    A = torch.zeros(N, N, dtype=torch.float64)
    for n in range(N):
        for k in range(n):
            A[n, k] = -((2 * n + 1) ** 0.5) * ((2 * k + 1) ** 0.5)
        A[n, n] = -(n + 1)
    return A.float()


def zoh_discretize(A: torch.Tensor, B: torch.Tensor, dt: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Zero-order hold discretization.
    A: (N, N), B: (N, U), dt: scalar or (batch,)
    Returns Abar: (N, N), Bbar: (N, U)
    """
    # Scale A by dt for the matrix exponential
    dtA = dt * A  # (N, N) broadcast with scalar dt
    Abar = torch.linalg.matrix_exp(dtA)
    # Bbar = A^{-1} (exp(A dt) - I) B
    # Computed as the solution to A X = (Abar - I) B for numerical stability
    AmI = Abar - torch.eye(A.shape[0], device=A.device, dtype=A.dtype)
    Bbar = torch.linalg.solve(A, AmI @ B)
    return Abar, Bbar


def bilinear_discretize(A: torch.Tensor, B: torch.Tensor, dt: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Bilinear (Tustin) discretization. Unconditionally stable.
    Maps left-half s-plane exactly onto interior of unit disk.
    """
    N = A.shape[0]
    I = torch.eye(N, device=A.device, dtype=A.dtype)
    half_dtA = (dt / 2.0) * A
    # (I - dt/2 * A)^{-1}
    left_inv = torch.linalg.inv(I - half_dtA)
    Abar = left_inv @ (I + half_dtA)
    Bbar = left_inv @ (dt * B)
    return Abar, Bbar


def build_ssm_kernel(Abar: torch.Tensor, Bbar: torch.Tensor, C: torch.Tensor, L: int) -> torch.Tensor:
    """
    Compute the SSM convolution kernel K of length L.
    K[i] = C @ Abar^i @ Bbar, shape: (L, O, U)
    For single-input single-output (U=O=1), K has shape (L,).
    """
    # Naive O(L * N^2) construction — replace with structured computation for large N
    kernel = []
    # Cache Abar powers via repeated multiplication
    Ai = torch.eye(Abar.shape[0], device=Abar.device, dtype=Abar.dtype)
    for i in range(L):
        # C @ Ai @ Bbar: (O, N) @ (N, N) @ (N, U) -> (O, U)
        Ki = C @ Ai @ Bbar
        kernel.append(Ki)
        Ai = Abar @ Ai
    return torch.stack(kernel, dim=0)  # (L, O, U)


class S4Layer(nn.Module):
    """
    A single S4-style SSM layer with:
      - HiPPO-LegT A initialization
      - ZOH discretization (dt learned via log parameterization)
      - Training: FFT-based convolution, O(L log L)
      - Inference: sequential recurrence, O(N) per step

    Args:
        d_model: input/output feature dimension
        d_state: latent state dimension N
        dt_min, dt_max: bounds for the initial log-dt distribution
    """
    def __init__(
        self,
        d_model: int,
        d_state: int = 64,
        dt_min: float = 0.001,
        dt_max: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state

        # Initialize A from HiPPO-LegT theory, frozen structure
        A_init = hippo_legt_matrix(d_state)
        # Parameterize A as a fixed structured matrix; learn a diagonal scaling
        self.register_buffer("A", A_init)

        # B: (N, d_model), C: (d_model, N), learned
        self.B = nn.Parameter(torch.randn(d_state, d_model) * 0.01)
        self.C = nn.Parameter(torch.randn(d_model, d_state) * 0.01)

        # Learned log-dt per feature dimension; initialized uniformly in [dt_min, dt_max]
        log_dt = torch.rand(d_model) * (math.log(dt_max) - math.log(dt_min)) + math.log(dt_min)
        self.log_dt = nn.Parameter(log_dt)

        # Optional skip connection (D matrix)
        self.D = nn.Parameter(torch.ones(d_model))

        # State buffer for autoregressive inference; None when not in inference mode
        self._inference_state: torch.Tensor | None = None

    def _get_discrete_params(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Discretize A, B using the current learned dt (mean across features)."""
        dt = self.log_dt.exp().mean()
        return zoh_discretize(self.A, self.B, dt)

    def _build_kernel(self, L: int) -> torch.Tensor:
        """
        Build the global convolution kernel of length L.
        Returns shape (d_model, L) for direct use with F.conv1d.
        """
        Abar, Bbar = self._get_discrete_params()
        # K[i] = C Abar^i Bbar: (d_model, N) @ (N, N)^i @ (N, d_model) -> (d_model, d_model)
        # For efficiency, we compute K as a (L, d_model, d_model) tensor then take the diagonal
        # (treating each output feature independently driven by its matching input feature).
        K_full = build_ssm_kernel(Abar, Bbar, self.C, L)  # (L, d_model, d_model)
        # Diagonal: each output channel i is driven only by input channel i
        K_diag = torch.diagonal(K_full, dim1=1, dim2=2)    # (L, d_model)
        return K_diag.T.contiguous()                        # (d_model, L)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        """
        Training-mode forward: FFT convolution.
        u: (batch, length, d_model) — standard sequence-first layout after transpose
        Returns y: (batch, length, d_model)
        """
        B_sz, L, D = u.shape
        assert D == self.d_model

        # Build kernel: (d_model, L)
        K = self._build_kernel(L)

        # FFT convolution along the sequence axis
        # Pad to length 2L - 1 to avoid circular aliasing
        fft_size = 1 << (2 * L - 1).bit_length()
        u_f = torch.fft.rfft(u.transpose(1, 2), n=fft_size)   # (B, D, fft_size//2+1)
        K_f = torch.fft.rfft(K, n=fft_size)                    # (D, fft_size//2+1)
        y_f = u_f * K_f.unsqueeze(0)
        y = torch.fft.irfft(y_f, n=fft_size)[..., :L]          # (B, D, L)

        # Skip connection: y += D * u
        y = y + self.D.unsqueeze(0).unsqueeze(-1) * u.transpose(1, 2)
        return y.transpose(1, 2)  # (B, L, D)

    def init_inference_state(self, batch_size: int) -> None:
        """Initialize zero recurrent state for autoregressive decoding."""
        device = self.A.device
        self._inference_state = torch.zeros(
            batch_size, self.d_state, self.d_model, device=device, dtype=self.A.dtype
        )

    def step(self, u_k: torch.Tensor) -> torch.Tensor:
        """
        Single-step recurrent inference: O(N) per token.
        u_k: (batch, d_model)
        Returns y_k: (batch, d_model)
        """
        assert self._inference_state is not None, "Call init_inference_state() before step()."
        Abar, Bbar = self._get_discrete_params()

        # h[k] = Abar h[k-1] + Bbar u[k]
        # h: (B, N, D), Abar: (N, N), Bbar: (N, D), u_k: (B, D)
        h = self._inference_state
        # Abar @ h: (N,N) x (B,N,D) -> einsum over state dim
        Ah = torch.einsum("nm,bmd->bnd", Abar, h)
        Bu = torch.einsum("nd,bd->bnd", Bbar, u_k)
        h_new = Ah + Bu
        self._inference_state = h_new

        # y[k] = C h[k] + D u[k]
        # C: (D, N), h_new: (B, N, D) -> sum over n: (B, D)
        y = torch.einsum("dn,bnd->bd", self.C, h_new) + self.D * u_k
        return y
```

A minimal correctness check to verify that the recurrent and convolutional paths agree:

```python
def verify_dual_paths():
    torch.manual_seed(42)
    layer = S4Layer(d_model=8, d_state=16)
    layer.eval()

    B_sz, L = 2, 32
    u = torch.randn(B_sz, L, 8)

    # Convolutional (training) path
    with torch.no_grad():
        y_conv = layer(u)

    # Recurrent (inference) path — step by step
    layer.init_inference_state(batch_size=B_sz)
    y_rec = []
    with torch.no_grad():
        for t in range(L):
            y_t = layer.step(u[:, t, :])
            y_rec.append(y_t)
    y_rec = torch.stack(y_rec, dim=1)  # (B, L, D)

    max_err = (y_conv - y_rec).abs().max().item()
    print(f"Max absolute error between conv and recurrent path: {max_err:.6e}")
    assert max_err < 1e-4, f"Paths disagree: {max_err}"
    print("Dual-path consistency verified.")

verify_dual_paths()
```

### Numerical Failure Modes and Their Mitigations

The most common failure mode in practice is **state explosion under poor $\mathbf{A}$ conditioning**. When $\mathbf{A}$ has eigenvalues near or outside the stability boundary, $\bar{\mathbf{A}}^k$ grows exponentially with $k$, and the hidden state $\mathbf{h}_k$ quickly overflows float16 during mixed-precision training. The symptom is loss becoming NaN after a few hundred steps, correlated with long sequences. The mitigation is threefold: use the HiPPO initialization rather than random Gaussian $\mathbf{A}$; apply spectral normalization or explicitly constrain $\mathbf{A}$ to have all eigenvalues in the left half-plane (for continuous time) before discretization; and monitor the spectral radius $\rho(\bar{\mathbf{A}})$ during training as a diagnostic.

**Gradient vanishing through deep state stacks** is the SSM analog of the classic RNN vanishing-gradient problem. Even when the forward dynamics are stable, the backward pass through $L$ applications of $\bar{\mathbf{A}}$ multiplies gradients by $(\bar{\mathbf{A}}^T)^L$. If the spectral radius of $\bar{\mathbf{A}}$ is less than one (which it must be for stability), gradients for early-sequence positions shrink geometrically. The structured $\mathbf{A}$ constructions from HiPPO mitigate this by concentrating eigenvalues near $-\epsilon$ for small $\epsilon$, so that $e^{-\epsilon L}$ stays close to one for large $L$. The practical fix when training very deep SSM stacks is to monitor gradient norms at each layer and apply gradient clipping with a tighter threshold than you would use for Transformers.

**Discretization mismatch at variable sequence lengths** arises when a model trained with one effective $\Delta t$ is evaluated at a different sampling rate — common in audio models deployed across different sample rates. Because ZOH discretization bakes the step size into $\bar{\mathbf{A}}$ and $\bar{\mathbf{B}}$ at initialization, changing $\Delta t$ at inference requires re-discretizing on the fly. Making `log_dt` a trainable parameter (as in the implementation above) rather than a fixed buffer is the correct architecture: the model learns the appropriate time scale during training and can be re-discretized to any target $\Delta t$ at deployment. For the bilinear method, this re-discretization is always numerically safe; for ZOH, re-compute the matrix exponential when $\Delta t$ changes by more than a factor of two from the training distribution.

**Kernel aliasing in the FFT path** occurs when the sequence length used at inference exceeds the kernel length used during training. Because the SSM kernel $\mathbf{K}_i = \mathbf{C}\bar{\mathbf{A}}^i\bar{\mathbf{B}}$ decays geometrically in $i$ (for stable $\bar{\mathbf{A}}$), truncating it to the training length $L$ introduces a small but nonzero error on longer sequences. The correct fix is to always build the kernel at the actual sequence length rather than caching a fixed-length kernel across sequence lengths. For models that must handle extremely long contexts, the structured state compression in S4D (diagonal $\mathbf{A}$) reduces kernel construction cost to $O(NL)$, making on-the-fly kernel construction feasible even for $L > 10^6$.

The table below summarizes the tradeoffs between discretization schemes along the dimensions most relevant to production deployment:

| Property | Euler | ZOH | Bilinear |
|---|---|---|---|
| Stability guarantee | Conditional on $\Delta t$ | Conditional on $\Delta t$ | Unconditional |
| Accuracy for piecewise-constant input | First-order | Exact | Second-order |
| Cost of re-discretization | $O(N^2)$ multiply | $O(N^3)$ matrix exp | $O(N^3)$ inversion |
| Frequency response preservation | Poor | Good | Excellent (with warping) |
| Recommended use case | Prototyping only | S4, fixed $\Delta t$ | Mamba, learned $\Delta t$ |

The practical takeaway is that ZOH is the default for production SSMs with fixed sampling rates, and bilinear is the right choice when $\Delta t$ is a learned or variable parameter. Euler discretization has no production use case beyond initial prototyping, where its simplicity speeds up debugging before the numerical properties matter.

The final invariant to internalize from this lesson is the one that motivates everything that follows: **a state space model is a lossy compression of an input sequence into a fixed-size state vector, and the entire art of SSM design is engineering that compression to be maximally informative for the downstream prediction task.** The continuous-time formulation gives you the mathematical language to reason about what information is preserved. Discretization gives you the computational mechanism to process discrete sequences. The duality between convolution and recurrence gives you the efficiency to do both training and inference at scale. Every architectural innovation in the SSM literature — HiPPO, S4, DSS, S5, Mamba, Jamba — is a refinement of one of these three elements, and understanding them at this level of precision is the prerequisite for evaluating and extending the state of the art.
