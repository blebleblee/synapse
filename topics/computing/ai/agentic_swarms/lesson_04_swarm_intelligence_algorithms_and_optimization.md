# Lesson 4: Swarm Intelligence Algorithms, Optimization Strategies

## 1. First-Principles Intuition & Invariants

The central paradox of swarm intelligence is that it derives sophisticated collective behavior from agents that are individually incapable of sophistication. A single ant has no map of its colony's foraging territory. A single starling does not know the shape of the murmuration it is part of. A single honeybee scout cannot model the full fitness landscape of potential nesting sites. Yet colonies find near-optimal foraging routes, murmurations execute coordinated evasive maneuvers that outpace predators, and swarms select nesting sites that satisfy dozens of competing environmental constraints with remarkable accuracy. The mathematical structure underlying all of these phenomena is the same: distributed stochastic search over a high-dimensional fitness landscape, where each agent samples a local region of that landscape and broadcasts its measurements through a shared stigmergic or social medium. The swarm's intelligence is not located in any agent; it resides in the statistical ensemble of their interactions.

For AI practitioners building agentic systems, this is not merely a biological curiosity. It is a blueprint for a class of optimization algorithms that exhibit properties that gradient-based methods cannot easily replicate. Classical gradient descent requires the fitness landscape to be differentiable, or at least approximately so. It follows the local geometry of the objective surface, which means it is structurally vulnerable to premature convergence at local minima in non-convex landscapes. Swarm algorithms make no such assumption. They maintain a population of candidate solutions distributed across the search space and use inter-agent communication to bias future sampling toward promising regions, all without computing a gradient. This makes them naturally applicable to discrete combinatorial problems, mixed-integer programs, neural architecture search, hyperparameter optimization, and multi-objective Pareto front approximation—domains where the fitness landscape is rugged, multimodal, and non-differentiable by construction.

The invariant at the heart of every swarm algorithm is the **exploration-exploitation tradeoff**, and understanding it mechanically is essential before examining any specific algorithm. Exploration means sampling regions of the search space that are distant from the current population's distribution—it has high expected information gain and high variance in reward. Exploitation means sampling densely around regions already known to be high-fitness—it has lower expected information gain but lower variance. A swarm that is purely exploratory performs a random walk and never converges. A swarm that is purely exploitative collapses onto a local optimum and stagnates. Every design choice in every swarm algorithm—inertia weight schedules in PSO, pheromone evaporation rates in ACO, the waggle dance probability in bee algorithms—is a mechanism for navigating this tradeoff across time. The swarm typically begins exploration-heavy to survey the landscape and progressively shifts toward exploitation as the population's belief about the global optimum concentrates. Getting this schedule wrong is the principal source of failure in deployed swarm systems.

The fitness landscape itself deserves rigorous treatment because practitioners frequently apply optimization algorithms without modeling the topology of the space they are searching. A fitness landscape is a mapping $f: \mathbb{R}^d \rightarrow \mathbb{R}$ (or its discrete analog) where $d$ is the number of decision variables and $f$ is the objective function to be maximized or minimized. The landscape's difficulty is characterized by its **modality** (how many local optima it has), its **epistasis** (how strongly variables interact, which determines how separable the objective is into independent subproblems), and its **deceptiveness** (whether the gradient of a local search leads away from the global optimum). The NK landscape model, introduced by Stuart Kauffman, provides a formal parametric framework: for $N$ binary variables each interacting with $K$ others, the landscape transitions from smooth and unimodal at $K=0$ to fully random and maximally rugged at $K=N-1$. Swarm algorithms are most advantageous when epistasis is moderate to high and deceptiveness is significant—exactly the conditions that defeat quasi-Newton methods and simulated annealing.

A second invariant shared by all production swarm systems is **convergence in probability rather than certainty**. No swarm algorithm, in general, provides deterministic convergence to the global optimum in finite time. What can be proven is convergence in probability: given sufficient population size, well-tuned parameters, and adequate iterations, the probability that the swarm has found the global optimum approaches one asymptotically. This is a weaker guarantee than what practitioners accustomed to convex optimization expect, and it has direct engineering consequences. Swarm-based optimizers must be run with multiple independent restarts, their results must be treated as probabilistic rather than definitive, and production deployments must include mechanisms for detecting stagnation and reinitializing sub-populations. Ignoring these requirements produces systems that appear to work in development but fail silently in production when the fitness landscape changes.

---

## 2. Core Architecture & Mechanics

### Particle Swarm Optimization

Particle Swarm Optimization, introduced by Kennedy and Eberhart in 1995, is the swarm algorithm most naturally mapped onto continuous parameter optimization, which makes it directly relevant to hyperparameter tuning, neural architecture search, and policy optimization in reinforcement learning. Each particle $i$ maintains three state vectors: its current position $\mathbf{x}_i \in \mathbb{R}^d$, its current velocity $\mathbf{v}_i \in \mathbb{R}^d$, and its personal best position $\mathbf{p}_i \in \mathbb{R}^d$—the highest-fitness location it has individually visited. The swarm additionally maintains a global best position $\mathbf{g} \in \mathbb{R}^d$ across all particles in the population (or, in topology-restricted variants, a neighborhood best $\mathbf{l}_i$ derived from a local communication graph).

The velocity update rule is the mechanical core of PSO:

$$\mathbf{v}_i^{t+1} = \omega \mathbf{v}_i^t + c_1 r_1 (\mathbf{p}_i - \mathbf{x}_i^t) + c_2 r_2 (\mathbf{g} - \mathbf{x}_i^t)$$

$$\mathbf{x}_i^{t+1} = \mathbf{x}_i^t + \mathbf{v}_i^{t+1}$$

The three terms encode the three behavioral forces acting on each particle. The inertia term $\omega \mathbf{v}_i^t$ carries the particle's momentum, preserving its current direction of travel and smoothing oscillations. The cognitive term $c_1 r_1 (\mathbf{p}_i - \mathbf{x}_i^t)$ pulls the particle back toward its own best-known position, encoding individual memory. The social term $c_2 r_2 (\mathbf{g} - \mathbf{x}_i^t)$ pulls the particle toward the swarm's best-known position, encoding collective social learning. The scalars $r_1, r_2 \sim \text{Uniform}(0,1)$ are resampled each iteration to introduce stochasticity; $c_1$ and $c_2$ are acceleration coefficients, typically set near 2.0; and $\omega$ is the inertia weight.

The inertia weight $\omega$ is the primary mechanism for scheduling the exploration-exploitation tradeoff across time. A large $\omega$ (near 1.0) produces high-momentum particles that sweep large areas of the search space—favorable early in the run. A small $\omega$ (near 0.4) produces low-momentum particles that converge tightly around local attractors—favorable late in the run when the swarm's belief has concentrated. The standard engineering recommendation, validated across dozens of benchmark studies, is to linearly decay $\omega$ from 0.9 to 0.4 over the course of the run. Shi and Eberhart's empirical analysis demonstrated that this schedule consistently outperforms fixed $\omega$ on multimodal landscapes because it allows the swarm to survey broadly before committing.

The topology of the social network connecting particles is a critical architectural decision that practitioners frequently overlook. The global best topology (gBest), where every particle observes the single best position across the entire swarm, converges fastest on unimodal landscapes but is the most susceptible to premature convergence on multimodal ones, because a single high-fitness region immediately attracts the entire population. The ring topology (lBest), where each particle communicates only with its two nearest neighbors in index space, propagates best-position information much more slowly, preserving diversity and enabling the swarm to maintain multiple distinct search fronts. For neural architecture search over highly multimodal spaces, lBest or clustered topology variants almost always outperform gBest in terms of final solution quality, at the cost of slower convergence.

```c
/*
 * pso_core.c — Canonical PSO implementation for continuous optimization
 * Compile: gcc -O2 -march=native -lm -o pso pso_core.c
 *
 * Demonstrates global-best topology PSO with linear inertia decay.
 * Fitness function: Rastrigin (highly multimodal, d=30 benchmark standard).
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include <time.h>

#define DIM          30
#define N_PARTICLES  60
#define MAX_ITER     2000
#define X_MIN       -5.12
#define X_MAX        5.12
#define V_MAX        1.0
#define C1           2.05
#define C2           2.05
#define OMEGA_START  0.9
#define OMEGA_END    0.4

typedef struct {
    double pos[DIM];
    double vel[DIM];
    double pbest_pos[DIM];
    double pbest_fit;
} Particle;

static double rand_uniform(void) {
    return (double)rand() / (double)RAND_MAX;
}

/* Rastrigin function: global minimum = 0.0 at origin */
static double rastrigin(const double *x) {
    double sum = 10.0 * DIM;
    for (int i = 0; i < DIM; i++) {
        sum += x[i] * x[i] - 10.0 * cos(2.0 * M_PI * x[i]);
    }
    return sum;
}

static void clamp_velocity(double *v) {
    for (int j = 0; j < DIM; j++) {
        if (v[j] >  V_MAX) v[j] =  V_MAX;
        if (v[j] < -V_MAX) v[j] = -V_MAX;
    }
}

static void clamp_position(double *x) {
    for (int j = 0; j < DIM; j++) {
        if (x[j] > X_MAX) x[j] = X_MAX;
        if (x[j] < X_MIN) x[j] = X_MIN;
    }
}

int main(void) {
    srand((unsigned)time(NULL));

    Particle swarm[N_PARTICLES];
    double   gbest_pos[DIM];
    double   gbest_fit = DBL_MAX;

    /* Initialization: uniform random positions and velocities */
    for (int i = 0; i < N_PARTICLES; i++) {
        for (int j = 0; j < DIM; j++) {
            swarm[i].pos[j] = X_MIN + rand_uniform() * (X_MAX - X_MIN);
            swarm[i].vel[j] = -V_MAX + rand_uniform() * 2.0 * V_MAX;
            swarm[i].pbest_pos[j] = swarm[i].pos[j];
        }
        swarm[i].pbest_fit = rastrigin(swarm[i].pos);
        if (swarm[i].pbest_fit < gbest_fit) {
            gbest_fit = swarm[i].pbest_fit;
            for (int j = 0; j < DIM; j++) gbest_pos[j] = swarm[i].pos[j];
        }
    }

    /* Main optimization loop */
    for (int iter = 0; iter < MAX_ITER; iter++) {
        /* Linear inertia weight decay */
        double omega = OMEGA_START - (OMEGA_START - OMEGA_END) *
                       ((double)iter / (double)MAX_ITER);

        for (int i = 0; i < N_PARTICLES; i++) {
            double r1 = rand_uniform();
            double r2 = rand_uniform();

            for (int j = 0; j < DIM; j++) {
                /* Velocity update: inertia + cognitive + social */
                swarm[i].vel[j] = omega * swarm[i].vel[j]
                    + C1 * r1 * (swarm[i].pbest_pos[j] - swarm[i].pos[j])
                    + C2 * r2 * (gbest_pos[j]           - swarm[i].pos[j]);
            }
            clamp_velocity(swarm[i].vel);

            for (int j = 0; j < DIM; j++) {
                swarm[i].pos[j] += swarm[i].vel[j];
            }
            clamp_position(swarm[i].pos);

            double fit = rastrigin(swarm[i].pos);

            /* Update personal best */
            if (fit < swarm[i].pbest_fit) {
                swarm[i].pbest_fit = fit;
                for (int j = 0; j < DIM; j++)
                    swarm[i].pbest_pos[j] = swarm[i].pos[j];
            }

            /* Update global best */
            if (fit < gbest_fit) {
                gbest_fit = fit;
                for (int j = 0; j < DIM; j++) gbest_pos[j] = swarm[i].pos[j];
            }
        }

        if (iter % 200 == 0) {
            printf("Iter %4d | GBest Fitness: %.6f | omega: %.4f\n",
                   iter, gbest_fit, omega);
        }
    }

    printf("\nFinal global best fitness: %.8f\n", gbest_fit);
    return 0;
}
```

The swarm's information flow follows the architecture below. At each iteration, every particle evaluates its local fitness, updates its personal memory, and reads from the shared global best register. The global best is a lock-free shared read with a single write path, which makes PSO straightforwardly parallelizable across CPU cores or GPU thread blocks with minimal synchronization overhead.

```
                       ┌─────────────────────────────────────┐
                       │          SWARM STATE (t)             │
                       │                                     │
                       │  P₀: [pos | vel | pbest]            │
                       │  P₁: [pos | vel | pbest]            │
                       │  P₂: [pos | vel | pbest]            │
                       │  ...                                 │
                       │  Pₙ: [pos | vel | pbest]            │
                       └────────────┬────────────────────────┘
                                    │  each particle
                                    ▼  evaluates f(x)
                       ┌────────────────────────┐
                       │   FITNESS EVALUATION   │
                       │   f(xᵢ) → scalar      │
                       └────────────┬───────────┘
                                    │
                   ┌────────────────┼────────────────────┐
                   ▼                ▼                     ▼
         Update pbest_i     Update gbest          Compute vᵢ(t+1)
         if f(xᵢ) < pbest   if f(xᵢ) < gbest    ω·vᵢ + c₁r₁(pbest-xᵢ)
                             (shared write)       + c₂r₂(gbest-xᵢ)
                   └────────────────┬────────────────────┘
                                    │
                                    ▼
                            xᵢ(t+1) = xᵢ(t) + vᵢ(t+1)
                            clamp to search bounds
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │   SWARM STATE (t+1)    │
                       │   iterate until        │
                       │   convergence or       │
                       │   budget exhausted     │
                       └────────────────────────┘
```

### Ant Colony Optimization

Where PSO operates over continuous spaces by moving particles along velocity vectors, Ant Colony Optimization operates over discrete combinatorial spaces by constructing solutions incrementally, guided by a pheromone matrix that encodes the swarm's accumulated historical preference for particular solution components. ACO was formalized by Marco Dorigo in his 1992 dissertation and has since become the definitive metaheuristic for routing, scheduling, and graph traversal problems—including, more recently, the topology search phase of neural architecture design.

The biological mechanism that ACO formalizes is **stigmergy**: indirect communication through environmental modification. Real ants deposit pheromone on paths they travel, and the probability of subsequent ants choosing a path is proportional to the pheromone concentration on that path. Because shorter paths are traversed more frequently in a fixed time interval, they accumulate pheromone faster. This positive feedback loop, balanced by pheromone evaporation (which prevents indefinite reinforcement of any single path), converges the colony toward short paths without any ant ever computing a path length globally. The evaporation rate is the analog of the inertia weight in PSO: it controls how quickly the system forgets sub-optimal solutions and how strongly it exploits its current best belief.

Formally, for a problem representable as a weighted graph $G = (V, E)$, the pheromone matrix $\tau_{ij}$ encodes the desirability of traversing edge $(i, j)$. Each ant constructs a complete solution by traversing the graph according to a stochastic decision rule at each node. In the canonical Ant System formulation, ant $k$ at node $i$ selects next node $j$ with probability:

$$P_{ij}^k = \frac{\tau_{ij}^\alpha \cdot \eta_{ij}^\beta}{\sum_{l \in \mathcal{N}_i^k} \tau_{il}^\alpha \cdot \eta_{il}^\beta}$$

where $\eta_{ij} = 1/d_{ij}$ is the heuristic desirability (inverse distance for TSP), $\mathcal{N}_i^k$ is the set of feasible next nodes for ant $k$, and $\alpha$, $\beta$ control the relative influence of pheromone history versus local heuristic. After all ants have completed their tours, the pheromone matrix is updated:

$$\tau_{ij}^{t+1} = (1 - \rho) \cdot \tau_{ij}^t + \sum_{k=1}^{m} \Delta\tau_{ij}^k$$

where $\rho \in (0, 1)$ is the evaporation coefficient and $\Delta\tau_{ij}^k = Q / L_k$ if ant $k$ traversed edge $(i, j)$ on its tour of length $L_k$, and zero otherwise. This update rule implements a collective Bayesian update: the pheromone matrix is a non-parametric prior over solution quality, and each ant's tour is a noisy likelihood observation. The evaporation term is the forgetting rate that prevents the prior from becoming too peaked around early-discovered solutions.

The most significant improvement over the basic Ant System is **Ant Colony System** (ACS), which introduced two changes that dramatically improve convergence speed. First, ACS uses a *pseudo-random proportional rule*: with probability $q_0$ (typically 0.9), the ant deterministically selects the edge maximizing $\tau_{ij}^\alpha \cdot \eta_{ij}^\beta$ rather than sampling from the distribution—a greedy exploitation step. With probability $1 - q_0$ it falls back to the stochastic rule. Second, ACS applies a local pheromone update immediately after each edge traversal, slightly evaporating the pheromone on that edge during the construction phase itself. This local update reduces the attractiveness of recently-used edges to subsequent ants in the same iteration, promoting diversity within a single generation and preventing all ants from collapsing onto the same path before the global update runs.

```python
"""
aco_tsp.py — Ant Colony System for the Traveling Salesman Problem
Requires: numpy, matplotlib (optional for visualization)

Implements ACS with pseudo-random proportional rule, local pheromone update,
and global pheromone update restricted to the best-so-far ant.
"""

import numpy as np
from typing import Optional


def euclidean_distance_matrix(coords: np.ndarray) -> np.ndarray:
    """Compute full pairwise Euclidean distance matrix from (n, 2) coords."""
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    return np.sqrt((diff ** 2).sum(axis=2))


def tour_length(tour: list[int], dist: np.ndarray) -> float:
    return sum(dist[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour)))


class AntColonySystem:
    """
    Parameters
    ----------
    dist        : (n, n) pairwise distance matrix
    n_ants      : number of ants per iteration
    n_iter      : number of optimization iterations
    alpha       : pheromone exponent (ACS typically fixes alpha=1)
    beta        : heuristic exponent (higher = stronger greedy bias)
    rho         : global evaporation coefficient
    phi         : local evaporation coefficient (ACS local update)
    q0          : exploitation probability in pseudo-random rule
    tau_init    : initial pheromone concentration on all edges
    """

    def __init__(
        self,
        dist: np.ndarray,
        n_ants: int = 20,
        n_iter: int = 300,
        alpha: float = 1.0,
        beta: float = 2.5,
        rho: float = 0.1,
        phi: float = 0.1,
        q0: float = 0.9,
        tau_init: Optional[float] = None,
        seed: int = 42,
    ):
        self.dist = dist
        self.n = dist.shape[0]
        self.n_ants = n_ants
        self.n_iter = n_iter
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.phi = phi
        self.q0 = q0
        self.rng = np.random.default_rng(seed)

        # Heuristic desirability: 1/d, avoid division by zero on diagonal
        with np.errstate(divide="ignore", invalid="ignore"):
            self.eta = np.where(dist > 0, 1.0 / dist, 0.0)

        # Initialize pheromone: use nearest-neighbor heuristic estimate if not given
        self.tau_init = tau_init if tau_init is not None else 1.0 / (self.n * self._nn_tour_length())
        self.tau = np.full((self.n, self.n), self.tau_init)

        self.best_tour: list[int] = []
        self.best_length: float = float("inf")

    def _nn_tour_length(self) -> float:
        """Greedy nearest-neighbor tour from node 0 for tau initialization."""
        visited = [False] * self.n
        tour = [0]
        visited[0] = True
        for _ in range(self.n - 1):
            current = tour[-1]
            distances = self.dist[current].copy()
            distances[visited] = np.inf
            nearest = int(np.argmin(distances))
            tour.append(nearest)
            visited[nearest] = True
        return tour_length(tour, self.dist)

    def _construct_tour(self, start: int) -> list[int]:
        visited = np.zeros(self.n, dtype=bool)
        tour = [start]
        visited[start] = True

        for _ in range(self.n - 1):
            current = tour[-1]
            feasible = np.where(~visited)[0]

            # Pseudo-random proportional rule (ACS)
            if self.rng.random() < self.q0:
                # Exploitation: deterministic argmax
                scores = (self.tau[current, feasible] ** self.alpha) * \
                         (self.eta[current, feasible] ** self.beta)
                next_node = feasible[np.argmax(scores)]
            else:
                # Exploration: sample proportional to pheromone × heuristic
                scores = (self.tau[current, feasible] ** self.alpha) * \
                         (self.eta[current, feasible] ** self.beta)
                probs = scores / scores.sum()
                next_node = self.rng.choice(feasible, p=probs)

            # Local pheromone update: evaporate edge just traversed
            self.tau[current, next_node] = (1.0 - self.phi) * self.tau[current, next_node] \
                                            + self.phi * self.tau_init
            self.tau[next_node, current] = self.tau[current, next_node]

            tour.append(next_node)
            visited[next_node] = True

        return tour

    def optimize(self) -> tuple[list[int], float]:
        for iteration in range(self.n_iter):
            iteration_tours = []

            # Each ant constructs a complete tour from a random start node
            for _ in range(self.n_ants):
                start = int(self.rng.integers(0, self.n))
                tour = self._construct_tour(start)
                length = tour_length(tour, self.dist)
                iteration_tours.append((tour, length))

                if length < self.best_length:
                    self.best_length = length
                    self.best_tour = tour[:]

            # Global pheromone update: only the best-so-far ant deposits
            self.tau *= (1.0 - self.rho)
            best_tour_this_iter = min(iteration_tours, key=lambda x: x[1])
            deposit = 1.0 / best_tour_this_iter[1]
            t = best_tour_this_iter[0]
            for i in range(self.n):
                a, b = t[i], t[(i + 1) % self.n]
                self.tau[a, b] += self.rho * deposit
                self.tau[b, a] = self.tau[a, b]

            if iteration % 50 == 0:
                print(f"Iter {iteration:4d} | Best length: {self.best_length:.4f}")

        return self.best_tour, self.best_length


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n_cities = 50
    coords = rng.uniform(0, 100, size=(n_cities, 2))
    dist = euclidean_distance_matrix(coords)

    acs = AntColonySystem(dist, n_ants=20, n_iter=300, beta=2.5, rho=0.1, phi=0.1, q0=0.9)
    best_tour, best_length = acs.optimize()
    print(f"\nFinal tour length: {best_length:.4f}")
    print(f"Tour (first 10 nodes): {best_tour[:10]}")
```

### Bee Algorithms and the Artificial Bee Colony

The Artificial Bee Colony algorithm, introduced by Karaboga in 2005, models the division of labor in a honeybee hive as a three-role system: **employed bees** exploit known food sources by searching in their immediate neighborhood; **onlooker bees** observe the waggle dances of returning employed bees and probabilistically choose which food sources to reinforce based on perceived quality; and **scout bees** replace employed bees whose sources have been abandoned after exhaustion, performing uniform random search to discover entirely new regions. This role decomposition is a direct implementation of an adaptive exploration-exploitation scheduler: the waggle dance is a physical communication mechanism that allocates more workers to better food sources, while the scout role guarantees a minimum rate of exploration even when the swarm has found high-quality solutions.

The architectural elegance of ABC is that it implements population-based Bayesian optimization without explicitly modeling a surrogate. The number of onlooker bees allocated to food source $i$ is proportional to $\text{fit}_i / \sum_j \text{fit}_j$, where $\text{fit}_i$ is a fitness score. This is a softmax allocation rule with temperature parameter implicitly set by the fitness landscape's scale. The neighborhood search performed by employed bees follows:

$$v_{ij} = x_{ij} + \phi_{ij}(x_{ij} - x_{kj})$$

where $k \neq i$ is a randomly chosen partner solution, $j$ is a randomly chosen dimension, and $\phi_{ij} \sim \text{Uniform}(-1, 1)$. This update generates a candidate position by moving in the direction of the difference between two existing solutions—a differential evolution-style perturbation that scales automatically with the current spread of the population. When the population is diverse, perturbations are large, favoring exploration. As the population converges, perturbations shrink, refining search around the best-known regions. This self-scaling property makes ABC robust to the fitness landscape's scale without manual step-size tuning.

### Reynolds' Flocking Rules and Emergent Behavior in Agentic Swarms

Craig Reynolds' 1987 Boids model establishes the minimum set of local rules sufficient to produce globally coherent flocking behavior, and it is directly applicable to multi-agent coordination in agentic AI systems where agents must navigate shared state spaces without centralized control. The three rules are **separation** (steer to avoid crowding neighbors), **alignment** (steer toward the average heading of neighbors), and **cohesion** (steer toward the average position of neighbors). No agent has global knowledge; all interactions are strictly local within a perception radius $r$.

The importance of Boids for agentic swarm engineers is not the simulation itself but the existence proof it provides: stable, coordinated collective behavior emerges from purely local rules at a computational cost that scales linearly with agent count. When translated to agentic AI systems—where agents share a vector embedding space, a knowledge graph, or a task queue rather than physical space—these three rules map onto mechanisms for maintaining semantic diversity among agents (separation), aligning agents' current objectives or reasoning strategies (alignment), and preventing fragmentation of the agent collective away from the shared problem domain (cohesion). The formal agentic analog is a multi-agent system where each agent's policy update is regularized by the policies of its $k$ nearest neighbors in embedding space, which produces convergence toward consensus behavior without a central coordinator.

```python
"""
boids.py — Vectorized Boids flocking simulation with NumPy
Demonstrates separation, alignment, and cohesion on N agents in 2D.
Extend to multi-agent LLM coordination by replacing position/velocity
with embedding vectors and policy gradient updates.
"""

import numpy as np


class BoidsSimulation:
    """
    Parameters
    ----------
    n_agents        : number of agents
    perception_r    : radius within which an agent perceives neighbors
    sep_weight      : weight for separation force
    align_weight    : weight for alignment force
    cohesion_weight : weight for cohesion force
    max_speed       : velocity clamp
    bounds          : (width, height) of the toroidal arena
    """

    def __init__(
        self,
        n_agents: int = 200,
        perception_r: float = 50.0,
        sep_weight: float = 1.5,
        align_weight: float = 1.0,
        cohesion_weight: float = 1.0,
        max_speed: float = 4.0,
        bounds: tuple[float, float] = (800.0, 600.0),
        seed: int = 0,
    ):
        self.n = n_agents
        self.r = perception_r
        self.w_sep = sep_weight
        self.w_ali = align_weight
        self.w_coh = cohesion_weight
        self.max_speed = max_speed
        self.W, self.H = bounds

        rng = np.random.default_rng(seed)
        self.pos = rng.uniform([0, 0], [self.W, self.H], size=(self.n, 2))
        angles = rng.uniform(0, 2 * np.pi, size=self.n)
        self.vel = np.stack([np.cos(angles), np.sin(angles)], axis=1) * (max_speed * 0.5)

    def _pairwise_delta(self) -> np.ndarray:
        """
        Returns (n, n, 2) array of displacement vectors from i to j,
        accounting for toroidal wrap-around.
        """
        delta = self.pos[np.newaxis, :, :] - self.pos[:, np.newaxis, :]
        # Toroidal wrap: shortest path across periodic boundary
        delta[..., 0] = (delta[..., 0] + self.W / 2) % self.W - self.W / 2
        delta[..., 1] = (delta[..., 1] + self.H / 2) % self.H - self.H / 2
        return delta

    def step(self) -> None:
        delta = self._pairwise_delta()                       # (n, n, 2)
        dist = np.linalg.norm(delta, axis=2)                 # (n, n)
        np.fill_diagonal(dist, np.inf)                       # exclude self
        neighbor_mask = dist < self.r                        # (n, n) bool

        sep_force   = np.zeros((self.n, 2))
        align_force = np.zeros((self.n, 2))
        cohesion_force = np.zeros((self.n, 2))

        for i in range(self.n):
            neighbors = neighbor_mask[i]
            n_count = neighbors.sum()
            if n_count == 0:
                continue

            # Separation: steer away from neighbors, weighted by inverse distance
            sep_vecs = -delta[i][neighbors]                  # vectors FROM neighbor TO i
            safe_dist = np.maximum(dist[i][neighbors], 1e-6)
            sep_force[i] = (sep_vecs / safe_dist[:, np.newaxis]).sum(axis=0) / n_count

            # Alignment: match velocity of neighbors
            align_force[i] = self.vel[neighbors].mean(axis=0) - self.vel[i]

            # Cohesion: steer toward centroid of neighbors
            centroid = self.pos[neighbors].mean(axis=0)
            cohesion_force[i] = centroid - self.pos[i]

        acceleration = (self.w_sep   * sep_force
                      + self.w_ali   * align_force
                      + self.w_coh   * cohesion_force)

        self.vel += acceleration
        # Clamp to max speed
        speeds = np.linalg.norm(self.vel, axis=1, keepdims=True)
        self.vel = np.where(speeds > self.max_speed,
                            self.vel / speeds * self.max_speed,
                            self.vel)
        self.pos = (self.pos + self.vel) % np.array([self.W, self.H])

    def run(self, steps: int = 500) -> None:
        for step_idx in range(steps):
            self.step()
            if step_idx % 100 == 0:
                mean_speed = np.linalg.norm(self.vel, axis=1).mean()
                # Order parameter: how aligned are velocities? (1.0 = perfectly aligned)
                mean_vel = self.vel.mean(axis=0)
                order = np.linalg.norm(mean_vel) / mean_speed
                print(f"Step {step_idx:4d} | Order parameter: {order:.4f} | "
                      f"Mean speed: {mean_speed:.4f}")


if __name__ == "__main__":
    sim = BoidsSimulation(n_agents=300, perception_r=50.0,
                          sep_weight=1.5, align_weight=1.0, cohesion_weight=1.0)
    sim.run(steps=500)
```

The order parameter printed above, $\psi = \|\bar{v}\| / \bar{s}$, is the standard measure of flocking coherence from statistical physics. When $\psi \approx 0$ the swarm is in a disordered phase with randomly oriented velocities; when $\psi \approx 1$ all agents are aligned. In agentic AI swarms, this metric can be adapted to measure the degree of strategic consensus among agents: replace velocity vectors with embedding-space policy gradients or attention weight distributions, and the same order parameter quantifies how coordinated the agents' reasoning has become.

---

## 3. High-Performance Optimization & Failure Modes

### Scaling Swarm Algorithms to Production Agentic Systems

The transition from textbook swarm algorithms to production agentic systems introduces three classes of engineering challenge that the academic literature systematically underweights: **asynchronous fitness evaluation**, **dynamic landscape drift**, and **multi-objective Pareto pressure**. Each requires specific architectural countermeasures.

Asynchronous evaluation arises because agentic swarms frequently operate in environments where fitness computation is not instantaneous. When fitness is a large neural network inference, a simulation rollout, or an external API call, the synchronous model—where all agents complete their evaluations before any velocity or pheromone update occurs—becomes the performance bottleneck. The standard solution is an **asynchronous evaluation pool** pattern: agents submit their candidate solutions to a shared job queue, a pool of workers evaluates them concurrently, and completed evaluations are immediately used to update the swarm state without waiting for the remaining in-flight evaluations. For PSO, this means maintaining a *partially updated* global best that reflects all evaluations completed so far. Research from Google Brain's work on asynchronous PSO (Kennedy & Mendes, 2002, later extended in distributed hyperparameter tuning literature) shows that asynchronous updates converge in wall-clock time significantly faster than synchronous variants, though they require more function evaluations to reach the same solution quality because stale global best information introduces noise into velocity updates.

```python
"""
async_pso_evaluator.py — Asynchronous PSO using Python's concurrent.futures.
Demonstrates how to decouple fitness evaluation from swarm state updates
for environments where evaluation latency dominates runtime.
"""

import numpy as np
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Particle:
    pos: np.ndarray
    vel: np.ndarray
    pbest_pos: np.ndarray
    pbest_fit: float = float("inf")
    particle_id: int = 0


def expensive_fitness(args: tuple[int, np.ndarray]) -> tuple[int, float]:
    """
    Simulate an expensive evaluation (e.g., neural net training rollout).
    Replace this body with the actual objective in production.
    particle_id is passed through so results can be matched to particles.
    """
    particle_id, pos = args
    # Simulated latency: real workloads vary 10x–100x across evaluations
    time.sleep(np.random.uniform(0.001, 0.005))
    # Rastrigin fitness
    d = len(pos)
    fit = 10.0 * d + sum(x**2 - 10.0 * np.cos(2.0 * np.pi * x) for x in pos)
    return particle_id, fit


class AsyncPSO:
    def __init__(
        self,
        dim: int = 10,
        n_particles: int = 40,
        max_iter: int = 200,
        x_bounds: tuple[float, float] = (-5.12, 5.12),
        omega_start: float = 0.9,
        omega_end: float = 0.4,
        c1: float = 2.05,
        c2: float = 2.05,
        n_workers: int = 8,
        seed: int = 0,
    ):
        self.dim = dim
        self.n = n_particles
        self.max_iter = max_iter
        self.xmin, self.xmax = x_bounds
        self.omega_start = omega_start
        self.omega_end = omega_end
        self.c1 = c1
        self.c2 = c2
        self.n_workers = n_workers

        rng = np.random.default_rng(seed)
        self.particles: list[Particle] = []
        for pid in range(self.n):
            pos = rng.uniform(self.xmin, self.xmax, size=self.dim)
            vel = rng.uniform(-1.0, 1.0, size=self.dim)
            self.particles.append(Particle(
                pos=pos.copy(), vel=vel.copy(), pbest_pos=pos.copy(), particle_id=pid
            ))

        self.gbest_pos: np.ndarray = self.particles[0].pos.copy()
        self.gbest_fit: float = float("inf")
        self.rng = rng

    def _update_velocity(self, p: Particle, omega: float) -> None:
        r1 = self.rng.uniform(0, 1, self.dim)
        r2 = self.rng.uniform(0, 1, self.dim)
        p.vel = (omega * p.vel
                 + self.c1 * r1 * (p.pbest_pos - p.pos)
                 + self.c2 * r2 * (self.gbest_pos - p.pos))
        p.vel = np.clip(p.vel, -1.0, 1.0)
        p.pos = np.clip(p.pos + p.vel, self.xmin, self.xmax)

    def optimize(self) -> tuple[np.ndarray, float]:
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            for iteration in range(self.max_iter):
                omega = self.omega_start - (self.omega_start - self.omega_end) * \
                        (iteration / self.max_iter)

                # Submit all current positions for async evaluation
                futures = {
                    executor.submit(expensive_fitness, (p.particle_id, p.pos.copy())): p
                    for p in self.particles
                }

                # Process results as they complete — no waiting for stragglers
                for future in as_completed(futures):
                    pid, fit = future.result()
                    p = futures[future]

                    if fit < p.pbest_fit:
                        p.pbest_fit = fit
                        p.pbest_pos = p.pos.copy()

                    if fit < self.gbest_fit:
                        self.gbest_fit = fit
                        self.gbest_pos = p.pos.copy()

                # Update velocities and positions with current gbest
                for p in self.particles:
                    self._update_velocity(p, omega)

                if iteration % 20 == 0:
                    print(f"Iter {iteration:4d} | GBest: {self.gbest_fit:.6f} | omega: {omega:.3f}")

        return self.gbest_pos, self.gbest_fit


if __name__ == "__main__":
    optimizer = AsyncPSO(dim=10, n_particles=40, max_iter=200, n_workers=8)
    best_pos, best_fit = optimizer.optimize()
    print(f"\nFinal best fitness: {best_fit:.8f}")
```

### Landscape Drift and Online Re-optimization

Dynamic optimization problems—where the fitness function $f(\mathbf{x}, t)$ changes over time—are the rule rather than the exception in production agentic systems. Agent performance objectives, environmental reward signals, and task distributions all shift as the deployment context evolves. A swarm that has converged tightly around a previous optimum becomes *over-committed*: its population diversity has collapsed to near zero, and when the landscape shifts, the swarm has lost the exploratory capacity needed to track the new optimum. This phenomenon is called **diversity collapse**, and it is the most common failure mode in deployed swarm optimizers.

Three mitigation strategies address diversity collapse in production. The first is **hypermutation**, where a subset of particles or ants are periodically reinitialized uniformly at random when stagnation is detected—typically measured as fewer than a threshold improvement in $f_\text{best}$ over the last $k$ iterations. The second is **exclusion**, where particles that converge within a minimum distance $r_\text{excl}$ of a particle with a better fitness are forcibly repelled to random positions, preventing the entire swarm from collapsing onto a single basin. The third, most architecturally sophisticated, is **multi-swarm parallelism**: rather than running a single swarm of size $N$, run $k$ independent sub-swarms of size $N/k$, with periodic migration of the best individual from each sub-swarm to its neighbors in a ring topology. This maintains $k$ independent search fronts, is naturally parallelizable across compute nodes, and has the statistical property that the probability of at least one sub-swarm escaping a local optimum in any given iteration is $1 - (1 - p_\text{escape})^k$, where $p_\text{escape}$ is the per-swarm escape probability—exponentially better than a single-swarm escape probability.

### Premature Convergence and the No Free Lunch Theorems

Wolpert and Macready's No Free Lunch theorems (1997) establish that over all possible objective functions, every optimization algorithm performs equally well on average. No swarm algorithm, however cleverly designed, can outperform random search on a uniformly random fitness landscape. The theorems are frequently misread as nihilistic, but their engineering implication is constructive: the choice of optimization algorithm must be matched to the problem's structural properties. PSO is advantageous for continuous, multimodal landscapes where particle momentum can carry solutions across shallow local optima barriers. ACO is advantageous for combinatorial problems with a natural graph structure where the pheromone matrix can encode meaningful heuristic knowledge. ABC is advantageous for problems where scale information is unavailable and self-adapting step sizes are beneficial. Bee algorithms (specifically the Bees Algorithm, distinct from ABC) are advantageous for problems with well-separated basins of attraction, because their combination of elite-site exploitation with random site recruitment mimics a parallel basin-hopping strategy.

Premature convergence manifests differently in each algorithm. In PSO, it appears as all particles clustering around a single gbest position with near-zero velocity magnitude—easily detected by monitoring $\text{std}(\|\mathbf{v}_i\|)$ across the population. In ACO, it appears as the pheromone matrix developing extreme values: a small number of edges with $\tau_{ij} \gg \tau_\text{init}$ and the remainder approaching zero—detectable by monitoring the entropy $H(\tau) = -\sum_{ij} \hat{\tau}_{ij} \log \hat{\tau}_{ij}$ of the normalized pheromone matrix. When entropy falls below a threshold (typically 20–30% of its initial value), the solution space has effectively been reduced to the neighborhood of a single tour, and aggressive pheromone reinitialization is required to restore diversity.

The fitness landscape diagnostic toolkit that every practitioner should maintain includes **empirical fitness-distance correlation** (FDC), which measures the correlation between a solution's fitness and its distance from the known global optimum across a sample of random solutions. FDC near 1.0 indicates a landscape that is unimodal and easily solvable by any algorithm. FDC near 0.0 indicates a random landscape. FDC near -1.0 indicates a deceptive landscape where gradient following leads away from the global optimum—the most dangerous case for any algorithm with a strong exploitation bias. Computing FDC requires knowing the global optimum, which is impossible in production, but it can be approximated by using the best solution found so far as a proxy optimum and monitoring whether the correlation structure changes as the swarm improves its estimate.

### Multi-Objective Swarm Optimization

Production agentic systems rarely optimize a single scalar objective. A multi-agent LLM orchestration layer might simultaneously optimize for response latency, token cost, accuracy on a benchmark, and robustness to adversarial inputs. These objectives are frequently in tension: lower latency often requires smaller models with lower accuracy; robustness techniques add computational overhead. The appropriate formalization is not a weighted sum of objectives (which requires pre-specifying trade-off weights that are often unknown) but a Pareto front approximation, where the goal is to identify the set of solutions that are non-dominated—no solution on the Pareto front can be improved on any objective without degrading at least one other.

Multi-Objective PSO (MOPSO) extends the standard PSO architecture by replacing the single global best with an **external archive** of non-dominated solutions discovered so far. Each particle's gbest is selected from the archive using a selection mechanism that promotes diversity along the Pareto front—typically hypercube-based selection, where the archive is divided into hypercubes in objective space and particles are preferentially guided toward the least-crowded hypercube, preventing collapse of the Pareto front approximation onto a single region. The personal best comparison is extended to Pareto dominance: a new position replaces pbest only if it dominates the current pbest in at least one objective and is not dominated in any other.

```python
"""
mopso.py — Multi-Objective PSO with external Pareto archive
Optimizes a bi-objective benchmark: minimize f1(x) and f2(x) simultaneously.
Uses hypercube crowding-distance archive selection for Pareto diversity.
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class MOParticle:
    pos: np.ndarray
    vel: np.ndarray
    pbest_pos: np.ndarray
    pbest_obj: np.ndarray   # objective vector at pbest
    obj: np.ndarray = field(default_factory=lambda: np.array([]))


def zdt1(x: np.ndarray) -> np.ndarray:
    """
    ZDT1 benchmark: standard bi-objective test function.
    Pareto front is f2 = 1 - sqrt(f1) for f1 in [0, 1].
    x in [0, 1]^d
    """
    n = len(x)
    f1 = x[0]
    g = 1.0 + 9.0 * x[1:].sum() / (n - 1)
    f2 = g * (1.0 - np.sqrt(f1 / g))
    return np.array([f1, f2])


def dominates(a: np.ndarray, b: np.ndarray) -> bool:
    """Return True if objective vector a Pareto-dominates b."""
    return np.all(a <= b) and np.any(a < b)


def update_archive(archive: list[MOParticle], candidate: MOParticle,
                   max_size: int = 100) -> list[MOParticle]:
    """Add candidate to archive, remove dominated solutions, enforce size limit."""
    new_archive = [p for p in archive if not dominates(candidate.obj, p.obj)]
    if not any(dominates(p.obj, candidate.obj) for p in new_archive):
        new_archive.append(candidate)
    # Size enforcement: remove most crowded solutions if archive exceeds limit
    if len(new_archive) > max_size:
        objs = np.array([p.obj for p in new_archive])
        # Compute crowding distance and remove smallest
        crowd = _crowding_distance(objs)
        sorted_idx = np.argsort(crowd)
        keep = sorted_idx[len(new_archive) - max_size:]
        new_archive = [new_archive[i] for i in keep]
    return new_archive


def _crowding_distance(objs: np.ndarray) -> np.ndarray:
    """Compute crowding distance in objective space for archive diversity."""
    n, m = objs.shape
    dist = np.zeros(n)
    for obj_idx in range(m):
        sorted_idx = np.argsort(objs[:, obj_idx])
        dist[sorted_idx[0]] = dist[sorted_idx[-1]] = np.inf
        obj_range = objs[sorted_idx[-1], obj_idx] - objs[sorted_idx[0], obj_idx]
        if obj_range == 0:
            continue
        for i in range(1, n - 1):
            dist[sorted_idx[i]] += (objs[sorted_idx[i + 1], obj_idx] -
                                     objs[sorted_idx[i - 1], obj_idx]) / obj_range
    return dist


class MOPSO:
    def __init__(
        self,
        dim: int = 10,
        n_particles: int = 100,
        n_iter: int = 250,
        omega: float = 0.4,
        c1: float = 2.0,
        c2: float = 2.0,
        archive_size: int = 100,
        seed: int = 0,
    ):
        self.dim = dim
        self.n = n_particles
        self.n_iter = n_iter
        self.omega = omega
        self.c1 = c1
        self.c2 = c2
        self.archive_size = archive_size
        self.rng = np.random.default_rng(seed)

        self.particles: list[MOParticle] = []
        for _ in range(self.n):
            pos = self.rng.uniform(0, 1, size=self.dim)
            vel = self.rng.uniform(-0.1, 0.1, size=self.dim)
            obj = zdt1(pos)
            p = MOParticle(pos=pos, vel=vel, pbest_pos=pos.copy(), pbest_obj=obj.copy(), obj=obj)
            self.particles.append(p)

        self.archive: list[MOParticle] = list(self.particles[:])

    def _select_gbest(self) -> np.ndarray:
        """Select leader from archive using crowding-distance tournament."""
        if len(self.archive) == 1:
            return self.archive[0].pbest_pos
        objs = np.array([p.obj for p in self.archive])
        crowd = _crowding_distance(objs)
        # Tournament: pick two random archive members, prefer less-crowded
        idx_a, idx_b = self.rng.choice(len(self.archive), size=2, replace=False)
        winner = idx_a if crowd[idx_a] > crowd[idx_b] else idx_b
        return self.archive[winner].pbest_pos

    def optimize(self) -> list[np.ndarray]:
        for iteration in range(self.n_iter):
            for p in self.particles:
                gbest_pos = self._select_gbest()
                r1 = self.rng.uniform(0, 1, self.dim)
                r2 = self.rng.uniform(0, 1, self.dim)

                p.vel = (self.omega * p.vel
                         + self.c1 * r1 * (p.pbest_pos - p.pos)
                         + self.c2 * r2 * (gbest_pos    - p.pos))
                p.vel = np.clip(p.vel, -0.5, 0.5)
                p.pos = np.clip(p.pos + p.vel, 0.0, 1.0)
                p.obj = zdt1(p.pos)

                # Update personal best using Pareto dominance
                if dominates(p.obj, p.pbest_obj):
                    p.pbest_pos = p.pos.copy()
                    p.pbest_obj = p.obj.copy()
                elif not dominates(p.pbest_obj, p.obj):
                    # Non-dominated: randomly accept (maintain diversity)
                    if self.rng.random() < 0.5:
                        p.pbest_pos = p.pos.copy()
                        p.pbest_obj = p.obj.copy()

                self.archive = update_archive(self.archive, p, self.archive_size)

            if iteration % 50 == 0:
                print(f"Iter {iteration:4d} | Archive size: {len(self.archive)}")

        return [p.obj for p in self.archive]


if __name__ == "__main__":
    mopso = MOPSO(dim=10, n_particles=100, n_iter=250)
    pareto_front = mopso.optimize()
    pareto_array = np.array(pareto_front)
    print(f"\nPareto front approximation ({len(pareto_front)} solutions):")
    print(f"  f1 range: [{pareto_array[:, 0].min():.4f}, {pareto_array[:, 0].max():.4f}]")
    print(f"  f2 range: [{pareto_array[:, 1].min():.4f}, {pareto_array[:, 1].max():.4f}]")
```

### Convergence Guarantees and Theoretical Boundaries

The theoretical convergence analysis of swarm algorithms is significantly less mature than that of gradient-based optimization, and practitioners should understand what guarantees exist and—critically—where they break down. For standard PSO with constriction factor formulation (Clerc and Kennedy, 2002), where velocities are multiplied by a constriction coefficient $\chi = 2 / |2 - \phi - \sqrt{\phi^2 - 4\phi}|$ with $\phi = c_1 + c_2 > 4$, it can be proven that particles converge to a stable equilibrium point that is a convex combination of their personal best and global best positions. This guarantees that the swarm will not diverge explosively—a stability guarantee—but it does not guarantee convergence to the global optimum. The equilibrium point is a local attractor, and whether it corresponds to the global optimum depends entirely on the landscape's topology.

For stochastic PSO variants, Jiang et al. (2007) and van den Bergh's earlier work established that PSO converges to a random attractor with probability one under mild conditions, using martingale theory. The practical implication is that PSO is guaranteed to converge *to something*, but proving bounds on the quality of that something requires assumptions about the fitness landscape that cannot be verified in advance. For ACO, Gutjahr (2000) provided the first rigorous convergence proof showing that the probability of ACO finding the global optimum converges to one as the number of iterations goes to infinity, under the condition that the pheromone evaporation rate satisfies $\rho \in (0, 1)$ and the minimum pheromone value is bounded below by a positive constant. These are satisfiable in practice but require explicit implementation: without a minimum pheromone floor $\tau_\text{min}$, edges can reach effectively zero pheromone concentration and become permanently excluded from consideration—cutting off paths to the global optimum.

The engineering translation of these theoretical results is a set of concrete implementation requirements. PSO deployments must monitor population diversity via $\text{std}(\mathbf{x}_i)$ across dimensions and trigger reinitializations when it falls below a threshold. ACO deployments must enforce a pheromone floor $\tau_\text{min} > 0$ on all edges and monitor pheromone entropy to detect premature crystallization of the pheromone distribution. All swarm optimizers must track stagnation windows—iterations elapsed since the last improvement in $f_\text{best}$—and respond with either population diversification or controlled restarts when stagnation exceeds the expected exploration budget for the problem's dimensionality.

The relationship between problem dimensionality and required swarm size is governed by the **curse of dimensionality** in its swarm-specific form: the volume of a hypercube in $d$ dimensions grows as $L^d$, so the density of particles per unit volume decreases exponentially with dimension. For $d > 100$, standard PSO with 50–100 particles is sampling an astronomically sparse fraction of the search space, and the algorithm's effectiveness depends almost entirely on the problem having low **intrinsic dimensionality**—a small number of dimensions that meaningfully influence fitness. Modern high-dimensional applications (neural architecture search over hundreds of hyperparameters, LLM prompt optimization) therefore combine swarm methods with dimensionality reduction: candidate solutions are encoded in a low-dimensional latent space learned by a variational autoencoder or Gaussian process surrogate, the swarm operates in this compressed space, and candidates are decoded back to full dimensionality for evaluation. This hybrid architecture—swarm search over surrogate-compressed spaces—is currently the state of the art for agentic hyperparameter optimization at scale, combining the exploration advantages of swarm methods with the sample efficiency of Bayesian surrogate models.
