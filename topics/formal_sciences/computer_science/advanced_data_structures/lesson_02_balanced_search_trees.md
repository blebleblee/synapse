# Lesson 2: Self-Balancing Search Trees

## 1. First-Principles Intuition & Invariants

The binary search tree is one of the most elegant data structures in theoretical computer science: a recursively defined ordered structure where every node $x$ satisfies $\text{key}(\text{left}(x)) < \text{key}(x) < \text{key}(\text{right}(x))$, enabling search, insertion, and deletion in time proportional to the height $h$ of the tree. The fundamental problem is that this height is not guaranteed to be logarithmic. A sequence of insertions in sorted order degrades the BST into a linked list with $h = n$, destroying the $O(\log n)$ promise entirely. Self-balancing trees are the structural solution to this fragility: they maintain a height invariant through local restructuring operations after each modification, guaranteeing $h = O(\log n)$ regardless of insertion order.

To understand why logarithmic height is the correct target, observe that a complete binary tree on $n$ nodes has height $h = \lfloor \log_2 n \rfloor$. This is not merely a convenient bound but a structural necessity: if every node has two children, then the number of nodes at depth $d$ is $2^d$, and summing over all depths gives $n = \sum_{d=0}^{h} 2^d = 2^{h+1} - 1$, which inverts to $h = O(\log n)$. Any balance condition strong enough to prevent one subtree from growing arbitrarily larger than its sibling forces height to remain within a constant factor of this ideal.

The formal language for balance conditions is rooted in height functions and balance factors. For a node $x$ in a binary tree, define $h(x)$ as the length of the longest path from $x$ to a leaf. The **balance factor** of $x$ is $\text{bf}(x) = h(\text{right}(x)) - h(\text{left}(x))$. A tree is height-balanced in the AVL sense if $|\text{bf}(x)| \leq 1$ for every node $x$. This is precisely the invariant that Georgy Adelson-Velsky and Evgenii Landis formalized in their 1962 paper, giving us the first provably $O(\log n)$ self-balancing BST. The key theorem underlying AVL trees states that any AVL tree on $n$ nodes satisfies:

$$h \leq 1.44 \log_2(n + 2) - 0.328$$

**Proof.** Let $N(h)$ denote the minimum number of nodes in an AVL tree of height $h$. The worst case occurs when the two subtrees of the root differ in height by exactly one, giving the recurrence:

$$N(h) = N(h-1) + N(h-2) + 1$$

with base cases $N(0) = 1$ and $N(1) = 2$. This recurrence is structurally identical to the Fibonacci recurrence: defining $F_k$ as the $k$-th Fibonacci number, one can verify by induction that $N(h) = F_{h+3} - 1$. Since $F_k \sim \phi^k / \sqrt{5}$ where $\phi = (1 + \sqrt{5})/2 \approx 1.618$, we have $N(h) \approx \phi^{h+3}/\sqrt{5} - 1$. Solving for $h$ in terms of $n = N(h)$:

$$n + 1 \approx \frac{\phi^{h+3}}{\sqrt{5}} \implies h + 3 \approx \log_\phi(\sqrt{5}(n+1)) \implies h \leq \log_\phi(n+2) - 3 + 3$$

Converting to base 2 using $\log_\phi(x) = \log_2(x) / \log_2(\phi) \approx 1.44 \log_2(x)$ yields the stated bound. $\blacksquare$

Red-black trees encode balance through a coloring invariant rather than an explicit height measurement. A red-black tree is a BST where every node carries a color bit in $\{\text{Red}, \text{Black}\}$ satisfying four properties: the root is black; every null leaf (sentinel) is black; a red node has two black children (no two consecutive red nodes on any path); and all paths from any node to its descendant null leaves contain the same number of black nodes. This last quantity, the **black-height** $\text{bh}(x)$, is the core structural invariant. The height bound follows from the coloring rules.

**Lemma.** A red-black tree on $n$ internal nodes has height $h \leq 2 \log_2(n+1)$.

**Proof.** First, establish by induction that the subtree rooted at any node $x$ contains at least $2^{\text{bh}(x)} - 1$ internal nodes. The base case is a null leaf with $\text{bh} = 0$ containing $2^0 - 1 = 0$ nodes. For the inductive step, each child of $x$ has black-height at least $\text{bh}(x) - 1$ (exactly $\text{bh}(x) - 1$ if the child is black, $\text{bh}(x)$ if the child is red). By induction, each subtree has at least $2^{\text{bh}(x)-1} - 1$ nodes. The subtree at $x$ contains both subtrees plus $x$ itself:

$$\text{size}(x) \geq 2(2^{\text{bh}(x)-1} - 1) + 1 = 2^{\text{bh}(x)} - 1$$

Since no two consecutive nodes on a root-to-leaf path are red, at least half the nodes on any such path are black, giving $\text{bh}(\text{root}) \geq h/2$. Combining: $n \geq 2^{h/2} - 1$, which rearranges to $h \leq 2\log_2(n+1)$. $\blacksquare$

The 2-3-4 tree provides a third, conceptually distinct route to the same guarantee. Rather than constraining height differences between subtrees, the 2-3-4 tree abandons the fixed branching factor entirely: every internal node holds either one, two, or three keys, with two, three, or four children respectively, and all leaves sit at the same depth. This perfect leaf-depth uniformity trivially enforces $h = O(\log n)$: since every node has at least two children, $n \geq 2^h$, giving $h \leq \log_2 n$. The connection to red-black trees is not merely analogical but constitutes a formal isomorphism, which we will make explicit in Section 2.

B-trees generalize the 2-3-4 structure to arbitrary branching order $t \geq 2$, where every non-root node holds between $t-1$ and $2t-1$ keys. This generalization is motivated by external storage: when data lives on disk and each node access incurs an I/O, maximizing the branching factor minimizes the number of disk reads per operation. With $t$ chosen so that a node fills one disk block (typically 4KB or 8KB), a B-tree on $10^9$ keys has height at most $\log_t(5 \times 10^8) \approx 3$ for $t = 1000$, meaning every search touches at most three disk pages.

Weight-balanced trees and scapegoat trees represent a different philosophical lineage: rather than maintaining strict local invariants after every operation, they permit bounded imbalance and trigger rebuilding only when a global weight condition is violated. A **weight-balanced tree** (BB$[\alpha]$ tree, Nievergelt and Reingold 1973) maintains the invariant that for every node $x$ with left subtree $L$ and right subtree $R$, the weight $w(x) = |x| + 1$ (number of internal nodes plus one) satisfies:

$$\alpha \leq \frac{w(L)}{w(x)} \leq 1 - \alpha$$

for a fixed balance parameter $\alpha \in (1 - 1/\sqrt{2},\ 1/\sqrt{2}) \approx (0.293,\ 0.707)$. When a rotation or double rotation restores balance after a weight violation, the resulting subtree satisfies the invariant uniformly. A **scapegoat tree** (Galperin and Rivest 1993) is even more permissive: it permits the tree to become arbitrarily deep during a sequence of insertions, but after any insertion that causes the depth of the newly inserted node to exceed $\lfloor \log_{1/\alpha} n \rfloor$ for a fixed $\alpha \in (0.5, 1)$, it locates the highest ancestor $x$ where $\text{size}(\text{heavy-child}(x)) > \alpha \cdot \text{size}(x)$, calls this the scapegoat, and rebuilds the entire subtree at $x$ from scratch in $O(\text{size}(x))$ time. The amortized cost of rebuilding spreads across the insertions that caused the imbalance, yielding $O(\log n)$ amortized time per operation.

---

## 2. Core Architecture & Mechanics

### AVL Trees: Rotations as the Atomic Unit of Rebalancing

The rotation is the primitive operation underlying every BST rebalancing scheme. A **right rotation** at node $y$ promotes $y$'s left child $x$ to $y$'s position, making $y$ the right child of $x$ and $x$'s former right subtree $B$ the left subtree of $y$. The operation preserves the BST order property because the original in-order sequence $(\text{left}(x), x, B, y, \text{right}(y))$ is preserved after the rotation:

```text
      y                x
     / \              / \
    x   C    →       A   y
   / \                  / \
  A   B                B   C
```

The right rotation takes $O(1)$ time, touching only four pointer fields. Its mirror image, the left rotation, is symmetric. A **double rotation** (left-right or right-left) is the composition of two single rotations and handles the case where the imbalance arises from an "inner" subtree.

An AVL insertion proceeds as follows. First, perform a standard BST insertion, placing the new node as a leaf with $\text{bf} = 0$. Walk back up the insertion path toward the root, updating balance factors. At each ancestor $x$:

If $|\text{bf}(x)| \leq 1$ after update, the subtree at $x$ is still AVL-valid. If the height of $x$'s subtree did not change, propagation stops entirely. If $|\text{bf}(x)| = 2$, a rotation is needed. The specific case determines which rotation:

**Case 1 (Right-Right):** $\text{bf}(x) = +2$ and $\text{bf}(\text{right}(x)) \geq 0$. A single left rotation at $x$ restores balance.

**Case 2 (Left-Left):** $\text{bf}(x) = -2$ and $\text{bf}(\text{left}(x)) \leq 0$. A single right rotation at $x$ restores balance.

**Case 3 (Right-Left):** $\text{bf}(x) = +2$ and $\text{bf}(\text{right}(x)) < 0$. A right rotation at $\text{right}(x)$ followed by a left rotation at $x$.

**Case 4 (Left-Right):** $\text{bf}(x) = -2$ and $\text{bf}(\text{left}(x)) > 0$. A left rotation at $\text{left}(x)$ followed by a right rotation at $x$.

After any rotation, the height of the rotated subtree decreases by one relative to the pre-rotation state, so height propagation always terminates at or before the first rotation during insertion. Deletion is more involved: a single deletion can require up to $O(\log n)$ rotations because removing a node can cause height reductions that propagate all the way to the root.

### Red-Black Trees: Insertion and the Case Analysis

A red-black tree node carries five fields: $\{\text{key},\ \text{color},\ \text{left},\ \text{right},\ \text{parent}\}$. Null leaves are represented by a single shared sentinel node $T.\text{nil}$ colored black, which eliminates boundary condition checks throughout the implementation. Insertion colors the new node red and then repairs any red-red violation through a case analysis on the uncle's color.

Let $z$ be the newly inserted red node with parent $p = \text{parent}(z)$ and grandparent $g = \text{parent}(p)$ (guaranteed to exist since $p$ cannot be the root, as the root is black and $z$ is red). The uncle is $u = \text{sibling}(p)$.

**Case A (Red Uncle):** Recolor: set $p$ and $u$ to black, set $g$ to red. Move the violation pointer up to $g$ and repeat. This case propagates the violation upward at the cost of two recolorings but no rotations.

**Case B (Black Uncle, $z$ is an inner child):** A rotation at $p$ transforms this into Case C. Specifically, if $p$ is a left child and $z$ is a right child, perform a left rotation at $p$, swapping the roles of $z$ and $p$.

**Case C (Black Uncle, $z$ is an outer child):** Recolor $p$ to black and $g$ to red, then perform a rotation at $g$. This terminates the loop.

The total cost is $O(\log n)$ for traversal plus $O(1)$ rotations at termination. At most two rotations occur per insertion. Deletion is more elaborate, requiring a "double-black" abstraction to maintain the black-height invariant, but similarly completes in $O(\log n)$ time with at most three rotations.

### The 2-3-4 to Red-Black Isomorphism

Every 2-3-4 tree has a corresponding red-black tree, and vice versa. The correspondence maps each 2-3-4 node to a small cluster of red-black nodes: a 2-node (one key, two children) becomes a single black node. A 3-node (two keys $a < b$, three children) becomes a black node with key $b$ and a red left child with key $a$, or equivalently a black node with key $a$ and a red right child with key $b$. A 4-node (three keys $a < b < c$, four children) becomes a black node with key $b$, a red left child with key $a$, and a red right child with key $c$.

```text
2-node: [B]           →    B(black)

3-node: [A|B]         →    B(black)
                           /
                        A(red)

4-node: [A|B|C]       →    B(black)
                           / \
                       A(red) C(red)
```

This mapping is a bijection on tree shapes, and the red-black invariants correspond exactly to the structural constraints of the 2-3-4 tree. The black-height of a red-black tree equals the uniform depth of all leaves in the corresponding 2-3-4 tree. The no-consecutive-red rule corresponds to the fact that 2-3-4 nodes have at most three keys. This isomorphism is not merely pedagogical: it provides a clean mental model for the red-black insertion and deletion algorithms. A 4-node split in the 2-3-4 tree corresponds precisely to the Case A recoloring in red-black insertion.

### B-Trees: Block-Aligned Storage Architecture

A B-tree of minimum degree $t$ stores between $t-1$ and $2t-1$ keys per non-root node and between $t$ and $2t$ children per internal non-root node. The root holds between $1$ and $2t-1$ keys. All leaf nodes reside at the same depth. The height satisfies:

$$h \leq \log_t \frac{n+1}{2}$$

which follows from the minimum-branching argument: each non-root internal node has at least $t$ children, so the number of nodes at depth $d$ is at least $2t^{d-1}$ for $d \geq 1$, giving $n \geq 1 + (t-1)\sum_{d=1}^{h} 2t^{d-1} = 1 + 2(t^h - 1)$, from which $t^h \leq (n+1)/2$ and $h \leq \log_t((n+1)/2)$.

B-tree insertion uses a **proactive split** strategy to avoid a second upward pass. As the search descends to the insertion leaf, every full node ($2t-1$ keys) encountered along the path is split before descending into it. Splitting a full child $y$ of $x$ at position $i$ proceeds in $O(t)$ time:

A new node $z$ is allocated. The upper $t-1$ keys of $y$ (positions $t+1$ through $2t-1$) move to $z$, along with $y$'s upper $t$ children. The median key $y.\text{key}[t]$ moves up into $x$ at position $i$. Node $y$ now holds $t-1$ keys. This split increases the number of nodes by one and may propagate upward, but because every full node was split on the way down, the parent of any node being split is guaranteed to have room for the promoted median key.

```text
Before split of y (full, 2t-1 keys):
     x: [..., k_i, k_{i+1}, ...]
            |
            y: [k_1,...,k_{t-1} | k_t | k_{t+1},...,k_{2t-1}]

After split:
     x: [..., k_i, k_t, k_{i+1}, ...]
            |         |
     y:[k_1..k_{t-1}] z:[k_{t+1}..k_{2t-1}]
```

The choice of $t$ in practice is driven by the disk block size $B_{\text{block}}$ and the node record size $R$: set $t = \lfloor (B_{\text{block}} / R + 1) / 2 \rfloor$. For PostgreSQL's default 8KB page and a 16-byte key-pointer pair, $t \approx 250$, giving a tree of height at most 3 for tables with up to $10^9$ rows.

### Weight-Balanced Trees and Scapegoat Trees

A BB$[\alpha]$ tree augments each node with its subtree size $w$, computed as $w(x) = w(\text{left}(x)) + w(\text{right}(x)) + 1$, which costs $O(1)$ to maintain through any single rotation. The balance check at a node $x$ is:

$$\alpha \cdot w(x) \leq w(\text{left}(x)) \leq (1-\alpha) \cdot w(x)$$

A single rotation restores the invariant when $\alpha \leq 1 - 1/\sqrt{2}$, and a double rotation is needed in a narrow range near the boundary. The weight field also enables order-statistic operations: $\text{rank}(x)$ and $\text{select}(k)$ run in $O(\log n)$ without any additional augmentation, since the size of the left subtree gives the rank of the root within its subtree directly.

A scapegoat tree stores no balance information at all, only the keys, children, and a global counter of the current node count $n$ and the high-water mark $n_{\max}$ (the maximum value of $n$ since the last full rebuild). The balance parameter $\alpha \in (0.5, 1)$ controls the trade-off between memory waste and rebuild frequency. After an insertion that places a node at depth $d > \lfloor \log_{1/\alpha} n \rfloor$, the tree walks up the path from the new leaf, computing subtree sizes on the way, until it finds the scapegoat node $s$ where $\text{size}(\text{heavy-child}(s)) > \alpha \cdot \text{size}(s)$. The subtree at $s$ is flattened into a sorted array in $O(\text{size}(s))$ time by an in-order traversal, then rebuilt into a perfectly balanced BST in $O(\text{size}(s))$ time by recursively taking the median of each subarray as the root. The amortized analysis assigns a "credit" to each inserted node proportional to $\log_{1/\alpha} n$; the rebuild at $s$ is paid for by the credits of the nodes responsible for the imbalance.

---

## 3. High-Performance Optimization & Failure Modes

### Cache Locality and Node Layout

The dominant performance factor in production BST implementations is not the asymptotic operation count but cache behavior. A naive pointer-based BST with separately heap-allocated nodes causes one L1 cache miss per node visited during search, since there is no guarantee that parent and child reside in the same cache line. For a balanced BST of depth 20 on $10^6$ nodes, a lookup touches 20 nodes scattered across memory, potentially incurring 20 cache misses at 100ns each — a total of 2 microseconds, dominated by memory latency rather than computation.

The standard mitigation is **van Emde Boas layout** (also called cache-oblivious layout or recursive layout): arrange the nodes of the tree in memory in the order they appear in the recursive van Emde Boas tree decomposition, where the top $\lfloor h/2 \rfloor$ levels form one block and the bottom subtrees each form a contiguous block. This layout guarantees that any subtree of height $k$ fits within $O(2^k)$ contiguous cache lines, minimizing cache misses for any cache-line size without needing to know the cache parameters at build time. For a static or bulk-loaded tree, this layout is straightforward to implement during construction. For dynamic trees, it requires periodic rebuilding, which is natural for scapegoat trees but adds complexity to AVL or red-black implementations.

An alternative approach used in high-performance databases and B-tree libraries is **node chunking**: store four to eight keys per node in a small sorted array, with one pointer per key-interval boundary. This is effectively a B-tree with a small $t$, and the in-node linear scan over $2t-1 \leq 15$ keys fits entirely within two or three cache lines, reducing pointer indirection. The Intel x86 `SIMD` integer comparison instructions make the in-node search branchless and extremely fast in practice.

### Rotation Count and Structural Sharing

Red-black trees guarantee at most two rotations per insertion and at most three per deletion. AVL trees guarantee at most one rotation (single or double) per insertion but potentially $O(\log n)$ rotations per deletion. For workloads with far more insertions than deletions, AVL trees produce a flatter tree ($h \leq 1.44 \log_2 n$ versus $h \leq 2 \log_2 n$ for red-black trees) and therefore faster lookups. The difference is approximately 40% fewer comparisons per search in the worst case. For mixed workloads, red-black trees are preferred in most standard library implementations (C++ `std::map`, Java `TreeMap`, Linux kernel interval trees) because their deletion rotation bound is constant.

In a **functional** (purely persistent) setting, structural sharing changes the cost accounting substantially. A functional red-black tree cannot mutate nodes in place; each rotation or recoloring creates new nodes along the access path, leaving the old version intact for other references. Because an operation touches $O(\log n)$ nodes, it allocates $O(\log n)$ new node records. Scapegoat trees are extremely poorly suited to functional use: rebuilding a subtree of size $k$ allocates $O(k)$ new nodes. Weight-balanced trees and AVL trees are the standard choices for persistent maps in functional languages like Haskell's `Data.Map` and OCaml's `Map`, due to their bounded rotation counts and the resulting $O(\log n)$ allocation cost.

### Deletion Edge Cases and the Double-Black Invariant

Red-black deletion is the most error-prone algorithm in this family. The standard approach distinguishes two phases: first, perform the structural BST deletion (replacing the node with its in-order successor if it has two children, reducing to the case of at most one non-null child). Second, if the removed node was black, the black-height invariant is violated on the path where the node was removed. This violation is modeled by a **double-black** marker on the node that replaced the removed node (or on the null sentinel if the replacement is null). The fix-up loop propagates this double-black upward, consuming it through a case analysis:

When the double-black node's sibling is red, rotate at the parent and recolor to convert to a case with a black sibling. When the sibling is black with two black children, absorb the double-black by recoloring the sibling red and moving the double-black to the parent. When the sibling is black with at least one red child, a rotation at the parent (possibly preceded by a rotation at the sibling) terminates the loop.

A particularly subtle failure mode is the interaction between deletion and the sentinel node $T.\text{nil}$. Implementations that omit a proper sentinel and instead use raw null pointers must special-case color reads on null children throughout the fix-up procedure. A single missed null check causes undefined behavior in C or a null pointer exception in Java during tree traversal, often manifesting only on specific deletion sequences that reach the terminal cases of the fix-up loop. The correct discipline is to allocate $T.\text{nil}$ once at tree initialization, set its color to black, and ensure that all rotations and recolorings check identity against $T.\text{nil}$ rather than null.

### B-Tree Underflow and Merge/Redistribute

B-tree deletion must handle the **underflow** case: when a key is deleted from a leaf, the leaf may fall below the minimum of $t-1$ keys. The repair has two sub-cases. If an immediate sibling has $t$ or more keys, redistribute: rotate one key from the sibling through the parent into the deficient node, restoring the invariant without changing the tree's height. If both immediate siblings have exactly $t-1$ keys, merge: combine the deficient node, the median key from the parent, and one sibling into a single node of $2t-2$ keys, then delete the median key from the parent. This may cause the parent to underflow, propagating the merge upward. The worst case is a cascade of merges all the way to the root, reducing the tree height by one. While this is $O(h) = O(\log_t n)$ operations, each operation moves $O(t)$ keys, giving $O(t \log_t n)$ total work, which for large $t$ is dominated by the $O(t)$ cost of a single node operation at the leaf level.

The proactive split strategy during insertion has an analogous **proactive merge** strategy during deletion, sometimes called the **proactive fill** strategy: when descending to find the key to delete, if any node along the path has exactly $t-1$ keys (the minimum), immediately inflate it by either redistributing from a sibling or merging with a sibling. This ensures the deletion at the leaf never triggers a merge cascade, at the cost of potentially performing unnecessary merges on the way down. The two-pass approach (search, then fix-up on the way up) is simpler to reason about but requires the parent pointer or an explicit stack. High-performance B-tree implementations in databases like SQLite (which calls its B-tree pages "btrees" and stores entire pages in a memory-mapped buffer pool) use the proactive approach precisely because it avoids the need to track the upward path.

### Scapegoat Tree Rebuild Timing and Memory Reclamation

The scapegoat tree's $O(\log n)$ amortized bound relies on the invariant that $n \leq n_{\max}$, where $n_{\max}$ is the size after the last rebuild. If a workload consists of alternating single insertions and single deletions, $n_{\max}$ can grow without bound relative to $n$, never triggering a full rebuild but steadily increasing the allowed depth threshold $\lfloor \log_{1/\alpha} n_{\max} \rfloor$. The standard fix is to trigger a full tree rebuild whenever $n < n_{\max} / 2$, resetting $n_{\max} = n$. This ensures that $n_{\max} \leq 2n$ at all times, keeping the depth threshold at $O(\log n)$. Without this deletion trigger, a scapegoat tree degrades to $O(\log n_{\max})$ search time, which may grow to $O(n)$ over a long sequence of interleaved insertions and deletions.

The memory layout of the flattened-and-rebuilt subtree also warrants attention. A naive rebuild allocates the new nodes independently, reproducing the same cache-scattered layout as the original tree. A high-performance implementation allocates the entire rebuilt subtree as a single contiguous array, ordered by the van Emde Boas traversal described earlier. When the scapegoat is the root, this amounts to a full tree rebuild into a cache-optimal layout, which is a significant practical advantage: a workload that periodically triggers root-level scapegoat rebuilds will naturally maintain good cache locality without any explicit layout management.

### Comparative Summary of Structural Guarantees

The five tree families differ along axes that matter for practical selection. AVL trees offer the tightest height bound ($1.44 \log_2 n$) and constant rotations per insertion, making them optimal for lookup-heavy workloads where the tree is built once and queried many times. Red-black trees bound deletions to three rotations and are the standard choice for general-purpose mutable ordered maps in systems programming. 2-3-4 trees are pedagogically central and algorithmically equivalent to red-black trees but carry a constant-factor overhead from multi-key nodes. B-trees with large $t$ dominate external-memory and database index workloads because their I/O cost is determined by height alone, and maximizing $t$ to fill a disk block minimizes height. Weight-balanced trees are preferred when order-statistic operations ($\text{rank}$, $\text{select}$, $\text{split}$, $\text{join}$) must be supported alongside search, deletion, and insertion with uniform $O(\log n)$ cost, since the size augmentation is intrinsic to the balance condition itself. Scapegoat trees occupy a unique niche: they require no per-node balance information, minimizing node size, and are well-suited to memory-constrained environments or implementations where simplicity of the structural invariant outweighs the occasional $O(n)$ rebuild cost.

The formal property that unites all of them is the guarantee that the height $h$ satisfies $h = \Theta(\log n)$ under any insertion/deletion sequence, ensuring that the $O(h)$ operations of search, predecessor, successor, insertion, and deletion all run in $O(\log n)$ time. The differences are constant factors in height, rotation counts, and node size — but in systems where these constant factors translate directly into cache misses, disk I/Os, or memory footprint, choosing the right variant is an engineering decision with measurable consequences.
