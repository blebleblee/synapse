# Lesson 1: Sequent Calculus vs Natural Deduction

## 1. First-Principles Intuition & Invariants

The architecture of formal proof systems rests on a foundational tension between two competing philosophies of mathematical reasoning: the *synthetic* approach, which mirrors human intuition by constructing proofs through hypothesis-driven forward reasoning, and the *analytic* approach, which dissects provability by systematically decomposing logical structures until atomic truths emerge. Natural deduction, introduced by Gerhard Gentzen in 1934 alongside his sequent calculus, embodies the synthetic tradition. It formalizes the mathematician's natural impulse to assume hypotheses, derive consequences, and discharge assumptions when conclusions are reached. Sequent calculus, by contrast, adopts an analytic stance: it treats provability as a relation between structured contexts (the left side of a sequent, representing assumptions) and conclusions (the right side), with inference rules that systematically reduce complex formulas to simpler components until axioms are reached.

The profound insight animating both systems is that logical truth can be characterized entirely through the *introduction* and *elimination* behavior of connectives. In natural deduction, each logical operator is defined by a pair of rules: introduction rules specify how to construct a proof of a formula containing that operator, while elimination rules specify how to use such a proof. For conjunction, the introduction rule $\land\text{-intro}$ permits inferring $A \land B$ from separate proofs of $A$ and $B$, while the elimination rules $\land\text{-elim}_1$ and $\land\text{-elim}_2$ extract $A$ or $B$ from a proof of $A \land B$. This duality reflects the fundamental principle that the meaning of a logical operator is entirely determined by its proof-theoretic behavior: what counts as evidence for a compound formula, and what information can be extracted from such evidence.

Sequent calculus rearranges this picture by making the context explicit. A sequent $\Gamma \vdash \Delta$ encodes a provability claim: from the assumptions in $\Gamma$, at least one formula in $\Delta$ is derivable. Gentzen's original system LK (for classical logic, where $\Delta$ may contain multiple formulas) and LJ (for intuitionistic logic, restricting $\Delta$ to at most one formula) decompose logical reasoning into *left rules* and *right rules*. Right rules introduce connectives on the conclusion side and mirror the introduction rules of natural deduction. Left rules introduce connectives on the assumption side and mirror elimination rules. This structural symmetry exposes a deep duality: in classical logic, every connective has a left/right pair of rules that are mirror images under the exchange of assumptions and conclusions.

The invariant that unifies both systems is the *subformula property* in cut-free proofs. Gentzen's Hauptsatz (cut-elimination theorem) establishes that any proof in sequent calculus using the cut rule—which allows chaining proofs by inferring $\Gamma, \Gamma' \vdash \Delta, \Delta'$ from $\Gamma \vdash A, \Delta$ and $A, \Gamma' \vdash \Delta'$—can be transformed into a cut-free proof where every formula appearing in the derivation is a subformula of the conclusion. This property is the logical analogue of polynomial-time decidability: it bounds the search space for proofs and provides a systematic proof-search algorithm. Natural deduction achieves an analogous property through *normalization*: every proof can be transformed into a normal form where introduction rules never immediately precede elimination rules for the same connective. The Curry-Howard correspondence reveals that this normalization process is isomorphic to $\beta$-reduction in the simply-typed lambda calculus, where cut-elimination corresponds to computational evaluation.

The structural differences between the two systems manifest most clearly in the treatment of implication and disjunction. In natural deduction, implication introduction $\to\text{-intro}$ discharges a hypothesis: from a proof of $B$ under the assumption $A$, we derive $A \to B$ without $A$ remaining as an active assumption. This operation has no direct analogue in sequent calculus, where the right rule for implication $\Gamma \vdash A \to B, \Delta$ is derived from $A, \Gamma \vdash B, \Delta$, moving the antecedent $A$ from the right side to the left. The hypothesis discharge mechanism of natural deduction is encoded in sequent calculus through the structural manipulation of contexts. Similarly, disjunction elimination in natural deduction requires case analysis: from proofs of $C$ under separate assumptions $A$ and $B$, and a proof of $A \lor B$, we derive $C$. In sequent calculus, this becomes the left disjunction rule, which splits a sequent $A \lor B, \Gamma \vdash \Delta$ into two subgoals $A, \Gamma \vdash \Delta$ and $B, \Gamma \vdash \Delta$.

The choice between natural deduction and sequent calculus is not merely aesthetic. Natural deduction proofs are typically more compact and correspond more directly to informal mathematical arguments, making them suitable for proof presentation and human verification. Sequent calculus, with its explicit context manipulation and symmetric treatment of assumptions and conclusions, is better suited for automated proof search and metatheoretic analysis. The sequent calculus structure makes properties like consistency, completeness, and decidability more accessible: contraction-free fragments of linear logic, for instance, admit polynomial-time proof search, a fact that is obscured in natural deduction formulations. The dual nature of left and right rules also exposes symmetries in classical logic that are hidden in the natural deduction presentation, where negation is often defined indirectly through implication and absurdity.

## 2. Core Architecture & Mechanics

The natural deduction system for intuitionistic propositional logic is organized around the principle that each connective is characterized by its canonical introduction and elimination forms. The rules are structured as inference schemas, where horizontal lines separate premises (above) from conclusions (below), and side conditions specify when rules apply. We adopt the convention that $\Gamma$ denotes a set of undischarged assumptions, and we write $\Gamma, A$ for $\Gamma \cup \{A\}$ when $A \notin \Gamma$.

The conjunction rules exhibit the simplest duality. Introduction requires separate proofs of both conjuncts under the same assumptions:

$$\frac{\Gamma \vdash A \quad \Gamma \vdash B}{\Gamma \vdash A \land B} \land\text{-intro}$$

Elimination extracts each conjunct independently:

$$\frac{\Gamma \vdash A \land B}{\Gamma \vdash A} \land\text{-elim}_1 \qquad \frac{\Gamma \vdash A \land B}{\Gamma \vdash B} \land\text{-elim}_2$$

The harmony between introduction and elimination is manifest: anything we can do with a conjunction $A \land B$ (namely, extract $A$ or $B$) is precisely what is required to construct it (proofs of both $A$ and $B$). This local soundness ensures that elimination does not overcommit—we can only extract information that was required for introduction—and local completeness ensures that elimination is strong enough to recover the construction evidence.

Disjunction reverses this pattern. Introduction allows proving $A \lor B$ from either disjunct:

$$\frac{\Gamma \vdash A}{\Gamma \vdash A \lor B} \lor\text{-intro}_1 \qquad \frac{\Gamma \vdash B}{\Gamma \vdash A \lor B} \lor\text{-intro}_2$$

Elimination implements case analysis. To derive a conclusion $C$ from $A \lor B$, we must prove $C$ under the separate assumptions of $A$ and $B$:

$$\frac{\Gamma \vdash A \lor B \quad \Gamma, A \vdash C \quad \Gamma, B \vdash C}{\Gamma \vdash C} \lor\text{-elim}$$

The critical observation is that the premises $\Gamma, A \vdash C$ and $\Gamma, B \vdash C$ represent hypothetical derivations: we temporarily assume $A$ or $B$ to derive $C$, then discharge these assumptions when applying the elimination rule. This hypothesis discharge mechanism is the signature feature distinguishing natural deduction from Hilbert-style axiomatic systems.

Implication introduction formalizes the deduction theorem. From a derivation of $B$ that may use $A$ as an assumption, we construct a proof of $A \to B$ that no longer depends on $A$:

$$\frac{\Gamma, A \vdash B}{\Gamma \vdash A \to B} \to\text{-intro}^{[A]}$$

The superscript $[A]$ marks the discharged hypothesis. In proof trees, this is often indicated by bracketing or labeling the assumption $A$ with a unique identifier that is referenced by the introduction rule. Elimination is modus ponens:

$$\frac{\Gamma \vdash A \to B \quad \Gamma \vdash A}{\Gamma \vdash B} \to\text{-elim}$$

Negation in intuitionistic logic is defined as $\neg A := A \to \bot$, where $\bot$ represents absurdity or falsehood. The only rule for $\bot$ is ex falso quodlibet:

$$\frac{\Gamma \vdash \bot}{\Gamma \vdash A} \bot\text{-elim}$$

This rule asserts that from a contradiction, anything follows. In classical logic, we add the law of excluded middle $A \lor \neg A$ as an axiom, or equivalently, the double negation elimination rule:

$$\frac{\Gamma \vdash \neg\neg A}{\Gamma \vdash A} \text{DNE}$$

The sequent calculus reformulates these ideas by making the multiset of assumptions and conclusions explicit. A sequent is a pair $\Gamma \vdash \Delta$ where $\Gamma$ and $\Delta$ are finite multisets of formulas. The interpretation in classical logic LK is that if all formulas in $\Gamma$ are true, then at least one formula in $\Delta$ is true. In intuitionistic logic LJ, $\Delta$ is restricted to contain at most one formula, reflecting the constructive principle that a proof must determine which conclusion is derivable.

The axiom and structural rules provide the foundation. The identity axiom asserts that any formula implies itself:

$$\frac{}{A \vdash A} \text{Axiom}$$

The cut rule allows composition of derivations:

$$\frac{\Gamma \vdash A, \Delta \quad A, \Gamma' \vdash \Delta'}{\Gamma, \Gamma' \vdash \Delta, \Delta'} \text{Cut}$$

The structural rules govern context manipulation. Weakening permits adding extraneous assumptions or conclusions:

$$\frac{\Gamma \vdash \Delta}{\Gamma, A \vdash \Delta} \text{Weak-L} \qquad \frac{\Gamma \vdash \Delta}{\Gamma \vdash A, \Delta} \text{Weak-R}$$

Contraction allows duplicating assumptions or conclusions:

$$\frac{A, A, \Gamma \vdash \Delta}{A, \Gamma \vdash \Delta} \text{Contr-L} \qquad \frac{\Gamma \vdash A, A, \Delta}{\Gamma \vdash A, \Delta} \text{Contr-R}$$

Exchange permits reordering contexts (often implicit when treating $\Gamma$ and $\Delta$ as multisets rather than sequences).

The logical rules decompose connectives. Right rules introduce connectives in the conclusion, mirroring natural deduction introduction:

$$\frac{\Gamma \vdash A, \Delta \quad \Gamma \vdash B, \Delta}{\Gamma \vdash A \land B, \Delta} \land\text{-R}$$

$$\frac{\Gamma \vdash A, \Delta}{\Gamma \vdash A \lor B, \Delta} \lor\text{-R}_1 \qquad \frac{\Gamma \vdash B, \Delta}{\Gamma \vdash A \lor B, \Delta} \lor\text{-R}_2$$

$$\frac{A, \Gamma \vdash B, \Delta}{\Gamma \vdash A \to B, \Delta} \to\text{-R}$$

Left rules introduce connectives in assumptions, mirroring elimination:

$$\frac{A, \Gamma \vdash \Delta}{\Gamma, A \land B \vdash \Delta} \land\text{-L}_1 \qquad \frac{B, \Gamma \vdash \Delta}{\Gamma, A \land B \vdash \Delta} \land\text{-L}_2$$

$$\frac{A, \Gamma \vdash \Delta \quad B, \Gamma \vdash \Delta}{A \lor B, \Gamma \vdash \Delta} \lor\text{-L}$$

$$\frac{\Gamma \vdash A, \Delta \quad B, \Gamma' \vdash \Delta'}{A \to B, \Gamma, \Gamma' \vdash \Delta, \Delta'} \to\text{-L}$$

The translation between natural deduction and sequent calculus is mechanical. A natural deduction derivation $\Gamma \vdash A$ corresponds to a sequent $\Gamma \vdash A$ (in LJ, where the right side contains exactly one formula). The hypothesis discharge mechanism in implication introduction maps directly to the movement of $A$ from the right side to the left in $\to\text{-R}$. Conversely, a cut-free sequent calculus proof can be translated to natural deduction by interpreting right rules as introductions and left rules as eliminations, with the proviso that the multiple-conclusion structure of classical LK requires invoking classical principles like excluded middle.

The Curry-Howard correspondence establishes a three-way isomorphism between intuitionistic natural deduction proofs, simply-typed lambda terms, and sequent calculus derivations (via a translation that preserves structure). Under this correspondence, formulas are types, proofs are programs, and proof normalization is program evaluation. The implication $A \to B$ corresponds to the function type $A \to B$, with implication introduction $\to\text{-intro}$ mapping to lambda abstraction $\lambda x^A. M^B$ and elimination $\to\text{-elim}$ mapping to application $M^{A \to B} N^A$. The conjunction $A \land B$ corresponds to the product type $A \times B$, with introduction mapping to pairing $\langle M^A, N^B \rangle$ and elimination to projections $\pi_1$ and $\pi_2$. Disjunction $A \lor B$ corresponds to the sum type $A + B$, with introduction mapping to injections $\text{inl}^A(M)$ and $\text{inr}^B(N)$, and elimination mapping to case analysis $\text{case } L^{A + B} \text{ of inl}(x) \Rightarrow M^C \mid \text{inr}(y) \Rightarrow N^C$.

The normalization process eliminates detours: subproofs where an introduction rule is immediately followed by an elimination rule for the same connective. For implication, a $\beta$-redex arises when we apply $\to\text{-elim}$ to a proof constructed by $\to\text{-intro}$:

$$\frac{\displaystyle\frac{\vdots}{\Gamma, A \vdash B}}{\Gamma \vdash A \to B} \to\text{-intro}^{[A]} \qquad \frac{\Gamma \vdash A \to B \qquad \Gamma \vdash A}{\Gamma \vdash B} \to\text{-elim}$$

Normalization replaces this with a direct derivation of $\Gamma \vdash B$ by substituting the proof of $A$ for the discharged hypothesis in the derivation of $B$. This operation is precisely $\beta$-reduction in the lambda calculus: $(\lambda x. M) N \to_\beta M[N/x]$. The strong normalization theorem for intuitionistic propositional logic asserts that every reduction sequence terminates in a unique normal form, corresponding to the fact that every typed lambda term has a unique normal form under $\beta$-reduction. This property is the logical foundation of type safety in functional programming languages.

## 3. High-Performance Optimization & Failure Modes

The computational complexity of proof search in natural deduction and sequent calculus diverges sharply depending on structural restrictions and the logic fragment under consideration. Full propositional intuitionistic logic admits proof search that is PSPACE-complete, while classical propositional logic is coNP-complete (proof search is equivalent to determining tautology, the complement of satisfiability). The subformula property of cut-free sequent calculus provides a crucial optimization: the search space is bounded by the number of subformulas of the goal formula, yielding a proof search algorithm with exponential time complexity in the size of the formula but polynomial space complexity via depth-first search.

The focused sequent calculus, introduced by Andreoli for linear logic and later adapted to intuitionistic and classical logics, partitions connectives into *positive* (or asynchronous) and *negative* (or synchronous) classes based on whether their decomposition preserves provability deterministically. Positive connectives like $\land$ and $\lor$ on the right, and $\to$ on the left, admit don't-care nondeterminism: the order of decomposition does not affect provability. Negative connectives like $\to$ on the right and $\land$ on the left exhibit don't-know nondeterminism: the choice of which formula to decompose first may lead to proof search failure. Focused proof search alternates between *invertible* phases, where all positive formulas are eagerly decomposed, and *focusing* phases, where a single negative formula is selected and decomposed until a positive formula is reached. This discipline reduces backtracking by committing to a focus formula and exhausting its decomposition before making the next nondeterministic choice.

In practical proof assistants like Coq and Lean, which are based on dependent type theory rather than pure propositional logic, the natural deduction style is preferred for proof term construction because it produces compact, human-readable evidence. The tactics language in these systems provides high-level commands that compile to sequences of natural deduction rules: `intro` applies $\to\text{-intro}$ or $\forall\text{-intro}$, `destruct` applies elimination rules, `split` applies $\land\text{-intro}$, and `left`/`right` apply $\lor\text{-intro}_1$ and $\lor\text{-intro}_2$. The proof term generated by a tactic script is a lambda term that can be independently type-checked, exploiting the Curry-Howard isomorphism to separate proof construction (which may use heuristics and automation) from proof verification (which is a deterministic type-checking algorithm).

Sequent calculus is the foundation for automated theorem provers like Prover9, Vampire, and E, which implement resolution-based proof search for first-order logic. Resolution is a refutation calculus derived from sequent calculus by specializing to clausal form (disjunctions of literals) and fusing the cut rule with the negation rules to obtain a single resolution rule:

$$\frac{C \lor A \quad \neg A \lor D}{C \lor D} \text{Resolution}$$

The completeness of resolution follows from the completeness and cut-elimination theorem for sequent calculus: a formula is unsatisfiable if and only if the empty clause (representing $\bot$) can be derived by resolution from its clausal form. Modern resolution provers incorporate sophisticated redundancy elimination techniques (subsumption, simplification), indexing structures (discrimination trees, substitution trees), and clause selection heuristics (weight-based, age-based) that exploit the sequent calculus structure to prune the search space.

A critical failure mode in both systems is the loss of canonicity in the presence of classical principles. In intuitionistic logic, cut-free proofs enjoy the disjunction property (if $\vdash A \lor B$, then $\vdash A$ or $\vdash B$) and the existence property (if $\vdash \exists x. P(x)$, then $\vdash P(t)$ for some term $t$), which ensure that proofs are computationally informative. Adding the law of excluded middle destroys these properties: a classical proof of $A \lor \neg A$ does not determine which disjunct holds. The computational content of classical proofs can be recovered through continuation-passing style interpretations (the double-negation translation) or by restricting to fragments like Boolean BI or focused classical logic, where the locus of nonconstructivity is isolated.

Another failure mode arises in proof term size explosion during normalization. While strong normalization guarantees termination, the size of the normal form can be non-elementary in the size of the original proof for higher-order logics. In propositional logic, the normal form is at most exponentially larger, but in System F (second-order intuitionistic logic), normalization can produce proofs whose size is a tower of exponentials. This phenomenon reflects the Ackermann-like behavior of type-level computation in polymorphic lambda calculi and imposes practical limits on proof normalization in systems like Coq, which must balance the benefits of normalization (canonical representations, efficient equality checking) against the cost in proof term size.

The structural rules—weakening, contraction, and exchange—also have profound implications for computational interpretation. Linear logic, obtained by removing weakening and contraction, interprets proofs as resource-sensitive computations where assumptions are consumed exactly once. The sequent calculus for linear logic stratifies into multiplicative connectives ($\otimes$, $\multimap$, which correspond to parallel composition and linear implication) and additive connectives ($\&$, $\oplus$, which correspond to choice and branching). The absence of contraction ensures that the size of proofs is polynomial in the size of the conclusion, yielding a tractable proof search algorithm for multiplicative linear logic (MLL), which is NP-complete. This resource-conscious perspective has applications in verification of concurrent systems, where formulas represent protocol states and proofs represent valid execution traces.

In summary, the choice between natural deduction and sequent calculus hinges on the intended application. Natural deduction excels in proof presentation and proof-term-based verification, where compactness and readability dominate. Sequent calculus excels in automated proof search and metatheoretic analysis, where the explicit structure of contexts and the symmetry of left and right rules enable algorithmic optimization and modular system design. The Curry-Howard correspondence unifies both perspectives, revealing that logical derivations, functional programs, and type assignments are three views of the same mathematical object, and that proof-theoretic properties like normalization and cut-elimination correspond to computational properties like evaluation and program transformation. Mastery of both systems, and fluency in translating between them, is essential for the working logician and theoretical computer scientist.
