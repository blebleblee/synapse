# Lesson 3: Greedy Algorithms with Dynamic Programming

## 1. First-Principles Intuition & Invariants

The history of algorithmic thinking contains a persistent temptation: the belief that locally optimal decisions, made in sequence, will accumulate into a globally optimal solution. This temptation is not nave. For a surprisingly rich class of problems, it is exactly correct. For an equally rich class, it is catastrophically wrong. The discipline of algorithm design demands that we know, with mathematical precision, which world we inhabit before we commit a single line of code.

Greedy algorithms and dynamic programming represent two fundamentally different responses to the same underlying challenge: how to solve an optimization problem over a combinatorial structure without enumerating every candidate solution. A greedy algorithm commits irrevocably to a locally optimal choice at each step, never reconsidering. Dynamic programming, by contrast, defers commitment by decomposing the problem into overlapping subproblems, caching their solutions, and assembling the global optimum from verified parts. These are not merely stylistic preferences. They reflect deep structural properties of the problem itself, and distinguishing them requires a precise vocabulary grounded in combinatorics and linear algebra.

### The Greedy Choice Property

The formal foundation of correctness for any greedy algorithm is the **greedy choice property**: there exists an optimal solution that is consistent with the greedy choice made at the first step. This is not a claim that every greedy choice leads to optimality in isolation. It is the stronger claim that no matter which optimal solution the adversary presents, we can transform it into one that agrees with our greedy choice without degrading its quality. This exchange argument is the canonical proof technique for greedy correctness, and mastering it is essential.

To make this precise, consider a maximization problem over a family $\mathcal{F}$ of feasible sets drawn from a ground set $U$. The greedy algorithm selects an element $e^* \in U$ that maximizes some objective contribution, adds it to the current solution, and recurses on the residual problem. The greedy choice property asserts that there exists an optimal solution $OPT \in \mathcal{F}$ with $e^* \in OPT$. The proof proceeds by assuming the contrary: that every optimal solution excludes $e^*$. We then take some $OPT' \in \mathcal{F}$ not containing $e^*$, construct $OPT'' = (OPT' \setminus \{e'\}) \cup \{e^*\}$ for some $e' \in OPT'$, and show $OPT''$ is both feasible and no worse in objective value than $OPT'$. The specific argument depends on the problem structure, but the logical skeleton is universal.

The second invariant required for greedy correctness is the **optimal substructure property**: once the greedy choice has been made, the remaining subproblem has the same form as the original, and an optimal solution to the full problem consists of the greedy choice together with an optimal solution to the residual. This is precisely where greedy algorithms and dynamic programming share a common ancestor. Dynamic programming also requires optimal substructure, but it additionally requires overlapping subproblems, the condition under which naive recursion would recompute the same subproblem exponentially many times. When optimal substructure holds and the greedy choice property also holds, we obtain a greedy algorithm, which is strictly stronger (and cheaper) than DP. When optimal substructure holds but greedy choices are not globally safe, we fall back to DP.

### Matroids: The Algebraic Foundation of Greedy Optimality

The deepest and most satisfying explanation for why greedy algorithms work on certain problems is the theory of **matroids**, a structure introduced by Hassler Whitney in 1935 at the intersection of linear algebra and combinatorics. A matroid is a pair $M = (U, \mathcal{I})$ where $U$ is a finite ground set and $\mathcal{I} \subseteq 2^U$ is a family of subsets called independent sets, satisfying three axioms.

The first axiom is that the empty set is independent: $\emptyset \in \mathcal{I}$. The second is the hereditary property: if $A \in \mathcal{I}$ and $B \subseteq A$, then $B \in \mathcal{I}$. Every subset of an independent set is independent. The third is the augmentation (or exchange) axiom: if $A, B \in \mathcal{I}$ and $|A| < |B|$, then there exists some $e \in B \setminus A$ such that $A \cup \{e\} \in \mathcal{I}$.

$$\text{If } A, B \in \mathcal{I} \text{ and } |A| < |B|, \text{ then } \exists\, e \in B \setminus A : A \cup \{e\} \in \mathcal{I}$$

The augmentation axiom is precisely what enables greedy algorithms to function. It guarantees that whenever our current independent set is smaller than some other independent set, we can extend it. This prevents the algorithm from getting trapped at a local maximum that is not globally maximal. A maximal independent set in any matroid has the same cardinality as every other maximal independent set; this common cardinality is the **rank** of the matroid.

The prototypical example is the **linear matroid** (or vector matroid): given a matrix $A$ over a field $\mathbb{F}$, let $U$ be the set of column indices and declare $I \subseteq U$ independent if the corresponding columns are linearly independent over $\mathbb{F}$. The augmentation axiom holds because of the dimension theorem from linear algebra: if two sets of vectors have different sizes, the larger set spans a higher-dimensional space, so the smaller set must be extensible. A second fundamental example is the **graphic matroid**: given a graph $G = (V, E)$, let $U = E$ and declare $I \subseteq E$ independent if $I$ forms a forest (acyclic subgraph). The augmentation axiom holds here because a spanning forest of a connected graph always has exactly $|V| - 1$ edges, so any smaller forest can be extended by an edge that does not form a cycle.

The central theorem connecting matroids to algorithmic design is due to Jack Edmonds (1971):

**Theorem (Edmonds).** Let $M = (U, \mathcal{I})$ be a matroid and let $w : U \to \mathbb{R}_{\geq 0}$ be a weight function. The greedy algorithm, which builds an independent set by repeatedly adding the maximum-weight element that preserves independence, finds a maximum-weight basis of $M$.

Furthermore, Edmonds proved the converse: if $\mathcal{I}$ is a hereditary family for which the greedy algorithm finds a maximum-weight independent set for every weight function $w$, then $(U, \mathcal{I})$ is a matroid. The greedy algorithm and matroids are, in a precise sense, equivalent. This equivalence is the theoretical reason Kruskal's algorithm for minimum spanning trees is correct, the reason the greedy interval scheduling algorithm is correct, and the reason the greedy algorithm fails on the knapsack problem (where the feasible sets do not form a matroid).

### Activity Selection and the Interval Scheduling Matroid

The **activity selection problem** is the canonical textbook application of greedy correctness, but its matroid structure is worth examining carefully because it reveals more than the standard exchange argument alone. We are given $n$ activities, each specified by a start time $s_i$ and finish time $f_i$, and we wish to select the maximum number of mutually compatible activities (no two overlap in time). The greedy strategy sorts activities by finish time and selects each activity that does not conflict with the most recently selected one.

Formally, define $U = \{a_1, \ldots, a_n\}$ sorted so $f_1 \leq f_2 \leq \cdots \leq f_n$. Declare $I \subseteq U$ independent if the activities in $I$ are pairwise compatible. This family is hereditary (any subset of compatible activities is compatible) and satisfies augmentation (a consequence of the finish-time ordering). The greedy algorithm processes activities left to right; at each step it selects $a_i$ if $s_i \geq f_j$ where $a_j$ is the last selected activity.

**Theorem.** The greedy algorithm selects a maximum-cardinality set of compatible activities.

**Proof.** We prove by induction that after $k$ greedy selections, the algorithm has made as many selections as any optimal solution after considering the first $k$ selected activities. Base case $k = 0$ is trivial. For the inductive step, let the greedy solution after $k$ steps be $G_k = \{g_1, \ldots, g_k\}$ and let $OPT = \{o_1, \ldots, o_m\}$ be any optimal solution, both sorted by finish time. We claim $f_{g_k} \leq f_{o_k}$ for all $k \leq m$. This is the key invariant: the greedy solution always finishes no later than the optimal solution at each comparable step, which means it never precludes opportunities that the optimal solution would have kept open. The claim follows by induction: $f_{g_1} \leq f_{o_1}$ because the greedy algorithm chose the activity with the smallest finish time. Assuming $f_{g_k} \leq f_{o_k}$, the next optimal activity $o_{k+1}$ satisfies $s_{o_{k+1}} \geq f_{o_k} \geq f_{g_k}$, so $o_{k+1}$ is also compatible with the greedy solution after step $k$. The greedy algorithm at step $k+1$ selects the compatible activity with smallest finish time, so $f_{g_{k+1}} \leq f_{o_{k+1}}$. If $m > |G|$ (the greedy solution has fewer activities than optimal), then after $|G|$ steps the optimal solution still has an unconsidered activity compatible with the greedy state, contradicting greedy termination. Therefore $|G| = m$. $\blacksquare$

### Huffman Coding: Greedy Optimality in Information Theory

**Huffman coding** (1952) solves a different optimization problem: given an alphabet $\Sigma = \{c_1, \ldots, c_n\}$ with symbol frequencies $\{f_1, \ldots, f_n\}$, construct a prefix-free binary code (representable as a full binary tree) that minimizes the expected code length

$$B(T) = \sum_{i=1}^{n} f_i \cdot d_T(c_i)$$

where $d_T(c_i)$ is the depth of leaf $c_i$ in the coding tree $T$. A prefix-free code is one where no codeword is a prefix of another; this is equivalent to assigning symbols to leaves of a binary tree.

The greedy insight is that in any optimal tree, the two symbols with the smallest frequencies must be siblings at the maximum depth of the tree. This is the exchange argument at work: if the two least-frequent symbols were not siblings, we could swap them closer together and closer to the bottom, reducing $B(T)$. Given this, the Huffman algorithm merges the two minimum-frequency symbols into a single meta-symbol with frequency $f_i + f_j$, recurses, and reconstructs the tree.

**Theorem.** The Huffman algorithm produces a prefix-free binary code achieving the minimum expected length $B(T)$.

**Proof.** Let $x$ and $y$ be the two symbols with minimum frequencies $f_x \leq f_y$. We claim that there exists an optimal tree in which $x$ and $y$ are siblings at maximum depth.

Take any optimal tree $T^*$. Let $a, b$ be siblings at maximum depth in $T^*$. If $\{a, b\} = \{x, y\}$ we are done. Otherwise, without loss of generality assume $a \neq x$. Since $x$ is not at maximum depth, $d_{T^*}(x) \leq d_{T^*}(a)$. Swap $x$ and $a$ in $T^*$ to produce $T_1$. The change in cost is

$$B(T_1) - B(T^*) = f_x \cdot d_{T^*}(a) + f_a \cdot d_{T^*}(x) - f_x \cdot d_{T^*}(x) - f_a \cdot d_{T^*}(a)$$
$$= (f_x - f_a)(d_{T^*}(a) - d_{T^*}(x))$$

Since $f_x \leq f_a$ (as $x$ has minimum frequency) and $d_{T^*}(a) \geq d_{T^*}(x)$ (since $a$ is at maximum depth), the product $(f_x - f_a)(d_{T^*}(a) - d_{T^*}(x)) \leq 0$. Thus $B(T_1) \leq B(T^*)$, so $T_1$ is also optimal. Applying the same argument to place $y$ as the sibling of $x$ yields an optimal tree $T_2$ where $x$ and $y$ are siblings.

Now let $T'$ be the tree obtained by merging $x$ and $y$ into a meta-node $z$ with $f_z = f_x + f_y$. The cost satisfies

$$B(T_2) = B(T') + f_x + f_y$$

because every node in $T'$ contributes the same depth cost in $T_2$, plus the two leaves $x$ and $y$ each contribute one additional level. By induction on $n$ (the base case of two symbols is trivial), the Huffman algorithm applied to the reduced problem with $z$ produces an optimal $T'$, and therefore $T_2$ is optimal for the original problem. $\blacksquare$

The implementation uses a min-heap to extract the two minimum-frequency nodes in $O(\log n)$ time, performing $n - 1$ merge operations for a total time complexity of $O(n \log n)$.

### Optimal Substructure and the DP Foundation

Where greedy algorithms rely on the greedy choice property to avoid exploring alternatives, **dynamic programming** relies on a more general principle: if an optimal solution to a problem of size $n$ uses an optimal solution to a subproblem of size $k < n$, we can build the full solution bottom-up by solving all subproblems first. This optimal substructure is the sine qua non of DP, and verifying it rigorously for a given problem is the first task of algorithm design.

The two operational modalities of DP are **memoization** (top-down recursion with a cache) and **tabulation** (bottom-up iterative filling of a table). Both exploit the same mathematical structure: the **recurrence relation** that expresses the optimal value of a problem in terms of optimal values of its subproblems. For memoization, we write the natural recursive solution and annotate it with a lookup table; if a subproblem has been solved before, we return the cached result in $O(1)$ instead of recomputing. For tabulation, we identify a topological ordering of subproblems (smaller problems must be solved before larger ones) and fill the table in that order.

The formal correctness of tabulation rests on the **principle of optimality** articulated by Richard Bellman in the 1950s: "An optimal policy has the property that whatever the initial state and initial decision are, the remaining decisions must constitute an optimal policy with regard to the state resulting from the first decision." This is not a theorem to be proved but a property to be verified for each problem. When it fails, DP fails. The classic failure case is problems with negative-weight cycles in shortest-path formulations, where "optimal" subpaths interact non-locally.

---

## 2. Core Architecture & Mechanics

### The Structural Taxonomy of DP Recurrences

Dynamic programming problems organize themselves around the topology of their subproblem dependency graph. The three canonical topologies are linear, interval, and tree-shaped dependencies, and each admits a characteristic table structure and filling order.

In a **linear DP**, the solution to problem of size $i$ depends only on solutions to problems of size $i - 1$ (or some constant number of preceding sizes). The Fibonacci sequence is the trivial example, but the more interesting one is the **weighted interval scheduling** problem: given intervals with weights, find a maximum-weight compatible subset. Define $p(j)$ as the largest index $i < j$ such that interval $i$ is compatible with interval $j$ (intervals sorted by finish time). The recurrence is

$$OPT(j) = \max\bigl(w_j + OPT(p(j)),\; OPT(j-1)\bigr)$$

The first argument represents selecting interval $j$ (and jumping to the last compatible predecessor), while the second represents skipping it. Tabulation fills $OPT(0) = 0$ through $OPT(n)$ in $O(n)$ time after an $O(n \log n)$ sort, with $p(j)$ computed by binary search.

In an **interval DP**, the solution to interval $[i, j]$ depends on solutions to shorter intervals $[i, k]$ and $[k+1, j]$ for some split point $k$. The canonical example is **matrix chain multiplication**: given matrices $M_1, M_2, \ldots, M_n$ with compatible dimensions, find the parenthesization minimizing the total number of scalar multiplications. If matrix $M_i$ has dimensions $d_{i-1} \times d_i$, then the cost of multiplying $M_i \cdot M_{i+1} \cdots M_j$ with the split at $k$ is

$$C(i, j) = \min_{i \leq k < j} \bigl( C(i, k) + C(k+1, j) + d_{i-1} \cdot d_k \cdot d_j \bigr)$$

with base case $C(i, i) = 0$. The table is an upper-triangular $n \times n$ matrix filled by increasing interval length $\ell = j - i$, so that when we compute $C(i, j)$ all shorter intervals are already filled. Time complexity is $O(n^3)$, with $O(n^2)$ space.

### The 0/1 Knapsack: DP Under Resource Constraints

The **0/1 knapsack problem** is the archetypal resource-constrained optimization problem and the standard demonstration that greedy algorithms fail in the absence of matroid structure. Given $n$ items, each with weight $w_i \in \mathbb{Z}_{>0}$ and value $v_i \geq 0$, and a knapsack with capacity $W$, we wish to maximize total value subject to total weight not exceeding $W$:

$$\text{maximize} \sum_{i=1}^{n} v_i x_i \quad \text{subject to} \sum_{i=1}^{n} w_i x_i \leq W, \quad x_i \in \{0, 1\}$$

The feasible sets (subsets of items fitting within capacity $W$) do not form a matroid: the augmentation property fails because adding a high-weight item from a larger feasible set can violate capacity, so no augmentation path is guaranteed. The value-to-weight ratio greedy heuristic fails even for tiny instances: consider $W = 10$, one item of weight 6 and value 10, and two items of weight 5 and value 7 each. The greedy heuristic picks the weight-6 item first (ratio $10/6 \approx 1.67$ versus $7/5 = 1.4$), yielding total value 10. The optimal solution takes both weight-5 items for value 14.

The DP formulation defines $dp[i][w]$ as the maximum value achievable using only items from $\{1, \ldots, i\}$ with total weight at most $w$. The recurrence is

$$dp[i][w] = \begin{cases} dp[i-1][w] & \text{if } w_i > w \\ \max\bigl(dp[i-1][w],\; v_i + dp[i-1][w - w_i]\bigr) & \text{if } w_i \leq w \end{cases}$$

with base cases $dp[0][w] = 0$ for all $w$ and $dp[i][0] = 0$ for all $i$. The table is filled row by row (item by item) from left to right (capacity $1$ to $W$). The time complexity is $O(nW)$ and space is $O(nW)$, reducible to $O(W)$ by observing that each row depends only on the previous row.

This $O(nW)$ complexity is **pseudopolynomial**: polynomial in the numeric value of $W$ but exponential in the bit-length $\log W$ of its binary representation. The 0/1 knapsack is NP-hard in the strong sense only when weights are exponentially large; for polynomially bounded $W$, the DP is tractable in practice.

The **unbounded knapsack** variant removes the $x_i \in \{0, 1\}$ restriction, allowing unlimited copies of each item. The recurrence simplifies to

$$dp[w] = \max_{1 \leq i \leq n,\, w_i \leq w}\bigl(v_i + dp[w - w_i]\bigr)$$

which fills a one-dimensional table of size $W + 1$ in $O(nW)$ time. The **fractional knapsack** (where items may be fractionally included) does admit a greedy solution: sort by $v_i / w_i$ descending and fill greedily. This is an exact solution because the feasible region for fractional knapsack is the intersection of a simplex with a hyperplane, a polymatroid, and greedy optimality over polymatroids is a known result.

### Execution Flow and Data Structures

The following diagrams illustrate the internal mechanics of Huffman coding and 0/1 knapsack tabulation, the two core algorithms of this lesson.

**Huffman Tree Construction (Min-Heap):**

```
Input frequencies: a:5, b:9, c:12, d:13, e:16, f:45

Step 1 — Min-Heap (by frequency):
[ 5:a | 9:b | 12:c | 13:d | 16:e | 45:f ]

Step 2 — Extract 5:a and 9:b, merge → 14:ab
[ 12:c | 13:d | 14:ab | 16:e | 45:f ]

Step 3 — Extract 12:c and 13:d, merge → 25:cd
[ 14:ab | 16:e | 25:cd | 45:f ]

Step 4 — Extract 14:ab and 16:e, merge → 30:abe
[ 25:cd | 30:abe | 45:f ]

Step 5 — Extract 25:cd and 30:abe, merge → 55:cdabe
[ 45:f | 55:cdabe ]

Step 6 — Extract 45:f and 55:cdabe, merge → 100:root

Final Tree:
              100
             /    \
           45:f   55
                 /   \
               25     30
              /  \   /  \
            12:c 13:d 14  16:e
                      / \
                    5:a  9:b

Codewords: f=0, c=100, d=101, a=1100, b=1101, e=111
```

**0/1 Knapsack DP Table Fill Order:**

```
Items: (w=2,v=3), (w=3,v=4), (w=4,v=5), (w=5,v=6)
Capacity W = 5

     w=0  w=1  w=2  w=3  w=4  w=5
i=0:  0    0    0    0    0    0
i=1:  0    0    3    3    3    3    ← item1(w=2,v=3)
i=2:  0    0    3    4    4    7    ← item2(w=3,v=4): 4+dp[1][2]=4+3=7
i=3:  0    0    3    4    5    7    ← item3(w=4,v=5): 5+dp[2][1]=5+0=5<7
i=4:  0    0    3    4    5    7    ← item4(w=5,v=6): 6+dp[3][0]=6<7

Optimal value: dp[4][5] = 7  (select items 1 and 2)
```

**Subproblem Dependency Graph (Interval DP):**

```
Interval lengths and fill order:

Length 1:  [1,1] [2,2] [3,3] [4,4]   ← base cases, cost = 0
              ↓     ↓     ↓     ↓
Length 2:  [1,2] [2,3] [3,4]          ← depend only on length-1 cells
              ↓     ↓     ↓
Length 3:  [1,3] [2,4]                ← depend on length-1 and length-2 cells
              ↓     ↓
Length 4:  [1,4]                      ← the full problem
```

The fill-order invariant for interval DP is that cell $[i, j]$ is computed only after all cells $[i, k]$ and $[k+1, j]$ for $i \leq k < j$ are populated. Iterating the outer loop over interval length $\ell = j - i$ guarantees this, since any sub-interval has strictly smaller length.

### Memoization vs. Tabulation: A Precise Comparison

Memoization and tabulation compute identical values but differ in their traversal of the subproblem DAG. Memoization performs a **depth-first traversal**: it follows the recursion down to base cases and fills the cache on the way back up, computing only those subproblems reachable from the top-level call. This is advantageous when the problem has sparse subproblem structure, meaning the optimal solution only touches a small fraction of all possible subproblems. The **longest common subsequence (LCS)** of two strings of length $m$ and $n$ has an $O(mn)$ table, but for inputs that are nearly identical, a memoized recursion with early termination may visit only $O(\min(m, n))$ distinct states.

Tabulation performs a **topological-order traversal**: it fills every cell in the table, regardless of whether that cell is needed. This eliminates recursive call overhead (no stack frames, no hash-map lookups for the cache), and it admits **space optimization** through rolling arrays. When the recurrence for row $i$ depends only on row $i - 1$, we maintain only two rows and alternate between them, reducing space from $O(nW)$ to $O(W)$ for knapsack or from $O(mn)$ to $O(\min(m,n))$ for LCS.

The choice between them is a function of problem structure. If the subproblem space is dense and all subproblems are needed, tabulation wins on constant factors. If the subproblem space is sparse or the recursion has natural pruning conditions, memoization wins on total work.

---

## 3. High-Performance Optimization & Failure Modes

### Identifying and Exploiting the SMAWK and Divide-and-Conquer Optimizations

For certain classes of DP recurrences, the $O(n^2)$ or $O(n^3)$ naive fill time is not tight. Two important structural properties, the **monotone minima property** and the **concave/convex SMAWK property**, allow inner-loop optimizations that reduce complexity.

The **divide-and-conquer DP optimization** applies when the recurrence has the form

$$dp[i][j] = \min_{k \leq j} \bigl(dp[i-1][k] + C(k, j)\bigr)$$

and the cost function $C$ satisfies the **quadrangle inequality**: $C(a, c) + C(b, d) \leq C(a, d) + C(b, c)$ for $a \leq b \leq c \leq d$. Under this condition, the optimal split point $k^*(i, j)$ (the $k$ achieving the minimum) is monotone in $j$: for a fixed row $i$, as $j$ increases, $k^*(i, j)$ never decreases. This allows the divide-and-conquer optimization: to compute all entries $dp[i][j]$ for $j \in [l, r]$, find the optimal $k$ for the midpoint $m = \lfloor(l+r)/2\rfloor$ by scanning $k \in [k^*(i, l), k^*(i, r)]$, then recurse on the left half with the updated left $k$-bound and the right half with the updated right $k$-bound. The total work per DP layer is $O(n \log n)$, reducing a $O(n^3)$ interval DP to $O(n^2 \log n)$.

The optimal BST problem (Knuth's algorithm) goes further: the quadrangle inequality for its cost function is tight enough that $k^*(i, j)$ satisfies $k^*(i, j-1) \leq k^*(i, j) \leq k^*(i+1, j)$, allowing the inner loop to run over a range of size proportional to the length of the adjacent intervals. This reduces the $O(n^3)$ interval DP to $O(n^2)$.

### The Bitset Optimization for Knapsack

For the 0/1 knapsack with boolean feasibility queries (can a subset of items achieve exactly weight $W$?), a bitset optimization reduces runtime by a factor of $64$ on 64-bit architectures. The DP state $dp$ is a bitset of length $W + 1$ where bit $w$ is set if weight $w$ is achievable. The transition for item $i$ with weight $w_i$ is

$$dp \leftarrow dp \;\mathtt{|}\; (dp \ll w_i)$$

This performs the entire DP transition for one item as a single bitwise OR of a bitshifted integer, which a 64-bit CPU executes across 64 bits simultaneously. For $W = 10^4$ and $n = 10^3$, the naive loop requires $10^7$ integer operations; the bitset requires $\lceil 10^4 / 64 \rceil \cdot 10^3 \approx 156{,}250$ 64-bit word operations. The asymptotic complexity becomes $O(nW / 64)$ in practice, a wall-clock speedup of roughly $64\times$.

### Greedy Failure Analysis: When the Matroid Condition Breaks

Understanding greedy failure is as important as understanding greedy correctness. The most common failure mode is applying a greedy algorithm to a problem whose feasibility structure violates the augmentation axiom. Consider the **set cover problem**: given a universe $U$ and a family of subsets $S_1, \ldots, S_m$, find the minimum number of subsets whose union is $U$. The greedy algorithm selects the subset covering the most uncovered elements at each step. This is not optimal: for $U = \{1, 2, 3, 4\}$ with subsets $\{1,2,3\}$, $\{2,3,4\}$, $\{1,4\}$, the greedy algorithm may select $\{1,2,3\}$ then $\{2,3,4\}$ (3 subsets), while the optimal is $\{1,2,3\}$ and $\{4\}$ or $\{1,4\}$ and $\{2,3,4\}$ (2 subsets). The feasibility structure is not a matroid because the augmentation axiom fails.

However, the greedy algorithm for set cover achieves an approximation ratio of $H_n = \sum_{k=1}^{n} 1/k \approx \ln n$ where $n = |U|$. This approximation bound is tight: for any $\epsilon > 0$, there exist instances for which no polynomial-time algorithm achieves ratio $(1 - \epsilon) \ln n$ unless P = NP (Feige, 1998). The greedy algorithm is thus not just a heuristic but a provably near-optimal polynomial-time strategy.

A subtler failure occurs in **greedy coloring** of graphs. The greedy algorithm colors vertices in some order, assigning each vertex the smallest color not used by its already-colored neighbors. The number of colors used depends heavily on the vertex ordering: for a bipartite graph (which needs only 2 colors), a bad ordering can force the greedy algorithm to use $\Theta(\sqrt{n})$ colors. The optimal coloring problem is NP-hard in general, and greedy provides no universal approximation guarantee without structural assumptions on the graph or ordering strategy.

### Failure Mode: Incorrect Subproblem Formulation in DP

The most common DP failure in practice is formulating subproblems that do not carry enough state to represent the global structure needed for optimal combination. Consider the problem of finding the **longest path in a directed acyclic graph (DAG)**: the DP is correct here because a DAG has no cycles, and the longest path to node $v$ is well-defined as the maximum over all predecessors $u$ of $v$ of (longest path to $u$) plus the edge weight $w(u,v)$. The subproblem $dp[v]$ captures exactly the state needed.

Now consider the same problem on a general directed graph (with possible cycles). The "subproblem" $dp[v]$ loses coherence because the optimal path to $v$ might pass through nodes that the path to $v$'s successors also passes through, violating the independence of subproblems. The longest path problem on general graphs is NP-hard, and DP fails not due to an implementation error but because optimal substructure does not hold: choosing an optimal path to some intermediate node $u$ can close off edges that a globally optimal path would need.

A more subtle instance of incorrect state arises in the **traveling salesman problem (TSP)**. The Held-Karp DP algorithm (1962) achieves $O(2^n n^2)$ time by defining the state as a subset $S \subseteq V$ of visited vertices plus the current vertex $v$, with $dp[S][v]$ being the minimum cost to visit exactly the vertices in $S$ starting from the origin and ending at $v$. The subset $S$ is essential: without tracking which vertices have been visited, the recurrence would conflate paths that visit the same current vertex via different sets of previously visited nodes, destroying optimality. The state space of $O(2^n \cdot n)$ is what makes TSP exponential, but it is the minimum state needed to maintain optimal substructure.

### Complexity Boundaries and the Pseudopolynomial Trap

The relationship between problem size and algorithm complexity deserves careful treatment for practitioners. The 0/1 knapsack DP runs in $O(nW)$ time, which looks polynomial. But $W$ is a numeric input parameter, not the size of the input encoding. If $W$ is specified in binary, its encoding length is $L = \lceil \log_2 W \rceil$ bits, and $W = 2^L$. The algorithm's runtime in terms of encoding length is $O(n \cdot 2^L)$, which is exponential. This is what **pseudopolynomial** means: polynomial in the numeric value of the input, exponential in its encoding length.

The practical implication is that the 0/1 knapsack DP is fast for small to moderate $W$ (up to roughly $10^6$ on modern hardware with bitset optimization) but completely impractical for large $W$ even with moderate $n$. For large $W$, approximation schemes such as the **fully polynomial time approximation scheme (FPTAS)** are the right tool: by scaling and rounding item values to $\hat{v}_i = \lfloor v_i / \theta \rfloor$ for a precision parameter $\theta = \epsilon \cdot v_{max} / n$, the rounded values satisfy $\hat{v}_i \leq n / \epsilon$, reducing the DP table size to $O(n^2 / \epsilon)$ and achieving a $(1 - \epsilon)$-approximation in $O(n^3 / \epsilon)$ time for any $\epsilon > 0$.

### Practical Implementation Invariants

Several implementation-level invariants determine the difference between a correct DP that times out and one that runs efficiently in practice.

For **space-optimized tabulation**, always identify whether row $i$ depends only on row $i-1$ before allocating the full table. For knapsack, iterating the capacity loop in reverse (from $W$ down to $w_i$) when updating a 1D table in-place prevents the double-counting that would arise from using updated values within the same item's transition:

```
for i in 1..n:
    for w in W..w[i]:       # reverse iteration prevents reuse within same item
        dp[w] = max(dp[w], v[i] + dp[w - w[i]])
```

For **interval DP**, always fill by increasing interval length before by left endpoint, never by left endpoint before by length. The incorrect order creates data dependencies where $C(i, j)$ is computed before $C(i, k)$ for $k < j$, producing silently wrong results rather than runtime errors.

For **memoization in recursive implementations**, the choice of cache data structure matters. A hash map is correct but slow for integer-keyed subproblems; a direct array indexed by the problem parameters is $O(1)$ access and far more cache-friendly. For multi-dimensional DP states, use a flat array with computed offsets rather than nested dynamic arrays to preserve spatial locality and avoid allocation overhead.

The discipline of algorithm design ultimately rests on the same foundation as mathematical proof: identifying the exact structural conditions under which a technique is valid, verifying those conditions for the problem at hand, and exploiting them to the fullest extent that correctness permits. Greedy algorithms are not shortcuts; they are the precise exploitation of matroid structure. Dynamic programming is not brute force with memory; it is the precise exploitation of optimal substructure and overlapping subproblems. The practitioner who understands both at this level will never misapply either.
