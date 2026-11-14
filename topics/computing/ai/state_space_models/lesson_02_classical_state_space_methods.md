# Lesson 2: Classical State Space Methods

## 1. First-Principles Intuition & Invariants

Every sensor lies. Every physical process drifts. Every measurement arrives corrupted by noise that is irreducible in principle and expensive to attenuate in practice. Classical state space methods exist to answer a deceptively simple question: given a stream of noisy, partial observations of a dynamical system, what is the best estimate of the system's true hidden state at every point in time?

The answer turns out to depend on a precise characterization of two distinct phenomena that must never be conflated. The first is *process noise*: the inherent stochasticity in how the system itself evolves from one time step to the next. A satellite drifts under unmodeled atmospheric drag; a financial asset's volatility responds to unobserved market microstructure events; a robot's wheel slips on uneven terrain. The second is *measurement noise*: the corrupting influence of the sensor apparatus itself, which cannot observe the true state directly but instead produces a noisy projection of it. A classical state space model is precisely the mathematical apparatus that separates these two noise sources and exploits their statistical structure to produce estimates that are strictly better than either raw sensor readings or naive model predictions alone.

The formal framing is a linear dynamical system in discrete time. At each time step $t$, the latent state vector $\mathbf{x}_t \in \mathbb{R}^n$ evolves according to

$$\mathbf{x}_t = \mathbf{F}_t \mathbf{x}_{t-1} + \mathbf{B}_t \mathbf{u}_t + \mathbf{w}_t, \quad \mathbf{w}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{Q}_t)$$

and produces an observation $\mathbf{z}_t \in \mathbb{R}^m$ via

$$\mathbf{z}_t = \mathbf{H}_t \mathbf{x}_t + \mathbf{v}_t, \quad \mathbf{v}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{R}_t)$$

where $\mathbf{F}_t$ is the state transition matrix, $\mathbf{B}_t$ maps control inputs $\mathbf{u}_t$, $\mathbf{H}_t$ is the observation model, $\mathbf{Q}_t$ is the process noise covariance, and $\mathbf{R}_t$ is the measurement noise covariance. The Kalman filter's first invariant is that this model is a Gaussian linear system: the state prior, the transition noise, and the measurement noise are all Gaussian, which means the posterior over the state remains Gaussian at every time step, closed and analytically tractable. This is not merely a mathematical convenience. It is the structural property that makes exact inference possible in linear systems without Monte Carlo approximation.

The second invariant is the Markov property. The state $\mathbf{x}_t$ captures everything about the past that is relevant for predicting $\mathbf{x}_{t+1}$. Formally, $p(\mathbf{x}_t | \mathbf{x}_{1:t-1}, \mathbf{z}_{1:t-1}) = p(\mathbf{x}_t | \mathbf{x}_{t-1})$. This property transforms the global inference problem over an entire trajectory into a local two-step recursion: predict forward using the dynamics model, then correct using the incoming observation. Without the Markov property, every new observation would require reprocessing the entire history. With it, the filter's memory is completely encoded in the current state estimate and its covariance matrix.

Hidden Markov Models (HMMs) occupy a structurally related but fundamentally different position. Where the Kalman filter operates in continuous state spaces with Gaussian noise, HMMs model discrete latent states. At each time step, the system occupies one of $K$ hidden states $s_t \in \{1, \ldots, K\}$, transitions to a new state according to a stochastic matrix $A$ where $A_{ij} = p(s_t = j | s_{t-1} = i)$, and emits an observation according to an emission distribution $B_j(o_t) = p(o_t | s_t = j)$. The HMM enforces the same first-order Markov condition on the hidden state, but the inference machinery differs because marginalizing over discrete states requires summing over exponentially many paths rather than propagating Gaussian sufficient statistics.

Particle filters generalize both frameworks to the nonlinear, non-Gaussian regime. Where the Kalman filter tracks a Gaussian through linear transformations and the HMM tracks a categorical distribution through matrix multiplication, the particle filter tracks an arbitrary probability distribution through arbitrary dynamics by representing it as a weighted set of samples (particles). Each particle is a hypothesis about the system's current state, and the filter reweights hypotheses in proportion to how well they explain incoming observations, periodically resampling to prevent weight degeneracy. The formal guarantee is that as the particle count $N \to \infty$, the empirical particle distribution converges to the true posterior. At finite $N$, the approximation quality depends critically on the choice of proposal distribution and resampling strategy, which is where most practical engineering difficulty concentrates.

Understanding these three regimes — Gaussian linear, discrete Markov, and nonlinear particle-based — as a progressive relaxation of tractability assumptions is the organizing invariant of this entire lesson. Each step down the tractability ladder buys representational power at the cost of computational exactness, and each transition point reveals a new class of algorithmic decision the practitioner must make deliberately.

---

## 2. Core Architecture & Mechanics

### The Kalman Filter: Two-Phase Estimation

The Kalman filter is a recursive Bayesian estimator whose full state at any time step is completely described by two quantities: the posterior mean $\hat{\mathbf{x}}_{t|t}$ and the posterior covariance $\mathbf{P}_{t|t}$. The filter alternates between a prediction step, which propagates these quantities forward through the dynamics model, and an update step, which corrects them against the incoming observation.

```
  Prior at t-1                 Prediction Step               Measurement at t
  x̂_{t-1|t-1}, P_{t-1|t-1}  ──────────────────────►  x̂_{t|t-1}, P_{t|t-1}
                                                                │
                                                                │  z_t arrives
                                                                ▼
                                                       Kalman Gain K_t
                                                                │
                                                                ▼
                                                     Update Step
                                                     x̂_{t|t}, P_{t|t}  ──► next cycle
```

In the prediction step, the prior mean is propagated by the state transition:

$$\hat{\mathbf{x}}_{t|t-1} = \mathbf{F}_t \hat{\mathbf{x}}_{t-1|t-1} + \mathbf{B}_t \mathbf{u}_t$$

and the covariance inflates to account for the added process uncertainty:

$$\mathbf{P}_{t|t-1} = \mathbf{F}_t \mathbf{P}_{t-1|t-1} \mathbf{F}_t^\top + \mathbf{Q}_t$$

The update step computes the *innovation* — the discrepancy between what was observed and what the model predicted would be observed — and then corrects the prior proportionally to how informative the sensor is relative to the prediction uncertainty:

$$\tilde{\mathbf{y}}_t = \mathbf{z}_t - \mathbf{H}_t \hat{\mathbf{x}}_{t|t-1}$$

$$\mathbf{S}_t = \mathbf{H}_t \mathbf{P}_{t|t-1} \mathbf{H}_t^\top + \mathbf{R}_t$$

$$\mathbf{K}_t = \mathbf{P}_{t|t-1} \mathbf{H}_t^\top \mathbf{S}_t^{-1}$$

$$\hat{\mathbf{x}}_{t|t} = \hat{\mathbf{x}}_{t|t-1} + \mathbf{K}_t \tilde{\mathbf{y}}_t$$

$$\mathbf{P}_{t|t} = (\mathbf{I} - \mathbf{K}_t \mathbf{H}_t) \mathbf{P}_{t|t-1}$$

The Kalman gain $\mathbf{K}_t$ is the heart of the algorithm's optimality. When $\mathbf{R}_t$ is small (the sensor is precise), $\mathbf{S}_t \approx \mathbf{H}_t \mathbf{P}_{t|t-1} \mathbf{H}_t^\top$, and $\mathbf{K}_t \to \mathbf{H}_t^{-1}$, meaning the filter trusts the measurement almost completely. When $\mathbf{P}_{t|t-1}$ is small (the prediction is confident), $\mathbf{K}_t \to \mathbf{0}$, and the filter barely moves from its prior. This is not heuristic; it is the minimum mean-squared error (MMSE) estimator for Gaussian linear systems, provably optimal within that model class.

The following implementation is a production-grade NumPy Kalman filter with vectorized batch filtering support. It correctly handles numerically stable covariance updates using the Joseph form $(\mathbf{I} - \mathbf{K}\mathbf{H})\mathbf{P}(\mathbf{I} - \mathbf{K}\mathbf{H})^\top + \mathbf{K}\mathbf{R}\mathbf{K}^\top$ when numerical conditioning is critical.

```python
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KalmanFilter:
    """
    Linear Gaussian Kalman filter.

    State model:  x_t = F @ x_{t-1} + B @ u_t + w_t,  w_t ~ N(0, Q)
    Observation:  z_t = H @ x_t + v_t,                 v_t ~ N(0, R)

    Attributes:
        F: State transition matrix          (n, n)
        H: Observation model matrix         (m, n)
        Q: Process noise covariance         (n, n)
        R
