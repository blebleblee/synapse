# Lesson 4: Policy Gradient Methods and Actor-Critic Architectures

## 1. First-Principles Intuition & Invariants

The central tension in reinforcement learning is one of representation: should an agent encode knowledge about which actions are valuable at each state, or should it encode the probability of taking each action directly? Value-based methods, epitomized by Q-learning and its deep variants, answer the first way. They build a critic that scores state-action pairs, then derive a policy implicitly by selecting the highest-scoring action. Policy gradient methods answer the second way, and in doing so, they sidestep an entire class of problems that torment value-based approaches while introducing their own distinct challenges.

The fundamental objection to pure value-based methods surfaces most clearly in continuous action spaces. If an agent must learn to control a robotic joint with a torque ranging continuously from -100 N·m to 100 N·m, the argmax operation over a Q-function becomes an inner optimization problem that must be solved at every step. Beyond that, in stochastic environments or under partial observability, the optimal policy is itself stochastic: sometimes the agent genuinely should randomize over actions. A deterministic policy extracted from a value function cannot represent this. Policy gradient methods parameterize the policy directly as a differentiable function $\pi_\theta(a \mid s)$, treating the policy as a first-class object to be optimized, and they frame the optimization objective in terms of expected cumulative reward.

### The Policy Gradient Theorem

The objective is defined as the expected discounted return under the current policy, integrated over trajectories drawn from that policy:

$$J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T} \gamma^t r_t\right]$$

The agent wants to find $\theta^* = \arg\max_\theta J(\theta)$. Gradient ascent on $J(\theta)$ requires computing $\nabla_\theta J(\theta)$, but this derivative involves the expectation of a stochastic process whose distribution itself depends on $\theta$ through the trajectory distribution $p_\theta(\tau)$. This is not a gradient through a fixed distribution: it is a gradient through the sampling mechanism itself.

The resolution is the log-derivative trick, also called the REINFORCE identity. For any differentiable, parameterized distribution $p_\theta(x)$, the identity $\nabla_\theta p_\theta(x) = p_\theta(x) \nabla_\theta \log p_\theta(x)$ allows one to push the gradient inside an expectation:

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\left(\sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t \mid s_t)\right) G_t\right]$$

where $G_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$ is the discounted return from timestep $t$. This is the Policy Gradient Theorem, derived rigorously by Sutton et al. in 1999, and it is the bedrock on which every actor-critic method is built. The remarkable insight is that the gradient of the environment's transition dynamics — which the agent does not know and cannot differentiate through — vanishes entirely. Only the gradient of the policy's own log-probability survives, weighted by the signal of how good the trajectory was.

### Why This Form Has High Variance

The gradient estimator above is unbiased: its expectation over trajectories is the true gradient of $J(\theta)$. But it has catastrophically high variance in practice. The return $G_t$ accumulates reward noise over an entire trajectory. An agent training on a 1,000-step episode must attribute a final reward to actions taken 900 steps earlier, and the statistical noise in this assignment dwarfs the signal. High variance means that individual gradient estimates point in wildly different directions from the true gradient, forcing the use of extremely small learning rates and requiring enormous numbers of samples before convergence.

The variance problem is not an incidental implementation detail. It is the central engineering problem of policy gradient methods, and every major architectural development in the field — baselines, advantage functions, generalized advantage estimation, actor-critic decomposition — is a direct answer to it.

### Causality and Reward-to-Go

The first refinement follows from causality. The gradient contribution of action $a_t$ cannot be influenced by rewards that occurred before $t$; those rewards are independent of the current action given the current policy. The full return $G_0$ can be replaced with the reward-to-go $\hat{R}_t = \sum_{k=t}^{T} \gamma^{k-t} r_k$, which does not sum rewards before $t$. This reduces variance by discarding terms that are, by construction, uncorrelated with the action's log-probability gradient. This substitution produces an estimator with the same expectation but lower variance, and it is a free variance reduction that no sane practitioner omits.

---

## 2. Core Architecture & Mechanics

### Baselines and the Advantage Function

Even after the reward-to-go refinement, the estimator weights each log-gradient by the raw magnitude of return. An agent might take a good action in an intrinsically high-reward environment, receive a large return, and correctly push that action's probability up. But it might also take a bad action — one that reduced total reward compared to the alternatives — and still receive a large positive return by accident of environment richness. The raw return cannot distinguish "this action was better than average" from "this trajectory was generally good."

A baseline $b(s_t)$ is any function that depends on state but not on action, subtracted from the return in the gradient estimator:

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta}\left[\sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t \mid s_t) \left(G_t - b(s_t)\right)\right]$$

Adding a baseline does not introduce bias. The proof is direct: $\mathbb{E}_{a_t \sim \pi_\theta(\cdot \mid s_t)}\left[\nabla_\theta \log \pi_\theta(a_t \mid s_t) b(s_t)\right] = b(s_t) \nabla_\theta \sum_a \pi_\theta(a \mid s_t) = b(s_t) \nabla_\theta 1 = 0$. The baseline term averages to zero, leaving the gradient's expectation unchanged while reducing variance whenever the baseline correlates with the return. The optimal baseline in terms of minimizing estimator variance is $b^*(s) = \mathbb{E}[G_t^2 \mid s_t = s] / \mathbb{E}[G_t \mid s_t = s]$, though this is expensive to compute and practitioners almost universally use the value function $V^\pi(s) = \mathbb{E}_{\pi}[G_t \mid s_t = s]$ as the baseline instead, since it is both approximately optimal and naturally interpretable.

Subtracting the value function baseline from the return yields the advantage function:

$$A^\pi(s_t, a_t) = Q^\pi(s_t, a_t) - V^\pi(s_t)$$

The advantage directly measures how much better (or worse) the specific action $a_t$ is compared to the average action the policy would take in state $s_t$. When $A^\pi > 0$, the action was above average and its probability should increase. When $A^\pi < 0$, the action was below average and its probability should decrease. The policy gradient with advantage-weighted log-probabilities is the theoretical core of every modern actor-critic algorithm.

### The Actor-Critic Split

The critical practical implication of using the advantage as a weighting signal is that the value function $V^\pi$ must itself be estimated, and this estimation problem is a regression problem: a second neural network, the critic, is trained to predict expected return from states. The actor is the policy network $\pi_\theta$; the critic is the value network $V_\phi$. These two components form the actor-critic architecture.

```
              ┌────────────────────────────────────────────────┐
              │               Environment                      │
              │   s_t ──────────────────────────► r_t, s_{t+1} │
              └────────────┬────────────────────────┬──────────┘
                           │ state s_t              │ reward r_t
                           │                        │
              ┌────────────▼──────────┐  ┌──────────▼──────────────────┐
              │        ACTOR          │  │          CRITIC              │
              │                       │  │                              │
              │  π_θ(a | s)           │  │  V_φ(s)                     │
              │  ─────────────────    │  │  ─────────────────────────  │
              │  Policy network       │  │  Value network              │
              │  Outputs action dist  │  │  Outputs scalar V-estimate  │
              │                       │  │                              │
              │  Loss: -log π_θ(a|s) │  │  Loss: (V_φ(s) - G_t)²      │
              │        * Â_t         │  │                              │
              └────────────┬──────────┘  └──────────┬────────────────-─┘
                           │ ∇_θ loss               │ ∇_φ loss
                           │                        │
              ┌────────────▼────────────────────────▼──────────┐
              │               Optimizer (Adam)                 │
              │        Updates θ (actor), φ (critic)           │
              └────────────────────────────────────────────────┘
```

The critic is trained with a temporal-difference (TD) target, bootstrapping from the next state's value estimate to avoid requiring full trajectory rollouts. The one-step TD target is $r_t + \gamma V_\phi(s_{t+1})$, and the TD error (the difference between this target and the current prediction) serves as a low-variance proxy for the advantage: $\delta_t = r_t + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)$.

This one-step TD error is unbiased only when the value function is perfect. In practice, the critic is learned from sampled data and starts far from the true value function, introducing bias into the advantage estimates. The tradeoff between bias and variance is fundamental: Monte Carlo returns are unbiased but high-variance; one-step TD is low-variance but biased. Generalized Advantage Estimation offers a principled mechanism to navigate this tradeoff.

### Generalized Advantage Estimation

John Schulman introduced Generalized Advantage Estimation (GAE) in 2015 as an exponentially weighted average of $k$-step advantage estimators. Define the $k$-step return as $\hat{G}_t^{(k)} = \sum_{l=0}^{k-1} \gamma^l r_{t+l} + \gamma^k V_\phi(s_{t+k})$. The $k$-step advantage estimator $\hat{A}_t^{(k)} = \hat{G}_t^{(k)} - V_\phi(s_t)$ has variance that grows with $k$ (more terms of accumulated noise) and bias that shrinks with $k$ (less reliance on the imperfect critic).

GAE introduces a parameter $\lambda \in [0, 1]$ and defines:

$$\hat{A}_t^{\text{GAE}(\gamma, \lambda)} = \sum_{l=0}^{T-t-1} (\gamma \lambda)^l \delta_{t+l}$$

where $\delta_{t+l} = r_{t+l} + \gamma V_\phi(s_{t+l+1}) - V_\phi(s_{t+l})$ is the TD error at step $t+l$. When $\lambda = 0$, GAE reduces to the one-step TD advantage, which has minimum variance but maximum bias. When $\lambda = 1$, GAE reduces to the full Monte Carlo advantage (up to discounting), which has minimum bias but maximum variance. Values of $\lambda$ between 0.9 and 0.99 work well across a wide range of problems in practice, and $\lambda$ has the intuitive interpretation of an eligibility trace decay: actions in the distant past receive exponentially diminishing credit as $\lambda^l$ shrinks.

The elegance of the GAE formula is computational. It can be computed in a single backward pass over a collected trajectory using the recurrence $\hat{A}_t = \delta_t + \gamma \lambda \hat{A}_{t+1}$, with $\hat{A}_T = 0$ at the trajectory terminal state. This is O(T) in both time and memory, making it trivial to integrate into any batched rollout buffer.

### Proximal Policy Optimization

PPO, also introduced by Schulman in 2017, addresses a second fundamental instability in policy gradient methods: destructive policy updates. If the gradient step is too large, the new policy $\pi_{\theta'}$ can be radically different from the policy $\pi_\theta$ that collected the trajectory data. The advantage estimates computed under $\pi_\theta$ are then no longer valid for the new policy, the gradient loses its accuracy, and training can collapse irreversibly.

PPO solves this through a clipped surrogate objective. Define the probability ratio $r_t(\theta) = \pi_\theta(a_t \mid s_t) / \pi_{\theta_\text{old}}(a_t \mid s_t)$. The unclipped objective is simply $r_t(\theta) \hat{A}_t$, the importance-weighted advantage. PPO clips this ratio within $[1-\varepsilon, 1+\varepsilon]$ where $\varepsilon$ is typically 0.2:

$$L^{\text{CLIP}}(\theta) = \mathbb{E}_t\left[\min\left(r_t(\theta)\hat{A}_t,\ \text{clip}(r_t(\theta), 1-\varepsilon, 1+\varepsilon)\hat{A}_t\right)\right]$$

The min of the clipped and unclipped objective creates a pessimistic lower bound: when the advantage is positive, the ratio is clipped at $1+\varepsilon$ so the agent cannot exploit a good action too aggressively in a single update. When the advantage is negative, the ratio is clipped at $1-\varepsilon$ so the agent cannot suppress a bad action too aggressively. This keeps the new policy in a trust region around the old policy without the computational overhead of the KL-constrained optimization that TRPO (PPO's predecessor) required.

### Complete PPO Implementation

The following is a complete, production-grade PPO implementation in PyTorch against a vectorized environment, incorporating GAE, the clipped surrogate objective, shared actor-critic networks with separate output heads, and entropy regularization.

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import gymnasium as gym
from torch.distributions import Categorical


# ─────────────────────────────────────────────────────────────────────────────
# Network Architecture: Shared torso, separate actor/critic heads.
# Using orthogonal initialization, which is empirically superior to Xavier for
# RL policy networks. The final layer uses a 0.01 scale to produce a nearly
# uniform initial policy distribution, allowing exploration in early training.
# ─────────────────────────────────────────────────────────────────────────────

def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    nn.init.orthogonal_(layer.weight, std)
    nn.init.constant_(layer.bias, bias_const)
    return layer


class ActorCritic(nn.Module):
    def __init__(self, obs_dim: int, act_dim: int):
        super().__init__()
        # Shared feature extractor
        self.shared = nn.Sequential(
            layer_init(nn.Linear(obs_dim, 64)),
            nn.Tanh(),
            layer_init(nn.Linear(64, 64)),
            nn.Tanh(),
        )
        # Actor head: logits over discrete action space
        self.actor_head = layer_init(nn.Linear(64, act_dim), std=0.01)
        # Critic head: scalar value estimate
        self.critic_head = layer_init(nn.Linear(64, 1), std=1.0)

    def get_value(self, x: torch.Tensor) -> torch.Tensor:
        return self.critic_head(self.shared(x))

    def get_action_and_value(
        self, x: torch.Tensor, action: torch.Tensor = None
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.shared(x)
        logits = self.actor_head(features)
        dist = Categorical(logits=logits)
        if action is None:
            action = dist.sample()
        return action, dist.log_prob(action), dist.entropy(), self.critic_head(features)


# ─────────────────────────────────────────────────────────────────────────────
# Rollout Buffer: Stores one full batch of environment experience.
# Pre-allocated tensors avoid repeated allocation overhead inside the hot path.
# ─────────────────────────────────────────────────────────────────────────────

class RolloutBuffer:
    def __init__(self, num_steps: int, num_envs: int, obs_dim: int, device: torch.device):
        self.obs         = torch.zeros(num_steps, num_envs, obs_dim).to(device)
        self.actions     = torch.zeros(num_steps, num_envs, dtype=torch.long).to(device)
        self.log_probs   = torch.zeros(num_steps, num_envs).to(device)
        self.rewards     = torch.zeros(num_steps, num_envs).to(device)
        self.dones       = torch.zeros(num_steps, num_envs).to(device)
        self.values      = torch.zeros(num_steps, num_envs).to(device)
        self.advantages  = torch.zeros(num_steps, num_envs).to(device)
        self.returns     = torch.zeros(num_steps, num_envs).to(device)
        self.ptr = 0
        self.num_steps = num_steps
        self.num_envs = num_envs

    def store(self, obs, actions, log_probs, rewards, dones, values):
        self.obs[self.ptr]       = obs
        self.actions[self.ptr]   = actions
        self.log_probs[self.ptr] = log_probs
        self.rewards[self.ptr]   = rewards
        self.dones[self.ptr]     = dones
        self.values[self.ptr]    = values.squeeze(-1)
        self.ptr += 1

    def reset(self):
        self.ptr = 0

    def compute_gae(
        self,
        last_value: torch.Tensor,
        last_done: torch.Tensor,
        gamma: float,
        gae_lambda: float
    ):
        """
        Backward pass GAE computation using the recurrence:
            Â_t = δ_t + (γλ) * Â_{t+1} * (1 - done_{t+1})

        The (1 - done) mask zeros out the bootstrap from terminal states,
        preventing the value of the next episode from leaking backward
        across episode boundaries — a subtle but critical correctness detail.
        """
        gae = torch.zeros_like(last_value.squeeze(-1))
        for step in reversed(range(self.num_steps)):
            if step == self.num_steps - 1:
                next_non_terminal = 1.0 - last_done.float()
                next_value = last_value.squeeze(-1)
            else:
                next_non_terminal = 1.0 - self.dones[step + 1]
                next_value = self.values[step + 1]

            delta = (
                self.rewards[step]
                + gamma * next_value * next_non_terminal
                - self.values[step]
            )
            gae = delta + gamma * gae_lambda * next_non_terminal * gae
            self.advantages[step] = gae

        self.returns = self.advantages + self.values

    def get_flat_batches(self, minibatch_size: int):
        """
        Flatten (num_steps, num_envs, ...) → (num_steps * num_envs, ...)
        and yield random minibatches for the PPO update epochs.
        """
        total = self.num_steps * self.num_envs
        indices = torch.randperm(total)
        flat_obs      = self.obs.view(total, -1)
        flat_actions  = self.actions.view(total)
        flat_logprobs = self.log_probs.view(total)
        flat_advs     = self.advantages.view(total)
        flat_returns  = self.returns.view(total)

        for start in range(0, total, minibatch_size):
            mb_idx = indices[start : start + minibatch_size]
            yield (
                flat_obs[mb_idx],
                flat_actions[mb_idx],
                flat_logprobs[mb_idx],
                flat_advs[mb_idx],
                flat_returns[mb_idx],
            )


# ─────────────────────────────────────────────────────────────────────────────
# PPO Training Loop
# ─────────────────────────────────────────────────────────────────────────────

def train_ppo(env_id: str = "CartPole-v1"):
    # Hyperparameters
    total_timesteps  = 500_000
    num_envs         = 8          # Parallel environments (vectorized)
    num_steps        = 128        # Steps per rollout per env → batch = 1024
    num_epochs       = 4          # PPO update epochs per rollout
    minibatch_size   = 256
    gamma            = 0.99
    gae_lambda       = 0.95
    clip_coef        = 0.2        # ε in the clipped surrogate objective
    ent_coef         = 0.01       # Entropy bonus coefficient
    vf_coef          = 0.5        # Value loss coefficient in total loss
    max_grad_norm    = 0.5        # Global gradient norm clipping
    lr               = 2.5e-4
    target_kl        = 0.01       # Early stopping threshold per update epoch

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Vectorized environments. SyncVectorEnv runs sequentially in one process;
    # swap for AsyncVectorEnv on multi-core machines to parallelize step().
    envs = gym.vector.SyncVectorEnv([lambda: gym.make(env_id)] * num_envs)
    obs_dim = envs.single_observation_space.shape[0]
    act_dim = envs.single_action_space.n

    model  = ActorCritic(obs_dim, act_dim).to(device)
    optim_ = optim.Adam(model.parameters(), lr=lr, eps=1e-5)
    buffer = RolloutBuffer(num_steps, num_envs, obs_dim, device)

    obs, _   = envs.reset()
    obs      = torch.tensor(obs, dtype=torch.float32).to(device)
    done     = torch.zeros(num_envs).to(device)

    global_step  = 0
    num_updates  = total_timesteps // (num_steps * num_envs)

    for update in range(1, num_updates + 1):
        # ── Rollout Phase ────────────────────────────────────────────────────
        # Collect num_steps transitions per environment under the current
        # policy. No gradient computation here: use torch.no_grad() to avoid
        # storing computation graphs for every forward pass in the hot loop.
        buffer.reset()
        model.eval()
        with torch.no_grad():
            for step in range(num_steps):
                global_step += num_envs
                action, log_prob, _, value = model.get_action_and_value(obs)

                next_obs_np, reward_np, term_np, trunc_np, _ = envs.step(
                    action.cpu().numpy()
                )
                done_np  = np.logical_or(term_np, trunc_np)
                reward   = torch.tensor(reward_np, dtype=torch.float32).to(device)
                next_obs = torch.tensor(next_obs_np, dtype=torch.float32).to(device)
                next_done = torch.tensor(done_np, dtype=torch.float32).to(device)

                buffer.store(obs, action, log_prob, reward, done, value)
                obs  = next_obs
                done = next_done

            # Bootstrap value at the end of the rollout for GAE
            last_value = model.get_value(obs)
            buffer.compute_gae(last_value, done, gamma, gae_lambda)

        # ── Update Phase ─────────────────────────────────────────────────────
        # Normalize advantages across the entire rollout batch to stabilize
        # gradient magnitudes. This is a form of adaptive scaling: advantages
        # are measured in units of their own standard deviation.
        model.train()
        flat_advs = buffer.advantages.view(-1)
        adv_mean, adv_std = flat_advs.mean(), flat_advs.std() + 1e-8

        for epoch in range(num_epochs):
            for mb_obs, mb_actions, mb_old_logprobs, mb_advs, mb_returns in \
                    buffer.get_flat_batches(minibatch_size):

                mb_advs = (mb_advs - adv_mean) / adv_std

                _, new_logprobs, entropy, new_values = model.get_action_and_value(
                    mb_obs, mb_actions
                )
                new_values = new_values.squeeze(-1)

                # ── PPO Clipped Surrogate Loss ────────────────────────────
                log_ratio = new_logprobs - mb_old_logprobs
                ratio     = log_ratio.exp()

                # Approximate KL for early stopping (Schulman approximation):
                # kl ≈ (ratio - 1) - log_ratio, unbiased and numerically stable
                approx_kl = ((ratio - 1.0) - log_ratio).mean()

                pg_loss_unclipped = -mb_advs * ratio
                pg_loss_clipped   = -mb_advs * torch.clamp(
                    ratio, 1.0 - clip_coef, 1.0 + clip_coef
                )
                pg_loss = torch.max(pg_loss_unclipped, pg_loss_clipped).mean()

                # ── Critic Loss ──────────────────────────────────────────
                # Using unclipped MSE. Some implementations also clip the value
                # prediction; evidence for this being beneficial is mixed.
                v_loss = 0.5 * ((new_values - mb_returns) ** 2).mean()

                # ── Entropy Bonus ────────────────────────────────────────
                # Entropy regularization encourages exploration by penalizing
                # the policy for collapsing to deterministic behavior too early.
                entropy_loss = entropy.mean()

                # ── Total Loss ───────────────────────────────────────────
                loss = pg_loss + vf_coef * v_loss - ent_coef * entropy_loss

                optim_.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                optim_.step()

            # Early stopping: if KL divergence from old policy exceeds the
            # threshold, abandon remaining epochs for this rollout.
            if approx_kl > target_kl:
                break

        if update % 10 == 0:
            print(
                f"Update {update}/{num_updates} | "
                f"Step {global_step} | "
                f"pg_loss={pg_loss.item():.4f} | "
                f"v_loss={v_loss.item():.4f} | "
                f"approx_kl={approx_kl.item():.4f}"
            )

    envs.close()
    return model


if __name__ == "__main__":
    trained_model = train_ppo("CartPole-v1")
```

The structure of the update loop is worth examining carefully because several implementation decisions have outsized impact on training stability. Advantage normalization is applied after GAE computation but before the minibatch loop, using statistics computed over the entire rollout batch. This is correct: computing normalization statistics per-minibatch would introduce statistical noise for small minibatches and would make advantage magnitudes inconsistent across the batch. The early stopping check on approximate KL divergence guards against epochs where the probability ratio has drifted far enough from 1.0 that the importance weights are no longer reliable — a subtlety the original PPO paper mentions but many tutorial implementations omit.

---

## 3. High-Performance Optimization & Failure Modes

### Diagnosing Gradient Variance and Policy Collapse

The most common failure mode in policy gradient training is policy collapse: the actor converges to a near-deterministic policy before the critic is well-calibrated. This happens when the entropy bonus coefficient is too small, allowing the actor's distribution to sharpen rapidly around whatever actions happened to receive positive advantage estimates in the first few rollouts. Once the policy is near-deterministic, the advantage estimates for the unchosen actions have no data support, the critic cannot improve its estimates for unvisited state-action regions, and the agent is permanently stuck in a local optimum.

The diagnostic signal is the policy entropy, which should be monitored continuously during training. For a discrete action space of size $k$, the maximum entropy is $\log k$ (uniform distribution) and the minimum is $0$ (deterministic). A healthy PPO training run on a moderate environment typically shows entropy declining slowly from near-maximum over hundreds of thousands of steps. A run where entropy drops below $0.1 \log k$ within the first 20% of training steps is almost always heading toward a collapsed policy. Increasing `ent_coef` from $0.01$ to $0.05$, or temporarily scheduling entropy coefficient decay rather than keeping it fixed, usually resolves premature collapse.

The approximate KL diagnostic is equally important. When the KL consistently triggers early stopping on the first or second epoch of every update, the effective number of gradient steps per rollout is far less than `num_epochs * (rollout_size / minibatch_size)`. This means the data efficiency is poor: the agent collects data, performs almost no learning from it, and discards it. The root cause is typically a learning rate that is too large, causing the policy to move too far in parameter space per gradient step. Reducing the learning rate or reducing the rollout size (so that each rollout is a smaller, more stationary slice of behavior) generally resolves this.

The approx KL formula $\hat{\text{KL}} = \mathbb{E}[(r - 1) - \log r]$ is worth understanding rather than treating as a black box. It is a second-order approximation of the true KL divergence $D_{KL}(\pi_{\theta_\text{old}} \| \pi_\theta) = \mathbb{E}_{a \sim \pi_{\theta_\text{old}}}[\log(r^{-1})] = -\mathbb{E}[\log r]$, shifted to be non-negative and symmetric around $r=1$. When $r$ is exactly $1$ everywhere (no parameter change), both the true KL and the approximation are $0$. When $r$ deviates significantly from $1$, the approximation diverges from the true KL, but it is cheap to compute and sufficient for the early-stopping heuristic.

### Sample Efficiency: Vectorization and Throughput

The wall-clock bottleneck in deep RL training is almost never gradient computation — it is environment interaction. A single-environment loop in Python can collect perhaps 2,000–5,000 steps per second on a CartPole-class environment. Vectorizing to 32 parallel environments with `AsyncVectorEnv`, each stepping simultaneously in separate processes, multiplies throughput roughly linearly up to the point where the CPU cores are saturated. For GPU-accelerated environments (Brax, Isaac Gym, MuJoCo XLA backends), parallelism can extend to thousands of simultaneous simulations running on the GPU itself, allowing collection of tens of millions of steps per second and shifting the bottleneck to the neural network update.

The relationship between rollout length `num_steps`, number of environments `num_envs`, and batch size is worth analyzing precisely. The total batch size for one PPO update is `num_steps * num_envs`. For a fixed computational budget, increasing `num_envs` while decreasing `num_steps` preserves batch size but changes the statistical properties of the rollout: shorter rollouts have less temporal autocorrelation between samples (better) but accumulate more GAE bootstrap bias per sample (worse). Values of `num_steps` between 64 and 2048 are common depending on environment horizon length; environments with long episodes and dense rewards benefit from longer rollouts, while environments with sparse rewards often need longer rollouts to capture any reward signal at all within a single collection window.

### Critic Underfitting and TD Error Magnitude

The critic's accuracy directly controls the bias of the advantage estimator. When the critic is poorly fit — when its value predictions have high mean-squared error relative to the true value function — the advantage estimates are noisy and biased, the policy gradient is unreliable, and training slows dramatically. This is a chicken-and-egg problem: the policy changes every update, shifting the target distribution for the critic, which prevents the critic from converging. The standard mitigation is to weight the value loss higher in the total loss (larger `vf_coef`), to give the critic more gradient signal per update relative to the actor. Some practitioners train the critic for more gradient steps per rollout than the actor, particularly in the early phase of training when the critic starts far from the true value function.

The explained variance of the value predictions is the standard diagnostic:

$$\text{EV} = 1 - \frac{\text{Var}[G_t - V_\phi(s_t)]}{\text{Var}[G_t]}$$

An explained variance near 1 means the critic is predicting returns accurately. Values below 0.5 at the end of training indicate the critic is severely underfitting, and advantage estimates are carrying most of the variance of raw returns rather than isolating action-specific signal. Computing and logging explained variance at every update is a low-cost diagnostic that provides direct insight into whether the actor is receiving clean advantage signals.

### The Bias-Variance Landscape of GAE Lambda

The choice of $\lambda$ in GAE deserves more analytical attention than it typically receives in textbook treatments. Consider the extreme $\lambda = 0$ case. The advantage estimate is simply the one-step TD error $\delta_t = r_t + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)$. This has variance proportional to the variance of a single reward plus the variance of the value function prediction error at $s_{t+1}$. The bias is the full approximation error of the value function, which could be large in early training. For $\lambda = 1$, the advantage estimate is the full Monte Carlo return minus the baseline: $\hat{A}_t^{MC} = \sum_{k=0}^{T-t-1} \gamma^k r_{t+k} - V_\phi(s_t)$. This has zero bias (the value function only appears as a baseline on the current state, which does not affect bias), but variance that grows with the remaining trajectory length.

For environments with high per-step reward noise, $\lambda$ should be pulled closer to $0$ to avoid accumulating noise over long sums. For environments where the value function is known to be inaccurate (early training, sparse reward environments), $\lambda$ should be closer to $1$ to avoid the high bias of bootstrapping from a poor critic. In practice, $\lambda = 0.95$ works across an impressively wide range of tasks because most environments have moderately well-behaved reward distributions and the critic improves sufficiently within the first 10% of training to make bootstrap bias manageable.

### Convergence Guarantees and the On-Policy Constraint

A crucial invariant distinguishes PPO and all on-policy actor-critic methods from off-policy methods like SAC or DDPG: the data in the rollout buffer was collected under $\pi_{\theta_\text{old}}$ and is valid for importance-weighted updates only within the trust region. Once the update epochs complete, the buffer must be discarded entirely. Storing transitions for replay across multiple rollout iterations — as one might naively attempt for sample efficiency — violates the theoretical foundation of the importance weight correction in the clipped objective. The ratio $r_t(\theta) = \pi_\theta / \pi_{\theta_\text{old}}$ assumes $\pi_{\theta_\text{old}}$ is the policy that collected the data, and if that policy is now many updates old, the ratio is no longer a valid importance weight.

This is the fundamental sample inefficiency of on-policy methods: data is expensive to collect and cheap to discard. Off-policy methods like SAC address this by maintaining a replay buffer of arbitrary age and correcting for distributional shift with importance weights throughout, but they require careful hyperparameter tuning and can be unstable in discrete action spaces. The right choice between on-policy and off-policy methods depends on the environment's data-collection cost and the degree to which accurate off-policy correction is tractable. For environments with fast simulation, on-policy PPO often wins in wall-clock time despite its data inefficiency. For environments where each step is expensive — physical robotics, expensive simulators, human-in-the-loop systems — the sample efficiency of off-policy methods is worth the additional complexity.

The architectural and theoretical bridge from pure value-based methods to pure policy gradient methods is thus not a sharp boundary but a continuous design space. Actor-critic methods occupy the interior of this space, using a value function to control variance (the critic's role) while maintaining a differentiable policy for direct gradient optimization (the actor's role). GAE controls where on the bias-variance curve the advantage estimator sits. PPO's clipping mechanism controls how far the policy is allowed to move per update. The practitioner's job is to calibrate these mechanisms to the statistical properties of the specific environment at hand — and to read the training diagnostics carefully enough to know which knob to turn when training goes wrong.
