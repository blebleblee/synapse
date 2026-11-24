# Operational Verification Labs: Cancer Biology and Oncology

## Objective & Operational Lab Setup

This guide functions as a working laboratory manual for the clinical and research practitioner who needs to move from conceptual understanding of oncology into verifiable, repeatable analytical work. The three exercises that follow operate progressively: the first demands that you reconstruct a tumor's biological logic from pathology data alone; the second requires you to stress-test a treatment decision against pharmacokinetic and resistance variables; the third places you inside a metastatic cascade failure scenario where the standard of care has broken down and you must triage, recalculate, and recover a patient's therapeutic plan. Each exercise uses toolchains that are native to the clinical and translational medicine environment—histopathological scoring rubrics, TNM staging frameworks, genomic variant interpretation, pharmacodynamic modeling in a spreadsheet environment, and evidence-based audit criteria drawn from NCCN, ESMO, and RECIST 1.1 guidelines.

Before beginning, your analytical environment must be configured as follows. You need access to a spreadsheet application capable of iterative calculation—Microsoft Excel with Solver enabled, or Google Sheets with the iterative calculation toggle activated under Settings → Calculation. You will also use the publicly available cBioPortal for Cancer Genomics (cbioportal.org), the NCI's GDC Data Portal, and the COSMIC (Catalogue of Somatic Mutations in Cancer) database, all accessible via standard browser. Download and print, or keep open in a parallel window, the current NCCN Clinical Practice Guidelines in Oncology for Non-Small Cell Lung Cancer (freely available with registration), the AJCC Cancer Staging Manual 8th Edition TNM criteria for the relevant tumor type used in each exercise, and the RECIST 1.1 criteria document. Have a scientific calculator or the spreadsheet open for all quantitative work. Each exercise assumes you are working as an attending oncologist or senior oncology fellow with access to a multidisciplinary tumor board, and the analytical decisions you make should reflect that level of clinical accountability.

---

## Exercise 1: Foundational Practical Implementation

### Reconstructing Tumor Biology from a Pathology Package and Staging a New Diagnosis

The entry point for every oncology case is the pathology report paired with imaging, and the practitioner's first operational act is to extract the full biological picture from that document before any treatment discussion begins. This exercise gives you a complete, realistic pathology and imaging dataset and requires you to work through histological grading, molecular subtyping, formal TNM staging, and prognosis estimation using validated actuarial tables. You will not summarize; you will execute each step as you would on a live patient.

**The Clinical Dataset**

Your patient is a 61-year-old male, former 40-pack-year smoker who quit seven years ago, presenting with a six-week history of progressive dyspnea and an incidental 3.8 cm spiculated right upper lobe mass on chest radiograph. The CT of the chest, abdomen, and pelvis reports a 3.8 × 3.2 × 3.0 cm spiculated right upper lobe mass abutting but not invading the visceral pleura, two ipsilateral hilar lymph nodes measuring 1.4 cm and 1.1 cm (both PET-avid with SUVmax 6.2 and 5.8 respectively), no mediastinal nodal involvement, no pleural effusion, and no distant metastases. Brain MRI is negative. The patient underwent CT-guided core needle biopsy. The pathology report reads as follows.

*Gross description:* Three cores of tan-white firm tissue, each 1.4 cm in length. *Microscopic description:* Sections show a moderately differentiated adenocarcinoma with acinar-predominant growth pattern, focal lepidic component comprising approximately 15% of the sampled tumor, and scattered micropapillary foci. Moderate nuclear pleomorphism, frequent mitoses at 8 per 10 high-power fields. No necrosis identified. *Immunohistochemistry panel:* TTF-1 positive (strong, diffuse), Napsin-A positive, p40 negative, CK5/6 negative, Synaptophysin negative, Chromogranin negative. PD-L1 TPS (Tumor Proportion Score) by 22C3 pharmDx assay: 55%. *Molecular testing (NGS panel, 592-gene):* EGFR exon 19 deletion detected (pathogenic), TP53 R248W co-mutation detected (pathogenic), no ALK rearrangement, no ROS1 rearrangement, no MET exon 14 skipping, no KRAS mutation, no BRAF V600E, TMB 6 mutations/megabase.

**Step 1.1 — Histological Grade and Subtype Verification**

Working from the microscopic description, confirm the tumor type and grade using the 2021 WHO Classification of Thoracic Tumours. Adenocarcinoma is confirmed by the acinar-predominant pattern and positive TTF-1/Napsin-A with negative squamous markers. Under the 2021 WHO framework, lung adenocarcinoma is graded on a three-tier system: Grade 1 is lepidic-predominant with no high-grade patterns, Grade 2 is acinar- or papillary-predominant with no high-grade patterns, and Grade 3 is any tumor with micropapillary or solid predominance, or any tumor with high-grade patterns comprising 20% or more. This tumor is acinar-predominant with a micropapillary component that must be quantified. The report states micropapillary foci are present but does not give a percentage. In clinical practice your next action is to contact the pathologist directly and request quantification of the micropapillary component. For the purposes of this exercise, assume the pathologist addends the report: micropapillary component 18%, solid component 0%. Per the 2021 WHO criteria, a micropapillary component of any percentage upstages the histological grade to Grade 3. Record this: **WHO Grade 3 adenocarcinoma, acinar-predominant with high-grade micropapillary component (18%).** The mitotic rate of 8 per 10 HPF is consistent with Grade 3 biology. The lepidic 15% component does not change the grade because the dominant pattern and the presence of a high-grade pattern override it.

**Step 1.2 — TNM Staging (AJCC 8th Edition)**

Open the AJCC 8th Edition criteria for lung. Work each descriptor independently before assembling the stage.

For the T descriptor: the primary tumor measures 3.8 cm in greatest dimension. Per AJCC 8th Edition lung criteria, T1 is ≤3 cm, T2a is >3 cm and ≤4 cm. The 3.8 cm measurement places this in **T2a**. The CT report notes the tumor abuts but does not invade the visceral pleura. Visceral pleural invasion (VPI) would upgrade to T2 regardless of size; because invasion is absent, the T2a designation based on size alone stands. Confirm this with the pathologist's report: elastic stain (Verhoeff-Van Gieson or orcein) should have been performed on the biopsy. If the report does not mention an elastic stain and VPI cannot be excluded on H&E alone, flag this for surgical pathology review at resection.

For the N descriptor: the report describes two PET-avid ipsilateral hilar lymph nodes at 1.4 cm and 1.1 cm. The hilar station is N1. No mediastinal nodes are involved. Record **N1**. Note that radiological size and PET avidity do not replace pathological confirmation in a potentially resectable patient. Per NCCN and ESMO guidelines, nodes ≥1 cm on CT or PET-avid nodes require mediastinal staging. Because these are hilar (N1) rather than mediastinal (N2/N3), and the mediastinum is PET-negative, endobronchial ultrasound (EBUS) should still be performed to pathologically confirm N1 and exclude occult N2 disease before resecting. Record the clinical N as **cN1**, pending pathological confirmation.

For the M descriptor: brain MRI negative, no distant metastases, no malignant pleural effusion. **M0.**

Assembled clinical stage: **cT2a cN1 M0 = Stage IIB.** This is a critical inflection point. Stage IIB non-small cell lung cancer sits at the boundary of definitive surgical resection with adjuvant therapy versus concurrent chemoradiation, depending on mediastinal staging results and patient performance status.

**Step 1.3 — Molecular Subtype and Targetable Alteration Mapping**

Open cBioPortal. Navigate to the Mutation tab. Search for EGFR exon 19 deletion in lung adenocarcinoma. You will see this alteration is present in approximately 12–15% of Western NSCLC patients and 30–40% of East Asian patients. Its functional consequence is constitutive kinase activation of the EGFR receptor, driving downstream RAS-RAF-MEK-ERK and PI3K-AKT-mTOR proliferative signaling. The critical clinical implication is not the biology itself but the therapeutic actionability: EGFR exon 19 deletions confer sensitivity to first-, second-, and third-generation EGFR tyrosine kinase inhibitors (TKIs), with osimertinib (third-generation) now holding Level 1A evidence for both first-line metastatic and adjuvant resected EGFR-mutant NSCLC (ADAURA trial data).

The TP53 R248W co-mutation requires separate interpretation. In COSMIC, TP53 R248W is a hotspot gain-of-function mutation associated with dominant-negative p53 activity, impaired apoptotic response, and—critically for this case—emerging data suggesting it may attenuate response durability to EGFR TKIs and accelerate acquired resistance mechanisms. Record this as a **prognostic co-mutation with potential resistance implications**, not a currently targetable alteration.

The PD-L1 TPS of 55% is positive but does not drive first-line treatment in this EGFR-mutant patient. The KEYNOTE-789 trial demonstrated that adding pembrolizumab to chemotherapy did not improve outcomes in EGFR-mutant metastatic NSCLC, and there is consistent evidence that PD-1/PD-L1 inhibitor monotherapy is inferior to EGFR TKIs in EGFR-mutant disease. Record the PD-L1 score as a **biomarker noted but not treatment-directing** given the EGFR driver mutation.

**Step 1.4 — Prognosis Estimation**

Using the SEER database 5-year survival statistics (2012–2018 data, the most recent available through NCI SEER Explorer), Stage IIB NSCLC carries a 5-year relative survival rate of approximately 31% for all comers. However, EGFR exon 19 deletion status in resected Stage IIB disease treated with adjuvant osimertinib (ADAURA) demonstrated a disease-free survival hazard ratio of 0.17 at 4 years, representing a dramatic improvement in DFS. The overall survival data from ADAURA showed a hazard ratio of 0.49 for EGFR-mutant patients receiving adjuvant osimertinib. Document your complete staging and biological characterization in the following structured format, which you will carry forward into Exercise 2.

| Parameter | Finding |
|---|---|
| Histology | Lung adenocarcinoma, WHO Grade 3 |
| Dominant Pattern | Acinar (67%) |
| High-Grade Pattern | Micropapillary (18%) |
| PD-L1 TPS | 55% (22C3) |
| Driver Mutation | EGFR exon 19 deletion (pathogenic) |
| Co-mutation | TP53 R248W (pathogenic) |
| Clinical Stage | cT2a cN1 M0 — Stage IIB |
| Pending Confirmation | EBUS pathological N staging, elastic stain VPI |
| Primary Treatment Path | Surgical resection + adjuvant osimertinib (ADAURA) if pN0–N1; concurrent CRT if pN2 confirmed |

---

## Exercise 2: Parameter Variation & Empirical Analysis

### Pharmacokinetic Stress-Testing a Treatment Decision Under Variable Patient Parameters

Exercise 1 delivered a clean, operable case. This exercise introduces the analytical complexity that governs real therapeutic decisions: the same molecular diagnosis but different patient parameters that require you to quantitatively stress-test your treatment plan. You will build a pharmacodynamic comparison model in a spreadsheet, run a resistance timeline projection, and adjudicate a treatment sequence decision using evidence-based criteria.

**The Modified Clinical Dataset**

Advance this patient five years. He underwent right upper lobectomy with mediastinal lymph node dissection. Final pathology confirmed pT2a pN1 M0 (two hilar nodes positive, 2/8 sampled; mediastinal nodes negative). He completed three years of adjuvant osimertinib 80 mg daily per ADAURA protocol, tolerated well, and was disease-free for 48 months post-surgery. He now presents with a new 2.1 cm right lower lobe lesion on surveillance CT and a 1.3 cm right paratracheal lymph node. PET-CT confirms both are FDG-avid (SUVmax 7.4 and 4.1). Brain MRI shows two new lesions: 0.8 cm right frontal and 0.6 cm left cerebellar, both with mild surrounding edema. Liquid biopsy (plasma cell-free DNA) is returned: EGFR exon 19 deletion persists, **EGFR T790M mutation detected** at a variant allele fraction (VAF) of 18%, **C797S mutation detected** at VAF 7%.

This is now **Stage IV recurrent NSCLC** with acquired resistance to osimertinib via a T790M + C797S double mutation, one of the most clinically challenging resistance mechanisms in thoracic oncology.

**Step 2.1 — Building the Pharmacodynamic Decision Model in a Spreadsheet**

Open a new spreadsheet. Create the following structure beginning in cell A1.

In cells A1 through A3, enter the headers: **Patient ID**, **Age**, **Weight (kg)**. In B1 through B3 enter: *Patient-Ex2*, *66*, *78*. These will anchor all subsequent calculations.

Beginning in row 5, build a drug comparison table. The clinical decision in this patient is between three second-line or salvage options: (1) platinum-doublet chemotherapy (carboplatin AUC 5 + pemetrexed 500 mg/m²), (2) enrollment in a clinical trial of a fourth-generation EGFR TKI targeting C797S (using published BLU-945 or BBT-176 phase I data as your reference pharmacology), or (3) amivantamab + lazertinib (MARIPOSA-2 data) for osimertinib-resistant NSCLC. Enter the following table:

| Cell | Entry |
|---|---|
| A5 | Regimen |
| B5 | Mechanism |
| C5 | Key Eligibility Constraint |
| D5 | Expected PFS (months, median) |
| E5 | ORR (%) |
| F5 | CNS Penetration |
| G5 | Resistance Mechanism Covered |

Row 6 (Carboplatin/Pemetrexed):

| A6 | Carboplatin AUC5 + Pemetrexed 500 mg/m² |
| B6 | DNA crosslinking + thymidylate synthase inhibition |
| C6 | CrCl ≥45 mL/min, B12/folate supplementation required |
| D6 | 4.4 (IMPOWER150 chemo arm reference) |
| E6 | 27 |
| F6 | Poor (BBB limited) |
| G6 | Cytotoxic; mechanism-agnostic |

Row 7 (Amivantamab + Lazertinib):

| A7 | Amivantamab 1050mg IV + Lazertinib 240mg PO |
| B7 | EGFR/MET bispecific antibody + 3rd-gen TKI |
| C7 | ECOG PS 0–1, no prior amivantamab |
| D7 | 6.3 (MARIPOSA-2) |
| E7 | 33 |
| F7 | Moderate (lazertinib CNS penetration documented) |
| G7 | Overcomes some post-osimertinib resistance; C797S coverage partial |

Row 8 (Clinical Trial — 4th-gen TKI):

| A8 | BLU-945 (phase I; 400mg BID target dose) |
| B8 | EGFR inhibitor designed for T790M+C797S in cis |
| C8 | Trial eligibility: EGFR ex19del + T790M + C797S confirmed; no prior BLU-945 |
| D8 | Not yet mature; phase I ORR reference: 29% at 400mg BID |
| E8 | 29 (phase I) |
| F8 | Under investigation; preclinical CNS data favorable |
| G8 | Direct C797S + T790M coverage (cis configuration required) |

**Step 2.2 — The Cis/Trans Configuration Determination**

Before the clinical trial option (BLU-945) is actionable, you must determine whether the T790M and C797S mutations are on the same allele (cis) or opposite alleles (trans). This is the single most consequential analytical step in this exercise. If the mutations are in cis, a single fourth-generation agent targeting both simultaneously is rational. If they are in trans, then a combination of a first- or second-generation TKI (which inhibits the T790M-negative/C797S-positive allele) with osimertinib (which inhibits the T790M-positive allele) is theoretically required, though clinical data for this combination are limited and toxicity is significant.

The liquid biopsy report gave VAF data only. To determine cis/trans configuration, you require either (a) single-molecule sequencing of cfDNA using a platform that reports haplotype phasing (such as long-read sequencing), (b) tumor biopsy tissue subjected to single-cell sequencing or digital droplet PCR with allele-specific primers, or (c) validated computational phasing if the VAF ratio provides sufficient inference. The T790M VAF is 18% and the C797S VAF is 7%. A simple VAF ratio approach: if C797S VAF is roughly half or less of T790M VAF, it is consistent with C797S arising in a subclone of the T790M-positive population, suggesting cis. The 7%/18% = 0.39 ratio is consistent with cis configuration. Document this inference as provisional and flag for confirmatory allele-specific PCR on rebiopsy tissue.

In your spreadsheet, create a cell G10 labeled **Mutation Configuration** and enter **Likely cis (VAF ratio 0.39; confirmatory allele-specific PCR pending)**. This determination unlocks clinical trial eligibility.

**Step 2.3 — Carboplatin Dose Calculation Using the Calvert Formula**

For the chemotherapy arm, you must calculate the precise carboplatin dose. The Calvert formula is:

**Dose (mg) = Target AUC × (GFR + 25)**

Your patient's weight is 78 kg, age 66, and serum creatinine from the labs is 1.1 mg/dL. First calculate the estimated GFR using the CKD-EPI equation. The CKD-EPI equation for a male patient with creatinine ≤0.9 mg/dL uses one calculation branch; for creatinine >0.9 mg/dL (as here, 1.1 mg/dL), the formula is:

**eGFR = 141 × (Scr/0.9)^(−1.209) × 0.993^Age**

Working the calculation: (1.1/0.9) = 1.222; 1.222^(−1.209) = 1.222^(−1.209). Calculate this in your spreadsheet: enter in cell B12 the formula `=141*(1.1/0.9)^(-1.209)*(0.993^66)` and you will obtain approximately **69.5 mL/min/1.73m²**.

Now apply Calvert: Dose = 5 × (69.5 + 25) = 5 × 94.5 = **473 mg** carboplatin. Enter this in cell B13 with label A13 = "Carboplatin Dose (mg)".

For pemetrexed, calculate body surface area first using the Mosteller formula: BSA = √((height_cm × weight_kg) / 3600). The patient is 175 cm tall and 78 kg. BSA = √((175 × 78) / 3600) = √(13650/3600) = √3.792 = **1.947 m²**. Pemetrexed 500 mg/m² × 1.947 = **973.5 mg**, rounded to **974 mg**. Enter these in cells B14 and A14 respectively.

**Step 2.4 — Resistance Timeline Projection**

Create a new sheet tab labeled "Resistance Projection." Build the following Gompertzian tumor growth and therapeutic response model. This model is a simplified but quantitatively grounded tool used in translational pharmacology to reason about treatment sequencing.

The core assumption is that tumor cell populations under TKI selection follow a selective sweep dynamic: a drug-sensitive clone is suppressed while a pre-existing or newly acquired resistant subclone expands. Using the clinical data from MARIPOSA-2 (median PFS 6.3 months for amivantamab + lazertinib in this population) and the phase I BLU-945 data (ORR 29%, median duration of response approximately 7 months in responders at the 400 mg dose), you will project resistance timelines for each regimen.

In cells A1:F1 of the Resistance Projection tab, enter headers: **Regimen**, **Initial Response (% tumor reduction)**, **Median PFS (months)**, **Estimated Resistance Onset (months from start)**, **Likely Resistance Mechanism**, **Next-Line Option**.

Row 2 (Amivantamab + Lazertinib):

| A2 | Amivantamab+Lazertinib |
| B2 | 33% ORR; median −28% size reduction |
| C2 | 6.3 |
| D2 | 5–7 (coincides with PFS; resistance concurrent with progression) |
| E2 | MET amplification, KRAS amplification, epithelial-mesenchymal transition |
| F2 | Platinum doublet; tepotinib if MET amplification confirmed |

Row 3 (BLU-945 Trial):

| A3 | BLU-945 400mg BID |
| B3 | 29% ORR; median −22% size reduction (phase I estimate) |
| C3 | 7 (responders); 3 (non-responders) |
| D3 | 6–9 in responders |
| E3 | C797S secondary mutations in trans; MET amplification; KRAS G12C emergence |
| F3 | Platinum doublet; consider KRAS G12C inhibitor if that resistance emerges |

Row 4 (Chemotherapy):

| A4 | Carboplatin/Pemetrexed |
| B4 | 27% ORR; non-driver cytotoxic; less durable |
| C4 | 4.4 |
| D4 | 3–5 |
| E4 | Clonal expansion of residual TKI-resistant cells; thymidylate synthase upregulation |
| F4 | Docetaxel ± ramucirumab; re-challenge TKI if molecular evolution observed |

**Step 2.5 — CNS Disease Decision Adjudication**

The two brain metastases require independent management. Apply the NCCN CNS metastasis algorithm for NSCLC. For a patient with ≤3 brain metastases and all lesions ≤2 cm, stereotactic radiosurgery (SRS) without whole-brain radiation therapy (WBRT) is the preferred approach, preserving neurocognitive function. The two lesions (0.8 cm and 0.6 cm) meet SRS criteria. The systemic therapy chosen must have adequate CNS penetration to address potential micrometastatic CNS disease.

In your spreadsheet, create cell B16 labeled "CNS Management" and enter: **SRS to right frontal (0.8 cm) and left cerebellar (0.6 cm) lesions; systemic agent must demonstrate CNS activity. Lazertinib (in amivantamab+lazertinib regimen) has documented CNS penetration. BLU-945 CNS data under phase I investigation. Coordinate SRS timing with systemic therapy initiation: SRS first, begin systemic therapy 1–2 weeks post-SRS.**

**Step 2.6 — Treatment Recommendation Synthesis**

Your final analytical product for this exercise is a structured treatment decision document. In a third sheet tab labeled "Tx Decision," synthesize the following. Recommended first action: enrollment in BLU-945 or comparable fourth-generation EGFR TKI trial if cis mutation configuration is confirmed on allele-specific PCR of rebiopsy tissue, with SRS delivered to both CNS lesions in the interim. If trial is not accessible or cis configuration cannot be confirmed, amivantamab 1050 mg IV weekly × 4 then every 2 weeks + lazertinib 240 mg PO daily is the standard-of-care salvage regimen with the strongest current evidence for post-osimertinib resistance. Document carboplatin/pemetrexed as the second-line chemotherapy backbone for use upon progression from either targeted regimen. Record all dose calculations and decision criteria in the spreadsheet to simulate the tumor board case submission document.

---

## Exercise 3: Stress Testing, Boundary Failure & Recovery Protocol

### Managing Treatment Failure in a Metastatic Cascade: Acute Toxicity and Re-staging Protocol

The final exercise tests the most demanding clinical scenario: a patient whose treatment has produced a life-threatening toxicity event mid-course, whose disease has progressed on restaging, and whose performance status has deteriorated to a level that excludes aggressive cytotoxic therapy. The operative skill here is not adding new knowledge but applying a systematic audit rubric under pressure to recover a coherent, evidence-compliant plan from what appears to be a treatment dead end.

**The Failure Scenario Dataset**

A 58-year-old woman with stage IV NSCLC (KRAS G12C mutation, PD-L1 TPS 80%, STK11 wild-type, KEAP1 wild-type) initiated sotorasib 960 mg daily (CodeBreaK 100 first-line extension) in combination with pembrolizumab 200 mg IV every 3 weeks per investigational protocol. She presented to the emergency department on Day 44 of therapy with Grade 3 immune-mediated pneumonitis (CT showing bilateral ground-glass opacities, right > left, involving 25–50% of parenchyma) and an oxygen saturation of 88% on room air. She was admitted, both sotorasib and pembrolizumab were held, and high-dose corticosteroids were initiated (methylprednisolone 2 mg/kg/day IV). After 10 days of hospitalization, pneumonitis improved to Grade 1 on repeat imaging. She was discharged on a prednisone taper (60 mg → taper over 6 weeks). At the Week 8 restaging CT (performed during steroid taper, day 56 of steroid course), new hepatic lesions are identified: three lesions in segments IV, VI, and VII measuring 1.4 cm, 1.1 cm, and 0.9 cm, all new compared to baseline. The lung primary shows 15% increase in longest diameter (from 4.2 cm to 4.8 cm). Her ECOG performance status is now 2 (ambulatory, capable of self-care, up >50% of waking hours but unable to do any work).

**Step 3.1 — RECIST 1.1 Formal Progression Analysis**

Apply RECIST 1.1 criteria systematically. Per RECIST 1.1, target lesions are measured at baseline and at each restaging; the primary lung lesion was 4.2 cm (longest diameter, target lesion 1). The new hepatic lesions are non-target at baseline (they were absent at baseline) and are classified as new lesions at restaging, which constitutes progressive disease (PD) under RECIST 1.1 regardless of target lesion behavior.

In addition, the lung primary increased from 4.2 cm to 4.8 cm, an absolute increase of 6 mm and a relative increase of 14.3%. RECIST 1.1 defines Progressive Disease as ≥20% increase in sum of target lesion diameters (with ≥5 mm absolute increase). The 14.3% increase does not meet the 20% threshold for PD based on target lesion alone. However, the appearance of new lesions is independently sufficient for RECIST PD determination.

Enter this analysis into a spreadsheet column labeled "RECIST 1.1 Audit":

| Assessment Point | Lesion | Baseline Measurement | Current Measurement | % Change | RECIST Category |
|---|---|---|---|---|---|
| Week 8 | Lung primary (TL1) | 4.2 cm | 4.8 cm | +14.3% | Non-PD (target) |
| Week 8 | Hepatic segment IV (new) | Absent | 1.4 cm | New | PD (new lesion) |
| Week 8 | Hepatic segment VI (new) | Absent | 1.1 cm | New | PD (new lesion) |
| Week 8 | Hepatic segment VII (new) | Absent | 0.9 cm | New | PD (new lesion) |
| **Overall Response** | | | | | **Progressive Disease** |

**Step 3.2 — Toxicity Attribution and Re-challenge Safety Audit**

The primary audit question is whether sotorasib, pembrolizumab, or the combination caused the pneumonitis, because this determines which agents can be safely re-introduced.

Apply the CTCAE v5.0 and ESMO immunotherapy toxicity management guidelines to structure this determination. Immune-mediated pneumonitis (IMP) in the context of PD-1 inhibitor therapy follows a well-characterized pattern: typically onset between 2 and 24 weeks, bilateral ground-glass opacities, responsive to steroids. Sotorasib-associated pneumonitis has been reported but is far less common (approximately 2.7% any grade in CodeBreaK 100). The bilateral distribution, the temporal onset at Day 44 of combination therapy, and the steroid responsiveness are most consistent with PD-1 inhibitor-mediated IMP. However, combination attribution cannot be excluded.

Build the following re-challenge safety matrix in your spreadsheet:

| Agent | Causality Assessment | ESMO/NCCN Re-challenge Recommendation | Decision |
|---|---|---|---|
| Pembrolizumab | Probable (Grade 3 IMP, bilateral, steroid-responsive) | Grade 3 IMP: **permanent discontinuation** per ESMO IO toxicity guidelines | **PERMANENTLY DISCONTINUED** |
| Sotorasib | Possible contributory (less likely primary cause) | Grade 3 pulmonary event during combination: hold pending safety data; re-challenge acceptable if pneumonitis resolves to ≤Grade 1 and clear alternative attribution exists | **CONDITIONAL HOLD — requires MDT discussion before re-challenge** |

The critical finding is that pembrolizumab must be permanently discontinued. This eliminates checkpoint immunotherapy from the therapeutic arsenal entirely. For KRAS G12C NSCLC with PD-L1 80%, pembrolizumab monotherapy would have been a primary treatment option; its elimination substantially narrows the remaining pathway.

**Step 3.3 — ECOG PS 2 Treatment Eligibility Audit**

Performance status PS 2 marks a clinically meaningful boundary in oncology treatment guidelines. Most aggressive doublet cytotoxic regimens are studied in ECOG 0–1 populations. Examine the evidence for each remaining option against PS 2 eligibility.

Sotorasib 960 mg daily: CodeBreaK 100 and 200 included ECOG 0–1 predominantly, but sotorasib's oral, once-daily administration with manageable toxicity profile makes it feasible in PS 2 patients. The FDA label does not explicitly restrict to PS 0–1. NCCN notes PS 2 patients may receive targeted therapy for driver-positive disease. Sotorasib re-challenge is therefore **feasible if MDT approves and pneumonitis remains ≤Grade 1**.

Docetaxel 75 mg/m² every 3 weeks: FDA-approved second-line NSCLC. PS 2 is associated with significantly worse outcomes on chemotherapy, but docetaxel is used in PS 2 with dose modification. The ECOG 1594 trial demonstrated that PS 2 patients had substantially higher toxicity and lower benefit from platinum doublets, but single-agent docetaxel at reduced dose (60 mg/m²) is the standard compromise. This is a viable but suboptimal pathway.

Ramucirumab + docetaxel (REVEL data): median OS 10.5 months vs. docetaxel alone 9.1 months. The REVEL trial excluded PS 2. Ramucirumab is not standard of care for PS 2 patients in this scenario.

Adagrasib 600 mg BID: KRYSTAL-1 trial data for second-line KRAS G12C. The patient was on sotorasib first-line. Cross-resistance between sotorasib and adagrasib is partial but real. At progression on sotorasib, the dominant resistance mechanisms are KRAS amplification, secondary KRAS mutations (Y96D), and RAF/MEK pathway bypass. Adagrasib has a different binding profile from sotorasib (covalent, different switch-II pocket engagement kinetics) and has shown responses in sotorasib-pretreated patients in limited case series, though prospective data are sparse. Adagrasib is **potentially active, oral, PS 2-feasible, and represents the highest-priority option** pending resistance mechanism characterization from rebiopsy.

**Step 3.4 — Mandatory Rebiopsy Protocol**

Before initiating any further systemic therapy, molecular re-testing is non-negotiable. The hepatic metastases provide accessible biopsy targets. The rebiopsy protocol you must specify is as follows.

Target the largest accessible hepatic lesion (segment IV, 1.4 cm) under ultrasound or CT guidance. Request comprehensive NGS (≥400-gene panel) with specific attention to: KRAS amplification, secondary KRAS mutations (G12C → Y96D, Q61H, R68S), RAF1/BRAF amplification or mutation, MEK1/2 (MAP2K1/2) mutations, MET amplification, NRAS mutation, and STK11/KEAP1 mutation status (which affects IO and KRAS inhibitor response). Also request repeat PD-L1 TPS (heterogeneity can change PD-L1 score between primary and metastatic sites). Obtain a simultaneous liquid biopsy for cfDNA as a parallel track in case tissue biopsy is insufficient.

Additionally, a critical steroid interaction must be documented. The patient is on day 56 of a prednisone taper. Systemic corticosteroids at doses ≥10 mg prednisone equivalent suppress immune effector function and can directly impair the CD8+ T-cell killing mechanisms that underlie IO-based therapy. They also interact with cytochrome P450 enzymes involved in sotorasib metabolism (CYP3A4). For sotorasib re-challenge, the NCCN and sotorasib prescribing information recommend delaying initiation until corticosteroid dose is ≤10 mg prednisone equivalent per day.

In your spreadsheet, track the steroid taper schedule: beginning at 60 mg prednisone on day 1 of discharge, reducing by 10 mg every 7 days until 20 mg, then by 5 mg every 7 days. Build this in spreadsheet cells:

| Week | Day | Prednisone Dose (mg) |
|---|---|---|
| 1 | 1–7 | 60 |
| 2 | 8–14 | 50 |
| 3 | 15–21 | 40 |
| 4 | 22–28 | 30 |
| 5 | 29–35 | 20 |
| 6 | 36–42 | 15 |
| 7 | 43–49 | 10 |
| 8 | 50–56 | 5 |
| 9 | 57 | Discontinue |

Sotorasib or adagrasib re-initiation is cleared once the patient reaches ≤10 mg (Week 7, Day 43 of the taper). Record this as the **earliest permissible systemic therapy restart date**.

**Step 3.5 — Recovery Protocol: Reconstituted Treatment Plan**

The recovered treatment plan must address four simultaneous requirements: managing active hepatic metastatic disease, respecting the permanent pembrolizumab discontinuation, respecting the ≤10 mg steroid threshold before TKI re-initiation, and managing PS 2 performance status with an agent that does not impose prohibitive toxicity.

**Immediate actions (Days 1–42 of recovery period):** Complete the steroid taper as scheduled above. Obtain hepatic biopsy and comprehensive re-NGS. If the patient is symptomatic from hepatic disease (pain, transaminase elevation), consider single-fraction liver-directed stereotactic body radiation therapy (SBRT) to the dominant lesion (segment IV, 1.4 cm) as a bridge, as SBRT is feasible during a steroid taper and does not interact with the subsequent TKI resumption. SBRT to hepatic oligometastatic disease in NSCLC has been validated as a local control strategy (SINDAS trial, though that trial was for oligometastatic disease specifically).

**Re-initiation decision (Day 43+, prednisone ≤10 mg):** If rebiopsy NGS confirms no secondary KRAS mutation and no dominant bypass pathway, resume sotorasib 960 mg daily. If rebiopsy confirms adagrasib-sensitive resistance profile, switch to adagrasib 600 mg BID. If the resistance mechanism is a KRAS-bypass pathway (e.g., BRAF mutation), consult NCCN for applicable targeted combination. If no actionable resistance mechanism is identified and performance status permits, initiate single-agent docetaxel 60 mg/m² every 3 weeks with G-CSF support given PS 2.

**Monitoring cadence:** Conduct LFTs, CBC, and CMP weekly for the first 4 weeks of re-initiated therapy; repeat CT chest/abdomen/pelvis at 8 weeks from re-initiation (RECIST 1.1 restaging); repeat brain MRI at 12 weeks from re-initiation given prior CNS metastasis risk in KRAS G12C disease.

Document this complete recovery protocol in a final sheet tab labeled "Recovery Plan," with dates calculated relative to the actual hospital discharge date, and present it in the format of a tumor board case review summary including the RECIST audit, the toxicity attribution matrix, the re-challenge eligibility determination, the rebiopsy rationale, and the sequenced re-initiation schedule.

---

## Operational Reference Guide & Diagnostic Checklist

### Section 1: Oncological Staging Audit Rubric

Every new diagnosis and every restaging event must pass through a systematic verification sequence before a treatment decision is documented. The habit of treating staging as an auditable, checklist-verified act rather than a clinical impression is what separates rigorous oncology practice from pattern-matching. The following rubric applies to any solid tumor case and should be applied in full at diagnosis and at every restaging.

The staging audit begins with pathological confirmation: no treatment should be initiated on the basis of imaging alone unless tissue biopsy carries prohibitive risk. The pathology report must include histological type and grade (using the most current WHO classification for the tumor site), IHC panel results with positive and negative markers documented, and molecular/genomic testing results with variant classification (pathogenic, likely pathogenic, variant of uncertain significance, or benign). If NGS was performed, the report must specify the number of genes in the panel, the coverage depth, and the germline/somatic filtering methodology, because a somatic BRCA2 mutation carries different therapeutic and counseling implications than a germline BRCA2 mutation.

TNM staging must cite the edition of the AJCC manual used (8th edition is current as of publication). Each descriptor must be justified by the specific evidence used to assign it: imaging measurement with slice and series reference, PET SUVmax value and location for N staging, and biopsy or clinical exclusion rationale for M staging. Stage IIB assigned without noting which CT measured which lymph node is an audit failure.

Biomarker testing completeness must be verified against site-specific NCCN guidelines. For NSCLC at any stage, the minimum required biomarker panel per NCCN 2024 guidelines includes EGFR (exon 18, 19, 20, 21), ALK, ROS1, BRAF V600E, MET exon 14, RET, NTRK1/2/3, KRAS G12C, PD-L1 TPS, and TMB for advanced disease. Any missing test must be documented as pending with an expected result date, or as waived with clinical rationale.

### Section 2: Common Drug Dose Calculation Reference

| Drug | Formula | Reference Weight | Notes |
|---|---|---|---|
| Carboplatin | AUC × (GFR + 25) mg | Actual BW | Cap GFR at 125 mL/min to prevent overdose |
| Pemetrexed | 500 mg/m² × BSA | BSA (Mosteller) | Folate/B12 supplementation mandatory 7 days prior |
| Docetaxel | 75 mg/m² (PS 0–1); 60 mg/m² (PS 2) | BSA | G-CSF prophylaxis at 60 mg/m² in PS 2 |
| Osimertinib | 80 mg PO daily fixed dose | Fixed | Reduce to 40 mg if Grade 3 toxicity; CYP3A4 interactions |
| Sotorasib | 960 mg PO daily fixed dose | Fixed | Take with food; CYP3A4 inhibitor; hepatotoxicity monitoring |
| Adagrasib | 600 mg PO BID fixed dose | Fixed | QTc monitoring; drug interactions extensive |
| Amivantamab | 1050 mg IV (BW < 80 kg); 1400 mg (BW ≥80 kg) | Actual BW | Infusion reactions; premedicate with antihistamine + acetaminophen |
| Pembrolizumab | 200 mg IV q3w or 400 mg q6w flat dose | Fixed | Permanent discontinuation for Grade 3+ IMP |

### Section 3: RECIST 1.1 Quick Reference

Applying RECIST 1.1 correctly requires that you identify target lesions (maximum 5 total, maximum 2 per organ, measurable by CT ≥10 mm longest diameter or lymph nodes ≥15 mm short axis) and non-target lesions (all other lesions) at baseline, and track only target lesion diameter sums at subsequent time points. Complete Response (CR) is disappearance of all target lesions, with all pathological nodes reduced to < 10 mm short axis. Partial Response (PR) is ≥30% decrease in sum of target lesion diameters from baseline. Progressive Disease (PD) is ≥20% increase in sum from nadir (not baseline) with ≥5 mm absolute increase, or appearance of new lesions. Stable Disease (SD) is any result not meeting PR or PD criteria.

The most common RECIST errors in clinical practice are measuring a lymph node by longest diameter rather than short axis, calling a cyst or necrotic area a target lesion (target lesions must be measurable solid lesions), failing to document the nadir sum (using the wrong baseline for the 20% PD calculation), and failing to flag new lesions as PD when target lesion change alone does not meet PD criteria.

### Section 4: Diagnostic Failure Checklist

The following conditions represent the most common failure modes in the analytical exercises above and in clinical practice. Work through this list at the completion of any oncological assessment before presenting the case at tumor board.

Confirm that staging used the AJCC 8th Edition and that the edition is cited in the documentation. Confirm that all NCCN-mandated biomarkers for the tumor type have been tested or are explicitly pending. Confirm that liquid biopsy and tissue biopsy results are cross-referenced and discordant results (e.g., EGFR mutation present in ctDNA but absent in tissue) are flagged for repeat testing rather than adjudicated by clinical impression alone. Confirm that the drug dose calculations cite the specific formula used and the input values, not only the final dose. Confirm that RECIST measurements cite the CT series date, slice position, and measurement axis. Confirm that any Grade ≥3 toxicity attributed to IO therapy has been evaluated against ESMO re-challenge criteria, with permanent discontinuation clearly documented where indicated. Confirm that performance status was reassessed at the time of the restaging decision, not carried forward from the prior visit. Confirm that CNS imaging has been obtained or explicitly deferred with clinical rationale, as brain metastases change both staging and systemic therapy selection for NSCLC, breast cancer, melanoma, and renal cell carcinoma. Confirm that the tumor board discussion occurred or is scheduled before initiating any new line of therapy.

Each of these checkpoints maps directly to a decision point in the three exercises above. If any checkpoint fails during your exercise review, return to the relevant exercise section, identify where the failure occurred, and correct the documentation before proceeding. The purpose of this audit is not bureaucratic compliance; it is to ensure that every analytical decision in this guide reflects the standard of reasoning that a patient with cancer deserves.
