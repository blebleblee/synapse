# Lesson 2: Stability Theory, Linearization, Lyapunov Methods

## 1. First-Principles Intuition & Invariants

The central question of dynamical systems theory is not merely whether a system evolves, but *how* it evolves relative to distinguished states. A pendulum released from near its downward equilibrium swings back; released from near its upward equilibrium, it falls away catastrophically. Both positions are equilibria in the mathematical sense — the system rests there if placed there exactly — yet their qualitative characters are entirely opposite. Stability theory is the machinery that distinguishes these cases, quantifies the distinction, and ultimately classifies the long-run fate of trajectories.

We work throughout with an autonomous ordinary differential equation on $\mathbb{R}^n$,

$$\dot{x} = f(x), \quad x \in \mathbb{R}^n,$$

where $f : U \subseteq \mathbb{R}^n \to \mathbb{R}^n$ is at least $C^1$ on an open set $U$. A point $x^* \in U$ is an **equilibrium** (or fixed point) if $f(x^*) = 0$, so that the constant function $x(t) = x^*$ satisfies the equation for all time. The geometric picture is a zero of the vector field; the dynamical picture is a trajectory that never moves. The stability question asks what happens to trajectories that start near $x^*$ but not exactly at it.

### Lyapunov's Three Gradations of Stability

The taxonomy originates with Aleksandr Mikhailovich Lyapunov's 1892 doctoral dissertation, one of the foundational documents of modern mathematics. Let $\phi(t, x_0)$ denote the solution of $\dot{x} = f(x)$ with initial condition $x(0) = x_0$, and let $\|\cdot\|$ denote the Euclidean norm.

**Definition (Lyapunov Stability).** The equilibrium $x^*$ is *stable in the sense of Lyapunov* if for every $\varepsilon > 0$ there exists $\delta > 0$ such that

$$\|x_0 - x^*\| < \delta \implies \|\phi(t, x_0) - x^*\| < \varepsilon \quad \text{for all } t \ge 0.$$

This is the dynamical analogue of uniform continuity: small initial perturbations remain small for all future time. The equilibrium neither attracts nor repels; it merely contains perturbations without amplifying them. The undamped harmonic oscillator $\ddot{x} + \omega^2 x = 0$ exhibits exactly this: its orbits are closed ellipses surrounding the origin, so nearby initial conditions stay nearby, but they never return to the origin.

**Definition (Asymptotic Stability).** The equilibrium $x^*$ is *asymptotically stable* if it is Lyapunov stable and there exists $\delta' > 0$ such that

$$\|x_0 - x^*\| < \delta' \implies \lim_{t \to \infty} \phi(t, x_0) = x^*.$$

Asymptotic stability is the practically decisive condition. A damped oscillator with $\ddot{x} + 2\gamma\dot{x} + \omega^2 x = 0$ and $\gamma > 0$ spirals inward to the origin; the origin is asymptotically stable. The key conceptual refinement is that the two conditions — boundedness and convergence — are genuinely independent. Lyapunov stability without convergence is possible (the undamped oscillator), and convergence without Lyapunov stability is also possible in certain degenerate cases, though for autonomous ODEs with continuous $f$, convergence implies stability when the equilibrium is isolated.

**Definition (Instability).** The equilibrium $x^*$ is *unstable* if it is not Lyapunov stable: there exists $\varepsilon > 0$ such that for every $\delta > 0$, some initial condition $x_0$ with $\|x_0 - x^*\| < \delta$ produces a trajectory that eventually exits the $\varepsilon$-ball around $x^*$. The upward equilibrium of a pendulum, the unstable node of $\dot{x} = x$, the saddle point: all are unstable.

### The Basin of Attraction

For an asymptotically stable equilibrium $x^*$, the **basin of attraction** (or domain of attraction) is the set

$$\mathcal{B}(x^*) = \bigl\{ x_0 \in \mathbb{R}^n : \lim_{t \to \infty} \phi(t, x_0) = x^* \bigr\}.$$

This is an open, invariant set containing $x^*$. Its boundary $\partial \mathcal{B}(x^*)$ is itself an invariant set — a repeller or a saddle manifold separating competing basins — and understanding its geometry is one of the deepest problems in applied dynamical systems. When the basin is all of $\mathbb{R}^n$, we say $x^*$ is *globally asymptotically stable*. The logistic equation $\dot{x} = rx(1 - x/K)$ on $\mathbb{R}_{>0}$ has the equilibrium $x^* = K$ with basin $(0, \infty)$; the equilibrium $x^* = 0$ is unstable. The boundary between the two basins in that case is simply $\{0\}$, which is itself an equilibrium. In higher-dimensional systems the basin boundary can be a fractal, a phenomenon with profound implications for the predictability of the system.

---

## 2. Core Architecture & Mechanics

### Linearization and the Jacobian at a Fixed Point

The first systematic tool for analyzing stability near an equilibrium is **linearization**: we approximate the nonlinear vector field $f$ by its first-order Taylor expansion at $x^*$. Since $f(x^*) = 0$, writing $x = x^* + \xi$ for a small perturbation $\xi$ gives

$$\dot{\xi} = f(x^* + \xi) = f(x^*) + Df(x^*)\,\xi + O(\|\xi\|^2) = Df(x^*)\,\xi + O(\|\xi\|^2),$$

where $Df(x^*)$ is the **Jacobian matrix** of $f$ evaluated at $x^*$,

$$Df(x^*)_{ij} = \frac{\partial f_i}{\partial x_j}\bigg|_{x = x^*}.$$

The linearized system is $\dot{\xi} = A\xi$ with $A = Df(x^*)$. This is a constant-coefficient linear ODE whose solution is $\xi(t) = e^{At}\xi_0$, completely determined by the matrix exponential $e^{At}$. The long-time behavior of $e^{At}$ is governed by the eigenvalues of $A$: if all eigenvalues have strictly negative real part, then $e^{At} \to 0$ exponentially; if any eigenvalue has strictly positive real part, solutions of the linearization grow exponentially; if eigenvalues sit on the imaginary axis, the linearized picture is inconclusive about the nonlinear system.

**Definition (Hyperbolic Equilibrium).** The equilibrium $x^*$ of $\dot{x} = f(x)$ is *hyperbolic* if the Jacobian $A = Df(x^*)$ has no eigenvalue with zero real part. Hyperbolic equilibria are the generic case: they persist under small perturbations of $f$, and their stability type is fully determined by the linearization.

The classification of hyperbolic equilibria in the plane is elegant and complete. If both eigenvalues have negative real part, $x^*$ is a **stable node** (real eigenvalues) or **stable spiral** (complex conjugate pair). If both have positive real part, the equilibrium is an **unstable node** or **unstable spiral**. If the eigenvalues are real with opposite signs, the equilibrium is a **saddle**: trajectories converge along the stable manifold (the eigenspace of the negative eigenvalue) and diverge along the unstable manifold (the eigenspace of the positive eigenvalue). These five cases, depicted below in terms of phase portrait topology, exhaust the classification.

```
Eigenvalue Configuration          Phase Portrait Type       Stability
─────────────────────────────────────────────────────────────────────
λ₁ < λ₂ < 0                       Stable node               AS
λ₁ > λ₂ > 0                       Unstable node             Unstable
λ₁ < 0 < λ₂                       Saddle point              Unstable
α ± iβ,  α < 0, β ≠ 0             Stable spiral             AS
α ± iβ,  α > 0, β ≠ 0             Unstable spiral           Unstable
±iβ      (α = 0)                   Center (nonlinear!)       Indeterminate
─────────────────────────────────────────────────────────────────────
AS = Asymptotically Stable
```

The final row is the critical warning: a linearization with purely imaginary eigenvalues tells us almost nothing about the nonlinear system. The nonlinear system might have a center (stable but not asymptotically stable), a stable spiral, or an unstable spiral — all three are compatible with a linear center. This is the domain where Lyapunov's direct method becomes essential.

### The Hartman–Grobman Theorem

The deepest theoretical justification for linearization is the **Hartman–Grobman theorem**, which asserts that near a hyperbolic equilibrium, the nonlinear flow is *topologically equivalent* to the linear flow — not merely similar in some vague qualitative sense, but rigorously equivalent through a homeomorphism of phase space.

**Theorem (Hartman–Grobman).** Let $x^*$ be a hyperbolic equilibrium of $\dot{x} = f(x)$, with $f \in C^1$, and let $A = Df(x^*)$. There exist neighborhoods $V$ of $x^*$ and $W$ of the origin, and a homeomorphism $h : V \to W$, such that $h$ maps orbits of $\dot{x} = f(x)$ in $V$ to orbits of $\dot{\xi} = A\xi$ in $W$, preserving the direction of time.

The homeomorphism $h$ is the agent of **topological conjugacy**: the nonlinear flow $\phi^t$ and the linear flow $e^{At}$ are conjugate in the sense that

$$h \circ \phi^t = e^{At} \circ h$$

on $V$, for all $t$ in the domain of definition. This means every topological feature of the phase portrait — the number of separatrices entering or leaving the equilibrium, whether orbits spiral inward or spiral outward, the existence of stable and unstable manifolds — is faithfully reproduced by the linearization. The theorem does *not* say that $h$ is smooth; in general it is only a homeomorphism, and constructing it explicitly requires either the Banach fixed-point theorem applied to a suitable functional space or the Schoenflies extension theorem.

The proof proceeds by constructing $h$ as the composition of two maps. First, one establishes the existence of local stable and unstable manifolds — smooth invariant submanifolds tangent at $x^*$ to the stable and unstable eigenspaces of $A$ — via the **Stable Manifold Theorem**, whose proof uses the graph transform (a contraction mapping on a space of Lipschitz graphs). Then one builds $h$ by integrating the flow for a fixed time interval and comparing linearized to nonlinear evolution. The key estimate is that the nonlinear remainder $f(x) - Af(x - x^*)$ is $O(\|x - x^*\|^2)$, which is small enough that it does not distort the topological type of the phase portrait near $x^*$.

The structure of the conjugacy near a hyperbolic equilibrium can be visualized as follows, where the arrows indicate the direction of the conjugating map:

```
Nonlinear System                    Linear System
φ(t, x₀) near x*     ←── h ───→   e^{At} ξ₀ near 0
     │                                   │
     │  t-flow                           │  t-flow
     ▼                                   ▼
φ(t+s, x₀) near x*   ←── h ───→   e^{A(t+s)} ξ₀ near 0

Commutativity: h(φ(t, x)) = e^{At} h(x)
```

The significance of Hartman–Grobman for the practitioner is this: for a hyperbolic equilibrium, stability analysis of the nonlinear system reduces entirely to computing eigenvalues of a matrix. One need not solve the nonlinear ODE, construct a Lyapunov function, or perform any further nonlinear analysis. The classification of the linear system is the classification of the nonlinear system, up to continuous deformation of phase space. This reduction from infinite-dimensional function space analysis to finite-dimensional linear algebra is the geometric miracle at the heart of local stability theory.

### Lyapunov's Direct Method: Energy as a Proof

For non-hyperbolic equilibria, and for global stability results that the local linearization cannot provide, we need Lyapunov's **direct method** (also called the second method of Lyapunov). The idea is inspired by energy: if a physical system has a positive-definite energy function that decreases along every trajectory, the system must converge to its minimum-energy state. Lyapunov's insight was to axiomatize and generalize this intuition into a purely geometric condition on scalar functions, independent of physical energy.

**Definition (Lyapunov Function).** Let $x^*$ be an equilibrium of $\dot{x} = f(x)$. A function $V : U \to \mathbb{R}$ on a neighborhood $U$ of $x^*$ is a *Lyapunov function* for the system if:

1. $V$ is continuously differentiable on $U$.
2. $V(x^*) = 0$ and $V(x) > 0$ for all $x \in U \setminus \{x^*\}$ (positive definiteness).
3. The **Lie derivative** $\dot{V}(x) := \nabla V(x) \cdot f(x) \le 0$ for all $x \in U \setminus \{x^*\}$ (negative semi-definiteness along trajectories).

The Lie derivative $\dot{V}$ is the time derivative of $V$ along solutions of the ODE, computed without solving the ODE: by the chain rule,

$$\dot{V}(x) = \frac{d}{dt}\bigl[V(\phi(t,x))\bigr]\bigg|_{t=0} = \sum_{i=1}^n \frac{\partial V}{\partial x_i} f_i(x) = \nabla V(x) \cdot f(x).$$

This is the decisive computational fact: one evaluates the stability condition entirely in terms of $V$, $\nabla V$, and $f$, without integrating a single trajectory.

**Theorem (Lyapunov Stability).** If a Lyapunov function $V$ exists with $\dot{V}(x) \le 0$ on $U \setminus \{x^*\}$, then $x^*$ is Lyapunov stable. If additionally $\dot{V}(x) < 0$ on $U \setminus \{x^*\}$ (strict negative definiteness), then $x^*$ is asymptotically stable.

*Proof (Lyapunov Stability).* Let $\varepsilon > 0$ be given, small enough that $\overline{B_\varepsilon(x^*)} \subset U$. The level set $\{V = c\}$ for small $c > 0$ is a closed curve surrounding $x^*$ contained in $B_\varepsilon(x^*)$ (by continuity of $V$ and $V(x^*)=0$). Let $\Omega_c = \{x : V(x) \le c\}$. Because $\dot{V} \le 0$, the value of $V$ along any trajectory is non-increasing; if the trajectory starts in $\Omega_c$, it remains in $\Omega_c$ for all future time. That is, $\Omega_c$ is **positively invariant**. Choose $\delta$ so that $B_\delta(x^*) \subset \Omega_c$; then any trajectory starting in $B_\delta(x^*)$ stays in $\Omega_c \subset B_\varepsilon(x^*)$, establishing Lyapunov stability. $\square$

*Proof (Asymptotic Stability with $\dot{V} < 0$).* We already have Lyapunov stability, so trajectories from $B_\delta(x^*)$ remain in $\Omega_c$. Suppose for contradiction that some trajectory $\phi(t, x_0)$ does not converge to $x^*$. Since $V(\phi(t, x_0))$ is strictly decreasing and bounded below by $0$, it converges to some limit $\ell \ge 0$. If $\ell > 0$, the trajectory stays in the compact annular region $A = \{\ell \le V(x) \le V(x_0)\} \cap \overline{B_\varepsilon(x^*)}$. On this compact set, $\dot{V}(x) < 0$ attains a maximum $-\mu < 0$, so

$$V(\phi(t, x_0)) \le V(x_0) - \mu t \to -\infty,$$

contradicting $V \ge 0$. Hence $\ell = 0$, which means $V(\phi(t,x_0)) \to 0$, and by positive definiteness of $V$, this implies $\phi(t, x_0) \to x^*$. $\square$

**Theorem (LaSalle's Invariance Principle).** When $\dot{V}$ is only negative semi-definite, asymptotic stability can still be recovered under an additional condition. Let $\Omega_c$ be a compact positively invariant set for $\dot{x} = f(x)$ on which $\dot{V}(x) \le 0$. Define

$$E = \{x \in \Omega_c : \dot{V}(x) = 0\}, \quad M = \text{largest invariant subset of } E.$$

Then every trajectory starting in $\Omega_c$ converges to $M$ as $t \to \infty$.

LaSalle's principle is essential when the Lyapunov function candidate has flat directions along which $\dot{V} = 0$. For example, in a mechanical system with friction-free constraints, the energy may be constant along certain directions; LaSalle extracts convergence nonetheless by identifying the largest invariant subset of the zero set of $\dot{V}$.

### Constructing Lyapunov Functions: The Practitioner's Craft

The principal challenge with Lyapunov's method is that there is no universal algorithm for constructing $V$. This is not merely a practical inconvenience: it is essentially unavoidable, since the existence of a Lyapunov function is equivalent to asymptotic stability by the converse Lyapunov theorems (due to Massera and Kurzweil), so a constructive algorithm for $V$ would be a constructive algorithm for deciding asymptotic stability, which is undecidable in general. Nevertheless, several powerful strategies exist.

The most direct strategy for mechanical systems is **physical energy**. For the damped pendulum $\ddot{\theta} + \gamma\dot{\theta} + \sin\theta = 0$ (with $\gamma > 0$, working near $\theta = 0, \dot{\theta} = 0$), write the system as $\dot{\theta} = \omega$, $\dot{\omega} = -\gamma\omega - \sin\theta$. The natural energy is

$$V(\theta, \omega) = \frac{1}{2}\omega^2 + (1 - \cos\theta),$$

which is positive definite near the origin (since $1 - \cos\theta \ge 0$ with equality only at $\theta = 0$). Computing the Lie derivative:

$$\dot{V} = \omega\dot{\omega} + \sin\theta \cdot \dot{\theta} = \omega(-\gamma\omega - \sin\theta) + \sin\theta \cdot \omega = -\gamma\omega^2.$$

This is only negative semi-definite, since $\dot{V} = 0$ whenever $\omega = 0$. LaSalle's principle applies: the set $E = \{\omega = 0\}$, and the largest invariant subset of $E$ is found by substituting $\omega = 0$, $\dot{\omega} = 0$ into the equation of motion, giving $\sin\theta = 0$, so $\theta = 0$ in a neighborhood of the origin. Thus $M = \{(0,0)\}$, and the origin is asymptotically stable.

For nonlinear systems without a physical interpretation, a powerful systematic approach is to try **quadratic Lyapunov functions** $V(x) = x^T P x$ with $P$ a positive definite symmetric matrix, and require $\dot{V}(x) = x^T(A^T P + PA)x < 0$. This reduces to the **Lyapunov equation**

$$A^T P + PA = -Q$$

for a chosen positive definite matrix $Q$ (often taken as $Q = I$). A classical theorem states: $A$ is Hurwitz (all eigenvalues have negative real part) if and only if the Lyapunov equation has a unique positive definite solution $P$ for every positive definite $Q$. This gives a direct algebraic method: solve $A^TP + PA = -I$ for $P$; if $P > 0$, the origin is asymptotically stable and $V(x) = x^TPx$ is an explicit Lyapunov function. The solution is

$$P = \int_0^\infty e^{A^T t} Q\, e^{At}\, dt,$$

a formula which converges whenever $A$ is Hurwitz and provides both the proof and an explicit construction.

For a concrete worked example, take the system

$$\dot{x}_1 = -x_1 + x_1 x_2, \quad \dot{x}_2 = -x_2,$$

with equilibrium at the origin. The Jacobian at the origin is $A = \begin{pmatrix} -1 & 0 \\ 0 & -1 \end{pmatrix}$, which has eigenvalues $-1, -1$: both negative. The linearization predicts asymptotic stability. We confirm this with a Lyapunov function $V(x_1, x_2) = x_1^2 + x_2^2$. Then

$$\dot{V} = 2x_1\dot{x}_1 + 2x_2\dot{x}_2 = 2x_1(-x_1 + x_1 x_2) + 2x_2(-x_2) = -2x_1^2 + 2x_1^2 x_2 - 2x_2^2.$$

Rewriting: $\dot{V} = -2x_1^2(1 - x_2) - 2x_2^2$. In the region $|x_2| < 1/2$, we have $1 - x_2 > 1/2$, so

$$\dot{V} \le -2 \cdot \frac{1}{2} x_1^2 - 2x_2^2 = -(x_1^2 + 2x_2^2) < 0.$$

This confirms asymptotic stability on the neighborhood $\{|x_2| < 1/2\}$, and the sublevel sets $\{V \le c\}$ contained in this region are positively invariant and lie within the basin of attraction.

---

## 3. High-Performance Optimization & Failure Modes

### Estimating the Basin of Attraction

The global question — how large is $\mathcal{B}(x^*)$? — is answered by Lyapunov methods through sublevel set analysis. If $V$ is a Lyapunov function with $\dot{V} < 0$ on $\{V \le c\} \setminus \{x^*\}$ and the sublevel set $\Omega_c = \{x : V(x) \le c\}$ is compact and contains no other equilibria, then $\Omega_c \subset \mathcal{B}(x^*)$. The maximal such $c$ before $\Omega_c$ either hits another equilibrium or becomes unbounded gives the best estimate of the basin available from the particular choice of $V$.

The practical workflow is therefore: find a Lyapunov function $V$, compute $\dot{V}$, determine the region $\{x : \dot{V}(x) < 0\}$, and then find the largest sublevel set $\Omega_c$ entirely contained in that region. This can be cast as an optimization problem: maximize $c$ subject to $\Omega_c \subset \{\dot{V} < 0\}$, which for polynomial $f$ and polynomial $V$ can be addressed using sum-of-squares (SOS) decompositions and semidefinite programming — a modern computational approach that transforms the search for Lyapunov functions into a convex optimization.

The key limitation is that any fixed $V$ gives only an *inner estimate* of $\mathcal{B}(x^*)$; the true basin may be considerably larger. The boundary $\partial\mathcal{B}(x^*)$ is the stable manifold of an unstable equilibrium or limit cycle forming the boundary of attraction, and reconstructing this boundary exactly requires either specialized numerical continuation methods or deeper theoretical tools such as Zubov's equation, which characterizes the exact basin of attraction as a sublevel set of the solution to a first-order PDE.

### Topological Conjugacy and Structural Stability

The concept of topological conjugacy, introduced in the Hartman–Grobman theorem, extends beyond fixed points into a global theory. Two vector fields $f$ and $g$ on $\mathbb{R}^n$ are **topologically equivalent** if there exists a homeomorphism $h$ of $\mathbb{R}^n$ mapping orbits of $\dot{x} = f(x)$ to orbits of $\dot{x} = g(x)$ while preserving the direction of time. A vector field $f$ is **structurally stable** if every $C^1$-perturbation $g$ with $\|g - f\|_{C^1}$ small is topologically equivalent to $f$.

The Peixoto–Kupka–Smale theorem characterizes structurally stable vector fields on compact surfaces: they are open and dense in the $C^1$ topology, and they are precisely those with finitely many hyperbolic equilibria, finitely many hyperbolic periodic orbits, and no saddle connections (trajectories connecting saddle points). This theorem is not merely a technical result; it says that the "generic" dynamical system is one whose qualitative behavior is robust to perturbation, and that the exceptional, non-generic cases are precisely those where new orbit topology can appear under arbitrarily small changes.

For practitioners performing qualitative analysis, structural stability provides a crucial sanity check. If a system has an equilibrium with a purely imaginary eigenvalue pair, it lies on a bifurcation boundary: the slightest perturbation can convert a center into a stable spiral or an unstable spiral. Any conclusion drawn about a center without a fully nonlinear analysis is therefore unreliable as a prediction about physically realizable systems, since no physical system is known to exactly infinite precision.

### The Failure Mode of Linearization: Non-Hyperbolic Equilibria

The most consequential failure mode in stability analysis is treating a non-hyperbolic equilibrium as though the linear analysis were sufficient. Consider the scalar systems $\dot{x} = -x^3$ and $\dot{x} = x^3$, both with equilibrium at $x = 0$, both with Jacobian $A = Df(0) = 0$. The linearization $\dot{\xi} = 0$ gives a line of equilibria: every point is an equilibrium of the linear system. But the two nonlinear systems have diametrically opposite stabilities: $\dot{x} = -x^3$ has an asymptotically stable origin (since $\dot{V} = -x^4 \cdot 2x / (2x) $... more carefully, with $V = x^2/2$, $\dot{V} = x \cdot (-x^3) = -x^4 < 0$ for $x \ne 0$), while $\dot{x} = x^3$ has an unstable origin. The linearization, returning the zero matrix, cannot distinguish these cases.

In higher dimensions, the situation is richer. Consider a system in $\mathbb{R}^2$ where $A = Df(0)$ has eigenvalues $0$ and $-1$. The linear system has a line of equilibria along the zero eigenspace, and all initial conditions converge along the stable eigenspace to this line. The nonlinear system may have a unique equilibrium at the origin (if the nonlinear terms break the line of linear equilibria), and the origin might be stable or unstable depending entirely on the higher-order behavior along the center manifold. The **center manifold theorem** provides the right framework: near a non-hyperbolic equilibrium, there exists an invariant smooth manifold tangent to the center eigenspace (the eigenspace of eigenvalues with zero real part), and the stability of the full system is determined by the dynamics restricted to this manifold. Reducing to the center manifold turns an $n$-dimensional problem into a $k$-dimensional one, where $k$ is the dimension of the center eigenspace.

**Example.** Consider $\dot{x}_1 = x_1 x_2$, $\dot{x}_2 = -x_2 + x_1^2$, with equilibrium at the origin. The Jacobian is $A = \begin{pmatrix} 0 & 0 \\ 0 & -1 \end{pmatrix}$: one zero eigenvalue, one eigenvalue $-1$. The center eigenspace is the $x_1$-axis. The center manifold is a curve tangent to the $x_1$-axis, expressed as $x_2 = h(x_1)$ for a smooth function $h$ with $h(0) = 0$, $h'(0) = 0$. Substituting $x_2 = h(x_1)$ into the ODE for $x_2$ and using $\dot{x}_2 = h'(x_1)\dot{x}_1$:

$$h'(x_1) \cdot x_1 h(x_1) = -h(x_1) + x_1^2.$$

We seek $h(x_1) = ax_1^2 + O(x_1^3)$. At leading order: $a \cdot 0 \cdot x_1 h(x_1) = -ax_1^2 + x_1^2$, giving $a = 1$. So $h(x_1) = x_1^2 + O(x_1^3)$, and the center manifold equation is $x_2 = x_1^2 + O(x_1^3)$. The reduced dynamics on the center manifold are

$$\dot{x}_1 = x_1 h(x_1) = x_1 \cdot x_1^2 + O(x_1^4) = x_1^3 + O(x_1^4).$$

Since $\dot{x}_1 = x_1^3 + O(x_1^4)$ has the same sign as $x_1$ for small $x_1 \ne 0$, the origin is **unstable** — despite the $-1$ eigenvalue in the transverse direction pulling trajectories toward the center manifold. The instability along the center manifold overcomes the stability in the transverse direction.

### Proving Global Asymptotic Stability: Radially Unbounded Lyapunov Functions

For global results, the sublevel-set argument requires that $\Omega_c$ be compact for all $c$, which is guaranteed by the **radial unboundedness** condition $V(x) \to \infty$ as $\|x\| \to \infty$. A Lyapunov function satisfying this condition is called **proper** or **radially unbounded**, and together with $\dot{V}(x) < 0$ for all $x \ne x^*$, it implies global asymptotic stability.

**Theorem (Global Asymptotic Stability).** Suppose $V : \mathbb{R}^n \to \mathbb{R}$ is $C^1$, positive definite, radially unbounded ($V(x) \to \infty$ as $\|x\| \to \infty$), and satisfies $\dot{V}(x) < 0$ for all $x \ne x^*$. Then $x^*$ is globally asymptotically stable.

The proof is straightforward: the radially unbounded condition ensures every sublevel set $\Omega_c$ is compact, hence positively invariant (since $\dot{V} < 0$ prevents trajectories from crossing $\partial\Omega_c$ outward). Every trajectory thus lies in some $\Omega_c$ and converges to $x^*$ by the argument of the asymptotic stability theorem. The basin of attraction is all of $\mathbb{R}^n$.

The failure mode here is subtle. Many natural Lyapunov functions — in particular, logarithmic storage functions arising from the Kullback–Leibler divergence in information-geometric analysis, or barrier-type functions for constrained systems — are not radially unbounded, and cannot give global conclusions without additional work. Moreover, global asymptotic stability is a strong hypothesis that need not hold for nonlinear systems even when local stability is clear: consider $\dot{x} = -x + x^3$, whose origin is locally asymptotically stable (the linearization gives $\dot{\xi} = -\xi$) but whose basin of attraction is only $(-1, 1)$, since trajectories starting with $|x| > 1$ blow up in finite time. The quadratic candidate $V = x^2/2$ gives $\dot{V} = x(-x + x^3) = -x^2 + x^4 = x^2(x^2 - 1)$, which is positive for $|x| > 1$: the sublevel set argument correctly bounds the basin at $|x| < 1$, but fails to yield a global result, which is as it should be.

### Structural Summary: The Hierarchy of Tools

The tools developed in this lesson form a natural hierarchy ordered by power and computational cost. The first resort is always the **Jacobian analysis**: compute $A = Df(x^*)$, extract eigenvalues, and invoke Hartman–Grobman when $x^*$ is hyperbolic. This costs $O(n^3)$ arithmetic operations (eigenvalue computation) and delivers a complete local topological characterization. When $x^*$ is non-hyperbolic, one reduces to the **center manifold**, computing the invariant manifold as a formal power series and studying the reduced system, whose dimension equals the number of critical eigenvalues. When local analysis is insufficient and global or quantitative stability information is needed, one turns to **Lyapunov's direct method**, accepting the burden of constructing $V$ while gaining in return the ability to certify stability without solving the ODE, to bound the basin of attraction, and to handle non-hyperbolic and globally nonlinear behavior. LaSalle's invariance principle then extends the method from the strictly decreasing case to systems with conserved quantities or partial dissipation.

The interplay between these tools — linearization giving local topology, center manifold reducing dimension, Lyapunov functions certifying stability, LaSalle extracting long-run behavior — constitutes the foundational methodology that every subsequent topic in dynamical systems, from bifurcation theory to Hamiltonian mechanics to topological dynamics, inherits and builds upon.
