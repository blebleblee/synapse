# Foundation: Strategic Game Theory & Interactive Decision Systems

## 1. Conceptual Mental Model

### Beyond Individual Optimization
Classical decision theory and microeconomic consumer theory operate on **parametric optimization**: an individual decision-maker faces an inanimate environment (e.g., maximizing utility subject to a budget constraint, or minimizing risk against fixed probability distributions). In parametric optimization, nature does not react to your choices.

**Game Theory is the mathematical foundation of Strategic Interaction.**
In a strategic setting, your payoff depends not only on your choice, but on the simultaneous or sequential choices of other autonomous, rational agents who are actively anticipating your behavior.

$$\text{Optimization: } \max_{x \in X} f(x) \quad \longleftrightarrow \quad \text{Game Theory: } \max_{s_i \in S_i} u_i(s_i, s_{-i})$$

Where $s_i$ is player $i$'s strategy, and $s_{-i}$ represents the strategy vector chosen by all other players in the system.

```
The Strategic Feedback Cycle
============================

      +-------------------------------------------+
      | Player 1 chooses strategy s_1 \in S_1     |
      |   Anticipates Player 2's best response    |
      +-------------------------------------------+
                         |       ^
            Payoff u_1   |       |   Payoff u_2
          Interdependent |       | Interdependent
                         v       |
      +-------------------------------------------+
      | Player 2 chooses strategy s_2 \in S_2     |
      |   Anticipates Player 1's best response    |
      +-------------------------------------------+
```

A **Nash Equilibrium** represents a state of strategic rest. No player possesses a unilateral incentive to deviate from their chosen strategy given the strategies currently chosen by everyone else:

$$u_i(s_i^*, s_{-i}^*) \ge u_i(s_i, s_{-i}^*) \quad \forall s_i \in S_i, \quad \forall i \in N$$

---

## 2. Essential Terminology & Taxonomy

| Concept | Formal Mathematical Definition |
| :--- | :--- |
| **Normal (Strategic) Form Game** | A tuple $G = \langle N, (S_i)_{i \in N}, (u_i)_{i \in N} \rangle$ where $N = \{1, 2, \dots, n\}$ is the set of players, $S_i$ is the strategy set for player $i$, and $u_i: \prod_{j \in N} S_j \to \mathbb{R}$ is the payoff function. |
| **Strict / Weak Dominance** | Strategy $s_i'$ strictly dominates $s_i''$ if $u_i(s_i', s_{-i}) > u_i(s_i'', s_{-i})$ for all $s_{-i} \in S_{-i}$. Rational players will never play strictly dominated strategies. |
| **Best-Response Correspondence** | The set-valued mapping $BR_i(s_{-i}) = \arg\max_{s_i \in S_i} u_i(s_i, s_{-i})$. An equilibrium occurs at the intersection of all players' best-response correspondences. |
| **Mixed Strategy ($\sigma_i$)** | A probability distribution over pure strategies: $\sigma_i \in \Delta(S_i)$ where $\sum_{s_i \in S_i} \sigma_i(s_i) = 1$ and $\sigma_i(s_i) \ge 0$. |
| **Extensive Form Game** | A game modeled as a directed tree $T$ containing decision nodes, action edges, information sets, chance moves, and terminal payoff vectors. |
| **Information Set ($I_k$)** | A collection of decision nodes for player $i$ such that player $i$ cannot distinguish which specific node in the set has been reached. Represents imperfect information. |
| **Subgame Perfect Equilibrium (SPNE)** | A strategy profile that induces a Nash equilibrium in **every subgame** of an extensive-form game, eliminating non-credible threats. |
| **Pareto Optimality** | An outcome $(s_1, \dots, s_n)$ such that no player can be made strictly better off without making at least one other player strictly worse off. |

---

## 3. The Classic Canonical Matrix Games

### 1. The Prisoner's Dilemma (Defection Dominance vs. Social Optimality)

Two suspects are arrested and interrogated in separate rooms.

| | Player 2: Cooperate ($C$) | Player 2: Defect ($D$) |
| :--- | :---: | :---: |
| **Player 1: Cooperate ($C$)** | $(-1, -1)$ | $(-5, 0)$ |
| **Player 1: Defect ($D$)** | $(0, -5)$ | **$(-3, -3)$** |

* **Mathematical Invariant:** $D$ strictly dominates $C$ for both players:
  - If Player 2 plays $C$, Player 1 gets $0$ with $D$ vs $-1$ with $C$ ($0 > -1$).
  - If Player 2 plays $D$, Player 1 gets $-3$ with $D$ vs $-5$ with $C$ ($-3 > -5$).
* **The Paradox:** The unique Nash Equilibrium $(D, D)$ yields $(-3, -3)$, which is strictly Pareto-dominated by the cooperative outcome $(C, C)$ yielding $(-1, -1)$. Rational individual optimization leads directly to collective sub-optimality.

### 2. Matching Pennies (Zero-Sum Pure Instability)

Two players simultaneously choose Heads ($H$) or Tails ($T$). Player 1 wins if coins match; Player 2 wins if coins differ.

| | Player 2: Heads ($H$) | Player 2: Tails ($T$) |
| :--- | :---: | :---: |
| **Player 1: Heads ($H$)** | $(+1, -1)$ | $(-1, +1)$ |
| **Player 1: Tails ($T$)** | $(-1, +1)$ | $(+1, -1)$ |

* **Pure Strategy Nash Equilibrium:** **None**.
* **Mixed Strategy Nash Equilibrium:** Both players randomize uniformly: $\sigma_1^* = (\frac{1}{2}H, \frac{1}{2}T)$, $\sigma_2^* = (\frac{1}{2}H, \frac{1}{2}T)$. Expected payoff is $0$.

---

## 4. Common Misconceptions & Mental Traps

### Misconception 1: "A Nash Equilibrium produces the best outcome for everyone."
* **Reality:** Nash equilibrium guarantees **stability**, not efficiency or fairness. As proven by the Prisoner's Dilemma, an equilibrium can be severely Pareto-inefficient. It merely means no single player can unilaterally improve their payoff.

### Misconception 2: "In mixed strategies, players choose actions randomly because they don't care."
* **Reality:** In a mixed strategy Nash equilibrium, your probability mixture is chosen specifically to make your opponent **indifferent** between their pure strategies. If you randomized arbitrarily, your opponent would exploit your probabilities by playing a pure best response, destroying the equilibrium.

### Misconception 3: "Subgame perfection applies to normal-form matrix games."
* **Reality:** Subgame perfection is a refinement strictly for **extensive-form (dynamic/sequential) games**. Normal-form games flatten temporal sequences into simultaneous commitments, which can conceal non-credible threats.

---

## 5. Socratic Discussion Starters

1. **The Folk Theorem:** In a one-shot Prisoner's Dilemma, mutual defection $(D, D)$ is the only rational outcome. Why does repeating the game infinitely with a discount factor $\delta \ge \frac{1}{2}$ allow cooperation $(C, C)$ to be sustained as a subgame perfect equilibrium?
2. **Mechanism Design & Incentive Compatibility:** In a Vickrey second-price sealed-bid auction, why is bidding your exact true valuation a weakly dominant strategy, regardless of what all other bidders do?
3. **Commitment as Power:** In sequential Stackelberg duopoly competition, why does moving first and irrevocably committing to a large production quantity yield higher profits than moving simultaneously?
