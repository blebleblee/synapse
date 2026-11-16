# Lesson 2: Elementary Transcendental Functions, Power Series, Radius of Convergence

## 1. First-Principles Intuition & Invariants

The transition from real analysis to complex analysis is not merely a change of domain; it is a qualitative restructuring of what a function *is*. On the real line, a differentiable function need not be twice differentiable, let alone analytic. The moment we admit complex numbers as the domain, the constraint tightens dramatically: a function that is complex-differentiable even once on an open set is automatically infinitely differentiable there, and its local behavior is completely governed by a convergent power series. This fact—that complex differentiability implies analyticity—is the deepest structural result of the theory, and it elevates power series from a convenient tool to the *defining characteristic* of the objects we study.

The right way to understand elementary transcendental functions in the complex setting is to *define* them by power series, not to extend their real graphs by analogy. The real exponential $e^x$ is continuous, monotone, and satisfies $e^{x+y} = e^x e^y$. None of these properties uniquely determine it on $\mathbb{R}$ without additional constraints, but the power series $e^z = \sum_{n=0}^{\infty} \frac{z^n}{n!}$ converges for every $z \in \mathbb{C}$, and on the real axis it reduces exactly to the familiar $e^x$. This power series definition is not an approximation or a continuation heuristic; it is the *primary* definition. The real exponential is the restriction of the complex exponential to $\mathbb{R}$, not the other way around. The same principle applies to the trigonometric and hyperbolic functions: we define $\cos z$, $\sin z$, $\cosh z$, and $\sinh z$ through the exponential and its power series, and the real versions emerge as special cases.

The logarithm, however, introduces the first genuinely complex-analytic phenomenon with no real counterpart: *multi-valuedness*. The equation $e^w = z$ has, for any nonzero $z$, infinitely many solutions differing by integer multiples of $2\pi i$. This is a direct consequence of the periodicity $e^{z + 2\pi i k} = e^z$, itself visible immediately from Euler's formula $e^{i\theta} = \cos\theta + i\sin\theta$. There is no way to select a single-valued branch of the logarithm on all of $\mathbb{C} \setminus \{0\}$ that remains continuous, let alone analytic. We must make a *branch cut*—a curve from the origin to infinity—across which the chosen branch jumps discontinuously. The existence of this obstruction is not an artifact of poor definitions; it is a topological fact, rooted in the nonzero winding of the punctured plane. The branch cut is the price of admission for single-valuedness, and choosing it wisely is a recurring practical and theoretical decision.

The unifying invariant of this entire lesson is the **radius of convergence**. Every power series $\sum_{n=0}^{\infty} a_n (z - z_0)^n$ has an associated disk $|z - z_0| < R$ inside which it converges absolutely and outside which it diverges. The boundary $|z - z_0| = R$ is the frontier where analyticity can break down, and the value of $R$ is dictated by the nearest singularity of the function the series represents. This is the content of the Cauchy–Hadamard theorem, and it provides the central diagnostic tool for understanding where a power series representation is valid. The identity theorem—arguing that two analytic functions agreeing on a set with an accumulation point must be identical—then ensures that the power series representation is *unique*: there is only one analytic function that matches a given series inside its disk of convergence, and any other representation or formula producing the same values on even a tiny arc must be the same function everywhere on the connected domain.

## 2. Core Architecture & Mechanics

### 2.1 The Cauchy–Hadamard Theorem and the Radius of Convergence

A power series centered at $z_0 \in \mathbb{C}$ is a series of the form $\sum_{n=0}^{\infty} a_n (z - z_0)^n$ where $a_n \in \mathbb{C}$ are fixed coefficients. The fundamental result governing its convergence is the following.

**Theorem (Cauchy–Hadamard).** *The power series $\sum_{n=0}^{\infty} a_n (z - z_0)^n$ has a radius of convergence*
$$R = \frac{1}{\limsup_{n \to \infty} |a_n|^{1/n}}$$
*with the conventions $1/0 = \infty$ and $1/\infty = 0$. The series converges absolutely for every $z$ with $|z - z_0| < R$ and diverges for every $z$ with $|z - z_0| > R$. On the boundary $|z - z_0| = R$, convergence is not determined by the theorem and depends on the specific coefficients.*

**Proof.** We apply the root test to the series $\sum |a_n| |z - z_0|^n$. The root test states that a series $\sum b_n$ of nonnegative terms converges if $\limsup_{n\to\infty} b_n^{1/n} < 1$ and diverges if $\limsup_{n\to\infty} b_n^{1/n} > 1$. Setting $b_n = |a_n| |z - z_0|^n$, we compute:

$$\limsup_{n \to \infty} b_n^{1/n} = \limsup_{n \to \infty} |a_n|^{1/n} \cdot |z - z_0| = |z - z_0| \cdot \limsup_{n \to \infty} |a_n|^{1/n}$$

Denote $L = \limsup_{n \to \infty} |a_n|^{1/n}$. Then $\limsup b_n^{1/n} = |z - z_0| \cdot L$. The series converges absolutely when $|z - z_0| \cdot L < 1$, that is, $|z - z_0| < 1/L = R$, and diverges when $|z - z_0| \cdot L > 1$, that is, $|z - z_0| > 1/L = R$. If $L = 0$ then $R = \infty$ and the series converges for all $z$. If $L = \infty$ then $R = 0$ and the series converges only at $z = z_0$. $\blacksquare$

When the limit $\lim_{n \to \infty} |a_n / a_{n+1}|$ exists (including as $\infty$), the **ratio test** provides an equivalent and often more computationally convenient formula:

$$R = \lim_{n \to \infty} \left|\frac{a_n}{a_{n+1}}\right|$$

This follows because if $|a_n / a_{n+1}| \to R$, then $|a_n|^{1/n} \to 1/R$ by a standard argument relating ratio and root tests. The root test via the Cauchy–Hadamard formula is strictly more general, however, since the limsup always exists (possibly as $\infty$) while the ratio limit may not.

### 2.2 Uniform Convergence and the Weierstrass M-Test

Absolute convergence inside the disk of convergence is only the first step. For the analytic machinery to function—term-by-term integration, term-by-term differentiation, continuity of the sum—we need **uniform convergence** on compact subsets. A power series does not generally converge uniformly on the entire open disk $|z - z_0| < R$, but it does converge uniformly on every closed disk $|z - z_0| \leq r$ with $r < R$. This is the content of the following result, proved via the Weierstrass M-test.

**Theorem.** *Let $\sum_{n=0}^{\infty} a_n (z - z_0)^n$ have radius of convergence $R > 0$. For any $r$ with $0 < r < R$, the series converges uniformly and absolutely on the closed disk $\overline{D}(z_0, r) = \{z : |z - z_0| \leq r\}$.*

**Proof.** Since $r < R$, the series $\sum_{n=0}^{\infty} |a_n| r^n$ converges (by the absolute convergence guaranteed by Cauchy–Hadamard). For every $z$ with $|z - z_0| \leq r$, we have $|a_n (z - z_0)^n| \leq |a_n| r^n =: M_n$. The series $\sum M_n = \sum |a_n| r^n$ converges, so by the Weierstrass M-test, $\sum a_n (z - z_0)^n$ converges uniformly and absolutely on $\overline{D}(z_0, r)$. $\blacksquare$

This theorem is the workhorse of complex power series theory. Uniform convergence on compact subsets is the precise condition needed for the sum to inherit continuity from its partial sums (each partial sum is a polynomial, hence continuous), and—combined with Morera's theorem—for the sum to inherit analyticity.

### 2.3 Analyticity of the Sum: Term-by-Term Differentiation

**Theorem.** *Let $f(z) = \sum_{n=0}^{\infty} a_n (z - z_0)^n$ converge for $|z - z_0| < R$. Then $f$ is analytic on this disk, and its derivative is obtained by term-by-term differentiation:*
$$f'(z) = \sum_{n=1}^{\infty} n \, a_n \, (z - z_0)^{n-1}$$
*This derived series has the same radius of convergence $R$.*

**Proof.** We first show the derived series $\sum_{n=1}^{\infty} n a_n (z - z_0)^{n-1}$ has the same radius of convergence. Its $n$-th coefficient (after reindexing) is $b_n = (n+1) a_{n+1}$ for the term $(z-z_0)^n$, so we need $\limsup |(n+1) a_{n+1}|^{1/n}$. Since $(n+1)^{1/n} \to 1$ as $n \to \infty$, and $|a_{n+1}|^{1/n} = |a_{n+1}|^{1/(n+1)} \cdot |a_{n+1}|^{1/n - 1/(n+1)}$, the second factor tends to $1$ whenever $|a_{n+1}|^{1/(n+1)}$ is bounded (which it is, since the original series has positive radius $R$). Therefore $\limsup |(n+1) a_{n+1}|^{1/n} = \limsup |a_n|^{1/n}$, and both series share the same radius $R$.

Now we prove $f$ is analytic and $f'$ equals the derived series. We use **Morera's theorem**: a continuous function on a domain that integrates to zero over every triangle contained in the domain is analytic. The partial sums $f_N(z) = \sum_{n=0}^{N} a_n (z - z_0)^n$ are polynomials, hence analytic, so by Cauchy's theorem $\oint_T f_N(z)\,dz = 0$ for every triangle $T$ in the disk. Since $f_N \to f$ uniformly on compact subsets (proved in §2.2), and $T$ is compact, for any $\epsilon > 0$ there exists $N_0$ such that $|f_N(z) - f(z)| < \epsilon$ on $T$ for all $N \geq N_0$. Then:

$$\left|\oint_T f(z)\,dz - \oint_T f_N(z)\,dz\right| = \left|\oint_T (f(z) - f_N(z))\,dz\right| \leq \epsilon \cdot \text{length}(T)$$

Since $\oint_T f_N(z)\,dz = 0$, we get $|\oint_T f(z)\,dz| \leq \epsilon \cdot \text{length}(T)$ for all $\epsilon > 0$, hence $\oint_T f(z)\,dz = 0$. By Morera's theorem, $f$ is analytic on $|z - z_0| < R$.

The fact that $f'$ equals the derived series now follows from the standard theory of Taylor series for analytic functions: since $f$ is analytic, it equals its Taylor series, and the Taylor coefficients of $f'$ are $n a_n$, giving $f'(z) = \sum_{n=1}^{\infty} n a_n (z - z_0)^{n-1}$. Alternatively, one can verify directly that the derived series converges uniformly on compact subsets and apply the classical theorem on term-by-term differentiation of uniformly convergent series of $C^1$ functions. $\blacksquare$

By induction, $f$ is infinitely differentiable, and the $k$-th derivative is:

$$f^{(k)}(z) = \sum_{n=k}^{\infty} n(n-1)\cdots(n-k+1) \, a_n \, (z - z_0)^{n-k} = k! \sum_{n=k}^{\infty} \binom{n}{k} a_n (z-z_0)^{n-k}$$

Evaluating at $z = z_0$ recovers the Taylor coefficients: $a_k = \frac{f^{(k)}(z_0)}{k!}$, the **Taylor formula**.

### 2.4 Abel's Theorem

The Cauchy–Hadamard theorem is silent about the boundary $|z - z_0| = R$. Abel's theorem addresses a different but related question: if a power series *happens* to converge at a boundary point, does the sum function approach that boundary value as $z$ approaches the boundary from inside the disk?

**Theorem (Abel).** *Let $\sum_{n=0}^{\infty} a_n$ be a convergent series of complex numbers with sum $s$. Then*
$$\lim_{r \to 1^-} \sum_{n=0}^{\infty} a_n r^n = s$$
*where $r$ is real and $0 < r < 1$. More generally, if $\sum a_n z_0^n$ converges for some $z_0$ on the boundary $|z_0| = R$, then $f(z) = \sum a_n z^n \to \sum a_n z_0^n$ as $z \to z_0$ from within the disk along a sector that does not become tangent to the boundary (Stolz sector).*

**Proof of the basic form.** We use **Abel's summation by parts** (also called Abel's lemma). Define the partial sums $s_n = \sum_{k=0}^{n} a_k$ with $s_{-1} = 0$, so that $a_n = s_n - s_{n-1}$. For $0 \leq r < 1$ and any $N \geq 0$:

$$\sum_{n=0}^{N} a_n r^n = \sum_{n=0}^{N} (s_n - s_{n-1}) r^n = (1-r) \sum_{n=0}^{N-1} s_n r^n + s_N r^N$$

This identity is verified by expanding the right side: $(1-r)\sum_{n=0}^{N-1} s_n r^n + s_N r^N = \sum_{n=0}^{N-1} s_n r^n - \sum_{n=0}^{N-1} s_n r^{n+1} + s_N r^N = s_0 + \sum_{n=1}^{N-1}(s_n - s_{n-1}) r^n + (s_N - s_{N-1}) r^N$ after telescoping, which equals $\sum_{n=0}^{N} a_n r^n$.

Since $s_n \to s$, write $s_n = s + \epsilon_n$ where $\epsilon_n \to 0$. Substituting:

$$\sum_{n=0}^{N} a_n r^n = (1-r)\sum_{n=0}^{N-1} (s + \epsilon_n) r^n + (s + \epsilon_N) r^N = s\left[(1-r)\sum_{n=0}^{N-1} r^n + r^N\right] + (1-r)\sum_{n=0}^{N-1} \epsilon_n r^n + \epsilon_N r^N$$

The bracket simplifies: $(1-r) \cdot \frac{1 - r^N}{1-r} + r^N = 1 - r^N + r^N = 1$. Therefore:

$$\sum_{n=0}^{N} a_n r^n = s + (1-r)\sum_{n=0}^{N-1} \epsilon_n r^n + \epsilon_N r^N$$

Taking $N \to \infty$ (the series $\sum a_n r^n$ converges for $r < 1$):

$$\sum_{n=0}^{\infty} a_n r^n - s = (1-r)\sum_{n=0}^{\infty} \epsilon_n r^n$$

Now let $\epsilon > 0$. Since $\epsilon_n \to 0$, choose $N_0$ such that $|\epsilon_n| < \epsilon/2$ for all $n \geq N_0$. Split the sum:

$$\left|(1-r)\sum_{n=0}^{\infty} \epsilon_n r^n\right| \leq (1-r)\sum_{n=0}^{N_0 - 1} |\epsilon_n| r^n + (1-r)\sum_{n=N_0}^{\infty} |\epsilon_n| r^n$$

For the tail, since $|\epsilon_n| < \epsilon/2$ for $n \geq N_0$:

$$(1-r)\sum_{n=N_0}^{\infty} |\epsilon_n| r^n \leq \frac{\epsilon}{2}(1-r)\sum_{n=N_0}^{\infty} r^n \leq \frac{\epsilon}{2}(1-r) \cdot \frac{r^{N_0}}{1-r} = \frac{\epsilon}{2} r^{N_0} < \frac{\epsilon}{2}$$

For the finite sum, let $M = \max_{0 \leq n < N_0} |\epsilon_n|$. Then:

$$(1-r)\sum_{n=0}^{N_0-1} |\epsilon_n| r^n \leq M \cdot N_0 \cdot (1-r)$$

Choose $\delta > 0$ such that $M N_0 (1-r) < \epsilon/2$ for $1 - \delta < r < 1$. Then for $r > 1 - \delta$:

$$\left|\sum_{n=0}^{\infty} a_n r^n - s\right| < \frac{\epsilon}{2} + \frac{\epsilon}{2} = \epsilon$$

This proves $\lim_{r \to 1^-} \sum a_n r^n = s$. $\blacksquare$

The practical import of Abel's theorem is that it allows us to compute sums of conditionally convergent series by evaluating a related power series and taking a radial limit. For instance, $\sum_{n=1}^{\infty} \frac{(-1)^{n+1}}{n} = \ln 2$ can be recovered from $\lim_{r \to 1^-} \sum_{n=1}^{\infty} \frac{(-1)^{n+1}}{n} r^n = \lim_{r \to 1^-} \ln(1+r) = \ln 2$.

### 2.5 The Identity Theorem

The identity theorem is the uniqueness principle of complex analysis. It says that an analytic function is completely determined by its values on any set with an accumulation point within the domain.

**Theorem (Identity Theorem).** *Let $f$ and $g$ be analytic on a domain (connected open set) $D$. If the set $S = \{z \in D : f(z) = g(z)\}$ has an accumulation point in $D$—that is, a point $z_0 \in D$ such that every neighborhood of $z_0$ contains a point of $S \setminus \{z_0\}$—then $f \equiv g$ on $D$.*

**Proof.** Let $h = f - g$, which is analytic on $D$. The set $S$ is the zero set of $h$, and $z_0 \in D$ is an accumulation point of zeros. Since $h$ is analytic at $z_0$, it has a Taylor expansion $h(z) = \sum_{n=0}^{\infty} c_n (z - z_0)^n$ valid in some disk $|z - z_0| < \rho$.

We claim all coefficients $c_n$ are zero. Suppose not, and let $m$ be the smallest index with $c_m \neq 0$. Then:

$$h(z) = (z - z_0)^m \underbrace{\sum_{k=0}^{\infty} c_{m+k} (z - z_0)^k}_{\phi(z)}$$

The function $\phi$ is analytic in $|z - z_0| < \rho$ and $\phi(z_0) = c_m \neq 0$. By continuity, there exists $\delta > 0$ such that $\phi(z) \neq 0$ for $|z - z_0| < \delta$. But then $h(z) = (z-z_0)^m \phi(z) \neq 0$ for $0 < |z - z_0| < \delta$, which contradicts $z_0$ being an accumulation point of zeros. Therefore $c_n = 0$ for all $n$, and $h \equiv 0$ on the disk $|z - z_0| < \rho$.

Now define $A = \{z \in D : h \text{ vanishes identically in a neighborhood of } z\}$. We have shown $z_0 \in A$, so $A \neq \varnothing$. The set $A$ is open by definition. We show $A$ is also closed in $D$: let $w$ be a limit point of $A$ in $D$. Since points arbitrarily close to $w$ lie in $A$, the function $h$ vanishes on a set accumulating at $w$. By the same argument as above (Taylor expansion at $w$), $h$ vanishes identically near $w$, so $w \in A$. Since $D$ is connected and $A$ is nonempty, open, and closed in $D$, we conclude $A = D$, so $h \equiv 0$ on $D$. $\blacksquare$

The identity theorem has an immediate and powerful corollary: if an analytic function on a domain $D$ vanishes on a line segment, a curve, an open disk, or any set with an accumulation point in $D$, it vanishes everywhere on $D$. This is how we transfer identities from the real line to the complex plane: if $\sin^2 x + \cos^2 x = 1$ for all $x \in \mathbb{R}$, then $\sin^2 z + \cos^2 z = 1$ for all $z \in \mathbb{C}$, because both sides are entire functions agreeing on $\mathbb{R}$, which has accumulation points.

### 2.6 The Complex Exponential

We define the **complex exponential** by its power series:

$$e^z = \exp(z) = \sum_{n=0}^{\infty} \frac{z^n}{n!}$$

The radius of convergence is $R = \infty$ since $|a_n|^{1/n} = (n!)^{-1/n} \to 0$ (by Stirling's approximation, $n! \approx \sqrt{2\pi n}(n/e)^n$, so $(n!)^{1/n} \approx n/e \to \infty$, hence $(n!)^{-1/n} \to 0$). The exponential is therefore **entire**—analytic on all of $\mathbb{C}$.

The fundamental algebraic property is the **addition formula** $e^{z+w} = e^z e^w$, which we prove directly from the power series using the **Cauchy product**. Since both series converge absolutely, we may multiply them term by term:

$$e^z \cdot e^w = \left(\sum_{n=0}^{\infty} \frac{z^n}{n!}\right)\left(\sum_{m=0}^{\infty} \frac{w^m}{m!}\right) = \sum_{k=0}^{\infty} \left(\sum_{j=0}^{k} \frac{z^j}{j!} \cdot \frac{w^{k-j}}{(k-j)!}\right) = \sum_{k=0}^{\infty} \frac{1}{k!} \sum_{j=0}^{k} \binom{k}{j} z^j w^{k-j}$$

By the binomial theorem, $\sum_{j=0}^{k} \binom{k}{j} z^j w^{k-j} = (z+w)^k$, so:

$$e^z \cdot e^w = \sum_{k=0}^{\infty} \frac{(z+w)^k}{k!} = e^{z+w}$$

Setting $z = iy$ (with $y$ real) and comparing with the Taylor series of the real sine and cosine:

$$e^{iy} = \sum_{n=0}^{\infty} \frac{(iy)^n}{n!} = \sum_{k=0}^{\infty} \frac{(iy)^{2k}}{(2k)!} + \sum_{k=0}^{\infty} \frac{(iy)^{2k+1}}{(2k+1)!} = \sum_{k=0}^{\infty} \frac{(-1)^k y^{2k}}{(2k)!} + i\sum_{k=0}^{\infty} \frac{(-1)^k y^{2k+1}}{(2k+1)!} = \cos y + i \sin y$$

This is **Euler's formula**. Combined with the addition law, for $z = x + iy$:

$$e^z = e^{x+iy} = e^x \cdot e^{iy} = e^x(\cos y + i \sin y)$$

so $|e^z| = e^x$ and $\arg(e^z) = y$. The exponential is **periodic** with period $2\pi i$: $e^{z + 2\pi i} = e^z \cdot e^{2\pi i} = e^z \cdot 1 = e^z$. This periodicity is the source of all multi-valuedness in the logarithm.

### 2.7 Trigonometric and Hyperbolic Functions

We define the complex trigonometric functions through the exponential:

$$\cos z = \frac{e^{iz} + e^{-iz}}{2}, \qquad \sin z = \frac{e^{iz} - e^{-iz}}{2i}$$

These are entire functions (linear combinations of entire functions). Their Taylor series, obtained by substituting into the exponential series, are:

$$\cos z = \sum_{k=0}^{\infty} \frac{(-1)^k z^{2k}}{(2k)!}, \qquad \sin z = \sum_{k=0}^{\infty} \frac{(-1)^k z^{2k+1}}{(2k+1)!}$$

both with infinite radius of convergence. On the real axis, these reduce to the classical real cosine and sine. The identity theorem then lifts all real trigonometric identities to the complex plane: $\sin^2 z + \cos^2 z = 1$ for all $z \in \mathbb{C}$, $\sin(z+w) = \sin z \cos w + \cos z \sin w$, and so on.

A notable departure from real behavior is that $\cos z$ and $\sin z$ are **unbounded** on $\mathbb{C}$. For instance, $\cos(iy) = \frac{e^{-y} + e^{y}}{2} = \cosh y$, which grows exponentially as $y \to \infty$. The boundedness of sine and cosine on $\mathbb{R}$ is an artifact of the real axis, not an intrinsic property of the functions.

The **hyperbolic functions** are defined by:

$$\cosh z = \frac{e^z + e^{-z}}{2}, \qquad \sinh z = \frac{e^z - e^{-z}}{2}$$

They relate to the trigonometric functions via $\cos(iz) = \cosh z$ and $\sin(iz) = i \sinh z$. The zeros of $\sin z$ are $z = n\pi$ for $n \in \mathbb{Z}$, and the zeros of $\cos z$ are $z = \frac{\pi}{2} + n\pi$ for $n \in \mathbb{Z}$, exactly as on the real line—a fact that follows from the identity theorem or from direct computation using the addition formula.

### 2.8 The Complex Logarithm and Multi-Valuedness

The logarithm is the inverse of the exponential, but because $e^z$ is periodic with period $2\pi i$, the inverse relation is not a function in the single-valued sense. For $z \neq 0$, writing $z = |z| e^{i\arg z}$ in polar form, the equation $e^w = z$ requires $e^{\text{Re}(w)} = |z|$ and $\text{Im}(w) = \arg z + 2\pi k$ for some $k \in \mathbb{Z}$. Therefore:

$$\log z = \ln|z| + i(\arg z + 2\pi k), \qquad k \in \mathbb{Z}$$

This is a **multi-valued function**: each nonzero $z$ has countably many logarithms, differing by integer multiples of $2\pi i$. The set of values is:

$$\text{Log}(z) = \{\ln|z| + i(\Arg z + 2\pi k) : k \in \mathbb{Z}\}$$

where $\Arg z \in (-\pi, \pi]$ is the **principal argument**.

To obtain a single-valued analytic branch, we restrict the domain by making a **branch cut**. The standard choice is the **principal logarithm**:

$$\text{Log}\, z = \ln|z| + i \Arg z, \qquad \Arg z \in (-\pi, \pi)$$

defined on the slit plane $\mathbb{C} \setminus (-\infty, 0]$. On this domain, $\text{Log}$ is analytic, and its derivative is $\frac{1}{z}$. This derivative formula is universal: every branch of the logarithm has derivative $1/z$ on its domain of analyticity, because locally the logarithm is an inverse of $e^w$ and $\frac{d}{dz} \log z = \frac{1}{e^{\log z}} = \frac{1}{z}$ by the inverse function theorem.

```
Branch cut for the principal logarithm Log z

        Im z
         ↑
         |    . . . . . .
         |  .   Domain of    .
         |.    analyticity     .
    ----●----+----+----+----→ Re z
    -∞  0   |        +∞
         |.    (slit: (-∞,0])  .
         |  .                .
         |    . . . . . .
         ↓
         
    Log z = ln|z| + i·Arg z,  Arg z ∈ (-π, π)
    Jump discontinuity: +2πi across the cut
```

The branch cut along $(-\infty, 0]$ is a convention, not a necessity. Any simple curve from the origin to infinity serves as a valid branch cut, and different cuts give different single-valued branches. For instance, cutting along the positive real axis with $\Arg z \in (0, 2\pi)$ gives a branch analytic on $\mathbb{C} \setminus [0, \infty)$. The choice of cut is a practical decision guided by the application: which region of the complex plane must remain free of discontinuities, and which paths of analytic continuation must be accommodated.

### 2.9 Complex Powers and Roots

Using the logarithm, we define $z^a = e^{a \log z}$ for $z \neq 0$ and $a \in \mathbb{C}$. Since $\log z$ is multi-valued, so is $z^a$ in general. For the principal branch:

$$z^a = e^{a\,\text{Log}\, z} = e^{a(\ln|z| + i\Arg z)}$$

When $a = n$ is a positive integer, $z^n = e^{n \log z}$ is single-valued because $e^{n \cdot 2\pi i k} = 1$ for all $k$, so all branches agree. When $a = 1/n$ (an $n$-th root), we get $n$ distinct values:

$$z^{1/n} = |z|^{1/n} e^{i(\Arg z + 2\pi k)/n}, \qquad k = 0, 1, \ldots, n-1$$

For irrational $a$, $z^a$ has countably many distinct values. The multi-valuedness of $z^a$ is governed by the **monodromy**: as $z$ traverses a loop around the origin, $\arg z$ increases by $2\pi$, and the value of $z^a$ multiplies by $e^{2\pi i a}$. If $a$ is an integer, this factor is $1$ and the function is single-valued. Otherwise, the function changes value upon encircling the branch point at $z = 0$.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Singularities Determine the Radius of Convergence

The most important practical consequence of the Taylor representation is that the radius of convergence of the Taylor series of an analytic function $f$ centered at $z_0$ equals the distance from $z_0$ to the nearest singularity of $f$. This gives a geometric, computational way to determine $R$ without calculating any limits of coefficients.

**Theorem.** *Let $f$ be analytic on a domain $D$ containing $z_0$, and let $z_1$ be the nearest point where $f$ fails to be analytic (a singularity, including poles, branch points, and essential singularities). Then the Taylor series of $f$ at $z_0$ has radius of convergence $R = |z_1 - z_0|$, the distance to the nearest singularity.*

The proof has two directions. First, $R \leq |z_1 - z_0|$: if the Taylor series converged beyond the nearest singularity, its sum would be analytic there (by the theorem on analyticity of power series sums), contradicting that $z_1$ is a singularity. Second, $R \geq |z_1 - z_0|$: $f$ is analytic on the open disk $|z - z_0| < |z_1 - z_0|$ (since there are no singularities inside), so by the Taylor expansion theorem, the Taylor series converges on this disk.

This result transforms the computation of $R$ from an analytic problem (limsup of coefficients) to a geometric one (locate the nearest singularity). For example, $f(z) = \frac{1}{1-z}$ has a pole at $z = 1$, so its Taylor series at $z_0 = 0$ has $R = 1$. The function $f(z) = \frac{1}{z^2 + 4} = \frac{1}{(z-2i)(z+2i)}$ has poles at $z = \pm 2i$, so the Taylor series at the origin has $R = 2$, the distance to the nearest pole. The function $\text{Log}(1+z)$ has a branch point at $z = -1$, so its Taylor series at $z_0 = 0$ has $R = 1$.

### 3.2 Numerical Evaluation: Horner's Method and Argument Reduction

For computational purposes, evaluating a power series $\sum_{n=0}^{N} a_n z^n$ directly requires $O(N^2)$ multiplications if done naively. **Horner's method** reorganizes the computation as:

$$\sum_{n=0}^{N} a_n z^n = a_0 + z(a_1 + z(a_2 + \cdots + z(a_{N-1} + z \cdot a_N)\cdots))$$

requiring only $O(N)$ multiplications and additions. This also improves numerical stability by reducing the number of intermediate overflow/underflow events.

For the exponential function specifically, direct evaluation of $\sum \frac{z^n}{n!}$ for large $|z|$ suffers from catastrophic cancellation: individual terms $|z|^n / n!$ can be enormous before the factorial eventually dominates. The standard **argument reduction** technique exploits the periodicity and the addition law. Write $z = x + iy$ and reduce $y$ modulo $2\pi$ to the range $[-\pi, \pi]$:

$$e^z = e^x \cdot e^{iy} = e^x \cdot e^{i(y \bmod 2\pi)}$$

Then $|e^{iy}| = 1$ and $|e^{iy} - 1| \leq 2$, so the power series $\sum \frac{(iy')^n}{n!}$ with $|y'| \leq \pi$ has terms bounded by $\pi^n / n!$, which converge rapidly and without catastrophic cancellation. The real exponential $e^x$ can similarly be reduced: for large $x$, write $x = m \ln 2 + r$ with $|r| \leq \ln 2 / 2$ and compute $e^x = 2^m \cdot e^r$, where $e^r$ is evaluated by the series with $|r| \leq 0.347$, giving rapid convergence.

### 3.3 Branch Cut Selection as an Optimization Problem

The choice of branch cut is not merely conventional; it has real consequences for computation and for the validity of identities. Consider the identity $\log(z_1 z_2) = \log z_1 + \log z_2$, which holds for positive real numbers but **fails** for the principal logarithm in general. For example, $z_1 = z_2 = -1$ gives $\text{Log}(z_1 z_2) = \text{Log}(1) = 0$, while $\text{Log}(z_1) + \text{Log}(z_2) = i\pi + i\pi = 2\pi i$. The correct statement is:

$$\log(z_1 z_2) = \log z_1 + \log z_2 \pmod{2\pi i}$$

For the principal branch, $\text{Log}(z_1 z_2) = \text{Log}\, z_1 + \text{Log}\, z_2$ holds when $-\pi < \Arg z_1 + \Arg z_2 \leq \pi$, and fails (differs by $\pm 2\pi i$) otherwise. This boundary failure occurs when the product $z_1 z_2$ crosses the branch cut.

A practical strategy for multi-function computations is to choose all branch cuts to lie along the same ray, so that the domain of analyticity is consistent across all functions involved. For example, if the computation involves $\text{Log}\, z$, $\sqrt{z}$, and $z^{1/3}$, choosing all cuts along $(-\infty, 0]$ ensures they are simultaneously analytic on $\mathbb{C} \setminus (-\infty, 0]$, and compositions remain valid throughout this domain.

### 3.4 Natural Boundaries and the Limits of Analytic Continuation

Not every power series can be analytically continued beyond its disk of convergence. When the entire boundary $|z - z_0| = R$ consists of singularities, the boundary is a **natural boundary**, and no continuation is possible in any direction.

A classical example is the **lacunary series** $f(z) = \sum_{k=0}^{\infty} z^{n_k}$ where $n_k$ grows sufficiently fast (the Hadamard gap theorem gives the precise condition $n_{k+1}/n_k \geq q > 1$). For instance, $f(z) = \sum_{k=0}^{\infty} z^{2^k} = z + z^2 + z^4 + z^8 + \cdots$ has radius of convergence $R = 1$ (since $\limsup |a_n|^{1/n} = 1$), and the unit circle $|z| = 1$ is a natural boundary. Every point on $|z| = 1$ is a singularity, so the function cannot be extended beyond the unit disk by any means.

This stands in contrast to "generic" power series like $\sum z^n / n = -\text{Log}(1-z)$, which has $R = 1$ but only one singularity (at $z = 1$) on the boundary. This series can be analytically continued to all of $\mathbb{C} \setminus [1, \infty)$. The lesson is that the boundary behavior is not determined by $R$ alone; it depends on the arithmetic structure of the coefficients.

### 3.5 Failure Modes: A Catalogue of Pitfalls

Several common errors arise when transferring real-function intuition to the complex setting.

**Failure of square root multiplicativity.** The identity $\sqrt{z_1 z_2} = \sqrt{z_1}\sqrt{z_2}$ fails for the principal branch. Taking $z_1 = z_2 = -1$: the left side gives $\sqrt{(-1)(-1)} = \sqrt{1} = 1$, while the right side gives $\sqrt{-1}\sqrt{-1} = i \cdot i = -1$. The correct identity, holding modulo the monodromy, is $\sqrt{z_1 z_2} = \pm\sqrt{z_1}\sqrt{z_2}$, with the sign depending on the arguments.

**Failure of the intermediate value property.** On the real line, $e^x$ is monotone, so $e^x = c$ has a unique real solution for $c > 0$. In the complex plane, $e^z = c$ has infinitely many solutions for every $c \neq 0$, spaced $2\pi i$ apart. Similarly, $\sin z = w$ has solutions for every $w \in \mathbb{C}$ (not just $w \in [-1, 1]$), because $\sin z = \frac{e^{iz} - e^{-iz}}{2i}$ is a surjection onto $\mathbb{C}$.

**Confusing analyticity with continuity across a branch cut.** A branch of $\text{Log}\, z$ is continuous up to the branch cut from one side but jumps by $2\pi i$ when crossing it. Numerical code that evaluates $\text{Log}\, z$ for $z$ near the cut must account for this discontinuity; naively passing $z$ from one side of the cut to the other will produce a jump of $2\pi i$ in the output, which can cascade into large errors in downstream computations involving $z^a$, $\log(\Gamma(z))$, or other functions built on the logarithm.

**Assuming the radius of convergence is infinite.** The exponential, sine, and cosine are entire, but most functions arising in practice are not. The function $\frac{\sin z}{z}$ (with the removable singularity at $z = 0$ filled in as $1$) is entire, but $\frac{1}{\sin z}$ has poles at $z = n\pi$ and its Taylor series at $z_0 = 1$ has radius $R = \pi$ (the distance to the nearest pole at $z = 0$ or $z = \pi$). Misjudging $R$ leads to using a series outside its domain of validity, producing silently incorrect results.

**Overlooking branch points when determining $R$.** The function $f(z) = \sqrt{z}$ has a branch point at $z = 0$. Its Taylor series at $z_0 = 1$ is $\sum_{n=0}^{\infty} \binom{1/2}{n} (z-1)^n$ with $R = 1$, the distance to the branch point. The boundary point $z = 0$ is not a pole or an essential singularity; it is a branch point, which is equally an obstruction to analytic continuation and equally sets the radius of convergence.
