# Lesson 1: First-Order ODEs — Exact Forms, Integrating Factors, Separability

## 1. First-Principles Intuition & Invariants

A differential equation is not, at its core, a computational recipe. It is a *constraint on the shape of the unknown*. When we write

$$\frac{dy}{dx} = f(x, y),$$

we are not asking for a number but for a function $y(x)$ whose slope at every point of its graph is prescribed by the rule $f$. The geometric content of this constraint is immediate: the equation defines a *slope field*, a direction field painted across the $(x, y)$-plane, and a solution is a curve that flows everywhere tangent to those directions. Every technique in the classical theory of first-order ODEs is, in essence, a strategy for finding such a curve, either by exploiting special algebraic structure in $f$, by constructing an auxiliary function that reorganizes the equation into a recognizable form, or by appealing to an existence theorem that guarantees the curve exists even when we cannot write it down.

The classification of first-order equations is not an arbitrary taxonomy. Each class corresponds to a genuine structural property of the differential form underlying the equation, and each solution method is an algebraic consequence of that structure. Understanding this correspondence is what separates a practitioner who can recognize and solve equations from one who merely memorizes procedures.

**The Differential Form Perspective.** Every first-order ODE can be written not in slope form $dy/dx = f(x,y)$ but in symmetric differential form

$$M(x, y)\, dx + N(x, y)\, dy = 0.$$

This notation is geometrically honest. It treats $x$ and $y$ symmetrically as coordinates on the plane and asks: along what curves does the 1-form $\omega = M\, dx + N\, dy$ vanish? This is the perspective that unifies separable, exact, and linear equations and makes the theory of integrating factors coherent.

**Existence and Uniqueness: Picard-Lindelöf.** Before solving any equation, the mathematician must ask whether a solution exists and, if so, whether it is unique. The Picard-Lindelöf theorem provides the fundamental answer.

**Theorem (Picard-Lindelöf).** Let $f : \mathbb{R}^2 \to \mathbb{R}$ be continuous on an open rectangle $R = (x_0 - a, x_0 + a) \times (y_0 - b, y_0 + b)$ and satisfy a Lipschitz condition in $y$ on $R$: there exists a constant $L > 0$ such that

$$|f(x, y_1) - f(x, y_2)| \le L|y_1 - y_2|$$

for all $(x, y_1), (x, y_2) \in R$. Then the initial value problem

$$\frac{dy}{dx} = f(x, y), \quad y(x_0) = y_0$$

has a unique solution $y(x)$ on some interval $(x_0 - h, x_0 + h)$ where $h = \min\!\left(a,\, b/M_f\right)$ and $M_f = \sup_R |f|$.

The proof is constructive through Picard iteration. Define the sequence of functions

$$y_0(x) = y_0, \qquad y_{n+1}(x) = y_0 + \int_{x_0}^{x} f\!\left(t,\, y_n(t)\right) dt,$$

and demonstrate that this sequence is a Cauchy sequence in the Banach space $C([x_0 - h, x_0 + h])$ equipped with the supremum norm. The Lipschitz condition ensures the Picard operator $T[y](x) = y_0 + \int_{x_0}^x f(t, y(t))\, dt$ is a contraction on a suitable closed ball, and the Banach fixed-point theorem delivers a unique fixed point, which is exactly the solution. This iterative construction also yields the first meaningful approximation scheme: Picard iterates converge to the solution with exponentially decaying error, a fact that underpins numerical integration at the theoretical level.

The Lipschitz hypothesis is essential, not decorative. The equation $dy/dx = y^{1/2}$ with $y(0) = 0$ has two solutions on $[0,\infty)$: the identically zero function and $(x/2)^2$. Here $f(x,y) = y^{1/2}$ fails the Lipschitz condition at $y = 0$ because $\partial f/\partial y = \frac{1}{2}y^{-1/2}$ blows up there. Uniqueness fails precisely where the theorem's hypothesis fails, and this is not a coincidence.

---

### Separable Equations

The simplest structural property an ODE can have is separability. The equation $dy/dx = f(x,y)$ is *separable* if $f$ factors as

$$\frac{dy}{dx} = g(x)\, h(y)$$

for functions $g$ and $h$ depending only on their respective variables. The differential form of this equation is

$$h(y)^{-1}\, dy = g(x)\, dx,$$

and the core algebraic fact is that the variables have been cleanly separated onto opposite sides of the equation. Integration then yields the implicit solution

$$H(y) = G(x) + C, \quad \text{where } H'(y) = h(y)^{-1},\; G'(x) = g(x).$$

The formal manipulation of "moving $dx$ to the right-hand side" can be made rigorous. If $y(x)$ is a solution, then differentiating $H(y(x)) = G(x) + C$ with respect to $x$ via the chain rule gives $H'(y) \cdot y' = G'(x)$, which is exactly $h(y)^{-1} \cdot g(x) h(y) = g(x)$. The separation is not a heuristic; it is the chain rule run in reverse.

**Worked Example.** Solve the initial value problem

$$\frac{dy}{dx} = \frac{x}{y}, \quad y(0) = 2.$$

Separating variables: $y\, dy = x\, dx$. Integrating both sides:

$$\int y\, dy = \int x\, dx \implies \frac{y^2}{2} = \frac{x^2}{2} + C.$$

Applying $y(0) = 2$: $\frac{4}{2} = 0 + C$, so $C = 2$. The solution is $y^2 - x^2 = 4$, or on the branch containing $(0, 2)$:

$$y(x) = \sqrt{x^2 + 4}.$$

This is defined for all $x \in \mathbb{R}$, and $y(0) = 2$ is confirmed. Note that $f(x,y) = x/y$ is not Lipschitz near $y = 0$, so the Picard-Lindelöf theorem would apply only away from the $x$-axis — the solution curve we found, sitting at $y \ge 2$, is comfortably in a region where $f$ is smooth and Lipschitz.

---

### Linear First-Order Equations

A first-order ODE is *linear* if it has the form

$$\frac{dy}{dx} + P(x)\, y = Q(x).$$

The left-hand side is a linear operator acting on $y$: writing $L[y] = y' + P(x)y$, linearity means $L[\alpha y_1 + \beta y_2] = \alpha L[y_1] + \beta L[y_2]$. This algebraic structure implies the solution set of the homogeneous equation $L[y] = 0$ is a one-dimensional vector space, and any particular solution of the inhomogeneous equation, once found, generates the entire general solution by superposition.

The homogeneous equation $y' + P(x)y = 0$ is separable: $dy/y = -P(x)\, dx$, giving $y_h = C \exp\!\left(-\int P(x)\, dx\right)$. The key idea for the inhomogeneous case is *variation of parameters*: guess that the solution has the form $y = u(x) \exp\!\left(-\int P\, dx\right)$ where $u(x)$ is an unknown function. Substituting into the ODE:

$$u' e^{-\int P\, dx} - u P e^{-\int P\, dx} + P u e^{-\int P\, dx} = Q(x),$$

so $u' e^{-\int P\, dx} = Q(x)$, giving $u' = Q(x) e^{\int P\, dx}$. Thus

$$u(x) = \int Q(x)\, e^{\int P(x)\, dx}\, dx + C,$$

and the general solution is

$$y(x) = e^{-\int P(x)\, dx}\!\left[\int Q(x)\, e^{\int P(x)\, dx}\, dx + C\right].$$

This derivation will reappear in disguise when we develop integrating factors, because the function $\mu(x) = e^{\int P(x)\, dx}$ is precisely the integrating factor that converts the left-hand side of the linear equation into an exact derivative.

---

### Exact Equations

An equation $M\, dx + N\, dy = 0$ is *exact* if the 1-form $\omega = M\, dx + N\, dy$ is an exact differential, meaning there exists a function $F(x,y)$ — called a potential function — such that

$$dF = \frac{\partial F}{\partial x}\, dx + \frac{\partial F}{\partial y}\, dy = M\, dx + N\, dy.$$

This requires $\partial F/\partial x = M$ and $\partial F/\partial y = N$. The solution to the ODE is then $F(x,y) = C$ for constant $C$, because $dF = 0$ along any solution curve.

The necessary condition for exactness follows from the symmetry of mixed partial derivatives. If $F$ exists with continuous second partials, then

$$\frac{\partial M}{\partial y} = \frac{\partial^2 F}{\partial y\, \partial x} = \frac{\partial^2 F}{\partial x\, \partial y} = \frac{\partial N}{\partial x}.$$

On a simply connected domain, this condition is also sufficient: by the Poincaré lemma, $\partial M/\partial y = \partial N/\partial x$ on a simply connected open set implies $\omega$ is exact.

**Constructing the Potential Function.** Given $\partial M/\partial y = \partial N/\partial x$, the potential $F$ is built by integration. Integrate $\partial F/\partial x = M$ with respect to $x$, treating $y$ as a parameter:

$$F(x, y) = \int M(x, y)\, dx + g(y),$$

where $g(y)$ is an arbitrary function of $y$ alone (the "constant" of integration with respect to $x$). Then enforce $\partial F/\partial y = N$:

$$\frac{\partial}{\partial y}\int M\, dx + g'(y) = N(x,y) \implies g'(y) = N(x,y) - \frac{\partial}{\partial y}\int M\, dx.$$

The exactness condition guarantees the right-hand side depends only on $y$, so $g'(y)$ is well-defined and $g(y) = \int g'(y)\, dy$.

**Worked Example.** Solve $(2xy + 3)\, dx + (x^2 + 4y)\, dy = 0$.

Here $M = 2xy + 3$ and $N = x^2 + 4y$. Check exactness: $\partial M / \partial y = 2x$ and $\partial N / \partial x = 2x$. These are equal, so the equation is exact.

Integrate $M$ with respect to $x$:

$$F(x,y) = \int (2xy + 3)\, dx = x^2 y + 3x + g(y).$$

Enforce $\partial F/\partial y = N$:

$$x^2 + g'(y) = x^2 + 4y \implies g'(y) = 4y \implies g(y) = 2y^2.$$

The potential function is $F(x,y) = x^2 y + 3x + 2y^2$, and the general solution is

$$x^2 y + 3x + 2y^2 = C.$$

This is an implicit solution; in general it cannot be simplified to explicit form $y = y(x)$, and there is no reason to expect it to be. The implicit form is the natural answer to an exact equation.

---

### Integrating Factors as Symmetry-Restoring Operators

When $\partial M/\partial y \neq \partial N/\partial x$, the form $\omega = M\, dx + N\, dy$ is not exact, but it may become exact after multiplication by a carefully chosen function $\mu(x, y)$. Such a function is called an *integrating factor*. The equation

$$\mu M\, dx + \mu N\, dy = 0$$

is exact if and only if $\partial(\mu M)/\partial y = \partial(\mu N)/\partial x$, which expands to

$$\mu_y M + \mu M_y = \mu_x N + \mu N_x,$$

or equivalently

$$\mu(M_y - N_x) = \mu_x N - \mu_y M.$$

This is a PDE for $\mu$, generally harder to solve than the original ODE. The theory becomes tractable under special assumptions on the structure of the integrating factor.

**Case 1: $\mu = \mu(x)$ depends only on $x$.** Setting $\mu_y = 0$, the condition becomes $\mu(M_y - N_x) = \mu' N$, so

$$\frac{\mu'}{\mu} = \frac{M_y - N_x}{N}.$$

This is a separable ODE for $\mu$ with solution $\mu(x) = \exp\!\left(\int \frac{M_y - N_x}{N}\, dx\right)$, provided the right-hand side depends only on $x$.

**Case 2: $\mu = \mu(y)$ depends only on $y$.** Setting $\mu_x = 0$, the condition becomes $\mu_y M + \mu(M_y - N_x) = 0$, giving

$$\frac{\mu'}{\mu} = \frac{N_x - M_y}{M},$$

which must depend only on $y$.

The connection to linear equations is not coincidental. For the linear ODE written as $(P(x)y - Q(x))\, dx + dy = 0$, we have $M = Py - Q$, $N = 1$, so

$$\frac{M_y - N_x}{N} = \frac{P - 0}{1} = P(x).$$

The integrating factor for exactness is $\mu(x) = e^{\int P(x)\, dx}$, exactly what variation of parameters produced. Integrating factors for linear equations are not a trick; they are the specialization of the general theory of restoring exactness to the simplest structural case.

**Worked Example.** Solve $(y^2 - x)\, dx + 2y\, dy = 0$.

Here $M = y^2 - x$, $N = 2y$. Compute $M_y - N_x = 2y - 0 = 2y$. Then

$$\frac{M_y - N_x}{N} = \frac{2y}{2y} = 1,$$

which depends only on $x$. The integrating factor is $\mu(x) = e^{\int 1\, dx} = e^x$. Multiply through:

$$e^x(y^2 - x)\, dx + 2y e^x\, dy = 0.$$

This should now be exact. Verify: $\partial(e^x(y^2 - x))/\partial y = 2y e^x$ and $\partial(2ye^x)/\partial x = 2ye^x$. Confirmed. Now construct the potential:

$$F = \int 2ye^x\, dy = y^2 e^x + g(x).$$

Enforce $\partial F/\partial x = e^x(y^2 - x)$:

$$y^2 e^x + g'(x) = e^x y^2 - xe^x \implies g'(x) = -xe^x.$$

Integrate by parts: $g(x) = -xe^x + e^x = e^x(1 - x)$. Thus $F(x,y) = y^2 e^x + e^x(1-x) = e^x(y^2 + 1 - x)$, and the general solution is

$$y^2 + 1 - x = Ce^{-x}.$$

---

### Homogeneous Equations

An equation $dy/dx = f(x,y)$ is called *homogeneous* (in the classical ODE sense, not the linear algebra sense) if $f$ depends only on the ratio $y/x$, that is, $f(x,y) = g(y/x)$ for some function $g$. This scaling invariance — that $f(\lambda x, \lambda y) = f(x,y)$ for all $\lambda \neq 0$ — corresponds to the fact that $f$ is a homogeneous function of degree zero.

The substitution $v = y/x$, equivalently $y = vx$, transforms such an equation into a separable one. Differentiating $y = vx$ with respect to $x$ gives $dy/dx = v + xv'$, so

$$v + x\frac{dv}{dx} = g(v) \implies x\frac{dv}{dx} = g(v) - v.$$

This is separable: $\frac{dv}{g(v) - v} = \frac{dx}{x}$, which integrates (at least implicitly) to give $v$ as a function of $x$, and then $y = vx$ recovers the solution.

**Worked Example.** Solve $\frac{dy}{dx} = \frac{y^2 - x^2}{2xy}$.

Write $f(x,y) = \frac{y^2 - x^2}{2xy} = \frac{(y/x)^2 - 1}{2(y/x)} = g(v)$ where $v = y/x$. The equation is homogeneous. Substitute $y = vx$:

$$v + x\frac{dv}{dx} = \frac{v^2 - 1}{2v}.$$

Then:

$$x\frac{dv}{dx} = \frac{v^2 - 1}{2v} - v = \frac{v^2 - 1 - 2v^2}{2v} = \frac{-v^2 - 1}{2v}.$$

Separate: $\frac{2v}{v^2 + 1}\, dv = -\frac{dx}{x}$. Integrate both sides:

$$\ln(v^2 + 1) = -\ln|x| + C_1 \implies v^2 + 1 = \frac{K}{|x|}.$$

Resubstitute $v = y/x$:

$$\frac{y^2}{x^2} + 1 = \frac{K}{|x|} \implies y^2 + x^2 = K|x|.$$

This family of curves is a family of circles. The structure of the original equation encoded an underlying rotational symmetry that became visible once we applied the right substitution.

---

## 2. Core Architecture & Mechanics

The classification problem for a first-order ODE is not a matter of matching the equation to a list; it is a sequence of structural tests, each peeling away a layer of algebraic complexity. The following diagram depicts the decision logic as a flow through the equation's properties.

```mermaid
flowchart TD
    START["<b>Given:</b> M(x,y) dx + N(x,y) dy = 0<br/>(or equivalently: dy/dx = f(x,y))"]

    Q1{"Is f(x,y) = g(x)·h(y)?"}

    SEP["<b>SEPARABLE</b><br/>Integrate each side"]

    Q2{"Is f(x,y) = g(y/x)?"}

    HOM["<b>HOMOGENEOUS</b><br/>Sub v = y/x<br/>→ separable"]

    Q3{"Is ∂M/∂y = ∂N/∂x?"}

    EXACT["<b>EXACT</b><br/>Integrate for F(x,y)"]

    Q4{"Is equation linear in y?<br/>dy/dx + P(x)y = Q(x)"}

    LIN["<b>LINEAR</b><br/>μ = e^∫P dx<br/>Variation of parameters"]

    MU["<b>SEEK INTEGRATING FACTOR μ</b><br/>Test μ(x): (M_y − N_x) / N = φ(x)?<br/>Test μ(y): (N_x − M_y) / M = ψ(y)?"]

    START --> Q1
    Q1 -->|YES| SEP
    Q1 -->|NO|  Q2
    Q2 -->|YES| HOM
    Q2 -->|NO|  Q3
    Q3 -->|YES| EXACT
    Q3 -->|NO|  Q4
    Q4 -->|YES| LIN
    Q4 -->|NO|  MU
```

This decision tree is the operational skeleton of classical first-order ODE theory. Each branch corresponds not to an ad hoc trick but to a theorem: separable equations reduce to two independent quadratures by the chain rule; exact equations are solvable by the Poincaré lemma on simply connected domains; linear equations admit integrating factors by exponential construction; and homogeneous equations are separable after the scaling substitution.

**The Potential Function Construction in Detail.** For exact equations, the construction of $F$ proceeds in two phases that must be executed carefully to avoid algebraic error. Given $M\, dx + N\, dy = 0$ with $M_y = N_x$, integrate $M$ with respect to $x$ to obtain $F(x,y) = \int M\, dx + g(y)$. This integral is performed with $y$ held constant. The function $g(y)$ absorbs all $y$-dependence not captured by integrating $M$ horizontally. It is determined by differentiating the intermediate $F$ with respect to $y$ and setting the result equal to $N$, which produces an ODE $g'(y) = N - \partial_y \int M\, dx$ whose right-hand side, guaranteed by exactness, is a pure function of $y$.

The two-phase construction can be visualized as follows. The domain is a region of the $(x,y)$-plane. Integrating $M$ with respect to $x$ sweeps horizontal paths from some base point $(x_0, y)$, accumulating contributions from the $dx$-component of the form. The correction function $g(y)$ then accounts for the residual $dy$-component along the vertical axis. Together they construct the unique (up to constant) potential $F$ whose level curves are the solution trajectories.

**Phase-Line Analysis for Autonomous Equations.** When the ODE takes the autonomous form

$$\frac{dy}{dx} = f(y),$$

there is no explicit $x$-dependence, and the dynamics are entirely governed by the zeros and signs of $f$. The *phase line* is the $y$-axis together with the annotation: mark each zero of $f$ as an equilibrium point, draw upward arrows where $f(y) > 0$ (the solution is increasing), and downward arrows where $f(y) < 0$ (the solution is decreasing).

An equilibrium $y^* = c$ where $f(c) = 0$ is *stable* (attracting) if $f'(c) < 0$, because solutions above $c$ have negative slope and fall toward $c$, while solutions below $c$ have positive slope and rise toward $c$. Conversely, $y^*$ is *unstable* (repelling) if $f'(c) > 0$. The case $f'(c) = 0$ requires higher-order analysis.

Consider the autonomous logistic equation

$$\frac{dy}{dx} = ry\!\left(1 - \frac{y}{K}\right),$$

where $r, K > 0$. Here $f(y) = ry(1 - y/K)$ has zeros at $y = 0$ and $y = K$. For $0 < y < K$, $f(y) > 0$, so solutions increase. For $y > K$, $f(y) < 0$, so solutions decrease toward $K$. For $y < 0$, $f(y) < 0$. Thus $y = K$ is a stable equilibrium and $y = 0$ is an unstable equilibrium. This conclusion is obtained entirely from the phase line, without solving the equation explicitly. The explicit solution, obtained by separating variables and partial fractions, is

$$y(x) = \frac{K y_0 e^{rx}}{K + y_0(e^{rx} - 1)},$$

which confirms the phase-line prediction: for all $y_0 > 0$, $\lim_{x\to\infty} y(x) = K$.

**Bernoulli Equations as a Bridge.** The Bernoulli equation

$$\frac{dy}{dx} + P(x)y = Q(x)y^n, \quad n \neq 0, 1,$$

is nonlinear but reduces to a linear equation via the substitution $v = y^{1-n}$. Computing $v' = (1-n)y^{-n}y'$ and substituting:

More cleanly: dividing the Bernoulli equation by $y^n$ gives $y^{-n}y' + P(x)y^{1-n} = Q(x)$. Setting $v = y^{1-n}$ so that $v' = (1-n)y^{-n}y'$:

$$\frac{v'}{1-n} + P(x)v = Q(x) \implies v' + (1-n)P(x)v = (1-n)Q(x).$$

This is linear in $v$ and is solved by the standard integrating factor $\mu = e^{(1-n)\int P\, dx}$. The Bernoulli equation is therefore not a separate class but a linearizable perturbation of the linear class, illustrating how the taxonomy of ODEs is not flat but hierarchical.

---

## 3. High-Performance Optimization & Failure Modes

### Exactness Testing Before Computing

A practitioner who attempts to construct the potential function $F$ before verifying exactness wastes substantial effort and often generates nonsensical intermediate expressions. The exactness test $\partial M/\partial y = \partial N/\partial x$ must be the first computation performed on any candidate exact equation. This test is $O(1)$ in the sense that it requires only two partial differentiations, whereas constructing $F$ requires at minimum two integrations and a system of comparisons. The asymmetry in cost is large. Develop the habit of testing before constructing.

### Domain Topology and Potential Functions

The Poincaré lemma guarantees that $M_y = N_x$ implies exactness *on a simply connected domain*. This hypothesis is not vacuous. Consider the 1-form

$$\omega = \frac{-y\, dx + x\, dy}{x^2 + y^2}$$

on the punctured plane $\mathbb{R}^2 \setminus \{(0,0)\}$. Here $M = -y/(x^2+y^2)$ and $N = x/(x^2+y^2)$. Computing:

$$\frac{\partial M}{\partial y} = \frac{y^2 - x^2}{(x^2+y^2)^2}, \quad \frac{\partial N}{\partial x} = \frac{y^2 - x^2}{(x^2+y^2)^2}.$$

The test passes everywhere on the punctured plane. Yet $\omega = d\theta$ where $\theta = \arctan(y/x)$ is the polar angle — a function that cannot be defined continuously on all of $\mathbb{R}^2 \setminus \{(0,0)\}$ because the punctured plane is not simply connected. Any closed loop encircling the origin accumulates $2\pi$, not zero. On any simply connected subdomain (a half-plane, for instance), a genuine potential exists; globally it does not. The practitioner must specify the domain when asserting that an equation is exact and a potential exists.

### Integrating Factor Existence Obstructions

Not every non-exact equation admits an integrating factor $\mu(x)$ or $\mu(y)$. The test $(M_y - N_x)/N = \phi(x)$ may fail to yield a function of $x$ alone. When both single-variable tests fail, the equation may still admit an integrating factor of a different form — for example, $\mu = \mu(xy)$ or $\mu = \mu(x^2 + y^2)$ — but finding it requires guessing the functional form and solving the resulting compatibility condition, a process that is more art than algorithm. The honest assessment is that the class of ODEs solvable by elementary integrating factors is strictly smaller than the class of all first-order ODEs, and recognizing the boundary of tractability prevents wasted effort.

### Singular Solutions and Divisibility Pitfalls

Separating variables requires dividing by $h(y)$, and this division silently discards any value $y_c$ where $h(y_c) = 0$. Such values, when constant, are equilibrium solutions of the autonomous reduction $y' = g(x) h(y)$, and they may or may not be recoverable from the general solution by a limiting argument. For instance, in $dy/dx = y^2$, separating gives $y^{-2}\, dy = dx$, integrated to $-y^{-1} = x + C$, or $y = -1/(x+C)$. The value $y = 0$ was divided away; it satisfies the ODE directly ($0 = 0^2$) but is not recovered from the general solution for any finite $C$. It is a *singular solution*, and forgetting it produces an incomplete solution set. Whenever $h(y) = 0$ admits roots, check each root as a candidate constant solution after completing the separation.

### Picard Iteration as a Practical Approximation Scheme

For equations where no closed form is available, the Picard iterates are not merely a theoretical existence proof; they are a computable approximation scheme. Starting from $y_0(x) = y_0$, the first iterate

$$y_1(x) = y_0 + \int_{x_0}^x f(t, y_0)\, dt$$

is explicitly computable and coincides with the Taylor expansion of the true solution to first order in $x - x_0$. The $n$-th iterate matches the Taylor expansion to order $n$ under sufficient smoothness, converging uniformly on $[x_0 - h, x_0 + h]$ at a rate controlled by $(Lh)^n / n!$. This exponential convergence makes the scheme practically efficient when $Lh$ is moderately small. For stiff equations — where $L$ is very large and forces $h$ to be tiny for convergence — Picard iteration degrades, motivating implicit numerical schemes that lie beyond the scope of this lesson but whose theoretical necessity is now visible from the structure of the existence proof.

### Autonomous Equations and Finite-Time Blowup

The equation $dy/dx = y^2$ with $y(0) = 1$ has the explicit solution $y = 1/(1-x)$, which blows up at $x = 1$. The Picard-Lindelöf theorem guarantees existence only on an interval, and that interval may be strictly bounded even when $f$ is smooth everywhere away from the singularity. Finite-time blowup is not a failure of the theory; it is a genuine feature of the solution. The phase-line perspective makes this visible for autonomous equations: when $f(y) > 0$ and $f$ grows faster than linearly in $y$ (e.g., $f(y) = y^2$), solutions escape to infinity in finite $x$-time, because the integral $\int_{y_0}^\infty dy/f(y)$ converges. This integral convergence criterion — the *finite-time blowup test* — is a direct consequence of the separable structure of autonomous equations and provides a sharp diagnostic for escape behavior.

Specifically, for $dy/dx = f(y)$, the time to reach infinity from $y_0 > 0$ is $\int_{y_0}^\infty dy/f(y)$. For $f(y) = y^p$ with $p > 1$, this integral is $\frac{y_0^{1-p}}{p-1} < \infty$. For $f(y) = y$ (linear growth), the integral diverges and solutions grow without bound only as $x \to \infty$. The transition at $p = 1$ marks the boundary between finite-time blowup and infinite-time growth, a structural threshold visible entirely from the phase line and the convergence of a single improper integral.

### The Role of Smooth Dependence on Initial Conditions

A consequence of the Picard-Lindelöf proof that is often overlooked in first exposure is that the solution $y(x; x_0, y_0)$ depends smoothly on the initial condition $y_0$ when $f$ is smooth in $y$. This follows because the Picard operator, viewed as a map on the space of initial conditions, is differentiable. The derivative of $y$ with respect to $y_0$, denoted $\Phi(x) = \partial y/\partial y_0$, satisfies the *variational equation*

$$\frac{d\Phi}{dx} = f_y(x, y(x))\, \Phi, \quad \Phi(x_0) = 1,$$

which is a linear ODE for $\Phi$ and can always be solved once the solution $y(x)$ is known. This smooth dependence is the mathematical foundation of sensitivity analysis and perturbation theory, and it means that the solution map $y_0 \mapsto y(x; x_0, y_0)$ is a diffeomorphism for each fixed $x$ in the interval of existence — a fact of central importance in the geometric theory of ODEs and in the study of flows on manifolds that the later lessons in this curriculum will develop in full.
