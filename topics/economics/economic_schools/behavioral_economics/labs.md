# Operational Verification Labs: Behavioral Economics

## Objective & Operational Lab Setup

Behavioral economics emerged as a radical departure from the neoclassical assumption of perfect rationality, integrating psychological realism into economic modeling through systematic documentation of cognitive biases, heuristics, and preference anomalies. These laboratories provide hands-on operational verification of the foundational experiments that exposed violations of expected utility theory, time-consistency, and market efficiency. You will replicate the canonical behavioral experiments using controlled elicitation protocols, analyze choice data through maximum likelihood estimation of prospect theory parameters, and stress-test the robustness of behavioral anomalies across demographic segments and framing variations.

The practical objective is not merely to observe that humans deviate from rational choice axioms, but to quantify the magnitude, stability, and policy relevance of these deviations through rigorous experimental design and statistical inference. Each exercise builds operational competence in constructing incentive-compatible choice tasks, coding behavioral models in R and Python, and interpreting parameter estimates through the lens of welfare economics and paternalistic intervention design. Unlike pure theoretical behavioral economics courses that dwell on taxonomies of biases, these labs prioritize replicable measurement protocols and falsifiable empirical predictions.

Your analytical research environment requires R (version 4.0 or higher) with the tidyverse, ggplot2, and maxLik packages for choice modeling, Python 3.8+ with NumPy, Pandas, SciPy, and Matplotlib for simulation and visualization, and spreadsheet software (Excel or LibreOffice Calc) for manual lottery construction and payoff calculation. Install R packages by executing `install.packages(c("tidyverse", "ggplot2", "maxLik", "MASS"))` in the R console. For Python dependencies, run `pip install numpy pandas scipy matplotlib seaborn` in your terminal. You will also need access to online survey platforms such as Qualtrics or Google Forms for administering choice experiments to human subjects, though pilot testing can be conducted on yourself or a small convenience sample.

The diagnostic framework centers on three operational standards. First, preference reversals and framing effects must be statistically significant at the p < 0.05 level with effect sizes exceeding Cohen's d = 0.3 to distinguish genuine behavioral phenomena from measurement noise. Second, estimated prospect theory parameters (loss aversion λ, probability weighting γ) must fall within the consensus ranges reported in meta-analyses: λ ∈ [1.5, 2.5], γ ∈ [0.6, 0.8]. Third, out-of-sample prediction accuracy for behavioral models must exceed rational benchmarks by at least 10 percentage points in hold-out validation samples. These thresholds ensure that observed anomalies are robust, reproducible, and economically meaningful rather than statistical artifacts of small samples or poor experimental design.

Prepare your workspace by creating a project directory `behavioral_econ_labs/` with subdirectories `data/`, `scripts/`, `results/`, and `documentation/`. Download the Tversky-Kahneman (1992) cumulative prospect theory paper and the Thaler-Sunstein (2008) "Nudge" framework as reference materials. Familiarize yourself with the concept of incentive compatibility: experimental choices must involve real monetary stakes (even if small) to elicit true preferences rather than hypothetical responses. A budget of $50–100 for participant payments will suffice for pilot studies with 20–30 subjects. Document all experimental protocols, randomization procedures, and data exclusion criteria in a preregistration file before data collection begins to prevent p-hacking and hindsight bias in your own analysis.

## Exercise 1: Foundational Practical Implementation

This exercise constructs the canonical Allais Paradox and Asian Disease framing experiments to demonstrate violations of expected utility theory and susceptibility to logically irrelevant description changes. You will hand-code the choice problems, administer them to a small sample, calculate choice frequencies, and perform chi-square tests for independence to verify that preferences reverse under logically equivalent framings.

Begin with the Allais Paradox, which exposes violations of the independence axiom through a pair of choice problems involving lotteries over monetary outcomes. Problem A asks subjects to choose between Lottery A1 (certainty of $1 million) and Lottery A2 (10% chance of $5 million, 89% chance of $1 million, 1% chance of $0). Problem B presents Lottery B1 (11% chance of $1 million, 89% chance of $0) versus Lottery B2 (10% chance of $5 million, 90% chance of $0). Expected utility theory requires that if a subject prefers A1 to A2, they must also prefer B1 to B2, because both choices differ only in the common consequence of receiving $1 million with 89% probability. However, the modal response pattern is A1 over A2 (certainty preference) and B2 over B1 (risk-seeking when probabilities are small), violating independence.

Construct a spreadsheet implementing these lotteries. In Excel, create a table with columns for Problem (A or B), Lottery ID (A1, A2, B1, B2), Outcome 1, Probability 1, Outcome 2, Probability 2, Outcome 3, Probability 3, and Expected Value. For Lottery A1, enter $1,000,000 at 100% probability. For A2, enter $5,000,000 at 10%, $1,000,000 at 89%, and $0 at 1%. Calculate expected values using the formula `=SUMPRODUCT(outcome_range, probability_range)`. Verify that EV(A2) = $1,390,000 exceeds EV(A1) = $1,000,000, confirming that risk-neutral agents should prefer A2. Repeat for Problem B, confirming EV(B2) = $500,000 exceeds EV(B1) = $110,000.

Administer the choice problems using a Google Form or paper survey. Randomize the order of problems across subjects to control for order effects. For each problem, present the two lotteries side-by-side with clear probability-outcome tables and ask subjects to select their preferred option. Include an attention check question (e.g., "Choose option X if you are reading carefully") to filter out careless respondents. Recruit at least 30 subjects from your institution, social network, or online labor markets (e.g., Amazon Mechanical Turk). If using MTurk, pay at least minimum wage ($7.25/hour) for an estimated 5-minute task, resulting in a $0.60 payment per subject plus platform fees.

After data collection, code the responses in a CSV file `allais_data.csv` with columns `subject_id`, `problem_A_choice` (A1 or A2), and `problem_B_choice` (B1 or B2). Load the data into R and construct a contingency table cross-tabulating Problem A and Problem B choices. Execute the following R script:

```r
library(tidyverse)

# Load data
allais <- read_csv("data/allais_data.csv")

# Create contingency table
cont_table <- table(allais$problem_A_choice, allais$problem_B_choice)
print(cont_table)

# Calculate modal response frequencies
n_total <- nrow(allais)
n_A1_B2 <- sum(allais$problem_A_choice == "A1" & allais$problem_B_choice == "B2")
n_A2_B1 <- sum(allais$problem_A_choice == "A2" & allais$problem_B_choice == "B1")
n_violation <- n_A1_B2 + n_A2_B1

cat(sprintf("Independence violations: %d / %d (%.1f%%)\n", 
            n_violation, n_total, 100 * n_violation / n_total))

# Chi-square test for independence
chisq_result <- chisq.test(cont_table)
print(chisq_result)

# Calculate effect size (Cramér's V)
cramers_v <- sqrt(chisq_result$statistic / (n_total * (min(dim(cont_table)) - 1)))
cat(sprintf("Cramér's V: %.3f\n", cramers_v))
```

Expected outcomes: The chi-square test should reject independence (p < 0.05), and the violation rate should exceed 50%. Cramér's V measures effect size; values above 0.3 indicate a medium effect. If the violation rate is below 40%, examine whether subjects understood the problems by checking attention check responses and excluding those who failed. Re-administer with improved instructions emphasizing that subjects should imagine receiving real money with the stated probabilities.

Now implement the Asian Disease framing experiment demonstrating reference point manipulation. The problem describes a disease outbreak expected to kill 600 people and presents two intervention programs. In the Gain frame, Program A saves 200 people for certain, while Program B has a 1/3 chance of saving all 600 and a 2/3 chance of saving no one. In the Loss frame, Program C results in 400 people dying for certain, while Program D has a 1/3 chance that no one dies and a 2/3 chance that 600 die. Programs A and C are identical in outcomes, as are B and D, but describing outcomes as lives saved (gain) versus lives lost (loss) reverses preferences due to loss aversion.

Create a survey with two between-subjects conditions, randomly assigning half of subjects to the Gain frame and half to the Loss frame. For the Gain frame, present: "If Program A is adopted, 200 people will be saved. If Program B is adopted, there is a 1/3 probability that 600 people will be saved and a 2/3 probability that no people will be saved. Which program would you favor?" Repeat for the Loss frame with C and D. Recruit 60 subjects (30 per condition) and record their choices in `asian_disease_data.csv` with columns `subject_id`, `frame_condition` (Gain or Loss), and `choice` (certain or risky).

Analyze the data with the following R script:

```r
# Load data
asian <- read_csv("data/asian_disease_data.csv")

# Calculate choice proportions by frame
choice_summary <- asian %>%
  group_by(frame_condition, choice) %>%
  summarise(n = n()) %>%
  mutate(prop = n / sum(n))

print(choice_summary)

# Test for frame effect using chi-square
frame_table <- table(asian$frame_condition, asian$choice)
frame_test <- chisq.test(frame_table)
print(frame_test)

# Calculate risk-seeking in loss frame vs. gain frame
gain_risk <- sum(asian$frame_condition == "Gain" & asian$choice == "risky") / 
             sum(asian$frame_condition == "Gain")
loss_risk <- sum(asian$frame_condition == "Loss" & asian$choice == "risky") / 
             sum(asian$frame_condition == "Loss")

cat(sprintf("Risk-seeking in Gain frame: %.1f%%\n", 100 * gain_risk))
cat(sprintf("Risk-seeking in Loss frame: %.1f%%\n", 100 * loss_risk))
cat(sprintf("Framing effect: %.1f percentage points\n", 100 * (loss_risk - gain_risk)))
```

Expected results: Subjects should prefer the certain option (A) in the Gain frame (70–80% certainty preference) and the risky option (D) in the Loss frame (60–70% risk-seeking), producing a framing effect of 30–40 percentage points. The chi-square test should reject the null hypothesis of frame independence. If the effect is weak (< 20 percentage points), check whether subjects perceived the equivalence between frames by adding a manipulation check question asking whether Programs A and C have the same outcome.

Document your findings in a memo summarizing the violation rates, chi-square statistics, and effect sizes. Discuss the implications for expected utility theory: the Allais Paradox demonstrates that real decision-makers overweight small probabilities and exhibit certainty effects, while the Asian Disease framing effect shows that preferences depend on arbitrary description choices rather than objective outcomes. These results motivate the need for non-expected utility models such as prospect theory that incorporate reference dependence and probability weighting.

## Exercise 2: Parameter Variation & Empirical Analysis

This exercise estimates prospect theory parameters from choice data using maximum likelihood methods, allowing you to quantify the curvature of the value function (diminishing sensitivity) and the distortion of probability weights (overweighting of small probabilities). You will construct a series of binary lottery choices spanning gains and losses, collect response data, and fit a parameterized cumulative prospect theory (CPT) model to recover individual-level or population-level preference parameters.

Prospect theory posits that individuals evaluate lotteries relative to a reference point, apply a value function $v(x)$ with diminishing sensitivity in both gains and losses, and transform objective probabilities through a weighting function $w(p)$. The canonical value function is $v(x) = x^\alpha$ for gains (x ≥ 0) and $v(x) = -\lambda(-x)^\beta$ for losses (x < 0), where α and β capture diminishing sensitivity and λ represents loss aversion. The cumulative probability weighting function introduced by Tversky and Kahneman (1992) is $w(p) = p^\gamma / (p^\gamma + (1-p)^\gamma)^{1/\gamma}$, which overweights small probabilities when γ < 1.

Design a choice set of 30 binary lottery pairs spanning four domains: small-probability gains, large-probability gains, small-probability losses, and large-probability losses. For example, Choice 1 might pit Lottery L1 ($100 with 10% probability, $0 otherwise) against Lottery L2 ($10 with 100% probability). Choice 15 could present Lottery L15 (lose $100 with 20% probability, $0 otherwise) versus Lottery L16 (lose $20 for certain). Ensure that choices include pairs where expected values are equal but probabilities differ, pairs where probabilities are equal but outcomes differ, and pairs that identify loss aversion by trading off equivalent-magnitude gains and losses.

Implement the choice set in a spreadsheet with columns: `choice_id`, `lottery_A_outcome1`, `lottery_A_prob1`, `lottery_A_outcome2`, `lottery_A_prob2`, `lottery_B_outcome1`, `lottery_B_prob1`, `lottery_B_outcome2`, `lottery_B_prob2`. Calculate expected values for each lottery to verify that the choice set includes sufficient variation in risk-return tradeoffs. For example:

```
choice_id, A_out1, A_p1, A_out2, A_p2, B_out1, B_p1, B_out2, B_p2
1, 100, 0.10, 0, 0.90, 10, 1.00, 0, 0.00
2, 50, 0.50, 0, 0.50, 20, 1.00, 0, 0.00
3, 200, 0.05, 0, 0.95, 10, 1.00, 0, 0.00
...
15, -100, 0.20, 0, 0.80, -20, 1.00, 0, 0.00
16, -50, 0.50, 0, 0.50, -25, 1.00, 0, 0.00
```

Administer the choice task via Qualtrics or a custom web application, presenting each choice sequentially with randomized lottery positions (left/right) to control for response bias. Instruct subjects that one choice will be randomly selected for real payment at the end, implementing incentive compatibility through the random lottery incentive mechanism. Recruit 50 subjects and pay the expected value of the median lottery (approximately $5–10) plus a $5 show-up fee. Export responses to `prospect_choices.csv` with columns `subject_id`, `choice_1` through `choice_30` (coded as A or B).

Estimate prospect theory parameters using maximum likelihood in R. The likelihood function for subject i choosing lottery A over lottery B in choice t is $\Pr(\text{A over B}) = \Lambda(\text{CPT}(A) - \text{CPT}(B))$, where Λ is the logistic CDF and CPT(L) computes the prospect theory value of lottery L. For a two-outcome lottery with outcomes x₁, x₂ and probabilities p₁, p₂ (ordered so x₁ > x₂), the CPT value is $\text{CPT}(L) = v(x_1) w(p_1) + v(x_2)(1 - w(p_1))$ when both outcomes are non-negative. For mixed lotteries with gains and losses, use the rank-dependent formulation separating gain and loss domains.

Implement the following R script for parameter estimation:

```r
library(tidyverse)
library(maxLik)

# Load choice data
choices <- read_csv("data/prospect_choices.csv")
choice_set <- read_csv("data/choice_set.csv")

# Reshape to long format
choices_long <- choices %>%
  pivot_longer(cols = starts_with("choice_"), 
               names_to = "choice_id", 
               values_to = "chosen",
               names_prefix = "choice_") %>%
  mutate(choice_id = as.integer(choice_id),
         chose_A = as.integer(chosen == "A"))

# Merge with choice set
data_merged <- choices_long %>%
  left_join(choice_set, by = "choice_id")

# Define value function
value_function <- function(x, alpha, beta, lambda) {
  ifelse(x >= 0, x^alpha, -lambda * (-x)^beta)
}

# Define probability weighting function (Tversky-Kahneman 1992)
weight_function <- function(p, gamma) {
  p^gamma / (p^gamma + (1 - p)^gamma)^(1/gamma)
}

# Compute CPT value of a two-outcome lottery
cpt_value <- function(out1, p1, out2, p2, alpha, beta, lambda, gamma) {
  v1 <- value_function(out1, alpha, beta, lambda)
  v2 <- value_function(out2, alpha, beta, lambda)
  w1 <- weight_function(p1, gamma)
  
  # Simple case: both outcomes same sign
  if ((out1 >= 0 & out2 >= 0) | (out1 <= 0 & out2 <= 0)) {
    return(v1 * w1 + v2 * (1 - w1))
  } else {
    # Mixed lottery: separate gains and losses
    if (out1 > 0 & out2 < 0) {
      w_gain <- weight_function(p1, gamma)
      w_loss <- weight_function(p2, gamma)
      return(v1 * w_gain + v2 * w_loss)
    } else {
      w_gain <- weight_function(p2, gamma)
      w_loss <- weight_function(p1, gamma)
      return(v2 * w_gain + v1 * w_loss)
    }
  }
}

# Log-likelihood function
log_lik <- function(params, data) {
  alpha <- params[1]
  beta <- params[2]
  lambda <- params[3]
  gamma <- params[4]
  
  # Compute CPT values
  cpt_A <- mapply(cpt_value, 
                  data$A_out1, data$A_p1, data$A_out2, data$A_p2,
                  MoreArgs = list(alpha, beta, lambda, gamma))
  cpt_B <- mapply(cpt_value, 
                  data$B_out1, data$B_p1, data$B_out2, data$B_p2,
                  MoreArgs = list(alpha, beta, lambda, gamma))
  
  # Logit choice probability
  utility_diff <- cpt_A - cpt_B
  prob_A <- plogis(utility_diff)
  
  # Log-likelihood
  ll <- sum(data$chose_A * log(prob_A) + (1 - data$chose_A) * log(1 - prob_A))
  return(ll)
}

# Initial parameter values: alpha=0.88, beta=0.88, lambda=2.25, gamma=0.65
# (Tversky-Kahneman 1992 estimates)
start_params <- c(alpha = 0.88, beta = 0.88, lambda = 2.25, gamma = 0.65)

# Run maximum likelihood estimation
mle_result <- maxLik(log_lik, start = start_params, data = data_merged,
                     method = "BFGS",
                     control = list(printLevel = 2))

# Extract and display results
summary(mle_result)
estimates <- coef(mle_result)
std_errors <- sqrt(diag(vcov(mle_result)))

cat("\nEstimated Parameters:\n")
cat(sprintf("alpha (gain sensitivity): %.3f (SE: %.3f)\n", 
            estimates["alpha"], std_errors["alpha"]))
cat(sprintf("beta (loss sensitivity): %.3f (SE: %.3f)\n", 
            estimates["beta"], std_errors["beta"]))
cat(sprintf("lambda (loss aversion): %.3f (SE: %.3f)\n", 
            estimates["lambda"], std_errors["lambda"]))
cat(sprintf("gamma (probability weighting): %.3f (SE: %.3f)\n", 
            estimates["gamma"], std_errors["gamma"]))

# Save results
write_csv(tibble(parameter = names(estimates), 
                 estimate = estimates, 
                 std_error = std_errors),
          "results/prospect_parameters.csv")
```

Expected estimates should fall in the following ranges based on meta-analytic evidence: α ∈ [0.8, 1.0], β ∈ [0.8, 1.0], λ ∈ [1.5, 2.5], γ ∈ [0.6, 0.8]. The α and β parameters below 1.0 indicate diminishing sensitivity (risk aversion for gains, risk-seeking for losses). Loss aversion λ > 1 confirms that losses loom larger than equivalent-magnitude gains. Probability weighting γ < 1 demonstrates overweighting of small probabilities and underweighting of moderate-to-large probabilities.

Validate the model by computing in-sample and out-of-sample fit. Reserve 20% of subjects as a hold-out sample, re-estimate parameters on the training sample, and predict hold-out choices using the estimated parameters. Calculate prediction accuracy as the percentage of hold-out choices correctly predicted (choosing lottery A when CPT(A) > CPT(B), and vice versa). Compare to a benchmark expected value model that predicts choices based purely on EV(A) vs. EV(B). The prospect theory model should achieve 10–15 percentage points higher accuracy, confirming its superior descriptive power.

Conduct sensitivity analysis by varying the starting values for the optimization algorithm. Re-run the MLE with five different random initializations drawn from uniform distributions: α, β ~ Uniform(0.5, 1.2), λ ~ Uniform(1.0, 3.0), γ ~ Uniform(0.4, 1.0). If all runs converge to similar parameter values (within 0.1 for each parameter), the estimates are robust to initialization. If estimates vary substantially, the likelihood surface may have multiple local maxima, indicating that your choice set lacks sufficient identifying variation. Add more choices that cleanly separate parameters (e.g., choices with certainty versus risk to identify α/β, choices with equal expected value but different outcome signs to identify λ).

Visualize the estimated value function and weighting function. Generate plots showing $v(x)$ over the range x ∈ [-200, 200] and $w(p)$ over p ∈ [0, 1] using the estimated parameters. The value function should exhibit an S-shape with a kink at the reference point (x = 0), steeper in losses than gains. The weighting function should be inverse-S-shaped, crossing the diagonal at approximately p = 0.3–0.4, indicating overweighting below and underweighting above this probability.

```r
# Plot value function
x_range <- seq(-200, 200, by = 1)
v_values <- value_function(x_range, estimates["alpha"], estimates["beta"], estimates["lambda"])

ggplot(data.frame(x = x_range, v = v_values), aes(x, v)) +
  geom_line(size = 1.2, color = "darkblue") +
  geom_hline(yintercept = 0, linetype = "dashed") +
  geom_vline(xintercept = 0, linetype = "dashed") +
  labs(title = "Estimated Value Function", x = "Outcome", y = "Value") +
  theme_minimal()

ggsave("results/value_function.png", width = 6, height = 4)

# Plot weighting function
p_range <- seq(0.01, 0.99, by = 0.01)
w_values <- weight_function(p_range, estimates["gamma"])

ggplot(data.frame(p = p_range, w = w_values), aes(p, w)) +
  geom_line(size = 1.2, color = "darkred") +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed") +
  labs(title = "Estimated Probability Weighting Function", 
       x = "Objective Probability", y = "Decision Weight") +
  theme_minimal()

ggsave("results/weighting_function.png", width = 6, height = 4)
```

Document the estimation results in a technical report presenting the parameter estimates, standard errors, goodness-of-fit statistics (log-likelihood, AIC, BIC), and validation accuracy. Compare your estimates to published benchmarks from Tversky and Kahneman (1992) and discuss any deviations. If λ < 1.5, loss aversion may be weak in your sample, possibly due to low monetary stakes or lack of genuine incentive compatibility. If γ > 0.9, probability weighting may be minimal, suggesting that subjects treated probabilities more linearly than expected—investigate whether probability information was presented clearly and whether subjects had sufficient numeracy to process it.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

This exercise probes the boundary conditions of behavioral anomalies by testing whether preference reversals and framing effects persist under conditions designed to promote rational decision-making: high stakes, market experience, learning opportunities, and transparent incentive structures. You will systematically vary experimental parameters to identify when behavioral biases attenuate or disappear, document the robustness of effects across demographic segments, and develop protocols for debiasing interventions when anomalies prove welfare-reducing.

Begin by implementing a high-stakes replication of the Asian Disease framing experiment. The standard version uses hypothetical lives saved versus lost, but critics argue that real monetary stakes might eliminate framing effects by inducing more careful deliberation. Modify the experiment to involve personal financial outcomes: in the Gain frame, subjects choose between receiving $200 for certain (Program A) or a lottery with 1/3 chance of $600 and 2/3 chance of $0 (Program B). In the Loss frame, subjects choose between losing $400 for certain (Program C) or a lottery with 1/3 chance of losing $0 and 2/3 chance of losing $600 (Program D). These are financially equivalent to the original framing but involve the subject's own money rather than abstract lives.

Recruit 80 subjects and randomly assign them to Gain or Loss frames with genuinely binding payoffs. Each subject receives a $10 show-up fee, then faces their assigned choice with real consequences: if they select the certain option in the Gain frame, they leave with $10 + $200 = $210; if they select the risky option and win, they leave with $610, otherwise $10. In the Loss frame, subjects start with $410 and face the certain loss (leaving with $10) or the risky loss lottery. This high-stakes design requires a larger experimental budget ($10 show-up × 80 subjects + $200 average gain frame payoff × 40 subjects + $200 average loss frame payoff × 40 subjects ≈ $800 + $8000 + $8000 = $16,800), but can be scaled down proportionally (e.g., divide all amounts by 10) while maintaining incentive compatibility.

Analyze the data using the same chi-square framework as Exercise 1, comparing the magnitude of the framing effect in the high-stakes version to the original hypothetical version. If the framing effect persists with similar magnitude (30–40 percentage points), behavioral anomalies are robust to stake size, supporting the external validity of lab experiments. If the effect attenuates significantly (< 15 percentage points), rationality emerges under high stakes, vindicating the evolutionary-psychology argument that biases are domain-specific adaptations that break down when real resources are at risk.

Next, test whether market experience eliminates behavioral biases by conducting a repeated-choice learning experiment. Subjects face the same Allais Paradox choice problems from Exercise 1, but repeat the task 10 times with feedback after each round showing whether the chosen lottery paid off and the cumulative earnings. If subjects are rational Bayesian learners, they should converge toward expected-value-maximizing choices (A2 and B2) as they accumulate evidence about lottery outcomes. If independence violations persist across rounds, preferences are stable rather than mistakes correctable by learning.

Implement the repeated-choice design in Python using a simple command-line interface or Jupyter notebook. The script should present each choice, record the response, simulate the lottery outcome using random number generation, display feedback, and update cumulative earnings. After 10 rounds, analyze whether the violation rate declines over time using a logistic mixed-effects regression predicting independence violations from round number with random intercepts for subjects.

```python
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
import matplotlib.pyplot as plt

# Define Allais lotteries
lotteries = {
    'A1': {'outcomes': [1000000], 'probs': [1.0]},
    'A2': {'outcomes': [5000000, 1000000, 0], 'probs': [0.10, 0.89, 0.01]},
    'B1': {'outcomes': [1000000, 0], 'probs': [0.11, 0.89]},
    'B2': {'outcomes': [5000000, 0], 'probs': [0.10, 0.90]}
}

def simulate_lottery(lottery):
    """Simulate one draw from a lottery."""
    outcomes = lottery['outcomes']
    probs = lottery['probs']
    return np.random.choice(outcomes, p=probs)

def run_allais_learning(subject_id, n_rounds=10):
    """Run repeated Allais choices with feedback."""
    results = []
    cumulative_earnings = 0
    
    for round_num in range(1, n_rounds + 1):
        print(f"\n--- Round {round_num}/10 ---")
        print(f"Cumulative earnings: ${cumulative_earnings:,.0f}")
        
        # Problem A
        print("\nProblem A:")
        print("A1: $1,000,000 for certain")
        print("A2: 10% chance of $5,000,000, 89% chance of $1,000,000, 1% chance of $0")
        choice_A = input("Choose A1 or A2: ").strip().upper()
        
        # Problem B
        print("\nProblem B:")
        print("B1: 11% chance of $1,000,000, 89% chance of $0")
        print("B2: 10% chance of $5,000,000, 90% chance of $0")
        choice_B = input("Choose B1 or B2: ").strip().upper()
        
        # Simulate outcomes (randomly pick one problem for payment)
        paid_problem = np.random.choice(['A', 'B'])
        if paid_problem == 'A':
            chosen = choice_A
            outcome = simulate_lottery(lotteries[chosen])
        else:
            chosen = choice_B
            outcome = simulate_lottery(lotteries[chosen])
        
        cumulative_earnings += outcome
        
        print(f"\nOutcome: Problem {paid_problem}, lottery {chosen} paid ${outcome:,.0f}")
        print(f"New cumulative earnings: ${cumulative_earnings:,.0f}")
        
        # Record results
        violates = (choice_A == 'A1' and choice_B == 'B2') or (choice_A == 'A2' and choice_B == 'B1')
        results.append({
            'subject_id': subject_id,
            'round': round_num,
            'choice_A': choice_A,
            'choice_B': choice_B,
            'violates_independence': violates,
            'cumulative_earnings': cumulative_earnings
        })
    
    return pd.DataFrame(results)

# Example: run for one subject
subject_data = run_allais_learning(subject_id=1, n_rounds=10)
subject_data.to_csv("data/allais_learning_subject1.csv", index=False)

# Analyze learning trend (after collecting data from multiple subjects)
def analyze_learning(data):
    """Analyze whether violations decline over rounds."""
    violation_by_round = data.groupby('round')['violates_independence'].mean()
    
    plt.figure(figsize=(8, 5))
    plt.plot(violation_by_round.index, violation_by_round.values, 
             marker='o', linewidth=2, markersize=8)
    plt.axhline(y=0.5, color='gray', linestyle='--', label='Chance level')
    plt.xlabel('Round')
    plt.ylabel('Violation Rate')
    plt.title('Learning Curve: Independence Violations Over Time')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("results/learning_curve.png")
    plt.close()
    
    # Statistical test: logistic regression
    from sklearn.linear_model import LogisticRegression
    X = data[['round']].values
    y = data['violates_independence'].values
    model = LogisticRegression()
    model.fit(X, y)
    
    coef = model.coef_[0][0]
    print(f"Logistic regression coefficient for round: {coef:.4f}")
    if coef < -0.05:
        print("Significant learning effect detected (violations decline over time)")
    else:
        print("No significant learning effect (violations persist)")

# After collecting data from 30 subjects across 10 rounds each
all_data = pd.concat([pd.read_csv(f"data/allais_learning_subject{i}.csv") 
                      for i in range(1, 31)])
analyze_learning(all_data)
```

Expected outcomes: Meta-analytic evidence suggests that violation rates decline modestly (5–10 percentage points) over the first few rounds as subjects eliminate random errors, but stabilize at 40–50% even with extensive feedback. This pattern indicates that independence violations reflect genuine preference structures rather than confusion or mistakes. If violations drop below 20% by round 10, learning is strong, suggesting that debiasing is feasible through repeated market exposure.

Now stress-test the robustness of loss aversion across demographic segments. Re-analyze the prospect theory parameter estimates from Exercise 2, stratifying subjects by age, gender, education, and income. Run separate MLE regressions for each subgroup and compare the estimated λ parameters. Conduct formal tests of parameter equality using likelihood ratio tests: estimate a constrained model forcing λ to be identical across groups and compare its log-likelihood to the unconstrained model allowing different λ values per group. The test statistic $-2(\ln L_{\text{constrained}} - \ln L_{\text{unconstrained}})$ is asymptotically χ² distributed with degrees of freedom equal to the number of parameter constraints.

```r
# Load demographic data
demographics <- read_csv("data/subject_demographics.csv")
data_with_demo <- data_merged %>%
  left_join(demographics, by = "subject_id")

# Estimate separate models by gender
male_data <- data_with_demo %>% filter(gender == "Male")
female_data <- data_with_demo %>% filter(gender == "Female")

mle_male <- maxLik(log_lik, start = start_params, data = male_data, method = "BFGS")
mle_female <- maxLik(log_lik, start = start_params, data = female_data, method = "BFGS")

lambda_male <- coef(mle_male)["lambda"]
lambda_female <- coef(mle_female)["lambda"]

cat(sprintf("Loss aversion (Male): %.3f\n", lambda_male))
cat(sprintf("Loss aversion (Female): %.3f\n", lambda_female))

# Likelihood ratio test
ll_unconstrained <- logLik(mle_male) + logLik(mle_female)
# (Constrained model requires custom estimation forcing lambda equal; omitted for brevity)
# lr_stat <- -2 * (ll_constrained - ll_unconstrained)
# p_value <- pchisq(lr_stat, df = 1, lower.tail = FALSE)
```

If loss aversion varies systematically by demographics (e.g., λ_female > λ_male, λ_low_income > λ_high_income), this suggests that behavioral biases are partly socially constructed or environment-dependent rather than universal psychological constants. Document these heterogeneity patterns and discuss implications for paternalistic policy design: if loss aversion is weaker among financially sophisticated populations, nudge interventions may be less justifiable for those groups.

Finally, develop and test a debiasing protocol targeting the Allais Paradox. Design an educational intervention explaining the independence axiom using transparent visual representations. Create a decision tree diagram showing that Problems A and B differ only in the reallocation of the common 89% chance of $1 million, making it illogical for the 89% branch to influence preferences over the remaining 11%. Administer this intervention to a treatment group, then re-elicit Allais choices and compare violation rates to a control group receiving no intervention.

Implement the intervention as a one-page PDF handout with the following elements: (1) A clear statement of the independence axiom: "If you prefer X to Y, you should also prefer any lottery that mixes X with a third option Z over the lottery that mixes Y with Z, as long as Z is the same in both." (2) A side-by-side decision tree for Problems A and B showing that both branch into an 89% node leading to $1 million, and the choice only affects the remaining 11% branch. (3) A worked example demonstrating that choosing A1 over A2 but B2 over B1 is logically inconsistent because it implies preferring $1 million to the (10/11 chance $5M, 1/11 chance $0) lottery in one context but reversing in another context that differs only by adding the same 89% branch.

Recruit 60 new subjects, randomly assign 30 to treatment (read the handout, take a comprehension quiz, then complete the Allais choices) and 30 to control (complete choices immediately). Compare violation rates using a chi-square test. If the intervention reduces violations by 20+ percentage points, debiasing is effective, supporting the "mistakes" interpretation of behavioral anomalies. If the intervention has no effect, violations reflect stable preferences resistant to education, supporting the "alternative rationality" interpretation.

```r
# Analyze debiasing intervention
debiasing_data <- read_csv("data/debiasing_experiment.csv")

violation_by_condition <- debiasing_data %>%
  group_by(condition) %>%
  summarise(violation_rate = mean(violates_independence),
            n = n())

print(violation_by_condition)

# Chi-square test
condition_table <- table(debiasing_data$condition, debiasing_data$violates_independence)
chisq_test <- chisq.test(condition_table)
print(chisq_test)

# Effect size
effect_size <- violation_by_condition$violation_rate[violation_by_condition$condition == "control"] -
               violation_by_condition$violation_rate[violation_by_condition$condition == "treatment"]
cat(sprintf("Debiasing effect: %.1f percentage points\n", 100 * effect_size))
```

Document all boundary condition tests in a comprehensive report discussing the robustness and external validity of behavioral anomalies. Conclude with practical recommendations for applied economists and policymakers: under what conditions should behavioral models replace rational choice models in welfare analysis, and when are nudge interventions justified versus paternalistic overreach? A principled stance is that behavioral anomalies warrant policy intervention only when three conditions hold: (1) the bias is empirically robust across stakes, experience, and demographics, (2) the bias leads to systematically welfare-reducing choices (not merely different choices), and (3) intervention does not impose excessive decision costs or restrict autonomy. Use your stress-test findings to evaluate whether canonical biases meet these criteria.

## Operational Reference Guide & Diagnostic Checklist

### Core Experimental Design Principles

All behavioral economics experiments must satisfy three methodological invariants to produce credible evidence. First, incentive compatibility requires that subjects face real monetary consequences or genuinely binding outcomes. Hypothetical choices introduce hypothetical bias where subjects express preferences they would not act on with real stakes. Implement incentive compatibility through the random lottery incentive mechanism: inform subjects that one choice will be randomly selected for payment at the end, ensuring each choice is treated as consequential. An acceptable minimum payment is $5 per subject for 15 minutes of participation, with lottery outcomes ranging from $0 to $50 to create meaningful variation without excessive budget requirements.

Second, randomization of treatment assignment and choice presentation order eliminates confounds from selection bias and order effects. Use computerized random number generation or random permutation tables to assign subjects to framing conditions, randomize the left-right position of lotteries in binary choices, and randomize the sequence of choice problems across subjects. Document the randomization protocol in a preregistration file before data collection and verify balance across treatment groups by testing whether observable characteristics (age, gender, education) differ significantly between groups.

Third, transparency in data exclusion criteria prevents p-hacking and selective reporting. Preregister all exclusion rules before viewing the data: exclude subjects who fail attention checks (e.g., selecting a dominated option in a catch trial), exhibit response times below 2 seconds per choice (indicating random clicking), or report in post-experiment debriefing that they did not understand the task. Apply exclusion rules mechanically to all subjects without peeking at how exclusions affect the results. Report the number of excluded subjects and the robustness of findings to alternative exclusion thresholds.

### Statistical Power and Sample Size Requirements

Detecting behavioral anomalies requires adequate statistical power to reject the null hypothesis of rational choice. For between-subjects framing effects (Asian Disease experiment), a medium effect size (Cohen's h = 0.5, corresponding to a 25 percentage point difference in choice rates) requires n = 64 subjects per condition (128 total) to achieve 80% power at α = 0.05 using a two-proportion z-test. For within-subjects designs (Allais Paradox), detecting a 30% violation rate (against a null of 0% under expected utility theory) requires n = 30 subjects to achieve 80% power using a binomial test.

Conduct power analysis before data collection using the pwr package in R. For example, to determine the required sample size for detecting a framing effect with 25 percentage points difference:

```r
library(pwr)

# Two-proportion test for framing effect
pwr_result <- pwr.2p.test(h = ES.h(0.7, 0.45), sig.level = 0.05, power = 0.80)
cat(sprintf("Required sample size per group: %.0f\n", ceiling(pwr_result$n)))
```

Adjust sample sizes upward by 20% to account for exclusions due to attention check failures or missing data. For parameter estimation via maximum likelihood, aim for at least 50 subjects with 30 choice observations each to achieve standard errors below 0.1 for key parameters (loss aversion λ, probability weighting γ). Larger samples are required when estimating heterogeneous treatment effects or subgroup parameters.

### Model Validation and Robustness Checks

Evaluate the descriptive adequacy of prospect theory models using multiple fit statistics. The log-likelihood value itself is not interpretable in isolation, but likelihood ratio tests comparing nested models (e.g., prospect theory vs. expected utility) provide formal hypothesis tests. The test statistic $\text{LR} = -2(\ln L_{\text{restricted}} - \ln L_{\text{unrestricted}})$ follows a χ² distribution with degrees of freedom equal to the number of additional parameters in the unrestricted model.

Use information criteria (AIC, BIC) to compare non-nested models. AIC = -2 ln L + 2k and BIC = -2 ln L + k ln(n), where k is the number of parameters and n is the sample size. Lower values indicate better fit, penalizing model complexity. A difference of 10+ points in BIC provides strong evidence for the preferred model. Prospect theory (4 parameters) should achieve BIC at least 20 points lower than expected utility (1 parameter: risk aversion) to justify the added complexity.

Validate predictive accuracy through cross-validation. Randomly split subjects into 80% training and 20% test sets, estimate parameters on the training set, and predict hold-out choices. Calculate accuracy, precision, recall, and area under the ROC curve (AUC) for the hold-out sample. Prospect theory should achieve hold-out accuracy exceeding 65% (compared to 50% baseline from random guessing) and AUC > 0.70. If hold-out accuracy is below 60%, the model overfits the training data, suggesting that the choice set lacks sufficient identifying variation or that subjects exhibit excessive noise/inconsistency.

### Common Failure Modes and Diagnostic Procedures

**Failure Mode 1: Weak or Null Effects in Canonical Experiments**

If the Allais violation rate is below 30% or the Asian Disease framing effect is below 15 percentage points, the experiment may suffer from comprehension failures, insufficient stakes, or atypical sample composition. Diagnose by examining attention check pass rates (should exceed 90%), average response times (should exceed 30 seconds per choice problem), and post-experiment survey responses about task understanding. Administer a comprehension quiz asking subjects to calculate expected values of simple lotteries; if pass rates are below 80%, subjects may lack numeracy required to process probabilistic information.

**Recovery Protocol:** Re-administer with enhanced instructions including worked examples, visual probability representations (pie charts showing chances), and mandatory practice trials with feedback before the main task. Increase stakes by 10x if the budget permits, or recruit from populations with higher numeracy (university students, professional samples). If effects remain weak after these adjustments, document the null result and discuss implications for external validity: laboratory anomalies may not generalize to real-world economic decisions.

**Failure Mode 2: Parameter Estimates Outside Consensus Ranges**

If MLE returns loss aversion λ < 1.0 or probability weighting γ > 1.0, the estimation has converged to an implausible region of parameter space, possibly due to flat likelihood surfaces, poor initial values, or misspecified choice sets. Diagnose by plotting the likelihood function over a grid of parameter values to visualize the surface. If the likelihood is flat (changes by less than 1 log-unit over a wide parameter range), the choice set lacks identifying power for that parameter.

**Recovery Protocol:** Add targeted choice problems that cleanly identify the problematic parameter. To identify loss aversion, add choices directly trading off gains against losses (e.g., "Accept a 50-50 gamble to win $100 or lose $X" for varying X). To identify probability weighting, add choices varying only in probabilities while holding outcomes constant (e.g., "$100 with 10% probability" vs. "$10 with 100% probability"). Re-estimate with the expanded choice set. If estimates remain implausible, consider restricting the parameter space by imposing bounds (α, β, γ ∈ [0.3, 1.2], λ ∈ [1.0, 4.0]) during optimization.

**Failure Mode 3: Learning Effects Eliminate Behavioral Anomalies**

If violation rates decline to near zero (< 10%) after 5–10 repetitions with feedback, subjects are learning to optimize according to rational choice principles, undermining the claim that behavioral biases are stable preference features. Diagnose by plotting violation rates across rounds and testing for a negative time trend using logistic regression.

**Recovery Protocol:** This is not a failure requiring correction; it is an informative boundary condition demonstrating that biases are mistakes correctable by experience rather than fundamental preference axioms. Document the learning dynamics and discuss implications: in repeated-game settings with transparent feedback (financial markets, professional decision-makers), rational choice models may suffice, while one-shot or opaque environments (consumer goods, insurance, retirement savings) may require behavioral models. Consider testing whether learning transfers across domains by training subjects on the Allais Paradox, then testing whether they exhibit fewer violations in structurally similar but superficially different problems.

### Equipment and Software Maintenance

Maintain up-to-date installations of R and Python environments with version control for reproducibility. Document package versions in a `sessionInfo.txt` file:

```r
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")
```

For Python, use a requirements.txt file:

```bash
pip freeze > requirements.txt
```

Back up raw data files immediately after collection with versioned filenames (e.g., `allais_data_2025-01-15.csv`) to prevent accidental overwrites. Store data on encrypted drives or secure cloud storage compliant with IRB regulations for human subjects research. Maintain a codebook documenting variable definitions, coding schemes, and units of measurement.

Calibrate random number generators by testing that simulated lottery outcomes match theoretical distributions. For example, simulate 10,000 draws from a lottery with 10% chance of $100 and 90% chance of $0, then verify that the sample mean is within $1 of the expected value ($10):

```python
outcomes = [100 if np.random.rand() < 0.1 else 0 for _ in range(10000)]
print(f"Sample mean: ${np.mean(outcomes):.2f} (expected: $10.00)")
```

If the sample mean deviates by more than $2, the RNG may be flawed or the simulation code contains errors. Re-check the probability values and RNG seed initialization.

### Ethical Considerations and IRB Compliance

All human subjects research requires Institutional Review Board (IRB) approval or exemption. Submit a protocol describing the experimental design, recruitment procedures, informed consent process, potential risks (typically minimal for economic choice experiments), data protection measures, and debriefing procedures. Emphasize that participation is voluntary, subjects can withdraw at any time without penalty, and data will be anonymized before analysis.

Obtain written informed consent before beginning the experiment. The consent form must disclose that subjects will make choices involving real money, that outcomes are partly random, and that payment depends on their choices and chance. For experiments involving losses (e.g., the Loss frame in Asian Disease), endow subjects with the maximum possible loss amount upfront to avoid ethical issues of taking money subjects arrived with. For example, if the maximum loss is $400, give subjects a $410 show-up fee, then implement the loss lottery by reducing their take-home payment.

Debrief subjects after the experiment, explaining the research hypotheses and educational purpose. Offer to email a summary of results after publication. If subjects exhibited severe misunderstanding of the task (e.g., believed probabilities were adversarially chosen rather than random), consider excluding their data on ethical grounds to avoid exploiting confusion, but preregister this exclusion rule to maintain transparency.

### Reporting Standards and Publication Checklist

Prepare a complete methods section covering: (1) sample size and recruitment procedure, (2) randomization protocol, (3) full text of choice problems and instructions, (4) exclusion criteria and number of excluded subjects, (5) statistical analysis plan including all tests, (6) software and package versions. Include all materials in an online appendix or repository (e.g., Open Science Framework, GitHub).

Report effect sizes (Cohen's d, Cramér's V, odds ratios) alongside p-values. A significant p-value alone does not establish practical importance; effect sizes quantify the magnitude of deviations from rationality. For framing effects, report the absolute difference in choice rates (percentage points) and the odds ratio. For parameter estimates, report point estimates, standard errors, and 95% confidence intervals.

Conduct robustness checks: (1) re-analyze with alternative exclusion criteria (e.g., include all subjects vs. strict attention filters), (2) test for order effects by interacting treatment with presentation order, (3) check for demographic heterogeneity in treatment effects, (4) validate parametric tests with non-parametric alternatives (e.g., Wilcoxon rank-sum test instead of t-test). If results are sensitive to arbitrary analytical choices, acknowledge this limitation and discuss the boundary conditions under which effects hold.

Pre-register all confirmatory analyses before viewing the data using platforms like AsPredicted or OSF Registries. Clearly distinguish confirmatory (preregistered) from exploratory (post-hoc) analyses in the paper. Exploratory findings can generate hypotheses but cannot confirm them; they require independent replication. This discipline prevents the garden of forking paths where researchers unconsciously select analytical paths that yield significant results, inflating false positive rates.

By adhering to these methodological invariants, you ensure that behavioral economics experiments produce replicable, interpretable, and policy-relevant evidence about the cognitive and motivational factors shaping real-world economic decisions. The practical skills developed through these laboratories—experimental design, incentive-compatible elicitation, structural estimation, and robustness testing—transfer directly to applied work in consumer protection regulation, pension design, health insurance exchanges, and financial literacy interventions where behavioral insights inform paternalistic policy choices.
