# Operational Verification Labs: Political Economy

## Objective & Operational Lab Setup

Political economy occupies the contested boundary between market mechanisms and institutional power structures. Where neoclassical economics assumes away distributional conflict and treats institutions as exogenous constraints, political economy places the endogenous formation of property rights, regulatory regimes, and fiscal extraction at the analytical center. These laboratories train the practitioner to dissect real-world policy outcomes not as Pareto-efficient equilibria but as the result of interest group bargaining, rent-seeking coalitions, and path-dependent institutional lock-in.

The operational objective is threefold: first, to build quantitative models of voting behavior, legislative coalition formation, and bureaucratic capture that generate falsifiable predictions about policy outcomes; second, to conduct empirical forensic analysis of actual policy episodes—trade protection lobbying, central bank independence erosion, tax code manipulation—using regression discontinuity designs, difference-in-differences estimators, and institutional event studies; third, to stress-test policy proposals against adversarial political equilibria, identifying which reform designs survive coalition defection, regulatory capture, and time-inconsistency problems.

The laboratory environment requires a hybrid analytical stack. For voting and coalition models, install Python 3.10 or later with NumPy, SciPy, Matplotlib, and NetworkX for graph-theoretic representation of legislative coalitions. For empirical regression work, install R 4.3 or later with the `fixest` package for high-dimensional fixed effects estimation, `rdrobust` for regression discontinuity inference, and `did` for staggered difference-in-differences with heterogeneous treatment effects. For institutional simulation and agent-based modeling of rent-seeking dynamics, install Mesa (Python) or NetLogo 6.3. All datasets referenced are publicly available: World Bank Governance Indicators, IMF Government Finance Statistics, Transparency International Corruption Perceptions Index, and the Database of Political Institutions (DPI) from the Inter-American Development Bank.

Prepare a working directory with subdirectories for code (`/scripts`), data (`/data`), output (`/results`), and documentation (`/docs`). Each exercise produces quantitative deliverables: coefficient tables with robust standard errors, coalition stability diagrams, and counterfactual policy simulations. The practitioner must be prepared to interpret results through the lens of mechanism design, median voter equilibria, and the Coase theorem's failure under high transaction costs and asymmetric information.

The analytical posture is forensic and adversarial. When a policy fails—trade liberalization stalls, central bank independence collapses, infrastructure investment evaporates—the political economist does not invoke exogenous shocks or irrational voters. Instead, the practitioner reverse-engineers the coalition structure, identifies which interest groups extracted veto power, quantifies the magnitude of regulatory capture, and specifies the incentive-compatible contract that would have survived the political equilibrium. This is not abstract institutional economics; this is operational policy autopsy with empirical rigor.

## Exercise 1: Foundational Practical Implementation

### Median Voter Theorem and Uni-Dimensional Policy Space Simulation

The median voter theorem provides the foundational equilibrium concept for majority-rule democracies under single-peaked preferences. Given a continuum of voters with ideal points distributed along a single policy dimension—tax rates, trade openness, immigration quotas—the Condorcet winner is the ideal point of the median voter, and no coalition can defeat this platform in pairwise majority voting. The theorem fails catastrophically under multi-dimensional policy spaces, where cycling occurs and agenda control becomes decisive, but it remains the baseline model for legislative bargaining over divisible budgets and linear tax schedules.

Construct a Python simulation of a single-issue election where 1,001 voters have ideal points drawn from a mixture distribution: 60% from a Normal distribution centered at position 40 on a 0-100 policy scale (representing a center-left bloc), 30% from a Normal distribution centered at position 70 (center-right bloc), and 10% from a Uniform distribution across the entire spectrum (swing voters with heterogeneous preferences). Two candidates simultaneously announce platforms, voters vote for the candidate whose platform minimizes their Euclidean distance to their ideal point, and the candidate with the majority wins.

Create a file `median_voter_simulation.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

np.random.seed(42)

# Generate voter ideal points from mixture distribution
n_voters = 1001
center_left = np.random.normal(40, 8, int(0.6 * n_voters))
center_right = np.random.normal(70, 8, int(0.3 * n_voters))
swing = np.random.uniform(0, 100, int(0.1 * n_voters))
ideal_points = np.concatenate([center_left, center_right, swing])
ideal_points = np.clip(ideal_points, 0, 100)
ideal_points.sort()

median_voter_position = np.median(ideal_points)

print(f"Median voter position: {median_voter_position:.2f}")
print(f"Distribution summary: mean={ideal_points.mean():.2f}, std={ideal_points.std():.2f}")

# Simulate two-candidate competition with Nash equilibrium convergence
def calculate_vote_share(platform, ideal_points):
    distances_a = np.abs(ideal_points - platform[0])
    distances_b = np.abs(ideal_points - platform[1])
    votes_a = np.sum(distances_a < distances_b) + 0.5 * np.sum(distances_a == distances_b)
    return votes_a / len(ideal_points)

# Candidates start at random positions
platform_a = np.random.uniform(20, 50)
platform_b = np.random.uniform(50, 80)

learning_rate = 0.5
for iteration in range(50):
    # Candidate A best-responds to B's position
    test_positions_a = np.linspace(0, 100, 201)
    vote_shares_a = [calculate_vote_share([pos, platform_b], ideal_points) for pos in test_positions_a]
    platform_a = test_positions_a[np.argmax(vote_shares_a)]
    
    # Candidate B best-responds to A's position
    test_positions_b = np.linspace(0, 100, 201)
    vote_shares_b = [1 - calculate_vote_share([platform_a, pos], ideal_points) for pos in test_positions_b]
    platform_b = test_positions_b[np.argmax(vote_shares_b)]
    
    if iteration % 10 == 0:
        vote_share_a = calculate_vote_share([platform_a, platform_b], ideal_points)
        print(f"Iteration {iteration}: A={platform_a:.2f} (share={vote_share_a:.3f}), B={platform_b:.2f}")

final_vote_share_a = calculate_vote_share([platform_a, platform_b], ideal_points)
print(f"\nNash Equilibrium: A={platform_a:.2f}, B={platform_b:.2f}")
print(f"Final vote shares: A={final_vote_share_a:.3f}, B={1-final_vote_share_a:.3f}")
print(f"Distance from median: A={abs(platform_a - median_voter_position):.2f}, B={abs(platform_b - median_voter_position):.2f}")

# Visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

ax1.hist(ideal_points, bins=50, density=True, alpha=0.7, color='steelblue', edgecolor='black')
ax1.axvline(median_voter_position, color='red', linestyle='--', linewidth=2, label=f'Median Voter ({median_voter_position:.1f})')
ax1.axvline(platform_a, color='green', linestyle='-', linewidth=2, label=f'Candidate A ({platform_a:.1f})')
ax1.axvline(platform_b, color='orange', linestyle='-', linewidth=2, label=f'Candidate B ({platform_b:.1f})')
ax1.set_xlabel('Policy Position (0=Far Left, 100=Far Right)', fontsize=12)
ax1.set_ylabel('Density', fontsize=12)
ax1.set_title('Median Voter Theorem: Equilibrium Convergence', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(alpha=0.3)

# Vote share as function of candidate A's position (holding B fixed at equilibrium)
test_positions = np.linspace(0, 100, 201)
vote_shares = [calculate_vote_share([pos, platform_b], ideal_points) for pos in test_positions]

ax2.plot(test_positions, vote_shares, color='darkblue', linewidth=2)
ax2.axhline(0.5, color='red', linestyle='--', linewidth=1.5, label='Majority Threshold')
ax2.axvline(median_voter_position, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
ax2.axvline(platform_a, color='green', linestyle='-', linewidth=2, label=f'Equilibrium A ({platform_a:.1f})')
ax2.fill_between(test_positions, 0.5, vote_shares, where=(np.array(vote_shares) > 0.5), alpha=0.3, color='green', label='A Wins')
ax2.set_xlabel('Candidate A Position', fontsize=12)
ax2.set_ylabel('Vote Share for Candidate A', fontsize=12)
ax2.set_title('Vote Share Landscape: Unilateral Deviation Payoffs', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(alpha=0.3)
ax2.set_ylim(0, 1)

plt.tight_layout()
plt.savefig('results/median_voter_equilibrium.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to results/median_voter_equilibrium.png")
```

Execute the script and observe the Nash equilibrium convergence. Both candidates should converge to positions within 2-3 units of the median voter position (approximately 45-48 on the 0-100 scale given the mixture distribution). The vote share landscape confirms that any unilateral deviation away from the median reduces vote share, establishing local stability. The histogram overlay demonstrates that the median voter theorem does not require symmetric or unimodal distributions; it holds for any preference distribution as long as preferences are single-peaked.

The critical operational insight is that in single-dimensional policy spaces, centrist convergence is not a normative aspiration but a positive prediction derived from majority-rule incentives. Polarization and non-convergence in real elections signal either multi-dimensional policy spaces (where cycling occurs), asymmetric information (candidates uncertain about voter distribution), or non-policy motivations (valence advantages, expressive voting, party identification overriding spatial considerations).

### Regression Discontinuity Design: Electoral Threshold Effects on Policy Outcomes

Regression discontinuity (RD) designs exploit discontinuous assignment rules to estimate causal effects when randomized experiments are infeasible. In political economy, close elections provide natural experiments: municipalities where a left-wing candidate wins by 1% versus those where a right-wing candidate wins by 1% are plausibly comparable in all dimensions except the identity of the winning party. The running variable is vote margin, the threshold is zero, and the outcome variables are subsequent policy choices—public spending levels, tax rates, regulatory stringency.

Download a dataset of Brazilian mayoral elections and municipal budget outcomes from the Brazilian Electoral Tribunal (TSE) and FINBRA fiscal database. The dataset contains 5,507 municipalities across four election cycles (2000-2012) with vote margins between left-wing PT (Workers' Party) and center-right PSDB (Brazilian Social Democracy Party) candidates, along with per-capita municipal spending in education, health, and infrastructure in the subsequent four-year term.

Create `rdd_electoral_threshold.R`:

```r
library(tidyverse)
library(rdrobust)
library(fixest)

set.seed(123)

# Simulate Brazilian municipal election dataset (representative structure)
n_municipalities <- 5507
municipalities <- tibble(
  municipality_id = 1:n_municipalities,
  state = sample(c("SP", "MG", "RJ", "BA", "RS", "PR"), n_municipalities, replace = TRUE),
  population = exp(rnorm(n_municipalities, mean = 10, sd = 1.2)),
  vote_margin_pt = rnorm(n_municipalities, mean = 0, sd = 12),  # PT margin over PSDB
  gdp_per_capita_log = rnorm(n_municipalities, mean = 9.5, sd = 0.6)
)

# Generate potential outcomes with treatment effect at threshold
# PT victory (vote_margin >= 0) increases education spending by ~8%
municipalities <- municipalities %>%
  mutate(
    pt_wins = vote_margin_pt >= 0,
    # Smooth trend in outcomes as function of vote margin
    baseline_education_spending = 800 + 15 * vote_margin_pt + 0.05 * vote_margin_pt^2 + 
                                   50 * gdp_per_capita_log + rnorm(n_municipalities, 0, 80),
    # Discontinuous jump at threshold
    education_spending_per_capita = baseline_education_spending + 
                                     ifelse(pt_wins, 65, 0) + 
                                     rnorm(n_municipalities, 0, 40),
    # Health and infrastructure for placebo tests (no true effect)
    health_spending_per_capita = 600 + 10 * vote_margin_pt + 
                                  40 * gdp_per_capita_log + 
                                  rnorm(n_municipalities, 0, 60),
    infrastructure_spending_per_capita = 450 + 8 * vote_margin_pt + 
                                          30 * gdp_per_capita_log + 
                                          rnorm(n_municipalities, 0, 55)
  )

# Summary statistics by treatment status
summary_stats <- municipalities %>%
  group_by(pt_wins) %>%
  summarise(
    n = n(),
    mean_education = mean(education_spending_per_capita),
    mean_health = mean(health_spending_per_capita),
    mean_infrastructure = mean(infrastructure_spending_per_capita),
    mean_gdp = mean(gdp_per_capita_log),
    mean_population = mean(log(population))
  )

print("Summary Statistics by PT Victory Status:")
print(summary_stats)

# Regression Discontinuity: Non-parametric estimation with robust inference
rd_education <- rdrobust(
  y = municipalities$education_spending_per_capita,
  x = municipalities$vote_margin_pt,
  c = 0,
  p = 1,  # Local linear regression
  kernel = "triangular",
  bwselect = "mserd",  # MSE-optimal bandwidth
  vce = "hc2"
)

print("\n=== RD Estimate: PT Victory Effect on Education Spending ===")
print(summary(rd_education))

# Extract key results
ate_education <- rd_education$coef[1]
se_education <- rd_education$se[1]
ci_lower_education <- rd_education$ci[1, 1]
ci_upper_education <- rd_education$ci[1, 2]
bandwidth <- rd_education$bws[1]

cat(sprintf("\nTreatment Effect: %.2f (SE=%.2f)\n", ate_education, se_education))
cat(sprintf("95%% CI: [%.2f, %.2f]\n", ci_lower_education, ci_upper_education))
cat(sprintf("Optimal Bandwidth: %.2f percentage points\n", bandwidth))

# Placebo tests: outcomes that should NOT respond to PT victory
rd_health <- rdrobust(
  y = municipalities$health_spending_per_capita,
  x = municipalities$vote_margin_pt,
  c = 0,
  p = 1,
  kernel = "triangular",
  bwselect = "mserd",
  vce = "hc2"
)

rd_infrastructure <- rdrobust(
  y = municipalities$infrastructure_spending_per_capita,
  x = municipalities$vote_margin_pt,
  c = 0,
  p = 1,
  kernel = "triangular",
  bwselect = "mserd",
  vce = "hc2"
)

print("\n=== Placebo Test: Health Spending (Expected: No Effect) ===")
print(summary(rd_health))

print("\n=== Placebo Test: Infrastructure Spending (Expected: No Effect) ===")
print(summary(rd_infrastructure))

# Visualization: RD plot with binned scatter and fitted lines
bin_width <- 2
municipalities <- municipalities %>%
  mutate(vote_margin_bin = floor(vote_margin_pt / bin_width) * bin_width + bin_width / 2)

binned_data <- municipalities %>%
  group_by(vote_margin_bin) %>%
  summarise(
    mean_education = mean(education_spending_per_capita),
    n = n()
  ) %>%
  filter(n >= 10)  # Drop bins with < 10 observations

# Fit local linear regression on each side of threshold
left_data <- municipalities %>% filter(vote_margin_pt < 0 & vote_margin_pt >= -bandwidth)
right_data <- municipalities %>% filter(vote_margin_pt >= 0 & vote_margin_pt <= bandwidth)

fit_left <- lm(education_spending_per_capita ~ vote_margin_pt, data = left_data)
fit_right <- lm(education_spending_per_capita ~ vote_margin_pt, data = right_data)

pred_left <- tibble(
  vote_margin_pt = seq(-bandwidth, 0, length.out = 100),
  predicted = predict(fit_left, newdata = tibble(vote_margin_pt = seq(-bandwidth, 0, length.out = 100)))
)

pred_right <- tibble(
  vote_margin_pt = seq(0, bandwidth, length.out = 100),
  predicted = predict(fit_right, newdata = tibble(vote_margin_pt = seq(0, bandwidth, length.out = 100)))
)

png("results/rdd_education_spending.png", width = 3600, height = 2400, res = 300)
ggplot() +
  geom_point(data = binned_data, aes(x = vote_margin_bin, y = mean_education, size = n), 
             alpha = 0.6, color = "steelblue") +
  geom_line(data = pred_left, aes(x = vote_margin_pt, y = predicted), 
            color = "red", size = 1.2) +
  geom_line(data = pred_right, aes(x = vote_margin_pt, y = predicted), 
            color = "darkgreen", size = 1.2) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "black", size = 1) +
  annotate("text", x = 5, y = max(binned_data$mean_education) * 0.95, 
           label = sprintf("ATE = %.1f\n(SE=%.1f)", ate_education, se_education),
           hjust = 0, size = 4.5, fontface = "bold") +
  labs(
    title = "Regression Discontinuity: PT Victory Effect on Education Spending",
    subtitle = sprintf("Bandwidth = %.1f pp | Local Linear Regression with Triangular Kernel", bandwidth),
    x = "Vote Margin (PT - PSDB, percentage points)",
    y = "Education Spending per Capita (BRL)",
    size = "Observations"
  ) +
  theme_minimal(base_size = 13) +
  theme(
    plot.title = element_text(face = "bold", size = 15),
    plot.subtitle = element_text(size = 11),
    legend.position = "bottom"
  )
dev.off()

cat("\nVisualization saved to results/rdd_education_spending.png\n")

# Density test: check for manipulation of running variable (McCrary test)
# If candidates can precisely manipulate vote margins, sorting around threshold invalidates RD
density_test <- rddensity::rddensity(municipalities$vote_margin_pt, c = 0)
print("\n=== McCrary Density Test (Manipulation Check) ===")
print(summary(density_test))

cat("\n=== Operational Interpretation ===\n")
cat("1. Treatment Effect Magnitude: PT victory increases education spending by ~", round(ate_education), "BRL per capita\n")
cat("   Relative effect: ~", round(100 * ate_education / mean(municipalities$education_spending_per_capita), 1), "% increase\n")
cat("2. Placebo Tests: Health and infrastructure should show null effects (|t-stat| < 2)\n")
cat("3. Density Test: p-value > 0.05 indicates no sorting around threshold (valid RD design)\n")
cat("4. Policy Implication: Left-wing governments prioritize education spending when fiscal constraints bind\n")
```

Execute the R script. The RD estimate should recover a treatment effect of approximately 65 BRL per capita (≈8% increase) with a standard error around 15-20 BRL, yielding a t-statistic above 3 and a 95% confidence interval excluding zero. The placebo tests on health and infrastructure spending should produce point estimates near zero with wide confidence intervals, confirming that the discontinuity is specific to education and not a spurious artifact of the threshold. The McCrary density test checks whether the density of the running variable (vote margin) is continuous at zero; a significant jump would indicate strategic sorting (candidates manipulating close elections), invalidating the RD design. A p-value above 0.10 confirms no evidence of manipulation.

The operational lesson is that close elections provide credible identification of partisan policy effects only when three conditions hold: continuity of potential outcomes in the running variable (smooth trends on both sides of threshold), no precise manipulation of the running variable (McCrary test passes), and common support (sufficient observations near the threshold). When these conditions are met, RD designs dominate observational regressions with controls, which suffer from omitted variable bias and functional form misspecification. The practitioner must always conduct placebo tests on outcomes the treatment should not affect and density tests for manipulation; without these diagnostics, RD estimates are no more credible than naive OLS comparisons.

## Exercise 2: Parameter Variation & Empirical Analysis

### Lobbying and Rent-Seeking: Contest Success Functions and Aggregate Deadweight Loss

Rent-seeking models formalize the dissipation of economic surplus through competitive expenditure on non-productive influence activities. When governments allocate licenses, tariffs, subsidies, or regulatory exemptions worth $R$ dollars, interest groups invest resources in lobbying to capture the rent. Tullock's contest success function specifies that group $i$'s probability of winning is $p_i = x_i^r / \sum_j x_j^r$, where $x_i$ is group $i$'s lobbying expenditure and $r > 0$ parameterizes the contest's decisiveness (higher $r$ means marginal spending more strongly tilts outcomes). In Nash equilibrium, each group invests until marginal cost equals expected marginal benefit, leading to total dissipation: aggregate lobbying expenditure approaches the full value of the rent as $r \to 1$ and the number of contestants grows.

Construct a numerical model of a tariff lobbying contest where domestic producers seek protection worth $R = 100$ million dollars (the present value of monopoly rents from excluding foreign competition). Five industry associations compete: Steel ($\theta_1 = 1.5$), Textiles ($\theta_2 = 1.2$), Agriculture ($\theta_3 = 1.0$), Automobiles ($\theta_4 = 1.3$), and Electronics ($\theta_5 = 0.9$), where $\theta_i$ represents group $i$'s lobbying effectiveness (ability to convert dollars into political influence due to geographic concentration, PAC infrastructure, or revolving-door connections). The contest success function is $p_i = (\theta_i x_i)^r / \sum_j (\theta_j x_j)^r$.

Create `rent_seeking_simulation.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# Parameters
R = 100  # Rent value (million dollars)
theta = np.array([1.5, 1.2, 1.0, 1.3, 0.9])  # Lobbying effectiveness
n_groups = len(theta)
group_names = ["Steel", "Textiles", "Agriculture", "Automobiles", "Electronics"]

def contest_success_function(x, r):
    """Compute win probabilities given expenditures x and decisiveness r"""
    effective_spending = (theta * x) ** r
    total = np.sum(effective_spending)
    if total == 0:
        return np.ones(n_groups) / n_groups
    return effective_spending / total

def best_response(x_i, x_minus_i, r):
    """Compute group i's best response to others' spending"""
    def foc(x):
        if x <= 0:
            return -R  # Marginal benefit at zero spending
        # Marginal benefit: dP_i/dx_i * R
        total_effective = (theta[i] * x) ** r + np.sum((theta * x_minus_i) ** r)
        prob_i = (theta[i] * x) ** r / total_effective
        marginal_prob = r * (theta[i] ** r) * (x ** (r - 1)) / total_effective - \
                         (r * (theta[i] ** r) * (x ** r) * (theta[i] ** r) * (x ** (r - 1))) / (total_effective ** 2)
        marginal_benefit = marginal_prob * R
        marginal_cost = 1
        return marginal_benefit - marginal_cost
    
    # Solve first-order condition
    if foc(0) <= 0:
        return 0  # Corner solution: don't lobby
    x_optimal = fsolve(lambda x: foc(x[0]) if x[0] > 0 else -R, [1.0])[0]
    return max(0, x_optimal)

def compute_nash_equilibrium(r, max_iterations=1000, tolerance=1e-6):
    """Compute Nash equilibrium lobbying expenditures"""
    x = np.ones(n_groups) * 5  # Initial guess
    
    for iteration in range(max_iterations):
        x_new = np.zeros(n_groups)
        for i in range(n_groups):
            x_minus_i = np.concatenate([x[:i], x[i+1:]])
            x_new[i] = best_response(i, x_minus_i, r)
        
        if np.max(np.abs(x_new - x)) < tolerance:
            return x_new
        x = 0.3 * x_new + 0.7 * x  # Damped iteration for stability
    
    print(f"Warning: Nash equilibrium did not converge for r={r:.2f}")
    return x

# Compute equilibria for different decisiveness parameters
r_values = np.linspace(0.5, 2.0, 16)
results = []

for r in r_values:
    x_eq = compute_nash_equilibrium(r)
    p_eq = contest_success_function(x_eq, r)
    total_dissipation = np.sum(x_eq)
    dissipation_rate = total_dissipation / R
    
    results.append({
        'r': r,
        'expenditures': x_eq.copy(),
        'probabilities': p_eq.copy(),
        'total_dissipation': total_dissipation,
        'dissipation_rate': dissipation_rate
    })
    
    print(f"\nr = {r:.2f}:")
    print(f"  Total dissipation: ${total_dissipation:.2f}M ({dissipation_rate:.1%} of rent)")
    for i in range(n_groups):
        net_payoff = p_eq[i] * R - x_eq[i]
        print(f"  {group_names[i]:12s}: spend=${x_eq[i]:5.2f}M, prob={p_eq[i]:.3f}, net=${net_payoff:6.2f}M")

# Visualization
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

# Panel 1: Dissipation rate vs decisiveness
dissipation_rates = [res['dissipation_rate'] for res in results]
ax1.plot(r_values, dissipation_rates, 'o-', linewidth=2.5, markersize=8, color='darkred')
ax1.axhline(1.0, linestyle='--', color='black', linewidth=1.5, alpha=0.7, label='Full Dissipation')
ax1.fill_between(r_values, 0, dissipation_rates, alpha=0.3, color='darkred')
ax1.set_xlabel('Decisiveness Parameter (r)', fontsize=13, fontweight='bold')
ax1.set_ylabel('Aggregate Dissipation Rate', fontsize=13, fontweight='bold')
ax1.set_title('Rent Dissipation vs Contest Decisiveness', fontsize=14, fontweight='bold')
ax1.grid(alpha=0.3)
ax1.legend(fontsize=11)
ax1.set_ylim(0, max(dissipation_rates) * 1.1)

# Panel 2: Expenditure by group vs decisiveness
for i in range(n_groups):
    expenditures_i = [res['expenditures'][i] for res in results]
    ax2.plot(r_values, expenditures_i, 'o-', linewidth=2, markersize=6, label=group_names[i])
ax2.set_xlabel('Decisiveness Parameter (r)', fontsize=13, fontweight='bold')
ax2.set_ylabel('Equilibrium Lobbying Expenditure ($M)', fontsize=13, fontweight='bold')
ax2.set_title('Lobbying Expenditure by Interest Group', fontsize=14, fontweight='bold')
ax2.grid(alpha=0.3)
ax2.legend(fontsize=10, loc='upper left')

# Panel 3: Win probability distribution at r=1.0
r_baseline = 1.0
result_baseline = [res for res in results if abs(res['r'] - r_baseline) < 0.01][0]
probs_baseline = result_baseline['probabilities']
colors_baseline = plt.cm.viridis(np.linspace(0.2, 0.9, n_groups))
bars = ax3.bar(group_names, probs_baseline, color=colors_baseline, edgecolor='black', linewidth=1.5)
ax3.set_ylabel('Win Probability', fontsize=13, fontweight='bold')
ax3.set_title(f'Equilibrium Win Probabilities (r={r_baseline:.1f})', fontsize=14, fontweight='bold')
ax3.grid(axis='y', alpha=0.3)
ax3.set_ylim(0, max(probs_baseline) * 1.2)
for bar, prob in zip(bars, probs_baseline):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{prob:.2%}', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Panel 4: Net payoffs vs decisiveness
for i in range(n_groups):
    net_payoffs_i = [res['probabilities'][i] * R - res['expenditures'][i] for res in results]
    ax4.plot(r_values, net_payoffs_i, 'o-', linewidth=2, markersize=6, label=group_names[i])
ax4.axhline(0, linestyle='--', color='black', linewidth=1.5, alpha=0.5)
ax4.set_xlabel('Decisiveness Parameter (r)', fontsize=13, fontweight='bold')
ax4.set_ylabel('Expected Net Payoff ($M)', fontsize=13, fontweight='bold')
ax4.set_title('Net Payoffs: Expected Rent Minus Lobbying Cost', fontsize=14, fontweight='bold')
ax4.grid(alpha=0.3)
ax4.legend(fontsize=10, loc='upper right')

plt.tight_layout()
plt.savefig('results/rent_seeking_equilibrium.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n" + "="*80)
print("OPERATIONAL SUMMARY")
print("="*80)
print(f"Rent at stake: ${R}M (tariff protection present value)")
print(f"Dissipation rate at r=1.0: {result_baseline['dissipation_rate']:.1%}")
print(f"Total deadweight loss: ${result_baseline['total_dissipation']:.2f}M")
print(f"\nKey Findings:")
print(f"1. As decisiveness (r) increases, marginal spending becomes more effective")
print(f"2. Groups with higher effectiveness (θ) spend more and win more often")
print(f"3. All groups earn positive net payoffs despite dissipation (no pure common-pool tragedy)")
print(f"4. Policy implication: Transparent allocation rules (low r) reduce rent-seeking waste")
print("\nVisualization saved to results/rent_seeking_equilibrium.png")
```

Execute the script. At $r = 1.0$, aggregate dissipation should reach 60-80% of the rent value, with Steel (highest $\theta = 1.5$) spending the most and winning with probability 0.25-0.30, while Electronics (lowest $\theta = 0.9$) spends least and wins with probability 0.15-0.18. As $r$ increases toward 2.0, the contest becomes more winner-take-all, increasing dissipation toward 90-95% of $R$, because marginal spending has higher leverage in swaying the outcome. Conversely, as $r$ falls toward 0.5, the contest becomes more random (lobbying less decisive), reducing equilibrium expenditures to 40-50% of $R$.

The critical policy insight is that institutional design directly controls dissipation rates. Transparent, rule-based allocation mechanisms (competitive auctions, objective scoring criteria) correspond to low $r$, minimizing rent-seeking waste. Opaque, discretionary processes (bureaucratic favoritism, closed-door negotiations) correspond to high $r$, maximizing dissipation. The practitioner evaluating regulatory reform proposals must estimate the implied decisiveness parameter: does the reform make marginal lobbying spending more or less effective? A reform that increases transparency but concentrates decision authority in a single regulator may paradoxically increase $r$ and dissipation by making targeted influence more decisive.

### Panel Data Event Study: Central Bank Independence and Inflation Outcomes

Central bank independence—the statutory and operational insulation of monetary authorities from fiscal and political pressure—represents a canonical institutional reform with measurable macroeconomic consequences. The theoretical prediction is straightforward: independent central banks commit to low inflation because they do not face re-election incentives to engineer pre-electoral booms, and their credibility anchors inflation expectations. Empirical identification exploits discrete legal reforms that grant independence: New Zealand's Reserve Bank Act (1989), Bank of England independence (1997), European Central Bank establishment (1999). The event study design estimates average treatment effects on inflation using difference-in-differences with staggered treatment timing.

Construct a panel dataset of 32 OECD countries from 1980 to 2020, coding central bank independence reforms as discrete events and tracking annual CPI inflation rates before and after. Use the Cukierman-Webb-Neyapti (CWN) index of legal independence (0-1 scale) and the Dincer-Eichengreen index of transparency (0-15 scale) as continuous treatment intensity measures. The baseline specification is a two-way fixed effects regression with country and year fixed effects; the dynamic specification adds event-time leads and lags to trace out pre-trends and post-reform trajectories.

Create `central_bank_independence_event_study.R`:

```r
library(tidyverse)
library(fixest)
library(did)

set.seed(456)

# Simulate OECD panel with staggered central bank independence reforms
countries <- c("AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CZE", "DNK", "EST", "FIN",
               "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN", "KOR",
               "LVA", "LTU", "MEX", "NLD", "NZL", "NOR", "POL", "PRT", "SVK", "SVN",
               "ESP", "SWE", "CHE", "TUR", "GBR", "USA")

years <- 1980:2020
n_years <- length(years)

# Treatment timing: reforms clustered in early 1990s and late 1990s
reform_years <- c(
  "NZL" = 1989, "CHL" = 1990, "CAN" = 1991, "GBR" = 1997, "JPN" = 1998,
  "KOR" = 1998, "POL" = 1998, "MEX" = 1994, "ISR" = 1985, "SWE" = 1999,
  "NOR" = 2001, "CZE" = 1993, "HUN" = 2001, "SVK" = 1993, "SVN" = 1991,
  "EST" = 1993, "LVA" = 1992, "LTU" = 1994
)

panel <- expand_grid(
  country = countries,
  year = years
) %>%
  mutate(
    # Baseline inflation: declining trend + country fixed effect + AR(1) error
    country_fe = rnorm(1, mean = 0, sd = 2)[match(country, unique(country))],
    time_trend = -0.15 * (year - 1980),
    reform_year = reform_years[country],
    treated = !is.na(reform_year),
    years_since_reform = ifelse(treated, year - reform_year, NA),
    post_reform = treated & (years_since_reform >= 0)
  ) %>%
  group_by(country) %>%
  mutate(
    # AR(1) inflation shocks
    shock = arima.sim(n = n_years, list(ar = 0.6), sd = 1.5) %>% as.numeric()
  ) %>%
  ungroup() %>%
  mutate(
    # Treatment effect: -2 pp inflation after reform (gradual phase-in over 3 years)
    treatment_effect# Operational Verification Labs: Political Economy

## Objective & Operational Lab Setup

Political economy examines how institutions, power structures, and incentive systems shape resource allocation and economic outcomes. Unlike abstract microeconomic equilibrium theory or pure macroeconomic forecasting, political economy operationalization requires you to model the boundary between formal institutions (constitutional law, property rights regimes, central bank charters) and actual economic behavior (rent-seeking, regulatory capture, incumbent protection, policy transmission lags). This laboratory sequence trains you to construct empirical audits of real-world policy institutions, measure institutional drift from theoretical ideal states, simulate policy intervention scenarios under competing interest groups, and diagnose failure modes when formal rules produce unintended outcomes.

The operational challenge is that political economy lacks a single universal toolkit—instead, practitioners synthesize microeconomic theory (consumer choice, firm behavior under constraints), macroeconomic accounting (sectoral flows, distributional impacts), institutional analysis (transaction cost measurement, contract design), and behavioral observation (revealed preferences under political pressure). Your verification labs will combine spreadsheet-based institutional audits, econometric regression models fitted to time-series policy data, scenario simulation under competing institutional regimes, and stress tests that push policy mechanisms to failure boundaries.

### Lab Environment & Authentication Setup

You will require the following operational infrastructure: a spreadsheet application (Microsoft Excel, Google Sheets, or LibreOffice Calc) for institutional accounting and scenario modeling; a statistical package with time-series and regression capability (R with the `tidyverse` and `dynlm` packages, or Python with `pandas`, `statsmodels`, and `numpy`); access to public macroeconomic data repositories (Federal Reserve Economic Data [FRED], World Bank Open Data, OECD Statistics, IMF Primary Balance Sheet, ECB Statistical Data Warehouse); and a text editor or Jupyter notebook environment for scripting reproducible analyses. All exercises use publicly available data and open-source analytical frameworks—no proprietary software or commercial datasets are required.

Before beginning Exercise 1, validate your environment by confirming that you can retrieve a single time-series from FRED (Federal Reserve Economic Data). Use the `fredr` R package or direct API access via Python's `requests` library to pull the U.S. federal funds rate (series ID: DFF) for the period 2008–2024. This serves as your baseline verification that you can operationally access the data infrastructure upon which all political economy empirical work rests. If FRED access fails, verify your internet connection, API key status (if required), and firewall permissions before proceeding.

---

## Exercise 1: Foundational Practical Implementation — Institutional Audit & Distributional Impact Mapping

### Exercise 1A: Property Rights & Distributional Rent Measurement

Political economy's foundation lies in understanding how institutions allocate property rights and how those allocations generate distributional rents—that is, income flows that accrue to specific actors not because of competitive market process but because of formal or informal institutional protection. Your first operational task is to construct an institutional audit that maps rent flows in a single market sector and measures how institutional design choices (patent protection duration, tariff schedules, regulatory entry barriers, subsidy targeting) produce observed distributional outcomes.

**Operational Scenario:** You will audit the U.S. pharmaceutical patent system's distributional impact. The core institutional design question is whether a standard 20-year patent duration (from filing date, per the Patent Act of 1984) generates socially justified innovation incentives or functions primarily as a rent-extraction mechanism for incumbent firms.

Begin by constructing a simple institutional rent calculation spreadsheet. Open your spreadsheet application and create a structured model with the following columns:

| Drug Name | Therapeutic Class | Patent Issue Date | Patent Expiration Date | Peak Annual Sales (USD Millions) | Years at Peak Sales | Generic Entry Lag (months) | Discounted Rents (5% Discount) | Generic Competition Impact |
|-----------|-------------------|-------------------|------------------------|----------------------------------|---------------------|---------------------------|--------------------------------|----------------------------|
| Lipitor | Statin | 1996-03-27 | 2011-11-30 | 12,700 | 8 | 7 | 78,250 | −70% (2012–2020) |
| Atorvastatin Generic | Statin | N/A | N/A | 3,200 | — | 0 | N/A | Competitive displacement |
| Viagra | Erectile Dysfunction | 1996-10-16 | 2020-04-21 | 1,930 | 18 | 3 | 24,680 | −85% (2021–2024) |
| Sildenafil Generic | Erectile Dysfunction | N/A | N/A | 280 | — | 0 | N/A | Competitive displacement |

This table structure embodies the core rent-measurement logic. The "Discounted Rents" column uses the formula: $$\text{Rent} = \sum_{t=1}^{T} \frac{\text{Annual Sales}_{t} \times \text{Gross Margin}_{t}}{(1 + r)^t}$$

where $r = 0.05$ (a standard 5% discount rate used in policy evaluation), $T$ equals years of above-competitive profitability under patent protection, and Annual Sales × Gross Margin estimates the economic profit extractable because competitors cannot legally enter.

For this exercise, use publicly available FDA Orange Book data (U.S. Food and Drug Administration Orange Book: Approved Drug Products with Therapeutic Equivalence Evaluations), which lists all approved drugs, patent dates, and generic entry dates. Access this via the FDA's website or commercial health data APIs. For each drug in the table above, populate actual dates and actual sales figures from FDA records and SEC filings (access SEC EDGAR for 10-K and 10-Q filings of pharmaceutical manufacturers). If exact sales data is unavailable, use average industry gross margins (typically 60–80% for branded pharmaceuticals) as conservative estimates.

Now construct the analysis cell: Calculate total cumulative rents under the current 20-year patent regime. Sum the "Discounted Rents" column. In the example above, the cumulative rent from just these four molecules totals approximately $102,930 million. This represents income transferred from consumers and insurers to patent holders because institutional rules prevent generic competition. The institutional question is whether this rent magnitude aligns with ex ante innovation incentives—that is, do firms require $100+ billion in pharmaceutical sector rents to justify R&D investment?

To answer this operationally, construct a second analytical layer. In a new spreadsheet section, model the relationship between patent duration and innovation supply. Research published papers in the health economics literature (particularly work by Acemoglu, Finkelstein, and others on the pharmaceutical patent-innovation nexus) to extract empirically estimated elasticities. A typical elasticity estimate from the literature is approximately 0.3–0.5, meaning a 10% increase in patent duration induces a 3–5% increase in R&D spending. Use this relationship to construct a counterfactual scenario:

Calculate what pharmaceutical innovation would be under a hypothetical 15-year patent regime (instead of 20 years). Using an elasticity of 0.4, the reduction is: $$\Delta \text{Innovation} = 0.4 \times \frac{15 - 20}{20} = 0.4 \times (-0.25) = -0.10$$

meaning innovation would decline by approximately 10%. Now estimate the social welfare trade-off. The 10% reduction in innovation might eliminate the development of 2–3 drugs that would have been approved under the 20-year regime. Estimate the aggregate health benefit forgone by such drugs (using quality-adjusted life years or cost-effectiveness thresholds from health economic studies). If the forgone health benefit (measured in present-value terms) is less than the rent savings from generic competition arriving 5 years earlier, the institutional design is rent-extractive rather than innovation-incentive-optimized.

**Verification Checkpoint:** Your institutional audit should produce three deliverables: (1) a completed rent calculation table with actual data for 10–15 major pharmaceutical molecules; (2) a sensitivity analysis showing how cumulative rents change under patent durations of 15, 17.5, 20, 22.5, and 25 years; and (3) a recommendation statement specifying whether current U.S. patent duration produces rents that exceed plausible innovation incentive requirements. If your analysis shows cumulative rents exceed by 50%+ the estimated innovation incentive level, institutional rent-extraction is operationally verified. If cumulative rents fall short by 30%+, institutional rent-inadequacy is verified. If the two measures lie within 30%, the regime is near-optimal (under your empirical assumptions).

---

### Exercise 1B: Regulatory Capture Measurement & Policy Outcome Inversion

Political economy theory predicts that regulated industries (where governments set prices, entry conditions, or service standards) are vulnerable to regulatory capture—the phenomenon where the regulated firm influences the regulator to produce outcomes favoring the firm rather than the public interest. Your operational task is to measure evidence of regulatory capture by comparing stated policy objectives against empirical policy outcomes and identifying divergences that suggest capture.

**Operational Scenario:** You will audit U.S. telecommunications regulatory capture by examining whether the Federal Communications Commission (FCC) decisions on broadband price regulation and infrastructure investment align with stated objectives (affordability, universal service, innovation) or have been inverted to favor incumbent providers.

Begin by constructing a timeline-based policy audit. In a new spreadsheet, create columns for (1) FCC regulatory decision date, (2) stated policy objective, (3) predicted outcome if truly implemented, (4) actual empirical outcome, and (5) discrepancy indicator.

| FCC Decision | Date | Stated Objective | Predicted Outcome (Theory) | Actual Empirical Outcome | Discrepancy |
|--------------|------|------------------|----------------------------|--------------------------|-------------|
| Broadband Classification as "Information Service" | 2002 | Promote private investment in broadband infrastructure | Competitive entry by new providers, infrastructure investment | Market consolidation; 2 carriers control 60% of markets; investment decline post-2015 | Yes — Outcome inverted |
| Net Neutrality Reclassification (Title II) | 2015 | Ensure open internet; prevent ISP gatekeeping | ISPs required to treat all traffic equally; new entrants can compete fairly | ISP blocking diminished temporarily; however, repealed in 2017 | Partial reversal |
| Title II Repeal | 2017 | Promote broadband investment and innovation | Increased private investment; faster speed deployment | Investment flat/declining; speed improvements slower than peer nations | Outcome misaligned |

The key operational step is populating the "Actual Empirical Outcome" column with quantitative evidence, not inference. For each FCC decision, retrieve actual broadband market data from three sources: (1) FCC Form 477 Broadband Deployment Reports (available via FCC database), which document broadband availability, speeds, and prices by county; (2) SEC 10-K filings from major broadband providers (Comcast, Verizon, AT&T, Charter), reporting capital expenditure, pricing, and customer acquisition; and (3) academic datasets on broadband pricing and availability (e.g., the National Broadband Map, BroadbandNow speed tests, Pew Research broadband adoption data).

Now construct the statistical test for capture. Extract broadband pricing data pre- and post-each FCC decision. For the 2002 "Information Service" classification, retrieve average broadband prices from FCC Form 477 data for 2000–2002 (pre-decision) and 2003–2008 (post-decision). Calculate whether prices declined (supporting the stated "competition" objective) or increased (suggesting capture). The empirical finding from historical FCC data shows broadband prices actually increased by 25–35% in real terms during the post-2002 period, despite the stated pro-competition objective. This outcome inversion is operationally consistent with capture.

Repeat this analysis for infrastructure investment. The stated objective of the 2002 and 2017 FCC decisions was to promote private broadband infrastructure investment. However, extract capital expenditure data from provider 10-K filings (available via SEC EDGAR). Compare average annual CapEx as a percentage of revenue pre- and post-decision. The empirical finding is that CapEx-to-revenue ratios declined from approximately 18–22% (2000–2005) to 14–16% (2010–2024), contradicting the stated objective.

Finally, quantify the welfare loss from observed capture. Use revealed preference: if consumers and businesses were willing to pay for faster broadband (as shown by international comparisons where competitive markets deliver 100+ Mbps at lower prices), estimate the consumer surplus transferred to providers through capture-enabled price elevation and investment reduction. Calculate this as:

$$\text{Welfare Loss} = \int_{p_{\text{observed}}}^{p_{\text{competitive}}} Q(p) \, dp$$

where $p_{\text{observed}}$ is the actual U.S. broadband price, $p_{\text{competitive}}$ is the price that would prevail in a competitive market (inferred from international comparisons), and $Q(p)$ is the demand curve estimated from FCC and Pew Research data.

**Verification Checkpoint:** Your regulatory capture audit should produce: (1) a completed policy-outcome table for 5–7 major FCC decisions spanning 2000–2024; (2) a statistical summary showing percentage divergence between stated objectives and actual outcomes; (3) quantified evidence of market consolidation (HHI index, market share concentration) before and after each decision; and (4) a welfare loss estimate in billions of dollars. If outcomes diverge from stated objectives by 50%+, and divergence favors incumbent providers, regulatory capture is operationally verified.

---

## Exercise 2: Parameter Variation & Empirical Analysis — Institutional Regime Comparison & Macroeconomic Transmission

### Exercise 2A: Central Bank Independence & Inflation Outcomes — Institutional Regime Comparison

Political economy recognizes that the same monetary policy rule (e.g., the Taylor Rule for interest rate setting) will produce different inflation and output outcomes depending on institutional structure—specifically, whether the central bank possesses legal independence from political pressure. Your operational task is to construct an empirical comparison of monetary policy transmission under two contrasting institutional regimes: operationally independent central banks versus politically subordinate central banks.

**Operational Scenario:** You will compare monetary policy effectiveness in two economies with similar baseline conditions but different central bank institutional designs: the United States (with a legally independent Federal Reserve) and Turkey (where central bank independence has eroded since 2015). The analytical question is whether inflation volatility and real output stability differ systematically as institutional independence changes, holding baseline macroeconomic conditions constant.

Begin by retrieving monthly time-series data for both economies. Use FRED (U.S.) and Turkish Statistical Institute (TURKSTAT) data repositories to construct parallel datasets covering January 2010 through December 2023 (14 years of observations). For each economy, retrieve: (1) policy interest rate (federal funds rate for the U.S.; policy rate for Turkey's Central Bank); (2) inflation rate (CPI percent change); (3) real GDP growth rate (annualized); (4) unemployment rate; and (5) central bank balance sheet size (total assets, as a ratio to nominal GDP).

Organize the data in a spreadsheet with rows representing monthly observations and columns representing each series for each economy. The data should look like this structure:

| Date | US Fed Funds Rate (%) | US CPI Inflation (%) | US GDP Growth (%) | Turkey Policy Rate (%) | Turkey CPI Inflation (%) | Turkey GDP Growth (%) | US CB Independence Index | Turkey CB Independence Index |
|------|----------------------|----------------------|-------------------|------------------------|--------------------------|----------------------|------------------------|-----------------------------|
| 2010-01 | 0.18 | 2.1 | −2.1 | 6.25 | 4.8 | −0.5 | 0.85 | 0.72 |
| 2010-02 | 0.18 | 2.3 | −1.9 | 6.25 | 5.2 | 0.1 | 0.85 | 0.72 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 2023-12 | 5.33 | 3.4 | 2.5 | 24.00 | 61.5 | −4.7 | 0.85 | 0.38 |

Source central bank independence indices from the Alesina-Summers Central Bank Independence Index (available in academic literature) or the Grilli-Masciandaro-Tabellini index, which quantifies legal independence on a 0–1 scale based on charter provisions, governor appointment procedures, and operational autonomy.

Now construct the empirical analysis. Divide the time period into two sub-periods: Period 1 (January 2010 – December 2015), before major Turkish central bank independence erosion; and Period 2 (January 2016 – December 2023), after independence decline. Calculate basic descriptive statistics for each economy in each period:

$$\text{Mean Inflation} = \frac{1}{n} \sum_{t=1}^{n} \pi_t$$

$$\text{Inflation Volatility} = \sqrt{\frac{1}{n} \sum_{t=1}^{n} (\pi_t - \bar{\pi})^2}$$

where $\pi_t$ is the inflation rate in month $t$ and $n$ is the number of months in the period.

The empirical finding should show that U.S. inflation mean and volatility remained relatively stable across both periods (approximately 2% mean, 0.6–0.8% standard deviation), while Turkish inflation and volatility increased substantially from Period 1 (approximately 8.1% mean, 2.2% volatility) to Period 2 (approximately 24.6% mean, 18.3% volatility). The institutional interpretation is that political pressure on the Turkish central bank to finance government spending produced monetary accommodation, inflation acceleration, and currency depreciation—a classic political economy outcome under weak institutional constraints.

Next, construct a regression model to quantify the relationship between institutional independence and inflation outcomes. Estimate the following specification:

$$\text{Inflation}_t = \alpha + \beta_1 \times \text{Lagged Inflation}_{t-1} + \beta_2 \times \text{Output Gap}_t + \beta_3 \times \text{CB Independence}_t + \beta_4 \times \text{Policy Rate}_{t-1} + \epsilon_t$$

The output gap is calculated as $(y_t - y_t^*) / y_t^*$, where $y_t$ is actual real GDP and $y_t^*$ is potential real GDP (estimated via Hodrick-Prescott filter available in most statistical packages). Estimate this regression separately for the U.S. and Turkey using ordinary least squares (OLS) with Newey-West standard errors (which correct for serial correlation typical in macroeconomic data). The coefficient $\beta_3$ captures the ceteris paribus effect of central bank independence on inflation. A negative $\beta_3$ indicates that greater independence reduces inflation; a positive or zero $\beta_3$ suggests independence has no effect or is offset by other factors.

The empirical finding should be approximately: U.S. $\beta_3 \approx -1.2$ (with t-statistic ≈ −2.8), indicating that a one-unit increase in institutional independence reduces inflation by roughly 1.2 percentage points, holding other factors constant. For Turkey, $\beta_3$ may be close to zero or positive during the full 2010–2023 period (because both independence and inflation varied in complex ways), but the structural break is visible: the post-2016 period shows political pressure on monetary policy directly translated into inflation acceleration.

**Verification Checkpoint:** Your institutional regime comparison should produce: (1) cleaned and merged time-series datasets for both economies; (2) a summary table comparing mean inflation, inflation volatility, output growth, and unemployment across institutional regimes; (3) estimated regression coefficients with standard errors and test statistics; and (4) a qualitative interpretation explaining why central bank independence matters for inflation outcomes. If your analysis shows that inflation volatility and mean inflation remain lower in the independent central bank regime (U.S.) despite similar external shocks (global commodity prices, financial crisis impacts), institutional independence is operationally verified as economically consequential.

---

### Exercise 2B: Supply-Side Institution Design — Labor Market Rigidity & Unemployment Persistence

Political economy recognizes that labor market institutions (minimum wage floors, employment protection legislation, union bargaining structures, unemployment insurance design) fundamentally shape how labor markets equilibrate and how economies absorb shocks. Your operational task is to measure empirically how institutional variation in labor market rigidity produces different unemployment persistence profiles across economies.

**Operational Scenario:** You will compare unemployment dynamics in three economies with structurally different labor market institutions: the United States (flexible labor market with weak employment protection); Germany (rigid labor market with strong employment protection but active labor market policies); and Spain (rigid labor market with weak labor market policies and high unemployment persistence). The question is whether institutional design predicts observed unemployment outcomes.

Retrieve monthly unemployment rate data for all three economies from OECD Statistics database (available at stats.oecd.org) or national statistical agencies (U.S. Bureau of Labor Statistics, Destatis for Germany, INE for Spain) covering January 2000 through December 2023. Additionally, retrieve labor market rigidity indices from the World Bank's Doing Business Database or OECD employment protection legislation (EPL) indices, which quantify institutional constraints on hiring and firing on a 0–6 scale.

Organize the data:

| Date | US Unemployment (%) | Germany Unemployment (%) | Spain Unemployment (%) | US EPL Index | Germany EPL Index | Spain EPL Index |
|------|---------------------|--------------------------|------------------------|--------------|-------------------|-----------------|
| 2000-01 | 4.0 | 8.3 | 13.1 | 0.21 | 2.80 | 3.10 |
| 2000-02 | 4.1 | 8.4 | 13.2 | 0.21 | 2.80 | 3.10 |
| ... | ... | ... | ... | ... | ... | ... |
| 2023-12 | 3.7 | 5.8 | 11.5 | 0.21 | 2.79 | 3.08 |

Now construct the empirical analysis. The key political economy insight is that labor market rigidity (high EPL scores) produces persistence in unemployment shocks—workers laid off during recessions remain unemployed longer because firms face high regulatory costs to rehire, and workers have weaker incentives to search. To measure this persistence, estimate the autocorrelation of unemployment rates. Calculate the first-order autocorrelation for each economy:

$$\rho = \frac{\text{Cov}(u_t, u_{t-1})}{\text{Var}(u_t)}$$

where $u_t$ is the unemployment rate in month $t$. The autocorrelation should be higher in Germany (approximately 0.95–0.98) and especially Spain (approximately 0.97–0.99) relative to the U.S. (approximately 0.90–0.93), reflecting institutional persistence in unemployment.

Next, decompose unemployment into trend and cyclical components. Use the Hodrick-Prescott filter to separate the long-run trend in unemployment from cyclical fluctuations. The operational hypothesis is that rigid labor market institutions produce higher trend unemployment (because hiring/firing costs raise equilibrium unemployment) and slower cyclical recovery (because adjustment is constrained by regulation). Calculate:

$$u_t = u_t^{\text{trend}} + u_t^{\text{cycle}}$$

For the U.S., the trend unemployment should fluctuate around 4–5% with cyclical fluctuations of ±1.5 percentage points. For Spain, trend unemployment should be substantially higher (6–7% during normal times) and cyclical fluctuations larger and more persistent (±2.5 percentage points or more).

Now quantify the cost of unemployment persistence. A standard Okun's Law relationship estimates that each percentage point of unemployment above trend reduces real GDP by approximately 2% (though this varies by institutional context). If Spain maintains unemployment 4 percentage points higher than the U.S. due to rigid institutions, and this persists over a decade, the cumulative GDP loss is substantial. Estimate:

$$\text{GDP Loss} = \sum_{t=1}^{120} (u_t^{\text{Spain}} - u_t^{\text{US}}) \times 2 \% \times \text{Nominal GDP}_t$$

where the sum covers 120 months (10 years), and the 2% coefficient is Okun's Law elasticity. For an economy the size of Spain (€1.4 trillion nominal GDP), cumulative losses from institutional unemployment persistence over a decade can exceed €100–150 billion.

**Verification Checkpoint:** Your labor market institution analysis should produce: (1) merged time-series unemployment datasets for all three economies; (2) autocorrelation estimates and Hodrick-Prescott trend-cycle decompositions; (3) a comparative table showing mean trend unemployment, cyclical volatility, and adjustment speed across economies; and (4) a quantified GDP loss estimate attributable to labor market rigidity. If your analysis demonstrates that rigid labor market institutions (Spain, Germany) produce unemployment that is both higher in trend and slower to adjust cyclically compared to flexible markets (U.S.), labor market institution consequences are operationally verified.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Exercise 3A: Policy Crisis Propagation Under Institutional Constraints — The European Sovereign Debt Crisis as Case Study

Political economy theory predicts that when an economy faces external shocks (commodity price collapses, sudden capital outflows, financial crises), the institutional structure determines whether the shock is absorbed smoothly or amplifies into systemic failure. Your operational task is to reconstruct the 2010–2015 European sovereign debt crisis empirically and identify the institutional failure points that transformed a Greek fiscal problem into a systemic Eurozone existential crisis.

**Operational Scenario:** You will model how Greece's institutional constraint (membership in the Eurozone without fiscal transfer mechanisms or independent monetary policy) converted a fiscal sustainability problem into a banking collapse and currency near-crisis. The counterfactual analysis asks: what would have happened to Greece if it retained the drachma and could pursue independent monetary policy?

Begin by retrieving quarterly data for Greece and Germany covering Q1 2008 through Q4 2015 from Eurostat and OECD databases. For each economy, retrieve: (1) general government debt as percentage of GDP; (2) government budget deficit as percentage of GDP; (3) 10-year government bond yields; (4) real GDP growth rate; (5) unemployment rate; (6) current account balance as percentage of GDP; and (7) foreign exchange reserves (for Greece, substitute Eurozone TARGET2 imbalances, which measure net intra-Eurozone claims).

| Quarter | Greece Debt (% GDP) | Germany Debt (% GDP) | Greece Bond Yield (%) | Germany Bond Yield (%) | Greece GDP Growth (%) | Germany GDP Growth (%) | Greece Unemployment (%) |
|---------|---------------------|----------------------|----------------------|------------------------|----------------------|----------------------|------------------------|
| Q1 2008 | 112.5 | 64.1 | 4.26 | 3.76 | 2.1 | 1.4 | 7.3 |
| Q1 2009 | 124.5 | 73.2 | 3.45 | 2.48 | −3.1 | −5.3 | 8.9 |
| Q1 2010 | 142.6 | 81.0 | 12.45 | 3.14 | −4.9 | −5.1 | 11.7 |
| Q1 2011 | 170.3 | 82.4 | 15.75 | 2.61 | −6.9 | 3.1 | 15.1 |
| Q1 2015 | 317.0 | 71.2 | 9.25 | 0.26 | −0.3 | 1.7 | 27.5 |

The institutional constraint is that Greece, as a Eurozone member, cannot independently adjust its exchange rate or print euro currency to finance government spending. This creates a constraint equation. Greece's government budget must satisfy:

$$G_t - T_t = \text{Primary Deficit}_t$$

where $G_t$ is government spending and $T_t$ is tax revenue. If tax revenue cannot expand (because the economy is contracting) and spending cannot adjust (because of political constraints), debt accumulates. Additionally, if investors lose confidence in Greece's ability to repay (rational given deteriorating fundamentals), bond yields spike, raising borrowing costs and accelerating debt accumulation. A Markov switching model can capture this dynamic:

$$y_t^{\text{Greece}} = \begin{cases} 3.2 + 0.85 \times y_{t-1} + \epsilon_t & \text{if confidence state = high} \\ 12.0 + 1.05 \times y_{t-1} + \epsilon_t & \text{if confidence state = low} \end{cases}$$

where $y_t^{\text{Greece}}$ is the Greek 10-year government bond yield. The interpretation is that in high-confidence states, yields revert toward fundamental rates; in low-confidence states, yields amplify forward due to panic (coefficient > 1), creating a self-fulfilling crisis.

Now construct a counterfactual scenario: assume Greece retained the drachma and could pursue independent monetary policy. Under this assumption, when the crisis began, Greece's central bank could have: (1) expanded base money (quantitative easing) to prevent banking system collapse; (2) allowed drachma depreciation to restore competitiveness without wage adjustment; and (3) financed government spending directly (via central bank credit) rather than relying on capital markets. Estimate the mechanics using a simple open-economy DSGE framework.

Model Greek GDP under two regimes:

**Actual (Eurozone):** Greece's real GDP contracted by approximately 25% cumulatively from 2010 to 2015 (a contraction not matched by any other post-WWII advanced economy outside active war). This contraction was driven by fiscal austerity (government spending cuts), banking collapse (credit supply collapse after capital controls), and lack of depreciation (the euro remained stable despite Greek competitiveness crisis).

**Counterfactual (Independent drachma):** Had Greece retained monetary policy independence, GDP contraction would likely have been approximately 10–12% (corresponding to the contraction in 2010–2012 alone, followed by stabilization and recovery). The intuition: monetary accommodation prevents banking collapse, depreciation restores competitiveness, and government spending can be maintained at sustainable levels.

Calculate the welfare loss from the institutional constraint. The difference between the actual outcome (25% cumulative GDP contraction) and the counterfactual outcome (10% contraction) is approximately 15 percentage points of foregone GDP. For an economy the size of Greece (€250 billion nominal GDP at 2010 levels), the cumulative welfare loss from 2010–2015 is approximately €60–80 billion in present-value terms.

Additionally, calculate the employment cost. Greece's unemployment rose from 7.3% in Q1 2008 to 27.5% in Q1 2015—a rise of 20.2 percentage points. This corresponds to approximately 900,000 additional unemployed persons (out of a labor force of approximately 4.5 million). Estimate the present-value income loss to these workers, accounting for depressed future earnings (long-term unemployment scarring effects reduce future wage-earning capacity by approximately 10–15% permanently). The welfare loss from unemployment persistence alone exceeds €50 billion in present-value terms.

**Verification Checkpoint:** Your crisis propagation analysis should produce: (1) merged time-series data for Greece and Germany through the crisis period; (2) estimated Markov switching bond yield models demonstrating regime-switching between confidence and panic states; (3) a counterfactual quantification of outcomes under policy independence; and (4) a welfare loss estimate from institutional constraints. If your analysis demonstrates that the Eurozone institutional structure (no independent monetary policy, no fiscal transfers, no exchange rate adjustment) converted a manageable fiscal problem into a catastrophic depression, institutional fragility is operationally verified.

---

### Exercise 3B: Recovery Protocol & Institutional Reform — Modeling Policy Options Under Binding Constraints

Having identified institutional failure modes in Exercise 3A, your operational task is to construct and simulate alternative policy reforms and quantify their expected outcomes. This exercise operationalizes the question: given an economy trapped in institutional constraints, which reforms produce the largest welfare gains?

**Operational Scenario:** Returning to the European context of 2012 (at the nadir of the sovereign debt crisis), you will model three alternative policy responses and estimate their macroeconomic and institutional outcomes:

**Option A (Pursued):** Fiscal austerity + structural reform within Eurozone constraints (the Troika program). This involved government spending cuts, labor market deregulation, privatization, and reliance on ECB liquidity provision.

**Option B (Counterfactual):** Eurozone fiscal transfer union. Establish permanent fiscal redistribution mechanisms from surplus countries (Germany, Netherlands) to deficit countries (Greece, Spain, Portugal), similar to U.S. fiscal federalism, reducing debt burden on periphery countries.

**Option C (Counterfactual):** Monetary accommodation + nominal debt relief. ECB conducts large-scale asset purchases (directly purchasing government debt), and negotiates debt relief (haircuts on Greek debt owed to creditors), allowing Greece to stabilize while maintaining moderate fiscal adjustment.

For each option, construct a five-year forward projection (2012–2017) using a calibrated macroeconomic accounting framework. The basic structure is:

$$\text{Real GDP Growth}_t = \text{Baseline Growth} + \text{Fiscal Multiplier} \times \Delta G_t + \text{Monetary Transmission} \times \Delta i_t + \text{External Demand Shock}$$

where $\Delta G_t$ is the change in government spending and $\Delta i_t$ is the change in policy interest rates.

**Option A (Austerity):** Government spending cuts of approximately €10 billion annually (roughly 5% of government budget) from 2012–2015. Using a fiscal multiplier estimate of 1.2 (appropriate for economies in recession with constrained monetary policy), the real GDP impact is:

$$\Delta \text{GDP}_t = -1.2 \times 5\% = -6\%$$

annually. Combined with external demand weakness and credit supply collapse (banking sector balance sheet repair), projected real GDP growth is approximately −3% to −2% annually through 2015. This matches the actual observed outcome: Greece's real GDP contracted by approximately 3.5% annually from 2012–2014. However, debt ratios worsen because GDP contraction outpaces deficit reduction: $$\text{Debt Ratio}_{t} = \frac{\text{Debt}_{t-1}}{(1 + g_t) \times (1 + \pi_t)} + \text{Primary Deficit}_t$$

where $g_t$ is real GDP growth and $\pi_t$ is inflation. With negative real growth and inflation near zero, the denominator shrinks, causing debt ratios to explode. Greece's debt-to-GDP ratio rose from 170% in 2011 to 317% by 2015 despite fiscal adjustment.

**Option B (Fiscal Union):** Establish a Eurozone transfer mechanism distributing €15 billion annually to peripheral countries, financed by progressive taxation in core countries. This transfer reduces Greek government financing needs, allowing less harsh fiscal adjustment. New government spending path: €5 billion annual cuts (instead of €10 billion), producing $$\Delta \text{GDP}_t = -1.2 \times 2.5\% = -3\%$$ annually. Combined with transfer-induced demand boost from redistribution, projected real GDP growth is approximately −1.5% to −0.5% annually. By 2017, Greece's debt-to-GDP ratio would stabilize around 220–240% (instead of reaching 320%) and recovery would commence. The trade-off is political: German and Dutch taxpayers would face permanent transfer costs of approximately €3–4 billion annually.

**Option C (Monetary Accommodation + Debt Relief):** ECB purchases €50 billion in Greek government debt over 2012–2015 (direct monetary financing, akin to quantitative easing), and creditors accept a 50% haircut on €200 billion in Greek debt owed to official lenders (IMF, EU). This reduces Greece's debt stock from €380 billion to approximately €290 billion immediately. The debt relief reduces future debt service obligations by approximately €15 billion annually. New government spending path: €2 billion annual cuts (mild adjustment), producing $$\Delta \text{GDP}_t = -1.2 \times 1\% = -1.2\%$$ annually initially, but with monetary accommodation preventing banking collapse and depressed asset prices recovering (equity prices, property values), private sector demand rebounds faster. Projected real GDP growth by 2014–2015 is approximately +0.5% to +1.5%. Additionally, ECB purchases directly inject liquidity into Greek financial system, preventing banking collapse. By 2017, debt-to-GDP ratios would stabilize around 180–200% (with debt stock physically reduced through haircuts, and growth resuming). The trade-off is to creditors and Northern European publics: Northern banks and governments absorb losses.

Now simulate these alternatives in a spreadsheet. Create three separate projection modules, each containing the accounting identities:

$$\text{Debt}_{t+1} = \frac{\text{Debt}_t}{1 + g_t} + \text{Primary Deficit}_t$$

$$\text{Primary Deficit}_t = G_t - T_t$$

$$T_t = \tau \times Y_t$$

where $\tau$ is the tax rate (assumed constant or with policy adjustment), and $Y_t$ is nominal GDP (the product of real GDP growth and inflation). Build macroeconomic feedback loops: lower growth reduces tax revenue ($T_t$ declines), worsening the primary deficit unless $G_t$ is cut further; accumulating debt requires rising debt service payments (interest rate payments increase as debt levels rise), creating a secondary deficit burden.

For each option, produce a table:

| Year | Option A GDP Growth (%) | Option A Debt/GDP (%) | Option B GDP Growth (%) | Option B Debt/GDP (%) | Option C GDP Growth (%) | Option C Debt/GDP (%) |
|------|-------------------------|------------------------|-------------------------|------------------------|------------------------|-----------------------|
| 2012 | −6.6 | 166 | −3.2 | 160 | −2.1 | 145 |
| 2013 | −3.8 | 199 | −1.9 | 168 | +0.8 | 160 |
| 2014 | −2.7 | 252 | −0.5 | 172 | +1.4 | 168 |
| 2015 | −2.1 | 289 | +1.2 | 170 | +2.1 | 172 |
| 2016 | +0.1 | 307 | +2.8 | 162 | +2.7 | 168 |
| 2017 | +0.7 | 316 | +3.2 | 151 | +3.1 | 160 |

The operational insight is stark: Option A (pursued) results in debt-to-GDP ratios remaining unsustainably high (>300%) even through 2017, requiring continued austerity and making eventual debt default likely. Option B produces steady improvement in debt ratios while restoring growth faster. Option C produces the fastest growth recovery and lowest eventual debt ratios, but only by imposing costs on creditors and generating political conflict.

Calculate a welfare metric for each option. Use a simple discounted utility framework where social welfare is the present value of per-capita consumption:

$$W = \sum_{t=2012}^{2020} \beta^t \times c_t$$

where $\beta = 0.96$ is the annual discount factor (standard in macroeconomic models), $c_t$ is real per-capita consumption in year $t$, and real consumption is proportional to real GDP (adjusted for distribution changes, which are negligible for this comparison). Calculate the cumulative real GDP loss relative to a no-crisis baseline for each option. Option A produces approximately €120 billion in cumulative lost output (relative to pre-crisis trend) over 2012–2017. Option B produces approximately €60 billion. Option C produces approximately €30 billion. Converting these to per-capita welfare losses (dividing by Greek population of approximately 10.7 million), Option A imposes approximately €11,200 per capita in permanent income loss, while Option C imposes approximately €2,800 per capita.

**Verification Checkpoint:** Your institutional reform analysis should produce: (1) three separate forward-projection scenarios with detailed accounting tables; (2) calculated welfare (discounted output) losses for each option; (3) distributional analysis showing who bears costs under each option (Greek citizens, German taxpayers, international creditors); and (4) a policy recommendation synthesizing trade-offs. If your analysis demonstrates that institutional reforms (fiscal union or monetary accommodation) substantially reduce welfare losses compared to the pursued austerity path, the welfare gains from institutional reform are operationally verified, and you have constructed a quantitative basis for policy advocacy or institutional design discussion.

---

## Operational Reference Guide & Diagnostic Checklist

### Section I: Data Source Verification & Access Authentication

Before executing any political economy analysis, verify that you can successfully authenticate and retrieve data from required sources. This diagnostic checklist ensures your analytical infrastructure is operational.

**U.S. Federal Data Sources:** The Federal Reserve's FRED database (https://fred.stlouisfed.org) requires no authentication for basic API access but requests registration for high-frequency queries. Create a free FRED API key by registering at the website. Test access by retrieving a single series: use the query endpoint to pull the federal funds rate (series ID DFF) for Q1 2008. If the query returns a JSON object with data values, FRED access is verified. The U.S. Census Bureau (https://data.census.gov), Bureau of Labor Statistics (https://www.bls.gov), and SEC EDGAR (https://www.sec.gov/cgi-bin) all provide free public data access; no authentication is required, though large batch downloads may be throttled.

**European Data Sources:** Eurostat (https://ec.europa.eu/eurostat) provides EU member state macroeconomic data; access is free but requires registering for bulk downloads. The ECB Statistical Data Warehouse (https://www.ecb.europa.eu/web/ecb/home) provides Eurozone monetary and financial data; access requires no authentication for web interface but API access requires registration. National statistical agencies (Destatis for Germany, INE for Spain, ELSTAT for Greece) provide country-specific data; access is free through their respective websites.

**International Data Sources:** The OECD Statistics database (https://stats.oecd.org) provides cross-country comparable data on labor markets, fiscal policy, trade, and institutions; access requires registration but is free. The World Bank Open Data (https://data.worldbank.org) provides development indicators, fiscal data, and institutional indices; access requires no authentication. The IMF Primary Balance Sheet (available through IMF Data Tools) provides central bank and government fiscal data; access is free via API.

**Institutional Data:** The Worldwide Governance Indicators (WGI), maintained by the World Bank, quantify rule of law, regulatory quality, and government effectiveness across countries; data is freely available. The Polity5 dataset (https://www.systemicpeace.org/polityproject.html) codes regime type and political institutions for 167 countries; access is free. Labor market rigidity indices come from OECD Employment Protection Legislation (EPL) scores and are freely available via OECD.Stat.

### Section II: Analytical Model Library

**Model 1: Institutional Rent Calculation (Exercise 1A)**

Purpose: Quantify income flows generated by institutional protection (patents, regulatory barriers, monopoly rents).

Formula: $$R = \sum_{t=1}^{T} \frac{\pi_t}{(1 + r)^t}$$

where $\pi_t = $ economic profit in year $t$ (typically revenue × gross margin − competitive normal profit), $r = $ discount rate (typically 0.05), $T = $ duration of institutional protection.

Implementation: Construct a spreadsheet with columns for {asset/firm, institutional protection, market size, market share under protection, competitive price level, institutional price level, gross margin, discounted rents, welfare loss}. The welfare loss column estimates consumer surplus transferred to the protected entity.

**Model 2: Policy Outcome Divergence Test (Exercise 1B)**

Purpose: Test whether implemented policies produce outcomes matching stated objectives (detecting regulatory capture).

Formula: $$\text{Divergence} = \left| \frac{\text{Predicted Outcome} - \text{Actual Outcome}}{\text{Predicted Outcome}} \right| \times 100\%$$

Implementation: For each policy decision, extract the stated objective from regulatory documents. Translate the objective into a predicted quantitative outcome using economic theory (e.g., "promote competition" predicts declining prices and rising entry). Retrieve actual outcome data from administrative sources. Calculate divergence percentage. If divergence >50%, capture/corruption is indicated. If divergence <10%, policy is working as intended.

**Model 3: Inflation Persistence & Central Bank Independence (Exercise 2A)**

Purpose: Measure whether monetary policy transmission and inflation stabilization depend on institutional central bank independence.

Formula: $$\pi_t = \alpha + \beta_1 \pi_{t-1} + \beta_2 y_t + \beta_3 i_t + \beta_4 \text{CB Ind}_t + \epsilon_t$$

where $\pi_t = $ inflation rate, $y_t = $ output gap, $i_t = $ lagged policy rate, CB Ind$_t = $ central bank independence index (0–1).

Implementation: Retrieve monthly inflation, output gap, policy rates, and CB independence indices for test economies. Stack data into a time-series cross-sectional (panel) format. Estimate via OLS with panel-corrected standard errors or use random-effects estimation. The coefficient on CB Ind should be negative (independence reduces inflation). If coefficient is not significant or positive, independence has limited institutional force.

**Model 4: Labor Market Rigidity & Unemployment Dynamics (Exercise 2B)**

Purpose: Quantify the relationship between labor market institutions (hiring/firing costs) and unemployment persistence.

Formula: $$u_t = \rho u_{t-1} + (1-\rho) u^* + \gamma \times \text{EPL Index} + \epsilon_t$$

where $u_t = $ unemployment rate, $u^* = $ natural rate of unemployment, EPL = employment protection legislation rigidity index, $\rho = $ persistence parameter.

Implementation: Retrieve quarterly unemployment rates and EPL indices for OECD countries. Estimate $\rho$ (autocorrelation) separately for high-rigidity and low-rigidity subsamples. High-rigidity economies should exhibit $\rho > 0.95$; low-rigidity economies should exhibit $\rho < 0.90$. Calculate average lag length for unemployment shocks to dissipate: lag length = $-1 / \ln(\rho)$ quarters. Higher EPL correlates with longer lag lengths.

**Model 5: Sovereign Debt Dynamics Under Institutional Constraints (Exercise 3A)**

Purpose: Model debt accumulation and crisis dynamics when central bank support and fiscal transfers are institutionally constrained.

Formula: $$\text{Debt}_{t+1} = \frac{\text{Debt}_t}{(1+g_t)(1+\pi_t)} + \text{Primary Deficit}_t$$

$$i_t^{\text{bond}} = r_f + \text{Risk Premium}_t$$

$$\text{Risk Premium}_t = \begin{cases} 200 \text{ bps} & \text{if } \text{Debt}_{t-1}/\text{GDP}_{t-1} < 90\% \\ 500 + 50 \times (\text{Debt}/\text{GDP} - 90) \text{ bps} & \text{if } \text{Debt}_{t-1}/\text{GDP}_{t-1} \geq 90\% \end{cases}$$

where $g_t = $ real GDP growth (endogenous to primary deficit changes via fiscal multiplier), $\pi_t = $ inflation rate, $r_f = $ risk-free rate (typically German bund rate).

Implementation: Construct a spreadsheet with rows for each quarter and columns for {real GDP, inflation, primary deficit, debt stock, debt-to-GDP ratio, bond yield, debt service payments}. Use the accounting identities above and embed fiscal multiplier effects (primary deficit cuts reduce GDP growth). Iterate year-by-year to simulate debt dynamics. This model will reproduce the Greek debt spiral of 2010–2015 if calibrated with accurate austerity multipliers.

**Model 6: Macroeconomic Projection Under Alternative Institutional Regimes (Exercise 3B)**

Purpose: Project forward macroeconomic outcomes under counterfactual institutional arrangements (monetary independence, fiscal transfers, debt relief).

Formula: $$Y_t = Y_0 \times (1 + g)^t + \sum_{s=1}^{t} \text{Policy Shock}_s \times \text{Multiplier}_s$$

where $Y_0 = $ baseline real GDP, $g = $ long-run growth rate, policy shocks include fiscal adjustment, monetary accommodation, debt relief, each with specific multipliers.

Implementation: Construct three separate projection models (one for each institutional scenario). For each scenario, specify {government spending path, central bank policy rate, debt relief amounts, external demand assumptions}. Use fiscal multiplier (1.0–1.5 depending on whether economy is in recession and whether monetary policy is constrained) to translate spending changes into GDP effects. Use Okun's Law (each percentage point of unemployment above trend reduces GDP by 2%) to translate unemployment changes into output losses. Simulate five-year forward paths and calculate cumulative present-value welfare losses for each scenario.

### Section III: Diagnostic Troubleshooting & Quality Assurance

**Data Quality Flags:** Before proceeding with analysis, validate all data series for obvious errors. Check for: (1) missing values (NaNs or blanks); (2) outlier values (any observation >3 standard deviations from mean) indicating data entry errors or methodological breaks; (3) structural breaks in data (series level shifts) indicating changes in measurement methodology; (4) currency and units consistency (ensure inflation rates are percent changes, not basis points; ensure GDP figures are in same currency).

**Model Specification Validation:** After estimating any regression model, examine residuals for violations of OLS assumptions. Calculate the Durbin-Watson statistic to test for serial correlation in residuals (acceptable range: 1.5–2.5). Conduct Jarque-Bera test for normality of residuals (if test p-value <0.05, residuals are non-normal, suggesting potential specification error). Perform White test for heteroskedasticity (if p-value <0.05, standard errors require correction). If diagnostics indicate specification problems, consider log-transformation of variables, lagged dependent variables, or instrumental variables estimation.

**Counterfactual Reasonableness Check:** After constructing counterfactual scenarios, verify that projected outcomes are plausible relative to historical precedents. For example, if your counterfactual projects Greek GDP growth of +5% annually under monetary independence, but no advanced economy has achieved sustained 5% growth in the post-1980 era under similar conditions, the projection is unrealistic. Compare your counterfactual output growth rates against historical growth rates for similar economies in similar periods (e.g., compare Greek counterfactual against historical growth in Hungary, Czech Republic, Poland during their transition periods).

**Institutional Parameter Sensitivity:** Many political economy models depend on calibrated parameters (fiscal multipliers, monetary policy transmission elasticities, unemployment persistence). After building your model, conduct sensitivity analysis: vary each parameter by ±10% and recalculate outcomes. If results are robust (conclusions unchanged), your model is stable. If small parameter changes flip your conclusions, your analysis is fragile and requires greater scrutiny of parameter estimates.

### Section IV: Publication & Communication Standards

Political economy analysis, particularly when addressing contested institutional reforms, requires explicit documentation of assumptions and sources to maintain credibility. When presenting your findings, adhere to the following standards:

**Transparency on Data Sources:** For every data series used, document the source institution, series identifier, retrieval date, and any transformations applied (e.g., seasonal adjustment, log-transformation, deflation to real terms). If you use non-public or proprietary data, clearly label it and justify why public alternatives were insufficient.

**Explicit Modeling Assumptions:** Document all behavioral assumptions embedded in your models. If you assume fiscal multipliers of 1.2, cite the empirical literature supporting this (e.g., "IMF Staff calculations suggest multipliers of 1.2–1.5 for advanced economies in recession; we use 1.2 as conservative estimate"). If you calibrate parameter values, explain the calibration procedure (e.g., "we set the time preference discount rate to match average real interest rates observed in the period").

**Counterfactual Identification:** When presenting counterfactual outcomes, clearly state the institutional differences between the actual and counterfactual scenarios. For example: "Under the counterfactual scenario where Greece retained the drachma and independent monetary policy, we assume: (1) the Greek central bank could have conducted quantitative easing similar to the ECB starting in 2012; (2) the drachma would have depreciated 30–40% against the euro by 2013, restoring competitiveness; (3) government spending would have declined 2–3% annually instead of 5% annually due to monetary accommodation preventing fiscal crisis." Distinguish between modeling assumptions and empirical outcomes.

**Uncertainty Quantification:** For all projections and estimates, provide confidence intervals or ranges rather than point estimates. For example: "We project Greek GDP contraction of −3% to −1% annually under Option B, with 95% confidence interval reflecting uncertainty in fiscal multipliers and external demand assumptions."

**Conflict of Interest Disclosure:** If your analysis has implications for specific stakeholders (e.g., your analysis of labor market rigidity could benefit workers if it supports pro-union policy, or benefit firms if it supports deregulation), disclose the potential bias and explain how you have attempted to mitigate it (e.g., by using independent data sources, soliciting critiques from opposing viewpoints, or submitting to peer review).

This operational reference guide, combined with the three exercise modules above, provides a complete toolkit for political economy analysis. The exercises are designed to be reproducible: another analyst following these procedures with the same data sources should obtain similar quantitative results. The institutional interpretations, while grounded in theory and evidence, require professional judgment and are appropriate subjects for scholarly debate. The goal is not to provide definitive answers to contested political economy questions, but rather to operationalize the analysis so that competing claims can be empirically tested and their assumptions transparently laid bare.
```
