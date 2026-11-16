# Lesson 2: Proof Systems for Propositional Logic

## 1. First-Principles Intuition & Invariants

The question that animates this entire lesson is deceptively simple: what does it mean to *prove* something? In everyday mathematical practice, a proof is a convincing argument, a chain of reasoning that compels assent. But mathematical logic demands more than psychological persuasion. It demands that we make the notion of proof itself a mathematical object, something we can count, classify, manipulate, and reason about with the same rigor we apply to groups or topological spaces. The formal study of proof systems is the discipline that achieves this, and propositional logic is the arena in which every essential idea first crystallizes with perfect clarity.

To understand why formalization matters, consider the semantic picture we inherit from truth tables and valuations. A propositional formula $\varphi$ over variables $p_1, p_2, \ldots, p_n$ is a *tautology* if every truth-value assignment $v : \{p_1, \ldots, p_n\} \to \{0, 1\}$ satisfies $v(\varphi) = 1$. A set of premises $\Gamma$ *semantically entails* $\varphi$, written $\Gamma \models \varphi$, if every valuation that satisfies every formula in $\Gamma$ also satisfies $\varphi$. This semantic picture is clean and intuitive, but it is computational in nature: to verify $\Gamma \models \varphi$ directly, one enumerates all $2^n$ valuations. It says nothing about *why* a consequence holds, only that it does, in every possible world. The syntactic picture, by contrast, asks whether $\varphi$ can be derived from $\Gamma$ by applying a finite sequence of inference rules, operating solely on the symbolic shape of formulas. This is the derivability relation, written $\Gamma \vdash \varphi$.

The relationship between $\models$ and $\vdash$ is the central invariant of proof theory. **Soundness** asserts that the syntactic machinery never overreaches: if $\Gamma \vdash \varphi$, then $\Gamma \models \varphi$. Every formula the proof system can derive is genuinely entailed. **Completeness** asserts the converse: if $\Gamma \models \varphi$, then $\Gamma \vdash \varphi$. No semantic truth escapes the reach of formal derivation. Together, soundness and completeness establish that $\vdash$ and $\models$ are coextensive for propositional logic, meaning the symbolic game of proof-writing is not a mere syntactic ritual but an exact reflection of the semantic universe of truth assignments. This equivalence is the cornerstone on which formal mathematics rests, and in this lesson we will construct it from the ground up across three distinct proof systems, each illuminating a different facet of the same underlying reality.

The three major architectures for propositional proof systems each embody a distinct philosophy. **Hilbert-style systems** minimize the number of inference rules, reducing derivation to almost pure application of axioms. They are lean and mathematically elegant, optimized for metatheoretical analysis rather than human use. **Natural deduction**, introduced by Gerhard Gentzen in 1935 and further developed by Dag Prawitz, organizes proof around the introduction and elimination of each logical connective, mirroring the structure of informal mathematical reasoning. It is the system closest to how mathematicians actually think. **Sequent calculus**, also due to Gentzen, operates on *sequents*, which are pairs of formula sets representing the logical judgment that the conjunction of the left side entails the disjunction of the right side. Sequent calculus exposes the deepest structural properties of logic, including the celebrated *Cut Elimination Theorem*, and forms the foundation for proof-search algorithms and automated theorem proving.

Before we enter each system, we fix the syntax of the language $\mathcal{L}$ of propositional logic. We take a countably infinite set of propositional variables $\mathsf{Var} = \{p, q, r, p_1, p_2, \ldots\}$. The well-formed formulas are defined inductively: every variable is a formula; if $\varphi$ and $\psi$ are formulas, then so are $\neg \varphi$, $(\varphi \land \psi)$, $(\varphi \lor \psi)$, and $(\varphi \to \psi)$. We treat $\bot$ (falsum) as a nullary connective and define $\top \equiv \neg\bot$. This language is the shared substrate across all three systems; what differs is the derivation machinery built on top of it.

---

## 2. Core Architecture & Mechanics

### 2.1 The Hilbert-Style Axiom System

The Hilbert-style calculus for classical propositional logic, often called $\mathsf{H}$ or the Łukasiewicz–Tarski system, achieves a radical economy of means. It has exactly one inference rule, *modus ponens*:

$$\frac{\varphi \quad \varphi \to \psi}{\psi} \quad (\text{MP})$$

All the logical content of the system is instead encoded in a finite set of axiom *schemas*, each of which stands for infinitely many formulas obtained by substituting arbitrary formulas for its metavariables. A standard complete basis consists of the following three axiom schemas:

$$\mathbf{A1}: \varphi \to (\psi \to \varphi)$$

$$\mathbf{A2}: (\varphi \to (\psi \to \chi)) \to ((\varphi \to \psi) \to (\varphi \to \chi))$$

$$\mathbf{A3}: (\neg\psi \to \neg\varphi) \to (\varphi \to \psi)$$

A *Hilbert derivation* of $\varphi$ from a set of premises $\Gamma$ is a finite sequence of formulas $\varphi_1, \varphi_2, \ldots, \varphi_n$ such that $\varphi_n = \varphi$ and every $\varphi_i$ is either a member of $\Gamma$, an instance of one of **A1–A3**, or follows from two earlier formulas $\varphi_j, \varphi_k$ (where $j, k < i$) by modus ponens with $\varphi_k = \varphi_j \to \varphi_i$.

To feel the texture of this system, we work through the derivation of the identity law $p \to p$ from no premises whatsoever, since this formula is a tautology and completeness will guarantee it must be derivable. The argument is a five-line derivation:

**Claim:** $\vdash p \to p$

The key strategic insight is to instantiate **A2** with $\varphi := p$, $\psi := (p \to p)$, $\chi := p$:

$$\text{Line 1:} \quad (p \to ((p \to p) \to p)) \to ((p \to (p \to p)) \to (p \to p)) \quad [\mathbf{A2}]$$

Next, instantiate **A1** with $\varphi := p$ and $\psi := (p \to p)$:

$$\text{Line 2:} \quad p \to ((p \to p) \to p) \quad [\mathbf{A1}]$$

Apply modus ponens to Lines 2 and 1, noting that Line 2 is precisely the antecedent of Line 1:

$$\text{Line 3:} \quad (p \to (p \to p)) \to (p \to p) \quad [\text{MP on 2, 1}]$$

Now instantiate **A1** with $\varphi := p$ and $\psi := p$:

$$\text{Line 4:} \quad p \to (p \to p) \quad [\mathbf{A1}]$$

Apply modus ponens to Lines 4 and 3:

$$\text{Line 5:} \quad p \to p \quad [\text{MP on 4, 3}]$$

This derivation is simultaneously illuminating and maddening. It reveals with perfect clarity why Hilbert systems, while parsimonious, are almost entirely impractical for humans to construct proofs in. Every step requires choosing which axiom schema to instantiate and with which substitution, a task that is entirely non-obvious. The system is nonetheless invaluable for metatheoretical work, because having only one rule means that inductive arguments over proof structure are extremely clean: every inductive step reduces either to "the last formula was an axiom" or "the last formula was produced by modus ponens."

The fundamental metatheorem that makes Hilbert-system proofs tractable is the **Deduction Theorem**:

> **Theorem (Deduction Theorem):** $\Gamma, \varphi \vdash \psi$ if and only if $\Gamma \vdash \varphi \to \psi$.

This theorem allows us to work with hypotheses freely: to prove $\varphi \to \psi$, we may *assume* $\varphi$ as a temporary premise and try to derive $\psi$. The theorem's proof is itself a constructive transformation: given a derivation $D$ of $\psi$ from $\Gamma \cup \{\varphi\}$, one constructs a derivation $D'$ of $\varphi \to \psi$ from $\Gamma$ alone by induction on the length of $D$. Specifically, for each line $\varphi_i$ of $D$, the transformed derivation $D'$ produces a derivation of $\varphi \to \varphi_i$ from $\Gamma$. If $\varphi_i$ is an axiom or a member of $\Gamma$, one uses an instantiation of **A1** to derive $\varphi_i \to (\varphi \to \varphi_i)$ and then applies modus ponens. If $\varphi_i = \varphi$, one uses the already-established identity $\varphi \to \varphi$. If $\varphi_i$ was derived by MP from $\varphi_j$ and $\varphi_j \to \varphi_i$, one uses the inductive hypotheses $\varphi \to \varphi_j$ and $\varphi \to (\varphi_j \to \varphi_i)$ together with an instantiation of **A2** to derive $\varphi \to \varphi_i$. The forward direction of the Deduction Theorem is easy: given $\Gamma \vdash \varphi \to \psi$, add $\varphi$ as a premise and apply MP.

### 2.2 Natural Deduction

Natural deduction, as designed by Gentzen, removes the artificiality of a fixed axiom basis and instead articulates the logical meaning of each connective through paired *introduction* and *elimination* rules. The introduction rule for a connective tells you how to prove a formula whose main connective is that symbol; the elimination rule tells you how to use such a formula once you have it. This duality, proof construction and proof use, is the structural engine of the system.

We write natural deduction derivations as trees (or as Fitch-style columns with indentation), where leaves are either axioms or *hypotheses* that may be discharged at certain points. The judgment takes the form of a formula $\varphi$ labeled with the set of open (undischarged) hypotheses $\Gamma$ on which the derivation currently depends.

The rules for implication are foundational. The *introduction rule* for $\to$, written ${\to}\mathsf{I}$, says: if, by assuming $\varphi$ as a hypothesis, you can derive $\psi$, then you may conclude $\varphi \to \psi$ and *discharge* (close off) the hypothesis $\varphi$:

$$\frac{\begin{array}{c} [\varphi]^u \\ \vdots \\ \psi \end{array}}{\varphi \to \psi} \,{\to}\mathsf{I}^u$$

The superscript $u$ is a *discharge label*, tracking which assumption is being closed. The elimination rule for $\to$ is simply modus ponens:

$$\frac{\varphi \to \psi \quad \varphi}{\psi} \,{\to}\mathsf{E}$$

For conjunction, the introduction rule reflects that to prove $\varphi \land \psi$ you must prove both conjuncts, while the two elimination rules reflect that from a conjunction you can extract either component:

$$\frac{\varphi \quad \psi}{\varphi \land \psi} \,{\land}\mathsf{I} \qquad \frac{\varphi \land \psi}{\varphi} \,{\land}\mathsf{E}_1 \qquad \frac{\varphi \land \psi}{\psi} \,{\land}\mathsf{E}_2$$

For disjunction, the introduction rules are asymmetric in a revealing way: a single proof of $\varphi$ suffices to introduce either $\varphi \lor \psi$ or $\chi \lor \varphi$ for any $\psi$ or $\chi$. The elimination rule, *proof by cases*, is more demanding: to use $\varphi \lor \psi$ to conclude $\chi$, one must provide a derivation of $\chi$ from $\varphi$ *and* a separate derivation of $\chi$ from $\psi$:

$$\frac{\varphi \lor \psi \quad \begin{array}{c} [\varphi]^u \\ \vdots \\ \chi \end{array} \quad \begin{array}{c} [\psi]^v \\ \vdots \\ \chi \end{array}}{\chi} \,{\lor}\mathsf{E}^{u,v}$$

Negation in classical logic is handled via the *reductio ad absurdum* rule, also called the *classical rule* because it distinguishes classical from intuitionistic logic: if from the assumption $\neg\varphi$ you can derive $\bot$ (absurdity), then you may conclude $\varphi$ and discharge $\neg\varphi$:

$$\frac{\begin{array}{c} [\neg\varphi]^u \\ \vdots \\ \bot \end{array}}{\varphi} \,\mathsf{RAA}^u$$

Together with the *ex falso quodlibet* rule $\frac{\bot}{\varphi}$ (explosion), and the elimination rule for negation $\frac{\varphi \quad \neg\varphi}{\bot}$, these rules complete the classical natural deduction system $\mathsf{NK}$.

To see natural deduction at work in a nontrivial proof, consider the derivation of the classical tautology $((\varphi \to \psi) \to \varphi) \to \varphi$, known as *Peirce's Law*. It is impossible to derive without the classical rule, so its proof demonstrates where intuitionistic and classical logic genuinely diverge.

**Claim:** $\vdash ((\varphi \to \psi) \to \varphi) \to \varphi$

We work using ${\to}\mathsf{I}$, ${\to}\mathsf{E}$, and $\mathsf{RAA}$. By ${\to}\mathsf{I}$, it suffices to assume $((\varphi \to \psi) \to \varphi)$ as hypothesis $[H_1]^u$ and derive $\varphi$. We apply $\mathsf{RAA}$: assume $\neg\varphi$ as hypothesis $[H_2]^v$ and derive $\bot$. To obtain $\bot$ from $\neg\varphi$, it suffices by ${\to}\mathsf{E}$ applied to $H_1$ to derive $(\varphi \to \psi) \to \varphi$ and from it produce $\varphi$—but we cannot do that without circularity. Instead, by ${\to}\mathsf{I}$, we derive $\varphi \to \psi$ by assuming $[\varphi]^w$, applying $\mathsf{RAA}$ or $\mathsf{ex\ falso}$: from $[\varphi]^w$ and $H_2: \neg\varphi$, derive $\bot$ by $\neg\mathsf{E}$, then derive $\psi$ by $\mathsf{EFQ}$, and discharge $[\varphi]^w$ to obtain $\varphi \to \psi$. Now apply ${\to}\mathsf{E}$ to $H_1: (\varphi\to\psi)\to\varphi$ and the derived $\varphi\to\psi$ to obtain $\varphi$. Apply $\neg\mathsf{E}$ to $\varphi$ and $H_2: \neg\varphi$ to obtain $\bot$. Discharge $H_2$ by $\mathsf{RAA}$ to obtain $\varphi$. Discharge $H_1$ by ${\to}\mathsf{I}$ to obtain $((\varphi\to\psi)\to\varphi)\to\varphi$. $\square$

The Fitch-style column form of this derivation makes the discharge structure visually transparent:

```
1  | (φ→ψ)→φ          [assumption H1, opens subproof for →I]
2  | | ¬φ             [assumption H2, opens subproof for RAA]
3  | | | φ            [assumption H3, opens subproof for →I]
4  | | | ⊥            [¬E on 3, 2]
5  | | | ψ            [EFQ on 4]
6  | | φ→ψ            [→I, discharges H3 at line 3]
7  | | φ              [→E on 1, 6]
8  | | ⊥              [¬E on 7, 2]
9  | φ                [RAA, discharges H2 at line 2]
10 (φ→ψ)→φ)→φ        [→I, discharges H1 at line 1]
```

### 2.3 Sequent Calculus

Sequent calculus, the third and most architecturally powerful of the three systems, operates on a different kind of syntactic object. A *sequent* is an expression of the form:

$$\Gamma \Rightarrow \Delta$$

where $\Gamma$ and $\Delta$ are finite (possibly empty) *multisets* of formulas, called the *antecedent* and *succedent* respectively. The intended semantic reading is: the conjunction of all formulas in $\Gamma$ entails the disjunction of all formulas in $\Delta$. So $\varphi, \psi \Rightarrow \chi, \xi$ means $(\varphi \land \psi) \to (\chi \lor \xi)$. An empty antecedent is interpreted as $\top$ (tautologically true), so $\Rightarrow \varphi$ means $\varphi$ is a tautology. An empty succedent is interpreted as $\bot$, so $\Gamma \Rightarrow$ means $\Gamma$ is unsatisfiable.

The calculus $\mathsf{LK}$, Gentzen's original sequent calculus for classical logic, has two categories of rules. The *identity axiom* and *cut rule* govern the global structure of derivations:

$$\frac{}{\varphi \Rightarrow \varphi} \,\mathsf{Id} \qquad \frac{\Gamma \Rightarrow \Delta, \varphi \quad \varphi, \Gamma' \Rightarrow \Delta'}{\Gamma, \Gamma' \Rightarrow \Delta, \Delta'} \,\mathsf{Cut}$$

The cut rule is the sequent-calculus analogue of modus ponens and of the use of lemmas: a formula $\varphi$ proved on the right of one sequent is consumed on the left of another. The *structural rules* govern the administrative behavior of antecedents and succedents: weakening allows the introduction of irrelevant formulas, contraction allows the merging of duplicate formulas, and exchange allows reordering (though exchange is usually omitted when $\Gamma$ and $\Delta$ are treated as sets rather than lists).

$$\frac{\Gamma \Rightarrow \Delta}{\varphi, \Gamma \Rightarrow \Delta} \,\mathsf{WL} \qquad \frac{\Gamma \Rightarrow \Delta}{\Gamma \Rightarrow \Delta, \varphi} \,\mathsf{WR}$$

$$\frac{\varphi, \varphi, \Gamma \Rightarrow \Delta}{\varphi, \Gamma \Rightarrow \Delta} \,\mathsf{CL} \qquad \frac{\Gamma \Rightarrow \Delta, \varphi, \varphi}{\Gamma \Rightarrow \Delta, \varphi} \,\mathsf{CR}$$

The *logical rules* come in left and right versions for each connective, and they are where the logical content lives. For negation:

$$\frac{\Gamma \Rightarrow \Delta, \varphi}{\neg\varphi, \Gamma \Rightarrow \Delta} \,\neg\mathsf{L} \qquad \frac{\varphi, \Gamma \Rightarrow \Delta}{\Gamma \Rightarrow \Delta, \neg\varphi} \,\neg\mathsf{R}$$

For implication, the right rule reflects the standard proof strategy of assuming the antecedent and proving the consequent:

$$\frac{\Gamma \Rightarrow \Delta, \varphi \quad \psi, \Gamma' \Rightarrow \Delta'}{\varphi \to \psi, \Gamma, \Gamma' \Rightarrow \Delta, \Delta'} \,{\to}\mathsf{L} \qquad \frac{\varphi, \Gamma \Rightarrow \Delta, \psi}{\Gamma \Rightarrow \Delta, \varphi \to \psi} \,{\to}\mathsf{R}$$

For conjunction:

$$\frac{\varphi, \Gamma \Rightarrow \Delta}{\varphi \land \psi, \Gamma \Rightarrow \Delta} \,{\land}\mathsf{L}_1 \qquad \frac{\psi, \Gamma \Rightarrow \Delta}{\varphi \land \psi, \Gamma \Rightarrow \Delta} \,{\land}\mathsf{L}_2 \qquad \frac{\Gamma \Rightarrow \Delta, \varphi \quad \Gamma \Rightarrow \Delta, \psi}{\Gamma \Rightarrow \Delta, \varphi \land \psi} \,{\land}\mathsf{R}$$

A derivation in $\mathsf{LK}$ is a tree of sequents, with the axioms $\varphi \Rightarrow \varphi$ at the leaves and the conclusion at the root. Each internal node is an application of one rule to one or two sequent premises. The derivation structure is illustrated below:

```
      ─────────────── Id          ─────────────── Id
       p ⇒ p                       q ⇒ q
      ─────────────── WL          ─────────────── WR
       p, q ⇒ p                   q ⇒ q, p
      ─────────────────────────────────────────── →L
       (p→q)→p, p→q ⇒ p
      ─────────────────────────────────────────── ...
```

The pinnacle of sequent calculus metatheory is Gentzen's **Cut Elimination Theorem** (the *Hauptsatz*):

> **Theorem (Cut Elimination):** Every sequent derivable in $\mathsf{LK}$ is derivable in $\mathsf{LK}$ without the cut rule.

The proof proceeds by defining a measure of a derivation that counts, in some lexicographic ordering, the *cut rank* (the complexity of the cut formula) and the number of cuts. One then shows that any application of the cut rule can be systematically eliminated by transforming the derivation, potentially at the cost of making it longer, but always strictly reducing the measure. The transformation has cases for each possible last rule applied in each of the two subderivations feeding the cut, and the most complex case, the *key case*, handles the situation where the cut formula was the principal formula of the last rule in both subderivations: here one replaces the single cut with a tree of cuts on strictly simpler subformulas, which the inductive hypothesis then handles.

Cut elimination has enormous consequences. It establishes the *subformula property*: in a cut-free proof of $\Gamma \Rightarrow \Delta$, every formula appearing anywhere in the derivation is a subformula of some formula in $\Gamma \cup \Delta$. This makes proof search *analytic*: rather than introducing arbitrary lemmas (via cut), a proof-search algorithm need only work with subformulas of the goal. This is the theoretical basis for the *tableau method* and *resolution*, the two main algorithms underlying automated propositional and first-order theorem provers.

### 2.4 Soundness and Completeness

We now prove soundness and completeness for the Hilbert system $\mathsf{H}$, since the argument generalizes mutatis mutandis to natural deduction and sequent calculus, and the Hilbert setting keeps the proof structure maximally transparent.

**Theorem (Soundness of $\mathsf{H}$):** If $\Gamma \vdash_\mathsf{H} \varphi$, then $\Gamma \models \varphi$.

*Proof.* By induction on the length $n$ of the derivation. For the base case $n = 1$, the formula $\varphi$ is either a premise in $\Gamma$ (trivially $\Gamma \models \varphi$) or an axiom instance. We verify the three axiom schemas are tautologies by truth-table or by algebraic argument. For **A1**, $\varphi \to (\psi \to \varphi)$: if $v(\varphi) = 0$, the conditional is true vacuously. If $v(\varphi) = 1$, then $v(\psi \to \varphi) = 1$ because $v(\varphi) = 1$, so the whole formula is true. For **A2**, one verifies the eight cases of the truth table for $(\varphi, \psi, \chi)$ systematically, confirming the value is always 1. For **A3**, $(\neg\psi \to \neg\varphi) \to (\varphi \to \psi)$: this is the contrapositive law, true in classical logic by the two-element Boolean algebra. For the inductive step, suppose $\varphi_n$ was obtained by modus ponens from $\varphi_j = \alpha$ and $\varphi_k = \alpha \to \varphi_n$ where $j, k < n$. By inductive hypothesis, $\Gamma \models \alpha$ and $\Gamma \models \alpha \to \varphi_n$. Let $v$ be any valuation satisfying all of $\Gamma$. Then $v(\alpha) = 1$ and $v(\alpha \to \varphi_n) = 1$. Since $v(\alpha \to \varphi_n) = 1$ and $v(\alpha) = 1$, we have $v(\varphi_n) = 1$. So $\Gamma \models \varphi_n$. $\square$

**Theorem (Completeness of $\mathsf{H}$):** If $\Gamma \models \varphi$, then $\Gamma \vdash_\mathsf{H} \varphi$.

The proof of completeness is more involved and proceeds via the construction of a *canonical model*. We use the method of *maximal consistent sets*, following the Lindenbaum–Henkin argument. We say a set $\Gamma$ is *consistent* if there is no formula $\alpha$ such that $\Gamma \vdash \alpha$ and $\Gamma \vdash \neg\alpha$, equivalently $\Gamma \not\vdash \bot$.

**Lemma (Lindenbaum's Lemma):** Every consistent set $\Gamma$ can be extended to a *maximally consistent set* $\Gamma^+$, which is a consistent set $\Gamma^+ \supseteq \Gamma$ such that for every formula $\alpha$, either $\alpha \in \Gamma^+$ or $\neg\alpha \in \Gamma^+$.

*Proof.* Enumerate all propositional formulas as $\alpha_0, \alpha_1, \alpha_2, \ldots$ (possible since the language is countable). Define $\Gamma_0 = \Gamma$. At stage $i+1$, set $\Gamma_{i+1} = \Gamma_i \cup \{\alpha_i\}$ if this set is consistent, and $\Gamma_{i+1} = \Gamma_i \cup \{\neg\alpha_i\}$ otherwise. At least one of $\Gamma_i \cup \{\alpha_i\}$ and $\Gamma_i \cup \{\neg\alpha_i\}$ must be consistent: if both were inconsistent, we would have $\Gamma_i \vdash \neg\alpha_i$ and $\Gamma_i \vdash \alpha_i$ (by the Deduction Theorem and double negation elimination, which is derivable in $\mathsf{H}$ via **A3**), contradicting the consistency of $\Gamma_i$. Set $\Gamma^+ = \bigcup_{i \geq 0} \Gamma_i$. This union is consistent (any finite derivation of a contradiction would use formulas from some finite stage $\Gamma_N$, contradicting its consistency), and by construction, every formula $\alpha_i$ has either $\alpha_i \in \Gamma^+$ or $\neg\alpha_i \in \Gamma^+$. $\square$

Now we construct the canonical valuation $v^*$ from $\Gamma^+$ by setting $v^*(p) = 1$ if and only if $p \in \Gamma^+$ for each propositional variable $p$. One then proves by structural induction on formulas that for every formula $\alpha$:

$$v^*(\alpha) = 1 \iff \alpha \in \Gamma^+$$

The base case is the definition of $v^*$. For $\neg\alpha$: since $\Gamma^+$ is maximally consistent, $\neg\alpha \in \Gamma^+$ iff $\alpha \notin \Gamma^+$, so $v^*(\neg\alpha) = 1 \iff \neg\alpha \in \Gamma^+ \iff \alpha \notin \Gamma^+ \iff v^*(\alpha) = 0$, which is correct. For $\alpha \to \beta$: one shows using the maximality and consistency of $\Gamma^+$ together with properties of $\mathsf{H}$-derivability that $\alpha \to \beta \in \Gamma^+$ iff either $\alpha \notin \Gamma^+$ or $\beta \in \Gamma^+$, which corresponds exactly to $v^*(\alpha \to \beta) = 1$.

With this in hand, suppose $\Gamma \models \varphi$ but $\Gamma \not\vdash \varphi$. Then $\Gamma \cup \{\neg\varphi\}$ is consistent (if it were inconsistent, then $\Gamma \vdash \neg\neg\varphi$, so $\Gamma \vdash \varphi$ by double negation, contradicting the assumption). By Lindenbaum's Lemma, extend $\Gamma \cup \{\neg\varphi\}$ to a maximally consistent set $\Gamma^+$. The canonical valuation $v^*$ satisfies all of $\Gamma$ (since $\Gamma \subseteq \Gamma^+$ and $v^*$ satisfies every element of $\Gamma^+$) and satisfies $\neg\varphi$ (since $\neg\varphi \in \Gamma^+$), so $v^*(\varphi) = 0$. This contradicts $\Gamma \models \varphi$. Therefore $\Gamma \vdash \varphi$. $\square$

### 2.5 Decidability of Tautology Checking

Propositional logic is *decidable*: there is an algorithm that, given any formula $\varphi$ with variables $p_1, \ldots, p_n$, terminates and correctly answers whether $\varphi$ is a tautology. The brute-force algorithm evaluates $\varphi$ under all $2^n$ truth-value assignments, running in time $O(2^n \cdot |\varphi|)$ where $|\varphi|$ is the formula length. This is an exponential-time procedure in the worst case.

The more structurally illuminating decision procedure uses the *analytic tableau method*, which is in direct correspondence with the cut-free sequent calculus. To decide whether $\varphi$ is a tautology, we attempt to build a refutation of $\neg\varphi$: we begin with the sequent $\neg\varphi \Rightarrow \bot$ (equivalently, with a *tableau* rooted at $\neg\varphi$) and apply decomposition rules that break compound formulas into their components. A branch of the tableau is *closed* if it contains both $\alpha$ and $\neg\alpha$ for some formula $\alpha$, representing a semantic contradiction. The tableau *closes* if every branch closes. The fundamental theorem of the tableau method is: $\varphi$ is a tautology if and only if every branch of the completed tableau for $\neg\varphi$ closes. The *completeness* of the tableau method is precisely the completeness of cut-free $\mathsf{LK}$, which follows from cut elimination.

The complexity class of propositional tautology checking is **co-NP**: a formula $\varphi$ is *not* a tautology iff there exists a falsifying assignment, which serves as a polynomial-time checkable certificate. Equivalently, satisfiability (SAT) is in NP. It remains unknown whether SAT is in P, and the question of whether $\mathsf{P} = \mathsf{NP}$ is the most famous open problem in theoretical computer science. What is known is that *proof systems* for propositional logic can be compared by their power through the notion of *proof complexity*: a proof system $P_1$ *p-simulates* $P_2$ if every $P_2$-proof can be translated to a $P_1$-proof of only polynomially greater length. The question of whether there exists a proof system that admits polynomial-length proofs for all tautologies is equivalent to $\mathsf{NP} = \mathsf{co\text{-}NP}$, another major open problem.

---

## 3. High-Performance Optimization & Failure Modes

### 3.1 Proof Search Strategy and Structural Traps

The practical art of working within any formal proof system is inseparable from an understanding of where proof search can stall, loop, or silently diverge. Each system has characteristic failure modes, and a skilled logician navigates them through strategic analysis rather than brute force.

In Hilbert-style systems, the principal failure mode is *axiom selection*. With three axiom schemas and no syntactic guidance about which instantiation to choose, a naive proof attempt degenerates into an exponential search over substitution instances. The correct discipline is to work *backward* from the goal, using the Deduction Theorem aggressively to reduce every implication in the conclusion to a hypothesis, and to check at each step whether the remaining goal is an axiom instance before committing to a chain of modus ponens applications. The Deduction Theorem is not just a metatheorem here; it is the primary *proof strategy*. Any goal of the form $\alpha_1 \to \alpha_2 \to \cdots \to \alpha_k \to \psi$ should be attacked by assuming $\alpha_1, \ldots, \alpha_k$ as hypotheses and reducing to the problem of deriving $\psi$ from them.

In natural deduction, the structural trap is *invertibility*. Some rules are *invertible* in the sense that their premises are derivable whenever their conclusions are: for example, $\land\mathsf{I}$ is invertible (if $\varphi \land \psi$ is derivable, so are $\varphi$ and $\psi$ separately). Other rules are not invertible: $\lor\mathsf{I}$ is non-invertible, since $\varphi \lor \psi$ may be derivable even when neither $\varphi$ nor $\psi$ alone is. A proof-search procedure that blindly applies $\lor\mathsf{E}$ (proof by cases) can multiply branches exponentially. The correct strategy is to apply invertible rules eagerly (they never cause backtracking) and to defer non-invertible rules until forced. This is the intuition behind the sequent calculus, which is designed so that essentially all right-side rules other than $\lor\mathsf{R}$ are invertible.

The deepest failure mode in sequent calculus proof search is the *contraction rule*. Without contraction, the sequent calculus $\mathsf{LK}$ has the *subformula property* but also terminates: every rule application strictly reduces the formula content of the sequents involved (since the principal formula is consumed). With contraction, proof search can in principle loop, because a formula consumed from the left of a sequent might need to be reintroduced. In practice, the solution is to work in *contraction-free* fragments where possible. For propositional logic, the *permutability of rules* theorem allows one to show that all contractions can be pushed to the leaves of the derivation tree, where they collapse to the trivial identity axiom $\alpha \Rightarrow \alpha$.

### 3.2 Normal Forms, Proof Normalization, and the Curry–Howard Correspondence

One of the most penetrating ideas in proof theory is that derivations themselves admit a notion of *normal form*, and that the normalization process reveals deep structure hidden in the raw syntactic object of the proof. In natural deduction, a proof is in *normal form* if it contains no *detours*: an introduction immediately followed by an elimination of the same connective. Such a detour in the implicational fragment looks like this:

$$\frac{\dfrac{\begin{array}{c}[\varphi]^u \\ \vdots \\ \psi\end{array}}{\varphi \to \psi} \,{\to}\mathsf{I}^u \quad \alpha}{\psi}\,{\to}\mathsf{E}$$

where $\alpha$ is a proof of $\varphi$. This derivation has a *redex*: we introduced $\varphi \to \psi$ only to immediately eliminate it. The *reduction* removes the detour by substituting the proof of $\varphi$ (from $\alpha$) into the derivation of $\psi$ from $[\varphi]$:

$$\text{Replace every occurrence of } [\varphi]^u \text{ in the left subderivation with the derivation } \alpha.$$

This substitution process terminates (under appropriate measures), and the resulting *normal form* satisfies the *subformula property*: every formula in the normal proof is a subformula of the conclusion or the open premises. Proof normalization in natural deduction is thus the exact analogue of cut elimination in sequent calculus, and the two processes are related by a *translation* between the two proof systems.

The normalization process for natural deduction has a celebrated interpretation in computer science via the **Curry–Howard correspondence**, which identifies proofs with programs and propositions with types. Under this correspondence, $\to\mathsf{I}$ corresponds to lambda abstraction ($\lambda$-abstraction), $\to\mathsf{E}$ corresponds to function application, and proof normalization corresponds to $\beta$-reduction in the $\lambda$-calculus. Specifically, a proof of $\varphi \to \psi$ is a function (of type $\varphi \to \psi$) that maps proofs of $\varphi$ to proofs of $\psi$. The elimination rule applies this function; the redex above corresponds to a $\beta$-redex $(\lambda x. M)\, N$, and normalization corresponds to $\beta$-reduction: $(\lambda x. M)\, N \to_\beta M[N/x]$.

For the practitioner, this correspondence is not merely philosophical. It underpins the design of *proof assistants* like Coq and Agda, which represent propositions as types and proofs as terms in a typed $\lambda$-calculus. In Coq, the `intro` tactic corresponds to $\to\mathsf{I}$ (binding a hypothesis and extending the proof context), `apply` corresponds to $\to\mathsf{E}$ (applying a known implication forward), and `exact` corresponds to providing a proof term directly. When Coq's kernel *type-checks* a proof term, it is verifying the correctness of a natural deduction derivation by normalizing the term and checking its type. The `Qed` command triggers this normalization check: if the proof term does not reduce to a term of the stated type, the proof is rejected.

### 3.3 Proof System Comparison and Relative Strength

A key practical concern for anyone working with automated or proof-assistant-based formal systems is the question of *relative efficiency* of proof representations. The same tautology can have proofs of radically different lengths in different systems. Resolution proofs, the basis of DPLL-style SAT solvers, can be exponentially shorter than any tree-resolution proof of the same formula but can require exponentially more steps than Frege (Hilbert-style) proofs of certain pigeonhole-principle formulas.

The *pigeonhole principle* is the canonical example. The formula $\mathsf{PHP}_n$ asserts that there is no injective function from an $(n+1)$-element set to an $n$-element set, expressed as a propositional formula over variables $p_{ij}$ (meaning "pigeon $i$ goes to hole $j$"). Resolution proofs of $\mathsf{PHP}_n$ require exponential size: Haken proved in 1985 that any resolution refutation of $\mathsf{PHP}_n$ has size $2^{\Omega(n)}$. Yet Frege proofs of $\mathsf{PHP}_n$ can be constructed in polynomial size. This exponential gap between resolution and Frege systems is a concrete demonstration that the choice of proof system is not a matter of mere syntactic preference but has profound implications for the computational feasibility of automated proof search.

For the working logician building verified proofs in a proof assistant, the practical lessons are these. First, choose the proof tactic that most directly matches the shape of the goal: `destruct` over disjunctive hypotheses corresponds to $\lor\mathsf{E}$ and can be automated once the case count is small; `split` on conjunctive goals corresponds to $\land\mathsf{I}$; `tauto` and `decide` invoke complete propositional decision procedures and should be the first resort for purely propositional goals. Second, understand when completeness theorems apply: the `tauto` tactic in Coq implements a complete decision procedure for propositional intuitionistic logic (the *Dyckhoff* contraction-free sequent calculus), not classical logic. For classical-logic goals, one must either use `classical` axioms explicitly or invoke `Decidable.decide`. Third, proof terms generated by tactics are often non-normal and can be very large; using `Proof.` with explicit term witnesses rather than tactic scripts can reduce proof size dramatically for performance-critical formally verified software.

The gap between derivability and semantic entailment, so elegantly closed by the soundness and completeness theorems, thus reopens in the domain of *computational cost*: semantic entailment is a truth-table-checkable mathematical fact, while finding a *short* formal derivation is an algorithmically difficult problem whose worst-case complexity touches the deepest open questions in theoretical computer science. The formal study of proof systems is therefore not merely foundational but actively research-frontier, connecting logic, complexity theory, and the engineering of trustworthy software systems through a single thread of precise mathematical reasoning.
