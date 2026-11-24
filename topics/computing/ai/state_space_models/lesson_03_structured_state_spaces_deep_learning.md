# Lesson 3: Structured State Spaces in Deep Learning

## 1. First-Principles Intuition & Invariants

The emergence of Structured State Space models (S4) represents a fundamental shift in how we conceptualize sequence modeling within deep learning architectures. Where transformers achieve their remarkable expressivity through explicit attention mechanisms that compute pairwise relationships across sequence positions—an operation scaling quadratically with sequence length—state space models offer a return to principles rooted in continuous-time dynamical systems and linear time-invariant signal processing. The central insight animating S4 architecture lies in recognizing that many long-range dependency problems can be reformulated as filtering operations over continuous-time state trajectories, then discretized and parameterized in ways that preserve both computational efficiency and the capacity to capture dependencies spanning tens of thousands of time steps.

At its mathematical core, a state space model describes the evolution of a hidden state vector through time via a system of linear differential equations. The continuous-time formulation takes the form $\frac{dx(t)}{dt} = Ax(t) + Bu(t)$ for the state evolution equation, coupled with the output equation $y(t) = Cx(t) + Du(t)$, where $x(t) \in \mathbb{R}^N$ represents the latent state, $u(t) \in \mathbb{R}^1$ the input signal, and $y(t) \in \mathbb{R}^1$ the output. The matrices $A \in \mathbb{R}^{N \times N}$, $B \in \mathbb{R}^{N \times 1}$, $C \in \mathbb{R}^{1 \times N}$, and $D \in \mathbb{R}^{1 \times 1}$ constitute the system's parameters, encoding how the state transitions forward and how observations are generated from hidden states.

The path from continuous-time systems to practical discrete-time computation requires discretization strategies that preserve the stability and expressivity of the underlying continuous dynamics. The bilinear transform and zero-order hold methods provide such mappings, converting the continuous matrices $(A, B, C, D)$ into their discrete counterparts $(\bar{A}, \bar{B}, \bar{C}, \bar{D})$ through operations that respect the matrix exponential structure of the solution to the differential equation. For a time step $\Delta$, the discretized state transition matrix takes the form $\bar{A} = \exp(\Delta A)$, while the input matrix becomes $\bar{B} = A^{-1}(\exp(\Delta A) - I)B$, with $\bar{C} = C$ and $\bar{D} = D$ typically preserved directly.

Once discretized, the state space model admits two equivalent computational representations that reveal its dual nature as both a recurrent system and a convolutional operator. In recurrent form, we iterate the state update $x_k = \bar{A}x_{k-1} + \bar{B}u_k$ and generate outputs $y_k = \bar{C}x_k + \bar{D}u_k$, processing the sequence one step at a time with explicit state dependence across time. This formulation naturally captures sequential dependencies but requires $O(L)$ sequential operations for a sequence of length $L$, fundamentally limiting parallelization during training. The convolutional perspective emerges when we recognize that unrolling the recurrence yields an expression where each output depends on all previous inputs through a convolution kernel $\bar{K}$. Specifically, the sequence of outputs can be written as $y = \bar{K} * u$, where the convolution kernel elements are $\bar{K}_i = \bar{C}\bar{A}^i\bar{B}$ for $i \geq 0$, plus the direct feedthrough term $\bar{D}$ at position zero.

The profound challenge facing vanilla state space parameterizations lies in the simultaneous satisfaction of competing numerical constraints. The state matrix $A$ must encode long-range dependencies—requiring eigenvalues with magnitudes approaching unity to prevent exponential decay of information—while remaining numerically stable during gradient-based optimization. The discretization operation $\exp(\Delta A)$ can produce catastrophically large values when $A$ has eigenvalues with large positive real parts, and the repeated matrix powers $\bar{A}^i$ needed to compute the convolution kernel are notoriously unstable for general matrices. Furthermore, computing the full convolution kernel explicitly requires $O(L)$ matrix-vector products, each involving the $N \times N$ state matrix, yielding $O(LN^2)$ complexity before even performing the convolution operation itself.

The S4 architecture resolves these tensions through structured parameterization strategies that impose constraints on $A$, enabling closed-form computation of the kernel coefficients and efficient convolution via Fast Fourier Transform. The breakthrough insight recognizes that diagonal and nearly-diagonal structures in the state matrix—when combined with principled initialization schemes derived from approximation theory—preserve the expressive power needed for long-range dependencies while enabling computational shortcuts that reduce kernel generation from $O(LN^2)$ to $O(N \log L)$ and leverage FFT-based convolution at $O(L \log L)$ cost. The resulting architecture maintains the representational capacity of continuous-time dynamical systems while achieving computational efficiency competitive with Transformers on short sequences and vastly superior performance as sequence length grows.

## 2. Core Architecture & Mechanics

The construction of an S4 layer begins with the choice of state matrix structure and initialization scheme. The HiPPO (High-order Polynomial Projection Operators) framework provides the theoretical foundation for this initialization, deriving state matrices from the principle of optimal polynomial approximation of historical input signals. The core idea posits that the hidden state should maintain a compressed representation of the input history by storing coefficients of an orthogonal polynomial expansion that best reconstructs past observations. Different choices of polynomial basis and measure over time yield different HiPPO matrices, each encoding different notions of memory and decay.

The HiPPO-LegS (Scaled Legendre) matrix emerges from approximating the input signal over a sliding window $[t-\theta, t]$ using translated Legendre polynomials, where $\theta$ controls the memory horizon. The resulting continuous-time state matrix takes a specific structured form where off-diagonal elements encode coupling between polynomial coefficients. When $N$ state dimensions are used, this matrix enables reconstruction of the input history using an $N$-th degree polynomial approximation, with approximation error decreasing as $O(1/N)$ under smoothness assumptions on the input. The HiPPO-LagT (Laplace-Transformed Legendre) variant instead optimizes approximation over the infinite past $(-\infty, t]$ with exponential weighting, producing a state matrix whose eigenvalue spectrum naturally concentrates near the imaginary axis—precisely the region conferring both stability and long-term memory.

The diagonal state space models (DSS) formulation introduces the central structural constraint that enables efficient computation. Rather than parameterizing $A$ as a full $N \times N$ matrix, we restrict it to diagonal form $A = \text{diag}(\lambda_1, \lambda_2, \ldots, \lambda_N)$ where each $\lambda_i \in \mathbb{C}$ is a complex scalar. The vectors $B, C \in \mathbb{C}^N$ remain unrestricted, while $D \in \mathbb{R}$ serves as a residual connection strength. This parameterization reduces the number of state transition parameters from $O(N^2)$ to $O(N)$ while preserving expressive power through careful initialization and complex-valued computation. The diagonality constraint proves crucial because the matrix exponential $\exp(\Delta A)$ becomes element-wise: $\exp(\Delta A) = \text{diag}(\exp(\Delta\lambda_1), \ldots, \exp(\Delta\lambda_N))$, and more importantly, the matrix power $A^i$ equals $\text{diag}(\lambda_1^i, \ldots, \lambda_N^i)$.

With diagonal structure in place, the convolution kernel computation simplifies dramatically. Recall that $\bar{K}_i = \bar{C}\bar{A}^i\bar{B}$, which for diagonal $\bar{A}$ becomes a sum over state dimensions: $\bar{K}_i = \sum_{n=1}^{N} \bar{C}_n \bar{A}_n^i \bar{B}_n = \sum_{n=1}^{N} \bar{C}_n \exp(i \Delta \lambda_n) \bar{B}_n$. This expression reveals that each kernel element is a weighted sum of geometric progressions, one per state dimension. Computing all $L$ kernel values naively still requires $O(LN)$ operations, but the structure admits a crucial optimization through frequency domain computation. The convolution $y = \bar{K} * u$ in the time domain corresponds to element-wise multiplication in the frequency domain: $\hat{y}(\omega) = \hat{\bar{K}}(\omega) \cdot \hat{u}(\omega)$, where $\hat{f}$ denotes the Fourier transform of sequence $f$.

The frequency-domain convolution kernel can be evaluated directly from the continuous-time transfer function. For a state space system, the transfer function $H(s) = C(sI - A)^{-1}B + D$ maps Laplace-domain inputs to outputs. With diagonal $A$, this simplifies to $H(s) = \sum_{n=1}^{N} \frac{C_n B_n}{s - \lambda_n} + D$. To evaluate the discrete-time frequency response at the FFT grid points, we substitute $s = 2\pi i \omega / \Delta$ and compute $\hat{\bar{K}}(\omega) = \sum_{n=1}^{N} \frac{\bar{C}_n \bar{B}_n}{2\pi i \omega / \Delta - \lambda_n} + D$ for each frequency bin. This requires $O(N)$ operations per frequency point, and with $L$ frequency bins spanning the FFT grid, the total kernel evaluation cost becomes $O(NL)$. The convolution itself via FFT requires $O(L \log L)$ operations: one forward FFT of the input, element-wise multiplication with the pre-computed kernel spectrum, and one inverse FFT to return to the time domain.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import rearrange
import math


class S4Layer(nn.Module):
    """
    Diagonal Structured State Space (S4) layer with HiPPO initialization
    and efficient FFT-based convolution.
    """
    
    def __init__(self, d_model, state_dim=64, dt_min=0.001, dt_max=0.1):
        super().__init__()
        self.d_model = d_model
        self.N = state_dim
        
        # Initialize HiPPO-LegS matrix eigenvalues (diagonal elements)
        # These are complex-valued and positioned near the imaginary axis
        lambda_real = torch.linspace(-0.5, -0.01, state_dim)
        lambda_imag = torch.linspace(0, math.pi * state_dim, state_dim)
        self.register_buffer('lambda_re', lambda_real)
        self.register_buffer('lambda_im', lambda_imag)
        
        # Learnable parameters: B, C vectors and D scalar
        # Initialize B with Xavier uniform, C to match HiPPO projection
        self.B = nn.Parameter(torch.randn(d_model, state_dim, 2))  # complex: [..., 0]=real, [..., 1]=imag
        self.C = nn.Parameter(torch.randn(d_model, state_dim, 2))
        nn.init.xavier_uniform_(self.B[..., 0])
        nn.init.xavier_uniform_(self.B[..., 1])
        nn.init.xavier_uniform_(self.C[..., 0])
        nn.init.xavier_uniform_(self.C[..., 1])
        
        self.D = nn.Parameter(torch.randn(d_model))
        
        # Learnable step size (log-space for stability)
        log_dt = torch.rand(d_model) * (math.log(dt_max) - math.log(dt_min)) + math.log(dt_min)
        self.log_dt = nn.Parameter(log_dt)
        
        # Layer norm and output projection
        self.norm = nn.LayerNorm(d_model)
        self.output_linear = nn.Linear(d_model, d_model)
        
    def kernel_fft(self, L):
        """
        Compute SSM convolution kernel in frequency domain.
        Returns kernel frequency response at L frequency bins.
        """
        dt = torch.exp(self.log_dt)  # [d_model]
        
        # Discretize: compute exp(dt * lambda)
        # lambda is complex: lambda = lambda_re + i * lambda_im
        dt_lambda_re = dt.unsqueeze(-1) * self.lambda_re  # [d_model, N]
        dt_lambda_im = dt.unsqueeze(-1) * self.lambda_im
        
        # Discrete A_bar = exp(dt * lambda) for diagonal case
        A_bar_re = torch.exp(dt_lambda_re) * torch.cos(dt_lambda_im)  # real part
        A_bar_im = torch.exp(dt_lambda_re) * torch.sin(dt_lambda_im)  # imag part
        
        # Discrete B_bar: (dt*A)^{-1} (exp(dt*A) - I) B ≈ (exp(dt*A) - I) / (dt*A) * B
        # For diagonal, this simplifies per element
        # Approximation: B_bar ≈ B * (exp(dt*lambda) - 1) / (dt*lambda)
        eps = 1e-7
        dt_lambda_mag = torch.sqrt(dt_lambda_re**2 + dt_lambda_im**2 + eps)
        exp_factor_re = (A_bar_re - 1.0)
        exp_factor_im = A_bar_im
        
        # B is complex: B = B_re + i*B_im
        B_re = self.B[..., 0]  # [d_model, N]
        B_im = self.B[..., 1]
        
        # B_bar = (exp(dt*lambda) - 1) / (dt*lambda) * B
        # For diagonal: element-wise complex multiplication
        scale_re = exp_factor_re / (dt_lambda_mag + eps)
        scale_im = exp_factor_im / (dt_lambda_mag + eps)
        
        B_bar_re = scale_re * B_re - scale_im * B_im
        B_bar_im = scale_re * B_im + scale_im * B_re
        
        # C_bar = C (unchanged)
        C_bar_re = self.C[..., 0]  # [d_model, N]
        C_bar_im = self.C[..., 1]
        
        # Generate frequency grid for FFT: omega_k = 2*pi*k/L for k=0..L-1
        # Transfer function: H(2*pi*i*k/L) = sum_n (C_n * B_n) / (2*pi*i*k/L - lambda_n) + D
        freqs = torch.linspace(0, 2 * math.pi, L, device=dt.device)  # [L]
        
        # Frequency domain evaluation:
        # s = 2*pi*i*omega (pure imaginary for DFT frequencies)
        # For diagonal SSM: H(s) = sum_n C_n * B_n / (s - lambda_n) + D
        # s = i*omega, lambda = lambda_re + i*lambda_im
        # (s - lambda) = i*omega - lambda_re - i*lambda_im = -lambda_re + i*(omega - lambda_im)
        
        s_re = torch.zeros_like(freqs)  # [L]
        s_im = freqs  # [L]
        
        # Broadcast: [d_model, N, L]
        denom_re = s_re.view(1, 1, -1) - self.lambda_re.view(1, -1, 1)  # -lambda_re + 0
        denom_im = s_im.view(1, 1, -1) - self.lambda_im.view(1, -1, 1)  # omega - lambda_im
        
        denom_mag_sq = denom_re**2 + denom_im**2 + eps
        
        # (C * B) / (s - lambda) where all are complex
        # Numerator: C_bar * B_bar (complex multiplication)
        CB_re = C_bar_re.unsqueeze(-1) * B_bar_re.unsqueeze(-1) - C_bar_im.unsqueeze(-1) * B_bar_im.unsqueeze(-1)
        CB_im = C_bar_re.unsqueeze(-1) * B_bar_im.unsqueeze(-1) + C_bar_im.unsqueeze(-1) * B_bar_re.unsqueeze(-1)
        
        # Complex division: (CB_re + i*CB_im) / (denom_re + i*denom_im)
        H_re = (CB_re * denom_re + CB_im * denom_im) / denom_mag_sq
        H_im = (CB_im * denom_re - CB_re * denom_im) / denom_mag_sq
        
        # Sum over state dimensions
        H_re = H_re.sum(dim=1)  # [d_model, L]
        H_im = H_im.sum(dim=1)
        
        # Add direct feedthrough D (real-valued, affects only DC/real component)
        H_re = H_re + self.D.unsqueeze(-1)
        
        # Return as complex tensor
        H = torch.complex(H_re, H_im)  # [d_model, L]
        return H
    
    def forward(self, u):
        """
        Forward pass using FFT-based convolution.
        
        Args:
            u: Input tensor of shape [batch, length, d_model]
            
        Returns:
            Output tensor of shape [batch, length, d_model]
        """
        batch, length, _ = u.shape
        
        # Transpose to [batch, d_model, length] for per-channel convolution
        u = rearrange(u, 'b l d -> b d l')
        
        # Compute kernel frequency response
        L_fft = 2 * length  # Zero-pad to avoid circular convolution artifacts
        H = self.kernel_fft(L_fft)  # [d_model, L_fft]
        
        # FFT of input (per channel)
        U_fft = torch.fft.rfft(u, n=L_fft)  # [batch, d_model, L_fft//2+1]
        
        # Take only the positive frequencies from H (rfft symmetry)
        H_rfft = H[:, :L_fft//2+1]  # [d_model, L_fft//2+1]
        
        # Element-wise multiplication in frequency domain
        Y_fft = U_fft * H_rfft.unsqueeze(0)  # [batch, d_model, L_fft//2+1]
        
        # Inverse FFT back to time domain
        y = torch.fft.irfft(Y_fft, n=L_fft)  # [batch, d_model, L_fft]
        
        # Truncate to original length
        y = y[:, :, :length]
        
        # Transpose back to [batch, length, d_model]
        y = rearrange(y, 'b d l -> b l d')
        
        # Apply normalization and output projection
        y = self.norm(y)
        y = self.output_linear(y)
        
        return y


class S4Block(nn.Module):
    """
    Full S4 block with pre-norm, S4 layer, GELU activation, and residual connection.
    """
    
    def __init__(self, d_model, state_dim=64, dropout=0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.s4 = S4Layer(d_model, state_dim)
        self.dropout1 = nn.Dropout(dropout)
        
        self.norm2 = nn.LayerNorm(d_model)
        self.ff = nn.Sequential(
            nn.Linear(d_model, 4 * d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(4 * d_model, d_model),
            nn.Dropout(dropout)
        )
        
    def forward(self, x):
        # S4 layer with residual
        x = x + self.dropout1(self.s4(self.norm1(x)))
        
        # Feedforward with residual
        x = x + self.ff(self.norm2(x))
        
        return x


class S4Model(nn.Module):
    """
    Complete S4 model for sequence classification or generation.
    """
    
    def __init__(self, vocab_size, d_model=256, n_layers=4, state_dim=64, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.blocks = nn.ModuleList([
            S4Block(d_model, state_dim, dropout) for _ in range(n_layers)
        ])
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size)
        
    def forward(self, x):
        """
        Args:
            x: Input token IDs [batch, length]
            
        Returns:
            Logits [batch, length, vocab_size]
        """
        x = self.embedding(x)  # [batch, length, d_model]
        
        for block in self.blocks:
            x = block(x)
        
        x = self.norm(x)
        logits = self.head(x)
        
        return logits


# Example training loop demonstrating long-range dependency handling
def train_s4_on_long_sequences():
    """
    Training procedure demonstrating S4's efficiency on long sequences.
    """
    # Hyperparameters
    vocab_size = 10000
    d_model = 256
    n_layers = 6
    state_dim = 64
    batch_size = 16
    seq_length = 16384  # Very long sequences where transformers struggle
    
    # Initialize model
    model = S4Model(vocab_size, d_model, n_layers, state_dim).cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
    
    # Synthetic data (replace with actual data loader)
    x = torch.randint(0, vocab_size, (batch_size, seq_length)).cuda()
    y = torch.randint(0, vocab_size, (batch_size, seq_length)).cuda()
    
    # Forward pass
    model.train()
    logits = model(x)  # [batch, seq_length, vocab_size]
    
    # Compute loss (cross-entropy over sequence)
    loss = F.cross_entropy(
        logits.reshape(-1, vocab_size),
        y.reshape(-1)
    )
    
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    
    # Gradient clipping for stability
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    
    optimizer.step()
    
    print(f"Loss: {loss.item():.4f}")
    print(f"Memory allocated: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")
    
    return model, loss.item()
```

The recurrent mode of operation provides an alternative execution path critical for autoregressive generation and online inference scenarios where the full sequence is not available upfront. During generation, we maintain the explicit state vector $x_k \in \mathbb{C}^N$ and iteratively apply the discrete state update equations. For diagonal $\bar{A}$, the update $x_k = \bar{A}x_{k-1} + \bar{B}u_k$ becomes element-wise: each state dimension evolves independently as $x_k^{(n)} = \bar{A}_n x_{k-1}^{(n)} + \bar{B}_n u_k$. The output is computed via $y_k = \text{Re}(\bar{C}^\top x_k) + D u_k$, where we take the real part since the output must be real-valued while the internal states remain complex to capture oscillatory dynamics.

```python
class S4Recurrent(nn.Module):
    """
    Recurrent formulation of S4 layer for autoregressive generation.
    Maintains explicit state across time steps.
    """
    
    def __init__(self, d_model, state_dim=64, dt_min=0.001, dt_max=0.1):
        super().__init__()
        self.d_model = d_model
        self.N = state_dim
        
        # Same initialization as S4Layer
        lambda_real = torch.linspace(-0.5, -0.01, state_dim)
        lambda_imag = torch.linspace(0, math.pi * state_dim, state_dim)
        self.register_buffer('lambda_re', lambda_real)
        self.register_buffer('lambda_im', lambda_imag)
        
        self.B = nn.Parameter(torch.randn(d_model, state_dim, 2))
        self.C = nn.Parameter(torch.randn(d_model, state_dim, 2))
        self.D = nn.Parameter(torch.randn(d_model))
        
        nn.init.xavier_uniform_(self.B[..., 0])
        nn.init.xavier_uniform_(self.B[..., 1])
        nn.init.xavier_uniform_(self.C[..., 0])
        nn.init.xavier_uniform_(self.C[..., 1])
        
        log_dt = torch.rand(d_model) * (math.log(dt_max) - math.log(dt_min)) + math.log(dt_min)
        self.log_dt = nn.Parameter(log_dt)
        
        self.norm = nn.LayerNorm(d_model)
        self.output_linear = nn.Linear(d_model, d_model)
        
    def discretize(self):
        """
        Compute discrete-time parameters A_bar, B_bar, C_bar, D_bar.
        Returns them in a form convenient for recurrent stepping.
        """
        dt = torch.exp(self.log_dt)  # [d_model]
        
        # A_bar = exp(dt * lambda) for diagonal
        dt_lambda_re = dt.unsqueeze(-1) * self.lambda_re  # [d_model, N]
        dt_lambda_im = dt.unsqueeze(-1) * self.lambda_im
        
        A_bar_re = torch.exp(dt_lambda_re) * torch.cos(dt_lambda_im)
        A_bar_im = torch.exp(dt_lambda_re) * torch.sin(dt_lambda_im)
        
        # B_bar discretization
        eps = 1e-7
        dt_lambda_mag = torch.sqrt(dt_lambda_re**2 + dt_lambda_im**2 + eps)
        exp_factor_re = A_bar_re - 1.0
        exp_factor_im = A_bar_im
        
        B_re = self.B[..., 0]
        B_im = self.B[..., 1]
        
        scale_re = exp_factor_re / (dt_lambda_mag + eps)
        scale_im = exp_factor_im / (dt_lambda_mag + eps)
        
        B_bar_re = scale_re * B_re - scale_im * B_im
        B_bar_im = scale_re * B_im + scale_im * B_re
        
        C_bar_re = self.C[..., 0]
        C_bar_im = self.C[..., 1]
        
        # Package as complex tensors for cleaner stepping
        A_bar = torch.complex(A_bar_re, A_bar_im)  # [d_model, N]
        B_bar = torch.complex(B_bar_re, B_bar_im)  # [d_model, N]
        C_bar = torch.complex(C_bar_re, C_bar_im)  # [d_model, N]
        
        return A_bar, B_bar, C_bar, self.D
    
    def init_state(self, batch_size, device):
        """
        Initialize hidden state to zero.
        
        Returns:
            State tensor [batch, d_model, N] (complex)
        """
        return torch.zeros(batch_size, self.d_model, self.N, dtype=torch.complex64, device=device)
    
    def step(self, u, state, A_bar, B_bar, C_bar, D):
        """
        Single recurrent step: x_k = A_bar * x_{k-1} + B_bar * u_k
                               y_k = Re(C_bar^T * x_k) + D * u_k
        
        Args:
            u: Input at current timestep [batch, d_model]
            state: Previous state [batch, d_model, N] (complex)
            A_bar, B_bar, C_bar, D: Discrete-time parameters
            
        Returns:
            y: Output [batch, d_model]
            new_state: Updated state [batch, d_model, N]
        """
        # State update: x_k = A_bar * x_{k-1} + B_bar * u_k
        # For diagonal A: element-wise multiplication
        new_state = A_bar.unsqueeze(0) * state + B_bar.unsqueeze(0) * u.unsqueeze(-1)  # [batch, d_model, N]
        
        # Output: y_k = Re(C_bar^T * x_k) + D * u_k
        # C_bar^T * x_k: sum over state dimensions
        y_complex = (C_bar.unsqueeze(0) * new_state).sum(dim=-1)  # [batch, d_model]
        y = y_complex.real + D.unsqueeze(0) * u  # [batch, d_model]
        
        return y, new_state
    
    def forward_recurrent(self, u, state=None):
        """
        Recurrent forward pass processing sequence one step at a time.
        Used for autoregressive generation or streaming inference.
        
        Args:
            u: Input tensor [batch, length, d_model]
            state: Optional initial state [batch, d_model, N]
            
        Returns:
            y: Output tensor [batch, length, d_model]
            final_state: Final hidden state [batch, d_model, N]
        """
        batch, length, _ = u.shape
        
        # Initialize state if not provided
        if state is None:
            state = self.init_state(batch, u.device)
        
        # Discretize parameters once
        A_bar, B_bar, C_bar, D = self.discretize()
        
        # Process sequence recurrently
        outputs = []
        for t in range(length):
            u_t = u[:, t, :]  # [batch, d_model]
            y_t, state = self.step(u_t, state, A_bar, B_bar, C_bar, D)
            outputs.append(y_t)
        
        # Stack outputs
        y = torch.stack(outputs, dim=1)  # [batch, length, d_model]
        
        # Apply normalization and output projection
        y = self.norm(y)
        y = self.output_linear(y)
        
        return y, state


def demonstrate_autoregressive_generation():
    """
    Demonstrate autoregressive generation using recurrent S4.
    """
    vocab_size = 10000
    d_model = 256
    state_dim = 64
    batch_size = 4
    max_gen_length = 100
    
    # Initialize model in eval mode
    model = S4Recurrent(d_model, state_dim).cuda().eval()
    
    # Start with a prompt (e.g., first few tokens)
    prompt = torch.randint(0, vocab_size, (batch_size, 10)).cuda()
    
    # Embedding layer
    embedding = nn.Embedding(vocab_size, d_model).cuda()
    head = nn.Linear(d_model, vocab_size).cuda()
    
    # Initialize state
    state = model.init_state(batch_size, prompt.device)
    
    # Process prompt to establish initial state
    with torch.no_grad():
        prompt_emb = embedding(prompt)  # [batch, 10, d_model]
        _, state = model.forward_recurrent(prompt_emb, state)
        
    # Generate tokens one at a time
    generated = []
    current_token = prompt[:, -1]  # Last token of prompt
    
    for _ in range(max_gen_length):
        with torch.no_grad():
            # Embed current token
            u = embedding(current_token).unsqueeze(1)  # [batch, 1, d_model]
            
            # Single recurrent step
            y, state = model.forward_recurrent(u, state)  # y: [batch, 1, d_model]
            
            # Get logits and sample next token
            logits = head(y.squeeze(1))  # [batch, vocab_size]
            current_token = torch.argmax(logits, dim=-1)  # [batch]
            
            generated.append(current_token)
    
    generated = torch.stack(generated, dim=1)  # [batch, max_gen_length]
    print(f"Generated sequence shape: {generated.shape}")
    
    return generated
```

The interplay between convolutional and recurrent formulations reveals a fundamental duality in state space architectures. Training leverages the convolutional view for parallelization across sequence length, computing gradients efficiently via FFT-based operations that scale logarithmically. Inference for autoregressive tasks switches to recurrent mode, maintaining constant memory footprint independent of generation length and requiring only $O(N)$ operations per generated token—a stark contrast to transformers' $O(L^2)$ attention recomputation. This architectural flexibility positions S4 models as particularly well-suited for tasks demanding both efficient batch training on long sequences and low-latency sequential generation.

## 3. High-Performance Optimization & Failure Modes

The practical deployment of S4 models in production systems requires attention to numerical stability considerations that emerge from the complex-valued parameterization and exponential functions in the discretization process. The most critical failure mode arises when the learned eigenvalues $\lambda_n$ acquire large positive real components, causing $\exp(\Delta \lambda_n)$ to explode during discretization. Even when training appears stable in the convolutional mode—where the FFT evaluation bypasses explicit matrix exponentiation—switching to recurrent inference can expose latent instability as the discrete $\bar{A}$ produces unbounded state magnitudes after dozens of steps.

The standard mitigation enforces spectral constraints during training through parameterization tricks. Rather than learning the eigenvalues $\lambda_n$ directly, we parameterize their real parts in log-space with negative bias: $\text{Re}(\lambda_n) = -\exp(\theta_n^{\text{re}})$ where $\theta_n^{\text{re}}$ is the learned parameter. This ensures all eigenvalues have negative real parts, guaranteeing exponential decay and bounded discretization. The imaginary parts remain unrestricted, allowing the model to learn oscillatory dynamics across a wide frequency range. The time step $\Delta$ similarly benefits from log-space parameterization, typically initialized to values between $0.001$ and $0.1$ to balance temporal resolution against numerical precision.

Memory efficiency during training on extremely long sequences—contexts exceeding one hundred thousand time steps—demands careful management of intermediate activations. The FFT-based convolution avoids storing the full $O(L)$ sequence of hidden states, but the backward pass still requires gradients with respect to the frequency-domain kernel. The checkpointing strategy trades computation for memory by recomputing the forward FFT during the backward pass rather than caching it, reducing peak memory from $O(BLD)$ to $O(BL + BD)$ where $B$ is batch size, $L$ sequence length, and $D$ model dimension. For sequences approaching the million-token regime, further optimization splits the convolution into overlapping chunks processed independently, with boundary corrections to maintain mathematical equivalence to the full convolution.

The initialization strategy profoundly impacts both training dynamics and final model expressivity. While HiPPO matrices provide theoretically principled starting points, their spectral properties must be adapted to the specific sequence modeling task. For tasks requiring memorization of precise long-range dependencies—such as copying tokens from positions thousands of steps in the past—initializing eigenvalues with tightly clustered imaginary parts biases the model toward oscillatory patterns at specific frequencies. Conversely, logarithmically spaced imaginary components provide broad spectral coverage, enabling the model to adapt to dependencies at multiple time scales. The $B$ and $C$ vectors typically receive Xavier initialization scaled by $1/\sqrt{N}$, while the skip connection $D$ initializes near zero to allow the state space dynamics to dominate early in training.

The training procedure for S4 models benefits from warmup schedules and gradient clipping more than standard transformer training. The coupling between the learned eigenvalues and the discretization exponentials creates gradient pathways with widely varying magnitudes—eigenvalues near the imaginary axis produce large gradients through the frequency-domain kernel evaluation, while those with more negative real parts contribute vanishing gradients. A learning rate warmup of typically one thousand to five thousand steps, combined with gradient norm clipping at values between $0.5$ and $1.0$, stabilizes early training and prevents runaway updates to the spectral parameters. The AdamW optimizer with weight decay around $0.01$ provides appropriate regularization without over-damping the complex-valued parameters.

Validation of long-range dependency modeling capability requires carefully designed diagnostic tasks. The Long Range Arena benchmark suite provides standardized evaluation across sequence lengths from one thousand to sixteen thousand tokens, spanning modalities including text classification, image recognition on flattened pixel sequences, and path-finding on graphs serialized as sequences. The Path-X task in particular—requiring the model to determine path connectivity between points in unrolled 128x128 pixel images represented as sequences of length sixteen thousand—serves as a strong test of genuine long-term memory, as random guessing achieves only fifty percent accuracy while perfect memorization requires maintaining information from the sequence beginning through to the final prediction.

Profiling S4 inference reveals characteristic performance patterns distinct from transformer architectures. The convolutional mode exhibits a clear sweet spot between sequence lengths of roughly four thousand and thirty-two thousand, where FFT overhead is amortized and memory access patterns remain cache-friendly. Beyond these lengths, the FFT's $O(L \log L)$ complexity becomes measurable, and careful tuning of FFT library choices—such as cuFFT with CUDA Graphs for GPU deployment or FFTW with thread pinning for CPU inference—yields meaningful throughput improvements. The recurrent mode maintains flat per-step latency independent of previous generation length, making it the clear choice for interactive applications and streaming scenarios.

The integration of S4 layers with other architectural components requires attention to dimension matching and normalization strategies. When stacking S4 layers, inserting layer normalization before each S4 operation—the pre-norm configuration—proves more stable than post-norm arrangements, likely due to the spectral sensitivity of the state space parameters to input scale. Residual connections around each S4 block enable gradient flow through deep stacks, with typical production models employing between four and twelve layers. For sequence-to-sequence tasks, standard encoder-decoder patterns apply, though the cross-attention mechanism between encoder and decoder can itself be replaced by a state space layer that treats the encoder output sequence as input to a decoder-side SSM.

The diagnostic analysis of trained S4 models reveals their learned specialization patterns through eigenvalue spectrum visualization. Models successfully trained on long-range tasks typically develop eigenvalues forming distinct clusters in the complex plane, with each cluster corresponding to a characteristic time scale. High-frequency clusters—eigenvalues with large imaginary components—capture rapid token-to-token dependencies, while low-frequency clusters encode slow-varying trends and distant correlations. This emergent multi-scale representation arises without explicit architectural inductive bias beyond the HiPPO initialization, suggesting the training dynamics naturally discover the relevant frequency decompositions of the task.

Failure modes in deployed S4 systems most commonly manifest as drift during long generation sequences, where the recurrent state gradually accumulates numerical error or bias, causing output quality degradation after hundreds or thousands of generated tokens. The mitigation strategy periodically reinitializes the state by running the convolutional forward pass over the generated-so-far sequence in batches, then resuming recurrent generation from the recomputed state. This refresh operation costs $O(L \log L)$ but resets accumulated error, practically extending stable generation length indefinitely. For real-time systems, the refresh can be scheduled during natural pause boundaries in the generation task.

The comparison between S4 and transformer architectures reveals complementary strengths rather than strict dominance. Transformers excel at capturing complex, irregular dependency patterns within their context window through explicit attention, achieving state-of-the-art results on tasks where relevant information is densely distributed across moderate sequence lengths. S4 models demonstrate superior efficiency and stability on tasks with extremely long contexts or requiring constant-memory sequential processing, making them ideal for domains like genomic sequence analysis, long-document processing, time-series forecasting, and audio synthesis where sequence lengths routinely exceed fifty thousand time steps. Hybrid architectures combining local attention mechanisms for short-range refinement with S4 layers for long-range context aggregation represent an active research direction, attempting to capture the best characteristics of both paradigms within a unified model.
