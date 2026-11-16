# Lesson 3: Topology of the Real Line — Open Sets, Compactness, Continuity

## 1. First-Principles Intuition & Invariants

The real line $\mathbb{R}$ is far more than a set of numbers. It is a continuum whose structure emerges from three primal forces acting in concert: a linear order $\leq$ that arranges points, a metric $d(x,y) = |x - y|$ that measures distances, and the least-upper-bound property that guarantees no gaps. Every topological notion we develop here — openness, closedness, compactness, connectedness, continuity — can be traced back to these foundations, and understanding the causal chain from order to metric to topology is what separates a mathematician who can compute from one who can reason about why computations succeed or fail.

The fundamental building block is the open ball. For $x \in \mathbb{R}$ and $r > 0$, the open ball of radius $r$ centered at $x$ is the interval $B_r(x) = (x - r, x + r) = \{y \in \mathbb{R} : |x - y| < r\}$. A subset $U \subseteq \mathbb{R}$ is **open** if for every $x \in U$ there exists $r > 0$ such that $B_r(x) \subseteq U$. The intuition is local: every point of an open set has room to move in every direction without leaving the set. A subset $F \subseteq \mathbb{R}$ is **closed** if its complement $\mathbb{R} \setminus F$ is open, which is equivalent to $F$ containing all its limit points — those points $x$ for which every open ball $B_r(x)$ intersects $F$ in some point other than $x$ itself. The two notions are not exhaustive: the half-open interval $[0,1)$ is neither open nor closed, and $\mathbb{R}$ itself is both.

The collection of all open subsets of $\mathbb{R}$, denoted $\tau$, satisfies three axioms that make it a topology. The empty set and $\mathbb{R}$ belong to $\tau$. The union of any family of open sets is open, because each point lies in some member of the family and inherits its surrounding ball. The intersection of finitely many open sets is open: given $U_1, \ldots, U_n$ and a point $x \in \bigcap U_i$, each $U_i$ provides a radius $r_i > 0$ with $B_{r_i}(x) \subseteq U_i$, and $r = \min(r_1, \ldots, r_n) > 0$ yields $B_r(x) \subseteq \bigcap U_i$. The finiteness is essential here. The intersection $\bigcap_{n=1}^{\infty} (-1/n, 1/n) = \{0\}$ is a single point, which is closed, not open. This asymmetry — arbitrary unions preserve openness but only finite intersections do — is the structural signature of a topology, and it propagates through every theorem that follows.

From open sets we derive the two operators that pervade analysis. The **interior** of $E \subseteq \mathbb{R}$, denoted $E^\circ$, is the largest open set contained in $E$, equivalently the union of all open sets contained in $E$. The **closure** $\overline{E}$ is the smallest closed set containing $E$, equivalently the intersection of all closed sets containing $E$. A point $x$ lies in $\overline{E}$ if and only if every neighborhood of $x$ meets $E$, which in $\mathbb{R}$ amounts to: for every $r > 0$, $B_r(x) \cap E \neq \emptyset$. The **boundary** $\partial E = \overline{E} \setminus E^\circ$ consists of points that are limits of both $E$ and its complement. For the interval $(0,1)$, the interior is $(0,1)$ itself, the closure is $[0,1]$, and the boundary is $\{0, 1\}$. These three operators are not merely descriptive; they are the tools by which we test whether a set is open ($E = E^\circ$), closed ($E = \overline{E}$), or neither.

**Connectedness** is the topological property that prevents a set from being split into two separated pieces. A set $E \subseteq \mathbb{R}$ is **connected** if it cannot be written as $E = A \cup B$ where $A$ and $B$ are nonempty, disjoint, and each is open in the subspace topology of $E$. Equivalently, $E$ is connected if the only subsets of $E$ that are simultaneously open and closed in $E$ (clopen) are $\emptyset$ and $E$ itself. On the real line, connectedness has a strikingly concrete characterization.

**Theorem (Connected Subsets of $\mathbb{R}$).** *A subset $E \subseteq \mathbb{R}$ is connected if and only if $E$ is an interval — that is, whenever $a, b \in E$ with $a < b$, the entire segment $[a, b] \subseteq E$.*

*Proof.* We prove both directions.

($\Longleftarrow$) Suppose $E$ is an interval and, for contradiction, $E = A \cup B$ where $A$ and $B$ are nonempty, disjoint, and open in $E$. Pick $a \in A$ and $b \in B$; without loss of generality, $a < b$. Since $E$ is an interval, $[a, b] \subseteq E$. Let $S = \{x \in A : [a, x] \subseteq A\}$, which is nonempty (it contains $a$) and bounded above by $b$. Let $c = \sup S$. Then $a \leq c \leq b$, so $c \in E$.

Since $c$ is the supremum of a subset of $A$, either $c \in A$ or $c$ is a limit point of $A$; in either case $c \in \overline{A} \cap E$. Now consider two cases. If $c \in A$, then since $A$ is open in $E$, there exists $\delta > 0$ such that $(c - \delta, c + \delta) \cap E \subseteq A$. Because $c < b$ (as $b \in B$ and $A \cap B = \emptyset$), we may shrink $\delta$ so that $c + \delta/2 < b$, and since $E$ is an interval, $c + \delta/2 \in E$. Thus $c + \delta/2 \in A$, but $c + \delta/2 > c = \sup S$ and $[a, c + \delta/2] \subseteq A$ (since $[a, c] \subseteq A$ and $(c - \delta, c + \delta) \cap E \subseteq A$), contradicting $c = \sup S$.

If $c \in B$, then since $B$ is open in $E$, there exists $\delta > 0$ with $(c - \delta, c + \delta) \cap E \subseteq B$. But $c = \sup S$ means there exists $x \in S$ with $x > c - \delta$, so $x \in (c - \delta, c + \delta) \cap E \subseteq B$, contradicting $x \in A$ and $A \cap B = \emptyset$. Both cases lead to contradiction, so $E$ is connected.

($\Longrightarrow$) If $E$ is not an interval, there exist $a, b \in E$ with $a < c < b$ and $c \notin E$ for some $c$. Then $E = \bigl(E \cap (-\infty, c)\bigr) \cup \bigl(E \cap (c, \infty)\bigr)$ is a separation into two nonempty disjoint open subsets of $E$, so $E$ is disconnected. $\blacksquare$

This theorem is the bedrock of the Intermediate Value Theorem, which we shall derive as a direct corollary of the fact that continuous images of connected sets are connected. The power of the topological viewpoint is that it replaces the $\varepsilon$-$\delta$ machinery of Bolzano's original proof with a structural argument: intervals are connected, connectedness is preserved by continuous maps, and connected subsets of $\mathbb{R}$ are intervals. The content of the IVT is thus that a continuous function cannot "jump over" a value, because doing so would tear the image into two separated pieces, violating connectedness.

## 2. Core Architecture & Mechanics

### Continuity: The $\varepsilon$-$\delta$ Definition and Sequential Equivalence

The $\varepsilon$-$\delta$ definition of continuity, introduced by Weierstrass in the 1860s, is the precise formalization of the intuitive idea that a continuous function maps nearby inputs to nearby outputs. A function $f: E \to \mathbb{R}$ is **continuous at** $c \in E$ if for every $\varepsilon > 0$ there exists $\delta > 0$ such that for all $x \in E$ with $|x - c| < \delta$, we have $|f(x) - f(c)| < \varepsilon$. The function is **continuous on** $E$ if it is continuous at every point of $E$.

The critical structural feature is that $\delta$ depends on both $\varepsilon$ and the point $c$. This local dependence is what makes pointwise continuity strictly weaker than uniform continuity, a distinction with profound consequences for approximation and integration.

In metric spaces, continuity admits an equivalent sequential formulation that is often more tractable. A function $f: E \to \mathbb{R}$ is **sequentially continuous at** $c \in E$ if for every sequence $(x_n)$ in $E$ with $x_n \to c$, we have $f(x_n) \to f(c)$.

**Theorem (Equivalence of $\varepsilon$-$\delta$ and Sequential Continuity).** *Let $E \subseteq \mathbb{R}$, $f: E \to \mathbb{R}$, and $c \in E$. Then $f$ is continuous at $c$ if and only if $f$ is sequentially continuous at $c$.*

*Proof.* ($\Longrightarrow$) Suppose $f$ is continuous at $c$ and $x_n \to c$ in $E$. Given $\varepsilon > 0$, continuity provides $\delta > 0$ with $|x - c| < \delta \implies |f(x) - f(c)| < \varepsilon$. Since $x_n \to c$, there exists $N \in \mathbb{N}$ such that $|x_n - c| < \delta$ for all $n \geq N$. Then $|f(x_n) - f(c)| < \varepsilon$ for all $n \geq N$, so $f(x_n) \to f(c)$.

($\Longleftarrow$) We prove the contrapositive. Suppose $f$ is not continuous at $c$. Then there exists $\varepsilon_0 > 0$ such that for every $\delta > 0$, there is some $x \in E$ with $|x - c| < \delta$ but $|f(x) - f(c)| \geq \varepsilon_0$. For each $n \in \mathbb{N}$, take $\delta = 1/n$ and choose $x_n \in E$ with $|x_n - c| < 1/n$ and $|f(x_n) - f(c)| \geq \varepsilon_0$. Then $x_n \to c$ but $f(x_n) \not\to f(c)$, so $f$ is not sequentially continuous at $c$. $\blacksquare$

This equivalence is specific to metric spaces (more generally, to first-countable spaces). In general topological spaces, sequential continuity is strictly weaker than continuity. The equivalence is a consequence of $\mathbb{R}$ being first-countable: the topology at each point is generated by a countable neighborhood basis $\{B_{1/n}(c) : n \in \mathbb{N}\}$, which allows us to extract the sequence $(x_n)$ in the proof above.

### Compactness and the Heine-Borel Theorem

Compactness is the topological generalization of finiteness. A subset $K \subseteq \mathbb{R}$ is **compact** if every open cover of $K$ admits a finite subcover: whenever $K \subseteq \bigcup_{\alpha} U_\alpha$ with each $U_\alpha$ open, there exist finitely many indices $\alpha_1, \ldots, \alpha_n$ such that $K \subseteq U_{\alpha_1} \cup \cdots \cup U_{\alpha_n}$. The definition is existential and infinitary — it quantifies over all possible open covers — which makes compactness the subtlest of the topological properties we study. Unlike openness or connectedness, compactness cannot be checked by examining a single neighborhood or a single decomposition; it is a global property of the entire set relative to all possible covers.

The **Heine-Borel Theorem** provides the decisive characterization on $\mathbb{R}$: compactness reduces to the concrete, checkable conditions of closedness and boundedness.

**Theorem (Heine-Borel).** *A subset $K \subseteq \mathbb{R}$ is compact if and only if $K$ is closed and bounded.*

*Proof.* We establish both directions, starting with the easier implications.

**($\Longrightarrow$) Compact implies bounded.** The family $\{(-n, n) : n \in \mathbb{N}\}$ is an open cover of $K$. By compactness, finitely many suffice: $K \subseteq (-n_1, n_1) \cup \cdots \cup (-n_k, n_k) = (-N, N)$ where $N = \max(n_1, \ldots, n_k)$. Thus $K$ is bounded.

**($\Longrightarrow$) Compact implies closed.** We show $\mathbb{R} \setminus K$ is open. Let $x \in \mathbb{R} \setminus K$. For each $y \in K$, set $r_y = |x - y|/2 > 0$. The open balls $U_y = B_{r_y}(y)$ and $V_y = B_{r_y}(x)$ are disjoint by the triangle inequality: if $z \in U_y \cap V_y$, then $|x - y| \leq |x - z| + |z - y| < r_y + r_y = |x - y|$, a contradiction. The family $\{U_y : y \in K\}$ is an open cover of $K$. By compactness, $K \subseteq U_{y_1} \cup \cdots \cup U_{y_n}$ for some $y_1, \ldots, y_n \in K$. Let $V = V_{y_1} \cap \cdots \cap V_{y_n}$, which is an open neighborhood of $x$ (a finite intersection of open sets). We claim $V \cap K = \emptyset$: if $z \in V \cap K$, then $z \in U_{y_i}$ for some $i$, but also $z \in V \subseteq V_{y_i}$, contradicting $U_{y_i} \cap V_{y_i} = \emptyset$. Thus $x$ is an interior point of $\mathbb{R} \setminus K$, so $\mathbb{R} \setminus K$ is open and $K$ is closed.

**($\Longleftarrow$) Closed and bounded implies compact.** This is the substantive direction. We proceed in two stages.

*Stage 1: $[a, b]$ is compact.* Let $\{U_\alpha\}$ be an open cover of $[a, b]$. Define $S = \{x \in [a, b] : [a, x] \text{ is covered by finitely many } U_\alpha\}$. Then $S$ is nonempty (it contains $a$, since $a \in U_{\alpha_0}$ for some $\alpha_0$) and bounded above by $b$. Let $c = \sup S$.

We first show $c \in S$. Since $c \in [a, b]$, there exists $\alpha_0$ with $c \in U_{\alpha_0}$. Since $U_{\alpha_0}$ is open, there exists $\delta > 0$ with $(c - \delta, c + \delta) \subseteq U_{\alpha_0}$. Since $c = \sup S$, there exists $s \in S$ with $s > c - \delta$ (otherwise $c - \delta$ would be an upper bound for $S$). Now $[a, s]$ is covered by finitely many $U_{\alpha_1}, \ldots, U_{\alpha_n}$, and $[s, c] \subseteq (c - \delta, c + \delta) \subseteq U_{\alpha_0}$, so $[a, c] \subseteq U_{\alpha_1} \cup \cdots \cup U_{\alpha_n} \cup U_{\alpha_0}$. Thus $c \in S$.

We now show $c = b$. If $c < b$, then since $(c - \delta, c + \delta) \subseteq U_{\alpha_0}$, we can pick $c' \in [a, b]$ with $c < c' < c + \delta$ and $c' < b$. Then $[a, c'] \subseteq [a, c] \cup (c - \delta, c + \delta) \subseteq U_{\alpha_1} \cup \cdots \cup U_{\alpha_n} \cup U_{\alpha_0}$, so $c' \in S$, contradicting $c = \sup S$. Therefore $c = b$, and $[a, b]$ is covered by finitely many $U_\alpha$.

*Stage 2: General closed and bounded $K$.* Since $K$ is bounded, $K \subseteq [a, b]$ for some $a, b \in \mathbb{R}$. Let $\{U_\alpha\}$ be an open cover of $K$. Since $K$ is closed, $\mathbb{R} \setminus K$ is open. The family $\{U_\alpha\} \cup \{\mathbb{R} \setminus K\}$ is an open cover of $[a, b]$. By Stage 1, finitely many suffice to cover $[a, b]$: $[a, b] \subseteq U_{\alpha_1} \cup \cdots \cup U_{\alpha_n} \cup (\mathbb{R} \setminus K)$ (we may or may not need $\mathbb{R} \setminus K$ in the finite subcover). Intersecting with $K$: $K \subseteq U_{\alpha_1} \cup \cdots \cup U_{\alpha_n}$ (since $K \cap (\mathbb{R} \setminus K) = \emptyset$, any occurrence of $\mathbb{R} \setminus K$ in the finite subcover is redundant for covering $K$). Thus $K$ is compact. $\blacksquare$

The proof of Stage 1 deserves attention for its mechanism. The set $S$ is the locus of "finite coverage so far," and the supremum $c = \sup S$ is the frontier beyond which we have not yet verified finite coverage. The argument shows that this frontier cannot stall: the open set containing $c$ reaches backward to overlap with the region already covered, extending the frontier forward. This is the bisection-free variant of the classical argument, and it is constructive in the sense that it identifies the mechanism (overlap of the covering set at the supremum) rather than relying on a purely existential contradiction.

### The Bolzano-Weierstrass Theorem and Sequential Compactness

An equivalent formulation of compactness in metric spaces is **sequential compactness**: every sequence in $K$ has a subsequence converging to a limit in $K$. The equivalence rests on the **Bolzano-Weierstrass Theorem**.

**Theorem (Bolzano-Weierstrass).** *Every bounded sequence in $\mathbb{R}$ has a convergent subsequence.*

*Proof.* Let $(x_n)$ be bounded, so $x_n \in [a, b]$ for all $n$. We construct a convergent subsequence by successive bisection. Set $[a_0, b_0] = [a, b]$. At step $k$, bisect $[a_k, b_k]$ at $m_k = (a_k + b_k)/2$. At least one half-interval contains infinitely many terms of $(x_n)$; call it $[a_{k+1}, b_{k+1}]$. Choose $n_{k+1} > n_k$ with $x_{n_{k+1}} \in [a_{k+1}, b_{k+1}]$ (possible because the interval contains infinitely many terms). Then $b_k - a_k = (b - a)/2^k \to 0$, and for $j \geq k$, both $x_{n_j}$ and $x_{n_k}$ lie in $[a_k, b_k]$, so $|x_{n_j} - x_{n_k}| \leq (b - a)/2^k$. Thus $(x_{n_k})$ is Cauchy, and by the completeness of $\mathbb{R}$, it converges. $\blacksquare$

From this, closed and bounded $K$ is sequentially compact: any sequence in $K$ is bounded (hence has a convergent subsequence by Bolzano-Weierstrass), and the limit lies in $K$ because $K$ is closed. The equivalence of sequential compactness and cover compactness in metric spaces follows from a more general argument involving total boundedness and the Lebesgue number lemma, which we develop below.

### The Lebesgue Number Lemma

The Lebesgue number lemma is the technical device that connects open covers to uniform local behavior, and it is the key to proving that continuous functions on compact sets are uniformly continuous.

**Theorem (Lebesgue Number Lemma).** *Let $K \subseteq \mathbb{R}$ be compact and $\{U_\alpha\}$ an open cover of $K$. There exists $\delta > 0$ (a Lebesgue number) such that every subset of $K$ with diameter less than $\delta$ is contained in some single $U_\alpha$.*

*Proof.* For each $x \in K$, there exists $\alpha(x)$ with $x \in U_{\alpha(x)}$. Since $U_{\alpha(x)}$ is open, there exists $r_x > 0$ with $B_{r_x}(x) \subseteq U_{\alpha(x)}$. The family $\{B_{r_x/2}(x) : x \in K\}$ is an open cover of $K$. By compactness, finitely many suffice: $K \subseteq B_{r_{x_1}/2}(x_1) \cup \cdots \cup B_{r_{x_n}/2}(x_n)$. Set $\delta = \min(r_{x_1}/2, \ldots, r_{x_n}/2) > 0$.

Let $S \subseteq K$ with $\operatorname{diam}(S) < \delta$. Pick any $s \in S$; then $s \in B_{r_{x_i}/2}(x_i)$ for some $i$. For any $t \in S$, $|t - x_i| \leq |t - s| + |s - x_i| < \delta + r_{x_i}/2 \leq r_{x_i}/2 + r_{x_i}/2 = r_{x_i}$. Thus $S \subseteq B_{r_{x_i}}(x_i) \subseteq U_{\alpha(x_i)}$. $\blacksquare$

### Continuous Images of Compact and Connected Sets

Two preservation theorems form the backbone of the classical results. Both state that continuous functions preserve a topological property in their image.

**Theorem (Continuous Image of Compact is Compact).** *If $K \subseteq \mathbb{R}$ is compact and $f: K \to \mathbb{R}$ is continuous, then $f(K)$ is compact.*

*Proof.* Let $\{V_\beta\}$ be an open cover of $f(K)$. Since $f$ is continuous, each $f^{-1}(V_\beta)$ is open in $K$ (in the subspace topology), and $\{f^{-1}(V_\beta)\}$ covers $K$. By compactness, finitely many suffice: $K \subseteq f^{-1}(V_{\beta_1}) \cup \cdots \cup f^{-1}(V_{\beta_n})$. Applying $f$: $f(K) \subseteq V_{\beta_1} \cup \cdots \cup V_{\beta_n}$. $\blacksquare$

**Theorem (Continuous Image of Connected is Connected).** *If $E \subseteq \mathbb{R}$ is connected and $f: E \to \mathbb{R}$ is continuous, then $f(E)$ is connected.*

*Proof.* Suppose $f(E) = A \cup B$ where $A, B$ are disjoint nonempty open subsets of $f(E)$. Then $f^{-1}(A)$ and $f^{-1}(B)$ are open in $E$ (by continuity), disjoint, nonempty, and cover $E$. This contradicts $E$ being connected. $\blacksquare$

### The Intermediate Value Theorem

**Theorem (Intermediate Value Theorem).** *Let $f: [a, b] \to \mathbb{R}$ be continuous with $f(a) < f(b)$, and let $v$ satisfy $f(a) < v < f(b)$. Then there exists $c \in (a, b)$ with $f(c) = v$.*

*Proof (via connectedness).* The interval $[a, b]$ is connected. Since $f$ is continuous, $f([a, b])$ is connected, hence an interval. Since $f(a), f(b) \in f([a,b])$ and $f(a) < v < f(b)$, the interval $f([a,b])$ contains $v$, so there exists $c \in [a, b]$ with $f(c) = v$. Since $f(a) \neq v$ and $f(b) \neq v$, we have $c \in (a, b)$. $\blacksquare$

*Proof (constructive, via bisection).* This proof produces an algorithm that locates $c$ to arbitrary precision. Set $a_0 = a$, $b_0 = b$, maintaining the invariant $f(a_n) < v < f(b_n)$. Given $[a_n, b_n]$, let $m_n = (a_n + b_n)/2$. If $f(m_n) = v$, we are done. If $f(m_n) < v$, set $[a_{n+1}, b_{n+1}] = [m_n, b_n]$. If $f(m_n) > v$, set $[a_{n+1}, b_{n+1}] = [a_n, m_n]$. In either case, $f(a_{n+1}) < v < f(b_{n+1})$ and $b_{n+1} - a_{n+1} = (b - a)/2^{n+1}$.

The nested intervals $[a_n, b_n]$ satisfy $b_n - a_n \to 0$, so by the Nested Interval Property, $\bigcap_{n=0}^{\infty} [a_n, b_n] = \{c\}$ for a unique $c \in [a, b]$. Both $a_n \to c$ and $b_n \to c$. By continuity, $f(a_n) \to f(c)$ and $f(b_n) \to f(c)$. Since $f(a_n) < v$ for all $n$, $f(c) \leq v$. Since $f(b_n) > v$ for all $n$, $f(c) \geq v$. Therefore $f(c) = v$. Moreover, $b_n - a_n = (b - a)/2^n$, so after $n$ steps the root is localized to an interval of length $(b - a)/2^n$, giving exponential convergence. $\blacksquare$

The bisection proof is not merely an alternative; it is a computational procedure. Given a tolerance $\varepsilon$, the number of iterations required to guarantee $|c_n - c| < \varepsilon$ is $\lceil \log_2((b - a)/\varepsilon) \rceil$. For $[a, b] = [0, 1]$ and $\varepsilon = 10^{-16}$ (double precision), this requires 54 iterations — a remarkably small number for such a stringent tolerance, and a direct consequence of the exponential contraction $2^{-n}$.

### The Extreme Value Theorem

**Theorem (Extreme Value Theorem).** *If $f: K \to \mathbb{R}$ is continuous and $K$ is compact, then $f$ attains its supremum and infimum on $K$. That is, there exist $c_{\max}, c_{\min} \in K$ with $f(c_{\max}) = \sup_{x \in K} f(x)$ and $f(c_{\min}) = \inf_{x \in K} f(x)$.*

*Proof.* Since $K$ is compact and $f$ is continuous, $f(K)$ is compact, hence closed and bounded. Boundedness ensures $M = \sup f(K)$ exists as a finite real number. Since $f(K)$ is closed and $M$ is a limit point of $f(K)$ (as the supremum of a bounded set is either a maximum or a limit point), $M \in f(K)$. Thus there exists $c_{\max} \in K$ with $f(c_{\max}) = M$. The argument for the infimum is symmetric. $\blacksquare$

The EVT is the theoretical guarantee that optimization problems over compact domains have solutions. Without compactness, the supremum may exist but remain unattainable: $f(x) = x$ on $(0, 1)$ has $\sup = 1$ but no point in the domain achieves it. The failure is attributable to the domain not being closed — the limit point $x = 1$ where the supremum would be achieved is excluded.

### Uniform Continuity on Compact Sets

A function $f: E \to \mathbb{R}$ is **uniformly continuous** on $E$ if for every $\varepsilon > 0$ there exists $\delta > 0$ such that for all $x, y \in E$, $|x - y| < \delta \implies |f(x) - f(y)| < \varepsilon$. The defining feature is that $\delta$ depends only on $\varepsilon$, not on the location. Uniform continuity is a global property; pointwise continuity is a local one. Every uniformly continuous function is continuous, but the converse requires compactness.

**Theorem (Uniform Continuity on Compact Sets).** *If $K \subseteq \mathbb{R}$ is compact and $f: K \to \mathbb{R}$ is continuous, then $f$ is uniformly continuous on $K$.*

*Proof (via Lebesgue number).* Given $\varepsilon > 0$, for each $x \in K$ there exists $\delta_x > 0$ such that $|y - x| < \delta_x \implies |f(y) - f(x)| < \varepsilon/2$. The open cover $\{B_{\delta_x/2}(x) : x \in K\}$ has a Lebesgue number $\delta > 0$ by the Lebesgue Number Lemma. Now if $x, y \in K$ with $|x - y| < \delta$, the set $\{x, y\}$ has diameter less than $\delta$, so both points lie in some $B_{\delta_{x_0}/2}(x_0)$. Then $|x - x_0| < \delta_{x_0}/2 < \delta_{x_0}$, so $|f(x) - f(x_0)| < \varepsilon/2$, and similarly $|f(y) - f(x_0)| < \varepsilon/2$. By the triangle inequality, $|f(x) - f(y)| \leq |f(x) - f(x_0)| + |f(x_0) - f(y)| < \varepsilon/2 + \varepsilon/2 = \varepsilon$. $\blacksquare$

*Proof (via sequential compactness, by contradiction).* Suppose $f$ is continuous on compact $K$ but not uniformly continuous. Then there exists $\varepsilon_0 > 0$ such that for every $\delta > 0$, there exist $x, y \in K$ with $|x - y| < \delta$ but $|f(x) - f(y)| \geq \varepsilon_0$. Taking $\delta = 1/n$, we obtain sequences $(x_n), (y_n)$ in $K$ with $|x_n - y_n| < 1/n$ and $|f(x_n) - f(y_n)| \geq \varepsilon_0$. Since $K$ is sequentially compact, $(x_n)$ has a convergent subsequence $x_{n_k} \to x^* \in K$. Then $|y_{n_k} - x^*| \leq |y_{n_k} - x_{n_k}| + |x_{n_k} - x^*| < 1/n_k + |x_{n_k} - x^*| \to 0$, so $y_{n_k} \to x^*$ as well. By continuity, $f(x_{n_k}) \to f(x^*)$ and $f(y_{n_k}) \to f(x^*)$, so $|f(x_{n_k}) - f(y_{n_k})| \to 0$, contradicting $|f(x_{n_k}) - f(y_{n_k})| \geq \varepsilon_0$ for all $k$. $\blacksquare$

Both proofs illuminate different aspects. The Lebesgue number proof is constructive: it shows how to extract a uniform $\delta$ from the open cover, and the mechanism is the Lebesgue number — a positive lower bound on the "reach" of the cover. The sequential proof is by contradiction and leverages Bolzano-Weierstrass; its mechanism is that failure of uniform continuity produces pairs of sequences that converge to the same limit yet maintain separated function values, which continuity forbids.

## 3. High-Performance Optimization & Failure Modes

### The Cost of Non-Compactness: A Catalogue of Failures

Every theorem in Section 2 requires compactness or connectedness, and the failures when these hypotheses are dropped are not merely theoretical curiosities — they are the exact points where numerical algorithms break down, where optimization fails to converge, and where approximation theory must introduce corrections.

**Failure of the Extreme Value Theorem on non-closed domains.** The function $f(x) = x$ on $(0, 1)$ is continuous and bounded with $\sup f = 1$ and $\inf f = 0$, but neither value is attained. The domain $(0, 1)$ is bounded but not closed. The supremum and infimum are limit values at the excluded boundary points. In practice, this means that an optimization routine searching for the maximum of $f(x) = x$ on $(0, 1)$ will approach $1$ asymptotically but never reach it, and any termination criterion based on $|f(x_n) - \sup f| < \varepsilon$ will require an understanding of the convergence rate that the problem structure does not inherently provide.

**Failure of the Extreme Value Theorem on unbounded domains.** The function $f(x) = x^2$ on $\mathbb{R}$ is continuous but unbounded above; $\sup f = +\infty$ and no maximum exists. On $[0, \infty)$, the function $f(x) = 1/(x + 1)$ is continuous and bounded with $\sup f = 1$ (attained at $x = 0$) and $\inf f = 0$ (not attained). The domain is closed but not bounded, and the infimum escapes to infinity.

**Failure of uniform continuity on non-compact domains.** The function $f(x) = 1/x$ on $(0, 1]$ is continuous but not uniformly continuous. To see this, take $x_n = 1/n$ and $y_n = 1/(n+1)$. Then $|x_n - y_n| = 1/(n(n+1)) \to 0$, but $|f(x_n) - f(y_n)| = |n - (n+1)| = 1$, which does not converge to $0$. No single $\delta$ can control the variation of $f$ across the entire domain, because the derivative $f'(x) = -1/x^2$ grows without bound as $x \to 0^+$. The function "oscillates" (in the sense of having unbounded local variation) near the excluded limit point $0$.

The function $f(x) = x^2$ on $\mathbb{R}$ is another example. Take $x_n = n + 1/n$ and $y_n = n$. Then $|x_n - y_n| = 1/n \to 0$ but $|f(x_n) - f(y_n)| = |n^2 + 2 + 1/n^2 - n^2| = 2 + 1/n^2 \to 2 \neq 0$. The domain is closed but unbounded, and the failure of uniform continuity is due to the unbounded growth of the derivative. A continuous function on a non-compact domain is uniformly continuous if and only if its modulus of continuity $\omega(\delta) = \sup\{|f(x) - f(y)| : x, y \in E, |x - y| \leq \delta\}$ satisfies $\omega(\delta) \to 0$ as $\delta \to 0^+$, a condition that is automatic on compact domains but must be checked by hand otherwise.

**Failure of the Intermediate Value Theorem on disconnected domains.** The function $f: \{-1\} \cup \{1\} \to \mathbb{R}$ defined by $f(-1) = -1, f(1) = 1$ is continuous (the domain is discrete, so every function is continuous), but $f$ never takes the value $0$ despite $f(-1) < 0 < f(1)$. The domain is disconnected. More subtly, $f: [0, 1] \cup [2, 3] \to \mathbb{R}$ defined by $f(x) = 0$ on $[0, 1]$ and $f(x) = 1$ on $[2, 3]$ is continuous on each piece but jumps over the interval $(0, 1)$ without taking intermediate values, because the domain has a gap.

### Pathologies in Continuity: Thomae's Function and the Dirichlet Function

Two classical examples test the boundaries of the $\varepsilon$-$\delta$ definition.

The **Dirichlet function** $D: \mathbb{R} \to \mathbb{R}$, defined by $D(x) = 1$ if $x \in \mathbb{Q}$ and $D(x) = 0$ if $x \notin \mathbb{Q}$, is discontinuous at every point. For any $c$ and any $\delta > 0$, the ball $B_\delta(c)$ contains both rational and irrational points, so $|D(x) - D(c)| = 1$ for points of the opposite type. No $\delta$ can make $|D(x) - D(c)| < 1/2$ for all $x$ near $c$. This function is not Riemann integrable on any interval.

**Thomae's function** $T: \mathbb{R} \to \mathbb{R}$, defined by $T(x) = 0$ if $x$ is irrational and $T(p/q) = 1/q$ for rational $x = p/q$ in lowest terms with $q > 0$, is continuous at every irrational and discontinuous at every rational. At an irrational $c$, for any $\varepsilon > 0$, there are only finitely many rationals $p/q$ in $[c - 1, c + 1]$ with $q \leq 1/\varepsilon$ (since for each $q$, there are at most $2q + 1$ such rationals, and $q$ ranges over a finite set). Let $\delta$ be the minimum distance from $c$ to these finitely many rationals; then $|x - c| < \delta$ implies either $x$ is irrational (so $|T(x) - T(c)| = 0 < \varepsilon$) or $x = p/q$ with $q > 1/\varepsilon$ (so $|T(x) - T(c)| = 1/q < \varepsilon$). At a rational $c = p/q$, every neighborhood contains irrationals where $T = 0$, so $|T(x) - T(c)| = 1/q$ for irrational $x$ near $c$, which cannot be made small. Thomae's function illustrates that the set of continuity points of a function can be a proper, dense, uncountable subset (the irrationals) while the discontinuity set is also dense (the rationals). By a theorem of Lebesgue, the set of discontinuities of any real-valued function is an $F_\sigma$ set (a countable union of closed sets), and the rationals $\mathbb{Q}$ are indeed $F_\sigma$.

### The Topologist's Sine Curve: Connected but Not Path-Connected

The set $S = \{(x, \sin(1/x)) : 0 < x \leq 1\} \cup \{(0, y) : -1 \leq y \leq 1\}$ in $\mathbb{R}^2$ is a standard example showing that connectedness does not imply path-connectedness. The graph $\{(x, \sin(1/x)) : x > 0\}$ is connected (it is the continuous image of the connected set $(0, 1]$), and its closure includes the vertical segment $\{0\} \times [-1, 1]$. The closure of a connected set is connected, so $S$ is connected. However, there is no continuous path from a point on the vertical segment to a point on the graph, because $\sin(1/x)$ oscillates infinitely as $x \to 0^+$, and any continuous path would need to realize a continuous parametrization of this oscillation, which is impossible. This example, while in $\mathbb{R}^2$, motivates the care needed when generalizing from $\mathbb{R}$ to higher dimensions: in $\mathbb{R}$, connectedness and path-connectedness coincide (both characterize intervals), but this equivalence does not persist.

### Generalization Pitfalls: Beyond the Real Line

The Heine-Borel theorem characterizes compactness as "closed and bounded," but this characterization is specific to $\mathbb{R}^n$ with the Euclidean metric. In general metric spaces, closed and bounded does not imply compact. The closed unit ball in an infinite-dimensional normed space — for instance, in $\ell^2$, the space of square-summable sequences — is closed and bounded but not compact. The sequence $e_n = (0, \ldots, 0, 1, 0, \ldots)$ (the $n$-th standard basis vector) lies in the closed unit ball, but $|e_n - e_m| = \sqrt{2}$ for $n \neq m$, so no subsequence is Cauchy. Compactness in infinite-dimensional spaces requires a stronger condition (total boundedness), and the failure of Heine-Borel is the reason that functional analysis must develop more delicate tools — weak topologies, Arzelà-Ascoli for function spaces, and the Banach-Alaoglu theorem for dual spaces.

Even in finite dimensions, the metric matters. In the discrete metric $d(x, y) = 1$ for $x \neq y$ on $\mathbb{R}$, the closed unit ball $\overline{B_1(0)} = \{x : d(x, 0) \leq 1\} = \mathbb{R}$ is closed and bounded but not compact (the open cover $\{B_{1/2}(x) : x \in \mathbb{R}\} = \{\{x\} : x \in \mathbb{R}\}$ has no finite subcover). The Heine-Borel characterization depends on the Euclidean metric, or more precisely, on a metric whose topology coincides with the order topology on $\mathbb{R}$.

### Computational Consequences and Practical Synthesis

The theorems of this lesson are not merely structural results; they are the guarantees that make numerical analysis possible. The Intermediate Value Theorem, through its bisection proof, gives a root-finding algorithm with guaranteed convergence at the rate $|b_n - a_n| = (b - a) \cdot 2^{-n}$, halving the search interval at each step. The Extreme Value Theorem guarantees that optimization over a compact set has a solution, which is the theoretical foundation of every global optimization algorithm. Uniform continuity on compact sets guarantees that a continuous function can be approximated by its values on a finite grid: if $f$ is uniformly continuous on $K$ with modulus $\omega(\delta)$, then sampling $f$ at points spaced $\delta$ apart and interpolating (or taking the nearest value) approximates $f$ to within $\omega(\delta)$. The Weierstrass Approximation Theorem — every continuous function on $[a, b]$ can be uniformly approximated by polynomials — depends on compactness for the uniform approximation, and its proof (via Bernstein polynomials) is a constructive embodiment of the EVT and uniform continuity working in concert.

The synthesis is this: compactness replaces the infinite with the finite, ensuring that local properties (continuity) become global ones (uniform continuity, attainment of extrema), and that coverings by infinitely many sets can be reduced to finitely many. Connectedness replaces the discrete with the continuous, ensuring that intermediate values are achieved and that the image of a continuous function cannot be torn apart. On the real line, these two properties are characterized by elementary conditions — closed-and-bounded for compactness, interval-ness for connectedness — but the theorems themselves, and the proofs that establish them, reveal the deep mechanism: the completeness of $\mathbb{R}$, the convergence of Cauchy sequences, the existence of suprema, and the interplay between order, metric, and topology that makes $\mathbb{R}$ the unique complete ordered field. Every generalization to higher dimensions, to function spaces, or to abstract topological spaces must confront the question of which of these mechanisms persist and which must be replaced by new structures.
