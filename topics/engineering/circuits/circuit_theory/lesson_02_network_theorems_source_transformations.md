# Lesson 2: Network Theorems, Source Transformations, Equivalent Circuits

## 1. First-Principles Intuition & Invariants

Every resistive network, regardless of its topological complexity, can be reduced to a simpler equivalent form when analyzed from the perspective of a single pair of terminals. This observation, born from the superposition principle and the linearity of Ohm's law, forms the foundation of network reduction theorems that transform labyrinthine circuit meshes into tractable, two-component models. The practical power of these theorems lies not in abstract mathematical elegance but in their capacity to collapse multi-branch networks into forms that permit rapid load analysis, impedance matching calculations, and iterative design refinement at the laboratory bench.

Thévenin's theorem, articulated by French telegraph engineer Léon Charles Thévenin in 1883, asserts that any linear two-terminal network containing independent sources, dependent sources, and resistances can be replaced by a single voltage source in series with a single resistance. Norton's theorem, formulated independently by Hans Ferdinand Mayer at Siemens in 1926 and later attributed to Bell Labs engineer Edward Lawry Norton, provides the dual representation: a current source in parallel with a resistance. These are not separate truths but rather two facets of the same fundamental equivalence, related by a simple source transformation that preserves terminal voltage-current characteristics while altering internal topology.

The invariant preserved across all network reduction theorems is the voltage-current relationship at the terminal pair under consideration. Whether you model a complex power distribution network as a Thévenin equivalent for voltage-mode analysis or as a Norton equivalent for current-mode nodal techniques, the external circuit—the load attached to those terminals—experiences identical electrical behavior. This equivalence extends to dependent sources, which introduce controlled feedback paths that modify the effective output impedance through mechanisms identical to operational amplifier gain-desensitivity effects. The mathematical linearity requirement means these theorems apply rigorously to resistive networks and extend naturally to AC analysis when resistances generalize to complex impedances, enabling frequency-domain modeling of filters, transmission lines, and antenna feed networks.

Maximum power transfer, a corollary of Thévenin's theorem, dictates that a load extracts maximum available power from a source when the load resistance exactly matches the source's Thévenin resistance. This condition, while optimal for power extraction efficiency measured at the load terminals, results in exactly 50% overall efficiency since half the generated power dissipates internally within the source resistance. Radio frequency engineers designing antenna matching networks confront this tradeoff daily: conjugate impedance matching maximizes signal transfer at the expense of power dissipation in the source, a compromise acceptable when the alternative is reflected power causing transmitter damage or reduced link margin.

The substitution theorem offers a conceptual bridge between circuit analysis and synthesis: if the voltage across or current through a branch element is known through measurement or prior calculation, that element may be replaced by an ideal voltage source or current source without disturbing the remainder of the network. This theorem underpins incremental circuit modification strategies where designers iteratively refine individual stages while preserving boundary conditions. Reciprocity, proven rigorously for bilateral passive networks, establishes that swapping the locations of an ideal voltage source and an ideal ammeter leaves the ammeter reading unchanged—a symmetry that simplifies two-port network characterization and forms the theoretical basis for antenna reciprocity in electromagnetic theory.

Millman's theorem, less widely celebrated but profoundly practical, reduces parallel branches containing series voltage sources and resistances to a single equivalent voltage source and resistance, providing a rapid computational pathway for multi-source networks where Kirchhoff's current law would otherwise demand solving simultaneous equations. Star-delta (also known as wye-delta or Y-Δ) transformations permit topological rewiring of three-terminal resistive subnetworks, converting between star configurations common in three-phase power distribution and delta configurations prevalent in impedance matching networks and bridge circuits. These transformations preserve the impedance seen between any pair of the three terminals while altering the internal structure, enabling mesh simplification that often converts non-planar circuit graphs into planar forms amenable to straightforward mesh or nodal analysis.

The presence of dependent sources—voltage-controlled voltage sources (VCVS), current-controlled current sources (CCCS), voltage-controlled current sources (VCCS), and current-controlled voltage sources (CCVS)—introduces controlled feedback that modifies effective resistance values through gain mechanisms. When computing Thévenin or Norton equivalents of networks containing dependent sources, the internal resistance calculation cannot rely solely on passive source deactivation; instead, the resistance must be extracted by applying a test source at the terminals and measuring the resulting current-to-voltage ratio, accounting for the modulation introduced by the controlled elements. This complication reflects the physical reality of active circuits containing transistor stages, operational amplifiers, and gyrator circuits, where feedback loops alter input and output impedances in ways that passive component analysis alone cannot predict.


## 2. Core Architecture & Mechanics

The mechanical procedure for Thévenin equivalent extraction begins with terminal identification. Designate the pair of nodes across which you wish to compute the equivalent circuit as terminals A and B. The Thévenin voltage, denoted $V_{TH}$, equals the open-circuit voltage measured between terminals A and B when no load is connected. Computation of this voltage typically requires full nodal or mesh analysis of the original network with all independent sources active and the load disconnected. For simple voltage divider topologies, $V_{TH}$ emerges from ratio inspection, but for networks with multiple sources or internal feedback paths, superposition or systematic nodal voltage solution becomes necessary.

The Thévenin resistance $R_{TH}$ represents the equivalent resistance seen looking back into the network from terminals A and B with all independent sources deactivated—voltage sources replaced by short circuits and current sources replaced by open circuits. In purely passive networks without dependent sources, $R_{TH}$ reduces to the series-parallel combination of the remaining resistances. When dependent sources exist, this passive deactivation method fails because dependent sources must remain active, responding to their controlling variables. The robust computational approach applies a test voltage source $V_{test}$ at terminals A and B, measures or calculates the resulting current $I_{test}$, and computes $R_{TH} = V_{test} / I_{test}$. Alternatively, apply a test current source $I_{test}$, measure the resulting voltage $V_{test}$, and compute the same ratio. This test source method works universally, accommodating dependent sources by evaluating the complete network response including feedback effects.

Norton equivalent extraction follows a parallel pathway. The Norton current $I_{N}$ equals the short-circuit current flowing from terminal A to terminal B when those terminals are directly connected by an ideal wire. This current can be computed via mesh analysis with the short circuit in place, or more elegantly recognized as $I_{N} = V_{TH} / R_{TH}$ once the Thévenin equivalent is known, exploiting the duality between representations. The Norton resistance $R_{N}$ equals $R_{TH}$ identically, since both represent the same internal impedance viewed from the terminal pair. The transformation between Thévenin and Norton forms thus reduces to:

$$
V_{TH} = I_{N} \cdot R_{N}
$$

$$
I_{N} = \frac{V_{TH}}{R_{TH}}
$$

$$
R_{N} = R_{TH}
$$

Source transformation, the repeated application of this Thévenin-Norton duality to individual branches, enables iterative network simplification. A voltage source $V_s$ in series with resistance $R_s$ transforms to a current source $I_s = V_s / R_s$ in parallel with the same resistance $R_s$. Conversely, a current source $I_s$ in parallel with $R_s$ transforms to a voltage source $V_s = I_s \cdot R_s$ in series with $R_s$. Apply these transformations strategically to convert series branches into parallel branches or vice versa, facilitating combination of like-topology elements. For instance, multiple current sources in parallel combine by algebraic addition of their magnitudes, while their parallel resistances combine via the standard parallel resistance formula $R_{eq} = (1/R_1 + 1/R_2 + \ldots + 1/R_n)^{-1}$.

Maximum power transfer derivation proceeds from the Thévenin equivalent circuit loaded by a variable resistance $R_L$. The power dissipated in the load becomes:

$$
P_L = I^2 R_L = \left( \frac{V_{TH}}{R_{TH} + R_L} \right)^2 R_L = \frac{V_{TH}^2 R_L}{(R_{TH} + R_L)^2}
$$

Differentiate with respect to $R_L$ and set the derivative to zero:

$$
\frac{dP_L}{dR_L} = V_{TH}^2 \frac{(R_{TH} + R_L)^2 - 2R_L(R_{TH} + R_L)}{(R_{TH} + R_L)^4} = 0
$$

Simplify the numerator:

$$
(R_{TH} + R_L)^2 - 2R_L(R_{TH} + R_L) = (R_{TH} + R_L)(R_{TH} + R_L - 2R_L) = (R_{TH} + R_L)(R_{TH} - R_L) = 0
$$

Since $R_{TH} + R_L \neq 0$, the condition reduces to $R_{TH} = R_L$. Under this matched condition, the maximum load power becomes:

$$
P_{L,max} = \frac{V_{TH}^2 R_{TH}}{(2R_{TH})^2} = \frac{V_{TH}^2}{4R_{TH}}
$$

The total power supplied by the source equals $P_{total} = V_{TH}^2 / (2R_{TH})$, confirming that exactly half the source power reaches the load while half dissipates internally, yielding 50% efficiency.

Millman's theorem addresses the specific topology of N parallel branches, where branch $k$ consists of a voltage source $V_k$ in series with resistance $R_k$. The equivalent circuit reduces to a single voltage source $V_{eq}$ in series with resistance $R_{eq}$, where:

$$
V_{eq} = \frac{\sum_{k=1}^{N} \frac{V_k}{R_k}}{\sum_{k=1}^{N} \frac{1}{R_k}}
$$

$$
R_{eq} = \frac{1}{\sum_{k=1}^{N} \frac{1}{R_k}}
$$

This formulation resembles a conductance-weighted average of the source voltages. In practical terms, branches with smaller series resistances (larger conductances) exert proportionally greater influence on the equivalent voltage, reflecting their ability to supply more current. Millman's theorem streamlines analysis of multi-supply bus networks and permits rapid hand calculation without invoking full nodal analysis machinery.

Star-delta transformations convert between three-terminal configurations. Given a star (wye) network with resistances $R_1$, $R_2$, and $R_3$ connected to a common central node and extending to terminals A, B, and C respectively, the equivalent delta network with resistances $R_{AB}$, $R_{BC}$, and $R_{CA}$ connecting the terminals pairwise satisfies:

$$
R_{AB} = \frac{R_1 R_2 + R_2 R_3 + R_3 R_1}{R_3}
$$

$$
R_{BC} = \frac{R_1 R_2 + R_2 R_3 + R_3 R_1}{R_1}
$$

$$
R_{CA} = \frac{R_1 R_2 + R_2 R_3 + R_3 R_1}{R_2}
$$

Notice that the numerator remains identical for all three delta resistances, representing the sum of all pairwise products of star resistances. Each delta resistance divides this sum by the star resistance opposite the corresponding delta edge. The inverse transformation, delta to star, derives from algebraic manipulation:

$$
R_1 = \frac{R_{AB} R_{CA}}{R_{AB} + R_{BC} + R_{CA}}
$$

$$
R_2 = \frac{R_{AB} R_{BC}}{R_{AB} + R_{BC} + R_{CA}}
$$

$$
R_3 = \frac{R_{BC} R_{CA}}{R_{AB} + R_{BC} + R_{CA}}
$$

Each star resistance equals the product of its two adjacent delta resistances divided by the sum of all three delta resistances. For the special case of a balanced three-phase system where all star resistances equal $R_Y$ and all delta resistances equal $R_\Delta$, the transformation simplifies to $R_\Delta = 3R_Y$.

```text
Star (Wye) Configuration:          Delta Configuration:

        A                               A
        |                              / \
       R1                          R_AB   R_CA
        |                          /       \
    ----●----                     B---------C
    |       |                         R_BC
   R2       R3
    |       |
    B       C
```

The substitution theorem operates by recognizing that any branch element can be replaced by an equivalent source matching its terminal conditions. If a resistor carries current $I$ with voltage drop $V = IR$, substitute an ideal voltage source of magnitude $V$ with polarity matching the original voltage drop, or substitute an ideal current source of magnitude $I$ with direction matching the original current flow. The remainder of the network experiences no perturbation. This theorem proves particularly valuable in piecewise linearization of nonlinear circuits, where a nonlinear element's operating point, once determined, allows replacement by a linear equivalent for small-signal analysis.

Reciprocity theorem formalization requires careful statement: in a linear bilateral network containing a single voltage source, if the source placed between nodes A and B produces current $I$ through nodes C and D, then moving the source to nodes C and D will produce the same current $I$ through nodes A and B. The bilateral requirement excludes components with directional characteristics such as diodes and transistors operating in nonlinear modes. For AC analysis, reciprocity extends to complex impedances provided all passive elements exhibit bilateral impedance characteristics. Antenna engineers exploit reciprocity when characterizing antenna patterns: transmit pattern measurements directly predict receive patterns without requiring separate receive-mode testing infrastructure.

Dependent source handling during Thévenin resistance computation demands attention to controlling variable preservation. Consider a VCVS with gain $A$ where the output voltage equals $A$ times some controlling voltage $V_c$ elsewhere in the network. When applying a test voltage source to compute $R_{TH}$, the VCVS remains active, contributing voltage determined by $V_c$, which itself depends on the test source through the network's response. The resulting $R_{TH}$ may even exhibit negative values, indicating that the network delivers power rather than absorbing it, a characteristic of active circuits containing amplification. Similarly, a CCCS with transconductance $g_m$ (as in a common-emitter transistor model) modulates current based on a controlling current, altering effective impedance through feedback action.


## 3. High-Performance Optimization & Failure Modes

Workflow acceleration in practical circuit analysis hinges on pattern recognition that bypasses full symbolic solution. When confronted with a multi-stage amplifier requiring input impedance characterization, immediately identify the terminal pair of interest and mentally partition the network into the subsystem under analysis versus everything else treated as load or source. Apply Thévenin equivalencing iteratively, starting from the deepest nested stage and propagating outward, replacing each analyzed stage with its two-component equivalent before tackling the next level of hierarchy. This divide-and-conquer strategy transforms a ten-node network into a sequence of two-node problems, each solvable by inspection or minimal computation.

Source transformation proves most powerful when the goal involves combining multiple sources. Convert all voltage sources to current sources if working toward a parallel configuration amenable to nodal analysis, or convert all current sources to voltage sources if mesh analysis suits the topology better. Mixed topologies benefit from hybrid approaches: transform individual branches to achieve local series or parallel groupings, combine the simplified sections, then potentially transform back to match the original configuration type. The key insight recognizes that each transformation preserves electrical equivalence while potentially exposing algebraic simplifications invisible in the original form.

Laboratory validation of Thévenin equivalents requires careful measurement protocol. To measure $V_{TH}$ directly, disconnect the load and probe the open-circuit voltage between terminals A and B using a high-impedance voltmeter—10 MΩ input impedance for general work, higher for high-impedance circuit nodes. To measure $R_{TH}$ experimentally, the test source method translates to applying a known voltage from a precision DC power supply or function generator with series current-sense resistor, measuring terminal voltage and current simultaneously, and computing the ratio. Alternatively, reconnect the load, measure the loaded terminal voltage $V_L$ and load current $I_L$, then compute $R_{TH} = (V_{TH} - V_L) / I_L$. This method exploits the voltage divider relationship between $R_{TH}$ and $R_L$ without requiring source deactivation, valuable when the original network contains elements difficult to deactivate such as biasing networks or charged capacitors transitioning to resistive analysis after DC steady state.

Maximum power transfer calculations frequently encounter the misconception that matching always constitutes optimal design. In battery-powered systems, maximizing load power at 50% efficiency rapidly depletes the battery, contradicting design intent. Instead, operate with $R_L \gg R_{TH}$ to achieve high efficiency despite reduced absolute power transfer, acceptable when the available power exceeds requirements. Conversely, RF amplifier output stages driving 50Ω transmission lines must match impedances to prevent standing waves and reflections that corrupt signal integrity and potentially damage output transistors through voltage standing wave ratio (VSWR) induced overvoltage. The maximum power transfer theorem provides the boundary condition for optimal power extraction; practical design balances this against efficiency, thermal limits, and cost constraints.

Star-delta transformations often reveal hidden series or parallel combinations in bridge circuits and three-phase systems. The classic Wheatstone bridge, initially presenting four resistors in a non-series, non-parallel topology, becomes trivially solvable after star-delta transformation converts one of its triangular sections into a star, exposing series and parallel paths. The computational cost involves evaluating the transformation formulas once, after which standard series-parallel reduction proceeds immediately. In three-phase power distribution analysis, delta loads convert to equivalent wye configurations to enable per-phase analysis with neutral reference, simplifying unbalanced load calculations.

Dependent source circuit reduction exhibits failure modes when controlling variables become ambiguous after simplification. If a VCCS depends on a voltage across a resistor that gets combined with other elements during Thévenin reduction, the controlling variable reference may vanish, invalidating the simplification. The remedy requires careful tracking of controlling variable locations, sometimes necessitating auxiliary equations that express the controlling variable in terms of the new simplified circuit's variables. Alternatively, defer simplification of branches containing controlling variables until after computing the dependent source contributions, then fold those contributions into the final equivalent.

Numerical precision degradation plagues hand calculations involving star-delta transformations when resistance ratios span multiple decades. A star network with $R_1 = 1\,\Omega$, $R_2 = 10\,\text{k}\Omega$, $R_3 = 10\,\text{k}\Omega$ transforms to delta values including $R_{AB} \approx 100\,\text{M}\Omega$ and $R_{BC} = R_{CA} \approx 10\,\text{k}\Omega$, where the 100 MΩ value emerges from the numerator sum $(1 \cdot 10^4 + 10^4 \cdot 10^4 + 10^4 \cdot 1) / 10^4 \approx 10^4$ divided by the 1Ω denominator resistance. This extreme range complicates further analysis; recognizing when a transformed resistance becomes effectively an open circuit permits approximation that avoids carrying insignificant terms through subsequent calculations.

Reciprocity verification in the laboratory provides a powerful sanity check for passive network characterization. Construct a test fixture with accessible injection and measurement ports, inject a known AC signal at port 1 while measuring response at port 2, then swap injection and measurement locations. Deviations from reciprocal response indicate either nonlinear operation, directional components, or measurement error such as ground loop coupling or probe loading. For two-port networks characterized by Z-parameters, reciprocity demands $Z_{12} = Z_{21}$; for Y-parameters, $Y_{12} = Y_{21}$. Automated network analyzers implement reciprocity checks as part of calibration validation sequences.

Thévenin equivalent extraction from circuits containing operational amplifiers requires recognizing that an ideal op-amp with feedback enforces $V_+ = V_-$ and draws zero input current, constraints that simplify analysis dramatically. However, the op-amp itself contains internal dependent sources—typically modeled as a VCVS with open-loop gain $A_{OL}$—so the Thévenin resistance looking back into an op-amp output may approach zero (stiff voltage source) for negative feedback configurations or become large for high-output-impedance topologies. Real op-amps introduce frequency-dependent output impedance and finite open-loop gain, requiring AC analysis with complex impedances and careful attention to stability margins when feedback paths contain reactive elements.

Millman's theorem encounters numerical instability when branch conductances vary widely, similar to the star-delta precision issue. A network with parallel branches having resistances 1Ω, 1kΩ, and 1MΩ yields conductances $1\,\text{S}$, $1\,\text{mS}$, and $1\,\mu\text{S}$. The 1Ω branch dominates the equivalent conductance sum, rendering the contributions from the 1MΩ branch negligible in most practical accuracy contexts. Recognize such dominance early and omit negligible terms to streamline computation without sacrificing meaningful accuracy.

Superposition, while not detailed in this lesson's primary focus, interacts synergistically with Thévenin and Norton equivalencing. When a network contains multiple independent sources, compute the Thévenin equivalent contribution from each source independently with all others deactivated, then superimpose the resulting $V_{TH}$ values algebraically while recognizing that $R_{TH}$ derives from the passive network and remains constant across all superposition terms. This hybrid approach decomposes complex multi-source problems into manageable single-source subproblems.

Real-world component tolerance propagation through equivalent circuits demands attention in precision applications. If the original network resistances exhibit ±1% tolerance, the Thévenin voltage and resistance inherit compounded uncertainty from ratio calculations and sums. Monte Carlo simulation or worst-case analysis quantifies the tolerance envelope, ensuring that matched load designs achieve acceptable performance across manufacturing variation. For maximum power transfer in radio frequency matching networks, component tolerance directly affects realized VSWR and link margin, potentially degrading communication range below specification if equivalents assume ideal nominal values.

Finally, recognize that network theorems apply rigorously to linear time-invariant circuits operating in DC steady state or AC sinusoidal steady state. Transient analysis, nonlinear semiconductor circuits, and time-varying parameter systems require extensions beyond the basic theorems. Small-signal linearization permits Thévenin equivalent extraction around an operating point for incremental analysis of weakly nonlinear circuits, while piecewise-linear models approximate diodes and transistors as switched networks of linear equivalent circuits, each valid over a defined operating region. The foundational principles of terminal equivalence and source transformation remain applicable, adapted through appropriate modeling techniques to accommodate the physical realities of active semiconductor devices and energy storage elements.
