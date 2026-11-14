# Lesson 1: Markov Decision Processes, Value Functions, Bellman Equations

## 1. First-Principles Intuition & Invariants

Reinforcement learning is, at its core, a mathematical theory of sequential decision-making under uncertainty. Before any neural network architecture enters the picture, before any gradient flows through a policy head, there is a precisely defined formal framework that every practical RL algorithm implicitly solves. That framework is the Markov Decision Process. Understanding it deeply — not as a checklist of symbols but as a living mechanical substrate — is what separates engineers who tune hyperparameters from researchers who can diagnose why an algorithm diverges, design novel reward structures without introducing unintended incentives, and reason about sample complexity from first principles.

The fundamental problem RL addresses is this: an agent embedded in an environment must choose a sequence of actions over time, and the quality of those choices is not revealed immediately but only through the cumulative consequences that unfold across many time steps. This delayed credit assignment is the central difficulty. Supervised learning sidesteps it entirely by providing ground-truth labels at each data point. RL cannot. The agent must discover, through interaction, which early decisions are responsible for late rewards — a problem that is simultaneously statistical, computational, and dynamical.

### The Markov Property and Why It Enables Computation

The Markov Decision Process is defined by a tuple $(\mathcal{S}, \mathcal{A}, P, R, \gamma)$. Each component encodes a specific structural assumption about the world, and violating these assumptions in deployment is precisely how production RL systems fail silently.

The state space $\mathcal{S}$ can be finite, countably infinite, or a continuous manifold such as $\mathbb{R}^n$. The action space $\mathcal{A}$ similarly spans discrete vocabularies (chess moves, API calls, token selections) or continuous control domains (joint torques, steering angles). The transition kernel $P: \mathcal{S} \times \mathcal{A} \times \mathcal{S} \to [0,1]$ encodes the conditional probability $P(s' \mid s, a)$ — the probability that taking action $a$ in state $s$ leads to successor state $s'$. The reward function $R: \mathcal{S} \times \mathcal{A} \to \mathbb{R}$ assigns an immediate scalar signal to each state-action pair. The discount factor $\gamma \in [0, 1)$ geometrically attenuates future rewards.

The load-bearing assumption of the entire edifice is the **Markov property**: the transition distribution $P(s_{t+1} \mid s_t, a_t)$ depends only on the current state and action, not on any preceding history. Formally, $P(s_{t+1} \mid s_0, a_0, s_1, a_1, \ldots, s_t, a_t) = P(s_{t+1} \mid s_t, a_t)$. This is not a mild technical convenience — it is the axiom that makes dynamic programming tractable. Without it, the value of a state would be a function of unbounded history, and no finite representation could capture it.

In practice, the Markov property is never perfectly satisfied by raw sensory observations. A single video frame does not encode the velocity of objects; a single price tick does not encode market momentum; a single LIDAR scan does not encode whether a pedestrian is accelerating or decelerating. The engineering response is **state augmentation**: concatenating multiple frames (as in Atari DQN), appending velocity estimates computed by finite difference, or running a recurrent encoder that compresses history into a fixed-size latent vector. When you do this, you are constructing an approximate Markov state from non-Markov observations, and the quality of that approximation directly bounds the quality of the resulting policy.

### Policies, Stochasticity, and the Object We Are Optimizing

A **policy** $\pi$ is a decision rule that maps states to actions. A deterministic policy $\pi: \mathcal{S} \to \mathcal{A}$ assigns exactly one action to each state. A stochastic policy $\pi: \mathcal{S} \times \mathcal{A} \to [0,1]$ assigns a probability distribution over actions given a state, written $\pi(a \mid s)$. Stochastic policies are not merely a theoretical generalization; they are essential for exploration, they appear as the optimal solution in partially observable environments and in multi-agent settings with adversarial opponents, and they are the natural output of policy gradient methods.

The agent's objective is to find a policy that maximizes expected cumulative discounted reward. Given a starting state $s_0$ and a policy $\pi$, the **return** $G_t$ from time step $t$ onward is defined as the discounted sum of future rewards:

$$G_t = \sum_{k=0}^{\infty} \gamma^k R_{t+k+1}$$

The discount factor $\gamma$ does real work here. When $\gamma = 0$, the agent is purely myopic and optimizes only the immediate reward. When $\gamma \to 1$, all future rewards are weighted equally, and the sum may diverge for non-terminating episodes unless rewards are bounded. For episodic tasks with guaranteed termination, $\gamma = 1$ is often used. For continuing tasks, keeping $\gamma < 1$ ensures the return is finite with probability 1 provided rewards are bounded — specifically, $|G_t| \leq R_{\max} / (1 - \gamma)$.

This geometric bound is worth internalizing. At $\gamma = 0.99$, the effective time horizon of the agent (the number of steps beyond which rewards contribute less than 1% of their face value) is approximately $\log(0.01) / \log(0.99) \approx 458$ steps. Setting $\gamma$ is therefore an architectural decision about the agent's planning horizon, not merely a numerical regularizer.

---

## 2. Core Architecture & Mechanics

### Value Functions as the Fundamental Data Structure

Value functions are the central data structure of RL. They compress the expected future return of a state (or state-action pair) under a given policy into a single scalar, enabling the agent to compare states and make decisions without re-running full trajectory rollouts. Every major RL algorithm — dynamic programming, temporal difference learning, actor-critic architectures — either explicitly estimates value functions or implicitly computes objects equivalent to them.

The **state value function** under policy $\pi$ is defined as:

$$V^\pi(s) = \mathbb{E}_\pi \left[ G_t \mid s_t = s \right] = \mathbb{E}_\pi \left[ \sum_{k=0}^{\infty} \gamma^k R_{t+k+1} \;\middle|\; s_t = s \right]$$

The **action-value function** (Q-function) conditions on both the current state and the first action taken, then follows $\pi$ thereafter:

$$Q^\pi(s, a) = \mathbb{E}_\pi \left[ G_t \mid s_t = s, a_t = a \right]$$

The relationship between $V^\pi$ and $Q^\pi$ is immediate: $V^\pi(s) = \sum_a \pi(a \mid s) \, Q^\pi(s, a)$, which is the expectation of $Q^\pi$ under the policy's action distribution. This identity is mechanically important — it appears in the advantage function $A^\pi(s, a) = Q^\pi(s, a) - V^\pi(s)$, which measures how much better action $a$ is relative to the policy average. Advantage functions are the variance-reduction mechanism at the heart of actor-critic methods such as PPO and A3C.

### The Bellman Expectation Equations

The Bellman equations are consistency conditions on value functions. They express the fact that if $V^\pi$ is correct, then the value of a state must equal the expected immediate reward plus the discounted value of the successor state — both expectations taken under the policy and transition dynamics. For the state value function:

$$V^\pi(s) = \sum_a \pi(a \mid s) \sum_{s'} P(s' \mid s, a) \left[ R(s, a) + \gamma V^\pi(s') \right]$$

For the action-value function:

$$Q^\pi(s, a) = \sum_{s'} P(s' \mid s, a) \left[ R(s, a) + \gamma \sum_{a'} \pi(a' \mid s') Q^\pi(s', a') \right]$$

These are not recursive definitions to be feared — they are simultaneous linear equations. For a finite MDP with $|\mathcal{S}|$ states and $|\mathcal{A}|$ actions, the Bellman equations for $V^\pi$ form a system of $|\mathcal{S}|$ linear equations in $|\mathcal{S}|$ unknowns. Under the discount $\gamma < 1$, the coefficient matrix $(I - \gamma P^\pi)$ is strictly diagonally dominant and therefore invertible, guaranteeing a unique solution: $V^\pi = (I - \gamma P^\pi)^{-1} R^\pi$. For small state spaces, you can compute this directly. For the large or continuous state spaces that characterize practical problems, you approximate.

### The Bellman Optimality Equations

The Bellman expectation equations characterize the value of a fixed policy. The Bellman optimality equations characterize the value of the **optimal policy** $\pi^*$, the policy that maximizes expected return from every state simultaneously:

$$V^*(s) = \max_a \sum_{s'} P(s' \mid s, a) \left[ R(s, a) + \gamma V^*(s') \right]$$

$$Q^*(s, a) = \sum_{s'} P(s' \mid s, a) \left[ R(s, a) + \gamma \max_{a'} Q^*(s', a') \right]$$

The critical structural difference from the expectation equations is the replacement of the expectation over $\pi(a \mid s)$ with a maximization over $a$. This converts the linear system into a nonlinear fixed-point problem. The right-hand side of the $V^*$ equation defines the **Bellman optimality operator** $\mathcal{T}^*$:

$$(\mathcal{T}^* V)(s) = \max_a \sum_{s'} P(s' \mid s, a) \left[ R(s, a) + \gamma V(s') \right]$$

This operator is a **contraction mapping** in the sup-norm $\|\cdot\|_\infty$ with contraction factor $\gamma$. That is, for any two value function estimates $V$ and $U$:

$$\|\mathcal{T}^* V - \mathcal{T}^* U\|_\infty \leq \gamma \|V - U\|_\infty$$

By the Banach fixed-point theorem, repeated application of $\mathcal{T}^*$ to any initial value function estimate converges to $V^*$ at a geometric rate. This is the theoretical foundation for **value iteration**, the simplest dynamic programming algorithm. The contraction factor $\gamma$ directly controls convergence speed: at $\gamma = 0.99$, errors decay by only 1% per iteration, requiring hundreds of sweeps to converge, whereas $\gamma = 0.9$ achieves 10% error reduction per iteration.

### Execution Flow: Dynamic Programming in a Finite MDP

The following diagram captures the data flow of value iteration in a finite MDP, where the transition model $P$ and reward function $R$ are known.

```
┌─────────────────────────────────────────────────────────────┐
│                    VALUE ITERATION LOOP                     │
│                                                             │
│  Initialize V(s) = 0 for all s ∈ S                         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  For each state s ∈ S:                               │  │
│  │                                                      │  │
│  │   For each action a ∈ A:                             │  │
│  │     Q(s,a) = Σ P(s'|s,a) · [R(s,a) + γ·V(s')]      │  │
│  │              s'                                      │  │
│  │                                                      │  │
│  │   V_new(s) = max Q(s,a)                              │  │
│  │               a                                      │  │
│  └───────────────────────┬──────────────────────────────┘  │
│                          │                                  │
│          δ = max |V_new(s) - V(s)|                          │
│               s                                             │
│                          │                                  │
│          ┌───────────────┴───────────────┐                  │
│          │ δ < ε ?                       │                  │
│          │  YES → extract π*(s)=argmax Q │                  │
│          │  NO  → V ← V_new, repeat      │                  │
│          └───────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

Each full pass over all states constitutes one **sweep** of value iteration. The convergence criterion $\delta = \max_s |V_{\text{new}}(s) - V(s)| < \varepsilon$ is checked after each sweep. Once $V^*$ is computed to within $\varepsilon$, the greedy policy $\pi^*(s) = \arg\max_a Q^*(s, a)$ is extracted in a single pass and is guaranteed to be $\varepsilon/(1-\gamma)$-optimal.

### Implementing a Tabular MDP Solver

The following is a complete, production-grade Python implementation of an exact MDP solver with both policy evaluation and value iteration. It operates on dense NumPy arrays for vectorized Bellman backup computation — a design that scales to state spaces of several hundred thousand states before memory pressure becomes the binding constraint.

```python
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class MDP:
    """
    Finite Markov Decision Process.

    P: transition tensor of shape (S, A, S) where P[s, a, s'] = P(s'|s,a)
    R: reward matrix of shape (S, A) where R[s,a] = E[r | s,a]
    gamma: discount factor in [0, 1)
    """
    P: np.ndarray      # (S, A, S)
    R: np.ndarray      # (S, A)
    gamma: float

    def __post_init__(self):
        S, A, Sp = self.P.shape
        assert S == Sp, "Transition tensor must be square in state dimensions."
        assert self.R.shape == (S, A), "Reward matrix shape must match (S, A)."
        assert 0.0 <= self.gamma < 1.0, "Discount factor must be in [0, 1)."
        # Verify stochasticity: each row of P must sum to 1.
        row_sums = self.P.sum(axis=2)
        assert np.allclose(row_sums, 1.0, atol=1e-6), (
            "Transition tensor rows must be valid probability distributions."
        )

    @property
    def n_states(self) -> int:
        return self.P.shape[0]

    @property
    def n_actions(self) -> int:
        return self.P.shape[1]


def bellman_backup(mdp: MDP, V: np.ndarray) -> np.ndarray:
    """
    Compute one full Bellman optimality backup over all (s, a) pairs.

    For each (s, a), computes Q(s,a) = sum_{s'} P(s'|s,a) * [R(s,a) + gamma * V(s')]
    using vectorized einsum for efficiency, then returns max_a Q(s,a).

    Returns V_new of shape (S,).
    """
    # Q[s, a] = sum_{s'} P[s, a, s'] * (R[s, a] + gamma * V[s'])
    # Equivalent to: R + gamma * (P @ V), computed per (s,a) pair.
    # P has shape (S, A, S), V has shape (S,), so P @ V contracts last dim of P with V.
    future = np.einsum('ijk,k->ij', mdp.P, V)   # shape: (S, A)
    Q = mdp.R + mdp.gamma * future               # shape: (S, A)
    return Q.max(axis=1), Q                      # V_new: (S,), Q: (S, A)


def value_iteration(
    mdp: MDP,
    epsilon: float = 1e-8,
    max_iterations: int = 10_000,
) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Solve MDP via value iteration.

    Converges when max_s |V_new(s) - V(s)| < epsilon * (1 - gamma) / (2 * gamma),
    which guarantees the extracted greedy policy is epsilon-optimal.

    Returns (V_star, pi_star, iterations_to_convergence).
    """
    S = mdp.n_states
    V = np.zeros(S, dtype=np.float64)

    # Convergence threshold from Puterman (1994): guarantees epsilon-optimality
    # of the greedy policy extracted from the converged value function.
    convergence_threshold = epsilon * (1.0 - mdp.gamma) / (2.0 * mdp.gamma)

    for iteration in range(1, max_iterations + 1):
        V_new, Q = bellman_backup(mdp, V)
        delta = np.max(np.abs(V_new - V))
        V = V_new

        if delta < convergence_threshold:
            pi_star = Q.argmax(axis=1)   # greedy policy: (S,)
            return V, pi_star, iteration

    raise RuntimeError(
        f"Value iteration did not converge within {max_iterations} iterations. "
        f"Final delta: {delta:.6e}. Consider increasing max_iterations or "
        f"checking the MDP specification for absorbing states without self-loops."
    )


def policy_evaluation(
    mdp: MDP,
    policy: np.ndarray,
    epsilon: float = 1e-8,
    max_iterations: int = 10_000,
) -> np.ndarray:
    """
    Compute V^pi exactly for a given deterministic policy via iterative application
    of the Bellman expectation operator.

    policy: integer array of shape (S,) where policy[s] is the action taken in s.
    Returns V_pi of shape (S,).
    """
    S = mdp.n_states
    V = np.zeros(S, dtype=np.float64)

    # Extract the transition and reward slices induced by the fixed policy.
    # P_pi[s, s'] = P[s, policy[s], s']  — shape (S, S)
    # R_pi[s]     = R[s, policy[s]]      — shape (S,)
    state_indices = np.arange(S)
    P_pi = mdp.P[state_indices, policy, :]   # (S, S)
    R_pi = mdp.R[state_indices, policy]      # (S,)

    convergence_threshold = epsilon * (1.0 - mdp.gamma) / (2.0 * mdp.gamma)

    for _ in range(max_iterations):
        V_new = R_pi + mdp.gamma * P_pi @ V
        delta = np.max(np.abs(V_new - V))
        V = V_new
        if delta < convergence_threshold:
            return V

    raise RuntimeError("Policy evaluation did not converge.")


def policy_iteration(
    mdp: MDP,
    epsilon: float = 1e-8,
) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Solve MDP via policy iteration: alternates between exact policy evaluation
    and greedy policy improvement until the policy is stable.

    Policy iteration converges in at most |A|^|S| iterations (finite policy space),
    but in practice converges in far fewer steps than value iteration for most MDPs.

    Returns (V_star, pi_star, policy_improvement_steps).
    """
    S = mdp.n_states
    # Initialize with the uniform-random deterministic policy (action 0 everywhere).
    pi = np.zeros(S, dtype=np.int64)

    for step in range(1, S * mdp.n_actions + 2):
        V_pi = policy_evaluation(mdp, pi, epsilon=epsilon)

        # Greedy improvement: recompute Q under V_pi and extract argmax.
        future = np.einsum('ijk,k->ij', mdp.P, V_pi)
        Q_pi = mdp.R + mdp.gamma * future
        pi_new = Q_pi.argmax(axis=1)

        if np.array_equal(pi_new, pi):
            return V_pi, pi, step

        pi = pi_new

    raise RuntimeError("Policy iteration failed to converge — check MDP validity.")
```

This implementation encodes several subtleties worth examining explicitly. The convergence threshold in `value_iteration` uses the Puterman bound $\varepsilon (1-\gamma)/(2\gamma)$ rather than the raw $\varepsilon$, ensuring the extracted greedy policy is $\varepsilon$-optimal in return, not merely $\varepsilon$-close in value norm. The `bellman_backup` function uses `np.einsum` to contract the transition tensor against the value vector in a single vectorized operation, avoiding Python loops over states. For an MDP with $|\mathcal{S}| = 10^4$ states and $|\mathcal{A}| = 100$ actions, the transition tensor occupies $10^4 \times 100 \times 10^4 \times 8$ bytes = 80 GB — which immediately reveals the fundamental scalability wall of tabular methods and motivates function approximation.

---

## 3. High-Performance Optimization & Failure Modes

### Scaling the Bellman Computation: Sparse Transitions and Vectorization

For most real MDPs, the transition tensor $P$ is sparse: from any given state-action pair, only a small number of successor states have nonzero probability. A robotic navigation grid has at most 4–8 reachable successor states per cell. A game tree has bounded branching factor. Only fully connected stochastic systems like financial models have dense transitions. This sparsity structure is exploitable: representing $P$ as a sparse matrix (SciPy CSR format for the matrix-vector product $P^\pi V$) reduces both memory footprint and compute from $O(|\mathcal{S}|^2)$ to $O(|\mathcal{S}| \cdot \bar{b})$ where $\bar{b}$ is the average branching factor.

```python
import scipy.sparse as sp

def build_sparse_policy_matrix(mdp: MDP, policy: np.ndarray) -> sp.csr_matrix:
    """
    Construct the sparse transition matrix P_pi induced by a deterministic policy.
    P_pi[s, s'] = P[s, policy[s], s']

    For a grid world of 10^6 states with average branching factor 4,
    this reduces memory from 8 TB (dense) to ~32 MB (sparse CSR).
    """
    S = mdp.n_states
    rows, cols, data = [], [], []

    for s in range(S):
        a = policy[s]
        for sp_idx in range(S):
            prob = mdp.P[s, a, sp_idx]
            if prob > 0.0:
                rows.append(s)
                cols.append(sp_idx)
                data.append(prob)

    return sp.csr_matrix((data, (rows, cols)), shape=(S, S))
```

For state spaces too large even for sparse tabular representation, the transition model must be replaced by a **learned or implicit model** (as in model-based RL) or discarded entirely (as in model-free RL). In that regime, the Bellman equations are still the theoretical object being solved, but they are approximated via sampled backups: the TD(0) update $V(s_t) \leftarrow V(s_t) + \alpha \left[ r_{t+1} + \gamma V(s_{t+1}) - V(s_t) \right]$ is a stochastic approximation of a single Bellman backup, substituting an observed transition $(s_t, a_t, r_{t+1}, s_{t+1})$ for the full expectation over $P$.

### Critical Failure Modes in MDP Formulation

The most consequential failure mode in applied RL is not algorithmic — it is **reward misspecification**. The Bellman optimality equations find the exact solution to the MDP you specified. If your reward function does not faithfully encode your intent, you will obtain a policy that maximizes the specified reward and violates your intent, often in spectacular and unforeseen ways. This is not a failure of the algorithm; it is a failure of the MDP formulation.

A second structural failure mode is **partial observability masquerading as full observability**. When the true state is not Markov in the observations fed to the agent — because critical information is missing, noisy, or delayed — value function estimates become inconsistent. The agent may appear to converge during training (the TD error decreases) while actually fitting a smooth interpolation over aliased states rather than a true value function. The diagnostic symptom is high variance in evaluation returns despite low TD error. The correct response is state augmentation, recurrent state encoders, or reformulating the problem as a Partially Observable MDP (POMDP).

Discount factor miscalibration is a subtler failure. Setting $\gamma$ too close to 1 in continuing tasks without guaranteed absorption causes the value function to scale as $R_{\max}/(1-\gamma)$, which for $\gamma = 0.999$ and $R_{\max} = 1$ places values in the range $[0, 1000]$. When a neural network approximates $V^*$ in this regime, the output layer must represent values orders of magnitude larger than the input features, creating training instability. Reward scaling — normalizing rewards by a running estimate of the return standard deviation, as implemented in OpenAI's PPO baselines — addresses this symptom. The root cause is the interaction between $\gamma$, the effective time horizon, and the numeric range of the value estimator.

Absorbing state handling is a constant source of bugs. Many RL environments use a terminal flag `done=True` to signal episode end, and the Bellman backup for a terminal state must be $Q(s_{\text{term}}, a) = R(s_{\text{term}}, a)$ — the future value is zero because no future rewards will be collected. Failing to mask the bootstrap target in terminal states produces the error $Q(s_{\text{term}}, a) = R(s_{\text{term}}, a) + \gamma V(s')$ where $s'$ is the initial state of the next episode (a reset artifact). This contaminates the value estimate with cross-episode information and is among the most common bugs in replay-buffer-based implementations.

```python
def td_target(
    reward: np.ndarray,
    next_value: np.ndarray,
    done: np.ndarray,
    gamma: float,
) -> np.ndarray:
    """
    Compute bootstrapped TD targets for a batch of transitions.

    reward:     (B,) observed rewards
    next_value: (B,) V(s_{t+1}) or max_a Q(s_{t+1}, a) from target network
    done:       (B,) boolean mask: True if s_{t+1} is terminal
    gamma:      discount factor

    The (1 - done) mask zeros out the bootstrap term for terminal transitions,
    correctly implementing the absorbing-state boundary condition.
    """
    return reward + gamma * next_value * (1.0 - done.astype(np.float64))
```

### The Relationship Between Bellman Equations and Modern Deep RL

Every major deep RL algorithm is an approximation scheme applied to the Bellman equations. DQN parameterizes $Q^*(s, a)$ with a neural network $Q_\theta$ and minimizes the squared Bellman residual $\left( Q_\theta(s, a) - \mathcal{T}^* Q_{\theta^-}(s, a) \right)^2$ where $\theta^-$ is a periodically copied target network. The target network exists because using the same parameters $\theta$ for both sides of the Bellman equation makes the target non-stationary in a way that causes divergence — a direct consequence of the fact that $\mathcal{T}^*$ is a contraction in the tabular case but gradient descent on the Bellman residual with a function approximator does not preserve this contraction property.

Policy gradient methods such as PPO do not explicitly solve the Bellman equations for $Q^*$, but they estimate the advantage function $A^\pi(s, a)$ using Generalized Advantage Estimation, which is a weighted average of multi-step Bellman residuals indexed by a parameter $\lambda \in [0, 1]$ that interpolates between one-step TD ($\lambda = 0$) and Monte Carlo ($\lambda = 1$). Actor-critic methods maintain both a policy network and a separate critic network that solves the Bellman expectation equation for $V^\pi$ under the current policy, feeding its estimates back into the policy gradient update.

The Bellman equations are therefore not an introductory warmup before the real material — they are the entire theoretical substrate. The choice of which Bellman equation to solve (expectation vs. optimality), how to parameterize the value function, how to stabilize the bootstrap target, and how to handle the deadly triad of off-policy learning, function approximation, and bootstrapping are the questions that define the architecture of every production RL system in deployment today.
