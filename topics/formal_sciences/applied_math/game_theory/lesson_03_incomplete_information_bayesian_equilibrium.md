# Lesson 3: Incomplete Information, Bayesian Games, Perfect Bayesian Equilibrium

## 1. First-Principles Intuition & Invariants

The classical framework of strategic and extensive-form games rests upon a critical but restrictive assumption: all players possess complete knowledge of the game structure, including the payoff functions, strategy spaces, and rationality of every participant. Yet the real world rarely affords such transparency. Auctions unfold where bidders remain uncertain about their rivals' valuations. Labor markets operate where employers cannot directly observe worker productivity before hiring. International negotiations proceed under fog-of-war conditions where each nation's resolve, resource constraints, and internal political pressures remain partially opaque. The theory of games with incomplete information, inaugurated by John Harsanyi in the late 1960s, transforms this epistemic uncertainty from an analytical obstacle into a formal object of study.

Harsanyi's foundational insight was to model incomplete information as imperfect information about an initial move by Nature. Rather than treating unknown player characteristics as an intractable barrier, he introduced the concept of player types: each player belongs to one of finitely or infinitely many types, drawn according to a common prior probability distribution. A type encapsulates all the private information a player possesses—her payoff function, her risk preferences, her cost structure, or any other parameter that affects strategic calculation but remains hidden from opponents. This transformation reduces the problem of incomplete information to one of imperfect information, where players observe their own type but can only form probabilistic beliefs about the types of others.

The conceptual elegance of Harsanyi's construction lies in its preservation of the Nash equilibrium framework while accommodating uncertainty. A **Bayesian Nash equilibrium** specifies a strategy for each type of each player such that, given the equilibrium strategies of all other types and the common prior distribution over types, no player-type has an incentive to deviate. This equilibrium concept respects the informational constraints: each player optimizes based on her own type and her beliefs about others' types, which are derived from the common prior and the Bayesian updating principle.

The distinction between **ex ante** and **interim** perspectives proves essential in welfare analysis and mechanism design. The ex ante stage occurs before Nature reveals types, when all players share identical beliefs governed by the common prior. At this stage, expected payoffs integrate over all possible type realizations. The interim stage occurs after each player learns her own type but before the game unfolds. Interim beliefs condition on the player's private information, and interim expected payoffs reflect this conditioning. The ex post stage, though less central to Bayesian equilibrium analysis, occurs after all uncertainty resolves and all types become public knowledge.

When games unfold sequentially and players observe actions but not types, a more refined equilibrium concept becomes necessary. **Perfect Bayesian Equilibrium** (PBE) extends Bayesian Nash equilibrium to extensive-form games by imposing two additional requirements: sequential rationality and belief consistency. Sequential rationality demands that at every information set, the player's strategy must be optimal given her beliefs about the types and past actions of others. Belief consistency requires that beliefs be derived from Bayes' rule and the equilibrium strategies whenever possible. This dual mandate ensures that strategies remain credible at every decision node and that beliefs update rationally as information accrues.

The canonical application of Perfect Bayesian Equilibrium is the class of signaling games, where one player (the Sender) possesses private information about her type and takes an action observable to another player (the Receiver), who then responds. The Sender's action serves as a signal that may reveal, conceal, or distort information about her type. The Receiver forms beliefs about the Sender's type by interpreting the signal through the lens of Bayes' rule, and these beliefs determine the Receiver's optimal response. The strategic tension lies in the Sender's incentive to manipulate the Receiver's beliefs and the Receiver's awareness of this incentive.

Signaling games admit multiple Perfect Bayesian Equilibria, often including both separating equilibria (where different types choose distinct signals, fully revealing their types) and pooling equilibria (where all types choose the same signal, leaving the Receiver's beliefs unchanged). This multiplicity arises because beliefs at information sets that are never reached in equilibrium—so-called off-the-equilibrium-path information sets—can be specified arbitrarily subject only to the constraint that they form a probability distribution. Different off-path beliefs sustain different equilibria, even when on-path behavior remains unchanged.

The proliferation of equilibria motivated the development of refinement criteria that impose additional restrictions on beliefs to eliminate equilibria deemed implausible or unreasonable. **Forward induction** captures the idea that players should interpret unexpected deviations as rational choices by some type for whom the deviation is beneficial, rather than as mistakes. If a player observes an out-of-equilibrium action that would be profitable for only one type, she should believe with high probability that the deviating player is of that type. The **intuitive criterion**, formalized by Cho and Kreps, operationalizes forward induction in signaling games by requiring that if an off-path signal is equilibrium-dominated for one type (meaning that type would never send it even if it induced the most favorable receiver beliefs) but not for another type, the Receiver must place zero probability on the first type having sent the signal.

The mathematical architecture of Bayesian games interweaves probability theory, decision theory, and game-theoretic equilibrium analysis. Each player's strategy space expands from a set of actions to a mapping from types to actions. Beliefs become first-order probability distributions over opponents' types, and higher-order beliefs—beliefs about beliefs—lurk in the background, disciplined by the common prior assumption. Equilibrium conditions transform into systems of inequalities expressing interim incentive compatibility constraints, where each type's expected payoff from her equilibrium strategy must weakly exceed the expected payoff from any deviation, with expectations taken over the distribution of opponents' types.

The transition from static Bayesian games to dynamic games with incomplete information introduces the mechanism of belief updating. As the game tree unfolds and players observe actions, they refine their beliefs about opponents' types using Bayes' rule. The posterior probability that an opponent is of a particular type, conditional on observing a specific action, equals the prior probability of that type multiplied by the likelihood that type would choose that action, normalized by the total probability of observing the action across all types. This updating process must respect the constraints of probability theory: beliefs remain non-negative, sum to one, and evolve consistently with the information structure of the game.

Sequential rationality imposes a stringent consistency requirement on strategies: at every information set, regardless of whether that set is reached with positive probability in equilibrium, the player's continuation strategy must maximize her expected payoff given her beliefs. This requirement eliminates strategies that rely on non-credible threats or promises off the equilibrium path. In contrast to subgame perfection, which applies only at decision nodes that are singletons (where the player knows the complete history), sequential rationality applies at all information sets, even those containing multiple nodes where the player faces residual uncertainty about past actions or types.

The interplay between beliefs and strategies gives rise to a fixed-point structure reminiscent of Nash equilibrium. Beliefs must be consistent with strategies via Bayes' rule, and strategies must be optimal given beliefs via expected utility maximization. This mutual consistency defines the equilibrium, but unlike Nash equilibrium in complete-information games, the fixed point involves both behavioral strategies and belief systems. The existence of Perfect Bayesian Equilibrium in finite signaling games follows from Kakutani's fixed-point theorem applied to the correspondence mapping belief-strategy profiles to best-response belief-strategy profiles, though the technical details require care in handling the sequential structure and the conditioning on zero-probability events.

The richness of Bayesian games lies not only in their descriptive power but in their prescriptive implications for mechanism design, contract theory, and information economics. By modeling informational asymmetries explicitly, the theory exposes the strategic value of information, the costs of adverse selection and moral hazard, and the potential for signaling and screening to overcome informational frictions. The equilibrium analysis reveals when and how information is credibly transmitted, when it is concealed, and when informational rents accrue to privately informed parties.


## 2. Core Architecture & Mechanics

The formal architecture of a Bayesian game begins with Harsanyi's type space construction. Let $I = \{1, 2, \ldots, n\}$ denote the set of players. For each player $i \in I$, let $\Theta_i$ denote the set of possible types for player $i$, where a type $\theta_i \in \Theta_i$ encodes all the private information player $i$ possesses. The full type space is the Cartesian product $\Theta = \Theta_1 \times \Theta_2 \times \cdots \times \Theta_n$, representing all possible type profiles. Nature draws a type profile $\theta = (\theta_1, \theta_2, \ldots, \theta_n)$ from $\Theta$ according to a common prior probability distribution $p \in \Delta(\Theta)$, where $\Delta(\Theta)$ denotes the set of probability distributions over $\Theta$. Each player $i$ learns her own type $\theta_i$ but not the types of other players, denoted $\theta_{-i} = (\theta_1, \ldots, \theta_{i-1}, \theta_{i+1}, \ldots, \theta_n)$.

Given her type $\theta_i$, player $i$ forms beliefs about the types of others by conditioning the common prior on the event that her type is $\theta_i$. The conditional probability distribution over $\theta_{-i}$ given $\theta_i$ is

$$p(\theta_{-i} \mid \theta_i) = \frac{p(\theta_i, \theta_{-i})}{\sum_{\theta'_{-i} \in \Theta_{-i}} p(\theta_i, \theta'_{-i})},$$

provided the denominator is positive. This conditional distribution represents player $i$'s interim beliefs about the types of other players. When types are drawn independently—meaning $p(\theta) = \prod_{i=1}^n p_i(\theta_i)$—interim beliefs factor into the product of marginal distributions over each opponent's type, simplifying the analysis.

Each player $i$ possesses an action set $A_i$ and a payoff function $u_i: A \times \Theta \to \mathbb{R}$, where $A = A_1 \times \cdots \times A_n$ is the set of action profiles. The payoff function captures the dependence of player $i$'s utility on the actions chosen by all players and the full type profile. A **pure strategy** for player $i$ in a Bayesian game is a function $s_i: \Theta_i \to A_i$ that maps each of her types to an action. A mixed strategy is a function $\sigma_i: \Theta_i \to \Delta(A_i)$ that maps each type to a probability distribution over actions. The strategy profile $s = (s_1, \ldots, s_n)$ specifies the behavior of all player types.

The interim expected payoff for player $i$ of type $\theta_i$ when playing strategy $s_i$ against the strategies $s_{-i}$ of others is

$$U_i(s_i, s_{-i} \mid \theta_i) = \sum_{\theta_{-i} \in \Theta_{-i}} p(\theta_{-i} \mid \theta_i) \, u_i(s_i(\theta_i), s_{-i}(\theta_{-i}), \theta_i, \theta_{-i}).$$

This expression integrates over the uncertainty about opponents' types, weighting each type profile's payoff by the interim belief probability. A strategy profile $s^*$ constitutes a **Bayesian Nash equilibrium** if for every player $i \in I$ and every type $\theta_i \in \Theta_i$, the strategy $s_i^*(\theta_i)$ maximizes player $i$'s interim expected payoff given the strategies $s_{-i}^*$ of all other types:

$$U_i(s_i^*, s_{-i}^* \mid \theta_i) \geq U_i(s_i, s_{-i}^* \mid \theta_i) \quad \text{for all } s_i: \Theta_i \to A_i.$$

Equivalently, for each type $\theta_i$, the action $s_i^*(\theta_i)$ must be a best response to the distribution of opponents' actions induced by their types and strategies.

To illustrate the computational structure, consider a first-price sealed-bid auction with two bidders. Each bidder $i \in \{1, 2\}$ has a private valuation $v_i \in [0, 1]$ for the object, drawn independently from the uniform distribution on $[0, 1]$. Simultaneously, each bidder submits a bid $b_i \in [0, 1]$. The highest bidder wins and pays her bid; in case of a tie, the object is awarded randomly. Bidder $i$'s payoff is $v_i - b_i$ if she wins and $0$ if she loses. In this setting, $\Theta_i = [0, 1]$, $A_i = [0, 1]$, and the payoff function is

$$u_i(b_1, b_2, v_1, v_2) = \begin{cases}
v_i - b_i & \text{if } b_i > b_j \text{ for } j \neq i, \\
\frac{1}{2}(v_i - b_i) & \text{if } b_i = b_j, \\
0 & \text{if } b_i < b_j.
\end{cases}$$

We seek a symmetric Bayesian Nash equilibrium where each bidder uses the same bidding strategy $b(v)$. By symmetry, bidder $i$ with valuation $v_i$ faces an opponent whose valuation is uniformly distributed on $[0, 1]$. If bidder $i$ bids $b$ and the opponent uses the strategy $b(v)$, bidder $i$ wins whenever the opponent's valuation $v_j$ satisfies $b(v_j) \leq b$. If $b(v)$ is strictly increasing (a property we will verify), this condition is equivalent to $v_j \leq b^{-1}(b)$, which occurs with probability $b^{-1}(b)$. The expected payoff for bidder $i$ when her valuation is $v_i$ and she bids $b$ is

$$U_i(b \mid v_i) = (v_i - b) \cdot \Pr[b(v_j) \leq b] = (v_i - b) \cdot b^{-1}(b).$$

To find the optimal bid, we differentiate with respect to $b$:

$$\frac{d U_i}{d b} = -b^{-1}(b) + (v_i - b) \cdot \frac{d}{d b} b^{-1}(b).$$

In equilibrium, bidder $i$ chooses $b = b(v_i)$, so $b^{-1}(b) = v_i$. The derivative of the inverse function is $\frac{d}{d b} b^{-1}(b) = \frac{1}{b'(b^{-1}(b))} = \frac{1}{b'(v_i)}$. Substituting and setting the derivative equal to zero yields

$$-v_i + (v_i - b(v_i)) \cdot \frac{1}{b'(v_i)} = 0,$$

which rearranges to

$$b'(v_i) \cdot v_i = v_i - b(v_i).$$

This is a first-order linear ordinary differential equation in $b(v_i)$. Rearranging gives

$$b'(v_i) + \frac{b(v_i)}{v_i} = 1.$$

Multiplying both sides by the integrating factor $v_i$ yields

$$v_i b'(v_i) + b(v_i) = v_i,$$

which is the derivative of $v_i b(v_i)$ with respect to $v_i$. Integrating both sides from $0$ to $v_i$ and applying the boundary condition $b(0) = 0$ (a bidder with zero valuation bids zero) gives

$$v_i b(v_i) = \int_0^{v_i} v \, dv = \frac{v_i^2}{2},$$

hence

$$b(v_i) = \frac{v_i}{2}.$$

This symmetric strategy profile, where each bidder bids half her valuation, constitutes the unique symmetric Bayesian Nash equilibrium of the first-price auction.

The extension to extensive-form games with incomplete information requires embedding the type space into a game tree. A standard representation begins with a chance node where Nature draws the type profile $\theta$ according to the common prior $p$. Each player $i$ observes only $\theta_i$, not $\theta_{-i}$. The game then proceeds through a sequence of decision nodes, where at each node a player chooses an action from a feasible set. Information sets partition the decision nodes in the usual way, respecting the constraint that a player cannot distinguish between nodes in the same information set based on the history of play and her private information.

A **Perfect Bayesian Equilibrium** in an extensive-form game with incomplete information consists of a strategy profile $s^* = (s_1^*, \ldots, s_n^*)$ and a belief system $\mu$, where $\mu$ assigns to each information set $h$ a probability distribution $\mu(\cdot \mid h)$ over the nodes in $h$ and over the type profiles consistent with reaching $h$. The equilibrium must satisfy four conditions:

**Condition 1: Sequential Rationality.** At every information set $h$ where player $i$ moves, the continuation strategy $s_i^* \mid_h$ must maximize player $i$'s expected payoff conditional on being at $h$, given the beliefs $\mu(\cdot \mid h)$ and the strategies $s_{-i}^*$ of other players.

**Condition 2: Belief Consistency via Bayes' Rule.** Whenever possible, beliefs must be derived from the strategy profile $s^*$ and the prior $p$ using Bayes' rule. Specifically, if information set $h$ is reached with positive probability under $s^*$ and $p$, then

$$\mu(x, \theta \mid h) = \frac{\Pr[x, \theta \mid s^*, p]}{\sum_{(x', \theta') \in h} \Pr[x', \theta' \mid s^*, p]},$$

where $\Pr[x, \theta \mid s^*, p]$ is the probability of reaching node $x$ with type profile $\theta$ when players follow $s^*$ and Nature draws types according to $p$.

**Condition 3: Off-Path Belief Specification.** If information set $h$ is reached with zero probability under $s^*$ and $p$, beliefs $\mu(\cdot \mid h)$ can be specified arbitrarily, subject only to the requirement that they form a probability distribution.

**Condition 4: Strategy Optimality at All Histories.** The strategy profile $s^*$ must specify optimal actions at every information set, even those off the equilibrium path, given the beliefs $\mu$ and the continuation strategies.

Conditions 1 and 4 together enforce sequential rationality: no player wishes to deviate at any point in the game, even after unexpected moves. Condition 2 ensures that beliefs align with the equilibrium play wherever possible, respecting the laws of conditional probability. Condition 3 acknowledges the fundamental indeterminacy of beliefs off the equilibrium path, an indeterminacy that gives rise to equilibrium multiplicity and motivates refinements.

A signaling game provides the archetypal setting for Perfect Bayesian Equilibrium. The structure consists of two players: the Sender (player 1) and the Receiver (player 2). Nature draws the Sender's type $\theta \in \Theta$ according to a prior distribution $p \in \Delta(\Theta)$. The Sender observes $\theta$ and chooses a signal $m \in M$ from a message space. The Receiver observes $m$ but not $\theta$, forms beliefs $\mu(\theta \mid m)$ about the Sender's type, and chooses an action $a \in A$. Payoffs are $u_S(\theta, m, a)$ for the Sender and $u_R(\theta, m, a)$ for the Receiver.

A Perfect Bayesian Equilibrium in a signaling game specifies a Sender strategy $m^*(\theta)$, a Receiver strategy $a^*(m)$, and beliefs $\mu^*(\theta \mid m)$ such that:

1. For every type $\theta$, the signal $m^*(\theta)$ maximizes the Sender's expected payoff given the Receiver's strategy $a^*(m)$:
   $$m^*(\theta) \in \arg\max_{m \in M} u_S(\theta, m, a^*(m)).$$

2. For every message $m$, the action $a^*(m)$ maximizes the Receiver's expected payoff given beliefs $\mu^*(\theta \mid m)$:
   $$a^*(m) \in \arg\max_{a \in A} \sum_{\theta \in \Theta} \mu^*(\theta \mid m) \, u_R(\theta, m, a).$$

3. For every message $m$ sent with positive probability in equilibrium, beliefs are derived via Bayes' rule:
   $$\mu^*(\theta \mid m) = \frac{p(\theta) \cdot \mathbf{1}_{m^*(\theta) = m}}{\sum_{\theta' \in \Theta} p(\theta') \cdot \mathbf{1}_{m^*(\theta') = m}}.$$

4. For messages $m$ sent with zero probability, beliefs $\mu^*(\theta \mid m)$ are arbitrary.

The equilibrium structure distinguishes between **separating equilibria**, where different types send different messages ($m^*(\theta) \neq m^*(\theta')$ whenever $\theta \neq \theta'$), and **pooling equilibria**, where all types send the same message ($m^*(\theta) = m$ for all $\theta \in \Theta$). In a separating equilibrium, the Receiver learns the Sender's type perfectly, and beliefs place probability one on the true type: $\mu^*(\theta \mid m^*(\theta)) = 1$. In a pooling equilibrium, the Receiver learns nothing from the message, and beliefs coincide with the prior: $\mu^*(\theta \mid m) = p(\theta)$. Semi-separating or partially pooling equilibria, where some types pool and others separate, occupy the middle ground.

The canonical job-market signaling model, introduced by Spence, illustrates these concepts. A worker's productivity $\theta \in \{\theta_L, \theta_H\}$ with $0 < \theta_L < \theta_H$ is private information, drawn with probabilities $p(\theta_L) = q$ and $p(\theta_H) = 1 - q$. The worker chooses an education level $e \in [0, \infty)$, which is costly. The cost of education is $c(e, \theta)$, where $c$ is increasing and convex in $e$ and satisfies the single-crossing property: $\frac{\partial c}{\partial e}(e, \theta_L) > \frac{\partial c}{\partial e}(e, \theta_H)$ for all $e > 0$. This property captures the idea that education is less costly (in terms of effort, time, or money) for high-productivity workers. An employer observes $e$ but not $\theta$, forms beliefs $\mu(\theta \mid e)$, and offers a wage $w(e)$. In a competitive labor market, the wage equals the employer's expected value of the worker's productivity:

$$w(e) = \sum_{\theta \in \{\theta_L, \theta_H\}} \mu(\theta \mid e) \cdot \theta = \mu(\theta_L \mid e) \theta_L + \mu(\theta_H \mid e) \theta_H.$$

The worker's payoff is $w(e) - c(e, \theta)$, and the employer's payoff is $\theta - w(e)$, which is zero in equilibrium due to competition.

A separating equilibrium requires that the low-type chooses $e_L$ and the high-type chooses $e_H$ with $e_L < e_H$. Beliefs are $\mu(\theta_L \mid e_L) = 1$ and $\mu(\theta_H \mid e_H) = 1$, implying wages $w(e_L) = \theta_L$ and $w(e_H) = \theta_H$. For the high-type not to deviate to $e_L$, we require

$$\theta_H - c(e_H, \theta_H) \geq \theta_L - c(e_L, \theta_H).$$

For the low-type not to deviate to $e_H$, we require

$$\theta_L - c(e_L, \theta_L) \geq \theta_H - c(e_H, \theta_L).$$

Rearranging these inequalities yields

$$\theta_H - \theta_L \geq c(e_H, \theta_H) - c(e_L, \theta_H),$$

$$c(e_H, \theta_L) - c(e_L, \theta_L) \geq \theta_H - \theta_L.$$

The first inequality is the **incentive compatibility constraint** for the high-type, ensuring she prefers revealing her type. The second is the **incentive compatibility constraint** for the low-type, ensuring she does not mimic the high-type. These constraints are compatible when the cost difference between education levels is sufficiently larger for the low-type than for the high-type, a consequence of the single-crossing property.

A continuum of separating equilibria exists, parameterized by the education level $e_H$ of the high-type, provided $e_H$ satisfies both incentive constraints. The least-cost separating equilibrium, which minimizes the education level of the high-type subject to the constraints, sets the low-type's incentive constraint to bind:

$$c(e_H, \theta_L) - c(0, \theta_L) = \theta_H - \theta_L.$$

This equation implicitly defines $e_H$ as a function of the productivity difference and the cost function. The low-type chooses $e_L = 0$, as any positive education level would be wasteful when it does not affect wages. Despite the efficiency of the allocation conditional on the information asymmetry, the separating equilibrium exhibits a deadweight loss: the high-type invests in costly education solely to signal her productivity, not to enhance it.

Pooling equilibria also exist under certain conditions. Suppose both types choose the same education level $e_P$, so $m^*(\theta_L) = m^*(\theta_H) = e_P$. Beliefs remain at the prior: $\mu(\theta_H \mid e_P) = 1 - q$, and the wage is

$$w(e_P) = q \theta_L + (1 - q) \theta_H.$$

For this to be an equilibrium, both types must prefer $e_P$ over any deviation. Consider a deviation to education level $e \neq e_P$. Off-path beliefs $\mu(\theta \mid e)$ are not pinned down by Bayes' rule. If the employer believes that any deviation comes from the low-type—setting $\mu(\theta_L \mid e) = 1$ for $e \neq e_P$—then the wage after deviation is $w(e) = \theta_L$. The high-type's incentive constraint becomes

$$w(e_P) - c(e_P, \theta_H) \geq \theta_L - c(e, \theta_H) \quad \text{for all } e \neq e_P.$$

The low-type's constraint is

$$w(e_P) - c(e_P, \theta_L) \geq \theta_L - c(e, \theta_L) \quad \text{for all } e \neq e_P.$$

These constraints are satisfied if the pooling wage $w(e_P)$ is sufficiently attractive relative to the low wage $\theta_L$ and the cost of deviating is sufficiently high. However, such pooling equilibria often fail refinement tests, as we shall see.


## 3. High-Performance Optimization & Failure Modes

The multiplicity of Perfect Bayesian Equilibria in signaling games poses a challenge for predictive accuracy and prescriptive mechanism design. The freedom to specify off-path beliefs arbitrarily allows the analyst to sustain virtually any behavior as an equilibrium by threatening sufficiently pessimistic beliefs following deviations. This indeterminacy undermines the theory's empirical content and motivates the search for refinements that impose discipline on off-path beliefs.

**Forward induction** provides a conceptual foundation for such refinements. The principle asserts that when a player observes an unexpected action, she should interpret it as a rational choice made by some type for whom that action is beneficial, rather than as an irrational mistake or a random perturbation. This interpretation requires the observer to ask: which types would find this deviation profitable, even accounting for the subsequent play? If only one type (or a subset of types) could benefit, the observer should assign high probability to that type having deviated.

The **intuitive criterion**, formalized by Cho and Kreps in their seminal 1987 paper, operationalizes forward induction in signaling games. The criterion proceeds in two steps. First, for each off-path message $m$ and each type $\theta$, we ask whether there exists any belief $\mu \in \Delta(\Theta)$ that the Receiver could hold after observing $m$ such that type $\theta$ would prefer sending $m$ to sending her equilibrium message $m^*(\theta)$. If no such belief exists, we say that message $m$ is **equilibrium-dominated** for type $\theta$. Second, if message $m$ is equilibrium-dominated for all types in a set $\Theta_0 \subseteq \Theta$, the intuitive criterion requires that the Receiver's beliefs place zero probability on types in $\Theta_0$ after observing $m$: $\mu(\theta \mid m) = 0$ for all $\theta \in \Theta_0$.

Formally, let $(m^*, a^*, \mu^*)$ be a Perfect Bayesian Equilibrium. For an off-path message $m \neq m^*(\theta)$ for some type $\theta$, define the set of **best responses** the Receiver could take after observing $m$:

$$BR(m) = \left\{ a \in A : \exists \mu \in \Delta(\Theta) \text{ such that } a \in \arg\max_{a' \in A} \sum_{\theta'} \mu(\theta') u_R(\theta', m, a') \right\}.$$

This set includes all actions that the Receiver might rationally choose for some beliefs. Type $\theta$ finds message $m$ equilibrium-dominated if for all Receiver responses $a \in BR(m)$, the payoff from sending $m$ and receiving response $a$ is no better than the equilibrium payoff:

$$u_S(\theta, m, a) \leq u_S(\theta, m^*(\theta), a^*(m^*(\theta))) \quad \text{for all } a \in BR(m).$$

If this inequality holds strictly for all $a \in BR(m)$, message $m$ is **strictly equilibrium-dominated** for type $\theta$. The intuitive criterion requires that if message $m$ is equilibrium-dominated for all types except those in a set $\Theta_1$, then the Receiver must place all probability on $\Theta_1$: $\mu(\theta \mid m) = 0$ for $\theta \notin \Theta_1$ and $\mu(\theta \mid m) > 0$ only if $\theta \in \Theta_1$.

Returning to the job-market signaling model, consider a pooling equilibrium where both types choose education level $e_P = 0$ and the wage is $w(0) = q \theta_L + (1 - q) \theta_H$. Off-path beliefs assign $\mu(\theta_L \mid e) = 1$ for all $e > 0$, so any deviation results in wage $w(e) = \theta_L$. For the high-type, the equilibrium payoff is

$$U_H^* = q \theta_L + (1 - q) \theta_H - c(0, \theta_H) = q \theta_L + (1 - q) \theta_H.$$

Consider a deviation to education level $e > 0$. If the Receiver believes the deviation comes from the high-type and sets $\mu(\theta_H \mid e) = 1$, the wage is $w(e) = \theta_H$, yielding payoff

$$U_H(e) = \theta_H - c(e, \theta_H).$$

The high-type prefers this deviation if

$$\theta_H - c(e, \theta_H) > q \theta_L + (1 - q) \theta_H,$$

which simplifies to

$$q (\theta_H - \theta_L) > c(e, \theta_H).$$

Since $c(0, \theta_H) = 0$ and $c$ is continuous, for sufficiently small $e > 0$, this inequality holds. Now consider the low-type's payoff from deviating to the same $e$ under the belief $\mu(\theta_H \mid e) = 1$:

$$U_L(e) = \theta_H - c(e, \theta_L).$$

The low-type prefers this deviation if

$$\theta_H - c(e, \theta_L) > q \theta_L + (1 - q) \theta_H,$$

which simplifies to

$$q (\theta_H - \theta_L) > c(e, \theta_L).$$

By the single-crossing property, $c(e, \theta_L) > c(e, \theta_H)$ for all $e > 0$. Therefore, there exists a range of education levels $e$ such that

$$c(e, \theta_H) < q (\theta_H - \theta_L) < c(e, \theta_L).$$

For any such $e$, the high-type would benefit from deviating to $e$ if the Receiver responds with $\mu(\theta_H \mid e) = 1$, but the low-type would not. This implies that education level $e$ is equilibrium-dominated for the low-type but not for the high-type. The intuitive criterion therefore requires $\mu(\theta_L \mid e) = 0$, forcing $\mu(\theta_H \mid e) = 1$. But then the high-type has a profitable deviation, contradicting the equilibrium condition. The pooling equilibrium fails the intuitive criterion.

The application of the intuitive criterion often eliminates all but the least-cost separating equilibrium in signaling games, sharpening the theory's predictions. However, the criterion is not without limitations. It applies only to signaling games with a single Sender and does not extend straightforwardly to multi-sender settings or games with more complex information structures. Moreover, the criterion is silent on equilibria where multiple types pool, and it does not resolve all indeterminacies in dynamic games with incomplete information.

**Belief refinements** beyond the intuitive criterion include the **divinity criterion** and the **universal divinity criterion**, which impose progressively stronger restrictions on off-path beliefs. The divinity criterion compares the set of Receiver responses that make a deviation profitable for different types, assigning higher probability to types for whom the profitable response set is smaller. Universal divinity iterates this logic, requiring that if type $\theta$ has a smaller profitable-response set than type $\theta'$, then $\theta$ should be assigned probability one after the deviation. These refinements eliminate additional equilibria but increase the computational and conceptual complexity of equilibrium analysis.

In dynamic signaling games with multiple rounds of communication, the concept of **consistent beliefs** becomes more intricate. Players must update beliefs not only after observing actions but also after reaching information sets that involve multiple histories. The **weak sequential equilibrium** and **sequential equilibrium** concepts, introduced by Kreps and Wilson, impose consistency requirements that go beyond Perfect Bayesian Equilibrium by demanding that beliefs be limits of beliefs derived from completely mixed strategies (strategies that assign positive probability to every action). This trembling-hand interpretation ensures that even off-path information sets are reached with positive probability under some perturbation, allowing Bayes' rule to discipline beliefs everywhere.

The computational challenge of finding Perfect Bayesian Equilibria scales with the complexity of the type space and the game tree. In signaling games with continuous type spaces, equilibrium strategies are typically characterized by differential equations or variational inequalities, requiring numerical methods for solution. When types are multi-dimensional or the action space is large, the dimensionality of the optimization problem can become prohibitive. Algorithmic approaches include iterating best-response correspondences until convergence, solving systems of first-order conditions derived from Kuhn-Tucker optimality conditions, and employing homotopy or continuation methods to trace equilibrium paths as parameters vary.

Failure modes in Bayesian equilibrium analysis often stem from misspecification of the common prior or neglect of higher-order beliefs. The common prior assumption—that all players share the same probability distribution over types before the game begins—is a strong restriction. In practice, players may have divergent priors, reflecting different information sources, experiences, or biases. When priors differ, the Harsanyi construction breaks down, and equilibrium analysis requires an explicit model of how players form and update beliefs in the absence of a common foundation. The theory of **common knowledge** and **agreeing to disagree** results, due to Aumann, show that rational Bayesian updaters with common priors cannot agree to disagree: if their posterior beliefs become common knowledge, they must coincide. This result implies that persistent disagreement signals either non-common priors or failure of common knowledge, both of which complicate equilibrium analysis.

Another failure mode arises from the neglect of **out-of-equilibrium dynamics**. Perfect Bayesian Equilibrium is a static solution concept that does not model how players might learn or adapt over time. In repeated or evolutionary settings, players may experiment with different strategies, observe outcomes, and refine their beliefs and behaviors. The stability of equilibria under such dynamics depends on properties like the basin of attraction of the equilibrium under best-response or replicator dynamics. Equilibria that are unstable under plausible learning rules may be poor predictors of long-run behavior, even if they satisfy the formal equilibrium conditions.

The design of **robust mechanisms** under incomplete information requires careful attention to incentive compatibility constraints and participation constraints. A mechanism is a game form that implements a desired social choice function regardless of the realization of types, subject to the constraint that players truthfully reveal their types or play strategies consistent with their types. The **revelation principle** asserts that any outcome implementable in Bayesian Nash equilibrium by an arbitrary mechanism can be implemented by a direct mechanism in which players report their types truthfully. This principle reduces the mechanism design problem to the design of direct mechanisms satisfying incentive compatibility (truthful reporting is optimal) and individual rationality (participation is voluntary).

The **Vickrey-Clarke-Groves (VCG) mechanisms** achieve efficient allocation and truthful revelation in settings with quasi-linear preferences, where utility is transferable via monetary payments. In the VCG mechanism, each player reports her type, the mechanism selects an outcome that maximizes total welfare based on reported types, and each player receives a payment equal to her marginal contribution to total welfare. The payment structure ensures that each player internalizes the externality her report imposes on others, aligning private incentives with social efficiency. However, VCG mechanisms may run budget deficits or surpluses and may be vulnerable to collusion or false-name manipulations, limiting their applicability.

When efficiency is unattainable due to incentive constraints, the mechanism designer faces a **trade-off between allocative efficiency and informational rent extraction**. The **optimal auction** problem, solved by Myerson, characterizes the revenue-maximizing auction format when bidders have private valuations. The optimal mechanism distorts the allocation away from efficiency by sometimes awarding the object to a bidder who does not have the highest valuation, in order to reduce the informational rents captured by high-valuation bidders. The distortion is captured by the **virtual valuation** function, which adjusts the true valuation downward to account for the informational rent. The optimal mechanism allocates the object to the bidder with the highest non-negative virtual valuation and sets a reserve price below which the object is not sold.

The integration of Bayesian games into algorithmic game theory and computational mechanism design has generated powerful tools for automated market design, spectrum auctions, and online advertising. **Algorithmic mechanism design** combines game-theoretic equilibrium analysis with computational complexity theory, studying the computational feasibility of achieving incentive compatibility, efficiency, and other desiderata. Problems such as combinatorial auctions, where bidders have preferences over bundles of items, involve computational challenges even in the absence of strategic considerations; when combined with incomplete information and incentive constraints, the design and analysis of mechanisms require sophisticated algorithmic techniques, including linear programming relaxations, approximation algorithms, and online learning methods.

The practical deployment of Bayesian mechanisms requires empirical estimation of the type distribution, a task fraught with statistical and strategic challenges. Bidders or players may manipulate their behavior to influence the mechanism designer's beliefs about the distribution, a phenomenon known as **belief manipulation** or **prior manipulation**. Robust mechanism design addresses this issue by seeking mechanisms that perform well across a range of possible type distributions, rather than optimizing for a single prior. The **worst-case** or **max-min** approach designs mechanisms that maximize the worst-case welfare or revenue over a set of plausible priors, trading off average performance for robustness.

In conclusion, the theory of incomplete information and Bayesian games extends the Nash equilibrium framework to environments where players possess private information, enabling rigorous analysis of auctions, signaling, bargaining, and contracts. The Bayesian Nash equilibrium concept disciplines beliefs via common priors and Bayesian updating, while Perfect Bayesian Equilibrium enforces sequential rationality and belief consistency in dynamic settings. The multiplicity of equilibria in signaling games motivates refinement criteria such as the intuitive criterion, which apply forward induction reasoning to eliminate implausible equilibria. The computational and conceptual challenges of Bayesian equilibrium analysis—ranging from multi-dimensional optimization to higher-order belief modeling—remain active areas of research, with applications spanning economics, computer science, and engineering. Mastery of these tools equips the applied mathematician to design mechanisms, predict strategic behavior, and evaluate policies in the pervasive setting of asymmetric information.
