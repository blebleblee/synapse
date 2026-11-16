# Lesson 4: Qualitative Theory — Phase Portraits, Stability, Invariant Sets

## 1. First-Principles Intuition & Invariants

The central ambition of the qualitative theory of differential equations is a profound shift in posture: rather than searching for explicit closed-form solutions, which are unavailable for most nonlinear systems, we ask what the solution curves *look like* in aggregate, how they are organized in state space, and what long-run behaviors are geometrically inevitable. This program, initiated by Henri Poincaré in his 1881–1886 memoirs on curves defined by differential equations and deepened by Aleksandr Lyapunov's 1892 doctoral thesis, transforms the analytic problem of integration into a geometric and topological one. The payoff is extraordinary: we can often determine whether a system is stable, whether it admits periodic orbits, and how trajectories are asymptotically sorted, all without knowing a single trajectory in closed form.

We work throughout with an autonomous system in the plane, meaning one of the form

$$\dot{x} = f(x, y), \qquad \dot{y} = g(x, y),$$

where $f, g : U \subseteq \mathbb{R}^2 \to \mathbb{R}$ are at least $C^1$ on an open domain $U$, and the right-hand side carries no explicit dependence on the independent variable $t$. The autonomy condition is the structural key: it implies that if $\varphi(t)$ is a solution, then so is any time-translate $\varphi(t + c)$. Consequently, the solution curves in the $(x, y)$-plane, which we call **orbits** or **trajectories**, are well-defined as geometric objects independent of initial time. The $(x, y)$-plane equipped with the directed field of these orbits is the **phase plane**, and a complete depiction of the orbit structure is a **phase portrait**.

The phase portrait is partitioned by the dynamics in a canonical way. An **equilibrium point** (also called a fixed point or critical point) is a point $(x^*, y^*)$ satisfying $f(x^*, y^*) = 0$ and $g(x^*, y^*) = 0$ simultaneously. At such a point, the velocity vector vanishes; the system sits still, making equilibria the structural skeleton around which all other orbits are organized. A **periodic orbit** is a nontrivial closed curve $\Gamma$ traversed in finite time $T > 0$, so that $\varphi(t + T) = \varphi(t)$ for all $t$. Between equilibria and periodic orbits, the remaining orbits are heteroclinic connections (connecting distinct equilibria), homoclinic loops (departing and returning to the same equilibrium), or unbounded orbits escaping to infinity.

The concept of an **invariant set** formalizes the notion of a region from which no trajectory escapes. A set $S \subseteq \mathbb{R}^2$ is **positively invariant** under the flow $\phi_t$ if $\phi_t(S) \subseteq S$ for all $t \ge 0$; it is **negatively invariant** if the same holds for $t \le 0$; and it is **invariant** if both conditions hold. Every orbit, every equilibrium, every periodic orbit, every stable and unstable manifold, and every $\omega$-limit set is an invariant set. The concept is powerful precisely because it is preserved by the flow without requiring explicit knowledge of that flow.

The **$\omega$-limit set** $\omega(p)$ of a point $p$ captures the asymptotic destination of the trajectory through $p$: it is the set of all accumulation points of the sequence $\phi_{t_n}(p)$ for some $t_n \to +\infty$. Dually, the $\alpha$-limit set $\alpha(p)$ captures backward-time behavior. These sets are always closed, invariant, and connected when the trajectory is bounded — a fact whose proof combines the invariance of limit sets with the connectedness of the trajectory's closure. They are the natural targets of the qualitative theory, and classifying them is the central problem the Poincaré–Bendixson theorem solves.

---

## 2. Core Architecture & Mechanics

### 2.1 Linearization and the Jacobian at Equilibria

The first-order tool for understanding the local geometry near an equilibrium is linearization. Let $(x^*, y^*)$ be an equilibrium and write $\mathbf{x} = (x, y)^T$, $\mathbf{x}^* = (x^*, y^*)^T$. Setting $\mathbf{u} = \mathbf{x} - \mathbf{x}^*$, a Taylor expansion of the vector field $F = (f, g)^T$ around $\mathbf{x}^*$ gives

$$\dot{\mathbf{u}} = J(\mathbf{x}^*)\,\mathbf{u} + O(\|\mathbf{u}\|^2),$$

where the **Jacobian matrix** evaluated at the equilibrium is

$$J = J(\mathbf{x}^*) = \begin{pmatrix} \partial f/\partial x & \partial f/\partial y \\ \partial g/\partial x & \partial g/\partial y \end{pmatrix}\bigg|_{(x^*, y^*)}.$$

The linearized system $\dot{\mathbf{u}} = J\mathbf{u}$ is a constant-coefficient linear ODE whose solution is $\mathbf{u}(t) = e^{Jt}\mathbf{u}(0)$, and its qualitative behavior is completely determined by the eigenvalues $\lambda_1, \lambda_2$ of $J$. The characteristic polynomial of the $2 \times 2$ matrix $J$ is

$$\lambda^2 - \text{tr}(J)\,\lambda + \det(J) = 0,$$

so

$$\lambda_{1,2} = \frac{\text{tr}(J) \pm \sqrt{\text{tr}(J)^2 - 4\det(J)}}{2}.$$

The **Hartman–Grobman theorem** then provides the foundational justification for reading nonlinear behavior from linear data: if $J$ has no eigenvalue with zero real part (i.e., the equilibrium is **hyperbolic**), then in a neighborhood of $(x^*, y^*)$ the nonlinear flow $\phi_t$ is topologically conjugate to the linear flow $e^{Jt}$. The phase portrait near a hyperbolic equilibrium is therefore a topological copy of the linear portrait, and the linearization is not merely an approximation but a faithful local model.

The classification of equilibria proceeds directly from the eigenvalue geometry. When $\det(J) > 0$ and the discriminant $\text{tr}(J)^2 - 4\det(J) < 0$, the eigenvalues are complex conjugates $\lambda = \alpha \pm i\beta$ with $\beta \neq 0$. If $\alpha < 0$, the equilibrium is a **stable spiral**: trajectories wind inward toward $(x^*, y^*)$ as $t \to +\infty$. If $\alpha > 0$, it is an **unstable spiral**: trajectories unwind outward. The angular velocity of the spiraling is governed by $\beta$. When $\alpha = 0$ exactly, the linear system exhibits a **center**, with purely imaginary eigenvalues $\pm i\beta$ and closed elliptical orbits; however, the center is not hyperbolic, so Hartman–Grobman does not apply, and the nonlinear system may exhibit a true center, a stable spiral, or an unstable spiral depending on the higher-order terms — a subtlety that Lyapunov theory must resolve.

When the eigenvalues are real and distinct, $\lambda_1 \neq \lambda_2 \in \mathbb{R}$, the equilibrium is a **node** if both have the same sign, or a **saddle** if they have opposite signs. A **stable node** has $\lambda_1 < \lambda_2 < 0$: all trajectories approach $(x^*, y^*)$ tangentially to the eigenvector associated with $\lambda_2$ (the slower eigenvalue). An **unstable node** has $0 < \lambda_1 < \lambda_2$. A **saddle** has $\lambda_1 < 0 < \lambda_2$: along the eigenvector of $\lambda_1$ there is a stable manifold (trajectories approaching the equilibrium), and along the eigenvector of $\lambda_2$ there is an unstable manifold (trajectories departing), creating the characteristic X-shaped portrait that dominates the phase plane near a saddle. When $\lambda_1 = \lambda_2 = \lambda$ with $J$ not diagonalizable (a repeated eigenvalue with a single eigenvector), the equilibrium is an **improper node**, also called a **star node** in the degenerate diagonalizable case.

The following diagram organizes the classification by the trace-determinant plane:

```
det(J)
^
| (stable spiral) | (unstable spiral)
| tr<0, Δ<0 | tr>0, Δ<0
| |
|---stable-node---+---unstable-node-----> tr(J)
| tr<0, Δ>0 | tr>0, Δ>0
|                 |
| saddle: det(J) < 0 (below the tr-axis)
|
Parabola: Δ = tr^2 - 4·det = 0 (boundary: improper nodes)
Center line: tr(J) = 0, det > 0 (linear centers / nonlinear TBD)
```

The saddle condition $\det(J) < 0$ means the eigenvalues have opposite signs regardless of the trace value, placing saddles entirely in the lower half of the trace-determinant plane.

### 2.2 Worked Example: The Nonlinear Pendulum

The undamped pendulum is governed by

$$\ddot{\theta} + \frac{g}{L}\sin\theta = 0,$$

which as a first-order planar system becomes

$$\dot{\theta} = \omega, \qquad \dot{\omega} = -\frac{g}{L}\sin\theta.$$

Setting $f(\theta, \omega) = \omega$ and $g(\theta, \omega) = -(g/L)\sin\theta$, the equilibria satisfy $\omega = 0$ and $\sin\theta = 0$, so $(x^*, \omega^*) = (n\pi, 0)$ for $n \in \mathbb{Z}$. The Jacobian is

$$J = \begin{pmatrix} 0 & 1 \\ -\frac{g}{L}\cos\theta & 0 \end{pmatrix}.$$

At $\theta = 0$ (downward rest): $J = \bigl(\begin{smallmatrix} 0 & 1 \\ -g/L & 0 \end{smallmatrix}\bigr)$, with $\text{tr}(J) = 0$ and $\det(J) = g/L > 0$. The eigenvalues are $\pm i\sqrt{g/L}$, purely imaginary, so the linearization is a center. The nonlinear system is in fact a true center at $\theta = 0$ (which we confirm below via a conserved energy), and the closed orbits correspond to oscillations of the pendulum.

At $\theta = \pi$ (upward balance): $J = \bigl(\begin{smallmatrix} 0 & 1 \\ g/L & 0 \end{smallmatrix}\bigr)$, with $\det(J) = -g/L < 0$. The eigenvalues are $\pm\sqrt{g/L}$, real with opposite signs. This is a saddle, confirming the physical intuition that the inverted pendulum is unstable. The stable and unstable manifolds of this saddle appear in the phase portrait as the separatrices that bound the region of oscillatory (bounded) motion.

### 2.3 Lyapunov Stability and Lyapunov Functions

Hartman–Grobman handles hyperbolic equilibria, but non-hyperbolic equilibria and global stability questions require a different instrument. Lyapunov's direct method (also called the second method of Lyapunov) provides a way to certify stability without integrating the system.

**Definition (Lyapunov Stability).** An equilibrium $\mathbf{x}^*$ of $\dot{\mathbf{x}} = F(\mathbf{x})$ is **Lyapunov stable** if for every $\varepsilon > 0$ there exists $\delta > 0$ such that $\|\mathbf{x}(0) - \mathbf{x}^*\| < \delta$ implies $\|\mathbf{x}(t) - \mathbf{x}^*\| < \varepsilon$ for all $t \ge 0$. It is **asymptotically stable** if it is Lyapunov stable and there exists $\delta' > 0$ such that $\|\mathbf{x}(0) - \mathbf{x}^*\| < \delta'$ implies $\mathbf{x}(t) \to \mathbf{x}^*$ as $t \to +\infty$. It is **unstable** if Lyapunov stability fails.

A **Lyapunov function** for the equilibrium $\mathbf{x}^*$ on an open set $U \ni \mathbf{x}^*$ is a continuously differentiable function $V : U \to \mathbb{R}$ satisfying:

$$V(\mathbf{x}^*) = 0, \quad V(\mathbf{x}) > 0 \text{ for all } \mathbf{x} \in U \setminus \{\mathbf{x}^*\},$$

and whose **orbital derivative** (Lie derivative along the vector field $F$) satisfies

$$\dot{V}(\mathbf{x}) := \nabla V(\mathbf{x}) \cdot F(\mathbf{x}) = \frac{\partial V}{\partial x}f + \frac{\partial V}{\partial y}g \le 0 \quad \text{on } U \setminus \{\mathbf{x}^*\}.$$

**Lyapunov's Stability Theorem.** If such a $V$ exists with $\dot{V} \le 0$ on $U \setminus \{\mathbf{x}^*\}$, then $\mathbf{x}^*$ is Lyapunov stable. If moreover $\dot{V}(\mathbf{x}) < 0$ on $U \setminus \{\mathbf{x}^*\}$, then $\mathbf{x}^*$ is asymptotically stable.

The proof is elegant and geometric. Because $V$ is positive definite and continuous, its level sets $\{V = c\}$ form a family of closed curves enclosing $\mathbf{x}^*$ for small $c > 0$. The condition $\dot{V} \le 0$ means $V$ is non-increasing along orbits, so a trajectory beginning inside $\{V \le c\}$ cannot cross outward to $\{V > c\}$: the level sets are positively invariant. This traps the trajectory within any prescribed $\varepsilon$-neighborhood of $\mathbf{x}^*$, establishing Lyapunov stability. If $\dot{V} < 0$, then $V(\phi_t(p))$ is strictly decreasing along every trajectory and bounded below by $0$; the limit must exist, and one shows via the LaSalle invariance principle (see below) that this limit can only be $0$, forcing $\phi_t(p) \to \mathbf{x}^*$.

Returning to the pendulum, the total mechanical energy

$$V(\theta, \omega) = \frac{1}{2}\omega^2 + \frac{g}{L}(1 - \cos\theta)$$

is a natural Lyapunov function. We have $V(0, 0) = 0$, $V > 0$ for $(\theta, \omega) \neq (0, 0)$ near the origin (since $1 - \cos\theta \ge 0$ with equality only at $\theta = 0$), and

$$\dot{V} = \omega\dot{\omega} + \frac{g}{L}\sin\theta\cdot\dot{\theta} = \omega\left(-\frac{g}{L}\sin\theta\right) + \frac{g}{L}\sin\theta\cdot\omega = 0.$$

The orbital derivative vanishes identically, confirming that $V$ is a first integral (conservation of energy), that every level set is an orbit (a closed curve for small energy), and that the origin is Lyapunov stable but not asymptotically stable — which matches the center classification from linearization and confirms what linearization could only suggest.

### 2.4 LaSalle's Invariance Principle

Lyapunov's theorem in its basic form requires $\dot{V} < 0$ strictly for asymptotic stability, which is often too strong. Many physically natural Lyapunov functions, like the energy of a damped pendulum, satisfy $\dot{V} \le 0$ with $\dot{V} = 0$ on a set larger than just the equilibrium. LaSalle's invariance principle resolves this.

**LaSalle's Invariance Principle.** Let $\Omega$ be a compact positively invariant set for $\dot{\mathbf{x}} = F(\mathbf{x})$, and let $V : \Omega \to \mathbb{R}$ be $C^1$ with $\dot{V}(\mathbf{x}) \le 0$ on $\Omega$. Define the set $E = \{\mathbf{x} \in \Omega : \dot{V}(\mathbf{x}) = 0\}$, and let $M$ be the largest invariant subset of $E$. Then every trajectory beginning in $\Omega$ satisfies $\phi_t(\mathbf{x}) \to M$ as $t \to +\infty$.

The proof proceeds as follows. Because $\dot{V} \le 0$, the function $t \mapsto V(\phi_t(\mathbf{x}))$ is non-increasing and bounded below on the compact set $\Omega$, so it converges to some $c \ge 0$. The $\omega$-limit set $\omega(\mathbf{x})$ is nonempty (by compactness and the Bolzano–Weierstrass theorem), is contained in $\Omega$, and is invariant. For any $\mathbf{y} \in \omega(\mathbf{x})$, the entire orbit through $\mathbf{y}$ lies in $\omega(\mathbf{x})$, and $V$ is constant equal to $c$ on $\omega(\mathbf{x})$ (since $V(\phi_t(\mathbf{y}))$ is simultaneously non-increasing and equal to $c$ at all limit points). Thus $\dot{V} = 0$ on $\omega(\mathbf{x})$, so $\omega(\mathbf{x}) \subseteq E$. Since $\omega(\mathbf{x})$ is invariant and contained in $E$, it is contained in $M$. Therefore $\phi_t(\mathbf{x}) \to M$.

For the **damped pendulum** $\dot{\theta} = \omega$, $\dot{\omega} = -(g/L)\sin\theta - b\omega$ with damping $b > 0$, the energy function gives

$$\dot{V} = -b\omega^2 \le 0,$$

which vanishes on the set $E = \{\omega = 0\}$. The largest invariant subset of $E$ within a suitable compact positively invariant region is the equilibrium $\{(0, 0)\}$ alone, since any trajectory with $\omega = 0$ identically must also have $\dot{\omega} = -(g/L)\sin\theta = 0$, forcing $\theta = 0$. LaSalle therefore guarantees asymptotic stability of the downward equilibrium, a conclusion that the strict-negativity condition on $\dot{V}$ could not reach directly.

### 2.5 Stable, Unstable, and Center Manifolds

Near a hyperbolic equilibrium, the eigenspaces of $J$ extend to invariant manifolds of the nonlinear system. This is the content of the **Stable Manifold Theorem** (also called the Hadamard–Perron theorem), one of the central structural results in the geometric theory of ODEs.

Let $\mathbf{x}^*$ be an equilibrium of $\dot{\mathbf{x}} = F(\mathbf{x})$ with $F \in C^r$, $r \ge 1$. Suppose $J = DF(\mathbf{x}^*)$ has $n_s$ eigenvalues with negative real part, $n_u$ eigenvalues with positive real part, and $n_c = n - n_s - n_u$ eigenvalues with zero real part. The corresponding generalized eigenspaces are $E^s$, $E^u$, and $E^c$.

**Stable Manifold Theorem.** There exist $C^r$ manifolds $W^s_{\text{loc}}(\mathbf{x}^*)$ and $W^u_{\text{loc}}(\mathbf{x}^*)$, tangent at $\mathbf{x}^*$ to $E^s$ and $E^u$ respectively, satisfying:

$$\phi_t(\mathbf{x}) \to \mathbf{x}^* \text{ as } t \to +\infty \text{ for all } \mathbf{x} \in W^s_{\text{loc}}(\mathbf{x}^*),$$
$$\phi_t(\mathbf{x}) \to \mathbf{x}^* \text{ as } t \to -\infty \text{ for all } \mathbf{x} \in W^u_{\text{loc}}(\mathbf{x}^*).$$

The dimensions satisfy $\dim W^s = n_s$ and $\dim W^u = n_u$. These manifolds are as smooth as the vector field and are unique in the sense that any trajectory remaining near $\mathbf{x}^*$ for all future (respectively past) time must lie on $W^s$ (respectively $W^u$).

In the planar case with a saddle, $n_s = n_u = 1$ and $n_c = 0$. The stable manifold $W^s$ is a smooth curve tangent to the stable eigenvector, and $W^u$ is a smooth curve tangent to the unstable eigenvector. These four branches of $W^s$ and $W^u$ (two for each manifold, one on each side of the saddle) are the **separatrices** that organize the global phase portrait. Trajectories not on these curves follow hyperbola-like paths that asymptotically shadow the unstable manifold as $t \to +\infty$ and the stable manifold as $t \to -\infty$.

When $n_c > 0$ (non-hyperbolic equilibrium), one also has a **center manifold** $W^c_{\text{loc}}(\mathbf{x}^*)$, tangent to $E^c$, whose existence is guaranteed by the Center Manifold Theorem. The center manifold need only be $C^r$ for finite $r$, and the dynamics on it determine the stability type of the equilibrium, reducing the analysis to a lower-dimensional system. For the planar problem with $J$ having purely imaginary eigenvalues, the entire plane is the center manifold, and stability is determined by the nature of the nonlinear terms — specifically by the first Lyapunov coefficient, whose vanishing or sign determines whether the equilibrium is a stable spiral, unstable spiral, or true center in the nonlinear system.

### 2.6 The Poincaré–Bendixson Theorem

Having classified equilibria and their associated manifolds, we turn to the global question: what are the possible $\omega$-limit sets in the plane? The Poincaré–Bendixson theorem provides a complete answer, made possible by the topological rigidity of the plane relative to higher-dimensional spaces.

**Poincaré–Bendixson Theorem.** Let $F \in C^1$ on an open set $U \subseteq \mathbb{R}^2$, and let $\phi_t$ be the flow. Suppose $\Omega$ is a compact positively invariant set containing only finitely many equilibria. For any $p \in \Omega$, the $\omega$-limit set $\omega(p)$ is one of:

1. A single equilibrium.
2. A single periodic orbit (limit cycle).
3. A collection of equilibria and orbits connecting them (a **homoclinic** or **heteroclinic** cycle).

The proof hinges on the Jordan curve theorem: any simple closed curve in $\mathbb{R}^2$ divides the plane into exactly two connected components. This topological fact prevents an orbit in the plane from recrossing any transversal segment more than once in the same direction, which is the key geometric constraint that limits $\omega$-limit set structure. In $\mathbb{R}^3$ and above, this constraint is absent, and $\omega$-limit sets can be strange attractors — fractal geometric objects supporting chaotic dynamics — a possibility the Jordan curve theorem structurally forecloses in $\mathbb{R}^2$.

The theorem's constructive power is usually exercised via the following strategy. One identifies a compact positively invariant region $\Omega$ (typically by constructing a Lyapunov-like bounding function or by physical energy arguments), verifies that $\Omega$ contains no equilibria (or that all equilibria in $\Omega$ are unstable), and concludes by Poincaré–Bendixson that $\Omega$ must contain at least one periodic orbit — a limit cycle. This is the standard existence proof for limit cycles in nonlinear oscillator theory.

**Corollary (Bendixson's Criterion).** If $\text{div}(F) = \partial f/\partial x + \partial g/\partial y$ does not change sign on a simply connected region $D$ (and is not identically zero), then there is no periodic orbit or homoclinic/heteroclinic cycle in $D$.

The proof follows immediately from Green's theorem: if $\Gamma$ were a closed orbit enclosing region $R \subseteq D$, then

$$\oint_\Gamma (f\,dy - g\,dx) = \iint_R \left(\frac{\partial f}{\partial x} + \frac{\partial g}{\partial y}\right) dA \neq 0,$$

but the left side equals $\oint_\Gamma F \cdot \mathbf{n}\,ds$ where $\mathbf{n}$ is the outward normal, which is zero since the orbit is tangent to $F$ (not normal to it) — a contradiction that collapses when one writes the line integral correctly as $\oint_\Gamma F \cdot \mathbf{n}\,ds = \oint_\Gamma (f\dot{y} - g\dot{x})/|F|\,ds$ evaluated along the orbit where $(\dot{x}, \dot{y}) = (f, g)$, giving the integral of $f^2 + g^2 > 0$, a nonzero quantity. More cleanly: along any periodic orbit $\Gamma$ bounding region $R$, the divergence theorem gives $\oint_\Gamma F \cdot \mathbf{n}\,ds = \iint_R \text{div}(F)\,dA$, and since the orbit is tangent to $F$ we have $F \cdot \mathbf{n} = 0$ on $\Gamma$, so the left side is zero. If $\text{div}(F)$ does not change sign, the right side is nonzero, a contradiction.

### 2.7 Limit Cycles: Existence, Stability, and the Hopf Bifurcation Precursor

A **limit cycle** is an isolated periodic orbit $\Gamma$: a periodic orbit such that no nearby orbit is periodic. This isolation distinguishes limit cycles from the continuum of closed orbits surrounding a center. A limit cycle is **stable** (attracting) if nearby orbits spiral toward $\Gamma$ as $t \to +\infty$, **unstable** (repelling) if they spiral away, and **semi-stable** if they approach from one side and retreat from the other.

The classical example is the **van der Pol oscillator**

$$\ddot{x} - \mu(1 - x^2)\dot{x} + x = 0, \quad \mu > 0,$$

written as the planar system

$$\dot{x} = y, \qquad \dot{y} = \mu(1 - x^2)y - x.$$

The origin is the unique equilibrium, with $J = \bigl(\begin{smallmatrix} 0 & 1 \\ -1 & \mu \end{smallmatrix}\bigr)$, trace $\mu > 0$, and determinant $1 > 0$: the origin is an unstable spiral. For large $|(x, y)|$, the term $-\mu x^2 y$ provides strong damping that drives trajectories inward. One constructs explicit compact annular regions invariant under the flow, with no equilibria, and Poincaré–Bendixson guarantees the existence of a limit cycle in the annulus. Numerical computation and the Liénard plane analysis reveal a unique stable limit cycle for each $\mu > 0$.

The quantitative criterion for the **stability of a limit cycle** involves the **Poincaré map** (also called the first return map). Given a transversal section $\Sigma$ to the periodic orbit $\Gamma$ at a point $p_0 \in \Gamma$, the Poincaré map $\Pi : \Sigma \to \Sigma$ sends a nearby point $p \in \Sigma$ to the first return point $\phi_T(p) \cap \Sigma$ where $T(p)$ is the return time. The periodic orbit corresponds to a fixed point $p_0 = \Pi(p_0)$. Stability of $\Gamma$ as a limit cycle is equivalent to $|\Pi'(p_0)| < 1$ (the multiplier of the fixed point has absolute value less than one). The multiplier can be computed as

$$\Pi'(p_0) = \exp\!\left(\int_0^T \text{div}\,F(\phi_t(p_0))\,dt\right),$$

a formula that connects the stability of the limit cycle directly to the integral of the divergence of the vector field along the orbit — a beautiful result that makes the Bendixson criterion's divergence condition structurally transparent.

---

## 3. High-Performance Optimization & Failure Modes

### 3.1 Constructing Lyapunov Functions: Strategies and Failure Modes

Finding a Lyapunov function is as much an art as a technique, and the practitioner needs several systematic approaches. The most broadly applicable general strategy for polynomial vector fields is the **sum-of-squares (SOS) method**: seek $V$ as a polynomial satisfying $V(\mathbf{x}^*) = 0$, $V > 0$ globally (certified by writing $V$ as a sum of squares), and $-\dot{V}$ as a sum of squares as well. This reduces the existence question to a semidefinite programming feasibility problem, computable by standard numerical solvers.

For gradient systems $\dot{\mathbf{x}} = -\nabla \Phi(\mathbf{x})$, the potential $\Phi$ itself is a Lyapunov function: $\dot{\Phi} = \nabla\Phi \cdot (-\nabla\Phi) = -\|\nabla\Phi\|^2 \le 0$. The largest invariant subset of $E = \{\nabla\Phi = 0\}$ is the set of equilibria, so LaSalle forces convergence to equilibrium. Gradient structure is therefore globally stabilizing, and recognizing or constructing gradient form is a primary decomposition tool.

For mechanical systems with a natural energy $H = T + V_{\text{pot}}$, the Hamiltonian itself is typically a Lyapunov function for Lyapunov stability of minima of $V_{\text{pot}}$ (Dirichlet's theorem), but it cannot certify asymptotic stability since $\dot{H} = 0$ along trajectories. Asymptotic stability requires explicit dissipation, as in the LaSalle argument for the damped pendulum.

A common failure mode is what might be called the **radial trapping error**: constructing a $V$ that is positive definite and has $\dot{V} \le 0$ only within a small neighborhood, and then concluding global asymptotic stability. The correct conclusion is local asymptotic stability, with the region of attraction estimated by the largest sublevel set $\{V \le c\}$ contained in the domain where $\dot{V} \le 0$. Global asymptotic stability requires the additional condition that $V$ is **radially unbounded**: $V(\mathbf{x}) \to +\infty$ as $\|\mathbf{x}\| \to \infty$. Without radial unboundedness, trajectories may escape to infinity while $V$ remains bounded, invalidating the global conclusion. This is captured by **Barbalat's lemma** and its relatives, which require explicit hypotheses on the growth of $V$.

### 3.2 Applying Poincaré–Bendixson: Constructing Trapping Regions

The practical bottleneck in applying Poincaré–Bendixson is constructing a compact positively invariant region $\Omega$ that excludes unstable equilibria. The standard approach is to find a $C^1$ function $B : \mathbb{R}^2 \to \mathbb{R}$ such that the region $\Omega = \{B(\mathbf{x}) \le 0\}$ is compact and $\dot{B} = \nabla B \cdot F < 0$ on the boundary $\partial\Omega = \{B = 0\}$. This guarantees that the vector field points strictly inward on $\partial\Omega$, making $\Omega$ positively invariant.

For the van der Pol oscillator, a convenient outer bounding circle of large radius $R$ works for the outer boundary (since the vector field points inward for large $|(x,y)|$), while an inner circle of small radius $r$ around the origin works for the inner boundary (since the origin is an unstable spiral, the vector field points outward on $\partial B_r$). The resulting annulus $\{r \le |(x,y)| \le R\}$ is a compact positively invariant region with no equilibria, and Poincaré–Bendixson delivers a limit cycle.

A failure mode specific to the Poincaré–Bendixson application is the **hidden equilibrium problem**: if the constructed trapping region $\Omega$ contains an equilibrium that was overlooked (perhaps a non-obvious one arising from the nonlinear terms), then the theorem permits $\omega$-limit sets consisting of that equilibrium alone, and the conclusion about limit cycle existence collapses. Thoroughness in finding all equilibria within $\Omega$ — typically by analyzing the algebraic system $f = g = 0$ over the relevant region — is not optional. Using Bézout's theorem to bound the number of equilibria of polynomial systems provides a useful sanity check: a polynomial planar system of degree $d$ has at most $d^2$ equilibria in $\mathbb{CP}^2$, so in $\mathbb{R}^2$ the count is bounded.

### 3.3 Index Theory as a Global Constraint

The **index** of an equilibrium $\mathbf{x}^*$ of a planar vector field $F$ is the integer

$$\text{ind}(\mathbf{x}^*) = \frac{1}{2\pi}\oint_{\gamma} d\,(\text{angle of }F),$$

where $\gamma$ is a small positively oriented simple closed curve encircling $\mathbf{x}^*$ and no other equilibrium. For the standard classifications: nodes, spirals, and centers have index $+1$; saddles have index $-1$; centers (and all nondegenerate equilibria with $\det(J) > 0$) have index $+1$; and higher-order equilibria can have other integer values.

The key global theorem relates the index of a periodic orbit to the indices of the equilibria it encloses. If $\Gamma$ is a periodic orbit of a $C^1$ planar vector field, then the sum of the indices of all equilibria in the interior of $\Gamma$ equals $+1$:

$$\sum_{\mathbf{x}^* \,\text{inside}\, \Gamma} \text{ind}(\mathbf{x}^*) = +1.$$

This index formula has immediate practical consequences. A limit cycle must enclose at least one equilibrium. If the enclosed equilibria are all saddles (each with index $-1$), their total index is negative, and the formula cannot be satisfied — so no periodic orbit can enclose only saddles. Any periodic orbit must enclose a configuration of equilibria whose indices sum to $+1$. This provides a rapid test: if one constructs a candidate trapping region containing only saddles, Poincaré–Bendixson cannot guarantee a periodic orbit, and in fact the index theorem guarantees none exists there.

### 3.4 Bifurcations of Equilibria and the Birth of Limit Cycles

A topic that sits at the boundary of qualitative theory and bifurcation theory, but which every practitioner of phase portrait analysis must understand, is the **Hopf bifurcation**: the mechanism by which a stable or unstable spiral transitions to a limit cycle as a parameter varies. Suppose a family of vector fields $F_\mu$ has an equilibrium at the origin for all $\mu$ near $0$, with the Jacobian $J(\mu)$ having eigenvalues $\lambda(\mu) = \alpha(\mu) \pm i\beta(\mu)$, where $\alpha(0) = 0$, $\beta(0) \neq 0$, and $d\alpha/d\mu|_{\mu=0} \neq 0$ (the eigenvalues cross the imaginary axis transversally). At $\mu = 0$, the linearization is a center; for $\mu \neq 0$, the equilibrium is a spiral. The Hopf bifurcation theorem states that generically (specifically when the first Lyapunov coefficient $\ell_1$, computed from the cubic terms of the Taylor expansion, is nonzero), a unique limit cycle bifurcates from the equilibrium.

If $\ell_1 < 0$, the bifurcation is **supercritical**: for $\mu > 0$ (after the equilibrium becomes unstable), a stable small-amplitude limit cycle appears, surrounding the now-unstable spiral. If $\ell_1 > 0$, it is **subcritical**: an unstable limit cycle collapses into the equilibrium as $\mu$ passes through $0$, leaving the equilibrium unstable with no nearby attracting set — a potentially catastrophic situation in applications, since the trajectory must jump to a distant attractor. The first Lyapunov coefficient is computed from the nonlinear terms at $\mu = 0$ as

$$\ell_1 = \frac{1}{16}\left(f_{xxx} + f_{xyy} + g_{xxy} + g_{yyy}\right) + \frac{1}{16\beta_0}\left(f_{xy}(f_{xx}+f_{yy}) - g_{xy}(g_{xx}+g_{yy}) - f_{xx}g_{xx} + f_{yy}g_{yy}\right),$$

where all partial derivatives are evaluated at the equilibrium at $\mu = 0$ and $\beta_0 = \beta(0)$. Computing $\ell_1$ is the definitive diagnostic for the character of the Hopf bifurcation and determines whether the emerging limit cycle is born stable or unstable.

### 3.5 Structural Stability and the Limits of Phase Portrait Analysis

A phase portrait is **structurally stable** if its qualitative topology — the number and types of equilibria, the number and stability types of limit cycles, the connections between saddles — is preserved under small $C^1$ perturbations of the vector field. The Peixoto theorem characterizes structurally stable vector fields on compact surfaces: they are open and dense in the space of $C^1$ vector fields on compact 2-manifolds, and they are precisely the vector fields with finitely many hyperbolic equilibria, finitely many hyperbolic limit cycles, no saddle connections, and whose non-wandering set consists entirely of equilibria and periodic orbits.

The lesson for practice is that non-hyperbolic equilibria and homoclinic orbits are **degenerate**: they represent measure-zero phenomena in parameter space, and any small perturbation can resolve them into qualitatively different portraits. Centers, in particular, are non-generic: a center in a polynomial system is typically converted to a spiral by any generic perturbation, and certifying that a system has a true center (rather than a very slowly spiraling focus) requires exact conservation of a first integral, which only special symmetry or Hamiltonian structure can guarantee. The practitioner who observes near-circular orbits in numerical simulation should not conclude the existence of a center without a rigorous first-integral argument; the period map must be constant, not merely approximately constant, and verifying this analytically via the Abel–Liouville formula or direct algebraic integration is the only reliable certification.

The grand synthesis of this lesson is thus: phase portrait analysis of autonomous planar systems is not a collection of local tests but a coherent global theory. Eigenvalue geometry at equilibria, Lyapunov functions and LaSalle's principle, the index theorem, Poincaré–Bendixson, and the Poincaré map for limit cycles form a tightly interlocked framework in which local information at equilibria, global topological constraints from planarity, and energy-like witnesses in the form of Lyapunov functions mutually reinforce each other to yield complete structural pictures of dynamics that no explicit formula could easily capture.
