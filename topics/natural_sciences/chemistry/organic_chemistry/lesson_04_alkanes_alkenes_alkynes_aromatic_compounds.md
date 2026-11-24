# Lesson 4: Alkanes, Alkenes, Alkynes, and Aromatic Compounds

## 1. First-Principles Intuition & Invariants

### 1.1 Quantum Mechanical Foundation

The distinction between alkanes, alkenes, alkynes, and aromatic compounds emerges from the hybridization state of carbon atoms, which itself derives from quantum mechanical orbital mixing principles.

**Invariant 1: Orbital Energy Minimization**
Carbon's ground state electronic configuration (1s² 2s² 2p²) undergoes hybridization to minimize total system energy when forming bonds. The type of hybridization determines molecular geometry and reactivity:

- **sp³ hybridization** (alkanes): Four equivalent hybrid orbitals at 109.5° (tetrahedral)
- **sp² hybridization** (alkenes): Three coplanar hybrid orbitals at 120°, one unhybridized p orbital
- **sp hybridization** (alkynes): Two linear hybrid orbitals at 180°, two unhybridized p orbitals
- **sp² with cyclic conjugation** (aromatics): Delocalized π-electron system obeying Hückel's rule

**Invariant 2: Bonding Electron Density Distribution**

The σ/π bond distinction is fundamental:
- **σ bonds**: Cylindrically symmetric electron density along internuclear axis (all C-C and C-H bonds)
- **π bonds**: Electron density concentrated above and below the σ-bond plane (side-to-side p orbital overlap)

**Mathematical Invariant: Bond Strength and Length Correlation**

```text
Bond Type          Length (pm)      Strength (kJ/mol)      s-character
C-C (sp³-sp³)         154                348                   25%
C=C (sp²-sp²)         134                614                   33%
C≡C (sp-sp)           120                839                   50%
C(aromatic)           140                ~518                  33%
```

The relationship follows: **Higher s-character → Shorter bond → Greater strength**

This emerges because s orbitals have electron density closer to the nucleus than p orbitals, making sp hybrids with higher s-character more contracted and forming shorter, stronger bonds.

**Invariant 3: Thermodynamic Stability Hierarchy**

At constant carbon number:
- Alkanes (saturated) have lowest potential energy but lowest reactivity
- Alkenes (one π bond) have moderate potential energy and moderate reactivity
- Alkynes (two π bonds) have higher potential energy and higher reactivity
- Aromatics have exceptional thermodynamic stability despite unsaturation (resonance stabilization energy: ~150 kJ/mol for benzene)

### 1.2 Information-Theoretic Perspective

**Degree of Unsaturation (Index of Hydrogen Deficiency)**

$$\text{DoU} = \frac{2C + 2 + N - H - X}{2}$$

Where: C = carbons, N = nitrogens, H = hydrogens, X = halogens

This formula encodes the "missing" hydrogen pairs relative to the saturated alkane formula CₙH₂ₙ₊₂:
- Each ring: DoU = 1
- Each π bond: DoU = 1
- Benzene (C₆H₆): DoU = 4 (three π bonds + one ring equivalence)

**Physical Invariant: Electron Density and Reactivity**

π electrons exist in higher-energy orbitals with greater spatial extent than σ electrons, making them:
1. More polarizable (higher London dispersion forces)
2. More nucleophilic (react with electrophiles)
3. More susceptible to oxidation

### 1.3 Symmetry and Topology

**Alkanes**: Maximum rotational freedom around C-C bonds (conformational isomers)
**Alkenes**: Restricted rotation around C=C (geometric isomers: cis/trans, E/Z)
**Alkynes**: Linear geometry eliminates geometric isomerism for disubstituted alkynes
**Aromatics**: Planar geometry with cyclic electron delocalization (D₆ₕ symmetry for benzene)

## 2. Core Architecture & Mechanics

### 2.1 Alkanes: Saturated Hydrocarbons

**Structural Formula**: CₙH₂ₙ₊₂ (acyclic), CₙH₂ₙ (monocyclic)

**Hybridization Architecture**
Every carbon: sp³ hybridized (25% s-character, 75% p-character)
- Four σ bonds arranged tetrahedrally
- No π bonds present
- All bonds are single bonds

**Nomenclature Mechanics**

1. **Identify longest continuous carbon chain** (parent alkane)
2. **Number from end giving substituents lowest numbers**
3. **Name substituents alphabetically** with position numbers
4. **Use multiplying prefixes** (di-, tri-, tetra-) for identical substituents

```text
Example: 3-ethyl-2,4-dimethylhexane

        CH₃
         |
CH₃-CH-CH-CH₂-CH-CH₃
     |      |
    CH₃   CH₂CH₃

Parent: hexane (6 carbons)
Substituents: 2-methyl, 3-ethyl, 4-methyl
```

**Physical Properties Architecture**

Boiling point trend: **Intermolecular forces dominate**

- **Linear alkanes**: BP increases with molecular weight (greater surface area → stronger London dispersion)
- **Branched alkanes**: BP decreases with branching at same MW (reduced surface contact)

```text
n-pentane:     36°C
isopentane:    28°C
neopentane:     9°C
```

**Conformational Analysis**

Energy barrier for C-C rotation: ~12-15 kJ/mol

**Newman Projection Mechanics for Ethane:**

```text
    H           H
    |           |
H - C - H   H - C - H
    |           |
    H           H

Staggered       Eclipsed
(0 kJ/mol)     (+12 kJ/mol)
```

**Butane rotational potential** (about C2-C3):

- **Anti** (180°): 0 kJ/mol (most stable)
- **Gauche** (±60°): +3.8 kJ/mol (steric strain)
- **Eclipsed** (0°, 120°, 240°): +16-19 kJ/mol (torsional + steric strain)

**Cycloalkane Strain Architecture**

Total strain = **Angle strain** + **Torsional strain** + **Steric strain**

```text
Ring Size    Strain Energy (kJ/mol)    Primary Source
Cyclopropane      115                  Angle strain (60° vs 109.5°)
Cyclobutane        110                  Angle + torsional strain
Cyclopentane       26                   Torsional strain
Cyclohexane         0                   Strain-free in chair form
```

**Cyclohexane Chair Conformation Mechanics**

Two distinct positions:
- **Axial**: Parallel to C₃ rotation axis (6 positions)
- **Equatorial**: Roughly in ring plane (6 positions)

Ring flip interconverts: axial ↔ equatorial (ΔG‡ ≈ 45 kJ/mol at 25°C)

**Substituent preference**: Equatorial position favored by:
- CH₃: 7.6 kJ/mol
- C(CH₃)₃: 23 kJ/mol (severe 1,3-diaxial interactions)

**Reactivity Profile**

Alkanes are chemically inert except for:

1. **Combustion** (complete oxidation):
   $$\text{C}_n\text{H}_{2n+2} + \frac{3n+1}{2}\text{O}_2 \rightarrow n\text{CO}_2 + (n+1)\text{H}_2\text{O}$$

2. **Halogenation** (free radical substitution):
   Mechanism: Initiation → Propagation → Termination

**Propagation steps:**
```text
Cl• + CH₃-H → HCl + •CH₃        (ΔH ≈ +4 kJ/mol, slow)
•CH₃ + Cl₂ → CH₃Cl + Cl•        (ΔH ≈ -100 kJ/mol, fast)
```

**Reactivity order (H abstraction):**
3° > 2° > 1° > CH₃ (stability of radical intermediate)

### 2.2 Alkenes: Olefins

**Structural Formula**: CₙH₂ₙ (acyclic, one C=C), general formula for k double bonds: CₙH₂ₙ₋₂ₖ

**Hybridization Architecture**

sp² carbons at C=C:
- Three σ bonds (sp² hybrids) at 120°
- One π bond (p-p lateral overlap perpendicular to molecular plane)
- Planar geometry at double bond

**π Bond Mechanics**

- **Barrier to rotation**: ~264 kJ/mol (must break π bond)
- **Electron density**: Maximum above and below σ-bond plane
- **HOMO-LUMO**: π (HOMO) and π* (LUMO) are frontier orbitals

**Geometric Isomerism**

**Cahn-Ingold-Prelog Priority Rules:**
1. Higher atomic number has priority
2. If tie, examine next atoms outward
3. Double bonds count as two single bonds to that atom

**E/Z notation:**
- **(E)**: *Entgegen* (opposite) - high priority groups on opposite sides
- **(Z)**: *Zusammen* (together) - high priority groups on same side

```text
       H         CH₃              CH₃        H
        \       /                  \       /
         C = C                      C = C
        /       \                  /       \
      CH₃        H                H         CH₃

     (Z)-2-butene              (E)-2-butene
```

**Nomenclature Mechanics**

1. Longest chain containing C=C
2. Number to give C=C lowest number
3. Suffix: -ene
4. Indicate C=C position before suffix

Example: **4-methylpent-2-ene**

**Stability Hierarchy**

Alkene stability increases with substitution (Zaitsev's rule):

$$R_2C=CR_2 > R_2C=CHR > R_2C=CH_2 > RCH=CHR > RCH=CH_2 > CH_2=CH_2$$

**Hyperconjugation model**: σ electrons from C-H bonds adjacent to C=C donate into π* orbital, stabilizing the alkene.

**Thermodynamic data** (ΔH° for hydrogenation to alkane):
- Ethene: -136 kJ/mol
- Propene: -126 kJ/mol
- But-2-ene: -115 kJ/mol (trans), -120 kJ/mol (cis)

**Reactivity Profile: Electrophilic Addition**

**Fundamental Mechanism Architecture:**

```text
Step 1: π electrons attack electrophile → carbocation intermediate
Step 2: Nucleophile attacks carbocation → product
```

**Markovnikov's Rule** (regioselectivity):
"Hydrogen adds to the carbon with more hydrogens"

**Mechanistic basis**: Reaction proceeds through more stable carbocation (3° > 2° > 1°)

**Key Reactions:**

1. **Hydrohalogenation** (HX)
   ```text
   RCH=CH₂ + HBr → RCH(Br)-CH₃  (Markovnikov)
   ```
   With peroxides (anti-Markovnikov via radical mechanism)

2. **Hydration** (H₂O/H⁺)
   ```text
   RCH=CH₂ + H₂O/H⁺ → RCH(OH)-CH₃  (Markovnikov)
   ```

3. **Halogenation** (X₂)
   ```text
   RCH=CHR + Br₂ → RCH(Br)-CHR(Br)  (anti addition)
   ```
   Mechanism: Cyclic bromonium ion intermediate → backside attack

4. **Hydrogenation** (H₂/catalyst)
   ```text
   RCH=CHR + H₂/Pt → RCH₂-CH₂R  (syn addition)
   ```
   Heterogeneous catalysis on metal surface

5. **Oxidation**
   - **Epoxidation** (RCO₃H): syn addition of oxygen across C=C
   - **Dihydroxylation** (OsO₄ or KMnO₄): syn addition of two OH groups
   - **Ozonolysis** (O₃, then workup): cleaves C=C to form carbonyl compounds

### 2.3 Alkynes: Acetylenes

**Structural Formula**: CₙH₂ₙ₋₂ (one C≡C)

**Hybridization Architecture**

sp carbons at C≡C:
- Two σ bonds (sp hybrids) at 180° (linear)
- Two π bonds (two perpendicular p-p overlaps)
- Cylindrical π electron density around molecular axis

**Bond Mechanics**

C≡C bond components:
- One σ bond (sp-sp overlap)
- Two π bonds (pₓ-pₓ and pᵧ-pᵧ overlaps)
- Total bond order: 3
- 50% s-character in sp hybrids

**Consequence of high s-character:**
- **C≡C-H bond**: More acidic (pKₐ ≈ 25) than sp² C-H (pKₐ ≈ 44) or sp³ C-H (pKₐ ≈ 50)
- **Electronegativity**: sp carbon (50% s) > sp² (33% s) > sp³ (25% s)

**Nomenclature**: Suffix -yne, number position of triple bond

Example: **hex-3-yne** (CH₃CH₂C≡CCH₂CH₃)

**Acidity and Nucleophilicity**

Terminal alkynes (RC≡CH) are weak acids:

```text
RC≡CH + NaNH₂ → RC≡C⁻Na⁺ + NH₃
```

Alkynide anion (RC≡C⁻) is a strong nucleophile and base, used in:
- **Nucleophilic substitution**: RC≡C⁻ + R'X → RC≡CR' + X⁻
- **Carbon chain extension**

**Reactivity Profile**

Similar to alkenes but generally less reactive (π electrons held more tightly due to higher s-character).

**Key Reactions:**

1. **Hydrogenation**
   - **Complete** (H₂/Pt, 2 equiv): alkyne → alkane
   - **Partial** (H₂/Lindlar catalyst, 1 equiv): alkyne → cis-alkene
   - **Dissolving metal** (Na/NH₃): alkyne → trans-alkene

2. **Hydrohalogenation** (2 equiv HX)
   ```text
   RC≡CH + 2HBr → RCBr₂CH₃  (Markovnikov)
   ```

3. **Hydration** (H₂O/H⁺/HgSO₄)
   ```text
   RC≡CH + H₂O/H⁺/HgSO₄ → RCOCH₃ (via enol tautomerization to methyl ketone)
   ```

4. **Halogenation** (2 equiv X₂)
   ```text
   RC≡CR + 2Br₂ → RCBr₂-CBr₂R
   ```

### 2.4 Aromatic Compounds

**Fundamental Criterion: Hückel's Rule**

A planar, cyclic, fully conjugated system is aromatic if it contains **(4n + 2) π electrons** where n = 0, 1, 2, 3...

- n = 1: **6 π electrons** (benzene, pyridine, pyrrole)
- n = 2: **10 π electrons** (naphthalene, azulene)

**Antiaromatic systems** (4n π electrons): Highly unstable, avoid planar conjugation
**Non-aromatic systems**: Not fully conjugated or not planar

**Benzene Architecture**

**Molecular Formula**: C₆H₆
**Structure**: Planar hexagon, all C-C bonds equivalent (140 pm)
**Hybridization**: All carbons sp² with p orbitals perpendicular to ring plane

**Molecular Orbital Description:**

Six p orbitals combine to form six π molecular orbitals:
- 1 bonding (lowest energy, Ψ₁)
- 2 bonding (degenerate pair, Ψ₂, Ψ₃)
- 2 antibonding (degenerate pair, Ψ₄*, Ψ₅*)
- 1 antibonding (highest energy, Ψ₆*)

Six π electrons fill three bonding MOs → exceptional stability

**Resonance Stabilization Energy**: ~150 kJ/mol

Determined by comparing:
- Experimental heat of hydrogenation of benzene: -208 kJ/mol
- Predicted (3 × cyclohexene): -360 kJ/mol
- Difference: ~150 kJ/mol (stabilization)

**Nomenclature Mechanics**

**Monosubstituted**: Name as benzene derivative
- Methylbenzene (toluene)
- Hydroxybenzene (phenol)
- Aminobenzene (aniline)

**Disubstituted**: Use ortho/meta/para or 1,2-/1,3-/1,4- numbering

```text
        2 (ortho)
       /
   1--6
      |
   5--4
       \
        3 (meta)
        
        4 (para)
```

**Polysubstituted**: Number to give lowest numbers, name substituents alphabetically

**Reactivity Profile: Electrophilic Aromatic Substitution (EAS)**

**Fundamental Principle**: Benzene undergoes substitution (not addition) to preserve aromaticity

**General Mechanism Architecture:**

```text
Step 1: Electrophile generation (E⁺)
Step 2: π system attacks E⁺ → σ complex (arenium ion, cyclohexadienyl cation)
Step 3: Base removes H⁺ → aromaticity restored
```

**σ Complex Structure:**
- sp³ carbon at substitution site
- Four sp² carbons
- Non-aromatic (loss of resonance stabilization)
- Rate-determining step for most EAS reactions

**Key EAS Reactions:**

1. **Halogenation** (X₂/FeX₃)
   ```text
   C₆H₆ + Br₂/FeBr₃ → C₆H₅Br + HBr
   Electrophile: Br⁺ (from Br₂ + FeBr₃ → Br⁺ + FeBr₄⁻)
   ```

2. **Nitration** (HNO₃/H₂SO₄)
   ```text
   C₆H₆ + HNO₃/H₂SO₄ → C₆H₅NO₂ + H₂O
   Electrophile: NO₂⁺ (nitronium ion)
   ```

3. **Sulfonation** (H₂SO₄/SO₃)
   ```text
   C₆H₆ + H₂SO₄/SO₃ → C₆H₅SO₃H
   Electrophile: SO₃ (or HSO₃⁺)
   ```

4. **Friedel-Crafts Alkylation** (RX/AlCl₃)
   ```text
   C₆H₆ + CH₃Cl/AlCl₃ → C₆H₅CH₃ + HCl
   Electrophile: R⁺ (carbocation)
   Limitations: Carbocation rearrangement, over-alkylation
   ```

5. **Friedel-Crafts Acylation** (RCOCl/AlCl₃)
   ```text
   C₆H₆ + CH₃COCl/AlCl₃ → C₆H₅COCH₃ + HCl
   Electrophile: RCO⁺ (acylium ion)
   No rearrangement, no over-acylation
   ```

**Substituent Effects on EAS**

**Electronic effects govern reactivity and orientation:**

**Activating Groups** (increase reactivity, ortho/para directors):
- **Electron-donating**: -OH, -OR, -NH₂, -NHR, -NR₂ (resonance donors)
- **Alkyl groups**: -CH₃, -CH₂CH₃ (inductive donors, hyperconjugation)

**Mechanism**: Stabilize σ complex through electron donation

**Deactivating Groups** (decrease reactivity):
- **meta directors**: -NO₂, -CN, -COOH, -CHO, -COR (electron-withdrawing by resonance and induction)
- **ortho/para directors**: -F, -Cl, -Br, -I (electron-withdrawing by induction, but lone-pair resonance donation)

**Quantitative Reactivity:**

Relative rates for nitration at 25°C (benzene = 1):
- Toluene (CH₃): 25
- Phenol (OH): 1000
- Nitrobenzene (NO₂): 0.0000067
- Benzaldehyde (CHO): 0.0001

**Polycyclic Aromatic Hydrocarbons (PAHs)**

**Naphthalene** (C₁₀H₈): Two fused benzene rings, 10 π electrons
- Resonance energy: ~250 kJ/mol (not 2 × benzene)
- Reactivity: α position (1,4,5,8) > β position (2,3,6,7)

**Anthracene** (C₁₄H₁₀): Three linearly fused rings, 14 π electrons
**Phenanthrene** (C₁₄H₁₀): Three angularly fused rings (isomer of anthracene)

**Heterocyclic Aromatics**

**Pyridine** (C₅H₅N): 6 π electrons, nitrogen sp² lone pair not part of π system
- Less reactive than benzene in EAS (nitrogen withdraws electrons)
- Basic (pKₐ of conjugate acid: 5.2)

**Pyrrole** (C₄H₅N): 6 π electrons, nitrogen p lone pair contributes to π system
- More reactive than benzene in EAS
- Weakly basic (protonation destroys aromaticity)

**Furan** (C₄H₄O): 6 π electrons, oxygen p lone pair contributes
**Thiophene** (C₄H₄S): 6 π electrons, sulfur p lone pair contributes

## 3. High-Performance Implementation & Failure Modes

### 3.1 Strategic Synthesis Design

**Retrosynthetic Analysis Framework**

**For Alkanes:**
1. **Hydrogenation of alkenes/alkynes** (reduces unsaturation)
2. **Wurtz coupling** (2 RX + 2 Na → R-R + 2 NaX) - limited utility due to side reactions
3. **Corey-House synthesis** (R₂CuLi + R'X → R-R') - controlled coupling

**For Alkenes:**
1. **Elimination reactions** (E2, E1 from alkyl halides or alcohols)
   - E2: Antiperiplanar geometry required (H and leaving group must be 180°)
   - Zaitsev rule: More substituted alkene predominates (thermodynamic product)
   - Hofmann rule: Less substituted alkene with bulky base (kinetic product)

2. **Wittig reaction** (Ph₃P=CR₂ + R'₂C=O → R₂C=CR'₂ + Ph₃P=O)
   - Advantage: Precise C=C placement, no rearrangement
   - Stereochemistry: Z-selective with unstabilized ylides

3. **Partial reduction of alkynes**
   - Lindlar catalyst: H₂/Pd-CaCO₃/Pb(OAc)₂ → cis-alkene
   - Dissolving metal: Na/NH₃(l) → trans-alkene

**For Alkynes:**
1. **Double elimination** from dihaloalkanes (vicinal or geminal)
2. **Alkynide alkylation** (RC≡C⁻ + R'X → RC≡CR')

**For Aromatics:**
1. **Cyclotrimerization** of alkynes (limited)
2. **Aromatic ring construction** (Diels-Alder followed by dehydrogenation)
3. **EAS sequence** - order matters critically

### 3.2 Critical Failure Modes

**Failure Mode 1: Carbocation Rearrangement**

**Problem**: Carbocations rearrange via 1,2-hydride or 1,2-alkyl shifts to more stable carbocations

```text
Example: Addition of HCl to 3-methylbut-1-ene

Expected: CH₃-CH(CH₃)-CH₂-CH₂Cl
Observed: CH₃-CH(CH₃)-CHCl-CH₃ (major)

Mechanism:
1. H⁺ adds to C1 → secondary carbocation at C2
2. Hydride shift → tertiary carbocation at C3
3. Cl⁻ attacks → rearranged product
```

**Mitigation**: 
- Use reactions that don't involve carbocations (anti-Markovnikov hydroboration-oxidation)
- Recognize when rearrangement is thermodynamically favorable

**Failure Mode 2: E2 Stereoelectronic Requirement Violation**

**Problem**: E2 elimination requires antiperiplanar geometry (H and leaving group at 180°)

```text
cis-1-bromo-2-methylcyclohexane with conformational constraint:

If Br is equatorial → No adjacent H is antiperiplanar → No elimination or very slow
Must have Br axial for E2 to proceed efficiently
```

**Mitigation**:
- Draw chair conformations
- Verify antiperiplanar relationship
- Consider conformational flipping barriers

**Failure Mode 3: Over-alkylation in Friedel-Crafts**

**Problem**: Alkyl groups are activating → product is more reactive than starting material

```text
C₆H₆ + CH₃Cl/AlCl₃ → C₆H₅CH₃ → C₆H₄(CH₃)₂ → C₆H₃(CH₃)₃...
```

**Mitigation**:
- Use large excess of benzene
- Switch to Friedel-Crafts acylation (acyl groups are deactivating) followed by reduction

**Failure Mode 4: Friedel-Crafts Incompatibility**

**Problem**: F-C reactions fail with strongly deactivated rings or basic substituents

```text
Nitrobenzene + RX/AlCl₃ → NO REACTION (too deactivated)
Aniline + RX/AlCl₃ → NO REACTION (NH₂ binds AlCl₃, deactivating)
```

**Mitigation**:
- Introduce activating groups first, then F-C, then convert to deactivating
- Protect basic groups (e.g., acetylate aniline before F-C)

**Failure Mode 5: Aromatic Substitution Pattern Error**

**Problem**: Multiple substituents with conflicting directing effects

```text
p-nitrotoluene nitration:

-CH₃ (ortho/para director, activating) at position 1
-NO₂ (meta director, deactivating) at position 4

Question: Where does second NO₂ add?

Answer: Position 2 (ortho to CH₃)
Reason: CH₃ activates ring; NO₂ deactivates → reaction occurs in activated region
```

**Decision rule**: Activating group dominates orientation when opposing deactivating group

**Failure Mode 6: Syn vs Anti Addition Confusion**

**Problem**: Stereochemical outcome depends on mechanism

```text
Br₂ addition to alkene: Anti addition (via bromonium ion)
OsO₄ dihydroxylation: Syn addition (via cyclic osmate ester)
Hydrogenation (H₂/Pt): Syn addition (surface catalysis)
```

**Mitigation**: Memorize mechanism → deduce stereochemistry

**Failure Mode 7: Ignoring Aromatic Resonance Stabilization**

**Problem**: Assuming aromatic compounds react like alkenes

```text
Attempted: C₆H₆ + Br₂ → C₆H₆Br₂ (addition)
Actual: C₆H₆ + Br₂/FeBr₃ → C₆H₅Br + HBr (substitution)

Reason: Addition would destroy aromaticity (~150 kJ/mol penalty)
```

**Recognition**: Aromatic systems resist reactions that destroy conjugation

### 3.3 Advanced Problem-Solving Protocols

**Protocol 1: Structure Elucidation from Molecular Formula**

Given: C₅H₈

```text
Step 1: Calculate DoU
DoU = (2×5 + 2 - 8)/2 = 2

Step 2: Enumerate possibilities
- Two rings
- One ring + one π bond
- Two π bonds (alkene + alkene, or one alkyne)
- One ring + one π bond

Step 3: Use spectroscopic data to differentiate
- IR: Alkyne C≡C stretch (2100-2200 cm⁻¹), alkene C=C (1620-1680 cm⁻¹)
- ¹H NMR: Alkyne H (δ 1.7-3.1), vinyl H (δ 4.5-6.5)
- ¹³C NMR: sp carbon (δ 65-85), sp² carbon (δ 100-150)
```

**Protocol 2: Multistep Synthesis Planning**

**Problem**: Synthesize p-chlorotoluene from benzene

**Incorrect approach**:
1. Chlorinate → chlorobenzene
2. Alkylate → mixture of o- and p-chlorotoluene

**Correct approach**:
1. Alkylate benzene (CH₃Cl/AlCl₃) → toluene
2. Chlorinate toluene (Cl₂/FeCl₃) → o- and p-chlorotoluene (separable, p- predominates)

**Rationale**: -CH₃ is ortho/para director → better selectivity

**Protocol 3: Predicting Major Product with Competing Pathways**

**Problem**: Heat 2-bromo-2-methylbutane with NaOCH₂CH₃/ethanol

```text
Competing reactions:
- E2 elimination (strong base, high T)
- SN2 (tertiary substrate → very slow)
- SN1 (polar protic solvent favors)

Prediction:
Primary pathway: E2 (strong base, sterically hindered substrate)
Products by Zaitsev: 2-methylbut-2-ene (trisubstituted) > 2-methylbut-1-ene (disubstituted)

Major product: 2-methylbut-2-ene
```

**Protocol 4: Aromatic Synthesis with Multiple Substituents**

**Problem**: Synthesize m-bromonitrobenzene from benzene

**Analysis**:
- Both Br and NO₂ are deactivating
- Br is o/p director; NO₂ is m director
- Want meta relationship

**Strategy**:
1. Introduce meta-director first: C₆H₆ + HNO₃/H₂SO₄ → C₆H₅NO₂
2. Brominate: C₆H₅NO₂ + Br₂/FeBr₃ → m-BrC₆H₄NO₂

**Alternative (incorrect)**:
1. C₆H₆ + Br₂/FeBr₃ → C₆H₅Br
2. C₆H₅Br + HNO₃/H₂SO₄ → o- and p-BrC₆H₄NO₂ (wrong isomers)

### 3.4 Optimization Strategies

**Strategy 1: Regioselective Alkene Hydration**

**Markovnikov (H₂O/H⁺)**:
- Mechanism: Carbocation intermediate
- Product: More substituted alcohol
- Issues: Rearrangement possible

**Anti-Markovnikov (Hydroboration-oxidation)**:
- Mechanism: Concerted syn addition of BH₃, then oxidation
- Product: Less substituted alcohol
- Advantages: No rearrangement, syn stereochemistry

```text
Example: Methylcyclohexene

Markovnikov → 1-methylcyclohexanol (3°)
Anti-Markovnikov → trans-2-methylcyclohexan-1-ol (2°)
```

**Strategy 2: Chemoselective Reduction**

**Problem**: Reduce alkyne to alkene without over-reduction to alkane

**Solutions**:
- **Lindlar catalyst**: H₂/Pd-CaCO₃/Pb(OAc)₂ → Stops at cis-alkene (catalyst poisoned)
- **Dissolving metal**: Li or Na/NH₃(l) → trans-alkene via radical anion intermediate

**Strategy 3: Protecting Group Tactics in Aromatic Synthesis**

**Problem**: Synthesize p-nitroaniline from benzene

**Direct approach fails**:
- Nitrate first → nitrobenzene (deactivated, meta-director)
- Reduce NO₂ → aniline
- Nitrate again → m-nitroaniline (wrong isomer) + reaction very slow

**Successful strategy**:
1. Nitrate: C₆H₆ → C₆H₅NO₂
2. Reduce: C₆H₅NO₂ → C₆H₅NH₂
3. **Protect**: C₆H₅NH₂ + (CH₃CO)₂O → C₆H₅NHCOCH₃ (amide is less activating, o/p director)
4. Nitrate: C₆H₅NHCOCH₃ → p-O₂NC₆H₄NHCOCH₃
5. **Deprotect**: p-O₂NC₆H₄NHCOCH₃ + H₂O/H⁺ → p-O₂NC₆H₄NH₂

**Strategy 4: Exploiting Directing Effects Sequence**

**Problem**: Synthesize p-chlorobenzenesulfonic acid from benzene

**Analysis**:
- SO₃H is meta director (deactivating)
- Cl is ortho/para director (deactivating)
- Want para relationship

**Correct sequence**:
1. Chlorinate first
2. Sulfonate (will go ortho/para to Cl, para predominates)

**Incorrect sequence**:
1. Sulfonate first
2. Chlorinate (will go meta to SO₃H → wrong isomer)

### 3.5 Analytical Problem Recognition Patterns

**Pattern 1: Molecular formula indicates degree of unsaturation**

CₙHₓ compared to CₙH₂ₙ₊₂:
- Every 2 H deficiency = 1 DoU (ring or π bond)
- Aromatic ring (benzene) = 4 DoU (3 π bonds + ring equivalence)

**Pattern 2: Reactivity prediction from structure**

```text
Alkane < Alkyne < Aromatic < Alkene
(increasing reactivity toward electrophiles)

Exception: Aromatic undergoes substitution preferentially
```

**Pattern 3: Product distribution from thermodynamic vs kinetic control**

**Thermodynamic (reversible, high T, long time)**:
- Most stable product dominates
- Zaitsev elimination (more substituted alkene)
- Trans > cis alkene

**Kinetic (irreversible, low T, short time)**:
- Fastest-forming product dominates
- Hofmann elimination with bulky base (less substituted)
- May trap less stable intermediate

**Pattern 4: Stereochemical outcomes encode mechanism**

- **Racemization** → Carbocation intermediate (planar, achiral)
- **Inversion** → SN2 mechanism (backside attack)
- **Retention** → Double inversion or frontside (rare)
- **Anti addition** → Cyclic intermediate (bromonium, mercurinium)
- **Syn addition** → Concerted mechanism (hydrogenation, hydroboration)

## 4. Summary & Verification Matrix

### 4.1 Conceptual Hierarchy Map

```text
Hydrocarbons
│
├── Saturated (Alkanes)
│   ├── Acyclic: CₙH₂ₙ₊₂
│   ├── Cyclic: CₙH₂ₙ
│   └── Reactivity: Radical substitution, combustion
│
├── Unsaturated
│   │
│   ├── Alkenes (C=C)
│   │   ├── Formula: CₙH₂ₙ
│   │   ├── Geometry: sp², trigonal planar
│   │   ├── Isomerism: E/Z geometric isomers
│   │   └── Reactivity: Electrophilic addition
│   │
│   ├── Alkynes (C≡C)
│   │   ├── Formula: CₙH₂ₙ₋₂
│   │   ├── Geometry: sp, linear
│   │   ├── Acidity: Terminal H (pKₐ ~25)
│   │   └── Reactivity: Electrophilic addition, nucleophilic substitution (via anion)
│   │
│   └── Aromatics (conjugated rings)
│       ├── Criterion: (4n+2) π electrons, planar, cyclic
│       ├── Prototype: Benzene (C₆H₆)
│       ├── Stability: Resonance energy ~150 kJ/mol
│       └── Reactivity: Electrophilic aromatic substitution
│
```

### 4.2 Quantitative Reference Table

| Property | Alkane | Alkene | Alkyne | Aromatic |
|----------|--------|--------|--------|----------|
| **Hybridization** | sp³ | sp² at C=C | sp at C≡C | sp² |
| **Bond angles** | 109.5° | 120° | 180° | 120° |
| **s-character** | 25% | 33% | 50% | 33% |
| **C-C bond length** | 154 pm | 134 pm | 120 pm | 140 pm |
| **C-C bond energy** | 348 kJ/mol | 614 kJ/mol | 839 kJ/mol | ~518 kJ/mol |
| **C-H acidity (pKₐ)** | ~50 | ~44 | ~25 | ~43 |
| **Primary reactivity** | Radical subst. | Electrophilic add. | Electrophilic add. | Electrophilic subst. |
| **Rotation barrier** | ~12 kJ/mol | ~264 kJ/mol | 0 (cylindrical) | N/A (planar) |

### 4.3 Reaction Summary Matrix

| Reaction Type | Alkane | Alkene | Alkyne | Aromatic |
|---------------|--------|--------|--------|----------|
| **Combustion** | Complete oxidation | Complete oxidation | Complete oxidation | Sooty flame |
| **Halogenation** | Radical (hv/Δ) | Electrophilic addition (anti) | Electrophilic addition (2 eq) | EAS (catalyst required) |
| **Hydrogenation** | N/A | H₂/cat → alkane | H₂/cat → alkene/alkane | High P,T → cyclohexane |
| **Hydration** | N/A | H₂O/H⁺ → alcohol (Markovnikov) | H₂O/H⁺/Hg²⁺ → ketone | N/A |
| **Dehydration** | N/A | Reverse of hydration | N/A | N/A |
| **With HX** | Radical substitution | Addition (Markovnikov/anti-M) | Addition (2 eq) | N/A directly |
| **Oxidation** | Difficult (combustion) | Epoxidation, dihydroxylation, ozonolysis | Ozonolysis | Side-chain oxidation |
| **Acidity** | Non-acidic | Weakly acidic (allylic H) | Terminal H acidic (pKₐ 25) | Phenol acidic (pKₐ 10) |

### 4.4 Critical Decision Trees

**Decision Tree 1: Predicting Major Product**

```text
Is carbocation involved?
├── Yes: Check for rearrangement possibility
│   ├── Can form more stable carbocation? → Rearrangement occurs
│   └── No more stable option → No rearrangement
└── No: Consider sterics and electronics
    ├── Steric hindrance → Hofmann orientation
    └── No major steric issue → Zaitsev orientation
```

**Decision Tree 2: Aromatic Substitution Pattern**

```text
Identify all substituents
│
For each EAS reaction:
├── Is ring activated or deactivated?
│   ├── Activated: Reaction proceeds faster than benzene
│   └── Deactivated: Reaction proceeds slower (may require harsh conditions)
│
└── Where does substitution occur?
    ├── Activating groups present?
    │   └── Yes: Follow strongest activator (typically o/p director)
    └── Only deactivating groups?
        └── Follow meta directors if no ortho/para deactivating groups dominate
```

**Decision Tree 3: Synthesis Strategy Selection**

```text
Target molecule analysis:
│
├── Contains aromatic ring?
│   ├── Yes: Plan EAS sequence (order by activating/deactivating effects)
│   └── No: Proceed to aliphatic analysis
│
├── Degree of unsaturation?
│   ├── 0: Alkane synthesis (hydrogenation, coupling)
│   ├── 1: Alkene synthesis (elimination, Wittig, partial reduction)
│   └── 2+: Alkyne synthesis (double elimination, alkynide alkylation)
│
└── Stereochemistry required?
    ├── E/Z specific: Choose syn vs anti addition carefully
    └── Racemic acceptable: Standard protocols apply
```

### 4.5 Self-Assessment Checkpoints

**Checkpoint 1: Nomenclature Competency**

Can you name these structures correctly using IUPAC rules?
- Branched alkanes with multiple substituents
- E/Z alkenes with priority assignment
- Polysubstituted aromatics (ortho/meta/para or numbered)

**Checkpoint 2: Mechanism Fluency**

Can you draw complete electron-pushing mechanisms for:
- Free radical halogenation (initiation, propagation, termination)
- Electrophilic addition to alkenes (carbocation formation, nucleophile attack)
- Electrophilic aromatic substitution (σ-complex formation, deprotonation)

**Checkpoint 3: Stereochemical Reasoning**

Can you predict:
- E/Z configuration from structure
- Syn vs anti addition outcome from mechanism
- Conformational preferences in cyclohexanes (axial/equatorial)

**Checkpoint 4: Synthesis Planning**

Can you design multistep syntheses that:
- Install substituents in correct order for aromatic synthesis
- Avoid carbocation rearrangements
- Control regioselectivity (Markovnikov vs anti-Markovnikov)
- Achieve desired stereochemistry

**Checkpoint 5: Reactivity Prediction**

Can you rank reactivity orders for:
- Carbocation stability (3° > 2° > 1° > methyl)
- Alkene stability (more substituted > less substituted)
- Aromatic ring activation (-OH > -CH₃ > -H > -Cl > -NO₂)
- Leaving group ability (I⁻ > Br⁻ > Cl⁻ > F⁻)

### 4.6 Common Misconception Corrections

**Misconception 1**: "Alkynes are less reactive than alkenes"
**Reality**: Alkynes are generally less reactive in electrophilic additions (π electrons held tighter), BUT terminal alkynes are more acidic and alkynide anions are excellent nucleophiles.

**Misconception 2**: "Aromatic compounds don't react with electrophiles"
**Reality**: Aromatics react readily with electrophiles, but prefer substitution over addition to maintain aromaticity.

**Misconception 3**: "The longest chain is always the parent"
**Reality**: For alkenes and alkynes, the parent chain must contain the multiple bond, even if not the longest chain.

**Misconception 4**: "cis/trans and E/Z are interchangeable"
**Reality**: cis/trans only applies when each sp² carbon has one H and one non-H substituent. E/Z uses priority rules and applies universally.

**Misconception 5**: "All cyclic, conjugated systems are aromatic"
**Reality**: Must satisfy Hückel's rule (4n+2 π electrons). Cyclobutadiene (4 π electrons) is antiaromatic and highly unstable.

**Misconception 6**: "Carbocations always rearrange"
**Reality**: Rearrangement occurs only when a more stable carbocation can form via 1,2-shift. 3° carbocations rarely rearrange unless special stabilization (e.g., benzylic) is possible.

### 4.7 Mastery Validation Problems

**Problem Set 1: Structure and Nomenclature**

1. Draw all constitutional isomers of C₅H₁₀ and classify each (cycloalkane, alkene, etc.)
2. Name: (CH₃)₂CHCH₂C≡CCH(CH₃)₂
3. Draw the structure of (2E,4Z)-hexa-2,4-diene

**Problem Set 2: Mechanism and Stereochemistry**

4. Propose a mechanism for the addition of HBr to propene, showing carbocation formation and predicting the major product.
5. Explain why bromination of alkenes gives anti addition while hydrogenation gives syn addition.
6. Draw the chair conformations of cis-1,3-dimethylcyclohexane and predict the more stable conformer.

**Problem Set 3: Synthesis Design**

7. Synthesize (Z)-hex-3-ene from hex-3-yne.
8. Propose a synthesis of m-nitrobenzoic acid from benzene.
9. How would you convert benzene to p-nitrotoluene? Why is this order preferred?

**Problem Set 4: Reactivity Prediction**

10. Rank these alkenes by stability: 2-methylbut-2-ene, but-1-ene, (E)-but-2-ene, 2-methylprop-1-ene
11. Predict the major product(s) of: cyclohexanol + H₂SO₄/heat
12. Which position(s) in naphthalene are most reactive toward electrophilic substitution?

**Expected Mastery Outcomes:**
- 100% accuracy on nomenclature and structure drawing
- Complete mechanisms with correct electron flow
- Correct stereochemical predictions in >90% of cases
- Successful multistep synthesis design with proper ordering
- Accurate reactivity rankings based on first principles

### 4.8 Connection to Advanced Topics

This lesson provides foundation for:

- **Spectroscopy**: IR frequencies correlate with hybridization (C≡C at 2100-2200 cm⁻¹, C=C at 1620-1680 cm⁻¹)
- **Reaction mechanisms**: Carbocation chemistry appears in SN1, E1, and many rearrangements
- **Stereochemistry**: E/Z nomenclature extends to more complex systems; conformational analysis applies to all organic molecules
- **Synthesis planning**: EAS substituent effects and retrosynthetic logic apply throughout organic synthesis
- **Medicinal chemistry**: Aromatic rings are ubiquitous in pharmaceuticals (benzene ring present in ~75% of drugs)
- **Polymer chemistry**: Alkene polymerization (addition polymers) and aromatic polymers (Kevlar, polycarbonate)
- **Biochemistry**: Aromatic amino acids (Phe, Tyr, Trp), isoprene units in terpenes, unsaturated fatty acids

The principles established here—hybridization determining geometry and reactivity, stabilization through conjugation, electron-donating/withdrawing effects—recur throughout advanced organic chemistry and provide the interpretive framework for understanding complex molecular behavior.
