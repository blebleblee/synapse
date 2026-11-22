# Lesson 2: Linear Transformations, Matrix Representations, Kernel, Image

## 1. First-Principles Intuition & Invariants

The story of linear algebra is ultimately a story about *structure-preserving maps*. A vector space, standing alone, is a purely algebraic object: a set equipped with two operations, addition and scalar multiplication, satisfying eight familiar axioms. But a vector space in isolation is an abstraction with no leverage. The power of the theory emerges the moment you study maps *between* vector spaces, maps that respect the algebraic structure, and ask: what is preserved, what is collapsed, and what is revealed about the spaces themselves by the maps that connect them?

A **linear transformation** (also called a linear map, or in the language of algebra, a vector space homomorphism) is a function $T: V \to W$ between vector spaces $V$ and $W$ over a common field $\mathbb{F}$ satisfying two invariants. First, additivity: $T(u + v) = T(u) + T(v)$ for all $u, v \in V$. Second, homogeneity: $T(\alpha v) = \alpha T(v)$ for all $\alpha \in \mathbb{F}$ and $v \in V$. These two conditions collapse into a single identity, $T(\alpha u + \beta v) = \alpha T(u) + \beta T(v)$, which asserts that $T$ intertwines linear combinations. Whatever linear dependencies exist among vectors in $V$ are faithfully transported, or at worst collapsed but never fabricated, into $W$.

This is a profound constraint. It means a linear map is entirely determined by its action on a basis. If $\{e_1, e_2, \ldots, e_n\}$ is a basis for $V$, and you know $T(e_1), T(e_2), \ldots, T(e_n) \in W$, then for any vector $v = \sum_{i=1}^n c_i e_i$ you have:

$$T(v) = T\!\left(\sum_{i=1}^n c_i e_i\right) = \sum_{i=1}^n c_i\, T(e_i)$$

No further information about $T$ is needed or possible. This is the first great invariant of the theory: the value of a linear map is entirely encoded in the images of basis vectors, and conversely, any assignment of basis vectors to arbitrary target vectors extends uniquely to a linear map. This gives a complete classification of all linear maps $V \to W$ when $V$ is finite-dimensional.

### The Kernel and Image as Fundamental Subspaces

Every linear map $T: V \to W$ canonically carves two subspaces out of the ambient spaces. The **kernel** (or null space) of $T$ is:

$$\ker T = \{v \in V : T(v) = 0_W\}$$

This is the set of all vectors in the domain that $T$ annihilates. It is a subspace of $V$: it contains $0_V$ since $T(0_V) = 0_W$ by linearity, and it is closed under addition and scalar multiplication because if $T(u) = T(v) = 0_W$ then $T(\alpha u + \beta v) = \alpha T(u) + \beta T(v) = 0_W$. The kernel measures exactly how far $T$ is from being injective. Indeed, $T$ is injective if and only if $\ker T = \{0_V\}$, since if $T(u) = T(v)$ then $T(u - v) = 0_W$ implies $u - v \in \ker T$, and when $\ker T$ is trivial this forces $u = v$.

The **image** (or range) of $T$ is:

$$\operatorname{im} T = \{T(v) : v \in V\} \subseteq W$$

This is a subspace of $W$: the zero vector of $W$ lies in $\operatorname{im} T$, and the image is closed under linear combinations because $\alpha T(u) + \beta T(v) = T(\alpha u + \beta v)$, which is the image of $\alpha u + \beta v \in V$. The image measures how much of $W$ is actually reached by $T$. The map $T$ is surjective precisely when $\operatorname{im} T = W$.

The sizes of these subspaces are related by one of the most fundamental theorems in all of linear algebra.

### The Rank-Nullity Theorem

**Theorem (Rank-Nullity).** Let $T: V \to W$ be a linear map with $V$ finite-dimensional. Then:

$$\dim(\ker T) + \dim(\operatorname{im} T) = \dim V$$

The two quantities have standard names: $\dim(\ker T)$ is the **nullity** of $T$, written $\text{null}(T)$, and $\dim(\operatorname{im} T)$ is the **rank** of $T$, written $\text{rank}(T)$.

The proof is constructive and illuminating. Let $\{u_1, \ldots, u_k\}$ be a basis for $\ker T$, where $k = \text{null}(T)$. Since $V$ is finite-dimensional, extend this to a basis of $V$ by adjoining vectors $\{v_1, \ldots, v_r\}$, so that $\{u_1, \ldots, u_k, v_1, \ldots, v_r\}$ is a basis for $V$ with $k + r = \dim V$.

The claim is that $\{T(v_1), \ldots, T(v_r)\}$ is a basis for $\operatorname{im} T$.

**Spanning:** Any $w \in \operatorname{im} T$ has the form $T(v)$ for some $v \in V$. Write $v = \sum_{i=1}^k a_i u_i + \sum_{j=1}^r b_j v_j$. Then:

$$w = T(v) = \sum_{i=1}^k a_i T(u_i) + \sum_{j=1}^r b_j T(v_j) = \sum_{j=1}^r b_j T(v_j)$$

since each $u_i \in \ker T$ contributes zero. So $\{T(v_1), \ldots, T(v_r)\}$ spans $\operatorname{im} T$.

**Linear independence:** Suppose $\sum_{j=1}^r b_j T(v_j) = 0_W$. Then $T\!\left(\sum_{j=1}^r b_j v_j\right) = 0_W$, which means $\sum_{j=1}^r b_j v_j \in \ker T$. Since $\{u_1, \ldots, u_k\}$ is a basis for $\ker T$, there exist scalars $a_i$ such that:

$$\sum_{j=1}^r b_j v_j = \sum_{i=1}^k a_i u_i$$

Rearranging, $\sum_{i=1}^k (-a_i) u_i + \sum_{j=1}^r b_j v_j = 0$. Since $\{u_1, \ldots, u_k, v_1, \ldots, v_r\}$ is a basis for $V$, all coefficients are zero: each $b_j = 0$. This establishes linear independence.

Therefore $\{T(v_1), \ldots, T(v_r)\}$ is a basis for $\operatorname{im} T$, so $\dim(\operatorname{im} T) = r$. The theorem follows: $\text{null}(T) + \text{rank}(T) = k + r = \dim V$. $\blacksquare$

The rank-nullity theorem is not merely a counting result. It encodes a *conservation law* for dimension: dimension that is annihilated by $T$ (falling into the kernel) is precisely the dimension lost from the image. Nothing is created; the domain's dimension is partitioned between collapse and survival.

### Isomorphisms and the Classification of Finite-Dimensional Vector Spaces

A linear map that is both injective and surjective is called a **linear isomorphism**, and the spaces $V$ and $W$ are then said to be **isomorphic**, written $V \cong W$. An isomorphism is simultaneously an algebraic and structural equivalence: the two spaces are, for all purposes of linear algebra, the same object. The inverse $T^{-1}: W \to V$ is also linear, since $(T^{-1})(\alpha w_1 + \beta w_2) = T^{-1}(\alpha T(v_1) + \beta T(v_2)) = T^{-1}(T(\alpha v_1 + \beta v_2)) = \alpha v_1 + \beta v_2 = \alpha T^{-1}(w_1) + \beta T^{-1}(w_2)$.

The rank-nullity theorem immediately yields the classification theorem for finite-dimensional spaces: *two finite-dimensional vector spaces over the same field are isomorphic if and only if they have the same dimension*. If $\dim V = \dim W = n$, then any bijection of a basis of $V$ onto a basis of $W$ extends to an isomorphism. Conversely, an isomorphism $T: V \to W$ has $\ker T = \{0\}$ and $\operatorname{im} T = W$, so by rank-nullity $\dim V = 0 + \dim W$. Every $n$-dimensional vector space over $\mathbb{F}$ is therefore isomorphic to the coordinate space $\mathbb{F}^n$, which is the theoretical foundation for representing abstract vectors as tuples of scalars.

---

## 2. Core Architecture & Mechanics

### From Maps to Matrices: The Coordinate Representation

The classification above tells us that every finite-dimensional abstract vector space is a disguised copy of $\mathbb{F}^n$, but it does more: it tells us that every linear map between finite-dimensional spaces is a disguised copy of a matrix multiplication. This is the bridge between the coordinate-free theory and the computational machinery of matrices.

Let $V$ be an $n$-dimensional vector space with ordered basis $\mathcal{B} = (e_1, \ldots, e_n)$, and $W$ an $m$-dimensional vector space with ordered basis $\mathcal{C} = (f_1, \ldots, f_m)$. The **coordinate isomorphisms** $[\,\cdot\,]_\mathcal{B}: V \to \mathbb{F}^n$ and $[\,\cdot\,]_\mathcal{C}: W \to \mathbb{F}^m$ are defined by:

$$[v]_\mathcal{B} = \begin{pmatrix} c_1 \\ \vdots \\ c_n \end{pmatrix} \quad \text{where } v = \sum_{i=1}^n c_i e_i$$

For the linear map $T: V \to W$, each basis vector $e_j$ maps to some vector $T(e_j) \in W$, which has a unique expansion in the basis $\mathcal{C}$:

$$T(e_j) = \sum_{i=1}^m a_{ij} f_i$$

The **matrix of $T$ with respect to $\mathcal{B}$ and $\mathcal{C}$** is the $m \times n$ matrix $[T]_{\mathcal{B}}^{\mathcal{C}}$ whose $j$-th column is $[T(e_j)]_\mathcal{C}$:

$$[T]_{\mathcal{B}}^{\mathcal{C}} = \begin{pmatrix} a_{11} & a_{12} & \cdots & a_{1n} \\ a_{21} & a_{22} & \cdots & a_{2n} \\ \vdots & \vdots & \ddots & \vdots \\ a_{m1} & a_{m2} & \cdots & a_{mn} \end{pmatrix}$$

The fundamental computational fact is that this matrix converts coordinate vectors: $[T(v)]_\mathcal{C} = [T]_{\mathcal{B}}^{\mathcal{C}} \cdot [v]_\mathcal{B}$. The proof is a direct calculation. Write $v = \sum_{j=1}^n c_j e_j$, so $[v]_\mathcal{B} = (c_1, \ldots, c_n)^T$. Then:

$$T(v) = \sum_{j=1}^n c_j T(e_j) = \sum_{j=1}^n c_j \sum_{i=1}^m a_{ij} f_i = \sum_{i=1}^m \left(\sum_{j=1}^n a_{ij} c_j\right) f_i$$

The coefficient of $f_i$ in this expansion is $\sum_{j=1}^n a_{ij} c_j$, which is exactly the $i$-th entry of the matrix product $[T]_{\mathcal{B}}^{\mathcal{C}} \cdot [v]_\mathcal{B}$. The abstract map and the matrix product are the same thing, seen through the lens of coordinates.

The composition law for matrices follows immediately. If $S: U \to V$ and $T: V \to W$ are linear maps with bases $\mathcal{A}, \mathcal{B}, \mathcal{C}$ on $U, V, W$ respectively, then:

$$[T \circ S]_\mathcal{A}^\mathcal{C} = [T]_\mathcal{B}^\mathcal{C} \cdot [S]_\mathcal{A}^\mathcal{B}$$

This is not a convention but a theorem: matrix multiplication was *defined* to make composition of linear maps correspond to multiplication of their matrices.

### The Flow of Information: A Structural Diagram

The relationship between the abstract map $T$, its coordinate representation, and the resulting matrix algebra can be organized as a commutative diagram. The commutativity of this square is the content of the representation theorem.

```mermaid
flowchart TD
    T["T"]
    V["V"]
    W["W"]
    F_n["F^n"]
    F_m["F^m"]
    
    T --> V
    T --> W
    V -->|"[·]_B"| F_n
    W -->|[·]_C| F_m
    F_n -->|"[T]_B^C · (–)"| F_m
```

The two paths from $V$ to $\mathbb{F}^m$ produce the same result: apply $T$ then coordinatize, or coordinatize then multiply by $[T]_\mathcal{B}^\mathcal{C}$. The diagram commutes, meaning:

$$[\,T(v)\,]_\mathcal{C} = [T]_\mathcal{B}^\mathcal{C} \cdot [\,v\,]_\mathcal{B}$$

This commutativity is not a coincidence; it is the precise sense in which the matrix *represents* the map. The map $T$ is the geometric, coordinate-free object. The matrix is its numerical shadow, cast by a choice of bases.

### Kernel and Image from the Matrix

Once $T$ is represented by a matrix $A = [T]_\mathcal{B}^\mathcal{C}$, the kernel and image admit immediate computational descriptions. The kernel of $T$ corresponds, via the basis isomorphism, to the **null space** of $A$: the set of vectors $x \in \mathbb{F}^n$ satisfying $Ax = 0$. Finding a basis for this null space is exactly the task of solving a homogeneous linear system, accomplished by reducing $A$ to row echelon form via elementary row operations (which are themselves linear maps from $\mathbb{F}^m$ to $\mathbb{F}^m$, specifically the left-multiplication by elementary matrices).

The image of $T$ corresponds to the **column space** of $A$: the span of the columns of $A$ in $\mathbb{F}^m$. Each column $A_j$ of $A$ is $[T(e_j)]_\mathcal{C}$, so:

$$\operatorname{im} T \cong \operatorname{col}(A) = \operatorname{span}\{A_1, A_2, \ldots, A_n\}$$

The rank of $A$, defined as the number of pivot columns in its row echelon form, equals $\dim(\operatorname{col}(A)) = \dim(\operatorname{im} T)$. The rank-nullity theorem then becomes the matrix equation:

$$\text{rank}(A) + \text{nullity}(A) = n$$

where $n$ is the number of columns. This is a purely algebraic fact about the matrix, but its proof is the same theorem proved above, now read through coordinates.

A critical invariant: the row rank of $A$ (dimension of its row space) equals the column rank. This non-obvious fact, proved by showing both equal the number of non-zero rows in the reduced row echelon form, means the rank is an intrinsic property of the matrix, independent of whether you count linearly independent rows or columns. Algorithmically, row reduction transforms $A$ into reduced row echelon form (RREF), from which both a basis for the null space and a basis for the column space can be read directly.

### Change of Basis and Similarity

A single linear transformation $T: V \to V$ (an **endomorphism**, where domain and codomain are the same space) can be represented by different matrices depending on which basis is chosen for $V$. Understanding how the matrix changes under a change of basis is essential for finding canonical forms and simplifying computations.

Let $\mathcal{B} = (e_1, \ldots, e_n)$ and $\mathcal{B}' = (e_1', \ldots, e_n')$ be two ordered bases of $V$. The **change-of-basis matrix** from $\mathcal{B}'$ to $\mathcal{B}$ is the matrix $P$ whose $j$-th column is $[e_j']_\mathcal{B}$, the coordinate vector of the new basis vector $e_j'$ expressed in the old basis. This matrix $P$ is invertible (since it represents the coordinate isomorphism from $\mathcal{B}'$-coordinates to $\mathcal{B}$-coordinates, and both are bases), and:

$$[v]_\mathcal{B} = P \cdot [v]_{\mathcal{B}'}$$

Now let $A = [T]_\mathcal{B}$ and $A' = [T]_{\mathcal{B}'}$ be the matrices of $T$ in the two bases. To transform $v$-coordinates to $T(v)$-coordinates in $\mathcal{B}'$, the following path through the commutative diagram applies:

$$[T(v)]_{\mathcal{B}'} = P^{-1} [T(v)]_\mathcal{B} = P^{-1} A [v]_\mathcal{B} = P^{-1} A \, P [v]_{\mathcal{B}'}$$

Therefore $A' = P^{-1} A P$. Two matrices related by this equation are called **similar**. The fundamental insight is: *similar matrices are coordinate representations of the same linear map in different bases*. Similarity is an equivalence relation on the set of $n \times n$ matrices, and each equivalence class corresponds to exactly one linear endomorphism of $\mathbb{F}^n$ (up to the identification of abstract spaces with coordinate spaces).

The goal of much of the deeper theory, including eigenvalue theory, Jordan normal form, and rational canonical form, is to find, for a given matrix $A$, the simplest possible similar matrix, that is, the basis in which $T$ looks most transparent. The diagonal form is the ideal case: a matrix is diagonalizable if and only if $V$ has a basis of eigenvectors of $T$, in which case $A' = \text{diag}(\lambda_1, \ldots, \lambda_n)$ where the $\lambda_i$ are the eigenvalues.

---

## 3. High-Performance Optimization & Failure Modes

### Working Coordinate-Free: When Abstraction Is the Right Tool

A recurring mistake, even among experienced students, is to reach for coordinates too quickly. Many theorems about linear maps are most cleanly proved and most deeply understood in the coordinate-free language of kernels, images, and linear maps, without any choice of basis. Choosing coordinates prematurely forces you to carry the weight of a specific representation through every calculation, introduces opportunities for error, and often obscures the invariant content of what you are proving.

Consider the following important result. If $T: V \to W$ and $S: W \to X$ are linear maps, then:

$$\dim(\ker(S \circ T)) \leq \dim(\ker S) + \dim(\ker T)$$

A coordinate proof would require setting up three systems of coordinates and tracking indices. The coordinate-free proof is immediate: define the restriction $T|_{\ker(S \circ T)}: \ker(S \circ T) \to W$. The image of this restriction lands inside $\ker S$, since for $v \in \ker(S \circ T)$ we have $S(T(v)) = 0$. By the rank-nullity theorem applied to this restriction:

$$\dim(\ker(S \circ T)) = \dim(\ker T \cap \ker(S \circ T)) + \dim(\operatorname{im}(T|_{\ker(S \circ T)}))$$

$$\leq \dim(\ker T) + \dim(\ker S)$$

The coordinate-free argument is two lines. The lesson: choose the level of abstraction that matches the invariant content of the problem. Coordinate arguments are indispensable for computation and for concrete examples, but they are often the wrong tool for proving structural theorems.

### Rank, the Four Fundamental Subspaces, and the Failure of Invertibility

For a linear map $T: V \to W$ represented by an $m \times n$ matrix $A$, four subspaces partition the linear-algebraic content of $T$ into a complete picture. The **column space** $\operatorname{col}(A) \subseteq \mathbb{F}^m$ and the **null space** $\operatorname{null}(A) \subseteq \mathbb{F}^n$ are the image and kernel already encountered. Their orthogonal complements (when working over $\mathbb{R}$ or $\mathbb{C}$ with an inner product) give the **row space** $\operatorname{row}(A) \subseteq \mathbb{F}^n$ and the **left null space** $\operatorname{null}(A^T) \subseteq \mathbb{F}^m$.

The rank-nullity theorem and its transpose give:

$$\dim(\operatorname{col}(A)) + \dim(\operatorname{null}(A^T)) = m$$
$$\dim(\operatorname{row}(A)) + \dim(\operatorname{null}(A)) = n$$

and the row-rank equals column-rank equality gives $\dim(\operatorname{col}(A)) = \dim(\operatorname{row}(A)) = \text{rank}(A)$. These four dimensions are constrained by the single integer $r = \text{rank}(A)$, the fundamental invariant of $T$.

This framework immediately diagnoses the failure modes of linear systems. The equation $Ax = b$ has: a solution if and only if $b \in \operatorname{col}(A)$; a unique solution if and only if $b \in \operatorname{col}(A)$ and $\operatorname{null}(A) = \{0\}$; infinitely many solutions (a coset of the null space) when $b \in \operatorname{col}(A)$ and $\operatorname{null}(A) \neq \{0\}$; and no solution when $b \notin \operatorname{col}(A)$.

### Numerical Rank Deficiency and the Instability of Near-Singular Maps

In applications to numerical linear algebra and theoretical computer science, the rank-nullity theorem interacts with floating-point arithmetic in a subtle and dangerous way. A matrix may be theoretically full rank but *numerically rank deficient*: its smallest singular value $\sigma_{\min}$ may be extremely small, making the map $T$ nearly singular without technically being singular. The condition number $\kappa(A) = \sigma_{\max} / \sigma_{\min}$ measures this instability. When $\kappa(A)$ is large, small perturbations to $b$ produce large changes in the solution $x = A^{-1}b$, and the computed null space (from floating-point row reduction) may be misleading.

The correct tool for this regime is the **singular value decomposition** (SVD): $A = U \Sigma V^T$ where $U, V$ are orthogonal matrices and $\Sigma = \text{diag}(\sigma_1, \ldots, \sigma_r, 0, \ldots, 0)$ with $\sigma_1 \geq \sigma_2 \geq \cdots \geq \sigma_r > 0$. The SVD gives a basis for each of the four fundamental subspaces from the columns of $U$ and $V$, and the numerical rank is determined by counting singular values above a chosen threshold $\epsilon$. This is the basis for the **pseudoinverse** $A^+ = V \Sigma^+ U^T$, which provides the minimum-norm least-squares solution when $T$ is not invertible, minimizing $\|Ax - b\|_2$ subject to minimizing $\|x\|_2$.

### Change of Basis: Computational Strategy and Common Errors

When changing bases to simplify a matrix, the most common error is inverting $P$ in the wrong direction. The mnemonic is this: the change-of-basis matrix $P$ *from $\mathcal{B}'$ to $\mathcal{B}$* has the new basis vectors as its *columns*, expressed in the old basis. To transform the matrix of $T$ from $\mathcal{B}$ to $\mathcal{B}'$, compute $A' = P^{-1} A P$, with $P^{-1}$ on the left and $P$ on the right. The left multiplication by $P^{-1}$ converts output coordinates back from $\mathcal{B}$ to $\mathcal{B}'$; the right multiplication by $P$ converts input coordinates from $\mathcal{B}'$ to $\mathcal{B}$.

A fully worked example clarifies the mechanics. Let $T: \mathbb{R}^2 \to \mathbb{R}^2$ be defined by $T(x, y) = (3x + y,\, x + 3y)$, so the standard-basis matrix is:

$$A = \begin{pmatrix} 3 & 1 \\ 1 & 3 \end{pmatrix}$$

The eigenvalues are found from $\det(A - \lambda I) = (3 - \lambda)^2 - 1 = 0$, giving $\lambda^2 - 6\lambda + 8 = 0$, so $\lambda_1 = 4$ and $\lambda_2 = 2$. The eigenvectors are $v_1 = (1, 1)^T$ for $\lambda_1 = 4$ and $v_2 = (1, -1)^T$ for $\lambda_2 = 2$. Setting $P = \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$, the inverse is $P^{-1} = \frac{1}{-2}\begin{pmatrix} -1 & -1 \\ -1 & 1 \end{pmatrix} = \begin{pmatrix} 1/2 & 1/2 \\ 1/2 & -1/2 \end{pmatrix}$. Then:

$$P^{-1} A P = \begin{pmatrix} 1/2 & 1/2 \\ 1/2 & -1/2 \end{pmatrix} \begin{pmatrix} 3 & 1 \\ 1 & 3 \end{pmatrix} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$$

Computing the right product first: $AP = \begin{pmatrix} 4 & 2 \\ 4 & -2 \end{pmatrix}$. Then:

$$P^{-1}(AP) = \begin{pmatrix} 1/2 & 1/2 \\ 1/2 & -1/2 \end{pmatrix}\begin{pmatrix} 4 & 2 \\ 4 & -2 \end{pmatrix} = \begin{pmatrix} 4 & 0 \\ 0 & 2 \end{pmatrix} = \operatorname{diag}(4, 2)$$

The map $T$, which looks like a coupled system in standard coordinates, is revealed in the eigenbasis as a pure rescaling: stretch by a factor of $4$ along $(1,1)$ and by a factor of $2$ along $(1,-1)$. The abstract structure of $T$ was always a diagonal map; the standard basis simply hid this fact.

### The First Isomorphism Theorem for Vector Spaces

The deepest structural result governing linear maps is the vector space version of the First Isomorphism Theorem, which the reader will recognize as an exact analogue of the group-theoretic result $G / \ker\phi \cong \text{im}\,\phi$.

**Theorem.** Let $T: V \to W$ be a linear map. Then there is a canonical isomorphism:

$$V / \ker T \;\cong\; \operatorname{im} T$$

Here $V / \ker T$ is the **quotient space**: the set of cosets $v + \ker T = \{v + u : u \in \ker T\}$, equipped with the vector space structure $(v_1 + \ker T) + (v_2 + \ker T) = (v_1 + v_2) + \ker T$ and $\alpha(v + \ker T) = \alpha v + \ker T$. The dimension of this quotient space is $\dim V - \dim(\ker T) = \text{rank}(T)$, which is exactly $\dim(\operatorname{im} T)$, consistent with rank-nullity.

The isomorphism $\tilde{T}: V / \ker T \to \operatorname{im} T$ is defined by $\tilde{T}(v + \ker T) = T(v)$. This is well-defined: if $v + \ker T = v' + \ker T$, then $v - v' \in \ker T$, so $T(v - v') = 0$ and $T(v) = T(v')$. It is linear by direct verification, surjective since $\operatorname{im} T = \operatorname{im} \tilde{T}$, and injective since $\tilde{T}(v + \ker T) = 0$ implies $T(v) = 0$ implies $v \in \ker T$ implies $v + \ker T = 0 + \ker T$, the zero coset. So $\tilde{T}$ is an isomorphism. $\blacksquare$

The First Isomorphism Theorem completes the coordinate-free picture of a linear map: $T$ collapses the kernel to zero, passes through an isomorphism on the quotient, and embeds the result into $W$. Everything that happens in a linear map factors through this canonical decomposition. Matrix rank, the solvability of linear systems, the existence of left and right inverses, and the theory of projections and direct sums all flow from this single structural theorem, which reveals a linear map not as an arbitrary function but as a precisely structured morphism carrying an exact signature: the dimension of what it destroys and the dimension of what it creates.
