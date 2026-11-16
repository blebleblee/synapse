# Lesson 1: Topological Spaces, Open Sets, Axioms

## 1. First-Principles Intuition & Invariants

Topology begins with an act of radical abstraction. In metric spaces — the familiar arena of undergraduate analysis — the notion of "closeness" is encoded by a distance function, and the entire architecture of limits, continuity, and convergence is built on that numerical foundation. Topology asks a sharper question: how much of that architecture survives if you strip away the metric entirely? The answer is essentially everything that matters, and the structure that remains after the distance function is discarded is a *topology*.

The historical pressure toward this abstraction was genuine and not merely aesthetic. By the late nineteenth century, mathematicians working in analysis, complex function theory, and algebraic geometry were repeatedly encountering the same structural phenomena — continuity, connectedness, compactness — in settings where no natural metric existed. Henri Poincaré's work on the qualitative behavior of differential equations, Georg Cantor's investigations into point sets on the real line, and Felix Hausdorff's systematic study of ordered sets all converged on the need for a framework that treated "nearness" as a primitive rather than a derived concept. The open set axioms, crystallized largely through Hausdorff's 1914 *Grundzüge der Mengenlehre* and later refined by Kuratowski and others, became that framework.

The key conceptual inversion is this: in a metric space, you *prove* that the collection of open sets satisfies certain closure properties (closed under arbitrary unions, closed under finite intersections). In a topological space, you *declare* a collection of sets to have those properties, and that declaration is the entire definition of the structure. This shifts open sets from theorems about distance to axioms about structure, and opens the subject to a vastly larger class of spaces.

**Definition 1.1 (Topological Space).** Let $X$ be a set. A *topology* on $X$ is a collection $\mathcal{T} \subseteq \mathcal{P}(X)$ satisfying three axioms:

$$\text{(T1)}\quad \emptyset \in \mathcal{T} \text{ and } X \in \mathcal{T}$$

$$\text{(T2)}\quad \text{If } \{U_\alpha\}_{\alpha \in A} \subseteq \mathcal{T} \text{ for any index set } A, \text{ then } \bigcup_{\alpha \in A} U_\alpha \in \mathcal{T}$$

$$\text{(T3)}\quad \text{If } U_1, U_2, \ldots, U_n \in \mathcal{T} \text{ for some finite } n, \text{ then } \bigcap_{i=1}^n U_i \in \mathcal{T}$$

The pair $(X, \mathcal{T})$ is called a *topological space*, and the members of $\mathcal{T}$ are called *open sets*. A set $C \subseteq X$ is *closed* if its complement $X \setminus C$ is open.

The asymmetry between T2 and T3 — arbitrary unions but only *finite* intersections — is not arbitrary. It reflects the essential behavior of open intervals on the real line. The intersection $\bigcap_{n=1}^\infty \left(-\frac{1}{n}, \frac{1}{n}\right) = \{0\}$ is a single point, which is not open in the standard metric topology on $\mathbb{R}$. If we permitted arbitrary intersections, we would force every singleton to be open, collapsing all topologies to a single rigid structure. The finiteness restriction in T3 is precisely what gives the axiom system enough flexibility to admit the rich diversity of topological spaces studied in modern mathematics.

The emptyset and the whole space are required by T1 for logical coherence: a topology closed under arbitrary unions must contain the empty union $\bigcup_{\alpha \in \emptyset} U_\alpha = \emptyset$, and a topology on $X$ that failed to contain $X$ itself would be unable to represent the "entire space" as an open set, which causes difficulties with complements and closed sets. T1 is thus less an independent insight than a bookkeeping requirement that closes off degenerate edge cases.

### The Extreme Cases: Discrete and Indiscrete Topologies

For any set $X$, there are two canonical topologies that bound all others in a precise sense. The *discrete topology* is $\mathcal{T}_{\text{disc}} = \mathcal{P}(X)$, the full power set. Every subset of $X$ is declared open. This topology is the finest possible: it discriminates between points as sharply as conceivable. In a discrete topological space, every singleton $\{x\}$ is open, every function out of $X$ is automatically continuous, and every subset is simultaneously open and closed. The discrete topology on a finite set $X$ corresponds exactly to the metric topology induced by the discrete metric $d(x,y) = 1$ whenever $x \neq y$.

At the opposite extreme, the *indiscrete topology* (or *trivial topology*) is $\mathcal{T}_{\text{indisc}} = \{\emptyset, X\}$, the coarsest possible topology. It contains nothing beyond what the axioms absolutely demand. In this topology, the only open sets are $\emptyset$ and $X$ themselves, and the only continuous functions *into* $(X, \mathcal{T}_{\text{indisc}})$ are all functions — since preimages of the only open sets are $\emptyset$ and $X$, which are open in any topology on the domain. The indiscrete topology is pathologically coarse: no two points can be "separated" by open sets in any meaningful sense.

Every topology $\mathcal{T}$ on $X$ satisfies $\mathcal{T}_{\text{indisc}} \subseteq \mathcal{T} \subseteq \mathcal{T}_{\text{disc}}$, and the collection of all topologies on $X$ forms a complete lattice under inclusion, with the indiscrete topology as the bottom element and the discrete topology as the top. This lattice perspective is productive: given two topologies $\mathcal{T}_1$ and $\mathcal{T}_2$ on $X$, their meet is $\mathcal{T}_1 \cap \mathcal{T}_2$ (which is easily verified to be a topology), and their join is the topology generated by $\mathcal{T}_1 \cup \mathcal{T}_2$.

### Neighborhood Systems

An equivalent and often more intuitive approach to topology proceeds through the concept of a *neighborhood system*. If $(X, \mathcal{T})$ is a topological space and $x \in X$, a *neighborhood* of $x$ is any set $N \subseteq X$ such that there exists an open set $U \in \mathcal{T}$ with $x \in U \subseteq N$. The collection $\mathcal{N}(x)$ of all neighborhoods of $x$ is the *neighborhood filter* at $x$. It satisfies four characteristic properties:

$$\text{(N1)}\quad X \in \mathcal{N}(x) \text{ and every } N \in \mathcal{N}(x) \text{ satisfies } x \in N$$

$$\text{(N2)}\quad \text{If } N \in \mathcal{N}(x) \text{ and } N \subseteq M, \text{ then } M \in \mathcal{N}(x)$$

$$\text{(N3)}\quad \text{If } N_1, N_2 \in \mathcal{N}(x), \text{ then } N_1 \cap N_2 \in \mathcal{N}(x)$$

$$\text{(N4)}\quad \text{For every } N \in \mathcal{N}(x), \text{ there exists } M \in \mathcal{N}(x) \text{ with } M \subseteq N \text{ such that } M \in \mathcal{N}(y) \text{ for all } y \in M$$

Properties N1 through N3 say that $\mathcal{N}(x)$ is a *filter* on $X$ containing $x$. Property N4 is the topological coherence condition: it says that every neighborhood of $x$ contains a neighborhood that is "uniformly" a neighborhood of all its own points, which is exactly the content of openness. This characterization is due to Hausdorff and is logically equivalent to the open-set axioms: given a neighborhood system satisfying N1–N4 on every point, one recovers a unique topology by declaring $U$ open if and only if $U \in \mathcal{N}(x)$ for every $x \in U$.

The neighborhood perspective is particularly well-suited to analysis and functional analysis, where the notion of "being close to a point" is more natural than "belonging to an abstract open set." For the working mathematician, fluency in both formulations — open sets and neighborhood filters — is essential, since different problems call for different languages.

---

## 2. Core Architecture & Mechanics

### Basis and Subbasis Constructions

Specifying a topology by listing all of its open sets is almost always impractical. For $\mathbb{R}$ with the standard topology, the open sets form an uncountable collection. The right approach is to identify a small generating family and show that it determines the topology completely. This leads to the concepts of basis and subbasis.

**Definition 2.1 (Basis).** Let $(X, \mathcal{T})$ be a topological space. A collection $\mathcal{B} \subseteq \mathcal{T}$ is a *basis* for $\mathcal{T}$ if every open set $U \in \mathcal{T}$ can be written as a union of elements of $\mathcal{B}$. Equivalently, for every $U \in \mathcal{T}$ and every $x \in U$, there exists $B \in \mathcal{B}$ such that $x \in B \subseteq U$.

Rather than starting from a topology and finding a basis, one more often starts from a candidate basis and constructs the topology it generates. The following theorem gives the precise conditions under which a family of sets qualifies as a basis for *some* topology.

**Theorem 2.1 (Basis Criterion).** Let $X$ be a set and $\mathcal{B} \subseteq \mathcal{P}(X)$ a collection of subsets. Then $\mathcal{B}$ is a basis for a topology on $X$ if and only if the following two conditions hold:

$$\text{(B1)}\quad \bigcup_{B \in \mathcal{B}} B = X$$

$$\text{(B2)}\quad \text{For all } B_1, B_2 \in \mathcal{B} \text{ and } x \in B_1 \cap B_2, \text{ there exists } B_3 \in \mathcal{B} \text{ such that } x \in B_3 \subseteq B_1 \cap B_2$$

*Proof.* First assume $\mathcal{B}$ is a basis for some topology $\mathcal{T}$. Since $X \in \mathcal{T}$ and every open set is a union of basis elements, $X = \bigcup_{B \in \mathcal{B}} B$, giving B1. For B2: given $B_1, B_2 \in \mathcal{B}$ and $x \in B_1 \cap B_2$, the intersection $B_1 \cap B_2$ is open (by T3), so there exists $B_3 \in \mathcal{B}$ with $x \in B_3 \subseteq B_1 \cap B_2$.

Conversely, assume B1 and B2 hold. Define $\mathcal{T}$ to be the collection of all sets expressible as unions of elements of $\mathcal{B}$ (including the empty union, which gives $\emptyset$). By B1, $X \in \mathcal{T}$. The collection $\mathcal{T}$ is closed under arbitrary unions by construction. It remains to verify T3. Let $U_1, U_2 \in \mathcal{T}$ and $x \in U_1 \cap U_2$. Since $U_1$ is a union of basis elements, there exists $B_1 \in \mathcal{B}$ with $x \in B_1 \subseteq U_1$, and similarly $B_2 \in \mathcal{B}$ with $x \in B_2 \subseteq U_2$. By B2, there exists $B_3 \in \mathcal{B}$ with $x \in B_3 \subseteq B_1 \cap B_2 \subseteq U_1 \cap U_2$. Hence $U_1 \cap U_2$ is a union of basis elements and lies in $\mathcal{T}$. By induction, finite intersections of elements of $\mathcal{T}$ are in $\mathcal{T}$, confirming T3. $\blacksquare$

The standard topology on $\mathbb{R}$ is generated by the basis $\mathcal{B} = \{(a,b) : a < b,\ a,b \in \mathbb{R}\}$ of open intervals. Verifying B1 and B2 is immediate: B1 holds since every real number lies in some open interval, and B2 holds because $(a_1,b_1) \cap (a_2,b_2) = (\max(a_1,a_2), \min(b_1,b_2))$ is itself an open interval (or empty) whenever nonempty.

A *subbasis* is an even more economical generating structure. 

**Definition 2.2 (Subbasis).** A collection $\mathcal{S} \subseteq \mathcal{P}(X)$ is a *subbasis* for a topology $\mathcal{T}$ on $X$ if the topology $\mathcal{T}$ is the smallest topology on $X$ containing $\mathcal{S}$. Equivalently, the family of all finite intersections of elements of $\mathcal{S}$ (together with $X$ itself, as the empty intersection) forms a basis for $\mathcal{T}$.

Every collection $\mathcal{S}$ of subsets of $X$ generates a topology this way, without any conditions analogous to B1 and B2, because we can always adjoin $X$ and $\emptyset$ to handle the degenerate cases. The topology generated by $\mathcal{S}$ consists of all arbitrary unions of finite intersections of elements of $\mathcal{S}$.

The product topology, one of the most important constructions in all of topology, is most cleanly defined via a subbasis. Given topological spaces $(X_\alpha, \mathcal{T}_\alpha)$ for $\alpha$ ranging over an index set $A$, the *product topology* on $\prod_{\alpha \in A} X_\alpha$ is generated by the subbasis of *sub-cylinders* $\pi_\alpha^{-1}(U_\alpha)$ for $U_\alpha \in \mathcal{T}_\alpha$ and $\alpha \in A$, where $\pi_\alpha$ denotes the projection onto the $\alpha$-th coordinate. This subbasis definition ensures that the product topology is exactly the coarsest topology making every projection map continuous, which is the right universal property.

### Structural Diagram: From Subbasis to Topology

The layered construction from subbasis to basis to full topology can be visualized as follows:

```
SUBBASIS S
  (arbitrary collection of subsets)
         |
         |  close under finite intersections
         v
BASIS B = { S_{i1} ∩ S_{i2} ∩ ... ∩ S_{ik} : S_{ij} ∈ S, k ≥ 0 }
  (B1: covers X, B2: intersection condition holds)
         |
         |  close under arbitrary unions
         v
TOPOLOGY T = { ∪_α B_α : B_α ∈ B }
  (T1: ∅, X ∈ T  |  T2: arbitrary unions  |  T3: finite intersections)
```

The vertical arrows represent closure operations. Moving from subbasis to basis adds finite intersection stability; moving from basis to topology adds arbitrary union stability. Each step is irreversible in the sense that the resulting structure has strictly more sets, and moving in the reverse direction (from a topology down to a basis) requires choosing a generating subfamily, which is typically non-unique.

### The Closure, Interior, and Boundary Operators

Given a topological space $(X, \mathcal{T})$, one defines three fundamental derived operators that assign to each subset $A \subseteq X$ a "regularized" version of that set reflecting the topology.

**Definition 2.3 (Interior).** The *interior* of $A$, written $\text{int}(A)$ or $A^\circ$, is the largest open set contained in $A$:
$$A^\circ = \bigcup \{ U \in \mathcal{T} : U \subseteq A \}$$

Since an arbitrary union of open sets is open by T2, the interior is itself open and is the unique largest open subset of $A$.

**Definition 2.4 (Closure).** The *closure* of $A$, written $\overline{A}$ or $\text{cl}(A)$, is the smallest closed set containing $A$:
$$\overline{A} = \bigcap \{ C \subseteq X : C \text{ is closed and } A \subseteq C \}$$

Since a finite intersection of closed sets is closed (the complement condition of T3), and in fact an *arbitrary* intersection of closed sets is closed (as the complement of an arbitrary union of open sets, using T2), the closure is itself closed. It is the unique smallest closed superset of $A$.

**Definition 2.5 (Boundary).** The *boundary* of $A$, written $\partial A$ or $\text{bd}(A)$, is:
$$\partial A = \overline{A} \setminus A^\circ = \overline{A} \cap \overline{X \setminus A}$$

The boundary consists of points that cannot be "separated" from $A$ or from its complement by open sets: every neighborhood of a boundary point meets both $A$ and $X \setminus A$.

There is an equivalent characterization of closure that makes its local nature transparent: $x \in \overline{A}$ if and only if every open set $U$ containing $x$ satisfies $U \cap A \neq \emptyset$. Equivalently, $x \in \overline{A}$ if and only if every neighborhood of $x$ intersects $A$. This formulation connects closure directly to the neighborhood filter and shows that $\overline{A}$ captures the idea of "points arbitrarily close to $A$" in topological terms.

**Theorem 2.2 (Kuratowski Closure Axioms).** Let $X$ be a set and $\text{cl}: \mathcal{P}(X) \to \mathcal{P}(X)$ an operator. Then $\text{cl}$ is the closure operator of some topology on $X$ if and only if it satisfies:

$$\text{(K1)}\quad \text{cl}(\emptyset) = \emptyset$$

$$\text{(K2)}\quad A \subseteq \text{cl}(A) \quad \text{for all } A \subseteq X$$

$$\text{(K3)}\quad \text{cl}(\text{cl}(A)) = \text{cl}(A) \quad \text{for all } A \subseteq X \quad \text{(idempotence)}$$

$$\text{(K4)}\quad \text{cl}(A \cup B) = \text{cl}(A) \cup \text{cl}(B) \quad \text{for all } A, B \subseteq X$$

*Proof sketch.* Given a topology $\mathcal{T}$, the closure operator defined in Definition 2.4 satisfies these axioms. K1 holds because $\emptyset$ is closed. K2 holds by definition of closure as a superset. K3 holds because $\text{cl}(A)$ is already closed, so it equals its own closure. For K4: since $A \subseteq A \cup B$ and $B \subseteq A \cup B$, we have $\text{cl}(A) \cup \text{cl}(B) \subseteq \text{cl}(A \cup B)$. Conversely, $\text{cl}(A) \cup \text{cl}(B)$ is a finite union of closed sets, hence closed, and contains $A \cup B$, so $\text{cl}(A \cup B) \subseteq \text{cl}(A) \cup \text{cl}(B)$.

Conversely, given an operator satisfying K1–K4, declare $C$ closed if $\text{cl}(C) = C$. The resulting closed sets satisfy the axioms for a topology: $X$ and $\emptyset$ are closed by K1 and K2; arbitrary intersections of closed sets are closed because closure can be characterized pointwise; finite unions of closed sets are closed by K4. The closure operator of this topology is precisely the given $\text{cl}$. $\blacksquare$

The Kuratowski axioms are historically significant because they represent yet another complete axiomatization of topology — equivalent to the open-set axioms and the neighborhood axioms — but organized around the notion of limit points. Kuratowski's 1922 formulation predates the now-standard open-set presentation and remains useful in settings where the closure operation is the natural primitive, such as the study of topological lattices and closure spaces in theoretical computer science.

### Explicit Computation: Closure, Interior, and Boundary on $\mathbb{R}$

The standard topology on $\mathbb{R}$ is generated by the basis of open intervals, and closed sets are those whose complements are open. Working through examples in this topology builds the geometric intuition that abstract theorems require.

Consider $A = (0,1] \subseteq \mathbb{R}$. The interior $A^\circ$ is the largest open set contained in $(0,1]$. The set $(0,1)$ is open and contained in $A$; and no open set can contain $1$ while remaining within $A$, since every open set containing $1$ contains an interval $(1-\varepsilon, 1+\varepsilon)$, which extends beyond $A$. Therefore $A^\circ = (0,1)$.

The closure $\overline{A}$ is the smallest closed set containing $(0,1]$. The closed interval $[0,1]$ is closed (its complement $(-\infty,0) \cup (1,\infty)$ is open) and contains $A$. For any $\varepsilon > 0$, the set $(0,1]$ is not contained in $[\varepsilon, 1]$ since points in $(0,\varepsilon)$ are in $A$ but not $[\varepsilon,1]$. Therefore $[0,1]$ is the smallest closed superset of $A$, and $\overline{A} = [0,1]$.

The boundary is therefore:
$$\partial A = \overline{A} \setminus A^\circ = [0,1] \setminus (0,1) = \{0, 1\}$$

This confirms the intuition that boundary points are those at the "edge" of a set, where neighborhoods cross from inside to outside. Both $0$ and $1$ have this property: every open interval around $0$ or $1$ meets both $(0,1]$ and its complement.

---

## 3. High-Performance Optimization & Failure Modes

### Working Efficiently with Topological Axioms: Strategies for Proof Construction

The practicing mathematician working in topology encounters a characteristic set of technical challenges. Chief among these is the problem of *verifying or disproving* that a proposed collection forms a topology, and the problem of computing closure and interior operators for complex sets without direct appeal to the definition.

When verifying that $\mathcal{T}$ is a topology, the most common failure point is T3: the finite intersection condition. Verifying T2 is usually trivial because union-stability is structurally easy to arrange; intersection-stability requires checking that the intersection of any two open sets is open, which typically demands a careful case analysis depending on how the open sets are defined. For topology defined by a basis, the Basis Criterion (Theorem 2.1) reduces this to checking B2 for pairs of basis elements, which is a significantly smaller verification task.

A common technique is to prove that a family $\mathcal{B}$ satisfies B1 and B2 and then work entirely within the basis, using the following lemma implicitly: $U \in \mathcal{T}_\mathcal{B}$ if and only if for every $x \in U$, there exists $B \in \mathcal{B}$ with $x \in B \subseteq U$. This "local basis" criterion localizes all topological verification to individual points, which is exactly how analysis works: $f$ is continuous at $x$ if and only if for every open $V$ containing $f(x)$, there exists a basis element $B$ around $x$ with $f(B) \subseteq V$.

### Comparing Topologies: The Coarser-Finer Order

One of the most important practical skills is comparing two topologies $\mathcal{T}_1$ and $\mathcal{T}_2$ on the same set $X$. We say $\mathcal{T}_1$ is *coarser* than $\mathcal{T}_2$ (and $\mathcal{T}_2$ is *finer* than $\mathcal{T}_1$) if $\mathcal{T}_1 \subseteq \mathcal{T}_2$. The operative test for bases is:

**Lemma 3.1.** Let $\mathcal{B}_1$ and $\mathcal{B}_2$ be bases for topologies $\mathcal{T}_1$ and $\mathcal{T}_2$ on $X$. Then $\mathcal{T}_1 \subseteq \mathcal{T}_2$ if and only if for every $B_1 \in \mathcal{B}_1$ and every $x \in B_1$, there exists $B_2 \in \mathcal{B}_2$ with $x \in B_2 \subseteq B_1$.

*Proof.* Suppose $\mathcal{T}_1 \subseteq \mathcal{T}_2$. Every $B_1 \in \mathcal{B}_1 \subseteq \mathcal{T}_1 \subseteq \mathcal{T}_2$ is open in $\mathcal{T}_2$, so for every $x \in B_1$, the definition of basis for $\mathcal{T}_2$ gives $B_2 \in \mathcal{B}_2$ with $x \in B_2 \subseteq B_1$. Conversely, suppose the basis condition holds. For any $U \in \mathcal{T}_1$ and $x \in U$, there exists $B_1 \in \mathcal{B}_1$ with $x \in B_1 \subseteq U$, and then $B_2 \in \mathcal{B}_2$ with $x \in B_2 \subseteq B_1 \subseteq U$. So $U \in \mathcal{T}_2$. $\blacksquare$

Applied to $\mathbb{R}$: the basis of open intervals $(a,b)$ with $a,b \in \mathbb{Q}$ generates the same topology as the basis of open intervals $(a,b)$ with $a,b \in \mathbb{R}$. The former is a *countable* basis, establishing that $\mathbb{R}$ is *second-countable* — a property with far-reaching consequences (Lindelöf's theorem, the existence of countable dense subsets, and separability all follow). Verifying this via Lemma 3.1 is routine: for any $(a,b)$ and $x \in (a,b)$, one chooses rational $a' < x < b'$ with $a < a'$ and $b' < b$, giving the rational basis element $(a',b')$ containing $x$ inside $(a,b)$.

### Failure Modes in Specifying Topologies

Several constructions that appear plausible at first inspection fail to define topologies.

**Failure Mode 1: The Cocountable Trap on $\mathbb{R}$.** Define $\mathcal{T}$ on $\mathbb{R}$ by declaring $U$ open if $U = \emptyset$ or $\mathbb{R} \setminus U$ is countable (the *cocountable topology*). Checking T1–T2 is easy. For T3: let $U_1 = \mathbb{R} \setminus \mathbb{Q}$ and $U_2 = \mathbb{R} \setminus (\mathbb{R} \setminus \mathbb{Q}) = \mathbb{Q}$. Then $\mathbb{R} \setminus U_1 = \mathbb{Q}$ is countable and $\mathbb{R} \setminus U_2 = \mathbb{R} \setminus \mathbb{Q}$ is uncountable, so $U_2 \notin \mathcal{T}$. This particular pair does not cause T3 to fail (T3 concerns finite intersections of *open* sets), but the general point stands: the cocountable topology *is* a valid topology on $\mathbb{R}$, though it is strictly coarser than the standard topology, and many familiar sets (like individual points) are not closed in it. The failure mode is the assumption that it agrees with the standard topology — it does not.

**Failure Mode 2: The "Half-Open" Basis Confusion.** A student might propose the collection $\mathcal{B} = \{[a,b) : a < b,\ a,b \in \mathbb{R}\}$ as a basis for the standard topology on $\mathbb{R}$. It satisfies B1 and B2 (the intersection $[a_1,b_1) \cap [a_2,b_2) = [\max(a_1,a_2), \min(b_1,b_2))$ is again a half-open interval or empty), so it does define a topology — but *not* the standard topology. This is the *lower limit topology* (or Sorgenfrey line), written $\mathbb{R}_\ell$. It is strictly finer than the standard topology: every open interval $(a,b) = \bigcup_{n} [a + 1/n, b)$ is open in $\mathbb{R}_\ell$, but $[0,1)$ is open in $\mathbb{R}_\ell$ and not in the standard topology. The Sorgenfrey line provides counterexamples to several plausible conjectures (most notably, $\mathbb{R}_\ell \times \mathbb{R}_\ell$ is not normal despite $\mathbb{R}_\ell$ being normal), and is a standard stress-test for topological intuitions.

**Failure Mode 3: Confusing Boundary with the Topological Frontier.** A common error is to identify $\partial A$ with the set-theoretic "edge" of $A$ as visualized geometrically, then apply this visualization in settings where it fails. In the discrete topology on $\mathbb{R}$, every set is both open and closed, so $\overline{A} = A$ and $A^\circ = A$ for every $A$, giving $\partial A = \emptyset$ for all $A$. In particular, the boundary of $[0,1]$ in the discrete topology is empty, not $\{0,1\}$. The boundary is a topological invariant that depends entirely on the topology, not on the ambient set's geometry.

### The Derived Set and Condensation Points

A refinement of the closure operator yields the concept of a *derived set*. The *derived set* $A'$ of a subset $A \subseteq X$ is the set of all *limit points* (or *accumulation points*) of $A$: points $x \in X$ such that every open set containing $x$ meets $A \setminus \{x\}$. Crucially, $x$ need not belong to $A$ itself. The relationship between closure and derived set is:

$$\overline{A} = A \cup A'$$

This identity requires proof. If $x \in A$, then trivially $x \in \overline{A}$. If $x \in A'$, then every open neighborhood of $x$ meets $A$, so $x \in \overline{A}$ by the neighborhood characterization of closure. Conversely, if $x \notin A$ and $x \notin A'$, then there exists an open $U$ containing $x$ with $U \cap (A \setminus \{x\}) = \emptyset$. Since $x \notin A$, this means $U \cap A = \emptyset$, so $x \notin \overline{A}$.

A set $A$ is closed if and only if $A' \subseteq A$: a closed set contains all its limit points. A set is *perfect* if $A = A'$, meaning it is closed and every point of $A$ is a limit point of $A$. The Cantor set is the canonical example of a perfect set that contains no open interval — a totally disconnected, uncountable, measure-zero subset of $\mathbb{R}$ whose topological structure is as extreme as the Sorgenfrey line is for basis constructions.

A *condensation point* of $A$ is a point $x$ such that every open neighborhood of $x$ contains uncountably many points of $A$. In second-countable spaces (which is the natural setting for most analysis), every uncountable closed set has uncountably many condensation points, and the set of non-condensation points of any closed set is countable. This is the Cantor-Bendixson theorem, whose proof uses transfinite induction on derived sets $A^{(0)} = A$, $A^{(\alpha+1)} = (A^{(\alpha)})'$, and $A^{(\lambda)} = \bigcap_{\alpha < \lambda} A^{(\alpha)}$ for limit ordinals $\lambda$, iterating until stabilization. The result is a canonical decomposition $A = P \cup C$ where $P$ is perfect and $C$ is countable — a first bridge between the topological and set-theoretic content of the subject, and a preview of the deeper interaction between topology and descriptive set theory that runs through the rest of the curriculum.

The lesson establishes the foundational language through which all subsequent topological reasoning is conducted. The open set axioms are not merely a convenient definition but a precise distillation of what is needed to support continuous functions, limit operations, and structural invariants. The basis and subbasis constructions show how rich and varied topologies can be built from economical specifications. The closure, interior, and boundary operators translate the global structure of the topology into local geometric information about individual subsets. Each of these components reappears, in increasingly sophisticated form, throughout the study of connectedness, compactness, separation axioms, and homotopy theory that follows.
