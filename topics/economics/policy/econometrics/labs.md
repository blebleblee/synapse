# Operational Verification Labs: Econometrics

## Objective & Operational Lab Setup

Econometrics sits at the empirical frontier of economic science, transforming theoretical propositions into testable hypotheses through the rigorous application of statistical methods to real-world data. For the policy practitioner, econometric competence is not an academic luxury but an operational necessity. Central bank officials must estimate output gaps and inflation expectations from noisy macroeconomic indicators. Trade negotiators must quantify elasticities of substitution to forecast the welfare effects of tariff adjustments. Fiscal authorities must identify causal treatment effects of tax policy changes while disentangling correlation from causation in observational datasets riddled with confounding variables and selection bias.

This laboratory guide equips you with the operational toolkit to conduct publication-grade empirical analysis. You will estimate linear regression models, diagnose specification errors, implement instrumental variable strategies to recover causal parameters under endogeneity, construct robust standard errors in the presence of heteroskedasticity and autocorrelation, and deploy time-series methods to model dynamic macroeconomic relationships. Every exercise prioritizes hands-on execution over theoretical abstraction, yet each technique is grounded in the statistical foundations that justify its deployment in real policy contexts.

Your analytical environment centers on R, the lingua franca of applied econometric research, supplemented by Python for data wrangling pipelines and replication workflows. R's statistical computing ecosystem offers unparalleled depth: the `lmtest` and `sandwich` packages for robust inference, `AER` for instrumental variables and panel data methods, `forecast` and `vars` for time-series analysis, and `fixest` for high-dimensional fixed effects estimation. Python's `pandas` and `statsmodels` libraries provide complementary tools for data preparation and model estimation, while `linearmodels` handles panel data and instrumental variable regressions with syntax familiar to Stata users.

Begin by establishing a clean project directory structure that separates raw data, processed datasets, estimation scripts, and output artifacts. Install the required R packages by executing the following command in your R console, which will fetch dependencies from CRAN and compile any necessary binary components:

```r
install.packages(c("tidyverse", "lmtest", "sandwich", "AER", "plm", 
                   "forecast", "vars", "fixest", "modelsummary", 
                   "stargazer", "ggplot2", "tseries", "urca"))
```

For Python users, construct a virtual environment to isolate package versions and prevent dependency conflicts. Navigate to your project directory in a terminal and execute:

```bash
python3 -m venv econometrics_lab
source econometrics_lab/bin/activate  # On Windows: econometrics_lab\Scripts\activate
pip install pandas numpy scipy statsmodels linearmodels matplotlib seaborn jupyter
```

Verify your installation by launching R or Python and loading core libraries. In R, execute `library(tidyverse); library(AER)` and confirm no error messages appear. In Python, run `import pandas as pd; import statsmodels.api as sm; import linearmodels as lm` and ensure all modules import successfully.

Acquire real-world datasets that mirror the empirical challenges policy economists face daily. The Federal Reserve Economic Data (FRED) repository maintained by the St. Louis Fed provides high-frequency macroeconomic time series spanning inflation, unemployment, interest rates, and GDP components. Download quarterly real GDP, the GDP deflator, the federal funds rate, and the unemployment rate from 1960 onward using the `quantmod` R package or FRED's direct API. For microeconomic applications, obtain the Current Population Survey (CPS) extract from IPUMS-CPS, which contains individual-level wage, education, and demographic data essential for labor market analysis. Panel data exercises will draw on the Penn World Table for cross-country growth regressions and the Bureau of Labor Statistics' longitudinal establishment microdata for productivity studies.

The operational philosophy governing these laboratories is ruthless empiricism tempered by theoretical discipline. You will estimate models, inspect residual diagnostics, confront specification tests, and iterate toward robust inference. When a coefficient estimate contradicts economic intuition, you will investigate whether the anomaly stems from data quality issues, omitted variable bias, measurement error, or genuine empirical refutation of the theoretical prior. When standard errors appear suspiciously small, you will test for autocorrelation and clustering that might inflate false positives. When an instrumental variable strategy hinges on an exclusion restriction, you will interrogate whether the instrument truly satisfies the exogeneity condition or merely shifts the bias to a less transparent margin.

Each exercise follows a structured workflow: data ingestion and cleaning, exploratory graphical analysis, model specification and estimation, diagnostic testing, robust inference construction, and substantive interpretation anchored in policy implications. Code snippets are complete and executable, not pseudocode skeletons. Every parameter choice is justified by econometric theory or empirical best practice, not arbitrary convention.

## Exercise 1: Foundational Practical Implementation

The classical linear regression model forms the bedrock of applied econometric analysis, yet its proper execution demands attention to specification, identification, and inference procedures that novice practitioners often neglect. This foundational exercise constructs a wage equation using individual-level microdata, estimates the returns to education, and rigorously tests the regression assumptions underpinning valid causal inference.

Begin by loading a cross-sectional extract from the Current Population Survey for wage and salary workers aged 25 to 64. If you lack access to restricted-use CPS microdata, the `AER` package in R includes the `CPS1985` dataset, a 534-observation sample containing wages, years of education, experience, occupation, and demographic characteristics. Load the dataset and inspect its structure:

```r
library(AER)
library(tidyverse)
library(lmtest)
library(sandwich)

data("CPS1985")
glimpse(CPS1985)
summary(CPS1985)
```

The dataset contains hourly wages in 1985 dollars, years of completed education, potential labor market experience calculated as age minus years of schooling minus six, binary indicators for gender and union membership, occupation categories, and region fixed effects. Before estimating any model, conduct exploratory graphical analysis to identify outliers, nonlinearities, and unconditional correlations that inform specification choices.

Construct a scatter plot of log wages against years of education, overlaying a flexible locally weighted regression (LOESS) smoother to detect deviations from linearity:

```r
ggplot(CPS1985, aes(x = education, y = log(wage))) +
  geom_point(alpha = 0.4, color = "steelblue") +
  geom_smooth(method = "loess", se = TRUE, color = "darkred") +
  labs(title = "Log Wages vs. Years of Education",
       subtitle = "CPS 1985 Cross-Section",
       x = "Years of Education",
       y = "Log Hourly Wage (1985 USD)") +
  theme_minimal()
```

The LOESS curve reveals an approximately linear relationship, justifying a log-linear specification where the coefficient on education admits a percentage interpretation. The semi-logarithmic form also addresses right-skewness in the wage distribution and stabilizes residual variance, mitigating heteroskedasticity.

Estimate the baseline Mincer wage equation regressing log wages on education and a quadratic in potential experience, the canonical specification in labor economics:

```r
mincer_basic <- lm(log(wage) ~ education + experience + I(experience^2), 
                   data = CPS1985)
summary(mincer_basic)
```

Examine the coefficient on education, which estimates the average percentage increase in wages for each additional year of schooling under the identifying assumption that education is exogenous conditional on experience. The baseline estimate typically ranges between 7 and 12 percent in U.S. data. The experience terms capture the concave lifecycle earnings profile: wages rise with labor market tenure but at a diminishing rate, eventually flattening or declining as depreciation of human capital and health deterioration offset further accumulation.

Extend the specification to control for observable heterogeneity correlated with both education and wages, addressing omitted variable bias. Include gender, union membership, and occupation fixed effects:

```r
mincer_extended <- lm(log(wage) ~ education + experience + I(experience^2) + 
                      gender + union + occupation, 
                      data = CPS1985)
summary(mincer_extended)
```

The education coefficient typically falls by 2 to 4 percentage points once controls enter, revealing that part of the raw correlation between schooling and wages operates through sorting into better-paying occupations and union coverage. The gender coefficient quantifies the raw wage gap, though this estimate conflates discrimination, differences in unobserved productivity characteristics, occupational segregation, and labor supply choices.

Before interpreting these coefficients as causal effects, rigorously test the regression assumptions. Begin with residual diagnostics to detect heteroskedasticity, non-normality, and functional form misspecification. Extract fitted values and residuals, then construct diagnostic plots:

```r
CPS1985 <- CPS1985 %>%
  mutate(fitted = fitted(mincer_extended),
         resid = residuals(mincer_extended),
         resid_std = rstandard(mincer_extended))

# Residuals vs. fitted values (heteroskedasticity check)
ggplot(CPS1985, aes(x = fitted, y = resid)) +
  geom_point(alpha = 0.4, color = "steelblue") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "darkred") +
  geom_smooth(method = "loess", se = FALSE, color = "darkgreen") +
  labs(title = "Residuals vs. Fitted Values",
       x = "Fitted Log Wage",
       y = "Residual") +
  theme_minimal()

# Q-Q plot (normality check)
ggplot(CPS1985, aes(sample = resid_std)) +
  stat_qq(color = "steelblue") +
  stat_qq_line(color = "darkred") +
  labs(title = "Normal Q-Q Plot of Standardized Residuals") +
  theme_minimal()
```

The residuals-versus-fitted plot should exhibit a random scatter around zero with no systematic patterns. A funnel shape indicates heteroskedasticity: residual variance increases with the conditional mean. The LOESS smoother should trace a flat horizontal line; systematic curvature signals functional form misspecification or omitted nonlinearities. The Q-Q plot assesses normality: points should align tightly with the 45-degree reference line. Heavy tails or skewness imply non-normality, which invalidates conventional t-statistics and F-tests in finite samples, though asymptotic inference remains valid under weak regularity conditions.

Formalize the heteroskedasticity diagnosis with the Breusch-Pagan test, which regresses squared residuals on the regressors and tests whether the fitted values significantly predict residual variance:

```r
bptest(mincer_extended)
```

A p-value below 0.05 rejects homoskedasticity, necessitating robust standard error correction. Similarly, test functional form adequacy with Ramsey's RESET test, which augments the regression with powers of fitted values and tests their joint significance:

```r
resettest(mincer_extended, power = 2:3, type = "fitted")
```

Rejection indicates omitted nonlinearities or interaction terms that bias coefficient estimates and invalidate inference.

When heteroskedasticity is detected, compute heteroskedasticity-consistent (HC) standard errors, also known as Huber-White or Eicker-White robust standard errors. The `sandwich` package provides multiple heteroskedasticity-robust covariance estimators. HC1 applies a finite-sample degrees-of-freedom correction; HC3 adjusts for high-leverage observations:

```r
coeftest(mincer_extended, vcov = vcovHC(mincer_extended, type = "HC1"))
```

Robust standard errors typically exceed OLS standard errors in the presence of heteroskedasticity, widening confidence intervals and reducing statistical significance. Compare conventional and robust inference side-by-side using the `modelsummary` package:

```r
library(modelsummary)

models <- list(
  "OLS (Conventional SE)" = mincer_basic,
  "OLS + Controls (Conventional SE)" = mincer_extended
)

modelsummary(models, 
             vcov = list("classical", "classical"),
             stars = TRUE,
             gof_map = c("nobs", "r.squared", "adj.r.squared"))

modelsummary(models,
             vcov = list("HC1", "HC1"),
             stars = TRUE,
             gof_map = c("nobs", "r.squared", "adj.r.squared"))
```

The robust inference often reveals that marginally significant coefficients under conventional standard errors lose significance, particularly for binary indicators and interaction terms with small cell sizes.

Substantive interpretation must acknowledge the limitations of this observational analysis. The education coefficient estimates a conditional correlation, not a causal effect, because unobserved ability, family background, and discount rates jointly determine educational attainment and labor market productivity. Individuals who complete more schooling possess unobserved characteristics that raise wages independently of schooling itself, creating positive omitted variable bias. If ability is positively correlated with education and enters the error term, OLS overestimates the true causal return. Conversely, measurement error in self-reported years of schooling attenuates the coefficient toward zero. The net direction of bias remains ambiguous without exogenous variation or credible instruments.

For policy applications, document the full estimation workflow, diagnostic test results, and sensitivity checks in a reproducible R Markdown or Jupyter notebook. Export regression tables to LaTeX for academic publication using `stargazer`:

```r
library(stargazer)

stargazer(mincer_basic, mincer_extended,
          type = "latex",
          se = list(sqrt(diag(vcovHC(mincer_basic, type = "HC1"))),
                    sqrt(diag(vcovHC(mincer_extended, type = "HC1")))),
          title = "Mincer Wage Equation: OLS Estimates with Robust Standard Errors",
          dep.var.labels = "Log Hourly Wage",
          covariate.labels = c("Years of Education", "Experience", "Experience$^2$",
                               "Male", "Union Member"),
          omit = "occupation",
          add.lines = list(c("Occupation FE", "No", "Yes")),
          notes = "Heteroskedasticity-robust standard errors (HC1) in parentheses.",
          notes.align = "l")
```

This foundational exercise establishes the operational workflow for all subsequent econometric analysis: specify models grounded in economic theory, estimate parameters using appropriate estimators, rigorously test identifying assumptions, construct robust inference adjusting for detected violations, and interpret results with epistemic humility regarding causal claims from observational data.

## Exercise 2: Parameter Variation & Empirical Analysis

Instrumental variable (IV) estimation recovers causal parameters when endogenous regressors correlate with unobserved determinants of the outcome, a pervasive challenge in policy analysis where treatment assignment is non-random and selection bias confounds naive comparisons. This exercise deploys two-stage least squares (2SLS) to estimate the causal effect of education on wages using quarter of birth as an instrument, exploiting compulsory schooling laws that generate quasi-experimental variation in completed schooling independent of ability.

The identification strategy, pioneered by Joshua Angrist and Alan Krueger in their seminal 1991 Quarterly Journal of Economics paper, leverages the institutional fact that children born in different quarters of the year reach the legal school-leaving age after completing different amounts of education. Students born earlier in the year can drop out with slightly less schooling than those born later, while ability remains uncorrelated with birth timing conditional on cohort. This generates an exogenous "nudge" in educational attainment that isolates the causal effect for compliers who adjust schooling in response to the compulsory schooling rule.

Load a dataset containing quarter of birth indicators alongside wage, education, and demographic variables. The `AER` package does not include the full Angrist-Krueger dataset, so construct a simulated dataset that preserves the key identifying variation:

```r
set.seed(42)
n <- 5000

# Simulate quarter of birth (1 to 4)
qob <- sample(1:4, n, replace = TRUE)

# Unobserved ability (mean 0, sd 1)
ability <- rnorm(n, 0, 1)

# Education: function of ability, quarter of birth (QOB 1 gets less schooling)
education <- 12 + 0.5 * ability - 0.3 * (qob == 1) + rnorm(n, 0, 1.5)
education <- pmax(education, 9)  # Minimum 9 years

# Log wage: function of education AND ability (endogeneity)
log_wage <- 1.5 + 0.08 * education + 0.15 * ability + rnorm(n, 0, 0.3)

# Potential experience (age - education - 6), age uniform 25-64
age <- sample(25:64, n, replace = TRUE)
experience <- age - education - 6
experience <- pmax(experience, 0)

# Create data frame
iv_data <- tibble(
  log_wage = log_wage,
  education = education,
  experience = experience,
  qob = factor(qob),
  qob1 = as.integer(qob == 1),
  ability = ability  # Unobserved in real data
)

# Remove ability from observable data (only for verification)
iv_data_observed <- iv_data %>% select(-ability)
```

First estimate the naive OLS regression ignoring endogeneity to establish the biased baseline. Then estimate the causal effect using two-stage least squares with quarter-of-birth instruments.

```r
# Naive OLS (biased upward due to omitted ability)
ols_naive <- lm(log_wage ~ education + experience + I(experience^2), 
                data = iv_data_observed)
summary(ols_naive)

# First stage: regress education on instrument and controls
first_stage <- lm(education ~ qob1 + experience + I(experience^2), 
                  data = iv_data_observed)
summary(first_stage)

# Check first-stage F-statistic (should exceed 10 for strong instrument)
first_stage_fstat <- summary(first_stage)$fstatistic[1]
print(paste("First-stage F-statistic:", round(first_stage_fstat, 2)))
```

The first-stage regression tests instrument relevance: does quarter of birth significantly predict educational attainment conditional on experience? The F-statistic on the excluded instrument must exceed 10 to satisfy the Stock-Yogo rule-of-thumb for strong instruments. A weak instrument induces finite-sample bias in the 2SLS estimator toward the OLS estimate and invalidates asymptotic inference, producing confidence intervals with incorrect coverage rates.

Estimate the structural equation via 2SLS using the `ivreg` function from the `AER` package, which automates the two-stage procedure:

```r
# 2SLS estimation
iv_model <- ivreg(log_wage ~ education + experience + I(experience^2) | 
                  qob1 + experience + I(experience^2), 
                  data = iv_data_observed)
summary(iv_model, diagnostics = TRUE)
```

The syntax specifies the structural equation before the vertical bar and the first-stage equation after, listing all exogenous variables and excluded instruments. The `diagnostics = TRUE` option reports Sargan-Hansen overidentification test statistics when multiple instruments are available and Wu-Hausman endogeneity tests comparing OLS and 2SLS estimates.

Examine the education coefficient from 2SLS relative to OLS. In the simulated data, the true causal effect is 0.08, OLS overestimates it due to ability bias, and 2SLS recovers an unbiased estimate under the exclusion restriction that quarter of birth affects wages only through education. In real applications, the 2SLS estimate typically falls below the OLS estimate, consistent with downward attenuation bias from measurement error in education dominating upward ability bias in OLS, or with local average treatment effect (LATE) interpretation where the IV estimate captures returns for compliers induced by compulsory schooling laws who may have below-average returns.

Rigorously test instrument validity. The exclusion restriction requires that quarter of birth not correlate with unobserved wage determinants except through education. This assumption is untestable without exogenous variation in wages independent of education, but indirect evidence can support or undermine credibility. Regress log wages on quarter-of-birth dummies and controls among individuals who completed college, a group unaffected by compulsory schooling laws:

```r
# Placebo test: quarter of birth should not predict wages among college graduates
placebo_data <- iv_data_observed %>% filter(education >= 16)
placebo_reg <- lm(log_wage ~ qob + experience + I(experience^2), 
                  data = placebo_data)
summary(placebo_reg)
```

Significant coefficients on quarter-of-birth dummies in the placebo sample suggest the instrument correlates with unobserved determinants like family background or seasonal birth effects on health and cognitive development, violating the exclusion restriction.

Compute robust standard errors for 2SLS using the `sandwich` package, applying heteroskedasticity-consistent covariance estimation to the second-stage equation:

```r
coeftest(iv_model, vcov = vcovHC(iv_model, type = "HC1"))
```

Standard errors increase under robust correction, reflecting efficiency losses from heteroskedasticity that 2SLS fails to exploit optimally. For more efficient inference under conditional heteroskedasticity, implement generalized method of moments (GMM) estimation using optimal weighting:

```r
library(gmm)

# Construct moment conditions for GMM
g <- function(theta, x) {
  education <- x[, 1]
  experience <- x[, 2]
  qob1 <- x[, 3]
  log_wage <- x[, 4]
  
  # Residuals from structural equation
  resid <- log_wage - theta[1] - theta[2] * education - theta[3] * experience - 
           theta[4] * experience^2
  
  # Moment conditions: E[Z' * u] = 0
  m1 <- resid  # Intercept
  m2 <- resid * experience
  m3 <- resid * experience^2
  m4 <- resid * qob1  # Excluded instrument
  
  cbind(m1, m2, m3, m4)
}

x_matrix <- cbind(iv_data_observed$education, 
                  iv_data_observed$experience,
                  iv_data_observed$qob1,
                  iv_data_observed$log_wage)

gmm_model <- gmm(g, x = x_matrix, t0 = c(1.5, 0.08, 0.02, -0.0005))
summary(gmm_model)
```

GMM produces asymptotically efficient estimates under arbitrary heteroskedasticity by optimally weighting moment conditions with the inverse of the variance-covariance matrix of sample moments.

Compare OLS, 2SLS, and GMM estimates in a unified regression table:

```r
modelsummary(
  list("OLS" = ols_naive, "2SLS" = iv_model, "GMM" = gmm_model),
  stars = TRUE,
  gof_map = c("nobs", "r.squared")
)
```

This comparative analysis reveals the magnitude of endogeneity bias and documents sensitivity to estimator choice, transparency essential for credible policy evaluation.

Extend the analysis to panel data structures where repeated observations on individuals or firms enable difference-in-differences or fixed effects identification strategies. Construct a simulated panel dataset with individual-level unobserved heterogeneity:

```r
set.seed(123)
n_individuals <- 500
n_periods <- 8

panel_data <- expand_grid(
  id = 1:n_individuals,
  time = 1:n_periods
) %>%
  group_by(id) %>%
  mutate(
    # Time-invariant individual effect (ability, family background)
    alpha_i = rnorm(1, 0, 1.5),
    # Time-varying education (increases over time for some)
    education = 12 + 0.2 * time + rnorm(1, 0, 1),
    experience = time - 1,
    # Log wage: function of education, experience, individual effect
    log_wage = 1.5 + 0.08 * education + 0.03 * experience + alpha_i + rnorm(n(), 0, 0.3)
  ) %>%
  ungroup()
```

Estimate a pooled OLS regression ignoring panel structure, then a fixed effects model that differences out time-invariant unobserved heterogeneity:

```r
library(plm)

# Pooled OLS (biased due to individual effects)
pooled_ols <- lm(log_wage ~ education + experience, data = panel_data)

# Fixed effects estimation (within transformation)
panel_data_plm <- pdata.frame(panel_data, index = c("id", "time"))
fe_model <- plm(log_wage ~ education + experience, 
                data = panel_data_plm, 
                model = "within")

summary(pooled_ols)
summary(fe_model)
```

The fixed effects estimator eliminates bias from time-invariant confounders by comparing changes in education to changes in wages within individuals over time. The education coefficient falls closer to the true 0.08 causal effect as individual heterogeneity is swept out. However, fixed effects identification requires within-individual variation in education; purely cross-sectional variation in time-invariant schooling is absorbed by individual dummies.

Test whether fixed effects are necessary using an F-test for joint significance of individual dummies or the Hausman specification test comparing random effects and fixed effects estimators:

```r
# Random effects model
re_model <- plm(log_wage ~ education + experience, 
                data = panel_data_plm, 
                model = "random")

# Hausman test: systematic difference between FE and RE?
phtest(fe_model, re_model)
```

Rejection of the Hausman test null hypothesis indicates that individual effects correlate with regressors, necessitating fixed effects over the more efficient but inconsistent random effects estimator.

Compute cluster-robust standard errors that account for within-individual correlation across time periods, the appropriate inference adjustment for panel data:

```r
coeftest(fe_model, vcov = vcovHC(fe_model, type = "HC1", cluster = "group"))
```

Cluster-robust standard errors exceed conventional standard errors when within-cluster correlation is positive, preventing false positives from understated uncertainty.

This exercise establishes operational mastery of instrumental variable and panel data methods, the workhorse identification strategies in applied policy research. Successful execution requires not merely running canned commands but interrogating instrument validity, assessing first-stage strength, testing overidentification restrictions, and conducting sensitivity analysis to gauge robustness of causal claims.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

Time-series econometrics confronts unique challenges absent in cross-sectional analysis: serial dependence invalidates standard inference, trends and unit roots generate spurious regression, and dynamic feedback between variables demands vector autoregression rather than single-equation methods. This exercise stress-tests your operational capacity to model macroeconomic time series, diagnose nonstationarity, estimate vector autoregressions, and conduct structural impulse response analysis for monetary policy evaluation.

Download quarterly U.S. macroeconomic data from FRED spanning 1960 through 2024. Retrieve real GDP (GDPC1), the GDP deflator (GDPDEF), the federal funds rate (FEDFUNDS), and the civilian unemployment rate (UNRATE). Use the `quantmod` package to automate data retrieval:

```r
library(quantmod)
library(forecast)
library(vars)
library(tseries)
library(urca)

# Download data from FRED
getSymbols(c("GDPC1", "GDPDEF", "FEDFUNDS", "UNRATE"), src = "FRED")

# Combine into a single data frame
macro_data <- merge(GDPC1, GDPDEF, FEDFUNDS, UNRATE, all = FALSE)
macro_data <- data.frame(date = index(macro_data), coredata(macro_data))

# Convert to quarterly frequency if needed, fill FEDFUNDS (monthly) to quarterly average
macro_data <- macro_data %>%
  mutate(
    quarter = as.yearqtr(date),
    gdp = GDPC1,
    inflation = 400 * (log(GDPDEF) - log(lag(GDPDEF))),  # Annualized quarterly inflation
    ffr = FEDFUNDS,
    unemp = UNRATE
  ) %>%
  group_by(quarter) %>%
  summarise(
    gdp = mean(gdp, na.rm = TRUE),
    inflation = mean(inflation, na.rm = TRUE),
    ffr = mean(ffr, na.rm = TRUE),
    unemp = mean(unemp, na.rm = TRUE)
  ) %>%
  drop_na()

# Convert to time series objects
gdp_ts <- ts(macro_data$gdp, start = c(1960, 1), frequency = 4)
inflation_ts <- ts(macro_data$inflation, start = c(1960, 1), frequency = 4)
ffr_ts <- ts(macro_data$ffr, start = c(1960, 1), frequency = 4)
unemp_ts <- ts(macro_data$unemp, start = c(1960, 1), frequency = 4)
```

Before estimating dynamic models, test each series for stationarity using the Augmented Dickey-Fuller (ADF) test, which evaluates the null hypothesis of a unit root against the alternative of trend stationarity:

```r
# ADF test for unit root (include drift and trend)
adf_gdp <- ur.df(gdp_ts, type = "trend", lags = 4)
summary(adf_gdp)

adf_inflation <- ur.df(inflation_ts, type = "trend", lags = 4)
summary(adf_inflation)

adf_ffr <- ur.df(ffr_ts, type = "drift", lags = 4)
summary(adf_ffr)

adf_unemp <- ur.df(unemp_ts, type = "drift", lags = 4)
summary(adf_unemp)
```

The test statistic is compared against critical values tabulated for the Dickey-Fuller distribution. Failure to reject the null indicates a unit root, requiring differencing to achieve stationarity. Real GDP exhibits a strong stochastic trend, necessitating first-differencing or transformation to growth rates. Inflation and the federal funds rate are typically stationary, though structural breaks during high-inflation episodes may complicate inference. The unemployment rate appears stationary but highly persistent, with an autoregressive root near unity.

Transform GDP to quarterly growth rates and confirm stationarity of the transformed series:

```r
gdp_growth <- 400 * diff(log(gdp_ts))  # Annualized quarterly growth rate
adf_growth <- ur.df(gdp_growth, type = "drift", lags = 4)
summary(adf_growth)
```

The first-differenced series rejects the unit root null, validating the integrated order I(1) classification for real GDP and justifying growth rate specifications in subsequent models.

Estimate a reduced-form vector autoregression (VAR) to model the dynamic interdependence of GDP growth, inflation, and the federal funds rate. The VAR nests traditional structural macroeconomic models as restricted special cases and provides a flexible framework for forecasting and impulse response analysis. Begin by determining optimal lag length using information criteria:

```r
# Combine variables into multivariate time series
var_data <- cbind(gdp_growth, inflation_ts[-1], ffr_ts[-1])
colnames(var_data) <- c("gdp_growth", "inflation", "ffr")

# Select optimal lag order (AIC, BIC, HQ)
lag_selection <- VARselect(var_data, lag.max = 8, type = "const")
print(lag_selection$selection)
```

The Akaike Information Criterion (AIC) balances model fit against parameter proliferation, typically selecting longer lags than the Bayesian Information Criterion (BIC), which imposes a stronger penalty for dimensionality. Choose a lag length that satisfies both parsimony and residual diagnostic tests for serial correlation.

Estimate the VAR model with the selected lag order:

```r
# Estimate VAR(4)
var_model <- VAR(var_data, p = 4, type = "const")
summary(var_model)
```

Each equation in the VAR regresses a variable on its own lags and lags of all other variables, capturing feedback effects and Granger causality. The GDP growth equation reveals whether lagged inflation and interest rates help predict output fluctuations. The federal funds rate equation estimates the Federal Reserve's implicit policy reaction function, analogous to a Taylor rule.

Diagnose residual properties to validate the VAR specification. Residuals should be serially uncorrelated and exhibit no remaining ARCH effects:

```r
# Portmanteau test for residual autocorrelation
serial_test <- serial.test(var_model, lags.pt = 12, type = "PT.asymptotic")
print(serial_test)

# Test for ARCH effects in residuals
arch_test <- arch.test(var_model, lags.multi = 8)
print(arch_test)

# Stability check: roots of the companion matrix should lie inside unit circle
stability <- stability(var_model, type = "OLS-CUSUM")
plot(stability)
```

Residual autocorrelation indicates insufficient lags or misspecification, requiring augmentation with additional lags or exogenous variables. ARCH effects signal time-varying volatility, common in financial time series and periods of macroeconomic instability. VAR stability requires all eigenvalues of the companion matrix to lie strictly inside the unit circle; otherwise, shocks have explosive effects and impulse responses diverge.

Conduct impulse response analysis to trace the dynamic effect of a monetary policy shock on GDP growth and inflation. Orthogonalize shocks using Cholesky decomposition, ordering variables as GDP growth, inflation, then the federal funds rate, under the identifying assumption that monetary policy responds contemporaneously to output and inflation but affects them with a one-period lag:

```r
# Impulse response functions: shock to FFR
irf_ffr <- irf(var_model, impulse = "ffr", response = c("gdp_growth", "inflation"),
               n.ahead = 20, ortho = TRUE, runs = 1000, ci = 0.90)

plot(irf_ffr)
```

The impulse response function plots the dynamic trajectory of GDP growth and inflation following a one-standard-deviation surprise increase in the federal funds rate. The classic finding: a contractionary monetary shock initially raises short-term rates, reducing output growth within two to four quarters and lowering inflation with a longer lag of six to eight quarters. The delayed inflation response reflects sticky prices and forward-looking expectations embedded in wage and price-setting behavior.

Confidence intervals constructed via bootstrap resampling quantify estimation uncertainty. Narrow bands indicate precise impulse response estimates; wide bands suggest parameter uncertainty and limited information in the data, particularly for long-horizon responses where forecast errors accumulate.

Perform Granger causality tests to assess whether lagged interest rates help predict GDP growth and inflation beyond their own lags, formalizing the notion of monetary policy transmission:

```r
# Granger causality: does FFR Granger-cause GDP growth?
granger_gdp <- causality(var_model, cause = "ffr")
print(granger_gdp$Granger)

# Granger causality: does FFR Granger-cause inflation?
granger_inflation <- causality(var_model, cause = "ffr")
print(granger_inflation$Granger)
```

Rejection of the null hypothesis confirms that monetary policy shocks have predictive content for real activity and price dynamics, supporting the Federal Reserve's dual mandate framework.

Conduct out-of-sample forecast evaluation to assess the VAR's predictive accuracy for policy scenario analysis. Split the sample into estimation and holdout periods, estimate the VAR on the training data, generate multi-step-ahead forecasts, and compute mean absolute error (MAE) and root mean squared error (RMSE) relative to realized values:

```r
# Split data: training (1960-2019), holdout (2020-2024)
train_end <- which(time(var_data) == as.yearqtr("2019 Q4"))
var_train <- window(var_data, end = time(var_data)[train_end])
var_holdout <- window(var_data, start = time(var_data)[train_end + 1])

# Estimate VAR on training data
var_train_model <- VAR(var_train, p = 4, type = "const")

# Generate forecasts
forecast_horizon <- nrow(var_holdout)
var_forecast <- predict(var_train_model, n.ahead = forecast_horizon, ci = 0.90)

# Extract point forecasts
fcst_gdp <- var_forecast$fcst$gdp_growth[, "fcst"]
fcst_inflation <- var_forecast$fcst$inflation[, "fcst"]
fcst_ffr <- var_forecast$fcst$ffr[, "fcst"]

# Compute forecast errors
actual_gdp <- as.numeric(var_holdout[, "gdp_growth"])
actual_inflation <- as.numeric(var_holdout[, "inflation"])
actual_ffr <- as.numeric(var_holdout[, "ffr"])

mae_gdp <- mean(abs(fcst_gdp - actual_gdp), na.rm = TRUE)
rmse_gdp <- sqrt(mean((fcst_gdp - actual_gdp)^2, na.rm = TRUE))

mae_inflation <- mean(abs(fcst_inflation - actual_inflation), na.rm = TRUE)
rmse_inflation <- sqrt(mean((fcst_inflation - actual_inflation)^2, na.rm = TRUE))

mae_ffr <- mean(abs(fcst_ffr - actual_ffr), na.rm = TRUE)
rmse_ffr <- sqrt(mean((fcst_ffr - actual_ffr)^2, na.rm = TRUE))

print(paste("GDP Growth - MAE:", round(mae_gdp, 2), "RMSE:", round(rmse_gdp, 2)))
print(paste("Inflation - MAE:", round(mae_inflation, 2), "RMSE:", round(rmse_inflation, 2)))
print(paste("FFR - MAE:", round(mae_ffr, 2), "RMSE:", round(rmse_ffr, 2)))
```

Large forecast errors during the COVID-19 pandemic and 2022 inflation surge reveal model breakdown when structural shocks fall outside the historical distribution used for parameter estimation. This boundary failure underscores the limits of reduced-form time-series models for scenario analysis under regime shifts, necessitating structural DSGE models with microfounded policy rules and expectation formation.

Recover structural shocks by imposing long-run or sign restrictions on impulse responses, an identification strategy that avoids the arbitrary Cholesky ordering. Estimate a structural VAR (SVAR) imposing the restriction that monetary policy shocks have no long-run effect on real GDP, consistent with the classical dichotomy and neutrality of money:

```r
# Long-run restrictions: monetary policy shocks have no permanent effect on GDP
amat <- diag(3)
amat[1, 3] <- NA  # Allow contemporaneous FFR effect on GDP

bmat <- diag(3)
bmat[1, 3] <- 0  # Long-run restriction: no permanent effect on GDP

svar_model <- SVAR(var_model, Amat = amat, Bmat = bmat, max.iter = 1000)
summary(svar_model)

# Structural impulse responses
svar_irf <- irf(svar_model, impulse = "ffr", n.ahead = 20, runs = 1000, ci = 0.90)
plot(svar_irf)
```

Structural identification permits causal interpretation of impulse responses as the pure effect of exogenous policy innovations orthogonal to systematic Fed reactions to economic conditions. The structural monetary shock represents the surprise component of interest rate changes unexplained by the Taylor rule, isolating the policy experiment relevant for counterfactual welfare analysis.

This exercise completes the operational toolkit for rigorous time-series econometric analysis in policy settings. Mastery requires fluency in stationarity diagnostics, lag selection criteria, VAR estimation mechanics, structural identification schemes, impulse response computation, Granger causality testing, and out-of-sample forecast evaluation—the full empirical apparatus underpinning modern central bank forecasting models and scenario analysis.

## Operational Reference Guide & Diagnostic Checklist

This reference guide consolidates best practices, diagnostic workflows, and troubleshooting protocols for operational econometric analysis in policy environments. Consult these checklists before finalizing empirical results for publication or policy briefings.

### Regression Specification and Estimation

**Model Specification Checklist:**
- Justify functional form (linear, log-linear, log-log) using economic theory and exploratory data analysis.
- Include all theoretically relevant controls to mitigate omitted variable bias.
- Test for nonlinearities using quadratic terms, splines, or generalized additive models.
- Avoid controlling for post-treatment variables that absorb the causal effect of interest.
- Clearly distinguish between reduced-form policy evaluation and structural parameter estimation.

**Diagnostic Tests (OLS):**
- Residual plots: Plot residuals versus fitted values to detect heteroskedasticity and nonlinearity. Plot residuals versus each regressor to identify omitted interactions.
- Q-Q plot: Assess normality of residuals for finite-sample validity of t-tests and F-tests.
- Breusch-Pagan test: Formal test for heteroskedasticity (`bptest` in R).
- White test: General test for heteroskedasticity including squares and cross-products of regressors.
- RESET test: Ramsey's regression specification error test for omitted variables and functional form (`resettest` in R).
- Variance inflation factors (VIF): Detect multicollinearity; VIF > 10 indicates severe collinearity requiring variable removal or ridge regression.

**Standard Error Adjustments:**
- Heteroskedasticity-consistent (HC) standard errors: Apply HC1 or HC3 estimators when Breusch-Pagan rejects homoskedasticity.
- Cluster-robust standard errors: Mandatory for panel data, repeated cross-sections, or geographic units to account for within-cluster correlation.
- Newey-West HAC standard errors: Adjust for autocorrelation and heteroskedasticity in time-series regressions.
- Bootstrap standard errors: Nonparametric alternative when asymptotic theory is questionable due to small samples or thick-tailed errors.

### Instrumental Variable Estimation

**Instrument Validity Checklist:**
- Relevance: First-stage F-statistic must exceed 10 (Stock-Yogo weak instrument threshold). Report first-stage regression results explicitly.
- Exclusion restriction: Argue qualitatively why the instrument affects the outcome only through the endogenous regressor. Conduct placebo tests on subpopulations unaffected by the instrument.
- Monotonicity: For LATE interpretation, argue that the instrument shifts treatment in the same direction for all individuals.
- Overidentification test: With multiple instruments, Sargan-Hansen J-test evaluates whether instruments satisfy exclusion restrictions as a group. Rejection suggests at least one instrument is invalid.

**Diagnostic Tests (2SLS/IV):**
- Weak instrument diagnostics: Compute Kleibergen-Paap F-statistic for heteroskedasticity-robust weak instrument test.
- Endogeneity test: Durbin-Wu-Hausman test compares OLS and 2SLS estimates; rejection confirms endogeneity necessitates IV.
- Overidentification test: Hansen J-statistic tests whether excluded instruments are orthogonal to the structural error.
- Plot reduced-form relationship: Regress outcome directly on instrument and controls; significant reduced-form coefficient is necessary for instrument relevance.

**Reporting Standards:**
- Report both OLS and 2SLS estimates side-by-side for comparison.
- Document first-stage regression with F-statistic and partial R-squared explicitly.
- State identifying assumptions in prose, acknowledging untestable aspects.
- Conduct sensitivity analysis relaxing exclusion restriction partially to assess robustness (Conley et al. sensitivity bounds).

### Panel Data Methods

**Fixed Effects vs. Random Effects:**
- Fixed effects (FE): Consistent when individual effects correlate with regressors. Eliminates time-invariant confounders but requires within-individual variation in treatment.
- Random effects (RE): More efficient than FE but inconsistent under correlation between effects and regressors. Use only when Hausman test fails to reject RE.
- First-differences: Alternative to FE robust to time-invariant measurement error in regressors.
- Correlated random effects (Mundlak device): Augment RE model with group means of time-varying regressors to control for correlation.

**Panel Data Diagnostics:**
- Hausman test: Compare FE and RE estimates; rejection favors FE.
- Serial correlation test: Wooldridge test for autocorrelation in panel data residuals.
- Cross-sectional dependence test: Pesaran CD test detects spatial correlation across panel units.
- Cluster-robust standard errors: Always cluster at the panel identifier (individual or firm) to account for within-unit autocorrelation.

**Difference-in-Differences (DiD):**
- Parallel trends assumption: Plot pre-treatment trends for treated and control groups. Conduct event-study regression with leads of treatment to test for pre-trends.
- Staggered treatment: Use Callaway-Sant'Anna or Sun-Abraham estimators to avoid bias from heterogeneous treatment effects and dynamic effects.
- Robust inference: Cluster standard errors at the unit of treatment assignment (e.g., state or policy jurisdiction).

### Time-Series Analysis

**Stationarity and Unit Root Tests:**
- Augmented Dickey-Fuller (ADF): Tests null hypothesis of unit root. Include trend and drift components as appropriate.
- Phillips-Perron (PP): Nonparametric alternative to ADF robust to heteroskedasticity and serial correlation.
- KPSS test: Reverses null and alternative; tests stationarity against unit root alternative.
- Breakpoint tests: Zivot-Andrews test allows for single structural break in trend or intercept.

**VAR Model Specification:**
- Lag length selection: Use AIC for forecasting, BIC for structural inference. Ensure residuals pass serial correlation tests.
- Stability condition: All roots of companion matrix must lie inside unit circle. Check stability before impulse response analysis.
- Cointegration: If variables are I(1) and cointegrated, estimate vector error correction model (VECM) instead of VAR in differences.
- Granger causality: Test whether lags of variable X improve forecasts of variable Y beyond Y's own lags.

**Impulse Response Functions:**
- Identification: Choose between recursive (Cholesky), long-run restrictions, or sign restrictions based on economic theory.
- Confidence intervals: Bootstrap IRFs with at least 1000 replications. Report point estimates and confidence bands.
- Forecast error variance decomposition: Quantify the fraction of forecast variance in each variable attributable to each structural shock.

### Computational Workflow Best Practices

**Reproducibility Standards:**
- Use version control (Git) for all estimation scripts and data processing pipelines.
- Set random number generator seeds for bootstrap, simulation, and cross-validation procedures.
- Document R and Python package versions in a `sessionInfo()` output or `requirements.txt` file.
- Separate raw data, processed data, estimation scripts, and output artifacts into distinct directories.
- Write R Markdown or Jupyter notebooks embedding code, results, and narrative exposition for full replication.

**Data Quality Checks:**
- Inspect summary statistics, histograms, and missing data patterns before estimation.
- Flag and investigate outliers using Tukey's rule (values beyond 1.5 IQR from quartiles).
- Merge datasets using unique identifiers and validate merge success rate (zero unmatched observations from master dataset).
- Standardize variable naming conventions and units across datasets.

**Estimation Efficiency:**
- Pre-compute fixed effects using `fixest` package for multi-way fixed effects with millions of observations.
- Use sparse matrix methods for large panel datasets with clustered standard errors.
- Parallelize bootstrap and cross-validation loops using `parallel` or `foreach` packages.
- Profile code to identify computational bottlenecks before optimizing.

**Inference Pitfalls to Avoid:**
- Do not interpret statistical significance as economic significance; report effect sizes and policy-relevant magnitudes.
- Do not cherry-pick specifications that yield desired results; report sensitivity across plausible alternatives.
- Do not claim causality from observational data without explicit identification strategy and robustness checks.
- Do not extrapolate out-of-sample predictions beyond the support of the training data.

### Troubleshooting Common Estimation Failures

**Convergence Failures in Nonlinear Models:**
- Rescale variables to avoid numerical precision issues (e.g., divide GDP by 1000).
- Provide better starting values from a simpler model or two-step estimation.
- Increase maximum iterations and tighten convergence tolerance.
- Check whether likelihood function is globally concave or exhibits multiple local optima.

**Weak Instruments:**
- Seek alternative instruments with stronger first-stage relationships.
- Combine multiple weak instruments to achieve collective strength.
- Use limited information maximum likelihood (LIML) estimator, which is less biased than 2SLS under weak instruments.
- Report Anderson-Rubin confidence intervals, which are robust to weak instruments but may be wide.

**Perfect Multicollinearity:**
- Drop one category from each set of mutually exclusive dummy variables.
- Remove linearly dependent regressors identified via condition number diagnostics.
- Use ridge regression or elastic net if multicollinearity is severe but all variables are theoretically essential.

**Heteroskedasticity or Autocorrelation:**
- Apply robust standard error corrections rather than attempting to "fix" the data.
- For time-series, consider GARCH models if volatility clustering is substantively important.
- In panel data, cluster at the highest level of aggregation where treatment is assigned.

This operational reference guide serves as a living diagnostic checklist, refined iteratively as you encounter novel empirical challenges in policy analysis. Econometric mastery emerges not from memorizing formulas but from internalizing the diagnostic workflow that connects theoretical identification assumptions to empirical falsification tests, translating abstract statistical theory into actionable policy intelligence.
