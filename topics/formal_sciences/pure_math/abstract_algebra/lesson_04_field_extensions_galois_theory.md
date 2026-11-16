# Lesson 4: Field Extensions, Galois Theory

## 1. First-Principles Intuition & Invariants

The theory of field extensions and Galois theory arose from one of the most consequential dead ends in the history of mathematics: the search for a general formula expressing the roots of a polynomial of arbitrary degree in terms of its coefficients, using only the four arithmetic operations and the extraction of $n$-th roots. For degrees one through four, such formulas were known by the mid-sixteenth century. The cubic was resolved by del Ferro and Tartaglia, the quartic by Ferrari, and both were published by Cardano in 1545. Then, for nearly three centuries, the quintic resisted every attempt. Mathematicians tried increasingly elaborate substitutions, resolvents, and transformations, assuming that the formula simply had not yet been found. The breakthrough came not from a more clever manipulation but from a complete reframing of the question. Ruffini and Abel independently proved that no such formula exists for the general quintic. Then Galois, in the few years before his death in 1832 at the age of twenty, constructed the theory that explained *why*.

Galois recognized that every polynomial carries an associated finite group, now called its Galois group, and that the solvability of the polynomial by radicals is equivalent to a purely group-theoretic property of this group: its solvability in the sense of group theory. This insight transplanted a problem about equations into the domain of symmetry, and it required the development of field extensions as the algebraic infrastructure in which the roots of a polynomial live.

A **field extension** is a pair of fields $F \subseteq E$, where $E$ is a field containing $F$ as a subfield. We write $E/F$ and call $F$ the **base field** and $E$ the **extension field**. The simplest way to build an extension is to adjoin an element: given a field $F$ and an element $\alpha$ in some larger field, $F(\alpha)$ denotes the smallest field containing $F$ and $\alpha$. If $\alpha$ is a root of a nonzero polynomial $f(x) \in F[x]$, we say $\alpha$ is **algebraic** over $F$; otherwise $\alpha$ is **transcendental** over $F$. The distinction is sharp and has deep structural consequences.

When $\alpha$ is algebraic over $F$, there exists a unique monic irreducible polynomial $m_\alpha(x) \in F[x]$ of minimal degree such that $m_\alpha(\alpha) = 0$. This is the **minimal polynomial** of $\alpha$ over $F$. Its existence and uniqueness follow from a clean algebraic argument. Consider the evaluation homomorphism $\varphi_\alpha: F[x] \to E$ defined by $\varphi_\alpha(f) = f(\alpha)$. The kernel $\ker \varphi_\alpha = \{f \in F[x] : f(\alpha) = 0\}$ is a nonzero ideal (since $\alpha$ is algebraic), and $F[x]$ is a principal ideal domain. Therefore $\ker \varphi_\alpha = (m_\alpha(x))$ for a unique monic generator $m_\alpha(x)$. This polynomial is irreducible: if $m_\alpha = g \cdot h$ with both factors of positive degree, then $g(\alpha) h(\alpha) = 0$ in $E$, and since $E$ is a field (hence an integral domain), one of $g(\alpha)$ or $h(\alpha)$ is zero, contradicting the minimality of $\deg m_\alpha$. By the First Isomorphism Theorem for rings, we obtain $F[x]/(m_\alpha(x)) \cong F(\alpha)$, and since $m_\alpha$ is irreducible, the quotient is a field, confirming that $F(\alpha)$ is indeed a field.

The **degree** of the extension $F(\alpha)/F$, written $[F(\alpha) : F]$, equals $\deg m_\alpha$. More generally, for any field extension $E/F$, the degree $[E : F]$ is the dimension of $E$ as a vector space over $F$. When this dimension is finite, we call $E/F$ a **finite extension**; every finite extension is algebraic, though the converse requires the extension to be finitely generated.

The Tower Law is the foundational counting identity for nested extensions. If $F \subseteq K \subseteq E$ are fields, then $[E : F] = [E : K][K : F]$. To prove this, let $\{\alpha_1, \ldots, \alpha_m\}$ be a basis for $K$ over $F$ and $\{\beta_1, \ldots, \beta_n\}$ be a basis for $E$ over $K$. We claim $\{\alpha_i \beta_j : 1 \leq i \leq m,\ 1 \leq j \leq n\}$ is a basis for $E$ over $F$. For spanning: any $\gamma \in E$ can be written $\gamma = \sum_j c_j \beta_j$ with $c_j \in K$, and each $c_j = \sum_i d_{ij} \alpha_i$ with $d_{ij} \in F$, giving $\gamma = \sum_{i,j} d_{ij} \alpha_i \beta_j$. For linear independence: if $\sum_{i,j} d_{ij} \alpha_i \beta_j = 0$ with $d_{ij} \in F$, regroup as $\sum_j \left(\sum_i d_{ij} \alpha_i\right) \beta_j = 0$. Since the $\beta_j$ are linearly independent over $K$, each coefficient $\sum_i d_{ij} \alpha_i = 0$. Since the $\alpha_i$ are linearly independent over $F$, each $d_{ij} = 0$. This gives $\dim_F E = mn$, completing the proof.

The Tower Law immediately yields a powerful consequence: if $[E : F]$ is finite and $\alpha \in E$ is algebraic over $F$, then $[F(\alpha) : F]$ divides $[E : F]$, since $[E : F] = [E : F(\alpha)][F(\alpha) : F]$. In particular, if $[E : F] = p$ is prime, then there are no intermediate fields between $F$ and $E$, because any intermediate field $K$ would give $[K : F] \mid p$, forcing $[K : F] = 1$ or $p$.

The concept of a minimal polynomial is the algebraic "DNA" of an element. It encodes every polynomial relation satisfied by $\alpha$ over $F$, since $f(\alpha) = 0$ if and only if $m_\alpha \mid f$ in $F[x]$. The degree of $m_\alpha$ measures the "cost" of adjoining $\alpha$ to $F$. When we adjoin multiple elements, the Tower Law tells us how these costs compose. This framework is the foundation on which the entire edifice of Galois theory is built.

## 2. Core Architecture & Mechanics

### Splitting Fields

Given a polynomial $f(x) \in F[x]$, we want the smallest extension of $F$ in which $f$ completely factors into linear factors. This is the **splitting field** of $f$ over $F$, and it is the central object of Galois theory.

**Theorem (Existence of Splitting Fields).** Let $F$ be a field and $f(x) \in F[x]$ a non-constant polynomial of degree $n$. There exists an extension $E$ of $F$ with $[E : F] \leq n!$ such that $f$ splits into linear factors in $E[x]$.

**Proof.** We proceed by induction on $\deg f$. If $\deg f = 1$, then $f$ already splits over $F$, so $E = F$ suffices. For $\deg f = n > 1$, let $p(x)$ be an irreducible factor of $f$ in $F[x]$. Form the quotient ring $F_1 = F[x]/(p(x))$, which is a field because $p$ is irreducible. The class $\bar{x}$ of $x$ in $F_1$ is a root of $p$, hence of $f$. So $f(x) = (x - \bar{x})g(x)$ in $F_1[x]$, where $\deg g = n - 1$. By the inductive hypothesis, $g$ has a splitting field $E$ over $F_1$ with $[E : F_1] \leq (n-1)!$. Then $E$ is a splitting field for $f$ over $F$, and $[E : F] = [E : F_1][F_1 : F] \leq (n-1)! \cdot n = n!$. $\square$

The bound $n!$ is sharp: the general polynomial of degree $n$ has a splitting field of degree exactly $n!$ over its coefficient field, with Galois group $S_n$.

**Theorem (Uniqueness of Splitting Fields).** Let $\sigma: F \to F'$ be a field isomorphism, and let $f \in F[x]$ with $f' = \sigma(f) \in F'[x]$. If $E$ is a splitting field of $f$ over $F$ and $E'$ is a splitting field of $f'$ over $F'$, then $\sigma$ extends to an isomorphism $\bar{\sigma}: E \to E'$.

**Proof.** We use induction on $[E : F]$. If $[E : F] = 1$, then $f$ splits over $F$, so $f'$ splits over $F'$, and $\sigma$ itself is the extension. For $[E : F] > 1$, choose an irreducible factor $p(x)$ of $f(x)$ with $\deg p > 1$, and let $f' = \sigma(f)$, $p' = \sigma(p)$. Pick a root $\alpha \in E$ of $p$ and a root $\alpha' \in E'$ of $p'$. By the isomorphism extension lemma, $\sigma$ extends to an isomorphism $\sigma_1: F(\alpha) \to F'(\alpha')$ sending $\alpha \mapsto \alpha'$. Over $F(\alpha)$, $f$ has the factorization $f(x) = (x - \alpha)g(x)$, and correspondingly $f'(x) = (x - \alpha')g'(x)$ over $F'(\alpha')$. Now $E$ is a splitting field of $g$ over $F(\alpha)$, and $E'$ is a splitting field of $g'$ over $F'(\alpha')$, with $[E : F(\alpha)] < [E : F]$. By the inductive hypothesis, $\sigma_1$ extends to an isomorphism $\bar{\sigma}: E \to E'$. $\square$

This uniqueness theorem is stronger than it appears: it says that the splitting field is unique *up to isomorphism*, and moreover that any isomorphism of the base fields extends to an isomorphism of the splitting fields. This extension property is the seed from which the entire Galois correspondence grows.

### Separable and Inseparable Extensions

A polynomial is **separable** if it has no repeated roots in its splitting field. An algebraic element $\alpha$ over $F$ is separable over $F$ if its minimal polynomial is separable. An extension $E/F$ is separable if every element of $E$ is separable over $F$.

The formal derivative provides a clean criterion. Given $f(x) = \sum a_i x^i \in F[x]$, the **formal derivative** is $f'(x) = \sum i a_i x^{i-1}$, where $i$ denotes the image of the integer $i$ in $F$.

**Theorem.** Let $f \in F[x]$ be irreducible. Then $f$ is separable if and only if $f' \neq 0$.

**Proof.** Suppose $f' \neq 0$. Since $\deg f' < \deg f$ and $f$ is irreducible, $\gcd(f, f') = 1$ (any common factor would be a non-constant factor of $f$, contradicting irreducibility, since $f' \neq 0$ ensures $\gcd \neq f$). If $\alpha$ were a repeated root of $f$ in its splitting field, then $(x - \alpha)^2 \mid f(x)$, and differentiating gives $(x - \alpha) \mid f'(x)$, so $(x - \alpha) \mid \gcd(f, f') = 1$, a contradiction. Conversely, if $f' = 0$, write $f(x) = \sum a_i x^i$. Then $f'(x) = \sum i a_i x^{i-1} = 0$ means $i \cdot a_i = 0$ in $F$ for all $i$. This forces $a_i = 0$ whenever $\text{char}(F) \nmid i$. If $\text{char}(F) = 0$, this means all $a_i = 0$ for $i \geq 1$, so $f$ is constant, contradicting irreducibility. If $\text{char}(F) = p > 0$, then $a_i = 0$ for $p \nmid i$, so $f(x) = \sum a_{pk} x^{pk} = g(x^p)$ for some $g \in F[x]$. If $\alpha$ is a root of $f$, then $g(\alpha^p) = 0$. Let $\beta$ be a root of $g$ so that $\alpha^p = \beta$ (in the splitting field). Then $f(x) = g(x^p) = \prod (x^p - \beta_j) = \prod (x - \beta_j^{1/p})^p$ in the splitting field (using the Frobenius endomorphism: $(x - \gamma)^p = x^p - \gamma^p$ in characteristic $p$). Every root has multiplicity at least $p$, so $f$ is inseparable. $\square$

This theorem has an immediate corollary: over a field of characteristic zero, every irreducible polynomial is separable, and hence every algebraic extension is separable. The situation in characteristic $p$ is more subtle. A field $F$ of characteristic $p$ is called **perfect** if every irreducible polynomial over $F$ is separable. Finite fields are perfect (as we shall see), and so are fields of characteristic zero. An imperfect field must be infinite of characteristic $p$. The standard example is $F = \mathbb{F}_p(t)$, the field of rational functions over $\mathbb{F}_p$: the polynomial $x^p - t$ is irreducible over $F$ but has derivative zero, so it is inseparable.

### The Galois Group

Let $E/F$ be a field extension. The **Galois group** $\text{Gal}(E/F)$ is the group of all $F$-automorphisms of $E$, that is, field automorphisms $\sigma: E \to E$ that fix every element of $F$ pointwise. Under composition, these form a group. The key intuition is that $\text{Gal}(E/F)$ measures the symmetries of the extension: automorphisms that permute the "new" elements of $E$ while keeping the base field $F$ fixed.

For a finite extension $E/F$, we always have $|\text{Gal}(E/F)| \leq [E : F]$. The extension is called **Galois** when equality holds. Equivalently, $E/F$ is Galois if and only if $E$ is the splitting field of a separable polynomial over $F$, which is equivalent to $E/F$ being both **normal** (every irreducible polynomial over $F$ that has a root in $E$ splits completely in $E$) and **separable**.

The equality $|\text{Gal}(E/F)| = [E : F]$ for a Galois extension follows from a counting argument using the isomorphism extension property of splitting fields. If $E$ is the splitting field of a separable $f \in F[x]$ with roots $\alpha_1, \ldots, \alpha_n$, then any $\sigma \in \text{Gal}(E/F)$ permutes these roots, and $\sigma$ is completely determined by where it sends each $\alpha_i$. The number of such permutations is bounded by $n!$, but more precisely, by extending automorphisms one root at a time and using separability (distinct roots give distinct choices), one shows the count is exactly $[E : F]$.

### The Fundamental Theorem of Galois Theory

The Fundamental Theorem of Galois Theory (FTGT) establishes a bijection between intermediate fields of a Galois extension and subgroups of its Galois group. This is the dictionary that translates field-theoretic questions into group-theoretic ones.

**Theorem (Fundamental Theorem of Galois Theory).** Let $E/F$ be a Galois extension, and let $G = \text{Gal}(E/F)$. Define two maps:

$$\Phi: \{K : F \subseteq K \subseteq E\} \to \{H : H \leq G\}, \quad \Phi(K) = \text{Gal}(E/K)$$

$$\Psi: \{H : H \leq G\} \to \{K : F \subseteq K \subseteq E\}, \quad \Psi(H) = E^H = \{\alpha \in E : \sigma(\alpha) = \alpha \text{ for all } \sigma \in H\}$$

Then $\Phi$ and $\Psi$ are inclusion-reversing bijections, inverse to each other. Moreover:

1. $[E : K] = |\text{Gal}(E/K)|$ and $[K : F] = [G : \text{Gal}(E/K)]$ for every intermediate $K$.
2. $K/F$ is Galois if and only if $\text{Gal}(E/K) \trianglelefteq G$, and in this case $\text{Gal}(K/F) \cong G / \text{Gal}(E/K)$.

**Proof.** We proceed in several stages.

**Step 1: Artin's Theorem.** We first show that for any finite subgroup $H$ of $\text{Aut}(E)$ (the full automorphism group of $E$), $[E : E^H] = |H|$. Clearly $H \leq \text{Gal}(E/E^H)$, so $|H| \leq |\text{Gal}(E/E^H)| \leq [E : E^H]$. For the reverse inequality, let $|H| = n$ and suppose for contradiction that $[E : E^H] > n$. Then there exist $n + 1$ elements $\alpha_1, \ldots, \alpha_{n+1} \in E$ that are linearly independent over $E^H$. Consider the system of $n$ equations in $n + 1$ unknowns: $\sigma(\alpha_1) x_1 + \cdots + \sigma(\alpha_{n+1}) x_{n+1} = 0$ for each $\sigma \in H$. This homogeneous system has a nontrivial solution $(x_1, \ldots, x_{n+1}) \in E^{n+1}$. Choose such a solution with the fewest nonzero entries, and relabel so $x_1, \ldots, x_r$ are the nonzero ones. Scale so $x_1 = 1$. For any $\tau \in H$, applying $\tau$ to each equation gives $\tau\sigma(\alpha_1) x_1 + \cdots = 0$, which is another equation of the same system (since $\tau\sigma$ ranges over $H$ as $\sigma$ does). So $(\tau(x_1), \ldots, \tau(x_{n+1}))$ is also a solution. Subtracting from the original: $(x_1 - \tau(x_1), \ldots, x_{n+1} - \tau(x_{n+1}))$ is a solution with fewer nonzero entries (since $x_1 = 1$ and $\tau(1) = 1$ gives zero in the first position), contradicting minimality unless all $x_i \in E^H$. But then the original linear relation $\sum \alpha_i x_i = 0$ is a nontrivial relation over $E^H$, contradicting linear independence. Therefore $[E : E^H] \leq |H|$, giving equality.

**Step 2: $\Phi$ and $\Psi$ are inverses.** For any subgroup $H \leq G$, we have $\Phi(\Psi(H)) = \text{Gal}(E/E^H)$. By Artin's theorem, $[E : E^H] = |H|$, and $H \leq \text{Gal}(E/E^H)$, so $|\text{Gal}(E/E^H)| \leq [E : E^H] = |H|$, forcing $\text{Gal}(E/E^H) = H$. Thus $\Phi \circ \Psi = \text{id}$.

For any intermediate field $K$, consider $\Psi(\Phi(K)) = E^{\text{Gal}(E/K)}$. Since $E/F$ is Galois (normal and separable), $E/K$ is also Galois: normality is inherited because $E$ is the splitting field of a polynomial over $F$, hence also over $K$, and separability is inherited because every element of $E$ separable over $F$ is separable over $K$. For a Galois extension, the fixed field of the full Galois group is the base field: $E^{\text{Gal}(E/K)} = K$. To verify, if $\alpha \in E \setminus K$, then $\alpha$ has a minimal polynomial $m$ over $K$ with at least one other root $\beta \neq \alpha$ in $E$ (by normality), and the isomorphism $K(\alpha) \to K(\beta)$ extends to an automorphism $\sigma \in \text{Gal}(E/K)$ with $\sigma(\alpha) = \beta \neq \alpha$, so $\alpha \notin E^{\text{Gal}(E/K)}$. Thus $\Psi \circ \Phi = \text{id}$.

**Step 3: Inclusion reversal.** If $K_1 \subseteq K_2$, then any automorphism fixing $K_2$ pointwise also fixes $K_1$ pointwise, so $\text{Gal}(E/K_2) \subseteq \text{Gal}(E/K_1)$. Conversely, if $H_1 \subseteq H_2$, then any element fixed by all of $H_2$ is fixed by all of $H_1$, so $E^{H_2} \subseteq E^{H_1}$.

**Step 4: Degree formulas.** Since $E/K$ is Galois for every intermediate $K$, we have $|\text{Gal}(E/K)| = [E : K]$. By the Tower Law, $[E : F] = [E : K][K : F]$, and since $|G| = [E : F]$, we get $[K : F] = |G| / |\text{Gal}(E/K)| = [G : \text{Gal}(E/K)]$.

**Step 5: Normality correspondence.** We use the identity $\sigma(E^H) = E^{\sigma H \sigma^{-1}}$ for $\sigma \in G$. To verify: $\alpha \in E^H$ means $\tau(\alpha) = \alpha$ for all $\tau \in H$. Then $\sigma(\alpha)$ satisfies $(\sigma \tau \sigma^{-1})(\sigma(\alpha)) = \sigma(\tau(\alpha)) = \sigma(\alpha)$ for all $\tau \in H$, so $\sigma(\alpha) \in E^{\sigma H \sigma^{-1}}$. The reverse inclusion follows by replacing $\sigma$ with $\sigma^{-1}$.

Now, $K/F$ is Galois (i.e., normal) if and only if $\sigma(K) = K$ for all $\sigma \in G$. Since $K = E^{\text{Gal}(E/K)}$ (by Step 2), we have $\sigma(K) = \sigma(E^{\text{Gal}(E/K)}) = E^{\sigma \text{Gal}(E/K) \sigma^{-1}}$. This equals $K = E^{\text{Gal}(E/K)}$ for all $\sigma \in G$ if and only if $\sigma \text{Gal}(E/K) \sigma^{-1} = \text{Gal}(E/K)$ for all $\sigma$, i.e., $\text{Gal}(E/K) \trianglelefteq G$.

When $K/F$ is Galois, the restriction map $\text{res}: G \to \text{Gal}(K/F)$, $\sigma \mapsto \sigma|_K$, is a well-defined surjective homomorphism (surjectivity follows from the isomorphism extension property of splitting fields: every $F$-automorphism of $K$ extends to an $F$-automorphism of $E$). Its kernel is $\{\sigma \in G : \sigma|_K = \text{id}_K\} = \text{Gal}(E/K)$. By the First Isomorphism Theorem, $\text{Gal}(K/F) \cong G / \text{Gal}(E/K)$. $\square$

The power of this theorem is that it converts the lattice of intermediate fields—often an unwieldy infinite set—into the lattice of subgroups of a finite group, which is a finite, computable object. The correspondence preserves inclusion (reversing it), preserves degrees as indices, and translates normality of field extensions into normality of subgroups.

### A Concrete Example: $\mathbb{Q}(\sqrt{2}, \sqrt{3})/\mathbb{Q}$

The splitting field of $(x^2 - 2)(x^2 - 3)$ over $\mathbb{Q}$ is $E = \mathbb{Q}(\sqrt{2}, \sqrt{3})$, with $[E : \mathbb{Q}] = 4$. The Galois group is $G = \text{Gal}(E/\mathbb{Q}) \cong \mathbb{Z}_2 \times \mathbb{Z}_2$, generated by:

$$\sigma: \sqrt{2} \mapsto -\sqrt{2},\ \sqrt{3} \mapsto \sqrt{3}, \qquad \tau: \sqrt{2} \mapsto \sqrt{2},\ \sqrt{3} \mapsto -\sqrt{3}$$

The four elements are $\{\text{id}, \sigma, \tau, \sigma\tau\}$, and the automorphism $\sigma\tau$ sends $\sqrt{2} \mapsto -\sqrt{2}$, $\sqrt{3} \mapsto -\sqrt{3}$, which fixes $\sqrt{2} \cdot \sqrt{3} = \sqrt{6}$.

The subgroup lattice and the corresponding fixed field lattice illustrate the inclusion-reversing bijection:

```
   Intermediate Fields              Subgroups of G = Z₂ × Z₂

     E = Q(√2, √3)  ←———→  {e}
     /     |      \          /     |      \
 Q(√2)  Q(√6)  Q(√3) ←→ ⟨τ⟩  ⟨στ⟩   ⟨σ⟩
     \     |      /          \     |      /
          Q        ←———→       G
```

Every subgroup has index 2 in $G$, so every intermediate field has degree 2 over $\mathbb{Q}$, and every intermediate extension is Galois (since every subgroup of an abelian group is normal). The quotient $G/\langle\sigma\rangle \cong \mathbb{Z}_2$ corresponds to $\text{Gal}(\mathbb{Q}(\sqrt{3})/\mathbb{Q}) \cong \mathbb{Z}_2$, and similarly for the others.

### A Non-Abelian Example: The Splitting Field of $x^3 - 2$

The polynomial $x^3 - 2$ is irreducible over $\mathbb{Q}$ (by Eisenstein's criterion with $p = 2$). Its roots are $\alpha = \sqrt[3]{2}$, $\alpha\omega$, and $\alpha\omega^2$, where $\omega = e^{2\pi i/3}$ satisfies $\omega^2 + \omega + 1 = 0$. The splitting field is $E = \mathbb{Q}(\alpha, \omega)$, and $[E : \mathbb{Q}] = 6$ by the Tower Law: $[\mathbb{Q}(\alpha) : \mathbb{Q}] = 3$ and $[E : \mathbb{Q}(\alpha)] = 2$ (since $\omega \notin \mathbb{Q}(\alpha) \subseteq \mathbb{R}$ but $\omega$ satisfies the degree-2 polynomial $x^2 + x + 1$).

The Galois group $G = \text{Gal}(E/\mathbb{Q})$ has order 6 and is isomorphic to $S_3$. It is generated by the automorphisms:

$$\sigma: \alpha \mapsto \alpha\omega,\ \omega \mapsto \omega \quad\text{(3-cycle on roots, order 3)}$$

$$\tau: \alpha \mapsto \alpha,\ \omega \mapsto \omega^2 \quad\text{(transposition, complex conjugation, order 2)}$$

Labeling the roots $r_1 = \alpha$, $r_2 = \alpha\omega$, $r_3 = \alpha\omega^2$, we have $\sigma = (r_1\, r_2\, r_3)$ and $\tau = (r_2\, r_3)$, so $G \cong S_3$ acting on the three roots.

The subgroup lattice of $S_3$ has six subgroups: the trivial group, three subgroups of order 2 generated by the three transpositions, the cyclic subgroup $A_3 = \langle(123)\rangle$ of order 3, and $S_3$ itself. The FTGT gives the correspondence:

| Subgroup of $G$ | Fixed Field | $[K:\mathbb{Q}]$ | Galois over $\mathbb{Q}$? |
|---|---|---|---|
| $\{e\}$ | $E = \mathbb{Q}(\alpha, \omega)$ | 6 | Yes |
| $\langle\sigma\rangle \cong \mathbb{Z}_3$ | $\mathbb{Q}(\omega)$ | 2 | Yes ($A_3 \trianglelefteq S_3$) |
| $\langle\tau\rangle \cong \mathbb{Z}_2$ | $\mathbb{Q}(\alpha)$ | 3 | No ($\langle\tau\rangle \not\trianglelefteq S_3$) |
| $\langle\sigma\tau\rangle \cong \mathbb{Z}_2$ | $\mathbb{Q}(\alpha\omega^2)$ | 3 | No |
| $\langle\sigma^2\tau\rangle \cong \mathbb{Z}_2$ | $\mathbb{Q}(\alpha\omega)$ | 3 | No |
| $G \cong S_3$ | $\mathbb{Q}$ | 1 | Yes |

The subgroup $\langle\sigma\rangle = A_3$ is normal in $S_3$, so $\mathbb{Q}(\omega)/\mathbb{Q}$ is Galois, and indeed $\mathbb{Q}(\omega)$ is the splitting field of $x^2 + x + 1$ over $\mathbb{Q}$. The three order-2 subgroups are not normal, and correspondingly $\mathbb{Q}(\alpha)$, $\mathbb{Q}(\alpha\omega)$, $\mathbb{Q}(\alpha\omega^2)$ are not Galois over $\mathbb{Q}$—each contains only one of the three roots of $x^3 - 2$.

## 3. High-Performance Optimization & Failure Modes

### Solvable Groups and Radical Extensions

A group $G$ is **solvable** if it has a subnormal series $\{e\} = G_0 \trianglelefteq G_1 \trianglelefteq \cdots \trianglelefteq G_n = G$ with each quotient $G_i / G_{i-1}$ abelian. Equivalently, the **derived series** terminates: define $G^{(0)} = G$ and $G^{(k+1)} = [G^{(k)}, G^{(k)}]$ (the commutator subgroup); then $G$ is solvable if and only if $G^{(n)} = \{e\}$ for some $n$.

A polynomial $f \in F[x]$ is **solvable by radicals** over $F$ if its roots can be expressed from the coefficients of $f$ using field operations ($+$, $-$, $\times$, $\div$) and extraction of $n$-th roots. Formally, this means the splitting field $E$ of $f$ is contained in some **radical extension** of $F$: a tower $F = F_0 \subseteq F_1 \subseteq \cdots \subseteq F_m$ where $F_i = F_{i-1}(\sqrt[n_i]{a_i})$ for some $a_i \in F_{i-1}$ and positive integer $n_i$.

The central theorem connecting these notions is:

**Theorem (Galois's Criterion).** Let $F$ be a field of characteristic 0, and let $f \in F[x]$ with splitting field $E$. Then $f$ is solvable by radicals over $F$ if and only if $\text{Gal}(E/F)$ is a solvable group.

**Proof sketch.** For the forward direction, suppose $f$ is solvable by radicals, so $E \subseteq M$ for some radical extension $M$ of $F$. We may assume $M/F$ is Galois by replacing $M$ with its Galois closure (which is still a radical extension, since the Galois closure of a tower of radical extensions is again radical, after adjoining appropriate roots of unity). The key observation is that the Galois group of a radical extension is solvable: each step $F_i = F_{i-1}(\sqrt[n_i]{a_i})$ gives an extension whose Galois group (over $F_{i-1}$, after adjoining roots of unity) is cyclic or a subgroup of a semidirect product of cyclic groups, hence solvable. A tower of solvable extensions has solvable Galois group (by the FTGT, using the fact that a group with a solvable normal subgroup with solvable quotient is itself solvable). Since $E/F$ is Galois and $E \subseteq M$, the restriction $\text{Gal}(M/F) \to \text{Gal}(E/F)$ is surjective, so $\text{Gal}(E/F)$ is a quotient of a solvable group, hence solvable.

For the reverse direction, suppose $G = \text{Gal}(E/F)$ is solvable. We construct a radical extension containing $E$. The derived series of $G$ gives a chain $\{e\} = G_n \trianglelefteq G_{n-1} \trianglelefleq \cdots \trianglelefteq G_0 = G$ with abelian quotients. Refine this to a composition series with cyclic quotients of prime order. By the FTGT, this corresponds to a tower of fields $F = E_{G_0} \subseteq E_{G_1} \subseteq \cdots \subseteq E_{G_n} = E$ where each step $E_{G_{i+1}}/E_{G_i}$ is a cyclic Galois extension of prime degree $p_i$. By Kummer theory (after adjoining $p_i$-th roots of unity, which is itself a radical step), a cyclic extension of degree $p_i$ is generated by a $p_i$-th root. Thus each step is radical, and the whole tower is a radical extension. $\square$

### The Simplicity of $A_5$ and the Insolvability of the Quintic

The alternating group $A_5$ has order 60. Its conjugacy classes, computed by examining cycle types in $S_5$ and determining which split in $A_5$, have sizes:

| Cycle type | Class size in $A_5$ |
|---|---|
| Identity | 1 |
| Double transpositions $(ab)(cd)$ | 15 |
| 3-cycles $(abc)$ | 20 |
| 5-cycles (one class) | 12 |
| 5-cycles (other class) | 12 |

The 5-cycles form a single class of size 24 in $S_5$, but this class splits into two classes of size 12 in $A_5$ because the centralizer of a 5-cycle in $S_5$ is $\langle(12345)\rangle$, which is contained in $A_5$ (all 5-cycles are even permutations).

**Theorem.** $A_5$ is simple (has no proper nontrivial normal subgroup).

**Proof.** A normal subgroup is a union of conjugacy classes (since it is closed under conjugation) and contains the identity. So its order is a sum of the form $1 + \sum c_i$ where each $c_i$ is chosen from $\{12, 12, 15, 20\}$ (the non-identity class sizes). This sum must divide $|A_5| = 60$. We check all possibilities: the divisors of 60 are $1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60$. The achievable sums (including the mandatory 1) are:

- $1$ (trivial subgroup)
- $1 + 12 = 13$ — does not divide 60
- $1 + 12 + 12 = 25$ — does not divide 60
- $1 + 15 = 16$ — does not divide 60
- $1 + 20 = 21$ — does not divide 60
- $1 + 12 + 15 = 28$ — does not divide 60
- $1 + 12 + 20 = 33$ — does not divide 60
- $1 + 15 + 20 = 36$ — does not divide 60
- $1 + 12 + 12 + 15 = 40$ — does not divide 60
- $1 + 12 + 12 + 20 = 45$ — does not divide 60
- $1 + 12 + 15 + 20 = 48$ — does not divide 60
- $1 + 12 + 12 + 15 + 20 = 60$ — the whole group

No sum other than 1 and 60 divides 60. Therefore $A_5$ has no proper nontrivial normal subgroup. $\square$

**Corollary.** $S_5$ is not solvable.

**Proof.** The derived series of $S_5$ is $S_5^{(0)} = S_5$, $S_5^{(1)} = [S_5, S_5] = A_5$ (since $S_5/A_5 \cong \mathbb{Z}_2$ is abelian, so $[S_5, S_5] \subseteq A_5$, and $A_5$ is generated by 3-cycles, each of which is a commutator: $(abc) = [(ab), (ac)]$). Then $S_5^{(2)} = [A_5, A_5] = A_5$ (since $A_5$ is simple and non-abelian, so its commutator subgroup is either trivial or $A_5$ itself, and non-abelian forces the latter). The derived series stabilizes at $A_5 \neq \{e\}$, so $S_5$ is not solvable. $\square$

### A Specific Quintic Not Solvable by Radicals

To demonstrate the insolvability in a fully concrete setting, we exhibit a specific polynomial over $\mathbb{Q}$ with Galois group $S_5$.

**Theorem.** The polynomial $f(x) = x^5 - 5x + 2$ is not solvable by radicals over $\mathbb{Q}$.

**Proof.** We show $\text{Gal}(f) \cong S_5$, which is not solvable, so Galois's criterion applies.

**Irreducibility.** By the rational root theorem, the only candidates for rational roots are $\pm 1, \pm 2$. We compute $f(1) = -2$, $f(-1) = 6$, $f(2) = 24$, $f(-2) = -20$, so there are no rational roots. To rule out a factorization as degree 2 times degree 3, suppose $f(x) = (x^2 + ax + b)(x^3 + cx^2 + dx + e)$ with integer coefficients (Gauss's lemma). Expanding and comparing:

$$c + a = 0, \quad d - a^2 + b = 0, \quad e + a^3 - 2ab = 0, \quad -a^4 + 3a^2b - b^2 = -5, \quad -a^3b + 2ab^2 = 2$$

From the last equation, $b(-a^3 + 2ab) = 2$, so $b$ divides 2. Testing $b \in \{1, 2, -1, -2\}$, one finds no integer solution for $a$ in any case. Therefore $f$ is irreducible over $\mathbb{Q}$.

Since $f$ is irreducible of degree 5, $G = \text{Gal}(f)$ acts transitively on the five roots, so $5 \mid |G|$ by the orbit-stabilizer theorem. By Cauchy's theorem, $G$ contains an element of order 5, which in $S_5$ must be a 5-cycle.

**Real roots.** We compute $f'(x) = 5x^4 - 5$, so $f'(x) = 0$ at $x = \pm 1$. The values at critical points are $f(-1) = -1 + 5 + 2 = 6 > 0$ (local maximum) and $f(1) = 1 - 5 + 2 = -2 < 0$ (local minimum). Since $f(x) \to -\infty$ as $x \to -\infty$ and $f(x) \to +\infty$ as $x \to +\infty$, the sign changes give exactly three real roots (one in $(-\infty, -1)$, one in $(-1, 1)$, one in $(1, \infty)$). The remaining two roots are a complex conjugate pair.

**Complex conjugation.** Complex conjugation acts on the roots as an automorphism of order 2 that fixes the three real roots and swaps the two complex conjugate roots. This is a transposition in $G \subseteq S_5$.

**Conclusion.** $G$ is a transitive subgroup of $S_5$ containing a 5-cycle and a transposition. The transitive subgroups of $S_5$ are $\mathbb{Z}_5$ (order 5), $D_5$ (order 10), $\text{AGL}(1,5)$ (order 20), $A_5$ (order 60), and $S_5$ (order 120). Of these, only $S_5$ contains a transposition: $A_5$ contains only even permutations, and $\mathbb{Z}_5$, $D_5$, and $\text{AGL}(1,5)$ have no transpositions in their cycle-type spectra. Therefore $G = S_5$, which is not solvable. $\square$

This argument is a complete, constructive proof that a specific, explicitly written polynomial has roots that cannot be expressed by radicals. The insolvability is not a matter of our ingenuity failing to find a formula; it is a theorem that no such formula can exist.

### Finite Fields and the AES Galois Field

The theory of finite fields is a direct application of splitting fields and Galois theory that is computationally implemented in modern cryptography.

**Theorem.** For every prime $p$ and positive integer $n$, there exists a unique (up to isomorphism) finite field of order $p^n$, denoted $\mathbb{F}_{p^n}$. It is the splitting field of $x^{p^n} - x$ over $\mathbb{F}_p$.

**Proof.** The polynomial $x^{p^n} - x$ has derivative $p^n x^{p^n - 1} - 1 = -1 \neq 0$ in $\mathbb{F}_p[x]$ (since $\text{char} = p$ divides $p^n$), so it is separable. Its splitting field $E$ over $\mathbb{F}_p$ contains exactly $p^n$ roots (the polynomial has degree $p^n$ and is separable), and these roots form a field: if $\alpha^{p^n} = \alpha$ and $\beta^{p^n} = \beta$, then $(\alpha + \beta)^{p^n} = \alpha^{p^n} + \beta^{p^n} = \alpha + \beta$ (by the Frobenius endomorphism), and similarly $(\alpha\beta)^{p^n} = \alpha\beta$ and $(\alpha^{-1})^{p^n} = \alpha^{-1}$. So $E$ is a field of $p^n$ elements. Uniqueness follows from the uniqueness of splitting fields. $\square$

The Galois group $\text{Gal}(\mathbb{F}_{p^n}/\mathbb{F}_p)$ is cyclic of order $n$, generated by the **Frobenius automorphism** $\varphi: x \mapsto x^p$. This follows because $\varphi$ fixes $\mathbb{F}_p$ pointwise (by Fermat's little theorem), has order $n$ (since $\varphi^n(x) = x^{p^n} = x$ for all $x \in \mathbb{F}_{p^n}$, and no smaller power fixes all elements), and $|\text{Gal}(\mathbb{F}_{p^n}/\mathbb{F}_p)| = [\mathbb{F}_{p^n} : \mathbb{F}_p] = n$. The FTGT tells us that there is exactly one intermediate field for each divisor $d$ of $n$, namely $\mathbb{F}_{p^d}$, corresponding to the unique subgroup $\langle\varphi^d\rangle$ of order $n/d$.

In the AES (Advanced Encryption Standard) block cipher, the Rijndael field $\mathbb{F}_{2^8}$ is constructed as $\mathbb{F}_2[x] / (m(x))$ where $m(x) = x^8 + x^4 + x^3 + x + 1$ is an irreducible polynomial over $\mathbb{F}_2$. Elements of $\mathbb{F}_{2^8}$ are represented as polynomials of degree at most 7 with coefficients in $\mathbb{F}_2$, which correspond to 8-bit bytes. Addition is componentwise XOR. Multiplication is polynomial multiplication modulo $m(x)$, which keeps the result within the field.

The irreducibility of $m(x) = x^8 + x^4 + x^3 + x + 1$ over $\mathbb{F}_2$ can be verified by checking that it is not divisible by any irreducible polynomial of degree 1, 2, or 4 over $\mathbb{F}_2$ (since $\deg m = 8 = 2 \times 4$, the only possible factorizations are $1 \times 7$, $2 \times 6$, $3 \times 5$, and $4 \times 4$; checking against all irreducible polynomials of degree $\leq 4$ suffices). The irreducible polynomials of degree 1 over $\mathbb{F}_2$ are $x$ and $x+1$. Since $m(0) = 1$ and $m(1) = 1 + 1 + 1 + 1 + 1 = 1$ (in $\mathbb{F}_2$, an odd number of 1s sums to 1), neither divides $m$. The irreducible degree-2 polynomial is $x^2 + x + 1$; performing the division confirms a nonzero remainder. The three irreducible degree-4 polynomials are $x^4 + x + 1$, $x^4 + x^3 + 1$, and $x^4 + x^3 + x^2 + x + 1$; each leaves a nonzero remainder when divided into $m(x)$. Therefore $m(x)$ is irreducible, and $\mathbb{F}_2[x]/(m(x))$ is indeed the field $\mathbb{F}_{2^8}$.

The multiplicative group $\mathbb{F}_{2^8}^*$ is cyclic of order 255. In AES, the S-box substitution step uses multiplicative inversion in this group (with 0 mapped to 0), followed by an affine transformation over $\mathbb{F}_2$. The inversion exploits the cyclic structure: for any nonzero $\alpha \in \mathbb{F}_{2^8}$, $\alpha^{-1} = \alpha^{254}$ since $\alpha^{255} = 1$. The MixColumns step performs matrix multiplication over $\mathbb{F}_{2^8}$, treating each column of the state matrix as a vector and multiplying by a fixed circulant matrix whose entries are in $\mathbb{F}_{2^8}$.

### Constructibility and the Classical Impossibility Theorems

Galois theory also resolves the three classical construction problems of antiquity, which ask what can be constructed using only compass and straightedge. A point is constructible from a set of given points if and only if its coordinates lie in a field obtained from the field of the given coordinates by a sequence of quadratic extensions. Therefore, a constructible number $\alpha$ over $\mathbb{Q}$ satisfies $[\mathbb{Q}(\alpha) : \mathbb{Q}] = 2^k$ for some $k \geq 0$.

**Doubling the cube.** To construct a cube of twice the volume of a unit cube requires constructing $\sqrt[3]{2}$. The minimal polynomial of $\sqrt[3]{2}$ over $\mathbb{Q}$ is $x^3 - 2$ (irreducible by Eisenstein with $p = 2$), so $[\mathbb{Q}(\sqrt[3]{2}) : \mathbb{Q}] = 3$, which is not a power of 2. Therefore $\sqrt[3]{2}$ is not constructible, and the cube cannot be doubled by compass and straightedge.

**Squaring the circle.** This requires constructing $\sqrt{\pi}$. Since $\pi$ is transcendental over $\mathbb{Q}$ (proved by Lindemann in 1882, beyond the scope of this lesson but using analytic methods), $\sqrt{\pi}$ is also transcendental, so $[\mathbb{Q}(\sqrt{\pi}) : \mathbb{Q}]$ is infinite, certainly not a power of 2. The circle cannot be squared.

**Trisecting a general angle.** Some angles can be trisected (for example, $180°$ trisects to $60°$, which is constructible), but not all. The angle $60°$ cannot be trisected: this would require constructing $\cos(20°)$, whose minimal polynomial over $\mathbb{Q}$ is $8x^3 - 6x - 1$ (derived from $\cos(3\theta) = 4\cos^3\theta - 3\cos\theta$ with $\theta = 20°$ and $\cos(60°) = 1/2$). This cubic polynomial is irreducible over $\mathbb{Q}$, so $[\mathbb{Q}(\cos 20°) : \mathbb{Q}] = 3$, not a power of 2.

These impossibility results illustrate the full arc of Galois theory: from the abstract definition of field extensions and minimal polynomials, through the Galois correspondence and the structure of finite groups, to definitive negative answers to questions that stood open for over two thousand years. The machinery is not merely classificatory but predictive: it tells us, before any attempt at construction, that certain constructions are impossible and certain equations cannot be solved. The barrier is not human limitation but mathematical law, encoded in the structure of the Galois group.
