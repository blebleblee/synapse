# Lesson 3: Integration Theory, Fundamental Theorem

## 1. First-Principles Intuition & Invariants

The concept of integration emerges from a deceptively simple question: how do we compute the area beneath a curve? While this geometric intuition serves as our entry point, the rigorous theory of integration that mathematicians developed in the nineteenth century transcends mere area calculation. Integration stands as one of the two fundamental operations of calculus, encoding the inverse relationship to differentiation and providing the mathematical machinery for accumulation, reconstruction, and limit processes across continuous domains.

The naive approach to computing area under a function $f(x)$ over an interval $[a, b]$ suggests subdividing the interval into smaller pieces, approximating the area above each subinterval with simple geometric shapes like rectangles, and summing these approximations. As we refine the subdivision by taking increasingly many pieces of decreasing width, we expect this process to converge to the true area. This limiting procedure, when formalized rigorously, produces the **Riemann integral**.

The profound insight at the heart of integration theory lies in recognizing that not every function admits such a limiting process. The class of Riemann integrable functions possesses specific structural properties related to the nature and extent of discontinuities. A function that oscillates wildly or exhibits pathological discontinuity behavior may defy integration entirely. Therefore, establishing the precise conditions under which a function qualifies as integrable becomes our first theoretical imperative.

The **Darboux characterization** of Riemann integrability provides an elegant reformulation that sidesteps the complexity of arbitrary partition choices and sample point selections. Instead of considering all possible Riemann sums, Darboux focused on the extreme cases: the supremum and infimum of function values over each subinterval. This perspective leads to upper and lower sums that sandwich the true integral value, and integrability reduces to the convergence of these bounds.

Once we establish that a function $f$ is integrable on $[a, b]$, we denote its integral as $\int_a^b f(x) \, dx$, a notation introduced by Leibniz that encodes both the summation process (the elongated S symbol) and the infinitesimal width element $dx$. The number this integral represents is a definite real value capturing the signed area between the function and the horizontal axis over the specified interval.

The **Fundamental Theorem of Calculus** stands as the central pillar of integration theory, establishing the precise relationship between differentiation and integration. This theorem appears in two parts. The first part asserts that integration reverses differentiation: if we integrate a continuous function $f$ to produce an antiderivative function $F(x) = \int_a^x f(t) \, dt$, then differentiating $F$ recovers the original function, so $F'(x) = f(x)$. The second part provides the computational payoff: if $F$ is any antiderivative of $f$, then the definite integral equals the difference in antiderivative values at the endpoints, written $\int_a^b f(x) \, dx = F(b) - F(a)$.

This connection transforms integration from a limiting process involving infinite subdivisions into an algebraic problem of finding antiderivatives. The practical implications cannot be overstated: computing definite integrals reduces to antidifferentiation followed by evaluation at boundary points. The entire edifice of integration techniques—substitution, integration by parts, partial fractions, trigonometric substitutions—rests on manipulating integrands into forms whose antiderivatives we recognize.

Beyond finite intervals and bounded functions, the theory extends to **improper integrals**, where either the domain becomes unbounded or the integrand exhibits vertical asymptotes within the integration region. These integrals require careful limit analysis to determine convergence or divergence. The study of improper integrals connects deeply to infinite series theory through integral comparison tests, providing a powerful analytical tool for assessing the behavior of functions at infinity or near singularities.

The invariants we must internalize throughout this lesson are these: integrability depends on the controllable behavior of function oscillations; the Fundamental Theorem bridges the continuous world of integrals with the algebraic world of antiderivatives; and convergence analysis for improper integrals follows the same limiting rigor that undergirds all of calculus.

## 2. Core Architecture & Mechanics

### Riemann Sums and Partition Refinement

The construction of the Riemann integral begins with the notion of a **partition** of an interval $[a, b]$. A partition $P$ is a finite ordered sequence of points $P = \{x_0, x_1, x_2, \ldots, x_n\}$ satisfying $a = x_0 < x_1 < x_2 < \cdots < x_n = b$. This partition subdivides $[a, b]$ into $n$ subintervals $[x_{i-1}, x_i]$ for $i = 1, 2, \ldots, n$. The width of the $i$-th subinterval is $\Delta x_i = x_i - x_{i-1}$, and the **mesh** or **norm** of the partition, denoted $\|P\|$, is the maximum subinterval width: $\|P\| = \max_{1 \le i \le n} \Delta x_i$.

Given a bounded function $f : [a, b] \to \mathbb{R}$ and a partition $P$, we construct a **Riemann sum** by selecting a sample point $t_i^* \in [x_{i-1}, x_i]$ within each subinterval and forming the sum:

$$
S(f, P, T) = \sum_{i=1}^n f(t_i^*) \Delta x_i
$$

where $T = \{t_1^*, t_2^*, \ldots, t_n^*\}$ denotes the collection of sample points. Different choices of sample points yield different Riemann sums for the same partition. Common choices include left endpoints ($t_i^* = x_{i-1}$), right endpoints ($t_i^* = x_i$), and midpoints ($t_i^* = (x_{i-1} + x_i)/2$).

The function $f$ is **Riemann integrable** on $[a, b]$ if there exists a number $I \in \mathbb{R}$ such that for every $\varepsilon > 0$, there exists $\delta > 0$ such that whenever $P$ is a partition with $\|P\| < \delta$ and $T$ is any choice of sample points, we have $|S(f, P, T) - I| < \varepsilon$. In this case, we write $I = \int_a^b f(x) \, dx$ and call $I$ the Riemann integral of $f$ over $[a, b]$.

This definition encodes a delicate limiting process: as we refine partitions by taking mesh size to zero, all Riemann sums must converge to the same limiting value $I$, regardless of how we choose sample points within subintervals. This uniformity requirement eliminates functions with pathological oscillatory behavior.

### Darboux Sums and Integrability Criterion

The Darboux approach replaces arbitrary sample point choices with extremal values over each subinterval. For a bounded function $f$ and partition $P = \{x_0, x_1, \ldots, x_n\}$, define:

$$
m_i = \inf_{x \in [x_{i-1}, x_i]} f(x), \quad M_i = \sup_{x \in [x_{i-1}, x_i]} f(x)
$$

These yield the **lower Darboux sum** $L(f, P) = \sum_{i=1}^n m_i \Delta x_i$ and the **upper Darboux sum** $U(f, P) = \sum_{i=1}^n M_i \Delta x_i$. By construction, $L(f, P) \le S(f, P, T) \le U(f, P)$ for any choice of sample points $T$, so Darboux sums provide bounds for all possible Riemann sums.

As we refine partitions, lower sums increase (or remain constant) while upper sums decrease (or remain constant). Specifically, if $P'$ is a **refinement** of $P$ (meaning $P' \supseteq P$ as sets), then $L(f, P) \le L(f, P')$ and $U(f, P') \le U(f, P)$. This monotonicity ensures that the set of all lower sums is bounded above and the set of all upper sums is bounded below.

Define the **lower Darboux integral** as $\underline{\int_a^b} f = \sup_P L(f, P)$ and the **upper Darboux integral** as $\overline{\int_a^b} f = \inf_P U(f, P)$, where the supremum and infimum range over all partitions of $[a, b]$. A fundamental property is that $\underline{\int_a^b} f \le \overline{\int_a^b} f$ always holds.

The **Darboux integrability criterion** states that $f$ is Riemann integrable if and only if $\underline{\int_a^b} f = \overline{\int_a^b} f$, and in this case, the common value equals the Riemann integral: $\int_a^b f = \underline{\int_a^b} f = \overline{\int_a^b} f$.

An equivalent formulation involves the difference $U(f, P) - L(f, P)$, which measures the total oscillation of $f$ across the partition. The function $f$ is Riemann integrable if and only if for every $\varepsilon > 0$, there exists a partition $P$ such that $U(f, P) - L(f, P) < \varepsilon$. This condition quantifies the intuition that integrable functions cannot oscillate too wildly: their oscillations must be controllable through sufficiently fine partitioning.

**Theorem (Riemann's Integrability Condition):** A bounded function $f : [a, b] \to \mathbb{R}$ is Riemann integrable if and only if the set of discontinuities of $f$ has measure zero.

This theorem provides the sharpest characterization of Riemann integrability. Functions with countably many discontinuities are integrable, as are monotone functions (which have at most countably many discontinuities). However, a function that is discontinuous at every point in a non-trivial interval fails integrability.

### Fundamental Theorem of Calculus: Part I

The first part of the Fundamental Theorem concerns the derivative of an integral with variable upper limit. Let $f : [a, b] \to \mathbb{R}$ be continuous, and define the **antiderivative function** $F : [a, b] \to \mathbb{R}$ by:

$$
F(x) = \int_a^x f(t) \, dt
$$

**Theorem (FTC Part I):** If $f$ is continuous on $[a, b]$, then $F$ is differentiable on $[a, b]$ and $F'(x) = f(x)$ for all $x \in [a, b]$.

**Proof:** Fix $x \in (a, b)$ and consider the difference quotient:

$$
\frac{F(x + h) - F(x)}{h} = \frac{1}{h} \left( \int_a^{x+h} f(t) \, dt - \int_a^x f(t) \, dt \right) = \frac{1}{h} \int_x^{x+h} f(t) \, dt
$$

by the additivity property of integrals. Since $f$ is continuous at $x$, for any $\varepsilon > 0$, there exists $\delta > 0$ such that $|t - x| < \delta$ implies $|f(t) - f(x)| < \varepsilon$. For $0 < |h| < \delta$, every $t \in [x, x+h]$ (or $[x+h, x]$ if $h < 0$) satisfies $|t - x| \le |h| < \delta$, so $|f(t) - f(x)| < \varepsilon$.

Therefore:

$$
\left| \frac{1}{h} \int_x^{x+h} f(t) \, dt - f(x) \right| = \left| \frac{1}{h} \int_x^{x+h} (f(t) - f(x)) \, dt \right| \le \frac{1}{|h|} \int_x^{x+h} |f(t) - f(x)| \, dt < \frac{1}{|h|} \cdot |h| \cdot \varepsilon = \varepsilon
$$

where we used the property that the integral of an absolute value bounds the absolute value of the integral, and the fact that $|f(t) - f(x)| < \varepsilon$ throughout the integration interval. This proves that $\lim_{h \to 0} \frac{F(x+h) - F(x)}{h} = f(x)$, so $F'(x) = f(x)$. The argument extends to the endpoints $a$ and $b$ using one-sided derivatives. ∎

This theorem guarantees that every continuous function possesses an antiderivative. The function $F(x) = \int_a^x f(t) \, dt$ provides an explicit construction of such an antiderivative, even when we cannot express $F$ in terms of elementary functions.

### Fundamental Theorem of Calculus: Part II

The second part of the Fundamental Theorem provides the computational method for evaluating definite integrals via antiderivatives.

**Theorem (FTC Part II):** Let $f : [a, b] \to \mathbb{R}$ be continuous, and let $F : [a, b] \to \mathbb{R}$ be any antiderivative of $f$ (meaning $F'(x) = f(x)$ for all $x \in [a, b]$). Then:

$$
\int_a^b f(x) \, dx = F(b) - F(a)
$$

This difference $F(b) - F(a)$ is often written using the evaluation notation $F(x) \big|_a^b$ or $[F(x)]_a^b$.

**Proof:** Define $G(x) = \int_a^x f(t) \, dt$. By Part I of the Fundamental Theorem, $G'(x) = f(x)$ for all $x \in [a, b]$. Since $F$ is also an antiderivative of $f$, we have $F'(x) = f(x) = G'(x)$. This means $(F - G)'(x) = F'(x) - G'(x) = 0$ for all $x \in [a, b]$.

A function with zero derivative everywhere on an interval must be constant (this follows from the Mean Value Theorem: if $(F - G)'(x) = 0$, then for any $x_1 < x_2$ in $[a, b]$, there exists $c \in (x_1, x_2)$ such that $\frac{(F - G)(x_2) - (F - G)(x_1)}{x_2 - x_1} = (F - G)'(c) = 0$, implying $(F - G)(x_2) = (F - G)(x_1)$). Therefore, $F(x) - G(x) = C$ for some constant $C$ and all $x \in [a, b]$.

Evaluating at $x = a$ gives $F(a) - G(a) = C$. Since $G(a) = \int_a^a f(t) \, dt = 0$, we have $C = F(a)$. Thus $F(x) = G(x) + F(a)$ for all $x \in [a, b]$.

Setting $x = b$ yields:

$$
F(b) = G(b) + F(a) = \int_a^b f(t) \, dt + F(a)
$$

Rearranging gives $\int_a^b f(t) \, dt = F(b) - F(a)$, which is the desired result. ∎

The power of Part II lies in reducing integration to antidifferentiation. If we can find a function $F$ whose derivative equals $f$, the definite integral equals the net change in $F$ over the interval. This transforms a limiting process involving partitions and Riemann sums into a two-step algebraic procedure: find $F$ such that $F' = f$, then compute $F(b) - F(a)$.

### Integration Techniques: Substitution

The **substitution rule** (also called $u$-substitution or change of variables) generalizes the chain rule for derivatives. If $g : [a, b] \to \mathbb{R}$ is continuously differentiable and $f : [g(a), g(b)] \to \mathbb{R}$ is continuous, then:

$$
\int_a^b f(g(x)) g'(x) \, dx = \int_{g(a)}^{g(b)} f(u) \, du
$$

**Proof:** Let $F$ be an antiderivative of $f$, so $F' = f$. Define $H(x) = F(g(x))$. By the chain rule, $H'(x) = F'(g(x)) \cdot g'(x) = f(g(x)) \cdot g'(x)$. Therefore, $H$ is an antiderivative of the integrand $f(g(x)) g'(x)$.

Applying FTC Part II:

$$
\int_a^b f(g(x)) g'(x) \, dx = H(b) - H(a) = F(g(b)) - F(g(a))
$$

But by FTC Part II again applied to the integral $\int_{g(a)}^{g(b)} f(u) \, du$, we have:

$$
\int_{g(a)}^{g(b)} f(u) \, du = F(g(b)) - F(g(a))
$$

Thus the two integrals are equal. ∎

The practical procedure for substitution involves identifying a composite structure $f(g(x)) g'(x)$ in the integrand, setting $u = g(x)$ (so $du = g'(x) \, dx$), and transforming the integral into one over the variable $u$. For definite integrals, we must also transform the limits: when $x = a$, we have $u = g(a)$, and when $x = b$, we have $u = g(b)$.

**Example:** Evaluate $\int_0^{\pi/2} \sin(x) \cos(x) \, dx$.

Let $u = \sin(x)$, so $du = \cos(x) \, dx$. When $x = 0$, $u = \sin(0) = 0$. When $x = \pi/2$, $u = \sin(\pi/2) = 1$. The integral becomes:

$$
\int_0^1 u \, du = \frac{u^2}{2} \bigg|_0^1 = \frac{1}{2} - 0 = \frac{1}{2}
$$

### Integration Techniques: Integration by Parts

**Integration by parts** arises from the product rule for derivatives: $(uv)' = u'v + uv'$. Integrating both sides over $[a, b]$ and rearranging gives:

$$
\int_a^b u(x) v'(x) \, dx = u(x) v(x) \bigg|_a^b - \int_a^b u'(x) v(x) \, dx
$$

or more compactly, $\int u \, dv = uv - \int v \, du$ for indefinite integrals.

The strategy involves choosing which part of the integrand to designate as $u$ (to be differentiated) and which part as $dv$ (to be integrated). The goal is to produce a simpler integral $\int v \, du$ than the original $\int u \, dv$.

**Example:** Evaluate $\int_0^1 x e^x \, dx$.

Let $u = x$ and $dv = e^x \, dx$. Then $du = dx$ and $v = e^x$. Applying integration by parts:

$$
\int_0^1 x e^x \, dx = x e^x \bigg|_0^1 - \int_0^1 e^x \, dx = (1 \cdot e^1 - 0 \cdot e^0) - (e^1 - e^0) = e - (e - 1) = 1
$$

For integrals requiring repeated application of integration by parts, such as $\int e^x \sin(x) \, dx$, we may need to apply the technique twice and solve algebraically for the desired integral.

### Integration Techniques: Partial Fractions

Rational functions—quotients of polynomials $\frac{P(x)}{Q(x)}$—can often be integrated by decomposing them into simpler fractions. If the degree of $P$ is less than the degree of $Q$ and $Q$ factors into linear and irreducible quadratic factors over $\mathbb{R}$, we express $\frac{P(x)}{Q(x)}$ as a sum of terms of the form $\frac{A}{(x - a)^k}$ and $\frac{Bx + C}{(x^2 + bx + c)^k}$.

**Example:** Integrate $\int \frac{1}{x^2 - 1} \, dx$.

Factor the denominator: $x^2 - 1 = (x - 1)(x + 1)$. The partial fraction decomposition takes the form:

$$
\frac{1}{x^2 - 1} = \frac{A}{x - 1} + \frac{B}{x + 1}
$$

Multiplying through by $x^2 - 1$ gives $1 = A(x + 1) + B(x - 1)$. Setting $x = 1$ yields $1 = 2A$, so $A = 1/2$. Setting $x = -1$ yields $1 = -2B$, so $B = -1/2$. Thus:

$$
\frac{1}{x^2 - 1} = \frac{1/2}{x - 1} - \frac{1/2}{x + 1}
$$

Integrating:

$$
\int \frac{1}{x^2 - 1} \, dx = \frac{1}{2} \ln|x - 1| - \frac{1}{2} \ln|x + 1| + C = \frac{1}{2} \ln\left|\frac{x - 1}{x + 1}\right| + C
$$

### Improper Integrals: Type I (Infinite Limits)

An **improper integral** extends the definite integral concept to cases where the integration interval is unbounded or the integrand becomes unbounded. For Type I improper integrals, the domain extends to infinity. The integral $\int_a^\infty f(x) \, dx$ is defined as the limit:

$$
\int_a^\infty f(x) \, dx = \lim_{R \to \infty} \int_a^R f(x) \, dx
$$

provided the limit exists and is finite. Similarly, $\int_{-\infty}^b f(x) \, dx = \lim_{R \to -\infty} \int_R^b f(x) \, dx$, and $\int_{-\infty}^\infty f(x) \, dx$ is defined by splitting at any point $c$ and requiring both $\int_{-\infty}^c f(x) \, dx$ and $\int_c^\infty f(x) \, dx$ to converge.

**Example:** Evaluate $\int_1^\infty \frac{1}{x^2} \, dx$.

$$
\int_1^\infty \frac{1}{x^2} \, dx = \lim_{R \to \infty} \int_1^R x^{-2} \, dx = \lim_{R \to \infty} \left[ -x^{-1} \right]_1^R = \lim_{R \to \infty} \left( -\frac{1}{R} + 1 \right) = 1
$$

The integral converges to $1$.

**Counterexample:** Consider $\int_1^\infty \frac{1}{x} \, dx$.

$$
\int_1^\infty \frac{1}{x} \, dx = \lim_{R \to \infty} \int_1^R \frac{1}{x} \, dx = \lim_{R \to \infty} \left[ \ln x \right]_1^R = \lim_{R \to \infty} (\ln R - \ln 1) = \lim_{R \to \infty} \ln R = \infty
$$

The integral diverges.

The **$p$-integral test** generalizes this behavior: $\int_1^\infty \frac{1}{x^p} \, dx$ converges if and only if $p > 1$. This test becomes a powerful tool for comparison tests.

### Improper Integrals: Type II (Unbounded Integrand)

A Type II improper integral occurs when the integrand approaches infinity at some point within or at the boundary of the integration interval. If $f$ has a vertical asymptote at $x = b$, we define:

$$
\int_a^b f(x) \, dx = \lim_{t \to b^-} \int_a^t f(x) \, dx
$$

**Example:** Evaluate $\int_0^1 \frac{1}{\sqrt{x}} \, dx$.

The integrand $\frac{1}{\sqrt{x}}$ approaches infinity as $x \to 0^+$. We compute:

$$
\int_0^1 \frac{1}{\sqrt{x}} \, dx = \lim_{t \to 0^+} \int_t^1 x^{-1/2} \, dx = \lim_{t \to 0^+} \left[ 2x^{1/2} \right]_t^1 = \lim_{t \to 0^+} (2 \cdot 1 - 2\sqrt{t}) = 2
$$

The integral converges to $2$.

### Convergence Tests for Improper Integrals

**Comparison Test:** Suppose $0 \le f(x) \le g(x)$ for $x \ge a$. If $\int_a^\infty g(x) \, dx$ converges, then $\int_a^\infty f(x) \, dx$ converges. If $\int_a^\infty f(x) \, dx$ diverges, then $\int_a^\infty g(x) \, dx$ diverges.

**Limit Comparison Test:** If $f(x) > 0$ and $g(x) > 0$ for $x \ge a$, and if $\lim_{x \to \infty} \frac{f(x)}{g(x)} = L$ where $0 < L < \infty$, then $\int_a^\infty f(x) \, dx$ and $\int_a^\infty g(x) \, dx$ either both converge or both diverge.

**Example:** Determine whether $\int_1^\infty \frac{\sin^2 x}{x^2} \, dx$ converges.

Since $0 \le \sin^2 x \le 1$, we have $0 \le \frac{\sin^2 x}{x^2} \le \frac{1}{x^2}$. The integral $\int_1^\infty \frac{1}{x^2} \, dx$ converges (as shown earlier). By the comparison test, $\int_1^\infty \frac{\sin^2 x}{x^2} \, dx$ converges.

**Absolute Convergence Test:** If $\int_a^\infty |f(x)| \, dx$ converges, then $\int_a^\infty f(x) \, dx$ converges. An integral satisfying this condition is said to converge absolutely. If $\int_a^\infty f(x) \, dx$ converges but $\int_a^\infty |f(x)| \, dx$ diverges, the integral converges conditionally.

## 3. High-Performance Optimization & Failure Modes

### Selecting Optimal Integration Techniques

The efficiency of computing integrals by hand depends critically on pattern recognition and technique selection. When faced with an integrand, the first diagnostic step involves identifying structural features: is it a composition suitable for substitution? Does it contain a product suggesting integration by parts? Is it a rational function amenable to partial fractions?

For substitution, look for a function composed with its derivative, or more generally, an inner function whose derivative appears as a multiplicative factor. The substitution $u = g(x)$ succeeds when the transformed integral $\int f(u) \, du$ is simpler than the original. If the substitution introduces complexity—such as requiring inverse functions or producing algebraically messier expressions—reconsider the approach.

Integration by parts works best when one factor $u$ simplifies upon differentiation while the other factor $dv$ remains manageable upon integration. The heuristic **LIATE** (Logarithmic, Inverse trigonometric, Algebraic, Trigonometric, Exponential) suggests choosing $u$ from the earliest category appearing in the integrand. For instance, in $\int x \ln x \, dx$, choose $u = \ln x$ (logarithmic) and $dv = x \, dx$ (algebraic). Differentiating $\ln x$ yields $1/x$, which simplifies the subsequent integral.

For products of polynomials with exponentials or trigonometric functions, repeated integration by parts often succeeds. The technique may require applying the formula twice and solving for the desired integral algebraically. This occurs classically with integrals like $\int e^x \cos x \, dx$, where two applications yield an equation of the form $I = \text{(expression)} - I$, allowing us to solve $2I = \text{(expression)}$.

Rational functions require partial fraction decomposition when the degree of the numerator is less than the degree of the denominator. If the numerator degree equals or exceeds the denominator degree, perform polynomial long division first to extract a polynomial part plus a proper rational remainder. Factor the denominator completely over the reals, and set up the decomposition with unknown coefficients. Solve for these coefficients by equating numerators after clearing denominators, using strategic values of $x$ or matching coefficients of like powers.

Trigonometric integrals involving powers of sine and cosine benefit from parity analysis. For $\int \sin^m x \cos^n x \, dx$, if $m$ is odd, factor out one $\sin x$ for the differential and convert remaining $\sin^2 x$ factors to $1 - \cos^2 x$, enabling substitution $u = \cos x$. If $n$ is odd, factor out $\cos x$ and convert remaining $\cos^2 x$ factors to $1 - \sin^2 x$, using substitution $u = \sin x$. If both $m$ and $n$ are even, apply half-angle identities: $\sin^2 x = \frac{1 - \cos(2x)}{2}$ and $\cos^2 x = \frac{1 + \cos(2x)}{2}$.

Trigonometric substitution handles integrands containing $\sqrt{a^2 - x^2}$, $\sqrt{a^2 + x^2}$, or $\sqrt{x^2 - a^2}$. For $\sqrt{a^2 - x^2}$, substitute $x = a \sin \theta$ with $\theta \in [-\pi/2, \pi/2]$. For $\sqrt{a^2 + x^2}$, substitute $x = a \tan \theta$ with $\theta \in (-\pi/2, \pi/2)$. For $\sqrt{x^2 - a^2}$, substitute $x = a \sec \theta$ with $\theta \in [0, \pi/2) \cup (\pi/2, \pi]$. These substitutions exploit the Pythagorean identities to eliminate radicals.

### Computational Failure Modes and Resolution

The most common failure mode arises from attempting to apply the Fundamental Theorem to discontinuous or non-integrable functions. If $f$ is not Riemann integrable on $[a, b]$, the definite integral $\int_a^b f(x) \, dx$ is undefined, and no antiderivative evaluation will yield a valid result. Before applying FTC Part II, verify that $f$ is continuous (or at worst has finitely many jump discontinuities, which are integrable but require splitting the integral at discontinuity points).

A subtler error occurs when an antiderivative $F$ possesses discontinuities within the integration interval. The function $f(x) = \frac{1}{x}$ has antiderivative $F(x) = \ln|x|$, but this antiderivative is discontinuous at $x = 0$. The expression $\int_{-1}^1 \frac{1}{x} \, dx = \ln|1| - \ln|-1| = 0$ is false because the integrand has a vertical asymptote at $x = 0$, making this a Type II improper integral that diverges. Always check the domain of the antiderivative and identify points where the integrand becomes unbounded.

For improper integrals, failure to properly set up the limiting process leads to incorrect conclusions. The integral $\int_{-\infty}^\infty f(x) \, dx$ cannot be evaluated as $\lim_{R \to \infty} \int_{-R}^R f(x) \, dx$ unless this symmetric limit agrees with the proper definition requiring separate convergence of $\int_{-\infty}^0 f(x) \, dx$ and $\int_0^\infty f(x) \, dx$. For example, $\int_{-\infty}^\infty x \, dx$ is undefined because both tails diverge, even though the symmetric limit $\lim_{R \to \infty} \int_{-R}^R x \, dx = 0$ due to cancellation. This symmetric limit is called the **Cauchy principal value** and does not represent convergence of the improper integral in the standard sense.

When applying comparison tests for improper integral convergence, the choice of comparison function $g(x)$ must reflect the asymptotic behavior of $f(x)$. For integrals of the form $\int_1^\infty \frac{P(x)}{Q(x)} \, dx$ where $P$ and $Q$ are polynomials, the dominant behavior at infinity depends on the leading terms. If $\deg(Q) - \deg(P) > 1$, the integral converges. If $\deg(Q) - \deg(P) \le 1$, the integral diverges. Construct the comparison function by isolating the leading terms: $\frac{P(x)}{Q(x)} \sim \frac{c x^m}{d x^n} = \frac{c}{d} x^{m-n}$ as $x \to \infty$, and apply the $p$-integral test with $p = n - m$.

For integrals with oscillatory integrands like $\int_1^\infty \frac{\sin x}{x^p} \, dx$, direct comparison to non-negative functions fails because the integrand changes sign. Instead, use absolute convergence: $\left|\frac{\sin x}{x^p}\right| \le \frac{1}{x^p}$, and $\int_1^\infty \frac{1}{x^p} \, dx$ converges for $p > 1$. Thus $\int_1^\infty \frac{\sin x}{x^p} \, dx$ converges absolutely for $p > 1$. For $p \le 1$, specialized techniques like Dirichlet's test or integration by parts are required to determine convergence.

### Numerical Integration and Error Bounds

When antiderivatives cannot be expressed in elementary functions—such as $\int e^{-x^2} \, dx$ or $\int \frac{\sin x}{x} \, dx$—numerical integration provides approximate values. The three foundational methods are the **Riemann sum**, **Trapezoidal rule**, and **Simpson's rule**.

The Riemann sum with uniform partition of width $\Delta x = (b - a)/n$ yields approximations $R_n = \sum_{i=1}^n f(x_i^*) \Delta x$, where $x_i^*$ denotes a sample point in the $i$-th subinterval. The error for left or right Riemann sums is $O(\Delta x)$, meaning the error is proportional to the mesh size.

The Trapezoidal rule approximates the area under the curve by trapezoids rather than rectangles:

$$
T_n = \frac{\Delta x}{2} \left[ f(x_0) + 2f(x_1) + 2f(x_2) + \cdots + 2f(x_{n-1}) + f(x_n) \right]
$$

The error bound for the Trapezoidal rule, when $f''$ is continuous on $[a, b]$, is:

$$
\left| \int_a^b f(x) \, dx - T_n \right| \le \frac{(b - a)^3}{12n^2} \max_{x \in [a, b]} |f''(x)|
$$

This $O((\Delta x)^2)$ error decays quadratically with the number of subintervals, making the Trapezoidal rule significantly more efficient than Riemann sums for smooth functions.

Simpson's rule fits parabolic arcs through triplets of points, yielding:

$$
S_n = \frac{\Delta x}{3} \left[ f(x_0) + 4f(x_1) + 2f(x_2) + 4f(x_3) + \cdots + 2f(x_{n-2}) + 4f(x_{n-1}) + f(x_n) \right]
$$

where $n$ must be even. The error bound for Simpson's rule, when $f^{(4)}$ is continuous, is:

$$
\left| \int_a^b f(x) \, dx - S_n \right| \le \frac{(b - a)^5}{180n^4} \max_{x \in [a, b]} |f^{(4)}(x)|
$$

The $O((\Delta x)^4)$ error makes Simpson's rule highly accurate for smooth integrands, often requiring far fewer subdivisions than the Trapezoidal rule to achieve a desired precision.

For improper integrals, numerical methods require truncating the infinite domain or handling singularities through substitution. The integral $\int_0^\infty e^{-x} \, dx = 1$ can be approximated by $\int_0^R e^{-x} \, dx$ for sufficiently large $R$, with the tail error bounded by $\int_R^\infty e^{-x} \, dx = e^{-R}$. For Type II improper integrals like $\int_0^1 \frac{1}{\sqrt{x}} \, dx$, the substitution $u = \sqrt{x}$ transforms the integral to $\int_0^1 2 \, du = 2$, eliminating the singularity and permitting direct numerical evaluation.

### Leibniz Rule and Differentiating Under the Integral

When an integral depends on a parameter, the **Leibniz integral rule** allows differentiation with respect to that parameter under the integral sign. If $f(x, t)$ and $\frac{\partial f}{\partial t}(x, t)$ are continuous on $[a, b] \times [c, d]$, then:

$$
\frac{d}{dt} \int_a^b f(x, t) \, dx = \int_a^b \frac{\partial f}{\partial t}(x, t) \, dx
$$

This powerful technique transforms difficult integrals into simpler ones by introducing a parameter and differentiating. When the limits of integration also depend on the parameter, the full Leibniz rule states:

$$
\frac{d}{dt} \int_{\alpha(t)}^{\beta(t)} f(x, t) \, dx = \int_{\alpha(t)}^{\beta(t)} \frac{\partial f}{\partial t}(x, t) \, dx + f(\beta(t), t) \beta'(t) - f(\alpha(t), t) \alpha'(t)
$$

**Example:** Evaluate $I(a) = \int_0^\infty e^{-ax} \sin(x) \, dx$ for $a > 0$.

Differentiate with respect to $a$:

$$
\frac{dI}{da} = \int_0^\infty \frac{\partial}{\partial a} (e^{-ax} \sin x) \, dx = -\int_0^\infty x e^{-ax} \sin x \, dx
$$

Using integration by parts twice (or looking up the standard result), we find $\int_0^\infty x e^{-ax} \sin x \, dx = \frac{2a}{(a^2 + 1)^2}$. Thus:

$$
\frac{dI}{da} = -\frac{2a}{(a^2 + 1)^2}
$$

Integrating with respect to $a$:

$$
I(a) = \int -\frac{2a}{(a^2 + 1)^2} \, da = \frac{1}{a^2 + 1} + C
$$

To determine $C$, note that as $a \to \infty$, $I(a) \to 0$ (by dominated convergence), implying $C = 0$. Therefore:

$$
I(a) = \frac{1}{a^2 + 1}
$$

Setting $a = 1$ gives $\int_0^\infty e^{-x} \sin x \, dx = \frac{1}{2}$.

### Theoretical Limitations and Non-Elementary Integrals

Not every continuous function possesses an antiderivative expressible in terms of elementary functions (polynomials, exponentials, logarithms, trigonometric functions, and their compositions). Classic examples include $\int e^{-x^2} \, dx$ (the Gaussian integral, related to the error function $\text{erf}(x)$), $\int \frac{\sin x}{x} \, dx$ (the sine integral $\text{Si}(x)$), and $\int \frac{1}{\ln x} \, dx$ (the logarithmic integral $\text{li}(x)$).

The existence of non-elementary integrals follows from the **Risch algorithm**, which provides a decision procedure for determining whether a given elementary function has an elementary antiderivative. When no elementary antiderivative exists, we define new special functions to represent the integrals. These special functions become objects of study in their own right, with series expansions, asymptotic behavior, and functional equations characterizing their properties.

The Fundamental Theorem guarantees that every continuous function has *some* antiderivative $F(x) = \int_a^x f(t) \, dt$, but this antiderivative may not simplify to a closed form using the standard function vocabulary. In such cases, numerical integration, series approximations, or asymptotic methods provide practical computational strategies.

The theoretical framework of integration extends far beyond the Riemann integral developed here. The **Lebesgue integral**, constructed via measure theory, integrates a vastly broader class of functions and provides the foundation for modern probability theory and functional analysis. The Riemann integral suffices for continuous functions and functions with controlled discontinuities, but Lebesgue integration handles highly discontinuous functions and provides stronger convergence theorems essential for advanced analysis.

Integration theory stands as a testament to the power of limit processes in mathematics. From the intuitive notion of area, we constructed a rigorous theory encoding accumulation, inverse differentiation, and infinite summation. The Fundamental Theorem bridges discrete and continuous worlds, transforming limiting processes into algebraic calculations. Mastery of integration techniques empowers us to solve differential equations, compute probabilities, analyze physical systems, and investigate the deep structure of mathematical functions.
