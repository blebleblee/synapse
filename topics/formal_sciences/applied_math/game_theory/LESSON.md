# In-Depth Technical Lesson: Nash Equilibria, Dynamic Subgame Perfection & Mechanism Design

## 1. Normal-Form Games & Mixed Strategy Nash Equilibrium

### Mathematical Formalization
A normal-form game is formally defined as an ordered triple:

$$G = \langle N, (S_i)_{i \in N}, (u_i)_{i \in N} \rangle$$

* $N = \{1, 2, \dots, n\}$ is the finite set of players.
* $S_i = \{s_{i1}, s_{i2}, \dots, s_{im_i}\}$ is the finite pure strategy space of player $i$.
* $S = \prod_{i=1}^n S_i$ is the Cartesian product space of pure strategy profiles.
* $u_i: S \to \mathbb{R}$ is the von Neumann-Morgenstern utility (payoff) function of player $i$.

A **mixed strategy** for player $i$ is a probability measure $\sigma_i \in \Delta(S_i)$ on the simplex:

$$\Delta(S_i) = \left\{ \sigma_i \in \mathbb{R}^{|S_i|} \;\middle|\; \sum_{s_i \in S_i} \sigma_i(s_i) = 1 \quad \text{and} \quad \sigma_i(s_i) \ge 0 \; \forall s_i \in S_i \right\}$$

The expected payoff of player $i$ under mixed strategy profile $\sigma = (\sigma_1, \dots, \sigma_n) \in \Sigma = \prod_{i=1}^n \Delta(S_i)$ is:

$$U_i(\sigma) = \sum_{s \in S} \left( \prod_{j \in N} \sigma_j(s_j) \right) u_i(s)$$

### Definition of Nash Equilibrium
A strategy profile $\sigma^* = (\sigma_1^*, \dots, \sigma_n^*) \in \Sigma$ is a **Nash Equilibrium** if and only if for every player $i \in N$:

$$U_i(\sigma_i^*, \sigma_{-i}^*) \ge U_i(\sigma_i, \sigma_{-i}^*) \quad \forall \sigma_i \in \Delta(S_i)$$

Where $\sigma_{-i}^* = (\sigma_1^*, \dots, \sigma_{i-1}^*, \sigma_{i+1}^*, \dots, \sigma_n^*)$.

### The Indifference Principle of Mixed Equilibria
If $\sigma^*$ is a mixed strategy Nash equilibrium and $\sigma_i^*(s_i) > 0$ for multiple pure strategies $s_i \in \text{supp}(\sigma_i^*)$, then player $i$ must receive **identical expected utility** across every pure strategy in their support:

$$U_i(s_i, \sigma_{-i}^*) = U_i(s_i', \sigma_{-i}^*) = U_i(\sigma_i^*, \sigma_{-i}^*) \quad \forall s_i, s_i' \in \text{supp}(\sigma_i^*)$$

Furthermore, for any pure strategy outside the support ($s_k \notin \text{supp}(\sigma_i^*)$):

$$U_i(s_k, \sigma_{-i}^*) \le U_i(\sigma_i^*, \sigma_{-i}^*)$$

---

## 2. Proof of Nash's Existence Theorem via Kakutani's Fixed Point Theorem

**Theorem (John Nash, 1950):** *Every finite normal-form game possesses at least one mixed strategy Nash equilibrium.*

```
Topological Mapping in Nash's Proof
===================================

     Strategy Space \Sigma = \prod \Delta(S_i)
        (Compact, Convex Subset of \mathbb{R}^M)
                      |
                      v
     Best Response Mapping: BR: \Sigma \rightrightarrows \Sigma
        BR(\sigma) = \prod_{i=1}^n \arg\max_{\sigma_i'} U_i(\sigma_i', \sigma_{-i})
                      |
      Kakutani's Conditions:
        1. \Sigma is compact, convex, non-empty.
        2. BR(\sigma) is non-empty for all \sigma (Weierstrass Extreme Value Theorem).
        3. BR(\sigma) is convex-valued (Linearity of expectation).
        4. BR has a closed graph (Berge's Maximum Theorem).
                      |
                      v
      \exists \sigma^* \in BR(\sigma^*)  ===>  NASH EQUILIBRIUM
```

### Formal Proof Walkthrough
1. **Compactness and Convexity:** Each probability simplex $\Delta(S_i)$ is closed, bounded, and convex. The strategy profile space $\Sigma = \prod_{i=1}^n \Delta(S_i)$ is a product of compact, convex sets, and is therefore non-empty, compact, and convex in $\mathbb{R}^{\sum |S_i|}$.
2. **Best Response Correspondence:** Define the set-valued correspondence $BR_i: \Sigma \rightrightarrows \Delta(S_i)$:
   $$BR_i(\sigma_{-i}) = \left\{ \sigma_i \in \Delta(S_i) \;\middle|\; U_i(\sigma_i, \sigma_{-i}) = \max_{\sigma_i' \in \Delta(S_i)} U_i(\sigma_i', \sigma_{-i}) \right\}$$
   Define the product correspondence $BR: \Sigma \rightrightarrows \Sigma$ as $BR(\sigma) = \prod_{i \in N} BR_i(\sigma_{-i})$.
3. **Non-Emptiness:** Because $U_i$ is continuous and $\Delta(S_i)$ is compact, the Weierstrass Extreme Value Theorem guarantees that $BR_i(\sigma_{-i})$ is non-empty for all $\sigma$.
4. **Convexity of Images:** $U_i(\sigma_i, \sigma_{-i})$ is multilinear—strictly linear in $\sigma_i$. If $\sigma_i', \sigma_i'' \in BR_i(\sigma_{-i})$, then for any $\alpha \in [0, 1]$:
   $$U_i(\alpha \sigma_i' + (1 - \alpha)\sigma_i'', \sigma_{-i}) = \alpha U_i(\sigma_i', \sigma_{-i}) + (1 - \alpha)U_i(\sigma_i'', \sigma_{-i}) = \max U_i$$
   Therefore, $BR(\sigma)$ is convex-valued for all $\sigma \in \Sigma$.
5. **Closed Graph Property:** By Berge's Maximum Theorem, since the objective function $U_i$ is continuous, the argmax correspondence $BR_i$ is upper hemicontinuous with closed values, meaning its graph $\text{Gr}(BR) = \{(\sigma, \sigma') \mid \sigma' \in BR(\sigma)\}$ is closed.
6. **Fixed Point Application:** By **Kakutani's Fixed Point Theorem**, there exists a point $\sigma^* \in \Sigma$ such that:
   $$\sigma^* \in BR(\sigma^*)$$
   By definition, $\sigma_i^* \in BR_i(\sigma_{-i}^*)$ for every player $i \in N$. Hence, $\sigma^*$ is a Nash Equilibrium. $\blacksquare$

---

## 3. Dynamic Games: Extensive Form, Backward Induction & Subgame Perfection

A game in strategic form masks temporal ordering. Dynamic games are represented in **Extensive Form** via a game tree:

$$\Gamma = \langle N, X, \prec, P, (H_i)_{i \in N}, A, (u_i)_{i \in N} \rangle$$

* $X$ is the set of game nodes; $\prec$ is the strict partial order of precedence.
* $P: X \setminus Z \to N \cup \{0\}$ identifies the acting player at non-terminal node $x$ ($0$ denotes Chance).
* $H_i$ is the partition of player $i$'s decision nodes into **Information Sets**. An information set $h \in H_i$ contains nodes that player $i$ cannot distinguish at the time of choice.

```
Subgame Perfection vs. Non-Credible Threat
==========================================

                      Firm 1 (Incumbent)
                         /          \
                        /            \
                Accommodate         Fight (Price War)
                   (2, 2)              (-1, -1)
                    ^                     ^
                    |                     |
          [Subgame Perfect]     [Non-Credible Threat]
                    \                     /
                     \                   /
                     Firm 2: Enter Market
```

### Zermelo's Theorem (1913) & Backward Induction
In any finite extensive-form game of **perfect information** (every information set is a singleton), there exists a pure strategy Nash equilibrium that can be computed by **Backward Induction**:
1. Identify all terminal decision nodes whose children are all leaf payoffs.
2. Determine the optimal action for the acting player at each node.
3. Replace those decision nodes with the resulting payoff vectors.
4. Recurse backward to the root of the tree.

### Subgame Perfect Nash Equilibrium (SPNE)
A strategy profile $\sigma^*$ is a **Subgame Perfect Nash Equilibrium (Selten, 1965)** if it induces a Nash equilibrium in **every subgame** of the extensive-form game, including subgames that are off the equilibrium path.

**The One-Shot Deviation Principle:** In a finite-horizon game, a strategy profile $\sigma^*$ is an SPNE if and only if no player $i$ can increase their expected payoff by deviating from $\sigma_i^*$ at a single information set $h \in H_i$ while keeping all subsequent actions fixed to $\sigma_i^*$.

---

## 4. Repeated Games & The Folk Theorem

Consider a stage game $G$ repeated across infinite discrete time periods $t \in \{0, 1, 2, \dots\}$ with discount factor $\delta \in (0, 1)$.
The normalized present discounted value of player $i$'s payoff sequence $(u_i^t)_{t=0}^\infty$ is:

$$V_i = (1 - \delta) \sum_{t=0}^\infty \delta^t u_i^t$$

### Minimax Payoff (The Reservation Threat)
The lowest payoff that player $i$'s opponents can force player $i$ to receive is their **minimax payoff**:

$$\underline{v}_i = \min_{\sigma_{-i} \in \Sigma_{-i}} \max_{s_i \in S_i} u_i(s_i, \sigma_{-i})$$

A payoff vector $v = (v_1, \dots, v_n)$ is **strictly individually rational** if $v_i > \underline{v}_i$ for all $i \in N$.

### Friedman's Folk Theorem (1971)
Let $e$ be a static Nash equilibrium of stage game $G$ yielding payoffs $u(e)$. Let $v$ be any feasible payoff vector such that $v_i > u_i(e)$ for all $i \in N$.
Then there exists a critical threshold $\underline{\delta} < 1$ such that for all $\delta \in (\underline{\delta}, 1)$, there exists a Subgame Perfect Nash Equilibrium sustaining payoff $v$.

```
Grim Trigger Mechanism
======================
Period 0: Play cooperative action profile s* yielding v_i.
Period t: 
  If all players played s* in all prior periods:
    Play s*.
  Else (if any deviation occurred in history):
    Play static Nash equilibrium e forever (Permanent Punishment).
```

For cooperation to hold under Grim Trigger, the discounted reward from continued cooperation must exceed the one-shot deviation temptation:

$$\frac{u_i(s^*)}{1 - \delta} \ge u_i(s_i^{\text{dev}}, s_{-i}^*) + \frac{\delta \cdot u_i(e)}{1 - \delta} \iff \delta \ge \frac{u_i(s_i^{\text{dev}}, s_{-i}^*) - u_i(s^*)}{u_i(s_i^{\text{dev}}, s_{-i}^*) - u_i(e)}$$

---

## 5. Mechanism Design & The Revelation Principle

Mechanism design is **reverse game theory**: rather than analyzing the equilibrium of a given game, the designer seeks to engineer an extensive game (a mechanism) whose equilibrium implements a desired **Social Choice Function** $f: \Theta \to X$.

* $\Theta = \Theta_1 \times \dots \times \Theta_n$: Space of private player types (e.g., private valuations).
* $X$: Space of outcomes (allocations and payments).

### The Revelation Principle
**Theorem:** *If an arbitrary mechanism $\Gamma = \langle (M_i)_{i \in N}, g \rangle$ implements a social choice function $f$ in dominant strategies (or Bayesian Nash equilibrium), then there exists a direct revelation mechanism where players report their types directly ($M_i = \Theta_i$) that truthfully implements $f$ in dominant strategies:*

$$u_i(f(\theta_i, \theta_{-i}), \theta_i) \ge u_i(f(\hat{\theta}_i, \theta_{-i}), \theta_i) \quad \forall \theta_i, \hat{\theta}_i \in \Theta_i, \quad \forall \theta_{-i} \in \Theta_{-i}$$

### The Vickrey-Clarke-Groves (VCG) Mechanism
In quasilinear environments with outcome $k \in K$ and monetary transfers $t_i \in \mathbb{R}$:

$$u_i(k, t_i, \theta_i) = v_i(k, \theta_i) + t_i$$

A VCG mechanism chooses the efficient allocation $k^*(\hat{\theta}) = \arg\max_{k \in K} \sum_{j \in N} v_j(k, \hat{\theta}_j)$ and imposes the transfer:

$$t_i(\hat{\theta}) = \sum_{j \ne i} v_j(k^*(\hat{\theta}), \hat{\theta}_j) - h_i(\hat{\theta}_{-i})$$

Where $h_i(\hat{\theta}_{-i})$ is an arbitrary function independent of bidder $i$'s report (typically chosen as Clarke's pivot rule: $\max_{k \in K} \sum_{j \ne i} v_j(k, \hat{\theta}_j)$).
**Result:** Under VCG, truth-telling ($\hat{\theta}_i = \theta_i$) is a **weakly dominant strategy** for every participant.

---

## 6. Cooperative Game Theory & The Shapley Value

In cooperative (coalitional) games, binding contracts are enforceable.
A cooperative game with transferable utility is defined as $(N, v)$, where:
* $N = \{1, \dots, n\}$ is the grand coalition of players.
* $v: 2^N \to \mathbb{R}$ is the characteristic function with $v(\emptyset) = 0$, representing the total surplus generated by coalition $S \subseteq N$.

### The Shapley Value Axioms (Lloyd Shapley, 1953)
There is a unique value allocation $\phi(v) = (\phi_1(v), \dots, \phi_n(v))$ satisfying four fundamental fairness axioms:
1. **Efficiency:** $\sum_{i \in N} \phi_i(v) = v(N)$.
2. **Symmetry:** If $v(S \cup \{i\}) = v(S \cup \{j\})$ for all $S \subseteq N \setminus \{i, j\}$, then $\phi_i(v) = \phi_j(v)$.
3. **Dummy Player:** If $v(S \cup \{i\}) = v(S)$ for all $S \subseteq N \setminus \{i\}$, then $\phi_i(v) = 0$.
4. **Additivity:** For two distinct games $(N, v)$ and $(N, w)$, $\phi_i(v + w) = \phi_i(v) + \phi_i(w)$.

### The Explicit Shapley Value Formula
$$\phi_i(v) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N| - |S| - 1)!}{|N|!} \left[ v(S \cup \{i\}) - v(S) \right]$$

The weight represents the probability that player $i$ enters a randomly ordered coalition sequence and finds exactly the subset $S$ already present, capturing player $i$'s expected marginal contribution across all $|N|!$ permutations.

---

## 7. Key Takeaways

1. **Equilibrium is Strategic Stability:** A Nash equilibrium does not imply social efficiency; it establishes mutual best-response invariance.
2. **Topological Existence:** Nash's existence theorem is a direct consequence of Kakutani's Fixed Point Theorem applied to the compact, convex mixed-strategy simplex.
3. **Dynamic Refinement:** Subgame perfection eliminates non-credible off-equilibrium threats via backward induction.
4. **Cooperation via Shadow of the Future:** The Folk Theorem proves that repeated interaction can transform competitive prisoner's dilemmas into cooperative equilibria.
5. **Truth as Dominant Strategy:** Mechanism design and VCG transfers align individual private incentives with global Pareto-optimal social choice.
