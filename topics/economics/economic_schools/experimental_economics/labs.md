# Operational Verification Labs: Experimental Economics

## Objective & Operational Lab Setup

Experimental economics transforms abstract theoretical propositions into empirically testable hypotheses by constructing controlled laboratory markets where human subjects make real economic decisions under incentive-compatible compensation schemes. This operational guide equips practitioners with the technical apparatus to design, execute, and analyze laboratory experiments that reveal behavioral regularities, test equilibrium predictions, and measure the robustness of institutional mechanisms across diverse economic schools of thought.

The central verification objective is to operationalize core theoretical claims from Classical, Neoclassical, Austrian, Keynesian, and Behavioral schools through repeatable laboratory protocols. You will construct double-auction markets to test Walrasian equilibrium convergence, implement public goods experiments to measure voluntary contribution mechanisms against free-rider predictions, execute asset market bubbles to validate or refute rational expectations hypotheses, and deploy coordination games to examine Keynesian multiplicity of equilibria. Each exercise embeds rigorous experimental controls—randomization of subject assignment, incentive alignment through real monetary payoffs, and standardized institutional rules—that allow causal inference about economic behavior under alternative theoretical frameworks.

The laboratory environment requires three integrated analytical platforms. First, you will utilize **z-Tree** (Zurich Toolbox for Ready-made Economic Experiments), the industry-standard software for programming interactive economic experiments with networked client-server architecture. z-Tree enables precise control over information flows, decision timing, market clearing algorithms, and automated data logging at millisecond resolution. Second, you will employ **R** with specialized packages (`ggplot2` for visualization, `lme4` for mixed-effects regression models, `plm` for panel data econometrics) to conduct statistical analysis of experimental outcomes, test equilibrium predictions, and estimate treatment effects. Third, you will maintain experimental protocol documentation in structured spreadsheet templates that record subject demographics, randomization assignments, payoff calculation formulas, and institutional parameter configurations.

Physical setup demands a dedicated computer laboratory with networked workstations—one server machine running z-Tree server software and N client machines (minimum 12, optimal 20-24) running z-Tree client applications. Each workstation must have privacy partitions to prevent visual communication between subjects, ensuring decision independence. Prepare sealed envelopes containing initial endowments in experimental currency units (ECUs) convertible to real currency at a predetermined exchange rate, typically 10-20 ECUs per US dollar. Stock the laboratory with informed consent forms, printed experimental instructions with comprehension quizzes, receipt vouchers for cash payments, and backup paper recording sheets for manual data redundancy.

Experimental subject recruitment follows rigorous protocols to ensure external validity and minimize selection bias. Advertise sessions through university-wide email lists, community bulletin boards, and online platforms, emphasizing "participate in paid decision-making study" rather than "economic experiment" to avoid self-selection of economics-trained subjects. Screen for prior experimental participation to prevent contamination from repeated exposure to similar protocols. Maintain a subject database tracking participation history, contact information, and show-up rates. Pay subjects promptly in cash immediately after session completion, with total compensation including a fixed show-up fee plus variable performance-based earnings, ensuring average hourly rates exceed local minimum wage by 50-100% to sustain incentive compatibility.

Before initiating Exercise 1, verify your analytical environment by installing z-Tree version 4.2 or later, R version 4.0 or later with required packages, and ensuring network connectivity across all laboratory workstations. Conduct a dry-run pilot session with research assistants playing subject roles to debug protocol timing, test payoff calculation accuracy, and confirm data export functionality.

## Exercise 1: Foundational Practical Implementation—Double Auction Market Convergence

The double auction institution represents the canonical experimental test of Walrasian general equilibrium theory. This exercise operationalizes Vernon Smith's pioneering 1962 market experiments by constructing a continuous double-auction trading platform where human subjects, endowed with heterogeneous induced valuations and costs, negotiate competitive equilibrium prices through decentralized bid-ask negotiations. The core theoretical prediction—that repeated market periods drive transaction prices toward competitive equilibrium despite subjects' lack of global market information—constitutes a fundamental empirical verification of Hayekian distributed knowledge aggregation and Neoclassical price mechanism efficiency.

Begin by programming the experimental market structure in z-Tree. Launch z-Tree Server and create a new treatment file named `DoubleAuction_Baseline.ztt`. Define the subject role structure with two types: Buyers (N=6) and Sellers (N=6), randomly assigned at session start. Specify the commodity as a homogeneous fictitious good with unit quantity per transaction. Program the valuation assignment mechanism by creating a `subjects` table with fields `role`, `valuation`, and `cost`. For Buyers, draw valuations from the distribution V = {$10.00, $9.50, $9.00, $8.50, $8.00, $7.50}, ensuring each value appears exactly once through random permutation without replacement. For Sellers, draw costs from C = {$3.00, $3.50, $4.00, $4.50, $5.00, $5.50}, similarly ensuring unique assignment.

These induced value distributions generate a known competitive equilibrium prediction: sort Buyers' values in descending order and Sellers' costs in ascending order, then find the intersection quantity where the Nth highest buyer value equals or exceeds the Nth lowest seller cost. For the specified distributions, competitive equilibrium predicts quantity Q* = 4 units and price P* between $7.50 and $8.00, with theoretical consumer surplus CS = ($10.00 - $8.00) + ($9.50 - $8.00) + ($9.00 - $8.00) + ($8.50 - $8.00) = $5.00 and producer surplus PS = ($8.00 - $3.00) + ($8.00 - $3.50) + ($8.00 - $4.00) + ($8.00 - $4.50) = $14.00, yielding total surplus TS = $19.00 and market efficiency = (TS realized / TS maximum) × 100%.

Implement the trading mechanism interface by programming a real-time order book display showing all outstanding bids and asks ranked by price priority. Code the bid submission screen for Buyers with input validation requiring bid ≤ assigned valuation, preventing negative profit trades. Code the ask submission screen for Sellers with validation requiring ask ≥ assigned cost. Program the transaction execution rule: any bid ≥ any ask triggers immediate contract acceptance at the average of bid-ask spread, with automatic removal of matched orders from the book and instantaneous profit calculation displayed privately to both transacting parties. Set the trading period duration to 240 seconds (4 minutes), with a visual countdown timer and audible warning at 30 seconds remaining.

Configure the experimental sequence to run 6 consecutive trading periods with identical valuation/cost assignments maintained throughout, allowing subjects to learn from repeated market interaction. Between periods, program a 45-second information screen displaying: (1) the subject's own profit from the previous period, (2) cumulative profit across all periods, and (3) the complete price-quantity history of all contracts executed in the previous period, sorted chronologically. This public price information enables rational Bayesian updating of beliefs about equilibrium price levels across periods. Disable any communication of individual valuations, costs, or identities to preserve the veil of anonymity and prevent collusive coordination.

Program automated data logging to export a transactions table with fields: `period`, `timestamp`, `buyer_id`, `seller_id`, `contract_price`, `buyer_profit`, `seller_profit`, `efficiency`. Export an orders table capturing all bids and asks submitted, including rejected orders, with fields: `period`, `timestamp`, `subject_id`, `role`, `order_type`, `price`, `accepted`. Configure z-Tree to save these tables as tab-delimited text files in a designated output directory immediately after session completion.

Execute the experimental session by recruiting 12 subjects through your established subject pool, confirming participation 24 hours prior via email reminder with session time and location. Upon arrival, seat subjects at randomly assigned workstations using a predetermined randomization list generated by random number generator. Distribute printed experimental instructions written in plain language, avoiding economic jargon. Read instructions aloud to ensure common knowledge, then administer a comprehension quiz requiring subjects to calculate hypothetical profits for sample trades. Subjects must answer all quiz questions correctly before proceeding; provide private corrective feedback for errors.

Initiate the z-Tree client connections, verify all subjects see their assigned valuations or costs displayed on-screen, and launch the first trading period. Monitor the session from the server console, observing aggregate market statistics (total contracts, average price) in real time but refraining from intervention. After period 6 concludes, compute final earnings for each subject: show-up fee ($5.00) plus cumulative trading profits converted at exchange rate 10 ECUs = $1.00. Pay subjects in cash using sealed envelopes prepared during the session, collect signed receipt vouchers, and debrief subjects by explaining the competitive equilibrium benchmark without revealing individual strategies.

Conduct statistical analysis by importing the transactions table into R. Calculate period-by-period market efficiency:

```r
library(tidyverse)

# Load experimental data
transactions <- read_delim("DoubleAuction_Baseline_transactions.txt", delim = "\t")

# Define competitive equilibrium benchmarks
CE_price <- 7.75  # Midpoint of $7.50-$8.00 range
CE_quantity <- 4
CE_total_surplus <- 19.00

# Calculate realized efficiency per period
efficiency_by_period <- transactions %>%
  group_by(period) %>%
  summarise(
    realized_quantity = n(),
    realized_surplus = sum(buyer_profit) + sum(seller_profit),
    avg_price = mean(contract_price),
    price_variance = var(contract_price),
    efficiency_pct = (realized_surplus / CE_total_surplus) * 100
  )

print(efficiency_by_period)

# Visualize convergence dynamics
ggplot(efficiency_by_period, aes(x = period, y = avg_price)) +
  geom_line(size = 1.2) +
  geom_point(size = 3) +
  geom_hline(yintercept = CE_price, linetype = "dashed", color = "red", size = 1) +
  annotate("text", x = 1, y = CE_price + 0.3, label = "Competitive Equilibrium", color = "red") +
  labs(
    title = "Double Auction Price Convergence to Competitive Equilibrium",
    x = "Trading Period",
    y = "Average Contract Price ($)",
    caption = "Red dashed line indicates theoretical CE price"
  ) +
  theme_minimal(base_size = 14)

ggsave("price_convergence.png", width = 10, height = 6, dpi = 300)
```

Test the null hypothesis that average prices in periods 4-6 equal competitive equilibrium using a one-sample t-test:

```r
late_period_prices <- transactions %>%
  filter(period >= 4) %>%
  pull(contract_price)

t_test_result <- t.test(late_period_prices, mu = CE_price)
print(t_test_result)

# Report result
if (t_test_result$p.value > 0.05) {
  cat("RESULT: Fail to reject null hypothesis (p =", round(t_test_result$p.value, 3), 
      "). Observed prices statistically indistinguishable from competitive equilibrium.\n")
} else {
  cat("RESULT: Reject null hypothesis (p =", round(t_test_result$p.value, 3), 
      "). Significant deviation from competitive equilibrium detected.\n")
}
```

Compute allocative efficiency by comparing realized surplus extraction to the theoretical maximum. Classical and Neoclassical theory predicts efficiency approaching 100% as market experience accumulates. Calculate the improvement trajectory:

```r
# Efficiency improvement regression
efficiency_model <- lm(efficiency_pct ~ period, data = efficiency_by_period)
summary(efficiency_model)

# Extract slope coefficient
efficiency_slope <- coef(efficiency_model)[2]
cat("Efficiency gains per period:", round(efficiency_slope, 2), "percentage points\n")

# Test for significant positive trend
if (summary(efficiency_model)$coefficients[2, 4] < 0.05 & efficiency_slope > 0) {
  cat("VERIFICATION: Significant positive efficiency convergence confirms Smithian invisible hand hypothesis.\n")
}
```

Document all deviations from competitive equilibrium predictions. Common empirical patterns include: (1) initial period prices dispersed widely around equilibrium as subjects explore the trading space, (2) gradual variance reduction across periods as price discovery occurs, (3) slight overpricing bias when demand exceeds supply at equilibrium (or underpricing when reversed), and (4) occasional contracts at off-equilibrium prices due to errors or impatience near period deadlines. These behavioral regularities align with Hayekian knowledge diffusion dynamics but challenge strong-form rational expectations models requiring instantaneous equilibrium coordination.

Exercise 1 establishes the baseline laboratory infrastructure and demonstrates core experimental protocols applicable to all subsequent exercises. You have now verified that: (1) z-Tree software correctly implements market institutions and data logging, (2) subject recruitment and payment procedures maintain incentive compatibility, (3) statistical analysis pipelines extract theoretically relevant metrics, and (4) empirical outcomes conform to Walrasian equilibrium predictions under repeated market interaction. This foundational competence enables exploration of institutional variations, behavioral anomalies, and policy interventions in Exercises 2 and 3.

## Exercise 2: Parameter Variation & Empirical Analysis—Public Goods Voluntary Contribution Mechanism

Exercise 2 operationalizes the core tension between individual rationality and collective welfare emphasized by Classical economists (Adam Smith's invisible hand limitations), Austrian economists (spontaneous order boundaries), and modern Public Choice theorists (government failure analysis). The voluntary contribution mechanism (VCM) experiment tests whether rational self-interested agents voluntarily fund public goods or free-ride on others' contributions, as predicted by dominant-strategy Nash equilibrium analysis. By systematically varying the marginal per capita return (MPCR) parameter across treatments, you will measure the empirical elasticity of cooperation with respect to private incentive alignment, revealing conditions under which decentralized voluntary mechanisms succeed or fail.

The theoretical setup involves N subjects simultaneously deciding contribution levels to a public good. Each subject receives an endowment w (measured in ECUs) and chooses contribution c_i ∈ [0, w] to the public account, retaining (w - c_i) in a private account. The public account generates a return of m × Σc_i distributed equally to all N subjects, where m represents the MPCR and satisfies 1/N < m < 1 for the social dilemma structure to hold. The payoff function for subject i is:

$$\pi_i = (w - c_i) + m \sum_{j=1}^{N} c_j$$

The inequality 1/N < m < 1 ensures that (1) marginal social return exceeds marginal private return (m × N > 1), making full contribution socially optimal, but (2) marginal private return is less than one (m < 1), making zero contribution the dominant strategy Nash equilibrium. This tension between individual and collective rationality operationalizes the free-rider problem central to public goods theory.

Program the VCM experiment in z-Tree by creating a new treatment file `PublicGoods_MPCR.ztt`. Set the group size N = 4 subjects per public goods group, allowing simultaneous operation of multiple independent groups in a single session (e.g., 16 subjects organized into 4 groups). Define the endowment w = 20 ECUs for all subjects. Implement the contribution decision screen with a slider input allowing subjects to allocate any integer amount from 0 to 20 ECUs to the public account, with real-time visual feedback showing their private account retention (20 - c_i).

Configure three between-subjects treatment conditions varying the MPCR parameter:

- **Treatment LOW**: m = 0.30 (MPCR = 30%, group multiplier m × N = 1.20)
- **Treatment MEDIUM**: m = 0.50 (MPCR = 50%, group multiplier m × N = 2.00)
- **Treatment HIGH**: m = 0.70 (MPCR = 70%, group multiplier m × N = 2.80)

All treatments maintain identical endowment, group size, and decision interface; only the MPCR parameter varies. The LOW treatment generates weak social efficiency gains (20% surplus), the MEDIUM treatment doubles contributions, and the HIGH treatment provides strong collective incentives (180% surplus). Standard Nash equilibrium predicts zero contribution across all treatments, but behavioral regularities documented since Marwell and Ames (1979) show positive contributions declining toward zero across repeated rounds.

Program the information feedback structure to balance learning opportunities against confound prevention. After each round, display to each subject: (1) their own contribution decision, (2) the sum of all four group members' contributions, (3) the public account payout (m × group total), (4) their own round payoff, and (5) their cumulative earnings. Critically, do NOT reveal individual contributions of other group members, as this prevents targeted punishment or reciprocity dynamics that would conflate free-riding with strategic retaliation. Run 10 consecutive rounds with randomly re-matched groups each round (stranger matching protocol) to eliminate repeated-game reputation effects and isolate the one-shot social dilemma.

Conduct three experimental sessions, one for each treatment, with 16 subjects per session. Maintain identical recruitment, instruction, and payment protocols as Exercise 1. The only procedural difference is the MPCR value announced in printed instructions. After session completion, export contribution data with fields: `session_id`, `treatment`, `round`, `group_id`, `subject_id`, `contribution`, `group_total`, `payoff`.

Import the pooled data into R for cross-treatment empirical analysis:

```r
library(tidyverse)
library(lme4)

# Load pooled data from three sessions
vgm_data <- bind_rows(
  read_delim("PublicGoods_LOW.txt", delim = "\t") %>% mutate(treatment = "LOW", mpcr = 0.30),
  read_delim("PublicGoods_MEDIUM.txt", delim = "\t") %>% mutate(treatment = "MEDIUM", mpcr = 0.50),
  read_delim("PublicGoods_HIGH.txt", delim = "\t") %>% mutate(treatment = "HIGH", mpcr = 0.70)
)

# Calculate average contribution by treatment and round
contribution_summary <- vgm_data %>%
  group_by(treatment, round) %>%
  summarise(
    mean_contribution = mean(contribution),
    se_contribution = sd(contribution) / sqrt(n()),
    cooperation_rate = mean(contribution) / 20  # Fraction of endowment contributed
  )

# Visualize contribution dynamics across treatments
ggplot(contribution_summary, aes(x = round, y = mean_contribution, color = treatment, group = treatment)) +
  geom_line(size = 1.2) +
  geom_point(size = 3) +
  geom_errorbar(aes(ymin = mean_contribution - se_contribution, ymax = mean_contribution + se_contribution), width = 0.3) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
  geom_hline(yintercept = 20, linetype = "dashed", color = "blue") +
  annotate("text", x = 9, y = 21, label = "Social Optimum (Full Contribution)", color = "blue", size = 3.5) +
  annotate("text", x = 9, y = 1, label = "Nash Equilibrium (Zero Contribution)", color = "black", size = 3.5) +
  scale_color_manual(values = c("LOW" = "#D55E00", "MEDIUM" = "#0072B2", "HIGH" = "#009E73")) +
  labs(
    title = "Public Goods Contributions by MPCR Treatment",
    x = "Round",
    y = "Mean Contribution (ECUs)",
    color = "MPCR Treatment"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "top")

ggsave("public_goods_contributions.png", width = 12, height = 7, dpi = 300)
```

Test the treatment effect of MPCR on contribution levels using a mixed-effects regression model with subject random effects to account for within-subject correlation across rounds:

```r
# Mixed-effects model: contribution ~ MPCR + round + random(subject)
model_mpcr <- lmer(contribution ~ mpcr + round + (1 | subject_id), data = vgm_data)
summary(model_mpcr)

# Extract MPCR coefficient
mpcr_effect <- fixef(model_mpcr)["mpcr"]
mpcr_pvalue <- summary(model_mpcr)$coefficients["mpcr", "Pr(>|t|)"]

cat("MPCR Treatment Effect:", round(mpcr_effect, 2), "ECUs per 0.10 increase in MPCR\n")
cat("Statistical Significance: p =", round(mpcr_pvalue, 4), "\n")

if (mpcr_pvalue < 0.001) {
  cat("VERIFICATION: Highly significant positive MPCR effect confirms conditional cooperation hypothesis.\n")
  cat("Implication: Subjects respond to incentive alignment, contradicting zero-contribution Nash prediction.\n")
}
```

Quantify the decay rate of contributions across rounds to test the prediction that learning drives convergence to Nash equilibrium:

```r
# Decay model: contribution ~ round, separately by treatment
decay_models <- vgm_data %>%
  group_by(treatment) %>%
  do(model = lm(contribution ~ round, data = .))

# Extract decay slopes
decay_summary <- decay_models %>%
  summarise(
    treatment = treatment,
    decay_rate = coef(model)[2],
    p_value = summary(model)$coefficients[2, 4]
  )

print(decay_summary)

# Test for negative decay
if (all(decay_summary$decay_rate < 0) & all(decay_summary$p_value < 0.05)) {
  cat("VERIFICATION: Significant negative decay across all treatments confirms learning-to-defect hypothesis.\n")
  cat("Implication: Initial cooperation erodes toward Nash equilibrium under repeated interaction.\n")
}
```

Calculate efficiency losses relative to social optimum:

```r
# Efficiency = (realized total payoff) / (optimum total payoff)
efficiency_analysis <- vgm_data %>%
  group_by(treatment, round) %>%
  summarise(
    realized_total = sum(payoff),
    optimum_total = n() * (20 + 0.70 * 20 * 4)  # Using HIGH treatment for maximum efficiency
  ) %>%
  mutate(efficiency_loss_pct = (1 - realized_total / optimum_total) * 100)

avg_efficiency_loss <- efficiency_analysis %>%
  group_by(treatment) %>%
  summarise(avg_loss = mean(efficiency_loss_pct))

print(avg_efficiency_loss)
```

The empirical pattern consistently observed across thousands of VCM experiments worldwide reveals three robust behavioral regularities that challenge Classical free-market optimism and Nash equilibrium predictions: (1) initial contributions average 40-60% of endowment despite dominant-strategy zero contribution, (2) contributions decay approximately linearly at 2-4 ECUs per round toward but not reaching zero, and (3) higher MPCR values significantly increase contribution levels and slow decay rates. These findings validate **conditional cooperation** models where subjects reciprocate perceived group cooperation norms but require repeated evidence of others' contributions to sustain their own.

The Austrian School interpretation emphasizes that VCM failure stems from inadequate property rights assignment and absence of excludability mechanisms. Voluntary public goods provision succeeds only when contributors capture sufficient private returns through reputational capital, selective incentives, or repeated interaction shadow-of-the-future effects. The Classical liberal critique highlights that government provision alternatives suffer from political free-riding (rational ignorance of voters) and rent-seeking distortions, making the comparison between imperfect voluntary mechanisms and imperfect political mechanisms empirically ambiguous.

Document alternative institutional solutions tested in experimental extensions: (1) threshold provision with money-back guarantees (assurance contracts), (2) punishment mechanisms allowing costly sanctioning of low contributors, (3) communication and pledge opportunities before contribution decisions, and (4) leadership by example through sequential contribution timing. Each modification alters the strategic environment, testing theories of institutional design proposed by Elinor Ostrom, Herbert Gintis, and Samuel Bowles.

Exercise 2 establishes your competence in between-subjects experimental designs, parametric treatment variations, and panel data analysis using mixed-effects models. You have empirically verified that: (1) incentive alignment (MPCR) significantly affects cooperation rates, (2) learning dynamics drive decay toward but not complete convergence with Nash equilibrium, and (3) efficiency losses from voluntary provision justify institutional innovation beyond naive free-market reliance.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol—Asset Market Bubbles and Rational Expectations Breakdown

Exercise 3 operationalizes the most dramatic experimental challenge to rational expectations theory and efficient markets hypothesis: the laboratory asset market bubble phenomenon pioneered by Vernon Smith, Gerry Suchanek, and Arlington Williams (1988). Despite complete information about fundamental asset value, finite horizon with known terminal period, and experienced trader subjects, experimental asset markets reliably generate boom-bust price patterns with prices rising 200-400% above fundamental value before crashing. This systematic deviation from rational expectations equilibrium tests the boundary conditions of Neoclassical asset pricing theory, validates Keynesian "beauty contest" dynamics and animal spirits intuition, and reveals the behavioral microfoundations of financial instability emphasized by Hyman Minsky and Charles Kindleberger.

The experimental stress test constructs an artificial asset market where fundamental value is transparent and deterministic, eliminating the information asymmetry defense for price deviations. Program the asset market in z-Tree with the following institutional structure. Each of N = 9 subjects receives an initial endowment of 2 shares of a dividend-paying asset plus 360 ECUs cash. The asset pays a random dividend each period drawn from the distribution {0, 8, 28, 60} cents with equal probability, yielding expected dividend E[d] = 24 cents per period. The market operates for exactly T = 15 periods, after which the asset becomes worthless (no terminal value). The fundamental value in period t is therefore:

$$FV_t = (T - t + 1) \times E[d] = (15 - t + 1) \times 0.24$$

This generates a linear declining fundamental value schedule: FV_1 = $3.60, FV_2 = $3.36, ..., FV_14 = $0.48, FV_15 = $0.24. Subjects receive printed tables showing fundamental value for all 15 periods, making this information common knowledge. Rational expectations equilibrium predicts prices equal fundamental value in every period.

Implement the continuous double-auction trading interface identical to Exercise 1: subjects submit bids and asks for shares, contracts execute at bid-ask midpoint when bid ≥ ask, and the order book displays all outstanding orders. Set the trading period duration to 180 seconds (3 minutes) per period. After each trading period, conduct the dividend draw publicly by displaying the realized dividend to all subjects and crediting accounts automatically. Display the updated cash and share holdings for each subject privately, plus the complete transaction history (prices and quantities) publicly.

Critical design feature: ensure subjects fully understand the dividend distribution and declining fundamental value structure by administering a mandatory comprehension quiz requiring calculation of expected dividends, fundamental value in sample periods, and maximum rational price for a share in period 10. Subjects must demonstrate full comprehension before trading begins, eliminating the excuse that bubble prices result from confusion about asset mechanics.

Configure experimental treatments to stress-test boundary conditions for bubble formation:

**Treatment BASELINE**: Inexperienced subjects, no short-selling allowed (subjects can only sell shares they own).

**Treatment EXPERIENCE**: Same subjects return for a second session 1-2 weeks later, trading an identical asset market with same dividend structure and fundamental value schedule. Rational learning models predict bubble elimination after experiencing the first crash.

**Treatment SHORT**: Allow negative share holdings (short-selling), enabling arbitrage by subjects who recognize overpricing. Short-sellers borrow shares, sell at inflated prices, and repurchase at lower prices to profit from the bubble collapse. Arbitrage should discipline prices toward fundamental value.

Execute the BASELINE session with 9 subjects. Monitor trading in real-time from the z-Tree server console, observing price formation patterns. Typical bubble anatomy exhibits three phases: (1) **Early Periods (1-5)**: Prices fluctuate near fundamental value as subjects cautiously explore trading, (2) **Bubble Phase (6-11)**: Prices rise dramatically above fundamental value, often peaking at 200-300% of FV in period 10-11, driven by momentum trading and greater-fool speculation, (3) **Crash Phase (12-15)**: Prices collapse toward zero as the terminal period approaches and subjects realize no buyer will purchase worthless assets.

After session completion, export transaction data and conduct statistical analysis:

```r
library(tidyverse)

# Load bubble experiment data
bubble_data <- read_delim("AssetMarket_BASELINE.txt", delim = "\t")

# Calculate fundamental value schedule
fundamental_value <- tibble(
  period = 1:15,
  FV = (15 - period + 1) * 0.24
)

# Calculate average transaction price per period
price_summary <- bubble_data %>%
  group_by(period) %>%
  summarise(
    avg_price = mean(contract_price),
    n_trades = n(),
    max_price = max(contract_price),
    min_price = min(contract_price)
  ) %>%
  left_join(fundamental_value, by = "period")

# Visualize bubble formation and crash
ggplot(price_summary, aes(x = period)) +
  geom_line(aes(y = avg_price, color = "Average Price"), size = 1.5) +
  geom_point(aes(y = avg_price, color = "Average Price"), size = 3) +
  geom_line(aes(y = FV, color = "Fundamental Value"), size = 1.5, linetype = "dashed") +
  geom_ribbon(aes(ymin = min_price, ymax = max_price), alpha = 0.2, fill = "blue") +
  scale_color_manual(
    name = "",
    values = c("Average Price" = "#D55E00", "Fundamental Value" = "#0072B2")
  ) +
  labs(
    title = "Experimental Asset Market Bubble: Price vs. Fundamental Value",
    x = "Trading Period",
    y = "Price (ECUs)",
    caption = "Shaded region shows min-max price range within period"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "top")

ggsave("asset_bubble.png", width = 12, height = 7, dpi = 300)
```

Calculate quantitative bubble metrics used in experimental finance literature:

```r
# Relative Absolute Deviation (RAD): average percentage price deviation from FV
bubble_metrics <- price_summary %>%
  mutate(
    deviation = abs(avg_price - FV),
    rel_deviation = deviation / FV
  ) %>%
  summarise(
    RAD = mean(rel_deviation) * 100,
    amplitude = max(avg_price) / max(FV),
    peak_period = period[which.max(avg_price)],
    crash_magnitude = max(avg_price) - min(avg_price[period > peak_period]),
    turnover = sum(n_trades) / (9 * 2)  # Total trades / initial shares
  )

print(bubble_metrics)

cat("\nBubble Severity Interpretation:\n")
cat("RAD < 10%: No bubble (prices track fundamentals)\n")
cat("RAD 10-30%: Mild bubble\n")
cat("RAD 30-60%: Moderate bubble\n")
cat("RAD > 60%: Strong bubble\n")
cat("Observed RAD:", round(bubble_metrics$RAD, 1), "%\n")
```

Test the statistical significance of mispricing using a period-by-period comparison:

```r
# Two-sample t-test: observed prices vs. fundamental value
mispricing_test <- t.test(price_summary$avg_price, price_summary$FV, paired = TRUE, alternative = "greater")

cat("Mispricing Test Results:\n")
cat("Mean price:", round(mean(price_summary$avg_price), 2), "ECUs\n")
cat("Mean FV:", round(mean(price_summary$FV), 2), "ECUs\n")
cat("t-statistic:", round(mispricing_test$statistic, 2), "\n")
cat("p-value:", format.pval(mispricing_test$p.value, digits = 3), "\n")

if (mispricing_test$p.value < 0.001) {
  cat("\nVERIFICATION: Highly significant overpricing confirms systematic deviation from rational expectations equilibrium.\n")
  cat("Implication: Efficient markets hypothesis fails under complete information and finite horizon.\n")
}
```

Execute the EXPERIENCE treatment by inviting the same 9 subjects back for a second session. The rational learning hypothesis predicts bubble elimination after subjects experience the boom-bust cycle. Analyze the experience effect:

```r
# Load experienced session data
bubble_exp <- read_delim("AssetMarket_EXPERIENCE.txt", delim = "\t")

# Compare baseline vs. experience
comparison <- bind_rows(
  price_summary %>% mutate(session = "Inexperienced"),
  bubble_exp %>%
    group_by(period) %>%
    summarise(avg_price = mean(contract_price), n_trades = n()) %>%
    left_join(fundamental_value, by = "period") %>%
    mutate(session = "Experienced")
)

# Visualize learning effect
ggplot(comparison, aes(x = period, y = avg_price, color = session, group = session)) +
  geom_line(size = 1.2) +
  geom_point(size = 3) +
  geom_line(aes(y = FV), color = "black", linetype = "dashed", size = 1) +
  scale_color_manual(values = c("Inexperienced" = "#D55E00", "Experienced" = "#009E73")) +
  labs(
    title = "Experience Effect on Asset Market Bubbles",
    x = "Trading Period",
    y = "Average Price (ECUs)",
    color = "Subject Pool"
  ) +
  theme_minimal(base_size = 14)

ggsave("experience_effect.png", width = 12, height = 7, dpi = 300)

# Calculate RAD reduction
rad_baseline <- bubble_metrics$RAD
rad_experience <- bubble_exp %>%
  group_by(period) %>%
  summarise(avg_price = mean(contract_price)) %>%
  left_join(fundamental_value, by = "period") %>%
  summarise(RAD = mean(abs(avg_price - FV) / FV) * 100) %>%
  pull(RAD)

cat("Bubble severity reduction with experience:", round(rad_baseline - rad_experience, 1), "percentage points\n")
cat("Percentage reduction:", round((1 - rad_experience / rad_baseline) * 100, 1), "%\n")

if (rad_experience > 0.3 * rad_baseline) {
  cat("\nRESULT: Bubbles persist despite experience, contradicting strong rational learning hypothesis.\n")
  cat("Even subjects who suffered losses in crash continue momentum trading in subsequent session.\n")
}
```

Execute the SHORT treatment with a fresh subject pool to test arbitrage discipline effects. Allow negative share holdings with borrowing costs of 5% per period to prevent unlimited leverage. Program the z-Tree interface to permit short sales by removing the non-negativity constraint on share holdings. Arbitrageurs can sell shares they don't own, creating negative positions, then close positions by repurchasing shares at (hopefully) lower prices.

Analyze whether short-selling reduces bubble magnitude:

```r
# Load short-selling treatment data
bubble_short <- read_delim("AssetMarket_SHORT.txt", delim = "\t")

# Compare bubble severity across treatments
comparison_short <- tibble(
  treatment = c("BASELINE", "EXPERIENCE", "SHORT"),
  RAD = c(
    rad_baseline,
    rad_experience,
    bubble_short %>%
      group_by(period) %>%
      summarise(avg_price = mean(contract_price)) %>%
      left_join(fundamental_value, by = "period") %>%
      summarise(RAD = mean(abs(avg_price - FV) / FV) * 100) %>%
      pull(RAD)
  )
)

print(comparison_short)

# Bar plot of treatment effects
ggplot(comparison_short, aes(x = treatment, y = RAD, fill = treatment)) +
  geom_col(width = 0.6) +
  geom_hline(yintercept = 10, linetype = "dashed", color = "red") +
  annotate("text", x = 1.5, y = 12, label = "10% threshold (mild bubble)", color = "red") +
  scale_fill_manual(values = c("BASELINE" = "#D55E00", "EXPERIENCE" = "#009E73", "SHORT" = "#0072B2")) +
  labs(
    title = "Asset Market Bubble Severity Across Institutional Treatments",
    x = "Treatment Condition",
    y = "Relative Absolute Deviation (%)",
    fill = "Treatment"
  ) +
  theme_minimal(base_size = 14) +
  theme(legend.position = "none")

ggsave("treatment_comparison.png", width = 10, height = 6, dpi = 300)
```

Theoretical implications and recovery protocols emerge from this stress test. The robust replication of bubbles under complete information conditions falsifies strong-form efficient markets hypothesis and rational expectations models that assume common knowledge of rationality. Alternative behavioral explanations include: (1) **Heterogeneous expectations**: subjects hold divergent beliefs about other traders' rationality levels, creating speculative demand from traders betting on resale to greater fools, (2) **Ambiguity aversion**: uncertainty about others' behavior induces precautionary momentum following, (3) **Limited cognition**: subjects apply heuristics (trend extrapolation) rather than backward induction, and (4) **Confusion**: despite comprehension quizzes, subjects fail to fully internalize declining fundamental value implications.

Austrian economists interpret bubbles as evidence of monetary distortions and malinvestment driven by artificially low interest rates, but laboratory bubbles emerge without central bank policy variables, suggesting behavioral microfoundations independent of monetary regime. Keynesian "beauty contest" intuition receives strong support: traders optimize not against fundamental value but against anticipated higher-order beliefs about average opinion.

Policy implications for financial market regulation include: (1) **Circuit breakers**: automatic trading halts during rapid price movements prevent cascading momentum crashes, (2) **Margin requirements**: limiting leverage reduces speculative excess demand, (3) **Short-selling facilitation**: arbitrage mechanisms dampen but do not eliminate bubbles, and (4) **Transparency mandates**: public fundamental value disclosure (analogous to earnings reports) provides rational anchors but insufficient to prevent mispricing.

Document the recovery protocol for detecting and mitigating experimental bubbles in applied settings. Real-time monitoring indicators include: (1) **Price-to-fundamentals ratio** exceeding 1.5, (2) **Turnover rate** (trades per share per period) above 0.3, indicating speculative churning, (3) **Bid-ask spread compression** below 10% of price, signaling aggressive buying, and (4) **Volume concentration** in late boom phase as liquidity dries up before crash. Implement automated alerts in z-Tree to flag these thresholds for experimenter awareness, though do NOT intervene during the session to preserve external validity.

Post-crash debriefing interviews reveal trader psychology. Common rationalizations include: "I knew it was overpriced but expected to sell before the crash" (greater-fool strategy), "I thought others had private information justifying high prices" (information cascade), and "Prices were rising so I followed the trend" (momentum heuristic). These verbal protocols validate behavioral models over rational expectations.

Exercise 3 completes your experimental economics laboratory training by demonstrating: (1) stress testing of theoretical predictions under extreme parameter configurations, (2) identification of systematic boundary failures for rational models, (3) implementation of institutional variations (experience, short-selling) to test recovery mechanisms, and (4) integration of quantitative metrics with qualitative behavioral interpretation. You have empirically verified that rational expectations equilibrium fails under high-stakes incentives, complete information, and repeated interaction—the strongest possible conditions for rational behavior.

## Operational Reference Guide & Diagnostic Checklist

### z-Tree Programming Verification Protocol

Before launching any experimental session, execute this comprehensive diagnostic sequence to prevent runtime failures and data corruption:

**Infrastructure Verification**: Boot the server machine and all client machines, confirming network connectivity by pinging each client IP address from the server terminal. Launch z-Tree Server version 4.2+ and verify the treatment file loads without syntax errors. Navigate to Treatment → Test Client Alone to simulate single-subject decisions and confirm payoff calculations match hand-calculated values. Check that data export paths are writable and contain no legacy files that could be overwritten.

**Randomization Integrity**: Verify that subject-to-role assignments use true random number generation (z-Tree's internal `random()` function seeded by system clock) rather than pseudorandom sequences that could correlate with arrival order. For between-subjects treatments, confirm that treatment assignment occurs via independent random draw rather than alternating or sequential assignment that creates period effects.

**Incentive Compatibility Audit**: Calculate worst-case and best-case earnings for each experimental task assuming rational play. Confirm that the minimum guaranteed payment (show-up fee plus worst-case earnings) exceeds 150% of local minimum wage × session duration to maintain recruitment viability. Verify that the exchange rate between ECUs and real currency is clearly communicated in instructions and that subjects see live cumulative earnings in real currency units to sustain salience.

**Timing Calibration**: Test trading period durations by running mock sessions with research assistants. For double-auction markets, 240-second periods allow approximately 15-20 contracts per period; shorter durations truncate price discovery, longer durations induce boredom. For simultaneous decision tasks (VCM, asset markets), 90-120 seconds suffices for input entry. Set the inter-period pause to 30-45 seconds for subjects to review feedback screens without rushing.

**Data Logging Validation**: After completing a test session with mock subjects, export all data tables and verify: (1) transaction timestamps recorded at millisecond precision, (2) subject IDs anonymized and consistent across tables, (3) all payoff calculations match z-Tree's internal computation, (4) missing values flagged correctly for periods where subjects made no decision, and (5) no data truncation for sessions exceeding 50 periods or 1000 observations per table.

### Subject Recruitment & Management Best Practices

Maintain a centralized subject database in spreadsheet format with fields: `subject_id`, `name`, `email`, `phone`, `date_recruited`, `sessions_participated`, `experiments_completed`, `payment_total`, `no_show_history`, `notes`. Assign permanent anonymous subject IDs (e.g., SUB001, SUB002) at first recruitment and use consistently across all sessions to enable longitudinal tracking without revealing identities in data files.

Recruitment advertisements should specify: (1) estimated session duration (±15 minutes buffer), (2) guaranteed show-up fee, (3) potential variable earnings range (e.g., "$15-$35 depending on decisions"), (4) location and parking instructions, and (5) exclusion criteria (prior participation in similar studies). Send confirmation emails 24 hours before sessions with calendar invitations and reminder text messages 2 hours prior to reduce no-show rates below 10%.

Over-recruit by 20% to compensate for no-shows. If excess subjects arrive, pay the show-up fee and dismiss politely, logging them as "paid-not-participated" for future priority scheduling. For experiments requiring exact group sizes (public goods N=4 groups), prepare alternative single-player tasks (e.g., risk elicitation, survey) for subjects who cannot be evenly assigned to groups.

Payment protocols require audit trails for IRB compliance and tax reporting. Print receipt vouchers with fields: `subject_id`, `session_date`, `experiment_title`, `show_up_fee`, `performance_earnings`, `total_payment`, `signature`. Subjects sign receipts upon receiving cash payment in sealed envelopes. Retain copies for 7 years. For payments exceeding $600 annually to a single subject, collect W-9 tax forms and issue 1099-MISC reports.

### Statistical Analysis Pipeline & Replication Standards

All experimental data analysis must satisfy transparency and reproducibility requirements codified by the American Economic Association Data and Code Availability Policy. Store raw z-Tree export files in version-controlled repositories (Git) with immutable commit hashes tagging data as collected. Never edit raw data files; perform all cleaning and transformations in documented R scripts with line-by-line comments explaining each step.

Adopt a three-stage analysis pipeline: (1) **Descriptive Statistics Stage**: Calculate means, standard deviations, and confidence intervals for all primary outcomes, generate summary tables and visualization plots, and document sample size, attrition, and exclusions, (2) **Hypothesis Testing Stage**: Pre-register primary hypotheses before data collection, report exact p-values rather than asterisk thresholds, include effect size measures (Cohen's d, odds ratios) alongside significance tests, and (3) **Robustness Checks Stage**: Re-estimate main results with alternative specifications (non-parametric tests, outlier exclusion, subgroup analysis) to verify stability.

For longitudinal experiments with repeated measures (VCM contributions across 10 rounds, asset prices across 15 periods), employ hierarchical modeling that accounts for within-subject correlation. The `lme4` package in R implements mixed-effects regression:

```r
library(lme4)

# Random intercepts model
model_ri <- lmer(outcome ~ treatment + time + (1 | subject_id), data = experiment_data)

# Random slopes model (allows heterogeneous treatment effects)
model_rs <- lmer(outcome ~ treatment * time + (1 + time | subject_id), data = experiment_data)

# Model comparison via likelihood ratio test
anova(model_ri, model_rs)
```

Report model comparison statistics (AIC, BIC, log-likelihood) and choose the parsimonious specification unless complex models significantly improve fit (p < 0.05 in likelihood ratio test).

### Common Experimental Pathologies & Diagnostic Resolution

**Pathology: Zero-variance outcomes** (all subjects make identical choices). Diagnosis: Dominant-strategy game design eliminates strategic uncertainty, or instructions insufficiently clear causing coordinated confusion. Resolution: Pilot test instructions with naive subjects, revise language to emphasize decision independence, or redesign payoff structure to introduce meaningful tradeoffs.

**Pathology: Excess missing data** (>10% of subjects fail to enter decisions before timeout). Diagnosis: Time pressure too severe, or interface confusion. Resolution: Extend decision period duration by 30-60 seconds, add visual countdown warning at halfway point, or simplify input controls (slider vs. text entry).

**Pathology: Order effects** (early-period decisions systematically differ from late-period decisions unrelated to learning). Diagnosis: Fatigue, boredom, or experimenter demand effects. Resolution: Limit total session duration to 90 minutes maximum, randomize task order across sessions, or debrief subjects to assess awareness of experimental hypotheses.

**Pathology: Collusion** (subjects communicate between workstations despite privacy partitions). Diagnosis: Inadequate physical separation or break-time interaction. Resolution: Stagger subject arrival times to prevent social familiarity, enforce strict no-talking policy with immediate dismissal penalty, or use individual testing rooms for high-stakes strategic games.

**Pathology: Software crashes** (z-Tree client disconnects mid-session). Diagnosis: Network instability or insufficient server RAM for large session sizes. Resolution: Run session on isolated LAN without internet connectivity, upgrade server machine to 16GB+ RAM, and implement automatic client reconnection with session state recovery from server backup.

**Pathology: Replication failure** (published experimental results not reproduced in your laboratory). Diagnosis: Subtle institutional differences (e.g., student population characteristics, payment exchange rates, instruction phrasing). Resolution: Obtain original authors' z-Tree treatment files and instruction scripts to ensure exact replication protocol, increase sample size to detect smaller effect sizes, or conduct many-labs coordinated replication with standardized protocols across institutions.

### Ethics & IRB Compliance Standards

All experimental research involving human subjects requires Institutional Review Board (IRB) approval before data collection. Submit protocol applications including: (1) complete experimental instructions and consent forms, (2) z-Tree treatment files or detailed task descriptions, (3) recruitment materials and subject payment rate justification, (4) data security plan specifying encryption and de-identification procedures, and (5) risk assessment documenting potential psychological or financial harms.

Standard experimental economics studies qualify for expedited review under minimal risk criteria: subjects face no physical danger, decisions involve hypothetical or low-stakes monetary outcomes, and participation is voluntary with withdrawal permitted at any time. However, experiments involving deception (e.g., confederate subjects, false feedback) or vulnerable populations (children, prisoners, cognitively impaired) require full board review with enhanced protections.

Informed consent procedures must clearly communicate: (1) the purpose of the study in general terms (without revealing specific hypotheses that could induce demand effects), (2) the duration and compensation structure, (3) the right to withdraw without penalty, (4) confidentiality protections (anonymous subject IDs, encrypted data storage), and (5) experimenter contact information for questions or complaints. Subjects sign consent forms before viewing experimental instructions; forms are stored separately from data files to prevent identity linkage.

Data security protocols require encryption of raw data files containing subject IDs, storage on password-protected university servers with nightly backups, and destruction of linking keys (mapping subject IDs to names) within 1 year of data collection unless longitudinal follow-up is planned. Published datasets must be fully de-identified with no combination of variables permitting re-identification.

Financial compensation must satisfy two constraints: (1) minimum payment (show-up fee) independent of performance to avoid coercion of risk-averse subjects, and (2) meaningful performance incentives scaling approximately linearly with effort or skill. Typical show-up fees range $5-$10, with total earnings averaging $20-$30 per hour. Never frame payments as "wages" to avoid employment law complications; subjects are research participants, not employees.

### Archival Data Preservation & Meta-Analysis Contribution

Deposit raw experimental data in public repositories (Harvard Dataverse, Open Science Framework, AEA Data Repository) within 12 months of publication. Include: (1) z-Tree treatment files with documentation, (2) de-identified subject-level data tables, (3) R analysis scripts with session information files (package versions, random seeds), (4) experimental instructions in PDF format, and (5) README files explaining variable definitions and data structure.

Properly archived data enables meta-analyses aggregating experimental results across laboratories to estimate population-level treatment effects and identify moderating factors (subject pool characteristics, experimenter effects, cultural differences). For example, meta-regression of 50+ VCM experiments reveals that student subjects contribute 15-20 percentage points less than community subjects, and that experiments conducted in collectivist cultures (Asia, Middle East) generate 10-15 percentage points higher cooperation than individualist cultures (North America, Western Europe).

Contribute to standardized experimental protocols by participating in Many Labs replication projects coordinated through the Economic Science Association. Standardization reduces researcher degrees of freedom in design choices (e.g., exchange rates, instruction wording) that can inadvertently introduce bias or noise, improving cumulative knowledge generation in experimental economics.

This operational verification laboratory sequence has equipped you with the complete technical infrastructure to design, execute, and analyze experimental economics research across diverse theoretical schools. You have mastered the software tools (z-Tree, R statistical analysis), institutional design principles (double auctions, public goods mechanisms, asset markets), subject management protocols (recruitment, payment, ethics compliance), and statistical inference methods (mixed-effects models, hypothesis testing, robustness checks) that define professional experimental practice. Deploy these capabilities to empirically test economic theories, measure behavioral parameters, and inform policy design in domains ranging from market regulation to public finance to institutional reform.
