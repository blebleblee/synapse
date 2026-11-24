# Operational Verification Labs: Diabetes And Metabolic Syndrome

## Objective & Operational Lab Setup

This lab guide is built for the practitioner who needs to move from raw patient data to actionable clinical decisions with speed and precision. The three exercises that follow treat diabetes and metabolic syndrome not as abstract disease categories but as measurable, quantifiable physiological states that respond predictably to systematic analysis. You will work with real diagnostic criteria, calculate risk scores by hand and in spreadsheet models, stress-test your clinical reasoning against edge cases drawn from actual patient archetypes, and build a reusable audit checklist capable of surviving the pressure of a busy outpatient clinic or a wilderness medicine scenario where a glucometer is your only instrument.

Metabolic syndrome is defined operationally by the harmonized IDF/AHA/NHLBI 2009 consensus as the presence of any three of five criteria: waist circumference ≥102 cm (men) or ≥88 cm (women); fasting triglycerides ≥1.7 mmol/L (150 mg/dL) or on lipid-lowering therapy; HDL-C < 1.0 mmol/L (40 mg/dL) in men or < 1.3 mmol/L (50 mg/dL) in women; resting blood pressure ≥130/85 mmHg or on antihypertensive therapy; and fasting plasma glucose ≥5.6 mmol/L (100 mg/dL) or on glucose-lowering therapy. Type 2 diabetes is confirmed by fasting plasma glucose ≥7.0 mmol/L (126 mg/dL), 2-hour oral glucose tolerance test (OGTT) plasma glucose ≥11.1 mmol/L (200 mg/dL), HbA1c ≥48 mmol/mol (6.5%), or random plasma glucose ≥11.1 mmol/L with classic hyperglycemic symptoms. These thresholds are your operational ground truth throughout every exercise.

### Analytical Environment Setup

You need three tools active before beginning Exercise 1: a spreadsheet application (Microsoft Excel, LibreOffice Calc, or Google Sheets), a scientific calculator (physical or the built-in Windows/macOS calculator in scientific mode), and printed or screen-accessible copies of the ADA Standards of Medical Care in Diabetes (current year), the UKPDS Risk Engine documentation, and the Framingham Cardiovascular Risk Score tables.

In your spreadsheet, create a master workbook with four tabs named **Patient_Registry**, **Lipid_Calculator**, **OGTT_Plotter**, and **CV_Risk_Engine**. The Patient_Registry tab should have column headers in row 1 as follows: Patient_ID, Age, Sex, Weight_kg, Height_m, BMI, Waist_cm, SBP, DBP, FPG_mmol, HbA1c_pct, TG_mmol, HDL_mmol, LDL_mmol, Creatinine_umol, eGFR, MetSyn_Criteria_Count, MetSyn_Diagnosis, DM_Status. Set column widths to 14 for readability. This registry will serve as the living data substrate for all three exercises.

---

## Exercise 1: Foundational Practical Implementation

### 1.1 — Patient Intake and Biometric Calculation

You will work through five patient cases simultaneously, populating the registry and computing every derived value by formula rather than by lookup. This builds the operational habit of treating each number as a live calculation rather than a static entry, which matters enormously when a single lab value is revised and you need the downstream risk score to update automatically.

Enter the following five patients into rows 2–6 of the Patient_Registry tab exactly as shown:

| Patient_ID | Age | Sex | Weight_kg | Height_m | Waist_cm | SBP | DBP | FPG_mmol | HbA1c_pct | TG_mmol | HDL_mmol | LDL_mmol | Creatinine_umol |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PT-001 | 54 | M | 102 | 1.74 | 107 | 138 | 88 | 6.2 | 6.8 | 2.1 | 0.9 | 3.4 | 88 |
| PT-002 | 47 | F | 78 | 1.62 | 91 | 126 | 80 | 5.4 | 5.9 | 1.6 | 1.2 | 2.9 | 71 |
| PT-003 | 61 | M | 118 | 1.70 | 114 | 152 | 96 | 8.9 | 8.4 | 3.8 | 0.8 | 4.1 | 104 |
| PT-004 | 38 | F | 64 | 1.68 | 82 | 118 | 76 | 4.9 | 5.1 | 0.9 | 1.6 | 2.3 | 62 |
| PT-005 | 66 | M | 95 | 1.78 | 99 | 144 | 90 | 7.4 | 7.1 | 1.9 | 1.1 | 3.7 | 131 |

In column F (BMI), enter the formula `=D2/(E2^2)` for PT-001 and fill down through row 6. BMI results should read: 33.7, 29.7, 40.8, 22.7, 30.0. If yours differ by more than 0.1, recheck that Height_m is entered as a decimal (1.74, not 174).

The eGFR column requires the CKD-EPI 2021 equation. For a male patient, the formula applied to creatinine in µmol/L is:

**eGFR = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^(−1.200) × 0.9938^Age**

where κ = 80 µmol/L and α = −0.302 for males; κ = 62 µmol/L and α = −0.241 for females. Because spreadsheet implementation of the min/max operator requires nested IF logic, enter the following formula into the eGFR column for PT-001 (male, creatinine in N2, age in B2):

```text
=142*IF(N2/80<1,(N2/80)^(-0.302),(N2/80)^0)*IF(N2/80>1,(N2/80)^(-1.2),1)*0.9938^B2
```

For PT-002 (female), the formula changes κ and α:

```text
=142*IF(N3/62<1,(N3/62)^(-0.241),(N3/62)^0)*IF(N3/62>1,(N3/62)^(-1.2),1)*0.9938^B3*1.012
```

Apply the sex-appropriate formula for each patient. Expected eGFR values: PT-001 = 79, PT-002 = 86, PT-003 = 65, PT-004 = 103, PT-005 = 54. PT-003 and PT-005 fall below 90 mL/min/1.73m², placing them in CKD stage G2 and G3a respectively — a clinical flag for SGLT2 inhibitor dosing adjustments that you will revisit in Exercise 3.

### 1.2 — Metabolic Syndrome Scoring

The MetSyn_Criteria_Count column requires you to evaluate five Boolean conditions per patient and sum them. In the Q column, enter:

```text
=((C2="M")*(G2>=102)+(C2="F")*(G2>=88))
+((H2>=130)+(I2>=85)>0)
+(J2>=5.6)
+(K2>=6.5)
+(L2>=1.7)
+((C2="M")*(M2<1.0)+(C2="F")*(M2<1.3))
```

This formula evaluates waist circumference against sex-specific cut-offs, flags either SBP or DBP breach as a single criterion, checks fasting glucose, HbA1c (as a glucose surrogate within the screening context), triglycerides, and HDL-C. The maximum possible score is 6 because HbA1c and FPG both reflect the glycemia criterion and may both be elevated simultaneously — the formula counts them independently for scoring purposes, but clinically the glycemia criterion is counted only once. Adjust the formula by wrapping the FPG and HbA1c terms in a combined OR-style cap:

```text
=((C2="M")*(G2>=102)+(C2="F")*(G2>=88))
+MIN(1,((H2>=130)+(I2>=85)))
+MIN(1,((J2>=5.6)+(K2>=6.5)))
+(L2>=1.7)
+MIN(1,((C2="M")*(M2<1.0)+(C2="F")*(M2<1.3)))
```

The expected MetSyn_Criteria_Count results are: PT-001 = 5, PT-002 = 3, PT-003 = 5, PT-004 = 0, PT-005 = 3. In the R column (MetSyn_Diagnosis), enter `=IF(Q2>=3,"YES","NO")`. PT-001, PT-002, PT-003, and PT-005 all meet criteria.

In the S column (DM_Status), apply the following tiered classification:

```text
=IF(OR(J2>=7.0,K2>=6.5),"T2DM",IF(OR(J2>=5.6,K2>=5.7),"Pre-DM","Normoglycemic"))
```

Results: PT-001 = Pre-DM, PT-002 = Pre-DM, PT-003 = T2DM, PT-004 = Normoglycemic, PT-005 = T2DM.

### 1.3 — OGTT Simulation and Glucose Curve Construction

Navigate to the OGTT_Plotter tab. A 75g oral glucose tolerance test generates a characteristic time-concentration curve that reveals not just diagnostic category but the kinetic signature of insulin resistance: a delayed and exaggerated peak, a prolonged elevation, and a sluggish return toward fasting values. You will simulate this curve for three patient archetypes using a compartmental model.

The two-compartment OGTT model approximates plasma glucose at time *t* (in minutes) as:

**G(t) = G_fasting + A × (e^(−k₂t) − e^(−k₁t))**

where A is the peak amplitude above fasting, k₁ is the absorption rate constant (glucose appearance), and k₂ is the elimination rate constant (insulin-mediated disposal). For a normoglycemic individual, use A = 4.5 mmol/L, k₁ = 0.025 min⁻¹, k₂ = 0.012 min⁻¹. For a pre-diabetic individual, use A = 6.2 mmol/L, k₁ = 0.018 min⁻¹, k₂ = 0.008 min⁻¹. For a T2DM individual, use A = 8.8 mmol/L, k₁ = 0.012 min⁻¹, k₂ = 0.005 min⁻¹.

In column A of the OGTT_Plotter tab, enter time points 0, 15, 30, 45, 60, 90, 120, 150, 180 in rows 2–10. In columns B, C, D enter the respective G(t) formulas. For the normoglycemic column B, with fasting glucose of 4.8 mmol/L:

```text
=4.8+4.5*(EXP(-0.012*A2)-EXP(-0.025*A2))
```

For pre-diabetic (fasting 5.6 mmol/L) in column C:

```text
=5.6+6.2*(EXP(-0.008*A2)-EXP(-0.018*A2))
```

For T2DM (fasting 7.2 mmol/L) in column D:

```text
=7.2+8.8*(EXP(-0.005*A2)-EXP(-0.012*A2))
```

Select columns A through D, insert a scatter chart with smooth lines, and label the series. Add horizontal reference lines at 7.8 mmol/L (impaired glucose tolerance threshold) and 11.1 mmol/L (T2DM threshold) using secondary series with constant values across all nine time points. The resulting chart will show the normoglycemic curve peaking around minute 30–45 at approximately 7.1 mmol/L and returning below 7.8 mmol/L by minute 90. The T2DM curve will peak near minute 60–75 at approximately 12.4 mmol/L and remain above the diagnostic threshold through minute 120, visually demonstrating why the 2-hour value is the operative diagnostic criterion in the OGTT rather than the peak.

This graph is not decorative. Use it in clinical rounds or patient counseling to explain why post-prandial glucose monitoring at 1 hour (which captures the kinetic peak better than 2 hours in some individuals) is now being evaluated as a superior screening window in patients with borderline 2-hour results.

---

## Exercise 2: Parameter Variation & Empirical Analysis

### 2.1 — UKPDS-Based Cardiovascular Risk Calculation

The UKPDS Risk Engine (version 2.0) estimates 10-year coronary heart disease (CHD) risk in patients with Type 2 diabetes using eight variables: age at diagnosis, duration of diabetes, sex, ethnicity, smoking status, systolic blood pressure, total cholesterol-to-HDL ratio, and HbA1c. Navigate to the CV_Risk_Engine tab and build the following calculation framework.

The simplified UKPDS CHD risk equation for a non-smoking White male patient is:

**CHD_Risk (%) = 1 − 0.9333^exp(L − 3.8524)**

where L is the linear predictor:

**L = 0.0112 × Age_at_dx + 0.0171 × Duration + 0.0115 × SBP + 0.4728 × ln(TC/HDL) + 0.3337 × HbA1c_pct**

In column A, label rows as: Age_at_diagnosis, Duration_years, SBP_mmHg, TC_HDL_ratio, HbA1c_pct, L_value, CHD_Risk_10yr. In column B, enter the input values, and in column C, enter the computed values. For PT-003 (61 years old, diagnosed at age 55, 6 years duration, SBP 152, TC = LDL + HDL + TG/2.2 = 4.1 + 0.8 + 3.8/2.2 = 6.63 mmol/L, TC/HDL = 6.63/0.8 = 8.29, HbA1c 8.4%):

```text
L = (0.0112 × 55) + (0.0171 × 6) + (0.0115 × 152) + (0.4728 × LN(8.29)) + (0.3337 × 8.4)
L = 0.616 + 0.103 + 1.748 + 0.993 + 2.803
L = 6.263
```

CHD_Risk = 1 − 0.9333^exp(6.263 − 3.8524) = 1 − 0.9333^exp(2.411) = 1 − 0.9333^11.14 = 1 − 0.4592 = **54.1%**

In spreadsheet formula form in cell C6:

```text
=1-(0.9333^EXP((0.0112*B1)+(0.0171*B2)+(0.0115*B3)+(0.4728*LN(B4))+(0.3337*B5)-3.8524))
```

PT-003 carries a 54.1% 10-year CHD risk, which places this patient firmly in the very high-risk category demanding immediate statin therapy (atorvastatin 40–80 mg), ACE inhibitor or ARB initiation for the BP of 152/96, and an HbA1c reduction target of < 53 mmol/mol (7.0%) while balancing hypoglycemia risk given eGFR of 65.

Repeat this calculation for PT-005 (diagnosed at 60, 6 years duration, SBP 144, TC = 3.7 + 1.1 + 1.9/2.2 = 5.66 mmol/L, TC/HDL = 5.66/1.1 = 5.15, HbA1c 7.1%). Expected L = 5.84, CHD_Risk = 44.7%. Now vary HbA1c from 6.0% to 10.0% in 0.5% increments and record the resulting CHD_Risk in a sensitivity table. Create a data table in the spreadsheet using Excel's Data > What-If Analysis > Data Table function (one-variable, with HbA1c_pct as the row input cell). The resulting gradient demonstrates that each 1% reduction in HbA1c reduces 10-year CHD risk by approximately 3.5–4.5 percentage points in this risk profile — a number worth quoting directly to a patient who is debating whether medication adjustment is "worth it."

### 2.2 — Insulin Resistance Index Computation and Interpretation

The Homeostatic Model Assessment of Insulin Resistance (HOMA-IR) quantifies insulin resistance from a single fasting blood draw. The formula is:

**HOMA-IR = (Fasting Insulin µU/mL × Fasting Glucose mmol/L) / 22.5**

Add five rows to the Patient_Registry for a second cohort with known fasting insulin values:

| Patient_ID | FPG_mmol | Fasting_Insulin_µU/mL |
|---|---|---|
| PT-006 | 5.8 | 14.2 |
| PT-007 | 6.4 | 22.7 |
| PT-008 | 7.1 | 8.4 |
| PT-009 | 5.1 | 9.6 |
| PT-010 | 9.3 | 6.1 |

HOMA-IR results: PT-006 = 3.66, PT-007 = 6.46, PT-008 = 2.65, PT-009 = 2.17, PT-010 = 2.52. The reference range cutoff for insulin resistance is HOMA-IR >2.5–3.0 depending on the population studied; use 2.9 as your operational threshold. PT-006 and PT-007 are insulin resistant by this criterion. PT-008 and PT-010 are of particular clinical interest: both have elevated FPG yet low HOMA-IR, which is the metabolic signature of beta-cell failure rather than insulin resistance. These patients are secreting inadequate insulin relative to their glucose load — a distinction that radically changes pharmacotherapy. PT-007, with the highest HOMA-IR of 6.46 and an FPG still below the T2DM threshold, is the ideal candidate for metformin initiation (500 mg twice daily with meals, titrating to 1000 mg twice daily over 4 weeks) and an intensive lifestyle program targeting 7% body weight loss.

Compute the QUICKI (Quantitative Insulin Sensitivity Check Index) for each patient as a cross-validation:

**QUICKI = 1 / (log₁₀(Insulin µU/mL) + log₁₀(Glucose mg/dL))**

Convert FPG from mmol/L to mg/dL by multiplying by 18.0182. For PT-007: Glucose = 6.4 × 18.0182 = 115.3 mg/dL.

```text
QUICKI = 1 / (LOG10(22.7) + LOG10(115.3))
       = 1 / (1.356 + 2.062)
       = 1 / 3.418
       = 0.293
```

QUICKI values below 0.339 indicate insulin resistance; below 0.312 indicates overt T2DM-level resistance. PT-007 at 0.293 confirms severe insulin resistance, consistent with HOMA-IR of 6.46. Build a scatter plot with HOMA-IR on the x-axis and QUICKI on the y-axis for all ten patients to visually confirm the inverse nonlinear relationship between the two indices. Add a power trendline (not linear) in Excel by right-clicking the series and selecting "Power" from the trendline options. The R² should exceed 0.92, confirming that both indices are measuring the same physiological construct through different mathematical lenses.

### 2.3 — Lipid Panel Analysis and Atherogenic Index Computation

The Atherogenic Index of Plasma (AIP) is a logarithmic ratio of triglycerides to HDL cholesterol in mmol/L that outperforms individual lipid fractions in predicting cardiovascular events in metabolic syndrome:

**AIP = log₁₀(TG mmol/L / HDL mmol/L)**

Compute AIP for all five original patients. Enter the formula `=LOG10(L2/M2)` in a new column of the Patient_Registry. Results: PT-001 = log₁₀(2.1/0.9) = 0.368, PT-002 = log₁₀(1.6/1.2) = 0.125, PT-003 = log₁₀(3.8/0.8) = 0.676, PT-004 = log₁₀(0.9/1.6) = −0.250, PT-005 = log₁₀(1.9/1.1) = 0.237.

Interpretation thresholds: AIP < 0.11 is low risk; 0.11–0.21 is intermediate risk; >0.21 is high risk. PT-001, PT-003, and PT-005 all fall in the high-risk zone. PT-003's AIP of 0.676 is exceptional — this degree of dyslipidemia, combined with the UKPDS CHD risk of 54.1%, makes aggressive lipid-lowering non-negotiable. Fenofibrate 145 mg daily may be considered as an adjunct to statin therapy specifically to address the TG of 3.8 mmol/L, particularly given the associated pancreatitis risk above 5.6 mmol/L.

Build a stacked bar chart showing each patient's AIP value with color-coded background bands at the three risk thresholds. This visualization is suitable for direct use in a clinical audit or quality improvement presentation.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### 3.1 — Edge Case Identification: Euglycemic Metabolic Syndrome

The diagnostic architecture you built in Exercise 1 rests on threshold-based Boolean logic, which creates hard boundaries in a continuous physiological landscape. Exercise 3 systematically stress-tests those boundaries to identify where your model fails and what clinical action to take when it does.

Consider a patient with the following values: Age 52, Male, waist 103 cm, SBP 131, DBP 84, FPG 5.5 mmol/L, HbA1c 5.6%, TG 1.65 mmol/L, HDL 1.05 mmol/L. Enter this as PT-011 and run the MetSyn scoring formula. The result should be MetSyn_Criteria_Count = 2 (waist and blood pressure), giving a MetSyn_Diagnosis of NO. Yet this patient sits at the edge of three additional criteria: TG at 97% of the diagnostic threshold, HDL at 105% of the diagnostic threshold, and FPG at 98% of the threshold. A re-measurement one week later after a high-saturated-fat meal and mild dehydration could easily produce TG 1.75, HDL 0.98, and FPG 5.7, flipping three criteria simultaneously to give MetSyn_Criteria_Count = 5.

This is the analytical boundary failure of threshold-based models. Your recovery protocol has two components. First, implement a "proximity flag" column in the spreadsheet that marks any criterion as "borderline" when it falls within 10% below the diagnostic threshold:

```text
=IF(AND(C2="M",G2>=92,G2<102),"Borderline-Waist",
   IF(AND(C2="F",G2>=79,G2<88),"Borderline-Waist",""))
```

Apply equivalent formulas for TG (flag when 1.53–1.69 mmol/L), HDL-M (flag when 1.00–1.09 mmol/L), HDL-F (flag when 1.30–1.42 mmol/L), SBP (flag when 120–129 mmHg), and FPG (flag when 5.0–5.5 mmol/L). A patient with two confirmed criteria and three proximity flags should be treated clinically as equivalent to metabolic syndrome pending confirmatory repeat testing at 4–6 weeks — this is the operational recovery protocol for boundary-zone patients.

Second, implement the continuous MetSyn severity score proposed by Kassi et al. by z-scoring each of the five components against the population mean and summing the absolute deviations. Use the following population reference values for a Western adult population: waist mean = 94 cm, SD = 14 cm; SBP mean = 122 mmHg, SD = 18 mmHg; FPG mean = 5.1 mmol/L, SD = 0.9 mmol/L; TG mean = 1.4 mmol/L, SD = 0.6 mmol/L; HDL mean = 1.3 mmol/L, SD = 0.3 mmol/L (inverted, since lower is worse). For PT-011:

```text
Z_waist = (103 − 94) / 14 = 0.643
Z_SBP   = (131 − 122) / 18 = 0.500
Z_FPG   = (5.5 − 5.1) / 0.9 = 0.444
Z_TG    = (1.65 − 1.4) / 0.6 = 0.417
Z_HDL   = (1.3 − 1.05) / 0.3 = 0.833  [inverted: (mean − observed) / SD]

Continuous_MetSyn_Score = 0.643 + 0.500 + 0.444 + 0.417 + 0.833 = 2.837
```

A continuous score above 2.5 identifies individuals at equivalent metabolic risk to those meeting categorical criteria, even when they fall one criterion short of the binary cutoff. Add this column to your spreadsheet with the full z-score formula chain, and validate it against all eleven patients. PT-011 scores 2.837, correctly flagging this boundary patient as high-risk despite failing the binary MetSyn diagnosis.

### 3.2 — Medication Interaction and Glycemia Stress Test

The clinical stress test in this section simulates what happens to your five core patients' metabolic panel under common pharmacological interventions that adversely affect glycemia or lipids, allowing you to predict iatrogenic metabolic decompensation before it happens.

Build a Medication_Stress tab in your workbook. The following medications carry documented dysglycemic or dyslipidemic effects at the specified magnitudes based on published meta-analytic data:

| Medication Class | FPG Effect (mmol/L) | HbA1c Effect (%) | TG Effect | HDL Effect |
|---|---|---|---|---|
| Thiazide diuretic (high-dose) | +0.5 | +0.3 | +0.3 mmol/L | −0.05 mmol/L |
| Beta-blocker (non-selective) | +0.3 | +0.2 | +0.2 mmol/L | −0.08 mmol/L |
| Atypical antipsychotic (olanzapine) | +1.4 | +0.8 | +0.6 mmol/L | −0.12 mmol/L |
| High-dose glucocorticoid (prednisone ≥20 mg) | +3.2 | +1.5 | +0.8 mmol/L | −0.05 mmol/L |
| Combined OCP (levonorgestrel) | +0.2 | +0.1 | +0.4 mmol/L | −0.10 mmol/L |

For each patient-medication combination, write a formula that applies the effect delta to the baseline value and then re-runs the DM_Status classification and MetSyn scoring. For PT-001 (Pre-DM, MetSyn positive) initiated on a thiazide diuretic for hypertension management:

```text
Stressed_FPG  = 6.2 + 0.5 = 6.7 mmol/L
Stressed_HbA1c = 6.8 + 0.3 = 7.1%
Stressed_TG   = 2.1 + 0.3 = 2.4 mmol/L
Stressed_HDL  = 0.9 − 0.05 = 0.85 mmol/L
```

Re-running the DM_Status formula: FPG 6.7 is below 7.0 mmol/L but HbA1c 7.1% is ≥6.5%, classifying this patient as T2DM after thiazide initiation. Document this as a **pharmacologically-induced diabetes conversion event**. The recovery protocol for this scenario is substitution with a calcium channel blocker (amlodipine 5–10 mg) or an ACE inhibitor (ramipril 5–10 mg), both of which carry neutral or favorable metabolic profiles and are appropriate for this patient's BP of 138/88 with established metabolic syndrome.

Apply the glucocorticoid stress to PT-003 (already T2DM with FPG 8.9): stressed FPG = 8.9 + 3.2 = 12.1 mmol/L. This patient would require basal insulin initiation (insulin glargine 10 units subcutaneous at bedtime, titrated by 2 units every 3 days targeting fasting glucose 4.4–7.2 mmol/L) for steroid-induced hyperglycemia management, in addition to continuing existing oral agents unless contraindicated.

### 3.3 — CKD-Adjusted Drug Dosing Protocol

PT-003 (eGFR 65) and PT-005 (eGFR 54) require eGFR-adjusted pharmacotherapy decisions. Build a Drug_Dosing_Check tab with the following reference table and an automated flagging formula:

| Drug | Full Dose | eGFR 45–60 Action | eGFR 30–45 Action | eGFR < 30 Action |
|---|---|---|---|---|
| Metformin 1000 mg BD | Standard | Reduce to 500 mg BD | Reduce to 500 mg OD | STOP |
| Dapagliflozin 10 mg | Standard | Reduce to 5 mg; efficacy reduced | STOP | STOP |
| Sitagliptin 100 mg | Standard | Reduce to 50 mg | Reduce to 25 mg | 25 mg OD |
| Empagliflozin 10 mg | Standard | STOP (eGFR< 45) | STOP | STOP |
| Ramipril 10 mg | Standard | 75% dose (7.5 mg) | 50% dose (5 mg) | Specialist review |

Enter each patient's eGFR in column B of this tab and use nested IF formulas to output the appropriate drug action automatically. For PT-005 (eGFR 54) on dapagliflozin:

```text
=IF(B2>=60,"Standard 10mg",IF(AND(B2>=45,B2<60),"Reduce to 5mg - efficacy reduced",IF(AND(B2>=30,B2<45),"STOP",IF(B2<30,"STOP","Check eGFR"))))
```

This tab becomes a live clinical safety tool: any time you update a patient's eGFR (quarterly for CKD G2–3), the drug actions update automatically, flagging medications that must be discontinued before they cause volume depletion nephrotoxicity or lactic acidosis.

---

## Operational Reference Guide & Diagnostic Checklist

### Master Clinical Audit Rubric

The following audit rubric is designed for case-based review in a clinical training environment, quality improvement audit, or objective structured clinical examination (OSCE) station. Apply it to any patient case in the registry to generate a structured competency score.

**Domain 1 — Diagnostic Accuracy (25 points)**
Score 5 points for each of the following correctly computed: BMI from height and weight, eGFR from CKD-EPI formula with sex correction, MetSyn criteria count with sex-appropriate waist cut-off, DM_Status using correct threshold precedence, and AIP computed and correctly interpreted against the three-tier risk scale. Deduct 3 points for any threshold applied to the wrong sex.

**Domain 2 — Risk Stratification (25 points)**
Score 5 points each for: HOMA-IR computed and interpreted against the 2.9 threshold, QUICKI cross-validated and consistent with HOMA-IR direction, UKPDS CHD risk computed with correct L-value assembly, AIP classified into the correct risk tier, and the continuous MetSyn z-score computed with correct HDL inversion. Deduct 5 points if the UKPDS calculation omits duration of diabetes as a separate variable from age at diagnosis.

**Domain 3 — Pharmacotherapy Safety (25 points)**
Score 5 points each for: identifying the correct eGFR threshold for metformin dose reduction, flagging SGLT2 inhibitor cessation at eGFR < 45, applying the correct statin intensity (high-intensity defined as atorvastatin ≥40 mg or rosuvastatin ≥20 mg) to any patient with UKPDS CHD risk >20%, identifying thiazide diuretic as a diabetes conversion risk in a Pre-DM patient with MetSyn, and recommending ACE/ARB preference over thiazide or beta-blocker in a hypertensive T2DM patient with microalbuminuria.

**Domain 4 — Boundary Case Management (25 points)**
Score 5 points each for: implementing the 10% proximity flag for borderline-threshold patients, computing the continuous MetSyn z-score for a patient who fails binary criteria, correctly identifying the beta-cell failure pattern (high FPG + low HOMA-IR) as distinct from insulin resistance (high FPG + high HOMA-IR), managing steroid-induced hyperglycemia with basal insulin rather than increasing oral agents, and re-classifying post-medication-stress DM_Status correctly.

A score of 90–100 reflects mastery. 75–89 reflects competent practice with one significant gap. Below 75 requires targeted remediation in the failed domain before independent case management.

### Rapid Field Reference — Key Diagnostic Thresholds

| Parameter | Pre-Diabetes | T2DM | MetSyn Criterion |
|---|---|---|---|
| FPG | 5.6–6.9 mmol/L | ≥7.0 mmol/L | ≥5.6 mmol/L |
| 2h OGTT | 7.8–11.0 mmol/L | ≥11.1 mmol/L | — |
| HbA1c | 39–47 mmol/mol (5.7–6.4%) | ≥48 mmol/mol (6.5%) | — |
| TG | — | — | ≥1.7 mmol/L |
| HDL-M | — | — | < 1.0 mmol/L |
| HDL-F | — | — | < 1.3 mmol/L |
| Waist-M | — | — | ≥102 cm |
| Waist-F | — | — | ≥88 cm |
| SBP/DBP | — | — | ≥130/85 mmHg |
| HOMA-IR | 2.9–4.0 (at-risk) | Variable | — |
| AIP | 0.11–0.21 (intermediate) | >0.21 (high) | — |
| eGFR action | — | < 60: metformin review | < 45: SGLT2i STOP |

### Diagnostic Algorithm: First 60 Minutes with an Undiagnosed Patient

When you receive a patient with suspected diabetes or metabolic syndrome and no prior workup, the following sequence maximizes diagnostic yield from a single fasting blood draw and a 10-minute physical examination. Begin with the anthropometric assessment: measure waist circumference at the level of the iliac crest, not the umbilicus, using a non-elastic tape measure in the standing patient at end-expiration. Record weight in minimal clothing on a calibrated scale. Record height without shoes. Calculate BMI immediately.

Measure blood pressure after the patient has been seated for 5 minutes in a chair with back support, feet flat, arm at heart level, using a cuff covering 80% of arm circumference. Record two readings 1–2 minutes apart and use the average. If radial pulse is irregular, auscultate manually for atrial fibrillation before interpreting the BP reading.

From the fasting blood draw, the minimum panel is: FPG, HbA1c, fasting lipid profile (TC, LDL, HDL, TG), creatinine, and urine albumin-to-creatinine ratio (UACR). Fasting insulin should be added if HOMA-IR computation is desired and the laboratory can process it. With these values, you can compute every metric in this lab guide within 15 minutes of receiving the results.

The clinical priority order for intervention, once diagnosis is confirmed, follows the absolute risk reduction hierarchy: smoking cessation (if applicable) produces the largest single-variable CV risk reduction; blood pressure control to < 130/80 mmHg produces the second largest reduction in microvascular endpoints; lipid-lowering with high-intensity statin therapy reduces MACE by 25% per 1 mmol/L LDL reduction; glycemic control targets HbA1c individualized to < 53 mmol/mol (7%) in most patients or < 58 mmol/mol (7.5%) in elderly patients with significant comorbidity or hypoglycemia risk. SGLT2 inhibitors and GLP-1 receptor agonists with demonstrated CV and renal outcomes data (empagliflozin, dapagliflozin, liraglutide, semaglutide) should be prioritized in patients with established cardiovascular disease, heart failure, or CKD regardless of baseline HbA1c, as their benefit is independent of glycemic effect.

This operational framework — registry construction, formula-driven risk calculation, boundary-zone flagging, pharmacological stress testing, and audit-ready scoring — constitutes the repeatable analytical cycle that separates reactive clinical documentation from proactive metabolic risk management.
