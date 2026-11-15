# Operational Verification Labs: Product User Experience

## Objective & Operational Lab Setup

The discipline of product user experience sits at the intersection of behavioral psychology, product economics, and commercial strategy. For a management practitioner, UX is not an aesthetic concern but a revenue mechanism. Every friction point in a user flow has a measurable cost: a 100-millisecond increase in checkout latency has been shown to reduce conversion by approximately 1%, and a single additional mandatory form field in a B2B onboarding flow can depress week-one activation rates by 15 to 20 percentage points. This lab series is built around that economic frame. You will treat UX not as design output but as a system to be instrumented, diagnosed, and optimized through rigorous empirical methods.

The three exercises that follow progress in a deliberate sequence. The first exercise grounds you in the construction of a complete UX audit rubric scored against real product flows, using the heuristic evaluation method alongside a quantified severity matrix. The second exercise introduces parameter variation through A/B test design and cohort retention analysis, forcing you to reason about what changes move which metrics and by how much. The third exercise stress-tests your product experience model by simulating failure modes: broken onboarding flows, accessibility violations under WCAG 2.1 AA standards, and cognitive overload conditions measured against George Miller's channel capacity research. The recovery protocols are operational, not theoretical.

### Analytical Environment Setup

Before beginning any exercise, configure your analytical workspace. You will work across three tools: a spreadsheet application (Google Sheets or Excel), a Miro or FigJam board for user journey mapping, and a statistical calculator for significance testing. The spreadsheet workbook should be organized with one tab per exercise model. Name the tabs `UX_Audit_Rubric`, `AB_Test_Model`, and `Stress_Test_Heatmap`. All quantitative cells should use explicit formula references rather than hardcoded values so that parameter changes cascade correctly through the model.

You will also need access to a real product flow to audit. If you are working without a live product, use the publicly accessible onboarding flow of any freemium SaaS product, such as Notion, Linear, or Figma. Navigate through the flow as a first-time user, capture screenshots at every distinct screen state, and number them sequentially. These screenshots constitute your primary diagnostic artifact throughout all three exercises.

---

## Exercise 1: Foundational Practical Implementation — Heuristic UX Audit with Quantified Severity Scoring

### Background and Mechanical Rationale

Jakob Nielsen's ten usability heuristics, originally published in 1994, remain the most operationally reliable diagnostic framework for identifying UX failures without access to behavioral data. The heuristics are not abstract principles; each one maps to a specific category of cognitive failure. Violation of "visibility of system status" means users cannot form accurate mental models of what the system is doing, which produces anxiety and abandonment. Violation of "match between system and the real world" means the product's vocabulary requires a translation layer that consumes working memory, increasing task completion time and error rates. Understanding the mechanism behind each heuristic is what allows you to score findings with precision rather than guesswork.

A raw heuristic violation list has limited operational value because it conflates a confusing tooltip label with a catastrophic data loss failure. The severity scoring matrix resolves this. You score each violation on two independent axes: frequency (how often users encounter this problem) and impact (the degree to which the problem prevents task completion). Multiplying these scores produces a risk-weighted severity index that lets you rank findings and build a prioritized remediation backlog directly comparable to a RICE-scored product backlog.

### Step 1: Build the Severity Scoring Matrix in the `UX_Audit_Rubric` Tab

Open your spreadsheet and configure the `UX_Audit_Rubric` tab with the following column headers across row 1: `Finding_ID`, `Screen_Number`, `Heuristic_Violated`, `Violation_Description`, `Frequency_Score`, `Impact_Score`, `Severity_Index`, `Affected_User_Segment`, `Remediation_Effort_Days`, and `Priority_Rank`.

Frequency is scored on a 1-to-5 scale where 1 means the violation is encountered by fewer than 10% of users on a typical session path, 3 means it appears in the dominant user flow and affects 50 to 70% of users, and 5 means every user encounters it on every session. Impact is scored on a 1-to-5 scale where 1 means users notice the issue but complete the task without meaningful degradation, 3 means users require a workaround or experience a measurable delay of more than 30 seconds, and 5 means users cannot complete the primary task without external help or abandonment.

In column G (`Severity_Index`), enter the formula `=E2*F2` for row 2 and copy it down through all finding rows. This gives you a severity index ranging from 1 (cosmetic noise) to 25 (critical blocker). In column J (`Priority_Rank`), use `=RANK(G2, $G$2:$G$50, 0)` to auto-rank findings across the full finding set. This formula ranks highest severity as rank 1 and handles ties by assigning the same rank to tied rows.

### Step 2: Conduct the Heuristic Walkthrough

Work through your captured product screenshots in sequence. For each screen, evaluate it against all ten heuristics systematically. Do not shortcut this by scanning for obvious problems and moving on. The highest-value findings are often invisible until you apply the heuristic frame explicitly. A common practitioner error is conflating "I understood what to do" with "this screen is well-designed." Your subjective familiarity with software conventions makes you blind to failures that devastate first-time users.

For each violation you identify, create one row in your rubric. Write the violation description in plain, specific language: not "the button is confusing" but "the primary CTA button on the account setup screen (Screen 4) uses the label 'Continue' without indicating whether the previous field values have been saved, violating the Visibility of System Status heuristic. Users who have invested ten minutes in configuration will hesitate before proceeding because they cannot distinguish whether clicking advances them or discards their work." That specificity is what makes the finding actionable in a sprint backlog.

A fully executed audit of a mid-complexity SaaS onboarding flow (8 to 12 screens) should yield between 15 and 35 findings. Fewer than 10 findings suggests you are not applying the heuristic lens rigorously enough. More than 50 suggests you are conflating design preferences with genuine usability violations.

### Step 3: Score, Rank, and Translate to a Prioritized Backlog

Once all findings are entered, sort the rubric by `Severity_Index` descending. The top five to eight findings constitute your critical UX remediation backlog. For each of these, populate `Remediation_Effort_Days` with an honest engineering and design estimate. A label change is 0.5 days. Restructuring an information architecture requires 15 to 30 days including discovery, design, development, and QA.

Compute a composite priority score using the formula `Priority = Severity_Index / Remediation_Effort_Days`. This is the UX equivalent of the RICE score's effort denominator. A severity-25 finding that takes 1 day to fix scores 25.0. A severity-20 finding that takes 20 days to fix scores 1.0. The former must ship before the latter despite the latter's higher raw severity, because marginal impact per unit of investment is an order of magnitude larger.

Document this ranked backlog in a table at the bottom of the `UX_Audit_Rubric` tab, with columns for `Priority_Score`, `Finding_ID`, `Violation_Description`, `Owner`, and `Target_Sprint`. Leave the `Owner` and `Target_Sprint` fields populated with real names and sprint numbers from your team's actual planning calendar. A UX audit that does not terminate in a sprint-assignable backlog has zero operational value.

---

## Exercise 2: Parameter Variation & Empirical Analysis — A/B Test Design and Cohort Retention Modeling

### Background and Mechanical Rationale

The heuristic audit in Exercise 1 identifies candidate improvements through expert judgment. Exercise 2 teaches you to validate those improvements through controlled experimentation and to model how UX changes propagate through retention curves over time. These are distinct skills. Expert judgment tells you that removing a mandatory phone number field from a signup form probably reduces friction. Controlled experimentation tells you by exactly how much, in your specific user population, with statistical confidence. The difference between those two levels of rigor is the difference between a product team that ships improvements and one that ships improvements and knows whether they worked.

The retention curve is the central economic instrument here. If a UX change improves week-one activation by 8 percentage points, the question that matters commercially is not "did we activate more users this month" but "how much does that activation improvement shift the 90-day retained cohort, and what is the NPV of that incremental retention?" Connecting a UX intervention to a retention curve to a revenue impact is the analytical chain that earns product UX work its budget allocation.

### Step 1: Design the A/B Test in the `AB_Test_Model` Tab

Identify one finding from your Exercise 1 backlog that is both high-severity and tractable within a two-week sprint. The ideal candidate is a change to a single UI element: a CTA label, a form field removal, a progress indicator addition, or an error message rewrite. The change must be binary (control versus variant), and the primary metric must be a single, unambiguous rate that can be measured at the user level within the experiment window.

In the `AB_Test_Model` tab, build a sample size calculator. Enter the following inputs in a labeled parameter block in rows 2 through 7: `Baseline_Conversion_Rate` (the current rate in control, expressed as a decimal), `Minimum_Detectable_Effect` (the smallest relative improvement you care about detecting, also as a decimal), `Statistical_Power` (set to 0.80 as the standard threshold), `Significance_Level` (set to 0.05 for a two-tailed test), `Daily_Unique_Visitors` (the actual daily traffic entering the tested flow), and `Experiment_Duration_Days` (calculated, not set manually).

The required sample size per variant is calculated from the formula derived from the normal approximation to the binomial distribution. In a dedicated cell, enter:

```
=2 * ((NORM.S.INV(1 - B6/2) + NORM.S.INV(B5))^2 * (B2*(1-B2) + (B2*(1+B4))*(1-(B2*(1+B4))))) / (B2*B4)^2
```

Where B2 is `Baseline_Conversion_Rate`, B4 is `Minimum_Detectable_Effect`, B5 is `Statistical_Power`, and B6 is `Significance_Level`. This formula computes the per-variant sample size needed to detect a relative lift of `MDE` over the baseline at 80% power and 5% significance. For a baseline conversion of 0.35, an MDE of 0.08 (detecting an 8 percentage-point relative improvement, meaning moving from 35% to 37.8%), power of 0.80, and alpha of 0.05, the formula returns approximately 3,814 users per variant, or 7,628 users total.

Divide the total required sample by `Daily_Unique_Visitors` to calculate `Experiment_Duration_Days`. If your daily traffic is 500 visitors and the required sample is 7,628, your experiment must run for at least 16 days. Enter this as `=CEILING(SampleSizeCell * 2 / B7, 1)` where B7 is `Daily_Unique_Visitors`.

### Step 2: Build the Cohort Retention Model

In a new section of the `AB_Test_Model` tab, build a 12-week cohort retention model that projects the downstream revenue impact of your hypothesized UX improvement. Configure the following row structure: row 1 is the week label (Week 0 through Week 12), row 2 is the control cohort retention curve, row 3 is the variant cohort retention curve, row 4 is the incremental retained users (variant minus control), and row 5 is the incremental MRR generated by those additional retained users.

For the control cohort retention curve, use an exponential decay model calibrated to realistic SaaS retention benchmarks. A healthy PLG (product-led growth) product retains approximately 60% of activated users at Week 1, 42% at Week 4, 30% at Week 8, and 24% at Week 12. Enter Week 0 as 1.0 (100% by definition), and in each subsequent week apply the decay formula. In B2 through N2 for weeks 0 through 12, enter:

```
Week 0: 1.0
Week 1: =B2 * 0.60
Week 2: =C2 * 0.85
Week 3: =D2 * 0.90
Week 4: =E2 * 0.90
Weeks 5-12: =PreviousCell * 0.95
```

This decay schedule reflects the characteristic L-shaped retention curve observed in most SaaS products: a steep early drop from onboarding friction followed by a flatter long-tail among engaged users. For the variant cohort in row 3, increase the Week 1 retention multiplier from 0.60 to 0.65 (representing the 8-percentage-point activation improvement your UX change is hypothesized to deliver), and hold all subsequent multipliers identical to the control. This isolates the impact of onboarding-stage improvement from engagement-stage dynamics.

In row 4, calculate incremental retained users as `=B3 - B2` multiplied by your initial activated cohort size. Set the cohort size in a dedicated parameter cell, say 1,000 activated users. In row 5, multiply incremental retained users by your product's ARPU (Average Revenue Per User). Set ARPU in a parameter cell with a value of $45 per month per retained user. The cumulative incremental MRR by Week 12 is the sum of row 5 across all weeks.

For a cohort of 1,000 activated users, a Week 1 retention improvement from 60% to 65%, and an ARPU of $45, the 12-week incremental revenue calculation produces approximately $14,200 in cumulative additional MRR from a single cohort. Annualize this across the number of new cohorts entering the product per year (say, 48 weekly cohorts) and the revenue impact of one onboarding UX fix exceeds $680,000 annually. This is the number you bring to the roadmap prioritization meeting.

### Step 3: Interpret Results Against Decision Thresholds

After your experiment runs, record the observed conversion rates for control and variant in the results section of your model. Calculate the observed lift as `=(VariantRate - ControlRate) / ControlRate`. Calculate the z-statistic using:

```
=( (VariantRate - ControlRate) ) / SQRT( ControlRate*(1-ControlRate)/ControlN + VariantRate*(1-VariantRate)/VariantN )
```

Convert the z-statistic to a two-tailed p-value using `=2*(1-NORM.S.DIST(ABS(ZStatCell), TRUE))`. If the p-value falls below 0.05, the result is statistically significant at your pre-specified alpha. If it does not, do not adjust the threshold retroactively. A p-value of 0.07 is not "almost significant"; it is a failure to detect the effect at the required confidence level, and the correct response is to either extend the experiment to gather more data or accept that the change does not produce a detectable lift of your target MDE.

Document the decision explicitly: ship, hold, or iterate. A statistically significant result does not automatically mean ship. If the variant produces a 3% lift in the primary metric but a 5% degradation in a secondary metric (say, the percentage of users who complete the second onboarding step), the interaction effect may make the net impact negative. This is why you specify your secondary guardrail metrics before the experiment runs, not after.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol — Cognitive Load Audit, Accessibility Violation Mapping, and Flow Failure Simulation

### Background and Mechanical Rationale

The first two exercises operate under normal conditions: competent users navigating a functioning flow with roughly average cognitive resources. Exercise 3 deliberately breaks those assumptions. Stress testing a UX system means exposing it to the conditions under which real users fail: low literacy, assistive technology dependency, high ambient cognitive load, mobile data constraints, and system error states. These are not edge cases. Approximately 15% of the global population lives with some form of disability. Mobile data throttling is the default condition for users in emerging markets and rural areas. Cognitive load peaks during exactly the moment users are most engaged with a product: initial signup, checkout, configuration, and crisis response.

Cognitive load theory, developed by John Sweller in the 1980s, distinguishes between intrinsic load (the inherent complexity of the task), extraneous load (complexity imposed by poor design), and germane load (the productive cognitive work of learning). UX design can do nothing about intrinsic load, but it can and must minimize extraneous load. George Miller's research established that human working memory can hold approximately seven plus or minus two discrete chunks of information simultaneously. A product screen that presents more than nine distinct interactive or informational elements is operating at the boundary of working memory capacity for most users. Under stress or interruption, that boundary drops to four or five chunks, which is the basis for the "four-item rule" in mobile UX design.

WCAG 2.1 AA compliance is not a legal checkbox exercise. The standard's four principles (perceivable, operable, understandable, robust) map directly to the same failure modes that hurt all users, not just users with disabilities. A button without sufficient color contrast fails users with color vision deficiency, but it also fails users viewing the product on a low-quality screen in bright sunlight, which describes a large fraction of mobile users globally.

### Step 1: Build the Cognitive Load Heatmap in the `Stress_Test_Heatmap` Tab

Configure the `Stress_Test_Heatmap` tab with one row per screen from your product flow audit. The columns should be: `Screen_Number`, `Interactive_Element_Count`, `Distinct_Text_Block_Count`, `Total_Chunk_Count`, `Chunk_Overload_Flag`, `Intrinsic_Load_Score`, `Extraneous_Load_Score`, `Total_Load_Score`, and `Failure_Risk_Rating`.

`Interactive_Element_Count` is a manual count of every clickable, typeable, selectable, or toggleable element on the screen. Count these literally from your screenshot: buttons, input fields, dropdowns, checkboxes, radio buttons, links in body text, and navigation items all count. `Distinct_Text_Block_Count` counts every visually distinct text grouping: headings, body paragraphs, labels, tooltips, helper text blocks, and error messages.

`Total_Chunk_Count` is the sum of the two counts above. In the `Chunk_Overload_Flag` column, use `=IF(D2>9, "OVERLOAD", IF(D2>6, "WARNING", "OK"))` where D2 is `Total_Chunk_Count`. Any screen flagged OVERLOAD is a stress-test failure candidate.

For `Intrinsic_Load_Score`, assign a 1-to-5 rating based on the inherent complexity of the task the screen supports: a simple "confirm your email address" screen is a 1; a multi-entity configuration screen for setting up data pipeline permissions is a 5. This score is your analyst judgment and should be documented with a one-sentence rationale. For `Extraneous_Load_Score`, assign a 1-to-5 rating based on how much of the screen's complexity is attributable to design decisions rather than task requirements: unnecessary navigation chrome on a focused task screen, redundant instructional copy, decorative icons that compete visually with functional ones, and inconsistent visual hierarchy all increase extraneous load.

`Total_Load_Score` is `=F2 + G2`, ranging from 2 to 10. `Failure_Risk_Rating` translates this into an operational flag: `=IF(H2>=8, "CRITICAL", IF(H2>=6, "HIGH", IF(H2>=4, "MODERATE", "LOW")))`.

### Step 2: Execute the WCAG 2.1 AA Accessibility Violation Scan

For each screen in your product flow, execute a systematic accessibility scan across the four WCAG 2.1 AA principle categories. You do not need automated tooling for this exercise; the goal is to build the diagnostic muscle through manual evaluation, which produces deeper understanding of the failure mechanisms than a linter report.

Work through the following checks on each screen in sequence. Under Perceivable, verify that all non-text content has a text alternative: every image, icon, and graphic should have an `alt` attribute or `aria-label`. Check color contrast ratios for all body text (minimum 4.5:1 against background) and large text (minimum 3:1). The contrast ratio formula is `(L1 + 0.05) / (L2 + 0.05)` where L1 is the relative luminance of the lighter color and L2 is the relative luminance of the darker color. Relative luminance for an sRGB channel value C is calculated as: if `C/255 <= 0.04045`, then `C/255 / 12.92`; otherwise, `((C/255 + 0.055) / 1.055)^2.4`. Sum the R, G, B luminance contributions weighted by `0.2126, 0.7152, 0.0722` respectively to get relative luminance.

For a common design pattern like medium-gray text (#767676) on a white background (#FFFFFF), compute the contrast ratio: white luminance is 1.0. For #767676, each channel value is 118. Applying the sRGB linearization: 118/255 = 0.463, which is greater than 0.04045, so the formula is `((0.463 + 0.055)/1.055)^2.4 = (0.518/1.055)^2.4 = 0.491^2.4 ≈ 0.216`. Since R=G=B for a gray, luminance is `0.2126 * 0.216 + 0.7152 * 0.216 + 0.0722 * 0.216 = 0.216`. Contrast ratio is `(1.0 + 0.05) / (0.216 + 0.05) = 1.05 / 0.266 = 3.95:1`. This fails the 4.5:1 body text standard. #767676 is a notoriously common failure case in SaaS UI kits and appears in production interfaces from companies that have never run a contrast audit.

Under Operable, verify that all interactive elements are reachable and activatable via keyboard alone. Tab through the entire screen in sequence and confirm that the focus order is logical, that focus indicators are visible (a default browser outline is acceptable; invisible focus is not), and that no keyboard traps exist. Under Understandable, verify that all form fields have associated labels (not just placeholder text, which disappears on input), that error messages identify the specific field in error and explain the correction required, and that the page language is declared in the HTML. Under Robust, verify that all custom UI components use appropriate ARIA roles and that the DOM structure is semantically meaningful.

Log each violation in a dedicated accessibility findings table in your `Stress_Test_Heatmap` tab with columns for `Screen_Number`, `WCAG_Principle`, `Success_Criterion_ID`, `Violation_Description`, `Severity` (Critical blocks access entirely, Serious degrades it significantly, Moderate creates friction, Minor is a best-practice gap), and `Remediation`.

### Step 3: Simulate Flow Failure and Execute Recovery Protocol

The final stress test simulates what happens when the product's UX system encounters failure states: network interruption during a form submission, session timeout mid-task, payment processing failure at checkout, and validation errors on a complex multi-step form. These failure states are where UX quality most directly determines whether a user recovers and completes the task or abandons permanently.

For each failure scenario, work through your product flow and identify the screen and state where the failure would manifest. Then evaluate the existing failure UX against five recovery criteria. First, is the error message specific about what failed and why, or does it produce a generic "something went wrong" message that gives the user no actionable information? Second, does the product preserve user-entered data through the failure, or does the user face a blank form after a network error? Third, does the error state provide a clear next action: a retry button, a support contact, or a step-by-step resolution path? Fourth, is the visual design of the error state perceivable: does it use color alone to signal failure (a red border without an icon or text label fails users with protanopia), or does it use redundant encoding across color, icon, and explicit text? Fifth, does the system log the error in a way that allows support and engineering teams to diagnose the failure without requiring the user to describe what happened?

Score each criterion as pass or fail for each failure scenario. Any scenario with more than two failures is a critical flow reliability defect, not a UX polish issue. The business impact is direct: a payment processing failure that destroys entered data and displays a generic error converts a recoverable transaction failure into permanent customer churn. The recovery protocol for critical flow reliability defects should be treated as a P0 engineering fix, not a design sprint candidate.

Document the full stress test results in a summary section at the bottom of the `Stress_Test_Heatmap` tab. The summary should report the number of screens flagged OVERLOAD or WARNING in the cognitive load heatmap, the total WCAG 2.1 AA violations by severity level, the number of critical flow reliability defects identified, and the aggregate failure surface score calculated as `= (OVERLOAD_Count * 3) + (WARNING_Count * 1) + (Critical_WCAG * 4) + (Serious_WCAG * 2) + (Critical_Flow_Defects * 5)`. This composite score gives you a single number to track across product releases as your remediation work ships.

---

## Operational Reference Guide & Diagnostic Checklist

### Framework Reference: When to Apply Each Model

The three exercises in this lab correspond to three distinct diagnostic questions that every product manager must be able to answer. The heuristic audit with severity scoring answers the question "where are the UX failures in my product and which ones most damage business outcomes?" It is the right tool at the beginning of a product cycle, before you have behavioral data, and after any significant UI redesign ships. Run it every quarter on your three highest-traffic flows.

The A/B test design and cohort retention model answers "what does this specific UX change do to my conversion and retention metrics, and what is the revenue value of the improvement?" It is the right tool when you have a specific, implementable change hypothesis and sufficient traffic to run a valid experiment. The minimum viable experiment requires the sample size calculation to show a test duration of no more than 30 days. If your traffic requires 90 days to reach significance on your target MDE, either widen your MDE threshold (accept that you can only detect larger effects), increase the scope of the change (target a higher-traffic screen), or use a Bayesian approach that allows for earlier decision-making with explicit prior beliefs.

The stress test and cognitive load audit answers "does my product hold up under conditions of real-world adversity: low-bandwidth users, assistive technology users, cognitively loaded users, and system failure states?" It is the right tool before any major launch into a new market segment, before enterprise sales begin (accessibility compliance is frequently a procurement requirement), and after any user research session surfaces patterns of confusion or abandonment in specific user scenarios.

### Diagnostic Checklist: Pre-Launch UX Verification Gate

A product launch should not proceed without passing the following verification checks. Each check maps directly to the exercises in this lab.

The heuristic audit must be complete with all Severity Index 20 or higher findings either remediated or explicitly deferred with a documented rationale and a sprint assignment. No finding with a severity of 25 may be deferred across a launch boundary. The A/B test for any change to the primary conversion flow (signup, onboarding step one, payment) must have concluded with a statistically significant result at p < 0.05 or a declared equivalence test confirming the change does not degrade conversion below the lower bound of the equivalence margin. The cognitive load heatmap must show zero screens rated OVERLOAD in the primary user flow for the top three user personas. WCAG 2.1 AA compliance must show zero Critical and zero Serious violations in the core task flows. All failure scenario recovery criteria must pass at four of five criteria for every critical flow; any scenario with three or more failures blocks the launch.

### Common Diagnostic Errors and Corrections

The most frequent analytical error in UX work is confusing engagement metrics with experience quality. High time-on-page, for example, is often cited as evidence of user engagement, but in task-completion flows it is frequently a symptom of confusion. A user spending four minutes on a two-minute onboarding screen is not engaged; they are stuck. The correct diagnostic instrument for distinguishing engagement from confusion is task completion time benchmarked against an expert walkthrough. If average user completion time exceeds expert time by more than 2.5x, the screen has a usability problem regardless of what the engagement numbers suggest.

The second common error is running experiments on too many variables simultaneously. A product team that is simultaneously testing a new CTA label, a form field removal, and a progress bar addition is running a confounded experiment. Any observed lift cannot be attributed to a specific change, which means the team learns nothing actionable about the mechanism of improvement. The discipline of one-variable-at-a-time experimentation feels slow, but it is the only method that produces causal knowledge rather than directional noise.

The third error is treating statistical significance as the final word on whether a change is beneficial. Statistical significance tells you that an observed effect is unlikely to be due to random sampling variation. It tells you nothing about whether the effect size is commercially meaningful, whether the improvement persists beyond the novelty period of the experiment, or whether the variant performs equally well across user segments. A proper experiment analysis segments the results by acquisition channel, device type, and user tenure cohort before declaring a winner. Variants that produce a 10% aggregate lift but a 20% degradation for mobile users represent a net negative outcome for a product with 60% mobile traffic.

### Quick-Reference Formula Summary

The sample size formula, the contrast ratio calculation, the cohort retention NPV model, the composite failure surface score, and the RICE priority formula are the five quantitative instruments that underpin the full lab sequence. The sample size formula produces the minimum per-variant exposure required to detect your MDE at specified power and significance. The contrast ratio formula validates color accessibility against WCAG 2.1 AA thresholds. The cohort retention NPV model converts an activation rate improvement into a 12-week cumulative MRR impact. The composite failure surface score aggregates stress test results into a single regression-trackable health metric. The RICE priority formula (`(Reach * Impact * Confidence) / Effort`) ensures that your remediation backlog is sorted by value delivered per unit of team capacity, not by the loudest stakeholder voice in the room.

Each formula in this lab is complete, executable in a standard spreadsheet, and grounded in the specific behavioral and economic mechanics it is designed to measure. Apply them together and you have a full UX verification system capable of taking a product flow from heuristic diagnosis through experimental validation to stress-tested launch readiness, with every decision documented, quantified, and defensible.
