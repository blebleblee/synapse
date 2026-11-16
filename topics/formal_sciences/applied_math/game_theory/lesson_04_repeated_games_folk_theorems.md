# Lesson 4: Repeated Games, Folk Theorems, Cooperation

## 1. First-Principles Intuition & Invariants

The theory of repeated games addresses a fundamental tension in strategic interaction: how can rational, self-interested agents sustain cooperation when immediate defection yields higher payoffs? In one-shot encounters, the prisoner's dilemma demonstrates that mutual defection dominates mutual cooperation despite the collective irrationality of the outcome. Yet we observe sustained cooperation across diverse domains—international trade agreements persist despite short-term incentives for protectionism, firms maintain collusive pricing above competitive equilibrium, and social norms enforce reciprocity in repeated interactions. The resolution to this paradox lies not in altruism or bounded rationality, but in the shadow of the future.

When strategic interactions repeat over time, players acquire the capacity to condition current behavior on past play. This temporal structure transforms the incentive landscape: defection in the current period can trigger punishment in future periods, and the present value of these future losses can outweigh immediate gains from deviation. The mathematical formalization of this intuition yields the folk theorems, which characterize the vast multiplicity of equilibrium outcomes sustainable through appropriately designed punishment schemes.

The fundamental object of study is a stage game $G$ repeated either finitely $T$ times or infinitely with discount factor $\delta \in (0,1)$. The stage game is a simultaneous-move normal form game with player set $N = \{1, \ldots, n\}$, action spaces $A_i$ for each player $i$, and payoff functions $u_i: A \to \mathbb{R}$ where $A = \prod_{i \in N} A_i$. A history at time $t$ is a sequence $h_t = (a^0, a^1, \ldots, a^{t-1}) \in A^t$ recording all action profiles played in previous periods. A strategy in the repeated game is a function $s_i: \bigcup_{t=0}^\infty A^t \to A_i$ mapping histories to actions. The space of possible strategies is thus infinite-dimensional even when action spaces are finite, and this richness enables equilibrium multiplicity.

The critical distinction between finite and infinite repetition centers on backward induction. In a finitely repeated game, subgame perfection imposes that play in the final period $T$ must constitute a Nash equilibrium of the stage game, since no future periods remain to condition behavior. Working recursively backward, if the stage game possesses a unique Nash equilibrium, that outcome must be played in every period of any subgame perfect equilibrium. This is the celebrated chain-store paradox: no matter how many markets a monopolist serves sequentially, if the one-shot game has a unique equilibrium where the monopolist accommodates entry, predatory pricing cannot be sustained through backward induction.

The infinite horizon shatters this logic. With no final period, backward induction finds no anchor point, and the space of subgame perfect equilibria expands dramatically. The discount factor $\delta$ parameterizes patience: a player discounts period-$t$ payoffs by $\delta^t$, and the normalized present value of a payoff stream $(u_0, u_1, u_2, \ldots)$ is $(1 - \delta) \sum_{t=0}^\infty \delta^t u_t$. The factor $(1 - \delta)$ normalizes continuation values to the same scale as stage payoffs. As $\delta \to 1$, players become arbitrarily patient, and future consequences weigh heavily against immediate temptations.

The folk theorems establish that for sufficiently patient players, any feasible, individually rational payoff vector can be sustained as a subgame perfect equilibrium outcome. To formalize this, let $V = \{v \in \mathbb{R}^n : v = \sum_{a \in A} \lambda_a u(a), \lambda_a \ge 0, \sum_a \lambda_a = 1\}$ denote the set of feasible payoff vectors, the convex hull of stage-game payoffs. A payoff $v_i$ is individually rational if $v_i \ge \underline{v}_i$ where $\underline{v}_i = \min_{s_{-i}} \max_{s_i} u_i(s_i, s_{-i})$ is player $i$'s minmax payoff, the most that opponents can hold $i$ to through any joint strategy. The minmax payoff represents the harshest credible punishment: if $i$ receives less than $\underline{v}_i$ on average, $i$ can unilaterally improve payoffs regardless of opponents' strategies, violating individual rationality.

The intuition behind folk theorems is that cooperation can be sustained by threatening reversion to minmax punishment following deviation. If the one-period gain from deviation is outweighed by the present value of future losses, deviation becomes unprofitable. The grim trigger strategy formalizes this: play a cooperative action profile $a^*$ as long as no deviation has occurred; if any player deviates, play the minmax action profile against the deviator forever. The simplicity of grim trigger—eternal punishment for a single transgression—makes it pedagogically transparent, but more sophisticated strategies employing temporary punishments or renegotiation-proof mechanisms often characterize realistic enforcement.

The mathematical architecture of repeated games intertwines recursive structure with one-deviation principle verification. Subgame perfection requires that continuation play from any history constitutes a Nash equilibrium in the remaining subgame. Because deviations are observable and players can condition on full histories, the one-deviation principle holds: a strategy profile is subgame perfect if and only if no player can profitably deviate for a single period and then revert to the prescribed continuation strategy. This reduces infinite-dimensional optimization to a finite collection of local incentive constraints, one per player per history type.

The contrast between finite and infinite horizons reveals a phase transition in strategic possibilities. With finitely many repetitions, the unique stage-game Nash equilibrium propagates through backward induction, and cooperation collapses. With infinitely many repetitions and sufficiently patient players, the folk theorems guarantee that almost any individually rational outcome becomes enforceable. The boundary case—infinitely repeated games with impatient players ($\delta$ small)—bridges these extremes: some cooperation may be sustainable, but the set of equilibrium payoffs contracts as $\delta$ decreases. The critical discount factor thresholds, derived from binding incentive constraints, demarcate the frontier between sustainable and unsustainable outcomes.

## 2. Core Architecture & Mechanics

The strategic structure of repeated games rests on three interlocking components: the extensive form representation tracking histories and information sets, the payoff aggregation mechanism through discounting or time-averaging, and the equilibrium refinement selecting credible continuation strategies. We dissect each layer to expose the mathematical machinery enabling cooperation.

### Extensive Form and History-Dependent Strategies

The extensive form of an infinitely repeated game constructs an infinite game tree where each stage corresponds to one play of the base game $G$. At the initial node, players simultaneously choose actions from $A_i$, generating an action profile $a^0 \in A$. This branches into $|A|$ successor nodes, one for each possible outcome. At each subsequent node indexed by history $h_t$, players again choose simultaneously, yielding $|A|$ branches. The tree is infinite in depth but finite in branching factor (assuming finite action spaces).

A pure strategy for player $i$ is a function $s_i: \bigcup_{t=0}^\infty A^t \to A_i$ specifying an action for every possible history. The domain of $s_i$ is countably infinite, and the range is finite, so the space of pure strategies is uncountable with cardinality $|A_i|^{\aleph_0}$. Mixed strategies randomize at each history node, further expanding the strategy space. Behavioral strategies condition randomization on information sets, but in repeated games with perfect monitoring, all past actions are observed, so information sets are singletons and mixed and behavioral strategies coincide.

The payoff function aggregates stage payoffs through discounting. For an infinite sequence of action profiles $(a^0, a^1, a^2, \ldots)$ generated by strategy profile $s = (s_1, \ldots, s_n)$, player $i$'s normalized discounted payoff is

$$
U_i(s) = (1 - \delta) \sum_{t=0}^\infty \delta^t u_i(a^t).
$$

The factor $(1 - \delta)$ ensures that $U_i$ scales comparably to stage payoffs: if player $i$ receives constant stage payoff $c$ in every period, the normalized payoff equals $c$. Without normalization, the sum $(1 - \delta)^{-1} c$ would diverge as $\delta \to 1$. The discount factor $\delta$ captures time preference: $\delta = 0$ corresponds to myopic play (only current period matters), while $\delta \to 1$ represents extreme patience.

An alternative aggregation mechanism is the limit of means (time-average) payoff:

$$
\overline{U}_i(s) = \liminf_{T \to \infty} \frac{1}{T} \sum_{t=0}^{T-1} u_i(a^t).
$$

This captures long-run average returns without discounting, treating all periods symmetrically. The folk theorems hold under both criteria, though the discount factor approach yields sharper thresholds and cleaner comparative statics.

### Subgame Perfection and One-Deviation Principle

A Nash equilibrium of the repeated game is a strategy profile $s^*$ such that no player can increase $U_i$ by unilaterally deviating to a different strategy. Subgame perfection strengthens this: $s^*$ induces a Nash equilibrium in every subgame, where a subgame is the continuation game starting from any history $h_t$. Formally, for every history $h_t$ and every player $i$, the continuation strategy $s_i^* | h_t$ (the restriction of $s_i^*$ to histories extending $h_t$) must be a best response to $s_{-i}^* | h_t$ in the subgame starting at $h_t$.

The one-deviation principle provides a tractable verification criterion. A strategy profile $s^*$ is subgame perfect if and only if no player can profitably deviate in a single period at any history and then conform to $s^*$ thereafter. To formalize, let $\hat{s}_i^{h_t, a_i}$ denote the strategy that deviates to action $a_i$ at history $h_t$ and follows $s_i^*$ subsequently. Then $s^*$ is subgame perfect if and only if for all $i$, all histories $h_t$, and all actions $a_i \in A_i$,

$$
U_i(s^* | h_t) \ge U_i(\hat{s}_i^{h_t, a_i}, s_{-i}^* | h_t).
$$

This reduces the infinite-dimensional optimization problem (checking all possible deviations across all periods) to a countable collection of single-period constraints. The key insight is that multi-period deviations decompose recursively: if a multi-period deviation is profitable, then either the first-period component or some subsequent single-period component must be profitable.

### Minmax Payoffs and Punishment Mechanisms

The minmax value $\underline{v}_i$ for player $i$ is defined by

$$
\underline{v}_i = \min_{s_{-i} \in S_{-i}} \max_{s_i \in S_i} u_i(s_i, s_{-i}),
$$

where $S_i$ denotes player $i$'s mixed strategy space in the stage game. This is the lowest payoff opponents can credibly hold $i$ to: they play the minmax strategy profile $m_{-i}^*$ that minimizes $i$'s best response payoff. Player $i$ cannot prevent this outcome, as $\max_{s_i} u_i(s_i, m_{-i}^*)$ is achieved by $i$'s best response but cannot exceed $\underline{v}_i$ by construction.

In two-player games, the minmax value coincides with the maxmin value due to von Neumann's minimax theorem:

$$
\min_{s_{-i}} \max_{s_i} u_i(s_i, s_{-i}) = \max_{s_i} \min_{s_{-i}} u_i(s_i, s_{-i}).
$$

In games with more than two players, the minmax value can be strictly lower than the maxmin value because multiple opponents coordinate to punish $i$ more effectively than any single opponent could.

The individually rational payoff set is

$$
V^* = \{v \in V : v_i \ge \underline{v}_i \text{ for all } i \in N\},
$$

the feasible payoffs exceeding each player's minmax value. The folk theorem asserts that for $\delta$ sufficiently close to 1, any $v \in \text{int}(V^*)$ (the interior of $V^*$) is achievable as the average payoff in some subgame perfect equilibrium.

### Grim Trigger Strategy Construction

Consider a two-player prisoner's dilemma with actions $C$ (cooperate) and $D$ (defect) and payoffs:

$$
\begin{array}{c|cc}
  & C & D \\
\hline
C & (3,3) & (0,5) \\
D & (5,0) & (1,1)
\end{array}
$$

Mutual cooperation yields $(3,3)$, but $(D,D)$ is the unique Nash equilibrium with payoff $(1,1)$. The minmax payoffs are $\underline{v}_1 = \underline{v}_2 = 1$, achieved when the opponent plays $D$.

The grim trigger strategy for player $i$ is:

$$
s_i^{\text{GT}}(h_t) = \begin{cases}
C & \text{if } a^\tau = (C,C) \text{ for all } \tau < t, \\
D & \text{otherwise}.
\end{cases}
$$

Both players start with $C$. If either deviates, both switch to $D$ forever. We verify subgame perfection. On the equilibrium path where $a^\tau = (C,C)$ for all $\tau < t$, player 1's continuation payoff from conforming is

$$
U_1(s^{\text{GT}} | h_t) = (1 - \delta) \sum_{\tau=0}^\infty \delta^\tau \cdot 3 = 3.
$$

If player 1 deviates to $D$ at $t$, she earns 5 in period $t$ and triggers mutual defection yielding 1 thereafter:

$$
U_1(\hat{s}_1^{h_t, D}, s_2^{\text{GT}} | h_t) = (1 - \delta)(5 + \delta \cdot 1 + \delta^2 \cdot 1 + \cdots) = (1 - \delta)(5 + \delta \sum_{\tau=0}^\infty \delta^\tau) = (1 - \delta)(5 + \frac{\delta}{1 - \delta}) = 5(1 - \delta) + \delta.
$$

The incentive constraint requires $3 \ge 5(1 - \delta) + \delta$, which simplifies to

$$
3 \ge 5 - 5\delta + \delta = 5 - 4\delta \implies 4\delta \ge 2 \implies \delta \ge \frac{1}{2}.
$$

For $\delta \ge 1/2$, grim trigger sustains mutual cooperation as a subgame perfect equilibrium. Off the equilibrium path, after any deviation, both players play $D$ forever, which is a Nash equilibrium of the stage game and trivially subgame perfect.

### Tit-for-Tat and Forgiving Strategies

Tit-for-tat (TFT) mimics the opponent's previous action:

$$
s_i^{\text{TFT}}(h_t) = \begin{cases}
C & \text{if } t = 0, \\
a_{-i}^{t-1} & \text{if } t \ge 1.
\end{cases}
$$

Against itself, TFT sustains cooperation: both players cooperate indefinitely. A single deviation triggers one period of punishment (the opponent defects next period), after which cooperation resumes. TFT is forgiving, allowing recovery from isolated mistakes.

However, TFT is not subgame perfect in the prisoner's dilemma. After player 1 deviates to $D$ at some history, TFT prescribes that player 2 plays $D$ next period, then reverts to copying player 1's action. If player 1 anticipates this and plays $C$ in the punishment period, cooperation resumes, and player 1's one-period gain from the initial deviation is not offset by sufficient punishment. The incentive constraint fails for moderate $\delta$.

To construct forgiving subgame perfect strategies, we employ temporary punishment phases. One approach is the $k$-period punishment strategy: after a deviation, play the minmax profile for $k$ periods, then revert to cooperation. The length $k$ adjusts to ensure that the present value of punishment outweighs the one-period deviation gain. As $\delta$ increases, shorter punishment phases suffice.

### Friedman's Folk Theorem

Friedman's 1971 folk theorem provides the foundational result for two-player games. Let $v^* = (v_1^*, v_2^*)$ be a feasible payoff vector Pareto-dominating the minmax profile, so $v_i^* > \underline{v}_i$ for both $i$. There exists a $\overline{\delta} < 1$ such that for all $\delta \ge \overline{\delta}$, there is a subgame perfect equilibrium yielding average payoff $v^*$.

The proof constructs a grim trigger strategy: play actions generating $v^*$ on the equilibrium path; if anyone deviates, switch to the minmax profile forever. For player $i$, let $a^*$ denote the action profile (possibly mixed or a convex combination of action profiles over time) yielding $v^*$, and let $g_i$ be the maximum payoff $i$ can achieve by deviating from $a^*$. The incentive constraint is

$$
v_i^* \ge (1 - \delta) g_i + \delta \underline{v}_i.
$$

Rearranging,

$$
v_i^* - \underline{v}_i \ge (1 - \delta)(g_i - \underline{v}_i) \implies \delta \ge \frac{g_i - v_i^*}{g_i - \underline{v}_i}.
$$

Since $v_i^* > \underline{v}_i$, the denominator is positive. The threshold $\overline{\delta} = \max_i \frac{g_i - v_i^*}{g_i - \underline{v}_i}$ bounds $\delta$ from below. For $\delta \ge \overline{\delta}$, the incentive constraints hold for both players, and grim trigger is subgame perfect.

Friedman's theorem establishes that any strictly individually rational, feasible payoff is sustainable for sufficiently patient players. The restriction to strict inequality ($v_i^* > \underline{v}_i$) ensures that punishment is worse than cooperation, making threats credible.

### Fudenberg-Maskin Folk Theorem

The Fudenberg-Maskin 1986 folk theorem extends to $n$-player games and relaxes the strict inequality requirement, allowing payoffs on the boundary of $V^*$. The statement is: for any $v \in \text{int}(V^*)$ and any $\epsilon > 0$, there exists $\overline{\delta} < 1$ such that for all $\delta \ge \overline{\delta}$, there is a subgame perfect equilibrium with average payoff within $\epsilon$ of $v$.

The proof employs more sophisticated punishment schemes. Instead of permanent minmax punishment, Fudenberg-Maskin use temporary punishment phases followed by reward phases. After player $i$ deviates, opponents minmax $i$ for $T$ periods (where $T$ depends on $\delta$), then all players receive a reward exceeding their minmax values to incentivize participation in punishment.

The key insight is decomposability: any feasible payoff can be approximated by a mixture of action profiles over time. By cycling through appropriate profiles and inserting punishment and reward phases, the desired long-run average is achieved while satisfying all incentive constraints. The interior condition ensures that small perturbations (the $\epsilon$ tolerance) maintain individual rationality, and patience ($\delta$ near 1) ensures that future rewards outweigh immediate temptations.

A critical technical point is that subgame perfection requires punishment of punishers: if player $j$ fails to punish player $i$ after $i$ deviates, then $j$ must be punished. This recursive structure necessitates a hierarchy of punishment phases, but finite memory suffices due to the interior condition and patient players.

### Critical Discount Factor Thresholds

For concrete games, we derive exact threshold values. Consider symmetric $n$-player public goods provision. Each player chooses contribution $c_i \in [0, \omega]$ with cost $c_i$ and benefit $(1 + \beta) \sum_{j=1}^n c_j / n$ where $\beta > 0$ represents the public goods multiplier. The stage game has a unique Nash equilibrium with $c_i^* = 0$ (free riding), yielding payoff 0. The efficient outcome is $c_i = \omega$ for all $i$, yielding payoff $\omega \beta$ per player.

Grim trigger prescribes $c_i = \omega$ on path and $c_i = 0$ off path. The on-path payoff is $\omega \beta$. A deviator sets $c_i = 0$, earning $(1 + \beta)(n-1)\omega / n$ in the deviation period (benefiting from others' contributions without cost) and 0 thereafter. The incentive constraint is

$$
\omega \beta \ge (1 - \delta)(1 + \beta)\frac{(n-1)\omega}{n} + \delta \cdot 0.
$$

Simplifying,

$$
\beta \ge (1 - \delta)(1 + \beta)\frac{n-1}{n} \implies \frac{\beta n}{n-1} \ge (1 - \delta)(1 + \beta) \implies \delta \ge 1 - \frac{\beta n}{(1 + \beta)(n-1)}.
$$

As $n \to \infty$, the threshold approaches $\delta \ge 1 - \frac{\beta}{1 + \beta} = \frac{1}{1 + \beta}$. For large groups, cooperation becomes harder to sustain (higher $\delta$ required) because each player's contribution has diluted impact, reducing the per-capita benefit of cooperation relative to the free-riding temptation.

## 3. High-Performance Optimization & Failure Modes

The theoretical power of folk theorems—virtually any cooperative outcome is achievable—translates into practical indeterminacy. With infinitely many equilibria, selecting among them requires coordination devices, focal points, or renegotiation dynamics. We examine computational strategies for equilibrium construction, robustness concerns, and behavioral refinements that filter the equilibrium set.

### Algorithmic Equilibrium Construction

Constructing explicit subgame perfect equilibria for complex stage games involves optimizing over both on-path action profiles and off-path punishment schemes. The procedure decomposes into three phases: payoff target selection, incentive constraint verification, and continuation value recursion.

First, select a target payoff vector $v^* \in \text{int}(V^*)$. This can be a Pareto-efficient outcome, a Nash bargaining solution, or any interior point. Second, construct a sequence of action profiles $\{a^t\}$ (possibly stochastic or cycling deterministically) yielding average payoff $v^*$. For finite action spaces, express $v^*$ as a convex combination $v^* = \sum_{a \in A} \lambda_a u(a)$ and interpret $\lambda_a$ as the long-run frequency of profile $a$.

Third, design punishment strategies. For each player $i$, compute the minmax action profile $m_{-i}$ that minimizes $i$'s best response payoff. Grim trigger uses $m_{-i}$ as the permanent off-path continuation. For temporary punishments, specify a punishment length $T_i$ such that the discounted loss $(1 - \delta) \sum_{t=1}^{T_i} \delta^t (\underline{v}_i - v_i^*)$ exceeds the one-period deviation gain $g_i - v_i^*$.

Fourth, verify incentive constraints at each history type. Using the one-deviation principle, check that no player profits from a single-period deviation at any on-path history or during any punishment phase. For punishment phases, ensure that punishers have incentives to carry out punishment (requiring recursive punishment of non-punishers).

Numerically, this involves solving a system of inequalities. For $n$ players and $k$ distinct history types (equilibrium path, player $i$ being punished, etc.), there are $O(nk)$ incentive constraints. Each constraint is a linear inequality in $\delta$ for linear payoff functions, so binary search over $\delta$ efficiently finds the minimum threshold.

### Renegotiation-Proofness and Credible Threats

A fundamental critique of grim trigger and permanent punishment equilibria is renegotiation: if both players would prefer to restart cooperation rather than persist in mutual punishment, why should the threat be credible? After a deviation, both players suffer low payoffs forever, but could Pareto-improve by returning to cooperation. Anticipating this, deviators may not fear punishment, undermining enforcement.

A renegotiation-proof equilibrium survives the following test: at every history, no coalition of players can jointly deviate to a continuation strategy profile that makes all members weakly better off and some strictly better off, provided the opponents play their prescribed continuations. This refinement is strong and often rules out simple punishment equilibria.

Renegotiation-proof constructions rely on temporary punishments with reward phases. After player $i$ deviates, opponents minmax $i$ for $T$ periods. During punishment, non-deviators receive rewards greater than on-path payoffs, incentivizing them to reject renegotiation with the deviator. After punishment, all return to cooperation at a lower continuation value for the deviator (building a reputation cost). The reward phase makes punishment individually optimal for non-deviators, eliminating Pareto-improving renegotiations.

Technically, renegotiation-proofness requires that continuation values lie on the Pareto frontier relative to the subgame. This imposes tighter constraints than standard subgame perfection and may increase the minimal discount factor threshold.

### Imperfect Monitoring and Stochastic Outcomes

When actions are imperfectly observed or payoffs are stochastic, distinguishing deviations from bad luck becomes critical. Suppose stage payoffs are random: $\tilde{u}_i(a) = u_i(a) + \epsilon_i$ where $\epsilon_i$ is noise. Players observe outcomes but not opponents' actions directly. A low realized payoff could indicate a deviation or bad luck.

Green and Porter (1984) analyze collusion under imperfect monitoring in oligopoly. Firms coordinate on a high-price profile but cannot observe competitors' prices directly, only market demand. Low demand could signal a price cut (deviation) or a negative demand shock. The equilibrium uses trigger strategies based on observable outcomes: if market price falls below a threshold, all firms enter a punishment phase (price war) for $T$ periods, then revert to collusion.

This introduces false positives: punishment occurs even when no deviation happened. The frequency of punishment phases trades off enforcement strength (tight threshold detects more deviations) against efficiency (frequent wars reduce average payoffs). The critical discount factor rises because players must tolerate occasional unjust punishment.

Formally, let $y$ be an observed signal with distribution $P(\cdot | a)$ conditional on action profile $a$. A public strategy maps histories of signals to actions. The optimal threshold $\bar{y}$ satisfies the incentive constraint for deviators:

$$
v_i^* \ge \max_{a_i'} \left[ (1 - \delta) \mathbb{E}[u_i(a_i', a_{-i}^*) | y < \bar{y}] + \delta v_i^* P(y \ge \bar{y} | a_i', a_{-i}^*) + \delta \underline{v}_i P(y < \bar{y} | a_i', a_{-i}^*) \right].
$$

Solving for $\bar{y}$ and $\delta$ numerically yields the equilibrium threshold and minimal patience requirement.

### Private Monitoring and Belief Coordination

When signals are private (each player observes a different noisy indicator), folk theorems require belief-free or semi-private strategies. Players cannot coordinate on common beliefs about past play, complicating punishment schemes. Mailath and Morris (2002) show that approximate efficiency is achievable if individual signals are sufficiently informative.

The construction uses block strategies: the infinite horizon divides into blocks of length $T$. Within each block, players follow a review phase strategy, and at block boundaries, continuation values adjust based on accumulated private signals. By the law of large numbers, long blocks smooth out noise, and the distribution of block-average signals becomes nearly deterministic, enabling approximate coordination.

The technical challenge is ensuring that deviations within a block are detectable from private signals and that punishments remain incentive-compatible despite incomplete information. The minimal discount factor threshold increases with noise variance and the required approximation tolerance.

### Finite Automaton Strategies and Bounded Rationality

Subgame perfect strategies can be arbitrarily complex, requiring unbounded memory to track full histories. Bounded rationality constraints motivate restricting attention to finite-state automata. A finite automaton strategy for player $i$ is a tuple $(Q_i, q_i^0, f_i, \tau_i)$ where $Q_i$ is a finite state space, $q_i^0 \in Q_i$ is the initial state, $f_i: Q_i \to A_i$ maps states to actions, and $\tau_i: Q_i \times A \to Q_i$ is the transition function.

Grim trigger is a two-state automaton: state $C$ (cooperate) with $f_i(C) = C$ and transition $\tau_i(C, a) = C$ if $a = (C, \ldots, C)$, else $\tau_i(C, a) = D$; state $D$ (defect) with $f_i(D) = D$ and $\tau_i(D, a) = D$ always. Tit-for-tat is also two-state: state $C$ with $f_i(C) = C$ and $\tau_i(C, a) = C$ if $a_{-i} = C$, else $D$; state $D$ with $f_i(D) = D$ and similar transitions.

Restricting to automata with at most $k$ states limits the equilibrium set. For small $k$, only simple strategies are feasible, and many folk theorem outcomes become unattainable. Conversely, as $k$ grows, the gap between $k$-state equilibria and full subgame perfect equilibria vanishes. For two-player prisoner's dilemma, Abreu and Rubinstein (1988) show that three-state automata suffice for many efficient equilibria.

The computational complexity of verifying whether a given automaton profile is subgame perfect scales as $O(|Q|^n |A|)$ where $|Q| = \prod_i |Q_i|$ is the joint state space size. For large games, symbolic model checking or dynamic programming can prune the verification space.

### Evolutionary Stability and Trembling-Hand Robustness

From an evolutionary perspective, strategies compete based on long-run payoffs against the population distribution. An evolutionarily stable strategy (ESS) is a Nash equilibrium that resists invasion by rare mutants. In repeated games, ESS refinement filters equilibria by robustness to small perturbations.

Tit-for-tat famously performed well in Axelrod's iterated prisoner's dilemma tournaments, exhibiting nice (never defects first), forgiving (returns to cooperation after opponent cooperates), and retaliatory (punishes defection) properties. However, TFT is not evolutionarily stable: a population of TFT players is invadable by "always cooperate" (which achieves the same payoff against TFT but higher payoff against other always-cooperate mutants).

Trembling-hand perfection requires that strategies remain best responses even when opponents tremble with small probability $\epsilon > 0$. A trembling-hand perfect equilibrium is a limit of $\epsilon$-perfect equilibria as $\epsilon \to 0$, where $\epsilon$-perfect means every strategy puts probability at least $\epsilon$ on every action. In repeated games, trembling-hand perfection can rule out grim trigger if trembles trigger irreversible punishment, making forgiving strategies more robust.

Generous tit-for-tat (GTFT) cooperates with probability $1 - \epsilon$ after opponent defects, providing some forgiveness. This buffers against accidental defections and is evolutionarily stable in noisy environments. The trade-off is reduced punishment strength, requiring higher $\delta$ to enforce cooperation.

### Multi-Dimensional Payoff Spaces and Efficiency Frontiers

When stage games have rich action spaces or multiple strategic dimensions, the feasible payoff set $V$ becomes a high-dimensional polytope (for finite actions) or continuum (for continuous actions). Characterizing the Pareto frontier and interior of $V^*$ requires convex optimization.

For two-player games, the Pareto frontier is one-dimensional and parameterizable by a scalar weight $\lambda \in [0, 1]$. Maximizing $\lambda v_1 + (1 - \lambda) v_2$ over $V$ traces the frontier. For $n$-player games, the frontier is $(n-1)$-dimensional, and systematic exploration requires multi-objective optimization algorithms.

In practice, selecting a target payoff on the frontier involves bargaining protocols. The Nash bargaining solution maximizes the product of surplus $(v_1 - \underline{v}_1)(v_2 - \underline{v}_2)$, providing a focal point with axiomatic justification (Pareto efficiency, symmetry, independence of irrelevant alternatives, invariance to affine transformations). The kalai-Smorodinsky solution equalizes ratios of gains from disagreement, offering an alternative focal point.

Computing the Nash bargaining solution for complex games involves solving a nonlinear program. For quadratic payoffs, closed-form solutions exist; otherwise, numerical optimization applies. The folk theorems then guarantee that the bargaining solution is sustainable as a subgame perfect equilibrium for sufficiently high $\delta$.

### Failure Modes: Coordination Traps and Multiplicity

The multiplicity of equilibria in repeated games creates coordination challenges. Players may converge on inefficient equilibria if coordination on efficient outcomes is difficult. For instance, in the prisoner's dilemma, always-defect is always an equilibrium (repeating the stage Nash), and no unilateral deviation can reach a cooperative equilibrium. Coordination on grim trigger requires common knowledge of the strategy, shared discount factor beliefs, and synchronization of punishment triggers.

Miscoordination on punishment timing is catastrophic. If player 1 believes a deviation occurred at period $t$ but player 2 believes play is on-path, their actions diverge, and cooperation collapses. This fragility motivates public randomization devices (correlated equilibria) or communication protocols to align beliefs.

Another failure mode is ratcheting: once cooperation breaks down, returning to cooperation may require costly signaling or negotiation. If punishment phases are long or players have heterogeneous discount factors, agreement on restart terms can be elusive. Mechanism design approaches precommit to fixed protocols (automatic restart after $T$ punishment periods), reducing renegotiation friction.

### Extensions to Asymmetric Information and Reputation

When players have private information about payoffs or types, repeated interactions enable reputation building. A long-lived player facing short-lived opponents can invest in a reputation for toughness (e.g., never accommodating entry) to deter future opponents. This introduces a signaling dimension: current actions convey information about type.

The Kreps-Wilson (1982) and Milgrom-Roberts (1982) reputation models formalize this in finitely repeated games. With small probability, the long-lived player is a behavioral type committed to a fixed strategy (e.g., always predating entrants). Short-lived opponents cannot perfectly infer the type, so even rational types pool with behavioral types early on to build reputation. As the horizon approaches, reputation concerns diminish, and play converges to stage equilibrium.

The key result is that reputational incentives can sustain cooperation even in finite repetition if there is incomplete information. The required perturbation (positive prior probability on behavioral types) is arbitrarily small, making reputation a robust phenomenon. The discount factor threshold trades off the cost of mimicking the behavioral type against the long-run gain from reputation.

In infinitely repeated settings with incomplete information, the revelation principle applies: any equilibrium can be implemented by a direct mechanism where players truthfully report types each period. However, dynamic consistency (sequential rationality) imposes tighter constraints than static mechanism design, and not all social choice functions are implementable.

### Computational Implementation: Dynamic Programming Over Continuation Values

Implementing folk theorem strategies computationally requires dynamic programming over continuation values. Define $W_i(h_t)$ as player $i$'s continuation value at history $h_t$. Subgame perfection requires $W_i(h_t) = (1 - \delta) u_i(a^t) + \delta W_i(h_{t+1})$ where $a^t$ is the action profile played at $h_t$ and $h_{t+1}$ is the successor history.

For finite automaton strategies, $W_i$ depends only on the current state $q$, reducing the state space from infinite histories to finite states. The Bellman equation becomes $W_i(q) = (1 - \delta) u_i(f(q)) + \delta W_i(\tau(q, f(q)))$. For a strategy profile to be subgame perfect, we verify

$$
W_i(q) \ge (1 - \delta) u_i(a_i, f_{-i}(q)) + \delta W_i(\tau(q, (a_i, f_{-i}(q))))
$$

for all $i$, all states $q$, and all deviations $a_i \ne f_i(q)$.

Algorithmically, this is a fixed-point computation. Initialize $W_i^{(0)}(q)$ arbitrarily (e.g., minmax values). Iterate $W_i^{(k+1)}(q) = (1 - \delta) u_i(f(q)) + \delta W_i^{(k)}(\tau(q, f(q)))$ until convergence. Then check incentive constraints. If any constraint fails, adjust the strategy profile or discount factor.

For continuous action spaces, approximate the continuation value function using function approximation (polynomial basis, neural networks). Fitted value iteration or temporal difference learning (as in reinforcement learning) can compute approximate subgame perfect equilibria, though convergence guarantees are weaker than in finite spaces.

### Experimental Evidence and Behavioral Deviations

Laboratory experiments testing folk theorems reveal systematic deviations from theoretical predictions. Players cooperate more than theory predicts in finitely repeated games, especially when the horizon is uncertain or subjects have social preferences (altruism, fairness, reciprocity). Conversely, cooperation sometimes unravels faster than backward induction suggests when players exhibit mistrust or pessimism.

In infinitely repeated games (approximated by random continuation with probability $\delta$), cooperation rates increase with $\delta$ as theory predicts, but thresholds are often lower than the equilibrium $\delta$. This suggests players use forgiving strategies (TFT-like) or have higher subjective discount rates than revealed by incentive constraints.

Punishment behavior exhibits social preferences: players punish deviators even when punishment is costly and offers no strategic benefit, a phenomenon termed altruistic punishment. This willingness to punish can sustain cooperation at lower $\delta$ than predicted, effectively increasing enforcement strength.

Incorporating bounded rationality via level-$k$ reasoning or quantal response equilibrium partially explains these deviations. Level-1 players best respond to a naive (random or simple) opponent model, level-2 best respond to level-1, and so forth. Quantal response assumes players randomize with probabilities proportional to $\exp(\lambda \cdot \text{utility})$, smoothing discrete best responses. These models predict gradualism in reaching cooperation and occasional breakdowns due to cognitive errors.

---

The machinery of repeated games transforms the strategic landscape from the stark Hobbesian world of one-shot interactions to the intricate web of contingent cooperation underpinned by patient enforcement. The folk theorems establish that almost any outcome is theoretically sustainable, but this multiplicity demands coordination, credibility, and robustness refinements to guide practical applications. The critical discount factor thresholds distill patience requirements into actionable parameters, while automaton representations and algorithmic verification ground abstract theory in computational practice. Understanding both the mathematical architecture and behavioral boundary conditions enables deployment of repeated game theory to mechanism design, contract enforcement, and institutional stability across domains from industrial organization to international relations.
