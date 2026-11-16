# Lesson 6: Vector Calculus & Multiple Integration Theorems

## 1. First-Principles Intuition & Invariants

The transition from single-variable calculus to vector calculus is not merely a matter of adding dimensions to familiar operations. It represents a fundamental shift in what we mean by integration itself. In one variable, integration accumulates a scalar quantity along an interval of the real line, and the topology of that domain is as simple as topology can be. The moment the domain becomes a curve winding through $\mathbb{R}^3$, a surface bending through space, or a solid volume with a nontrivial boundary, the integrand and the domain must be described together as a geometric object, and the integral becomes a statement about the interplay between a field and the geometry it lives on.

The central invariants of vector calculus are the three great integral theorems: **Green's theorem**, the **Divergence theorem** (Gauss's theorem), and **Stokes' theorem**. These are not three separate results with a family resemblance. They are three instances of a single, deeper theorem — the **Generalized Stokes' theorem** — which states that the integral of a differential form over the boundary of an oriented manifold equals the integral of its exterior derivative over the manifold itself:

$$\int_{\partial \Omega} \omega = \int_{\Omega} d\omega$$

Understanding this unification is the organizing invariant of the entire lesson. Every specific theorem we derive will be recognizable as a specialization of this identity under a particular choice of ambient dimension, orientation, and differential form.

### Fields, Forms, and the Geometric Setup

A **vector field** on an open set $U \subseteq \mathbb{R}^n$ is a smooth map $\mathbf{F}: U \to \mathbb{R}^n$ assigning a vector to every point of the domain. In $\mathbb{R}^3$ we write $\mathbf{F} = P\,\hat{\mathbf{i}} + Q\,\hat{\mathbf{j}} + R\,\hat{\mathbf{k}}$ with component functions $P, Q, R : U \to \mathbb{R}$. The natural objects attached to such fields are the **differential operators**: the gradient $\nabla f$, the divergence $\nabla \cdot \mathbf{F}$, and the curl $\nabla \times \mathbf{F}$. These operators encode local geometric and analytic properties of the field, and the integral theorems are precisely the statements that connect their local behavior to global boundary data.

The **differential 1-form** $\omega = P\,dx + Q\,dy + R\,dz$ is the algebraic object dual to the vector field $\mathbf{F}$. The wedge product of two 1-forms is a 2-form, and of three is a 3-form. The exterior derivative $d$ raises degree: $df$ of a 0-form (scalar function) is a 1-form, $d\omega$ of a 1-form is a 2-form, $d\alpha$ of a 2-form is a 3-form. The critical algebraic identity is $d^2 = 0$, meaning $d(d\omega) = 0$ for any form $\omega$. This identity is the algebraic shadow of two classical vanishing theorems: $\nabla \times (\nabla f) = \mathbf{0}$ (the curl of a gradient is zero) and $\nabla \cdot (\nabla \times \mathbf{F}) = 0$ (the divergence of a curl is zero). Both follow because $d^2 = 0$, and both play decisive roles in determining when line and surface integrals are path-independent.

### Conservative Fields and Exact Differentials

A vector field $\mathbf{F}$ on a simply connected domain $U$ is called **conservative** if there exists a scalar potential function $f: U \to \mathbb{R}$ such that $\mathbf{F} = \nabla f$. In terms of differential forms, the corresponding 1-form $\omega = P\,dx + Q\,dy + R\,dz$ is **exact** — it is the exterior derivative of a 0-form: $\omega = df$.

The necessary condition for exactness is that $\omega$ be **closed**, meaning $d\omega = 0$. In coordinates this amounts to the integrability conditions:

$$\frac{\partial P}{\partial y} = \frac{\partial Q}{\partial x}, \qquad \frac{\partial Q}{\partial z} = \frac{\partial R}{\partial y}, \qquad \frac{\partial R}{\partial x} = \frac{\partial P}{\partial z}$$

These three equations are equivalent to requiring $\nabla \times \mathbf{F} = \mathbf{0}$. On a **simply connected** domain (one with no holes, in the sense that every closed loop is contractible to a point), closed implies exact. On a domain with nontrivial topology — the punctured plane $\mathbb{R}^2 \setminus \{0\}$, for example — a closed form need not be exact, and this failure is measured by the first de Rham cohomology group $H^1_{\mathrm{dR}}(U)$.

The canonical counterexample is the angular form on $\mathbb{R}^2 \setminus \{0\}$:

$$\omega = \frac{-y\,dx + x\,dy}{x^2 + y^2}$$

One checks directly that $d\omega = 0$, yet

$$\oint_{C} \omega = 2\pi$$

for any simple closed curve $C$ winding once counterclockwise around the origin. Because this integral is nonzero, $\omega$ cannot be $df$ for any globally defined smooth function $f$ on $\mathbb{R}^2 \setminus \{0\}$. The local primitive $f = \arctan(y/x)$ fails to extend globally precisely because the domain has a hole. This example is not a curiosity; it is the prototype for the topological obstructions that the integral theorems probe.

When $\mathbf{F}$ is conservative with potential $f$, the Fundamental Theorem for Line Integrals gives:

$$\int_C \mathbf{F} \cdot d\mathbf{r} = f(\mathbf{r}(b)) - f(\mathbf{r}(a))$$

This is the most direct generalization of the Fundamental Theorem of Calculus: the integral depends only on endpoint data, not on the path connecting them. It is the simplest instance of $\int_{\partial \Omega} \omega = \int_\Omega d\omega$, with $\Omega$ a curve, $\partial\Omega$ its two endpoints, and $\omega = df$ an exact form.

---

## 2. Core Architecture & Mechanics

### Line Integrals: Setup and Parametrization

Let $C$ be a smooth oriented curve in $\mathbb{R}^3$, parametrized by $\mathbf{r}: [a,b] \to \mathbb{R}^3$ with $\mathbf{r}(t) = (x(t), y(t), z(t))$. The **line integral of a scalar function** $\phi$ with respect to arc length is:

$$\int_C \phi\,ds = \int_a^b \phi(\mathbf{r}(t))\,\|\mathbf{r}'(t)\|\,dt$$

where $ds = \|\mathbf{r}'(t)\|\,dt$ is the arc length element. This integral is parametrization-independent in the sense that any orientation-preserving reparametrization yields the same value.

The **line integral of a vector field** $\mathbf{F}$ along $C$ is:

$$\int_C \mathbf{F} \cdot d\mathbf{r} = \int_a^b \mathbf{F}(\mathbf{r}(t)) \cdot \mathbf{r}'(t)\,dt = \int_a^b \left(P\frac{dx}{dt} + Q\frac{dy}{dt} + R\frac{dz}{dt}\right)dt$$

Mechanically, this computes the cumulative tangential component of $\mathbf{F}$ along the path — the net work done by the field on a particle traversing $C$.

**Worked Example.** Let $\mathbf{F}(x,y,z) = (yz, xz, xy)$ and let $C$ be the helix parametrized by $\mathbf{r}(t) = (\cos t, \sin t, t)$ for $t \in [0, 2\pi]$. The derivative is $\mathbf{r}'(t) = (-\sin t, \cos t, 1)$. Along $C$, the field evaluates to:

$$\mathbf{F}(\mathbf{r}(t)) = (t\sin t,\; t\cos t,\; \cos t \sin t)$$

The integrand becomes:

$$\mathbf{F}(\mathbf{r}(t)) \cdot \mathbf{r}'(t) = -t\sin^2 t + t\cos^2 t + \cos t \sin t = t\cos(2t) + \tfrac{1}{2}\sin(2t)$$

Before computing, notice that $\mathbf{F} = \nabla f$ where $f(x,y,z) = xyz$, since $\partial_{x}(xyz) = yz$, $\partial_y(xyz) = xz$, $\partial_z(xyz) = xy$. By the Fundamental Theorem:

$$\int_C \mathbf{F} \cdot d\mathbf{r} = f(\mathbf{r}(2\pi)) - f(\mathbf{r}(0)) = f(1, 0, 2\pi) - f(1, 0, 0) = 0 - 0 = 0$$

The closed-form answer requires no integration at all. This illustrates the computational power of identifying conservative fields before parametrizing.

### Green's Theorem: The Planar Case

Green's theorem governs the relationship between a line integral around a closed planar curve and a double integral over the region it encloses.

**Theorem (Green).** Let $D \subseteq \mathbb{R}^2$ be a compact region with piecewise smooth boundary $\partial D$, oriented counterclockwise (the positive orientation, so that $D$ lies to the left as you traverse $\partial D$). Let $P, Q: D \to \mathbb{R}$ be continuously differentiable. Then:

$$\oint_{\partial D} P\,dx + Q\,dy = \iint_D \left(\frac{\partial Q}{\partial x} - \frac{\partial P}{\partial y}\right)dA$$

**Proof.** It suffices to establish the two scalar identities separately and add them. We prove

$$\oint_{\partial D} P\,dx = -\iint_D \frac{\partial P}{\partial y}\,dA$$

and an analogous identity for $Q$. Suppose $D$ is a **Type I region**: $D = \{(x,y) : a \le x \le b,\, \phi_1(x) \le y \le \phi_2(x)\}$. The right-hand side evaluates by the Fundamental Theorem of Calculus in the $y$-variable:

$$-\iint_D \frac{\partial P}{\partial y}\,dA = -\int_a^b \int_{\phi_1(x)}^{\phi_2(x)} \frac{\partial P}{\partial y}(x,y)\,dy\,dx = -\int_a^b \left[P(x,\phi_2(x)) - P(x,\phi_1(x))\right]dx$$

The boundary $\partial D$ of a Type I region consists of four oriented segments (bottom, right, top, left). The top boundary runs from right to left, so traversing $C_{\text{top}}$ in the positive orientation means $x$ decreases from $b$ to $a$. Parametrize the bottom boundary $C_{\text{bot}}$ by $x \in [a,b]$ with $y = \phi_1(x)$, and the top boundary $C_{\text{top}}$ by $x \in [b,a]$ (reversed) with $y = \phi_2(x)$. The left and right segments are vertical, so $dx = 0$ on them. Thus:

$$\oint_{\partial D} P\,dx = \int_{C_{\text{bot}}} P(x,\phi_1(x))\,dx + \int_{C_{\text{top}}} P(x,\phi_2(x))\,dx = \int_a^b P(x,\phi_1(x))\,dx - \int_a^b P(x,\phi_2(x))\,dx$$

This matches $-\iint_D \frac{\partial P}{\partial y}\,dA$ exactly. The corresponding identity $\oint_{\partial D} Q\,dy = \iint_D \frac{\partial Q}{\partial x}\,dA$ follows from treating $D$ as a Type II region and applying the same argument in the $x$-variable. Adding the two identities completes the proof for simple Type I/II regions. General compact regions with piecewise smooth boundaries are handled by decomposing into finitely many such pieces and noting that interior cuts are traversed in opposite directions by adjacent pieces, so their contributions to the line integrals cancel. $\blacksquare$

**Application: Area via Line Integrals.** A striking consequence of Green's theorem is that the area of $D$ can be computed directly from its boundary. Taking $P = 0$, $Q = x$ gives $\frac{\partial Q}{\partial x} - \frac{\partial P}{\partial y} = 1$, so:

$$\text{Area}(D) = \oint_{\partial D} x\,dy$$

Similarly, $P = -y$, $Q = 0$ yields $\text{Area}(D) = -\oint_{\partial D} y\,dx$, and averaging both formulas:

$$\text{Area}(D) = \frac{1}{2}\oint_{\partial D} (x\,dy - y\,dx)$$

This formula is the basis for the **surveyor's formula** (shoelace formula) for polygons and arises in the computation of areas bounded by parametric curves such as ellipses and cycloids.

### Surface Integrals: Flux and Scalar Integrals

A smooth surface $S \subseteq \mathbb{R}^3$ is parametrized by $\mathbf{r}: D \subseteq \mathbb{R}^2 \to \mathbb{R}^3$, $\mathbf{r}(u,v) = (x(u,v), y(u,v), z(u,v))$. The partial derivatives $\mathbf{r}_u = \partial\mathbf{r}/\partial u$ and $\mathbf{r}_v = \partial\mathbf{r}/\partial v$ are tangent vectors to the surface, and their cross product:

$$d\mathbf{S} = (\mathbf{r}_u \times \mathbf{r}_v)\,du\,dv$$

is the **vector area element**: a vector whose magnitude is the area of the infinitesimal parallelogram spanned by $\mathbf{r}_u$ and $\mathbf{r}_v$, and whose direction is the surface normal. The scalar area element is $dS = \|\mathbf{r}_u \times \mathbf{r}_v\|\,du\,dv$.

The **flux integral** (surface integral of a vector field) measures the net flow of $\mathbf{F}$ through $S$:

$$\iint_S \mathbf{F} \cdot d\mathbf{S} = \iint_D \mathbf{F}(\mathbf{r}(u,v)) \cdot (\mathbf{r}_u \times \mathbf{r}_v)\,du\,dv$$

For a surface given explicitly as $z = g(x,y)$ over a domain $D \subseteq \mathbb{R}^2$, with upward orientation, one has $\mathbf{r}(x,y) = (x, y, g(x,y))$, and:

$$\mathbf{r}_x \times \mathbf{r}_y = \left(-\frac{\partial g}{\partial x},\, -\frac{\partial g}{\partial y},\, 1\right)$$

so the flux integral becomes:

$$\iint_S \mathbf{F} \cdot d\mathbf{S} = \iint_D \left(-P\frac{\partial g}{\partial x} - Q\frac{\partial g}{\partial y} + R\right)dA$$

**Worked Example.** Compute the flux of $\mathbf{F}(x,y,z) = (x, y, z)$ outward through the upper hemisphere $S: x^2 + y^2 + z^2 = 1$, $z \ge 0$.

Parametrize by spherical coordinates: $\mathbf{r}(\theta,\phi) = (\sin\phi\cos\theta, \sin\phi\sin\theta, \cos\phi)$ with $\theta \in [0,2\pi]$, $\phi \in [0, \pi/2]$. Computing:

$$\mathbf{r}_\theta = (-\sin\phi\sin\theta,\; \sin\phi\cos\theta,\; 0)$$
$$\mathbf{r}_\phi = (\cos\phi\cos\theta,\; \cos\phi\sin\theta,\; -\sin\phi)$$

$$\mathbf{r}_\phi \times \mathbf{r}_\theta = (\sin^2\phi\cos\theta,\; \sin^2\phi\sin\theta,\; \sin\phi\cos\phi)$$

(This points outward since its $z$-component is positive for $\phi \in (0,\pi/2)$.) On $S$, $\mathbf{F}(\mathbf{r}(\theta,\phi)) = (\sin\phi\cos\theta, \sin\phi\sin\theta, \cos\phi)$, which equals the position vector — that is, $\mathbf{F} = \hat{\mathbf{n}}$ on the unit sphere (since $|\mathbf{r}| = 1$). Thus $\mathbf{F} \cdot (\mathbf{r}_\phi \times \mathbf{r}_\theta) = \sin\phi$, and:

$$\iint_S \mathbf{F} \cdot d\mathbf{S} = \int_0^{2\pi}\int_0^{\pi/2} \sin\phi\,d\phi\,d\theta = 2\pi \cdot [-\cos\phi]_0^{\pi/2} = 2\pi \cdot (0 - (-1)) = 2\pi$$

### The Divergence Theorem

The Divergence theorem lifts Green's theorem from two to three dimensions, relating the flux of a vector field through a closed surface to the divergence of the field in the enclosed volume.

**Theorem (Gauss–Ostrogradsky).** Let $E \subseteq \mathbb{R}^3$ be a compact region with piecewise smooth boundary $\partial E$, oriented with outward-pointing normals. Let $\mathbf{F}: E \to \mathbb{R}^3$ be continuously differentiable. Then:

$$\oiint_{\partial E} \mathbf{F} \cdot d\mathbf{S} = \iiint_E (\nabla \cdot \mathbf{F})\,dV$$

where $\nabla \cdot \mathbf{F} = \frac{\partial P}{\partial x} + \frac{\partial Q}{\partial y} + \frac{\partial R}{\partial z}$.

**Proof.** As with Green's theorem, it suffices to prove the three scalar identities separately. We establish:

$$\oiint_{\partial E} R\,\hat{\mathbf{k}} \cdot d\mathbf{S} = \iiint_E \frac{\partial R}{\partial z}\,dV$$

Suppose $E$ is a **Type I solid**: $E = \{(x,y,z): (x,y) \in D,\, \psi_1(x,y) \le z \le \psi_2(x,y)\}$ where $D$ is the projection of $E$ onto the $xy$-plane. The right-hand side, by the one-dimensional Fundamental Theorem in $z$:

$$\iiint_E \frac{\partial R}{\partial z}\,dV = \iint_D \int_{\psi_1}^{\psi_2} \frac{\partial R}{\partial z}\,dz\,dA = \iint_D \left[R(x,y,\psi_2) - R(x,y,\psi_1)\right]dA$$

The boundary $\partial E$ has an upper surface $S_2: z = \psi_2(x,y)$, a lower surface $S_1: z = \psi_1(x,y)$, and possibly a lateral surface where the outward normal is horizontal (so $\hat{\mathbf{k}} \cdot \hat{\mathbf{n}} = 0$, contributing nothing). For the upper surface with upward outward normal, $\hat{\mathbf{k}} \cdot d\mathbf{S} = dA$. For the lower surface with downward outward normal, $\hat{\mathbf{k}} \cdot d\mathbf{S} = -dA$. Therefore:

$$\oiint_{\partial E} R\,\hat{\mathbf{k}} \cdot d\mathbf{S} = \iint_D R(x,y,\psi_2(x,y))\,dA - \iint_D R(x,y,\psi_1(x,y))\,dA$$

This matches the volume integral exactly. Analogous arguments for $P$ and $Q$ over Type II and Type III solids, combined by the same decomposition argument used in Green's theorem, complete the proof. $\blacksquare$

**Worked Example.** Compute the outward flux of $\mathbf{F}(x,y,z) = (x^3, y^3, z^3)$ through the unit sphere $S: x^2 + y^2 + z^2 = 1$.

Direct parametrization would be laborious. The divergence theorem gives:

$$\nabla \cdot \mathbf{F} = 3x^2 + 3y^2 + 3z^2 = 3(x^2 + y^2 + z^2) = 3\rho^2$$

in spherical coordinates, where $\rho = \sqrt{x^2+y^2+z^2}$. The volume integral over the unit ball $B$ is:

$$\iiint_B 3\rho^2\,dV = 3\int_0^{2\pi}\int_0^{\pi}\int_0^1 \rho^2 \cdot \rho^2\sin\phi\,d\rho\,d\phi\,d\theta = 3 \cdot 2\pi \cdot 2 \cdot \frac{1}{5} = \frac{12\pi}{5}$$

### Stokes' Theorem

Stokes' theorem is the full three-dimensional generalization of Green's theorem, relating the circulation of a vector field around a closed curve to the flux of its curl through any surface bounded by that curve.

**Theorem (Stokes).** Let $S$ be a compact oriented surface in $\mathbb{R}^3$ with piecewise smooth boundary $\partial S$, where the orientation of $\partial S$ is induced by that of $S$ via the right-hand rule. Let $\mathbf{F}: S \to \mathbb{R}^3$ be continuously differentiable. Then:

$$\oint_{\partial S} \mathbf{F} \cdot d\mathbf{r} = \iint_S (\nabla \times \mathbf{F}) \cdot d\mathbf{S}$$

where the curl is:

$$\nabla \times \mathbf{F} = \left(\frac{\partial R}{\partial y} - \frac{\partial Q}{\partial z}\right)\hat{\mathbf{i}} - \left(\frac{\partial R}{\partial x} - \frac{\partial P}{\partial z}\right)\hat{\mathbf{j}} + \left(\frac{\partial Q}{\partial x} - \frac{\partial P}{\partial y}\right)\hat{\mathbf{k}}$$

**Proof (for a graph surface).** Let $S$ be parametrized as the graph $z = g(x,y)$ over a domain $D$ with boundary $\partial D$. The boundary curve $\partial S$ is the image of $\partial D$ under the lifting $(x,y) \mapsto (x,y,g(x,y))$.

The right-hand side, using $d\mathbf{S} = (-g_x, -g_y, 1)\,dA$, expands to:

$$\iint_D \left[\left(\frac{\partial R}{\partial y} - \frac{\partial Q}{\partial z}\right)(-g_x) - \left(\frac{\partial R}{\partial x} - \frac{\partial P}{\partial z}\right)(-g_y) \cdot (-1) + \left(\frac{\partial Q}{\partial x} - \frac{\partial P}{\partial y}\right)\right]dA$$

We simplify this by applying Green's theorem to the planar domain $D$. Define modified component functions:

$$\tilde{P}(x,y) = P(x,y,g(x,y)) + R(x,y,g(x,y))\,g_x(x,y)$$
$$\tilde{Q}(x,y) = Q(x,y,g(x,y)) + R(x,y,g(x,y))\,g_y(x,y)$$

The left-hand side, with the boundary curve $\partial S$ lifted from $\partial D$, becomes:

$$\oint_{\partial S} \mathbf{F} \cdot d\mathbf{r} = \oint_{\partial D} (P\,dx + Q\,dy + R\,dz) = \oint_{\partial D} \left(P + R g_x\right)dx + \left(Q + R g_y\right)dy = \oint_{\partial D} \tilde{P}\,dx + \tilde{Q}\,dy$$

By Green's theorem applied to $\tilde{P}$ and $\tilde{Q}$ over $D$:

$$\oint_{\partial D} \tilde{P}\,dx + \tilde{Q}\,dy = \iint_D \left(\frac{\partial \tilde{Q}}{\partial x} - \frac{\partial \tilde{P}}{\partial y}\right)dA$$

One then computes $\frac{\partial \tilde{Q}}{\partial x} - \frac{\partial \tilde{P}}{\partial y}$ using the chain rule, collecting all terms involving $g_x$, $g_y$, $g_{xx}$, $g_{xy}$, $g_{yy}$. The second-derivative terms cancel by symmetry of mixed partials ($g_{xy} = g_{yx}$), and the remaining terms assemble exactly into the components of $(\nabla \times \mathbf{F}) \cdot (-g_x, -g_y, 1)$. This completes the proof for graph surfaces; the general case follows by decomposing $S$ into graph patches. $\blacksquare$

**Key Consequence.** Stokes' theorem gives a surface-independent characterization of curl-free fields. If $\nabla \times \mathbf{F} = \mathbf{0}$ throughout a simply connected domain, then for any two surfaces $S_1$, $S_2$ with the same boundary $\partial S_1 = \partial S_2 = C$:

$$\oint_C \mathbf{F} \cdot d\mathbf{r} = \iint_{S_1}(\nabla \times \mathbf{F}) \cdot d\mathbf{S} = 0 = \iint_{S_2}(\nabla \times \mathbf{F}) \cdot d\mathbf{S}$$

confirming path-independence and the existence of a potential function. The simple connectivity is essential: on $\mathbb{R}^3 \setminus \{\text{a line}\}$, curl-free does not imply conservative.

### Change of Variables: The Jacobian and Pullback

Multiple integration theorems rarely yield tractable integrals in Cartesian coordinates. The correct framework for changing variables is the **pullback of a differential form** under a smooth map.

Let $T: D^* \to D$ be a smooth bijection with $T(u,v) = (x(u,v), y(u,v))$. The double integral transforms as:

$$\iint_D f(x,y)\,dx\,dy = \iint_{D^*} f(x(u,v), y(u,v))\,|J_T(u,v)|\,du\,dv$$

where the **Jacobian determinant** is:

$$J_T(u,v) = \frac{\partial(x,y)}{\partial(u,v)} = \det\begin{pmatrix} \frac{\partial x}{\partial u} & \frac{\partial x}{\partial v} \\ \frac{\partial y}{\partial u} & \frac{\partial y}{\partial v} \end{pmatrix} = \frac{\partial x}{\partial u}\frac{\partial y}{\partial v} - \frac{\partial x}{\partial v}\frac{\partial y}{\partial u}$$

The absolute value $|J_T|$ is the local area scaling factor of $T$: infinitesimal area elements in $D^*$ are stretched or compressed by this factor under $T$. In the differential forms language, this is simply the pullback identity $T^*(dx \wedge dy) = J_T\,du \wedge dv$, where the wedge product enforces the orientation bookkeeping automatically.

For polar coordinates $x = r\cos\theta$, $y = r\sin\theta$:

$$J = \det\begin{pmatrix}\cos\theta & -r\sin\theta \\ \sin\theta & r\cos\theta\end{pmatrix} = r\cos^2\theta + r\sin^2\theta = r$$

so $dx\,dy = r\,dr\,d\theta$. For cylindrical coordinates $(r,\theta,z)$, $dV = r\,dr\,d\theta\,dz$. For spherical coordinates $(\rho,\theta,\phi)$ with $x = \rho\sin\phi\cos\theta$, $y = \rho\sin\phi\sin\theta$, $z = \rho\cos\phi$:

$$J = \rho^2\sin\phi \qquad \Longrightarrow \qquad dV = \rho^2\sin\phi\,d\rho\,d\phi\,d\theta$$

The Jacobian determinant has a geometric meaning beyond formal computation: it measures how the map $T$ distorts oriented volume at each point, and the sign records whether $T$ preserves or reverses orientation. The correct change-of-variables theorem asserts that orientation-reversing maps contribute with a sign flip, which is automatically handled by the absolute value in the scalar formula or by the orientation conventions in the differential forms formula.

The diagrammatic structure below summarizes how the integral theorems relate domains, boundaries, and differential operators:

```
Dimension 0: Points (endpoints)
        ↑  FTC for Line Integrals:  ∫_{a}^{b} df = f(b) - f(a)

Dimension 1: Curves (C)
        ↑  Green's Theorem / Stokes in 2D:  ∮_{∂D} ω = ∬_{D} dω

Dimension 2: Surfaces (S)
        ↑  Stokes' Theorem:  ∮_{∂S} F·dr = ∬_{S} (∇×F)·dS

Dimension 3: Volumes (E)
        ↑  Divergence Theorem:  ∯_{∂E} F·dS = ∭_{E} (∇·F) dV

Unifying Identity:  ∫_{∂Ω} ω = ∫_{Ω} dω   (Generalized Stokes)
```

The operators $d$ on forms correspond precisely to the classical operators: $d(f) = \nabla f$, $d(\omega^1) = \nabla \times \mathbf{F}$ (via the Hodge star in $\mathbb{R}^3$), $d(\omega^2) = \nabla \cdot \mathbf{F}$.

---

## 3. High-Performance Optimization & Failure Modes

### Choosing the Right Theorem: Computational Strategy

Each integral theorem is both a theoretical identity and a computational tool. The practitioner's skill lies in recognizing which direction of a theorem to apply — sometimes converting a surface integral to a volume integral is cheaper, sometimes the reverse — and in detecting the symmetries that make one coordinate system vastly more efficient than another.

**Strategy 1: Closing surfaces to apply the Divergence Theorem.** When asked to compute flux through an open surface (e.g., the hemisphere, a paraboloid cap, the lateral face of a cylinder), the direct computation is often expensive. The standard strategy is to close the surface by adding a simple "cap" piece, apply the Divergence Theorem to the closed surface, then subtract the flux through the cap.

For example, to find the flux of $\mathbf{F}$ through the upper hemisphere $S_{\text{top}}$ alone: let $S_{\text{disk}}$ be the disk $x^2 + y^2 \le 1$, $z = 0$ with downward normal (to close the surface into a solid $E$). Then:

$$\iint_{S_{\text{top}}} \mathbf{F} \cdot d\mathbf{S} = \iiint_E (\nabla \cdot \mathbf{F})\,dV - \iint_{S_{\text{disk}}} \mathbf{F} \cdot d\mathbf{S}$$

The disk integral is frequently trivial — if $\mathbf{F}$ has $R = 0$ on the $z = 0$ plane, its flux through the horizontal disk is zero, and the entire problem reduces to a volume integral.

**Strategy 2: Choosing the right spanning surface for Stokes' theorem.** The boundary curve $\partial S$ uniquely determines the left-hand side of Stokes' theorem, but the choice of spanning surface $S$ is free. If $C$ is a complicated space curve, one can choose $S$ to be the "simplest" surface with boundary $C$. For curves lying in a plane, the planar region bounded by $C$ is often optimal. For curves on a known surface (a sphere, a cylinder), the capping disc or spherical cap is cleaner.

**Strategy 3: Symmetry and the vanishing principle.** If $\nabla \times \mathbf{F} = \mathbf{0}$ on a surface and the entire boundary is traversed, Stokes' theorem immediately gives zero without any computation. Similarly, if $\nabla \cdot \mathbf{F} = 0$ (a **solenoidal** or **divergence-free** field) throughout a volume, the net flux through the boundary is zero. These vanishing results are not just computational shortcuts — they encode physical conservation laws (magnetic flux, incompressible fluid flow) and topological invariants.

### Failure Modes: Orientation Errors

The most common and consequential error in applying these theorems is an orientation mistake. Each theorem has a strict consistency requirement: the orientation of the boundary must be **induced** by the orientation of the domain.

For the Divergence Theorem, "outward" always means away from the interior of $E$. For Stokes' theorem, the boundary curve $\partial S$ is oriented by the **right-hand rule**: if the thumb of the right hand points in the direction of the surface normal, the fingers curl in the direction of $\partial S$. Reversing any one orientation flips the sign of an entire side of the equation, turning a correct answer into its negative.

A subtle failure arises with **non-orientable surfaces** such as the Möbius band. These have no consistent global choice of normal vector, and Stokes' theorem — which requires a coherent orientation — does not apply in its classical form. The generalized Stokes' theorem for manifolds handles this via the machinery of de Rham cohomology, where the integral is defined for forms rather than fields, and orientation is encoded in the choice of volume form.

### Failure Modes: Domain Topology and the Exactness Gap

A closed form ($d\omega = 0$) is exact ($\omega = df$) on any **contractible** open set by the **Poincaré Lemma**, which we now state and prove.

**Lemma (Poincaré).** If $U \subseteq \mathbb{R}^n$ is contractible (smoothly homotopy equivalent to a point), then every closed $k$-form on $U$ is exact.

**Proof sketch.** Define the **homotopy operator** $h_k: \Omega^k(U) \to \Omega^{k-1}(U)$ by integrating a form along the contracting homotopy $H: U \times [0,1] \to U$ with $H(x,0) = x_0$ (a fixed point) and $H(x,1) = x$. Explicitly, for a $k$-form $\omega$:

$$h_k(\omega)(x) = \int_0^1 \iota_{\partial_t} H^* \omega \cdot t^{k-1}\,dt$$

where $\iota_{\partial_t}$ denotes interior multiplication by the vector $\partial_t$. A direct computation using the naturality of $d$ and $d(H^*\omega) = H^*(d\omega)$ establishes the **homotopy formula**:

$$d \circ h_k + h_{k+1} \circ d = \text{id}$$

If $d\omega = 0$, then $d(h_k\omega) + h_{k+1}(0) = \omega$, so $\omega = d(h_k\omega)$ is exact. $\blacksquare$

The Poincaré Lemma's hypothesis is sharp. On $\mathbb{R}^2 \setminus \{0\}$ (not contractible, $\pi_1 \cong \mathbb{Z}$), the angular form $\omega$ is closed but not exact. On $\mathbb{R}^3 \setminus \{0\}$ (not contractible at the level of 2-spheres, $\pi_2 \cong \mathbb{Z}$), the radial flux form $\alpha = \frac{x\,dy\wedge dz - y\,dx\wedge dz + z\,dx\wedge dy}{(x^2+y^2+z^2)^{3/2}}$ is closed (its exterior derivative is zero) but not exact: its integral over the unit sphere equals $4\pi$, and by Stokes' theorem, an exact form would integrate to zero over any closed surface. These non-exact closed forms are the generators of de Rham cohomology groups, and they represent genuine topological obstructions that no analytic manipulation can remove.

### Boundary Edge Cases and Improper Integrals

The Divergence Theorem requires that $\mathbf{F}$ be continuously differentiable on the **closed** region $\overline{E}$, including the boundary. When $\mathbf{F}$ has a singularity inside $E$ — as the Coulomb field $\mathbf{F} = \hat{\mathbf{r}}/\rho^2$ has at the origin — the theorem cannot be applied directly. The standard resolution is to **excise a small ball** $B_\epsilon(0)$ of radius $\epsilon$ around the singularity, apply the Divergence Theorem to $E \setminus B_\epsilon(0)$, then take the limit as $\epsilon \to 0$.

For the Coulomb field, $\nabla \cdot (\hat{\mathbf{r}}/\rho^2) = 0$ away from the origin (a computation that must be done carefully in spherical coordinates). Therefore, for any closed surface $S$ enclosing the origin:

$$\oiint_S \frac{\hat{\mathbf{r}}}{\rho^2} \cdot d\mathbf{S} = \lim_{\epsilon\to 0} \oiint_{S_\epsilon} \frac{\hat{\mathbf{r}}}{\rho^2} \cdot d\mathbf{S} = \lim_{\epsilon\to 0} \frac{1}{\epsilon^2} \cdot 4\pi\epsilon^2 = 4\pi$$

This computation, done in full generality using the **Dirac delta distribution** $\nabla \cdot (\hat{\mathbf{r}}/\rho^2) = 4\pi\delta^3(\mathbf{r})$, is the mathematical foundation of Gauss's law in electrostatics. The value $4\pi$ is not arbitrary; it is the surface area of the unit sphere, the geometric constant encoding three-dimensional solid angle. The excision technique generalizes: whenever a singularity of $\mathbf{F}$ is isolated, one removes it with a small ball, checks that the flux through the shrinking sphere has a finite limit, and incorporates that limit as the singular "source term."

### Coordinate Optimization and the Jacobian in Practice

Computing triple integrals over non-rectangular domains in Cartesian coordinates is almost always the wrong approach. The practitioner's first task is to identify the **natural symmetry group** of the domain and integrand, then to choose the coordinate system in which the domain becomes a rectangular box and the integrand simplifies.

A sphere of radius $a$ centered at the origin is rectangular in spherical coordinates: $0 \le \rho \le a$, $0 \le \theta \le 2\pi$, $0 \le \phi \le \pi$. A solid cylinder of radius $a$ and height $h$ is rectangular in cylindrical coordinates. An ellipsoid $\frac{x^2}{a^2} + \frac{y^2}{b^2} + \frac{z^2}{c^2} \le 1$ becomes the unit ball under the linear map $(x,y,z) = (au, bv, cw)$, which has Jacobian $abc$. These coordinate changes are not tricks but systematic applications of the change-of-variables theorem: the new coordinates are a diffeomorphism from the new parameter domain to the original domain, and the Jacobian accounts for the resulting distortion of volume elements.

For general regions defined by inequalities $u_1 \le u \le u_2$, $v_1(u) \le v \le v_2(u)$, $w_1(u,v) \le w \le w_2(u,v)$ in the new coordinates, the integral reduces to an iterated integral in a canonical order. The choice of order of integration is then a secondary optimization problem: pick the order in which the innermost antiderivative is explicitly computable in closed form. The classical example is $\iint_D e^{x^2}\,dA$ over a triangular domain: in one order the inner integral has no closed form, while switching order converts it to $\int e^{x^2}\,dx$ evaluated at a specific upper limit, which yields a Gaussian integral after completing the square or applying Fubini's theorem to the full square domain.

The synthesis of these techniques — conservative field identification, strategic theorem application, orientation discipline, coordinate adaptation, and singularity excision — constitutes the full toolkit of the working analyst. Each theorem in this lesson is ultimately one face of a single geometric truth: that the behavior of a smooth field on a manifold is completely determined by its behavior on the boundary, mediated by an appropriate differential operator. That truth, expressed in the language of differential forms as $\int_{\partial\Omega}\omega = \int_\Omega d\omega$, is one of the most consequential identities in all of mathematics.
