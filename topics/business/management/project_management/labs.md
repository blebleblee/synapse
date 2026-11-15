# Operational Verification Labs: Project Management

## Objective & Operational Lab Setup

These labs transform project management theory into muscle memory. Each exercise is designed around the instruments a working project manager actually uses: a Work Breakdown Structure built in a spreadsheet, an Earned Value Management model that generates live performance indices, a critical path network that exposes schedule float, and a risk register that feeds directly into a Monte Carlo simulation. The goal across all three exercises is not familiarity with concepts but operational fluency — the ability to sit down in front of a real project, build the control artifacts from scratch, read their diagnostic signals correctly, and intervene before variance becomes failure.

The lab environment requires nothing proprietary. Every model runs in Microsoft Excel or Google Sheets, using native formula syntax that you can verify cell by cell. Where simulation logic is required, it uses the RAND() and NORM.INV() functions available in both platforms without add-ins. A working browser and a copy of the companion spreadsheet you will build during Exercise 1 are your only tools. By the time you complete Exercise 3, you will have constructed a fully integrated project control model — one that accepts schedule updates, recomputes Earned Value indices in real time, identifies the critical path under resource constraints, and stress-tests schedule confidence through 1,000 Monte Carlo iterations.

**Analytical Research Environment Setup**

Before beginning Exercise 1, open a new spreadsheet and create four named worksheets: `WBS`, `Schedule`, `EVM`, and `Risk`. The naming convention matters because cross-sheet formulas in later exercises reference these tabs explicitly. Set your spreadsheet locale to use a period as the decimal separator and ensure date formatting follows ISO 8601 (YYYY-MM-DD) so that date arithmetic functions behave predictably across both Excel and Sheets.

The project context used throughout all three exercises is a fixed scenario: a mid-market SaaS company is deploying a new customer onboarding module. The project has a baseline budget of $480,000, a planned duration of 20 weeks, and a team of seven resources across engineering, QA, design, and project coordination. This context is specific enough that every formula, risk rating, and variance calculation you produce maps to a real managerial decision rather than an abstract exercise.

---

## Exercise 1: Foundational Practical Implementation

### Part A — Building the Work Breakdown Structure and Baseline Schedule

The Work Breakdown Structure is not a task list. It is a scope decomposition hierarchy that makes the relationship between deliverables and cost accounts explicit. A properly constructed WBS guarantees that every dollar of budget and every day of schedule is traceable to a discrete deliverable — a property called the 100% Rule. If the sum of all child-level work packages does not equal the full scope of the parent deliverable, your WBS is broken and your budget baseline is unreliable.

Navigate to the `WBS` sheet and set up columns A through H with the following headers in row 1: `WBS ID`, `Level`, `Deliverable Name`, `Work Package Owner`, `Planned Start`, `Planned Finish`, `Planned Duration (days)`, and `Planned Cost ($)`. Now enter the following decomposition. The Level 1 node is the project itself. Level 2 nodes are the five major phases. Level 3 nodes are the work packages that roll up into each phase.

Enter the following rows, beginning at row 2:

| WBS ID | Level | Deliverable Name | Owner | Planned Start | Planned Finish | Duration | Cost |
|---|---|---|---|---|---|---|---|
| 1.0 | 1 | Onboarding Module Deployment | PM | 2025-01-06 | 2025-05-23 | 140 | 480000 |
| 1.1 | 2 | Requirements & Design | BA Lead | 2025-01-06 | 2025-01-31 | 20 | 72000 |
| 1.1.1 | 3 | Stakeholder Interviews | BA Lead | 2025-01-06 | 2025-01-10 | 5 | 12000 |
| 1.1.2 | 3 | User Persona Mapping | UX Lead | 2025-01-13 | 2025-01-17 | 5 | 14000 |
| 1.1.3 | 3 | Functional Requirements Doc | BA Lead | 2025-01-20 | 2025-01-24 | 5 | 22000 |
| 1.1.4 | 3 | UI Wireframes | UX Lead | 2025-01-27 | 2025-01-31 | 5 | 24000 |
| 1.2 | 2 | Backend Development | Eng Lead | 2025-02-03 | 2025-03-14 | 40 | 144000 |
| 1.2.1 | 3 | API Architecture Design | Eng Lead | 2025-02-03 | 2025-02-07 | 5 | 28000 |
| 1.2.2 | 3 | Database Schema Build | Eng 1 | 2025-02-10 | 2025-02-21 | 10 | 38000 |
| 1.2.3 | 3 | Core API Endpoints | Eng Lead | 2025-02-24 | 2025-03-07 | 10 | 46000 |
| 1.2.4 | 3 | Integration Connectors | Eng 2 | 2025-03-10 | 2025-03-14 | 5 | 32000 |
| 1.3 | 2 | Frontend Development | Eng 3 | 2025-03-17 | 2025-04-11 | 20 | 96000 |
| 1.3.1 | 3 | Component Library Setup | Eng 3 | 2025-03-17 | 2025-03-21 | 5 | 22000 |
| 1.3.2 | 3 | Onboarding Flow UI | Eng 3 | 2025-03-24 | 2025-04-04 | 10 | 44000 |
| 1.3.3 | 3 | Integration with Backend | Eng 3 | 2025-04-07 | 2025-04-11 | 5 | 30000 |
| 1.4 | 2 | QA & Testing | QA Lead | 2025-04-14 | 2025-05-02 | 15 | 84000 |
| 1.4.1 | 3 | Test Plan & Cases | QA Lead | 2025-04-14 | 2025-04-18 | 5 | 18000 |
| 1.4.2 | 3 | Functional Testing | QA 1 | 2025-04-21 | 2025-04-25 | 5 | 32000 |
| 1.4.3 | 3 | UAT Execution | BA Lead | 2025-04-28 | 2025-05-02 | 5 | 34000 |
| 1.5 | 2 | Deployment & Handover | PM | 2025-05-05 | 2025-05-23 | 15 | 84000 |
| 1.5.1 | 3 | Staging Environment Deploy | Eng Lead | 2025-05-05 | 2025-05-09 | 5 | 28000 |
| 1.5.2 | 3 | Production Cutover | Eng Lead | 2025-05-12 | 2025-05-16 | 5 | 32000 |
| 1.5.3 | 3 | Documentation & Training | PM | 2025-05-19 | 2025-05-23 | 5 | 24000 |

Verify the 100% Rule by summing the Level 3 `Planned Cost` values for each Level 2 phase. The sum of 1.1.1 through 1.1.4 must equal 72,000. The sum of 1.2.1 through 1.2.4 must equal 144,000. Continue for each phase. Then confirm the grand total of all Level 2 planned costs equals 480,000. If any level fails this check, your scope decomposition has a gap and the EVM model you build in Part B will produce misleading variance signals.

### Part B — Building the Earned Value Baseline

Navigate to the `EVM` sheet. This model will track project performance using the three core Earned Value quantities — Planned Value (PV), Earned Value (EV), and Actual Cost (AC) — and derive the four diagnostic indices from them. Enter headers across row 1 in columns A through N: `WBS ID`, `Work Package`, `Budget at Completion (BAC)`, `Planned % Complete`, `PV`, `Actual % Complete`, `EV`, `AC`, `Schedule Variance (SV)`, `Cost Variance (CV)`, `Schedule Performance Index (SPI)`, `Cost Performance Index (CPI)`, `Estimate to Complete (ETC)`, `Estimate at Completion (EAC)`.

The formulas in columns E through N are the operational core of this lab. Each formula must be entered exactly as shown for each work package row. Assume row 2 represents work package 1.1.1 (Stakeholder Interviews), which has a BAC of $12,000. Set cell C2 to 12000. For this initial baseline exercise, you are capturing the status at the end of Week 5 (2025-02-07). Enter the following values and formulas beginning at row 2 for all Level 3 work packages.

**Column E — Planned Value (PV):**
PV is the budgeted cost of work scheduled to have been completed by the status date. For work packages that should be fully complete by Week 5, the planned percent complete (column D) is 1.0. For those not yet started, it is 0.0. For work in partial progress, it reflects the proportion of duration elapsed.

`=C2*D2`

**Column G — Earned Value (EV):**
EV is the budgeted cost of work actually completed. The actual percent complete in column F is what you enter from reality; EV is derived from it.

`=C2*F2`

**Column H — Actual Cost (AC):**
Enter AC values directly as reported by the finance system. These represent money actually spent as of the status date. For the first status cycle at Week 5, use the following actual costs by work package: 1.1.1 = 13,200; 1.1.2 = 13,500; 1.1.3 = 0 (not yet started); 1.1.4 = 0.

**Column I — Schedule Variance (SV):**
`=G2-E2`

A negative SV means work is behind schedule relative to the baseline plan. A positive SV means work is ahead of schedule. The unit is dollars of work, not days.

**Column J — Cost Variance (CV):**
`=G2-H2`

A negative CV means you spent more than the budgeted value of the work completed. A positive CV means work was done under budget.

**Column K — Schedule Performance Index (SPI):**
`=G2/E2`

An SPI below 1.0 indicates the project is accomplishing less work per time unit than planned. An SPI of 0.85 means you are completing 85 cents of planned work for every dollar of time elapsed.

**Column L — Cost Performance Index (CPI):**
`=G2/H2`

A CPI below 1.0 means every dollar spent is producing less than a dollar of budgeted progress. CPI is the single most statistically reliable early predictor of final cost outcome in projects exceeding 20% completion.

**Column M — Estimate to Complete (ETC):**
ETC answers the question: given current performance efficiency, how much will it cost to finish the remaining scope? Use the CPI-adjusted formula, which accounts for the fact that past performance predicts future performance on most technology delivery projects.

`=(C2-G2)/L2`

**Column N — Estimate at Completion (EAC):**
EAC is the projected final cost of the entire work package given current performance.

`=H2+(C2-G2)/L2`

After entering all formulas for all 11 Level 3 work packages, build a summary row beneath all work packages. Set the summary BAC as `=SUM(C2:C12)`. Set the summary EV as `=SUM(G2:G12)`. Set the summary AC as `=SUM(H2:H12)`. Set the summary PV as `=SUM(E2:E12)`. Then compute the project-level SPI and CPI using the aggregated values:

`Project SPI = SUM(EV range) / SUM(PV range)`

`Project CPI = SUM(EV range) / SUM(AC range)`

The project-level EAC uses the most conservative defensible formula — the independent estimate at completion (IEAC) — which applies the project-level CPI to the remaining budget:

`=SUM(H2:H12) + (SUM(C2:C12) - SUM(G2:G12)) / (SUM(G2:G12) / SUM(H2:H12))`

This formula produces the number you present to a sponsor when asked "what will this project actually cost?" It is not an opinion; it is a mathematically derived projection anchored in real performance data.

### Part C — Building the Critical Path Network

Navigate to the `Schedule` sheet. The critical path is the longest sequence of dependent activities through the network; it determines the project's minimum possible duration. Any delay on a critical path activity delays the project end date by exactly that amount. Activities off the critical path have float — the amount of time they can slip before they threaten the finish date.

Set up columns A through J: `Activity ID`, `Activity Name`, `Predecessors`, `Optimistic Duration (days)`, `Most Likely Duration (days)`, `Pessimistic Duration (days)`, `PERT Duration`, `Early Start`, `Early Finish`, `Float`.

PERT duration smooths the three-point estimate into a weighted average that acknowledges the asymmetric nature of schedule risk (delays are more common than early completions):

`=( D2 + 4*E2 + F2 ) / 6`

Enter the following activity network. Activity IDs map to WBS work packages. Predecessors are listed by Activity ID.

| ID | Activity | Pred | O | ML | P |
|---|---|---|---|---|---|
| A | Stakeholder Interviews | — | 4 | 5 | 8 |
| B | User Persona Mapping | A | 4 | 5 | 7 |
| C | Functional Requirements Doc | A | 4 | 5 | 9 |
| D | UI Wireframes | B,C | 4 | 5 | 8 |
| E | API Architecture Design | D | 4 | 5 | 7 |
| F | Database Schema Build | E | 8 | 10 | 15 |
| G | Core API Endpoints | F | 9 | 10 | 14 |
| H | Integration Connectors | G | 4 | 5 | 8 |
| I | Component Library Setup | D | 4 | 5 | 7 |
| J | Onboarding Flow UI | I,H | 9 | 10 | 14 |
| K | Integration with Backend | J | 4 | 5 | 7 |
| L | Test Plan & Cases | K | 4 | 5 | 7 |
| M | Functional Testing | L | 4 | 5 | 8 |
| N | UAT Execution | M | 4 | 5 | 7 |
| O | Staging Environment Deploy | N | 4 | 5 | 7 |
| P | Production Cutover | O | 4 | 5 | 7 |
| Q | Documentation & Training | P | 4 | 5 | 6 |

The PERT duration for each activity populates column G. The forward pass computes Early Start (ES) and Early Finish (EF). For the first activity with no predecessors, ES = 0 and EF = ES + PERT Duration. For every subsequent activity, ES = the maximum EF among all predecessor activities. This maximum-of-predecessors logic captures the fact that a dependent activity cannot begin until all its inputs are available.

For Activity A: `ES = 0`, `EF = 0 + G2`

For Activity B (predecessor A): `ES = EF_A`, `EF = ES_B + G3`

For Activity D (predecessors B and C): `ES = MAX(EF_B, EF_C)`, `EF = ES_D + G5`

The backward pass computes Late Start (LS) and Late Finish (LF), working from the final activity back to the start. For the terminal activity, LF = EF. For all other activities, LF equals the minimum LS of all successor activities. Float for each activity = LF − EF (equivalently, LS − ES). Activities with Float = 0 lie on the critical path.

Add columns K and L for `Late Start` and `Late Finish` to complete the backward pass. Then add column M labeled `Critical Path` and enter the formula:

`=IF(J2=0,"CRITICAL","Float: "&J2&" days")`

where column J holds Float calculated as `=L2-I2`. This formula flags every zero-float activity as CRITICAL and displays the float value for all others, giving you an at-a-glance critical path map across the entire project network.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Part A — Sensitivity Analysis on Cost Performance Index Assumptions

The EAC formula you built in Exercise 1 assumes that the current CPI will persist for the remainder of the project. This assumption is empirically well-supported — studies of government and defense contracts by Christensen and Anbari consistently show that CPI stabilizes after the 20% completion point and rarely improves materially. However, the assumption deserves stress testing. A sponsor who wants to know the range of possible final costs, not just the central estimate, needs a sensitivity table.

On the `EVM` sheet, build a two-dimensional sensitivity table beneath your summary row. The table will vary two independent inputs — CPI (from 0.75 to 1.25 in steps of 0.05) and the percentage of remaining scope that gets re-scoped or cut (from 0% to 20% in steps of 5%) — and show the resulting EAC for each combination.

Place CPI values across row headers (columns B through L) starting at a row well below your data, say row 20. Place re-scope percentage values down column A (rows 21 through 25) with values 0%, 5%, 10%, 15%, 20%. The EAC formula in each cell of the table is:

`= AC_total + ( BAC_total * (1 - re_scope_pct) - EV_total ) / CPI_input`

In spreadsheet terms, anchoring to your summary row (assume summary AC is in cell H14, summary BAC in C14, summary EV in G14), and placing CPI inputs in row 20 starting at B20, and re-scope percentages in column A starting at A21:

`=H$14 + ($C$14*(1-$A21) - $G$14) / B$20`

The dollar sign anchoring is not optional. Without it, copying this formula across the table will shift your references and produce garbage. After entering this formula in cell B21, copy it across to L21, then copy the entire range B21:L21 down to row 25. You now have a 5x11 matrix of EAC scenarios. Apply conditional formatting: color cells below $480,000 (the original BAC) in green, cells between $480,000 and $530,000 in yellow, and cells above $530,000 in red.

The pattern that emerges from this table is itself the analytical finding. When CPI is 0.85 and no scope is cut, the EAC typically lands 15–18% over budget — the signal that tells a PM to escalate to the sponsor and begin scope negotiation rather than hoping performance recovers. When CPI drops to 0.80, even a 20% scope reduction rarely brings the final cost back inside the original budget envelope, which reframes the problem as a fundamental delivery constraint rather than a correctable execution issue.

### Part B — Float Consumption Tracking and Schedule Sensitivity

Return to the `Schedule` sheet and add a new section beginning in column O. This section models float consumption over time — the progressive erosion of schedule buffer as activities slip. Understanding the rate of float consumption is as important as knowing current float, because a path with 10 days of float that is consuming 1.5 days of float per week will breach the critical path in under 7 weeks.

Add the column `Reported Slip (days)` in column O, `Remaining Float` in column P, and `Weeks Until Critical` in column Q.

Enter the following reported slips as of Week 5 of the project. Activity A slipped 1 day. Activity B slipped 2 days. Activity C slipped 1 day. Activity D has not yet started but its critical predecessor (C) slipped, so enter 0 as direct slip but note the upstream effect propagates through the network.

For `Remaining Float` in column P:
`= J2 - O2`

This is a simplification appropriate for activities not yet on the critical path. For critical activities where J2 = 0, Remaining Float will go negative when slips occur — a negative value means the project end date has already moved right by that number of days.

For `Weeks Until Critical` in column Q:
`=IF(P2<=0,"PAST CRITICAL",P2/1.5)`

The divisor 1.5 represents an empirical slip rate assumption of 1.5 days per week — a conservative but realistic figure for technology projects under moderate resource pressure. This is a parameter you should calibrate from your own project history. If your team has historical velocity data showing slippage of 1.0 days per week on average, substitute 1.0.

Apply conditional formatting to column Q: values below 4 weeks in red (immediate intervention required), values between 4 and 8 weeks in amber (monitor weekly), values above 8 weeks in green (normal tracking cycle). This color-coded float forecast gives your weekly status meeting an immediate visual focus: any red row demands a recovery plan before the next report cycle, not after.

### Part C — Variance Threshold Alerting and Escalation Triggers

Professional project control frameworks do not wait for a PM to notice problems; they define quantitative thresholds that automatically escalate. The two most operationally useful thresholds are the CPI threshold and the SV% threshold.

Add a `Variance Alerts` section on the `EVM` sheet. In a row beneath the sensitivity table, label three alert cells: `CPI Alert`, `SPI Alert`, and `EAC Overrun Alert`.

For `CPI Alert`:
`=IF(L14<0.90,"ESCALATE: CPI "&TEXT(L14,"0.00")&" — Cost overrun trajectory",IF(L14<0.95,"WATCH: CPI "&TEXT(L14,"0.00")&" — Monitor weekly","NOMINAL: CPI "&TEXT(L14,"0.00")))`

Here L14 is your project-level CPI. This formula produces a text string with the precise CPI value embedded, so the alert is self-documenting in any status report.

For `SPI Alert`:
`=IF(K14<0.85,"ESCALATE: SPI "&TEXT(K14,"0.00")&" — Schedule recovery plan required",IF(K14<0.92,"WATCH: SPI "&TEXT(K14,"0.00")&" — Compression options needed","NOMINAL: SPI "&TEXT(K14,"0.00")))`

For `EAC Overrun Alert`, compute the overrun percentage against the original BAC:
`=IF((N14-C14)/C14>0.15,"ESCALATE: EAC "&TEXT((N14-C14)/C14,"0%")&" over BAC",IF((N14-C14)/C14>0.07,"WATCH: "&TEXT((N14-C14)/C14,"0%")&" over BAC","NOMINAL: "&TEXT((N14-C14)/C14,"0%")&" variance"))`

These three alert cells form the executive dashboard of your EVM model. They are updated automatically every time you enter a new status cycle's PV, EV, and AC values, and they communicate triage priority without requiring the reader to interpret numbers.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Part A — Monte Carlo Schedule Simulation

The PERT durations you computed in Exercise 1 produce a single-point estimate of project duration. But a single-point schedule is a fiction: duration is a probability distribution, not a fixed number. Monte Carlo simulation samples from each activity's uncertainty range 1,000 times, adds up the resulting critical path length for each iteration, and produces a distribution of project completion dates. From this distribution you read schedule confidence intervals: the P50 (median expected finish), P70, P80, and P90 completion dates.

Navigate to the `Risk` sheet. Build the Monte Carlo simulation using the following architecture. Column A will hold Activity IDs (A through Q). Columns B, C, D will hold Optimistic, Most Likely, and Pessimistic durations copied from the `Schedule` sheet — values exactly as entered earlier. Column E will hold a single simulated duration draw for each activity. Column F will hold the cumulative path length calculation. Rows 1 through 17 define the activities. Beginning at row 20, you will run 1,000 iterations by recalculating the random draws.

The simulation draw for each activity uses a triangular distribution approximated through a standard Normal inverse, which is the most practical method available without specialized add-ins. The standard deviation of a PERT activity is estimated as:

σ = (Pessimistic − Optimistic) / 6

In spreadsheet terms, for Activity A in row 2:

`=NORM.INV(RAND(), (B2 + 4*C2 + D2)/6, (D2-B2)/6)`

This generates a random duration sampled from a normal distribution centered on the PERT mean with a standard deviation reflecting the spread between optimistic and pessimistic estimates. RAND() returns a new uniform random value between 0 and 1 on every recalculation, and NORM.INV converts it to a corresponding duration on the normal curve.

The critical path duration in any single iteration is not simply the sum of all activity durations; it is the longest path through the network. For the linear backbone of this project (A → C → D → E → F → G → H → J → K → L → M → N → O → P → Q), the path length is:

`=E2+E4+E5+E6+E7+E8+E9+E11+E12+E13+E14+E15+E16+E17+E18`

where E2 through E18 reference the simulated duration column for each activity in the backbone sequence. This sum goes into cell G2 as the simulated project duration for one iteration.

To run 1,000 iterations without a macro, use a data table. Place your single-iteration path length formula in a named cell (call it `SimDuration`). Create a one-column data table in the range I1:I1001. Cell I1 is blank (the row input cell). Cells I2 through I1001 each contain a reference to `SimDuration`. Select the range I1:I1001, go to Data → What-If Analysis → Data Table, leave Row Input Cell blank, and set Column Input Cell to any empty cell on the sheet. Excel recalculates the formula 1,000 times with 1,000 fresh RAND() samples and stores each result.

Once the data table is populated, compute the percentile outputs in column K:

`P50 = PERCENTILE(I2:I1001, 0.50)`
`P70 = PERCENTILE(I2:I1001, 0.70)`
`P80 = PERCENTILE(I2:I1001, 0.80)`
`P90 = PERCENTILE(I2:I1001, 0.90)`

Convert these duration percentiles to calendar dates by adding them to your project start date (2025-01-06):

`=DATE(2025,1,6) + PERCENTILE(I2:I1001, 0.80)`

The P80 date answers the question every sponsor actually wants answered: "What completion date can we commit to with reasonable confidence?" The baseline planned finish of 2025-05-23 represents a 140-day schedule. If the P80 from your simulation comes out at 155 days, the honest answer is that the project has an 80% probability of finishing by that later date, and a commitment to the original date carries a 65–70% chance of overrun. That number belongs in the project charter revision, not buried in a risk log.

### Part B — Resource Constraint Failure and Recovery Modeling

The critical path analysis in Exercise 1 assumed unlimited resource availability. Reality does not. When two critical path activities share the same resource, the earlier activity creates a dependency that extends the logical critical path even when no technical dependency exists between the work packages.

Return to the `Schedule` sheet and add columns N and O: `Primary Resource` and `Resource-Adjusted Start`. Assign resources as follows: Activities A and C both require the BA Lead. Activities B and D both require the UX Lead. Activities E, G, and H all require the Eng Lead. Activities F and I can proceed in parallel because they use different resources (Eng 1 and Eng 3 respectively).

The resource-leveled start date for Activity C, given that the BA Lead is finishing Activity A, is:

`=MAX(EF_A_resource_adjusted, ES_C_network_logic)`

In practice, since A must finish before C can begin anyway (A is a predecessor of C), the resource constraint adds no additional delay here. However, Activities E and H share the Eng Lead. If H's network logic allows it to start before E finishes, the resource constraint forces H to wait. Identify every such conflict by adding a column labeled `Resource Conflict Flag`:

`=IF(COUNTIF($N$2:$N$18, N2)>1,"CHECK RESOURCE CONFLICT","OK")`

This flags every activity where more than one entry uses the same resource label. Review each flagged activity pair manually. For the Eng Lead conflict between Activities E, G, and H: E runs weeks 7–8, G runs weeks 11–13, and H runs weeks 14. No calendar overlap exists, so resource leveling does not extend the schedule in this specific scenario. Document this finding explicitly in your project control log — the absence of a resource conflict is as important to record as a confirmed conflict, because it validates your schedule assumptions.

For the scenario where a key resource becomes unavailable — the Eng Lead leaves the project after completing Activity G — build a recovery plan analysis. The remaining critical path activities requiring the Eng Lead are Activity H (Integration Connectors) and Activity O (Staging Environment Deploy). Identify substitute resources, their availability windows, and the resulting schedule delta. Create a recovery scenario table with four columns: `Recovery Option`, `Resource`, `Duration Increase (days)`, `Schedule Impact (days)`.

Enter three recovery options: (1) contract Eng Lead back as a consultant for Activity H only, duration unchanged, 0-day schedule impact at a cost premium of $8,000; (2) promote Eng 2 to cover Activity H with a 3-day duration increase due to ramp-up, adding 3 days to the schedule; (3) defer Activity H and compress testing by running UAT in parallel with Functional Testing, which saves 5 days in phase 1.4 at the cost of elevated re-work risk. Rate each option on a simple 3-axis matrix: Cost Impact (1–5), Schedule Impact (1–5), and Risk Impact (1–5). Sum the scores and select the minimum. This structured recovery option analysis is what you present to a steering committee when a critical resource fails — not a verbal assurance that you will "find a way."

### Part C — Risk Register Integration and Quantitative Risk Exposure

Navigate to the `Risk` sheet and build a formal risk register beneath the Monte Carlo simulation section. Set up columns A through J: `Risk ID`, `Risk Description`, `Category`, `Probability (0–1)`, `Schedule Impact (days)`, `Cost Impact ($)`, `Risk Score`, `Mitigation Action`, `Residual Probability`, `Residual Risk Score`.

Risk Score is the product of probability and impact, but because schedule and cost are separate dimensions, compute two scores and take the weighted average. Define a weighting parameter: schedule weight = 0.60, cost weight = 0.40, reflecting the fact that this project is schedule-sensitive (a delayed launch costs the business approximately $24,000 per week in deferred revenue, which you can verify by dividing the project's projected Year 1 incremental ARR of $1.25M by 52 weeks).

The composite risk score for a given risk is:

`= (D2 * E2 * 0.60) + (D2 * (F2/24000) * 0.40)`

This formula normalizes the cost impact into weeks of equivalent schedule impact before weighting, so both dimensions are expressed in the same unit (weeks of schedule equivalent) before aggregation.

Enter the following risks:

| ID | Description | Cat | Prob | Sched Impact (days) | Cost Impact ($) |
|---|---|---|---|---|---|
| R-01 | API vendor deprecates endpoint mid-project | Technical | 0.25 | 10 | 32000 |
| R-02 | BA Lead departs before requirements sign-off | Resource | 0.15 | 8 | 18000 |
| R-03 | UAT scope creep extends testing phase | Scope | 0.40 | 7 | 22000 |
| R-04 | Staging environment unavailable at cutover | Infrastructure | 0.20 | 5 | 14000 |
| R-05 | Security audit flags compliance gap post-UAT | Compliance | 0.30 | 12 | 45000 |

For each risk, enter a mitigation action and assign a residual probability (the probability after the mitigation is in place). R-01 mitigation: contract a versioning SLA with the API vendor; residual probability 0.10. R-02 mitigation: cross-train Eng 1 on requirements documentation; residual probability 0.07. R-03 mitigation: define UAT acceptance criteria in the test plan before sign-off; residual probability 0.20. R-04 mitigation: provision a parallel staging instance 2 weeks early; residual probability 0.08. R-05 mitigation: engage security review in parallel with QA rather than post-UAT; residual probability 0.12.

Compute the residual risk score using the same composite formula but substituting residual probability for initial probability. Then compute the total risk exposure before and after mitigation by summing all risk scores:

`Pre-mitigation Total Exposure = SUMPRODUCT(D2:D6, E2:E6) * 0.60 + SUMPRODUCT(D2:D6, F2:F6/24000) * 0.40`

`Post-mitigation Total Exposure = SUMPRODUCT(I2:I6, E2:E6) * 0.60 + SUMPRODUCT(I2:I6, F2:F6/24000) * 0.40`

The difference between pre- and post-mitigation exposure is the quantified value of your risk management plan — a number you can present to a PMO director or CFO to justify the cost of mitigation activities. If the mitigation plan costs $15,000 to implement (documentation, early staging provisioning, security review hours) and reduces risk exposure by an equivalent of $72,000 in expected cost and schedule value, the ROI on risk management is positive and defensible.

---

## Operational Reference Guide & Diagnostic Checklist

### Earned Value Diagnostic Thresholds

The following thresholds are grounded in empirical research across government and commercial projects and represent the professional standard for EVM-based decision making. CPI and SPI values should be tracked weekly from the 15% completion point onward. CPI is considered statistically stable — meaning it does not change by more than ±10% — once a project crosses the 20% completion mark; this stability is the basis for the IEAC formula's predictive validity.

A project-level CPI in the range 0.95 to 1.05 is nominal and requires standard weekly tracking. A CPI between 0.90 and 0.95 triggers a formal variance analysis report identifying root causes by work package — not by phase, because phase-level aggregation masks the specific activity drivers. A CPI below 0.90 triggers formal escalation to the project sponsor and requires a revised EAC with a documented recovery plan within five business days. A CPI below 0.80 is a project failure signal; at this level, the statistically expected final cost overrun typically exceeds 20% of BAC, and scope reduction or schedule extension negotiation must begin immediately.

SPI thresholds follow a similar logic but with an important caveat: SPI converges to 1.0 at project completion regardless of how badly the schedule performed, because all planned work is eventually either complete or cancelled. This mathematical artifact makes SPI an unreliable measure in the final 20% of a project. After the 80% completion point, replace SPI with a direct comparison of Earned Schedule (ES) against Actual Time (AT) to preserve schedule diagnostic validity.

### Critical Path Monitoring Protocol

Check the float of every non-critical activity at each weekly status cycle. The critical number is not today's float but the float consumption rate. Any path consuming more than 1.0 days of float per week is a candidate for critical path migration — the process by which a currently non-critical path absorbs enough slippage to become the longest path and thereby redefine the project's finish date. When a path's projected weeks-until-critical figure drops below three weeks, it requires the same management attention as an already-critical activity.

Document every instance of critical path migration in your project log with the date, the new critical path sequence, the float values at migration, and the root cause of the slip. Over the course of a project, this log becomes the most honest narrative of project execution that exists, and it is exactly the document a post-mortem review needs to generate organizational learning.

### Monte Carlo Confidence Interval Usage

Report the P80 schedule date as the commitment date to external stakeholders. Report the P50 date as the internal baseline for resource planning. The gap between P50 and P80 is the schedule contingency reserve — the buffer that belongs in the project charter as an explicitly named reserve, not embedded invisibly in inflated task estimates. Embedding contingency in task estimates is a governance failure: it hides risk from sponsors, makes performance measurement impossible, and prevents the organization from learning its true historical schedule accuracy.

When the Monte Carlo P10 date (the optimistic tail) is later than the contractual deadline, the project has a structural schedule problem that no amount of execution improvement can resolve without scope reduction or additional resources. This is the finding that reframes a tactical schedule conversation into a strategic project scope conversation — and it is a finding you can only make if you have run the simulation.

### Weekly Project Health Checklist

The following checklist should be completed at every weekly status cycle. For each item, record the actual measured value, not a qualitative judgment. Project management is a measurement discipline.

Confirm that EV, AC, and PV have been updated from actual time-tracking and cost system data, not estimated. Compute CPI and SPI and compare them to the prior week's values; a deteriorating trend over three consecutive weeks is a leading indicator that requires investigation even if absolute values are still within tolerance. Update all float values on the critical path network based on actual activity completions and any reported slips. Verify that every risk with a probability above 0.25 has had its mitigation action checked for execution status — a mitigation plan that is documented but not executed provides zero risk reduction. Confirm that the EAC is current and that the sponsor has been notified if EAC has moved more than 5% since the last reported value.

Identify the single highest-priority action required before the next status cycle. Write it as a specific, owned, dated commitment: not "address the API risk" but "Eng Lead to send API vendor the versioning SLA draft for review by 2025-02-14." The specificity of action items in a project log is a direct measure of the PM's operational control over the project. Vague action items are where project accountability goes to die.
