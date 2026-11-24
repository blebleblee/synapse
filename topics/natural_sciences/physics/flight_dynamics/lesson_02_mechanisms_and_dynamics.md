# Lesson 2: Physical Mechanisms & Dynamical Equations

Flight is not a phenomenon imposed on the air. It is a negotiation between a solid body and a fluid continuum, mediated by pressure gradients, viscous shear, inertial momentum, and gravitational potential. Every aircraft in steady cruise, every bird banking through a thermal, every spinning maple seed descending in autumn embodies a precise instantaneous solution to a system of nonlinear partial differential equations. This lesson dismantles those equations from first principles, then immediately anchors them to the measurement strategies, instrumentation choices, and data-reduction procedures that practicing flight dynamicists use in wind tunnels, flight-test programs, and computational simulations.

---

## 1. Governing Differential Equations & Analytical Derivations

### 1.1 The Navier–Stokes Foundation

The irreducible governing law of aerodynamics is Newton's second law applied to a fluid parcel. For a Newtonian, incompressible fluid of density $\rho$ and dynamic viscosity $\mu$, that statement produces the incompressible Navier–Stokes equations:

$$
\rho \left( \frac{\partial \vec{u}}{\partial t} + (\vec{u} \cdot \nabla)\vec{u} \right) = -\nabla p + \mu \nabla^2 \vec{u} + \rho \vec{g}
$$

$$
\nabla \cdot \vec{u} = 0
$$

Here $\vec{u}(\vec{x}, t)$ is the local velocity field (m/s), $p(\vec{x}, t)$ is the mechanical pressure (Pa), and $\vec{g}$ is gravitational acceleration (m/s²). The left-hand side is the material acceleration of a fluid parcel: the local time rate of change $\partial \vec{u}/\partial t$ plus the convective acceleration $(\vec{u} \cdot \nabla)\vec{u}$, which captures the fact that a parcel moving into a region of different velocity experiences acceleration even in a steady flow. The right-hand side balances three physical agents: the pressure gradient force that accelerates fluid from high to low pressure, the viscous diffusion term $\mu \nabla^2 \vec{u}$ that redistributes momentum through molecular shear, and body forces from gravity.

The ratio of inertial to viscous forces defines the Reynolds number, the single most important dimensionless parameter in aerodynamics:

$$
Re = \frac{\rho U L}{\mu} = \frac{U L}{\nu}
$$

where $U$ is a characteristic velocity (m/s), $L$ is a characteristic length (m), and $\nu = \mu/\rho$ is the kinematic viscosity (m²/s). At sea level in the International Standard Atmosphere, $\nu_{\text{air}} \approx 1.46 \times 10^{-5}$ m²/s. A general aviation aircraft with chord $L = 1.5$ m cruising at $U = 55$ m/s operates at $Re \approx 5.6 \times 10^6$, squarely in the turbulent regime where the boundary layer transitions on the forward third of the wing. A dragonfly with chord 4 mm at 5 m/s operates at $Re \approx 1400$, where viscous forces dominate and separated vortex lift becomes the dominant mechanism rather than attached Kutta–Joukowski circulation.

**Experimental calibration protocol — Reynolds number matching in a wind tunnel.** When you configure a low-speed open-circuit tunnel for a wing section experiment, you must match the flight Reynolds number to within ±5% to preserve boundary layer topology. Measure ambient temperature $T$ with a calibrated platinum resistance thermometer (PRT) accurate to ±0.1°C, and barometric pressure $P_{\text{atm}}$ with a Digiquartz transducer accurate to ±0.01 hPa. Compute kinematic viscosity from Sutherland's formula:

$$
\mu(T) = \mu_0 \left(\frac{T}{T_0}\right)^{3/2} \frac{T_0 + S}{T + S}
$$

with reference values $\mu_0 = 1.716 \times 10^{-5}$ Pa·s, $T_0 = 273.15$ K, and Sutherland constant $S = 110.4$ K, all temperatures in Kelvin. With $\nu$ in hand, set tunnel freestream velocity $U_\infty$ via the pitot-static system using:

$$
U_\infty = \sqrt{\frac{2 \Delta p_{\text{pitot}}}{\rho}}
$$

where $\rho = P_{\text{atm}} / (R_{\text{air}} T)$ with $R_{\text{air}} = 287.058$ J/(kg·K). Tune the tunnel fan drive frequency until $Re = U_\infty c / \nu$ reaches the target value. Document tunnel turbulence intensity $Tu = \sqrt{\overline{u'^2}}/U_\infty$ with a hot-wire anemometer; values above $Tu = 0.1\%$ will artificially advance boundary-layer transition and corrupt your drag polar measurements.

### 1.2 The Equations of Rigid-Body Flight Dynamics

The Navier–Stokes equations govern the aerodynamic environment around the aircraft. A second, coupled system governs the rigid-body motion of the aircraft itself through that environment. The standard 6-degree-of-freedom (6-DOF) equations of motion express Newton's and Euler's laws in the body-fixed frame, whose axes $(x_B, y_B, z_B)$ are aligned with the aircraft's forward, right, and downward directions respectively. The translational equations are:

$$
m(\dot{u} + qw - rv) = F_X
$$
$$
m(\dot{v} + ru - pw) = F_Y
$$
$$
m(\dot{w} + pv - qu) = F_Z
$$

where $(u, v, w)$ are body-axis velocity components (m/s), $(p, q, r)$ are roll, pitch, and yaw rates (rad/s), $m$ is aircraft mass (kg), and $(F_X, F_Y, F_Z)$ are the total external forces in the body frame, comprising aerodynamic forces, thrust, and gravity resolved through the Euler angle rotation matrix. The rotational equations — Euler's equations for a rigid body with inertia tensor $\mathbf{I}$ — are:

$$
I_{xx}\dot{p} - I_{xz}(\dot{r} + pq) + (I_{zz} - I_{yy})qr = L
$$
$$
I_{yy}\dot{q} + (I_{xx} - I_{zz})pr + I_{xz}(p^2 - r^2) = M
$$
$$
I_{zz}\dot{r} - I_{xz}(\dot{p} - qr) + (I_{yy} - I_{xx})pq = N
$$

Here $I_{xx}$, $I_{yy}$, $I_{zz}$ are the principal moments of inertia about the roll, pitch, and yaw axes respectively (kg·m²), $I_{xz}$ is the cross-product of inertia in the $xz$-plane (kg·m²), and $(L, M, N)$ are the aerodynamic and thrust moments (N·m). The $I_{xz}$ term is nonzero for most conventional aircraft because the mass distribution is not symmetric about the $xB$–$zB$ plane when you account for engine placement, wing sweep, and fuel asymmetry. Neglecting it introduces coupling errors that become significant during sideslip maneuvers.

**Experimental identification of inertial properties.** The moments of inertia are not directly observable in flight; they must be measured on the ground using a bifilar pendulum or a compound pendulum rig before a flight-test campaign. For a bifilar torsional pendulum, suspend the aircraft (or a scaled model) from two parallel wires of length $l$ separated by distance $d$. The restoring torque for a twist angle $\theta$ is $\tau = mgd^2\theta/(4l)$, giving a torsional oscillation period:

$$
T_{\text{osc}} = 2\pi \sqrt{\frac{4 I_{\text{axis}} l}{m g d^2}}
$$

Solving for the moment of inertia:

$$
I_{\text{axis}} = \frac{m g d^2 T_{\text{osc}}^2}{16 \pi^2 l}
$$

Measure $T_{\text{osc}}$ as the average of at least 20 consecutive oscillation periods using a high-resolution digital timer (resolution ≤ 1 ms). Repeat the suspension in all three body-axis orientations and in a combined yaw-roll orientation at 45° to extract $I_{xz}$ using the parallel-axis decomposition. Uncertainty in $I_{\text{axis}}$ propagates as:

$$
\frac{\delta I}{I} = \sqrt{\left(\frac{\delta m}{m}\right)^2 + \left(\frac{2\delta d}{d}\right)^2 + \left(\frac{2\delta T}{T}\right)^2 + \left(\frac{\delta l}{l}\right)^2}
$$

For a 1500 kg GA aircraft, targeting $\delta I / I < 1\%$ requires mass measurement to ±0.5 kg, wire separation $d$ to ±0.5 mm, and period measurement to ±5 ms.

### 1.3 Small-Perturbation Linearization and the Stability Derivatives

The full 6-DOF system is nonlinear and couples all six states. For stability analysis and control design, the standard approach is to linearize about a trim condition — a steady, wings-level, unaccelerated flight state. Let every state variable be decomposed into a trim value and a small perturbation: $u = U_0 + \Delta u$, $q = 0 + \Delta q$, $\alpha = \alpha_0 + \Delta\alpha$, etc. Retaining only first-order perturbation terms and exploiting the symmetry of conventional aircraft (which decouples longitudinal from lateral-directional modes to first order), the longitudinal perturbation equations become:

$$
\begin{pmatrix} \dot{\Delta u} \\ \dot{\Delta w} \\ \dot{\Delta q} \\ \dot{\Delta\theta} \end{pmatrix} = \mathbf{A}_{\text{lon}} \begin{pmatrix} \Delta u \\ \Delta w \\ \Delta q \\ \Delta\theta \end{pmatrix} + \mathbf{B}_{\text{lon}} \Delta\delta_e
$$

The system matrix $\mathbf{A}_{\text{lon}}$ is populated entirely by aerodynamic stability derivatives — partial derivatives of the aerodynamic force and moment coefficients with respect to each state variable. The pitching moment coefficient $C_m$ depends on angle of attack, pitch rate, and elevator deflection through:

$$
C_m = C_{m_0} + C_{m_\alpha}\alpha + C_{m_q}\frac{qc}{2U_0} + C_{m_{\dot{\alpha}}}\frac{\dot{\alpha}c}{2U_0} + C_{m_{\delta_e}}\delta_e
$$

where $c$ is the mean aerodynamic chord (m) and all derivatives are dimensionless. The static longitudinal stability criterion requires $C_{m_\alpha} < 0$: an increase in angle of attack must generate a nose-down restoring moment. The numerical value of $C_{m_\alpha}$ is the most consequential single parameter in aircraft handling qualities, and measuring it accurately is a central objective of any wind tunnel or flight test program.

**Wind tunnel measurement of $C_{m_\alpha}$.** Mount a full-span model on a six-component strain-gauge balance inside the test section. Zero the balance with no flow, then bring the tunnel to test Reynolds number. Set the model incidence to $\alpha = -4°$ using a calibrated incidence mechanism with resolution ±0.05°, record the pitching moment coefficient $C_m$ after averaging 10 seconds of data at 1 kHz sample rate, then step $\alpha$ in 1° increments to $\alpha = +14°$. The stability derivative is the slope of the linear portion of the $C_m$–$\alpha$ curve, which you extract via ordinary least-squares regression across the linear range (typically $-2° \leq \alpha \leq 8°$ for a conventional airfoil):

$$
C_{m_\alpha} = \frac{\sum_{i}(\alpha_i - \bar{\alpha})(C_{m,i} - \bar{C}_m)}{\sum_{i}(\alpha_i - \bar{\alpha})^2}
$$

Apply tunnel wall interference corrections following the standard ESDU 76028 method before computing the derivative. Tare runs at each incidence with no model (or a dummy sting) isolate aerodynamic signal from balance and sting loads.

---

## 2. Microscopic vs. Macroscopic Phase Transitions

### 2.1 Boundary Layer Transition: From Laminar Order to Turbulent Chaos

The most consequential phase transition in applied aerodynamics occurs within the boundary layer — the thin region of retarded flow adjacent to the wing surface where viscous shear dissipates momentum. In the laminar state, fluid parcels move in parallel streamlines; momentum transport occurs only through molecular viscosity; and wall shear stress is comparatively low. In the turbulent state, three-dimensional vortical eddies at a continuous range of length scales transport momentum transversely across the layer far more effectively than molecular diffusion alone; wall shear stress increases by a factor of three to ten; and skin friction drag rises accordingly. This is not merely a quantitative change in flow character — it is a topological phase transition from a low-dimensional, quasi-ordered state to a high-dimensional, chaotic attractor.

The laminar boundary layer on a flat plate is described analytically by the Blasius solution. The boundary layer thickness $\delta_{99}$ — the wall-normal distance at which the local velocity reaches 99% of the freestream — grows as:

$$
\delta_{99}(x) = 4.91 \sqrt{\frac{\nu x}{U_\infty}} = 4.91 \frac{x}{\sqrt{Re_x}}
$$

where $Re_x = U_\infty x / \nu$ is the local Reynolds number based on streamwise distance $x$ from the leading edge. The local skin friction coefficient in the laminar regime is:

$$
C_{f,\text{lam}}(x) = \frac{0.664}{\sqrt{Re_x}}
$$

The transition from laminar to turbulent flow begins with the amplification of Tollmien–Schlichting (TS) waves — two-dimensional instability modes that satisfy the Orr–Sommerfeld equation. These waves first become unstable above a critical Reynolds number $Re_{x,\text{crit}} \approx 3 \times 10^5$ for a zero-pressure-gradient flat plate, though adverse pressure gradients (flow decelerating toward the trailing edge) reduce this to as low as $Re_{x,\text{crit}} \approx 10^5$, and favorable pressure gradients can sustain laminar flow past $Re_x = 10^6$. After TS wave amplification, the flow passes through secondary instability (Lambda vortex formation), vortex breakdown, and finally full turbulent breakdown over a transition zone of finite extent. In the fully turbulent regime, the local skin friction follows the empirical relation:

$$
C_{f,\text{turb}}(x) \approx \frac{0.0592}{Re_x^{1/5}}
$$

which is substantially higher than the laminar value. The integrated drag penalty from premature transition over a natural-laminar-flow (NLF) wing designed for 60% laminar run can exceed 30% of total profile drag, making transition location the controlling design variable for high-performance gliders and long-endurance UAVs.

**Transition detection by surface pressure and hot-film anemometry.** The standard experimental method for locating transition on a wind tunnel model combines two independent techniques. First, apply a continuous array of surface pressure taps at $x/c = 0.02, 0.05, 0.10, 0.15, \ldots, 0.90$ along the suction surface, chordwise at $y/b = 0.50$ (midspan). Transition produces a characteristic inflection in the pressure distribution: the laminar separation bubble (if present) manifests as a plateau in $C_p$ followed by a sharp pressure recovery at reattachment. Plot the pressure coefficient:

$$
C_p(x) = \frac{p(x) - p_\infty}{\frac{1}{2}\rho U_\infty^2}
$$

and locate the inflection point to within one tap spacing. For higher spatial resolution, bond a spanwise array of flush-mounted constant-temperature hot-film sensors (Dantec 55R47 or equivalent, overheat ratio $a = (R_w - R_0)/R_0 = 0.08$ for surface gauges) at $x/c$ locations between 0.10 and 0.60 in 0.025$c$ increments. The root-mean-square of the bridge voltage output $V_{\text{rms}}$ rises abruptly at transition by a factor of 3 to 6, providing a direct indicator of turbulent intermittency. Cross-plot $V_{\text{rms}}(x/c)$ with the pressure distribution: the onset of elevated $V_{\text{rms}}$ should coincide with the pressure plateau midpoint to within ±0.01$c$ when both diagnostics are functioning correctly.

### 2.2 Flow Separation and the Stall Transition

At angles of attack beyond the design range, the adverse pressure gradient on the suction surface intensifies until the boundary layer can no longer remain attached. The wall-normal velocity gradient at the surface, $\partial u / \partial y |_{y=0}$, reaches zero — the mathematical definition of separation — and the boundary layer detaches, forming a region of reversed flow. This is the stall transition: a sudden, global reorganization of the flowfield topology from an attached, lift-generating configuration to a separated, wake-dominated state.

There are three aerodynamically distinct stall types depending on airfoil geometry and Reynolds number. In a trailing-edge stall (thick airfoils, $t/c > 12\%$, $Re > 10^6$), turbulent boundary layer separation originates at the trailing edge and progresses forward continuously with increasing $\alpha$, producing a gradual round-topped $C_L$–$\alpha$ curve and benign handling qualities.

In contrast, **leading-edge stall** (thin airfoils, $t/c < 10\%$, moderate $Re \sim 5 \times 10^5$ to $2 \times 10^6$) occurs when the laminar boundary layer separates near the leading edge and fails to reattach, creating an abrupt lift loss as a separation bubble bursts. The $C_L$–$\alpha$ curve exhibits a sharp peak followed by rapid collapse, often with significant hysteresis between increasing and decreasing $\alpha$ sweeps. This behavior is particularly sensitive to leading-edge contamination, surface roughness, and acoustic disturbances. Finally, **thin-airfoil stall** (very thin sections, $t/c < 6\%$, low $Re < 5 \times 10^5$) combines both mechanisms: laminar separation near the leading edge with simultaneous trailing-edge separation, producing an extremely narrow operating envelope and pronounced Reynolds-number dependence. All three types share the same physical origin—the Navier–Stokes momentum balance cannot sustain attached flow when $\int_0^\delta (U_e - u) \, dy$ exceeds the turbulent mixing capacity—but manifest different symptomology depending on whether the critical separation point lies forward or aft of the transition zone.

The practical consequence for flight dynamics is that stall imposes a firm upper bound on usable lift coefficient, typically $C_{L,\max} \approx 1.2$ to $1.8$ for conventional sections, which in turn dictates minimum flying speed $V_{\min} = \sqrt{2W/(\rho S C_{L,\max})}$ and maximum sustained load factor $n_{\max} = (\rho V^2 S C_{L,\max})/(2W)$ at any given airspeed. Post-stall, the center-of-pressure shift generates a strong nose-down pitching moment ($\Delta C_m \approx -0.3$ to $-0.5$ for aft-loaded sections) that provides natural stall recovery if the static margin is positive, but can drive deep-stall lock-in on T-tail configurations where the separated wing wake blankets the horizontal stabilizer. Accurate prediction requires either high-fidelity RANS with transition modeling (e.g., $\gamma$–$\text{Re}_{\theta t}$ or Menter SST with intermittency transport) or direct wind-tunnel measurement at matched Reynolds and Mach numbers, since panel methods and inviscid Euler solutions become wholly invalid once $\partial u/\partial y|_{y=0} \to 0$.

---

## Summary & Verification Matrix

| **Invariant / Mechanism** | **Governing Relation** | **Physical Interpretation** | **Diagnostic Criterion** | **Typical Value / Threshold** |
|---------------------------|------------------------|----------------------------|--------------------------|-------------------------------|
| **Kutta condition** | $\Gamma = \pi c U_\infty \sin(\alpha + \beta)$ or $\Delta C_p \to 0$ at TE | Circulation adjusts until trailing-edge stagnation point lies exactly on the sharp edge, eliminating infinite velocities | Pressure taps at $x/c = 0.95, 0.98$ on upper/lower surfaces must read equal static pressure within ±0.5% $q_\infty$ | $\|C_{p,\text{upper}} - C_{p,\text{lower}}\|_{x/c=1} < 0.01$ |
| **Laminar–turbulent transition** | Orr–Sommerfeld eigenvalue $\text{Im}(\omega) > 0$ when $\text{Re}_{\delta^*} > 520$ (Tollmien–Schlichting); $H_{12} \approx 2.6$ at separation | Small disturbances amplify exponentially once Reynolds number based on displacement thickness exceeds critical value; shape factor drops from 2.6 (laminar) to 1.4 (turbulent) | Hot-film $V_{\text{rms}}$ increase by factor 3–6; surface oil-flow visualization shows sudden thickening of streamline spacing | Transition $x/c \approx 0.3$–$0.5$ for clean airfoil at $Re_c = 10^6$; $V_{\text{rms,turb}}/V_{\text{rms,lam}} > 3$ |
| **Boundary-layer separation** | $\partial u/\partial y\|_{y=0} = 0$ and $\tau_w = \mu (\partial u/\partial y)\|_{y=0} = 0$ | Adverse pressure gradient $dp/dx > 0$ decelerates near-wall fluid until wall shear stress vanishes and flow reverses | Tuft reversal; surface oil accumulation line; $C_p$ plateau in pressure distribution; PIV reveals negative $u$ component near wall | Turbulent separation: $C_p$ recovery $\Delta C_p > 0.6$ over $\Delta x/c \sim 0.3$; laminar: $\Delta C_p > 0.1$ over $\Delta x/c \sim 0.05$ |
| **Stall onset & $C_{L,\max}$** | $C_L = 2\pi(\alpha - \alpha_{L=0})$ breaks down; $\partial C_L/\partial\alpha \to 0$ then negative | Global flow topology transition from attached circulation to separated wake; lift slope collapses when separation region exceeds ~30% chord | Force-balance $C_L$ plateau or downturn; tuft reversal over >50% upper surface; sudden $C_m$ pitch-break | $C_{L,\max} \approx 1.2$–$1.8$ (section); stall $\alpha \approx 12°$–$18°$ depending on $t/c$, leading-edge radius, $Re$ |
| **Pressure coefficient** | $C_p = (p - p_\infty)/(½\rho U_\infty^2)$ | Dimensionless measure of local static pressure relative to freestream dynamic pressure; integrates to section lift and moment | Compare measured $C_p(x/c)$ to panel-method or thin-airfoil theory prediction; suction peak $C_{p,\min} \approx -2$ to $-4$ near leading edge at moderate $\alpha$ | Inviscid agreement within 5% up to $C_{p,\min}$; deviation >15% indicates separation or transition modeling error |
| **Reynolds-number scaling** | $Re_c = \rho U_\infty c/\mu$; transition $x_{\text{tr}}/c \propto Re_c^{-0.2}$; $C_{D,\text{visc}} \propto Re_c^{-0.2}$ (turbulent flat plate) | Ratio of inertial to viscous forces; higher $Re$ delays transition, thins boundary layer, reduces viscous drag but also reduces laminar extent | Match $Re_c$ in wind tunnel to flight value within factor of 2; apply trip strip if test $Re$ too low; check $C_D$ vs $Re$ trend against Blasius/Prandtl–Schlichting correlations | Flight $Re_c \sim 5 \times 10^6$ (GA) to $3 \times 10^7$ (transport); $C_{D,\text{section}} \approx 0.006$–$0.010$ at cruise $C_L$ |
