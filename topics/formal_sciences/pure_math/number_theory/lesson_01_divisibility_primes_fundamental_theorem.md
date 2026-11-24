# Lesson 1: Divisibility, Primes, the Fundamental Theorem of Arithmetic

## 1. First-Principles Intuition & Invariants

Number theory stands as the queen of mathematics not through royal decree but through the relentless structural elegance of its fundamental objects: the integers. Unlike the continuum of real analysis or the abstract scaffolding of category theory, number theory derives its power from discrete, atomic units—the integers themselves—and the multiplicative relationships that bind them. At the foundation of this edifice lies a deceptively simple question: given two integers $a$ and $b$ with $b \neq 0$, can we divide $a$ by $b$ to yield another integer? This question of divisibility, far from being a relic of elementary arithmetic, encodes deep structural invariants that permeate cryptography, computational complexity, algebraic geometry, and the very foundations of mathematical logic.

We begin with the notion of divisibility as a binary relation on the integers. For integers $a$ and $b$ with $b \neq 0$, we say that $b$ divides $a$, written $b \mid a$, if there exists an integer $q$ such that $a = bq$. This relation is reflexive ($a \mid a$ for all $a \neq 0$), transitive (if $a \mid b$ and $b \mid c$, then $a \mid c$), but critically not symmetric—divisibility imposes a partial ordering on the integers that captures multiplicative hierarchy. The integers divisible by $b$ form an ideal $b\mathbb{Z}$ in the ring $\mathbb{Z}$, and this ideal-theoretic perspective will later generalize to arbitrary commutative rings, but for now we anchor ourselves in the computational concreteness of integer division.

The first structural theorem we require is the Division Algorithm, which asserts that division with remainder is always possible and unique. Given integers $a$ and $b$ with $b > 0$, there exist unique integers $q$ (the quotient) and $r$ (the remainder) such that $a = bq + r$ with $0 \le r < b$. This is not an algorithm in the computational sense but rather an existence and uniqueness theorem that guarantees well-defined division with remainder. The proof of existence relies on the Well-Ordering Principle: the set $S = \{a - bk : k \in \mathbb{Z}, \, a - bk \ge 0\}$ is a nonempty subset of the nonnegative integers, hence contains a least element $r = a - bq$ for some $q$. If $r \ge b$, then $r - b = a - b(q+1) \in S$ contradicts the minimality of $r$, so $0 \le r < b$. Uniqueness follows immediately: if $a = bq + r = bq' + r'$ with $0 \le r, r' < b$, then $b(q - q') = r' - r$ with $|r' - r| < b$, forcing $q = q'$ and $r = r'$.

The Division Algorithm converts the abstract divisibility relation into a computational procedure: to test whether $b \mid a$, compute the remainder $r$ when dividing $a$ by $b$; then $b \mid a$ if and only if $r = 0$. This algorithmic character extends to the Euclidean Algorithm, which computes the greatest common divisor (gcd) of two integers through iterated application of the Division Algorithm. For integers $a$ and $b$ with $b \neq 0$, the gcd is defined as $\gcd(a, b) = \max\{d \in \mathbb{Z}^+ : d \mid a \text{ and } d \mid b\}$. The Euclidean Algorithm proceeds by repeatedly replacing the pair $(a, b)$ with $(b, r)$ where $r$ is the remainder of $a$ divided by $b$:

$$
\begin{aligned}
a &= bq_1 + r_1, \quad 0 \le r_1 < b, \\
b &= r_1 q_2 + r_2, \quad 0 \le r_2 < r_1, \\
r_1 &= r_2 q_3 + r_3, \quad 0 \le r_3 < r_2, \\
&\vdots \\
r_{n-2} &= r_{n-1} q_n + r_n, \quad 0 \le r_n < r_{n-1}, \\
r_{n-1} &= r_n q_{n+1} + 0.
\end{aligned}
$$

The sequence of remainders $b > r_1 > r_2 > \cdots > r_n > 0$ is strictly decreasing and bounded below by zero, hence terminates in finitely many steps by the Well-Ordering Principle. We claim that $\gcd(a, b) = r_n$, the last nonzero remainder. To prove this, observe that any common divisor of $a$ and $b$ divides $r_1 = a - bq_1$, and by induction any common divisor of $r_{k-1}$ and $r_k$ divides $r_{k+1} = r_{k-1} - r_k q_{k+1}$, hence any common divisor of $a$ and $b$ divides $r_n$. Conversely, $r_n \mid r_{n-1}$ by the final equation, and by backward induction $r_n$ divides each $r_k$ and ultimately both $b$ and $a$, so $r_n$ is a common divisor of $a$ and $b$. Since $r_n$ is divisible by every common divisor and is itself a common divisor, $r_n = \gcd(a, b)$.

The Euclidean Algorithm yields far more than just the gcd; by unwinding the recursive divisions, we obtain Bézout's Identity, which asserts that $\gcd(a, b)$ can be expressed as an integer linear combination of $a$ and $b$. Specifically, there exist integers $x$ and $y$ such that $\gcd(a, b) = ax + by$. To construct $x$ and $y$, we run the Euclidean Algorithm forward to obtain the sequence of remainders, then work backward substituting each remainder in terms of the previous two. For example, if $a = 252$ and $b = 105$, we compute:

$$
\begin{aligned}
252 &= 105 \cdot 2 + 42, \\
105 &= 42 \cdot 2 + 21, \\
42 &= 21 \cdot 2 + 0,
\end{aligned}
$$

so $\gcd(252, 105) = 21$. Working backward, $21 = 105 - 42 \cdot 2 = 105 - (252 - 105 \cdot 2) \cdot 2 = 105 - 252 \cdot 2 + 105 \cdot 4 = 252 \cdot (-2) + 105 \cdot 5$, yielding $x = -2$ and $y = 5$. This algorithmic procedure generalizes to arbitrary pairs and can be implemented via the Extended Euclidean Algorithm, which tracks the coefficients $(x_k, y_k)$ satisfying $r_k = ax_k + by_k$ at each stage through the recurrence $(x_{k+1}, y_{k+1}) = (x_{k-1} - q_k x_k, y_{k-1} - q_k y_k)$.

Bézout's Identity has profound structural consequences. It immediately implies that $\gcd(a, b)$ is the smallest positive integer that can be expressed as $ax + by$ for integers $x$ and $y$. Indeed, the set $\{ax + by : x, y \in \mathbb{Z}\}$ is precisely the ideal generated by $a$ and $b$ in $\mathbb{Z}$, and since $\mathbb{Z}$ is a principal ideal domain (PID), this ideal equals $d\mathbb{Z}$ for some $d \ge 0$. But $d$ divides both $a$ and $b$ (since $a, b \in d\mathbb{Z}$), and any common divisor of $a$ and $b$ divides $d$ (since $d = ax + by$ for some $x, y$), so $d = \gcd(a, b)$. This characterization of the gcd as the generator of an ideal extends the computational perspective of the Euclidean Algorithm to the abstract algebraic perspective of ideal theory, foreshadowing the generalization of unique factorization to Dedekind domains in algebraic number theory.

A critical application of Bézout's Identity is the proof that if $\gcd(a, b) = 1$ and $a \mid bc$, then $a \mid c$. This Euclid's Lemma is the linchpin of unique factorization. To prove it, write $1 = ax + by$ for some integers $x$ and $y$ by Bézout, then multiply by $c$ to obtain $c = acx + bcy$. Since $a \mid ac$ trivially and $a \mid bc$ by hypothesis, we have $a \mid (acx + bcy) = c$, as desired. This lemma captures the intuition that coprime divisors act independently: if $a$ and $b$ share no common factors and $a$ divides a multiple of $b$, then $a$ must divide the other factor.

We now turn to the structure of prime numbers, the atomic building blocks of multiplicative number theory. An integer $p > 1$ is called prime if its only positive divisors are $1$ and $p$. Equivalently, $p$ is prime if whenever $p \mid ab$, either $p \mid a$ or $p \mid b$—this is the defining property of a prime element in a general integral domain. To prove the equivalence, suppose $p$ is prime and $p \mid ab$. If $p \nmid a$, then $\gcd(p, a) = 1$ (since the only divisors of $p$ are $1$ and $p$), so by Euclid's Lemma $p \mid b$. Conversely, suppose $p$ has the division property and $d \mid p$ with $d > 0$. Write $p = de$ for some $e > 0$. Then $p \mid de$, so $p \mid d$ or $p \mid e$. If $p \mid d$, then $d \ge p$, forcing $d = p$. If $p \mid e$, then $e \ge p$, forcing $e = p$ and $d = 1$. Thus $p$ is prime.

The infinitude of primes is one of the oldest and most elegant results in mathematics, first proved by Euclid around 300 BCE. The proof is a paradigm of indirect reasoning: suppose there are only finitely many primes $p_1, p_2, \ldots, p_k$, and consider the integer $N = p_1 p_2 \cdots p_k + 1$. For any prime $p_i$, we have $N = p_i(p_1 \cdots p_{i-1} p_{i+1} \cdots p_k) + 1$, so dividing $N$ by $p_i$ leaves remainder $1$, hence $p_i \nmid N$. But $N > 1$, so $N$ has a prime divisor $p$ by the fundamental fact that every integer greater than $1$ is divisible by some prime (which we will prove shortly as a corollary of the Fundamental Theorem of Arithmetic). This prime $p$ cannot be any of $p_1, \ldots, p_k$, contradicting the assumption that the list was exhaustive. Hence there are infinitely many primes.

Euclid's proof is nonconstructive: it establishes existence without providing an algorithm to enumerate all primes. Nevertheless, the proof technique generalizes to show the infinitude of primes in arithmetic progressions (Dirichlet's Theorem) and in polynomial rings, and it motivates the definition of the Riemann zeta function $\zeta(s) = \sum_{n=1}^\infty n^{-s}$, whose Euler product $\zeta(s) = \prod_{p \text{ prime}} (1 - p^{-s})^{-1}$ encodes the distribution of primes in the multiplicative structure of the integers.

We now arrive at the Fundamental Theorem of Arithmetic (FTA), which asserts that every integer $n > 1$ can be expressed uniquely as a product of primes, up to the order of factors. The theorem decomposes into two statements: existence (every integer factors into primes) and uniqueness (the factorization is unique). Both proofs rely on the Well-Ordering Principle, but in subtly different ways.

**Existence of Prime Factorization.** We prove by strong induction on $n$ that every integer $n \ge 2$ is either prime or a product of primes. The base case $n = 2$ is immediate since $2$ is prime. For the inductive step, assume the statement holds for all integers $k$ with $2 \le k < n$, and consider $n$. If $n$ is prime, we are done. Otherwise, $n$ is composite, so $n = ab$ for some integers $a, b$ with $1 < a, b < n$. By the inductive hypothesis, both $a$ and $b$ factor into primes, say $a = p_1 \cdots p_r$ and $b = q_1 \cdots q_s$. Then $n = p_1 \cdots p_r q_1 \cdots q_s$ is a product of primes, completing the induction.

An alternative proof uses the Well-Ordering Principle directly. Suppose, for contradiction, that the set $S$ of integers greater than $1$ that do not factor into primes is nonempty. By Well-Ordering, $S$ contains a least element $n$. Since $n$ does not factor into primes, $n$ is not prime, so $n = ab$ for some $1 < a, b < n$. But then $a, b \notin S$ by minimality of $n$, so both $a$ and $b$ factor into primes, hence so does $n = ab$, a contradiction. Therefore $S = \emptyset$, and every integer greater than $1$ factors into primes.

**Uniqueness of Prime Factorization.** Suppose $n$ has two prime factorizations $n = p_1 p_2 \cdots p_r = q_1 q_2 \cdots q_s$, where each $p_i$ and $q_j$ is prime. We must show that $r = s$ and, after reordering, $p_i = q_i$ for all $i$. The proof proceeds by induction on $\min(r, s)$. If $r = 1$, then $n = p_1$ is prime, so $s = 1$ and $p_1 = q_1$. For the inductive step, assume uniqueness holds for all integers with fewer than $r$ prime factors in the smaller factorization. Since $p_1 \mid q_1 \cdots q_s$, Euclid's Lemma implies $p_1 \mid q_j$ for some $j$. Reordering if necessary, assume $p_1 \mid q_1$. Since $q_1$ is prime and $p_1 > 1$, we have $p_1 = q_1$. Canceling $p_1$ from both sides, $p_2 \cdots p_r = q_2 \cdots q_s$. By the inductive hypothesis (applied to the integer $n / p_1$, which has $r - 1$ factors on the left), $r - 1 = s - 1$ and the remaining factors match up to order. Hence $r = s$ and the factorizations are identical up to reordering.

The crux of the uniqueness proof is Euclid's Lemma, which itself relies on Bézout's Identity and the Euclidean Algorithm. This chain of dependencies—Well-Ordering $\Rightarrow$ Division Algorithm $\Rightarrow$ Euclidean Algorithm $\Rightarrow$ Bézout $\Rightarrow$ Euclid's Lemma $\Rightarrow$ Unique Factorization—illustrates the hierarchical structure of number theory, where each theorem builds inexorably on the foundational properties of the integers.

The Fundamental Theorem of Arithmetic justifies the canonical prime factorization representation: every integer $n > 1$ can be written uniquely in the form $n = p_1^{a_1} p_2^{a_2} \cdots p_k^{a_k}$, where $p_1 < p_2 < \cdots < p_k$ are distinct primes and $a_i \ge 1$ for all $i$. This representation encodes the multiplicative structure of $n$ in a canonical form that is invariant under isomorphisms of the multiplicative group $\mathbb{Z}_{>1}$ and generalizes to the factorization of ideals in Dedekind domains. The exponents $a_i$ are called the multiplicities or valuations of $n$ at $p_i$, and they satisfy the valuation property: $v_p(mn) = v_p(m) + v_p(n)$, where $v_p(n)$ denotes the exponent of $p$ in the prime factorization of $n$. This additive structure on the multiplicative semigroup $\mathbb{Z}_{>1}$ is the logarithmic transform that connects multiplication in $\mathbb{Z}$ to addition in $\mathbb{Z}^k$, a correspondence that underlies the Fast Fourier Transform and logarithmic representations in computational number theory.

Given the canonical factorizations $m = p_1^{a_1} \cdots p_k^{a_k}$ and $n = p_1^{b_1} \cdots p_k^{b_k}$ (where we allow $a_i = 0$ or $b_i = 0$ for primes not dividing $m$ or $n$), the gcd and least common multiple (lcm) have simple closed forms in terms of the valuations:

$$
\gcd(m, n) = p_1^{\min(a_1, b_1)} \cdots p_k^{\min(a_k, b_k)}, \quad \text{lcm}(m, n) = p_1^{\max(a_1, b_1)} \cdots p_k^{\max(a_k, b_k)}.
$$

These formulas reduce the computation of gcd and lcm to pointwise operations on exponent vectors, trading arithmetic on integers for arithmetic on tuples of nonnegative integers. The identity $\gcd(m, n) \cdot \text{lcm}(m, n) = mn$ follows immediately from $\min(a, b) + \max(a, b) = a + b$ for all nonnegative integers $a$ and $b$, and it reflects the duality between meet and join in the lattice of divisibility.

The divisibility partial order $(d \mid n)$ induces a lattice structure on the positive divisors of any integer $n$: the meet of two divisors is their gcd, and the join is their lcm. This lattice is isomorphic to the product lattice of the exponent vectors under pointwise min and max, a finite distributive lattice that generalizes to the ideal lattice of any Dedekind domain. The number of divisors of $n$, denoted $\tau(n)$ or $d(n)$, is given by $\tau(n) = (a_1 + 1)(a_2 + 1) \cdots (a_k + 1)$ from the prime factorization $n = p_1^{a_1} \cdots p_k^{a_k}$, since each divisor corresponds to choosing an exponent $0 \le e_i \le a_i$ for each prime $p_i$. Similarly, the sum of divisors function $\sigma(n) = \sum_{d \mid n} d$ factors as $\sigma(n) = \sigma(p_1^{a_1}) \cdots \sigma(p_k^{a_k})$ with $\sigma(p^a) = 1 + p + p^2 + \cdots + p^a = (p^{a+1} - 1) / (p - 1)$, a formula that connects number-theoretic functions to geometric series and generating functions.

The Fundamental Theorem of Arithmetic fails in more general rings, providing a gateway to algebraic number theory. For example, in the ring $\mathbb{Z}[\sqrt{-5}] = \{a + b\sqrt{-5} : a, b \in \mathbb{Z}\}$, the element $6$ has two distinct factorizations into irreducibles: $6 = 2 \cdot 3 = (1 + \sqrt{-5})(1 - \sqrt{-5})$. Here $2, 3, 1 + \sqrt{-5}, 1 - \sqrt{-5}$ are all irreducible (cannot be factored into products of non-units), but they are not prime (they do not satisfy Euclid's Lemma). This failure of unique factorization motivated Dedekind's introduction of ideals and the definition of Dedekind domains, where unique factorization is restored at the level of ideals: every nonzero ideal factors uniquely as a product of prime ideals. The integers $\mathbb{Z}$ are a prototypical Dedekind domain where principal ideals and prime elements coincide, making the FTA a special case of the more general ideal factorization theorem.

## 2. Core Architecture & Mechanics

The computational architecture of number-theoretic algorithms rests on efficient implementations of the Division Algorithm, Euclidean Algorithm, and Extended Euclidean Algorithm. These algorithms form the inner loop of cryptographic protocols (RSA key generation, Diffie-Hellman key exchange, elliptic curve cryptography), symbolic computation systems (polynomial gcd, rational function simplification), and computational algebra systems (Gröbner bases, lattice reduction). We dissect the data flow and complexity of these core primitives.

**Division Algorithm Implementation.** The Division Algorithm computes the quotient $q$ and remainder $r$ satisfying $a = bq + r$ with $0 \le r < b$ for given integers $a \ge 0$ and $b > 0$. A naive implementation subtracts $b$ from $a$ repeatedly until the result falls below $b$, requiring $O(a/b)$ operations—unacceptable for large $a$ and small $b$. The standard implementation uses binary long division, processing the bits of $a$ from most significant to least significant, maintaining an invariant that after processing $k$ bits, the remainder is less than $2^k b$. This yields $O(\log a)$ iterations, each performing a constant number of bit operations (shift, compare, subtract), for total complexity $O((\log a)^2)$ using schoolbook arithmetic or $O((\log a) \log(\log a))$ using fast multiplication.

In pseudocode, the bit-by-bit division algorithm for $a, b \ge 0$ with $b > 0$ proceeds as:

```text
DivMod(a, b):
  q ← 0, r ← 0
  for i from (bit-length of a - 1) down to 0:
    r ← 2r + bit_i(a)
    if r ≥ b:
      r ← r - b
      q ← q + 2^i
  return (q, r)
```

This algorithm maintains the invariant $a = bq + r$ with $0 \le r < 2b$ after each iteration, tightening to $r < b$ at the final conditional subtraction. The quotient $q$ is built up bit-by-bit, with each bit determined by whether the current doubled remainder exceeds $b$. This is precisely the mechanical process taught in elementary school, formalized into a loop invariant proof.

**Euclidean Algorithm Implementation.** The Euclidean Algorithm computes $\gcd(a, b)$ by iterating the Division Algorithm: replace $(a, b)$ with $(b, r)$ where $r = a \bmod b$, until $b = 0$. The termination and correctness proofs rely on two observations: the sequence of remainders strictly decreases, and $\gcd(a, b) = \gcd(b, r)$ for all $r = a \bmod b$. The latter follows from the fact that any common divisor of $a$ and $b$ divides $r = a - bq$, and any common divisor of $b$ and $r$ divides $a = bq + r$, so the two pairs have the same set of common divisors.

```text
GCD(a, b):
  while b ≠ 0:
    r ← a mod b
    a ← b
    b ← r
  return a
```

The complexity of the Euclidean Algorithm is determined by the number of division steps. Lamé's Theorem (1844) establishes that the number of steps is at most $5$ times the number of decimal digits of the smaller input, or more precisely $O(\log \min(a, b))$. The worst-case inputs are consecutive Fibonacci numbers: $\gcd(F_{n+1}, F_n)$ requires exactly $n-1$ division steps. To prove this, observe that the Fibonacci recurrence $F_{n+1} = F_n + F_{n-1}$ is precisely the Division Algorithm with quotient $1$ and remainder $F_{n-1}$, so the Euclidean Algorithm on $(F_{n+1}, F_n)$ unwinds the Fibonacci sequence one step at a time. Since $F_n \approx \phi^n / \sqrt{5}$ where $\phi = (1 + \sqrt{5})/2$ is the golden ratio, the number of steps is $\Theta(\log a)$, where $a = \min(a, b)$.

Combining the $O(\log b)$ iterations with the $O((\log a)^2)$ cost per division (where $a$ is the current dividend), the total complexity of the Euclidean Algorithm is $O((\log \max(a, b))^3)$ using schoolbook arithmetic, or $O((\log \max(a, b))^2 \log \log \max(a, b))$ using fast multiplication. For cryptographic integers with thousands of bits, these complexity bounds are critical: the difference between $O(n^3)$ and $O(n^2 \log n)$ is the difference between milliseconds and seconds.

**Extended Euclidean Algorithm.** The Extended Euclidean Algorithm (XGCD) augments the Euclidean Algorithm to compute Bézout coefficients $x, y$ satisfying $\gcd(a, b) = ax + by$ alongside the gcd itself. The algorithm maintains the invariant that at each stage, the current remainders $r_i$ and $r_{i-1}$ can be expressed as $r_i = ax_i + by_i$ and $r_{i-1} = ax_{i-1} + by_{i-1}$ for some integers $x_i, y_i, x_{i-1}, y_{i-1}$. The recurrence $r_{i+1} = r_{i-1} - q_i r_i$ (from the Division Algorithm) translates to $(x_{i+1}, y_{i+1}) = (x_{i-1} - q_i x_i, y_{i-1} - q_i y_i)$.

```text
ExtendedGCD(a, b):
  (old_r, r) ← (a, b)
  (old_x, x) ← (1, 0)
  (old_y, y) ← (0, 1)
  
  while r ≠ 0:
    q ← old_r div r
    (old_r, r) ← (r, old_r - q·r)
    (old_x, x) ← (x, old_x - q·x)
    (old_y, y) ← (y, old_y - q·y)
  
  return (old_r, old_x, old_y)  // gcd, x, y with gcd = a·x + b·y
```

The Extended Euclidean Algorithm has the same asymptotic complexity as the standard Euclidean Algorithm—the coefficient updates add only $O(1)$ arithmetic operations per iteration—but the coefficients $x$ and $y$ can grow exponentially in magnitude, up to $O(a)$ and $O(b)$ respectively. In practice, the Bézout coefficients are needed primarily for computing modular inverses: if $\gcd(a, n) = 1$, then $ax \equiv 1 \pmod{n}$ where $x$ is the Bézout coefficient from $1 = ax + ny$, reducing $x$ modulo $n$ to ensure $0 \le x < n$. This operation is the core of RSA decryption and signature verification, where the private exponent $d$ satisfies $ed \equiv 1 \pmod{\phi(n)}$.

**Prime Factorization Algorithms.** While the Fundamental Theorem of Arithmetic guarantees the existence and uniqueness of prime factorizations, it provides no efficient algorithm to compute them. Trial division, the simplest factorization method, tests divisibility by all primes up to $\sqrt{n}$, requiring $O(\sqrt{n} / \log n)$ primality tests by the Prime Number Theorem (the number of primes up to $x$ is approximately $x / \log x$). For $n \approx 2^{2048}$ (a typical RSA modulus), trial division requires roughly $2^{1024} / (1024 \ln 2) \approx 2^{1024} / 710 \approx 10^{305}$ operations—cosmologically infeasible.

Modern factorization algorithms exploit algebraic structure to achieve subexponential complexity. The Quadratic Sieve and Number Field Sieve factor $n$ in time $L_n[1/2, c]$ and $L_n[1/3, c]$ respectively, where $L_n[\alpha, c] = \exp((c + o(1))(\log n)^\alpha (\log \log n)^{1-\alpha})$. These algorithms construct congruences of squares $x^2 \equiv y^2 \pmod{n}$ with $x \not\equiv \pm y \pmod{n}$, which yield nontrivial factors $\gcd(x - y, n)$ via the identity $(x-y)(x+y) \equiv 0 \pmod{n}$. The security of RSA relies on the presumed hardness of factoring: no polynomial-time classical algorithm is known, though Shor's quantum algorithm factors in polynomial time $O((\log n)^3)$ on a quantum computer.

For small integers and pedagogical purposes, the Sieve of Eratosthenes generates all primes up to $n$ in $O(n \log \log n)$ time by iteratively marking multiples of each prime:

```text
SieveOfEratosthenes(n):
  is_prime ← array of True, indexed from 2 to n
  for p from 2 to √n:
    if is_prime[p]:
      for k from p² to n step p:
        is_prime[k] ← False
  return [p for p in 2..n if is_prime[p]]
```

The sieve's efficiency stems from starting each inner loop at $p^2$ (since all smaller multiples of $p$ have been marked by smaller primes) and marking only odd multiples when $p > 2$. The sieve is parallelizable and cache-friendly, making it practical for generating primes up to $10^9$ or beyond on modern hardware.

**Canonical Factorization and Arithmetic Functions.** Given an integer $n$ with canonical factorization $n = p_1^{a_1} \cdots p_k^{a_k}$, we can compute arithmetic functions multiplicatively. A function $f : \mathbb{Z}_{>0} \to \mathbb{C}$ is called multiplicative if $f(mn) = f(m)f(n)$ whenever $\gcd(m, n) = 1$, and completely multiplicative if $f(mn) = f(m)f(n)$ for all $m, n$. For multiplicative $f$, the value at $n$ factors as $f(n) = f(p_1^{a_1}) \cdots f(p_k^{a_k})$, reducing the computation to prime powers. Examples include:

- The Euler totient function $\phi(n) = \#\{1 \le k \le n : \gcd(k, n) = 1\}$ counts integers coprime to $n$. For prime powers, $\phi(p^a) = p^a - p^{a-1} = p^{a-1}(p-1)$, since exactly $p^{a-1}$ multiples of $p$ exist in $\{1, \ldots, p^a\}$. By multiplicativity, $\phi(n) = n \prod_{p \mid n} (1 - 1/p)$.

- The Möbius function $\mu(n)$ equals $(-1)^k$ if $n$ is a product of $k$ distinct primes, and $0$ if $n$ is divisible by a perfect square. This function inverts Dirichlet convolution: $\sum_{d \mid n} \mu(d) = [n = 1]$, where $[P]$ is $1$ if $P$ is true and $0$ otherwise.

- The divisor sum $\sigma_k(n) = \sum_{d \mid n} d^k$ generalizes to $\sigma_k(n) = \prod_{p^a \| n} (1 + p^k + p^{2k} + \cdots + p^{ak}) = \prod_{p^a \| n} (p^{(a+1)k} - 1) / (p^k - 1)$.

These functions satisfy Dirichlet convolution identities that form the foundation of analytic number theory, connecting elementary arithmetic to complex analysis via Dirichlet series $\sum_{n=1}^\infty f(n) n^{-s}$ and Euler products $\prod_p (1 - f(p) p^{-s})^{-1}$.

The data structure for canonical factorization is a sparse representation: a list of (prime, exponent) pairs sorted by increasing prime. Operations on factored integers reduce to merging sorted lists (for multiplication), pointwise operations on exponent vectors (for gcd and lcm), and dictionary lookups (for divisibility testing). This representation is efficient for integers with few distinct prime factors but degenerates for highly composite numbers like factorials, where dense representations or logarithmic transforms are preferable.

## 3. High-Performance Optimization & Failure Modes

The practical deployment of number-theoretic algorithms in computational algebra systems, cryptographic libraries, and competitive programming requires careful attention to performance optimization, numerical stability, and edge-case handling. We examine the bottlenecks and failure modes that arise when theory meets silicon.

**Modular Arithmetic and Montgomery Reduction.** Cryptographic protocols perform millions of modular exponentiations $a^e \bmod n$, each decomposing into $O(\log e)$ modular multiplications $(ab \bmod n)$. Naive modular reduction via the Division Algorithm costs $O((\log n)^2)$ per multiplication, dominating the runtime. Montgomery reduction replaces division by $n$ with division by a power of two $R = 2^k > n$, exploiting the efficiency of bitwise operations. The Montgomery representation of $a$ is $\bar{a} = aR \bmod n$, and Montgomery multiplication computes $\overline{ab} = \bar{a} \bar{b} R^{-1} \bmod n$ without explicit division by $n$:

```text
MontgomeryReduce(T, n, n', R):
  // Inputs: T < Rn, n < R, n' = -n^(-1) mod R
  m ← ((T mod R) · n') mod R
  t ← (T + mn) / R
  if t ≥ n:
    return t - n
  else:
    return t
```

The division $(T + mn) / R$ is exact (since $T + mn \equiv T \pmod{R}$ and $mn \equiv 0 \pmod{R}$) and reduces to a right shift when $R = 2^k$. The precomputed constant $n' = -n^{-1} \bmod R$ (obtained via Extended Euclidean Algorithm) ensures $T + mn \equiv 0 \pmod{R}$. Montgomery multiplication reduces the cost of modular reduction from $O((\log n)^2)$ to $O(\log n)$, a factor-of-$(\log n)$ speedup that is decisive for multi-thousand-bit RSA moduli.

The price of Montgomery reduction is a change of representation: inputs and outputs live in the Montgomery domain $\bar{a} = aR \bmod n$, requiring domain conversions via $\bar{a} = aR \bmod n$ (one modular multiplication by $R^2 \bmod n$) and $a = \bar{a} R^{-1} \bmod n$ (one Montgomery reduction). For chains of operations (modular exponentiation, elliptic curve scalar multiplication), the conversion cost is amortized over many Montgomery multiplications, yielding substantial net speedup. Failure to convert correctly between domains is a common bug, producing outputs that are off by a factor of $R^k \bmod n$ for some $k$.

**GCD Computation in Euclidean Domains.** The Euclidean Algorithm generalizes to any Euclidean domain—a ring $R$ equipped with a norm function $N : R \setminus \{0\} \to \mathbb{Z}_{\ge 0}$ such that for all $a, b \in R$ with $b \neq 0$, there exist $q, r \in R$ with $a = bq + r$ and either $r = 0$ or $N(r) < N(b)$. Examples include polynomial rings $k[x]$ over a field $k$ (with $N(f) = \deg f$) and Gaussian integers $\mathbb{Z}[i]$ (with $N(a + bi) = a^2 + b^2$). The Euclidean Algorithm in $k[x]$ computes polynomial gcd via repeated polynomial long division, terminating when the remainder is zero. The Extended Euclidean Algorithm yields Bézout coefficients that solve the Bézout identity $\gcd(f, g) = s f + t g$ for polynomials $s, t \in k[x]$, enabling rational function partial fraction decomposition and Chinese Remainder Theorem applications.

In $\mathbb{Z}[i]$, the Euclidean Algorithm computes gcd of Gaussian integers via division with remainder in the complex plane: given $\alpha, \beta \in \mathbb{Z}[i]$, the quotient $q$ is chosen as the Gaussian integer nearest to $\alpha / \beta$ in $\mathbb{C}$, ensuring $N(\alpha - \beta q) < N(\beta)$. This geometric interpretation of the Division Algorithm extends to imaginary quadratic fields $\mathbb{Q}(\sqrt{-d})$ for small $d$, though not all such fields are Euclidean (e.g., $\mathbb{Z}[\sqrt{-5}]$ is not a Euclidean domain, as evidenced by the failure of unique factorization).

**Failure Modes: Overflow, Sign Handling, and Coprimality.** Number-theoretic algorithms are rife with edge cases and overflow vulnerabilities. The Extended Euclidean Algorithm computes Bézout coefficients $x, y$ satisfying $\gcd(a, b) = ax + by$, but the intermediate values of $x$ and $y$ can grow to $O(a)$ and $O(b)$ respectively—far exceeding the magnitudes of $a$ and $b$. For 64-bit inputs, intermediate values may require 128-bit integers to avoid overflow. Signed integer overflow is undefined behavior in C/C++, causing silent wraparound or trapping, while unsigned overflow wraps modulo $2^{64}$, potentially producing incorrect results. Defensive implementations use checked arithmetic or arbitrary-precision integers (GMP, Python's `int`) to guarantee correctness.

Sign handling in the Euclidean Algorithm requires care when $a$ or $b$ is negative. The mathematical definition $\gcd(a, b) = \gcd(|a|, |b|)$ ensures the gcd is always nonnegative, but the Division Algorithm $a = bq + r$ with $0 \le r < |b|$ requires adjusting the quotient and remainder when $b < 0$. Many implementations define $a \bmod b$ to have the same sign as $b$ (Python's `%`) or the same sign as $a$ (C's `%` for C99 onwards), leading to subtle discrepancies. A robust Euclidean Algorithm normalizes inputs to positive values or carefully handles signs in the loop invariant.

Coprimality testing via $\gcd(a, b) = 1$ is efficient ($O((\log \min(a, b))^2)$ or better), but probabilistic compositeness tests (Miller-Rabin, Baillie-PSW) offer faster primality testing for large integers. The Miller-Rabin test runs in $O(k (\log n)^3)$ time for $k$ rounds and has error probability at most $4^{-k}$, making it suitable for cryptographic applications where deterministic primality is not required. Carmichael numbers (composite integers that satisfy Fermat's test $a^{n-1} \equiv 1 \pmod{n}$ for all $a$ coprime to $n$) defeat naive Fermat testing, but Miller-Rabin detects them with high probability.

**Batch GCD and the Subproduct Tree.** Computing $\gcd(n, m_i)$ for many $m_i$ arises in factorization algorithms (testing divisibility by many primes), vulnerability scanning (searching for common factors in RSA moduli), and redundancy elimination. A naive loop computes $k$ independent gcds in $O(k (\log n)^2)$ time. The batch gcd algorithm uses a subproduct tree to reduce the complexity to $O(k (\log n) (\log k)^2)$ via fast polynomial evaluation techniques.

The subproduct tree is a binary tree where each leaf is an input $m_i$ and each internal node is the product of its children. Building the tree requires $O(k (\log n) \log k)$ time using divide-and-conquer multiplication. The gcd $\gcd(n, m_1 m_2 \cdots m_k)$ is computed at the root, then propagated down: at each node with product $P$ and gcd $g = \gcd(n, P)$, the gcd at the left child with product $P_L$ is $\gcd(g, P_L)$, and similarly for the right child. The total time is $O(k (\log n) (\log k)^2)$, a logarithmic factor improvement over the naive approach. This technique is implemented in Sage's `gcd` for lists and in specialized factorization tools like `cado-nfs`.

**Parallel and Distributed Factorization.** Large-scale factorization (RSA Factoring Challenge, cryptanalysis of weak keys) employs distributed computation across thousands of cores. The Number Field Sieve distributes the relation collection phase (sieving for smooth values) across many machines, each processing a disjoint interval of the sieving space. The linear algebra phase (finding a null vector in a sparse matrix over $\mathbb{F}_2$) uses parallelized Lanczos or Wiedemann algorithms, which scale to matrices with billions of rows and columns. Communication overhead is minimized by partitioning the sieving space spatially and batching matrix-vector products.

Modern factorization libraries (GMP-ECM, CADO-NFS, msieve) incorporate decades of algorithmic refinements: stage-2 ECM with improved baby-step giant-step tables, special-purpose sieving for polynomials with small coefficients, GPU-accelerated trial division, and just-in-time compilation of sieving kernels. Performance tuning requires profiling to identify bottlenecks: L1/L2 cache misses in sieve array access, branch mispredictions in inner loops, and memory bandwidth saturation in sparse matrix operations. The interplay between algorithmic complexity and hardware microarchitecture determines the wall-clock runtime—theoretical $O(n^2)$ algorithms can outperform theoretical $O(n \log n)$ algorithms for small $n$ due to cache locality and vectorization.

**Edge Cases and Defensive Programming.** Robust implementations handle corner cases explicitly: $\gcd(0, b) = |b|$ and $\gcd(a, 0) = |a|$ by definition, avoiding division by zero in the Euclidean Algorithm. The lcm of zero and any integer is zero, $\text{lcm}(0, b) = 0$, though the formula $\text{lcm}(a, b) = ab / \gcd(a, b)$ appears to fail via division by zero when $a = 0$—the correct interpretation treats $\text{lcm}$ as the dual of $\gcd$ in the lattice of divisibility, with zero as the top element. Extended Euclidean Algorithm implementations verify the output via $\gcd(a, b) = ax + by$, catching sign errors and overflow.

Unit testing of number-theoretic code requires adversarial inputs: consecutive Fibonacci numbers (worst-case GCD), Carmichael numbers (defeating Fermat tests), and large primes near $2^k$ boundaries (exposing overflow). Property-based testing (Hypothesis, QuickCheck) generates random inputs and verifies invariants: $\gcd(a, b) \mid a$, $\gcd(a, b) \mid b$, $\gcd(a, b) = ax + by$ for some $x, y$, and $\text{lcm}(a, b) = ab / \gcd(a, b)$ (avoiding overflow by computing $a / \gcd(a, b)$ first). Differential testing compares implementations against a reference (GMP, Mathematica, SageMath), catching discrepancies in sign conventions, tie-breaking rules, and undefined behavior.

The synthesis of theoretical elegance and computational pragmatism defines modern number theory. The Fundamental Theorem of Arithmetic, a theorem so foundational it is often introduced in elementary school, underpins the $2$ trillion-dollar internet economy through its application to RSA cryptography, elliptic curve cryptography, and lattice-based post-quantum schemes. The Euclidean Algorithm, a procedure known to Euclid in 300 BCE, powers every TLS handshake, every Bitcoin transaction, and every secure message on Signal. The interplay between divisibility, primes, and unique factorization is not merely an abstract curiosity but the bedrock of secure communication, verifiable computation, and the digital trust infrastructure of the twenty-first century. Mastery of these foundational concepts is prerequisite to advanced work in algebraic number theory, arithmetic geometry, cryptanalysis, and computational complexity—domains where the integers reveal their inexhaustible depth and the prime numbers continue to guard their secrets against the relentless ingenuity of mathematicians and computer scientists.
