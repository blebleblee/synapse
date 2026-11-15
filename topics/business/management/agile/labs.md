# Operational Verification Labs: Agile

## Objective & Operational Lab Setup

This laboratory guide operationalizes Agile management as a measurable, instrumented system rather than a philosophical posture. Every exercise in this guide treats Agile ceremonies, artifacts, and metrics as engineering inputs to a delivery pipeline whose throughput, quality, and predictability can be quantified, stress-tested, and iteratively improved. The objective is to move you from a conceptual understanding of Scrum, Kanban, and hybrid frameworks into hands-on facility with the quantitative models that actually govern sprint commitments, flow efficiency, release forecasting, and empirical process control.

The lab environment is an analytical workspace built around quantitative spreadsheets. You will need a spreadsheet application with formula support, statistical functions, and charting capabilities (Google Sheets, Microsoft Excel, or LibreOffice Calc all suffice). Each exercise below provides exact cell references, formulas, and parameter values so that you can construct working models from scratch with zero ambiguity. Where statistical methods are invoked—A/B test sample sizing, Monte Carlo delivery simulation, cohort retention analysis—you will implement them directly in the spreadsheet using native functions, not rely on black-box tools.

Before beginning, set up a workbook named `Agile_Lab_Master.xlsx` with the following sheet tabs: `Backlog_RICE`, `Sprint_Planning`, `Velocity_Tracker`, `Burndown_Calculator`, `Kanban_WIP_Model`, `AB_Test_Sample_Size`, `Cohort_Retention`, `Monte_Carlo_Forecast`, and `Diagnostic_Rubric`. These sheets will be populated progressively across the three exercises. Each sheet operates as a self-contained model but references others where data flow is intentional, mirroring how Agile artifacts feed one another in a real delivery organization.

The theoretical backbone of this guide is empirical process control, the foundational principle that underpins all Agile frameworks. Empirical process control demands three conditions: transparency (work items, progress, and impediments are visible to all stakeholders), inspection (progress toward goals is checked frequently at regular intervals), and adaptation (processes are adjusted when inspection reveals deviation from acceptable limits). Every model you build in these labs is an instantiation of one or more of these conditions. Velocity tracking is transparency. Burndown analysis is inspection. Sprint retrospective action items and WIP limit adjustments are adaptation. By the end of these labs, you will have a complete, reusable analytical toolkit for instrumenting an Agile delivery system and diagnosing its failure modes under stress.

---

## Exercise 1: Foundational Practical Implementation

### Lab 1A: Backlog Prioritization with RICE Scoring

The first operational task in any Agile system is producing a prioritized backlog. Prioritization is not a subjective consensus exercise; it is a quantified scoring problem where competing initiatives are evaluated along consistent dimensions and ranked by a composite score. The RICE framework—Reach, Impact, Confidence, Effort—is one of the most operationally rigorous prioritization models because each input is independently estimable and the composite score is mechanically reproducible across teams.

Navigate to the `Backlog_RICE` sheet. Build the model as follows.

In row 1, enter the column headers across columns A through G: `Feature`, `Reach (users/qtr)`, `Impact Score (0-3)`, `Confidence (%)`, `Effort (person-sprints)`, `RICE Score`, `Rank`. In row 2, enter your first feature candidate. We will populate ten realistic backlog items to create a working prioritization matrix.

| Row | Feature | Reach | Impact | Confidence | Effort |
|-----|--------|-------|--------|------------|--------|
| 2 | SSO Integration for Enterprise | 4500 | 3 | 80% | 6 |
| 3 | In-App Onboarding Tour | 12000 | 2 | 70% | 3 |
| 4 | API Rate Limiting | 800 | 3 | 90% | 2 |
| 5 | Mobile Push Notifications | 9000 | 2 | 60% | 4 |
| 6 | Audit Log Export | 1500 | 1 | 95% | 2 |
| 7 | Dark Mode | 20000 | 1 | 50% | 5 |
| 8 | Bulk User Provisioning API | 3000 | 3 | 85% | 4 |
| 9 | Churn Prediction Dashboard | 2000 | 3 | 40% | 8 |
| 10 | Payment Method Vault | 5000 | 2 | 75% | 5 |
| 11 | Webhook Retry Queue | 3500 | 2 | 90% | 3 |

The RICE score formula is mechanically simple but its inputs encode deep product judgment. Reach is the number of users affected per quarter. Impact is scored on a 0–3 scale where 0.25 is minimal, 1 is low, 2 is medium, and 3 is massive—this is a categorical estimate of how much the feature will move the target metric per affected user. Confidence is a percentage representing how certain you are in your Reach and Impact estimates, with 100% meaning high-confidence measured data and 50% meaning pure gut estimate. Effort is the total person-sprints required across all disciplines (engineering, design, QA, PM). The composite score divides Reach × Impact × Confidence by Effort, producing a single number that rewards high-reach, high-impact, high-confidence, low-effort work.

In cell F2, enter the formula: `=(B2 * C2 * D2) / E2`. Copy this formula down through F11. In cell G2, enter: `=RANK(F2, $F$2:$F$11)` and copy down through G11. Your resulting RICE scores and ranks will look like this:

| Feature | RICE Score | Rank |
|---------|-----------|------|
| SSO Integration | 1800 | 2 |
| In-App Onboarding | 5600 | 1 |
| API Rate Limiting | 1080 | 3 |
| Mobile Push Notifications | 2700 | 4 |
| Audit Log Export | 712.5 | 7 |
| Dark Mode | 2000 | 5 |
| Bulk Provisioning API | 1912.5 | 3 |
| Churn Prediction Dashboard | 300 | 10 |
| Payment Method Vault | 1500 | 6 |
| Webhook Retry Queue | 2100 | 4 |

The exercise here is not merely computing scores but interrogating them. In-App Onboarding ranks first because it reaches 12,000 users per quarter with moderate impact at modest effort. SSO Integration ranks second despite reaching fewer users because its massive impact score (3) and high confidence (80%) compound against a moderate effort estimate. Churn Prediction Dashboard ranks last not because it lacks value—it has a massive potential impact—but because the confidence is only 40% and the effort is 8 person-sprints, making it the highest-risk, highest-cost item. This is the core insight RICE delivers: it surfaces the asymmetry between value and cost-of-certainty, forcing the team to either invest in reducing uncertainty or defer the work.

To complete this lab, perform a sensitivity analysis. Change the Confidence value for Churn Prediction Dashboard from 40% to 80% (cell D9) and observe that its RICE score rises from 300 to 600, still ranking last. Now reduce its Effort from 8 to 3 (cell E9) and observe the score jumps to 1,600, ranking it 5th. This demonstrates that for high-impact, high-uncertainty features, the most productive next action is often a spike or proof-of-concept that reduces Effort estimates and increases Confidence simultaneously, rather than committing to full delivery.

### Lab 1B: Sprint Planning, Velocity Tracking, and Commitment Modeling

Navigate to the `Velocity_Tracker` sheet. This model captures the empirical foundation of sprint commitment: historical velocity is the only defensible basis for sprint capacity planning, and it must be tracked with statistical rigor rather than single-point averages.

Set up the sheet with the following columns in row 1: `Sprint #`, `Committed Story Points`, `Completed Story Points`, `Carried Over SP`, `Team Size`, `Avg Velocity (rolling 3)`, `Velocity StdDev`, `Upper Control Limit`, `Lower Control Limit`. Populate rows 2 through 11 with the following ten sprints of historical data for a 7-person cross-functional team:

| Sprint | Committed | Completed | Carried | Team Size |
|--------|-----------|-----------|--------|-----------|
| 1 | 55 | 48 | 7 | 7 |
| 2 | 52 | 50 | 2 | 7 |
| 3 | 50 | 46 | 4 | 6 |
| 4 | 48 | 52 | 0 | 7 |
| 5 | 54 | 49 | 5 | 7 |
| 6 | 51 | 44 | 7 | 5 |
| 7 | 45 | 42 | 3 | 6 |
| 8 | 47 | 51 | 0 | 7 |
| 9 | 53 | 47 | 6 | 7 |
| 10 | 49 | 50 | 0 | 7 |

In cell F4 (the rolling 3-sprint average for Sprint 3), enter: `=AVERAGE(C2:C4)`. Copy this down through F11. This rolling average smooths single-sprint variance and provides a more stable planning baseline. In cell G4, enter: `=STDEV(C2:C4)` and copy down through G11. The standard deviation quantifies how much sprint-to-sprint throughput varies, which is the single most important number for assessing planning reliability.

In cell H4, enter the upper control limit formula: `=F4 + (2 * G4)`. In cell I4, enter the lower control limit: `=F4 - (2 * G4)`. Copy both down through row 11. Using two standard deviations above and below the rolling mean creates a 95% confidence band. Any sprint that completes story points outside this band is a statistically significant outlier, not random variation, and warrants root-cause analysis in the retrospective.

After computing, your Sprint 10 values will be: rolling average velocity = 49.33, standard deviation = 2.05, upper control limit = 53.43, lower control limit = 45.23. This tells the team that, at current performance levels, they can reliably commit to 45 story points and expect to complete them with 95% confidence. Committing to 49–50 is the expected outcome but with reduced certainty. Committing above 53 enters statistically improbable territory and will likely result in carry-over.

Navigate to the `Sprint_Planning` sheet. This is the operative model that converts velocity data into a sprint commitment. In row 1, enter: `Story ID`, `Feature`, `Story Points`, `Priority`, `Cumulative SP`, `Within Capacity?`. Set cell B1's adjacent cell (we will use cell J1) as `Available Capacity` and in J2 enter: `=MIN('Velocity_Tracker'!I11, 'Velocity_Tracker'!F11)`. This formula selects the lesser of the lower control limit and the rolling average, giving you a conservative, defensible sprint capacity.

Populate the sprint backlog with the following candidate stories, ordered by RICE priority rank from Lab 1A:

| Story ID | Feature | Story Points | Priority |
|----------|---------|-------------|----------|
| S-001 | In-App Onboarding Tour | 8 | P0 |
| S-002 | In-App Onboarding Tour | 5 | P0 |
| S-003 | SSO Integration | 8 | P0 |
| S-004 | SSO Integration | 3 | P0 |
| S-005 | API Rate Limiting | 5 | P1 |
| S-006 | API Rate Limiting | 5 | P1 |
| S-007 | Mobile Push Notifications | 8 | P1 |
| S-008 | Dark Mode | 13 | P2 |
| S-009 | Audit Log Export | 5 | P2 |
| S-010 | Payment Method Vault | 8 | P2 |

In cell E2, enter: `=C2`. In cell E3, enter: `=E2 + C3`. Copy E3 down through E11. This cumulative story point total is the mechanism for capacity fit. In cell F2, enter: `=IF(E2 <= $J$2, "YES", "NO")` and copy down. With a capacity of approximately 45, the model will show stories S-001 through S-007 fitting within capacity (cumulative 42) and S-008 (cumulative 55) exceeding it. The sprint commitment is therefore stories S-001 through S-007, totaling 42 story points, which sits comfortably within the lower control limit of 45.23.

The operational insight here is that sprint planning is a constrained optimization problem. You are maximizing delivered value (proxied by RICE rank order) subject to a capacity constraint (derived from statistical velocity analysis). The cumulative story point column is the constraint-binding mechanism, and the `Within Capacity?` flag is the go/no-go gate for each story.

### Lab 1C: Burndown Chart Construction and Interpretation

Navigate to the `Burndown_Calculator` sheet. A sprint burndown chart plots remaining work against the ideal linear completion trajectory, making deviation from plan visible at daily granularity. This is the core inspection instrument of empirical process control within a sprint.

In row 1, enter: `Day`, `Date`, `Ideal Burndown`, `Actual Remaining SP`, `Variance`, `Status Flag`. The sprint is 10 working days (two-week sprint, Monday through Friday of week 1 and week 2). The total committed story points are 42 (from Lab 1B).

In cell A2, enter `0` and in A3 enter `1`. Select both cells and drag-fill down to A12, producing days 0 through 10. In cell C2, enter the ideal burndown starting point: `=42`. In cell C3, enter: `=$C$2 - ((ROW()-2) * ($C$2 / 10))`. This formula computes the ideal linear burndown: on day 0, 42 remain; on day 10, 0 remain; each day should burn 4.2 story points. Copy C3 down through C12.

For the actual burndown, enter the following realistic daily remaining story points, which represent a sprint where the team front-loads complexity and experiences a mid-sprint slowdown before recovering:

| Day | Actual Remaining |
|-----|-----------------|
| 0 | 42 |
| 1 | 39 |
| 2 | 35 |
| 3 | 33 |
| 4 | 32 |
| 5 | 28 |
| 6 | 24 |
| 7 | 18 |
| 8 | 10 |
| 9 | 4 |
| 10 | 0 |

In cell E2, enter: `=D2 - C2` and copy down through E12. This variance column shows how many story points above or below ideal the team is at each daily checkpoint. In cell F2, enter: `=IF(E2 > 2, "BEHIND", IF(E2 < -2, "AHEAD", "ON TRACK"))` and copy down. The threshold of ±2 story points creates a tolerance band; variance within this band is normal execution noise, while variance exceeding it signals a material deviation that should trigger a mid-sprint corrective action.

The burndown you just constructed reveals a specific narrative. Days 1–3 show the team ahead of or near ideal pace (variances of -3, -2, -1), suggesting the initial stories were smaller than estimated. Day 4 shows a stall (variance of +2.2), which is the first warning signal. Days 5–7 show acceleration back toward ideal. Days 8–10 show the team pulling ahead and completing all work by sprint end. The burndown chart's value is not in the final outcome—it is in the daily visibility it provides, allowing a Scrum Master to detect the day-4 stall in real time and investigate whether an impediment, estimation error, or scope creep is the cause.

Create a line chart with Day on the X-axis and both Ideal Burndown and Actual Remaining SP as series. The visual intersection pattern—actual line dropping below ideal, rising above it, then converging to zero—is the diagnostic pattern that distinguishes a healthy sprint from one masking problems.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Lab 2A: Kanban WIP Limit Optimization and Flow Efficiency Modeling

Kanban replaces time-boxed sprints with continuous flow, governed by Work In Progress (WIP) limits that constrain the number of items in each workflow state. The fundamental theorem of Kanban, derived from queueing theory and Little's Law, is that average lead time equals WIP divided by average throughput. This relationship means that reducing WIP directly reduces lead time, but it also reduces resource utilization, creating a trade-off that must be optimized empirically rather than assumed.

Navigate to the `Kanban_WIP_Model` sheet. In row 1, enter: `WIP Limit`, `Avg Throughput (items/day)`, `Avg Lead Time (days)`, `Flow Efficiency (%)`, `Utilization (%)`, `Optimal?`. We will model five WIP limit configurations for a team with the following workflow states: Backlog, In Dev, In Review, In QA, Done. The team's measured average throughput at various WIP levels is:

| WIP Limit | Throughput | Flow Efficiency |
|-----------|-----------|-----------------|
| 3 | 1.8 | 85% |
| 5 | 2.5 | 78% |
| 7 | 2.9 | 65% |
| 10 | 2.8 | 48% |
| 15 | 2.6 | 32% |

Flow efficiency is the ratio of active work time to total lead time—the percentage of time a work item is actively being worked on versus sitting in a queue waiting for the next stage. High WIP limits increase queue depth, which inflates lead time and collapses flow efficiency even as throughput may remain stable.

In cell C2, enter the Little's Law computation: `=A2 / B2`. This gives you average lead time as WIP divided by throughput. Copy down through C6. In cell E2, enter the utilization formula: `=B2 / MAX($B$2:$B$6)` and format as percentage. Copy down. In cell F2, enter: `=IF(AND(B2=MAX($B$2:$B$6), C2=MIN($C$2:$C$6)), "OPTIMAL", "")`. Copy down.

Your computed results will be:

| WIP Limit | Throughput | Lead Time | Flow Efficiency | Utilization | Optimal? |
|-----------|-----------|-----------|-----------------|-------------|----------|
| 3 | 1.8 | 1.67 | 85% | 62% | |
| 5 | 2.5 | 2.00 | 78% | 86% | |
| 7 | 2.9 | 2.41 | 65% | 100% | OPTIMAL |
| 10 | 2.8 | 3.57 | 48% | 97% | |
| 15 | 2.6 | 5.77 | 32% | 90% | |

The model reveals the critical Kanban optimization insight: throughput peaks at WIP=7 (2.9 items/day) but lead time at that level is 2.41 days with only 65% flow efficiency. At WIP=5, throughput is 86% of maximum but lead time drops to 2.0 days and flow efficiency rises to 78%. The "optimal" designation flags WIP=7 because it maximizes throughput, but a practitioner must weigh whether the 15% throughput gain from WIP 5→7 is worth the 20% lead time increase and 13% flow efficiency degradation. In most B2B product contexts where predictability matters more than raw throughput, WIP=5 is the superior operating point.

To make this trade-off explicit, add a composite scoring column. In cell G1, enter `Composite Score`. In cell G2, enter: `=(B2 / MAX($B$2:$B$6)) * 0.4 + (1 - C2 / MAX($C$2:$C$6)) * 0.3 + (D2 / 100) * 0.3`. This weights throughput at 40%, lead time (inverted, so lower is better) at 30%, and flow efficiency at 30%. Copy down. The scores will be:

| WIP | Composite Score |
|-----|----------------|
| 3 | 0.770 |
| 5 | 0.861 |
| 7 | 0.807 |
| 10 | 0.657 |
| 15 | 0.493 |

Under this weighting, WIP=5 scores highest at 0.861, confirming the practitioner intuition that a moderate WIP limit balances throughput against lead time and flow quality better than the throughput-maximizing point. The exercise demonstrates that Kanban WIP optimization is not about maximizing any single metric but about finding the Pareto-efficient operating point across a multi-dimensional trade-off space.

### Lab 2B: A/B Test Sample Size Calculation and Statistical Significance Verification

Agile teams ship incrementally, and each increment should be validated through controlled experiments. The statistical machinery of A/B testing is therefore a core Agile operational skill, not a specialized analytics function. You must be able to calculate the minimum sample size required to detect a meaningful effect before launching an experiment, and you must be able to verify significance after data is collected.

Navigate to the `AB_Test_Sample_Size` sheet. In row 1, enter: `Parameter`, `Value`, `Formula Reference`. We will compute the sample size for a two-proportion z-test, the standard test for comparing conversion rates between a control and treatment group.

Enter the following parameters:

| Parameter | Value |
|-----------|-------|
| Baseline Conversion Rate (p1) | 0.12 |
| Minimum Detectable Effect (MDE) | 0.03 |
| Treatment Conversion Rate (p2) | 0.15 |
| Significance Level (alpha) | 0.05 |
| Statistical Power (1 - beta) | 0.80 |
| Z-score (alpha/2, two-tailed) | 1.96 |
| Z-score (beta, one-tailed) | 0.8416 |

The minimum detectable effect of 3 percentage points means we want to reliably detect if the treatment improves conversion from 12% to at least 15%. The significance level of 0.05 is the probability of a false positive (declaring a winner when there is none). Statistical power of 0.80 is the probability of detecting a true effect of the specified size—conventionally, 80% power is the minimum acceptable threshold, meaning we accept a 20% chance of a false negative (failing to detect a real effect).

The sample size formula for a two-proportion z-test per group is:

n = (Z_α/2 × √(2 × p̄ × (1 − p̄)) + Z_β × √(p1 × (1 − p1) + p2 × (1 − p2)))² / (p2 − p1)²

where p̄ = (p1 + p2) / 2 is the pooled conversion rate.

In the spreadsheet, assign the following cell references: B2 = 0.12 (p1), B3 = 0.03 (MDE), B4 = 0.15 (p2), B5 = 0.05 (alpha), B6 = 0.80 (power), B7 = 1.96 (Z_alpha/2), B8 = 0.8416 (Z_beta). In cell B9, enter the pooled rate: `=(B2 + B4) / 2`. In cell B10, enter the numerator computation: `=(B7 * SQRT(2 * B9 * (1 - B9)) + B8 * SQRT(B2 * (1 - B2) + B4 * (1 - B4)))^2`. In cell B11, enter the denominator: `=(B4 - B2)^2`. In cell B12, enter the per-group sample size: `=B10 / B11`. In cell B13, enter the total sample size (both groups): `=B12 * 2`.

The computed per-group sample size will be approximately 2,476, and the total sample size will be approximately 4,952. This means that to reliably detect a 3-percentage-point improvement in conversion rate from a 12% baseline, you need roughly 4,952 total users split evenly between control and treatment. If your daily traffic is 500 users, this experiment will take approximately 10 days to reach sufficient sample size. If your traffic is 50 users per day, the experiment would take 99 days, at which point the statistical validity is compromised by temporal confounds (seasonality, product changes during the test window, audience shift).

Now build the significance verification model. Below the sample size calculation, enter the following observed experimental results:

| Metric | Control | Treatment |
|--------|---------|-----------|
| Users (n) | 2500 | 2500 |
| Conversions | 305 | 380 |
| Conversion Rate | 0.122 | 0.152 |

In cell B18, enter: `=305 / 2500` (control rate). In cell C18, enter: `=380 / 2500` (treatment rate). In cell B19, enter the pooled proportion: `=(305 + 380) / (2500 + 2500)`. In cell B20, enter the standard error: `=SQRT(B19 * (1 - B19) * (1/2500 + 1/2500))`. In cell B21, enter the z-statistic: `=(C18 - B18) / B20`. In cell B22, enter the p-value (two-tailed): `=2 * (1 - NORMSDIST(ABS(B21)))`.

The z-statistic will be approximately 2.71 and the p-value will be approximately 0.0067. Since the p-value (0.0067) is below the significance threshold (0.05), you reject the null hypothesis and conclude that the treatment's effect is statistically significant. The treatment improved conversion from 12.2% to 15.2%, an absolute lift of 3.0 percentage points and a relative lift of 24.6%.

The operational discipline this lab instills is the sequence: compute required sample size before launching, run the experiment until that sample size is reached (no peeking), then verify significance. Stopping an experiment early because the p-value crosses 0.05 in the first three days is the most common statistical error in Agile experimentation and inflates the false positive rate far beyond the nominal 5%.

### Lab 2C: Cohort Retention Curve Analysis

Retention is the single most diagnostic metric for product health. Acquisition numbers can be inflated through spend, and revenue can mask churn in expansion-led growth models, but cohort retention curves reveal whether the product delivers durable value to users over time. A retention curve that flattens at a nonzero level indicates a product with a stable core user base. A retention curve that decays to zero indicates that the product fails to create lasting habituation, regardless of how many users are acquired.

Navigate to the `Cohort_Retention` sheet. In row 1, enter cohort identifiers across columns B through F: `Jan 2024`, `Feb 2024`, `Mar 2024`, `Apr 2024`, `May 2024`. In column A, enter the retention periods: `Week 0`, `Week 1`, `Week 2`, `Week 3`, `Week 4`, `Week 8`, `Week 12`. Populate the matrix with the following weekly active user retention percentages (each cell represents the percentage of the original cohort still active in that week):

| Period | Jan 2024 | Feb 2024 | Mar 2024 | Apr 2024 | May 2024 |
|--------|---------|---------|---------|---------|---------|
| Week 0 | 100% | 100% | 100% | 100% | 100% |
| Week 1 | 62% | 58% | 65% | 68% | 71% |
| Week 2 | 48% | 44% | 52% | 55% | 58% |
| Week 3 | 40% | 36% | 42% | 46% | 49% |
| Week 4 | 35% | 31% | 36% | 40% | 43% |
| Week 8 | 28% | 24% | 29% | 33% | 35% |
| Week 12 | 25% | 21% | 26% | 30% | 32% |

To analyze this data quantitatively, compute the month-over-month improvement in Week 4 retention. In cell B8 (below the Week 4 row), enter: `=(F6 - B6) / B6`. This computes the percentage improvement in Week 4 retention from the January cohort (35%) to the May cohort (43%), which is a 22.9% improvement over five months. This trend is the product team's most important leading indicator: it shows that onboarding and activation improvements are compounding, with each new cohort retaining better than the last.

Next, fit a power-law decay model to the January cohort to determine if retention flattens. In cells B10 through B12, enter: `Week`, `Actual Retention`, `Predicted Retention`. Copy the week numbers (0, 1, 2, 3, 4, 8, 12) into A10:A16. Copy the January retention values into B10:B16. The power-law model takes the form R(t) = a × t^(-b), where R is retention, t is the week number, a is the initial retention coefficient, and b is the decay exponent. To fit this, take the log of both sides: ln(R) = ln(a) - b × ln(t). In cell C11, enter: `=LN(B11)` and in D11 enter: `=LN(A11)`. Copy both down through C16 (skip row 10 since ln(0) is undefined). In cell E1, enter the slope: `=SLOPE(C11:C16, D11:D16)` and in E2 enter the intercept: `=INTERCEPT(C11:C16, D11:D16)`. The decay exponent b = -SLOPE (because the model is ln(R) = ln(a) - b × ln(t), so slope = -b). In E3, enter: `=-E1` (this is b). In E4, enter: `=EXP(E2)` (this is a).

For the January cohort, the fitted parameters will be approximately a = 52.3 and b = 0.74. The predicted retention at week 12 is: `=E4 * 12^(-E3)`, which will be approximately 24.7%, closely matching the actual 25%. The power-law fit confirms that retention asymptotically approaches but does not reach zero—mathematically, a × t^(-b) never equals zero for finite t, and the rate of decay slows as t increases. This is the characteristic signature of a healthy product: the users who remain after the initial drop-off form a durable core.

In cell E5, compute the projected Week 24 retention: `=E4 * 24^(-E3)`, which will be approximately 17.5%. In cell E6, compute projected Week 52 retention: `=E4 * 52^(-E3)`, approximately 11.2%. These projections feed directly into customer lifetime value calculations and capacity planning for customer success teams.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Lab 3A: Monte Carlo Delivery Forecasting Under Uncertainty

Point estimates for delivery dates are the single most damaging artifact in Agile program management. When a team says "we will deliver on March 15th," stakeholders hear a commitment, but the team has expressed a guess drawn from a single historical data point. Monte Carlo simulation replaces the point estimate with a probability distribution, producing a range of delivery dates with associated confidence levels. This is the professional standard for release forecasting in environments where story-level estimates carry significant uncertainty.

Navigate to the `Monte_Carlo_Forecast` sheet. We will simulate 1,000 iterations of a 40-story-point backlog using historical velocity data. In row 1, enter: `Iteration`, `Sprint 1 Velocity`, `Sprint 2 Velocity`, `Sprint 3 Velocity`, `Sprint 4 Velocity`, `Sprint 5 Velocity`, `Cumulative SP Delivered`, `Sprints to Complete 40 SP`, `Delivery Date`. 

Before running the simulation, establish the velocity distribution from the `Velocity_Tracker` sheet. The historical completed story points (Sprints 1–10) are: 48, 50, 46, 52, 49, 44, 42, 51, 47, 50. The mean is 47.9 and the standard deviation is 3.14. We will model velocity as a normal distribution with these parameters, truncated at a minimum of 30 (to prevent unrealistic negative-adjacent draws) and a maximum of 60 (to prevent unrealistic blowout sprints).

In cell M1, enter `Mean Velocity` and in M2 enter: `=AVERAGE('Velocity_Tracker'!C2:C11)`. In M3, enter `StdDev Velocity` and in M4 enter: `=STDEV('Velocity_Tracker'!C2:C11)`. In M5, enter `Target Backlog SP` and in M6 enter `40`. In M7, enter `Sprint Length (days)` and in M8 enter `10`. In M9, enter `Start Date` and in M10 enter `2025-01-06` (a Monday).

Now build the simulation. In cell A2, enter `1` and in A3 enter `=A2 + 1`. Copy A3 down through A1001 to create 1,000 iterations. In cell B2, enter the Sprint 1 velocity draw: `=MAX(30, MIN(60, NORMINV(RAND(), $M$2, $M$4)))`. This formula generates a random draw from the normal distribution, clamped between 30 and 60. Copy B2 into C2 through F2 (representing Sprints 1–5 for iteration 1). 

In cell G2, enter the cumulative story points delivered: `=MIN(B2 + C2 + D2 + E2 + F2, $M$6 * 2)`. This caps the cumulative at twice the target to handle cases where velocity is high. In cell H2, enter the sprints-to-complete calculation: `=IF(B2 >= $M$6, 1, IF(B2 + C2 >= $M$6, 2, IF(B2 + C2 + D2 >= $M$6, 3, IF(B2 + C2 + D2 + E2 >= $M$6, 4, IF(B2 + C2 + D2 + E2 + F2 >= $M$6, 5, 6)))))`. This formula checks, for each iteration, how many sprints are needed to accumulate at least 40 story points. In cell I2, enter the delivery date: `=$M$10 + (H2 - 1) * $M$8`. This converts sprints-to-complete into a calendar date by adding sprint-length days from the start date.

Copy all formulas in row 2 down through row 1001 to complete the 1,000-iteration simulation.

Now build the probability distribution of outcomes. In cell K2, enter `1` and in K3 enter `2`, continuing through K7 for values 1 through 6 (sprints to complete). In cell L2, enter the count of iterations resulting in that sprint count: `=COUNTIF($H$2:$H$1001, K2)`. Copy down through L7. In cell M2, enter the probability: `=L2 / 1000`. Copy down.

After running the simulation (press F9 or Cmd+= to recalculate all random draws), a typical distribution will look like:

| Sprints to Complete | Count | Probability | Delivery Date |
|---------------------|-------|-------------|---------------|
| 1 | 45 | 4.5% | 2025-01-06 |
| 2 | 520 | 52.0% | 2025-01-20 |
| 3 | 390 | 39.0% | 2025-01-30 |
| 4 | 38 | 3.8% | 2025-02-10 |
| 5 | 7 | 0.7% | 2025-02-20 |
| 6 | 0 | 0.0% | 2025-03-03 |

The cumulative probability of completing within 2 sprints is 56.5%, within 3 sprints is 95.5%, and within 4 sprints is 99.3%. The operationally useful forecast is: "We are 95% confident the 40-story-point backlog will be delivered within 3 sprints, by January 30, 2025." This is a fundamentally different and far more defensible statement than "we will deliver on January 20th" (the 2-sprint point estimate, which has only a 56.5% probability).

The stress-testing dimension emerges when you vary the input parameters. Change the standard deviation in cell M4 from 3.14 to 8.0 (simulating a highly volatile team with erratic velocity). Re-run the simulation and observe that the probability distribution flattens dramatically: the 3-sprint completion probability may drop from 95% to 70%, and the tail extends to 6 sprints with non-trivial probability. This demonstrates that velocity consistency (low standard deviation) is more valuable for predictable delivery than high average velocity, because high variance widens the confidence interval and makes every downstream commitment less reliable.

### Lab 3B: Sprint Failure Mode Simulation and Recovery Protocol

This lab simulates three common sprint failure modes and builds the recovery playbook for each. The objective is to move from reactive firefighting to pre-validated recovery protocols that can be executed immediately when a failure mode is detected.

**Failure Mode 1: Critical Team Member Unavailability Mid-Sprint**

A senior developer accounting for 25% of the team's capacity becomes unavailable on day 3 of a 10-day sprint. The team has committed to 42 story points. At the current burndown pace, 35 story points remain.

The recovery model quantifies the capacity reduction and determines which stories to descope. In the `Sprint_Planning` sheet, add a new section below the existing sprint backlog. In cell A15, enter `Remaining Capacity (person-days)` and in B15 enter `35` (7 team members × 5 remaining days). In A16, enter `Lost Capacity (person-days)` and in B16 enter `15` (the unavailable member's remaining 5 days × 3, since they accounted for ~25% of the 7-person team's daily output). In A17, enter `Adjusted Capacity Ratio` and in B17 enter: `=B15 / (B15 + B16)`, which gives 0.70. In A18, enter `Achievable Story Points` and in B18 enter: `=42 * B17`, which gives 29.4, meaning the team can realistically complete approximately 29 story points instead of 42.

The descope decision is mechanical: work backward from the bottom of the prioritized backlog, removing the lowest-priority stories until cumulative story points drop to 29. From Lab 1B, removing S-010 (8 SP), S-009 (5 SP) reduces the commitment to 29 SP. The descope must happen on day 3, not day 8, to give the team a realistic target and prevent the psychological damage of a visible sprint failure. The Scrum Master communicates to stakeholders: "Due to [team member] unavailability, we are descoping Audit Log Export and Payment Method Vault to the next sprint. All P0 and P1 stories remain on track."

**Failure Mode 2: Story Point Discovery Mid-Sprint (Scope Inflation)**

On day 4, the team discovers that S-003 (SSO Integration, estimated at 8 SP) actually requires 20 SP of work due to an unanticipated identity provider compatibility issue. The burndown chart from Lab 1C already showed a day-4 stall—this is the cause.

The recovery protocol requires re-estimation and either scope reduction or sprint extension. In the `Sprint_Planning` sheet, in cell C4 (S-003 story points), change 8 to 20. The cumulative SP column now shows the sprint total jumping to 54, which exceeds the lower control limit of 45.23 by 8.77 story points. The team has two options.

Option A is to split the story. S-003 becomes S-003a (SSO with Okta, 8 SP) and S-003b (SSO with Azure AD, 12 SP), with S-003b moving to the next sprint. This preserves the sprint commitment at 42 SP and delivers partial value. In the spreadsheet, change C4 back to 8 and add a new row: S-003b, SSO Azure AD, 12, P1, with cumulative SP recomputed. The sprint total remains 42 and the sprint is recovered.

Option B is to negotiate a sprint extension to 12 days (adding 2 days). This is generally discouraged because it breaks the sprint cadence and trains stakeholders to expect extensions whenever difficulty arises. However, if S-003 is a hard dependency for S-004 (SSO Integration, 3 SP) and S-005 (API Rate Limiting, 5 SP), the cascade effect means 8 additional story points are blocked, and a 2-day extension to complete 54 SP is operationally rational. The decision criterion is: if descoping or splitting is possible, do that; extend only when a hard dependency chain makes partial delivery impossible.

**Failure Mode 3: Velocity Collapse Across Multiple Sprints**

Navigate back to `Velocity_Tracker`. Simulate a velocity collapse by changing the completed story points for Sprints 8, 9, and 10 from 51, 47, 50 to 30, 28, 25. The rolling 3-sprint average for Sprint 10 drops from 49.33 to 27.67. The standard deviation jumps from 2.05 to 2.52. The lower control limit drops to 22.63.

This collapse pattern—three consecutive sprints below the previous lower control limit—triggers a structural intervention, not a tactical adjustment. The recovery protocol is:

First, convene an emergency retrospective focused on root cause, not process improvement. The five-whys analysis is the diagnostic instrument. Why did velocity drop? Because story estimates were consistently too low. Why? Because requirements were underspecified at sprint planning. Why? Because the product owner was unavailable for refinement sessions. Why? Because the PO was managing a separate critical escalation. Why? Because there is no backup PO coverage model. The root cause is an organizational staffing gap, not an estimation problem, and no amount of planning poker refinement will fix it.

Second, implement a capacity correction. The new sprint commitment should be based on the collapsed velocity, not the historical average. Set the sprint capacity to the new lower control limit of 22.63, rounded down to 22 story points. This is a 53% reduction from the previous 42-point commitment and will feel psychologically devastating, but it is the honest, data-driven planning baseline. Over the next 3–4 sprints, as the root cause is addressed (backup PO assigned, refinement sessions resume), velocity should recover, and the rolling average will climb back toward the original band.

Third, communicate to stakeholders with the statistical evidence. "Our velocity has dropped from a rolling average of 49 to 28 over the past three sprints, driven by an unresolved product ownership gap. We are committing to 22 story points this sprint while we implement a structural fix. We expect velocity to recover to 40+ within four sprints, at which point we will re-baseline commitments."

---

## Operational Reference Guide & Diagnostic Checklist

This reference guide consolidates the quantitative models, decision thresholds, and diagnostic heuristics from all three exercises into a single operational reference. It is designed to be used during sprint planning, mid-sprint health checks, release forecasting, and retrospective root-cause analysis.

**Sprint Planning Reference.** Sprint capacity should be set to the lesser of the rolling 3-sprint average velocity or the lower control limit (mean minus 2 standard deviations). This ensures commitments are achievable with 95% statistical confidence. If the team's velocity standard deviation exceeds 20% of the mean, the team has a consistency problem that will degrade forecast reliability regardless of average throughput. Prioritize the backlog using RICE scoring, fill the sprint in priority order until cumulative story points reach capacity, and descope any story that would exceed it. Never commit above the upper control limit; doing so has a less than 2.5% probability of success.

**Burndown Diagnostic Thresholds.** Variance from ideal burndown of ±2 story points is normal execution noise. Variance exceeding +2 story points for two consecutive days triggers a mid-sprint check-in. Variance exceeding +4 story points triggers immediate descope evaluation. A burndown that goes flat for three or more days indicates either an impediment, a story that was grossly underestimated, or a team member who has become unavailable. The daily standup should surface the cause; if it does not, the Scrum Master must investigate directly.

**Kanban WIP Optimization.** Compute a composite score weighting throughput (40%), inverse lead time (30%), and flow efficiency (30%) for each WIP configuration. Select the WIP level with the highest composite score, not the highest throughput. If two WIP levels have composite scores within 5% of each other, choose the lower WIP to optimize for predictability and lower work-in-process inventory.

**A/B Test Operational Rules.** Compute required sample size before launching using the two-proportion z-test formula with alpha = 0.05 and power = 0.80. Do not evaluate results until the pre-computed sample size is reached. The minimum detectable effect should be set to the smallest effect size that would justify shipping the feature; smaller MDE requires larger samples, and the trade-off between detection sensitivity and experiment duration must be made explicitly. After data collection, verify that the p-value is below 0.05 and that the observed effect size meets or exceeds the MDE before declaring significance.

**Cohort Retention Monitoring.** Fit a power-law decay model (R(t) = a × t^(-b)) to each monthly cohort's retention curve. The decay exponent b is the critical monitoring metric: b < 0.5 indicates strong retention with rapid flattening, 0.5 < b < 1.0 indicates moderate retention, and b > 1.0 indicates weak retention with continued linear decline. Track the Week 4 retention rate across cohorts month-over-month; a sustained decline of more than 5% across three consecutive cohorts is a red flag requiring product investigation. A sustained improvement of 5% or more indicates that onboarding or activation changes are compounding effectively.

**Monte Carlo Forecasting Protocol.** For any release commitment exceeding one sprint, generate a 1,000-iteration Monte Carlo simulation using the team's historical velocity distribution. Report the 85th percentile delivery date (the date by which 85% of simulations completed), not the mean or median. This provides stakeholders with a date that has an 85% probability of being met, which is the standard confidence level for external commitments. If the velocity standard deviation exceeds 25% of the mean, widen the reporting window and flag the release as high-variance. Recalculate the simulation at the end of each sprint with updated velocity data.

**Sprint Failure Recovery Decision Tree.** When a mid-sprint failure mode is detected, apply the following decision sequence. First, quantify the capacity impact (person-days lost, story points affected). Second, determine whether descoping or story splitting can bring the commitment back within the adjusted lower control limit. If yes, descope or split immediately and communicate to stakeholders. If no, evaluate whether a 1–2 day sprint extension preserves the sprint cadence without creating a precedent. If extension is not viable, fail the sprint explicitly, move all incomplete stories to the next sprint backlog, and conduct a root-cause retrospective before re-planning. Never silently absorb a failure by carrying over 30%+ of committed story points without explicit stakeholder communication and retrospective action items.

**Velocity Collapse Detection.** Three consecutive sprints with completed story points below the previous lower control limit constitute a statistically significant velocity collapse. This triggers: (1) an emergency root-cause retrospective using five-whys analysis, (2) re-baselining of sprint capacity to the new lower control limit, (3) a structural intervention targeting the identified root cause, and (4) a recovery timeline communicated to stakeholders with the expectation that velocity will return to the previous band within 3–4 sprints after the intervention takes effect. If velocity does not recover within 6 sprints, the structural intervention was insufficient and a second root-cause cycle is required.
