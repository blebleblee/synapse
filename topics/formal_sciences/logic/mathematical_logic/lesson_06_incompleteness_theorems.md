# Lesson 6: Gödel's Incompleteness Theorems — Provability Limits in Formal Arithmetic

## 1. First-Principles Intuition & Invariants

### The Crisis That Made the Theorems Necessary

To understand why Gödel's incompleteness theorems constitute one of the most profound intellectual achievements of the twentieth century, one must first inhabit the mathematical world of 1900. David Hilbert, the foremost mathematician of his era, had placed before the community a program of extraordinary ambition: formalize all of mathematics in a finite, complete, and consistent axiomatic system. By "complete," Hilbert meant that every true mathematical statement should be derivable from the axioms. By "consistent," he meant the system should never derive a contradiction. By "finitely axiomatizable," he meant the rules of inference and axioms should be explicitly listable, leaving nothing to intuition. This was not idle speculation — it was the logical culmination of the formalist movement, which sought to reduce mathematical truth to mechanical symbol manipulation, purging from the foundations any dependence on semantic meaning or geometric intuition.

The confidence behind Hilbert's program was not irrational. Peano had given arithmetic a clean axiomatic basis. Cantor had formalized the theory of sets. Frege, Russell, and Whitehead had shown that large swaths of mathematics could be encoded in formal logic. The feeling in the air was that completeness and consistency were simply waiting to be proved — technical matters for the next generation to tidy up. Hilbert famously declared, "We must know, we will know."

In 1931, Kurt Gödel, a 25-year-old logician working in Vienna, destroyed this program in a single paper. He showed, with absolute mathematical rigor, that any sufficiently expressive formal system — one capable of representing basic arithmetic — cannot be both complete and consistent. If it is consistent, there exist true arithmetic statements it cannot prove. Moreover, the consistency of such a system cannot itself be proved from within the system. Hilbert's program was not merely incomplete; it was foundationally impossible.

What makes Gödel's proof so remarkable is that it does not appeal to some exotic, unreachable region of mathematics. The unprovable statement Gödel constructs is a statement about the natural numbers, expressible in the language of Peano Arithmetic (PA). The mechanism of the proof is essentially arithmetic self-reference: Gödel found a way to make the formal system talk about its own provability, and from this capacity for self-reference, he extracted a contradiction with completeness.

### The Formal System: Peano Arithmetic

The natural formal setting for Gödel's theorems is Peano Arithmetic, though the results apply to any sufficiently strong consistent formal system. PA operates over a first-order language $\mathcal{L}_A$ with the following signature. The language contains a constant symbol $0$, a unary function symbol $S$ (the successor function), and binary function symbols $+$ and $\cdot$ for addition and multiplication. The axioms of PA are as follows.

The first group governs successor: $S(x) \neq 0$ for all $x$, and $S(x) = S(y) \to x = y$ (injectivity of successor). The second group defines addition recursively: $x + 0 = x$ and $x + S(y) = S(x + y)$. The third group defines multiplication recursively: $x \cdot 0 = 0$ and $x \cdot S(y) = (x \cdot y) + x$. Finally, the induction schema asserts, for every formula $\phi(x)$ in $\mathcal{L}_A$:

$$\bigl(\phi(0) \land \forall x\,(\phi(x) \to \phi(S(x)))\bigr) \to \forall x\,\phi(x)$$

This schema, being parameterized over all formulas $\phi$, generates infinitely many axioms. This is the standard formulation of first-order PA, and it is strong enough to represent all primitive recursive functions and to encode the syntax and proof theory of itself — the precise capacity Gödel needed.

### Representability: The Bridge Between Syntax and Arithmetic

The central technical precondition for Gödel's proof is the representability of computable functions within PA. The intuition is this: if the formal system can reason about natural numbers, and if we can encode syntactic objects — formulas, proofs, derivations — as natural numbers, then the system can reason about its own syntactic operations. This encoding is called Gödel numbering, and representability is what gives the encoding logical force.

A function $f: \mathbb{N}^k \to \mathbb{N}$ is said to be **representable** in PA if there exists a formula $\phi_f(x_1, \ldots, x_k, y)$ in $\mathcal{L}_A$ such that for every tuple of natural numbers $(n_1, \ldots, n_k)$:

$$f(n_1, \ldots, n_k) = m \quad \Longleftrightarrow \quad \text{PA} \vdash \phi_f(\bar{n}_1, \ldots, \bar{n}_k, \bar{m})$$

where $\bar{n}$ denotes the numeral for $n$, defined as $S^n(0)$ — the $n$-fold application of the successor function to $0$. Additionally, PA must prove uniqueness: $\text{PA} \vdash \forall y\,(\phi_f(\bar{n}_1, \ldots, \bar{n}_k, y) \to y = \bar{m})$.

The critical theorem is that every **primitive recursive function** is representable in PA. Primitive recursive functions are built from the base cases of zero ($Z(x) = 0$), successor ($S(x) = x + 1$), and projection ($P_i^k(x_1, \ldots, x_k) = x_i$), closed under composition and primitive recursion. The full class of representable functions in PA extends further — to the **recursive** (or general recursive) functions, which additionally allow unbounded minimization — but primitive recursion suffices for encoding syntax.

The proof that primitive recursive functions are representable proceeds by structural induction on the construction of the function. The base functions are trivially representable by atomic formulas: $Z$ by the formula $y = 0$, $S$ by $y = S(x)$, and projections by $y = x_i$. For composition, if $h = f(g_1, \ldots, g_k)$ and each $g_i$ is represented by $\phi_{g_i}$ and $f$ is represented by $\phi_f$, then $h$ is represented by:

$$\phi_h(\vec{x}, y) \equiv \exists z_1 \cdots \exists z_k\,\bigl(\phi_{g_1}(\vec{x}, z_1) \land \cdots \land \phi_{g_k}(\vec{x}, z_k) \land \phi_f(z_1, \ldots, z_k, y)\bigr)$$

For primitive recursion, the construction is more involved and requires encoding sequences of values as a single natural number — a technique Gödel himself handled with a beautiful device using the Chinese Remainder Theorem, now known as the **$\beta$-function lemma**.

### The $\beta$-Function Lemma

Primitive recursion defines $f(x, 0) = g(x)$ and $f(x, S(n)) = h(x, n, f(x, n))$. To represent this in PA, one needs a way to talk about the entire sequence of values $\langle f(x, 0), f(x, 1), \ldots, f(x, n) \rangle$ using a single natural number. Gödel's $\beta$-function accomplishes exactly this.

Define $\beta(c, d, i) = \text{rem}(c, 1 + (i+1) \cdot d)$, where $\text{rem}(a, b)$ denotes the remainder of $a$ divided by $b$. The lemma states: for any finite sequence of natural numbers $a_0, a_1, \ldots, a_n$, there exist natural numbers $c$ and $d$ such that $\beta(c, d, i) = a_i$ for all $0 \le i \le n$.

The proof is an application of the Chinese Remainder Theorem. Set $d = \max(n, a_0, \ldots, a_n)!$ (the factorial of the maximum, ensuring divisibility conditions). Then the numbers $1 + d, 1 + 2d, \ldots, 1 + (n+1)d$ are pairwise coprime: if a prime $p$ divides both $1 + id$ and $1 + jd$ with $i < j$, then $p$ divides $(j - i)d$. Since $p$ divides $1 + id$, it does not divide $d$, so $p$ divides $j - i$. But $j - i \le n \le d$, so $p \le d$, and therefore $p$ divides $d!$, hence $p$ divides $d$, a contradiction. By CRT, we can find $c$ such that $c \equiv a_i \pmod{1 + (i+1)d}$ for each $i$. Then $\beta(c, d, i) = \text{rem}(c, 1 + (i+1)d) = a_i$.

Since the $\beta$-function is primitive recursive (remainder is definable from division, which is primitive recursive), and since the lemma guarantees that any finite sequence is coded by some pair $(c, d)$, we can represent primitive recursion in PA by quantifying over the codes of intermediate computation sequences. This completes the proof that all primitive recursive functions are representable.

---

## 2. Core Architecture & Mechanics

### Gödel Numbering: The Encoding Architecture

The technical heart of Gödel's proof is the assignment of a unique natural number — a Gödel number — to every symbol, formula, and finite sequence of formulas in the language $\mathcal{L}_A$. Once this encoding is in place, syntactic operations become arithmetic operations, and PA can speak about its own formulas as naturally as it speaks about the integers.

The encoding proceeds in stages. First, assign a unique positive integer to each symbol of $\mathcal{L}_A$. A standard assignment might be:

| Symbol | Gödel Number |
|--------|-------------|
| $0$ | 1 |
| $S$ | 2 |
| $+$ | 3 |
| $\cdot$ | 4 |
| $=$ | 5 |
| $\lnot$ | 6 |
| $\land$ | 7 |
| $\lor$ | 8 |
| $\to$ | 9 |
| $\forall$ | 10 |
| $\exists$ | 11 |
| $($ | 12 |
| $)$ | 13 |
| $v_i$ (variable) | $14 + i$ |

Given a finite sequence of symbols $s_1, s_2, \ldots, s_n$ with Gödel numbers $e_1, e_2, \ldots, e_n$, the Gödel number of the sequence is:

$$\ulcorner s_1 s_2 \cdots s_n \urcorner = 2^{e_1} \cdot 3^{e_2} \cdot 5^{e_3} \cdots p_n^{e_n}$$

where $p_k$ is the $k$-th prime. By the Fundamental Theorem of Arithmetic, this encoding is injective: every finite sequence of symbols corresponds to exactly one natural number, and that number can be decoded uniquely by factoring. The Gödel number of the formula $0 = 0$, for instance, is $2^1 \cdot 3^5 \cdot 5^1$, encoding the symbols $0$, $=$, $0$ in sequence.

A finite sequence of formulas $\phi_1, \phi_2, \ldots, \phi_k$ — such as a proof — is itself encoded by treating each $\ulcorner \phi_i \urcorner$ as the exponent of the $i$-th prime:

$$\ulcorner \phi_1, \ldots, \phi_k \urcorner = 2^{\ulcorner \phi_1 \urcorner} \cdot 3^{\ulcorner \phi_2 \urcorner} \cdots p_k^{\ulcorner \phi_k \urcorner}$$

This two-level encoding allows proofs themselves to be assigned Gödel numbers and reasoned about arithmetically.

The critical consequence is that every syntactic predicate about formulas and proofs — "is a well-formed formula," "is a proof of $\phi$ from PA," "is a closed formula" — becomes an arithmetic predicate. Gödel showed, with considerable effort, that all such predicates of immediate proof-theoretic relevance are in fact primitive recursive, and hence representable in PA.

### The Provability Predicate and Its Architecture

The most important predicate Gödel constructs is $\text{Proof}(p, \phi)$: the number $p$ codes a valid proof in PA of the formula with Gödel number $\phi$. This is a primitive recursive relation on natural numbers. Its construction proceeds by verifying, in a purely mechanical and finite way, that the sequence coded by $p$ constitutes a valid derivation: each line is either an axiom of PA or follows from earlier lines by modus ponens or generalization, and the final line is $\phi$.

Each component of this verification is primitive recursive. The predicate "is a logical axiom" is decidable by pattern matching on the formula's Gödel number. The predicate "is a PA-specific axiom" is decidable because the axioms (other than the induction schema) are finitely enumerable, and membership in the induction schema is a decidable syntactic check. Modus ponens and generalization are syntactically checkable. The conjunction of these conditions over a finite sequence is primitive recursive.

From $\text{Proof}(p, \phi)$, define the **provability predicate**:

$$\text{Prov}(\phi) \equiv \exists p\, \text{Proof}(p, \phi)$$

This asserts that there exists some natural number that codes a valid proof of $\phi$. Since $\text{Proof}$ is primitive recursive (hence representable), $\text{Prov}$ is a $\Sigma_1^0$ formula — it involves an existential quantifier over natural numbers prefixing a decidable relation. Within PA, let $\text{Prov}(x)$ denote the formula representing this predicate, and write $\Box \phi$ for $\text{Prov}(\ulcorner \phi \urcorner)$, the statement "PA proves $\phi$."

The following flow illustrates the architecture of encoding and self-reference:

```
   Syntactic Realm                   Arithmetic Realm
   ─────────────────                 ──────────────────────────────
   Symbols of L_A    ──encode──▶     Natural numbers (Gödel numbers)
   Formulas           ──encode──▶     Gödel numbers of formulas
   Proofs             ──encode──▶     Gödel numbers of proof sequences
   Syntactic ops      ──encode──▶     Primitive recursive functions
   "φ is provable"    ──encode──▶     Prov(⌈φ⌉)  [Σ₁⁰ formula in PA]
        │                                         │
        └──────── PA can reason about ────────────┘
                  its own provability
```

This feedback loop — the system reasoning arithmetically about its own syntax — is the structural precondition for Gödel's self-referential construction.

### The Diagonal Lemma

The Diagonal Lemma (also called the Fixed-Point Lemma or Self-Reference Lemma) is the technical core of the incompleteness proof. It guarantees that for any formula $\psi(x)$ with one free variable, there exists a sentence $\phi$ such that:

$$\text{PA} \vdash \phi \leftrightarrow \psi(\ulcorner \phi \urcorner)$$

The sentence $\phi$ is, in a precise formal sense, a sentence that "says" $\psi$ of its own Gödel number.

**Proof of the Diagonal Lemma.** Define the **diagonalization** function $\text{diag}: \mathbb{N} \to \mathbb{N}$ as follows: for a natural number $n$, if $n$ is the Gödel number of a formula $\alpha(x)$ with one free variable $x$, then $\text{diag}(n) = \ulcorner \alpha(\bar{n}) \urcorner$ — the Gödel number of the formula obtained by substituting the numeral $\bar{n}$ for the free variable in $\alpha$. If $n$ does not code such a formula, $\text{diag}(n) = 0$ by convention.

The function $\text{diag}$ is primitive recursive: substituting a numeral into a formula is a purely syntactic, finitely computable operation on the Gödel number encoding, hence representable in PA by some formula $\delta(x, y)$ satisfying $\text{PA} \vdash \delta(\bar{n}, \overline{\text{diag}(n)})$ for all $n$.

Now, given $\psi(x)$, define the formula $\theta(x) \equiv \psi(\delta(x, x))$... but more cleanly, proceed as follows. Let $\alpha(x)$ be the formula $\psi(\delta(x, x))$, where $\delta(x,y)$ represents the diagonalization function. Let $n = \ulcorner \alpha \urcorner$. Define $\phi \equiv \alpha(\bar{n})$.

Unfolding: $\phi$ is $\psi(\delta(\bar{n}, \bar{n}))$. Since $\delta$ represents $\text{diag}$ and $\text{diag}(\ulcorner \alpha \urcorner) = \ulcorner \alpha(\bar{n}) \urcorner = \ulcorner \phi \urcorner$, PA proves $\delta(\bar{n}, \bar{n}) = \ulcorner \phi \urcorner$. Substituting into the definition of $\phi$:

$$\text{PA} \vdash \phi \leftrightarrow \psi(\ulcorner \phi \urcorner)$$

This is the fixed point: $\phi$ is provably equivalent (within PA) to $\psi$ applied to $\phi$'s own Gödel number. The proof is entirely constructive — given $\psi$, one can explicitly compute the Gödel number of $\phi$ by applying the diagonalization operation once. $\square$

The analogy to the classical Liar Paradox is sharp but carefully controlled. The Liar says "This sentence is false," generating a semantic paradox because the predicate is truth. Gödel replaces truth with provability — a syntactic, arithmetic predicate — and uses a formal equivalence ($\vdash \phi \leftrightarrow \psi(\ulcorner\phi\urcorner)$) rather than a semantic self-reference. This keeps the construction within the formal system and avoids paradox, while producing an undecidable sentence.

### The First Incompleteness Theorem: Construction and Proof

Apply the Diagonal Lemma with $\psi(x) \equiv \lnot \text{Prov}(x)$. The result is a sentence $\gamma$ such that:

$$\text{PA} \vdash \gamma \leftrightarrow \lnot \text{Prov}(\ulcorner \gamma \urcorner)$$

The sentence $\gamma$ asserts its own unprovability in PA. This is the **Gödel sentence**. We now prove Gödel's First Incompleteness Theorem.

**Theorem (Gödel, 1931).** If PA is consistent, then $\gamma$ is not provable in PA.

**Proof.** Suppose for contradiction that PA $\vdash \gamma$. Since $\text{Prov}$ represents provability and PA $\vdash \gamma$, there exists a proof of $\gamma$ coded by some natural number $p$, so $\text{Proof}(p, \ulcorner \gamma \urcorner)$ is true. Since $\text{Proof}$ is primitive recursive and hence $\Sigma_1^0$-definable in PA, and since $\text{Proof}(p, \ulcorner \gamma \urcorner)$ is in fact true for this specific $p$, PA proves $\text{Proof}(\bar{p}, \ulcorner \gamma \urcorner)$. From $\text{Proof}(\bar{p}, \ulcorner \gamma \urcorner)$, PA derives $\exists p\, \text{Proof}(p, \ulcorner \gamma \urcorner)$, which is precisely $\text{Prov}(\ulcorner \gamma \urcorner)$, i.e., $\Box \gamma$. But by the fixed-point construction, PA $\vdash \gamma \leftrightarrow \lnot \Box \gamma$, so PA $\vdash \lnot \gamma$. We now have PA $\vdash \gamma$ and PA $\vdash \lnot \gamma$, contradicting the consistency of PA. $\square$

**Theorem.** If PA is $\omega$-consistent, then $\lnot \gamma$ is not provable in PA.

Here, $\omega$-consistency is a strengthening of consistency: it requires that PA not prove $\exists x\, \lnot \phi(x)$ whenever it proves $\phi(\bar{n})$ for every specific numeral $\bar{n}$. Under $\omega$-consistency, suppose PA $\vdash \lnot \gamma$, i.e., PA $\vdash \text{Prov}(\ulcorner \gamma \urcorner)$, i.e., PA $\vdash \exists p\, \text{Proof}(p, \ulcorner \gamma \urcorner)$. But we just showed PA $\nvdash \gamma$, meaning no proof of $\gamma$ exists in PA. Hence for every $n$, $\text{Proof}(n, \ulcorner \gamma \urcorner)$ is false, and since $\text{Proof}$ correctly represents the proof-checking relation, PA proves $\lnot \text{Proof}(\bar{n}, \ulcorner \gamma \urcorner)$ for every numeral $\bar{n}$. By $\omega$-consistency, PA cannot prove $\exists p\, \text{Proof}(p, \ulcorner \gamma \urcorner)$. This contradicts PA $\vdash \lnot \gamma$. $\square$

Together, these two results show that $\gamma$ is independent of PA: neither provable nor refutable. Rosser later (1936) strengthened this to require only simple consistency rather than $\omega$-consistency, by modifying the Gödel sentence using a more refined self-referential construction that explicitly compares the lengths of proofs and refutations.

The semantic content of $\gamma$ is illuminating. Under the standard model $\mathbb{N}$, the sentence $\gamma$ is in fact true: PA is consistent (we believe), so it does not prove $\gamma$, so $\gamma$'s assertion of its own unprovability is accurate. Gödel's theorem therefore exhibits a true arithmetic statement that PA cannot prove. This is not merely a formal curiosity; it shows that formal provability is strictly weaker than truth in the standard model — a gap that persists for every consistent extension of PA.

### The Second Incompleteness Theorem: Consistency is Unprovable

The Second Incompleteness Theorem sharpens the First by identifying a specific, natural, and mathematically meaningful statement that PA cannot prove: its own consistency.

The consistency of PA can be expressed as the arithmetic sentence:

$$\text{Con}(\text{PA}) \equiv \lnot \text{Prov}(\ulcorner 0 = 1 \urcorner)$$

This asserts that the formula $0 = 1$ has no proof in PA — a direct encoding of "PA does not derive a contradiction." The Second Incompleteness Theorem states that if PA is consistent, then PA $\nvdash \text{Con}(\text{PA})$.

The proof strategy is elegant: show that the argument of the First Incompleteness Theorem — the derivation of a contradiction from the assumption PA $\vdash \gamma$ — can itself be formalized within PA. If PA could prove $\text{Con}(\text{PA})$, it could then prove $\gamma$ (by running the formalized proof of the First Theorem inside PA), contradicting what the First Theorem established.

Formalizing this argument requires the **Hilbert-Bernays-Löb (HBL) provability conditions**, also called the derivability conditions. For the provability predicate $\Box \phi \equiv \text{Prov}(\ulcorner \phi \urcorner)$, three conditions must hold:

**D1 (Necessitation).** If PA $\vdash \phi$, then PA $\vdash \Box \phi$.

**D2 (Internalization of modus ponens).** PA $\vdash \Box(\phi \to \psi) \to (\Box \phi \to \Box \psi)$.

**D3 (Self-provability of provability).** PA $\vdash \Box \phi \to \Box \Box \phi$.

Each condition expresses, within PA, a property of the provability predicate that one can verify by inspecting the construction. D1 says that actual proofs give rise to provability claims. D2 says that proofs of implications, combined with proofs of their hypotheses, yield proofs of conclusions — this mirrors the arithmetic formalization of modus ponens. D3, the deepest, says that if $\phi$ is provable, then the fact of its provability is itself provable; this requires verifying that the existence of a proof implies the PA-provable existence of that proof, which follows from the $\Sigma_1^0$ character of $\text{Prov}$ and the fact that true $\Sigma_1^0$ sentences are provable in PA.

**Proof of the Second Incompleteness Theorem.** We formalize the argument of the First Theorem inside PA. Recall that the First Theorem established: if PA is consistent, then PA $\nvdash \gamma$. In other words: $\text{Con}(\text{PA}) \to \lnot \Box \gamma$. By the fixed point construction, $\gamma \leftrightarrow \lnot \Box \gamma$, so this yields $\text{Con}(\text{PA}) \to \gamma$.

We now show PA $\vdash \text{Con}(\text{PA}) \to \gamma$. The key steps, carried out inside PA using the HBL conditions, are as follows.

Step 1: By D1, applying to the fixed-point biconditional PA $\vdash \gamma \leftrightarrow \lnot \Box \gamma$, we get PA $\vdash \Box(\gamma \leftrightarrow \lnot \Box \gamma)$.

Step 2: Suppose (within PA) that $\Box \gamma$. By D2 and the boxed biconditional, PA can derive $\Box \lnot \Box \gamma$.

Step 3: From $\Box \gamma$ and D3, we get $\Box \Box \gamma$.

Step 4: We now have both $\Box \Box \gamma$ (step 3) and $\Box \lnot \Box \gamma$ (step 2). These together yield $\Box(0 = 1)$ — provability of a contradiction — by the fact that any contradiction is provable once we have both $\Box \phi$ and $\Box \lnot \phi$ for any $\phi$.

Step 5: So within PA, $\Box \gamma \to \Box(0=1)$, which is to say $\Box \gamma \to \lnot \text{Con}(\text{PA})$. Contrapositively, $\text{Con}(\text{PA}) \to \lnot \Box \gamma$.

Step 6: By the fixed point, $\lnot \Box \gamma \leftrightarrow \gamma$, so PA $\vdash \text{Con}(\text{PA}) \to \gamma$.

Now suppose PA $\vdash \text{Con}(\text{PA})$. Then by modus ponens, PA $\vdash \gamma$. But the First Incompleteness Theorem showed that if PA is consistent, PA $\nvdash \gamma$. Assuming PA is consistent, we have a contradiction. Therefore PA $\nvdash \text{Con}(\text{PA})$. $\square$

This result is philosophically devastating for Hilbert's program. The specific strategy Hilbert had proposed — prove the consistency of strong mathematics using finitary methods, which would naturally be formalizable within a weaker system — is blocked. Any system strong enough to formalize arithmetic cannot prove its own consistency. A consistency proof for PA would require stepping outside PA to a strictly stronger system, which would then face the same problem at the next level.

---

## 3. High-Performance Optimization & Failure Modes

### Navigating the Boundaries: Where the Theorems Apply and Where They Don't

Practitioners working in proof theory, foundations of mathematics, or the design of automated theorem provers must maintain precise awareness of the scope conditions under which the incompleteness theorems apply. A common and consequential error is over-applying the theorems to systems that are either too weak or too strong for the conclusions to hold in the expected form.

The theorems require the formal system to meet two simultaneous conditions: it must be consistent, and it must be strong enough to represent all primitive recursive functions. This second condition, called being "sufficiently strong" or "interpreting Robinson Arithmetic (Q)," is the lower bound. Robinson Arithmetic is a finitely axiomatized subtheory of PA that lacks the induction schema but retains enough arithmetic to define Gödel numbering and the basic representability machinery. Any consistent system that interprets Q — meaning Q is interpretable within it — falls under the incompleteness theorems.

This matters for understanding which theories escape incompleteness. Presburger Arithmetic — first-order arithmetic with addition but without multiplication — is complete and decidable. Tarski proved this in 1929 using quantifier elimination: every formula in the language $\{+, <, 0, 1\}$ is provably equivalent in Presburger Arithmetic to a quantifier-free formula, and truth of such formulas is decidable. The absence of multiplication is not a minor technicality; it removes the ability to represent the pairing functions and exponentiation needed for Gödel numbering, putting Presburger Arithmetic below the interpretability threshold for Q. Similarly, the theory of real closed fields (Tarski's other quantifier elimination result) and Euclidean geometry are complete decidable theories. Incompleteness does not reach them.

On the other end, theories much stronger than PA — such as $\text{ZFC}$ (Zermelo-Fraenkel set theory with Choice) — do interpret PA and are therefore subject to incompleteness. The sentence Con(PA) is not only unprovable in PA but is in fact provable in ZFC (assuming ZFC is consistent), since ZFC has access to stronger axioms like the axiom of infinity and the axiom schema of replacement. However, Con(ZFC) is unprovable in ZFC, by the second theorem applied to ZFC itself. This yields an infinite tower: each system can prove the consistency of weaker systems but not of itself.

### The $\Sigma_1^0$ Completeness Lemma and Its Operational Significance

A key operational fact — frequently underappreciated but essential for practitioners working with proof assistants and formal verification — is that the incompleteness gap affects only statements of sufficient logical complexity. Specifically, every true $\Sigma_1^0$ sentence (a sentence of the form $\exists x\, R(x)$ where $R$ is primitive recursive) is provable in PA. This follows from the fact that if $\exists x\, R(x)$ is true in $\mathbb{N}$, then some specific $n$ witnesses it, $R(\bar{n})$ holds, PA proves $R(\bar{n})$ (since $R$ is representable and the computation halts), and existential introduction gives PA $\vdash \exists x\, R(x)$.

The Gödel sentence $\gamma$ is a $\Pi_1^0$ sentence (a universal sentence of the form $\forall x\, R(x)$ where $R$ is primitive recursive): it asserts that no natural number codes a proof of $\gamma$ in PA. The true but unprovable statements lie at and above the $\Pi_1^0$ level in the arithmetical hierarchy. All true $\Sigma_1^0$ statements, including all true statements of the form "this program halts on this input," are provable. This aligns with the well-known connection: the $\Sigma_1^0$ sentences are exactly the recursively enumerable predicates, and PA's provability set is itself recursively enumerable. The incompleteness gap begins precisely at the $\Pi_1^0$ level, mirroring the undecidability of the Halting Problem (which is also $\Pi_1^0$-complete).

### Consistency Strength and the Ordinal Analysis Program

A sophisticated operational framework for measuring the "strength" of formal systems — going well beyond the binary consistent/inconsistent distinction — is the program of ordinal analysis, initiated by Gentzen in 1936. Gentzen proved the consistency of PA using transfinite induction up to the ordinal $\varepsilon_0$ (the least ordinal satisfying $\omega^\alpha = \alpha$), carried out within a weaker system called Primitive Recursive Arithmetic (PRA) augmented with $\varepsilon_0$-induction. This consistency proof does not contradict the Second Incompleteness Theorem because transfinite induction up to $\varepsilon_0$ is not provable within PA itself — it is an instance of a principle stronger than anything PA can establish.

Each consistent, recursively axiomatized theory extending PA has an associated **proof-theoretic ordinal**: the supremum of the ordinals whose well-foundedness the theory can prove. PA's proof-theoretic ordinal is $\varepsilon_0$. For stronger theories like ATR$_0$ (Arithmetical Transfinite Recursion), the ordinal is $\Gamma_0$. This hierarchy of ordinals provides a fine-grained measure of consistency strength that operationalizes the tower of incompleteness. When one asks "how much stronger than PA is a given formal system?", ordinal analysis gives a precise, quantitative answer.

### Common Failure Modes in Proof-Theoretic Reasoning

Several subtle errors recur in practice when logicians, mathematicians, or computer scientists apply the incompleteness theorems to concrete problems.

The first and most common confusion is conflating truth with provability. Gödel's First Theorem establishes the existence of true-but-unprovable sentences, but it does so relative to the standard model $\mathbb{N}$ — the intended interpretation of PA. There exist non-standard models of PA in which $\gamma$ is false. In a non-standard model, the "proof" of $\gamma$ that the model thinks exists is coded by a non-standard integer: an integer larger than every standard natural number, unreachable by any finite proof in the real world. The sentence $\gamma$ is therefore true in $\mathbb{N}$ and false in certain non-standard models, which is exactly the behavior one expects from a formally independent sentence. When one says $\gamma$ is "true," one always means true in the standard model, not true in every model of PA.

The second failure mode involves an incorrect application of the Second Incompleteness Theorem to relative consistency proofs. The theorem says a consistent system $T$ cannot prove $\text{Con}(T)$ using resources available within $T$. It does not prevent $T$ from proving $\text{Con}(T')$ for a strictly weaker theory $T'$. ZFC proves Con(PA). ZFC + a large cardinal axiom proves Con(ZFC). These are legitimate relative consistency proofs and are not blocked by the second theorem. The error occurs when someone argues "ZFC proves Con(ZFC)" — this would require ZFC to be inconsistent, by the second theorem.

The third failure mode is in the design of formal verification systems and automated provers. A type theory or proof assistant (Coq, Lean, Agda) is a formal system subject to the incompleteness theorems. The Curry-Howard correspondence identifies proofs with programs and propositions with types, but the underlying logical framework is typically a dependent type theory such as the Calculus of Inductive Constructions (CIC). CIC is a formal system considerably stronger than PA — it can prove Con(PA) and much more — but it too has its Gödel sentence and cannot prove its own consistency. A proof assistant developer must accept that the system's consistency cannot be certified from within the system; it rests on the community's accumulated trust in the design and on relative consistency results to outer models. The practical implication is that any claim of "absolute" verification is philosophically untenable; what one achieves is verification relative to the correctness and consistency of the proof assistant's kernel.

A fourth, more technical failure involves the use of the provability predicate in contexts where the HBL conditions are not verified. The derivability conditions D1–D3 are essential to the proof of the Second Incompleteness Theorem. There exist provability-like predicates — sometimes called "Rosser provability predicates" or pathological variants — for which one or more of the HBL conditions fail. For such predicates, the second theorem may not hold in its standard form. This is not a loophole in the theorem; it reflects that the HBL conditions are part of the theorem's hypotheses, and proof assistants or logicians constructing non-standard provability predicates for specialized purposes must verify these conditions explicitly rather than assuming them.

### Löb's Theorem and Reflection Principles

A consequential result downstream of the HBL framework is **Löb's Theorem** (1955), which states: if PA $\vdash \Box \phi \to \phi$, then PA $\vdash \phi$. In other words, the only formulas $\phi$ for which PA can prove "if $\phi$ is provable then $\phi$" are those that PA already proves outright.

**Proof.** Suppose PA $\vdash \Box \phi \to \phi$. Apply the Diagonal Lemma with $\psi(x) \equiv \Box x \to \phi$ to obtain a sentence $\lambda$ such that PA $\vdash \lambda \leftrightarrow (\Box \lambda \to \phi)$. By D1 applied to this biconditional, PA $\vdash \Box(\lambda \leftrightarrow (\Box \lambda \to \phi))$. Using D2 repeatedly, we get PA $\vdash \Box \lambda \to \Box(\Box \lambda \to \phi)$ and PA $\vdash \Box \lambda \to (\Box \Box \lambda \to \Box \phi)$. By D3, PA $\vdash \Box \lambda \to \Box \Box \lambda$. Combining: PA $\vdash \Box \lambda \to \Box \phi$. By hypothesis, PA $\vdash \Box \phi \to \phi$, so PA $\vdash \Box \lambda \to \phi$. By the fixed point, PA $\vdash \lambda$. Applying D1, PA $\vdash \Box \lambda$. By the derivation above (PA $\vdash \Box \lambda \to \phi$), we conclude PA $\vdash \phi$. $\square$

Löb's Theorem has a striking corollary: PA $\nvdash \Box \phi \to \phi$ for any $\phi$ that PA does not prove. In particular, taking $\phi \equiv \bot$ (or $0 = 1$), we get PA $\nvdash \Box \bot \to \bot$, which is exactly PA $\nvdash \lnot \Box \bot$, i.e., PA $\nvdash \text{Con}(\text{PA})$ — the Second Incompleteness Theorem as a special case. The theorem also characterizes the **reflection principles** that PA can and cannot internalize: PA can prove $\Box \phi \to \phi$ only when it already has an independent proof of $\phi$. This is a precise, operational constraint on the self-reflective capacity of any formal system extending PA.

### The Arithmetical Hierarchy and Undecidability

The machinery developed in this lesson connects directly to computability theory through the arithmetical hierarchy of definable sets of natural numbers. A set $A \subseteq \mathbb{N}$ is $\Sigma_1^0$ (recursively enumerable) if its membership predicate is $\exists x\, R(x, n)$ for primitive recursive $R$. It is $\Pi_1^0$ if its complement is $\Sigma_1^0$. It is $\Delta_1^0$ (recursive, or decidable) if it is both $\Sigma_1^0$ and $\Pi_1^0$.

The set of Gödel numbers of PA-provable sentences is $\Sigma_1^0$: a sentence is provable iff a proof exists, and the existence of a proof is verifiable by an enumeration procedure. The set of Gödel numbers of PA-refutable sentences (sentences whose negations are provable) is also $\Sigma_1^0$. The set of independent sentences — provable in neither direction — is therefore $\Pi_1^0$ when viewed from outside the system.

The Halting Problem is $\Sigma_1^0$-complete: a Turing machine halts on input $n$ iff there exists a computation history certifying this, which is a primitive recursive check on a finite object. Its complement — "this machine does not halt" — is $\Pi_1^0$ and undecidable. The direct correspondence with Gödel's construction is not coincidental; Turing's 1936 proof of the undecidability of the Halting Problem and Church's undecidability of provability in first-order logic were both directly inspired by Gödel's techniques, and all three results can be seen as manifestations of the same diagonalization argument applied in different settings.

For practitioners building decision procedures, type checkers, or automated proof systems, the arithmetical hierarchy delineates the boundary of what can be automated. Any decision procedure for a problem at or above the $\Pi_1^0$ level in the hierarchy cannot be both sound and complete. SAT solvers, SMT solvers, and type inference algorithms achieve tractability by restricting to decidable fragments — bounded arithmetic, linear arithmetic, or type theories with termination-guaranteed computation — deliberately staying below the threshold where incompleteness bites.

### Gödel's Theorems in Contemporary Proof Assistants

The abstractions developed across this lesson have direct, grounded manifestations in modern proof assistant engineering. In Lean 4, the core type theory is a variant of CIC with universe polymorphism and quotient types. The kernel is a small, trusted piece of code that checks proof terms for type correctness; all higher-level tactics reduce to this kernel. The Lean community has formalized Gödel's First Incompleteness Theorem in Lean itself — a project due to Paulson and subsequently refined — using the representability of primitive recursive functions within the type theory and constructing an explicit Gödel sentence for a formalized version of PA encoded in Lean's type theory.

This formalization exercise is simultaneously a validation of the proof's correctness and a demonstration of its constructive character. The Diagonal Lemma, the construction of $\text{Proof}(p, \phi)$, the HBL conditions, and the derivation of $\gamma$ are all explicitly computable transformations on data structures representing formal proofs. When one runs a Lean proof of the First Incompleteness Theorem, one is not merely asserting the theorem — one is executing the Gödel numbering scheme, constructing the fixed point, and verifying the logical derivation in a type-theoretically certified environment. The theorem is not an abstraction; it is a program, and the incompleteness it describes is a structurally guaranteed feature of the type-theoretic universe in which the proof assistant itself lives.

This is the deepest practical lesson of Gödel's work: the limits of formal proof are not bugs to be fixed or edges to be engineered around. They are intrinsic to the nature of expressive formal systems, grounded in the same diagonalization that connects computability, logic, and the structure of mathematical truth. Any practitioner working at the foundations — whether designing a proof assistant, reasoning about program verification, or constructing a type theory — works permanently in the shadow of these limits and builds better by understanding their exact shape.
