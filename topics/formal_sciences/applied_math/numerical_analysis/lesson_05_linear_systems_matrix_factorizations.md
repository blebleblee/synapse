# Lesson 5: Direct Methods for Linear Systems, Matrix Factorizations, Stability

## 1. First-Principles Intuition & Invariants

The central computational problem of numerical linear algebra is the solution of the linear system $Ax = b$, where $A \in \mathbb{R}^{n \times n}$ is a given nonsingular matrix and $b \in \mathbb{R}^n$ is a given vector. Direct methods solve this problem in a finite number of steps, transforming the original matrix into a product of simpler factors whose structure makes the solve immediate. The defining virtue of a direct method is its determinism: there are no convergence tolerances to tune, no iteration counts to guess, and the total arithmetic cost is a known polynomial in $n$. The defining challenge is that every arithmetic operation in floating-point introduces a small relative error, and over the course of millions of operations these errors compound. The central question of this lesson is not merely how to factor a matrix, but how to understand the gap between the computed solution $\hat{x}$ and the true solution $x$ in terms of two quantities: the backward error introduced by the algorithm and the intrinsic sensitivity of the problem as measured by the condition number.

The condition number of a nonsingular matrix $A$ with respect to a subordinate matrix norm $\|\cdot\|$ is defined as $\kappa(A) = \|A\| \, \|A^{-1}\|$. This single quantity governs how perturbations in the input data propagate to the solution. To see this precisely, suppose that the data $A$ and $b$ are perturbed to $A + \Delta A$ and $b + \Delta b$, and let the perturbed solution satisfy $(A + \Delta A)(x + \Delta x) = b + \Delta b$. Expanding and using $Ax = b$ gives $A\,\Delta x = \Delta b - \Delta A\,x - \Delta A\,\Delta x$, which rearranges to $\Delta x = A^{-1}(\Delta b - \Delta A\,x) - A^{-1}\Delta A\,\Delta x$. Taking norms and applying the triangle inequality yields

$$\|\Delta x\| \leq \|A^{-1}\|\bigl(\|\Delta b\| + \|\Delta A\|\,\|x\|\bigr) + \|A^{-1}\|\,\|\Delta A\|\,\|\Delta x\|.$$

Collecting the $\|\Delta x\|$ terms on the left and dividing by $\|x\|$ (noting that $\|b\| \leq \|A\|\,\|x\|$, so $\|x\| \geq \|b\|/\|A\|$), we obtain the fundamental perturbation bound:

$$\frac{\|\Delta x\|}{\|x\|} \leq \frac{\kappa(A)\!\left(\frac{\|\Delta b\|}{\|b\|} + \frac{\|\Delta A\|}{\|A\|}\right)}{1 - \kappa(A)\frac{\|\Delta A\|}{\|A\|}},$$

valid provided $\kappa(A)\frac{\|\Delta A\|}{\|A\|} < 1$. The numerator shows that the relative error in the solution is amplified by $\kappa(A)$ relative to the relative errors in the data, and the denominator reveals that when $\kappa(A)\frac{\|\Delta A\|}{\|A\|}$ approaches unity, the bound blows up entirely—the perturbed matrix becomes singular and the solution ceases to exist in any meaningful sense. A matrix with $\kappa(A) \approx 1$ is called well-conditioned; one with $\kappa(A) \gg 1$ is ill-conditioned. The Hilbert matrix $H_{ij} = 1/(i+j-1)$, a classic example from interpolation and quadrature, has $\kappa(H_{10}) \approx 1.6 \times 10^{13}$, meaning that in double precision (with unit roundoff $u \approx 1.1 \times 10^{-16}$) one can expect to lose roughly 13 digits of accuracy.

The concept of backward stability, introduced systematically by James Wilkinson in the 1960s, provides the bridge between algorithm design and the perturbation bound above. An algorithm for solving $Ax = b$ is called backward stable if the computed solution $\hat{x}$ is the exact solution of a nearby problem, that is, if there exists a small perturbation $\Delta A$ such that $(A + \Delta A)\hat{x} = b$ exactly (in exact arithmetic). The size of $\Delta A$ relative to $A$ is the backward error. Crucially, the backward error is a property of the algorithm, while the condition number is a property of the problem. If an algorithm is backward stable with backward error $\|\Delta A\| / \|A\| = O(u)$, where $u$ is the unit roundoff, then the perturbation bound immediately gives

$$\frac{\|\hat{x} - x\|}{\|x\|} \leq \frac{O(u)\,\kappa(A)}{1 - O(u)\,\kappa(A)} \approx O(u)\,\kappa(A),$$

where the approximation holds when $u\,\kappa(A) \ll 1$. This is the Wilkinson principle: a backward-stable algorithm applied to a well-conditioned problem yields an accurate solution, and the forward error is bounded by the product of the backward error and the condition number. When $u\,\kappa(A) \approx 1$, no algorithm can reliably distinguish the solution from any other vector, because the perturbation in the data is as large as the signal itself. The practical threshold in double precision is $\kappa(A) \lesssim 10^{16}$; beyond this, the problem is effectively singular at that precision regardless of the algorithm used.

## 2. Core Architecture & Mechanics

### 2.1 Gaussian Elimination and the LU Factorization

Gaussian elimination transforms a matrix $A$ into upper triangular form by a sequence of elementary row operations. Each operation multiplies a row by a scalar and subtracts it from another row, zeroing entries below the diagonal. The key algebraic insight is that these row operations correspond to multiplication by unit lower triangular matrices, and their product gives the LU factorization $A = LU$, where $L$ is unit lower triangular (ones on the diagonal) and $U$ is upper triangular.

The algorithm proceeds in $n-1$ major steps. At step $k$, the entries below the diagonal in column $k$ are eliminated using the pivot $a_{kk}$. For each row $i > k$, the multiplier is $\ell_{ik} = a_{ik}/a_{kk}$, and the update to the trailing submatrix (rows and columns $k+1$ through $n$) is $a_{ij} \leftarrow a_{ij} - \ell_{ik}\, a_{kj}$. After all steps, the upper triangle stores $U$ and the strictly lower triangle (with an implicit unit diagonal) stores the multipliers in $L$.

```text
    k=1          k=2          k=3          Result
  [ * * * * ]  [ * * * * ]  [ * * * * ]  [ * * * * ]
  [ * * * * ]  [ 0 * * * ]  [ 0 * * * ]  [ 0 * * * ]
  [ * * * * ]  [ 0 * * * ]  [ 0 0 * * ]  [ 0 0 * * ]
  [ * * * * ]  [ 0 * * * ]  [ 0 0 * * ]  [ 0 0 0 * ]
   eliminate    eliminate    eliminate
   col 1        col 2        col 3
```

The existence and uniqueness of the LU factorization is governed by the leading principal minors. Define $\Delta_k = \det(A[1{:}k,\, 1{:}k])$ as the determinant of the $k \times k$ leading principal submatrix. The factorization $A = LU$ with $L$ unit lower triangular and $U$ upper triangular exists if and only if $\Delta_k \neq 0$ for all $k = 1, \ldots, n-1$, and it is unique when it exists.

The proof proceeds by induction. For $n = 1$, the result is trivial: $a_{11} = 1 \cdot a_{11}$. Assume the result holds for all $(n-1) \times (n-1)$ matrices with nonzero leading minors. Partition $A$ as

$$A = \begin{pmatrix} A_{n-1} & c \\ r^T & \alpha \end{pmatrix},$$

where $A_{n-1}$ has nonzero leading minors by hypothesis. By the inductive assumption, $A_{n-1} = L_{n-1} U_{n-1}$. Write the factorization as

$$A = \begin{pmatrix} L_{n-1} & 0 \\ \ell^T & 1 \end{pmatrix}\begin{pmatrix} U_{n-1} & u \\ 0 & \beta \end{pmatrix}.$$

Matching blocks gives $L_{n-1} u = c$ (solvable since $L_{n-1}$ is unit lower triangular and thus nonsingular), $\ell^T U_{n-1} = r^T$ (solvable since $U_{n-1}$ is upper triangular and nonsingular, which follows from $\Delta_{n-1} = \det(U_{n-1}) \neq 0$), and $\beta = \alpha - \ell^T u$. For uniqueness, if $A = L_1 U_1 = L_2 U_2$, then $L_2^{-1} L_1 = U_2 U_1^{-1}$. The left side is unit lower triangular and the right side is upper triangular; the only matrix that is both is the identity, so $L_1 = L_2$ and $U_1 = U_2$.

The computational cost of LU factorization is dominated by the trailing-matrix updates. At step $k$, the update $a_{ij} \leftarrow a_{ij} - \ell_{ik}\, a_{kj}$ for $i, j = k+1, \ldots, n$ requires $(n-k)^2$ multiply-subtract pairs, each costing two floating-point operations (one multiply, one subtract). Additionally, computing the $n-k$ multipliers requires $n-k$ divisions. The total flop count is

$$\sum_{k=1}^{n-1}\bigl[(n-k) + 2(n-k)^2\bigr] = \frac{n(n-1)}{2} + \frac{n(n-1)(2n-1)}{3} = \frac{2n^3}{3} + O(n^2).$$

Once the factorization is available, solving $Ax = b$ requires two triangular solves: forward substitution for $Ly = b$ and back substitution for $Ux = y$. Each triangular solve costs $n^2$ flops, which is dominated by the factorization cost for large $n$. The total cost of solving a single system is therefore $\frac{2}{3}n^3 + O(n^2)$. The major practical advantage of the factorization viewpoint over raw Gaussian elimination is that the expensive $\frac{2}{3}n^3$ factorization is done once, and each additional right-hand side costs only $O(n^2)$.

### 2.2 Partial Pivoting: Why and How

The LU factorization as described above fails when a pivot $a_{kk}$ is zero, and it produces large errors when the pivot is small relative to other entries in the column. The remedy is partial pivoting: before each elimination step, the algorithm searches the current column (from the diagonal downward) for the entry of largest absolute value, swaps the corresponding row into the pivot position, and then proceeds with elimination. The row swaps are recorded in a permutation matrix $P$, and the factorization becomes $PA = LU$.

The algorithm at step $k$ finds $p = \arg\max_{i \geq k} |a_{ik}|$, swaps rows $k$ and $p$ in both the active submatrix and the already-computed part of $L$, and then performs the elimination. The effect on $L$ is that $|l_{ik}| \leq 1$ for all $i > k$, since each multiplier is a ratio of a subdiagonal entry to the largest entry in its column. This bound on the multipliers is the key mechanism by which partial pivoting controls error growth.

Partial pivoting guarantees that the growth factor $\rho = \frac{\max_{i,j} |u_{ij}|}{\max_{i,j} |a_{ij}|}$ satisfies $\rho \leq 2^{n-1}$. To prove this, let $a_{ij}^{(k)}$ denote the entry in position $(i,j)$ after $k$ elimination steps. After partial pivoting, $|a_{kj}^{(k)}| \leq \max_{i \geq k} |a_{ij}^{(k-1)}|$ (the new pivot row was the largest in its column). The Schur complement update gives $|a_{ij}^{(k)}| = |a_{ij}^{(k-1)} - l_{ik} a_{kj}^{(k-1)}| \leq |a_{ij}^{(k-1)}| + |a_{kj}^{(k-1)}|$ since $|l_{ik}| \leq 1$. Defining $M_k = \max_{i,j \geq k} |a_{ij}^{(k)}|$, we obtain $M_k \leq 2 M_{k-1}$, which by induction gives $M_{n-1} \leq 2^{n-1} M_0$. Since $U$ is the final upper triangular matrix, $\max |u_{ij}| = M_{n-1}$, and the bound follows. This worst-case bound of $2^{n-1}$ is attained by special matrices constructed by Wilkinson, but in practice the growth factor is almost always $O(n)$, making partial pivoting reliable for the overwhelming majority of problems.

The backward stability of the complete solve via Gaussian elimination with partial pivoting (GEPP) can be established by combining the factorization error with the triangular solve errors. The factorization step in floating-point arithmetic produces computed factors $\hat{L}$ and $\hat{U}$ satisfying

$$\hat{L}\hat{U} = PA + E_1, \quad \text{where} \quad |E_1| \leq \gamma_n\, |\hat{L}|\,|\hat{U}|,$$

with $\gamma_n = nu/(1 - nu)$. This is a componentwise bound, which is sharper than a normwise bound because it accounts for the scale of each entry individually. The forward substitution step computes $\hat{y}$ satisfying $(\hat{L} + \Delta L)\hat{y} = Pb$ with $|\Delta L| \leq \gamma_n |\hat{L}|$, and the back substitution computes $\hat{x}$ satisfying $(\hat{U} + \Delta U)\hat{x} = \hat{y}$ with $|\Delta U| \leq \gamma_n |\hat{U}|$. Combining these three results yields

$$(A + \Delta A)\hat{x} = b, \quad \text{where} \quad \|\Delta A\|_\infty \leq p(n)\, u\, \rho\, \|A\|_\infty,$$

for a modest polynomial $p(n)$ in $n$ and the growth factor $\rho$. The backward error is thus $O(u\rho p(n))$, which is $O(u)$ whenever $\rho$ is not pathologically large. Applying the perturbation bound from Section 1 gives the forward error estimate

$$\frac{\|\hat{x} - x\|_\infty}{\|x\|_\infty} \lesssim p(n)\, u\, \rho\, \kappa_\infty(A).$$

This confirms that GEPP is backward stable under mild conditions on $\rho$, and the accuracy of the computed solution is governed by $\kappa(A)$.

### 2.3 Cholesky Factorization for Symmetric Positive Definite Systems

When $A$ is symmetric positive definite (SPD), meaning $A = A^T$ and $x^T A x > 0$ for all nonzero $x$, a more efficient and stable factorization is available. The Cholesky factorization writes $A = LL^T$, where $L$ is lower triangular with positive diagonal entries. It exploits symmetry to halve both the storage and the computational cost compared to LU, and it requires no pivoting for numerical stability.

The existence and uniqueness of the Cholesky factorization can be proved by induction. For $n = 1$, the condition $a_{11} > 0$ (which follows from positive definiteness) gives $l_{11} = \sqrt{a_{11}}$. For general $n$, partition

$$A = \begin{pmatrix} \alpha & b^T \\ b & C \end{pmatrix}, \quad L = \begin{pmatrix} \lambda & 0 \\ \ell & L_2 \end{pmatrix}.$$

Matching blocks in $LL^T = A$ gives $\lambda = \sqrt{\alpha}$, $\ell = b/\lambda = b/\sqrt{\alpha}$, and $L_2 L_2^T = C - \ell \ell^T = C - bb^T/\alpha$. To apply the inductive hypothesis, we must show that $C - bb^T/\alpha$ is SPD. For any nonzero $z \in \mathbb{R}^{n-1}$, consider the vector $(t, z)$ with $t = -b^T z / \alpha$. By positive definiteness of $A$,

$$0 < \begin{pmatrix} t \\ z \end{pmatrix}^T \begin{pmatrix} \alpha & b^T \\ b & C \end{pmatrix} \begin{pmatrix} t \\ z \end{pmatrix} = \alpha t^2 + 2t\, b^T z + z^T C z = z^T C z - \frac{(b^T z)^2}{\alpha}.$$

This shows $z^T(C - bb^T/\alpha)z > 0$ for all nonzero $z$, so the Schur complement is SPD, and the induction proceeds. Uniqueness follows because the diagonal entries of $L$ are constrained to be positive, eliminating the sign ambiguity that exists in the general LU case.

The Cholesky algorithm computes one column of $L$ at a time. For column $j$, the diagonal entry is

$$l_{jj} = \sqrt{a_{jj} - \sum_{k=1}^{j-1} l_{jk}^2},$$

and the subdiagonal entries are

$$l_{ij} = \frac{1}{l_{jj}}\left(a_{ij} - \sum_{k=1}^{j-1} l_{ik}\, l_{jk}\right), \quad i = j+1, \ldots, n.$$

The diagonal formula requires that $a_{jj} - \sum_{k=1}^{j-1} l_{jk}^2 > 0$, which is guaranteed by positive definiteness: this quantity equals the $j$-th Schur complement, which inherits positive definiteness from $A$. This is why Cholesky needs no pivoting—the algorithm cannot fail on an SPD matrix, and the diagonal entries of $L$ are automatically well-scaled relative to the matrix entries.

The computational cost is approximately $\frac{1}{3}n^3 + O(n^2)$ flops, half that of LU. To count precisely, the diagonal computation at step $j$ costs $2(j-1)$ flops for the squared-sum, plus one square root. The subdiagonal computation processes $n-j$ entries, each requiring $2(j-1)$ flops for the dot product and one division, giving $2(j-1)+1$ flops per entry. The dominant term is

$$\sum_{j=1}^{n} 2(n-j)(j-1) = 2\sum_{m=0}^{n-1} m(n-1-m) = \frac{n^3}{3} + O(n^2),$$

where the substitution $m = j - 1$ has been used.

The backward stability of Cholesky factorization is particularly clean. The computed $\hat{L}$ satisfies

$$\hat{L}\hat{L}^T = A + E, \quad \|E\|_2 \leq \gamma_{n+1}\|A\|_2,$$

and the relative backward error is $O(u)$ without any growth factor, because the Cholesky process is self-scaling: each diagonal entry is a square root of a Schur complement, and the magnitudes are controlled by the positive definiteness of $A$. In practice, Cholesky is the method of choice for SPD systems, and its absence of a growth factor makes it unconditionally backward stable.

### 2.4 Backward Stability of Triangular Solves

The triangular solve is the workhorse of direct methods: every factorization is useful only because triangular systems can be solved efficiently and stably. A careful error analysis of this seemingly simple operation reveals why the entire factorization approach works.

Consider forward substitution for the lower triangular system $Ly = b$, where $L \in \mathbb{R}^{n \times n}$ is nonsingular and lower triangular. The algorithm computes

$$y_i = \frac{b_i - \sum_{j=1}^{i-1} l_{ij}\, y_j}{l_{ii}}, \quad i = 1, \ldots, n.$$

In floating-point arithmetic, the computation of each $y_i$ involves a sequence of multiply-add operations, each introducing a relative error bounded by the unit roundoff $u$. The inner product $s = \sum_{j=1}^{i-1} l_{ij} y_j$ is accumulated in floating point, and the standard model for floating-point summation gives

$$\widehat{s} = \sum_{j=1}^{i-1} l_{ij}\, y_j\, (1 + \theta_{ij}), \quad |\theta_{ij}| \leq \gamma_{i-1} = \frac{(i-1)u}{1 - (i-1)u}.$$

The subtraction $b_i - \widehat{s}$ and the division by $l_{ii}$ each introduce one additional rounding error. Combining all errors, the computed $\hat{y}_i$ satisfies

$$l_{ii}\, \hat{y}_i = \left(b_i - \sum_{j=1}^{i-1} l_{ij}\, \hat{y}_j\, (1 + \theta_{ij})\right)(1 + \theta_i),$$

where $|\theta_i| \leq u$. Rearranging this expression into matrix form, we can write

$$(L + \Delta L)\hat{y} = b, \quad |\Delta L| \leq \gamma_n\, |L|.$$

This is a componentwise backward error bound: each entry of $L$ is perturbed by an amount proportional to its own magnitude, with the proportionality constant bounded by $\gamma_n \approx nu$. The analogous result holds for back substitution solving $Ux = y$:

$$(U + \Delta U)\hat{x} = \hat{y}, \quad |\Delta U| \leq \gamma_n\, |U|.$$

The componentwise nature of this bound is significant. It means that if $L$ has entries of widely varying magnitude, the backward error in each entry is scaled to that entry's size, not to the largest entry. This is stronger than a normwise bound and is the reason why triangular solves are backward stable even for badly scaled triangular matrices. The practical consequence is that once a good factorization is obtained, the triangular solves introduce negligible additional error compared to the factorization itself.

### 2.5 QR Factorization and Least Squares

When the system $Ax = b$ is overdetermined—$A \in \mathbb{R}^{m \times n}$ with $m > n$ and full column rank—there is generally no exact solution, and the problem becomes the least-squares problem: minimize $\|Ax - b\|_2$. The classical approach via the normal equations forms $A^T A x = A^T b$ and applies Cholesky, but this squares the condition number: $\kappa(A^T A) = \kappa(A)^2$. If $\kappa(A) \approx 10^8$, a perfectly manageable value, then $\kappa(A^T A) \approx 10^{16}$, which exhausts double precision entirely. The QR factorization avoids this squaring and solves the least-squares problem with a backward error of $O(u)$ independent of $\kappa(A)$.

The QR factorization writes $A = QR$, where $Q \in \mathbb{R}^{m \times m}$ is orthogonal ($Q^T Q = I$) and $R \in \mathbb{R}^{m \times n}$ is upper triangular (or upper trapezoidal). Orthogonal transformations preserve the 2-norm, so

$$\|Ax - b\|_2 = \|Q^T(Ax - b)\|_2 = \|Rx - Q^T b\|_2.$$

Partitioning $R = \begin{pmatrix} R_1 \\ 0 \end{pmatrix}$ where $R_1 \in \mathbb{R}^{n \times n}$ is upper triangular, and $Q^T b = \begin{pmatrix} c_1 \\ c_2 \end{pmatrix}$ where $c_1 \in \mathbb{R}^n$, the norm splits as $\|R_1 x - c_1\|_2^2 + \|c_2\|_2^2$. The minimum is achieved when $R_1 x = c_1$, which is solved by back substitution, and the residual norm is $\|c_2\|_2$.

The standard method for computing the QR factorization is the Householder reflector. A Householder reflector is a matrix of the form $H = I - 2vv^T/(v^T v)$, where $v \in \mathbb{R}^m$ is a nonzero vector. This matrix is symmetric ($H = H^T$) and orthogonal: $H^T H = (I - 2vv^T/v^Tv)^2 = I - 4vv^T/v^Tv + 4v(v^Tv)v^T/(v^Tv)^2 = I$. Given a vector $x$, the reflector is chosen to map $x$ to a multiple of $e_1$: setting $v = x + \text{sign}(x_1)\|x\|_2\, e_1$, one can verify that $Hx = -\text{sign}(x_1)\|x\|_2\, e_1$. The sign choice avoids cancellation: it ensures that $v_1 = x_1 + \text{sign}(x_1)\|x\|_2$ does not subtract two nearly equal quantities.

The QR factorization applies a sequence of $n$ Householder reflectors to progressively zero out the subdiagonal entries of $A$. At step $k$, the reflector $H_k$ is constructed from the vector $a_{k:m,\,k}$ (the $k$-th column of the current matrix, from row $k$ downward) and applied to the trailing submatrix $A_{k:m,\, k:n}$. The reflector is stored implicitly as the vector $v_k$ (with $v_k(1) = 1$ by normalization), so the application $H_k A_{k:m,k:n} = A_{k:m,k:n} - 2v_k(v_k^T A_{k:m,k:n})/(v_k^T v_k)$ costs $4(m-k+1)(n-k+1)$ flops. Summing over all steps gives the total cost

$$\sum_{k=1}^{n} 4(m-k+1)(n-k+1) = 2mn^2 - \frac{2n^3}{3} + O(mn).$$

For a square matrix ($m = n$), this is $\frac{4}{3}n^3$ flops, twice the cost of LU. For a tall thin matrix ($m \gg n$), the cost is approximately $2mn^2$, linear in $m$.

The backward stability of Householder QR is a model result. The computed factorization satisfies $\hat{Q}\hat{R} = A + E$ with $\|E\|_2 \leq p(m,n)\, u\, \|A\|_2$, where $p(m,n)$ is a modest polynomial. The orthogonality of $\hat{Q}$ is also preserved to working precision: $\|\hat{Q}^T \hat{Q} - I\|_2 \leq p(m,n)\, u$. For the least-squares problem, the computed solution $\hat{x}$ satisfies

$$\|(A + \Delta A)\hat{x} - (b + \Delta b)\|_2 = \min_x \|(A + \Delta A)x - (b + \Delta b)\|_2,$$

with $\|\Delta A\|_2 \leq p(m,n)\, u\, \|A\|_2$ and $\|\Delta b\|_2 \leq p(m,n)\, u\, \|b\|_2$. This is a backward stable result for the least-squares problem: the computed solution is the exact least-squares solution of a slightly perturbed problem. The forward error in the solution is then bounded by $\kappa(A)\, u$ (not $\kappa(A)^2\, u$ as with normal equations), preserving the conditioning of the original problem.

## 3. High-Performance Optimization & Failure Modes

### 3.1 Block Algorithms and Memory Hierarchy

The unblocked algorithms described above perform one rank-1 update at a time, which is inefficient on modern architectures because each update touches the entire trailing submatrix with low arithmetic intensity (ratio of flops to memory operations). The remedy is block (or blocked) factorization, which processes a block of $b$ columns at a time and performs the bulk of the work as a matrix-matrix multiplication (level-3 BLAS operation), which has high arithmetic intensity and achieves a large fraction of peak performance.

In block LU factorization, at each step a block of $b$ columns is factored using the unblocked algorithm, producing $L_{11}$ (a $b \times b$ unit lower triangular block) and $U_{11}$ (a $b \times b$ upper triangular block). The off-diagonal blocks $U_{12}$ are computed by forward substitution: $L_{11} U_{12} = A_{12}$. The multipliers $L_{21}$ are then $L_{21} = A_{21} U_{11}^{-1}$, also by triangular solve. Finally, the Schur complement is updated as $A_{22} \leftarrow A_{22} - L_{21} U_{12}$, which is a matrix multiplication of two rectangular blocks. This final update dominates the computation and achieves high performance because it is a level-3 operation. The total flop count is unchanged at $\frac{2}{3}n^3 + O(n^2)$, but the fraction of flops performed as matrix-matrix multiplication approaches $1 - 3b/(2n)$, which is close to unity for $n \gg b$. The block size $b$ is typically chosen to fit the relevant blocks in cache, with values in the range 32–256 on contemporary hardware.

Block Cholesky follows a similar pattern: a $b \times b$ diagonal block is factored, the corresponding row block of $L$ is computed by triangular solve, and the Schur complement is updated by a symmetric rank-$b$ update. The symmetry of the update is exploited to halve the work, maintaining the $\frac{1}{3}n^3$ cost.

### 3.2 The Growth Factor: When Pivoting Is Not Enough

The worst-case growth factor bound $\rho \leq 2^{n-1}$ for partial pivoting is alarming: for $n = 100$, this permits growth by a factor of $10^{30}$, which would destroy all accuracy. In practice, such growth is almost never observed. Extensive numerical experiments over decades have found that for random matrices, the growth factor is typically $O(n^{1/2})$, and even for structured matrices it rarely exceeds $O(n)$. The matrices that achieve the worst-case bound are carefully constructed and do not arise in physical applications.

However, partial pivoting is not the only pivoting strategy, and certain problem classes expose its limitations. Complete pivoting searches the entire trailing submatrix (not just the current column) for the largest entry, giving the tighter bound $\rho \leq n^{1/2}(2 \cdot 3^{1/2} \cdot 4^{1/3} \cdots n^{1/(n-1)})^{1/2} \approx n^{1/2} \cdot (2.91)^{1/2}$, which grows much more slowly. The cost is $O(n^3)$ extra comparisons, which is significant. Rook pivoting is a compromise that searches along the current row and column for an entry that is maximal in both, giving growth bounds comparable to complete pivoting at a lower search cost.

For matrices where partial pivoting is known to fail, such as those arising from certain discretizations of integral equations, the practical remedy is often to rescale the matrix (equilibration) before factorization, or to use a different factorization altogether. The LAPACK routine `xGESVX` provides automatic equilibration, which computes diagonal scaling matrices $D_r$ and $D_c$ such that $D_r A D_c$ has entries of roughly uniform magnitude, then applies GEPP to the scaled matrix.

### 3.3 Iterative Refinement

When the condition number is large but not so large that the solution is entirely lost, iterative refinement can recover digits of accuracy that were lost in the initial solve. Given the computed factorization $\hat{L}\hat{U} \approx PA$ and the initial solution $\hat{x}^{(0)}$, one step of refinement computes the residual $r^{(k)} = b - A\hat{x}^{(k)}$, solves the correction equation $PAd^{(k)} = r^{(k)}$ using the existing factors, and updates $\hat{x}^{(k+1)} = \hat{x}^{(k)} + d^{(k)}$.

The critical implementation detail is the precision of the residual computation. If $r^{(k)}$ is computed in the same precision as the solve, the residual is contaminated by rounding errors of size $\|A\|\|\hat{x}^{(k)}\| u$, and the correction $d^{(k)}$ has relative error $\kappa(A) u$. Each step reduces the error by a factor of approximately $\kappa(A) u$, so convergence requires $\kappa(A) u < 1$ and takes $O(\log(1/(u\kappa(A))) / \log(\kappa(A)u))$ steps to reach full precision.

If the residual is computed in extended precision—typically by accumulating $r = b - A\hat{x}$ in double the working precision (e.g., using extended-precision BLAS or fused multiply-add operations)—the picture changes entirely. The residual is then accurate to $O(u^2)$, and each refinement step reduces the error by a factor of approximately $u$ (not $\kappa(A) u$). This means that iterative refinement converges to full working precision for any $\kappa(A) < 1/u$, extending the range of solvable problems dramatically. In double precision, this covers condition numbers up to $\approx 10^{16}$, compared to $\approx 10^8$ without refinement. This mixed-precision approach is implemented in LAPACK's `xGERFS` and has become increasingly practical with the widespread availability of mixed-precision hardware.

### 3.4 Rank Deficiency and Column-Pivoted QR

When $A \in \mathbb{R}^{m \times n}$ has rank less than $n$, the least-squares problem has infinitely many solutions, and the standard QR factorization may produce a factor $R_1$ that is numerically singular. The remedy is column-pivoted QR, which permutes the columns of $A$ during factorization so that the diagonal entries of $R$ are non-increasing in magnitude. At step $k$, the column with the largest remaining 2-norm is swapped into position $k$, and the Householder reflector is applied. The resulting factorization is $AP = QR$, where $P$ is a permutation matrix, and the diagonal of $R$ satisfies $|r_{11}| \geq |r_{22}| \geq \cdots \geq |r_{nn}|$.

The rank-revealing property is that if $\text{rank}(A) = r < n$, then $|r_{r+1, r+1}|$ is small relative to $|r_{11}|$, and the first $r$ columns of $AP$ form a well-conditioned basis for the column space of $A$. The factorization can then be partitioned as

$$AP = Q \begin{pmatrix} R_{11} & R_{12} \\ 0 & R_{22} \end{pmatrix}, \quad \text{with} \quad \|R_{22}\| \text{ small},$$

and the least-squares solution is obtained by solving $R_{11} x_1 = c_1 - R_{12} x_2$ with $x_2 = 0$ (the minimum-norm solution). Column-pivoted QR is the standard method for rank determination in least-squares problems and is implemented in LAPACK as `xGEQP3`. For problems where the rank determination must be reliable, more sophisticated rank-revealing factorizations (such as the URV or ULV decompositions) provide guaranteed bounds on $\|R_{22}\|$ at higher cost.

### 3.5 Failure Modes of Cholesky and Regularization

The Cholesky factorization fails when the input matrix is not positive definite, and the failure is informative: the algorithm attempts to take the square root of a negative or zero quantity, which signals that the matrix has a non-positive eigenvalue. For matrices that are positive semidefinite (with some zero eigenvalues), the diagonal $l_{jj}$ becomes zero, causing a division by zero in the subdiagonal computation.

A subtler failure mode arises for matrices that are theoretically positive definite but have been perturbed by rounding so that the smallest eigenvalue is close to zero. The Cholesky factorization may complete but produce a factor $L$ with very small diagonal entries, leading to large entries in the solution and amplifying rounding errors. The condition number $\kappa(A) = \lambda_{\max}/\lambda_{\min}$ quantifies this sensitivity: when $\lambda_{\min}$ approaches $u \lambda_{\max}$, the matrix is numerically singular and the solution is unreliable regardless of the algorithm.

The practical remedy for near-singular SPD systems is Tikhonov regularization: replace $A$ by $A + \alpha I$ for a small positive $\alpha$, which shifts all eigenvalues upward by $\alpha$ and reduces the condition number to $\kappa(A + \alpha I) = (\lambda_{\max} + \alpha)/(\lambda_{\min} + \alpha)$. The choice of $\alpha$ trades off the accuracy of the solution against its stability; common selection criteria include the L-curve method, generalized cross-validation, and the discrepancy principle. The regularized system remains SPD, so Cholesky can be applied directly.

For matrices that are symmetric but indefinite, the Cholesky factorization does not apply. The appropriate alternatives are the $LDL^T$ factorization (which avoids square roots and handles indefinite matrices through a diagonal block factor $D$) or the symmetric indefinite factorization of Bunch and Kaufmann, which uses a combination of $1 \times 1$ and $2 \times 2$ pivot blocks to maintain symmetry and achieve backward stability with a growth factor bounded by $O(n^2)$. The Bunch-Kaufmann factorization is implemented in LAPACK as `xSYTRF` and is the standard method for symmetric indefinite systems, costing $\frac{1}{3}n^3 + O(n^2)$ flops, the same as Cholesky.
