# Operational Verification Labs: Health Economics

## Objective & Operational Lab Setup

Health economics sits at the intersection of microeconomic theory, institutional analysis, and empirical policy evaluation. This laboratory guide trains you to operationalize the core analytical frameworks that practitioners deploy when evaluating insurance market equilibria, pharmaceutical pricing strategies, hospital production functions, and government intervention mechanisms in healthcare markets. You will build spreadsheet-based models grounded in consumer theory, principal-agent contracts, adverse selection dynamics, and cost-effectiveness analysis—the same quantitative tools health economists use in ministries of health, regulatory agencies, pharmaceutical consulting firms, and academic research centers.

These exercises prioritize hands-on construction of working models over passive reading of theoretical propositions. You will parameterize utility functions, calibrate demand elasticities from real mortality and expenditure data, simulate insurance market death spirals under adverse selection, and execute incremental cost-effectiveness ratio (ICER) calculations that mirror real-world technology assessment protocols used by NICE (National Institute for Health and Care Excellence) in the UK and ICER in the United States. Each lab delivers a concrete artifact: a calibrated spreadsheet model, a set of comparative statics results, or a diagnostic checklist you can deploy in operational policy contexts.

### Analytical Environment Configuration

Your primary analytical platform is a spreadsheet application—Excel, Google Sheets, or LibreOffice Calc—configured to handle multi-sheet workbooks with named ranges, scenario managers, and sensitivity tables. You will also maintain a plain-text log file documenting parameter sources, calibration decisions, and model validation steps. This log serves as your audit trail, enabling replication and peer review.

**Spreadsheet Setup Protocol:** Create a new workbook titled `HealthEcon_Labs.xlsx`. Establish five separate sheets: `Parameters`, `DemandModel`, `InsuranceEquilibrium`, `CostEffectiveness`, and `ValidationLog`. The `Parameters` sheet will house all exogenous variables—population demographics, income distributions, price vectors, epidemiological rates—with cells named using Excel's Name Manager for transparent cross-sheet referencing. The `ValidationLog` sheet will record every calibration source, assumption, and sensitivity test in chronological order, forming a running narrative of your analytical decisions.

**Data Acquisition Infrastructure:** Health economics relies on publicly available datasets from national statistical agencies, WHO databases, and peer-reviewed supplement files. For these labs, you will draw on three canonical sources: the Medical Expenditure Panel Survey (MEPS) for U.S. healthcare utilization and spending micro-data, WHO Global Health Expenditure Database for international comparisons, and published elasticity estimates from the RAND Health Insurance Experiment. Download the MEPS 2022 Full Year Consolidated Data File (HC-233) from the AHRQ website, extract the ASCII file, and import the subset of variables into your `Parameters` sheet: `TOTEXP22` (total healthcare expenditure), `AGE22`, `INSURC22` (insurance coverage indicator), and `RTHLTH53` (perceived health status). You will use these microdata to calibrate demand functions and simulate counterfactual insurance reforms.

**Computational Conventions:** All monetary units are expressed in constant 2022 U.S. dollars unless otherwise noted. Discount rates for cost-effectiveness analysis default to 3% per annum, reflecting OMB Circular A-94 guidelines and standard health technology assessment protocols. Utility functions follow the conventional CRRA (Constant Relative Risk Aversion) form with risk aversion coefficient $\sigma$ calibrated from experimental literature. Every model parameter must cite its source in the adjacent cell using Excel comments or a dedicated `Source` column in the `Parameters` sheet.

**Verification Standards:** After constructing each model, you will execute a three-tier validation protocol. First, internal consistency checks: verify that budget constraints bind at optimum, that probability weights sum to unity, and that comparative statics align with theoretical predictions (e.g., demand slopes downward, moral hazard increases utilization). Second, external calibration: compare your model's baseline predictions to observed aggregate statistics—total health expenditure as a percentage of GDP, insurance coverage rates, average out-of-pocket spending. Third, sensitivity robustness: systematically vary each parameter by ±20% and confirm that qualitative results remain stable. Document all validation outcomes in the `ValidationLog` sheet with pass/fail indicators and quantitative deviation metrics.

## Exercise 1: Foundational Practical Implementation—Demand for Healthcare Under Uncertainty and Insurance

This exercise constructs a fully parameterized model of individual demand for healthcare services under uncertainty, incorporating the foundational Arrow (1963) and Pauly (1968) framework of insurance as a risk-transfer mechanism. You will build a two-state expected utility model where an individual faces a probability of illness, values healthcare consumption through a state-dependent utility function, and chooses optimal insurance coverage given actuarially fair or loaded premiums. The output is a calibrated spreadsheet model that generates demand curves for healthcare, computes willingness-to-pay for insurance, and quantifies the welfare loss from moral hazard.

### Theoretical Microfoundations and Model Architecture

The individual maximizes expected utility over two states of the world: healthy (state H) and sick (state S). In state H, which occurs with probability $(1 - p)$, the individual consumes a composite good $c_H$ and requires minimal healthcare $m_H \approx 0$. In state S, which occurs with probability $p$, illness imposes a medical need $\bar{m}$ and the individual consumes $c_S$ and medical care $m_S$. The state-dependent utility function takes the separable form:

$$U(c, m | \text{state}) = u(c) + v(m, \text{state})$$

where $u(c) = \frac{c^{1-\sigma}}{1-\sigma}$ is the standard CRRA utility over consumption, and $v(m, S) = \theta \ln(m)$ captures the health benefits of medical care when sick, with $\theta$ representing the marginal utility of health. When healthy, $v(m, H) = 0$ since healthcare provides no additional utility beyond the baseline.

The individual's expected utility without insurance is:

$$EU_0 = (1-p) \left[ u(w) \right] + p \left[ u(w - p_m \bar{m}) + \theta \ln(\bar{m}) \right]$$

where $w$ is initial wealth, $p_m$ is the unit price of medical care, and $\bar{m}$ is the medically appropriate quantity of care in the sick state. With actuarially fair insurance that pays out $I$ in the sick state for premium $\pi = p \cdot I$, expected utility becomes:

$$EU_I = (1-p) \left[ u(w - \pi) \right] + p \left[ u(w - \pi - p_m \bar{m} + I) + \theta \ln(\bar{m}) \right]$$

The individual's optimal insurance purchase $I^*$ equates the marginal cost of the premium to the expected marginal benefit of the payout, weighted by the marginal utility of consumption in each state. Under full insurance ($I^* = p_m \bar{m}$), consumption is equalized across states, eliminating income risk but introducing moral hazard if the quantity $\bar{m}$ responds to the effective price reduction.

### Spreadsheet Construction Protocol

Navigate to the `Parameters` sheet and establish the following named ranges. In cell `B2`, enter `Income` with value 50000 (representing median U.S. household income in 2022 dollars). In `B3`, enter `RiskAversionSigma` with value 2.0, a standard calibration from experimental studies of risk preferences. In `B4`, enter `ProbIllness` with value 0.15, approximating the annual probability of a significant health shock requiring substantial medical care. In `B5`, enter `MedicalPrice` with value 150, representing the per-unit price of a standardized healthcare service (e.g., per physician visit or per procedure). In `B6`, enter `MedicalNeed` with value 20, the quantity of care required when sick. In `B7`, enter `HealthUtilityWeight` with value 5000, calibrated such that the health utility term $\theta \ln(\bar{m})$ is economically significant relative to consumption utility. In `B8`, enter `LoadingFactor` with value 1.15, representing administrative costs and profit margins in private insurance markets (i.e., premiums exceed actuarially fair values by 15%).

Navigate to the `DemandModel` sheet and construct the utility calculation infrastructure. In column A, create a scenario parameter `InsurancePayout` ranging from 0 to 3000 in increments of 100 (rows 2 through 32). In cell `B1`, label `Premium`. In column B, calculate the premium for each payout level: `=ProbIllness * A2 * LoadingFactor` in `B2`, and copy down. In cell `C1`, label `ConsumptionHealthy`. In column C, calculate consumption in the healthy state: `=Income - B2` in `C2`, and copy down. In cell `D1`, label `ConsumptionSick`. In column D, calculate consumption in the sick state: `=Income - B2 - MedicalPrice * MedicalNeed + A2` in `D2`, and copy down.

In cell `E1`, label `UtilityHealthy`. In column E, calculate CRRA utility in the healthy state: `=IF(RiskAversionSigma = 1, LN(C2), (C2^(1 - RiskAversionSigma)) / (1 - RiskAversionSigma))` in `E2`, and copy down. The conditional handles the log utility special case when $\sigma = 1$. In cell `F1`, label `UtilitySick`. In column F, calculate total utility in the sick state (consumption plus health): `=IF(RiskAversionSigma = 1, LN(D2), (D2^(1 - RiskAversionSigma)) / (1 - RiskAversionSigma)) + HealthUtilityWeight * LN(MedicalNeed)` in `F2`, and copy down. In cell `G1`, label `ExpectedUtility`. In column G, compute expected utility: `=(1 - ProbIllness) * E2 + ProbIllness * F2` in `G2`, and copy down.

Identify the optimal insurance purchase by locating the maximum value in column G using Excel's `MAX` function. In cell `H1`, enter `OptimalPayout`, and in `H2`, use `=INDEX(A:A, MATCH(MAX(G:G), G:G, 0))`. In cell `I1`, enter `OptimalPremium`, and in `I2`, use `=INDEX(B:B, MATCH(MAX(G:G), G:G, 0))`. In cell `J1`, enter `MaxExpectedUtility`, and in `J2`, enter `=MAX(G:G)`. These cells now display the individual's optimal insurance choice and the resulting welfare level.

### Calibration Against Empirical Benchmarks

Compare your model's predictions to observed insurance coverage patterns. The optimal payout $I^*$ should cover a substantial fraction of expected medical expenses $p \cdot p_m \cdot \bar{m} = 0.15 \times 150 \times 20 = 450$ dollars. With the baseline parameters, the model should predict near-complete coverage if the loading factor is low, but partial coverage as loading increases. In cell `K1`, enter `CoverageRatio`, and in `K2`, calculate `=H2 / (MedicalPrice * MedicalNeed)`. A coverage ratio near 0.7 to 0.9 aligns with observed employer-sponsored insurance plans that feature cost-sharing provisions.

Next, compute the certainty equivalent wealth—the guaranteed income that would yield the same expected utility as the uncertain health lottery with optimal insurance. In cell `L1`, enter `CertaintyEquivalent`. In `L2`, calculate: `=IF(RiskAversionSigma = 1, EXP(J2), ((1 - RiskAversionSigma) * J2)^(1/(1 - RiskAversionSigma)))`. The risk premium is the difference between initial wealth and the certainty equivalent: in cell `M1`, enter `RiskPremium`, and in `M2`, calculate `=Income - L2`. For $\sigma = 2.0$ and $p = 0.15$, the risk premium should fall in the range of $500 to $1500, reflecting moderate risk aversion. Document this result in the `ValidationLog` sheet: "Baseline risk premium = [value], within expected range for sigma=2.0 per Holt and Laury (2002) elicitation studies."

### Moral Hazard Extension and Demand Elasticity

Extend the model to incorporate moral hazard by allowing the quantity of medical care consumed $m_S$ to respond to the effective price after insurance. Replace the fixed `MedicalNeed` parameter with an endogenous demand function. In the `Parameters` sheet, add `B9` labeled `DemandElasticity` with value -0.17, the canonical estimate from the RAND Health Insurance Experiment (Manning et al., 1987).

In the `DemandModel` sheet, insert a new column H labeled `EffectivePrice`. In `H2`, calculate the out-of-pocket price faced by the insured individual: `=MedicalPrice * (1 - A2 / (MedicalPrice * MedicalNeed))`. This represents the marginal cost per unit of care after insurance reimbursement. In column I, labeled `QuantityConsumed`, calculate the quantity demanded at the effective price: `=MedicalNeed * (H2 / MedicalPrice)^DemandElasticity` in `I2`, and copy down. This is a constant-elasticity demand curve with reference point at the uninsured price and quantity.

Revise the consumption and utility calculations to use the endogenous quantity. Update column D (`ConsumptionSick`) to: `=Income - B2 - H2 * I2` in `D2`, reflecting that the individual pays the effective price for the quantity consumed. Update column F (`UtilitySick`) to: `=IF(RiskAversionSigma = 1, LN(D2), (D2^(1 - RiskAversionSigma)) / (1 - RiskAversionSigma)) + HealthUtilityWeight * LN(I2)` in `F2`, incorporating the actual quantity consumed into the health utility term.

Re-solve for the optimal insurance payout with moral hazard. The new optimal coverage will be lower than the no-moral-hazard case because the individual internalizes the efficiency loss from overconsumption. Create a scatter chart plotting `InsurancePayout` (x-axis) against `ExpectedUtility` (y-axis) to visualize the utility-maximizing choice. Annotate the chart with the optimal payout under both the fixed-quantity and elastic-demand specifications, demonstrating the quantitative impact of moral hazard on insurance demand.

### Welfare Decomposition and Policy Counterfactuals

Compute the deadweight loss from moral hazard by comparing total surplus under first-best (full insurance with fixed quantity) and second-best (endogenous quantity response) allocations. In cell `N1`, enter `FirstBestUtility`, and in `N2`, reference the maximum expected utility from the fixed-quantity model (before the moral hazard extension). In cell `O1`, enter `SecondBestUtility`, and in `O2`, reference the maximum expected utility with elastic demand. In cell `P1`, enter `WelfareLoss`, and in `P2`, calculate the utility difference: `=N2 - O2`. Convert this utility loss to monetary units using the marginal utility of consumption at the optimal allocation: in cell `Q1`, enter `WelfareLossDollars`, and in `Q2`, approximate `=P2 / (C2^(-RiskAversionSigma))`, where `C2` references the optimal consumption level in the healthy state from the second-best model.

The welfare loss quantifies the efficiency cost of moral hazard as a dollar amount per individual per year. For the baseline calibration, expect a loss on the order of $50 to $150, representing 0.1% to 0.3% of income. This aligns with the RAND findings that moral hazard generates modest but non-negligible welfare costs. Document in `ValidationLog`: "Moral hazard welfare loss = [value], consistent with RAND HIE elasticity-based calculations."

Simulate a policy counterfactual: a government-mandated high-deductible health plan (HDHP) with a $1000 deductible. In the `DemandModel` sheet, insert column J labeled `OutOfPocketHDHP`. In `J2`, calculate: `=MIN(MedicalPrice * I2, 1000) + MAX(0, MedicalPrice * I2 - 1000) * 0.2`, representing full cost up to the deductible, then 20% coinsurance above it. Recalculate consumption in the sick state and expected utility under this cost-sharing structure, and compare to the baseline optimal insurance. The HDHP should reduce moral hazard overconsumption but increase exposure to financial risk, producing an ambiguous welfare effect that depends on risk aversion $\sigma$ and elasticity $\eta$. Run sensitivity analysis by varying $\sigma$ from 1.0 to 3.0 and $\eta$ from -0.1 to -0.3, documenting the parameter regions where HDHPs improve welfare. This forms the empirical basis for policy debates over consumer-directed health plans.

## Exercise 2: Parameter Variation & Empirical Analysis—Adverse Selection in Insurance Markets and Equilibrium Unraveling

This exercise operationalizes the Rothschild-Stiglitz (1976) model of competitive insurance markets under adverse selection, where heterogeneous risk types generate equilibrium pooling, separating, or non-existence outcomes. You will parameterize a two-type model (high-risk and low-risk individuals), simulate insurer competition through zero-profit contract offerings, and trace the boundaries of equilibrium existence as a function of population risk composition. The deliverable is a dynamic spreadsheet model that replicates the canonical graphical analysis in Rothschild-Stiglitz, extended with empirical calibration from actual insurance market risk distributions.

### Model Structure and Equilibrium Concepts

The economy contains two types of individuals: low-risk (type L) with illness probability $p_L$, and high-risk (type H) with illness probability $p_H > p_L$. The population share of high-risk types is $\lambda$. Each type maximizes expected utility $EU = (1-p_i) u(w - \pi) + p_i u(w - \pi - L + I)$, where $w$ is wealth, $L$ is the monetary loss from illness, $\pi$ is the insurance premium, and $I$ is the insurance payout. Insurers observe the distribution of types but cannot identify individual risk ex ante, creating an adverse selection problem.

A competitive equilibrium is a set of insurance contracts $(I_L, \pi_L)$ and $(I_H, \pi_H)$ such that: (1) each contract earns zero expected profit; (2) no individual prefers to deviate to an unserved contract; and (3) no insurer can profitably enter with a contract that attracts a profitable subset of the population. A pooling equilibrium offers a single contract purchased by both types, with premium $\pi^* = (\lambda p_H + (1-\lambda) p_L) I$. A separating equilibrium offers two contracts: full insurance for high-risk types at premium $\pi_H = p_H I_H$, and partial insurance for low-risk types at a premium-coverage pair that high-risk types reject. Rothschild and Stiglitz prove that pooling equilibria generically fail to exist (they are broken by cream-skimming entry), separating equilibria exist only when $\lambda$ is sufficiently large, and no equilibrium exists for intermediate values of $\lambda$.

### Spreadsheet Implementation of the Two-Type Model

Navigate to the `InsuranceEquilibrium` sheet and construct the parameter infrastructure. In the `Parameters` sheet, add the following: `B10` labeled `Wealth` with value 100000; `B11` labeled `LossAmount` with value 30000; `B12` labeled `ProbLowRisk` with value 0.05; `B13` labeled `ProbHighRisk` with value 0.20; `B14` labeled `PopShareHighRisk` with value 0.25; `B15` labeled `RiskAversionSigma` with value 1.5. These parameters approximate a stylized individual health insurance market: a 5% annual probability of a $30,000 medical event for healthy individuals, 20% for those with chronic conditions, and 25% of the population having chronic conditions.

In the `InsuranceEquilibrium` sheet, construct the contract space. In column A, rows 2-102, create a payout grid from 0 to 30000 in increments of 300. Label column B `PremiumPooling` and calculate the pooling premium for each payout: `=(PopShareHighRisk * ProbHighRisk + (1 - PopShareHighRisk) * ProbLowRisk) * A2` in `B2`, and copy down. This is the zero-profit premium when both types purchase the same contract.

Label columns C and D as `UtilityLowRiskPooling` and `UtilityHighRiskPooling`. For each contract, compute the expected utility for each type under the pooling premium. In `C2`: `=(1 - ProbLowRisk) * IF(RiskAversionSigma = 1, LN(Wealth - B2), (Wealth - B2)^(1 - RiskAversionSigma) / (1 - RiskAversionSigma)) + ProbLowRisk * IF(RiskAversionSigma = 1, LN(Wealth - B2 - LossAmount + A2), (Wealth - B2 - LossAmount + A2)^(1 - RiskAversionSigma) / (1 - RiskAversionSigma))`. Copy to `D2` and replace `ProbLowRisk` with `ProbHighRisk`. Copy both formulas down through row 102.

Identify the pooling contract that maximizes low-risk utility (which will also attract high-risk types since they prefer more insurance at the same actuarial price). In cell `E1`, enter `OptimalPoolingPayout`, and in `E2`: `=INDEX(A:A, MATCH(MAX(C:C), C:C, 0))`. In `F1`, enter `OptimalPoolingPremium`, and in `F2`: `=INDEX(B:B, MATCH(MAX(C:C), C:C, 0))`. This is the candidate pooling equilibrium contract.

Test whether this pooling contract is an equilibrium by checking for profitable cream-skimming. An entrant could offer a contract just below the pooling indifference curve for low-risk types, attracting only low risks and earning positive profit. Create a column G labeled `PremiumLowRiskActuarial` with formula `=ProbLowRisk * A2` in `G2`, copying down. This is the actuarially fair premium for low-risk types. If there exists a contract $(I', \pi')$ such that $\pi' = p_L I'$ (zero profit on low risks), low-risk types prefer it to the pooling contract, and high-risk types do not prefer it, then the pooling equilibrium unravels.

Implement the cream-skimming test. In column H labeled `UtilityLowRiskDeviating`, calculate low-risk utility at the actuarially fair contracts: copy the formula from `C2` but replace `B2` with `G2`. In column I labeled `UtilityHighRiskDeviating`, calculate high-risk utility at these same contracts: copy the formula from `D2` but replace `B2` with `G2`. In cell `J1`, enter `PoolingBreaksDown`, and in `J2`, use: `=IF(AND(MAX(H:H) > INDEX(C:C, MATCH(E2, A:A, 0)), INDEX(I:I, MATCH(MAX(H:H), H:H, 0)) < INDEX(D:D, MATCH(E2, A:A, 0))), "YES", "NO")`. This tests whether any low-risk actuarially fair contract Pareto-dominates the pooling contract for low risks while being rejected by high risks.

For the baseline parameters ($\lambda = 0.25$), the test should return "YES", confirming that pooling cannot be an equilibrium. High-risk types impose an externality on low-risk types through premium cross-subsidization, and competitive entry eliminates this cross-subsidy.

### Constructing the Separating Equilibrium

A separating equilibrium requires two distinct contracts: $(I_H, \pi_H)$ offering full insurance to high risks at actuarially fair terms, and $(I_L, \pi_L)$ offering partial insurance to low risks such that high risks weakly prefer their own contract (the incentive compatibility constraint). The high-risk contract is straightforward: $I_H = L = 30000$ and $\pi_H = p_H L$. The low-risk contract must lie on the zero-profit line for low risks ($\pi_L = p_L I_L$) and on the indifference curve of high-risk types through the high-risk contract.

In the `Parameters` sheet, add a manual input cell `B16` labeled `SeparatingPayoutLow` with initial value 20000. This will be adjusted iteratively to satisfy the incentive compatibility constraint. In cell `B17` labeled `SeparatingPremiumLow`, calculate `=ProbLowRisk * B16`. In `B18` labeled `SeparatingPayoutHigh`, enter 30000. In `B19` labeled `SeparatingPremiumHigh`, calculate `=ProbHighRisk * B18`.

In the `InsuranceEquilibrium` sheet, compute the utility of each type under the separating contracts. In cell `K1`, enter `UtilityLowSeparating`, and in `K2`: `=(1 - ProbLowRisk) * IF(RiskAversionSigma = 1, LN(Wealth - SeparatingPremiumLow), (Wealth - SeparatingPremiumLow)^(1 - RiskAversionSigma) / (1 - RiskAversionSigma)) + ProbLowRisk * IF(RiskAversionSigma = 1, LN(Wealth - SeparatingPremiumLow - LossAmount + SeparatingPayoutLow), (Wealth - SeparatingPremiumLow - LossAmount + SeparatingPayoutLow)^(1 - RiskAversionSigma) / (1 - RiskAversionSigma))`. In cell `L1`, enter `UtilityHighFromHighContract`, and calculate high-risk utility from the full-insurance contract. In cell `M1`, enter `UtilityHighFromLowContract`, and calculate high-risk utility from the partial-insurance contract using the same formula structure as `K2` but with `ProbHighRisk`.

The incentive compatibility constraint requires `L2 >= M2`, i.e., high risks weakly prefer their own contract. Use Excel's Goal Seek to find the maximum payout to low risks that satisfies this constraint. Set `M2` equal to `L2` by changing `SeparatingPayoutLow` (B16). Navigate to Data > What-If Analysis > Goal Seek. Set cell `M2`, to value `=L2`, by changing cell `B16`. Execute. The resulting `SeparatingPayoutLow` defines the separating equilibrium low-risk contract.

After Goal Seek converges, verify the equilibrium conditions: (1) both contracts earn zero profit (by construction); (2) each type prefers their own contract (incentive compatibility); (3) low-risk types are worse off than in a hypothetical pooling equilibrium (they bear the separation cost). Compute the welfare loss from adverse selection: in cell `N1`, enter `WelfareGapLowRisk`, and in `N2`: `=INDEX(C:C, MATCH(MAX(C:C), C:C, 0)) - K2`. This is the utility difference between the first-best pooling allocation and the constrained separating allocation. Convert to dollars using the marginal utility approximation as in Exercise 1. The welfare loss should be on the order of 2-5% of wealth for moderate risk aversion, consistent with empirical estimates of adverse selection costs in health insurance markets (Einav et al., 2010).

### Equilibrium Existence and the Critical Population Share

The separating equilibrium exists only when the population share of high-risk types $\lambda$ exceeds a critical threshold. Below this threshold, the low-risk contract required to deter high-risk mimicry involves such severe underinsurance that low risks would prefer to remain uninsured, violating the participation constraint. Trace the boundary of equilibrium existence by varying $\lambda$ and testing whether the separating contracts are feasible.

Create a Data Table in the `InsuranceEquilibrium` sheet. In column O, rows 2-52, enter values of `PopShareHighRisk` from 0.05 to 0.55 in increments of 0.01. In cell `P1`, enter a formula referencing `K2` (utility of low-risk types in the separating equilibrium). In cell `Q1`, reference the utility of low-risk types with no insurance: `=(1 - ProbLowRisk) * IF(RiskAversionSigma = 1, LN(Wealth), (Wealth)^(1 - RiskAversionSigma) / (1 - RiskAversionSigma)) + ProbLowRisk * IF(RiskAversionSigma = 1, LN(Wealth - LossAmount), (Wealth - LossAmount)^(1 - RiskAversionSigma) / (1 - RiskAversionSigma))`.

Highlight the range O1:Q52, navigate to Data > What-If Analysis > Data Table, and set column input cell to `PopShareHighRisk` (B14). Excel will recalculate the separating equilibrium utility for each value of $\lambda$. In column R, compute a binary equilibrium existence indicator: `=IF(P2 > Q2, "EXISTS", "NONE")` in `R2`, copying down. A separating equilibrium exists when low-risk types prefer the separating contract to no insurance.

Create a line chart plotting $\lambda$ (x-axis) against the utility gap `P - Q` (y-axis). The equilibrium existence region corresponds to positive utility gaps. For the baseline parameters, the critical threshold should fall around $\lambda^* \approx 0.15$ to 0.20, meaning that at least 15-20% of the population must be high-risk for a separating equilibrium to exist. Below this threshold, the market features no equilibrium—an unraveling case where no stable contract configuration emerges. This replicates the Rothschild-Stiglitz non-existence theorem and provides a quantitative calibration of the conditions under which insurance markets fail.

### Empirical Calibration to Real Insurance Market Data

Calibrate the model to observed data from the individual health insurance market pre-ACA (before community rating regulations). Use MEPS data to estimate the population risk distribution. Import the 2009 MEPS file (pre-ACA reform) and construct the distribution of total healthcare expenditures `TOTEXP09`. Compute the 75th percentile of expenditures (approximately $5,000) and the 95th percentile (approximately $20,000). Define "high-risk" as individuals in the top 25% of the expenditure distribution, and calibrate `ProbHighRisk` such that $p_H \cdot L$ matches the 95th percentile expenditure, and `ProbLowRisk` such that $p_L \cdot L$ matches the median expenditure among the bottom 75%. This grounds the model in real-world risk heterogeneity.

Estimate the population share $\lambda$ from MEPS by computing the fraction of the sample with chronic conditions (e.g., `CHDDX` for heart disease, `DIABDX` for diabetes). For the 2009 MEPS, this fraction is approximately 0.30. Substitute this empirical $\lambda$ into your model and re-solve for the separating equilibrium. Compare the predicted premium differential between high-risk and low-risk contracts to the observed differential in the pre-ACA individual market (approximately 3:1 to 5:1 for similar coverage levels). Document in `ValidationLog`: "Model premium ratio = [value], observed market ratio = 4.2 (Kaiser Family Foundation 2010), deviation = [X]%."

The calibrated model should predict substantial underinsurance for low-risk types (coverage around 50-70% of the loss) and full insurance for high-risk types, matching the stylized facts of pre-ACA individual insurance: young, healthy individuals purchased high-deductible catastrophic plans while individuals with chronic conditions purchased comprehensive coverage at much higher premiums. This validates the adverse selection framework as a quantitatively relevant description of real insurance markets.

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol—Cost-Effectiveness Analysis and Budget Impact Modeling for Pharmaceutical Adoption

This exercise operationalizes the incremental cost-effectiveness ratio (ICER) framework used by health technology assessment agencies to evaluate new pharmaceuticals and medical devices. You will construct a full cost-effectiveness model comparing a novel therapy to standard-of-care treatment, incorporating probabilistic sensitivity analysis (PSA) to quantify parameter uncertainty, and stress-testing the ICER against alternative assumptions about treatment efficacy, costs, and discount rates. The output is a publication-ready cost-effectiveness model compliant with NICE and ICER methodological guidelines, including a cost-effectiveness acceptability curve (CEAC) and a budget impact analysis for population-level adoption.

### Cost-Effectiveness Framework and QALY Calculation

Cost-effectiveness analysis evaluates the incremental cost per quality-adjusted life year (QALY) gained when adopting a new intervention relative to a comparator. The ICER is defined as:

$$\text{ICER} = \frac{C_{\text{new}} - C_{\text{standard}}}{E_{\text{new}} - E_{\text{standard}}}$$

where $C$ denotes lifetime cost and $E$ denotes lifetime QALYs. A QALY is a health outcome measure combining length of life and quality of life, with utility weights ranging from 0 (death) to 1 (perfect health). Decision-makers compare the ICER to a willingness-to-pay (WTP) threshold—conventionally $50,000 to $150,000 per QALY in the U.S., and £20,000 to £30,000 in the U.K.—to determine cost-effectiveness.

The model structure follows a Markov cohort simulation over a lifetime horizon, tracking a population through discrete health states (e.g., healthy, diseased, post-treatment, dead) with annual transition probabilities, state-specific costs, and state-specific utility weights. Each annual cycle, the cohort accumulates costs and QALYs, discounted at rate $r$ (typically 3% per annum). The model compares the discounted cumulative outcomes under standard-of-care versus the new therapy.

### Spreadsheet Construction of the Markov Model

Navigate to the `CostEffectiveness` sheet and establish the state-transition structure. Define four health states: (1) Disease-Free, (2) Disease Present, (3) Post-Treatment (for the new therapy), (4) Dead. The standard-of-care arm includes only states 1, 2, and 4. The new therapy arm includes all four states, with state 3 representing successful treatment that reduces disease burden.

In the `Parameters` sheet, add the following model inputs: `B20` labeled `AnnualDiscountRate` with value 0.03; `B21` labeled `CohortSize` with value 1000; `B22` labeled `TimeHorizon` with value 30 (years); `B23` labeled `TransitionDiseaseFreeToDiseased` with value 0.05; `B24` labeled `TransitionDiseasedToDeadStandard` with value 0.10; `B25` labeled `TransitionDiseasedToDeadNewTx` with value 0.03; `B26` labeled `TransitionDiseasedToPostTx` with value 0.60 (treatment success rate); `B27` labeled `TransitionPostTxToDiseased` with value 0.02 (relapse rate); `B28` labeled `CostDiseaseFree` with value 500; `B29` labeled `CostDiseased` with value 8000; `B30` labeled `CostPostTx` with value 3000; `B31` labeled `CostNewTxDrug` with value 50000 (one-time treatment cost); `B32` labeled `UtilityDiseaseFree` with value 0.95; `B33` labeled `UtilityDiseased` with value 0.60; `B34` labeled `UtilityPostTx` with value 0.85.

These parameters approximate a chronic disease with moderate baseline mortality (10% annual death rate when diseased under standard care), a high-cost curative therapy that reduces mortality to 3% and transitions 60% of patients to a post-treatment state with improved quality of life, and annual disease management costs. The one-time drug cost of $50,000 is typical for novel biologics or gene therapies.

In the `CostEffectiveness` sheet, create the Markov trace infrastructure. In row 1, label columns: `A1` = "Cycle", `B1` = "DiseaseFree_Standard", `C1` = "Diseased_Standard", `D1` = "Dead_Standard", `E1` = "DiseaseFree_NewTx", `F1` = "Diseased_NewTx", `G1` = "PostTx_NewTx", `H1` = "Dead_NewTx". In column A, rows 2-32, enter cycle numbers 0 through 30.

Initialize the cohort distribution at cycle 0. In row 2: `B2` = `CohortSize`, `C2` = 0, `D2` = 0, `E2` = `CohortSize`, `F2` = 0, `G2` = 0, `H2` = 0. All individuals start disease-free in both arms.

Implement the state transition logic for the standard-of-care arm. In row 3 (cycle 1): 

`B3` = `B2 * (1 - TransitionDiseaseFreeToDiseased)` (disease-free individuals who remain disease-free)

`C3` = `B2 * TransitionDiseaseFreeToDiseased + C2 * (1 - TransitionDiseasedToDeadStandard)` (new diseased plus surviving diseased)

`D3` = `D2 + C2 * TransitionDiseasedToDeadStandard` (cumulative dead)

Copy these formulas down through row 32. This traces the cohort through the standard-of-care pathway, accumulating deaths from disease.

Implement the state transition logic for the new therapy arm, incorporating treatment uptake at cycle 1. In row 3:

`E3` = `E2 * (1 - TransitionDiseaseFreeToDiseased)` (remain disease-free)

`F3` = `E2 * TransitionDiseaseFreeToDiseased * (1 - TransitionDiseasedToPostTx) + G2 * TransitionPostTxToDiseased + F2 * (1 - TransitionDiseasedToPostTx - TransitionDiseasedToDeadNewTx)` (diseased individuals: new cases not treated, relapses from post-treatment, and persistently diseased)

`G3` = `E2 * TransitionDiseaseFreeToDiseased * TransitionDiseasedToPostTx + G2 * (1 - TransitionPostTxToDiseased)` (successfully treated individuals)

`H3` = `H2 + F2 * TransitionDiseasedToDeadNewTx` (cumulative dead under new therapy)

Copy these formulas down through row 32. This model assumes that newly diseased individuals in cycle 1 receive the new therapy with success probability `TransitionDiseasedToPostTx`, and that post-treatment individuals face a low relapse risk.

### Cost and QALY Accumulation with Discounting

Create columns to accumulate annual costs and QALYs for each arm. In column I, label "AnnualCost_Standard". In `I3` (cycle 1), calculate: `=(B3 * CostDiseaseFree + C3 * CostDiseased) / ((1 + AnnualDiscountRate)^A3)`. Copy down through row 32. This discounts state-specific costs to present value.

In column J, label "AnnualQALY_Standard". In `J3`: `=(B3 * UtilityDiseaseFree + C3 * UtilityDiseased) / ((1 + AnnualDiscountRate)^A3)`. Copy down. Each living individual accrues one year of life weighted by utility.

In column K, label "AnnualCost_NewTx". In `K3`: `=(E3 * CostDiseaseFree + F3 * CostDiseased + G3 * CostPostTx + IF(A3 = 1, E2 * TransitionDiseaseFreeToDiseased * TransitionDiseasedToPostTx * CostNewTxDrug, 0)) / ((1 + AnnualDiscountRate)^A3)`. The conditional term adds the one-time drug cost in cycle 1 for treated individuals. Copy down.

In column L, label "AnnualQALY_NewTx". In `L3`: `=(E3 * UtilityDiseaseFree + F3 * UtilityDiseased + G3 * UtilityPostTx) / ((1 + AnnualDiscountRate)^A3)`. Copy down.

Sum the discounted costs and QALYs over the time horizon. In cell `M1`, label "TotalCost_Standard". In `M2`: `=SUM(I3:I32) / CohortSize`. This gives the per-person lifetime cost. In `N1`, label "TotalQALY_Standard". In `N2`: `=SUM(J3:J32) / CohortSize`. In `O1`, label "TotalCost_NewTx". In `O2`: `=SUM(K3:K32) / CohortSize`. In `P1`, label "TotalQALY_NewTx". In `P2`: `=SUM(L3:L32) / CohortSize`.

Calculate the incremental outcomes. In `Q1`, label "IncrementalCost". In `Q2`: `=O2 - M2`. In `R1`, label "IncrementalQALY". In `R2`: `=P2 - N2`. In `S1`, label "ICER". In `S2`: `=Q2 / R2`. This is the incremental cost-effectiveness ratio in dollars per QALY.

For the baseline parameters, the ICER should fall in the range of $70,000 to $120,000 per QALY, depending on the exact calibration of treatment efficacy and costs. Compare to published ICERs for novel oncology or immunology therapies, which typically range from $50,000 to $200,000 per QALY. Document in `ValidationLog`: "Baseline ICER = [value], within range for high-cost biologics per Neumann et al. (2014) meta-analysis."

### Probabilistic Sensitivity Analysis and Cost-Effectiveness Acceptability Curve

Deterministic ICER point estimates ignore parameter uncertainty. Probabilistic sensitivity analysis (PSA) samples each model parameter from its uncertainty distribution, recalculates the ICER for each parameter draw, and summarizes the distribution of ICERs to quantify decision uncertainty. For health technology assessment, PSA is mandatory under NICE and ICER guidelines.

Define uncertainty distributions for key parameters. In the `Parameters` sheet, add columns for PSA: `C20` = "Distribution", `D20` = "Param1", `E20` = "Param2". For `TransitionDiseasedToDeadStandard` (B24), specify: `C24` = "Beta", `D24` = 10 (alpha), `E24` = 90 (beta), representing a Beta(10, 90) distribution with mean 0.10. For `TransitionDiseasedToPostTx` (B26), specify Beta(60, 40) with mean 0.60. For `CostNewTxDrug` (B31), specify Gamma distribution: `C31` = "Gamma", `D31` = 25 (shape), `E31` = 2000 (scale), yielding mean 50,000 and coefficient of variation 0.20. For utility weights, use Beta distributions bounded on [0,1]: `UtilityDiseased` as Beta(18, 12) with mean 0.60.

Implement the Monte Carlo simulation. Create a new sheet `PSA`. In column A, rows 2-1002, label "SimRun" and enter integers 1 through 1000. In columns B through K, draw random parameter samples using Excel's distribution functions. In `B2`: `=BETA.INV(RAND(), 10, 90)` (sampled `TransitionDiseasedToDeadStandard`). In `C2`: `=BETA.INV(RAND(), 60, 40)` (sampled `TransitionDiseasedToPostTx`). In `D2`: `=GAMMA.INV(RAND(), 25, 2000)` (sampled `CostNewTxDrug`). In `E2`: `=BETA.INV(RAND(), 18, 12)` (sampled `UtilityDiseased`). Add similar formulas for all uncertain parameters. Copy the entire row 2 down through row 1002, generating 1000 independent parameter sets.

For each simulation run, recalculate the ICER using the sampled parameters. This requires a VBA macro or a structured reference that updates the base model parameters and retrieves the resulting ICER. If VBA is available, write a macro that loops through each PSA row, substitutes the sampled values into the `Parameters` sheet, triggers recalculation, and writes the resulting ICER into column L of the PSA sheet. If VBA is unavailable, manually copy the PSA parameter rows into the base model and record the ICERs, or use Excel's Data Table function with a custom intermediate calculation sheet.

Assuming the macro populates column L (`ICER_Sampled`), compute summary statistics. In cell `M1`, label "MeanICER". In `M2`: `=AVERAGE(L2:L1002)`. In `N1`, label "MedianICER". In `N2`: `=MEDIAN(L2:L1002)`. In `O1`, label "95thPercentileICER". In `O2`: `=PERCENTILE.INC(L2:L1002, 0.95)`. In `P1`, label "ProbCostEffective_50k". In `P2`: `=COUNTIF(L2:L1002, "<50000") / 1000`. This calculates the probability that the ICER falls below a $50,000/QALY threshold.

Construct the cost-effectiveness acceptability curve (CEAC) by computing the probability of cost-effectiveness across a range of WTP thresholds. In column Q, rows 2-22, enter WTP values from 0 to 200000 in increments of 10000. In column R, calculate the fraction of PSA runs where the ICER is below the corresponding WTP threshold: `=COUNTIF($L$2:$L$1002, "<"&Q2) / 1000` in `R2`, copy down. Create an XY scatter chart with WTP (x-axis) and probability (y-axis). The CEAC visualizes decision uncertainty: a steep curve indicates high confidence in the cost-effectiveness decision, while a flat curve indicates high uncertainty.

For the baseline model, the CEAC should show a probability around 0.60 to 0.75 at a $100,000/QALY threshold, indicating moderate confidence that the new therapy is cost-effective. If the probability falls below 0.50, the therapy is not cost-effective at that threshold on average. Document in `ValidationLog`: "At WTP=$100,000/QALY, probability cost-effective = [value]."

### Stress Testing and Boundary Failure Analysis

Stress-test the ICER under pessimistic assumptions to identify the boundary of cost-effectiveness. Conduct univariate sensitivity analysis on the three most influential parameters: treatment efficacy (`TransitionDiseasedToPostTx`), drug cost (`CostNewTxDrug`), and discount rate (`AnnualDiscountRate`). Create a Tornado diagram showing the impact of each parameter's range on the ICER.

In a new sheet `TornadoDiagram`, list the three parameters in column A. In columns B and C, enter the low and high values for each parameter (e.g., efficacy from 0.40 to 0.80, drug cost from $30,000 to $70,000, discount rate from 0% to 6%). In columns D and E, calculate the ICER at the low and high parameter values by temporarily overriding the base parameter and retrieving the resulting ICER. The spread `|ICER_high - ICER_low|` quantifies parameter influence.

Sort the parameters by descending spread and create a horizontal bar chart with the baseline ICER as the center axis. The Tornado diagram visually identifies which parameters drive uncertainty. For typical pharmaceutical cost-effectiveness models, drug cost and treatment efficacy dominate, while discount rate has moderate impact.

Identify the threshold drug cost at which the ICER exceeds a $100,000/QALY willingness-to-pay. Use Excel's Goal Seek: set the ICER (cell `S2` in `CostEffectiveness`) to 100000 by changing `CostNewTxDrug` (B31). The resulting value is the maximum acceptable drug price under the target cost-effectiveness threshold. For the baseline model, expect a threshold around $40,000 to $55,000. This provides actionable pricing guidance for manufacturers and payers: if the drug is priced above this threshold, it will not meet standard cost-effectiveness criteria without additional evidence of benefit.

Test a scenario where the new therapy is used in combination with standard-of-care rather than as a replacement, increasing total costs but potentially improving efficacy. Duplicate the `CostEffectiveness` sheet and modify the cost structure: in the combination scenario, diseased individuals receive both standard care costs and the new drug cost. Recalculate the ICER. The combination strategy should yield a higher ICER (less cost-effective) unless efficacy gains are proportionally larger. This type of scenario analysis is critical for formulary decisions where multiple treatment lines are available.

### Budget Impact Analysis for Population Adoption

Cost-effectiveness analysis informs coverage decisions, but budget impact analysis (BIA) quantifies the aggregate financial consequences of population-level adoption. BIA projects total healthcare spending over a 3-5 year horizon under alternative adoption scenarios, accounting for market uptake dynamics and displaced standard-of-care costs.

In a new sheet `BudgetImpact`, establish the population framework. In the `Parameters` sheet, add: `B35` labeled `TargetPopulation` with value 500000 (eligible patients nationally); `B36` labeled `YearOneUptake` with value 0.10 (10% market penetration in year one); `B37` labeled `AnnualUptakeGrowth` with value 0.15 (15% compound annual growth). In the `BudgetImpact` sheet, row 1 labels: `A1` = "Year", `B1` = "Uptake_Fraction", `C1` = "Treated_Count", `D1` = "Cost_NewTx_Total", `E1` = "Cost_Standard_Avoided", `F1` = "Net_Budget_Impact".

In column A, rows 2-6, enter years 1 through 5. In `B2`: `=YearOneUptake`. In `B3`: `=B2 * (1 + AnnualUptakeGrowth)`, copy down through `B6`. In `C2`: `=TargetPopulation * B2`, copy down. In `D2`, calculate the total cost of treating the uptake cohort with the new therapy: `=C2 * (CostNewTxDrug / (1 + AnnualDiscountRate)^A2)`, copy down. In `E2`, calculate the avoided standard-of-care costs for the treated cohort (approximate as five years of disease management): `=C2 * 5 * CostDiseased / (1 + AnnualDiscountRate)^A2`, copy down. In `F2`: `=D2 - E2`, copy down. This is the net budget impact per year.

Sum the net budget impact over the five-year horizon. In cell `G1`, label "TotalBudgetImpact". In `G2`: `=SUM(F2:F6)`. For the baseline parameters, the total budget impact should be on the order of $1 to $3 billion over five years, depending on the uptake assumptions and population size. This magnitude is typical for novel specialty pharmaceuticals entering large patient populations.

Conduct threshold analysis on uptake rates. Create a Data Table varying `YearOneUptake` from 0.05 to 0.30 and computing the resulting `TotalBudgetImpact`. Plot uptake rate (x-axis) against budget impact (y-axis). This curve informs payer negotiations: if the manufacturer offers a price discount conditional on volume commitments, the payer can use this analysis to project financial exposure under different utilization scenarios.

Integrate the budget impact findings with the cost-effectiveness results. In cell `H1`, label "BudgetImpactPerQALY". In `H2`: `=G2 / (C6 * IncrementalQALY)`. This metric expresses the aggregate budget impact per QALY gained across the entire treated population, providing a population-level cost-effectiveness perspective. Document in `ValidationLog`: "Five-year budget impact = [value], per-QALY population cost = [value]."

## Operational Reference Guide & Diagnostic Checklist

This section consolidates the technical protocols, parameter sources, and validation standards required for operational deployment of health economics models in policy and industry settings. Use this guide as a reference when constructing new models, auditing existing analyses, or responding to regulatory queries.

### Parameter Calibration Standards and Data Sources

Every model parameter must be traceable to a primary data source or published estimate. Maintain a parameter log in the `ValidationLog` sheet with the following fields: Parameter Name, Value, Source (citation), Date Accessed, Confidence Level (High/Medium/Low), and Sensitivity Tested (Yes/No). High-confidence parameters derive from meta-analyses, large randomized controlled trials, or national datasets with sample sizes exceeding 10,000. Medium-confidence parameters come from single-study estimates or administrative data with known limitations. Low-confidence parameters rely on expert opinion or indirect evidence and require extensive sensitivity analysis.

For demand elasticities, prioritize estimates from the RAND Health Insurance Experiment (Manning et al., 1987, Journal of Health Economics), which provides the canonical -0.17 price elasticity for outpatient care. For inpatient care, use -0.05 to -0.10. For pharmaceuticals, elasticities range from -0.20 to -0.40 depending on therapeutic class. For chronic conditions with few substitutes (e.g., insulin), use the lower bound.

For utility weights, source EQ-5D index values from published catalogs such as Sullivan et al. (2006, Medical Care) or the Cost-Effectiveness Analysis Registry at Tufts Medical Center. Disease-specific utilities: diabetes without complications (0.85), diabetes with complications (0.70), end-stage renal disease (0.50), post-myocardial infarction (0.75), advanced cancer (0.40). When EQ-5D data are unavailable, convert SF-6D or HUI3 scores using published mapping algorithms.

For transition probabilities in Markov models, extract hazard rates from survival curves in clinical trial publications or cohort studies. Convert cumulative survival functions to annual transition probabilities using the formula $p = 1 - S(t)^{1/t}$, where $S(t)$ is the survival probability at time $t$. When only median survival is reported, assume exponential survival and calculate the annual death rate as $\lambda = \ln(2) / \text{median}$.

For costs, distinguish between charges (list prices) and actual payments (reimbursement rates). Use Medicare fee schedules for provider costs, average wholesale price (AWP) minus standard discounts for pharmaceuticals, and DRG (diagnosis-related group) weights for hospitalizations. Adjust all costs to current dollars using the medical care component of the Consumer Price Index (CPI-M), not the general CPI. The Bureau of Labor Statistics publishes annual CPI-M inflation factors.

### Model Validation Checklist

Execute the following validation steps before presenting or publishing any health economics model:

**Internal Consistency Tests:**
- Budget constraints bind at optimum in all consumer choice models
- Probability weights sum to 1.0 in all Markov states (row sums of transition matrices equal 1.0)
- Discounted outcomes monotonically decrease over time (no spurious future cost or QALY spikes)
- Expected utility increases with wealth and decreases with risk for all parameterizations
- Demand curves slope downward over the entire price range tested
- Insurance coverage monotonically increases with risk aversion holding prices constant

**Face Validity Against Empirical Benchmarks:**
- Total healthcare expenditure as percentage of GDP: U.S. baseline 18% (2022), OECD average 9%, model baseline should match national context
- Insurance coverage rates: U.S. employer-sponsored 55%, individual market 7%, Medicaid 18%, Medicare 15%, uninsured 10% (pre-ACA 15%)
- Out-of-pocket spending: average $1,200 annually per capita, top quartile $5,000+
- Hospital days per 1,000 population: 550-650 in U.S., 700-900 in high-utilization countries
- Prescription drug spending per capita: $1,300 in U.S., $500-700 in peer nations

**Comparative Statics Directional Tests:**
- Increasing price reduces quantity demanded (negative elasticity)
- Increasing income increases insurance coverage (normal good)
- Increasing risk aversion increases willingness-to-pay for insurance
- Increasing loading factor reduces insurance coverage
- Increasing coinsurance rate reduces utilization (moral hazard)
- Increasing subsidy increases coverage (participation response)

**Sensitivity Analysis Robustness:**
- Vary each parameter individually by ±20% and confirm qualitative results unchanged
- Test worst-case and best-case joint parameter scenarios
- Identify parameters to which results are most sensitive (elasticity > 0.5) and flag for additional data collection
- Confirm that ICERs remain within ±50% of baseline under univariate sensitivity for non-influential parameters

### Regulatory and Reporting Standards

When preparing cost-effectiveness models for submission to NICE, ICER, or other health technology assessment bodies, comply with the following reporting standards derived from the Consolidated Health Economic Evaluation Reporting Standards (CHEERS) checklist:

**Structural Requirements:**
- Model type (decision tree, Markov cohort, discrete event simulation, individual-level microsimulation) explicitly stated with justification
- Time horizon justified with reference to disease natural history and treatment effect duration
- Cycle length justified (typically one year for chronic diseases, one month for acute events)
- Discount rate explicitly stated (3% base case, 0% and 5% in sensitivity analysis per NICE reference case)
- Half-cycle correction applied when appropriate (first and last cycles contribute 0.5× the per-cycle outcome)

**Parameter Transparency:**
- All model parameters presented in a summary table with point estimates, uncertainty ranges, and sources
- Deterministic sensitivity analysis on all uncertain parameters, typically testing 95% confidence intervals
- Probabilistic sensitivity analysis with 1,000+ iterations, reported as mean ICER, median ICER, and cost-effectiveness acceptability curve
- Structural uncertainty addressed through scenario analysis (alternative model structures, alternative comparators)

**Result Presentation:**
- Incremental cost-effectiveness plane (scatter plot of incremental cost vs. incremental QALYs from PSA)
- Cost-effectiveness acceptability curve (probability cost-effective vs. willingness-to-pay threshold)
- Expected value of perfect information (EVPI) to quantify the value of eliminating parameter uncertainty
- Budget impact analysis over 3-5 years with explicit market uptake assumptions

**Subgroup Analysis:**
- Stratify results by clinically relevant subgroups (age, disease severity, comorbidities) when treatment effects are heterogeneous
- Report separate ICERs for each subgroup and test for statistical interaction
- Avoid post-hoc subgroup mining; pre-specify subgroups based on biological plausibility

### Common Modeling Pitfalls and Recovery Protocols

**Failure Mode 1: Negative Incremental QALYs**
Symptom: The new therapy yields fewer QALYs than standard-of-care, producing a negative denominator in the ICER.
Root Cause: Typically arises from treatment-related adverse events that reduce quality of life more than the disease benefits gained.
Recovery Protocol: Calculate the incremental net monetary benefit (INMB) instead of the ICER: $\text{INMB} = \lambda \cdot \Delta E - \Delta C$, where $\lambda$ is the willingness-to-pay threshold. INMB handles negative incremental QALYs without producing undefined ratios. Report INMB alongside the ICER and state that the therapy is "dominated" (more costly and less effective).

**Failure Mode 2: ICER Exceeds $500,000 per QALY**
Symptom: The calculated ICER is orders of magnitude above conventional cost-effectiveness thresholds.
Root Cause: Drug cost too high, treatment efficacy too low, or inappropriate comparator (should compare to best available alternative, not placebo).
Recovery Protocol: Conduct threshold analysis to identify the maximum drug price yielding an acceptable ICER. If no plausible price achieves cost-effectiveness, report that the therapy does not meet cost-effectiveness criteria under current evidence. Propose value-based pricing: $P_{\text{max}} = \lambda \cdot \Delta E + C_{\text{comparator}} - C_{\text{administration}}$, where $\lambda$ is the WTP threshold and $C_{\text{administration}}$ captures additional costs of delivering the new therapy.

**Failure Mode 3: Markov Trace Does Not Sum to Cohort Size**
Symptom: The sum of individuals across all states in a given cycle does not equal the initial cohort size (excluding cumulative deaths).
Root Cause: Transition probabilities do not sum to 1.0 for at least one state, or absorbing states (e.g., dead) incorrectly allow transitions out.
Recovery Protocol: Audit the transition probability matrix. For each row (each originating state), sum the transition probabilities to all destination states, including remaining in the same state. This sum must equal 1.0. Adjust the "remain in state" probability as a residual: $p_{ii} = 1 - \sum_{j \neq i} p_{ij}$. Verify that the "Dead" state has a 1.0 probability of transitioning to itself and 0.0 to all other states.

**Failure Mode 4: PSA Mean ICER Differs Substantially from Deterministic ICER**
Symptom: The mean ICER from probabilistic sensitivity analysis is 20%+ different from the deterministic (point estimate) ICER.
Root Cause: Nonlinearities in the model structure interact with parameter uncertainty, particularly when parameters are correlated or the model includes thresholds (e.g., survival only improves if response exceeds 50%).
Recovery Protocol: Investigate parameter correlations. If clinical efficacy and cost are negatively correlated (higher efficacy implies higher intensity of care), impose this correlation in the PSA by sampling from a multivariate distribution. Use Cholesky decomposition to generate correlated normal samples, then transform to the target marginal distributions. Re-run PSA with correlated parameters and check if the mean ICER converges to the deterministic value. If the discrepancy persists, report both the deterministic and probabilistic mean ICERs and provide a narrative explanation of the nonlinearity driving the difference.

**Failure Mode 5: Budget Impact Implausibly Large Relative to National Health Expenditure**
Symptom: The five-year budget impact exceeds 5% of annual national health expenditure.
Root Cause: Unrealistic market uptake assumptions, failure to account for displaced costs, or double-counting of costs already included in disease management.
Recovery Protocol: Disaggregate the budget impact into components: new therapy acquisition cost, administration cost, monitoring cost, and displaced standard-of-care cost. Verify that displaced costs fully account for all services no longer needed when patients switch to the new therapy (e.g., if the new therapy prevents hospitalizations, subtract avoided hospitalization costs). Recalibrate uptake assumptions against historical adoption curves for similar therapies. For blockbuster drugs, peak market share rarely exceeds 30-40% of the eligible population within five years. Impose a logistic uptake curve rather than linear growth.

### Practical Workflow for Real-World Consulting Engagements

When commissioned to perform a health economic evaluation for a pharmaceutical client, regulatory agency, or payer, follow this operational workflow:

**Week 1: Problem Definition and Data Acquisition**
- Define the decision problem: payer perspective, time horizon, comparator therapy, target population
- Identify all relevant clinical evidence: pivotal trials, real-world evidence, long-term extension studies
- Obtain patient-level data if available, or extract aggregate statistics from published literature
- Compile cost data: drug acquisition cost, administration costs, monitoring costs, adverse event management costs
- Assemble utility weights from published catalogs or elicit from patients if primary data collection is feasible

**Week 2: Model Construction and Calibration**
- Build the structural model (decision tree or Markov) with transparent state definitions and transition logic
- Implement the model in Excel with clear separation of parameters, calculations, and outputs
- Calibrate the model to reproduce the observed outcomes from the pivotal trial (internal validation)
- Extrapolate beyond the trial horizon using external data sources (e.g., disease registries, natural history studies)

**Week 3: Base Case Analysis and Deterministic Sensitivity Analysis**
- Execute the base case analysis with point estimate parameters
- Calculate the incremental cost, incremental QALYs, and ICER
- Perform univariate sensitivity analysis on all parameters, generating a Tornado diagram
- Identify the three most influential parameters and flag for probabilistic analysis

**Week 4: Probabilistic Sensitivity Analysis and Scenario Analysis**
- Assign uncertainty distributions to all model parameters
- Execute 1,000-iteration Monte Carlo simulation
- Generate the cost-effectiveness plane and acceptability curve
- Conduct scenario analyses: alternative comparators, alternative time horizons, subgroup analyses

**Week 5: Budget Impact Analysis and Reporting**
- Project market uptake over 3-5 years with justification
- Calculate annual and cumulative budget impact from payer perspective
- Identify budget impact per capita and per member per month (PMPM) for insurance plan context
- Prepare final report with executive summary, methods, results, limitations, and conclusions

The final deliverable includes: (1) a comprehensive written report (30-50 pages) following CHEERS guidelines, (2) a fully documented Excel model with audit trail, (3) a slide deck for stakeholder presentation (15-20 slides), and (4) appendices with all data sources, literature citations, and sensitivity analysis tables. The Excel model must be unlocked and formula-auditable to allow independent verification by the commissioning party.
