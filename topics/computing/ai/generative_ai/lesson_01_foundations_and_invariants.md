# Lesson 1: Foundations & Mathematical Formulation

## Curriculum Roadmap

This lesson establishes the theoretical groundwork for Generative AI. We build from first principles — the maximum likelihood estimation framework — through the major families of generative models (explicit vs. implicit density), derive their objective functions, and analyze their architectural trade-offs. By the end, you will understand why each model family exists, what mathematical invariant it optimizes, and where it breaks down.

---

## 1. First-Principles Intuition & The Problem Space

### 1.1 What Generative Models Actually Do

A generative model learns a mapping from a latent space $\mathcal{Z}$ to a data space $\mathcal{X}$ such that sampling from $\mathcal{Z}$ and passing through the model produces samples distributed according to the true data distribution $p_{\text{data}}(\mathbf{x})$. Formally, given a dataset $\{\mathbf{x}^{(1)}, \dots, \mathbf{x}^{(N)}\}$ drawn i.i.d. from $p_{\text{data}}$, we seek parameters $\theta$ such that $p_\theta(\mathbf{x}) \approx p_{\text{data}}(\mathbf{x})$.

This is fundamentally a density estimation problem. The distinction between model families lies in **how** they approach this estimation:

- **Explicit density models** define $p_\theta(\mathbf{x})$ tractably and maximize the log-likelihood $\sum_i \log p_\theta(\mathbf{x}^{(i)})$. Autoregressive models (PixelCNN, Transformer language models) and flow-based models (RealNVP, Glow) fall here. VAEs are explicit but maximize a lower bound on log-likelihood rather than the likelihood itself.
- **Implicit density models** never define $p_\theta(\mathbf{x})$ explicitly. Instead, they learn a sampling procedure whose output distribution matches $p_{\text{data}}$. GANs are the canonical example — the generator defines a pushforward distribution $p_G(\mathbf{x}) = \int p_{\mathcal{Z}}(\mathbf{z}) \, \delta(\mathbf{x} - G_\theta(\mathbf{z})) \, d\mathbf{z}$, and training uses a discriminator to align $p_G$ with $p_{\text{data}}$ without ever computing $p_G$ directly.
- **Iterative denoising models** (diffusion models, score-based models) learn to reverse a noising process. They define $p_\theta(\mathbf{x})$ implicitly through a Markov chain that gradually denoises from a Gaussian prior.

### 1.2 The Curse of Dimensionality

Consider modeling $28 \times 28$ grayscale images (784 pixels, each $\in \{0, \dots, 255\}$). The sample space has $256^{784} \approx 10^{1889}$ possible configurations. The true data distribution concentrates on a manifold of dramatically lower effective dimension — natural images occupy a tiny fraction of pixel space. This is why generative models incorporate **inductive biases** that exploit structure:

- **Locality** (convolutional architectures, local attention)
- **Compositionality** (hierarchical latent variables, multi-scale architectures)
- **Symmetry** (permutation invariance in set-based models, equivariance in geometric models)

The dimensionality challenge also explains why naive approaches fail. A histogram-based density estimator in pixel space would require exponentially many bins. Kernel density estimation suffers the same exponential sample complexity. Neural network-based models parameterize the density with a function approximator whose capacity scales polynomially with the effective (manifold) dimension rather than the ambient dimension.

### 1.3 Why PCA and t-SNE Are Not Solutions

The original material suggested PCA and t-SNE as dimensionality reduction techniques for generative modeling. This is misleading in two ways:

1. **PCA** learns a linear projection. It is useful as a preprocessing step or as a trivial baseline (e.g., eigenface models), but it cannot capture nonlinear manifold structure. A generative model built on PCA produces blurry, low-rank reconstructions because the Gaussian assumption in PCA latent space is too restrictive for natural data.

2. **t-SNE** is a **non-parametric visualization technique**. It maps high-dimensional data to 2D or 3D for human inspection. It does not produce an invertible mapping — you cannot generate new high-dimensional samples from t-SNE output. It also distorts global geometry, preserving only local neighborhood structure. Using t-SNE as a preprocessing step for a generative model is methodologically incorrect.

The actual dimensionality reduction that matters in generative AI happens **inside** the model: the encoder in a VAE compresses data to a low-dimensional latent code, the generator in a GAN maps a low-dimensional noise vector to data space, and the U-Net in a diffusion model operates on representations at multiple scales. The model itself is the dimensionality reducer.

---

## 2. Mathematical Formalization & Core Invariants

### 2.1 Maximum Likelihood: The Unifying Objective

All explicit generative models ultimately optimize (or bound) the log-likelihood of the data:

$$\mathcal{L}(\theta) = \frac{1}{N} \sum_{i=1}^{N} \log p_\theta(\mathbf{x}^{(i)})$$

This is equivalent to minimizing the Kullback-Leibler divergence $D_{\text{KL}}(p_{\text{data}} \,\|\, p_\theta)$:

$$D_{\text{KL}}(p_{\text{data}} \,\|\, p_\theta) = \mathbb{E}_{\mathbf{x} \sim p_{\text{data}}} \left[ \log p_{\text{data}}(\mathbf{x}) \right] - \mathbb{E}_{\mathbf{x} \sim p_{\text{data}}} \left[ \log p_\theta(\mathbf{x}) \right]$$

Since $\log p_{\text{data}}(\mathbf{x})$ is constant w.r.t. $\theta$, maximizing log-likelihood minimizes this KL divergence. The different model families differ in how they make $\log p_\theta(\mathbf{x})$ tractable.

### 2.2 Variational Autoencoders (VAEs)

VAEs handle intractable posteriors by introducing an encoder $q_\phi(\mathbf{z}|\mathbf{x})$ and optimizing the Evidence Lower Bound (ELBO):

$$\log p_\theta(\mathbf{x}) \geq \mathcal{L}_{\text{ELBO}}(\theta, \phi; \mathbf{x}) = \underbrace{\mathbb{E}_{q_\phi(\mathbf{z}|\mathbf{x})} \left[ \log p_\theta(\mathbf{x}|\mathbf{z}) \right]}_{\text{Reconstruction term}} - \underbrace{D_{\text{KL}}\left(q_\phi(\mathbf{z}|\mathbf{x}) \,\|\, p(\mathbf{z})\right)}_{\text{Regularization term}}$$

The gap between $\log p_\theta(\mathbf{x})$ and $\mathcal{L}_{\text{ELBO}}$ is exactly $D_{\text{KL}}(q_\phi(\mathbf{z}|\mathbf{x}) \,\|\, p_\theta(\mathbf{z}|\mathbf{x}))$, the KL divergence between the approximate and true posterior. Tightening this bound requires a flexible encoder.

The reparameterization trick makes the expectation differentiable: instead of sampling $\mathbf{z} \sim q_\phi(\mathbf{z}|\mathbf{x}) = \mathcal{N}(\boldsymbol{\mu}_\phi(\mathbf{x}), \boldsymbol{\sigma}^2_\phi(\mathbf{x}))$ directly, we sample $\boldsymbol{\epsilon} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$ and compute $\mathbf{z} = \boldsymbol{\mu}_\phi(\mathbf{x}) + \boldsymbol{\sigma}_\phi(\mathbf{x}) \odot \boldsymbol{\epsilon}$. Gradients flow through $\boldsymbol{\mu}$ and $\boldsymbol{\sigma}$ via the deterministic transformation.

### 2.3 Generative Adversarial Networks (GANs)

GANs abandon explicit likelihood. The objective is a two-player minimax game:

$$\min_G \max_D \; V(D, G) = \mathbb{E}_{\mathbf{x} \sim p_{\text{data}}} \left[ \log D(\mathbf{x}) \right] + \mathbb{E}_{\mathbf{z} \sim p_{\mathcal{Z}}} \left[ \log(1 - D(G(\mathbf{z}))) \right]$$

At the global optimum, $D^*(\mathbf{x}) = \frac{p_{\text{data}}(\mathbf{x})}{p_{\text{data}}(\mathbf{x}) + p_G(\mathbf{x})}$ and $p_G = p_{\text{data}}$, at which point $D^*$ outputs $1/2$ everywhere and the value function equals $-\log 4$. This can be shown by substituting the optimal discriminator back into the value function, which yields:

$$C(G) = -\log(4) + 2 \cdot D_{\text{JS}}(p_{\text{data}} \,\|\, p_G)$$

where $D_{\text{JS}}$ is the Jensen-Shannon divergence. The minimizer is $D_{\text{JS}} = 0$, achieved when $p_G = p_{\text{data}}$.

In practice, the non-saturating generator loss $\mathbb{E}_{\mathbf{z}}[-\log D(G(\mathbf{z}))]$ is used instead of $\mathbb{E}_{\mathbf{z}}[\log(1 - D(G(\mathbf{z})))]$ to avoid vanishing gradients early in training when $D$ easily rejects generated samples.

### 2.4 Diffusion Models

Diffusion models define a forward noising process and learn to reverse it. The forward process is a fixed Markov chain:

$$q(\mathbf{x}_t | \mathbf{x}_{t-1}) = \mathcal{N}(\mathbf{x}_t; \sqrt{1 - \beta_t} \, \mathbf{x}_{t-1}, \beta_t \mathbf{I})$$

where $\{\beta_t\}_{t=1}^T$ is a variance schedule. A key property is that $\mathbf{x}_t$ can be sampled in closed form from $\mathbf{x}_0$:

$$q(\mathbf{x}_t | \mathbf{x}_0) = \mathcal{N}(\mathbf{x}_t; \sqrt{\bar{\alpha}_t} \, \mathbf{x}_0, (1 - \bar{\alpha}_t) \mathbf{I}), \quad \bar{\alpha}_t = \prod_{s=1}^{t} (1 - \beta_s)$$

The reverse process is parameterized as:

$$p_\theta(\mathbf{x}_{t-1} | \mathbf{x}_t) = \mathcal{N}(\mathbf{x}_{t-1}; \boldsymbol{\mu}_\theta(\mathbf{x}_t, t), \boldsymbol{\Sigma}_\theta(\mathbf{x}_t, t))$$

Training simplifies to a denoising score-matching objective. Ho et al. (2020) showed that the ELBO reduces to:

$$\mathcal{L}_{\text{simple}}(\theta) = \mathbb{E}_{t, \mathbf{x}_0, \boldsymbol{\epsilon}} \left[ \| \boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t) \|^2 \right]$$

where $\boldsymbol{\epsilon} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$ is the noise added to produce $\mathbf{x}_t$, and $\boldsymbol{\epsilon}_\theta$ is a network trained to predict that noise. This is remarkably simple: the model learns to predict the noise vector given a noisy image and the timestep.

### 2.5 Core Invariants Summary

| Model Family | Objective | Divergence Minimized | Tractable Likelihood | Training Stability |
|---|---|---|---|---|
| Autoregressive | $\sum_t \log p(x_t \mid x_{<t})$ | $D_{\text{KL}}(p_{\text{data}} \| p_\theta)$ | Yes | High |
| Flow | $\log p_\theta(\mathbf{x}) = \log p_{\mathcal{Z}}(f_\theta^{-1}(\mathbf{x})) + \log |\det J_{f_\theta^{-1}}|$ | $D_{\text{KL}}(p_{\text{data}} \| p_\theta)$ | Yes | High |
| VAE | ELBO (lower bound on $\log p_\theta$) | $D_{\text{KL}}(p_{\text{data}} \| p_\theta)$ (bounded) | Lower bound only | Moderate |
| GAN | Adversarial minimax | $D_{\text{JS}}(p_{\text{data}} \| p_G)$ | No | Low (mode collapse) |
| Diffusion | Denoising score matching | $D_{\text{KL}}(q \| p_\theta)$ (via ELBO) | Lower bound only | High |

---

## 3. High-Level Pipeline & Architecture Dataflow

### 3.1 General Generative Modeling Pipeline

```mermaid
graph LR
    A["Raw Dataset<br/>{x^1, ..., x^N}"] -->| "Preprocessing<br/>(normalize, augment)" | B["Training Set"]
    B -->| "Feed to model" | C["Generative Model<br/>(G, D, or ε_θ)"]
    C -->| "Optimize objective" | D["Trained Parameters θ"]
    D --> E{"Evaluation"}
    E -->| "Likelihood/FID/IS" | F["Quality Metrics"]
    E -->| "Visual inspection" | G["Sample Quality"]
    D -->| "Sample z ~ N(0,I)" | H["Generator Inference"]
    H --> I["Generated Samples"]
```

### 3.2 GAN Architecture Dataflow

```mermaid
graph TB
    subgraph sub_training_loop ["Training Loop"]
        Z["Latent z ~ N(0, I)"] -->| "G_θ(z)" | GX["Generated x_fake"]
        RD["Real data x_real"] --> DISC["Discriminator D_φ"]
        GX --> DISC
        DISC -->| "D(x) ∈ (0,1)" | LOSS["Adversarial Loss"]
        LOSS -->| "∇_θ (generator)" | GUPD["Update G_θ"]
        LOSS -->| "∇_φ (discriminator)" | DUPD["Update D_φ"]
        GUPD -.->| "Iterate" | Z
        DUPD -.->| "Iterate" | Z
    end
    subgraph sub_inference ["Inference"]
        Z2["z ~ N(0, I)"] -->| "G_θ(z)" | OUT["Generated sample"]
    end
```

### 3.3 VAE Architecture Dataflow

```mermaid
graph TB
    subgraph sub_encoder_q___z_x ["Encoder q_φ(z|x)"]
        X["Input x"] --> ENC["Encoder Network"]
        ENC --> MU["μ_φ(x)"]
        ENC --> SIGMA["σ_φ(x)"]
        EPS["ε ~ N(0, I)"] --> REPARAM["z = μ + σ ⊙ ε"]
        MU --> REPARAM
        SIGMA --> REPARAM
    end
    REPARAM -->| "z" | DEC["Decoder p_θ(x|z)"]
    DEC --> XHAT["Reconstruction x̂"]
    X -->| "Reconstruction loss" | LOSS["ELBO"]
    MU -->| "KL to prior N(0,I)" | KL["KL Divergence"]
    SIGMA --> KL
    KL --> LOSS
    XHAT --> LOSS
    LOSS -->| "Backprop" | ENC
    LOSS -->| "Backprop" | DEC
```

### 3.4 Diffusion Model Dataflow

```mermaid
graph TB
    subgraph sub_forward_process_q__fixed__no_lea ["Forward Process q (fixed, no learning)"]
        X0["x_0 (clean image)"] -->| "Add noise β_1" | X1["x_1"]
        X1 -->| "Add noise β_2" | X2["x_2"]
        X2 -->| "..." | XT["x_T (pure noise)"]
    end
    subgraph sub_reverse_process_p____learned ["Reverse Process p_θ (learned)"]
        XT2["x_T ~ N(0, I)"] -->| "Denoise step T" | U1["x_{T-1}"]
        U1 -->| "ε_θ(x_t, t)" | U2["x_{T-2}"]
        U2 -->| "..." | X0HAT["x_0 (generated)"]
    end
    subgraph sub_training_objective ["Training Objective"]
        X0TR["x_0"] -->| "Sample t, add noise ε" | XTN["x_t, ε"]
        XTN --> NET["U-Net ε_θ(x_t, t)"]
        NET --> PRED["Predicted ε̂"]
        EPS_TRUE["True ε"] --> MSE["‖ε - ε̂‖²"]
        PRED --> MSE
    end
```

---

## 4. Production-Grade Implementation

### 4.1 DCGAN in PyTorch (Working, Complete Example)

The original code used deprecated TensorFlow 1.x APIs (`tf.placeholder`, `tf.layers.dense`) and was non-functional. Below is a complete, runnable DCGAN implementation in PyTorch targeting the MNIST dataset.

```python
"""
DCGAN for MNIST — Complete training implementation.
Architecture follows Radford et al. (2016) guidelines:
  - Strided convolutions in discriminator, transposed convs in generator
  - BatchNorm in both networks (except final generator layer and first discriminator layer)
  - LeakyReLU(0.2) in discriminator, ReLU in generator, Tanh in final generator layer
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import numpy as np

# Hyperparameters
LATENT_DIM = 100
LR_G = 0.0002
LR_D = 0.0002
BETA1 = 0.5
BATCH_SIZE = 128
NUM_EPOCHS = 50
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Generator(nn.Module):
    """Maps latent z ∈ R^100 to 28×28 grayscale images."""
    def __init__(self, latent_dim: int = LATENT_DIM):
        super().__init__()
        self.net = nn.Sequential(
            # Project and reshape: (latent_dim,) -> (256, 7, 7)
            nn.Linear(latent_dim, 256 * 7 * 7),
            nn.BatchNorm1d(256 * 7 * 7),
            nn.ReLU(True),
            nn.Unflatten(1, (256, 7, 7)),
            # (256, 7, 7) -> (128, 14, 14)
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            # (128, 14, 14) -> (1, 28, 28)
            nn.ConvTranspose2d(128, 1, kernel_size=4, stride=2, padding=1),
            nn.Tanh(),  # Output in [-1, 1]
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)


class Discriminator(nn.Module):
    """Classifies 28×28 images as real (1) or fake (0)."""
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            # (1, 28, 28) -> (64, 14, 14)
            nn.Conv2d(1, 64, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            # (64, 14, 14) -> (128, 7, 7)
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=True),
            # Flatten and classify
            nn.Flatten(),
            nn.Linear(128 * 7 * 7, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(1)


def weights_init(m: nn.Module) -> None:
    """Initialize conv and batchnorm layers per DCGAN paper."""
    classname = m.__class__.__name__
    if isinstance(m, nn.Conv2d) or isinstance(m, nn.ConvTranspose2d):
        nn.init.normal_(m.weight.data, mean=0.0, std=0.02)
        if m.bias is not None:
            nn.init.constant_(m.bias.data, 0)
    elif isinstance(m, nn.BatchNorm2d):
        nn.init.normal_(m.weight.data, mean=1.0, std=0.02)
        nn.init.constant_(m.bias.data, 0)


def train_dcgan() -> None:
    # Data loading: normalize to [-1, 1] to match Tanh output
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,)),  # [0,1] -> [-1,1]
    ])
    dataset = torchvision.datasets.MNIST(
        root="./data", train=True, download=True, transform=transform
    )
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)

    G = Generator().to(DEVICE)
    D = Discriminator().to(DEVICE)
    G.apply(weights_init)
    D.apply(weights_init)

    opt_g = optim.Adam(G.parameters(), lr=LR_G, betas=(BETA1, 0.999))
    opt_d = optim.Adam(D.parameters(), lr=LR_D, betas=(BETA1, 0.999))
    criterion = nn.BCELoss()

    real_label = 1.0
    fake_label = 0.0

    for epoch in range(NUM_EPOCHS):
        for i, (real_imgs, _) in enumerate(dataloader):
            real_imgs = real_imgs.to(DEVICE)
            batch_size = real_imgs.size(0)

            # --- Train Discriminator: maximize log(D(x)) + log(1 - D(G(z))) ---
            D.zero_grad()
            # Real batch
            labels_real = torch.full((batch_size,), real_label, device=DEVICE)
            output_real = D(real_imgs)
            loss_d_real = criterion(output_real, labels_real)
            loss_d_real.backward()

            # Fake batch
            z = torch.randn(batch_size, LATENT_DIM, device=DEVICE)
            fake_imgs = G(z).detach()  # Detach to avoid updating G during D step
            labels_fake = torch.full((batch_size,), fake_label, device=DEVICE)
            output_fake = D(fake_imgs)
            loss_d_fake = criterion(output_fake, labels_fake)
            loss_d_fake.backward()

            loss_d = loss_d_real + loss_d_fake
            opt_d.step()

            # --- Train Generator: maximize log(D(G(z))) (non-saturating loss) ---
            G.zero_grad()
            labels_g = torch.full((batch_size,), real_label, device=DEVICE)  # Flip labels
            z = torch.randn(batch_size, LATENT_DIM, device=DEVICE)
            fake_imgs = G(z)
            output_g = D(fake_imgs)
            loss_g = criterion(output_g, labels_g)  # Non-saturating generator loss
            loss_g.backward()
            opt_g.step()

            if i % 200 == 0:
                print(
                    f"[Epoch {epoch}/{NUM_EPOCHS}] "
                    f"[Batch {i}/{len(dataloader)}] "
                    f"D_loss: {loss_d.item():.4f} "
                    f"G_loss: {loss_g.item():.4f}"
                )

    # Save a grid of generated samples
    G.eval()
    with torch.no_grad():
        z = torch.randn(64, LATENT_DIM, device=DEVICE)
        samples = G(z).cpu()
        grid = torchvision.utils.make_grid(samples, normalize=True, nrow=8)
        plt.imshow(np.transpose(grid, (1, 2, 0)), cmap="gray")
        plt.axis("off")
        plt.savefig("dcgan_samples.png", dpi=150, bbox_inches="tight")
        print("Saved generated samples to dcgan_samples.png")


if __name__ == "__main__":
    train_dcgan()
```

### 4.2 Evaluation Metrics (Corrected)

The original material suggested PSNR (Peak Signal-to-Noise Ratio) and SSIM (Structural Similarity Index). These are **reconstruction quality** metrics used in image restoration tasks, not generative model evaluation metrics. They require a paired reference image, which generative models do not produce — the entire point is to generate *new* samples, not reconstruct existing ones.

The standard generative model evaluation metrics are:

**Fréchet Inception Distance (FID)** — Extracts features from both real and generated image sets using a pretrained Inception-v3 network, then measures the Fréchet distance (Wasserstein-2) between the two Gaussian distributions in feature space:

$$\text{FID} = \|\boldsymbol{\mu}_r - \boldsymbol{\mu}_g\|^2 + \text{Tr}\left(\boldsymbol{\Sigma}_r + \boldsymbol{\Sigma}_g - 2(\boldsymbol{\Sigma}_r \boldsymbol{\Sigma}_g)^{1/2}\right)$$

Lower FID indicates better quality and diversity. It is the de facto standard for image generation.

**Inception Score (IS)** — Uses the same Inception network to measure both confidence of class predictions (quality) and entropy of the marginal class distribution (diversity):

$$\text{IS} = \exp\left(\mathbb{E}_{\mathbf{x}} \left[ D_{\text{KL}}\left(p(y|\mathbf{x}) \,\|\, p(y)\right) \right]\right)$$

Higher IS is better. IS does not compare against real data, making it less sensitive to mode collapse than FID.

**Precision and Recall (for distributions)** — Introduced by Kynäänniemi et al. (2019), these decompose quality (precision: do generated samples lie on the real data manifold?) from coverage (recall: does the generator cover the full real data manifold?).

```python
"""FID computation using torchmetrics (pip install torchmetrics torch-fidelity)."""

import torch
from torchmetrics.image.fid import FrechetInceptionDistance

def compute_fid(
    real_images: torch.Tensor,
    generated_images: torch.Tensor,
    feature_dim: int = 2048,
) -> float:
    """
    Compute Fréchet Inception Distance between real and generated image sets.

    Args:
        real_images: (N, 3, H, W) tensor in [0, 1], uint8 or float.
        generated_images: (M, 3, H, W) tensor in [0, 1], uint8 or float.
        feature_dim: Inception feature dimension (default 2048).

    Returns:
        FID score (lower is better).
    """
    fid = FrechetInceptionDistance(
        feature_dim=feature_dim,
        normalize=True,  # Expects [0,1] float input
        reset_real_features=True,
    )
    fid.update(real_images, real=True)
    fid.update(generated_images, real=False)
    return fid.compute().item()
```

### 4.3 Autoregressive Language Model (Minimal Transformer)

To demonstrate that generative AI extends well beyond GANs and VAEs, here is a minimal autoregressive transformer for text generation. This is the architecture class that powers GPT, LLaMA, Claude, and other large language models.

```python
"""
Minimal GPT-style autoregressive language model.
Demonstrates the explicit-density approach: p_θ(x) = Π_t p_θ(x_t | x_{<t}).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass


@dataclass
class ModelConfig:
    vocab_size: int = 256       # Byte-level tokenization
    d_model: int = 256
    n_heads: int = 8
    n_layers: int = 4
    max_seq_len: int = 512
    dropout: float = 0.1


class MultiHeadSelfAttention(nn.Module):
    """Causal (masked) multi-head self-attention."""
    def __init__(self, config: ModelConfig):
        super().__init__()
        assert config.d_model % config.n_heads == 0
        self.n_heads = config.n_heads
        self.d_head = config.d_model // config.n_heads
        self.qkv = nn.Linear(config.d_model, 3 * config.d_model, bias=False)
        self.proj = nn.Linear(config.d_model, config.d_model)
        self.dropout = nn.Dropout(config.dropout)

        # Causal mask: upper triangle = -inf
        mask = torch.triu(
            torch.ones(config.max_seq_len, config.max_seq_len) * float("-inf"),
            diagonal=1,
        )
        self.register_buffer("causal_mask", mask)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.shape
        qkv = self.qkv(x)  # (B, T, 3C)
        q, k, v = qkv.split(C, dim=-1)
        # Reshape to (B, n_heads, T, d_head)
        q = q.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        k = k.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        v = v.view(B, T, self.n_heads, self.d_head).transpose(1, 2)

        # Scaled dot-product attention with causal mask
        att = (q @ k.transpose(-2, -1)) / (self.d_head ** 0.5)
        att = att + self.causal_mask[:T, :T]
        att = F.softmax(att, dim=-1)
        att = self.dropout(att)

        out = att @ v  # (B, n_heads, T, d_head)
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        return self.dropout(self.proj(out))


class TransformerBlock(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.d_model)
        self.attn = MultiHeadSelfAttention(config)
        self.ln2 = nn.LayerNorm(config.d_model)
        self.ffn = nn.Sequential(
            nn.Linear(config.d_model, 4 * config.d_model),
            nn.GELU(),
            nn.Linear(4 * config.d_model, config.d_model),
            nn.Dropout(config.dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Pre-LayerNorm (GPT-2 style)
        x = x + self.attn(self.ln1(x))
        x = x + self.ffn(self.ln2(x))
        return x


class GPTModel(nn.Module):
    """
    Autoregressive language model.
    Log-likelihood: log p_θ(x) = Σ_t log p_θ(x_t | x_{<t}).
    Trained by maximizing this (equivalently, minimizing cross-entropy loss).
    """
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.token_emb = nn.Embedding(config.vocab_size, config.d_model)
        self.pos_emb = nn.Embedding(config.max_seq_len, config.d_model)
        self.blocks = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.n_layers)
        ])
        self.ln_f = nn.LayerNorm(config.d_model)
        self.head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        # Weight tying: output projection shares weights with token embedding
        self.head.weight = self.token_emb.weight

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        """
        Args:
            idx: (B, T) integer token indices.
        Returns:
            logits: (B, T, vocab_size) unnormalized log-probabilities.
        """
        B, T = idx.shape
        assert T <= self.config.max_seq_len

        pos = torch.arange(T, device=idx.device).unsqueeze(0)  # (1, T)
        x = self.token_emb(idx) + self.pos_emb(pos)  # (B, T, d_model)

        for block in self.blocks:
            x = block(x)

        x = self.ln_f(x)
        logits = self.head(x)  # (B, T, vocab_size)
        return logits

    def compute_loss(self, idx: torch.Tensor) -> torch.Tensor:
        """
        Standard autoregressive cross-entropy loss.
        Predicts token t+1 from tokens 0..t.
        """
        logits = self(idx[:, :-1])  # (B, T-1, V)
        targets = idx[:, 1:]        # (B, T-1)
        loss = F.cross_entropy(
            logits.reshape(-1, logits.size(-1)),
            targets.reshape(-1),
        )
        return loss

    @torch.no_grad()
    def sample(
        self,
        prompt: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_k: int | None = None,
    ) -> torch.Tensor:
        """Autoregressive sampling with optional top-k filtering."""
        self.eval()
        for _ in range(max_new_tokens):
            # Crop to max sequence length
            idx_cond = prompt if prompt.size(1) <= self.config.max_seq_len \
                else prompt[:, -self.config.max_seq_len:]
            logits = self(idx_cond)[:, -1, :] / temperature  # (B, V)

            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")

            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)  # (B, 1)
            prompt = torch.cat([prompt, next_token], dim=1)

        return prompt
```

---

## 5. Diffusion Model Implementation (U-Net Denoiser)

```python
"""
Minimal DDPM (Denoising Diffusion Probabilistic Model) in PyTorch.
Implements the simplified training objective from Ho et al. (2020).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class SinusoidalPositionEmbedding(nn.Module):
    """Embeds scalar timestep t into a vector of dimension d_model."""
    def __init__(self, d_model: int):
        super().__init__()
        self.d_model = d_model

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        # t: (B,) integer or float timesteps
        half = self.d_model // 2
        freqs = torch.exp(
            -np.log(10000) * torch.arange(half, device=t.device) / half
        )  # (d/2,)
        args = t[:, None].float() * freqs[None, :]  # (B, d/2)
        emb = torch.cat([torch.sin(args), torch.cos(args)], dim=-1)  # (B, d)
        return emb


class ResidualBlock(nn.Module):
    """U-Net residual block with timestep conditioning."""
    def __init__(self, in_ch: int, out_ch: int, time_dim: int):
        super().__init__()
        self.norm1 = nn.GroupNorm(8, in_ch)
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, padding=1)
        self.norm2 = nn.GroupNorm(8, out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1)
        self.time_mlp = nn.Linear(time_dim, out_ch)
        self.skip = nn.Conv2d(in_ch, out_ch, 1) if in_ch != out_ch else nn.Identity()

    def forward(self, x: torch.Tensor, t_emb: torch.Tensor) -> torch.Tensor:
        h = self.conv1(F.silu(self.norm1(x)))
        h = h + self.time_mlp(F.silu(t_emb))[:, :, None, None]
        h = self.conv2(F.silu(self.norm2(h)))
        return h + self.skip(x)


class SimpleUNet(nn.Module):
    """
    U-Net architecture for noise prediction ε_θ(x_t, t).
    Encoder-decoder with skip connections at each resolution.
    """
    def __init__(self, in_channels: int = 1, base_ch: int = 64, time_dim: int = 128):
        super().__init__()
        self.time_embed = nn.Sequential(
            SinusoidalPositionEmbedding(time_dim),
            nn.Linear(time_dim, time_dim * 4),
            nn.GELU(),
            nn.Linear(time_dim * 4, time_dim),
        )

        ch = [base_ch, base_ch * 2, base_ch * 4]

        # Encoder
        self.enc1 = ResidualBlock(in_channels, ch[0], time_dim)
        self.enc2 = ResidualBlock(ch[0], ch[1], time_dim)
        self.enc3 = ResidualBlock(ch[1], ch[2], time_dim)
        self.down = nn.MaxPool2d(2)

        # Bottleneck
        self.mid = ResidualBlock(ch[2], ch[2], time_dim)

        # Decoder
        self.up1 = nn.ConvTranspose2d(ch[2], ch[1], 2, stride=2)
        self.dec1 = ResidualBlock(ch[1] * 2, ch[1], time_dim)
        self.up2 = nn.ConvTranspose2d(ch[1], ch[0], 2, stride=2)
        self.dec2 = ResidualBlock(ch[0] * 2, ch[0], time_dim)

        self.out = nn.Conv2d(ch[0], in_channels, 1)

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        t_emb = self.time_embed(t)  # (B, time_dim)

        # Encoder
        h1 = self.enc1(x, t_emb)       # (B, ch0, H, W)
        h2 = self.enc2(self.down(h1), t_emb)  # (B, ch1, H/2, W/2)
        h3 = self.enc3(self.down(h2), t_emb)  # (B, ch2, H/4, W/4)

        # Bottleneck
        h = self.mid(h3, t_emb)

        # Decoder with skip connections
        h = self.up1(h)
        h = self.dec1(torch.cat([h, h3], dim=1), t_emb)
        h = self.up2(h)
        h = self.dec2(torch.cat([h, h2], dim=1), t_emb)

        return self.out(h)


class DDPM:
    """
    DDPM scheduler and training loop.
    Uses a linear variance schedule β_1...β_T.
    """
    def __init__(
        self,
        model: nn.Module,
        timesteps: int = 1000,
        beta_start: float = 1e-4,
        beta_end: float = 0.02,
        device: str = "cpu",
    ):
        self.model = model.to(device)
        self.T = timesteps
        self.device = device

        # Linear variance schedule
        self.betas = torch.linspace(beta_start, beta_end, timesteps, device=device)
        self.alphas = 1.0 - self.betas
        self.alpha_bars = torch.cumprod(self.alphas, dim=0)  # ᾱ_t

    def q_sample(
        self, x0: torch.Tensor, t: torch.Tensor, noise: torch.Tensor = None
    ) -> torch.Tensor:
        """Forward process: sample x_t from q(x_t | x_0)."""
        if noise is None:
            noise = torch.randn_like(x0)
        sqrt_ab = self.alpha_bars[t][:, None, None, None].sqrt()
        sqrt_1m_ab = (1 - self.alpha_bars[t])[:, None, None, None].sqrt()
        return sqrt_ab * x0 + sqrt_1m_ab * noise

    def training_step(self, x0: torch.Tensor, optimizer: torch.optim.Optimizer) -> float:
        """One training step: sample t, add noise, predict noise, MSE loss."""
        self.model.train()
        optimizer.zero_grad()

        B = x0.size(0)
        t = torch.randint(0, self.T, (B,), device=self.device, dtype=torch.long)
        noise = torch.randn_like(x0)
        x_t = self.q_sample(x0, t, noise)
        predicted_noise = self.model(x_t, t)
        loss = F.mse_loss(predicted_noise, noise)

        loss.backward()
        optimizer.step()
        return loss.item()

    @torch.no_grad()
    def sample(self, shape: tuple) -> torch.Tensor:
        """Reverse process: iteratively denoise from x_T ~ N(0, I)."""
        self.model.eval()
        x = torch.randn(shape, device=self.device)

        for t in reversed(range(self.T)):
            t_batch = torch.full((shape[0],), t, device=self.device, dtype=torch.long)
            predicted_noise = self.model(x, t_batch)

            alpha_t = self.alphas[t]
            alpha_bar_t = self.alpha_bars[t]
            beta_t = self.betas[t]

            # Posterior mean: μ_θ(x_t, t)
            mean = (1 / alpha_t.sqrt()) * (
                x - (beta_t / (1 - alpha_bar_t).sqrt()) * predicted_noise
            )

            if t > 0:
                noise = torch.randn_like(x)
                x = mean + beta_t.sqrt() * noise
            else:
                x = mean

        return x
```

---

## Exercises

1. **Derive the optimal discriminator.** Given the GAN value function $V(D, G)$, show that for a fixed generator $G$, the optimal discriminator is $D^*(\mathbf{x}) = \frac{p_{\text{data}}(\mathbf{x})}{p_{\text{data}}(\mathbf{x}) + p_G(\mathbf{x})}$. Then substitute $D^*$ back into $V$ to show the value function reduces to $C(G) = -\log 4 + 2 \, D_{\text{JS}}(p_{\text{data}} \| p_G)$.

2. **Implement and train a VAE** on the MNIST dataset using PyTorch. Use the reparameterization trick and compute both the reconstruction loss and KL divergence term. Experiment with different latent dimensions (2, 16, 64, 128) and plot the FID scores as a function of latent dimension. What dimension gives the best trade-off between reconstruction quality and latent compactness?

3. **Compare evaluation metrics.** Train a DCGAN and a VAE on the same dataset. Compute FID scores for both models using the `torchmetrics` implementation. Additionally, compute the Inception Score. Discuss: does IS correlate with FID? In what scenarios might they disagree, and why? Consider mode collapse as a confounding factor.

4. **Derive the ELBO decomposition.** Starting from $\log p_\theta(\mathbf{x}) \geq \mathcal{L}_{\text{ELBO}}$, show that the gap is $D_{\text{KL}}(q_\phi(\mathbf{z}|\mathbf{x}) \| p_\theta(\mathbf{z}|\mathbf{x}))$. Then show that the ELBO decomposes as $\mathcal{L}_{\text{ELBO}} = \mathbb{E}_{q_\phi}[\log p_\theta(\mathbf{x}|\mathbf{z})] - D_{\text{KL}}(q_\phi(\mathbf{z}|\mathbf{x}) \| p(\mathbf{z}))$. Interpret each term.

5. **Implement top-k sampling** for the GPT model. Add nucleus sampling (top-p) as well. Compare the output diversity of greedy, temperature, top-k, and top-p sampling strategies by generating 100 samples from each and computing the self-BLEU score or distinct-n metric.

6. **Train the DDPM** on MNIST (1000 timesteps, 50 epochs). Then reduce to 100 timesteps and compare FID. What happens to sample quality as you reduce timesteps? Explain the trade-off between sampling speed and quality, and discuss how DDIM (Denoising Diffusion Implicit Models) addresses this.
