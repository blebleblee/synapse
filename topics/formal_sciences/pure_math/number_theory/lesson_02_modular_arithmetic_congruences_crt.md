# Lesson 2: Modular Arithmetic, Congruences, and the Chinese Remainder Theorem

## 1. First-Principles Intuition & Invariants

Number theory begins, in a deep sense, with the observation that equality is too strong a relation for many computational and structural purposes. When a clock strikes thirteen, we do not record the number thirteen—we record one, because the mechanism of the clock cares only about residues modulo twelve. This apparently mundane observation conceals an extraordinary algebraic architecture. Modular arithmetic is not a weakening of ordinary arithmetic; it is a quotient construction that exposes the multiplicative and additive skeleton of the integers in ways that absolute equality obscures.

### Congruence as an Equivalence Relation

Let $m$ be a positive integer. We say that two integers $a$ and $b$ are **congruent modulo $m$**, written $a \equiv b \pmod{m}$, if $m \mid (a - b)$—that is, if the difference $a - b$ is divisible by $m$. This single definition does enormous work. It is immediately an equivalence relation on $\mathbb{Z}$: reflexivity holds because $m \mid 0$; symmetry holds because $m \mid (a-b)$ implies $m \mid (b-a)$; transitivity holds because $m \mid (a-b)$ and $m \mid (b-c)$ together imply $m \mid (a-c)$ by the closure of divisibility under addition.

The equivalence classes under this relation are the **residue classes** modulo $m$. The class of an integer $a$ is the set $[a]_m = \{a + km : k \in \mathbb{Z}\}$, which we can canonically represent by the unique integer $r$ satisfying $0 \le r < m$ and $r \equiv a \pmod{m}$. There are exactly $m$ such classes, forming the set $\mathbb{Z}/m\mathbb{Z} = \{[0]_m, [1]_m, \ldots, [m-1]_m\}$. What elevates this from a mere partitioning of $\mathbb{Z}$ into an algebraic object is the fact that addition and multiplication are **well-defined** on these classes: if $a \equiv a' \pmod{m}$ and $b \equiv b' \pmod{m}$, then both $a + b \equiv a' + b' \pmod{m}$ and $ab \equiv a'b' \pmod{m}$.

The proof of multiplicative compatibility is worth carrying out explicitly because it underpins everything that follows. Write $a = a' + sm$ and $b = b' + tm$ for integers $s, t$. Then:

$$ab = (a' + sm)(b' + tm) = a'b' + a'tm + smb' + s t m^2 = a'b' + m(a't + sb' + stm).$$

Since $m$ divides the second term, $ab \equiv a'b' \pmod{m}$. This establishes that $\mathbb{Z}/m\mathbb{Z}$ is a commutative ring under the induced operations, called the **ring of integers modulo $m$**.

### The Multiplicative Group and Units

Not every element of $\mathbb{Z}/m\mathbb{Z}$ is invertible. The class $[a]_m$ is a unit—that is, has a multiplicative inverse—if and only if $\gcd(a, m) = 1$. The collection of all such units forms a group under multiplication, denoted $(\mathbb{Z}/m\mathbb{Z})^{\times}$, whose order is given by **Euler's totient function**:

$$\phi(m) = m \prod_{p \mid m} \left(1 - \frac{1}{p}\right),$$

where the product ranges over distinct prime divisors of $m$. For $m = p$ prime, every nonzero residue is a unit, so $(\mathbb{Z}/p\mathbb{Z})^{\times}$ has order $p - 1$ and, since every finite subgroup of the multiplicative group of a field is cyclic, it is in fact cyclic of order $p - 1$. This cyclic structure—the existence of a primitive root modulo $p$—is a cornerstone of discrete logarithm-based reasoning.

**Euler's theorem** states that for $\gcd(a, m) = 1$, we have $a^{\phi(m)} \equiv 1 \pmod{m}$. When $m = p$ is prime, this reduces to **Fermat's little theorem**: $a^{p-1} \equiv 1 \pmod{p}$ for $p \nmid a$, or equivalently $a^p \equiv a \pmod{p}$ for all $a$. Both results follow from the same Lagrange's-theorem argument: the order of any element in a finite group divides the group order, so $a^{\phi(m)} = 1$ in $(\mathbb{Z}/m\mathbb{Z})^{\times}$.

### Wilson's Theorem

A striking and self-contained result that connects modular arithmetic directly to the characterization of primes is **Wilson's theorem**: an integer $p > 1$ is prime if and only if

$$(p-1)! \equiv -1 \pmod{p}.$$

**Proof.** For the forward direction, suppose $p$ is prime. We work in the field $\mathbb{F}_p = \mathbb{Z}/p\mathbb{Z}$. Consider the product $(p-1)! = 1 \cdot 2 \cdots (p-1)$. In $\mathbb{F}_p^{\times}$, every element $a$ has a unique inverse $a^{-1}$. The only elements that are their own inverses satisfy $a^2 \equiv 1 \pmod{p}$, i.e., $p \mid (a-1)(a+1)$, so $a \equiv 1$ or $a \equiv -1 \pmod{p}$. Every other element $a \in \{2, 3, \ldots, p-2\}$ pairs with a distinct element $a^{-1} \neq a$, and each such pair contributes $a \cdot a^{-1} = 1$ to the product. The product over all elements of $\mathbb{F}_p^{\times}$ therefore collapses to

$$(p-1)! \equiv 1 \cdot (p-1) \cdot \prod_{\substack{a=2 \\ a \neq a^{-1}}}^{p-2} a \equiv 1 \cdot (-1) \cdot 1 \equiv -1 \pmod{p}.$$

For the converse, suppose $p$ is composite. Then $p$ has a divisor $d$ with $1 < d < p$, so $d \mid (p-1)!$. If $(p-1)! \equiv -1 \pmod{p}$, then $p \mid (p-1)! + 1$, and since $d \mid p$ this gives $d \mid (p-1)! + 1$. But $d \mid (p-1)!$ as well, so $d \mid 1$, a contradiction. Hence composite $p$ cannot satisfy the congruence. $\blacksquare$

Wilson's theorem is elegant but computationally impractical as a primality test—computing $(p-1)! \bmod p$ costs $O(p)$ multiplications, exponential in the bit-length of $p$—yet it carries real theoretical weight, appearing in proofs of quadratic reciprocity and in constructions involving Wilson quotients.

---

## 2. Core Architecture & Mechanics

### Linear Congruences: Solvability and Complete Solution Sets

The first genuinely nontrivial problem in modular arithmetic is solving a **linear congruence**: given integers $a$, $b$, and $m$ with $m > 0$, find all integers $x$ such that

$$ax \equiv b \pmod{m}.$$

This is not simply division. The congruence $ax \equiv b \pmod{m}$ is equivalent to the Diophantine equation $ax - my = b$ for integers $x, y$, and by Bezout's identity this equation has a solution if and only if $d = \gcd(a, m)$ divides $b$.

**Theorem (Linear Congruence).** The congruence $ax \equiv b \pmod{m}$ has a solution if and only if $d = \gcd(a,m)$ divides $b$. When solutions exist, there are exactly $d$ incongruent solutions modulo $m$, given explicitly by

$$x \equiv x_0 + \frac{m}{d} k \pmod{m}, \quad k = 0, 1, \ldots, d-1,$$

where $x_0$ is any particular solution.

**Proof.** Write $d = \gcd(a, m)$. The congruence $ax \equiv b \pmod{m}$ holds iff $m \mid ax - b$, iff $ax - b = my$ for some $y \in \mathbb{Z}$. By Bezout, the set of integers representable as $ax + my$ over all $x, y \in \mathbb{Z}$ is exactly $d\mathbb{Z}$. So a solution exists iff $d \mid b$.

Assuming $d \mid b$, divide through by $d$: the congruence becomes $(a/d)x \equiv (b/d) \pmod{m/d}$, where now $\gcd(a/d, m/d) = 1$. Since $a/d$ is invertible modulo $m/d$, there is a unique solution $x_0$ modulo $m/d$. Lifting back to $\mathbb{Z}/m\mathbb{Z}$, the solutions modulo $m$ satisfying the original congruence are $x_0, x_0 + m/d, x_0 + 2m/d, \ldots, x_0 + (d-1)m/d$—exactly $d$ residues. $\blacksquare$

The practical algorithm for finding $x_0$ is the **Extended Euclidean Algorithm**, which computes $\gcd(a, m)$ while simultaneously finding integers $s, t$ satisfying $sa + tm = d$. Setting $x_0 = s \cdot (b/d)$ gives an explicit particular solution.

**Worked example.** Solve $18x \equiv 30 \pmod{42}$.

Compute $d = \gcd(18, 42)$. By Euclid: $42 = 2 \cdot 18 + 6$, $18 = 3 \cdot 6 + 0$, so $d = 6$. Since $6 \mid 30$, solutions exist. Divide by 6: $3x \equiv 5 \pmod{7}$. Since $\gcd(3,7) = 1$, the inverse of $3$ mod $7$ is $5$ (because $3 \cdot 5 = 15 = 2 \cdot 7 + 1 \equiv 1$). So $x \equiv 5 \cdot 5 = 25 \equiv 4 \pmod{7}$. The six solutions modulo 42 are $x \equiv 4, 11, 18, 25, 32, 39 \pmod{42}$.

### The Chinese Remainder Theorem: Coprime Moduli

The **Chinese Remainder Theorem (CRT)** is one of the most structurally important theorems in elementary number theory, and its proof illuminates the ring-theoretic decomposition of $\mathbb{Z}/m\mathbb{Z}$ more directly than any amount of abstract description could.

**Theorem (CRT, Classical Form).** Let $m_1, m_2, \ldots, m_k$ be pairwise coprime positive integers—meaning $\gcd(m_i, m_j) = 1$ for all $i \neq j$—and let $M = m_1 m_2 \cdots m_k$. Then for any integers $a_1, a_2, \ldots, a_k$, the simultaneous congruence system

$$x \equiv a_1 \pmod{m_1}, \quad x \equiv a_2 \pmod{m_2}, \quad \ldots, \quad x \equiv a_k \pmod{m_k}$$

has a unique solution modulo $M$.

**Proof.** We construct the solution explicitly using **Garner's method** (or the standard CRT construction). For each $i$, define:

$$M_i = \frac{M}{m_i} = \prod_{j \neq i} m_j.$$

Since $\gcd(M_i, m_i) = 1$ (as the product of integers coprime to $m_i$), the inverse $M_i^{-1} \bmod m_i$ exists. Define the **CRT basis elements**:

$$e_i = M_i \cdot (M_i^{-1} \bmod m_i).$$

Observe that $e_i \equiv 1 \pmod{m_i}$ by construction, and $e_i \equiv 0 \pmod{m_j}$ for $j \neq i$ because $m_j \mid M_i$ whenever $j \neq i$. These basis elements act as idempotent selectors: the combination $e_i$ "activates" only the $i$-th slot. The solution is then:

$$x_0 = \sum_{i=1}^{k} a_i e_i \pmod{M}.$$

To verify: for any fixed index $j$, reducing $x_0$ modulo $m_j$ kills every term except $i = j$, leaving $x_0 \equiv a_j e_j \equiv a_j \cdot 1 = a_j \pmod{m_j}$. For uniqueness: if $x$ and $x'$ are both solutions, then $m_i \mid (x - x')$ for all $i$. Since the $m_i$ are pairwise coprime, $M = \prod m_i$ divides $x - x'$, so $x \equiv x' \pmod{M}$. $\blacksquare$

### Ring Isomorphism and the Structural Meaning of CRT

The CRT is not merely a device for solving simultaneous congruences. It is a statement about ring structure. When $\gcd(m_i, m_j) = 1$ for all $i \neq j$, there is a **ring isomorphism**:

$$\mathbb{Z}/M\mathbb{Z} \cong \mathbb{Z}/m_1\mathbb{Z} \times \mathbb{Z}/m_2\mathbb{Z} \times \cdots \times \mathbb{Z}/m_k\mathbb{Z}.$$

The isomorphism $\Phi: \mathbb{Z}/M\mathbb{Z} \to \prod_i \mathbb{Z}/m_i\mathbb{Z}$ is given by $\Phi([x]_M) = ([x]_{m_1}, [x]_{m_2}, \ldots, [x]_{m_k})$. That this map is well-defined follows because $M \mid (x - x')$ implies $m_i \mid (x - x')$ for each $i$. It is a ring homomorphism because reduction modulo $m_i$ is compatible with addition and multiplication. Surjectivity is exactly the existence clause of CRT. Injectivity follows from the uniqueness clause: $\Phi(x) = \Phi(0)$ means $m_i \mid x$ for all $i$, hence $M \mid x$, so $[x]_M = [0]_M$.

As a consequence of this isomorphism at the group level of units, we recover the multiplicativity of Euler's totient:

$$\phi(M) = \phi(m_1) \phi(m_2) \cdots \phi(m_k),$$

since the group of units on the right decomposes as $(\mathbb{Z}/M\mathbb{Z})^{\times} \cong \prod_i (\mathbb{Z}/m_i\mathbb{Z})^{\times}$.

**Worked example.** Solve the system $x \equiv 2 \pmod{3}$, $x \equiv 3 \pmod{5}$, $x \equiv 2 \pmod{7}$.

Here $M = 3 \cdot 5 \cdot 7 = 105$. Compute $M_1 = 35, M_2 = 21, M_3 = 15$.

Find inverses: $35 \equiv 2 \pmod{3}$, so $35^{-1} \equiv 2 \pmod{3}$ (since $2 \cdot 2 = 4 \equiv 1$). Thus $e_1 = 35 \cdot 2 = 70$. Next, $21 \equiv 1 \pmod{5}$, so $21^{-1} \equiv 1 \pmod{5}$, giving $e_2 = 21 \cdot 1 = 21$. Finally, $15 \equiv 1 \pmod{7}$, so $15^{-1} \equiv 1 \pmod{7}$, giving $e_3 = 15$.

The solution is:

$$x_0 = 2 \cdot 70 + 3 \cdot 21 + 2 \cdot 15 = 140 + 63 + 30 = 233 \equiv 233 - 2 \cdot 105 = 23 \pmod{105}.$$

Verify: $23 = 7 \cdot 3 + 2 \equiv 2 \pmod 3$ ✓; $23 = 4 \cdot 5 + 3 \equiv 3 \pmod 5$ ✓; $23 = 3 \cdot 7 + 2 \equiv 2 \pmod 7$ ✓.

### CRT for Non-Coprime Moduli

The pairwise coprimality hypothesis in classical CRT is essential. When the moduli share common factors, the system $x \equiv a_i \pmod{m_i}$ may have no solution, may have a unique solution modulo $\text{lcm}(m_1, \ldots, m_k)$, or may have multiple solutions, depending on the compatibility conditions. The general theory reduces to the two-modulus case by induction: consider

$$x \equiv a_1 \pmod{m_1}, \quad x \equiv a_2 \pmod{m_2},$$

with $d = \gcd(m_1, m_2)$. A solution exists if and only if $a_1 \equiv a_2 \pmod{d}$. When this **compatibility condition** holds, the solution is unique modulo $\text{lcm}(m_1, m_2) = m_1 m_2 / d$.

**Proof.** The system requires $m_1 \mid x - a_1$ and $m_2 \mid x - a_2$. Write $x = a_1 + m_1 t$. Then $m_2 \mid a_1 + m_1 t - a_2$, so $m_1 t \equiv a_2 - a_1 \pmod{m_2}$. This linear congruence in $t$ has a solution iff $d = \gcd(m_1, m_2)$ divides $a_2 - a_1$, confirming the compatibility condition. Solving for $t$ gives $t \equiv t_0 \pmod{m_2/d}$, so $x = a_1 + m_1 t_0 + m_1(m_2/d) s$ for integer $s$, meaning $x$ is unique modulo $m_1 m_2 / d = \text{lcm}(m_1, m_2)$. $\blacksquare$

For a system with $k > 2$ moduli, one proceeds iteratively: combine the first two congruences into a single congruence modulo $\text{lcm}(m_1, m_2)$ (if compatible), then combine that result with the third, and so on. The process terminates with a solution modulo $\text{lcm}(m_1, \ldots, m_k)$ if and only if all pairwise compatibility conditions hold.

### Structural Diagram: CRT Decomposition and Lifting

The following diagram captures the flow of the CRT construction and the Hensel lifting process described in the next section.

```
Input: system x ≡ aᵢ (mod mᵢ), i = 1..k
                    │
        ┌───────────▼────────────┐
        │  Check pairwise gcd    │
        │  gcd(mᵢ, mⱼ) = 1?     │
        └───────┬────────┬───────┘
                │ YES    │ NO
                │        ▼
                │  Compatibility check:
                │  aᵢ ≡ aⱼ (mod gcd(mᵢ,mⱼ))
                │  for all pairs → merge moduli iteratively
                │
                ▼
    Compute M = m₁·m₂·…·mₖ (or lcm in general)
    Compute Mᵢ = M/mᵢ
    Compute yᵢ = Mᵢ⁻¹ mod mᵢ  (Extended Euclidean)
    Compute eᵢ = Mᵢ · yᵢ
                │
                ▼
    x₀ = Σ aᵢ · eᵢ  (mod M)
                │
                ▼
    Unique solution mod M (or mod lcm in non-coprime case)
                │
                ▼  [If modulus is prime power pⁿ]
        ┌───────▼────────────┐
        │  Hensel Lifting    │
        │  x mod p → x mod  │
        │  p² → … → x mod pⁿ│
        └────────────────────┘
```

### Hensel's Lemma and Lifting Solutions to Prime Powers

The CRT reduces problems about $\mathbb{Z}/M\mathbb{Z}$ to problems about $\mathbb{Z}/p_i^{e_i}\mathbb{Z}$ for each prime power in the factorization of $M$. A fundamental tool for solving congruences modulo prime powers is **Hensel's Lemma**, which provides a constructive lifting procedure: given a solution modulo $p$, lift it—under a non-degeneracy condition—to a solution modulo $p^2$, then $p^3$, and so on.

**Lemma (Hensel's Lemma).** Let $f(x)$ be a polynomial with integer coefficients, $p$ a prime, and $r$ an integer satisfying $f(r) \equiv 0 \pmod{p}$ and $f'(r) \not\equiv 0 \pmod{p}$. Then there exists a unique integer $s$ with $0 \le s < p$ such that $r' = r + sp$ satisfies $f(r') \equiv 0 \pmod{p^2}$.

More generally, if $r_n$ satisfies $f(r_n) \equiv 0 \pmod{p^n}$ and $f'(r_n) \not\equiv 0 \pmod{p}$, then there is a unique $r_{n+1} \equiv r_n \pmod{p^n}$ satisfying $f(r_{n+1}) \equiv 0 \pmod{p^{n+1}}$.

**Proof.** Write $r' = r_n + t p^n$ for some integer $t$. Expand $f(r')$ using Taylor's theorem over $\mathbb{Z}$:

$$f(r_n + t p^n) = f(r_n) + f'(r_n) \cdot t p^n + \sum_{k \ge 2} \frac{f^{(k)}(r_n)}{k!} (t p^n)^k.$$

Since $k \ge 2$ implies $(tp^n)^k$ is divisible by $p^{n+1}$ (as $k \ge 2$ gives $kn \ge n+1$ when $n \ge 1$; more carefully, $p^{2n}$ divides the higher-order terms when $n \ge 1$), we have

$$f(r_n + t p^n) \equiv f(r_n) + f'(r_n) \cdot t p^n \pmod{p^{n+1}}.$$

For $r' = r_n + tp^n$ to satisfy $f(r') \equiv 0 \pmod{p^{n+1}}$, we require

$$f(r_n) + f'(r_n) \cdot t p^n \equiv 0 \pmod{p^{n+1}}.$$

Since $p^n \mid f(r_n)$ by hypothesis, write $f(r_n) = p^n \cdot c$. The equation becomes $c + f'(r_n) \cdot t \equiv 0 \pmod{p}$, i.e.,

$$t \equiv -c \cdot (f'(r_n))^{-1} \pmod{p}.$$

The inverse $(f'(r_n))^{-1} \bmod p$ exists precisely because $f'(r_n) \not\equiv 0 \pmod{p}$. This gives a unique $t \bmod p$, hence a unique $r_{n+1} = r_n + tp^n \bmod p^{n+1}$. $\blacksquare$

The condition $f'(r) \not\equiv 0 \pmod p$ is called the **simple root** or non-degenerate condition. When it fails—when $p \mid f'(r)$—the lifting either has no solution or multiple non-unique lifts, a situation requiring separate analysis.

**Worked example.** Solve $x^2 \equiv 2 \pmod{7^3}$.

**Step 1: Solve modulo 7.** We need $x^2 \equiv 2 \pmod 7$. Check: $3^2 = 9 \equiv 2 \pmod 7$. So $r_1 = 3$ is a solution. Verify $f'(x) = 2x$; $f'(3) = 6 \not\equiv 0 \pmod 7$. The non-degeneracy condition holds.

**Step 2: Lift to modulo $7^2 = 49$.** Write $r_2 = 3 + 7t$. Compute $c = f(r_1)/p = (9 - 2)/7 = 1$. Then $t \equiv -c \cdot (f'(r_1))^{-1} \equiv -1 \cdot 6^{-1} \pmod 7$. Since $6 \equiv -1 \pmod 7$, $6^{-1} \equiv -1 \equiv 6 \pmod 7$. So $t \equiv -1 \cdot 6 = -6 \equiv 1 \pmod 7$. Thus $r_2 = 3 + 7 \cdot 1 = 10$.

Verify: $10^2 = 100 = 2 \cdot 49 + 2$, so $100 \equiv 2 \pmod{49}$ ✓.

**Step 3: Lift to modulo $7^3 = 343$.** Write $r_3 = 10 + 49s$. Compute $c = (100 - 2)/49 = 2$. Then $s \equiv -2 \cdot (f'(10))^{-1} \equiv -2 \cdot (20)^{-1} \pmod 7$. Now $20 \equiv 6 \pmod 7$, and $6^{-1} \equiv 6 \pmod 7$ as above. So $s \equiv -2 \cdot 6 = -12 \equiv -12 + 14 = 2 \pmod 7$. Thus $r_3 = 10 + 49 \cdot 2 = 108$.

Verify: $108^2 = 11664$. We need $11664 - 2 = 11662$ to be divisible by $343$. Indeed, $11662 / 343 = 33.99... $, so check: $343 \cdot 34 = 11662$. Thus $108^2 \equiv 2 \pmod{343}$ ✓.

---

## 3. High-Performance Optimization & Failure Modes

### Algorithmic Complexity of CRT Reconstruction

The standard CRT construction requires, for each $i$, computing $M_i = M / m_i$ and then the modular inverse $M_i^{-1} \bmod m_i$ via the Extended Euclidean Algorithm. The Extended Euclidean Algorithm on inputs $a, b$ with $b \le a$ runs in $O(\log \min(a,b))$ divisions, each on integers of size $O(\log a)$ bits, giving a total bit complexity of $O(\log^2 a)$ using schoolbook arithmetic. With $k$ moduli and $M \le m^k$ for $m = \max m_i$, the inverse computations cost $O(k \log^2 m)$ bit operations in total, which is essentially linear in the total bit-length of the input. The final summation $\sum a_i e_i \bmod M$ involves numbers of size $O(k \log m)$ bits and costs $O(k^2 \log^2 m)$ bit operations with schoolbook multiplication.

For large-scale applications—multi-precision integer arithmetic, symbolic computation—**Garner's algorithm** avoids accumulating the large number $M$ by expressing the solution in a **mixed-radix representation**. Rather than computing $x_0 = \sum a_i e_i \bmod M$ directly, Garner's method expresses the solution as

$$x_0 = c_1 + c_2 m_1 + c_3 m_1 m_2 + \cdots + c_k m_1 m_2 \cdots m_{k-1},$$

where each $c_i$ is computed by a recursive formula involving only arithmetic modulo the small moduli $m_i$ and not the product $M$. This keeps all intermediate computations bounded by $M$ in magnitude but avoids the $O(k)$-factor blowup in the number of digits during intermediate summation.

The computational payoff of CRT in practice appears most vividly in **multi-precision integer multiplication via the Number Theoretic Transform (NTT)**. To multiply two large integers $a$ and $b$, one reduces them modulo several small NTT-friendly primes $p_1, \ldots, p_k$ (primes of the form $c \cdot 2^n + 1$ admitting fast FFT-based convolution), performs the multiplications modulo each $p_i$ using polynomial multiplication in $\mathbb{F}_{p_i}[x]$, and then reconstructs the true product using CRT. The correctness of this approach requires $M = \prod p_i > 2 \cdot \max(a \cdot b)$ to ensure no wraparound occurs—a size constraint that dictates the choice and number of primes.

### Failure Modes and Degenerate Cases

**Incompatible systems.** The most common failure in applying CRT to non-coprime moduli is a violated compatibility condition. The system $x \equiv 1 \pmod 4$, $x \equiv 2 \pmod 6$ has no solution: the first requires $x$ odd, the second requires $x$ even (since $x \equiv 2 \pmod 6$ implies $x = 2, 8, 14, \ldots$, all even, while $x \equiv 1 \pmod 4$ requires $x = 1, 5, 9, 13, \ldots$, all odd). Formally, $\gcd(4, 6) = 2$ and $1 \not\equiv 2 \pmod 2$. Any algorithm must check compatibility before attempting to construct a solution.

**Degenerate Hensel lifting: the case $p \mid f'(r)$.** When the derivative condition in Hensel's lemma fails, the quadratic term in the Taylor expansion no longer dominates, and the analysis bifurcates. If $p \mid f'(r)$ and $p \nmid f(r)/p^n$—i.e., the coefficient $c$ is not divisible by $p$—then the congruence $c + f'(r_n) t \equiv 0 \pmod p$ reduces to $c \equiv 0 \pmod p$, which is false, and the lift has **no solution**. If instead $p \mid f'(r)$ and $p \mid c$, then every value of $t \in \{0, 1, \ldots, p-1\}$ yields a valid lift, giving **$p$ distinct solutions** modulo $p^{n+1}$. This non-uniqueness is the signature of a repeated root over $\mathbb{F}_p$.

A concrete instance: $f(x) = x^2 - p$ modulo $p^2$. We have $f(0) = -p \equiv 0 \pmod p$ but $f'(0) = 0 \equiv 0 \pmod p$, so the standard lemma does not apply. Indeed, the solutions of $x^2 \equiv p \pmod{p^2}$ require a separate analysis (and in fact $x^2 \equiv p \pmod{p^2}$ has no solution for $p > 2$, since $v_p(x^2) \in \{0, 2, 4, \ldots\}$ while $v_p(p) = 1$, where $v_p$ denotes the $p$-adic valuation).

**Overflow in direct CRT reconstruction.** In computational implementations working with fixed-width integers, the intermediate quantity $a_i \cdot M_i$ can far exceed the word size even when the final answer $x_0$ does not. Garner's algorithm explicitly mitigates this, but naive CRT implementations that multiply before reducing can silently overflow. The correct discipline is to reduce modulo $M$ at each step of the summation, not after.

**Modular inverse computation failures.** The Extended Euclidean Algorithm assumes $\gcd(M_i, m_i) = 1$. If the moduli are not pairwise coprime and this coprimality was assumed without verification, the inverse computation fails (returns $\gcd \neq 1$). Robust implementations use the full non-coprime CRT pipeline—merging via $\text{lcm}$ and checking compatibility—rather than the coprime shortcut, unless coprimality has been externally guaranteed.

### The $p$-adic Perspective and Projective Limits

The Hensel lifting process reveals a structure far deeper than a computational trick. As $n \to \infty$, the compatible sequence of solutions $(r_1 \bmod p, r_2 \bmod p^2, \ldots)$ defines an element of the **$p$-adic integers** $\mathbb{Z}_p$. Formally, $\mathbb{Z}_p$ is the inverse limit of the system:

$$\mathbb{Z}_p = \varprojlim_n \mathbb{Z}/p^n\mathbb{Z},$$

where the transition maps are the natural reduction homomorphisms $\mathbb{Z}/p^{n+1}\mathbb{Z} \to \mathbb{Z}/p^n\mathbb{Z}$. An element of $\mathbb{Z}_p$ is a coherent sequence $(a_n)_{n \ge 1}$ with $a_n \in \mathbb{Z}/p^n\mathbb{Z}$ and $a_n \equiv a_{n+1} \pmod{p^n}$. Hensel's lemma, in this language, is the statement that a simple root of $f$ over $\mathbb{F}_p$ lifts to a root in $\mathbb{Z}_p$, and this root is unique. The $p$-adic integers form a complete, valued ring carrying a topology where the ideals $p^n \mathbb{Z}_p$ constitute a neighborhood basis of zero, entirely analogous to how $\mathbb{R}$ is the completion of $\mathbb{Q}$ with respect to the Archimedean absolute value.

Understood this way, every theorem in this lesson—congruences, linear Diophantine solvability, the CRT isomorphism, Hensel lifting—is a finite truncation of a theory living naturally in $\mathbb{Z}_p$. The ring isomorphism

$$\mathbb{Z}/p^n\mathbb{Z} \cong \mathbb{Z}_p / p^n \mathbb{Z}_p$$

shows that computations modulo $p^n$ are computations in a quotient of the $p$-adic integers, and the exactness of the CRT decomposition $\mathbb{Z}/M\mathbb{Z} \cong \prod_i \mathbb{Z}/p_i^{e_i}\mathbb{Z}$ reflects, at the level of completions, the product decomposition $\hat{\mathbb{Z}} \cong \prod_p \mathbb{Z}_p$ of the profinite completion of $\mathbb{Z}$. These are not distant generalizations—they are the natural home of the arithmetic we have been doing from the first line of this lesson, and understanding them as such makes the structure of modular arithmetic not just a toolkit but a coherent and inevitable mathematical world.
