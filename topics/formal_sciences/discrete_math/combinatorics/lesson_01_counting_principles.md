# Lesson 1: Fundamental Counting Principles

## 1. First-Principles Intuition & Invariants

Combinatorics begins with a deceptively simple question: in how many ways can something happen? Before any machinery of generating functions, recurrences, or asymptotic estimates can be deployed, a mathematician must have an airtight account of *why* counting works at all. That account rests on two primitive rules, a proof technique grounded in set bijection, and a theorem about inevitable collisions. Together, these form the axiomatic bedrock on which every edifice of combinatorial reasoning is built.

To appreciate why a formal foundation is necessary, consider the difference between *enumeration by exhaustion* and *enumeration by principle*. A child listing every possible outcome of rolling two dice is performing exhaustion. A mathematician who observes that each of six faces on the first die pairs independently with each of six faces on the second, and concludes without listing anything that there are $6 \times 6 = 36$ outcomes, is applying a principle. That principle, properly stated, is a theorem about the cardinality of Cartesian products of finite sets. The gap between these two approaches is not merely one of efficiency; it is the gap between computation and understanding.

### The Set-Theoretic Foundation

Finite combinatorics is ultimately a theory about finite sets and the functions between them. A *finite set* $A$ has cardinality $|A| = n$ if there exists a bijection $f : A \to \{1, 2, \ldots, n\}$. This definition, grounded in Cantor's general theory of cardinality, anchors every counting argument. When we say "there are $n$ ways to perform a task," we are asserting a bijection between the set of ways to perform that task and the standard set $[n] = \{1, 2, \ldots, n\}$. Counting is, at its core, the construction or verification of such bijections.

This perspective immediately demands precision about what constitutes a "set of outcomes." Two outcomes are distinct if and only if they correspond to distinct elements of the set being counted. Conflating two distinct outcomes or double-counting a single outcome corresponds precisely to failing to maintain the bijection. The combinatorial discipline of careful counting is therefore the discipline of rigorously specifying the set $S$ whose cardinality you want, then finding a structure-preserving map from $S$ to something you already know how to count.

### The Rule of Sum

**Theorem (Rule of Sum).** Let $A$ and $B$ be finite sets with $A \cap B = \emptyset$. Then $|A \cup B| = |A| + |B|$.

This theorem is a direct consequence of the definition of cardinality via bijections. The proof proceeds by explicit construction. Since $|A| = m$, there exists a bijection $f : A \to [m]$. Since $|B| = n$, there exists a bijection $g : B \to [n]$. Define $h : A \cup B \to [m+n]$ by

$$h(x) = \begin{cases} f(x) & \text{if } x \in A \\ g(x) + m & \text{if } x \in B \end{cases}$$

Since $A$ and $B$ are disjoint, every $x \in A \cup B$ falls into exactly one of the two cases, so $h$ is well-defined. To verify injectivity: if $h(x) = h(y)$ and both $x, y \in A$, then $f(x) = f(y)$, so $x = y$ by injectivity of $f$. If both lie in $B$, then $g(x) + m = g(y) + m$, so $g(x) = g(y)$, giving $x = y$ by injectivity of $g$. If $x \in A$ and $y \in B$, then $h(x) = f(x) \le m < m + 1 \le g(y) + m = h(y)$, so $h(x) \ne h(y)$. For surjectivity: any $k \in [m]$ has preimage $f^{-1}(k) \in A$, and any $k \in \{m+1, \ldots, m+n\}$ has preimage $g^{-1}(k - m) \in B$. Thus $h$ is a bijection, confirming $|A \cup B| = m + n$. $\blacksquare$

The generalization to finitely many pairwise-disjoint sets $A_1, A_2, \ldots, A_k$ follows by induction:

$$\left| \bigcup_{i=1}^{k} A_i \right| = \sum_{i=1}^{k} |A_i| \quad \text{whenever } A_i \cap A_j = \emptyset \text{ for all } i \ne j$$

The critical invariant of the rule of sum is *disjointness*. When the sets overlap, the formula overcounts the intersection, which is precisely the error corrected by inclusion-exclusion. The rule of sum is therefore not merely an addition formula; it is a statement that additive decomposition of a counting problem requires a *partition* of the outcome set into mutually exclusive, collectively exhaustive cases.

### The Rule of Product

**Theorem (Rule of Product).** Let $A$ and $B$ be finite sets. Then $|A \times B| = |A| \cdot |B|$.

Here $A \times B = \{(a, b) : a \in A, b \in B\}$ is the Cartesian product. The proof again proceeds by explicit bijection. With $|A| = m$ and $|B| = n$, let $f : A \to [m]$ and $g : B \to [n]$ be bijections. Define $h : A \times B \to [m \times n]$ by

$$h(a, b) = (f(a) - 1) \cdot n + g(b)$$

This is the standard *row-major* encoding of a grid. For injectivity, suppose $h(a_1, b_1) = h(a_2, b_2)$. Then $(f(a_1) - 1) \cdot n + g(b_1) = (f(a_2) - 1) \cdot n + g(b_2)$. Since $1 \le g(b_i) \le n$, we can apply the division algorithm: dividing both sides by $n$ gives the same quotient $f(a_i) - 1$ and the same remainder $g(b_i)$. Therefore $f(a_1) = f(a_2)$ and $g(b_1) = g(b_2)$, which by bijectivity of $f$ and $g$ gives $(a_1, b_1) = (a_2, b_2)$. For surjectivity, any $k \in [mn]$ can be written as $k = qn + r$ with $1 \le r \le n$ and $0 \le q \le m-1$ (adjusting for 1-indexing), and then $(f^{-1}(q+1), g^{-1}(r))$ maps to $k$. Thus $h$ is a bijection, so $|A \times B| = mn$. $\blacksquare$

The geometric intuition is a rectangular grid: $m$ rows, $n$ columns, $mn$ cells. What makes the rule of product more than grid-counting is its interpretation in terms of *sequential independent choices*. When you select an element of $A$ and then, independently of that choice, select an element of $B$, the full set of outcomes is in bijection with $A \times B$. The word "independently" is the crucial invariant: the number of available choices in the second stage must not depend on what was chosen in the first stage. When that dependence exists, the product rule does not apply directly and must be replaced with a sum over stages, which is the combinatorial analogue of the law of total probability.

Generalizing to $k$ sets,

$$|A_1 \times A_2 \times \cdots \times A_k| = \prod_{i=1}^{k} |A_i|$$

by straightforward induction, with the bijection constructed as a generalized mixed-radix encoding. This formula underlies the counts of $k$-tuples, sequences with repetition, and functions between finite sets: the number of functions $f : [k] \to [n]$ is $n^k$, since each of the $k$ independent choices of $f(i)$ ranges over $[n]$.

### Bijective Proofs

A bijective proof of the identity $|A| = |B|$ constructs an explicit bijection $\phi : A \to B$. This technique is both more elegant and more informative than algebraic manipulation of counting formulas: it reveals a *structural correspondence* between two sets that may appear to have nothing in common on the surface.

**Theorem.** The number of subsets of $[n]$ of size $k$ equals the number of subsets of $[n]$ of size $n - k$:

$$\binom{n}{k} = \binom{n}{n-k}$$

*Algebraic proof.* $\binom{n}{n-k} = \dfrac{n!}{(n-k)!\, k!} = \binom{n}{k}$. This is correct but uninformative.

*Bijective proof.* Let $A = \{S \subseteq [n] : |S| = k\}$ and $B = \{S \subseteq [n] : |S| = n - k\}$. Define $\phi : A \to B$ by $\phi(S) = [n] \setminus S$ (the complement of $S$ in $[n]$). Since $|S| = k$, we have $|[n] \setminus S| = n - k$, so $\phi$ maps $A$ into $B$. The map $\phi$ is its own inverse: $\phi(\phi(S)) = [n] \setminus ([n] \setminus S) = S$. An involution is always a bijection. $\blacksquare$

The complement bijection is trivial, but the technique scales to deep identities. Consider the Vandermonde convolution:

$$\binom{m+n}{r} = \sum_{k=0}^{r} \binom{m}{k}\binom{n}{r-k}$$

*Bijective proof.* The left side counts $r$-element subsets of a set $[m+n]$. Partition $[m+n]$ into $M = [m]$ and $N = \{m+1, \ldots, m+n\}$. Any $r$-element subset $S$ of $[m+n]$ satisfies $|S \cap M| = k$ for some $0 \le k \le r$, and consequently $|S \cap N| = r - k$. The choice of $S \cap M$ is a $k$-element subset of $M$ (counted by $\binom{m}{k}$) and $S \cap N$ is an $(r-k)$-element subset of $N$ (counted by $\binom{n}{r-k}$). These two choices are independent and together uniquely determine $S$. Summing over all valid $k$ partitions the set of $r$-element subsets of $[m+n]$ into disjoint cases, giving the identity. $\blacksquare$

The bijective proof does more than verify the formula: it explains *why* it is true by providing a combinatorial decomposition.

### The Pigeonhole Principle

**Theorem (Pigeonhole Principle).** If $n$ objects are distributed into $k$ containers with $n > k$, then at least one container holds at least $\lceil n/k \rceil$ objects. In particular, if $n \ge k + 1$, at least one container holds at least two objects.

*Proof.* Suppose for contradiction that every container holds fewer than $\lceil n/k \rceil$ objects, meaning at most $\lceil n/k \rceil - 1$ objects. The total number of objects is then at most

$$k \cdot \left(\lceil n/k \rceil - 1\right) < k \cdot \frac{n}{k} = n$$

a contradiction since there are exactly $n$ objects. $\blacksquare$

The formal statement in function-theoretic language is cleaner: if $f : A \to B$ is a function with $|A| > |B|$, then $f$ is not injective. Equivalently, there exist $a_1 \ne a_2 \in A$ with $f(a_1) = f(a_2)$.

This theorem is simultaneously trivial and astonishing. Its power lies not in the statement but in the ingenuity with which one defines the objects and containers to solve a specific problem. The principle does not tell you which container is full; it only guarantees that a full container must exist. The craft of applying it lies in finding a mapping from the objects of a problem to a small set of categories such that the existence of a collision in one category yields the desired conclusion.

**Application: Monochromatic Pairs.** Among any 5 points selected from the vertices of a regular hexagon, some two are connected by a diameter (a segment passing through the center). The hexagon has exactly 3 diametrically opposite pairs: $\{v_1, v_4\}, \{v_2, v_5\}, \{v_3, v_6\}$. These 3 pairs are the containers. Five vertices are the objects. By pigeonhole, at least one pair has both of its vertices among the 5 selected, meaning those two vertices are antipodal. $\blacksquare$

**Application: Repeated Decimal.** The decimal expansion of any rational $p/q$ with $\gcd(p, q) = 1$ and $q \ne 0$ eventually repeats with period at most $q$. When performing long division of $p$ by $q$, the remainder at each step lies in $\{0, 1, \ldots, q-1\}$, a set of $q$ values. After at most $q + 1$ steps, by pigeonhole, some remainder must repeat, at which point the decimal pattern cycles. $\blacksquare$

---

## 2. Core Architecture & Mechanics

The practical machinery of combinatorial counting consists of a small set of inference rules applied in sequence to decompose a complex counting problem into subproblems whose cardinalities are known or easily derived. Understanding *how* these rules compose, and under what conditions their application is valid, is the central mechanical skill of discrete mathematics.

### The Decomposition Workflow

Every counting problem has the same high-level structure: you are given a description of a set $S$ (the outcome space), and you must determine $|S|$. The decomposition workflow proceeds as follows.

First, you identify whether the elements of $S$ can be described as *sequences* or *sets*. Sequences (ordered tuples) have more structure and are usually easier to count directly via the product rule. Sets (unordered collections) require accounting for the equivalence classes under permutation, which introduces the factorial correction $k!$ that transforms permutation counts into combination counts.

Second, you check whether a natural *partition* of $S$ exists into cases $S_1, S_2, \ldots, S_r$ such that $S = \bigsqcup_{i} S_i$. If so, the rule of sum reduces the problem to counting each $S_i$ independently. Each $S_i$ may then decompose via the product rule if its elements can be described as independent sequential choices.

Third, you look for a *bijection* from $S$ to a set $T$ whose cardinality is easier to determine. This is the most creative step and often yields the most elegant solutions.

The following diagram illustrates the decision logic of a counting argument as a flow:

```text
Start: Describe the set S explicitly
         |
         v
Is S a Cartesian product A_1 × A_2 × ... × A_k
  with independent stage sizes?
         |
    Yes  |  No
         |   \
         v    v
  Apply Product   Can S be partitioned into
  Rule: |S| =     disjoint S_1, S_2, ..., S_r?
  |A_1|·...·|A_k|       |
                    Yes  |  No
                         |   \
                         v    v
                   Apply Sum   Seek bijection
                   Rule:       φ: S → T where
                   |S| =       |T| is known
                   Σ|S_i|
```

### The Principle of Double Counting

A fundamental technique that exploits both the sum and product rules simultaneously is *double counting*, also called counting in two ways. The strategy is to find a quantity $N$ that counts the edges of a bipartite graph (or more generally, the pairs $(x, y)$ satisfying some relation $R$) and to express $N$ as a sum over one side of the bipartition and also as a sum over the other side.

**Theorem (Handshaking Lemma).** For any finite graph $G = (V, E)$,

$$\sum_{v \in V} \deg(v) = 2|E|$$

*Proof by double counting.* Define the incidence set $I = \{(v, e) : v \in e\}$ of vertex-edge pairs where $v$ is an endpoint of $e$. Counting by vertices: each vertex $v$ contributes $\deg(v)$ pairs, so $|I| = \sum_{v \in V} \deg(v)$. Counting by edges: each edge $e = \{u, v\}$ contributes exactly 2 pairs (one for each endpoint), so $|I| = 2|E|$. Since both expressions count $|I|$, they are equal. $\blacksquare$

This proof is a template. The same argument structure generates the identity $\sum_{k=0}^{n} k \binom{n}{k} = n \cdot 2^{n-1}$ (counting pairs $(k, S)$ where $S \subseteq [n]$, $|S| = k$, and a distinguished element of $S$ is selected, once by summing over $k$ and once by noting each element of $[n]$ appears in $2^{n-1}$ subsets).

### Formalizing the Pigeonhole Argument

The mechanical structure of a pigeonhole argument has three components, each requiring precise specification.

The *objects* are the elements of a set $A$. The *containers* are the elements of a set $B$. The *assignment* is a function $f : A \to B$. The conclusion is that $f$ is not injective when $|A| > |B|$, with the quantitative refinement that some $b \in B$ satisfies $|f^{-1}(b)| \ge \lceil |A| / |B| \rceil$.

The iterative strength of this principle comes from its quantitative form. Define the *load* of container $b$ as $\lambda(b) = |f^{-1}(b)|$. We have $\sum_{b \in B} \lambda(b) = |A|$ by a simple partition argument (the preimage sets $\{f^{-1}(b)\}_{b \in B}$ partition $A$). The average load is $|A| / |B|$. Since the maximum of a collection of nonnegative integers is at least their average, $\max_{b} \lambda(b) \ge |A| / |B|$. Because this maximum is an integer, it is at least $\lceil |A| / |B| \rceil$.

This reasoning extends to the *probabilistic method* in combinatorics, where the existence of a combinatorial object with a desired property is proved by showing that a randomly chosen object has nonnegative expected value of some parameter, hence a deterministic object achieving or exceeding that expectation must exist. The pigeonhole principle is in this sense a deterministic precursor to probabilistic existence arguments.

### Counting Functions, Injections, and Bijections

The following table organizes the counts of maps between finite sets $[m]$ and $[n]$, each following directly from the rules above.

| Map Type | Condition | Count | Derivation |
|---|---|---|---|
| All functions | None | $n^m$ | Product rule: $m$ independent choices from $[n]$ |
| Injections | $m \le n$ | $n^{\underline{m}} = n(n-1)\cdots(n-m+1)$ | Product rule with decreasing options |
| Surjections | $m \ge n$ | $\sum_{k=0}^{n}(-1)^k\binom{n}{k}(n-k)^m$ | Inclusion-exclusion |
| Bijections | $m = n$ | $n!$ | Injections with $m = n$ |

The falling factorial $n^{\underline{m}}$ counts injections because the first element of $[m]$ can map to any of $n$ values, the second to any of the remaining $n - 1$, and so forth, with each stage's option count depending on prior choices in a fully determined way, so the product rule still applies. This is the controlled form of stage-dependence: the *number* of choices decreases by exactly one at each stage, regardless of which specific choice was made.

The surjection count requires inclusion-exclusion because "every element of $[n]$ is hit" is not a constructive condition; it is defined by the absence of unhit elements, which forces an alternating sum over subsets of $[n]$ that are allowed to be unhit.

---

## 3. High-Performance Optimization & Failure Modes

Mastery of these principles requires not only knowing when to apply them but recognizing the failure modes that arise from careless application. Each rule carries an invariant that, when violated, silently produces incorrect counts.

### The Overcounting Trap in the Product Rule

The product rule requires that the sets being multiplied across stages are genuinely independent. A common failure occurs when the stages are described verbally in a way that suggests independence but are actually constrained.

**Example.** How many 5-letter strings over $\{A, B, C, D, E\}$ contain at least one repeated letter?

A naive attempt: "At some position, the letter repeats a previous one. Count the position and the repeated letter." This decomposition is ill-formed because a string with multiple repeated letters gets counted multiple times, once for each repeated letter.

The correct approach uses complementary counting:

$$|\text{strings with at least one repeat}| = |\text{all strings}| - |\text{strings with all distinct letters}|$$

$$= 5^5 - 5! = 3125 - 120 = 3005$$

The complement set (all-distinct strings) is a set of injections from positions to letters, counted by $5^{\underline{5}} = 5!$, while the full set of strings is counted by the product rule as $5^5$. The subtraction is valid because the two complementary sets partition the full set of strings.

### The Undercounting Trap in the Rule of Sum

The rule of sum requires a genuine partition: the cases must be exhaustive (every outcome falls in some case) and mutually exclusive (no outcome falls in two cases simultaneously). A case analysis that leaves a gap undercounts; a case analysis with overlap overcounts.

**Example.** Count integers in $[1, 100]$ divisible by 2 or by 3.

A flawed application: $|\text{div by 2}| + |\text{div by 3}| = 50 + 33 = 83$. This overcounts numbers divisible by both 2 and 3 (i.e., by 6) since those appear in both summands. The correct count applies inclusion-exclusion:

$$|A \cup B| = |A| + |B| - |A \cap B| = 50 + 33 - 16 = 67$$

where $|A \cap B| = \lfloor 100/6 \rfloor = 16$. Inclusion-exclusion is precisely the correction term that repairs the failure of disjointness in the rule of sum.

### The Bijection Validity Requirement

A bijective proof is only valid if the map $\phi$ is demonstrably a bijection. In practice, two checks are required: (1) $\phi$ maps $A$ into $B$ (the image is well-defined and lands in the correct set), and (2) $\phi$ is a bijection (injective and surjective). The cleanest way to establish both simultaneously is to exhibit an explicit two-sided inverse $\psi : B \to A$ such that $\psi \circ \phi = \text{id}_A$ and $\phi \circ \psi = \text{id}_B$; a function with a two-sided inverse is always a bijection.

A common error in bijective proofs is defining a map that depends on an arbitrary choice (such as a canonical ordering) without verifying that the choice does not affect the output. For instance, when proving $\binom{2n}{n} = \sum_{k=0}^{n} \binom{n}{k}^2$ bijectively (via lattice path reflection), one must verify that the reflecting procedure is deterministic and that the intermediate path always crosses the diagonal at the claimed first point.

### Quantitative Pigeonhole and Ramsey-Type Lower Bounds

The quantitative pigeonhole principle provides lower bounds in settings where finding an explicit combinatorial structure is hard. When you can show that if no container holds $\lceil n/k \rceil$ objects then the total object count is strictly less than $n$, you have a contradiction proof that some container must exceed threshold.

**Example: Erdős–Szekeres Theorem.** Any sequence of more than $(r-1)(s-1)$ distinct real numbers contains either an increasing subsequence of length $r$ or a decreasing subsequence of length $s$.

*Proof.* Label each element $a_i$ of the sequence with the pair $(\text{lis}(i), \text{lds}(i))$ where $\text{lis}(i)$ is the length of the longest increasing subsequence ending at $a_i$ and $\text{lds}(i)$ is the length of the longest decreasing subsequence ending at $a_i$. The function $f : [N] \to [(r-1)] \times [(s-1)]$ assigns each position its label. If $N > (r-1)(s-1)$, by pigeonhole, two positions $i < j$ share the same label: $\text{lis}(i) = \text{lis}(j)$ and $\text{lds}(i) = \text{lds}(j)$. If $a_i < a_j$, then $\text{lis}(j) \ge \text{lis}(i) + 1$, a contradiction. If $a_i > a_j$, then $\text{lds}(j) \ge \text{lds}(i) + 1$, also a contradiction. If $a_i = a_j$, the sequence has non-distinct elements, contradicting our assumption. Therefore the labels are all distinct, so $(r-1)(s-1) \ge N$; to avoid this, one of $\text{lis}$ or $\text{lds}$ must exceed its bound, giving the desired subsequence. $\blacksquare$

This proof is a template for a broad class of arguments: assign a label from a small set to each combinatorial object, apply quantitative pigeonhole, derive a contradiction from the collision, and conclude the existence of the desired structure.

### The Interplay of All Four Principles

These four principles do not operate in isolation. A sophisticated counting argument might partition the outcome space via the rule of sum, count each piece via the product rule, verify an intermediate identity via a bijection, and confirm that some extremal structure must exist via pigeonhole. The measure of mastery is not knowing each rule in isolation, but fluency in their simultaneous deployment.

**Problem.** A group of 23 people are in a room. Prove that at least two of them share a birthday (ignoring leap years).

The 23 people are objects, the 365 days of the year are containers, the assignment of birthday to person is the function. Since $23 \le 365$, the basic pigeonhole principle ($n > k$) does not apply. The correct question is: *what is the probability that all 23 have distinct birthdays?* Modeling birthdays as uniform independent draws from $[365]$, the number of ways to assign 23 distinct birthdays is $365^{\underline{23}}$ (injections, counted by the product rule with decreasing stages), and the total number of birthday assignments is $365^{23}$ (all functions, counted by the product rule with constant stages). The probability of all-distinct birthdays is

$$P = \frac{365^{\underline{23}}}{365^{23}} = \prod_{k=0}^{22} \frac{365 - k}{365} \approx 0.4927$$

so the probability that *at least two share a birthday* is approximately $1 - 0.4927 = 0.5073 > 1/2$. This is not a pigeonhole argument in the strict sense; it is a product-rule calculation of the complement. The birthday paradox is a warning against intuition: 23 people give a *better than even chance* of a collision, not because 23 exceeds 365 but because the number of pairs $\binom{23}{2} = 253$ is comfortably large relative to 365.

This problem encapsulates the lesson of the entire chapter. Each principle is easy to state. The craft lies in knowing *which* principle applies to *which* set in a given problem, in constructing the right partition, the right bijection, or the right assignment function, and in verifying the invariants that make each application valid. These skills are not absorbed by reading definitions; they are built by working through the full chain of reasoning until the logical structure of a counting argument becomes second nature.
