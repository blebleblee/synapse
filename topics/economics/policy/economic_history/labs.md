# Operational Verification Labs: Economic History

## Objective & Operational Lab Setup

Economic history provides the empirical laboratory for testing macroeconomic theories, institutional hypotheses, and policy transmission mechanisms across time. This operational verification lab sequence trains practitioners to reconstruct historical economic episodes using archival data, quantitative methods, and counterfactual policy analysis. The exercises dissect three canonical episodes: the classical gold standard transmission mechanism (1880–1914), the Great Depression monetary collapse and policy response (1929–1939), and the Volcker disinflation and credibility-building regime shift (1979–1982). Each lab combines primary source data reconstruction, statistical hypothesis testing, and structural break identification to build operational intuition for how institutions, policy regimes, and exogenous shocks interact across historical time.

The analytical environment requires a spreadsheet application capable of regression analysis (Excel with Analysis ToolPak enabled, LibreOffice Calc, or Google Sheets), access to FRED (Federal Reserve Economic Data) and NBER Macrohistory Database for time-series retrieval, and a text editor for documenting institutional rule changes and policy regime annotations. The practitioner will construct rolling-window regressions, event-study difference-in-differences estimators, and Chow tests for structural breaks. All data series, regression specifications, and diagnostic criteria are provided in full operational detail with zero placeholders. The goal is not passive historical narrative but active reconstruction: given the constraints, information sets, and institutional rules facing policymakers in each episode, what transmission mechanisms operated, what policy levers existed, and what counterfactual interventions could have altered outcomes?

The lab structure progresses from foundational data assembly and stylized fact identification (Exercise 1), through comparative institutional analysis and regime-switching detection (Exercise 2), to stress testing policy counterfactuals and boundary condition exploration (Exercise 3). Each exercise concludes with a diagnostic checklist verifying that the practitioner has correctly identified transmission channels, quantified policy effects, and documented institutional constraints. The operational reference guide provides regression specification templates, data transformation protocols, and citation standards for archival sources.

### Environment Configuration and Data Acquisition Protocol

Begin by establishing a working directory structure: create folders labeled `data_raw/`, `data_transformed/`, `regressions/`, and `counterfactuals/`. Download monthly or annual time-series data from FRED for the following core indicators: industrial production index (INDPRO), consumer price index (CPIAUCSL), unemployment rate (UNRATE), M2 money stock (M2SL), and 10-year Treasury constant maturity rate (GS10). For pre-1947 data, access the NBER Macrohistory Database and retrieve historical series: wholesale price index, manufacturing output, bank suspensions, and gold reserve ratios. Store all raw data files in `data_raw/` with filenames encoding the source, frequency, and date range (e.g., `FRED_INDPRO_monthly_1919-1940.csv`). Transform all nominal series into real terms by dividing by the CPI and rebasing to a common index year. Compute year-over-year growth rates and log differences for all flow variables. Document every transformation step in a metadata file (`data_transformed/README.md`) to ensure full replicability.

Configure your spreadsheet application to enable regression analysis. In Excel, activate the Analysis ToolPak by navigating to File → Options → Add-ins → Manage Excel Add-ins → Analysis ToolPak, then check the box and click OK. In LibreOffice Calc, regression tools are natively available under Tools → Regression. Verify functionality by running a simple OLS regression of a dependent variable on a constant and one regressor, confirming that the output table includes coefficients, standard errors, t-statistics, R-squared, and residual diagnostics. Set numerical precision to display at least four decimal places for coefficients and two decimal places for test statistics.

For institutional context, compile a policy regime timeline document tracking key changes: legislative acts (e.g., Glass-Steagall Act, Employment Act of 1946), central bank operating procedures (e.g., Burgess-Riefler doctrine, borrowed reserves targeting, non-borrowed reserves targeting), and exchange rate arrangements (gold parity adjustments, Bretton Woods realignments). This timeline serves as the institutional annotation layer for interpreting statistical results and identifying candidate structural break dates.

## Exercise 1: Foundational Practical Implementation

### Reconstructing the Classical Gold Standard Transmission Mechanism (1880–1914)

The classical gold standard operated as an automatic monetary adjustment mechanism linking domestic price levels, gold flows, and interest rates across countries through arbitrage and specie flow dynamics. This exercise reconstructs the gold standard transmission mechanism using historical data for the United Kingdom and United States, testing the canonical Hume price-specie-flow hypothesis and quantifying the interest rate adjustment speed under gold convertibility constraints. The practitioner will assemble annual data on gold reserves, price levels, interest rates, and trade balances, estimate bilateral adjustment coefficients, and identify deviations from the idealized automatic adjustment mechanism that required discretionary central bank intervention.

Retrieve annual data from the NBER Macrohistory Database for 1880–1914: UK gold reserves held by the Bank of England (series m13027a), US Treasury gold stock (series m14076a), UK wholesale price index (series m13002a), US wholesale price index (series m04051a), Bank of England discount rate (series m13027b), and US short-term interest rate (series m13001a). Download trade balance data from Historical Statistics of the United States (Table Ee362-370). Import all series into a master spreadsheet with columns: Year, UK_Gold, US_Gold, UK_WPI, US_WPI, UK_Rate, US_Rate, UK_Trade_Balance, US_Trade_Balance. Verify data completeness and flag missing observations. For any gaps, interpolate linearly if the gap spans fewer than three consecutive years; otherwise, document the gap and exclude those observations from regression analysis.

Transform the raw data to construct theoretically relevant variables. Compute the UK-US wholesale price ratio as $\text{Price Ratio}_t = \frac{\text{UK WPI}_t}{\text{US WPI}_t}$, rebased so that the sample mean equals 100. Calculate year-over-year percentage changes in gold reserves: $\Delta \text{Gold}_t = \frac{\text{Gold}_t - \text{Gold}_{t-1}}{\text{Gold}_{t-1}} \times 100$. Compute the interest rate differential as $\text{Rate Diff}_t = \text{UK Rate}_t - \text{US Rate}_t$. These transformations operationalize the Hume mechanism: a country losing gold should experience falling prices and rising interest rates relative to its trading partner, which should reverse the gold outflow through improved competitiveness and capital inflows.

Estimate the price-specie-flow regression for the United Kingdom. Regress the annual percentage change in UK gold reserves ($\Delta \text{UK Gold}_t$) on the lagged price ratio ($\text{Price Ratio}_{t-1}$) and the lagged trade balance as a percentage of GDP ($\text{UK Trade Balance}_{t-1} / \text{UK GDP}_{t-1}$). The regression specification is:

$$
\Delta \text{UK Gold}_t = \beta_0 + \beta_1 \text{Price Ratio}_{t-1} + \beta_2 \left( \frac{\text{UK Trade Balance}_{t-1}}{\text{UK GDP}_{t-1}} \right) + \varepsilon_t
$$

The theory predicts $\beta_1 < 0$: when UK prices are high relative to US prices, gold flows out of the UK as British goods become less competitive. The coefficient $\beta_2$ should be positive: a trade surplus brings gold inflows. Run the regression in your spreadsheet application using the period 1881–1914 (using lagged values requires dropping the first year). Record the estimated coefficients, standard errors, t-statistics, and R-squared. A well-functioning gold standard should yield $\beta_1$ significantly negative with $|\beta_1| > 0.5$, indicating that a 1 percent relative price increase induces at least a 0.5 percent gold outflow the following year.

Parallel this analysis with an interest rate adjustment regression. The gold standard theory implies that gold outflows should trigger interest rate increases as central banks defend convertibility by tightening liquidity. Estimate the Bank of England policy reaction function:

$$
\Delta \text{UK Rate}_t = \gamma_0 + \gamma_1 \Delta \text{UK Gold}_{t-1} + \gamma_2 \text{UK Trade Balance}_{t-1} + u_t
$$

The expected sign is $\gamma_1 < 0$: gold losses (negative $\Delta \text{UK Gold}$) lead to interest rate increases (positive $\Delta \text{UK Rate}$). A statistically significant negative coefficient confirms that the Bank of England actively managed the discount rate to stabilize gold reserves, deviating from the purely automatic adjustment mechanism. Repeat both regressions for the United States to compare the symmetry of adjustment between core and peripheral gold standard participants.

Construct a counterfactual policy experiment by simulating the gold reserve path under alternative Bank of England reaction coefficients. Using the estimated baseline $\gamma_1$, generate the fitted interest rate series $\widehat{\Delta \text{UK Rate}}_t$. Then re-run the gold flow regression replacing actual interest rate changes with counterfactual rates computed assuming $\gamma_1 = 0$ (no policy response) and $\gamma_1 = 2 \times \widehat{\gamma}_1$ (aggressive defense). Plot the resulting gold reserve paths on a single chart with actual reserves to visualize how discretionary policy stabilized or destabilized the system. This exercise reveals the operational tension between the gold standard's nominal automaticity and the practical requirement for active central bank management.

Document the following diagnostic findings: (1) the magnitude and statistical significance of the price-specie-flow coefficient $\beta_1$, (2) the speed of interest rate adjustment as measured by $\gamma_1$, (3) the fraction of gold reserve variance explained by price competitiveness versus discretionary policy, and (4) any episodes where gold flows or interest rate changes sharply deviated from the fitted model, indicating financial crises or speculative attacks. Annotate these deviations with institutional context from your policy regime timeline (e.g., the Panic of 1907, Baring Crisis of 1890).

## Exercise 2: Parameter Variation & Empirical Analysis

### Detecting Monetary Regime Shifts and Policy Ineffectiveness During the Great Depression (1929–1939)

The Great Depression provides the archetypal case study for monetary policy regime failure, institutional rigidity, and the limits of gold standard constraints on countercyclical stabilization. This exercise uses structural break tests and rolling regressions to identify the collapse of the money multiplier, the failure of interest rate transmission, and the delayed regime shift from passive gold standard adherence to active reflation policy. The practitioner will quantify the timing and magnitude of these regime changes, estimate the output cost of delayed intervention, and test the counterfactual effectiveness of earlier gold standard suspension and money supply expansion.

Assemble monthly data from FRED and NBER sources for January 1929 through December 1939: industrial production index (INDPRO, rebased to 1929 = 100), M2 money stock (M2SL), consumer price index (CPIAUCSL), bank suspensions count (NBER series m13040a), gold stock held by the Federal Reserve (FRED series GOLDSTOCK), and federal funds effective rate (approximate with the discount rate from FRED series M13009USM156NNBR for the pre-1954 period). Compute the velocity of money as $V_t = \frac{\text{Industrial Production}_t}{\text{M2}_t}$ and the money multiplier as $m_t = \frac{\text{M2}_t}{\text{Monetary Base}_t}$ where the monetary base equals currency in circulation plus bank reserves (retrieve from FRED series BOGMBASE or NBER series m13015a). Transform all series into natural logarithms for growth rate analysis.

Perform a Chow test for structural breaks in the money demand function. Estimate the baseline regression for the full sample 1929–1939:

$$
\ln(V_t) = \alpha_0 + \alpha_1 \ln(\text{CPI}_t) + \alpha_2 \text{Interest Rate}_t + \varepsilon_t
$$

The velocity of money should respond negatively to interest rates (liquidity preference) and positively to the price level (real balance effect). Record the sum of squared residuals (SSR) for this unrestricted full-sample regression. Now partition the sample at the candidate break date: April 1933, when the United States abandoned the gold standard and began reflation policy under the Emergency Banking Act. Estimate the regression separately for 1929:01–1933:03 and 1933:04–1939:12, recording the SSR for each sub-sample as $SSR_1$ and $SSR_2$. Compute the Chow F-statistic:

$$
F = \frac{(SSR_{\text{full}} - (SSR_1 + SSR_2)) / k}{(SSR_1 + SSR_2) / (n - 2k)}
$$

where $k = 3$ is the number of parameters and $n$ is the total number of observations. Compare the computed F-statistic to the critical value from the F-distribution with $(k, n - 2k)$ degrees of freedom at the 5 percent significance level. A statistically significant Chow test confirms a structural break in money demand at the regime shift date. Repeat this test for alternative break dates (March 1933, March 1932, January 1934) to identify the most statistically significant break point.

Estimate the collapse of the money multiplier using a rolling 12-month window regression. For each month $t$ from January 1930 to December 1938, estimate the regression:

$$
\ln(m_t) = \delta_0 + \delta_1 \text{Bank Suspensions}_{t} + \delta_2 \ln(\text{Excess Reserves}_t) + \eta_t
$$

using data from month $t - 11$ through month $t$. Plot the rolling coefficient $\widehat{\delta}_1$ over time. The theory predicts that bank failures destroy deposit money and collapse the money multiplier, so $\delta_1 < 0$. The magnitude of $\delta_1$ quantifies the fragility of the fractional reserve banking system. During the acute crisis phase (1930–1933), the rolling $\widehat{\delta}_1$ should become sharply more negative, indicating an accelerating collapse. After the banking system stabilization in mid-1933 (FDIC insurance, suspension of gold convertibility), the coefficient should moderate. This rolling-window approach identifies the temporal evolution of systemic fragility more precisely than a single full-sample regression.

Construct a counterfactual simulation to estimate the output cost of delayed monetary expansion. Using the estimated money demand and production function parameters, simulate what industrial production would have been if the Federal Reserve had expanded the monetary base by 25 percent in 1930 (rather than allowing it to contract). The counterfactual production path is:

$$
\widehat{\ln(\text{Production})}_t = \ln(\text{Production})_t + \widehat{\alpha}_1 \Delta \ln(\text{M2})_{\text{counterfactual}, t}
$$

where $\Delta \ln(\text{M2})_{\text{counterfactual}, t}$ is the difference between the counterfactual money stock path (with 25 percent base expansion) and the actual money stock. Compute the cumulative output gap as the sum of percentage differences between counterfactual and actual production from 1930 to 1933. Convert this into a total output loss by multiplying the percentage gap by actual GDP for each year and summing. This quantifies the cost of policy inaction in dollar terms.

Test the gold standard constraint hypothesis by regressing the Federal Reserve discount rate on the gold reserve ratio. If the gold standard binding constraint prevented aggressive monetary expansion, the discount rate should respond positively to declines in the gold reserve ratio:

$$
\text{Discount Rate}_t = \theta_0 + \theta_1 \left( \frac{\text{Gold Stock}_t}{\text{Federal Reserve Notes}_t} \right) + \theta_2 \Delta \ln(\text{Industrial Production}_t) + \xi_t
$$

A positive and significant $\theta_1$ indicates that the Federal Reserve raised rates to defend gold reserves even as output collapsed, validating the structural constraint narrative. After April 1933, re-estimate the regression to test whether $\theta_1$ drops to insignificance, confirming the regime shift to domestic output stabilization as the primary policy objective.

Document the following empirical findings: (1) the Chow test F-statistic and break date for the money demand function, (2) the trajectory of the rolling money multiplier coefficient and its nadir in 1933, (3) the cumulative output loss from delayed monetary expansion, expressed in billions of 1929 dollars, and (4) the magnitude of the gold standard constraint coefficient $\theta_1$ before and after suspension. Annotate the timeline of policy changes (Banking Act of 1933, Gold Reserve Act of 1934, abandonment of gold convertibility) and relate them to the estimated break dates and coefficient shifts.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Policy Credibility, Expectation Anchoring, and the Volcker Disinflation (1979–1982)

The Volcker disinflation represents the canonical modern case of a central bank engineering a regime shift to restore price stability and anchor inflation expectations after a decade of high and volatile inflation. This exercise quantifies the credibility-building process through forward-looking inflation expectation series, estimates the sacrifice ratio (output loss per percentage point of disinflation), and tests the boundary condition under which a disinflationary policy regime becomes unsustainable due to political or financial instability. The practitioner will decompose the disinflation into monetary policy shocks, expectation revisions, and residual cost-push components, then stress-test the policy rule under alternative unemployment tolerance thresholds.

Retrieve monthly data from FRED for January 1979 through December 1982: CPI all items (CPIAUCSL), unemployment rate (UNRATE), federal funds effective rate (FEDFUNDS), 10-year Treasury constant maturity rate (GS10), and M2 money stock (M2SL). Download the University of Michigan 1-year ahead inflation expectation survey series (MICH) and the 10-year breakeven inflation rate derived from TIPS spreads (for post-1997 context; for the 1979–1982 period, use the University of Michigan 5-to-10-year inflation expectation series or the Livingston Survey median forecast). Compute realized inflation as the year-over-year percentage change in CPI: $\pi_t = \frac{\text{CPI}_t - \text{CPI}_{t-12}}{\text{CPI}_{t-12}} \times 100$. Compute the inflation expectation error as $\pi_t - E_{t-12}[\pi_t]$ where $E_{t-12}[\pi_t]$ is the 1-year ahead survey expectation from 12 months prior.

Estimate the Volcker-era Taylor rule to characterize the Federal Reserve's policy reaction function. The Taylor rule posits that the federal funds rate responds to inflation deviations from target and output gaps:

$$
i_t = r^* + \pi_t + \phi_\pi (\pi_t - \pi^*) + \phi_y (y_t - y^*)
$$

where $i_t$ is the federal funds rate, $r^*$ is the equilibrium real interest rate (assumed 2 percent), $\pi_t$ is current inflation, $\pi^*$ is the inflation target (assumed 2 percent post-1982, but ambiguous during 1979–1982), $y_t - y^*$ is the output gap (proxied by the unemployment gap $u_t - u^*$ with a negative sign), and $\phi_\pi, \phi_y$ are policy response coefficients. Estimate the regression:

$$
\text{FEDFUNDS}_t = \beta_0 + \beta_1 \pi_t + \beta_2 (\pi_t - 2) + \beta_3 (\text{UNRATE}_t - 6) + \varepsilon_t
$$

Run this regression separately for the pre-Volcker period (1970:01–1979:07) and the Volcker period (1979:08–1982:12) to test for a structural break in policy aggressiveness. The pre-Volcker regime should yield $\beta_2 < 1$, indicating passive accommodation of inflation (the Taylor principle violated). The Volcker regime should yield $\beta_2 > 1$, confirming aggressive inflation-fighting. A Chow test at the break date of August 1979 (when Volcker assumed the chairmanship and announced the shift to non-borrowed reserves targeting) should reject equality of coefficients across the two periods.

Decompose the disinflation into monetary policy shocks and expectation revisions using a variance decomposition. Estimate a Vector Autoregression (VAR) with three variables: inflation $\pi_t$, unemployment rate $u_t$, and federal funds rate $i_t$. Use four lags and estimate the VAR over the period 1979:08–1982:12. Identify the monetary policy shock using a Cholesky decomposition with the ordering $[\pi_t, u_t, i_t]$, which assumes that inflation and unemployment do not respond contemporaneously to interest rate changes but the policy rate responds contemporaneously to inflation and unemployment (the standard recursive identification). Compute the impulse response functions showing the effect of a one-standard-deviation positive federal funds rate shock on inflation and unemployment over 24 months. The inflation response should be negative and persistent; the unemployment response should be positive (the sacrifice ratio). Integrate the cumulative inflation response and unemployment response to compute the sacrifice ratio: the cumulative percentage point increase in unemployment per percentage point reduction in inflation.

Test the sustainability boundary of the Volcker policy by estimating the maximum politically tolerable unemployment rate. Using the estimated Taylor rule, simulate the interest rate path under alternative inflation target convergence speeds: aggressive (reaching 2 percent inflation in 18 months), baseline (36 months, the actual path), and gradual (60 months). For each scenario, use the estimated VAR to forecast the unemployment path. Historical evidence suggests that unemployment rates above 10 percent for extended periods trigger severe political pressure for policy reversal (as occurred in 1982 with Congressional and business community criticism of Volcker). Define the boundary condition as any scenario producing unemployment above 10.5 percent for more than six consecutive months. Identify which disinflation speed scenarios violate this boundary and which remain sustainable. This quantifies the political economy constraint on optimal monetary policy.

Construct an expectation-anchoring diagnostic by regressing changes in survey inflation expectations on lagged policy announcements and realized inflation surprises. The regression specification is:

$$
\Delta E_t[\pi_{t+12}] = \lambda_0 + \lambda_1 (\pi_t - E_{t-1}[\pi_t]) + \lambda_2 \Delta i_t + \lambda_3 D_t + \nu_t
$$

where $\Delta E_t[\pi_{t+12}]$ is the monthly change in the 1-year ahead inflation expectation, $\pi_t - E_{t-1}[\pi_t]$ is the inflation surprise, $\Delta i_t$ is the change in the federal funds rate, and $D_t$ is a dummy variable for major Volcker policy announcement dates (October 1979 shift to reserves targeting, October 1982 shift back to interest rate targeting). The coefficient $\lambda_2$ measures the direct effect of interest rate changes on expectations (the signaling channel), while $\lambda_3$ captures the discrete credibility jumps from major regime announcements. A successful credibility-building campaign should show $\lambda_3 < 0$ and statistically significant: announcements directly lower inflation expectations independent of realized inflation outcomes.

Perform a boundary failure stress test by simulating a counterfactual scenario in which Volcker abandoned the disinflation in mid-1982 under political pressure. Using the VAR model, simulate the inflation and unemployment path from July 1982 onward under the assumption that the federal funds rate reverts to the pre-Volcker policy rule (the estimated $\beta_2 < 1$ from the 1970–1979 period). Compare the simulated inflation path to the actual post-1982 path. The counterfactual should show inflation re-accelerating to 8–10 percent by 1984, validating the necessity of policy persistence despite short-run costs. This stress test demonstrates the irreversibility constraint: once a disinflationary policy is initiated, premature abandonment destroys credibility and necessitates even larger future sacrifices.

Document the following operational findings: (1) the estimated Taylor rule coefficients and Chow test result confirming the policy regime break, (2) the computed sacrifice ratio from the VAR impulse responses, (3) the boundary unemployment rate threshold and which disinflation speed scenarios violate it, (4) the magnitude of the expectation-anchoring coefficient $\lambda_3$ and its statistical significance, and (5) the counterfactual inflation re-acceleration path under premature policy abandonment. Compile these results into a policy memo format that directly answers: What was the minimum feasible disinflation speed given political constraints, what was the quantified output cost, and what institutional factors enabled Volcker to sustain the policy despite crossing the unemployment boundary threshold?

## Operational Reference Guide & Diagnostic Checklist

### Regression Specification Templates

For practitioners conducting economic history analysis, the following standardized regression templates ensure consistency and replicability across episodes. All specifications include robust standard error corrections and diagnostic tests for autocorrelation and heteroskedasticity.

**Price-Specie-Flow Mechanism (Gold Standard Transmission):**

$$
\Delta \text{Gold Reserves}_t = \beta_0 + \beta_1 \text{Relative Price Level}_{t-1} + \beta_2 \text{Trade Balance}_{t-1} + \beta_3 \text{Interest Rate Differential}_{t-1} + \varepsilon_t
$$

**Central Bank Policy Reaction Function (Interest Rate Rule):**

$$
\Delta i_t = \gamma_0 + \gamma_1 \Delta \text{Gold Reserves}_{t-1} + \gamma_2 \pi_t + \gamma_3 (u_t - u^*) + u_t
$$

**Money Demand with Structural Breaks:**

$$
\ln(V_t) = \alpha_0 + \alpha_1 \ln(P_t) + \alpha_2 i_t + \alpha_3 D_t + \alpha_4 (D_t \times \ln(P_t)) + \varepsilon_t
$$

where $D_t$ is a regime dummy (0 before break, 1 after) and the interaction term $\alpha_4$ tests for parameter instability.

**VAR System for Monetary Policy Shock Identification (Cholesky Ordering $[\pi_t, u_t, i_t]$):**

$$
\begin{bmatrix} \pi_t \\ u_t \\ i_t \end{bmatrix} = \mathbf{A}_0 + \mathbf{A}_1 \begin{bmatrix} \pi_{t-1} \\ u_{t-1} \\ i_{t-1} \end{bmatrix} + \cdots + \mathbf{A}_p \begin{bmatrix} \pi_{t-p} \\ u_{t-p} \\ i_{t-p} \end{bmatrix} + \mathbf{e}_t
$$

Estimate using OLS equation-by-equation with four lags ($p = 4$). Compute impulse responses using the Cholesky decomposition $\mathbf{P}$ where $\mathbf{P} \mathbf{P}' = \Sigma$ and $\Sigma$ is the variance-covariance matrix of residuals.

### Data Transformation and Diagnostic Protocol

**Step 1: Raw Data Verification.** Upon importing historical data, check for structural inconsistencies: currency redenominations, base year changes, seasonal adjustment revisions. NBER Macrohistory Database series often splice multiple underlying sources; verify splice dates and test for breaks at splice points using the Chow test.

**Step 2: Unit Root Testing.** Before estimating regressions with time-series data, test all variables for stationarity using the Augmented Dickey-Fuller (ADF) test. If a variable is non-stationary (fails to reject the unit root null hypothesis), difference it or use cointegration methods. For the gold standard and Great Depression exercises, most variables should be stationary in growth rates or first differences.

**Step 3: Outlier Detection and Treatment.** Economic history data contain genuine shocks (wars, panics, natural disasters) that appear as outliers but carry economic information. Use the DFFITS diagnostic to identify high-leverage observations:

$$
\text{DFFITS}_i = \frac{\widehat{y}_i - \widehat{y}_{i(i)}}{\widehat{\sigma}_{(i)} \sqrt{h_{ii}}}
$$

where $\widehat{y}_i$ is the fitted value with observation $i$ included, $\widehat{y}_{i(i)}$ is the fitted value with observation $i$ excluded, $\widehat{\sigma}_{(i)}$ is the residual standard error with observation $i$ excluded, and $h_{ii}$ is the leverage. Observations with $|\text{DFFITS}_i| > 2\sqrt{k/n}$ should be investigated. If the outlier corresponds to a documented historical event (e.g., October 1929 stock market crash), retain it but include a dummy variable for that observation.

**Step 4: Autocorrelation Correction.** Compute the Durbin-Watson statistic to test for first-order autocorrelation. If $DW < 1.5$ or $DW > 2.5$, residuals exhibit significant autocorrelation. Correct by estimating the regression with Newey-West standard errors (heteroskedasticity and autocorrelation consistent, HAC) using a lag length $L = \lfloor 4(T/100)^{2/9} \rfloor$ where $T$ is the sample size.

**Step 5: Multicollinearity Check.** For regressions with multiple regressors, compute the Variance Inflation Factor (VIF) for each variable:

$$
\text{VIF}_j = \frac{1}{1 - R_j^2}
$$

where $R_j^2$ is the R-squared from regressing variable $j$ on all other regressors. A $\text{VIF} > 10$ indicates severe multicollinearity. In economic history applications, multicollinearity often arises from trending variables (e.g., price level and money stock both trending upward). Mitigate by using detrended or differenced variables.

### Counterfactual Simulation Best Practices

Counterfactual policy analysis requires explicit articulation of the intervention, the transmission channel, and the maintained assumptions. Structure counterfactual simulations as follows:

**Define the Intervention Precisely.** Specify the counterfactual policy action in operational terms: the magnitude of the monetary base expansion (e.g., 25 percent increase), the timing (e.g., beginning January 1930), and the duration (e.g., sustained through December 1933). Vague counterfactuals like "more expansionary policy" are not operationalizable.

**Identify the Transmission Mechanism.** State which estimated parameter captures the transmission from the policy instrument to the target variable. For a monetary expansion counterfactual, this is typically the money demand elasticity or the money multiplier. Use the point estimate from your baseline regression, not an optimistic or pessimistic scenario, to maintain empirical discipline.

**Hold Structural Parameters Constant (Lucas Critique Caveat).** The Lucas critique warns that policy regime changes alter behavioral parameters. When simulating a counterfactual policy that represents a dramatic regime shift (e.g., suspending the gold standard in 1930 rather than 1933), acknowledge that structural parameters estimated under the historical regime may not hold. Bound the counterfactual by simulating both the baseline parameter values and a 50 percent attenuation of the transmission effect to represent parameter instability.

**Validate Against Out-of-Sample Episodes.** Where possible, validate your counterfactual simulation approach by applying it to a historical episode with known outcomes. For example, simulate the 1921 deflation and recovery using the same money demand parameters estimated for the 1930s, then compare the simulated output path to actual outcomes. Close agreement validates the parameter estimates and simulation methodology.

### Diagnostic Checklist for Historical Episode Analysis

Complete the following checklist after finishing each exercise to verify operational rigor and empirical validity:

**Data Provenance and Transformation:**
- [ ] All data sources documented with retrieval dates and version numbers
- [ ] Splice dates and base year changes identified and tested for structural breaks
- [ ] Nominal-to-real conversions and growth rate calculations verified by manual spot check
- [ ] Missing data flagged, and interpolation or exclusion decisions documented

**Regression Diagnostics:**
- [ ] R-squared and adjusted R-squared reported (should be > 0.3 for well-specified models)
- [ ] All coefficients report standard errors, t-statistics, and p-values
- [ ] Durbin-Watson statistic computed and autocorrelation corrected if necessary
- [ ] VIF computed for all regressors; multicollinearity addressed if VIF > 10
- [ ] Chow test performed for hypothesized structural break dates; F-statistic and p-value reported

**Economic Interpretation:**
- [ ] Sign and magnitude of key coefficients align with theoretical predictions
- [ ] Statistically insignificant results acknowledged and alternative explanations explored
- [ ] Economically significant deviations from the model annotated with institutional context
- [ ] Counterfactual simulations bounded by parameter uncertainty and structural stability concerns

**Institutional Context Integration:**
- [ ] Policy regime timeline cross-referenced with regression break dates
- [ ] Major legislative and institutional changes annotated in time-series plots
- [ ] Deviations from model predictions linked to specific historical events or shocks

**Reproducibility:**
- [ ] All regression specifications written in equation form with variable definitions
- [ ] Data transformations and lag structures explicitly documented
- [ ] Counterfactual scenarios specified with precise parameter values and timing
- [ ] Results tables and diagnostic statistics preserved in a summary spreadsheet for reference

This operational verification lab sequence equips the practitioner with the econometric and institutional knowledge to reconstruct historical economic episodes, test competing hypotheses about policy transmission mechanisms, and quantify the costs of policy errors. The discipline of operational economic history—assembling primary data, estimating structural parameters, and simulating counterfactuals—trains the same empirical rigor and causal inference skills required for real-time policy analysis. Historical episodes provide the laboratory where theories can be tested against outcomes uncorrupted by publication bias or data mining, revealing the genuine constraints, transmission lags, and institutional frictions that condition policy effectiveness across different monetary and fiscal regimes.
