# Lesson 2: Value Iteration, Policy Iteration, Convergence Guarantees

## 1. First-Principles Intuition & Invariants

The planning problem in reinforcement learning reduces to a single mathematical question when the environment model is fully known: given a Markov Decision Process specified by its transition kernel $P(s'|s,a)$, reward function $R(s,a,s')$, and discount factor $\gamma \in [0,1)$, compute the optimal value function $V^*(s)$ and the deterministic optimal policy $\pi^*(s)$ without ever interacting with the environment. This is the domain of dynamic programming, and it rests on a recursive structural property of MDPs called the Bellman equation.

The Bellman optimality equation states that the value of any state under the optimal policy equals the expected return of the best available action, where future returns are discounted by $\gamma$:

$$V^*(s) = \max_a \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma V^*(s') \right]$$

This equation is self-referential: $V^*$ appears on both sides. The equation does not give $V^*$ directly; it defines $V^*$ as the fixed point of an operator. To make this precise, define the Bellman optimality operator $\mathcal{T}^*: \mathbb{R}^{|S|} \to \mathbb{R}^{|S|}$ as:

$$(\mathcal{T}^* V)(s) = \max_a \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma V(s') \right]$$

The optimal value function is the unique fixed point: $\mathcal{T}^* V^* = V^*$. The bootstrap mechanism is embedded in this definition. We estimate the value of a state using estimated values of successor states. This seems circular, and it would be dangerous without a guarantee that the circularity resolves. The guarantee comes from the contraction property.

$\mathcal{T}^*$ is a $\gamma$-contraction in the sup-norm. For any two value functions $V, W \in \mathbb{R}^{|S|}$:

$$\|\mathcal{T}^* V - \mathcal{T}^* W\|_\infty \leq \gamma \|V - W\|_\infty$$

The proof is a chain of elementary inequalities. For each state $s$, the max operator satisfies $|\max_a f(a) - \max_a g(a)| \leq \max_a |f(a) - g(a)|$. Applying this, then pulling the absolute value inside the expectation, then bounding each $|V(s') - W(s')|$ by $\|V - W\|_\infty$, and finally using the fact that $P(\cdot|s,a)$ is a probability distribution summing to 1, yields the contraction. Because $(\mathbb{R}^{|S|}, \|\cdot\|_\infty)$ is a complete metric space and $\mathcal{T}^*$ is a contraction with modulus $\gamma < 1$, the Banach fixed-point theorem guarantees that $V^*$ exists, is unique, and that repeated application of $\mathcal{T}^*$ from any initialization converges to $V^*$ at a geometric rate: $\|V_k - V^*\|_\infty \leq \gamma^k \|V_0 - V^*\|_\infty$.

There is a second operator of equal importance. For a fixed policy $\pi$, the Bellman expectation operator $\mathcal{T}^\pi$ computes the value of being in state $s$ and following $\pi$ henceforth:

$$(\mathcal{T}^\pi V)(s) = \sum_a \pi(a|s) \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma V(s') \right]$$

For a deterministic policy $\pi$, this simplifies to $(\mathcal{T}^\pi V)(s) = R(s,\pi(s)) + \gamma \sum_{s'} P(s'|s,\pi(s)) V(s')$. The operator $\mathcal{T}^\pi$ is also a $\gamma$-contraction, and its fixed point $V^\pi$ is the value function of policy $\pi$. Policy evaluation, the task of computing $V^\pi$ for a given $\pi$, is a simpler problem than finding $V^*$ because it removes the max operator and reduces to solving a linear system.

The policy improvement theorem is the bridge between policy evaluation and optimal control. If $\pi'$ is the greedy policy with respect to $V^\pi$, meaning $\pi'(s) = \arg\max_a Q^\pi(s,a)$ where $Q^\pi(s,a) = R(s,a) + \gamma \sum_{s'} P(s'|s,a) V^\pi(s')$, then $V^{\pi'} \geq V^\pi$ component-wise. The proof follows from applying the Bellman expectation operator of $\pi'$ to $V^\pi$: since $\pi'$ selects the action maximizing $Q^\pi$ at every state, $V^\pi \leq \mathcal{T}^{\pi'} V^\pi$. Iterating $\mathcal{T}^{\pi'}$ preserves the inequality and converges to $V^{\pi'}$, so $V^\pi \leq V^{\pi'}$. If $V^{\pi'} = V^\pi$, the policy is already optimal because $V^\pi = \mathcal{T}^{\pi'} V^\pi \leq \mathcal{T}^* V^\pi \leq V^*$, and the first inequality is tight when $\pi'$ is greedy.

These two operators, $\mathcal{T}^*$ and $\mathcal{T}^\pi$, and the policy improvement theorem, generate the two principal families of exact MDP solution algorithms. Value iteration applies $\mathcal{T}^*$ repeatedly until convergence. Policy iteration alternates between solving for $V^\pi$ exactly (policy evaluation via matrix inversion) and computing the greedy policy (policy improvement). Both are guaranteed to converge to $V^*$, but they trade per-iteration cost against iteration count in fundamentally different ways.

## 2. Core Architecture & Mechanics

### The MDP Specification

Before deriving the algorithms, we need a concrete MDP implementation. The following `GridworldMDP` encodes a two-dimensional grid navigation problem with stochastic transitions, terminal states, and configurable rewards. It precomputes the full transition tensor $P[s, a, s']$ and reward matrix $R[s, a]$ as dense NumPy arrays, which enables fully vectorized Bellman backups.

```python
import numpy as np
from dataclasses import dataclass, field
from typing import List, Set, Tuple, Dict, Optional
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


@dataclass
class GridworldMDP:
    rows: int = 8
    cols: int = 8
    slip_prob: float = 0.10
    step_reward: float = -0.01
    goal_reward: float = 1.0
    pit_reward: float = -1.0
    gamma: float = 0.95
    goal_states: List[int] = field(default_factory=list)
    pit_states: List[int] = field(default_factory=list)

    def __post_init__(self):
        self.n_states: int = self.rows * self.cols
        self.n_actions: int = 4
        if not self.goal_states:
            self.goal_states = [self.n_states - 1]
        self._terminal: Set[int] = set(self.goal_states) | set(self.pit_states)
        self._precompute()

    def _precompute(self) -> None:
        self.P = np.zeros((self.n_states, self.n_actions, self.n_states))
        self.R_sa = np.zeros((self.n_states, self.n_actions))

        deltas: List[Tuple[int, int]] = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        perp: List[Tuple[int, int]] = [(1, 3), (0, 2), (1, 3), (0, 2)]
        intended_p: float = 1.0 - 2.0 * self.slip_prob
        goal_set: Set[int] = set(self.goal_states)
        pit_set: Set[int] = set(self.pit_states)

        for s in range(self.n_states):
            r, c = divmod(s, self.cols)
            for a in range(self.n_actions):
                if s in self._terminal:
                    self.P[s, a, s] = 1.0
                    self.R_sa[s, a] = 0.0
                    continue

                for prob, act in [(intended_p, a),
                                   (self.slip_prob, perp[a][0]),
                                   (self.slip_prob, perp[a][1])]:
                    dr, dc = deltas[act]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        ns = nr * self.cols + nc
                    else:
                        ns = s
                    self.P[s, a, ns] += prob
                    r_sas = self.step_reward
                    if ns in goal_set:
                        r_sas += self.goal_reward
                    elif ns in pit_set:
                        r_sas += self.pit_reward
                    self.R_sa[s, a] += prob * r_sas

    def is_terminal(self, s: int) -> bool:
        return s in self._terminal
```

The transition model uses a slipping mechanism: with probability `1 - 2*slip_prob` the agent moves in the intended direction, and with probability `slip_prob` it moves in each of the two perpendicular directions. If a movement would exit the grid, the agent stays in place. Terminal states are absorbing: they transition to themselves with probability 1 and yield zero reward. The reward for a transition into a goal state includes the goal reward, and transitions into pits include the pit penalty. This structure creates a non-trivial planning problem where the optimal policy must balance the step cost against the risk of slipping into a pit.

### Value Iteration

Value iteration is the most direct application of the Bellman optimality operator. Starting from $V_0 = \mathbf{0}$ (or any initialization), each iteration computes $V_{k+1} = \mathcal{T}^* V_k$:

$$V_{k+1}(s) = \max_a \left[ R(s,a) + \gamma \sum_{s'} P(s'|s,a) V_k(s') \right]$$

The max over actions makes each update a full Bellman optimality backup. The algorithm terminates when the sup-norm change between successive iterations falls below a threshold derived from the contraction property.

The practical stopping criterion follows from the error bound. Since $\mathcal{T}^*$ is a $\gamma$-contraction, after $k$ iterations:

$$\|V_k - V^*\|_\infty \leq \frac{\gamma}{1-\gamma} \|V_k - V_{k-1}\|_\infty$$

To guarantee $\|V_k - V^*\|_\infty < \epsilon$, we stop when $\|V_k - V_{k-1}\|_\infty < \epsilon(1-\gamma)/\gamma$. For the greedy policy $\pi_k$ extracted from $V_k$, a tighter analysis gives $\|V^{\pi_k} - V^*\|_\infty \leq \frac{2\gamma}{1-\gamma} \|V_k - V_{k-1}\|_\infty$, so the threshold $\epsilon(1-\gamma)/(2\gamma)$ guarantees an $\epsilon$-optimal policy.

```python
def value_iteration(mdp: GridworldMDP,
                    target_accuracy: float = 1e-6,
                    max_iters: int = 100_000,
                    track_history: bool = True
                    ) -> Tuple[np.ndarray, np.ndarray, int, Dict]:
    V = np.zeros(mdp.n_states)
    terminal = np.array(list(mdp._terminal), dtype=int)
    gamma = mdp.gamma
    threshold = target_accuracy * (1.0 - gamma) / gamma if gamma > 0 else target_accuracy

    history: Dict = {'values': [], 'deltas': [], 'policies': []}

    for it in range(max_iters):
        Q = mdp.R_sa + gamma * (mdp.P @ V)
        V_new = np.max(Q, axis=1)
        if len(terminal) > 0:
            V_new[terminal] = 0.0

        delta = np.max(np.abs(V_new - V))
        V = V_new

        if track_history:
            history['values'].append(V.copy())
            history['deltas'].append(delta)
            history['policies'].append(np.argmax(Q, axis=1))

        if delta < threshold:
            break

    Q = mdp.R_sa + gamma * (mdp.P @ V)
    policy = np.argmax(Q, axis=1)

    return V, policy, it + 1, history
```

The core computation is the single line `Q = mdp.R_sa + gamma * (mdp.P @ V)`. The matrix-vector product `mdp.P @ V` exploits NumPy's broadcasting: $P$ has shape $(|S|, |A|, |S|)$ and $V$ has shape $(|S|,)$, so the product yields a $(|S|, |A|)$ array of expected discounted future values for each state-action pair. Adding the reward matrix and taking the row-wise max completes the Bellman backup. This vectorization eliminates Python-level loops over states and actions, reducing the per-iteration cost to a single BLAS call.

The convergence guarantee is geometric. Each iteration contracts the error by a factor of $\gamma$, so the number of iterations to reach accuracy $\epsilon$ from initialization $V_0$ is:

$$k \geq \frac{\log\left(\frac{\epsilon(1-\gamma)}{\|V_1 - V_0\|_\infty}\right)}{\log(\gamma)}$$

For $\gamma = 0.95$ and $\epsilon = 10^{-6}$, this is approximately 570 iterations, regardless of the state space size. The total cost is $O(|S|^2|A| \cdot k)$, where $k$ depends on $\gamma$ and $\epsilon$ but not on $|S|$.

### Policy Iteration

Policy iteration decomposes the problem into two phases that alternate until the policy stabilizes. Policy evaluation solves the linear system $V^\pi = (I - \gamma P^\pi)^{-1} r^\pi$ exactly, where $P^\pi$ is the $|S| \times |S|$ transition matrix induced by policy $\pi$ (row $s$ is $P(s'|s, \pi(s))$), and $r^\pi$ is the vector of expected rewards under $\pi$. Policy improvement then computes the greedy policy $\pi'(s) = \arg\max_a [R(s,a) + \gamma \sum_{s'} P(s'|s,a) V^\pi(s')]$. If $\pi' = \pi$, the algorithm has converged.

```python
def policy_iteration(mdp: GridworldMDP,
                     max_iters: int = 1000,
                     track_history: bool = True
                     ) -> Tuple[np.ndarray, np.ndarray, int, Dict]:
    policy = np.zeros(mdp.n_states, dtype=int)
    gamma = mdp.gamma
    eye = np.eye(mdp.n_states)
    states = np.arange(mdp.n_states)
    terminal = np.array(list(mdp._terminal), dtype=int)

    history: Dict = {'values': [], 'policies': []}

    for it in range(max_iters):
        P_pi = mdp.P[states, policy, :]
        r_pi = mdp.R_sa[states, policy]
        A = eye - gamma * P_pi
        V = np.linalg.solve(A, r_pi)
        if len(terminal) > 0:
            V[terminal] = 0.0

        Q = mdp.R_sa + gamma * (mdp.P @ V)
        new_policy = np.argmax(Q, axis=1)

        if track_history:
            history['values'].append(V.copy())
            history['policies'].append(policy.copy())

        if np.array_equal(new_policy, policy):
            break
        policy = new_policy

    Q = mdp.R_sa + gamma * (mdp.P @ V)
    final_policy = np.argmax(Q, axis=1)

    return V, final_policy, it + 1, history
```

The matrix inversion $A^{-1} r^\pi$ is the expensive step. NumPy's `linalg.solve` uses LU decomposition with partial pivoting, which costs $O(|S|^3)$. The matrix $I - \gamma P^\pi$ is always invertible when $\gamma < 1$: $P^\pi$ is a stochastic matrix with spectral radius 1, so $I - \gamma P^\pi$ has eigenvalues $1 - \gamma \lambda$ where $|\lambda| \leq 1$, giving a minimum eigenvalue magnitude of $1 - \gamma > 0$.

Policy iteration's convergence is fundamentally different from value iteration's. The policy improvement theorem guarantees $V^{\pi_{k+1}} \geq V^{\pi_k}$ component-wise. Since there are exactly $|A|^{|S|}$ deterministic stationary policies, the strictly increasing value sequence cannot repeat a policy, so policy iteration converges in at most $|A|^{|S|}$ iterations. In practice, the iteration count is tiny, typically fewer than 20 even for large state spaces. The per-iteration cost is $O(|S|^3 + |S|^2|A|)$, dominated by the matrix solve.

The table below summarizes the computational trade-offs:

| Algorithm | Per-Iteration Cost | Iterations to Converge | Total Cost | Best Regime |
|-----------|-------------------|----------------------|------------|-------------|
| Value Iteration | $O(\|S\|^2\|A\|)$ | $O\left(\frac{\log \epsilon^{-1}}{1-\gamma}\right)$ | $O\left(\frac{\|S\|^2\|A\|\log \epsilon^{-1}}{1-\gamma}\right)$ | Large $\|S\|$, any $\gamma$ |
| Policy Iteration | $O(\|S\|^3 + \|S\|^2\|A\|)$ | $O(\|S\|\|A\|)$ worst, $\sim 10$ typical | $O(\|S\|^3 \cdot \text{iters})$ | Small-to-mid $\|S\|$, high $\gamma$ |
| Modified PI ($k$) | $O(k\|S\|^2\|A\| + \|S\|^2\|A\|)$ | $O\left(\frac{\log \epsilon^{-1}}{1-\gamma}\right)$ | Interpolates VI and PI | Tunable balance |

### Modified Policy Iteration

Modified policy iteration bridges the two extremes. Instead of solving policy evaluation exactly via matrix inversion, it performs $k$ steps of iterative policy evaluation using the Bellman expectation operator, then improves the policy. When $k=1$, the algorithm reduces to value iteration because the single evaluation step is just a Bellman backup under the greedy policy, which equals the Bellman optimality backup. When $k \to \infty$, it becomes full policy iteration.

```python
def modified_policy_iteration(mdp: GridworldMDP,
                               k: int = 5,
                               target_accuracy: float = 1e-6,
                               max_iters: int = 10_000,
                               track_history: bool = True
                               ) -> Tuple[np.ndarray, np.ndarray, int, Dict]:
    V = np.zeros(mdp.n_states)
    gamma = mdp.gamma
    states = np.arange(mdp.n_states)
    terminal = np.array(list(mdp._terminal), dtype=int)
    threshold = target_accuracy * (1.0 - gamma) / gamma if gamma > 0 else target_accuracy

    history: Dict = {'values': [], 'deltas': [], 'policies': []}

    for it in range(max_iters):
        Q = mdp.R_sa + gamma * (mdp.P @ V)
        policy = np.argmax(Q, axis=1)
        P_pi = mdp.P[states, policy, :]
        r_pi = mdp.R_sa[states, policy]

        for _ in range(k):
            V = r_pi + gamma * (P_pi @ V)
        if len(terminal) > 0:
            V[terminal] = 0.0

        if track_history and len(history['values']) > 0:
            delta = np.max(np.abs(V - history['values'][-1]))
            history['deltas'].append(delta)

        if track_history:
            history['values'].append(V.copy())
            history['policies'].append(policy.copy())

        if history['deltas'] and history['deltas'][-1] < threshold:
            break

    Q = mdp.R_sa + gamma * (mdp.P @ V)
    policy = np.argmax(Q, axis=1)

    return V, policy, it + 1, history
```

The convergence of modified policy iteration is guaranteed for any $k \geq 1$. The proof, due to Puterman and Shin (1978), shows that the value sequence is bounded, the Bellman residual converges to zero, and therefore $V_k \to V^*$. The practical advantage is that $k$ provides a tunable knob: small $k$ keeps iterations cheap but requires more outer iterations, while large $k$ approaches policy iteration's fast convergence at higher per-iteration cost. For many MDPs, $k \in [5, 20]$ offers a favorable balance.

### Benchmark Comparison

The following script instantiates an 8x8 Gridworld with a pit at the center, runs all three algorithms, and reports iteration counts, wall-clock times, and the sup-norm distance between each algorithm's solution and a reference solution computed by value iteration with extreme precision.

```python
def run_benchmark() -> Dict:
    mdp = GridworldMDP(
        rows=8, cols=8, slip_prob=0.15, step_reward=-0.02,
        goal_reward=1.0, pit_reward=-1.0, gamma=0.95,
        goal_states=[63],
        pit_states=[27, 28, 35, 36]
    )

    V_ref, pi_ref, _, _ = value_iteration(mdp, target_accuracy=1e-12, track_history=False)

    results: Dict = {}

    t0 = time.perf_counter()
    V_vi, pi_vi, iters_vi, hist_vi = value_iteration(mdp, target_accuracy=1e-6)
    t_vi = time.perf_counter() - t0
    results['Value Iteration'] = {
        'V': V_vi, 'policy': pi_vi, 'iterations': iters_vi,
        'time_ms': t_vi * 1000,
        'value_error': np.max(np.abs(V_vi - V_ref)),
        'policy_match': np.mean(pi_vi == pi_ref),
        'history': hist_vi
    }

    t0 = time.perf_counter()
    V_pi, pi_pi, iters_pi, hist_pi = policy_iteration(mdp)
    t_pi = time.perf_counter() - t0
    results['Policy Iteration'] = {
        'V': V_pi, 'policy': pi_pi, 'iterations': iters_pi,
        'time_ms': t_pi * 1000,
        'value_error': np.max(np.abs(V_pi - V_ref)),
        'policy_match': np.mean(pi_pi == pi_ref),
        'history': hist_pi
    }

    t0 = time.perf_counter()
    V_mpi, pi_mpi, iters_mpi, hist_mpi = modified_policy_iteration(mdp, k=10, target_accuracy=1e-6)
    t_mpi = time.perf_counter() - t0
    results['Modified PI (k=10)'] = {
        'V': V_mpi, 'policy': pi_mpi, 'iterations': iters_mpi,
        'time_ms': t_mpi * 1000,
        'value_error': np.max(np.abs(V_mpi - V_ref)),
        'policy_match': np.mean(pi_mpi == pi_ref),
        'history': hist_mpi
    }

    return results, mdp, V_ref, pi_ref


results, mdp, V_ref, pi_ref = run_benchmark()

print(f"{'Algorithm':<25} {'Iterations':>10} {'Time (ms)':>10} "
      f"{'||V-V*||_inf':>14} {'Policy %':>10}")
print("-" * 75)
for name, res in results.items():
    print(f"{name:<25} {res['iterations']:>10} {res['time_ms']:>10.2f} "
          f"{res['value_error']:>14.2e} {res['policy_match']*100:>9.1f}%")
```

For the 8x8 Gridworld with $\gamma = 0.95$ and $\epsilon = 10^{-6}$, value iteration typically requires 200-400 iterations, policy iteration converges in 5-8 iterations, and modified policy iteration with $k=10$ converges in 15-30 outer iterations. Policy iteration's per-iteration cost ($O(|S|^3) = O(64^3) \approx 262{,}000$ flops) is dominated by the matrix solve, while value iteration's per-iteration cost ($O(|S|^2|A|) = O(64^2 \cdot 4) \approx 16{,}000$ flops) is cheap. On this small problem, all three algorithms complete in under 50 milliseconds. The scaling story changes dramatically as $|S|$ grows, as the next section demonstrates.

### Visualization

```python
def visualize_solution(mdp: GridworldMDP, V: np.ndarray, policy: np.ndarray,
                       V_ref: np.ndarray, title: str, ax: plt.Axes) -> None:
    grid = V.reshape(mdp.rows, mdp.cols)
    im = ax.imshow(grid, cmap='RdYlGn', interpolation='nearest', vmin=V_ref.min(), vmax=V_ref.max())

    arrow_map = {0: (0, 0.25), 1: (0.25, 0), 2: (0, -0.25), 3: (-0.25, 0)}
    for s in range(mdp.n_states):
        if s in mdp._terminal:
            continue
        r, c = divmod(s, mdp.cols)
        dr, dc = arrow_map[policy[s]]
        ax.arrow(c, r, dc, dr, head_width=0.12, head_length=0.08,
                 fc='black', ec='black', alpha=0.7)

    for gs in mdp.goal_states:
        r, c = divmod(gs, mdp.cols)
        ax.plot(c, r, 'g*', markersize=12, markeredgecolor='black')
    for ps in mdp.pit_states:
        r, c = divmod(ps, mdp.cols)
        ax.plot(c, r, 'rX', markersize=12, markeredgecolor='black')

    ax.set_title(title, fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])


def plot_convergence(mdp: GridworldMDP, results: Dict, V_ref: np.ndarray) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(24, 5))

    for ax, (name, res) in zip(axes[:3], results.items()):
        visualize_solution(mdp, res['V'], res['policy'], V_ref,
                           f"{name}\n{res['iterations']} iters, {res['time_ms']:.1f}ms", ax)

    ax = axes[3]
    for name, res in results.items():
        vals = res['history'].get('values', [])
        if vals:
            errors = [np.max(np.abs(v - V_ref)) for v in vals]
            ax.semilogy(range(len(errors)), errors, label=name, linewidth=1.5)
    ax.set_xlabel('Outer Iteration')
    ax.set_ylabel(r'$\|V_k - V^*\|_\infty$')
    ax.set_title('Convergence to Optimal Value')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('mdp_convergence.png', dpi=150, bbox_inches='tight')
    plt.close()

plot_convergence(mdp, results, V_ref)
```

The convergence plot reveals the structural difference between the algorithms. Value iteration's error decreases smoothly and geometrically, a straight line on the log-scale plot with slope $\log \gamma$. Policy iteration's error drops in discrete jumps, each corresponding to a policy improvement step that can dramatically reduce the error. Modified policy iteration sits between the two, with smaller jumps at each outer iteration reflecting the partial policy evaluation.

## 3. High-Performance Optimization & Failure Modes

### Gauss-Seidel Value Iteration

Standard value iteration uses Jacobi updates: all states are updated simultaneously based on the previous iteration's values. Gauss-Seidel value iteration updates states in-place, so that when computing $V_{k+1}(s)$, the already-updated values $V_{k+1}(s')$ for $s' < s$ are used instead of $V_k(s')$. This propagates information faster through the state space and typically reduces the iteration count by a constant factor, though the contraction guarantee still holds because the Gauss-Seidel operator is also a $\gamma$-contraction.

```python
def value_iteration_gauss_seidel(mdp: GridworldMDP,
                                  target_accuracy: float = 1e-6,
                                  max_iters: int = 100_000
                                  ) -> Tuple[np.ndarray, np.ndarray, int]:
    V = np.zeros(mdp.n_states)
    gamma = mdp.gamma
    threshold = target_accuracy * (1.0 - gamma) / gamma if gamma > 0 else target_accuracy

    for it in range(max_iters):
        delta = 0.0
        for s in range(mdp.n_states):
            if s in mdp._terminal:
                continue
            v_old = V[s]
            Q_s = mdp.R_sa[s] + gamma * (mdp.P[s] @ V)
            V[s] = np.max(Q_s)
            delta = max(delta, abs(V[s] - v_old))
        if delta < threshold:
            break

    Q = mdp.R_sa + gamma * (mdp.P @ V)
    policy = np.argmax(Q, axis=1)
    return V, policy, it + 1
```

The trade-off is that Gauss-Seidel is inherently sequential over states, so it cannot be fully vectorized. For small to medium state spaces, the reduced iteration count compensates for the loss of vectorization. For large state spaces, the Jacobi variant's BLAS-accelerated matrix-vector product wins. The crossover point depends on the hardware and the problem structure, but for $|S| > 5000$, the vectorized Jacobi version is almost always faster in wall-clock time despite requiring more iterations.

### Scaling to Large State Spaces

To study scaling behavior, we construct a parametric RandomMDP where the transition kernel has controlled sparsity. This models structured environments where each state-action pair reaches only a small number of successor states, which is the common case in real applications.

```python
@dataclass
class RandomMDP:
    n_states: int = 1000
    n_actions: int = 4
    gamma: float = 0.95
    sparsity: int = 10
    seed: int = 42

    def __post_init__(self):
        rng = np.random.default_rng(self.seed)
        self._terminal: Set[int] = set()
        n_next = min(self.sparsity, self.n_states)

        self.P = np.zeros((self.n_states, self.n_actions, self.n_states))
        self.R_sa = np.zeros((self.n_states, self.n_actions))

        for s in range(self.n_states):
            for a in range(self.n_actions):
                next_states = rng.choice(self.n_states, size=n_next, replace=False)
                probs = rng.dirichlet(np.ones(n_next))
                self.P[s, a, next_states] = probs
                self.R_sa[s, a] = rng.normal(0, 0.5)

    def is_terminal(self, s: int) -> bool:
        return s in self._terminal
```

The following benchmark sweeps over state space sizes from 100 to 10,000 and records wall-clock time for each algorithm.

```python
def scaling_benchmark() -> None:
    state_sizes = [100, 500, 1000, 2000, 5000, 10000]
    timings: Dict[str, List[float]] = {'VI': [], 'PI': [], 'MPI-5': [], 'MPI-20': []}
    iteration_counts: Dict[str, List[int]] = {'VI': [], 'PI': [], 'MPI-5': [], 'MPI-20': []}

    for n in state_sizes:
        mdp = RandomMDP(n_states=n, n_actions=4, gamma=0.9, sparsity=10, seed=42)

        t0 = time.perf_counter()
        _, _, iters, _ = value_iteration(mdp, target_accuracy=1e-4, track_history=False)
        timings['VI'].append((time.perf_counter() - t0) * 1000)
        iteration_counts['VI'].append(iters)

        t0 = time.perf_counter()
        _, _, iters, _ = policy_iteration(mdp, max_iters=200, track_history=False)
        timings['PI'].append((time.perf_counter() - t0) * 1000)
        iteration_counts['PI'].append(iters)

        t0 = time.perf_counter()
        _, _, iters, _ = modified_policy_iteration(mdp, k=5, target_accuracy=1e-4, track_history=False)
        timings['MPI-5'].append((time.perf_counter() - t0) * 1000)
        iteration_counts['MPI-5'].append(iters)

        t0 = time.perf_counter()
        _, _, iters, _ = modified_policy_iteration(mdp, k=20, target_accuracy=1e-4, track_history=False)
        timings['MPI-20'].append((time.perf_counter() - t0) * 1000)
        iteration_counts['MPI-20'].append(iters)

    print(f"{'|S|':>8} {'VI (ms)':>10} {'VI iters':>8} {'PI (ms)':>10} {'PI iters':>8} "
          f"{'MPI-5 (ms)':>10} {'MPI-5 it':>8} {'MPI-20 (ms)':>11} {'MPI-20 it':>8}")
    print("-" * 95)
    for i, n in enumerate(state_sizes):
        print(f"{n:>8} {timings['VI'][i]:>10.1f} {iteration_counts['VI'][i]:>8} "
              f"{timings['PI'][i]:>10.1f} {iteration_counts['PI'][i]:>8} "
              f"{timings['MPI-5'][i]:>10.1f} {iteration_counts['MPI-5'][i]:>8} "
              f"{timings['MPI-20'][i]:>11.1f} {iteration_counts['MPI-20'][i]:>8}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for name in timings:
        ax1.loglog(state_sizes, timings[name], 'o-', label=name, linewidth=1.5, markersize=5)
    ax1.set_xlabel('Number of States |S|')
    ax1.set_ylabel('Wall-Clock Time (ms)')
    ax1.set_title('Scaling: Time vs State Space Size')
    ax1.legend()
    ax1.grid(True, alpha=0.3, which='both')

    for name in iteration_counts:
        ax2.semilogx(state_sizes, iteration_counts[name], 'o-', label=name, linewidth=1.5, markersize=5)
    ax2.set_xlabel('Number of States |S|')
    ax2.set_ylabel('Iterations to Converge')
    ax2.set_title('Iteration Count vs State Space Size')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('mdp_scaling.png', dpi=150, bbox_inches='tight')
    plt.close()

scaling_benchmark()
```

The scaling benchmark exposes the fundamental algorithmic trade-off. Policy iteration's iteration count remains nearly constant (5-10 iterations) as $|S|$ grows, because the number of policy improvements depends on the problem structure, not the state space size. But each iteration costs $O(|S|^3)$ for the matrix solve, so the wall-clock time grows cubically. At $|S| = 10{,}000$, the matrix inversion of a $10{,}000 \times 10{,}000$ system takes several seconds, while value iteration's $O(|S|^2|A|)$ backup takes milliseconds. Modified policy iteration with $k=5$ and $k=20$ interpolates between the two: the $k=5$ variant stays close to value iteration's scaling profile, while $k=20$ approaches policy iteration's iteration count at a fraction of the per-iteration cost.

### Prioritized Sweeping

When the transition kernel is sparse, most states have no effect on most other states. Standard value iteration wastes computation by applying the Bellman backup to every state uniformly, even when most values have barely changed. Prioritized sweeping addresses this by maintaining a priority queue of states ordered by their Bellman error, the magnitude of the change a backup would produce. States with large Bellman errors are updated first, and after each update, only the predecessors of the updated state are re-examined, because only their backups could be affected by the change.

```python
import heapq


def prioritized_sweeping(mdp, target_accuracy: float = 1e-6,
                         max_sweeps: int = 500_000
                         ) -> Tuple[np.ndarray, np.ndarray, int]:
    V = np.zeros(mdp.n_states)
    gamma = mdp.gamma

    predecessors: List[List[Tuple[int, float]]] = [[] for _ in range(mdp.n_states)]
    for s in range(mdp.n_states):
        for a in range(mdp.n_actions):
            for ns in range(mdp.n_states):
                if mdp.P[s, a, ns] > 0:
                    predecessors[ns].append((s, mdp.P[s, a, ns]))

    current_priority = np.zeros(mdp.n_states)
    pq: List[Tuple[float, int]] = []

    for s in range(mdp.n_states):
        if s in mdp._terminal:
            continue
        Q_s = mdp.R_sa[s] + gamma * (mdp.P[s] @ V)
        bellman_error = abs(np.max(Q_s) - V[s])
        if bellman_error > 1e-12:
            current_priority[s] = bellman_error
            heapq.heappush(pq, (-bellman_error, s))

    sweeps = 0
    while pq and sweeps < max_sweeps:
        neg_priority, s = heapq.heappop(pq)
        if -neg_priority < current_priority[s] - 1e-15:
            continue

        sweeps += 1
        Q_s = mdp.R_sa[s] + gamma * (mdp.P[s] @ V)
        V[s] = np.max(Q_s)
        current_priority[s] = 0.0

        for pred_s, _ in predecessors[s]:
            if pred_s in mdp._terminal:
                continue
            Q_pred = mdp.R_sa[pred_s] + gamma * (mdp.P[pred_s] @ V)
            bellman_error = abs(np.max(Q_pred) - V[pred_s])
            if bellman_error > target_accuracy and bellman_error > current_priority[pred_s]:
                current_priority[pred_s] = bellman_error
                heapq.heappush(pq, (-bellman_error, pred_s))

    Q = mdp.R_sa + gamma * (mdp.P @ V)
    policy = np.argmax(Q, axis=1)
    return V, policy, sweeps
```

The predecessor map is the key data structure. For each state $s'$, it stores the list of states $s$ that can reach $s'$ in one step, along with the transition probability. When $V(s')$ changes, only the states in `predecessors[s']` need to be re-evaluated. For a sparse MDP where each state reaches only $k$ successors, the average in-degree is also $k$, so each update touches only $O(k)$ predecessors instead of scanning all $|S|$ states.

The stale-entry problem is handled by tracking `current_priority[s]` for each state. When a state is popped from the heap, we check whether the stored priority matches the current priority. If it does not, the entry is stale and skipped. This avoids the overhead of a decrease-key operation, which binary heaps do not support efficiently.

Prioritized sweeping is most effective when the value function has a localized error distribution, meaning that a small number of states account for most of the Bellman error. This is common early in the iteration process when information is propagating from terminal states. As the value function converges, the error becomes uniformly small across all states, and prioritized sweeping degrades to the same cost as synchronous value iteration.

### Failure Modes and Practical Mitigations

The most common failure mode is slow convergence when $\gamma$ approaches 1. The contraction modulus is $\gamma$, so the number of iterations scales as $O(1/(1-\gamma))$. At $\gamma = 0.99$, value iteration needs roughly 20 times more iterations than at $\gamma = 0.95$ for the same accuracy. At $\gamma = 0.999$, the factor grows to 200. Policy iteration is less sensitive to $\gamma$ because it does not rely on iterative contraction for policy evaluation, but the matrix $I - \gamma P^\pi$ becomes increasingly ill-conditioned as $\gamma \to 1$, with condition number $O(1/(1-\gamma))$. This degrades the numerical stability of the linear solve. The practical mitigation is to use iterative policy evaluation with a small number of steps rather than exact matrix inversion when $\gamma > 0.99$, effectively switching to modified policy iteration.

A second failure mode arises from ties in the argmax operator. When two or more actions have nearly identical Q-values at a state, floating-point noise can cause the policy to oscillate between them across iterations. This is rarely a problem for value iteration, because the value function converges regardless of which tied action is selected. But for policy iteration, oscillating policies prevent the equality check `np.array_equal(new_policy, policy)` from triggering, and the algorithm can cycle indefinitely. The fix is to add a tolerance to the policy comparison, checking whether the value functions are close rather than the policies: `np.max(np.abs(V_new - V_old)) < tolerance`. Alternatively, use lexicographic tie-breaking with a secondary criterion such as action index.

Numerical precision issues arise when the value range is large relative to the stopping threshold. If rewards are on the order of $10^6$ and the threshold is $10^{-6}$, the 12-order-of-magnitude dynamic range exceeds float64 precision. The solution is to normalize the reward scale before solving, or to use the relative Bellman error $\|V_{k+1} - V_k\|_\infty / \|V_k\|_\infty$ as the stopping criterion instead of the absolute error.

For very large state spaces where even $O(|S|^2)$ storage is prohibitive, the transition tensor cannot be materialized as a dense array. In this regime, the function `transitions(s, a)` must be computed on demand or stored in a sparse format, and the vectorized Bellman backup `mdp.P @ V` must be replaced with a loop over states that computes each row of $P$ lazily. The algorithmic structure is unchanged, but the performance profile shifts: memory accesses dominate over computation, and cache locality becomes the primary performance factor. For MDPs derived from continuous-state problems via discretization, this is the standard operating regime, and the choice between value iteration and modified policy iteration is determined by the trade-off between iteration count and per-iteration memory bandwidth.
