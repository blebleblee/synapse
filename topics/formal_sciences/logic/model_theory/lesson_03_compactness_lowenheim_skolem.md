# Lesson 3: Compactness Theorem, Löwenheim-Skolem Theorems

## 1. First-Principles Intuition & Invariants

The Compactness Theorem and the Löwenheim-Skolem Theorems stand as the twin pillars of model theory, establishing fundamental constraints on the relationship between syntactic theories and their semantic realizations. These results reveal a profound asymmetry: while first-order logic possesses sufficient expressive power to encode complex mathematical structures, it simultaneously exhibits intrinsic limitations that prevent it from fully capturing infinite cardinalities or uniquely characterizing certain mathematical objects up to isomorphism. This tension between expressiveness and limitation defines the character of first-order model theory and distinguishes it from stronger logical systems.

The Compactness Theorem asserts that a set of first-order sentences $\Gamma$ has a model if and only if every finite subset of $\Gamma$ has a model. This result establishes a bridge between local syntactic consistency and global semantic realizability. The theorem's power lies in its ability to construct infinite models from finite approximations, enabling us to prove the existence of structures that cannot be directly exhibited. The compactness property fails dramatically in second-order logic and infinitary logics, making it a signature characteristic of first-order systems.

The Löwenheim-Skolem Theorems address cardinality constraints on models. The Downward Löwenheim-Skolem Theorem guarantees that any theory with an infinite model possesses a countable model, while the Upward Löwenheim-Skolem Theorem ensures that theories with infinite models admit arbitrarily large models. These results demonstrate that first-order logic cannot control the cardinality of infinite models: if a theory admits one infinite model, it must admit models of every infinite cardinality. This cardinality indeterminacy has profound consequences, including the existence of non-standard models of arithmetic that satisfy all first-order axioms of Peano Arithmetic yet contain "integers" that differ from the standard natural numbers.

Together, these theorems reveal that first-order theories occupy a peculiar position in the landscape of logic. They are weak enough to guarantee completeness and compactness, yet strong enough to express substantial mathematics. The price of this balance is the inability to categorically characterize infinite structures or to pin down exact cardinalities through axiomatization alone.

## 2. Core Architecture & Mechanics

### Compactness via Completeness

The most direct proof of the Compactness Theorem flows through the Completeness Theorem established by Gödel in 1929. Recall that the Completeness Theorem states that a set of sentences $\Gamma$ is satisfiable if and only if it is consistent, meaning no contradiction can be derived from $\Gamma$ using the proof rules of first-order logic. The syntactic notion of consistency thus perfectly aligns with the semantic notion of satisfiability.

To prove compactness, suppose every finite subset of $\Gamma$ has a model. We must establish that $\Gamma$ itself has a model. By the Completeness Theorem, it suffices to prove that $\Gamma$ is consistent. Assume toward contradiction that $\Gamma$ is inconsistent. Then there exists a formal derivation of a contradiction from $\Gamma$. Every formal proof is finite and utilizes only finitely many premises. Thus, there exists a finite subset $\Delta \subseteq \Gamma$ from which a contradiction can be derived. By the soundness of first-order logic, this finite subset $\Delta$ must be unsatisfiable. But this contradicts our hypothesis that every finite subset of $\Gamma$ has a model. Therefore, $\Gamma$ must be consistent, and by completeness, $\Gamma$ has a model.

The converse direction is immediate: if $\Gamma$ has a model, then every subset of $\Gamma$ is satisfied by that same model, hence every finite subset has a model. This completes the proof via completeness.

This proof strategy reveals the deep connection between proof theory and model theory. The compactness phenomenon arises because formal proofs are inherently finite objects, touching only finite fragments of an infinite theory. No finite proof can distinguish between the consistency of an infinite theory and the consistency of all its finite subtheories.

### Compactness via Ultraproducts

An alternative proof of compactness, independent of the Completeness Theorem, proceeds through ultraproducts. This construction provides a direct semantic route to compactness and illuminates the technique of building models from infinite collections of approximating structures.

Let $\Gamma$ be a set of first-order sentences such that every finite subset has a model. For each finite subset $\Delta \subseteq \Gamma$, let $\mathcal{M}_\Delta$ be a model of $\Delta$. We construct an ultraproduct that will serve as a model of the entire theory $\Gamma$.

Index the finite subsets of $\Gamma$ by a set $I$, and for each $i \in I$, let $\mathcal{A}_i$ be a model of the corresponding finite subset. Consider the ultrafilter $\mathcal{U}$ on $I$ extending the filter of cofinite sets. The ultraproduct $\prod_{i \in I} \mathcal{A}_i / \mathcal{U}$ is formed by taking the Cartesian product of the domains and quotienting by the equivalence relation induced by $\mathcal{U}$: two sequences $(a_i)$ and $(b_i)$ are equivalent if the set $\{i \in I : a_i = b_i\}$ belongs to $\mathcal{U}$.

By Łoś's Theorem, a first-order sentence $\varphi$ is true in the ultraproduct if and only if the set of indices $i$ where $\varphi$ is true in $\mathcal{A}_i$ belongs to the ultrafilter $\mathcal{U}$. For any sentence $\varphi \in \Gamma$, the set of finite subsets containing $\varphi$ is cofinite among all finite subsets of $\Gamma$ (specifically, it contains all supersets of the singleton $\{\varphi\}$). Since $\mathcal{U}$ contains all cofinite sets, the sentence $\varphi$ is true in the ultraproduct. Therefore, $\prod_{i \in I} \mathcal{A}_i / \mathcal{U}$ satisfies every sentence in $\Gamma$.

This ultraproduct construction reveals compactness as a consequence of the finite character of first-order satisfaction combined with the extension properties of ultrafilters. The ultrafilter serves as a "generalized limit" that coherently selects truth values from the collection of finite approximations.

### Applications of Compactness

The Compactness Theorem enables the construction of models with specific properties by encoding those properties as infinite sets of sentences and verifying finite satisfiability. A canonical application constructs non-standard models of arithmetic.

Consider the theory $\text{PA}$ of Peano Arithmetic formulated in the language $\mathcal{L} = \{0, S, +, \cdot, <\}$, where $S$ is the successor function. Extend the language by adding a new constant symbol $c$, and form the theory $\Gamma = \text{PA} \cup \{c > \underline{n} : n \in \mathbb{N}\}$, where $\underline{n}$ denotes the numeral $S(S(\cdots S(0)\cdots))$ with $n$ applications of the successor function. Each sentence $c > \underline{n}$ asserts that $c$ exceeds the standard natural number $n$.

Every finite subset of $\Gamma$ is satisfiable: given finitely many sentences from $\Gamma$, only finitely many constraints $c > \underline{n}$ appear. Let $N$ be the maximum such $n$. The standard model $\mathbb{N}$ satisfies PA, and we can interpret $c$ as any natural number greater than $N$, satisfying all the finite constraints. By compactness, the entire theory $\Gamma$ has a model $\mathcal{M}$.

In this model $\mathcal{M}$, the interpretation $c^\mathcal{M}$ of the constant $c$ satisfies $c^\mathcal{M} > n^\mathcal{M}$ for every standard natural number $n$. Thus $c^\mathcal{M}$ is a non-standard element, an "infinite integer" that exceeds all standard numbers. The model $\mathcal{M}$ necessarily contains an entire non-standard segment consisting of elements unreachable from zero by finitely many successor operations. This demonstrates that first-order Peano Arithmetic cannot categorically characterize the natural numbers; it admits unintended models alongside the standard one.

Another classical application constructs infinite objects from finite approximations. To prove the existence of an infinite graph with finite chromatic number, we encode the requirements as an infinite theory. Let $\mathcal{L}$ be a language with a binary relation $E$ (edge relation) and unary predicates $C_1, C_2, \ldots, C_k$ (color classes). Form a theory asserting that $E$ is irreflexive and symmetric, that the color classes partition the vertices, that no edge connects vertices of the same color, and that there exist at least $n$ distinct vertices for each $n \in \mathbb{N}$. Each finite subset of this theory is satisfiable by constructing a sufficiently large finite $k$-colorable graph. By compactness, the entire theory has a model, yielding an infinite $k$-colorable graph.

### Downward Löwenheim-Skolem Theorem

The Downward Löwenheim-Skolem Theorem asserts that if a first-order theory $T$ in a countable language has an infinite model, then $T$ has a countable model. More generally, if $\mathcal{M}$ is an infinite model of $T$ and $A \subseteq M$ is a subset of cardinality $\kappa$, then there exists an elementary substructure $\mathcal{N} \preccurlyeq \mathcal{M}$ containing $A$ with $|N| \leq \max(\kappa, \aleph_0, |\mathcal{L}|)$.

The proof proceeds by constructing a countable elementary substructure through a recursive closure process incorporating Skolem functions. Let $\mathcal{M}$ be an infinite model of $T$ in a countable language $\mathcal{L}$, and let $A \subseteq M$ be a countable subset (possibly empty). We build an increasing chain of countable subsets $A = A_0 \subseteq A_1 \subseteq A_2 \subseteq \cdots$ such that each $A_{n+1}$ contains witnesses for all existential statements satisfied in $\mathcal{M}$ by parameters from $A_n$.

At stage $n$, for every formula $\varphi(x, \bar{y})$ in one free variable $x$ and tuple $\bar{a}$ from $A_n$ such that $\mathcal{M} \models \exists x \, \varphi(x, \bar{a})$, we select a witness $b \in M$ satisfying $\mathcal{M} \models \varphi(b, \bar{a})$ and add it to $A_{n+1}$. The countability of the language ensures that there are only countably many formulas, and the countability of $A_n$ ensures countably many parameter tuples, so $A_{n+1}$ remains countable.

Let $N = \bigcup_{n \in \mathbb{N}} A_n$. The set $N$ is a countable union of countable sets, hence countable. We must verify that the restriction $\mathcal{N} = \mathcal{M} \restriction N$ forms an elementary substructure, meaning $\mathcal{N} \preccurlyeq \mathcal{M}$.

The proof that $\mathcal{N} \preccurlyeq \mathcal{M}$ proceeds by induction on formula complexity. For atomic formulas, satisfaction is determined entirely by the interpretation of relations and functions within $\mathcal{M}$, so $\mathcal{N} \models \varphi(\bar{a})$ if and only if $\mathcal{M} \models \varphi(\bar{a})$ for $\bar{a} \in N$. Boolean connectives preserve the equivalence trivially. The critical case is existential quantification.

Suppose $\mathcal{M} \models \exists x \, \varphi(x, \bar{a})$ for some tuple $\bar{a} \in N$ and formula $\varphi$. Since $N = \bigcup_n A_n$ and $\bar{a}$ is finite, there exists some stage $n$ where $\bar{a} \subseteq A_n$. By construction, $A_{n+1}$ contains a witness $b \in N$ such that $\mathcal{M} \models \varphi(b, \bar{a})$. By the induction hypothesis, $\mathcal{N} \models \varphi(b, \bar{a})$, so $\mathcal{N} \models \exists x \, \varphi(x, \bar{a})$. Conversely, if $\mathcal{N} \models \exists x \, \varphi(x, \bar{a})$, then there exists $b \in N$ with $\mathcal{N} \models \varphi(b, \bar{a})$. By the induction hypothesis, $\mathcal{M} \models \varphi(b, \bar{a})$, so $\mathcal{M} \models \exists x \, \varphi(x, \bar{a})$. This completes the induction, establishing $\mathcal{N} \preccurlyeq \mathcal{M}$.

The Downward Löwenheim-Skolem Theorem has a startling consequence known as Skolem's Paradox. Zermelo-Fraenkel set theory ZFC, formulated in a countable first-order language, proves the existence of uncountable sets such as the power set of the natural numbers. Yet if ZFC is consistent, it has a countable model $\mathcal{M}$ by the Downward Löwenheim-Skolem Theorem. Within this model, there exists an element $\mathcal{P}(\mathbb{N})^\mathcal{M}$ that $\mathcal{M}$ believes to be uncountable. However, from the external perspective, the entire model $\mathcal{M}$ is countable, so the set $\mathcal{P}(\mathbb{N})^\mathcal{M}$ is actually countable.

The resolution of this apparent paradox lies in the relativity of uncountability. The model $\mathcal{M}$ does not contain a bijection between $\mathbb{N}^\mathcal{M}$ and $\mathcal{P}(\mathbb{N})^\mathcal{M}$, so internally, from the perspective of first-order definability within $\mathcal{M}$, the set $\mathcal{P}(\mathbb{N})^\mathcal{M}$ is uncountable. Externally, in the ambient metatheory, a bijection exists between the countable set $\mathbb{N}^\mathcal{M}$ and the countable set $\mathcal{P}(\mathbb{N})^\mathcal{M}$, but this bijection is not an element of $\mathcal{M}$ and cannot be defined within $\mathcal{M}$ using first-order formulas. Uncountability is not an absolute property but rather a statement about the non-existence of bijections within the model.

### Upward Löwenheim-Skolem Theorem

The Upward Löwenheim-Skolem Theorem asserts that if a first-order theory $T$ in a language $\mathcal{L}$ has an infinite model, then for every cardinal $\kappa \geq |\mathcal{L}|$, the theory $T$ has a model of cardinality $\kappa$. This result demonstrates that first-order theories cannot impose upper bounds on the cardinality of their models: if infinity is admitted, then models of all infinite cardinalities must exist.

The proof employs a technique of adding Skolem functions and expanding the language. Let $\mathcal{M}$ be an infinite model of $T$, and let $\kappa \geq |\mathcal{L}|$ be a cardinal. Expand the language $\mathcal{L}$ by adding $\kappa$ new constant symbols $\{c_\alpha : \alpha < \kappa\}$. Form the theory $T' = T \cup \{c_\alpha \neq c_\beta : \alpha < \beta < \kappa\}$, asserting that the new constants are pairwise distinct.

We verify that every finite subset of $T'$ has a model. Any finite subset involves only finitely many of the new constants, say $c_{\alpha_1}, \ldots, c_{\alpha_n}$. Since $\mathcal{M}$ is infinite, we can assign distinct elements of $M$ to these finitely many constants, extending $\mathcal{M}$ to a model of the finite subset. By the Compactness Theorem, the entire theory $T'$ has a model $\mathcal{M}'$.

In the model $\mathcal{M}'$, the interpretations of the constants $\{c_\alpha : \alpha < \kappa\}$ are pairwise distinct, so the domain of $\mathcal{M}'$ has cardinality at least $\kappa$. By restricting the language back to $\mathcal{L}$, we obtain a model of $T$ with cardinality at least $\kappa$. If the cardinality exceeds $\kappa$, we can extract a substructure of cardinality exactly $\kappa$ by selecting an appropriate subset and defining the structure on that subset. Alternatively, we can apply the Downward Löwenheim-Skolem Theorem to obtain an elementary substructure of cardinality exactly $\kappa$, provided $\kappa$ is infinite and at least $|\mathcal{L}|$.

The Upward Löwenheim-Skolem Theorem implies that first-order theories cannot categorically characterize any infinite structure. For example, the second-order axioms for the real numbers categorically determine $\mathbb{R}$ up to isomorphism through the completeness axiom, which involves quantification over sets of reals. However, any first-order theory satisfied by $\mathbb{R}$ must also have models of every infinite cardinality, so no first-order theory can uniquely characterize the real number field.

### Countable Models and Categoricity

A theory $T$ is $\kappa$-categorical if all models of $T$ of cardinality $\kappa$ are isomorphic. The Löwenheim-Skolem Theorems constrain the possible categoricity behavior of first-order theories. Morley's Categoricity Theorem establishes that if a countable complete first-order theory is $\kappa$-categorical for some uncountable cardinal $\kappa$, then it is $\lambda$-categorical for all uncountable cardinals $\lambda$.

However, countable categoricity does not imply uncountable categoricity. The theory of dense linear orders without endpoints (DLO) is $\aleph_0$-categorical: the rational numbers $\mathbb{Q}$ and any countable dense linear order without endpoints are isomorphic by the back-and-forth method. Yet DLO is not categorical in any uncountable cardinality: $\mathbb{R}$ and $\mathbb{R}$ followed by a copy of $\mathbb{Q}$ are both dense linear orders without endpoints of cardinality $2^{\aleph_0}$, but they are not isomorphic, because the first is Dedekind-complete and the second is not.

The existence of countable models for every consistent theory in a countable language places a fundamental limitation on the expressive power of first-order logic. Uncountable mathematical structures such as the real numbers, complex numbers, or arbitrary infinite-dimensional vector spaces cannot be uniquely pinned down by first-order axioms. This limitation motivates the study of second-order logic, infinitary logics, and other extended logical frameworks that can capture richer mathematical content at the cost of losing compactness and completeness.

### Non-Standard Models of Arithmetic

The interplay between compactness and the Löwenheim-Skolem Theorems produces non-standard models that satisfy the same first-order sentences as their intended standard counterparts yet differ radically in structure. Peano Arithmetic provides the most studied example.

The standard model of Peano Arithmetic is the structure $\mathbb{N} = (\mathbb{N}, 0, S, +, \cdot, <)$ consisting of the natural numbers with their usual operations. Every non-standard model $\mathcal{M} \models \text{PA}$ contains an initial segment isomorphic to $\mathbb{N}$, consisting of the interpretations of the standard numerals $0, S(0), S(S(0)), \ldots$. However, $\mathcal{M}$ necessarily contains additional elements beyond this initial segment.

The order structure of a non-standard model has a characteristic form. After the initial standard segment isomorphic to $\mathbb{N}$, the model contains a non-standard segment ordered like $\mathbb{N} + (\mathbb{Z} + \mathbb{Z}) \cdot \mathbb{Q}$, meaning a copy of the natural numbers followed by densely ordered copies of the integers indexed by the rationals. Every non-standard element $a \in M \setminus \mathbb{N}$ is larger than all standard natural numbers, and between any two non-standard elements, there exist infinitely many other elements.

Non-standard models exhibit peculiar arithmetic properties. For instance, in a non-standard model, there exist "infinite primes" — non-standard elements that are prime in the sense that they satisfy the first-order definition of primality but exceed all standard primes. The Fundamental Theorem of Arithmetic, which asserts unique prime factorization, holds in all models of PA, so these infinite primes factor non-standard composite numbers. However, the factorization process may involve non-standard prime factors and non-standard exponents.

The existence of non-standard models demonstrates that induction, when formulated as a first-order axiom schema, is weaker than the full second-order induction principle. The first-order induction schema asserts $\varphi(0) \land \forall n (\varphi(n) \to \varphi(S(n))) \to \forall n \, \varphi(n)$ for every first-order formula $\varphi$. However, this schema does not capture induction over arbitrary sets, only over definable sets. Non-standard models contain sets (from the perspective of the external metatheory) that are inductive but not definable within the model, allowing non-standard elements to "escape" the reach of first-order induction.

## 3. High-Performance Optimization & Failure Modes

### Optimizing Skolem Function Selection in Model Construction

When applying the Downward Löwenheim-Skolem Theorem constructively, the selection of witnesses for existential formulas directly impacts the structural properties of the resulting elementary substructure. In computational applications and model-theoretic algorithms, judicious witness selection can produce substructures with desirable algorithmic properties, such as minimal complexity or efficient representation.

Consider the Henkin construction used in completeness proofs and model enumeration. A set of Skolem functions can be represented as a computable enumeration if the theory is recursively axiomatizable. For a decidable theory, the witness selection process terminates in finite time for each existential query, enabling effective construction of countable models. Conversely, for undecidable theories such as Peano Arithmetic, witness selection may require arbitrarily complex search procedures, and the resulting elementary substructure may have high descriptive complexity.

When constructing elementary substructures in uncountable models, choice functions play an essential role. The full generality of the Downward Löwenheim-Skolem Theorem requires the Axiom of Choice to select witnesses from potentially uncountable families of existential statements. In the absence of choice, the theorem may fail for certain cardinals and certain theories. However, for countable languages and countable subsets, dependent choice suffices, and the construction remains effective in many practical contexts.

### Cardinality Control and Theory Constraints

The Löwenheim-Skolem Theorems reveal that first-order theories cannot precisely control the cardinality of infinite models, but they do impose structural constraints that limit the diversity of models at a given cardinality. For example, an $\aleph_0$-categorical theory admits only one countable model up to isomorphism, while an $\aleph_1$-categorical theory admits only one model of cardinality $\aleph_1$ up to isomorphism (assuming the continuum hypothesis or working in specific set-theoretic contexts).

The failure of first-order logic to enforce cardinality constraints has practical implications for database theory and knowledge representation. Relational databases can be viewed as finite models of first-order theories, and queries correspond to first-order formulas. However, the Compactness Theorem implies that certain global properties, such as finiteness itself, cannot be expressed in first-order logic. A first-order theory cannot assert that a relation is finite without admitting infinite models as well. This limitation motivates the use of fixed-point logics, transitive closure operators, and other extensions in database query languages.

### Edge Cases in Compactness Applications

The Compactness Theorem applies only to first-order logic, and its failure in stronger logics reveals the boundaries of its applicability. Second-order logic does not satisfy compactness: the second-order theory of the natural numbers, consisting of the second-order Peano axioms categorically characterize $\mathbb{N}$ and have exactly one model: the standard natural numbers and rules out non-standard models. Similarly, infinitary logics such as $\mathcal{L}_{\omega_1, \omega}$, which allow countable conjunctions and disjunctions, fail to satisfy compactness.

In applications involving infinite theories, verifying finite satisfiability often requires constructing increasingly large finite models. For example, proving that an infinite graph is $k$-colorable by compactness requires showing that arbitrarily large finite subgraphs are $k$-colorable. If the chromatic number grows with the size of the subgraph, compactness cannot be applied. The finite Ramsey theorem ensures finite satisfiability for certain combinatorial properties, enabling compactness arguments, while the failure of analogous properties in other contexts limits the scope of the technique.

### Failure Modes in Non-Standard Model Construction

When constructing non-standard models of arithmetic using compactness, the resulting models may exhibit pathological features that complicate their analysis. For instance, non-standard models need not be well-founded: there may exist infinite descending chains in the ordering, violating the principle that every non-empty set has a least element. However, the first-order axiom schema of induction does not assert well-foundedness; it only ensures that first-order definable sets are well-founded. Sets that are not first-order definable within the model may fail to have minimal elements.

Another failure mode arises in the context of truth predicates. By Tarski's Undefinability Theorem, no sufficiently strong arithmetical theory can define its own truth predicate. Non-standard models of Peano Arithmetic contain "pseudo-finite" sets that the model believes to be finite but are externally infinite. For example, the set of Gödel numbers of true sentences in the standard model is not definable in the standard model, but a non-standard model may contain a set it believes to encode truth values, yet this set cannot correspond to actual truth in the standard model.

### Computational Complexity of Skolemization

The algorithmic complexity of constructing elementary substructures depends critically on the decidability and complexity of the underlying theory. For a complete decidable theory such as the theory of algebraically closed fields, witness selection for existential formulas can be performed algorithmically using quantifier elimination procedures. The resulting elementary substructure can be represented finitely through generators and relations, with polynomial-time verification of membership and satisfaction for quantifier-free formulas.

For undecidable theories, Skolemization requires non-computable oracles. The construction of a specific non-standard model of Peano Arithmetic, for instance, cannot be made fully explicit in the sense of providing a computable enumeration of the model's domain and operations. However, generic non-standard models can be studied through their first-order properties, and many structural theorems hold uniformly across all non-standard models.

### Relativization and Absoluteness

The interpretation of the Löwenheim-Skolem Theorems depends on the ambient set theory in which model theory is formalized. In the standard set-theoretic metatheory ZFC, the theorems assert the existence of models of specific cardinalities. However, different models of ZFC may disagree on the cardinalities of these models, leading to relativized interpretations.

For example, a countable model of ZFC may contain an element it believes to be an uncountable set. From the perspective of this countable model, the Downward Löwenheim-Skolem Theorem applies internally, producing what the model considers to be a countable substructure. However, from the external perspective of the true metatheory, both the original model and the substructure are countable.

Certain properties are absolute across models of ZFC, meaning they are preserved under forcing extensions and inner models. For instance, the satisfaction of a first-order sentence by a structure is absolute: if a formula $\varphi$ holds in a model $\mathcal{M}$ within one model of ZFC, it holds in $\mathcal{M}$ within any other model of ZFC containing $\mathcal{M}$. However, cardinality is not absolute, and the existence of bijections between sets can change under forcing or inner models.

### Practical Workflow for Model-Theoretic Proofs

When applying the Compactness Theorem or Löwenheim-Skolem Theorems in practice, the typical workflow follows a structured verification strategy. For compactness arguments, first formulate the desired property as an infinite theory $\Gamma$ by encoding each aspect of the property as a sentence or family of sentences. Second, verify that every finite subset of $\Gamma$ is satisfiable by constructing explicit finite models or appealing to known satisfiability results. Third, invoke compactness to conclude that $\Gamma$ itself has a model, and extract the desired property from this model's existence.

For Löwenheim-Skolem applications, identify an initial model $\mathcal{M}$ of the theory $T$ and determine the desired cardinality $\kappa$. For downward applications, construct an elementary substructure by iteratively adding witnesses for existential formulas, ensuring that the closure process terminates at the desired cardinality. For upward applications, expand the language with new constants to force the model to have the desired cardinality, apply compactness to construct a large model, and adjust the cardinality as needed using elementary substructures or superstructures.

Verification of elementary embeddings and elementary substructures requires induction on formula complexity, systematically checking atomic formulas, Boolean combinations, and quantified formulas. Automated theorem provers and model checkers can assist with finite fragments, but the full verification typically requires human insight into the structure of the formulas and the properties of the models involved.
