# Lesson 3: Fermat's Little Theorem, Euler's Totient, Primitive Roots

## 1. First-Principles Intuition & Invariants

The multiplicative structure of the integers modulo $n$ forms the bedrock of modern cryptography, pseudorandom number generation, and primality testing. Unlike the additive group $(\mathbb{Z}/n\mathbb{Z}, +)$, which always possesses the full cyclic structure of order $n$, the multiplicative group $(\mathbb{Z}/n\mathbb{Z})^*$ consisting of residue classes coprime to $n$ exhibits rich, modulus-dependent behavior. When $n = p$ is prime, this group becomes cyclic of order $p - 1$, admitting primitive roots that generate the entire multiplicative structure through repeated exponentiation. For composite moduli, the group decomposes into a product of cyclic components whose orders are governed by the prime factorization of $n$.

Euler's totient function $\varphi(n)$ counts the number of integers in $\{1, 2, \ldots, n\}$ that are coprime to $n$, thereby measuring the cardinality of the multiplicative group $(\mathbb{Z}/n\mathbb{Z})^*$. The multiplicativity of $\varphi$ flows directly from the Chinese Remainder Theorem: when $\gcd(m, n) = 1$, the ring isomorphism $\mathbb{Z}/mn\mathbb{Z} \cong \mathbb{Z}/m\mathbb{Z} \times \mathbb{Z}/n\mathbb{Z}$ preserves the coprimality structure, yielding $\varphi(mn) = \varphi(m) \varphi(n)$. This multiplicativity permits efficient computation via the prime factorization formula: for $n = p_1^{e_1} p_2^{e_2} \cdots p_k^{e_k}$, we have

$$\varphi(n) = n \prod_{p \mid n} \left(1 - \frac{1}{p}\right) = p_1^{e_1 - 1}(p_1 - 1) \cdot p_2^{e_2 - 1}(p_2 - 1) \cdots p_k^{e_k - 1}(p_k - 1).$$

Fermat's Little Theorem emerges as an immediate corollary of Lagrange's Theorem applied to the finite group $(\mathbb{Z}/p\mathbb{Z})^*$. Since this group has order $p - 1$ when $p$ is prime, every element $a \in (\mathbb{Z}/p\mathbb{Z})^*$ satisfies $a^{p-1} \equiv 1 \pmod{p}$. Euler generalized this result to arbitrary moduli: for any $a$ with $\gcd(a, n) = 1$, we have $a^{\varphi(n)} \equiv 1 \pmod{n}$. The smallest positive exponent $d$ such that $a^d \equiv 1 \pmod{n}$ for all $a$ coprime to $n$ is called the Carmichael function $\lambda(n)$, and it divides $\varphi(n)$. While $\varphi(n)$ measures group cardinality, $\lambda(n)$ captures the exponent of the group—the least common multiple of all element orders.

The existence of primitive roots, elements whose multiplicative order equals $\varphi(n)$, is guaranteed precisely when $n$ takes one of the forms $1, 2, 4, p^k,$ or $2p^k$ for odd prime $p$ and positive integer $k$. For prime moduli $p$, the group $(\mathbb{Z}/p\mathbb{Z})^*$ is cyclic of order $p - 1$, and the number of primitive roots is $\varphi(p - 1)$. When a primitive root $g$ exists, every element $a \in (\mathbb{Z}/n\mathbb{Z})^*$ can be expressed uniquely as $a \equiv g^x \pmod{n}$ for some $0 \le x < \varphi(n)$. The discrete logarithm problem asks to recover $x$ from $a$ and $g$, a computational task believed intractable for sufficiently large primes despite the existence of subexponential algorithms like the Number Field Sieve for discrete logarithms.

## 2. Core Architecture & Mechanics

### Euler's Totient Function: Derivation and Multiplicativity

We begin with the foundational computation of $\varphi(p^k)$ for prime power moduli. The integers in $\{1, 2, \ldots, p^k\}$ that share a common factor with $p^k$ are precisely the multiples of $p$: $\{p, 2p, 3p, \ldots, p^{k-1} \cdot p\}$. There are $p^{k-1}$ such multiples, so the count of coprime residues is

$$\varphi(p^k) = p^k - p^{k-1} = p^{k-1}(p - 1).$$

To establish multiplicativity for coprime moduli, we invoke the Chinese Remainder Theorem. Suppose $\gcd(m, n) = 1$. The ring isomorphism

$$\Phi: \mathbb{Z}/mn\mathbb{Z} \to \mathbb{Z}/m\mathbb{Z} \times \mathbb{Z}/n\mathbb{Z}, \quad \Phi(x \bmod mn) = (x \bmod m, x \bmod n)$$

restricts to a group isomorphism on units:

$$\Phi^*: (\mathbb{Z}/mn\mathbb{Z})^* \to (\mathbb{Z}/m\mathbb{Z})^* \times (\mathbb{Z}/n\mathbb{Z})^*.$$

Indeed, $\gcd(x, mn) = 1$ if and only if $\gcd(x, m) = 1$ and $\gcd(x, n) = 1$, since $m$ and $n$ share no prime factors. This bijection between units implies

$$\varphi(mn) = |(\mathbb{Z}/mn\mathbb{Z})^*| = |(\mathbb{Z}/m\mathbb{Z})^*| \cdot |(\mathbb{Z}/n\mathbb{Z})^*| = \varphi(m) \varphi(n).$$

Combining the prime power formula with multiplicativity, we obtain the general expression. For $n = p_1^{e_1} \cdots p_k^{e_k}$, we have

$$\varphi(n) = \varphi(p_1^{e_1}) \cdots \varphi(p_k^{e_k}) = p_1^{e_1 - 1}(p_1 - 1) \cdots p_k^{e_k - 1}(p_k - 1).$$

Factoring out $n = p_1^{e_1} \cdots p_k^{e_k}$ yields the product formula

$$\varphi(n) = n \prod_{i=1}^k \left(1 - \frac{1}{p_i}\right).$$

**Concrete Example:** For $n = 360 = 2^3 \cdot 3^2 \cdot 5$, we compute

$$\varphi(360) = 360 \cdot \left(1 - \frac{1}{2}\right) \left(1 - \frac{1}{3}\right) \left(1 - \frac{1}{5}\right) = 360 \cdot \frac{1}{2} \cdot \frac{2}{3} \cdot \frac{4}{5} = 96.$$

Alternatively, using the prime power formula directly:

$$\varphi(360) = 2^2(2 - 1) \cdot 3^1(3 - 1) \cdot 5^0(5 - 1) = 4 \cdot 1 \cdot 3 \cdot 2 \cdot 1 \cdot 4 = 96.$$

### Euler's Theorem and Fermat's Little Theorem

**Theorem (Euler):** If $\gcd(a, n) = 1$, then $a^{\varphi(n)} \equiv 1 \pmod{n}$.

**Proof:** Let $G = (\mathbb{Z}/n\mathbb{Z})^*$ denote the multiplicative group of units modulo $n$. By Lagrange's Theorem, the order of any element divides the order of the group. Since $|G| = \varphi(n)$, the order of $a$ in $G$ divides $\varphi(n)$, say $\text{ord}(a) = d$ with $d \mid \varphi(n)$. Write $\varphi(n) = d \cdot k$ for some integer $k$. Then

$$a^{\varphi(n)} = a^{dk} = (a^d)^k \equiv 1^k = 1 \pmod{n}.$$

**Corollary (Fermat's Little Theorem):** If $p$ is prime and $\gcd(a, p) = 1$, then $a^{p-1} \equiv 1 \pmod{p}$.

**Proof:** When $n = p$ is prime, every integer $a$ with $1 \le a < p$ satisfies $\gcd(a, p) = 1$, so $\varphi(p) = p - 1$. Applying Euler's Theorem yields $a^{p-1} \equiv 1 \pmod{p}$.

Multiplying both sides of Fermat's congruence by $a$ gives the alternate form $a^p \equiv a \pmod{p}$, which holds for all integers $a$ including multiples of $p$ since $0^p \equiv 0 \pmod{p}$.

**Computational Application:** Fermat's Little Theorem enables modular exponentiation via exponent reduction. To compute $a^e \bmod p$ where $e \ge p - 1$, write $e = q(p - 1) + r$ with $0 \le r < p - 1$. Then

$$a^e = a^{q(p-1) + r} = (a^{p-1})^q \cdot a^r \equiv 1^q \cdot a^r = a^r \pmod{p}.$$

For $a = 2$, $e = 1000$, $p = 7$, we have $\varphi(7) = 6$ and $1000 = 166 \cdot 6 + 4$, so

$$2^{1000} \equiv 2^4 = 16 \equiv 2 \pmod{7}.$$

### The Carmichael Function $\lambda(n)$

While Euler's Theorem guarantees $a^{\varphi(n)} \equiv 1 \pmod{n}$ for all $a$ coprime to $n$, the smallest such universal exponent is often strictly smaller than $\varphi(n)$. The Carmichael function $\lambda(n)$ is defined as the exponent of the group $(\mathbb{Z}/n\mathbb{Z})^*$, i.e., the smallest positive integer $m$ such that $a^m \equiv 1 \pmod{n}$ for all $a$ with $\gcd(a, n) = 1$. Equivalently, $\lambda(n)$ is the least common multiple of the orders of all elements in the group.

For prime powers, the structure is straightforward:

$$\lambda(2) = 1, \quad \lambda(4) = 2, \quad \lambda(2^k) = 2^{k-2} \text{ for } k \ge 3,$$

$$\lambda(p^k) = \varphi(p^k) = p^{k-1}(p - 1) \text{ for odd prime } p.$$

The anomalous behavior at powers of 2 arises because $(\mathbb{Z}/2^k\mathbb{Z})^*$ is not cyclic for $k \ge 3$; it decomposes as $\mathbb{Z}/2 \times \mathbb{Z}/2^{k-2}$.

For general $n = p_1^{e_1} \cdots p_k^{e_k}$, the Chinese Remainder Theorem decomposes the multiplicative group as a direct product, and the exponent of a direct product is the least common multiple of the component exponents:

$$\lambda(n) = \text{lcm}(\lambda(p_1^{e_1}), \ldots, \lambda(p_k^{e_k})).$$

**Example:** For $n = 72 = 2^3 \cdot 3^2$, we compute

$$\lambda(2^3) = 2^{3-2} = 2, \quad \lambda(3^2) = 3^{2-1}(3 - 1) = 6,$$

so $\lambda(72) = \text{lcm}(2, 6) = 6$. Indeed, $\varphi(72) = \varphi(8) \varphi(9) = 4 \cdot 6 = 24$, but every element of $(\mathbb{Z}/72\mathbb{Z})^*$ has order dividing 6.

The Carmichael function plays a critical role in the RSA cryptosystem. For RSA modulus $n = pq$ with distinct odd primes $p$ and $q$, we have

$$\lambda(n) = \text{lcm}(p - 1, q - 1).$$

The private exponent $d$ must satisfy $ed \equiv 1 \pmod{\lambda(n)}$ rather than $\pmod{\varphi(n)}$, though both formulations work. Using $\lambda(n)$ yields a smaller exponent and slightly faster decryption.

### Primitive Roots and Cyclic Multiplicative Groups

An integer $g$ is a primitive root modulo $n$ if its multiplicative order equals $\varphi(n)$, i.e., if $g$ generates the entire group $(\mathbb{Z}/n\mathbb{Z})^*$ under exponentiation. Not all moduli admit primitive roots; the complete characterization is given by the following theorem.

**Theorem (Primitive Root Existence):** A primitive root modulo $n$ exists if and only if $n \in \{1, 2, 4, p^k, 2p^k\}$ where $p$ is an odd prime and $k \ge 1$.

The proof relies on the structure theorem for finitely generated abelian groups. For $n = p^k$ with odd prime $p$, the group $(\mathbb{Z}/p^k\mathbb{Z})^*$ is cyclic of order $\varphi(p^k) = p^{k-1}(p - 1)$. For $n = 2p^k$, the Chinese Remainder Theorem gives

$$(\mathbb{Z}/2p^k\mathbb{Z})^* \cong (\mathbb{Z}/2\mathbb{Z})^* \times (\mathbb{Z}/p^k\mathbb{Z})^* \cong \mathbb{Z}/1 \times \mathbb{Z}/\varphi(p^k) \cong \mathbb{Z}/\varphi(p^k),$$

which remains cyclic. For $n = 2^k$ with $k \ge 3$, the group decomposes as $\mathbb{Z}/2 \times \mathbb{Z}/2^{k-2}$, which is not cyclic. For composite $n$ with two distinct odd prime factors, the group is a product of at least two nontrivial cyclic groups and thus non-cyclic.

**Existence for Prime Moduli:** We focus on the case $n = p$, proving that $(\mathbb{Z}/p\mathbb{Z})^*$ is cyclic. Let $p - 1 = q_1^{f_1} \cdots q_m^{f_m}$ be the prime factorization of $p - 1$. For each prime power divisor $d \mid (p - 1)$, the polynomial $x^d - 1$ has at most $d$ roots in the field $\mathbb{Z}/p\mathbb{Z}$. The number of elements of order exactly $d$ in $(\mathbb{Z}/p\mathbb{Z})^*$ is either 0 or $\varphi(d)$, since if one element of order $d$ exists, the cyclic subgroup it generates contains exactly $\varphi(d)$ generators.

By Lagrange's Theorem, every element has order dividing $p - 1$, so

$$p - 1 = \sum_{d \mid (p-1)} |\{a : \text{ord}(a) = d\}| \le \sum_{d \mid (p-1)} \varphi(d) = p - 1,$$

where the last equality follows from the identity $\sum_{d \mid n} \varphi(d) = n$. Thus equality holds throughout, implying that for every divisor $d$ of $p - 1$, there exist exactly $\varphi(d)$ elements of order $d$. In particular, there exist $\varphi(p - 1)$ elements of order $p - 1$, which are precisely the primitive roots modulo $p$.

**Lifting Primitive Roots to Prime Powers:** If $g$ is a primitive root modulo $p$, we can construct a primitive root modulo $p^k$ by a lifting procedure. If $g^{p-1} \not\equiv 1 \pmod{p^2}$, then $g$ itself is a primitive root modulo $p^k$ for all $k$. If $g^{p-1} \equiv 1 \pmod{p^2}$, then $g + p$ is a primitive root modulo $p^k$ for all $k$. This follows from Hensel's Lemma considerations and the factorization of $\varphi(p^k)$.

**Concrete Example:** For $p = 7$, we have $\varphi(7) = 6$ and $\varphi(6) = 2$, so there are exactly 2 primitive roots modulo 7 in the reduced residue system $\{1, 2, 3, 4, 5, 6\}$. Testing $g = 3$:

$$3^1 \equiv 3, \quad 3^2 \equiv 2, \quad 3^3 \equiv 6, \quad 3^4 \equiv 4, \quad 3^5 \equiv 5, \quad 3^6 \equiv 1 \pmod{7}.$$

Since $3$ generates all nonzero residues modulo 7, it is a primitive root. The other primitive root is $g = 5$:

$$5^1 \equiv 5, \quad 5^2 \equiv 4, \quad 5^3 \equiv 6, \quad 5^4 \equiv 2, \quad 5^5 \equiv 3, \quad 5^6 \equiv 1 \pmod{7}.$$

### Discrete Logarithms and Computational Hardness

When a primitive root $g$ modulo $p$ exists, every element $a \in (\mathbb{Z}/p\mathbb{Z})^*$ can be uniquely expressed as $a \equiv g^x \pmod{p}$ for some integer $x$ with $0 \le x < p - 1$. The integer $x$ is called the discrete logarithm of $a$ to the base $g$ modulo $p$, denoted $x = \log_g a$ or $x = \text{ind}_g(a)$.

The discrete logarithm satisfies properties analogous to the real logarithm:

$$\log_g(ab) \equiv \log_g a + \log_g b \pmod{p-1},$$

$$\log_g(a^k) \equiv k \log_g a \pmod{p-1}.$$

These properties follow from the group homomorphism $\phi: \mathbb{Z}/(p-1)\mathbb{Z} \to (\mathbb{Z}/p\mathbb{Z})^*$ given by $\phi(x) = g^x$.

**Computational Complexity:** While exponentiation $g^x \bmod p$ can be performed in $O(\log x)$ modular multiplications via binary exponentiation (with each multiplication taking $O(\log^2 p)$ bit operations using schoolbook arithmetic), the inverse problem of computing $x$ from $g^x$ is believed computationally intractable for sufficiently large primes. The best known classical algorithms are:

- **Baby-step giant-step:** Time complexity $O(\sqrt{p})$ with $O(\sqrt{p})$ storage. Precompute $g^j$ for $0 \le j < \lceil \sqrt{p-1} \rceil$ and store in a hash table. For given $a$, compute $a (g^{-\lceil \sqrt{p-1} \rceil})^i$ for $i = 0, 1, 2, \ldots$ until a collision is found with the precomputed table. Then $a \equiv g^j (g^{\lceil \sqrt{p-1} \rceil})^i$, so $x = j + i \lceil \sqrt{p-1} \rceil$.

- **Pollard's rho:** Expected time complexity $O(\sqrt{p})$ with $O(1)$ storage. Construct a pseudorandom walk in $(\mathbb{Z}/p\mathbb{Z})^*$ by partitioning the group into three sets and defining iterative multiplications by $g$, $a$, or squaring. Maintain parallel slow and fast iterators until a collision occurs, yielding a relation $g^{x_1} a^{y_1} \equiv g^{x_2} a^{y_2} \pmod{p}$, which can be solved for $\log_g a$.

- **Index calculus:** Subexponential complexity $L_p[1/2, c]$ where $L_p[\alpha, c] = \exp((c + o(1))(\log p)^\alpha (\log \log p)^{1-\alpha})$. Restrict attention to "smooth" elements that factor over a small factor base of primes. Collect linear relations modulo $p - 1$ among discrete logarithms of factor base elements, solve the resulting linear system, then express the target element in terms of the factor base.

For prime fields, the Number Field Sieve for discrete logarithms achieves complexity $L_p[1/3, (64/9)^{1/3}] \approx L_p[1/3, 1.923]$, which is subexponential but still infeasible for cryptographically sized primes (e.g., 2048-bit $p$). Quantum algorithms such as Shor's algorithm solve the discrete logarithm problem in polynomial time $O((\log p)^3)$, rendering classical discrete-logarithm-based cryptosystems insecure against quantum adversaries.

**Diffie-Hellman Key Exchange:** The computational hardness of discrete logarithms underpins the Diffie-Hellman protocol. Alice and Bob publicly agree on a prime $p$ and primitive root $g$. Alice chooses secret $a$ and sends $A = g^a \bmod p$; Bob chooses secret $b$ and sends $B = g^b \bmod p$. Both compute the shared secret $K = g^{ab} \bmod p$ via $K = B^a = A^b$. An eavesdropper observing $g, p, A, B$ must solve the Computational Diffie-Hellman (CDH) problem: given $g^a$ and $g^b$, compute $g^{ab}$. While CDH is not known to be equivalent to the discrete logarithm problem, no polynomial-time classical algorithm for CDH is known when discrete logarithms are hard.

## 3. High-Performance Optimization & Failure Modes

### Efficient Totient Computation via Factorization

The evaluation of $\varphi(n)$ reduces to integer factorization, which itself is computationally hard for large composite $n$. For cryptographic applications where $n = pq$ is a product of two large primes, the factorization is known by design to the key generator, and $\varphi(n) = (p - 1)(q - 1)$ is computed in constant time given $p$ and $q$. However, an adversary knowing only $n$ cannot efficiently compute $\varphi(n)$ without factoring $n$, since knowledge of $\varphi(n)$ combined with $n$ immediately yields $p$ and $q$ by solving the quadratic

$$t^2 - (n - \varphi(n) + 1)t + n = 0,$$

whose roots are $p$ and $q$. The coefficients satisfy $p + q = n - \varphi(n) + 1$ and $pq = n$.

For numbers with unknown factorization, trial division up to $\sqrt{n}$ requires $O(\sqrt{n})$ operations, which is infeasible for $n$ beyond $10^{20}$. The general number field sieve factors $n$ in heuristic time $L_n[1/3, (64/9)^{1/3}]$, subexponential but still prohibitively expensive for cryptographic moduli.

When $n$ is known to have small prime factors, the product formula for $\varphi(n)$ enables incremental computation. Factor out small primes $p_i \le B$ via trial division, compute $\varphi(p_i^{e_i})$ for each prime power, and multiply. If a large prime cofactor $q > B$ remains, test primality via Miller-Rabin or AKS; if prime, $\varphi(q) = q - 1$.

### Modular Exponentiation and Repeated Squaring

The evaluation of $a^e \bmod n$ via naive repeated multiplication requires $e - 1$ modular multiplications, which is exponential in the bit length of $e$. Binary exponentiation reduces this to $O(\log e)$ multiplications by processing the binary representation of $e$ from most significant to least significant bit.

**Algorithm (Right-to-Left Binary Exponentiation):**

Initialize $r \gets 1$ and $b \gets a \bmod n$. For each bit $e_i$ in the binary expansion $e = \sum_{i=0}^{k-1} e_i 2^i$, if $e_i = 1$ then $r \gets r \cdot b \bmod n$, then $b \gets b^2 \bmod n$. Return $r$.

**Invariant:** After processing bit $i$, we have $r \equiv a^{\sum_{j=0}^{i} e_j 2^j} \pmod{n}$ and $b \equiv a^{2^{i+1}} \pmod{n}$.

**Example:** Compute $3^{13} \bmod 7$. Binary representation: $13 = 1101_2$.

- $i = 0$: $e_0 = 1$, $r = 1 \cdot 3 = 3$, $b = 3^2 = 2 \pmod{7}$.
- $i = 1$: $e_1 = 0$, $r = 3$, $b = 2^2 = 4 \pmod{7}$.
- $i = 2$: $e_2 = 1$, $r = 3 \cdot 4 = 5 \pmod{7}$, $b = 4^2 = 2 \pmod{7}$.
- $i = 3$: $e_3 = 1$, $r = 5 \cdot 2 = 3 \pmod{7}$, $b = 2^2 = 4 \pmod{7}$.

Result: $3^{13} \equiv 3 \pmod{7}$.

For cryptographic exponents with $e \approx 2^{2048}$, this requires approximately 2048 squarings and 1024 multiplications on average, each modulo an $n$ of comparable size. Using Karatsuba multiplication (complexity $O(k^{1.585})$ for $k$-bit operands) or FFT-based multiplication (complexity $O(k \log k \log \log k)$), the total time complexity is $O(k^{2.585})$ or $O(k^2 \log k \log \log k)$ respectively for $k$-bit modulus.

### Primitive Root Search and Order Computation

To find a primitive root modulo prime $p$, we must verify that the order of a candidate $g$ equals $p - 1$. A naive approach tests whether $g^d \equiv 1 \pmod{p}$ for all proper divisors $d$ of $p - 1$, requiring iteration over $\tau(p - 1)$ divisors where $\tau$ is the divisor function. However, by group theory, the order of $g$ divides $p - 1$, and $g$ is a primitive root if and only if $g^{(p-1)/q} \not\equiv 1 \pmod{p}$ for every prime divisor $q$ of $p - 1$. Thus we need only test $\omega(p - 1)$ prime divisors, where $\omega(n)$ counts the number of distinct prime divisors.

**Algorithm (Primitive Root Verification):**

Given prime $p$, candidate $g$, and prime factorization $p - 1 = q_1^{f_1} \cdots q_m^{f_m}$, check that $g^{(p-1)/q_i} \not\equiv 1 \pmod{p}$ for $i = 1, \ldots, m$. If all tests pass, $g$ is a primitive root; otherwise, try next candidate.

Since there are $\varphi(p - 1)$ primitive roots among the $p - 1$ nonzero residues, the expected number of candidates tested before finding a primitive root is $(p - 1) / \varphi(p - 1)$. For $p - 1$ highly composite with many small prime factors, $\varphi(p - 1)$ is small relative to $p - 1$, increasing search time. For Sophie Germain primes where $p = 2q + 1$ with $q$ prime, we have $\varphi(p - 1) = \varphi(2q) = \varphi(2) \varphi(q) = q - 1 \approx (p - 1)/2$, so roughly half of all elements are primitive roots.

**Example:** For $p = 23$, we have $p - 1 = 22 = 2 \cdot 11$. Test $g = 2$:

$$2^{22/2} = 2^{11} \bmod 23, \quad 2^{22/11} = 2^2 = 4 \bmod 23.$$

Computing $2^{11} \bmod 23$ via binary exponentiation: $11 = 1011_2$, so $2^{11} = 2^8 \cdot 2^2 \cdot 2 = 256 \cdot 4 \cdot 2 = 2048 \equiv 1 \pmod{23}$. Since $2^{11} \equiv 1 \pmod{23}$, the order of 2 divides 11, hence 2 is not a primitive root.

Test $g = 5$: $5^{11} \bmod 23$ and $5^2 = 25 \equiv 2 \pmod{23}$. Computing $5^{11}$: $5^{11} = 5^8 \cdot 5^2 \cdot 5$. We have $5^2 = 2$, $5^4 = 4$, $5^8 = 16$, so $5^{11} = 16 \cdot 2 \cdot 5 = 160 \equiv 22 \equiv -1 \pmod{23}$. Since $5^{11} \not\equiv 1$ and $5^2 \not\equiv 1$, we conclude that 5 is a primitive root modulo 23.

### Carmichael Numbers and Fermat Pseudoprimes

Fermat's Little Theorem provides a necessary condition for primality: if $a^{n-1} \not\equiv 1 \pmod{n}$ for some $a$ coprime to $n$, then $n$ is composite. However, the converse fails: composite numbers $n$ satisfying $a^{n-1} \equiv 1 \pmod{n}$ for particular bases $a$ are called Fermat pseudoprimes to base $a$. A Carmichael number is a composite $n$ satisfying $a^{n-1} \equiv 1 \pmod{n}$ for all $a$ coprime to $n$, i.e., $\lambda(n) \mid (n - 1)$.

The smallest Carmichael number is $561 = 3 \cdot 11 \cdot 17$. We verify that $\lambda(561) = \text{lcm}(2, 10, 16) = 80$ divides $560 = 561 - 1$. Indeed, for any $a$ with $\gcd(a, 561) = 1$, we have $a^{80} \equiv 1 \pmod{561}$ by Carmichael's theorem, and since $560 = 7 \cdot 80$, we obtain $a^{560} = (a^{80})^7 \equiv 1 \pmod{561}$.

Carmichael numbers are characterized by Korselt's criterion: a composite $n > 1$ is a Carmichael number if and only if $n$ is squarefree and for every prime divisor $p$ of $n$, we have $(p - 1) \mid (n - 1)$. This implies that simple Fermat primality tests fail for Carmichael numbers regardless of the chosen base. The Miller-Rabin primality test strengthens Fermat's test by exploiting the structure of quadratic residues, successfully detecting Carmichael numbers with high probability.

### Discrete Logarithm Precomputation and Lookup Tables

For fixed small primes $p$, discrete logarithms can be precomputed and stored in lookup tables, reducing online computation to $O(1)$ table access. A table mapping $a \mapsto \log_g a$ for all $a \in (\mathbb{Z}/p\mathbb{Z})^*$ requires $O(p)$ storage. For primes up to $p \approx 10^6$, this remains feasible on modern hardware.

When $p$ is a safe prime (i.e., $p = 2q + 1$ with $q$ prime), the subgroup of quadratic residues modulo $p$ has prime order $q$, and discrete logarithms within this subgroup resist Pohlig-Hellman attacks that exploit smooth group orders. The Pohlig-Hellman algorithm reduces discrete logarithms in a group of order $n = \prod p_i^{e_i}$ to discrete logarithms in subgroups of prime power order $p_i^{e_i}$, then reconstructs the solution via the Chinese Remainder Theorem. Time complexity is $\sum_i e_i (\log n + \sqrt{p_i})$, exponential in the largest prime factor of $n$. For safe primes, the largest prime factor is approximately $p/2$, maintaining hardness.

### Boundary Cases and Degenerate Moduli

The totient function exhibits boundary behavior at small moduli: $\varphi(1) = 1$, $\varphi(2) = 1$. For $n = 2$, the multiplicative group $(\mathbb{Z}/2\mathbb{Z})^* = \{1\}$ is trivial, and 1 is the unique primitive root. For $n = 4$, we have $(\mathbb{Z}/4\mathbb{Z})^* = \{1, 3\}$ with $\varphi(4) = 2$ and $\lambda(4) = 2$; both 1 and 3 have order dividing 2, and 3 generates the group, so 3 is a primitive root modulo 4.

For $n = 8$, the group $(\mathbb{Z}/8\mathbb{Z})^* = \{1, 3, 5, 7\}$ has order 4, but $\varphi(4) = 2$ and $\lambda(8) = 2$. Testing orders: $3^2 = 9 \equiv 1 \pmod{8}$, $5^2 = 25 \equiv 1 \pmod{8}$, $7^2 = 49 \equiv 1 \pmod{8}$. Every element has order dividing 2, so the group is not cyclic, isomorphic to $\mathbb{Z}/2 \times \mathbb{Z}/2$. No primitive root exists modulo 8.

When implementing totient or Carmichael function computation, careful handling of the $n = 2^k$ case is essential. A common implementation error is to apply the formula $\lambda(2^k) = 2^{k-2}$ for all $k \ge 1$, which fails for $k = 1, 2$. The correct piecewise definition is

$$\lambda(2^k) = \begin{cases} 1 & \text{if } k = 1, \\ 2 & \text{if } k = 2, \\ 2^{k-2} & \text{if } k \ge 3. \end{cases}$$

Failure to distinguish these cases leads to incorrect exponent computation in RSA key generation when one of the primes is 2 (which never occurs in practice, since RSA primes are odd and large, but may arise in testing or educational implementations).

### Resistance to Side-Channel Attacks in Exponentiation

Modular exponentiation implementations must guard against timing attacks that leak information about the secret exponent through variations in execution time correlated with exponent bits. A naive binary exponentiation algorithm performs multiplication only when the current exponent bit is 1, creating a timing difference between 0-bits and 1-bits. An adversary measuring execution time can recover the exponent bit-by-bit.

**Countermeasure (Constant-Time Exponentiation):** Perform both squaring and multiplication in every iteration, but conditionally use the multiplication result based on the exponent bit via constant-time selection (e.g., bitwise masking or conditional move instructions that do not branch).

**Algorithm (Constant-Time Right-to-Left Exponentiation):**

Initialize $r \gets 1$ and $b \gets a$. For $i = 0$ to $k - 1$, compute $r' \gets r \cdot b \bmod n$, then set $r \gets r'$ if $e_i = 1$ or $r$ otherwise using constant-time selection. Then set $b \gets b^2 \bmod n$. Return $r$.

This ensures that the sequence of operations (and hence timing) is independent of the exponent bits, thwarting simple timing attacks. Further protections include blinding (randomizing the base or exponent) and scalar multiplication algorithms with regular patterns (e.g., Montgomery ladder).

For RSA signatures and decryption, Chinese Remainder Theorem optimization splits exponentiation modulo $n = pq$ into two exponentiations modulo $p$ and $q$, reducing each exponent to roughly half the bit length and quartering the total computation time. However, CRT-RSA is vulnerable to fault attacks where an adversary induces a computational error in one of the CRT branches, then factors $n$ from the faulty output. Implementations must include integrity checks or redundant computation to detect faults.
