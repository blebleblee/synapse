# Lesson 2: Structural Rules in Substructural Logics

## 1. First-Principles Intuition & Invariants

Classical logic and intuitionistic logic share a hidden assumption so pervasive that most introductory treatments never name it explicitly: the assumption that hypotheses are resources of unlimited abundance. When you write a proof that derives $B$ from $A$, classical logic permits you to use $A$ once, twice, or not at all, in any order, and to pile up as many copies of $A$ as the derivation demands. These freedoms feel natural precisely because they mirror how we reason about mathematical truths — a theorem, once true, remains available indefinitely and costs nothing to invoke again. But this abundance is purchased at a price: the logical system loses the ability to track *how* a premise is consumed, and therefore loses the ability to reason about resources, processes, or actions where use genuinely matters.

Proof theory isolates this abundance into three named rules, collectively called the **structural rules**, which govern the manipulation of the context (the multiset or sequence of hypotheses) rather than the logical content of formulas. They are **weakening**, **contraction**, and **exchange**. Each encodes a distinct assumption about the nature of hypotheses. Substructural logics are defined precisely by which of these rules are permitted, restricted, or entirely removed, and the resulting systems are not mere curiosities — they are the proof-theoretic foundations of programming language type systems, concurrent process calculi, quantum protocol verification, and the semantics of natural language.

### The Sequent Calculus as a Laboratory

The natural setting for dissecting structural rules is Gentzen's sequent calculus. A **sequent** has the form

$$\Gamma \vdash \Delta$$

where $\Gamma$ is the **antecedent** (a structured collection of hypotheses) and $\Delta$ is the **succedent** (a structured collection of conclusions). In classical sequent calculus $\mathbf{LK}$, both $\Gamma$ and $\Delta$ are finite multisets of formulas. In intuitionistic sequent calculus $\mathbf{LJ}$, $\Delta$ is restricted to at most one formula. The structural rules operate entirely on these collections, without inspecting the internal structure of any formula. This isolation is what makes it possible to remove a structural rule cleanly: its absence does not corrupt the logical connectives themselves, only the bookkeeping of hypotheses.

It is worth pausing on what a sequent calculus proof actually *is*. A proof of $\Gamma \vdash \Delta$ is a finite tree of rule applications, rooted at $\Gamma \vdash \Delta$, in which every leaf is an axiom of the form $A \vdash A$ (the identity rule). Each internal node is an instance of an inference rule that transforms one or two sequents above the line (the **premisses**) into the sequent below the line (the **conclusion**). Gentzen's central theorem — **cut elimination** — establishes that any proof using the **cut rule**

$$\frac{\Gamma \vdash \Delta, A \qquad A, \Gamma' \vdash \Delta'}{\Gamma, \Gamma' \vdash \Delta, \Delta'} \quad (\text{Cut})$$

can be transformed into a cut-free proof of the same sequent. Cut elimination is the engine of consistency proofs and the guarantor of the subformula property: in a cut-free proof, every formula appearing in an intermediate sequent is a subformula of the endsequent. This property holds in all substructural logics we examine here, and its proof proceeds in each case without requiring structural rules — a critical observation, because it means substructural logics inherit the analytic character of classical sequent calculus even after the structural rules are removed.

### Weakening: The Right to Ignore

The weakening rules state that an arbitrary formula may be added to either side of a sequent without disturbing provability:

$$\frac{\Gamma \vdash \Delta}{A, \Gamma \vdash \Delta} \quad (\text{WL}) \qquad \frac{\Gamma \vdash \Delta}{\Gamma \vdash \Delta, A} \quad (\text{WR})$$

The left weakening rule says: if you can prove $\Delta$ from $\Gamma$, you can prove $\Delta$ from $\Gamma$ even when an extra hypothesis $A$ is present — that is, you are free to discard $A$ entirely. The right weakening rule says: if $\Delta$ follows from $\Gamma$, then $\Delta$ together with any additional $A$ also follows, meaning $A$ need not be established. Weakening encodes the logical notion of **monotonicity**: adding more hypotheses never destroys a proof, and the conclusion set can always be padded with unprovable formulas without contradiction (since the sequent only asserts that *some* formula in the succedent holds).

This seems entirely uncontroversial until you consider a proof-as-program interpretation. Under the Curry-Howard correspondence, a proof of $A \vdash B$ is a program that takes an input of type $A$ and produces an output of type $B$. Left weakening then says: a program $f : B \to C$ can be given a value $a : A$ and simply throw it away. In a language tracking memory or other consumable resources, this is a **deallocation** step — and it may not always be valid. If $A$ represents a file handle or a network socket, discarding it without closing it constitutes a resource leak. Removing left weakening forces every hypothesis to be used at least once, thereby enforcing a form of mandatory resource consumption.

### Contraction: The Right to Duplicate

The contraction rules state that two copies of a formula can be merged into one:

$$\frac{A, A, \Gamma \vdash \Delta}{A, \Gamma \vdash \Delta} \quad (\text{CL}) \qquad \frac{\Gamma \vdash \Delta, A, A}{\Gamma \vdash \Delta, A} \quad (\text{CR})$$

Contraction encodes the assumption that a hypothesis can be used an **unbounded number of times** from a single occurrence. Its presence is what allows $A \vdash A \otimes A$ to fail to be provable in linear logic while $A \vdash A$ remains provable — in linear logic, $A$ is consumed exactly once to produce $A$, but producing two copies of $A$ would require two copies of $A$ as input.

In the proof-as-program reading, contraction is **copying**: a value $a : A$ is duplicated so the same computational resource can be used in two branches of a derivation. For types modeling exclusive access, mutation, or communication channels, duplication is semantically unsound. A channel can only be in one place. A mutable reference cannot be safely aliased. Linear type theory, descended directly from linear logic, enforces the prohibition on contraction as a type-system invariant, and this single restriction suffices to give static guarantees about memory safety that are otherwise enforced only at runtime.

### Exchange: The Right to Reorder

The exchange rules state that two adjacent formulas in a context may be swapped:

$$\frac{\Gamma, A, B, \Gamma' \vdash \Delta}{\Gamma, B, A, \Gamma' \vdash \Delta} \quad (\text{EL}) \qquad \frac{\Gamma \vdash \Delta, A, B, \Delta'}{\Gamma \vdash \Delta, B, A, \Delta'} \quad (\text{ER})$$

In classical and intuitionistic logic, contexts are unordered multisets, so exchange is built into the data structure: order is simply not tracked. In a **non-commutative** or **ordered logic**, the context is a sequence, and exchange is a genuine rule that may be restricted. Without exchange, the position of a hypothesis in the antecedent carries meaning — it encodes temporal order, spatial position, or causal precedence. This is the proof-theoretic basis for **Lambek calculi**, which model the grammatical structure of natural language by treating concatenation of linguistic constituents as non-commutative multiplication in a residuated algebra. The sentence "dogs bite men" and "men bite dogs" have identical word-multisets but different syntactic structures, and an ordered logic without exchange captures this distinction at the level of proof.

For most of this lesson, we will work in commutative settings where exchange is freely available, since linear logic, relevance logic, and affine logic all retain exchange. The loss of exchange appears primarily in linguistic applications and in the proof theory of non-commutative algebra, which we treat as a boundary case in Section 3.

---

## 2. Core Architecture & Mechanics

Having named the three structural rules and established their proof-theoretic meaning, we can now dissect each major substructural logic as a precisely defined sequent calculus, trace the internal architecture of its connectives, and understand the resource semantics that emerges from each combination of restrictions.

### Linear Logic: Neither Weakening Nor Contraction

Jean-Yves Girard introduced **linear logic** in 1987 by observing that classical logic can be decomposed into a resource-sensitive core plus the structural rules. The key insight was that the structural rules — specifically weakening and contraction — are not features of logical connectives themselves but of the contexts those connectives inhabit. By removing both weakening and contraction, Girard obtained a logic in which every hypothesis is used **exactly once**. The resulting system, $\mathbf{LL}$, treats formulas as consumable resources.

The first architectural consequence of this removal is that the classical connectives $\wedge$ and $\vee$ each **split** into two distinct connectives, since their classical definitions blur a distinction that only becomes visible when resources are counted. Consider classical conjunction: $A \wedge B$ means both $A$ and $B$ hold simultaneously. But in a resource-sensitive setting, "both $A$ and $B$ are available" can mean two different things. It can mean that the agent *possesses* both $A$ and $B$ and must use them together (multiplicative conjunction, written $A \otimes B$, pronounced "tensor"), or it can mean that the agent can *choose* either $A$ or $B$ on demand (additive conjunction, written $A \with B$, pronounced "with"). Similarly, classical disjunction splits into multiplicative disjunction $A \parr B$ (par) and additive disjunction $A \oplus B$ (plus). These four connectives are the linear logic analogues of the classical binary connectives, and no amount of weakening or contraction can collapse the multiplicative/additive distinction once those rules are removed.

The sequent calculus for linear logic, $\mathbf{LL}$, is built from these connectives with the following rules for multiplicative conjunction:

$$\frac{\Gamma \vdash \Delta, A \qquad \Gamma' \vdash \Delta', B}{\Gamma, \Gamma' \vdash \Delta, \Delta', A \otimes B} \quad (\otimes R) \qquad \frac{A, B, \Gamma \vdash \Delta}{A \otimes B, \Gamma \vdash \Delta} \quad (\otimes L)$$

Notice that the right rule for $\otimes$ **splits the context**: the hypotheses $\Gamma$ are used to prove $A$ and the hypotheses $\Gamma'$ are used to prove $B$, with no overlap. This is the proof-theoretic expression of "consuming both." By contrast, the additive conjunction uses a **shared context**:

$$\frac{\Gamma \vdash \Delta, A \qquad \Gamma \vdash \Delta, B}{\Gamma \vdash \Delta, A \& B} \quad (\& R) \qquad \frac{A, \Gamma \vdash \Delta}{A \with B, \Gamma \vdash \Delta} \quad (\with L_1) \qquad \frac{B, \Gamma \vdash \Delta}{A \with B, \Gamma \vdash \Delta} \quad (\with L_2)$$

In the right rule for $\&$, the same context $\Gamma$ proves both $A$ and $B$ independently — the agent chooses which to produce, but either way the same resources are consumed. In the left rules, $A \& B$ means the agent can extract either $A$ or $B$ from it, but only one. These distinctions are invisible in classical logic because contraction allows $\Gamma$ to be duplicated freely, eliminating any difference between sharing and splitting.

Linear logic handles the controlled reintroduction of classical structural rules through the **exponential modalities** $!A$ (pronounced "of course $A$") and $?A$ (pronounced "why not $A$"). The formula $!A$ asserts that $A$ is an **unlimited resource** — it can be weakened and contracted:

$$\frac{\Gamma \vdash \Delta}{!A, \Gamma \vdash \Delta} \quad (!W) \qquad \frac{!A, !A, \Gamma \vdash \Delta}{!A, \Gamma \vdash \Delta} \quad (!C) \qquad \frac{A, \Gamma \vdash \Delta}{!A, \Gamma \vdash \Delta} \quad (!D)$$

The rule $(!D)$ is **dereliction**: it demotes $!A$ to a single-use $A$, spending one copy. The promotion rule lifts an ordinary proof into the exponential context:

$$\frac{!\Gamma \vdash A, ?\Delta}{!\Gamma \vdash !A, ?\Delta} \quad (!P)$$

This rule requires that every hypothesis in context is itself an unlimited resource ($!\Gamma$) and every auxiliary conclusion in the succedent is a question-marked formula ($?\Delta$). Promotion reflects the fact that only a proof that makes no essential use of resource restrictions can produce an unlimited resource. The exponential fragment of linear logic is precisely classical propositional logic, embedded inside the resource-sensitive linear core.

The following diagram illustrates how the structural rules and connectives of classical logic decompose into the linear logic architecture:

```text
Classical Logic
      │
      ├── Structural Rules ──────────────────────────┐
      │       Weakening  ─────────────────────────── !A, ?A (exponentials)
      │       Contraction ────────────────────────── !A, ?A (exponentials)
      │       Exchange ──────────────────────────── retained
      │
      └── Connectives (split by resource sensitivity)
              ∧  ──────── A ⊗ B  (multiplicative: split context)
                └───────  A & B  (additive: shared context)
              ∨  ──────── A ⅋ B  (multiplicative: par)
                └───────  A ⊕ B  (additive: choice)
              ¬  ──────── A⊥     (linear negation, involutive)
```

The linear negation $A^\perp$ is **involutive**: $(A^\perp)^\perp = A$, which makes linear logic genuinely classical in its treatment of duality. This involutivity follows from the absence of weakening and contraction, which in classical logic are responsible for the asymmetry that intuitionistic logic introduces into negation.

### Linear Logic Proof Nets

For multiplicative linear logic (the fragment $\mathbf{MLL}$ containing only $\otimes$, $\parr$, and their units), Girard introduced **proof nets** as a canonical, graph-theoretic representation of proofs that eliminates the bureaucratic redundancy of the sequent calculus. A proof net for a sequent $\vdash A_1, \ldots, A_n$ is a directed graph with one vertex for each formula occurrence (after decomposing each formula into its subformulas using a fixed tree structure), linked by two kinds of edges: **axiom links** pairing each formula with its negation, and **rule links** encoding $\otimes$ and $\parr$ nodes. A graph is a valid proof net — that is, corresponds to an actual sequent calculus proof — if and only if it satisfies Girard's **correctness criterion**: removing any single $\parr$ link must disconnect the graph into exactly the number of components determined by that link's immediate context. Proof nets collapse the sequentialization overhead of the sequent calculus, making proof identity a graph isomorphism problem and proof normalization (cut elimination) a graph rewriting problem.

### Relevance Logic: No Weakening, Contraction Retained

**Relevance logic** was developed independently of linear logic, motivated not by resource semantics but by a philosophical objection to the classical theorem $A \to (B \to A)$: the principle that any true proposition $A$ can be concluded from any hypothesis $B$, even when $B$ has no bearing on $A$. This is exactly left weakening at the level of the implication connective. Relevance logicians — principally Anderson, Belnap, and their collaborators at Pittsburgh — argued that a valid inference must exhibit a genuine connection between premises and conclusion, a condition they called **relevance**.

The standard system of relevance logic is $\mathbf{R}$, presented in Hilbert-style as the set of theorems derivable from the axioms of positive relevant logic plus negation axioms consistent with the De Morgan laws. In sequent calculus terms, $\mathbf{R}$ removes left weakening but retains contraction and exchange. The retention of contraction is crucial: in relevance logic, a premise may be used multiple times, so hypotheses are not consumed. The prohibition on weakening simply requires that every hypothesis must appear in the proof — no premise can be entirely idle.

The defining connective of relevance logic is the **relevant implication** $A \to B$, which is interpreted not as material implication but as an entailment that requires $A$ to be actually used in deriving $B$. The relevant disjunction and conjunction satisfy the standard lattice laws, and negation obeys the De Morgan dualities. The semantic interpretation of $\mathbf{R}$ uses **Routley-Meyer frames**: triples $(W, R, *)$ where $W$ is a set of worlds, $R \subseteq W \times W \times W$ is a ternary accessibility relation, and $*: W \to W$ is the Routley star operation modeling negation. The truth condition for implication at world $w$ is:

$$w \Vdash A \to B \iff \forall u, v. \, R\,w\,u\,v \text{ and } u \Vdash A \implies v \Vdash B$$

The ternary relation $R$ replaces the binary accessibility of Kripke semantics for intuitionistic logic, and the three-slot structure reflects the fact that implication elimination (modus ponens) consumes both the implication and its antecedent. The Routley-Meyer semantics validates all and only the theorems of $\mathbf{R}$, providing a completeness theorem that parallels Kripke's completeness result for intuitionistic logic.

A central technical result in the proof theory of relevance logic is that **cut elimination holds for the sequent calculus formulation** of $\mathbf{R}$, though the proof is significantly more involved than the classical case due to the absence of weakening. The standard strategy — transforming a cut on a formula $A$ by reducing the complexity of $A$ — requires careful tracking of which hypotheses are actually used, since the contexts cannot be freely padded.

### Affine Logic: Weakening Without Contraction

**Affine logic** occupies the position between classical logic and linear logic: it removes contraction but retains weakening. This means every hypothesis may be used **at most once** — it can be discarded (weakening is available) but not duplicated (contraction is not). The name "affine" derives from the connection to affine geometry, in which transformations are allowed to translate points but not to rescale them; here, the analogy is that formulas may be passed forward or discarded, but not multiplied.

Affine logic is the proof-theoretic foundation of **uniqueness type systems** in programming languages. ML-style type systems with unique types (as in Clean) or owned types (as in Rust's ownership model) correspond directly to affine type theory: an owned value may be dropped (affine weakening permits this) but may not be cloned without an explicit operation (affine logic prohibits contraction). The Rust borrow checker, in its conceptual underpinning, enforces an affine discipline on owned types, permitting move semantics (the owner relinquishes the resource entirely, using it at most once) while requiring explicit `clone()` calls for duplication.

The sequent calculus for affine logic $\mathbf{AL}$ is obtained from linear logic $\mathbf{LL}$ by adding the structural weakening rules while retaining the prohibition on contraction. All the multiplicative and additive connectives of linear logic remain meaningful in $\mathbf{AL}$, but the distinction between $A \otimes B$ and $A \& B$ is partially collapsed: since weakening is available, the additive $\with$ can now simulate aspects of $\otimes$ by simply discarding one of the two proofs. The exponentials $!$ and $?$ still exist but their role changes: $!A$ in affine logic allows contraction on $A$, which is now a genuine strengthening since contraction is otherwise absent.

The comparison table below positions the three major substructural systems against the classical baseline:

| System | Weakening | Contraction | Exchange | Hypothesis use |
|---|---|---|---|---|
| Classical $\mathbf{LK}$ | ✓ | ✓ | ✓ | Any number of times |
| Affine $\mathbf{AL}$ | ✓ | ✗ | ✓ | At most once |
| Relevance $\mathbf{R}$ | ✗ | ✓ | ✓ | At least once |
| Linear $\mathbf{LL}$ | ✗ | ✗ | ✓ | Exactly once |
| Ordered (Lambek) $\mathbf{L}$ | ✗ | ✗ | ✗ | Exactly once, in order |

### Resource Sensitivity as a Proof-Theoretic Invariant

The most important conceptual result in this area is that **resource sensitivity is a structural invariant preserved by cut elimination**. That is: if a proof of $\Gamma \vdash A$ in linear logic uses each hypothesis in $\Gamma$ exactly once, then every cut-free proof of the same sequent also uses each hypothesis exactly once. This invariant cannot be disturbed by proof normalization because cut elimination in $\mathbf{LL}$ never introduces weakening or contraction steps — the normalization procedure respects the structural constraints of the system. The formal statement requires tracking the multiplicities of formulas throughout the cut elimination procedure, and Girard's original 1987 proof verified this explicitly for $\mathbf{MLL}$ and $\mathbf{MALL}$ (multiplicative-additive linear logic) before extending to the full system with exponentials.

The key technical tool is a **weight function** $w : \text{Proofs} \to \mathbb{N}$ that assigns to each cut a non-negative integer measuring the complexity of the cut formula plus the structural depth of the proof above each premiss of the cut. The cut elimination procedure proceeds by selecting a **topmost cut** — a cut whose premisses are cut-free — and reducing it according to the principal case analysis on the cut formula's main connective. Each reduction either eliminates a cut entirely or replaces it with cuts of strictly smaller weight, guaranteeing termination by well-founded induction on $(w, d)$ where $d$ is the depth of the cut tree. For $\mathbf{LL}$ with exponentials, the weight function must account for the interaction of cuts with $!P$ (promotion) steps, which requires a more elaborate lexicographic measure, but the fundamental structure of the induction is unchanged.

---

## 3. High-Performance Optimization & Failure Modes

### Proof Search in Substructural Logics

Deciding provability in classical propositional logic is NP-complete; in intuitionistic propositional logic, it is PSPACE-complete. The removal of structural rules changes the complexity landscape dramatically. Provability in **multiplicative linear logic** ($\mathbf{MLL}$) without units is decidable in polynomial time, because the absence of contraction means that proof search cannot loop on a fixed formula — each step strictly decreases the total number of formula tokens in the context. The key measure is the total token count

$$N(\Pi) = \sum_{A \in \Gamma} \text{count}(A, \Gamma)$$

where count tracks the multiplicity of each formula in the antecedent multiset. Each rule application in $\mathbf{MLL}$ either eliminates a connective (reducing formula complexity) or distributes the context between two premisses (reducing $N$ in each branch). Since the initial sequent has finite $N$ and each step strictly reduces it, the proof search tree is finite, and exhaustive backward chaining terminates.

Adding the additive connectives to obtain $\mathbf{MALL}$ raises provability to NP-hard, because the additive rules share the context rather than splitting it, introducing a nondeterministic choice of which branch to pursue with the full context. The additive right rule for $\with$ requires proving both $A$ and $B$ from the same $\Gamma$, so there is no token consumption at this step. Proof search for $\mathbf{MALL}$ is in NP because any proof can be verified in polynomial time by checking formula occurrences, but finding the proof requires search over exponentially many branching choices. For the full system $\mathbf{LL}$ with exponentials, provability is undecidable: the exponentials $!$ and $?$ can encode Minsky counter machines, and the unbounded reuse permitted by $!$ reintroduces the same complexity that makes first-order logic undecidable.

The proof-search practitioner working with $\mathbf{LL}$ therefore faces a triage problem: identify which fragment of linear logic is relevant to the problem at hand, and deploy the appropriate algorithm for that fragment. For $\mathbf{MLL}$, proof nets provide the most efficient search strategy, since the correctness criterion reduces proof search to a graph construction problem solvable in $O(n^2)$ time by Danos-Regnier's algorithm. For $\mathbf{MALL}$, standard sequent calculus backward chaining with memoization (storing proved sequents in a table indexed by their token multiset) avoids redundant recomputation and brings the algorithm within the NP bound in practice.

### Focusing and Polarity in Linear Logic

A major source of nondeterminism in sequent calculus proof search is the freedom to apply rules in any order. If the proof calculus is **confluent** — meaning that different rule-application orders always lead to the same set of provable sequents — then search can impose an order without losing completeness. Andreoli's **focusing theorem** for $\mathbf{LL}$ provides a canonical strategy for eliminating this nondeterminism. The key observation is that linear logic connectives have a natural **polarity**:

A formula is **negative** (or **asynchronous**) if its right introduction rule can always be applied immediately without loss of generality: $A \parr B$, $A \with B$, $?A$, and the top $\top$ are negative. A formula is **positive** (or **synchronous**) if applying its right introduction rule commits the prover to a particular decomposition: $A \otimes B$, $A \oplus B$, $!A$, and the constant $1$ are positive. A focused proof organizes derivations into alternating **negative phases** (in which all asynchronous rules are applied eagerly, in any order, since they commute with each other) and **positive phases** (in which a single positive formula is selected and decomposed completely before switching phase).

The focused sequent calculus $\mathbf{LKF}$ implements this discipline by annotating sequents with a distinguished **focused formula**: during a positive phase, the focus is maintained on a single formula until the proof either closes on an axiom or the focused formula is fully decomposed. The focusing theorem states that every provable sequent in $\mathbf{LL}$ has a focused proof, so focusing is a **complete** restriction of the proof space. The practical gain is substantial: proof search in the focused calculus avoids the combinatorial blowup of unordered rule application, since at any point the proof strategy is either deterministic (apply the unique applicable asynchronous rule) or makes a small bounded choice (select a positive formula from the context and a positive rule to apply).

Focusing extends naturally to affine and relevance logic. In affine logic, the negative phase is enriched by weakening steps, which can be applied to any hypothesis not needed in the current branch; since weakening is deterministic (the prover can decide to drop a hypothesis without branching), it integrates smoothly into the asynchronous phase. In relevance logic, the absence of weakening means that proof search must track **used hypotheses** throughout the derivation, maintaining a global invariant that every hypothesis in the initial antecedent will appear in some leaf of the proof tree. This tracking adds an overhead to proof search, but it also provides early termination criteria: if a proof branch reaches a point where a hypothesis cannot possibly appear in its subtree, the branch is immediately pruned as invalid.

### Failure Modes: When Structural Restrictions Are Violated

The most common failure mode when working with substructural logics arises from inadvertently smuggling a forbidden structural rule through a derived rule or a macro-level reasoning step. Consider the following tempting but invalid derivation in linear logic. Suppose we wish to prove $!A \vdash A \otimes A$ — that an unlimited resource can supply two copies of $A$. The correct derivation is:

$$\frac{\dfrac{!A \vdash A \quad (!D)}{} \quad \dfrac{!A \vdash A \quad (!D)}{}}{!A, !A \vdash A \otimes A \quad (\otimes R)}$$

followed by a contraction on $!A$:

$$\frac{!A, !A \vdash A \otimes A}{!A \vdash A \otimes A} \quad (!C)$$

This is valid precisely because $!A$ carries the contraction permission for $A$. By contrast, the derivation $A \vdash A \otimes A$ is not provable in $\mathbf{LL}$: the right rule for $\otimes$ would require splitting the singleton context $\{A\}$ into two disjoint parts, each required to prove $A$, which is impossible since $A$ cannot appear in both halves of the split. Any attempted proof of this sequent will fail to close, and the failure is not an error in the calculus but a correct detection of a resource violation — the proof system is refusing to allow a single token of $A$ to appear in two places simultaneously.

A subtler failure mode arises from **context pollution** in the additive rules. In $\mathbf{MALL}$, the additive conjunction rule requires the same context to prove both branches. A common error in manual proof construction is to use different subsets of the context in each branch under the guise of "selecting what is needed," which silently introduces weakening. Mechanized proof assistants for linear logic — such as the $\mathbf{LL}$ mode of Coq developed via the LL tactic library, or the LLVM-based linear type checker — enforce context linearity by maintaining a **consumption bitmap**: a boolean flag for each hypothesis in the current context, initialized to false and set to true the first time the hypothesis is used. Any attempt to close a proof branch without all flags set to true triggers a linearity error, and any attempt to use a hypothesis whose flag is already true triggers a duplication error. The additive rules require that the bitmap be **forked** (duplicated) at the additive branch point and that both copies end with all flags set, enforcing the shared-context invariant.

For relevance logic, the failure mode is dual: a proof that ignores a hypothesis is inadmissible, but automated proof search may not detect this until the final closure check. The standard mitigation is **labeling semantics**: each hypothesis is assigned a unique label, and the conclusion of each inference rule carries a label expression tracking which hypotheses contribute to it. A proof is admissible in $\mathbf{R}$ if and only if every hypothesis label appears in the label expression of the final conclusion. This labeling technique, introduced by Belnap, is essentially an algebraic bookkeeping system that enforces relevance without modifying the inference rules themselves — it tracks the invariant at the meta-level while letting the object-level proof proceed normally.

### Embedding Classical Logic and the Double-Negation Translation

A fundamental theoretical tool is the ability to **embed** one logic into another via a translation that preserves and reflects provability. The classical double-negation translation of Gödel-Gentzen embeds classical propositional logic into intuitionistic logic by replacing each formula $A$ with $\neg\neg A$ (or more precisely, by applying the translation homomorphically through the formula structure). An analogous embedding exists for linear logic: classical logic embeds into the exponential fragment of $\mathbf{LL}$ by translating each classical formula $A$ as $!A^\circ$, where $A^\circ$ is the linear logic formula obtained by translating each classical connective into its linear logic counterpart using the multiplicatives. The resulting embedding, known as the **Girard translation**, satisfies:

$$\text{Classical logic proves } A \iff \mathbf{LL} \text{ proves } !A_1^\circ, \ldots, !A_n^\circ \vdash !B^\circ$$

for all classical sequents $A_1, \ldots, A_n \vdash B$. This translation makes precise the sense in which linear logic is a **refinement** of classical logic: it separates the logical content of classical reasoning from its structural assumptions, packaging the structural freedom into explicit exponential annotations. A classical theorem is not false in linear logic — it is simply a theorem about unlimited resources, which requires the $!$ modality to express.

The embedding also provides a correctness criterion for substructural restrictions in applied settings. If a type theory is to enforce affine discipline (at-most-once use), the Girard translation tells you exactly which classical types must be replaced with linear types and which may be freely annotated with $!$ (the types that are genuinely unlimited, such as integers or booleans, which can be copied without semantic consequence). Types that represent exclusive resources — file handles, allocated memory, channel endpoints — must remain linear, and any attempted embedding of a classical proof about them into the linear setting will fail at precisely the point where a structural rule is implicitly invoked.

### Proof Nets as a Verification Tool

For practitioners implementing or verifying proofs in multiplicative linear logic, proof nets provide a practical alternative to sequent calculus derivations that is both more compact and more amenable to algorithmic verification. Given a proposed proof net for a sequent $\vdash A_1, \ldots, A_n$, Danos and Regnier's formulation of the correctness criterion can be checked in $O(n^2)$ time using the following procedure. Decompose each formula $A_i$ into its syntactic tree, labeling each leaf with an atomic formula or its negation. Connect each positive atomic occurrence $p$ to the unique negative occurrence $p^\perp$ via an axiom link (since in the multiplicative setting, the duality structure ensures a bijection between positive and negative occurrences in a correct net). For each internal node of a formula tree labeled $\otimes$ or $\parr$, insert the corresponding rule link connecting the node to its two children. The resulting graph is a **proof structure**. Apply the correctness criterion: for each subset $S$ of $\parr$ links, removing the edges in $S$ from the graph must result in exactly $|S|+1$ connected components if $S$ forms a **switching** (a selection of one child edge from each $\parr$ node). A graph satisfying this criterion for every switching is a valid proof net, and the sequent it corresponds to is provable in $\mathbf{MLL}$.

This algorithmic perspective on proof nets is not merely theoretical. Proof net algorithms have been implemented in proof-checking systems such as **ProofTools** and in the linear logic module of **Agda**'s categorical semantics library. The correctness criterion serves as a decision procedure for $\mathbf{MLL}$ provability that is significantly faster than sequent-calculus proof search, making proof nets the preferred representation for applications in natural language parsing (via the Lambek calculus, a non-commutative variant) and in the proof-theoretic analysis of session types in concurrent programming languages.

The deepest lesson of substructural proof theory is not that classical logic is wrong, but that it is wasteful: it discards structural information that is semantically meaningful in any domain where resources are finite, processes are irreversible, or communication is directional. Linear logic, relevance logic, and affine logic are not restrictions of classical logic so much as they are more careful accountants of the same logical currency, spending it only where genuinely required and refusing to counterfeit it through contraction or discard it through weakening. The structural rules are the site where logic meets the world's constraints, and removing them is the proof-theoretic act of taking those constraints seriously.
