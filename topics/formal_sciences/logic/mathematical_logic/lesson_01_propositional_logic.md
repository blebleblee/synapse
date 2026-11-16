# Lesson 1: Propositional Logic — Syntax, Semantics, Connectives

## 1. First-Principles Intuition & Invariants

Propositional logic stands as the most elementary stratum of formal reasoning, yet its conceptual machinery underpins virtually all rigorous mathematics, computer science verification, circuit design, and automated theorem proving. At its essence, propositional logic isolates the skeletal structure of declarative reasoning by treating atomic statements as indivisible units—truth-bearing entities whose internal structure remains opaque—and constructing compound statements through precisely defined connectives. The discipline bifurcates into two complementary investigations: **syntax**, the combinatorial rules governing well-formed formulas, and **semantics**, the mathematical theory of truth assignments that breathe meaning into these syntactic objects.

The historical lineage traces to Aristotle's syllogistic reasoning, but the modern algebraic formulation crystallized through the work of George Boole, Augustus De Morgan, and Gottlob Frege in the nineteenth century. Boole's insight was radical: logical operations obey algebraic laws analogous to arithmetic, permitting mechanical manipulation divorced from intuitive meaning. Frege later axiomatized propositional logic within his *Begriffsschrift*, establishing the concept of a formal language—a recursive syntactic specification paired with interpretation rules. This duality between form and meaning constitutes the bedrock invariant: syntax provides a finitary, combinatorial object amenable to computational manipulation, while semantics furnishes the mathematical justification that these manipulations preserve truth.

The fundamental invariant of propositional logic is **compositionality**: the truth value of a compound formula depends exclusively on the truth values of its constituent atomic propositions and the semantics of the connectives binding them. This principle, sometimes called the **principle of truth-functionality**, distinguishes propositional logic from richer systems like modal or temporal logic, where truth depends on possible worlds or temporal indices. Truth-functionality guarantees that semantic evaluation reduces to finite computation: given $n$ atomic propositions, there exist exactly $2^n$ possible truth assignments, and each formula induces a well-defined Boolean function $f : \{0, 1\}^n \to \{0, 1\}$.

Three canonical semantic classifications partition the space of formulas. A **tautology** (or valid formula) evaluates to true under every truth assignment, representing logical laws that hold irrespective of contingent facts. The formula $p \lor \neg p$, the Law of Excluded Middle, exemplifies this: it asserts the dichotomy of truth and falsity, admitting no countermodel. Conversely, a **contradiction** (or unsatisfiable formula) evaluates to false under all assignments, such as $p \land \neg p$. Between these extremes lie **contingent** formulas, whose truth varies with the assignment, embodying statements whose veracity depends on factual circumstances. The satisfiability problem—determining whether a given formula admits at least one satisfying assignment—emerges as the central computational question, and despite propositional logic's simplicity, satisfiability is NP-complete, the canonical intractable problem that delineates the boundary of efficient computation.

Semantic entailment, denoted $\Gamma \models \phi$, formalizes the notion that formula $\phi$ is a logical consequence of premise set $\Gamma$: every truth assignment satisfying all formulas in $\Gamma$ must also satisfy $\phi$. This relation captures deductive validity—the preservation of truth from premises to conclusion—and grounds the soundness of formal proof systems. A proof calculus is **sound** when every derivable formula is semantically valid, ensuring that syntactic manipulation cannot manufacture falsehoods from truths. The converse property, **completeness**, asserts that every semantically valid formula possesses a formal derivation. For propositional logic, both properties hold: the system is sound and complete, a remarkable alignment between proof theory and model theory established by Emil Post and others in the early twentieth century.

## 2. Core Architecture & Mechanics

The construction of propositional logic proceeds through three interlocking layers: the definition of a formal language via recursive syntax rules, the assignment of meaning through truth-functional semantics, and the algebraic theory of logical equivalence and normal forms.

### Syntax: The Recursive Grammar of Well-Formed Formulas

We begin by fixing a countably infinite set of **propositional variables** (or atomic propositions), typically denoted $p, q, r, p_1, p_2, \ldots$, or in some contexts by capital letters $P, Q, R$. These variables represent primitive declarative statements whose truth or falsity remains unanalyzed within the logic. The set of **well-formed formulas** (wffs), denoted $\mathcal{L}$ or $\text{Form}$, arises through the following recursive definition:

1. Every propositional variable $p$ is a formula.
2. If $\phi$ is a formula, then $\neg \phi$ (negation, read "not phi") is a formula.
3. If $\phi$ and $\psi$ are formulas, then $(\phi \land \psi)$ (conjunction, "phi and psi"), $(\phi \lor \psi)$ (disjunction, "phi or psi"), $(\phi \to \psi)$ (implication, "phi implies psi"), and $(\phi \leftrightarrow \psi)$ (biconditional, "phi if and only if psi") are formulas.
4. Nothing else is a formula.

This inductive specification ensures that every formula possesses a unique parse tree, eliminating syntactic ambiguity. Parentheses enforce grouping; standard precedence conventions allow omission when clarity permits: negation binds most tightly, followed by conjunction and disjunction, with implication and biconditional weakest. Thus $\neg p \land q \to r$ parses as $((\neg p) \land q) \to r$.

The recursive structure induces a natural notion of **subformula**: $\psi$ is a subformula of $\phi$ if $\psi$ appears in the parse tree of $\phi$. Every formula decomposes uniquely into its **main connective** and immediate subformulas, a property exploited in proof by structural induction. The **length** or **size** of a formula counts the total number of connective and variable occurrences, governing the computational complexity of syntactic operations.

### Semantics: Truth Assignments and Valuation Functions

Meaning enters through the notion of a **truth assignment** (or valuation), a function $v : \{\text{propositional variables}\} \to \{0, 1\}$ assigning each atomic proposition a truth value, where 1 represents true and 0 represents false. Every truth assignment extends uniquely to a homomorphism $\bar{v} : \mathcal{L} \to \{0, 1\}$ mapping all formulas to truth values, defined recursively by the **truth tables** of the logical connectives.

The **negation** $\neg \phi$ inverts truth: $\bar{v}(\neg \phi) = 1$ if and only if $\bar{v}(\phi) = 0$. Formally:

$$
\begin{array}{c|c}
\phi & \neg \phi \\
\hline
1 & 0 \\
0 & 1
\end{array}
$$

The **conjunction** $\phi \land \psi$ is true precisely when both conjuncts are true, implementing logical "and":

$$
\begin{array}{cc|c}
\phi & \psi & \phi \land \psi \\
\hline
1 & 1 & 1 \\
1 & 0 & 0 \\
0 & 1 & 0 \\
0 & 0 & 0
\end{array}
$$

The **disjunction** $\phi \lor \psi$ is true when at least one disjunct is true, representing inclusive "or":

$$
\begin{array}{cc|c}
\phi & \psi & \phi \lor \psi \\
\hline
1 & 1 & 1 \\
1 & 0 & 1 \\
0 & 1 & 1 \\
0 & 0 & 0
\end{array}
$$

The **material implication** $\phi \to \psi$ merits careful attention, as its truth conditions diverge from colloquial usage. The formula is false precisely when the antecedent $\phi$ is true and the consequent $\psi$ is false; in all other cases, including when $\phi$ is false, the implication is true. This definition, sometimes called **material conditional**, renders "if-then" truth-functional at the cost of counterintuitive instances like "if 2 is odd, then the moon is made of cheese" evaluating to true:

$$
\begin{array}{cc|c}
\phi & \psi & \phi \to \psi \\
\hline
1 & 1 & 1 \\
1 & 0 & 0 \\
0 & 1 & 1 \\
0 & 0 & 1
\end{array}
$$

The implication satisfies the key semantic invariant: $\phi \to \psi$ is true if and only if whenever $\phi$ is true, $\psi$ is also true. The cases where $\phi$ is false are vacuously satisfied, a principle known as **ex falso quodlibet** or "from falsehood, anything follows."

The **biconditional** $\phi \leftrightarrow \psi$ is true when both formulas share the same truth value, formalizing logical equivalence within the object language:

$$
\begin{array}{cc|c}
\phi & \psi & \phi \leftrightarrow \psi \\
\hline
1 & 1 & 1 \\
1 & 0 & 0 \\
0 & 1 & 0 \\
0 & 0 & 1
\end{array}
$$

This connective decomposes as $(\phi \to \psi) \land (\psi \to \phi)$, capturing mutual implication.

### Functional Completeness and Expressive Adequacy

A natural question arises: are these five connectives essential, or could a smaller set suffice? The answer invokes the concept of **functional completeness**: a set of connectives is functionally complete if every Boolean function $f : \{0, 1\}^n \to \{0, 1\}$ can be expressed as a formula using only those connectives. The five-connective set $\{\neg, \land, \lor, \to, \leftrightarrow\}$ is overcomplete; in fact, the pair $\{\neg, \land\}$ or $\{\neg, \lor\}$ suffices. To demonstrate, observe that disjunction expresses via De Morgan's law:

$$\phi \lor \psi \equiv \neg (\neg \phi \land \neg \psi)$$

Similarly, implication and biconditional reduce:

$$\phi \to \psi \equiv \neg \phi \lor \psi \equiv \neg (\phi \land \neg \psi)$$

$$\phi \leftrightarrow \psi \equiv (\phi \to \psi) \land (\psi \to \phi)$$

Even more economically, a single connective can achieve functional completeness: the **Sheffer stroke** (NAND, denoted $\phi \mid \psi$, true except when both inputs are true) and the **Peirce arrow** (NOR, denoted $\phi \downarrow \psi$, true only when both inputs are false) are individually universal. For NAND:

$$\neg \phi \equiv \phi \mid \phi$$

$$\phi \land \psi \equiv (\phi \mid \psi) \mid (\phi \mid \psi)$$

This minimalism has practical significance in digital circuit design, where NAND gates serve as universal building blocks.

### Semantic Consequence and Logical Equivalence

Two formulas $\phi$ and $\psi$ are **logically equivalent**, written $\phi \equiv \psi$ or $\phi \Leftrightarrow \psi$, if they share identical truth values under all truth assignments: for every valuation $v$, $\bar{v}(\phi) = \bar{v}(\psi)$. Logical equivalence partitions the set of formulas into equivalence classes, each representing a unique Boolean function. Key equivalences include:

**Idempotence**: $\phi \land \phi \equiv \phi$ and $\phi \lor \phi \equiv \phi$.

**Commutativity**: $\phi \land \psi \equiv \psi \land \phi$ and $\phi \lor \psi \equiv \psi \lor \phi$.

**Associativity**: $(\phi \land \psi) \land \chi \equiv \phi \land (\psi \land \chi)$ and similarly for disjunction, allowing unparenthesized notation $\phi \land \psi \land \chi$.

**Distributivity**: $\phi \land (\psi \lor \chi) \equiv (\phi \land \psi) \lor (\phi \land \chi)$ and $\phi \lor (\psi \land \chi) \equiv (\phi \lor \psi) \land (\phi \lor \chi)$.

**De Morgan's Laws**: $\neg (\phi \land \psi) \equiv \neg \phi \lor \neg \psi$ and $\neg (\phi \lor \psi) \equiv \neg \phi \land \neg \psi$.

**Double Negation**: $\neg \neg \phi \equiv \phi$.

**Absorption**: $\phi \land (\phi \lor \psi) \equiv \phi$ and $\phi \lor (\phi \land \psi) \equiv \phi$.

These laws form a Boolean algebra, a mathematical structure $(B, \land, \lor, \neg, 0, 1)$ satisfying these axioms. The set of equivalence classes of formulas under $\equiv$, ordered by semantic entailment, constitutes the **Lindenbaum-Tarski algebra**, a cornerstone of algebraic logic.

Semantic consequence, $\Gamma \models \phi$, holds when every truth assignment satisfying all formulas in the premise set $\Gamma$ also satisfies $\phi$. When $\Gamma = \emptyset$, this reduces to $\models \phi$, asserting that $\phi$ is a tautology. A formula $\phi$ is satisfiable if there exists an assignment making it true; it is **falsifiable** if some assignment makes it false. The satisfiability problem (SAT) is solvable in exponential time via exhaustive truth table enumeration over $2^n$ rows for $n$ variables, but no polynomial-time algorithm is known, and SAT is the prototypical NP-complete problem. Modern SAT solvers employ sophisticated heuristics—conflict-driven clause learning, watched literals, restarts—that achieve astonishing practical performance on industrial instances despite worst-case exponential complexity.

### Normal Forms: Conjunctive and Disjunctive Canonical Representations

Every propositional formula admits two canonical representations: **disjunctive normal form** (DNF) and **conjunctive normal form** (CNF). A **literal** is a propositional variable $p$ or its negation $\neg p$. A **clause** (in CNF) is a disjunction of literals, and a formula is in CNF if it is a conjunction of clauses. Dually, a **term** (in DNF) is a conjunction of literals, and a formula is in DNF if it is a disjunction of terms.

Every formula $\phi$ has an equivalent DNF, constructable directly from its truth table: for each truth assignment $v$ making $\phi$ true, form a term that conjoins $p_i$ if $v(p_i) = 1$ and $\neg p_i$ if $v(p_i) = 0$. The disjunction of all such terms yields a DNF equivalent to $\phi$. For example, consider the formula $\phi$ over variables $p, q$ with truth table:

$$
\begin{array}{cc|c}
p & q & \phi \\
\hline
1 & 1 & 1 \\
1 & 0 & 0 \\
0 & 1 & 1 \\
0 & 0 & 0
\end{array}
$$

The satisfying rows are $(p = 1, q = 1)$ and $(p = 0, q = 1)$, yielding terms $p \land q$ and $\neg p \land q$. Thus $\phi \equiv (p \land q) \lor (\neg p \land q)$, which simplifies via distributivity to $q$.

CNF construction proceeds similarly via falsifying rows or by applying De Morgan's laws to the DNF of $\neg \phi$ and negating. CNF is particularly significant in automated theorem proving and SAT solving, as the resolution proof rule—a sound and refutation-complete inference method—operates directly on CNF clauses.

## 3. High-Performance Optimization & Failure Modes

The practical deployment of propositional logic in verification, synthesis, and automated reasoning demands attention to computational efficiency, representation compactness, and boundary case handling. While propositional logic's decidability is a profound theoretical asset, the exponential explosion inherent in $2^n$ truth assignments necessitates sophisticated optimization strategies.

### Truth Table Enumeration and Complexity Scaling

The brute-force method for determining satisfiability, validity, or equivalence constructs the complete truth table, requiring $2^n$ rows for $n$ propositional variables. Each row demands $O(|\phi|)$ time to evaluate the formula $\phi$, where $|\phi|$ denotes formula size, yielding $O(2^n |\phi|)$ total complexity. For small formulas with $n \le 20$ variables, this remains tractable, but moderate-scale problems with $n \approx 100$ variables render exhaustive enumeration infeasible: $2^{100} \approx 10^{30}$ rows exceed all physical computation resources.

Modern SAT solvers circumvent this barrier through intelligent search space pruning. The **DPLL algorithm** (Davis-Putnam-Logemann-Loveland) combines unit propagation, pure literal elimination, and backtracking search. Unit propagation identifies clauses containing a single unassigned literal and fixes that literal's truth value to satisfy the clause, often triggering cascading simplifications. Pure literal elimination assigns truth values to variables appearing with consistent polarity throughout the formula. When neither heuristic applies, the algorithm speculatively assigns a variable, recursively simplifies, and backtracks upon encountering a conflict (an unsatisfiable empty clause). Enhancements like conflict-driven clause learning (CDCL) analyze conflicts to derive learned clauses that prune the search space, achieving state-of-the-art performance on industrial instances with millions of variables.

### Compactness: Binary Decision Diagrams and Symbolic Representation

Truth tables scale poorly in storage as well as computation: a formula over $n$ variables requires $2^n$ bits. **Binary Decision Diagrams** (BDDs), introduced by Randal Bryant, offer an alternative representation. A BDD is a directed acyclic graph where each non-terminal node represents a variable decision (if-then-else branching) and terminal nodes represent truth values 0 or 1. By enforcing variable ordering and canonicalizing through reduction rules (merging isomorphic subgraphs and eliminating redundant tests), **Reduced Ordered Binary Decision Diagrams** (ROBDDs) provide a canonical, often compact representation for Boolean functions.

For certain functions, ROBDDs remain exponential in size—multiplication circuits, for instance, admit no polynomial-size ROBDD regardless of variable ordering. However, many practical functions, particularly those arising in hardware verification (control logic, protocol verification), compress dramatically. BDDs support efficient logical operations: conjunction, disjunction, and negation execute in time polynomial in BDD size, and equivalence checking reduces to pointer equality. This makes BDDs the workhorse of symbolic model checking tools.

Variable ordering critically impacts BDD size. For a ripple-carry adder computing $c_n$ (the $n$-th carry bit), an optimal interleaved ordering $a_1, b_1, c_1, a_2, b_2, c_2, \ldots$ yields a BDD of size $O(n)$, while a poor ordering $a_1, \ldots, a_n, b_1, \ldots, b_n, c_1, \ldots, c_n$ results in exponential size. Finding the optimal ordering is NP-hard, but dynamic reordering heuristics and domain-specific insights often suffice.

### Semantic Entailment and the Deduction Theorem

Verifying semantic entailment $\Gamma \models \phi$ reduces to checking validity of the implication $\bigwedge \Gamma \to \phi$, or equivalently, unsatisfiability of $\bigwedge \Gamma \land \neg \phi$. This transformation, the **Deduction Theorem** at the semantic level, allows leveraging unsatisfiability solvers for entailment checking. In practice, this means encoding the premises and negated conclusion as a CNF formula and invoking a SAT solver: the formula is unsatisfiable if and only if the entailment holds.

The deduction theorem illuminates the duality between validity and unsatisfiability: $\phi$ is valid if and only if $\neg \phi$ is unsatisfiable. This duality underpins proof by contradiction (reductio ad absurdum): to prove $\Gamma \models \phi$, assume $\Gamma \cup \{\neg \phi\}$ and derive a contradiction, witnessing the unsatisfiability of the assumption set.

### Failure Modes: Vacuous Truth and the Material Conditional

The material implication $\phi \to \psi$ presents a persistent source of confusion and subtle errors, particularly in informal reasoning. The vacuous truth of implications with false antecedents—$0 \to 0$ and $0 \to 1$ both evaluate to true—admits logically valid but semantically bizarre statements. For instance, $(\text{moon is made of cheese}) \to (\text{pigs fly})$ is vacuously true. This divergence from natural language conditionals, which often carry presuppositions or causal connotations, demands vigilance when formalizing informal arguments.

A common pitfall arises in formalizing "if $\phi$ then $\psi$ else $\chi$" as $(\phi \to \psi) \land (\neg \phi \to \chi)$. This correctly captures the intended semantics: when $\phi$ holds, $\psi$ must hold, and when $\phi$ fails, $\chi$ must hold. However, naively translating as $(\phi \to \psi)$ alone omits the else-branch, permitting models where $\phi$ and $\psi$ are both false.

Another subtlety concerns the contrapositive: $\phi \to \psi$ is logically equivalent to $\neg \psi \to \neg \phi$, a fact exploited in proof strategies. However, the converse $\psi \to \phi$ and inverse $\neg \phi \to \neg \psi$ are not equivalent to the original implication; they are equivalent to each other but logically independent of $\phi \to \psi$.

### Satisfiability Modulo Theories and Extensions

Pure propositional logic, while foundational, lacks the expressiveness to reason about arithmetic, data structures, or quantified statements. **Satisfiability Modulo Theories** (SMT) extends propositional satisfiability by interpreting certain predicates via background theories—linear arithmetic, bit-vectors, arrays, uninterpreted functions. An SMT solver combines a SAT solver with theory-specific decision procedures, alternating between Boolean constraint solving and theory constraint solving. Modern SMT solvers like Z3, CVC5, and Yices handle industrial-scale verification and synthesis tasks by leveraging this modular architecture.

The transition from propositional logic to first-order logic introduces quantifiers $\forall$ and $\exists$, expanding expressive power at the cost of decidability: first-order satisfiability is undecidable in general, and validity checking is only semi-decidable. Nonetheless, restricted fragments—monadic first-order logic, Presburger arithmetic—retain decidability, and practical solvers employ quantifier instantiation heuristics to handle many real-world formulas.

### Optimization Heuristics and Preprocessing Transformations

Before invoking a SAT solver, preprocessing can dramatically reduce formula complexity. **Subsumption elimination** removes clauses that are supersets of others: if $C_1 \subseteq C_2$ as sets of literals, then $C_1$ subsumes $C_2$, and $C_2$ is redundant. **Self-subsuming resolution** identifies pairs of clauses $(C \lor x)$ and $(D \lor \neg x)$ where $C \subseteq D$, allowing elimination of literals from $D$. **Bounded variable elimination** substitutes out variables appearing in few clauses, trading formula size against clause count to accelerate downstream solving.

**Polarity analysis** detects variables appearing with consistent polarity (only positively or only negatively) across the formula, enabling pure literal elimination. **Equivalent literal detection** identifies variables constrained to have identical truth values (e.g., from clauses $(x \lor \neg y)$ and $(\neg x \lor y)$ forcing $x \equiv y$) and merges them.

These transformations, integrated in preprocessing engines like SatELite and CryptoMiniSat's inprocessing, reduce industrial SAT instances by orders of magnitude, often rendering previously intractable problems solvable in seconds.

### Boundary Cases and Degenerate Formulas

Two degenerate formulas warrant special attention: the **empty conjunction** $\bigwedge_{i \in \emptyset} \phi_i$, representing the vacuously true tautology 1 (or $\top$, pronounced "top"), and the **empty disjunction** $\bigvee_{i \in \emptyset} \phi_i$, representing the contradiction 0 (or $\bot$, pronounced "bottom"). These constants serve as identity elements: $\phi \land \top \equiv \phi$, $\phi \lor \bot \equiv \phi$, and absorbing elements: $\phi \land \bot \equiv \bot$, $\phi \lor \top \equiv \top$.

In CNF, the empty clause (a disjunction of zero literals) represents $\bot$, immediately signaling unsatisfiability. SAT solvers detect the empty clause as a conflict condition. Conversely, the empty CNF (a conjunction of zero clauses) is $\top$, trivially satisfiable.

Formula simplification must respect these edge cases. A simplifier eliminating all clauses risks producing the empty CNF, incorrectly claiming satisfiability when the original formula was contradictory. Robust implementations maintain explicit representations of $\top$ and $\bot$, short-circuiting evaluation when these constants arise.

### Tautology Checking and the Co-NP Duality

While satisfiability is NP-complete, tautology checking—determining whether $\phi$ is valid—is co-NP-complete, the complement problem. No efficient reduction from tautology to satisfiability is known unless NP = co-NP, an open question believed unlikely. In practice, tautology checking proceeds by checking unsatisfiability of $\neg \phi$, leveraging the duality $\models \phi$ if and only if $\neg \phi$ is unsatisfiable. This converts tautology checking into a SAT query, allowing reuse of optimized SAT solvers.

The asymmetry between satisfiability and validity manifests in verification workflows. Proving a program incorrect (finding a bug) requires exhibiting a single counterexample, a satisfiability witness. Proving correctness demands showing no counterexample exists, a validity or unsatisfiability problem. This asymmetry drives the emphasis on unsatisfiability proofs and interpolation techniques in formal verification.
