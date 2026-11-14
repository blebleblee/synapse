# Operational Verification Labs: Reinforcement Learning

## Objective & Environment Setup

Reinforcement learning occupies a distinct position in the machine learning taxonomy. Unlike supervised learning, where labeled examples guide model updates, or unsupervised learning, where structure emerges from unlabeled data distributions, reinforcement learning frames intelligence as sequential decision-making under uncertainty. An agent observes environmental state, selects actions according to a policy, receives scalar reward signals, and iteratively refines its behavior to maximize cumulative long-term return. This temporal credit assignment problem—determining which past actions contributed to delayed rewards—constitutes the central challenge that separates RL from other learning paradigms.

The mathematical foundation rests on Markov Decision Processes (MDPs), formalized as the tuple $(S, A, P, R, \gamma)$, where $S$ denotes the state space, $A$ the action space, $P(s'|s,a)$ the state transition probability, $R(s,a,s')$ the reward function, and $\gamma \in [0,1)$ the discount factor encoding temporal preference. The agent's policy $\pi(a|s)$ maps states to action probability distributions, and the objective becomes finding the optimal policy $\pi^*$ that maximizes the expected discounted return $\mathbb{E}_{\pi}\left[\sum_{t=0}^{\infty} \gamma^t r_t\right]$. Value functions—the state-value function $V^\pi(s)$ and action-value function $Q^\pi(s,a)$—provide scalar estimates of expected future reward and serve as the foundation for both policy evaluation and improvement.

Modern deep reinforcement learning combines classical RL algorithms with neural function approximators, enabling agents to operate in high-dimensional continuous state spaces that traditional tabular methods cannot address. Deep Q-Networks (DQN) approximate the action-value function using convolutional networks, stabilizing learning through experience replay and target networks. Policy gradient methods like Proximal Policy Optimization (PPO) directly optimize parameterized policies through gradient ascent on expected return, employing clipped surrogate objectives to prevent destructive large updates. Actor-critic architectures unify both approaches, maintaining separate policy and value networks that bootstrap from each other's estimates.

This lab grounds you in production RL engineering through three progressively complex exercises. You will implement a complete DQN agent for the CartPole control task, instrument PPO for continuous control in the LunarLander environment, and stress-test trained policies against adversarial perturbations and distributional shift. Each exercise demands full implementation with working training loops, evaluation harnesses, hyperparameter sweeps, and diagnostic telemetry. You will profile GPU memory consumption, diagnose gradient explosion, implement reward shaping strategies, and verify policy robustness through systematic perturbation testing.

Your working environment requires Python 3.11 or later with PyTorch 2.0+, OpenAI Gymnasium for standardized RL environments, NumPy for numerical computation, Matplotlib and TensorBoard for visualization, and Weights & Biases for experiment tracking. Establish a clean virtual environment and install dependencies with the following sequence:

```bash
python3.11 -m venv rl_lab_env
source rl_lab_env/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install gymnasium[classic-control,box2d] numpy matplotlib tensorboard wandb tqdm
```

Verify your environment by instantiating a Gymnasium environment and confirming CUDA availability for GPU acceleration:

```python
import gymnasium as gym
import torch
import numpy as np

env = gym.make('CartPole-v1', render_mode='rgb_array')
print(f"Observation space: {env.observation_space}")
print(f"Action space: {env.action_space}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
env.close()
```

The CartPole environment exposes a four-dimensional continuous state vector encoding cart position, cart velocity, pole angle, and pole angular velocity, with a discrete binary action space representing leftward or rightward force application. The episode terminates when the pole angle exceeds ±12 degrees or the cart position exceeds ±2.4 units, with each timestep yielding a reward of +1. This sparse reward structure demands temporal credit assignment across hundreds of timesteps.

## Exercise 1: Hands-On Implementation & Pipeline Execution

Deep Q-Networks approximate the optimal action-value function $Q^*(s,a)$ through a neural network parameterized by weights $\theta$. The network ingests state vectors and outputs Q-values for each action, enabling action selection via $\arg\max_a Q(s,a;\theta)$. Training proceeds by minimizing the temporal difference error between predicted Q-values and bootstrapped targets derived from the Bellman optimality equation: $Q^*(s,a) = \mathbb{E}_{s'}[r + \gamma \max_{a'} Q^*(s',a')]$. Two critical stabilization techniques prevent divergence in the nonlinear function approximation regime: experience replay breaks temporal correlation by sampling transitions uniformly from a replay buffer, and a target network $\theta^-$ updated periodically provides stable bootstrapping targets while the online network $\theta$ learns continuously.

Implement the complete DQN agent in a single executable script that encompasses the neural network architecture, replay buffer, epsilon-greedy exploration schedule, training loop with target network synchronization, and evaluation harness. The following implementation provides production-grade code with proper device management, gradient clipping, and telemetry instrumentation:

```python
import gymnasium as gym
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
import matplotlib.pyplot as plt
from tqdm import tqdm

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (np.array(states), np.array(actions), np.array(rewards), 
                np.array(next_states), np.array(dones))
    
    def __len__(self):
        return len(self.buffer)

class DQN(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, x):
        return self.network(x)

class DQNAgent:
    def __init__(self, state_dim, action_dim, learning_rate=1e-3, gamma=0.99, 
                 epsilon_start=1.0, epsilon_end=0.01, epsilon_decay=0.995,
                 buffer_capacity=100000, batch_size=64, target_update_freq=10,
                 device='cuda'):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        self.online_network = DQN(state_dim, action_dim).to(self.device)
        self.target_network = DQN(state_dim, action_dim).to(self.device)
        self.target_network.load_state_dict(self.online_network.state_dict())
        self.target_network.eval()
        
        self.optimizer = optim.Adam(self.online_network.parameters(), lr=learning_rate)
        self.replay_buffer = ReplayBuffer(buffer_capacity)
        self.update_counter = 0
        
    def select_action(self, state, explore=True):
        if explore and random.random() < self.epsilon:
            return random.randrange(self.action_dim)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.online_network(state_tensor)
            return q_values.argmax(dim=1).item()
    
    def train_step(self):
        if len(self.replay_buffer) < self.batch_size:
            return None
        
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)
        
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        current_q_values = self.online_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(dim=1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        loss = nn.functional.mse_loss(current_q_values, target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.online_network.parameters(), max_norm=10.0)
        self.optimizer.step()
        
        self.update_counter += 1
        if self.update_counter % self.target_update_freq == 0:
            self.target_network.load_state_dict(self.online_network.state_dict())
        
        return loss.item()
    
    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

def train_dqn(env_name='CartPole-v1', num_episodes=500, max_steps=500):
    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    
    agent = DQNAgent(state_dim, action_dim)
    
    episode_rewards = []
    episode_losses = []
    
    progress_bar = tqdm(range(num_episodes), desc="Training DQN")
    
    for episode in progress_bar:
        state, _ = env.reset()
        episode_reward = 0
        episode_loss_sum = 0
        loss_count = 0
        
        for step in range(max_steps):
            action = agent.select_action(state, explore=True)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            
            agent.replay_buffer.push(state, action, reward, next_state, float(done))
            
            loss = agent.train_step()
            if loss is not None:
                episode_loss_sum += loss
                loss_count += 1
            
            state = next_state
            episode_reward += reward
            
            if done:
                break
        
        agent.decay_epsilon()
        episode_rewards.append(episode_reward)
        avg_loss = episode_loss_sum / loss_count if loss_count > 0 else 0
        episode_losses.append(avg_loss)
        
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            progress_bar.set_postfix({
                'Avg Reward': f'{avg_reward:.2f}',
                'Epsilon': f'{agent.epsilon:.3f}',
                'Loss': f'{avg_loss:.4f}'
            })
    
    env.close()
    return agent, episode_rewards, episode_losses

def evaluate_agent(agent, env_name='CartPole-v1', num_episodes=100, render=False):
    render_mode = 'human' if render else 'rgb_array'
    env = gym.make(env_name, render_mode=render_mode)
    
    eval_rewards = []
    
    for episode in range(num_episodes):
        state, _ = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action = agent.select_action(state, explore=False)
            state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            episode_reward += reward
        
        eval_rewards.append(episode_reward)
    
    env.close()
    
    mean_reward = np.mean(eval_rewards)
    std_reward = np.std(eval_rewards)
    
    print(f"\nEvaluation over {num_episodes} episodes:")
    print(f"Mean reward: {mean_reward:.2f} ± {std_reward:.2f}")
    print(f"Min reward: {np.min(eval_rewards):.2f}")
    print(f"Max reward: {np.max(eval_rewards):.2f}")
    
    return eval_rewards

def plot_training_curves(episode_rewards, episode_losses):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.plot(episode_rewards, alpha=0.6, label='Episode Reward')
    window = 10
    rolling_mean = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
    ax1.plot(range(window-1, len(episode_rewards)), rolling_mean, 
             linewidth=2, label=f'{window}-Episode Moving Average')
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Total Reward')
    ax1.set_title('Training Rewards')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(episode_losses, alpha=0.6, label='TD Loss')
    rolling_loss = np.convolve(episode_losses, np.ones(window)/window, mode='valid')
    ax2.plot(range(window-1, len(episode_losses)), rolling_loss, 
             linewidth=2, label=f'{window}-Episode Moving Average')
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Loss')
    ax2.set_title('Training Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dqn_training_curves.png', dpi=150, bbox_inches='tight')
    print("\nTraining curves saved to dqn_training_curves.png")
    plt.close()

if __name__ == "__main__":
    print("Training DQN agent on CartPole-v1...")
    agent, rewards, losses = train_dqn(num_episodes=500)
    
    plot_training_curves(rewards, losses)
    
    eval_rewards = evaluate_agent(agent, num_episodes=100)
    
    torch.save({
        'online_network': agent.online_network.state_dict(),
        'target_network': agent.target_network.state_dict(),
        'optimizer': agent.optimizer.state_dict(),
        'episode_rewards': rewards,
        'episode_losses': losses
    }, 'dqn_cartpole_checkpoint.pt')
    print("\nCheckpoint saved to dqn_cartpole_checkpoint.pt")
```

Execute this training script from your terminal within the activated virtual environment:

```bash
python dqn_cartpole.py
```

The training loop proceeds through 500 episodes, each consisting of up to 500 timesteps. During initial episodes, the epsilon-greedy exploration schedule maintains high random action probability, enabling the agent to discover reward-yielding trajectories. As epsilon decays exponentially toward 0.01, the agent increasingly exploits learned Q-value estimates. The replay buffer accumulates 100,000 transitions, breaking temporal correlation inherent in sequential environment interaction. Batch sampling draws 64 random transitions for each gradient update, computing the mean squared temporal difference error between online network predictions and target network bootstrapped estimates.

Gradient clipping with maximum L2 norm of 10.0 prevents exploding gradients that commonly arise in early training when Q-value estimates exhibit high variance. The target network synchronizes with online network weights every 10 updates, providing stable regression targets that mitigate the moving target problem inherent in bootstrapping from the same network being updated. CartPole's sparse reward structure—constant +1 per timestep until failure—demands that the agent learn to balance the pole through credit assignment across hundreds of sequential decisions.

Monitor training progress through the progress bar displaying rolling average reward, current epsilon, and mean TD loss. Successful training manifests as episode rewards climbing from random baseline (~20-30 steps) toward the theoretical maximum of 500 steps. The saved training curves visualize both raw episodic rewards and 10-episode moving averages, revealing learning dynamics and convergence behavior. Evaluation over 100 episodes with exploration disabled measures policy quality through mean and standard deviation of cumulative rewards.

Inspect the saved checkpoint to examine learned Q-value structure. Load the trained network and visualize Q-values across the state space:

```python
import torch
import numpy as np
import matplotlib.pyplot as plt
from dqn_cartpole import DQN

checkpoint = torch.load('dqn_cartpole_checkpoint.pt')
state_dim = 4
action_dim = 2
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

network = DQN(state_dim, action_dim).to(device)
network.load_state_dict(checkpoint['online_network'])
network.eval()

cart_positions = np.linspace(-2.4, 2.4, 50)
pole_angles = np.linspace(-0.2, 0.2, 50)

q_value_diff = np.zeros((len(pole_angles), len(cart_positions)))

for i, angle in enumerate(pole_angles):
    for j, position in enumerate(cart_positions):
        state = np.array([position, 0.0, angle, 0.0], dtype=np.float32)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
        
        with torch.no_grad():
            q_values = network(state_tensor).cpu().numpy()[0]
        
        q_value_diff[i, j] = q_values[1] - q_values[0]

plt.figure(figsize=(10, 8))
plt.imshow(q_value_diff, extent=[-2.4, 2.4, -0.2, 0.2], 
           aspect='auto', origin='lower', cmap='RdBu_r')
plt.colorbar(label='Q(s, right) - Q(s, left)')
plt.xlabel('Cart Position')
plt.ylabel('Pole Angle (radians)')
plt.title('Learned Q-Value Difference Across State Space')
plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
plt.axvline(x=0, color='black', linestyle='--', alpha=0.5)
plt.savefig('q_value_heatmap.png', dpi=150, bbox_inches='tight')
print("Q-value heatmap saved to q_value_heatmap.png")
plt.close()
```

The resulting heatmap exposes the policy's learned control strategy. Positive values indicate preference for rightward action, negative values for leftward action. The boundary between positive and negative regions traces the learned switching surface where the optimal policy transitions between actions. For CartPole, you should observe that when the pole tilts right (positive angle), the agent prefers rightward motion to push the cart under the pole, and symmetrically for leftward tilt. This reveals the learned bang-bang control policy characteristic of underactuated mechanical systems.

Profile GPU memory consumption during training by instrumenting CUDA allocation tracking:

```python
if torch.cuda.is_available():
    torch.cuda.reset_peak_memory_stats()
    agent, rewards, losses = train_dqn(num_episodes=100)
    peak_memory = torch.cuda.max_memory_allocated() / (1024**3)
    print(f"\nPeak GPU memory usage: {peak_memory:.3f} GB")
    print(torch.cuda.memory_summary())
```

For the DQN architecture with 128-unit hidden layers and batch size 64, expect peak memory consumption under 100 MB, dominated by gradient computation and optimizer state rather than model parameters. This modest footprint reflects CartPole's low-dimensional state space and small network capacity.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

Reinforcement learning exhibits extreme sensitivity to hyperparameter configuration. Learning rate, discount factor, exploration schedule, network architecture, replay buffer capacity, batch size, and target update frequency interact in complex nonlinear ways to determine convergence speed, sample efficiency, final policy quality, and training stability. Systematic hyperparameter search transforms heuristic tuning into empirical science, exposing performance landscapes and identifying robust configurations that generalize across similar tasks.

Policy gradient methods circumvent Q-function approximation by directly parameterizing the policy $\pi(a|s;\theta)$ and optimizing expected return through gradient ascent. The policy gradient theorem establishes that $\nabla_\theta J(\theta) \propto \mathbb{E}_\pi[\nabla_\theta \log \pi(a|s;\theta) Q^\pi(s,a)]$, enabling gradient estimation from sampled trajectories. Proximal Policy Optimization (PPO) stabilizes policy gradient learning through a clipped surrogate objective that constrains policy updates to a trust region, preventing catastrophic performance collapse from large parameter changes. The PPO objective balances policy improvement with KL-divergence regularization:

$$L^{CLIP}(\theta) = \mathbb{E}_t\left[\min\left(r_t(\theta)\hat{A}_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t\right)\right]$$

where $r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)}$ denotes the probability ratio between new and old policies, $\hat{A}_t$ the advantage estimate, and $\epsilon$ the clipping threshold typically set to 0.2.

Implement a complete PPO agent for the LunarLander-v2 environment, which presents continuous state observations and discrete action selection for a spacecraft descending toward a landing pad. The environment provides eight-dimensional state vectors encoding position, velocity, angle, angular velocity, and leg ground contact indicators, with four discrete actions: do nothing, fire left engine, fire main engine, and fire right engine. Reward shaping combines landing proximity, velocity penalties, fuel consumption costs, and terminal bonuses for successful landings.

Create a modular PPO implementation with separate policy and value networks, generalized advantage estimation (GAE) for variance-reduced advantage computation, and orthogonal weight initialization for improved gradient flow:

```python
import gymnasium as gym
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.distributions import Categorical
from tqdm import tqdm
import json

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super(ActorCritic, self).__init__()
        
        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)
        )
        
        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)
    
    def forward(self, state):
        action_probs = self.actor(state)
        state_value = self.critic(state)
        return action_probs, state_value
    
    def get_action(self, state):
        action_probs, _ = self.forward(state)
        dist = Categorical(action_probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action)
    
    def evaluate(self, states, actions):
        action_probs, state_values = self.forward(states)
        dist = Categorical(action_probs)
        action_log_probs = dist.log_prob(actions)
        dist_entropy = dist.entropy()
        return action_log_probs, state_values.squeeze(-1), dist_entropy

class PPOAgent:
    def __init__(self, state_dim, action_dim, learning_rate=3e-4, gamma=0.99, 
                 gae_lambda=0.95, clip_epsilon=0.2, value_coef=0.5, 
                 entropy_coef=0.01, max_grad_norm=0.5, device='cuda'):
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        self.max_grad_norm = max_grad_norm
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        self.policy = ActorCritic(state_dim, action_dim).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)
        
    def compute_gae(self, rewards, values, dones, next_value):
        advantages = []
        gae = 0
        
        values = values + [next_value]
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        returns = [adv + val for adv, val in zip(advantages, values[:-1])]
        return advantages, returns
    
    def update(self, trajectories, num_epochs=10, batch_size=64):
        states = torch.FloatTensor(trajectories['states']).to(self.device)
        actions = torch.LongTensor(trajectories['actions']).to(self.device)
        old_log_probs = torch.FloatTensor(trajectories['log_probs']).to(self.device)
        returns = torch.FloatTensor(trajectories['returns']).to(self.device)
        advantages = torch.FloatTensor(trajectories['advantages']).to(self.device)
        
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        dataset_size = states.shape[0]
        indices = np.arange(dataset_size)
        
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy = 0
        num_updates = 0
        
        for epoch in range(num_epochs):
            np.random.shuffle(indices)
            
            for start_idx in range(0, dataset_size, batch_size):
                batch_indices = indices[start_idx:start_idx + batch_size]
                
                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_returns = returns[batch_indices]
                batch_advantages = advantages[batch_indices]
                
                new_log_probs, state_values, entropy = self.policy.evaluate(
                    batch_states, batch_actions
                )
                
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 
                                   1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                value_loss = nn.functional.mse_loss(state_values, batch_returns)
                
                entropy_loss = -entropy.mean()
                
                loss = (policy_loss + self.value_coef * value_loss + 
                       self.entropy_coef * entropy_loss)
                
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.optimizer.step()
                
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy += entropy.mean().item()
                num_updates += 1
        
        return {
            'policy_loss': total_policy_loss / num_updates,
            'value_loss': total_value_loss / num_updates,
            'entropy': total_entropy / num_updates
        }

def collect_trajectories(env, agent, num_steps=2048):
    trajectories = {
        'states': [],
        'actions': [],
        'log_probs': [],
        'rewards': [],
        'values': [],
        'dones': []
    }
    
    state, _ = env.reset()
    
    for _ in range(num_steps):
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(agent.device)
        
        with torch.no_grad():
            _, value = agent.policy(state_tensor)
            action, log_prob = agent.policy.get_action(state_tensor)
        
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        
        trajectories['states'].append(state)
        trajectories['actions'].append(action)
        trajectories['log_probs'].append(log_prob.item())
        trajectories['rewards'].append(reward)
        trajectories['values'].append(value.item())
        trajectories['dones'].append(float(done))
        
        state = next_state
        
        if done:
            state, _ = env.reset()
    
    with torch.no_grad():
        next_state_tensor = torch.FloatTensor(state).unsqueeze(0).to(agent.device)
        _, next_value = agent.policy(next_state_tensor)
        next_value = next_value.item()
    
    advantages, returns = agent.compute_gae(
        trajectories['rewards'], 
        trajectories['values'], 
        trajectories['dones'],
        next_value
    )
    
    trajectories['advantages'] = advantages
    trajectories['returns'] = returns
    
    return trajectories

def train_ppo(env_name='LunarLander-v2', num_iterations=500, steps_per_iter=2048,
              learning_rate=3e-4, gamma=0.99, gae_lambda=0.95, clip_epsilon=0.2):
    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    
    agent = PPOAgent(state_dim, action_dim, learning_rate=learning_rate, 
                    gamma=gamma, gae_lambda=gae_lambda, clip_epsilon=clip_epsilon)
    
    iteration_rewards = []
    iteration_metrics = []
    
    progress_bar = tqdm(range(num_iterations), desc="Training PPO")
    
    for iteration in progress_bar:
        trajectories = collect_trajectories(env, agent, num_steps=steps_per_iter)
        
        metrics = agent.update(trajectories)
        
        episode_rewards = []
        episode_reward = 0
        for reward, done in zip(trajectories['rewards'], trajectories['dones']):
            episode_reward += reward
            if done:
                episode_rewards.append(episode_reward)
                episode_reward = 0
        
        mean_reward = np.mean(episode_rewards) if episode_rewards else 0
        iteration_rewards.append(mean_reward)
        iteration_metrics.append(metrics)
        
        if (iteration + 1) % 10 == 0:
            avg_reward = np.mean(iteration_rewards[-10:])
            progress_bar.set_postfix({
                'Avg Reward': f'{avg_reward:.2f}',
                'Policy Loss': f'{metrics["policy_loss"]:.4f}',
                'Value Loss': f'{metrics["value_loss"]:.4f}'
            })
    
    env.close()
    return agent, iteration_rewards, iteration_metrics

def hyperparameter_sweep():
    learning_rates = [1e-4, 3e-4, 1e-3]
    clip_epsilons = [0.1, 0.2, 0.3]
    gae_lambdas = [0.90, 0.95, 0.98]
    
    results = []
    
    for lr in learning_rates:
        for clip_eps in clip_epsilons:
            for gae_lambda in gae_lambdas:
                config = {
                    'learning_rate': lr,
                    'clip_epsilon': clip_eps,
                    'gae_lambda': gae_lambda
                }
                
                print(f"\nTraining with config: {config}")
                
                agent, rewards, metrics = train_ppo(
                    num_iterations=300,
                    learning_rate=lr,
                    clip_epsilon=clip_eps,
                    gae_lambda=gae_lambda
                )
                
                final_performance = np.mean(rewards[-50:])
                
                results.append({
                    'config': config,
                    'final_performance': final_performance,
                    'rewards': rewards,
                    'metrics': metrics
                })
                
                print(f"Final performance: {final_performance:.2f}")
    
    results.sort(key=lambda x: x['final_performance'], reverse=True)
    
    with open('hyperparameter_sweep_results.json', 'w') as f:
        json.dump([{
            'config': r['config'],
            'final_performance': r['final_performance']
        } for r in results], f, indent=2)
    
    print("\n=== Top 5 Configurations ===")
    for i, result in enumerate(results[:5], 1):
        print(f"{i}. {result['config']}")
        print(f"   Final performance: {result['final_performance']:.2f}\n")
    
    return results

if __name__ == "__main__":
    print("Starting hyperparameter sweep for PPO on LunarLander-v2...")
    results = hyperparameter_sweep()
```

Execute the hyperparameter sweep, which systematically explores 27 configurations across three learning rates, three clip thresholds, and three GAE lambda values:

```bash
python ppo_hyperparameter_sweep.py
```

This exhaustive search requires approximately 8-12 hours on modern GPU hardware, training 27 independent agents for 300 iterations each. The sweep exposes performance sensitivity to hyperparameter configuration, revealing interaction effects between learning rate and clipping threshold. High learning rates paired with aggressive clipping (epsilon = 0.1) often yield unstable training, while conservative clipping (epsilon = 0.3) tolerates larger policy updates but may converge more slowly.

The GAE lambda parameter trades bias and variance in advantage estimation. Values near 0.90 produce low-variance but higher-bias estimates by truncating temporal bootstrapping earlier, while values near 0.98 reduce bias at the cost of increased variance. LunarLander's episodic structure and moderate episode length (typically 200-400 steps) generally favor intermediate lambda values around 0.95.

Analyze the sweep results by loading the JSON output and visualizing performance distributions:

```python
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

with open('hyperparameter_sweep_results.json', 'r') as f:
    results = json.load(f)

learning_rates = sorted(list(set([r['config']['learning_rate'] for r in results])))
clip_epsilons = sorted(list(set([r['config']['clip_epsilon'] for r in results])))
gae_lambdas = sorted(list(set([r['config']['gae_lambda'] for r in results])))

performance_matrix = np.zeros((len(clip_epsilons), len(learning_rates)))

for result in results:
    lr = result['config']['learning_rate']
    clip_eps = result['config']['clip_epsilon']
    
    lr_idx = learning_rates.index(lr)
    clip_idx = clip_epsilons.index(clip_eps)
    
    performance_matrix[clip_idx, lr_idx] = result['final_performance']

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(performance_matrix, cmap='viridis', aspect='auto')

ax.set_xticks(np.arange(len(learning_rates)))
ax.set_yticks(np.arange(len(clip_epsilons)))
ax.set_xticklabels([f'{lr:.0e}' for lr in learning_rates])
ax.set_yticklabels([f'{eps:.2f}' for eps in clip_epsilons])

ax.set_xlabel('Learning Rate', fontsize=12)
ax.set_ylabel('Clip Epsilon', fontsize=12)
ax.set_title('PPO Performance Across Hyperparameters (GAE λ averaged)', fontsize=14)

for i in range(len(clip_epsilons)):
    for j in range(len(learning_rates)):
        text = ax.text(j, i, f'{performance_matrix[i, j]:.0f}',
                      ha="center", va="center", color="white", fontsize=10)

plt.colorbar(im, ax=ax, label='Final Performance')
plt.tight_layout()
plt.savefig('hyperparameter_heatmap.png', dpi=150, bbox_inches='tight')
print("Hyperparameter heatmap saved to hyperparameter_heatmap.png")
plt.close()
```

The resulting heatmap exposes the performance landscape. Typical successful configurations for LunarLander cluster around learning rate 3e-4, clip epsilon 0.2, and GAE lambda 0.95, achieving mean rewards above 200 points. Extreme configurations—very high learning rates or very tight clipping—often fail to converge, manifesting as low or negative mean rewards.

Benchmark your best configuration against the baseline random policy and a hand-tuned heuristic controller:

```python
def benchmark_policies():
    env = gym.make('LunarLander-v2')
    
    def random_policy(state):
        return env.action_space.sample()
    
    def heuristic_policy(state):
        x, y, vx, vy, angle, angular_vel, left_leg, right_leg = state
        
        if y > 0 or vy > 0:
            return 2
        
        if abs(angle) > 0.2:
            return 1 if angle > 0 else 3
        
        if abs(vx) > 0.5:
            return 1 if vx < 0 else 3
        
        return 0
    
    checkpoint = torch.load('ppo_best_checkpoint.pt')
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    ppo_policy = ActorCritic(state_dim, action_dim).to(device)
    ppo_policy.load_state_dict(checkpoint['policy'])
    ppo_policy.eval()
    
    def ppo_policy_fn(state):
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            action_probs, _ = ppo_policy(state_tensor)
            return torch.argmax(action_probs, dim=1).item()
    
    policies = {
        'Random': random_policy,
        'Heuristic': heuristic_policy,
        'PPO': ppo_policy_fn
    }
    
    num_eval_episodes = 100
    
    results = {}
    
    for name, policy_fn in policies.items():
        episode_rewards = []
        
        for _ in tqdm(range(num_eval_episodes), desc=f"Evaluating {name}"):
            state, _ = env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                action = policy_fn(state)
                state, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward
            
            episode_rewards.append(episode_reward)
        
        results[name] = {
            'mean': np.mean(episode_rewards),
            'std': np.std(episode_rewards),
            'min': np.min(episode_rewards),
            'max': np.max(episode_rewards)
        }
    
    env.close()
    
    print("\n=== Policy Benchmark Results ===")
    for name, stats in results.items():
        print(f"{name}:")
        print(f"  Mean: {stats['mean']:.2f} ± {stats['std']:.2f}")
        print(f"  Range: [{stats['min']:.2f}, {stats['max']:.2f}]\n")
    
    return results

benchmark_policies()
```

The benchmark reveals that random action selection yields mean rewards around -150, reflecting frequent crashes and fuel waste. The simple heuristic controller achieves modest positive rewards around 50-100 by maintaining upright orientation and decelerating during descent, but lacks the fine-grained control needed for soft landings. The trained PPO agent consistently exceeds 200 points, demonstrating successful landing, minimal fuel consumption, and centered touchdown.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

Production deployment of reinforcement learning systems demands rigorous verification beyond mean performance metrics. Trained policies must exhibit robustness to state perturbations, distributional shift, adversarial inputs, and edge cases underrepresented in training data. Stress testing exposes failure modes through systematic perturbation injection, worst-case scenario generation, and counterfactual analysis. This exercise implements a comprehensive robustness evaluation suite that quantifies policy degradation under varying perturbation magnitudes and characterizes failure modes through failure case clustering.

State space perturbations model sensor noise, actuator delays, and environmental variations that training simulators fail to capture. Gaussian noise injection with varying standard deviations tests graceful degradation as observation quality deteriorates. Adversarial perturbations—small targeted modifications that maximize policy failure—expose worst-case vulnerabilities through gradient-based attack synthesis. Distributional shift testing evaluates transfer performance to modified environment dynamics, such as altered gravity or increased wind turbulence.

Implement a modular robustness testing framework that systematically perturbs trained policies and quantifies performance degradation:

```python
import gymnasium as gym
import torch
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from tqdm import tqdm
import json

class PolicyRobustnessTester:
    def __init__(self, policy, env_name='LunarLander-v2', device='cuda'):
        self.policy = policy
        self.policy.eval()
        self.env_name = env_name
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
    
    def evaluate_with_noise(self, noise_levels, num_episodes=50):
        results = defaultdict(list)
        
        for noise_std in noise_levels:
            env = gym.make(self.env_name)
            
            for _ in tqdm(range(num_episodes), 
                         desc=f"Noise σ={noise_std:.3f}", leave=False):
                state, _ = env.reset()
                episode_reward = 0
                done = False
                
                while not done:
                    noisy_state = state + np.random.normal(0, noise_std, state.shape)
                    
                    with torch.no_grad():
                        state_tensor = torch.FloatTensor(noisy_state).unsqueeze(0).to(self.device)
                        action_probs, _ = self.policy(state_tensor)
                        action = torch.argmax(action_probs, dim=1).item()
                    
                    state, reward, terminated, truncated, _ = env.step(action)
                    done = terminated or truncated
                    episode_reward += reward
                
                results[noise_std].append(episode_reward)
            
            env.close()
        
        summary = {}
        for noise_std, rewards in results.items():
            summary[noise_std] = {
                'mean': np.mean(rewards),
                'std': np.std(rewards),
                'min': np.min(rewards),
                'max': np.max(rewards)
            }
        
        return summary
    
    def evaluate_with_actuator_delay(self, delay_steps, num_episodes=50):
        env = gym.make(self.env_name)
        results = []
        
        for _ in tqdm(range(num_episodes), desc=f"Delay={delay_steps} steps"):
            state, _ = env.reset()
            episode_reward = 0
            done = False
            
            action_buffer = [0] * delay_steps
            
            while not done:
                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                    action_probs, _ = self.policy(state_tensor)
                    new_action = torch.argmax(action_probs, dim=1).item()
                
                action_buffer.append(new_action)
                actual_action = action_buffer.pop(0)
                
                state, reward, terminated, truncated, _ = env.step(actual_action)
                done = terminated or truncated
                episode_reward += reward
            
            results.append(episode_reward)
        
        env.close()
        
        return {
            'mean': np.mean(results),
            'std': np.std(results),
            'min': np.min(results),
            'max': np.max(results)
        }
    
    def adversarial_perturbation_attack(self, num_episodes=20, epsilon=0.1, 
                                       num_steps=10):
        env = gym.make(self.env_name)
        attack_results = []
        
        for episode in tqdm(range(num_episodes), desc="Adversarial attacks"):
            state, _ = env.reset()
            episode_reward = 0
            done = False
            step_count = 0
            
            while not done:
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                state_tensor.requires_grad = True
                
                if step_count % num_steps == 0:
                    action_probs, _ = self.policy(state_tensor)
                    original_action = torch.argmax(action_probs, dim=1).item()
                    
                    loss = -action_probs[0, original_action]
                    loss.backward()
                    
                    perturbation = epsilon * torch.sign(state_tensor.grad)
                    adversarial_state = (state_tensor + perturbation).detach().cpu().numpy()[0]
                else:
                    adversarial_state = state
                
                with torch.no_grad():
                    adv_tensor = torch.FloatTensor(adversarial_state).unsqueeze(0).to(self.device)
                    action_probs, _ = self.policy(adv_tensor)
                    action = torch.argmax(action_probs, dim=1).item()
                
                state, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward
                step_count += 1
            
            attack_results.append(episode_reward)
        
        env.close()
        
        return {
            'mean': np.mean(attack_results),
            'std': np.std(attack_results),
            'min': np.min(attack_results),
            'max': np.max(attack_results)
        }
    
    def collect_failure_cases(self, num_episodes=100, reward_threshold=-100):
        env = gym.make(self.env_name)
        failure_cases = []
        
        for _ in tqdm(range(num_episodes), desc="Collecting failure cases"):
            state, _ = env.reset()
            episode_reward = 0
            trajectory = []
            done = False
            
            while not done:
                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                    action_probs, value = self.policy(state_tensor)
                    action = torch.argmax(action_probs, dim=1).item()
                
                trajectory.append({
                    'state': state.copy(),
                    'action': action,
                    'value': value.item()
                })
                
                state, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated
                episode_reward += reward
            
            if episode_reward < reward_threshold:
                failure_cases.append({
                    'episode_reward': episode_reward,
                    'trajectory': trajectory
                })
        
        env.close()
        return failure_cases

def comprehensive_robustness_evaluation(policy_path):
    checkpoint = torch.load(policy_path)
    state_dim = 8
    action_dim = 4
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    from ppo_hyperparameter_sweep import ActorCritic
    policy = ActorCritic(state_dim, action_dim).to(device)
    policy.load_state_dict(checkpoint['policy'])
    
    tester = PolicyRobustnessTester(policy)
    
    print("\n=== Gaussian Noise Robustness ===")
    noise_levels = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5]
    noise_results = tester.evaluate_with_noise(noise_levels, num_episodes=50)
    
    for noise_std, stats in noise_results.items():
        print(f"σ = {noise_std:.2f}: {stats['mean']:.2f} ± {stats['std']:.2f}")
    
    print("\n=== Actuator Delay Robustness ===")
    delay_levels = [0, 1, 2, 3, 5]
    delay_results = {}
    
    for delay in delay_levels:
        result = tester.evaluate_with_actuator_delay(delay, num_episodes=50)
        delay_results[delay] = result
        print(f"Delay = {delay} steps: {result['mean']:.2f} ± {result['std']:.2f}")
    
    print("\n=== Adversarial Robustness ===")
    epsilon_levels = [0.01, 0.05, 0.1, 0.2]
    adversarial_results = {}
    
    for epsilon in epsilon_levels:
        result = tester.adversarial_perturbation_attack(num_episodes=20, epsilon=epsilon)
        adversarial_results[epsilon] = result
        print(f"ε = {epsilon:.2f}: {result['mean']:.2f} ± {result['std']:.2f}")
    
    print("\n=== Failure Case Analysis ===")
    failure_cases = tester.collect_failure_cases(num_episodes=200, reward_threshold=-100)
    print(f"Failure rate: {len(failure_cases)/200*100:.1f}%")
    
    if failure_cases:
        failure_states = np.array([traj['state'] for case in failure_cases 
                                  for traj in case['trajectory']])
        
        print(f"\nFailure state statistics:")
        print(f"Mean position: {failure_states[:, 0].mean():.3f} ± {failure_states[:, 0].std():.3f}")
        print(f"Mean velocity: {failure_states[:, 2:4].mean():.3f} ± {failure_states[:, 2:4].std():.3f}")
        print(f"Mean angle: {failure_states[:, 4].mean():.3f} ± {failure_states[:, 4].std():.3f}")
    
    results_summary = {
        'noise_robustness': noise_results,
        'delay_robustness': delay_results,
        'adversarial_robustness': adversarial_results,
        'failure_rate': len(failure_cases) / 200
    }
    
    with open('robustness_evaluation_results.json', 'w') as f:
        json.dump({k: v for k, v in results_summary.items() if k != 'noise_robustness'}, 
                 f, indent=2, default=float)
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    noise_stds = list(noise_results.keys())
    noise_means = [noise_results[std]['mean'] for std in noise_stds]
    noise_stds_err = [noise_results[std]['std'] for std in noise_stds]
    
    axes[0].errorbar(noise_stds, noise_means, yerr=noise_stds_err, 
                    marker='o', capsize=5, linewidth=2)
    axes[0].set_xlabel('Noise Standard Deviation')
    axes[0].set_ylabel('Mean Episode Reward')
    axes[0].set_title('Gaussian Noise Robustness')
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    delays = list(delay_results.keys())
    delay_means = [delay_results[d]['mean'] for d in delays]
    delay_stds_err = [delay_results[d]['std'] for d in delays]
    
    axes[1].errorbar(delays, delay_means, yerr=delay_stds_err, 
                    marker='s', capsize=5, linewidth=2)
    axes[1].set_xlabel('Actuator Delay (steps)')
    axes[1].set_ylabel('Mean Episode Reward')
    axes[1].set_title('Actuator Delay Robustness')
    axes[1].grid(True, alpha=0.3)
    axes[1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    epsilons = list(adversarial_results.keys())
    adv_means = [adversarial_results[e]['mean'] for e in epsilons]
    adv_stds_err = [adversarial_results[e]['std'] for e in epsilons]
    
    axes[2].errorbar(epsilons, adv_means, yerr=adv_stds_err, 
                    marker='^', capsize=5, linewidth=2)
    axes[2].set_xlabel('Adversarial Perturbation ε')
    axes[2].set_ylabel('Mean Episode Reward')
    axes[2].set_title('Adversarial Robustness')
    axes[2].grid(True, alpha=0.3)
    axes[2].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('robustness_evaluation_plots.png', dpi=150, bbox_inches='tight')
    print("\nRobustness evaluation plots saved to robustness_evaluation_plots.png")
    plt.close()
    
    return results_summary

if __name__ == "__main__":
    comprehensive_robustness_evaluation('ppo_best_checkpoint.pt')
```

Execute the comprehensive robustness evaluation:

```bash
python policy_robustness_evaluation.py
```

The evaluation proceeds through four systematic stress tests. Gaussian noise injection with standard deviations from 0.0 to 0.5 models increasing sensor degradation. Well-trained policies typically maintain positive performance up to noise levels around 0.2, beyond which observation corruption overwhelms learned control strategies. Actuator delay testing simulates communication latency by buffering actions for 0-5 timesteps before execution. Single-step delays often reduce performance by 20-30%, while delays exceeding 3 steps frequently cause complete failure as the policy's reactive control loop desynchronizes from environment dynamics.

Adversarial perturbation attacks synthesize worst-case state modifications through gradient-based optimization. The fast gradient sign method (FGSM) computes the gradient of policy output with respect to input state, then perturbs the state in the direction that maximally reduces the probability of the current action. Perturbation magnitudes epsilon from 0.01 to 0.2 expose the policy's susceptibility to targeted attacks. Robustly trained policies degrade gracefully, while brittle policies exhibit catastrophic failures even under small perturbations.

Failure case collection accumulates trajectories where episode reward falls below -100, indicating crashes or severe fuel waste. Clustering failure states through k-means or principal component analysis reveals common failure modes. Typical failure patterns in LunarLander include high horizontal velocity at low altitude (sideways crashes), inverted orientation (flipped landings), and fuel depletion far from the landing pad. Analyzing value function estimates along failure trajectories diagnoses whether failures stem from incorrect value prediction (value network deficiency) or suboptimal action selection given accurate values (policy network deficiency).

Implement a failure mitigation strategy through reward shaping and curriculum learning. Augment the base reward function with auxiliary terms that penalize risky intermediate states:

```python
def shaped_reward_wrapper(env, shaping_coef=0.01):
    class ShapedRewardEnv(gym.Wrapper):
        def step(self, action):
            state, reward, terminated, truncated, info = self.env.step(action)
            
            x, y, vx, vy, angle, angular_vel, left_leg, right_leg = state
            
            shaping_penalty = 0.0
            
            shaping_penalty += shaping_coef * (vx**2 + vy**2)
            
            shaping_penalty += shaping_coef * abs(angle)
            
            if y < 0.5 and (abs(vx) > 0.5 or abs(vy) > 0.5):
                shaping_penalty += shaping_coef * 10.0
            
            shaped_reward = reward - shaping_penalty
            
            return state, shaped_reward, terminated, truncated, info
    
    return ShapedRewardEnv(env)

env = gym.make('LunarLander-v2')
shaped_env = shaped_reward_wrapper(env, shaping_coef=0.01)
```

Retrain the PPO agent on the shaped reward environment and compare robustness metrics against the baseline. Reward shaping typically improves sample efficiency and failure-case robustness by providing denser learning signals during early training, guiding the policy away from dangerous state regions before catastrophic failures occur.

## ML Diagnostic Cheat Sheet & Verification Checklist

This diagnostic reference provides systematic procedures for identifying and resolving common failure modes in reinforcement learning systems. Use this checklist during training, evaluation, and deployment to ensure policy quality and system reliability.

**Training Divergence Diagnosis:**
- Monitor TD loss magnitude and gradient norms. Exponentially increasing loss or gradient explosion indicates unstable learning.
- Check replay buffer composition for off-policy algorithms. Biased sampling or outdated transitions corrupt value estimates.
- Verify target network synchronization frequency. Too-frequent updates reintroduce moving target instability.
- Inspect epsilon decay schedule. Premature exploitation before sufficient exploration yields suboptimal local minima.
- Profile gradient statistics across layers. Vanishing or exploding gradients indicate network initialization or architecture issues.

**Sample Inefficiency Diagnosis:**
- Compute timesteps-to-threshold metric. Compare against published baselines for the environment.
- Analyze advantage estimate variance. High variance indicates inadequate value function accuracy or excessive GAE lambda.
- Measure action entropy over training. Premature entropy collapse signals insufficient exploration.
- Inspect value function prediction error on held-out states. Large errors reveal generalization failures.
- Verify discount factor alignment with episode horizon. Mismatch between gamma and typical episode length impairs credit assignment.

**Policy Brittleness Diagnosis:**
- Evaluate under state perturbations with increasing noise magnitudes. Sharp performance cliffs indicate overfitting.
- Measure performance variance across random seeds. High variance signals instability.
- Test on environment variations (altered dynamics, visual perturbations). Poor transfer reveals lack of robust features.
- Analyze failure case clustering. Concentrated failures in narrow state regions suggest training distribution mismatch.
- Verify policy smoothness through action consistency on nearby states. Erratic action changes indicate decision boundary fragility.

**Environment-Specific Verification:**
- Confirm observation space normalization. Unbounded or poorly scaled features impede neural network learning.
- Validate reward scaling and clipping. Extreme rewards destabilize value function estimation.
- Check episode length distribution. Truncated episodes bias value estimates and corrupt bootstrapping.
- Inspect action space coverage during training. Insufficient exploration of valid actions reduces policy expressiveness.
- Verify environment stochasticity level. Deterministic environments may not require robust policies.

**Deployment Safety Checklist:**
- Establish hard constraints on action outputs through safe projection operators.
- Implement anomaly detection for out-of-distribution states triggering fallback controllers.
- Deploy shadow policies for online performance comparison without affecting production.
- Monitor value function predictions as confidence estimates. Low values signal uncertain or risky states.
- Log state-action trajectories for post-hoc failure analysis and continuous improvement.

**Performance Profiling Commands:**
```bash
# Profile GPU memory consumption during training
python -c "import torch; torch.cuda.reset_peak_memory_stats(); exec(open('train_ppo.py').read()); print(f'Peak memory: {torch.cuda.max_memory_allocated()/(1024**3):.2f} GB')"

# Time training iteration throughput
python -m cProfile -s cumtime train_ppo.py | head -n 20

# Monitor GPU utilization during training
nvidia-smi dmon -s u -d 1 -c 100

# Verify gradient flow through network layers
python -c "from train_ppo import *; agent = PPOAgent(8, 4); trajectories = collect_trajectories(gym.make('LunarLander-v2'), agent, 256); agent.update(trajectories); [print(f'{name}: {param.grad.norm():.4f}') for name, param in agent.policy.named_parameters() if param.grad is not None]"
```

**Common Failure Modes and Mitigations:**

Exploding gradients manifest as NaN losses or diverging value estimates. Mitigate through gradient clipping (max norm 0.5-10.0), reduced learning rates (1e-4 to 1e-5), or batch normalization in value networks.

Collapsed exploration occurs when entropy bonus coefficient decays too aggressively or action distribution concentrates prematurely. Restore through higher entropy coefficients (0.01-0.1), curriculum learning with exploration phases, or intrinsic motivation rewards.

Value function overestimation introduces optimistic bias that propagates through bootstrapping. Correct through double Q-learning, clipped value targets, or reduced discount factors.

Catastrophic forgetting in continual learning scenarios requires experience replay mixing old and new data, elastic weight consolidation penalizing changes to important parameters, or progressive neural networks with frozen submodules.

Distributional shift between training and deployment environments demands domain randomization during training, online adaptation through meta-learning, or sim-to-real transfer techniques like domain adaptation networks.

This operational verification lab grounds you in production reinforcement learning engineering through complete implementations, systematic hyperparameter search, and comprehensive robustness evaluation. You have implemented DQN and PPO from first principles, profiled training performance, stress-tested policies against adversarial perturbations, and diagnosed failure modes through quantitative analysis. These techniques form the foundation for deploying RL systems in production environments where sample efficiency, robustness, and reliability are paramount.
