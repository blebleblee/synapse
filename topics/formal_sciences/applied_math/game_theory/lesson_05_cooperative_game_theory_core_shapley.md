# Lesson 5: Cooperative Game Theory, Core, Shapley Value

## 1. First-Principles Intuition & Invariants

### The Fundamental Shift: From Competition to Coalition

Non-cooperative game theory asks a tightly constrained question: given a fixed set of strategic options, what does rational individual behavior produce? The Nash equilibrium, however elegant, is ultimately a theory of mutual best responses, and it is indifferent to the aggregate welfare those responses generate. Cooperative game theory asks an entirely different question. When players *can* communicate, write binding agreements, and redistribute payoffs freely among themselves, what coalitions will form, and how should the gains from cooperation be allocated? The shift is not merely one of modeling convention. It represents a philosophical reorientation from the mechanics of strategic interaction to the mathematics of fair division under collective rationality.

The practical relevance is immediate. Cost-sharing in telecommunications networks, profit division among corporate joint ventures, voting power in legislative assemblies, and nucleotide sequence alignment in computational biology all share a common structure: a set of agents, a function that assigns a worth to every subset of those agents, and the problem of distributing that worth in a way that is simultaneously stable and equitable. The characteristic function form is the mathematical language that captures exactly this structure.

### The Characteristic Function and Superadditivity

A **cooperative game in characteristic function form** is a pair $(N, v)$ where $N = \{1, 2, \ldots, n\}$ is a finite set of players and $v : 2^N \to \mathbb{R}$ is a function mapping every coalition $S \subseteq N$ to a real number $v(S)$, subject to the normalization $v(\emptyset) = 0$. The value $v(S)$ represents the total payoff that coalition $S$ can guarantee itself through coordinated action, regardless of what the players outside $S$ do. This guaranteed-value interpretation, formalized by von Neumann and Morgenstern in their 1944 treatise, allows us to decouple the analysis of coalition formation from the specifics of the underlying strategic game.

The first structural property that any interesting cooperative game should satisfy is **superadditivity**. A game $(N, v)$ is superadditive if for all disjoint coalitions $S, T \subseteq N$ with $S \cap T = \emptyset$,

$$v(S \cup T) \geq v(S) + v(T).$$

Superadditivity encodes the basic premise that cooperation is beneficial: by merging, two coalitions can do at least as well as they could separately. When this condition holds, there is always an incentive for the grand coalition $N$ to form, because its value weakly dominates any partition of players into smaller groups. Most economically interesting games are superadditive, though important exceptions arise in games with congestion or communication constraints.

A strictly stronger condition is **convexity**. A game $(N, v)$ is convex if for all $S \subseteq T \subseteq N$ and all $i \notin T$,

$$v(T \cup \{i\}) - v(T) \geq v(S \cup \{i\}) - v(S).$$

Convexity says that the marginal contribution of player $i$ to a coalition is nondecreasing in the size of that coalition: the larger the coalition $i$ joins, the more $i$ contributes. This supermodularity condition captures synergistic effects where scale amplifies productivity. The class of convex games, introduced by Shapley in 1971, enjoys a remarkable collection of structural properties that we will return to throughout this lesson.

**Example 1: A Three-Player Production Game.** Let $N = \{1, 2, 3\}$ represent three firms, where firm 1 owns a manufacturing facility, firm 2 owns a distribution network, and firm 3 owns a retail brand. No single firm can generate revenue alone; in combination, they produce the following:

$$v(\{1\}) = 0, \quad v(\{2\}) = 0, \quad v(\{3\}) = 0,$$
$$v(\{1,2\}) = 40, \quad v(\{1,3\}) = 50, \quad v(\{2,3\}) = 30,$$
$$v(\{1,2,3\}) = 100.$$

This game is superadditive: $v(\{1,2,3\}) = 100 \geq v(\{1,2\}) + v(\{3\}) = 40$, and all similar inequalities hold. We will use this example throughout the lesson to ground each theoretical construct in explicit computation.

### The Core: Stability as a Mathematical Condition

The central stability concept of cooperative game theory is the **core**. An **imputation** is a payoff vector $x = (x_1, x_2, \ldots, x_n) \in \mathbb{R}^n$ satisfying two conditions: individual rationality, $x_i \geq v(\{i\})$ for all $i \in N$, and efficiency, $\sum_{i \in N} x_i = v(N)$. An imputation is a minimal fairness criterion: no player accepts less than what they could guarantee alone, and the full value of the grand coalition is distributed.

The core strengthens this by demanding **coalitional rationality**. The core $C(N, v)$ of a game $(N, v)$ is the set of all imputations $x$ such that for every coalition $S \subseteq N$,

$$\sum_{i \in S} x_i \geq v(S).$$

Geometrically, the core is the intersection of $2^n - 1$ half-spaces (one per nonempty coalition) with the efficiency hyperplane. It is a convex polytope, possibly empty. The economic interpretation is clean: a payoff vector $x$ is in the core if and only if no coalition has an incentive to break away from the grand coalition and redistribute $v(S)$ among its members, since each such coalition is already receiving at least $v(S)$ under $x$.

**Core computation for Example 1.** The core requires $(x_1, x_2, x_3)$ with $x_1 + x_2 + x_3 = 100$ and the six inequality constraints below. The binding ones reduce to:

$$x_1 + x_2 \geq 40, \quad x_1 + x_3 \geq 50, \quad x_2 + x_3 \geq 30,$$
$$x_1 \geq 0, \quad x_2 \geq 0, \quad x_3 \geq 0.$$

Substituting $x_3 = 100 - x_1 - x_2$ into $x_1 + x_3 \geq 50$ gives $100 - x_2 \geq 50$, so $x_2 \leq 50$. From $x_2 + x_3 \geq 30$: $100 - x_1 \geq 30$, so $x_1 \leq 70$. From $x_1 + x_2 \geq 40$: this remains explicit. The core is nonempty; for instance, $x = (35, 25, 40)$ satisfies all constraints. Verification: $35 + 25 = 60 \geq 40$, $35 + 40 = 75 \geq 50$, $25 + 40 = 65 \geq 30$, sum $= 100$.

### Balancedness and the Bondareva-Shapley Theorem

The core can be empty. The classical example is the **three-player majority voting game**, where $v(S) = 1$ if $|S| \geq 2$ and $v(S) = 0$ otherwise. Any imputation $x$ with $x_1 + x_2 + x_3 = 1$ must satisfy $x_1 + x_2 \geq 1$, $x_1 + x_3 \geq 1$, and $x_2 + x_3 \geq 1$ simultaneously, which sum to $2(x_1 + x_2 + x_3) \geq 3$, contradicting the efficiency equation $x_1 + x_2 + x_3 = 1$. The core is empty, reflecting the inherent instability of pure majority power games.

The question of when the core is nonempty is answered definitively by the **Bondareva-Shapley Theorem**, independently established by Olga Bondareva (1963) and Lloyd Shapley (1967). The characterization rests on the concept of a **balanced collection**. A collection $\mathcal{B} = \{S_1, S_2, \ldots, S_k\}$ of coalitions in $N$ is **balanced** if there exist positive weights $\lambda_{S_j} > 0$ for each $S_j \in \mathcal{B}$ such that for every player $i \in N$,

$$\sum_{S \in \mathcal{B} : i \in S} \lambda_S = 1.$$

Intuitively, a balanced collection represents a fractional partition of time: each player $i$ can distribute their participation across the coalitions in $\mathcal{B}$, spending fraction $\lambda_S$ of their time in coalition $S$, so that every player's time fully accounts to 1. The collection $\mathcal{B} = \{\{1,2\}, \{1,3\}, \{2,3\}\}$ with weights $\lambda_S = 1/2$ for each is balanced for $N = \{1,2,3\}$, since each player appears in exactly two of the three coalitions.

**Bondareva-Shapley Theorem.** A game $(N, v)$ has a nonempty core if and only if for every balanced collection $\mathcal{B}$ with weights $\{\lambda_S\}$,

$$\sum_{S \in \mathcal{B}} \lambda_S \cdot v(S) \leq v(N).$$

The proof proceeds in both directions through linear programming duality. Consider the linear program whose feasibility question is exactly the existence of a core element: find $x \in \mathbb{R}^n$ such that $\sum_{i \in S} x_i \geq v(S)$ for all $S \subseteq N$ and $\sum_{i \in N} x_i = v(N)$. The dual of this LP has variables $\lambda_S \geq 0$ for each $S \subsetneq N$. By LP duality, the primal is feasible if and only if the dual is bounded, and the dual boundedness condition translates precisely to the balanced collection inequality stated above. We carry out the duality argument completely.

**Primal LP (Core Feasibility):** We seek $x \in \mathbb{R}^n$ satisfying

$$\sum_{i \in N} x_i = v(N), \qquad \sum_{i \in S} x_i \geq v(S) \text{ for all } S \subsetneq N, \quad S \neq \emptyset.$$

Rewriting the coalition constraints as $-\sum_{i \in S} x_i \leq -v(S)$ and introducing the efficiency equality as two inequalities, the dual LP associates a nonnegative multiplier $\lambda_S \geq 0$ to each proper coalition constraint and an unrestricted multiplier $\mu$ to the efficiency equation. The dual feasibility conditions require, for each player $j \in N$,

$$-\sum_{S \ni j, S \subsetneq N} \lambda_S + \mu \cdot (-1) = 0 \implies \mu = \sum_{S \ni j} \lambda_S \text{ for all } j.$$

This forces all players to have the same coverage sum $\mu$, so normalizing $\mu = 1$ gives exactly the balancedness condition $\sum_{S \ni j} \lambda_S = 1$ for all $j$. The dual objective is $-\sum_S \lambda_S v(S) + \mu \cdot v(N)$, and primal feasibility holds (by strong duality) if and only if this dual objective is bounded above by zero for all dual-feasible $\lambda$, yielding $\sum_S \lambda_S v(S) \leq v(N)$ for all balanced collections. This completes the proof.

**Corollary.** Every convex game has a nonempty core. This follows because convexity implies that the grand coalition's value dominates the balanced weighted sum of coalition values, as the supermodularity condition bounds each such sum from above by $v(N)$.

---

## 2. Core Architecture & Mechanics

### The Structural Anatomy of a Cooperative Game

Before developing solution concepts, it is valuable to understand the computational data model that any formal treatment of cooperative game theory operates on. The characteristic function $v$ on $n$ players is a map from $2^N \to \mathbb{R}$, which requires specifying $2^n - 1$ values (excluding the empty set). For small $n$, this is tractable; for $n = 10$, there are 1023 coalition values. The combinatorial explosion motivates both the importance of structural properties like convexity (which allow efficient parameterization) and the value of compact representations such as weighted voting games, where $v(S) = 1$ if $\sum_{i \in S} w_i \geq q$ for a quota $q$ and player weights $w_i$.

The following diagram shows the structural relationships among the key solution concepts and their mathematical dependencies.

```
Characteristic Function (N, v)
│
├─── Structural Properties
│         │
│         ├── Superadditivity: v(S∪T) ≥ v(S) + v(T)
│         │
│         └── Convexity (Supermodularity):
│                  v(S∪{i}) - v(S) ≥ v(T∪{i}) - v(T), ∀ T ⊆ S
│
├─── Core C(N,v): { x ∈ Rⁿ | Σᵢ xᵢ = v(N), Σᵢ∈S xᵢ ≥ v(S) ∀S }
│         │
│         └── Nonemptiness ⟺ Bondareva-Shapley Balancedness Condition
│                            Σ λₛ v(S) ≤ v(N) for all balanced {λₛ}
│
├─── Shapley Value φ(v): Unique solution satisfying
│         │       Efficiency + Symmetry + Dummy + Additivity
│         │
│         └── Formula: φᵢ(v) = Σₛ [|S|!(n-|S|-1)!/n!] [v(S∪{i}) - v(S)]
│
└─── Bargaining Solutions (Two-Player / Convex Feasible Sets)
          │
          ├── Nash Bargaining: max (u₁-d₁)(u₂-d₂) over feasible set F
          │
          └── Kalai-Smorodinsky: Proportional to utopia point ratio
```

### The Shapley Value: Axiomatic Derivation

The core is a set-valued solution concept: it may be a large polytope, a single point, or empty. When we want a unique point prediction, we turn to the **Shapley value**, which Shapley introduced in 1953 as the unique solution concept satisfying a compelling collection of axioms. The derivation proceeds by identifying the axioms first and then proving uniqueness and existence simultaneously through an explicit formula.

Let $\Gamma^n$ denote the set of all cooperative games on player set $N$ with $|N| = n$. A **value function** is a map $\phi : \Gamma^n \to \mathbb{R}^n$ assigning to each game a payoff vector. Shapley's four axioms are stated as follows.

**Axiom E (Efficiency).** $\sum_{i \in N} \phi_i(v) = v(N)$. The value distributes the full worth of the grand coalition.

**Axiom S (Symmetry).** If players $i$ and $j$ are **symmetric** in $v$, meaning $v(S \cup \{i\}) = v(S \cup \{j\})$ for all $S \subseteq N \setminus \{i, j\}$, then $\phi_i(v) = \phi_j(v)$. Players who make identical contributions to every coalition receive equal shares.

**Axiom D (Dummy Player).** Player $i$ is a **dummy** if $v(S \cup \{i\}) = v(S)$ for all $S \subseteq N \setminus \{i\}$. If $i$ is a dummy, then $\phi_i(v) = 0$. Players who contribute nothing receive nothing.

**Axiom A (Additivity).** For any two games $v$ and $w$ on the same player set, $\phi(v + w) = \phi(v) + \phi(w)$, where $(v+w)(S) = v(S) + w(S)$.

**Theorem (Shapley 1953).** There exists a unique value function satisfying axioms E, S, D, and A. It is given by the **Shapley value**:

$$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!\,(n - |S| - 1)!}{n!} \left[ v(S \cup \{i\}) - v(S) \right].$$

**Proof of uniqueness and existence.** The proof employs the basis representation strategy. For each coalition $T \subseteq N$ with $T \neq \emptyset$, define the **unanimity game** $u_T : 2^N \to \mathbb{R}$ by

$$u_T(S) = \begin{cases} 1 & \text{if } T \subseteq S, \\ 0 & \text{otherwise.} \end{cases}$$

The unanimity games form a basis for the vector space $\Gamma^n$ (which has dimension $2^n - 1$ over $\mathbb{R}$). That is, every game $v$ can be written uniquely as

$$v = \sum_{\emptyset \neq T \subseteq N} c_T(v) \cdot u_T,$$

where the coefficients $c_T(v)$ are the **Harsanyi dividends**, given by the Möbius inversion formula:

$$c_T(v) = \sum_{S \subseteq T} (-1)^{|T| - |S|} v(S).$$

This representation is unique by the invertibility of the Möbius function on the Boolean lattice $2^N$. Now, by Axiom A, $\phi(v) = \sum_T c_T(v) \cdot \phi(u_T)$, so the value is fully determined by its behavior on unanimity games. For the unanimity game $u_T$, every player in $T$ is symmetric by Axiom S (since the game's value depends only on whether $T \subseteq S$, all members of $T$ play identical roles), and every player $i \notin T$ is a dummy by Axiom D (since adding $i$ to any $S$ not already containing $T$ cannot create $T \subseteq S \cup \{i\}$ unless $T \setminus \{i\} \subseteq S$, but $i \notin T$, so $v(S \cup \{i\}) = v(S)$ for all $S$). Therefore, by Axiom D, $\phi_i(u_T) = 0$ for all $i \notin T$, and by Axiom S, all players in $T$ receive the same amount. By Axiom E, the total must equal $u_T(N) = 1$, so each player in $T$ receives $1/|T|$. Thus,

$$\phi_i(u_T) = \begin{cases} 1/|T| & \text{if } i \in T, \\ 0 & \text{if } i \notin T. \end{cases}$$

This determines $\phi$ uniquely on all unanimity games, and by Axiom A, on all games. Existence is verified by confirming the formula satisfies all four axioms.

To arrive at the closed-form expression, substitute $\phi_i(u_T) = \mathbf{1}[i \in T] / |T|$ into the basis expansion:

$$\phi_i(v) = \sum_{T \ni i} \frac{c_T(v)}{|T|} = \sum_{T \ni i} \frac{1}{|T|} \sum_{S \subseteq T} (-1)^{|T|-|S|} v(S).$$

Rearranging by substituting $S = T \setminus \{i\} \cup R$ for subsets $R \subseteq S \setminus \{i\}$ and collecting terms by the size of $S$ yields the standard formula. The coefficient of $v(S)$ for a coalition $S$ not containing $i$ is

$$\sum_{T : S \subseteq T, i \in T} \frac{(-1)^{|T|-|S|}}{|T|},$$

which after combinatorial simplification (summing over $T$ of size $|S| + k + 1$ for $k = 0, 1, \ldots, n - |S| - 1$) evaluates to $|S|!(n-|S|-1)!/n!$. The coefficient of $v(S \cup \{i\})$ is the negative of the coefficient for $v(S)$ with $i$ absorbed, yielding the marginal contribution form $v(S \cup \{i\}) - v(S)$ weighted by $|S|!(n-|S|-1)!/n!$, as stated.

### The Permutation Interpretation

The Shapley value formula admits a probabilistic interpretation that is both computationally transparent and conceptually illuminating. Consider all $n!$ orderings (permutations) of the player set $N$. For a uniformly random permutation $\sigma$, define the **set of predecessors** of player $i$ as $P_i(\sigma) = \{j \in N : \sigma^{-1}(j) < \sigma^{-1}(i)\}$, that is, the set of players who arrive before $i$ in the ordering $\sigma$. The Shapley value is the expected marginal contribution of player $i$ over all $n!$ equally likely orderings:

$$\phi_i(v) = \frac{1}{n!} \sum_{\sigma \in \Pi(N)} \left[ v(P_i(\sigma) \cup \{i\}) - v(P_i(\sigma)) \right].$$

This representation makes all four axioms transparent: efficiency holds because the sum of marginal contributions over all players in any single permutation telescopes to $v(N) - v(\emptyset) = v(N)$; symmetry holds because if $i$ and $j$ are symmetric, then swapping their positions in every permutation maps the expectation for $i$ to the expectation for $j$; dummy players have zero marginal contribution in every ordering; and additivity holds because expectation is linear. The permutation interpretation also establishes the formula as a Monte Carlo computable quantity: for large $n$, one samples permutations uniformly at random and averages observed marginal contributions.

### Shapley Value Computation for Example 1

We compute $\phi(v)$ for the three-player production game exactly. With $n = 3$, there are $3! = 6$ permutations. The marginal contribution table is:

For each of the six orderings $\sigma$ of $\{1, 2, 3\}$, we record $(P_1(\sigma), P_2(\sigma), P_3(\sigma))$ and the resulting marginal contributions $m_i(\sigma) = v(P_i(\sigma) \cup \{i\}) - v(P_i(\sigma))$.

**Ordering (1, 2, 3):** Player 1 arrives first to the empty coalition: $m_1 = v(\{1\}) - v(\emptyset) = 0$. Player 2 joins player 1: $m_2 = v(\{1,2\}) - v(\{1\}) = 40$. Player 3 joins both: $m_3 = v(\{1,2,3\}) - v(\{1,2\}) = 60$.

**Ordering (1, 3, 2):** $m_1 = 0$, $m_3 = v(\{1,3\}) - v(\{1\}) = 50$, $m_2 = v(\{1,2,3\}) - v(\{1,3\}) = 50$.

**Ordering (2, 1, 3):** $m_2 = v(\{2\}) - v(\emptyset) = 0$, $m_1 = v(\{1,2\}) - v(\{2\}) = 40$, $m_3 = v(\{1,2,3\}) - v(\{1,2\}) = 60$.

**Ordering (2, 3, 1):** $m_2 = 0$, $m_3 = v(\{2,3\}) - v(\{2\}) = 30$, $m_1 = v(\{1,2,3\}) - v(\{2,3\}) = 70$.

**Ordering (3, 1, 2):** $m_3 = v(\{3\}) = 0$, $m_1 = v(\{1,3\}) - v(\{3\}) = 50$, $m_2 = v(\{1,2,3\}) - v(\{1,3\}) = 50$.

**Ordering (3, 2, 1):** $m_3 = 0$, $m_2 = v(\{2,3\}) - v(\{3\}) = 30$, $m_1 = v(\{1,2,3\}) - v(\{2,3\}) = 70$.

Summing and dividing by 6:

$$\phi_1(v) = \frac{0 + 0 + 40 + 70 + 50 + 70}{6} = \frac{230}{6} \approx 38.33,$$

$$\phi_2(v) = \frac{40 + 50 + 0 + 0 + 50 + 30}{6} = \frac{170}{6} \approx 28.33,$$

$$\phi_3(v) = \frac{60 + 50 + 60 + 30 + 0 + 0}{6} = \frac{200}{6} \approx 33.33.$$

Verification: $\phi_1 + \phi_2 + \phi_3 = 230/6 + 170/6 + 200/6 = 600/6 = 100 = v(N)$. Efficiency holds.

We confirm that the Shapley value lies in the core: $\phi_1 + \phi_2 = 230/6 + 170/6 = 400/6 \approx 66.67 \geq 40$; $\phi_1 + \phi_3 = 430/6 \approx 71.67 \geq 50$; $\phi_2 + \phi_3 = 370/6 \approx 61.67 \geq 30$. The Shapley value is in the core for this game, as expected for convex games (the production game is convex, as direct verification of the supermodularity inequality confirms).

### The Nash Bargaining Solution

The cooperative bargaining framework specializes the problem to two players facing a **feasible set** $F \subseteq \mathbb{R}^2$ of jointly achievable utility pairs and a **disagreement point** $d = (d_1, d_2) \in F$ representing the payoffs if no agreement is reached. The feasible set is assumed to be convex, compact, and comprehensive (if $(u_1, u_2) \in F$ and $(w_1, w_2) \leq (u_1, u_2)$ componentwise, then $(w_1, w_2) \in F$), with at least one point strictly dominating $d$.

Nash (1950) characterized a unique bargaining solution through four axioms: Pareto optimality (no feasible point weakly dominates the solution), symmetry (if the problem is symmetric, the solution divides equally), invariance to affine transformations of utility, and independence of irrelevant alternatives (if the feasible set shrinks but the original solution remains feasible, it stays optimal).

**Nash Bargaining Solution.** The unique solution satisfying Nash's axioms is the point $(u_1^*, u_2^*)$ in $F$ that maximizes the **Nash product**:

$$\max_{(u_1, u_2) \in F} (u_1 - d_1)(u_2 - d_2).$$

The proof of existence and uniqueness is a classical constrained optimization argument. Because $F$ is compact and the Nash product is continuous, a maximum exists. Because $F$ is convex and the Nash product is strictly quasiconcave on the region where both factors are positive, the maximum is unique. The first-order conditions at an interior optimum yield the tangency condition

$$\frac{u_2^* - d_2}{u_1^* - d_1} = -\frac{\partial F}{\partial u_1}\bigg|_{(u_1^*, u_2^*)},$$

that is, the slope of the Pareto frontier at the solution equals the negative ratio of the two bargaining surpluses.

**Example 2: Nash Bargaining.** Let $F = \{(u_1, u_2) : u_1 + u_2 \leq 10, u_1, u_2 \geq 0\}$ and $d = (1, 2)$. We maximize $(u_1 - 1)(u_2 - 2)$ subject to $u_1 + u_2 = 10$ (the Pareto frontier). Substituting $u_2 = 10 - u_1$:

$$\max_{u_1} (u_1 - 1)(8 - u_1).$$

Differentiating: $(8 - u_1) - (u_1 - 1) = 9 - 2u_1 = 0 \implies u_1^* = 4.5$ and $u_2^* = 5.5$. The Nash product at this point is $(3.5)(3.5) = 12.25$.

### The Kalai-Smorodinsky Solution

A well-known objection to the Nash solution is its failure of **monotonicity**: expanding the feasible set in a direction that benefits only player 2 can actually reduce player 2's Nash solution payoff, because the geometric maximizer of the Nash product shifts. Kalai and Smorodinsky (1975) proposed an alternative satisfying a monotonicity axiom that Nash's solution fails.

For a bargaining problem $(F, d)$, define the **utopia point** $a = (a_1, a_2)$ where $a_i = \max\{u_i : (u_1, u_2) \in F, u_j \geq d_j \text{ for all } j\}$ is player $i$'s maximum achievable utility subject to the other player receiving at least their disagreement payoff. The Kalai-Smorodinsky solution is the unique Pareto-optimal point in $F$ on the line segment connecting $d$ to $a$:

$$\text{KS}(F, d) = \max \left\{ \lambda \cdot a + (1 - \lambda) \cdot d : \lambda \in [0,1],\; \lambda a + (1-\lambda)d \in F \right\}.$$

Equivalently, it is the Pareto-optimal point $(u_1^*, u_2^*)$ satisfying

$$\frac{u_1^* - d_1}{a_1 - d_1} = \frac{u_2^* - d_2}{a_2 - d_2},$$

meaning both players achieve the same fraction of their individually ideal surplus. The axioms characterizing the KS solution replace Nash's independence of irrelevant alternatives with **individual monotonicity**: if the feasible set expands in a way that enlarges player $i$'s maximum attainable utility without changing player $j$'s, then player $i$'s payoff should not decrease.

**Example 2 continued.** With $F$ as above and $d = (1, 2)$, the utopia point has $a_1 = \max\{u_1 : u_1 + u_2 \leq 10, u_2 \geq 2\} = 8$ and $a_2 = \max\{u_2 : u_1 + u_2 \leq 10, u_1 \geq 1\} = 9$. The KS condition demands

$$\frac{u_1^* - 1}{8 - 1} = \frac{u_2^* - 2}{9 - 2} \implies \frac{u_1^* - 1}{7} = \frac{u_2^* - 2}{7} \implies u_1^* - 1 = u_2^* - 2 \implies u_2^* = u_1^* + 1.$$

Combined with $u_1^* + u_2^* = 10$: $2u_1^* + 1 = 10$, so $u_1^* = 4.5$ and $u_2^* = 5.5$. For this symmetric case, both solutions coincide, as expected by symmetry. For an asymmetric feasible set, the two solutions diverge.

---

## 3. High-Performance Optimization & Failure Modes

### Computational Complexity and the Shapley Value

The straightforward computation of the Shapley value via the permutation formula requires summing $n!$ terms, which is feasible only for $n \leq 15$ in practice. This exponential complexity is not merely an artifact of the formula. Castro, Gómez, and Tejada (2009) showed that exact Shapley value computation for general characteristic function games is \#P-hard (meaning it is at least as hard as any problem in the counting complexity class \#P), ruling out polynomial-time exact algorithms under standard complexity assumptions.

Three algorithmic strategies address this in practice. The first is **direct marginal contribution enumeration** via the formula $\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(n-|S|-1)!}{n!} [v(S \cup \{i\}) - v(S)]$, which requires evaluating $2^{n-1}$ coalition values per player for a total of $n \cdot 2^{n-1}$ evaluations. This is exponential but preferable to $n!$ for $n \geq 20$, since $n \cdot 2^{n-1}$ grows slower. For $n = 25$, this is roughly $4 \times 10^8$ evaluations, tractable with efficient bit-manipulation indexing of coalitions as integers.

The second strategy is **stratified Monte Carlo sampling**. Rather than computing the expectation over all $n!$ permutations exactly, one samples $m$ permutations uniformly at random and estimates

$$\hat{\phi}_i(v) = \frac{1}{m} \sum_{k=1}^m \left[ v(P_i(\sigma^{(k)}) \cup \{i\}) - v(P_i(\sigma^{(k)})) \right].$$

By the central limit theorem, the estimation error is $O(m^{-1/2})$ with high probability, independent of $n$. With $m = 10^4$ samples and $n = 100$ players, the computation requires $100 \times 10^4 = 10^6$ coalition evaluations, far more tractable than exact methods.

The third strategy exploits **structural decompositions**. For weighted voting games $v(S) = \mathbf{1}[\sum_{i \in S} w_i \geq q]$, dynamic programming on the weight sum allows coalition values to be computed in $O(nq)$ time, and Shapley values can be derived from the DP table in $O(n^2 q)$ time. For graph-based games where $v(S)$ depends only on the subgraph induced by $S$, tree decomposition algorithms compute Shapley values in time exponential only in the treewidth of the graph, which is small for sparse networks.

### Core Failure Modes and Stability Recovery

The core's most consequential failure mode is emptiness. When the balancedness condition of the Bondareva-Shapley theorem is violated, no stable allocation exists in the core sense: every proposed distribution can be blocked by some coalition. Three responses are standard in the literature.

The first response is to **relax the solution concept**. The $\varepsilon$-core or strong $\varepsilon$-core allows coalition $S$ to block only if it can improve by more than $\varepsilon$:

$$C_\varepsilon(N,v) = \left\{ x \in \mathbb{R}^n : \sum_{i \in N} x_i = v(N),\; \sum_{i \in S} x_i \geq v(S) - \varepsilon \text{ for all } S \right\}.$$

The least $\varepsilon$ for which the $\varepsilon$-core is nonempty is the **nucleolus** parameter, and the unique imputation at that point is the **nucleolus**, introduced by Schmeidler (1969). The nucleolus is always defined (it lies in the imputation set for superadditive games), satisfies coalitional rationality as far as possible, and lies in the core whenever the core is nonempty.

The second response is to adopt the **Shapley value** as a normative solution even when the core is empty. The Shapley value is always uniquely defined, satisfies efficiency, and has the axiomatic foundation described above. It represents each player's expected marginal contribution and can be justified on fairness grounds independently of stability considerations.

The third response is to **redesign the game structure**. If the characteristic function arises from an underlying strategic game or mechanism, the designer can sometimes modify the allocation rule or communication structure to restore convexity, which guarantees a nonempty core. In network cost-sharing games, for instance, requiring that costs be allocated proportionally to the minimum spanning tree edges used by each coalition converts an empty-core problem into a convex game, as shown by Granot and Huberman (1984).

### Edge Cases in Bargaining Solutions

The Nash bargaining solution fails when the feasible set $F$ is not strictly convex along the Pareto frontier. If the Pareto frontier contains a flat segment, the Nash product maximizer is not unique, and the solution set is an interval rather than a point. Regularization methods include using lexicographic Nash products or perturbing the feasible set.

The Kalai-Smorodinsky solution fails to generalize cleanly beyond two players. The utopia point $a$ is well-defined for any number of players, but the line segment from $d$ to $a$ may not intersect the Pareto frontier of the $n$-player feasible set at a unique point. This is the reason the KS solution remains primarily a two-player construct, while the Nash generalization to $n$ players (as the maximizer of $\prod_i (u_i - d_i)$) extends naturally and retains uniqueness under strict convexity.

A deeper issue arises in the comparison of the two bargaining solutions under changes in the feasible set. Consider a problem where expanding $F$ to $F' \supset F$ increases $a_1$ (the utopia payoff of player 1) without changing $a_2$. The KS solution gives player 1 a higher payoff in $F'$, satisfying individual monotonicity. The Nash solution, by contrast, shifts its maximizer in a direction determined purely by the geometry of the Pareto frontier of $F'$, which may actually reduce player 1's payoff. This failure of monotonicity in the Nash solution is not pathological: it reflects the fact that the Nash product weighs the two players' surpluses multiplicatively, so a larger feasible set for player 1 may induce a steeper Pareto frontier that the Nash product trades off against player 1. The choice between the two solutions therefore carries real normative weight: Nash embeds a particular notion of bargaining efficiency, while KS embeds a notion of proportional fairness.

### Connecting the Shapley Value to the Core: The Convex Case

For the class of convex games, the Shapley value is not merely a normative allocation; it occupies a distinguished geometric position inside the core. Shapley (1971) proved that for convex games, the Shapley value is the centroid of the core, that is, the average of the extreme points (vertices) of the core polytope. This result is striking because the core can have up to $n!$ vertices (one for each ordering, corresponding to the marginal contribution vectors), and the Shapley value is their average. This gives the Shapley value an additional stability justification in convex games: it is the most central stable allocation.

The marginal contribution vector for a permutation $\sigma$, defined by $m_i^\sigma = v(P_i(\sigma) \cup \{i\}) - v(P_i(\sigma))$, is always in the core for convex games. This follows directly from supermodularity: for any coalition $S$ and ordering $\sigma$, the sum $\sum_{i \in S} m_i^\sigma \geq v(S)$ because convexity ensures that the marginal contributions of players in $S$, evaluated with respect to the predecessors determined by $\sigma$, cannot collectively undervalue $S$. The formal proof proceeds by induction on $|S|$: for a single player $\{j\}$, $m_j^\sigma \geq v(\{j\})$ because $m_j^\sigma = v(P_j(\sigma) \cup \{j\}) - v(P_j(\sigma)) \geq v(\{j\}) - v(\emptyset) = v(\{j\})$ by convexity (taking $T = P_j(\sigma)$, $S = \emptyset$ in the supermodularity inequality). Extending this inductively to all $S$ completes the argument.

Combining: the Shapley value $\phi(v) = (1/n!) \sum_\sigma m^\sigma$ is the average of $n!$ points all lying in the core $C(N, v)$. Since the core is convex, the average is also in the core. For convex games, therefore, the Shapley value is simultaneously axiomatically unique, geometrically central, and strategically stable. These three properties, rarely coinciding in solution theory, make convex cooperative games the canonical setting in which the full architecture of cooperative game theory is simultaneously coherent and applicable.
