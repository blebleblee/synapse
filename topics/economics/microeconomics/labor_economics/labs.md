# Operational Verification Labs: Labor Economics

## Objective & Operational Lab Setup

Labor economics dissects the microeconomic mechanisms governing wage determination, employment dynamics, human capital accumulation, and the institutional structures shaping labor market outcomes. This laboratory guide trains practitioners to execute empirical wage regression analysis, construct and calibrate static labor supply models, decompose compensating wage differentials, audit monopsony power in local labor markets, and simulate dynamic search-and-matching frameworks that replicate unemployment persistence and vacancy duration distributions observed in administrative data.

The operational objective is mastery of the core analytical toolkit: estimating Mincer earnings functions from cross-sectional household survey microdata, implementing calibrated labor supply elasticity experiments under varying tax schedules, constructing Oaxaca-Blinder decompositions to quantify wage gaps attributable to discrimination versus skill endowments, and running Monte Carlo simulations of the Mortensen-Pissarides search model to audit equilibrium unemployment rates under alternative separation shock distributions and matching function specifications.

**Analytical Environment Configuration**

Establish a dedicated research directory structure that separates raw data, cleaned datasets, regression output, calibration routines, and simulation code. Your working directory should contain subdirectories for `data/`, `scripts/`, `output/figures/`, and `output/tables/`. The primary computational toolkit combines spreadsheet-based calibration for static labor supply models, statistical software for wage regression and decomposition analysis, and either Python or R for dynamic simulation exercises. For regression work, practitioners typically employ Stata, R with the `fixest` or `lfe` packages for high-dimensional fixed effects, or Python with `statsmodels` and `linearmodels`. Dynamic search models require numerical solvers for value function iteration; MATLAB, Python with NumPy/SciPy, or Julia are standard choices.

**Data Acquisition and Preprocessing Protocol**

Labor economics research depends on high-quality microdata. For wage analysis, acquire the Current Population Survey (CPS) Merged Outgoing Rotation Group (MORG) files from IPUMS-CPS, which provide monthly cross-sections of wage and employment data with consistent coding. Download the Panel Study of Income Dynamics (PSID) for lifecycle earnings trajectories and human capital investment tracking. For European labor markets, obtain EU-SILC (Statistics on Income and Living Conditions) or national labor force surveys. Extract hourly wage observations, demographic characteristics (age, education, gender, race, marital status, region), occupation and industry codes, union membership status, and usual hours worked per week. 

Construct real hourly wages by deflating nominal wages using the Consumer Price Index (CPI) for urban wage earners, then taking natural logarithms to linearize the earnings distribution and facilitate regression interpretation. Impose standard sample restrictions: drop self-employed workers (whose earnings confound labor and capital income), restrict age to 25-64 to focus on prime working years, exclude hourly wages below half the federal minimum or above the 99th percentile to eliminate coding errors and extreme outliers, and limit the sample to individuals reporting positive usual hours worked. Recode education into years of schooling or categorical degree attainment (less than high school, high school diploma, some college, bachelor's degree, graduate degree). Generate potential experience as age minus years of schooling minus six, recognizing this proxy conflates actual labor market experience with time out of the labor force.

**Calibration and Simulation Software Stack**

For static labor supply models, construct a calibration spreadsheet with parameter input cells (wage rate, nonlabor income, preference parameters governing the elasticity of substitution between consumption and leisure), a column computing utility at each integer hour of labor supply from zero to eighty hours per week, and a lookup function identifying the utility-maximizing labor supply choice. Use Excel's Solver add-in or Google Sheets' built-in optimization to numerically solve for optimal hours when analytical solutions are unavailable under general CES or translog utility specifications.

Dynamic search-and-matching simulations require iterative value function solvers. In Python, use NumPy arrays to store value functions over discrete state spaces (employment status, match quality, duration), SciPy's `fsolve` or fixed-point iteration to solve Bellman equations, and Matplotlib for phase diagrams and impulse response plots. In R, the `quantecon` package provides pre-built routines for discrete dynamic programming, though manual implementation using vectorized operations in base R is often more transparent for pedagogical purposes. MATLAB remains the workhorse in academic labor economics for its matrix notation clarity and fast linear algebra libraries, though open-source alternatives have closed the performance gap.

**Reproducibility and Version Control**

Maintain a project repository under Git version control, committing raw data acquisition scripts, data cleaning code with inline comments documenting each filter and transformation, regression specification files, calibration spreadsheets with locked parameter cells, and simulation code with seeded random number generators. Tag each commit corresponding to a completed exercise, and maintain a `README.md` file documenting data sources, software versions, and replication instructions. This discipline ensures that every empirical result and calibration exercise can be audited and extended by collaborators or replicated by referees during peer review.

## Exercise 1: Foundational Practical Implementation

### Mincer Earnings Function Estimation and Human Capital Returns Decomposition

The Mincer earnings equation forms the empirical backbone of labor economics, quantifying the return to schooling and the lifecycle wage-experience profile. The canonical specification regresses log hourly wages on years of schooling, potential experience, and experience squared:

$$\ln(w_i) = \beta_0 + \beta_1 S_i + \beta_2 \text{Exp}_i + \beta_3 \text{Exp}_i^2 + \epsilon_i$$

where $w_i$ denotes the hourly wage for individual $i$, $S_i$ represents completed years of schooling, $\text{Exp}_i$ is potential experience (age minus schooling minus six), and $\epsilon_i$ captures unobserved heterogeneity in ability, motivation, and match quality. The coefficient $\beta_1$ estimates the percentage increase in wages per additional year of schooling, interpreted as the private return to education under the assumption that schooling does not directly affect productivity but signals pre-existing ability. The experience terms $\beta_2$ and $\beta_3$ trace out the concave lifecycle earnings profile, with wages rising rapidly early in the career as workers accumulate firm-specific human capital and occupational skills, then flattening as depreciation and obsolescence offset new learning.

**Data Preparation and Sample Construction**

Download the 2023 CPS MORG extract from IPUMS-CPS, selecting variables for hourly wage (if reported directly) or constructing it from weekly earnings divided by usual hours worked, age, educational attainment, sex, race, metropolitan status, and survey weights. Load the data into your statistical environment. In R, use the `ipumsr` package to read the fixed-width format DAT file along with the DDI codebook for automatic variable labeling. In Python, `pandas.read_fwf()` with column specifications from the IPUMS documentation achieves the same result. In Stata, the IPUMS extract includes a do-file that automatically defines variable labels and value labels.

Begin data cleaning by restricting the sample to wage and salary workers aged 25 to 64, excluding the self-employed, unpaid family workers, and those with allocated wages (imputed by Census Bureau hot-deck procedures). Drop observations with hourly wages below $4 or above $250 in nominal 2023 dollars, as these likely reflect coding errors or represent extreme outliers whose inclusion distorts regression estimates. Deflate nominal wages to constant 2023 dollars using the CPI-U-RS (Consumer Price Index for All Urban Consumers Research Series), then compute log wages. Recode education into years of schooling: less than high school diploma as 10 years, high school graduate as 12 years, some college as 14 years, bachelor's degree as 16 years, master's degree as 18 years, professional degree as 19 years, and doctoral degree as 20 years. Construct potential experience as age minus years of schooling minus six, and generate experience squared.

**Baseline OLS Regression Specification**

Estimate the Mincer equation using ordinary least squares with heteroskedasticity-robust standard errors clustered at the state level to account for correlated wage shocks within regional labor markets. In Stata, the command sequence is:

```stata
use cps_morg_2023_clean.dta, clear
gen log_wage = ln(hourly_wage_real)
gen exper = age - educ_years - 6
gen exper_sq = exper^2
regress log_wage educ_years exper exper_sq [aweight=wtfinl], vce(cluster statefip)
outreg2 using mincer_baseline.tex, replace ctitle("Baseline") label dec(3)
```

In R with `fixest`:

```r
library(fixest)
library(haven)
data <- read_dta("cps_morg_2023_clean.dta")
data$log_wage <- log(data$hourly_wage_real)
data$exper <- data$age - data$educ_years - 6
data$exper_sq <- data$exper^2
baseline <- feols(log_wage ~ educ_years + exper + exper_sq, 
                  data = data, weights = ~wtfinl, 
                  cluster = ~statefip)
etable(baseline, file = "mincer_baseline.tex", replace = TRUE)
```

In Python with `linearmodels`:

```python
import pandas as pd
from linearmodels.iv import IV2SLS
import numpy as np
data = pd.read_stata("cps_morg_2023_clean.dta")
data['log_wage'] = np.log(data['hourly_wage_real'])
data['exper'] = data['age'] - data['educ_years'] - 6
data['exper_sq'] = data['exper']**2
mod = IV2SLS(dependent=data['log_wage'], 
             exog=data[['educ_years', 'exper', 'exper_sq']], 
             weights=data['wtfinl']).fit(cov_type='clustered', clusters=data['statefip'])
print(mod.summary)
```

**Interpreting the Return to Schooling**

The estimated coefficient on years of schooling typically ranges from 0.08 to 0.12 in U.S. data, implying an 8-12 percent wage premium per additional year of education. This return conflates the causal effect of human capital accumulation (skills directly acquired through schooling) with ability bias (high-ability individuals select into more schooling and would have earned higher wages regardless) and signaling (employers use educational credentials to screen workers). To isolate the causal return, researchers employ instrumental variables such as compulsory schooling law changes, distance to college, or quarter of birth (exploiting school entry age rules), though each instrument carries its own identifying assumptions and local average treatment effect interpretation.

The experience profile coefficients reveal the timing of human capital investment over the lifecycle. A positive $\beta_2$ and negative $\beta_3$ generate the characteristic concave age-earnings profile: wages rise steeply in the first decade of work as individuals acquire occupation-specific skills, then the growth rate declines as learning slows and depreciation accelerates. The turning point occurs at $\text{Exp}^* = -\beta_2 / (2\beta_3)$, typically around 25-30 years of experience, after which wage growth stagnates or even reverses as technological obsolescence dominates incremental learning.

**Extended Specifications with Demographic Controls and Fixed Effects**

Augment the baseline Mincer equation with binary indicators for female, nonwhite, married, union member, metropolitan residence, and region fixed effects (Northeast, Midwest, South, West). These controls absorb systematic wage differentials correlated with observable characteristics, tightening the conditional interpretation of the schooling coefficient. Add occupation fixed effects (using two-digit SOC codes) and industry fixed effects (using two-digit NAICS codes) to control for sorting across sectors with different skill intensity and rent-sharing arrangements. In Stata:

```stata
regress log_wage educ_years exper exper_sq i.female i.nonwhite i.married ///
    i.union i.metro i.region i.occ2d i.ind2d [aweight=wtfinl], vce(cluster statefip)
outreg2 using mincer_extended.tex, append ctitle("Extended") label dec(3)
```

In R:

```r
extended <- feols(log_wage ~ educ_years + exper + exper_sq + 
                  female + nonwhite + married + union + metro | region + occ2d + ind2d, 
                  data = data, weights = ~wtfinl, cluster = ~statefip)
etable(baseline, extended, file = "mincer_comparison.tex", replace = TRUE)
```

Compare the return to schooling estimate across specifications. The coefficient typically attenuates by 1-2 percentage points when occupation and industry fixed effects are included, as these controls capture part of the schooling premium that operates through sorting into high-wage sectors. This decomposition highlights that education raises wages both by increasing individual productivity (within-occupation effect) and by enabling access to better-paying occupations and industries (between-occupation selection effect).

**Subgroup Heterogeneity and Interaction Effects**

Estimate separate Mincer equations for men and women, and for college graduates versus high school graduates, to audit heterogeneity in the return to schooling across demographic groups and credential levels. Generate interaction terms between schooling and demographic indicators, then test for equality of coefficients using F-tests or Wald tests on the interactions. In Stata:

```stata
regress log_wage c.educ_years##i.female exper exper_sq [aweight=wtfinl], vce(cluster statefip)
margins, dydx(educ_years) at(female=(0 1))
marginsplot, title("Return to Schooling by Gender")
```

In R with `marginaleffects`:

```r
library(marginaleffects)
interact_mod <- feols(log_wage ~ educ_years*female + exper + exper_sq, 
                      data = data, weights = ~wtfinl, cluster = ~statefip)
avg_slopes(interact_mod, variables = "educ_years", by = "female")
plot_slopes(interact_mod, variables = "educ_years", condition = "female")
```

Empirical patterns reveal that the return to schooling is higher for women than men in recent U.S. data, reflecting both demand-side factors (gender-specific technological change favoring cognitive over physical tasks) and supply-side composition effects (women's educational attainment has surpassed men's, compressing the distribution and raising the marginal return). The return to a bachelor's degree relative to a high school diploma (the "college premium") has risen from approximately 40 percent in 1980 to 80 percent by 2020, driven by skill-biased technological change and globalization pressures that devalue routine manual and cognitive tasks while amplifying returns to abstract problem-solving and interpersonal communication skills.

**Diagnostic Audit: Specification Tests and Robustness Checks**

Assess regression diagnostics to validate the empirical strategy. Plot residuals against fitted values to check for heteroskedasticity and nonlinear patterns unaccounted for by the quadratic experience specification. Construct quantile-quantile plots of residuals against a normal distribution to detect heavy tails or outliers. Test for omitted variable bias by comparing R-squared values and coefficient stability across nested specifications: if the return to schooling estimate is sensitive to inclusion of occupation or industry controls, this signals that unobserved ability or sorting mechanisms confound the baseline estimate.

Run a placebo test by regressing log wages on years of schooling, experience, and a randomly generated "fake education" variable. The coefficient on fake education should be statistically insignificant and close to zero, confirming that the observed return to actual schooling is not an artifact of specification search or data mining. Implement a leave-one-out cross-validation routine, iteratively dropping each state from the sample and re-estimating the Mincer equation, then plotting the distribution of state-specific schooling coefficients to assess parameter stability across regional labor markets.

Finally, address measurement error in potential experience. Actual labor market experience diverges from potential experience for individuals with employment gaps due to childrearing, disability, or unemployment spells. If longitudinal data are available (e.g., PSID or NLSY79), construct actual work experience by summing years employed, and compare the estimated experience profile to the potential experience baseline. Measurement error in experience attenuates the estimated experience coefficients toward zero, biasing downward the implied lifecycle earnings growth rate.

## Exercise 2: Parameter Variation & Empirical Analysis

### Static Labor Supply Calibration and Tax Policy Elasticity Experiments

Labor supply theory derives hours worked from the individual's utility maximization problem trading off consumption and leisure subject to a time constraint and a budget constraint shaped by wage rates, nonlabor income, and tax schedules. The static model abstracts from intertemporal savings decisions and human capital investment, focusing on the contemporaneous choice of hours worked conditional on a fixed wage. Calibrating this model and simulating labor supply responses to tax reforms trains practitioners in numerical optimization, comparative statics analysis, and translating structural parameters into policy-relevant elasticities.

**Theoretical Framework and Elasticity Definitions**

The household maximizes a utility function $U(C, L)$ defined over consumption $C$ and leisure $L$, subject to the budget constraint $C = w(T - L) + Y$, where $w$ is the hourly wage, $T$ is total time endowment (normalized to 168 hours per week or 5,840 hours per year), and $Y$ is nonlabor income (asset returns, transfers). The first-order condition equates the marginal rate of substitution between consumption and leisure to the wage:

$$\frac{U_L}{U_C} = w$$

This condition implicitly defines labor supply $H = T - L$ as a function of the wage and nonlabor income: $H = H(w, Y)$. The uncompensated (Marshallian) wage elasticity of labor supply measures the percentage change in hours worked in response to a one percent increase in the wage, holding nonlabor income constant:

$$\varepsilon_H^w = \frac{\partial H}{\partial w} \frac{w}{H}$$

This elasticity decomposes into a substitution effect (higher wages increase the opportunity cost of leisure, inducing more work) and an income effect (higher wages increase full income, inducing more leisure if leisure is a normal good). The compensated (Hicksian) wage elasticity isolates the substitution effect by adjusting nonlabor income to hold utility constant, and is always positive. The income elasticity measures the response of labor supply to nonlabor income:

$$\varepsilon_H^Y = \frac{\partial H}{\partial Y} \frac{Y}{H}$$

For prime-age males, empirical estimates place $\varepsilon_H^w$ near zero (ranging from -0.1 to 0.1), reflecting offsetting substitution and income effects, while for married women, $\varepsilon_H^w$ ranges from 0.2 to 0.5, as labor force participation margins dominate hours adjustments. These elasticities govern the efficiency costs of taxation and the labor supply responses to transfer program phase-outs.

**Calibration Procedure with CES Utility Specification**

Adopt a constant elasticity of substitution (CES) utility function:

$$U(C, L) = \left[ \alpha C^{\rho} + (1 - \alpha) L^{\rho} \right]^{1/\rho}$$

where $\alpha \in (0, 1)$ is the consumption weight parameter, and $\rho \in (-\infty, 1)$ governs the elasticity of substitution $\sigma = 1 / (1 - \rho)$. When $\rho = 0$, the utility function reduces to Cobb-Douglas $U(C, L) = C^\alpha L^{1-\alpha}$. For $\rho < 0$, consumption and leisure are complements; for $\rho > 0$, they are substitutes.

Set the time endowment to $T = 5,840$ hours per year (16 hours per day times 365 days, assuming 8 hours daily for sleep and personal care are not discretionary). Choose a baseline wage $w = 25$ dollars per hour (near the median U.S. hourly wage for prime-age workers) and nonlabor income $Y = 5,000$ dollars per year (representing modest asset income or transfer receipts). Initialize preference parameters to $\alpha = 0.5$ and $\rho = -0.5$ (implying an elasticity of substitution $\sigma = 0.67$, consistent with empirical estimates suggesting consumption and leisure are weak complements).

Construct a calibration spreadsheet with the following columns: hours worked $H$ (ranging from 0 to 4,000 in increments of 10), implied leisure $L = T - H$, consumption $C = wH + Y$, utility $U(C, L)$ computed using the CES formula, and marginal utility of leisure $U_L$ and marginal utility of consumption $U_C$ computed via numerical derivatives (forward difference: $U_L \approx [U(C, L+1) - U(C, L)] / 1$). Identify the utility-maximizing hours by finding the row with the maximum utility value.

**Spreadsheet Implementation in Excel**

In Excel, create a sheet with cells A1:B5 containing parameter labels and values:

```text
A1: w (wage)          B1: 25
A2: Y (nonlabor inc)  B2: 5000
A3: T (time endow)    B3: 5840
A4: alpha             B4: 0.5
A5: rho               B5: -0.5
```

In column A starting at row 7, generate hours worked from 0 to 4000 in steps of 10:

```text
A7: 0
A8: =A7+10
[drag down to row 407]
```

In column B, compute leisure:

```text
B7: =$B$3 - A7
[drag down]
```

In column C, compute consumption:

```text
C7: =$B$1*A7 + $B$2
[drag down]
```

In column D, compute CES utility:

```text
D7: =($B$4*C7^$B$5 + (1-$B$4)*B7^$B$5)^(1/$B$5)
[drag down]
```

Identify the maximum utility row using Excel's `MAX` function and `INDEX-MATCH`:

```text
F7: =MAX(D7:D407)
F8: =INDEX(A7:A407, MATCH(F7, D7:D407, 0))
```

Cell F8 now displays the optimal hours worked. For the baseline calibration ($w=25$, $Y=5000$, $\alpha=0.5$, $\rho=-0.5$), optimal hours are approximately 2,080 hours per year (40 hours per week times 52 weeks), which aligns with full-time employment norms.

**Comparative Statics: Wage Variation Elasticity Experiment**

Compute the labor supply response to a 10 percent wage increase by changing cell B1 from 25 to 27.5 and recording the new optimal hours from cell F8. Construct a data table with wage values ranging from 15 to 40 in increments of 1, and use Excel's Data Table feature (Data → What-If Analysis → Data Table) to populate optimal hours for each wage level. Plot the labor supply curve $H(w)$ with wage on the horizontal axis and hours on the vertical axis.

Calculate the uncompensated wage elasticity numerically:

$$\varepsilon_H^w = \frac{H(27.5) - H(25)}{H(25)} \div \frac{27.5 - 25}{25} = \frac{\Delta H / H}{\Delta w / w}$$

For the CES calibration with $\rho = -0.5$ and $\alpha = 0.5$, the uncompensated elasticity typically falls in the range 0.1 to 0.3, indicating a modestly positive labor supply response driven by a substitution effect that dominates the income effect. Repeat the calculation at different points along the wage distribution to assess elasticity heterogeneity: elasticities are larger at low wage levels (where income effects are minimal) and smaller at high wage levels (where income effects are stronger).

**Income Elasticity and Transfer Program Simulation**

Increase nonlabor income from $5,000 to $10,000 and record the change in optimal hours. The income elasticity is:

$$\varepsilon_H^Y = \frac{H(10000) - H(5000)}{H(5000)} \div \frac{10000 - 5000}{5000}$$

Empirical estimates suggest $\varepsilon_H^Y$ ranges from -0.05 to -0.15 for prime-age males (leisure is a normal good, so higher nonlabor income reduces labor supply) and -0.3 to -0.5 for married women. If calibrated elasticities diverge from empirical targets, adjust preference parameters $\alpha$ and $\rho$ iteratively until the model replicates observed elasticities. This calibration-to-targets approach ensures the model's policy predictions rest on empirically grounded behavioral responses.

Simulate the labor supply impact of a universal basic income (UBI) policy that provides $Y_{UBI} = 12,000$ dollars per year to all households. Compute the predicted reduction in aggregate hours worked by multiplying the individual-level hour reduction by the labor force size, then scale by the income elasticity. Compare the efficiency cost (deadweight loss from reduced labor supply) to the equity gain (reduced income inequality and poverty alleviation) using a social welfare function that trades off mean consumption against consumption inequality.

**Tax Wedge Analysis and Marginal Tax Rate Experiments**

Introduce a proportional income tax at rate $\tau$, modifying the budget constraint to $C = (1 - \tau) w H + Y$. The after-tax wage is $w_{net} = (1 - \tau) w$, and the individual optimizes against the net wage. Calibrate the model with a baseline tax rate $\tau = 0.25$ (the average effective marginal tax rate faced by median earners after federal and state income taxes and payroll taxes). Compute optimal hours at $\tau = 0.25$, then vary the tax rate from 0 to 0.5 in increments of 0.05, recording optimal hours at each rate.

Plot the Laffer curve relating tax revenue $R = \tau w H(\tau)$ to the tax rate $\tau$. For low tax rates, revenue rises with $\tau$ despite modest reductions in $H$. Beyond a critical rate (the revenue-maximizing tax rate), further increases in $\tau$ reduce hours worked so sharply that revenue declines. For the CES calibration with $\varepsilon_H^w = 0.2$, the revenue-maximizing rate typically falls between 50 and 70 percent, far above observed statutory rates, implying that current U.S. tax policy sits on the upward-sloping portion of the Laffer curve where rate increases raise revenue.

Extend the analysis to a progressive tax system with marginal rate brackets. Implement the 2023 federal income tax schedule with brackets at 10%, 12%, 22%, 24%, 32%, 35%, and 37%. For each integer value of hours worked, compute taxable income $wH$, calculate total tax liability by summing tax owed in each bracket, and derive consumption as after-tax income plus nonlabor income. Recompute utility over the hours grid accounting for the nonlinear budget constraint introduced by bracket kinks. Identify the optimal hours by maximizing utility subject to the progressive tax schedule.

Document the labor supply distortion induced by the progressive system relative to a flat tax with the same revenue yield. The progressive system generates kinks in the budget constraint at bracket thresholds, potentially bunching hours worked just below these thresholds to avoid higher marginal rates. Empirical evidence of bunching behavior is mixed: salaried workers exhibit minimal bunching due to institutional constraints on hours flexibility, while self-employed and gig workers show stronger responses at salient kink points such as the EITC phase-out region and Social Security taxable maximum.

**Robustness Checks: Alternative Utility Specifications**

Repeat the calibration exercises using a Cobb-Douglas utility function $U(C, L) = C^\alpha L^{1-\alpha}$, which imposes an elasticity of substitution equal to one. The Cobb-Douglas specification generates analytical solutions for optimal hours:

$$H^* = \frac{\alpha}{w} \left( wT + Y \right) - \frac{Y}{w}$$

The uncompensated wage elasticity under Cobb-Douglas is:

$$\varepsilon_H^w = \frac{wT}{wT + Y}$$

which approaches one as nonlabor income $Y$ approaches zero and declines toward zero as $Y$ grows large. Compare the Cobb-Douglas wage elasticity to the CES calibration, and assess whether qualitative policy predictions (direction of labor supply response to tax changes) are robust to functional form assumptions.

Test sensitivity to the consumption weight parameter $\alpha$ by varying it from 0.3 to 0.7. Lower $\alpha$ (higher weight on leisure) produces a downward-sloping labor supply curve where income effects dominate, while higher $\alpha$ (higher weight on consumption) generates an upward-sloping curve with strong substitution effects. Document the $\alpha$ threshold that produces a zero wage elasticity, corresponding to the empirical pattern observed for prime-age males.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Oaxaca-Blinder Wage Gap Decomposition and Monopsony Power Diagnostics

Labor market institutions, discrimination, and market power distort wage determination away from the competitive benchmark where wages equal marginal productivity. This exercise trains practitioners to decompose observed wage differentials into components attributable to differences in productive characteristics (skill endowments, experience, education) versus differences in returns to characteristics (discrimination, differential bargaining power, occupational segregation). Additionally, auditing monopsony power—employer wage-setting authority arising from labor market concentration or search frictions—requires empirical techniques that estimate the elasticity of labor supply facing individual firms and test for markdown of wages below marginal revenue product.

**Oaxaca-Blinder Decomposition Methodology**

The Oaxaca-Blinder decomposition partitions the mean wage gap between two groups (e.g., men and women, white and Black workers) into an "explained" component due to differences in observable characteristics and an "unexplained" component attributed to differences in coefficients (returns to characteristics). Estimate separate Mincer equations for each group:

$$\ln(w_A) = X_A \beta_A + \epsilon_A$$
$$\ln(w_B) = X_B \beta_B + \epsilon_B$$

where $X$ is a vector of covariates (education, experience, occupation, industry), and $\beta$ captures the returns to these characteristics. The mean log wage gap is:

$$\overline{\ln(w_A)} - \overline{\ln(w_B)} = (\overline{X_A} - \overline{X_B}) \beta_B + \overline{X_A} (\beta_A - \beta_B)$$

The first term $(\overline{X_A} - \overline{X_B}) \beta_B$ is the "explained" component: the wage gap that would persist if group A had the same characteristics as group B but group B's returns. The second term $\overline{X_A} (\beta_A - \beta_B)$ is the "unexplained" component: the gap due to differential returns, often interpreted as discrimination or unmeasured skill differences. Alternative decompositions weight the unexplained component by $\beta_A$ or a pooled coefficient $\beta^*$, generating different allocations of the interaction term $(\overline{X_A} - \overline{X_B})(\beta_A - \beta_B)$.

**Empirical Implementation: Gender Wage Gap**

Using the CPS MORG data from Exercise 1, subset the sample into male and female workers. Estimate Mincer equations separately for each group, including the same covariates: education, experience, experience squared, race, marital status, union membership, metropolitan status, region, occupation, and industry fixed effects. Store the estimated coefficients and sample mean covariates for each group. In Stata:

```stata
use cps_morg_2023_clean.dta, clear
gen log_wage = ln(hourly_wage_real)
gen exper = age - educ_years - 6
gen exper_sq = exper^2

* Estimate separate regressions
regress log_wage educ_years exper exper_sq i.nonwhite i.married i.union i.metro ///
    i.region i.occ2d i.ind2d if female==0 [aweight=wtfinl], vce(robust)
estimates store male_reg

regress log_wage educ_years exper exper_sq i.nonwhite i.married i.union i.metro ///
    i.region i.occ2d i.ind2d if female==1 [aweight=wtfinl], vce(robust)
estimates store female_reg

* Oaxaca-Blinder decomposition
oaxaca log_wage educ_years exper exper_sq i.nonwhite i.married i.union i.metro ///
    i.region i.occ2d i.ind2d [aweight=wtfinl], by(female) weight(1)
```

The `oaxaca` command in Stata automatically computes the threefold decomposition, reporting the explained, unexplained, and interaction components. In R, the `oaxaca` package provides similar functionality:

```r
library(oaxaca)
data_male <- subset(data, female == 0)
data_female <- subset(data, female == 1)

results <- oaxaca(log_wage ~ educ_years + exper + exper_sq + nonwhite + married + 
                  union + metro + region + occ2d + ind2d | female, 
                  data = data, weights = "wtfinl")
plot(results)
summary(results)
```

**Interpreting Decomposition Results**

Typical findings in U.S. data reveal that women earn approximately 17-20 percent less than men in log wage terms (corresponding to an 18-22 percent gap in levels). The explained component attributable to differences in education, experience, occupation, and industry accounts for 30-50 percent of the gap, leaving 50-70 percent unexplained. This unexplained component has declined from approximately 25 percent in 1980 to 12-15 percent in 2020, reflecting reduced occupational segregation, enforcement of equal pay legislation, and shifting social norms.

Decompose the explained component into contributions from specific covariates by computing $(\overline{X_{jA}} - \overline{X_{jB}}) \beta_{jB}$ for each covariate $j$. Experience differences explain a substantial share, as women have lower average potential experience due to career interruptions for childrearing. Occupational and industry differences explain another large share, as women remain concentrated in lower-paying sectors (education, healthcare, retail) and underrepresented in high-wage fields (engineering, finance, executive management). Educational differences contribute minimally, as women's educational attainment now exceeds men's.

The unexplained component captures discrimination, unmeasured ability differences, compensating differentials for job characteristics (flexibility, physical demands), and differential negotiation outcomes. Taste-based discrimination (Becker's model where employers, customers, or coworkers have prejudiced preferences) generates wage gaps that should erode under competitive pressure as nondiscriminating firms gain cost advantages. Statistical discrimination (employers use group averages to proxy for unobserved individual productivity) persists even in competitive markets if skill signals are noisy. Empirical evidence of audit studies (sending matched resumes with randomized names) documents persistent callback rate gaps, supporting the presence of taste-based or statistical discrimination in hiring.

**Boundary Failure Diagnostic: Unexplained Component Persistence**

If the unexplained component remains large even after controlling for detailed occupation and industry, this signals either omitted variable bias (unobserved productivity differences systematically correlated with group membership) or residual discrimination operating within narrowly defined job cells. Test for within-job discrimination by estimating the decomposition separately within two-digit occupation-industry cells, then aggregating the cell-specific unexplained components weighted by employment shares. If within-cell gaps persist, discrimination or unobserved skill differences operate at finer granularity than observable occupation codes capture.

Run a falsification test by constructing a "pseudo-gap" between workers with odd versus even birth months, a characteristic unrelated to productivity. Estimate the Oaxaca-Blinder decomposition for this pseudo-gap. The unexplained component should be statistically insignificant and close to zero. If a large unexplained component emerges for the pseudo-gap, this indicates specification error or overfitting, invalidating the interpretation of the unexplained component as discrimination in the actual gender or race gap analysis.

**Monopsony Power Estimation: Firm-Level Labor Supply Elasticity**

Monopsony arises when firms face upward-sloping labor supply curves, granting them wage-setting power. In a monopsonistic labor market, firms set wages below the competitive level, hiring fewer workers and extracting rents. The markdown of wages below marginal revenue product is inversely proportional to the firm-level labor supply elasticity $\varepsilon^{firm}$:

$$\frac{w}{MRP} = \frac{\varepsilon^{firm}}{\varepsilon^{firm} + 1}$$

where $MRP$ denotes the marginal revenue product of labor. Estimating $\varepsilon^{firm}$ requires microdata linking workers to firms and observing wage and employment responses to firm-specific shocks.

Use linked employer-employee data (LEED) such as the Longitudinal Employer Household Dynamics (LEHD) or administrative tax records matching workers to establishments. Estimate the firm-level labor supply elasticity by regressing the log number of employees at firm $f$ on the log average wage, controlling for firm fixed effects and time trends:

$$\ln(N_{ft}) = \varepsilon^{firm} \ln(w_{ft}) + \alpha_f + \lambda_t + \epsilon_{ft}$$

The OLS estimate of $\varepsilon^{firm}$ is biased upward due to reverse causality: firms that experience positive productivity shocks increase both wages and employment, generating a spurious positive correlation. Instrument the wage using regional labor market shocks (e.g., industry-specific wage growth in other geographic areas) or policy-induced minimum wage changes that shift the wage floor exogenously. In the first-stage regression, predict firm-level wages using the instrument; in the second stage, regress log employment on instrumented log wages.

**Simulation Protocol for Monopsony Markdown Calculation**

For firms in concentrated labor markets (high local employer concentration measured by Herfindahl-Hirschman Index of employment shares), estimate $\varepsilon^{firm}$ near 1.0, implying a markdown of wages below marginal product of approximately 50 percent. For firms in competitive urban labor markets, $\varepsilon^{firm}$ exceeds 5.0, implying markdowns below 17 percent. Compute the welfare loss from monopsony as the deadweight loss triangle:

$$DWL = \frac{1}{2} (MRP - w) (N^* - N^m)$$

where $N^*$ is competitive employment and $N^m$ is monopsonistic employment. Calibrate $MRP$ by estimating firm-level production functions, regressing log output on log labor and capital inputs, and recovering the labor output elasticity. The marginal product of labor is the output elasticity times average revenue product.

**Recovery Protocol: Policy Interventions to Restore Competitive Outcomes**

Test the impact of minimum wage increases on employment in monopsonistic labor markets. Theory predicts that binding minimum wages compress the markdown, raising wages and potentially increasing employment if the initial wage was below the monopsonistic optimum. Use a difference-in-differences design exploiting state-level minimum wage variation: compare employment changes in low-wage industries in states that raised minimum wages versus adjacent states that did not. Estimate the effect using a two-way fixed effects regression:

$$\ln(N_{ist}) = \beta \cdot \text{MinWage}_{st} + \alpha_i + \lambda_t + \epsilon_{ist}$$

where $i$ indexes industries, $s$ indexes states, and $t$ indexes time. A positive $\beta$ supports the monopsony model; a negative $\beta$ supports the competitive model where minimum wages reduce employment. Meta-analyses of minimum wage studies find small negative employment effects (elasticity of -0.1) for teens and negligible effects for prime-age workers, consistent with moderate monopsony power in low-wage labor markets.

Simulate the employment and welfare effects of policies that reduce labor market concentration: merger prohibitions, non-compete clause bans, and portability of occupational licenses. Non-compete clauses reduce worker mobility, steepening the firm-level labor supply curve and increasing monopsony power. Empirical evidence from state-level non-compete enforcement variation shows that relaxing enforcement raises wages by 3-8 percent in affected occupations without reducing employment, consistent with reductions in monopsony markdown.

**Stress Test: Search Frictions and Dynamic Monopsony**

Monopsony power arises not only from spatial concentration but also from search frictions: when workers face costly job search, firms can pay wages below marginal product without losing all workers. Estimate the elasticity of separations (quits) with respect to wages using linked employer-employee data:

$$\ln(q_{ft}) = -\varepsilon^{sep} \ln(w_{ft}) + \alpha_f + \lambda_t + \epsilon_{ft}$$

where $q_{ft}$ is the quarterly separation rate. The separation elasticity $\varepsilon^{sep}$ measures the responsiveness of worker turnover to wage changes, providing an alternative estimate of monopsony power: $\varepsilon^{firm} = \varepsilon^{sep}$. Empirical estimates of $\varepsilon^{sep}$ range from 1.5 to 4.0, confirming moderate monopsony power in U.S. labor markets.

Incorporate these frictions into a dynamic search-and-matching model. Simulate worker flows using a discrete-time version of the Mortensen-Pissarides framework: workers transition between employment, unemployment, and out of the labor force each period according to exogenous separation rates $\delta$ and endogenous job-finding rates $f(\theta)$ that depend on labor market tightness $\theta = v / u$ (vacancies divided by unemployment). Firms post vacancies at cost $c$ per period, matching with unemployed workers according to a Cobb-Douglas matching function:

$$m(u, v) = A u^\alpha v^{1-\alpha}$$

The job-finding rate is $f(\theta) = m / u = A \theta^{1-\alpha}$, and the vacancy-filling rate is $q(\theta) = m / v = A \theta^{-\alpha}$. In steady state, flows into and out of unemployment balance:

$$\delta (1 - u) = f(\theta) u$$

Solve for equilibrium unemployment $u^*$ and tightness $\theta^*$. Calibrate parameters to match U.S. labor market statistics: monthly separation rate $\delta = 0.03$, job-finding rate $f = 0.45$, matching function elasticity $\alpha = 0.5$, and vacancy posting cost $c$ set to replicate observed vacancy-unemployment ratios. Simulate the model's response to a negative productivity shock that reduces match surplus, showing how unemployment rises and vacancies fall during recessions, tracing out the Beveridge curve (negative relationship between unemployment and vacancies).

**Empirical Verification Against JOLTS Data**

Compare simulated vacancy and unemployment dynamics to observed data from the Job Openings and Labor Turnover Survey (JOLTS). Download monthly JOLTS data on job openings, hires, and separations from the Bureau of Labor Statistics. Construct the vacancy-unemployment ratio and the job-finding rate (hires divided by unemployment), then plot the model-implied Beveridge curve against the empirical curve. Assess whether the calibrated model replicates the outward shift in the Beveridge curve observed post-2008 financial crisis and post-2020 pandemic, which signals persistent mismatch between worker skills and job requirements or geographic mobility barriers.

Run counterfactual simulations reducing search costs (e.g., expanding internet job boards, subsidizing worker relocation) or increasing match efficiency (e.g., training programs that reduce skill mismatch). A 20 percent reduction in search costs (modeled as a 20 percent increase in matching function efficiency $A$) raises the job-finding rate, lowers equilibrium unemployment by 1-2 percentage points, and increases steady-state employment. These exercises quantify the welfare gains from policies that reduce labor market frictions and restore competitive wage-setting.

## Operational Reference Guide & Diagnostic Checklist

### Data Sources and Quality Audits

**Primary Microdata Repositories**

Current Population Survey (CPS): Monthly cross-sectional household survey administered by the Census Bureau and Bureau of Labor Statistics. The CPS Merged Outgoing Rotation Group (MORG) provides nationally representative wage and employment data with sample sizes exceeding 200,000 observations annually. Access via IPUMS-CPS with consistent variable coding across decades. Strengths: large sample, high-frequency (monthly), comprehensive demographic and labor market variables. Limitations: cross-sectional (no longitudinal tracking), potential experience is a noisy proxy for actual experience, self-reported wages may suffer recall bias.

Panel Study of Income Dynamics (PSID): Longitudinal survey tracking U.S. families since 1968, administered biennially since 1997. Provides lifecycle earnings trajectories, wealth accumulation, family formation, and intergenerational linkages. Strengths: long panel dimension enables fixed effects estimation controlling for unobserved individual heterogeneity, wealth and consumption data permit lifecycle modeling. Limitations: smaller sample (approximately 9,000 families), attrition bias, biennial frequency misses high-frequency labor market transitions.

National Longitudinal Surveys (NLSY79, NLSY97): Cohort studies following individuals from youth through adulthood. NLSY79 tracks individuals born 1957-1964; NLSY97 tracks individuals born 1980-1984. Includes cognitive test scores (AFQT), detailed work history, human capital investment decisions. Strengths: rich skill measures enable controlling for ability bias in return-to-schooling estimates, high-frequency interviews capture job-to-job transitions. Limitations: cohort-specific, aging panels lose relevance for current labor market conditions.

Linked Employer-Employee Data (LEED): Administrative datasets linking workers to firms, typically constructed from unemployment insurance wage records or tax filings. Examples include the Longitudinal Employer-Household Dynamics (LEHD) and various European national administrative registers. Strengths: census coverage of formal employment, precise measurement of firm-level wages and turnover, no attrition or reporting error. Limitations: restricted data access requiring secure enclaves, earnings censored at Social Security taxable maximum, self-employed and informal sector workers excluded.

**Data Quality Diagnostics**

Before estimating wage regressions or calibrating labor supply models, implement the following data quality checks. Inspect univariate distributions of key variables: plot histograms of log wages, experience, and hours worked, flagging mass points, gaps, or outliers. Mass points at round numbers (wages of $10, $15, $20 per hour) suggest heaping or reporting coarseness. Gaps at institutional thresholds (minimum wage) indicate binding constraints or censoring. Apply the Kolmogorov-Smirnov test comparing the empirical wage distribution to a log-normal benchmark; significant deviations signal fat tails or excess kurtosis requiring robust regression techniques or quantile regression.

Cross-tabulate wage observations by data source: wages reported as hourly versus computed from weekly earnings divided by hours may diverge due to overtime premia or misreported hours. Workers reporting hourly wages directly exhibit lower variance and fewer outliers. When constructing hourly wages from weekly earnings, trim observations with reported usual hours below 20 or above 80 per week, as extreme values likely reflect part-time, gig, or multiple-job arrangements that violate the static labor supply model's assumptions.

Assess item nonresponse and imputation flags. CPS allocates missing wage values using hot-deck imputation based on cell means stratified by age, education, gender, and occupation. Allocated wage observations are flagged with an allocation dummy variable; exclude these observations or include the allocation flag as a control to avoid attenuating regression estimates. Typical allocation rates range from 20-30 percent in CPS wage samples, so excluding allocated values reduces sample size substantially but improves precision.

Test for outliers using robust regression diagnostics: estimate the baseline Mincer equation, compute studentized residuals, and flag observations with absolute residuals exceeding three standard deviations. Reestimate the model excluding flagged outliers, comparing coefficient stability. If return-to-schooling estimates shift by more than 0.01 (one percentage point), investigate flagged observations for data entry errors or sample composition anomalies (e.g., celebrity earnings, top executives with stock option compensation).

### Regression Specification Decision Tree

**Choosing the Wage Functional Form**

Linear wage specification $w_i$ versus log wage $\ln(w_i)$: The log specification is preferred because wage distributions are highly right-skewed, and the log transformation achieves approximate normality, satisfying OLS error assumptions. Coefficients in the log specification have convenient percentage-change interpretations: $\beta_1 \times 100$ percent wage increase per year of schooling. Use the Box-Cox test to formally assess the optimal transformation parameter; typical estimates confirm that $\lambda = 0$ (log transformation) dominates.

Experience functional form: The quadratic $\beta_2 \text{Exp} + \beta_3 \text{Exp}^2$ specification is the baseline. Test for higher-order polynomials (cubic, quartic) using F-tests on joint significance of additional terms. Alternatives include piecewise linear splines with knots at 10, 20, and 30 years of experience, or age-fixed effects that flexibly estimate separate wage levels for each age. The quadratic specification typically balances parsimony and fit, though splines may better capture nonlinearities at very low and very high experience levels.

Continuous versus categorical education: Continuous years of schooling impose linearity in the return to education; categorical degree dummies (high school, some college, bachelor's, graduate) allow for nonlinear returns such as the "sheepskin effect" (large wage jumps at degree thresholds beyond the return to incremental years). Estimate both specifications and test for equality of marginal returns across degree levels. If the continuous specification is rejected, adopt the categorical specification and report returns to specific credentials.

**Fixed Effects Strategy for Unobserved Heterogeneity**

When panel data are available (PSID, NLSY), estimate wage equations with individual fixed effects $\alpha_i$ to absorb time-invariant unobserved ability, motivation, and family background:

$$\ln(w_{it}) = \beta_1 S_{it} + \beta_2 \text{Exp}_{it} + \beta_3 \text{Exp}_{it}^2 + \alpha_i + \lambda_t + \epsilon_{it}$$

The fixed effects estimator (within transformation) identifies returns to schooling from individuals who change education levels over time (rare for adult workers) or from the interaction of schooling with time-varying returns. In practice, education exhibits minimal within-individual variation, so the fixed effects estimate of $\beta_1$ is imprecise and often insignificant. Interpret this null result cautiously: it does not imply zero returns to schooling, but rather that cross-sectional return estimates conflate causal effects with unobserved ability differences.

For cross-sectional data, address omitted ability bias using instrumental variables. Common instruments include quarter of birth (Angrist-Krueger instrument exploiting compulsory schooling laws), distance to college (Card instrument), or state-level education policy changes (compulsory attendance age, school construction programs). The IV estimate identifies the local average treatment effect (LATE) for compliers—individuals induced to obtain more schooling by the instrument. External validity requires that compliers' returns approximate average treatment effects, an assumption that often fails when compliers are marginal students with below-average returns.

**Clustering and Robust Standard Errors**

Wage observations within geographic regions or industries exhibit correlated errors due to common shocks (local labor demand shifts, industry-specific technological change). Cluster standard errors at the state, metropolitan area, or industry level to account for these correlations. The Moulton problem arises when regressors vary at the cluster level (e.g., state minimum wage) but standard errors are not clustered: t-statistics are severely overstated, leading to spurious significance. Use the wild cluster bootstrap for robust inference when the number of clusters is small (fewer than 30).

Test for serial correlation in panel data using the Breusch-Pagan LM test. If present, cluster standard errors at the individual level or use Newey-West HAC standard errors with lag length selected by the Schwert criterion. For spatially correlated errors (e.g., wage spillovers across neighboring counties), use Conley spatial HAC standard errors with distance-based kernel weighting.

### Calibration and Simulation Troubleshooting

**Labor Supply Model Convergence Failures**

If the calibration spreadsheet fails to identify a unique optimum (multiple local maxima, flat utility over a range of hours), diagnose the issue by plotting the utility function $U(H)$ over the full range of hours. Non-concavity indicates misspecified preference parameters (e.g., $\rho > 1$ generating increasing marginal utility) or numerical precision errors in the CES utility formula. Ensure that the CES expression is evaluated with sufficient floating-point precision (double precision or higher) to avoid rounding errors when $\rho$ approaches zero or negative infinity.

Boundary solutions at $H = 0$ or $H = T$ signal that the wage rate, nonlabor income, or preference parameters are inconsistent with interior solutions. If optimal hours hit the zero-hour boundary, nonlabor income is sufficiently high relative to the wage that the individual chooses full leisure. If optimal hours hit the time endowment boundary, the marginal utility of consumption far exceeds the marginal disutility of foregone leisure, implying implausibly low valuation of leisure. Recalibrate parameters to replicate observed labor force participation rates (65-80 percent for prime-age workers) and average hours conditional on working (35-45 hours per week).

**Dynamic Search Model Stability and Convergence**

Value function iteration in the Mortensen-Pissarides search model solves the Bellman equations for the value of unemployment $U$ and the value of employment $W$:

$$rU = b + f(\theta) [W - U]$$
$$rW = w + \delta [U - W]$$

where $r$ is the discount rate, $b$ is unemployment benefits, and $w$ is the wage. Iterate on these equations until convergence: update $U$ and $W$ using the right-hand side expressions, check whether the maximum absolute difference between successive iterations falls below a tolerance threshold (e.g., $10^{-6}$), and repeat. Convergence typically requires 50-200 iterations depending on parameter values and initial guesses.

If iteration fails to converge or oscillates, reduce the updating weight using a dampening parameter $\gamma \in (0, 1)$: $U^{new} = \gamma U^{RHS} + (1 - \gamma) U^{old}$. Start with $\gamma = 0.5$ and decrease if oscillations persist. Alternatively, reformulate the Bellman equations as a fixed-point problem and apply Newton-Raphson or Broyden's method for faster convergence with quadratic rather than linear convergence rates.

Check parameter restrictions ensuring well-defined steady states: the discount rate must be positive, the separation rate must be less than one, and the vacancy posting cost must be positive. The steady-state unemployment rate is $u^* = \delta / (\delta + f(\theta^*))$; if the calibrated parameters generate $u^* < 0$ or $u^* > 1$, parameter values are infeasible.

**Sensitivity Analysis and Robustness Protocols**

Every calibrated model and estimated elasticity should undergo systematic sensitivity analysis. For labor supply elasticities, vary preference parameters $\alpha$ and $\rho$ over a grid spanning empirically plausible ranges, recompute optimal hours and elasticities at each grid point, and report the range of elasticity estimates. If qualitative policy conclusions (sign of the labor supply response to taxation) reverse across the plausible parameter space, policy recommendations are fragile and require additional empirical discipline through moment-matching or reduced-form elasticity targets.

For wage regression estimates, test coefficient stability across alternative sample restrictions (age ranges, education groups, full-time versus part-time workers), covariate sets (baseline versus extended controls), and estimation methods (OLS, fixed effects, instrumental variables). Plot coefficient estimates and confidence intervals across specifications using forest plots. If point estimates vary by more than one standard error across specifications, investigate the source of sensitivity: omitted variable bias, measurement error, or sample selection.

Document all robustness checks in an appendix table showing baseline and alternative specifications side by side. Report F-tests or Hausman tests comparing nested models. For instrumental variable estimates, report first-stage F-statistics (threshold: F > 10 for strong instruments) and overidentification tests when multiple instruments are available. Transparent reporting of specification searches and robustness checks builds credibility and prevents selective reporting of favored results.

### Diagnostic Checklist for Pre-Submission Verification

Before finalizing labor economics empirical analysis, complete the following verification protocol:

**Data and Sample Construction**

□ Raw data sourced from reputable repository with documented cleaning code  
□ Sample restrictions justified and documented (age, wage trimming, hours filters)  
□ Real wages constructed using appropriate deflator (CPI-U-RS for U.S. wages)  
□ Potential experience computed correctly (age - schooling - 6)  
□ Allocated wage observations excluded or flagged with control variable  
□ Weighted statistics computed using survey weights  
□ Missing values handled via listwise deletion or multiple imputation, not ad-hoc fills  

**Regression Specification and Estimation**

□ Log wage specification adopted for right-skewed wage distribution  
□ Experience entered as quadratic or tested against flexible alternatives  
□ Appropriate fixed effects included (region, occupation, industry)  
□ Standard errors clustered at relevant level (state, metro, industry)  
□ Heteroskedasticity-robust standard errors reported  
□ Regression diagnostics checked (residual plots, normality tests, outlier detection)  
□ Coefficient magnitudes compared to literature benchmarks  

**Calibration and Simulation**

□ Preference parameters disciplined by empirical elasticity targets  
□ Utility function checked for global concavity ensuring unique optimum  
□ Calibrated optimal hours align with observed labor supply (35-45 hours/week)  
□ Comparative statics directionally consistent with economic theory  
□ Numerical convergence verified with tolerance threshold documentation  
□ Sensitivity analysis over plausible parameter ranges conducted  

**Interpretation and Policy Conclusions**

□ Causal claims justified by identification strategy (IV, fixed effects, quasi-experiment)  
□ Reduced-form elasticities translated to policy-relevant metrics (deadweight loss, revenue)  
□ Welfare calculations explicitly state normative social welfare function  
□ Distributional impacts reported alongside aggregate efficiency measures  
□ External validity and generalizability caveats acknowledged  
□ Policy recommendations explicitly state underlying assumptions and limitations  

This diagnostic checklist ensures that labor economics empirical work meets professional standards for reproducibility, transparency, and rigor. Each completed exercise should pass every checkpoint before being presented as evidence for academic research, policy advocacy, or operational decision-making within firms and government agencies.
