# Lesson 04: Resolution Strategies & Formal Implications

## 1. First-Principles Intuition & Invariants

### 1.1 What a Paradox Formally Is

A logical paradox is a derivation that, from prima facie acceptable premises and prima facie valid inference rules, produces a contradiction or an absurd conclusion. The qualifier "prima facie" is load-bearing: a paradox is not merely a contradiction, which is a well-formed formula `φ ∧ ¬φ` that any consistent theory simply excludes. A paradox is a contradiction whose derivation pressure comes from rules or axioms we independently wish to keep. The challenge is therefore not "how do we remove the contradiction" but "which of the components generating the derivation pressure should we revise, and at what cost."

Every paradox in formal logic can be decomposed into three structural components:

1. **A referential substrate.** A domain of objects, statements, or truth-values over which variables range. For the liar paradox this is sentences; for Russell's paradox it is classes; for the Banach-Tarski paradox it is subsets of ℝ³.
2. **A closure principle.** A rule that permits constructing a new member of the substrate from a condition on members. Russell's comprehension axiom does this for classes; the T-schema does it for truth; unrestricted self-reference does it for programs.
3. **A negation or complement operation.** A way of expressing that a condition fails to hold, which, combined with closure, produces a fixed point of negation: an object that applies (or refers) to itself in the negative mode.

The invariant that every paradox violates is **consistency of the closure**. Given a closure principle C and a negation operator ¬, we obtain a contradiction whenever there exists an element d such that `C(¬φ(d)) = d`, because then `φ(d) ↔ ¬φ(d)`. The liar sentence L satisfying `L ↔ ¬True(L)` is exactly such a fixed point. Russell's class `R = {x : x ∉ x}` is another, since `R ∈ R ↔ R ∉ R`.

### 1.2 The Three Structural Invariants

Across all formal paradoxes, three invariants recur as the trade-space within which every resolution must operate. They form an impossibility relation: no standard resolution preserves all three simultaneously for self-referential substrates.

**Invariant I — Consistency.** The theory derives no formula of the form `φ ∧ ¬φ` (syntactic) or satisfies no model where a sentence and its negation are both designated (semantic). Consistency is the minimal condition for a theory to have a classical model. Explosive logics, those validating the principle *ex falso quodlibet* (`φ, ¬φ ⊢ ψ`), collapse entirely upon its loss: every sentence becomes derivable, and the theory's consequence relation becomes trivial.

**Invariant II — Closure completeness.** The closure principle is unrestricted: every well-formed condition defines an object in the substrate. The comprehension axiom in its naive form, "for any predicate φ, there exists a class {x : φ(x)}," is the paradigmatic instance. The T-schema, "True(⌜φ⌝) ↔ φ" for every sentence φ, is the semantic analogue. Closure completeness is what makes a theory expressive: it guarantees that the substrate is rich enough to talk about every condition expressible in the language, including conditions that mention the substrate itself.

**Invariant III — Classical logic.** The inference rules are those of classical first-order logic: bivalence (every sentence is either true or false), the law of excluded middle (`φ ∨ ¬φ`), double-negation elimination (`¬¬φ ⊢ φ`), and the unrestricted structural rules (weakening, contraction, exchange). Classical logic is the default metalogic against which the cost of a resolution is measured.

The fundamental theorem of the paradox landscape is:

> For any substrate that supports self-reference (achieved via diagonalization, Gödel coding, or direct fixed-point constructors), **no theory can simultaneously maintain Consistency, Closure completeness, and Classical logic.**

This is not a single result but a family. Russell's paradox shows it for classes: naive comprehension plus classical logic yields inconsistency. Tarski's undefinability theorem shows it for truth: a language rich enough to define its own truth predicate is inconsistent. Gödel's second incompleteness theorem shows it for provability: a consistent, sufficiently expressive theory cannot prove its own consistency. Yablo's paradox shows it even without direct self-reference: an infinite sequence of sentences each saying "all subsequent sentences are false" generates a contradiction under classical bivalence, using only ω-length descent rather than a fixed point.

### 1.3 The Taxonomy of Derivation Pressure

Resolution strategies are classified by which invariant they sacrifice. This is not a stylistic choice but a structural one: the proof of the paradox fixes the options.

| Paradox | Closure principle | What must be sacrificed |
|---|---|---|
| Russell's (classes) | Naive comprehension | Closure (type theory) or Logic (paraconsistency) |
| Liar (truth) | T-schema unrestricted | Closure (hierarchical truth) or Logic (non-classical truth) |
| Gödel (provability) | Representability + diagonalization | Closure (limit expressiveness) or Consistency (the theory is weak) |
| Yablo (ω-liar) | Bivalence over infinite sequences | Logic (drop bivalence) or Closure (block ω-comprehension) |
| Curry (conditional) | Naive truth + material conditional | Closure or Logic (revise the conditional) |
| Sorites (vagueness) | Classical bivalence over predicates | Logic (many-valued or supervaluation) |

The Curry paradox deserves special attention because it does not rely on negation. Given a sentence C such that `C ↔ (True(C) → ⊥)`, naive truth plus the material conditional lets us derive `⊥` outright:

```
1. C ↔ (True(C) → ⊥)          [fixed point construction]
2. C → (True(C) → ⊥)           [from 1, ↔ elimination]
3. True(C)                     [from 1, ↔ introduction reversed: C holds, so True(C)]
4. True(C) → ⊥                 [modus ponens on 2, 3]
5. ⊥                           [modus ponens on 3, 4]
```

The Curry paradox shows that the problem is not negation per se but the combination of self-reference, a truth predicate satisfying the T-schema, and a conditional that satisfies contraction (using a premise twice is no stronger than using it once). This constrains resolution strategies that target only negation: any adequate resolution of the truth paradoxes must handle Curry's paradox, which means it must address the conditional or the structural rules, not merely the law of excluded middle.

### 1.4 The Diagonalization Mechanism

Self-reference, the engine of most logical paradoxes, is constructed through diagonalization. The mechanism is general and worth isolating.

Given a binary relation `R(x, y)` in a system with enough representational power, diagonalization constructs an element `d` such that `R(d, d)` holds iff `R(d, d)` does not hold. The construction proceeds:

1. Enumerate the substrate: assign each element an index, so we can speak of `R(i, j)` where `i` is a "row" and `j` is a "column."
2. Define the diagonal property `D(i) := ¬R(i, i)`. This "flips" the diagonal of the relation matrix.
3. Ask whether `D` itself appears as a row. If the enumeration is complete (closure completeness), there exists an index `k` such that `D = R(k, ·)`.
4. Evaluate `D(k)`: by definition `D(k) = ¬R(k, k)`, but since `D = R(k, ·)`, we have `D(k) = R(k, k)`. So `R(k, k) = ¬R(k, k)`.

This is the abstract skeleton underlying Cantor's theorem (R = "is in bijection with"), Russell's paradox (R = "is a member of"), the liar (R = "is true of"), Gödel's first incompleteness theorem (R = "is provable in"), and the halting problem (R = "halts on input"). Every resolution strategy must either prevent step 3 (block the diagonal element from appearing in the enumeration), reject the bivalence in step 4 (deny that `R(k,k)` must be either true or false), or accept the contradiction in step 4 and revise the logic so that contradictions are not explosive.

## 2. Core Architecture & Mechanics

### 2.1 Type Theory: Restricting Closure

Type theory, introduced by Russell in *Principia Mathematica* (1903–1910) and refined through the ramified theory of types, resolves the paradoxes by restricting the closure principle. The core mechanism is **stratification**: objects are partitioned into levels (types), and the membership relation is constrained so that a collection at level n can only contain objects at levels strictly below n. The class `R = {x : x ∉ x}` is not well-formed because the condition `x ∉ x` requires `x` to be both a member and a set at the same level, which type theory prohibits.

**Simple type theory** (the "unramified" fragment) assigns:
- Type 0: individuals.
- Type 1: sets of individuals.
- Type 2: sets of sets of individuals.
- And so on.

The formation rule is `x ∈ y` is well-formed iff `type(y) = type(x) + 1`. Under this rule, `x ∈ x` is ill-typed for every x, so the Russell class cannot be constructed. The comprehension axiom is revised to: for any predicate `φ(x)` where `x` ranges over type n, there exists a set of type `n+1` containing exactly those x satisfying `φ`. The predicate `x ∉ x` is not typeable, so no Russell class is formed.

**Ramified type theory** adds a second dimension of stratification to handle semantic paradoxes. A statement about truth is assigned not just a type (what it refers to) but an **order** (what truth-predicates it may invoke). The liar sentence "this sentence is false" is blocked because a truth predicate of order k can only apply to sentences of order less than k, and the sentence's own truth predicate must be of higher order than the sentence itself, making self-application impossible.

The cost is severe: ramified type theory cannot express certain well-formed mathematical statements. A universal claim like "every real number has a least upper bound" must specify the order of the quantifier, and the proof that the supremum exists may require a higher-order quantifier than the statement itself. This led to the **axiom of reducibility**, which asserts that every higher-order predicate is coextensive with a first-order one, effectively collapsing the ramification. The axiom is ad hoc: it has no independent justification and is introduced solely to recover expressiveness that the type system took away. Ramsey (1925) argued that the ramification is unnecessary for set-theoretic paradoxes and is only relevant to semantic ones, leading most modern formulations to adopt simple type theory and handle semantic paradoxes by other means.

Modern descendants of type theory include Martin-Löf dependent type theory and the calculus of constructions underlying Coq and Lean. These systems maintain consistency by enforcing stratification through the type-checking algorithm itself: the well-typed terms are exactly those that can be constructed without paradox, and type-checking is decidable. The halting problem for general computation does not arise because the type system restricts computation to total functions (or, in systems with general recursion like Lean's meta-level, non-terminating terms are excluded from the core logic).

### 2.2 Hierarchical Truth: Tarski's Object/Meta-Language Distinction

Tarski (1933) proposed a resolution to the liar paradox that is the semantic analogue of type theory. The mechanism is a strict separation between an object language `L₀` and a metalanguage `L₁` in which the truth predicate for `L₀` is defined.

The truth predicate `True₀(·)` is a predicate of `L₁`, not of `L₀`. It is defined by the T-schema restricted to `L₀`:

```
For every sentence φ of L₀:  True₀(⌜φ⌝) ↔ φ
```

where `⌜φ⌝` is the Gödel code of φ, a term of `L₁`. The liar sentence "this sentence is false" cannot be constructed in `L₀` because `L₀` has no truth predicate. To express "sentence S of `L₀` is false," one must ascend to `L₁`. To express "sentence S of `L₁` is false," one must ascend to `L₂`, and so on.

The construction is iterated into a transfinite hierarchy:

```
L₀ ⊂ L₁ ⊂ L₂ ⊂ ... ⊂ L_ω ⊂ L_{ω+1} ⊂ ...
```

Each level `L_{α+1}` adds a truth predicate `True_α` for `L_α`. At limit ordinals, the language is the union of all prior levels. The hierarchy is **irreducible**: no level can define its own truth predicate (Tarski's theorem), so there is no level at which the full T-schema holds unrestrictedly.

The structural cost is that there is no single language in which one can say "a sentence is true" simpliciter. Every truth attribution must specify a level, and the level is always higher than the sentence being attributed. This is philosophically dissatisfying: ordinary discourse routinely makes unqualified truth claims, and the hierarchy requires fragmenting them. Kripke (1975) raised the further objection that the level of a sentence is often not determinable from its content. "Everything Nixon said about Watergate is true" is a truth claim, but the sentences it quantifies over may include sentences about truth, whose levels depend on what Nixon actually said. The hierarchy cannot assign a fixed level to such a sentence in advance.

### 2.3 Kripke's Fixed-Point Theory: Partial Truth

Kripke's "Outline of a Theory of Truth" (1975) abandons classical bivalence and constructs a truth predicate that is partial: some sentences are true, some are false, and some are neither (or "undefined"). The construction uses a three-valued logic (typically Kleene's strong Kleene logic) and builds the truth predicate iteratively, starting from a language with no truth predicate and adding truth values monotonically until a fixed point is reached.

**Kleene's three-valued logic.** The truth values are {T, F, U} (true, false, undefined). The connectives are defined by:

| φ | ψ | ¬φ | φ ∧ ψ | φ ∨ ψ | φ → ψ |
|---|---|-----|-------|-------|-------|
| T | T | F | T | T | T |
| T | F | F | F | T | F |
| T | U | F | U | T | U |
| F | T | T | F | T | T |
| F | F | T | F | F | T |
| F | U | T | F | U | U |
| U | T | U | U | T | T |
| U | F | U | F | U | U |
| U | U | U | U | U | U |

The key property: if φ and ψ have classical values, the connectives produce classical values; if either is U, the result is U unless the classical value is already determined (e.g., `F ∧ ψ = F` regardless of ψ).

**The evaluation process.** Let `L` be a base language without a truth predicate, interpreted over a classical structure M. Kripke defines a sequence of partial truth predicates `True_α` indexed by ordinals:

1. `True_0(⌜φ⌝)` is undefined for all sentences φ. The extension and anti-extension of `True_0` are both empty.
2. `True_{α+1}(⌜φ⌝)` is T if φ evaluates to T under the current partial interpretation (using `True_α` for truth-attributions within φ), F if φ evaluates to F, and U otherwise.
3. At limit ordinals λ, `True_λ` is the union of all prior stages: `True_λ = ∪_{α<λ} True_α`.

The process is monotone: if `True_α(⌜φ⌝) = T`, then `True_β(⌜φ⌝) = T` for all `β > α`. By the Knaster-Tarski fixed-point theorem, the sequence reaches a least fixed point `True_κ` at some ordinal κ (for countable languages, `κ ≤ ω₁`).

At the fixed point, the liar sentence L satisfying `L ↔ ¬True(L)` evaluates as follows: `True(L)` is U (since L has not stabilized to T or F at any stage), so `¬True(L)` is U, so `L` is U. The liar is **undefined**, not false. This is a "truth-value gap" rather than a contradiction. The theory remains consistent because the gap prevents the T-schema from producing a contradiction: `True(⌜L⌝) ↔ L` evaluates to `U ↔ U`, which is U, not a contradiction.

**Strengths and limits.** Kripke's construction allows a single language to contain its own truth predicate (partially defined), which Tarski's hierarchy cannot. Ordinary non-paradoxical sentences receive classical truth values. The construction handles "grounded" sentences correctly: a sentence whose truth value can be determined by tracing dependencies to non-semantic facts receives a classical value.

The limitation is the **revenge problem**. Consider the sentence E: "This sentence is false or undefined." Under Kripke's scheme, if E is false, then "E is false or undefined" is true, so E is true, contradiction. If E is undefined, then "E is false or undefined" is true, so E is true, contradiction. If E is true, then "E is false or undefined" is false, contradiction. The sentence E, called the **revenge liar** or the **strengthened liar**, cannot be handled by any three-valued scheme that adds "undefined" as a third value, because the liar can exploit the new value. Every finitely-valued truth predicate faces a revenge version: if the predicate has values `v₁, ..., vₙ`, the sentence "this sentence does not have value `v₁`" generates a contradiction if the sentence's value is `v₁`, and the sentence "this sentence has none of the values `v₁, ..., vₙ`" generates a contradiction if the sentence has any of them. This is the central open problem of truth-theoretic resolutions.

### 2.4 Paraconsistent Logic: Accepting the Contradiction

Paraconsistent logics accept that some contradictions are derivable but deny that contradictions explode. The principle *ex falso quodlibet* (`φ, ¬φ ⊢ ψ` for arbitrary ψ) is rejected, so a theory can contain `φ ∧ ¬φ` without becoming trivial. The liar paradox is then simply a true contradiction, a **dialetheia**.

The most developed paraconsistent approach is Graham Priest's **dialetheism** (1987, 2006), built on the logic LP (Logic of Paradox, a three-valued logic where the third value is "both" rather than "undefined"):

| Truth value | ¬ | ∧ (with T) | ∧ (with F) | ∧ (with B) |
|---|---|---|---|---|
| T | F | T | F | B |
| F | T | F | F | F |
| B (both) | B | B | F | B |

In LP, the truth values are {T, F, B} where B means "both true and false." The designated values (those that count as "assertible") are T and B. The liar sentence receives value B: it is both true and false. The T-schema `True(⌜L⌝) ↔ L` is satisfied because both sides are B, and `B ↔ B` is designated.

**The cost of paraconsistency.** LP preserves the unrestricted T-schema and classical reasoning for non-paradoxical sentences, but it requires revising classical logic. The key losses:

- **Modus ponens fails** in the material-conditional form. If `φ → ψ` is defined as `¬φ ∨ ψ`, then `φ → ψ` can be designated (B) while φ is designated (T) and ψ is not (F), blocking modus ponens. LP requires a relevant or relevant-like conditional, not the material conditional.
- **Disjunctive syllogism fails.** From `φ ∨ ψ` and `¬φ`, we cannot infer `ψ`, because `φ ∨ ψ` might be B (designated) and `¬φ` B (designated) while `ψ` is F.
- **Contraposition, proof by contradiction, and reductio ad absurdum** all fail in their classical forms.

The Curry paradox is particularly challenging for paraconsistent approaches because it does not use negation. If the conditional validates contraction and modus ponens, Curry trivializes the theory even in a paraconsistent setting. Priest's response is to use a conditional that does not validate contraction, but this weakens the logic substantially and makes the conditional behave very differently from the classical or material conditional.

### 2.5 Intuitionistic and Relevance Logics: Revising the Conditional

**Intuitionistic logic** resolves some paradoxes by rejecting the law of excluded middle (`φ ∨ ¬φ`) and double-negation elimination. In intuitionistic logic, `¬¬φ ⊬ φ`, so a proof that `¬φ` leads to a contradiction does not establish `φ` directly. This blocks certain paradox derivations that rely on excluded middle or reductio.

However, intuitionistic logic does not by itself resolve the liar paradox. The liar sentence `L ↔ ¬L` in intuitionistic logic still produces a problem: from `L → ¬L` and `¬L → L`, we derive `L → ¬L → L`, which gives `L → ¬L` and then `¬L` (by applying `L → ¬L` to L), and then `L` (by `¬L → L`). The contradiction `L ∧ ¬L` is derivable in intuitionistic logic. Intuitionistic logic blocks the classical move from `¬(L ∧ ¬L)` to excluded middle, but it does not prevent the derivation of the contradiction itself. The liar is not specifically a classical-logic phenomenon; it is a self-reference phenomenon.

**Relevance logic** targets the Curry paradox and related conditional-based paradoxes by requiring that premises be relevantly connected to conclusions. The key revision is to the conditional: in relevance logic, `φ → ψ` requires that φ actually be used in the derivation of ψ. The structural rule of **contraction** (using a premise twice is the same as using it once) is the target. In substructural logics that reject contraction (linear logic and its relatives), the Curry derivation breaks down because the step that uses the conditional `C → (True(C) → ⊥)` twice—once to derive `True(C) → ⊥` and once to derive `⊥`—requires contracting the premise, which the logic forbids.

The cost of rejecting contraction is that the resulting logics are weaker than classical logic in ways that affect ordinary mathematical reasoning. Most mathematical proofs use contraction freely (any time a lemma is applied more than once, or a hypothesis is used in multiple branches of a case split). Linear logic, the best-developed contraction-free system, partitions the logic into additive and multiplicative fragments, and mathematical theorems must be re-examined to determine which fragment they inhabit.

### 2.6 Revision Theory of Truth

Gupta and Belnap's **revision theory of truth** (1993) takes a different approach: rather than constructing a fixed point, it treats truth as a **circular concept** defined by a revision process that never stabilizes. The theory defines truth via a revision rule that, given an initial "hypothesis" about the extension of the truth predicate, produces a revised hypothesis by evaluating all sentences under the current hypothesis.

Formally, let `h: Sentences → {T, F}` be a hypothesis (a total assignment of classical truth values to all sentences). The revision operator `τ` maps `h` to `τ(h)` where:

```
τ(h)(⌜φ⌝) = T  if φ evaluates to T under hypothesis h
τ(h)(⌜φ⌝) = F  if φ evaluates to F under hypothesis h
```

For non-semantic sentences (grounded in non-semantic facts), `τ` stabilizes immediately. For the liar sentence `L ↔ ¬True(L)`, the revision alternates: if `h(L) = T`, then `τ(h)(L) = F`, then `τ²(h)(L) = T`, and so on, oscillating forever.

A sentence is **stable** under a hypothesis h if the revision sequence starting from h eventually assigns it a constant value. A sentence is **stably true** if it is stably T under every "cofinite" hypothesis (one that agrees with the actual world on all but finitely many sentences), and **stably false** if it is stably F under every cofinite hypothesis. Sentences that are neither are **unstable**. The liar is unstable: it alternates between T and F under every hypothesis.

The revision theory preserves classical logic for all stable sentences and treats unstable sentences as having no determinate truth value. Unlike Kripke's fixed point, the revision theory classifies more sentences as determinate: a sentence like "the liar sentence is not true" is stably true (it is T at every even stage and F at every odd stage, but under the cofinite criterion, the initial hypothesis washes out and the sentence stabilizes to T on the "not true" reading). The theory handles some revenge paradoxes better than Kripke's construction because the revision process can be extended to accommodate "unstable" as a semantic category, but the revenge problem recurs at the meta-level: "this sentence is not stably true" is itself paradoxical under the revision definition.

### 2.7 Contextual Theories of Truth

Contextual theories, developed by Glanzberg (2004), Simmons (1993), and others, treat the truth predicate as **context-dependent**. The extension of "true" shifts with the context of utterance, and the liar paradox is diagnosed as an illegitimate context shift within a single discourse.

The mechanism: in a context `c₁`, the truth predicate `True₁` applies to sentences not involving truth. A sentence like "snow is white" is true in `c₁` iff snow is white. When the liar sentence L ("this sentence is not true") is uttered, it invokes a truth predicate that must range over sentences in the current context. But L itself is in the current context, so L's truth predicate would have to apply to L, which would require a stronger context `c₂` with a wider truth predicate `True₂`. The utterance of L triggers a context shift from `c₁` to `c₂`, but in `c₂`, a new liar sentence can be constructed that requires `c₃`, and so on.

The structural similarity to Tarski's hierarchy is intentional, but the contextual theory differs in that the levels are not fixed in advance. They are generated by the dynamics of discourse, and the same sentence can be evaluated in different contexts without being assigned a permanent level. The theory aims to capture the intuition that ordinary speakers use "true" without specifying a level and that the level is determined by what is being evaluated.

The cost is a complication of the semantics. The truth predicate's extension is not a function of the world alone but of the world plus the context, and the context-shift mechanism must be formalized precisely. Glanzberg's implementation uses Kaplan-style semantics with character (a function from contexts to contents) distinguishing the truth predicate's behavior across contexts. The formal details are intricate, and the relationship between contextual theories and the revenge problem is an active area of research.

## 3. High-Performance Implementation & Failure Modes

### 3.1 Implementing Type-Theoretic Resolution in Proof Assistants

Modern proof assistants (Coq, Lean, Agda) implement type-theoretic resolutions. The implementation architecture is:

1. **Term language.** Expressions are typed at the syntactic level. The type of each term is determined by the typing rules, which enforce stratification. The term `λ x. x ∈ x` is not typeable because `∈` requires its left argument to have a type one level below its right argument, and `x` cannot have two different types simultaneously.

2. **Type-checking algorithm.** Given a term `t` and a type `T`, the algorithm decides whether `t : T` is derivable. For dependent type theories with decidable type-checking (the Martin-Löf fragment, the calculus of inductive constructions), this is a terminating algorithm. The Curry-Howard correspondence ensures that every well-typed term corresponds to a valid proof, so type-checking doubles as proof verification.

3. **Paradox prevention as a type system invariant.** The type system is designed so that the Girard paradox (the type-theoretic analogue of Russell's paradox) is not derivable. In Coq's Calculus of Inductive Constructions, this is achieved by the **universe hierarchy**: Type₀ : Type₁ : Type₂ : ..., and a term of type `Type_i` cannot be applied to itself. In Agda, the hierarchy is controlled by universe levels, and `Set ℓ : Set (ℓ + 1)` with no fixed point. In Lean, the hierarchy is similar, and the `meta` keyword (now deprecated in Lean 4) provided an unsafe escape hatch that could introduce inconsistency if used carelessly.

**Failure mode: universe inconsistency.** The most common implementation failure is universe inconsistency: attempting to construct a term where a universe level is required to be strictly greater than itself. For example, in Coq, `Definition foo (A : Type) : Type := A` works, but `Definition bar : Type @ Type := Type` fails because it would require `Type₀ : Type₀`, which the hierarchy forbids. This is the type-theoretic manifestation of Russell's paradox being blocked.

**Failure mode: positivity violations.** Inductive definitions in Coq and Agda must satisfy a positivity condition: the type being defined may not appear in a negative position in its own arguments. `Inductive Bad := mkBad : (Bad -> False) -> Bad` is rejected because `Bad` appears negatively (to the left of an arrow) in its own constructor. Without positivity, the inductive type could be used to derive a contradiction via a variant of the liar paradox: define a function `f : Bad -> False` by `f (mkBad g) = g (mkBad g)`, which gives `f (mkBad f) = f (mkBad f)`, a recursive call that, combined with the falsity, produces `False`.

**Failure mode: non-termination.** In systems that allow general recursion (Lean's meta-level, some Agda configurations with `--type-in-type`), a non-terminating term can be used to inhabit any type, including `False`. The halting problem ensures there is no algorithm that can separate terminating from non-terminating terms in general, so systems that admit general recursion are inconsistent as logics. The solution is either to restrict recursion to structurally decreasing arguments (Coq, Agda by default) or to separate the logical core (where all functions terminate) from a computational meta-level (where general recursion is allowed but results are not part of the proof term).

### 3.2 Implementing Kripke's Construction: The Evaluation Algorithm

Kripke's fixed-point construction can be implemented as an iterated evaluation procedure. The algorithm operates on a finite approximation (since real implementations handle finite or recursively enumerable languages).

**Data structures:**
- `valence: Sentence → {True, False, Unknown}` — the current partial truth assignment.
- `dependencies: Sentence → Set[Sentence]` — for each sentence, the set of truth-attributions it contains.

**Algorithm:**

```
function kripke_fixed_point(sentences: Set[Sentence]) → Valuation:
    v := {s → Unknown for all s in sentences}
    repeat:
        changed := false
        for each s in sentences:
            new_val := evaluate(s, v)
            if new_val ≠ v[s]:
                v[s] := new_val
                changed := true
    until not changed
    return v

function evaluate(s: Sentence, v: Valuation) → {True, False, Unknown}:
    match s:
        case Atomic(p):      return classical_value(p)
        case ¬t:             return negate(evaluate(t, v))
        case t ∧ u:          return kleene_and(evaluate(t, v), evaluate(u, v))
        case t ∨ u:          return kleene_or(evaluate(t, v), evaluate(u, v))
        case True(⌜t⌝):     return v[t]  // circular reference resolved by lookup
```

The `True(⌜t⌝)` case is the critical one: it looks up the current valuation of `t` rather than evaluating `t` recursively. This ensures that the process is monotone and converges to a fixed point.

**Failure mode: non-monotone updates.** If the evaluation function can change a sentence from True to False (or vice versa) across iterations, the process is not monotone and may not converge. Kripke's construction ensures monotonicity by using Kleene's strong logic, where once a sentence becomes True (or False), additional information can only confirm it, never overturn it. An implementation that uses a non-monotone logic (default logic, circumscription) for the evaluation step would not have this guarantee and might cycle indefinitely.

**Failure mode: revenge at the implementation level.** If the implementation language itself has a truth predicate (as in a meta-circular interpreter), the revenge liar "this sentence is not true or unknown" can be expressed in the implementation language, and the three-valued evaluator cannot handle it. The implementation must either stratify the language (evaluate object-language sentences with a meta-language evaluator that does not share the object language's truth predicate) or accept the limitation that the evaluator is correct only for sentences that do not mention the evaluator's own truth predicate.

### 3.3 Implementing Paraconsistent Reasoning: LP as a Post-Processing Layer

Paraconsistent reasoning is rarely implemented as a standalone theorem prover. The practical approach is to use a classical theorem prover and add a **consistency-checking post-processing layer** that filters out explosive inferences. The architecture:

1. **Classical derivation.** A standard theorem prover (resolution, tableaux, DPLL) derives consequences from the premise set, including any contradictions.
2. **Consistency filtering.** Each derived conclusion is checked for consistency with the non-contradictory subset of the premise set. Conclusions that depend on a contradiction (traceable via the proof's dependency graph) are flagged as paraconsistent and treated as unreliable.
3. **Belief revision.** When a contradiction is detected, the system does not collapse but instead marks the contradictory propositions as "contested" and continues reasoning about non-contested propositions normally.

This is the architecture used in paraconsistent logic programming (particularly the Annotated Logic Programs of Subrahmanian and the paraconsistent answer-set programming systems). The key implementation challenge is tracking the dependency graph efficiently: in a resolution-based prover, the proof trace records which clauses were used in each inference, and the consistency filter checks whether any of those clauses participate in a known contradiction.

**Failure mode: reasoning degradation.** In a paraconsistent setting, certain classical inference patterns produce incorrect results. If the system does not explicitly block disjunctive syllogism (from `p ∨ q` and `¬p`, infer `q`), it will produce wrong conclusions when `p` is contradictory. The implementation must track which inference rules are valid in the paraconsistent fragment and restrict the prover accordingly. This is a substantial engineering effort, and most paraconsistent logic programming systems restrict the language to a decidable fragment where the validity of inference rules can be checked syntactically.

**Failure mode: trivialization under Curry.** If the system uses the material conditional and validates contraction, the Curry paradox trivializes the system even in paraconsistent mode. The implementation must either use a relevant conditional (which complicates the unification algorithm, since relevance constraints must be tracked through the proof) or restrict the language to exclude self-referential conditionals (which defeats the purpose of allowing self-reference in the first place). No fully satisfactory implementation of a paraconsistent system that handles Curry's paradox is known.

### 3.4 Formal Implications: Incompleteness, Undecidability, and the Limits of Formal Systems

The resolution strategies are not merely responses to individual paradoxes; they are constrained by deep meta-theorems that bound what any formal system can achieve.

**Gödel's first incompleteness theorem.** Any consistent, recursively axiomatizable theory T that is strong enough to express elementary arithmetic contains a sentence G such that neither G nor ¬G is provable in T. The sentence G, constructed by diagonalization, says "G is not provable in T." If T proves G, then T proves "G is not provable in T," and T also proves "T proves G" (by the proof it just produced), so T is inconsistent. If T proves ¬G, then T proves "G is provable in T," which means T proves that a proof of G exists, and since T is ω-consistent (or merely consistent, by Rosser's improvement), this means a proof of G does exist, contradicting the first case. So neither is provable.

The incompleteness theorem is a direct consequence of the diagonalization mechanism in section 1.4. The relation R is "is provable in T," and the diagonal sentence G says `¬Prov_T(⌜G⌝)`. The theorem shows that closure completeness (T can express its own provability predicate) plus consistency forces incompleteness: there is a sentence in the language of T that T cannot decide. This is the structural reason: no consistent, expressive, recursively axiomatized theory can be complete.

**Gödel's second incompleteness theorem.** Under the same hypotheses, T cannot prove its own consistency, formalized as `Con(T) = ¬Prov_T(⌜⊥⌝)`. The proof constructs a sentence that, via the Hilbert-Bernays-Löb derivability conditions, establishes `T ⊢ Con(T) → G`, and since `T ⊬ G` (by the first theorem), `T ⊬ Con(T)`. This means that the consistency of T can only be established in a stronger theory, which itself cannot prove its own consistency, leading to an infinite regress.

**Tarski's undefinability theorem.** No consistent, sufficiently expressive language can define its own truth predicate. Formally, there is no formula `True(x)` in the language of arithmetic such that for every sentence φ, `PA ⊢ True(⌜φ⌝) ↔ φ`. The proof is a direct application of the liar diagonalization: if such a formula existed, the fixed-point lemma would produce a sentence L with `PA ⊢ L ↔ ¬True(⌜L⌝)`, and substituting the definition of `True` would give `PA ⊢ L ↔ ¬L`, making PA inconsistent. This is the formal version of the claim that the T-schema cannot be unrestrictedly satisfied.

**Löb's theorem.** If `T ⊢ Prov_T(⌜φ⌝) → φ`, then `T ⊢ φ`. This is a strengthening of the second incompleteness theorem (taking `φ = ⊥` gives the second theorem). It shows that a theory can only prove that its proofs are sound for a sentence φ if it can already prove φ directly. The proof uses the fixed-point lemma to construct a sentence L with `T ⊢ L ↔ (Prov_T(⌜L⌝) → φ)`, then derives `T ⊢ Prov_T(⌜L⌝) → (Prov_T(⌜φ⌝) → φ)`, and manipulates the derivability conditions to reach the conclusion. Löb's theorem constrains self-referential reasoning: any theory that can reason about its own proofs is subject to this theorem, and it shows that self-referential provability claims are tightly constrained.

**The halting problem.** The undecidability of the halting problem is the computational analogue of the first incompleteness theorem. There is no algorithm that, given a program P and input w, determines whether P halts on w. The proof uses diagonalization: assume such an algorithm H exists, construct a program D that halts iff H says it does not halt, and run D on itself. The contradiction shows H cannot exist. This is identical in structure to the liar paradox: the "halting" predicate plays the role of "truth," and D is the diagonal sentence.

**Rice's theorem.** A generalization: every non-trivial semantic property of programs is undecidable. This means that any attempt to classify programs by their behavior (does P halt on all inputs? does P compute a total function? does P output 0?) is algorithmically impossible. The proof reduces the halting problem to each such property, showing that decidability of the property would imply decidability of the halting problem.

**Computability-theoretic implications for resolution strategies.** Type-theoretic resolutions work because type-checking is decidable: the algorithm terminates and gives a definite yes/no answer. This comes at the cost of expressiveness (only total functions are typeable). Paraconsistent resolutions trade decidability for expressiveness: in an inconsistent theory, the set of theorems is not recursively enumerable (or if it is, it is the set of all formulas, which is trivial). Kripke's construction is effective for finite or recursively enumerable languages (the fixed point is reached in countably many stages), but the classification of a sentence as "grounded" or "ungrounded" is generally undecidable, since it requires determining whether the revision process stabilizes, which is equivalent to the halting problem for arbitrary programs.

### 3.5 The Revenge Problem as a Universal Failure Mode

Every resolution strategy that introduces a new semantic category (undefined, both, unstable, context-shifted) faces the revenge problem: the liar sentence can be reformulated to exploit the new category. The strengthened liar for Kripke's three-valued logic is "this sentence is not true" where "not true" means "false or undefined." For paraconsistent LP, it is "this sentence is false but not true" (i.e., it has value F, not B). For revision theory, it is "this sentence is not stably true."

The revenge problem is not a coincidence but a structural feature. Any semantic theory that introduces a set of "status values" `S = {v₁, ..., vₙ}` and defines "true" as having a particular subset of these values faces the diagonal sentence: "this sentence does not have any of the values in the true-subset." If the theory is expressive enough to state this, the sentence creates a contradiction. The only escape is to make the meta-theory inexpressive enough that the sentence cannot be stated, which is the Tarski hierarchical approach: each level's truth predicate cannot be mentioned at that level.

This leads to a classification of resolution strategies by their relationship to revenge:

- **Hierarchical strategies** (Tarski, type theory) avoid revenge by blocking self-reference entirely. They pay in expressiveness: the language cannot state certain natural sentences.
- **Fixed-point strategies** (Kripke, partial logic) face revenge and handle it by declaring the revenge sentence "undefined" (or whatever the gap value is), but the revenge sentence can be reformulated to exploit the gap, and the process iterates. These strategies accept that some sentences are beyond the theory's reach but do not provide a principled boundary.
- **Paraconsistent strategies** (dialetheism, LP) face revenge and handle it by accepting the revenge contradiction as a dialetheia. This is the most permissive approach: it accepts contradictions rather than trying to exclude them. The cost is the loss of classical inference rules and the difficulty of constraining the conditional.
- **Revision strategies** face revenge and handle it by declaring the revenge sentence "unstable." The revision theory's notion of stability is more fine-grained than Kripke's groundedness, but the revenge problem recurs at the meta-level.
- **Contextual strategies** face revenge and handle it by positing context shifts that prevent the revenge sentence from being evaluated in a single context. This is promising but requires a fully formalized context-shift mechanism, which remains an open problem.

No known resolution fully solves the revenge problem. The literature has converged on the view that any resolution involves a trade-off between expressiveness (what sentences the theory can handle) and logical strength (which inference rules are valid), and the choice of trade-off is driven by the application domain rather than by a universal optimality criterion.

## 4. Summary & Verification Matrix

### 4.1 Resolution Strategies: Trade-off Summary

| Strategy | Invariant sacrificed | Mechanism | Strengths | Weaknesses |
|---|---|---|---|---|
| Simple type theory | Closure (stratification) | Block `x ∈ x` by typing | Decidable type-checking, constructive | Cannot express impredicative definitions |
| Ramified type theory | Closure (orders) | Block self-reference of truth predicates | Handles both set and semantic paradoxes | Reducibility axiom is ad hoc; loses expressiveness |
| Tarski hierarchy | Closure (language levels) | Truth predicate is meta-linguistic | Clean, classical, well-understood | No single language for all truth claims |
| Kripke fixed-point | Classical bivalence | Partial truth predicate, gaps | Single language, handles grounded truth | Revenge problem; undecidable groundedness |
| Paraconsistent (LP) | Non-explosion | Accept contradictions as dialetheia | Preserves T-schema fully | Loses modus ponens, disjunctive syllogism |
| Intuitionistic | Excluded middle | Constructive truth | Compatible with computability | Does not resolve liar alone |
| Relevance / substructural | Contraction | Relevant conditional | Handles Curry paradox | Weak logic; re-engineers mathematics |
| Revision theory | Classical stability | Iterated revision process | Finer classification than Kripke | Revenge at meta-level; complex semantics |
| Contextual | Fixed extension | Context-dependent truth | Models ordinary discourse | Context-shift mechanism hard to formalize |

### 4.2 Paradox-to-Resolution Verification Matrix

| Paradox | Closure principle | Type theory | Tarski | Kripke | Paraconsistent | Revision | Contextual |
|---|---|---|---|---|---|---|---|
| Russell's (sets) | Naive comprehension | ✓ (blocks `x∈x`) | N/A | N/A | ✓ (accepts `R∈R ∧ R∉R`) | N/A | N/A |
| Liar | T-schema | ✓ (ramified) | ✓ (levels) | ✓ (gap) | ✓ (dialetheia) | ✓ (unstable) | ✓ (context shift) |
| Strengthened liar | Revenge on T-schema | ✓ (higher level) | ✓ (higher level) | ✗ (revenge) | ✓ (accepts new dialetheia) | ✓ (unstable) | ✓ (context shift) |
| Curry | T-schema + conditional | ✓ (ramified) | ✓ (levels) | ✗ (no negation needed) | ✗ (needs relevant conditional) | ✓ (unstable) | ✓ (context shift) |
| Yablo (ω-liar) | Bivalence + ω-sequence | ✓ (ramified ω-levels) | ✓ (transfinite levels) | ✓ (ω-gaps) | ✓ (ω-dialetheia) | ✓ (ω-unstable) | ? (open) |
| Gödel sentence | Provability + diagonalization | ✓ (blocks diagonal) | ✓ (meta-language) | N/A (not truth) | N/A (not truth) | N/A | N/A |
| Grelling (heterological) | "Denotes itself" | ✓ (types on adjectives) | ✓ (levels) | ✓ (gap) | ✓ (dialetheia) | ✓ (unstable) | ✓ |
| Berry ("nameable in < 18 words") | Definability | ✓ (types) | ✓ (levels) | ✓ (gap) | ✓ | ✓ | ✓ |
| Richard (definable reals) | Definability | ✓ (types) | ✓ (levels) | ✓ (gap) | ✓ | ✓ | ✓ |
| Sorites (vagueness) | Bivalence over predicates | N/A | N/A | ✓ (gaps = borderline) | ✓ (overlap) | ? | ? |

### 4.3 Meta-Theorem Implications

| Meta-theorem | What it constrains | Implication for resolution strategies |
|---|---|---|
| Gödel I | Completeness of expressive theories | No recursive, consistent, expressive theory is complete; incompleteness is structural, not eliminable |
| Gödel II | Self-consistency proofs | No theory proves its own consistency; hierarchical proof of consistency is the only option |
| Tarski undefinability | Self-definition of truth | No language defines its own truth predicate; hierarchical truth is forced if classical logic is kept |
| Löb's theorem | Self-referential provability | `Prov(⌜φ⌝) → φ` implies φ; self-referential soundness claims are trivialized |
| Halting problem | Decidability of program behavior | No algorithm decides halting; type systems that guarantee termination must restrict expressiveness |
| Rice's theorem | Decidability of semantic properties | Any non-trivial semantic property of programs is undecidable |
| Church-Turing thesis | Computability boundary | All sufficiently expressive formal systems face the same computability limits |
| Cantor (diagonal) | Cardinality of power set | Any closure-complete collection is larger than its enumeration; diagonalization is unavoidable |

### 4.4 Verification Checklist for a Resolution Strategy

A proposed resolution of the paradoxes should be checked against the following criteria:

1. **Paradox coverage.** Does it resolve all the standard paradoxes (liar, strengthened liar, Curry, Yablo, Grelling, Berry, Richard), not just one? A resolution that handles the liar but not Curry is incomplete.
2. **Revenge resistance.** Does it survive the revenge problem, or does it merely push the contradiction to a higher level? If it introduces a new semantic category, can the liar exploit it?
3. **Expressiveness.** What natural sentences can the theory no longer express? If the theory blocks "this sentence is true" as well as "this sentence is false," it has over-restricted.
4. **Logical strength.** Which classical inference rules are preserved? A resolution that preserves modus ponens, disjunctive syllogism, and proof by contradiction is more useful than one that does not.
5. **Compositionality.** Does the truth value of a compound sentence depend only on the truth values of its components, or does it require global information? Compositional theories are easier to implement and reason about.
6. **Computability.** Is the truth predicate computable, or at least recursively enumerable? If the theory classifies sentences as true/false/gap, is the classification decidable?
7. **Consistency at the meta-level.** Is the meta-theory in which the resolution is formulated itself consistent? If the meta-theory uses the same logic that the resolution revises, the resolution may be circular.
8. **Generality.** Does the resolution apply to paradoxes beyond truth and sets (e.g., epistemic paradoxes, deontic paradoxes, game-theoretic paradoxes), or is it specific to one domain?

No known resolution satisfies all eight criteria. The honest state of the field is that the paradoxes have not been "solved" in the sense of a single, universally accepted resolution. What the literature provides is a menu of strategies, each with a defined trade-off profile, and the choice among them is driven by the demands of the application. Type theory dominates in proof assistants because decidability of type-checking is the primary requirement. Kripke's construction dominates in philosophical logic because it preserves the most natural truth predicate. Paraconsistent logic dominates in inconsistent database applications because it preserves the most information. The formal implications (incompleteness, undecidability, undefinability) are not problems to be solved but structural features of any sufficiently expressive formal system, and they set the boundary within which all resolution strategies must operate.
