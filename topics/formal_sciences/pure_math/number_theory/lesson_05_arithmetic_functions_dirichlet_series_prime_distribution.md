# Lesson 5: Arithmetic Functions, Möbius Inversion, Dirichlet Series, the Distribution of Primes

## 1. First-Principles Intuition & Invariants

The architecture of multiplicative number theory rests upon a single foundational observation: integers possess a prime factorization structure that propagates through arithmetic operations in predictable, exploitable patterns. When we study functions $f : \mathbb{N} \to \mathbb{C}$ that respect this multiplicative skeleton—functions satisfying $f(mn) = f(m)f(n)$ whenever $\gcd(m,n) = 1$—we unlock a powerful algebraic calculus that transforms summation problems into product manipulations, inverts intricate counting formulas through elegant transform pairs, and reveals the asymptotic distribution of primes through analytic continuation.

The theory of arithmetic functions begins with the recognition that many naturally occurring number-theoretic quantities exhibit multiplicative or additive behavior. The Euler totient function $\phi(n)$, counting integers coprime to $n$, is multiplicative: if $m$ and $n$ share no common factors, then the Chinese Remainder Theorem guarantees that $\phi(mn) = \phi(m)\phi(n)$ through an explicit bijection between residue classes. The divisor sum function $\sigma_k(n) = \sum_{d \mid n} d^k$ inherits multiplicativity from the factorization lattice: divisors of $mn$ factor uniquely as products of divisors of $m$ and divisors of $n$ when $\gcd(m,n) = 1$. Even the humble constant function $\mathbf{1}(n) = 1$ and the identity function $\text{id}(n) = n$ are multiplicative, forming the multiplicative and additive identities of our function algebra.

The Möbius function $\mu(n)$ emerges as the multiplicative inverse of the constant function $\mathbf{1}$ within the ring of arithmetic functions equipped with Dirichlet convolution. Defined by $\mu(1) = 1$, $\mu(p_1 p_2 \cdots p_k) = (-1)^k$ for distinct primes, and $\mu(n) = 0$ if $n$ has a squared prime factor, this function encodes inclusion-exclusion combinatorics at the level of prime factorization. The remarkable Möbius inversion formula asserts that if $g(n) = \sum_{d \mid n} f(d)$, then $f(n) = \sum_{d \mid n} \mu(d) g(n/d)$, providing an explicit inversion mechanism that reverses divisor summations. This transform pair appears throughout enumerative combinatorics, lattice theory, and the analysis of arithmetic progressions.

Dirichlet series $F(s) = \sum_{n=1}^\infty \frac{f(n)}{n^s}$ provide the analytic continuation machinery that connects discrete arithmetic functions to continuous complex analysis. When $f$ is multiplicative, the series factors as an Euler product $F(s) = \prod_p \left(1 + \frac{f(p)}{p^s} + \frac{f(p^2)}{p^{2s}} + \cdots \right)$, transforming summation over integers into multiplication over primes. The Riemann zeta function $\zeta(s) = \sum_{n=1}^\infty n^{-s} = \prod_p (1 - p^{-s})^{-1}$ sits at the apex of this theory, its analytic properties encoding the distribution of primes through the Prime Number Theorem: $\pi(x) \sim x / \log x$ as $x \to \infty$. The zero-free region of $\zeta(s)$ near the line $\Re(s) = 1$ translates directly into quantitative bounds on prime gaps and the accuracy of logarithmic prime density estimates.

Dirichlet's theorem on primes in arithmetic progressions extends this analytic machinery to congruence classes: for coprime integers $a$ and $q$, the arithmetic progression $a, a+q, a+2q, \ldots$ contains infinitely many primes, with density $1/\phi(q)$ relative to all primes. The proof introduces Dirichlet $L$-functions $L(s, \chi) = \sum_{n=1}^\infty \chi(n) n^{-s}$, where $\chi$ is a character modulo $q$, and establishes non-vanishing at $s = 1$ through a delicate argument distinguishing principal and non-principal characters. This theorem constitutes the first major result in analytic number theory beyond the classical distribution of all primes, opening the door to modern sieve methods, the Chebotarev density theorem, and the Langlands program.

Throughout this lesson, we adopt the convention that all sums and products over divisors or primes are understood to range over positive integers unless otherwise specified. The variable $s$ in Dirichlet series denotes a complex number $s = \sigma + it$ with real part $\sigma = \Re(s)$ and imaginary part $t = \Im(s)$. Multiplicative functions are always understood to satisfy $f(1) = 1$ as a normalization convention, ensuring that Euler products converge to the correct Dirichlet series in the region of absolute convergence.

## 2. Core Architecture & Mechanics

### Multiplicative and Additive Function Taxonomy

An arithmetic function $f : \mathbb{N} \to \mathbb{C}$ is **completely multiplicative** if $f(mn) = f(m)f(n)$ for all positive integers $m, n$, and **multiplicative** if this equality holds whenever $\gcd(m,n) = 1$. The distinction is critical: completely multiplicative functions are determined entirely by their values on primes, since $f(p^k) = f(p)^k$ follows immediately. Multiplicative functions require specifying $f(p^k)$ independently for each prime power, but the Chinese Remainder Theorem guarantees that $f(n) = \prod_{p^k \| n} f(p^k)$, where $p^k \| n$ denotes the exact power of $p$ dividing $n$.

The principal examples establish the landscape. The constant function $\mathbf{1}(n) = 1$ is completely multiplicative. The identity function $\text{id}(n) = n$ is completely multiplicative. The Euler totient function $\phi(n) = \#\{1 \le k \le n : \gcd(k,n) = 1\}$ is multiplicative but not completely multiplicative, since $\phi(p^k) = p^{k-1}(p-1) \ne \phi(p)^k = (p-1)^k$ for $k \ge 2$. The divisor function $d(n) = \sum_{d \mid n} 1$ counts divisors and satisfies $d(p^k) = k+1$, making it multiplicative with the factorization formula $d(n) = \prod_{p^k \| n} (k+1)$.

An arithmetic function $f$ is **additive** if $f(mn) = f(m) + f(n)$ whenever $\gcd(m,n) = 1$, and **completely additive** if this holds for all $m, n$. The prime omega functions illustrate this dichotomy: $\Omega(n)$ counts prime factors with multiplicity, so $\Omega(12) = \Omega(2^2 \cdot 3) = 3$, and is completely additive. The function $\omega(n)$ counts distinct prime factors, so $\omega(12) = 2$, and is merely additive. The logarithm $\log n$ is completely additive, transforming multiplication into addition and providing the fundamental link between multiplicative structure and linear analysis.

To compute $\phi(n)$ constructively, we employ the prime factorization $n = \prod_{i=1}^r p_i^{k_i}$. Since $\phi$ is multiplicative, $\phi(n) = \prod_{i=1}^r \phi(p_i^{k_i})$. For a prime power $p^k$, the integers in $\{1, 2, \ldots, p^k\}$ that share a common factor with $p^k$ are precisely the multiples of $p$, of which there are $p^{k-1}$. Thus $\phi(p^k) = p^k - p^{k-1} = p^{k-1}(p-1)$, yielding the formula

$$\phi(n) = n \prod_{p \mid n} \left(1 - \frac{1}{p}\right).$$

This product representation exhibits $\phi$ as a multiplicative function built from completely multiplicative components, a pattern that recurs throughout the theory.

### Dirichlet Convolution Algebra

The set of arithmetic functions forms a commutative ring under pointwise addition and Dirichlet convolution. Given functions $f$ and $g$, their Dirichlet convolution $(f * g)(n)$ is defined by

$$(f * g)(n) = \sum_{d \mid n} f(d) g(n/d) = \sum_{ab = n} f(a) g(b),$$

where the sum ranges over all ordered factorizations of $n$. This operation is commutative by the symmetry $d \leftrightarrow n/d$, associative by reorganizing sums over divisors, and has the identity element $\mathbf{e}(n) = \begin{cases} 1 & n = 1 \\ 0 & n > 1 \end{cases}$, since $(f * \mathbf{e})(n) = f(n) \cdot 1 = f(n)$.

The Möbius function $\mu$ serves as the multiplicative inverse of the constant function $\mathbf{1}$ within this ring structure: $(\mu * \mathbf{1})(n) = \sum_{d \mid n} \mu(d) = \mathbf{e}(n)$. To verify this identity, observe that for $n = 1$, the sum contains only $\mu(1) = 1$, giving $\mathbf{e}(1) = 1$. For $n = p_1^{k_1} \cdots p_r^{k_r}$ with $r \ge 1$, multiplicativity of both $\mu$ and $\mathbf{1}$ implies that the convolution is also multiplicative, so it suffices to verify the identity on prime powers. For $n = p^k$ with $k \ge 1$, the divisors are $1, p, p^2, \ldots, p^k$, and $\mu(p^j) = 0$ for $j \ge 2$, leaving

$$\sum_{d \mid p^k} \mu(d) = \mu(1) + \mu(p) = 1 + (-1) = 0 = \mathbf{e}(p^k).$$

This calculation establishes the fundamental inversion relation $\mu * \mathbf{1} = \mathbf{e}$.

The Möbius inversion formula emerges by convolving both sides of an identity with $\mu$. Suppose $g = f * \mathbf{1}$, meaning $g(n) = \sum_{d \mid n} f(d)$. Convolving both sides with $\mu$ yields

$$\mu * g = \mu * (f * \mathbf{1}) = (\mu * \mathbf{1}) * f = \mathbf{e} * f = f,$$

where we have used associativity of Dirichlet convolution. Expanding $(\mu * g)(n)$ explicitly gives

$$f(n) = \sum_{d \mid n} \mu(d) g(n/d) = \sum_{d \mid n} \mu(n/d) g(d),$$

both forms being equivalent by the substitution $d \leftrightarrow n/d$. This inversion formula provides the explicit inverse transform: given the divisor sum $g$, we recover $f$ by a weighted sum involving the Möbius function.

As a canonical application, consider the sum of Euler totient values over divisors. Define $g(n) = \sum_{d \mid n} \phi(d)$. By a direct counting argument, every integer $k$ in $\{1, 2, \ldots, n\}$ has $\gcd(k, n) = d$ for exactly one divisor $d$ of $n$, and there are $\phi(n/d)$ such integers $k$. Summing over all divisors yields $n = \sum_{d \mid n} \phi(d)$, so $g(n) = n = \text{id}(n)$. Möbius inversion immediately gives

$$\phi(n) = \sum_{d \mid n} \mu(d) \cdot (n/d) = n \sum_{d \mid n} \frac{\mu(d)}{d},$$

recovering the product formula $\phi(n) = n \prod_{p \mid n} (1 - 1/p)$ through the factorization of the Möbius-weighted divisor sum.

The convolution algebra respects multiplicativity: if $f$ and $g$ are both multiplicative, then $f * g$ is multiplicative. The proof proceeds by verifying the identity on coprime arguments. For $\gcd(m, n) = 1$, every divisor $d$ of $mn$ factors uniquely as $d = d_1 d_2$ with $d_1 \mid m$ and $d_2 \mid n$, so

$$(f * g)(mn) = \sum_{d \mid mn} f(d) g(mn/d) = \sum_{d_1 \mid m} \sum_{d_2 \mid n} f(d_1 d_2) g(mn / d_1 d_2).$$

Since $f$ and $g$ are multiplicative and $\gcd(d_1, d_2) = 1$, we have $f(d_1 d_2) = f(d_1) f(d_2)$ and $g(mn / d_1 d_2) = g(m/d_1) g(n/d_2)$, yielding

$$(f * g)(mn) = \left(\sum_{d_1 \mid m} f(d_1) g(m/d_1)\right) \left(\sum_{d_2 \mid n} f(d_2) g(n/d_2)\right) = (f * g)(m) (f * g)(n),$$

confirming multiplicativity of the convolution product.

### Dirichlet Series and Euler Products

A Dirichlet series associates to an arithmetic function $f$ the complex function

$$F(s) = \sum_{n=1}^\infty \frac{f(n)}{n^s},$$

defined for complex $s = \sigma + it$ where the series converges. Absolute convergence holds in the half-plane $\sigma > \sigma_a$ for some abscissa $\sigma_a$, and conditional convergence may extend to $\sigma > \sigma_c \le \sigma_a$. The prototypical example is the Riemann zeta function

$$\zeta(s) = \sum_{n=1}^\infty \frac{1}{n^s},$$

which converges absolutely for $\Re(s) > 1$ and admits analytic continuation to $\mathbb{C} \setminus \{1\}$ with a simple pole at $s = 1$.

When $f$ is multiplicative, the Dirichlet series factors as an Euler product over primes. The fundamental factorization theorem states that for $\Re(s) > \sigma_a$,

$$\sum_{n=1}^\infty \frac{f(n)}{n^s} = \prod_{p \text{ prime}} \left( \sum_{k=0}^\infty \frac{f(p^k)}{p^{ks}} \right).$$

To establish this identity, consider the finite product over primes $p \le N$. By multiplicativity and the fundamental theorem of arithmetic, expanding the product yields

$$\prod_{p \le N} \left( \sum_{k=0}^\infty \frac{f(p^k)}{p^{ks}} \right) = \sum_{\substack{n \ge 1 \\ p \mid n \Rightarrow p \le N}} \frac{f(n)}{n^s},$$

where the sum ranges over integers whose prime factors all satisfy $p \le N$. As $N \to \infty$, this set exhausts all positive integers, and absolute convergence justifies interchanging the limit with summation, yielding the Euler product formula.

For the Riemann zeta function, $f(n) = 1$ is completely multiplicative, so $f(p^k) = 1$ and

$$\zeta(s) = \prod_{p} \left( \sum_{k=0}^\infty \frac{1}{p^{ks}} \right) = \prod_{p} \frac{1}{1 - p^{-s}},$$

valid for $\Re(s) > 1$. This Euler product encodes the unique factorization of integers into primes: each integer $n = \prod p_i^{k_i}$ contributes exactly once to the product expansion. Taking logarithms gives

$$\log \zeta(s) = -\sum_p \log(1 - p^{-s}) = \sum_p \sum_{k=1}^\infty \frac{1}{k p^{ks}} = \sum_p \frac{1}{p^s} + O(1),$$

where the error term $O(1)$ accounts for higher prime powers. This logarithmic formula reveals that $\zeta(s)$ has no zeros in $\Re(s) > 1$, since the Euler product converges to a non-zero value, and establishes the heuristic that the density of primes is captured by the singularity of $\zeta(s)$ at $s = 1$.

The Dirichlet convolution of arithmetic functions corresponds to ordinary multiplication of their Dirichlet series. If $h = f * g$, then

$$H(s) = \sum_{n=1}^\infty \frac{h(n)}{n^s} = \sum_{n=1}^\infty \frac{1}{n^s} \sum_{d \mid n} f(d) g(n/d) = \left( \sum_{d=1}^\infty \frac{f(d)}{d^s} \right) \left( \sum_{m=1}^\infty \frac{g(m)}{m^s} \right) = F(s) G(s),$$

where the interchange of summation is justified by absolute convergence. This correspondence transforms convolution inversion problems into division of analytic functions. For instance, since $\mu * \mathbf{1} = \mathbf{e}$, we have $M(s) \zeta(s) = 1$, where $M(s) = \sum_{n=1}^\infty \mu(n) n^{-s}$ is the Dirichlet series of the Möbius function. Thus $M(s) = 1/\zeta(s)$, and the reciprocal of the zeta function encodes the Möbius function through its Dirichlet coefficients.

### The Prime Number Theorem: Analytic Foundations

The Prime Number Theorem asserts that the prime counting function $\pi(x) = \#\{p \le x : p \text{ prime}\}$ satisfies

$$\pi(x) \sim \frac{x}{\log x} \quad \text{as } x \to \infty,$$

meaning $\lim_{x \to \infty} \pi(x) / (x / \log x) = 1$. Equivalently, the $n$-th prime $p_n$ satisfies $p_n \sim n \log n$. This theorem quantifies the density of primes and validates the logarithmic integral approximation $\text{Li}(x) = \int_2^x \frac{dt}{\log t}$, which provides a more accurate estimate: $\pi(x) = \text{Li}(x) + O(x e^{-c \sqrt{\log x}})$ for some constant $c > 0$.

The proof strategy involves analyzing the Riemann zeta function $\zeta(s)$ and the von Mangoldt function $\Lambda(n)$, defined by $\Lambda(n) = \log p$ if $n = p^k$ for a prime $p$ and integer $k \ge 1$, and $\Lambda(n) = 0$ otherwise. The Chebyshev function $\psi(x) = \sum_{n \le x} \Lambda(n)$ counts primes with logarithmic weights and satisfies $\psi(x) \sim x$, which implies the Prime Number Theorem through partial summation.

The Dirichlet series of $\Lambda$ is

$$-\frac{\zeta'(s)}{\zeta(s)} = \sum_{n=1}^\infty \frac{\Lambda(n)}{n^s},$$

valid for $\Re(s) > 1$. To verify this, differentiate the Euler product $\zeta(s) = \prod_p (1 - p^{-s})^{-1}$ logarithmically:

$$\frac{\zeta'(s)}{\zeta(s)} = \sum_p \frac{d}{ds} \log(1 - p^{-s})^{-1} = \sum_p \frac{\log p \cdot p^{-s}}{1 - p^{-s}} = \sum_p \sum_{k=1}^\infty \frac{\log p}{p^{ks}} = \sum_{n=1}^\infty \frac{\Lambda(n)}{n^s},$$

confirming the identity. The logarithmic derivative $-\zeta'(s)/\zeta(s)$ thus encodes prime powers through the von Mangoldt function.

By Perron's formula and contour integration, the sum $\psi(x) = \sum_{n \le x} \Lambda(n)$ can be expressed as an integral involving $-\zeta'(s)/\zeta(s)$:

$$\psi(x) = \frac{1}{2\pi i} \int_{c - i\infty}^{c + i\infty} \left( -\frac{\zeta'(s)}{\zeta(s)} \right) \frac{x^s}{s} \, ds,$$

where $c > 1$. Shifting the contour to the left and applying the residue theorem, the integral picks up contributions from the pole of $\zeta(s)$ at $s = 1$ and from zeros of $\zeta(s)$ in the critical strip $0 < \Re(s) < 1$. The residue at $s = 1$ yields the main term $x$, while zeros contribute error terms.

The critical step is establishing a zero-free region for $\zeta(s)$ near the line $\Re(s) = 1$. Hadamard and de la Vallée Poussin independently proved that $\zeta(s) \ne 0$ for $\Re(s) \ge 1$, which suffices to deduce $\psi(x) = x + o(x)$ and hence $\pi(x) \sim x / \log x$. The proof of the zero-free region employs the inequality

$$3 + 4 \cos \theta + \cos 2\theta = 2(1 + \cos \theta)^2 \ge 0,$$

which implies $|\zeta(\sigma)|^3 |\zeta(\sigma + it)|^4 |\zeta(\sigma + 2it)| \ge 1$ for $\sigma > 1$. As $\sigma \to 1^+$, the pole of $\zeta(\sigma)$ dominates, forcing $\zeta(1 + it) \ne 0$ for all $t \ne 0$. A more delicate argument extends this to a region $\Re(s) \ge 1 - c / \log(|t| + 2)$ for some constant $c > 0$, which yields the error term $\psi(x) = x + O(x e^{-c \sqrt{\log x}})$ through explicit residue calculations.

### Dirichlet $L$-Functions and Primes in Arithmetic Progressions

Dirichlet's theorem on primes in arithmetic progressions asserts that for coprime integers $a$ and $q$, the congruence class $a \pmod{q}$ contains infinitely many primes. Moreover, the density of such primes is $1/\phi(q)$, meaning

$$\lim_{x \to \infty} \frac{\#\{p \le x : p \equiv a \pmod{q}\}}{\pi(x)} = \frac{1}{\phi(q)}.$$

The proof introduces Dirichlet characters $\chi : (\mathbb{Z}/q\mathbb{Z})^\times \to \mathbb{C}^\times$, which are group homomorphisms from the multiplicative group of units modulo $q$ to the non-zero complex numbers. Extending $\chi$ to all integers by $\chi(n) = 0$ if $\gcd(n, q) > 1$, we define the Dirichlet $L$-function

$$L(s, \chi) = \sum_{n=1}^\infty \frac{\chi(n)}{n^s} = \prod_{p} \frac{1}{1 - \chi(p) p^{-s}},$$

converging absolutely for $\Re(s) > 1$. The trivial character $\chi_0(n) = 1$ if $\gcd(n, q) = 1$ and $\chi_0(n) = 0$ otherwise yields $L(s, \chi_0) = \zeta(s) \prod_{p \mid q} (1 - p^{-s})$, which has a pole at $s = 1$.

The orthogonality relations for Dirichlet characters provide a sieve mechanism. For any integer $n$ and residue class $a \pmod{q}$ with $\gcd(a, q) = 1$,

$$\frac{1}{\phi(q)} \sum_{\chi \pmod{q}} \overline{\chi(a)} \chi(n) = \begin{cases} 1 & n \equiv a \pmod{q}, \gcd(n,q) = 1 \\ 0 & \text{otherwise}, \end{cases}$$

where the sum ranges over all $\phi(q)$ Dirichlet characters modulo $q$. This identity isolates primes in a given congruence class: summing the von Mangoldt function $\Lambda(n)$ weighted by the indicator function for $n \equiv a \pmod{q}$ yields

$$\sum_{\substack{n \le x \\ n \equiv a \pmod{q}}} \Lambda(n) = \frac{1}{\phi(q)} \sum_{\chi \pmod{q}} \overline{\chi(a)} \sum_{n \le x} \chi(n) \Lambda(n).$$

By Perron's formula, the inner sum $\sum_{n \le x} \chi(n) \Lambda(n)$ is governed by the logarithmic derivative $-L'(s, \chi) / L(s, \chi)$, and contour integration shifts the integral to the left, picking up poles and zeros. For the trivial character $\chi_0$, the pole at $s = 1$ contributes the main term $x / \phi(q)$. For non-trivial characters, the critical condition is that $L(1, \chi) \ne 0$, which ensures no spurious main terms from non-trivial characters.

The proof that $L(1, \chi) \ne 0$ for non-trivial $\chi$ proceeds by contradiction. Suppose $L(1, \chi) = 0$ for some non-trivial character $\chi$ modulo $q$. Consider the product

$$\prod_{\chi \pmod{q}} L(s, \chi) = \prod_{p} \prod_{\chi} \frac{1}{1 - \chi(p) p^{-s}}.$$

For primes $p \nmid q$, the inner product over characters factors by orthogonality: if $p \equiv a \pmod{q}$, then $\prod_{\chi} (1 - \chi(p) p^{-s}) = (1 - p^{-s})^{\phi(q)} / (1 - p^{-s\phi(q)})$ by the relation between symmetric functions and character sums. As $s \to 1^+$, the term $(1 - p^{-s})$ behaves like $s - 1$, so the product diverges unless all $L(1, \chi) \ne 0$. The precise argument involves bounding partial products and showing that the assumption $L(1, \chi) = 0$ leads to a contradiction in the growth rate, confirming non-vanishing at $s = 1$.

With $L(1, \chi) \ne 0$ established, the contour integration yields

$$\sum_{\substack{n \le x \\ n \equiv a \pmod{q}}} \Lambda(n) = \frac{x}{\phi(q)} + o(x),$$

and partial summation converts this to $\pi(x; q, a) \sim x / (\phi(q) \log x)$, where $\pi(x; q, a) = \#\{p \le x : p \equiv a \pmod{q}\}$. This completes the proof of Dirichlet's theorem, establishing equidistribution of primes across coprime residue classes modulo $q$.

## 3. High-Performance Optimization & Failure Modes

### Efficient Computation of Multiplicative Functions

Computing multiplicative functions $f(n)$ for all $n \le N$ admits significant optimization through sieving techniques that exploit the multiplicativity constraint. The naive approach of factoring each $n$ individually requires $O(N \sqrt{N})$ operations, but a sieve-based algorithm reduces this to $O(N \log \log N)$ time by propagating values through the factorization lattice.

The algorithm initializes $f(1) = 1$ and $f(n) = 0$ for $n > 1$, then iterates over primes $p \le N$. For each prime $p$ and each multiple $m = kp$ with $k \le N/p$, if $\gcd(k, p) = 1$ (meaning $p \nmid k$), then $f(m) = f(k) f(p)$ by multiplicativity. For prime powers $p^j$ with $j \ge 2$, the function must specify $f(p^j)$ explicitly, and multiples $m = kp^j$ with $p \nmid k$ satisfy $f(m) = f(k) f(p^j)$. This propagation scheme ensures each $f(n)$ is computed exactly once through its prime factorization.

For the Euler totient function $\phi(n)$, the recurrence $\phi(p^k) = p^{k-1}(p-1)$ yields an $O(N \log \log N)$ sieve. Initialize $\phi(n) = n$ for all $n$, then for each prime $p$, update $\phi(n) \gets \phi(n) (1 - 1/p) = \phi(n) (p-1)/p$ for all multiples $n$ of $p$. This multiplication by $(p-1)/p$ corresponds to removing the $p$-component from the product formula $\phi(n) = n \prod_{p \mid n} (1 - 1/p)$. The total number of updates is $\sum_{p \le N} N/p = O(N \log \log N)$ by Mertens' theorem, achieving linear-quasilinear time complexity.

For divisor sums $\sigma_k(n) = \sum_{d \mid n} d^k$, a sieve iterates over each $d \le N$ and increments $\sigma_k(n)$ by $d^k$ for each multiple $n$ of $d$. This requires $O(N \log N)$ time, as the inner loop over multiples of $d$ executes $N/d$ times, and $\sum_{d=1}^N N/d = N H_N = O(N \log N)$. However, exploiting multiplicativity reduces this to $O(N \log \log N)$: for each prime $p$ and exponent $k$, compute $\sigma_k(p^j) = 1 + p^k + p^{2k} + \cdots + p^{jk}$ explicitly, then propagate through coprime multiples as in the general multiplicative sieve.

The Möbius function $\mu(n)$ benefits from a specialized sieve that marks square-free integers and assigns signs based on prime factor parity. Initialize $\mu(n) = 1$ and a boolean array $\text{squarefree}(n) = \text{true}$. For each prime $p \le N$, iterate over multiples $n = kp$ with $k \le N/p$. If $p \nmid k$, toggle the sign: $\mu(n) \gets -\mu(k)$. For $n = kp^2$ with $k \le N/p^2$, mark $\text{squarefree}(n) = \text{false}$ and set $\mu(n) = 0$. This approach computes $\mu(n)$ in $O(N \log \log N)$ time through additive updates to the prime factor count modulo $2$.

### Numerical Evaluation of Dirichlet Series and Euler Products

Computing values of Dirichlet series $F(s) = \sum_{n=1}^\infty f(n) n^{-s}$ for fixed $s = \sigma + it$ requires truncating the infinite sum and estimating the tail. For $\sigma > \sigma_a$, the tail satisfies

$$\left| \sum_{n > N} \frac{f(n)}{n^s} \right| \le \sum_{n > N} \frac{|f(n)|}{n^\sigma} \le \frac{C}{N^{\sigma - \sigma_a - \epsilon}}$$

for some constant $C$ depending on $f$, provided $\sigma > \sigma_a + \epsilon$. Choosing $N \approx C^{1/(\sigma - \sigma_a - \epsilon)}$ ensures the tail error is below a prescribed tolerance $\delta$.

For $s$ near the abscissa of convergence, Euler-Maclaurin summation accelerates convergence by incorporating derivative corrections:

$$\sum_{n=1}^N \frac{f(n)}{n^s} = \int_1^N \frac{f(x)}{x^s} \, dx + \frac{f(1)}{1^s} + \frac{f(N)}{2N^s} + \sum_{k=1}^K \frac{B_{2k}}{(2k)!} \left( \frac{d^{2k-1}}{dx^{2k-1}} \frac{f(x)}{x^s} \right) \bigg|_1^N + R_K,$$

where $B_{2k}$ are Bernoulli numbers and $R_K$ is the remainder. When $f$ is a smooth function, the integral and Bernoulli corrections provide exponentially fast convergence in the number of terms $K$.

Euler products $F(s) = \prod_p (1 - \chi(p) p^{-s})^{-1}$ are evaluated by truncating the product at primes $p \le P$ and estimating the tail contribution from $p > P$. The logarithmic tail satisfies

$$\log \prod_{p > P} \frac{1}{1 - \chi(p) p^{-s}} = -\sum_{p > P} \log(1 - \chi(p) p^{-s}) = \sum_{p > P} \sum_{k=1}^\infty \frac{\chi(p)^k}{k p^{ks}}.$$

For $\Re(s) > 1$, the dominant contribution comes from $k = 1$: $\sum_{p > P} \chi(p) p^{-s} \approx \log \log P - \log \log X$ for some cutoff $X$, decaying as $1 / \log P$. Including higher $k$ terms improves accuracy to $O(1/P^\sigma)$. In practice, computing $50$ to $100$ prime factors suffices for $8$ to $10$ digits of precision in the critical strip $1/2 < \Re(s) < 2$.

For the Riemann zeta function $\zeta(s)$ in the critical strip $0 < \Re(s) < 1$, the functional equation

$$\zeta(s) = 2^s \pi^{s-1} \sin\left(\frac{\pi s}{2}\right) \Gamma(1-s) \zeta(1-s)$$

relates values at $s$ to those at $1-s$, allowing evaluation in the right half-plane $\Re(s) > 1$ via the Euler product, then reflection to the left. The Riemann-Siegel formula provides a direct asymptotic expansion for $\zeta(1/2 + it)$ along the critical line, exploiting the approximate functional equation and Poisson summation to achieve $O(\sqrt{t})$ complexity per point, enabling high-precision zero computation.

### Analytic Continuation and Zero-Free Regions

Establishing zero-free regions for $\zeta(s)$ and $L(s, \chi)$ near $\Re(s) = 1$ is critical for obtaining effective bounds in the Prime Number Theorem and Dirichlet's theorem. The classical zero-free region $\Re(s) \ge 1 - c / \log(|t| + 2)$ is obtained through the inequality

$$\Re \left( 3 \log \zeta(\sigma) + 4 \log \zeta(\sigma + it) + \log \zeta(\sigma + 2it) \right) \ge 0$$

for $\sigma > 1$, derived from $3 + 4 \cos \theta + \cos 2\theta \ge 0$. As $\sigma \to 1^+$, the term $\log \zeta(\sigma)$ behaves like $\log(1/(\sigma - 1))$, dominating the others and forcing $\zeta(1 + it) \ne 0$.

Quantitative refinements use explicit estimates for $1/\zeta(s)$. The function $1/\zeta(s) = \sum_{n=1}^\infty \mu(n) n^{-s}$ converges absolutely for $\Re(s) > 1$ and satisfies $1/\zeta(\sigma) = \sigma - 1 + O(1)$ as $\sigma \to 1^+$. Bounding the sum $\sum_{n=1}^N \mu(n)$ through Möbius inversion and partial summation gives $|\sum_{n=1}^N \mu(n)| \le C N / \log N$ for some constant $C$, which translates to a zero-free region $\Re(s) \ge 1 - c / \log |t|$ for $|t| \ge 2$.

For Dirichlet $L$-functions $L(s, \chi)$ with non-trivial characters $\chi$, the logarithmic product $\prod_{\chi \pmod{q}} L(s, \chi)$ is entire and non-vanishing for $\Re(s) > 1$, since it equals a product over primes $p \nmid q$ of factors $\prod_{\chi} (1 - \chi(p) p^{-s})^{-1}$, which are bounded and non-zero. The vanishing of any single $L(s, \chi)$ on the line $\Re(s) = 1$ would contradict the non-vanishing of the full product as $s \to 1^+$, since the trivial character contributes a pole. This indirect argument, formalized through careful asymptotic estimates, establishes $L(1, \chi) \ne 0$ for all non-trivial $\chi$.

### Error Terms and Effective Bounds in Prime Number Theorems

The error term in the Prime Number Theorem $\pi(x) = \text{Li}(x) + E(x)$ is intimately connected to the zero distribution of $\zeta(s)$. The explicit formula

$$\psi(x) = x - \sum_{\rho} \frac{x^\rho}{\rho} - \log 2\pi - \frac{1}{2} \log(1 - x^{-2})$$

sums over non-trivial zeros $\rho = \beta + i\gamma$ of $\zeta(s)$ in the critical strip, with the main term $x$ from the pole at $s = 1$. The Riemann Hypothesis, asserting that all $\rho$ satisfy $\beta = 1/2$, implies $E(x) = O(\sqrt{x} \log^2 x)$. Unconditionally, the zero-free region $\beta \le 1 - c / \log \gamma$ yields $E(x) = O(x \exp(-c' \sqrt{\log x}))$ for some constants $c, c' > 0$.

Effective bounds for small $x$ require computing initial zeros of $\zeta(s)$ and summing their contributions explicitly. The first zero occurs at $\rho_1 \approx 1/2 + 14.134725i$, and the first $10^{13}$ zeros have been verified to lie on the critical line $\Re(s) = 1/2$. For $x \le 10^{19}$, explicit formulas incorporating these zeros provide $\pi(x)$ with rigorous error bounds below $\sqrt{x} \log x$, sufficient for computational number theory applications such as primality testing and factorization algorithm analysis.

For Dirichlet's theorem, the error term in $\pi(x; q, a)$ depends on the zeros of $L(s, \chi)$ for all characters $\chi$ modulo $q$. The Generalized Riemann Hypothesis (GRH) posits that all non-trivial zeros of $L(s, \chi)$ lie on $\Re(s) = 1/2$, implying $\pi(x; q, a) = \text{Li}(x) / \phi(q) + O(\sqrt{x} \log(qx))$. Under GRH, the least prime $p \equiv a \pmod{q}$ satisfies $p \le O((\phi(q) \log q)^2)$, a bound critical for algorithmic applications in cryptography and computational algebra.

### Failure Modes in Numerical Arithmetic Function Evaluation

Overflow in integer arithmetic occurs when computing products of multiplicative functions over large prime powers. For $\sigma_k(n)$ with large $k$ and $n$ having large prime factors, the sum $\sum_{d \mid n} d^k$ may exceed $2^{64}$ even for moderate $n \le 10^9$. Switching to floating-point arithmetic introduces rounding errors that accumulate multiplicatively through the sieve propagation. Arbitrary-precision integer arithmetic (e.g., GMP) avoids overflow but incurs significant computational overhead, increasing sieve runtime by a factor of $5$ to $10$.

Cancellation errors plague the computation of $\sum_{n \le x} \mu(n)$, as the Möbius function alternates in sign and the partial sums exhibit erratic oscillation with magnitude $O(\sqrt{x})$. Summing $N$ terms using floating-point arithmetic accumulates rounding errors proportional to $\sqrt{N} \epsilon_{\text{mach}}$, where $\epsilon_{\text{mach}} \approx 10^{-16}$ for double precision. For $N = 10^{12}$, the accumulated error reaches $10^{-10}$, overwhelming the signal when the true sum is $O(10^6)$. Kahan summation or compensated summation algorithms reduce this to $O(\epsilon_{\text{mach}})$, preserving accuracy.

Convergence failure in Dirichlet series evaluation arises when $\Re(s)$ approaches the abscissa of convergence $\sigma_a$. For $s$ slightly above $\sigma_a$, the tail $\sum_{n > N} f(n) n^{-s}$ decays slowly, requiring astronomically large $N$ for fixed precision. Analytic continuation via the functional equation or integral representations bypasses this issue but introduces complexity in implementation. For $\zeta(s)$ near $s = 1$, the pole dominates numerical evaluation: computing $\zeta(1 + 10^{-6})$ directly from the series requires summing $10^6$ terms, whereas the Laurent expansion $\zeta(s) = 1/(s-1) + \gamma + O(s-1)$ (where $\gamma$ is the Euler-Mascheroni constant) provides the value immediately.

Character orthogonality computations for Dirichlet $L$-functions require evaluating $\chi(n)$ for all characters $\chi$ modulo $q$ and summing weighted contributions. When $q$ has large prime factors, the character group $(\mathbb{Z}/q\mathbb{Z})^\times$ has large order $\phi(q)$, necessitating discrete logarithm computation modulo $q$ to represent $\chi$ via primitive roots. For $q \approx 10^6$, this involves computing $10^5$ character values per residue class, totaling $10^{11}$ operations for a full sieve. Caching character tables and exploiting multiplicativity of characters reduces this to $O(q \phi(q) \log \log q)$ through a character sieve analogous to the multiplicative function sieve.
