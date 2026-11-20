# Lesson 2: Health Insurance Theory

## 1. First-Principles Intuition & Invariants

The demand for health insurance emerges from a fundamental asymmetry between human welfare and the randomness of health outcomes. Unlike the purchase of a deterministic good—where a consumer pays a known price for a known quantity of utility—health insurance involves the exchange of a certain payment (premium) today for uncertain, contingent payoffs tomorrow. This inversion of certainty creates the entire theoretical edifice of health insurance economics, and understanding it requires us to begin with the consumer's primitive relationship to risk itself.

Consider a simple thought experiment. A consumer faces two possible health states: healthy (probability $p$) or ill (probability $1-p$). If ill, she incurs medical costs $M$, which we can interpret as lost income, required expenditures on treatment, or reduced consumption capacity. If healthy, she incurs zero medical costs. Without insurance, her consumption in the healthy state is $W$ (her total wealth), and in the ill state it is $W - M$. She faces a lottery: with probability $p$ she consumes $W$, and with probability $1-p$ she consumes $W - M$.

Now, an insurance company offers a contract: pay a premium $\pi$ today, and if you become ill, the insurer will reimburse you $I$ (the indemnity). After purchasing insurance, the consumer's consumption becomes certain: in both states, she consumes $W - \pi$ in the healthy state and $W - M + I - \pi$ in the ill state. If the insurance is actuarially fair—meaning the expected cost to the insurer equals the premium charged—then $\pi = (1-p)I$. Under full insurance ($I = M$), the consumer's consumption is equalized across both states to $W - (1-p)M$.

The critical question is: why would a risk-averse consumer be willing to pay more than the expected value of potential losses to obtain insurance? The answer lies in the concavity of her utility function. Expected Utility Theory, axiomatized by von Neumann and Morgenstern, posits that a rational consumer chooses among risky alternatives by maximizing the probability-weighted sum of utilities across states. Formally, if $u(c)$ denotes utility from consumption $c$, the consumer's expected utility without insurance is:

$$E[U_{\text{no insurance}}] = p \cdot u(W) + (1-p) \cdot u(W - M)$$

With actuarially fair full insurance, expected utility becomes:

$$E[U_{\text{insurance}}] = p \cdot u(W - (1-p)M) + (1-p) \cdot u(W - (1-p)M) = u(W - (1-p)M)$$

If the utility function exhibits diminishing marginal utility—that is, $u''(c) < 0$, indicating concavity—then Jensen's inequality guarantees that the expected utility with insurance exceeds the expected utility without insurance. The intuition is immediate: a concave function places more weight on lower arguments. Since insurance reduces consumption volatility by equalizing consumption across states, it increases overall welfare by concentrating consumption at a higher level on average.

This foundational insight—that risk aversion (captured by concavity of the utility function) generates demand for insurance—is the bedrock upon which the entire theory of health insurance rests. However, real insurance markets deviate from this idealized actuarially fair scenario in three critical dimensions. First, insurers are not nonprofits; they charge administrative costs and require profit margins, making premiums exceed expected claims. Second, insurers lack perfect information about consumers' true risk profiles, creating asymmetric information problems. Third, the act of purchasing insurance may alter consumer behavior in ways that increase claims—the moral hazard problem. These three deviations—loading costs, adverse selection, and moral hazard—define the practical architecture of health insurance economics.

The problem of adverse selection warrants particular emphasis because it fundamentally restructures how insurance markets equilibrate. Suppose insurers cannot distinguish between high-risk and low-risk consumers; they know only the population distribution of risks. High-risk consumers have probability $p_H$ of illness and low-risk consumers have probability $p_L$, with $p_H > p_L$. If both groups exist in proportions $\alpha$ and $1-\alpha$ respectively, the population-average risk is $\bar{p} = \alpha p_H + (1-\alpha)p_L$. If the insurer charges a single premium based on average risk, that premium will be actuarially fair for the average consumer but unfair for each type individually: high-risk consumers receive favorable terms (paying less than their expected claims) and low-risk consumers receive unfavorable terms (paying more than their expected claims).

This creates a sorting incentive. Low-risk consumers, facing a premium that exceeds their expected losses, may choose to remain uninsured, purchasing insurance only if the premium reflects their true low risk. High-risk consumers, facing a premium subsidized by low-risk pooling, eagerly purchase coverage. As low-risk consumers exit the pool, the insurer's claims experience deteriorates, forcing the premium upward. This dynamic can trigger an unraveling: higher premiums induce more low-risk exits, further deteriorating the pool, in a feedback loop that can eventually result in market collapse (the classic Akerlof "lemons market" problem applied to health insurance).

The existence of this adverse selection externality—where one consumer's decision to exit the pool imposes a negative externality on remaining consumers by worsening the risk pool—is not merely a theoretical curiosity. It shapes the entire regulatory and institutional architecture of real-world health insurance markets. Community rating regulations (which mandate that insurers charge the same premium regardless of health status) attempt to prevent adverse selection by making it unprofitable for high-risk consumers to self-select into higher premiums and for low-risk consumers to self-select into lower-risk pools. Experience rating (where premiums reflect claims history) operates in the opposite direction, explicitly allowing differentiation. Understanding when each is optimal requires careful analysis of the trade-offs between pooling efficiency and distributional equity.

Moral hazard represents an equally profound departure from the idealized insurance contract. When a consumer purchases insurance, the financial consequences of illness are reduced. If insurance covers a fraction $\gamma$ of medical costs (so the out-of-pocket cost is $(1-\gamma)M$), the consumer faces a lower effective price for medical care. Economic theory predicts that lower prices induce higher quantity demanded—a basic demand curve principle. Thus, moral hazard manifests as increased medical utilization when insured. More subtly, moral hazard can also reduce the consumer's incentive to engage in preventive health behaviors. If the cost of illness is already covered by insurance, why invest in costly prevention?

The insurer's response to moral hazard is contractual design. Rather than offering full insurance (which maximizes moral hazard), insurers introduce cost-sharing mechanisms: deductibles (the consumer pays the first $D$ dollars of medical costs), coinsurance (the consumer pays a fraction $\gamma$ of costs), and copayments (fixed fees per service). These mechanisms preserve consumer incentives to economize on care while providing partial risk protection. However, they also expose consumers to residual risk, creating a tension between risk-pooling efficiency and incentive alignment that cannot be fully resolved. The optimal insurance contract balances these competing forces by choosing cost-sharing parameters that maximize consumer welfare subject to the insurer's zero-profit constraint (or profit target).

## 2. Core Architecture & Mechanics

The mechanics of health insurance equilibrium can be rigorously formulated through the lens of adverse selection and moral hazard within the context of competitive markets. We will develop the canonical model in stages, beginning with the frictionless baseline and then introducing information asymmetries and behavioral responses.

### The Baseline Framework: Perfect Information and Actuarially Fair Insurance

Suppose there are two consumer types: high-risk ($H$) and low-risk ($L$). Each type has probability of illness $p_i$ (where $i \in \{H, L\}$ and $p_H > p_L$), illness cost $M$, and wealth $W$. Assume the population consists of a fraction $\alpha$ of high-risk consumers and $1-\alpha$ of low-risk consumers. Each consumer has a concave utility function $u(c)$ with $u'(c) > 0$ and $u''(c) < 0$.

If insurers observe types perfectly, competitive markets will offer type-specific actuarially fair insurance contracts. For type $i$, the equilibrium premium is:

$$\pi_i = p_i M$$

With full coverage ($I_i = M$), each consumer's consumption is equalized across states at $W - p_i M$. Expected utility for type $i$ under full coverage is:

$$E[U_i^*] = u(W - p_i M)$$

This is the first-best outcome where each consumer is fully insured at an actuarially fair rate. The distribution of risk across types does not impede market function; instead, it leads to perfect actuarial price discrimination.

### Pooling Equilibrium Under Adverse Selection

Now suppose insurers cannot distinguish between types. They observe only that the population average risk is $\bar{p} = \alpha p_H + (1-\alpha)p_L$. In a competitive market, uninformed insurers will offer a single contract with premium:

$$\pi_{\text{pool}} = \bar{p} M$$

Under this pooled contract, both types face the same premium. However, this premium is unfavorable for low-risk consumers (they pay more than their expected claims $p_L M$) and favorable for high-risk consumers (they pay less than their expected claims $p_H M$). Specifically:

$$\pi_{\text{pool}} - p_L M = (\alpha p_H + (1-\alpha)p_L)M - p_L M = \alpha(p_H - p_L)M > 0$$

Low-risk consumers overpay by $\alpha(p_H - p_L)M$, an amount that increases with the proportion of high-risk consumers in the population and the difference in their risks.

Whether low-risk consumers choose to buy the pooled insurance or remain uninsured depends on their reservation price. The consumer remains uninsured if:

$$E[U_{\text{uninsured}}] \geq E[U_{\text{pooled}}]$$

That is, if:

$$p_L u(W) + (1-p_L)u(W - M) \geq u(W - \pi_{\text{pool}})$$

Intuitively, if the pooled premium is sufficiently high relative to a low-risk consumer's expected medical costs, the guaranteed consumption loss from the premium outweighs the benefit of risk reduction. This defines the critical threshold premium $\pi_L^*$ at which a low-risk consumer is indifferent between insurance and the uninsured lottery:

$$p_L u(W) + (1-p_L)u(W - M) = u(W - \pi_L^*)$$

If $\pi_{\text{pool}} > \pi_L^*$, low-risk consumers exit the insurance market. The resulting adverse selection unraveling proceeds as follows: as low-risk consumers leave, the pool's average risk increases, forcing the remaining premium $\pi_{\text{pool}}'$ higher. If this new premium exceeds the reservation price of the remaining low-risk consumers (those for whom $\pi_L^* > \pi_{\text{pool}}'$ but only barely), they too exit. This iterative process can culminate in complete market unraveling, where only high-risk consumers remain, paying the pooled premium $\pi_H = p_H M$.

Formally, a pooling equilibrium (where both types purchase insurance at the same premium) exists only if low-risk consumers' reservation price exceeds the pooled premium:

$$\pi_{\text{pool}} \leq \pi_L^*$$

This condition is equivalent to:

$$(\alpha p_H + (1-\alpha)p_L)M \leq \pi_L^*$$

The existence of a pooling equilibrium depends on the distribution of types. If the low-risk population is sufficiently large (high $1-\alpha$), the cross-subsidy from low-risk to high-risk is small, and the pooled premium remains near low-risk expected claims, making the pooled contract attractive even to low-risk consumers.

### Separating Equilibrium Under Adverse Selection

When a pooling equilibrium cannot exist, markets may exhibit a separating equilibrium, where high-risk and low-risk consumers purchase different contracts and thus self-identify their type through their choice. The canonical separating equilibrium is characterized by two contracts: one designed to appeal primarily to high-risk consumers (full insurance at a high premium) and one designed to appeal to low-risk consumers (partial insurance at a lower premium).

Denote the contract offered to high-risk consumers as $(I_H, \pi_H)$ and the contract for low-risk consumers as $(I_L, \pi_L)$. For a separating equilibrium to exist, two constraints must be satisfied. First, each type must prefer their assigned contract to the other (the self-selection constraints):

$$p_H u(W - \pi_H + I_H) + (1-p_H)u(W - \pi_H) \geq p_H u(W - \pi_L + I_L) + (1-p_H)u(W - \pi_L)$$

$$p_L u(W - \pi_L + I_L) + (1-p_L)u(W - \pi_L) \geq p_L u(W - \pi_H + I_H) + (1-p_L)u(W - \pi_H)$$

The first inequality ensures high-risk consumers prefer the $H$-contract; the second ensures low-risk consumers prefer the $L$-contract. Second, each contract must break even (competitive zero-profit conditions):

$$\pi_H = p_H I_H$$

$$\pi_L = p_L I_L$$

The high-risk contract can offer full coverage ($I_H = M$) at an actuarially fair premium $\pi_H = p_H M$, since high-risk consumers have no incentive to understate their risk. However, if the low-risk contract also offered full coverage at $\pi_L = p_L M$, high-risk consumers would strictly prefer it (since $p_L M < p_H M$), violating the self-selection constraint.

The solution is to distort the low-risk contract by reducing coverage below the first-best level. The low-risk contract offers partial coverage $(I_L, \pi_L)$ with $I_L < M$ and $\pi_L = p_L I_L$. The indemnity $I_L$ is set precisely at the level that makes high-risk consumers indifferent between the two contracts. This is called the *binding incentive compatibility constraint*. At the margin, high-risk consumers are willing to pay the premium $\pi_H$ for full coverage rather than purchase the limited coverage $(I_L, \pi_L)$.

The separating equilibrium exhibits a striking inefficiency: low-risk consumers are underinsured (exposed to residual risk) relative to the first-best, not because of moral hazard, but purely to deter high-risk consumers from mimicking their contract. This is the *screening cost* of asymmetric information. The equilibrium trades off pooling efficiency (which would fully insure both types) against sorting efficiency (which ensures types do not misrepresent themselves).

### Moral Hazard and Optimal Cost-Sharing

Now introduce moral hazard: the consumer's medical utilization $x$ depends on the out-of-pocket price of care. Suppose the consumer faces an illness state and must decide how much medical care to purchase. Let $x$ denote the quantity of medical services (measured in dollars), and let the consumer's health benefit from $x$ be measured by a health state variable $h(x)$, where $h'(x) > 0$ and $h''(x) < 0$ (diminishing health returns to spending). If insurance covers a fraction $\gamma$ of medical costs, the consumer pays $(1-\gamma)x$ out-of-pocket and the insurer pays $\gamma x$.

The consumer's optimization problem, conditional on being ill, is to choose $x$ to maximize:

$$u(W - M - (1-\gamma)x) + v(h(x))$$

where $v$ is the utility from health improvements. The first-order condition is:

$$(1-\gamma)u'(W - M - (1-\gamma)x) = v'(h(x))h'(x)$$

The left-hand side is the marginal cost of additional spending (the consumer's out-of-pocket price times the marginal utility of consumption). The right-hand side is the marginal health benefit. As $\gamma$ increases (more generous coverage), the out-of-pocket price falls, the left-hand side decreases, and the consumer demands more care $x^*(\gamma)$. This defines the demand curve for medical care under insurance: $\frac{dx^*}{d\gamma} > 0$.

The insurer's expected payout under a contract with coinsurance rate $\gamma$ is:

$$E[\text{Payout}] = (1-p)(1-(1-p))\gamma x^*(\gamma) + p \gamma x^*(\gamma) = (1-p) \gamma x^*(\gamma)$$

where the notation reflects that moral hazard applies when the consumer is ill (probability $1-p$). The consumer's expected utility is:

$$E[U] = p \cdot u(W - \pi) + (1-p)[u(W - \pi - (1-\gamma)x^*(\gamma)) + v(h(x^*(\gamma)))]$$

where the premium $\pi$ is set to break even: $\pi = (1-p) \gamma x^*(\gamma)$.

The optimal insurance contract chooses $\gamma^*$ to maximize consumer expected utility subject to the zero-profit constraint. This involves balancing two effects. Increasing $\gamma$ reduces the consumer's out-of-pocket exposure when ill, improving risk protection—a positive effect. However, it also increases moral hazard by inducing higher utilization $x^*(\gamma)$, and the entire marginal utilization is borne by the consumer through a higher premium. For a risk-averse consumer with concave utility, the optimal $\gamma^*$ is strictly between zero (no insurance) and one (full insurance). The consumer is deliberately left exposed to some residual risk to preserve incentives for cost control.

In practice, this theoretical insight translates into the specific cost-sharing mechanisms observed in real health insurance contracts. A contract with a deductible $D$ means the consumer pays the first $D$ dollars of medical expenses; an insurance company covers the remainder. This creates a kinked budget constraint: if total medical spending is less than $D$, the consumer bears the full cost; if spending exceeds $D$, the consumer pays $D$ and the insurer covers the excess. Deductibles can be understood as the insurer's mechanism to induce the consumer to economize on low-value care (spending less than $D$) while protecting against catastrophic costs (when spending exceeds $D$).

A visual representation of the equilibrium under moral hazard and cost-sharing illustrates the trade-off:

```text
┌─────────────────────────────────────────────────────────────────┐
│                  Consumption and Health Trade-off                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Utility                                                         │
│     ▲                                                            │
│     │                    Optimal γ* creates residual risk       │
│     │              ╱╲                                           │
│     │             ╱  ╲                                          │
│     │            ╱    ╲                                         │
│     │           ╱      ╲  ← Full Insurance (γ=1)               │
│     │          ╱        ╲   creates max moral hazard            │
│     │         ╱          ╲                                      │
│     │        ╱            ╲                                     │
│     │   No Insurance      γ*                                    │
│     │   (max risk,    (balanced                                 │
│     │    no moral       risk & incentives)                      │
│     │    hazard)        ╱╲                                      │
│     │                 ╱  ╲_                                    │
│     │               ╱  ╲___╲_                                  │
│     │              ╱         ╲___                               │
│     │             ╱ ──────────────╲                             │
│     └────────────────────────────────────────────────────────►  │
│       0        γ*                   1  Coinsurance Rate (γ)     │
│                                                                  │
│    Note: γ*=0: Consumer bears all risk, max incentive control  │
│          γ*=1: Consumer bears no risk, max moral hazard        │
│          γ*∈(0,1): Optimal interior solution                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 3. High-Performance Optimization & Failure Modes

### Regulatory Architectures: Community Rating vs. Experience Rating

Real-world health insurance markets operate under radically different regulatory regimes, each representing a different resolution of the adverse selection problem. The two dominant poles are community rating and experience rating.

**Community rating** mandates that insurers charge all consumers in a defined geographic or occupational community the same premium, regardless of observed health status, age, or claims history. This regulation directly attempts to prevent adverse selection by making it impossible for insurers to offer low-risk consumers lower premiums. The theoretical justification rests on three grounds. First, it prevents the unraveling dynamics that would otherwise segregate risks into separate markets. Second, it promotes horizontal equity by treating individuals with similar incomes identically regardless of health status (which many view as morally arbitrary). Third, it provides an implicit intergenerational insurance mechanism: young, healthy individuals overpay during their low-illness years, and when they age and become high-risk, they underpay relative to their true risk.

However, community rating imposes a significant efficiency cost. By preventing insurers from pricing according to risk, it eliminates the financial incentive for high-risk consumers to purchase insurance from specialized, high-risk pools. Instead, it forces cross-subsidies within the community-rated pool. A low-risk consumer pays:

$$\pi_{\text{community}} = \bar{p} M$$

where $\bar{p}$ is the population-average illness probability. If $\bar{p} > p_L$, the low-risk consumer overpays relative to their expected claims. This overpayment can be large if the community includes many high-risk individuals (elderly, individuals with chronic diseases). Consequently, some low-risk consumers may rationally decide that the overpayment exceeds their willingness to pay for risk reduction and exit the insured pool entirely, becoming self-insured or purchasing catastrophic-only coverage.

The empirical magnitude of this adverse selection response under community rating has been substantial in real insurance markets. In the United States, before the Affordable Care Act (ACA) expanded community rating requirements, individual health insurance markets exhibited strong adverse selection: individuals with pre-existing conditions faced premiums 2-3 times higher than healthy individuals, and many young, healthy individuals chose to remain uninsured rather than pay community-rated premiums. After the ACA mandated near-universal community rating, the uninsured rate fell, but premiums in individual markets increased significantly, particularly in regions with concentrated populations of high-risk individuals.

**Experience rating** operates in the opposite direction: premiums are set based on the individual's or group's claims history.

## Experience Rating and the Trade-Off Between Efficiency and Equity

Experience rating allows premiums to adjust dynamically based on realized claims, creating a feedback loop between utilization and price. For an individual or group with claims history $C_t$, the premium in period $t+1$ becomes $\pi_{t+1} = f(C_t)$, where $f$ is an increasing function. This approach achieves allocative efficiency by aligning premiums with true risk, eliminating cross-subsidies and reducing adverse selection. Low-risk consumers pay actuarially fair rates, incentivizing broad market participation. However, experience rating generates two critical failures: it penalizes individuals who develop chronic conditions (effectively uninsuring them when they need coverage most), and it destroys the fundamental insurance property of risk pooling across time. An individual diagnosed with diabetes faces permanently elevated premiums, transforming insurance from a risk-spreading mechanism into a pay-as-you-go system. The resulting welfare loss is severe for risk-averse consumers, who lose precisely the intertemporal protection that justifies insurance purchase. Real-world implementations attempt to balance these extremes through partial experience rating (adjusting premiums within bounds) or guaranteed renewability provisions (locking initial rates conditional on continuous coverage). The optimal regulatory equilibrium remains contested: pure community rating maximizes equity but induces adverse selection spirals; pure experience rating maximizes short-run efficiency but destroys long-run insurability. Hybrid approaches—such as risk adjustment transfers, reinsurance mechanisms, and individual mandates—attempt to preserve both dimensions, though each introduces administrative complexity and second-order distortions.

The fundamental tension in health insurance pricing reflects the dual role of insurance markets: as risk-pooling institutions (requiring cross-subsidies and community rating) and as competitive markets (requiring actuarially fair pricing and experience rating). Economic theory demonstrates that no pricing mechanism can simultaneously achieve perfect risk pooling, allocative efficiency, and voluntary participation without external intervention. Mandatory participation (individual mandates) can sustain community-rated pools by eliminating adverse selection, but requires enforcement mechanisms and generates political opposition from low-risk consumers who perceive themselves as subsidizing others. Risk adjustment—transferring funds from insurers with low-risk enrollees to those with high-risk enrollees—preserves competitive markets while reducing selection incentives, but depends critically on the accuracy of risk prediction models and creates incentives for diagnosis code manipulation. The empirical performance of these mechanisms varies widely: Medicare Advantage risk adjustment explains approximately 11-14% of individual-level spending variation, leaving substantial residual selection pressures, while ACA risk corridors and reinsurance programs successfully stabilized individual markets in early implementation years but were politically constrained. The enduring lesson is that health insurance market design cannot be reduced to a single pricing rule; it requires a complementary architecture of mandates, subsidies, risk adjustment, and regulatory constraints that collectively balance the competing objectives of equity, efficiency, and sustainability.

## Summary & Verification Matrix

| **Concept** | **Governing Invariant** | **Core Mechanism** | **Diagnostic Criterion** |
|-------------|-------------------------|-------------------|-------------------------|
| **Adverse Selection** | High-risk consumers have higher willingness to pay for insurance than low-risk consumers at any given premium. | Asymmetric information causes high-risk pool concentration; insurers cannot observe individual risk types ex ante. | Compare enrollment rates by risk category; death spiral occurs when $\pi > WTP_{\text{low-risk}}$ and only high-risk remain. |
| **Moral Hazard** | Insurance reduces marginal cost of care, increasing consumption beyond efficient level where $MB = MC_{\text{social}}$. | Consumer faces coinsurance rate $c < 1$, so perceives price $c \cdot p$ rather than true price $p$; overconsumes when $MB = c \cdot p < p$. | Deadweight loss $= \frac{1}{2} \epsilon \cdot (1-c)^2 \cdot p \cdot q$; measure demand elasticity $\epsilon$ and consumption differential between insured/uninsured. |
| **Actuarially Fair Premium** | $\pi = p \cdot L$ where $p$ is illness probability and $L$ is financial loss when ill. | Insurer sets premium equal to expected payout; zero profit condition in competitive equilibrium. | Risk-neutral consumer indifferent to insurance; risk-averse consumer has $E[U(\text{insured})] > E[U(\text{uninsured})]$ only if loading $\lambda > 0$. |
| **Community Rating** | All consumers pay identical premium $\pi = \bar{p} \cdot M$ regardless of individual risk $p_i$. | Cross-subsidy from low-risk to high-risk; eliminates price discrimination but induces adverse selection. | Low-risk exit when $\pi_{\text{community}} - \pi_{\text{actuarial}} > $ risk premium; measure by uninsured rate among healthy populations. |
| **Experience Rating** | Premium in period $t+1$ is function of realized claims in period $t$: $\pi_{t+1} = f(C_t)$. | Dynamic pricing aligns premiums with revealed risk; achieves short-run efficiency but destroys intertemporal insurance. | Reclassification risk: individuals with chronic diagnoses face permanently elevated premiums; compare $\Delta \pi$ after health shock. |
| **Optimal Insurance Contract** | Full insurance ($c = 0$) maximizes risk protection but maximizes moral hazard; optimal coinsurance balances risk-bearing cost against efficiency loss. | Social planner trades off variance reduction (favors $c \to 0$) against deadweight loss (favors $c \to 1$); optimum where $\frac{\partial \text{Risk Cost}}{\partial c} = -\frac{\partial \text{DWL}}{\partial c}$. | Optimal $c^* \in (0,1)$ increases with demand elasticity $\epsilon$ and decreases with risk aversion coefficient $\rho$; empirical $c^* \approx 0.15$-$0.25$ for medical care. |
