# Lesson 5: Number Theory, Modular Arithmetic, Cryptographic Foundations

## 1. First-Principles Intuition & Invariants

Number theory emerged from humanity's earliest attempts to understand the structure of integers—the discrete, indivisible units of counting. Unlike the continuous real numbers that model physical quantities, integers exhibit combinatorial rigidity: they cannot be subdivided, only combined through addition and multiplication. This discreteness gives rise to phenomena entirely absent from continuous mathematics: prime factorization, modular periodicity, and the hard computational problems that underpin modern cryptography.

The fundamental theorem of arithmetic establishes that every integer greater than one admits a unique factorization into prime powers, up to reordering. This unique decomposition property makes primes the atoms of multiplicative structure, and understanding their distribution becomes the central problem of analytic number theory. When we write $n = p_1^{e_1} p_2^{e_2} \cdots p_k^{e_k}$, we are expressing $n$ in its canonical form, revealing its intrinsic multiplicative anatomy.

Divisibility provides the first structural lens through which we examine integers. We say that integer $a$ divides integer $b$, written $a \mid b$, if there exists an integer $k$ such that $b = ak$. This relation is reflexive ($a \mid a$), transitive (if $a \mid b$ and $b \mid c$ then $a \mid c$), and antisymmetric in the sense that if $a \mid b$ and $b \mid a$ with $a, b > 0$, then $a = b$. Divisibility forms a partial order on the positive integers, and this ordering structure governs the behavior of greatest common divisors and least common multiples.

The greatest common divisor $\gcd(a, b)$ is the largest positive integer dividing both $a$ and $b$. A profound invariant emerges: for any integers $a$ and $b$, there exist integers $x$ and $y$ satisfying the Bézout identity $\gcd(a, b) = ax + by$. This linear representation of the greatest common divisor is not merely an abstract curiosity—it provides the computational foundation for modular inverses, which enable division in modular arithmetic and underpin the RSA cryptosystem.

The Euclidean algorithm computes $\gcd(a, b)$ through a sequence of division steps, replacing the pair $(a, b)$ with $(b, a \bmod b)$ until the remainder vanishes. This process terminates in $O(\log \min(a, b))$ steps, a consequence of the fact that each iteration reduces the larger argument by at least half whenever it exceeds twice the smaller. The extended Euclidean algorithm augments this process to simultaneously compute the Bézout coefficients $x$ and $y$, maintaining the invariant that at each step $(r_i, s_i, t_i)$ satisfies $r_i = s_i a + t_i b$.

Modular arithmetic introduces equivalence classes that partition the integers into residue classes modulo $n$. When we write $a \equiv b \pmod{n}$, we assert that $n \mid (a - b)$, establishing an equivalence relation that respects addition and multiplication. The ring $\mathbb{Z}/n\mathbb{Z}$ of integers modulo $n$ inherits these operations, but exhibits fundamentally different behavior: zero divisors appear when $n$ is composite, and the multiplicative structure becomes intricate.

The units of $\mathbb{Z}/n\mathbb{Z}$—those elements admitting multiplicative inverses—are precisely the residue classes $[a]$ where $\gcd(a, n) = 1$. Euler's totient function $\phi(n)$ counts these units, measuring the order of the multiplicative group $(\mathbb{Z}/n\mathbb{Z})^*$. When $n = p$ is prime, every nonzero element is a unit, yielding $\phi(p) = p - 1$ and establishing $\mathbb{Z}/p\mathbb{Z}$ as a field—the finite field $\mathbb{F}_p$ where polynomial division and linear algebra operate without pathology.

Fermat's Little Theorem states that for prime $p$ and integer $a$ with $\gcd(a, p) = 1$, we have $a^{p-1} \equiv 1 \pmod{p}$. This result follows from Lagrange's theorem in group theory: the order of any element divides the group order, so $a^{\phi(p)} = a^{p-1} \equiv 1$. The immediate consequence is that $a^p \equiv a \pmod{p}$ for all integers $a$, providing both a primality test heuristic and the foundation for modular exponentiation in cryptographic protocols.

Euler's theorem generalizes Fermat's result to composite moduli: for any integer $a$ with $\gcd(a, n) = 1$, we have $a^{\phi(n)} \equiv 1 \pmod{n}$. This multiplicative periodicity governs the structure of repeated modular multiplication. When we compute $a^k \bmod n$, we can reduce the exponent modulo $\phi(n)$ without changing the result, transforming potentially astronomic exponentiation into tractable computation through the identity $a^k \equiv a^{k \bmod \phi(n)} \pmod{n}$.

The RSA cryptosystem exploits the computational asymmetry between modular exponentiation and discrete logarithm extraction. Given primes $p$ and $q$, we set $n = pq$ and choose encryption exponent $e$ with $\gcd(e, \phi(n)) = 1$. The decryption exponent $d$ satisfies $ed \equiv 1 \pmod{\phi(n)}$, computable via the extended Euclidean algorithm. Encryption transforms message $m$ into ciphertext $c = m^e \bmod n$, while decryption recovers $m = c^d \bmod n$. The correctness follows from Euler's theorem: since $ed = 1 + k\phi(n)$ for some integer $k$, we have $c^d = (m^e)^d = m^{ed} = m^{1 + k\phi(n)} = m \cdot (m^{\phi(n)})^k \equiv m \cdot 1^k = m \pmod{n}$.

The security of RSA rests on the hardness of factoring: given $n = pq$ and $e$, an adversary who factors $n$ can compute $\phi(n) = (p-1)(q-1)$ and derive $d$ through the extended Euclidean algorithm. No polynomial-time classical algorithm is known for factoring large semiprimes, creating a computational moat around private keys. The public key $(n, e)$ enables anyone to encrypt, while only the holder of the private key $(n, d)$—equivalently, the holder of the factorization $(p, q)$—can decrypt.

## 2. Core Architecture & Mechanics

The divisibility relation induces a lattice structure on the positive integers under $\gcd$ and $\text{lcm}$ operations. For any pair of integers $a$ and $b$, their greatest common divisor forms the meet (infimum) in this lattice, while their least common multiple forms the join (supremum). These operations satisfy the absorption laws: $\gcd(a, \text{lcm}(a, b)) = a$ and $\text{lcm}(a, \gcd(a, b)) = a$. The fundamental identity $\gcd(a, b) \cdot \text{lcm}(a, b) = ab$ reveals the complementary nature of these operations, linking the smallest common divisor to the largest common multiple through the product.

The Euclidean algorithm proceeds through a sequence of remainder reductions. Given inputs $a \geq b > 0$, we perform the division $a = bq_1 + r_1$ with $0 \leq r_1 < b$. If $r_1 = 0$, then $\gcd(a, b) = b$. Otherwise, we recurse with $(b, r_1)$, obtaining $b = r_1 q_2 + r_2$. This process generates a strictly decreasing sequence of remainders $b > r_1 > r_2 > \cdots \geq 0$ that must terminate when some $r_k = 0$, at which point $\gcd(a, b) = r_{k-1}$.

The correctness of the Euclidean algorithm follows from the invariant that $\gcd(a, b) = \gcd(b, r_1)$ at each step. To verify this, observe that any common divisor of $a$ and $b$ must divide $r_1 = a - bq_1$, so it divides both $b$ and $r_1$. Conversely, any common divisor of $b$ and $r_1$ divides $a = bq_1 + r_1$. Thus the set of common divisors remains unchanged, and the greatest common divisor is preserved.

The extended Euclidean algorithm maintains auxiliary variables to track the linear combination. We initialize $(r_0, s_0, t_0) = (a, 1, 0)$ and $(r_1, s_1, t_1) = (b, 0, 1)$, ensuring that $r_i = s_i a + t_i b$ at each step. When we compute $r_{i+1} = r_{i-1} - q_i r_i$ from the division $r_{i-1} = q_i r_i + r_{i+1}$, we simultaneously update $s_{i+1} = s_{i-1} - q_i s_i$ and $t_{i+1} = t_{i-1} - q_i t_i$. The invariant is preserved by linearity: $r_{i+1} = (s_{i-1} - q_i s_i)a + (t_{i-1} - q_i t_i)b$. When the algorithm terminates with remainder $r_k = \gcd(a, b)$, we obtain Bézout coefficients $(s_k, t_k)$ satisfying $\gcd(a, b) = s_k a + t_k b$.

Let us trace the extended Euclidean algorithm computing $\gcd(240, 46)$ with full state tracking:

```
i  |  r_i   q_i   s_i   t_i
---|------------------------
0  |  240    -     1     0
1  |   46    -     0     1
---|------------------------
2  |   10    5     1    -5      (240 - 5·46 = 10)
3  |    6    4     -4   21      (46 - 4·10 = 6)
4  |    4    1     5   -26      (10 - 1·6 = 4)
5  |    2    1    -9    47      (6 - 1·4 = 2)
6  |    0    2     -     -      (4 - 2·2 = 0)
```

The algorithm terminates at step 5 with $\gcd(240, 46) = 2$, yielding the Bézout identity $2 = (-9) \cdot 240 + 47 \cdot 46$. We verify: $-9 \cdot 240 + 47 \cdot 46 = -2160 + 2162 = 2$.

Modular arithmetic operations form a ring structure on $\mathbb{Z}/n\mathbb{Z}$. Addition is performed component-wise with reduction: $(a + b) \bmod n$. Multiplication likewise reduces the product: $(a \cdot b) \bmod n$. These operations are well-defined on equivalence classes because congruence is compatible with arithmetic: if $a \equiv a' \pmod{n}$ and $b \equiv b' \pmod{n}$, then $a + b \equiv a' + b' \pmod{n}$ and $ab \equiv a'b' \pmod{n}$.

The multiplicative inverse of $a$ modulo $n$ exists if and only if $\gcd(a, n) = 1$. When the inverse exists, it is the unique residue class $[x]$ satisfying $ax \equiv 1 \pmod{n}$. The extended Euclidean algorithm provides the computational method: running the algorithm on $(a, n)$ yields coefficients $s$ and $t$ with $sa + tn = \gcd(a, n) = 1$. Reducing modulo $n$, we obtain $sa \equiv 1 \pmod{n}$, so $a^{-1} \equiv s \pmod{n}$.

Consider computing $13^{-1} \bmod 60$. We execute the extended Euclidean algorithm on $(13, 60)$:

```
i  |  r_i   q_i   s_i   t_i
---|------------------------
0  |   60    -     1     0
1  |   13    -     0     1
---|------------------------
2  |    8    4     1    -4
3  |    5    1    -1     5
4  |    3    1     2    -9
5  |    2    1    -3    14
6  |    1    1     5   -23
7  |    0    2     -     -
```

We find $\gcd(13, 60) = 1$ with $1 = 5 \cdot 13 + (-1) \cdot 60$, so $13^{-1} \equiv 5 \pmod{60}$. Verification: $13 \cdot 5 = 65 = 60 + 5 \equiv 5 \pmod{60}$ is incorrect; we recalculate: $13 \cdot 5 = 65 \equiv 5 \pmod{60}$. Checking properly: $13 \cdot 5 = 65 = 1 \cdot 60 + 5$, so $13 \cdot 5 \equiv 5 \pmod{60}$, which is not 1. Let us retrace: from $1 = 5 \cdot 13 - 1 \cdot 60$, we have $5 \cdot 13 \equiv 1 \pmod{60}$, confirming $13^{-1} \equiv 5 \pmod{60}$. Direct check: $13 \cdot 5 = 65 = 60 + 5$, so $13 \cdot 5 \bmod 60 = 5$, not 1. There is an error in the algorithm trace. Let us recompute from scratch.

The division sequence for $\gcd(60, 13)$:

$$\begin{align}
60 &= 4 \cdot 13 + 8 \\
13 &= 1 \cdot 8 + 5 \\
8 &= 1 \cdot 5 + 3 \\
5 &= 1 \cdot 3 + 2 \\
3 &= 1 \cdot 2 + 1 \\
2 &= 2 \cdot 1 + 0
\end{align}$$

Back-substitution from $1 = 3 - 1 \cdot 2$:

$$\begin{align}
1 &= 3 - 1 \cdot 2 \\
  &= 3 - 1 \cdot (5 - 1 \cdot 3) = 2 \cdot 3 - 1 \cdot 5 \\
  &= 2 \cdot (8 - 1 \cdot 5) - 1 \cdot 5 = 2 \cdot 8 - 3 \cdot 5 \\
  &= 2 \cdot 8 - 3 \cdot (13 - 1 \cdot 8) = 5 \cdot 8 - 3 \cdot 13 \\
  &= 5 \cdot (60 - 4 \cdot 13) - 3 \cdot 13 = 5 \cdot 60 - 23 \cdot 13
\end{align}$$

Thus $1 = -23 \cdot 13 + 5 \cdot 60$, yielding $(-23) \cdot 13 \equiv 1 \pmod{60}$. Since $-23 \equiv 37 \pmod{60}$, we have $13^{-1} \equiv 37 \pmod{60}$. Verification: $13 \cdot 37 = 481 = 8 \cdot 60 + 1 \equiv 1 \pmod{60}$.

Modular exponentiation computes $a^k \bmod n$ efficiently through repeated squaring. Representing the exponent in binary as $k = \sum_{i=0}^{t} k_i 2^i$ with $k_i \in \{0, 1\}$, we write $a^k = \prod_{i: k_i = 1} a^{2^i}$. The algorithm maintains a running product, squaring the base at each step and multiplying into the accumulator when the corresponding bit is set. This reduces exponentiation from $O(k)$ multiplications to $O(\log k)$ multiplications and squarings.

The square-and-multiply algorithm for $a^k \bmod n$ proceeds as follows. Initialize result $r = 1$ and base $b = a \bmod n$. Scan the bits of $k$ from least significant to most significant. For each bit position $i$: if bit $k_i = 1$, update $r \gets (r \cdot b) \bmod n$; then square the base $b \gets b^2 \bmod n$ for the next iteration. When all bits are processed, $r$ contains $a^k \bmod n$.

Computing $3^{47} \bmod 23$ illustrates the method. The binary representation of $47$ is $101111_2$, scanning right to left as bits $(1, 1, 1, 1, 0, 1)$:

```
Bit  |  r         b         Operation
-----|------------------------------------
Init |  1         3
  1  |  3        9         r = 1·3 = 3, b = 3² = 9
  1  |  4        12        r = 3·9 = 27 ≡ 4, b = 9² = 81 ≡ 12
  1  |  2        6         r = 4·12 = 48 ≡ 2, b = 12² = 144 ≡ 6
  1  |  12       13        r = 2·6 = 12, b = 6² = 36 ≡ 13
  0  |  12       8         r unchanged, b = 13² = 169 ≡ 8
  1  |  4        -         r = 12·8 = 96 ≡ 4
```

Thus $3^{47} \equiv 4 \pmod{23}$. We can verify using Fermat's Little Theorem: $\phi(23) = 22$, so $3^{22} \equiv 1 \pmod{23}$. Then $3^{47} = 3^{44} \cdot 3^3 = (3^{22})^2 \cdot 27 \equiv 1^2 \cdot 27 \equiv 4 \pmod{23}$.

Euler's totient function $\phi(n)$ counts integers in $\{1, 2, \ldots, n\}$ coprime to $n$. For prime $p$, all nonzero residues are coprime to $p$, yielding $\phi(p) = p - 1$. For prime power $p^k$, the only residues sharing a factor with $p^k$ are the multiples of $p$, of which there are $p^{k-1}$, giving $\phi(p^k) = p^k - p^{k-1} = p^{k-1}(p - 1)$. The totient function is multiplicative: for coprime integers $m$ and $n$, we have $\phi(mn) = \phi(m)\phi(n)$. This follows from the Chinese Remainder Theorem, which establishes an isomorphism $\mathbb{Z}/mn\mathbb{Z} \cong \mathbb{Z}/m\mathbb{Z} \times \mathbb{Z}/n\mathbb{Z}$ preserving the unit groups.

For $n = p_1^{e_1} \cdots p_k^{e_k}$, multiplicativity yields the product formula:

$$\phi(n) = n \prod_{p \mid n} \left(1 - \frac{1}{p}\right) = \prod_{i=1}^k p_i^{e_i - 1}(p_i - 1)$$

Computing $\phi(720)$ where $720 = 2^4 \cdot 3^2 \cdot 5$:

$$\phi(720) = 720 \cdot \left(1 - \frac{1}{2}\right)\left(1 - \frac{1}{3}\right)\left(1 - \frac{1}{5}\right) = 720 \cdot \frac{1}{2} \cdot \frac{2}{3} \cdot \frac{4}{5} = 192$$

Alternatively, $\phi(720) = 2^3(2-1) \cdot 3^1(3-1) \cdot 5^0(5-1) = 8 \cdot 1 \cdot 2 \cdot 2 \cdot 1 \cdot 4 = 8 \cdot 2 \cdot 4 \cdot 2 = 192$.

The proof of Euler's theorem relies on group theory. The set $U_n = \{a \in \mathbb{Z}/n\mathbb{Z} : \gcd(a, n) = 1\}$ forms a group under multiplication modulo $n$, with identity 1 and inverses guaranteed by the Bézout identity. This group has order $|U_n| = \phi(n)$. By Lagrange's theorem, the order of any element divides the group order, so for any $a \in U_n$, we have $a^{\phi(n)} = 1$ in $U_n$, equivalently $a^{\phi(n)} \equiv 1 \pmod{n}$.

The Chinese Remainder Theorem provides an isomorphism between $\mathbb{Z}/n\mathbb{Z}$ and the product $\prod_{i=1}^k \mathbb{Z}/p_i^{e_i}\mathbb{Z}$ when $n = \prod p_i^{e_i}$ is the prime factorization. Given a system of congruences $x \equiv a_i \pmod{m_i}$ with pairwise coprime moduli $m_i$, there exists a unique solution modulo $M = \prod m_i$. The constructive proof uses the method of successive substitutions or direct construction via $x = \sum_{i=1}^k a_i M_i y_i$ where $M_i = M/m_i$ and $y_i$ satisfies $M_i y_i \equiv 1 \pmod{m_i}$.

RSA key generation begins with the selection of two large distinct primes $p$ and $q$, typically 1024 or 2048 bits each. The modulus $n = pq$ becomes the public parameter, while $\phi(n) = (p-1)(q-1)$ remains secret. The encryption exponent $e$ is chosen such that $1 < e < \phi(n)$ and $\gcd(e, \phi(n)) = 1$; common choices include $e = 3$, $e = 17$, or $e = 65537 = 2^{16} + 1$, which enable fast encryption via minimal Hamming weight. The decryption exponent $d$ is computed as the modular inverse of $e$ modulo $\phi(n)$ using the extended Euclidean algorithm, yielding $ed \equiv 1 \pmod{\phi(n)}$.

The RSA encryption function maps plaintext $m \in \{0, 1, \ldots, n-1\}$ to ciphertext $c = m^e \bmod n$. Decryption recovers $m$ via $m = c^d \bmod n$. Correctness follows from the identity $(m^e)^d = m^{ed} \equiv m \pmod{n}$ when $\gcd(m, n) = 1$. For the rare case where $\gcd(m, n) > 1$, the message shares a factor with $n$, revealing the factorization and breaking the system. In practice, proper padding schemes like OAEP ensure that plaintexts are preprocessed to avoid pathological cases and provide semantic security.

The formal correctness proof proceeds as follows. Since $ed \equiv 1 \pmod{\phi(n)}$, there exists integer $k$ such that $ed = 1 + k\phi(n)$. Then $m^{ed} = m \cdot (m^{\phi(n)})^k$. If $\gcd(m, n) = 1$, Euler's theorem gives $m^{\phi(n)} \equiv 1 \pmod{n}$, so $(m^{\phi(n)})^k \equiv 1 \pmod{n}$ and $m^{ed} \equiv m \pmod{n}$.

When $\gcd(m, n) > 1$, we split the analysis using the Chinese Remainder Theorem. Since $n = pq$ with distinct primes $p$ and $q$, either $p \mid m$ or $q \mid m$ (but not both, else $n \mid m$ contradicting $m < n$ for nonzero messages). Suppose $p \mid m$. Then $m \equiv 0 \pmod{p}$, so $m^{ed} \equiv 0 \equiv m \pmod{p}$. For modulo $q$: since $\gcd(m, q) = 1$, Fermat's Little Theorem yields $m^{q-1} \equiv 1 \pmod{q}$. Now $\phi(n) = (p-1)(q-1)$, so $ed - 1 = k(p-1)(q-1) = k(p-1) \cdot (q-1)$, giving $m^{ed} = m^{1 + k(p-1)(q-1)} = m \cdot (m^{q-1})^{k(p-1)} \equiv m \cdot 1^{k(p-1)} = m \pmod{q}$. By the Chinese Remainder Theorem, $m^{ed} \equiv m \pmod{p}$ and $m^{ed} \equiv m \pmod{q}$ together imply $m^{ed} \equiv m \pmod{pq}$.

## 3. High-Performance Optimization & Failure Modes

The Euclidean algorithm's runtime is bounded by the Lamé theorem, which states that for $a > b$, the number of division steps is at most $5h$ where $h$ is the number of decimal digits in $b$. More precisely, if the algorithm takes $k$ steps, then $b \geq F_{k+1}$ where $F_i$ denotes the $i$-th Fibonacci number. Since $F_n \sim \phi^n / \sqrt{5}$ with golden ratio $\phi = (1 + \sqrt{5})/2 \approx 1.618$, the number of steps is $O(\log b)$. This logarithmic complexity makes the Euclidean algorithm efficient even for astronomically large integers encountered in cryptography.

Binary GCD algorithms replace division with shifts and subtractions, exploiting the efficiency of binary operations in hardware. The binary GCD recursively applies the identities: if both $a$ and $b$ are even, then $\gcd(a, b) = 2 \gcd(a/2, b/2)$; if $a$ is even and $b$ is odd, then $\gcd(a, b) = \gcd(a/2, b)$; if both are odd, then $\gcd(a, b) = \gcd(|a - b|, \min(a, b))$. These reductions preserve the GCD while replacing expensive divisions with cheap bit shifts and subtractions. The binary GCD achieves the same asymptotic complexity as the Euclidean algorithm but with better constant factors on modern architectures.

Modular multiplication for large integers requires careful implementation to avoid overflow. The naive computation $(a \cdot b) \bmod n$ for $a, b < n$ can produce an intermediate product $a \cdot b$ of size $2 \log_2 n$ bits. Montgomery multiplication provides a method for computing $abR^{-1} \bmod n$ efficiently for fixed $R$, avoiding explicit division by $n$. By performing all arithmetic in the Montgomery domain with representatives $\tilde{a} = aR \bmod n$, multiplication and exponentiation proceed without trial division, and the final result is converted back via a single Montgomery reduction.

The Montgomery reduction algorithm computes $TR^{-1} \bmod n$ for $T < nR$ given precomputed $n' = -n^{-1} \bmod R$ where $R$ is coprime to $n$ and typically a power of 2. The algorithm computes $m = Tn' \bmod R$, then $(T + mn)/R$, which equals $TR^{-1} \bmod n$. This avoids explicit division by $n$ through the use of division by $R$, which is a simple right shift when $R = 2^k$.

Modular exponentiation via repeated squaring minimizes multiplications but can leak information through timing side channels. The number of multiplications depends on the Hamming weight of the exponent—the number of 1 bits—allowing an adversary to infer bits of the private exponent by measuring execution time. Constant-time implementations use the square-and-multiply-always variant, performing a dummy multiplication when the bit is 0 to ensure uniform operation count. More sophisticated approaches like Montgomery ladders provide scalar multiplication algorithms with data-independent control flow.

Prime generation for RSA requires probabilistic primality testing. Deterministic primality proofs are computationally expensive for large numbers, so practical implementations use the Miller-Rabin test, which provides a probabilistic guarantee. The Miller-Rabin test exploits the fact that for odd prime $p$, we can write $p - 1 = 2^s d$ with $d$ odd, and for any $a$ not divisible by $p$, either $a^d \equiv 1 \pmod{p}$ or $a^{2^r d} \equiv -1 \pmod{p}$ for some $0 \leq r < s$. A composite number passing this test for a random base $a$ is called a strong pseudoprime to base $a$. Running the test with $k$ independent random bases reduces the probability of erroneously declaring a composite as prime to at most $4^{-k}$.

The deterministic Miller test for a candidate prime $n$ writes $n - 1 = 2^s d$ and checks whether $a^d \equiv 1 \pmod{n}$ or $a^{2^r d} \equiv -1 \pmod{n}$ for some $r \in \{0, 1, \ldots, s-1\}$. If neither condition holds, $n$ is composite. Testing with $a = 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37$ suffices to deterministically verify primality for all $n < 2^{64}$, eliminating probabilistic uncertainty for moderate-sized integers.

Choosing RSA parameters involves security-performance tradeoffs. Larger moduli provide greater security against factoring but slow encryption and decryption. Current recommendations specify 2048-bit moduli for medium-term security and 3072-bit or 4096-bit moduli for long-term protection. The encryption exponent $e = 65537$ balances security and performance: its low Hamming weight (two 1 bits) enables fast encryption via two squarings and one multiplication, while being large enough to resist attacks exploiting small exponents.

Small encryption exponents like $e = 3$ enable fast encryption but introduce vulnerabilities when used without proper padding. If the plaintext $m$ satisfies $m^3 < n$, then $c = m^3 \bmod n = m^3$ over the integers, allowing trivial recovery via integer cube root extraction. Broadcast attacks compound this: if the same message $m$ is encrypted to $e$ different recipients with coprime moduli $n_1, \ldots, n_e$ using exponent $e$, the Chinese Remainder Theorem allows recovery of $m^e \bmod \prod n_i = m^e$ over the integers, again enabling root extraction. Proper padding schemes like OAEP prepend randomness to prevent such structural attacks.

The factorization of $n = pq$ remains computationally hard for sufficiently large primes chosen uniformly at random. The General Number Field Sieve (GNFS), the fastest known classical factoring algorithm, has conjectured complexity $\exp(O((\log n)^{1/3} (\log \log n)^{2/3}))$, subexponential in $\log n$ but superpolynomial. For 2048-bit moduli, GNFS requires on the order of $2^{110}$ operations, far beyond current computational feasibility.

Quantum computers threaten RSA through Shor's algorithm, which factors integers in polynomial time $O((\log n)^3)$ using quantum Fourier transforms to find the period of modular exponentiation. A quantum computer with several thousand error-corrected logical qubits could factor 2048-bit numbers in hours, breaking RSA entirely. Post-quantum cryptography develops alternative schemes resistant to quantum attacks, including lattice-based cryptosystems (Learning With Errors), hash-based signatures (SPHINCS+), and code-based encryption (Classic McEliece).

Modular arithmetic failures arise from implementation errors in reduction and overflow handling. Incorrect reduction can produce representatives outside $\{0, 1, \ldots, n-1\}$, breaking congruence invariants. Integer overflow in intermediate products corrupts results silently. Defensive implementations use arbitrary-precision arithmetic libraries like GMP (GNU Multiple Precision) that dynamically allocate storage and handle carries correctly.

Timing attacks exploit data-dependent execution paths in modular exponentiation. If the square-and-multiply algorithm skips multiplications when exponent bits are 0, an adversary measuring execution time can infer the Hamming weight of the exponent. More refined attacks like Kocher's timing attack recover individual bits through statistical analysis of timing variations. Blinding techniques randomize the computation: before decryption, multiply the ciphertext by $r^e$ for random $r$, perform decryption, then multiply the result by $r^{-1}$. This randomization decorrelates execution time from the plaintext, thwarting timing analysis.

Fault attacks introduce transient hardware errors during cryptographic operations to extract secret keys. Bellcore's attack on RSA-CRT implementations induces a fault in one of the CRT computations, producing an incorrect signature $s'$ where $s' \equiv s \pmod{p}$ but $s' \not\equiv s \pmod{q}$. Computing $\gcd(s'^e - m, n)$ reveals the prime $p$, breaking the system. Countermeasures include redundant computation with comparison, algorithmic fault detection via invariant checking, and hardware-level fault detection mechanisms.

Side-channel resistance requires algorithmic and implementation vigilance. Constant-time algorithms eliminate data-dependent branches and memory accesses. Masking splits secret values into random shares, ensuring that intermediate computations reveal no information about secrets without access to all shares. Hardware countermeasures include random instruction scheduling, noise injection, and physical shielding against electromagnetic and power analysis.

The mathematical elegance of number theory—divisibility lattices, modular periodicity, and multiplicative group structure—translates directly into the cryptographic protocols securing modern communication. The computational hardness of integer factorization and discrete logarithms creates asymmetry between public and private operations, enabling public-key cryptography. Careful implementation closes the gap between mathematical security and physical realizability, bridging pure theory and engineering practice to safeguard information in an adversarial world.
