# Lesson 3: Combinatorics, Counting Principles, Generating Functions

## 1. First-Principles Intuition & Invariants

Combinatorics is the discipline of counting without enumerating. When we ask how many objects satisfy a given property, the naive approach—list every object and tally—collides with combinatorial explosion almost immediately. A deck of fifty-two cards admits $52! \approx 8.07 \times 10^{67}$ permutations, a number far exceeding the count of atoms in the observable universe. The combinatorialist's task is to replace enumeration with structural reasoning: to find the algebraic or recursive pattern that the counting problem obeys, and to exploit that pattern to arrive at a closed form, a recurrence, or a generating function that encodes the answer.

The entire edifice rests on a small number of counting principles that function as axioms for the discipline. The most fundamental is the **Sum Rule**: if a set $A$ can be partitioned into $k$ pairwise disjoint subsets $A_1, A_2, \ldots, A_k$, then $|A| = |A_1| + |A_2| + \cdots + |A_k|$. This is a direct consequence of finite set cardinality being a measure-theoretic quantity respecting disjoint unions. The dual principle is the **Product Rule**: if a procedure consists of $k$ sequential stages, where stage $i$ can be completed in $n_i$ ways regardless of the choices made in prior stages, then the total number of outcomes is $n_1 \cdot n_2 \cdots n_k$. Formally, this is the statement $|A_1 \times A_2 \times \cdots \times A_k| = |A_1| \cdot |A_2| \cdots |A_k|$, the multiplicativity of cardinality under Cartesian products.

These two rules seem trivially simple, yet they generate the entire combinatorial zoo when combined with symmetry constraints. The moment we impose that certain positions are indistinguishable, or that selections must satisfy an ordering constraint, or that repetitions are allowed or forbidden, we branch into the classical counting formulas. The art lies not in memorizing the resulting formulas but in recognizing which structural decomposition—sum, product, or their recursive interplay—maps to the problem at hand. A practitioner who internalizes the sum and product rules as decomposition tools can derive every standard formula from scratch, which is the only reliable way to apply combinatorics under the pressure of a novel problem.

The **Pigeonhole Principle** occupies a special epistemological niche. It is the only counting principle that proves *existence* without *construction*: if $n + 1$ objects are placed into $n$ boxes, at least one box contains two or more objects. The principle extends to its generalized form: if $N$ objects are placed into $k$ boxes, then some box contains at least $\lceil N / k \rceil$ objects. What makes this principle powerful is not its statement— which is obvious to the point of self-evidence—but the ingenuity required in its application. The challenge is always the same: identify what plays the role of "objects" and what plays the role of "boxes," and verify that the arithmetic forces a collision. In the most elegant applications, the mapping from problem domain to pigeonhole structure is deeply non-obvious.

The core invariant that unifies all of combinatorics is **bijective proof**. Two sets have the same cardinality if and only if a bijection exists between them. This is not merely a theoretical observation; it is the most powerful problem-solving tool in the combinatorialist's arsenal. When a direct count is difficult, one seeks a bijection to a set whose cardinality is known or easier to compute. The binomial coefficient $\binom{n}{k}$, for instance, can be counted by the product rule (choose $k$ items from $n$ in order, then divide by $k!$ for overcounting), but it can also be understood as the number of lattice paths from $(0,0)$ to $(n-k, k)$ using right and up steps—a bijection that transforms a selection problem into a path-counting problem, connecting combinatorics to graph theory and probability in a single move.

## 2. Core Architecture & Mechanics

### 2.1 Permutations and Arrangements

A **permutation** of a finite set $S$ with $|S| = n$ is an ordered arrangement of its elements. The number of permutations is given by the falling factorial:

$$P(n, n) = n! = n \cdot (n-1) \cdot (n-2) \cdots 2 \cdot 1$$

The derivation proceeds directly from the Product Rule. We fill $n$ positions sequentially. The first position can be filled in $n$ ways (any element of $S$). Having chosen one element, the second position is filled in $n - 1$ ways. The third in $n - 2$ ways, and so on, until the final position offers only one remaining choice. The product $n \cdot (n-1) \cdots 1 = n!$ is the result.

More generally, a **$k$-permutation** is an ordered arrangement of $k$ elements selected from $n$ distinct elements. The count is the falling factorial:

$$P(n, k) = n^{\underline{k}} = \frac{n!}{(n-k)!} = n \cdot (n-1) \cdot (n-2) \cdots (n-k+1)$$

where $n^{\underline{k}}$ denotes the falling factorial notation. The Product Rule applies identically: $k$ sequential choices, the first from $n$ options, the second from $n-1$, and so forth down to $n - k + 1$.

When elements are not all distinct, the count changes dramatically. Consider permutations of the multiset $\{a, a, a, b, b, c\}$, which contains $n_1 = 3$ copies of $a$, $n_2 = 2$ copies of $b$, and $n_3 = 1$ copy of $c$, with total size $n = 6$. The number of distinct permutations is:

$$\frac{n!}{n_1! \cdot n_2! \cdots n_k!} = \frac{6!}{3! \cdot 2! \cdot 1!} = \frac{720}{12} = 60$$

The proof is instructive and relies on the Product Rule combined with a division argument. Suppose all $n$ elements were labeled distinctly: $a_1, a_2, a_3, b_1, b_2, c$. There would be $n! = 720$ permutations. But the labels on the three $a$'s are artificial; any permutation of $a_1, a_2, a_3$ among the $a$-positions yields the same unlabeled arrangement, so we divide by $3! = 6$. Similarly, the two $b$-labels can be permuted in $2! = 2$ ways without changing the unlabeled arrangement. The division by $n_1! \cdot n_2! \cdots n_k!$ corrects for this overcounting.

A **$k$-combination** is an unordered selection of $k$ elements from $n$ distinct elements. The formula is:

$$\binom{n}{k} = \frac{n!}{k!(n-k)!} = \frac{n^{\underline{k}}}{k!}$$

The derivation: count ordered $k$-selections via the Product Rule to get $n^{\underline{k}} = \frac{n!}{(n-k)!}$. Each unordered subset of size $k$ corresponds to exactly $k!$ ordered selections (one for each permutation of its elements). Dividing by $k!$ yields $\binom{n}{k}$.

When repetition is allowed, the counting problem shifts. The number of **combinations with repetition**—selecting $k$ items from $n$ types, where each type can be chosen multiple times—is:

$$\binom{n + k - 1}{k} = \binom{n + k - 1}{n - 1}$$

The proof uses a stars-and-bars bijection. Represent a selection of $k$ items from $n$ types as a sequence of $k$ stars (the items) separated by $n - 1$ bars (the dividers between types). For example, selecting $k = 7$ items from $n = 4$ types might look like $\star\star|\star\star\star||\star\star$, meaning two of type 1, three of type 2, zero of type 3, and two of type 4. The total number of symbols is $k + (n-1) = k + n - 1$, and we choose which $k$ positions are stars (equivalently, which $n - 1$ are bars), giving $\binom{n + k - 1}{k}$.

The following table summarizes the four canonical counting models, distinguished by whether order matters and whether repetition is allowed:

| Model | Order Matters? | Repetition? | Formula |
|---|---|---|---|
| $k$-permutation | Yes | No | $\dfrac{n!}{(n-k)!}$ |
| $k$-permutation with rep. | Yes | Yes | $n^k$ |
| $k$-combination | No | No | $\dfrac{n!}{k!(n-k)!}$ |
| $k$-combination with rep. | No | Yes | $\dbinom{n+k-1}{k}$ |

The formula $n^k$ for permutations with repetition is the simplest: each of $k$ positions is filled independently from $n$ choices, so the Product Rule gives $n \cdot n \cdots n = n^k$ directly.

### 2.2 The Pigeonhole Principle: Constructive Applications

The pigeonhole principle's power emerges in problems where a direct combinatorial count is intractable but a structural guarantee can be forced by counting constraints. Consider a classic application: in any set of $n + 1$ integers chosen from $\{1, 2, \ldots, 2n\}$, at least two must be coprime (share no common factor greater than 1).

The proof assigns pigeonholes by consecutive pairs: $\{1, 2\}, \{3, 4\}, \ldots, \{2n-1, 2n\}$, yielding $n$ boxes. By the pigeonhole principle, selecting $n + 1$ numbers forces at least two into the same pair. Consecutive integers are always coprime (since $\gcd(m, m+1) = 1$ for any integer $m$, because any common divisor divides their difference, which is 1), so those two numbers are coprime. The structural insight—pairing consecutive integers—transforms an existence claim into an immediate pigeonhole argument.

A deeper application proves that in any sequence of $n^2 + 1$ distinct real numbers, there exists either an increasing subsequence of length $n + 1$ or a decreasing subsequence of length $n + 1$ (Erdős–Szekeres theorem). Assign to each element $a_i$ in the sequence the pair $(u_i, d_i)$, where $u_i$ is the length of the longest increasing subsequence ending at $a_i$ and $d_i$ is the length of the longest decreasing subsequence ending at $a_i$. If no increasing subsequence has length $n + 1$ and no decreasing subsequence has length $n + 1$, then $u_i \in \{1, \ldots, n\}$ and $d_i \in \{1, \ldots, n\}$, giving at most $n^2$ distinct pairs. But there are $n^2 + 1$ elements, so by pigeonhole, two elements $a_i$ and $a_j$ (with $i < j$) share the same pair $(u_i, d_i) = (u_j, d_j)$. If $a_i < a_j$, then appending $a_j$ to the longest increasing subsequence ending at $a_i$ gives a subsequence of length $u_i + 1 = u_j + 1 > u_j$, contradicting the definition of $u_j$. If $a_i > a_j$, the analogous argument applies to the decreasing subsequence. Either way, a contradiction arises, so one of the two long subsequences must exist.

### 2.3 The Principle of Inclusion-Exclusion

The Sum Rule requires disjoint sets. When sets overlap, direct addition overcounts. The **Principle of Inclusion-Exclusion (PIE)** corrects for overlapping unions. For two sets:

$$|A \cup B| = |A| + |B| - |A \cap B|$$

The subtraction of $|A \cap B|$ compensates for the elements counted in both $|A|$ and $|B|$. For three sets, the pattern extends:

$$|A \cup B \cup C| = |A| + |B| + |C| - |A \cap B| - |A \cap C| - |B \cap C| + |A \cap B \cap C|$$

The general formula for $n$ sets $A_1, A_2, \ldots, A_n$ is:

$$\left|\bigcup_{i=1}^{n} A_i\right| = \sum_{k=1}^{n} (-1)^{k+1} \sum_{1 \le i_1 < i_2 < \cdots < i_k \le n} |A_{i_1} \cap A_{i_2} \cap \cdots \cap A_{i_k}|$$

**Proof.** We show that each element $x$ in $\bigcup_{i=1}^n A_i$ is counted exactly once by the right-hand side. Suppose $x$ belongs to exactly $r$ of the sets, say $A_{j_1}, A_{j_2}, \ldots, A_{j_r}$ (with $r \ge 1$ since $x$ is in the union). In the sum, $x$ is counted once for each intersection it belongs to. The number of $k$-fold intersections containing $x$ is $\binom{r}{k}$ (choosing $k$ of the $r$ sets that contain $x$). The sign attached to $k$-fold intersections is $(-1)^{k+1}$. So the net count of $x$ is:

$$\sum_{k=1}^{r} (-1)^{k+1} \binom{r}{k} = 1 - \sum_{k=0}^{r} (-1)^{k} \binom{r}{k} + 1 = 1 - (1 - 1)^r = 1 - 0 = 1$$

where we used the Binomial Theorem (proved below) to evaluate $\sum_{k=0}^{r} (-1)^{k} \binom{r}{k} = (1 - 1)^r = 0^r = 0$ for $r \ge 1$. Thus every element is counted exactly once, completing the proof. $\square$

The canonical application of PIE is the **derangement** problem: how many permutations of $\{1, 2, \ldots, n\}$ leave no element in its original position? A derangement is a permutation $\sigma$ such that $\sigma(i) \ne i$ for all $i$. Let $A_i$ be the set of permutations where $\sigma(i) = i$ (element $i$ is a fixed point). We seek the complement: $n! - |A_1 \cup A_2 \cup \cdots \cup A_n|$.

By PIE:

$$|A_1 \cup \cdots \cup A_n| = \sum_{k=1}^{n} (-1)^{k+1} \binom{n}{k} (n-k)!$$

The term $\binom{n}{k}(n-k)!$ counts permutations where at least $k$ specific elements are fixed: choose $k$ elements to fix (in $\binom{n}{k}$ ways), then permute the remaining $n - k$ freely (in $(n-k)!$ ways). The number of derangements is:

$$D_n = n! - \sum_{k=1}^{n} (-1)^{k+1} \binom{n}{k} (n-k)! = n! \sum_{k=0}^{n} \frac{(-1)^k}{k!}$$

The simplification: $\binom{n}{k}(n-k)! = \frac{n!}{k!(n-k)!} \cdot (n-k)! = \frac{n!}{k!}$, so:

$$D_n = \sum_{k=0}^{n} (-1)^k \frac{n!}{k!} = n! \sum_{k=0}^{n} \frac{(-1)^k}{k!}$$

As $n \to \infty$, the sum $\sum_{k=0}^{n} \frac{(-1)^k}{k!} \to e^{-1} \approx 0.3679$, giving the well-known approximation $D_n \approx n!/e$. The probability that a random permutation is a derangement approaches $1/e$ as $n$ grows, a result with direct applications in cryptographic analysis (e.g., analyzing substitution ciphers where no plaintext symbol maps to itself).

### 2.4 The Binomial Theorem

The **Binomial Theorem** states that for any real numbers $a, b$ and non-negative integer $n$:

$$(a + b)^n = \sum_{k=0}^{n} \binom{n}{k} a^{n-k} b^k$$

**Proof by combinatorial argument.** Expand $(a+b)^n = \underbrace{(a+b)(a+b)\cdots(a+b)}_{n \text{ factors}}$. Each term in the expansion arises by choosing either $a$ or $b$ from each of the $n$ factors. A term containing $b^k$ (and thus $a^{n-k}$) is produced by choosing $b$ from exactly $k$ of the $n$ factors. There are $\binom{n}{k}$ ways to select which $k$ factors contribute $b$, so the coefficient of $a^{n-k}b^k$ is $\binom{n}{k}$. $\square$

**Proof by induction.** Base case: $n = 0$ gives $(a+b)^0 = 1 = \binom{0}{0}a^0 b^0$. Inductive step: assume $(a+b)^n = \sum_{k=0}^n \binom{n}{k} a^{n-k} b^k$. Then:

$$(a+b)^{n+1} = (a+b) \cdot \sum_{k=0}^{n} \binom{n}{k} a^{n-k} b^k = \sum_{k=0}^{n} \binom{n}{k} a^{n+1-k} b^k + \sum_{k=0}^{n} \binom{n}{k} a^{n-k} b^{k+1}$$

Re-index the second sum by substituting $j = k + 1$:

$$= \sum_{k=0}^{n} \binom{n}{k} a^{n+1-k} b^k + \sum_{j=1}^{n+1} \binom{n}{j-1} a^{n+1-j} b^j$$

Combining the sums (noting the overlapping range $k = 1, \ldots, n$):

$$= \binom{n}{0} a^{n+1} + \sum_{k=1}^{n} \left[\binom{n}{k} + \binom{n}{k-1}\right] a^{n+1-k} b^k + \binom{n}{n} b^{n+1}$$

By **Pascal's Identity**, $\binom{n}{k} + \binom{n}{k-1} = \binom{n+1}{k}$ (proved below), so:

$$= \sum_{k=0}^{n+1} \binom{n+1}{k} a^{n+1-k} b^k$$

completing the induction. $\square$

**Pascal's Identity** itself: $\binom{n}{k} + \binom{n}{k-1} = \binom{n+1}{k}$. Combinatorial proof: to choose $k$ elements from $n+1$, fix a distinguished element $x$. Either $x$ is chosen (leaving $\binom{n}{k-1}$ ways to pick the remaining $k-1$ from the other $n$) or $x$ is not chosen (leaving $\binom{n}{k}$ ways). The cases are disjoint and exhaustive, so $\binom{n+1}{k} = \binom{n}{k-1} + \binom{n}{k}$.

The binomial coefficients satisfy numerous identities that are indispensable in algorithmic analysis. The **Vandermonde Identity** states $\binom{m+n}{r} = \sum_{k=0}^{r} \binom{m}{k}\binom{n}{r-k}$, proved by observing that choosing $r$ from $m + n$ elements (partitioned into groups of size $m$ and $n$) requires choosing $k$ from the first group and $r - k$ from the second, summed over all valid $k$. The **hockey stick identity** $\sum_{i=r}^{n} \binom{i}{r} = \binom{n+1}{r+1}$ follows from repeated application of Pascal's identity.

### 2.5 Recurrence Relations

A **recurrence relation** defines a sequence by expressing each term as a function of its predecessors. Recurrences arise naturally in combinatorial counting: the structure of many combinatorial objects allows decomposition into smaller instances of the same problem, yielding a recursive formula that can then be solved for a closed form.

The **Fibonacci sequence** is the paradigmatic example. Defined by $F_0 = 0$, $F_1 = 1$, and $F_n = F_{n-1} + F_{n-2}$ for $n \ge 2$, it counts the number of ways to tile a $1 \times n$ strip with $1 \times 1$ squares and $1 \times 2$ dominoes. The recurrence arises from the last tile: if the last tile is a square, the remaining $1 \times (n-1)$ strip can be tiled in $F_{n-1}$ ways; if the last tile is a domino, the remaining $1 \times (n-2)$ strip can be tiled in $F_{n-2}$ ways. The base cases $F_0 = 0$ (empty tiling) and $F_1 = 1$ (one square) anchor the recurrence.

For **linear homogeneous recurrence relations with constant coefficients** of the form:

$$a_n + c_1 a_{n-1} + c_2 a_{n-2} + \cdots + c_k a_{n-k} = 0$$

the solution method proceeds via the **characteristic equation**. We substitute $a_n = r^n$ and obtain:

$$r^k + c_1 r^{k-1} + c_2 r^{k-2} + \cdots + c_k = 0$$

If this polynomial has $k$ distinct roots $r_1, r_2, \ldots, r_k$, the general solution is:

$$a_n = \alpha_1 r_1^n + \alpha_2 r_2^n + \cdots + \alpha_k r_k^n$$

where $\alpha_1, \ldots, \alpha_k$ are constants determined by the initial conditions. If a root $r$ has multiplicity $m$, the corresponding terms are $(\alpha_1 + \alpha_2 n + \alpha_3 n^2 + \cdots + \alpha_m n^{m-1}) r^n$.

For the Fibonacci recurrence $F_n - F_{n-1} - F_{n-2} = 0$, the characteristic equation is $r^2 - r - 1 = 0$, with roots $r = \frac{1 \pm \sqrt{5}}{2}$. Let $\varphi = \frac{1+\sqrt{5}}{2}$ (the golden ratio) and $\hat{\varphi} = \frac{1-\sqrt{5}}{2}$. The general solution is $F_n = \alpha \varphi^n + \beta \hat{\varphi}^n$. Applying initial conditions $F_0 = 0$ and $F_1 = 1$:

$$\alpha + \beta = 0 \implies \beta = -\alpha$$
$$\alpha \varphi - \alpha \hat{\varphi} = 1 \implies \alpha = \frac{1}{\varphi - \hat{\varphi}} = \frac{1}{\sqrt{5}}$$

This yields **Binet's Formula**:

$$F_n = \frac{1}{\sqrt{5}} \left(\frac{1+\sqrt{5}}{2}\right)^n - \frac{1}{\sqrt{5}} \left(\frac{1-\sqrt{5}}{2}\right)^n = \frac{\varphi^n - \hat{\varphi}^n}{\sqrt{5}}$$

Since $|\hat{\varphi}| < 1$, the term $\hat{\varphi}^n / \sqrt{5}$ vanishes rapidly, giving $F_n = \lfloor \varphi^n / \sqrt{5} + 1/2 \rfloor$ for all $n \ge 0$. This closed form enables $O(\log n)$ computation of $F_n$ via fast matrix exponentiation on the matrix $\begin{pmatrix} 1 & 1 \\ 1 & 0 \end{pmatrix}$, since $\begin{pmatrix} F_{n+1} & F_n \\ F_n & F_{n-1} \end{pmatrix} = \begin{pmatrix} 1 & 1 \\ 1 & 0 \end{pmatrix}^n$.

For **non-homogeneous** recurrences of the form $a_n + c_1 a_{n-1} + \cdots + c_k a_{n-k} = f(n)$, the general solution is the sum of the homogeneous solution $a_n^{(h)}$ and a particular solution $a_n^{(p)}$ that satisfies the full recurrence. The particular solution is found by the method of undetermined coefficients: if $f(n)$ is a polynomial of degree $d$, try $a_n^{(p)} = P_d(n)$ (a degree-$d$ polynomial); if $f(n) = c \cdot r^n$, try $a_n^{(p)} = \alpha r^n$ (adjusting if $r$ is a root of the characteristic equation by multiplying by $n^m$ where $m$ is the multiplicity).

The **Tower of Hanoi** provides a clean illustration. Moving $n$ disks requires $T_n$ moves, where $T_n = 2T_{n-1} + 1$ with $T_1 = 1$. The characteristic equation $r - 2 = 0$ gives homogeneous solution $\alpha \cdot 2^n$. For the particular solution, since $f(n) = 1$ is a degree-0 polynomial and $r = 1$ is not a root, try $a_n^{(p)} = C$ (constant). Substituting: $C = 2C + 1$, so $C = -1$. The general solution is $T_n = \alpha \cdot 2^n - 1$. From $T_1 = 1$: $\alpha \cdot 2 - 1 = 1$, so $\alpha = 1$, giving $T_n = 2^n - 1$.

### 2.6 Generating Functions

Generating functions transform combinatorial problems into algebraic ones by encoding a sequence $\{a_n\}_{n=0}^{\infty}$ as coefficients of a formal power series. The **ordinary generating function (OGF)** of the sequence is:

$$G(x) = \sum_{n=0}^{\infty} a_n x^n = a_0 + a_1 x + a_2 x^2 + a_3 x^3 + \cdots$$

The key insight is that the algebraic structure of $G(x)$ mirrors the combinatorial structure of the counting problem. Operations on generating functions correspond to combinatorial operations on the underlying objects.

**Addition** of generating functions corresponds to the Sum Rule: if $G(x) = \sum a_n x^n$ counts objects of type $A$ and $H(x) = \sum b_n x^n$ counts objects of type $B$, then $G(x) + H(x) = \sum (a_n + b_n) x^n$ counts objects that are either type $A$ or type $B$ (disjoint union).

**Multiplication** corresponds to the Product Rule with convolution: $G(x) \cdot H(x) = \sum_n \left(\sum_{k=0}^n a_k b_{n-k}\right) x^n$. The coefficient of $x^n$ in the product counts ordered pairs $(a, b)$ where $a$ is an $A$-object of size $k$ and $b$ is a $B$-object of size $n-k$, summed over all valid $k$. This is the **Cauchy product** or **convolution** of the two sequences, and it is the algebraic encoding of the combinatorial Product Rule.

The fundamental example is the OGF for the constant sequence $a_n = 1$ for all $n \ge 0$:

$$\frac{1}{1-x} = \sum_{n=0}^{\infty} x^n = 1 + x + x^2 + x^3 + \cdots$$

This is the geometric series, and it is the generating function for the single type of object of every non-negative size (one way to choose each size). Composing it with $x^k$ gives $\frac{1}{1-x^k} = \sum_{n=0}^{\infty} x^{kn}$, the OGF for selecting items of size $k$ with unlimited repetition.

To count the number of ways to make change for $n$ cents using pennies (1¢), nickels (5¢), dimes (10¢), and quarters (25¢), we form the product:

$$G(x) = \frac{1}{(1-x)(1-x^5)(1-x^{10})(1-x^{25})}$$

Each factor $\frac{1}{1-x^k} = 1 + x^k + x^{2k} + \cdots$ encodes using 0, 1, 2, ... coins of denomination $k$. The product's coefficient $[x^n] G(x)$ gives the number of ways to total $n$ cents, because the Cauchy product assembles all combinations of coin counts whose values sum to $n$. This is a direct application of the Product Rule via generating function multiplication.

The OGF for the binomial coefficients $\binom{n}{k}$ (for fixed $n$, varying $k$) is given directly by the Binomial Theorem:

$$(1+x)^n = \sum_{k=0}^{n} \binom{n}{k} x^k$$

So $(1+x)^n$ is the OGF for the $n$-th row of Pascal's triangle. The OGF for the sequence $\binom{n}{k}$ (for fixed $k$, varying $n$) is:

$$\sum_{n=0}^{\infty} \binom{n}{k} x^n = \frac{x^k}{(1-x)^{k+1}}$$

This identity can be proved by induction on $k$ or by differentiating the geometric series $k$ times. Starting from $\frac{1}{1-x} = \sum x^n$, differentiate both sides: $\frac{1}{(1-x)^2} = \sum n x^{n-1}$, so $\frac{x}{(1-x)^2} = \sum n x^n = \sum \binom{n}{1} x^n$ (since $\binom{n}{1} = n$). Differentiating again and multiplying by $x$ gives $\frac{x^2}{(1-x)^3} = \sum \binom{n}{2} x^n$, and the pattern continues by induction.

The OGF for the Fibonacci sequence is derived from the recurrence. Let $G(x) = \sum_{n=0}^{\infty} F_n x^n$. Multiply the recurrence $F_n = F_{n-1} + F_{n-2}$ (valid for $n \ge 2$) by $x^n$ and sum:

$$\sum_{n=2}^{\infty} F_n x^n = \sum_{n=2}^{\infty} F_{n-1} x^n + \sum_{n=2}^{\infty} F_{n-2} x^n$$

$$G(x) - F_0 - F_1 x = x \sum_{n=2}^{\infty} F_{n-1} x^{n-1} + x^2 \sum_{n=2}^{\infty} F_{n-2} x^{n-2}$$

$$G(x) - 0 - x = x(G(x) - F_0) + x^2 G(x) = x \cdot G(x) + x^2 \cdot G(x)$$

Solving for $G(x)$:

$$G(x) = \frac{x}{1 - x - x^2}$$

The denominator factors as $1 - x - x^2 = (1 - \varphi x)(1 - \hat{\varphi} x)$ where $\varphi = \frac{1+\sqrt{5}}{2}$ and $\hat{\varphi} = \frac{1-\sqrt{5}}{2}$. Partial fraction decomposition gives:

$$G(x) = \frac{1}{\sqrt{5}} \left(\frac{1}{1 - \varphi x} - \frac{1}{1 - \hat{\varphi} x}\right)$$

Extracting coefficients via $\frac{1}{1-rx} = \sum (rx)^n$ yields Binet's formula immediately: $F_n = \frac{\varphi^n - \hat{\varphi}^n}{\sqrt{5}}$.

The **exponential generating function (EGF)** is used when objects have labeled positions (permutations rather than combinations). The EGF of $\{a_n\}$ is:

$$E(x) = \sum_{n=0}^{\infty} \frac{a_n}{n!} x^n$$

The EGF for the sequence of derangements $D_n$ is:

$$\sum_{n=0}^{\infty} \frac{D_n}{n!} x^n = \frac{e^{-x}}{1-x}$$

This follows from $D_n = n! \sum_{k=0}^{n} \frac{(-1)^k}{k!}$, so:

$$\sum_{n=0}^{\infty} \frac{D_n}{n!} x^n = \sum_{n=0}^{\infty} \sum_{k=0}^{n} \frac{(-1)^k}{k!} x^n = \left(\sum_{k=0}^{\infty} \frac{(-x)^k}{k!}\right) \cdot \left(\sum_{j=0}^{\infty} x^j\right) = e^{-x} \cdot \frac{1}{1-x}$$

where the Cauchy product of $e^{-x} = \sum \frac{(-x)^k}{k!}$ and $\frac{1}{1-x} = \sum x^j$ produces the double sum, and the interchange of summation order is justified by absolute convergence for $|x| < 1$. The product $e^{-x} \cdot \frac{1}{1-x}$ has a striking combinatorial interpretation: $\frac{1}{1-x}$ is the EGF for the identity permutation (one permutation of each size), and $e^{-x}$ "excludes" fixed points (the EGF for permutations with no fixed points of a given subset), with their product assembling derangements by inclusion-exclusion at the generating function level.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Computational Considerations for Binomial Coefficients

Direct computation of $\binom{n}{k} = \frac{n!}{k!(n-k)!}$ via factorials is numerically hazardous for moderate $n$. The factorial $20! = 2{,}432{,}902{,}008{,}176{,}640{,}000$ already exceeds $2^{61}$, overflowing a 64-bit signed integer. The standard mitigation is **multiplicative accumulation** using the identity:

$$\binom{n}{k} = \prod_{i=1}^{k} \frac{n - k + i}{i}$$

Computing the product left to right, performing division at each step, keeps intermediate values integral (since $\prod_{i=1}^{j} (n-k+i)$ is always divisible by $j!$ for $j \le k$, being a product of $j$ consecutive integers divided by $j!$). This approach computes $\binom{n}{k}$ in $O(k)$ time with $O(1)$ space beyond the accumulator, and it avoids overflow as long as the final result fits in the integer type.

For problems requiring $\binom{n}{k} \pmod{p}$ for prime $p$ (common in competitive programming and cryptographic protocols), **Lucas' Theorem** decomposes the computation. Write $n$ and $k$ in base $p$: $n = n_0 + n_1 p + n_2 p^2 + \cdots + n_d p^d$ and $k = k_0 + k_1 p + k_2 p^2 + \cdots + k_d p^d$. Then:

$$\binom{n}{k} \equiv \prod_{i=0}^{d} \binom{n_i}{k_i} \pmod{p}$$

If any $k_i > n_i$, the product is zero, meaning $\binom{n}{k} \equiv 0 \pmod{p}$—a condition with direct implications for the $p$-adic valuation of binomial coefficients and applications in coding theory (specifically, determining the weight distribution of Reed-Solomon codes). The proof relies on the fact that $(1+x)^p \equiv 1 + x^p \pmod{p}$ (the "Freshman's Dream" in $\mathbb{F}_p[x]$, since all intermediate binomial coefficients $\binom{p}{i}$ for $0 < i < p$ are divisible by $p$), so $(1+x)^n = \prod (1+x)^{n_i p^i} \equiv \prod (1 + x^{p^i})^{n_i} \pmod{p}$, and comparing coefficients of $x^k$ yields the product formula.

### 3.2 Generating Function Extraction via Partial Fractions

When a generating function $G(x) = \frac{P(x)}{Q(x)}$ is a rational function with $\deg P < \deg Q$, the partial fraction decomposition provides a systematic method for extracting coefficients. If $Q(x)$ factors as $\prod_{i=1}^{m} (1 - r_i x)^{d_i}$ with distinct roots $r_i$ and multiplicities $d_i$, then:

$$G(x) = \sum_{i=1}^{m} \sum_{j=1}^{d_i} \frac{c_{i,j}}{(1 - r_i x)^j}$$

Each term contributes to the coefficient of $x^n$ via the identity $\frac{1}{(1-rx)^j} = \sum_{n=0}^{\infty} \binom{n+j-1}{j-1} r^n x^n$. So the closed form is:

$$a_n = \sum_{i=1}^{m} \sum_{j=1}^{d_i} c_{i,j} \binom{n+j-1}{j-1} r_i^n$$

The dominant term (largest $|r_i|$) controls the asymptotic growth rate, providing the exponential growth rate and polynomial correction factor of the sequence. This is the mechanism by which the characteristic equation method for linear recurrences works: the roots of the characteristic polynomial are precisely the reciprocals $1/r_i$ of the roots of $Q(x)$.

The failure mode to watch for is **repeated roots** in $Q(x)$. When $Q(x) = (1 - rx)^d$, the coefficient of $x^n$ is $\binom{n+d-1}{d-1} r^n$, which is a polynomial of degree $d-1$ in $n$ times $r^n$, not simply $r^n$. Omitting the polynomial factor is the most common error in solving recurrences with repeated characteristic roots, leading to exponential error in the closed form.

### 3.3 Common Counting Pitfalls

**Overcounting due to symmetry.** When counting arrangements of objects with indistinguishable elements, failing to divide by the symmetry factor is the most frequent error. The number of distinct arrangements of the letters in "MISSISSIPPI" (with multiplicities M=1, I=4, S=4, P=2, total $n=11$) is $\frac{11!}{1! \cdot 4! \cdot 4! \cdot 2!} = \frac{39916800}{1152} = 34{,}650$. A direct $11!$ count without division yields roughly $40$ million, off by a factor of over $1{,}000$.

**Conflating ordered and unordered selection.** The formula $\binom{n}{k}$ counts unordered subsets; $P(n, k) = \frac{n!}{(n-k)!}$ counts ordered selections. Using $\binom{n}{k}$ when order matters, or vice versa, produces results off by a factor of $k!$. This error is particularly insidious in probability calculations, where it silently corrupts the sample space denominator.

**Inclusion-exclusion sign errors.** The alternating signs in PIE are easy to get wrong, especially for $n \ge 4$ sets. The sign of the $k$-fold intersection term is $(-1)^{k+1}$ in the union formula (or $(-1)^k$ in the complement). A reliable mnemonic: for $|A_1 \cup \cdots \cup A_n|$, single sets are added (+), pairs are subtracted (−), triples are added (+), and so on, alternating. For the complement $|\overline{A_1} \cap \cdots \cap \overline{A_n}| = N - |A_1 \cup \cdots \cup A_n|$, the signs flip: singles subtracted (−), pairs added (+), triples subtracted (−).

**Misidentifying the pigeonhole structure.** The pigeonhole principle requires correctly identifying objects and boxes. A frequent error is assigning the obvious quantities as objects and boxes without checking that the pigeonhole count actually forces the desired conclusion. In the Erdős–Szekeres theorem, the non-obvious assignment of the pair $(u_i, d_i)$ as the "object" and the $n \times n$ grid of possible pairs as the "boxes" is what makes the proof work. A naive assignment (e.g., positions as objects and values as boxes) yields no useful collision.

**Generating function convergence vs. formal power series.** When manipulating generating functions, one must distinguish between analytic operations (requiring convergence) and formal operations (valid in the ring of formal power series). The identity $\frac{1}{1-x} = \sum x^n$ holds as a formal power series regardless of convergence; the analytic identity holds only for $|x| < 1$. Operations like multiplication, addition, differentiation, and composition with polynomials are valid in the formal ring. However, substitution of specific $x$ values, evaluation of limits, and analytic continuation require convergence. The failure mode is treating a formal identity as an analytic equality at a point outside the radius of convergence, producing nonsensical numerical results. For combinatorial purposes, the formal power series interpretation suffices: the coefficient of $x^n$ is well-defined as a finite computation regardless of convergence, since extracting $[x^n]$ from a product or sum involves only finitely many terms.

**Recurrence base case mismatch.** When solving a recurrence via generating functions, the initial conditions must be handled precisely. The Fibonacci derivation required $F_0 = 0$ and $F_1 = 1$ specifically; using $F_1 = 1$ and $F_2 = 1$ as initial conditions (a common alternative convention) shifts the index and produces $G(x) = \frac{x}{1-x-x^2}$ only if the summation starts at $n=1$ rather than $n=0$. A mismatch between the summation index and the recurrence's base cases produces a generating function that satisfies the recurrence but not the initial conditions, yielding a sequence offset by one or more positions—a subtle error that propagates through every extracted coefficient.
