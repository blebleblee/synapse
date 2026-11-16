# Lesson 4: Limited Dependent Variables, Panel Data Estimation

## 1. First-Principles Intuition & Invariants

Policy analysis lives and dies by its ability to answer questions that ordinary linear regression cannot honestly address. When a government economist asks whether a household will fall into poverty after a benefits reform, whether a firm will exit a market following a regulatory change, or whether a worker will participate in a retraining program, the outcome variable is not a continuous quantity measured on an unbounded scale. It is a binary indicator, a zero or a one, and treating it as if it were otherwise produces predictions that are economically nonsensical and statistically invalid. This is the essential problem that limited dependent variable models were built to solve, and understanding why the standard linear probability model fails is the right place to begin.

Consider the linear probability model (LPM), where $\Pr(y_i = 1 \mid \mathbf{x}_i) = \mathbf{x}_i'\boldsymbol{\beta}$. The appeal is simplicity: the coefficient $\beta_k$ is interpretable as the marginal effect of $x_k$ on the probability of the outcome. But the model is structurally incoherent. For extreme values of $\mathbf{x}_i'\boldsymbol{\beta}$, fitted probabilities can easily fall below zero or exceed one, which is a logical impossibility. The error term is heteroskedastic by construction, since $\text{Var}(y_i \mid \mathbf{x}_i) = \mathbf{x}_i'\boldsymbol{\beta}(1 - \mathbf{x}_i'\boldsymbol{\beta})$, which violates the homoskedasticity assumption required for OLS efficiency. More fundamentally, the relationship between a continuous linear index and a binary outcome is never truly linear across the full support of the covariates. Near the boundaries of the probability space, the response to any change in $x_k$ must be bounded and diminishing, a feature that the LPM cannot accommodate but that the probit and logit models handle elegantly through their link functions.

Both models are built on the same latent variable foundation. We posit an unobserved continuous index $y_i^*$ that captures the underlying propensity of an agent to take some action:

$$y_i^* = \mathbf{x}_i'\boldsymbol{\beta} + \varepsilon_i$$

The observed binary outcome is then a threshold-crossing rule: $y_i = 1$ if $y_i^* > 0$ and $y_i = 0$ otherwise. What distinguishes probit from logit is the assumed distribution of $\varepsilon_i$. If $\varepsilon_i \sim \mathcal{N}(0, 1)$, the threshold-crossing probability is governed by the standard normal cumulative distribution function, giving the probit model:

$$\Pr(y_i = 1 \mid \mathbf{x}_i) = \Phi(\mathbf{x}_i'\boldsymbol{\beta})$$

If instead $\varepsilon_i$ follows the standard logistic distribution, with CDF $\Lambda(z) = \frac{e^z}{1 + e^z}$, the resulting model is the logit:

$$\Pr(y_i = 1 \mid \mathbf{x}_i) = \frac{e^{\mathbf{x}_i'\boldsymbol{\beta}}}{1 + e^{\mathbf{x}_i'\boldsymbol{\beta}}}$$

Both link functions are strictly bounded between zero and one, monotonically increasing in the linear index, and symmetric around 0.5. In practice, the two models produce nearly identical marginal effects for probabilities in the middle range of $[0.1, 0.9]$. The logistic distribution has slightly heavier tails, meaning the logit assigns more probability mass to extreme outcomes than the probit. For most policy applications, the choice between them is secondary to the quality of the specification and the data. What matters far more is that the analyst understands what these models actually estimate and what they do not.

This brings us to the most consequential interpretive point in limited dependent variable analysis: **the coefficients $\boldsymbol{\beta}$ are not marginal effects**. In a linear model, $\beta_k$ tells you directly how much $y$ changes when $x_k$ increases by one unit. In a nonlinear model, the effect of $x_k$ on the probability of $y_i = 1$ depends on the entire covariate vector of observation $i$, because the derivative of the CDF is not constant. The marginal effect of $x_k$ at a point $\mathbf{x}$ is:

$$\frac{\partial \Pr(y_i = 1 \mid \mathbf{x})}{\partial x_k} = \phi(\mathbf{x}'\boldsymbol{\beta}) \cdot \beta_k$$

where $\phi(\cdot)$ is the standard normal PDF for probit or $\Lambda(\cdot)(1 - \Lambda(\cdot))$ for logit. Because $\phi(\cdot)$ achieves its maximum at the center of the distribution and declines toward the tails, the same unit change in $x_k$ has a larger impact on the probability when the agent is near the margin of indifference than when they are deeply committed to one outcome. This is not a statistical artifact but an economically meaningful property: at the threshold between complying with a regulation or not, a small change in the cost of compliance carries much greater weight than it does for a firm that is already strongly incentivized to comply.

Practitioners report either marginal effects evaluated at the sample mean (MEM) or the more defensible average marginal effect (AME). The AME averages the derivative across all observations in the sample:

$$\widehat{\text{AME}}_k = \frac{1}{n}\sum_{i=1}^{n} \phi(\mathbf{x}_i'\hat{\boldsymbol{\beta}}) \cdot \hat{\beta}_k$$

The AME is preferred in policy work because it integrates over the actual distribution of covariates rather than relying on a hypothetical representative agent whose characteristics are the sample mean. When a covariate is binary, the marginal effect is replaced by the finite difference in predicted probabilities between the two states.

### Maximum Likelihood Estimation: The Mechanism

Neither probit nor logit can be estimated by OLS, because the outcome is discrete. The natural estimation framework is maximum likelihood, which asks: given the observed data, what values of $\boldsymbol{\beta}$ make the observed sample of zeros and ones most probable? For a sample of $n$ independent observations, the log-likelihood function is:

$$\ell(\boldsymbol{\beta}) = \sum_{i=1}^{n} \left[ y_i \ln F(\mathbf{x}_i'\boldsymbol{\beta}) + (1 - y_i) \ln \left(1 - F(\mathbf{x}_i'\boldsymbol{\beta})\right) \right]$$

where $F(\cdot)$ is $\Phi(\cdot)$ for probit or $\Lambda(\cdot)$ for logit. This function is globally concave in $\boldsymbol{\beta}$ for both specifications, which guarantees that iterative numerical maximization—typically Newton-Raphson or Fisher scoring—converges to a unique global maximum. The score (gradient) equations are:

$$\frac{\partial \ell}{\partial \boldsymbol{\beta}} = \sum_{i=1}^{n} \frac{y_i - F(\mathbf{x}_i'\boldsymbol{\beta})}{F(\mathbf{x}_i'\boldsymbol{\beta})(1 - F(\mathbf{x}_i'\boldsymbol{\beta}))} f(\mathbf{x}_i'\boldsymbol{\beta}) \mathbf{x}_i = \mathbf{0}$$

where $f(\cdot) = F'(\cdot)$ is the PDF. At the MLE $\hat{\boldsymbol{\beta}}$, standard errors are obtained from the negative inverse of the Hessian of the log-likelihood, the information matrix, which under standard regularity conditions gives $\sqrt{n}(\hat{\boldsymbol{\beta}} - \boldsymbol{\beta}_0) \xrightarrow{d} \mathcal{N}(\mathbf{0}, \mathcal{I}(\boldsymbol{\beta}_0)^{-1})$ where $\mathcal{I}$ is the Fisher information matrix. In practice, the analyst must always pair MLE standard errors with an assessment of the model's asymptotic properties, and in clustered survey designs, clustered standard errors are essential.

A failure mode specific to binary models that every policy analyst must know is **complete separation**. If some linear combination of the covariates perfectly predicts the outcome (every observation with $x_k > c$ has $y_i = 1$ and every observation with $x_k \leq c$ has $y_i = 0$), the likelihood has no finite maximum and $\hat{\beta}_k \to \infty$. The iterative algorithm will simply keep increasing the coefficient without converging. This is not a numerical error; it is a signal that the model is overspecified relative to the data or that the binary outcome is effectively deterministic conditional on a covariate. Firth's penalized likelihood estimator, which applies a Jeffreys prior penalty to the log-likelihood, is the standard corrective in policy datasets where rare outcomes or small samples make separation likely.

### Panel Data: The Architecture of Repeated Observations

A single cross-section of observations, however large, cannot answer the most important questions in policy evaluation without strong and often untestable assumptions about selection. When a government implements a welfare reform, the individuals affected by the reform differ systematically from those who are not, in ways that are observable to the analyst only partially and to the policymaker not at all. Panel data, which tracks the same units—households, firms, municipalities, countries—across multiple time periods, provides the variation needed to separate the treatment effect from pre-existing, time-invariant differences between units. This is the essential logic that makes panel methods central to any serious policy impact evaluation.

Consider the canonical two-way panel data generating process. For unit $i$ observed at time $t$, we write:

$$y_{it} = \mathbf{x}_{it}'\boldsymbol{\beta} + \alpha_i + \lambda_t + \varepsilon_{it}$$

where $\alpha_i$ is a unit-specific fixed effect capturing all time-invariant unobserved heterogeneity (a household's innate ability, a firm's culture, a municipality's geography), $\lambda_t$ is a time fixed effect capturing aggregate shocks common to all units (a business cycle shock, a national policy change), and $\varepsilon_{it}$ is an idiosyncratic error. The central question of panel data econometrics is how to treat $\alpha_i$. The answer determines everything: whether the estimator is consistent, what identifying variation it uses, and what policy questions it can and cannot answer.

The **fixed effects (FE) estimator** treats $\alpha_i$ as a parameter to be absorbed by demeaning the data within each unit. The within transformation subtracts unit-specific time means from each variable:

$$\tilde{y}_{it} = y_{it} - \bar{y}_i, \quad \tilde{\mathbf{x}}_{it} = \mathbf{x}_{it} - \bar{\mathbf{x}}_i$$

and estimates $\boldsymbol{\beta}$ by OLS on the demeaned data: $\hat{\boldsymbol{\beta}}_{FE} = \left(\sum_i \sum_t \tilde{\mathbf{x}}_{it}\tilde{\mathbf{x}}_{it}'\right)^{-1}\sum_i \sum_t \tilde{\mathbf{x}}_{it}\tilde{y}_{it}$. By eliminating $\alpha_i$ entirely through demeaning, the FE estimator is consistent whether or not $\alpha_i$ is correlated with $\mathbf{x}_{it}$. This is its decisive advantage in policy settings: an analyst evaluating the effect of a minimum wage increase on employment does not need to assume that pre-existing differences across states in labor market conditions are unrelated to the timing of wage increases. The within transformation sweeps away those differences entirely. The cost of this insurance is that all time-invariant covariates—race, gender, baseline infrastructure level—are also swept out and cannot be estimated.

The **random effects (RE) estimator** takes the opposite stance, treating $\alpha_i$ as a random draw from a distribution with mean zero and variance $\sigma_\alpha^2$, unrelated to $\mathbf{x}_{it}$. Under this assumption, the composite error $v_{it} = \alpha_i + \varepsilon_{it}$ has a specific variance-covariance structure where observations on the same unit are correlated. Generalized Least Squares exploits this structure, applying a partial demeaning with factor $\theta = 1 - \sqrt{\frac{\sigma_\varepsilon^2}{\sigma_\varepsilon^2 + T\sigma_\alpha^2}}$:

$$\check{y}_{it} = y_{it} - \theta\bar{y}_i$$

The RE estimator is more efficient than FE when the orthogonality assumption holds, because it uses both within-unit and between-unit variation. But if $\alpha_i$ is correlated with $\mathbf{x}_{it}$—the typical situation in observational policy data—RE is inconsistent. The choice between FE and RE is therefore not primarily about efficiency: it is about whether the analyst is willing to assume away the most common source of bias in non-experimental data.

The **Hausman test** formalizes this choice. It compares the FE and RE coefficient vectors under the null hypothesis that RE is consistent (i.e., the orthogonality condition holds). The test statistic is:

$$H = (\hat{\boldsymbol{\beta}}_{FE} - \hat{\boldsymbol{\beta}}_{RE})' \left[\widehat{\text{Var}}(\hat{\boldsymbol{\beta}}_{FE}) - \widehat{\text{Var}}(\hat{\boldsymbol{\beta}}_{RE})\right]^{-1} (\hat{\boldsymbol{\beta}}_{FE} - \hat{\boldsymbol{\beta}}_{RE}) \xrightarrow{d} \chi^2_k$$

A significant Hausman statistic is evidence that the RE assumption is violated and the FE estimator should be preferred. In practice, the test should not be treated as an unconditional oracle: it has well-known size distortions in short panels, and a modern analyst often supplements it with theoretical reasoning about whether selection into treatment is plausibly correlated with unit-level unobservables.

### Difference-in-Differences: Causal Identification Through Comparative Dynamics

Difference-in-differences (DiD) is perhaps the most widely used quasi-experimental method in applied policy evaluation, and for good reason. It offers a clean, transparent identification strategy that is relatively easy to explain to policymakers, connects naturally to the panel data framework, and can be implemented with modest data requirements. Its logic rests on a single, non-testable but often plausible assumption: that in the absence of treatment, the treated and control groups would have followed parallel trends over time.

The canonical two-period, two-group setup has a treatment group ($D_i = 1$) exposed to a policy change between period $t=0$ and $t=1$, and a control group ($D_i = 0$) that is not. The DiD estimator is:

$$\hat{\tau}_{DiD} = \left(\bar{y}_{1,\text{treat}} - \bar{y}_{0,\text{treat}}\right) - \left(\bar{y}_{1,\text{control}} - \bar{y}_{0,\text{control}}\right)$$

This double-differencing removes two sources of bias simultaneously. The first difference within each group removes group-specific time trends. The second difference across groups removes time-invariant differences between groups. The regression implementation is:

$$y_{it} = \alpha + \gamma D_i + \lambda \mathbf{1}[t=1] + \tau (D_i \times \mathbf{1}[t=1]) + \varepsilon_{it}$$

where $\hat{\tau}$ is the DiD coefficient of interest. The parallel trends assumption requires that in the counterfactual world where no policy was implemented, the average outcome in the treatment group would have evolved at the same rate as in the control group. This is fundamentally untestable for the post-treatment period, but analysts build credibility by testing for pre-trends: if the treatment and control groups were on parallel trajectories in the periods before treatment, there is stronger reason to believe the assumption holds.

The generalization to staggered adoption DiD, where different units adopt a policy at different times, dominated applied work for two decades through the two-way fixed effects (TWFE) estimator. Recent work by Callaway and Sant'Anna (2021), Goodman-Bacon (2021), and de Chaisemartin and D'Haultfœuille (2020) has exposed a serious flaw in this approach: the TWFE coefficient is a weighted average of cohort-specific treatment effects, but the weights can be negative when treatment effects are heterogeneous across cohorts or when treatment effects evolve over time. Early-adopting groups can inadvertently serve as the control for later-adopting groups, so if the early adopters' treatment effect grows post-adoption, they contaminate the control group comparison for later adopters. This "forbidden comparison" problem can cause the TWFE estimator to be severely biased, even reversing sign, relative to any economically meaningful average treatment effect.

---

## 2. Core Architecture & Mechanics

The practical workflow for implementing these methods in policy analysis follows a consistent logical architecture regardless of the specific software environment. Understanding the data flow and decision points as a structured system helps analysts avoid specification errors and correctly interpret results.

```
RAW POLICY DATA (cross-section / panel)
           │
           ▼
┌─────────────────────────────────────┐
│         DATA STRUCTURE AUDIT        │
│  - Binary outcome? → LDV route      │
│  - Repeated obs per unit? → Panel   │
│  - Treatment timing? → DiD/TWFE     │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
 LDV PATHWAY      PANEL PATHWAY
       │                │
       ▼                ▼
  Latent index     Unit/Time FE
  y* = Xβ + ε     structure check
       │                │
       ▼                ▼
  MLE via           Hausman Test
  Newton-Raphson    (FE vs. RE)
       │                │
       ▼                ▼
  AME / MEM        Within-estimator
  computation      (demeaned OLS)
       │                │
       ▼                ▼
  Separation       Parallel trends
  check (Firth)    pre-test (event
       │            study plot)
       └───────┬────────┘
               │
               ▼
     ┌──────────────────┐
     │  INFERENCE LAYER │
     │  Clustered SE    │
     │  Bootstrap       │
     │  Wild cluster    │
     └──────────────────┘
               │
               ▼
     POLICY-INTERPRETABLE
     MARGINAL EFFECTS /
     ATT ESTIMATES
```

### Implementing Binary Choice Models

Working in Stata, which remains the dominant platform for policy econometrics, the `probit` and `logit` commands handle MLE internally. The critical workflow step that separates careful policy work from mechanical output production is computing and reporting marginal effects through Stata's `margins` post-estimation command.

After estimating a probit model of program participation on a set of household characteristics, the typical command sequence is:

```stata
probit participate income age educ_years female rural, robust
margins, dydx(*) atmeans
margins, dydx(*) post
```

The first `margins` call computes marginal effects at the sample mean (MEM); the second computes average marginal effects (AME). The `dydx(*)` option requests the derivative of the predicted probability with respect to each covariate. For binary covariates such as `female` or `rural`, Stata automatically computes the finite difference in predicted probabilities rather than a derivative, which is the correct quantity. Standard errors for AMEs are computed via the delta method.

In R, the `glm()` function with `family = binomial(link = "probit")` or `family = binomial(link = "logit")` fits the model, and the `marginaleffects` package by Arel-Bidwell (2023) provides the most flexible and correct AME computation:

```r
library(marginaleffects)
fit <- glm(participate ~ income + age + educ_years + female + rural,
           data = df, family = binomial(link = "probit"))
avg_slopes(fit)
```

Model fit for binary models is assessed not through $R^2$ (which has no natural analog) but through the McFadden pseudo-$R^2$, defined as $\rho^2 = 1 - \frac{\ell(\hat{\boldsymbol{\beta}})}{\ell(\bar{y})}$, where $\ell(\bar{y})$ is the log-likelihood of an intercept-only model. Values above 0.2 generally indicate good fit in binary outcome models. The analyst should also examine the Percent Correctly Predicted, though this metric is sensitive to the threshold chosen and is dominated by the majority class in unbalanced samples. Receiving Operating Characteristic (ROC) curves and their associated area under the curve (AUC) statistic provide a threshold-independent measure of discriminatory power.

### Implementing Fixed Effects Panel Estimation

For a balanced panel in Stata, the `xtreg` command with the `fe` option implements the within estimator. The command `xtset id year` first declares the panel structure, specifying the unit identifier and time variable. Standard errors must be clustered at the unit level to account for serial correlation within units, which the `vce(cluster id)` option provides:

```stata
xtset firm_id year
xtreg log_employment log_minwage log_gdp, fe vce(cluster firm_id)
estimates store fe_model

xtreg log_employment log_minwage log_gdp, re vce(cluster firm_id)
estimates store re_model

hausman fe_model re_model, sigmamore
```

In R, the `fixest` package (Bergé, 2018) has become the standard for high-dimensional fixed effects estimation due to its computational efficiency and clean interface:

```r
library(fixest)
fe_model <- feols(log_employment ~ log_minwage + log_gdp | firm_id + year,
                  data = panel_df, cluster = ~firm_id)
summary(fe_model)
etable(fe_model, se = "cluster")
```

The `| firm_id + year` syntax absorbs both unit and time fixed effects without constructing dummy variable matrices explicitly, using the alternating projections algorithm (Gaure, 2013) for computational efficiency. For panels with thousands of firms or municipalities, this matters: explicit dummy variable regression with $n-1$ unit dummies is computationally prohibitive, while the demeaning approach scales linearly.

A critical diagnostic for panel models is **testing for serial correlation in the residuals**. After FE estimation, the Arellano-Bond test (Stata: `xtabond`) checks for first-order and second-order autocorrelation in the first-differenced residuals. If $\varepsilon_{it}$ is serially uncorrelated, first differences should exhibit AR(1) correlation (since $\Delta\varepsilon_{it}$ and $\Delta\varepsilon_{it-1}$ share the $\varepsilon_{it-1}$ term) but no AR(2) correlation. Rejection of the AR(2) test is evidence that the idiosyncratic errors themselves are serially correlated, violating the strict exogeneity assumption and introducing bias that clustered standard errors alone cannot correct.

### Implementing Difference-in-Differences with Staggered Adoption

The modern approach to staggered DiD uses the Callaway-Sant'Anna estimator, which computes cohort-time average treatment effects $ATT(g,t)$ for each group $g$ (defined by when the unit first receives treatment) at each time $t$, using only clean comparisons between the treated cohort and units that have not yet been treated by time $t$. The aggregate treatment effect on the treated is then a weighted average of these cohort-time estimates.

In R, the `did` package implements this:

```r
library(did)
cs_est <- att_gt(yname = "outcome",
                 gname = "first_treat_year",
                 idname = "unit_id",
                 tname = "year",
                 xformla = ~controls,
                 data = staggered_df,
                 control_group = "notyettreated",
                 clustervars = "unit_id")

agg_simple <- aggte(cs_est, type = "simple")
agg_dynamic <- aggte(cs_est, type = "dynamic")
ggdid(agg_dynamic)
```

The `type = "dynamic"` aggregation produces the event-study plot: a time series of the estimated treatment effect at each relative period from adoption, from several periods before ($-k, \ldots, -1$) through several periods after ($0, 1, \ldots, m$). The pre-treatment coefficients for periods $-k$ through $-2$ should be statistically indistinguishable from zero if the parallel trends assumption holds in the pre-period. Period $-1$ is the excluded reference period by convention.

The event-study architecture is worth visualizing explicitly for the staggered case:

```
RELATIVE TIME (periods since treatment adoption)
          -3    -2    -1     0    +1    +2    +3
           │     │     │     │     │     │     │
Cohort A   ◆─────◆─────◆─────◆─────◆─────◆     (treated t=2015)
Cohort B   ◆─────◆─────◆─────◆─────◆           (treated t=2017)
Cohort C   ◆─────◆─────◆─────◆                 (treated t=2019)
           │     │     │     │
           └── pre-treatment ─┴── post-treatment
           │                 │
     [Should be ≈ 0]    [ATT estimates
     [pre-trend test]    of interest]

Control group: "not yet treated" units at each calendar time t
```

This diagram captures the clean comparison logic: for Cohort B at relative time $+1$ (calendar year 2018), the control group consists of Cohort C units, which have not yet been treated. This avoids the forbidden comparison between early and late adopters that contaminates the TWFE estimator.

---

## 3. High-Performance Optimization & Failure Modes

### Failure Mode 1: Complete Separation in Binary Models

Complete or quasi-complete separation is far more common in policy evaluation data than most practitioners expect. It arises frequently when the outcome is rare, the sample is small, or a covariate nearly perfectly predicts treatment assignment. The symptom is a runaway coefficient, usually with an enormous standard error, that the iterative MLE algorithm cannot stabilize. Stata will often issue a warning about "0 cells with failures" or "0 cells with outcomes"; R's `glm()` will issue an `algorithm did not converge` warning and produce suspiciously large coefficients.

The correct response is **not** to drop the offending variable but to use Firth's penalized likelihood, implemented in R as `logistf::logistf()` and in Stata via the `firthlogit` user package. Firth's method adds a penalty term $\frac{1}{2}\ln|\mathcal{I}(\boldsymbol{\beta})|$ to the log-likelihood, which is equivalent to a Jeffreys prior and produces finite, consistent estimates in separated samples. The resulting AMEs will be smaller in magnitude than the explosive separated estimates but will reflect what the data can actually support.

### Failure Mode 2: Incidental Parameters in Nonlinear Panel Models

Combining binary outcome models with individual fixed effects creates a deep inconsistency problem. When a probit or logit model is estimated with unit-specific fixed effects on a short panel (small $T$, large $n$), each unit's $\alpha_i$ is estimated from only $T$ observations. As $n \to \infty$ with $T$ fixed, the number of incidental parameters $\alpha_i$ grows without bound, and their estimation error biases $\hat{\boldsymbol{\beta}}$ even asymptotically. For logit with $T = 2$, the fixed effects estimator overstates $|\boldsymbol{\beta}|$ by a factor of 2 in large samples. This is Neyman and Scott's (1948) incidental parameters problem, and it is a genuine failure of the model, not a finite-sample quirk.

The solution, for logit only, is the **conditional fixed effects logit** estimator (Chamberlain, 1980), which conditions on the within-unit sum $\sum_t y_{it}$ to form a likelihood that is free of the $\alpha_i$ parameters. In Stata:

```stata
xtlogit outcome treatment controls, fe vce(cluster id)
```

No analogous solution exists for probit, because the normal distribution does not have the sufficient statistic property that makes conditioning work for the logistic. For probit with fixed effects in short panels, the analyst must either use the linear probability model with unit dummies (accepting its limitations) or use bias-corrected estimators such as those developed by Hahn and Newey (2004), available through the `xtprobit` command with analytical bias correction.

### Failure Mode 3: Violation of Parallel Trends Through Anticipation Effects

A parallel trends violation that is particularly difficult to detect is **treatment anticipation**. If units that will eventually be treated begin changing their behavior before treatment is officially implemented—because they observe the policy debate, respond to announcements, or adjust to regulations before they take legal effect—the pre-treatment outcome path in the treated group diverges from the control group not because of a confound but because treatment has already begun to operate. This will appear as significant pre-trend coefficients in the event-study plot, which the analyst might incorrectly attribute to a failure of the parallel trends assumption.

The standard correction is to redefine the treatment onset to an earlier date that reflects when anticipatory behavior plausibly began, often the date of legislative passage or public announcement rather than the date of regulatory enforcement. The `att_gt()` function in the `did` package accepts an `anticipation` argument specifying how many periods of anticipation to allow, shifting the effective treatment date accordingly.

### Optimizing for Clustered Standard Errors with Few Clusters

The asymptotic justification for cluster-robust standard errors requires a large number of clusters, typically invoked as $G \geq 50$. Policy evaluation panels frequently have far fewer: a study of state-level minimum wage laws has $G = 50$ clusters at best, and a cross-country study might have $G = 20$. With few clusters, cluster-robust standard errors are biased downward, leading to over-rejection of null hypotheses.

The **wild cluster bootstrap** (Cameron, Gelbach, Miller, 2008) is the correction of choice. It resamples the entire residual vector at the cluster level, using a Rademacher distribution to draw weights $\{-1, +1\}$ each with probability $\frac{1}{2}$. For DiD with two-way clustering (by unit and by time), the intersection clustering approach adds a third cluster dimension for unit-time cells. In Stata, the `boottest` package (Roodman et al., 2019) implements the wild bootstrap efficiently:

```stata
xtreg outcome treatment post treat_post controls, fe
boottest treat_post, reps(999) cluster(state_id)
```

In R, `fwildclusterboot::boot_coef()` provides the equivalent functionality and integrates directly with `fixest` model objects.

A related precision problem in staggered DiD is that the Callaway-Sant'Anna standard errors, while theoretically valid, can be conservative in panels with limited cohort heterogeneity. The honest approach is to report both asymptotic and bootstrap confidence intervals and note where they diverge. When the number of treated cohorts is very small (fewer than five), all treatment effect estimates should be reported with strong caveats about statistical power.

### Specification Strategy: Building the Model Progressively

Sound practice in policy econometrics is to build the model specification progressively, testing at each stage whether adding controls changes the estimates in economically significant ways. For a panel DiD study, this means beginning with a raw difference in pre-post means across groups, then adding time fixed effects, then unit fixed effects, then time-varying controls, and finally testing for heterogeneous treatment effects by subgroup. Each step should be reported in a coefficient table so that readers can trace how each assumption contributes to the final estimate.

The sensitivity of the DiD estimate to the choice of control group deserves particular attention. When units self-select into treatment based on observable characteristics, adding regression controls for those characteristics to the DiD regression makes the parallel trends assumption conditional on those controls, which is often more plausible than the unconditional version. Formally, the conditional parallel trends assumption requires that $\mathbb{E}[Y_{it}(0) - Y_{it-1}(0) \mid D_i = 1, \mathbf{X}_i] = \mathbb{E}[Y_{it}(0) - Y_{it-1}(0) \mid D_i = 0, \mathbf{X}_i]$, meaning treated and control units with the same observable characteristics would have trended in parallel. The Sant'Anna-Zhao (2020) doubly-robust DiD estimator, also implemented in the `did` package, combines inverse probability weighting on the selection model with outcome regression to produce estimates that are consistent if either the propensity score model or the outcome model is correctly specified.

The payoff of mastering these methods is the ability to give policy advice that rests on defensible causal claims rather than correlational patterns. When an analyst tells a housing minister that the coefficient on a rent control variable in a panel DiD is $-0.12$ with a 95% confidence interval of $[-0.18, -0.06]$ under parallel trends, that statement has a precise and honest interpretation: in municipalities that adopted rent control, the annual rate of new housing construction fell by approximately 12 percentage points relative to comparable municipalities that did not, controlling for pre-existing trends. That is a statement with real policy weight, and every element of the machinery covered in this lesson exists in service of making it.
