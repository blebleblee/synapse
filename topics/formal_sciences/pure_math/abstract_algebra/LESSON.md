# In-Depth Technical Lesson: Sylow Theorems, Factorization Domains & Galois Theory

## 1. Group Actions & The Sylow Theorems

### Group Actions on Sets
Let $G$ be a group and $X$ a non-empty set. A **group action** is a function $\cdot: G \times X \to X$ satisfying:
1. **Identity:** $e \cdot x = x$ for all $x \in X$.
2. **Compatibility:** $(g_1 g_2) \cdot x = g_1 \cdot (g_2 \cdot x)$ for all $g_1, g_2 \in G, x \in X$.

For any element $x \in X$:
* **The Orbit of $x$:** $\mathcal{O}_x = G \cdot x = \{ g \cdot x \mid g \in G \} \subseteq X$.
* **The Stabilizer of $x$:** $G_x = \text{Stab}_G(x) = \{ g \in G \mid g \cdot x = x \} \le G$.

### The Orbit-Stabilizer Theorem
**Theorem:** *Let $G$ be a finite group acting on a set $X$. For any $x \in X$, there is a natural bijection between the orbit $\mathcal{O}_x$ and the left cosets of the stabilizer $G / G_x$. Consequently:*

$$|G| = |\mathcal{O}_x| \cdot |G_x| = [G : G_x] \cdot |G_x|$$

### The Class Equation
When a group $G$ acts on itself by **conjugation** ($g \cdot x = g x g^{-1}$):
* The stabilizer of $x$ is the centralizer: $C_G(x) = \{ g \in G \mid gx = xg \}$.
* The fixed points of the action form the **Center** of the group: $Z(G) = \{ z \in G \mid zg = gz \; \forall g \in G \}$.
Partitioning $G$ into conjugacy class orbits yields the **Class Equation**:

$$|G| = |Z(G)| + \sum_{i=1}^k [G : C_G(x_i)]$$

Where $x_1, \dots, x_k$ are representatives of non-central conjugacy classes.

---

### The Three Sylow Theorems (Ludwig Sylow, 1872)
Let $G$ be a finite group of order $|G| = p^k m$, where $p$ is prime, $k \ge 1$, and $\gcd(p, m) = 1$. A subgroup $P \le G$ of order $|P| = p^k$ is called a **Sylow $p$-Subgroup**.

```
The Sylow Subgroup Invariants
=============================

1. Existence:
   A subgroup of prime-power order p^k always exists.

2. Conjugacy:
   Any two Sylow p-subgroups P_1, P_2 are conjugate:
   \exists g \in G such that P_2 = g P_1 g^{-1}.

3. Number of Subgroups (n_p):
   The number of distinct Sylow p-subgroups satisfies:
     n_p \equiv 1 (mod p)
     n_p divides m
```

* **Sylow's First Theorem (Existence):** $G$ contains at least one Sylow $p$-subgroup of order $p^k$. More generally, for every $1 \le j \le k$, $G$ contains a subgroup of order $p^j$, and every subgroup of order $p^j$ is normal in some subgroup of order $p^{j+1}$.
* **Sylow's Second Theorem (Conjugacy):** If $P_1$ and $P_2$ are Sylow $p$-subgroups of $G$, then they are conjugate in $G$: there exists $g \in G$ such that $P_2 = g P_1 g^{-1}$. Furthermore, any $p$-subgroup of $G$ is contained within some Sylow $p$-subgroup.
* **Sylow's Third Theorem (Divisibility & Counting):** Let $n_p$ denote the number of distinct Sylow $p$-subgroups in $G$. Then:
  $$n_p \equiv 1 \pmod p \quad \text{and} \quad n_p \mid m$$
* **Crucial Classification Corollary:** If $n_p = 1$, then the unique Sylow $p$-subgroup $P$ is invariant under all inner automorphisms ($gPg^{-1} = P$). Thus, **$P$ is a normal subgroup ($P \triangleleft G$)**, proving that $G$ is not simple.

---

## 2. Ring Theory, Ideals & Factorization Domains

### Ideals: Prime vs. Maximal
Let $R$ be a commutative ring with unity $1 \ne 0$. An ideal $I \subseteq R$ is a subring absorbing ring multiplication: $\forall r \in R, x \in I \implies rx \in I$.

```
Quotient Ring Characterization
==============================

   I is a Maximal Ideal  <===>  R / I is a Field
            |                            |
            v (Every field is an domain) v
   I is a Prime Ideal    <===>  R / I is an Integral Domain
```

1. **Prime Ideal:** A proper ideal $P \subsetneq R$ is prime if for all $a, b \in R$:
   $$ab \in P \implies a \in P \quad \text{or} \quad b \in P$$
   *Theorem:* $P$ is prime if and only if the quotient ring $R/P$ is an **Integral Domain** (has no zero divisors).
2. **Maximal Ideal:** A proper ideal $M \subsetneq R$ is maximal if no proper ideal strictly contains $M$:
   $$M \subseteq I \subseteq R \implies I = M \quad \text{or} \quad I = R$$
   *Theorem:* $M$ is maximal if and only if the quotient ring $R/M$ is a **Field**.
3. **The Implication:** Since every field is an integral domain, **every maximal ideal is automatically a prime ideal**. (The converse holds in PIDs, but not in general rings—e.g., $\langle x \rangle \subset \mathbb{Z}[x]$ is prime but not maximal since $\mathbb{Z}[x]/\langle x \rangle \cong \mathbb{Z}$, which is a domain but not a field).

---

### The Strict Hierarchy of Factorization Domains

```
   Fields
     |
     v (Strict inclusion: \mathbb{Z} is a Euclidean Domain but not a field)
   Euclidean Domains (ED)
     |
     v (Strict inclusion: \mathbb{Z}[(1 + \sqrt{-19})/2] is a PID but not an ED)
   Principal Ideal Domains (PID)
     |
     v (Strict inclusion: \mathbb{Z}[x] and \mathbb{R}[x, y] are UFDs but not PIDs)
   Unique Factorization Domains (UFD)
     |
     v (Strict inclusion: \mathbb{Z}[\sqrt{-5}] is an Integral Domain but not a UFD)
   Integral Domains
```

1. **Euclidean Domain (ED):** An integral domain equipped with a Euclidean norm function $d: R \setminus \{0\} \to \mathbb{N}_0$ satisfying the division algorithm: for all $a, b \in R$ with $b \ne 0$, there exist $q, r \in R$ such that:
   $$a = bq + r \quad \text{with} \quad r = 0 \;\text{ or }\; d(r) < d(b)$$
   *Examples:* $\mathbb{Z}$ with $d(n) = |n|$; Polynomial ring $F[x]$ over field $F$ with $d(p) = \deg(p)$; Gaussian integers $\mathbb{Z}[i]$ with $d(a+bi) = a^2 + b^2$.
2. **Principal Ideal Domain (PID):** An integral domain where **every ideal is principal** (generated by a single element): $\forall I \subseteq R, I = \langle a \rangle$.
   *Theorem:* Every Euclidean Domain is a PID. (Proof: In an ideal $I \ne \{0\}$, pick non-zero $b \in I$ minimizing $d(b)$. For any $a \in I$, divide $a = bq + r$. Since $r = a - bq \in I$ and $d(r) < d(b)$, minimality forces $r = 0$, so $a = bq \in \langle b \rangle$, proving $I = \langle b \rangle$).
3. **Unique Factorization Domain (UFD):** An integral domain where every non-zero, non-unit element factors uniquely (up to associates and permutation) into a product of irreducible elements.
   *Theorem:* Every PID is a UFD.
   *Counter-example (UFD that is NOT a PID):* $\mathbb{Z}[x]$ is a UFD (by Gauss's Lemma), but the ideal $\langle 2, x \rangle$ cannot be generated by any single polynomial, so $\mathbb{Z}[x]$ is not a PID.
   *Counter-example (Domain that is NOT a UFD):* In $\mathbb{Z}[\sqrt{-5}]$, the element $6$ has two non-associate irreducible factorizations:
   $$6 = 2 \times 3 = (1 + \sqrt{-5})(1 - \sqrt{-5})$$
   Thus unique factorization fails in $\mathbb{Z}[\sqrt{-5}]$.

---

## 3. Field Extensions & Galois Theory

Let $F \subseteq E$ be a field extension. $E$ is naturally a vector space over the base field $F$. The **degree** of the extension is:

$$[E : F] = \dim_F(E)$$

### The Tower Law
If $F \subseteq K \subseteq E$ are field extensions, then:

$$[E : F] = [E : K] \cdot [K : F]$$

### Algebraic vs. Transcendental Elements
An element $\alpha \in E$ is **algebraic** over $F$ if there exists a non-zero polynomial $p(x) \in F[x]$ such that $p(\alpha) = 0$. The unique monic irreducible polynomial of minimal degree annihilating $\alpha$ is its **minimal polynomial** $m_{\alpha, F}(x)$. The simple extension satisfies:

$$F(\alpha) \cong F[x] / \langle m_{\alpha, F}(x) \rangle \quad \text{and} \quad [F(\alpha) : F] = \deg(m_{\alpha, F})$$

---

### The Galois Correspondence
An extension $E/F$ is a **Galois Extension** if it is both:
1. **Normal:** $E$ is the splitting field of a family of polynomials in $F[x]$ (every irreducible polynomial in $F[x]$ with one root in $E$ splits completely into linear factors in $E[x]$).
2. **Separable:** Every algebraic element has a minimal polynomial with distinct roots in its splitting field (no repeated roots; always true over fields of characteristic $0$, such as $\mathbb{Q}$).

The **Galois Group** of an extension $E/F$ is the group of field automorphisms of $E$ fixing the base field $F$ pointwise:

$$\text{Gal}(E/F) = \text{Aut}_F(E) = \{ \sigma: E \xrightarrow{\sim} E \mid \sigma(a) = a \; \forall a \in F \}$$

For a finite Galois extension, $|\text{Gal}(E/F)| = [E : F]$.

```
The Fundamental Theorem of Galois Theory
========================================

    Intermediate Fields (K)                Subgroups of Gal(E/F) (H)
       E (Splitting Field)  <===========>       {id} (Trivial Subgroup)
             |                                    |
             v                                    ^
             K              <===========>         H = Aut_K(E)
             |                                    |
             v                                    ^
       F (Base Field)       <===========>       Gal(E/F) (Full Galois Group)

  Order-Reversing Bijection:
    K = E^H = { x \in E | \sigma(x) = x  \forall \sigma \in H }
    [E : K] = |H|
    [K : F] = [Gal(E/F) : H]
    K / F is Normal  <===>  H \triangleleft Gal(E/F)
    If K / F is Normal, then Gal(K/F) \cong Gal(E/F) / H
```

---

## 4. The Insolvability of the General Quintic (Abel-Ruffini Theorem)

A polynomial $f(x) \in F[x]$ is **solvable by radicals** if its roots can be expressed through a finite sequence of field operations ($+, -, \times, \div$) and $n$-th root extractions ($\sqrt[n]{\cdot}$).

### The Galois Criterion for Solvability
**Theorem (Évariste Galois, 1832):** *A polynomial $f(x) \in F[x]$ is solvable by radicals if and only if its Galois group $\text{Gal}(E/F)$ over $F$ is a **Solvable Group**.*

A finite group $G$ is **solvable** if it possesses a subnormal series:

$$\{e\} = G_0 \triangleleft G_1 \triangleleft G_2 \triangleleft \dots \triangleleft G_k = G$$

Such that every quotient factor $G_{i+1} / G_i$ is an **Abelian Group**.

### The Breakdown for $n \ge 5$
* For quadratic ($n=2$), cubic ($n=3$), and quartic ($n=4$) polynomials, the symmetric groups $S_2, S_3, S_4$ are solvable:
  - $S_3 \triangleright A_3 \triangleright \{e\}$ (quotients: $\mathbb{Z}/2\mathbb{Z}, \mathbb{Z}/3\mathbb{Z}$—both abelian).
  - $S_4 \triangleright A_4 \triangleright V_4 \triangleright \{e\}$ (quotients: $\mathbb{Z}/2\mathbb{Z}, \mathbb{Z}/3\mathbb{Z}, \mathbb{Z}/2\mathbb{Z} \times \mathbb{Z}/2\mathbb{Z}$—all abelian).
* For $n = 5$: The Symmetric Group $S_5$ has order $|S_5| = 120$. Its only non-trivial proper normal subgroup is the **Alternating Group $A_5$** ($|A_5| = 60$).
* **Crucial Invariant:** **$A_5$ is a Simple Group** (the smallest non-abelian simple group). It has no non-trivial proper normal subgroups.
* Therefore, the only possible normal series for $S_5$ is:
  $$\{e\} \triangleleft A_5 \triangleleft S_5$$
  While $S_5 / A_5 \cong \mathbb{Z}/2\mathbb{Z}$ is abelian, the quotient factor $A_5 / \{e\} \cong A_5$ is **non-abelian**.
* **Conclusion:** $S_5$ is **not solvable**. Because there exist degree-5 polynomials over $\mathbb{Q}$ (such as $f(x) = x^5 - 4x + 2$) whose Galois group is precisely $S_5$, **no general algebraic formula by radicals exists for quintic equations.** $\blacksquare$

---

## 5. Key Takeaways

1. **Groups Quantify Invariance:** Group actions capture symmetry through the Orbit-Stabilizer theorem, connecting structural cardinality to centralizer subgroups.
2. **Sylow Invariants Determine Group Structure:** The three Sylow theorems allow classifying finite groups and proving the existence of normal subgroups purely from prime factorizations of group orders.
3. **Ideals Govern Ring Factorization:** Prime ideals produce integral domains, maximal ideals produce fields, and the Euclidean division algorithm guarantees principal ideal unique factorization.
4. **Galois Theory Translates Fields to Groups:** The Fundamental Theorem of Galois Theory establishes an exact bridge turning field extension arithmetic into permutation group lattice analysis.
