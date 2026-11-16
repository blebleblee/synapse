# Lesson 5: Discrete Dynamical Systems, Iterated Maps, Recurrence

## 1. First-Principles Intuition & Invariants

The study of dynamical systems begins with a deceptively simple question: given a rule that transforms a state into a new state, what happens when that rule is applied again and again, indefinitely? This is the central engine of discrete dynamics. Unlike its continuous counterpart, governed by differential equations and smooth flows, the discrete-time world operates through iteration — the repeated application of a single map — and its behavior is at once more combinatorially rigid and more wildly unpredictable than the continuous case might suggest.

Formally, a **discrete dynamical system** is a pair $(X, f)$ where $X$ is a set (the phase space) and $f: X \to X$ is a map. The orbit of a point $x_0 \in X$ is the sequence

$$x_0,\; x_1 = f(x_0),\; x_2 = f(x_1) = f^2(x_0),\; \ldots,\; x_n = f^n(x_0),$$

where $f^n$ denotes the $n$-fold composition of $f$ with itself. The central objects of study are the long-run fates of these orbits: do they converge to a fixed point, settle into a periodic cycle, wander densely through the space, or exhibit sensitive dependence on initial conditions?

A point $p \in X$ is a **fixed point** of $f$ if $f(p) = p$. It is a **periodic point of period $n$** if $f^n(p) = p$ and $n$ is the smallest such positive integer; the orbit $\{p, f(p), f^2(p), \ldots, f^{n-1}(p)\}$ is called a **periodic orbit** or $n$-cycle. The stability of a fixed point in the smooth setting, say $X \subseteq \mathbb{R}$ and $f$ differentiable, is governed by the **multiplier** $\lambda = f'(p)$. When $|\lambda| < 1$, the fixed point is **asymptotically stable** (attracting): nearby orbits converge to $p$ exponentially fast. When $|\lambda| > 1$, it is **unstable** (repelling): nearby orbits diverge from $p$ at an exponential rate. The boundary case $|\lambda| = 1$ requires higher-order analysis and is where the most interesting bifurcations live.

To make this concrete, consider the **linear recurrence** $x_{n+1} = \lambda x_n$ with initial condition $x_0$. Its solution is $x_n = \lambda^n x_0$, a geometric sequence. For $|\lambda| < 1$, every orbit converges to the fixed point $0$; for $|\lambda| > 1$, every nonzero orbit diverges. This trivial system is the prototype for local linearization near any hyperbolic fixed point: the Hartman-Grobman theorem (in its discrete form) guarantees that near a fixed point where $|f'(p)| \neq 1$, the dynamics of $f$ are topologically conjugate to the linear map $x \mapsto f'(p) \cdot x$. Conjugacy is the right equivalence relation: two systems $(X, f)$ and $(Y, g)$ are **topologically conjugate** if there exists a homeomorphism $h: X \to Y$ such that $h \circ f = g \circ h$. Conjugacy preserves every dynamical property that is topological in nature — period lengths, orbit structure, entropy — and it is the primary tool for classifying systems up to qualitative equivalence.

### Difference Equations and Linear Theory

A **linear recurrence relation** of order $k$ takes the form

$$x_{n+k} = a_{k-1} x_{n+k-1} + a_{k-2} x_{n+k-2} + \cdots + a_0 x_n,$$

and its solution theory is an exact parallel of the theory of linear ODEs with constant coefficients. One associates the **characteristic polynomial**

$$p(\lambda) = \lambda^k - a_{k-1}\lambda^{k-1} - \cdots - a_0,$$

and the general solution is a linear combination of terms of the form $\lambda_i^n$ for each distinct root $\lambda_i$, with polynomial modifications when roots repeat. The Fibonacci sequence illustrates this beautifully. With $x_{n+2} = x_{n+1} + x_n$, the characteristic polynomial is $\lambda^2 - \lambda - 1 = 0$, whose roots are the golden ratio $\phi = (1 + \sqrt{5})/2$ and its conjugate $\hat{\phi} = (1 - \sqrt{5})/2$. The unique solution with $x_0 = 0, x_1 = 1$ is Binet's formula:

$$x_n = \frac{\phi^n - \hat{\phi}^n}{\sqrt{5}}.$$

Since $|\hat{\phi}| < 1$, we have $x_n \sim \phi^n / \sqrt{5}$ for large $n$, meaning Fibonacci numbers grow exponentially at rate $\phi$. The ratio $x_{n+1}/x_n \to \phi$ is itself a dynamical statement: the orbit of the ratio converges to the fixed point $\phi$ of the Möbius transformation $r \mapsto 1 + 1/r$.

For nonlinear systems, closed-form solutions are the exception rather than the rule. The apparatus of local analysis — linearization, multipliers, Lyapunov functions — gives local information, but the global orbit structure demands a different toolkit: invariant sets, topological entropy, symbolic dynamics, and the combinatorial theorems that govern the coexistence of periodic orbits.

### The Logistic Map: A Complete Case Study

The **logistic map** $f_\mu: [0,1] \to [0,1]$ defined by

$$f_\mu(x) = \mu x(1-x), \quad \mu \in [0,4],$$

is the canonical example of a one-dimensional discrete dynamical system exhibiting the full spectrum of behavior from trivial fixed-point convergence to fully developed chaos. Its origins in population biology — $x_n$ represents a normalized population and $\mu$ is a growth rate — belie its mathematical depth, but the map has become the standard laboratory for the phenomenon of **period-doubling bifurcation**.

For $\mu \in (0,1)$, the only fixed point in $[0,1]$ is $x^* = 0$, and it is globally attracting: every orbit converges to extinction. At $\mu = 1$, a bifurcation occurs. For $\mu \in (1,3)$, the nonzero fixed point

$$x^*(\mu) = 1 - \frac{1}{\mu}$$

is born and is asymptotically stable, since the multiplier $f'_\mu(x^*) = 2 - \mu$ satisfies $|2 - \mu| < 1$ for $\mu \in (1,3)$.

At $\mu = 3$, this fixed point loses stability because $f'_\mu(x^*) = -1$. A **period-2 orbit** is born through a **period-doubling bifurcation** (also called a flip bifurcation). To find the 2-cycle explicitly, one solves $f^2_\mu(x) = x$ while excluding the fixed points of $f_\mu$ itself. The map $f^2_\mu(x) = f_\mu(f_\mu(x))$ is a degree-4 polynomial, and after factoring out the fixed-point roots $(x = 0$ and $x = x^*(\mu))$, the remaining quadratic yields the 2-cycle points

$$p_{1,2} = \frac{(\mu+1) \pm \sqrt{(\mu+1)(\mu-3)}}{2\mu}.$$

These are real for $\mu > 3$, confirming the bifurcation point. The multiplier of the 2-cycle is $(f^2_\mu)'(p_1) = f'_\mu(p_2) \cdot f'_\mu(p_1)$ by the chain rule, and stability analysis of this product shows the 2-cycle is stable for $\mu \in (3, 1+\sqrt{6}) \approx (3, 3.449)$.

This cascade repeats: the 2-cycle undergoes a flip bifurcation at $\mu = 1 + \sqrt{6}$, spawning a stable 4-cycle, which spawns an 8-cycle, and so on. The bifurcation values $\mu_k$ at which the $2^k$-cycle is born accumulate at the **Feigenbaum point** $\mu_\infty \approx 3.56995$, with the ratios converging at a universal rate:

$$\lim_{k \to \infty} \frac{\mu_k - \mu_{k-1}}{\mu_{k+1} - \mu_k} = \delta \approx 4.66920\ldots$$

This is the **Feigenbaum constant** $\delta$, and its universality — it arises identically in every smooth unimodal map with a quadratic critical point — is one of the profound discoveries of twentieth-century dynamics, explained by the renormalization group theory of Mitchell Feigenbaum and independently by Pierre Coullet and Charles Tresser. Beyond $\mu_\infty$, the system enters a regime mixing periodic windows with chaotic intervals, culminating at $\mu = 4$ in a fully chaotic map topologically conjugate (via $x = \sin^2(\pi\theta/2)$) to the **tent map** $T(\theta) = 1 - |2\theta - 1|$.

---

## 2. Core Architecture & Mechanics

### Poincaré Maps and the Reduction of Flows

While this lesson is fundamentally about discrete systems, it is important to understand why discrete maps appear naturally in the study of continuous flows. Consider a continuous-time system $\dot{x} = F(x)$ on a manifold $M$ of dimension $n$. If the flow admits a **periodic orbit** $\gamma$, one can choose a codimension-1 submanifold $\Sigma \subset M$ (a **surface of section** or **Poincaré section**) that the orbit $\gamma$ crosses transversally. Each time a trajectory passes through $\Sigma$, it defines a new point, and the map

$$P: \Sigma \to \Sigma, \quad x \mapsto \text{(next intersection of the trajectory through } x \text{ with } \Sigma),$$

is the **Poincaré return map**. The continuous-time dynamics near $\gamma$ reduce to the discrete-time dynamics of $P$ near the fixed point $p = \gamma \cap \Sigma$. This reduction trades an $n$-dimensional continuous system for an $(n-1)$-dimensional discrete one, which is both computationally tractable and structurally cleaner. The eigenvalues of $DP(p)$ — called the **characteristic multipliers** of $\gamma$ — determine its stability: $\gamma$ is asymptotically stable if all multipliers lie strictly inside the unit circle.

The diagram below sketches this reduction schematically. The periodic orbit $\gamma$ (the loop) punctures the section $\Sigma$ at $p$; nearby trajectories trace out the action of $P$.

```
        Continuous Flow (3D)         Poincaré Map (2D section Σ)
        ─────────────────────         ─────────────────────────────
              ╭─────╮
           ╭─→  γ   ─→╮               p  ──P──→  P(p) = p
          │  (periodic │                   ↑
          │   orbit)   │             near │  trajectories
          ╰────────────╯             orbits spiral inward
                │                   if |λ_i| < 1 for all multipliers
           cuts Σ at p
```

This construction places the logistic map, the circle map, and every other discrete system we study in a unified framework: they either arise as Poincaré maps of natural flows, or they serve as model systems whose dynamics illuminate the behavior of the full flow.

### Circle Maps and the Rotation Number

A **circle map** is a continuous map $f: S^1 \to S^1$. Working with the universal cover, we lift $f$ to a map $F: \mathbb{R} \to \mathbb{R}$ satisfying $F(x+1) = F(x) + d$ where $d \in \mathbb{Z}$ is the **degree** of $f$. For degree-1 maps (the case of physical interest, arising in models of coupled oscillators and cardiac rhythms), $F(x+1) = F(x)+1$, and the **rotation number** is defined by

$$\rho(f) = \lim_{n \to \infty} \frac{F^n(x) - x}{n}.$$

This limit exists and is independent of $x$ (for degree-1 maps): this is a theorem, not an assumption. The rotation number $\rho(f) \in [0,1]$ captures the average angular advance per iterate. When $\rho(f) = p/q$ is rational, every orbit is eventually periodic with period $q$. When $\rho(f)$ is irrational, the dynamics depend on the regularity of $f$: for a pure **rigid rotation** $R_\alpha: x \mapsto x + \alpha \pmod{1}$, every orbit is dense in $S^1$ (by Weyl's equidistribution theorem), and $f$ is minimal. For a general $C^1$ map with irrational rotation number, Denjoy's theorem guarantees that if $f$ is $C^1$ with $\log f'$ of bounded variation, then $f$ is topologically conjugate to $R_\alpha$ — meaning all orbits are dense and the dynamics are uniquely ergodic.

The standard family of circle maps provides a concrete parameter space to explore. Define

$$F_{\Omega,K}(x) = x + \Omega - \frac{K}{2\pi}\sin(2\pi x),$$

the lift of a degree-1 circle map parameterized by the bare frequency $\Omega \in [0,1]$ and coupling strength $K \geq 0$. At $K = 0$, this is a pure rotation with $\rho = \Omega$. For $K > 0$, the map becomes nonlinear, and the rotation number becomes a nontrivial function of $(\Omega, K)$. The parameter space organizes itself into **Arnold tongues**: for each rational $p/q$, there is a region $T_{p/q}$ in the $(\Omega, K)$ plane on which $\rho = p/q$. At $K=0$ these tongues collapse to the single points $\{\Omega = p/q\}$; for $K > 0$ they open into wedge-shaped regions. The complement of the union of all tongues — the set of parameter values with irrational rotation number — has positive measure for $K < 1$ but zero measure for $K = 1$, the critical line at which the map becomes a homeomorphism only barely (it fails to be a diffeomorphism at the inflection points). The devil's staircase structure of $\rho(\Omega)$ at fixed $K$ is a **Cantor function**: nonconstant, continuous, with zero derivative almost everywhere, and taking rational values on a dense open set of full measure.

Computing $\rho$ for a given $(f, x_0)$ numerically requires discarding a transient and averaging:

$$\rho_N(x_0) = \frac{F^N(x_0) - x_0}{N}.$$

Convergence is fast when $\rho$ is rational (exponential in $N$) but slow when $\rho$ is irrational (like $O(1/N)$ in the worst case, faster for smooth maps by Fourier methods).

### Sarkovskii's Theorem: The Combinatorial Miracle

Among all results in one-dimensional discrete dynamics, Sarkovskii's theorem stands apart for the sheer improbability of its statement. Oleksandr Sharkovskii proved it in 1964, though it did not receive wide Western attention until the 1975 paper "Period Three Implies Chaos" by Li and Yorke, which rediscovered its most striking corollary.

Define the **Sarkovskii ordering** on the positive integers as follows. Write every positive integer uniquely as $n = 2^k m$ where $m$ is odd. Then order the positive integers as:

$$3 \surhd 5 \surhd 7 \surhd 9 \surhd \cdots \surhd 2 \cdot 3 \surhd 2 \cdot 5 \surhd 2 \cdot 7 \surhd \cdots \surhd 4 \cdot 3 \surhd 4 \cdot 5 \surhd \cdots \surhd 2^3 \surhd 2^2 \surhd 2 \surhd 1.$$

That is: first all odd numbers greater than 1 in increasing order, then 2 times all odd numbers greater than 1 in increasing order, then 4 times all odd numbers, and so on, with the pure powers of 2 in decreasing order ($\ldots, 8, 4, 2, 1$) at the very end.

**Sarkovskii's Theorem.** Let $f: \mathbb{R} \to \mathbb{R}$ be continuous, and suppose $f$ has a periodic point of period $m$. Then $f$ has a periodic point of period $n$ for every $n$ such that $m \surhd n$ in the Sarkovskii ordering.

The corollary is immediate and spectacular: if $f$ has a periodic point of period 3, then $f$ has periodic points of every positive integer period. The converse is also true: for every initial segment of the Sarkovskii ordering, there exists a continuous map realizing exactly that set of periods. Period 3 sits at the very top of the ordering, so its existence implies maximal combinatorial complexity.

The proof of Sarkovskii's theorem is constructive and uses only the **intermediate value theorem** (IVT), which makes it available for any continuous map on a real interval. The core mechanism is the existence of a chain of intervals whose images cover one another. We sketch the argument for the case $m = 3$ fully, then describe the general inductive structure.

**Lemma (IVT Covering).** Let $I$ and $J$ be closed intervals with $f(I) \supseteq J$. Then $f$ has a fixed point in $I$, and for any finite sequence $I_0, I_1, \ldots, I_{n-1}$ of closed intervals with $f(I_k) \supseteq I_{k+1}$ for each $k$ (indices mod $n$), there exists a point $x \in I_0$ such that $f^k(x) \in I_k$ for all $k$.

*Proof.* For the fixed-point claim: since $f(I) \supseteq J \supseteq I$ (taking $J = I$), consider $g(x) = f(x) - x$ on $I = [a,b]$. Then $f(a) \leq a$ and $f(b) \geq b$ (or vice versa, by surjectivity onto $I$), so by IVT there exists $c \in [a,b]$ with $f(c) = c$. For the orbit claim, one builds subintervals inductively: given $I_0$, the preimage $f^{-1}(I_1) \cap I_0$ is nonempty by the covering assumption and IVT, yielding a subinterval $I_0' \subseteq I_0$ with $f(I_0') = I_1$. Continuing, one finds a nested sequence of compact sets whose intersection is the desired point. $\square$

**Proof that period 3 implies all periods.** Let $f$ have a 3-cycle $a < b < c$ with, say, $f(a) = b$, $f(b) = c$, $f(c) = a$ (the other case $f(a) = c, f(c) = b, f(b) = a$ is symmetric). Set $I = [a,b]$ and $J = [b,c]$. Then:

- $f(I) = f([a,b]) \supseteq [b,c] = J$ because $f(a) = b$ and $f(b) = c$ and $f$ is continuous.
- $f(J) = f([b,c]) \supseteq [a,c] \supseteq I \cup J$ because $f(b) = c$ and $f(c) = a$ and $f$ is continuous.

In particular, $f(J) \supseteq I$ and $f(J) \supseteq J$. For $n \geq 2$, consider the covering chain $J \to J \to \cdots \to J \to I \to J$ where $J$ appears $n-1$ times and then $I$ appears once and then $J$ closes the loop. More precisely:

$$J \xrightarrow{f} J \xrightarrow{f} \cdots \xrightarrow{f} J \xrightarrow{f} I \xrightarrow{f} J.$$

By the lemma, there exists a point $x_0 \in J$ such that $f^k(x_0) \in J$ for $k = 0, \ldots, n-2$, then $f^{n-1}(x_0) \in I$, and $f^n(x_0) \in J \ni x_0$. So $f^n(x_0) = x_0$ by the fixed-point application of the lemma to the final $I \to J$ step. The fact that the period of $x_0$ is exactly $n$ (not a proper divisor) requires showing that $x_0$ does not land in $I$ before step $n-1$, which follows from the choice of chain: for the first $n-1$ steps, $x_0$ is confined to $J$, and the fixed points and 2-cycles in $J$ are accounted for by the lower part of the Sarkovskii ordering. The full inductive argument handles all periods in the ordering. $\square$

The power of Sarkovskii's theorem lies in what it says about the **orbit combinatorics** of a map from pure topological data. It is fundamentally a one-dimensional result: in two or more dimensions, a periodic orbit of period 3 does not force all other periods, as simple rotations in $\mathbb{R}^2$ demonstrate. The correct higher-dimensional generalization involves braid types and the Nielsen-Thurston classification of surface homeomorphisms, a considerably deeper theory.

### Julia Sets and the Architecture of Complex Dynamics

We now pass from the real line to the complex plane, where the iteration of rational maps acquires a geometric richness encoded in **Julia sets** and **Fatou sets**. Let $f: \hat{\mathbb{C}} \to \hat{\mathbb{C}}$ be a rational map of degree $d \geq 2$ on the Riemann sphere, the most studied family being the quadratic family $f_c(z) = z^2 + c$ for $c \in \mathbb{C}$.

The **Fatou set** $\mathcal{F}(f)$ is the largest open set on which the family of iterates $\{f^n\}$ is **equicontinuous** (equivalently, **normal** in the sense of Montel's theorem). The **Julia set** $\mathcal{J}(f) = \hat{\mathbb{C}} \setminus \mathcal{F}(f)$ is its complement, a nonempty perfect compact set that is completely invariant: $f(\mathcal{J}) = f^{-1}(\mathcal{J}) = \mathcal{J}$.

To understand why the Julia set is the locus of chaotic behavior, recall Montel's theorem: a family of holomorphic functions is normal on a domain $U$ if and only if it omits at least two values from $\hat{\mathbb{C}}$ on $U$. On the Fatou set, nearby orbits remain close; on the Julia set, the iterates are hypersensitive to perturbation, and this sensitivity is uniform. More precisely:

**Theorem (Density of repelling periodic points).** The repelling periodic points of $f$ are dense in $\mathcal{J}(f)$.

This is an extraordinary structural result: the Julia set, however fractal its geometry, is the closure of an explicitly defined countable set. The repelling periodic points are those with $|(f^n)'(p)| > 1$; they are dense, but the attracting periodic points (those with $|(f^n)'(p)| < 1$) lie in the Fatou set.

For $f_c(z) = z^2 + c$, the **critical point** is $z_0 = 0$ (where $f_c'(0) = 0$). The behavior of the critical orbit $0, c, c^2 + c, \ldots$ completely determines the topology of $\mathcal{J}(f_c)$ through a dichotomy: either the critical orbit remains bounded (in which case $\mathcal{J}(f_c)$ is connected) or it escapes to infinity (in which case $\mathcal{J}(f_c)$ is totally disconnected, a Cantor set). The **Mandelbrot set** $\mathcal{M}$ is the set of parameters $c \in \mathbb{C}$ for which the critical orbit is bounded:

$$\mathcal{M} = \{c \in \mathbb{C} : f_c^n(0) \not\to \infty \text{ as } n \to \infty\}.$$

This is not merely a numerical definition; it has deep structural properties. The main cardioid of $\mathcal{M}$ is the set of $c$ for which $f_c$ has an attracting fixed point, parameterized by the multiplier $\lambda \in \mathbb{D}$ (the open unit disk) via $c = \lambda/2 - \lambda^2/4$. The period-2 bulb attached to the cardioid corresponds to the attracting 2-cycle born at $c = -3/4$, and each further bulb corresponds to a higher period — a precise reflection of the period-doubling cascade we computed for the logistic map (to which $f_c$ is conjugate on the real axis via $x = 2 + 4(z - 1/2)/c$ when $c \in [-2, 1/4]$, up to rescaling).

**Computing the Julia set.** For a point $z \in \mathbb{C}$, one determines membership in $\mathcal{J}(f_c)$ via the **escape time algorithm**. Since $|f_c^n(z)| \to \infty$ if and only if the orbit eventually exceeds the escape radius $R = 2$ (a standard result whose proof uses the fact that $|z| > 2$ implies $|f_c(z)| > |z|$), one iterates:

$$z_0 = z, \quad z_{n+1} = z_n^2 + c,$$

and declares $z$ to have **escaped** at step $N$ if $|z_N| > 2$ for the first time. Points that never escape belong (approximately) to the **filled Julia set** $\mathcal{K}(f_c) = \{z : f_c^n(z) \not\to \infty\}$, whose boundary is $\mathcal{J}(f_c)$. The coloring of escape times gives the characteristic halo-like visualization of the Mandelbrot set's complement.

A finer invariant is the **Green's function** (Böttcher coordinate). For $|c| < 2$, there exists a conformal isomorphism $\phi_c: \hat{\mathbb{C}} \setminus \mathcal{K}(f_c) \to \hat{\mathbb{C}} \setminus \overline{\mathbb{D}}$ satisfying $\phi_c(f_c(z)) = \phi_c(z)^2$, intertwining $f_c$ with $z \mapsto z^2$ on the Riemann sphere. The **potential function** $G_c(z) = \log|\phi_c(z)|$ satisfies $G_c(f_c(z)) = 2 G_c(z)$, is harmonic on $\hat{\mathbb{C}} \setminus \mathcal{K}(f_c)$, and measures the speed of escape. The level sets of $G_c$ are the **equipotential curves** of the Julia set, and the gradient field lines of $G_c$ are the **external rays**, which play a fundamental role in the combinatorial encoding of the Mandelbrot set.

The external ray at angle $\theta \in \mathbb{R}/\mathbb{Z}$ under the map $f_c$ satisfies the **doubling map** on angles: the ray at angle $\theta$ maps to the ray at angle $2\theta \pmod{1}$. This converts the problem of understanding the combinatorics of $f_c$ into the problem of understanding the dynamics of the **angle-doubling map** $D: \theta \mapsto 2\theta \pmod{1}$ — itself a simple discrete dynamical system whose periodic points of period $n$ are the rationals with denominator $2^n - 1$, dense in $S^1$. The landing theorem (Douady and Hubbard's fundamental result) states that every rational external ray lands at a well-defined point of $\mathcal{J}(f_c)$, and the combinatorial pattern of ray landings encodes the topology of the Julia set completely.

---

## 3. High-Performance Optimization & Failure Modes

### Numerical Analysis of Orbits: Precision, Transients, and Shadowing

Iterating a map on a computer is a seemingly straightforward task, but it conceals several pitfalls that can produce deeply misleading results. Understanding these failure modes is not peripheral to the mathematics; it is part of the practitioner's discipline, and the corrective theorems are themselves beautiful.

The first issue is **floating-point orbit divergence**. The logistic map at $\mu = 4$ is chaotic, with Lyapunov exponent $\lambda_{\text{Lyap}} = \log 2 \approx 0.693$. This means two orbits starting at points separated by $\epsilon$ will diverge to distance of order 1 after roughly $n^* \approx (\log \epsilon^{-1}) / (\log 2)$ steps. For double-precision arithmetic ($\epsilon \approx 10^{-16}$), this gives $n^* \approx 53$ steps — after which the computed orbit bears no relationship to any true orbit starting at $x_0$. The standard response is the **shadowing lemma**, which provides a corrective guarantee in the other direction.

**Shadowing Lemma (Bowen-Anosov).** Let $f: M \to M$ be a diffeomorphism with a **hyperbolic** invariant set $\Lambda$ (meaning the tangent bundle over $\Lambda$ splits into uniformly contracting and expanding directions for $Df$). For every $\epsilon > 0$, there exists $\delta > 0$ such that every $\delta$**-pseudo-orbit** (a sequence $\{x_n\}$ with $d(x_{n+1}, f(x_n)) < \delta$ for all $n$) is $\epsilon$**-shadowed** by a true orbit: there exists $y$ with $d(f^n(y), x_n) < \epsilon$ for all $n$.

A floating-point computation produces a pseudo-orbit because each step introduces a rounding error of size at most machine epsilon $\epsilon_{\text{mach}}$. The shadowing lemma then guarantees that this pseudo-orbit, though not the orbit of any specific point, accurately tracks the orbit of some true point nearby. The numerical simulation is therefore not measuring the dynamics of a specific initial condition, but it is faithfully capturing a true trajectory of the system. This epistemological point is critical: chaotic systems are not "numerically unreliable" in the sense of being meaningless; they are reliable for statistical and ergodic statements (time averages, Lyapunov exponents, invariant measures) but unreliable for pointwise trajectory predictions over long times.

The practical consequence is that one should **always compute orbits statistically** when studying chaotic maps. Rather than tracking a single orbit $\{f^n(x_0)\}$ for large $n$, one should compute ensemble averages:

$$\langle A \rangle = \frac{1}{N} \sum_{n=0}^{N-1} A(f^n(x_0)) \approx \int A \, d\mu_{\text{inv}},$$

where $\mu_{\text{inv}}$ is the **natural invariant measure** of the map (the SRB measure, in the hyperbolic case). For the logistic map at $\mu = 4$, the natural measure has density $\rho(x) = 1/(\pi \sqrt{x(1-x)})$ — the arcsine distribution — and this density can be recovered from iteration to arbitrary precision by binning long orbits.

### Computing the Rotation Number: Continued Fractions and Convergence Rates

The rotation number $\rho(f)$ of a circle map is the central invariant one wants to compute, and the analysis of its continued-fraction expansion determines the convergence rate of numerical estimates and the width of Arnold tongues.

Recall that every irrational $\alpha \in [0,1]$ has a unique **continued fraction expansion** $\alpha = [0; a_1, a_2, a_3, \ldots]$ with $a_i \in \mathbb{Z}_{>0}$, and the convergents $p_k/q_k = [0; a_1, \ldots, a_k]$ satisfy

$$\left|\alpha - \frac{p_k}{q_k}\right| < \frac{1}{q_k q_{k+1}}.$$

For a rigid rotation $R_\alpha$, the orbit of $0$ under $R_\alpha$ returns closest to $0$ at precisely the denominators $q_k$ of the convergents, and the error $q_k \alpha - p_k$ alternates in sign and decreases like $1/q_{k+1}$. This gives an exact algorithm for computing $\rho$: iterate the map, track the closest returns to the initial point, read off the denominators $q_k$ of the convergents, and from these reconstruct $\alpha$ via the continued fraction.

For a smooth nonlinear circle map, the convergence of $\rho_N(x_0) = (F^N(x_0) - x_0)/N$ to $\rho$ is governed by the **cohomological equation**. If $f$ is conjugate to $R_\alpha$ by a diffeomorphism $h$, then $F^N(x) - x - N\alpha = h^{-1}(h(x) + N\alpha) - x$ is a function of $h(x)$ alone, and its time average decays like the Fourier coefficients of $h$. For $f$ real-analytic with $\rho = \alpha$ of bounded type (meaning $a_i \leq M$ for all $i$), the conjugacy $h$ is real-analytic, and the averaging error decays exponentially: $|\rho_N - \rho| \leq C e^{-\gamma N}$ for computable constants $C, \gamma > 0$.

### Bifurcation Diagrams: Construction and Pathologies

The standard bifurcation diagram for a one-parameter family $f_\mu$ is constructed by iterating the map for many values of $\mu$, discarding a transient of $N_{\text{trans}}$ iterates to allow convergence to the attractor, and then plotting the next $N_{\text{plot}}$ points $(mu, x_n)$. This produces the familiar picture: stable fixed points, period-doubling cascades, chaotic bands, and periodic windows.

Several failure modes arise in this construction. The **transient problem**: in parameter regions near tangent bifurcations (where a stable and unstable periodic orbit collide and annihilate), the system exhibits **intermittency** — long near-periodic epochs interrupted by chaotic bursts. The duration of the near-periodic epochs scales as $(\mu - \mu_c)^{-1/2}$ near the bifurcation point $\mu_c$, so a fixed transient discard of $N_{\text{trans}} = 1000$ iterates may be wildly insufficient near $\mu_c$. One must use an adaptive transient length, testing for convergence of the sample variance of successive iterates before plotting.

The **resolution problem** is subtler. The chaotic bands of the logistic map for $\mu > \mu_\infty$ are not a single connected interval; they are $2^k$-banded structures for $\mu$ in certain ranges, meaning the attractor consists of $2^k$ disjoint intervals that the orbit visits in a fixed cyclic order. If the parameter step $\Delta\mu$ is too coarse, these bands are not resolved, and what appears to be a single chaotic band is actually a period-$2^k$ pattern of bands. The correct diagnostic is to compute the **symbolic itinerary**: at each $\mu$, partition $[0,1]$ into $L = [0, x^*(\mu))$ and $R = [x^*(\mu), 1]$ where $x^*(\mu) = (\mu+1)/(2\mu)$ is the maximum of $f_\mu$, and record whether each iterate lands in $L$ or $R$. The periodic structure of the symbolic sequence determines the band count exactly.

### Lyapunov Exponents: Computation and Interpretation

The **Lyapunov exponent** $\lambda$ of the orbit starting at $x_0$ under a differentiable map $f$ is defined as

$$\lambda(x_0) = \lim_{n \to \infty} \frac{1}{n} \log |(f^n)'(x_0)| = \lim_{n \to \infty} \frac{1}{n} \sum_{k=0}^{n-1} \log |f'(x_k)|,$$

when the limit exists. By Birkhoff's ergodic theorem, for an ergodic invariant measure $\mu$, the limit exists $\mu$-almost everywhere and equals the **mean Lyapunov exponent**

$$\lambda = \int \log |f'(x)| \, d\mu(x).$$

For the logistic map at $\mu = 4$ with the arcsine measure $\rho(x) = 1/(\pi\sqrt{x(1-x)})$:

$$\lambda = \int_0^1 \log|f'_4(x)| \cdot \frac{dx}{\pi\sqrt{x(1-x)}} = \int_0^1 \log|4 - 8x| \cdot \frac{dx}{\pi\sqrt{x(1-x)}}.$$

The substitution $x = \sin^2(\pi\theta/2)$ transforms this to $\lambda = \int_0^1 \log|4\cos(\pi\theta)| \, d\theta = \log 4 - \log 4 + \log 2 = \log 2$, confirming $\lambda = \log 2 \approx 0.693$ and certifying fully developed chaos (positive Lyapunov exponent) with an explicit formula.

Positive $\lambda$ does not automatically certify chaos in the topological sense; one must separately verify topological transitivity (the existence of a dense orbit). But for the logistic map at $\mu = 4$, both hold. The relationship between Lyapunov exponents and **topological entropy** $h_{\text{top}}(f)$ is formalized by the **Ruelle inequality**: for a $C^1$ map $f$ preserving an ergodic Borel probability measure $\mu$, $h_{\mu}(f) \leq \lambda^+$ where $\lambda^+$ is the sum of positive Lyapunov exponents. For maps with absolutely continuous invariant measures (SRB measures), Pesin's formula gives equality: $h_\mu(f) = \lambda^+$.

For the degree-$d$ angle-doubling map $D(\theta) = d\theta \pmod{1}$ on $S^1$, the topological entropy is $h_{\text{top}}(D) = \log d$. For the complex map $f_c(z) = z^2 + c$, the topological entropy is $h_{\text{top}}(f_c) = \log 2$ regardless of $c$ (a theorem of Gromov and Lyubich), because the degree is 2 and the topological entropy of a degree-$d$ rational map on $\hat{\mathbb{C}}$ is always $\log d$.

### Failure Modes in Complex Iteration

The escape-time algorithm for Julia sets has its own failure modes, all related to the interaction between the escape radius and the fractal geometry of the Julia set near its boundary.

The standard threshold $|z| > 2$ as the escape criterion is sharp: the smallest value of $R$ such that $|z| > R$ implies $|f_c^n(z)| \to \infty$ for $f_c(z) = z^2 + c$ with $|c| \leq 2$ is exactly $R = (1 + \sqrt{1+4|c|})/2$, which for $|c| \leq 2$ is at most $2$. Using $R = 2$ is therefore both sufficient and tight. However, points in the **hedgehog regions** near parabolic fixed points (where the multiplier $f_c'(p) = e^{2\pi i p/q}$ is a root of unity) have orbits that spiral into the fixed point extremely slowly: the approach rate is polynomial in $n$ rather than exponential. The escape time algorithm assigns these points finite (but large) escape times, and the resulting visualization shows the characteristic **cauliflower** geometry of parabolic Julia sets correctly only when the maximum iteration count $N_{\max}$ is taken large enough (order $10^4$ to $10^5$ for parameters near the parabolic boundary of the main cardioid).

A more severe failure arises near **Siegel disks**, domains around irrationally neutral fixed points (multiplier $e^{2\pi i \alpha}$ with $\alpha$ a Diophantine irrational) on which $f_c$ is analytically conjugate to a rotation. The boundary of a Siegel disk is in the Julia set, and orbits starting just inside the disk rotate without escaping, while orbits just outside are asymptotically repelled. The escape time algorithm correctly assigns nonescaping orbits to the filled Julia set, but the apparent boundary — where the coloring transitions — is blurred by finite $N_{\max}$, with an error that decreases as $O(1/N_{\max})$ in the worst case. The correct approach for high-precision Julia set computation near Siegel boundaries is to combine the escape algorithm with the **distance estimator method**, which uses the derivative $|(f_c^n)'(z)|$ to estimate the distance from $z$ to $\mathcal{J}(f_c)$ via

$$\text{dist}(z, \mathcal{J}(f_c)) \approx 2 \frac{|f_c^N(z)| \log|f_c^N(z)|}{|(f_c^N)'(z)|},$$

a formula derived from the Böttcher coordinate and valid whenever $|f_c^N(z)|$ is large. This gives smooth, anti-aliased Julia set renderings at any magnification and identifies the boundary to within floating-point precision, independent of the fractal roughness of the set.

The deepest structural result connecting all three themes of this lesson — periodic orbits, rotation numbers, and Julia sets — is Douady and Hubbard's **straightening theorem** for polynomial-like maps, which states that every polynomial-like map $f: U \to V$ of degree $d$ is hybrid-equivalent (conjugate by a quasiconformal map that is conformal on the filled Julia set) to a polynomial of degree $d$. This theorem converts local dynamical data (the germ of a rational map near its Julia set) into global polynomial models, and it is the foundation for the renormalization theory of the Mandelbrot set: the small Mandelbrot copies visible inside the Mandelbrot set at every scale are images of the full Mandelbrot set under straightening maps, and the self-similar structure they encode is precisely the period-doubling and period-$n$ bifurcation structure we computed for the logistic map, now replicated throughout the complex parameter plane with the full richness of holomorphic geometry.
