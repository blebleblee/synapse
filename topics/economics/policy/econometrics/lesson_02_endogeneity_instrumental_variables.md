# Lesson 2: Endogeneity, Instrumental Variables, Two-Stage Least Squares

## 1. First-Principles Intuition & Invariants

Every causal inference problem in policy econometrics eventually confronts the same uncomfortable truth: the variables we most want to study are almost never assigned at random. A government analyst estimating the employment effect of a minimum wage increase cannot run a controlled experiment on regional labor markets. A central bank researcher modeling how interest rate changes affect inflation faces a policy rule that itself responds to inflation. A development economist studying how education affects wages must contend with the fact that people who choose more schooling differ from those who do not in ways that also independently determine their earnings. In each case, the explanatory variable of interest is *endogenous* — correlated with the regression error term — and ordinary least squares (OLS) estimation, however clean and convenient, will produce biased and inconsistent estimates that no amount of additional data can rescue.

Understanding endogeneity at the level of its causes, rather than merely its symptoms, is prerequisite to solving it. Three structural mechanisms generate endogeneity in policy research, and each demands its own analytical vocabulary.

The first mechanism is **omitted variable bias**. Suppose a policy analyst estimates the effect of public health expenditure per capita on infant mortality rates across a cross-section of countries. The OLS regression assumes that all determinants of infant mortality not captured by health expenditure are uncorrelated with health expenditure itself. That assumption fails immediately: countries with stronger institutions, higher GDP per capita, and better-educated populations simultaneously spend more on health *and* have lower infant mortality for independent reasons. Institutional quality and national income are omitted from the regression, and because they correlate with the regressor of interest, their influence bleeds into its estimated coefficient. The resulting bias carries the sign of the correlation between the omitted variable and both the included regressor and the outcome. If richer countries spend more on health ($\text{Cov}(x, z) > 0$) and income independently reduces mortality ($\gamma < 0$), the OLS coefficient on health expenditure is biased toward larger negative magnitudes than the true causal effect warrants.

The second mechanism is **simultaneity** or **reverse causation**. This arises whenever the causal arrow runs in both directions between the regressor and the outcome, making it impossible to identify a supply-side from a demand-side effect using a single equation. The canonical example in policy economics is the wage-employment relationship in labor markets, but the problem is pervasive across fiscal and monetary policy work. When a central bank's policy rate ($i_t$) responds to inflation ($\pi_t$) through a Taylor-type reaction function, any regression of inflation on the policy rate recovers a mixture of the monetary policy transmission effect and the feedback rule that generated the rate setting in the first place. The two equations are determined jointly; treating one as the dependent variable and the other as an independent regressor violates the exogeneity requirement upon which OLS consistency rests.

The third mechanism is **measurement error** in the regressor. If a researcher proxies household permanent income with current annual income — a standard necessity in survey data — classical measurement error attenuates the OLS coefficient toward zero, because random noise in the regressor creates artificial variation that is by construction uncorrelated with the true signal. Attenuation bias is insidious in policy work because it makes interventions appear weaker than they are, potentially leading analysts to underestimate the importance of programs they should be scaling.

Formally, consider the structural model

$$y_i = \beta_0 + \beta_1 x_i + \varepsilon_i$$

where $y_i$ is the policy outcome of interest, $x_i$ is the endogenous regressor, and $\varepsilon_i$ is the structural error. The OLS estimator is

$$\hat{\beta}_1^{OLS} = \beta_1 + \frac{\text{Cov}(x_i, \varepsilon_i)}{\text{Var}(x_i)}$$

The asymptotic bias term $\text{Cov}(x_i, \varepsilon_i) / \text{Var}(x_i)$ is nonzero under any of the three mechanisms above. OLS is not merely imprecise in this setting — it is inconsistent. As the sample grows without bound, it converges to the wrong number.

### The Logic of Identification Through Instruments

The solution instrumental variables (IV) offers is deceptively elegant: find a variable $z_i$ that moves $x_i$ through a channel entirely separate from $\varepsilon_i$. If such a variable exists and its exclusion from the structural equation is defensible, it allows the analyst to isolate the exogenous component of $x_i$'s variation and use only that component to identify $\beta_1$. The instrument $z_i$ must satisfy two conditions that together constitute the identification requirements of IV estimation.

The **relevance condition** requires that the instrument be correlated with the endogenous regressor:

$$\text{Cov}(z_i, x_i) \neq 0$$

This is an empirical claim that can be tested directly. In the first stage of two-stage least squares (2SLS), the analyst regresses $x_i$ on $z_i$ (and all included exogenous controls) and examines whether the instrument enters with a statistically and economically meaningful coefficient. The strength of this first-stage relationship determines how much identifying variation the instrument delivers; weak instruments, as we will examine in detail, corrupt the second-stage inference even when the exclusion restriction holds.

The **exclusion restriction** requires that the instrument affect the outcome *only through* the endogenous regressor:

$$\text{Cov}(z_i, \varepsilon_i) = 0$$

This condition is fundamentally untestable from the data alone when the model is exactly identified. It is an argument about economic mechanisms — a claim that must be defended by institutional knowledge, economic theory, and plausible narrative about why the instrument has no direct pathway to the outcome other than through $x_i$. This is where policy econometrics becomes genuinely difficult, and where the quality of causal inference separates journeyman analysts from rigorous ones.

The classic illustration used in public economics is Card's (1994) study of the return to education, which instruments years of schooling with proximity to a college. The identifying argument is that living near a college in childhood lowers the cost of obtaining higher education, thereby increasing years of schooling among individuals who would otherwise have faced prohibitive commuting or housing costs. Geographic proximity is plausibly uncorrelated with individual ability or family motivation (the exclusion restriction), yet robustly predicts whether a person completes more schooling (the relevance condition). The IV estimate of the wage return to education — substantially larger than OLS — is consistent with downward attenuation bias or ability-bias working in opposite directions in the OLS specification.

In monetary policy research, one of the most important instrument designs is the high-frequency identification approach pioneered by Kuttner (2001) and refined by Nakamura and Steinsson (2018). The strategy uses the change in federal funds futures prices in a narrow window around scheduled FOCD announcements as the instrument for monetary policy surprises. Because financial markets clear within minutes and the futures price change over a 30-minute window isolates the informational content of the announcement itself, the instrument captures the exogenous component of central bank policy decisions. The exclusion restriction holds if the futures price changes in that tight window reflect only the monetary policy surprise rather than new macroeconomic information simultaneously released by the central bank — an assumption that remains debated but is far more credible than any regression run on monthly or quarterly policy rate data.

### The Local Average Treatment Effect

A subtlety that applied policy researchers often underweight is that IV does not, in general, estimate the same parameter as OLS or as a randomized controlled trial would estimate. When treatment effects are heterogeneous across the population — as they almost always are in policy contexts — the IV estimator with a binary instrument recovers the **Local Average Treatment Effect (LATE)**, defined as the average treatment effect for the subpopulation of *compliers*: individuals whose treatment status is changed by the instrument.

$$\text{LATE} = E[y_i(1) - y_i(0) \mid D_i(1) > D_i(0)]$$

where $D_i(z)$ denotes the potential treatment status under instrument value $z$. In Card's college proximity example, the LATE is the return to education for individuals who attended college because they happened to grow up near one — predominantly lower-income, credit-constrained students who were on the margin of attendance. This is not the same as the average return across all workers, nor the return for always-takers (those who would attend college regardless of proximity). Whether the LATE is the policy-relevant parameter depends on who the government is trying to target. For a policy expanding access to affordable regional colleges, it is precisely the right parameter. For a policy debate about the average social return to education broadly, it may generalize poorly. This distinction is not pedantic — misidentifying which treatment effect IV recovers has led to genuine disagreement in the minimum wage, immigration, and education literature about whether different studies are contradicting each other or simply estimating different objects.

---

## 2. Core Architecture & Mechanics

### Two-Stage Least Squares: The Estimation Pipeline

Two-stage least squares is the workhorse IV estimator for policy applications, and understanding its mechanical anatomy prevents the class of errors — standard error miscalculation, overfitting in the first stage, and misspecified exclusion restrictions — that plague applied work.

Consider the structural equation with one endogenous regressor and one instrument, generalized to include a vector of exogenous controls:

$$y_i = \beta_1 x_i + \mathbf{W}_i'\boldsymbol{\gamma} + \varepsilon_i \tag{1}$$

where $x_i$ is endogenous, $\mathbf{W}_i$ is a vector of included exogenous variables (controls), and $\varepsilon_i$ is the structural error. The first stage regression is

$$x_i = \pi_1 z_i + \mathbf{W}_i'\boldsymbol{\delta} + \nu_i \tag{2}$$

The first stage produces fitted values $\hat{x}_i = \hat{\pi}_1 z_i + \mathbf{W}_i'\hat{\boldsymbol{\delta}}$, which represent the component of $x_i$ that is explained by the instrument and the included exogenous controls. Because $z_i$ is uncorrelated with $\varepsilon_i$ by the exclusion restriction, and because $\mathbf{W}_i$ is exogenous by assumption, $\hat{x}_i$ is purged of the endogenous contamination. The second stage then regresses the outcome on these purified fitted values:

$$y_i = \beta_1 \hat{x}_i + \mathbf{W}_i'\boldsymbol{\gamma} + \eta_i \tag{3}$$

The 2SLS estimate of $\beta_1$ is consistent under the two IV conditions. Notice that the controls $\mathbf{W}_i$ must appear in *both* stages — a common error in manual implementation is to omit them from the first stage, which leaves residual variation in $x_i$ attributable to $\mathbf{W}_i$ incorrectly pooled with the instrument's variation, producing inconsistent estimates.

The anatomy of the 2SLS estimator can be written in closed form as

$$\hat{\beta}_1^{2SLS} = \frac{\text{Cov}(z_i, y_i)}{\text{Cov}(z_i, x_i)}$$

in the simple case with no additional controls. This ratio of reduced-form to first-stage coefficients is the **Wald estimator**, and reading it this way clarifies the information flow: the numerator captures how the instrument moves the outcome (the reduced form), and the denominator captures how the instrument moves the regressor (the first stage). The ratio scales the reduced-form effect by the first-stage "compliance rate," converting the intent-to-treat reduced form into a per-unit causal effect. When the instrument is binary and the regressor is binary, this collapses exactly to the LATE formula discussed above.

The execution pipeline in a modern policy research workflow looks as follows:

```
DATA PREPARATION
      │
      ▼
┌─────────────────────────────────────────────┐
│  Merge outcome (y), endogenous regressor    │
│  (x), instrument(s) (z), and controls (W)  │
│  Inspect joint coverage; handle missing data│
│  Test instrument relevance: Cov(z, x)       │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│  FIRST STAGE: Regress x on z, W             │
│  ─────────────────────────────              │
│  OLS: x = π₁z + Wδ + ν                     │
│  Test F-statistic on excluded instruments   │
│  Rule of thumb: F > 10 (Stock–Yogo)         │
│  Obtain fitted values: x̂ = π̂₁z + Wδ̂       │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│  SECOND STAGE: Regress y on x̂, W           │
│  ─────────────────────────────              │
│  2SLS: y = β₁x̂ + Wγ + η                   │
│  Use IV-corrected standard errors           │
│  (not OLS SEs from manual second stage)     │
│  Cluster or heteroskedasticity-robust SEs   │
└─────────────────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────┐
│  DIAGNOSTICS                                │
│  ─────────                                  │
│  Hausman/Wu test: Endogeneity confirmed?    │
│  Sargan-Hansen J-test: Overidentification   │
│  Anderson-Rubin: Weak-instrument-robust CI  │
└─────────────────────────────────────────────┘
```

### Implementation in Stata and R

Policy researchers in government agencies, multilateral institutions (IMF, World Bank, OECD), and central banks overwhelmingly run IV specifications in Stata, with R (via the `ivreg` and `fixest` packages) increasingly common in academic and think-tank settings. Both ecosystems offer first-class 2SLS implementations that produce properly corrected standard errors — a critical point because manually running two OLS regressions and reading the second-stage standard errors produces underestimates of coefficient uncertainty, since the generated regressors $\hat{x}_i$ carry first-stage estimation error that propagates into the second stage.

In Stata, the canonical command is `ivregress 2sls`, which handles both homoskedastic and robust inference and integrates cleanly with the `estat firststage` and `estat overid` post-estimation diagnostics:

```stata
* Structural equation: y = β₁·x + γ₁·w1 + γ₂·w2 + ε
* Instrument: z1 (excluded); w1, w2 exogenous controls

ivregress 2sls y w1 w2 (x = z1), robust

* First-stage diagnostics
estat firststage

* Hausman endogeneity test (compare OLS to 2SLS)
quietly regress y x w1 w2
estimates store ols
quietly ivregress 2sls y w1 w2 (x = z1), robust
estimates store iv
hausman iv ols, sigmamore

* Overidentification test (requires ≥ 2 instruments)
ivregress 2sls y w1 w2 (x = z1 z2), robust
estat overid
```

In R, the `fixest` package provides the most performant 2SLS implementation with support for high-dimensional fixed effects — essential for panel policy datasets covering municipalities, firms, or country-year observations:

```r
library(fixest)

# Structural equation with panel fixed effects:
# y_it = β₁·x_it + γ·w_it + α_i + δ_t + ε_it
# Instrument: z_it

fit_iv <- feols(y ~ w1 + w2 | id + year | x ~ z1,
                data = panel_data,
                cluster = ~id)

summary(fit_iv)
fitstat(fit_iv, type = "ivf")   # First-stage F-statistics
```

The `fixest` syntax deserves attention because its three-part formula structure makes the identification architecture explicit: the first segment defines exogenous covariates, the second segment defines fixed effects, and the third segment after the second `|` defines the endogenous variable and its instruments. This design forces the researcher to state the identification assumptions clearly rather than burying them in option flags.

### Reading the First-Stage Output

The first-stage regression is not a nuisance step — it is an independent evidentiary claim about the instrument's relevance. A properly reported first-stage table should include the coefficient on each excluded instrument, the first-stage $F$-statistic for joint significance of the excluded instruments, and the partial $R^2$ attributable to the instruments after partialing out the included controls. Policy researchers should report all three. The $F$-statistic carries the most diagnostic weight, but the partial $R^2$ conveys the practical magnitude of the first-stage relationship, and the coefficient signs and magnitudes provide a sanity check against the theoretical mechanism.

For a specification with one endogenous regressor and one instrument, the relevant $F$-statistic is simply the squared $t$-statistic on the instrument. The Stock-Yogo (2005) weak instrument critical values provide the formal standard: for a maximum relative bias of 10% (meaning the 2SLS bias is at most 10% of the OLS bias), the first-stage $F$-statistic must exceed 10. For a maximum bias of 5%, the threshold rises to roughly 16. These critical values depend on the number of instruments, and the original tables in Stock and Yogo (2005) should be consulted when multiple instruments are excluded. The rule-of-thumb threshold of $F > 10$ remains a useful screening heuristic but is not a substitute for the formal critical values.

---

## 3. High-Performance Optimization & Failure Modes

### The Weak Instrument Problem: Mechanics and Consequences

Weak instruments are among the most consequential and underappreciated failure modes in applied policy econometrics. When the first-stage $F$-statistic falls below the Stock-Yogo thresholds, 2SLS estimation suffers from two distinct pathologies that work in opposite directions and compound each other.

First, the 2SLS estimator develops severe finite-sample bias toward the OLS estimator. The intuition is straightforward: when the instrument explains very little of the variation in $x_i$, the first-stage fitted values $\hat{x}_i$ are dominated by variation attributable to $\mathbf{W}_i$ and sampling noise rather than to $z_i$. The "purified" regressor is barely distinguishable from the original endogenous regressor, so the second stage recovers something close to the OLS estimate. In the limit as $\pi_1 \to 0$, 2SLS collapses to OLS. This finite-sample bias toward OLS is not innocuous: OLS was inconsistent to begin with, and an estimator that converges toward it cannot be treated as a credible alternative.

Second, weak instruments produce severely distorted inference. The asymptotic normal approximation that justifies standard $t$-tests and confidence intervals fails when instruments are weak. The actual sampling distribution of the 2SLS estimator under weak instruments is non-normal, often bimodal, and has fat tails that conventional standard errors dramatically understate. A confidence interval computed as $\hat{\beta} \pm 1.96 \cdot SE$ may have true coverage far below 95%, meaning researchers routinely find statistically significant effects that are artifacts of weak identification rather than genuine signal. The 2008 Angrist-Pischke review documented that many published IV results in top economics journals had first-stage $F$-statistics below 10, raising serious concerns about the reliability of the published confidence intervals.

The correct response to weak instruments is not to report the 2SLS point estimate with an apologetic footnote. The Anderson-Rubin (AR) test and Anderson-Rubin confidence sets provide inference that is **robust to weak instruments** because they invert a test that remains valid regardless of first-stage strength. The AR test evaluates the null hypothesis $H_0: \beta_1 = \beta_0$ by testing whether the instrument $z_i$ has a reduced-form effect on the residualized outcome $(y_i - \beta_0 x_i)$. This test statistic has a known $\chi^2$ distribution under the null regardless of instrument strength, and inverting it over a grid of $\beta_0$ values produces a confidence set that maintains correct coverage even when the first stage is weak. In Stata, `weakivtest` (Pflueger-Wang) and `condivreg` provide these robust confidence intervals; in R, the `ivmodel` package implements AR confidence sets.

A parallel diagnostic, **Montiel Olea-Pflueger effective F-statistic**, improves on Stock-Yogo by accounting for heteroskedasticity and clustering in the first stage. The Stock-Yogo critical values assume homoskedastic errors; in panel policy datasets with clustered errors — the standard empirical setting — the effective $F$-statistic diverges from the conventional $F$, often downward, meaning researchers relying on the conventional $F > 10$ screen may be overconfident about instrument strength. The `weakivtest` command in Stata implements the effective $F$-statistic and reports the appropriate critical values.

### Overidentification and the Sargan-Hansen J-Test

When a researcher has more instruments than endogenous regressors — the overidentified case — the extra instruments provide an opportunity for a testable, if limited, check on the exclusion restriction. If all instruments are valid, they should all point toward the same structural parameter $\beta_1$. If different instruments imply different parameter estimates, at least one of them is violating the exclusion restriction (or the model is misspecified). The Sargan-Hansen $J$-test formalizes this intuition.

The test statistic is computed as $n$ times the $R^2$ from a regression of the 2SLS residuals $\hat{\varepsilon}_i^{IV}$ on all instruments and included exogenous controls. Under the null hypothesis that all exclusion restrictions hold, this statistic is distributed $\chi^2(q-k)$, where $q$ is the number of excluded instruments and $k$ is the number of endogenous regressors. A significant $J$-statistic rejects the joint null that all instruments satisfy the exclusion restriction.

The overidentification test has a critical limitation that every policy analyst must internalize: **it tests consistency among instruments, not validity of any individual instrument**. If all excluded instruments are endogenous in the same direction — for example, if two geographic instruments both correlate with regional economic fundamentals that independently affect the outcome — the $J$-test will fail to reject even though the exclusion restriction is violated for all of them. The test has power against instrument invalidity only when the instruments' exclusion restriction violations differ in direction or magnitude. Passing the $J$-test is necessary but not sufficient for instrument validity. It should be reported as one diagnostic among several, not as a certification of identification.

In practice, the overidentification test is most useful as a specification check when the researcher has strong theoretical reasons to believe one instrument is valid and is evaluating whether a second instrument is consistent with the first. If the $J$-test rejects when both instruments are included but accepts when each is used alone, the researcher has evidence that the two instruments are identifying different objects — possibly because they affect different populations of compliers, or because one genuinely violates the exclusion restriction.

### Instrument Validity in Policy Research: Common Failure Patterns

The hardest failures in IV policy research are not computational — they are failures of the economic argument underlying the exclusion restriction. Several recurring patterns deserve attention.

**Geographic instruments and sorting.** Instruments based on physical geography (distance to treatment centers, elevation, rainfall, historical borders) are widely used in development economics and public finance. Their Achilles heel is residential sorting: if households or firms sort into locations partly based on characteristics that also affect the outcome, then geographic variation is not exogenous to the error term. Distance to a college affects wages partly by changing educational attainment (the intended channel) but also potentially by sorting higher-ability families into areas with better labor markets near universities. The exclusion restriction survives only if the analyst can plausibly argue that conditional on the included controls, the residual geographic variation is unrelated to unobserved determinants of the outcome.

**Lagged variables as instruments.** A common fallback when better instruments are unavailable is to instrument for a contemporaneous endogenous variable with its own lagged value. This strategy fails whenever the error term is serially correlated, which is the norm rather than the exception in macroeconomic and panel policy datasets. If $\text{Cov}(\varepsilon_t, \varepsilon_{t-1}) \neq 0$ — as it would be under any persistent omitted variable — then $x_{t-1}$ is correlated with $\varepsilon_t$ through the serial correlation in the error, violating the exclusion restriction. Lagged instruments are admissible only under strong assumptions about error structure that must be explicitly tested.

**Bartik/shift-share instruments.** The Bartik instrument, which constructs a local labor demand shock by interacting national industry employment growth rates with local industry employment shares, has become ubiquitous in regional labor economics and place-based policy evaluation. Goldsmith-Pinkham, Sorkin, and Swift (2020) showed that the identifying variation in a Bartik instrument comes primarily from the initial industry shares, not the national growth rates, and that validity therefore requires the initial shares to be exogenous to local labor market trends — an assumption that fails if cities with high shares in a given industry were already on different pre-trend paths before the period under study. The implication for policy research is that Bartik instruments require pre-trend testing and sensitivity analysis across the weighting of shares, not simply a first-stage $F$-statistic.

### Scaling to Panel Data: Fixed Effects and IV

Policy research with administrative microdata or multi-country panel data introduces an important interaction between fixed effects and IV. The within-group transformation that eliminates fixed effects (the Mundell-Fleming demeaning procedure in panel models) must be applied to both the endogenous regressor and the instrument. If the analyst demeans the outcome and regressor but uses a level-form instrument, the first stage is misspecified. In `fixest`, the fixed effects are absorbed jointly from all variables including instruments through the alternating projections algorithm, ensuring the demeaning is applied consistently. In Stata's `ivregress`, adding `absorb()` via `xtivreg2` (Baum, Schaffer, Stillman) handles within-group transformation correctly with clustered standard errors.

The choice of clustering level matters substantially for inference. In a dataset covering 500 municipalities over 20 years, standard errors clustered at the municipality level account for serial correlation within municipalities but treat cross-sectional observations as independent. If the instrument varies at a higher level of aggregation — say, at the state or region level — clustering at the municipality level understates standard errors, because observations within the same state share the same instrument value and are therefore not independent conditional on the instrument. The correct clustering level is typically the coarser of the instrument's unit of variation and the regressor's unit of variation. Moulton (1990) established the analytical basis for this aggregation problem, and in modern practice researchers routinely cluster at the instrument's level of variation to avoid false precision.

### Assessing Instrument Quality: A Practical Checklist for Policy Analysts

Rather than treating instrument validation as a post-hoc ritual of running diagnostic tests, the most effective policy researchers build the identification argument prospectively, before estimation, by systematically interrogating the economic mechanism. The identifying question is always a specific causal pathway claim: through precisely what mechanism does the instrument affect the endogenous regressor, and through what mechanism could it *not* affect the outcome other than through that regressor? Documenting this mechanism story in the paper — not just in the researcher's private notes — subjects the exclusion restriction to the scrutiny of readers who may know the institutional context better than the author.

The empirical battery that operationalizes this prospective reasoning involves four assessments. First, the reduced form: a regression of the outcome directly on the instrument, without the endogenous regressor, should produce a coefficient with the sign and approximate magnitude predicted by the structural pathway. If the instrument affects the outcome in the reduced form but the sign is inconsistent with the proposed mechanism, the exclusion restriction is likely violated. Second, pre-trend tests in panel settings: if the instrument is plausibly exogenous, treated and control units should have parallel trends in the outcome before the instrument's variation activates. Third, placebo tests using outcomes that the structural mechanism predicts should be unaffected: if a rainfall instrument for agricultural income is valid, it should not predict industrial wages in the same region through any direct channel other than the agricultural income pathway. Fourth, sensitivity analysis over instrument construction, particularly for shift-share designs where the choice of base year shares and the level of industry aggregation can be varied to assess how much the results depend on arbitrary specification choices.

The goal of this battery is not to construct a statistical argument that the instrument is valid — no finite battery of tests can prove the exclusion restriction. The goal is to make the exclusion restriction assumption as transparent and falsifiable as possible, so that the reader can evaluate whether the causal interpretation of the 2SLS coefficient is warranted given the institutional context of the policy question.

Endogeneity is not a statistical nuisance to be corrected with the right command. It is a signal that the data-generating process is more structurally complex than a simple regression model represents, and instrumental variables is the tool that forces researchers to make explicit what causal pathway they are trying to isolate. Done well, IV estimation produces the most credible causal estimates available outside of randomization. Done carelessly — with weak instruments, implausible exclusion restrictions, or mismeasured standard errors — it produces numbers that look rigorous but are less reliable than the OLS estimates they replaced.
