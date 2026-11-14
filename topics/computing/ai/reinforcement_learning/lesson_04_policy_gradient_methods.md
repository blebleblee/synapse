# Lesson 4: Policy Gradient Theorem, Actor-Critic Methods, Variance Reduction

## 1. First-Principles Intuition & Invariants

The fundamental tension at the heart of reinforcement learning is a question of representation: should the agent learn *what the world is worth*, or should it learn *what to do directly*? Value-based methods like Q-learning answer the first question and derive behavior as a byproduct. Policy gradient methods answer the second question directly, parameterizing the policy itself and optimizing it through gradient ascent on expected return. This distinction is not merely aesthetic. It defines which problem classes are tractable, which failure modes dominate, and which mathematical machinery governs training stability.

Value-based methods impose an implicit constraint: the policy must be derivable from a value function, typically through a greedy or softmax operator. For discrete action spaces this is workable. For continuous action spaces, like the torque applied to a robot joint or the steering angle of an autonomous vehicle, the greedy operation $\arg\max_{a} Q(s,a)$ requires solving a continuous optimization problem at every environment step, which is computationally prohibitive. Policy gradient methods sidestep this entirely by representing the policy as a differentiable function $\pi_\theta(a \mid s)$, parameterized by $\theta$, and optimizing $\theta$ directly. The continuous action case falls out naturally: a Gaussian policy $\mathcal{N}(\mu_\theta(s), \sigma^2)$ over action space $\mathbb{R}^d$ requires no inner optimization loop at inference time.

The objective function that policy gradient methods optimize is the expected discounted return:

$$J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T} \gamma^t r_t\right]$$

where $\tau = (s_0, a_0, r_0, s_1, a_1, r_1, \ldots)$ is a trajectory sampled by executing $\pi_\theta$ in the environment, and $\gamma \in [0,1)$ is the discount factor. The challenge is that $J(\theta)$ is an expectation over trajectories whose distribution depends on $\theta$ through both the action probabilities and the induced state visitation distribution. Differentiating through the environment dynamics is generally impossible: the transition function $p(s' \mid s, a)$ is unknown, stochastic, or not differentiable. The policy gradient theorem resolves this by producing an estimator for $\nabla_\theta J(\theta)$ that requires differentiating only through $\pi_\theta$, not through the environment.

### The Log-Derivative Trick and the Policy Gradient Theorem

The derivation of the policy gradient theorem begins with the REINFORCE identity, also known as the log-derivative trick or the likelihood ratio trick. The core observation is that for any differentiable probability distribution $p_\theta(x)$ and function $f(x)$:

$$\nabla_\theta \mathbb{E}_{x \sim p_\theta}[f(x)] = \mathbb{E}_{x \sim p_\theta}\left[f(x) \nabla_\theta \log p_\theta(x)\right]$$

This identity holds because $\nabla_\theta p_\theta(x) = p_\theta(x) \nabla_\theta \log p_\theta(x)$, allowing the gradient to pass inside the expectation and be estimated by Monte Carlo sampling. Applied to trajectories, the log-probability of a trajectory under $\pi_\theta$ decomposes as:

$$\log p_\theta(\tau) = \log p(s_0) + \sum_{t=0}^{T} \left[\log \pi_\theta(a_t \mid s_t) + \log p(s_{t+1} \mid s_t, a_t)\right]$$

The initial state distribution $\log p(s_0)$ and the transition log-probabilities $\log p(s_{t+1} \mid s_t, a_t)$ carry no dependence on $\theta$, so their gradients vanish. The policy gradient theorem therefore states:

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t \mid s_t) \cdot G_t\right]$$

where $G_t = \sum_{t'=t}^{T} \gamma^{t'-t} r_{t'}$ is the return from time $t$ onward. This is the REINFORCE estimator, introduced by Williams in 1992. Its beauty is that it requires no model of the environment and applies to any differentiable policy. Its practical liability is severe variance: $G_t$ is a sum of future rewards along a stochastic trajectory, and the product of this noisy scalar with the policy gradient direction produces an estimator with variance that grows with horizon length. Training with raw REINFORCE on any nontrivial problem produces gradient estimates so noisy that learning either stalls or diverges.

### Baselines and the Causality of Reward

Two structural improvements make REINFORCE usable in practice before actor-critic methods are introduced. The first is causality. Because actions at time $t$ cannot influence rewards before time $t$, the full trajectory return $G$ can be replaced by the future return $G_t$ without introducing bias. This eliminates the variance contribution of past rewards, which is an exact zero-bias reduction.

The second improvement is a baseline. Any function $b(s_t)$ that depends only on the current state can be subtracted from the return signal without introducing bias into the gradient estimator:

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t \mid s_t) \cdot (G_t - b(s_t))\right]$$

The unbiasedness follows from the fact that $\mathbb{E}_{a_t \sim \pi_\theta(\cdot \mid s_t)}[\nabla_\theta \log \pi_\theta(a_t \mid s_t)] = 0$ for any normalized distribution. The optimal baseline that minimizes estimator variance is proportional to $\mathbb{E}[G_t^2 \|\nabla_\theta \log \pi_\theta(a_t \mid s_t)\|^2] / \mathbb{E}[\|\nabla_\theta \log \pi_\theta(a_t \mid s_t)\|^2]$, but this is expensive to compute. In practice, a learned value function $V_\phi(s_t) \approx \mathbb{E}_\pi[G_t \mid s_t]$ serves as an excellent baseline. The term $G_t - V_\phi(s_t)$ is called the **advantage** of action $a_t$ in state $s_t$: it measures how much better this particular action was than the average action the policy would have taken.

The advantage function is the conceptual bridge to actor-critic methods. When we learn a parameterized critic to estimate $V^\pi(s)$ alongside the actor that represents $\pi_\theta$, we have entered the actor-critic architecture. The critic's role is not to drive behavior directly but to reduce the variance of the actor's gradient estimates by replacing noisy Monte Carlo returns with lower-variance bootstrapped estimates.

---

## 2. Core Architecture & Mechanics

### The Advantage Function and Critic Estimation

The advantage of an action is defined formally as:

$$A^\pi(s, a) = Q^\pi(s, a) - V^\pi(s)$$

where $Q^\pi(s,a) = \mathbb{E}_\pi\left[\sum_{t=0}^\infty \gamma^t r_t \mid s_0=s, a_0=a\right]$ is the action-value function and $V^\pi(s) = \mathbb{E}_{a \sim \pi}[Q^\pi(s,a)]$ is its expectation under the policy. A positive advantage means the chosen action outperforms the policy's average; a negative advantage means it underperforms. The policy gradient expressed in terms of the advantage is:

$$\nabla_\theta J(\theta) = \mathbb{E}_{s,a \sim \pi_\theta}\left[\nabla_\theta \log \pi_\theta(a \mid s) \cdot A^\pi(s, a)\right]$$

Computing $A^\pi(s,a)$ exactly requires knowing $Q^\pi$ and $V^\pi$, which are themselves unknown. Actor-critic methods estimate the advantage using a parameterized value function $V_\phi(s)$ as the critic, combined with reward samples from the environment. The standard estimator is the TD residual (one-step advantage):

$$\hat{A}_t^{(1)} = r_t + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)$$

This is the Bellman error of $V_\phi$ along the observed transition. It trades some bias (because $V_\phi$ is imperfect) for a substantial reduction in variance compared to the Monte Carlo return. The bias-variance tradeoff is controlled by the $n$-step return, which generalizes between TD(0) and Monte Carlo:

$$\hat{A}_t^{(n)} = \sum_{k=0}^{n-1} \gamma^k r_{t+k} + \gamma^n V_\phi(s_{t+n}) - V_\phi(s_t)$$

As $n \to \infty$, $\hat{A}_t^{(n)}$ approaches the full Monte Carlo advantage. Generalized Advantage Estimation (GAE), introduced by Schulman et al. in 2015, exponentially weights the $n$-step advantages with a parameter $\lambda \in [0,1]$:

$$\hat{A}_t^{\text{GAE}(\gamma, \lambda)} = \sum_{k=0}^{\infty} (\gamma \lambda)^k \delta_{t+k}$$

where $\delta_t = r_t + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)$ is the TD residual at step $t$. When $\lambda = 0$, GAE reduces to the one-step TD advantage, with low variance and high bias. When $\lambda = 1$, GAE recovers the Monte Carlo advantage, unbiased but high variance. In practice, $\lambda \in [0.92, 0.98]$ provides a productive middle ground for most continuous control tasks.

### Actor-Critic Data Flow and Network Architecture

A complete actor-critic system consists of four interacting components: a policy network (actor), a value network (critic), a rollout buffer, and a gradient computation graph. The actor and critic can share a common trunk of feature extraction layers with separate output heads, or they can be entirely independent networks. Shared architectures reduce computation and can improve sample efficiency through multitask representation learning, but they introduce gradient interference: the value loss and the policy loss operate on different scales, and without careful normalization they will corrupt each other.

The following diagram shows the data flow through one training iteration:

```
Environment
     │  (s_t, r_t, done_t)
     ▼
┌─────────────────────────────────┐
│          Rollout Buffer         │
│  stores T steps of              │
│  (s, a, r, s', log_π(a|s))     │
└──────────────┬──────────────────┘
               │
     ┌─────────┴──────────┐
     ▼                    ▼
┌─────────┐          ┌──────────┐
│  Actor  │          │  Critic  │
│ π_θ(a|s)│          │  V_φ(s)  │
└────┬────┘          └────┬─────┘
     │                    │
     │   Compute GAE      │
     │  Â_t = Σ(γλ)^k δ_k │
     └────────┬───────────┘
              │
     ┌────────▼────────┐
     │  Policy Loss    │       ┌─────────────────────────┐
     │  L_π = -E[     │       │  Value Loss             │
     │   log π(a|s)·Â]│       │  L_V = E[(V_φ(s)-G_t)²]│
     └────────┬────────┘       └───────────┬─────────────┘
              │                            │
              └──────────┬─────────────────┘
                         │
              ┌──────────▼──────────┐
              │  Combined Gradient  │
              │  ∇L = ∇L_π + c·∇L_V│
              │      - β·∇H[π]     │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │   Adam / RMSProp    │
              │   θ ← θ - α∇_θ L   │
              │   φ ← φ - α∇_φ L_V │
              └─────────────────────┘
```

The entropy bonus $H[\pi_\theta] = -\mathbb{E}[\log \pi_\theta(a \mid s)]$ is added to the objective with coefficient $\beta$ to prevent premature policy collapse, where the policy becomes deterministic before adequate exploration has occurred. It acts as a regularizer that keeps the action distribution spread across viable options.

### Proximal Policy Optimization: Constraining the Trust Region

Vanilla policy gradient updates have an instability rooted in the fact that a large gradient step can move $\theta$ into a region where $\pi_\theta$ is drastically different from the rollout policy, invalidating the advantage estimates computed under the old policy. TRPO (Trust Region Policy Optimization) addresses this by constraining each update to lie within a KL-divergence ball around the old policy, but its second-order optimization requires computing and inverting the Fisher information matrix, which is computationally prohibitive for large networks.

PPO approximates the TRPO constraint using a clipped surrogate objective. Define the probability ratio $r_t(\theta) = \pi_\theta(a_t \mid s_t) / \pi_{\theta_\text{old}}(a_t \mid s_t)$. The PPO-Clip objective is:

$$L^{\text{CLIP}}(\theta) = \mathbb{E}_t\left[\min\left(r_t(\theta)\hat{A}_t,\ \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t\right)\right]$$

The clip operation prevents $r_t(\theta)$ from deviating more than $\epsilon$ (typically 0.1 to 0.2) from 1, which limits the policy update magnitude without solving a constrained optimization problem. The minimum of the clipped and unclipped objectives ensures that the update is always pessimistic: when the advantage is positive, we cannot benefit from pushing the probability ratio above $1+\epsilon$, and when the advantage is negative, we cannot be penalized for pushing it below $1-\epsilon$.

The full PPO objective, as typically implemented, combines the policy surrogate, value function loss, and entropy bonus:

$$L(\theta, \phi) = L^{\text{CLIP}}(\theta) - c_1 \cdot L^V(\phi) + c_2 \cdot H[\pi_\theta]$$

where $c_1 \approx 0.5$ and $c_2 \approx 0.01$ are coefficients tuned per domain. The joint optimization over $\theta$ and $\phi$ can run multiple epochs over the same rollout batch, since the clipping constrains the policy from moving too far from the data-generating distribution.

### Continuous Action Spaces: Gaussian and Squashed Policies

For continuous control, the actor outputs the parameters of a probability distribution over $\mathbb{R}^d$. The simplest choice is a diagonal Gaussian:

$$\pi_\theta(a \mid s) = \mathcal{N}(a; \mu_\theta(s), \text{diag}(\sigma_\theta(s))^2)$$

where $\mu_\theta(s) \in \mathbb{R}^d$ and $\sigma_\theta(s) \in \mathbb{R}^d_{>0}$ are outputs of the actor network. The log-probability required by the gradient estimator is:

$$\log \pi_\theta(a \mid s) = -\frac{1}{2}\sum_{i=1}^{d}\left[\frac{(a_i - \mu_i)^2}{\sigma_i^2} + 2\log\sigma_i + \log 2\pi\right]$$

When action bounds must be respected, as in a robotic arm that cannot exceed joint torque limits, the Gaussian is passed through a $\tanh$ squashing function: $\tilde{a} = \tanh(a)$, mapping actions to $(-1, 1)^d$. The change of variables requires a log-probability correction to account for the Jacobian of the $\tanh$ transformation:

$$\log \pi_\theta(\tilde{a} \mid s) = \log \pi_\theta(a \mid s) - \sum_{i=1}^{d} \log(1 - \tanh^2(a_i))$$

This correction is used in Soft Actor-Critic (SAC), where it appears in the reparameterized gradient estimator. SAC additionally replaces the REINFORCE estimator entirely with the reparameterization trick, using $a = \mu_\theta(s) + \sigma_\theta(s) \odot \epsilon$ where $\epsilon \sim \mathcal{N}(0,I)$, enabling gradients to flow directly through the sampled action into the policy parameters without variance from the score function estimator.

### Full PyTorch Implementation: PPO with GAE

The following is a complete, runnable implementation of PPO with GAE for a continuous action space environment conforming to the Gymnasium API. It includes the actor-critic network with a shared MLP trunk, GAE computation, rollout buffer, and the PPO update loop.

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import gymnasium as gym
from torch.distributions import Normal

# ──────────────────────────────────────────────────────────
# Actor-Critic Network with shared feature extractor
# ──────────────────────────────────────────────────────────

class ActorCritic(nn.Module):
    """
    Shared-trunk actor-critic for continuous action spaces.
    Actor outputs (mu, log_std); critic outputs a scalar V(s).
    """
    def __init__(self, obs_dim: int, act_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.shared_trunk = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )
        # Actor head: outputs mean of Gaussian policy
        self.actor_mu = nn.Linear(hidden_dim, act_dim)
        # Log std as a learned state-independent parameter vector
        self.log_std = nn.Parameter(torch.zeros(act_dim))

        # Critic head: outputs scalar value estimate V(s)
        self.critic_head = nn.Linear(hidden_dim, 1)

        # Orthogonal initialization: improves gradient flow at start of training
        for layer in self.shared_trunk:
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, gain=np.sqrt(2))
                nn.init.zeros_(layer.bias)
        nn.init.orthogonal_(self.actor_mu.weight, gain=0.01)
        nn.init.zeros_(self.actor_mu.bias)
        nn.init.orthogonal_(self.critic_head.weight, gain=1.0)
        nn.init.zeros_(self.critic_head.bias)

    def forward(self, obs: torch.Tensor):
        features = self.shared_trunk(obs)
        mu = self.actor_mu(features)
        std = torch.exp(self.log_std.clamp(-5.0, 2.0))
        value = self.critic_head(features).squeeze(-1)
        return mu, std, value

    def get_action_and_value(self, obs: torch.Tensor, action: torch.Tensor = None):
        mu, std, value = self.forward(obs)
        dist = Normal(mu, std)
        if action is None:
            action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=-1)  # sum over action dims
        entropy = dist.entropy().sum(dim=-1)
        return action, log_prob, entropy, value


# ──────────────────────────────────────────────────────────
# Rollout Buffer: stores on-policy experience for one epoch
# ──────────────────────────────────────────────────────────

class RolloutBuffer:
    """
    Fixed-size circular buffer for on-policy PPO rollouts.
    Stores T steps collected from N parallel environments.
    """
    def __init__(self, num_steps: int, num_envs: int, obs_dim: int, act_dim: int):
        self.T = num_steps
        self.N = num_envs
        self.obs       = torch.zeros(num_steps, num_envs, obs_dim)
        self.actions   = torch.zeros(num_steps, num_envs, act_dim)
        self.log_probs = torch.zeros(num_steps, num_envs)
        self.rewards   = torch.zeros(num_steps, num_envs)
        self.dones     = torch.zeros(num_steps, num_envs)
        self.values    = torch.zeros(num_steps, num_envs)
        self.ptr = 0

    def store(self, obs, action, log_prob, reward, done, value):
        self.obs[self.ptr]       = obs
        self.actions[self.ptr]   = action
        self.log_probs[self.ptr] = log_prob
        self.rewards[self.ptr]   = reward
        self.dones[self.ptr]     = done
        self.values[self.ptr]    = value
        self.ptr = (self.ptr + 1) % self.T

    def compute_gae(
        self,
        last_value: torch.Tensor,  # V(s_T), shape (N,)
        gamma: float = 0.99,
        lam: float   = 0.95,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Compute GAE advantages and returns in-place.
        Returns advantages (T, N) and value targets (T, N).
        """
        advantages = torch.zeros_like(self.rewards)
        last_gae   = torch.zeros(self.N)

        for t in reversed(range(self.T)):
            if t == self.T - 1:
                next_non_terminal = 1.0 - self.dones[t]
                next_value = last_value
            else:
                next_non_terminal = 1.0 - self.dones[t]
                next_value = self.values[t + 1]

            delta = (
                self.rewards[t]
                + gamma * next_value * next_non_terminal
                - self.values[t]
            )
            last_gae = delta + gamma * lam * next_non_terminal * last_gae
            advantages[t] = last_gae

        returns = advantages + self.values
        return advantages, returns


# ──────────────────────────────────────────────────────────
# PPO Update: multi-epoch minibatch optimization
# ──────────────────────────────────────────────────────────

def ppo_update(
    model: ActorCritic,
    optimizer: optim.Optimizer,
    buffer: RolloutBuffer,
    advantages: torch.Tensor,
    returns: torch.Tensor,
    clip_coef:    float = 0.2,
    vf_coef:      float = 0.5,
    entropy_coef: float = 0.01,
    max_grad_norm: float = 0.5,
    update_epochs: int   = 10,
    minibatch_size: int  = 256,
):
    """
    Run PPO-Clip update for `update_epochs` passes over the rollout data.
    Flattens the (T, N) buffer into (T*N,) and iterates minibatches.
    """
    T, N = buffer.T, buffer.N
    total = T * N

    obs_flat    = buffer.obs.view(total, -1)
    act_flat    = buffer.actions.view(total, -1)
    logp_flat   = buffer.log_probs.view(total)
    adv_flat    = advantages.view(total)
    ret_flat    = returns.view(total)

    # Normalize advantages across the minibatch (crucial for stability)
    adv_flat = (adv_flat - adv_flat.mean()) / (adv_flat.std() + 1e-8)

    for _ in range(update_epochs):
        indices = torch.randperm(total)
        for start in range(0, total, minibatch_size):
            mb_idx  = indices[start:start + minibatch_size]
            mb_obs  = obs_flat[mb_idx]
            mb_act  = act_flat[mb_idx]
            mb_logp = logp_flat[mb_idx]
            mb_adv  = adv_flat[mb_idx]
            mb_ret  = ret_flat[mb_idx]

            _, new_logp, entropy, new_value = model.get_action_and_value(
                mb_obs, mb_act
            )

            # Policy ratio r(θ) = exp(log π_new(a|s) - log π_old(a|s))
            log_ratio = new_logp - mb_logp
            ratio = torch.exp(log_ratio)

            # PPO-Clip surrogate objective
            surr1 = ratio * mb_adv
            surr2 = torch.clamp(ratio, 1.0 - clip_coef, 1.0 + clip_coef) * mb_adv
            policy_loss = -torch.min(surr1, surr2).mean()

            # Value function loss with clipping (optional but common)
            value_loss = 0.5 * ((new_value - mb_ret) ** 2).mean()

            entropy_loss = -entropy.mean()

            loss = policy_loss + vf_coef * value_loss + entropy_coef * entropy_loss

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()


# ──────────────────────────────────────────────────────────
# Training Loop
# ──────────────────────────────────────────────────────────

def train_ppo(
    env_id:        str   = "HalfCheetah-v4",
    total_steps:   int   = 2_000_000,
    num_envs:      int   = 8,
    num_steps:     int   = 2048,
    learning_rate: float = 3e-4,
    gamma:         float = 0.99,
    gae_lambda:    float = 0.95,
    clip_coef:     float = 0.2,
    vf_coef:       float = 0.5,
    entropy_coef:  float = 0.01,
    max_grad_norm: float = 0.5,
    update_epochs: int   = 10,
    minibatch_size: int  = 256,
    device_str:    str   = "cpu",
):
    device = torch.device(device_str)

    envs = gym.vector.SyncVectorEnv([
        lambda: gym.make(env_id) for _ in range(num_envs)
    ])

    obs_dim = envs.single_observation_space.shape[0]
    act_dim = envs.single_action_space.shape[0]

    model     = ActorCritic(obs_dim, act_dim).to(device)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, eps=1e-5)
    buffer    = RolloutBuffer(num_steps, num_envs, obs_dim, act_dim)

    obs, _ = envs.reset()
    obs    = torch.tensor(obs, dtype=torch.float32, device=device)

    num_updates    = total_steps // (num_steps * num_envs)
    global_step    = 0
    episode_return = np.zeros(num_envs)

    for update in range(1, num_updates + 1):
        # Optional: linear learning rate annealing
        frac = 1.0 - (update - 1.0) / num_updates
        for param_group in optimizer.param_groups:
            param_group["lr"] = learning_rate * frac

        # ── Rollout collection phase ──────────────────────
        model.eval()
        with torch.no_grad():
            for step in range(num_steps):
                global_step += num_envs

                action, log_prob, _, value = model.get_action_and_value(obs)

                # Clamp actions to valid range before stepping environment
                clipped_action = action.clamp(
                    torch.tensor(envs.single_action_space.low,  device=device),
                    torch.tensor(envs.single_action_space.high, device=device),
                )

                next_obs_np, reward_np, terminated_np, truncated_np, _ = \
                    envs.step(clipped_action.cpu().numpy())

                done_np = np.logical_or(terminated_np, truncated_np).astype(np.float32)
                reward  = torch.tensor(reward_np,  dtype=torch.float32, device=device)
                done    = torch.tensor(done_np,    dtype=torch.float32, device=device)

                episode_return += reward_np
                for i, d in enumerate(done_np):
                    if d:
                        episode_return[i] = 0.0

                buffer.store(obs, action, log_prob, reward, done, value)
                obs = torch.tensor(next_obs_np, dtype=torch.float32, device=device)

            # Bootstrap value at the end of the rollout horizon
            last_value = model.get_action_and_value(obs)[3]

        # ── Advantage and return computation ─────────────
        advantages, returns = buffer.compute_gae(
            last_value, gamma=gamma, lam=gae_lambda
        )

        # ── Policy and value network update ──────────────
        model.train()
        ppo_update(
            model, optimizer, buffer, advantages, returns,
            clip_coef=clip_coef, vf_coef=vf_coef,
            entropy_coef=entropy_coef, max_grad_norm=max_grad_norm,
            update_epochs=update_epochs, minibatch_size=minibatch_size,
        )

        if update % 10 == 0:
            print(f"Update {update}/{num_updates} | Steps {global_step:,}")

    envs.close()
    return model


if __name__ == "__main__":
    trained_model = train_ppo(
        env_id        = "HalfCheetah-v4",
        total_steps   = 2_000_000,
        num_envs      = 8,
        num_steps     = 2048,
        learning_rate = 3e-4,
        device_str    = "cpu",
    )
    torch.save(trained_model.state_dict(), "ppo_halfcheetah.pt")
    print("Training complete. Model saved to ppo_halfcheetah.pt")
```

### Soft Actor-Critic: Off-Policy Actor-Critic with Entropy Regularization

SAC introduces a maximum entropy objective that augments the standard expected return with an entropy term weighted by a temperature $\alpha$:

$$J_{\text{SAC}}(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^T \gamma^t \left(r_t + \alpha H[\pi_\theta(\cdot \mid s_t)]\right)\right]$$

This changes the nature of the optimal policy: rather than a deterministic policy that maximizes return, the optimal SAC policy is the most random policy that is still near-optimal. Entropy regularization encourages exploration naturally, prevents premature convergence to local optima in multimodal reward landscapes, and in practice produces dramatically more stable training curves than on-policy methods on locomotion benchmarks.

SAC operates off-policy, maintaining a replay buffer of transitions collected under old policies. It learns two Q-networks $Q_{\phi_1}$ and $Q_{\phi_2}$ to mitigate positive bias from function approximation errors (the Double Q trick introduced by TD3), and uses the minimum across both networks as the critic target:

$$y = r + \gamma \left(\min_{j=1,2} Q_{\phi_j'}(s', \tilde{a}') - \alpha \log \pi_\theta(\tilde{a}' \mid s')\right)$$

where $\tilde{a}' \sim \pi_\theta(\cdot \mid s')$ is a fresh action sample and $\phi'$ denotes the target network, updated via exponential moving average. The actor is updated by maximizing:

$$J_\pi(\theta) = \mathbb{E}_{s \sim \mathcal{D}, \epsilon \sim \mathcal{N}}\left[\min_{j=1,2} Q_{\phi_j}(s, f_\theta(\epsilon; s)) - \alpha \log \pi_\theta(f_\theta(\epsilon; s) \mid s)\right]$$

where $f_\theta(\epsilon; s) = \tanh(\mu_\theta(s) + \sigma_\theta(s) \odot \epsilon)$ is the reparameterized action. This gradient is low-variance because the reparameterization trick routes the gradient through the deterministic function $f_\theta$ rather than through the score function of the distribution. The temperature $\alpha$ can be tuned automatically by treating it as a Lagrange multiplier maintaining a target entropy $\mathcal{H}_{\text{target}} = -\dim(\mathcal{A})$, solving:

$$\alpha^* = \arg\min_\alpha \mathbb{E}_{a \sim \pi_\theta}\left[-\alpha \log \pi_\theta(a \mid s) - \alpha \mathcal{H}_{\text{target}}\right]$$

---

## 3. High-Performance Optimization & Failure Modes

### Gradient Variance: The Dominant Failure Mode

The most pervasive failure in policy gradient training is not incorrect implementation but uncontrolled variance. High variance in the gradient estimator manifests as oscillating loss curves, policy collapse (entropy drops to near-zero while performance remains poor), or the more subtle failure of training progress stalling at a suboptimal local policy while gradient norms remain nonzero. Each of these failure modes has a specific mechanical cause.

Advantage normalization is the first line of defense. When advantages are not normalized per minibatch, the magnitude of the policy gradient scales with the typical scale of the reward signal. If rewards are in the range $[0, 1000]$, the effective policy learning rate is 1000 times higher than if rewards are in $[0, 1]$, overwhelming the gradient clipping and producing destructive updates. Normalizing advantages to zero mean and unit variance per minibatch decouples gradient magnitude from reward scale. The normalization must happen within each minibatch, not across the full rollout, so that the normalization statistics do not introduce dependencies between minibatches.

Value function accuracy is the second determinant of gradient quality. If the critic $V_\phi$ is poorly fit, the advantage estimates are dominated by the value estimation error rather than the true advantage signal. This is a bias source: even a perfect Monte Carlo return $G_t$ subtracted from a badly learned $V_\phi$ produces a noisy and biased advantage. The critic loss should be monitored throughout training; a value loss that is not decreasing, or is decreasing far slower than the policy loss, indicates that the value function is the bottleneck. Common causes include too-small critic network capacity, too-large value coefficient $c_1$ causing the critic to dominate the shared trunk gradient, or insufficient training epochs dedicated to the critic.

### Clipping Hyperparameter Sensitivity and KL Divergence Monitoring

The PPO clip coefficient $\epsilon$ controls how much the policy is allowed to change per update. Setting $\epsilon$ too large makes PPO behave like vanilla policy gradient, with the same instability. Setting it too small prevents meaningful improvement per rollout batch, requiring exponentially more environment interactions. A productive diagnostic is to monitor the approximate KL divergence between the old and new policy during training:

$$\hat{D}_{\text{KL}} = \mathbb{E}_t[\log \pi_{\theta_{\text{old}}}(a_t \mid s_t) - \log \pi_\theta(a_t \mid s_t)]$$

If $\hat{D}_{\text{KL}}$ consistently exceeds $0.02$ to $0.05$, the policy is moving too far per update and either $\epsilon$ should be reduced or the number of update epochs decreased. An early stopping rule keyed on this KL threshold, terminating additional epochs once the KL exceeds a threshold, is a robust heuristic that improves performance on environments where the optimal policy update magnitude varies across training.

### Reward Scaling and the Critic's Regression Target

The critic in PPO regresses toward return values $G_t$, which are sums of discounted rewards. If individual rewards are large (sparse $+1000$ upon success) or have high variance, the return distribution has a large range, making the value regression difficult and the advantage estimates noisy. Two complementary techniques address this. The first is reward normalization: maintain a running mean and variance of observed rewards and normalize each reward to unit variance before storing in the rollout buffer, with or without subtracting the mean depending on whether reward sign carries information. The second is return normalization, where $G_t$ values are divided by a running standard deviation estimate before the critic regression, keeping the target distribution in a range where linear output layers can saturate gracefully.

Parallelism through vectorized environments is both an optimization and a variance reduction technique. Collecting $N$ parallel rollouts of $T$ steps each yields $N \times T$ transitions per update. The variance of the gradient estimator scales as $O(1 / (N \cdot T))$, so doubling the number of parallel environments halves gradient variance at the cost of $N$ times the environment simulation compute. For CPU-bound simulations like physics engines (MuJoCo, Bullet), $N = 8$ to $64$ environments running in parallel on separate processes is typical, and the reduction in training wall clock time is superlinear because larger minibatches make better use of hardware accelerators.

### The Deadly Triad in Actor-Critic Methods

When actor-critic methods are used off-policy (as in SAC or the original DQN-style critics), they encounter the deadly triad identified by Sutton and Barto: function approximation, bootstrapping, and off-policy training can interact to produce divergence. In practice, this manifests as Q-value overestimation, where the critic assigns progressively larger values to unseen state-action pairs, eventually causing the actor to collapse onto a small region of action space that exploits the critic's errors. The Double Q trick in SAC partially mitigates this by preventing the maximization bias from both networks compounding, but it does not eliminate it.

Target networks are the standard countermeasure. Maintaining a slowly updated copy of the critic with parameters $\phi' \leftarrow \tau \phi + (1-\tau) \phi'$ (with $\tau \approx 0.005$) provides stable regression targets that do not change rapidly within a training epoch, preventing the feedback loop where a large critic update produces a large actor update which produces a different data distribution which produces a large critic update. The soft update rule is strictly more stable than hard target network updates (copying $\phi' \leftarrow \phi$ every $C$ steps) for most continuous control tasks.

### Hyperparameter Sensitivity: What to Tune First

When a fresh training run fails to learn, the diagnostic priority order reflects the importance of each component to gradient quality. The critic's value loss should be inspected first: if it is not decreasing, the critic has insufficient capacity or the value coefficient is too small. If the policy entropy drops below the target within the first 10% of training, the entropy coefficient is too small and exploration has collapsed. If the policy loss is decreasing but the episodic return is not improving, the advantage estimates are likely biased due to poor critic fit or incorrect GAE parameter choices. A $\lambda$ that is too high ($\lambda > 0.98$) on tasks with sparse long-horizon rewards will produce high-variance advantages that corrupt the gradient direction. A $\lambda$ that is too low ($\lambda < 0.9$) on tasks with dense shaped rewards will introduce bias from the imperfect critic, pushing the policy toward a locally optimal behavior that maximizes short-horizon advantage while ignoring long-term structure.

Learning rate scheduling deserves careful attention in PPO specifically because the rollout data quality changes over training. Early in training, the policy is random and the rollouts contain diverse, high-variance experience. Later in training, the policy is near-optimal and the rollouts cover a narrow distribution of near-optimal trajectories. A fixed learning rate that was appropriate early in training will be too large late in training, causing the policy to oscillate around the optimum. Linear annealing of the learning rate (as implemented in the training loop above) is a simple and reliable mitigation, but cosine annealing schedules and adaptive per-parameter learning rate methods like Adam also provide implicit scheduling. The critical discipline is to not change the learning rate and clip coefficient simultaneously when debugging, since their effects on gradient magnitude are entangled.

### Connecting Value-Based and Policy-Based Methods: A Unified View

The mathematical relationship between value-based and policy-based methods is deeper than the surface-level distinction between implicit and explicit policy representations suggests. The policy gradient theorem can be expressed in terms of the advantage function, which is itself defined through the value and Q functions. Actor-critic methods bridge the two families by learning both: the actor represents the policy directly, and the critic represents the value function that makes the actor's gradient estimates tractable. The Q-function and the policy are related through the Bellman optimality equation, and the advantage function is the residual between $Q^\pi$ and $V^\pi$. This means that any advance in value function estimation, whether through better neural architectures, improved bootstrapping targets, or off-policy data augmentation, directly improves the quality of the advantage estimates and thus the variance of the policy gradient. The separation between value-based and policy-based methods is a pedagogical convenience; production systems like SAC, PPO with shared trunks, and TD3 are all actor-critic systems that lie on a continuum between the two extremes.

The entropy-regularized framework of SAC generalizes this relationship further. In the maximum entropy framework, the optimal policy is not a delta function at the greedy action but a Boltzmann distribution $\pi^*(a \mid s) \propto \exp(Q^*(s,a) / \alpha)$. This means the soft Q-function and the entropy-regularized policy are dual representations of the same underlying object, related by a soft max operation. As $\alpha \to 0$, the soft policy converges to the greedy policy and SAC reduces to a standard off-policy Q-learning method. As $\alpha \to \infty$, the policy becomes uniform over the action space and reduces to pure exploration. The practical operating point, the automatic temperature tuning at a target entropy, finds the $\alpha$ that keeps the policy maximally exploratory while still exploiting discovered reward structure. This is a precise, principled formulation of the exploration-exploitation tradeoff that the broader field of reinforcement learning has grappled with since its inception.
