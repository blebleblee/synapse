# Lesson 6: Sequences of Functions — Pointwise Convergence, Uniform Convergence, Series

## 1. First-Principles Intuition & Invariants

The transition from sequences of real numbers to sequences of functions represents one of the most profound conceptual leaps in mathematical analysis. When we study a sequence $(a_n)$ of real numbers converging to a limit $a$, the notion of convergence is unambiguous: given any tolerance $\varepsilon > 0$, we can find an index $N$ beyond which all terms lie within $\varepsilon$ of $a$. The situation becomes vastly more intricate when we consider a sequence $(f_n)$ of functions defined on a common domain $D \subseteq \mathbb{R}$, each mapping points $x \in D$ to real values $f_n(x)$. Now we must ask: what does it mean for such a sequence to converge to a limiting function $f$?

The natural first answer is **pointwise convergence**: we say $f_n \to f$ pointwise on $D$ if, for each fixed point $x \in D$, the numerical sequence $(f_n(x))$ converges to $f(x)$. Formally, for every $x \in D$ and every $\varepsilon > 0$, there exists an index $N = N(\varepsilon, x)$ such that $|f_n(x) - f(x)| < \varepsilon$ for all $n \ge N$. The critical observation is that the index $N$ depends not only on the tolerance $\varepsilon$ but also on the specific point $x$ under consideration. Different points may require vastly different rates of convergence, and this heterogeneity across the domain leads to pathological behavior.

Consider the canonical cautionary example on $[0,1]$: define $f_n(x) = x^n$. For any $x \in [0,1)$, we have $\lim_{n \to \infty} x^n = 0$ because $0 \le x < 1$ forces the geometric sequence to decay exponentially. At $x = 1$, we have $f_n(1) = 1^n = 1$ for all $n$, so the limit is identically $1$. The pointwise limit function is therefore the discontinuous indicator
$$
f(x) = \begin{cases} 0 & \text{if } x \in [0,1) \\ 1 & \text{if } x = 1 \end{cases}
$$
Each $f_n$ is continuous—indeed, each is a smooth polynomial—yet the limit function $f$ is discontinuous at $x = 1$. This phenomenon exposes a fundamental defect of pointwise convergence: it does not preserve continuity. The analytic properties we care about—continuity, differentiability, integrability—can be destroyed in the limit, rendering pointwise convergence unsuitable for exchanging limits with other operations.

The resolution lies in a stronger notion: **uniform convergence**. We say $f_n \to f$ uniformly on $D$ if, for every $\varepsilon > 0$, there exists an index $N = N(\varepsilon)$, independent of $x$, such that $|f_n(x) - f(x)| < \varepsilon$ for all $n \ge N$ and all $x \in D$ simultaneously. Geometrically, uniform convergence means that beyond some index $N$, the entire graph of $f_n$ lies within an $\varepsilon$-tube around the graph of $f$. The uniformity of the convergence rate across the domain is the critical ingredient that preserves structure.

To see why the example $f_n(x) = x^n$ fails uniform convergence, fix $\varepsilon = 1/4$ and consider any index $N$. For $x_N = (1 - 1/N)$, we have $f_N(x_N) = (1 - 1/N)^N \to e^{-1} \approx 0.368$ as $N \to \infty$, while $f(x_N) = 0$. Thus $|f_N(x_N) - f(x_N)| \approx 0.368 > 1/4$, and no single $N$ works uniformly for all $x$. The convergence near $x = 1$ is arbitrarily slow, preventing uniform control.

The foundational theorems of uniform convergence establish that this stronger mode of convergence preserves the analytic fabric of function spaces. The **Uniform Limit Theorem** asserts that if each $f_n$ is continuous on $D$ and $f_n \to f$ uniformly on $D$, then $f$ is continuous on $D$. This is not merely a technical convenience; it is the gateway to functional analysis, where spaces of continuous functions equipped with the uniform norm become complete metric spaces. Similarly, uniform convergence permits the exchange of limits with integration and differentiation under appropriate hypotheses, enabling term-by-term manipulation of series and the rigorous justification of power series expansions.

The central tool for verifying uniform convergence in practice is the **Weierstrass M-test**, which reduces the problem to numerical majorization. For infinite series $\sum_{k=1}^\infty u_k(x)$, if we can find constants $M_k \ge 0$ such that $|u_k(x)| \le M_k$ for all $x \in D$ and $\sum_{k=1}^\infty M_k$ converges, then $\sum_{k=1}^\infty u_k(x)$ converges uniformly and absolutely on $D$. This criterion transforms the infinitary problem of controlling convergence for all $x$ simultaneously into the finitary problem of finding a convergent numerical majorant, a task often tractable through comparison tests and geometric series bounds.

Power series $\sum_{k=0}^\infty a_k (x - c)^k$ occupy a distinguished position in this theory because their convergence behavior is governed by a single parameter: the **radius of convergence** $R$, defined by the Cauchy-Hadamard formula $R^{-1} = \limsup_{k \to \infty} |a_k|^{1/k}$. Within the open interval $(c - R, c + R)$, the series converges absolutely and uniformly on every compact subset, permitting term-by-term differentiation and integration. On the boundary $|x - c| = R$, convergence may be conditional or absent entirely, requiring delicate analysis. The power series framework underpins the construction of analytic functions and provides the bridge between discrete algebraic data (the coefficients $a_k$) and smooth geometric objects (the represented function).

The mechanical intuition is this: pointwise convergence asks whether, for each $x$, the sequence of function values $f_n(x)$ eventually stabilizes near $f(x)$. Uniform convergence asks whether the entire family of sequences $(f_n(x))_{n=1}^\infty$, indexed by $x \in D$, stabilizes at a uniform rate, independent of position. The former is a pointwise interrogation; the latter is a global, metric property. The price of uniformity is a stronger hypothesis, but the reward is the preservation of structure: continuity, integrability, and differentiability all survive the passage to the limit. Mastery of these distinctions is indispensable for rigorous work in Fourier analysis, approximation theory, differential equations, and probability theory, where infinite processes are ubiquitous and limit interchange is the engine of computation.

## 2. Core Architecture & Mechanics

The formal architecture of function sequence convergence rests on two inequalities, each quantified differently. Let $(f_n)$ be a sequence of functions $f_n : D \to \mathbb{R}$ and let $f : D \to \mathbb{R}$ be a candidate limit function.

**Definition (Pointwise Convergence).** We say $f_n \to f$ pointwise on $D$ if for every $x \in D$ and every $\varepsilon > 0$, there exists $N = N(\varepsilon, x) \in \mathbb{N}$ such that
$$
n \ge N \implies |f_n(x) - f(x)| < \varepsilon.
$$
The quantifier structure is $\forall x \in D \ \forall \varepsilon > 0 \ \exists N(\varepsilon, x) \ \forall n \ge N$. The dependence of $N$ on both $\varepsilon$ and $x$ is explicit and unavoidable in general.

**Definition (Uniform Convergence).** We say $f_n \to f$ uniformly on $D$ if for every $\varepsilon > 0$, there exists $N = N(\varepsilon) \in \mathbb{N}$ such that
$$
n \ge N \implies |f_n(x) - f(x)| < \varepsilon \text{ for all } x \in D.
$$
The quantifier structure is $\forall \varepsilon > 0 \ \exists N(\varepsilon) \ \forall n \ge N \ \forall x \in D$. The order of quantifiers has changed: $N$ is chosen before $x$ is specified, enforcing uniformity across the domain.

Uniform convergence is equivalent to the statement that
$$
\lim_{n \to \infty} \sup_{x \in D} |f_n(x) - f(x)| = 0.
$$
This reformulation makes clear that uniform convergence is convergence in the **uniform norm** (or **supremum norm**)
$$
\|g\|_\infty = \sup_{x \in D} |g(x)|.
$$
The space of bounded functions on $D$ equipped with this norm becomes a normed vector space, and uniform convergence is precisely norm convergence in this space. This geometric perspective reveals why uniform convergence preserves continuity: the space $C_b(D)$ of bounded continuous functions on $D$ is a closed subspace of the space of all bounded functions, and limits of sequences in closed subspaces remain in the subspace.

**Theorem (Uniform Limit Theorem).** Let $(f_n)$ be a sequence of continuous functions on $D \subseteq \mathbb{R}$ converging uniformly to $f : D \to \mathbb{R}$. Then $f$ is continuous on $D$.

*Proof.* Fix $x_0 \in D$ and $\varepsilon > 0$. We must show that $f$ is continuous at $x_0$, i.e., there exists $\delta > 0$ such that $|x - x_0| < \delta$ implies $|f(x) - f(x_0)| < \varepsilon$. By uniform convergence, choose $N$ such that $\|f_n - f\|_\infty < \varepsilon/3$ for all $n \ge N$. Fix such an $n$. Since $f_n$ is continuous at $x_0$, there exists $\delta > 0$ such that $|x - x_0| < \delta$ implies $|f_n(x) - f_n(x_0)| < \varepsilon/3$. For any $x$ with $|x - x_0| < \delta$, we apply the triangle inequality:
$$
|f(x) - f(x_0)| \le |f(x) - f_n(x)| + |f_n(x) - f_n(x_0)| + |f_n(x_0) - f(x_0)| < \frac{\varepsilon}{3} + \frac{\varepsilon}{3} + \frac{\varepsilon}{3} = \varepsilon.
$$
Thus $f$ is continuous at $x_0$. Since $x_0$ was arbitrary, $f$ is continuous on $D$. $\square$

The proof architecture is the classic "$\varepsilon/3$-trick," a ubiquitous technique in analysis: we split the total error budget into three parts, using uniform convergence to control two parts and the continuity of $f_n$ to control the third. The key is that the uniform bound $\|f_n - f\|_\infty < \varepsilon/3$ works simultaneously at both $x$ and $x_0$, eliminating any dependence on the point.

For integration, uniform convergence permits the exchange of limit and integral:

**Theorem (Uniform Convergence and Integration).** Let $(f_n)$ be a sequence of Riemann integrable functions on $[a,b]$ converging uniformly to $f$ on $[a,b]$. Then $f$ is Riemann integrable on $[a,b]$, and
$$
\lim_{n \to \infty} \int_a^b f_n(x) \, dx = \int_a^b f(x) \, dx.
$$

*Proof.* Let $\varepsilon > 0$. Choose $N$ such that $|f_n(x) - f(x)| < \varepsilon / (2(b-a))$ for all $n \ge N$ and all $x \in [a,b]$. Then for $n \ge N$,
$$
\left| \int_a^b f_n(x) \, dx - \int_a^b f(x) \, dx \right| = \left| \int_a^b (f_n(x) - f(x)) \, dx \right| \le \int_a^b |f_n(x) - f(x)| \, dx < \int_a^b \frac{\varepsilon}{2(b-a)} \, dx = \frac{\varepsilon}{2}.
$$
Thus the sequence of integrals converges. To show $f$ is integrable, we use the fact that uniform limits of integrable functions are integrable (which follows from the Cauchy criterion for integrability and the uniform Cauchy criterion for sequences, details omitted for brevity). $\square$

The mechanical principle is that uniform convergence bounds the pointwise error $|f_n(x) - f(x)|$ independently of $x$, so integrating this error over $[a,b]$ simply multiplies by the length $b - a$, yielding a controlled total error.

For differentiation, uniform convergence of the functions $(f_n)$ alone is insufficient; we require uniform convergence of the derivatives $(f_n')$ along with pointwise convergence of $(f_n)$ at even a single point:

**Theorem (Term-by-Term Differentiation).** Let $(f_n)$ be a sequence of continuously differentiable functions on $[a,b]$ such that:
1. $(f_n(x_0))$ converges for some $x_0 \in [a,b]$.
2. $(f_n')$ converges uniformly on $[a,b]$ to a function $g$.

Then $(f_n)$ converges uniformly on $[a,b]$ to a function $f$, and $f$ is differentiable with $f' = g$.

*Proof.* For $m, n \in \mathbb{N}$ and $x \in [a,b]$, the Mean Value Theorem applied to $f_m - f_n$ on the interval between $x_0$ and $x$ gives
$$
(f_m(x) - f_n(x)) - (f_m(x_0) - f_n(x_0)) = (f_m' - f_n')(\xi) (x - x_0)
$$
for some $\xi$ between $x_0$ and $x$. Taking absolute values,
$$
|f_m(x) - f_n(x)| \le |f_m(x_0) - f_n(x_0)| + |f_m'(\xi) - f_n'(\xi)| \cdot |x - x_0| \le |f_m(x_0) - f_n(x_0)| + \|f_m' - f_n'\|_\infty (b - a).
$$
Since $(f_n(x_0))$ is Cauchy and $(f_n')$ is uniformly Cauchy, $(f_n)$ is uniformly Cauchy, hence converges uniformly to some $f$. By the Fundamental Theorem of Calculus,
$$
f_n(x) - f_n(x_0) = \int_{x_0}^x f_n'(t) \, dt.
$$
Taking $n \to \infty$ and using uniform convergence of $(f_n')$ to exchange limit and integral,
$$
f(x) - f(x_0) = \int_{x_0}^x g(t) \, dt.
$$
Differentiating both sides by the Fundamental Theorem, $f'(x) = g(x)$. $\square$

The architecture here is subtle: uniform convergence of the derivatives $(f_n')$ ensures that the Cauchy condition propagates uniformly via the Mean Value Theorem, forcing uniform convergence of $(f_n)$. The limit function $f$ then inherits differentiability from the integral representation.

For infinite series of functions, the partial sums $S_n(x) = \sum_{k=1}^n u_k(x)$ form a sequence of functions. We say the series $\sum_{k=1}^\infty u_k(x)$ **converges uniformly** on $D$ if the sequence $(S_n)$ converges uniformly on $D$. The Weierstrass M-test provides a practical sufficient condition:

**Theorem (Weierstrass M-Test).** Let $(u_k)$ be a sequence of functions on $D$. Suppose there exist constants $M_k \ge 0$ such that $|u_k(x)| \le M_k$ for all $x \in D$ and $\sum_{k=1}^\infty M_k < \infty$. Then $\sum_{k=1}^\infty u_k(x)$ converges uniformly and absolutely on $D$.

*Proof.* For $m > n$, we have
$$
\left| \sum_{k=n+1}^m u_k(x) \right| \le \sum_{k=n+1}^m |u_k(x)| \le \sum_{k=n+1}^m M_k.
$$
Since $\sum M_k$ converges, the tail $\sum_{k=n+1}^\infty M_k \to 0$ as $n \to \infty$. Given $\varepsilon > 0$, choose $N$ such that $\sum_{k=N+1}^\infty M_k < \varepsilon$. Then for all $m > n \ge N$ and all $x \in D$,
$$
\left| \sum_{k=n+1}^m u_k(x) \right| < \varepsilon,
$$
showing that the partial sums form a uniformly Cauchy sequence. By completeness, they converge uniformly. $\square$

The M-test architecture is elegant: we dominate the functional series by a convergent numerical series, converting the two-parameter problem (indexed by $k$ and $x$) into a one-parameter problem (indexed by $k$ alone). This majorization principle recurs throughout analysis, from comparison tests for series to dominated convergence for integrals.

**Example.** Consider $\sum_{k=1}^\infty \frac{\sin(kx)}{k^2}$ on $\mathbb{R}$. We have $|\sin(kx)| \le 1$, so $\left| \frac{\sin(kx)}{k^2} \right| \le \frac{1}{k^2}$. Since $\sum_{k=1}^\infty \frac{1}{k^2} = \frac{\pi^2}{6} < \infty$, the M-test guarantees uniform convergence on all of $\mathbb{R}$. Because each term $u_k(x) = \frac{\sin(kx)}{k^2}$ is continuous, the sum $f(x) = \sum_{k=1}^\infty \frac{\sin(kx)}{k^2}$ is continuous on $\mathbb{R}$ by the Uniform Limit Theorem.

For power series $\sum_{k=0}^\infty a_k (x - c)^k$, the convergence structure is determined by the **radius of convergence** $R$, defined by
$$
\frac{1}{R} = \limsup_{k \to \infty} |a_k|^{1/k}.
$$
Alternatively, if $\lim_{k \to \infty} \left| \frac{a_{k+1}}{a_k} \right|$ exists, then $R = \lim_{k \to \infty} \left| \frac{a_k}{a_{k+1}} \right|$ by the ratio test. The series converges absolutely for $|x - c| < R$, diverges for $|x - c| > R$, and requires individual analysis at the boundary points $x = c \pm R$.

**Theorem (Uniform Convergence of Power Series on Compact Subintervals).** Let $\sum_{k=0}^\infty a_k (x - c)^k$ have radius of convergence $R > 0$. For any $r < R$, the series converges uniformly on $[c - r, c + r]$.

*Proof.* For $|x - c| \le r < R$, we have $|a_k (x - c)^k| \le |a_k| r^k$. Since $r < R$, the series $\sum_{k=0}^\infty |a_k| r^k$ converges (by the definition of $R$). The M-test with $M_k = |a_k| r^k$ yields uniform convergence on $[c - r, c + r]$. $\square$

This uniformity on compact subsets permits term-by-term differentiation and integration within the interval of convergence:

**Theorem (Term-by-Term Differentiation of Power Series).** Let $f(x) = \sum_{k=0}^\infty a_k (x - c)^k$ with radius of convergence $R > 0$. Then $f$ is differentiable on $(c - R, c + R)$, and
$$
f'(x) = \sum_{k=1}^\infty k a_k (x - c)^{k-1}.
$$
The differentiated series has the same radius of convergence $R$.

*Proof sketch.* The radius of convergence of the differentiated series is
$$
R' = \lim_{k \to \infty} \frac{|k a_k|}{|(k+1) a_{k+1}|} = \lim_{k \to \infty} \frac{k}{k+1} \cdot \frac{|a_k|}{|a_{k+1}|} = 1 \cdot R = R.
$$
Fix $x_0 \in (c - R, c + R)$ and choose $r$ such that $|x_0 - c| < r < R$. On $[c - r, c + r]$, both the original series and the differentiated series converge uniformly. Applying the term-by-term differentiation theorem for uniformly convergent series on this interval yields $f'(x_0) = \sum_{k=1}^\infty k a_k (x_0 - c)^{k-1}$. $\square$

This result is profound: within the interval of convergence, a power series behaves like a polynomial of infinite degree, differentiable infinitely many times, with derivatives computed formally term-by-term. The machinery of uniform convergence on compact subsets guarantees the validity of these algebraic manipulations.

**Example.** The geometric series $\frac{1}{1-x} = \sum_{k=0}^\infty x^k$ converges for $|x| < 1$. Differentiating term-by-term,
$$
\frac{d}{dx} \frac{1}{1-x} = \frac{1}{(1-x)^2} = \sum_{k=1}^\infty k x^{k-1}.
$$
Substituting $x = 1/2$, we obtain $\sum_{k=1}^\infty k (1/2)^{k-1} = 4$, a result verifiable by other means but effortlessly derived via term-by-term differentiation.

## 3. High-Performance Optimization & Failure Modes

The practical workflow for proving uniform convergence of a function sequence or series involves a hierarchy of strategies, each suited to different structural features of the problem. The primary challenge is constructing the function $N(\varepsilon)$ explicitly, independent of $x$, or demonstrating that no such function exists.

**Strategy 1: Direct Estimation.** When $f_n(x)$ and $f(x)$ have closed-form expressions, attempt to bound $|f_n(x) - f(x)|$ uniformly in $x$. Factor out any $x$-dependence and show the remaining expression tends to zero. For example, consider $f_n(x) = \frac{x}{n}$ on $[0,1]$. We have $|f_n(x) - 0| = \frac{x}{n} \le \frac{1}{n}$ for all $x \in [0,1]$, so $\|f_n\|_\infty \le 1/n \to 0$, confirming uniform convergence to $f(x) = 0$. If the bound depends uncontrollably on $x$, such as $|f_n(x) - f(x)| \le g(x)/n$ where $g$ is unbounded, uniform convergence fails.

**Strategy 2: Negation via Counterexample.** To prove uniform convergence fails, exhibit a sequence of points $(x_n)$ such that $|f_n(x_n) - f(x_n)| \ge \delta$ for some fixed $\delta > 0$ and all $n$. This directly contradicts the existence of $N(\varepsilon)$ for $\varepsilon = \delta/2$. For $f_n(x) = x^n$ on $[0,1]$, we used $x_n = 1 - 1/n$ to show $|f_n(x_n) - f(x_n)| \approx e^{-1}$ remains bounded away from zero.

**Strategy 3: Cauchy Criterion.** A sequence $(f_n)$ converges uniformly on $D$ if and only if it is uniformly Cauchy: for every $\varepsilon > 0$, there exists $N$ such that $\|f_m - f_n\|_\infty < \varepsilon$ for all $m, n \ge N$. This criterion is indispensable when the limit function $f$ is not known in advance. It also underpins the completeness of the space $C_b(D)$ of bounded continuous functions, a cornerstone of functional analysis.

**Strategy 4: Weierstrass M-Test for Series.** For series $\sum u_k(x)$, search for a majorant sequence $(M_k)$ such that $|u_k(x)| \le M_k$ for all $x$ and $\sum M_k < \infty$. Geometric series, $p$-series, and exponential bounds are common majorants. If no majorant exists, uniform convergence may still hold but requires a different argument. If $\sum M_k$ diverges for every valid choice of $M_k$, investigate whether pointwise convergence holds but uniform convergence fails.

**Failure Mode 1: Slow Convergence Near Boundary Points.** Many sequences converge pointwise on an interval but fail uniform convergence because the rate degrades near a boundary. For $f_n(x) = n x (1 - x^n)$ on $[0,1]$, we have $f_n(0) = 0$ and $f_n(1) = 0$ for all $n$, and for $x \in (0,1)$, $f_n(x) \to 0$ as $n \to \infty$. However, $f_n(1 - 1/n) = n (1 - 1/n) (1 - (1 - 1/n)^n) \approx n \cdot 1 \cdot (1 - e^{-1}) \to \infty$, so convergence is not uniform. The obstruction is the concentration of mass near $x = 1$.

**Failure Mode 2: Discontinuous Limits of Continuous Functions.** As seen with $f_n(x) = x^n$, pointwise convergence of continuous functions can produce a discontinuous limit. This signals non-uniform convergence, as the Uniform Limit Theorem guarantees continuity under uniform convergence. Conversely, if you know $(f_n)$ are continuous and $f$ is discontinuous, you immediately deduce non-uniform convergence.

**Failure Mode 3: Non-Interchangeability of Limits.** Consider $f_n(x) = \frac{n x}{1 + n^2 x^2}$ on $[0, \infty)$. For any fixed $x > 0$, $f_n(x) \to 0$ as $n \to \infty$. However, $f_n(1/n) = \frac{n \cdot 1/n}{1 + n^2 (1/n)^2} = \frac{1}{2}$, so $\sup_{x \ge 0} f_n(x) \ge 1/2$ for all $n$, preventing uniform convergence. The phenomenon manifests in integration: $\int_0^\infty f_n(x) \, dx = \frac{\pi}{2}$ for all $n$ (computing via substitution), yet $\int_0^\infty \lim_{n \to \infty} f_n(x) \, dx = 0$. The failure to exchange limit and integral is diagnostic of non-uniform convergence.

**Optimization 1: Compact Subsets for Power Series.** When working with power series, never attempt to prove uniform convergence on the entire open interval $(c - R, c + R)$. Instead, prove uniform convergence on compact subintervals $[c - r, c + r]$ with $r < R$. The M-test works on these compact subsets, whereas it cannot handle the full open interval. This strategy underlies all rigorous treatments of analytic functions: properties are established on compact sets, then extended by exhaustion.

**Optimization 2: Dominated Convergence for Integrals.** When the domain is unbounded or functions are not uniformly bounded, the hypotheses of the uniform convergence theorem for integration may fail. The **Dominated Convergence Theorem** of Lebesgue integration theory provides a more flexible alternative: if $f_n \to f$ pointwise and $|f_n(x)| \le g(x)$ for all $n$ and $x$, where $g$ is integrable, then $\int f_n \to \int f$. This generalizes the Riemann theory and is essential for probability theory and functional analysis.

**Optimization 3: Dini's Theorem.** A powerful sharpening of the Uniform Limit Theorem applies when convergence is monotone. **Dini's Theorem** states: if $(f_n)$ is a monotone sequence of continuous functions on a compact set $K$ converging pointwise to a continuous function $f$, then convergence is uniform on $K$. This is a compactness phenomenon: monotonicity prevents oscillations, and compactness prevents escape to infinity. The proof uses the open cover definition of compactness applied to the sets $\{x : f_n(x) - f(x) < \varepsilon\}$. Dini's Theorem is invoked in approximation theory, where monotone approximations simplify convergence arguments.

**Optimization 4: Equicontinuity and Arzelà-Ascoli.** When proving uniform convergence of sequences constructed iteratively or via integral operators, pointwise arguments may be intractable. The **Arzelà-Ascoli Theorem** provides a compactness criterion: a sequence of functions on a compact set has a uniformly convergent subsequence if and only if the sequence is uniformly bounded and equicontinuous (the modulus of continuity is uniform in $n$). This theorem is fundamental in the study of differential equations, where solutions are constructed as limits of approximate solutions, and in numerical analysis, where discrete approximations must converge to continuous limits.

**Boundary Case: Power Series at the Radius of Convergence.** The behavior of $\sum a_k (x - c)^k$ at $x = c \pm R$ is subtle. The series $\sum_{k=1}^\infty \frac{1}{k} x^k$ (the logarithm series) converges for $x = -1$ (alternating harmonic series) but diverges for $x = 1$ (harmonic series). The series $\sum_{k=1}^\infty \frac{(-1)^k}{k} x^k$ converges conditionally at $x = 1$ to $-\ln(2)$ but diverges at $x = -1$. **Abel's Theorem** resolves continuity at the boundary: if $\sum a_k r^k$ converges at $x = r$ (a boundary point), then the power series function $f(x) = \sum a_k x^k$ is continuous from the left (or right) at $x = r$, i.e., $\lim_{x \to r^-} f(x) = \sum a_k r^k$. This permits evaluation of series via limits: $\ln(2) = \lim_{x \to 1^-} \sum_{k=1}^\infty \frac{(-1)^{k+1}}{k} x^k$. Abel's theorem relies on summation by parts (discrete integration by parts), a technique generalizing the analysis of alternating series.

**Workflow for Term-by-Term Differentiation.** Given a series $\sum u_k(x)$ that converges, to justify differentiation term-by-term, proceed in two stages. First, verify that each $u_k$ is differentiable and compute $u_k'(x)$. Second, prove that the series of derivatives $\sum u_k'(x)$ converges uniformly on the domain of interest, typically using the M-test. Uniform convergence of the derivatives guarantees uniform convergence of the original series and validates $\left( \sum u_k \right)' = \sum u_k'$. Skipping the uniform convergence check for the derivatives is a common error leading to incorrect results. For power series, the radius of convergence is preserved under differentiation, so uniform convergence on compact subsets is automatic.

**Workflow for Term-by-Term Integration.** Given $\sum u_k(x)$ converging uniformly on $[a,b]$ to $f(x)$, integration term-by-term is immediate:
$$
\int_a^b f(x) \, dx = \int_a^b \sum_{k=1}^\infty u_k(x) \, dx = \sum_{k=1}^\infty \int_a^b u_k(x) \, dx.
$$
No additional hypothesis beyond uniform convergence is required. For power series, integrating term-by-term also preserves the radius of convergence, and the constant of integration is determined by evaluating at a point within the interval of convergence.

The architectural principle underlying all these results is the interplay between local and global behavior. Pointwise convergence is a local property, interrogating behavior at individual points. Uniform convergence is a global property, demanding coherence across the entire domain simultaneously. The preservation of continuity, differentiability, and integrability under limits is not automatic but requires this global uniformity. The function space perspective—viewing $(f_n)$ as a sequence in the metric space $(C_b(D), \|\cdot\|_\infty)$—clarifies why uniform convergence is the natural topology for analysis: it is the topology that makes the space complete and the basic operations continuous. Mastery of these distinctions, along with fluency in the M-test, radius of convergence computations, and term-by-term manipulation theorems, equips the analyst to rigorously handle the infinite processes pervading modern mathematics, from Fourier series and Sturm-Liouville theory to probability generating functions and complex analysis.
