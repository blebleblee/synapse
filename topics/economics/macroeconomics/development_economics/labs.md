# Operational Verification Labs: Development Economics

## Objective & Operational Lab Setup

Development economics occupies the critical intersection between macroeconomic theory and the empirical realities of low-income economies transitioning toward industrialization, structural transformation, and sustained per-capita income growth. These laboratories are designed for practitioners who must operationalize development policy analysis, conduct rigorous empirical assessments of poverty traps, growth diagnostics, and institutional capacity constraints, and translate theoretical frameworks into actionable interventions that withstand scrutiny from multilateral development banks, finance ministries, and parliamentary budget committees.

The operational objective of these exercises is to build muscle memory in three critical development economics capabilities. First, you will construct and calibrate growth accounting decompositions that separate total factor productivity growth from capital accumulation and human capital formation, enabling precise identification of binding constraints on long-run convergence. Second, you will implement conditional convergence regressions and poverty trap diagnostics using real cross-country panel data, identifying structural breaks, institutional thresholds, and the empirical signatures of development takeoff versus stagnation. Third, you will conduct applied general equilibrium simulations of policy interventions—trade liberalization, infrastructure investment, conditional cash transfer programs—measuring their distributional impacts across income deciles and sectoral employment structures.

The analytical environment requires a quantitative spreadsheet platform capable of handling panel regression analysis, non-linear optimization, and matrix operations. Microsoft Excel with the Analysis ToolPak and Solver add-ins provides the baseline toolkit, though practitioners working in international development institutions may prefer Stata, R with the plm and lfe packages, or Python with pandas, statsmodels, and linearmodels libraries for handling large World Bank or Penn World Table datasets. The critical requirement is computational reproducibility: every parameter estimate, every calibrated model coefficient, and every simulated policy counterfactual must be traceable through transparent formula chains or annotated code blocks that a peer reviewer can audit line-by-line.

Establish a dedicated project directory structure that mirrors the empirical workflow. Create a `/data` subdirectory containing raw datasets from authoritative sources: Penn World Table 10.01 for aggregate output and capital stock series, World Development Indicators for sectoral employment and poverty headcount ratios, Barro-Lee educational attainment data for human capital stocks, and Polity IV or Varieties of Democracy indices for institutional quality measures. Maintain a `/scripts` subdirectory for reusable calculation templates and regression specification files. Store all calibrated model parameters and baseline simulation results in a `/calibration` subdirectory with versioned filenames that document the data vintage and parameter identification strategy. This discipline in data provenance and computational hygiene is not academic formalism—it is the operational standard that distinguishes rigorous development economics from policy advocacy masquerading as empirical analysis.

For each exercise, you will work with actual country time-series and cross-sectional datasets, not stylized toy examples. The laboratories deliberately impose the data quality constraints endemic to development economics: missing observations in conflict-affected states, measurement error in informal sector output, structural breaks from regime changes and civil wars, and the endogeneity problems that plague causal inference when institutions, geography, and historical legacies jointly determine both policy choices and economic outcomes. Learning to diagnose these empirical pathologies, construct defensible identification strategies, and communicate the resulting uncertainty bounds to non-technical policymakers constitutes the core operational competency this training develops.

Before proceeding to Exercise 1, verify your analytical environment by downloading the Penn World Table 10.01 dataset and successfully loading it into your spreadsheet or statistical software. Confirm that you can extract the real GDP (rgdpna), capital stock (rnna), employment (emp), and human capital index (hc) variables for at least 100 countries spanning 1960–2019. Verify that your regression toolkit can estimate fixed-effects panel models with clustered standard errors. This baseline capability check ensures that subsequent exercises will not founder on software configuration issues when you need to focus on economic interpretation and policy inference.

## Exercise 1: Foundational Practical Implementation

### Growth Accounting Decomposition and Total Factor Productivity Estimation

The Solow growth accounting framework decomposes aggregate output growth into contributions from capital accumulation, labor force expansion, and total factor productivity (TFP) growth—the residual capturing technological progress, institutional quality improvements, and allocative efficiency gains. For a developing economy, TFP growth represents the critical margin separating convergence toward high-income status from middle-income stagnation. This exercise operationalizes the full growth accounting workflow for a representative emerging market, establishing the empirical baseline for subsequent policy counterfactuals.

Select a developing economy with reasonably complete Penn World Table coverage from 1960 to 2019. Good candidates include South Korea (demonstrating successful convergence), Thailand (exhibiting middle-income slowdown), or Ghana (representing sub-Saharan African growth acceleration post-2000). Extract the annual time series for real GDP at constant national prices (`rgdpna`), capital stock at constant national prices (`rnna`), number of persons engaged (`emp`), and the human capital index (`hc`). The human capital index aggregates average years of schooling and returns to education into a single productivity-adjusted labor input measure.

Construct the capital-augmented production function in its growth-rate form. The standard Cobb-Douglas specification with human-capital-augmented labor takes the form:

$$Y_t = A_t K_t^\alpha (h_t L_t)^{1-\alpha}$$

where $Y_t$ denotes real output, $K_t$ is the capital stock, $L_t$ represents raw employment, $h_t$ is the human capital index per worker, $A_t$ captures total factor productivity, and $\alpha$ is capital's output elasticity. Taking logarithms and differentiating with respect to time yields the growth accounting identity:

$$g_Y = g_A + \alpha g_K + (1-\alpha)(g_h + g_L)$$

where $g_X \equiv \frac{\dot{X}}{X}$ denotes the proportional growth rate of variable $X$. The empirical task is to calculate each observable growth rate from the data and solve for the implied TFP growth rate $g_A$ as the residual.

In your spreadsheet, create annual growth rate columns by computing the log-difference: `g_Y = LN(Y_t / Y_{t-1})`. Repeat this calculation for capital, employment, and human capital. The critical calibration choice concerns the capital share parameter $\alpha$. Cross-country empirical evidence suggests $\alpha \approx 0.35$ for developing economies, reflecting lower capital intensity than advanced economies. However, you should verify this calibration using your country's national accounts data. If labor compensation data are available, compute $\alpha$ directly as the capital share of national income: $\alpha = 1 - \frac{W \cdot L}{Y}$, where $W$ denotes the average wage. For countries lacking reliable labor compensation series, use $\alpha = 0.35$ as the baseline and conduct sensitivity analysis across the range $[0.30, 0.40]$.

With the capital share calibrated, calculate the contribution of each factor to output growth. Capital's contribution is $\alpha \cdot g_K$, and human-capital-augmented labor's contribution is $(1-\alpha) \cdot (g_h + g_L)$. The TFP growth residual emerges as:

$$g_A = g_Y - \alpha g_K - (1-\alpha)(g_h + g_L)$$

Construct this decomposition for every year in your sample, then compute decade averages to smooth business cycle fluctuations and highlight structural trends. For South Korea, you should observe TFP growth averaging 2–3% annually during the 1960–1990 high-growth period, with capital accumulation contributing 3–4 percentage points and human capital adding another 1–2 percentage points to the 7–9% annual GDP growth. For sub-Saharan African economies, TFP growth often stagnates or turns negative during 1980–2000, explaining output growth collapse despite continued capital and labor force expansion.

Now extend the analysis to identify structural breaks and growth accelerations. Plot the cumulative TFP level $A_t = A_0 \exp\left(\sum_{s=1}^{t} g_{A,s}\right)$ on a log scale. Growth accelerations appear as upward inflections in the slope, while productivity collapses manifest as flat or declining segments. For Ghana, you should identify a clear structural break around 2000, coinciding with debt relief, macroeconomic stabilization, and improved governance indicators. This visual diagnostic provides the empirical foundation for subsequently testing whether policy reforms causally drove the acceleration.

Document your findings in a summary table with the following structure:

**Growth Accounting Decomposition: [Country Name], 1960–2019**

| Period | GDP Growth | Capital Contribution | Labor Contribution | Human Capital Contribution | TFP Growth |
|--------|------------|----------------------|--------------------|-----------------------------|------------|
| 1960–1970 | [value]% | [value]pp | [value]pp | [value]pp | [value]% |
| 1970–1980 | [value]% | [value]pp | [value]pp | [value]pp | [value]% |
| 1980–1990 | [value]% | [value]pp | [value]pp | [value]pp | [value]% |
| 1990–2000 | [value]% | [value]pp | [value]pp | [value]pp | [value]% |
| 2000–2010 | [value]% | [value]pp | [value]pp | [value]pp | [value]% |
| 2010–2019 | [value]% | [value]pp | [value]pp | [value]pp | [value]% |

The operational lesson from this decomposition is diagnostic precision. When a finance ministry claims that infrastructure investment will deliver 5% annual growth, you can now quantify exactly how much capital accumulation must occur—and how much TFP growth must simultaneously materialize—to deliver that outcome. When TFP growth stagnates despite rising educational attainment, you have identified an allocative efficiency or institutional quality constraint that schooling alone cannot overcome. This is the empirical bedrock for prioritizing reforms.

### Cross-Country Conditional Convergence Regression

The neoclassical growth model predicts conditional convergence: holding constant the determinants of steady-state income (savings rate, population growth, human capital, institutions), poorer countries should grow faster than richer countries as they accumulate capital toward their steady state. Testing this prediction empirically requires estimating the convergence coefficient $\beta$ in the cross-country regression:

$$g_{i,t} = \alpha + \beta \ln(y_{i,t-1}) + \gamma' X_{i,t} + \epsilon_{i,t}$$

where $g_{i,t}$ is country $i$'s average growth rate over period $t$, $y_{i,t-1}$ is initial income, and $X_{i,t}$ represents the vector of steady-state determinants. A negative and statistically significant $\beta$ confirms conditional convergence, with the magnitude indicating the speed of adjustment toward steady state.

Construct a cross-sectional dataset for the period 1990–2019 using Penn World Table data. For each country with complete data coverage, calculate the average annual growth rate of real GDP per capita over this 30-year window. Record the log of initial (1990) real GDP per capita as your key regressor. Assemble the conditioning variables: the average investment-to-GDP ratio (proxy for savings rate), the average population growth rate, the average years of schooling (from Barro-Lee data), and a governance quality index (use the average Polity2 score from Polity IV, or the World Bank's Government Effectiveness index if available).

Estimate the regression using ordinary least squares with heteroskedasticity-robust standard errors. In Excel, arrange your data with each country as a row and variables in columns. Use the Data Analysis ToolPak's Regression function, specifying growth rate as the dependent variable and initial log income plus all conditioning variables as independent variables. Check the "Residuals" and "Residual Plots" options to generate diagnostic output for subsequent validation.

For a properly specified convergence regression, you should obtain $\beta \approx -0.02$ to $-0.03$, implying that a country starting at half the initial income of another (one log point lower) grows approximately 2–3 percentage points faster annually, conditional on having similar steady-state determinants. The implied half-life of convergence is $\frac{\ln(2)}{|\beta|} \approx 23$ to 35 years—consistent with the observation that it takes several decades for successful emerging markets to close income gaps with advanced economies.

Examine the coefficient on the investment rate $\gamma_{\text{inv}}$. You should find a positive and significant effect: countries investing 25% of GDP grow substantially faster than those investing 15%, holding initial income constant. The schooling coefficient $\gamma_{\text{school}}$ should also be positive, quantifying the growth return to human capital accumulation. The governance coefficient $\gamma_{\text{gov}}$ captures the institutional quality channel—countries with stronger rule of law, lower corruption, and more accountable governments grow faster even after controlling for physical and human capital accumulation.

Now conduct the critical diagnostic test for omitted variable bias and model misspecification. Generate a scatterplot of the residuals against initial log income. If the convergence regression is correctly specified, the residuals should exhibit no systematic pattern with respect to initial income—they should be a horizontal cloud centered at zero. If you observe a U-shaped or inverted U-shaped pattern, this indicates omitted non-linearities or threshold effects. Sub-Saharan African countries often cluster as negative outliers, suggesting region-specific growth impediments not fully captured by the included regressors.

Test for outlier sensitivity by re-estimating the regression after dropping countries affected by civil wars, hyperinflation episodes, or economic collapse during the sample period. Compare the convergence coefficient before and after exclusion. If $\beta$ changes substantially, your baseline result is driven by extreme observations rather than representing the general convergence process. Document which countries drive the result and investigate their specific circumstances.

Finally, decompose the cross-country income variance into explained and unexplained components. The regression $R^2$ indicates the fraction of growth variation explained by initial income and steady-state determinants—typically 40–60% in well-specified models. The remaining variance reflects idiosyncratic shocks, measurement error, and omitted variables. For policy purposes, the key insight is that even after controlling for investment, education, and governance, enormous growth heterogeneity persists across developing economies. This residual variation represents the frontier of unsolved questions in development economics: why do countries with apparently similar fundamentals experience radically different growth trajectories?

Record your regression results in a standardized table format:

**Conditional Convergence Regression, 1990–2019 (N = [number] countries)**

| Variable | Coefficient | Std. Error | t-statistic | p-value |
|----------|-------------|------------|-------------|---------|
| Log Initial GDP per capita (1990) | $\beta$ | (se) | [t] | [p] |
| Investment Rate (% GDP) | $\gamma_{\text{inv}}$ | (se) | [t] | [p] |
| Population Growth Rate | $\gamma_{\text{pop}}$ | (se) | [t] | [p] |
| Average Years of Schooling | $\gamma_{\text{school}}$ | (se) | [t] | [p] |
| Governance Quality Index | $\gamma_{\text{gov}}$ | (se) | [t] | [p] |
| Constant | $\alpha$ | (se) | [t] | [p] |

**Model Fit:** $R^2$ = [value], Adjusted $R^2$ = [value], F-statistic = [value] (p = [value])

This table format is the operational standard for communicating regression results to policymakers. It enables immediate assessment of effect magnitudes, statistical significance, and model explanatory power. A finance minister can directly interpret the governance coefficient: improving from the 25th to the 75th percentile of governance quality (roughly a 1-standard-deviation improvement) translates into [calculate: $\gamma_{\text{gov}} \times 1$] percentage points of additional annual growth over the subsequent 30 years.

## Exercise 2: Parameter Variation & Empirical Analysis

### Poverty Trap Diagnostics and Threshold Regression Analysis

The poverty trap hypothesis posits that multiple equilibria exist in the development process: countries above a critical income or capital threshold converge toward high-income steady states, while those below the threshold remain stuck in low-income stagnation despite conventional policy reforms. Identifying poverty traps empirically requires detecting non-linearities in the growth-initial income relationship and testing whether the convergence coefficient $\beta$ varies systematically with initial conditions. This exercise operationalizes threshold regression techniques to test for poverty trap dynamics in cross-country data.

Return to your convergence regression dataset from Exercise 1, but now extend the sample backward to include the 1960–1990 period wherever data permit. This longer time span captures the pre-1990 growth collapses in Latin America and sub-Saharan Africa, increasing the likelihood of detecting threshold effects. Pool the data into non-overlapping 30-year windows (1960–1990 and 1990–2019) to construct a pseudo-panel with approximately 200–250 country-period observations.

The threshold regression model partitions the sample based on initial income:

$$g_{i,t} = \begin{cases}
\alpha_L + \beta_L \ln(y_{i,t-1}) + \gamma_L' X_{i,t} + \epsilon_{i,t} & \text{if } \ln(y_{i,t-1}) < \tau \\
\alpha_H + \beta_H \ln(y_{i,t-1}) + \gamma_H' X_{i,t} + \epsilon_{i,t} & \text{if } \ln(y_{i,t-1}) \geq \tau
\end{cases}$$

where $\tau$ represents the threshold income level, and subscripts $L$ and $H$ denote low-income and high-income regime parameters. A poverty trap is indicated by $|\beta_L| < |\beta_H|$: convergence is slower (or absent) below the threshold.

Estimating $\tau$ requires a grid search procedure. Begin by sorting your pooled sample by initial log income. Test a sequence of candidate thresholds spanning the 20th to 80th percentiles of the initial income distribution. For each candidate $\tau$, split the sample, estimate separate regressions for the below-threshold and above-threshold subsamples, and compute the sum of squared residuals (SSR) across both regressions. The optimal threshold $\hat{\tau}$ minimizes the combined SSR.

Implement this in Excel using a manual grid search. Create a column listing 20 candidate threshold values spanning $\ln(y) \in [7.5, 10.5]$ (corresponding roughly to $2,000 to $30,000 in constant 2017 PPP dollars). For each candidate, use nested IF statements to create an indicator variable splitting the sample, then run separate regressions for each regime. Record the SSR from each regression pair. Identify the threshold that yields the minimum combined SSR—this is your estimated $\hat{\tau}$.

At the optimal threshold, compare the convergence coefficients $\hat{\beta}_L$ and $\hat{\beta}_H$. For sub-Saharan African countries, empirical studies frequently find $\hat{\beta}_L \approx -0.01$ (slow convergence) below the threshold versus $\hat{\beta}_H \approx -0.03$ (standard convergence) above the threshold, with $\hat{\tau}$ around $\ln(y) \approx 8.5$ (roughly $5,000 per capita). This indicates that countries trapped below $5,000 per capita face structurally slower convergence dynamics—a diagnostic signature of poverty trap mechanisms.

The key diagnostic is testing whether this threshold effect is statistically significant or merely a data-mining artifact. Implement a bootstrap procedure to construct confidence intervals for $\hat{\tau}$. Resample your dataset with replacement 1,000 times, re-estimate the threshold for each bootstrap sample, and record the distribution of threshold estimates. The 95% confidence interval is the range between the 2.5th and 97.5th percentiles of this bootstrap distribution. If the confidence interval is wide, spanning several thousand dollars of per-capita income, the threshold estimate is imprecise and should not guide policy. If the confidence interval is narrow, you have credible evidence of a threshold effect.

Now investigate potential mechanisms underlying the threshold. Re-estimate the threshold regression using different conditioning variables: first with only investment and population growth (testing for a capital accumulation threshold), then adding human capital (testing for an education threshold), then adding governance quality (testing for an institutional threshold). If the threshold disappears when conditioning on governance, this suggests that the apparent income threshold is actually an institutional quality threshold—countries below a critical level of state capacity, rule of law, or contract enforcement cannot sustain convergence regardless of investment or education.

An alternative poverty trap diagnostic examines the distribution dynamics of income across countries over time. Construct a transition matrix showing the probability that a country in income quintile $j$ at time $t$ moves to quintile $k$ at time $t+30$. If perfect convergence holds, countries should exhibit high upward mobility from lower quintiles and downward mobility from upper quintiles, with the long-run distribution converging to a single mode. If poverty traps exist, you will observe persistence probability $p_{jj}$ high for the lowest quintile (countries remain poor) and high for the highest quintile (countries remain rich), with low transition probabilities between bottom and top—a "twin peaks" distribution.

Calculate this transition matrix using your 1990 and 2019 cross-sections. Rank countries by GDP per capita in 1990, assign each to a quintile (Q1 = poorest 20%, Q5 = richest 20%), then record their 2019 quintile assignment. Construct the $5 \times 5$ transition probability matrix where element $(j,k)$ is the fraction of countries starting in quintile $j$ that ended in quintile $k$. Persistence probabilities appear on the diagonal. For a sample of 100–150 countries, you should observe $p_{11} \approx 0.60$ to $0.75$ (most poor countries remain poor) and $p_{55} \approx 0.80$ to $0.90$ (most rich countries remain rich), with off-diagonal transition probabilities below 0.15. This immobility pattern provides complementary evidence of poverty trap dynamics.

Document your findings in a threshold regression summary:

**Threshold Regression Results: Growth on Initial Income**

- **Estimated Threshold:** $\hat{\tau} =$ [value] log GDP per capita ($[value] constant 2017 PPP)
- **Bootstrap 95% Confidence Interval:** $[\text{lower}, \text{upper}]$

| Regime | Sample Size | Convergence Coefficient $\beta$ | Std. Error | Investment Coeff. | Governance Coeff. |
|--------|-------------|----------------------------------|------------|-------------------|-------------------|
| Below Threshold | [N_L] | $\hat{\beta}_L$ | (se) | $\hat{\gamma}_{inv,L}$ | $\hat{\gamma}_{gov,L}$ |
| Above Threshold | [N_H] | $\hat{\beta}_H$ | (se) | $\hat{\gamma}_{inv,H}$ | $\hat{\gamma}_{gov,H}$ |

**Interpretation:** [Describe whether the threshold is statistically robust, which conditioning variables eliminate it, and what this implies for policy prioritization.]

The operational implication is strategic resource allocation. If poverty traps are real and driven by institutional thresholds, then aid flows and technical assistance must prioritize governance capacity building before infrastructure investment can yield sustained growth. If the threshold is spurious and disappears when conditioning on human capital, then universal primary education becomes the policy priority. The empirics directly inform the intervention hierarchy.

### Instrumental Variables Estimation: Institutions and Growth

The positive correlation between institutional quality and economic growth documented in Exercise 1 does not establish causality—it may reflect reverse causation (richer countries can afford better institutions) or omitted variables (geographic or cultural factors that jointly determine institutions and income). Credible causal inference requires an instrumental variables (IV) strategy that isolates exogenous variation in institutional quality. This exercise implements the canonical Acemoglu-Johnson-Robinson (AJR) settler mortality instrument, operationalizing the full IV workflow from first-stage diagnostics through structural interpretation.

The AJR identification strategy exploits the historical fact that European colonizers established extractive institutions (weak property rights, authoritarian governance) in colonies where high settler mortality from tropical diseases (malaria, yellow fever) discouraged permanent settlement, while establishing inclusive institutions (strong property rights, democratic constraints on executive power) in temperate colonies where low settler mortality enabled large-scale European settlement. Since settler mortality 200 years ago plausibly does not affect current income through any channel except its historical impact on institutions, it serves as a valid instrument for contemporary institutional quality.

Assemble the dataset by merging Penn World Table income data with the AJR settler mortality data (available from Acemoglu's website) and the Polity IV governance index. Restrict the sample to former European colonies with available settler mortality data—this yields roughly 60–70 countries spanning Africa, the Americas, Asia, and Oceania. Record the log of settler mortality per 1,000 early European settlers as your instrument, the Polity2 democracy score (or an alternative governance index) as the endogenous regressor, and the log of current (2019) GDP per capita as the outcome variable.

The IV estimation proceeds in two stages. The first-stage regression estimates the relationship between the instrument (settler mortality) and the endogenous regressor (institutions):

$$\text{Institutions}_i = \delta_0 + \delta_1 \ln(\text{Settler Mortality}_i) + \delta_2' Z_i + \nu_i$$

where $Z_i$ represents exogenous controls (latitude, continent fixed effects). Estimate this regression using OLS. The first-stage F-statistic tests instrument strength: values above 10 indicate a sufficiently strong instrument, while values below 10 signal weak instrument problems that invalidate IV inference.

In your spreadsheet, regress the Polity2 score on log settler mortality and latitude. You should obtain $\hat{\delta}_1 \approx -0.50$ to $-0.80$: a one-log-point increase in settler mortality (e.g., doubling mortality) reduces the democracy score by 0.5–0.8 points on the −10 to +10 Polity scale. The first-stage F-statistic should exceed 15–20, confirming strong instrument relevance. Save the predicted values $\widehat{\text{Institutions}}_i$ from this regression.

The second-stage regression estimates the causal effect of institutions on income using the predicted institutional quality from the first stage:

$$\ln(\text{GDP per capita})_i = \beta_0 + \beta_1 \widehat{\text{Institutions}}_i + \beta_2' Z_i + \epsilon_i$$

Estimate this regression, treating the fitted values from the first stage as the regressor. The coefficient $\hat{\beta}_1$ is the IV estimate of institutions' causal effect on income. Standard errors require a correction for the two-stage procedure; in practice, use the IV regression function in your statistical software's toolkit if available, or apply the formula:

$$\text{se}(\hat{\beta}_1^{IV}) = \frac{\hat{\sigma}_\epsilon}{\hat{\sigma}_\nu \sqrt{N} \cdot |\hat{\delta}_1|}$$

where $\hat{\sigma}_\epsilon$ and $\hat{\sigma}_\nu$ are the standard deviations of the second-stage and first-stage residuals, respectively.

The IV estimate typically yields $\hat{\beta}_1^{IV} \approx 0.70$ to $1.00$: a one-point improvement in the Polity2 democracy score (e.g., transitioning from electoral autocracy to electoral democracy) raises log income by 0.7–1.0, corresponding to a 100–170% increase in GDP per capita. This effect is substantially larger than the OLS estimate (typically $\hat{\beta}_1^{OLS} \approx 0.30$ to $0.50$), consistent with reverse causation bias attenuating the OLS coefficient—richer countries improve institutions, partially masking institutions' positive causal effect on income.

The critical validity test concerns the exclusion restriction: settler mortality affects current income only through institutions, not through direct channels. The main threat is geographic correlation—settler mortality was high in tropical regions, which also have agricultural productivity disadvantages or disease burdens affecting current income directly. Test this by including latitude, a malaria ecology index, and continent fixed effects as controls in both stages. If the IV estimate remains large and significant after including these geographic controls, the exclusion restriction is more plausible.

Conduct an overidentification test if you have multiple instruments. In addition to settler mortality, the AJR study uses indigenous population density in 1500 (areas with dense populations saw extractive colonial institutions designed to exploit native labor). Estimate the IV regression using both instruments, then test whether the two instruments yield consistent estimates using the Hansen J-statistic. Rejection of the overidentification test indicates that at least one instrument violates the exclusion restriction.

Document your IV results in a comparative table contrasting OLS and IV estimates:

**Institutions and Income: OLS vs. Instrumental Variables Estimates**

| Estimation Method | Institutional Quality Coefficient | Std. Error | 95% Confidence Interval | First-Stage F-stat |
|-------------------|-----------------------------------|------------|-------------------------|---------------------|
| OLS | $\hat{\beta}_1^{OLS}$ | (se) | $[\text{lower}, \text{upper}]$ | — |
| IV (Settler Mortality) | $\hat{\beta}_1^{IV}$ | (se) | $[\text{lower}, \text{upper}]$ | [F-stat] |

**Sample:** [N] former European colonies | **Controls:** Latitude, continent fixed effects

**Interpretation:** The IV estimate is [larger/smaller] than OLS, consistent with [describe the direction of bias in OLS]. The first-stage F-statistic of [value] indicates [strong/weak] instrument relevance. The exclusion restriction assumes settler mortality affects income only through institutions, conditional on geography controls.

The operational takeaway is evidentiary standards for policy. Cross-country correlations between governance and growth, no matter how robust, do not justify prioritizing governance reforms over alternative interventions without credible causal identification. The IV evidence provides that causal anchor, but at the cost of large standard errors and external validity concerns—the estimate applies to variation in institutions induced by colonial origins, which may not generalize to contemporary institutional reforms. Honest communication of these inferential limits is the hallmark of operational rigor.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Applied General Equilibrium Simulation: Trade Liberalization and Distributional Impacts

Policy interventions in developing economies generate equilibrium effects across sectors, factor markets, and household income distributions that partial equilibrium analysis cannot capture. A tariff reduction not only lowers consumer prices but also reallocates labor between tradable and non-tradable sectors, alters the skill premium in wages, and shifts income across rural and urban households through agricultural price channels. Applied general equilibrium (AGE) models quantify these systemic effects, enabling ex-ante policy evaluation before costly real-world implementation. This exercise constructs and simulates a stylized two-sector, two-factor AGE model of a small open economy undergoing trade liberalization, measuring the distributional consequences across income deciles.

The model economy consists of a tradable manufacturing sector and a non-tradable services sector, each producing output using skilled and unskilled labor with sector-specific production technologies. The manufacturing sector faces import competition from world markets at exogenous world prices, while the service sector produces only for domestic consumption. Households supply labor inelastically and consume both goods, with preferences represented by Cobb-Douglas utility. The policy experiment is a reduction in the manufacturing import tariff, which lowers the domestic manufacturing price, triggers factor reallocation from manufacturing to services, and redistributes income between skilled and unskilled workers.

Specify the production functions. Manufacturing output $Q_M$ uses skilled labor $S_M$ and unskilled labor $U_M$ with a constant elasticity of substitution (CES) technology:

$$Q_M = A_M \left[ \alpha_M S_M^\rho + (1 - \alpha_M) U_M^\rho \right]^{1/\rho}$$

where $A_M$ is total factor productivity, $\alpha_M$ is the distribution parameter (share weight on skilled labor), and $\rho = \frac{\sigma - 1}{\sigma}$ with $\sigma$ the elasticity of substitution between skill types. Calibrate $A_M = 1$, $\alpha_M = 0.60$ (manufacturing is skill-intensive), and $\sigma = 1.5$ (moderate substitutability). Services production $Q_S$ uses the same CES form with $\alpha_S = 0.40$ (services are less skill-intensive) and the same elasticity.

Specify household preferences over manufacturing and services consumption:

$$U = C_M^\theta C_S^{1-\theta}$$

where $\theta = 0.50$ implies equal expenditure shares on both goods at baseline. The household budget constraint is $P_M C_M + P_S C_S = w_S S + w_U U$, where $P_M$ and $P_S$ are good prices, $w_S$ and $w_U$ are skilled and unskilled wage rates, and $S$ and $U$ are the household's endowments of skilled and unskilled labor (supplied inelastically).

Define the trade policy regime. The domestic manufacturing price relates to the world price $P_M^*$ through the tariff: $P_M = (1 + t) P_M^*$. Normalize $P_M^* = 1$ (the world price is the numeraire), so the baseline tariff rate determines the domestic price. Calibrate the baseline tariff at $t = 0.20$ (20%), implying $P_M = 1.20$ initially. The services price $P_S$ is determined by domestic market clearing.

The equilibrium conditions are:

1. **Profit maximization (factor demands):** Firms in each sector hire skilled and unskilled labor to equate marginal revenue products to wages:
   
   $$w_S = P_M \cdot \frac{\partial Q_M}{\partial S_M}, \quad w_U = P_M \cdot \frac{\partial Q_M}{\partial U_M}$$
   
   and similarly for services. With CES production, these yield:
   
   $$\frac{S_M}{U_M} = \left[ \frac{\alpha_M}{1 - \alpha_M} \cdot \frac{w_U}{w_S} \right]^\sigma$$

2. **Labor market clearing:** Total skilled and unskilled labor supplies equal total demands across sectors:
   
   $$S_M + S_S = S, \quad U_M + U_S = U$$

3. **Goods market clearing for services:** Domestic production equals consumption:
   
   $$Q_S = C_S$$

4. **Budget balance:** Household expenditure equals factor income:
   
   $$P_M C_M + P_S C_S = w_S S + w_U U$$

5. **Utility maximization (consumption demands):** Cobb-Douglas preferences yield:
   
   $$P_M C_M = \theta (w_S S + w_U U), \quad P_S C_S = (1 - \theta)(w_S S + w_U U)$$

Calibrate the baseline equilibrium by fixing the aggregate labor endowments at $S = 30$ (skilled workers) and $U = 70$ (unskilled workers), reflecting a typical developing economy skill distribution. Solve the system numerically by guessing initial factor prices $(w_S, w_U)$ and the services price $P_S$, computing factor demands and consumption demands implied by the equilibrium conditions, checking whether labor markets and the services market clear, and iterating on prices until all markets clear simultaneously.

Implement the solver in Excel using the Solver add-in. Set up columns for the six endogenous variables: $w_S$, $w_U$, $P_S$, $S_M$, $S_S$, $U_M$, $U_S$, $Q_M$, $Q_S$, $C_M$, $C_S$. Define formula cells that compute these variables as functions of the factor prices using the equilibrium conditions above. Define three target cells representing the market-clearing errors:

$$\text{Error}_S = S_M + S_S - S, \quad \text{Error}_U = U_M + U_S - U, \quad \text{Error}_{Q_S} = Q_S - C_S$$

Invoke Solver to minimize the sum of squared errors $\text{Error}_S^2 + \text{Error}_U^2 + \text{Error}_{Q_S}^2$ by adjusting $(w_S, w_U, P_S)$ subject to non-negativity constraints on all variables. Start with initial guesses $w_S = 2.0$, $w_U = 1.0$, $P_S = 1.5$. Solver should converge to the baseline equilibrium within seconds.

Record the baseline equilibrium values: factor allocations across sectors, wage rates, output levels, and consumption levels. The skill premium $w_S / w_U$ should be approximately 2.0–2.5, reflecting the scarcity of skilled labor and the skill intensity of manufacturing under tariff protection.

Now simulate the trade liberalization policy experiment. Reduce the tariff from $t = 0.20$ to $t = 0.10$, lowering the domestic manufacturing price from $P_M = 1.20$ to $P_M = 1.10$. Re-run Solver to compute the new equilibrium factor allocations, wages, and consumption levels. The key outcomes to track:

1. **Factor reallocation:** Manufacturing production contracts as import competition intensifies. Labor reallocates from manufacturing to services. Measure the change in sectoral employment shares.

2. **Wage effects:** The skill premium $w_S / w_U$ falls because manufacturing (the skill-intensive sector) shrinks. Compute the percentage change in skilled and unskilled wages.

3. **Consumption gains:** Lower manufacturing prices increase real purchasing power. Compute the percentage change in household utility (equivalent variation in income).

For a typical calibration, you should observe a 5–10% decline in manufacturing employment, a 3–5 percentage point reduction in the skill premium, and a 2–4% gain in aggregate utility. Crucially, the distributional impacts are non-uniform: unskilled workers benefit from higher real wages (the manufacturing price decline dominates their nominal wage reduction), while skilled workers may lose in real terms if their nominal wage decline exceeds the price decline.

Extend the analysis to heterogeneous households by disaggregating the labor endowments across income deciles. Assign the lowest three deciles zero skilled labor and high unskilled labor endowments, reflecting low-education households. Assign the top two deciles high skilled labor and low unskilled labor endowments, representing educated urban elites. Middle deciles have intermediate mixes. For each decile, compute the change in real income from the tariff reduction:

$$\Delta \ln(\text{Real Income})_d = \frac{w_S^{\text{new}} S_d + w_U^{\text{new}} U_d}{P_M^{\text{new}\theta} P_S^{\text{new}(1-\theta)}} - \frac{w_S^{\text{base}} S_d + w_U^{\text{base}} U_d}{P_M^{\text{base}\theta} P_S^{\text{base}(1-\theta)}}$$

Plot the distributional incidence: real income change on the vertical axis, income decile on the horizontal axis. Trade liberalization typically generates a progressive distributional pattern—lower deciles gain more than upper deciles because unskilled workers benefit disproportionately from cheaper manufactured goods. However, if manufacturing workers are geographically concentrated or face high adjustment costs, short-run distributional effects may be regressive, with localized employment losses dominating long-run consumption gains.

This distributional diagnostic is operationally critical. A finance ministry proposing tariff reform must anticipate and address the political economy of trade adjustment. If the top three deciles lose real income, they will mobilize opposition through lobbying and media campaigns. If rural agricultural regions (which supply unskilled labor to services) gain while urban manufacturing regions lose, regional cleavages will dominate the reform debate. The AGE model quantifies these trade-offs, enabling policymakers to design compensatory transfers or adjustment assistance programs that build reform coalitions.

Document your simulation results in a policy impact table:

**AGE Simulation Results: Trade Liberalization (Tariff Reduction from 20% to 10%)**

| Outcome Variable | Baseline | Post-Liberalization | % Change |
|------------------|----------|---------------------|----------|
| Manufacturing Employment Share | [value] | [value] | [value]% |
| Services Employment Share | [value] | [value] | [value]% |
| Skilled Wage ($w_S$) | [value] | [value] | [value]% |
| Unskilled Wage ($w_U$) | [value] | [value] | [value]% |
| Skill Premium ($w_S / w_U$) | [value] | [value] | [value]% |
| Aggregate Utility | [value] | [value] | [value]% |

**Distributional Impacts by Income Decile:**

| Decile | Skilled Labor Endowment | Unskilled Labor Endowment | Real Income Change |
|--------|-------------------------|---------------------------|---------------------|
| 1 (poorest) | 0 | 12 | +[value]% |
| 2 | 0 | 11 | +[value]% |
| 3 | 1 | 10 | +[value]% |
| ... | ... | ... | ... |
| 10 (richest) | 10 | 2 | +[value]% |

**Policy Interpretation:** Trade liberalization generates aggregate welfare gains of [value]%, but distributional effects are [progressive/regressive]. The bottom [number] deciles gain [value]% real income, while the top [number] deciles gain [value]%. Sectoral reallocation requires [value] workers to shift from manufacturing to services, which may involve transitional unemployment if labor mobility is limited.

### Robustness Testing and Sensitivity Analysis: Parameter Variation

The AGE simulation outcomes depend critically on structural parameters—the elasticity of substitution between skill types, the consumption preference share, and the labor endowments. Real-world parameter values are uncertain, estimated with error from microdata or calibrated from aggregate relationships. Robust policy conclusions require sensitivity analysis demonstrating that qualitative results hold across plausible parameter ranges. This exercise implements systematic robustness checks by varying key parameters one at a time and mapping the resulting change in distributional outcomes.

Begin with the elasticity of substitution in production, $\sigma$. The baseline calibration used $\sigma = 1.5$. This value governs how easily firms can substitute skilled for unskilled labor in response to wage changes. A higher $\sigma$ implies greater substitutability, meaning tariff reductions induce larger factor reallocations and smaller wage adjustments. A lower $\sigma$ implies factors are complements, so wages adjust more and employment reallocation is limited.

Re-run the trade liberalization simulation with $\sigma \in \{1.0, 1.25, 1.5, 1.75, 2.0\}$. For each value, record the post-liberalization skill premium and the real income change for the bottom decile and top decile. Plot these outcomes against $\sigma$. You should observe that as $\sigma$ rises, the skill premium decline moderates (firms substitute toward unskilled labor more easily, dampening the wage effect), and distributional impacts become more regressive (high-skill workers can preserve their earnings by shifting sectors).

The critical threshold to identify is the elasticity value at which distributional progressivity reverses. For most calibrations, this occurs around $\sigma \approx 2.0$ to $2.5$. If empirical estimates of $\sigma$ from labor market microdata lie below this threshold, the progressive distributional conclusion is robust. If estimates span the threshold, policy uncertainty is high, and distributional outcomes could go either way depending on the true labor market substitutability.

Next, vary the consumption preference parameter $\theta$, which governs the expenditure share on manufactured goods. The baseline used $\theta = 0.50$. If manufacturing constitutes a larger share of household budgets (higher $\theta$), tariff reductions deliver larger real income gains through the price channel. Re-run the simulation with $\theta \in \{0.40, 0.45, 0.50, 0.55, 0.60\}$ and plot aggregate utility gains against $\theta$. The relationship should be positive and approximately linear: a 10 percentage point increase in manufacturing budget share raises utility gains by 1–2 percentage points.

This sensitivity test is operationally relevant when extending the model to multiple goods. If the tariff applies only to luxury manufactures consumed primarily by high-income households, aggregate utility gains will be small and distributional impacts regressive. If the tariff applies to staple goods consumed by all households, utility gains are large and progressive. The parameter $\theta$ is a reduced-form proxy for this heterogeneity across goods.

Finally, stress-test the labor market clearing assumption by introducing unemployment rigidity. In the baseline model, labor reallocates frictionlessly across sectors at full employment. In reality, displaced manufacturing workers may experience prolonged unemployment or only partially transition to services jobs. Model this by adding a constraint: post-liberalization manufacturing employment can fall by at most 10% (simulating labor mobility frictions or sector-specific skills). Re-solve the model with this constraint binding.

The constrained equilibrium will exhibit involuntary unemployment: manufacturing employment exceeds the unconstrained profit-maximizing level, and the manufacturing sector's marginal revenue product of labor falls below the wage. Measure the resulting unemployment rate and calculate the unemployment-inclusive utility change. For realistic frictions, the aggregate utility gain from liberalization may fall by 50% or more, and the distributional impacts may flip regressive as unskilled manufacturing workers bear the full adjustment cost through unemployment rather than smooth reallocation to services.

Document this stress test with a comparative table:

**Sensitivity Analysis: Trade Liberalization Outcomes Under Parameter Variation**

| Parameter Scenario | Aggregate Utility Gain | Skill Premium Change | Bottom Decile Real Income Change | Top Decile Real Income Change |
|--------------------|------------------------|----------------------|----------------------------------|-------------------------------|
| Baseline ($\sigma = 1.5$, $\theta = 0.50$, No Frictions) | +[value]% | −[value]% | +[value]% | +[value]% |
| Low Substitution ($\sigma = 1.0$) | +[value]% | −[value]% | +[value]% | +[value]% |
| High Substitution ($\sigma = 2.0$) | +[value]% | −[value]% | +[value]% | +[value]% |
| Low Mfg. Budget Share ($\theta = 0.40$) | +[value]% | −[value]% | +[value]% | +[value]% |
| High Mfg. Budget Share ($\theta = 0.60$) | +[value]% | −[value]% | +[value]% | +[value]% |
| 10% Max Mfg. Employment Decline Constraint | +[value]% | −[value]% | +[value]% | +[value]% |

**Robustness Conclusion:** Aggregate utility gains are robust across all scenarios, ranging from [min] to [max]%. Distributional progressivity holds when $\sigma < 2.0$ and $\theta > 0.45$. Under binding labor mobility constraints, short-run unemployment reduces welfare gains by [value]%, and distributional impacts become [more/less] progressive.

The operational lesson is honest communication of uncertainty. No simulation model perfectly captures reality. Parameter sensitivity analysis bounds the range of plausible outcomes and identifies which qualitative conclusions are robust versus fragile. A finance minister must understand that the headline "+3% welfare gain" carries confidence intervals and depends on unobserved structural parameters. Robust findings—that liberalization generates aggregate gains and primarily benefits unskilled workers—inform the strategic direction, while fragile findings—the exact magnitude of gains or the top-decile outcome—require hedging in policy communication.

## Operational Reference Guide & Diagnostic Checklist

This reference guide consolidates the operational procedures, diagnostic criteria, and troubleshooting protocols developed across the three exercises. Use it as a quick-reference checklist when conducting development economics empirical work for policy clients, academic research, or institutional capacity building.

### Growth Accounting: Execution Checklist

**Data Requirements:**
- Real GDP at constant national prices (Penn World Table `rgdpna`)
- Capital stock at constant national prices (`rnna`)
- Total employment (`emp`)
- Human capital index (`hc`)
- Minimum 30-year time series for structural trend identification

**Calibration Parameters:**
- Capital share $\alpha$: default 0.35 for developing economies; validate using national accounts labor compensation data if available
- Sensitivity range: $\alpha \in [0.30, 0.40]$

**Diagnostic Tests:**
- TFP growth residual should exhibit lower variance than output growth (if not, check data quality or revisit $\alpha$ calibration)
- Decade-average TFP growth should lie in range $[-2\%, +4\%]$ for typical developing economies
- Negative TFP growth exceeding −1% annually over a decade signals severe measurement error, civil conflict, or economic collapse—investigate country-specific context

**Red Flags:**
- Erratic year-to-year TFP swings exceeding $\pm 10\%$: likely data quality issues in capital stock or employment series
- TFP growth that exactly offsets capital and labor contributions, leaving GDP growth unchanged: check for circular reasoning in data construction (capital stock often imputed from investment series using perpetual inventory method)

### Convergence Regression: Execution Checklist

**Data Requirements:**
- Initial (period $t-1$) and final (period $t$) GDP per capita for cross-country sample
- Investment-to-GDP ratio, population growth rate, schooling attainment, governance index
- Minimum sample size: 60 countries for cross-sectional estimation; 100+ for pooled regressions

**Specification Checks:**
- Convergence coefficient $\beta$ should be negative; typical range $[-0.04, -0.01]$
- First-stage F-statistic for IV regressions must exceed 10 (preferably >15)
- Residual plot against initial income should show no systematic pattern (U-shape or inverted-U indicates omitted non-linearities)

**Diagnostic Tests:**
- Exclude countries with civil wars, hyperinflation (>50% annually), or sudden natural resource discoveries during the sample period
- Re-estimate after exclusions: if $\beta$ changes sign or loses significance, result is not robust
- Compare OLS and IV estimates: IV coefficient should be more negative (reverse causation biases OLS toward zero)

**Red Flags:**
- Convergence coefficient positive and significant: indicates model misspecification or sample selection issues (e.g., only successful convergers included)
- $R^2 < 0.20$: conditioning variables explain little cross-country variation; consider adding institutional or geographic controls
- Large standard errors (t-statistic <1.5): insufficient sample size or excessive measurement error

### Threshold Regression: Execution Checklist

**Data Requirements:**
- Pooled cross-country panel with at least 150 country-period observations
- Initial income spanning at least 1.5 log points (roughly 4-fold income range)

**Estimation Procedure:**
1. Sort observations by initial log income
2. Test candidate thresholds at 5-percentile intervals from 20th to 80th percentile
3. For each candidate, split sample and estimate separate regressions
4. Record sum of squared residuals (SSR) for each threshold
5. Select threshold minimizing SSR
6. Bootstrap 1,000 samples to construct threshold confidence interval

**Diagnostic Tests:**
- Bootstrap 95% CI width should be <0.5 log points (less than 65% income difference); wider intervals indicate imprecise threshold estimate
- Test whether threshold disappears when adding institutional or geographic controls: if so, apparent income threshold is proxy for omitted variables

**Red Flags:**
- Threshold estimate at boundary of tested range (20th or 80th percentile): extend grid search
- Low-regime sample size <30 observations: insufficient power to detect regime-specific convergence coefficient
- Confidence interval spans full tested range: no credible threshold exists in data

### IV Estimation: Execution Checklist

**Data Requirements:**
- Endogenous regressor (institutions), outcome (income), instrument (settler mortality or alternative)
- Sample restricted to observations where instrument is plausibly exogenous (e.g., former colonies for settler mortality instrument)

**First-Stage Diagnostics:**
- Coefficient on instrument should be statistically significant (t-stat >3) with expected sign
- First-stage F-statistic must exceed 10; values <10 indicate weak instrument problems
- Partial $R^2$ of instrument (incremental variance explained beyond other regressors) should exceed 0.05

**Exclusion Restriction Tests:**
- Include geographic controls (latitude, malaria ecology, continent fixed effects) to address threats to validity
- Conduct overidentification test if multiple instruments available (Hansen J-statistic)
- Examine reduced-form relationship (instrument on outcome): should show significant relationship through endogenous regressor channel only

**Red Flags:**
- IV estimate has opposite sign from OLS: likely exclusion restriction violation
- IV standard errors >3 times OLS standard errors: weak instrument problem or severe measurement error
- First-stage coefficient loses significance when adding controls: instrument relevance is fragile

### AGE Simulation: Execution Checklist

**Model Calibration Requirements:**
- Production function parameters: elasticity of substitution $\sigma \in [1.0, 2.5]$, factor share parameters consistent with sectoral labor cost shares
- Preference parameters: expenditure shares $\theta$ consistent with household expenditure survey data
- Labor endowments: skilled/unskilled split matching economy's educational attainment distribution

**Numerical Solution Procedure:**
1. Set up equilibrium conditions as system of equations in factor prices and quantities
2. Define market-clearing error terms (supply minus demand for each factor and good)
3. Use non-linear solver to minimize sum of squared errors
4. Verify solution: all markets clear (errors <0.001), all quantities non-negative, zero-profit conditions hold

**Convergence Diagnostics:**
- Solver should converge within 100 iterations from reasonable starting values
- Solution should be unique: perturb initial guesses and verify solver reaches same equilibrium
- Shadow prices (Lagrange multipliers) should have sensible economic interpretation

**Red Flags:**
- Solver fails to converge: check for specification errors (e.g., Cobb-Douglas exponents not summing to 1)
- Corner solutions (zero output in a sector): model calibration is extreme; recalibrate parameters
- Negative prices or quantities in solution: logical error in equilibrium conditions or constraint specification

### Sensitivity Analysis: Execution Checklist

**Parameter Variation Protocol:**
1. Identify structural parameters with high uncertainty (elasticities, preference shares)
2. Define plausible range for each parameter (±50% around baseline calibration)
3. Re-simulate model for 5–7 values spanning each parameter's range
4. Record key outcomes: welfare metrics, distributional impacts, sectoral allocations
5. Plot outcomes against parameters to identify thresholds or non-linearities

**Robustness Criteria:**
- Qualitative result (sign of effect) should hold across 80% of parameter range
- Quantitative result (magnitude) should vary by less than factor of 2 across range
- If qualitative result flips, identify critical parameter threshold and assess whether threshold lies within empirical confidence interval

**Stress Test Scenarios:**
- Binding constraints (e.g., labor mobility limits, credit constraints)
- Extreme parameter values (high elasticities, low substitution)
- Alternative functional forms (Leontief vs. CES production, Stone-Geary vs. Cobb-Douglas preferences)

This diagnostic checklist operationalizes the empirical discipline required for credible development policy analysis. Every parameter choice, every specification test, and every robustness check documented here reflects hard-won lessons from practitioners who learned that technical rigor is the only reliable defense against wishful thinking, political pressure, and the seductive appeal of convenient but fragile conclusions. Execute these protocols systematically, document every deviation transparently, and communicate uncertainty honestly. This is the operational standard.
