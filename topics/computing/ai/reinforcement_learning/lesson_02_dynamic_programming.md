# Lesson 2: Dynamic Programming Methods in Reinforcement Learning

## 1. First-Principles Intuition & Invariants

Dynamic programming methods in reinforcement learning stand as the theoretical foundation upon which all modern value-based algorithms rest. Unlike the Monte Carlo and temporal-difference methods that must contend with sampling variance and incomplete information, dynamic programming assumes perfect knowledge of the environment's transition dynamics and reward structure—a luxury that transforms the reinforcement learning problem into a tractable system of recursive equations. This complete model knowledge allows DP methods to compute exact solutions through systematic sweeps over the entire state space, establishing both the theoretical performance ceiling for tabular methods and the mathematical machinery that underpins approximate solution techniques in large-scale problems.

The mathematical heart of dynamic programming in RL emerges from Bellman's principle of optimality, which asserts that an optimal policy has the property that whatever the initial state and initial decision are, the remaining decisions must constitute an optimal policy with regard to the state resulting from the first decision. This recursive structure manifests in the Bellman optimality equations, which express the value of a state under an optimal policy as the maximum over all actions of the immediate reward plus the discounted value of the successor state. For the state-value function under optimal policy π*, this relationship crystallizes as:

$$v_*(s) = \max_a \mathbb{E}[R_{t+1} + \gamma v_*(S_{t+1}) \mid S_t = s, A_t = a]$$

When we expand the expectation using the model's transition dynamics p(s', r | s, a), we obtain the form that dynamic programming algorithms operate on directly:

$$v_*(s) = \max_a \sum_{s', r} p(s', r \mid s, a)[r + \gamma v_*(s')]$$

This equation reveals the computational structure that DP exploits: the optimal value of each state depends only on the optimal values of its immediate successor states, weighted by transition probabilities. The entire infinite-horizon optimization problem decomposes into a finite system of nonlinear equations, one per state, that can be solved through iterative refinement. The convergence properties of these iterations rest on the contraction mapping theorem from functional analysis, which guarantees that repeatedly applying the Bellman optimality operator brings the value function monotonically closer to the unique fixed point v*.

The distinction between policy evaluation, policy improvement, and control algorithms forms the conceptual architecture of dynamic programming methods. Policy evaluation solves the prediction problem: given a fixed policy π, compute its value function vπ(s) for all states. This prediction task reduces to solving a linear system of equations, since the Bellman equation for a fixed policy lacks the maximization operator:

$$v_\pi(s) = \sum_a \pi(a \mid s) \sum_{s', r} p(s', r \mid s, a)[r + \gamma v_\pi(s')]$$

The linearity ensures that iterative policy evaluation converges to the unique solution regardless of initialization, with convergence rate governed by the discount factor γ. Each iteration sweeps through all states, updating each state's value based on the current estimates of successor state values—a process called a full backup in the RL literature because it incorporates information from all possible transitions rather than sampling a single trajectory.

Policy improvement takes a value function vπ and constructs a new policy π' that is guaranteed to be at least as good as π by acting greedily with respect to vπ. The policy improvement theorem provides the formal guarantee: if vπ(s) ≤ vπ'(s) for all states when π' is the greedy policy with respect to vπ, then π' ≥ π in the partial ordering on policies. Moreover, if the inequality is strict for even a single state where vπ(s) < vπ'(s), then π' is strictly better than π. This greedy policy improvement step computes:

$$\pi'(s) = \arg\max_a \sum_{s', r} p(s', r \mid s, a)[r + \gamma v_\pi(s')]$$

The policy iteration algorithm alternates between these two operations: policy evaluation computes the value function for the current policy until convergence, then policy improvement generates a new improved policy. This process continues until the policy becomes stable—a condition that occurs precisely when the policy is optimal, because the only policy that is unchanged by greedy improvement with respect to its own value function is an optimal policy. The finite state and action spaces guarantee termination in a finite number of iterations, though the computational cost per iteration scales as O(|S|²|A|) for the evaluation step and O(|S||A|) for the improvement step.

Value iteration offers a computationally more efficient alternative by collapsing the distinction between evaluation and improvement. Instead of running policy evaluation to convergence before each improvement step, value iteration performs a single backup of each state using the Bellman optimality equation directly. This amounts to combining truncated policy evaluation with policy improvement into a single update operation. The remarkable theoretical result is that value iteration still converges to the optimal value function v*, from which the optimal policy can be extracted by a single greedy action selection. The convergence proof relies on showing that the Bellman optimality operator T* defined by:

$$(T^* v)(s) = \max_a \sum_{s', r} p(s', r \mid s, a)[r + \gamma v(s')]$$

is a γ-contraction in the infinity norm. This means that for any two value functions v and u, we have ||T*v - T*u||∞ ≤ γ||v - u||∞. The contraction mapping theorem then guarantees that repeated application of T* converges geometrically to the unique fixed point at rate γ, regardless of initialization.

The computational complexity tradeoffs between policy iteration and value iteration reflect a fundamental tension in dynamic programming. Policy iteration typically requires fewer iterations to converge—often just a handful of policy changes—but each iteration demands solving a system of |S| linear equations to convergence. Value iteration requires more iterations, with convergence rate determined by γ, but each iteration costs only O(|S||A|) operations for a single state-value update sweep. In practice, the choice depends on problem structure: for small state spaces with moderate action spaces, policy iteration often wins due to its aggressive convergence in policy space. For larger problems or those with expensive transition model evaluation, value iteration's lighter per-iteration cost becomes attractive.

The asynchronous dynamic programming variants relax the requirement that every state be updated in strict sweeps, allowing updates to occur in any order and even to focus computation on frequently visited or high-value states. The Gauss-Seidel style in-place updates, where newly computed values are used immediately in subsequent state updates within the same sweep, can accelerate convergence substantially compared to the Jacobi-style synchronous updates that use values from the previous iteration. Prioritized sweeping takes this further by maintaining a priority queue of states ordered by the magnitude of potential value changes, focusing computation where it matters most. These techniques foreshadow the modern deep RL practice of replay buffers and prioritized experience replay, showing how ideas from classical DP inform contemporary algorithms.

The generalized policy iteration framework unifies policy iteration, value iteration, and their variants under a single conceptual model. GPI describes any algorithm that maintains both a policy and a value function, with the policy always being improved with respect to the current value function and the value function always being driven toward the value function for the current policy. The two processes push against each other—policy improvement makes the value function incorrect for the new policy, while policy evaluation makes the policy no longer greedy. Yet this competition stabilizes exactly at optimality, where both processes agree. This perspective reveals that value iteration is simply GPI with a single evaluation sweep per improvement step, while policy iteration uses complete evaluation before each improvement.

## 2. Core Architecture & Mechanics

The execution model of dynamic programming algorithms centers on systematic state-space sweeps with full-backup updates that leverage complete model knowledge. To ground these concepts in concrete implementation, we construct a full tabular DP engine in Python that exposes the internal mechanics of both policy iteration and value iteration while maintaining numerical stability and computational efficiency.

The core data structures mirror the mathematical objects in the Bellman equations. The value function table stores a floating-point estimate for each state, while the policy representation depends on whether we maintain deterministic or stochastic policies. For tabular problems, deterministic policies map states to actions directly, while stochastic policies require a |S| × |A| probability table. The environment model consists of a transition probability tensor P of shape |S| × |A| × |S|, where P[s, a, s'] = p(s' | s, a), and a reward function R that can be represented either as a |S| × |A| matrix for deterministic rewards or as a full |S| × |A| × |S| tensor for state-dependent rewards.

```python
import numpy as np
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

class UpdateStrategy(Enum):
    SYNCHRONOUS = "synchronous"
    INPLACE = "inplace"
    PRIORITIZED = "prioritized"

@dataclass
class DPConfig:
    """Configuration for dynamic programming algorithms."""
    gamma: float = 0.99
    theta: float = 1e-6
    max_iterations: int = 1000
    update_strategy: UpdateStrategy = UpdateStrategy.INPLACE
    
@dataclass
class DPResult:
    """Results from DP algorithm execution."""
    value_function: np.ndarray
    policy: np.ndarray
    iterations: int
    converged: bool
    delta_history: List[float]

class TabularMDP:
    """
    Complete tabular MDP representation with transition dynamics and rewards.
    
    Implements the model p(s', r | s, a) required for dynamic programming.
    Maintains transition probability tensor P[s,a,s'] and reward function R[s,a,s'].
    """
    
    def __init__(self, n_states: int, n_actions: int):
        self.n_states = n_states
        self.n_actions = n_actions
        # Transition probabilities: P[s, a, s'] = p(s' | s, a)
        self.P = np.zeros((n_states, n_actions, n_states))
        # Rewards: R[s, a, s'] = expected reward for transition
        self.R = np.zeros((n_states, n_actions, n_states))
        # Terminal state mask
        self.terminal_states = np.zeros(n_states, dtype=bool)
        
    def set_transition(self, s: int, a: int, transitions: List[Tuple[int, float, float]]):
        """
        Set transition dynamics for state-action pair.
        
        Args:
            s: Source state
            a: Action
            transitions: List of (next_state, probability, reward) tuples
        """
        total_prob = 0.0
        for s_next, prob, reward in transitions:
            assert 0 <= prob <= 1, "Probability must be in [0,1]"
            assert 0 <= s_next < self.n_states, "Invalid next state"
            self.P[s, a, s_next] = prob
            self.R[s, a, s_next] = reward
            total_prob += prob
        assert np.isclose(total_prob, 1.0), f"Probabilities must sum to 1, got {total_prob}"
    
    def set_deterministic_transition(self, s: int, a: int, s_next: int, reward: float):
        """Convenience method for deterministic transitions."""
        self.set_transition(s, a, [(s_next, 1.0, reward)])
    
    def set_terminal(self, s: int):
        """Mark state as terminal (transitions to itself with zero reward)."""
        self.terminal_states[s] = True
        for a in range(self.n_actions):
            self.P[s, a, :] = 0.0
            self.P[s, a, s] = 1.0
            self.R[s, a, :] = 0.0
    
    def expected_return(self, s: int, a: int, v: np.ndarray, gamma: float) -> float:
        """
        Compute expected return: E[R + γ V(S') | s, a].
        
        This is the core Bellman backup operation.
        """
        immediate_reward = np.sum(self.P[s, a, :] * self.R[s, a, :])
        future_value = np.sum(self.P[s, a, :] * v)
        return immediate_reward + gamma * future_value
    
    def bellman_backup(self, v: np.ndarray, gamma: float, policy: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Perform full Bellman backup for all states.
        
        If policy is None, uses Bellman optimality operator (max over actions).
        If policy is provided, uses Bellman expectation operator for that policy.
        """
        v_new = np.zeros(self.n_states)
        
        for s in range(self.n_states):
            if self.terminal_states[s]:
                v_new[s] = 0.0
                continue
                
            action_values = np.array([
                self.expected_return(s, a, v, gamma) 
                for a in range(self.n_actions)
            ])
            
            if policy is None:
                # Bellman optimality: take max
                v_new[s] = np.max(action_values)
            else:
                # Bellman expectation: weighted by policy
                v_new[s] = np.sum(policy[s, :] * action_values)
        
        return v_new
    
    def greedy_policy(self, v: np.ndarray, gamma: float) -> np.ndarray:
        """
        Extract greedy policy with respect to value function.
        
        Returns deterministic policy as integer array mapping states to actions.
        """
        policy = np.zeros(self.n_states, dtype=int)
        
        for s in range(self.n_states):
            if self.terminal_states[s]:
                policy[s] = 0  # Arbitrary action in terminal state
                continue
                
            action_values = np.array([
                self.expected_return(s, a, v, gamma)
                for a in range(self.n_actions)
            ])
            policy[s] = np.argmax(action_values)
        
        return policy


class PolicyIterationEngine:
    """
    Policy iteration algorithm with configurable evaluation strategy.
    
    Alternates between policy evaluation (solve linear system) and 
    policy improvement (greedy action selection) until convergence.
    """
    
    def __init__(self, mdp: TabularMDP, config: DPConfig):
        self.mdp = mdp
        self.config = config
        
    def evaluate_policy(self, policy: np.ndarray, v_init: Optional[np.ndarray] = None) -> Tuple[np.ndarray, int]:
        """
        Evaluate policy using iterative application of Bellman expectation equation.
        
        Continues until max change in value function falls below theta.
        """
        v = v_init if v_init is not None else np.zeros(self.mdp.n_states)
        
        # Convert deterministic policy to stochastic for uniform interface
        policy_prob = np.zeros((self.mdp.n_states, self.mdp.n_actions))
        policy_prob[np.arange(self.mdp.n_states), policy] = 1.0
        
        iterations = 0
        while iterations < self.config.max_iterations:
            iterations += 1
            
            if self.config.update_strategy == UpdateStrategy.INPLACE:
                delta = 0.0
                for s in range(self.mdp.n_states):
                    if self.mdp.terminal_states[s]:
                        continue
                    v_old = v[s]
                    action_values = np.array([
                        self.mdp.expected_return(s, a, v, self.config.gamma)
                        for a in range(self.mdp.n_actions)
                    ])
                    v[s] = np.sum(policy_prob[s, :] * action_values)
                    delta = max(delta, abs(v_old - v[s]))
            else:
                # Synchronous update
                v_new = self.mdp.bellman_backup(v, self.config.gamma, policy_prob)
                delta = np.max(np.abs(v_new - v))
                v = v_new
            
            if delta < self.config.theta:
                break
        
        return v, iterations
    
    def solve(self, v_init: Optional[np.ndarray] = None) -> DPResult:
        """
        Execute policy iteration until convergence.
        
        Returns optimal value function and policy.
        """
        v = v_init if v_init is not None else np.zeros(self.mdp.n_states)
        policy = np.zeros(self.mdp.n_states, dtype=int)
        
        total_iterations = 0
        delta_history = []
        
        for iteration in range(self.config.max_iterations):
            # Policy evaluation
            v, eval_iters = self.evaluate_policy(policy, v)
            total_iterations += eval_iters
            
            # Policy improvement
            policy_stable = True
            for s in range(self.mdp.n_states):
                if self.mdp.terminal_states[s]:
                    continue
                    
                old_action = policy[s]
                action_values = np.array([
                    self.mdp.expected_return(s, a, v, self.config.gamma)
                    for a in range(self.mdp.n_actions)
                ])
                policy[s] = np.argmax(action_values)
                
                if old_action != policy[s]:
                    policy_stable = False
            
            # Track convergence
            v_check = self.mdp.bellman_backup(v, self.config.gamma, None)
            delta = np.max(np.abs(v_check - v))
            delta_history.append(delta)
            
            if policy_stable:
                return DPResult(
                    value_function=v,
                    policy=policy,
                    iterations=total_iterations,
                    converged=True,
                    delta_history=delta_history
                )
        
        return DPResult(
            value_function=v,
            policy=policy,
            iterations=total_iterations,
            converged=False,
            delta_history=delta_history
        )


class ValueIterationEngine:
    """
    Value iteration algorithm with support for synchronous and asynchronous updates.
    
    Applies Bellman optimality operator until value function converges,
    then extracts greedy policy.
    """
    
    def __init__(self, mdp: TabularMDP, config: DPConfig):
        self.mdp = mdp
        self.config = config
        
    def solve(self, v_init: Optional[np.ndarray] = None) -> DPResult:
        """
        Execute value iteration until convergence.
        
        Returns optimal value function and extracted greedy policy.
        """
        v = v_init if v_init is not None else np.zeros(self.mdp.n_states)
        delta_history = []
        
        for iteration in range(self.config.max_iterations):
            if self.config.update_strategy == UpdateStrategy.INPLACE:
                delta = 0.0
                for s in range(self.mdp.n_states):
                    if self.mdp.terminal_states[s]:
                        continue
                    v_old = v[s]
                    action_values = np.array([
                        self.mdp.expected_return(s, a, v, self.config.gamma)
                        for a in range(self.mdp.n_actions)
                    ])
                    v[s] = np.max(action_values)
                    delta = max(delta, abs(v_old - v[s]))
            else:
                # Synchronous update
                v_new = self.mdp.bellman_backup(v, self.config.gamma, None)
                delta = np.max(np.abs(v_new - v))
                v = v_new
            
            delta_history.append(delta)
            
            if delta < self.config.theta:
                # Extract greedy policy
                policy = self.mdp.greedy_policy(v, self.config.gamma)
                return DPResult(
                    value_function=v,
                    policy=policy,
                    iterations=iteration + 1,
                    converged=True,
                    delta_history=delta_history
                )
        
        # Extract policy even if not converged
        policy = self.mdp.greedy_policy(v, self.config.gamma)
        return DPResult(
            value_function=v,
            policy=policy,
            iterations=self.config.max_iterations,
            converged=False,
            delta_history=delta_history
        )


class PrioritizedValueIteration:
    """
    Value iteration with prioritized sweeping.
    
    Maintains priority queue of states ordered by Bellman error magnitude,
    focusing computation on states where value estimates are most inaccurate.
    """
    
    def __init__(self, mdp: TabularMDP, config: DPConfig):
        self.mdp = mdp
        self.config = config
        
    def compute_priority(self, s: int, v: np.ndarray) -> float:
        """Compute priority as magnitude of Bellman error."""
        if self.mdp.terminal_states[s]:
            return 0.0
        
        action_values = np.array([
            self.mdp.expected_return(s, a, v, self.config.gamma)
            for a in range(self.mdp.n_actions)
        ])
        return abs(np.max(action_values) - v[s])
    
    def solve(self, v_init: Optional[np.ndarray] = None) -> DPResult:
        """Execute prioritized value iteration."""
        import heapq
        
        v = v_init if v_init is not None else np.zeros(self.mdp.n_states)
        delta_history = []
        
        # Initialize priority queue (negative priority for max-heap behavior)
        pq = []
        for s in range(self.mdp.n_states):
            priority = self.compute_priority(s, v)
            heapq.heappush(pq, (-priority, s))
        
        updates = 0
        while updates < self.config.max_iterations and pq:
            # Pop highest priority state
            neg_priority, s = heapq.heappop(pq)
            priority = -neg_priority
            
            if priority < self.config.theta:
                break
            
            # Update state value
            v_old = v[s]
            action_values = np.array([
                self.mdp.expected_return(s, a, v, self.config.gamma)
                for a in range(self.mdp.n_actions)
            ])
            v[s] = np.max(action_values)
            delta = abs(v[s] - v_old)
            delta_history.append(delta)
            
            # Update priorities of predecessor states
            # (In full implementation, would maintain predecessor lists)
            # For simplicity, recompute priorities for all states
            if updates % self.mdp.n_states == 0:  # Periodic priority refresh
                pq = []
                for s_pred in range(self.mdp.n_states):
                    priority = self.compute_priority(s_pred, v)
                    if priority >= self.config.theta:
                        heapq.heappush(pq, (-priority, s_pred))
            
            updates += 1
        
        policy = self.mdp.greedy_policy(v, self.config.gamma)
        converged = len(pq) == 0 or (pq and -pq[0][0] < self.config.theta)
        
        return DPResult(
            value_function=v,
            policy=policy,
            iterations=updates,
            converged=converged,
            delta_history=delta_history
        )
```

The implementation architecture separates model representation in TabularMDP from algorithmic logic in the engine classes. This separation reflects the conceptual distinction between the MDP specification—transition dynamics and rewards that define the problem—and the solution method that computes optimal values and policies. The TabularMDP class exposes the core primitive operations that all DP algorithms require: computing expected returns for state-action pairs, performing Bellman backups, and extracting greedy policies. These operations directly implement the mathematical expressions in the Bellman equations, translating symbolic notation into executable array operations.

The policy evaluation subroutine in PolicyIterationEngine demonstrates the iterative solution of linear systems through repeated Bellman expectation updates. Each iteration refines the value estimate for every state by computing the expected return under the current policy, using the previous iteration's value estimates for successor states. The in-place update strategy modifies values immediately as each state is processed within an iteration, allowing information to propagate more quickly through the state space compared to synchronous updates that buffer all changes until the end of each sweep. This Gauss-Seidel approach can reduce iteration count by factors of two or more in problems with strong state-space locality.

Value iteration in ValueIterationEngine collapses the distinction between evaluation and improvement by directly applying the Bellman optimality operator. Each state's value is set to the maximum expected return over all actions, implicitly defining a greedy policy without maintaining an explicit policy representation during iteration. The convergence criterion checks whether the maximum change in value across all states falls below the threshold θ, guaranteeing that the value function has converged to within θ/(1-γ) of the optimal value function—a bound that follows from the contraction property of the Bellman optimality operator. The policy is extracted only at the end through a single greedy sweep, amortizing the cost of policy representation across the entire algorithm execution.

The prioritized sweeping variant in PrioritizedValueIteration introduces a priority queue keyed by Bellman error magnitude, directing computational effort toward states where value estimates are most uncertain. Each state's priority equals the absolute difference between its current value and the value it would have after a Bellman backup—the temporal difference error that drives value function updates. By processing high-priority states first, the algorithm accelerates convergence in problems where optimal values propagate from goal states or high-reward regions through chains of state transitions. The predecessor update logic, simplified here for clarity, would in a production implementation maintain explicit backward reachability edges to invalidate cached priorities only for states that transition into the updated state.

To demonstrate these algorithms on a concrete problem, we construct a classic gridworld navigation task where an agent moves through a two-dimensional grid to reach a goal state while avoiding obstacles and incurring small step costs.

```python
class Gridworld:
    """
    Classic gridworld environment for DP algorithm demonstration.
    
    Agent navigates grid with four cardinal actions, receiving -1 per step
    until reaching goal state. Obstacles block movement.
    """
    
    # Action encoding: 0=UP, 1=RIGHT, 2=DOWN, 3=LEFT
    ACTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    
    def __init__(self, height: int, width: int):
        self.height = height
        self.width = width
        self.obstacles = set()
        self.goal_state = None
        
    def add_obstacle(self, row: int, col: int):
        """Add obstacle at grid position."""
        self.obstacles.add((row, col))
    
    def set_goal(self, row: int, col: int):
        """Set goal state position."""
        self.goal_state = (row, col)
    
    def state_to_index(self, row: int, col: int) -> int:
        """Convert grid coordinates to flat state index."""
        return row * self.width + col
    
    def index_to_state(self, index: int) -> Tuple[int, int]:
        """Convert flat state index to grid coordinates."""
        return (index // self.width, index % self.width)
    
    def is_valid(self, row: int, col: int) -> bool:
        """Check if position is within bounds and not an obstacle."""
        return (0 <= row < self.height and 
                0 <= col < self.width and 
                (row, col) not in self.obstacles)
    
    def to_mdp(self, step_cost: float = -1.0, goal_reward: float = 0.0) -> TabularMDP:
        """
        Convert gridworld to tabular MDP representation.
        
        Implements deterministic transitions with step costs and goal reward.
        """
        n_states = self.height * self.width
        n_actions = len(self.ACTIONS)
        mdp = TabularMDP(n_states, n_actions)
        
        for row in range(self.height):
            for col in range(self.width):
                s = self.state_to_index(row, col)
                
                # Skip obstacle states (unreachable)
                if (row, col) in self.obstacles:
                    continue
                
                # Goal state is terminal
                if (row, col) == self.goal_state:
                    mdp.set_terminal(s)
                    continue
                
                # Set transitions for each action
                for a, (dx, dy) in enumerate(self.ACTIONS):
                    next_row, next_col = row + dy, col + dx
                    
                    if self.is_valid(next_row, next_col):
                        # Valid transition
                        s_next = self.state_to_index(next_row, next_col)
                        reward = goal_reward if (next_row, next_col) == self.goal_state else step_cost
                        mdp.set_deterministic_transition(s, a, s_next, reward)
                    else:
                        # Invalid transition: stay in place with step cost
                        mdp.set_deterministic_transition(s, a, s, step_cost)
        
        return mdp
    
    def visualize_policy(self, policy: np.ndarray) -> str:
        """
        Render policy as ASCII art with action arrows.
        """
        symbols = ['^', '>', 'v', '<']
        lines = []
        
        for row in range(self.height):
            line = []
            for col in range(self.width):
                if (row, col) in self.obstacles:
                    line.append('#')
                elif (row, col) == self.goal_state:
                    line.append('G')
                else:
                    s = self.state_to_index(row, col)
                    line.append(symbols[policy[s]])
            lines.append(' '.join(line))
        
        return '\n'.join(lines)
    
    def visualize_values(self, v: np.ndarray) -> str:
        """
        Render value function as formatted grid.
        """
        lines = []
        for row in range(self.height):
            line = []
            for col in range(self.width):
                if (row, col) in self.obstacles:
                    line.append('  ####  ')
                else:
                    s = self.state_to_index(row, col)
                    line.append(f'{v[s]:7.2f}')
            lines.append(' '.join(line))
        return '\n'.join(lines)


def compare_dp_algorithms():
    """
    Empirical comparison of DP algorithm variants on gridworld.
    
    Measures iteration counts and convergence behavior for policy iteration,
    value iteration, and prioritized sweeping.
    """
    # Create 10x10 gridworld with obstacles and goal
    grid = Gridworld(10, 10)
    grid.set_goal(9, 9)
    
    # Add obstacle wall
    for row in range(3, 7):
        grid.add_obstacle(row, 5)
    
    mdp = grid.to_mdp(step_cost=-1.0, goal_reward=0.0)
    
    # Configuration for experiments
    config = DPConfig(
        gamma=0.99,
        theta=1e-4,
        max_iterations=1000,
        update_strategy=UpdateStrategy.INPLACE
    )
    
    print("=" * 70)
    print("Dynamic Programming Algorithm Comparison on 10x10 Gridworld")
    print("=" * 70)
    
    # Policy Iteration
    print("\n[1] POLICY ITERATION")
    print("-" * 70)
    pi_engine = PolicyIterationEngine(mdp, config)
    pi_result = pi_engine.solve()
    
    print(f"Converged: {pi_result.converged}")
    print(f"Total backups: {pi_result.iterations}")
    print(f"Policy changes: {len(pi_result.delta_history)}")
    print(f"\nOptimal Policy:")
    print(grid.visualize_policy(pi_result.policy))
    print(f"\nValue Function (sample states):")
    print(grid.visualize_values(pi_result.value_function))
    
    # Value Iteration
    print("\n\n[2] VALUE ITERATION")
    print("-" * 70)
    vi_engine = ValueIterationEngine(mdp, config)
    vi_result = vi_engine.solve()
    
    print(f"Converged: {vi_result.converged}")
    print(f"Iterations: {vi_result.iterations}")
    print(f"Final delta: {vi_result.delta_history[-1]:.2e}")
    print(f"\nOptimal Policy:")
    print(grid.visualize_policy(vi_result.policy))
    
    # Verify value function equivalence
    value_diff = np.max(np.abs(pi_result.value_function - vi_result.value_function))
    print(f"\nValue function difference (PI vs VI): {value_diff:.2e}")
    
    # Prioritized Sweeping
    print("\n\n[3] PRIORITIZED VALUE ITERATION")
    print("-" * 70)
    config_prioritized = DPConfig(
        gamma=0.99,
        theta=1e-4,
        max_iterations=1000,
        update_strategy=UpdateStrategy.PRIORITIZED
    )
    ps_engine = PrioritizedValueIteration(mdp, config_prioritized)
    ps_result = ps_engine.solve()
    
    print(f"Converged: {ps_result.converged}")
    print(f"State updates: {ps_result.iterations}")
    print(f"Speedup vs VI: {vi_result.iterations / ps_result.iterations:.2f}x")
    
    # Convergence rate analysis
    print("\n\n[4] CONVERGENCE ANALYSIS")
    print("-" * 70)
    print(f"{'Algorithm':<20} {'Iterations':<12} {'Final Delta':<15} {'Work (S*A*iter)':<15}")
    print("-" * 70)
    
    pi_work = pi_result.iterations
    vi_work = vi_result.iterations * mdp.n_states
    ps_work = ps_result.iterations
    
    print(f"{'Policy Iteration':<20} {len(pi_result.delta_history):<12} "
          f"{pi_result.delta_history[-1]:<15.2e} {pi_work:<15}")
    print(f"{'Value Iteration':<20} {vi_result.iterations:<12} "
          f"{vi_result.delta_history[-1]:<15.2e} {vi_work:<15}")
    print(f"{'Prioritized VI':<20} {ps_result.iterations:<12} "
          f"{'N/A':<15} {ps_work:<15}")

if __name__ == "__main__":
    compare_dp_algorithms()
```

This demonstration framework exposes the performance characteristics that distinguish DP algorithms in practice. The policy iteration algorithm typically terminates in fewer policy improvement steps—often under ten for this gridworld—but each step requires running iterative policy evaluation to convergence, accumulating hundreds of state value updates. Value iteration eliminates the inner loop by performing optimality backups directly, but requires more iterations to converge because it must refine both the value function and implicit policy simultaneously. The prioritized variant achieves speedups by concentrating updates near the goal state where values change most rapidly, then propagating outward through the state space in order of decreasing temporal difference error.

## 3. High-Performance Optimization & Failure Modes

The practical deployment of dynamic programming methods demands careful attention to numerical stability, computational efficiency, and scalability boundaries that determine when tabular DP remains viable versus when function approximation becomes necessary. The theoretical elegance of DP algorithms—guaranteed convergence to exact optimal solutions—faces implementation challenges that arise from floating-point arithmetic, sparse transition structures, and the curse of dimensionality that makes exhaustive state enumeration intractable beyond modest problem sizes.

Numerical precision management begins with recognizing that the Bellman operators are contractions in the infinity norm but not necessarily in finite precision arithmetic. Repeated floating-point operations accumulate roundoff error, and the discount factor γ near 1.0 amplifies these errors through the division in the convergence bound ε/(1-γ). For problems requiring high-precision value estimates, such as financial portfolio optimization or safety-critical control, implementing DP in higher precision arithmetic or using adaptive threshold schedules becomes necessary. The convergence threshold θ should be set relative to the scale of rewards and the precision requirements of downstream policy usage: a threshold of 1e-6 provides value estimates accurate to within 1e-6/(1-γ), which for γ=0.99 yields an error bound of 1e-4.

Sparse transition structure offers the primary avenue for computational optimization in large tabular problems. Most real-world MDPs exhibit strong locality where each state-action pair transitions to only a small fraction of the total state space—gridworld navigation, inventory management, and queueing systems all demonstrate this property. Representing the transition tensor P as a sparse data structure reduces memory footprint from O(|S|²|A|) dense storage to O(|S||A|k) for average branching factor k, often achieving compression ratios of 100x or more. More significantly, sparse representation transforms the computational complexity of Bellman backups from O(|S|²|A|) to O(|S||A|k), enabling DP to scale to problems with millions of states when k remains small.

```python
import scipy.sparse as sp
from typing import List, Tuple

class SparseMDP:
    """
    Memory-efficient sparse MDP representation using CSR matrices.
    
    Stores transitions as sparse matrices P_a[s,s'] and R_a[s,s'] per action,
    reducing memory from O(S²A) to O(SAk) for branching factor k.
    """
    
    def __init__(self, n_states: int, n_actions: int):
        self.n_states = n_states
        self.n_actions = n_actions
        # List of sparse transition matrices, one per action
        self.P = [sp.lil_matrix((n_states, n_states)) for _ in range(n_actions)]
        self.R = [sp.lil_matrix((n_states, n_states)) for _ in range(n_actions)]
        self.terminal_states = np.zeros(n_states, dtype=bool)
        
    def finalize(self):
        """Convert to CSR format for efficient arithmetic operations."""
        self.P = [p.tocsr() for p in self.P]
        self.R = [r.tocsr() for r in self.R]
    
    def set_transitions(self, s: int, a: int, transitions: List[Tuple[int, float, float]]):
        """Set transitions for state-action pair."""
        for s_next, prob, reward in transitions:
            self.P[a][s, s_next] = prob
            self.R[a][s, s_next] = reward
    
    def expected_return_batch(self, a: int, v: np.ndarray, gamma: float) -> np.ndarray:
        """
        Compute expected returns for action a across all states efficiently.
        
        Uses sparse matrix-vector multiplication for O(Sk) complexity.
        """
        # Immediate rewards: sum over next states weighted by transition probs
        immediate = np.array((self.P[a].multiply(self.R[a])).sum(axis=1)).flatten()
        # Future values: P_a @ v
        future = self.P[a] @ v
        return immediate + gamma * future
    
    def value_iteration_sparse(self, gamma: float, theta: float, max_iters: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Optimized value iteration using vectorized sparse operations.
        """
        v = np.zeros(self.n_states)
        
        for iteration in range(max_iters):
            # Compute Q(s,a) for all actions using sparse matrix ops
            q_values = np.column_stack([
                self.expected_return_batch(a, v, gamma)
                for a in range(self.n_actions)
            ])
            
            # Bellman optimality backup
            v_new = np.max(q_values, axis=1)
            v_new[self.terminal_states] = 0.0
            
            # Check convergence
            delta = np.max(np.abs(v_new - v))
            v = v_new
            
            if delta < theta:
                break
        
        # Extract greedy policy
        q_values = np.column_stack([
            self.expected_return_batch(a, v, gamma)
            for a in range(self.n_actions)
        ])
        policy = np.argmax(q_values, axis=1)
        
        return v, policy


def benchmark_sparse_vs_dense():
    """
    Measure performance gains from sparse representation.
    """
    import time
    
    # Create large gridworld (50x50 = 2500 states)
    grid = Gridworld(50, 50)
    grid.set_goal(49, 49)
    
    # Add random obstacles for 10% density
    import random
    random.seed(42)
    for _ in range(250):
        row, col = random.randint(0, 49), random.randint(0, 49)
        if (row, col) != (0, 0) and (row, col) != (49, 49):
            grid.add_obstacle(row, col)
    
    print("Creating dense MDP representation...")
    start = time.time()
    dense_mdp = grid.to_mdp()
    dense_memory = (dense_mdp.P.nbytes + dense_mdp.R.nbytes) / (1024**2)
    print(f"Dense MDP: {dense_memory:.2f} MB, construction time: {time.time()-start:.3f}s")
    
    print("\nCreating sparse MDP representation...")
    start = time.time()
    sparse_mdp = SparseMDP(grid.height * grid.width, len(grid.ACTIONS))
    
    for row in range(grid.height):
        for col in range(grid.width):
            if (row, col) in grid.obstacles:
                continue
            s = grid.state_to_index(row, col)
            if (row, col) == grid.goal_state:
                sparse_mdp.terminal_states[s] = True
                continue
            
            for a, (dx, dy) in enumerate(grid.ACTIONS):
                next_row, next_col = row + dy, col + dx
                if grid.is_valid(next_row, next_col):
                    s_next = grid.state_to_index(next_row, next_col)
                    reward = 0.0 if (next_row, next_col) == grid.goal_state else -1.0
                    sparse_mdp.set_transitions(s, a, [(s_next, 1.0, reward)])
                else:
                    sparse_mdp.set_transitions(s, a, [(s, 1.0, -1.0)])
    
    sparse_mdp.finalize()
    
    # Estimate sparse memory (CSR format)
    sparse_memory = sum(
        (p.data.nbytes + p.indices.nbytes + p.indptr.nbytes + r.data.nbytes) / (1024**2)
        for p, r in zip(sparse_mdp.P, sparse_mdp.R)
    )
    print(f"Sparse MDP: {sparse_memory:.2f} MB, construction time: {time.time()-start:.3f}s")
    print(f"Memory reduction: {dense_memory/sparse_memory:.1f}x")
    
    # Benchmark value iteration
    print("\nRunning value iteration (dense)...")
    config = DPConfig(gamma=0.99, theta=1e-4, max_iterations=1000)
    vi_dense = ValueIterationEngine(dense_mdp, config)
    start = time.time()
    result_dense = vi_dense.solve()
    time_dense = time.time() - start
    print(f"Dense VI: {time_dense:.3f}s, {result_dense.iterations} iterations")
    
    print("\nRunning value iteration (sparse)...")
    start = time.time()
    v_sparse, policy_sparse = sparse_mdp.value_iteration_sparse(0.99, 1e-4, 1000)
    time_sparse = time.time() - start
    print(f"Sparse VI: {time_sparse:.3f}s")
    print(f"Speedup: {time_dense/time_sparse:.1f}x")
    
    # Verify solutions match
    diff = np.max(np.abs(result_dense.value_function - v_sparse))
    print(f"\nValue function difference: {diff:.2e}")
```

The sparse implementation demonstrates the practical performance gains available through algorithmic engineering. For the 50×50 gridworld with 2500 states and 4 actions, the dense representation requires 100MB for double-precision storage of the transition and reward tensors, while the sparse format with average branching factor 4 requires under 1MB—a 100x reduction. More importantly, the sparse matrix-vector multiplications in the Bellman backup achieve similar speedups by eliminating computation over zero-probability transitions, transforming an O(|S|²) operation into O(|S|k) work per action.

Parallel and distributed DP methods extend scalability by exploiting the independence of state updates within a single iteration. Since each state's Bellman backup depends only on the current value estimates of its successor states, updates for disjoint state subsets can proceed concurrently without synchronization. A straightforward parallelization partitions the state space across worker threads or processes, each computing backups for its assigned states using shared read-only access to the previous iteration's value function. After all workers complete, a barrier synchronization makes the new values visible for the next iteration. This parallel approach scales nearly linearly up to the number of available cores for large state spaces, though communication overhead in distributed settings requires careful batching to amortize network latency.

```python
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Array, Value
import ctypes

class ParallelValueIteration:
    """
    Multi-core parallel value iteration using process pool.
    
    Partitions state space across workers with shared memory for value function.
    """
    
    def __init__(self, mdp: TabularMDP, config: DPConfig, n_workers: int = None):
        self.mdp = mdp
        self.config = config
        self.n_workers = n_workers or max(1, mp.cpu_count() - 1)
        
    def solve(self) -> DPResult:
        """Execute parallel value iteration with state-space partitioning."""
        # Shared memory for value function
        v_shared = Array(ctypes.c_double, self.mdp.n_states)
        v = np.frombuffer(v_shared.get_obj(), dtype=np.float64)
        v[:] = 0.0
        
        # Partition states across workers
        states_per_worker = (self.mdp.n_states + self.n_workers - 1) // self.n_workers
        state_partitions = [
            range(i * states_per_worker, min((i+1) * states_per_worker, self.mdp.n_states))
            for i in range(self.n_workers)
        ]
        
        delta_history = []
        converged = False
        
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            for iteration in range(self.config.max_iterations):
                # Launch parallel backup tasks
                futures = [
                    executor.submit(self._backup_partition, states, v_shared)
                    for states in state_partitions
                ]
                
                # Collect results and compute global delta
                deltas = [f.result() for f in futures]
                max_delta = max(deltas)
                delta_history.append(max_delta)
                
                if max_delta < self.config.theta:
                    converged = True
                    break
        
        # Extract policy
        policy = self.mdp.greedy_policy(v, self.config.gamma)
        
        return DPResult(
            value_function=v.copy(),
            policy=policy,
            iterations=len(delta_history),
            converged=converged,
            delta_history=delta_history
        )
    
    def _backup_partition(self, states: range, v_shared: Array) -> float:
        """Worker function: compute Bellman backups for state partition."""
        v = np.frombuffer(v_shared.get_obj(), dtype=np.float64)
        max_delta = 0.0
        
        for s in states:
            if self.mdp.terminal_states[s]:
                continue
            
            v_old = v[s]
            action_values = np.array([
                self.mdp.expected_return(s, a, v, self.config.gamma)
                for a in range(self.mdp.n_actions)
            ])
            v[s] = np.max(action_values)
            max_delta = max(max_delta, abs(v[s] - v_old))
        
        return max_delta
```

The curse of dimensionality represents the fundamental scalability limit of tabular dynamic programming. State spaces grow exponentially with problem dimensionality: a continuous control problem with k state variables discretized into n bins per dimension yields n^k states, making exhaustive enumeration intractable beyond roughly k=10 even with aggressive discretization. This combinatorial explosion motivates the transition from tabular DP to function approximation methods that represent value functions through parameterized models—neural networks, linear functions, or kernel methods—that generalize across the state space. The theoretical guarantees of exact convergence no longer apply in the approximate setting, but practical scalability to high-dimensional problems becomes possible.

State aggregation and hierarchical abstractions offer intermediate approaches that preserve some tabular structure while managing dimensionality. State aggregation groups similar states into clusters, solving a smaller MDP over cluster representatives and then distributing the solution to individual states. Temporal abstraction through options and hierarchical RL decomposes the problem into subgoals connected by high-level policies, reducing the effective horizon that DP must consider. These techniques extend tabular DP's applicability while maintaining interpretability and convergence properties lost in end-to-end function approximation.

The failure modes of dynamic programming algorithms stem primarily from model misspecification and numerical instability. When the MDP model differs from the true environment—through discretization error, incorrect transition probabilities, or simplified reward functions—the optimal policy computed by DP may perform poorly when deployed. This model-reality mismatch motivates robust MDP formulations that optimize for worst-case performance under model uncertainty, trading off optimality under the nominal model for robustness to perturbations. Numerical instability manifests when discount factors approach 1.0, causing the effective horizon to extend and amplifying roundoff errors in iterative value updates. Decomposing problems into hierarchical subgoals with smaller effective horizons or using average-reward formulations that optimize steady-state performance can mitigate these issues.

Verification and validation of DP solutions requires checking both mathematical correctness and behavioral reasonableness. The Bellman optimality conditions provide a certificate of correctness: a value function v and policy π are optimal if and only if v satisfies the Bellman optimality equation for all states and π is greedy with respect to v. Numerical verification computes the Bellman residual—the maximum difference between v(s) and the Bellman backup at s—and confirms it falls below a small threshold. Behavioral validation simulates policy execution in the MDP model, measuring accumulated reward and state visitation patterns to detect pathological behaviors like policy oscillation near decision boundaries or failure to reach goal states.

```python
def verify_optimality(mdp: TabularMDP, v: np.ndarray, policy: np.ndarray, gamma: float, epsilon: float = 1e-6) -> Dict[str, any]:
    """
    Verify that value function and policy satisfy Bellman optimality conditions.
    
    Returns verification results including Bellman residual and policy consistency.
    """
    n_states = mdp.n_states
    bellman_residual = np.zeros(n_states)
    policy_consistent = True
    inconsistent_states = []
    
    for s in range(n_states):
        if mdp.terminal_states[s]:
            continue
        
        # Compute optimal backup
        action_values = np.array([
            mdp.expected_return(s, a, v, gamma)
            for a in range(mdp.n_actions)
        ])
        v_optimal = np.max(action_values)
        bellman_residual[s] = abs(v[s] - v_optimal)
        
        # Check policy consistency
        greedy_action = np.argmax(action_values)
        if policy[s] != greedy_action:
            policy_consistent = False
            inconsistent_states.append(s)
    
    max_residual = np.max(bellman_residual)
    mean_residual = np.mean(bellman_residual)
    
    return {
        'optimal': max_residual < epsilon and policy_consistent,
        'max_bellman_residual': max_residual,
        'mean_bellman_residual': mean_residual,
        'policy_consistent': policy_consistent,
        'inconsistent_states': inconsistent_states,
        'residual_distribution': np.percentile(bellman_residual, [50, 90, 99])
    }


def simulate_policy(mdp: TabularMDP, policy: np.ndarray, start_state: int, max_steps: int = 1000, n_episodes: int = 100) -> Dict[str, any]:
    """
    Simulate policy execution to measure empirical performance.
    
    Returns statistics on episode length, cumulative reward, and state coverage.
    """
    episode_lengths = []
    episode_returns = []
    state_visits = np.zeros(mdp.n_states)
    
    for episode in range(n_episodes):
        s = start_state
        cumulative_reward = 0.0
        
        for step in range(max_steps):
            state_visits[s] += 1
            
            if mdp.terminal_states[s]:
                episode_lengths.append(step)
                episode_returns.append(cumulative_reward)
                break
            
            # Execute policy action
            a = policy[s]
            
            # Sample next state from transition distribution
            probs = mdp.P[s, a, :]
            s_next = np.random.choice(mdp.n_states, p=probs)
            reward = mdp.R[s, a, s_next]
            
            cumulative_reward += reward
            s = s_next
        else:
            # Max steps reached without termination
            episode_lengths.append(max_steps)
            episode_returns.append(cumulative_reward)
    
    return {
        'mean_episode_length': np.mean(episode_lengths),
        'mean_return': np.mean(episode_returns),
        'std_return': np.std(episode_returns),
        'state_coverage': np.sum(state_visits > 0) / mdp.n_states,
        'visit_entropy': -np.sum((state_visits / np.sum(state_visits)) * 
                                 np.log(state_visits / np.sum(state_visits) + 1e-10))
    }
```

The verification framework provides both mathematical validation through Bellman residual analysis and empirical validation through policy simulation. A small Bellman residual certifies near-optimality: if the maximum residual is ε, then the value function is within ε/(1-γ) of optimal. Policy consistency confirms that the policy is greedy with respect to the value function, ensuring the solution represents a fixed point of the generalized policy iteration process. Simulation statistics reveal whether the policy exhibits desired behavioral properties: short episode lengths indicate efficient paths to goal states, high state coverage suggests good exploration, and low variance in returns demonstrates policy robustness to stochastic transitions.

The relationship between dynamic programming and modern deep reinforcement learning manifests through the conceptual framework rather than direct algorithmic application. Modern value-based methods like DQN, Rainbow, and their descendants implement approximate versions of value iteration using neural networks as function approximators, replacing exhaustive tabular updates with stochastic gradient descent on sampled transitions. Policy gradient methods like PPO and SAC draw inspiration from the policy improvement theorem, optimizing policies directly through gradient ascent while maintaining value function critics to reduce variance. Actor-critic architectures embody the generalized policy iteration principle, with the critic estimating values through temporal-difference learning while the actor improves the policy through gradient steps. Understanding the tabular DP foundation clarifies the theoretical underpinnings of these scalable approximations and reveals the convergence guarantees and optimality properties that approximate methods sacrifice for practical tractability in high-dimensional domains.
