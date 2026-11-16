# Lesson 1: Propositional Logic, Predicate Calculus, Proof Techniques

## 1. First-Principles Intuition & Invariants

Mathematical proof is the bedrock of all formal reasoning. Before one can architect algorithms, design cryptographic protocols, or verify hardware circuits, one must command the language of rigorous deduction. Discrete mathematics begins not with numbers or equations, but with the formalization of truth itself: propositional logic, the algebra of true and false statements, and predicate calculus, which extends this framework to reason about objects, properties, and relations.

The fundamental insight underlying propositional logic is that complex reasoning can be decomposed into atomic propositions—statements that are unambiguously true or false—and logical connectives that combine these atoms according to precise truth-functional rules. A proposition such as "$P$: The algorithm terminates" is atomic; we cannot further decompose it without leaving the realm of pure logic and entering the domain-specific world of algorithms. But when we write "$P \land Q$" (read: "$P$ and $Q$"), we construct a compound proposition whose truth value is mechanically determined by the truth values of $P$ and $Q$ according to the semantics of conjunction.

This compositional nature mirrors the structure of digital circuits, where logic gates combine binary signals, and the algebraic nature of Boolean algebras, where operations satisfy commutative, associative, and distributive laws. Indeed, propositional logic forms the mathematical foundation for circuit design, compiler optimization, automated theorem proving, and formal verification of software and hardware systems.

The transition from propositional to predicate calculus (first-order logic) introduces quantification: the ability to make statements about all elements of a domain ($\forall$) or assert the existence of elements with certain properties ($\exists$). Where propositional logic allows us to assert "$P \implies Q$", predicate logic enables statements of the form "$\forall x \, (P(x) \implies Q(x))$", which reads "for all $x$, if $x$ satisfies property $P$, then $x$ satisfies property $Q$." This expressive power is essential for formalizing mathematical theorems, specifying program correctness conditions, and reasoning about data structures.

Proof techniques form the operational toolkit for establishing truth in mathematics. Direct proof constructs a chain of logical implications from axioms and previously established theorems to the desired conclusion. Proof by contradiction (reductio ad absurdum) assumes the negation of the target statement and derives a logical impossibility, thereby establishing the original claim. Proof by contrapositive leverages the logical equivalence between "$P \implies Q$" and "$\neg Q \implies \neg P$". Mathematical induction exploits the well-ordering principle of natural numbers to establish universal statements about infinite domains through finite reasoning.

The invariants that govern this domain are few but absolute. First, the Law of Excluded Middle: every proposition is either true or false, with no intermediate state. Second, the Law of Non-Contradiction: no proposition can be simultaneously true and false. Third, truth-functionality: the truth value of a compound proposition depends only on the truth values of its components, not on their semantic content or context. These principles are not empirical observations but definitional commitments that establish the formal system we work within.

## 2. Core Architecture & Mechanics

### Propositional Logic: Syntax and Semantics

A propositional variable (often denoted $p$, $q$, $r$, or $P$, $Q$, $R$ when representing more complex statements) is a symbol that stands for an atomic proposition. The syntax of propositional logic recursively constructs well-formed formulas (wffs) from atoms and connectives. The primary logical connectives and their standard notations are:

- **Negation** ($\neg p$): "not $p$"
- **Conjunction** ($p \land q$): "$p$ and $q$"
- **Disjunction** ($p \lor q$): "$p$ or $q$" (inclusive or)
- **Implication** ($p \implies q$): "if $p$ then $q$" (also written $p \rightarrow q$)
- **Biconditional** ($p \iff q$): "$p$ if and only if $q$" (also written $p \leftrightarrow q$)

The semantics of these connectives are defined through truth tables, which exhaustively enumerate all possible combinations of truth values for the constituent propositions and determine the resulting truth value of the compound formula.

For a single proposition $p$, negation inverts the truth value:

| $p$ | $\neg p$ |
|-----|----------|
| T   | F        |
| F   | T        |

For two propositions $p$ and $q$, conjunction is true only when both components are true:

| $p$ | $q$ | $p \land q$ |
|-----|-----|-------------|
| T   | T   | T           |
| T   | F   | F           |
| F   | T   | F           |
| F   | F   | F           |

Disjunction is true when at least one component is true:

| $p$ | $q$ | $p \lor q$ |
|-----|-----|------------|
| T   | T   | T          |
| T   | F   | T          |
| F   | T   | T          |
| F   | F   | F          |

The implication connective is the most subtle and the source of persistent confusion. The statement "$p \implies q$" asserts that whenever $p$ is true, $q$ must also be true. Critically, when $p$ is false, the implication places no constraint on $q$, and thus the implication is vacuously true. This yields the truth table:

| $p$ | $q$ | $p \implies q$ |
|-----|-----|----------------|
| T   | T   | T              |
| T   | F   | F              |
| F   | T   | T              |
| F   | F   | T              |

The only case in which an implication is false is when a true antecedent leads to a false consequent. This definition aligns with mathematical practice: the statement "if $n$ is even, then $n^2$ is even" is not falsified by examining odd numbers. The biconditional "$p \iff q$" is true precisely when $p$ and $q$ have the same truth value:

| $p$ | $q$ | $p \iff q$ |
|-----|-----|------------|
| T   | T   | T          |
| T   | F   | F          |
| F   | T   | F          |
| F   | F   | T          |

Truth tables scale exponentially with the number of propositional variables: $n$ variables require $2^n$ rows. For complex formulas, systematic construction proceeds by evaluating subformulas in order of increasing complexity. Consider the formula $(p \land q) \implies (p \lor r)$. The truth table requires $2^3 = 8$ rows:

| $p$ | $q$ | $r$ | $p \land q$ | $p \lor r$ | $(p \land q) \implies (p \lor r)$ |
|-----|-----|-----|-------------|------------|-----------------------------------|
| T   | T   | T   | T           | T          | T                                 |
| T   | T   | F   | T           | T          | T                                 |
| T   | F   | T   | F           | T          | T                                 |
| T   | F   | F   | F           | T          | T                                 |
| F   | T   | T   | F           | T          | T                                 |
| F   | T   | F   | F           | F          | T                                 |
| F   | F   | T   | F           | T          | T                                 |
| F   | F   | F   | F           | F          | T                                 |

This formula is a tautology: it is true under all possible truth assignments. Tautologies represent logical laws that hold universally, independent of the truth values of their atomic components.

### Logical Equivalence and Algebraic Laws

Two formulas $\phi$ and $\psi$ are logically equivalent, written $\phi \equiv \psi$, if they have identical truth values under all possible truth assignments. Logical equivalence partitions the space of formulas into equivalence classes and allows us to replace subformulas with equivalent alternatives, just as algebraic identities permit term rewriting in algebra.

The foundational equivalences include the De Morgan's Laws, which describe the duality between conjunction and disjunction under negation:

$$\neg (p \land q) \equiv \neg p \lor \neg q$$

$$\neg (p \lor q) \equiv \neg p \land \neg q$$

These laws are immediately verifiable by truth table construction. For the first law:

| $p$ | $q$ | $p \land q$ | $\neg(p \land q)$ | $\neg p$ | $\neg q$ | $\neg p \lor \neg q$ |
|-----|-----|-------------|-------------------|----------|----------|----------------------|
| T   | T   | T           | F                 | F        | F        | F                    |
| T   | F   | F           | T                 | F        | T        | T                    |
| F   | T   | F           | T                 | T        | F        | T                    |
| F   | F   | F           | T                 | T        | T        | T                    |

The columns for $\neg(p \land q)$ and $\neg p \lor \neg q$ are identical, confirming the equivalence. De Morgan's Laws generalize to arbitrary finite conjunctions and disjunctions and are essential for normalizing Boolean expressions in circuit design and simplifying logical formulas in automated reasoning systems.

The implication connective can be eliminated in favor of negation and disjunction:

$$p \implies q \equiv \neg p \lor q$$

This equivalence is crucial for understanding the semantics of implication. The statement "if $p$ then $q$" is logically equivalent to "either $p$ is false or $q$ is true." Verifying this by truth table:

| $p$ | $q$ | $p \implies q$ | $\neg p$ | $\neg p \lor q$ |
|-----|-----|----------------|----------|-----------------|
| T   | T   | T              | F        | T               |
| T   | F   | F              | F        | F               |
| F   | T   | T              | T        | T               |
| F   | F   | T              | T        | T               |

The biconditional decomposes as a conjunction of two implications:

$$p \iff q \equiv (p \implies q) \land (q \implies p)$$

Combining this with the elimination of implication yields:

$$p \iff q \equiv (\neg p \lor q) \land (\neg q \lor p)$$

Further manipulation using distributive laws can transform this into a disjunction of conjunctions, illustrating the power of algebraic rewriting.

The distributive laws govern the interaction between conjunction and disjunction:

$$p \land (q \lor r) \equiv (p \land q) \lor (p \land r)$$

$$p \lor (q \land r) \equiv (p \lor q) \land (p \lor r)$$

Note the symmetric duality: conjunction distributes over disjunction and vice versa, unlike arithmetic where multiplication distributes over addition but addition does not distribute over multiplication. This algebraic symmetry reflects the deeper structure of Boolean algebras.

Associativity and commutativity hold for both conjunction and disjunction:

$$p \land (q \land r) \equiv (p \land q) \land r$$

$$p \land q \equiv q \land p$$

$$p \lor (q \lor r) \equiv (p \lor q) \lor r$$

$$p \lor q \equiv q \lor p$$

The double negation law states that negating a proposition twice returns the original:

$$\neg(\neg p) \equiv p$$

Idempotence asserts that repeating an operation does not change the result:

$$p \land p \equiv p$$

$$p \lor p \equiv p$$

Absorption laws relate conjunction and disjunction:

$$p \land (p \lor q) \equiv p$$

$$p \lor (p \land q) \equiv p$$

Identity laws specify neutral elements:

$$p \land \mathsf{T} \equiv p \quad \text{(where $\mathsf{T}$ is a tautology)}$$

$$p \lor \mathsf{F} \equiv p \quad \text{(where $\mathsf{F}$ is a contradiction)}$$

Domination laws specify absorbing elements:

$$p \land \mathsf{F} \equiv \mathsf{F}$$

$$p \lor \mathsf{T} \equiv \mathsf{T}$$

Finally, the law of excluded middle and the law of non-contradiction:

$$p \lor \neg p \equiv \mathsf{T}$$

$$p \land \neg p \equiv \mathsf{F}$$

These laws form a complete axiom system for propositional logic when interpreted as equations in a Boolean algebra. Any logical equivalence can be derived by successive application of these rewriting rules.

### Contrapositive, Converse, and Inverse

Given an implication $p \implies q$, three related statements are frequently encountered. The **contrapositive** is $\neg q \implies \neg p$, the **converse** is $q \implies p$, and the **inverse** is $\neg p \implies \neg q$. These relationships have distinct logical statuses.

The contrapositive is logically equivalent to the original implication:

$$p \implies q \equiv \neg q \implies \neg p$$

To verify this, we construct truth tables. For $p \implies q$:

| $p$ | $q$ | $p \implies q$ |
|-----|-----|----------------|
| T   | T   | T              |
| T   | F   | F              |
| F   | T   | T              |
| F   | F   | T              |

For the contrapositive $\neg q \implies \neg p$:

| $p$ | $q$ | $\neg q$ | $\neg p$ | $\neg q \implies \neg p$ |
|-----|-----|----------|----------|--------------------------|
| T   | T   | F        | F        | T                        |
| T   | F   | T        | F        | F                        |
| F   | T   | F        | T        | T                        |
| F   | F   | T        | T        | T                        |

The columns for $p \implies q$ and $\neg q \implies \neg p$ match perfectly. This equivalence is fundamental in proof technique: to prove "$p$ implies $q$", one may equivalently prove "if not $q$, then not $p$", which is sometimes more convenient.

The converse $q \implies p$ is **not** equivalent to the original implication. Consider the statement "if it is raining, then the ground is wet." The converse, "if the ground is wet, then it is raining," is clearly not logically necessary (the ground might be wet from a sprinkler). Truth table comparison confirms non-equivalence:

| $p$ | $q$ | $p \implies q$ | $q \implies p$ |
|-----|-----|----------------|----------------|
| T   | T   | T              | T              |
| T   | F   | F              | T              |
| F   | T   | T              | F              |
| F   | F   | T              | T              |

The columns differ in rows 2 and 3. The confusion between an implication and its converse is a pervasive error in informal reasoning.

The inverse $\neg p \implies \neg q$ is the contrapositive of the converse, and thus equivalent to the converse but not to the original implication. A common logical fallacy is to assume that if $p \implies q$ is true, then $\neg p \implies \neg q$ must also hold (the fallacy of denying the antecedent).

### Predicate Calculus: Quantifiers and Domains

Propositional logic is too coarse-grained to express many mathematical statements. The assertion "every even integer greater than 2 can be expressed as the sum of two primes" (the Goldbach Conjecture) involves quantification over an infinite domain and predicates that depend on variables. Predicate calculus (first-order logic) extends propositional logic by introducing:

- **Predicates**: functions from objects to truth values, such as $\text{Even}(x)$ or $\text{Prime}(y)$
- **Quantifiers**: universal quantification ($\forall$) and existential quantification ($\exists$)
- **Variables**: symbols ranging over a domain of discourse

A predicate such as $P(x)$ becomes a proposition only when the variable $x$ is bound by a quantifier or assigned a specific value. The universal quantifier $\forall x \, P(x)$ asserts that $P(x)$ is true for every element $x$ in the domain. The existential quantifier $\exists x \, P(x)$ asserts that there exists at least one element $x$ in the domain for which $P(x)$ is true.

The semantics of quantifiers are defined through the domain of discourse. If the domain is $D = \{a, b, c\}$, then:

$$\forall x \, P(x) \equiv P(a) \land P(b) \land P(c)$$

$$\exists x \, P(x) \equiv P(a) \lor P(b) \lor P(c)$$

For finite domains, quantifiers reduce to finite conjunctions and disjunctions. For infinite domains such as the natural numbers, quantifiers cannot be eliminated in this manner, but the intuition remains: $\forall$ is a generalized conjunction, $\exists$ is a generalized disjunction.

Negation interacts with quantifiers via generalized De Morgan's Laws:

$$\neg (\forall x \, P(x)) \equiv \exists x \, \neg P(x)$$

$$\neg (\exists x \, P(x)) \equiv \forall x \, \neg P(x)$$

These equivalences are essential for logical manipulation. To prove that "not all $x$ satisfy $P$" is equivalent to proving that "there exists an $x$ that does not satisfy $P$." To prove that "there does not exist an $x$ satisfying $P$" is equivalent to proving that "all $x$ satisfy $\neg P$."

The order of quantifiers is critical. The statement $\forall x \, \exists y \, P(x, y)$ asserts that for every $x$, there exists some $y$ (possibly depending on $x$) such that $P(x, y)$ holds. The statement $\exists y \, \forall x \, P(x, y)$ asserts that there exists a single $y$ such that $P(x, y)$ holds for all $x$. These are not equivalent. Consider the predicate $P(x, y)$ meaning "$y > x$" over the natural numbers. The statement $\forall x \, \exists y \, (y > x)$ is true: for any number $x$, we can find a larger number $y$. But $\exists y \, \forall x \, (y > x)$ is false: there is no single number $y$ that is larger than all numbers.

The scope of a quantifier extends over the formula immediately following it. Parentheses disambiguate scope: $\forall x \, (P(x) \implies Q(x))$ is distinct from $(\forall x \, P(x)) \implies Q(x)$. In the first, the quantifier binds $x$ in both $P(x)$ and $Q(x)$. In the second, the quantifier binds $x$ only in $P(x)$, and the implication itself is a proposition with $Q(x)$ containing a free variable.

### Proof Techniques: Direct Proof

A direct proof of the statement $p \implies q$ assumes $p$ is true and derives $q$ through a sequence of logical implications, each justified by axioms, definitions, or previously established theorems. The structure is linear and constructive.

Consider the theorem: *If $n$ is an even integer, then $n^2$ is an even integer.*

**Proof.** Assume $n$ is even. By definition of evenness, there exists an integer $k$ such that $n = 2k$. We compute:

$$n^2 = (2k)^2 = 4k^2 = 2(2k^2)$$

Since $2k^2$ is an integer (closure of integers under multiplication), we have expressed $n^2$ as $2$ times an integer, which is the definition of an even number. Therefore, $n^2$ is even. ∎

The proof proceeds by unpacking the hypothesis via the definition of evenness, performing algebraic manipulation, and repacking the result via the same definition. Each step is mechanically verifiable.

Direct proofs can involve multiple implications chained together. Consider: *If $n$ is an odd integer, then $n^2$ is odd.*

**Proof.** Assume $n$ is odd. By definition, there exists an integer $k$ such that $n = 2k + 1$. We expand:

$$n^2 = (2k + 1)^2 = 4k^2 + 4k + 1 = 2(2k^2 + 2k) + 1$$

Let $m = 2k^2 + 2k$. Since $m$ is an integer, we have $n^2 = 2m + 1$, which is the definition of an odd integer. Therefore, $n^2$ is odd. ∎

Direct proofs of universal statements often require introducing arbitrary elements. To prove $\forall x \, P(x)$, we introduce an arbitrary $x$ (with no special properties beyond being in the domain) and prove $P(x)$. Since $x$ was arbitrary, the conclusion holds for all $x$.

### Proof by Contrapositive

Exploiting the equivalence $p \implies q \equiv \neg q \implies \neg p$, a proof by contrapositive assumes $\neg q$ and derives $\neg p$. This technique is advantageous when the negations are easier to work with than the original statements.

Consider: *If $n^2$ is even, then $n$ is even.*

A direct proof would assume $n^2$ is even and attempt to deduce $n$ is even, but the path forward is unclear. The contrapositive reformulation is: *If $n$ is odd, then $n^2$ is odd.* This we have already proven above.

**Proof (by contrapositive).** We prove the contrapositive: if $n$ is odd, then $n^2$ is odd. Assume $n$ is odd. Then $n = 2k + 1$ for some integer $k$. Squaring:

$$n^2 = (2k + 1)^2 = 4k^2 + 4k + 1 = 2(2k^2 + 2k) + 1$$

Thus, $n^2$ is odd. Since we have proven $\neg(\text{$n$ is even}) \implies \neg(\text{$n^2$ is even})$, the contrapositive equivalence establishes that if $n^2$ is even, then $n$ is even. ∎

This result is instrumental in proving the irrationality of $\sqrt{2}$, as we shall see.

### Proof by Contradiction

Proof by contradiction (reductio ad absurdum) assumes the negation of the desired conclusion and derives a logical contradiction. Since our logical system is consistent, the assumption must be false, and therefore the original statement is true.

The classic example is the irrationality of $\sqrt{2}$.

**Theorem.** $\sqrt{2}$ is irrational.

**Proof (by contradiction).** Assume, for the sake of contradiction, that $\sqrt{2}$ is rational. Then there exist integers $p$ and $q$ with $q \neq 0$ such that:

$$\sqrt{2} = \frac{p}{q}$$

We may assume without loss of generality that $\frac{p}{q}$ is in lowest terms, meaning $\gcd(p, q) = 1$ (if not, cancel common factors). Squaring both sides:

$$2 = \frac{p^2}{q^2}$$

Multiplying by $q^2$:

$$p^2 = 2q^2$$

This equation tells us that $p^2$ is even. By our earlier theorem (the contrapositive proof), if $p^2$ is even, then $p$ is even. Therefore, there exists an integer $k$ such that $p = 2k$. Substituting:

$$(2k)^2 = 2q^2$$

$$4k^2 = 2q^2$$

$$2k^2 = q^2$$

This tells us that $q^2$ is even, and by the same theorem, $q$ is even. But now both $p$ and $q$ are even, which means they share the common factor $2$. This contradicts our assumption that $\gcd(p, q) = 1$.

Since our assumption that $\sqrt{2}$ is rational leads to a contradiction, the assumption must be false. Therefore, $\sqrt{2}$ is irrational. ∎

The power of proof by contradiction lies in its ability to leverage the full strength of logical deduction: any contradiction suffices, not necessarily one directly involving the hypothesis.

### Proof by Cases (Case Analysis)

When a statement must hold under multiple scenarios, proof by cases exhaustively treats each scenario. If the domain decomposes into disjoint cases and the conclusion holds in each case, it holds universally.

**Theorem.** For any integer $n$, the quantity $n^2 + n$ is even.

**Proof (by cases).** Every integer is either even or odd, so we consider these two cases.

*Case 1: $n$ is even.* Then $n = 2k$ for some integer $k$. We compute:

$$n^2 + n = (2k)^2 + 2k = 4k^2 + 2k = 2(2k^2 + k)$$

Since $2k^2 + k$ is an integer, $n^2 + n$ is even.

*Case 2: $n$ is odd.* Then $n = 2k + 1$ for some integer $k$. We compute:

$$n^2 + n = (2k + 1)^2 + (2k + 1) = 4k^2 + 4k + 1 + 2k + 1 = 4k^2 + 6k + 2 = 2(2k^2 + 3k + 1)$$

Since $2k^2 + 3k + 1$ is an integer, $n^2 + n$ is even.

In both cases, $n^2 + n$ is even. Since every integer falls into one of these cases, the theorem holds for all integers. ∎

Case analysis is particularly useful when the hypothesis or the domain naturally partitions into subcases, as with parity (even/odd), sign (positive/zero/negative), or algebraic structure.

### Mathematical Induction

Mathematical induction is a proof technique for establishing universal statements about the natural numbers (or any well-ordered set). The principle rests on the well-ordering principle: every non-empty subset of the natural numbers has a least element.

The structure of an induction proof has two components:

1. **Base case**: Prove the statement holds for the smallest element of the domain (typically $n = 0$ or $n = 1$).
2. **Inductive step**: Prove that if the statement holds for an arbitrary natural number $k$ (the inductive hypothesis), then it holds for $k + 1$.

The inductive step establishes a chain of implications: if the base case holds and each step implies the next, then the statement holds for all natural numbers by a domino effect.

**Theorem.** For all natural numbers $n \geq 1$, the sum of the first $n$ natural numbers is:

$$\sum_{i=1}^n i = \frac{n(n+1)}{2}$$

**Proof (by induction).** Let $P(n)$ be the statement that $\sum_{i=1}^n i = \frac{n(n+1)}{2}$.

*Base case ($n = 1$)*: We compute $\sum_{i=1}^1 i = 1$. The formula gives $\frac{1(1+1)}{2} = \frac{2}{2} = 1$. Thus, $P(1)$ holds.

*Inductive step*: Assume $P(k)$ holds for some arbitrary natural number $k \geq 1$. That is, assume:

$$\sum_{i=1}^k i = \frac{k(k+1)}{2}$$

We must prove that $P(k+1)$ holds, i.e., that:

$$\sum_{i=1}^{k+1} i = \frac{(k+1)(k+2)}{2}$$

Starting from the left-hand side:

$$\sum_{i=1}^{k+1} i = \left(\sum_{i=1}^k i\right) + (k+1)$$

By the inductive hypothesis, $\sum_{i=1}^k i = \frac{k(k+1)}{2}$. Substituting:

$$\sum_{i=1}^{k+1} i = \frac{k(k+1)}{2} + (k+1)$$

Factoring out $(k+1)$:

$$= (k+1)\left(\frac{k}{2} + 1\right) = (k+1)\left(\frac{k + 2}{2}\right) = \frac{(k+1)(k+2)}{2}$$

This is precisely $P(k+1)$. By the principle of mathematical induction, $P(n)$ holds for all $n \geq 1$. ∎

The inductive step is where the proof machinery does its work. We explicitly invoke the inductive hypothesis (the assumption that $P(k)$ holds) and use it to establish $P(k+1)$. The chain of reasoning is $P(1) \implies P(2) \implies P(3) \implies \cdots$, and since $P(1)$ is true, all subsequent statements are true.

Induction is not limited to summation formulas. Consider a proof involving divisibility.

**Theorem.** For all natural numbers $n \geq 1$, the quantity $n^3 - n$ is divisible by $3$.

**Proof (by induction).** Let $P(n)$ be the statement that $3$ divides $n^3 - n$.

*Base case ($n = 1$)*: We compute $1^3 - 1 = 0$, which is divisible by $3$. Thus, $P(1)$ holds.

*Inductive step*: Assume $P(k)$ holds, i.e., $3$ divides $k^3 - k$. We must show that $3$ divides $(k+1)^3 - (k+1)$.

Expanding $(k+1)^3$:

$$(k+1)^3 - (k+1) = k^3 + 3k^2 + 3k + 1 - k - 1 = k^3 + 3k^2 + 2k$$

We rewrite this as:

$$(k^3 - k) + 3k^2 + 3k = (k^3 - k) + 3(k^2 + k)$$

By the inductive hypothesis, $k^3 - k$ is divisible by $3$. The term $3(k^2 + k)$ is explicitly divisible by $3$. Therefore, their sum is divisible by $3$, establishing $P(k+1)$. By induction, $P(n)$ holds for all $n \geq 1$. ∎

The algebraic manipulation in the inductive step is critical: we decompose $(k+1)^3 - (k+1)$ into a part that matches the inductive hypothesis and a part that is explicitly divisible by $3$.

### Strong Induction

Strong induction (also called complete induction) is a variant in which the inductive hypothesis assumes the statement holds for all natural numbers up to $k$, not just for $k$ itself. This provides more leverage in the inductive step.

The structure is:

1. **Base case**: Prove the statement for the smallest element(s).
2. **Inductive step**: Assume the statement holds for all $m$ with $m \leq k$. Prove it holds for $k + 1$.

Strong induction is particularly useful when the proof for $n$ depends on multiple preceding cases, as in recursive algorithms or recurrence relations.

**Theorem.** Every natural number $n \geq 2$ can be expressed as a product of prime numbers.

**Proof (by strong induction).** Let $P(n)$ be the statement that $n$ can be written as a product of primes.

*Base case ($n = 2$)*: The number $2$ is prime, and thus trivially a product of primes (a product of one factor). So $P(2)$ holds.

*Inductive step*: Assume that for all natural numbers $m$ with $2 \leq m \leq k$, the statement $P(m)$ holds (i.e., $m$ can be factored into primes). We must prove $P(k+1)$.

Consider $k + 1$. If $k + 1$ is prime, then it is trivially a product of primes. If $k + 1$ is composite, then by definition, there exist integers $a$ and $b$ with $1 < a, b < k + 1$ such that $k + 1 = a \cdot b$. Note that $2 \leq a, b \leq k$.

By the strong inductive hypothesis, both $a$ and $b$ can be expressed as products of primes. Therefore, $k + 1 = a \cdot b$ is also a product of primes (the concatenation of the prime factorizations of $a$ and $b$). Thus, $P(k+1)$ holds.

By strong induction, every natural number $n \geq 2$ can be expressed as a product of primes. ∎

The strong inductive hypothesis allows us to invoke $P(a)$ and $P(b)$ for $a, b < k + 1$, which is essential since $k + 1$ factors into strictly smaller numbers, not just $k$.

Strong induction is logically equivalent to ordinary induction: any statement provable by one can be proven by the other. However, strong induction often simplifies the proof when the natural recursive structure of the problem involves arbitrary smaller cases rather than just the immediate predecessor.

## 3. High-Performance Optimization & Failure Modes

### Optimization: Efficient Truth Table Construction and Normal Forms

For propositions involving many variables, exhaustive truth table construction becomes computationally prohibitive. A formula with $n$ variables requires $2^n$ rows. For $n = 10$, this is already $1024$ rows; for $n = 20$, over a million. Practical applications in circuit design, SAT solvers, and automated theorem proving demand more efficient representations.

One approach is to convert formulas into normal forms: standardized syntactic structures that facilitate algorithmic manipulation. The two canonical normal forms are Conjunctive Normal Form (CNF) and Disjunctive Normal Form (DNF).

A formula is in **Disjunctive Normal Form** if it is a disjunction of conjunctions of literals (where a literal is a variable or its negation):

$$\bigvee_{i=1}^m \left(\bigwedge_{j=1}^{n_i} \ell_{ij}\right)$$

For example, $(p \land \neg q) \lor (\neg p \land q \land r)$ is in DNF. DNF corresponds directly to truth tables: each conjunction represents a row where the formula is true, and the disjunction unions these rows. Constructing DNF from a truth table is mechanical: for each row where the formula evaluates to true, form a conjunction of literals matching the truth assignment, then disjoin all such conjunctions.

A formula is in **Conjunctive Normal Form** if it is a conjunction of disjunctions of literals:

$$\bigwedge_{i=1}^m \left(\bigvee_{j=1}^{n_i} \ell_{ij}\right)$$

For example, $(p \lor \neg q) \land (\neg p \lor q)$ is in CNF. CNF is the dual of DNF and is preferred in SAT solving because the conjunction structure allows unit propagation and clause learning algorithms to operate efficiently.

Conversion to CNF proceeds by eliminating implications and biconditionals, pushing negations inward using De Morgan's Laws (De Morgan's Laws), and applying distributivity. Consider the formula $(p \implies q) \land r$. First, eliminate the implication:

$$(\neg p \lor q) \land r$$

This is already in CNF. For a more complex example, consider $(p \land q) \implies (r \lor s)$. Eliminate the implication:

$$\neg(p \land q) \lor (r \lor s)$$

Apply De Morgan's Law:

$$(\neg p \lor \neg q) \lor (r \lor s)$$

Flatten the disjunction:

$$\neg p \lor \neg q \lor r \lor s$$

This is a single clause in CNF. Conversion can exponentially increase formula size in the worst case, but many practical formulas remain tractable.

### Failure Mode: Misapplication of Quantifier Negation

A common error in predicate logic is incorrect negation of quantified statements. Students often mistakenly believe that $\neg(\forall x \, P(x))$ is equivalent to $\forall x \, \neg P(x)$, which is false. The correct negation is $\exists x \, \neg P(x)$: to say "not all $x$ satisfy $P$" is to say "there exists an $x$ that does not satisfy $P$."

Similarly, $\neg(\exists x \, P(x)) \equiv \forall x \, \neg P(x)$: to say "there does not exist an $x$ satisfying $P$" is to say "every $x$ does not satisfy $P$."

These negations mirror De Morgan's Laws and are essential for correctly formulating the negation of complex statements. In formal verification and specification, incorrect quantifier negation leads to specifications that fail to capture the intended behavior, allowing bugs to pass undetected.

### Failure Mode: Circular Reasoning in Induction

A subtle but fatal error in inductive proofs is assuming what must be proven. In the inductive step, the inductive hypothesis $P(k)$ is assumed, and $P(k+1)$ must be derived. If the proof of $P(k+1)$ directly assumes $P(k+1)$ or uses $P(k)$ in a way that is logically equivalent to assuming $P(k+1)$, the proof is circular and invalid.

For example, suppose we want to prove that $\sum_{i=1}^n i = \frac{n(n+1)}{2}$ but in the inductive step, instead of computing $\sum_{i=1}^{k+1} i = \sum_{i=1}^k i + (k+1)$ and substituting the inductive hypothesis, we simply write:

$$\sum_{i=1}^{k+1} i = \frac{(k+1)(k+2)}{2}$$

and claim "this is true by the inductive hypothesis." This is circular: we have assumed $P(k+1)$ to prove $P(k+1)$. The inductive hypothesis applies only to $P(k)$, not to $P(k+1)$.

Vigilance against circular reasoning is maintained by clearly delineating what is assumed (the inductive hypothesis for $P(k)$) and what must be derived ($P(k+1)$), and ensuring that the derivation does not covertly reintroduce the conclusion.

### Optimization: Proof by Smallest Counterexample

In well-ordered domains such as the natural numbers, a powerful technique combines contradiction with the well-ordering principle. To prove $\forall n \, P(n)$, assume for contradiction that there exists an $n$ for which $P(n)$ is false. By well-ordering, there exists a smallest such $n$. One then derives a contradiction, often by showing that a smaller counterexample must exist, contradicting minimality.

This technique is particularly effective when ordinary induction is cumbersome. Consider proving that every natural number $n \geq 2$ has a prime divisor.

**Proof (by smallest counterexample).** Assume, for contradiction, that there exists a natural number $n \geq 2$ that has no prime divisor. Let $m$ be the smallest such number. Since $m$ has no prime divisor, $m$ is not prime (else $m$ divides itself). Therefore, $m$ is composite, so there exist integers $a, b$ with $1 < a, b < m$ such that $m = a \cdot b$.

Since $a < m$ and $m$ is the smallest counterexample, $a$ must have a prime divisor $p$. But then $p$ divides $a$, and since $a$ divides $m$, we have $p$ divides $m$. This contradicts the assumption that $m$ has no prime divisor.

Therefore, no such counterexample exists, and every $n \geq 2$ has a prime divisor. ∎

This proof leverages the minimal element to construct a contradiction without explicitly formulating base cases and inductive steps.

### Failure Mode: Confusing Sufficient and Necessary Conditions

The statement $p \implies q$ asserts that $p$ is a **sufficient condition** for $q$: whenever $p$ holds, $q$ must hold. Conversely, $q$ is a **necessary condition** for $p$: $p$ cannot hold unless $q$ holds. Students and practitioners frequently conflate these.

To say "$p$ is sufficient for $q$" means $p \implies q$. To say "$p$ is necessary for $q$" means $q \implies p$ (equivalently, $\neg p \implies \neg q$). The biconditional $p \iff q$ asserts that $p$ is both necessary and sufficient for $q$.

In system specifications, confusing sufficiency and necessity can result in over-constrained or under-constrained designs. A security property might require that "authentication is necessary for access" ($\text{Access} \implies \text{Authentication}$), meaning access cannot occur without authentication. Misinterpreting this as "authentication is sufficient for access" ($\text{Authentication} \implies \text{Access}$) would allow authenticated users unrestricted access, violating authorization policies.

### Optimization: Heuristic Proof Strategy Selection

Experienced mathematicians and automated theorem provers employ heuristics to select proof strategies. For implications $p \implies q$:

- If $q$ is easier to establish from $p$ than $\neg p$ is from $\neg q$, use direct proof.
- If $\neg p$ is simpler to derive from $\neg q$, use contrapositive.
- If $q$ is existential or involves weak conditions, consider direct proof.
- If $\neg q$ is easily manipulated or leads to algebraic simplification, try contrapositive.
- If the statement is strong or counterintuitive, contradiction may be fruitful.

For universal statements over infinite domains, induction is the natural tool when the domain is the natural numbers or recursively structured. For statements over arbitrary domains, proof by cases or direct proof with arbitrary element introduction is appropriate.

These heuristics are not infallible but provide a roadmap for navigating the space of possible proofs, reducing trial-and-error and focusing effort on promising approaches.

### Failure Mode: Off-by-One Errors in Induction

A pernicious bug in inductive proofs is misalignment between the base case and the inductive step. The base case must cover the smallest element of the domain, and the inductive step must correctly increment from $k$ to $k + 1$. Forgetting to verify the base case or proving the inductive step from $P(k)$ to $P(k+2)$ invalidates the proof.

Consider the false "theorem": all horses are the same color. The "proof" proceeds by induction on the number of horses $n$.

*Base case ($n = 1$)*: A single horse trivially has the same color as itself. $P(1)$ holds.

*Inductive step*: Assume all sets of $k$ horses have the same color. Consider a set of $k + 1$ horses. Remove one horse, leaving a set of $k$ horses that, by the inductive hypothesis, all have the same color. Now remove a different horse and add back the first, again yielding $k$ horses that all have the same color. Since the two sets overlap, all $k + 1$ horses must have the same color.

This "proof" fails for $n = 2$: the two sets of $k = 1$ horse do not overlap, so the inductive step does not establish $P(2)$ from $P(1)$. The base case $P(1)$ is true, but the chain breaks at $n = 2$, and the induction collapses.

Rigorous inductive proofs verify that the inductive step genuinely establishes $P(k) \implies P(k+1)$ for all $k$ in the domain, without hidden gaps.

---

Propositional logic and predicate calculus form the syntactic and semantic foundation for all rigorous reasoning in mathematics and computer science. Truth tables provide a mechanical decision procedure for finite propositional logic, while logical equivalences enable algebraic rewriting. Quantifiers extend expressive power to infinite domains and relational structures. Proof techniques—direct proof, contrapositive, contradiction, cases, induction, and strong induction—constitute the operational toolkit for establishing mathematical truth. Mastery of these techniques is not merely theoretical; it directly impacts the ability to design correct algorithms, verify software and hardware, optimize combinatorial structures, and reason about computational complexity. The discipline of formal proof transforms intuition into certainty and conjecture into theorem, providing the rigorous scaffolding upon which all discrete mathematics is constructed.
