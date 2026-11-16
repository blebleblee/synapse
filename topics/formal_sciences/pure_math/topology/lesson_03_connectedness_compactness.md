# Lesson 3: Connectedness, Path-Connectedness, Compactness

## 1. First-Principles Intuition & Invariants

Topology, at its philosophical core, is the study of what persists when a space is stretched, twisted, or continuously deformed. Among all the properties a topological space can possess, three rise to singular importance in pure mathematics and its applications to analysis, algebra, and theoretical computer science: connectedness, path-connectedness, and compactness. These are not merely technical definitions imposed for convenience. They are the precise mathematical articulations of three deeply intuitive geometric phenomena — the idea that a space is "in one piece," the idea that any two points can be "continuously joined," and the idea that a space is "finite in extent" in a sense robust enough to survive passage from metric spaces to purely abstract topologies.

Understanding these properties requires resisting the temptation to reduce them to their most familiar examples and instead interrogating why each definition takes exactly the form it does, what pathological cases it rules out, and how the definitions interact and diverge as one moves from the well-behaved metric spaces of classical analysis to the exotic generality of arbitrary topological spaces.

### Connectedness: The Formal Articulation of "One Piece"

The intuitive idea of a space being connected — that it cannot be pulled apart into two separate regions — is captured by negation: a space fails to be connected precisely when it admits a nontrivial separation.

**Definition (Connectedness).** A topological space $(X, \mathcal{T})$ is *connected* if there is no pair of disjoint nonempty open sets $U, V \subseteq X$ such that $X = U \cup V$. Equivalently, the only subsets of $X$ that are simultaneously open and closed (clopen) are $\emptyset$ and $X$ itself.

The equivalence of these two formulations is immediate. If $X = U \cup V$ with $U, V$ disjoint, open, and nonempty, then $U = X \setminus V$ is also closed, so $U$ is a proper nonempty clopen subset. Conversely, any proper nonempty clopen set $U$ produces the separation $X = U \cup (X \setminus U)$.

It is worth pausing on why the definition demands both $U$ and $V$ be open (rather than, say, one open and one closed, or both measurable). The topology encodes precisely the notion of "nearness" in $X$: open sets are neighborhoods, regions of local coherence. A separation by two disjoint open sets means the two pieces are not merely distinct but genuinely isolated from one another — no sequence, no limit, no accumulation point can pass from one to the other. This is the topological rendering of "disconnection."

**Lemma 3.1 (Continuous images of connected spaces are connected).** If $f: X \to Y$ is continuous and $X$ is connected, then $f(X)$ is connected in $Y$.

*Proof.* Suppose for contradiction that $f(X)$ is not connected. Then there exist disjoint nonempty open sets $U, V$ in $Y$ with $f(X) \subseteq U \cup V$, $f(X) \cap U \neq \emptyset$, and $f(X) \cap V \neq \emptyset$. The sets $f^{-1}(U)$ and $f^{-1}(V)$ are open in $X$ by continuity of $f$. They are disjoint because $U \cap V = \emptyset$, and their union covers $X$ because $f(X) \subseteq U \cup V$. Neither is empty since $f(X)$ meets both $U$ and $V$. This gives a separation of $X$, contradicting connectedness. $\blacksquare$

This lemma is the engine behind most applications of connectedness: it guarantees that continuous functions cannot "split" a connected space. The Intermediate Value Theorem in classical analysis is precisely this result applied to $f: [a,b] \to \mathbb{R}$, with $[a,b]$ connected — a fact we establish below.

**Proposition 3.2.** Every interval in $\mathbb{R}$ (bounded or unbounded, open or closed) is connected.

*Proof.* Let $I \subseteq \mathbb{R}$ be an interval and suppose $I = U \cup V$ is a separation, with $U$ and $V$ disjoint, open in $I$, and nonempty. Pick $a \in U$ and $b \in V$; without loss of generality, $a < b$. Consider the set $S = \{x \in I : [a, x] \subseteq U\}$. Since $U$ is open and $a \in U$, there exists $\epsilon > 0$ with $[a, a+\epsilon) \subseteq U$, so $S$ is nonempty and bounded above by $b$. Let $c = \sup S$. Since $I$ is an interval and $a < c \leq b$, we have $c \in I$.

If $c \in U$, then since $U$ is open in $I$, there exists $\delta > 0$ with $(c - \delta, c + \delta) \cap I \subseteq U$. But then $c + \delta/2 \in S$, contradicting $c = \sup S$.

If $c \in V$, then since $V$ is open in $I$, there exists $\delta > 0$ with $(c-\delta, c+\delta) \cap I \subseteq V$. But then $c - \delta/2$ is an upper bound for $S$ smaller than $c$, contradicting $c = \sup S$.

Since $c$ must belong to either $U$ or $V$ and both cases yield contradictions, no such separation exists and $I$ is connected. $\blacksquare$

The proof uses only the completeness of $\mathbb{R}$ (via the existence of $\sup S$) and the definition of an interval (closed under betweenness). It is essentially the topological proof of the Intermediate Value Theorem, with no appeal to epsilon-delta analysis.

### Path-Connectedness: Joining Points by Continuous Curves

A stronger notion demands not merely that the space cannot be separated, but that any two points can be explicitly joined by a continuous path.

**Definition (Path-Connectedness).** A topological space $X$ is *path-connected* if for every $x, y \in X$, there exists a continuous function $\gamma: [0,1] \to X$ with $\gamma(0) = x$ and $\gamma(1) = y$. The function $\gamma$ is called a *path* from $x$ to $y$.

Since $[0,1]$ is connected and $\gamma$ is continuous, $\gamma([0,1])$ is connected by Lemma 3.1. This immediately implies the following.

**Proposition 3.3.** Every path-connected space is connected.

*Proof.* Suppose $X$ is path-connected and let $x_0 \in X$ be arbitrary. For each $y \in X$, choose a path $\gamma_y: [0,1] \to X$ with $\gamma_y(0) = x_0$ and $\gamma_y(1) = y$. Each image $\gamma_y([0,1])$ is a connected subset of $X$ containing $x_0$. The union

$$X = \bigcup_{y \in X} \gamma_y([0,1])$$

is a union of connected sets sharing the common point $x_0$. By the standard result that a union of connected sets with a common point is connected, $X$ is connected. $\blacksquare$

The converse fails, and the failure is instructive. The classical counterexample is the *topologist's sine curve*:

$$S = \left\{ \left(x, \sin\frac{1}{x}\right) : x > 0 \right\} \cup \{(0, y) : y \in [-1, 1]\}$$

with the subspace topology from $\mathbb{R}^2$. The set $S$ is connected: the oscillating curve is path-connected and hence connected, and its closure (which adds the vertical segment $\{0\} \times [-1,1]$) is connected because the closure of a connected set is connected. But $S$ is not path-connected. No path can reach a point on the vertical segment from a point on the sine curve, because the sine curve oscillates with unbounded frequency as $x \to 0^+$, preventing any continuous $\gamma: [0,1] \to S$ from converging to a definite point on the segment as $t \to t_0$ for the moment $\gamma(t_0)$ would first hit the segment.

The formal argument proceeds by contradiction: if such a path $\gamma$ existed, one considers the last time $t_0 \in [0,1]$ such that $\gamma(t_0) = (0, y_0)$ for some $y_0$. For $t < t_0$ near $t_0$, the path lies in the oscillating curve, so its first coordinate $\pi_1(\gamma(t)) > 0$ tends to $0$. The second coordinate $\sin(1/\pi_1(\gamma(t)))$ oscillates between $-1$ and $1$ with period tending to $0$, and cannot converge to any single value $y_0$, contradicting continuity of $\gamma$ at $t_0$.

This example is a canonical illustration of why the two definitions are not equivalent in general spaces, even though they agree on open subsets of $\mathbb{R}^n$ and on all manifolds.

**Remark on Path-Components.** Just as connectedness gives rise to connected components (the maximal connected subsets of $X$, which partition $X$), path-connectedness gives rise to path-components: the equivalence classes under the relation "$x \sim y$ if there exists a path from $x$ to $y$." This is indeed an equivalence relation: reflexivity follows from the constant path, symmetry from path reversal ($t \mapsto \gamma(1-t)$), and transitivity from path concatenation. Each path-component is path-connected, and the path-components of $X$ refine its connected components.

### Compactness: Finiteness Without Boundaries

Compactness is at once the deepest and the most technically demanding of the three properties. Its definition through open covers is initially opaque, but its motivation becomes clear once one appreciates the problem it was designed to solve: how to extend the well-behaved properties of finite sets to infinite sets.

Finite sets have a remarkable property: any open cover of a finite set has a finite subcover, trivially, by picking one open set for each point. The challenge is to identify which infinite sets behave like finite ones in this respect — specifically, which sets guarantee that every open cover, however fine or uncountable, admits a finite subcover.

**Definition (Compactness).** A topological space $X$ is *compact* if every open cover of $X$ has a finite subcover. That is, for every collection $\{U_\alpha\}_{\alpha \in A}$ of open sets satisfying $X = \bigcup_{\alpha \in A} U_\alpha$, there exist finitely many indices $\alpha_1, \ldots, \alpha_n \in A$ such that $X = U_{\alpha_1} \cup \cdots \cup U_{\alpha_n}$.

The quantifier structure of this definition demands attention: the condition must hold for *every* open cover, including covers specifically constructed to be pathologically large or fine. This universality is what gives compactness its power. When you prove something for every open cover, you have a tool that works against any adversary who tries to construct a cover with no finite subcover.

The historical path to this definition runs through Heine, Borel, Lebesgue, and Fréchet. The key observation, developed in the late nineteenth century, was that the closed bounded intervals of $\mathbb{R}$ were the natural domain for theorems about uniform continuity, uniform convergence, and the existence of maxima — and that these intervals shared exactly this covering property.

**Theorem 3.4 (Heine-Borel Theorem).** A subset $K \subseteq \mathbb{R}^n$ is compact (in the subspace topology from $\mathbb{R}^n$) if and only if it is closed and bounded.

The Heine-Borel theorem is one of the cornerstones of real analysis, and its proof illuminates the interplay between the algebraic structure of $\mathbb{R}^n$ (completeness, the least upper bound property) and topological compactness. We prove it in $\mathbb{R}^1$ for clarity; the generalization to $\mathbb{R}^n$ follows by induction using the product compactness theorem (Tychonoff's theorem for finite products).

*Proof (Heine-Borel in $\mathbb{R}$).* We show that $[a, b] \subseteq \mathbb{R}$ is compact.

Let $\{U_\alpha\}_{\alpha \in A}$ be an open cover of $[a,b]$. Define

$$S = \{x \in [a,b] : [a, x] \text{ can be covered by finitely many } U_\alpha\}.$$

The set $S$ is nonempty since $a \in S$: some $U_\alpha$ contains $a$, and $[a,a] = \{a\} \subseteq U_\alpha$. Let $c = \sup S$; since $S \subseteq [a,b]$, we have $c \leq b$. Some $U_\beta$ contains $c$, and since $U_\beta$ is open, there exists $\epsilon > 0$ with $(c - \epsilon, c + \epsilon) \subseteq U_\beta$.

Since $c - \epsilon < c = \sup S$, there exists $x_0 \in S$ with $x_0 > c - \epsilon$. By definition of $S$, the interval $[a, x_0]$ is covered by finitely many $U_\alpha$, say $U_{\alpha_1}, \ldots, U_{\alpha_k}$. Then $[a, \min(c + \epsilon/2, b)]$ is covered by $U_{\alpha_1}, \ldots, U_{\alpha_k}, U_\beta$, which is a finite subcover. This means $\min(c + \epsilon/2, b) \in S$.

If $c < b$, this contradicts $c = \sup S$. Therefore $c = b$, and $b \in S$, meaning $[a,b]$ has a finite subcover. This establishes compactness of $[a,b]$.

For the converse, suppose $K \subseteq \mathbb{R}$ is compact. If $K$ were unbounded, the open cover $\{(-n, n)\}_{n \in \mathbb{N}}$ would have no finite subcover, since any finite subcollection is bounded. If $K$ were not closed, it would omit some limit point $x_0$. The open sets $U_n = \{x \in \mathbb{R} : |x - x_0| > 1/n\}$ cover $K$ (since $x_0 \notin K$), but no finite subcollection covers $K$ (since $x_0$ is a limit point of $K$, points of $K$ lie within $1/n$ of $x_0$ for every $n$). Therefore, compactness implies closed and bounded. $\blacksquare$

The Heine-Borel theorem fails dramatically in infinite-dimensional spaces. The closed unit ball in an infinite-dimensional Banach space is closed and bounded but never compact — the sequence $(e_n)$ of standard basis vectors satisfies $\|e_m - e_n\| = \sqrt{2}$ for $m \neq n$, admitting no convergent subsequence. This signals that compactness is a genuinely topological invariant, not reducible to metric notions of size.

### Sequential Compactness and Limit Point Compactness

In metric spaces, two alternative characterizations of compactness are equivalent to the open cover definition. These alternative formulations often provide more tractable paths to proofs and reveal the combinatorial heart of compactness.

**Definition (Sequential Compactness).** A topological space $X$ is *sequentially compact* if every sequence in $X$ has a convergent subsequence (converging to a point in $X$).

**Definition (Limit Point Compactness).** A topological space $X$ is *limit point compact* if every infinite subset of $X$ has a limit point in $X$.

Recall that $x \in X$ is a limit point of $A \subseteq X$ if every open neighborhood of $x$ contains a point of $A$ other than $x$ itself. Limit point compactness is sometimes called the Bolzano-Weierstrass property, in honor of the theorem (proved for $\mathbb{R}^n$ by those mathematicians) that every bounded infinite set in $\mathbb{R}^n$ has a limit point.

**Theorem 3.5 (Interrelations in Metric Spaces).** For a metric space $(X, d)$, the following are equivalent:
1. $X$ is compact (every open cover has a finite subcover).
2. $X$ is sequentially compact.
3. $X$ is limit point compact.

The proof proceeds in a cycle: (1) $\Rightarrow$ (2) $\Rightarrow$ (3) $\Rightarrow$ (1). We prove each implication in full.

*Proof of (1) $\Rightarrow$ (2).* Suppose $X$ is compact and let $(x_n)$ be a sequence in $X$. We first establish that for every $\epsilon > 0$, some ball $B(x, \epsilon)$ contains infinitely many terms of the sequence. Suppose not: then for some $\epsilon > 0$, every $B(x, \epsilon)$ contains only finitely many terms. The collection $\{B(x, \epsilon) : x \in X\}$ is an open cover of $X$, so by compactness it admits a finite subcover $B(x_1, \epsilon), \ldots, B(x_k, \epsilon)$. But each $B(x_i, \epsilon)$ contains finitely many terms of $(x_n)$, so $(x_n)$ has only finitely many terms in total — a contradiction since $(x_n)$ is an infinite sequence.

Now construct a convergent subsequence by a diagonal-style argument. For $\epsilon = 1$, some ball $B(x^{(1)}, 1)$ contains infinitely many terms; call this infinite index set $I_1$. For $\epsilon = 1/2$, some ball $B(x^{(2)}, 1/2)$ contains infinitely many terms from $\{x_n : n \in I_1\}$; call this index set $I_2 \subseteq I_1$. Continuing, at stage $k$ we find an infinite index set $I_k \subseteq I_{k-1}$ and a point $x^{(k)}$ such that $\{x_n : n \in I_k\} \subseteq B(x^{(k)}, 1/k)$.

Pick $n_k \in I_k$ with $n_k > n_{k-1}$ at each stage. The subsequence $(x_{n_k})$ is Cauchy: for $j, k \geq N$, both $x_{n_j}$ and $x_{n_k}$ lie in $B(x^{(N)}, 1/N)$, so $d(x_{n_j}, x_{n_k}) < 2/N$. Since $X$ is compact, it is complete (as we now argue: if $(x_{n_k})$ is Cauchy and $X$ is compact, the limit point compactness we establish in (2) $\Rightarrow$ (3) $\Rightarrow$ (1) guarantees the sequence converges). The subsequence converges in $X$. $\blacksquare$

A cleaner route uses the notion of *total boundedness*: a metric space is compact if and only if it is complete and totally bounded, where total boundedness means that for every $\epsilon > 0$, $X$ can be covered by finitely many balls of radius $\epsilon$.

*Proof of (2) $\Rightarrow$ (3).* Suppose $X$ is sequentially compact and let $A \subseteq X$ be an infinite subset. Choose a sequence $(x_n)$ of distinct points in $A$. By sequential compactness, some subsequence $(x_{n_k})$ converges to a limit $x \in X$. Since the terms $x_{n_k}$ are distinct and converge to $x$, every open neighborhood of $x$ contains infinitely many, hence at least one, $x_{n_k} \neq x$. Therefore $x$ is a limit point of $A$ (and of $X$). $\blacksquare$

*Proof of (3) $\Rightarrow$ (1).* Suppose $X$ is limit point compact and let $\{U_\alpha\}$ be an open cover. We use total boundedness: we claim $X$ is totally bounded. Suppose not; then some $\epsilon > 0$ admits no finite $\epsilon$-net. Construct a sequence: pick $x_1$ arbitrarily. Having chosen $x_1, \ldots, x_n$ such that $d(x_i, x_j) \geq \epsilon$ for all $i \neq j$, we can find $x_{n+1}$ not within $\epsilon$ of any $x_i$ (since $\{B(x_i, \epsilon) : i = 1, \ldots, n\}$ does not cover $X$). The infinite set $A = \{x_1, x_2, \ldots\}$ has no limit point, since any ball $B(x, \epsilon/2)$ contains at most one $x_n$ — contradicting limit point compactness. So $X$ is totally bounded.

Now we claim $X$ is complete. If $(x_n)$ is a Cauchy sequence, the set $\{x_n\}$ is either finite (and the sequence is eventually constant, hence convergent) or infinite (and by limit point compactness, has a limit point $x$). One verifies that $x_n \to x$.

A complete totally bounded metric space is compact by a standard argument: given an open cover $\{U_\alpha\}$ with no finite subcover, produce a Cauchy sequence with no convergent subsequence, contradicting completeness (details proceed by bisection: cover $X$ with finitely many balls of radius $1$; at least one ball $B_1$ has no finite subcover; cover $B_1$ with balls of radius $1/2$; find $B_2 \subseteq B_1$ with no finite subcover; and so on, producing a nested sequence of balls whose radii tend to $0$, whose centers form a Cauchy sequence converging to a point $x$, which some $U_\alpha$ contains, contradicting the assumption that the ball at stage $N$ admits no finite subcover for large enough $N$). $\blacksquare$

### Where the Equivalences Break Down

The equivalence of these three forms of compactness is special to metric spaces. In general topological spaces, the implications are strictly one-directional. Compactness does not imply sequential compactness: the product $[0,1]^{[0,1]}$ (the space of all functions $[0,1] \to [0,1]$ with the product topology) is compact by Tychonoff's theorem, but not sequentially compact. Sequential compactness does not imply compactness in general: a first-countable, sequentially compact space need not be compact unless it is also Lindelöf (every open cover has a countable subcover). Limit point compactness does not imply compactness either: the particular point topology on an infinite set provides a counterexample.

The correct general hierarchy is: compactness implies limit point compactness in $T_1$ spaces (where points are closed), and sequential compactness implies limit point compactness always. The full equivalence depends on the space having enough structure — first-countability, the Hausdorff property, and the metric structure are each doing real work.

---

## 2. Core Architecture & Mechanics

The relationships among connectedness, path-connectedness, and compactness, and among the three forms of compactness, are most clearly seen through the interaction of their definitions with continuous maps and subspace constructions. The following diagram renders the logical dependencies and implication structure.

```
PATH-CONNECTED
      |
      | (Proposition 3.3)
      v
  CONNECTED
  
  
COMPACT (open cover)
      |
      | in metric spaces       in T1 spaces
      v                              |
SEQUENTIALLY COMPACT  -------> LIMIT POINT COMPACT
      |
      | (requires first-countability)
      v
   (implies compact in metric spaces, via total boundedness + completeness)
```

In the vertical chain on the left, path-connectedness strictly implies connectedness. The gap is illustrated by the topologist's sine curve: connected but not path-connected. In the lower chain, the three forms of compactness are equivalent in metric spaces but diverge in general topological spaces.

The following diagram exhibits how these properties interact under the fundamental constructions of topology.

```
CONSTRUCTION              CONNECTEDNESS    PATH-CONN.    COMPACTNESS
─────────────────────────────────────────────────────────────────────
Continuous image          preserved        preserved     preserved
Closed subspace           NOT preserved    NOT preserved preserved
Open subspace             NOT preserved    NOT preserved NOT preserved
Finite product            preserved        preserved     preserved
Arbitrary product         preserved        preserved     preserved (Tychonoff)
Closure                   preserved        NOT preserved preserved (if compact)
Union (common point)      preserved        preserved     NOT preserved
─────────────────────────────────────────────────────────────────────
```

Each entry in this table is a theorem — not an observation — and understanding the proof of each row is essential for working in topology. We detail the most consequential.

### Compactness Is Preserved by Continuous Maps

**Theorem 3.6.** If $f: X \to Y$ is continuous and $X$ is compact, then $f(X)$ is compact.

*Proof.* Let $\{V_\alpha\}$ be an open cover of $f(X)$. Each $V_\alpha$ is open in $f(X)$ (in the subspace topology from $Y$), so $V_\alpha = U_\alpha \cap f(X)$ for some $U_\alpha$ open in $Y$. The sets $f^{-1}(U_\alpha)$ are open in $X$ by continuity and cover $X$. By compactness, finitely many suffice: $X \subseteq f^{-1}(U_{\alpha_1}) \cup \cdots \cup f^{-1}(U_{\alpha_n})$. Then $f(X) \subseteq U_{\alpha_1} \cup \cdots \cup U_{\alpha_n}$, and intersecting with $f(X)$ gives $f(X) \subseteq V_{\alpha_1} \cup \cdots \cup V_{\alpha_n}$. $\blacksquare$

This theorem immediately yields two classical results: a continuous real-valued function on a compact space attains its maximum and minimum (since $f(X) \subseteq \mathbb{R}$ is compact, hence closed and bounded by Heine-Borel, so it contains $\sup f(X)$ and $\inf f(X)$); and a continuous bijection from a compact space to a Hausdorff space is a homeomorphism (since the continuous image of a closed, hence compact, subset is compact, hence closed in the Hausdorff codomain, so the inverse is continuous).

### Closed Subsets of Compact Spaces Are Compact

**Theorem 3.7.** If $X$ is compact and $C \subseteq X$ is closed, then $C$ is compact.

*Proof.* Let $\{U_\alpha\}$ be an open cover of $C$. The collection $\{U_\alpha\} \cup \{X \setminus C\}$ is an open cover of $X$ (the set $X \setminus C$ is open since $C$ is closed). By compactness of $X$, finitely many sets cover $X$: say $U_{\alpha_1}, \ldots, U_{\alpha_n}, X \setminus C$. These cover $C$, and $X \setminus C$ contributes nothing to the cover of $C$, so $U_{\alpha_1}, \ldots, U_{\alpha_n}$ cover $C$. $\blacksquare$

The converse also holds in Hausdorff spaces.

**Theorem 3.8.** If $X$ is Hausdorff and $C \subseteq X$ is compact, then $C$ is closed in $X$.

*Proof.* We show $X \setminus C$ is open. Fix $x \in X \setminus C$. For each $c \in C$, since $X$ is Hausdorff, there exist disjoint open sets $U_c \ni x$ and $V_c \ni c$. The sets $\{V_c : c \in C\}$ cover $C$, so by compactness there exist $c_1, \ldots, c_n$ with $C \subseteq V_{c_1} \cup \cdots \cup V_{c_n}$. Let $U = U_{c_1} \cap \cdots \cap U_{c_n}$. Then $U$ is open, $x \in U$, and $U \cap C = \emptyset$ since $U \subseteq U_{c_i}$ and $U_{c_i} \cap V_{c_i} = \emptyset$. So $U \subseteq X \setminus C$, proving $X \setminus C$ is open. $\blacksquare$

Together, Theorems 3.7 and 3.8 give the clean characterization: in a compact Hausdorff space, the compact subsets are exactly the closed subsets.

### Lebesgue's Number Lemma

One of the most practically useful results in metric space topology is a consequence of compactness with no analogue in arbitrary topological spaces.

**Lemma 3.9 (Lebesgue Number Lemma).** Let $\{U_\alpha\}$ be an open cover of a compact metric space $(X, d)$. There exists $\lambda > 0$ (the *Lebesgue number* of the cover) such that every subset of $X$ with diameter less than $\lambda$ is contained in some $U_\alpha$.

*Proof.* For each $x \in X$, since $\{U_\alpha\}$ covers $x$, some $U_{\alpha(x)}$ contains $x$, and since $U_{\alpha(x)}$ is open, there exists $r(x) > 0$ with $B(x, r(x)) \subseteq U_{\alpha(x)}$. The function $x \mapsto r(x)$ may not be continuous directly, but consider the function $f: X \to \mathbb{R}$ defined by $f(x) = \sup\{r > 0 : B(x, r) \subseteq U_\alpha \text{ for some } \alpha\}$. This function is continuous (by a triangle inequality argument) and positive everywhere on $X$. Since $X$ is compact, $f$ attains its minimum $\lambda = \min_{x \in X} f(x) > 0$. Any set $A$ with $\text{diam}(A) < \lambda$ has, for any $a \in A$, the entire $A \subseteq B(a, \lambda) \subseteq B(a, f(a)) \subseteq U_{\alpha(a)}$. $\blacksquare$

The Lebesgue number lemma is indispensable in the proof that continuous maps from compact metric spaces are uniformly continuous, and in the construction of covering spaces in algebraic topology (where it ensures that any path can be lifted in finitely many steps, each lying within an evenly covered open set).

### The Structure of Connected Components

For general topological spaces, the connected components of $X$ are defined as the maximal connected subsets of $X$. These partition $X$ and are always closed (since the closure of a connected set is connected), but need not be open. The *quasi-components* of $X$ — the equivalence classes of the relation "$x \sim y$ if no clopen set separates $x$ from $y$" — are always closed and always contain the connected components, but can be strictly larger in general spaces. In locally connected spaces, components are both open and closed, and components coincide with quasi-components. This local condition is what makes the structural theory of connectedness tractable for spaces such as manifolds and CW complexes.

---

## 3. High-Performance Optimization & Failure Modes

The practitioner's engagement with connectedness, path-connectedness, and compactness is primarily the work of proof: constructing demonstrations, verifying that hypotheses are satisfied, and anticipating the precise conditions under which theorems fail. This section develops the high-precision technique necessary for this work, with an emphasis on the failure modes that make otherwise plausible arguments collapse.

### Proving Connectedness: Strategy and Pitfalls

The primary technique for proving a space $X$ is connected is to exhibit it as a continuous image of a known connected space (Lemma 3.1), or as a union of connected sets sharing a common point, or as the closure of a connected set.

A common failure mode is attempting to prove connectedness by showing the space is "not obviously separated." The definition requires ruling out every possible separation, not just the ones that come to mind first. The correct approach is to assume a separation exists and derive a contradiction using the specific structure of the space.

Consider $\mathbb{R}^n \setminus \{0\}$ for $n \geq 2$. This space is connected (and in fact path-connected), since any two points can be joined by a path avoiding the origin in $n \geq 2$ dimensions. For $n = 1$, $\mathbb{R} \setminus \{0\} = (-\infty, 0) \cup (0, \infty)$ is not connected — the removal of a single point disconnects it. This dimension-dependence is a fundamental topological invariant: the fact that $\mathbb{R}$ and $\mathbb{R}^n$ for $n \geq 2$ are not homeomorphic follows from the observation that removing a point from $\mathbb{R}$ disconnects it while removing a point from $\mathbb{R}^n$ for $n \geq 2$ does not.

For subsets of $\mathbb{R}^n$, path-connectedness is usually easier to establish directly (by writing down explicit paths) than connectedness via the open cover definition. The standard technique is to verify that the space is *locally path-connected* (every point has arbitrarily small path-connected neighborhoods) and then argue globally. Open connected subsets of $\mathbb{R}^n$ are always path-connected, because local path-connectedness and connectedness together imply path-connectedness.

**Theorem 3.10.** A locally path-connected, connected topological space is path-connected.

*Proof.* Fix $x_0 \in X$ and define $U = \{x \in X : x_0 \text{ and } x \text{ are joined by a path}\}$ and $V = X \setminus U$. We show $U$ and $V$ are both open, which forces $V = \emptyset$ by connectedness (since $x_0 \in U$ so $U \neq \emptyset$).

If $x \in U$, let $\gamma$ be a path from $x_0$ to $x$. Since $X$ is locally path-connected, $x$ has an open path-connected neighborhood $W$. For any $y \in W$, concatenate $\gamma$ with a path in $W$ from $x$ to $y$; then $y \in U$. So $W \subseteq U$, proving $U$ is open.

If $x \in V$, the same local path-connected neighborhood $W$ of $x$ must lie entirely in $V$: if any $y \in W$ were in $U$, we could concatenate a path from $x_0$ to $y$ with a path in $W$ from $y$ to $x$, placing $x$ in $U$. So $W \subseteq V$, proving $V$ is open. $\blacksquare$

### Compactness Arguments: The Finite Subcover Toolkit

The power of compactness lies entirely in the ability to reduce infinite data to finite data. Every proof that uses compactness does so by constructing an open cover tailored to the problem, applying the finite subcover property, and then combining the finitely many local statements into a global conclusion.

The uniform continuity theorem illustrates this cleanly.

**Theorem 3.11.** A continuous function $f: X \to Y$ from a compact metric space to a metric space is uniformly continuous.

*Proof.* Let $\epsilon > 0$. For each $x \in X$, continuity of $f$ at $x$ gives $\delta(x) > 0$ such that $d_X(x, z) < \delta(x) \Rightarrow d_Y(f(x), f(z)) < \epsilon/2$. Consider the open cover $\{B(x, \delta(x)/2) : x \in X\}$ of $X$. By compactness, there exists a finite subcover: $X \subseteq \bigcup_{i=1}^n B(x_i, \delta(x_i)/2)$.

Set $\delta = \min_{i=1}^n \delta(x_i)/2 > 0$ (the minimum is over a finite set, so it is positive). Now suppose $d_X(a, b) < \delta$. Some $x_i$ satisfies $a \in B(x_i, \delta(x_i)/2)$, so $d_X(a, x_i) < \delta(x_i)/2$. Then:

$$d_X(b, x_i) \leq d_X(b, a) + d_X(a, x_i) < \delta + \frac{\delta(x_i)}{2} \leq \frac{\delta(x_i)}{2} + \frac{\delta(x_i)}{2} = \delta(x_i).$$

By choice of $\delta(x_i)$: $d_Y(f(a), f(x_i)) < \epsilon/2$ and $d_Y(f(b), f(x_i)) < \epsilon/2$. The triangle inequality gives $d_Y(f(a), f(b)) < \epsilon$. $\blacksquare$

The structure of this proof is a template: define $\delta(x)$ locally, cover by $B(x, \delta(x)/2)$, extract a finite subcover, take $\delta$ to be the minimum of the finite collection. The factor of $1/2$ is the triangle inequality buffer that allows the finite cover centered at $x_i$ to control points $b$ not originally covered by $B(x_i, \delta(x_i))$ but reached via a point $a$ close to $b$.

### The Failure of Compactness: Recognizing Non-Compact Spaces

Identifying when a space fails to be compact is as important as proving compactness. The standard method is to exhibit an explicit open cover with no finite subcover. The following exhibit a productive catalog of failure modes.

The open interval $(0,1) \subseteq \mathbb{R}$ is not compact: the cover $\{(1/n, 1) : n \geq 2\}$ has no finite subcover, since any finite subcollection $\{(1/n_1, 1), \ldots, (1/n_k, 1)\}$ fails to cover $(0, 1/N]$ for $N = \max(n_1, \ldots, n_k)$. The issue is that $(0,1)$ is not closed; points approach the boundary without reaching it. The cover is designed precisely to expose this boundary behavior.

$\mathbb{R}$ itself is not compact: the cover $\{(-n, n) : n \in \mathbb{N}\}$ has no finite subcover. The issue is that $\mathbb{R}$ is unbounded.

The rational numbers $\mathbb{Q} \cap [0, 1]$ are bounded and not closed in $\mathbb{R}$, hence not compact by Heine-Borel. An explicit cover without a finite subcover can be constructed using the irrationality of $\sqrt{2}/2$: cover each rational $q$ by an open interval not containing $\sqrt{2}/2$, chosen small enough that the intervals have no finite subcover of a sequence of rationals converging to $\sqrt{2}/2$.

In infinite-dimensional spaces, the failure mode is entirely different. Even the closed unit ball $\bar{B} = \{x \in \ell^2 : \|x\| \leq 1\}$ in the Hilbert space $\ell^2$ is not compact, as demonstrated by the orthonormal sequence $e_n$ satisfying $\|e_m - e_n\|_{\ell^2} = \sqrt{2}$ for $m \neq n$, which admits no Cauchy subsequence. The cover $\{B(x, 1/\sqrt{2}) : x \in \bar{B}\}$ has no finite subcover. The lesson is that in infinite-dimensional spaces, the equivalence between closed, bounded, and compact collapses entirely.

### The Tychonoff Theorem and Its Logical Weight

The most powerful compactness theorem in all of general topology is Tychonoff's theorem, which extends compactness from finite products to arbitrary products.

**Theorem 3.12 (Tychonoff).** An arbitrary product $\prod_{\alpha \in A} X_\alpha$ of compact topological spaces is compact in the product topology.

For finite products, Tychonoff's theorem follows from an elementary argument using the tube lemma, which we state and prove for the case of two factors.

**Lemma 3.13 (Tube Lemma).** Let $X$ be compact and $Y$ be any topological space. If $N$ is an open set in $X \times Y$ containing $X \times \{y_0\}$ for some $y_0 \in Y$, then there exists an open set $W \subseteq Y$ with $y_0 \in W$ such that $X \times W \subseteq N$.

*Proof.* For each $x \in X$, since $N$ is open and $(x, y_0) \in N$, there exist open sets $U_x \subseteq X$ and $V_x \subseteq Y$ with $(x, y_0) \in U_x \times V_x \subseteq N$. The sets $\{U_x : x \in X\}$ cover $X$, so by compactness, finitely many suffice: $X \subseteq U_{x_1} \cup \cdots \cup U_{x_n}$. Set $W = V_{x_1} \cap \cdots \cap V_{x_n}$. Then $W$ is open, $y_0 \in W$ (since $y_0 \in V_{x_i}$ for all $i$), and $X \times W \subseteq \bigcup_i (U_{x_i} \times V_{x_i}) \subseteq N$. $\blacksquare$

For infinite products, Tychonoff's theorem requires the axiom of choice — specifically, it is equivalent to the axiom of choice over ZF set theory (a theorem of Kelley, 1950). The standard proof uses Alexander's subbase theorem (a space is compact if every subbase cover has a finite subcover) together with Zorn's lemma. This logical depth gives Tychonoff's theorem a character distinct from the other results of this lesson: it is not simply a theorem about metric spaces or $\mathbb{R}^n$, but a statement about the entire universe of topological spaces whose proof reaches into the foundations of set theory.

### Navigating the Counterexample Landscape

The topology of connectedness and compactness is unusually rich in counterexamples, and mastery of the subject requires familiarity with the standard pathological spaces that expose the limits of intuition. The following are the most important for practitioners.

The *long line* (the one-point compactification of the first uncountable ordinal $\omega_1$ with the order topology) is compact and connected but not second-countable, illustrating that the sequential characterizations of compactness fail without countability assumptions.

The *Cantor set* $C \subseteq [0,1]$ — the intersection of nested closed sets obtained by iteratively removing middle thirds — is compact (as a closed subset of $[0,1]$), totally disconnected (every connected component is a single point), and perfect (every point is a limit point), yet homeomorphic to the product $\{0,1\}^{\mathbb{N}}$ with the product topology. Remarkably, every compact metrizable space is a continuous image of the Cantor set (the Alexandroff-Hausdorff theorem), making $C$ in some sense the "universal" compact metrizable space. This universality is the topological substrate of many constructions in descriptive set theory and in the theory of continuous functions.

The *Warsaw circle* — a quotient of the topologist's sine curve $S$ that closes the gap between the endpoint of the sine curve and the base of the vertical segment — is compact and connected but not locally path-connected, hence not path-connected. It is often used in algebraic topology to demonstrate that the fundamental group and singular homology of a compact connected space can fail to detect the full topology when local connectivity is absent.

The *one-point compactification* $X^+ = X \cup \{\infty\}$ of a locally compact Hausdorff space $X$ provides the essential construction for passing from non-compact to compact spaces: declare the open sets of $X^+$ to be the open sets of $X$ together with sets of the form $(X \setminus K) \cup \{\infty\}$ for $K$ compact in $X$. The resulting space $X^+$ is compact Hausdorff, and $X$ embeds as an open dense subspace. For $X = \mathbb{R}^n$, this gives the $n$-sphere $S^n$; for $X = \mathbb{C}$, it gives the Riemann sphere $S^2$. The one-point compactification is the right tool whenever a proof requires compactness but the natural domain is non-compact — it allows one to work in $X^+$ and then restrict conclusions to $X$.

### Coherence Across the Three Properties

The practitioner's picture of a topological space $X$ should always hold these three properties in view simultaneously. Compactness controls the global finiteness: it ensures continuous functions are bounded, uniformly continuous, and attain their extrema. Connectedness controls the global coherence: it prevents continuous functions from taking two distinct values without passing through every value in between. Path-connectedness controls the geometric coherence: it asserts that the space is traversable, that any two of its points can be reached from one another through a continuous journey within the space.

These three invariants are preserved by homeomorphisms and are therefore topological invariants in the strict sense — if two spaces differ on any of them, they cannot be homeomorphic. They are the first tools one reaches for when classifying topological spaces, the first hypotheses one checks when applying theorems in analysis and algebra, and the first structures one seeks to understand when a new space appears in geometry or logic.

Their interaction is subtle and deep. A space can be compact and connected without being path-connected (the Warsaw circle). It can be path-connected without being compact (any open ball in $\mathbb{R}^n$). It can be compact without being connected (a finite discrete space, or the two-point space $\{0, 1\}$ with the discrete topology). What cannot happen, in a Hausdorff space, is for a space to be compact and have its closed subsets fail to be compact, or for a continuous bijection from a compact space to fail to be a homeomorphism. These rigidities are where the real work of topology lives: in understanding not just what properties a space has, but how those properties constrain every continuous map into or out of the space, every subspace, every quotient, and every product.
