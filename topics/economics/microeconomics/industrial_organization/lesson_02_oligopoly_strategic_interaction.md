# Lesson 2: Oligopoly Models, Strategic Interaction, Game Theoretic Foundations

## 1. First-Principles Intuition & Invariants

The oligopoly problem sits at the precise intersection where market structure becomes endogenously strategic. Unlike perfect competition, where firms are price-takers operating in a mechanical equilibrium, or monopoly, where a single firm faces a passive demand curve, oligopolistic markets force firms into direct strategic awareness of one another. Each firm recognizes that its own actions—price changes, capacity decisions, product innovations—will provoke reactions from competitors, and these reactions feed back into the firm's own profit optimization calculus. This recursive interdependence is the defining characteristic of oligopoly, and it cannot be analyzed through the lens of parametric optimization alone.

The classical competitive model assumes that firms maximize profit by equating marginal cost to price, treating price as an exogenous parameter. But in oligopoly, price is endogenous to the collective behavior of the industry. Similarly, the monopoly model treats the entire demand curve as parametric from the firm's perspective—the monopolist knows that if it raises price, quantity demanded falls along the demand curve, but it does not anticipate defensive responses from rivals (because there are none). Oligopoly breaks both of these frameworks. The firm must construct a *conjectural demand curve* that embodies its beliefs about how rivals will respond to its own strategic moves.

This is where game theory enters industrial organization as more than mathematical convenience—it becomes epistemic necessity. A game-theoretic framework formalizes the structure of strategic interaction: a finite set of rational players, each with a strategy space (the set of feasible actions available), a payoff function (profit, revenue, market share, or any objective the firm pursues), and mutual knowledge that all players are rational and strategically aware. The solution concept of Nash equilibrium emerges as the natural prediction of play: a configuration of strategies where no single firm can unilaterally improve its payoff by deviating, given the strategies of all other firms.

The beauty—and the analytical power—of Nash equilibrium is that it brackets the infinite regress of strategic reasoning. Without such a bracketing device, firms would face an impossible cognitive burden: I must predict what my rival will do, which requires predicting what my rival thinks *I* will do, which requires predicting what my rival thinks I think *they* will do, and so forth. Nash equilibrium solves this by identifying a fixed point: a configuration where each firm's strategy is a best response to the other firms' strategies, and vice versa. At equilibrium, no firm has incentive to deviate unilaterally, so the configuration is self-sustaining.

The practical consequence is profound. Different assumptions about the *dimension of competition*—whether firms compete on quantity (Cournot) or price (Bertrand), whether they move simultaneously or sequentially (Stackelberg), whether capacity constraints bite, whether products are homogeneous or differentiated—yield radically different equilibrium predictions. The same industry can exhibit vastly different profitability, markup structure, and welfare properties depending on which strategic variable firms actually use as their control lever. This is why the choice of model is not a technical abstraction; it is an empirical claim about the organization of the market.

To ground this intuition concretely: consider two competing airlines on the same route. One model assumes they simultaneously choose flight frequencies (capacity/quantity), with price determined residually by the market's inverse demand. Another model assumes they simultaneously set ticket prices, with customers then choosing among carriers subject to capacity constraints. A third model assumes one airline moves first (sets its frequency and price), then the other airline observes this and responds optimally. Each model delivers different equilibrium predictions about pricing, frequency, and profitability. The analyst's job is to determine which model captures the actual competitive structure of the market, which requires deep institutional knowledge of how decisions are made in practice.

## 2. Core Architecture & Mechanics

### 2.1 The Cournot Model: Quantity Competition

The Cournot model begins with a stark simplification: firms compete on quantity, price is determined by an inverse demand function, and all firms move simultaneously without observing rivals' choices before acting. This is the natural framework when firms face capacity constraints that cannot be costlessly adjusted, when output is produced before demand is observed (as in agricultural or mineral extraction industries), or when the time scale of production decisions is longer than the time scale of price adjustments.

Formally, consider an industry with $n$ firms, each producing a homogeneous good. Let $q_i$ denote the quantity produced by firm $i$, and $Q = \sum_{j=1}^{n} q_j$ the aggregate industry quantity. The inverse demand function is $p(Q) = a - bQ$, where $a > 0$ is the demand intercept and $b > 0$ is the slope parameter. Each firm has constant marginal cost $c$, with $c < a$ (otherwise no production occurs). Firm $i$'s profit is:

$$\pi_i(q_i, q_{-i}) = [p(Q) - c] q_i = [a - b(q_i + \sum_{j \neq i} q_j) - c] q_i$$

where $q_{-i}$ denotes the vector of quantities chosen by all firms other than $i$.

To find the Nash equilibrium, we solve for each firm's best response function. Taking the first-order condition with respect to $q_i$:

$$\frac{\partial \pi_i}{\partial q_i} = a - c - 2bq_i - b\sum_{j \neq i} q_j = 0$$

Rearranging yields the best response function:

$$BR_i(q_{-i}) = \frac{a - c - b\sum_{j \neq i} q_j}{2b}$$

This is the crucial object in Cournot competition: given the aggregate quantity produced by all rivals, firm $i$ chooses the quantity that maximizes its profit. Notice the structure: firm $i$ views the quantity choices of rivals as parameters (conjecturally), and optimizes against this backdrop. As rivals produce more, firm $i$'s best response is to produce less, because the resulting market price falls and the marginal revenue from selling additional units declines.

By symmetry, all firms face identical cost and demand conditions, so in equilibrium all firms produce the same quantity: $q_i = q^*$ for all $i$. Substituting into the best response function and solving for the symmetric Nash equilibrium:

$$q^* = \frac{a - c}{b(n+1)}$$

The equilibrium price is:

$$p^* = a - bQ^* = a - b \cdot n \cdot q^* = a - \frac{nb(a-c)}{b(n+1)} = \frac{a + nc}{n+1}$$

Several properties emerge immediately. As the number of firms $n$ increases, each firm produces less ($q^*$ decreases), and the price falls toward marginal cost: $\lim_{n \to \infty} p^* = c$. In the limit, Cournot competition replicates perfect competition, where price equals marginal cost and economic profit is zero. Conversely, when $n = 1$ (monopoly), $q^* = \frac{a-c}{2b}$ and $p^* = \frac{a+c}{2}$, which is the familiar monopoly outcome of producing where marginal revenue equals marginal cost.

For the duopoly case ($n=2$), we have $q^* = \frac{a-c}{3b}$ and $p^* = \frac{a+2c}{3}$, illustrating an intermediate result between monopoly and competition. Each firm earns profit:

$$\pi^* = (p^* - c)q^* = \frac{a-c}{3} \cdot \frac{a-c}{3b} = \frac{(a-c)^2}{9b}$$

Comparing to monopoly profit, $\pi_m = \frac{(a-c)^2}{8b}$, we see that duopoly profit is less than monopoly profit but significantly more than the competitive profit of zero. This profit ladder—where profit decreases as the number of competitors increases—is robust across most oligopoly models, though the rate of decrease depends on the specific competitive mechanism.

The Cournot model's empirical relevance rests on the capacity constraint intuition. Consider crude oil production: OPEC members must invest in extraction capacity, and once installed, capacity is costly to expand or contract. Production decisions are made at quarterly or annual intervals, reflecting geological and engineering realities. Price adjusts quickly in response to global supply and demand, but production capacity adjusts slowly. This creates a Cournot-like environment where firms are effectively choosing quantities (subject to capacity), and price is the residual market-clearing variable.

### 2.2 The Bertrand Model: Price Competition

The Bertrand model inverts the Cournot logic: firms compete on price, and quantity is determined by demand. Consumers have perfect information about prices and buy from the cheapest supplier. If products are perfectly homogeneous, the firm with the lowest price captures the entire market demand; if prices are equal, market demand is split equally among tied firms.

Formally, firm $i$ sets price $p_i$, and its quantity is determined by:

$$q_i(p_i, p_{-i}) = \begin{cases} \frac{D(p_i)}{n} & \text{if } p_i < p_j \text{ for all } j \neq i \\ 0 & \text{if } p_i > \min_{j \neq i} p_j \\ \frac{D(p_i)}{m} & \text{if } p_i = \min_{j} p_j \text{ and } m \text{ firms tie for lowest price} \end{cases}$$

where $D(p_i)$ is the market demand at price $p_i$.

Under these demand conditions, the Nash equilibrium is surprisingly stark: all firms set price equal to marginal cost, $p^* = c$. To see why, suppose $p_i > c$ for some firm $i$. Then firm $i$ can profitably undercut all rivals by setting $p_i' = p_i - \epsilon$ for arbitrarily small $\epsilon > 0$, capturing the entire market demand at a price above marginal cost. Firm $i$ will always do this, which means any price above marginal cost cannot be an equilibrium. Conversely, if $p_i = c$, then firm $i$ earns zero profit, and cannot improve by deviating because any price below $c$ yields negative profit, and any price above $c$ is immediately undercut by rivals who capture the market.

This is the celebrated Bertrand paradox: with only two firms and homogeneous products, price competition yields the competitive outcome (price equals marginal cost, zero economic profit), despite there being only two competitors. The monopolist earns strictly positive profit; the Bertrand duopolist earns zero. This discontinuous jump in the competitive outcome as the number of competitors increases from one to two is jarring and empirically unintuitive for many industries.

The resolution of the Bertrand paradox lies in recognizing that the model's stark assumptions are often violated in practice. If firms face capacity constraints, a firm cannot infinitesimally undercut rivals without limit. If products are differentiated rather than homogeneous, consumers do not switch entirely to the lowest-priced competitor but rather exhibit price elasticity, creating a downward-sloping residual demand curve for each firm. If there are fixed costs of price-setting (menu costs), firms cannot adjust prices costlessly. If demand is stochastic and capacity is fixed, a low-priced firm may be unable to satisfy all demand, and customers turn to higher-priced rivals. Each of these extensions moves the Bertrand outcome toward more realistic price markups and profitability.

For concreteness, consider the case of differentiated products. Suppose consumer preferences are distributed uniformly on a line segment from 0 to 1, and two firms locate at positions 0 and 1 (the extreme endpoints). Consumers have quadratic transportation costs: a consumer at location $x$ incurs disutility $t(x - 0)^2$ to buy from firm 1 (at position 0) and $t(1-x)^2$ to buy from firm 2 (at position 1). The utility from purchasing from firm $i$ at price $p_i$ is $u - p_i - \text{transportation cost}$, where $u$ is the baseline utility. A consumer at position $x$ is indifferent between the two firms when:

$$u - p_1 - tx^2 = u - p_2 - t(1-x)^2$$

Solving for the indifferent consumer's position $x^*$:

$$x^* = \frac{1}{2} + \frac{p_2 - p_1}{2t}$$

Consumers to the left of $x^*$ buy from firm 1; consumers to the right buy from firm 2. Demand for firm 1 is $q_1(p_1, p_2) = x^*$; demand for firm 2 is $q_2(p_1, p_2) = 1 - x^*$. Firm $i$'s profit is:

$$\pi_i = (p_i - c) q_i(p_1, p_2)$$

Taking the first-order condition for firm 1 with respect to $p_1$:

$$\frac{\partial \pi_1}{\partial p_1} = q_1 + (p_1 - c) \frac{\partial q_1}{\partial p_1} = \left(\frac{1}{2} + \frac{p_2 - p_1}{2t}\right) + (p_1 - c) \left(-\frac{1}{2t}\right) = 0$$

By symmetry, in the Nash equilibrium $p_1^* = p_2^* = p^*$. Substituting:

$$\frac{1}{2} - \frac{1}{2t}(p^* - c) = 0$$

$$p^* = c + t$$

The equilibrium price now exceeds marginal cost by the parameter $t$, which measures the intensity of product differentiation. As products become more differentiated ($t$ increases), firms have more pricing power; as $t \to 0$ (products become homogeneous), price approaches marginal cost, recovering the Bertrand result. Each firm earns profit:

$$\pi^* = (p^* - c) \cdot \frac{1}{2} = \frac{t}{2}$$

This is a positive profit with only two competitors, which is empirically much more plausible than the Bertrand paradox. Product differentiation mitigates price competition by segmenting the market: each firm captures consumers for whom its product offers the best value, but some consumers value the alternative product enough that they will pay a premium rather than incur switching costs.

### 2.3 The Stackelberg Model: Sequential Competition

The Stackelberg model introduces asymmetry by assuming one firm (the leader) moves first, observing this choice, the other firm (the follower) responds optimally. This captures markets where one firm has a first-mover advantage, whether through historical precedence, technological leadership, or simply institutional timing.

Consider the Stackelberg quantity-competition model. Firm 1 (the leader) chooses $q_1$, and firm 2 (the follower) observes $q_1$ and chooses $q_2$. To solve this by backward induction, we first determine firm 2's best response to any choice of $q_1$ by firm 1. This is identical to the best response function in Cournot:

$$BR_2(q_1) = \frac{a - c - bq_1}{2b}$$

Anticipating this, firm 1 solves:

$$\max_{q_1} \pi_1(q_1) = [a - b(q_1 + BR_2(q_1)) - c] q_1$$

Substituting the best response:

$$\pi_1(q_1) = \left[a - b\left(q_1 + \frac{a - c - bq_1}{2b}\right) - c\right] q_1 = \left[\frac{a - c}{2} - \frac{bq_1}{2}\right] q_1$$

Taking the derivative:

$$\frac{d\pi_1}{dq_1} = \frac{a - c}{2} - bq_1 = 0$$

$$q_1^* = \frac{a - c}{2b}$$

Firm 2's best response is:

$$q_2^* = \frac{a - c - b \cdot \frac{a-c}{2b}}{2b} = \frac{(a-c)/2}{2b} = \frac{a - c}{4b}$$

Total output is:

$$Q^* = q_1^* + q_2^* = \frac{a-c}{2b} + \frac{a-c}{4b} = \frac{3(a-c)}{4b}$$

Equilibrium price is:

$$p^* = a - bQ^* = a - \frac{3(a-c)}{4} = \frac{a + 3c}{4}$$

Comparing the outcomes: the Stackelberg leader produces $\frac{a-c}{2b}$ versus the Cournot firm's $\frac{a-c}{3b}$ (for duopoly). The leader produces more because it internalizes the follower's best response, recognizing that if it produces more, the follower will produce less. The follower produces less than in Cournot (it produces $\frac{a-c}{4b}$ versus $\frac{a-c}{3b}$). Industry price falls below the Cournot level, and total output rises. The leader earns higher profit than in Cournot, while the follower earns lower profit. This is the first-mover advantage: by moving first, the leader can commit to a quantity that softens competition and secures a larger market share.

The Stackelberg model's empirical relevance depends on whether firms actually move sequentially. In some industries—particularly those with long production lead times, investment in capacity, or regulatory constraints—firms do make announcements or capacity commitments that are observed by rivals before they respond. Airlines expanding capacity on a route, pharmaceutical firms launching pipeline announcements, or real estate developers announcing new projects all have a Stackelberg flavor: the first mover's action is observable and partly irreversible, and rivals respond in light of this commitment.

### 2.4 Capacity Constraints and Limit Pricing

The interaction between price and quantity competition becomes particularly acute when firms face capacity constraints that cannot be costlessly adjusted. Suppose a firm must first invest in capacity at fixed cost $F$ per unit of capacity, and then sets a price. If capacity is abundant relative to demand at the equilibrium price, the capacity constraint is slack, and the firm's pricing decision is unconstrained by capacity. But if demand at the unconstrained optimal price exceeds capacity, the firm is effectively rationed by its capacity, and price must rise to clear the market.

This introduces a strategic consideration: a firm might invest in excess capacity not primarily to produce, but as a *commitment device* that deters entry or softens competition from incumbents. This is the limit pricing logic: by investing in capacity beyond what would be profit-maximizing in the short run, the firm signals to potential entrants that it will aggressively defend its market share if entry occurs. Facing this implicit threat, potential entrants rationally stay out, allowing the incumbent to enjoy higher profit in the long run than it could achieve if threatened by entry.

Formally, consider a simple two-stage game. In stage 1, the incumbent firm chooses capacity $K$, incurring fixed cost $F$ per unit. In stage 2, knowing the incumbent's capacity choice, a potential entrant decides whether to enter. If the entrant stays out, the incumbent is a monopolist with capacity constraint $K$, and chooses price to maximize $(p - c) \min(D(p), K)$. If the entrant enters, it incurs its own fixed cost of capacity and the two firms compete (either as Cournot or Bertrand competitors, depending on the model). The entrant enters if and only if its expected profit exceeds its sunk entry cost.

The incumbent's capacity choice must make entry unprofitable. If the incumbent commits to high capacity $K^*$ such that even after entry, the resulting Cournot or Bertrand equilibrium price is below the entrant's break-even level, then entry is deterred. This limit price is set not because it is profit-maximizing in the absence of entry threats, but precisely because the threat of entry would make the incumbent worse off if it did not credibly commit to aggressive post-entry behavior.

The welfare implications are subtle. From the consumer's perspective, limit pricing may be beneficial in the short run (lower prices due to aggressive capacity investment) but harmful in the long run if it forecloses competition and allows the incumbent to sustain high prices once entry threats recede. Antitrust authorities have long grappled with this tension: is limit pricing a legitimate competitive strategy or an anticompetitive exclusionary practice?

### 2.5 Product Differentiation and the Salop Circle Model

Product differentiation fundamentally alters the nature of price competition by creating "market segments" where each firm has local monopoly power. When products are differentiated, a firm's demand is not infinitely elastic at prices slightly above rivals' prices; instead, consumers view the products as imperfect substitutes, and a price increase causes gradual rather than discrete loss of market share.

The Salop circle model provides a tractable framework for analyzing this. Imagine consumers uniformly distributed on a circle of circumference 1. Each consumer has a most-preferred product location (a point on the circle) and incurs transportation cost $t$ per unit distance traveled. Firms locate at distinct points on the circle and set prices; each consumer buys from the closest firm (lowest delivered price, including transportation cost).

With $n$ firms equally spaced on the circle, the distance between adjacent firms is $\frac{1}{n}$. Consider a consumer located exactly at the midpoint between two adjacent firms. This consumer is indifferent between the two firms if their prices are equal. If firm $i$ sets price $p_i$ and firm $j$ sets price $p_j$, the indifferent consumer is located at distance $d$ from firm $i$ such that:

$$p_i + td = p_j + t\left(\frac{1}{n} - d\right)$$

Solving for $d$:

$$d = \frac{1}{2n} + \frac{p_j - p_i}{2t}$$

Firm $i$'s demand consists of consumers within distance $d$ on one side and distance $\frac{1}{n} - d$ on the other side (by symmetry with the firm on the other side). Total demand for firm $i$ is $q_i = \frac{1}{n}$, independent of prices, if all firms charge the same price.

In the symmetric Nash equilibrium, all firms charge the same price $p^*$ and each serves $\frac{1}{n}$ of the market. Taking the first-order condition for firm $i$'s profit (accounting for the derivative of its demand with respect to price, which equals $\frac{1}{t}$):

$$\frac{\partial \pi_i}{\partial p_i} = q_i + (p_i - c) \frac{\partial q_i}{\partial p_i} = \frac{1}{n} + (p^* - c) \left(-\frac{1}{t}\right) = 0$$

Solving for the equilibrium price:

$$p^* = c + \frac{t}{n}$$

As $n$ increases (more firms enter, product space becomes more crowded), the equilibrium price falls toward marginal cost. Each firm earns profit $\pi^* = (p^* - c) \cdot \frac{1}{n} = \frac{t}{n^2}$. The profit per firm declines with $n$, which determines the long-run free-entry equilibrium: firms enter until profit equals their fixed entry cost $F$, yielding $n^* = \sqrt{\frac{t}{F}}$.

This free-entry equilibrium is socially inefficient. The competitive outcome would be $p^* = c$, but the Salop model yields $p^* = c + \frac{t}{n^*}$. The markup reflects "excess entry": firms enter until their profit equals fixed costs, but each firm ignores the competitive externality it imposes on existing firms—by entering, a new firm reduces the market share and profit of incumbents. The socially optimal number of firms would balance the consumer benefit of more product variety against the fixed cost of entry; the market equilibrium has excessive entry relative to the social optimum.

### 2.6 Repeated Games and Collusion

The models analyzed thus far are one-shot games: firms interact once, choose their strategies simultaneously or sequentially, and the game ends. But many real markets feature repeated interaction: firms meet the same competitors repeatedly over time, and actions taken today affect market conditions and competitors' behavior tomorrow.

The infinitely repeated game is the standard framework. In each period $t = 1, 2, 3, \ldots$, firms choose actions (quantities or prices), payoffs are realized, and all firms observe the outcome before moving to the next period. Firms value future payoffs at discount factor $\delta \in [0, 1)$, where $\delta$ measures patience: $\delta = 1$ means the firm cares equally about all future periods; $\delta = 0$ means the firm only cares about the current period.

The folk theorem is the central result: in an infinitely repeated game, any feasible payoff vector that dominates the one-shot Nash equilibrium payoff can be sustained as an equilibrium under some trigger strategy. A trigger strategy specifies cooperatively favorable behavior (e.g., collusive pricing) as long as all firms comply, and punishment (e.g., a reversion to one-shot Nash equilibrium play) if any firm deviates.

For concreteness, consider collusion in a Cournot duopoly. The one-shot Nash equilibrium yields each firm profit $\pi_N$. The monopoly outcome (joint quantity-maximization) yields total profit that could be split evenly to give each firm profit $\pi_M > \pi_N$. Can the two firms sustain the monopoly outcome through repeated interaction?

The firms propose the following trigger strategy: each firm produces the monopoly quantity $q_M = \frac{a-c}{4b}$ (half the joint monopoly quantity) in each period, as long as both firms do the same. If either firm deviates from $q_M$, both firms revert to the one-shot Nash equilibrium quantity $q_N = \frac{a-c}{3b}$ forever.

A firm considering deviation in period $t$ trades off: today, I can deviate to some quantity that increases my current payoff (because I capture some market share stolen from my compliant rival), but tomorrow and forever, I revert to the harsh punishment of Nash equilibrium play. The firm's discounted lifetime payoff from cooperation is:

$$\pi_{\text{coop}} = \frac{\pi_M}{1 - \delta}$$

The firm's payoff if it deviates in period $t$ is the one-period deviation payoff $\pi_d$ (the profit from best-responding to the rival's monopoly quan
